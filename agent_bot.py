import os
import logging
import asyncio
import json
import tempfile
import time as _time
from collections import OrderedDict
from datetime import datetime, time
from dotenv import load_dotenv
from telegram import Update, constants
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes

from agent_orchestrator import OrchestratorAgent

load_dotenv()
TELEGRAM_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
NAPKIN_TOKEN = os.getenv("NAPKIN_API_TOKEN")

KNOWLEDGE_SOURCES = os.environ.get(
    "FLOSE_KNOWLEDGE_SOURCES",
    os.path.join(os.path.dirname(__file__), "vault_temp")
).split(os.pathsep)

# Controle de Acesso
_allowed_raw = os.environ.get("FLOSE_ALLOWED_CHAT_IDS", "")
ALLOWED_CHAT_IDS = set(int(x.strip()) for x in _allowed_raw.split(",") if x.strip())

import agent_core
logger = logging.getLogger(__name__)

# Rate Limiting
RATE_LIMIT_SECONDS = int(os.environ.get("FLOSE_RATE_LIMIT_SECONDS", "5"))
_last_message_time = {}

# Configuracao
MAX_ACTIVE_CHATS = int(os.environ.get("FLOSE_MAX_CHATS", "50"))
SAVE_STATE_INTERVAL = 30
_last_save_time = 0.0

ORCHESTRATOR = OrchestratorAgent(KNOWLEDGE_SOURCES, NAPKIN_TOKEN)
START_TIME = datetime.now()
MSG_IN = 0
MSG_OUT = 0
AUDIO_IN = 0
AUDIO_OUT = 0
DIAGRAMS_GEN = 0
BOT_STATE_FILE = os.path.join(os.path.dirname(__file__), "agent_bot_state.json")

CHAT_HISTORIES = OrderedDict()
GLOBAL_APPLICATION = None

# Classes Fakes para suporte à Fila Persistente
class FakeMessage:
    def __init__(self, chat_id):
        self.chat_id = chat_id

class FakeUpdate:
    def __init__(self, chat_id):
        self.message = FakeMessage(chat_id)

class FakeBot:
    def __init__(self, bot_instance):
        self._bot = bot_instance
        
    async def send_message(self, chat_id, text, parse_mode=None):
        if self._bot:
            await self._bot.send_message(chat_id=chat_id, text=text, parse_mode=parse_mode)
            
    async def send_photo(self, chat_id, photo, caption=None):
        if self._bot:
            await self._bot.send_photo(chat_id=chat_id, photo=photo, caption=caption)

class FakeContext:
    def __init__(self, bot_instance):
        self.bot = FakeBot(bot_instance)

import sqlite3
class PersistentQueue:
    """Fila de tarefas assíncronas persistente baseada em SQLite (Item 93)."""
    def __init__(self, db_path="logs/task_queue.db"):
        self.db_path = db_path
        self._init_db()
        self._cond = asyncio.Condition()

    def _init_db(self):
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS queue (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    data TEXT NOT NULL,
                    timestamp REAL NOT NULL
                )
            """)
            conn.commit()

    def qsize(self):
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT COUNT(*) FROM queue")
                return cursor.fetchone()[0]
        except Exception:
            return 0

    def empty(self):
        return self.qsize() == 0

    async def put(self, item):
        import time
        serializable_item = {}
        for k, v in item.items():
            if k == 'update':
                serializable_item['chat_id'] = v.message.chat_id
            elif k == 'context':
                pass
            else:
                serializable_item[k] = v
                
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                "INSERT INTO queue (data, timestamp) VALUES (?, ?)",
                (json.dumps(serializable_item), time.time())
            )
            conn.commit()
            
        async with self._cond:
            self._cond.notify_all()

    async def get(self):
        async with self._cond:
            while self.empty():
                await self._cond.wait()
                
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT id, data FROM queue ORDER BY timestamp ASC LIMIT 1")
            row = cursor.fetchone()
            if row:
                tid, data_str = row
                item = json.loads(data_str)
                conn.execute("DELETE FROM queue WHERE id = ?", (tid,))
                conn.commit()
                
                # Reconstrói FakeUpdate e FakeContext se for napkin
                if item.get('type') == 'napkin':
                    chat_id = item.get('chat_id')
                    item['update'] = FakeUpdate(chat_id)
                    if GLOBAL_APPLICATION:
                        item['context'] = FakeContext(GLOBAL_APPLICATION.bot)
                    else:
                        item['context'] = FakeContext(None)
                return item
        return {}

    def task_done(self):
        pass

# Fila Persistente em SQLite
TASK_QUEUE = PersistentQueue()
LAST_ACTIVITY = datetime.now()
USER_CHAT_ID = None

TG_MAX_LENGTH = 4096


def _is_authorized(chat_id: int) -> bool:
    if not ALLOWED_CHAT_IDS:
        return True
    return chat_id in ALLOWED_CHAT_IDS


async def _send_long_message(bot, chat_id, text, parse_mode=None):
    """Envia mensagem dividida em chunks se exceder limite do Telegram."""
    if len(text) <= TG_MAX_LENGTH:
        await bot.send_message(chat_id=chat_id, text=text, parse_mode=parse_mode)
        return

    chunks = []
    while text:
        if len(text) <= TG_MAX_LENGTH:
            chunks.append(text)
            break
        cut = text.rfind('\n', 0, TG_MAX_LENGTH)
        if cut == -1:
            cut = TG_MAX_LENGTH
        chunks.append(text[:cut])
        text = text[cut:].lstrip('\n')

    for chunk in chunks:
        try:
            await bot.send_message(chat_id=chat_id, text=chunk, parse_mode=parse_mode)
        except Exception:
            await bot.send_message(chat_id=chat_id, text=chunk)


def _is_rate_limited(chat_id: int) -> bool:
    now = _time.time()
    last = _last_message_time.get(chat_id, 0)
    if now - last < RATE_LIMIT_SECONDS:
        return True
    _last_message_time[chat_id] = now
    return False

def load_persistence():
    global MSG_IN, MSG_OUT, AUDIO_IN, AUDIO_OUT, DIAGRAMS_GEN, CHAT_HISTORIES
    if os.path.exists(BOT_STATE_FILE):
        try:
            with open(BOT_STATE_FILE, 'r') as f:
                data = json.load(f)
                MSG_IN = data.get("msg_in", 0)
                MSG_OUT = data.get("msg_out", 0)
                AUDIO_IN = data.get("audio_in", 0)
                AUDIO_OUT = data.get("audio_out", 0)
                DIAGRAMS_GEN = data.get("diagrams", 0)
                raw = data.get("raw_history", {})
                # Converte chaves de volta para int (IDs do Telegram)
                CHAT_HISTORIES = OrderedDict(
                    (int(k), v) for k, v in raw.items()
                )
        except Exception as e:
            logger.warning(f"Erro ao carregar persistencia: {e}")

load_persistence()

async def task_worker():
    while True:
        task = await TASK_QUEUE.get()
        try:
            if task['type'] == 'napkin':
                logger.info("Worker: Generating diagram for task")
                await ORCHESTRATOR.visual.create_diagram(task['update'], task['context'], task['content'])
                global DIAGRAMS_GEN
                DIAGRAMS_GEN += 1
                save_state(force=True)
                try:
                    chat_id = task['update'].message.chat_id
                    await task['context'].bot.send_message(
                        chat_id=chat_id,
                        text="\u2705 Diagrama gerado com sucesso!",
                    )
                except Exception as e:
                    logger.warning(f"Worker: Erro ao enviar confirmacao de diagrama: {e}")
                logger.info("Worker: Diagram generated successfully")
            elif task['type'] == 'index':
                logger.info("Worker: Starting background indexing")
                ORCHESTRATOR.rag.update_embeddings(LAST_ACTIVITY, background=True)
                logger.info("Worker: Background indexing finished")
        except Exception as e:
            logger.error(f"Worker Error: {e}")
            if task.get('type') == 'napkin':
                try:
                    chat_id = task['update'].message.chat_id
                    await task['context'].bot.send_message(
                        chat_id=chat_id,
                        text=f"\u274c Erro ao gerar diagrama: {e}",
                    )
                except Exception:
                    pass
        finally:
            TASK_QUEUE.task_done()

async def handle_voice(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Handler de voz do bot. Baixa o arquivo de áudio, realiza transcrição (Whisper local)
    e encaminha para o processamento de consulta.
    """
    global LAST_ACTIVITY, AUDIO_IN
    chat_id = update.message.chat_id

    if not _is_authorized(chat_id):
        logger.warning(f"Acesso negado para chat_id={chat_id}")
        await update.message.reply_text("⛔ Acesso não autorizado.")
        return

    if _is_rate_limited(chat_id):
        await update.message.reply_text("⏳ Aguarde alguns segundos antes de enviar outra mensagem.")
        return

    LAST_ACTIVITY = datetime.now()
    AUDIO_IN += 1
    audio_obj = update.message.voice or update.message.audio or update.message.video_note
    status = await update.message.reply_text("🎙 *Ouvindo...*", parse_mode=constants.ParseMode.MARKDOWN)

    path = None
    try:
        path = f"temp_{audio_obj.file_id}.oga"
        tg_file = await context.bot.get_file(audio_obj.file_id)
        await tg_file.download_to_drive(path)

        user_text = ORCHESTRATOR.voice.transcribe(path)
        logger.info(f"Voice received. Transcribed: {user_text[:50]}...")
    finally:
        if path and os.path.exists(path):
            os.remove(path)

    await status.edit_text(f"📝 *Entendido:* _{user_text}_", parse_mode=constants.ParseMode.MARKDOWN)
    await process_full_query(update, context, user_text, status, is_voice=True)

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Handler padrão de mensagens de texto do bot.
    Valida autorização, rate limiting e envia a consulta para processamento.
    """
    global MSG_IN
    chat_id = update.message.chat_id

    if not _is_authorized(chat_id):
        logger.warning(f"Acesso negado para chat_id={chat_id}")
        await update.message.reply_text("⛔ Acesso não autorizado.")
        return

    if _is_rate_limited(chat_id):
        await update.message.reply_text("⏳ Aguarde alguns segundos antes de enviar outra mensagem.")
        return

    MSG_IN += 1
    await process_full_query(update, context, update.message.text, is_voice=False)

async def process_full_query(update: Update, context: ContextTypes.DEFAULT_TYPE, text, status=None, is_voice=False):
    """
    Processa a mensagem transcrita ou textual através do OrchestratorAgent, gerencia
    o histórico do chat em cache LRU e enfileira geração de diagramas Napkin caso solicitado.
    """
    global USER_CHAT_ID, LAST_ACTIVITY
    chat_id = update.message.chat_id
    USER_CHAT_ID = chat_id
    LAST_ACTIVITY = datetime.now()
    
    # LRU: move chat para o final e limita numero de chats ativos
    if chat_id in CHAT_HISTORIES:
        CHAT_HISTORIES.move_to_end(chat_id)
    else:
        CHAT_HISTORIES[chat_id] = []
    while len(CHAT_HISTORIES) > MAX_ACTIVE_CHATS:
        CHAT_HISTORIES.popitem(last=False)

    if not status:
        await context.bot.send_chat_action(chat_id=chat_id, action=constants.ChatAction.TYPING)
        status = await update.message.reply_text("✨ *Pensando...*", parse_mode=constants.ParseMode.MARKDOWN)
    
    logger.info(f"Processing query: {text[:50]}...")
    # Orquestrador assume o controle
    ai_response = await ORCHESTRATOR.process_query(update, context, text, CHAT_HISTORIES[chat_id], is_voice)
    logger.info("Response generated.")
    
    # Pos-processamento: Visual (keywords expandidos)
    visual_keywords = [
        "diagrama", "desenho", "mapa mental", "infográfico",
        "fluxograma", "visualize", "desenhe", "esquema", "fluxo",
        "organograma", "mindmap", "ilustre", "gráfico",
    ]
    if any(x in text.lower() for x in visual_keywords):
        await update.message.reply_text("⏳ *VisualAgent:* Gerando seu diagrama na fila...", parse_mode=constants.ParseMode.MARKDOWN)
        await TASK_QUEUE.put({"type": "napkin", "update": update, "context": context, "content": ai_response})

    # Envio da Resposta — com fallback robusto
    try:
        if len(ai_response) <= TG_MAX_LENGTH:
            await context.bot.edit_message_text(
                chat_id=chat_id, message_id=status.message_id,
                text=ai_response, parse_mode=constants.ParseMode.MARKDOWN,
            )
        else:
            try:
                await context.bot.delete_message(chat_id=chat_id, message_id=status.message_id)
            except Exception:
                pass
            await _send_long_message(context.bot, chat_id, ai_response, parse_mode=constants.ParseMode.MARKDOWN)
    except Exception as e:
        logger.warning(f"Erro ao enviar com Markdown, tentando sem formatacao: {e}")
        try:
            if len(ai_response) <= TG_MAX_LENGTH:
                await context.bot.edit_message_text(
                    chat_id=chat_id, message_id=status.message_id,
                    text=ai_response,
                )
            else:
                await _send_long_message(context.bot, chat_id, ai_response)
        except Exception as e2:
            logger.error(f"Falha total ao enviar resposta: {e2}")
            try:
                await context.bot.send_message(
                    chat_id=chat_id,
                    text="\u26a0\ufe0f Erro ao formatar a resposta. Tente novamente.",
                )
            except Exception:
                pass
    
    # Resposta por Voz
    if is_voice:
        context.application.create_task(ORCHESTRATOR.voice.speak(context, chat_id, ai_response))
    
    # Memória
    CHAT_HISTORIES[chat_id].append({"u": text, "a": ai_response})
    if len(CHAT_HISTORIES[chat_id]) > 10:
        CHAT_HISTORIES[chat_id].pop(0)

    global MSG_OUT, AUDIO_OUT
    MSG_OUT += 1
    if is_voice:
        AUDIO_OUT += 1
    save_state()

def save_state(force=False):
    """Salva estado do bot com escrita atômica e envia via HTTP POST para o Flask (desacoplamento)."""
    global _last_save_time
    now = _time.time()
    if not force and (now - _last_save_time) < SAVE_STATE_INTERVAL:
        return
    _last_save_time = now

    last_chat = []
    if CHAT_HISTORIES:
        latest_chat_id = list(CHAT_HISTORIES.keys())[-1]
        last_chat = CHAT_HISTORIES[latest_chat_id][-5:]

    state = {
        "status": "online",
        "uptime": str(datetime.now() - START_TIME).split(".")[0],
        "msg_in": MSG_IN,
        "msg_out": MSG_OUT,
        "audio_in": AUDIO_IN,
        "audio_out": AUDIO_OUT,
        "diagrams": DIAGRAMS_GEN,
        "queue_size": TASK_QUEUE.qsize(),
        "active_chats": len(CHAT_HISTORIES),
        "last_messages": last_chat,
        "raw_history": dict(CHAT_HISTORIES),
        "index_status": ORCHESTRATOR.rag.get_index_status(),
        "last_activity": LAST_ACTIVITY.strftime("%H:%M:%S"),
        "timestamp": datetime.now().isoformat()
    }
    
    # 1. Grava backup local em arquivo físico (backup frio)
    try:
        dir_name = os.path.dirname(BOT_STATE_FILE) or '.'
        fd, tmp_path = tempfile.mkstemp(dir=dir_name, suffix='.tmp')
        try:
            with os.fdopen(fd, 'w') as f:
                json.dump(state, f)
            os.replace(tmp_path, BOT_STATE_FILE)
        except Exception:
            if os.path.exists(tmp_path):
                os.remove(tmp_path)
            raise
    except Exception as e:
        logger.error(f"Error saving state to backup file: {e}")

    # 2. Desacoplamento: Envia telemetria para o Flask App via HTTP POST
    flask_port = int(os.environ.get("PORT", 8091))
    url = f"http://localhost:{flask_port}/api/bot/telemetry"
    api_key = os.environ.get("FLOSE_API_KEY")

    def _send_telemetry_http():
        if not api_key:
            return
        try:
            headers = {"X-API-Key": api_key, "Content-Type": "application/json"}
            requests.post(url, json=state, headers=headers, timeout=5)
        except Exception as he:
            logger.debug(f"Erro ao enviar telemetria HTTP para o Flask Cockpit: {he}")

    try:
        # Tenta disparar a tarefa via thread assíncrona não bloqueante
        loop = asyncio.get_event_loop()
        if loop.is_running():
            loop.create_task(asyncio.to_thread(_send_telemetry_http))
        else:
            _send_telemetry_http()
    except Exception:
        # Fallback se não houver event loop ativo na thread
        try:
            import threading
            threading.Thread(target=_send_telemetry_http, daemon=True).start()
        except Exception:
            _send_telemetry_http()

async def monitor_idle(context):
    if (datetime.now() - LAST_ACTIVITY).total_seconds() > 1200:
        await TASK_QUEUE.put({"type": "index"})
    save_state(force=True)

async def cmd_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.message.chat_id
    logger.info(f"Start command received from {update.effective_user.id} (chat_id={chat_id})")
    if not _is_authorized(chat_id):
        await update.message.reply_text("\u26d4 Acesso n\u00e3o autorizado.")
        return
    await update.message.reply_text(
        "\ud83d\udc4b Ol\u00e1! Sou o seu Assistente Neural. Como posso ajudar hoje?\n\n"
        "Comandos dispon\u00edveis:\n"
        "/help \u2014 Ver comandos e capacidades\n"
        "/status \u2014 Ver estado do sistema\n"
        "/clear \u2014 Limpar hist\u00f3rico de conversa"
    )


async def cmd_help(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not _is_authorized(update.message.chat_id):
        await update.message.reply_text("\u26d4 Acesso n\u00e3o autorizado.")
        return
    await update.message.reply_text(
        "\ud83e\udde0 *Assistente Neural \u2014 Comandos*\n\n"
        "/start \u2014 Iniciar o bot\n"
        "/help \u2014 Ver esta mensagem\n"
        "/status \u2014 Estado do sistema (uptime, modelo, RAG)\n"
        "/clear \u2014 Limpar hist\u00f3rico de conversa\n\n"
        "*Capacidades:*\n"
        "\u2022 Respondo perguntas sobre sua base de conhecimento (vault)\n"
        "\u2022 Aceito mensagens de texto e \u00e1udio\n"
        "\u2022 Gero diagramas (pe\u00e7a um 'diagrama' ou 'mapa mental')\n"
        "\u2022 Crio resumos em HTML (pe\u00e7a um 'resumo')\n"
        "\u2022 Respondo por voz quando voc\u00ea envia \u00e1udio",
        parse_mode=constants.ParseMode.MARKDOWN,
    )


async def cmd_status(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not _is_authorized(update.message.chat_id):
        await update.message.reply_text("\u26d4 Acesso n\u00e3o autorizado.")
        return
    uptime = str(datetime.now() - START_TIME).split(".")[0]
    rag_status = ORCHESTRATOR.rag.get_index_status()
    model = os.environ.get("OLLAMA_MODEL", "gemma4:latest")
    await update.message.reply_text(
        f"\ud83d\udcca *Status do Sistema*\n\n"
        f"\u23f1 Uptime: `{uptime}`\n"
        f"\ud83e\udd16 Modelo: `{model}`\n"
        f"\ud83d\udce8 Msgs recebidas: {MSG_IN}\n"
        f"\ud83d\udce4 Msgs enviadas: {MSG_OUT}\n"
        f"\ud83c\udf99 Audios processados: {AUDIO_IN}\n"
        f"\ud83d\uddbc Diagramas gerados: {DIAGRAMS_GEN}\n"
        f"\ud83d\udcac Chats ativos: {len(CHAT_HISTORIES)}\n"
        f"\ud83d\udcda RAG: {rag_status.get('percentage', 0)}% indexado "
        f"({rag_status.get('indexed', 0)}/{rag_status.get('total', 0)} docs)\n"
        f"\ud83d\udd17 Perguntas geradas: {rag_status.get('questions', 0)}",
        parse_mode=constants.ParseMode.MARKDOWN,
    )


async def cmd_clear(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.message.chat_id
    if not _is_authorized(chat_id):
        await update.message.reply_text("\u26d4 Acesso n\u00e3o autorizado.")
        return
    if chat_id in CHAT_HISTORIES:
        CHAT_HISTORIES[chat_id] = []
        save_state(force=True)
    await update.message.reply_text("\ud83e\uddf9 Hist\u00f3rico de conversa limpo!")


async def post_init(application):
    """Inicializacao pos-startup: inicia worker e agenda indexacao."""
    global GLOBAL_APPLICATION
    GLOBAL_APPLICATION = application
    application.create_task(task_worker())
    await TASK_QUEUE.put({"type": "index"})


if __name__ == '__main__':
    app = ApplicationBuilder().token(TELEGRAM_TOKEN).post_init(post_init).build()
    save_state(force=True)

    app.job_queue.run_repeating(monitor_idle, interval=60)

    # Handlers de comando
    app.add_handler(CommandHandler("start", cmd_start))
    app.add_handler(CommandHandler("help", cmd_help))
    app.add_handler(CommandHandler("status", cmd_status))
    app.add_handler(CommandHandler("clear", cmd_clear))

    # Handlers de conteudo
    app.add_handler(MessageHandler(filters.VOICE | filters.AUDIO | filters.VIDEO_NOTE, handle_voice))
    app.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), handle_message))

    # Catch-all para debug
    async def debug_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
        logger.info(f"Received update: {update.to_dict()}")

    app.add_handler(MessageHandler(filters.ALL, debug_handler), group=1)

    logger.info("System initialized and starting polling...")
    app.run_polling()

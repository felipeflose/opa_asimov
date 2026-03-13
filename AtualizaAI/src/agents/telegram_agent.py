import os
import asyncio
from datetime import datetime
from telegram import Bot, Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from dotenv import load_dotenv

load_dotenv()

class TelegramAgent:
    def __init__(self, orchestrator, gcs_client=None, kg_manager=None, vision_agent=None):
        self.token = os.getenv("TELEGRAM_BOT_TOKEN")
        self.orchestrator = orchestrator
        self.gcs_client = gcs_client
        self.kg_manager = kg_manager
        self.vision_agent = vision_agent
        self.application = None
        self.is_running = False
        self.log_file = "telegram_bot.log"

    def log(self, message, data=None):
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_msg = f"[{timestamp}] {message}"
        with open(self.log_file, "a", encoding="utf-8") as f:
            f.write(f"{log_msg}\n")
        print(log_msg)

        # Upload para o Bucket (GCS) se disponível
        if self.gcs_client and data:
            filename = f"logs/telegram/msg_{datetime.now().strftime('%Y%m%d_%H%M%S_%f')}.json"
            try:
                self.gcs_client.upload_json(data, filename)
            except Exception as e:
                print(f"Erro ao subir log para GCS: {e}")

    async def start_handler(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        user = update.effective_user.username or update.effective_user.first_name
        self.log(f"Comando /start recebido de @{user}")
        await update.message.reply_text("🤖 Flose AI Platform | Telegram Bridge ATIVO.\nEnvie um comando para o Orchestrator!")

    async def message_handler(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        try:
            user = update.effective_user.username or update.effective_user.first_name
            user_text = update.message.text or update.message.caption or ""
            
            has_photo = bool(update.message.photo)
            
            log_data = {
                "platform": "telegram",
                "user": user,
                "message": user_text,
                "has_photo": has_photo,
                "timestamp": datetime.now().isoformat()
            }
            
            self.log(f"Mensagem de @{user}: {user_text} (Foto: {has_photo})", data=log_data)
            
            await update.message.reply_chat_action(action="typing")
            
            image_path = None
            visual_context = ""
            
            if has_photo:
                # Download da maior versão da foto
                photo_file = await update.message.photo[-1].get_file()
                image_path = f"tmp_tg_photo_{datetime.now().strftime('%H%M%S')}.jpg"
                await photo_file.download_to_drive(image_path)
                self.log(f"Foto baixada em: {image_path}")
                
                # Aciona o Agente de Visão se disponível
                if self.vision_agent:
                    try:
                        await update.message.reply_text("👁️ *Vision Agent analisando a imagem...*", parse_mode='Markdown')
                    except:
                        await update.message.reply_text("👁️ Vision Agent analisando a imagem...")
                    visual_context = self.vision_agent.analyze_image(image_path)
                    self.log(f"Análise de Visão completa: {visual_context[:50]}...")
                else:
                    visual_context = "[Imagem recebida, mas VisionAgent offline]"
    
            # Process via Orchestrator (Agora enviamos o que o Vision Agent viu!)
            full_command = f"Contexto Visual: {visual_context}\n\nComando do Usuário: {user_text}"
            decision = self.orchestrator.process_command(full_command, image_path=image_path)
            
            # Limpeza da imagem após processar
            if image_path and os.path.exists(image_path):
                os.remove(image_path)
    
            action = decision.get("action")
            reasoning = decision.get("reasoning", "Processando...")
            
            log_data["decision"] = decision
    
            # Mostrar Reasoning Chain se solicitado (Transparência)
            reasoning_msg = f"🧠 *AI Reasoning Chain:*\n_{reasoning}_"
            try:
                await update.message.reply_text(reasoning_msg, parse_mode='Markdown')
            except:
                await update.message.reply_text(f"AI Reasoning: {reasoning}")

            if action == "respond":
                response = decision.get("response", "Não consegui processar sua dúvida.")
                self.log(f"Resposta direta enviada para @{user}")
                try:
                    await update.message.reply_text(f"💬 *Flose AI*\n\n{response}", parse_mode='Markdown')
                except:
                    await update.message.reply_text(f"💬 Flose AI\n\n{response}")
            
            elif action == "create_agent":
                # Aqui criamos o agente e enviamos a confirmação
                result = self.orchestrator.execute_decision(decision)
                self.log(f"Agente criado via Telegram por @{user}")
                try:
                    await update.message.reply_text(f"🏗️ *Processamento de Agente*\n\n✅ {result}", parse_mode='Markdown')
                except:
                    await update.message.reply_text(f"🏗️ Processamento de Agente\n\n{result}")
            
            elif action == "generate_demand":
                result = self.orchestrator.execute_decision(decision)
                demand = decision.get("demand_info") or {}
                title = demand.get("title", "Sem título")
                dtype = demand.get("type", "tarefa")
                self.log(f"Demanda '{title}' registrada via Telegram por @{user}")
                try:
                    await update.message.reply_text(f"📝 *Nova Demanda (TRD)*\n\n📌 *Título:* {title}\n📂 *Tipo:* {dtype}\n\n✅ {result}", parse_mode='Markdown')
                except:
                    await update.message.reply_text(f"📝 Nova Demanda (TRD)\n\nTítulo: {title}\nTipo: {dtype}\n\n{result}")
    
            else: # execute
                # Executamos a tarefa e enviamos o resultado final para o Telegram
                result = self.orchestrator.execute_decision(decision)
                self.log(f"Tarefa executada via Telegram para @{user}")
                try:
                    await update.message.reply_text(f"⚙️ *Execução Finalizada*\n\n✅ *Resultado:* {result}", parse_mode='Markdown')
                except:
                    await update.message.reply_text(f"⚙️ Execução Finalizada\n\nResultado: {result}")
            
            # Sincroniza o log final (com a decisão) no GCS
            if self.gcs_client:
                filename_final = f"logs/telegram/decision_{datetime.now().strftime('%Y%m%d_%H%M%S_%f')}.json"
                self.gcs_client.upload_json(log_data, filename_final)
    
            # Atualiza o Knowledge Graph com novos conceitos aprendidos
            if self.kg_manager:
                agent_name = decision.get("agent_involved") or "Orchestrator"
                self.kg_manager.add_interaction(
                    agent_name=agent_name,
                    task_name=f"TG: {user_text[:20]}...",
                    outcome={
                        "status": "executed",
                        "learned_concepts": decision.get("knowledge_graph_update", [])
                    }
                )
        except Exception as e:
            error_msg = f"Erro no message_handler: {str(e)}"
            self.log(error_msg)
            try:
                await update.message.reply_text(f"⚠️ *Opa! Tive um pequeno problema interno:* \n`{str(e)}`", parse_mode='Markdown')
            except:
                pass

    async def error_handler(self, update: object, context: ContextTypes.DEFAULT_TYPE) -> None:
        self.log(f"Exception while handling an update: {context.error}")

    async def setup(self):
        """Inicializa a aplicação do bot."""
        if not self.token:
            return False
            
        self.application = Application.builder().token(self.token).build()
        self.application.add_handler(CommandHandler("start", self.start_handler))
        self.application.add_handler(MessageHandler(filters.TEXT | filters.PHOTO | filters.Document.IMAGE, self.message_handler))
        self.application.add_error_handler(self.error_handler)
        
        await self.application.initialize()
        await self.application.start()
        self.is_running = True
        print(f"Bot Application Initialized: {os.getenv('TELEGRAM_BOT_NAME')}")
        return True

    async def process_update(self, update_json):
        """Processa um update recebido via Webhook."""
        if not self.application:
            await self.setup()
            
        update = Update.de_json(update_json, self.application.bot)
        await self.application.process_update(update)

    def run(self):
        # Mantido para compatibilidade local se necessário
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.run_until_complete(self.setup())
        self.application.run_polling(drop_pending_updates=True)

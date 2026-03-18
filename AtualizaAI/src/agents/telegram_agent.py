import os
import asyncio
from datetime import datetime
from telegram import Bot, Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from dotenv import load_dotenv

load_dotenv()

class TelegramAgent:
    def __init__(self, orchestrator, gcs_client=None, kg_manager=None, vision_agent=None, audio_agent=None):
        self.token = os.getenv("TELEGRAM_BOT_TOKEN")
        self.orchestrator = orchestrator
        self.gcs_client = gcs_client
        self.kg_manager = kg_manager
        self.vision_agent = vision_agent
        self.audio_agent = audio_agent
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
                
                # Atualizar sumário de atividades recentes
                summary_path = "logs/telegram/latest_activity.json"
                summary = self.gcs_client.read_json(summary_path) or []
                new_entry = {
                    "user": data.get("user"),
                    "message": data.get("message"),
                    "timestamp": data.get("timestamp")
                }
                summary = [new_entry] + summary
                summary = summary[:10] # Manter apenas os 10 mais recentes
                self.gcs_client.upload_json(summary, summary_path)
            except Exception as e:
                print(f"Erro ao subir log para GCS: {e}")

    async def safe_reply(self, update: Update, text: str, parse_mode=None):
        """Envia mensagem garantindo que não ultrapasse o limite do Telegram."""
        # Garante resposta curta - max 4000 chars, sem truncamento apelativo
        if len(text) > 4000:
            text = text[:3900] + "..."
        
        try:
            await update.message.reply_text(text, parse_mode=parse_mode)
        except Exception:
            await update.message.reply_text(text.replace('*', '').replace('_', '').replace('`', ''))

    async def start_handler(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        user = update.effective_user.username or update.effective_user.first_name
        self.log(f"Comando /start recebido de @{user}")
        await update.message.reply_text("🤖 Flose AI Platform | Telegram Bridge ATIVO.\nEnvie um comando para o Orchestrator!")

    async def message_handler(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        try:
            user = update.effective_user.username or update.effective_user.first_name
            user_text = update.message.text or update.message.caption or ""
            
            has_photo = bool(update.message.photo)
            has_audio = bool(update.message.voice or update.message.audio)
            
            log_data = {
                "platform": "telegram",
                "user": user,
                "message": user_text,
                "has_photo": has_photo,
                "has_audio": has_audio,
                "timestamp": datetime.now().isoformat()
            }
            
            self.log(f"Mensagem de @{user}: {user_text} (Foto: {has_photo}, Audio: {has_audio})", data=log_data)
            
            await update.message.reply_chat_action(action="typing")
            
            # (Check de gatilhos movido para baixo para suportar áudio)

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
                    visual_context = "[Imagem recebida, mas Vision Agent offline]"
            
            audio_context = ""
            if has_audio:
                audio_obj = update.message.voice or update.message.audio
                audio_file = await audio_obj.get_file()
                
                # Extensão correta
                ext = "ogg" if update.message.voice else (audio_obj.file_name.split('.')[-1] if hasattr(audio_obj, 'file_name') else "mp3")
                audio_path = f"tmp_tg_audio_{datetime.now().strftime('%H%M%S')}.{ext}"
                
                await audio_file.download_to_drive(audio_path)
                self.log(f"Áudio baixado em: {audio_path}")
                
                if self.audio_agent:
                    try:
                        await update.message.reply_text("🎧 *Audio Agent processando sua voz...*", parse_mode='Markdown')
                    except:
                        await update.message.reply_text("🎧 Audio Agent processando sua voz...")
                    audio_context = self.audio_agent.analyze_audio(audio_path)
                    self.log(f"Análise de Áudio completa: {audio_context[:50]}...")
                else:
                    audio_context = "[Áudio recebido, mas Audio Agent offline]"
                
                if os.path.exists(audio_path):
                    os.remove(audio_path)

            # --- Detecta comando de diagrama Napkin (Texto ou Áudio) ---
            combined_input = (user_text + " " + audio_context).lower()
            napkin_triggers = ["diagrama", "desenho", "visual", "mapa", "flowchart", "mindmap", "esquema", "arquitetura"]
            if any(t in combined_input for t in napkin_triggers):
                # Se for áudio, usa a transcrição como prompt para o Napkin
                napkin_prompt = audio_context if (has_audio and not user_text) else user_text
                await self._handle_napkin_request(update, napkin_prompt)
                return

            # Process via Orchestrator
            full_command = f"Contexto Visual: {visual_context}\nContexto de Áudio: {audio_context}\n\nComando do Usuário: {user_text}"
            decision = self.orchestrator.process_command(full_command, image_path=image_path)
            
            # Limpeza da imagem após processar
            if image_path and os.path.exists(image_path):
                os.remove(image_path)

            # Se o Orchestrator falhou, responde de forma limpa
            if not decision or decision.get("error"):
                await self.safe_reply(update, "🤔 Não consegui entender o comando. Pode reformular?")
                return

            action = decision.get("action", "respond")
            reasoning = decision.get("reasoning", "")
            log_data["decision"] = decision

            # Reasoning Chain — visibilidade do raciocínio da IA
            if reasoning:
                reasoning_short = reasoning[:800]  # limita para não travar
                await self.safe_reply(update, f"🧠 *Reasoning Chain:*\n{reasoning_short}")
    
            if action == "respond":
                response = decision.get("response", "Processado com sucesso.")
                await self.safe_reply(update, f"💬 {response}")
                result = response
            
            elif action == "create_agent":
                result = self.orchestrator.execute_decision(decision)
                await self.safe_reply(update, f"🏗️ {result}")
            
            elif action == "generate_demand":
                result = self.orchestrator.execute_decision(decision)
                demand = decision.get("demand_info") or {}
                title = demand.get("title", "Nova demanda")
                await self.safe_reply(update, f"📝 Demanda registrada: {title}\n\n{result}")
    
            else: # execute
                result = self.orchestrator.execute_decision(decision)
                await self.safe_reply(update, f"⚙️ {result}")
            
            # --- NOVO: Auto-Renderização de Diagramas ---
            if isinstance(result, str) and "```mermaid" in result:
                import re
                mermaid_match = re.search(r"```mermaid\s*(.*?)\s*```", result, re.DOTALL)
                if mermaid_match:
                    mermaid_content = mermaid_match.group(1).strip()
                    self.log(f"Diagrama Mermaid detectado na resposta. Acionando Napkin...")
                    await asyncio.sleep(1) # Delay para mensagem chegar primeiro no TG
                    await self._handle_napkin_request(update, mermaid_content)

            # Sincroniza o log final (com a decisão) no GCS
            if self.gcs_client:
                filename_final = f"logs/telegram/decision_{datetime.now().strftime('%Y%m%d_%H%M%S_%f')}.json"
                self.gcs_client.upload_json(log_data, filename_final)
    
            # Atualiza o Knowledge Graph com novos conceitos aprendidos APENAS se houver execução real
            if self.kg_manager and decision.get("action") == "execute":
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
                await self.safe_reply(update, f"⚠️ Tive um problema interno. Tente novamente.")
            except:
                pass

    async def _handle_napkin_request(self, update: Update, user_text: str):
        """Gera um diagrama via Napkin AI, persiste no GCS e envia para o Telegram."""
        await update.message.reply_chat_action(action="upload_photo")
        await self.safe_reply(update, "🎨 Gerando seu diagrama e salvando no cofre da Flose AI... Aguarde!")
        
        try:
            from src.utils.napkin_client import NapkinClient
            napkin = NapkinClient()
            url = await napkin.generate_and_return_url(user_text)
            
            if url:
                import httpx
                async with httpx.AsyncClient(timeout=30.0) as client:
                    svg_resp = await client.get(url, headers={
                        "Authorization": f"Bearer {os.getenv('NAPKIN_API_KEY')}",
                        "Accept": "image/svg+xml"
                    })
                    if svg_resp.status_code == 200:
                        png_bytes = svg_resp.content
                        
                        # 1. Persistência no GCS (Não perder nada)
                        gcs_url = None
                        if self.gcs_client:
                            ts = datetime.now().strftime('%Y%m%d_%H%M%S')
                            gcs_path = f"visuals/diagrams/diagram_{ts}.png"
                            blob = self.gcs_client.bucket.blob(self.gcs_client._full_path(gcs_path))
                            blob.upload_from_string(png_bytes, content_type="image/png")
                            gcs_url = f"https://storage.googleapis.com/{self.gcs_client.bucket_name}/{self.gcs_client._full_path(gcs_path)}"
                            self.log(f"Diagrama persistido: {gcs_path}")

                        # 2. Enviar para Telegram (Como Foto!)
                        await update.message.reply_photo(
                            photo=png_bytes,
                            caption=f"📸 Diagrama gerado na Flose AI."
                        )

                        # 3. Registrar no Log de Atividades para aparecer no Dashboard
                        if self.gcs_client:
                            log_entry = {
                                "timestamp": datetime.now().isoformat(),
                                "user": update.effective_user.username or "telegram_user",
                                "message": f"Diagrama gerado: {user_text[:50]}...",
                                "type": "diagram_gen",
                                "visual_url": gcs_url
                            }
                            # Log individual
                            self.gcs_client.upload_json(log_entry, f"logs/executions/diag_{ts}.json")
                        return
            
            await self.safe_reply(update, "⚠️ Não consegui gerar o diagrama. Tente com uma descrição mais detalhada.")
        except Exception as e:
            import traceback
            traceback.print_exc()
            self.log(f"Erro Napkin: {str(e)}")
            await self.safe_reply(update, "⚠️ Serviço de diagramas indisponível no momento.")

    async def error_handler(self, update: object, context: ContextTypes.DEFAULT_TYPE) -> None:
        self.log(f"Exception while handling an update: {context.error}")

    async def setup(self):
        """Inicializa sem iniciar nenhum updater/polling interno."""
        if not self.token:
            return False
            
        # Usamos Application apenas para os handlers, mas NÃO damos start() 
        # para evitar que o updater interno tente fazer polling
        self.application = (
            Application.builder()
            .token(self.token)
            .updater(None)   # ← CRÍTICO: desativa o updater/polling interno
            .build()
        )
        self.application.add_handler(CommandHandler("start", self.start_handler))
        self.application.add_handler(MessageHandler(filters.TEXT | filters.PHOTO | filters.Document.IMAGE | filters.VOICE | filters.AUDIO, self.message_handler))
        self.application.add_error_handler(self.error_handler)
        
        await self.application.initialize()
        self.is_running = True
        print(f"✅ Bot inicializado em modo Webhook (sem polling): {os.getenv('TELEGRAM_BOT_NAME', 'Flose Bot')}")
        return True

    async def process_update(self, update_json):
        """Processa um update recebido via Webhook."""
        if not self.application:
            await self.setup()
            
        update = Update.de_json(update_json, self.application.bot)
        await self.application.process_update(update)

    def run(self):
        """Modo Polling (uso local). Remove webhook automaticamente para evitar conflito."""
        import asyncio
        import httpx

        # --- Garante que não haja webhook ativo ---
        if self.token:
            try:
                r = httpx.get(
                    f"https://api.telegram.org/bot{self.token}/deleteWebhook?drop_pending_updates=true",
                    timeout=10
                )
                if r.json().get("result"):
                    print("🔓 Webhook removido. Iniciando Polling local...")
            except Exception as e:
                print(f"Aviso: não foi possível verificar webhook: {e}")

        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.run_until_complete(self.setup())
        
        print("🤖 Bot rodando em modo Polling...")
        self.application.run_polling(drop_pending_updates=True)

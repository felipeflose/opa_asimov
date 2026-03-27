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
        self.start_time = datetime.now() # TASK-08: Uptime tracking
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

    async def dora_handler(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Retorna o resumo das métricas DORA."""
        try:
            user = update.effective_user.username or update.effective_user.first_name
            self.log(f"Comando /dora recebido de @{user}")
            
            summary = "Métricas DORA indisponíveis."
            if hasattr(self.orchestrator, 'dora'):
                data = self.orchestrator.dora.get_metrics_summary()
                summary = (
                    f"📈 *Engineering Metrics (DORA)*\n\n"
                    f"🚀 *Deploy Freq:* {data.get('deployment_frequency')}\n"
                    f"⏱️ *Lead Time:* {data.get('lead_time')}\n"
                    f"⚠️ *Failure Rate:* {data.get('change_failure_rate')}\n"
                    f"🔧 *MTTR:* {data.get('mttr')}"
                )
            
            await self.safe_reply(update, summary, parse_mode='Markdown')
        except Exception as e:
            self.log(f"Erro no dora_handler: {e}")
            await self.safe_reply(update, "⚠️ Erro ao buscar as métricas DORA.")

    async def status_handler(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Retorna o status atual: tarefas, custo e último agente."""
        try:
            user = update.effective_user.username or update.effective_user.first_name
            self.log(f"Comando /status recebido de @{user}")
            
            # 1. Tarefas Abertas
            open_tasks = 0
            if self.gcs_client:
                registry = self.gcs_client.read_json("demands/registry.json")
                if registry and "demands" in registry:
                    open_tasks = len([t for t in registry["demands"] if t.get("status") in ["Aberto", "OPEN", "pending"]])
            
            # 2. Custo do Dia
            cost_info = "Custo: Indisponível"
            if hasattr(self.orchestrator, 'finops'):
                cost_info = self.orchestrator.finops.get_finops_report()
            
            # 3. Último Agente Executado
            last_agent = "Nenhum"
            if self.gcs_client:
                prefix = f"users/{self.gcs_client.user_id}/logs/executions/"
                blobs = list(self.gcs_client.bucket.list_blobs(prefix=prefix))
                if blobs:
                    blobs.sort(key=lambda x: x.updated, reverse=True)
                    for blob in blobs[:10]: # Tenta nos últimos 10 logs
                        data = self.gcs_client.read_json(blob.name.replace(f"users/{self.gcs_client.user_id}/", ""))
                        if data and "agent" in data:
                            last_agent = data["agent"]
                            break
                        elif data and "user" in data and data.get("type") == "diagram_gen":
                            last_agent = f"DiagramAgent (via @{data['user']})"
                            break

            status_msg = (
                f"📊 *Status do Sistema*\n"
                f"📝 Tarefas Abertas: {open_tasks}\n"
                f"💰 {cost_info}\n"
                f"🤖 Último Agente: {last_agent}"
            )
            
            await self.safe_reply(update, status_msg, parse_mode='Markdown')
            
        except Exception as e:
            self.log(f"Erro no status_handler: {e}")
            await self.safe_reply(update, "⚠️ Erro ao buscar o status.")

    async def debug_handler(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Retorna informações técnicas de debug para admins."""
        try:
            user_id = str(update.effective_user.id)
            admins = os.getenv("ADMIN_USER_IDS", "").split(",")
            
            if user_id not in admins:
                await update.message.reply_text("⛔ Acesso negado. Este comando é restrito a administradores.")
                return

            self.log(f"Comando /debug recebido do admin {update.effective_user.username}")
            
            # 1. Status dos Serviços
            gcs_status = "✅ Online" if self.gcs_client and self.gcs_client.bucket else "❌ Offline"
            gemini_status = "✅ Online" if self.orchestrator and self.orchestrator.model else "❌ Offline"
            
            # 2. Última Execução Registrada
            last_exec = "Nenhuma encontrada"
            if self.gcs_client:
                try:
                    prefix = f"users/{self.gcs_client.user_id}/logs/executions/"
                    blobs = list(self.gcs_client.bucket.list_blobs(prefix=prefix, max_results=5))
                    if blobs:
                        blobs.sort(key=lambda x: x.updated, reverse=True)
                        data = self.gcs_client.read_json(blobs[0].name.replace(f"users/{self.gcs_client.user_id}/", ""))
                        if data:
                            last_exec = f"{data.get('agent', 'Unknown')} @ {data.get('timestamp', 'N/A')[:16]}"
                except: pass

            # 3. FinOps Consolidado de Hoje
            finops_today = "Sem dados"
            if hasattr(self.orchestrator, 'finops'):
                finops_today = self.orchestrator.finops.get_finops_report()

            # 4. Uptime e Contexto
            uptime = "N/A"
            if hasattr(self, 'start_time'):
                delta = datetime.now() - self.start_time
                uptime = str(delta).split(".")[0]

            debug_msg = (
                f"🛠️ *System Debug Info*\n\n"
                f"🗄️ *GCS:* {gcs_status}\n"
                f"🧠 *Gemini:* {gemini_status}\n"
                f"⏱️ *Uptime:* `{uptime}`\n"
                f"🚀 *Última Exec:* `{last_exec}`\n\n"
                f"💰 *FinOps Today:* \n`{finops_today}`"
            )
            
            await self.safe_reply(update, debug_msg, parse_mode='Markdown')
        except Exception as e:
            self.log(f"Erro no debug_handler: {e}")
            await self.safe_reply(update, "⚠️ Erro ao processar informações de debug.")

    async def incident_handler(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Registra um incidente via Telegram."""
        try:
            from src.storage.dora_manager import DoraManager
            dora = DoraManager(gcs_client=self.gcs_client)
            
            text = " ".join(context.args) if context.args else "Incidente reportado via Telegram"
            dora.log_incident(title=text, description=f"Reportado por @{update.effective_user.username}")
            
            await update.message.reply_text(f"🛑 *Incidente Registrado*\nO MTTR e a taxa de falha serão calculados no painel DORA.\nMsg: {text}", parse_mode='Markdown')
        except Exception as e:
            self.log(f"Erro no incident_handler: {e}")
            await update.message.reply_text("⚠️ Erro ao registrar incidente.")

    async def silence_handler(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Alterna o Modo Silencioso para o usuário."""
        try:
            user_id = str(update.effective_user.id)
            pref_path = f"users/{user_id}/preferences.json"
            
            prefs = {}
            if self.gcs_client:
                prefs = self.gcs_client.read_json(pref_path) or {}
            
            current = prefs.get("silent_mode", False)
            new_state = not current
            prefs["silent_mode"] = new_state
            
            if self.gcs_client:
                self.gcs_client.upload_json(prefs, pref_path)
            
            status = "ATIVADO 🤫" if new_state else "DESATIVADO 🔊"
            msg = f"Modo Silencioso {status}.\n"
            if new_state:
                msg += "Agora só responderei se você me marcar ou usar comandos."
            else:
                msg += "Responderei a todas as mensagens do chat."
            
            await update.message.reply_text(msg)
        except Exception as e:
            self.log(f"Erro no silence_handler: {e}")
            await update.message.reply_text("⚠️ Erro ao configurar modo silencioso.")

    async def conselho_handler(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Convoca o conselho de especialistas para uma pergunta estratégica."""
        try:
            user = update.effective_user.username or update.effective_user.first_name
            question = " ".join(context.args) if context.args else "Qual a melhor estratégia para o projeto hoje?"
            self.log(f"Comando /conselho recebido de @{user}: {question}")
            
            await update.message.reply_text("🏛️ *Convocando o Conselho de Especialistas da Flose AI...*", parse_mode='Markdown')
            await update.message.reply_chat_action(action="typing")
            
            # Chama o orquestrador para rodar em paralelo
            result = await self.orchestrator.run_conselho(question)
            
            await self.safe_reply(update, f"🏛️ *Veredito do Conselho*\n\n{result}", parse_mode='Markdown')
        except Exception as e:
            self.log(f"Erro no conselho_handler: {e}")
            await self.safe_reply(update, "⚠️ Erro ao buscar o conselho.")

        except Exception as e:
            self.log(f"Erro no conselho_handler: {e}")
            await self.safe_reply(update, "⚠️ Erro ao buscar o conselho.")

    async def cozinha_handler(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Alterna o Modo Cozinha (Modo Dev) para o usuário."""
        try:
            user_id = str(update.effective_user.id)
            arg = " ".join(context.args).lower() if context.args else ""
            pref_path = f"users/{user_id}/preferences.json"
            
            prefs = {}
            if self.gcs_client:
                prefs = self.gcs_client.read_json(pref_path) or {}
            
            if arg == 'off':
                prefs["dev_mode"] = False
                status = "DESATIVADO 🍽️"
                msg = f"Modo Cozinha {status}. Você voltou para o Orchestrator Padrão."
            else:
                prefs["dev_mode"] = True
                status = "ATIVADO 🥣"
                msg = f"Modo Cozinha {status}. Agora todas as suas perguntas serão respondidas pelo **DevAgent** especialista no codebase."
            
            if self.gcs_client:
                self.gcs_client.upload_json(prefs, pref_path)
            
            await update.message.reply_text(msg, parse_mode='Markdown')
        except Exception as e:
            self.log(f"Erro no cozinha_handler: {e}")
            await update.message.reply_text("⚠️ Erro ao configurar modo cozinha.")

    async def message_handler(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        try:
            if not update.message:
                return

            user_id = str(update.effective_user.id)
            user = update.effective_user.username or update.effective_user.first_name
            user_text = update.message.text or update.message.caption or ""
            
            # --- TASK-12/24: Modo Silencioso e Modo Dev ---
            is_silent = False
            is_dev = False
            if self.gcs_client:
                prefs = self.gcs_client.read_json(f"users/{user_id}/preferences.json") or {}
                is_silent = prefs.get("silent_mode", False)
                is_dev = prefs.get("dev_mode", False)
            
            bot_name = os.getenv("TELEGRAM_BOT_NAME", "Flose").lower()
            is_mentioned = bot_name in user_text.lower() or (update.message.reply_to_message and update.message.reply_to_message.from_user.id == context.bot.id)
            is_command = user_text.startswith("/")
            
            if is_silent and not (is_command or is_mentioned):
                return

            if is_dev and not is_command:
                from src.agents.dev_agent import DevAgent
                dev = DevAgent(gcs_client=self.gcs_client)
                await update.message.reply_chat_action(action="typing")
                result = dev.respond(user_text)
                await self.safe_reply(update, f"🥣 **Cozinha (DevAgent):**\n\n{result}", parse_mode='Markdown')
                return

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
            
            # --- TASK-17: Pipeline Multi-Agente (Texto ou Áudio) ---
            if " + " in combined_input and ("analise" in combined_input or "análise" in combined_input):
                parts = combined_input.replace("analise", "").replace("análise", "").split("+")
                agent_names = [p.strip() for p in parts]
                if len(agent_names) >= 2:
                    self.log(f"Pipeline sequencial detectada: {agent_names}")
                    await update.message.reply_text(f"⛓️ *Iniciando Pipeline Sequencial:* {' ➡️ '.join(agent_names)}", parse_mode='Markdown')
                    # Pega a transcrição total como prompt inicial
                    initial_prompt = audio_context if (has_audio and not user_text) else user_text
                    result = self.orchestrator.run_pipeline(agent_names, initial_prompt)
                    await self.safe_reply(update, result, parse_mode='Markdown')
                    return

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
                error_msg = decision.get("response") if decision else None
                if not error_msg:
                    error_msg = "🤔 Não consegui processar seu comando no momento. Por favor, tente reformular ou verifique a conexão."
                await self.safe_reply(update, error_msg)
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
                await self.safe_reply(update, f"🏗️ {result}", parse_mode='Markdown')
            
            elif action == "generate_demand":
                result = self.orchestrator.execute_decision(decision)
                demand = decision.get("demand_info") or {}
                title = demand.get("title", "Nova demanda")
                await self.safe_reply(update, f"📝 Demanda registrada: {title}\n\n{result}", parse_mode='Markdown')
    
            else: # execute
                result = self.orchestrator.execute_decision(decision)
                await self.safe_reply(update, f"⚙️ {result}", parse_mode='Markdown')
            
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
                # --- TASK-21: Cross-Analysis Persistence ---
                is_cross = has_photo and ("analise" in user_text.lower() or "avalie" in user_text.lower())
                if is_cross:
                    cross_data = {
                        "platform": "telegram",
                        "user": user,
                        "original_image": image_path,
                        "vision_context": visual_context,
                        "specialist_result": result,
                        "timestamp": datetime.now().isoformat()
                    }
                    ts = datetime.now().strftime('%Y%m%d_%H%M%S')
                    self.gcs_client.upload_json(cross_data, f"logs/cross_analysis/cross_{ts}.json")
                    self.log(f"Cross-Analysis salva em logs/cross_analysis/cross_{ts}.json")

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
            import traceback
            error_details = traceback.format_exc()
            error_msg = f"Erro no message_handler: {str(e)}\n{error_details}"
            self.log(error_msg)
            print(f"CRITICAL ERROR: {error_msg}")
            
            # Detectar falta de saldo/tokens (Erro 429 ResourceExhausted)
            if "ResourceExhausted" in str(e) or "spending cap" in str(e) or "429" in str(e):
                user_friendly_error = "🛑 **Saldo Insuficiente / Cota Excedida**\n\nNossos tokens (ou orçamento do GCP) acabaram para este ciclo ou o projeto atingiu o teto de faturamento. Por favor, verifique o Console Billing do GCP."
            else:
                user_friendly_error = "⚠️ Tive um problema interno técnico. Tente novamente."

            try:
                await self.safe_reply(update, user_friendly_error)
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
        """Inicializa a aplicação do Telegram em modo Webhook."""
        if not self.token:
            print("⚠️ TELEGRAM_BOT_TOKEN não configurado!")
            return

        self.application = Application.builder().token(self.token).build()

        # Handlers
        self.application.add_handler(CommandHandler("start", self.start_handler))
        self.application.add_handler(CommandHandler("status", self.status_handler))
        self.application.add_handler(CommandHandler("dora", self.dora_handler))
        self.application.add_handler(CommandHandler("debug", self.debug_handler)) # TASK-08
        self.application.add_handler(CommandHandler("incidente", self.incident_handler)) # DORA Refinement
        self.application.add_handler(CommandHandler("silencio", self.silence_handler)) # TASK-12
        self.application.add_handler(CommandHandler("conselho", self.conselho_handler)) # TASK-20
        self.application.add_handler(CommandHandler("cozinha", self.cozinha_handler)) # TASK-24
        self.application.add_handler(MessageHandler(filters.ALL & ~filters.COMMAND, self.message_handler))
        
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

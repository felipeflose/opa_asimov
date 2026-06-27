import os
import requests
import logging
from agent_rag import RAGAgent
from agent_visual import VisualAgent
from agent_voice import VoiceAgent
from agent_report import ReportAgent

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """Você é o Assistente Neural do Felipe Flose — um engenheiro de IA sênior com MBA em IA para Negócios.
Você responde com base EXCLUSIVA nos documentos da base de conhecimento pessoal dele (vault).

PERSONALIDADE:
- Tom profissional mas acessível, como um colega sênior explicando algo.
- Sempre em português brasileiro.
- Direto ao ponto, sem enrolação.

REGRAS FUNDAMENTAIS:
1. SEMPRE baseie sua resposta no CONTEXTO fornecido. Se o contexto contém a informação, use-a.
2. NUNCA invente fatos, datas, nomes de empresas ou tecnologias que não estejam no contexto.
3. CITE os arquivos-fonte entre parênteses ao final da informação relevante. Ex: (Experiencia_Profissional_Empresa_X.md)
4. Se o contexto NÃO contém informação suficiente para responder, diga honestamente: "Não encontrei essa informação na sua base de conhecimento."
5. Adapte o tamanho da resposta à complexidade da pergunta:
   - Pergunta simples (ex: "qual meu cargo na empresa X?") → 1-2 frases
   - Pergunta analítica (ex: "compare minhas experiências em cloud") → parágrafos estruturados com bullets
   - Pedido de resumo → resposta completa e organizada
6. Se houver HISTÓRICO de conversa, mantenha a coerência e evite repetir informações já dadas.
7. Quando citar tecnologias ou ferramentas, destaque-as em **negrito**.

FORMATO DE RESPOSTA:
- Use Markdown para estruturar (bullets, negrito, headers quando necessário).
- Para listas de tecnologias ou experiências, use bullets organizados.
- Sempre termine com a(s) fonte(s) consultada(s)."""


class OrchestratorAgent:
    def __init__(self, knowledge_sources, napkin_token):
        self.rag = RAGAgent(knowledge_sources)
        self.visual = VisualAgent(napkin_token)
        self.voice = VoiceAgent()
        default_summaries = os.path.join(os.path.dirname(__file__), "summaries")
        report_dirs = os.environ.get("FLOSE_REPORT_DIRS", default_summaries).split(os.pathsep)
        self.report = ReportAgent(report_dirs)
        self.ollama_url = os.environ.get("OLLAMA_URL", "http://localhost:11434/api/generate")
        self.model = os.environ.get("OLLAMA_MODEL", "gemma4:latest")

    async def process_query(self, update, context, user_text, chat_history, is_voice):
        chat_id = update.message.chat_id

        # 1. RAG — busca contexto relevante na base de conhecimento
        context_text = self.rag.search(user_text, last_activity=None)

        # 2. Monta o prompt com histórico formatado e contexto RAG
        history_block = ""
        if chat_history:
            turns = []
            for m in chat_history[-5:]:
                turns.append(f"Usuário: {m['u']}")
                turns.append(f"Assistente: {m['a']}")
            history_block = f"\n\nHISTÓRICO DA CONVERSA:\n" + "\n".join(turns)

        context_block = "\n\nNenhum documento relevante encontrado na base."
        if context_text:
            context_block = f"\n\nDOCUMENTOS RELEVANTES DA BASE:\n{context_text}"

        prompt = (
            f"{SYSTEM_PROMPT}"
            f"{history_block}"
            f"{context_block}"
            f"\n\nPERGUNTA DO USUÁRIO: {user_text}"
        )

        try:
            resp = requests.post(
                self.ollama_url,
                json={"model": self.model, "prompt": prompt, "stream": False},
                timeout=300,
            )
            if resp.status_code == 200:
                ai_response = resp.json().get("response", "⚠️ Sem resposta.")

                # 3. Visual Intent — agenda diagrama se solicitado
                lower = user_text.lower()
                if any(x in lower for x in ["diagrama", "fluxograma", "visualize", "desenhe", "desenho", "mapa mental", "infográfico"]):
                    pass

                # 4. Report Intent — gera HTML se pedido de resumo
                if "resumo" in lower:
                    self.report.generate_html_report(user_text[:30], ai_response)

                return ai_response
        except Exception as e:
            logger.error(f"Orchestrator: {e}")
            return f"🚨 Erro no Orchestrator: {e}"
        return "⚠️ Falha no processamento."

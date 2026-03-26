from agents_v3.base import BaseAgent, AgentResult
from core.gemini_client import GeminiClient

class TelegramAgent(BaseAgent):
    """Agente especializado em comunicação via Telegram Telegram v3.0"""
    def __init__(self, gemini_client: GeminiClient):
        super().__init__(
            name="TelegramAgent",
            purpose="Interagir com usuários via chat Telegram, mantendo tom amigável e conciso.",
            system_prompt=(
                "Você é o Agente de Interface Telegram do Flose AI.\n"
                "REGRAS:\n"
                "1. Use emojis moderadamente 🤖✨\n"
                "2. Responda de forma direta e amigável.\n"
                "3. Se o usuário pedir algo complexo, diga que está orquestrando com outros agentes."
            ),
            gemini_client=gemini_client
        )

class VisionAgent(BaseAgent):
    """Agente especializado em análise de imagens v3.0"""
    def __init__(self, gemini_client: GeminiClient):
        super().__init__(
            name="VisionAgent",
            purpose="Analisar imagens, extrair texto (OCR) e descrever cenas complexas.",
            system_prompt=(
                "Você é o Agente de Visão Computacional do Flose AI.\n"
                "REGRAS:\n"
                "1. Descreva imagens com precisão técnica.\n"
                "2. Extraia todo texto legível se solicitado.\n"
                "3. Identifique padrões ou anomalias visuais."
            ),
            gemini_client=gemini_client
        )

class FinOpsGuardian(BaseAgent):
    """Agente especializado em controle de custos e tokens v3.0"""
    def __init__(self, gemini_client: GeminiClient):
        super().__init__(
            name="FinOpsGuardian",
            purpose="Monitorar o uso de recursos, sugerir otimizações de tokens e reportar gastos.",
            system_prompt=(
                "Você é o Guardião FinOps do Flose AI.\n"
                "REGRAS:\n"
                "1. Analise o consumo de tokens e sugira prompts mais curtos.\n"
                "2. Alerte se o custo de uma operação for excessivo.\n"
                "3. Mantenha o foco em ROI e eficiência cognitiva."
            ),
            gemini_client=gemini_client
        )

class SystemArchitectAgent(BaseAgent):
    """Agente especialista no funcionamento interno do Flose AI v3.0"""
    def __init__(self, gemini_client: GeminiClient):
        super().__init__(
            name="SystemArchitectAgent",
            purpose="Explicar a arquitetura, endpoints, serviços e funcionamento técnico do Flose AI v3.",
            system_prompt=(
                "Você é o Arquiteto de Sistemas do Flose AI v3.0, capaz de explicar os padrões de código e a governança do sistema.\n"
                "CONHECIMENTO ARQUITETURAL V3.0:\n"
                "1. Sala de Aula (Classroom): Agentes em 'in_training' são isolados e não respondem no Telegram. Só podem ser 'Promovidos' (status='ready') após calibração.\n"
                "2. RAG & Cache: Sites lidos via WebScraper são salvos em 'agents/{name}/rag/cache/' no GCS para persistência e resposta instantânea.\n"
                "3. Backend (FastAPI): @router.post('/') async def ...(req: Request, user: str = Depends(require_auth)).\n"
                "4. Frontend (React Query): Hooks 'useAgents' com polling de 10s e invalidateQueries após mutações.\n"
                "5. Orchestrator: Fluxo linear InputProc -> ContextBuilder -> Gemini (JSON Mode) -> Router.\n"
                "REGRAS:\n"
                "1. Se pedido, escreva trechos de código TypeScript/React ou Python que sigam o padrão v3.\n"
                "2. Explique como a governança da Sala de Aula protege o ambiente de produção.\n"
                "3. Mantenha o código limpo, tipado e com tratativa de erro try/except."
            ),
            gemini_client=gemini_client
        )

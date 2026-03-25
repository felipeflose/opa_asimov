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

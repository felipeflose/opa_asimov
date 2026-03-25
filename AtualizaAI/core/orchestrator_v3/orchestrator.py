import re
from typing import Optional
import structlog

logger = structlog.get_logger()

class InputProcessor:
    """Sanitiza e valida o input do usuário"""
    def __init__(self, max_chars: int = 4000):
        self.max_chars = max_chars

    def process(self, text: str) -> str:
        if not text:
            return ""
            
        # Sanitização básica (remover espaços extras, limitar chars)
        sanitized = text.strip()[:self.max_chars]
        
        # Log de input cru (opcional, cuidado com PII)
        # logger.info("input_processed", length=len(sanitized))
        
        return sanitized

class ContextBuilder:
    """Monta o contexto (histórico, memória, etc) para o prompt"""
    def __init__(self, max_history: int = 4):
        self.max_history = max_history

    def build(self, current_input: str, history: Optional[list] = None) -> str:
        context = "SISTEMA: Você é o Flose AI, o Orquestrador Central.\n"
        context += "DIRETRIZ: Analise o input e decida a melhor ação em JSON.\n\n"
        
        if history:
            # Pega as últimas N interações
            recent = history[-self.max_history:]
            for msg in recent:
                role = "USER" if msg["role"] == "user" else "AI"
                context += f"{role}: {msg['content']}\n"
        
        context += f"USER: {current_input}\n"
        return context

class DecisionParser:
    """Valida e converte a resposta da IA em objetoDecisionResult"""
    def __init__(self):
        # Regex para capturar JSON caso a IA envie texto extra
        self.json_pattern = re.compile(r"\{.*\}", re.DOTALL)

    def parse(self, ai_text: str) -> dict:
        try:
            match = self.json_pattern.search(ai_text)
            if not match:
                raise ValueError("JSON não encontrado na resposta")
                
            import json
            decision = json.loads(match.group())
            
            # Validação básica de campos
            required = ["action", "response"]
            if not all(k in decision for k in required):
                raise ValueError(f"Campos obrigatórios ausentes: {required}")
                
            return decision
        except Exception as e:
            logger.error("decision_parse_error", text=ai_text, error=str(e))
            # Fallback seguro
            return {
                "action": "reply",
                "response": "Houve um erro técnico ao processar sua decisão. Vou responder diretamente.",
                "error": str(e)
            }

class ActionRouter:
    """Executa a ação decidida e retorna o resultado final ao usuário"""
    def __init__(self, agent_registry: Optional[any] = None):
        self.agent_registry = agent_registry

    async def route(self, decision: dict) -> str:
        action = decision.get("action", "reply")
        response = decision.get("response", "")
        agent_name = decision.get("agent_involved")

        if action == "delegate" and agent_name:
            # Futura implementação de execução de agentes v3
            # self.agent_registry.run_agent(agent_name)
            return f"{response}\n(Delegando para {agent_name}...)"
        
        return response

class OrchestratorV3:
    """Orquestrador Central: Coordena processamento, contexto, IA e execução"""
    def __init__(self, input_proc: InputProcessor, context_builder: ContextBuilder, gemini: any, parser: DecisionParser, router: ActionRouter):
        self.input_proc = input_proc
        self.context_builder = context_builder
        self.gemini = gemini
        self.parser = parser
        self.router = router

    async def process_command(self, text: str, history: Optional[list] = None, image_path: Optional[str] = None) -> dict:
        # 1. Input Processing
        clean_text = self.input_proc.process(text)
        
        # 2. Context Building
        prompt = self.context_builder.build(clean_text, history)
        
        # 3. LLM Generation
        # Definimos o formato JSON no system_instruction para Gemini v3
        system_instruction = (
            "Responda SEMPRE em JSON válido.\n"
            "Formato: {\"action\": \"reply|delegate|search\", \"response\": \"...\", \"agent_involved\": \"optional_name\"}"
        )
        
        ai_resp = await self.gemini.generate_text(prompt, system_instruction=system_instruction, image_path=image_path)
        
        # 4. Decision Parsing
        decision = self.parser.parse(ai_resp.text)
        
        # 5. Action Routing
        final_message = await self.router.route(decision)
        
        # Metrics & Log
        result = {
            "message": final_message,
            "decision": decision,
            "metrics": {
                "tokens_in": ai_resp.tokens_in,
                "tokens_out": ai_resp.tokens_out,
                "cost_usd": ai_resp.cost_usd
            }
        }
        
        logger.info("command_executed", action=decision.get("action"))
        return result

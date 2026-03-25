import google.generativeai as genai
import os
import re
import json as _json

class DebateAgent:
    """
    Para decisões críticas: dois agentes debatem, um juiz decide.
    Ativar quando: infra_cost > 1.0 ou action == 'execute' com budget_approved.
    """
    def __init__(self):
        self.api_key = os.getenv("GEMINI_API_KEY")
        if self.api_key:
            genai.configure(api_key=self.api_key)
        self.model = genai.GenerativeModel('gemini-2.5-flash')

    def debate(self, question: str, agents: list[str] = None, context: str = "") -> dict:
        """Sessão de debate expandida com N especialistas (TASK-18)."""
        arguments = {}
        
        if not agents:
            # Fallback Pro/Con se não houver lista de agentes
            pro_prompt = f"Você defende que a seguinte ação DEVE ser feita. Argumente em 3 pontos curtos.\nContexto: {context}\nAção: {question}"
            arguments["Pro-Execution"] = self.model.generate_content(pro_prompt).text.strip()

            con_prompt = f"Você defende que a seguinte ação NÃO deve ser feita agora. Argumente em 3 pontos curtos.\nContexto: {context}\nAção: {question}"
            arguments["Con-Execution"] = self.model.generate_content(con_prompt).text.strip()
        else:
            # Cada agente da lista defende seu ponto baseado em sua persona
            from src.storage.gcs_client import GCSClient
            project_id = os.getenv("GCP_PROJECT_ID")
            bucket_name = f"flose-ai-platform-{project_id}"
            gcs = GCSClient(bucket_name, project_id=project_id)
            registry = gcs.read_json("agents/registry.json") or {"agents": []}
            
            for name in agents:
                agent_data = next((a for a in registry.get("agents", []) if a['agent_name'].lower() == name.lower()), None)
                persona = agent_data['system_prompt'] if agent_data else "Você é um especialista em IA da Flose."
                
                arg_prompt = f"PERSONA: {persona}\n\nSITUAÇÃO: {question}\nCONTEXTO: {context}\n\nArgumente sobre a situação acima sob a ótica da sua especialidade em no máximo 3 pontos curtos."
                try:
                    resp = self.model.generate_content(arg_prompt).text.strip()
                    arguments[name] = resp
                except:
                    arguments[name] = "Falha técnica na argumentação do especialista."

        # Juiz: decide baseado em todas as perspectivas
        args_str = ""
        for name, arg in arguments.items():
            args_str += f"\n👉 PERSPECTIVA {name}:\n{arg}\n"

        judge_prompt = f"""
        Você é o Juiz Supremo da Flose AI Platform. Decida o futuro da seguinte ação baseando-se nos argumentos dos especialistas abaixo.
        
        AÇÃO PROPOSTA:
        {question}
        
        ARGUMENTOS:
        {args_str}
        
        Responda APENAS com um JSON estrito no formato:
        {{
            "decision": "proceed | abort | modify",
            "winner_agent": "nome do agente com argumento mais forte",
            "reasoning": "conclusão curta e direta",
            "confidence": 0.0_to_1.0
        }}
        """
        try:
            verdict_resp = self.model.generate_content(judge_prompt).text.strip()
            
            # Limpeza de JSON robusta
            raw = verdict_resp
            if "```json" in raw: raw = raw.split("```json")[1].split("```")[0].strip()
            elif "```" in raw: raw = raw.split("```")[1].split("```")[0].strip()
            
            match = re.search(r'\{.*\}', raw, re.DOTALL)
            parsed = _json.loads(match.group()) if match else {"decision": "proceed", "confidence": 0.5, "reasoning": "Erro parsear juiz."}
            
            return {
                "arguments": arguments,
                "verdict": parsed
            }
        except Exception as e:
            return {"error": str(e), "verdict": {"decision": "proceed", "confidence": 0.3, "reasoning": f"Erro crítico no juiz: {e}"}}

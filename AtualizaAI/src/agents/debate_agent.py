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
        self.model = genai.GenerativeModel('gemini-1.5-flash')

    def debate(self, question: str, context: str = "") -> dict:
        # Agente A: perspectiva favorável
        pro_prompt = f"Você defende que a seguinte ação DEVE ser feita. Argumente em 3 pontos curtos.\nContexto: {context}\nAção: {question}"
        pro = self.model.generate_content(pro_prompt).text.strip()

        # Agente B: perspectiva crítica
        con_prompt = f"Você defende que a seguinte ação NÃO deve ser feita agora. Argumente em 3 pontos curtos.\nContexto: {context}\nAção: {question}"
        con = self.model.generate_content(con_prompt).text.strip()

        # Juiz: decide baseado nos dois lados
        judge_prompt = f"""
        Você é o juiz da Flose AI Platform. Analise os dois lados e decida se devemos seguir com a execução.
        
        A FAVOR:
        {pro}
        
        CONTRA:
        {con}
        
        Responda APENAS com JSON no formato:
        {{"decision": "proceed|abort|modify", "reasoning": "sua conclusão", "confidence": 0.0_to_1.0}}
        """
        verdict_resp = self.model.generate_content(judge_prompt).text.strip()

        # Limpeza de JSON robusta
        raw = verdict_resp
        if "```json" in raw: raw = raw.split("```json")[1].split("```")[0].strip()
        elif "```" in raw: raw = raw.split("```")[1].split("```")[0].strip()
        
        match = re.search(r'\{.*\}', raw, re.DOTALL)
        parsed = _json.loads(match.group()) if match else {"decision": "proceed", "confidence": 0.5, "reasoning": "Erro ao parsear veredito."}

        return {"pro": pro, "con": con, "verdict": parsed}

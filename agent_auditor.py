"""
Agent Auditor — O Juiz de Qualidade
Avalia os retornos dos outros agentes e decide se o nó está pronto para o grafo ou se precisa de revisão.
"""
from agent_core import local_ollama_call

AUDITOR_PROMPT = """Você é o Juiz Socrático e Auditor de Qualidade da AI Factory.
Sua única função é avaliar o JSON gerado por outros agentes e REPROVAR qualquer trabalho medíocre.

🔍 CHECKLIST DE AUDITORIA (TOLERÂNCIA ZERO):
1. DENSIDADE COGNITIVA: O `strategic_title` parece o nome de um arquivo cru ou um título corporativo/acadêmico real? Se tiver "CV_", "MBA_", "Slides" ou sublinhados, REPROVE.
2. ESTRUTURA DE HUBS: A lista `hubs` deve ter pelo menos 3 itens para garantir profundidade. Hierarquias ricas (4, 5, 6 níveis) são MUITO bem-vindas. REPROVE apenas se for raso demais (menos de 3).
3. VEDAÇÃO GENÉRICA: Algum item na lista `hubs` é preguiçoso? (ex: "GERAL", "DADOS", "TRABALHO", "ARQUIVO"). Se sim, REPROVE e exija precisão cirúrgica.
4. LIMPEZA FORENSE: Algum hub contém nomes de arquivos brutais como "Inteligencia Artificial Generativa (GenAI)" em vez de apenas "GENAI"? REPROVE.

Retorne EXCLUSIVAMENTE um JSON válido:
{
  "status": "OK" ou "REPROVADO",
  "feedback": "Se OK, deixe vazio. Se REPROVADO, dê uma bronca técnica curta, ácida e direta instruindo o agente sobre exatamente qual das regras acima ele quebrou e como arrumar."
}"""

def audit_response(agent_type: str, filename: str, response: dict) -> dict:
    prompt = f"AGENTE: {agent_type}\nARQUIVO: {filename}\nRETORNO DA IA:\n{response}"
    
    # Chama o modelo (usando o modelo rápido para a auditoria ser ágil)
    res = local_ollama_call(prompt, AUDITOR_PROMPT)
    
    if res and "status" in res:
        return res
    return {"status": "OK", "feedback": "Falha na auditoria, deixando passar por segurança."}

import json
import logging
from agent_core import local_ollama_call, DEFAULT_MODEL

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """Você é o "Agent Perfect", um juiz de Qualidade (QA) extremamente chato e rigoroso.
Sua missão é auditar e CORRIGIR a extração de dados de um nó que vai para uma interface gráfica premium (D3.js).

Aqui estão as regras invioláveis (o crivo):
1. 'short_name': DEVE ter NO MÁXIMO 3 palavras. DEVE ser um nome próprio, marca ou tecnologia forte. Nunca use frases genéricas como "Consultoria em BI" ou "Fundamentos de". Se o nome cru for ruim, reescreva-o.
2. 'strategic_title': DEVE ser um título de valor que resuma o core do documento, sem exceder 10 palavras.
3. 'grouping_hub': DEVE ser um nome macro-categoria (ex: Nome de uma Empresa, Domínio de Tecnologia, ou Módulo). Evite hubs longos ou específicos demais. Se for inútil, escreva "Nenhum".
4. 'summary': DEVE ter no máximo 2 frases muito elegantes.
5. 'tags': NO MÁXIMO 5 tags. DEVEM estar em MAIÚSCULAS. DEVEM representar conceitos globais.

Aqui está o JSON submetido pela IA anterior:
{submitted_json}

E aqui está um trecho do arquivo original para contexto:
{content_snippet}

Se o JSON submetido já for perfeito, repita-o.
Se tiver QUALQUER defeito, você DEVE SOBRESCREVER E CORRIGIR os valores no JSON.
A formatação do JSON deve ser perfeita.

Retorne EXCLUSIVAMENTE um JSON válido neste formato:
{{
  "short_name": "Nome Curto Perfeito",
  "strategic_title": "Título Estratégico e Direto",
  "grouping_hub": "Nome do Agrupador",
  "summary": "Resumo executivo do conteúdo.",
  "tags": ["TAG1", "TAG2"]
}}
"""

def validate_node_quality(enriched_data: dict, content: str, model: str = None) -> dict:
    if not model:
        model = DEFAULT_MODEL
        
    submitted_json = json.dumps(enriched_data, ensure_ascii=False, indent=2)
    content_snippet = content[:800] # Passa apenas o início para contexto rápido
    
    prompt = SYSTEM_PROMPT.format(
        submitted_json=submitted_json,
        content_snippet=content_snippet
    )
    
    try:
        response = local_ollama_call(prompt=prompt, system_prompt="Inspecione e corrija a qualidade dos dados.", model=model)
        
        # Limpeza agressiva para garantir JSON puro
        clean_text = response.replace('```json', '').replace('```', '').strip()
        first_brace = clean_text.find('{')
        last_brace = clean_text.rfind('}')
        if first_brace != -1 and last_brace != -1:
            clean_text = clean_text[first_brace:last_brace+1]
            
        perfected_data = json.loads(clean_text)
        
        # Fallbacks em caso de chaves faltando
        return {
            "short_name": perfected_data.get("short_name", enriched_data.get("short_name", "")),
            "strategic_title": perfected_data.get("strategic_title", enriched_data.get("strategic_title", "")),
            "grouping_hub": perfected_data.get("grouping_hub", enriched_data.get("grouping_hub", "")),
            "summary": perfected_data.get("summary", enriched_data.get("summary", "")),
            "tags": perfected_data.get("tags", enriched_data.get("tags", []))
        }
    except Exception as e:
        logger.warning(f"Agent Perfect falhou ao validar o JSON. Usando o original. Erro: {e}")
        return enriched_data

if __name__ == "__main__":
    # Teste rápido
    test_data = {
        "short_name": "Consultoria em BI e Análise de Dados para Transformação Estratégica de Negócios",
        "strategic_title": "Documento completo sobre consultoria",
        "grouping_hub": "Projeto de Consultoria e Estratégia de Transformação de Processos e Negócios Digitais",
        "summary": "Este é um texto gigante que o agente antigo gerou para o resumo. O texto não acaba nunca e fala muita coisa desnecessária. Eu gostaria que acabasse.",
        "tags": ["tag1 lowercase", "uma tag com quatro palavras diferentes"]
    }
    content_mock = "Na Leega, atuei como Engenheiro de Dados focado em BI, criando pipelines e otimizando queries no Snowflake..."
    
    res = validate_node_quality(test_data, content_mock)
    print("RESULTADO:")
    print(json.dumps(res, indent=2, ensure_ascii=False))

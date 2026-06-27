import os
import logging
import json
from typing import Optional
from agent_core import local_ollama_call, _extract_sample

logger = logging.getLogger(__name__)

# Cache da taxonomia para não ler do disco 72 vezes
_cached_hubs = None
_cached_tags = None

def _load_taxonomy():
    global _cached_hubs, _cached_tags
    if _cached_hubs is not None:
        return _cached_hubs, _cached_tags
        
    TAXONOMY_FILE = os.path.join(os.path.dirname(__file__), "taxonomy_map.json")
    if os.path.exists(TAXONOMY_FILE):
        try:
            with open(TAXONOMY_FILE, 'r', encoding='utf-8') as f:
                tax = json.load(f)
                _cached_hubs = tax.get("grouping_hubs", [])
                _cached_tags = tax.get("global_tags", [])
        except Exception as e:
            logger.warning(f"Erro ao carregar taxonomy_map.json: {e}")
            _cached_hubs, _cached_tags = [], []
    else:
        _cached_hubs, _cached_tags = [], []
        
    return _cached_hubs, _cached_tags

SYSTEM_PROMPT = """Você é um especialista em análise de conteúdo da AI Factory.
Sua missão é extrair metadados estruturados de um arquivo para um grafo de conhecimento.

ARQUIVO: {filename}
CATEGORIA: {category} ({node_type})

** DICIONÁRIO GLOBAL DISPONÍVEL **
Grouping Hubs Globais Permitidos: {hubs}
Tags Globais Sugeridas: {tags}

Extraia as seguintes informações:
1. "short_name": Um nome BEM CURTO (máx 3 palavras) para o nó. Ex: "Talent Group", "n8n", "Engenharia de Prompts".
2. "strategic_title": Um título descritivo do valor real do arquivo (máx 10 palavras).
3. "grouping_hub": VOCÊ DEVE ESCOLHER EXATAMENTE UM DOS "Grouping Hubs Globais Permitidos" acima que melhor represente este arquivo. Se nenhum se encaixar perfeitamente, escolha o mais próximo ou escreva "Nenhum". NUNCA INVENTE UM HUB NOVO!
4. "summary": Resumo executivo de até 2 frases sobre o conteúdo.
5. "tags": Uma lista de até 5 palavras-chave. Priorize as "Tags Globais Sugeridas" acima, mas pode criar novas se for absolutamente necessário.

Retorne EXCLUSIVAMENTE um JSON válido neste formato:
{{
  "short_name": "Nome Curto",
  "strategic_title": "Título Estratégico Longo",
  "grouping_hub": "Nome Exato do Dicionário",
  "summary": "Resumo executivo do conteúdo.",
  "tags": ["TAG1", "TAG2"]
}}
"""

def enrich_node(content: str, filename: str, node_type: str, category: str, model: str = None) -> dict:
    hubs, tags = _load_taxonomy()
    
    sample = _extract_sample(content, max_chars=3000)
    prompt = f"ARQUIVO: {filename}\nCONTEÚDO:\n{sample}"
    
    hubs_str = ", ".join(hubs) if hubs else "Use seu melhor julgamento"
    tags_str = ", ".join(tags) if tags else "Use seu melhor julgamento"
    
    sys_prompt = SYSTEM_PROMPT.format(
        filename=filename, 
        category=category, 
        node_type=node_type,
        hubs=hubs_str,
        tags=tags_str
    )

    res = local_ollama_call(prompt, sys_prompt, model=model)
    if res and isinstance(res, dict) and "strategic_title" in res:
        return {
            "short_name": res.get("short_name", filename.replace(".md", "")),
            "strategic_title": res.get("strategic_title", filename.replace(".md", "")),
            "grouping_hub": res.get("grouping_hub", ""),
            "summary": res.get("summary", ""),
            "tags": res.get("tags", [])
        }
        
    # Fallback
    return {
        "short_name": filename.replace(".md", "")[:20],
        "strategic_title": filename.replace(".md", ""),
        "grouping_hub": "",
        "summary": "Conteúdo extraído via fallback automático.",
        "tags": []
    }

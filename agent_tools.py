"""
Agent Tools — Especialista Técnico
Mapeia e classifica o stack tecnológico do Felipe Flose.
Cria clusters granulares por domínio técnico.
"""
import logging
import re
from typing import Optional

from agent_core import local_ollama_call, _extract_sample, MAX_RETRIES, GENERIC_CLUSTERS

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """Você é o especialista técnico da AI Factory. Mapeie tecnologias e habilidades técnicas para montar um grafo de conhecimento.

REGRAS DE EXTRAÇÃO:
1. **CATEGORIA (category)**: Grande área técnica. Procure após "Área:" ou infira do conteúdo. Ex: "CLOUD COMPUTING", "DATA ENGINEERING", "ARTIFICIAL INTELLIGENCE".
2. **TÍTULO ESTRATÉGICO (strategic_title)**: Descreva a habilidade técnica principal. Não use o nome do arquivo.
   Ex: "Orquestração de Pipelines de Dados com Apache Airflow em GCP"
3. **HIERARQUIA DE HUBS (hubs)**: 3 a 5 níveis de abstração técnica:
   - Nível 1: Domínio (Ex: "DADOS", "INTELIGÊNCIA ARTIFICIAL", "INFRAESTRUTURA")
   - Nível 2: Paradigma/Plataforma (Ex: "CLOUD COMPUTING", "DEEP LEARNING", "ETL")
   - Nível 3: Ecossistema (Ex: "GCP", "AWS", "LANGCHAIN")
   - Nível 4+: Especializações (Ex: "DATA WAREHOUSING", "RAG", "MLOPS")
4. **TOOLS**: Sub-ferramentas ou tecnologias complementares citadas (Ex: BigQuery dentro de GCP, Vertex AI). Liste em MAIÚSCULAS.

PROIBIÇÕES:
- NUNCA use "HABILIDADE", "ÁREA", "CV", "TECNOLOGIA", "FERRAMENTA", "GERAL" como hub.
- NUNCA use nomes de arquivos como hub.
- Hubs devem ser termos técnicos específicos em MAIÚSCULAS.
- Prefira 3-5 hubs focados em vez de 6+ genéricos.

EXEMPLO DE SAÍDA:
{"strategic_title": "Plataforma de ML End-to-End com Vertex AI e BigQuery", "category": "INTELIGÊNCIA ARTIFICIAL", "hubs": ["INTELIGÊNCIA ARTIFICIAL", "MLOPS", "GCP", "VERTEX AI"], "tools": ["BIGQUERY", "CLOUD FUNCTIONS", "DOCKER", "KUBEFLOW"], "reasoning": "Proficiência avançada em MLOps no GCP, com pipelines automatizados de treinamento e deploy."}

Retorne EXCLUSIVAMENTE um JSON válido neste formato."""

REQUIRED_FIELDS = {"strategic_title", "hubs", "reasoning", "category"}



def process_tools(content: str, filename: str, directive: str = "", model: str = None) -> Optional[dict]:
    sample = _extract_sample(content)
    dir_block = f"\nDIRETRIZ ESTRATÉGICA DO SCOUT: {directive}\n" if directive else ""
    prompt = f"TECNOLOGIA: {filename}{dir_block}\nDESCRIÇÃO:\n{sample}"

    for attempt in range(1, MAX_RETRIES + 1):
        res = local_ollama_call(prompt, SYSTEM_PROMPT, model=model)
        if res and REQUIRED_FIELDS.issubset(res.keys()):
            # Valida se o primeiro hub não é genérico
            if res["hubs"] and res["hubs"][0].lower() in GENERIC_CLUSTERS:
                logger.warning(f"Tools: hub generico detectado, retry {attempt}.")
                continue
            return res
        logger.warning(f"Tools: resposta invalida (tentativa {attempt}/{MAX_RETRIES}). Retorno: {res}")

    # Fallback: usa hubs padrão baseados no nome do arquivo (Divisão Lógica)
    STOP_WORDS = {"de", "o", "a", "e", "com", "do", "da", "em", "para", "os", "as"}
    parts = [p.strip().upper() for p in re.split(r'[_,;]+', filename) if p.strip() and p.lower() not in STOP_WORDS and p.lower() not in {"cv", "habilidades e competencias", "habilidade"}]
    if not parts:
        parts = ["GERAL"]
    return {
        "strategic_title": filename,
        "category": "TECNOLOGIA",
        "hubs": parts,
        "reasoning": "💻 Classificação automática de fallback (Atomic Split).",
    }

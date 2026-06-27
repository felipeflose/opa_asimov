"""
Agent Work — Inteligência de Carreira
Realiza uma autópsia profissional de ativos de trabalho.
Cria clusters granulares por empresa, setor ou tipo de projeto.
"""
import logging
import re
from typing import Optional

from agent_core import local_ollama_call, _extract_sample, MAX_RETRIES, GENERIC_CLUSTERS

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """Você é o especialista de carreira da AI Factory. Extraia a estrutura profissional de ativos de trabalho para montar um grafo de conhecimento.

REGRAS DE EXTRAÇÃO:
1. **EMPRESA (company)**: Nome da empresa. Procure após "Empresa:", "Company:" ou no cabeçalho. Se não encontrar, use "NÃO IDENTIFICADA".
2. **TÍTULO ESTRATÉGICO (strategic_title)**: Baseie-se no cargo e nas principais contribuições. Não use o nome do arquivo.
   Ex: "Arquitetura de BI e Otimização de Data Warehouse na Empresa X"
3. **HIERARQUIA DE HUBS (hubs)**: 3 a 5 níveis do macro ao micro:
   - Nível 1: Setor (Ex: "TECNOLOGIA", "SAÚDE", "FINTECH")
   - Nível 2: Área Funcional (Ex: "BUSINESS INTELLIGENCE", "DATA ENGINEERING")
   - Nível 3: Cargo/Função (Ex: "CONSULTOR SÊNIOR", "TECH LEAD")
   - Nível 4+: Especializações (Ex: "MODELAGEM DIMENSIONAL", "OTIMIZAÇÃO DE QUERIES")
4. **TECNOLOGIAS (tools)**: Liste TODAS as tecnologias mencionadas, em MAIÚSCULAS. Procure em seções de ferramentas, stack técnica, ou citadas no corpo do texto.

PROIBIÇÕES:
- NUNCA use "CV", "EXPERIENCIA", "PROFISSIONAL", "TRABALHO", "GERAL" como hub.
- Hubs devem ser termos profissionais específicos em MAIÚSCULAS.
- Prefira 3-5 hubs focados em vez de 6+ genéricos.

EXEMPLO DE SAÍDA:
{"strategic_title": "Liderança de Data Engineering e Migração Cloud na Empresa ABC", "company": "EMPRESA ABC", "hubs": ["TECNOLOGIA", "DATA ENGINEERING", "CLOUD MIGRATION", "ETL PIPELINES"], "tools": ["GCP", "BIGQUERY", "AIRFLOW", "PYTHON", "TERRAFORM"], "reasoning": "Liderou migração de data warehouse on-premise para GCP, reduzindo custos em 40%."}

Retorne EXCLUSIVAMENTE um JSON válido neste formato."""

REQUIRED_FIELDS = {"strategic_title", "hubs", "reasoning", "company"}



def process_work(content: str, filename: str, directive: str = "", model: str = None) -> Optional[dict]:
    sample = _extract_sample(content)
    dir_block = f"\nDIRETRIZ ESTRATÉGICA DO SCOUT: {directive}\n" if directive else ""
    prompt = f"ATIVO PROFISSIONAL: {filename}{dir_block}\nCONTEÚDO:\n{sample}"

    for attempt in range(1, MAX_RETRIES + 1):
        res = local_ollama_call(prompt, SYSTEM_PROMPT, model=model)
        if res and REQUIRED_FIELDS.issubset(res.keys()):
            # Valida se o primeiro hub não é genérico
            if res["hubs"] and res["hubs"][0].lower() in GENERIC_CLUSTERS:
                logger.warning(f"Work: hub generico detectado, retry {attempt}.")
                continue
            return res
        logger.warning(f"Work: resposta invalida (tentativa {attempt}/{MAX_RETRIES}). Retorno: {res}")

    # Fallback: usa hubs padrão baseados no nome do arquivo (Divisão Lógica)
    STOP_WORDS = {"de", "o", "a", "e", "com", "do", "da", "em", "para", "os", "as"}
    parts = [p.strip().upper() for p in re.split(r'[_,;]+', filename) if p.strip() and p.lower() not in STOP_WORDS and p.lower() not in {"cv", "experiencia profissional"}]
    if not parts:
        parts = ["GERAL"]
    return {
        "strategic_title": filename,
        "company": "EMPRESA",
        "hubs": parts,
        "reasoning": "🏗️ Classificação automática de fallback (Atomic Split).",
    }

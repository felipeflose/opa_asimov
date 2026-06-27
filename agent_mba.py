"""
Agent MBA — Especialista Acadêmico
Processa ativos de MBA e os ancora no cronograma oficial.
Cria clusters granulares por área do conhecimento (não apenas 'DISCIPLINAS').
"""
import logging
import os
import re
import unicodedata
from typing import Optional

from agent_core import local_ollama_call, VAULT_PATH, _extract_sample, MAX_RETRIES, GENERIC_CLUSTERS

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """Você é o especialista acadêmico da AI Factory. Extraia a estrutura de conhecimento de materiais de MBA para montar um grafo de conceitos.

REGRAS DE EXTRAÇÃO:
1. **DISCIPLINA (discipline)**: Nome exato da matéria. Ex: "MACHINE LEARNING APLICADO A NEGÓCIOS".
2. **TÍTULO ESTRATÉGICO (strategic_title)**: Tema central do material. Não use o nome do arquivo. Descreva O QUE o material ensina.
3. **HIERARQUIA DE HUBS (hubs)**: Taxonomia educacional de 3 a 5 níveis, do geral ao específico:
   - Nível 1: Grande Área (Ex: "INTELIGÊNCIA ARTIFICIAL", "GESTÃO ESTRATÉGICA", "DATA SCIENCE")
   - Nível 2: Disciplina (Ex: "MACHINE LEARNING", "FINANÇAS CORPORATIVAS")
   - Nível 3: Módulo/Aula (Ex: "REGRESSÃO LINEAR", "CASE CHURN PREDICTION")
   - Nível 4+: Conceitos-chave se relevantes (Ex: "MÉTRICAS DE AVALIAÇÃO", "CROSS-VALIDATION")
4. **TOOLS**: Ferramentas e cases citados no material (Ex: "SCIKIT-LEARN", "CASE ITAÚ", "PANDAS").

PROIBIÇÕES:
- NUNCA use "GERAL", "SLIDES", "OUTROS" como hub.
- NUNCA use o nome do arquivo como título se for apenas código ou data.
- Hubs devem ser conceitos educacionais em MAIÚSCULAS.
- Prefira 3-5 hubs focados em vez de 6+ hubs genéricos.

EXEMPLO DE SAÍDA:
{"strategic_title": "Predição de Churn com Árvores de Decisão e Métricas de Negócio", "discipline": "MACHINE LEARNING APLICADO A NEGÓCIOS", "hubs": ["INTELIGÊNCIA ARTIFICIAL", "MACHINE LEARNING", "CLASSIFICAÇÃO", "CHURN PREDICTION"], "tools": ["SCIKIT-LEARN", "PANDAS", "CASE TELECOM"], "reasoning": "Material sobre modelos de classificação aplicados a churn, com case prático e métricas AUC/F1."}

Retorne EXCLUSIVAMENTE um JSON válido neste formato."""

REQUIRED_FIELDS = {"strategic_title", "hubs", "reasoning"}


def _normalize(text: str) -> str:
    return "".join(
        c for c in unicodedata.normalize('NFD', text)
        if unicodedata.category(c) != 'Mn'
    ).lower()


_CRONOGRAMA_CACHE = None

def _load_cronograma() -> dict:
    global _CRONOGRAMA_CACHE
    if _CRONOGRAMA_CACHE is not None:
        return _CRONOGRAMA_CACHE

    # No vault_temp achatado, o arquivo costuma ter prefixos de caminho
    # Tentamos encontrar qualquer arquivo que termine em cronograma.md
    crono_path = None
    for f in os.listdir(VAULT_PATH):
        if f.endswith('cronograma.md'):
            crono_path = os.path.join(VAULT_PATH, f)
            break
            
    if not crono_path or not os.path.exists(crono_path):
        _CRONOGRAMA_CACHE = {}
        return _CRONOGRAMA_CACHE

    disciplinas = {}
    try:
        with open(crono_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()
        current = None
        for line in lines:
            stripped = line.strip()
            if stripped.startswith('## '):
                current = stripped.lstrip('#').strip()
                disciplinas[_normalize(current)] = {"original": current, "date": "TBD", "done": False}
            elif current:
                if '- **Data:**' in line:
                    parts = line.split('**Data:**')[-1].strip().split('/')
                    if len(parts) >= 2:
                        disciplinas[_normalize(current)]["date"] = f"{parts[0]}/{parts[1]}"
                elif 'Nota máxima' in line:
                    disciplinas[_normalize(current)]["done"] = True
    except Exception as e:
        logger.warning(f"MBA: erro ao ler cronograma: {e}")

    _CRONOGRAMA_CACHE = disciplinas
    return disciplinas


def _match_cronograma(filename: str, path: str, disciplinas: dict) -> Optional[dict]:
    norm_filename = _normalize(filename)
    norm_path     = _normalize(path)
    for d_norm, info in disciplinas.items():
        if d_norm in norm_filename or d_norm in norm_path:
            icon   = "🏆 " if info["done"] else "⏳ "
            date   = f"[{info['date']}] " if info["date"] != "TBD" else ""
            status = "Concluído" if info["done"] else "Em progresso"
            # Usa o nome da disciplina como hub principal
            return {
                "strategic_title": f"{date}{icon}{info['original']}",
                "hubs": [info["original"].upper()],
                "reasoning": f"📚 {info['original']} | 📅 {info['date']} | 🏆 {status}",
            }
    return None


def process_mba(content: str, filename: str, path: str, directive: str = "", model: str = None) -> Optional[dict]:
    # 1. Tenta match rápido pelo cronograma (sem chamar IA)
    disciplinas = _load_cronograma()
    if disciplinas:
        match = _match_cronograma(filename, path, disciplinas)
        if match:
            return match

    # 2. Fallback: pede à IA com amostra inteligente (início + fim)
    sample = _extract_sample(content)
    dir_block = f"\nDIRETRIZ ESTRATÉGICA DO SCOUT: {directive}\n" if directive else ""
    prompt = f"ATIVO ACADÊMICO: {filename}{dir_block}\nCONTEÚDO:\n{sample}"

    for attempt in range(1, MAX_RETRIES + 1):
        res = local_ollama_call(prompt, SYSTEM_PROMPT, model=model)
        if res and REQUIRED_FIELDS.issubset(res.keys()):
            # Valida que o primeiro hub não é genérico
            if res["hubs"] and res["hubs"][0].lower() in GENERIC_CLUSTERS:
                logger.warning("MBA: hub generico detectado, forcando retry.")
                continue
            return res
        logger.warning(f"MBA: resposta invalida (tentativa {attempt}/{MAX_RETRIES}). Retorno: {res}")

    # Fallback final usando hubs baseados no nome do arquivo (Divisão Lógica)
    STOP_WORDS = {"de", "o", "a", "e", "com", "do", "da", "em", "para", "os", "as"}
    parts = [p.strip().upper() for p in re.split(r'[_,;]+', filename) if p.strip() and p.lower() not in STOP_WORDS]
    if not parts:
        parts = ["GERAL"]
        
    return {
        "strategic_title": filename,
        "hubs": parts,
        "reasoning": "📚 Classificação automática de fallback (Atomic Split).",
    }

"""
Agent Classifier — Triagem Semântica
Classifica um arquivo Markdown em: mba | work | tool | classificar
"""
import logging

from agent_core import local_ollama_call

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """Você é o classificador semântico da AI Factory. Analise o tom, estrutura e vocabulário do texto e classifique-o na categoria correta.

ANÁLISE OBRIGATÓRIA:
1. TOM: Corporativo (resultados, cargos)? Instrutivo (como fazer, documentação)? Acadêmico (teoria, aulas)?
2. MARCADORES: "Período:", "Cargo:", "Atividades:" → work. Blocos de código, guias de instalação → tool. "Aula", "Professor", "Disciplina" → mba.

CATEGORIAS:
- "work": Experiência profissional, currículo, cargos, projetos em empresas reais, networking, formação acadêmica. Foco em IMPACTO e RESULTADOS.
- "tool": Documentação técnica, habilidades, certificações, descrição de UMA tecnologia específica (Python, AWS, Snowflake). Foco em COMO FUNCIONA e PROFICIÊNCIA.
- "mba": APENAS conteúdo educacional de pós-graduação. Slides de aula, resumos teóricos, exercícios, cases acadêmicos. Foco em TEORIA e APRENDIZADO.
- "classificar": Use SOMENTE quando nenhuma das 3 categorias acima se aplica claramente.

REGRAS DE DESEMPATE:
1. Texto sobre tecnologia aplicada em empresa X → "tool" (foco principal é a habilidade técnica).
2. Texto acadêmico que menciona empresas como case de estudo → "mba" (contexto é educacional).
3. Texto com cargo + tecnologias → "work" se descreve o que FEZ; "tool" se descreve o que SABE.
4. Na dúvida entre work/tool → se tem "Empresa:" ou "Período:", é "work".
5. Na dúvida entre mba/tool → se tem "Aula" ou "Professor", é "mba".

Retorne EXCLUSIVAMENTE um JSON válido:
{"type": "work", "reasoning": "Tom corporativo com marcadores Empresa e Cargo. Descreve impacto em projeto real."}

Valores válidos para type: "mba", "work", "tool", "classificar"."""

VALID_TYPES = {"mba", "work", "tool", "classificar"}
MAX_RETRIES = 2


def _extract_content_sample(content: str, max_chars: int = 4000) -> str:
    """
    Extrai uma amostra inteligente do conteúdo:
    - Primeiros 2000 chars (cabeçalho, metadados, título)
    - Últimos 2000 chars (conclusões, referências)
    """
    if len(content) <= max_chars:
        return content
    half = max_chars // 2
    return content[:half] + "\n...[CONTEÚDO INTERMEDIÁRIO OMITIDO]...\n" + content[-half:]


def classify_content(content: str, filename: str) -> tuple[str, str]:
    # Heurística Forense: Regras de Ouro
    fn = filename.lower()
    if "experiencia profissional" in fn: return "work", "Heurística: Nome contém 'experiencia profissional'"
    if "habilidades e competencias" in fn: return "tool", "Heurística: Nome contém 'habilidades e competencias'"
    if "mba" in fn: return "mba", "Heurística: Nome contém 'mba'"
    if "contato" in fn or "formacao academica" in fn: return "work", "Heurística: Nome indica perfil profissional"

    sample = _extract_content_sample(content)
    prompt = f"ARQUIVO: {filename}\nCONTEÚDO:\n{sample}"

    for attempt in range(1, MAX_RETRIES + 1):
        res = local_ollama_call(prompt, SYSTEM_PROMPT)
        if res and res.get("type") in VALID_TYPES:
            return res["type"], res.get("reasoning", "Sem justificativa")
        logger.warning(f"Classifier: resposta invalida (tentativa {attempt}/{MAX_RETRIES}). Retorno: {res}")

    return "classificar", "Fallback após erros"


if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1:
        with open(sys.argv[1], 'r', encoding='utf-8') as f:
            result = classify_content(f.read(), sys.argv[1])
        print(f"Resultado: {result}")

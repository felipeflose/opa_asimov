"""
CHAOS MONKEY — Chief Innovation Disruptor

Não mais refatora código silenciosamente.
Agora: gera 1 ideia revolucionária por hora, submete a votação,
e se aprovada, coloca no topo do backlog com priority=ZERO.

Regra de Aprovação:
- 8 de 10 devs virtuais votam SIM
- 2 de 3 PMs virtuais aprovam
- Verificação de novidade (não pode ser duplicate do backlog)
"""
import os
import json
import random
import logging
import time
from datetime import datetime

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

APP_DIR = os.path.dirname(os.path.abspath(__file__))
IMPROVEMENTS_FILE = os.path.join(APP_DIR, 'improvement_backlog.json')
CHAOS_LOG_FILE = os.path.join(APP_DIR, 'improvements_run_log.txt')

# ── Time de votantes simulado ─────────────────────────────────────────────────
DEV_VOTERS = [
    {"name": "Lucas Oliveira",    "emoji": "👨💻", "role": "Backend Pleno",    "bias": "performance"},
    {"name": "Ana Paula Ribeiro", "emoji": "👩💻", "role": "Senior Full Stack", "bias": "code_quality"},
    {"name": "Thiago Martins",    "emoji": "🧑💻", "role": "Backend Junior",   "bias": "architecture"},
    {"name": "Jessica Souza",     "emoji": "👩💻", "role": "Frontend Pleno",   "bias": "ux"},
    {"name": "Rafael Lima",       "emoji": "👨💻", "role": "DevOps",           "bias": "infrastructure"},
    {"name": "Fernanda Costa",    "emoji": "👩💻", "role": "ML Engineer",      "bias": "ai"},
    {"name": "Gabriel Santos",    "emoji": "👨💻", "role": "Mobile/API",       "bias": "api"},
    {"name": "Isabela Rocha",     "emoji": "👩💻", "role": "Security",         "bias": "security"},
    {"name": "Pedro Alves",       "emoji": "👨💻", "role": "Tech Lead",        "bias": "scalability"},
    {"name": "Mariana Souza",     "emoji": "👩💻", "role": "Data Engineer",    "bias": "data"},
]

PM_VOTERS = [
    {"name": "Beatriz Santos",   "emoji": "👩💼", "threshold": 0.70},  # exigente
    {"name": "Rodrigo Carvalho", "emoji": "🧑💼", "threshold": 0.50},  # mais flexível
    {"name": "Camila Ferreira",  "emoji": "👩🔬", "threshold": 0.60},  # analítica
]

# ── Banco de ideias revolucionárias estáticas ────────────────────────────────
REVOLUTIONARY_IDEAS = [
    "Implementar grafo de conhecimento temporal — cada nota tem score que decai com o tempo e conexões que se fortalecem com revisões",
    "Sistema de podcast automático: o bot sintetiza os tópicos mais estudados da semana e gera áudio MP3",
    "Modo 'Sala de Estudo' colaborativa: múltiplos usuários exploram o mesmo grafo em tempo real via WebSocket",
    "IA que sugere próxima nota a estudar baseada em lacunas do grafo (spaced repetition visual)",
    "Integração com calendário: agenda automática de revisões baseada na curva do esquecimento de Ebbinghaus",
    "Sistema de badges e achievements para gamificação do processo de aprendizado",
    "Export do grafo como mindmap interativo em PDF com links clicáveis",
    "Análise de sentimento das notas — detecta quando o estudo está frustrante vs engajado",
    "Geração automática de flashcards Anki a partir de notas marcadas",
    "Dashboard de 'pontos cegos': tópicos citados mas nunca estudados em profundidade",
    "Voice search: busca por voz no grafo usando Whisper local",
    "Modo noturno adaptativo: ajusta densidade do grafo baseado no cansaço (detectado por hora do dia)",
    "Integração com GitHub: notas de código linkadas automaticamente a commits relevantes",
    "Sistema de 'pergunta socrática': bot questiona o usuário sobre tópicos pouco revisados",
    "Timeline visual: linha do tempo de quando cada conhecimento foi adquirido",
    "Cluster automático de notas com K-Means e exibição de comunidades no grafo",
    "Exportar grafo para formato Obsidian nativo e sincronizar com vault local via rsync",
    "Detecção de contradições: IA identifica notas que afirmam coisas opostas sobre o mesmo tópico",
    "Dashboard semanal enviado por email com estatísticas de aprendizado e recomendações",
    "API pública do grafo com autenticação OAuth para integração com Notion, Roam e Logseq",
]

# ── Argumentos de votação por bias do dev ────────────────────────────────────
VOTE_REASONS_YES = {
    "performance":   "Isso elimina gargalos críticos de I/O e vai reduzir latência percebida",
    "code_quality":  "A proposta vai aumentar coesão e diminuir complexidade ciclomática geral",
    "architecture":  "Está alinhado com o padrão hexagonal que adotamos — composição limpa",
    "ux":            "Excelente para engagement e retenção de usuários mobile e desktop",
    "infrastructure":"Viável na infra atual sem grandes mudanças no CI/CD ou Kubernetes",
    "ai":            "Abre um vetor interessante de personalização com embeddings contextuais",
    "api":           "A API de integração pode ser exposta facilmente via REST com versionamento",
    "security":      "Não abre novos vetores de ataque — posso auditar em <2h",
    "scalability":   "Escala horizontalmente sem estado compartilhado — pattern sólido",
    "data":          "Os dados gerados alimentam análises ricas e dashboards de retenção",
}

VOTE_REASONS_NO = {
    "performance":   "Benchmarks mostram que o ganho real seria marginal para o volume atual",
    "code_quality":  "Aumenta acoplamento entre módulos sem benefício claro de longo prazo",
    "architecture":  "Complexidade de infra subestimada — custo de manutenção é alto",
    "ux":            "Pode confundir usuários novos antes de um onboarding estruturado",
    "infrastructure":"Requer mudanças no Dockerfile e pipeline — risco de regressão elevado",
    "ai":            "Custo de tokens LLM pode aumentar 40% — precisa de análise de ROI",
    "api":           "Sem SLA definido para a integração externa — compliance em aberto",
    "security":      "A superfície de ataque aumenta — precisa de threat model antes do dev",
    "scalability":   "O padrão proposto tem single point of failure não mapeado",
    "data":          "Sem contrato de dados — pode gerar inconsistências no data warehouse",
}

# ── Palavras-chave por bias para checagem de afinidade com a ideia ───────────
BIAS_KEYWORDS = {
    "performance":   ["latência", "cache", "otimizar", "gargalo", "velocidade", "rápid"],
    "code_quality":  ["refatoração", "clean", "código", "qualidade", "manutenção", "padrão"],
    "architecture":  ["módulo", "componente", "hexagonal", "estrutura", "camada", "serviço"],
    "ux":            ["usuário", "interface", "estudo", "colaborativ", "visual", "experiência"],
    "infrastructure":["deploy", "docker", "kubernetes", "infra", "pipeline", "ci/cd"],
    "ai":            ["ia", "embedding", "llm", "modelo", "aprendizado", "inteligência"],
    "api":           ["api", "rest", "endpoint", "integração", "webhook", "oauth"],
    "security":      ["autenticação", "segurança", "criptografia", "token", "audit"],
    "scalability":   ["escala", "horizontal", "cluster", "shard", "réplica", "partição"],
    "data":          ["dados", "análise", "dashboard", "estatística", "métrica", "relatório"],
}


def check_novelty(idea_text: str, backlog_titles: list) -> tuple:
    """Verifica se a ideia não é duplicata do backlog."""
    idea_lower = idea_text.lower()
    idea_words = set(idea_lower.split())
    for existing in backlog_titles:
        existing_words = set(existing.lower().split())
        overlap = idea_words & existing_words
        # Considera duplicata se >60% das palavras da ideia já aparecem num item
        if len(idea_words) > 0 and len(overlap) / len(idea_words) > 0.60:
            return False, existing
    return True, None


def dev_vote_probability(dev: dict, idea_text: str) -> float:
    """Calcula probabilidade de voto SIM baseada no bias do dev vs conteúdo da ideia."""
    bias = dev["bias"]
    keywords = BIAS_KEYWORDS.get(bias, [])
    idea_lower = idea_text.lower()
    matches = sum(1 for kw in keywords if kw in idea_lower)
    # Base 55% de aprovação + bônus por afinidade temática
    base_prob = 0.55
    bonus = min(matches * 0.10, 0.30)
    return base_prob + bonus


def simulate_vote(idea_text: str, backlog_titles: list) -> dict:
    """
    Simula a votação da ideia pelo time de devs e PMs.
    Retorna dict com resultado detalhado da votação.
    """
    # 1. Verificar novidade
    is_novel, duplicate_title = check_novelty(idea_text, backlog_titles)

    # 2. Votação dos Devs
    dev_votes = []
    for dev in DEV_VOTERS:
        prob = dev_vote_probability(dev, idea_text)
        voted_yes = random.random() < prob
        reason = VOTE_REASONS_YES[dev["bias"]] if voted_yes else VOTE_REASONS_NO[dev["bias"]]
        dev_votes.append({
            "voter": dev,
            "yes": voted_yes,
            "reason": reason,
        })

    # 3. Votação dos PMs
    pm_votes = []
    for pm in PM_VOTERS:
        voted_yes = random.random() < pm["threshold"]
        pm_votes.append({
            "voter": pm,
            "yes": voted_yes,
        })

    devs_yes = sum(1 for v in dev_votes if v["yes"])
    pms_yes = sum(1 for v in pm_votes if v["yes"])

    approved = (devs_yes >= 8) and (pms_yes >= 2) and is_novel

    return {
        "approved": approved,
        "is_novel": is_novel,
        "duplicate_title": duplicate_title,
        "dev_votes": dev_votes,
        "pm_votes": pm_votes,
        "devs_yes": devs_yes,
        "pms_yes": pms_yes,
    }


def print_voting_log(idea_text: str, result: dict):
    """Imprime o log bonito da votação."""
    print()
    print("=" * 70)
    print("🐒 [CHAOS MONKEY] Nova ideia revolucionária gerada!")
    print(f"💡 Ideia: \"{idea_text[:80]}{'...' if len(idea_text) > 80 else ''}\"")
    print()
    print("📊 VOTAÇÃO EM ANDAMENTO:")
    print("-" * 70)

    for vote in result["dev_votes"]:
        dev = vote["voter"]
        symbol = "✅ SIM" if vote["yes"] else "❌ NÃO"
        role_short = dev["role"][:20]
        print(f"{dev['emoji']} {dev['name']:<22} [{role_short:<20}]: {symbol} — \"{vote['reason']}\"")

    print()
    print("👩💼 VOTAÇÃO PMs:")
    print("-" * 70)
    for vote in result["pm_votes"]:
        pm = vote["voter"]
        symbol = "✅ APROVADO" if vote["yes"] else "❌ REPROVADO"
        print(f"{pm['emoji']} {pm['name']:<22}: {symbol}")

    print()
    print("📋 RESULTADO:")
    print("-" * 70)
    devs_ok = "✅" if result["devs_yes"] >= 8 else "❌"
    pms_ok  = "✅" if result["pms_yes"]  >= 2 else "❌"
    novel_ok = "✅" if result["is_novel"] else "❌"

    print(f"{devs_ok} Devs: {result['devs_yes']}/10 aprovaram (mínimo: 8)")
    print(f"{pms_ok} PMs:  {result['pms_yes']}/3 aprovaram (mínimo: 2)")

    if result["is_novel"]:
        print(f"{novel_ok} Novidade confirmada — não é duplicata do backlog")
    else:
        print(f"{novel_ok} DUPLICATA detectada: \"{result['duplicate_title']}\"")

    print()
    if result["approved"]:
        print("🚀 IDEIA APROVADA! Adicionada ao backlog com PRIORITY ZERO!")
    else:
        print("🔴 IDEIA REPROVADA. Será refinada e reapresentada na próxima hora.")
    print("=" * 70)
    print()


def load_backlog() -> list:
    """Carrega o backlog atual do arquivo JSON."""
    if not os.path.exists(IMPROVEMENTS_FILE):
        return []
    try:
        with open(IMPROVEMENTS_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception:
        return []


def add_to_backlog_priority_zero(idea_text: str, vote_result: dict):
    """Adiciona a ideia aprovada ao topo do backlog com prioridade máxima."""
    backlog = load_backlog()

    new_item = {
        "id": f"CHAOS-{datetime.now().strftime('%Y%m%d%H%M%S')}",
        "title": idea_text[:120],
        "description": f"[CHAOS MONKEY] Ideia revolucionária aprovada por votação do time.\n"
                       f"Devs: {vote_result['devs_yes']}/10 | PMs: {vote_result['pms_yes']}/3\n\n"
                       f"Ideia completa: {idea_text}",
        "status": "todo",
        "priority": "ZERO",
        "category": "Inovação",
        "difficulty": "high",
        "impact": "high",
        "source": "chaos_monkey",
        "created_at": datetime.now().isoformat(),
        "vote_summary": {
            "devs_yes": vote_result["devs_yes"],
            "pms_yes": vote_result["pms_yes"],
            "approved_at": datetime.now().isoformat(),
        }
    }

    # Coloca no TOPO do backlog
    backlog.insert(0, new_item)

    with open(IMPROVEMENTS_FILE, 'w', encoding='utf-8') as f:
        json.dump(backlog, f, ensure_ascii=False, indent=2)

    # Tenta criar no Jira se disponível
    try:
        from dotenv import load_dotenv
        load_dotenv(os.path.join(APP_DIR, '.env'))
        from jira_client import JiraClient
        jira = JiraClient()
        jira.create_issue(
            summary=f"[CHAOS] {idea_text[:80]}",
            description=new_item["description"],
            details="Ideia gerada pelo Chaos Monkey Inovador e aprovada por votação do time virtual.",
            motivation_justification="Inovação disruptiva aprovada pelo processo de votação do Chaos Monkey",
            category="Inovação",
            priority="high",
            difficulty="high",
            impact="high",
        )
        logging.info("🐒 [CHAOS MONKEY] Issue criada no Jira com sucesso!")
    except Exception as e:
        logging.warning(f"🐒 [CHAOS MONKEY] Não foi possível criar no Jira (continuando): {e}")

    # Log no arquivo de runs
    with open(CHAOS_LOG_FILE, 'a', encoding='utf-8') as lf:
        lf.write(
            f"\n[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] [CHAOS-MONKEY] "
            f"IDEIA APROVADA e adicionada ao backlog (PRIORITY ZERO): {idea_text[:80]}\n"
        )

    return new_item


def pick_idea(backlog: list) -> str:
    """Escolhe uma ideia revolucionária da lista estática (sem duplicar itens já no backlog)."""
    backlog_titles = [item.get("title", "") for item in backlog]

    # Filtra ideias que não são candidatas a duplicata
    available = []
    for idea in REVOLUTIONARY_IDEAS:
        is_novel, _ = check_novelty(idea, backlog_titles)
        if is_novel:
            available.append(idea)

    if available:
        return random.choice(available)

    # Se todas já estiverem no backlog, pega uma aleatória da lista completa
    logging.info("🐒 [CHAOS MONKEY] Todas as ideias estáticas já estão no backlog. Reciclando...")
    return random.choice(REVOLUTIONARY_IDEAS)


def main():
    """
    Roda normalmente (chamado pelo cron a cada hora).
    Gera 1 ideia, simula votação, adiciona ao backlog se aprovada.
    """
    from dotenv import load_dotenv
    load_dotenv(os.path.join(APP_DIR, '.env'))

    logging.info("🐒 [CHAOS MONKEY] Iniciando sessão de inovação...")

    backlog = load_backlog()
    backlog_titles = [item.get("title", "") for item in backlog]

    # Gera a ideia
    idea = pick_idea(backlog)

    # Simula a votação com log detalhado de cada votante
    result = simulate_vote(idea, backlog_titles)

    # Exibe o log bonito da votação
    print_voting_log(idea, result)

    if result["approved"]:
        new_item = add_to_backlog_priority_zero(idea, result)
        logging.info(f"🐒 [CHAOS MONKEY] ✅ Ideia adicionada ao backlog: ID={new_item['id']}")
    else:
        # Loga o motivo da reprovação
        reasons = []
        if result["devs_yes"] < 8:
            reasons.append(f"devs insuficientes ({result['devs_yes']}/10)")
        if result["pms_yes"] < 2:
            reasons.append(f"PMs insuficientes ({result['pms_yes']}/3)")
        if not result["is_novel"]:
            reasons.append(f"duplicata detectada: '{result['duplicate_title']}'")

        logging.info(f"🐒 [CHAOS MONKEY] ❌ Ideia reprovada por: {', '.join(reasons)}")

        with open(CHAOS_LOG_FILE, 'a', encoding='utf-8') as lf:
            lf.write(
                f"\n[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] [CHAOS-MONKEY] "
                f"IDEIA REPROVADA ({', '.join(reasons)}): {idea[:80]}\n"
            )

    logging.info("🐒 [CHAOS MONKEY] Sessão encerrada. Até a próxima hora!")


if __name__ == '__main__':
    import sys
    if "--daemon" in sys.argv:
        logging.info("🐒 [CHAOS MONKEY] Iniciando no modo daemon (sprints de 5 minutos)...")
        while True:
            try:
                main()
            except Exception as e:
                logging.error(f"Erro no loop do Chaos Monkey: {e}")
            time.sleep(300)
    else:
        main()

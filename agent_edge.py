"""
Agent Edge — Auditor de Linhagem Autônomo v2
============================================
Missão completa:
  1. PRIORIDADE      — audita nós novos/classificar primeiro, ignora nós recentes
  2. LINHAGEM        — verifica e corrige a categoria/cluster de cada ativo
  3. ÓRFÃOS          — detecta e reconecta nós sem caminho até o Mestre
  4. DUPLICATAS      — detecta nós com títulos muito similares e marca para revisão
  5. CONEXÕES CROSS  — descobre links semânticos entre hubs diferentes (Work↔Tools)
  6. EDGE QUALITY    — verifica se arestas existentes fazem sentido
  7. AUDITORIA TRACK — registra `last_audited` em cada nó para não reauditar em excesso
"""
import logging
import os
import time
import json
from datetime import datetime, timedelta
from difflib import SequenceMatcher

import numpy as np
from agent_core import load_graph, save_graph, local_ollama_call, slugify, get_ollama_embedding, cosine_similarity

logger = logging.getLogger(__name__)

# ── Prompts ────────────────────────────────────────────────

LINEAGE_PROMPT = """Você é o auditor de linhagem da AI Factory. Verifique se o arquivo está na categoria e cluster corretos.

CATEGORIAS VÁLIDAS: "mba", "work", "tool", "classificar"

CRITÉRIOS DE RECLASSIFICAÇÃO:
- Mude a categoria SOMENTE se houver evidência clara de erro (ex: conteúdo acadêmico classificado como "work").
- Se a categoria atual é razoável, MANTENHA-A mesmo que outra seja possível.
- Clusters devem ser ESPECÍFICOS e em MAIÚSCULAS (ex: "MACHINE LEARNING", "FINTECH", "AWS"). Nunca use "GERAL" ou "OUTROS".

QUANDO RECLASSIFICAR:
- Texto com "Aula", "Professor", "Disciplina" marcado como work/tool → mude para "mba"
- Documentação técnica de ferramenta marcada como mba/work → mude para "tool"
- Experiência profissional com empresa/cargo marcada como mba/tool → mude para "work"

Retorne EXCLUSIVAMENTE um JSON válido:
{"type": "mba", "cluster": "MACHINE LEARNING", "reasoning": "Conteúdo acadêmico sobre ML com exercícios e referências de aula."}"""

CROSS_LINK_PROMPT = """Analise dois nós do grafo de conhecimento e decida se existe uma relação técnica ou estratégica direta entre eles.

QUANDO LINKAR (should_link: true):
- Projeto de WORK que usa/depende de uma TOOL específica (ex: "Projeto de BI" ↔ "Power BI")
- Conteúdo de MBA que ensina uma TOOL presente no grafo (ex: "Aula de ML" ↔ "Scikit-Learn")
- Experiência de WORK que aplica conhecimento de MBA (ex: "Consultoria em IA" ↔ "Deep Learning")

QUANDO NÃO LINKAR (should_link: false):
- Relação muito genérica (ex: ambos são "de tecnologia" mas sem conexão direta)
- Mesma categoria sem dependência real (ex: dois projetos independentes)
- Relação apenas temática sem aplicação prática (ex: "MBA Finanças" ↔ "Excel" se Excel não foi citado no material)

Retorne EXCLUSIVAMENTE um JSON válido:
{"should_link": true, "reasoning": "Projeto de BI na Empresa X utilizou Power BI como ferramenta principal."}"""

EDGE_QUALITY_PROMPT = """Avalie se esta conexão entre dois nós do grafo de conhecimento é válida e faz sentido.

CRITÉRIOS DE VALIDADE:
- A conexão representa uma relação REAL (hierárquica, tecnológica ou de aplicação)?
- Ambos os nós existem em contexto onde um referencia ou depende do outro?
- A conexão agrega valor ao grafo (ajuda a navegar o conhecimento)?

CONEXÕES INVÁLIDAS:
- Loops (A→B→A) ou auto-referências
- Relações genéricas sem evidência concreta
- Conexões duplicadas com reasoning diferente mas mesmo significado
- Nós de categorias diferentes sem sinergia real

Retorne EXCLUSIVAMENTE um JSON válido:
{"valid": true, "reasoning": "Hub CLOUD COMPUTING conecta corretamente ao sub-hub GCP por hierarquia técnica."}"""

SCOUT_PROMPT = """Analise o arquivo e decida onde ele se encaixa no grafo de conhecimento.

HUBS JÁ EXISTENTES NO GRAFO: {existing_hubs}

REGRAS:
1. REUTILIZE hubs existentes sempre que possível. Não crie hubs redundantes (ex: se já existe "MACHINE LEARNING", não crie "ML" ou "APRENDIZADO DE MÁQUINA").
2. Escolha o type correto: "mba" (acadêmico), "work" (profissional), "tool" (técnico).
3. suggested_hubs: liste os hubs da hierarquia, do mais geral ao mais específico.
4. parent_id: use o ID de um hub existente. IDs seguem o padrão: "mba_hub", "work_hub", "tool_hub", ou slugs como "machine_learning_hub".
5. strategic_directive: instrução curta para o agente especialista.

Retorne EXCLUSIVAMENTE um JSON válido:
{{
  "type": "tool",
  "suggested_hubs": ["CLOUD COMPUTING", "GCP"],
  "strategic_directive": "Extrair serviços GCP e nível de proficiência.",
  "parent_id": "tool_hub"
}}"""

# ── Configurações ──────────────────────────────────────────
AUDIT_COOLDOWN_HOURS = 6   # Não reaudita um nó antes desse intervalo
SIMILARITY_THRESHOLD  = 0.82  # Limiar para considerar nós duplicados (String)
SEMANTIC_THRESHOLD    = 0.88  # Limiar para duplicatas semânticas (Embeddings)
MAX_CROSS_LINKS_PER_CYCLE = 3  # Máx de cross-links descobertos por ciclo
MAX_CROSS_CHECK_PAIRS = int(os.environ.get("FLOSE_MAX_CROSS_CHECK_PAIRS", 10))
SLEEP_AUDIT_NODE_SECONDS = int(os.environ.get("FLOSE_SLEEP_AUDIT_NODE", 3))
SLEEP_COOLDOWN_SECONDS   = float(os.environ.get("FLOSE_SLEEP_COOLDOWN", 0.5))
SLEEP_CYCLE_SECONDS      = int(os.environ.get("FLOSE_SLEEP_CYCLE", 20))

from collections import OrderedDict

class LimitedCache(OrderedDict):
    """Implementação estrita de LRU Cache baseada em OrderedDict."""
    def __init__(self, maxsize=1000, *args, **kwargs):
        self.maxsize = maxsize
        super().__init__(*args, **kwargs)

    def __getitem__(self, key):
        value = super().__getitem__(key)
        self.move_to_end(key)
        return value

    def get(self, key, default=None):
        try:
            return self[key]
        except KeyError:
            return default

    def __setitem__(self, key, value):
        if key in self:
            super().__setitem__(key, value)
            self.move_to_end(key)
        else:
            if len(self) >= self.maxsize:
                self.popitem(last=False)
            super().__setitem__(key, value)

# Cache de embeddings em memória com limite firme (LRU Cache)
_EMBED_CACHE = LimitedCache(maxsize=1000)


# ── Helpers ────────────────────────────────────────────────

def _resolve_id(ref) -> str:
    return ref.get("id") if isinstance(ref, dict) else ref


def _similarity(a: str, b: str) -> float:
    return SequenceMatcher(None, a.lower(), b.lower()).ratio()


def _needs_audit(node: dict) -> bool:
    """Retorna True se o nó ainda não foi auditado ou o cooldown expirou."""
    last = node.get("last_audited")
    if not last:
        return True
    try:
        audited_at = datetime.fromisoformat(last)
        return datetime.now() - audited_at > timedelta(hours=AUDIT_COOLDOWN_HOURS)
    except Exception as e:
        logger.warning(f"Erro ao parsear last_audited: {e}")
        return True


def _mark_audited(node: dict) -> None:
    node["last_audited"] = datetime.now().isoformat()
    node.pop("validating", None)


def get_lineage(node_id: str, edges: list) -> list[str]:
    """Rastreia o caminho do nó até o Mestre."""
    path = [node_id]
    current = node_id
    for _ in range(8):
        parent = next(
            (e for e in edges if _resolve_id(e.get("target")) == current),
            None
        )
        if not parent:
            break
        current = _resolve_id(parent.get("source"))
        path.append(current)
        if current == "mestre":
            break
    return path


def set_validating(nodes: list, ids: set, state: bool) -> None:
    for node in nodes:
        if node["id"] in ids:
            node["validating"] = state


# ── Módulos de Auditoria ───────────────────────────────────

def audit_lineage(node: dict, nodes: list, edges: list) -> bool:
    """
    Verifica e corrige a linhagem do nó.
    Retorna True se houve alteração.
    """
    file_path = node.get("path", "")
    if not file_path or not os.path.exists(file_path):
        return False

    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        half = 1500
        sample = content[:half] + ("\n...\n" + content[-half:] if len(content) > half * 2 else "")
        prompt = (
            f"ARQUIVO: {node['title']}\n"
            f"CATEGORIA ATUAL: {node.get('type')}\n"
            f"CLUSTER ATUAL: {node.get('cluster', 'desconhecido')}\n"
            f"CONTEÚDO:\n{sample}"
        )
        res = local_ollama_call(prompt, LINEAGE_PROMPT)
        if res and res.get("type") and res["type"] != node.get("type"):
            logger.info(f"Reclassificando '{node['title']}': {node.get('type')} → {res['type']}")
            node["type"] = res["type"]
            return True
    except Exception as e:
        logger.error(f"Erro na auditoria de linhagem: {e}")
    return False


def scout_node(content: str, filename: str, nodes: list) -> dict:
    """
    Agente Scout: Analisa o terreno antes da execução.
    Retorna o plano de vôo para o agente responsável.
    """
    # 0. Heurísticas Forenses (Rápido e infalível para padrões conhecidos)
    fn = filename.lower()
    if "mba" in fn:
        return {"type": "mba", "suggested_hubs": [], "strategic_directive": "Extrair conceitos acadêmicos e técnicos do MBA.", "parent_id": "mba_hub"}
    if "habilidades e competencias" in fn or "certificacoes" in fn:
        return {"type": "tool", "suggested_hubs": [], "strategic_directive": "Extrair habilidades técnicas e certificações.", "parent_id": "tool_hub"}
    if "experiencia profissional" in fn or "projetos" in fn:
        return {"type": "work", "suggested_hubs": [], "strategic_directive": "Extrair conquistas, cargos e stack tecnológica.", "parent_id": "work_hub"}

    # 1. Mapeia Hubs existentes para dar contexto ao Scout
    existing_hubs = [n['title'].replace('📍 ', '') for n in nodes if "_hub" in n['id']]
    hubs_context = ", ".join(existing_hubs[:40]) # Top 40 hubs para não estourar contexto

    prompt = f"ARQUIVO: {filename}\nCONTEÚDO:\n{content[:2000]}\n"
    res = local_ollama_call(prompt, SCOUT_PROMPT.format(existing_hubs=hubs_context))
    
    if not res:
        # Fallback básico se a IA falhar
        return {"type": "classificar", "suggested_hubs": ["GERAL"], "strategic_directive": "Processamento padrão", "parent_id": "classificar_hub"}
    
    return res


def detect_orphans(nodes: list, edges: list) -> list[str]:
    """
    Detecta nós (depth >= 2) que não têm nenhuma edge apontando para eles
    e portanto estão desconectados da hierarquia.
    """
    all_targets = {_resolve_id(e.get("target")) for e in edges}
    orphans = [
        n["id"] for n in nodes
        if n.get("depth", 0) >= 2 and n["id"] not in all_targets
        and n["id"] != "mestre"
    ]
    return orphans


def fix_orphan(node: dict, nodes: list, edges: list, existing_links: set) -> bool:
    """
    Tenta reconectar um nó órfão ao super-hub correto.
    """
    h_type = node.get("type", "classificar")
    sh_id = f"{h_type}_hub"
    sh_exists = any(n["id"] == sh_id for n in nodes)
    if not sh_exists:
        sh_id = "classificar_hub"

    link_key = f"{sh_id}_{node['id']}"
    if link_key not in existing_links:
        edges.append({"source": sh_id, "target": node["id"], "reasoning": "🔧 Reconexão automática de órfão."})
        existing_links.add(link_key)
        logger.info(f"Orfao reconectado: '{node.get('title')}' → {sh_id}")
        return True
    return False


def detect_duplicates(nodes: list) -> list[tuple]:
    """
    Detecta pares de nós com títulos muito similares (String ou Semântica).
    Retorna lista de tuplas (id1, id2, score, type) usando descarte rápido e produto de matrizes.
    """
    ativos = [n for n in nodes if n.get("path") or n.get("type") in ['mba', 'work', 'tool']]
    duplicates = []
    
    # 1. Carrega embeddings
    ids = []
    embs = []
    for n in ativos:
        emb = _EMBED_CACHE.get(n["id"]) or n.get("embedding")
        if not emb:
            emb = get_ollama_embedding(n.get("title", ""))
            if emb: _EMBED_CACHE[n["id"]] = emb
        else:
            _EMBED_CACHE[n["id"]] = emb
            
        if emb:
            ids.append(n["id"])
            embs.append(emb)

    # 2. Comparações Textuais (com descarte rápido por comprimento)
    for i, a in enumerate(ativos):
        t_a = a.get("title", "")
        len_a = len(t_a)
        if not t_a: continue
        for b in ativos[i+1:]:
            t_b = b.get("title", "")
            len_b = len(t_b)
            if not t_b: continue
            
            # Descarte matemático por diferença de comprimento
            max_len = max(len_a, len_b)
            if max_len == 0: continue
            min_len = min(len_a, len_b)
            max_possible = 2.0 * min_len / (len_a + len_b)
            if max_possible < SIMILARITY_THRESHOLD:
                continue
                
            str_score = _similarity(t_a, t_b)
            if str_score >= SIMILARITY_THRESHOLD:
                duplicates.append((a["id"], b["id"], round(str_score, 2), "TEXTUAL"))

    # 3. Comparações Semânticas Vetorizadas (usando Numpy para produto de matrizes)
    if len(embs) > 1:
        try:
            E = np.array(embs, dtype=np.float32)
            norms = np.linalg.norm(E, axis=1, keepdims=True)
            norms[norms == 0] = 1e-9
            E_norm = E / norms
            S = np.dot(E_norm, E_norm.T)
            
            n_ativos = len(ids)
            for i in range(n_ativos):
                for j in range(i + 1, n_ativos):
                    score = float(S[i, j])
                    if score >= SEMANTIC_THRESHOLD:
                        id_a = ids[i]
                        id_b = ids[j]
                        # Evita adicionar se já foi detectada como duplicata textual
                        if not any((x[0] == id_a and x[1] == id_b) or (x[0] == id_b and x[1] == id_a) for x in duplicates):
                            duplicates.append((id_a, id_b, round(score, 2), "SEMÂNTICA"))
        except Exception as e:
            logger.warning(f"Erro no cálculo de duplicatas semânticas vetorizadas: {e}")
            # Fallback em Python puro
            for i, id_a in enumerate(ids):
                for j in range(i + 1, len(ids)):
                    id_b = ids[j]
                    score = cosine_similarity(_EMBED_CACHE[id_a], _EMBED_CACHE[id_b])
                    if score >= SEMANTIC_THRESHOLD:
                        if not any((x[0] == id_a and x[1] == id_b) for x in duplicates):
                            duplicates.append((id_a, id_b, round(score, 2), "SEMÂNTICA"))
                            
    return duplicates


def discover_cross_links(nodes: list, edges: list, existing_links: set) -> int:
    """
    Descobre conexões semânticas entre nós de hubs diferentes (Work↔Tools, MBA↔Tools).
    Usa a IA para validar se a conexão faz sentido.
    Retorna o número de links criados.
    """
    ativos = [n for n in nodes if n.get("path")]
    # Foca em pares de hubs diferentes
    pairs_to_check = [
        (a, b) for i, a in enumerate(ativos) for b in ativos[i+1:]
        if a.get("type") != b.get("type")
    ]

    links_created = 0
    max_links_per_node = int(os.environ.get("FLOSE_MAX_CROSS_LINKS_PER_NODE", 4))
    
    for a, b in pairs_to_check[:MAX_CROSS_CHECK_PAIRS]:  # Limita pares verificados por ciclo
        if links_created >= MAX_CROSS_LINKS_PER_CYCLE:
            break
            
        # Item 98: Limita a quantidade de cross-links por nó para evitar saturação do grafo
        a_cross_count = sum(1 for e in edges if e.get("cross_link") and (e["source"] == a["id"] or e["target"] == a["id"]))
        b_cross_count = sum(1 for e in edges if e.get("cross_link") and (e["source"] == b["id"] or e["target"] == b["id"]))
        if a_cross_count >= max_links_per_node or b_cross_count >= max_links_per_node:
            continue
            
        link_key = f"{a['id']}_{b['id']}"
        reverse_key = f"{b['id']}_{a['id']}"
        if link_key in existing_links or reverse_key in existing_links:
            continue

        prompt = (
            f"NÓ A: '{a.get('title')}' (tipo: {a.get('type')})\n"
            f"NÓ B: '{b.get('title')}' (tipo: {b.get('type')})\n"
            f"Existe uma relação estratégica direta entre eles na carreira de um Engenheiro de IA?"
        )
        res = local_ollama_call(prompt, CROSS_LINK_PROMPT)
        if res and res.get("should_link"):
            edges.append({
                "source": a["id"],
                "target": b["id"],
                "reasoning": f"🔗 Cross-link: {res.get('reasoning', 'Relação semântica descoberta.')}",
                "cross_link": True,
            })
            existing_links.add(link_key)
            logger.info(f"Cross-link criado: '{a['title']}' ↔ '{b['title']}'")
            links_created += 1

    return links_created


# ── Loop Principal ─────────────────────────────────────────

def run_curator():
    logger.info("AGENTE EDGE v2: Auditoria Completa Iniciada")
    cycle = 0

    while True:
        cycle += 1

        logger.info(f"CICLO #{cycle} - {datetime.now().strftime('%H:%M:%S')}")


        import copy
        graph = load_graph()
        nodes: list = copy.deepcopy(graph.get("nodes", []))
        edges: list = copy.deepcopy(graph.get("edges", []))
        existing_links = {f"{_resolve_id(e['source'])}_{_resolve_id(e['target'])}" for e in edges}

        # ── 1. DETECTA ÓRFÃOS ─────────────────────────────
        orphans = detect_orphans(nodes, edges)
        if orphans:
            logger.warning(f"{len(orphans)} nó(s) órfão(s) detectado(s): {orphans}")
            nodes_map = {n["id"]: n for n in nodes}
            changed = False
            for oid in orphans:
                if oid in nodes_map:
                    changed |= fix_orphan(nodes_map[oid], nodes, edges, existing_links)
            if changed:
                save_graph(nodes, edges, f"🔧 {len(orphans)} órfão(s) reconectado(s)")

        # ── 2. DETECTA DUPLICATAS ─────────────────────────
        dupes = detect_duplicates(nodes)
        if dupes:
            logger.warning(f"{len(dupes)} par(es) de possíveis duplicatas:")
            for id1, id2, score, d_type in dupes:
                n1 = next((n for n in nodes if n["id"] == id1), {})
                n2 = next((n for n in nodes if n["id"] == id2), {})
                logger.warning(f"   [{score:.0%}] {d_type}: '{n1.get('title')}' ↔ '{n2.get('title')}'")
                # Marca para revisão visual
                n1["duplicate_flag"] = True
                n2["duplicate_flag"] = True

        # ── 3. AUDITORIA DE LINHAGEM (priorizada) ─────────
        ativos = [n for n in nodes if n.get("path")]

        # Prioridade: classificar > novos (sem last_audited) > todos os demais
        priority_order = (
            [n for n in ativos if n.get("type") == "classificar"] +
            [n for n in ativos if not n.get("last_audited") and n.get("type") != "classificar"] +
            [n for n in ativos if n.get("last_audited") and _needs_audit(n)]
        )

        if not priority_order:
            logger.info("Todos os nos auditados recentemente. Pulando linhagem.")
        else:
            logger.info(f"{len(priority_order)} no(s) na fila de auditoria.")
            for node in priority_order:
                logger.info(f"Auditando linhagem: {node['title']} ({' → '.join(get_lineage(node['id'], edges))})")
                audit_lineage(node, nodes, edges)
                time.sleep(SLEEP_AUDIT_NODE_SECONDS)
                _mark_audited(node)
                time.sleep(SLEEP_COOLDOWN_SECONDS)
            save_graph(nodes, edges, f"✅ Linhagem concluída para {len(priority_order)} nós")

        # ── 4. DESCOBRE CROSS-LINKS (a cada 3 ciclos) ─────
        if cycle % 3 == 0:
            logger.info("Buscando conexoes cruzadas entre hubs...")
            new_links = discover_cross_links(nodes, edges, existing_links)
            if new_links > 0:
                save_graph(nodes, edges, f"🔗 {new_links} cross-link(s) descoberto(s)!")

        logger.info(f"Ciclo #{cycle} concluido. Aguardando {SLEEP_CYCLE_SECONDS}s...")
        time.sleep(SLEEP_CYCLE_SECONDS)


if __name__ == "__main__":
    run_curator()

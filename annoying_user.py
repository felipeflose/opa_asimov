import os
import json
import random
import requests
import logging
from datetime import datetime

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

APP_DIR = os.path.dirname(os.path.abspath(__file__))
FEEDBACK_FILE = os.path.join(APP_DIR, 'user_feedback.json')
SERVER_LOG = os.path.join(APP_DIR, 'server.log')
FLASK_PORT = "8091"

# Definição das Personas de Usuários Exigentes
USER_PERSONAS = [
    {
        "name": "Ana Silva", 
        "emoji": "👩‍🎨", 
        "role": "UI/UX Designer", 
        "prompt_add": "Aja como Ana, uma Designer de UI/UX impaciente. Foque em críticas visuais, cores neon cansativas, tamanhos de fontes, alinhamentos, física de zoom do grafo D3.js e usabilidade no navegador."
    },
    {
        "name": "Carlos Souza", 
        "emoji": "👨‍🔬", 
        "role": "Backend Engineer", 
        "prompt_add": "Aja como Carlos, um Engenheiro Backend rigoroso. Foque em latência de endpoints, logs com erros ou warnings, vazamento de memória, otimização de consultas SQLite e overhead de rotas de SSE."
    },
    {
        "name": "Mariana Costa", 
        "emoji": "👩‍🎓", 
        "role": "Especialista em RAG", 
        "prompt_add": "Aja como Mariana, uma Especialista em RAG e IA. Foque na qualidade e precisão dos resumos de notas, problemas com links Markdown quebrados ou nós órfãos, e relevância semântica das buscas."
    },
    {
        "name": "Lucas Pereira", 
        "emoji": "👨‍📱", 
        "role": "Mobile QA Tester", 
        "prompt_add": "Aja como Lucas, um usuário mobile frustrado. Foque no tempo de resposta do Bot do Telegram, suporte a comandos rápidos, menus responsivos no celular e experiência fora do desktop."
    },
    {
        "name": "Felipe Flóse", 
        "emoji": "👨‍💼", 
        "role": "Product Owner", 
        "prompt_add": "Aja como Felipe, o PO estratégico do projeto. Foque em controle de segurança de chaves, falta de features mais complexas (como Whisper, Napkin.ai), observabilidade de status e valor de produto."
    }
]

def call_llm_for_complaint(persona, context_type, context_data):
    """Gera uma reclamação baseada na persona selecionada e na inconformidade do sistema."""
    prompt = f"""Você é {persona['name']} ({persona['role']}) e está usando o Obsidian Graph App. {persona['prompt_add']}

---
TIPO DE AUDITORIA ATIVA: {context_type}
DADOS DO SISTEMA COLETADOS:
{context_data[:1200]}
---

Escreva uma reclamação curta, direta e irritada baseada na sua persona e nos dados acima (máximo de 2 frases, em português). Seja realista.
Não fale em termos de código se for designer ou usuário final, reclame do sintoma que você percebeu.
Retorne APENAS a reclamação em texto puro, sem aspas ou introduções."""

    groq_key = os.environ.get("GROQ_API_KEY")
    if groq_key:
        try:
            r = requests.post(
                "https://api.groq.com/openai/v1/chat/completions",
                headers={"Authorization": f"Bearer {groq_key}", "Content-Type": "application/json"},
                json={
                    "model": "gemma2-9b-it",
                    "messages": [{"role": "user", "content": prompt}],
                    "temperature": 0.75,
                },
                timeout=15
            )
            if r.status_code == 200:
                return r.json()["choices"][0]["message"]["content"].strip()
        except Exception:
            pass

    # Fallback Ollama Local
    try:
        r = requests.post(
            "http://localhost:11434/api/generate",
            json={
                "model": "gemma4-fast:latest",
                "prompt": prompt,
                "stream": False,
                "options": {"temperature": 0.75}
            },
            timeout=30
        )
        if r.status_code == 200:
            return r.json()["response"].strip()
    except Exception:
        pass

    # Fallbacks estáticos por persona
    fallbacks = {
        "Ana Silva": "O zoom no grafo tá meio travado e as cores neon da tela tão me dando dor de cabeça!",
        "Carlos Souza": "A rota do grafo demorou muito pra responder, deve estar tendo gargalo de concorrência ou I/O.",
        "Mariana Costa": "Encontrei vários nós sem conexões no grafo, parecem links perdidos que a indexação não arrumou.",
        "Lucas Pereira": "O bot do Telegram demora muito pra responder quando mando notas longas pelo celular.",
        "Felipe Flóse": "Falta uma opção robusta de salvar o estado visual do grafo e monitorar melhor o status da fábrica."
    }
    return fallbacks.get(persona["name"], "O sistema está apresentando inconsistências que dificultam meu uso.")

def audit_logs():
    if not os.path.exists(SERVER_LOG):
        return None
    try:
        with open(SERVER_LOG, 'r', encoding='utf-8') as f:
            lines = f.readlines()
        errors = [line.strip() for line in lines[-150:] if "ERROR" in line or "Exception" in line or "Traceback" in line]
        if errors:
            return "\n".join(errors[:5])
    except Exception:
        pass
    return None

def audit_api_performance():
    url = f"http://localhost:{FLASK_PORT}/api/graph"
    try:
        start = datetime.now()
        r = requests.get(url, timeout=5)
        duration = (datetime.now() - start).total_seconds()
        if duration > 0.8:
            return f"Latência na Rota Principal: {duration:.2f} segundos."
    except Exception as e:
        return f"Servidor indisponível ou com alta latência: {e}"
    return None

def audit_graph_integrity():
    graph_path = os.path.join(APP_DIR, 'obsidian_graph.json')
    if not os.path.exists(graph_path):
        return "Arquivo obsidian_graph.json ausente no servidor."
    try:
        with open(graph_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        nodes = data.get("nodes", [])
        edges = data.get("edges", [])
        connected_nodes = set([e["source"] for e in edges] + [e["target"] for e in edges])
        orphans = [n["id"] for n in nodes if n["id"] not in connected_nodes]
        if len(orphans) > 5:
            return f"Grafo possui {len(orphans)} nós completamente sem conexões ou órfãos."
    except Exception as e:
        return f"Erro ao analisar integridade dos dados do grafo: {e}"
    return None

def main():
    from dotenv import load_dotenv
    load_dotenv(os.path.join(APP_DIR, '.env'))

    # Escolhe entre 1 e 3 usuários aleatórios para agir nesta rodada
    num_users = random.randint(1, 3)
    selected_personas = random.sample(USER_PERSONAS, num_users)
    
    new_feedbacks = []

    # Carrega feedbacks existentes
    feedbacks = []
    if os.path.exists(FEEDBACK_FILE):
        try:
            with open(FEEDBACK_FILE, 'r', encoding='utf-8') as f:
                feedbacks = json.load(f)
        except Exception:
            pass

    for persona in selected_personas:
        # Associa cada persona ao seu tipo ideal de teste de auditoria
        if "Designer" in persona["role"]:
            audit_type = "INTERFACE_GRAPH"
            audit_result = "Física de posicionamento de nós do D3.js sem localStorage e contraste visual cansativo no tema escuro."
        elif "Backend" in persona["role"]:
            # Tenta ler log de erros, se não houver simula latência
            audit_type = "LOGS_AND_PERFORMANCE"
            audit_result = audit_logs() or audit_api_performance() or "Servidor com latência de resposta variável sob concorrência SSE."
        elif "RAG" in persona["role"]:
            audit_type = "INTEGRIDADE_CONHECIMENTO"
            audit_result = audit_graph_integrity() or "Notas órfãs detectadas no vault sem arestas correspondentes."
        else:
            # PO ou Mobile QA usam heurística geral de usabilidade e features
            audit_type = "FEATURES_PRODUTO"
            audit_result = random.choice([
                "Telegram bot com latência alta sem fila persistente SQLite.",
                "Dashboard sem visualização estruturada dos logs de auditoria do Cliente Oculto.",
                "Falta de controle de rate limit de API Key nos endpoints administrativos."
            ])

        complaint = call_llm_for_complaint(persona, audit_type, audit_result)
        logging.info(f"Usuário [{persona['name']}] reclamou: '{complaint}'")

        new_feedbacks.append({
            "timestamp": datetime.now().isoformat(),
            "user": persona["name"],
            "avatar": persona["emoji"],
            "role": persona["role"],
            "complaint": complaint,
            "status": "pending"
        })

    # Consolida e salva
    feedbacks.extend(new_feedbacks)
    with open(FEEDBACK_FILE, 'w', encoding='utf-8') as f:
        json.dump(feedbacks, f, ensure_ascii=False, indent=2)

if __name__ == '__main__':
    main()

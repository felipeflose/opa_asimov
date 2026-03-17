# Arquitetura do Sistema — Flose AI Platform

## Diagrama de Fluxo Principal

```
┌─────────────┐     webhook      ┌──────────────────────────────────────┐
│   Telegram  │ ─────────────► │         Cloud Run (FastAPI)            │
└─────────────┘                 │                                        │
                                │  ┌──────────────┐  ┌───────────────┐  │
┌─────────────┐     HTTPS       │  │  entrypoint  │  │  React SPA    │  │
│   Browser   │ ─────────────► │  │  (endpoints) │  │  (static)     │  │
└─────────────┘                 │  └──────┬───────┘  └───────────────┘  │
                                │         │                              │
                                │  ┌──────▼──────────────────────┐      │
                                │  │   CognitiveOrchestrator      │      │
                                │  │   (Gemini API + tenacity)    │      │
                                │  └──────┬──────────────────────-┘      │
                                │         │ dispatch                      │
                                │  ┌──────▼──────────────────────┐      │
                                │  │    Agentes Especializados    │      │
                                │  │  FinOps / QA / Briefing...   │      │
                                │  └──────┬──────────────────────-┘      │
                                └─────────┼──────────────────────────────┘
                                          │ read/write
                                ┌─────────▼──────────────────────┐
                                │   Google Cloud Storage (GCS)    │
                                │  ┌──────────┐  ┌────────────┐  │
                                │  │  Tasks   │  │  Kg Graph  │  │
                                │  │ Registry │  │  (Nodes/   │  │
                                │  └──────────┘  │  Links)    │  │
                                │  ┌──────────┐  └────────────┘  │
                                │  │ Exec Logs│                   │
                                │  └──────────┘                   │
                                └─────────────────────────────────┘
```

---

## Camadas do Sistema

### 1. Interface Layer

#### Telegram (entrada de comandos)
- Usuário envia mensagem ou imagem para o bot
- Telegram dispara um **POST** para `/telegram_webhook` no Cloud Run
- `TelegramAgent` processa e encaminha para o orquestrador

#### React Command Center (monitoramento humano)
- SPA React servida via FastAPI `StaticFiles`
- Autenticação via `POST /api/auth` → recebe token
- Token armazenado em `sessionStorage`
- Todas as chamadas de API usam `Authorization: Bearer <token>`

---

### 2. Orchestration Layer

#### `CognitiveOrchestrator`
O coração do sistema. Responsável por:
1. Receber o input sanitizado
2. Construir o system prompt com contexto do Knowledge Graph
3. Chamar o Gemini com retry (tenacity)
4. Validar a resposta via Pydantic
5. Rotear para o agente correto
6. Persistir o resultado no GCS

**Fluxo de sanitização:**
```
Input Raw → Truncar (4000 chars) → Redact Forbidden Tokens → Enviar ao LLM
```

**Fluxo de retry:**
```
Chamada Gemini → Falha? → Espera 2s → Nova tentativa → Falha? → Espera 4s
→ Nova tentativa → Falha? → Re-raise exception
```

---

### 3. Agent Layer

Cada agente herda de `BaseAgent` e implementa:

```python
class BaseAgent:
    def __init__(self, gcs_client, orchestrator)
    async def run(self, context: dict) -> str
    def _build_prompt(self, context: dict) -> str
```

#### Ciclo de Vida de uma Tarefa

```
[Aberto] → (Aprovação humana no frontend) → [Aprovado]
         → (Execução por agente) → [Em Progresso]
         → (Resultado salvo no GCS) → [Concluído]
         → (View Delivery no modal) → Usuário visualiza artefato
```

---

### 4. Storage Layer

#### GCSClient
- **Namespacing:** todos os paths são prefixados com `users/{user_id}/`
- **Cache em memória:** TTL de 30 segundos para leituras frequentes
- **Error handling:** todas as operações retornam `bool` ou `None` em caso de falha

#### Estrutura de Pastas no GCS

```
gs://flose-ai-platform-{project_id}/
└── users/
    └── fflose/
        ├── registry/
        │   └── task_registry.json        # Todas as tarefas
        ├── logs/
        │   └── executions/
        │       └── {result_id}.json      # Log de cada execução
        ├── knowledge/
        │   └── knowledge_graph.json      # Grafo de conhecimento
        ├── activity/
        │   └── telegram_log.json         # Histórico do Telegram
        └── agents/
            └── registry.json            # Configuração de todos os agentes
```

---

### 5. Infrastructure Layer

#### Cloud Run
- **Concorrência:** 80 requests simultâneos por instância
- **Min Instances:** 0 (scale-to-zero, custo zero quando inativo)
- **Memória:** 2GB (configurável)
- **Trigger:** HTTP (webhook Telegram + requests frontend)

#### Artifact Registry
- Imagem Docker armazenada no `us-central1-docker.pkg.dev`
- Build acontece na máquina local via `gcloud builds submit`

#### Secret Manager
- Todos os segredos injetados via environment variables no Cloud Run
- Nunca armazenados na imagem Docker ou no código

---

## Autenticação — Diagrama de Sequência

```
Browser          FastAPI          SessionStorage
   │                │                   │
   │──POST /api/auth──►│                │
   │◄──{ token }───│                   │
   │────────────────────► setItem()     │
   │                │                   │
   │──GET /api/stats──►│               │
   │  Authorization: Bearer <token>     │
   │                │                  │
   │  validate_token()                 │
   │  (header → query fallback)        │
   │◄──{ data }────│                   │
```

---

## Conhecimento Gerado (Knowledge Graph)

O Knowledge Graph armazena entidades tipadas:

| Tipo | Descrição | Exemplo |
|------|-----------|---------|
| `core` | Sistemas centrais do Flose | `CognitiveOrchestrator` |
| `pilar` | Domínios de conhecimento | `FinOps`, `Segurança` |
| `concept` | Conceitos aprendidos | `exponential backoff` |

Links entre nós representam relações semânticas (`groups`, `relates_to`, `implements`).
O grafo é visualizado como um force-directed graph no Command Center.

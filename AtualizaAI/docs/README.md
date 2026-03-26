# Flose AI Platform v3.0

> Plataforma de orquestração multi-agente de IA de Próxima Geração, operando no Google Cloud Platform (GCP) com Governança via Sala de Aula (Classroom) e Memória de Longo Prazo via RAG Cache (GCS).

---

## Componentes Principais (v3.0)

### 🎓 Sala de Aula (Classroom)
- Sistema de isolamento para agentes em treinamento (`in_training`).
- Calibração de Prompt, Ferramentas e RAG antes da promoção para produção.
- Checklist de progresso neuronal visível no Command Center.

### 🏛️ RAG & Cache Imortal
- Web Scraping integrado para leitura de sites externos.
- Persistência de conhecimento no Bucket GCS (`agents/{name}/rag/cache/`).
- Injeção de contexto dinâmica para reduzir alucinações da IA.

### 🧠 Orquestrador V3 (`core/orchestrator_v3/`)
- Motor de decisão em tempo real com Gemini Flash 1.5/2.0.
- Diagnóstico detalhado de erros (Cota, Rede, IA) para o usuário final.
- Suporte a ferramentas de Grounding (Google Search) nativo.

### 🛠️ Estrutura do Projeto (v3.0)

```
AtualizaAI/
├── entrypoint.py           # Servidor FastAPI (BFF Principle)
├── agents_v3/              # Agentes Especializados (Base & Specialized)
├── core/                   # Núcleo de Orquestração (Logic & Gemini)
├── api/routers/            # Endpoints modulares (Agents, Tasks, Chat...)
├── storage_v3/             # Nova camada de I/O GCS otimizada
├── services/               # Serviços de Domínio (Scraper, TaskService)
├── frontend/               # React + React Query (Command Center)
│   └── src/pages/          # Agents, Classroom, Tasks...
└── docs/                   # Documentação completa
```

---

## Deploy & GitHub CI/CD

O projeto utiliza **GitHub Actions** para deploy automático no Cloud Run.
Sempre que um `push` é feito na `main`:
1. O Frontend é compilado e injetado no diretório estático do FastAPI.
2. A imagem Docker é construída e enviada ao Artifact Registry.
3. O Cloud Run é atualizado com as novas camadas de segurança e rede.
4. O Webhook do Telegram é reconfigurado para a nova URL da revisão.

---

> Plataforma de orquestração multi-agente de IA, operating on Google Cloud Platform (GCP) com integração ao Telegram, Gemini API e Google Cloud Storage.

## Visão Geral

O Flose AI Platform é um sistema autônomo de agentes de IA desenvolvido para gerenciar tarefas, gerar conhecimento e tomar decisões com supervisão humana. O sistema roda no Cloud Run (GCP), é acionado via webhook do Telegram e possui um frontend React como Command Center.

---

## Arquitetura Geral

```
Telegram ──► Cloud Run (FastAPI) ──► CognitiveOrchestrator (Gemini AI)
                     │                         │
                     ▼                         ▼
               React Frontend           Agentes Especializados
               (Command Center)         (FinOps, QA, Briefing...)
                     │                         │
                     └─────────┬───────────────┘
                               ▼
                     Google Cloud Storage (GCS)
                     Knowledge Graph | Task Registry | Logs
```

---

## Componentes Principais

### Backend (`entrypoint.py`)
- **FastAPI** como servidor HTTP principal
- Autenticação via `Authorization: Bearer <token>` (header)
- Gerenciamento de webhook do Telegram
- Lazy loading do agente Telegram para reduzir cold start

### Orquestrador Cognitivo (`src/orchestrator/cognitive_orchestrator.py`)
- Motor principal de raciocínio usando **Gemini API**
- Retry automático com **exponential backoff** via `tenacity`
- Sanitização de input contra **prompt injection**
- Validação de schema das respostas do LLM via Pydantic

### Agentes Especializados (`src/agents/`)
| Agente | Responsabilidade |
|--------|-----------------|
| `TelegramAgent` | Recebe e processa mensagens do Telegram |
| `BriefingAgent` | Gera briefings executivos |
| `FinOpsGuardian` | Monitora custos e governa orçamentos |
| `DebateAgent` | Controla debates entre agentes |
| `VisionAgent` | Processa imagens enviadas ao Telegram |
| `ReportAgent` | Gera relatórios estruturados |
| `ProactiveAlertAgent` | Monitora o sistema e dispara alertas |

### Storage (`src/storage/`)
- **GCSClient**: Wrapper do Google Cloud Storage com cache em memória, tratamento de erros e namespacing por usuário
- **FinOpsManager**: Integração com Cloud Billing API + Cloud Monitoring para custo real

### Knowledge Graph (`src/graph/`)
- Grafo de conhecimento persistido no GCS
- Categorização em `core`, `pilar` e `concept`
- Visualizável no Command Center (D3.js force-directed)

### Frontend (`frontend/`)
- **React + Vite**
- Single-Page Application servida pelo FastAPI via `StaticFiles`
- Autenticação via `sessionStorage` (sem persistência cross-session por segurança)

---

## Variáveis de Ambiente

| Variável | Descrição | Obrigatório |
|----------|-----------|-------------|
| `MASTER_KEY` | Token mestre de autenticação da API | ✅ Sim |
| `GEMINI_API_KEY` | Chave da API do Google Gemini | ✅ Sim |
| `GCP_PROJECT_ID` | ID do projeto GCP | ✅ Sim |
| `TELEGRAM_BOT_TOKEN` | Token do bot do Telegram | ✅ Sim |
| `GCP_BILLING_ACCOUNT_ID` | ID do billing account (para custo real) | ⚠️ Recomendado |
| `GEMINI_MODEL` | Modelo Gemini a usar (default: `gemini-1.5-flash`) | ❌ Opcional |
| `NAPKIN_API_KEY` | Chave da API do Napkin AI (diagramas) | ❌ Opcional |
| `PORT` | Porta do servidor FastAPI (default: 8080) | ❌ Opcional |

> ⚠️ **NUNCA** commite valores reais no repositório. O Flose AI agora utiliza **GitHub Secrets** (`Settings > Secrets and variables > Actions`) para gerenciar as credenciais no deploy automatizado. Arquivos `.env` locais podem ser usados restritamente (estão no `.gitignore`).

---

## Deploy

O projeto conta com uma esteira de integração e entrega contínua (**CI/CD**) gerida pelo **GitHub Actions**.

Ao realizar um `git push` ou concluir um PR na branch `main`, o arquivo `deploy.yml` será acionado automaticamente e:
1. Instala dependências e constrói o build do frontend (`npm run build`).
2. Autentica no GCP usando a account de serviço registrada nos secrets do GitHub.
3. Constrói e publica a imagem Docker no Artifact Registry (`gcloud builds submit`).
4. Realiza o deploy da nova versão no Cloud Run com as variáveis de ambiente e injeta secrets no GCP Secret Manager a partir do GitHub.
5. Configura e atualiza a URL do webhook do Telegram apontando para o novo Cloud Run.

---

## Desenvolvimento Local

### Pré-requisitos
- Python 3.11+
- Node.js 18+
- Google Cloud SDK autenticado (`gcloud auth application-default login`)

### Backend

```bash
cd AtualizaAI
pip install -r requirements.txt
uvicorn entrypoint:app --reload --port 8080
```

### Frontend

```bash
cd AtualizaAI/frontend
npm install
npm run dev
```

O Vite rodará na porta 5173 e o proxy está configurado para apontar para o backend em `localhost:8080`.

---

## Segurança

Veja o arquivo [SECURITY.md](./SECURITY.md) para informações detalhadas sobre as políticas e práticas de segurança.

---

## Scripts Utilitários

| Script | Descrição |
|--------|-----------|
| `Atualiza_requirements.py` | Analisa imports do projeto e gera `requirements.txt` automaticamente |
| `scripts_aux/` | Scripts auxiliares de manutenção |

---

## Estrutura do Projeto

```
AtualizaAI/
├── entrypoint.py           # Servidor FastAPI + todos os endpoints da API
├── Dockerfile              # Container de produção
├── requirements.txt        # Dependências Python
├── docs/                   # Documentação
├── frontend/               # React + Vite (Command Center)
│   └── src/
│       ├── App.jsx         # Componente principal
│       └── App.css         # Estilos globais
├── src/
│   ├── agents/             # Agentes especializados
│   ├── orchestrator/       # Motor cognitivo (Gemini)
│   ├── storage/            # GCS + FinOps
│   ├── graph/              # Knowledge Graph
│   └── utils/              # Utilitários
└── tests/                  # Testes automatizados
```

# Flose AI Platform

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

> ⚠️ **NUNCA** commite valores reais no repositório. Use o Secret Manager do GCP ou um arquivo `.env` local (que está no `.gitignore`).

---

## Deploy

O projeto é deployado via Google Cloud Run usando o script:

```powershell
powershell -ExecutionPolicy Bypass -File deploy_gcp.ps1
```

O script automaticamente:
1. Habilita APIs necessárias no GCP
2. Configura os secrets no Secret Manager
3. Faz o build do frontend (`npm run build`)
4. Constrói e publica a imagem Docker no Artifact Registry
5. Deploya no Cloud Run com variáveis de ambiente configuradas
6. Configura o webhook do Telegram para o novo endpoint

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
| `deploy_gcp.ps1` | Script completo de CI/CD para o GCP |
| `scripts_aux/` | Scripts auxiliares de manutenção |

---

## Estrutura do Projeto

```
AtualizaAI/
├── entrypoint.py           # Servidor FastAPI + todos os endpoints da API
├── Dockerfile              # Container de produção
├── deploy_gcp.ps1          # Script de deploy automatizado
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

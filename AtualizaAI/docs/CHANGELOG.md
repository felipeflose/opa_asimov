# Changelog — Flose AI Platform

Todas as mudanças significativas do projeto estão documentadas aqui.

---

## [v2.1.0] — Março 2026 — Security & Reliability Overhaul

### 🔴 Segurança Crítica

#### Autenticação via Authorization Header
- **Antes:** Token passado como query parameter (`?token=...`)
- **Depois:** Todas as requisições usam `Authorization: Bearer <token>`
- **Impacto:** Tokens não aparecem mais em logs de servidor ou histórico do browser
- **Arquivos:** `entrypoint.py`, `frontend/src/App.jsx`

#### Token em SessionStorage (não localStorage)
- **Antes:** `localStorage.setItem('flose_token', ...)`
- **Depois:** `sessionStorage.setItem('flose_token', ...)`
- **Impacto:** Token expira ao fechar o browser, reduzindo risco de XSS persistente
- **Arquivo:** `frontend/src/App.jsx`

#### Função `validate_token()` centralizada no backend
- Adicionada função helper que aceita Bearer token do header com fallback para query param (retrocompatibilidade)
- Todos os 17 endpoints da API migrados para usar esta função
- **Arquivo:** `entrypoint.py`

---

### 🟠 Confiabilidade

#### Retry com Exponential Backoff no CognitiveOrchestrator
- Adicionada decoração `@retry` via `tenacity` em `_call_gemini()`
- Configuração: `min=2s`, `max=10s`, `3 tentativas`
- **Arquivo:** `src/orchestrator/cognitive_orchestrator.py`

#### Sanitização de Input Ampliada
- Expandida lista de tokens proibidos de 4 para 13 padrões
- Migrada para `re.sub(..., flags=re.IGNORECASE)` (antes: `str.replace()` case-sensitive)
- Novos padrões: `"ACT AS"`, `"DAN MODE"`, `"OVERRIDE"`, `"FORGET EVERYTHING"`, etc.
- **Arquivo:** `src/orchestrator/cognitive_orchestrator.py`

#### Error Handling completo no GCSClient
- Todos os métodos de I/O agora têm `try/except` com log de erro
- Métodos agora retornam `bool` (sucesso/falha) ou `None` em vez de propagar exceção
- **Arquivo:** `src/storage/gcs_client.py`

#### Validação de Schema do LLM
- Respostas do Gemini validadas via Pydantic antes do processamento
- Mecanismo de fallback para JSON malformado
- **Arquivo:** `src/orchestrator/cognitive_orchestrator.py`

---

### 🟡 Portabilidade

#### Caminhos dinâmicos no Atualiza_requirements.py
- **Antes:** `PATH_PROJETO = r'C:\Users\fflose\flose\opa_asimov'` (hardcoded)
- **Depois:** `PATH_PROJETO = os.path.dirname(os.path.abspath(__file__))`
- **Impacto:** Script funciona em qualquer máquina ou SO
- **Arquivo:** `Atualiza_requirements.py`

---

### 🎨 Frontend & UX

#### Modal de Entrega de Artefatos
- **Antes:** `alert()` com o conteúdo bruto do JSON
- **Depois:** Modal premium com apresentação estruturada do resultado
- Exibe erro formatado se o artefato não for encontrado (em vez de tela em branco)
- **Arquivo:** `frontend/src/App.jsx`

#### Conexão com GCP Billing API Real
- FinOps Guardian agora busca custo real via Cloud Billing API
- Fallback para Cloud Monitoring se API de Billing não estiver acessível
- **Antes:** Retornava valor mockado `0.12` (hardcoded com TODO)
- **Arquivo:** `src/storage/finops_manager.py`

---

## [v2.0.0] — Fevereiro 2026 — Multi-Agent System Launch

### Adicionado
- `CognitiveOrchestrator` com integração Gemini
- Agentes: `TelegramAgent`, `FinOpsGuardian`, `BriefingAgent`, `DebateAgent`
- Knowledge Graph Manager com persistência no GCS
- Frontend React: Dashboard, Cognitive Map, Task Manager, Agent Library
- Pipeline Builder para sequências de agentes
- Marketplace de templates de agentes
- Deploy automatizado via `deploy_gcp.ps1`

### Infraestrutura
- Cloud Run com Dockerfile otimizado
- Secret Manager para todas as credenciais
- Webhook do Telegram configurado automaticamente no deploy

---

## [v1.0.0] — Janeiro 2026 — MVP

### Adicionado
- Bot inicial no Telegram para responder perguntas via Gemini
- Armazenamento de conversas no GCS
- Protótipo do Knowledge Graph

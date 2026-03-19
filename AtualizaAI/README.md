# Flose AI Platform

Plataforma multi-agente de IA com orquestração via Gemini, deploy no Google Cloud Run e integração com Telegram.

## Documentação

| Documento | Descrição |
|-----------|-----------|
| [docs/README.md](docs/README.md) | Visão geral, variáveis de ambiente, setup e deploy |
| [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) | Arquitetura detalhada, diagramas de fluxo e estrutura de dados |
| [docs/SECURITY.md](docs/SECURITY.md) | Políticas de segurança, autenticação e gestão de segredos |
| [docs/CHANGELOG.md](docs/CHANGELOG.md) | Histórico de versões e mudanças |

## Quick Start

```node
# O deploy para produção (GCP) agora é automatizado via GitHub Actions
# Qualquer push ou PR merge na branch `main` disparatá a esteira de CI/CD.
```

## Stack

- **Backend:** FastAPI + Python 3.11
- **Frontend:** React + Vite
- **AI:** Google Gemini API
- **Storage:** Google Cloud Storage
- **Deploy:** Cloud Run (GCP) via GitHub Actions CI/CD
- **Bot:** Telegram Webhook

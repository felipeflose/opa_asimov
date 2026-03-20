# TASK-26 | /cozinha logs — Últimos Erros do Sistema

## Metadata
| Campo | Valor |
|---|---|
| ID | TASK-26 |
| Grupo | Cozinha (Modo Dev) |
| Prioridade | Alta |
| Responsável | DevAgent |
| Status | Aberto |

## Objetivo
Ver os últimos erros do sistema direto no Telegram, sem precisar acessar Cloud Logging ou o dashboard.

## Prompt para Antigravity

```
No `dev_agent.py`, detectar a keyword `logs` e buscar no GCS 
os últimos 20 arquivos de `logs/executions/*.json`, filtrar 
os que têm campo `error` preenchido e retornar no Telegram 
uma lista formatada: timestamp, agente, mensagem de erro. 
Sem passar pelo Gemini — leitura direta do GCS.
```

## Arquivos Envolvidos
- `src/agents/dev_agent.py`

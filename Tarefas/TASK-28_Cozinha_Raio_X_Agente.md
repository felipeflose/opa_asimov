# TASK-28 | /cozinha agente {nome} — Raio-X de um Agente

## Metadata
| Campo | Valor |
|---|---|
| ID | TASK-28 |
| Grupo | Cozinha (Modo Dev) |
| Prioridade | Média |
| Responsável | DevAgent |
| Status | Aberto |

## Objetivo
Ver tudo sobre um agente específico em uma única mensagem no Telegram, sem abrir o dashboard.

## Prompt para Antigravity

```
No `dev_agent.py`, detectar o padrão `agente {nome}`, buscar 
no `agents/registry.json` e retornar no Telegram: system_prompt 
atual, total de execuções, última execução (timestamp + 
resultado resumido em 1 linha), tools configuradas e % de 
acertividade calculada do `qa_report`.
```

## Arquivos Envolvidos
- `src/agents/dev_agent.py`
- `entrypoint.py` (endpoint `/api/qa/report`)

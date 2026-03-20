# TASK-29 | /cozinha diff — O que Mudou desde Ontem

## Metadata
| Campo | Valor |
|---|---|
| ID | TASK-29 |
| Grupo | Cozinha (Modo Dev) |
| Prioridade | Alta |
| Responsável | DevAgent |
| Status | Aberto |

## Objetivo
Acordar e saber em 30 segundos o que o sistema fez enquanto você dormia, sem precisar abrir logs ou o dashboard.

## Cenário Real
Você manda `/cozinha diff` de manhã e recebe: novos agentes criados ontem, tarefas que mudaram de status e erros que ocorreram.

## Prompt para Antigravity

```
No `dev_agent.py`, detectar a keyword `diff` e comparar os 
arquivos de log de execução de hoje vs ontem no GCS. Retornar: 
novos agentes criados, tarefas que mudaram de status, endpoints 
mais chamados e qualquer entrada com campo `error`. Formatar 
como changelog resumido no Telegram.
```

## Arquivos Envolvidos
- `src/agents/dev_agent.py`

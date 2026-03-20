# TASK-30 | /cozinha custo {agente} — Custo Real por Agente

## Metadata
| Campo | Valor |
|---|---|
| ID | TASK-30 |
| Grupo | Cozinha (Modo Dev) |
| Prioridade | Alta |
| Responsável | DevAgent |
| Status | Aberto |

## Objetivo
Saber exatamente quanto cada agente está custando em tokens e dinheiro, sem precisar cruzar logs manualmente.

## Prompt para Antigravity

```
No `dev_agent.py`, detectar o padrão `custo {agente}`, cruzar 
`logs/finops/billing_daily.json` com `logs/executions/*.json` 
filtrando pelo campo `agent`. Retornar: total de tokens 
consumidos, custo estimado em USD e número de execuções, 
tudo do dia atual e da semana.
```

## Arquivos Envolvidos
- `src/agents/dev_agent.py`
- `src/storage/finops_manager.py`

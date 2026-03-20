# TASK-05 | Histórico de Custo por Agente

## Metadata
| Campo | Valor |
|---|---|
| ID | TASK-05 |
| Grupo | Ideias Novas |
| Prioridade | Alta |
| Responsável | FinOpsGuardian |
| Status | Aberto |

## Prompt para Antigravity

```
No `src/storage/finops_manager.py`, adicionar campo 
`agent_name` no `log_usage()`. No endpoint `GET /api/stats`, 
retornar um breakdown de custo por agente. Exibir como 
gráfico de barras na aba FinOps do dashboard.
```

## Arquivos Envolvidos
- `src/storage/finops_manager.py`
- `entrypoint.py`
- `frontend/src/App.jsx`

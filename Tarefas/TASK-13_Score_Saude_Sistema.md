# TASK-13 | Score de Saúde do Sistema

## Metadata
| Campo | Valor |
|---|---|
| ID | TASK-13 |
| Grupo | Ideias Novas |
| Prioridade | Alta |
| Responsável | QualityInspector |
| Status | Aberto |

## Prompt para Antigravity

```
Criar endpoint `GET /api/health-score` no `entrypoint.py` 
que calcula uma nota de 0-100 baseada em: % de tarefas 
concluídas, custo abaixo do budget, agentes com system_prompt 
preenchido e Knowledge Graph com mais de 10 nós. Exibir 
como métrica principal no Overview do dashboard.
```

## Arquivos Envolvidos
- `entrypoint.py`
- `frontend/src/App.jsx`

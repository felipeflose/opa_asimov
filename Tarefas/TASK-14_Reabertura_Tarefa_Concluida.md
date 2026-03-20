# TASK-14 | Reabertura de Tarefa Concluída

## Metadata
| Campo | Valor |
|---|---|
| ID | TASK-14 |
| Grupo | Ideias Novas |
| Prioridade | Média |
| Responsável | FrontendAgent |
| Status | Aberto |

## Prompt para Antigravity

```
No `frontend/src/App.jsx`, no card de tarefas com status 
`Concluído`, adicionar botão `↩ Reabrir` que chama 
`POST /api/tasks/update-status` com `status=Aberto` e 
reseta `budget_approved` para `false` no registry.
```

## Arquivos Envolvidos
- `frontend/src/App.jsx`
- `entrypoint.py`

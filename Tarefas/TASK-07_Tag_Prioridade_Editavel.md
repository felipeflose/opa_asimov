# TASK-07 | Tag de Prioridade Editável no Kanban

## Metadata
| Campo | Valor |
|---|---|
| ID | TASK-07 |
| Grupo | Ideias Novas |
| Prioridade | Média |
| Responsável | FrontendAgent |
| Status | Aberto |

## Prompt para Antigravity

```
No `frontend/src/App.jsx`, no card de cada tarefa do Kanban, 
adicionar um `<select>` inline com as opções Alta/Média/Baixa 
que chama `PATCH /api/tasks/update-status` ao mudar, 
atualizando `priority` no `demands/registry.json`.
```

## Arquivos Envolvidos
- `frontend/src/App.jsx`
- `entrypoint.py`

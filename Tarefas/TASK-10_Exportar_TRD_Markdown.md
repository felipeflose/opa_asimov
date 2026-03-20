# TASK-10 | Exportar TRD como Markdown

## Metadata
| Campo | Valor |
|---|---|
| ID | TASK-10 |
| Grupo | Ideias Novas |
| Prioridade | Baixa |
| Responsável | FrontendAgent |
| Status | Aberto |

## Prompt para Antigravity

```
Criar endpoint `GET /api/tasks/{task_id}/export` no 
`entrypoint.py` que retorna a tarefa formatada como `.md` 
com título, objetivo, agente responsável e histórico de 
execuções. No frontend, adicionar botão de download no 
card da tarefa concluída.
```

## Arquivos Envolvidos
- `entrypoint.py`
- `frontend/src/App.jsx`

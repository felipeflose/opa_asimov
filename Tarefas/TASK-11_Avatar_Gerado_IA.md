# TASK-11 | Avatar Gerado por IA para Agentes

## Metadata
| Campo | Valor |
|---|---|
| ID | TASK-11 |
| Grupo | Ideias Novas |
| Prioridade | Baixa |
| Responsável | FrontendAgent |
| Status | Aberto |

## Prompt para Antigravity

```
No `entrypoint.py`, no endpoint `POST /api/agents`, ao criar 
um novo agente, chamar a URL 
`https://api.dicebear.com/7.x/bottts/svg?seed={agent_name}` 
e salvar a URL no campo `avatar` do `agents/registry.json` 
automaticamente.
```

## Arquivos Envolvidos
- `entrypoint.py`

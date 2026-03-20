# TASK-22 | Score de Complementaridade no Agent Library

## Metadata
| Campo | Valor |
|---|---|
| ID | TASK-22 |
| Grupo | Agentes Colaborativos |
| Prioridade | Baixa |
| Responsável | FrontendAgent |
| Status | Aberto |

## Prompt para Antigravity

```
No endpoint `GET /api/agents` do `entrypoint.py`, adicionar 
campo `complementary_agents: list[str]` calculado a partir do 
`affinity_matrix.json`. No `frontend/src/App.jsx`, exibir no 
card de cada agente os top 2 agentes com maior afinidade como 
badges clicáveis.
```

## Arquivos Envolvidos
- `entrypoint.py`
- `frontend/src/App.jsx`

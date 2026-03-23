# TASK-16 | Afinidade entre Agentes (Agent Affinity Score)

## Metadata
| Campo | Valor |
|---|---|
| ID | TASK-16 |
| Grupo | Agentes Colaborativos |
| Prioridade | Alta |
| Responsável | CognitiveOrchestrator |
| Status | Aberto |

## Objetivo
Criar visibilidade de quais agentes naturalmente trabalham juntos, permitindo análises cruzadas mais inteligentes.

## Prompt para Antigravity

```
Em `src/orchestrator/cognitive_orchestrator.py`, após cada 
execução bem-sucedida via `execute_decision`, registrar no GCS 
em `agents/affinity_matrix.json` qual agente foi chamado em 
sequência de qual outro. Calcular afinidade como: 
(co-execuções / total_execuções) * 100. Exibir como heatmap 
na aba Agent Library do `frontend/src/App.jsx`.
```

## Arquivos Envolvidos
- `src/orchestrator/cognitive_orchestrator.py`
- `frontend/src/App.jsx`
- `agents/affinity_matrix.json` (novo arquivo no GCS)

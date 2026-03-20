# TASK-23 | Memória Compartilhada entre Agentes

## Metadata
| Campo | Valor |
|---|---|
| ID | TASK-23 |
| Grupo | Agentes Colaborativos |
| Prioridade | Alta |
| Responsável | CognitiveOrchestrator |
| Status | Conclu�do |

## Objetivo
Fazer com que descobertas de um agente sejam automaticamente disponíveis para outros, sem intervenção manual.

## Cenário Real
FinOpsGuardian descobre que o Cloud Run está caro → escreve na memória compartilhada → QualityInspector já tem esse contexto na próxima execução.

## Prompt para Antigravity

```
Criar `src/storage/shared_memory.py` com métodos `write(agent, 
key, value)` e `read(key)` que persistem em `agents/shared_
memory.json` no GCS. No `cognitive_orchestrator.py`, antes de 
chamar qualquer agente via `execute_decision`, injetar no 
prompt as últimas 15 entradas da memória compartilhada 
relevantes ao tema (busca por keyword no campo `key`).
```

## Arquivos Envolvidos
- `src/storage/shared_memory.py` (novo arquivo)
- `src/orchestrator/cognitive_orchestrator.py`

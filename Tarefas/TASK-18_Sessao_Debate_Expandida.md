# TASK-18 | Sessão de Debate Expandida

## Metadata
| Campo | Valor |
|---|---|
| ID | TASK-18 |
| Grupo | Agentes Colaborativos |
| Prioridade | Média |
| Responsável | DebateAgent |
| Status | Aberto |

## Objetivo
Evoluir o DebateAgent de dois lados (pro/con) para N perspectivas, onde cada agente registrado argumenta com sua especialidade.

## Cenário Real
"devemos expandir para AWS?" → FinOpsGuardian (custo), QualityInspector (risco), BriefingAgent (estratégia) debatem simultaneamente.

## Prompt para Antigravity

```
No `src/agents/debate_agent.py`, evoluir o método `debate()` 
para aceitar uma lista de `agents: list[str]`. Para cada agente 
na lista, chamar seu `system_prompt` do `agents/registry.json` 
como persona do argumento. O juiz recebe N perspectivas ao 
invés de só pro/con. Retornar qual agente "venceu" o debate 
e com qual % de confiança.
```

## Arquivos Envolvidos
- `src/agents/debate_agent.py`

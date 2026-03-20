# TASK-25 | DevAgent — Especialista Técnico do Código

## Metadata
| Campo | Valor |
|---|---|
| ID | TASK-25 |
| Grupo | Cozinha (Modo Dev) |
| Prioridade | Alta |
| Responsável | CognitiveOrchestrator |
| Status | Aberto |

## Objetivo
Ter um agente que conhece o próprio codebase e responde perguntas técnicas sem precisar abrir o código ou o terminal.

## Cenário Real
`/cozinha` → "por que o VisionAgent não está sendo chamado?" → DevAgent lê o fluxo do `telegram_agent.py` e explica o roteamento.

## Prompt para Antigravity

```
Criar `src/agents/dev_agent.py` com system_prompt focado 
exclusivamente em responder perguntas sobre o próprio codebase. 
No `__init__`, carregar como contexto fixo: a estrutura de 
arquivos do projeto, os nomes de todos os endpoints do 
`entrypoint.py` e a lista de agentes do `agents/registry.json`. 
Responder perguntas como "qual arquivo cuida do billing?", 
"quantos endpoints existem?" ou "o que acontece quando chega 
uma imagem no bot?".
```

## Arquivos Envolvidos
- `src/agents/dev_agent.py` (novo arquivo)
- `entrypoint.py`

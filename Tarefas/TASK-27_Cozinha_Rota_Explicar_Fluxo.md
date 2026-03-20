# TASK-27 | /cozinha rota — Explicar Fluxo de uma Mensagem

## Metadata
| Campo | Valor |
|---|---|
| ID | TASK-27 |
| Grupo | Cozinha (Modo Dev) |
| Prioridade | Média |
| Responsável | DevAgent |
| Status | Aberto |

## Objetivo
Entender rapidamente por quais arquivos e métodos uma mensagem passa, sem precisar ler o código.

## Cenário Real
"rota de uma imagem enviada no Telegram" → resposta: `telegram_agent.py` → `VisionAgent` → `cognitive_orchestrator.py` → GCS.

## Prompt para Antigravity

```
No `dev_agent.py`, detectar a keyword `rota` e acionar o 
Gemini com o system_prompt do projeto completo + a pergunta. 
Responder explicando passo a passo por quais arquivos e 
métodos uma mensagem passaria.
```

## Arquivos Envolvidos
- `src/agents/dev_agent.py`

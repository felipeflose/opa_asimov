# TASK-17 | Pipeline Multi-Agente via Telegram

## Metadata
| Campo | Valor |
|---|---|
| ID | TASK-17 |
| Grupo | Agentes Colaborativos |
| Prioridade | Alta |
| Responsável | TelegramAgent |
| Status | Aberto |

## Objetivo
Permitir análises combinadas diretamente pelo Telegram, onde o output de um agente alimenta o próximo automaticamente.

## Cenário Real
"analise custo + qualidade das tarefas desta semana" → FinOpsGuardian gera relatório → QualityInspector analisa em cima.

## Prompt para Antigravity

```
No `telegram_agent.py`, detectar mensagens com o padrão 
"analise [X] + [Y]" e criar uma pipeline sequencial no 
`cognitive_orchestrator.py`: o output do primeiro agente 
vira o input do segundo. Salvar o resultado composto em 
`logs/pipelines/{timestamp}.json` e retornar no Telegram 
como uma mensagem unificada com seções por agente.
```

## Arquivos Envolvidos
- `src/agents/telegram_agent.py`
- `src/orchestrator/cognitive_orchestrator.py`

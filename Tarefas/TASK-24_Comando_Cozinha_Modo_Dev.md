# TASK-24 | Comando /cozinha — Ativar Modo Dev

## Metadata
| Campo | Valor |
|---|---|
| ID | TASK-24 |
| Grupo | Cozinha (Modo Dev) |
| Prioridade | Alta |
| Responsável | TelegramAgent |
| Status | Aberto |

## Objetivo
Criar uma sessão de bastidores no Telegram onde todas as perguntas são respondidas com foco técnico no próprio codebase, separado do fluxo normal de comandos.

## Prompt para Antigravity

```
No `telegram_agent.py`, criar handler `/cozinha` que seta 
`dev_mode: true` em `users/{user_id}/preferences.json` no GCS. 
Quando ativo, todas as mensagens seguintes são roteadas para 
um `DevAgent` dedicado ao invés do `CognitiveOrchestrator` 
padrão. Sair do modo com `/cozinha off`.
```

## Arquivos Envolvidos
- `src/agents/telegram_agent.py`
- `src/agents/dev_agent.py` (depende da TASK-25)

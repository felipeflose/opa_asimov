# TASK-12 | Modo Silencioso no Telegram

## Metadata
| Campo | Valor |
|---|---|
| ID | TASK-12 |
| Grupo | Ideias Novas |
| Prioridade | Baixa |
| Responsável | TelegramAgent |
| Status | Aberto |

## Prompt para Antigravity

```
Adicionar comando `/silencio` no `telegram_agent.py` que 
seta um flag `silent_mode: true` em 
`users/{user_id}/preferences.json` no GCS. Quando ativo, 
o bot só responde se a mensagem começar com `/` ou mencionar 
o nome do bot.
```

## Arquivos Envolvidos
- `src/agents/telegram_agent.py`

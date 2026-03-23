# TASK-08 | Comando /debug no Telegram

## Metadata
| Campo | Valor |
|---|---|
| ID | TASK-08 |
| Grupo | Ideias Novas |
| Prioridade | Média |
| Responsável | TelegramAgent |
| Status | Aberto |

## Prompt para Antigravity

```
Criar handler `/debug` no `telegram_agent.py` visível apenas 
se `update.effective_user.id` estiver em uma lista de admins 
no `.env`. Retorna: versão do modelo Gemini ativo, total de 
nós no Knowledge Graph e uptime do container.
```

## Arquivos Envolvidos
- `src/agents/telegram_agent.py`
- `.env` (nova variável `ADMIN_USER_IDS`)

# TASK-01 | Comando /status no Telegram

## Metadata
| Campo | Valor |
|---|---|
| ID | TASK-01 |
| Grupo | Ideias Novas |
| Prioridade | Alta |
| Responsável | TelegramAgent |
| Status | Concluído |

## Prompt para Antigravity

```
Criar handler `/status` no `telegram_agent.py` que retorna 
em uma mensagem: total de tarefas abertas, custo do dia 
(via FinOpsManager) e último agente executado, tudo em 
uma linha cada.
```

## Arquivos Envolvidos
- `src/agents/telegram_agent.py`
- `src/storage/finops_manager.py`

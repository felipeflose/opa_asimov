# TRD-P04 | Alerta de Tarefas Paradas

## Metadata
| Campo | Valor |
|---|---|
| ID | TRD-P04 |
| Grupo | Produto |
| Prioridade | Média |
| Responsável | ProactiveAlertAgent |
| Status | Aberto |

## Objetivo
Fechar o loop de gestão do Kanban notificando automaticamente quando tarefas ficam sem movimentação, evitando backlog esquecido.

## Prompt para Antigravity

```
No `entrypoint.py`, crie um endpoint `GET /api/tasks/stale` que lê 
`demands/registry.json`, filtra tarefas com status `Aberto` ou 
`Em Progresso` e `updated_at` há mais de 24h, e dispara uma mensagem 
via Telegram Bot API para o `TELEGRAM_CHAT_ID` com o ID e título de 
cada tarefa parada. Adicione uma chamada a esse endpoint no ciclo de 
vida do Cloud Run usando Cloud Scheduler (cron: `0 9 * * *`).
```

## Arquivos Envolvidos
- `entrypoint.py`
- `deploy_gcp.ps1` (configuração do Cloud Scheduler)

## Critério de Conclusão
- Endpoint `/api/tasks/stale` funcional
- Mensagem chegando no Telegram com tarefas paradas
- Cloud Scheduler configurado para rodar às 9h diariamente

# TRD-P03 | Memória Conversacional por Usuário

## Metadata
| Campo | Valor |
|---|---|
| ID | TRD-P03 |
| Grupo | Produto |
| Prioridade | Média |
| Responsável | CognitiveOrchestrator |
| Status | Aberto |

## Objetivo
Eliminar a necessidade de o usuário repetir contexto a cada nova sessão no Telegram, tornando o bot progressivamente mais inteligente por usuário.

## Prompt para Antigravity

```
No `src/agents/telegram_agent.py`, após cada resposta do orquestrador, 
salve o par (user_input, response) no GCS em 
`users/{user_id}/memory/history.json`, mantendo os últimos 10 turnos. 
No `cognitive_orchestrator.py`, no método `process_command`, leia esse 
histórico do GCS e injete-o no system prompt antes da chamada ao Gemini.
```

## Arquivos Envolvidos
- `src/agents/telegram_agent.py`
- `src/orchestrator/cognitive_orchestrator.py`

## Critério de Conclusão
- Histórico de 10 turnos salvo por `user_id` no GCS
- Contexto injetado automaticamente em cada nova mensagem

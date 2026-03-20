# TASK-31 | /cozinha endpoint {nome} — Testar Endpoint ao Vivo

## Metadata
| Campo | Valor |
|---|---|
| ID | TASK-31 |
| Grupo | Cozinha (Modo Dev) |
| Prioridade | Média |
| Responsável | DevAgent |
| Status | Aberto |

## Objetivo
Testar qualquer endpoint da API em produção diretamente pelo Telegram, sem precisar abrir o Postman ou o terminal.

## Cenário Real
"endpoint stats está retornando algo?" → DevAgent chama o endpoint e retorna status + resposta em 3 segundos.

## Prompt para Antigravity

```
No `dev_agent.py`, detectar o padrão `endpoint {nome}`, fazer 
uma chamada interna via `httpx` para o próprio FastAPI 
(`localhost:8080/api/{nome}`) usando o `MASTER_KEY` do env, 
e retornar no Telegram: status code, tempo de resposta em ms 
e os primeiros 200 chars do JSON retornado.
```

## Arquivos Envolvidos
- `src/agents/dev_agent.py`

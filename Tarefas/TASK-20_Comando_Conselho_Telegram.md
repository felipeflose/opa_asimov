# TASK-20 | Comando /conselho no Telegram

## Metadata
| Campo | Valor |
|---|---|
| ID | TASK-20 |
| Grupo | Agentes Colaborativos |
| Prioridade | Alta |
| Responsável | TelegramAgent |
| Status | Aberto |

## Objetivo
Acionar todos os agentes em paralelo para uma pergunta estratégica e receber uma síntese de perspectivas em uma única mensagem.

## Cenário Real
"/conselho vale a pena integrar com Stripe agora?" → cada agente responde da sua perspectiva, orquestrador sintetiza em uma mensagem final.

## Prompt para Antigravity

```
Criar handler `/conselho {pergunta}` no `telegram_agent.py` 
que aciona todos os agentes registrados com tools preenchidas 
em paralelo (usando `asyncio.gather`), coleta suas respostas 
e passa para o `cognitive_orchestrator.py` sintetizar em uma 
resposta final com o posicionamento de cada agente. Retornar 
no Telegram como mensagem formatada com o nome de cada agente 
e sua perspectiva em 1 frase.
```

## Arquivos Envolvidos
- `src/agents/telegram_agent.py`
- `src/orchestrator/cognitive_orchestrator.py`

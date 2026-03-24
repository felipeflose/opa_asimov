# TRD-P01 | Onboarding do Bot Telegram

## Metadata
| Campo | Valor |
|---|---|
| ID | TRD-P01 |
| Grupo | Produto |
| Prioridade | Alta |
| Responsável | TelegramAgent |
| Status | Aberto |

## Objetivo
Criar uma experiência de primeiro contato clara para novos usuários do bot, eliminando a fricção de não saber quais comandos existem.

## Prompt para Antigravity

```
No arquivo `src/agents/telegram_agent.py`, no método `start_handler`, 
substitua a mensagem atual por uma que liste os comandos disponíveis 
com exemplos reais de uso. Adicione um CommandHandler para `/ajuda` 
que envia um InlineKeyboardMarkup com os 5 comandos mais usados como 
botões. Os botões devem disparar o comando correspondente ao serem 
clicados.
```

## Arquivos Envolvidos
- `src/agents/telegram_agent.py`

## Critério de Conclusão
- Comando `/ajuda` funcional no Telegram
- Botões inline disparando os comandos corretamente
- Mensagem de boas-vindas no `/start` atualizada

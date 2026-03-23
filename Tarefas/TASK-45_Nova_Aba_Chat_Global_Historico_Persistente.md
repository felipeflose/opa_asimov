# TASK-45 | Nova Aba: Chat Global com Histórico Persistente

## Metadata
| Campo | Valor |
|---|---|
| ID | TASK-45 |
| Grupo | Nova Funcionalidade / IA |
| Prioridade | Alta |
| Responsável | FrontendAgent |
| Status | Aberto |

## Problema Identificado
O dashboard React não tem nenhuma forma de conversar com o Cognitive Orchestrator diretamente. Toda a interação conversacional está confinada ao Telegram. O Command Center do Streamlit tinha uma aba "💬 Chat" com histórico de sessão — isso foi perdido na migração React.

Para aprovar tarefas, criar agentes ou executar ações via linguagem natural, o usuário precisa sair do dashboard e ir para o Telegram. Isso quebra o fluxo de trabalho.

## Objetivo
Criar uma aba "Chat" no dashboard React que permite conversar com o Orchestrator, ver o reasoning chain de cada resposta, e ter o histórico salvo no GCS por sessão.

## Cenário Real
Usuário está no dashboard → abre aba "Chat" → digita "crie um agente especialista em análise de SEO" → vê o reasoning chain aparecer primeiro em um collapsible → depois a resposta final → o agente é criado e aparece na Agent Library automaticamente.

## Prompt para Antigravity

```
No `frontend/src/App.jsx`:

1. Adicionar aba "💬 Chat" na sidebar (posição 2, logo abaixo do Dashboard).

2. Estados necessários:
   - `chatMessages`: array de `{ role, content, reasoning, timestamp }`
   - `chatInput`: string
   - `chatLoading`: boolean
   - `sessionId`: gerado uma vez por sessão (Date.now())

3. Componente `<ChatView />`:

   a. HEADER: "Global Orchestrator Chat", session ID mascarado, 
      botão "Nova Sessão" (limpa chatMessages).

   b. MESSAGES AREA: `height: calc(100vh - 280px)`, overflow-y: auto,
      padding 20px, fundo levemente diferente do background.
      
      Cada mensagem de user: alinhada à direita, fundo 
      `rgba(0,242,255,0.08)`, borda cyan, border-radius `18px 18px 4px 18px`.
      
      Cada mensagem de assistant: alinhada à esquerda, fundo 
      `rgba(255,255,255,0.03)`, border `1px solid var(--border)`,
      border-radius `18px 18px 18px 4px`.

   c. REASONING CHAIN COLLAPSIBLE: antes de cada resposta da IA,
      mostrar `<details>` com summary "🧠 Ver Reasoning Chain" e 
      o conteúdo do campo `reasoning` da response em texto muted 
      tamanho 0.8rem. Default: fechado.

   d. TYPING INDICATOR: quando `chatLoading`, mostrar na área 
      de messages um card de "assistant" com 3 dots animados 
      (CSS animation bounce sequencial: ●●●).

   e. INPUT AREA: textarea que expande com o conteúdo (max 5 linhas),
      botão de envio com ícone → e suporte a `Shift+Enter` para 
      nova linha, `Enter` para enviar.

4. FUNÇÃO sendMessage():
   - Adiciona user message ao estado
   - Seta chatLoading = true
   - Chama `POST /api/chat` com `{ message, history: chatMessages }`
   - Recebe `{ response, reasoning }` 
   - Adiciona assistant message
   - Chama `fetchData()` para atualizar stats (agentes/tasks criados)

5. No `entrypoint.py`, criar endpoint `POST /api/chat`:
   - Recebe message + history
   - Chama `orchestrator.process_command(message, chat_history=history)`
   - Chama `orchestrator.execute_decision(decision)`
   - Retorna `{ response, reasoning, action }`

6. Persistência: salvar chatMessages no GCS via 
   `POST /api/chat/save` ao final de cada troca, 
   em `logs/chats/{sessionId}.json`.
```

## Arquivos Envolvidos
- `frontend/src/App.jsx`
- `entrypoint.py` (endpoints POST /api/chat e POST /api/chat/save)
- `frontend/src/index.css`

## Critério de Conclusão
- Chat funcional com o Orchestrator real
- Reasoning chain visível em collapsible
- Histórico persiste na sessão (não some ao trocar de aba)
- Typing indicator durante o loading
- Enter para enviar, Shift+Enter para nova linha
- fetchData() chamado após cada resposta para refletir mudanças

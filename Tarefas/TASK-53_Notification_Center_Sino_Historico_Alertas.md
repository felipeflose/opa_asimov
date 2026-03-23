# TASK-53 | Notification Center: Sino com Histórico de Alertas

## Metadata
| Campo | Valor |
|---|---|
| ID | TASK-53 |
| Grupo | Nova Funcionalidade / UX |
| Prioridade | Média |
| Responsável | FrontendAgent |
| Status | Aberto |

## Problema Identificado
O sistema tem um `ProactiveAlertAgent` que detecta anomalias e envia alertas no Telegram. Porém, esses alertas não aparecem em lugar nenhum no dashboard. Se o usuário não estiver com o Telegram aberto, perde os alertas.

Além disso, não há histórico centralizado de: tarefas completadas, agentes criados, custo ultrapassado, degradação de accuracy — tudo acontece "nos bastidores" sem visibilidade no dashboard.

## Objetivo
Criar um Notification Center acessível por um ícone de sino 🔔 no header com badge de contagem, que mostra o histórico de eventos e alertas do sistema em um dropdown lateral.

## Cenário Real
Usuário vê `🔔 3` no header → clica → painel desliza da direita → mostra:
- `[ALERTA] FinOpsGuardian: custo 50% acima da média hoje`
- `[TAREFA] TRD-045 "Deploy API v2" concluída por SystemAgent`
- `[AGENTE] Novo agente "SEOAnalyzer" criado pelo Orchestrator`

## Prompt para Antigravity

```
No `frontend/src/App.jsx`:

1. SINO NO HEADER:
   `<button onClick={() => setNotifOpen(v => !v)}>🔔</button>`
   Badge absoluto no canto superior direito do sino:
   `unreadCount` em vermelho, desaparece quando `notifOpen`
   e all marcadas como lidas.
   
   Estado: `notifOpen` boolean, `notifications` array,
   `unreadCount` number.

2. PAINEL DE NOTIFICAÇÕES (drawer da direita):
   `position: fixed; top: 0; right: 0; height: 100vh; width: 360px`
   `transform: translateX(notifOpen ? '0' : '100%')`
   `transition: transform 0.3s cubic-bezier(0.4, 0, 0.2, 1)`
   `background: rgba(5,8,18,0.98); backdrop-filter: blur(20px)`
   `border-left: 1px solid var(--border); z-index: 2000`
   
   Header do painel: "Notification Center" + botão `[Mark All Read]`
   
   Lista de notificações, cada item:
   - Ícone por tipo: ⚠️ alerta, ✅ tarefa, 🤖 agente, 💰 custo
   - Título bold
   - Descrição em muted
   - Timestamp relativo ("3 min ago")
   - Ponto azul se `!read`
   - Borda esquerda colorida por tipo

3. GERAÇÃO DE NOTIFICAÇÕES:
   No `fetchData()`, após receber os dados, gerar notificações 
   baseadas em diff com o estado anterior:
   
   - Nova tarefa concluída (diff de `completedTasks.length`):
     `{ type: 'task', title: 'Tarefa concluída', desc: task.title }`
   
   - Novo agente (diff de `agentList.length`):
     `{ type: 'agent', title: 'Novo agente registrado', desc: agent.agent_name }`
   
   - Custo acima da média (calcular na chegada de stats):
     `{ type: 'alert', title: 'Custo elevado', desc: '50% acima da média' }`
   
   Adicionar ao array `notifications` via:
   `setNotifications(prev => [newNotif, ...prev].slice(0, 50))`
   E incrementar `unreadCount` se `!notifOpen`.

4. FECHAR:
   Clicar fora do painel (overlay) fecha.
   Clicar em uma notificação: navega para a aba relevante 
   (`setActiveTab(...)`) e fecha o painel.

5. PERSISTÊNCIA:
   Salvar `notifications` em `sessionStorage` para sobreviver 
   a troca de abas (não a refresh).
```

## Arquivos Envolvidos
- `frontend/src/App.jsx`
- `frontend/src/index.css`

## Critério de Conclusão
- Sino com badge de contagem visível no header
- Painel abre/fecha com animação suave
- Notificações geradas automaticamente via diff no fetchData
- Clicar em notificação navega para a aba correta
- Mark all read zera o badge

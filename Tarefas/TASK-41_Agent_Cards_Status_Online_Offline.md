# TASK-41 | Agent Cards com Status Online/Offline e Last Seen

## Metadata
| Campo | Valor |
|---|---|
| ID | TASK-41 |
| Grupo | Agent Library / UX |
| Prioridade | Média |
| Responsável | FrontendAgent |
| Status | Aberto |

## Problema Identificado
Os cards de agentes na Agent Library mostram apenas nome, propósito e métricas estáticas (runs, tokens). Não há:
- Indicação se o agente executou algo recentemente (está "ativo"?)
- "Last seen" — quando foi a última execução
- Status visual diferenciado para agentes sem nenhuma execução (dormentes)
- Visualização do system_prompt inline sem precisar abrir modal
- Nenhuma ação rápida no card (delegar uma tarefa, editar prompt)

## Objetivo
Redesenhar os agent cards para serem informativos e acionáveis, com status de atividade baseado no histórico de execuções e ações rápidas acessíveis diretamente no card.

## Cenário Real
Card do `FinOpsGuardian`: dot verde "ACTIVE · 2h ago" no canto superior direito. Métricas: "47 runs · 128k tokens". Barra de accuracy 85%. Botões rápidos: [▶ Executar] [✏️ Editar DNA] [📤 Exportar].

Card de agente sem execuções: dot cinza "DORMANT", sem barra de accuracy, texto "No executions yet" em muted.

## Prompt para Antigravity

```
No `frontend/src/App.jsx`, na aba 'Agent Library', 
substituir os agent cards por um componente `<AgentCard />` 
com as seguintes propriedades visuais e funcionais:

1. STATUS INDICATOR no canto superior direito:
   - Se `agent.metrics.executions > 0` e última execução 
     há menos de 24h → dot verde pulsante + "ACTIVE"
   - Se `agent.metrics.executions > 0` mas > 24h → 
     dot amarelo + "IDLE · Xh ago"
   - Se `agent.metrics.executions === 0` → dot cinza + "DORMANT"
   
   Calcular "last seen" a partir de `agent.metrics.last_execution` 
   (adicionar este campo no BaseAgent.run() ao salvar o JSON).

2. ACCURACY BAR inline no card (não só no Quality Inspector):
   - Barra horizontal fina (4px height) na base do card
   - Cor dinâmica: verde > 70%, amarelo 40-70%, vermelho < 40%

3. QUICK ACTIONS (3 botões icon-only com tooltip):
   - ▶ → abre modal de execução rápida (input de tarefa + botão run)
   - ✏️ → abre inline editor do system_prompt (textarea substituindo o <p>)
   - 📤 → chama `handleExport(agent.agent_name)`

4. INLINE PROMPT PREVIEW: 
   - system_prompt truncado em 2 linhas com `webkit-line-clamp: 2`
   - Expandir/colapsar via click com animação de altura

5. TOOLS BADGES: cada tool como chip colorido 
   (fundo `rgba(0,242,255,0.08)`, borda cyan, texto monospace 0.6rem)

6. AVATAR: se `agent.avatar` é URL dicebear, renderizar como 
   `<img>` 50x50 com `border-radius: 50%` e border cyan.
   Fallback: 2 letras iniciais com background gradiente.

Adicionar campo `last_execution` no `BaseAgent.run()` 
no `base_agent.py` ao atualizar o JSON do agente.
```

## Arquivos Envolvidos
- `frontend/src/App.jsx`
- `AtualizaAI/src/agents/base_agent.py` (campo last_execution)

## Critério de Conclusão
- Status dot correto baseado em timestamp real
- Quick actions funcionais nos 3 botões
- Inline edit do prompt salva via `POST /api/agents/update`
- Tools badges visíveis no card
- Layout não quebra com nomes de agentes longos

# TASK-38 | Live Activity Feed com Polling Inteligente

## Metadata
| Campo | Valor |
|---|---|
| ID | TASK-38 |
| Grupo | Real-time / Dashboard |
| Prioridade | Alta |
| Responsável | FrontendAgent |
| Status | Aberto |

## Problema Identificado
O painel de "Recent Activity (Telegram)" no Dashboard atualiza apenas a cada 30 segundos via `setInterval`. Não há nenhuma indicação visual de que o sistema está vivo entre os refreshes. O feed parece estático e morto para o usuário.

Além disso, novos eventos (mensagem chegando no Telegram, tarefa completada, agente criado) não aparecem automaticamente — o usuário precisa esperar o próximo ciclo de 30s ou clicar em "Refresh".

## Objetivo
Criar um sistema de polling inteligente para o Activity Feed: verificação a cada 5s com diff inteligente (só renderiza se houver novos itens), animação de entrada para novos eventos, e indicador visual "● LIVE" pulsante.

## Cenário Real
O painel mostra "● LIVE" piscando em verde. A cada 5s, se houver nova atividade do Telegram ou execução, o novo item aparece no topo com animação slide-down + flash de highlight por 2 segundos.

## Prompt para Antigravity

```
No `frontend/src/App.jsx`:

1. Criar estado `activityPollInterval` separado de 5000ms 
   apenas para o activity feed (independente do fetchData global).

2. Criar função `fetchActivity()` isolada que chama apenas 
   `GET /api/activity` e compara com o estado anterior via 
   hash (JSON.stringify do primeiro item). Só atualiza o estado 
   `activity` se o primeiro item for diferente do atual.

3. Criar estado `newActivityIds` (Set) que marca itens recém-chegados. 
   Limpar o highlight após 2000ms via setTimeout.

4. No JSX do activity feed, adicionar no header:
   - Dot pulsante: `<span style={{color:'#00ff80'}}>●</span> LIVE`
   - Keyframe `pulse` no dot: opacity 1 → 0.3 → 1, 1.5s infinite

5. Cada item do feed com classe condicional `new-item` quando 
   está em `newActivityIds`:
   - `animation: highlightIn 0.4s ease` (fundo flash cyan)
   - Border-left 3px cyan temporária

6. Adicionar ícone contextual por tipo de atividade:
   - Se `act.agent` inclui "Telegram" → 📱
   - Se `act.agent` inclui "Vision" → 👁️
   - Se `act.type === 'execution'` → ⚡
   - Default → 🤖

7. Formatar timestamp relativo: "2 min ago", "just now", "1h ago"
   ao invés do `toLocaleTimeString()` atual.
```

## Arquivos Envolvidos
- `frontend/src/App.jsx`
- `frontend/src/index.css`

## Critério de Conclusão
- Feed atualiza a cada 5s sem piscar a tela inteira
- Novos itens aparecem com animação de entrada
- Indicator LIVE visível e pulsante
- Timestamps relativos legíveis
- Sem memory leak no interval ao trocar de aba

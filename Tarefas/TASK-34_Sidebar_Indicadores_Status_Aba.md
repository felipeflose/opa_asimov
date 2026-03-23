# TASK-34 | Sidebar com Indicadores de Status por Aba

## Metadata
| Campo | Valor |
|---|---|
| ID | TASK-34 |
| Grupo | UX / Navigation |
| Prioridade | Alta |
| Responsável | FrontendAgent |
| Status | Aberto |

## Problema Identificado
A sidebar atual é uma lista de textos simples. Não há nenhuma indicação de:
- Quantas tarefas abertas existem (badge no "Task Manager")
- Se há alertas ativos (badge no "Quality Inspector")
- Se o custo está acima do normal (indicador no "FinOps Guardian")
- Qual aba está ativa visualmente (além do highlight de cor)

O usuário precisa entrar em cada aba para saber se há algo urgente. Isso é um problema crítico de UX em um sistema de monitoramento.

## Objetivo
Enriquecer cada item da sidebar com badges de contagem e indicadores de status em tempo real, tornando a sidebar um painel de alertas passivo.

## Cenário Real
Usuário olha para a sidebar e vê:
- `Task Manager` com badge `[3]` em amarelo → sabe que há 3 tarefas abertas
- `Quality Inspector` com ponto vermelho pulsante → há agentes com accuracy < 50%
- `FinOps Guardian` com badge `$2.40` em verde → custo do dia
- `DORA Metrics` com badge `2 deploys` em cyan

## Prompt para Antigravity

```
No `frontend/src/App.jsx`, refatorar o mapa de abas da sidebar 
de um array de strings simples para um array de objetos:

const TABS = [
  { id: 'Dashboard', icon: '⚡', badge: null },
  { id: 'Cognitive Map', icon: '🧬', badge: null },
  { id: 'Task Manager', icon: '📋', badge: stats.tasks, badgeColor: '#f59e0b' },
  { id: 'Agent Library', icon: '🤖', badge: stats.agents },
  { id: 'Pipeline', icon: '🏗️', badge: null },
  { id: 'Marketplace', icon: '🛒', badge: null },
  { id: 'Quality Inspector', icon: '🔍', badge: qaAlert ? '!' : null, badgeColor: '#ff4d4d' },
  { id: 'FinOps Guardian', icon: '💎', badge: stats.cost, badgeColor: '#00ff80' },
  { id: 'DORA Metrics', icon: '📈', badge: null },
  { id: 'Settings', icon: '⚙️', badge: null },
];

Renderizar cada item com:
- Ícone à esquerda (font-size 1rem)
- Label no centro
- Badge à direita: círculo pequeno com número ou texto curto
- Ponto pulsante animado (keyframe `pulse`) se badgeColor for red

O estado `qaAlert` é calculado como: 
`qaReport?.summary?.avg_accuracy < 60`
```

## Arquivos Envolvidos
- `frontend/src/App.jsx`
- `frontend/src/App.css` (estilos do badge pulsante)

## Critério de Conclusão
- Badges atualizam a cada 30s junto com o fetchData
- Badge de Task Manager some quando tasks = 0
- Ponto vermelho pulsante aparece quando avg_accuracy < 60%
- Layout não quebra com textos longos nos badges

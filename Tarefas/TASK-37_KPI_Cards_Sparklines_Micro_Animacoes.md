# TASK-37 | KPI Cards com Sparklines e Micro-Animações

## Metadata
| Campo | Valor |
|---|---|
| ID | TASK-37 |
| Grupo | Design / Dashboard |
| Prioridade | Média |
| Responsável | FrontendAgent |
| Status | Aberto |

## Problema Identificado
Os 4 KPI cards do Dashboard (Tokens, Cost, Active Agents, Pending Tasks) são estáticos e genéricos. Mostram apenas um número com uma barra colorida de largura fixa (60%). Não há:
- Contexto histórico (o custo está subindo ou caindo?)
- Animação de entrada que dê sensação de sistema vivo
- Diferenciação visual entre cards positivos e negativos
- Trend indicator (seta para cima/baixo)

## Objetivo
Redesenhar os KPI cards com sparklines SVG inline, animação de counter ao carregar, indicadores de trend e cores dinâmicas baseadas no estado (seguro/alerta/crítico).

## Cenário Real
Card de custo mostra `$2.40` com seta verde ↓ (abaixo da média) e um mini gráfico de linha dos últimos 7 dias. Card de tasks pendentes mostra `3` com seta vermelha ↑ e pulsa suavemente.

## Prompt para Antigravity

```
No `frontend/src/App.jsx`, substituir os 4 glass-cards do KPI 
grid por um componente `<KpiCard />` com as seguintes props:
- `label`: string
- `value`: string (ex: "2.4k", "$2.40", "3")
- `trend`: 'up' | 'down' | 'neutral'
- `trendGood`: boolean (up é bom? ex: para agents=true, para cost=false)
- `sparkData`: array de números (últimos 7 valores)
- `icon`: string emoji

Visual do KpiCard:
1. Gradiente sutil no fundo baseado no estado:
   - neutral: `rgba(255,255,255,0.03)`
   - good: `rgba(0,255,128,0.04)`
   - alert: `rgba(255,77,77,0.04)`

2. Ícone grande (2rem) no canto superior esquerdo com 
   background circular translúcido.

3. Valor principal com `CountUp animation`: usar `useEffect` 
   com `requestAnimationFrame` para animar de 0 até o valor 
   final em 800ms com easing `easeOutQuart`.

4. Indicador de trend: seta SVG (↑ ou ↓) com cor dinâmica:
   - Se `trendGood && trend === 'up'` → verde
   - Se `!trendGood && trend === 'up'` → vermelho
   - Inverso para down

5. Sparkline: SVG inline de 80x30px com polyline dos últimos 
   7 valores normalizados, cor do stroke matching o estado, 
   fill gradient abaixo da linha.

6. Border bottom de 2px com cor do estado (good/neutral/alert).

Calcular `sparkData` usando o histórico do `finops` summary 
para o card de custo, e contagem de tasks por dia para o 
card de tasks (se disponível; senão, array de zeros).
```

## Arquivos Envolvidos
- `frontend/src/App.jsx`
- `frontend/src/index.css`

## Critério de Conclusão
- Counter animado ao carregar a aba Dashboard
- Sparkline renderiza corretamente mesmo com dados zerados
- Cores dinâmicas refletem o estado atual
- Cards responsivos no grid (min 180px por card)

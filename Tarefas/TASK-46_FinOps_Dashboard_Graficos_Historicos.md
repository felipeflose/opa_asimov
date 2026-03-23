# TASK-46 | FinOps Dashboard com Gráficos Históricos Reais

## Metadata
| Campo | Valor |
|---|---|
| ID | TASK-46 |
| Grupo | FinOps / Design |
| Prioridade | Alta |
| Responsável | FrontendAgent |
| Status | Aberto |

## Problema Identificado
A aba "FinOps Guardian" atual é extremamente básica — apenas 3 linhas de texto estático:
- Total Estimated Cost
- Tokens Used
- API Request Volume

Não há:
- Gráfico de evolução do custo nos últimos 7 dias
- Breakdown de custo por agente
- Projeção de custo mensal
- Alertas visuais quando o custo está acima da média
- Comparação custo de IA vs custo de infraestrutura GCP

O FinOpsManager já coleta todos esses dados (por agente, por dia) mas o frontend não os exibe.

## Objetivo
Redesenhar completamente a aba FinOps em um dashboard analítico com gráficos SVG inline, breakdown por agente e projeções.

## Cenário Real
Usuário abre FinOps → vê gráfico de barras dos últimos 7 dias com custo diário → vê donut chart de distribuição por agente → banner de alerta se custo hoje > média × 1.5 → seção de projeção "At this rate: $X este mês".

## Prompt para Antigravity

```
No `frontend/src/App.jsx`, substituir a aba 'FinOps Guardian' 
por um componente `<FinOpsView />` com:

1. Criar endpoint `GET /api/finops/history` no `entrypoint.py` 
   que retorna o JSON completo de `logs/finops/billing_daily.json` 
   processado como array de 7 dias, incluindo breakdown por agente.

2. SEÇÃO 1 — OVERVIEW (3 KPI cards horizontais):
   - "Today's Spend": valor com cor (verde < $2, amarelo < $5, vermelho > $5)
   - "This Month (est)": custo hoje × dias restantes no mês
   - "AI vs Infra Split": percentual (ex: "IA 68% · GCP 32%")

3. SEÇÃO 2 — GRÁFICO DE BARRAS (SVG puro, sem lib externa):
   - Últimos 7 dias no eixo X (labels "Mon", "Tue"...)
   - Custo em USD no eixo Y
   - Barras com gradiente cyan → azul
   - Linha tracejada horizontal: média dos 7 dias
   - Tooltip ao hover na barra: "$0.042 · 12k tokens · 8 calls"
   - Animação de entrada: bars crescem de height 0 via CSS transform

4. SEÇÃO 3 — BREAKDOWN POR AGENTE (tabela + mini bars):
   Para cada agente em `billing_today.agents`:
   - Nome do agente
   - Tokens consumidos hoje
   - Custo em USD
   - Barra de proporção (% do total)
   Ordenado por custo DESC.

5. SEÇÃO 4 — ALERTAS:
   - Se custo hoje > média × 1.5: banner vermelho 
     "⚠️ Custo acima da média — revise o uso do Orchestrator"
   - Se algum agente consumiu > 40% do total sozinho: 
     banner amarelo com o nome do agente
   - Se custo total do mês projetado > $50: banner crítico

6. SEÇÃO 5 — MONTHLY PROJECTION:
   Mini card: "A este ritmo, o custo mensal estimado é $X.XX"
   Com indicador visual (semáforo verde/amarelo/vermelho).
```

## Arquivos Envolvidos
- `frontend/src/App.jsx`
- `entrypoint.py` (endpoint GET /api/finops/history)
- `frontend/src/index.css`

## Critério de Conclusão
- Gráfico de barras renderiza com dados reais dos últimos 7 dias
- Fallback para zeros quando não há histórico
- Breakdown por agente correto e ordenado
- Alertas disparam nas condições certas
- Animações de entrada funcionam

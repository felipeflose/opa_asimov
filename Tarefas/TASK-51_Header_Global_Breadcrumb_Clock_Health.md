# TASK-51 | Header Global com Breadcrumb, Clock e Health Indicator

## Metadata
| Campo | Valor |
|---|---|
| ID | TASK-51 |
| Grupo | UX / Navigation |
| Prioridade | Média |
| Responsável | FrontendAgent |
| Status | Aberto |

## Problema Identificado
O header atual é estático: sempre mostra "Welcome back, Director." e o horário. Não comunica:
- Em qual aba o usuário está (breadcrumb)
- O estado de saúde geral do sistema (health score)
- Se há operações em andamento (loading global)
- A versão do sistema

Além disso, o clock usa `new Date().toLocaleTimeString()` renderizado uma vez — não atualiza em tempo real sem um `setInterval` dedicado.

## Objetivo
Redesenhar o header global para ser um painel de status contextual com breadcrumb dinâmico, health indicator, clock em tempo real e indicador de operações em andamento.

## Cenário Real
Header mostra: `Flose AI > Task Manager` (breadcrumb) | `● SYSTEM HEALTHY 94/100` (score) | `10:42:33` (clock vivo) | spinner girando quando fetchData está ativo.

## Prompt para Antigravity

```
No `frontend/src/App.jsx`, refatorar o bloco `<header>`:

1. CLOCK EM TEMPO REAL:
   `const [clock, setClock] = useState('')`
   `useEffect(() => {`
   `  const t = setInterval(() => setClock(new Date().toLocaleTimeString()), 1000)`
   `  return () => clearInterval(t)`
   `}, [])`
   
   Renderizar no lugar do `new Date().toLocaleTimeString()` estático.

2. BREADCRUMB DINÂMICO:
   Ao invés de "Welcome back, Director." fixo:
   - Linha 1: `<span style={{opacity:0.4}}>Flose AI</span> › <strong>{activeTab}</strong>`
   - Linha 2 contextual baseada na aba:
     - Dashboard → "System Overview · {stats.agents} agents active"
     - Task Manager → "{openTasks} tasks open · {completedTasks} delivered"  
     - Agent Library → "{agentList.length} specialists registered"
     - Quality Inspector → "Avg accuracy: {qaReport?.summary?.avg_accuracy || '...'}%"
     - Outros → "Module loaded"
   Usar `useMemo` para calcular o subtítulo.

3. HEALTH INDICATOR:
   Criar endpoint `GET /api/health-score` no `entrypoint.py`
   que calcula score 0-100:
   - +25 se `agents.length > 0`
   - +25 se `tasks` com `status Concluído > 0`
   - +25 se custo hoje < $5
   - +25 se Knowledge Graph tem > 10 nós
   
   No header, mostrar:
   - Se score >= 80: `● HEALTHY` em verde
   - Se score >= 50: `● DEGRADED` em amarelo  
   - Se score < 50: `● CRITICAL` em vermelho pulsante
   
   Buscar o score a cada 60s separadamente do fetchData.

4. LOADING INDICATOR:
   Estado `isFetching` (boolean). Setar `true` antes de 
   qualquer `fetch`, `false` após `Promise.allSettled`.
   
   No header: spinner CSS de 16px visível quando `isFetching`:
   `<div className={`spinner ${isFetching ? 'visible' : ''}`} />`
   `animation: rotate 0.8s linear infinite`
   Transição de opacity para aparecer/desaparecer suavemente.

5. VERSION TAG:
   Pequeno badge no canto: `v2.1.0` em texto muted 0.6rem.
   Clicar abre modal com changelog (conteúdo estático do CHANGELOG.md).
```

## Arquivos Envolvidos
- `frontend/src/App.jsx`
- `entrypoint.py` (endpoint GET /api/health-score)
- `frontend/src/index.css`

## Critério de Conclusão
- Clock atualiza a cada segundo sem causar re-render pesado
- Breadcrumb muda ao trocar de aba
- Health score busca e atualiza a cada 60s
- Spinner visível durante fetches
- Version badge clicável mostra changelog

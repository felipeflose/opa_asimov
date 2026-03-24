# TASK-47 | Skeleton Loading States em Todas as Abas

## Metadata
| Campo | Valor |
|---|---|
| ID | TASK-47 |
| Grupo | UX / Performance Percebida |
| Prioridade | Média |
| Responsável | FrontendAgent |
| Status | Aberto |

## Problema Identificado
Quando o usuário troca de aba ou a página carrega pela primeira vez, todo o conteúdo aparece de uma vez (após o fetch completar) ou não aparece nada enquanto carrega. Isso cria uma experiência de tela em branco → conteúdo abrupto.

O estado atual de carregamento do Quality Inspector (`qaLoading`) mostra apenas um texto simples "⏳". Não há skeletons em nenhuma outra aba.

## Objetivo
Implementar skeleton screens em todas as abas principais do dashboard, criando a percepção de que o sistema está carregando progressivamente e de forma organizada.

## Cenário Real
Usuário abre "Agent Library" → aparece imediatamente o layout dos cards com blocos cinza animados (shimmer) no lugar do conteúdo → em 500ms os dados chegam e os cards se preenchem com fade-in suave.

## Prompt para Antigravity

```
No `frontend/src/App.jsx` e `index.css`:

1. Criar componente base `<Skeleton width height borderRadius />`:
   - Background: `linear-gradient(90deg, rgba(255,255,255,0.03) 25%, rgba(255,255,255,0.08) 50%, rgba(255,255,255,0.03) 75%)`
   - `background-size: 400% 100%`
   - `animation: shimmer 1.5s ease-in-out infinite`
   - keyframe shimmer: `background-position: 100% 0 → -100% 0`
   - border-radius prop, default 8px

2. Criar componente `<SkeletonAgentCard />`:
   - Imitar o layout do AgentCard: círculo 60px + 3 linhas de texto
   - Grid 1x3 de SkeletonAgentCards no lugar da lista vazia

3. Criar componente `<SkeletonTaskCard />`:
   - Imitar card do Kanban: linhas de texto + badges

4. Criar componente `<SkeletonKpiGrid />`:
   - 4 retângulos de 200x100px lado a lado

5. Lógica de exibição:
   - Adicionar estado `loadingStates: { agents, tasks, activity, stats }` 
     com `true` inicial, `false` após fetch de cada endpoint completar
   - No Dashboard: mostrar `<SkeletonKpiGrid />` enquanto 
     `loadingStates.stats === true`
   - No Agent Library: mostrar 3 `<SkeletonAgentCard />` enquanto 
     `loadingStates.agents === true`
   - No Task Manager: mostrar `<SkeletonTaskCard />` em cada coluna 
     enquanto `loadingStates.tasks === true`
   - Transição: quando dados chegam, aplicar `animation: fadeIn 0.4s ease`

6. Garantir que o `fetchData()` atual sete cada `loadingState` 
   individualmente à medida que cada Promise resolve 
   (usar `Promise.allSettled` ao invés de `Promise.all`).
```

## Arquivos Envolvidos
- `frontend/src/App.jsx`
- `frontend/src/index.css`

## Critério de Conclusão
- Shimmer animation visível em todas as abas no carregamento inicial
- Transição suave de skeleton → conteúdo real
- Sem flash de tela em branco em nenhuma aba
- Skeletons têm proporções similares ao conteúdo real

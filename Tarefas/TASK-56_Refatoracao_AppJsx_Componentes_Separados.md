# TASK-56 | Refatoração: Quebrar App.jsx em Componentes Separados

## Metadata
| Campo | Valor |
|---|---|
| ID | TASK-56 |
| Grupo | Arquitetura / Frontend |
| Prioridade | Alta |
| Responsável | FrontendAgent |
| Status | Aberto |

## Problema Identificado
O `App.jsx` atual tem **mais de 1.500 linhas** em um único arquivo. Isso cria problemas sérios:

1. **Performance**: React re-renderiza componentes desnecessários porque tudo está no mesmo scope de estado.
2. **Manutenção**: Encontrar e editar um componente específico requer scroll extenso.
3. **Colaboração**: Impossível trabalhar em múltiplas features ao mesmo tempo sem conflitos de merge.
4. **Code splitting**: Vite não consegue fazer code splitting eficiente de um arquivo monolítico.
5. **Testing**: Impossível testar componentes individualmente.

O `renderContent()` com 15+ blocos `if (activeTab === ...)` é um anti-pattern grave em React.

## Objetivo
Refatorar o `App.jsx` em uma estrutura de componentes organizada por feature, mantendo 100% das funcionalidades existentes mas em arquivos separados e coesos.

## Estrutura Proposta

```
frontend/src/
├── App.jsx                    (raiz: estado global + layout)
├── hooks/
│   ├── useAppData.js          (fetchData, polling, todos os estados de dados)
│   ├── useForce.js            (hook de física do CognitiveMap — já existe inline)
│   └── useKeyboard.js         (atalhos de teclado globais: CMD+K, Alt+F)
├── components/
│   ├── layout/
│   │   ├── Sidebar.jsx        (nav, badges, user profile)
│   │   ├── Header.jsx         (breadcrumb, clock, health, spinner)
│   │   └── BottomNav.jsx      (mobile navigation)
│   ├── ui/
│   │   ├── ToastContainer.jsx (sistema de toasts - TASK-36)
│   │   ├── Skeleton.jsx       (skeleton loaders - TASK-47)
│   │   ├── KpiCard.jsx        (cards do dashboard - TASK-37)
│   │   └── SlantButton.jsx    (já existe inline)
│   ├── modals/
│   │   ├── AgentModal.jsx     (viewingAgent modal)
│   │   ├── DeliveryModal.jsx  (viewingDelivery modal)
│   │   └── ExecutionModal.jsx (executionPreview modal)
│   └── views/
│       ├── DashboardView.jsx  (aba Dashboard)
│       ├── CognitiveMap.jsx   (já existe inline, extrair)
│       ├── TaskManagerView.jsx
│       ├── AgentLibraryView.jsx
│       ├── PipelineView.jsx
│       ├── MarketplaceView.jsx
│       ├── QualityView.jsx
│       ├── FinOpsView.jsx
│       ├── DoraView.jsx
│       ├── SettingsView.jsx
│       ├── TerminalView.jsx   (TASK-43)
│       ├── ChatView.jsx       (TASK-45)
│       └── ReportsView.jsx    (TASK-55)
```

## Prompt para Antigravity

```
Refatorar `frontend/src/App.jsx` seguindo a estrutura acima:

1. Criar pasta `frontend/src/hooks/` e `frontend/src/components/`.

2. Extrair `useForce` para `hooks/useForce.js` (já existe inline).

3. Criar `hooks/useAppData.js` que exporta:
   - Todos os estados de dados: `stats, graphData, tasks, 
     activity, agentList, marketTemplates, qaReport, doraData`
   - Função `fetchData()` e `fetchQAReport()` e `fetchDoraData()`
   - Estados de loading: `loadingStates`
   Usar `useState`, `useEffect` internamente.
   App.jsx importa: `const { stats, tasks, ... } = useAppData(token)`

4. Criar `hooks/useKeyboard.js` que registra atalhos globais:
   - `CMD+K` → abre command palette
   - `Alt+F` → toggle sidebar
   - `Escape` → fecha qualquer modal aberto
   Recebe callbacks como parâmetros.

5. Cada View em `components/views/` recebe via props:
   - Dados relevantes (ex: DashboardView recebe stats, graphData, activity)
   - Callbacks de ação (ex: TaskManagerView recebe handleApprove, handleExecute)
   - Token (para chamadas internas se necessário)

6. App.jsx fica responsável apenas por:
   - Estado de autenticação
   - Estado de navegação (activeTab)
   - Estado de modais globais
   - Layout geral (sidebar + main)
   - Router simples: `{activeTab === 'Dashboard' && <DashboardView ... />}`

7. Cada arquivo deve ter no máximo 200 linhas.

8. Manter todos os imports existentes e não quebrar 
   nenhuma funcionalidade durante a refatoração.
   Fazer uma feature por arquivo, testar, depois o próximo.
```

## Arquivos Envolvidos
- `frontend/src/App.jsx` (drasticamente reduzido)
- Todos os arquivos novos da estrutura acima

## Critério de Conclusão
- App.jsx com menos de 200 linhas
- Cada componente com menos de 200 linhas
- Zero funcionalidades perdidas
- Build Vite sem erros ou warnings
- Hot reload funcional no dev

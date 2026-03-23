# TASK-35 | Global Command Palette (CMD+K)

## Metadata
| Campo | Valor |
|---|---|
| ID | TASK-35 |
| Grupo | UX / Power User |
| Prioridade | Alta |
| Responsável | FrontendAgent |
| Status | Aberto |

## Problema Identificado
Navegar entre 10 abas clicando na sidebar é lento. Para um power user que gerencia agentes e tarefas frequentemente, não existe atalho de teclado nenhum no sistema. O dashboard parece uma ferramenta passiva ao invés de um cockpit ativo.

## Objetivo
Criar uma Command Palette estilo VS Code / Linear que abre com `CMD+K` (ou `CTRL+K`), permitindo navegar para qualquer aba, executar ações rápidas e buscar tarefas/agentes pelo nome — tudo sem tirar as mãos do teclado.

## Cenário Real
Usuário pressiona `CTRL+K` → modal aparece com input focado → digita "fin" → sugestão "FinOps Guardian" aparece → pressiona Enter → vai para a aba.

Ou digita "aprovar" → lista as tarefas com `budget_approved: false` → clica em uma → abre o task manager naquela tarefa.

## Prompt para Antigravity

```
No `frontend/src/App.jsx`, criar componente `<CommandPalette />` 
com as seguintes características:

1. ATIVAÇÃO: `useEffect` com `keydown` listener para 
   `(e.metaKey || e.ctrlKey) && e.key === 'k'`. 
   Estado booleano `paletteOpen`.

2. VISUAL: Modal centralizado, largura 600px, fundo 
   `rgba(5,8,18,0.97)` com `backdrop-filter: blur(20px)`, 
   borda `1px solid var(--primary)`, `box-shadow` glow cyan.

3. INPUT: Campo focado automaticamente via `useRef` + 
   `ref.current.focus()` no `useEffect([paletteOpen])`.
   Placeholder: "Type a command or search..."

4. RESULTADOS: Lista de comandos filtrados em tempo real:
   - Seção "NAVIGATION": todas as abas com ícone
   - Seção "TASKS": primeiras 5 tarefas abertas matching o query
   - Seção "AGENTS": primeiros 5 agentes matching o query
   - Seção "ACTIONS": "Create New Task", "QA Auto-Fix", "Refresh Data"

5. NAVEGAÇÃO: setas ↑↓ para mover entre itens, Enter para executar, 
   Escape para fechar.

6. EXECUÇÃO: clicar ou pressionar Enter chama:
   - Para abas: `setActiveTab(item.id)`
   - Para tasks: `setActiveTab('Task Manager'); setSelectedTask(task)`
   - Para actions: chamar a função correspondente

Fechar ao clicar fora do modal (overlay click).
```

## Arquivos Envolvidos
- `frontend/src/App.jsx`
- `frontend/src/index.css` (estilos do palette e highlight de item ativo)

## Critério de Conclusão
- `CTRL+K` / `CMD+K` abre e fecha o palette
- Filtro funciona em tempo real (< 16ms)
- Navegação por teclado completa (↑↓ Enter Escape)
- Fecha ao clicar fora
- Não interfere com outros inputs da página

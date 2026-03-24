# TASK-44 | Modo Foco: Sidebar Recolhível + Fullscreen por Aba

## Metadata
| Campo | Valor |
|---|---|
| ID | TASK-44 |
| Grupo | UX / Produtividade |
| Prioridade | Baixa |
| Responsável | FrontendAgent |
| Status | Aberto |

## Problema Identificado
A sidebar ocupa 280px fixos da tela. Em abas como o Cognitive Map ou o Terminal de Logs, o usuário quer ver o máximo possível do conteúdo principal. Não existe forma de esconder a sidebar temporariamente sem sair do sistema.

## Objetivo
Adicionar um botão de "Focus Mode" que recolhe a sidebar para 60px (só ícones, sem labels) e expande o conteúdo principal. Double-click ou atalho `ALT+F` ativa/desativa.

## Cenário Real
Usuário está no Cognitive Map explorando os nós → clica no botão `⇥` no topo da sidebar → sidebar colapsa para 60px de ícones → mapa ocupa quase a tela toda. Clica novamente → sidebar volta ao normal.

## Prompt para Antigravity

```
No `frontend/src/App.jsx`:

1. Adicionar estado `sidebarCollapsed` (boolean, default false).

2. Botão toggle no topo da sidebar:
   `<button onClick={() => setSidebarCollapsed(v => !v)}>
     {sidebarCollapsed ? '»' : '«'}
   </button>`
   Posicionado no canto superior direito da sidebar.

3. CSS dinâmico na sidebar:
   - Quando `!sidebarCollapsed`: `width: 280px`
   - Quando `sidebarCollapsed`: `width: 60px; overflow: hidden`
   - `transition: width 0.3s cubic-bezier(0.4, 0, 0.2, 1)`

4. Quando colapsada, cada nav-item:
   - Esconder o label (text) com `opacity: 0; width: 0; overflow: hidden`
   - Mostrar apenas o ícone centralizado
   - Tooltip ao hover com o nome da aba (CSS `title` attribute)
   - `transition: opacity 0.2s 0.1s` (delay para aguardar o resize)

5. Logo e user-profile:
   - Quando colapsada: mostrar apenas o avatar (círculo FF) 
     no lugar do user-profile completo
   - Esconder título "Flose IA" e subtítulo

6. Atalho de teclado: `Alt+F` toggles sidebar.
   `useEffect` com keydown listener.

7. Persistir preferência em `localStorage` para manter 
   o estado após refresh.

8. No Cognitive Map especificamente, adicionar botão 
   fullscreen nativo `document.documentElement.requestFullscreen()`
   no header do mapa com ícone `⛶`.
```

## Arquivos Envolvidos
- `frontend/src/App.jsx`
- `frontend/src/index.css`

## Critério de Conclusão
- Sidebar colapsa e expande suavemente
- Ícones visíveis e com tooltip no estado colapsado
- Atalho Alt+F funcional
- Estado persiste após refresh
- Conteúdo principal preenche o espaço liberado

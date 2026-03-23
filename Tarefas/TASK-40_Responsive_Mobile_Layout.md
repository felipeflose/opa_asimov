# TASK-40 | Responsive Mobile Layout

## Metadata
| Campo | Valor |
|---|---|
| ID | TASK-40 |
| Grupo | UX / Mobile |
| Prioridade | Média |
| Responsável | FrontendAgent |
| Status | Aberto |

## Problema Identificado
O CSS atual tem `overflow: hidden` no `body` e `height: 100vh` fixo. A sidebar tem `width: 280px` hardcoded. O layout usa `display: flex` sem nenhuma media query.

Em mobile (< 768px), a interface é completamente inutilizável:
- Sidebar ocupa metade da tela
- Conteúdo fica espremido
- Textos cortados
- Nenhum gesto de swipe funciona

O Flose AI é acessado do Telegram, e usuários naturalmente vão querer verificar o dashboard pelo celular após receber uma notificação.

## Objetivo
Criar um layout responsivo que colapsa a sidebar em um bottom navigation bar no mobile, mantendo todas as funcionalidades acessíveis.

## Cenário Real
No desktop: layout atual com sidebar à esquerda.
No mobile: sidebar some, bottom nav aparece com ícones das abas principais (Dashboard, Tasks, Agents, FinOps, Settings). Conteúdo ocupa 100% da largura com padding ajustado.

## Prompt para Antigravity

```
No `frontend/src/index.css` e `App.css`:

1. Criar breakpoint principal em 768px:

@media (max-width: 768px) {
  body { overflow-y: auto; overflow-x: hidden; }
  
  .app-container { flex-direction: column; }
  
  .sidebar { 
    display: none; /* Esconder sidebar desktop */
  }
  
  .main-content { 
    padding: 15px; 
    padding-bottom: 80px; /* Espaço para bottom nav */
  }
  
  .kpi-grid { 
    grid-template-columns: repeat(2, 1fr); 
    gap: 12px;
  }
}

2. No `App.jsx`, criar componente `<BottomNav />` visível 
   apenas em mobile via CSS class `mobile-only`:

const MOBILE_TABS = [
  { id: 'Dashboard', icon: '⚡' },
  { id: 'Task Manager', icon: '📋' },
  { id: 'Agent Library', icon: '🤖' },
  { id: 'FinOps Guardian', icon: '💎' },
  { id: 'Settings', icon: '⚙️' },
];

Estilo do BottomNav:
- `position: fixed; bottom: 0; left: 0; right: 0`
- `background: rgba(5,8,18,0.97); backdrop-filter: blur(20px)`
- `border-top: 1px solid var(--border)`
- `display: none` no desktop, `display: flex` no mobile
- Cada item: ícone + label pequena + badge se aplicável

3. Adicionar botão hamburguer no header mobile que abre 
   a sidebar completa como drawer (overlay lateral) com 
   `transform: translateX(-100%) → translateX(0)` animado.

4. Ajustar os modais (viewingDelivery, viewingAgent, 
   executionPreview) para `width: 95vw` e `max-height: 90vh` 
   no mobile para não cortarem.
```

## Arquivos Envolvidos
- `frontend/src/index.css`
- `frontend/src/App.css`
- `frontend/src/App.jsx`

## Critério de Conclusão
- Layout usável em iPhone 12 (390px largura)
- Bottom nav funcional com navegação entre abas principais
- Modais não cortam conteúdo no mobile
- Drawer lateral abre/fecha suavemente
- Sem scroll horizontal em nenhuma tela

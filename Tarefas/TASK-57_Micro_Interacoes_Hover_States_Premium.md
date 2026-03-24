# TASK-57 | Micro-interações e Hover States Premium em Todo o Sistema

## Metadata
| Campo | Valor |
|---|---|
| ID | TASK-57 |
| Grupo | Design / Polimento |
| Prioridade | Baixa |
| Responsável | FrontendAgent |
| Status | Aberto |

## Problema Identificado
O sistema tem animações no Cognitive Map (força física) e no login, mas o restante do dashboard carece de micro-interações. Elementos interativos como botões, cards e inputs respondem de forma genérica ao hover, sem a sensação premium que o produto merece.

Exemplos de deficiências:
- Botões da sidebar: só mudam de cor, sem nenhuma animação de entrada
- Cards do Kanban: hover com `translateY(-5px)` mas sem shadow ou glow
- Botões de ação: sem ripple effect ou press state
- Inputs: sem animação de focus além da borda
- Métricas do QA: accuracy bar não anima na entrada

## Objetivo
Adicionar uma camada de micro-interações consistente em todo o sistema usando apenas CSS (sem libs externas), que torne a interface mais responsiva e viva.

## Prompt para Antigravity

```
No `frontend/src/index.css` e `App.css`:

1. BOTÕES — Press State (efeito de "apertar"):
   Todos os `.login-button`, `.refresh-btn`, `.nav-item`:
   ```css
   &:active {
     transform: scale(0.97);
     transition: transform 0.1s ease;
   }
   ```

2. RIPPLE EFFECT nos botões primários:
   No JSX, adicionar handler `onClick` que cria dinamicamente 
   um `<span class="ripple">` com posição do click calculada,
   animação `rippleExpand 0.6s ease-out forwards` e remove 
   após 600ms. CSS:
   ```css
   .ripple {
     position: absolute; border-radius: 50%;
     background: rgba(255,255,255,0.3);
     animation: rippleExpand 0.6s ease-out forwards;
     pointer-events: none;
   }
   @keyframes rippleExpand {
     from { width: 0; height: 0; opacity: 1; }
     to { width: 200px; height: 200px; opacity: 0; margin: -100px; }
   }
   ```

3. INPUTS — Focus Glow animado:
   ```css
   input:focus, textarea:focus {
     border-color: var(--primary);
     box-shadow: 0 0 0 0px rgba(0,242,255,0.3);
     animation: focusGlow 0.3s ease forwards;
   }
   @keyframes focusGlow {
     to { box-shadow: 0 0 0 3px rgba(0,242,255,0.15); }
   }
   ```

4. CARDS — Hover com glow direcional:
   `.glass-card:hover`:
   ```css
   transform: translateY(-3px);
   box-shadow: 0 8px 32px rgba(0,242,255,0.08), 
               0 0 0 1px rgba(0,242,255,0.1);
   transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
   ```

5. SIDEBAR NAV ITEMS — Slide indicator:
   Adicionar `::before` pseudo-element nos nav-items:
   ```css
   .nav-item::before {
     content: '';
     position: absolute; left: 0; top: 50%; 
     transform: translateY(-50%);
     width: 3px; height: 0; border-radius: 2px;
     background: var(--primary);
     transition: height 0.3s ease;
   }
   .nav-item.active::before { height: 70%; }
   .nav-item:hover::before { height: 40%; }
   ```

6. ACCURACY BARS (Quality Inspector) — Entrada animada:
   Ao montar o componente, iniciar width em 0 e animar até 
   o valor real via CSS `animation: barGrow 0.8s ease forwards`:
   Usar `style={{ animationDelay: `${index * 0.1}s` }}` 
   para efeito cascata.

7. NÚMEROS/MÉTRICAS — Countup ao entrar na viewport:
   Usar `IntersectionObserver` para detectar quando um 
   elemento com `data-countup` entra na viewport e só 
   então iniciar a animação de counter (ver TASK-37).

8. AVATAR DO USUÁRIO — Hover state:
   Ao hover no `.avatar` do user profile na sidebar:
   `transform: scale(1.1); box-shadow: 0 0 15px var(--primary)33`
```

## Arquivos Envolvidos
- `frontend/src/index.css`
- `frontend/src/App.css`
- `frontend/src/App.jsx` (ripple handlers)

## Critério de Conclusão
- Press state em todos os botões interativos
- Focus glow em todos os inputs
- Card hover com glow direcional
- Sidebar indicator line animado
- Accuracy bars com animação de entrada cascata
- Sem impacto perceptível no desempenho (apenas CSS)

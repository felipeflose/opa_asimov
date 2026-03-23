# TASK-49 | Temas: Dark Neon (atual) + Dark Minimal + Light Mode

## Metadata
| Campo | Valor |
|---|---|
| ID | TASK-49 |
| Grupo | Design / Personalização |
| Prioridade | Baixa |
| Responsável | FrontendAgent |
| Status | Aberto |

## Problema Identificado
O sistema tem apenas um tema: Dark Neon com cyan/purple/pink. Embora seja visualmente impactante, pode ser cansativo para sessões longas de trabalho. Além disso, não existe opção de tema mais sóbrio para apresentações ou contextos mais formais.

O CSS já usa variáveis CSS (`--primary`, `--secondary`, `--bg`, etc.) no `:root`, o que facilita muito a implementação de temas.

## Objetivo
Implementar um seletor de 3 temas na aba Settings, persistindo a escolha em localStorage, com troca instantânea sem reload.

## Temas:
1. **NEON** (atual): cyan/purple/pink, fundo #050505
2. **MIDNIGHT**: azul/índigo/slate, fundo #0a0f1e — mais sóbrio e profissional
3. **AURORA**: verde/teal/emerald, fundo #030d0a — temática "matrix"

## Prompt para Antigravity

```
No `frontend/src/index.css` e `App.jsx`:

1. Manter o `:root` atual como tema NEON.

2. Adicionar dois blocos de tema via data-attribute:

[data-theme="midnight"] {
  --primary: #6366f1;      /* indigo */
  --secondary: #818cf8;    /* slate blue */
  --accent: #a78bfa;       /* violet */
  --bg: #0a0f1e;
  --card-bg: rgba(99,102,241,0.05);
  --border: rgba(99,102,241,0.15);
  --grad: linear-gradient(135deg, #6366f1, #818cf8);
}

[data-theme="aurora"] {
  --primary: #10b981;      /* emerald */
  --secondary: #059669;    /* green */
  --accent: #34d399;       /* light emerald */
  --bg: #030d0a;
  --card-bg: rgba(16,185,129,0.04);
  --border: rgba(16,185,129,0.12);
  --grad: linear-gradient(135deg, #10b981, #059669);
}

3. No `App.jsx`:
   a. Estado: `const [theme, setTheme] = useState(localStorage.getItem('flose_theme') || 'neon')`
   
   b. useEffect: 
      `document.documentElement.setAttribute('data-theme', theme)`
      (para neon: `removeAttribute('data-theme')`)
      `localStorage.setItem('flose_theme', theme)`

4. Na aba Settings, seção "Dashboard Preferences",
   adicionar "Color Theme" com 3 botões de preview:
   
   Cada botão: mini card 80x50px mostrando uma miniatura 
   do gradiente do tema, com borda destacada se ativo e 
   label abaixo. Click → `setTheme('midnight')` etc.

5. Transição suave na troca:
   No `html { transition: background-color 0.3s ease; }`
   E no `body`, `.glass-card`, `.sidebar` adicionar 
   `transition: background-color 0.3s ease, border-color 0.3s ease`.

6. O tema NEON deve ser o padrão e não requerer data-attribute.
```

## Arquivos Envolvidos
- `frontend/src/index.css`
- `frontend/src/App.jsx`

## Critério de Conclusão
- 3 temas aplicados corretamente em todos os componentes
- Troca instantânea sem reload
- Preferência persistida em localStorage
- Preview dos temas visível na seleção
- Sem conflito de especificidade CSS

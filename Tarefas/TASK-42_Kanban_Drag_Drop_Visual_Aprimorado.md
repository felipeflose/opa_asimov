# TASK-42 | Kanban com Drag and Drop Visual Aprimorado

## Metadata
| Campo | Valor |
|---|---|
| ID | TASK-42 |
| Grupo | Task Manager / UX |
| Prioridade | Alta |
| Responsável | FrontendAgent |
| Status | Aberto |

## Problema Identificado
O Kanban atual usa o HTML5 Drag and Drop nativo (`draggable` + `onDragStart/onDrop`) que é funcional mas tem UX ruim:
- Nenhum feedback visual da coluna sendo "alvo" durante o drag
- O card sendo arrastado fica com aparência fantasma padrão do browser
- Não há animação de "reorder" nas colunas
- Cards não têm altura consistente — variam muito dependendo do conteúdo
- A área de drop não dá feedback visual (highlight da coluna)

## Objetivo
Melhorar significativamente a experiência de drag and drop do Kanban com feedback visual claro, animações suaves e estado consistente.

## Cenário Real
Usuário arrasta um card de "BACKLOG" para "EM EXECUÇÃO": a coluna destino fica com borda cyan destacada e fundo levemente iluminado durante o hover. O card arrastado fica com `opacity: 0.5` na posição original. Ao soltar, animação de `scale(1.02) → scale(1)` confirma o drop.

## Prompt para Antigravity

```
No `frontend/src/App.jsx`, na aba 'Task Manager':

1. ESTADO DE DRAG:
   Adicionar estados: `draggedTaskId`, `dragOverColumn`
   
   - `onDragStart`: setar `draggedTaskId` + criar custom drag 
     image via `e.dataTransfer.setDragImage()`
   - `onDragOver`: setar `dragOverColumn` (id da coluna)
   - `onDragLeave`: limpar `dragOverColumn`
   - `onDrop`: executar a troca + limpar ambos os estados

2. VISUAL DA COLUNA ALVO:
   Quando `dragOverColumn === col.id`:
   - `border: 2px solid var(--primary)`
   - `background: rgba(0,242,255,0.04)`
   - `box-shadow: inset 0 0 30px rgba(0,242,255,0.05)`
   - Transição `all 0.2s ease`

3. VISUAL DO CARD ARRASTADO:
   Quando `draggedTaskId === task.id`:
   - `opacity: 0.4`
   - `transform: scale(0.98)`
   - `border: 1px dashed var(--primary)`

4. ANIMAÇÃO DE DROP:
   Ao receber um card novo, a coluna aplica por 400ms 
   a classe `drop-received` que faz:
   - `animation: dropFlash 0.4s ease` 
   - keyframe: `background-color` flash de `rgba(0,242,255,0.08)` → transparent

5. DROP ZONE VAZIA:
   Quando a coluna está vazia e é o alvo do drag, 
   mostrar placeholder:
   `<div class="drop-placeholder">⬇ Solte aqui</div>`
   com borda dashed animada.

6. CONTADOR DE CARDS por coluna com animação quando muda:
   O número no header da coluna usa `key={count}` para 
   triggering do React re-render animation.
```

## Arquivos Envolvidos
- `frontend/src/App.jsx`
- `frontend/src/index.css` (keyframes dropFlash, drop-placeholder)

## Critério de Conclusão
- Feedback visual claro ao arrastar sobre qualquer coluna
- Card arrastado fica visualmente "fantasma" na origem
- Drop zone vazia mostra placeholder
- Animação de confirmação ao soltar
- Estado limpo corretamente após drop ou cancel

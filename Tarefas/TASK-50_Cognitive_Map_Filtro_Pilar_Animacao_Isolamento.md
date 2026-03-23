# TASK-50 | Cognitive Map: Filtro por Pilar com Animação de Isolamento

## Metadata
| Campo | Valor |
|---|---|
| ID | TASK-50 |
| Grupo | Cognitive Map / UX |
| Prioridade | Média |
| Responsável | FrontendAgent |
| Status | Aberto |

## Problema Identificado
O Cognitive Map atual tem filtros de tipo (ALL/CORE/PILLARS/CONCEPTS) mas não permite filtrar por **pilar específico**. Com 12+ pilares e dezenas de conceitos, o mapa fica denso e difícil de explorar.

Além disso:
- A busca atual filtra os nós mas simplesmente remove os não-matching do grafo — ao invés de isolá-los com opacity dim
- Não há como ver "todos os conceitos do pilar FinOps" especificamente
- Não existe contagem de conceitos por pilar

## Objetivo
Adicionar um painel de filtro por pilar que isola visualmente o cluster selecionado — os demais ficam com opacity reduzida mas não desaparecem — com animação de transição suave.

## Cenário Real
Usuário clica no pilar "GCP Infrastructure" no painel lateral → todos os conceitos ligados a esse pilar ficam em destaque (opacity 1, cores vivas) → os demais ficam dimmed (opacity 0.1) → contagem: "7 conceitos neste pilar".

## Prompt para Antigravity

```
No `frontend/src/App.jsx`, no componente `<CognitiveMap />`:

1. PAINEL DE PILARES (novo painel lateral dentro do mapa):
   Posição: `position: absolute; left: 20px; top: 80px`
   Fundo glassmorphism, `max-height: 400px`, `overflow-y: auto`
   
   Listar todos os nós com `type === 'pilar'`:
   - Nome do pilar como botão
   - Contagem de nós filhos: `(links.filter(l => l.source === pilar.id)).length`
   - Cor de background baseada na cor do nó (`node.color`)
   - Borda highlight se este pilar está selecionado
   
   Estado: `selectedPilar` (string | null)
   Clicar no mesmo pilar já selecionado: deselect (null)

2. LÓGICA DE ISOLAMENTO:
   Quando `selectedPilar` não é null:
   
   a. `highlightedIds` = Set com o pilar + todos os nós 
      que têm link com ele (diretos)
   
   b. Cada nó no render:
      - Se está em `highlightedIds`: `opacity 1`, cores normais
      - Se não está: `opacity 0.08`, `fill: rgba(255,255,255,0.1)` 
        no circle, texto invisível (`opacity 0`)
   
   c. Cada link:
      - Se conecta dois nós em `highlightedIds`: `stroke-opacity 0.6`, cyan
      - Caso contrário: `stroke-opacity 0.02`
   
   d. Transição suave: todos os elementos SVG com 
      `style={{ transition: 'opacity 0.4s ease' }}`

3. CONTAGEM NO HEADER:
   Quando pilar selecionado: mostrar badge no header do mapa:
   `"FinOps: 7 conceitos"` com botão `[✕ Limpar Filtro]`

4. HIGHLIGHT DE BUSCA APRIMORADO:
   Quando `searchTerm` está ativo, ao invés de filtrar os nós 
   (remover do array), manter todos mas:
   - Matching nodes: `opacity 1`, escala aumentada `r * 1.4`
   - Non-matching nodes: `opacity 0.05`
   Isso preserva o contexto espacial do grafo.

5. ANIMAÇÃO DE ENTRADA DO PAINEL DE PILARES:
   `animation: slideInLeft 0.3s ease` ao aparecer.
```

## Arquivos Envolvidos
- `frontend/src/App.jsx`
- `frontend/src/index.css`

## Critério de Conclusão
- Filtro por pilar isola visualmente o cluster correto
- Opacity dim nos nós não-relacionados (não remove do DOM)
- Contagem de conceitos por pilar correta
- Deselect ao clicar novamente no pilar
- Busca usa dimming ao invés de remoção

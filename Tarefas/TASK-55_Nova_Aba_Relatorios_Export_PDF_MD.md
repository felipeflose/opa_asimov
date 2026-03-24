# TASK-55 | Nova Aba: Relatórios com Export PDF e Markdown

## Metadata
| Campo | Valor |
|---|---|
| ID | TASK-55 |
| Grupo | Nova Funcionalidade / Produto |
| Prioridade | Média |
| Responsável | FrontendAgent |
| Status | Aberto |

## Problema Identificado
O `ReportAgent` no backend já gera relatórios semanais de performance e os salva no GCS (`reports/{REPORT_ID}.json`). Porém, não existe nenhuma tela no dashboard para visualizar esses relatórios.

O único jeito de ver um relatório é via Telegram (recebe a mensagem truncada) ou acessando o GCS diretamente. O export individual de tasks via `GET /api/tasks/{id}/export` existe mas é escondido e sem UX.

## Objetivo
Criar uma aba "Relatórios" que lista todos os relatórios salvos no GCS, permite visualizá-los inline com formatação Markdown renderizada, e exportá-los como PDF ou `.md`.

## Cenário Real
Usuário abre "Relatórios" → vê lista: "Relatório Semanal #12 · 14 Mar 2026", "Relatório Semanal #11 · 7 Mar 2026" → clica → conteúdo abre à direita com markdown renderizado, estilizado → botão "Exportar PDF" → browser faz download.

## Prompt para Antigravity

```
No `frontend/src/App.jsx`:

1. Adicionar "📄 Relatórios" na sidebar (após DORA Metrics).

2. No `entrypoint.py`, criar:
   `GET /api/reports` → lista arquivos em `reports/` no GCS,
   retorna array de `{ id, timestamp, preview }` onde preview 
   são os primeiros 200 chars do campo `content`.
   
   `GET /api/reports/{report_id}` → retorna o report completo.

3. COMPONENTE `<ReportsView />`:

   a. LISTA DE RELATÓRIOS (coluna esquerda, 300px):
      Cada item: card com data formatada ("14 Mar 2026"), 
      badge do tipo ("SEMANAL"), preview truncado.
      Click → `setSelectedReport(report)`
      Destaque no item ativo.

   b. VIEWER DO RELATÓRIO (coluna direita, flex: 1):
      Renderizar Markdown usando um parser simples:
      - `**bold**` → `<strong>`
      - `# Heading` → `<h2>` com estilo
      - `- item` → `<li>` com bullet custom
      - Sem lib externa — implementar mini parser com regex
      
      Estilo: fundo `rgba(0,0,0,0.2)`, padding 30px, 
      font-size 0.95rem, line-height 1.8, cor `#e2e8f0`.
      Headings em `var(--primary)`.

   c. AÇÕES NO VIEWER:
      - `[📋 Copiar]` → copia o conteúdo raw para clipboard
      - `[💾 .MD]` → download do arquivo .md via Blob URL:
        ```js
        const blob = new Blob([content], { type: 'text/markdown' });
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url; a.download = `${report.id}.md`; a.click();
        ```
      - `[🖨️ PDF]` → usar `window.print()` com CSS 
        `@media print` que esconde sidebar, header e botões,
        mostrando apenas o conteúdo do viewer em preto no branco.

   d. ESTADO VAZIO: quando não há relatórios, mostrar:
      "Nenhum relatório gerado ainda. O ReportAgent gera 
      relatórios semanais automaticamente toda sexta."
      Com botão `[Gerar Agora]` que chama `POST /weekly_report`.

4. BUSCA NA LISTA: input de busca simples por keyword 
   dentro dos previews dos relatórios.
```

## Arquivos Envolvidos
- `frontend/src/App.jsx`
- `entrypoint.py` (endpoints GET /api/reports e GET /api/reports/{id})
- `frontend/src/index.css` (`@media print` styles)

## Critério de Conclusão
- Lista de relatórios carrega do GCS real
- Markdown renderizado sem biblioteca externa
- Download .md funcional via Blob
- Print/PDF usando `window.print()` com estilos corretos
- Estado vazio com botão de geração

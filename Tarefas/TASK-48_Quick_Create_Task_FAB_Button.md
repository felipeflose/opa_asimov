# TASK-48 | Quick Create Task via Modal Flutuante (FAB Button)

## Metadata
| Campo | Valor |
|---|---|
| ID | TASK-48 |
| Grupo | Task Manager / UX |
| Prioridade | Média |
| Responsável | FrontendAgent |
| Status | Aberto |

## Problema Identificado
Para criar uma nova tarefa, o usuário precisa:
1. Ir para a aba Chat
2. Digitar um comando para o Orchestrator
3. Esperar o processamento
4. Verificar se a tarefa foi criada no Kanban

Não existe um botão "+" direto no Task Manager para criação rápida. O fluxo de criação de tarefas passa obrigatoriamente pelo LLM, o que é lento para tarefas simples que o usuário já sabe o que são.

## Objetivo
Criar um botão FAB (Floating Action Button) no Task Manager com `+` que abre um modal rápido para criar uma task diretamente, com formulário estruturado simples.

## Cenário Real
Usuário está no Task Manager → clica no `+` no canto inferior direito → modal abre com campos: Título, Prioridade, Responsável, Descrição → clica "Criar" → tarefa aparece no Kanban com animação → modal fecha.

## Prompt para Antigravity

```
No `frontend/src/App.jsx`, na aba 'Task Manager':

1. FAB BUTTON:
   Posição: `position: fixed; bottom: 30px; right: 30px; z-index: 500`
   Visual: círculo 56px, background `var(--grad)`, sombra glow,
   ícone `+` com font-size 1.8rem, cor branca.
   Hover: `transform: scale(1.1); box-shadow: 0 0 30px rgba(0,242,255,0.4)`
   Click: `setCreateTaskOpen(true)`
   Só visível quando `activeTab === 'Task Manager'`.

2. MODAL DE CRIAÇÃO:
   Estado: `createTaskOpen` boolean + `newTaskForm` object.
   
   Form fields (todos com estilo glassmorphism):
   - `Título *` → text input (required)
   - `Prioridade` → select: Alta / Média / Baixa (default: Média)
   - `Responsável` → select populado com `agentList.map(a => a.agent_name)`
     + opção "Não atribuído"
   - `Descrição` → textarea 3 linhas
   - `Aprovado pelo Budget?` → toggle switch (default: false)

   Botões: `[Cancelar]` + `[✓ Criar Tarefa]` (primary)

3. SUBMISSÃO:
   POST para `POST /api/tasks/create` com o form data.
   No `entrypoint.py`, criar endpoint que:
   - Gera ID: `TRD_${Date.now().toString(36).toUpperCase()}`
   - Monta o objeto de demanda
   - Adiciona no `demands/registry.json` via GCS
   - Retorna `{ status: 'success', task }`

4. PÓS-CRIAÇÃO:
   - Fechar modal
   - Chamar `fetchData()` para recarregar tasks
   - Toast de sucesso: "Tarefa [título] criada!"
   - Novo card aparece no Kanban com animação 
     `animation: slideDown 0.4s ease` + border highlight 
     por 2s

5. VALIDAÇÃO:
   - Campo Título required (mostrar erro inline se vazio)
   - Botão Criar desabilitado se título vazio
```

## Arquivos Envolvidos
- `frontend/src/App.jsx`
- `entrypoint.py` (endpoint POST /api/tasks/create)
- `frontend/src/index.css`

## Critério de Conclusão
- FAB visível apenas no Task Manager
- Modal abre e fecha com animação
- Validação de título obrigatório
- Tarefa aparece no Kanban imediatamente após criação
- Toast de confirmação via sistema da TASK-36

# TASK-52 | Pipeline Builder: Preview de Output e Execução Real Encadeada

## Metadata
| Campo | Valor |
|---|---|
| ID | TASK-52 |
| Grupo | Pipeline / UX |
| Prioridade | Alta |
| Responsável | FrontendAgent |
| Status | Aberto |

## Problema Identificado
A aba Pipeline atual tem problemas sérios de UX e funcionalidade:

1. **`prompt()` nativo do browser** para inserir a instrução de cada agente — mesmo problema dos `alert()`, bloqueante e feio.
2. **Execução fake**: o loop chama `POST /api/tasks/execute?task_id=PIPELINE` com `task_id` literal "PIPELINE" — isso vai falhar no backend pois não existe task com esse ID.
3. **Sem preview encadeado**: o output do Step 1 não é visualmente conectado como input do Step 2.
4. **Sem estado de progresso**: durante a execução, nenhum feedback de qual step está rodando.
5. **Results dump no final**: todos os resultados aparecem juntos em `details` collapsibles sem contexto visual de fluxo.

## Objetivo
Refatorar o Pipeline Builder com um formulário de instrução inline por step, execução real com progresso visual, e visualização de output encadeado onde o resultado de cada step aparece abaixo do card do agente antes de passar para o próximo.

## Cenário Real
Pipeline com 3 steps: FinOpsGuardian → QualityInspector → BriefingAgent.
O usuário vê os 3 cards conectados por linhas. Clica "Run". Step 1 começa a girar → resultado aparece abaixo do card 1 → Step 2 começa → usa o output do Step 1 como contexto → resultado abaixo do card 2 → Step 3 finaliza → relatório final.

## Prompt para Antigravity

```
No `frontend/src/App.jsx`, refatorar a aba 'Pipeline':

1. ADICIONAR STEP com formulário inline:
   Ao clicar em um agente no repositório, ao invés de `prompt()`:
   - O agente aparece na área do pipeline com um `<textarea>` 
     inline para a instrução (placeholder: "Instrução para este agente...")
   - Botão `[+ Adicionar]` abaixo do textarea confirma

2. VISUALIZAÇÃO DO PIPELINE como flow vertical:
   Cada step: card do agente com número + instrução resumida
   Entre steps: conector visual com seta `↓` e linha vertical dashed
   
   Quando pipeline tem > 1 step, mostrar contexto:
   `"receberá o output do step anterior como contexto"`

3. ESTADO DE EXECUÇÃO POR STEP:
   Array `stepStatuses`: `['idle' | 'running' | 'done' | 'error']`
   
   Card do step quando `running`:
   - Borda pulsante cyan
   - Spinner no lugar do número
   - Texto "Executando..."
   
   Card quando `done`:
   - Borda verde
   - Número substituído por `✓`
   - Output do agente aparece abaixo do card em um bloco 
     de código com `animation: slideDown 0.3s ease`

4. EXECUÇÃO REAL ENCADEADA:
   Criar endpoint `POST /api/pipeline/run` no `entrypoint.py`:
   ```python
   @app.post("/api/pipeline/run")
   async def run_pipeline(data: dict, request: Request, token: str = None):
       steps = data.get("steps")  # [{agent_name, instruction}]
       context = ""
       results = []
       for step in steps:
           full_task = f"{step['instruction']}\n\nCONTEXTO DO STEP ANTERIOR:\n{context}"
           # carregar agente e executar
           result, _ = agent_obj.run(full_task)
           context = result  # output vira input do próximo
           results.append({"agent": step["agent_name"], "output": result})
       return {"results": results}
   ```
   
   No frontend, iterar os steps no array e atualizar 
   `stepStatuses[i]` = 'running' → 'done' progressivamente 
   (simular via setTimeout entre steps se não tiver streaming).

5. RESULTADO FINAL:
   Após todos os steps, mostrar card especial "PIPELINE COMPLETE"
   com o output do último step em destaque + opção de salvar 
   como nova tarefa no Kanban.
```

## Arquivos Envolvidos
- `frontend/src/App.jsx`
- `entrypoint.py` (endpoint POST /api/pipeline/run)
- `frontend/src/index.css`

## Critério de Conclusão
- Zero `prompt()` nativos
- Execução real encadeada com contexto entre steps
- Status visual por step (idle/running/done/error)
- Output de cada step visível inline
- Opção de salvar resultado como task

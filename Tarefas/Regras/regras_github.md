# 🛠️ Regras de Fluxo e Governança GitHub - Flose AI

Para garantir a qualidade, rastreabilidade e produtividade no desenvolvimento da plataforma, este documento estabelece o fluxo obrigatório para toda interação com o repositório:

### 1. 🔄 Atualização Constante (Sync)
- Antes de iniciar qualquer tarefa ou abrir uma nova branch, **SEMPRE** dê um `git fetch origin` e `git pull origin main`. 
- Nunca trabalhe sobre uma base defasada para evitar conflitos no Pull Request.

### 2. 🌿 Branches Dedicadas
- **NUNCA** faça commits diretos na `main`.
- Toda nova ideia, bugfix ou melhoria deve ter sua própria branch (ex: `feat/minha-tarefa` ou `fix/bot-travado`).

### 3. 🎯 Um Commit por Ajuste/Tarefa
- Cada funcionalidade ou tarefa da pasta `Tarefas` deve ser um commit individual.
- Se houver ajustes de hotfix no meio do caminho, eles devem ser commitados separadamente ou squashed na tarefa correspondente, mantendo o histórico limpo.

### 4. 📝 Mensagens de Commit Claras
- As mensagens devem descrever **O QUE** e **POR QUE** (ex: `feat: implementa preview de tokens na dashboard (TASK-06)`).
- Preferencialmente em Português (pt-br) quando solicitado pelo usuário.

### 5. 🚀 Pull Request para Aprovação
- O trabalho não termina no `git push`. 
- É obrigatório gerar o link de comparação (`compare/main...branch`) e enviar para o usuário aprovar o Pull Request no GitHub.

### 6. 🧹 Limpeza Pós-Conclusão
- Após o merge e a validação do usuário, apagar o arquivo `.md` correspondente na pasta `Tarefas` para manter o backlog atualizado.

---
*Assinado: Cognitive Orchestrator & Antigravity (IA)*

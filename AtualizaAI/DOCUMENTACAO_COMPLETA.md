# Documentação da Plataforma Flose AI 🤖 (v4.3)

Esta documentação fornece uma visão detalhada de todos os componentes, arquitetura e fluxos da **Flose AI Platform**, atualizada com os protocolos de robustez e segurança de nível industrial.

---

# 📔 DOCUMENTAÇÃO TÉCNICA - FLOSE AI PLATFORM

## Versão: 4.8 - "Eco & Governance Edition"
**Data:** 13 de Março de 2026

### 1. Visão Geral
A Flose AI Platform evoluiu para uma estrutura de **Micro-Serviços Orquestrados** com foco em economia de escala (FinOps), governança técnica (Terraform) e execução autônoma de tarefas.

### 2. Novas Funcionalidades (v4.5 - v4.8)

#### 🧬 Agent Task Runner (Execução Real)
Os agentes deixaram de ser apenas prompts e passaram a ser executores.
*   **Método `.run()`**: Cada agente especialista agora possui inteligência própria baseada em seu `system_prompt`.
*   **Kanban Ativo**: Demandas no status "Aberto" podem ser delegadas a agentes específicos no Dashboard.
*   **Entrega Transparente**: O resultado das execuções é salvo no GCS (`logs/executions/`) e pode ser visualizado diretamente no card "Concluído".

#### 🛡️ Governança e FinOps (Human-in-the-loop)
Implementação de regras estritas para evitar gastos desnecessários e garantir infraestrutura como código.
*   **FinOps_Architect**: Agente especializado em estimativa de custos e justificativa de ROI.
*   **Terraform_Specialist**: Gera planos `.tf` para qualquer alteração de infraestrutura requerida.
*   **Trava de Aprovação**: Nenhuma tarefa técnica pode ser executada sem o **OK Orçamentário** (Selo ✅ no card). O usuário deve revisar as specs (Terraform/Custo) antes de liberar a execução.

#### 📉 Eco-Mode (Economia Zero-Base)
Arquitetura otimizada para custo mínimo no Google Cloud Run.
*   **On-Demand Scaling**: O container escala para zero quando inativo, eliminando custos fixos de 24h.
*   **Telegram Webhooks**: Substituição do polling constante por Webhooks. O Telegram "acorda" o container apenas quando há mensagens.
*   **Gateway FastAPI**: Um entrypoint unificado gerencia o tráfego do Webhook e faz o proxy do Dashboard Streamlit usando WebSockets estáveis.

### 3. Arquitetura de Software

#### Orquestrador Cognitivo (`cognitive_orchestrator.py`)
*   **Política Agent-First**: Prioriza a criação de especialistas antes de responder sobre novas tecnologias.
*   **Short-term Memory**: Mantém o contexto da conversa recente para respostas mais precisas.
*   **Schema Robusto**: Validação via Pydantic com campos para `budget_approved`, `terraform_plan` e `cost_explanation`.

#### Fluxo de Dados
1.  **Entrada**: Usuário interage via Telegram (Webhook) ou Dashboard.
2.  **Decisão**: Orquestrador decide entre `respond`, `create_agent` ou `generate_demand`.
3.  **Aprovação**: Se for uma demanda técnica, o usuário revisa o custo/plano Terraform e dá o `OK`.
4.  **Execução**: O especialista selecionado processa a tarefa e salva a "Entrega" no GCS.
5.  **Aprendizado**: O Grafo de Conhecimento é atualizado com os novos conceitos aprendidos ou implementados.

### 4. Stack Tecnológica Atualizada
*   **Core**: Python 3.11, FastAPI, Streamlit.
*   **IA**: Gemini 2.5 Flash (Multimodal + Protoloco de decisão).
*   **Storage/Infra**: GCS (Registry), GCP Cloud Run (Eco-Mode), Secret Manager.
*   **Conectividade**: Webhooks Telegram, `fastapi-proxy-lib`.
*   **Segurança**: Master Key via Secret Manager, SSL nativo GCP.

---
*Flose AI: Construindo a inteligência do futuro com governança e eficiência hoje.*

#### Secret Manager Integration
- A `MASTER_KEY` e outras chaves sensíveis não ficam mais em arquivos `.env` no servidor de produção. Elas são injetadas via **GCP Secret Manager** durante o deploy.

#### `deploy_gcp.ps1`
- Script de automação total que gerencia: Artifact Registry, Cloud Build, IAM Permissions, Secret Manager e o Deploy final no Cloud Run.

---

## 🛠️ Manual Funcional e Fluxos de Operação

### 1. Ciclo de Decisão Robusto
1. **Entrada**: Comando do usuário + Histórico recente + Imagem (opcional).
2. **Avaliação**: O Orquestrador avalia a intenção comparando com a memória semântica (RAG).
3. **Validação**: A saída é validada pelo schema Pydantic.
4. **Execução**:
   - Se for uma ação: Cria TRD no Kanban e notifica.
   - Se for conhecimento: Responde e atualiza o Grafo via Clusterização IA.
   - Se for complexo: Cria um agente especializado.

### 2. Regra de Ouro do Conhecimento
Para evitar que o Grafo se torne "sujo", o sistema segue a política: **Nenhum nó novo sem um agente ou um TRD prévio.** Isso garante que o conhecimento no grafo seja sempre validado por uma ação real.

---

## 🚀 Como Executar

### Configuração Inicial
1. Certifique-se de que a `MASTER_KEY` está definida no Secret Manager de seu projeto GCP.
2. O bucket GCS deve seguir o padrão `flose-ai-platform-[PROJECT_ID]`.

### Comandos
- **Deploy**: `./deploy_gcp.ps1`
- **Reset de Emergência**: `python reset_system.py` (Zera grafo, memória e backlog).
- **Dashboard**: `streamlit run src/dashboard/Home.py`

---
**Flose AI Platform** - *Decidir, Agir e Evoluir.*

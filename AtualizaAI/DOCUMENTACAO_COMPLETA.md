# Documentação da Plataforma Flose AI 🤖 (v4.3)

Esta documentação fornece uma visão detalhada de todos os componentes, arquitetura e fluxos da **Flose AI Platform**, atualizada com os protocolos de robustez e segurança de nível industrial.

---

## 🏛️ Visão Geral da Arquitetura

A Flose AI é uma plataforma de inteligência artificial multi-agente construída sobre a infraestrutura do **Google Cloud Platform (GCP)**, utilizando o modelo **Gemini 2.5 Flash** como cérebro central.

### Diferenciais da v4.3:
- **Robustez Extrema**: Validação de saída via Pydantic com 3 níveis de retry e feedback corretivo.
- **Memória Híbrida**: Combinação de RAG (longo prazo) com Contexto Conversacional (curto prazo).
- **Clusterização via IA**: O Grafo de Conhecimento organiza-se dinamicamente usando o Gemini, sem categorias estáticas.
- **Segurança Nativa**: Integração com **Google Secret Manager** para chaves sensíveis.

---

## 📂 Componentes Principais

### 1. Núcleo (Core)

#### `src/orchestrator/cognitive_orchestrator.py`
- **Classe**: `CognitiveOrchestrator`
- **Inteligência**: Agora utiliza **Pydantic Schemas** para garantir que cada decisão do LLM siga o formato esperado.
- **Mecanismo de Auto-Correção**: Se o modelo falhar na formatação, o sistema inicia um **Retry Loop** enviando o erro exato de volta para a IA se corrigir.
- **Memória de Curto Prazo**: O orquestrador agora processa o `chat_history`, permitindo perguntas de acompanhamento (ex: "Quem é ele?" ou "Quanto custa essa tecnologia?").
- **Modos de Operação**:
  - `RESPOND`: Conhecimento teórico e conversa.
  - `CREATE_AGENT`: Geração de novos agentes.
  - `EXECUTE`: Delegação de tarefas.
  - `GENERATE_DEMAND`: **Prioridade máxima** para novos pedidos no Backlog (TRD).

---

### 2. Gestão de Conhecimento (`src/storage/` & `src/graph/`)

#### `knowledge_graph.py`
- **AI Clusterization**: O sistema não usa mais um dicionário fixo. Ele pergunta ao Gemini: *"A qual cluster técnico este conceito pertence?"*.
- **Sanitização Proativa**: A lógica de limpeza de nós de ruído (commands, logs) agora é executada automaticamente em cada interação, mantendo o grafo limpo e profissional.
- **Pilares Estratégicos**: AI Models, GCP Infrastructure, Data Engineering, Programming, DevOps, UI/Analytics, Automation e FinOps.

#### `vector_store.py`
- **Tecnologia**: FAISS + Gemini Embeddings (`models/gemini-embedding-001`).
- **Persistência GCS**: Os índices e metadados são salvos e carregados do GCS, garantindo que a memória sobreviva a reinicializações de container.
- **Visualização**: Implementa projeção PCA para visualizar a densidade da memória em 2D no dashboard.

---

### 3. Segurança e Infraestrutura

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

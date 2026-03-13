# Documentação da Plataforma Flose AI 🤖

Esta documentação fornece uma visão detalhada de todos os componentes, arquitetura e fluxos da **Flose AI Platform**.

---

## 🏛️ Visão Geral da Arquitetura

A Flose AI é uma plataforma de inteligência artificial multi-agente construída sobre a infraestrutura do **Google Cloud Platform (GCP)**, utilizando o modelo **Gemini 2.5 Flash** como cérebro central. A plataforma integra processamento de linguagem natural, visão computacional, armazenamento vetorial e grafos de conhecimento.

### Fluxo de Dados:
1. **Entrada**: Usuário interage via Telegram ou Dashboard.
2. **Orquestração**: O `CognitiveOrchestrator` analisa a intenção (e imagens, se houver).
3. **Decisão**: O Orchestrator decide se deve responder diretamente, criar um novo agente ou executar uma tarefa.
4. **Segurança/FinOps**: O `FinOpsGuardian` valida se a execução cabe no orçamento de tokens e custos.
5. **Persistência**: Dados são salvos no Google Cloud Storage (GCS) e indexados no `VectorStore`.
6. **Aprendizado**: O `KnowledgeGraphManager` atualiza o grafo com novos conceitos técnicos aprendidos durante a interação.

---

## 📂 Componentes Principais

### 1. Núcleo (Core)

#### `main.py`
- **Função**: Ponto de entrada para testes e bootstrap da plataforma.
- **Responsabilidades**: Inicializa as camadas de storage, vector DB, knowledge graph e orchestrator. Demonstra um fluxo completo de processamento de comando.

#### `src/orchestrator/cognitive_orchestrator.py`
- **Classe**: `CognitiveOrchestrator`
- **Missão**: Decidir, agir e evoluir como o cérebro central (Gemini 2.5 Flash).
- **Modos de Operação**:
  - `RESPOND`: Resposta inteligente direta.
  - `CREATE_AGENT`: Geração proativa de novos agentes.
  - `EXECUTE`: Delegação para agentes existentes.
  - `GENERATE_DEMAND`: Registro de TRDs (Tarefas, Reuniões, Follow-ups).
- **Schema JSON (Obrigatório)**:
  ```json
  {
    "action": "respond | create_agent | execute | generate_demand",
    "reasoning": "Texto explicativo",
    "finops_check": { "estimated_tokens": n, "estimated_cost_usd": n, "approved": true },
    "agent_involved": "nome_do_agente",
    "knowledge_graph_update": ["conceitos"],
    "response": "Resposta final"
  }
  ```

---

### 2. Sistema de Agentes (`src/agents/`)

#### `base_agent.py`
- **Classe**: `BaseAgent`
- **Função**: Classe base abstrata para todos os agentes do ecossistema. Fornece métodos para registro no sistema e serialização.

#### `telegram_agent.py`
- **Classe**: `TelegramAgent`
- **Função**: Ponte de comunicação via Telegram.
- **Funcionalidades**:
  - Recebe textos e imagens.
  - Integra-se ao `VisionAgent` para análise visual.
  - Traduz comandos do chat para decisões do Orchestrator.
  - Mantém logs de atividade no GCS.

#### `vision_agent.py`
- **Classe**: `VisionAgent`
- **Função**: Especialista em análise de imagens.
- **Tecnologia**: Gemini 2.5 Flash (Multimodal).
- **Uso**: Descreve conteúdos visuais para que o Orchestrator possa tomar decisões baseadas em fotos/documentos enviados.

#### `finops_guardian.py`
- **Classe**: `FinOpsGuardian`
- **Função**: Guardião financeiro e de recursos.
- **Responsabilidades**: Estima o uso de tokens e custos de infraestrutura antes da execução, bloqueando operações que excedam os limites configurados.

---

### 3. Gestão de Conhecimento e Dados (`src/storage/` & `src/graph/`)

#### `knowledge_graph.py`
- **Classe**: `KnowledgeGraphManager`
- **Função**: Gerencia o Grafo de Conhecimento (NetworkX).
- **Recursos**: Mapeia conceitos técnicos (ex: Python, Terraform, BigQuery) e suas relações com pilares tecnológicos da plataforma.

#### `vector_store.py`
- **Classe**: `VectorStore`
- **Função**: Memória semântica de longo prazo.
- **Tecnologia**: FAISS + Gemini Embeddings (`models/embedding-001`).
- **Uso**: Armazena e recupera documentos e contextos com base em similaridade vetorial.

#### `gcs_client.py`
- **Classe**: `GCSClient`
- **Função**: Interface simplificada com o Google Cloud Storage.
- **Capacidades**: Upload/Download de arquivos e JSONs, listagem e verificação de existência de blobs.

#### `finops_manager.py`
- **Classe**: `FinOpsManager`
- **Função**: Rastreamento real de custos.
- **Responsabilidades**: Calcula custos baseados no uso real de tokens (Input/Output) do Gemini e gera summaries diários.

#### `gcp_resource_manager.py`
- **Classe**: `GCPResourceManager`
- **Função**: Monitoramento de infraestrutura.
- **Funcionalidades**: Checa o status de serviços no Cloud Run e busca métricas de utilização de recursos via Cloud Monitoring.

---

### 4. Interface e Dashboard (`src/dashboard/`)

#### `Home.py`
- **Framework**: Streamlit.
- **Função**: Página principal do dashboard. Exibe o status de saúde do sistema, métricas financeiras e o estado dos agentes.

#### `pages/Command_Center.py`
- **Função**: Interface de controle interativa.
- **Recursos**: Chat em tempo real com o Orchestrator, visualização de logs e histórico de decisões.

---

### 5. Scripts de Manutenção

#### `cleanup_graph.py` & `deep_clean_graph.py`
- **Função**: Limpeza e normalização do `global_graph.json`.
- **Ações**: Remove nós órfãos, normaliza nomes de conceitos e assegura a integridade da estrutura hierárquica do grafo.

---

---

## 🛠️ Manual Funcional e Fluxos de Operação

### 1. Interação via Telegram
O usuário interage com a plataforma através do bot oficial.
- **Comando `/start`**: Inicializa a sessão e confirma o status do bridge.
- **Envio de Texto**: Comandos diretos (ex: "Crie um relatório", "O que é Kubernetes?") são enviados ao Orchestrator.
- **Envio de Imagem**: Ativa automaticamente o `VisionAgent`. A descrição da imagem é enviada como contexto extra para o Orchestrator.
- **Feedback**: O bot exibe o raciocínio (`reasoning`) breve e o resultado final da execução.

### 2. Ciclo de Decisão do Orchestrator
O sistema não apenas responde, ele **decide**:
- **Respond (Responder)**: Para dúvidas gerais, o sistema utiliza sua base interna e o contexto do `VectorStore`.
- **Create Agent (Criar Agente)**: Se o usuário pede uma automação recorrente, o sistema gera o código/configuração de um novo agente e o registra no `registry.json` no GCS.
- **Execute (Executar)**: Se já existe um agente capaz de realizar a tarefa, o Orchestrator delega a execução.

### 3. Proteção FinOps (Segurança de Custo)
Toda execução pesada passa pelo `FinOpsGuardian`:
1. **Estimativa**: O sistema conta os caracteres e estima o custo de tokens.
2. **Validação**: Verifica no arquivo `daily_usage.json` se o limite diário (padrão $10.00) foi atingido.
3. **Bloqueio**: Se exceder, a tarefa é abortada com uma mensagem de segurança, evitando gastos inesperados no GCP.

---

## 🚀 Casos de Uso (Exemplos Práticos)

### Caso A: Criação de um Agente de Notícias
1. **Usuário no Telegram**: "Gostaria de um agente que monitore notícias de IA."
2. **Orchestrator**: Identifica a ação `create_agent`.
3. **Sistema**: Cria a entrada no registro, define o propósito e salva no GCS.
4. **Resultado**: O usuário recebe a confirmação e o agente está pronto para ser instanciado.

### Caso B: Análise de Print de Infraestrutura
1. **Usuário no Telegram**: Envia um print da tela do GCP Console.
2. **VisionAgent**: Analisa o print: "A imagem mostra um erro 403 no Cloud Run..."
3. **Orchestrator**: Recebe a análise e sugere: "Parece um erro de permissão IAM. Verifique a service account."
4. **Resultado**: Diagnóstico técnico rápido sem necessidade de digitar detalhes.

---

## 🛠️ Configuração e Execução

### Variáveis de Ambiente (.env)
- `GEMINI_API_KEY`: Chave do Google AI Studio.
- `TELEGRAM_BOT_TOKEN`: Token gerado pelo BotFather.
- `GCP_PROJECT_ID`: ID do projeto no Google Cloud.
- `GCP_REGION`: Região preferencial (ex: us-central1).

### Comandos Úteis
- **Rodar a Plataforma (CLI)**: `python main.py`
- **Rodar o Bot do Telegram**: `python run_telegram_bot.py`
- **Rodar o Dashboard**: `streamlit run src/dashboard/Home.py`

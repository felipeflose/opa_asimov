# Documentação da Plataforma Flose AI 🤖 (v5.0)

## Versão: 5.0 - "Sovereign Framework & React UI"
**Data:** 14 de Março de 2026

### 1. Visão Geral
A Flose AI Platform agora opera com um frontend de ultra-performance construído em **React/Vite**, substituindo o antigo Streamlit para proporcionar uma experiência de usuário (UX) premium, fluida e com monitoramento em tempo real. A arquitetura de agentes atingiu o estado de **Soberania**, permitindo gestão total via linguagem natural.

### 2. Novas Funcionalidades (v5.0)

#### 🧪 Agent Library & Metrics
A gestão de agentes foi centralizada e enriquecida com dados:
*   **DNA Editing**: O propósito e o `system_prompt` de qualquer agente podem ser editados diretamente na UI ou via chat inteligente.
*   **Metrics Tracker**: Cada agente agora rastreia seu histórico de execuções (`runs`) e o total de tokens processados, permitindo auditoria de performance individual.
*   **Registry Assistant**: Um chat dedicado na biblioteca de agentes permite fazer perguntas sobre quem é cada especialista e solicitar alterações sem mexer em código.

#### 📡 Telegram Sovereignty
O bot do Telegram tornou-se o principal terminal de comando soberano:
*   **Agent Management**: Comandos como "Crie um agente para auditoria" ou "Mude o prompt do FinOps" são processados e aplicados ao `registry.json` instantaneamente pelo Orquestrador.
*   **Implicit Execution**: No Task Manager, a escolha manual de agentes foi removida. O sistema delega automaticamente para o responsável definido na TRD, simplificando o fluxo "Human-in-the-loop".

#### 💎 FinOps Guardian (Real Costs)
*   **Infrastructure Integration**: O monitoramento de custos agora inclui estimativas reais do GCP vindas do SDK (Cloud Monitoring/Billing), além do custo de tokens do Gemini.
*   **Daily Breakdown**: Visualização clara de tokens, chamadas de API e custo projetado diário.

### 3. Arquitetura de Software (React Transition)
*   **Frontend**: React 18, Vite, Vanilla CSS com Glassmorphism.
*   **Backend API**: Gateway FastAPI unificado que serve o app estático e fornece os endpoints `/api/*` em substituição ao proxy do Streamlit.
*   **Orquestrador (Update Agent)**: Nova lógica de decisão que permite ao LLM reescrever arquivos de configuração de outros agentes no GCS.

### 4. Stack Tecnológica
*   **Core**: Python 3.11, FastAPI, React (Frontend).
*   **IA**: Gemini 2.5 Flash (Soberano).
*   **Storage**: GCS (Persistent Layer), VectorStore (Semantic Memory).
*   **Deploy**: Cloud Run (Containerizado) com scaling zero-base.

---
**Flose AI Platform 2026** - *The era of Sovereign Autonomous Agents.*

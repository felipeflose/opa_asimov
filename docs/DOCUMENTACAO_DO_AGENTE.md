# 🕵️‍♂️ OpenClaw: Auditor Socratica (Neural Graph Refiner)

Este documento define a missão, as leis e o protocolo de operação do Agente Auditor responsável pelo refinamento contínuo do DNA Neural de Felipe Flose.

## 🎯 Missão Principal
O Agente não é um sincronizador de dados; ele é um **Curador de Sinergias**. Sua função é combater o "Silenciamento do Conhecimento", encontrando pontes invisíveis entre os mundos do **MBA**, **TRABALHO** e **TECNOLOGIA**.

---

## ⚖️ As Leis da Arquitetura (Lineage Laws)

O Agente deve operar sob a **"Lei da Polaridade Solar"**:
1.  **Felipe Flose (Mestre)** é a origem de toda a gravidade (Nível 0).
2.  **Super-Hubs** (MBA/Work/Tool) são emanações diretas do Mestre (Nível 1).
3.  **Nichos/Clusters** são especializações dos Hubs (Nível 2).
4.  **Notas/Ativos** são a materialização do saber (Nível 3).

> **IMPORTANTE**: Em qualquer nova conexão criada pelo agente, o nó de **menor profundidade** (mais perto do Mestre) deve ser sempre o `source` (origem).

---

## 🔄 O Loop de Auditoria (Socratic Cycle)

O Agente opera em ciclos infinitos de "Meditação Digital":

1.  **Seleção Provocativa**: O agente escolhe um nó de uma sessão e o confronta com nós de sessões opostas (ex: IA no MBA vs Cloud na Carreira).
2.  **Raciocínio de Ponte**: Ele utiliza o modelo **Gemma4** para responder: *"Se eu unisse estes dois ativos, qual insight estratégico nasceria para a carreira do Felipe?"*.
3.  **Materialização Auditada**: Se o insight for validado pela IA, o link é inserido com o prefixo `[REFINO AGENTE]`.

---

## 🛠️ Especificações Técnicas (OpenClaw Entry)

- **Arquivos Principais**: `agent_edge.py` (Auditor de Linhagem) e `agent_graph_generator.py` (Motor de Grafo)
- **Motor**: Ollama / Llama 3.1 / Gemma 4
- **Persistência**: `obsidian_graph.json`
- **Output**: JSON estruturado com campo `reasoning` (justificativa).

## 🚀 Como Expandir o Agente
No futuro, o agente poderá ter permissão para:
- **Fusão de Nichos**: Identificar que "Python" e "Data Science" devem se tornar um único cluster maior.
- **Identificação de "Gaps"**: Alertar quando uma matéria de MBA não tem nenhuma aplicação prática na carreira (nó sem pontes).

## 🔌 Protocolo Operacional (Execução)

Para manter o ecossistema saudável, o Agente deve seguir estas instruções de manutenção:

### 1. Integridade do JSON
- **Acesso**: O arquivo `obsidian_graph.json` é a "Verdade Única".
- **Gravação**: O Agente deve realizar um `load -> modify -> dump` rápido para evitar conflitos com o motor de sincronização.
- **Backup**: Recomenda-se que o agente crie uma cópia `obsidian_graph.json.bak` antes de grandes reestruturações.

### 2. Ciclo de Atualização Visual
- O Agente de Refino altera o JSON, mas o **Flask (Server)** e o **D3.js (UI)** lêem o arquivo a cada 2-5 segundos.
- **NÃO é necessário reiniciar o Flask** para que os refinos apareçam; a UI detecta a mudança e "kika" a simulação automaticamente.

### 3. Orquestração de Processos
Se o sistema parecer lento ou travado:
1.  **Matar Processos Antigos**: `lsof -ti :8091 | xargs kill -9`.
2.  **Reiniciar Servidor**: `python app.py`.
3.  **Reiniciar Motor**: `python agent_graph_generator.py`.
4.  **Reiniciar Auditor**: `python agent_edge.py`.

---

## 🛠️ Manutenção Estratégica (O que alterar?)

O Agente tem "alvará" para:
- **Remover Duplicidade**: Se encontrar dois nichos semanticamente idênticos, ele deve reportar e sugerir a fusão.
- **Ajustar Pesos**: Aumentar o `distância` de links que ele provar serem fracos ou obsoletos.
- **Renomeação**: Melhorar o `title` de notas que tenham nomes brutos do Obsidian para nomes estratégicos.

---
*Assinado: Arquiteto de Sistemas Anti-Gravity.*

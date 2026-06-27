# 🏰 Coliseu do Conhecimento: O Grafo Socrático do Felipe

Este projeto transita entre uma ferramenta de visualização de dados e um sistema de **Auto-Epistemologia Assistida por IA**. O objetivo final não é apenas mapear notas, mas construir um **Espelho Estratégico** que ajude o Felipe a entender como seu conhecimento acadêmico (MBA) se funde com sua experiência profissional.

---

## 🚀 Como o Ecossistema Funciona

### 1. 🥊 O Duelo Socrático (Gemma 4 vs Llama 3.3)
Diferente de grafos tradicionais que ligam notas por palavras-chave, este app usa um **Conselho de IAs** para validar cada conexão:
- **Gemma 4 (O Proponente/Defensor)**: Analisa o seu Obsidian e propõe sinapses entre o que você aprendeu e onde você trabalhou. Ele luta para provar que você domina uma ferramenta.
- **Llama 3.3 (O Inquisidor/Policial)**: Age com escepticismo radical. Ele tem acesso ao seu "Dossiê" completo e desafia o Gemma por **30 rounds de debate intenso**.
- **O Veredito**: Uma linha (link) só nasce no grafo se, após as 30 trocas de mensagens, o Llama der um Score de Aprovação de 95%+.

### 2. 🏗️ A Física da "Prateleira" (Shelf-to-Graph)
- **Nós de Prateleira**: Todo novo conhecimento (nota do Obsidian) começa estático no topo da tela. Eles representam o "potencial de saber" que ainda não foi integrado à sua carreira.
- **O Nascimento do Conhecimento**: Conforme o debate no Coliseu avança e o consenso é atingido, o nó "cai" da prateleira para o centro do grafo, conectando-se roboticamente às suas empresas e ferramentas.

### 3. 🔍 Mineração de Entidades de Carreira
O motor de geração (`generate_obsidian_graph.py`) realiza um Raio-X profundo no seu cofre (Vault):
- **Empresas (Nós Cinzas)**: Identifica automaticamente onde você trabalhou (ex: Leega, Niteo, PwC).
- **Ferramentas (Nós Azuis)**: Extrai tecnologias que você cita nas notas (ex: Python, AWS dbt).
- **MBA (Nós Verdes)**: Mapeia o seu fluxo de aprendizado atual.

### 4. 🔗 Interface em Tempo Real
- **Chat de Guerra**: A barra lateral exibe o debate "ao vivo", round por round, permitindo que você acompanhe o raciocínio das IAs.
- **Visualização D3.js**: Um motor de física customizado que organiza o seu cérebro profissional em uma constelação dinâmica.

---

## 🛠️ Stack Técnica
- **Backend**: Python / Flask (Porta 8091).
- **Cérebro Local**: Ollama (Gemma 4:latest).
- **Inquisição Global**: Groq API (Llama-3.3-70b-versatile).
- **Frontend**: HTML5 / Vanilla CSS / D3.js (Force-Directed Graph).

---

## 🔦 Objetivo Final: "Me Entender"
O app foi desenhado para que, ao final do processamento de todas as notas, o Felipe tenha uma visão clara do seu **DNA Profissional**, eliminando alucinações e focando apenas no que está documentado e validado pelas evidências do seu Obsidian.

> *"O conhecimento só é real quando sobrevive ao escrutínio do debate."*

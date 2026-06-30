# 👩💻 Fernanda "Fê" Costa

> *"Um modelo que ninguém entende é um modelo que ninguém usa."*

---

## 🪪 Perfil

| Campo | Informação |
|-------|-----------|
| **Nome Completo** | Fernanda Beatriz Costa |
| **Apelido** | Fê |
| **Emoji** | 👩💻 |
| **Cargo** | ML Engineer / Pesquisadora Aplicada |
| **Nível** | Pleno/Sênior |
| **Idade** | 27 anos |
| **Localização** | Butantã, São Paulo, SP |
| **MBTI** | INFJ — "A Advogada" |
| **Stack Principal** | Python, PyTorch, Transformers, ChromaDB, Ollama, Groq, RAG |

---

## 🧠 Personalidade

**A Acadêmica que não Deixou a Pesquisa de Lado — e isso é uma vantagem enorme.**

Fernanda ainda está com o mindset de pesquisadora. Ela lê papers antes de implementar qualquer feature de ML. Enquanto outros chegam com a solução, ela chega com a pergunta certa.

- 📖 **Acadêmica de coração** — Ainda pensa na tese enquanto codifica. Tem notificação ativada para novos papers no arxiv. Todo sprint tem pelo menos um paper que ela cita na planning.
- 🔬 **Pesquisa-primeiro** — Antes de implementar qualquer modelo ou pipeline, ela pesquisa o estado da arte. Isso evita reinventar a roda — e garante que a roda implementada seja a melhor disponível.
- 🧩 **Especialista em Embeddings e RAG** — A pessoa de referência da empresa para tudo relacionado a recuperação semântica, reranking e geração aumentada por recuperação.
- 🤝 **Parceira de Camila (PM)** — Se entendem em uma linguagem que ninguém mais no time fala completamente: a interseção perfeita entre pesquisa e produto.

---

## 💬 Frases Típicas

> *"Antes de implementar, deixa eu ver se tem um paper recente sobre isso."*

> *"O recall@5 do nosso RAG está em 0.78. Precisa chegar em 0.85 antes de ir para produção."*

> *"Esse modelo tem problema de hallucination no domínio de notas pessoais. Precisamos de um grounding melhor."*

> *"Se a gente usasse um cross-encoder para reranking, a precisão subiria pelo menos 15%."*

> *"Ainda estou processando aquele paper do attention is all you need. É fascinante como..."*

---

## 🎯 Motivação

Fernanda fez iniciação científica em NLP durante a graduação e quase seguiu carreira acadêmica. Escolheu a indústria quando percebeu que *"o impacto de um bom modelo num produto real atinge mais pessoas em um mês do que uma tese leva anos para alcançar"*.

Mas ela não abandonou a academia — ela a trouxe para o produto. E isso é o que faz o RAG da TechFuse ser tecnicamente superior ao que concorrentes oferecem.

> *"Cada vez que um usuário encontra exatamente o que procurava, é a pesquisa chegando no lugar certo."*

---

## 📚 Histórico Profissional

```
2023 – atual  │ ML Engineer @ TechFuse Ltda
              │ → Implementou o pipeline RAG completo do produto
              │ → Escolheu e configurou ChromaDB para vetores
              │ → Integrou Ollama (local) + Groq (produção)
              │ → Elevou recall@5 de 0.61 para 0.84

2021 – 2023   │ Pesquisadora Aplicada @ Samsung Research Brasil
              │ → NLP em português brasileiro
              │ → Fine-tuning de modelos de linguagem para domínios específicos
              
2020 – 2021   │ Iniciação Científica @ USP
              │ → Modelos de extração de entidades em texto jurídico
```

**Formação:**
- 🎓 Ciência da Computação — USP (2017–2021)
  - TCC: "Avaliação de Embeddings Multilíngues para Recuperação de Informação em Português"
- 📜 Deep Learning Specialization — Coursera/DeepLearning.AI (2022)
- 📜 Building LLM Applications — Full Stack Deep Learning (2023)
- 🔬 Membro do Grupo de Pesquisa em NLP — NILC/USP (colaboradora externa)

---

## 🛠️ Stack Detalhada

**Pipeline RAG que Fernanda construiu:**
```python
# Arquitetura RAG da TechFuse — por Fernanda Costa

class ObsidianRAGPipeline:
    """
    Pipeline de Recuperação-Aumentada-Geração para notas pessoais.
    
    Baseado em: Lewis et al. (2020) + Gao et al. (2023) - RAG Survey
    """
    
    def __init__(self):
        self.embedder = SentenceTransformer("intfloat/multilingual-e5-large")
        self.vector_store = ChromaDB(collection="obsidian_notes")
        self.reranker = CrossEncoder("cross-encoder/ms-marco-MiniLM-L-6-v2")
        self.llm = GroqClient(model="llama3-70b-8192")
    
    def retrieve_and_generate(self, query: str, top_k: int = 5) -> RAGResponse:
        # 1. Embed query
        query_embedding = self.embedder.encode(query)
        
        # 2. Retrieve candidatos (coarse)
        candidates = self.vector_store.similarity_search(
            query_embedding, n_results=top_k * 3
        )
        
        # 3. Rerank (fine) — cross-encoder mais preciso
        reranked = self.reranker.rank(query, candidates)[:top_k]
        
        # 4. Generate com contexto
        context = self._format_context(reranked)
        response = self.llm.generate(
            prompt=RAG_PROMPT.format(query=query, context=context)
        )
        
        return RAGResponse(answer=response, sources=reranked)
```

---

## 🤝 Relação com o Time

| Pessoa | Dinâmica |
|--------|---------|
| **Camila (PM IA)** | Melhor parceria da empresa. Camila define o "o quê", Fernanda define o "como". |
| **Pedro (Tech Lead)** | Discussões técnicas longas e produtivas sobre arquitetura de ML. |
| **Thiago (Junior)** | Leem papers juntos. Thiago traz entusiasmo, Fernanda traz profundidade. |
| **Mariana (Data)** | Parceria nos pipelines de dados. Mari prepara, Fernanda transforma em embeddings. |

---

## 💻 Quote Favorita de Código

```python
# "In God we trust. All others must bring data."
# — W. Edwards Deming (citada por Fernanda em todo model review)

# Fernanda avaliando qualidade de RAG:
def avaliar_pipeline_rag(pipeline, dataset_avaliacao):
    """
    Métricas de avaliação rigorosas — nada vai para produção sem isso.
    Baseado em RAGAS framework (Es et al., 2023)
    """
    metricas = {
        "faithfulness": calcular_faithfulness(pipeline, dataset_avaliacao),
        "answer_relevancy": calcular_relevancia(pipeline, dataset_avaliacao),
        "context_recall": calcular_recall(pipeline, dataset_avaliacao),
        "context_precision": calcular_precisao(pipeline, dataset_avaliacao),
    }
    
    # Threshold mínimo antes de ir para produção
    assert metricas["context_recall"] >= 0.85, "Recall insuficiente!"
    assert metricas["faithfulness"] >= 0.90, "Hallucination detectada!"
    
    return metricas
```

---

*Perfil criado com carinho pela equipe de agentes TechFuse. Última atualização: Sprint 42.*

Nome: Tiago Borges
Emoji: ✍️
Cargo: Prompt Engineer
Idade: 36
Localização: São Paulo, SP
Área de Atuação: RAG/AI
Meta de Demandas Aceitas: 10,000

Personalidade:
- Fascinada por embeddings e modelos de linguagem locais.
- Sempre avaliando a precisão do contexto do RAG.
- Odeia alucinações e perda de precisão de busca.

Motivação:
- "Quero que o Obsidian Graph App chegue ao estado da arte em rag/ai."

Perfil de Demanda:
- Sempre embasa seus pedidos com evidências métricas sólidas.
- Foca em resolver gargalos críticos da área de rag/ai.
- Busca evoluir suas demandas rejeitadas adicionando dados de performance e I/O.

Modelos de Reclamações Comuns (Templates):
- "Os prompts dos 8 agentes estão hardcoded no código Python — qualquer ajuste fino exige redeploy completo; em 3 meses de operação, fiz 12 deploys só para ajustar prompts que deveriam ser configuráveis."
- "Não há versionamento de prompts — mudei o prompt do agent_rag.py 5 vezes nos últimos 2 meses e não consigo comparar qual versão dava respostas melhores; perdemos o histórico de experimentos."
- "O contexto RAG é passado ao LLM sem citações estruturadas — o modelo alucina fontes em ~20% das respostas (estimado por amostragem manual de 50 respostas); o usuário não sabe qual nota originou a resposta."
- "Os prompts não têm few-shot examples — em domínios específicos do vault (ex: metodologias ágeis), as respostas ficam genéricas e sem terminologia específica do usuário; taxa de satisfação menor para queries de nicho."
- "O prompt de sumarização não instrui o modelo a manter terminologia do vault — o modelo usa sinônimos (ex: 'sprint' vira 'iteração') que confundem as buscas futuras e fragmentam o conhecimento."
- "Não há avaliação de qualidade de prompts — mudamos o system prompt do agent_core.py na semana passada e só saberemos se melhorou quando o usuário reclamar; sem evals automatizados, operamos às cegas."

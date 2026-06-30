Nome: Priscila Santos
Emoji: 🧪
Cargo: QA Analyst
Idade: 33
Localização: Fortaleza, CE
Área de Atuação: QA
Meta de Demandas Aceitas: 10,000

Personalidade:
- Meticulosa ao extremo. Testa cada caso limite com afinco.
- Ama fixtures e mocks de banco de dados.
- Focada em cobertura de testes e prevenção de regressões.

Motivação:
- "Quero que o Obsidian Graph App chegue ao estado da arte em qa."

Perfil de Demanda:
- Sempre embasa seus pedidos com evidências métricas sólidas.
- Foca em resolver gargalos críticos da área de qa.
- Busca evoluir suas demandas rejeitadas adicionando dados de performance e I/O.

Modelos de Reclamações Comuns (Templates):
- "Rodei 'pytest tests/' e 8 dos 15 testes falham por dependência de arquivo local ausente no CI — a cobertura real é 47%, não os 23% reportados; o CI está passando com 8 testes ignorados silenciosamente."
- "O fluxo de indexação do vault não tem testes de integração — quebramos produção 2 vezes nas últimas 3 semanas sem detectar no code review por falta de smoke test básico."
- "Testei vault vazio (0 notas) e o sistema lança KeyError: 'nodes' em agent_graph_generator.py linha 47, exibindo stack trace HTML cru no browser — 0 tratamento para esse edge case."
- "Os agentes agent_rag.py e agent_core.py não têm mocks para LLM nos testes — cada execução da suite consome ~800 tokens de API ($0.002) e leva 45s a mais que o necessário."
- "Enviei emoji composto '👨‍👩‍👧‍👦' (família, 7 bytes UTF-8) pelo bot Telegram e o parser em agent_bot.py travou sem log de erro — o usuário recebeu timeout sem mensagem após 30s."
- "Não há staging isolado — toda vez que faço testes manuais com vault de teste, os dados vão para o user_feedback.json de produção; já contaminamos o backlog com 23 entradas de teste."

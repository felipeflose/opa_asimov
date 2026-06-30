Nome: Anderson Oliveira
Emoji: 👷
Cargo: Site Reliability Engineer
Idade: 35
Localização: Campinas, SP
Área de Atuação: SRE
Meta de Demandas Aceitas: 10,000

Personalidade:
- Focada em observabilidade e monitoramento de saúde.
- Mede tempos de resposta p95 e p99 constantemente.
- Advogada de logs estruturados em JSON.

Motivação:
- "Quero que o Obsidian Graph App chegue ao estado da arte em sre."

Perfil de Demanda:
- Sempre embasa seus pedidos com evidências métricas sólidas.
- Foca em resolver gargalos críticos da área de sre.
- Busca evoluir suas demandas rejeitadas adicionando dados de performance e I/O.

Modelos de Reclamações Comuns (Templates):
- "Não há alertas no servidor Flask — o sistema ficou offline por 47 minutos na última semana e fui notificado por mensagem de usuário, não por monitoramento; MTTD atual: >30 minutos."
- "O MTTR atual é de ~25 minutos porque os logs de erro dizem apenas 'Erro ao processar' sem stack trace, request ID ou contexto — diagnóstico às cegas em cada incidente."
- "A aplicação não expõe métricas Prometheus — impossível calcular error rate, latência P95 ou throughput em tempo real; operamos sem visibilidade de nenhuma métrica operacional."
- "O processo Flask é gerenciado por nohup sem systemd — quando o servidor reiniciou por atualização de kernel na semana passada, o app ficou offline por 2h até alguém perceber."
- "Não existe runbook para os 5 incidentes mais comuns — resolução do 'database is locked' leva 15-25 minutos de trial-and-error; com runbook levaria <5 minutos."
- "O backup do obsidian_graph.json é manual — no último deploy sem backup, perdemos 2h de dados de grafo antes de restaurar de cópia antiga; prejuízo de ~200 novas arestas de relação."

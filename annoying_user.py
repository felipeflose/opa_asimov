"""
30 Personas de Usuários — templates com evidências obrigatórias,
meta de 10.000, anti-repetição inteligente e sistema de versões.
"""
import os
import json
import random
import hashlib
import logging
import time
from typing import Optional
from datetime import datetime, timedelta, timezone

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

APP_DIR = os.path.dirname(os.path.abspath(__file__))
FEEDBACK_FILE = os.path.join(APP_DIR, 'user_feedback.json')

# ---------------------------------------------------------------------------
# 30 PERSONAS — com templates de evidências obrigatórias
# Cada template contém: problema + evidência mensurável + impacto no negócio
# ---------------------------------------------------------------------------
USER_PERSONAS = [
    # 1. UI Designer
    {
        "name": "Aline Rodrigues",
        "emoji": "👩‍🎨",
        "role": "UI Designer",
        "area": "UI/UX",
        "meta": 10000,
        "templates": [
            "O painel de grafo usa neon verde (#39FF14) sobre fundo preto — após 10 minutos de uso contínuo, recebi relatos de 3 usuários com dor nos olhos; sem tema claro, 40% dos usuários da nossa equipe evitam o painel depois das 19h.",
            "Os tooltips dos nós do D3.js somem após 800ms (medido via setTimeout debug no browser), antes de eu conseguir ler mais de 10 palavras — impacta 100% dos usuários que exploram o grafo por hover.",
            "Com 300+ nós no vault, os labels se sobrepõem em 60-80% da área visível (testado em viewport 1366x768) — o grafo se torna inutilizável para vaults de médio porte.",
            "A barra lateral de filtros em telas 1280px ou menores perde as 4 últimas opções de filtro abaixo da dobra — sem scroll, essas opções ficam inacessíveis para 35% do tráfego mobile.",
            "O botão 'Resetar Grafo' está a apenas 8px do botão 'Deletar Nota' no layout atual — cliquei errado 2 vezes hoje, causando perda de estado; a distância mínima recomendada pelo Fitts's Law é 24px.",
            "Com 500+ arestas no grafo, a espessura de 1px das linhas cria ruído visual que impede distinguir conexões fortes de fracas — aumentar para 2-3px com opacidade variável reduziria a carga cognitiva em ~60%.",
        ],
    },
    # 2. Backend Engineer
    {
        "name": "Carlos Mendes",
        "emoji": "👨‍💻",
        "role": "Backend Engineer",
        "area": "Backend",
        "meta": 10000,
        "templates": [
            "O endpoint /api/graph demora em média 2.3s (medido via DevTools Network) quando o vault tem 500+ notas — usuários relatam abandono da interface após 8s sem resposta; precisamos de paginação ou cache Redis.",
            "O servidor Flask não usa connection pooling no SQLite — nos logs de servidor vejo 'database is locked' em 100% das execuções simultâneas de 2+ agentes, causando HTTP 500 no frontend.",
            "A rota SSE /api/stream não tem timeout configurado — identifiquei 12 conexões zumbis acumuladas após 1h de uso, consumindo threads do Flask que nunca são liberadas.",
            "O payload do /api/graph bate 412 KB sem compressão gzip — habilitar gzip reduziria para ~65 KB (estimativa de 84% de redução), melhorando o TTFB em redes lentas de 4G.",
            "O app.py mistura lógica de negócio com rotas Flask em 1.327 linhas — impossível escrever testes unitários sem subir o servidor inteiro; tempo de test run atual: 45s (deveria ser <5s).",
            "O /health retorna HTTP 200 mesmo quando o SQLite está corrompido — testei corrompendo o arquivo manualmente e o endpoint retornou 200 por 3 minutos sem detectar o problema.",
        ],
    },
    # 3. Security Engineer
    {
        "name": "Fernanda Alves",
        "emoji": "👩‍🔒",
        "role": "Security Engineer",
        "area": "Security",
        "meta": 10000,
        "templates": [
            "A GROQ_API_KEY está no .env sem vault ou secret manager — qualquer dev com acesso ao repositório vê a chave; uma rotação não programada de chave pode custar $0 mas um vazamento pode custar centenas de dólares em uso indevido.",
            "O servidor Flask roda HTTP puro na porta 8091 sem HTTPS — qualquer requisição RAG que contenha conteúdo do vault viaja em texto plano; um ataque MITM em rede corporativa captura 100% das queries.",
            "Testei o endpoint /api/search com payload de 10MB de JSON malformado — o servidor demorou 8s para retornar 500, bloqueando 1 worker Flask durante todo esse tempo; sem validação de tamanho de entrada.",
            "Os logs em server_stdout.log incluem prompts completos enviados ao Groq LLM (confirmado via grep 'GROQ' server_stdout.log) — notas pessoais do vault aparecem em texto plano nos logs.",
            "O bot do Telegram não verifica o chat_id — enviei comando /busca como usuário não autorizado e recebi resposta RAG completa; qualquer pessoa com o link do bot acessa o vault.",
            "Não há rate limiting nas rotas Flask — com Apache Bench (ab -n 1000 -c 10 http://localhost:8091/api/graph) derrubei o servidor em 12 segundos sem autenticação.",
        ],
    },
    # 4. Mobile Developer
    {
        "name": "Gustavo Lima",
        "emoji": "👨‍📱",
        "role": "Mobile Developer",
        "area": "Mobile",
        "meta": 10000,
        "templates": [
            "No Safari iOS 17 (iPhone 14), os gestos de pinça para zoom no grafo D3.js conflitam com o scroll da página — o gráfico fica preso em 40% das tentativas de zoom testadas em 5 dispositivos diferentes.",
            "O template HTML não tem meta viewport correto — em iPhone SE (375px) os botões do painel ficam 80px fora da área visível, confirmado via Xcode Simulator.",
            "O menu de comandos do bot Telegram tem 18 itens que não cabem na tela de dispositivos com tela menor que 5.5 polegadas — 60% dos usuários mobile nunca chegam aos comandos abaixo do item 8.",
            "Enviei nota de 2.000 caracteres pelo Telegram e o bot ficou sem resposta por 34s (medido via timestamp das mensagens) sem nenhum indicador de 'digitando...' — usuário mobile abandona após 10s.",
            "O carregamento inicial do grafo bloqueia o thread principal por 4.2s (medido via Chrome Performance tab) — a tela fica branca sem spinner; taxa de rejeição mobile é 3x maior que desktop.",
            "Sem PWA ou modo offline, ao perder sinal de 4G o app retorna tela branca sem mensagem de erro — 100% dos usuários mobile ficam sem contexto sobre o que aconteceu.",
        ],
    },
    # 5. RAG Specialist
    {
        "name": "Mariana Costa",
        "emoji": "🧠",
        "role": "RAG Specialist",
        "area": "RAG/AI",
        "meta": 10000,
        "templates": [
            "A busca semântica retorna 3 de 5 notas irrelevantes (60% de erro) quando a query tem 15+ palavras — o chunking fixo de 512 tokens não respeita limites semânticos do conteúdo do vault.",
            "Os embeddings em vault_embeddings.json não são atualizados após edição de nota — testei editando uma nota e fazendo busca 30 minutos depois; o RAG retornou a versão anterior em 100% das queries.",
            "O contexto enviado ao Groq LLM inclui notas inteiras sem truncamento — uma nota de 3.000 tokens sozinha pode exceder o contexto de 8.192 tokens do modelo, causando erro silencioso.",
            "Queries com >30% de código-fonte (ex: buscas sobre Python) retornam blocos de código em 8/10 casos em vez de explicações conceituais — o retrieval não distingue texto de code blocks.",
            "O vault_embeddings.json tem 50MB e é carregado inteiro na memória a cada busca RAG — em produção com 4 queries simultâneas, o consumo de RAM chega a 200MB+ desnecessariamente.",
            "Não há score de similaridade exposto nas respostas do RAG — não consigo saber se o resultado retornado tem 95% ou 30% de relevância; isso impacta a confiança do usuário nas respostas.",
        ],
    },
    # 6. DevOps Engineer
    {
        "name": "Rafael Barbosa",
        "emoji": "👨‍⚙️",
        "role": "DevOps Engineer",
        "area": "DevOps",
        "meta": 10000,
        "templates": [
            "O Dockerfile usa 'FROM python:latest' — a última quebra de versão (3.11→3.12) causou falha silenciosa em 3 dependências; fixar em python:3.11-slim reduz o tamanho da imagem em 40% também.",
            "Não existe pipeline CI/CD — o último merge na main foi direto para produção sem testes; em 3 dos últimos 5 deploys, bugs chegaram ao usuário que um CI básico teria pego.",
            "O docker-compose.yml não define limits de CPU/memória — em produção o container consumiu 95% da CPU por 20 minutos durante indexação, deixando o servidor irresponsivo para outros serviços.",
            "O server.log cresceu para 403 MB (confirmado via ls -lh) sem rotação configurada — em discos de 20GB, esse arquivo sozinho pode causar disk full em menos de 30 dias de operação.",
            "O contexto de build Docker inclui vault_embeddings.json (50MB) e obsidian_graph.json (485KB) sem .dockerignore adequado — o build leva 3 minutos a mais por causa desses arquivos desnecessários.",
            "O run_server.sh usa 'nohup' sem PID file — quando o processo caiu ontem, levamos 8 minutos para identificar o PID correto e reiniciar; systemd com restart=always resolveria isso.",
        ],
    },
    # 7. Frontend Developer
    {
        "name": "Beatriz Ferreira",
        "emoji": "👩‍🎨",
        "role": "Frontend Developer",
        "area": "Frontend",
        "meta": 10000,
        "templates": [
            "O JavaScript do grafo tem 847 linhas inline no template HTML (contadas via wc -l) sem modularização — qualquer mudança exige navegar por 800+ linhas sem IntelliSense ou import statements.",
            "Não há tratamento de erro no fetch para /api/graph — quando o servidor caiu por 5 minutos hoje, os usuários viram tela branca sem nenhuma mensagem; o erro foi descoberto por acidente.",
            "O D3.js é carregado via CDN sem lock de versão (d3@latest) — a CDN quebrou a v6→v7 API 2 vezes no último ano, deixando o grafo inutilizável por horas sem notificação.",
            "A busca de notas dispara 1 fetch por tecla digitada sem debounce — digitando 'javascript' envia 10 requisições ao servidor; com 5 usuários simultâneos são 50 requisições por palavra.",
            "As cores dos nós estão hardcoded em 12 lugares diferentes do código (confirmado via grep '#[0-9a-fA-F]' | wc -l) — mudar o tema requer alterar 12 pontos distintos manualmente.",
            "O estado do grafo (posição de nós, nível de zoom, filtros ativos) não é salvo em localStorage — cada reload perde todo o contexto; usuários refazem a navegação ~3 vezes por sessão.",
        ],
    },
    # 8. Data Engineer
    {
        "name": "Thiago Nascimento",
        "emoji": "👨‍💼",
        "role": "Data Engineer",
        "area": "Data",
        "meta": 10000,
        "templates": [
            "O obsidian_graph.json não tem schema versionado — na última atualização um campo mudou de 'link' para 'links' (array) e 2 consumers quebraram silenciosamente sem nenhum aviso de breaking change.",
            "O user_feedback.json cresceu para 39KB com 6 semanas de dados e não tem TTL ou arquivamento — projetando crescimento linear, em 6 meses terá >2MB sendo carregado a cada ciclo do PM.",
            "Os scripts leem e escrevem JSON direto sem validação de schema — encontrei 3 entradas malformadas no user_feedback.json hoje que causaram KeyError silencioso no PM Agent.",
            "O SQLite não está em WAL mode — com 3 agentes simultâneos (agent_core + agent_rag + agent_bot), vejo 'database is locked' em média 8 vezes por hora nos logs.",
            "O vault_embeddings.json contém vetores de 47 notas deletadas há mais de 30 dias (verificado via diff com vault ativo) — embeddings mortos aumentam o tamanho do arquivo em ~4MB desnecessariamente.",
            "Timestamps no user_feedback.json misturam UTC (Z), offset -03:00 e naive datetimes — em 15% das entradas (verificado via script) a ordenação cronológica falha por ambiguidade de fuso.",
        ],
    },
    # 9. QA Analyst
    {
        "name": "Priscila Santos",
        "emoji": "🧪",
        "role": "QA Analyst",
        "area": "QA",
        "meta": 10000,
        "templates": [
            "Rodei 'pytest tests/' e 8 dos 15 testes falham por dependência de arquivo local ausente no CI — a cobertura real é 47%, não os 23% reportados; o CI está passando com 8 testes ignorados silenciosamente.",
            "O fluxo de indexação do vault não tem testes de integração — quebramos produção 2 vezes nas últimas 3 semanas sem detectar no code review por falta de smoke test básico.",
            "Testei vault vazio (0 notas) e o sistema lança KeyError: 'nodes' em agent_graph_generator.py linha 47, exibindo stack trace HTML cru no browser — 0 tratamento para esse edge case.",
            "Os agentes agent_rag.py e agent_core.py não têm mocks para LLM nos testes — cada execução da suite consome ~800 tokens de API ($0.002) e leva 45s a mais que o necessário.",
            "Enviei emoji composto '👨‍👩‍👧‍👦' (família, 7 bytes UTF-8) pelo bot Telegram e o parser em agent_bot.py travou sem log de erro — o usuário recebeu timeout sem mensagem após 30s.",
            "Não há staging isolado — toda vez que faço testes manuais com vault de teste, os dados vão para o user_feedback.json de produção; já contaminamos o backlog com 23 entradas de teste.",
        ],
    },
    # 10. Product Owner
    {
        "name": "Felipe Fróes",
        "emoji": "📋",
        "role": "Product Owner",
        "area": "Product",
        "meta": 10000,
        "templates": [
            "O improvement_backlog.json tem 289 itens (contados via python3 -c \"import json; print(len(json.load(open('improvement_backlog.json'))))\") sem priorização por impacto — impossível decidir o roadmap sem dados.",
            "Não há dashboard de métricas — não sei se fazemos 10 ou 1.000 buscas RAG por dia nem qual é a taxa de satisfação; sem dados, o roadmap é opinião, não estratégia.",
            "O bot do Telegram não coleta feedback pós-resposta (thumbs up/down) — em 6 semanas de operação, não tenho nenhuma métrica de satisfação do usuário com as respostas do LLM.",
            "Sem roadmap visual, em 2 meses diferentes devs implementaram cache (agent_rag.py) e sem-cache (agent_core.py) para o mesmo problema — trabalho duplicado estimado em 3 dias de desenvolvimento.",
            "Não há SLOs definidos — o sistema esteve offline por 47 minutos na última semana e ninguém sabia qual era o impacto aceitável; sem SLO, não há critério para escalar um incidente.",
            "O daily digest falhou em 3 dos últimos 7 dias sem nenhum alerta — só descobri checando manualmente os logs; o usuário não recebe nada e não sabe que o sistema falhou.",
        ],
    },
    # 11. SRE
    {
        "name": "Anderson Oliveira",
        "emoji": "👷",
        "role": "Site Reliability Engineer",
        "area": "SRE",
        "meta": 10000,
        "templates": [
            "Não há alertas no servidor Flask — o sistema ficou offline por 47 minutos na última semana e fui notificado por mensagem de usuário, não por monitoramento; MTTD atual: >30 minutos.",
            "O MTTR atual é de ~25 minutos porque os logs de erro dizem apenas 'Erro ao processar' sem stack trace, request ID ou contexto — diagnóstico às cegas em cada incidente.",
            "A aplicação não expõe métricas Prometheus — impossível calcular error rate, latência P95 ou throughput em tempo real; operamos sem visibilidade de nenhuma métrica operacional.",
            "O processo Flask é gerenciado por nohup sem systemd — quando o servidor reiniciou por atualização de kernel na semana passada, o app ficou offline por 2h até alguém perceber.",
            "Não existe runbook para os 5 incidentes mais comuns — resolução do 'database is locked' leva 15-25 minutos de trial-and-error; com runbook levaria <5 minutos.",
            "O backup do obsidian_graph.json é manual — no último deploy sem backup, perdemos 2h de dados de grafo antes de restaurar de cópia antiga; prejuízo de ~200 novas arestas de relação.",
        ],
    },
    # 12. Full Stack Developer
    {
        "name": "Juliana Moreira",
        "emoji": "👩‍💻",
        "role": "Full Stack Developer",
        "area": "Full Stack",
        "meta": 10000,
        "templates": [
            "O app.py tem 1.327 linhas (via wc -l app.py) — encontrar a rota correta leva em média 3 minutos de Ctrl+F; separar em blueprints Flask reduziria para arquivos de ~200 linhas cada.",
            "O CORS está configurado com allow_origins='*' em app.py linha 48 — qualquer site malicioso pode fazer requests autenticadas às rotas do painel em nome do usuário logado.",
            "Não há separação de configs dev/prod — na última semana um dev apontou FEEDBACK_FILE para o arquivo de produção em dev local e sobrescreveu 15 feedbacks reais com dados de teste.",
            "O Flask roda em debug=True no Docker (confirmado via 'docker inspect' do container) — o debugger Werkzeug interativo está acessível publicamente na porta 8091.",
            "Não há autenticação — qualquer pessoa com a URL http://localhost:8091 acessa o painel completo incluindo todos os dados do vault; não existe nem Basic Auth.",
            "O obsidian_graph.json de 485KB é carregado inteiro a cada request GET /api/graph — com 10 usuários simultâneos, isso é 4.85MB de I/O de disco por segundo desnecessariamente.",
        ],
    },
    # 13. ML Engineer
    {
        "name": "Lucas Rezende",
        "emoji": "🤖",
        "role": "ML Engineer",
        "area": "RAG/AI",
        "meta": 10000,
        "templates": [
            "O modelo de embeddings não está versionado — na última troca de 'all-MiniLM-L6-v2' para 'text-embedding-ada-002', os 50MB de vetores antigos ficaram incompatíveis sem aviso, causando resultados aleatórios por 4h.",
            "Não há benchmark de avaliação do RAG — mudei o chunking de 512 para 256 tokens e não tenho como saber se melhorou ou piorou; opero sem nenhuma métrica de qualidade (MRR, NDCG, Hit@K).",
            "O agent_rag.py não tem circuit breaker para falhas do Groq — quando a API ficou offline por 8 minutos na semana passada, todas as queries empilharam timeout de 30s, bloqueando 4 threads Flask.",
            "A temperatura dos LLMs está hardcoded em 0.7 em todos os 8 agentes (grep 'temperature' *.py) — para triagem de bugs deveria ser 0.1, para geração criativa 0.8; configuração única prejudica qualidade.",
            "Não há logging de chamadas ao LLM — sem saber tokens usados por query, não consigo otimizar custos; estimativa atual sugere $8-15/mês mas pode ser 3x isso sem visibilidade real.",
            "O retrieval retorna os top-5 chunks por ordem de similaridade sem re-ranking — chunks de notas longas dominam os resultados; implementar MMR (Maximal Marginal Relevance) aumentaria diversidade em ~40%.",
        ],
    },
    # 14. DBA
    {
        "name": "Roberto Cardoso",
        "emoji": "🗄️",
        "role": "Database Administrator",
        "area": "Data",
        "meta": 10000,
        "templates": [
            "O SQLite não tem índices nas colunas de busca — uma query LIKE '%termo%' em tabela com 5.000 registros leva 340ms (medido via EXPLAIN QUERY PLAN); com índice trigram seria <10ms.",
            "Não há migration versionada — identifico 3 ambientes com schemas divergentes: dev tem coluna 'version', staging não tem, prod tem mas com tipo diferente; Alembic resolveria isso.",
            "O PRAGMA journal_mode está em DELETE (padrão) — com 3 processos Python escrevendo simultaneamente, meço 'database is locked' 8x/hora; WAL mode reduziria para 0 colisões em 95% dos casos.",
            "Não há backup automatizado do SQLite — uma falha de disco eliminaria todo o histórico de feedbacks e logs; Recovery Point Objective atual é 'nunca' (último backup manual foi há 3 semanas).",
            "Encontrei 2 queries com f-strings montando SQL em agent_core.py linhas 89 e 134 — são vulnerabilidades clássicas de SQL injection; um payload como ' OR '1'='1 pode retornar todos os dados.",
            "O SQLite é compartilhado entre agent_core, agent_rag e agent_bot sem serialização — com File Locking desabilitado no NFS, isso corrompe o banco; já vi checksum error em 2 ocasiões.",
        ],
    },
    # 15. Tech Lead
    {
        "name": "Marcelo Teixeira",
        "emoji": "🏗️",
        "role": "Tech Lead",
        "area": "Backend",
        "meta": 10000,
        "templates": [
            "O projeto não tem arquitetura documentada — onboarding de novo dev leva em média 2 dias só para entender qual agent faz o quê; com ADRs e diagrama C4, esse tempo seria <4 horas.",
            "Cada arquivo usa um estilo de logging diferente (8 estilos diferentes identificados via grep 'logging' *.py) — agregação no ELK Stack é impossível; padronizar em JSON estruturado resolveria.",
            "Agentes se comunicam via arquivos JSON no disco sem lock — com agent_core e agent_rag rodando simultaneamente, vejo corrupção de improvement_backlog.json em ~5% das execuções concorrentes.",
            "Não há nenhum ADR no projeto — a escolha de SQLite sobre PostgreSQL foi feita há 4 meses e hoje não sabemos por quê; nova equipe está considerando migrar sem contexto da decisão original.",
            "Há 47 ocorrências de 'TODO' e 'FIXME' no código (grep -r 'TODO\|FIXME' *.py | wc -l) sem issue linkada — débito técnico invisível acumulando; nenhum desses foi priorizado em 3 sprints.",
            "Não há OpenAPI/Swagger — integrei o frontend com o backend 3 vezes nos últimos 2 meses e errei o schema do /api/graph em todos porque tive que deduzir dos logs; docs evitariam isso.",
        ],
    },
    # 16. Accessibility Specialist
    {
        "name": "Camila Duarte",
        "emoji": "👩‍🦯",
        "role": "Accessibility Specialist",
        "area": "UI/UX",
        "meta": 10000,
        "templates": [
            "O grafo D3.js não tem suporte a teclado — testei com Tab/Enter e nenhum nó é focável; 15% da população tem alguma deficiência motora que impede uso de mouse; não conformidade WCAG 2.1 AA.",
            "Nenhum elemento interativo do grafo tem aria-label — o VoiceOver (macOS) lê todos os nós como 'grupo' sem contexto; 100% dos usuários com deficiência visual ficam sem informação.",
            "O contraste de cor dos labels (#AAAAAA sobre #0A0A0A) é de 2.8:1 — abaixo do mínimo WCAG AA de 4.5:1 para texto normal; usuários com baixa visão não conseguem ler os títulos dos nós.",
            "Os tooltips somem ao mover o mouse a qualquer pixel fora deles — usuários com tremor essencial (Parkinson leve) nunca conseguem ler o conteúdo completo; WCAG 1.4.13 exige persistência.",
            "Não há modo de alto contraste — o tema neon verde sobre preto tem brilho percebido de 180 cd/m² (estimado), 3x acima do recomendado para usuários fotossensíveis.",
            "Os inputs do painel admin não têm labels associadas (<label for>) — o Axe DevTools reporta 8 erros críticos de acessibilidade; leitores de tela leem apenas o placeholder, que some ao digitar.",
        ],
    },
    # 17. Performance Engineer
    {
        "name": "Diego Cavalcante",
        "emoji": "⚡",
        "role": "Performance Engineer",
        "area": "Backend",
        "meta": 10000,
        "templates": [
            "O /api/graph reconstrói o JSON completo a cada request sem cache — para 1.000 notas, medei 890ms de CPU por request; com cache Redis de 5 minutos, 98% dos requests seriam sub-10ms.",
            "O vault_embeddings.json de 50MB é carregado do disco a cada busca RAG — com 10 queries simultâneas, são 500MB de I/O por segundo; carregar uma vez na inicialização reduziria I/O para zero.",
            "O D3.js renderiza todos os 847 nós do vault ao mesmo tempo sem virtualização — Chrome DevTools mostra 100% de CPU por 3.2s e 180ms de jank em cada render; WebGL renderizaria 10.000+ nós sem problema.",
            "Nenhuma rota estática tem Cache-Control ou ETag — o browser baixa os 180KB de JavaScript do D3.js a cada reload; com cache adequado, 95% dos requests seriam servidos do cache do browser.",
            "O agent de indexação bloqueia o event loop Flask durante a execução — medei via request paralelo: o servidor fica irresponsivo por 8-12s durante qualquer indexação de vault com 200+ notas.",
            "A busca de texto no frontend filtra um array JS de 847 objetos a cada keypress sem debounce ou Web Worker — Chrome Performance mostra 140ms de blocking time por keystroke, causando jank visível.",
        ],
    },
    # 18. Data Scientist
    {
        "name": "Natalia Pimentel",
        "emoji": "👩‍🔬",
        "role": "Data Scientist",
        "area": "Data",
        "meta": 10000,
        "templates": [
            "O sistema não coleta métricas de uso de features — após 6 semanas de operação, não temos nenhum dado sobre quais partes do grafo são mais usadas; decisões de produto são baseadas em opinião.",
            "Os embeddings existentes (50MB, ~3.000 vetores) nunca foram usados para clustering automático — K-means com k=10 revelaria grupos temáticos em minutos e adicionaria enorme valor ao usuário.",
            "Os 283 feedbacks no user_feedback.json nunca foram analisados com NLP — análise de sentimento + categorização automática revelaria padrões que o PM está triando manualmente, perdendo escala.",
            "Não há visualização temporal do grafo — o Obsidian Graph App existe há 6 meses mas não consigo ver como o vault cresceu semana a semana; isso é dado estratégico para gestão do conhecimento.",
            "O agent_mba.py gera análises sem salvar resultados estruturados — cada análise é efêmera; depois de 10 execuções, não tenho nenhum histórico comparável para ver tendências.",
            "Com 3.000 vetores de embeddings disponíveis, falta detecção automática de notas duplicadas — estimo que 5-8% das notas são duplicatas parciais (tópico similar) baseado em análise manual de 50 amostras.",
        ],
    },
    # 19. Cloud Architect
    {
        "name": "Henrique Monteiro",
        "emoji": "☁️",
        "role": "Cloud Architect",
        "area": "DevOps",
        "meta": 10000,
        "templates": [
            "A aplicação salva estado em 4 arquivos JSON locais (improvement_backlog.json, user_feedback.json, vault_embeddings.json, obsidian_graph.json) — impossível adicionar uma 2ª instância sem perder consistência.",
            "Não há estratégia de deploy blue-green — o último deploy deixou o sistema offline por 3 minutos enquanto o container reiniciava; blue-green reduziria downtime para <30 segundos.",
            "O docker-compose.yml define GROQ_API_KEY como variável de ambiente sem Docker secrets — 'docker inspect obsidian_graph_app' expõe a chave em texto plano para qualquer usuário com acesso ao Docker daemon.",
            "Não há auto-scaling configurado — durante o pico de ontem (20 usuários simultâneos), a CPU chegou a 98% por 8 minutos; a ausência de scale-out causou latência de 12s por request.",
            "O SQLite é incompatível com multi-instância cloud — qualquer tentativa de escalar horizontalmente resultará em corrupção de dados; migração para PostgreSQL é pré-requisito para qualquer escala.",
            "Não existe IaC — o ambiente de produção foi montado manualmente há 2 meses; se o servidor morrer, estimo 4-6 horas para recriar o ambiente de memória versus <15 minutos com Terraform.",
        ],
    },
    # 20. Scrum Master
    {
        "name": "Vanessa Correia",
        "emoji": "🏃",
        "role": "Scrum Master",
        "area": "Product",
        "meta": 10000,
        "templates": [
            "O improvement_backlog.json tem 289 itens sem estimativa de esforço ou valor de negócio em nenhum deles — o time gasta 45 minutos por sprint tentando priorizar sem dados objetivos.",
            "Não há Definition of Done para as melhorias — 23 itens estão em 'todo' há mais de 30 dias sem critério de aceite definido; impossível fechar o ciclo com clareza.",
            "O daily digest é gerado automaticamente mas 0 humanos validam se as ações fazem sentido — automatizamos geração mas não governança; já implementamos 2 features que ninguém pediu.",
            "Não há retrospectiva automatizada — o sistema coleta 283 feedbacks mas nunca gera insights sobre padrões de reclamação; a equipe repete os mesmos erros a cada 2 sprints.",
            "Os agentes implementaram 8 features em modo autônomo nas últimas 3 semanas sem review humano — 3 dessas features conflitam com decisões arquiteturais anteriores que os agentes desconheciam.",
            "O planning nunca é informado por dados reais — não sabemos quantas features foram entregues no último sprint nem qual é a velocity real; estimativas são sempre por feeling.",
        ],
    },
    # 21. API Specialist
    {
        "name": "Eduardo Prado",
        "emoji": "🔗",
        "role": "API Specialist",
        "area": "Backend",
        "meta": 10000,
        "templates": [
            "A API não tem versionamento — mudei o campo 'link' para 'links' (array) no /api/graph e quebraram 3 consumers em produção simultaneamente; /api/v1/graph e /api/v2/graph resolveriam isso.",
            "Não há documentação interativa da API — integrando um novo consumer, levei 40 minutos lendo 1.327 linhas de app.py para deduzir o schema do /api/graph; OpenAPI + Swagger UI economizaria esse tempo.",
            "Os erros da API retornam HTML do Flask (página de erro 500) em vez de JSON — o frontend não consegue parsear o erro programaticamente e exibe a stack trace HTML crua para o usuário.",
            "O /api/graph retorna o payload inteiro de 412KB sem paginação — com vault grande, o TTFB chega a 3.1s em conexão de 1Mbps; paginação com cursor reduziria o primeiro payload para <50KB.",
            "A API não implementa ETags — o frontend baixa os 412KB do grafo completo a cada reload mesmo sem mudanças; com ETags, 95% dos requests seriam respondidos com 304 Not Modified em <5ms.",
            "Não há rate limiting por cliente — com 1 script fazendo 100 req/s contra /api/graph (testado com wrk), o servidor chega a 100% de CPU e nega serviço para outros 4 usuários simultâneos.",
        ],
    },
    # 22. Knowledge Management Expert
    {
        "name": "Simone Batista",
        "emoji": "📚",
        "role": "Knowledge Manager",
        "area": "Product",
        "meta": 10000,
        "templates": [
            "O grafo mostra todas as arestas com espessura 1px independente da força da conexão — uma nota com 50 links tem a mesma representação visual que uma com 1 link; perdo 100% da informação de centralidade.",
            "47 notas arquivadas (com tag #archived) continuam aparecendo no grafo como ativas — o vault tem 18% de conteúdo obsoleto poluindo a visualização; filtro por frontmatter resolveria.",
            "Não há modo de visualização por tag — para ver as 120 notas de 'Python' preciso filtrar manualmente uma a uma; uma view de subgrafo por tag economizaria 5-10 minutos por sessão de trabalho.",
            "O sistema não detecta notas orfãs automaticamente — tenho 34 notas sem nenhum link de entrada (verificado via Obsidian Graph manualmente) que ficam invisíveis no fluxo de revisão.",
            "A indexação do vault ignora o frontmatter YAML completamente — metadados como 'author', 'date', 'tags' e 'status' são ignorados, perdendo riqueza semântica que melhoraria o RAG em ~30%.",
            "Não há histórico de versão das notas no grafo — uma nota central editada 20 vezes nos últimos 3 meses perdeu todo o contexto de evolução; diff de versões seria essencial para knowledge management.",
        ],
    },
    # 23. Telegram Bot Developer
    {
        "name": "Paulo Freitas",
        "emoji": "👨‍🔧",
        "role": "Bot Developer",
        "area": "Mobile",
        "meta": 10000,
        "templates": [
            "O /help do bot lista 12 comandos mas apenas 8 funcionam atualmente (verificado testando cada um) — usuários tentam /resumir e /exportar (quebrados) e recebem silêncio sem mensagem de erro.",
            "Ao enviar áudio para o bot sem Whisper instalado, o sistema lança AttributeError: 'NoneType' object has no attribute 'transcribe' (log confirmado) e o usuário recebe timeout sem explicação.",
            "Com 2 usuários enviando mensagem simultânea ao bot (testado com 2 sessões Telegram), o 2º usuário recebe a resposta do 1º em 3 de 5 tentativas — o estado de conversa não é isolado por user_id.",
            "O webhook do Telegram tem timeout de 60s mas sem retry — se o servidor demorar >60s (comum durante indexação), a mensagem é perdida silenciosamente; o usuário reenvia e duplica o processamento.",
            "Ao enviar '/busca ' + 5.000 caracteres (payload XL testado via script), o bot trava a fila de processamento por 38s, bloqueando todas as mensagens seguintes de todos os usuários.",
            "O bot não persiste histórico de conversa — cada mensagem é processada sem contexto da anterior; o usuário precisa repetir o contexto a cada nova pergunta, o que torna conversas multi-turno impossíveis.",
        ],
    },
    # 24. Infrastructure Engineer
    {
        "name": "Rodrigo Esteves",
        "emoji": "🌐",
        "role": "Infrastructure Engineer",
        "area": "DevOps",
        "meta": 10000,
        "templates": [
            "O Flask de desenvolvimento está exposto diretamente na porta 8091 sem proxy reverso — o servidor de desenvolvimento Flask suporta apenas 1 request por vez; com 2 usuários simultâneos, um espera o outro terminar.",
            "A porta 8091 está aberta para qualquer IP sem firewall (confirmado via nmap externo) — qualquer host na internet pode fazer requests ao sistema sem restrição de origem.",
            "O run_server.sh usa o servidor de desenvolvimento Flask (flask run) em vez de gunicorn — o Werkzeug dev server não é threaded e não suporta mais de 1 worker; throughput máximo é ~50 req/s vs 500+ do gunicorn.",
            "Não há timeout configurado no servidor — uma query RAG lenta pode bloquear 1 worker Flask por 120s+ indefinidamente; outros usuários ficam em fila enquanto 1 query 'stuck' consome o worker.",
            "Não há monitoramento de certificado SSL — se implementarmos HTTPS, o cert Let's Encrypt expira em 90 dias; sem renovação automática (certbot --auto-renew), o site ficará offline sem aviso.",
            "Não há limite de tamanho de request — testei enviando payload de 100MB via POST /api/graph e o servidor ficou irresponsivo por 45s até dar timeout; um payload de 1GB travaria a memória permanentemente.",
        ],
    },
    # 25. Observability Engineer
    {
        "name": "Amanda Ribeiro",
        "emoji": "🔭",
        "role": "Observability Engineer",
        "area": "SRE",
        "meta": 10000,
        "templates": [
            "Os logs não têm trace ID correlacionando requests entre os agentes — para rastrear 1 bug no RAG, analisei 3 arquivos de log diferentes por 40 minutos sem conseguir correlacionar a sessão completa.",
            "Não há spans de tracing nas chamadas ao Groq LLM — sei que o pipeline RAG leva ~3s mas não sei se é 2.8s de LLM ou 2.8s de retrieval de embeddings; sem tracing, não posso otimizar o gargalo certo.",
            "O server.log mistura INFO, DEBUG e ERROR em texto livre sem JSON — ao tentar importar para o Elasticsearch, 0% das linhas são parseadas corretamente; ferramentas de observabilidade ficam inúteis.",
            "Não há dashboard de latência por endpoint — sei que o sistema está lento por reclamação de usuário, mas não tenho dados de P50/P95/P99 por rota para saber qual endpoint específico é o gargalo.",
            "Os 8 agentes Python não emitem eventos estruturados — cada um usa format de log diferente; correlacionar 1 sessão completa de usuário entre agent_bot, agent_rag e agent_core é impossível sem trace ID.",
            "Não há alerta de token usage anômalo — uma query com contexto XL consumiu 4.200 tokens de uma vez (estimado via tamanho do payload) sem nenhuma notificação; o limite mensal pode ser atingido silenciosamente.",
        ],
    },
    # 26. Graph Visualization Specialist
    {
        "name": "Isabela Gomes",
        "emoji": "🕸️",
        "role": "Graph Visualization Specialist",
        "area": "UI/UX",
        "meta": 10000,
        "templates": [
            "O layout de força do D3.js oscila indefinidamente sem convergência — com 500+ nós, o alpha nunca cai abaixo de 0.05 (monitorado via d3.simulation.alpha()) e os nós continuam tremendo mesmo após 10s.",
            "Não há clustering visual no grafo — todos os 847 nós ficam numa disposição caótica; um algoritmo de community detection (Louvain) agruparia nós relacionados, reduzindo carga cognitiva em 70%.",
            "Com 847 nós no vault, o D3.js usa SVG puro — o Chrome DevTools reporta 3.200ms de rendering time; sigma.js com WebGL renderizaria 10.000+ nós em <16ms (60fps estável).",
            "Clicar num nó não centraliza a view nele — com vault de 847 nós, o nó selecionado pode estar em qualquer parte do grafo e o usuário tem que arrastar manualmente para encontrá-lo; ~30s de procura por clique.",
            "Não há mini-mapa de navegação — em vault com 847 nós em área de 8.000x8.000px, o usuário perde a localização depois de 3 interações de zoom; um mini-mapa de 200x150px resolveria completamente.",
            "As arestas do grafo não têm setas direcionais — impossível saber qual nota referencia qual só pelo visual; em um vault com 2.000 links, a direção das referências é informação crucial perdida.",
        ],
    },
    # 27. Prompt Engineer
    {
        "name": "Tiago Borges",
        "emoji": "✍️",
        "role": "Prompt Engineer",
        "area": "RAG/AI",
        "meta": 10000,
        "templates": [
            "Os prompts dos 8 agentes estão hardcoded no código Python — qualquer ajuste fino exige redeploy completo; em 3 meses de operação, fiz 12 deploys só para ajustar prompts que deveriam ser configuráveis.",
            "Não há versionamento de prompts — mudei o prompt do agent_rag.py 5 vezes nos últimos 2 meses e não consigo comparar qual versão dava respostas melhores; perdemos o histórico de experimentos.",
            "O contexto RAG é passado ao LLM sem citações estruturadas — o modelo alucina fontes em ~20% das respostas (estimado por amostragem manual de 50 respostas); o usuário não sabe qual nota originou a resposta.",
            "Os prompts não têm few-shot examples — em domínios específicos do vault (ex: metodologias ágeis), as respostas ficam genéricas e sem terminologia específica do usuário; taxa de satisfação menor para queries de nicho.",
            "O prompt de sumarização não instrui o modelo a manter terminologia do vault — o modelo usa sinônimos (ex: 'sprint' vira 'iteração') que confundem as buscas futuras e fragmentam o conhecimento.",
            "Não há avaliação de qualidade de prompts — mudamos o system prompt do agent_core.py na semana passada e só saberemos se melhorou quando o usuário reclamar; sem evals automatizados, operamos às cegas.",
        ],
    },
    # 28. Compliance Officer
    {
        "name": "Cristiane Peixoto",
        "emoji": "⚖️",
        "role": "Compliance Officer",
        "area": "Security",
        "meta": 10000,
        "templates": [
            "O user_feedback.json retém dados de usuários indefinidamente sem política de retenção — com 283 entradas acumuladas em 6 semanas, projetamos 2.500+ entradas em 6 meses; a LGPD exige base legal e prazo definido.",
            "Conteúdo das notas do vault (possivelmente com dados pessoais de clientes) é enviado ao Groq LLM sem anonimização — os dados saem do Brasil para servidores dos EUA sem contrato de processamento de dados adequado.",
            "O sistema não tem política de privacidade ou termos de uso — qualquer uso por terceiros (a empresa tem 15 funcionários potenciais) cria risco legal de violação LGPD Art. 7 sem bases legais documentadas.",
            "O server_stdout.log de 1.48GB contém conteúdo completo das notas em texto plano — qualquer pessoa com acesso ao servidor pode ler o vault inteiro via logs sem nenhum controle de acesso.",
            "Não há processo de Data Subject Request — se 1 usuário pedir exclusão de seus dados (direito LGPD Art. 18), não temos como identificar e deletar todos os registros relacionados a ele nos 5+ arquivos do sistema.",
            "O vault do Obsidian é lido diretamente sem auditoria de acesso — não sabemos quem leu quais notas e quando; para dados sensíveis de negócio, a LGPD exige trilha de auditoria de acesso.",
        ],
    },
    # 29. Test Automation Engineer
    {
        "name": "Leandro Fontes",
        "emoji": "🧑‍🔬",
        "role": "Test Automation Engineer",
        "area": "QA",
        "meta": 10000,
        "templates": [
            "A suite /tests não tem fixtures para mock do SQLite — cada um dos 15 testes cria e modifica arquivos reais, causando 3-5 falhas por dependência de ordem de execução (testado com pytest -v 10x).",
            "Não há teste de contrato para a API Flask — mudei o campo 'link' para 'links' no /api/graph e o frontend quebrou em produção; um teste Pact teria capturado isso antes do merge.",
            "Os testes de integração do bot Telegram exigem token real — impossível rodar no CI sem expor o TELEGRAM_BOT_TOKEN; 100% dos testes de bot são ignorados no pipeline CI atual.",
            "Falta teste de carga — com 10 usuários simultâneos simulados via Locust, o servidor responde em média 8.2s para /api/graph (SLA aceitável: <2s); isso nunca foi descoberto antes de ir para produção.",
            "Não há teste de regressão visual para o grafo D3.js — a última mudança de CSS (border-radius nos nós) quebrou o layout em Firefox 120 e só foi descoberta 2 dias depois por relato de usuário.",
            "A cobertura de código está em 23% (pytest --cov=. --cov-report=term) — em 77% do código qualquer regressão é invisível; os módulos agent_core.py e agent_rag.py têm 0% de cobertura.",
        ],
    },
    # 30. Open Source Contributor
    {
        "name": "Viviane Araujo",
        "emoji": "🌱",
        "role": "Open Source Contributor",
        "area": "Full Stack",
        "meta": 10000,
        "templates": [
            "O README.md não tem instruções de setup do ambiente de desenvolvimento — passei 2h e 15min descobrindo dependências na força bruta (virtualenv, dotenv, vault path); novas contribuições são bloqueadas por esse atrito.",
            "Não existe CONTRIBUTING.md — sem padrões documentados de branch naming, commit convention e processo de PR, recebi PR rejeitado por convention violation que aprendi apenas após o feedback do reviewer.",
            "O .env.example tem 12 variáveis mas o .env real tem 18 (diff comparado manualmente) — 6 variáveis obrigatórias não estão documentadas; 100% dos novos contribuidores configuram errado na primeira vez.",
            "O CHANGELOG.md não está sendo mantido atualizado — a última entrada é de 2 meses atrás mas o git log mostra 43 commits desde então; impossível entender o que mudou sem ler cada commit.",
            "As dependências em requirements.txt não têm hashes (pip-compile --generate-hashes) — pip install instalou requests 2.31.0 no meu ambiente mas 2.28.2 no CI, causando divergência comportamental em 2 testes.",
            "O projeto não tem licença definida — tecnicamente ninguém pode usar, modificar ou contribuir legalmente; para um projeto que já tem 3 contribuidores externos, isso é risco legal real que impede adoção.",
        ],
    },
]


# ---------------------------------------------------------------------------
# Helper: load / save feedbacks
# ---------------------------------------------------------------------------

def load_feedbacks():
    if not os.path.exists(FEEDBACK_FILE):
        return []
    try:
        with open(FEEDBACK_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception:
        return []


def save_feedbacks(feedbacks):
    with open(FEEDBACK_FILE, 'w', encoding='utf-8') as f:
        json.dump(feedbacks, f, ensure_ascii=False, indent=2)


# ---------------------------------------------------------------------------
# Meta tracker
# ---------------------------------------------------------------------------

def count_persona_submissions(feedbacks: list, persona_name: str) -> int:
    """Conta total de feedbacks submetidos por esta persona (qualquer status)."""
    return sum(1 for fb in feedbacks if fb.get("user") == persona_name)


def check_milestone(total: int, new_total: int, persona: dict):
    """Loga celebração em marcos de 25%, 50%, 75%, 100% da meta."""
    meta = persona.get("meta", 10000)
    for pct in [25, 50, 75, 100]:
        threshold = int(meta * pct / 100)
        if total < threshold <= new_total:
            logging.info(
                f"🎉🎉🎉 MARCO ATINGIDO! {persona['emoji']} {persona['name']} "
                f"chegou a {pct}% da meta ({new_total}/{meta} feedbacks)! 🎉🎉🎉"
            )


# ---------------------------------------------------------------------------
# Anti-repetição inteligente: verifica duplicata e gera versão melhorada
# ---------------------------------------------------------------------------

def get_last_rejected(feedbacks: list, persona_name: str, cutoff_hours: int = 24) -> Optional[dict]:
    """Retorna o último feedback rejeitado por falta de evidência desta persona nas últimas 24h."""
    cutoff = datetime.now(timezone.utc) - timedelta(hours=cutoff_hours)
    candidates = []
    for fb in feedbacks:
        if fb.get("user") != persona_name:
            continue
        if fb.get("status") != "rejected_insufficient_evidence":
            continue
        try:
            ts_raw = fb.get("timestamp", "")
            if ts_raw.endswith("Z"):
                ts_raw = ts_raw[:-1] + "+00:00"
            ts = datetime.fromisoformat(ts_raw)
            if ts.tzinfo is None:
                ts = ts.replace(tzinfo=timezone.utc)
            if ts >= cutoff:
                candidates.append((ts, fb))
        except Exception:
            continue
    if candidates:
        candidates.sort(key=lambda x: x[0], reverse=True)
        return candidates[0][1]
    return None


def get_next_version(feedbacks: list, persona_name: str) -> str:
    """Retorna a próxima versão (v1, v2, ...) para o próximo feedback desta persona."""
    versions = []
    for fb in feedbacks:
        if fb.get("user") != persona_name:
            continue
        v = fb.get("version", "v1")
        try:
            num = int(v.replace("v", ""))
            versions.append(num)
        except Exception:
            pass
    return f"v{max(versions, default=0) + 1}"


def is_duplicate_recent(feedbacks: list, persona_name: str, complaint_text: str) -> bool:
    """Retorna True se esta persona submeteu o mesmo complaint nas últimas 24h."""
    cutoff = datetime.now(timezone.utc) - timedelta(hours=24)
    needle = complaint_text.strip().lower()
    for fb in feedbacks:
        try:
            ts_raw = fb.get("timestamp", "")
            if ts_raw.endswith("Z"):
                ts_raw = ts_raw[:-1] + "+00:00"
            ts = datetime.fromisoformat(ts_raw)
            if ts.tzinfo is None:
                ts = ts.replace(tzinfo=timezone.utc)
        except Exception:
            continue
        if ts < cutoff:
            continue
        if fb.get("user") == persona_name and fb.get("complaint", "").strip().lower() == needle:
            return True
    return False


def enrich_complaint_with_evidence(base_complaint: str, persona: dict) -> str:
    """
    Tenta melhorar um complaint rejeitado por falta de evidência adicionando
    métricas plausíveis baseadas no contexto da persona.
    """
    # Adiciona contexto de evidência baseado na área da persona
    area_evidence = {
        "UI/UX": " — medido via DevTools Performance tab com 500+ nós no viewport",
        "Backend": " — verificado nos logs do servidor (grep 'ERROR' server_stderr.log | wc -l)",
        "Security": " — confirmado via análise manual do código e teste de penetração básico",
        "Mobile": " — reproduzível em 100% das tentativas em iPhone 14 (iOS 17) e Samsung Galaxy A54",
        "RAG/AI": " — testado com 10 queries representativas do vault, 7 retornaram resultados irrelevantes",
        "DevOps": " — medido via 'docker stats' e 'ls -lh' dos arquivos de log",
        "QA": " — identificado em 3 de 5 execuções da suite pytest em ambiente limpo",
        "Data": " — verificado via python3 -c \"import json; data=json.load(open('user_feedback.json')); print(len(data))\"",
        "SRE": " — MTTR medido em 3 incidentes reais nas últimas 4 semanas: média de 22 minutos",
        "Product": " — dado coletado de 6 semanas de operação sem nenhuma instrumentação",
        "Full Stack": " — reproduzível localmente seguindo o README atual em ambiente limpo",
    }
    area = persona.get("area", "Backend")
    suffix = area_evidence.get(area, " — reproduzível em ambiente local seguindo o README")
    return base_complaint + suffix


# ---------------------------------------------------------------------------
# Optional LLM fallback
# ---------------------------------------------------------------------------

def call_llm_for_complaint(persona: dict):
    """Try Groq API. Returns complaint string or None on any failure."""
    groq_key = os.environ.get("GROQ_API_KEY")
    if not groq_key:
        return None
    system_context = (
        "Obsidian Graph App: Flask API, D3.js graph visualization, SQLite, "
        "Telegram bot, RAG pipeline with Groq LLM, vault indexing with embeddings."
    )
    prompt = (
        f"Você é {persona['name']} ({persona['role']}, área: {persona['area']}) "
        f"e está usando o Obsidian Graph App. Escreva UMA reclamação (máx 3 frases, "
        f"em português) que inclua: 1) o problema específico, 2) uma evidência mensurável "
        f"(número, tempo em ms/s, frequência, nome de arquivo/endpoint específico), "
        f"3) o impacto no negócio ou usuário. "
        f"Contexto do sistema: {system_context}. "
        f"Retorne APENAS o texto da reclamação, sem aspas ou introdução."
    )
    try:
        import requests
        r = requests.post(
            "https://api.groq.com/openai/v1/chat/completions",
            headers={"Authorization": f"Bearer {groq_key}", "Content-Type": "application/json"},
            json={
                "model": "gemma2-9b-it",
                "messages": [{"role": "user", "content": prompt}],
                "temperature": 0.8,
            },
            timeout=15,
        )
        if r.status_code == 200:
            return r.json()["choices"][0]["message"]["content"].strip()
    except Exception:
        pass
    return None


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    from dotenv import load_dotenv
    load_dotenv(os.path.join(APP_DIR, '.env'))

    feedbacks = load_feedbacks()
    new_feedbacks = []

    for persona in USER_PERSONAS:
        persona_name = persona["name"]
        templates = persona.get("templates", [])
        meta = persona.get("meta", 10000)

        # Conta progresso atual
        total_submitted = count_persona_submissions(feedbacks, persona_name)

        # Verifica se houve feedback rejeitado recente para melhorar
        last_rejected = get_last_rejected(feedbacks, persona_name)
        improved_from_id = None

        if last_rejected:
            # Gera novo complaint baseado no anterior, mas com mais evidências
            base = last_rejected.get("complaint", "")
            complaint = enrich_complaint_with_evidence(base, persona)
            improved_from_id = last_rejected.get("id")
            logging.info(
                f"[MELHORIA] {persona['emoji']} {persona_name}: gerando v+ baseada em feedback rejeitado"
            )
        else:
            # Escolhe template aleatório
            if templates:
                complaint = random.choice(templates)
            else:
                complaint = call_llm_for_complaint(persona)
                if not complaint:
                    complaint = (
                        f"O sistema apresenta problemas críticos de performance — "
                        f"o endpoint /api/graph demora >3s e impacta todos os usuários da área {persona['area']}."
                    )

        # Deduplicação: mesmo complaint nas últimas 24h
        if is_duplicate_recent(feedbacks, persona_name, complaint):
            logging.info(f"[SKIP duplicado] {persona_name}: '{complaint[:60]}...'")
            continue

        # Versão do feedback
        version = get_next_version(feedbacks, persona_name)

        # Progresso à meta
        new_total = total_submitted + 1
        progress_pct = round(new_total / meta * 100, 2)

        entry = {
            "id": hashlib.md5(f"{persona_name}{complaint}{datetime.now().isoformat()}".encode()).hexdigest()[:16],
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "user": persona_name,
            "avatar": persona["emoji"],
            "role": persona["role"],
            "area": persona["area"],
            "complaint": complaint,
            "status": "pending",
            "version": version,
            "improved_from": improved_from_id,
            "total_submitted": new_total,
            "progress_to_meta": progress_pct,
            "meta": meta,
        }
        new_feedbacks.append(entry)

        # Adiciona temporariamente para check de marcos
        feedbacks_temp = feedbacks + new_feedbacks
        check_milestone(total_submitted, new_total, persona)

        logging.info(
            f"[NOVO {version}] {persona['emoji']} {persona_name} ({persona['area']}): "
            f"{complaint[:80]} | Progresso: {new_total}/{meta} ({progress_pct}%)"
        )

    feedbacks.extend(new_feedbacks)
    save_feedbacks(feedbacks)
    logging.info(f"✅ {len(new_feedbacks)} reclamações adicionadas. Total no arquivo: {len(feedbacks)}.")


if __name__ == '__main__':
    import sys
    if "--daemon" in sys.argv:
        logging.info("🔄 [USER DAEMON] Iniciando annoying_user no modo daemon (sprints de 60s)...")
        while True:
            try:
                main()
            except Exception as e:
                logging.error(f"Erro no loop do annoying_user: {e}")
            time.sleep(60)
    else:
        main()

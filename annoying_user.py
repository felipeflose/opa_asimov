import os
import json
import random
import logging
from datetime import datetime, timedelta, timezone

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

APP_DIR = os.path.dirname(os.path.abspath(__file__))
FEEDBACK_FILE = os.path.join(APP_DIR, 'user_feedback.json')

# ---------------------------------------------------------------------------
# 30 PERSONAS — Brazilian tech workers, realistic, diverse areas
# ---------------------------------------------------------------------------
USER_PERSONAS = [
    # 1. UI Designer
    {
        "name": "Aline Rodrigues",
        "emoji": "👩‍🎨",
        "role": "UI Designer",
        "area": "UI/UX",
        "templates": [
            "O painel de grafo usa neon verde sobre fundo preto — depois de 10 minutos minha vista cansa demais. Precisamos de um tema claro opcional.",
            "Os tooltips dos nós somem antes de eu conseguir ler o conteúdo. O delay de hover está absurdamente curto no D3.js.",
            "Quando dou zoom no grafo, os labels dos nós se sobrepõem uns aos outros e fica impossível identificar qual nota é qual.",
            "A barra lateral de filtros não tem scroll em telas menores; metade das opções fica escondida e sem forma de acessar.",
            "O botão 'Resetar Grafo' fica numa posição muito parecida com o botão 'Deletar Nota'. Já cliquei errado duas vezes hoje.",
            "As arestas do grafo ficam finas demais quando há muitas conexões — fica parecendo ruído visual, não informação útil.",
        ],
    },
    # 2. Backend Engineer
    {
        "name": "Carlos Mendes",
        "emoji": "👨‍💻",
        "role": "Backend Engineer",
        "area": "Backend",
        "templates": [
            "O endpoint /api/graph demora mais de 2 segundos quando o vault tem mais de 500 notas. Cadê a paginação ou cache?",
            "O servidor Flask não está usando connection pooling no SQLite — vejo 'database is locked' nos logs toda vez que dois agents rodam juntos.",
            "A rota SSE /api/stream não tem timeout configurado; conexões zumbis ficam abertas indefinidamente e consomem threads.",
            "Não há compressão gzip nas respostas JSON do /api/graph — o payload bate 400 KB sem necessidade nenhuma.",
            "O app.py mistura lógica de negócio com rotas Flask. Isso torna impossível escrever testes unitários sem subir o servidor inteiro.",
            "Falta um endpoint de health check adequado — o /health retorna 200 mesmo quando o SQLite está corrompido.",
        ],
    },
    # 3. Security Engineer
    {
        "name": "Fernanda Alves",
        "emoji": "🔐",
        "role": "Security Engineer",
        "area": "Security",
        "templates": [
            "A GROQ_API_KEY está exposta no arquivo .env sem nenhum vault ou secret manager. Qualquer pessoa com acesso ao repositório vê a chave.",
            "O servidor Flask roda sem HTTPS no modo desenvolvimento e ninguém avisa que isso não deve ir para produção assim.",
            "Não vi nenhuma validação de entrada nas rotas de busca — um payload malformado pode causar crash ou path traversal no vault.",
            "Os logs do servidor incluem os prompts completos enviados ao LLM, o que pode vazar dados sensíveis das notas do Obsidian.",
            "O bot do Telegram não verifica o chat_id do remetente — qualquer pessoa com o link pode enviar comandos ao sistema.",
            "Ausência total de rate limiting nas rotas da API Flask — trivial de explorar com um script de força bruta.",
        ],
    },
    # 4. Mobile Developer
    {
        "name": "Gustavo Lima",
        "emoji": "📱",
        "role": "Mobile Developer",
        "area": "Mobile",
        "templates": [
            "O grafo D3.js não funciona bem no mobile — os gestos de pinça para zoom conflitam com o scroll da página e tudo desanda.",
            "A interface web não tem viewport meta tag correta; em iPhone o layout quebra e os botões ficam fora da tela.",
            "O bot do Telegram tem um menu de comandos gigante que não cabe na tela de celulares compactos. Precisa de paginação.",
            "Enviei uma nota longa pelo Telegram e o bot travou por 30 segundos sem nenhum feedback de 'processando...'.",
            "O carregamento do grafo não tem indicador de progresso — a tela fica branca por vários segundos e parece que travou.",
            "Não existe PWA nem modo offline — se cair a internet no celular, o app vira uma tela em branco sem mensagem de erro.",
        ],
    },
    # 5. RAG Specialist
    {
        "name": "Mariana Costa",
        "emoji": "🧠",
        "role": "RAG Specialist",
        "area": "RAG/AI",
        "templates": [
            "A busca semântica retorna notas completamente irrelevantes quando a consulta tem mais de 15 palavras — o chunking está errado.",
            "Os embeddings não são atualizados quando uma nota é editada no Obsidian; o RAG continua retornando conteúdo desatualizado.",
            "O contexto enviado ao LLM inclui notas inteiras sem truncamento — isso desperdiça tokens e pode exceder o limite do modelo.",
            "Notas com muito código-fonte confundem o sistema de RAG; o retrieval prioriza blocos de código em vez do texto conceitual.",
            "Falta um score de similaridade nas respostas do RAG — não sei se o resultado tem 90% ou 30% de relevância para minha pergunta.",
            "O vault_embeddings.json já tem 50 MB — carregar isso inteiro na memória a cada busca é completamente inviável em produção.",
        ],
    },
    # 6. DevOps Engineer
    {
        "name": "Rafael Barbosa",
        "emoji": "⚙️",
        "role": "DevOps Engineer",
        "area": "DevOps",
        "templates": [
            "O Dockerfile usa 'python:latest' — isso vai quebrar na próxima atualização maior do Python. Precisamos fixar a versão.",
            "Não existe pipeline de CI/CD — merge na main vai direto para produção sem nenhum teste automatizado rodando antes.",
            "O docker-compose.yml não define limits de CPU e memória; em produção o container vai consumir todos os recursos da máquina.",
            "O server.log não tem rotação configurada — já vi esse arquivo crescer indefinidamente até lotar o disco.",
            "Falta um arquivo .dockerignore adequado — o contexto de build inclui o vault_embeddings.json de 50 MB desnecessariamente.",
            "O run_server.sh usa 'nohup' sem PID file — impossível saber o processo exato para reiniciar ou monitorar via systemd.",
        ],
    },
    # 7. Frontend Developer
    {
        "name": "Beatriz Ferreira",
        "emoji": "🎨",
        "role": "Frontend Developer",
        "area": "Frontend",
        "templates": [
            "O JavaScript do grafo está todo inline no template HTML — são mais de 800 linhas sem modularização nem bundler.",
            "Não tem tratamento de erro no fetch para /api/graph — se o servidor cair, a tela fica em branco sem nenhuma mensagem ao usuário.",
            "O D3.js está sendo carregado via CDN sem lock de versão — se a CDN mudar algo, o grafo para de funcionar em produção.",
            "A busca de notas faz um fetch a cada tecla digitada sem debounce — isso envia dezenas de requisições por segundo ao servidor.",
            "As cores dos nós do grafo estão hardcoded em hexadecimal espalhados pelo código — impossível mudar o tema sem grep global.",
            "O estado visual do grafo (posição dos nós, zoom) não é salvo em localStorage — a cada reload tudo reseta do zero.",
        ],
    },
    # 8. Data Engineer
    {
        "name": "Thiago Nascimento",
        "emoji": "📊",
        "role": "Data Engineer",
        "area": "Data",
        "templates": [
            "O obsidian_graph.json não tem schema versionado — qualquer mudança estrutural quebra todos os consumers silenciosamente.",
            "O user_feedback.json cresce indefinidamente sem TTL ou arquivamento — já imaginou esse arquivo com 6 meses de dados?",
            "Não existe pipeline de dados estruturado; os scripts leem e escrevem JSON direto sem validação de integridade.",
            "O SQLite não está configurado com WAL mode — em escritas simultâneas o banco trava e o servidor retorna 500.",
            "Falta um job de limpeza de embeddings obsoletos no vault_embeddings.json — notas deletadas continuam como vetores mortos.",
            "Os timestamps no feedback não estão padronizados em UTC — vejo entradas com offset -03:00 misturadas com naive datetimes.",
        ],
    },
    # 9. QA Analyst
    {
        "name": "Priscila Santos",
        "emoji": "🧪",
        "role": "QA Analyst",
        "area": "QA",
        "templates": [
            "Rodei a suite de testes e metade falha por dependência de arquivo local que não existe no ambiente de CI. Cobertura é ilusória.",
            "O fluxo de indexação do vault não tem testes de integração — já quebramos produção duas vezes sem perceber no code review.",
            "Não há testes para o caso de vault vazio — o sistema joga KeyError e o usuário vê uma stack trace crua no browser.",
            "Os agentes (agent_rag.py, agent_core.py) não têm mocks para chamadas LLM nos testes — cada execução de teste consome tokens de API.",
            "Testei o bot do Telegram com entrada em UTF-8 especial (emojis compostos) e o parser travou sem log de erro útil.",
            "Falta um ambiente de staging isolado — qualquer teste manual que faço bagunça os dados de produção do feedback.",
        ],
    },
    # 10. Product Owner
    {
        "name": "Felipe Fróes",
        "emoji": "📋",
        "role": "Product Owner",
        "area": "Product",
        "templates": [
            "O backlog de melhorias tem mais de 4 MB de JSON mas não tem priorização por impacto — impossível decidir o que atacar primeiro.",
            "Não existe dashboard de métricas de uso — não sei quantas buscas RAG são feitas por dia nem qual é a taxa de satisfação real.",
            "O bot do Telegram não coleta feedback pós-resposta — nunca sabemos se o usuário ficou satisfeito com a resposta do LLM.",
            "Falta uma roadmap visual do produto — cada desenvolvedor implementa o que acha mais interessante sem alinhamento estratégico.",
            "O sistema não tem SLOs definidos — não sabemos qual é o tempo de resposta aceitável nem como medir sucesso operacional.",
            "A feature de geração de daily digest não tem gatilho confiável — às vezes roda, às vezes não, sem nenhum alerta de falha.",
        ],
    },
    # 11. SRE
    {
        "name": "Anderson Oliveira",
        "emoji": "🔧",
        "role": "Site Reliability Engineer",
        "area": "SRE",
        "templates": [
            "Não há alertas configurados para o servidor Flask — fico sabendo que o sistema caiu só quando o usuário me manda mensagem.",
            "O MTTR está alto porque os logs de erro são vagos demais — 'Erro ao processar' sem stack trace ou contexto não me ajuda nada.",
            "A aplicação não expõe métricas Prometheus — impossível monitorar throughput, error rate e latência em tempo real.",
            "O processo do servidor Flask é gerenciado por nohup em vez de systemd — se o servidor reiniciar, o app não volta sozinho.",
            "Não existe runbook para os incidentes mais comuns — cada vez que o SQLite trava, o time vai no trial-and-error.",
            "O backup do obsidian_graph.json é feito manualmente — já perdemos dados importantes porque esquecemos de fazer o backup antes do deploy.",
        ],
    },
    # 12. Full Stack Developer
    {
        "name": "Juliana Moreira",
        "emoji": "💻",
        "role": "Full Stack Developer",
        "area": "Full Stack",
        "templates": [
            "O app.py tem mais de 1300 linhas — é impossível encontrar a rota certa sem fazer Ctrl+F. Isso precisa ser separado em blueprints.",
            "O CORS está configurado com allow_origins='*' — isso é um problema sério se alguma rota lidar com dados do usuário.",
            "Não existe separação entre variáveis de configuração de dev e prod — já quebramos o servidor de produção apontando pro banco errado.",
            "O servidor Flask roda em modo debug=True mesmo no Docker — isso expõe o debugger interativo publicamente.",
            "Falta um sistema de sessão — qualquer pessoa que conhece a URL consegue acessar o painel do grafo sem autenticação.",
            "O obsidian_graph.json é carregado inteiro na memória a cada request — para um grafo grande isso é um memory leak progressivo.",
        ],
    },
    # 13. ML Engineer
    {
        "name": "Lucas Rezende",
        "emoji": "🤖",
        "role": "ML Engineer",
        "area": "RAG/AI",
        "templates": [
            "O modelo de embeddings não está versionado no código — se trocarmos o modelo, os vetores antigos ficam incompatíveis sem nenhum aviso.",
            "Não há experimento de avaliação do RAG — como sabemos se o sistema está melhorando ou piorando com cada alteração?",
            "O agente agent_rag.py não tem circuit breaker para falhas de API — uma queda do Groq deixa o sistema inteiro bloqueado.",
            "A temperatura dos LLMs está hardcoded em 0.7 em todos os agentes — deveríamos ter configs diferentes por tipo de tarefa.",
            "Falta logging estruturado das chamadas ao LLM (tokens usados, latência, modelo) — impossível otimizar custos sem esses dados.",
            "O sistema não faz re-ranking dos resultados do retrieval — os primeiros k chunks nem sempre são os mais relevantes para a query.",
        ],
    },
    # 14. DBA
    {
        "name": "Roberto Cardoso",
        "emoji": "🗄️",
        "role": "Database Administrator",
        "area": "Data",
        "templates": [
            "O SQLite não tem índices nas colunas de busca de feedback — uma query full scan em tabela grande vai degradar brutalmente.",
            "Não existe migration versionada para o schema do SQLite — cada desenvolvedor aplica ALTER TABLE manualmente e o ambiente fica divergente.",
            "O banco SQLite não está configurado com PRAGMA journal_mode=WAL — escritas concorrentes causam 'database is locked' no servidor.",
            "Não há backup automatizado do SQLite — uma falha de disco elimina todo o histórico de feedbacks e logs estruturados.",
            "As queries no código usam f-strings para montar SQL — isso é vulnerabilidade de SQL injection clássica esperando para acontecer.",
            "O SQLite está sendo usado em modo shared entre múltiplos processos Python sem qualquer serialização — isso vai corromper os dados.",
        ],
    },
    # 15. Tech Lead
    {
        "name": "Marcelo Teixeira",
        "emoji": "🏗️",
        "role": "Tech Lead",
        "area": "Backend",
        "templates": [
            "O projeto não tem arquitetura documentada — novos devs levam dias entendendo qual agent faz o quê e como se conectam.",
            "Não há padrão de logging definido — cada arquivo usa um estilo diferente, o que torna a agregação de logs impossível.",
            "A comunicação entre agentes é feita via arquivos JSON no disco — isso vai criar race conditions sérios com múltiplos agentes rodando.",
            "Falta um ADR (Architectural Decision Record) para as escolhas de SQLite, Flask e D3.js — perdemos o contexto de por que essas decisões foram tomadas.",
            "O código de produção tem dezenas de 'TODO' e 'FIXME' sem issue linkada — débito técnico invisível que vai explodir um dia.",
            "Não existe contrato de API documentado (OpenAPI/Swagger) — cada consumidor descobre os campos na mão olhando o código.",
        ],
    },
    # 16. Accessibility Specialist
    {
        "name": "Camila Duarte",
        "emoji": "♿",
        "role": "Accessibility Specialist",
        "area": "UI/UX",
        "templates": [
            "O grafo D3.js é completamente inacessível via teclado — usuários com deficiência visual não conseguem navegar pelos nós.",
            "Não há atributos aria-label em nenhum elemento interativo do grafo — screen readers leem tudo como 'grupo' sem contexto.",
            "O contraste de cor dos labels dos nós não atinge o ratio mínimo WCAG AA — pessoas com daltonismo verde-vermelho não enxergam nada.",
            "Os tooltips do grafo somem ao mover o mouse — quem usa switch access ou teclado nunca consegue ler o conteúdo completo.",
            "Não existe modo de alto contraste — o tema neon escuro é bonito mas inacessível para quem tem sensibilidade à luz.",
            "Os formulários do painel administrativo não têm labels associadas corretamente — assistivos leem os inputs sem contexto algum.",
        ],
    },
    # 17. Performance Engineer
    {
        "name": "Diego Cavalcante",
        "emoji": "⚡",
        "role": "Performance Engineer",
        "area": "Backend",
        "templates": [
            "O endpoint /api/graph gera o JSON do grafo inteiro a cada request sem nenhum cache — para 1000 notas isso é reconstrução O(n²) toda vez.",
            "O vault_embeddings.json é carregado inteiro em memória a cada busca RAG — 50 MB de I/O de disco por query é inadmissível.",
            "O D3.js renderiza todos os nós do grafo sem virtualização — com 800+ nós o browser fica com 100% de CPU e trava.",
            "Não há cache HTTP (ETag, Cache-Control) nas rotas estáticas — o browser baixa os assets do zero a cada reload.",
            "O agente de indexação do vault bloqueia o event loop do Flask durante a execução — o servidor fica completamente irresponsivo.",
            "A busca de texto no frontend é feita via filter em um array com todos os nós carregados em memória JS — com grafo grande trava o browser.",
        ],
    },
    # 18. Data Scientist
    {
        "name": "Natalia Pimentel",
        "emoji": "📈",
        "role": "Data Scientist",
        "area": "Data",
        "templates": [
            "O sistema não coleta métricas de uso de features — não sei quais partes do grafo as pessoas mais usam nem o que ignoram.",
            "Falta análise de cluster nas notas do Obsidian — seria valioso descobrir automaticamente grupos temáticos no vault.",
            "Os feedbacks dos usuários ficam em JSON sem nenhuma análise de sentimento ou categorização automática — dado desperdiçado.",
            "Não há visualização de evolução do grafo ao longo do tempo — impossível ver como o conhecimento cresceu e mudou.",
            "O agente agent_mba.py roda análises sem salvar os resultados de forma estruturada — cada análise é efêmera e irreproduzível.",
            "Falta detecção automática de notas duplicadas ou muito similares no vault usando os embeddings que já existem.",
        ],
    },
    # 19. Cloud Architect
    {
        "name": "Henrique Monteiro",
        "emoji": "☁️",
        "role": "Cloud Architect",
        "area": "DevOps",
        "templates": [
            "A aplicação não é stateless — estado é salvo em arquivos JSON locais, o que impossibilita escalar horizontalmente.",
            "Não há estratégia de deploy blue-green ou canary — cada update é um big bang que coloca o sistema offline sem rollback fácil.",
            "O docker-compose.yml não usa secrets do Docker — variáveis de ambiente sensíveis ficam visíveis no 'docker inspect'.",
            "Falta configuração de auto-scaling — em picos de uso o servidor único vai afundar sem nenhuma forma de recuperação automática.",
            "O banco SQLite não é compatível com ambientes cloud multi-instância — precisamos migrar para Postgres antes de qualquer scale.",
            "Não existe IaC (Terraform, Pulumi) — o ambiente de produção foi montado manualmente e é impossível recriar de forma reprodutível.",
        ],
    },
    # 20. Scrum Master
    {
        "name": "Vanessa Correia",
        "emoji": "🏃",
        "role": "Scrum Master",
        "area": "Product",
        "templates": [
            "O improvement_backlog.json tem mais de 4 MB e centenas de itens sem nenhuma estimativa de esforço ou valor de negócio.",
            "Não existe definição de done para as melhorias geradas pelo sistema — itens ficam em pending para sempre sem critério de aceite.",
            "A daily digest é gerada automaticamente mas ninguém valida se as ações priorizadas fazem sentido — automação sem governança.",
            "Falta uma retrospectiva automatizada baseada nos dados de feedback — o sistema coleta dados mas não aprende com eles sistematicamente.",
            "Os agentes implementam features de forma autônoma sem review humano — já tivemos código em produção que ninguém revisou.",
            "Não há cerimônia de planning informada por dados reais de uso — priorizamos intuição em vez de evidências do sistema.",
        ],
    },
    # 21. GraphQL/API Specialist
    {
        "name": "Eduardo Prado",
        "emoji": "🔗",
        "role": "API Specialist",
        "area": "Backend",
        "templates": [
            "A API REST do Flask não tem versionamento — se mudarmos o schema do /api/graph, todos os clientes quebram simultaneamente.",
            "Não existe documentação interativa da API — toda vez que integro algo novo tenho que ler o app.py de 1300 linhas para entender.",
            "Os erros da API retornam HTML do Flask em vez de JSON estruturado — impossível para o frontend tratar erros programaticamente.",
            "Falta paginação no /api/graph — com vault grande o payload ultrapassa 400 KB e o time to first byte fica inaceitável.",
            "A API não implementa conditional requests (If-None-Match) — o frontend baixa o grafo completo mesmo quando nada mudou.",
            "Não há rate limiting por cliente nas rotas da API — um script mal feito pode derrubar o servidor para todos os usuários.",
        ],
    },
    # 22. Knowledge Management Expert
    {
        "name": "Simone Batista",
        "emoji": "📚",
        "role": "Knowledge Manager",
        "area": "Product",
        "templates": [
            "O grafo do Obsidian não mostra a força das conexões entre notas — todas as arestas têm o mesmo peso visual, perdendo informação.",
            "Notas arquivadas continuam aparecendo no grafo como se fossem ativas — isso polui a visualização com conteúdo obsoleto.",
            "Falta um modo de visualização por tag — quero ver apenas as notas de uma área específica sem filtrar manualmente.",
            "O sistema não detecta notas orfãs automaticamente — tenho dezenas de notas sem link que ficam invisíveis no grafo.",
            "A indexação do vault não respeita o frontmatter YAML das notas — metadados importantes como autor e data são ignorados.",
            "Não há histórico de versões das notas no grafo — quando uma nota muda muito, perco o contexto de como o conhecimento evoluiu.",
        ],
    },
    # 23. Telegram Bot Developer
    {
        "name": "Paulo Freitas",
        "emoji": "🤖",
        "role": "Bot Developer",
        "area": "Mobile",
        "templates": [
            "O bot do Telegram não tem comando /help atualizado — os comandos listados são diferentes dos que realmente funcionam.",
            "Ao enviar áudio para o bot, o sistema tenta processar sem verificar se o Whisper está disponível — joga uma exceção crua para o usuário.",
            "O bot não trata mensagens simultâneas corretamente — se dois usuários mandam mensagem ao mesmo tempo, um deles recebe a resposta do outro.",
            "O webhook do Telegram não tem retry configurado — se o servidor estiver lento na hora da entrega, a mensagem é perdida silenciosamente.",
            "Comandos com parâmetros como /busca <termo> não têm validação de tamanho — um termo muito longo trava o processamento RAG.",
            "O bot não persiste o histórico de conversa por usuário — cada mensagem é tratada como nova sem contexto da sessão anterior.",
        ],
    },
    # 24. Network/Infrastructure Engineer
    {
        "name": "Rodrigo Esteves",
        "emoji": "🌐",
        "role": "Infrastructure Engineer",
        "area": "DevOps",
        "templates": [
            "O servidor Flask roda diretamente sem proxy reverso (nginx/caddy) — está exposto diretamente na porta 8091 sem buffer de conexões.",
            "Não há configuração de firewall documentada — a porta 8091 está aberta para qualquer IP sem restrição.",
            "O run_server.sh não usa gunicorn ou uvicorn — o servidor de desenvolvimento do Flask não é adequado para uso em produção.",
            "Falta configuração de timeouts no servidor — conexões lentas bloqueiam workers do Flask por tempo indeterminado.",
            "Não existe monitoramento de certificado SSL — se usarmos HTTPS algum dia, o cert pode expirar sem ninguém perceber.",
            "O servidor não tem configuração de limites de tamanho de request — é possível enviar um payload de vários GB e travar a memória.",
        ],
    },
    # 25. Observability Engineer
    {
        "name": "Amanda Ribeiro",
        "emoji": "🔭",
        "role": "Observability Engineer",
        "area": "SRE",
        "templates": [
            "Os logs do sistema não têm trace ID correlacionando request entre os diferentes agentes — rastrear um bug é como procurar agulha no palheiro.",
            "Não há spans de tracing nas chamadas LLM — impossível saber qual etapa do pipeline RAG está causando lentidão.",
            "O server.log mistura logs de INFO, DEBUG e ERROR sem estrutura JSON — ferramentas de log management não conseguem parsear.",
            "Falta um dashboard de latência por endpoint — sei que o sistema está lento mas não sei exatamente qual rota é o gargalo.",
            "Os agentes não emitem eventos estruturados — cada um loga de forma diferente e correlacionar uma sessão completa é impossível.",
            "Não existe alerta de anomalia de token usage — uma query mal formada pode consumir todos os tokens do mês sem nenhum aviso.",
        ],
    },
    # 26. Graph Visualization Specialist
    {
        "name": "Isabela Gomes",
        "emoji": "🕸️",
        "role": "Graph Visualization Specialist",
        "area": "UI/UX",
        "templates": [
            "O layout de força do D3.js oscila indefinidamente mesmo depois de convergir — nós continuam tremendo quando o usuário para de interagir.",
            "Não há suporte a clusters visuais no grafo — todos os nós ficam numa sopa caótica sem agrupamento por área ou tag.",
            "A performance do D3.js cai drasticamente com mais de 500 nós — precisamos de WebGL (via sigma.js ou three.js) para grafos maiores.",
            "Ao clicar num nó, o grafo não centraliza nele automaticamente — o usuário tem que arrastar manualmente para encontrar o nó selecionado.",
            "Não há mini-mapa de navegação para grafos grandes — fico completamente perdido quando navego por um vault com centenas de notas.",
            "As arestas direcionadas não têm setas visíveis — impossível saber qual nota linka para qual apenas olhando o grafo.",
        ],
    },
    # 27. Prompt Engineer
    {
        "name": "Tiago Borges",
        "emoji": "✍️",
        "role": "Prompt Engineer",
        "area": "RAG/AI",
        "templates": [
            "Os prompts dos agentes estão hardcoded no código Python — qualquer ajuste fino exige redeploy em vez de editar um arquivo de config.",
            "Não há sistema de prompt versioning — mudamos o prompt e não conseguimos comparar qual versão anterior dava respostas melhores.",
            "O contexto RAG é passado ao LLM sem estruturação de citações — o modelo alucina fontes sem que o usuário saiba qual nota originou a resposta.",
            "Falta few-shot examples nos prompts dos agentes — as respostas ficam genéricas quando o domínio é muito específico do vault do usuário.",
            "O prompt de sumarização não instrui o modelo a manter terminologia do vault — respostas usam sinônimos que confundem a busca futura.",
            "Não há mecanismo de avaliação de qualidade dos prompts — mudamos e só sabemos se melhorou por feeling, não por métricas.",
        ],
    },
    # 28. Compliance/LGPD Officer
    {
        "name": "Cristiane Peixoto",
        "emoji": "⚖️",
        "role": "Compliance Officer",
        "area": "Security",
        "templates": [
            "O user_feedback.json armazena dados de usuários sem nenhuma política de retenção — isso pode violar a LGPD dependendo do conteúdo.",
            "Não há mecanismo de anonimização de dados nas notas enviadas ao LLM externo — dados pessoais do vault saem para APIs de terceiros.",
            "O sistema não tem política de privacidade ou termos de uso documentados — risco legal caso o app seja usado por terceiros.",
            "Logs do servidor contêm conteúdo das notas em texto plano — isso pode incluir dados pessoais sensíveis sem controle de acesso adequado.",
            "Não existe processo de data subject request — se um usuário pedir pra deletar seus dados, não temos mecanismo para atender.",
            "O vault do Obsidian é acessado diretamente pelo sistema sem auditoria de acesso — não sabemos quem leu o quê e quando.",
        ],
    },
    # 29. Test Automation Engineer
    {
        "name": "Leandro Fontes",
        "emoji": "🤖",
        "role": "Test Automation Engineer",
        "area": "QA",
        "templates": [
            "A suite de testes em /tests não tem fixtures para mock do SQLite — cada teste cria dependência de arquivo real e polui o ambiente.",
            "Não existe teste de contrato para a API Flask — mudanças no schema do /api/graph quebram o frontend sem nenhum teste alertando.",
            "Os testes de integração do bot Telegram dependem de uma conta real — impossível rodar em CI sem expor o token do bot.",
            "Falta teste de carga simulando 10+ usuários simultâneos — só vamos descobrir o gargalo de concorrência em produção.",
            "Não há teste de regressão visual para o grafo D3.js — uma mudança de CSS pode quebrar a visualização sem ninguém perceber.",
            "A cobertura de código está em 23% segundo o último relatório — estamos deployando às cegas em mais de 75% do código.",
        ],
    },
    # 30. Open Source Contributor
    {
        "name": "Viviane Araujo",
        "emoji": "🌱",
        "role": "Open Source Contributor",
        "area": "Full Stack",
        "templates": [
            "O README.md não tem instruções de como configurar o ambiente de desenvolvimento — passei 2 horas descobrindo dependências na força bruta.",
            "Não existe arquivo CONTRIBUTING.md — contribuidores externos não sabem o padrão de código, branch naming ou como abrir PRs.",
            "O .env.example não está sincronizado com o .env real — tem variáveis em uso que não estão documentadas no exemplo.",
            "Falta um arquivo de CHANGELOG bem mantido — não consigo entender o que mudou entre versões sem ler commit por commit.",
            "As dependências em requirements.txt não têm versões fixadas com hash — pip install pode instalar versões incompatíveis silenciosamente.",
            "O projeto não tem licença definida — tecnicamente ninguém pode usar, modificar ou contribuir legalmente sem permissão explícita.",
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
# Deduplication: same persona + same complaint text in last 24 h
# ---------------------------------------------------------------------------

def is_duplicate(feedbacks, persona_name: str, complaint_text: str) -> bool:
    """Return True if this persona already submitted the same complaint in the last 24 h."""
    cutoff = datetime.now(timezone.utc) - timedelta(hours=24)
    needle = complaint_text.strip().lower()
    for fb in feedbacks:
        # parse timestamp — handle both naive and tz-aware ISO strings
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


# ---------------------------------------------------------------------------
# Optional LLM fallback (only when persona has no templates — never by default)
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
        f"e está usando o Obsidian Graph App. Escreva UMA reclamação curta (máx 2 frases, "
        f"em português), direta e irritada sobre algum problema real do sistema. "
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
        templates = persona.get("templates", [])

        # Pick complaint text
        if templates:
            # Default fast path: random template, no LLM call
            complaint = random.choice(templates)
        else:
            # Fallback to LLM only if persona has no templates at all
            complaint = call_llm_for_complaint(persona)
            if not complaint:
                complaint = "O sistema está apresentando inconsistências que dificultam meu uso."

        # Deduplication check
        if is_duplicate(feedbacks, persona["name"], complaint):
            logging.info(f"[SKIP duplicado] {persona['name']}: '{complaint[:60]}...'")
            continue

        entry = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "user": persona["name"],
            "avatar": persona["emoji"],
            "role": persona["role"],
            "area": persona["area"],
            "complaint": complaint,
            "status": "pending",
        }
        new_feedbacks.append(entry)
        logging.info(f"[NOVO] {persona['emoji']} {persona['name']} ({persona['area']}): {complaint[:80]}")

    feedbacks.extend(new_feedbacks)
    save_feedbacks(feedbacks)
    logging.info(f"✅ {len(new_feedbacks)} reclamações adicionadas. Total no arquivo: {len(feedbacks)}.")


if __name__ == '__main__':
    main()

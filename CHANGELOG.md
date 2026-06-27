# Changelog — obsidian_graph_app

Todo o histórico de melhorias, correções de segurança, performance e observabilidade aplicados no ecossistema da AI Factory.

---

## [Lote 10] — Arquitetura e Escalabilidade — 23-05-2026
### Adicionado
- **Desacoplar Uptime e Logs do Bot**: Telemetria do Bot Telegram é enviada de forma assíncrona não bloqueante via HTTP POST para a rota `/api/bot/telemetry` do Flask App. O Flask gerencia o cache de integridade em memória, removendo o acoplamento físico concorrente de arquivos de estado.
- **Fila de Tarefas Persistente**: Substituição do `asyncio.Queue` do bot por `PersistentQueue` baseada em SQLite (`logs/task_queue.db`), garantindo sobrevivência de requisições de geração de diagramas e indexação após quedas e restarts.
- **Lock de Arquivo fcntl no RAG**: Proteção com `fcntl.flock` exclusivo e compartilhado na leitura e escrita do banco de embeddings `vault_embeddings.json`.
- **Resiliência contra Quedas do Ollama**: Função `local_ollama_call` equipada com retries automáticos com tempo de espera incremental (backoff exponencial) para tolerar indisponibilidades momentâneas de rede ou concorrência.
- **Fila de Prioridade para Novos Arquivos**: O gerador de grafos agora processa primeiro arquivos novos detectados no vault, colocando arquivos antigos (que já possuem correspondência no grafo) no final da fila.
- **Ordenação Inteligente de Embeddings**: `LimitedCache` em `agent_edge.py` refatorado para LRU Cache estrito baseado em `OrderedDict`.
- **Limite de Ligações Redundantes**: Implementada restrição de cross-links máximos por nó (`FLOSE_MAX_CROSS_LINKS_PER_NODE`, padrão: 4) no auditor de linhagem, mitigando saturação visual do grafo.
- **Controle de Versão de Schema**: Controle de versão no metadados do grafo (`schema_version: "2.0.0"`) com rotina automática de migração e sanitização de schema legado no `load_graph`.
- **Arquitetura de Sharding**: Criação do guia e manual conceitual `docs/SHARDING_DESIGN.md` para particionamento horizontal de vaults gigantescos em diretórios lógicos independentes.

---

## [Lote 9] — Configuração e DevOps — 23-05-2026
### Adicionado
- **Containerização**: Criação de `Dockerfile` otimizado (Python 3.9-slim, ferramentas de runtime e dependências de produção) e `docker-compose.yml` para orquestração isolada e persistência de volumes.
- **Congelamento e Separação de Dependências**: Divisão em `requirements.txt` (produção com versões estritas e gunicorn) e `requirements-dev.txt` (testes).
- **Monitoramento de Processos**: O `HealthMonitor` em `agent_health.py` agora monitora em background o uso de CPU e memória RAM do próprio processo ativo do Flask (PID), reportando para o status e health check.
- **Rotação de Logs e Limpeza de Backups**: Implementada rotação automática de logs que excedam 2MB (`rotate_logs`) e política inteligente de backups controlando tamanho total em disco e contagem de backups no `agent_sanitizer.py`.
- **Scripts Robustos**: `run_server.sh` aprimorado com tratamento estrito de erros, verificação de virtualenv e `exec` para melhor controle de sinais.
- **Templates de Deploy**: Arquivos templates do Supervisord (`supervisord.conf`) e Systemd (`flos_server.service` e `flos_bot.service`) criados sob a pasta `docs/` para auto-restart.

---

## [Lote 8] — UX / Interface / Frontend — 23-05-2026
### Adicionado
- **Modularização de Frontend**: Lógica JS e estilos CSS separados de `templates/index.html` para `static/js/app.js` e `static/css/style.css`.
- **Fundo Animado Dinâmico**: Integração do canvas interativo de partículas (`static/js/neural_bg.js`).
- **Loading State**: Tela de carregamento centralizada e animada exibida enquanto o D3.js processa os dados do grafo.
- **Spinners em Ações**: Botões de controle ("Sincronizar", "Auditoria", "Sanitizar") mostram spinners de processamento e são desativados temporariamente em requisições de API.
- **Filtros de Log**: Filtro rápido no console de atividade para classificar logs por fonte (`[GRAPH]`, `[BOT]`).
- **Persistência de Layout**: Estados de zoom, translação e posições de nós arrastados manualmente salvos e carregados do `localStorage`.
- **Pesquisa e Foco no Grafo**: Busca autocompletável para nós do grafo, aplicando zoom focado animado e efeito de pulsação temporário ao nó selecionado.
- **Tooltips Detalhados**: Informações avançadas ao passar o mouse sobre o nó (tipo, ID e grau/quantidade de conexões).
- **Modal de Confirmação**: Caixa de diálogo premium e interativa antes da ação crítica "Kill All".
- **Paginação e Busca de Resumos**: Sala de Estudos agora suporta paginação inteligente e pesquisa rápida de resumos.
- **Design Responsivo**: Adaptabilidade do cockpit para mobile e tablets (barra lateral convertida em rodapé e painel do nó vira bottom-sheet).

---

## [Lote 7] — Documentação — 23-05-2026
### Adicionado
- **README.md e Diagrama de Arquitetura**: Guia de setup completo com diagrama Mermaid descrevendo a topologia de microsserviços.
- **Docstrings Abrangentes**: Documentação in-code completa nos endpoints HTTP, RAGAgent, bot handlers e run_update.sh.
- **Manuais Atualizados**: Correção do manual `DOCUMENTACAO_DO_AGENTE.md` para a nova infraestrutura.
- **Especificação Swagger/OpenAPI**: Arquivo `docs/openapi.yaml` descrevendo formalmente todos os contratos da API.

---

## [Lote 6] — Testes e CI/CD — 23-05-2026
### Adicionado
- **Suite de testes Pytest** (`pytest`, `pytest-mock`): Substituiu testes frágeis legados baseados em unittest.
- **Mocks Globais de Rede** (`tests/conftest.py`): Mock de requisições de embeddings e geração locais do Ollama e APIs da Groq e Telegram.
- **Testes Unitários**:
  - `tests/test_agent_classifier.py`: Cobre as regras forenses de triagem e classificação semântica de notas.
  - `tests/test_agent_sanitizer.py`: Valida higienização do grafo (fusão de duplicatas, remoção de self-loops, limpeza física e backup).
  - `tests/test_agent_edge.py`: Cobre linhagem, reconexão de nós órfãos e cross-links semânticos.
  - `tests/test_agent_rag.py`: Valida o pipeline do `RAGAgent` (gerenciamento lazy de cache de embeddings e busca por Cosseno).
  - `tests/test_app.py`: Cobre rotas Flask de telemetria, integridade do Bot e segurança.
- **Workflow do GitHub Actions** (`.github/workflows/ci.yml`): Execução automática do suite de testes em commits e PRs na branch `main`.

---

## [Lote 5] — Observabilidade e Logging — 23-05-2026
### Adicionado
- **Logging Centralizado (`agent_core.py`)**: Inicialização global unificada de logs, com suporte a níveis dinâmicos (`LOG_LEVEL`) e formatação JSON estruturada configurável via `LOG_FORMAT=JSON` para produção.
- **Captura Global de Exceções (`sys.excepthook`)**: Captura erros fatais e logs críticos em todos os pontos de entrada do Python.
- **Correlation ID Pipeline (`app.py`, `agent_core.py`)**: Geração e propagação de IDs de correlação (`FLOSE_CORRELATION_ID`) entre requisições HTTP e subprocessos assíncronos.
- **Persistência de Métricas (`metrics_history.json`)**: Histórico de telemetria agora sobrevive a reinicializações do servidor Flask.
- **Health Check Robusto**: Rota `/api/health` agora verifica ativamente se o processo do bot Telegram (`agent_bot.py`) está em execução no sistema.

---

## [Lote 4] — Performance — 23-05-2026
### Adicionado
- **Carregamento Inteligente de Cache (`RAGAgent`)**: O cache de embeddings de 50MB agora é mantido em memória e invalidado apenas se o mtime do arquivo em disco for modificado.
- **Similaridade Semântica O(1) e O(N) Vetorizada**: Otimização no cálculo de similaridade de cosseno utilizando álgebra linear vetorizada em Numpy (`np.dot` e `np.linalg.norm`), reduzindo tempo de execução para frações de milissegundos.
- **Compressão GZIP Nativa**: Endpoint `/api/graph` agora envia respostas comprimidas por gzip, reduzindo o tráfego de rede de ~780KB para ~150KB.
- **Gravação em Lote (Batching)**: Geração de grafos e escrita em lote reduziram drasticamente I/O excessivo em disco.

---

## [Lote 3] — Qualidade de Código parte 2 — 23-05-2026
### Adicionado
- **Cache de Cronograma (`agent_mba.py`)**: Evita leituras redundantes de arquivos HTML em disco.
- **Merge de Grafos Robusto (`agent_core.py`)**: Consolidação do merge no `save_graph` evitando race conditions e reuso correto na atualização de status do pipeline.
- **Type Hints**: Adição de assinaturas de tipo e tipagem estática no RAG e agentes especialistas.

---

## [Lote 2] — Qualidade de Código parte 1 — 23-05-2026
### Adicionado
- **Centralização DRY**:
  - `cosine_similarity` e extratores de amostragem de texto centralizados em `agent_core.py`.
  - Constantes globais (como `MAX_RETRIES` e `GENERIC_CLUSTERS`) centralizadas para evitar duplicações.
- **Cache Limitado (`LimitedCache`)**: Implementação de cache LRU com descarte mais antigo usando `OrderedDict` limitando estouro de memória no auditor.

---

## [Lote 1] — Segurança — 23-05-2026
### Adicionado
- **Segurança de Segredos**: Criação do `.env.example`, remoção de injeção de chaves brutas de API no frontend e `.gitignore` robusto ignorando credenciais locais e logs.
- **Autenticação Administrativa**: Proteção de endpoints de controle de processos via header `X-API-Key` e rate-limiting por IP.
- **Validação de Inputs**: Mitigação de Path Traversal no endpoint de resumos usando `werkzeug.utils.safe_join`.

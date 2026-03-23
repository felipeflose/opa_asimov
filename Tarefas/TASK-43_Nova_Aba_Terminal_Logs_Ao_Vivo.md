# TASK-43 | Nova Aba: Terminal de Logs ao Vivo

## Metadata
| Campo | Valor |
|---|---|
| ID | TASK-43 |
| Grupo | Nova Funcionalidade / DevOps |
| Prioridade | Alta |
| Responsável | FrontendAgent |
| Status | Aberto |

## Problema Identificado
Para debugar o sistema, o desenvolvedor precisa:
1. Abrir o Console do Cloud Run no GCP (lento)
2. Rodar `gcloud logging read` no terminal
3. Verificar o arquivo `telegram_bot.log` manualmente

Não existe uma janela de logs em tempo real dentro do próprio dashboard. O Streamlit tinha uma aba "Setup Logs" (`Setup_Logs.py`) que foi perdida na migração para React.

## Objetivo
Criar uma nova aba "Terminal" no dashboard com um console de logs estilo terminal que exibe eventos do sistema em tempo real via polling, com filtros por agente/nível e capacidade de busca.

## Cenário Real
Desenvolvedor abre a aba Terminal → vê stream de logs:
```
[10:23:41] [INFO] Orchestrator → FinOpsGuardian: tarefa delegada
[10:23:42] [INFO] FinOpsGuardian: custo hoje = $0.024
[10:23:43] [WARN] VisionAgent: arquivo não encontrado
[10:23:44] [ERROR] GCSClient: timeout ao salvar vector
```

Pode filtrar por `[ERROR]` e ver apenas os erros. Pode buscar "VisionAgent" e ver todos os logs daquele agente.

## Prompt para Antigravity

```
No `frontend/src/App.jsx`:

1. Adicionar "Terminal" na lista de tabs da sidebar 
   (com ícone `>_` e badge de erros recentes se houver).

2. Criar novo endpoint `GET /api/logs/stream?limit=100` 
   no `entrypoint.py` que lê:
   - Últimos 20 arquivos de `logs/executions/` 
   - Últimos 20 arquivos de `logs/telegram/`
   - Combina, ordena por timestamp, retorna array de log entries:
     `{ timestamp, level, agent, message }`

3. Componente `<TerminalView />`:
   
   a. HEADER: título "SYSTEM_TERMINAL", botão `[CLEAR]` que 
      limpa logs da tela (não do GCS), botão `[EXPORT]` que 
      baixa os logs como .txt, toggle `[AUTO-SCROLL]`.
   
   b. FILTROS (chips clicáveis):
      - Levels: ALL | INFO | WARN | ERROR
      - Quick filter input para buscar por agente ou mensagem
   
   c. TERMINAL DISPLAY:
      - Fundo `#030507`, font `JetBrains Mono` ou `monospace`
      - Overflow-y: auto, height: `calc(100vh - 300px)`
      - Cada linha: `[HH:MM:SS]` em muted, badge level colorido, 
        agent em cyan, mensagem em white
      - Cores por level:
        - INFO: branco
        - WARN: `#f59e0b`  
        - ERROR: `#ff4d4d` + fundo `rgba(255,77,77,0.05)`
        - SUCCESS: `#00ff80`
   
   d. AUTO-SCROLL: `useRef` no container + `useEffect` que 
      faz `ref.current.scrollTop = ref.current.scrollHeight` 
      sempre que `logs` mudar (quando toggle ativo).
   
   e. POLLING: a cada 3s, chamar `fetchLogs()` com diff 
      inteligente (só adicionar logs novos ao topo, não 
      re-renderizar tudo).

4. Contador de erros nas últimas 24h visível no badge da sidebar.
```

## Arquivos Envolvidos
- `frontend/src/App.jsx`
- `entrypoint.py` (endpoint GET /api/logs/stream)
- `frontend/src/index.css`

## Critério de Conclusão
- Terminal atualiza a cada 3s com novos logs
- Filtro por level funciona em tempo real
- Auto-scroll opcional funciona corretamente
- Export como .txt funcional
- Badge na sidebar mostra contagem de erros recentes

# Plano de Implementação — KnowledgeBrokerAgent + TokenBudgetAgent

**Projeto:** Flose AI Platform  
**Data:** Março 2026  
**Objetivo:** Criar um ciclo autônomo de certificação, melhoria e curadoria de agentes gerados dinamicamente, com controle de consumo de tokens.

---

## Contexto do Problema

Hoje o `CognitiveOrchestrator` gera agentes dinamicamente via `create_agent`. Esses agentes nascem com um `system_prompt` genérico, são registrados no `agents/registry.json` e ficam lá sem validação real. As tasks que eles geram são genéricas demais — sem consciência de pré-requisitos do mundo real (ex: "integrar ElevenLabs" sem mencionar que precisa de conta, API key, plano pago, endpoint correto).

O resultado: tasks inúteis, agentes fantasma no registry, desperdício de tokens.

---

## Solução: Dois Novos Agentes

### 1. `KnowledgeBrokerAgent`
### 2. `TokenBudgetAgent`

Eles trabalham juntos em um ciclo noturno autônomo. Você não precisa intervir.

---

## AGENTE 1: KnowledgeBrokerAgent

### Arquivo a criar
```
AtualizaAI/src/agents/knowledge_broker_agent.py
```

### Responsabilidade
Varrer todos os agentes gerados dinamicamente, entrevistá-los sobre seus pré-requisitos reais, certificar os que passam, e devolver para evolução os que falham.

### Lógica completa

```python
class KnowledgeBrokerAgent:
    def __init__(self, gcs_client, orchestrator):
        self.gcs = gcs_client
        self.orchestrator = orchestrator
```

#### Método principal: `run_certification_cycle(agent_budget: int)`

Recebe um número de agentes para processar naquele ciclo (controlado pelo `TokenBudgetAgent`).

**Passo 1 — Carregar fila de agentes não certificados**

Ler `agents/registry.json`. Filtrar apenas agentes que:
- Têm campo `certified: false` OU não têm o campo `certified`
- Têm campo `created_at` (foram gerados dinamicamente, não são agentes core)
- NÃO são agentes core: `["FinOpsGuardian", "CognitiveOrchestrator", "VisionAgent", "AudioAgent", "BriefingAgent", "ReportAgent", "ProactiveAlertAgent", "EvolutionJob"]`

Ordenar por `created_at` do mais antigo para o mais novo.

Pegar apenas os primeiros `agent_budget` da lista.

**Passo 2 — Entrevista de certificação**

Para cada agente da fila, montar um prompt de provocação e enviá-lo ao Gemini:

```
Você é o KnowledgeBroker da Flose AI. Sua função é entrevistar agentes gerados 
automaticamente e verificar se eles têm conhecimento real suficiente para criar 
tasks úteis.

AGENTE EM AVALIAÇÃO: {agent_name}
PROPÓSITO DECLARADO: {purpose}
SYSTEM PROMPT ATUAL: {system_prompt}

FAÇA AS SEGUINTES PERGUNTAS AO AGENTE (simule as respostas com base no que 
o system_prompt atual permitiria responder):

1. Quais são os PRÉ-REQUISITOS REAIS para executar sua função principal?
   (ex: conta em serviço externo, API key, plano pago, configuração específica)

2. Se alguém pedisse uma task agora, quais informações CONCRETAS você incluiria?
   (ex: endpoint, formato do payload, limitações conhecidas)

3. O que você NÃO sabe fazer e deveria informar ao usuário antes de aceitar uma task?

AVALIE as respostas simuladas e retorne JSON:
{
  "certified": true | false,
  "certification_reason": "explicação objetiva",
  "knowledge_gaps": ["gap1", "gap2"],
  "suggested_system_prompt_addition": "texto adicional para enriquecer o prompt",
  "provocative_message": "mensagem direta ao agente sobre o que ele precisa aprender"
}
```

**Passo 3 — Processar resultado**

Se `certified: true`:
- Adicionar campo `certified: true` no agente dentro do `agents/registry.json`
- Adicionar campo `certified_at: datetime.now().isoformat()`
- Salvar no GCS

Se `certified: false`:
- Adicionar o `suggested_system_prompt_addition` ao `system_prompt` existente do agente
- Registrar os `knowledge_gaps` em `agents/certification/{agent_name}.json`
- Marcar `certified: false` com `certification_attempts: +1`
- Salvar no GCS
- Gerar uma task de auto-melhoria para o agente (ver abaixo)

**Passo 4 — Gerar task de auto-melhoria (apenas para reprovados)**

Salvar em `demands/registry.json` uma nova task:

```python
{
    "id": f"CERT_{os.urandom(3).hex()}",
    "title": f"Certificação Pendente: {agent_name}",
    "type": "tarefa",
    "responsible": agent_name,
    "priority": "Alta",
    "status": "Aberto",
    "budget_approved": True,
    "objective": f"O agente {agent_name} falhou na certificação do KnowledgeBroker. "
                 f"Gaps identificados: {knowledge_gaps}. "
                 f"O agente deve demonstrar conhecimento real dos pré-requisitos de sua função.",
    "governance_finops": "Custo estimado: 1 chamada Gemini (~0.5k tokens). Aprovado automaticamente pelo TokenBudget.",
    "created_at": datetime.now().isoformat()
}
```

**Passo 5 — Salvar log do ciclo**

Salvar em `logs/broker/cycle_{timestamp}.json`:

```json
{
  "timestamp": "...",
  "agents_processed": 5,
  "certified": ["AgentA", "AgentB"],
  "failed": ["AgentC"],
  "tokens_used_estimate": 2500
}
```

---

### Base de conhecimento de pré-requisitos

Criar arquivo `AtualizaAI/src/agents/broker_knowledge_base.py` com um dicionário estático de pré-requisitos conhecidos. O Broker injeta esse contexto no prompt de entrevista quando o nome do agente ou seu `purpose` contiver palavras-chave correspondentes.

```python
PREREQUISITES_KB = {
    "elevenlabs": {
        "requires_account": True,
        "requires_api_key": True,
        "free_plan_limits": "10k caracteres/mês",
        "paid_plan": "Starter $5/mês",
        "api_endpoint": "https://api.elevenlabs.io/v1",
        "key_operations": ["text-to-speech", "voice-cloning", "list-voices"],
        "notes": "Voice cloning requer plano Creator ou superior"
    },
    "stripe": {
        "requires_account": True,
        "requires_api_key": True,
        "key_types": ["publishable_key", "secret_key"],
        "webhook": "Requer configuração de endpoint e secret para verificação",
        "notes": "Webhook precisa de raw body — não parsear JSON antes de verificar assinatura"
    },
    "openai": {
        "requires_account": True,
        "requires_api_key": True,
        "billing": "Pay-per-use, cartão de crédito obrigatório após trial",
        "notes": "Rate limits variam por tier. GPT-4 tem custo 30x maior que GPT-3.5"
    },
    "gcp": {
        "requires_account": True,
        "requires_billing": True,
        "notes": "Billing precisa estar ativado mesmo para serviços gratuitos. APIs precisam ser habilitadas individualmente no Console."
    },
    "telegram": {
        "requires_bot_token": True,
        "how_to_get": "Criar bot via @BotFather",
        "webhook_vs_polling": "Webhook requer URL HTTPS pública. Polling funciona localmente.",
        "notes": "Limite de 30 mensagens/segundo por bot"
    },
    "napkin": {
        "requires_account": True,
        "requires_api_key": True,
        "notes": "API ainda em beta, pode ter instabilidades. Bearer token no header."
    }
}
```

O Broker verifica se alguma keyword do `purpose` ou `agent_name` bate com as chaves do dicionário e injeta o contexto relevante no prompt de entrevista.

---

## AGENTE 2: TokenBudgetAgent

### Arquivo a criar
```
AtualizaAI/src/agents/token_budget_agent.py
```

### Responsabilidade
Controlar quantos agentes o KnowledgeBroker pode processar por dia, baseado no budget diário de tokens disponível. Priorizar agentes mais antigos e mais críticos.

### Lógica completa

```python
class TokenBudgetAgent:
    DAILY_BROKER_TOKEN_BUDGET = 50_000  # tokens reservados por dia para ciclos do Broker
    TOKENS_PER_AGENT_ESTIMATE = 2_000   # estimativa conservadora por agente entrevistado
```

#### Método: `calculate_daily_agent_budget() -> int`

**Passo 1 — Verificar gasto atual do dia**

Ler `logs/finops/billing_daily.json` (já existe via `FinOpsManager`).

Pegar o total de tokens usados hoje.

**Passo 2 — Calcular quanto sobra para o Broker**

```python
used_today = daily_data.get("tokens", 0)
total_limit = 1_000_000  # limite diário configurado
broker_budget = DAILY_BROKER_TOKEN_BUDGET

# Se já gastou muito hoje, reduz o budget do Broker
if used_today > total_limit * 0.7:
    broker_budget = broker_budget * 0.3  # só 30% do budget normal
elif used_today > total_limit * 0.5:
    broker_budget = broker_budget * 0.6  # 60% do budget normal

agents_to_process = int(broker_budget / TOKENS_PER_AGENT_ESTIMATE)
return max(1, agents_to_process)  # mínimo 1 agente por dia
```

**Passo 3 — Retornar número de agentes permitidos**

Retornar o inteiro com quantos agentes o KnowledgeBroker pode processar naquele ciclo.

#### Método: `build_priority_queue() -> list`

Retorna lista de nomes de agentes em ordem de prioridade para o Broker processar.

Critérios de ordenação (do mais prioritário ao menos):

1. Agentes com `certified: false` e `certification_attempts >= 2` (crônicos — precisam de mais atenção)
2. Agentes com `certified: false` e `certification_attempts == 1` (primeira falha)
3. Agentes sem campo `certified` nenhum (nunca foram avaliados), ordenados por `created_at` do mais antigo
4. Agentes com `certified: true` mas `certified_at` há mais de 30 dias (re-certificação periódica)

#### Método: `log_budget_decision(agents_allowed, reason)`

Salvar em `logs/broker/budget_{date}.json` o motivo e a quantidade aprovada para auditoria.

---

## ENDPOINT: Ciclo Noturno

### Arquivo a modificar
```
AtualizaAI/entrypoint.py
```

### Adicionar endpoint

```python
@app.post("/broker_cycle")
async def broker_cycle():
    """Acionado pelo Cloud Scheduler à meia-noite. Executa o ciclo autônomo."""
    agent = await get_tg_agent()
    
    from src.agents.token_budget_agent import TokenBudgetAgent
    from src.agents.knowledge_broker_agent import KnowledgeBrokerAgent
    
    budget_agent = TokenBudgetAgent(gcs_client=agent.gcs_client)
    agents_allowed = budget_agent.calculate_daily_agent_budget()
    priority_queue = budget_agent.build_priority_queue()
    budget_agent.log_budget_decision(agents_allowed, "Ciclo automático noturno")
    
    broker = KnowledgeBrokerAgent(
        gcs_client=agent.gcs_client,
        orchestrator=agent.orchestrator
    )
    await broker.run_certification_cycle(agent_budget=agents_allowed, priority_queue=priority_queue)
    
    return {"status": "ok", "agents_processed": agents_allowed}
```

---

## CLOUD SCHEDULER: Agendamento

### Arquivo a modificar
```
AtualizaAI/.github/workflows/deploy.yml
```

### Adicionar step após o deploy

```yaml
- name: Setup Cloud Scheduler for Broker Cycle
  run: |
    SERVICE_URL=$(gcloud run services describe ${{ env.IMAGE_NAME }} \
      --platform managed --region ${{ env.REGION }} \
      --project=${{ env.PROJECT_ID }} --format="value(status.url)")
    
    gcloud scheduler jobs create http broker-nightly-cycle \
      --schedule="0 0 * * *" \
      --uri="${SERVICE_URL}/broker_cycle" \
      --http-method=POST \
      --location=${{ env.REGION }} \
      --project=${{ env.PROJECT_ID }} \
      --description="Ciclo noturno de certificação de agentes" \
      || gcloud scheduler jobs update http broker-nightly-cycle \
      --schedule="0 0 * * *" \
      --uri="${SERVICE_URL}/broker_cycle" \
      --location=${{ env.REGION }} \
      --project=${{ env.PROJECT_ID }}
```

---

## DASHBOARD: Visibilidade no Frontend

### Arquivo a modificar
```
AtualizaAI/frontend/src/App.jsx
```

### Adicionar aba "🎓 Broker"

Criar nova aba no menu lateral entre "Quality Inspector" e "FinOps Guardian".

A aba deve exibir:

**Seção 1 — Status de Certificação**

Tabela com todos os agentes gerados mostrando:
- Nome do agente
- Status: `✅ Certificado` / `⏳ Aguardando` / `❌ Reprovado`
- Data da última certificação
- Número de tentativas
- Botão "Ver Gaps" que abre modal com os `knowledge_gaps` do agente

**Seção 2 — Budget do Dia**

Três métricas simples:
- Tokens reservados para o Broker hoje
- Agentes processados hoje
- Agentes na fila

**Seção 3 — Log do Último Ciclo**

Exibir o conteúdo de `logs/broker/cycle_{último}.json` formatado como texto simples.

### Endpoint necessário no backend

Adicionar em `entrypoint.py`:

```python
@app.get("/api/broker/status")
async def get_broker_status(request: Request, token: str = None):
    if not validate_token(request, token):
        return {"error": "Unauthorized"}
    
    gcs = GCSClient(f"flose-ai-platform-{os.getenv('GCP_PROJECT_ID')}", 
                    project_id=os.getenv('GCP_PROJECT_ID'))
    
    registry = gcs.read_json("agents/registry.json") or {"agents": []}
    core_agents = ["FinOpsGuardian", "CognitiveOrchestrator", "VisionAgent", 
                   "AudioAgent", "BriefingAgent", "ReportAgent", 
                   "ProactiveAlertAgent", "EvolutionJob"]
    
    dynamic_agents = [
        a for a in registry.get("agents", []) 
        if a["agent_name"] not in core_agents
    ]
    
    certified = [a for a in dynamic_agents if a.get("certified") == True]
    failed = [a for a in dynamic_agents if a.get("certified") == False]
    pending = [a for a in dynamic_agents if "certified" not in a]
    
    # Buscar último log de ciclo
    last_cycle = None
    try:
        prefix = f"users/{gcs.user_id}/logs/broker/"
        blobs = list(gcs.bucket.list_blobs(prefix=prefix))
        cycle_blobs = [b for b in blobs if "cycle_" in b.name]
        if cycle_blobs:
            cycle_blobs.sort(key=lambda x: x.updated, reverse=True)
            last_cycle = gcs.read_json(
                cycle_blobs[0].name.replace(f"users/{gcs.user_id}/", "")
            )
    except:
        pass
    
    return {
        "summary": {
            "total_dynamic": len(dynamic_agents),
            "certified": len(certified),
            "failed": len(failed),
            "pending": len(pending)
        },
        "agents": dynamic_agents,
        "last_cycle": last_cycle
    }
```

---

## ESTRUTURA DE ARQUIVOS RESUMIDA

```
AtualizaAI/
├── src/
│   └── agents/
│       ├── knowledge_broker_agent.py     ← NOVO
│       ├── broker_knowledge_base.py      ← NOVO
│       └── token_budget_agent.py         ← NOVO
├── entrypoint.py                         ← MODIFICAR (2 endpoints novos)
├── frontend/src/App.jsx                  ← MODIFICAR (nova aba Broker)
└── .github/workflows/deploy.yml          ← MODIFICAR (Cloud Scheduler)
```

---

## CAMPOS NOVOS NO agents/registry.json

Cada agente no array `agents` passa a ter:

```json
{
  "agent_name": "...",
  "certified": true,
  "certified_at": "2026-03-20T00:00:00",
  "certification_attempts": 1,
  "knowledge_gaps": [],
  "last_broker_review": "2026-03-20T00:00:00"
}
```

---

## FLUXO COMPLETO (para o telespectador)

```
Meia-noite todo dia
        ↓
Cloud Scheduler chama /broker_cycle
        ↓
TokenBudgetAgent calcula quantos agentes processar
(baseado no gasto de tokens do dia)
        ↓
KnowledgeBrokerAgent pega a fila priorizada
(mais antigos sem certificação primeiro)
        ↓
Para cada agente: entrevista via Gemini
        ↓
Aprovado → certified: true no registry
Reprovado → system_prompt melhorado + task de auto-melhoria criada
        ↓
Log salvo em logs/broker/
        ↓
Dashboard atualiza automaticamente
        ↓
Você abre a aba Broker e vê o placar
```

---

## OBSERVAÇÕES IMPORTANTES

**Sobre tokens:** Cada entrevista de certificação consome ~2k tokens. Com budget de 50k/dia para o Broker, são ~25 agentes por dia. Se a plataforma tiver 10 agentes, o ciclo completo termina em 1 dia e depois fica só em re-certificação mensal.

**Sobre agentes core:** Nunca certificar ou modificar os agentes core do sistema. A lista de exclusão está hardcoded no `KnowledgeBrokerAgent`.

**Sobre o primeiro ciclo:** Na primeira execução, todos os agentes dinâmicos existentes entrarão na fila como `pending`. O TokenBudgetAgent vai processar em lotes diários até zerar a fila.

**Sobre falhas repetidas:** Agente que falha 3 vezes consecutivas recebe flag `deprecated: true` e uma task de alta prioridade é criada para revisão humana via Telegram. O sistema não deleta agentes automaticamente — só sinaliza.

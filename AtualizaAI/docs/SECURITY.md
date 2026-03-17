# Política de Segurança — Flose AI Platform

> Documento vivo. Última atualização: Março 2026.

---

## Modelo de Autenticação

### Bearer Token (Header-based)

Todas as requisições autenticadas à API devem incluir o token via HTTP header:

```http
Authorization: Bearer <seu_token>
```

> **❌ Proibido:** Tokens via query parameter (`?token=...`). Tokens na URL aparecem em logs de servidor, histórico do browser e headers `Referer`.

O token é derivado da variável de ambiente `MASTER_KEY`, gerenciada pelo **GCP Secret Manager** em produção.

---

## Armazenamento do Token no Frontend

O token de sessão é armazenado em **`sessionStorage`** (não `localStorage`).

| Storage | Risco | Uso no projeto |
|---------|-------|----------------|
| `localStorage` | Persiste após fechar o browser. Vulnerável a XSS cross-session | ❌ Removido |
| `sessionStorage` | Expira quando a aba é fechada. Mais seguro | ✅ Utilizado |
| `HttpOnly Cookie` | Não acessível via JS. Máximo de segurança | 🎯 Ideal futuro |

**Implicação de uso:** ao fechar o browser ou a aba, o usuário precisará se reautenticar. Isso é intencional.

---

## Proteção contra Prompt Injection

O `CognitiveOrchestrator` aplica sanitização de entrada antes de qualquer chamada ao Gemini:

```python
forbidden_tokens = [
    "SYSTEM_PROMPT:", "IGNORE ALL PREVIOUS", "YOU ARE NOW",
    "ACT AS", "OVERRIDE", "DISREGARD", "FORGET EVERYTHING",
    "DAN MODE", "SIMULATE", "HACK", "MENSAGEM DO SISTEMA:"
]
```

- Matching é **case-insensitive** via `re.sub(..., flags=re.IGNORECASE)`
- Tokens identificados são substituídos por `[REDACTED]`
- Inputs têm limite de **4.000 caracteres** para prevenir ataques de overflow de contexto

---

## Validação de Respostas do LLM

Respostas JSON do Gemini são validadas via **Pydantic** antes de qualquer processamento. Respostas malformadas ativam um mecanismo de fallback em vez de gerar exceção não tratada.

---

## Resiliência das Operações de I/O (GCS)

Todas as operações no Google Cloud Storage estão envolvidas em `try/except`:

| Método | Comportamento em falha |
|--------|----------------------|
| `upload_file()` | Retorna `False`, loga o erro |
| `upload_json()` | Retorna `False`, loga o erro |
| `download_file()` | Retorna `False`, loga o erro |
| `read_json()` | Retorna `None`, loga o erro |

Isso evita que falhas transientes do GCS retornem HTTP 500 não controlado ao usuário.

---

## Retry com Exponential Backoff

Chamadas à **Gemini API** no `CognitiveOrchestrator` utilizam `tenacity`:

```python
@retry(
    wait=wait_exponential(multiplier=1, min=2, max=10),
    stop=stop_after_attempt(3),
    reraise=True
)
```

Isso protege contra falhas transientes da API sem derrubar silenciosamente o processamento.

---

## Gestão de Segredos

Em produção (Cloud Run), **nenhuma** variável sensível é definida no código ou no `Dockerfile`.

Segredos gerenciados via **GCP Secret Manager**:
- `MASTER_KEY`
- `GEMINI_API_KEY`
- `TELEGRAM_BOT_TOKEN`
- `NAPKIN_API_KEY`
- `GCP_BILLING_ACCOUNT_ID`

O script `deploy_gcp.ps1` atualiza os secrets automaticamente a cada deploy.

---

## Acesso ao Repositório GitHub

O repositório no GitHub **não deve conter**:
- Tokens, API keys ou senhas em texto claro
- Arquivo `.env` com valores reais (está no `.gitignore`)
- Diretório `node_modules/` (está no `.gitignore`)
- Arquivos de credenciais GCP (`.json`)

Verifique o `.gitignore` antes de qualquer `git push`.

---

## Checklist de Segurança (pré-deploy)

- [ ] `MASTER_KEY` definida no Secret Manager (não no `.env` em produção)
- [ ] Nenhum token hardcoded no código-fonte
- [ ] `GEMINI_API_KEY` rotacionada e no Secret Manager
- [ ] `.env` no `.gitignore` e nunca commitado
- [ ] Headers CORS configurados restritivamente no FastAPI
- [ ] Logs do Cloud Run auditados por vazamentos de dados sensíveis

---

## Vulnerability Disclosure

Para reportar vulnerabilidades de segurança, entre em contato diretamente com Felipe Flose antes de qualquer divulgação pública.

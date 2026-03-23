# TASK-39 | Aba Settings Funcional

## Metadata
| Campo | Valor |
|---|---|
| ID | TASK-39 |
| Grupo | Produto / Configuração |
| Prioridade | Alta |
| Responsável | FrontendAgent |
| Status | Aberto |

## Problema Identificado
A aba "Settings" no menu lateral existe mas não faz absolutamente nada. Cai no fallback genérico:

```
"This module is currently being optimized by the specialized agents."
```

Isso é uma aba morta. Em um sistema que tem GCP Project ID, Gemini Model, Telegram Bot Name e Master Key configuráveis, não ter uma tela de Settings é uma falha de produto grave. O usuário é obrigado a editar variáveis de ambiente para mudar qualquer configuração.

## Objetivo
Implementar a aba Settings com seções organizadas para configurações do sistema, preferências visuais e informações do ambiente — com persistência via API.

## Cenário Real
Usuário entra em Settings → vê o modelo Gemini atual (`gemini-1.5-flash`) → muda para `gemini-2.5-flash` → salva → sistema passa a usar o novo modelo nas próximas chamadas.

## Prompt para Antigravity

```
No `frontend/src/App.jsx`, substituir o fallback da aba 
'Settings' por um componente com 4 seções:

--- SEÇÃO 1: System Configuration ---
Campos editáveis (inputs com style glassmorphism):
- "Gemini Model" (valor atual: stats.model ou env, editável)
- "GCP Project ID" (read-only, mascarado: "flose-ai-****")
- "Active Region" (read-only)
Botão "Save Configuration" → chama `POST /api/settings` 
com `{ gemini_model: value }`

--- SEÇÃO 2: Dashboard Preferences ---
Toggles (switches CSS customizados):
- "Auto-refresh Activity Feed" (default: true)
- "Show Reasoning Chain by default" (default: false)
- "Enable Sound Notifications" (default: false)
Persistir preferências em `localStorage` (não precisa de API)

--- SEÇÃO 3: Security ---
- "Last Login": timestamp formatado
- "Session Token": mascarado como `****...****` com botão 
  "Copy" que copia o token completo para o clipboard
- Botão "Regenerate Session" (chama logout + redirect para login)

--- SEÇÃO 4: About ---
- Versão da plataforma: "v2.1.0"
- Uptime do container: busca de `GET /api/health`
- Total de agentes registrados: `stats.agents`
- Link "View Changelog" (abre `docs/CHANGELOG.md` em modal)

No `entrypoint.py`, criar endpoint `POST /api/settings` que 
atualiza variável de ambiente `GEMINI_MODEL` em runtime 
(usando `os.environ["GEMINI_MODEL"] = new_value`).
```

## Arquivos Envolvidos
- `frontend/src/App.jsx`
- `entrypoint.py` (endpoint POST /api/settings)
- `frontend/src/index.css` (toggle switch styles)

## Critério de Conclusão
- Aba Settings não cai mais no fallback genérico
- Preferências de UI persistem após refresh via localStorage
- Modelo Gemini atualizável sem redeploy
- Token copiável com feedback visual (botão muda para "Copied!")

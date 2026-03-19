# TASK-03 | Agente de Resumo Semanal

## Metadata
| Campo | Valor |
|---|---|
| ID | TASK-03 |
| Grupo | Ideias Novas |
| Prioridade | Média |
| Responsável | ReportAgent |
| Status | Aberto |

## Prompt para Antigravity

```
Criar `src/agents/weekly_report_agent.py` que lê todos os 
`logs/executions/*.json` da semana, sumariza com Gemini e 
envia no Telegram toda segunda-feira às 8h via Cloud Scheduler.
```

## Arquivos Envolvidos
- `src/agents/weekly_report_agent.py` (novo arquivo)
- `entrypoint.py`
- `deploy_gcp.ps1`

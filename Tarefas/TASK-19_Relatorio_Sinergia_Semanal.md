# TASK-19 | Relatório de Sinergia Semanal

## Metadata
| Campo | Valor |
|---|---|
| ID | TASK-19 |
| Grupo | Agentes Colaborativos |
| Prioridade | Média |
| Responsável | ReportAgent |
| Status | Aberto |

## Objetivo
Entender automaticamente quais duplas de agentes colaboram mais e quais estão subutilizados, sem precisar analisar logs manualmente.

## Cenário Real
Toda sexta você recebe: "FinOps + QA colaboraram 8x esta semana. VisionAgent não foi acionado em 5 dias."

## Prompt para Antigravity

```
Criar `src/agents/synergy_report_agent.py` que lê 
`agents/affinity_matrix.json` e `logs/executions/*.json` 
da última semana. Gera com Gemini um relatório identificando: 
quais duplas de agentes mais colaboraram, qual combinação 
gerou melhores resultados e qual agente está isolado (sem 
co-execuções). Enviar via Telegram toda sexta às 17h.
```

## Arquivos Envolvidos
- `src/agents/synergy_report_agent.py` (novo arquivo)
- `entrypoint.py`
- `deploy_gcp.ps1`

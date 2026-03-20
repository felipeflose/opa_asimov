# TASK-21 | Cross-Analysis de Ferramenta via Imagem

## Metadata
| Campo | Valor |
|---|---|
| ID | TASK-21 |
| Grupo | Agentes Colaborativos |
| Prioridade | Média |
| Responsável | VisionAgent |
| Status | Aberto |

## Objetivo
Combinar análise visual com análise especializada em uma única interação — foto de uma ferramenta gera análise técnica e financeira automática.

## Cenário Real
Foto de dashboard de uma ferramenta externa → VisionAgent lê e extrai contexto → FinOpsGuardian avalia custo-benefício da integração.

## Prompt para Antigravity

```
No `telegram_agent.py`, quando uma imagem for enviada com 
texto que contenha "analise" ou "avalie", acionar em sequência: 
VisionAgent (extrai contexto visual) → depois passar o contexto 
para o agente mais adequado pelo tema do texto. Salvar o 
resultado dual em `logs/cross_analysis/{timestamp}.json`.
```

## Arquivos Envolvidos
- `src/agents/telegram_agent.py`
- `src/agents/vision_agent.py`

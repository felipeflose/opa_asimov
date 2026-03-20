# TASK-32 | Aba /cozinha no Dashboard

## Metadata
| Campo | Valor |
|---|---|
| ID | TASK-32 |
| Grupo | Cozinha (Modo Dev) |
| Prioridade | Média |
| Responsável | FrontendAgent |
| Status | Aberto |

## Objetivo
Trazer o modo dev também para o dashboard web, com visibilidade de todos os endpoints e capacidade de testá-los inline.

## Prompt para Antigravity

```
No `frontend/src/App.jsx`, adicionar aba `🔧 Cozinha` no menu 
lateral. Exibir: lista de todos os endpoints com método HTTP, 
path e último status code registrado. Adicionar botão `Testar` 
ao lado de cada um que chama o endpoint e exibe o response 
inline na tela, sem redirecionar.
```

## Arquivos Envolvidos
- `frontend/src/App.jsx`
- `entrypoint.py`

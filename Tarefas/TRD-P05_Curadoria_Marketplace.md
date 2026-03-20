# TRD-P05 | Curadoria do Agent Marketplace

## Metadata
| Campo | Valor |
|---|---|
| ID | TRD-P05 |
| Grupo | Produto |
| Prioridade | Baixa |
| Responsável | QualityInspector |
| Status | Conclu�do |

## Objetivo
Aumentar a utilidade do Marketplace adicionando contexto suficiente para o usuário decidir se quer importar um template antes de clicar.

## Prompt para Antigravity

```
No `entrypoint.py`, no endpoint `GET /api/marketplace`, adicione os 
campos `description`, `use_cases` (array de strings) e `category` 
ao schema de cada template retornado. No `frontend/src/App.jsx`, 
na aba Marketplace, exiba esses campos em um tooltip ou card expandido 
antes do botão de importar.
```

## Arquivos Envolvidos
- `entrypoint.py`
- `frontend/src/App.jsx`

## Critério de Conclusão
- Templates retornando os 3 novos campos
- Card expandido no Marketplace exibindo descrição e casos de uso

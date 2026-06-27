# OpenClaw Vault — Instructions for Claude Code

## O que é esse Vault?
Base de conhecimento centralizada do projeto OpenClaw (Flose). Memória de longo prazo que persiste entre sessões, formatada com metodologia Zettelkasten e geração local de grafos.

## Regras de Zettelkasten
### Criação de Notas
- Use sempre wikilinks: `[[nome-da-nota]]` (não use links do padrão markdown).
- Formate arquivos em kebab-case: `auth-flow.md`, não `Auth Flow.md`.
- No máximo 1 conceito fechado por nota na pasta `permanent/`.
- Priorize um Frontmatter (YAML) no cabeçalho em todas as notas.

### Exemplo de Frontmatter Obrigatório
```yaml
---
title: Nome da Nota
tags: [openclaw, topic]
created: YYYY-MM-DD
updated: YYYY-MM-DD
status: active
type: permanent
---
```

## Comandos de Sessão
### /resume
Quando receber esse comando numa nova sessão de terminal:
1. Leia as 3 notas mais recentes na pasta `logs/` no formato `YYYY-MM-DD-*.md`.
2. Busque referências soltas sobre a arquitetura para relembrar o sistema OpenClaw.
3. Resuma para o usuário o estado atual e o que ficou pendente.

### /save
Quando receber esse comando:
1. Crie uma nota em `logs/YYYY-MM-DD-descricao-curta.md` detalhando exatamente o que foi implementado na sessão, as decisões tomadas arquiteturais e o que sobrou.
2. Crie ou altere notas na pasta principal ou `permanent/`, e coloque `[[wikilinks]]` no log para referenciar os temas de trabalho.
3. Se o código for alterado, sugira ou rode `git commit + push`.

## Graphify (Codebase Maps)
### Estrutura
- `graphify/` -> Onde fica a "memória de código livre de tokens".
- As notas de código em `graphify` são auto-geradas por AST. **Não edite manualmente**.

## Filtros Dica
- `tag:chat-import` revela as memórias resgatadas de instâncias diversas do Claude.
- `path:graphify` foca apenas nos grafos da codebase.

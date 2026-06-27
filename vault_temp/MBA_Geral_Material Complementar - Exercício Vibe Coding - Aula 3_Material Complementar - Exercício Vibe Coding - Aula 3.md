## Exercício Vibe Coding

## Motor de Qualificação de Leads para Análise em Planilha (CSV)

## Objetivo do projeto:

A sua missão é desenvolver um Motor de Lead Scoring em Python. Este script deve tomar decisões sobre a qualidade de um lead e, crucialmente, formatar o resultado em um formato padrão (CSV/Planilha) para que o time de Operações de Marketing possa importá-lo facilmente e realizar análises de segmentação e enviar um email de ativação aos leads quentes.

## Requisitos Técnicos do Código:

Seu código deve seguir estas 3 etapas lógicas, utilizando variáveis e lógica condicional (if/elif/else):

## 1. INPUT (ENTRADA DE DADOS)

O código deve solicitar e capturar os seguintes dados do usuário (o Lead):

- Nome do Lead (string)
- Segmento (Ex: Tech, Retail, Services) (string)
- Pontuação de Engajamento (Um número inteiro entre 0 e 100) (integer)

## 2. PROCESSAMENTO (A LÓGICA DE SCORING)

O código deve aplicar a seguinte lógica para classificar o lead:

- Se a Pontuação for $\ge 70$: Classificar como SQL (Sales Qualified Lead) .
- Se a Pontuação for $\ge 40$ e $&lt; 70$: Classificar como MQL (Marketing Qualified Lead) .
- Se a Pontuação for $&lt; 40$: Classificar como Lead Frio .
- Ação de Marketing: Gerar uma Frase de E-mail Personalizada (uma string diferente para cada Status de Lead, utilizando o Nome e o Segmento).

## 3. OUTPUT (SAÍDA PARA ANÁLISE)

O código deve gerar DOIS resultados de saída:

## A. Output de Usuário (Para Visualização Imediata):

- Imprimir de forma amigável o Status Final do Lead e a Frase de E-mail Personalizada gerada.

## B. Output para Planilha (O Formato CSV):

- Este é o requisito mais importante para o time de Análise. O código deve imprimir uma única linha de dados, onde cada informação esteja separada por ponto e vírgula (;) .
- Formato de Saída (CSV): Nome;Segmento;Pontuacao;Status\_Final;Email\_Personalizado

## Exemplo de Saída Desejada (Planilha)

Se o nome for "João", o segmento for "Tech" e a pontuação for "85", o código deve imprimir exatamente:

João;Tech;85;SQL;Olá João, baseado no seu recente interesse em Tech, nossa equipe de vendas quer agendar 15min.

## Desafio Extra (Vibe Check)

Adicione uma formatação monetária (R$ XX.XX) se conseguir encaixar uma variável de "Valor de Contrato Estimado" na lógica de saída!

Com este prompt, os alunos têm os requisitos técnicos e de negócio bem definidos, focando na importância de estruturar os dados para análise posterior.
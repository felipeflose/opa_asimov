## Explorando a API da OpenAI

Asimov Academy

<!-- image -->

Parâmetro messages . . . . . . . . . . . . . Analisando a classe de resposta do modelo .

<!-- image -->

Analisando a mensagem de resposta

.

.

.

.

.

.

.

.

.

.

.

.

.

.

.

.

.

.

.

.

.

.

.

.

.

.

.

.

.

.

.

.

.

22

23

24

.

.

.

.

.

.

.

.

.

.

.

.

.

.

.

.

.

.

.

.

.

.

.

.

.

.

.

.

.

.

.

.

.

.

.

.

.

.

.

.

Demais parâmetros do método chatcompletion . . . . . . . . . . . . . . . . . . . . . 25

06. Gerando uma stream de texto

07. DESAFIO - Criando um Chatbot em Python

08. Adicionando funções e ferramentas externas

Definição de funções externas

.

.

.

.

.

.

.

.

.

28

30

32

34

.

.

.

.

.

.

.

.

.

.

.

.

.

.

.

.

.

.

.

.

.

.

.

.

.

## Explorando a API da OpenAI

<!-- image -->

Comparando o modelo com Fine-Tuning e o modelo padrão

13. Apresentando a Assistants API para geração de texto avançada

Criando um Assistant .

.

.

.

.

.

.

.

.

.

.

.

.

.

.

.

.

.

.

.

.

.

.

.

.

.

.

.

.

.

.

.

.

.

.

.

.

.

.

.

.

.

.

.

.

.

.

.

.

.

.

.

.

48

50

50

Criando um Thread . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 51 Adicionando mensagem a Thread . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 51

Solicitando ao Assistant para rodar uma Thread

## Esperando a Thread rodar

Verificando a resposta

.

.

.

.

.

.

.

.

.

.

.

.

.

.

.

.

.

.

.

.

.

.

.

.

.

.

.

.

.

.

.

.

.

.

.

.

.

.

.

.

.

.

.

.

.

.

.

.

.

.

.

.

.

.

.

.

.

.

.

.

.

.

.

.

.

.

.

.

.

.

.

.

.

.

.

.

.

.

.

.

.

.

.

.

.

.

.

.

.

52

52

52

Analisando os passos de processamento do Assistant . . . . . . . . . . . . . . . . . . 53 14. Analisando dados com Assistants Code Interpreter 56

Enviando arquivos para o Assistant . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 56 Verificando os passos . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 58

Gerando gráficos com Assistants .

.

.

.

.

.

15. Analisando arquivos pdf com File Search

16. Criando e editando imagens com Dall-e

Criando uma imagem .

.

.

.

.

.

Salvando a imagem gerada

Visualizando a imagem .

.

.

.

.

.

.

.

.

.

.

.

.

.

.

.

.

.

.

.

.

.

.

.

.

.

.

.

.

.

.

.

.

.

.

.

.

.

.

.

.

.

.

.

.

.

.

.

.

.

.

.

.

.

.

.

.

.

.

.

.

.

.

.

.

.

.

.

.

.

.

.

.

.

.

.

.

.

.

.

.

.

.

.

.

.

.

.

.

.

.

.

.

.

.

.

.

.

.

.

.

.

.

.

.

.

.

.

.

.

.

.

.

.

.

.

.

.

.

.

.

.

.

.

.

.

.

60

63

67

67

68

68

<!-- image -->

20. Mini-projeto - Chatbot com reconhecimento de fala

21. Finalizando o curso

86

88

Olá e bem-vindos ao nosso curso 'Explorando a API da OpenAI'! Estou super animado por ter vocês aqui e mal posso esperar para explorarmos juntos esse universo fascinante da programação e da

inteligência artificial.

Vocês já devem ter percebido que a IA está mudando o jogo em muitos campos, certo? É incrível como ela está transformando a maneira como lidamos com informações e realiza tarefas que antes pareciam

exclusivas da mente humana. E o mais legal é que não estamos apenas assistindo a essa mudança;

vamos fazer parte dela!

Com a API da OpenAI, temos a chance de interagir com alguns dos modelos de IA mais avançados que existem. E ao conciliarmos o poder desses modelos com as capacidades da programação Python,

damos um salto para o futuro.

Ao longo deste curso, vamos aprender a usar essa API para realizar tarefas incríveis, como criar textos, gerar imagens e transcrever áudios. E o mais bacana é que vamos fazer tudo isso de um jeito bem

prático, escrevendo nosso próprio código e vendo a mágica acontecer na frente dos nossos olhos.

Python é a ferramenta perfeita para isso. Ela é simples, direta e nos permite focar no que realmente importa: criar aplicações incríveis. E quando você combina essa simplicidade com o poder da IA, as

possibilidades são praticamente infinitas.

Então, se vocês estão tão empolgados quanto eu para começar a explorar o que a IA pode fazer e como podemos usá-la para expandir nossas habilidades de programação, vocês estão no lugar certo. Vamos

aprender, nos impressionar e, quem sabe, até criar algo que nunca imaginamos ser possível.

Sejam bem-vindos! Vamos nessa juntos e ver até onde podemos chegar com a API da OpenAI e nosso

<!-- image -->

querido Python.

<!-- image -->

que consta no cardápio (a documentação da API) e como fazer o pedido (como utilizar a API).

No contexto dos modelos de linguagem de grande escala (LLM), uma API é frequentemente disponi-

bilizada por provedores como a OpenAI para simplificar o acesso aos modelos. Por exemplo, uma

API pode permitir que você envie um texto e, em resposta, receba uma continuação coerente desse texto gerada pelo modelo, uma resposta a uma pergunta ou uma tradução. Isso possibilita que de- senvolvedores, mesmo aqueles com conhecimentos básicos de programação como você, integrem

funcionalidades de inteligência artificial avançadas em seus próprios aplicativos sem a necessidade de construir e treinar seus próprios modelos. Tal processo exigiria não apenas recursos computacionais

significativos, mas também expertise especializada.

E a utilização dessas APIs que serão o foco do nosso curso!

db

Documentation

Q Search!

GET STARTED

Overview

Introduction

Quickstart

Models

Tutorials

Changelog

CAPABILITIES

Text generation

Function calling

Embeddings

Fine-tuning

Image generation

Vision

Text-to-speech

Speech-to-text

Moderation

ASSISTANTS

Overview

How Assistants work

Tools

Prompt engineering

Production best practices

Safety best practices

Rate limits

API reference

Welcome to the OpenAl developer platform

Start with the basics

## Explorando a API da OpenAI

Quickstart tutorial

Make your first Chat Completions API request

Prompt examples

Explore what OpenAl models can do with prompts

Acessando a documentação da API

<!-- image -->

Para acessar a API da documentação, basta clicar aqui.

@ Forum

• Help

do |

Documentation

Documentation

Q Search

GET STARTED

Overview

Overview

Introduction

Quickstart

Models

Models

Tutorials

Changelog|

GPT-4

CAPABILITIES

Text generation

DALLE

Chat Completions

TTS I

JSON mode

Reproducible outputs

Managing tokens

Parameter details

Completions API (Legacy) |

ita

FAQ

lity

Function calling

Tutorials

Embeddings

Fine-tuning

Image generation

Vision I

Text-to-speech

Speech-to-text

Moderation

API reference

API reference

стк. K

3

Models

Text generation models

OpenAl's text generation models (often called generative pre-trained transformers or large language

Overview outputs in response to their inputs. The inputs to these models are also referred to as "prompts". Designing

models) have been trained to understand natural language, code, and images. The models provide text

The OpenAI API is powered by a diverse set of models with different capabilities and price points. You can also make customizations to our models for your specific use case with fine-tuning.

a prompt is essentially how you "program" a large language model model, usually by providing instructions

• Draft documents natural language or code

• Write computer code

GPT-3.5 Turbo

A set of models that improve on GPT-3.5 and can understand as well as generate natural language or code

<!-- image -->

Modelos

Na página de modelos, você pode ver a descrição completa de todos os modelos disponíveis hoje da

OpenAI.

• Answer questions about a knowledge base

• Forum|

@ Forum

• Help

© Help

careles uneletiteo.

ur cuUnNuUn.

Documentation

APl reference

OpenAl Cookbook

New APIs

Processing and narrating a video with

GPT's visual capabilities and the TTS API

Kai Chen

Q Search....

standard English.

Creating slides with the Assistants API

Using logprobs and DALL-E 3

Parse unstructured data

Exemplos de prompts

Dec 8,2023

Na página de exemplos, você pode verificar alguns prompts simples mas eficientes para diversas tarefas diferentes:

vinr

Jun 13, 2023

How to stream completions

Ted Sanders

Cookbook

A OpenAI fornece a explicação completa de diversos projetos desenvolvidos pela sua equipe na página de Cookbook.

About

API Docs

Prompt examples

Explore what's possible with some example prompts

What's new with DALL-E 3?

Assistants API Overview (Python SDK)

Will Depue

All categories

Simplify text to a level appropriate for a second-grade student.

Using GPT4 with Vision to tag and caption images

<!-- image -->

Emoji Translation

Ilan Bigio

ASSISTANTS FUNCTIONS

Contribute Q

@ Forum

Q Search....

• Help|

* K

API reference

Documentation

Fine-tuning

Image generation

Vision

Text-to-speech

Speech-to-text

Moderation

ASSISTANTS

Overview

How Assistants work

Tools

GUIDES

Prompt engineering

Six strategies for getting better results

Write clear instructions

Provide reference text

Split complex tasks into simpler subtasks

Give the model time to

"think"

lica ayternal tanle

Test changes systematically

Other resources

Production best practices

Safety best practices

Rate limits

Prompt engineering

This guide shares strategies and tactics for getting better results from large language models (sometimes referred to as GPT models) like GPT-4. The methods described here can sometimes be deployed in

combination for greater effect. We encourage experimentation to find the methods that work best for you.

Some of the examples demonstrated here currently work only with our most capable model, gpt -4. In

You can also explore example prompts which showcase what our models are capable of:

Prompt examples

Explore prompt examples to learn what GPT models can do

<!-- image -->

• Forum|

© Help

## Explorando a API da OpenAI

<!-- image -->

adicionar saldo para prosseguir.

Limites de uso gratuito

Nesta página, você pode verificar todas as limitações de uso por tipo de modelo. Os limites são portanto:

Modelo

RPM

RPD

TPM

gpt-3.5-turbo 3 200 40,000 text-embedding-3-small 3 200 150,000

whisper-1 3 200 - tts-1

dall-e-2

dall-e-3

3

5 imagem/min

1 imagem/min

200

-

-

-

-

-

Sendo: - RPM: requisições por minuto - RPD: requisições por dia - TPM: tokens por minuto

Você pode perceber que modelos mais avançados como o GPT-4 não está disponível a nível gratuito.

lyground sistants

le-tuning

I keys

›rage age

• !!!!!!!!unt ttings

ganization am

Documentation |

• Help nits

88 All products

Personal ling

ofile

Billing settings

Overview

Payment methods

Billing history Preferences

Overview

Payment methods

Free trial

Credit remaining ©

$0.00

Add payment details

Free trial

View usage

Payment methods

<!-- image -->

Billing history

Depois é só clicar em Add Payment details:

Clicar em Individual, caso for um cartão em nome de uma pessoa física:

Billing history

Preferences

ion

Pay as you go

19

ChatGPT account.

Credit balance ®

$12.90

Billing hist

View past ar

When your credit balance reaches $0, your API requests will stop working. Enable automatic recharge to automatically keep your credit balance topped up.

Enable auto recharge

Usage limi

Set monthly

Add to credit balance

Payment methods

Add or change payment method

Preferences

Manage billing information

E aparecerá uma tela para você adicionar suas informações de cartão. Após adicionado, será possível aportar saldo a sua conta, clicando em Add to credit balance:

<!-- image -->

Selecionando o valor e adicionando:

s will stop working. Enahle automatin ped up.

Add to credit balance

<!-- image -->

Billing hist

View past ar

Usage limi

Set monthly adicionou um limitador de custos mensais na aba de limits.

• Storage

Playground db Usage

• Assistants

Fine-tuning

{ Settings.

@ API keys |

Organization

Storage

Team

‹ Usage

Limits

@ Settings

Billing

Profile

Cost

Activity

Monthly Spend $29,15

Usage limits

Manage your API spend by configuring monthly spend limits. Notification emails will be sent to

## Explorando a API da OpenAI

$4

06 Mar

Usage limit

$6.04

$5.06

&lt;$0.01

No momento que você criu uma aplicação utilizando as APIs, será importatne monitorar os custos que

<!-- image -->

você está tendo por dia e por modelo diferente. Isso é possível na aba

Usage

.

Passando o mouse sobre o gráfico podemos verificar o custo por cada modelo.

Show all models

Model

Model

Quality

DALLE 3

gpt-4-0125-preview

Standard

DALL-E 3

gpt-4-1106-vision-preview

HD

DALLE 2

Input

Resolution

1024×1024

$10.00 / 1M tokens

1024×1024

$10.00 / 1M tokens

Output

Price

$0.040 / image

$30.00 / 1M tokens

$30.00 / 1M tokens

$0.080 / image

$30.00 / 1M tokens

$0.080 / image

(resposta do modelo).

<!-- image -->

Os diferentes modelos têm diferentes precificações. No caso dos modelos de imagem, a cobrança é

feita por imagem gerada:

Modelo de áudio para texto como o

Whisper

áudio cobram por caractere convertido:

cobram por minuto transcrito e modelos de texto para

Model

Whisper

TTS

TTS HD

Usage

$0.006 / minute (rounded to the nearest second)

$30.00 / 1M characters

<!-- image -->

Para associar as chamadas que você realiza à sua conta da OpenAI, é necessário gerar uma chave de

<!-- image -->

API (API key) e fornecê-la ao inicializar a biblioteca. Para criar essa chave, você deve retornar ao site da

OpenAI. Vamos até a aba de API Keys e cliacamos em Create new secreat key :

ET KEY

• Playground

.. 139C

Q Assistants.

* Fine-tuning

. . MChd

@ API keys

8 Storage db Usage

API keys

TRACKING •

+ Enable

CREATED

LAST USED •

PERMISSIONS

Your secret API keys are listed below. Please note that we do not display your secret API keys again after you generate them.

28 de nov. de 2023 13 de mar. de 2024 All

Do not share your API key with others, or expose it in the browser or other client-side code. In order to protect the security of your

14 de dAz de 2A02 12 da mar de onos All account, OpenAl may also automatically disable any API key that we've found has leaked publicly.

+ Enable

## Explorando a API da OpenAI

NAME

AsimoChat\_server

Settings is setting controls which o

e for each APl request. See Auth

SECRET KEY

sk-...r39C

TRACKING O

+ Enable

CREATED

го. m

LAST USED O

PERMISSIONS

28 de nov. de 2023 13 de mar. de 2024 All

<!-- image -->

Após a criação da chave, o valor será exibido para você. É essencial que você guarde esse valor de forma segura e não o divulgue, pois ele só aparecerá uma vez. Depois de clicar no botão 'done', não

será mais possível verificar o valor da chave, então, certifique-se de salvá-lo imediatamente!

Name Optional

sage page.

TRACKING

+ Enable

+ Enable

Enabled g controls which o

API request. See Auth

CREATED

LAST USED ®

PERMISSIONS

28 de nov. de 2023 13 de mar. de 2024 All

<!-- image -->

Perfeito, agora temos nossa key, biblioteca instalada e podemos inicializar nosso primeiro cliente.

Inicializando o cliente

Oclinete é a classe de comunicação com todos os recursos da API. Para inicializá-lo, será necessário termos em mão nossa api\_key e rodar o seguinte comando:

import api\_key

openai

=

=

'XXXXXXXXXXXXX'

client openai.Client(api\_key=api\_key)

Porquestõesdesegurança,érecomendávelnãoexpornossaschavesdeAPInosscriptsqueescrevemos.

Para evitar essa exposição, podemos utilizar a biblioteca arquivo

python-dotenv

, que permite ler um e definir as variáveis contidas nele como variáveis de ambiente. Primeiro, criamos nosso

arquivo

.env com o seguinte conteúdo:

OPENAI\_API\_KEY=XXXXXXXXXXXXXXXXXXXXX

.env

Você deve adicionar no valor em X a sua chave de API. Após isso, vamos instalar a biblioteca python- dotenv:

pip install python-dotenv

from dotenv import

\_

=

load\_dotenv(find\_dotenv())

import openai

\_

from dotenv import

=

load\_dotenv(find\_dotenv())

client

=

openai.Client()

Observe que, com essa abordagem, não é necessário referenciar a sua API key diretamente no código, pois a biblioteca da OpenAI buscará automaticamente a chave entre as variáveis de ambiente. Se a

<!-- image -->

<!-- image -->

resposta

=

client.chat.completions.create(

model='gpt-3.5-turbo-0125',

messages=mensagens,

max\_tokens=1000, temperature=0, )

mensagem\_resp

=

resposta.choices[0].message print(mensagem\_resp.content)

Vermelha ou

verde.

ChatGPT 3.5 v

•

•

You

O que é uma maçã em até 5 palavras?

## Explorando a API da OpenAI

<!-- image -->

Analisando o script inicial

Parâmetro messages

Para comunicar-se com o modelo, utilizamos o parâmetro

## de dicionários ao método

messages

. É necessário fornecer uma lista do client. Cada dicionário contém duas

chaves principais: content , que é o conteúdo da mensagem, e role , que define o papel de quem está enviando a mensagem. A chave role pode ter três valores distintos:

chat.completions.create

· system : A mensagem de sistema é usada para orientar o comportamento do assistente. Por exemplo, é possível alterar a personalidade do assistente ou dar instruções específicas sobre como ele deve agir durante a conversa. Vale ressaltar que a mensagem de sistema é opcional, e

a ausência dela pode resultar em um comportamento padrão do modelo, semelhante ao que ocorreria com uma mensagem genérica como 'Você é um assistente prestativo'.

user

: As mensagens de usuário são as solicitações ou comentários que o assistente deve responder.

assistant

: As mensagens do assistente representam as respostas anteriores ou podem ser criadas pelo usuário para exemplificar o comportamento desejado do modelo. Isso é útil, por

<!-- image -->

)

mensagem\_resp = resposta.choices[0].message

print(mensagem\_resp.content)

Negativo

Analisando a classe de resposta do modelo

Podemos observar que a resposta do modelo é sempre retornada no mesmo tipo de dado: a classe

ChatCompletion import

da biblioteca da OpenAI:

openai

\_

from dotenv import

=

load\_dotenv(find\_dotenv())

client

=

load\_dotenv, find\_dotenv

openai.Client()

mensagens

= [{'role':

'user', 'content': 'O que é uma maçã em até 5 palavras?'}]

messages=mensagens, resposta

=

client.chat.completions.create(

model='gpt-3.5-turbo-0125', max\_tokens=1000,

)

temperature=0, print(type(resposta))

Ela possui algumas propriedades interessantes:

•

id print(resposta.id)

chatcmpl-92frfZEkVrXD3yCTiEAJNPumPR8L6

•

usage print(resposta.usage)

CompletionUsage(completion\_tokens=9, prompt\_tokens=21, total\_tokens=30)

•

choices print(resposta.choices)

[Choice(finish\_reason='stop', index=0, logprobs=None, message=ChatCompletionMess e depois o

saborosa.', role='assistant', parâmetro

message mensagem\_resp

print(mensagem\_resp)

ChatCompletionMessage(content='Fruta

<!-- image -->

Analisando a mensagem de resposta

A resposta final é fornecida pela classe ChatCompletionMessage. Esta classe tem quatro propriedades:

content , role , function\_call e tool\_calls . Por ora, vamos focar apenas nas duas primeiras propriedades. Os termos content e role já são familiares, pois correspondem ao mesmo formato que utilizamos para enviar a mensagem inicial. Para incorporar a resposta do modelo à nossa men- sagem original, poderíamos proceder de duas maneiras:

mensagem\_resp

=

resposta.choices[0].message mensagens.append({'role': mensagem\_resp.role, 'content': mensagem\_resp.content})

Ou utilizando o método da classe ChatCompletionMessage para transformar a resposta em um di- cionário:

mensagens.append(mensagem\_resp.model\_dump(exclude\_none=True))

fun

Overview

Introduction

Quickstart

Models

Overview

Model updates

GPT-4|

GPT-3.5 Turbo

DALL-E

TTS

Whisper

Embeddings

Moderation I

GPT Base

Lances and canoe deta

Models

Overview

The OpenAI API is powered by a diverse set of models with different capabilities and price points. You can also make customizations to our models for your specific use case with fine-tuning.

natural language or code

GPT-3.5 Turbo

A set of models that improve on GPT-3.5 and can understand as well as generate

<!-- image -->

gpt-4-vision-preview

128,000 tokens

gpt-4-1106-vision-preview

128,000 tokens

Up to Apr 2023

Up to Apr 2023

gpt-4 8,192 tokens Up to Sep 2021

No método chatcompletion.create

max\_tokens

, basta passar uma string com o nome do modelo para utilizá-lo.

Oparâmetro max\_tokens

representa o tamanho máximo da resposta. Ele serve como umamedida de proteção contra custos excessivos da API, mas também pode resultar em respostas

incompletas se o limite for muito baixo.

## Explorando a API da OpenAI

mensagens += [{'role': 'user', 'content': 'E qual a sua cor?'}]

<!-- image -->

mensagens

+=

[mensagem\_resp.model\_dump(exclude\_none=True)]

resposta messages=mensagens,

)

=

client.chat.completions.create(

model='gpt-3.5-turbo-0125', max\_tokens=100, temperature=0,

## mensagem\_resp = resposta.choices[0].message

print(mensagem\_resp.content)

Vermelha ou verde.

mensagens += [mensagem\_resp.model\_dump(exclude\_none=True)] mensagens += [{'role': 'user', 'content': 'E qual a sua cor?'}]

resposta

=

client.chat.completions.create(

model='gpt-3.5-turbo-0125', messages=mensagens,

max\_tokens=100,

)

temperature=2, mensagem\_resp

=

resposta.choices[0].message print(mensagem\_resp.content)

basevoirizeísticaJD\_Wind

<!-- image -->

FavoritesP

A

You

Crie uma história de dois parágrafos sobre uma viagem a marte

06. Gerando uma stream de texto

É possível perceber que, ao utilizar a API conforme aprendido na última aula, o modelo gera a resposta completaantesdefornecê-la. Isso difere da experiência ao usar a interface do ChatGPT, onde a resposta

parece ser construída de maneira mais interativa.

<!-- image -->

You

Crie uma história de dois parágrafos sobre uma viagem a marte

G ChatGPT

Em uma era em que a exploração espacial se tornara rotineira, um grupo de pioneiros embarcou em uma jornada épica em direção a Marte. A nave, equipada com tecnologia de ponta, cortava o

vazio do espaço, levando consigo sonhos, esperanças e o espírito intrépido dos exploradores. À

medida que se aproximavam do Planeta Vermelho, a ansiedade se misturava com a excitação de pisar em um mundo completamente novo, desafiando os limites da imaginação humana. Com

corações palpitando de emoção, eles finalmente tocaram a superfície marciana, prontos para desvendar seus segredos e deixar sua marca na história interplanetária. •

Observamos que a interface do ChatGPT exibe cada novo token gerado, criando uma interação mais dinâmica com o usuário. Felizmente, é possível reproduzir esse mesmo efeito na API utilizando o

parâmetro import

from stream

openai dotenv

import

.

load\_dotenv, find\_dotenv

<!-- image -->

(.venv) python 07\_desafio.py

Bem-vindo ao ChatBot da Asimov. Digite sua mensagem abaixo!

User: Olá, modelo! Como você vai?

Assistant: Olá! Estou bem, obrigada. Como posso ajudar você hoje?

User: Você tem um nome?

Assistant: Não tenho um nome específico, mas você pode me chamar de assistente virtual. Com

## Explorando a API da OpenAI

Assistant: Que tal me chamar de Sophia? É um nome bonito e fácil de lembrar. O que acha?

def retorna\_resposta\_modelo( mensagens

<!-- image -->

resposta

=

client.chat.completions.create(

temperature=0,

):

messages=mensagens, model='gpt-3.5-turbo-0125', max\_tokens=1000,

## stream=True, )

mensagem\_resp = '' print('Assistant: ', end='') for stream\_resp in resposta:

if print(stream\_resp.choices[0].delta.content, end='') mensagem\_resp += stream\_resp.choices[0].delta.content print()

stream\_resp.choices[0].delta.content:

mensagens.append(

)

{'role': 'assistant', 'content': mensagem\_resp}

return main():

print('Bem-vindo ao ChatBot da Asimov. Digite sua mensagem abaixo!')

mensagens mensagens

=

[]

def

<!-- image -->

Umadaslimitaçõesdeummodelodelinguageméasuacapacidadedeacessarinformaçõesatualizadas.

Isso ocorre porque o modelo é treinado com dados históricos e, após ser colocado em operação, não continua seu treinamento. Por exemplo, o GPT-4 tem informações atualizadas até dezembro de 2023, e

o GPT-3 até setembro de 2021. No entanto, não há motivo para preocupação, pois existe uma solução incrível para obter respostas atuais mesmo sem esses dados na base de conhecimento do modelo: o

acesso a ferramentas externas.

Os modelos mais recentes têm a funcionalidade de chamada de funções (function calling). Essas funções podem coletar informações atualizadas para serem processadas pelo modelo ou até mesmo

permitir que o próprio modelo execute ações, como enviar e-mails, adicionar valores a uma base de dados, entre outras possibilidades.

A seguir, vamos apresentar um exemplo prático dessa funcionalidade e, depois, analisaremos cada etapa detalhadamente:

import json

import openai

from dotenv import

\_

=

load\_dotenv(find\_dotenv())

client openai.Client()

def

=

obter\_temperatura\_atual(local, if

elif

<!-- image -->

"são paulo"

return

{"local": "São Paulo", "temperatura":

"porto json.dumps(

alegre"

in return json.dumps( {"local": "Porto Alegre", "temperatura": "25", "unidade": unidade}

:

return

{"local":

)

[

"type":

"function":

local, json.dumps(

"function",

{

local.lower():

) elif "rio de janeiro" in local.lower(): return json.dumps( {"local": "Rio de Janeiro", "temperatura": "35", "unidade": unidade} )

else tools

{

=

)

"temperatura":

"32",

"unknown"}

"unidade":

unidade}

for tool\_call in tool\_calls: function\_name = tool\_call.function.name

<!-- image -->

mensagens.append(mensagem\_resp)

function\_to\_call

=

funcoes\_disponiveis[function\_name]

function\_response = function\_to\_call( local=function\_args.get("local"), unidade=function\_args.get("unidade"), function\_args

=

)

{

json.loads(tool\_call.function.arguments)

mensagens.append(

"tool\_call\_id":

tool\_call.id,

"name":

function\_name,

"role":

"tool",

"content":

function\_response,

## Explorando a API da OpenAI

real.

<!-- image -->

def obter\_temperatura\_atual(local,

if

"são paulo"

elif elif

local.lower():

"porto in

return json.dumps( {"local": "São Paulo", "temperatura": "32", "unidade": unidade} )

in alegre"

unidade="celsius"):

local.lower():

return

## {"local": "Porto

"rio json.dumps(

de janeiro"

Alegre",

"temperatura":

in return json.dumps( {"local": "Rio de Janeiro", "temperatura": "35", "unidade": unidade} )

)

local.lower():

else : return json.dumps( {"local": local, "temperatura": "unknown"}

Para garantir que a função retorne uma string, permitindo assim o processamento subsequente da informação pelo modelo, convertemos a saída em formato JSON. Isso é feito utilizando a função

json.dumps

, uma vez que o JSON é um formato de texto amplamente utilizado em APIs para a troca de dados.

)

"25",

"unidade":

unidade}

<!-- image -->

properties

: Cada chave dentro de properties representa um argumento da função,

e cada um é definido por:

·

: O tipo de dado do argumento (por exemplo, string, int, etc.).

· description : Uma breve descrição do argumento. · enum : Uma lista de valores pré-definidos entre os quais o argumento deve ser type

selecionado, se aplicável.

Comisso, temos uma estrutura organizada que permite ao ChatGPT identificar e utilizar as funções que desenvolvemos.

tools

=

[

"type":

{

"function":

"function",

"name":

{

"description":

"obter\_temperatura\_atual",

"parameters":

"Obtém

"type":

{

"properties":

a

temperatura

"object",

"local":

{

{

"type":

"string",

},

"description":

"unidade":

"O

nome

"type":

},

"enum":

},

{

["celsius",

"required":

["local"],

"fahrenheit"]

"string",

*

}, atual

da em

cidade.

uma

Ex:

dada

São cidade",

Paulo",

}

]

É importante observar que utilizamos uma lista de dicionários para descrever as ferramentas disponíveis. Se desejarmos incluir mais de uma função, basta adicionar um novo dicionário à lista,

detalhando a nova função.

pretende disponibilizar, seguindo o mesmo formato estrutural para garantir a consistência e a compreensão adequada pelo modelo.

Chamando

Para informar o modelo sobre as novas funções disponíveis, devemos passar a lista de ferramentas que construímos anteriormente como argumento no parâmetro tools. Isso permite que o modelo re-

conheça e interaja com as funções que adicionamos, expandindo suas capacidades de processamento e resposta.

mensagens

= [

"content":

{"role":

]

resposta

=

messages=mensagens, model="gpt-3.5-turbo-0125",

tools=tools,

)

<!-- image -->

tool\_choice="auto",

Oparâmetro tool\_choice

possui o valor 'auto' como padrão, o que permite ao modelo decidir automaticamente qual ferramenta utilizar. No entanto, se quisermos direcionar o modelo para usar

umafunção específica que criamos, podemos alterar o valor padrão de tool\_choice da nossa função. Isso forçará o modelo a utilizar a ferramenta que especificamos. Entendendo o parâmetro tool\_calls da resposta do modelo

Para o chamado que realizamos, a resposta do modelo foi:

mensagem\_resp

=

resposta.choices[0].message print(mensagem\_resp)

ChatCompletionMessage(content=None, role='assistant', function\_call=None, para o nome

}, tool\_c

funcoes\_disponiveis = { "obter\_temperatura\_atual": obter\_temperatura\_atual,

<!-- image -->

}

if tool\_calls: mensagens.append(mensagem\_resp) for tool\_call in tool\_calls:

function\_to\_call function\_name

=

tool\_call.function.name function\_args

=

funcoes\_disponiveis[function\_name]

function\_to\_call(

function\_response

=

json.loads(tool\_call.function.arguments)

local=function\_args.get("local"),

)

=

unidade=function\_args.get("unidade"),

## Explorando a API da OpenAI

<!-- image -->

nas:

funcoes\_disponiveis = {

}

"obter\_temperatura\_atual":

obter\_temperatura\_atual, for tool\_call in tool\_calls: function\_name = tool\_call.function.name

function\_to\_call

=

funcoes\_disponiveis[function\_name]

Como podem observar, os argumentos vem em string no formato json. Para transformá-lo em um dicionário de Python basta realizar o seguinte:

function\_args = json.loads(tool\_call.function.arguments)

E pegamos a resposta das funções rodadas: function\_response = function\_to\_call( local=function\_args.get("local"),

)

unidade=function\_args.get("unidade"),

E adicionamos as mensagens que serão enviadas ao modelo:

mensagens.append(

"tool\_call\_id":

tool\_call.id,

"name":

function\_name,

{

"role":

"tool",

<!-- image -->

in

print(mensagem, end='\n\n')

mensagem

{'role':

mensagens:

'user',

'content':

'Qual é a temperatura em São Paulo e Porto

Alegre?'}

ChatCompletionMessage(content=None, role='assistant', function\_call=None,

{'tool\_call\_id':

{'tool\_call\_id':

'call\_ZAkO73PtjNhZieyXorJgdKWp',

'call\_HNAL3thWncnSzh2MYSjhIkN5',

'role':

'role':

tool\_c

'tool', 'name':

'tool',

'name':

Observamos que o total de mensagens é quatro. A primeira mensagem corresponde à nossa pergunta inicial. A segunda é a resposta do modelo, na qual ele solicita informações às ferramentas externas. A

terceira e a quarta mensagens são as respostas fornecidas pela ferramenta externa em atendimento aos chamados feitos pelo modelo. Com essas informações em mãos, o modelo foi capaz de nos fornecer a

resposta correta!

mensagem\_resp segunda\_resposta.choices[0].message

print(mensagem\_resp.content)

A

=

temperatura em São Paulo é

de

32°C

e

'obter

'obter for

em

Porto

Alegre

é

de

25°C.

09. DESAFIO - ChatBot Finanças

Odesafio agora é criar um chatbot utilizando a API da openai que tenha acessos a dados do mercado financeiro. Para isso, você pode utilizar a api do yahoo finance:

pip install yfinance

ticker

=

'PETR4'

hist = ticker\_obj.history(period='1mo')

ticker\_obj = yf.Ticker(f'{ticker}.SA')

print(hist)

Oparâmetro period pode receber os seguintes valores:

•

•

•

•

•

: dia mo

: mês

y

: ano ytd

max

Fica o desafio para você tentar resolver. Caso não esteja com vontade, esta é a minha solução:

import

import yfinance as yf

<!-- image -->

import json

openai from

dotenv import

load\_dotenv,

\_

=

load\_dotenv(find\_dotenv())

client = openai.Client() # DEFINE FUNCOES

def retorna\_cotacao\_historica(ticker,

hist ticker\_obj = yf.Ticker(f'{ticker}.SA')

find\_dotenv periodo):

ticker\_obj.history(period=periodo)

if len(hist)

30:

hist

&gt;

hist.iloc[::-slice\_size][::-1]

=

slice\_size

=

int(len(hist)

/

30)

hist.index = hist.index.strftime('%m-%d-%Y')

return

=

hist['Close'].to\_json()

tools

=

[

{

d

mensagem\_resp = resposta.choices[0].message mensagens.append(mensagem\_resp)

<!-- image -->

tool\_calls

=

mensagem\_resp.tool\_calls function\_to\_call

if tool\_calls: for tool\_call in tool\_calls: function\_name = tool\_call.function.name function\_args

=

funcoes\_disponiveis[function\_name]

function\_response

=

json.loads(tool\_call.function.arguments)

ticker=function\_args.get("ticker"),

)

=

function\_to\_call(

periodo=function\_args.get("periodo"), mensagens.append(

## Explorando a API da OpenAI

<!-- image -->

mensagens

=

retorna\_resposta\_modelo(mensagens)

if \_\_name\_\_ == '\_\_main\_\_':

main()

Quando utilizar Fine-Tuning?

<!-- image -->

Oprocesso de Fine-tuning em modelos de geração de texto pode aprimorá-los para aplicações específicas, contudo, exige um investimento criterioso de tempo e recursos. Antes de recorrer ao Fine-tuning, é recomendável tentar alcançar resultados satisfatórios por meio de engenharia de prompts, encadea- mento de prompts (que consiste em dividir tarefas complexas em múltiplos prompts) e chamada de

função. As principais razões para essa abordagem são:

•

•

•

Muitas tarefas podem parecer desafiadoras para os modelos inicialmente, mas é possível melho- rar significativamente os resultados com a escolha adequada de prompts, tornando o Fine-tuning

desnecessário.

Oprocesso de iteração com prompts e outras estratégias permite um ciclo de feedback muito mais ágil do que o Fine-tuning, que demanda a criação de conjuntos de dados e a realização de

processos de treinamento.

Mesmo nos casos em que o Fine-tuning se faz necessário, o trabalho preliminar com engenharia de prompts não é perdido.

Geralmente, os melhores resultados são obtidos ao utilizar um prompt bem elaborado nos dados de Fine-tuning, ou ao combinar o encadeamento de prompts

e o uso de ferramentas com o Fine-tuning.

Nosso curso de Engenharia de Prompts oferece uma visão abrangente de algumas das estratégias e táticas mais eficientes para melhorar o desempenho dos modelos sem a necessidade de Fine-tuning.

Usos comuns

•

•

•

•

•

Criando um modelo com Fine-Tuning em Python

Definição do problema

Nosso objetivo com o exemplo a seguir é formatar as respostas. Desejamos que o modelo forneça sempre sua resposta no formato JSON, com as seguintes chaves: resposta, categoria e fonte. Eis a

definição das chaves:

•

•

•

<!-- image -->

categoria: a categoria da pergunta, a qual deve pertencer a uma das seguintes categorias: física,

Umprompt equivalente que geraria essa resposta seria o seguinte:

system\_mes

=

'''

conteúdos: física, matemática, língua portuguesa ou outros. ↪ → Retorne a resposta em um formato json, com as keys:

Responda as

perguntas em

um parágrafo

fonte: valor deve ser sempre AsimoBot resposta: a resposta para a pergunta categoria: a categoria da pergunta '''

Preparação de dados

A ideia por trás do fine-tuning é fornecer mais exemplos ao modelo, permitindo que ele seja re- treinadocombasenessesexemplose,assim,retornerespostasmaisalinhadascomnossasexpectativas.

Portanto, é essencial gerar dados contendo esses exemplos. A OpenAI requer arquivos de texto no formato JSONL para realizar o treinamento dos modelos. Abaixo, segue um exemplo de dado na

formatação necessária:

de até

20

palavras.

Categorize as

respostas no

seguintes

'resposta': entry['resposta'],

<!-- image -->

resposta

=

{

'categoria': entry['categoria'],

} entry = {"messages": [ {"role": "user", "content": entry['pergunta']},

'fonte':

'AsimoBot'

indent=2)}]

{"role":

"assistant",

}

outfile.write('\n')

json.dump(entry, json.dumps(resposta,

outfile,

"content":

ensure\_ascii=False)

→

↪

ensure\_ascii=False,

## Explorando a API da OpenAI

<!-- image -->

fine\_tuning.jobs.create

. É possível notar que passamos o ID do arquivo recém-adicionado e

selecionamos o modelo gpt-3.5-turbo para otimização.

Verificando status do novo modelo

Você pode utilizar o seguinte comando para verificar os processos de otimização que estão sendo

## rodados:

print(client.fine\_tuning.jobs.list(limit=10))

E você pode verificar o estado de algum processo em específico com o seguinte comando:

id\_do\_job = 'COLOCAR\_ID\_DO\_JOP\_AQUI' client.fine\_tuning.jobs.retrieve(id\_do\_job)

Você também pode verificar o status por esta página da OpenAI. Clicando em algum dos processo, você pode acompanhar as métricas do treinamento:

Fine-tuning

All Successful

• Playground |

Fine-tuning

Failed

All Successful Failed

© Assistants |

ft:gpt-3.5-turbo-0125:personal: :94CwIN1U|

18/03/2024, 16:13

° Fine-tuning ft:gpt-3.5-turbo-0125:personal: :94CwIN1U

ft:gpt-3.5-turbo-0125:personal: :94Cee01A|

18/03/2024, 15:49

ft:gpt-3.5-turbo-0125:personal: :94Cee01A

₴ API keys |

© Storage i) Usage|

@ Settings |

ft:gpt-3.5-turbo-0125:personal: :94CCVCH

ft:gpt-3.5-turbo-0125:personal: :94B4xZKa|

18/03/2024, 14:15

ft:gpt-3.5-turbo-0125:personal: :94B4xZKa ft:gpt-3.5-tuxbo-0125:personal: :94AmMyf6

ft:gpt-3.5-tuxbo-0125:personal: :938KB1d8

ft:gpt-3.5-turbo-0125:personal::937xcUkt

88 Trained tokens

29.211|

18/03/2024, 15:26

• Epochs |

18/03/2024, 14:15

• Created at

88 Trained tokens

MODEL

18/03/2024, 16:13

ft:gpt-3.5-turbo-0125:personal::94CwIN1U

© Succeeded

MODEL

18/03/2024, 15:49

ft:gpt-3.5-turbo-0125:personal::94CwlN1U © succeeded

@ Job ID

ftjob-00kYNLkBLuQV7S8k19kAMQ1V|

• Job ID|

ftjob-00kYNLkBLuQV7S8ki9kAMQ1V|

gpt-3.5- turbo-0125

18 de mar. de 2024, 16:13

29.211

<!-- image -->

Utilizando o novo modelo

Para utilizar o modelo modificado, basta verificar seu nome na página de Fine Tuning:

E agora utilizar o método chat.completions, mas com o argumento model definido com o nome do meunovo modelo:

mensagens

= [

]

{'role': 'user',

'content': 'O que é uma equação quadrática?'}

' '

• Learn more

+ Create

resposta

=

messages=mensagens, max\_tokens=1000,

)

temperature=0, mensagem\_resp

print(mensagem\_resp.content)

{

"categoria": "Matemática",

"resposta": "Uma equação quadrática é uma equação polinomial de segundo

}

"fonte": "AsimoBot"

E é possível observar que o modelo respondeu no formato solicitado, em um JSON contendo as chaves resposta, categoria e fonte. Além disso, a resposta possui o tamanho esperado, com um parágrafo

contendo até 20 palavras.

Comparando o modelo com Fine-Tuning e o modelo padrão

Se utilizamos a mesma lista de mensagens utilizado com o modelo novo no gpt padrão, a resposta seria a seguinte:

mensagens

<!-- image -->

{'role': 'user',

'content': 'O que é uma equação quadrática?'}

]

resposta

=

client.chat.completions.create(

max\_tokens=1000, temperature=0, )

messages=mensagens, model='gpt-3.5-turbo-0125', mensagem\_resp

print(mensagem\_resp.content)

Uma

=

resposta.choices[0].message equação quadrática é uma equação polinomial de segundo grau, ou seja,

Para obter uma resposta na formatação desejada, teríamos que adicionar o seguinte system\_mes

Responda as

→

↪

=

'''

conteúdos:

física, perguntas

em um

parágrafo de

até

20

palavras.

Categorize as

prompt respostas

no

:

seguintes

= [

matemática, língua

portuguesa ou

outros.

grau, uma

eq

<!-- image -->

ou seja,

## Explorando a API da OpenAI

<!-- image -->

como parte dos Threads entre os assistentes e os usuários. Ao usar ferramentas, os assistentes

também podem criar arquivos (por exemplo, imagens, planilhas, etc) e citar arquivos aos quais

fazem referência nas mensagens que criam.

Criando um Assistant

Vamosdar um exemplo rápido de utilização da Assistants. Primeiramente, criamos um novo Assistente com uma instrução específica:

from openai import OpenAI client = OpenAI()

assistant = client.beta.assistants.create( name="Math Tutor", instructions="You are a personal math tutor. Write and run code to answer math questions.", tools=[{"type":

"code\_interpreter"}],

)

model="gpt-4-turbo-preview",

Nesse caso, ele terá como tarefa responder dúvidas de matemática. Podemos ver que demos acesso à

ferramenta de interpretação de código (tools=[{'type': 'code\_interpreter'}]), ou seja, o assistente será

capaz de rodar códigos em Python para resolver as dúvidas.

Umavez criado, é possível acessar todos os Assistants através da interface da OpenAI.

+ → C : platform.openai.com/assistants|

Assistants

• Playground |

@ Assistants|

o Fine-tuning

• Documentation |

@ Help |

8g All products

Personal

Anteontem, 26 de mar.

Analista de Demonstrações Financelras asst\_ 7DP8aao6yKnbMVUEy25z7B9ml

Analis n Flancoito Supermercados Animov

Tutor de Matemática da Asimov asst\_loCeCKZtP6vkXNfmgc2wQKCn

Há 9 dias, 19 de mar.

Untitied assistant

Tutor de Matemática

Criando um Thread

<!-- image -->

Comomencionado anteriormente, a comunicação com os assistentes é feita através de Threads. As Threads simplificam o desenvolvimento de aplicações de IA ao armazenar o histórico de mensagens e truncá-lo quando a conversa fica muito longa para o comprimento do contexto do modelo. Você cria

umathread uma vez e simplesmente adiciona mensagens a ela conforme o usuário responde. A seguir, vamos criar uma thread:

thread

=

client.beta.threads.create()

Adicionando mensagem a Thread

Para adicionar mensagens à thread, basta passar os parâmetros de thread\_id (que capturamos da thread que acabamos de criar), o role e o content. Esses dois últimos nós já conhecemos da geração

de texto.

message

=

client.beta.threads.messages.create(

role='user', thread\_id=thread.id,

content='Se eu jogar um dado honesto 1000 vezes, qual é a probabilidade de eu obter

→

↪

)

exatamente 150 vezes o número 6? Resolva com um código'

15:00

1128

O DO10

+ Create

Solicitando ao Assistant para rodar uma Thread

Porfim, temosqueavisaraoAssistantquequeremosrodaraquelathreaddemensagensquecriamos:

run

)

Além disso, podemos enviar instruções específicas relacionadas àquela rodada de thread. Essa in- strução pode melhorar a resposta do Assistente ao aprimorar o contexto para aquele conjunto de

Esperando a Thread rodar

Para garantir que a thread já tenha sido executada, antes de prosseguirmos no código, podemos utilizar o seguinte trecho de código:

import time

while time.sleep(1)

run.status run

=

thread\_id=thread.id,

)

<!-- image -->

run\_id=run.id print(run.status)

Verificando a resposta

Por fim, basta verificarmos a resposta dada pelo modelo. Para isso, precisamos solicitar à API a lista de mensagens atual da thread: if run.status == 'completed': mensagens = client.beta.threads.messages.list( thread\_id=thread.id

print(mensagens)

)

:

print('Errro', run.status)

Tendo a mensagem final o formato de texto, podemos verificá-la da seguinte forma:

print(mensagens.data[0].content[0].text.value)

A

→

↪

probabilidade

é

de obter

aproximadamente exatamente

0.0126, ou

150

vezes seja, cerca

de

=

assistant\_id=assitant.id, thread\_id=thread.id,

else

o

número

1.26%.

6

ao lançar

um dado

honesto

1000

vezes

© ChatGPT

Para calcular a probabilidade de obter exatamente 150 vezes o número 6 ao jogar um dado honesto

1000 vezes, podemos usar a distribuição binomial. A fórmula da distribuição binomial é:

Onde:

python k = 150

p = 1/6

<!-- image -->

Ele até chega à fórmula correta, mas não consegue executá-la para obter o resultado final. No nosso caso, a fórmula foi executada pelo Assistente em um código Python e, por isso, obtivemos a resposta. Podemos verificar isso ao solicitar todos os passos que o modelo percorreu até chegar à solução.

Primeiro solicitamos todos os passos (

run\_steps steps

) realizados pelo nosso run:

client.beta.threads.runs.steps.list(

thread\_id=thread.id,

)

=

run\_id=run.id

## Explorando a API da OpenAI

<!-- image -->

onde:

-

número

6), sucessos

\(

é

de

\)

desejado

k

(número

o

do

-\( n \) é o número total de tentativas (lançamentos

-

dado), tentativa,

única uma

6),

\(

p

=

1

=

p

-

q

código obter

de sucesso

probabilidade que

-\( q \) é a probabilidade de fracasso em uma única tentativa (1 -p). Neste caso, \( n = 1000 \) (número total de lançamentos do dado), \( k = 150 \) (número de

→

↪

p

\)

vezes

é

em queremos

→

↪

um número

único

6

em lançamento)

## Vamos calcular essa

e

probabilidade

=== Step: tool\_calls -----from math import comb

# Definindo os parâmetros n = 1000 # número total de lançamentos do dado

p

probabilidade

=

#

1/6

=

#

150

k

número

q

=

1

-

p

#

vezes de

probabilidade

#

Calculando de

a

probabilidade probabilidade

de probabilidade

=

comb(n, k)

-----

0.01262946340594314

Result

*

obter que

obter

o

em número

\(

com um

queremos não

obter o usando

(p

**

o

a

k)

6

número número

fórmula

*

(q

**

em da

(n

\frac{1}{6}

\).

Python:

número

6

(probabilidade

\)

6

em

único um

lançamento um

único distribuição

-

k))

lançamento binomial

\(

a

o

de obter

o

<!-- image -->

2

3

Invoice ID

750-67-

8428

226-31-

3081

631-41-

3108

123-19-

1176

373-73-

7910

Branch

A

A

A

A

City

Yangon

Naypyitaw

Yangon

Yangon

Customer type

Gender

Member Female

Normal Female

Normal

Male

Member

Male

Product line

Health and beauty

Electronic accessories

Home and lifestyle

Health and beauty

Unit price

74.69

15.28

46.33

58.22

Quantity

7

5

7

8

Tax 5%

26.1415

3.8200

16.2155

23.2880

Total

548.9715

80.2200

340.5255

489.0480

Date

1/5/2019

3/8/2019

3/3/2019

1/27/2019

2/8/2019

Time

13:08

10:29

13:23

20:33

10:37

Payment cogs

Ewallet

522.83

Cash

76.40

Credit 324.31

Ewallet 465.76

Ewallet 604.17

gross margin percentage

4.761905

4.761905

4.761905

4.761905

4.761905

income Rating

26.1415

9.1

3.8200

16.2155

23.2880

30.2085

9.6

7.4

8.4

5.3

As habilidades de executar um código adicionam enormes capacidades ao Assistente. Além de criar códigos simples, ele pode interagir com arquivos passados a ele e extrair insights relevantes e rápidos,

com poucas linhas de código. E é isso que vamos explorar aqui brevemente: análise de dados com

Assistants.

Primeiro, vamos olhar os dados que vamos utilizar. Ele são referentes a vendas de um supermercado, e foram extraídos do Kaggle

import pandas

dataset = pd.read\_csv('arquivos/supermarket\_sales.csv')

dataset.head()

Enviando arquivos para o Assistant import

from dotenv import load\_dotenv, find\_dotenv

<!-- image -->

\_

=

openai load\_dotenv(find\_dotenv())

client = openai.Client()

file = client.files.create( file=open('arquivos/supermarket\_sales.csv', 'rb'), purpose='assistants' )

assitant

=

client.beta.assistants.create(

instructions='Você é um analista financeiro de um supermercado. Você deve utilizar os

→

↪

)

name="Analista dados

\

tools=[{'type': 'code\_interpreter'}],

Fianceiro",

.csv informados relativos as vendas do supermercado para realizar as suas análises.', tool\_resources={'code\_interpreter': {'file\_ids': [file.id]}},

model='gpt-4o'

)

<!-- image -->

run\_id=run.id print(run.status)

Agora podemos verificar a reposta:

if run.status

==

'completed':

messages

=

client.beta.threads.messages.list(

)

else thread\_id=thread.id

print(messages)

print('Erro', run.status)

:

## Explorando a API da OpenAI

<!-- image -->

for in

print('======= Step &gt;', step.step\_details.type)

step run\_steps.data[::-1]:

if step.step\_details.type

== 'tool\_calls':

for in

print(' ❵❵❵ ') print(tool\_call.code\_interpreter.input) print(' ❵❵❵ ')

tool\_call step.step\_details.tool\_calls:

if print('Result')

tool\_call.code\_interpreter.outputs[0].type

==

'logs':

print(tool\_call.code\_interpreter.outputs[0].logs)

step.step\_details.type == 'message\_creation':

if

=

message client.beta.threads.messages.retrieve(

if message.content[0].type == 'text': print(message.content[0].text.value) ======= Step &gt; message\_creation

Para

→

thread\_id=thread.id, message\_id=step.step\_details.message\_creation.message\_id )

calcular

o

arquivo que

↪

→

↪

=======

identificar

Step

&gt;

rating vendas

a

médio estrutura

você

enviou.

tool\_calls import

pandas as

#

Carregar data

das dos

pd

o

arquivo

=

pd.read\_csv(file\_path)

'/mnt/data/file-cEUCgJzyVO26Y5fZb4erTPqt'

file\_path

=

dados

e

do

a

seu supermercado,

coluna que

contém primeiro

os ratings

Vou começar

por abrir

e

examinar

o

conteúdo precisarei

analisar das

vendas.

do arquivo

para

o

2 13:23 Credit card 324.31 3 20:33 Ewallet 465.76

<!-- image -->

1

4

4.761905

4.761905

3.8200

23.2880

9.6

8.4

10:29

10:37

Cash

76.40

Step

=======

&gt;

=======

Ewallet

604.17

4.761905

4.761905

16.2155

30.2085

7.4

5.3

O arquivo contém várias colunas, incluindo 'Rating', que parece ser a coluna relevante para calcular o rating médio das vendas do supermercado. Vou proceder com o cálculo do rating médio agora. ↪ → ↪ →

#

Step

Calcular

o

message\_creation

&gt;

tool\_calls rating

average\_rating average\_rating = data['Rating'].mean()

Result

=======

6.9727

O

rating

→

Step

&gt;

informações médio

message\_creation ou

análises adicionais,

por favor,

↪

Podemos ver que ele necessitou de cinco passos:

•

•

•

•

Criação de mensagem (message\_creation): ele percebeu que era necessário abrir o arquivo e verificar as informações contidas nele.

Chamadadefunção (tool\_calls): ele executou o código em Python para abrir o arquivo e verificar os primeiros dados.

Criação de mensagem (message\_creation): ele percebeu que havia uma coluna 'Rating' e a partir dela seria possível calcular o que o usuário solicitou.

Chamada de função (tool\_calls): ele executou o código em Python para calcular o Rating a partir do arquivo informado.

vendas médio

das do

seu supermercado

é

me aproximadamente

avise!

6.97.

Se precisar

de mais

•

Gerando gráficos com Assistants

Outra feature bem legal é a possibilidade de gerar gráficos ao utilizarmos o code\_interpreter. Vamos ver como isso funciona.

Primeiro, vamos solicitar o seguinte ao modelo:

#

Adiciona pergunta

=

messages

=

role='user',

)

thread\_id=thread.id, content=pergunta

#

)

#

<!-- image -->

Aguarda

Solicita ao

thread\_id=thread.id, run

=

assistant\_id=assistant.id,

a

import time

while in

['queued', 'in\_progress', 'cancelling']:

run

run.status time.sleep(1)

thread\_id=thread.id,

=

client.beta.threads.runs.retrieve(

run\_id=run.id )

print(run.status) Verificamos as mensagens e notamos que a última não consiste mais em um texto, e sim em um arquivo de imagem (image\_file).

if run.status

==

'completed':

messages

=

client.beta.threads.messages.list(

)

else print('Erro', run.status)

thread\_id=thread.id print(messages)

:

print(messages.data[0].content[0])

<!-- image -->

#

Agregar

pagamento\_counts = data['Payment'].value\_counts()

#

Gerar

o

plt.show()

a

quantidade gráfico

de vendas

de pizza

por meio

de pagamento

plt.figure(figsize=(10, 7)) plt.pie(pagamento\_counts, labels=pagamento\_counts.index, autopct='%1.1f%%', startangle=140) plt.title('Percentual de Vendas Por Meio de Pagamento')

=======

Step

&gt;

message\_creation

Percentual de Vendas Por Meio de Pagamento

Credit card

## Explorando a API da OpenAI

Ewallet

<!-- image -->

E ele gerou corretamente o gráfico solicitado. Incrível!

<!-- image -->

import

from dotenv import load\_dotenv, find\_dotenv

\_

=

openai load\_dotenv(find\_dotenv())

files = ['arquivos/Explorando a API da OpenAI.pdf', client = openai.Client() vector\_store = client.beta.vector\_stores.create(name = 'Apostilas Asimov Aula 15')

'arquivos/Explorando o Universo das IAs com Hugging Face.pdf']

for file\_stream

=

[open(f, file\_batch

'rb')

f

in files]

client.beta.vector\_stores.file\_batches.upload\_and\_poll(

=

files=file\_stream vector\_store\_id=vector\_store.id,

)

Agora podemos criar o Assistant e vincular a esta Vector Store:

assitant

=

client.beta.assistants.create(

instructions="Você

→

↪

→

↪

→

↪

)

name="Tutor

é

um tutor

\

Asimov", perguntas

teóricas sobre

\

Face com

Python.

você

não

Você

de uma

a

api utiliza

encontre as

escola de

da

OpenAI

e

as respostas

tools=[{'type': 'file\_search'}], responder.",

apostilas nas

programação.

Você

sobre

a

utilização dos

cursos para

apostilas informadas,

é

ótimo da

basear você

para biblioteca

suas fala

responder do

Hugging respostas.

que tool\_resources={'file\_search': {'vector\_store\_ids': [vector\_store.id]}},

\

Caso não

sabe model='gpt-4o'

Nas ferramentas agora, adicionamos o retrieval (tools=[{'type': 'file\_search'}]), avisando a API que gostaríamos de utilizá-la.

E agora enviamos uma mensgem:

#

Criamos thread

=

#

uma

Adicionamos messages

=

role='user',

)

thread\_id=thread.id, content=pergunta

#

)

#

Aguradamos import

Solicitamos thread\_id=thread.id,

run

=

assistant\_id=assistant.id, time

while time.sleep(1)

run.status run

=

thread\_id=thread.id,

)

<!-- image -->

run\_id=run.id

print(run.status)

Podemos ver que a resposta foi:

print(messages.data[0].content[0].text.value)

Para utilizar Assistants com Python, você pode seguir os passos ilustrados abaixo para criar, configurar e interagir com assistentes inteligentes através da API da OpenAI. Este método inclui a criação de assistentes com instruções específicas e a utilização de ferramentas ↪ → ↪ →

→

Interpreter**.

↪

###

1.

como

o

**Code

Criando um

Assistente

**Inicializando

o

Cliente

Primeiro, você

deve inicializar

import da

OpenAI**

openai from

dotenv import

load\_dotenv,

\_

=

o

cliente da

find\_dotenv load\_dotenv(find\_dotenv())

OpenAI.

Aqui está

o

código para

fazer isso:

<!-- image -->

===

print(message.content[0].text.value)

Step:

tool\_calls

FileSearchToolCall(id='call\_n2Gohz4Tq2MPEvx3k672NCEi', file\_search={}, type='file\_search')

=== Step: message\_creation Para utilizar Assistants com Python, você pode seguir os passos ilustrados abaixo para criar,

→

↪

→

↪

→

↪

###

1.

configurar

e

interagir como

inclui

a

criação de

assistentes

o

**Code com

assistentes

Interpreter**.

Criando um

Assistente

**Inicializando

o

Cliente inteligentes

através da

API

da

OpenAI.

Este método

da com

OpenAI**

instruções específicas

e

a

utilização de

ferramentas

## Explorando a API da OpenAI

<!-- image -->

import openai

<!-- image -->

from dotenv import

load\_dotenv,

\_ = load\_dotenv(find\_dotenv()) client = openai.Client()

Vocês podem notar que fizemos mais dois imports que serão necessários para conseguirmos visualizar a imagem gerada. Requests já faz parte da biblioteca padrão, enquanto o PIL (que vem de Pillow) não,

e precisa ser instalado:

pip install Pillow

Criando uma imagem

Feito isso, podemos gerar as imagens:

nome

=

'bosque'

prompt modelo

=

'dall-e-3'

amplo com uma leve elevação ao fundo.'

=

'Crie qualidade

uma

=

imagem de

um campo

'hd'

style

=

'natural'

resposta

=

client.images.generate(

prompt=prompt, model=modelo,

size='1024x1024', quality=qualidade,

find\_dotenv de

pastagem,

\

)

style=style, n=1

•

model

-

-

prompt size

-

-

-

-

-

quality

-

-

'hd'

style

-

-

<!-- image -->

'natural' &gt; imagens mais naturais

· n : a quantidade de imagens que serão geradas simultaneamente

Salvando a imagem gerada

Agora vamos salvar a imagem: nome\_arquivo = f'{nome}\_{modelo}\_{qualidade}\_{style}.jpg'

image\_url img\_data

requests.get(image\_url).content with

f.write(img\_data)

=

resposta.data[0].url open(nome\_arquivo,

'wb')

as f:

Visualizando a imagem

E utilizamos PIL para visualizar a imagem:

=

•

•

•

•

<!-- image -->

Editando uma imagem

Para editar uma imagem, é necessário primeiro criarmos uma máscara. Ela consiste na mesma im- agem no formato PNG, apenas com a parte que será editada em branco, como podemos observar na

imagem:

## Explorando a API da OpenAI

<!-- image -->

rapp

DALL-E 2 Image Mask Editor

1. Escolher arquivo original.png

<!-- image -->

Oprocesso é simples, apenas adicione uma nova imagem. Com o mouse clicado, apage uma parte da imagem e depois faça o download da mask e da original novamente.

Feito isso, podemos voltar para o código:

resposta

=

client.images.edit(

model='dall-e-2',

)

size='1024x1024'

Salvando a imagem gerada

Agora vamos salvar a imagem:

nome\_arquivo image\_url

=

img\_data

=

with f.write(img\_data)

open(nome\_arquivo,

Visualizando a imagem

E utilizamos PIL para visualizar a imagem:

image

=

image.show()

n=1,

<!-- image -->

<!-- image -->

Criando variações

Por último, podemos criar variações de imagens com o seguinte código:

resposta n=1,

image=open('arquivos/imagens/bosque\_dall-e-3\_hd\_natural.jpg', 'rb'),

)

=

client.images.create\_variation(

size='1024x1024'

## Explorando a API da OpenAI

<!-- image -->

<!-- image -->

17. Visão computacional com GPT-Vision

Mais uma ferramenta muito poderosa desenvolvida pela OpenAI é o GPT-Vision. Ele é um modelo

Ou seja, o modelo recebe imagens e responde perguntas sobre elas. Incrível!

Interpretando uma imagem da internet

#

imports from

import necessários

dotenv import

\_

=

openai load\_dotenv(find\_dotenv())

client

=

openai.Client()

#interpretando url

comando

=

→

↪

resposta

=

messages=[{

model='gpt-4-vision-preview',

'role': 'user',

{'type':

}]

)

Esta é a imagem que estamos tentando descrever:

<!-- image -->

'content':

{'type': ]

'image\_url', 'image\_url': {'url': url}}

'text', 'text': comando},

=

<!-- image -->

Interpretando uma imagem do seu computador

Para enviar uma imagem do seu computador, é necessário antes realizar um encoding para base64: import base64

def encode\_image(caminho\_imagem):

with caminho

open(caminho\_imagem, 'rb'

return base64.b64encode(img.read()).decode('utf-8')

=

'celulas.jpg'

base\_64\_img =

encode\_image(caminho)

)

as img:

## Explorando a API da OpenAI

<!-- image -->

Agora rodamos o modelo perguntando quantas células ele vê na imagem:

imagem?'

## comando = 'Quantas células aparecem na url = f'data:image/jpg;base64,{base\_64\_img}'

resposta = client.chat.completions.create( model='gpt-4-vision-preview', messages=[{

'content': [ {'type': 'text', 'text': comando}, {'type': 'image\_url', 'image\_url':

}],

'role': 'user',

]

{'url':

max\_tokens=1000,

)

print(resposta.choices[0].message.content)

url}}

THE VICE PRESIDENT

<!-- image -->

import def

base64

encode\_image(caminho\_imagem):

with caminho

open(caminho\_imagem, 'rb'

return base64.b64encode(img.read()).decode('utf-8')

=

'escrito\_mao\_dificil.jpg'

)

as img:

base\_64\_img =

texto

=

"O

que resposta

=

messages=[{

model='gpt-4-vision-preview',

'role': 'user',

'content':

}],

]

max\_tokens=1000,

)

print(resposta.choices[0].message.content)

Na imagem,

The

Vice vê-se

President

4/30/13

Dear

I

am

→

↪

→

↪

You

Joe

<!-- image -->

Myles, sorry

People had

guns are

it love

a

good

Biden

Esta imagem mostra uma carta escrita pelo então

→

chamada

Myles, comentando

sobre

↪

Incrível, ele acertou perfeitamente!

uma ideia

vice-presidente relacionada

a

Joe armas

Biden que

para idea.

uma disparariam

If we

happier.

criança chocolate.

resposta.write\_to\_file(arquivo)

<!-- image -->

)

Temos os seguintes argumentos para explorar no método audio.speech.create:

· model : o modelo utilizado:

-

'tts-1'

-

'tts-1-hd'

voice

: o estilo da voz que será usado

-

'alloy'

•

## Explorando a API da OpenAI

<!-- image -->

print(transcricao.text)

<!-- image -->

)

Seja bem-vindo

muito

→

↪

programação, especificamente com a linguagem Python, aqui com a gente. Pode ter certeza que a gente colocou muito carinho e muita dedicação para construir esse material. Além dos conhecimentos técnicos que a gente vai apresentar sobre a linguagem e programação em si, ↪ → ↪ → ↪ →

minha equipe

e

→

↪

→

↪

→

↪

→

↪

→

↪

→

↪

→

↪

→

↪

→

↪

→

↪

→

↪

→

que nosso

curso bem-vinda

ficamos ou

coloquei também

eu

Soares longo

ao vocês

com engenheiro

Padeval analista

muito felizes

ao grande

desse eu

e

de dados.

treinamento.

parte não

sou

E

utilizei

e

eu que

e exclusivamente

única

é

quiserem tenham

vocês completo

experiência

e

da minha

a

Para programação

programador essa

é

dia para

no vocês

dúvidas,

a

muito mais inglês. Ou

ampla habilidade

no mercado

e

até

de seja,

programar.

↪

Oresultado foi ótimo. Entretanto, ele cometeu alguns erros ao se tratar de nomes próprio. Por exemplo,

Asimov Academy virou Zemove Academy e Rodrigo Soares Tadewald virou Rodrigo Soares Padeval.

Fez sentido, mas pode melhorar.

Para corrigir, podemos utilizar o parâmetro prompt, da seguinte forma:

audio = open('audio\_asimov.mp3', 'rb')

model='whisper-1', transcricao

=

client.audio.transcriptions.create(

file=audio,

O professor se chama Rodrigo Soares Tadewald.'

prompt='Essa é a transcrição de uma aula da Asimov Academy.\

entrar me

quem não

dentro da

minha escolhido

iniciar

Python de

aqui minha

vivência

Na origem.

de mágica

a

grande muito

anos verdade,

da conhece

carreira

Na software.

desenvolver

a

dia do

programação.

de vocês,

Tem mais

poderosa atrás,

que do

muitas era

no ainda,

meu da

Zemove para

eu me

Vocês vezes

como gente

com já

que no

mundo da

Academy.

compartilhar formei

como não

mercado verdade,

isso.

necessário que

certeza,

a

uma ela

nome

é

Rodrigo financeiro

como usada

ser pode

precisam habilidade

e

compara diz

Programação além

gente do

é, sem

tivesse utilizá-la

secundária.

a

que para

sombra inglês

programação inglês,

a

gente tem

de poder

que

Ela

o

é

o

novo saber

para futuro.

trabalho.

Hoje,

Eu

)

print(transcricao.text)

Seja muito

→

e

minha

Eu

↪

→

↪

→

↪

→

↪

→

↪

→

↪

→

↪

→

↪

→

↪

→

↪

→

↪

→

↪

→

↪

→

↪

→

↪

→

a

gente programação,

conhecimentos que

eu também

Soares vocês

com engenheiro

única analista

que vocês

e

é

muito inglês.

dúvidas, entrar

no programar.

↪

E agora o modelo a certou. Ao adicionarmos os nomes próprios no prompt o modelo consegue se corrigir e melhorar sua transcrição. Muito bem.

Podemos também gerar a transcrição no formato de legendas, modificando o response\_format para

'srt':

audio = open('audio\_asimov.mp3', 'rb')

model='whisper-1', transcricao

=

file=audio,

O professor se chama Rodrigo Soares Tadewald.',

response\_format='srt' )

<!-- image -->

print(transcricao)

1

Seja muito bem-vindo ou bem-vinda ao nosso curso completo de Python, 2 00:00:05,000 --&gt; 00:00:06,500

00:00:01,000

--&gt;

00:00:05,000

aqui da

Asimov

3

Eu

00:00:06,500

e

minha equipe

4

iniciar

00:00:09,500

no mundo

5

Academy.

--&gt;

ficamos

--&gt;

00:00:09,500

muito

00:00:11,000

da programação,

felizes que

vocês tenham

escolhido

Academy.

certeza mundo

da material.

Além dos

compartilhar programação

si, em

é

Rodrigo financeiro

como como

utilizá-la secundária.

usada para

o

sombra de

Ela programação

que

é

o

novo saber

poder

<!-- image -->

## Explorando a API da OpenAI

recognizer.adjust\_for\_ambient\_noise(source, audio = recognizer.listen(source)

<!-- image -->

print('Ouvindo...')

return audio

def transcricao\_audio(audio): wav\_data = BytesIO(audio.get\_wav\_data()) wav\_data.name = 'audio.wav'

transcricao

=

client.audio.transcriptions.create(

)

## model='whisper-1', file=wav\_data,

return transcricao.text def completa\_texto(mensagens):

messages=mensagens, model='gpt-3.5-turbo-0125', max\_tokens=1000, resposta

=

client.chat.completions.create(

)

temperature=0

return resposta

cria\_audio(texto):

if

Path(ARQUIVO\_AUDIO).unlink()

Path(ARQUIVO\_AUDIO).exists():

resposta

=

client.audio.speech.create(

voice='onyx', model='tts-1',

duration=1)

def

roda\_audio()

<!-- image -->

cria\_audio(mensagens[-1]["content"])

21. Finalizando o curso

E assim, chegamos ao fim de mais um curso. Esperamos que este conteúdo tenha sido útil para você!

Sinta-se à vontade para compartilhá-lo com seus amigos e, sempre que tiver dúvidas, nos chame nos comentários das aulas que responderemos prontamente!

Umgrande abraço!

<!-- image -->
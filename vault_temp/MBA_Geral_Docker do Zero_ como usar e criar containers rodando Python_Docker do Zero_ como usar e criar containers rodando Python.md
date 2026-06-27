## Docker do zero: como usar e criar containers rodando Python

Asimov Academy

<!-- image -->

Cgroups: Controle de Recursos . . . . . . . Union File Systems: Camadas de Arquivos .

<!-- image -->

Processos Isolados, Kernel Compartilhado

.

.

.

.

.

.

.

.

.

.

.

.

.

.

.

.

.

.

.

.

.

.

.

.

.

.

.

.

.

.

.

.

.

.

.

.

.

.

.

.

.

.

.

.

.

.

.

.

.

.

.

.

.

.

.

.

.

38

38

38

.

.

.

.

.

.

.

.

.

.

.

.

.

Docker não é uma Máquina Virtual . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 38 Comparativo: Docker vs Máquinas Virtuais (VMs) . . . . . . . . . . . . . . . . . . . . . 39

Os Sabores do Docker

.

.

.

.

.

.

.

.

.

.

.

.

.

.

.

.

.

Comparativo: Docker Engine vs Docker Desktop

Visão Geral dos Principais Conceitos do Docker .

Dockerfile: o ponto de partida

.

.

.

Docker Layers: blocos de construção

.

.

.

.

.

.

.

.

.

.

.

.

.

.

.

.

.

.

.

.

.

.

.

.

.

.

.

.

.

.

.

.

.

.

.

.

.

.

.

.

.

.

.

.

.

.

.

.

.

.

.

.

.

.

.

.

.

.

.

.

.

.

.

.

.

.

.

.

.

.

.

.

.

.

.

.

.

.

.

.

.

.

.

.

.

.

.

.

.

.

.

.

.

.

.

.

.

.

.

.

.

.

.

.

.

.

.

.

.

.

.

.

.

.

.

.

.

.

.

.

.

40

40

41

41

41

## Docker do zero: como usar e criar containers rodando Python

<!-- image -->

Conclusão do Experimento

.

.

.

.

.

.

.

.

.

.

.

.

.

.

.

.

.

.

.

.

Oquesão Volumes no Docker? . . . . . . . . . .

.

.

.

.

.

.

.

.

.

.

.

Experimento - Usando Volumes no Docker para Persistência de Dados

.

.

.

.

.

.

.

.

.

.

.

.

.

.

.

.

.

.

.

.

.

.

.

.

.

.

.

.

.

.

.

.

.

.

.

.

57

57

58

Objetivo do Experimento . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 58 Etapas do Experimento . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 58

Conclusão do Experimento

.

.

.

.

.

.

.

.

.

.

Experimento - Executando Script Python com Docker

Objetivo do Experimento .

.

.

.

.

.

.

.

.

.

.

.

.

.

.

.

.

.

.

.

.

.

.

.

.

.

.

.

.

.

.

.

.

.

.

.

.

.

.

.

.

.

.

.

.

.

.

.

.

.

.

.

.

.

.

.

.

.

.

.

.

.

.

.

.

.

.

.

.

.

.

.

.

.

.

.

.

59

59

59

Etapas do Experimento . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 59 Conclusão do Experimento . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 62 Experimento - Trabalhando com Volumes Gerenciados pelo Docker . . . . . . . . . . . . . . 63

Objetivo do Experimento . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 63 Etapas do Experimento . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 63

Conclusão do Experimento

.

.

.

.

.

.

.

.

.

.

.

.

.

.

.

.

.

.

.

.

.

.

.

.

.

.

.

Experimento - Fazendo Backup e Restauração de Volume Gerenciado pelo Docker .

Objetivo do Experimento .

Etapas do Experimento .

.

Conclusão do Experimento

Oquevocê aprendeu até aqui?

.

.

.

.

.

.

.

.

.

.

.

.

.

.

.

.

.

.

.

.

.

.

.

.

.

.

.

.

.

.

.

.

.

.

.

.

.

.

.

.

.

.

.

.

.

.

.

.

.

.

.

.

.

.

.

.

.

.

.

.

.

.

.

.

.

.

.

.

.

.

.

.

.

.

.

.

.

.

.

.

.

.

.

.

.

.

.

.

.

.

.

.

.

.

.

.

.

.

.

.

.

.

.

.

.

.

.

.

.

.

.

.

.

.

.

.

.

.

.

.

.

.

.

.

.

.

.

.

.

.

.

.

.

.

.

.

.

.

.

.

.

66

66

66

66

69

69

<!-- image -->

1. Máquinas Virtuais e Containers

Instalação do Docker Engine curl

<!-- image -->

Lubuntu 64 bits

, uma dis- tribuição Linux baseada no Ubuntu, conhecida por sua leveza e baixo consumo de recursos. Essa

escolha é ideal para ambientes de estudo, testes ou máquinas com hardware mais modesto, garantindo boa performance mesmo em equipamentos com recursos limitados. Além disso, por ser baseada no

Ubuntu, o Lubuntu é totalmente compatível com o Docker Engine e segue os mesmos procedimentos

Passos de Instalação

As instruções abaixo são retiradas da documentação do Docker.

1.

for

Removendo Versões Antigas pkg

→

runc

↪

2.

#

in

;

do

Adicionando um repositório

Add sudo

sudo apt-get update

sudo

Docker's apt-get

official install

GPG

key:

ca-certificates sudo curl -fsSL https://download.docker.com/linux/ubuntu/gpg -o /etc/apt/keyrings/docker.asc sudo chmod a+r /etc/apt/keyrings/docker.asc

install

-m

0755

-d

/etc/apt/keyrings

# Add the repository to Apt sources: echo \ "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.asc] https://download.docker.com/linux/ubuntu \ ↪ →

sudo

$(.

sudo

/etc/os-release apt-get

3.

tee

/etc/apt/sources.list.d/docker.list update

Instalando os pacotes Docker sudo

→

↪

apt-get install

docker-ce docker-compose-plugin

docker-ce-cli

&gt;

:-

$VERSION\_CODENAME}")

/dev/null containerd.io

stable"

docker-buildx-plugin echo

"${UBUNTU\_CODENAME

&amp;&amp;

|

\

containerd

<!-- image -->

Comandos Essenciais do Docker

Agora você aprenderá os comandos básicos para criar, visualizar, parar e remover containers Docker.

São eles: · docker run

•

docker ps

•

•

•

docker stop docker start

docker rm

## Docker do zero: como usar e criar containers rodando Python

docker run -d --name meu-nginx nginx

<!-- image -->

Esse comando: · Cria um container chamado meu-nginx a partir da imagem nginx .

## · Usa a opção -d

(detached) para rodar em segundo plano.

docker ps Ocomando docker ps lista os containers em execução no momento.

Sintaxe:

docker ps

[

opções

Oqueele faz:

•

Exibe informações como: ID do container, imagem usada, status, e portas expostas.

]

<!-- image -->

docker stop

Ocomando docker stop serve para

Sintaxe:

docker stop

&lt;

nome

Oqueele faz:

•

Envia um sinal para parar o processo principal do container de forma segura.

Exemplo:

docker stop meu-nginx

Esse comando para o container chamado docker

start

Ocomando docker

e que está parado.

meu-nginx

é utilizado para

.

iniciar um container que já foi criado anteriormente parar um container em execução

.

ou

ID

do container

start

&gt;

Sintaxe:

docker start

Oqueele faz:

•

•

Exemplo:

docker start

Esse comando:

•

Inicia o container chamado

•

Se o container estiver parado, ele será iniciado novamente com o mesmo estado de configuração.

docker rm

Ocomando

Sintaxe:

docker rm &lt; nome ou ID do container &gt;

Oqueele faz:

•

Exclui o container do sistema (não a imagem).

Exemplo:

docker rm

meu-nginx

Esse comando remove o container create

<!-- image -->

meu-nginx

, desde que ele esteja parado.

).

<!-- image -->

11 12

1

2

Roda na Minha

## Docker do zero: como usar e criar containers rodando Python

<!-- image -->

Umambiente de execução reproduzido é um ambiente computacional que foi configurado para ser idêntico ou extremamente semelhante ao ambiente original. Sem o ambiente reproduzido, desenvolvedores acabam com o problema conhecido como 'Mas roda na minha máquina' .

Umdosgrandesdesafiosaocriarumsoftwareégarantirqueelefuncionebememdiferentesambientes.

Muitas vezes, depois de horas programando, esquecemos que o computador do usuário final - ou mesmooservidor onde a aplicação será executada - pode não ter as mesmas bibliotecas e configura-

ções que usamos durante o desenvolvimento. Isso costuma causar erros e dificulta a implantação do sistema.

Parailustrar, pense em umaaplicaçãoPythonqueprecisaacessarumbancodedadosSQL.Noambiente de desenvolvimento, temos um servidor responsável por duas funções distintas:

•

•

Banco de dados (algo como MySQL)

Aplicação Python

As bibliotecas instaladas no sistema podem ser necessárias tanto para o

a

aplicação Python banco de dados

quanto para

. Ao mover o que foi criado para um ambiente de produção, é preciso garantir que

Ambiente de Desenvolvimento Reproduzido

Ambiente de

Desenvolvimento

Banco de

(Desenvolvimento)

Dados

Ambiente de

Produção

V

<!-- image -->

Umambiente reproduzido, desenvolvimento e produção.

Umambiente de execução reproduzido é necessário, pois garante ao desenvolvedor que ele pode reproduzir o comportamento do software tanto em ambiente de desenvolvimento como em ambiente de produção.

Ambiente de Execução Isolado

Umambiente de execução isolado é um espaço dedicado para executar aplicações ou processos, sepa- rado de outros ambientes e do sistema operacional host. Ele fornece uma camada de isolamento que

protege os recursos da aplicação e garante que ela funcione de forma independente, sem interferir em outras aplicações ou no sistema subjacente. Exemplos de ambientes de execução isolados:

e

máquinas virtuais

.

containers

AMBIENTE HOSPEDEIRO (HOST

SYSTEM)

&amp; AMBIENTE ISOLADO 1

Aplicação 1

Márquina

Virtual 1

&gt;

Sistema

Operacional

AMBIENTE ISOLADO 2

Aplicação 2

&gt;

Sistema

<!-- image -->

Operacional

Características Principais de um Ambiente de Execução Isolado:

Isolamento de Recursos

Cada ambiente possui seus próprios recursos, como sistema de arquivos (ou parte do sistema de arquivos), variáveis de ambiente, rede, e em alguns casos alocação de CPU e memória. Isso impede que configurações ou bibliotecas de um ambiente interfiram em outro.

Reprodutibilidade

Umambiente de execução isolado pode ser replicado facilmente em diferentes máquinas, garantindo que o comportamento da aplicação seja consistente.

Segurança

Oisolamento limita o impacto de falhas ou vulnerabilidades, protegendo tanto o sistema host quanto outros ambientes de execução.

Hipervisor

(Hypervisor)

App

Guest

S.O.

Principais Características

•

Isolamento

: cada VM é separada do sistema host e de outras VMs, aumentando segurança e estabilidade.

App

App

<!-- image -->

Três VMs em um único host.

## Docker do zero: como usar e criar containers rodando Python

<!-- image -->

container, a interface do aplicativo (o frontend) em outro, e a parte que conecta os dois - o backend -

emumterceiro container.

Ao se dedicar a uma única função e não tentar simular um sistema operacional completo, como fazem as VMs, os containers acabam sendo mais leves, rápidos e fáceis de gerenciar. Existem outras diferenças técnicas entre containers e VMs, mas o mais importante é que, na prática,

boa parte da Engenharia de Dados moderna depende do uso e da orquestração de containers.

Na ilustração a seguir, observamos três aplicações em execução independentemente (três containers).

Apesar de serem distintas e autônomas, as aplicações compartilham o mesmo sistema operacional e o mesmo hardware (servidor). Diferentemente de uma VM, o container não executa um sistema operacional autônomo ou simula hardware. O container representa apenas um programa autônomo

com todas as suas dependências.

App

App

App

<!-- image -->

Três aplicações isoladas. Mesmo Sistema Operacional (kernel do host), mesmo hardware

(servidor).

Principais Características de um Container

Isolamento

•

Cada container é executado de forma isolada do sistema host e de outros containers, usando recursos como

namespaces

e

cgroups fornecidos pelo kernel do sistema operacional. Isso signi-

fica que cada container tem seu próprio sistema de arquivos, espaço de processo e configuração de rede.

Portabilidade

•

Como o container inclui tudo o que a aplicação precisa para ser executada, ele pode ser mo- vido de um ambiente para outro (ex.: desenvolvimento, teste, produção) sem problemas de

compatibilidade.

Leveza

•

Diferente de máquinas virtuais, os containers compartilham o kernel do sistema operacional host, o que os torna muito mais leves e rápidos para iniciar.

Imagens como Base

•

Containers são criados a partir de imagens (exemplo: imagens Docker), que são como modelos contendo o sistema de arquivos e as instruções necessárias para rodar a aplicação.

Os containers se destacam por várias razões:

•

•

•

•

Completos:

Segregados:

Autônomos:

impacta os outros.

Adaptáveis:

funciona no seu computador de desenvolvimento terá o mesmo desempenho em um data center ou na nuvem.

Comparativo Entre Máquina Virtual e Container

Característica

Arquitetura

Gerenciamento

Isolamento

Desempenho

<!-- image -->

Altamente isolado, com segurança e

independência entre VMs.

Pode ter sobrecarga devido à virtualização

Compartilha o kernel do sistema

Utiliza uma engine (como Docker,

Isolado, mas menos seguro do que

VMs, já que compartilha o kernel.

Leve, com menos sobrecarga por do hardware. usar o kernel compartilhado.

Tamanho Requer imagens grandes, pois inclui todo o sistema operacional. Imagens menores, já que reutilizam o kernel do host. Tempo de Relativamente lento (pode levar minutos Muito rápido (pode levar segundos).

Inicialização

Flexibilidade de S.O.

Persistência de Estado

para inicializar).

Suporta sistemas operacionais diferentes do host (Windows em Linux, por exemplo).

Persistência mais simples devido ao armazenamento dedicado por VM.

Geralmente usa o mesmo sistema operacional do host (Linux em

Linux).

Necessita configuração adicional para persistência (volumes).

Linux, o verdadeiro salto veio com a introdução dos

<!-- image -->

cgroups

e

namespaces

, recursos nativos do kernel que possibilitam isolar recursos e visões de mundo entre processos. Essas tecnologias,

combinadas, formaram a base para ferramentas como o

LXC

, que trouxe uma forma prática e robusta de criar containers. Aqui traçamos essa linha evolutiva - não para detalhar cada tecnologia individualmente, mas para

mostrar como elas se conectam e contribuíram para o surgimento dos containers modernos. Entender essa trajetória ajuda a reconhecer que o Docker não surgiu do nada: ele é o resultado de anos de

experimentação, refinamento e avanços no ecossistema Linux.

Evolução das Tecnologias de Conteinerização

Início da

## Docker do zero: como usar e criar containers rodando Python

chroot (1979)

FreeBSD Jails

(2000)

OpenVz (2005)

cgroups (2006)

LXC (2008)

<!-- image -->

Conteinerização Moderna chroot

Oqueéochroot?

Principais avanços na Conteinerização

<!-- image -->

Típico usuário Linux dentro de um prisão chroot.

Umprograma que funciona nesse ambiente modificado não consegue acessar arquivos e comandos situados fora dessa estrutura de diretórios local. Este cenário modificado é chamado de prisão chroot

(ou chroot jail).

bin

•

etc

Emamarelo temos o sistema de arquivos. Em verde temos o sistema de arquivos reproduzido

/ (root)

emumaprisão chroot. Observe que muitas pastas são reproduzidas na prisão chroot, mas não

<!-- image -->

todas, já que o objetivo dessa prisão é isolar o usuário e garantir que ele não possa acessar todos os arquivos.

Umprisão chroot não é um ambiente seguro, pois no caso do usuário ter poderes administrativos é possível escapar da prisão e acessar todos os arquivos do sistema.

Para que serve?

•

Isolamento:

Limita o acesso de um processo ao sistema real. Muito usado por questões de segurança.

Ambientes controlados:

vos.

Permite criar ambientes de testes ou execução controlada de aplicati- bin

home

<!-- image -->

Cada 'Jail' do FreeBSD tem um sistema completo com próprio sistema de arquivos, separação de processos (programas) e endereço de IP.

## Docker do zero: como usar e criar containers rodando Python

<!-- image -->

Segurança

Complexidade

Limitada

Simples

Robusta

Moderada no mesmo servidor, sem que uma interfira na

Para que serve?

•

Hospedagem segura de múltiplas aplicações

## outra.

· Ambientes de desenvolvimento e testes com isolamento real. · Serviços de produção em que é necessário controle rigoroso e separação entre diferentes sistemas.

Papel histórico:

OFreeBSD Jail foi um dos primeiros passos em direção ao conceito moderno de containers

, e inspirou tecnologias posteriores como LXC e Docker no Linux. Ele mostra como sistemas Unix já buscavam

isolamento eficiente muito antes dos containers se popularizarem.

Para que serve?

<!-- image -->

•

Hospedar múltiplos clientes ou aplicações em um mesmo servidor físico com isolamento.

· Criar ambientes seguros de testes ou desenvolvimento.

•

Utilizar recursos do servidor de forma eficiente, com controle de uso por container.

Comparação com Outras Tecnologias

FreeBSD

Jail

SIM

SIM

SIM

NÃO

Alta

Característica

Isolamento de arquivos

Isolamento de processos

Isolamento de rede

Kernel separado

Eficiência de recursos

chroot

SIM

NÃO

NÃO

NÃO

Alta

OpenVZ

SIM

SIM

SIM

NÃO(compartilha kernel modificado)

Alta

Máquinas Virtuais

(como KVM)

SIM

SIM

SIM

(kernel próprio)

Menor

Limitação

Vale ressaltar que tratamos aqui do OpenVz original. A versão moderna do OpenVz não tem as mesmas limitações da versão original.

OpenVZ

se des- tacou por oferecer containers de alto desempenho e boa separação entre aplicações. No entanto, o

OpenVZ tinha uma limitação importante: ele exigia um para funcionar.

Isso significava que, para usar o OpenVZ, o administrador precisava substituir o kernel padrão por uma versão especial mantida pelos desenvolvedores do projeto.

Esse modelo oferecia vantagens técnicas, como melhor desempenho e funcionalidades extras de gerenciamento, mas também trazia desvantagens práticas. A dependência de um kernel não oficial

dificultava a adoção em ambientes corporativos ou em distribuições Linux mais rígidas quanto a estabilidade e suporte.

seguro.

Essa necessidade de um kernel customizado é um dos fatores que fizeram com que o OpenVZ, embora influente,

passou a investir em soluções baseadas em recursos namespaces

A versão original do OpenVZ foi desenvolvida

<!-- image -->

suas próprias extensões ao kernel

Papel histórico:

OOpenVZfoi um dos primeiros sistemas de containers amplamente utilizados em produção no mundo Linux, antes do surgimento do LXC e do Docker. Ele mostrou que era possível ter ambientes Linux totalmente isolados com grande desempenho , sem o peso de virtualização completa.

LXC

OqueéoLXC?

LXC (Linux Containers)

é uma tecnologia que permite criar os recursos do kernel, como

namespaces

e

cgroups modificado

.

, sem containers no Linux

usando diretamente necessidade de um hypervisor ou kernel

kernel customizado

-oqueresultou em um

. Em vez disso, a comunidade Linux cgroups

Docker

.

antes das funcionalidades modernas de na-

. Para adicionar

e

.

Tecnologia

Máquina Virtual

Docker

Kernel próprio?

Sim

Não

Isolamento Eficiência completo

Sim

Sim

Menor

Alta

FOCo principal

Emular sistemas inteiros

Containers de

<!-- image -->

Comparação entre Tecnologias de Containers/VM

Papel histórico:

## Docker do zero: como usar e criar containers rodando Python

recursos do sistema por grupos de processos .

<!-- image -->

Comcgroups, o sistema pode monitorar e impor restrições de CPU, memória, disco, rede e outros

recursos para diferentes conjuntos de processos, mantendo o sistema estável e prevenindo abusos (como um processo consumir toda a RAM e travar o servidor).

Pense nos cgroups como

'caixinhas de recursos'

. Cada grupo de processos recebe uma caixinha com uma certa quantidade de memória, CPU ou largura de banda. Se o grupo tentar ultrapassar esses

limites, o kernel impõe restrições automaticamente.

Para que serve cgroups?

· Evitar que um processo afete negativamente todo o sistema.

•

•

Garantir qualidade de serviço

(ex: dar mais CPU para processos críticos).

Isolar recursos entre containers ou aplicações.

•

Coletar estatísticas detalhadas de uso por processo ou grupo.

Utilize o comando mount

-l

|

grep cgroup2

para ver os cgroups

do seu sistema Linux.

<!-- image -->

•

Criaremos dois cgroups: grupo1 com 20% de CPU e grupo2 com 80% de CPU.

· Usaremos o controlador cpu.max para limitar o uso de CPU.

Executar processos bash em cada cgroup

:

· Rodaremos dois processos bash, cada um em um cgroup, executando um loop para consumir CPU.

•

Observaremos o uso de CPU para confirmar as limitações.

Verificar as diferenças

•

:

Compararemos o uso de CPU de cada processo para mostrar que os cgroups impõem limites distintos.

Comandos para o Experimento

1.

2.

Verificar cgroups v2

:

mount

|

grep cgroup2

Saída esperada é algo como:

cgroup2

on

/sys/fs/cgroup type

cgroup2

Se não aparecer, seu sistema deve estar usando cgroups v1 ou exige configuração adicional.

Instalar ferramentas de cgroups

No Ubuntu/Debian ou variantes:

:

2.

3.

3.

4.

5.

sudo apt

sudo apt

Criar dois cgroups sudo

sudo

Configurar limites de CPU

•

Para

•

sudo sudo

•

•

•

•

Para cgset

cgset sudo

Terminal 2 (para

<!-- image -->

grupo2

):

sudo cgexec -g cpu:/grupo2 bash -c

6. Monitorar o uso de CPU :

· Abra um terceiro terminal execute o comando abaixo para observar os processos. ps -ax -o pid,psr,pcpu,cmd,cgroup | grep while

•

Você verá que o processo em o processo em

grupo2

-

pid grupo1

usa aproximadamente 20% de uma CPU, enquanto usa aproximadamente 80%.

: exibe número do processo

-

-

-

-

psr

: exibe porcentagem de uso da cpu.

pscpu

: exibe número da cpu.

cmd:

exibe o comando .

cgroup

: exibe o cgroup do processo.

'while true;

do

:;

done'

<!-- image -->

o processo em grupo2

usará aproximadamente 80%.

· Isso demonstra que os cgroups aplicam limitações diferentes aos processos, mesmo sendo do

mesmotipo (bash).

Oquesãonamespaces?

Namespaces são uma funcionalidade do kernel Linux que permite

tem do sistema operacional

.

Cada namespace cria uma 'realidade paralela' para os processos que estão dentro dele. Isso significa que um processo pode ter sua própria

visão dos arquivos, da rede, dos usuários, dos processos isolar a visão que um processo

## Docker do zero: como usar e criar containers rodando Python

<!-- image -->

Tipo de

namespace Oqueele isola?

Processos (cada container tem seus próprios PIDs)

pid net Rede (interfaces, IPs, portas)

mnt

Pontos de montagem (sistemas de arquivos)

## uts

ipc

Nomedohost e nome do domínio

Comunicação entre processos (semaphores, filas)

user IDs de usuário e permissões cgroup Visão sobre cgroups (oculta a identidade do grupo de controle do qual o processo é membro)

Utilize o comando lsns

no Linux e veja a coluna

Experimento com Namespaces: Plano de Ação

Oobjetivo deste experimento é demonstrar o isolamento proporcionado pelos namespaces UTS do

Linux, criando dois processos bash

emnamespacesdistintos,cadaumcomumnomedehostdiferente.

Type que mostra os namespaces utilizados.

<!-- image -->

host são diferentes, demonstrando o isolamento do namespace UTS.

6. Testar outros comandos (opcional)

: Executar comandos como que apenas o hostname é isolado pelo namespace UTS.

7. Encerrar os processos : Finalizar os processos bash para limpar o ambiente.

Comandos para o Experimento

1.

2.

Criar o primeiro namespace UTS e iniciar o bash sudo

unshare

--uts

• Ocomando

/bin/bash unshare

O comando comando

exec atual.

Verificar o hostname no primeiro namespace

•

-c

"hostname

--uts bash

:

namespace1

&amp;&amp;

exec bash"

cria um novo namespace UTS

hostname namespace1

inicia um shell

, isolando o nome do host.

define o nome do host como bash

namespace1

. O

no novo namespace, substituindo o processo

:

No terminal do primeiro hostname

-

Este comando exibe o hostname atual do namespace, que deve ser confirmando que a alteração foi aplicada.

bash

:

whoami ou

ps para mostrar

,

namespace1

3.

4.

6.

•

•

•

sudo

•

echo sudo

sudo unshare

Similar ao passo 1,

<!-- image -->

atual, que está no novo namespace lista todos os namespaces UTS ativos no sistema,

. Procure o PID obtido em echo

. Este comandoretornaoidentificador

), que é único para o namespace criado.

cria outro namespace UTS. O comando

namespace2 define o nome do host como

umnovoshell unshare

bash

.

5. Verificar o hostname no segundo namespace :

· No terminal do segundo bash : hostname

-

Este comando exibe o hostname do segundo namespace, que deve ser

Determinar o namespace UTS no segundo namespace

•

No terminal do segundo echo

bash

$$

-

Retorna o PID do shell bash

, obter o PID:

no segundo namespace.

:

namespace2

. O comando exec

bash hostname

inicia

.

namespace2

--uts

-Encerra os shells bash , finalizando os namespaces associados.

<!-- image -->

Verificar o hostname do sistema original

· No terminal original:

hostname

-

Retorna o hostname original do sistema, confirmando que as alterações são locais aos namespaces.

:

9.

## Docker do zero: como usar e criar containers rodando Python

<!-- image -->

pois o namespace UTS afeta apenas o hostname.

•

Comentários Adicionais

:

-Persistência : Alterações no hostname são temporárias e limitadas ao namespace. O sistema global não é afetado.

-

Aplicação ao Docker

: Este experimento ilustra como namespaces UTS isolam o hostname, umconceito central para containers, onde cada container tem seu próprio ambiente iso-

## lado.

Comparação entre namespaces e cgroups

Característica cgroups namespaces

Foco principal

Limita uso de memória, CPU, disco

Oculta processos, rede, usuários

Usado em containers

Analogia

Controle de

Sim

Não

Essencial

'Quanto você pode usar'

recursos

Isolamento de

Não

Sim

Essencial

'O que você pode ver'

ambiente

•

•

•

•

hello-world

, e aprendeu a usar

,

docker start

e

docker rm

,

, FreeBSD

<!-- image -->

).

Neste capítulo, você conheceu os principais conceitos por trás das tecnologias que tornaram possível

o isolamento e a reprodução de ambientes computacionais - ferramentas fundamentais para a

Engenharia de Dados moderna. Vamos revisar os pontos mais importantes:

· Ambientes de Execução Reproduzidos e Isolados Você entendeu por que é essencial garantir que o ambiente onde o software é desenvolvido seja o mais próximo possível do ambiente onde ele será executado. Isso evita o clássico problema do

'mas na minha máquina funciona'.

Máquinas Virtuais vs Containers

Aprendeu as diferenças fundamentais entre essas duas abordagens. Enquanto as VMs simulam umsistema operacional completo, os containers compartilham o kernel do host e são mais leves

e rápidos.

Comandos Essenciais do Docker

Você executou seu primeiro container Docker com a imagem os comandos

docker run

,

docker ps

,

docker stop

que formam o ciclo básico de trabalho com containers.

Evolução Histórica dos Containers

Conheceu as tecnologias que prepararam o caminho para o Docker, como chroot

Jails, OpenVZ, e especialmente os recursos nativos do kernel Linux - que hoje sustentam o funcionamento dos containers modernos.

OPapel do LXC

Descobriu comooLXCfoioprimeirosistemadecontainerscompletonoLinuxecomoeleinspirou diretamente o surgimento do Docker.

namespaces

e

cgroups

-

•

Cgroups e Namespaces o funcionamento de containers (incluindo Docker), e realizou experimentos para entender o que

cada um isola.

<!-- image -->

•

<!-- image -->

•

NET namespace

IPC namespace

: possui sua própria pilha de rede (interfaces, IPs, roteamento).

: isola os recursos de comunicação entre processos.

· UTS namespace : permite definir hostname e nome de domínio separados. · MNTnamespace : isola o sistema de arquivos (pontos de montagem).

•

USER namespace

: permite mapear usuários do container para usuários diferentes no host.

Isso cria um ambiente no qual o container se comporta como se fosse uma máquina separada, mesmo rodando no mesmo kernel do host.

## Docker do zero: como usar e criar containers rodando Python

<!-- image -->

Processos Isolados, Kernel Compartilhado

Diferente de máquinas virtuais, containers compartilham o mesmo kernel do host.

Isso reduz o overhead , já que não é necessário virtualizar hardware ou carregar múltiplas instâncias de sistemas operacionais completos. Ao mesmo tempo, o isolamento fornecido pelo kernel garante que um container não interfira nos demais nem no sistema operacional subjacente.

Docker não é uma Máquina Virtual

Tanto Docker quanto máquinas virtuais criam ambientes isolados, mas o fazem de maneiras distintas. As VMs simulam um sistema completo com seu próprio kernel, o que aumenta o consumo de recursos.

Já o Docker compartilha o kernel do host, isolando apenas os processos, o que torna os containers mais leves e rápidos.

Além disso, o Docker facilita o empacotamento e a distribuição de aplicações com todas as depen- dências necessárias, promovendo portabilidade e consistência entre ambientes. Como não precisa

virtualizar hardware, é mais eficiente e ideal para desenvolvimento ágil, integração contínua e micros- serviços.

<!-- image -->

segundos

.

Baixa sobrecarga, já que roda

diretamente sobre o kernel do umaVM.

Alta sobrecarga, devido à virtualização do hardware e do sistema completo.

totalmente isolados host. Os processos estão isolados, mas Processos , não

visíveis no host

.

Containers são efêmeros por padrão, mas podem usar

volumes para persistência.

Menor nível de isolamento;

requer medidas adicionais para aumentar a segurança.

Muito mais fácil e rápido escalar horizontalmente (criar múltiplos

containers).

Ideal para microserviços,

aplicações stateless e CI/CD.

Pode ser seguro com configurações corretas.

visíveis fora da VM.

VMs têm sistemas de arquivos

persistentes por padrão.

Isolamento mais robusto por padrão, pois cada VM é

completamente independente

Escalar exige mais tempo e recursos, pois envolve

instanciar sistemas completos

Ideal para aplicações

.

monolíticas, sistemas legados

ou quando o isolamento forte é uma exigência (por exemplo, para

ambientes multiusuário críticos).

Overhead

Isolamento

Persistência

Segurança

Escalabilidade

Produção

.

Os Sabores do Docker

ODockerpodeserusadodeduasformasprincipais:

DockerEngine

é o núcleo do Docker, responsável por criar e gerenciar containers diretamente no Linux, utilizando o kernel do sistema para garantir isolamento e eficiência.

Já o

Docker Desktop comLinux

Emresumo:

•

Usuários Linux

•

Usuários de Windows/macOS

máquina virtual normalmente utilizam o Docker Desktop, que oferece uma expe-

Comparativo: Docker Engine vs Docker Desktop

Característica

Definição

Interface

S.O.

Produção

<!-- image -->

Linux nativamente. Pode ser instalado

emservidores Linux.

Recomendado para uso em produção

.

Aplicativo completo com interface gráfica, que inclui o Docker Engine e

Windows, macOS e Linux (utiliza VM

para rodar Docker Engine).

Não recomendado para produção.

Simples, leve e com menor sobrecarga. Voltado para desenvolvimento e testes locais. Desempenho Alto desempenho. Pode ter desempenho inferior por usar camadas de virtualização.

Uso

Recursos

Requer familiaridade com a linha de comando e configuração manual.

Baixo consumo, ideal para servidores e ambientes otimizados.

Mais amigável para iniciantes, com interface gráfica e configurações

automáticas.

Maior uso de memória e CPU, devido

à virtualização.

· Qual comando será executado quando o container iniciar.

<!-- image -->

Emresumo: o Dockerfile é o receituário

Docker Layers: blocos de construção

Cada instrução do Dockerfile (como

•

,

COPY

) cria um novo

Esses layers são

•

Docker utiliza empilhados

FROM

para montar um ambiente.

RUN

,

para formar a imagem.

cache de layers para acelerar construções e economizar espaço.

layer

(camada).

## Docker do zero: como usar e criar containers rodando Python

· Você pode iniciar, parar, pausar e excluir containers facilmente.

<!-- image -->

•

Containers são isolados

, leves e iniciam em segundos.

Ocontainer é a vida real da imagem - é quando o software de fato roda.

Docker Registry: um repositório de imagens

Um Docker Registry é um repositório centralizado para armazenar, gerenciar e distribuir imagens

Docker. Ele funciona como uma biblioteca onde você pode enviar (push) imagens criadas a partir de umDockerfile ou baixar (pull) imagens para usar localmente. Exemplos incluem o Docker Hub (padrão público), registries privados (como Amazon ECR ) ou registries locais hospedados internamente. As imagens no registry podem ser versionadas com tags (ex.: minha-imagem:latest) e compartilhadas

entre equipes ou ambientes, facilitando a portabilidade e a reutilização de imagens Docker.

Comotudose conecta

Dockerfile

<!-- image -->

Transforma um simples arquivo de configuração (Dockerfile) em um ambiente completo e funcional (container), garantindo portabilidade, reprodutibilidade e eficiência.

Experimento - Desmistificando o Isolamento do Docker

Umadasprincipais dificuldades ao comparar Docker com Máquinas Virtuais está em compreender o nível de isolamento que cada tecnologia oferece.

Enquanto

Máquinas Virtuais proporcionam um isolamento completo - com seu próprio sistema

operacional e kernel rodando sobre um ambiente virtualizado - o ele

compartilha o kernel do sistema operacional de mecanismos do próprio kernel, como

Para entender melhor esse modelo de simples

Docker adota um modelo diferente:

com os containers, isolando os processos por meio namespaces

e

cgroups

.

isolamento por processo, vamos realizar um experimento

. A ideia é observar o comportamento de um processo dentro do container e como ele aparece a partir do host (sistema principal).

Vamos utilizar o seguinte comando para criar um processo controlado:

tail

-f

/dev/null

Oqueesse comando faz?

Esse comando permanece em execução contínua, esperando que algo seja escrito no arquivo

/dev/null

Na prática, isso significa que o processo ficará ativo indefinidamente, sem produzir efeitos colaterais.

É ideal para manter o container em execução pelo tempo necessário, sem interferir no sistema.

Objetivo do Experimento

Oobjetivo deste experimento é demonstrar como o Docker isola processos dentro de containers, com- parando o

PID 1

e o comando ubuntu

, o experimento ilustra como o Docker usa namespaces para isolar o ambiente do container do sistema operacional host, permitindo que o mesmo processo tenha

IDs de processo (PIDs) diferentes dentro de cada namespace, apesar de ser o mesmo processo. O expe-

,

<!-- image -->

responsável pela gestão do ciclo de vida do container.

Etapas do Experimento

Etapa 1: Executando um container com imagem Ubuntu

Nesta primeira etapa, vamos iniciar um container a partir da imagem oficial do

será configurado para executar o comando tail

-f mantém o processo ativo sem gerar efeitos colaterais.

Ocontainer será nomeado como teste-pid . Para criá-lo e iniciá-lo, execute o seguinte comando emumterminal: docker run -dit --name teste-pid ubuntu tail -f /dev/null

Esse comando realiza duas ações: baixa a imagem do Ubuntu (caso ainda não esteja presente local- mente) e inicia o container em modo interativo e em segundo plano.

Detalhes do comando

•

docker run

: inicia um novo container.

/dev/null containerd-shim

Ubuntu

. O container

, que, como vimos anteriormente,

docker exec -it teste-pid bash

<!-- image -->

Esse comando inicia um novo shell Bash dentro do container, permitindo a execução de comandos como se estivéssemos diretamente logados em um sistema Ubuntu.

Detalhes do comando

•

docker exec

•

-i

: executa um comando dentro de um container ativo.

: mantém a sessão interativa, permitindo entrada de dados (ex.: digitar comandos).

## Docker do zero: como usar e criar containers rodando Python

<!-- image -->

tail

-f

/dev/null

definido como o processo principal do container - e, por padrão, o primeiro processo de qualquer

container recebe o PID 1 dentro de seu próprio namespace de processos.

PID (Process ID) é um número único que identifica um processo em execução dentro de um sistema operacional ou, no caso de um container Docker.

Esse detalhe será fundamental para a análise que faremos nas próximas etapas.

Neste ponto, já conseguimos observar uma diferença importante entre o ambiente do container e o sistema operacional do host. Dentro do container, o processo com PID 1 é o tail , que foi definido explicitamente no momento da

criação do container. Já no host Linux, o processo com PID 1 é o primeiro a ser iniciado na inicialização do sistema - e geralmente corresponde ao init ou ao systemd .

Para confirmar isso, em um terminal no host, execute:

ps

1

A saída será semelhante a:

PID

1

TTY

?

STAT

Ss

TIME

0:00

COMMAND

/sbin/init splash

<!-- image -->

• No host

, o processo de PID 1 é o

cional como um todo.

• No container

, o processo de PID 1 é o criado pelo Docker.

Essa distinção ilustra bem o modelo de isolamento por processo aplicado pelos containers.

Os comandos abaixo levam em consideração que o container que iniciamos a pouco seja o único ativo. No caso de mais de um container ativo, alguma adaptação é necessária.

Abra um novo terminal e execute o seguinte comando:

pgrep containerd-shim

Se somente um container estiver ativo, esperamos um único número mostrando o PID do processo containerd-shim

19762

O

containerd containerd-shim

é um processo leve no Docker que atua como intermediário entre o

(runtime do Docker) e o processo principal do container, gerenciando o ciclo de vida do container, mantendo fluxos de entrada/saída (STDIN, STDOUT, STDERR) abertos, cole-

tando códigos de saída e permitindo que containers sejam executados de forma independente.

, responsável por iniciar e gerenciar o sistema opera- systemd

tail

, executado de forma isolada, dentro do namespace

pstree

-p

19762

Observe que containerd-shim(19762)-+-tail(19786)

vez de

1

.

Outra maneira de chegar a essa conclusão é com o subcomando docker

<!-- image -->

top

Saída esperada:

UID

PID

PPID

C

STIME

TTY

TIME

CMD

root 19786 19762 0 15:36 pts/0 00:00:00 tail -f /dev/null

Detalhes da saída do subcomando top · PID (Process ID): é o número único que identifica um processo em execução no sistema. Na saída, o processo

host tail

-f

/dev/null tem

PID 19786

. Dentro do container, esse mesmo processo seria o pelo Docker.

PPID

(Parent

Process

ID):

Na saída, o

PPID 19762

containerd-shim

é

, indicando seu identificador no

PID 1

o PID

do processo

, devido ao namespace

'pai'

indica o processo pai de

.

que criou o processo

tail

-f usado

atual.

, que é o

/dev/null

•

é

19786

, em

<!-- image -->

•

Esta é a base da sua imagem. O Docker puxa a imagem alpine

do Docker Hub, que já

é composta por suas próprias camadas. A sua nova imagem começará com todas essas

camadas base do Alpine. Pense nisso como a 'primeira camada' visível da sua imagem.

2. RUN apk add --update --no-cache curl · Esta instrução executa o gerenciador de pacotes apk dentro da imagem alpine para instalar o

curl

. Todas as alterações no sistema de arquivos resultantes dessa instalação

(adição de arquivos binários do nova camada

curl

, bibliotecas, etc.) são capturadas e formam uma

. Essa camada é empilhada sobre as camadas base do alpine

. Se você

mudar apenas esta linha no futuro, o Docker invalidará o cache desta camada e de todas as subsequentes, mas manterá as camadas

FROM

alpine emcache.

## Docker do zero: como usar e criar containers rodando Python

<!-- image -->

leve de metadados, adicionada sobre as anteriores.

Benefícios dessa Estrutura de Camadas:

· Reutilização e Cache: cada camada é armazenada em cache. Se você fizer uma alteração em umalinha do Dockerfile, apenas essa linha e as linhas subsequentes serão reconstruídas. As ca-

madasanterioresquenãoforamalteradasserãoreutilizadasdocache, acelerandodrasticamente o processo de build.

· Eficiência de Armazenamento: se você tiver várias imagens baseadas em alpine , elas compartilharão as mesmas camadas base do alpine no disco, economizando espaço.

•

Versionamento Implícito:

cada alteração em uma camada pode ser vista como uma nova

'versão' de parte da sua imagem. · Distribuição Otimizada: ao compartilhar ou baixar uma imagem, apenas as camadas que ainda não existem localmente precisam ser transferidas, otimizando o uso da rede.

Boas práticas relacionadas

•

Posicione instruções que

Dockerfile.

raramente mudam

(como

RUN

apt-get

) no topo do install

,

<!-- image -->

Etapas do Experimento

Etapa 1: Baixe e prepare o material

Faça o download do arquivo ZIP fornecido no material do curso. Dentro dele, há uma pasta chamada alpine . Descompacte o arquivo ZIP e acesse a pasta alpine pelo terminal. Essa pasta contém os arquivos necessários para o experimento:

Dockerfile

e

entrypoint.sh

Etapa 2: Explore o rootfs

Na pasta alpine

, você encontrará o arquivo que é o

sistema de arquivos base arquitetura x86\_64.

(

alpine-minirootfs-3.21.3-x86\_64.tar.gz alpine-minirootfs-3.21.3-x86\_64.tar.gz

root filesystem

,

,

) da distribuição Alpine Linux, versão 3.21.3, para

Este arquivo contém os componentes essenciais de um sistema operacional

Alpine, como binários, bibliotecas e o shell

/bin/sh

, em um formato compactado. Ele é necessário porque fornece o ambiente inicial para a imagem Docker, permitindo que pacotes como

instalados e comandos sejam executados. No

Dockerfile curl

sejam

, esse arquivo é extraído para formar a base da imagem, possibilitando a construção de um ambiente funcional sem depender de imagens

pré-existentes do

Docker Hub imagem.

Etapa 3: Analise os arquivos

A pasta

Dockerfile alpine

, o que oferece maior controle e transparência sobre o conteúdo da

e

entrypoint.sh inclui dois outros arquivos cruciais:

.

•

FROM

RUN

ADD

Dockerfile scratch

alpine-minirootfs-3.21.3-x86\_64.tar.gz

COPY

apk add curl

chmod entrypoint.sh

ENTRYPOINT

RUN

CMD

+x

["curl"]

•

FROM scratch pré-configurado.

ADD

RUN

apk

COPY entrypoint.sh /

vos da imagem.

RUN

executado ao iniciar o container.

CMD

•

•

•

•

•

•

•

entrypoint.sh

#!/bin/sh

if [ "${1 # -}" != "${1}" ] || [ -z "$(command -v "${1}")" ] ; then set --curl "$@"

set

-e fi exec "$@" · set -e : faz o script falhar se qualquer comando retornar erro.

• O

if verifica se o primeiro argumento começa com

fornecido não existe. Nesse caso, o script define os argumentos adicionais.

exec "$@"

•

: executa o comando final (seja do script pelo comando.

Juntos, o

Dockerfile e o

entrypoint.sh

(indicando uma opção) ou se o comando curl

curl

-

como o comando padrão, preservando ou outro fornecido), substituindo o processo

criam uma imagem que executa o curl

mas permite flexibilidade para passar outros comandos ou URLs como argumentos.

por padrão, sem qualquer sistema

do Alpine para curl

, ne- do Ubuntu).

para a raiz do sistema de arqui- seja executável.

como o comando entrypoint.sh

: um script shell que gerencia a execução do container. Seu conteúdo é:

<!-- image -->

A saída esperada será:

<!-- image -->

REPOSITORY TAG IMAGE ID CREATED SIZE alpine-zero latest 83b065c8246a 14 seconds ago 15.3MB

Etapa 7: Execute o container e observe o resultado

Crie e execute um container a partir da imagem alpine-zero

com o comando:

## Docker do zero: como usar e criar containers rodando Python

Neste experimento, você aprendeu a criar uma imagem Docker do zero

<!-- image -->

mínima do Alpine Linux. Através do arquivo

, começando com uma base

, você configurou a instalação do e a cópia de um script entrypoint.sh , que gerencia a execução do container e permite baixar conteúdo de uma URL usando o curl . Tambémexploramos como exportar o sistema de arquivos de

umcontainer e observar a adição do

curl

Dockerfile curl

no caminho correto do sistema de arquivos. Esse processo ilustra como personalizar imagens Docker e configurar comportamentos específicos de execução para

## containers.

Experimento - Exportando, Removendo, Importando e Reutilizando uma Imagem

Docker Objetivo do Experimento

Oobjetivo deste experimento é aprender a gerenciar imagens Docker

fora do sistema local, expor- tando uma imagem para um arquivo, removendo-a do Docker, importando-a novamente e criando um

novo container a partir dela. Utilizando a imagem alpine-zero

exportar, limpar e restaurar imagens Docker, destacando a

, o experimento demonstra como portabilidade do Docker

. Com isso, você

poderá compartilhar ambientes, realizar backups ou migrar aplicações entre diferentes sistemas sem a necessidade de recompilação ou configuração adicional.

<!-- image -->

O arquivo alpine-zero.tar

será criado no diretório atual, contendo a imagem completa. Este

arquivo pode ser transferido para outra máquina (via USB, rede, etc.), permitindo que a imagem seja

usada em outro sistema com Docker instalado, de forma transparente, sem depender de um registry ou reconstrução.

Etapa

2:

Remover a imagem do sistema, alpine-zero

Para simular a preparação para uma migração ou limpeza, remova todos os containers associados à

imagem e a própria imagem:

docker docker

•

ps

-a

-q

--filter ancestor=alpine-zero

|

xargs

-r docker

rm

-f

: lista os IDs de todos os con- rmi

alpine-zero docker ps -a -q --filter ancestor=alpine-zero

tainers (ativos ou parados) que usam a imagem

-

alpine-zero

: inclui containers parados.

-

-

-a

-q

: retorna apenas os IDs.

--filter ancestor=alpine-zero

.

alpine-zero

.

containers incluindo

:

todos filtra

os containers

baseados que utilizem

na imagem

•

•

|

-

-

-f docker rmi alpine-zero

-

rmi

A imagem e seus containers são removidos do sistema.

alpine-zero onde a imagem será importada.

Etapa 3: Importar a imagem a partir do arquivo

Restaure a imagem transferido de outra máquina):

docker load -i

•

docker load

•

<!-- image -->

-i

A imagem alpine-zero é recriada no sistema com todos os

layers images

que

(que poderia ter sido e configurações originais, pronta

para uso como se tivesse sido construída localmente. Confirme com docker

images

. Este pro- cesso demonstra como a imagem pode ser restaurada em qualquer máquina com Docker, garantindo

portabilidade transparente.

Etapa 4: Criar um novo container usando a imagem carregada

Execute um container a partir da imagem docker

alpine-zero

•

run

--rm

Comando

•

docker

Parâmetro alpine-zero

restaurada:

'https://sample-files.com/downloads/documents/txt/simple.txt'

run

: cria e inicia um container a partir da imagem.

--rm

: remove o container após a execução, mantendo o sistema limpo.

<!-- image -->

principais

Existem dois tipos de volumes:

1. Volumes gerenciados pelo Docker (criando com

docker volume

create

)

· Armazenados em um diretório específico no sistema de arquivos do host, gerenciado pelo Docker. O local padrão é geralmente /var/lib/docker/volumes/ . · ODocker cuida da criação e gerenciamento dos volumes.

2.

Bind mounts

•

(liga uma pasta do host diretamente ao container)

Montam um diretório ou arquivo específico do sistema de arquivos do host diretamente no container. O caminho é especificado pelo usuário.

Ousuário é responsável por garantir que o diretório ou arquivo exista no host.

•

## Docker do zero: como usar e criar containers rodando Python

<!-- image -->

Etapa 2: Rodando o Container com o Volume Montado

Agora, vamos rodar o container usando a imagem alpine-zero , mapeando o diretório $HOME/Downloads do host para um diretório dentro do container. O comando a seguir realiza o download do arquivo simple.txt e o salva no volume, garantindo que ele persista no host.

## Execute o comando:

docker run

--rm

-v

$HOME/Downloads:/mnt alpine-zero

sh

-c

"curl

-o

/mnt/simple.txt https://sample-files.com/downloads/documents/txt/simple.txt" ↪ →

· docker run --rm : executa o container e o remove automaticamente quando a execução terminar.

•

•

•

-v

$HOME/Downloads:/mnt retório

:

monta o diretório dentro do container.

$HOME/Downloads

/mnt

$HOME/Downloads

Tudo o que for gravado em no host.

alpine-zero

: utiliza a imagem sh

alpine-zero

/mnt do host no di-

será persistido em já instalada.

-c "curl -o /mnt/simple.txt quivo

simple.txt

URL

: executa o comando curl

e armazená-lo no volume montado, ou seja, em host. URL é a longa url no fim do comando.

para baixar o ar-

$HOME/Downloads no

arquivo simple.txt

<!-- image -->

fosse armazenado no host, independentemente do ciclo de vida do container.

Esse processo de persistência é fundamental para cenários em que é necessário manter dados entre reinícios ou remoções de containers, e facilita o compartilhamento de arquivos entre o

container .

Experimento - Executando Script Python com Docker

Objetivo do Experimento

Oobjetivo deste experimento é aprender a utilizar a imagem oficial no Docker para criar um

explora o uso de container

volumes Docker e executar um

script Python host

e o python:3.13.5-bookworm

presente no host

. Oexperimento para mapear o diretório do host para o container, permitindo a

execução de scripts Python diretamente no ambiente do container.

Etapas do Experimento

Etapa 1: Fazendo o Pull da Imagem Python:3.13.5-bookworm

Primeiro, vamos garantir que a imagem python:3.13.5-bookworm

Execute o comando abaixo para fazer o pull da imagem:

esteja disponível localmente.

docker

Este comando baixa a imagem oficial do Python baseada no Debian Bookworm. Após o download, a imagem estará disponível localmente.

Etapa 2: Mostrando a Imagem Obtida

Agora, vamos verificar se a imagem foi corretamente baixada. Execute o comando abaixo para listar todas as imagens no seu sistema:

docker images

A saída esperada será algo semelhante a:

REPOSITORY

python

Etapa 3: Criando um Container com a Imagem Obtida

Agora, vamos criar um container a partir da imagem comando

docker

•

<!-- image -->

run

-dit

--name python-teste

--name python-teste python:3.13.5-bookworm

: dá ao container o nome tail

-f

/dev/null python-teste

.

· tail -f /dev/null : mantém o container ativo sem realizar nenhuma ação.

Etapa 4: Verificando se o Container foi Criado e Está Ativo Vamos verificar se o container python-teste foi criado corretamente e se está ativo. Execute o comando:

docker ps

A saída esperada será:

e executar o

Etapa 7: Criando e Preparando o Script Python no Host

<!-- image -->

Agora, vamos criar um script Python no diretório $HOME/scripts do host . 1. Se o diretório $HOME/scripts ainda não existir, crie-o com o comando:

mkdir

-p

$HOME/scripts

Crie o script usando o editor de texto

2.

micro

(ou outro editor de sua preferência):

## Docker do zero: como usar e criar containers rodando Python

<!-- image -->

Etapa 9: Executando o Script Python Usando Docker e Volumes

Agora, vamos rodar o container novamente, mapeando o diretório

container e executar o script Python diretamente.

Execute o comando:

docker run

--rm

-v

$HOME/scripts:/mnt

A saída esperada será:

Executando script Python, versão: 3.13.5 (main, Jun 12 2025, 22:47:08) [GCC 12.2.0]

Conclusão do Experimento

Neste experimento, você aprendeu a utilizar a imagem oficial do Python

no Docker para criar contai- ners, verificar a versão do Python e executar scripts diretamente dentro de containers. Além disso,

exploramos o uso de volumes Docker

para mapear um diretório do host para o container, permitindo que o script Python presente no host fosse executado no ambiente Docker. Esse processo facilita a

criação de ambientes de desenvolvimento isolados e a persistência de dados, permitindo a execução de código em containers de forma prática e eficiente.

$HOME/scripts do host para o

python:3.13.5-bookworm

/mnt/script.py

<!-- image -->

•

•

e restaurar volumes, o que facilita a gestão de dados persistentes (usando comando

Maior Segurança e Desempenho tar

).

: volumes podem ser configurados com permissões e po- dem usar o sistema de arquivos mais adequado ao Docker, além de serem otimizados para

desempenho.

Compartilhamento entre Containers

: volumes permitem que múltiplos containers comparti- lhem dados de forma simples e segura, sem a necessidade de manipulação direta do sistema de

arquivos do host.

Objetivo do Experimento

O objetivo deste experimento é aprender a utilizar volumes Docker

para persistir dados fora do container, sem depender de bind mounts. Vamos criar um volume Docker, usá-lo para armazenar dados

de um container e, posteriormente, garantir que esses dados permaneçam persistentes mesmo após a remoção do container. Esse experimento também explorará como volumes podem ser compartilhados

entre diferentes containers.

Etapas do Experimento

Etapa 1: Criando um Volume Docker

A primeira etapa do experimento é criar um volume Docker. Execute o comando abaixo para criar um volume chamado

meu-volume

:

docker volume

Etapa 2: Executando um Container com o Volume

Agora, vamos rodar um container usando o volume usar a imagem oficial do

volume no diretório docker

run

-dit

•

-dit pouco redundante usar

ideia ruim memorizar ner.

-v tainer.

tail -f /dev/null

com ele depois.

<!-- image -->

Etapa 3: Verificando o Volume Criado

Para verificar se o volume foi criado corretamente, execute o comando: docker volume ls

Você verá o volume meu-volume

listado entre os volumes disponíveis.

Etapa 4: Gravando Dados no Volume

Agora, vamos gravar alguns dados no volume montado. Execute o comando para acessar o container:

que acabamos de criar. Vamos

. Execute o comando abaixo para iniciar o container e montar o

/dev/null

. No comando acima é um

. Mas não é uma

) interativo (parâmetro

i

) para ao contai-

dentro do con-

: mantémocontainerativosemfazernada,paraquepossamosinteragir

•

•

•

<!-- image -->

Este

é

um teste

de persistência

de volume

no

Docker!

Etapa 6: Removendo o Volume Após verificar que os dados persistiram, podemos remover o volume para finalizar o experimento. Para remover o volume, execute o comando:

docker volume

rm meu-volume

Isso removerá o volume do Docker, apagando permanentemente os dados armazenados nele.

## Docker do zero: como usar e criar containers rodando Python

<!-- image -->

Etapas do Experimento

Etapa 1: Criando um Volume Docker

Primeiro, vamos criar um volume Docker vazio. Execute o comando abaixo para criar o volume:

## docker volume create

meu-volume

Este comando cria um volume chamado meu-volume . Ele será utilizado para armazenar dados que, posteriormente, serão copiados e gerenciados.

Etapa 2: Rodando um Container com o Volume

Agora, vamos rodar um container usando o volume que acabamos de criar. Vamos usar a imagem oficial do

Alpine Linux para manter o experimento simples e leve.

Execute o comando para iniciar o container e montar o volume no diretório ner:

/data dentro do contai-

<!-- image -->

Dentro do container, execute o seguinte comando para criar um arquivo de texto no diretório echo

"Este

é

um teste

de backup

e

restauração de

volume no

Etapa 4: Verificando os Dados no Volume

Apósagravaçãodoarquivo,saiadocontainercomocomando

Docker!"

exit

&gt;

/data/teste.txt

. Vamosagoraverificar se o arquivo foi corretamente gravado no volume. Para isso, acesse o volume diretamente, usando o comando:

docker run

--rm

-v meu-volume:/data

alpine

Isso deve exibir o conteúdo do arquivo

Este

é

cat

/data/teste.txt teste.txt

:

um teste de backup e restauração de volume no Docker!

Etapa 5: Fazendo Backup do Volume

Agora que os dados estão armazenados no volume, vamos fazer um docker

run com

tar backup

desse volume. O comando

é uma maneira simples de realizar o backup de volumes Docker.

Execute o seguinte comando para fazer o backup do volume backup como

meu-volume-backup.tar.gz

:

meu-volume e salvar o arquivo de

/data

:

docker run

→

/backup/meu-volume-backup.tar.gz

↪

•

•

•

-v do container.

-v tar

czf umarquivo

tar.gz

.

Etapa 6: Removendo o Volume Original

Agora, vamos remover o volume original para simular uma situação onde o volume foi perdido, como após uma falha de sistema ou exclusão acidental.

Execute o comando para remover o container e o volume:

docker rm

-f docker

volume

Etapa 7: Restaurando o Backup do Volume

<!-- image -->

Agora, vamos restaurar o volume a partir do arquivo de backup

Para isso, criamos um novo volume e restauramos os dados nele.

Execute o comando para criar um novo volume:

docker volume create meu-volume-restaurado Agora, vamos restaurar os dados do arquivo de backup para o novo volume. Execute o seguinte comando:

docker run

→

/backup/meu-volume-backup.tar.gz

-C

/volume

↪

Isso irá descompactar os dados do arquivo de backup para o volume restaurado.

meu-volume-backup.tar.gz

--rm

--rm meu-volume-restaurado:/volume

$PWD:/backup tar

/volume dentro

/backup dentro do

: Comprime e cria cria arquivos compactados do tipo

-v

-v alpine

xzf

.

<!-- image -->

entre ambientes, eliminando problemas como 'na minha máquina funciona'. Isso é

lamento essencial para desenvolvimento, testes e produção.

· Isolamento de Containers : Você aprendeu como o Docker utiliza namespaces (PID, NET, IPC, UTS, MNT, USER) e cgroups para isolar processos e limitar recursos, além de Union File Systems para criar camadas de arquivos eficientes. Isso permite que containers sejam leves, rápidos e isolados, compartilhando o kernel do host.

Diferença entre Containers e Máquinas Virtuais

: Você comparou containers com VMs, enten- dendo que containers são mais eficientes por não virtualizarem hardware ou sistemas operacio-

nais completos, sendo ideais para microsserviços e integração contínua.

•

## Docker do zero: como usar e criar containers rodando Python

<!-- image -->

.

: Você construiu a imagem

com comandos como pgrep e pstree -Construção de Imagem do Zero

rootfs

Alpine, configurandoo eumscript

alpine-zero a partir de um

paraexecutardownloads via URL, aprendendo como o Dockerfile e o entrypoint.sh trabalham juntos. -Exportação e Importação de Imagens : Você exportou a imagem alpine-zero para

um arquivo TAR com

## docker load

curl entrypoint.sh

, removeu-a com docker save

docker rmi

, importou-a com

, e executou um container, demonstrando a portabilidade do Docker entre máquinas.

-Persistência com Volumes : Você usou bind mounts para persistir dados em $HOME/Downloads e volumes gerenciados pelo Docker para armazenar e compartilhar dados entre containers, aprendendo como volumes garantem persistência mesmoapós a remoção de containers. -Backup e Restauração de Volumes : Você criou um volume, gravou dados, fez backup com

tar

, removeu o volume e restaurou os dados, destacando a robustez dos volumes para gerenciamento de dados críticos.

- ExecuçãodeScriptsPython

: Você utilizou a imagem python:3.13.5-bookworm

para executar um script Python via volumes, explorando como containers podem ser usados

para desenvolvimento isolado.

Boas Práticas

: Você aprendeu a otimizar Dockerfiles, posicionando instruções que mudam

•

<!-- image -->

Anexo A: Dicionário de Termos Docker

Termo

Container

Imagem

Dockerfile

Volume

Bind Mount

Docker Engine

Docker CLI

Docker Daemon

(dockerd)

Docker Compose

Docker Hub

Layer

Pull

Push

Context

Entrypoint

<!-- image -->

compostas por várias layers.

Build Processo de construção de uma imagem a partir de um Dockerfile.

Run

Comando para iniciar um container a partir de uma imagem.

Tag Rótulo atribuído a uma imagem para facilitar sua identificação e versionamento.

Network Recurso de rede interno do Docker que conecta containers entre si e com o exterior. Registry Serviço para armazenamento e distribuição de imagens Docker (ex: Docker Hub,

GitHub Container Registry).

Ação de baixar uma imagem de um registro (registry).

Ação de enviar uma imagem local para um registro.

Ambiente de execução atual usado pela CLI do Docker (local, remoto, etc).

Comando padrão que é executado quando um container é iniciado a partir de umaimagem.

| Termo           | Descrição                                                                                |
|-----------------|------------------------------------------------------------------------------------------|
| CMD             | Parâmetro default para execução dentro do container, que pode ser sobrescrito.           |
| Namespace       | Mecanismo do kernel Linux usado para isolamento de recursos emcontainers.                |
| Cgroups         | Control groups do Linux usados para limitar e monitorar recursos como CPU, memória, etc. |
| Overlay Network | Rede virtual que permite a comunicação entre containers emdiferentes hosts.              |
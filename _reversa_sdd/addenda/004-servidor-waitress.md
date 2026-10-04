# Adendo: servir a aplicação por um servidor de produção no Windows

> Identificador da feature: `004-servidor-waitress`
> Data: `2026-10-03`
> Cenário: **legado** (âncora em `_reversa_sdd/architecture.md` + `_reversa_sdd/domain.md`)

## Vigência

Vigente desde 2026-10-03.

## Resumo da entrega

A aplicação deixou de subir pelo servidor de desenvolvimento com o modo de depuração ligado. O bloco de entrada do `src/app.py` passa a iniciar a aplicação por um servidor WSGI de produção, com endereço de escuta, porta e concorrência lidos de variáveis de ambiente e padrões declarados no código. O servidor de desenvolvimento e a depuração deixam de existir, e o aviso de servidor de desenvolvimento desaparece junto. Nenhuma rota, campo de formulário ou mensagem de contrato foi alterada.

**Progresso: 8 de 11 ações concluídas.** Duas estão bloqueadas pela política de edição, e uma não foi verificável nesta execução. As três estão declaradas ao final deste adendo, e nenhuma delas é trabalho de código inacabado.

Provas medidas nesta entrega: o teste novo do bloco de entrada falhava antes da mudança, com três falhas, e passa depois, com três aprovações. A suíte ficou em **121 aprovados e 15 erros de ambiente**, contra a linha de base de 118 aprovados e os mesmos 15 erros, o que dá exatamente os três testes acrescentados. A paridade diferencial contra o oráculo congelado permanece em **100 por cento nas 6 fixtures**, com zero divergência.

## Impacto por artefato da extração

| Artefato | Seção | Tipo de impacto | Delta |
|---|---|---|---|
| `_reversa_sdd/inventory.md` | `#4` (Pontos de Entrada) | `regra-alterada` | A descrição do ponto de entrada, que registra a chamada ao servidor de desenvolvimento com depuração, deixou de valer. Leia como: servidor WSGI de produção, iniciado pelo bloco de entrada |
| `_reversa_sdd/inventory.md` | `#4` (Pontos de Entrada) | `contrato-novo` | Três variáveis de ambiente passam a configurar a execução, com padrões declarados: endereço de escuta, porta e concorrência |
| `_reversa_sdd/inventory.md` | `#6` (Cobertura de Testes) | `componente-novo` | Um arquivo de teste novo cobre o bloco de entrada por inspeção, sem abrir porta e sem importar o aplicativo |
| `_reversa_sdd/architecture.md` | `#6` (Resumo para o Reversa) | `regra-alterada` | A dívida do servidor de produção listado e não usado muda de natureza: passa a existir uso, e o que está listado é justamente a dependência que **não importa na plataforma alvo** |
| `_reversa_sdd/architecture.md` | `#3.3` (Estruturas de runtime) | `regra-alterada` | O endereço de escuta padrão passou a atender todas as interfaces de rede, e antes só a máquina local respondia. A pasta de upload continua sendo `src/uploads/`, resolvida pela mesma função ancorada no arquivo do aplicativo |
| `_reversa_sdd/dependencies.md` | `#2` (Dependências Diretas) | `regra-alterada` | **Pendente.** A troca do servidor no arquivo de dependências está planejada e bloqueada pela política. Leia o arquivo como ainda contendo o servidor que não sobe no Windows |
| `_reversa_sdd/code-analysis.md` | seção do componente de camada de rota | `regra-alterada` | O bloco de entrada do `app.py` tem conteúdo novo, e o módulo ganhou uma importação de `sys` no topo, usada apenas na mensagem de dependência ausente |
| `_reversa_sdd/domain.md` | `#4.1` e `#4.2` (Contrato de mensagens) | `presença` | Nenhuma mensagem de contrato muda: elas permanecem literais. É a `RN-01` da feature, e a suíte e a paridade a sustentam |

**Nenhuma regra de negócio do domínio foi criada, alterada ou removida.** O que mudou está no contrato de operação da aplicação, e não em `_reversa_sdd/domain.md#2` nem em `#3`.

## Regras sob vigilância

`W001`, `W002`, `W003`, `W004` e `W005`, definidos em `_reversa_forward/004-servidor-waitress/regression-watch.md`.

`W001` cobre o servidor de produção no ponto de entrada, `W002` cobre as três variáveis de ambiente, `W003` cobre a superfície HTTP e as mensagens de contrato, `W004` cobre o registro do servidor no arquivo de dependências e `W005` cobre a suíte e a paridade.

**`W004` está declarado como não satisfeito nesta data**, porque a ação que troca o servidor no arquivo de dependências está bloqueada pela política. O item entrou no watch já com a condição pendente, para que uma verificação futura não o trate como cumprido.

## Pendências declaradas

| Pendência | Ação | Motivo |
|---|---|---|
| O servidor de produção não está registrado no arquivo de dependências | `T001` | O caminho `requirements.txt` não casa com nenhum glob de `allowedPaths` em `.reversa/reversa-config.json`. A política manda recusar a escrita, e a liberação é ato exclusivo do usuário |
| A instalação a partir do arquivo atualizado não foi executada | `T002` | Consequência direta da `T001` |
| A falha por porta ocupada não foi verificada | `T011` | Duas razões, ambas registradas: a sandbox nega o diretório temporário que o `pip` usa para desempacotar, e **nenhuma ação do plano implementa mensagem legível para porta ocupada**, embora o cenário correspondente do `requirements.md` exija isso |

**Consequência operacional enquanto a `T001` estiver bloqueada:** uma instalação limpa a partir do arquivo de dependências não terá o servidor de produção. A aplicação sobe até o bloco de entrada e termina com mensagem que nomeia o pacote e o interpretador exato, sem abrir porta. Esse comportamento foi verificado, é o esperado, e não é defeito.

## Fontes

- `_reversa_forward/004-servidor-waitress/legacy-impact.md` (fonte principal do delta)
- `_reversa_forward/004-servidor-waitress/regression-watch.md`
- `_reversa_forward/004-servidor-waitress/requirements.md`
- `_reversa_forward/004-servidor-waitress/roadmap.md`
- `_reversa_forward/004-servidor-waitress/actions.md` (8 de 11 ações concluídas)
- `_reversa_forward/004-servidor-waitress/progress.jsonl`

## Atualização 2026-10-04

> **Segunda sincronização, no dia seguinte.** O conteúdo acima **não foi alterado**: esta seção apenas acrescenta o delta novo. Onde ela contradizer o que está escrito antes, esta seção é a leitura correta.

### O modo de produção foi verificado ao vivo

O aplicativo foi executado pelo usuário e verificado por requisição real, e não por inspeção de código: `HTTP 200` na rota raiz, cabeçalho de resposta `Server: waitress`, formulário de upload presente na página, e três requisições seguidas estáveis com o mesmo tamanho de resposta. O servidor de produção está atendendo de fato.

O endereço em uso foi `127.0.0.1`, e não o padrão `0.0.0.0` declarado no código. Isso indica que a variável `ANALISADOR_HOST` estava definida na sessão da execução, já que não existe variável persistente no ambiente do usuário, e o cabeçalho `Server: waitress` confirma que o código em execução é o desta feature. O efeito é o modo restrito à máquina local, que é o mais seguro, e portanto o cenário de acesso por outro equipamento **não** estava ativo nesta execução.

### A pendência da `T011` muda de natureza

A seção anterior declarou a `T011` como não verificável. Ela **foi executada em 2026-10-04**, e o resultado contradiz a premissa do cenário:

| Artefato | Seção | Tipo de impacto | Delta |
|---|---|---|---|
| `_reversa_forward/004-servidor-waitress/requirements.md` | `#7` (Critérios de Aceitação), cenário de porta em uso | `regra-removida` | O cenário descreve uma falha que **não acontece no Windows**: duas instâncias do servidor escutam na mesma porta ao mesmo tempo, então não há erro a reportar nem código de saída diferente de zero. O cenário precisa ser reescrito ou retirado, e isso é decisão do usuário |
| `_reversa_forward/004-servidor-waitress/requirements.md` | `#10` (Lacunas) | `regra-nova` | Surge uma lacuna que a versão inicial não previa: como impedir duas instâncias simultâneas, já que a plataforma não impede sozinha |
| `_reversa_sdd/architecture.md` | `#3.3` (Estruturas de runtime) | `regra-alterada` | Com duas instâncias, cada processo tem o **seu próprio** estado global da árvore genealógica, e duas requisições do mesmo navegador podem ser atendidas por processos diferentes. É a mesma classe do defeito de exposição de estado já registrado no projeto |

O experimento foi controlado, numa porta livre, e nenhum resíduo ficou no ambiente: os processos foram encerrados e as portas liberadas, conferido por `netstat`.

**O que continua igual:** a `T001` e a `T002` seguem bloqueadas pela política de edição, e a consequência operacional descrita acima permanece exata.

### Fontes desta atualização

- `_reversa_forward/004-servidor-waitress/actions.md` (Notas de execução de 2026-10-04)
- `_reversa_forward/004-servidor-waitress/regression-watch.md` (observações `O6` a `O8`)
- `_reversa_forward/004-servidor-waitress/progress.jsonl` (linha de 2026-10-04)

## Atualização 2026-10-04 (rodada 2)

> **Terceira sincronização, na mesma data da anterior.** O conteúdo acima **não foi alterado**. A frase final da seção anterior, que declarava a `T001` e a `T002` bloqueadas, **deixou de valer** com o que esta seção registra.

### A pendência de dependência foi fechada

O usuário acrescentou `requirements.txt` aos caminhos liberados em `.reversa/reversa-config.json`, e as duas ações que estavam bloqueadas foram executadas:

| Ação | O que foi feito | Prova |
|---|---|---|
| `T001` | O arquivo de dependências perdeu `gunicorn`, que não importa no Windows por exigir `fcntl`, e ganhou `waitress`. O arquivo ficou em ordem alfabética, e o espaço final que a linha antiga trazia desapareceu com ela | Conferência do conteúdo do arquivo |
| `T002` | `pip install -r requirements.txt` executado no interpretador do projeto | Código de saída **0**, com `waitress 3.0.2` no diretório de pacotes do usuário, visível tanto para `py -3.14` quanto para `python` |

Suíte remedida depois da mudança: **121 aprovados e 15 erros de ambiente**, idêntico. O `gunicorn` continua instalado na máquina, e isso é inofensivo: ele deixou de ser dependência do projeto, que é o que a leitura da extração precisa saber.

### O que muda neste adendo

| Artefato | Seção | Tipo de impacto | Delta |
|---|---|---|---|
| `_reversa_sdd/dependencies.md` | `#2` (Dependências Diretas) | `regra-alterada` | A entrada que descrevia o servidor de produção sem uso interno **deixa de valer na letra**: o projeto passa a ter um servidor de produção em uso, e a dependência listada é o `waitress`, não o `gunicorn`. A leitura correta é: o arquivo lista `Flask`, `ged4py`, `networkx`, `pandas`, `thefuzz` e `waitress` |
| `_reversa_sdd/architecture.md` | `#6` (Resumo para o Reversa) | `regra-alterada` | A dívida que dizia que o servidor de produção listado **não é usado no código** está **resolvida**: agora há uso, e a dependência inoperante saiu do arquivo |

### O que continua pendente

A `T011` segue aberta, e a razão está registrada na seção anterior: o cenário de porta ocupada descreve uma falha que **não acontece no Windows**, porque duas instâncias do servidor escutam na mesma porta ao mesmo tempo. O `requirements.md` precisa de decisão do usuário: reescrever o cenário ou retirá-lo, e decidir se o projeto passa a impedir instâncias simultâneas por conta própria.

### Fontes desta atualização

- `requirements.txt` (conteúdo atual)
- `_reversa_forward/004-servidor-waitress/actions.md` (10 de 11 ações concluídas)
- `_reversa_forward/004-servidor-waitress/regression-watch.md` (observação `O9`, e `W004` passando a satisfeito)
- `_reversa_forward/004-servidor-waitress/progress.jsonl` (linhas de `T001` e `T002`)

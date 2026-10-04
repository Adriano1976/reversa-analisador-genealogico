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

## Atualização 2026-10-04 (rodada 3)

> **Quarta sincronização, na mesma data.** O conteúdo acima **não foi alterado**. Onde esta seção contradizer o que está escrito antes, esta seção é a leitura correta. Em especial: a `T011` **deixou de estar pendente**, e a decisão que a seção anterior pedia ao usuário **já foi tomada**, na sessão de esclarecimento de 2026-10-04.

### A feature está completa

**Vinte de vinte ações concluídas.** As nove ações da segunda rodada (`T012` a `T020`) mais a `T011`, que foi reescopada na mesma sessão.

As três mudanças observáveis que a rodada entrega, com o requisito que as sustenta:

| Mudança | Antes | Depois | Requisito |
|---|---|---|---|
| Endereço de escuta padrão | `0.0.0.0`, atendia todas as interfaces de rede | `127.0.0.1`, atende apenas a máquina local, e abrir para a rede exige `ANALISADOR_HOST` | `RN-03`, `RF-02`, `D-02` revista |
| Instâncias simultâneas | coexistiam na mesma porta, cada uma com o seu próprio estado global | a segunda é recusada, com mensagem legível e código de saída 1, e a primeira segue atendendo | `RN-05`, `RF-08`, `D-10`, `D-11` |
| Versões das dependências | em aberto | fixadas com `==`, nas versões validadas | `RN-06`, `RF-09`, `D-12` |

Provas medidas nesta rodada: a suíte ficou em **125 aprovados e 15 erros de ambiente**, contra 121 aprovados e os mesmos 15 erros na medição anterior, o que dá exatamente as quatro afirmações acrescentadas ao teste do bloco de entrada. A paridade diferencial permanece em **100 por cento nas 6 fixtures**, com zero divergência. A recusa da segunda instância foi verificada com dois processos reais, e não por inspeção.

O padrão do endereço também foi verificado ao vivo, nos dois lados do critério da `RF-02` e com controle positivo: sem a variável definida, a escuta ficou em `127.0.0.1` e a aplicação respondeu `HTTP 200` na máquina local e **não** respondeu no endereço de rede dela (`192.168.1.40`); com `ANALISADOR_HOST=0.0.0.0`, a escuta ficou em `0.0.0.0` e respondeu nos dois endereços. O controle positivo existe para que o resultado negativo não seja confundido com uma sondagem quebrada.

### O cenário que a seção anterior pedia para decidir foi decidido

A seção anterior encerrou pedindo decisão do usuário sobre o cenário de porta ocupada. A sessão de esclarecimento de 2026-10-04 tomou as quatro decisões, e elas estão implementadas:

1. O cenário foi reescrito para o comportamento medido, e a exclusividade virou requisito novo, em vez de comportamento esperado da plataforma (`RN-05`, `RF-08`).
2. A aplicação passou a impedir duas instâncias por conta própria, com mensagem legível e código de saída diferente de zero (`D-10`, `D-11`).
3. O padrão do endereço passou a ser a máquina local (`D-02` revista).
4. Todas as dependências passaram a ter versão fixada (`RN-06`, `RF-09`, `D-12`).

### Como a exclusividade foi obtida

O bloco de entrada cria o socket de escuta, marca-o com `SO_EXCLUSIVEADDRUSE` no Windows, liga-o com `bind` e `listen`, e o entrega pronto ao servidor. O socket fica aberto até o processo terminar, e é isso que fecha a janela entre ligar e servir.

Dois achados restringem a implementação e ficam registrados:

- O servidor **recusa** receber socket pronto junto de `host` ou `port`, com `ValueError` (`waitress/adjustments.py`, linhas 299 e 300). O endereço e a porta passaram a existir apenas no socket ligado, e a linha de inicialização impressa pela aplicação é a única observabilidade do endereço em uso.
- A mensagem de recusa separa os dois motivos possíveis, porque eles pedem ações diferentes: `errno.EADDRINUSE`, que vale `10048` neste interpretador, para porta ocupada, e `10049` para endereço que não pertence à máquina. A separação foi medida, e não suposta.

### Correções declaradas

| O que foi corrigido | Onde | Por quê |
|---|---|---|
| A justificativa da `D-10` afirmava que o servidor não faz `bind` **nem** `listen` com socket pronto | `roadmap.md`, `onboarding.md`, observação `O12` do `regression-watch.md` | A leitura da fonte instalada mostra que ele pula o `bind`, mas chama `socket.listen(self.adj.backlog)` em `accept_connections` |
| A mensagem de dependência ausente mandava instalar o pacote avulso | `src/app.py`, `onboarding.md` | Passou a contradizer a versão fixada, porque uma instalação avulsa traria versão diferente da validada. Passou a nomear o pacote, o interpretador e o arquivo de dependências |
| O procedimento da dependência ausente mandava instalar o arquivo de dependências no ambiente descartável e rodar em seguida | `onboarding.md` | O arquivo inclui o servidor de produção, então o passo **não testava ausência alguma**. Passou a exigir a desinstalação no ambiente descartável |
| A seção de deploy afirmava que o arquivo de dependências inclui o Gunicorn | `README.md` | A execução da `T001`, na rodada anterior, tornou a afirmação falsa |
| A contagem de linhas do `app.py` e a árvore de testes do `README.md` | `README.md` | Desatualizadas, e a árvore não listava o teste do bloco de entrada |

### Impacto por artefato da extração

| Artefato | Seção | Tipo de impacto | Delta |
|---|---|---|---|
| `_reversa_sdd/inventory.md` | `#4` (Pontos de Entrada) | `contrato-alterado` | O ponto de entrada passa a criar e ligar o socket de escuta, a entregá-lo pronto ao servidor e a recusar a subida quando o endereço e a porta já estão em uso. O padrão do endereço passa a ser a máquina local |
| `_reversa_sdd/inventory.md` | `#6` (Cobertura de Testes) | `regra-alterada` | O arquivo de teste do bloco de entrada passou de três para sete afirmações: guarda de exclusividade, entrega do socket, recusa com código diferente de zero e padrão do endereço |
| `_reversa_sdd/architecture.md` | `#3.3` (Estruturas de runtime) | `regra-alterada` | A coexistência de instâncias, que a medição registrou, passa a ser impedida pela própria aplicação. O estado global por processo continua sendo a razão de impedir |
| `_reversa_sdd/dependencies.md` | `#2` (Dependências Diretas) | `contrato-alterado` | Cada linha passa a declarar a versão com `==`, nas versões validadas nesta máquina em Python 3.14. As dependências transitivas continuam em aberto, e a razão está na `D-12` |
| `_reversa_sdd/code-analysis.md` | seção do componente de camada de rota | `regra-alterada` | O bloco de entrada cresceu com o socket de escuta, a guarda de exclusividade e a recusa. O módulo ganhou as importações de `socket` e `errno` no topo, ao lado de `sys` |
| `_reversa_sdd/domain.md` | `#4.1` e `#4.2` (Contrato de mensagens) | `presença` | Nenhuma mensagem de contrato do domínio muda, e a paridade em 100 por cento nas 6 fixtures sustenta a afirmação. A mensagem de operação que mudou, a de dependência ausente, não pertence ao contrato HTTP |

### Regras sob vigilância acrescentadas

`W006`, `W007` e `W008`, definidos em `_reversa_forward/004-servidor-waitress/regression-watch.md`: a guarda de exclusividade no bloco de entrada, o padrão fechado do endereço e a versão fixada em toda linha do arquivo de dependências.

### Higiene

Os processos dos experimentos foram encerrados, as portas usadas foram liberadas, os scripts de verificação foram removidos e o resíduo da paridade foi limpo pelo próprio utilitário do pipeline, sem falhas. Um resíduo de ambiente chegou a ficar na raiz do projeto, criado por uma tentativa de apontar o diretório temporário do pytest para dentro do projeto, e precisou de acesso ampliado para ser removido; a tentativa **já estava documentada como abandonada** no `_clean_residue.py`, e a repetição está registrada na observação `O16`.

### Fontes desta atualização

- `src/app.py` (bloco de entrada atual)
- `requirements.txt` (conteúdo atual, com versões fixadas)
- `tests/test_servidor_producao.py` (sete afirmações)
- `README.md` (seções de execução, de abertura para a rede e de instância única)
- `_reversa_forward/004-servidor-waitress/actions.md` (20 de 20 ações concluídas, e as Notas de execução da segunda rodada)
- `_reversa_forward/004-servidor-waitress/onboarding.md` (seções 2, 8, 9 e 10)
- `_reversa_forward/004-servidor-waitress/regression-watch.md` (observações `O10` a `O16`, e `W006` a `W008`)
- `_reversa_forward/004-servidor-waitress/progress.jsonl` (linhas de `T011` a `T020`)

## Atualização 2026-10-04 (sincronização)

> **Quinta sincronização, na mesma data.** O conteúdo acima **não foi alterado**. Onde esta seção contradizer o que está escrito antes, **esta seção é a leitura correta**. Esta seção é o registro do `/reversa-sync` sobre a feature `004-servidor-waitress`, com as vinte ações fechadas.
>
> **Desvio declarado no título.** As três seções anteriores já usam a data de hoje, e o padrão do skill é `## Atualização YYYY-MM-DD`. Um quarto título idêntico tornaria ambíguo o apontador de qualquer leitura futura, então esta seção recebe o sufixo `(sincronização)`. O corpo segue o padrão do skill.

### Estado da sincronização

| Item | Valor |
|---|---|
| Feature ativa | `004-servidor-waitress` |
| Cenário detectado | **legado** (`_reversa_sdd/architecture.md` e `domain.md` presentes) |
| Ações | **20 de 20** concluídas, nenhuma `[ ]` aberta em `actions.md` |
| Tipo de sincronização | **total**, e não parcial: não há entrega pendente para complementar depois |
| Ganchos | `before-sync` e `after-sync` estão **vazios** em `.reversa/hooks.yml`, então nenhum comando foi executado |
| Impactos novos nesta seção | **nenhum**. O delta por artefato já está itemizado na seção `(rodada 3)`, e não é repetido aqui |

### Alerta: a fonte principal que o skill indica está congelada na primeira rodada

O `/reversa-sync` designa `_reversa_forward/<feature>/legacy-impact.md` como **fonte principal do delta**. Nesta feature, essa fonte **não pode ser usada sozinha**: ela é de `2026-10-03`, descreve a entrega antes da segunda rodada, e contradiz o sistema atual em pontos que mudam a leitura. As contradições, uma por uma:

| O que o `legacy-impact.md` afirma | O que o sistema faz hoje | Onde está a verdade |
|---|---|---|
| "o endereço padrão passa a atender todas as interfaces de rede", com severidade **HIGH** (linha 12) | o padrão é `127.0.0.1`, e atender a rede exige `ANALISADOR_HOST` explícita | `requirements.md#4` (`RN-03`), `roadmap.md` (`D-02` revista), `src/app.py` |
| `ANALISADOR_HOST` "com `0.0.0.0`" (linha 28) | o padrão declarado é `127.0.0.1` | `src/app.py`, bloco de entrada |
| "O endereço padrão passa de `127.0.0.1` para `0.0.0.0`. Isso é intencional" (linha 33) | é o inverso: passou de `0.0.0.0` para `127.0.0.1`, e é intencional | `requirements.md#9`, sessão de 2026-10-04 |
| `requirements.txt` "pendente, não aplicado" (linhas 15 e 82) | aplicado, e além disso com versão fixada nas seis linhas | `requirements.txt`, e `actions.md` (`T001`, `T002`, `T012`) |
| "três testes" no arquivo novo (linha 40) | sete afirmações | `tests/test_servidor_producao.py` |
| "o endereço de acesso deixou de ser apenas `127.0.0.1`" (linha 46) | o endereço de acesso **voltou** a ser apenas `127.0.0.1` | `README.md`, seção de configuração de execução |
| `T001`, `T002` e `T011` pendentes, com a seção 3 inteira dedicada a isso (linhas 48 a 54) | as três fecharam, e a `T011` foi medida com dois processos reais | `actions.md`, Notas de execução |
| "os mesmos 118 testes aprovados da linha de base" (linha 66) | **125 aprovados** e 15 erros de ambiente | `actions.md` (`T018`), `regression-watch.md` (`O15`) |
| nenhuma menção à guarda de instância única, ao diagnóstico por código de erro ou ao socket entregue pronto | os três existem | `actions.md` (`T015`, `T016`), `roadmap.md` (`D-10`, `D-11`) |

**Consequência prática para quem lê a extração:** para esta feature, a leitura correta é este adendo, seguido dos artefatos da feature em `_reversa_forward/004-servidor-waitress/` na ordem `requirements.md`, `roadmap.md`, `actions.md`, `regression-watch.md`. O `legacy-impact.md` vale apenas como registro do que a **primeira** rodada entregou.

**Por que o arquivo não foi corrigido aqui:** o `/reversa-sync` escreve apenas em `_reversa_sdd/addenda/`, e os artefatos da feature são somente leitura para ele. A correção do `legacy-impact.md` cabe a uma passagem por `/reversa-to-do` ou `/reversa-coding`, que têm esse arquivo como alvo.

### Linhas das tabelas anteriores que ficaram superadas

O adendo é cumulativo, e três linhas de tabelas mais antigas descrevem um estado que não vale mais. Elas **não foram reescritas**, por esta seção ser de registro. Quem lê a extração deve aplicar estas substituições:

| Linha superada | O que ela afirma | O que vale agora |
|---|---|---|
| `## Impacto por artefato da extração`, `architecture.md#3.3` | "O endereço de escuta padrão passou a atender todas as interfaces de rede" | O padrão passou a ser `127.0.0.1`. A linha da rodada 3 para o **mesmo artefato e a mesma seção** é a que vale |
| `## Impacto por artefato da extração`, `dependencies.md#2` | "**Pendente.** ... Leia o arquivo como ainda contendo o servidor que não sobe no Windows" | O arquivo lista `waitress` e fixa as seis versões. As linhas das rodadas 2 e 3 para o mesmo artefato são as que valem |
| `## Atualização 2026-10-04`, `requirements.md#7` | "O cenário precisa ser reescrito ou retirado, e isso é decisão do usuário" | A decisão foi tomada na sessão de esclarecimento de 2026-10-04: o cenário foi reescrito para o comportamento medido, e nasceram a `RN-05` e a `RF-08`, implementadas e verificadas |

As demais linhas continuam valendo como estão.

### Regras sob vigilância

`W001` a `W008`, em `_reversa_forward/004-servidor-waitress/regression-watch.md`. Os itens `W006`, `W007` e `W008` são desta rodada: a guarda de exclusividade no bloco de entrada, o padrão fechado do endereço de escuta e a versão fixada em toda linha do arquivo de dependências.

### Fontes desta atualização

- `.reversa/state.json` (`output_folder` e `forward_folder` resolvidos)
- `.reversa/active-requirements.json` (feature ativa e feature pausada)
- `.reversa/hooks.yml` (ganchos vazios)
- `_reversa_forward/004-servidor-waitress/legacy-impact.md` (fonte principal indicada pelo skill, usada como contraste)
- `_reversa_forward/004-servidor-waitress/requirements.md`, `roadmap.md`, `actions.md`, `regression-watch.md`, `progress.jsonl`
- `src/app.py`, `tests/test_servidor_producao.py`, `requirements.txt`, `README.md` (conferência do estado real)

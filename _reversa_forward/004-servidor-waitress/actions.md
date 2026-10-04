# Actions: servir a aplicação por um servidor de produção no Windows

> Identificador: `004-servidor-waitress`
> Data: `2026-10-03` (primeira rodada) e `2026-10-04` (segunda rodada)
> Roadmap: `_reversa_forward/004-servidor-waitress/roadmap.md`

## Resumo

| Métrica | Valor |
|---------|-------|
| Total de ações | **20** |
| Paralelizáveis (`[//]`) | **9** |
| Maior cadeia de dependência | 7 |

**Composição:** a primeira rodada, de `2026-10-03`, gerou `T001` a `T011`, e 10 dessas ações foram concluídas. A segunda rodada, de `2026-10-04`, acrescenta `T012` a `T020`, a partir da revisão do `requirements.md` e do `roadmap.md`. **Os IDs da primeira rodada não foram reciclados nem renumerados**, e as ações concluídas continuam marcadas como concluídas.

A maior cadeia de dependência continua sendo a da primeira rodada, com 7 elos. A cadeia mais longa da segunda rodada tem 6: `T012`, `T014`, `T015`, `T016`, `T017`, `T018`.

## Fase 1, Preparação

| ID | Descrição | Dependências | Paralelismo | Arquivo alvo | Confidência | Status |
|----|-----------|--------------|-------------|--------------|-------------|--------|
| T001 | Trocar o servidor no arquivo de dependências: entra o de produção, sai o que não importa no Windows | - | - | `requirements.txt` | 🟢 | `[X]` |
| T002 | Instalar as dependências atualizadas no interpretador que executa a aplicação e confirmar que o módulo do servidor importa nele | T001 | - | `requirements.txt` | 🟢 | `[X]` |

> **Bloqueio de política, resolvido em 2026-10-04.** Quando este plano foi escrito, `requirements.txt` **não estava liberado** em `.reversa/reversa-config.json`, e `T001` e `T002` ficaram paradas por isso. O usuário acrescentou o caminho à lista `allowedPaths` em 2026-10-04, e as duas ações foram executadas na sequência: o arquivo perdeu a dependência que não importa no Windows e ganhou a de produção, e a instalação a partir dele terminou com código de saída 0.

## Fase 2, Testes

| ID | Descrição | Dependências | Paralelismo | Arquivo alvo | Confidência | Status |
|----|-----------|--------------|-------------|--------------|-------------|--------|
| T003 | Escrever o teste que inspeciona o bloco de entrada e afirma que o servidor em uso é o de produção, confirmando que ele **falha** no estado atual | T002 | - | `tests/test_servidor_producao.py` | 🟢 | `[X]` |

## Fase 3, Núcleo

| ID | Descrição | Dependências | Paralelismo | Arquivo alvo | Confidência | Status |
|----|-----------|--------------|-------------|--------------|-------------|--------|
| T004 | Substituir o bloco de entrada: sai o servidor de desenvolvimento com depuração, entra o servidor de produção com endereço, porta e concorrência lidos das variáveis de ambiente e padrões declarados | T003 | - | `src/app.py` | 🟢 | `[X]` |
| T005 | Importar o servidor dentro do bloco de entrada, com tratamento de importação ausente que nomeia o pacote e o comando de instalação | T004 | - | `src/app.py` | 🟡 | `[X]` |
| T006 | Emitir na inicialização uma linha com o servidor, o endereço e a porta em uso | T005 | - | `src/app.py` | 🟡 | `[X]` |

## Fase 4, Integração

| ID | Descrição | Dependências | Paralelismo | Arquivo alvo | Confidência | Status |
|----|-----------|--------------|-------------|--------------|-------------|--------|
| T007 | Rodar a suíte completa e conferir o resultado contra a linha de base, incluindo o teste novo aprovado | T006 | `[//]` | `tests/` | 🟢 | `[X]` |
| T008 | Rodar a paridade diferencial contra o oráculo congelado e conferir 100 por cento nas 6 fixtures | T006 | `[//]` | `_reversa_sdd/parity/harness.py` | 🟢 | `[X]` |

## Fase 5, Polimento

| ID | Descrição | Dependências | Paralelismo | Arquivo alvo | Confidência | Status |
|----|-----------|--------------|-------------|--------------|-------------|--------|
| T009 | Documentar no `README.md` o comando de inicialização, o endereço de acesso e as três variáveis de ambiente com seus padrões | T004 | `[//]` | `README.md` | 🟡 | `[X]` |
| T010 | Verificar o caminho negativo de dependência ausente em ambiente virtual descartável, conferindo que a mensagem nomeia o pacote e o comando e que nenhuma porta fica aberta | T006 | `[//]` | `onboarding.md` | 🟡 | `[X]` |
| T011 | Verificar a recusa da segunda instância, conferindo mensagem legível, código de saída diferente de zero e a instância que já estava no ar seguindo atendendo | T010, T017 | - | `onboarding.md` | 🟢 | `[X]` |

> `T011` foi planejada como não paralelizável com `T010` por um motivo de recurso: as duas usam a mesma porta. **O motivo caiu com a medição de 2026-10-04**, registrada nas Notas de execução: no Windows, duas instâncias não disputam a porta, elas coexistem.
>
> **Reescopo de 2026-10-04:** a descrição e a confidência de `T011` foram atualizadas, e a dependência passou a incluir `T017`. O ID foi preservado. Antes, a ação verificava um comportamento que a plataforma não produz; agora ela verifica a recusa, que a `RF-08` passou a exigir, e por isso deixa de estar bloqueada por premissa.

## Segunda rodada, 2026-10-04

Aberta depois da execução real da entrega e da sessão de esclarecimento que revisou o `requirements.md`. São nove ações, `T012` a `T020`, derivadas das decisões `D-02` (revista), `D-10`, `D-11`, `D-12` e `D-13` do roadmap.

### Fase 1, Preparação

| ID | Descrição | Dependências | Paralelismo | Arquivo alvo | Confidência | Status |
|----|-----------|--------------|-------------|--------------|-------------|--------|
| T012 | Fixar a versão de cada dependência declarada, com `==`, nas versões validadas no ambiente que executa a aplicação | - | - | `requirements.txt` | 🟢 | `[X]` |
| T013 | Reinstalar a partir do arquivo com versões fixas e confirmar que o conjunto instalado corresponde ao declarado | T012 | `[//]` | `requirements.txt` | 🟢 | `[X]` |

### Fase 2, Testes

| ID | Descrição | Dependências | Paralelismo | Arquivo alvo | Confidência | Status |
|----|-----------|--------------|-------------|--------------|-------------|--------|
| T014 | Estender o teste por inspeção para afirmar a presença da guarda de exclusividade no bloco de entrada, confirmando que ele **falha** no estado atual | T012 | `[//]` | `tests/test_servidor_producao.py` | 🟢 | `[X]` |

### Fase 3, Núcleo

| ID | Descrição | Dependências | Paralelismo | Arquivo alvo | Confidência | Status |
|----|-----------|--------------|-------------|--------------|-------------|--------|
| T015 | Criar o socket de escuta com marca de uso exclusivo, ligá-lo com `bind` e `listen`, e entregá-lo pronto ao servidor | T014 | - | `src/app.py` | 🟢 | `[X]` |
| T016 | Recusar a subida com mensagem legível e código de saída diferente de zero quando o endereço e a porta já estiverem em uso | T015 | - | `src/app.py` | 🟢 | `[X]` |
| T017 | Mudar o padrão do endereço de escuta para a máquina local | T016 | - | `src/app.py` | 🟢 | `[X]` |

### Fase 4, Integração

| ID | Descrição | Dependências | Paralelismo | Arquivo alvo | Confidência | Status |
|----|-----------|--------------|-------------|--------------|-------------|--------|
| T018 | Rodar a suíte completa e conferir o resultado contra a linha de base | T017 | `[//]` | `tests/` | 🟢 | `[X]` |
| T019 | Rodar a paridade diferencial contra o oráculo congelado e conferir 100 por cento nas 6 fixtures | T017 | `[//]` | `_reversa_sdd/parity/harness.py` | 🟢 | `[X]` |

### Fase 5, Polimento

| ID | Descrição | Dependências | Paralelismo | Arquivo alvo | Confidência | Status |
|----|-----------|--------------|-------------|--------------|-------------|--------|
| T020 | Atualizar o `README.md` com o padrão fechado, o procedimento de abrir a rede e o comportamento de recusa da segunda instância | T017 | `[//]` | `README.md` | 🟡 | `[X]` |

**Por que `T018` e `T019` reaparecem**, quando `T007` e `T008` já foram concluídas: elas remedem o mesmo gate **depois** de o bloco de entrada voltar a mudar. Sem isso, a última medição de suíte e paridade seria anterior à guarda de exclusividade e à mudança do padrão.


## Notas de execução

Registrado por `/reversa-coding` em 2026-10-04.

- **`T001` e `T002` executadas.** O caminho `requirements.txt` foi liberado pelo usuário em 2026-10-04, e as duas ações fecharam na sequência. O arquivo trocou `gunicorn ` (com o espaço final que ele trazia) por `waitress`, e ficou em ordem alfabética. `pip install -r requirements.txt` terminou com código de saída 0, com `waitress 3.0.2` no diretório de pacotes do usuário, visível tanto para `py -3.14` quanto para `python`.
- **O `gunicorn` continua instalado na máquina**, e isso é inofensivo: ele deixou de ser dependência do projeto, que é o que importava. Nenhuma ação de desinstalação foi tomada, e nenhuma é necessária.
- **A `T011` foi executada, e o resultado contradiz a premissa do cenário.** Experimentos controlados numa porta livre mostraram que, no Windows, **duas instâncias do servidor escutam na mesma porta ao mesmo tempo**: as duas imprimem a linha de inicialização e o `netstat` lista os dois processos em `LISTENING`. O servidor usa `SO_REUSEADDR`, e a semântica do Windows é permissiva nesse ponto, diferente de outras plataformas. Portanto **não há falha a reportar e não existe código de saída diferente de zero**: o cenário de porta ocupada do `requirements.md` descreve um comportamento que não acontece nesta plataforma. A ação permanece aberta, porque o critério de aceite dela não pode ser satisfeito como está escrito.
- **O risco real, medido, não é a falha ausente: é a coexistência.** Com duas instâncias na mesma porta, a distribuição das requisições entre elas não é determinística, e cada processo tem o **seu próprio** estado global da árvore genealógica, em `core/gedcom_state.py`. Duas requisições do mesmo navegador podem cair em instâncias diferentes, e a segunda responde que não há árvore carregada. É a mesma classe do defeito de exposição de estado já registrado no projeto.
- **O caminho feliz foi verificado ao vivo**, com o aplicativo em execução real: `HTTP 200` na rota raiz, cabeçalho `Server: waitress`, formulário de upload presente, e três requisições seguidas estáveis com o mesmo tamanho de resposta.
- **O endereço em uso na execução real foi `127.0.0.1`**, e não o padrão `0.0.0.0` declarado no código. Isso indica que a variável `ANALISADOR_HOST` estava definida na sessão da execução, já que não existe variável persistente no ambiente do usuário, e o cabeçalho `Server: waitress` confirma que o código em execução é o desta feature. O efeito é o modo restrito à máquina local, que é o mais seguro.
- **Nenhuma das verificações deixou resíduo**: os processos dos experimentos foram encerrados e as portas usadas foram liberadas, conferido por `netstat`.

### Segunda rodada, 2026-10-04

Registrado por `/reversa-coding` na execução de `T011` a `T020`. As dez ações fecharam.

- **`T012` e `T013` executadas.** O `requirements.txt` passou a fixar as seis dependências diretas com `==`, nas versões validadas (`Flask 3.1.3`, `ged4py 0.5.2`, `networkx 3.6.1`, `pandas 3.0.3`, `thefuzz 0.22.1`, `waitress 3.0.2`), mantida a ordem alfabética. A reinstalação a partir do arquivo terminou com código de saída 0 e **nada foi instalado nem removido**, porque o conjunto já correspondia. A conferência entre declarado e instalado deu `divergentes: []` nas seis. As transitivas (`rapidfuzz 3.14.5`, `Werkzeug 3.1.8`) continuam flutuando, como a `D-12` já declarava.
- **O `pip` avisou que não conseguiu limpar diretórios temporários**, e o aviso é a mesma restrição de ambiente já registrada nesta feature, sem efeito sobre o resultado: com todas as versões satisfeitas, nenhum desempacotamento acontece.
- **`T014` executada, e o teste novo falhou antes da mudança**, que é o critério da `RF-05`: com o código anterior, `4 failed, 3 passed`. Depois da mudança, `7 passed`.
- **Defeito próprio, corrigido na `T014`.** Uma das afirmações novas procurava `"127.0.0.1"` entre aspas duplas, e o `ast.unparse` normaliza a aspa dupla para simples quando não há escapamento. A afirmação falhou por causa da aspa, e não do código. Passou a procurar o endereço sem as aspas, o que também é mais robusto, e ganhou a afirmação negativa de que o bloco não menciona mais `0.0.0.0`.
- **Achado que mudou a forma da `T015`.** O servidor **recusa** receber `sockets` junto de `host` ou `port`: levanta `ValueError` (`waitress/adjustments.py`, linhas 299 e 300). A chamada perdeu o `host` e o `port`, e o endereço e a porta passam a existir apenas no socket ligado. Por causa disso, a linha de inicialização que a `T006` já imprimia passa a ser a única forma de saber onde a aplicação escuta, e o teste ganhou afirmação sobre essa combinação, que é a que falharia em tempo de execução.
- **`T015` implementada como a `D-10` decidiu**: socket criado pela aplicação, marcado com `SO_EXCLUSIVEADDRUSE`, ligado com `bind` e `listen(socket.SOMAXCONN)`, e entregue pronto ao servidor. O socket entra em modo não bloqueante para ficar com a mesma postura do socket que o servidor criaria.
- **`T016` executada, e a mensagem segue o erro medido em vez de supor.** A sonda de 2026-10-04 mostrou que `errno.EADDRINUSE` vale `10048` neste interpretador e chega para porta ocupada, e que um endereço que não pertence à máquina chega com `10049`, que não é `EADDRINUSE`. A recusa passou a separar os dois casos, porque eles pedem ações diferentes, e os dois foram verificados: porta ocupada sai com a orientação de encerrar a instância ou trocar de porta, e endereço inválido sai com a orientação de conferir `ANALISADOR_HOST`. Em ambos, mensagem legível e código de saída 1.
- **`T017` executada**: o padrão passou a `127.0.0.1`. O teste afirma as duas metades, a presença do endereço local e a ausência do endereço que atende todas as interfaces. A `RF-02` foi verificada ao vivo, nos dois lados do critério e com controle positivo: sem a variável definida, o `netstat` mostrou `127.0.0.1:5088` em `LISTENING`, a requisição em `http://127.0.0.1:5088/` respondeu `HTTP 200`, e a requisição em `http://192.168.1.40:5088/`, que é o endereço de rede desta máquina, **não** respondeu; com `ANALISADOR_HOST=0.0.0.0`, o `netstat` mostrou `0.0.0.0:5089` em `LISTENING` e as duas requisições responderam `HTTP 200`. O controle positivo existe para que o resultado negativo não seja confundido com uma sondagem quebrada. As portas dos dois experimentos foram liberadas, conferido por `netstat`.
- **`T011` executada por medição real, e o resultado agora confirma o requisito.** Experimento controlado em porta livre, com dois processos: a primeira instância atendeu com `HTTP 200` e `Server: waitress`, a segunda terminou com código 1 e a mensagem de porta em uso, sem pilha de exceção, e a primeira continuou atendendo depois da tentativa. O experimento foi repetido com a instância que já estava no ar iniciada pelo **caminho da versão anterior**, em que o servidor cria o próprio socket e pede `SO_REUSEADDR` (confirmado com `getsockopt`, valor 1), e a recusa também aconteceu. É isso que torna honesta a instrução de encerrar a instância no ar antes de subir a versão nova.
- **A leitura da fonte instalada corrigiu uma premissa da `D-10`.** O servidor **faz** `listen` com socket pronto: `bind_socket=False` pula o `bind`, mas `accept_connections` chama `socket.listen(self.adj.backlog)` (`waitress/server.py`). A aplicação continua fazendo `bind` e `listen` por conta própria, e o motivo correto é garantir que o socket já esteja em escuta quando o servidor assumir. A precisão foi registrada no `roadmap.md`, e a afirmação errada que estava no `onboarding.md` foi corrigida.
- **`T018` executada**: `125 aprovados, 15 erros`. Os 15 erros são exatamente os da linha de base, todos em `test_upload_seguranca.py`, por permissão de diretório temporário no sandbox. O crescimento de 4 sobre os 121 anteriores é o das afirmações novas da `T014`. Apontar `--basetemp` para dentro do projeto foi tentado e **não** resolve: o diretório é criado, e o sandbox nega enumerá-lo. A tentativa está registrada no `onboarding.md` para não ser repetida.
- **`T019` executada**: `PARIDADE 100% (zero divergencia)` nas 6 fixtures.
- **`T020` executada**, com três correções declaradas além do que a ação pedia, todas causadas por esta rodada: a seção de deploy afirmava que o `requirements.txt` inclui o Gunicorn, o que a execução da `T001` tornou falso; a contagem de linhas do `app.py` estava desatualizada; e a árvore de testes não listava `tests/test_servidor_producao.py`, além de a contagem de testes estar defasada.
- **Uma mudança fora das dez ações, declarada.** A mensagem de dependência ausente da `T005` mandava instalar `waitress` avulso, o que passou a contradizer a versão fixada da `T012`. A mensagem agora nomeia o pacote, o interpretador exato e o arquivo de dependências. O comportamento foi reverificado depois da mudança: código de saída 1, mensagem legível, sem pilha de exceção e sem porta aberta.
- **O `onboarding.md` recebeu correções além da `T011`.** A seção da dependência ausente mandava instalar o arquivo de dependências em um ambiente virtual e rodar em seguida, o que **não** testa ausência alguma, porque o arquivo inclui o servidor de produção; passou a exigir a desinstalação no ambiente descartável, e ficou registrado que o passo não pôde ser executado neste ambiente. A verificação equivalente contra o bloco de entrada atual foi feita escondendo o módulo do servidor do interpretador, com o mesmo resultado esperado.

## Histórico de alterações

| Data | Alteração | Autor |
|------|-----------|-------|
| 2026-10-03 | Versão inicial gerada por `/reversa-to-do` | reversa |
| 2026-10-04 | Notas de execução do `/reversa-coding`, com o resultado medido da `T011` e a correção da nota de paralelismo | reversa |
| 2026-10-04 | `T001` e `T002` fechadas após a liberação do caminho `requirements.txt` pelo usuário | reversa |
| 2026-10-04 | Segunda rodada gerada por `/reversa-to-do`: `T012` a `T020` acrescentadas, `T011` reescopada, e o resumo atualizado para 20 ações. Os IDs da primeira rodada foram preservados | reversa |
| 2026-10-04 | `T011` a `T020` executadas por `/reversa-coding`, com as vinte ações fechadas. Notas de execução da segunda rodada acrescentadas, com as medições da guarda de exclusividade e as correções declaradas | reversa |

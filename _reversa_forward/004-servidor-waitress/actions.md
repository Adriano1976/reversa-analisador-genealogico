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
| T011 | Verificar a recusa da segunda instância, conferindo mensagem legível, código de saída diferente de zero e a instância que já estava no ar seguindo atendendo | T010, T017 | - | `onboarding.md` | 🟢 | `[ ]` |

> `T011` foi planejada como não paralelizável com `T010` por um motivo de recurso: as duas usam a mesma porta. **O motivo caiu com a medição de 2026-10-04**, registrada nas Notas de execução: no Windows, duas instâncias não disputam a porta, elas coexistem.
>
> **Reescopo de 2026-10-04:** a descrição e a confidência de `T011` foram atualizadas, e a dependência passou a incluir `T017`. O ID foi preservado. Antes, a ação verificava um comportamento que a plataforma não produz; agora ela verifica a recusa, que a `RF-08` passou a exigir, e por isso deixa de estar bloqueada por premissa.

## Segunda rodada, 2026-10-04

Aberta depois da execução real da entrega e da sessão de esclarecimento que revisou o `requirements.md`. São nove ações, `T012` a `T020`, derivadas das decisões `D-02` (revista), `D-10`, `D-11`, `D-12` e `D-13` do roadmap.

### Fase 1, Preparação

| ID | Descrição | Dependências | Paralelismo | Arquivo alvo | Confidência | Status |
|----|-----------|--------------|-------------|--------------|-------------|--------|
| T012 | Fixar a versão de cada dependência declarada, com `==`, nas versões validadas no ambiente que executa a aplicação | - | - | `requirements.txt` | 🟢 | `[ ]` |
| T013 | Reinstalar a partir do arquivo com versões fixas e confirmar que o conjunto instalado corresponde ao declarado | T012 | `[//]` | `requirements.txt` | 🟢 | `[ ]` |

### Fase 2, Testes

| ID | Descrição | Dependências | Paralelismo | Arquivo alvo | Confidência | Status |
|----|-----------|--------------|-------------|--------------|-------------|--------|
| T014 | Estender o teste por inspeção para afirmar a presença da guarda de exclusividade no bloco de entrada, confirmando que ele **falha** no estado atual | T012 | `[//]` | `tests/test_servidor_producao.py` | 🟢 | `[ ]` |

### Fase 3, Núcleo

| ID | Descrição | Dependências | Paralelismo | Arquivo alvo | Confidência | Status |
|----|-----------|--------------|-------------|--------------|-------------|--------|
| T015 | Criar o socket de escuta com marca de uso exclusivo, ligá-lo com `bind` e `listen`, e entregá-lo pronto ao servidor | T014 | - | `src/app.py` | 🟢 | `[ ]` |
| T016 | Recusar a subida com mensagem legível e código de saída diferente de zero quando o endereço e a porta já estiverem em uso | T015 | - | `src/app.py` | 🟢 | `[ ]` |
| T017 | Mudar o padrão do endereço de escuta para a máquina local | T016 | - | `src/app.py` | 🟢 | `[ ]` |

### Fase 4, Integração

| ID | Descrição | Dependências | Paralelismo | Arquivo alvo | Confidência | Status |
|----|-----------|--------------|-------------|--------------|-------------|--------|
| T018 | Rodar a suíte completa e conferir o resultado contra a linha de base | T017 | `[//]` | `tests/` | 🟢 | `[ ]` |
| T019 | Rodar a paridade diferencial contra o oráculo congelado e conferir 100 por cento nas 6 fixtures | T017 | `[//]` | `_reversa_sdd/parity/harness.py` | 🟢 | `[ ]` |

### Fase 5, Polimento

| ID | Descrição | Dependências | Paralelismo | Arquivo alvo | Confidência | Status |
|----|-----------|--------------|-------------|--------------|-------------|--------|
| T020 | Atualizar o `README.md` com o padrão fechado, o procedimento de abrir a rede e o comportamento de recusa da segunda instância | T017 | `[//]` | `README.md` | 🟡 | `[ ]` |

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

## Histórico de alterações

| Data | Alteração | Autor |
|------|-----------|-------|
| 2026-10-03 | Versão inicial gerada por `/reversa-to-do` | reversa |
| 2026-10-04 | Notas de execução do `/reversa-coding`, com o resultado medido da `T011` e a correção da nota de paralelismo | reversa |
| 2026-10-04 | `T001` e `T002` fechadas após a liberação do caminho `requirements.txt` pelo usuário | reversa |
| 2026-10-04 | Segunda rodada gerada por `/reversa-to-do`: `T012` a `T020` acrescentadas, `T011` reescopada, e o resumo atualizado para 20 ações. Os IDs da primeira rodada foram preservados | reversa |

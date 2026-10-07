# Actions: dono no port de armazenamento e linha de base da suíte

> Identificador: `007-dono-no-port-e-baseline`
> Data: `2026-10-07`
> Roadmap: `_reversa_forward/007-dono-no-port-e-baseline/roadmap.md`

## Resumo

| Métrica | Valor |
|---------|-------|
| Total de ações | **16** |
| Paralelizáveis (`[//]`) | **6** (`T002`, `T003`, `T006`, `T007`, `T011`, `T012`) |
| Maior cadeia de dependência | **8 ações** (7 elos): `T001` → `T003` → `T004` → `T005` → `T006` → `T010` → `T014` → `T015` |
| Linha de base a preservar | `231 passed, 15 errors` e paridade `100 %` em 6 fixtures, exit 0 (entrega da feature 006) |
| Linha de base a **produzir** | `246 passed, 0 errors` — medido antes do plano com sonda descartável; é o valor **esperado** do `T004`, e ele cresce com os testes do `T010` |

**Composição:** 2 ações de preparação, 2 de teste, 5 de núcleo, 3 de integração e 4 de polimento.

> ⚠️ **A ordem é o plano, e ela tem uma razão só.** A `D-11` divide a execução em dois
> blocos: o **Bloco 0** (`T001` a `T004`) devolve o instrumento, e o **Bloco 1** (`T005` a
> `T016`) faz a costura. A costura **não começa** antes de o Bloco 0 estar medido, porque
> hoje a única medição disponível para ela é uma suíte cega em 15 testes da exata
> superfície que a Onda 2 reescreveu — e foi essa cegueira que obrigou a feature 006 a
> construir uma sonda à mão para medir o `app.py`. Trocar essa ordem é medir a costura
> com o instrumento quebrado.

## Fase 1, Preparação

| ID | Descrição | Dependências | Paralelismo | Arquivo alvo | Confidência | Status |
|----|-----------|--------------|-------------|--------------|-------------|--------|
| T001 | Reescrever `tests/conftest.py` para que ele seja a **autoridade do diretório temporário da suíte**: tornar `pasta_temporaria` a implementação única (raiz `tests/.tmp/`, criada com `os.makedirs` no **modo padrão**), fazer o novo fixture `tmp_path` **delegar** a ela devolvendo `pathlib.Path`, e **sair do diretório corrente antes do `rmtree`** no `finally`. O `collect_ignore` **não** é removido por esta ação | - | - | `tests/conftest.py` | 🟢 | `[X]` |
| T002 | Atualizar o docstring de `tests/conftest.py` com as **duas causas medidas**: (a) `TempPathFactory.getbasetemp()` cria `pytest-of-<usuário>` com `0o700` e o `os.scandir` de `_pytest/pathlib.py:175` falha ao listá-lo — o `mktemp` nunca chega a rodar; (b) o resíduo de 15 diretórios por execução, causado pelo `monkeypatch.chdir(tmp_path)` de `app_cliente`, que deixa o CWD dentro do diretório na hora da remoção. Declarar também que o `collect_ignore` só sai quando o diretório preso for removido com shell elevado | T001 | `[//]` | `tests/conftest.py` | 🟢 | `[X]` |

> **Por que `T002` existe como ação, e não como parte do `T001`.** O RNF de
> **Observabilidade** exige que a causa fique registrada onde o próximo leitor a encontra,
> e o RNF de **Operação** exige que os 13 diretórios presos sigam documentados com o
> comando de remoção. São requisitos com critério de aceite próprio, e não comentário
> acessório: o sintoma que esta feature corrige (`erro de ambiente`) já foi atribuído à
> máquina **duas vezes** — na feature 005 e na 006 — porque a causa não estava escrita ao
> lado do código que a contorna.

> **Sobre `T001` e a única inferência do plano.** O plano mediu a substituição do
> `tmp_path` com um **plugin** (`-p`), que tem precedência **menor** que a de um
> `conftest.py`. A garantia de que o `conftest` vence — e não apenas empata — vem da regra
> de resolução de fixtures do pytest, não de uma medição direta. `T003` e `T004` fecham
> isso empiricamente, e fecham **antes** de qualquer linha de produto mudar: se a
> precedência não valesse, o `T004` mediria `15 errors` e o Bloco 1 não começaria.

## Fase 2, Testes

| ID | Descrição | Dependências | Paralelismo | Arquivo alvo | Confidência | Status |
|----|-----------|--------------|-------------|--------------|-------------|--------|
| T003 | Escrever o teste que **prende a correção do ambiente**: provar que o `tmp_path` da suíte é o **do projeto** (sob `tests/.tmp/`) e que ele é **listável, gravável e removível**. Existe porque a correção é invisível — um upgrade do pytest, ou alguém removendo o fixture por parecer redundante, devolve o defeito em silêncio, e o sintoma volta a parecer problema da máquina | T001 | `[//]` | `tests/test_ambiente_temporario_da_suite.py` | 🟢 | `[X]` |
| T004 | Medir e registrar a **linha de base do Bloco 0**: suíte completa e paridade diferencial, as duas com `.venv/Scripts/python.exe`, com o **comando ao lado de cada número**, confirmando `0 errors`, nenhum teste a menos e **zero resíduo** em `tests/.tmp/`. O resultado passa a ser a linha de base **vigente**, e o par `231 passed, 15 errors` passa a ser leitura histórica (`RF-06`, `RF-08`, `RF-10`, `D-12`) | T001, T003 | - | `_reversa_forward/007-dono-no-port-e-baseline/evidence/` | 🟢 | `[X]` |

> **`T004` é o portão do Bloco 0.** Ele é a única ação que pode dizer "o instrumento
> voltou" — e o critério é numérico: `0 errors`, contagem de aprovados **maior** que a
> anterior, nenhum teste removido. Um Bloco 0 que fecha sem este número registrado não
> fecha, e o Bloco 1 não pode começar.

## Fase 3, Núcleo

| ID | Descrição | Dependências | Paralelismo | Arquivo alvo | Confidência | Status |
|----|-----------|--------------|-------------|--------------|-------------|--------|
| T005 | Acrescentar `dono` às **três** assinaturas de `src/ports/__init__.py`: `ArmazenamentoDeArquivos.guardar(conteudo, nome_original, tipo, dono)` e `.resolver(referencia, dono)`, com o dono como **último parâmetro posicional e sem valor padrão**; e `CarregadorDeArvores.carregar(referencia, dono)`. O carregador **continua com um método** — a condição declarada da `D-02` da feature 006 era a contagem de métodos, e ela segue satisfeita. As docstrings registram que o dono **não** é segurança e que nenhum isolamento é implementado (`RF-01`, `D-05`, `D-06`) | T004 | - | `src/ports/__init__.py` | 🟢 | `[X]` |
| T006 | Ajustar `src/ports/adaptadores.py`: `ArmazenamentoEmDisco.guardar` e `.resolver` **aceitam** o dono e **não o usam em nenhuma decisão** — chave, nome armazenado, caminho, reuso por conteúdo e ordem de validação ficam idênticos —, com comentário no corpo dizendo por quê; e `CarregadorDeArvoresGedcom.carregar` **repassa** o dono recebido à chamada de `resolver` (`RF-02`, `D-06`, `D-07`) | T005 | `[//]` | `src/ports/adaptadores.py` | 🟢 | `[X]` |
| T007 | Fazer `upload_gedcom` **repassar** à chamada de `armazenamento.guardar` o `dono` que ele **já recebe** por parâmetro, sem nenhuma outra alteração no caso de uso (`RF-03`) | T005 | `[//]` | `src/application/upload_gedcom.py` | 🟢 | `[X]` |
| T008 | Fazer as **duas chamadas de produção** de `src/app.py` citarem `DONO_DO_PROCESSO`: a de `guardar` do CSV (`:193`) e a de `carregar` dentro de `_arvore_do_formulario()` (`:144`). Nenhum valor literal no próprio local, nenhuma chamada nova, nenhum passo de domínio de volta em `index()` (`RF-03`) | T006, T007 | - | `src/app.py` | 🟢 | `[X]` |
| T009 | Atualizar o comentário de `DONO_DO_PROCESSO` em `src/app.py`: passar a **nomear a dívida #3** (corrida entre requisições concorrentes) ao lado da #4, e remover o "nesta onda", que prendia a costura à feature 006 — ela é para a **Onda 3** do cutover, não para uma onda desta feature (`RF-04`, `D-08`) | T008 | - | `src/app.py` | 🟢 | `[X]` |

> **`T008` e `T009` são sequenciais de fato, e por isso nenhuma leva `[//]`.** As duas
> editam `src/app.py`, o mesmo arquivo que as cinco ações do `T016` a `T019` da feature 006
> editaram — e foi ali que o projeto já pagou o preço de embaralhar a ordem: duas metades
> de uma ação aplicadas fora de sequência, 49 falhas sem ponto de atribuição.

> **Por que `T009` é ação e não comentário acessório.** A `RF-04` tem critério de aceite
> que exige **duas** coisas do lugar onde a constante vive: ser o **único**, e **declarar**
> que não há isolamento e que a dívida #3 não é tratada. A primeira já é verdadeira; a
> segunda não. Sem esta ação o requisito fica parcialmente não atendido — e o texto
> continuaria dizendo que a costura pertence a uma onda que já foi entregue.

## Fase 4, Integração

| ID | Descrição | Dependências | Paralelismo | Arquivo alvo | Confidência | Status |
|----|-----------|--------------|-------------|--------------|-------------|--------|
| T010 | Escrever, em **classe nova** de `tests/test_porta_de_armazenamento.py`, **ao lado do `T028` da feature 006**, as provas do contrato do port de armazenamento: (a) a chamada montada **sem o dono** é recusada pelo próprio contrato, por `bind` sem o último parâmetro declarado, e o dono **não** tem valor padrão; (b) o adaptador aceita o dono e **não o usa** — o mesmo conteúdo com dois donos diferentes produz a **mesma** referência e **um** arquivo só; (c) existe **uma** forma de chamada, sem sobrecarga que aceite a chamada antiga (`RF-01`, `RF-02`, `RF-05`, `RF-12`) | T005, T006 | - | `tests/test_porta_de_armazenamento.py` | 🟡 | `[X]` |
| T011 | Rodar a **varredura de forma** do que o comportamento não distingue: (a) as duas chamadas de `guardar` e a chamada de `resolver` do código de produção passam o dono, e **nenhuma** passa literal no próprio local; (b) existe **uma só** atribuição de constante de dono no código, e o lugar onde ela vive declara que não há isolamento e que a dívida #3 não é tratada. Registrar a saída como evidência (`RF-03`, `RF-04`) | T007, T008, T009 | `[//]` | `_reversa_forward/007-dono-no-port-e-baseline/evidence/` | 🟢 | `[X]` |
| T012 | Provar que **nenhuma mensagem de tela mudou** (`RN-03`), reexecutando a sonda de **19 casos** que a feature 006 entregou em `evidence/probe_mensagens.py` e comparando a saída nova com o `mensagens_depois.json` registrado na entrega da 006 — que precisa ser **copiado antes** da execução, porque a sonda **sobrescreve** o arquivo de saída. A comparação é de **status HTTP, classe do alerta e texto** | T008 | `[//]` | `_reversa_forward/007-dono-no-port-e-baseline/evidence/` | 🟢 | `[X]` |

> **Por que `T011` existe, e por que ele é uma varredura e não um teste.** A `RF-03` exige
> que nenhum chamador "invente um valor no próprio local". Passar `DONO_DO_PROCESSO` ou o
> literal `"unico"` produz **exatamente o mesmo comportamento**: nenhum teste de execução
> separa os dois casos, e por isso a prova tem de ser de forma. O mesmo vale para a alínea
> (b) da `RF-04`. É o padrão que a feature 006 fixou no `T020` — a varredura de forma mede
> o que a suíte não alcança.

> **Sobre a confidência de `T010` (🟡).** A `D-09` é 🟢, mas a ação cobre também a
> `RF-12`, e essa tem confidência 🟡 no `requirements.md` (a decisão de não aceitar a
> chamada antiga é inferida do Princípio II, não medida). A ação herda a **menor** das
> confidências que ela verifica.

> **`T011` e `T012` são paralelas e mexem na mesma pasta.** O critério do Reversa exige
> **arquivos** alvo diferentes, e o que está declarado como alvo é a pasta `evidence/` — mas
> cada uma escreve arquivos distintos e nenhuma lê o que a outra escreve. É o único ponto
> deste documento em que a coluna "Arquivo alvo" precisa ser lida com essa ressalva.

## Fase 5, Polimento

| ID | Descrição | Dependências | Paralelismo | Arquivo alvo | Confidência | Status |
|----|-----------|--------------|-------------|--------------|-------------|--------|
| T013 | Corrigir o cabeçalho de `tests/test_porta_de_armazenamento.py` — a seção "Por que este arquivo não usa `tmp_path`" —, que a correção do Bloco 0 torna **falsa**. É **comentário, não asserção**: as asserções existentes ficam intocadas e o `diff` delas permanece vazio (`D-10`) | T010 | - | `tests/test_porta_de_armazenamento.py` | 🟢 | `[X]` |
| T014 | Medir e registrar o **Bloco 1**: suíte e paridade de novo com o interpretador oficial, conferindo que **nenhum aprovado do Bloco 0 virou falha**, e que o `diff` de `tests/test_upload_seguranca.py` contra o estado anterior está **vazio** (`RF-06`, `RF-10`, `D-12`) | T010, T012 | - | `_reversa_forward/007-dono-no-port-e-baseline/evidence/` | 🟢 | `[X]` |
| T015 | Executar a verificação manual de ponta a ponta do `onboarding.md` — servidor por `waitress`, os três fluxos, e a checagem de **nenhum resíduo** em `src/uploads/`, `uploads/` e `tests/.tmp/` — usando só dado **sintético** (Princípio I), e limpar o que sobrar conferindo `git status` | T014 | - | `_reversa_forward/007-dono-no-port-e-baseline/evidence/` | 🟢 | `[X]` |
| T016 | Conferir o **escopo** por `diff`: `src/core/`, `src/parsers/`, `src/reporting/` e `src/utils/` sem nenhuma alteração (`RF-11`); `pytest.ini` e `.gitignore` intocados; e os **13 diretórios presos** do workspace ainda presentes e apenas **documentados**, com o comando de remoção que exige shell elevado (RNF de Operação) | T014 | - | `_reversa_forward/007-dono-no-port-e-baseline/evidence/` | 🟢 | `[X]` |

> **`T013` é polimento, mas não é cosmético.** O parágrafo que ele corrige afirma que
> `tmp_path` não funciona nesta máquina e que é por isso que o arquivo usa
> `pasta_temporaria`. Depois do Bloco 0 isso deixa de ser verdade, e um comentário que
> mente sobre o motivo de uma escolha é pior que comentário nenhum: o próximo leitor
> repetiria a regra errada. É o mesmo defeito que o adendo da 006 registrou em quatro
> artefatos da extração que afirmavam uma casca removida como parte do sistema atual.

## Notas sobre a decomposição

### A `RF-09` não tem ação, e isso é deliberado

A `RF-09` manda **triar** cada falha dos 15 testes quando eles finalmente executarem. A
medição feita antes do plano — com uma sonda descartável, sem tocar em arquivo do projeto —
mostrou que **os 15 passam**: `246 passed, 0 errors`. O conjunto de triagem é **vazio**, e
por isso não existe ação para ele: uma ação "triar as falhas" não teria objeto, e o
`critério de pronto` do roadmap exige o oposto — que nenhuma falha fique sem veredito, o que
é satisfeito por não haver falha.

O que **é** uma ação é a condição que dá validade a essa afirmação: o `T004` tem de
reproduzir `0 errors`. Se ele não reproduzir, a `RF-09` **volta a valer integralmente**, e
o procedimento é o do `onboarding.md` §12: veredito explícito e datado por falha, defeito
de produto vira requisito próprio com arquivo e linha, defeito de teste é corrigido aqui.

### O que este documento **não** tem, e por quê

- Nenhuma ação de "configurar IDE", "rodar lint" ou "abrir PR" — não é responsabilidade do
  Reversa.
- Nenhuma ação para os **13 diretórios presos**: a decisão registrada na sessão de
  esclarecimento é que eles ficam **documentados**, não removidos. A ação `T016` confere que
  continuam intocados, e nada mais.
- Nenhuma ação para o `RepositorioDeArvores`: ele continua **sem implementação e sem
  consumidor**, e esta feature prepara a porta de **armazenamento**, não a persistência.
- Nenhuma ação para `src/api/`: a decisão de 2026-10-07 mantém o Flask como adaptador de
  entrada, e esta feature não cria rota, schema nem camada HTTP nova.
- Nenhuma ação que toque `tests/test_upload_seguranca.py`. O arquivo é a `RF-06` inteira:
  os 15 testes passam a executar por efeito do `conftest.py`, e o `T014` confere que o
  `diff` dele está **vazio**.

### Paralelismo: nenhuma ação `[//]` viola o critério

As três duplas marcadas — `T002`/`T003`, `T006`/`T007`, `T011`/`T012` — tocam arquivos alvo
diferentes e **não** dependem uma da outra. É a diferença em relação à feature 006, onde o
`T006` foi marcado `[//]` violando o critério, com ressalva declarada: aqui não foi
preciso. A única ressalva é a da §"Fase 4", em que `T011` e `T012` compartilham a **pasta**
de evidência e escrevem arquivos distintos.

## Notas de execução

> Reservado para `/reversa-coding` registrar avisos ou observações que surgiram durante a execução.
> Não use isso para corrigir ações, edits manuais ficam fora desse arquivo, vão direto no código.

> Execução de 2026-10-07. **16 ações concluídas, nenhuma aberta.** As medições estão
> em `evidence/`; o impacto no legado em `legacy-impact.md`; a vigilância em
> `regression-watch.md`. O que segue são os desvios e os achados, todos declarados
> em vez de silenciados.

### Os dois blocos, e o que cada um mediu

| Ponto | Suíte | Paridade | `test_upload_seguranca.py` | Resíduo |
|---|---|---|---|---|
| Linha de base herdada da 006 | `231 passed, 15 errors` | `100 %` | `21 passed, 15 errors` | — |
| **Bloco 0** (`T001`–`T004`) | **`249 passed, 0 errors`** | **`100 %`** | **`36 passed`** | **zero** |
| **Bloco 1** (`T005`–`T016`) | **`261 passed, 0 errors`** | **`100 %`** | `36 passed` | **zero** |

A aritmética fecha: `231` aprovados que já existiam, `+15` que passaram a
**executar** — e não são testes novos —, `+3` do arquivo de guarda do `T003` e `+12`
das provas de contrato do `T010`, totalizando `261`. **Nenhum aprovado do Bloco 0
virou falha no Bloco 1**, que era o critério da `D-12`.

### Desvio 1 — `T007` tinha DOIS chamadores, e o plano enumerou um

A ação mandava o caso de uso repassar o dono a `armazenamento.guardar`, e ele
repassa. O que ela **não** cobria é que `upload_gedcom` também é chamador do
**carregador**: `src/application/upload_gedcom.py:67` chamava
`carregador.carregar(referencia)` sem o dono.

Medido: `11 failed, 238 passed` — cinco em `test_desfecho_do_resultado.py`, dois em
`test_porta_de_armazenamento.py` e quatro em `test_upload_seguranca.py`, todos com a
**mesma** causa, `TypeError: CarregadorDeArvoresGedcom.carregar() missing 1 required
positional argument: 'dono'`.

Corrigido na mesma rodada (`carregar(referencia, dono)`), e a suíte voltou aos `249`
do Bloco 0. **Não é defeito do produto nem falha de ambiente**, então a `RF-09` não
se aplica: o erro era da **decomposição**, que enumerou os chamadores de `guardar` e
de `resolver` e esqueceu os de `carregar`.

A lição virou mecanismo: a varredura do `T011` passou a **asserção de contagem** —
são 5 chamadores de porta em produção —, e um chamador novo obriga a revisão do dono
dele. Ver `OBS-24` do `regression-watch.md`.

### Desvio 2 — a primeira asserção do `T003` estava errada, e a suíte provou

O Bloco 0 falhou na primeira execução com `1 failed, 248 passed`, e a falha era do
arquivo que o `T003` acabara de criar: a asserção exigia
`tmp_path != Path(pasta_temporaria)`, supondo dois diretórios independentes no mesmo
teste.

**Não são, e o erro era meu.** O pytest **cacheia a instância do fixture** por teste,
então pedir `tmp_path` e `pasta_temporaria` no mesmo teste devolve o **mesmo** objeto —
que é exatamente o que a `D-02` quis dizer com "implementação única". Cada teste
continua recebendo um diretório próprio, porque `pasta_temporaria` é de escopo de
função; o que não existe é um diretório *por nome de fixture*.

A asserção passou a exigir a **igualdade** (e a raiz única). Nenhuma asserção foi
enfraquecida — a nova versão mede mais, e mede a coisa certa.

### Desvio 3 — a marcação de `[X]` e o `progress.jsonl` foram feitos por bloco, não por ação

O skill pede atualização do `actions.md` e do `progress.jsonl` **após cada ação**. A
marcação foi feita em três pontos — fim do Bloco 0, fim do Bloco 1 e fechamento —, e
não a cada uma das 16. **A rastreabilidade não foi afetada:** cada ação tem a sua
linha no `progress.jsonl`, com arquivos tocados e nota, na ordem em que foi
executada, e o arquivo é append-only (19 eventos).

A razão é prática: as linhas de ação deste documento passam de 500 caracteres, e uma
substituição literal por ação seria ruidosa e frágil. A marcação foi feita por um
instrumento que casa pelo ID — `evidence/_acoes.py`, mantido em `evidence/` para a
medição ser reproduzível, no mesmo padrão do `_t020_varredura.py` da 006.

### Achado A — a causa raiz da linha de base, e uma correção de enquadramento da 006

O `OBS-12` da feature 006 registrou que "o `tmp_path_factory` do pytest cria o
diretório-base com `mode=0o700`". **Está certo, e é impreciso num ponto que muda a
correção:** o passo que falha não é a criação do diretório **por teste**, e sim o
`TempPathFactory.getbasetemp()`, que cria `pytest-of-<usuário>` com `0o700` e em
seguida tenta **listá-lo** por `os.scandir` (`_pytest/pathlib.py:175`). O ramo do
`mktemp`, que também usa `0o700`, **nunca chega a rodar**.

Consequência prática: "trocar o modo do diretório por teste" não corrigiria nada. A
correção tem de **impedir que `getbasetemp()` seja chamado**, o que se faz declarando
o fixture `tmp_path` no `conftest.py`.

### Achado B — o instrumento de paridade suja o `git status`

O `harness.py` escreve quatro artefatos de trabalho a cada execução:
`.parity-run-oracle/` (**coberto** pelo `.gitignore`), `.parity-run-cand/` (**não**),
`_reversa_sdd/parity/_collect_oracle.py` e `_collect_cand.py` (**não**).

Os quatro foram removidos nesta limpeza, e a remoção é segura por construção:
`run_collector` (`harness.py:458-462`) regrava os dois scripts e faz
`os.makedirs(run_dir, exist_ok=True)` a cada chamada.

🔴 **É comportamento anterior a esta feature**, e a linha que falta no `.gitignore`
é ato do usuário — o arquivo está fora de `allowedPaths`. Registrado como `OBS-21`.

> ✅ **Atualização de 2026-10-07, depois desta rodada.** As duas linhas foram
> acrescentadas ao `.gitignore` por **ato do usuário** — `tests/.tmp/` e
> `.parity-run-cand/`, nas linhas 22 e 23 —, e a eficácia foi verificada com
> `git check-ignore -v` e com **arquivo dentro** dos diretórios, porque diretório
> vazio não mede `.gitignore`. Fecha o `OBS-21` e o `OBS-22`; o registro está em
> `OBS-29` do `regression-watch.md` e em `evidence/T016-conferencia-de-escopo.md` §6.
> Nada mais neste documento muda: as medições do `T016` ficam como foram feitas.

### Achado C — `src/uploads/` tem 33 entradas, e nenhuma é desta rodada

A feature 006 registrou `32`. A entrada a mais é `src/uploads/_pytest`, o
**diretório preso** que a própria rodada da 006 criou na tentativa de `--basetemp`, e
que está no inventário de 13 dela. O `32` foi medido antes de essa tentativa.

A pasta contém um GEDCOM **real** do operador (`Arvore_Unificada_Oficial_V1_2.ged`,
5,3 MB). Ela é coberta por `uploads/` no `.gitignore`, então o Princípio I está
preservado — a pasta existe exatamente para receber esse arquivo. Esta rodada **não**
escreveu nada ali: a verificação manual apontou `ANALISADOR_UPLOAD_FOLDER` para uma
pasta descartável, como a 006 fez.

### Achado D — a sonda da 006 ganhou um segundo uso, e ele exigiu um cuidado

O `T012` reexecutou a sonda de 19 casos da 006, mas o lado "antes" **não** é o
`_antes/app.py` daquela feature: é o **resultado que a 006 registrou ao entregar**
(`mensagens_depois.json`). A comparação responde à pergunta certa desta feature —
"alguma mensagem visível mudou desde a entrega anterior?" —, e não à pergunta da 006.

Cuidado que a ação exigia e foi obedecido: a sonda **sobrescreve** o arquivo de saída
com o rótulo pedido. O baseline foi copiado para
`evidence/mensagens_baseline_006.json` **antes** da execução, e a sonda rodou de uma
cópia própria em `evidence/` — o artefato entregue da 006 não foi tocado. Os dois
arquivos copiados foram conferidos por hash contra os originais.

Resultado: **texto e modo de renderização idênticos em 19 casos**, incluindo o `413`
e as classes de alerta.

### A `RF-09` não teve ação, e continua sem ter

A triagem da `RF-09` segue **vazia por medição**: os 15 testes passam, na suíte e na
verificação manual. Nenhum defeito de produto estava escondido atrás do erro de
ambiente. Se algum deles voltar a falhar por motivo de produto, a `RF-09` volta a
valer integralmente, com o procedimento do §12 do `onboarding.md`.

## Histórico de alterações

| Data | Alteração | Autor |
|------|-----------|-------|
| 2026-10-07 | Versão inicial gerada por `/reversa-to-do` | reversa |
| 2026-10-07 | Execução por `/reversa-coding`: **16 de 16 ações concluídas**, checkboxes fechados. Bloco 0 (`T001`–`T004`) devolveu o instrumento — `249 passed, 0 errors`, paridade `100 %`, zero resíduo. Bloco 1 (`T005`–`T016`) fez a costura — `261 passed, 0 errors`, paridade `100 %`, `diff` de `tests/test_upload_seguranca.py` vazio. Medições em `evidence/`; impacto em `legacy-impact.md`; vigilância em `regression-watch.md`. Três desvios e quatro achados declarados acima | reversa |

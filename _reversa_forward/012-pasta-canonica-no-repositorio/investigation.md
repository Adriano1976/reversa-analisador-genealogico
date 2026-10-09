# Investigation: Pasta canônica de uploads dentro do repositório

> Identificador: `012-pasta-canonica-no-repositorio`
> Data: `2026-10-09`
> Requirements: `_reversa_forward/012-pasta-canonica-no-repositorio/requirements.md`

## 1. O que foi investigado, e por quê

Esta feature reverte uma decisão de operação, e decisão de operação se sustenta em duas coisas: **onde o
dado realmente está no disco** e **o que impede que ele vaze**. A investigação foi atrás das duas, e
encontrou três fatos que o `requirements.md` não tinha:

1. o dado real do operador estava em **quatro** diretórios, não em um;
2. as três cópias extras são **arrasto** de uma transformação de refactor que congelou `src/` inteiro;
3. o banco da feature 008 tem **2 linhas de histórico cujas referências de arquivo não existem mais**.

Também foi investigado o que **não** precisa mudar, e a resposta é o principal achado de escopo: o
padrão do código nunca deixou de ser `src/uploads`.

## 2. A origem medida das três cópias de arrasto

As três ficam em `_reversa_refactor/pacote-reconstructed/transformations/OPP-20261003-*/before-after/src-antes/uploads/`,
com 9 arquivos e 16.920.784 bytes cada. A causa está declarada nos próprios `transformation.md`:

> "Antes de mover qualquer arquivo, `src/` foi copiado inteiro para `before-after/src-antes/`. É
> obrigatório: o `HEAD` está atrás da `LMAY` e da `GUE7`, então o Git não serve como estado anterior."
> — `OPP-20261003-RAIZ-distribuir-modulos-soltos/transformation.md:142`

Os representantes `FLAT` e `GUE7` repetem a mesma frase nos seus documentos (`:136` e `:134`). O
`src/uploads` foi junto porque **está dentro de `src/`** — a cópia foi do diretório inteiro, sem
exclusão. Não houve decisão de copiar dado do operador: houve cópia de `src/`, e o dado estava lá
dentro.

**O que sustenta a remoção** (medido, não presumido):

| Verificação | Resultado |
|---|---|
| Algum arquivo dessas pastas está rastreado pelo git? | **Não.** `git ls-files` sobre as três: zero ocorrências de `uploads/`. Os 19 `.ged`/`.csv` versionados no repositório inteiro são fixtures sintéticas de 26 a 606 bytes |
| O git protege o caminho? | **Sim, por ignore.** `git check-ignore -v` responde `.gitignore:30:uploads/` — o padrão com barra final casa em qualquer profundidade |
| O contexto de build do Docker inclui? | **Não.** `.dockerignore` é lista de **permissão** (`!requirements.txt`, `!src/`, `!src/**`); `_reversa_refactor/**` não está nomeado, logo não entra |
| Algum documento ou instrumento referencia `src-antes/uploads`? | **Não.** As 30 ocorrências de `before-after/src-antes` no repositório apontam todas para `.py` de `reconstructed/` |
| Algum instrumento varre a árvore inteira de `src-antes/`? | **Não.** `registrar-diff.py:105-113` filtra `if not arquivo.endswith(".py")` e lê caminhos explícitos; `verificar-estrutura.py:269-274` opera no `src/` atual e **exclui** `uploads` da lista de pacotes |
| Algum conteúdo dessas cópias é único? | **Não — e este é o critério.** Todo `sha256` das três cópias ocorre também em `src/uploads`: **0 órfãos** em 27 arquivos |

O último item é o que transforma a remoção de fé em prova, e virou o critério de cancelamento da `D-03`.

## 3. O que a extração afirma, e o que está defasado

`_reversa_sdd/inventory.md:182` afirma:

> "**Dados do usuário:** 15 arquivos em `src/uploads/` e 4 em `uploads/` (local legado da raiz, anterior
> à ancoragem)."

Medido em 2026-10-09: **nem `uploads/` nem `analisador-genealogico/uploads/` existem** — a varredura
recursiva do repositório devolve só `src/uploads` mais os três arrastos e o `_tmp_e2e/uploads` de
evidência da feature 007. A contagem também está velha: são 36 arquivos. Nada disso é corrigido aqui:
`_reversa_sdd/` é do `/reversa`, e a `RN-07` proíbe esta feature de tocá-lo.

## 4. As duas guardas do Princípio I, e como cada uma funciona

### 4.1 `.gitignore` — padrão com barra final casa em qualquer profundidade

A linha é `uploads/` (`.gitignore:30`), e o comentário do próprio arquivo registra o efeito pretendido:
"O padrão com barra final casa em qualquer profundidade, cobrindo `uploads/` e
`analisador-genealogico/uploads/`". Verificado com `git check-ignore -v`, que não só confirma a
exclusão como **nomeia a regra e a linha** que a produziu — é por isso que a asserção de efeito da
`D-04` usa esse comando e não um teste de texto puro.

### 4.2 `.dockerignore` — lista de permissão, e a ordem importa

O arquivo é uma lista de **permissão** (`*` seguido de `!requirements.txt`, `!src/`, `!src/**`), com
reexclusões no fim (`src/uploads/` em `:24`, depois de `!src/**`). O comentário do arquivo registra a
medição que levou a essa forma: a regra de negação cobria 12 dos 22 diretórios que recusam
`os.scandir`, e `docker build` percorre o contexto inteiro e **aborta no primeiro diretório ilegível**.

A ordem não é estilo. A documentação oficial do Docker é explícita:

> "The placement of `!` exception rules influences the behavior: **the last line of the `.dockerignore`
> that matches a particular file determines whether it's included or excluded.**"
> — [Docker Docs, *Build context*, `.dockerignore files` → *Negating matches*](https://docs.docker.com/build/concepts/context/)

É por isso que `src/uploads/` tem de vir **depois** de `!src/**`: invertidas as duas linhas, o dado real
do operador passa a ser enviado ao daemon sem que nenhuma linha tenha sido removida. A `D-04` prende
essa ordem com asserção explícita.

## 5. O risco residual: `git clean`

`src/uploads` é não rastreada por construção, e as duas formas de `git clean` que removem ignorados a
apagam. A documentação oficial:

> "**`-x`** Don't use the standard ignore rules... This allows removing all untracked files, including
> build products."
> "**`-X`** Remove only files ignored by Git. This may be useful to rebuild everything from scratch, but
> keep manually created files."
> — [git-clean(1)](https://git-scm.com/docs/git-clean)

Ou seja: `-x` **e** `-X` apagam `src/uploads`; `clean.requireForce` vem `true`, então um `-f` é
necessário; e `-n` (`--dry-run`) mostra o que sairia sem remover. Decisão do operador em 2026-10-09
(§9 Q3 do `requirements.md`): **documentar o risco e manter backup próprio**, sem criar verbo de backup
na ferramenta.

## 6. Alternativas avaliadas

| Tema | Alternativas descartadas | Onde está a decisão |
|---|---|---|
| Onde a pasta canônica vive | (a) pasta fora do repositório, como a 010 declarou; (b) pasta nomeada por variável de ambiente dentro do contêiner; (c) pasta do repositório, sem configuração | `D-01`, `D-02` |
| Como remover as cópias de arrasto | (a) verbo novo na ferramenta de manutenção; (b) `Remove-Item -Recurse` manual; (c) instrumento *fail-closed* por conteúdo | `D-03` |
| Como prender as guardas | (a) só asserção literal; (b) só `git check-ignore`; (c) teste que muta o arquivo real; (d) asserção literal **mais** efeito **mais** ordem, com mutação em cópia temporária | `D-04`, `D-05` |
| O que fazer com o `onboarding.md` da 010 | (a) aviso só no topo; (b) reescrever substituindo; (c) revisar no lugar preservando o texto antigo | `D-06` |
| Qual manifesto usar no expurgo | (a) o da 010 como está; (b) apagar por padrão de nome; (c) regenerar antes de aplicar | `D-07` |
| Como superar o adendo 010 | (a) "superado" genérico; (b) reescrever o adendo antigo; (c) superação **parcial** com a lista do que permanece | `D-10` |
| Como verificar "pasta em uso" | (a) tabela de portas do sistema; (b) só processos do host; (c) `docker compose ps` mais processos do host | `D-11` |

## 7. Padrões aplicados

1. **Instrumento *fail-closed* para operação destrutiva.** Padrão já praticado na 010 (`migrar` copia
   com conferência e nunca remove a origem) e nesta feature em `evidence/_remover_copia_externa.py`.
   Em vez de "remova e torça", o instrumento **compara antes** e não remove se a comparação falhar.
2. **Operação destrutiva por manifesto revisável, com simulação obrigatória.** Padrão da 010 (`D-05`),
   reaproveitado pelo `RF-10`.
3. **Revisão no lugar com marcador, em vez de reescrita.** Precedente `D-02` da feature 004
   ("**Revista em 2026-10-04.**"). Preserva o registro e evita procedimento morto circulando.
4. **Superação parcial de adendo.** A convenção do projeto é marcar superação no adendo antigo, sem
   apagar conteúdo. Quando só parte dos deltas cai, a linha de vigência nomeia o que permanece.
5. **Prova por `diff` vazio.** Padrão da 010 (`D-08`): "não mudou" se prova com `git diff` vazio, não
   com afirmação.

## 8. Achados de ambiente (medidos nesta rodada, fora do escopo da feature)

1. **`DATABASE_URL` no processo.** Definido no ambiente desta sessão apontando para `db:5432`, embora
   **não** esteja nas variáveis de usuário nem de máquina do Windows, e `psycopg2` **não** esteja
   instalado no `.venv`. Com a variável, `tests/test_persistencia_desabilitada.py` falha em 2 testes
   (`325 passed, 2 failed, 9 skipped`); sem ela, a suíte dá a linha de base exata da 010
   (`327 passed, 9 skipped`). **Não é regressão desta feature.** O rastreamento correto é
   `/reversa-debugger`.
2. **Os dois contêineres estão no ar.** `docker compose ps`: `genealogia-app-1` (app, `127.0.0.1:5080`)
   e `genealogia-db-1` (Postgres 16, `healthy`, `127.0.0.1:5432`). O app monta o caminho de host que a
   remoção da cópia externa esvaziou, e por isso **`/app/src/uploads` não existe dentro dele**:
   `ls` responde "No such file or directory". A rota `/` segue respondendo 200. A correção é o `RF-01`
   mais `docker compose up -d`, que recria só o serviço `app`.
3. **O histórico do banco tem 2 referências não resolvidas.** `dna_analysis` tem 2 linhas, com
   `tree_ref` = `0646f8431ba58cca__sonda_t014.ged` e `dbc25ecc1cb17db3__sonda_t014.ged`, registradas em
   2026-10-09 entre 14:54:04 e 14:54:40 UTC — as sondas do `T016` da 010, pelo contêiner. **Nenhum
   arquivo com `sonda` no nome existe hoje em lugar nenhum do projeto** (varredura completa). Os
   artefatos da 010 ainda afirmam o contrário: `onboarding.md` §16 e `regression-watch.md` dizem que 4
   arquivos sintéticos ficaram no destino canônico.
4. **O histórico é só de escrita.** A varredura de `src/` mostra **zero `SELECT`**: nenhuma das três
   `action` consulta `dna_analysis`. A referência quebrada é **latente, não observável** — nada no
   runtime a resolve. É por isso que a `D-13` decide não corrigi-la aqui.
5. **A tabela de portas não é instrumento confiável sob o sandbox.** Três execuções de
   `Get-NetTCPConnection` produziram resultados contraditórios — uma não listou 5080 nem 5000, outra
   listou 5432, uma terceira não listou nada — **enquanto `docker compose ps` mostrava os dois serviços
   no ar**. Foi o que quase fez esta feature tratar uma pasta de contêiner vivo como livre. A `D-11`
   troca o instrumento.

## 9. Limites desta investigação

O que **não** foi verificado, e onde a verificação fica:

| Não verificado aqui | Por que | Onde é verificado |
|---|---|---|
| `registrar-diff.py` e `verificar-estrutura.py` **executando** depois da remoção | A remoção é ação do estágio de coding; a investigação leu o código, e leitura não é execução | Passo 4 do plano, com a saída registrada |
| O `bind mount` relativo `./src/uploads` funcionando no Docker Desktop | Não se recria contêiner no estágio de plano | `onboarding.md` §5, e passo 1 do plano |
| O total exato de arquivos depois do expurgo | Depende de o manifesto ser aplicado | **Previsto** por medição: 18 arquivos, 27.925.843 bytes — `data-delta.md` §5 |
| Se algum arquivo removido é referenciado por linha do banco | As referências do banco foram consultadas; o expurgo ainda não rodou | Passo 9 do plano, com o manifesto na mão |
| A semântica de ordem do `.dockerignore` por medição própria | Seria preciso montar contexto de build | Tomada da [documentação oficial](https://docs.docker.com/build/concepts/context/) e do comentário medido do próprio arquivo (`:22-23`) |

## 10. Fontes

- `_reversa_sdd/upload-gedcom/contracts.md#2.1`, `#2.2`
- `_reversa_sdd/inventory.md#4`, `#5`
- `_reversa_sdd/c4-containers.md#2`
- `_reversa_sdd/addenda/008-persistencia-postgres-docker.md`, `addenda/010-uploads-fora-do-repositorio.md`
- `_reversa_refactor/pacote-reconstructed/transformations/OPP-20261003-{FLAT,GUE7,RAIZ}*/transformation.md`
- `registrar-diff.py`, `verificar-estrutura.py` (leitura)
- `.gitignore:30`, `.dockerignore:12-24`, `docker/Dockerfile:25-26`, `docker-compose.yml:61-67`
- [Docker Docs — Build context, `.dockerignore` e a ordem das exceções](https://docs.docker.com/build/concepts/context/)
- [git-clean(1) — `-x`, `-X`, `-n`](https://git-scm.com/docs/git-clean)
- `.reversa/principles.md#I`, `#III`
- Medições desta rodada: inventários por `sha256`, consulta ao histórico do banco, `docker compose ps`

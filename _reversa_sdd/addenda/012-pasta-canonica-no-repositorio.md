# Adendo: pasta canônica de uploads dentro do repositório

> Identificador da feature: `012-pasta-canonica-no-repositorio`
> Data: `2026-10-09`
> Cenário: **legado** (âncora em `_reversa_sdd/architecture.md` + `_reversa_sdd/domain.md`)

## Vigência

Vigente desde 2026-10-09.

## Resumo da entrega

Esta feature **reverte**, em parte, a decisão de operação que o adendo `010-uploads-fora-do-repositorio`
declarou no mesmo dia: a pasta canônica de dados volta a ser `src/uploads`, **dentro** da árvore do
repositório, e passa a ser a **única**. Nenhuma linha de `src/` foi tocada — o padrão do código nunca
deixou de ser `<diretório do app>/uploads`; o que mudou foi o que a documentação e a composição de
contêineres declaravam.

A entrega tem cinco frentes: a composição volta a montar `./src/uploads` sobre o mesmo alvo interno (e o
`docker-compose.yml` fica **idêntico** ao entregue pela feature 008); o `README.md` volta a declarar a
pasta do repositório como canônica e passa a declarar as **duas guardas do Princípio I** e o risco de
`git clean`; as **três cópias de arrasto** de dado real dentro de `_reversa_refactor/` — 27 arquivos e
50.762.352 bytes, deixadas quando o refactor de 2026-10-03 congelou `src/` inteiro — são removidas com
conferência de órfão por `sha256`; as duas guardas ganham **teste que as prende**, com asserção de efeito,
de ordem e verificação por mutação; e o resíduo de instrumento é expurgado por manifesto, com simulação
antes de aplicar.

**24 de 24 ações executáveis concluídas** (`actions.md`), **0 falhas**. A 25ª ação, a escrita deste
adendo, é do estágio `/reversa-sync`. Suíte: `327 passed, 9 skipped` antes e **`335 passed, 9 skipped`**
depois — a diferença é exatamente o arquivo de teste novo. Paridade diferencial em **100 %** pelo
invólucro, com o `harness.py` byte a byte idêntico.

**Nenhuma regra de domínio foi modificada.** O `git diff` está vazio em `src/`.

## Impacto por artefato da extração

| Artefato | Seção | Tipo de impacto | Delta |
|----------|-------|-----------------|-------|
| `_reversa_sdd/architecture.md` | §1 Visão Geral da Arquitetura | delta-de-dados | A raiz declarada volta a ser a pasta do repositório. O "sistema de arquivos local" continua sendo o único estado persistente |
| `_reversa_sdd/inventory.md` | §4 Pontos de Entrada e Configurações | regra-alterada | `ANALISADOR_UPLOAD_FOLDER` volta a ser **sobreposição de processo**, usada pela suíte e pelo invólucro de paridade para não escreverem na pasta real — e não modo de operação |
| `_reversa_sdd/inventory.md` | §5 Banco de Dados e Armazenamento | delta-de-dados | Os arquivos enviados voltam a ser declarados em `src/uploads/`, e a pasta passa a ter **18 arquivos e 27.925.843 bytes** depois do expurgo do resíduo |
| `_reversa_sdd/c4-containers.md` | Container 3 — sistema de arquivos local | delta-de-dados | O ponto de montagem da composição volta a ser `./src/uploads`, com o **mesmo** alvo interno `/app/src/uploads` |
| `_reversa_sdd/upload-gedcom/contracts.md` | §2.2 Pasta | regra-alterada | O padrão do código passa a ser também o uso declarado; a variável perde o papel de modo de operação e o mantém como sobreposição de teste |
| `_reversa_sdd/upload-gedcom/design.md` | Estado Interno | delta-de-dados | A linha da pasta volta a apontar `src/uploads/`; a imutabilidade e a ausência de remoção pelo sistema continuam |
| `_reversa_sdd/data-dictionary.md` | Caminho padrão e tabela de variáveis de ambiente | delta-de-dados | O caminho padrão continua o do código e passa a ser o único; a variável é sobreposição. Nenhum nome de campo ou de arquivo muda |
| `_reversa_sdd/erd-complete.md` | `ARQUIVO_ARMAZENADO` | delta-de-dados | A coluna de localização aponta a pasta do repositório; a chave de conteúdo e a forma do nome permanecem idênticas |
| `_reversa_sdd/state-machines.md` | §5 Estados Deliberadamente NÃO Gerados | regra-alterada | O arquivo enviado continua sem ciclo de vida e o runtime continua sem apagar nada. O expurgo por manifesto, fora do runtime, **deixou de ser possibilidade e foi executado** |
| `_reversa_sdd/user-stories/upload-gedcom.md` | O que esta história não cobre | regra-alterada | A ressalva sobre expurgo por manifesto, acionado pelo operador, continua verdadeira — e agora é fato consumado |
| `_reversa_sdd/addenda/008-persistencia-postgres-docker.md` | O que a extração não precisa mudar | delta-de-contrato-externo | O 008 volta a estar **integralmente correto**: ele já afirmava "*bind mount* para `src/uploads/`" e "nenhum arquivo precisa ser renomeado ou movido" |
| `_reversa_sdd/addenda/010-uploads-fora-do-repositorio.md` | todo o adendo | regra-removida | **10 dos 13 impactos do adendo 010 deixam de valer**; 3 permanecem. Detalhe na seção seguinte |
| `README.md` (fora da extração, citado por completude) | Configuração de execução e Onde ficam os arquivos enviados | delta-de-contrato-externo | A pasta canônica é `src/uploads`; a variável é sobreposição; as duas guardas do Princípio I e o risco de `git clean` passam a ser declarados. Quatro afirmações falsas foram corrigidas |
| `.gitignore`, `.dockerignore` (fora da extração) | — | delta-de-contrato-externo | As duas linhas que sustentam o Princípio I passam a ter **teste que as prende** (`tests/test_guardas_do_armazenamento.py`), com asserção de ordem no `.dockerignore` |
| `_reversa_refactor/**` (fora da extração) | — | componente-extinto | Os três `…/before-after/src-antes/uploads/` deixam de existir; os `.py` irmãos ficam intactos |

## O que este adendo reverte do adendo 010

O adendo 010 foi escrito no mesmo dia e declarava a decisão oposta. **Ele não foi editado** — a linha de
superação é acrescentada pela pipeline reversa, não por este skill. Enquanto isso, esta seção é o que
impede que os dois sejam lidos como verdade simultânea: dos **13 impactos** que o 010 declarou,
**10 deixam de valer** e **3 permanecem**.

**Deixam de valer (10):** `architecture.md` §1 e §7; `inventory.md` §4 e §5;
`upload-gedcom/contracts.md` §2.2; `upload-gedcom/design.md`; `c4-containers.md` Container 3;
`data-dictionary.md`; `erd-complete.md` `ARQUIVO_ARMAZENADO`; e a linha sobre o adendo 008. Todos os
dez dependiam de a pasta canônica estar **fora** do repositório.

**Permanecem (3), e continuam verdadeiros:**

1. `state-machines.md` §5 — existe, fora do runtime, um expurgo por manifesto com simulação.
2. `user-stories/upload-gedcom.md` — a ressalva de que existe expurgo acionado pelo operador.
3. `README.md` — a tabela lista a variável da pasta e o caminho de execução da paridade é o invólucro
   `tests/rodar_paridade.py`.

> **Correção de contagem.** O `roadmap.md` desta feature dizia "cancela 9 e mantém 4", escrito antes da
> conferência linha a linha. A contagem medida é **10 e 3**: a linha `architecture.md` §7 também cai,
> porque o que ela declara é que a pasta compartilhada passou a ser *a canônica fora do repositório*.

## Regras sob vigilância

`W001`, `W002`, `W003`, `W004`, `W005`, `W006`, `W007`, `W008` — detalhe, tipo de verificação e sinal de
violação em `_reversa_forward/012-pasta-canonica-no-repositorio/regression-watch.md`. Cinco achados sem
peso de regressão estão na seção "Observações" do mesmo arquivo (`OBS-01` a `OBS-06`), entre eles o
critério de resíduo por conjunto fechado de nomes e as duas referências não resolvidas do banco.

## Fontes

- `_reversa_forward/012-pasta-canonica-no-repositorio/requirements.md`
- `_reversa_forward/012-pasta-canonica-no-repositorio/roadmap.md` (decisões `D-01` a `D-13`)
- `_reversa_forward/012-pasta-canonica-no-repositorio/legacy-impact.md`
- `_reversa_forward/012-pasta-canonica-no-repositorio/regression-watch.md`
- `_reversa_forward/012-pasta-canonica-no-repositorio/data-delta.md`
- `_reversa_forward/012-pasta-canonica-no-repositorio/progress.jsonl` (24 ações)
- `_reversa_forward/012-pasta-canonica-no-repositorio/evidence/` (20 arquivos: 15 de medição e 5 instrumentos)
- `_reversa_sdd/addenda/010-uploads-fora-do-repositorio.md` (o adendo revertido em parte)

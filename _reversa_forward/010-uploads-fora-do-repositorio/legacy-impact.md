# Legacy Impact — feature `010-uploads-fora-do-repositorio`

> Data: `2026-10-09`
> Extração de referência: `_reversa_sdd/architecture.md`, `_reversa_sdd/domain.md`
> Paridade diferencial: **100 %** antes e depois, com o `harness.py` byte a byte idêntico
> Âncora: **legado** (extração reversa presente e vigente)

## 1. Arquivos afetados

| Arquivo afetado | Componente | Tipo | Severidade | Justificativa |
|-----------------|------------|------|-----------|---------------|
| `tests/manutencao_de_uploads.py` (novo) | — | componente-novo | LOW | Ferramenta de manutenção do operador (`migrar`, `manifesto`, `expurgo`, `duplicatas`); não é runtime e não é importada pela aplicação |
| `tests/rodar_paridade.py` (novo) | instrumento de paridade — invólucro | componente-novo | LOW | Define a pasta de upload antes de lançar o harness, para o instrumento não escrever na pasta real |
| `tests/test_manutencao_de_uploads.py` (novo) | — | componente-novo | LOW | 19 testes da ferramenta, com arquivos sintéticos em pasta temporária |
| `tests/test_rodar_paridade.py` (novo) | — | componente-novo | LOW | 5 testes do invólucro, incluindo o controle negativo do redirecionamento |
| `tests/test_documentacao_do_upload.py` (novo) | — | componente-novo | LOW | Prende a variável na tabela do `README.md` e o caminho da paridade no invólucro |
| `README.md` | documentação do operador | delta-de-contrato-externo | MEDIUM | A variável entra na tabela de configuração; o destino canônico e o caminho da paridade passam a ser declarados; duas afirmações sobre `src/uploads/` deixaram de ser verdadeiras e foram corrigidas |
| `docker-compose.yml` | composição de contêineres | delta-de-dados | MEDIUM | O ponto de montagem deixa de ser `./src/uploads` e passa a ser a pasta canônica do host, fora do repositório |
| `D:\dados-genealogicos\uploads` | armazenamento dos arquivos enviados | delta-de-dados | MEDIUM | 36 arquivos e 27.932.474 bytes **copiados** com conferência de `sha256`; a origem permanece intacta |
| `src/**` | borda, casos de uso, núcleo, parsers, reporting, utils, ports, templates | **sem mudança** | — | `git diff --stat -- src` vazio: nenhuma regra de domínio, nenhum contrato HTTP e nenhum caminho de análise foi tocado |
| `_reversa_sdd/**` | extração e instrumentos | **sem mudança** | — | `git diff --stat -- _reversa_sdd` vazio; o `harness.py` conserva o mesmo `sha256` |

## 2. Diff conceitual por componente

### 2.1 Armazenamento dos arquivos enviados

**Antes.** A pasta era, no uso declarado, `<raiz do repositório>/src/uploads` — o único estado
persistente do sistema (`architecture.md#1`). O contrato de resolução já previa sobreposição por
`ANALISADOR_UPLOAD_FOLDER` (`upload-gedcom/contracts.md#2.2`), e a suíte já o usava para não escrever na
pasta real (`tests/conftest.py:154`).

**Depois.** O uso declarado aponta a pasta para uma pasta canônica **fora da árvore do repositório**, nos
dois modos de execução. **O código de resolução não mudou** — o padrão continua sendo
`<diretório do app>/uploads` e a variável continua sobrepondo. O que muda é o modo de operação
documentado, e é a documentação que sustenta o afastamento (`RN-01`).

### 2.2 Composição de contêineres

**Antes.** O serviço `app` montava `./src/uploads` (pasta do repositório) sobre `/app/src/uploads`.

**Depois.** Monta a pasta canônica do host sobre o **mesmo alvo interno**. O alvo não muda por escolha
deliberada (`D-02`): assim não entra uma segunda variável de ambiente no contêiner, o comentário do
`docker/Dockerfile` continua verdadeiro e o caminho interno segue sendo o que o código deriva de
`__file__`. Verificado no ciclo `down`/`up`: os arquivos sobreviveram e as três etapas de análise
concluíram antes e depois.

### 2.3 Instrumento de paridade

**Antes.** Executar o harness escrevia as sondas de GEDCOM e as fixtures de DNA na pasta **real** do
operador: 18 arquivos e 6.631 bytes medidos em 2026-10-09. A causa é estrutural — o coletor candidato
importa a aplicação, que resolve a pasta no import, e o `chdir` que o coletor já faz não a redireciona
desde a feature 006.

**Depois.** O caminho documentado passa a ser o invólucro `tests/rodar_paridade.py`, que define
`ANALISADOR_UPLOAD_FOLDER` antes de lançar o instrumento. **O `harness.py` não foi editado** — e isso é
uma escolha, não uma limitação: o instrumento é a régua da paridade, o repositório já o tratou como
"instrumento, não objeto da feature" e há precedente de que editar `_reversa_sdd/**` não é um caminho
liberado. Medição: paridade **100 %**, pasta real **36 → 36 sem alteração**, com 13 arquivos criados na
pasta descartável como controle positivo.

### 2.4 Documentação do operador

A variável entra na tabela de configuração do `README.md` — ela existia desde antes, mas só nas specs,
invisível para quem opera. Entram também o destino canônico, o aviso de que esquecer a variável não gera
erro e o caminho de execução da paridade. Duas afirmações que deixaram de ser verdadeiras foram
corrigidas: a que dizia que "cada processo lê o mesmo diretório de uploads `src/uploads/`" e a que
localizava os arquivos enviados em `src/uploads/`.

## 3. Preservadas

Nenhuma regra 🟢 do domínio foi alterada, removida ou teve confidência rebaixada. As que esta feature
toca de perto, e que continuam verdadeiras:

| Regra preservada | Fonte | Como foi conferida |
|------------------|-------|--------------------|
| A pasta é resolvida **uma vez**, no import, ancorada no arquivo do app, com a variável sobrepondo | `upload-gedcom/contracts.md#2.2` | `git diff` vazio em `src/` |
| O nome no disco é `<16 hexadecimais>__<nome visível>`, com a chave vinda do conteúdo | `upload-gedcom/contracts.md#2.1` | `git diff` vazio; a migração preserva o nome e o histórico continua resolvível |
| A aplicação **nunca** apaga arquivo enviado | `upload-gedcom/contracts.md#2.2`; `state-machines.md#5` | `git diff` vazio; o expurgo é ferramenta separada, por manifesto |
| A referência do formulário sustenta a continuidade entre requisições | `upload-gedcom/contracts.md#3` | as três etapas concluíram nos dois modos, sem "arquivo não existe mais" |
| Arquivo com a mesma chave não é reescrito | `upload-gedcom/contracts.md#2.2` | `git diff` vazio; a migração é idempotente e a re-entrega da fixture não criou arquivo novo |
| O sistema de arquivos continua sendo o único estado persistente | `architecture.md#1` | a mudança troca a **raiz**, não o mecanismo |
| A superfície HTTP é a mesma: rota, campos, status e mensagens | `openapi/index.yaml`; `user-stories/` | `git diff` vazio em `src/`; as sondas dos dois modos receberam as mensagens de contrato esperadas |

## 4. Modificadas

**Nenhuma regra de domínio.** O que mudou é contrato de **operação**, e está listado na tabela do §1:
o ponto de montagem da composição, a localização declarada dos arquivos e a documentação do operador.
O padrão do código permanece `<diretório do app>/uploads`, o que mantém toda afirmação da extração sobre
o armazenamento ainda correta.

A consequência para a extração é **aditiva**: ela não precisa ser corrigida, e sim complementada com o
modo de operação declarado — o que o `/reversa-sync` converge em `_reversa_sdd/addenda/`.

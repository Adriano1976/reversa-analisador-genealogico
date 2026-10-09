# Legacy Impact — feature `012-pasta-canonica-no-repositorio`

> Data: `2026-10-09`
> Extração de referência: `_reversa_sdd/architecture.md`, `_reversa_sdd/domain.md`
> Paridade diferencial: **100 %** pelo invólucro, com o `harness.py` byte a byte idêntico
> Âncora: **legado** (extração reversa presente e vigente)

## 1. Arquivos afetados

| Arquivo afetado | Componente | Tipo | Severidade | Justificativa |
|-----------------|------------|------|-----------|---------------|
| `docker-compose.yml` | composição de contêineres | delta-de-contrato-externo | MEDIUM | O ponto de montagem volta de um caminho absoluto do host para `./src/uploads`, com o mesmo alvo interno. O arquivo fica **idêntico** ao entregue pela feature 008 (`git diff HEAD` vazio) |
| `README.md` | documentação do operador | delta-de-contrato-externo | MEDIUM | A pasta canônica passa a ser declarada como `src/uploads`, dentro do repositório; as duas guardas do Princípio I e o risco do `git clean` passam a ser declarados; a linha da variável muda de papel. **Quatro** afirmações que a reversão tornou falsas foram corrigidas |
| `tests/test_guardas_do_armazenamento.py` (novo) | testes de guarda | componente-novo | LOW | 8 testes que prendem as duas linhas de configuração que sustentam o Princípio I, com asserção de efeito, de ordem e verificação por mutação |
| `tests/test_documentacao_do_upload.py` | testes de documento | regra-alterada | LOW | A exigência da variável na tabela de configuração continua; o que muda é a justificativa, que afirmava ser a documentação que mantém a pasta fora do repositório |
| `_reversa_forward/010-uploads-fora-do-repositorio/onboarding.md` | documentação de operação | regra-alterada | MEDIUM | Revisado no lugar: aviso no topo e 9 marcadores `Revisto em 2026-10-09`, com o texto original preservado. A seção 12, que mandava apagar `src/uploads/`, passa a trazer aviso explícito de **não executar** |
| `src/uploads` | armazenamento dos arquivos enviados | delta-de-dados | **HIGH** | Passa de 36 arquivos e 27.932.474 bytes para **18 arquivos e 27.925.843 bytes**: saem 18 de resíduo de instrumento (6.631 bytes). Nenhum arquivo do operador é removido, e os nomes não mudam |
| `D:\dados-genealogicos\uploads` | armazenamento — cópia externa | delta-de-dados | MEDIUM | **Removida** em 2026-10-09, por ordem explícita do operador, com inventário conferido por `sha256` antes e depois (36 arquivos idênticos dos dois lados, origem intacta). A pasta deixou de ser declarada como canônica |
| `_reversa_refactor/…/before-after/src-antes/uploads/` (3 diretórios) | artefato do framework, fora da extração | componente-extinto | MEDIUM | **Removidos**: 27 arquivos e 50.762.352 bytes de dado real que o refactor de 2026-10-03 arrastou ao copiar `src/` inteiro. Os `.py` irmãos em `src-antes/` ficam intactos |
| `src/**` | borda, casos de uso, núcleo, parsers, reporting, utils, ports, templates | **sem mudança** | — | `git diff -- src` vazio e `git diff --stat -- src` vazio: nenhuma regra de domínio, nenhum contrato HTTP e nenhum caminho de análise foi tocado |
| `_reversa_sdd/**` | extração e instrumentos | **sem mudança** | — | `git status --porcelain -- _reversa_sdd` só lista o adendo da feature 010, que já estava lá; o `harness.py` conserva o mesmo `sha256` |

## 2. Diff conceitual por componente

### 2.1 Armazenamento dos arquivos enviados

**Antes.** A feature 010 havia declarado a pasta canônica **fora** da árvore do repositório, e o
`README.md` ensinava a apontar `ANALISADOR_UPLOAD_FOLDER` para lá. O dado real acabou existindo em
**quatro** diretórios: `src/uploads` (36 arquivos), a cópia externa (36) e três cópias de arrasto dentro
de `_reversa_refactor/` (9 cada), somando 78.694.826 bytes.

**Depois.** A pasta canônica volta a ser `src/uploads`, dentro do repositório, e é a **única**
(`RN-01`). O dado real existe em **um** diretório, com 18 arquivos e 27.925.843 bytes. O que sustenta a
decisão são duas linhas de configuração, e é por isso que elas passam a ter teste.

### 2.2 Composição de contêineres

**Antes.** O serviço `app` montava `D:/dados-genealogicos/uploads` sobre `/app/src/uploads` — um caminho
absoluto de host que prendia a máquina ao arquivo.

**Depois.** Volta a montar `./src/uploads` sobre o **mesmo alvo interno**. O alvo não muda, e continua
sendo o que o código deriva de `__file__`; o comentário do `docker/Dockerfile` (`:25-26`) segue
verdadeiro sem edição, porque ele nunca nomeou o lado do host. Medição: `git diff HEAD --
docker-compose.yml` **vazio**, isto é, o arquivo é byte a byte o que a feature 008 entregou.

Verificado também o efeito colateral: o contêiner do app estava no ar montando o caminho removido, e
por isso `/app/src/uploads` respondia "No such file or directory" dentro dele. `docker compose up -d`
recriou **só** o serviço `app`; o `db` seguiu `Running`, `healthy`, com o mesmo `CREATED` e o mesmo
volume — nenhum `down -v` foi executado.

### 2.3 Guardas do Princípio I

**Antes.** Duas linhas de configuração sustentavam sozinhas o Princípio I com a pasta dentro do
repositório: `uploads/` no `.gitignore` e `src/uploads/` no `.dockerignore`. **Nenhuma das duas tinha
teste.**

**Depois.** `tests/test_guardas_do_armazenamento.py` prende as duas com três asserções cada: a linha
existe, o **efeito** acontece (`git check-ignore -v` nomeia o `.gitignore`), e — no `.dockerignore` — a
**ordem** é a correta, com `src/uploads/` depois de `!src/**`. A ordem é regra real do Docker: a última
linha que casa vence, e invertidas as duas o dado voltaria ao contexto de build sem que nenhuma linha
fosse removida. O teste é exercitado por **mutação** sobre cópias temporárias, porque uma asserção que
nunca foi vista falhar não é prova.

### 2.4 Instrumentos do refactor

**Antes.** As três transformações de 2026-10-03 congelaram `src/` inteiro em `before-after/src-antes/`,
e `src/uploads` foi junto porque está dentro de `src/`. Os instrumentos que usam esse congelado
(`registrar-diff.py`) ignoram `uploads/` por construção: filtram `endswith(".py")` e leem caminhos
explícitos.

**Depois.** As três cópias de arrasto saem, e os `.py` irmãos ficam. A prova de que a retirada não
quebrou os instrumentos é um **controle A/B**: as cópias foram reconstruídas a partir de `src/uploads`
(9 nomes, mesmo conteúdo, mesmo `sha256`) e a saída dos dois instrumentos é **idêntica** com e sem elas
(`evidence/T013-instrumentos-do-refactor.txt`). Achado declarado: os dois **já saíam com código 1 antes
desta feature** — `registrar-diff.py` aborta em `src/core/gedcom_state.py`, apagado pelo `T023` da
feature 005, e `verificar-estrutura.py` compara o `src/` de hoje com o congelado de 2026-10-03.

### 2.5 Documentação do operador

A seção "Onde ficam os arquivos enviados" do `README.md` foi reescrita: `src/uploads` é declarada a
pasta canônica e única, e a variável passa a ser apresentada como **sobreposição de processo** usada
pela suíte e pelo invólucro de paridade. Entram as duas guardas e o aviso de que `git clean -xdf` (e
`-Xdf`) apaga a pasta, porque ela é não rastreada. Quatro outras afirmações que a reversão tornou falsas
foram corrigidas — na visão geral, no parágrafo da ferramenta, na árvore do projeto e na seção de
arquitetura. `markdownlint`: **zero problemas**.

## 3. Preservadas

Nenhuma regra 🟢 do domínio foi alterada, removida ou teve confidência rebaixada. As que esta feature
toca de perto, e que continuam verdadeiras:

| Regra preservada | Fonte | Como foi conferida |
|------------------|-------|--------------------|
| O nome do cliente nunca compõe o caminho; a forma é fechada (`^[0-9a-f]{16}__[A-Za-z0-9._-]+$`) | `domain.md#3.5`; `upload-gedcom/contracts.md#2.1` | `git diff` vazio em `src/`; a remoção não renomeia nem apaga arquivo armazenado |
| A extensão original é preservada, não fixada em `.ged` | `domain.md#3.5` | `git diff` vazio; o expurgo só remove, nunca renomeia |
| Mesmo conteúdo, mesma chave — e a chave é o que circula entre requisições | `domain.md#3.5` | `git diff` vazio; `PARIDADE 100 %` |
| Arquivo com a mesma chave já existente **não é reescrito** | `domain.md#3.5` | `git diff` vazio; nenhum arquivo de `src/uploads` mudou de `sha256` |
| Teto de corpo de 16 MB com HTTP 413 em português | `domain.md#3.5` | `git diff` vazio em `src/` |
| A pasta é resolvida **uma vez, no import**, ancorada no arquivo do app, com a variável sobrepondo | `upload-gedcom/contracts.md#2.2` | `git diff` vazio; 36 entradas conferidas dentro do contêiner depois da recriação |
| A aplicação **nunca** apaga arquivo enviado | `upload-gedcom/contracts.md#2.2`; `state-machines.md#5` | `git diff` vazio; o expurgo é ferramenta separada, por manifesto revisável, com simulação |
| A referência do formulário sustenta a continuidade entre requisições | `upload-gedcom/contracts.md#3` | `PARIDADE 100 %`; nenhuma mudança de contrato HTTP |
| A validação do GEDCOM é de conteúdo (`0 HEAD`), não de extensão | `domain.md#3.5` | `git diff` vazio em `src/` |
| A superfície HTTP é a mesma: rota, campos, status e mensagens | `openapi/index.yaml`; `user-stories/` | `git diff` vazio em `src/` |

## 4. Modificadas

**Nenhuma regra de domínio.** O que mudou é contrato de **operação** e o **delta de dados**, listados
na tabela do §1: o ponto de montagem da composição, a localização declarada dos arquivos, o papel da
variável de ambiente e a existência de três cópias de arrasto no repositório. O padrão do código
permanece `<diretório do app>/uploads`, o que mantém toda afirmação da extração sobre o armazenamento
ainda correta.

A consequência para a extração é, de novo, **subtrativa em relação ao adendo 010**: dos 13 impactos que
aquele adendo declarou, 9 deixam de valer e 4 permanecem (a ferramenta de manutenção, o invólucro de
paridade, a linha da variável na tabela de configuração e o expurgo por manifesto). A convergência disso
em `_reversa_sdd/addenda/` é trabalho do `/reversa-sync` — a linha de vigência do adendo 010 passa a
dizer **o que continua valendo**, e não um "superado" genérico que apagaria a distinção.

# Adendo — renomear a raiz de código de `analisador-genealogico/` para `src/`

> Identificador da feature: `003-renomear-pasta-app-para-src`
> Data: `2026-10-03`
> Cenário: **legado** (âncora em `_reversa_sdd/architecture.md` + `_reversa_sdd/domain.md`)
> Veredito: **`spec-desatualizada`**
> Não existe versão anterior deste contrato.

## Vigência

Vigente desde 2026-10-03. **Não edita nenhuma spec original.** Declara que a raiz de código do sistema mudou de nome e que, por isso, toda citação de caminho nas specs da extração deve ser lida com o novo prefixo.

## Por que as specs estão desatualizadas

As specs foram escritas entre 2026-08-03 e 2026-09-30, quando a raiz de código se chamava `analisador-genealogico/`. A feature 003 renomeou essa raiz para `src/` por decisão do usuário, registrada em `_reversa_forward/003-renomear-pasta-app-para-src/requirements.md`, sessão de esclarecimentos de 2026-10-02.

A extração cita o caminho antigo em aproximadamente 259 pontos de documentação. Nenhum deles foi reescrito: por decisão do projeto (RN-03 do roadmap da feature), registro de extração se corrige por adendo, nunca por edição do texto original. Este adendo é essa correção.

## O que passa a valer

### 1. Regra de leitura única

**Toda citação de `analisador-genealogico/...` nas specs da extração deve ser lida como `src/...`.** Vale para árvores de diretório, tabelas de pontos de entrada, comandos de exemplo, referências de arquivo e linha, e caminhos em diagramas.

**A única exceção** são as citações ao commit congelado `e43ca22` e às URLs da API do GitHub com `?ref=`. Naquele commit a raiz realmente se chamava `analisador-genealogico/`, e o caminho histórico está correto. Isso vale, nominalmente, para:

- `_reversa_sdd/oracle/ORACLE_MANIFEST.md` — as linhas que citam `git show e43ca22:analisador-genealogico/app.py` e `git diff --stat e43ca22 HEAD -- analisador-genealogico/app.py`
- `_reversa_sdd/oracle/run_oracle.py` — a linha do comando `git show e43ca22:...`
- `_reversa_sdd/oracle/RECUPERACAO-20260929.md` — as URLs com `contents/analisador-genealogico/app.py?ref=e43ca22...`

### 2. O conteúdo da raiz nova

A raiz `src/` reúne o pacote de runtime:

| Caminho | Situação |
|---|---|
| `src/app.py` | camada de rota, sem alteração de conteúdo |
| `src/reconstructed/` | pacote do núcleo, com os mesmos 12 arquivos e os mesmos nomes de módulo |
| `src/templates/index.html` | inalterado |
| `src/uploads/` | pasta de upload; 9 arquivos de dados reais, não versionados |

`requirements.txt` passou para a **raiz do repositório**. `pytest.ini` e `pyrefly.toml` já estavam nela; o `search-path` do analisador estático passou a apontar para `src`.

### 3. Artefatos extintos

| Artefato | Situação | Efeito nas specs |
|---|---|---|
| `analisador-genealogico/README.md` (README herdado do módulo, em inglês) | **removido** | A dívida técnica nº 9 de `architecture.md#5` e a nota de `dependencies.md#4` descrevem um arquivo que não existe mais. Ambas ficam sem objeto. |
| `analisador-genealogico/.gitignore.txt` | **removido** | Não era citado como contrato; a única regra exclusiva apontava para artefato que o projeto deixou de gerar. |
| `analisador-genealogico/static/` | **removido** (diretório vazio) | Já registrado como inexistente por `inventory.md#2`; a remoção apenas consuma o registro. |

### 4. O contrato de upload permanece idêntico

A pasta de upload mudou de lugar junto com o código, e **nada mais mudou**: a chave de armazenamento continua derivada do conteúdo, o arquivo recusado continua não indo para o disco, e escrita e leitura continuam ancoradas no arquivo do aplicativo — não no diretório corrente. O adendo `bug-BUG-20260929-QMLY-v001` segue vigente e integralmente aplicável.

## Delta por seção alvo

| Locator | Como deve ser lido agora |
|---|---|
| `inventory.md#2` | A árvore do projeto: a raiz de código é `src/`; `requirements.txt` está na raiz do repositório; o README herdado e o arquivo de ignore do módulo não existem |
| `inventory.md#4` | Pontos de entrada: `src/app.py`; `pyrefly.toml` com `search-path = ["src"]`; `pytest.ini` inalterado |
| `inventory.md#3` | A tabela de módulos por arquivo: mesmo conteúdo, prefixo `src/` |
| `architecture.md#1` | As duas camadas continuam as mesmas e continuam no mesmo diretório — que agora se chama `src/`. Os quantitativos de linha citados (84 e 1117) são os de 2026-09-30 e **já estavam desatualizados antes desta feature**: o `app.py` tem 166 linhas desde a correção do BUG-QMLY, e o núcleo foi dividido por responsabilidade. |
| `architecture.md#3.3` | A pasta de upload é `src/uploads/`. A coluna "Onde" cita `UPLOAD_FOLDER`, símbolo que **não existe mais** no módulo do núcleo: ele migrou para o arquivo de entrada, e a resolução da pasta é feita por função ancorada no próprio arquivo |
| `architecture.md#5` | Dívida 9 perde o objeto (o README herdado foi removido). As dívidas 4 e 6 também estavam desatualizadas por outros motivos, alheios a esta feature: o upload passou a ter validação e teto, e existe um fluxo de publicação no repositório |
| `architecture.md#6` | A instrumentação de desenvolvimento continua fora do runtime; os scripts que resolvem a raiz de código foram atualizados e a paridade segue em 100% |
| `code-analysis.md#1` e demais seções | Mesmo mapa de dependências, prefixo `src/`. As referências de arquivo e linha continuam válidas para os módulos do núcleo, cujo conteúdo e numeração não mudaram |
| `domain.md#4.1` | As mensagens de contrato do núcleo permanecem **literais**; só o prefixo do caminho muda |
| `domain.md#7 (ADR-02)` | A decisão de promover os módulos para dentro da raiz de código continua válida; o diretório de destino é agora `src/reconstructed/` |
| `dependencies.md#1` | O arquivo de dependências está na raiz do repositório |
| `dependencies.md#4` | A nota sobre o README herdado anunciar a biblioteca abandonada perde o objeto: o arquivo foi removido |
| `parity_harness.md` | Os comandos de exemplo continuam válidos; o candidato avaliado passou a ser `src/reconstructed/` |
| `screens/golden/manifest.yaml` | A citação ao comando do oráculo, se ainda apontar para o caminho antigo, deve ser lida com o prefixo `src/` |
| `oracle/ORACLE_MANIFEST.md` | Só as citações ao commit `e43ca22` mantêm o caminho histórico; as demais seguem a regra de leitura única |
| `addenda/001`, `002`, `003` e `bug-*-v001/v002` | Já marcados como superados ou vigentes por seus próprios assuntos; nenhum é reescrito por este adendo |

## O que este adendo não altera

| Item | Situação |
|---|---|
| O núcleo de parsing, matching, caminho e renderização | **Intocado.** Nenhum nome de módulo mudou; nenhuma linha de importação do núcleo foi tocada; paridade medida em 100% depois da mudança |
| O contrato de mensagens ao usuário | Intocado e literal |
| A superfície HTTP | Intocada: rota única, mesmo despacho por campo de ação |
| O estado global de processo | Intocado (é o `BUG-20260929-BJJH`, trabalho de outra onda) |
| O comportamento do upload | Intocado, incluindo a chave derivada do conteúdo |
| O diretório de dados legado na raiz do repositório | **Intocado por decisão explícita do usuário** |
| As specs originais, os adendos anteriores e o registro de bugs e refatoração | Nenhum é editado |
| O fluxo de publicação do mini-site | Fora do escopo desta feature; o mini-site ainda cita o caminho antigo até ser regenerado |

## Evidências

Em `_reversa_forward/003-renomear-pasta-app-para-src/evidence/`:

- `gate0-suite-antes.txt` e `gate1-suite-depois.txt` — suíte **idêntica** antes e depois: 118 aprovados e 15 erros de diretório temporário do ambiente, sem teste removido ou desabilitado (RF-06)
- `gate0-paridade-antes.txt` e `gate2-paridade-depois.txt` — **PARIDADE 100%, zero divergência** nas 6 fixtures, nos dois estados (RF-07)
- `upload-antes.txt` e a conferência de T005 — 9 arquivos e 16.920.784 bytes, antes e depois (RF-08)
- `varredura-residual.txt` — 2 ocorrências no conjunto vivo, **ambas exceções declaradas**, zero inesperadas (RF-02)
- `versionamento.txt` — nenhum arquivo de dado real no estado do versionamento, e confirmação de que a regra de ignore alcança `src/uploads/` (RF-08)
- `aplicacao-t009-t014.txt` e os transformadores `apply-path-updates.py` e `verificar-residual.py` — registro reproduzível de exatamente o que foi transformado

## Fontes

- `_reversa_forward/003-renomear-pasta-app-para-src/requirements.md`
- `_reversa_forward/003-renomear-pasta-app-para-src/roadmap.md`
- `_reversa_forward/003-renomear-pasta-app-para-src/actions.md`
- `_reversa_forward/003-renomear-pasta-app-para-src/audit/cross-check.md`
- `_reversa_sdd/inventory.md`, `architecture.md`, `code-analysis.md`, `domain.md`, `dependencies.md`
- `.reversa/principles.md` (princípios I, II e III)
- `_reversa_sdd/addenda/bug-BUG-20260929-QMLY-v001.md` (vigente)

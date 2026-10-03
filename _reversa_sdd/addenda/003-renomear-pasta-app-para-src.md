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

## Atualização 2026-10-03

> **Sincronização parcial.** A feature tem 21 ações previstas e 20 concluídas. A ação `T021` — regeneração do mini-site de documentação — permanece aberta e será complementada em reexecução futura. Decisão do usuário nesta data, entre sincronizar parcialmente, aguardar o fechamento ou tratar de outro modo.
>
> O conteúdo acima, publicado pelo ciclo de codificação, **não foi alterado**. Esta seção acrescenta o delta do que está entregue, no formato canônico da sincronização.

### Impacto por artefato da extração

| Artefato | Seção | Tipo de impacto | Delta |
|----------|-------|-----------------|-------|
| `_reversa_sdd/architecture.md` | `#1` (visão geral e camadas) | `regra-alterada` | As duas camadas continuam as mesmas e continuam no mesmo diretório, que agora se chama `src/`. Os quantitativos de linha citados já estavam desatualizados antes desta feature |
| `_reversa_sdd/architecture.md` | `#3.3` (estruturas de runtime) | `regra-alterada` | A pasta de upload é `src/uploads/`. A coluna "Onde" cita um símbolo que não existe mais no módulo do núcleo: ele migrou para o arquivo de entrada, e a pasta passou a ser resolvida por função ancorada no próprio arquivo |
| `_reversa_sdd/architecture.md` | `#5` (dívidas técnicas) | `regra-removida` | A dívida 9 perde o objeto: o README herdado do módulo, que ela descrevia como desatualizado, foi removido. As dívidas 4 e 6 também estavam desatualizadas, por motivos alheios a esta feature |
| `_reversa_sdd/architecture.md` | `#6` (resumo para o Reversa) | `regra-alterada` | A instrumentação de desenvolvimento continua fora do runtime; os scripts que resolvem a raiz de código foram atualizados e a paridade foi remedida em 100% |
| `_reversa_sdd/inventory.md` | `#2` (árvore de diretórios) | `regra-alterada` | A raiz de código é `src/`; `requirements.txt` está na raiz do repositório |
| `_reversa_sdd/inventory.md` | `#2` (árvore de diretórios) | `componente-extinto` | O README herdado do módulo não existe mais |
| `_reversa_sdd/inventory.md` | `#2` (árvore de diretórios) | `componente-extinto` | O arquivo de ignore do módulo não existe mais |
| `_reversa_sdd/inventory.md` | `#2` (árvore de diretórios) | `componente-extinto` | O diretório vazio de artefatos estáticos não existe mais |
| `_reversa_sdd/inventory.md` | `#4` (pontos de entrada) | `regra-alterada` | O ponto de entrada é `src/app.py` e a configuração do analisador estático passou a apontar para `src` |
| `_reversa_sdd/code-analysis.md` | `#1` e demais seções de componente | `regra-alterada` | Mesmo mapa de dependências e mesmas responsabilidades, com o prefixo `src/`. As referências de arquivo e linha dos módulos do núcleo seguem válidas, porque nenhum nome de módulo mudou |
| `_reversa_sdd/domain.md` | `#4.1` (contrato de mensagens do núcleo) | `regra-alterada` | Nenhuma mensagem muda: elas permanecem literais. Apenas o prefixo de caminho das citações de origem |
| `_reversa_sdd/domain.md` | `#7` (ADR-02) | `regra-alterada` | A decisão de promover os módulos para dentro da raiz de código continua válida; o diretório de destino é agora `src/reconstructed/` |
| `_reversa_sdd/dependencies.md` | `#1` (gerenciador de pacotes) | `regra-alterada` | O arquivo de dependências está na raiz do repositório, e não mais dentro da raiz de código |
| `_reversa_sdd/dependencies.md` | `#4` (dependências removidas) | `regra-removida` | A nota de que o README herdado anunciava a biblioteca abandonada perde o objeto: o arquivo foi removido |
| `_reversa_sdd/migration/parity_harness.md` | comandos de exemplo | `regra-alterada` | Os comandos seguem válidos; o candidato avaliado passou a ser `src/reconstructed/` |
| `_reversa_sdd/screens/golden/manifest.yaml` | citação ao comando do oráculo | `regra-alterada` | Se ainda citar o caminho antigo, deve ser lida com o prefixo `src/` |
| `_reversa_sdd/oracle/ORACLE_MANIFEST.md` | citações de caminho | `regra-alterada` | Somente as citações ao commit congelado mantêm o caminho histórico; as demais seguem a regra de leitura única |
| `_reversa_sdd/oracle/run_oracle.py` | caminhos atuais | `regra-alterada` | Os caminhos atuais foram atualizados; a linha que emite o comando contra o commit congelado foi preservada de propósito, porque aquele commit não tem `src/` |

### Regras sob vigilância

`W001`, `W002`, `W003`, `W004` e `W005` — definidos em `_reversa_forward/003-renomear-pasta-app-para-src/regression-watch.md`.

O watch principal cobre cinco condições estruturais estabelecidas por esta feature: o nome da raiz de código e a identidade do pacote do núcleo (`W001`), a posição do arquivo de dependências (`W002`), a resolução da pasta de upload ancorada no arquivo do aplicativo (`W003`), a ausência dos três artefatos extintos (`W004`) e a permanência da paridade e do conjunto de testes (`W005`).

### Pendência declarada

A regeneração do mini-site de documentação (`T021`) não foi executada. Enquanto ela não rodar, o site derivado continua citando o caminho antigo. A pendência está registrada como observação `O4` no `regression-watch.md` e não afeta código, testes nem paridade.

### Fontes

- `_reversa_forward/003-renomear-pasta-app-para-src/legacy-impact.md` (fonte principal do delta)
- `_reversa_forward/003-renomear-pasta-app-para-src/regression-watch.md`
- `_reversa_forward/003-renomear-pasta-app-para-src/requirements.md`
- `_reversa_forward/003-renomear-pasta-app-para-src/progress.jsonl` (20 ações concluídas de 21)
- `_reversa_forward/003-renomear-pasta-app-para-src/actions.md`

## Atualização 2026-10-03 (rodada 2)

> **Sincronização parcial, a segunda na mesma data.** A ação `T021` continua aberta em `actions.md`, e a decisão desta rodada, tomada pelo usuário, foi sincronizar mesmo assim. O conteúdo acima **não foi alterado**: esta seção apenas acrescenta o delta, no formato canônico da sincronização.

> **O delta desta seção não é entrega da feature 003.** A entrega da feature não mudou desde a seção anterior: o `legacy-impact.md` dela está idêntico ao que gerou aquele texto. O que mudou foi a **árvore que este adendo descreve**, alterada depois daquela sincronização por sete transformações do time Code Quality, registradas em `_reversa_refactor/pacote-reconstructed/`. Essas transformações não passaram pelo ciclo forward e por isso não têm `legacy-impact.md` próprio: o registro de cada uma está no `transformation.md` da pasta dela.

### Por que este adendo estava defasado

O adendo afirma, em cinco lugares, que o pacote do núcleo é `src/reconstructed/`. Esse diretório **não existe mais**. A sequência que o esvaziou foi:

| Transformação | O que mudou na árvore |
|---|---|
| `OPP-20261003-TWNT` | `upload.py` deixou de existir: virou `gedcom_state.py` mais `gedcom_parser.py` |
| `OPP-20261003-DWJC` | `dna_analysis` passou a importar os provedores diretos, e não a fachada |
| `OPP-20261003-RGKA` | a tabela de cM e a tradução para parentesco saíram para `core/cm_estimator.py` |
| `OPP-20261003-LMAY` | `domain.py` virou `text_cleaning.py` |
| `OPP-20261003-GUE7` | os módulos planos passaram a `parsers/`, `core/` e `reporting/` |
| `OPP-20261003-RAIZ` | os cinco módulos soltos foram para `core/` e `utils/` |
| `OPP-20261003-FLAT` | o nível `reconstructed/` foi apagado: o núcleo virou pacotes de primeiro nível em `src/` |

A árvore de hoje, para leitura direta, é: `src/app.py` mais `src/parsers/` (dois leitores), `src/core/` (oito módulos), `src/reporting/` (um módulo) e `src/utils/` (dois utilitários), com 17 módulos no total, mais `templates/` e `uploads/`.

### Impacto por artefato da extração

| Artefato | Seção | Tipo de impacto | Delta |
|---|---|---|---|
| `_reversa_sdd/inventory.md` | `#2` (Estrutura de Árvore de Diretórios) | `componente-extinto` | O diretório `src/reconstructed/` deixou de existir, e com ele o nível de pacote que a árvore do adendo descreve |
| `_reversa_sdd/inventory.md` | `#2` (Estrutura de Árvore de Diretórios) | `componente-novo` | `src/core/`, `src/parsers/`, `src/reporting/` e `src/utils/` são pacotes de primeiro nível; `core/cm_estimator.py` e o subpacote `utils/` são novos em relação ao adendo anterior |
| `_reversa_sdd/inventory.md` | `#2` (Estrutura de Árvore de Diretórios) | `regra-alterada` | A árvore tem 17 módulos, e dois nomes mudaram: `upload.py` não existe, e `domain.py` virou `text_cleaning.py` |
| `_reversa_sdd/inventory.md` | `#4` (Pontos de Entrada) | `presença` | O ponto de entrada continua `src/app.py` e o comando continua `python src/app.py`. Nada muda nesta seção |
| `_reversa_sdd/architecture.md` | `#1` (Visão Geral da Arquitetura) | `regra-alterada` | As duas camadas continuam as mesmas. O que mudou é o mapa de módulos e a fronteira entre eles: o núcleo passou a ser importado por pacotes de primeiro nível a partir de `src/` |
| `_reversa_sdd/architecture.md` | `#5` (Dívidas Técnicas) | `regra-alterada` | A lacuna da fonte das faixas de cM ganhou um primeiro passo: o módulo que guarda a tabela passou a declarar, no próprio arquivo, que as faixas são heurísticas escritas à mão. O princípio V **continua formalmente aberto**, porque não existe referência externa a citar |
| `_reversa_sdd/code-analysis.md` | `#1` e seções de componente | `regra-alterada` | As responsabilidades e a maioria dos nomes de módulo continuam os mesmos. Dois nomes mudaram, um módulo foi extraído, e as referências de arquivo apontam para caminhos com prefixo diferente |
| `_reversa_sdd/domain.md` | `#2.1` (Relação prevista por faixa de cM) | `regra-alterada` | A tabela de nove faixas e a tradução passaram a viver em `core/cm_estimator.py`, com o mesmo contrato de lista. Nenhum valor de faixa mudou |
| `_reversa_sdd/domain.md` | `#2.3` (Matching difuso de nomes) | `regra-alterada` | A autoridade de limpeza de mojibake saiu de `domain.py` para `text_cleaning.py`. A regra é a mesma, e a implementação continua sendo uma só |
| `_reversa_sdd/domain.md` | `#7` (ADR-02) | `regra-alterada` | A decisão de promover os módulos para dentro da raiz de código continua válida. O destino mudou de novo: era `analisador-genealogico/`, passou a `src/reconstructed/` nesta feature, e hoje são os quatro pacotes direto em `src/`, sem nível intermediário |
| `_reversa_sdd/migration/parity_harness.md` | comandos de exemplo | `regra-alterada` | Os comandos seguem válidos. O candidato avaliado passou de `src/reconstructed/` para `src/`, e o instrumento foi ajustado nas transformações |

### Regras sob vigilância

`W001`, `W002`, `W003`, `W004` e `W005`, definidos em `_reversa_forward/003-renomear-pasta-app-para-src/regression-watch.md`.

A condição do `W001` foi **reescrita** nesta data pela `OPP-20261003-FLAT`, porque ela vigiava a identidade do pacote do núcleo como `reconstructed.*`, que deixou de existir. A nova condição vigia o núcleo como `parsers.*`, `core.*`, `reporting.*` e `utils.*`, importados direto de `src/`. Os cinco itens foram reverificados na rodada de codificação de hoje e os cinco estão verdadeiros, incluindo o `W005` (paridade em 100 por cento nas 6 fixtures e suíte com 118 aprovados e 15 erros de ambiente).

### Pendência declarada, agora em dobro

A regeneração do mini-site de documentação (`T021`) continua pendente, e a ela se somou o mesmo motivo: o site derivado cita `analisador-genealogico/` e a árvore de módulos anterior à série de refatoração. Uma única regeneração resolve as duas coisas. A pendência segue registrada como observação `O4` no `regression-watch.md`, e não afeta código, testes nem paridade.

### Fontes

- `_reversa_forward/003-renomear-pasta-app-para-src/legacy-impact.md` (fonte do delta da feature, inalterada nesta rodada)
- `_reversa_forward/003-renomear-pasta-app-para-src/regression-watch.md`
- `_reversa_forward/003-renomear-pasta-app-para-src/progress.jsonl` (20 ações concluídas de 21, mais a linha `blocked` da rodada 2)
- `_reversa_refactor/pacote-reconstructed/generated/index.md` (view do time Code Quality, sete transformações aplicadas)
- os `transformation.md` de cada uma das sete transformações citadas acima

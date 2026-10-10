# Dicionário de Dados — analisador-genealogico

> Nível de documentação: **Completo** (`state.json` → `doc_level`)
> Gerado pelo Reversa-Archaeologist em 2026-10-10 (re-extração). Substitui o dicionário de 2026-10-05.
> Snapshot da versão substituída: `.reversa/snapshots/2026-10-10-pre-reextracao/`
> Escala de confiança: 🟢 CONFIRMADO | 🟡 INFERIDO | 🔴 LACUNA
> Análise que dá contexto a estas estruturas: `code-analysis.md`. Fluxos: `flowcharts/`.

## 1. Como ler este documento

**A afirmação da rodada anterior — "este sistema não tem banco de dados" — deixou de valer.** A feature 008 introduziu PostgreSQL 16 (opcional) para a **persistência histórica da análise**. Os dados continuam existindo em quatro lugares, e cada um tem um dono e um tempo de vida diferente:

| Onde | O que é | Dono | Persiste? |
| --- | --- | --- | --- |
| Memória do processo | A **árvore** do GEDCOM carregado, passada por parâmetro | `parsers/gedcom_parser.py` produz; `core/*` consome | Não — morre com a requisição/processo |
| Disco | Arquivos enviados (`.ged`, `.csv`) sob chave derivada do conteúdo, mais os aposentados | `ports/adaptadores.py` (`ArmazenamentoEmDisco`) | Sim, como arquivo |
| Corpo da requisição/resposta | Formulário e o payload renderizado no template | `app.py` + Jinja2 | Não |
| **PostgreSQL** | **O histórico das análises** — análise, pessoas, conexões, kits, nós de caminho e descartados | `ports/adaptadores.py` (`RegistroDeAnalisesPostgres`) | **Sim, e é opcional** |

**O que a persistência NÃO é.** Ela fica **depois** do processamento e **fora** da decisão: nenhum módulo de `src/core/` conhece o registro, e nenhum fluxo consulta o banco para decidir, completar ou corrigir um resultado (`RN-01`, `RN-12`). Ela responde "o que esta análise concluiu, e por quê" — não produz a resposta.

**A árvore não é duplicada no banco.** Ela continua sendo o arquivo imutável de `src/uploads/`, referenciado por `tree_ref`. O que as tabelas guardam é o **retrato** das pessoas daquela análise, e ele não muda quando a árvore for reimportada.

**Convenção de `None`:** o sistema usa `None` para *não sei / não existe*, e **não** para zero. Onde a distinção importa, ela está anotada campo a campo — é o caso de `totals.cm` com múltiplos kits, de `largest_segment_cm`, de `plausible`, de `age_at_birth` e de `root_person_xref`.

---

## 2. A árvore do GEDCOM em memória

A árvore é uma **tupla de quatro posições**, e é assim que ela entra em **toda** função do núcleo: `arvore = (people, families, graph, child_to_family)`. Ela é produzida por `parsers.gedcom_parser.carregar_arvore(caminho)` e **não existe mais nenhum estado de processo** — `src/core/gedcom_state.py` foi apagado no `T023` da feature 005, e `dna_analysis`/`path_search` recebem a árvore por parâmetro.

| Posição | Nome | Tipo | Confiança |
| --- | --- | --- | --- |
| `arvore[0]` | `people` | `dict[str, registro ged4py INDI]` indexado por `xref_id` (`@I123@`) | 🟢 |
| `arvore[1]` | `families` | `dict[str, registro ged4py FAM]` indexado por `xref_id` (`@F6@`) | 🟢 |
| `arvore[2]` | `graph` | `networkx.Graph` não direcionado e **não** MultiGraph, bipartido pessoa↔família | 🟢 |
| `arvore[3]` | `child_to_family` | `dict[str, list[str]]` — filho → famílias onde aparece como `CHIL` | 🟢 |

> 🟢 **Nenhum campo é convertido em dataclass própria:** os valores de `people` e `families` são os registros crus do ged4py. Todo acesso a dado é por sub-registro (`BIRT`/`DATE`, `SEX`, `FAMC`, `FAMS`, `HUSB`, `WIFE`, `CHIL`).

### 2.1 Acesso aos dados do registro 🟢

| Dado | Como é obtido | Onde |
| --- | --- | --- |
| Nome formatado | `get_name(person)` → `person.name.format()` ou `"Sem Nome"` | `core/registro.py:40-46` |
| Identificador | `ref_id(val)` → `val.xref_id` ou o próprio valor | `core/registro.py:35-37` |
| Data de nascimento | `BIRT` → sub-registro `DATE` | `documentary_relationship.py:102-103` |
| Data de falecimento | `DEAT` → sub-registro `DATE` | `documentary_relationship.py:106-107` |
| Ano de uma data | `parse_year` — primeiro ano de 3 ou 4 dígitos | `documentary_relationship.py:76-87` |
| Sexo | sub-registro `SEX` | `documentary_relationship.py:151` |
| Local de nascimento | `BIRT` → sub-registro `PLAC` | `documentary_relationship.py:110-119` |
| Famílias como filho | sub-registros `FAMC` | `documentary_relationship.py:126-127` |
| Famílias como cônjuge | sub-registros `FAMS` | `family_navigation.py:87` |
| Pais | `FAMC` e, sem ele, `child_to_family` | `family_navigation.py:52-72` |
| Filhos | varredura de **todas** as famílias | `documentary_relationship.py:130-143` |

> 🟢 **`get_name` devolve string VAZIA quando o registro tem `Name` mas o formato resulta vazio.** Isso **ocorre em dado real**: **301** pessoas em 35.460 em `Arvore_Unificada_Oficial_V1_2.ged`, medido em 2026-10-10 nas **três** cópias da árvore (a de `src/uploads/` e as duas de `_aposentados/`); 17 em 3.056 em `Adriano_Santos.ged`. ⚠️ **O número 296 que circulava era de outra grandeza:** é a contagem de pessoas **divergentes do `DIV-001`** medida pelo harness de paridade em 2026-09-28 (`migration/parity_harness.md`), e não a contagem de nomes vazios do código atual. O literal `Sem Nome` só aparece quando o registro **não tem** `name`, e é inalcançável a partir de um `INDI` real — remover a tag `NAME` não produz `person.name is None`, porque o ged4py ainda entrega um objeto `Name` cujo `.format()` é `''`. Não "melhorar": o corpo é cópia **literal** do oráculo congelado (`DIV-001`).

### 2.2 O grafo 🟢

| Propriedade | Valor |
| --- | --- |
| Nós de pessoa | id da pessoa; atributos `label` (nome formatado) e `type="person"` |
| Nós de família | id da família; atributos `label="Familia"` e `type="family"` |
| Arestas | pessoa↔família, para `HUSB`, `WIFE` e cada `CHIL` existente no grafo |
| A ordem de inserção | **contrato de paridade** (tag `@ordem`): ela decide qual caminho o `nx.shortest_path` devolve quando há mais de um de mesmo comprimento |
| Substituição | o grafo é um **valor** da tupla; não há mais reatribuição de global, e nenhum import tardio |

### 2.3 O cache de nomes e a chave de invalidação 🟡

`documentary_relationship._INDICE_DE_NOMES` é um cache **de módulo**: `{nome normalizado: [ids]}`. A varredura de 35 mil pessoas custa ~0,9 s, e o fluxo de DNA (71 nomes distintos no arquivo real) pagava isso 71 vezes.

| Campo | Tipo | Descrição |
| --- | --- | --- |
| `chave` | `tuple` | Chave de invalidação: `(len(people), chaves[0], chaves[-1])` com `chaves = sorted(people)` |
| `mapa` | `dict[str, list[str]]` | nome normalizado (sem acento, após `demojibake`) → ids |

> 🟡 **A chave pode não invalidar entre duas árvores diferentes.** Dois GEDCOMs com o **mesmo número de pessoas** e os **mesmos xrefs extremos** produzem a mesma chave, e o mapa da árvore anterior é reaproveitado. O cenário é provável entre dois exports do mesmo exportador, que numeram de forma contígua. Consequência: o dossiê de homônimos passa a listar xrefs de outra árvore, **sem exceção** — `person_summary` degrada em silêncio. Achado registrado em `flowcharts/busca-caminho.md` §13. O `id()` do dicionário **não** serve como chave: ele é reciclado, e o próprio código explica por quê.

---

## 3. Armazenamento dos arquivos enviados

### 3.1 Nome do arquivo em disco 🟢

Forma: **`<16 hexadecimais>__<nome visível>`**.

| Parte | Origem | Regra |
| --- | --- | --- |
| Chave (16 hex) | `sha256(conteudo)[:16]` | Derivada do **conteúdo**: mesmo conteúdo → mesma chave. Estável entre requisições, porque o formulário devolve o valor no POST seguinte. |
| Separador | literal `__` | Fixo. |
| Nome visível | nome enviado pelo cliente, saneado | `/`, `\` e NUL viram `_`; espaços e acentos preservados; a extensão original é preservada; nome vazio ou só pontos → `arvore.ged`; sem extensão → recebe `.ged`. |

> 🟢 **A validação da referência recebida é por FORMA, e a forma foi afrouxada em 2026-10-10.** O alfabeto fechado `^[0-9a-f]{16}__[A-Za-z0-9._-]+$` recusava acento e espaço, que o **gravador preserva de propósito** (`RF-06`): três arquivos com acento e um com espaço estavam inalcançáveis, e a tela dizia que não existiam (`BUG-20261009-6RKP` / `RN-20`). Hoje a defesa é a exigência de que a referência seja um **NOME** — sem barra, barra invertida, NUL, `.` ou `..`, e `basename` de si mesma. `aposentar` usa o critério mais permissivo (`referencia_de_arquivo_da_pasta`); `resolver` continua exigindo a chave de conteúdo.

### 3.2 Pasta de upload e pasta de aposentados 🟢

| Item | Valor | Descrição |
| --- | --- | --- |
| Caminho padrão | `<diretório do app>/uploads` | Ancorado no arquivo do app, e não no diretório corrente: escrita e leitura usam o **mesmo** caminho, sempre. |
| Variável de ambiente | `ANALISADOR_UPLOAD_FOLDER` | Sobrepõe o padrão; usada pelos testes para não escrever na pasta real. |
| Subpasta de aposentados | `_aposentados` | `PASTA_DE_APOSENTADOS`. Fica **dentro** da pasta de upload de propósito: `listar` já ignora subdiretório, então o arquivo sai da lista sem que nenhum filtro novo precise existir. |
| Colisão no aposentado | sufixo `.1` … `.99` | Se já existe um aposentado com o mesmo nome, um sufixo numérico é acrescentado; esgotadas as 99 tentativas, a operação **desiste** em vez de sobrescrever. |

### 3.3 Entrada da listagem (`EntradaArmazenada`) 🟢

`ports/__init__.py:196-216`. É o **retrato do diretório**, e não o arquivo: nenhum campo exige abrir o conteúdo.

| Campo | Tipo | Obrigatório | Descrição |
| --- | --- | --- | --- |
| `nome` | `str` | sim | O **nome armazenado** (`<16 hex>__<nome visível>`) — é ele que o formulário devolve e o resolvedor aceita |
| `bytes` | `int` | sim | `os.stat().st_size` |
| `modificado_em` | `float` | sim | `os.stat().st_mtime`, em segundos desde a epoch. A ordem da lista é por ele, decrescente |

> 🟢 **A ordem é por data porque o nome exibido não é único:** medido, há **três** arquivos chamados `Arvore_Unificada_Oficial_V1_2.ged` na pasta real.

### 3.4 Formulário entre requisições 🟢

| Campo | Tipo | Obrigatório | Descrição |
| --- | --- | --- | --- |
| `action` | `str` | sim | `upload_gedcom`, `aposentar_arquivo`, `selecionar_arvore`, `dna_analysis` ou `path_search` |
| `gedcom_filename` | `str` | sim nos fluxos pós-upload | Nome armazenado da árvore; validado por forma antes de virar caminho |
| `arquivo_a_aposentar` | `str` | sim em `aposentar_arquivo` | Nome armazenado a mover para `_aposentados/` |
| `matches_csv_filename` | `str` | **não** | Referência do CSV escolhido na **lista**; tem precedência sobre o arquivo enviado |
| `person1_name` / `person2_name` | `str` | sim em `path_search` | Nomes consultados (recebem `strip`) |
| `root_name` | `str` | sim em `dna_analysis` | Nome da pessoa raiz |
| `gedcom` | arquivo | sim em `upload_gedcom` | Arquivo GEDCOM |
| `matches_csv` | arquivo | sim em `dna_analysis` **quando** `matches_csv_filename` não vem | CSV de matches |

---

## 4. CSV de matches

### 4.1 Colunas reconhecidas por papel 🟢

A detecção é por papel, tolerando variação de cabeçalho. A comparação ignora maiúsculas e espaços nas pontas.

| Papel | Nomes aceitos | Obrigatório | Onde |
| --- | --- | --- | --- |
| Nome | `Name`, `MatchedName`, `Nome` | **sim** | `csv_ingest.py:186-188`, `genetic_evidence.py:63` |
| cM | `cM`, `TotalCM`, `Total cM` | **sim** | idem |
| SNPs | `SNPs`, `SNP`, `SNPs Count` | não | `genetic_evidence.py:65` |
| Cromossomo | `Chromosome`, `Chr`, `Cromossomo` | não | `genetic_evidence.py:66` |
| Início | `Start`, `Start Location`, `Posicao inicial` | não | `genetic_evidence.py:67` |
| Fim | `End`, `End Location`, `Posicao final` | não | `genetic_evidence.py:68` |
| Fonte | `Source`, `Fonte`, `Company` | não | `genetic_evidence.py:69` |
| ID de match | primeira coluna com >30 % dos valores casando `[A-Z]{2}\d{7}` | não | `csv_ingest.py:191-193` |
| E-mail | a **última** coluna cujo nome contém `mail` | não | `genetic_evidence.py:70`, `csv_ingest.py:194-195` |
| Kit | coluna cujo **nome** casa `kit\|gedmatch\|teste\|test\b` e >50 % dos valores casam `[A-Z]{1,3}\d{4,8}`; senão, coluna com >30 % em `[A-Z]{2}\d{7}` | não | `genetic_evidence.py:72-82` |

### 4.2 Atributos de leitura (`df.attrs`) 🟢

Canal escolhido porque a assinatura de `read_csv_with_fallback` é contrato: trocar o retorno por tupla quebraria `dna_analysis` e o `__all__` que a reexporta.

| Atributo | Tipo | Padrão | Descrição |
| --- | --- | --- | --- |
| `separador` | `str` | `","` | Separador efetivamente usado (`,` `;` TAB `\|`) |
| `encoding` | `str` | `"utf-8"` | Encoding que funcionou (`utf-8` ou `latin-1`) |
| `linhas_antes_do_cabecalho` | `int` | `0` | Quantas linhas de preâmbulo foram puladas |
| `linhas_ignoradas` | `list[int]` | `[]` | Números (**1-based**) das linhas com número de campos diferente do cabeçalho, **depois** do cabeçalho |
| `erro_de_leitura` | `str \| None` | `None` | Texto do erro de tokenização do pandas, quando houve releitura |

### 4.3 `_group_key` (coluna temporária) 🟢

| Campo | Tipo | Descrição |
| --- | --- | --- |
| `_group_key` | `str` | `norm_name(demojibake(nome))` + `" \| "` + cauda, onde a cauda é o id em maiúsculas, ou o e-mail normalizado, ou nada. É a chave de soma dos cM na função de agregação legada. |

> ⚠️ **`_group_key` NÃO é a chave da evidência genética.** A agregação legada (`aggregate_matches`, mantida por compatibilidade e injetada pela borda) usa `_group_key`; o caminho que o fluxo realmente percorre é `build_genetic_evidence`, cuja chave é o par **(nome normalizado, kit)** — ver §5.1. As duas coexistem, e a diferença é justamente o que impede a soma entre kits.

---

## 5. Evidência genética

### 5.1 Evidência por (nome normalizado, kit) 🟢

Chave externa: `evidencias[nome_normalizado][chave_kit]`. **Duas linhas do CSV com o mesmo nome e kits diferentes são duas evidências, não uma.**

| Campo | Tipo | Obrigatório | Padrão | Descrição |
| --- | --- | --- | --- | --- |
| `kit` | `str \| None` | não | `None` | Kit de origem, em maiúsculas; `None` quando o CSV não traz kit nem e-mail |
| `person_name_csv` | `str` | sim | — | Nome como veio do CSV, já com mojibake corrigido |
| `source` | `str \| None` | não | `None` | Fonte declarada (empresa/laboratório); **primeira** não vazia encontrada |
| `total_cm` | `float` | sim | `0.0` | Soma dos segmentos **sem arredondamento** |
| `segments` | `list[dict]` | sim | `[]` | Segmentos individuais (§5.2) |
| `records_used` | `int` | sim | `0` | Quantas linhas do CSV entraram nesta evidência |
| `segment_count` | `int` | sim | `0` | Número de segmentos |
| `largest_segment_cm` | `float \| None` | não | `None` | Maior segmento; `None` quando nenhum segmento tem cM numérico |
| `snps_total` | `int \| None` | não | `None` | Soma de SNPs; `None` quando não há SNPs informados |
| `snps_largest_segment` | `int \| None` | não | `None` | SNPs do maior segmento |
| `chromosomes` | `list[str]` | sim | `[]` | Cromossomos distintos, ordenados por `(len, valor)` |
| `method` | `str` | sim | — | Texto que explica se o total é soma de N linhas ou valor de uma linha |
| `weak_segment` | `bool` | não | *(ausente)* | Presente e `True` quando o maior segmento é menor que 15 cM |

### 5.2 Segmento 🟢

| Campo | Tipo | Obrigatório | Padrão |
| --- | --- | --- | --- |
| `chromosome` | `str \| None` | não | `None` |
| `start` | `int \| None` | não | `None` |
| `end` | `int \| None` | não | `None` |
| `cm` | `float` | sim | `0.0` |
| `snps` | `int \| None` | não | `None` |

Ordenação: `cm` decrescente, com os `None` por último.

### 5.3 Aviso 🟢

| Campo | Tipo | Descrição |
| --- | --- | --- |
| `code` | `str` | `multiplos_kits`, `kit_ausente`, `segmento_fraco`, `sem_evidencia` |
| `message` | `str` | Texto em português, exibido ao operador |

### 5.4 Evidência consolidada de uma pessoa (`evidence_for`) 🟢

| Campo | Tipo | Padrão | Descrição |
| --- | --- | --- | --- |
| `available` | `bool` | `False` | Há evidência genética para a pessoa? |
| `source` | `str \| None` | `"fonte não identificada no CSV"` | Fonte do kit principal |
| `kits` | `list[dict]` | `[]` | Kits separados, ordenados por cM decrescente. **Nunca somados** |
| `totals.cm` | `float \| None` | `None` | **`None` quando há mais de um kit** — é o número honesto quando não se sabe qual kit é a pessoa do GEDCOM |
| `totals.cm_por_kit` | `dict[str, float]` | `{}` | cM por kit; chave ` SEM-KIT` (com espaço) quando não informado |
| `totals.segments` | `int` | `0` | Soma de segmentos de todos os kits |
| `totals.largest_segment_cm` | `float \| None` | `None` | Maior segmento entre os kits |
| `totals.chromosomes` | `list[str]` | `[]` | União dos cromossomos |
| `totals.records_used` | `int` | `0` | Soma das linhas usadas |
| `warnings` | `list[dict]` | `[]` | Avisos do kit + avisos recebidos |

---

## 6. Possibilidades e confronto

### 6.1 Bloco de hipótese por kit (`possible_relationships`) 🟢

| Campo | Tipo | Obrigatório | Padrão | Descrição |
| --- | --- | --- | --- | --- |
| `total_cm` | `float \| None` | não | `None` | Valor avaliado; `None` quando não há cM utilizável |
| `possible_relationships` | `list[dict]` | sim | `[]` | **Sempre lista**, inclusive vazia. Nunca um parentesco único |
| `confidence` | `str` | sim | `"indeterminada"` | `indeterminada`, `baixa` ou `muito baixa` — heurística **do projeto** |
| `confidence_note` | `str` | não | — | Explicação da confiança |
| `interpretation` | `str` | sim | — | Leitura em português do que o valor permite e do que não permite concluir |
| `reference` | `dict` | sim | — | `SCP40_META` (§6.3) |
| `kit` | `str \| None` | não | `None` | Kit a que o bloco se refere |
| `segment_count` | `int \| None` | não | `None` | Segmentos do kit |
| `largest_segment_cm` | `float \| None` | não | `None` | Maior segmento do kit |

### 6.2 Linha publicada do Shared cM Project 4.0 🟢

| Campo | Tipo | Descrição |
| --- | --- | --- |
| `key` | `str` | Chave canônica (`PARENT_CHILD`, `SIBLINGS`, `1C1R`, `GREAT_AUNT_1`, `DIRECT_3`, …) |
| `name_en` | `str` | Nome na fonte (`1C1R`, `Half 1C`, …) |
| `name_pt` | `str` | Nome em português exibido na tela |
| `meioses` | `int` | Saltos pai-filho entre as duas pessoas — a grandeza que o cM mede |
| `average` | `int` | Média publicada (a versão 4.0 **não** publica mediana) |
| `range_low` / `range_high` | `int` | Faixa publicada, após remoção de 1 % dos envios (0,5 % em cada ponta) |

**27 linhas publicadas**, e **6 relações declaradamente não publicadas** em `SCP40_NOT_PUBLISHED`: `1C4R`, `1C5R`, `1C6R`, `3C2R`, `DIRECT_4` (2º bisavô/avó) e `DIRECT_5` (3º bisavô/avó). Para elas existe `meioses_window`: a **envoltória** das relações publicadas com o mesmo número de meioses, com a média arredondada — e `None` quando não há nenhuma.

### 6.3 Metadados da fonte (`SCP40_META`) 🟢

| Campo | Valor |
| --- | --- |
| `version` | `4.0` |
| `release` | `março de 2020` |
| `sample_size` | `59714` |
| `range_definition` | Faixa (mínimo–máximo) após remoção de 1 % dos envios — **não** é o intervalo observado completo |
| `sources` | PDF oficial do Shared cM Project 4.0 e a ferramenta do DNA Painter |

### 6.4 Resultado do confronto 🟢

| Campo | Tipo | Padrão | Descrição |
| --- | --- | --- | --- |
| `status` | `str` | `"INCONCLUSIVO"` | `COMPATIVEL`, `POSSIVEL`, `CONFLITANTE`, `INCONCLUSIVO` |
| `label` | `str` | `"Inconclusivo"` | Rótulo em português; **é também nome de classe CSS** no template (`badge estado-{{ status }}`) |
| `message` | `str` | — | Mensagem fixa do estado |
| `causes` | `list[str]` | `[]` | 12 causas em `CONFLITANTE`; 9 em `POSSIVEL`; vazio nos demais |
| `per_kit` | `list[dict]` | `[]` | `{kit, status, cm, note}` por kit — **vazio** quando o confronto termina antes de avaliar kit por kit |
| `method` | `str \| None` | `None` | `scp40:<nome>` ou `scp40:meioses=<n>` — **como** o estado foi decidido |
| `expected_range` | `dict \| None` | `None` | `{low, high, average, label}` da janela esperada |
| `detail` | `str \| None` | `None` | Frase que reúne parentesco documental, janela e a nota de cada kit |
| `observations` | `list[str]` | `[]` | Notas e avisos preservados |

> 🟢 Com mais de um kit, o `status` final é o **mais conservador** na ordem `CONFLITANTE > POSSIVEL > COMPATIVEL > INCONCLUSIVO`, e a nota por kit é registrada.
>
> 🟡 **`INCONCLUSIVO` é o último da ordem:** um kit sem cM utilizável não rebaixa o resultado quando outro kit é `COMPATIVEL`. É escolha declarada no código.

---

## 7. Parentesco documental

### 7.1 Resultado (`documentary_relationship`) 🟢

| Campo | Tipo | Obrigatório | Padrão | Descrição |
| --- | --- | --- | --- | --- |
| `status` | `str` | sim | — | `found`, `ambiguous`, `not_found` ou `affinity` (o último é atribuído por `path_search.py`) |
| `source` | `str` | sim | `"GEDCOM"` | Origem da afirmação |
| `label` | `str` | sim | — | Rótulo legível do parentesco |
| `relationship_key` | `str \| None` | não | `None` | Chave canônica usada para casar com a tabela do Shared cM |
| `meioses` | `int \| None` | não | `None` | Saltos pai-filho entre as duas pessoas |
| `degrees` | `dict \| None` | não | `None` | `{a_up, b_up, cousin_degree, removed}` |
| `person_a` / `person_b` | `dict` | sim | — | Fichas completas (§7.2) |
| `common_ancestor` | `dict \| None` | não | `None` | `{id, name, birth}` |
| `common_ancestors` | `list[dict]` | sim | `[]` | Todos até **12** níveis, no máximo 12 (§7.5) |
| `path` | `dict \| None` | não | `None` | `{ids, names}` — caminho principal |
| `additional_paths` | `list[dict]` | sim | `[]` | Caminhos alternativos, nenhum descartado |
| `evidence` | `list[dict]` | sim | `[]` | Evidência por salto (§7.3) |
| `homonyms` | `dict` | sim | `{}` | Dossiê (§7.4) |
| `ambiguous_identity` | `bool` | sim | `False` | Atalho para `homonyms.ambiguous` |
| `warnings` | `list[dict]` | sim | `[]` | Códigos: `pessoa_ausente`, `sem_caminho`, `homonimo`, `data_impossivel`, `caminhos_multiplos`, `colapso_de_pedigree`, `afinidade` |

### 7.2 Ficha de pessoa (`person_summary`) 🟢

| Campo | Tipo | Obrigatório | Padrão |
| --- | --- | --- | --- |
| `id` | `str` | sim | — |
| `name` | `str` | sim | `"Sem Nome"` quando ausente |
| `sex` | `str \| None` | não | `None` |
| `birth` / `death` | `str \| None` | não | `None` |
| `birth_year` / `death_year` | `int \| None` | não | `None` |
| `birth_place` | `str \| None` | não | `None` |
| `parents` | `list[str]` | sim | `[]` |
| `parent_names` | `list[str]` | sim | `[]` |
| `spouses` | `list[str]` | sim | `[]` |
| `children` | `list[str]` | sim | `[]` |
| `family_as_child` | `list[str]` | sim | `[]` |

### 7.3 Evidência de salto (`hop_evidence`) 🟢

| Campo | Tipo | Padrão | Descrição |
| --- | --- | --- | --- |
| `child_id` / `child_name` / `child_birth` | `str \| None` | — | Filho do salto |
| `parent_id` / `parent_name` / `parent_birth` | `str \| None` | — | Genitor do salto |
| `family_id` | `str \| None` | `None` | Família que sustenta o vínculo |
| `family_husband` / `family_wife` | `dict \| None` | `None` | `{id, name}` do casal declarado |
| `age_at_birth` | `int \| None` | `None` | Idade do genitor no nascimento; `None` sem data |
| `plausible` | `bool \| None` | `None` | `False` fora de 12–70 anos; `None` quando falta data |
| `link_source` | `str` | — | `"FAMC/CHIL do GEDCOM"` ou `"sem registro de familia localizado"` |

### 7.4 Dossiê de homônimos (`homonym_dossier`) 🟢

| Campo | Tipo | Padrão | Descrição |
| --- | --- | --- | --- |
| `query` | `str` | — | Nome consultado |
| `exact_count` | `int` | `0` | Registros com o **mesmo nome normalizado** (sem acento) |
| `exact_matches` | `list[dict]` | `[]` | Fichas dos exatos |
| `similar_count` | `int` | `0` | Candidatos semelhantes informados pelo chamador |
| `similar_matches` | `list[dict]` | `[]` | Até 5 fichas dos semelhantes |
| `ambiguous` | `bool` | `False` | Mais de um exato, **ou** `similar_ids` não vazio |
| `differences` | `list[dict]` | `[]` | `{campo, rotulo}` em que as fichas divergem (só com mais de um exato) |
| `identical_data` | `bool` | `False` | Ambíguo, mas sem nenhuma divergência de dado |

### 7.5 Ancestral comum e caminho alternativo 🟢

| Estrutura | Campos |
| --- | --- |
| Ancestral comum | `id`, `name`, `distance_a`, `distance_b`, `total_meioses`, `birth` |
| Caminho alternativo | `ids`, `names`, `via`, `distance_a`, `distance_b`, `total_meioses`, `ancestor_name` |

---

## 8. Payload do núcleo → tela

Os três fluxos devolvem estruturas **tipadas** na fronteira de aplicação, e nenhuma carrega nome de campo de template (`RF-20`).

### 8.1 Resultado da análise de DNA 🟢

| Campo | Tipo | Descrição |
| --- | --- | --- |
| `match_name` | `str` | Nome do registro do GEDCOM escolhido |
| `csv_name` | `str` | Nome como veio do CSV |
| `cm` | `float` | cM **do kit** — nunca a soma de kits diferentes |
| `kit` | `str \| None` | Kit do match |
| `text_path` | `str` | Caminho documental em texto, separado por seta |
| `mermaid_data` | `str \| None` | Diagrama do caminho documental, ou `None` quando não há caminho |
| `documentary` | `dict` | §7.1 |
| `genetic_evidence` | `dict` | §5.4 |
| `hypotheses` | `list[dict]` | §6.1, uma por kit |
| `comparison` | `dict` | §6.4 |
| `observations` | `list[str]` | Observações **deduplicadas**, na ordem de origem |
| `warnings` | `list[dict]` | Avisos do documental + da evidência |

**Descartado** (§8.2) e **mensagem final** (§8.3): `csv_name`, `kit`, `cm`, `motivo` — o motivo é o **texto do núcleo**, e nunca vazio (`"não encontrado"` é o padrão). A mensagem é `"{N} conexões encontradas. {M} descartadas."`, e os avisos de arquivo (preâmbulo e linhas descartadas) são **anexados à mensagem** quando não há nenhum resultado, porque não há cartão na tela onde eles apareçam.

### 8.2 `ResultadoDeAnalise` — o que o caso de uso devolve 🟢

`src/application/dna_analysis.py:41-57`.

| Campo | Tipo | Padrão | Descrição |
| --- | --- | --- | --- |
| `resultados` | `list` | — | Payload do núcleo, já na ordem de apresentação |
| `descartados` | `list` | — | Matches descartados, com motivo |
| `mensagem` | `str` | — | Mensagem de contrato do núcleo |
| `aviso_de_persistencia` | `str \| None` | `None` | **Único campo** que a feature 008 acrescentou. Nulo significa "nada a avisar" — gravado **ou** persistência desabilitada — e nesse caso a tela não renderiza nada |

### 8.3 `ResultadoDeBusca` e `Desfecho` 🟢

`src/application/path_search.py:32-45` e `src/application/__init__.py:35-57`.

| Campo | Tipo | Descrição |
| --- | --- | --- |
| `desfecho` | `Desfecho` | `RESULTADO`, `SEM_RESULTADO` ou `ERRO_DE_ENTRADA` |
| `dados` | `dict \| None` | Payload do núcleo, **sem renomear nada** dele |
| `mensagem` | `str` | Mensagem de contrato congelada |

**Derivação do desfecho** (a precedência importa): payload presente → `RESULTADO`; sem payload e com sucesso → `SEM_RESULTADO`; sem payload e sem sucesso → `ERRO_DE_ENTRADA`. Nunca do texto da mensagem.

### 8.4 Portas e payloads de persistência 🟢

`src/ports/__init__.py`. Quatro `Protocol` e cinco tipos de dado. As **portas** são consumidas por parâmetro pelos casos de uso; nenhum caso de uso instancia a implementação concreta.

| Porta | Métodos | Implementação |
| --- | --- | --- |
| `ArmazenamentoDeArquivos` | `guardar`, `resolver`, `listar`, `aposentar` | `ArmazenamentoEmDisco` |
| `CarregadorDeArvores` | `carregar` | `CarregadorDeArvoresGedcom` |
| `RepositorioDeArvores` | `guardar`, `obter` | **nenhuma, e sem consumidor** (`D-03`) |
| `RegistroDeAnalises` | `registrar` | `RegistroDeAnalisesPostgres` |

| Tipo de payload | Campos | Papel |
| --- | --- | --- |
| `PessoaDaAnalise` | `xref`, `nome`, `sexo`, `nascimento`, `local_nascimento`, `falecimento`, `completa` | Retrato de UMA pessoa usada na análise. `completa` distingue a ficha inteira (raiz e match) da mera identificação (nós do caminho) |
| `KitDaAnalise` | `ordinal`, `kit`, `source`, `total_cm`, `segment_count`, `largest_segment_cm`, `status`, `status_note` | Metadados de UM kit e o veredito **dele** |
| `ConexaoDaAnalise` | `ordinal`, `csv_name`, `matched_name`, `matched_person_xref`, `comparison_*` (4), `documentary_status`, `total_cm`, `relationship_key`, `relationship_label`, `meioses`, `mrca_xref`, `comparison_method`, `expected_low/high/average`, `causes`, `observations`, `kits`, `caminho` | Uma conexão: documento, genética e confronto |
| `DescartadoDaAnalise` | `ordinal`, `csv_name`, `reason`, `kit`, `total_cm` | Uma conexão descartada, com o motivo **em texto** |
| `AnaliseParaRegistrar` | `tree_ref`, `match_file_ref`, `root_name_input`, `message`, `pessoas`, `conexoes`, `descartados`, `root_person_xref`, `accepted_count`, `skipped_count` | A análise inteira, **já projetada**: dado plano, sem dicionário aninhado |

> 🟢 **`caminho` carrega pares `(xref, papel)`**, e não só identificadores: `match_path_node.role` é `NOT NULL` com domínio fechado, e o núcleo **não** entrega o papel de cada nó. Quem deriva é a projeção, dividindo o caminho no ancestral comum. `afinidade` **nunca** aparece aqui — quem atribui esse estado é `path_search.py`.

---

## 9. Esquema PostgreSQL

`init.sql` (189 linhas), executado pelo **entrypoint** do PostgreSQL, montado em `/docker-entrypoint-initdb.d/`. **Idempotente por requisito** (`RF-12`): tudo usa `IF NOT EXISTS` e **não existe nenhum `DROP`** no arquivo, porque um `DROP` no topo apagaria o histórico — que é o propósito da feature.

### 9.1 `dna_analysis` — a análise

| Coluna | Tipo | Restrições | Descrição |
| --- | --- | --- | --- |
| `analysis_id` | `UUID` | PK, `DEFAULT gen_random_uuid()` | `gen_random_uuid()` é nativo desde o PostgreSQL 13, então não há `CREATE EXTENSION pgcrypto` |
| `owner_id` | `TEXT` | `NOT NULL` | O `dono`. **Sem FK e sem índice de escopo** (`RN-10`) |
| `tree_ref` | `TEXT` | `NOT NULL` | Chave de conteúdo + nome visível do GEDCOM |
| `match_file_ref` | `TEXT` | `NOT NULL` | Idem, para o CSV |
| `root_name_input` | `TEXT` | `NOT NULL` | O que o operador digitou (auditoria) |
| `root_person_xref` | `TEXT` | — | Nulo quando nenhum resultado foi aceito (`D-15`) |
| `accepted_count` | `INTEGER` | `NOT NULL DEFAULT 0` | Conexões aceitas |
| `skipped_count` | `INTEGER` | `NOT NULL DEFAULT 0` | Conexões descartadas |
| `message` | `TEXT` | `NOT NULL` | A mensagem de contrato, ao caractere |
| `created_at` | `TIMESTAMPTZ` | `NOT NULL DEFAULT now()` | Índice `ix_dna_analysis_created` (`created_at DESC`) |

### 9.2 `analysis_person` — o snapshot das pessoas

| Coluna | Tipo | Restrições |
| --- | --- | --- |
| `analysis_id` | `UUID` | PK composta, FK → `dna_analysis` `ON DELETE CASCADE` |
| `xref` | `TEXT` | PK composta |
| `nome` | `TEXT` | — |
| `sexo` | `TEXT` | — |
| `nascimento` | `TEXT` | — |
| `local_nascimento` | `TEXT` | — |
| `falecimento` | `TEXT` | — |
| `completa` | `BOOLEAN` | `NOT NULL` |

> 🟢 **`analysis_person` não é a tabela `person` do alvo.** A árvore **não é duplicada** no banco (`RN-04`): ela continua sendo o arquivo imutável de `src/uploads/`, referenciado por `tree_ref`. O que se guarda é o retrato das pessoas **desta** análise, e ele não muda quando a árvore for reimportada.

### 9.3 `match_result` — a conexão e o veredito

| Coluna | Tipo | Restrições | Descrição |
| --- | --- | --- | --- |
| `match_id` | `UUID` | PK, `DEFAULT gen_random_uuid()` | |
| `analysis_id` | `UUID` | `NOT NULL`, FK → `dna_analysis` CASCADE | |
| `result_ordinal` | `INTEGER` | `NOT NULL` | **A ordem é dado** (`RN-08`, `E-01`) |
| `csv_name` | `TEXT` | `NOT NULL` | |
| `matched_name` | `TEXT` | `NOT NULL` | |
| `matched_person_xref` | `TEXT` | `NOT NULL` | FK composta com `analysis_person` |
| `total_cm` | `NUMERIC(12,4)` | — | Transportado do núcleo, **nunca reagregado** (`RN-05`) |
| `relationship_key` | `TEXT` | — | |
| `relationship_label` | `TEXT` | — | |
| `meioses` | `INTEGER` | — | |
| `documentary_status` | `TEXT` | `NOT NULL`, CHECK ∈ {`found`,`not_found`,`ambiguous`,`affinity`} | |
| `mrca_xref` | `TEXT` | — | |
| `causes` | `TEXT[]` | — | |
| `observations` | `TEXT[]` | — | |
| `comparison_status` | `TEXT` | `NOT NULL`, CHECK ∈ {`COMPATIVEL`,`POSSIVEL`,`CONFLITANTE`,`INCONCLUSIVO`} | Verifica **lixo**, não a regra: a autoridade continua sendo `core/evidence_comparison.py` |
| `comparison_label` | `TEXT` | `NOT NULL` | |
| `comparison_method` | `TEXT` | — | Nulo é legítimo: `INCONCLUSIVO` sem janela |
| `expected_low` / `expected_high` / `expected_average` | `NUMERIC(12,4)` | — | |
| `comparison_detail` | `TEXT` | `NOT NULL` | |

Índice `ix_match_result_ordinal` em `(analysis_id, result_ordinal)` — **é o único campo que reproduz a ordem do núcleo**, que é `(tem_caminho, -cM)` e não cM decrescente puro.

### 9.4 `match_path_node` — os nós do caminho

| Coluna | Tipo | Restrições |
| --- | --- | --- |
| `match_id` | `UUID` | PK composta, FK → `match_result` CASCADE |
| `ordinal` | `INTEGER` | PK composta |
| `person_xref` | `TEXT` | `NOT NULL`, FK composta com `analysis_person` |
| `role` | `TEXT` | `NOT NULL`, CHECK ∈ {`ascendente`,`descendente`,`afinidade`} |
| `is_affinity_anchor` | `BOOLEAN` | `NOT NULL DEFAULT FALSE` — o código grava **sempre** `FALSE` |
| `analysis_id` | `UUID` | `NOT NULL` — coluna **redundante**, e existe por um motivo só: permitir a FK composta com `analysis_person` |

### 9.5 `match_kit` — metadados e veredito POR kit

| Coluna | Tipo | Restrições |
| --- | --- | --- |
| `match_kit_id` | `UUID` | PK, `DEFAULT gen_random_uuid()` |
| `match_id` | `UUID` | `NOT NULL`, FK → `match_result` CASCADE |
| `ordinal` | `INTEGER` | `NOT NULL`, `UNIQUE (match_id, ordinal)` |
| `kit` | `TEXT` | Nulo é legítimo: o núcleo usa o marcador ` SEM-KIT` |
| `source` | `TEXT` | — |
| `total_cm` | `NUMERIC(12,4)` | O cM **deste** kit, nunca a soma entre kits (`RF-05`) |
| `segment_count` | `INTEGER` | — |
| `largest_segment_cm` | `NUMERIC(12,4)` | — |
| `status` | `TEXT` | `NOT NULL`, CHECK ∈ {os quatro estados} |
| `status_note` | `TEXT` | — |

Índice `ix_match_kit_match`.

### 9.6 `skipped_match` — os descartados

| Coluna | Tipo | Restrições |
| --- | --- | --- |
| `skipped_id` | `UUID` | PK, `DEFAULT gen_random_uuid()` |
| `analysis_id` | `UUID` | `NOT NULL`, FK → `dna_analysis` CASCADE |
| `ordinal` | `INTEGER` | `NOT NULL`, `UNIQUE (analysis_id, ordinal)` |
| `csv_name` | `TEXT` | `NOT NULL` |
| `kit` | `TEXT` | — |
| `total_cm` | `NUMERIC(12,4)` | — |
| `reason` | `TEXT` | `NOT NULL` — **texto livre**: o núcleo não produz código, e fechar um enum exigiria mapear texto em código |

Índice `ix_skipped_match_analysis`.

### 9.7 O que **não** existe no esquema, e por quê 🔴

`app_user`, `consent_record`, `data_retention_policy`, `access_audit` e `uploaded_file` existem no DDL do alvo (`migration/target_data_model.md`, congelado em 2026-09-28) e **não** são criadas: pertencem às Ondas 3 e 5, e nenhuma tem consumidor. `person`, `family` e `gedcom_tree` não são criadas porque a árvore não é duplicada.

**Nenhum índice começa por `owner_id`**, ao contrário do alvo: `RN-10` diz que nenhuma consulta filtra por dono, e um índice que sugere escopo seria a única coisa no esquema a insinuar isolamento — que segue **aberto** como dívida #4.

**Não há tabela de versão de esquema nem runner de migração.** Limite declarado: `CREATE TABLE IF NOT EXISTS` **não altera** tabela existente, então uma mudança de esquema depois da primeira subida exige `docker compose down -v` (perdendo o histórico) ou `ALTER TABLE` manual.

---

## 10. Configuração e Parâmetros

### 10.1 Variáveis de ambiente 🟢

| Variável | Padrão | Efeito |
| --- | --- | --- |
| `ANALISADOR_HOST` | `127.0.0.1` | Endereço de escuta; abrir para a rede é ato explícito (não há autenticação alguma) |
| `ANALISADOR_PORT` | `5000` | Porta de escuta |
| `ANALISADOR_THREADS` | `4` | Threads do servidor waitress |
| `ANALISADOR_UPLOAD_FOLDER` | *(sem padrão)* | Redireciona a pasta de upload |
| `DATABASE_URL` | *(sem padrão)* | **Ausente ⇒ persistência DESABILITADA** (`_REGISTRO = None`). Presente ⇒ monta `RegistroDeAnalisesPostgres` |

> 🔴 **`psycopg2-binary==2.9.13` está declarado no pin e NÃO está instalado no `.venv/`**, que é o interpretador oficial da suíte e da paridade. Sem o driver, e com `DATABASE_URL` presente, a análise roda igual e a tela ganha o aviso de histórico não registrado (`RN-13`). O import é **preguiçoso** exatamente por isso.

### 10.2 Constantes de domínio 🟢

| Constante | Valor | Papel |
| --- | --- | --- |
| `TETO_DE_UPLOAD_EM_BYTES` | 16 MB | Teto de corpo de requisição (`MAX_CONTENT_LENGTH`) |
| `CABECALHO_GEDCOM` | `0 HEAD` | Assinatura de **conteúdo** aceita no upload |
| `DONO_DO_PROCESSO` | `"unico"` | Marcador único de processo. **Não é mecanismo de segurança** |
| `PASTA_DE_APOSENTADOS` | `_aposentados` | Subpasta para onde `aposentar` move o arquivo |
| `MAX_DEPTH` | 20 | Teto de **iterações** do BFS bidirecional |
| `MAX_HOPS` | 40 | Teto de **arestas** do grafo pessoa↔família no caminho indireto |
| `MAX_DEPTH_ALTERNATIVOS` | 12 | Teto da enumeração de ancestrais comuns |
| `LIMITE_DE_CADEIAS` | 8 | Teto da contagem de cadeias (colapso de pedigree) |
| `LIMITE_DE_CANDIDATOS` | 5 | Teto por lado nas combinações com homônimos |
| `LIMITE_DE_PREAMBULO` | 10 | Teto de linhas antes do cabeçalho do CSV |
| `SEPARADORES` | `(",", ";", "\t", "\|")` | Candidatos a separador, na ordem de desempate |
| `LIMITE_SEGMENTO_FRACO` | 15.0 cM | Limiar de segmento fraco (**critério do projeto**) |
| `IDADE_MINIMA_GENITOR` / `IDADE_MAXIMA_GENITOR` | 12 / 70 | Faixa plausível de idade do genitor |
| `SCP40_ROWS` | 27 linhas | Tabela publicada do Shared cM Project 4.0 |
| `SCP40_NOT_PUBLISHED` | 6 chaves | Relações que a 4.0 **não** publica |
| `STOP_WORDS`, `GENERIC_GIVENS`, `SURNAME_SUFFIXES`, `COMMON_SURNAMES`, `SURNAME_EQUIV`, `SHORT_KEEP` | ver `name_normalization.py:25-52` | Vocabulário do matching |
| `SHARED_CM_DATA` | 9 faixas | Tabela **legada, fora do fluxo**, sem fonte verificável (`cm_estimator.py`) |

---

## 11. Valores Padrão e Sentinelas

| Sentinela | Significado | Onde |
| --- | --- | --- |
| `" SEM-KIT"` (com espaço à esquerda) | CSV sem coluna de kit e sem e-mail. **O espaço é a defesa contra colisão** (`E-03`): `_clean` aplica `.strip()` em todo valor do CSV, então nenhum kit real pode começar com espaço | `genetic_evidence.SEM_KIT` |
| `"Sem Nome"` | Registro **sem** `name` (não é o mesmo que formato vazio) | `core/registro.get_name` |
| `""` (string vazia) | Registro com `Name`, mas formato vazio — **ocorre em dado real** | idem |
| `None` em `totals.cm` | Há mais de um kit e não se sabe qual é a pessoa do GEDCOM | `genetic_evidence.evidence_for` |
| `None` em `largest_segment_cm` | Nenhum segmento tinha cM numérico | `build_genetic_evidence` |
| `None` em `plausible` | Falta data para julgar a idade do genitor (**diferente** de `False`) | `hop_evidence` |
| `None` em `relationship_key` | Relação sem chave canônica (ex.: conexão por afinidade, `SELF`) | `documentary_relationship` |
| `None` em `per_kit` vazio | O confronto terminou antes de avaliar kit por kit | `evidence_comparison.compare` |
| `None` em `aviso_de_persistencia` | Nada a avisar: gravado **ou** persistência desabilitada | `ResultadoDeAnalise` |
| `None` em `root_person_xref` | Nenhum resultado foi aceito | `projetar_analise` |
| `"não encontrado"` | Motivo padrão de um match descartado sem motivo específico | `dna_analysis` |
| `"fonte não identificada no CSV"` | Nenhuma fonte declarada em nenhuma linha do kit | `evidence_for` |
| `"—"` | Valor ausente na formatação de inteiro — ausência **não** é zero | `number_format.formatar_inteiro` |
| `"Sem evidência genética disponível para esta pessoa."` | Código `sem_evidencia` | `evidence_for` |
| `arvore.ged` | Nome visível de fallback quando o nome enviado é vazio | `validate.nome_visivel_seguro` |
| `False` em `is_affinity_anchor` | **Sempre** falso na escrita da análise de DNA | `RegistroDeAnalisesPostgres` |

---

## 12. Rastreabilidade

| Estrutura | Nasce em | É consumida por |
| --- | --- | --- |
| `people`, `families`, `graph`, `child_to_family` | `parsers/gedcom_parser.py` (`carregar_arvore`) | `core/*`, `reporting/mermaid_render.py` (via resolvedor) |
| `EntradaArmazenada` | `ports/adaptadores.py` (`listar`) | `reporting/lista_de_arquivos.py`, tela de entrada |
| Ficha de pessoa, dossiê de homônimos | `core/documentary_relationship.py` | `core/dna_analysis.py`, `core/path_search.py`, template |
| Evidência por kit e por segmento | `core/genetic_evidence.py` | `core/relationship_hypotheses.py`, `core/evidence_comparison.py`, `core/dna_analysis.py` |
| Bloco de hipótese | `core/relationship_hypotheses.py` | `core/evidence_comparison.py`, `core/dna_analysis.py` |
| Confronto | `core/evidence_comparison.py` | `core/dna_analysis.py`, template (estado como classe CSS) |
| Resultado do núcleo de DNA | `core/dna_analysis.py` | `application/dna_analysis.py` (projeção) |
| `PessoaDaAnalise`, `KitDaAnalise`, `ConexaoDaAnalise`, `DescartadoDaAnalise` | `application/dna_analysis.py` (projeção pura) | `AnaliseParaRegistrar` → `RegistroDeAnalises` |
| `AnaliseParaRegistrar` | `application/dna_analysis.py` | `ports/adaptadores.py` (`RegistroDeAnalisesPostgres`) |
| Tabelas `dna_analysis`, `analysis_person`, `match_result`, `match_path_node`, `match_kit`, `skipped_match` | `init.sql` | **nenhum código de `src/` lê** — a persistência só escreve |
| Resultado da busca | `core/path_search.py` | `application/path_search.py` (`ResultadoDeBusca`) → template |
| Diagrama Mermaid | `reporting/mermaid_render.py` | `core/path_search.py`, `core/dna_analysis.py` |
| Arte de runtime | `tests/icone_de_atalho.py`, `tests/banner_da_tela.py` | `src/app.py` (as duas rotas de arte) |

---

*Gerado pelo Reversa-Archaeologist em 2026-10-10 (re-extração).*

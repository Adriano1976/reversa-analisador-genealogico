# Dicionário de Dados — analisador-genealogico

> Nível de documentação: **Completo** (`state.json` → `doc_level`)
> Gerado pelo Reversa-Archaeologist em 2026-10-05 (re-extração).
> Escala de confiança: 🟢 CONFIRMADO | 🟡 INFERIDO | 🔴 LACUNA
> Análise que dá contexto a estas estruturas: `code-analysis.md`. Fluxos: `flowcharts/`.

## 1. Como ler este documento

Este sistema **não tem banco de dados**. Não há DDL, migration, schema nem ORM. Os "dados" existem em três lugares, e cada um tem um dono:

| Onde | O que é | Dono | Persiste? |
| --- | --- | --- | --- |
| Memória do processo | Pessoas, famílias e o grafo do GEDCOM carregado | `core/gedcom_state.py` | Não — morre com o processo |
| Disco | Arquivos enviados (`.ged`, `.csv`) sob chave derivada do conteúdo | `app.py` + `utils/validate.py` | Sim, como arquivo |
| Corpo da requisição/resposta | Formulário e o payload renderizado no template | `app.py` + Jinja2 | Não |

As estruturas abaixo são, portanto, **dicionários e dataclasses leves em memória**, não tabelas. Quando o campo `obrigatório` diz "sim", significa que o produtor sempre o preenche — não que exista uma restrição de banco.

**Convenção de `None`:** o sistema usa `None` para *não sei / não existe*, e **não** para zero. Onde a distinção importa, ela está anotada campo a campo — é o caso de `totals.cm` com múltiplos kits, de `largest_segment_cm`, de `plausible` e de `age_at_birth`.

---

## 2. Entidades do GEDCOM em memória

### 2.1 `people` 🟢

| Campo | Tipo | Obrigatório | Padrão | Origem | Descrição |
| --- | --- | --- | --- | --- | --- |
| *(chave)* | `str` | sim | — | `ref_id(rec.xref_id)` | Identificador do registro (`@I123@`). |
| *(valor)* | registro `ged4py` INDI | sim | — | `parser.records0("INDI")` | Registro cru do GEDCOM; **não** é convertido em dataclass própria. |

**Acesso aos dados do registro** (não são campos de um dicionário, e sim sub-registros do ged4py):

| Dado | Como é obtido | Onde |
| --- | --- | --- |
| Nome formatado | `get_name(person)` → `person.name.format()` ou `"Sem Nome"` | `gedcom_state.py:38-52` |
| Data de nascimento | `BIRT` → sub-registro `DATE` | `documentary_relationship.py:84` |
| Data de falecimento | `DEAT` → sub-registro `DATE` | `documentary_relationship.py:88` |
| Sexo | sub-registro `SEX` | `documentary_relationship.py:132` |
| Local de nascimento | `BIRT` → sub-registro `PLAC` | `documentary_relationship.py:92-101` |
| Famílias como filho | sub-registros `FAMC` | `documentary_relationship.py:243` |
| Famílias como cônjuge | sub-registros `FAMS` | `family_navigation.py:56` |

> ⚠️ `get_name` devolve **string vazia** quando o registro tem `Name` mas o formato resulta vazio. Isso **ocorre em dado real** (296 pessoas em 35.460 em `Arvore_Unificada_Oficial_V1_2.ged`; 17 em 3.056 em `Adriano_Santos.ged`). O literal `Sem Nome` só aparece quando o registro não tem `name`. Não "melhorar" isso: é contrato de paridade com o oráculo congelado (`DIV-001`). 🟢

### 2.2 `families` 🟢

| Campo | Tipo | Obrigatório | Padrão | Origem | Descrição |
| --- | --- | --- | --- | --- | --- |
| *(chave)* | `str` | sim | — | `ref_id(fam.xref_id)` | Identificador da família (`@F6@`). |
| *(valor)* | registro `ged4py` FAM | sim | — | `parser.records0("FAM")` | Registro cru. |

| Sub-registro | Papel | Campo derivado |
| --- | --- | --- |
| `HUSB` | Marido/pai | `family_husband` na evidência de salto; pai em `get_parents` |
| `WIFE` | Esposa/mãe | `family_wife` na evidência de salto; mãe em `get_parents` |
| `CHIL` | Filho | `child_to_family`, `get_children` |

### 2.3 `graph` 🟢

| Propriedade | Valor | Confiança |
| --- | --- | --- |
| Tipo | `networkx.Graph` (não direcionado, **não** MultiGraph) | 🟢 |
| Nós de pessoa | id da pessoa; atributos `label` (nome formatado) e `type="person"` | 🟢 |
| Nós de família | id da família; atributos `label="Familia"` e `type="family"` | 🟢 |
| Arestas | pessoa↔família, para HUSB, WIFE e cada CHIL existente no grafo | 🟢 |
| Substituição | **reatribuído** a cada carga (`gedcom_state.graph = new_graph`) | 🟢 |

> Por ser reatribuído (e não mutado *in place*), quem o consome precisa importá-lo **dentro da função**: é o que `path_finding.find_indirect_path` faz. 🟢

### 2.4 `child_to_family` 🟢

| Campo | Tipo | Obrigatório | Padrão | Descrição |
| --- | --- | --- | --- | --- |
| *(chave)* | `str` | sim | — | id da pessoa na condição de filho |
| *(valor)* | `list[str]` | sim | `[]` | ids das famílias onde aparece como `CHIL` — **lista**, porque pode ser filho em mais de uma |

### 2.5 `versao` 🟢

| Campo | Tipo | Obrigatório | Padrão | Descrição |
| --- | --- | --- | --- | --- |
| `versao` | `int` | sim | `0` | Contador de carregamentos, incrementado por `load_gedcom_and_build_graph`. É o **sinal de invalidação** de índices derivados: `id()` não muda quando os dicionários são mutados *in place*, e dois GEDCOMs diferentes podem ter a mesma contagem de pessoas. Consumido por `documentary_relationship._indice_por_nome`. |

---

## 3. Armazenamento dos arquivos enviados

### 3.1 Nome do arquivo em disco 🟢

Forma: **`<16 hexadecimais>__<nome visível>`** — validada por `^[0-9a-f]{16}__[A-Za-z0-9._-]+$`.

| Parte | Origem | Regra |
| --- | --- | --- |
| Chave (16 hex) | `sha256(conteudo)[:16]` | Derivada do **conteúdo**: mesmo conteúdo → mesma chave. Estável entre requisições, porque o formulário devolve o valor no POST seguinte. |
| Separador | literal `__` | Fixo. |
| Nome visível | nome enviado pelo cliente, saneado | `/`, `\` e NUL viram `_`; espaços e acentos preservados; a **extensão original** é preservada (CSV não vira `.ged`); nome vazio ou só pontos → `arvore.ged`; sem extensão → recebe `.ged`. |

### 3.2 Pasta de upload 🟢

| Campo | Valor | Descrição |
| --- | --- | --- |
| Caminho padrão | `<diretório do app>/uploads` | Ancorado no arquivo do app, e não no diretório corrente: escrita e leitura usam o **mesmo** caminho, sempre. |
| Variável de ambiente | `ANALISADOR_UPLOAD_FOLDER` | Sobrepõe o padrão; usada pelos testes para não escrever na pasta real. |
| Criação | no import, pela **mesma** função que resolve o caminho | Impede que o diretório criado e o procurado divirjam. |

### 3.3 Formulário entre requisições 🟢

| Campo | Tipo | Obrigatório | Descrição |
| --- | --- | --- | --- |
| `action` | `str` | sim | `upload_gedcom`, `dna_analysis` ou `path_search`. |
| `gedcom_filename` | `str` | sim nos dois fluxos pós-upload | Nome armazenado; validado por forma antes de virar caminho. |
| `person1_name` / `person2_name` | `str` | sim em `path_search` | Nomes consultados (recebem `strip`). |
| `root_name` | `str` | sim em `dna_analysis` | Nome da pessoa raiz. |
| `gedcom` | arquivo | sim em `upload_gedcom` | Arquivo GEDCOM. |
| `matches_csv` | arquivo | sim em `dna_analysis` | CSV de matches. |

---

## 4. CSV de matches

### 4.1 Colunas reconhecidas por papel 🟢

A detecção é por papel, tolerando variação de cabeçalho. A comparação ignora maiúsculas e espaços nas pontas.

| Papel | Nomes aceitos | Obrigatório | Onde |
| --- | --- | --- | --- |
| Nome | `Name`, `MatchedName`, `Nome` | **sim** | `csv_ingest.py:186` |
| cM | `cM`, `TotalCM`, `Total cM` | **sim** | `csv_ingest.py:187` |
| SNPs | `SNPs`, `SNP`, `SNPs Count` | não | `genetic_evidence.py:64` |
| Cromossomo | `Chromosome`, `Chr`, `Cromossomo` | não | `genetic_evidence.py:65` |
| Início | `Start`, `Start Location`, `Posicao inicial` | não | `genetic_evidence.py:66` |
| Fim | `End`, `End Location`, `Posicao final` | não | `genetic_evidence.py:67` |
| Fonte | `Source`, `Fonte`, `Company` | não | `genetic_evidence.py:68` |
| ID de match | primeira coluna com >30% dos valores casando `[A-Z]{2}\d{7}` | não | `csv_ingest.py:190-192` |
| E-mail | **última** coluna cujo nome contém `mail` | não | `csv_ingest.py:193-194` |
| Kit | coluna cujo **nome** casa `kit`, `gedmatch`, `teste` ou `test` e >50% dos valores casam `[A-Z]{1,3}\d{4,8}`; senão, coluna com >30% em `[A-Z]{2}\d{7}` | não | `genetic_evidence.py:71-81` |

### 4.2 Atributos de leitura (`df.attrs`) 🟢

Canal escolhido porque a assinatura de `read_csv_with_fallback` é contrato: trocar o retorno por tupla quebraria `dna_analysis` e o `__all__` que a reexporta.

| Atributo | Tipo | Padrão | Descrição |
| --- | --- | --- | --- |
| `separador` | `str` | `","` | Separador efetivamente usado. |
| `encoding` | `str` | `"utf-8"` | Encoding que funcionou (`utf-8` ou `latin-1`). |
| `linhas_antes_do_cabecalho` | `int` | `0` | Quantas linhas de preâmbulo foram puladas. |
| `linhas_ignoradas` | `list[int]` | `[]` | Números (1-based) das linhas com número de campos diferente do cabeçalho. |
| `erro_de_leitura` | `str \| None` | `None` | Texto do erro de tokenização do pandas, quando houve releitura. |

### 4.3 `_group_key` (coluna temporária) 🟢

| Campo | Tipo | Descrição |
| --- | --- | --- |
| `_group_key` | `str` | `norm_name(demojibake(nome))` + `" \| "` + cauda, onde a cauda é o id em maiúsculas, ou o e-mail normalizado, ou nada. É a chave de soma dos cM. |

---

## 5. Evidência genética

### 5.1 Evidência por (nome normalizado, kit) 🟢

Chave externa: `evidencias[nome_normalizado][kit]`.

| Campo | Tipo | Obrigatório | Padrão | Descrição |
| --- | --- | --- | --- | --- |
| `kit` | `str \| None` | não | `None` | Kit de origem; `None` quando o CSV não traz kit nem e-mail. |
| `person_name_csv` | `str` | sim | — | Nome como veio do CSV, já com mojibake corrigido. |
| `source` | `str \| None` | não | `None` | Fonte declarada (empresa/laboratório); primeira não vazia encontrada. |
| `total_cm` | `float` | sim | `0.0` | Soma dos segmentos **sem arredondamento**. |
| `segments` | `list[dict]` | sim | `[]` | Segmentos individuais (§5.2). |
| `records_used` | `int` | sim | `0` | Quantas linhas do CSV entraram nesta evidência. |
| `segment_count` | `int` | sim | `0` | Número de segmentos. |
| `largest_segment_cm` | `float \| None` | não | `None` | Maior segmento; `None` quando nenhum segmento tem cM numérico. |
| `snps_total` | `int \| None` | não | `None` | Soma de SNPs; `None` quando não há SNPs informados. |
| `snps_largest_segment` | `int \| None` | não | `None` | SNPs do maior segmento. |
| `chromosomes` | `list[str]` | sim | `[]` | Cromossomos distintos, ordenados por tamanho e depois por valor. |
| `method` | `str` | sim | — | Texto que explica se o total é soma de N linhas ou valor de uma linha. |
| `weak_segment` | `bool` | não | *(ausente)* | Presente e `True` quando o maior segmento é menor que 15 cM. |

### 5.2 Segmento 🟢

| Campo | Tipo | Obrigatório | Padrão |
| --- | --- | --- | --- |
| `chromosome` | `str \| None` | não | `None` |
| `start` | `int \| None` | não | `None` |
| `end` | `int \| None` | não | `None` |
| `cm` | `float` | sim | `0.0` |
| `snps` | `int \| None` | não | `None` |

Ordenação dos segmentos: `cm` decrescente, com os `None` por último.

### 5.3 Aviso 🟢

| Campo | Tipo | Descrição |
| --- | --- | --- |
| `code` | `str` | `multiplos_kits`, `kit_ausente`, `segmento_fraco`, `sem_evidencia` |
| `message` | `str` | Texto em português, exibido ao operador |

### 5.4 Evidência consolidada de uma pessoa (`evidence_for`) 🟢

| Campo | Tipo | Padrão | Descrição |
| --- | --- | --- | --- |
| `available` | `bool` | `False` | Há evidência genética para a pessoa? |
| `source` | `str \| None` | `"fonte não identificada no CSV"` | Fonte do kit principal. |
| `kits` | `list[dict]` | `[]` | Kits separados, ordenados por cM decrescente. **Nunca somados.** |
| `totals.cm` | `float \| None` | `None` | **`None` quando há mais de um kit** — é o número honesto quando não se sabe qual kit é a pessoa do GEDCOM. |
| `totals.cm_por_kit` | `dict[str, float]` | `{}` | cM por kit; chave `SEM-KIT` quando não informado. |
| `totals.segments` | `int` | `0` | Soma de segmentos de todos os kits. |
| `totals.largest_segment_cm` | `float \| None` | `None` | Maior segmento entre os kits. |
| `totals.chromosomes` | `list[str]` | `[]` | União dos cromossomos. |
| `totals.records_used` | `int` | `0` | Soma das linhas usadas. |
| `warnings` | `list[dict]` | `[]` | Avisos do kit + avisos recebidos. |

---

## 6. Possibilidades e confronto

### 6.1 Bloco de hipótese por kit (`possible_relationships`) 🟢

| Campo | Tipo | Obrigatório | Padrão | Descrição |
| --- | --- | --- | --- | --- |
| `total_cm` | `float \| None` | não | `None` | Valor avaliado; `None` quando não há cM utilizável. |
| `possible_relationships` | `list[dict]` | sim | `[]` | **Sempre lista**, inclusive vazia. Nunca um parentesco único. |
| `confidence` | `str` | sim | `"indeterminada"` | `indeterminada`, `baixa` ou `muito baixa` — heurística **do projeto**. |
| `confidence_note` | `str` | não | — | Explicação da confiança. |
| `interpretation` | `str` | sim | — | Leitura em português do que o valor permite e do que não permite concluir. |
| `reference` | `dict` | sim | — | `SCP40_META` (§6.3). |
| `kit` | `str \| None` | não | `None` | Kit a que o bloco se refere. |
| `segment_count` | `int \| None` | não | `None` | Segmentos do kit. |
| `largest_segment_cm` | `float \| None` | não | `None` | Maior segmento do kit. |

### 6.2 Linha publicada do Shared cM Project 4.0 🟢

| Campo | Tipo | Descrição |
| --- | --- | --- |
| `key` | `str` | Chave canônica (`PARENT_CHILD`, `SIBLINGS`, `1C1R`, …) |
| `name_en` | `str` | Nome na fonte (`1C1R`, `Half 1C`, …) |
| `name_pt` | `str` | Nome em português exibido na tela |
| `meioses` | `int` | Saltos pai-filho entre as duas pessoas — a grandeza que o cM mede |
| `average` | `int` | Média publicada (a versão 4.0 **não** publica mediana) |
| `range_low` / `range_high` | `int` | Faixa publicada, após remoção de 1% dos envios (0,5% em cada ponta) |

### 6.3 Metadados da fonte (`SCP40_META`) 🟢

| Campo | Valor |
| --- | --- |
| `version` | `4.0` |
| `release` | `março de 2020` |
| `sample_size` | `59714` |
| `range_definition` | Faixa (mínimo–máximo) após remoção de 1% dos envios — **não** é o intervalo observado completo |
| `sources` | PDF oficial do Shared cM Project 4.0 e a ferramenta do DNA Painter |

### 6.4 Resultado do confronto 🟢

| Campo | Tipo | Padrão | Descrição |
| --- | --- | --- | --- |
| `status` | `str` | `"INCONCLUSIVO"` | `COMPATIVEL`, `POSSIVEL`, `CONFLITANTE`, `INCONCLUSIVO` |
| `label` | `str` | `"Inconclusivo"` | Rótulo em português |
| `message` | `str` | — | Mensagem fixa do estado |
| `causes` | `list[str]` | `[]` | 12 causas possíveis em `CONFLITANTE`; 9 em `POSSIVEL`; vazio nos demais |
| `per_kit` | `list[dict]` | `[]` | `{kit, status, cm, note}` por kit |
| `method` | `str \| None` | `None` | `scp40:<nome>` ou `scp40:meioses=<n>` — **como o estado foi decidido** |
| `expected_range` | `dict \| None` | `None` | `{low, high, average, label}` da janela esperada |
| `detail` | `str \| None` | `None` | Frase que reúne parentesco documental, janela e a nota de cada kit |
| `observations` | `list[str]` | `[]` | Notas e avisos preservados |

> Com mais de um kit, o `status` final é o **mais conservador** na ordem `CONFLITANTE > POSSIVEL > COMPATIVEL > INCONCLUSIVO`, e a nota por kit é registrada. 🟢

---

## 7. Parentesco documental

### 7.1 Resultado (`documentary_relationship`) 🟢

| Campo | Tipo | Obrigatório | Padrão | Descrição |
| --- | --- | --- | --- | --- |
| `status` | `str` | sim | — | `found`, `ambiguous`, `not_found` ou `affinity` |
| `source` | `str` | sim | `"GEDCOM"` | Origem da afirmação |
| `label` | `str` | sim | — | Rótulo legível do parentesco |
| `relationship_key` | `str \| None` | não | `None` | Chave canônica usada para casar com a tabela do Shared cM |
| `meioses` | `int \| None` | não | `None` | Saltos pai-filho entre as duas pessoas |
| `degrees` | `dict \| None` | não | `None` | `{a_up, b_up, cousin_degree, removed}` |
| `person_a` / `person_b` | `dict` | sim | — | Fichas completas (§7.2) |
| `common_ancestor` | `dict \| None` | não | `None` | `{id, name, birth}` |
| `common_ancestors` | `list[dict]` | sim | `[]` | Todos até 12 níveis (§7.5) |
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
| `exact_count` | `int` | `0` | Registros com o **mesmo nome normalizado** |
| `exact_matches` | `list[dict]` | `[]` | Fichas dos exatos |
| `similar_count` | `int` | `0` | Candidatos semelhantes informados pelo chamador |
| `similar_matches` | `list[dict]` | `[]` | Até 5 fichas dos semelhantes |
| `ambiguous` | `bool` | `False` | Mais de um exato |
| `differences` | `list[dict]` | `[]` | `{campo, rotulo}` em que as fichas divergem |
| `identical_data` | `bool` | `False` | Ambíguo, mas sem nenhuma divergência de dado |

### 7.5 Ancestral comum e caminho alternativo 🟢

| Estrutura | Campos |
| --- | --- |
| Ancestral comum | `id`, `name`, `distance_a`, `distance_b`, `total_meioses`, `birth` |
| Caminho alternativo | `ids`, `names`, `via`, `distance_a`, `distance_b`, `total_meioses`, `ancestor_name` |

---

## 8. Resultado da análise de DNA (payload da tela)

### 8.1 Item de resultado 🟢

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
| `observations` | `list[str]` | Observações deduplicadas, na ordem de origem |
| `warnings` | `list[dict]` | Avisos do documental + da evidência |

### 8.2 Descartado 🟢

| Campo | Tipo | Descrição |
| --- | --- | --- |
| `csv_name` | `str` | Nome do CSV que não virou resultado |
| `kit` | `str \| None` | Kit do descartado |
| `cm` | `float` | cM do kit |
| `motivo` | `str` | Motivo declarado; nunca vazio (`"não encontrado"` é o padrão) |

### 8.3 Mensagem final 🟢

Forma: `"{N} conexões encontradas. {M} descartadas."`. Quando não há nenhum resultado, os avisos de arquivo (preâmbulo e linhas descartadas) são **anexados à mensagem**, porque não há cartão na tela onde eles apareçam.

---

## 9. Configuração e Parâmetros

### 9.1 Variáveis de ambiente 🟢

| Variável | Padrão | Efeito |
| --- | --- | --- |
| `ANALISADOR_HOST` | `127.0.0.1` | Endereço de escuta; abrir para a rede é ato explícito |
| `ANALISADOR_PORT` | `5000` | Porta de escuta |
| `ANALISADOR_THREADS` | `4` | Threads do servidor waitress |
| `ANALISADOR_UPLOAD_FOLDER` | *(sem padrão)* | Redireciona a pasta de upload |

### 9.2 Constantes de domínio 🟢

| Constante | Valor | Papel |
| --- | --- | --- |
| `MAX_CONTENT_LENGTH` | 16 MB | Teto de corpo de requisição |
| `CABECALHO_GEDCOM` | `0 HEAD` | Assinatura de conteúdo aceita no upload |
| `MAX_DEPTH` | 20 | Teto de iterações do BFS bidirecional |
| `MAX_HOPS` | 40 | Teto de arestas do caminho indireto |
| `MAX_DEPTH_ALTERNATIVOS` | 12 | Teto da enumeração de ancestrais comuns |
| `LIMITE_DE_CADEIAS` | 8 | Teto da contagem de cadeias (colapso) |
| `LIMITE_DE_CANDIDATOS` | 5 | Teto por lado nas combinações com homônimos |
| `LIMITE_DE_PREAMBULO` | 10 | Teto de linhas antes do cabeçalho do CSV |
| `LIMITE_SEGMENTO_FRACO` | 15.0 cM | Limiar de segmento fraco (**critério do projeto**) |
| `IDADE_MINIMA_GENITOR` / `IDADE_MAXIMA_GENITOR` | 12 / 70 | Faixa plausível de idade do genitor |
| `CASAS` | 2 | Teto de casas decimais na exibição (não é número fixo) |
| `SCP40_META.version` | 4.0 | Versão da tabela de possibilidades |
| `STOP_WORDS`, `GENERIC_GIVENS`, `SURNAME_SUFFIXES`, `COMMON_SURNAMES`, `SURNAME_EQUIV`, `SHORT_KEEP` | ver `name_normalization.py:22-49` | Vocabulário do matching |

---

## 10. Valores Padrão e Sentinelas

| Sentinela | Significado | Onde |
| --- | --- | --- |
| `"Sem Nome"` | Registro **sem** `name` (não é o mesmo que formato vazio) | `gedcom_state.get_name` |
| `""` (string vazia) | Registro com `Name`, mas formato vazio — **ocorre em dado real** | idem |
| `None` em `totals.cm` | Há mais de um kit e não se sabe qual é a pessoa do GEDCOM | `genetic_evidence.evidence_for` |
| `None` em `largest_segment_cm` | Nenhum segmento tinha cM numérico | `build_genetic_evidence` |
| `None` em `plausible` | Falta data para julgar a idade do genitor (diferente de `False`) | `hop_evidence` |
| `None` em `relationship_key` | Relação sem chave canônica (ex.: conexão por afinidade) | `documentary_relationship` |
| `" SEM-KIT"` (com espaço à esquerda) | CSV sem coluna de kit e sem e-mail. **O espaço é a defesa contra colisão** (`E-03`): `_clean` aplica `.strip()` em todo valor do CSV, então nenhum kit real pode começar com espaço. Antes era o literal `"SEM-KIT"`, que um CSV podia conter de fato — corrigido em 2026-10-05 | `genetic_evidence.SEM_KIT` |
| `"não encontrado"` | Motivo padrão de um match descartado sem motivo específico | `dna_analysis` |
| `"—"` | Valor ausente na formatação de inteiro — ausência **não** é zero | `number_format.formatar_inteiro` |
| `arvore.ged` | Nome visível de fallback quando o nome enviado é vazio | `validate.nome_visivel_seguro` |

---

## 11. Rastreabilidade

| Estrutura | Nasce em | É consumida por |
| --- | --- | --- |
| `people`, `families`, `graph`, `child_to_family`, `versao` | `parsers/gedcom_parser.py` | `core/*`, `reporting/mermaid_render.py` |
| Ficha de pessoa, dossiê de homônimos | `core/documentary_relationship.py` | `core/dna_analysis.py`, `core/path_search.py`, template |
| Evidência por kit e por segmento | `core/genetic_evidence.py` | `core/relationship_hypotheses.py`, `core/evidence_comparison.py`, `core/dna_analysis.py` |
| Bloco de hipótese | `core/relationship_hypotheses.py` | `core/evidence_comparison.py`, `core/dna_analysis.py` |
| Confronto | `core/evidence_comparison.py` | `core/dna_analysis.py`, template |
| Resultado da análise | `core/dna_analysis.py` | `app.py` → `templates/index.html` |
| Resultado da busca | `core/path_search.py` | `app.py` → `templates/index.html` |
| Diagrama Mermaid | `reporting/mermaid_render.py` | `core/path_search.py`, `core/dna_analysis.py` |

---

*Gerado pelo Reversa-Archaeologist em 2026-10-05 (re-extração).*

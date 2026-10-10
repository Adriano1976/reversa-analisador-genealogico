# Unit `analise-dna` — Design Técnico

> Spec gerada pelo Reversa-Writer na re-extração de **2026-10-10** (nível **Completo**). Substitui o design de 2026-10-05, que descrevia o fluxo **sem** fronteira de aplicação, **sem** projeção pura e **sem** persistência.
> Fontes: `application/dna_analysis.py`, `application/traducao.py`, `core/{dna_analysis,genetic_evidence,relationship_hypotheses,evidence_comparison,matching,name_normalization,registro,cm_estimator,erros}.py`, `parsers/csv_ingest.py`, `ports/`, `app.py` (ramo `dna_analysis`), `init.sql`.
> Escala de confiança: 🟢 CONFIRMADO | 🟡 INFERIDO | 🔴 LACUNA

---

## Interface

### Endpoint HTTP

| Método | Caminho | Ação | Entrada | Saída | Status |
|--------|---------|------|---------|-------|--------|
| POST | `/` | `dna_analysis` | `gedcom_filename`, `root_name`, `matches_csv` (arquivo) **ou** `matches_csv_filename` (referência) | `index.html` com `dna_results`, `skipped_matches`, `message`, `aviso_de_persistencia`, `success` | 200 |

> 🟢 **Toda recusa de negócio é HTML com status `200` e `success=False`.** O status que `traduzir` devolve (`404`/`422`) **não tem consumidor** nesta onda: vale só para a API nova, que não existe (`BR-D-95`).

### Símbolos

| Símbolo | Arquivo | Assinatura | Retorno | Observação |
|---------|---------|-----------|---------|------------|
| `dna_analysis` (caso de uso) | `application/dna_analysis.py` | `(caminho_do_csv, root_name, arvore, deps, dono, referencia_da_arvore=None, registro=None)` | `ResultadoDeAnalise` | `dono` **não** participa de decisão; `None` em `registro` ou em `referencia_da_arvore` = não registrar 🟢 |
| `projetar_analise` | idem | `(resultados, descartados, mensagem, referencia_da_arvore, referencia_do_csv, root_name)` | `AnaliseParaRegistrar` | **Pura**, pública para ser exercitada sem banco 🟢 |
| `_juntar` / `_ficha` / `_pessoas` | idem | `(por_xref, pessoa)` / `(ficha, completa)` / `(resultados)` | `None` / `PessoaDaAnalise \| None` / `(pessoas, raiz)` | A ficha completa vence; sem `id` devolve `None` 🟢 |
| `_papeis_do_caminho` | idem | `(documentary)` | `tuple[(xref, papel)]` | Papel **derivado**, corte no MRCA 🟢 |
| `_kits` / `_conexao` | idem | `(evidence, comparison)` / `(ordinal, resultado)` | `tuple[KitDaAnalise]` / `ConexaoDaAnalise` | Pareamento **por índice** 🟢 |
| `dna_analysis` (núcleo) | `core/dna_analysis.py` | `(csv_path, root_name, deps, arvore)` | `(results_sorted, skipped, message)` | Não conhece registro 🟢 |
| `_montar_diagrama` | idem | `(deps, documentary, root_id, pid, dominio)` | `str \| None` | Mermaid do caminho **documental**, ou `None` 🟢 |
| `_observacoes` | idem | `(documentary, evidence, comparison, extra)` | `list[str]` | Deduplicada, preservando a ordem 🟢 |
| `read_csv_with_fallback` | `parsers/csv_ingest.py` | `(path)` | `DataFrame` com `attrs` | `separador`, `encoding`, `linhas_antes_do_cabecalho`, `linhas_ignoradas`, `erro_de_leitura` 🟢 |
| `detectar_separador` / `localizar_cabecalho` / `linhas_irregulares` | idem | `(path, encoding)` / `(path, sep, encoding)` / `(path, sep, encoding, cabecalho)` | `str` / `int` / `list[int]` | Nunca `csv.Sniffer` 🟢 |
| `detect_columns` / `aggregate_matches` | idem | `(df)` / `(df, name_col, cm_col, id_col, email_col)` | `(name, cm, id, email)` / `DataFrame` | Agrupa por `_group_key` e soma cM 🟢 |
| `detect_segment_columns` | `core/genetic_evidence.py` | `(df)` | `dict` de colunas por papel | SNPs, cromossomo, início, fim, fonte, kit, e-mail 🟢 |
| `build_genetic_evidence` | idem | `(df)` | `(evidencias, avisos)` | Agrupa por **(nome, kit)** 🟢 |
| `evidence_for` | idem | `(dossie, avisos, kit_key)` | `dict` | **Nunca soma kits** 🟢 |
| `possible_relationships` / `hypotheses_for_evidence` | `core/relationship_hypotheses.py` | `(total_cm)` / `(evidence)` | `dict` / `list[dict]` | Sempre lista, inclusive vazia 🟢 |
| `row_for_key` / `rows_by_meioses` / `meioses_window` | idem | `(key)` / `(meioses)` / `(meioses)` | `dict \| None` / `list` / `dict \| None` | Envoltória por meioses 🟢 |
| `compare` / `_avaliar_kit` / `_janela_do_documental` | `core/evidence_comparison.py` | `(documentary, hypotheses, evidence)` / `(bloco, janela, meioses_documental)` / `(documentary)` | `dict` | `_avaliar_kit` **recebe e não usa** `meioses_documental` 🟡 |
| `build_ged_indexes` / `match_candidates` | `core/matching.py` | `(arvore)` / `(arvore, match_name, cm_value, ged_index, surname_index, features)` | `(ged_index, surname_index, features)` / `(candidate_pids, reason)` | `reason` é **texto**, não código 🟢 |
| `norm_name` | `utils/name_keys.py` | `(s)` | `str` | NFKD, sem diacríticos, minúsculas 🟢 |
| `split_name_pt` / `surname_core_tokens` / `soft_prefix_jaccard` | `core/name_normalization.py` | `(s)` / `(name, keep_last=3)` / `(a, b, min_pref=4, min_len=2)` | `(given, surnames, suffixes)` / `(base, suffixes)` / `float` | Vocabulário em `BR-D-54`..`BR-D-61` 🟢 |
| `documentary_relationship` / `homonym_dossier` | `core/documentary_relationship.py` | `(arvore, a_id, b_id, homonyms=None)` / `(arvore, name_query, similar_ids=None)` | `dict` | **Nunca lê cM**; compartilhado com `busca-caminho` 🟢 |
| `traduzir` | `application/traducao.py` | `(erro: ErroDeDominio)` | `RespostaDeErro(mensagem, status)` | Tabela de **funções**, não mapa de constantes 🟢 |
| `RegistroDeAnalisesPostgres.registrar` | `ports/adaptadores.py` | `(analise, dono)` | `(referencia, aviso)` | **Nunca levanta** 🟢 |
| `get_relationships_by_cm` | `core/cm_estimator.py` | `(cm_value)` | `list[str]` | **Legado fora do fluxo** 🟢 |

### Os três eixos, e a costura entre eles

| Eixo | Módulo | Entra | Sai | O que ele **não** pode fazer |
|------|--------|-------|-----|------------------------------|
| Parentesco **documental** | `core/documentary_relationship.py` | xrefs + árvore | caminho, MRCA, meioses, rótulo, dossiê de homônimos | **Ler cM** 🟢 |
| Evidência **genética** | `core/genetic_evidence.py` | `DataFrame` | evidências por (nome, kit), avisos | **Conhecer o GEDCOM** 🟢 |
| **Confronto** | `core/evidence_comparison.py` | os dois acima + hipóteses | um dos 4 estados, com causas | **Reescrever vínculo** 🟢 |

## Fluxo Principal

### Borda (`app.py`, ramo `dna_analysis`)

1. `_arvore_do_formulario()` resolve e parseia a árvore escolhida (unit `tela-de-entrada`). Erro aqui encerra o ramo. 🟢
2. Lê `root_name` de `request.form`. 🟢
3. Lê `matches_csv_filename` — **campo novo, opcional** (`BR-D-89`). Presente? `_ARMAZENAMENTO.resolver(...)`; não resolve → `Erro: Arquivo 'X' não existe mais.`, com a tela ainda utilizável. 🟢
4. Ausente? Exige o arquivo `matches_csv` e o grava com `guardar_com_substituicao(..., "csv", ...)` — **a mesma** porta e a **mesma** regra de reenvio do GEDCOM. A substituição gera `aviso_de_substituicao`, que será **acrescentado** depois da mensagem do resultado. 🟢
5. Chama o caso de uso com `caminho_do_csv`, `root_name`, `arvore`, `_DEPENDENCIAS`, `DONO_DO_PROCESSO`, `gedcom_filename`, `_REGISTRO`. 🟢
6. `except ErroDeDominio` → `traduzir(erro).mensagem` com `success=False`; `except Exception` → `Ocorreu um erro: {e}`. 🟢

### Caso de uso (`application/dna_analysis.py`)

1. `fluxo_dna(caminho_do_csv, root_name, deps, arvore)` — **todo** o cálculo está no núcleo; aqui não há decisão de negócio. 🟢
2. Se `registro is not None` **e** `referencia_da_arvore`: `projetar_analise(...)` e `registro.registrar(analise, dono)`, **dentro de um `try`**. Exceção → `aviso = "Histórico não registrado: falha ao preparar os dados (Tipo: msg)."`. 🟢
3. Devolve `ResultadoDeAnalise(resultados, descartados, mensagem, aviso_de_persistencia=aviso)`. 🟢

> 🟢 **`ResultadoDeAnalise` não tem desfecho de três valores** — diferente de `busca-caminho`, que tem. Esta unit **ou levanta exceção de domínio, ou devolve resultado com mensagem de contrato**. `aviso_de_persistencia` é o **único** campo que a persistência acrescentou, e nulo significa "nada a avisar".

### Núcleo — leitura e evidência

1. Resolve a raiz: `root_name.lower()` como substring de `get_name(p).lower()` sobre `arvore[0]`; vazio → `PessoaNaoEncontrada("Seu nome 'X' não foi encontrado no GEDCOM.")`; ambígua → usa o **primeiro** e monta o aviso com a contagem e os ids. 🟢
2. `deps.read_csv(caminho)` → `DataFrame` com `attrs`. Preâmbulo e linhas irregulares viram `detalhe_linhas` e, depois, **avisos do arquivo** com a contagem e até 10 números de linha (com `…` se houver mais). 🟢
3. `deps.detect_columns(df)`; sem nome **ou** sem cM → `DnaCsvSemColunas` com a **mensagem longa e acionável** (separador usado, colunas encontradas, e o que conferir). 🟢
4. `build_genetic_evidence(df)` → evidências por (nome, kit) + avisos. 🟢
5. `build_ged_indexes(arvore)` → índices e cache de atributos normalizados, **uma vez**. 🟢
6. `homonym_dossier(arvore, root_name)` → aviso de raiz ambígua. 🟢
7. `resolvedor_de_diagrama(arvore)` — montado **uma vez por análise**, fora do laço (`BR-D-64`). 🟢

### Núcleo — matching e parentesco, por evidência

1. Para cada evidência, `match_candidates(...)` devolve `(candidate_pids, reason)` com o **cM do kit** (`BR-D-38`). 🟢
2. Para cada candidato, o dossiê de homônimos vem do cache por **nome** (`_dossie`) e o parentesco do cache por **pessoa** (`documental_por_pessoa`). 🟢
3. Vence o **primeiro** candidato com caminho documental; sem nenhum, o primeiro da lista (`BR-D-39`). 🟢
4. `hypotheses_for_evidence(evidence)` → lista por kit; `compare(documentary, hypotheses, evidence)` → estado, rótulo, mensagem, causas, `per_kit`, `method`, `expected_range`, `detail`. 🟢
5. Monta `comparison`, `observations` (deduplicadas, na ordem documental → genética → confronto → avisos) e `mermaid_data` **só** quando há caminho. 🟢
6. Ordena: **documental primeiro**, depois cM decrescente (`BR-D-41`). 🟢
7. Mensagem: `"N conexões encontradas. M descartadas."`; **sem resultado**, os avisos do arquivo são anexados (`BR-D-42`, `BR-D-43`). 🟢

### Projeção e registro

1. `_pessoas(resultados)` monta o retrato por xref: `person_a`/`person_b` **completos**, nós do caminho **incompletos**; a ficha completa vence; a raiz é `person_a.id` da **primeira** conexão. 🟢
2. `_conexao(i, r)` para cada resultado, com `ordinal` = posição **apresentada**, `kits` por **índice** e `caminho` por papel **derivado**. 🟢
3. `descartados` → `DescartadoDaAnalise` com `reason` = motivo textual (default `"não encontrado"`). 🟢
4. `_escrever(cursor, …)` grava na ordem das FKs, tudo numa transação. 🟢

### Leitura tolerante do CSV (`parsers/csv_ingest.py`)

| Passo | Regra |
| --- | --- |
| Encoding | `utf-8`; na falha, `latin-1` — e **nenhuma exceção de domínio intercepta a troca de codec** 🟢 |
| Separador | Conta `,` `;` TAB `\|` no cabeçalho; **maior vence**, empate fica com a vírgula 🟢 |
| Cabeçalho | Número de campos **modal**, exigindo frequência ≥ 2, primeira linha divergente e posição entre as 10 primeiras 🟢 |
| Preâmbulo | Linhas antes do cabeçalho são reportadas à parte e **não** contam como linha torta 🟢 |
| Linha torta | No erro de tokenização, **relê** com `on_bad_lines="skip"` e registra os números em `df.attrs` 🟢 |
| Erro final | `CsvIlegivel` em português, listando as tentativas e o que conferir 🟢 |

### Confronto (`core/evidence_comparison.py`)

1. O dicionário nasce com `status = "INCONCLUSIVO"` e `observations` acumulando os avisos relevantes do documental (`data_impossivel`, `colapso_de_pedigree`, `caminhos_multiplos`). 🟢
2. Sem DNA → `INCONCLUSIVO`, registrando que o documental vale por si. 🟢
3. Com DNA mas **sem caminho** → `INCONCLUSIVO`: nenhum caminho é inventado a partir do DNA. 🟢
4. Identidade ambígua → `INCONCLUSIVO`, listando os registros. 🟢
5. Sem faixa publicada **nem** janela por meioses → `INCONCLUSIVO`. 🟢
6. Registra `method` (`scp40:<nome>` ou `scp40:meioses=<n>`) e `expected_range`; se a janela veio da envoltória, a nota explica por quê. 🟢
7. Avalia **cada kit** com `_avaliar_kit` e registra `per_kit`. 🟢
8. Estado final = **o mais conservador**, e o rol de causas conforme o estado: 12 em `CONFLITANTE`, **8** em `POSSIVEL`. 🟢

## Fluxos Alternativos

| Condição | Comportamento | Conf. |
| --- | --- | --- |
| Sem árvore resolvida, ou arquivo removido | Erro antes de qualquer análise (`_arvore_do_formulario`) | 🟢 |
| Sem CSV e sem referência de CSV | `"Por favor, carregue o arquivo CSV de matches."`, preservando a lista de nomes | 🟢 |
| Referência de CSV que não resolve | `Erro: Arquivo 'X' não existe mais.` | 🟢 |
| Raiz não encontrada | `PessoaNaoEncontrada` → `"Ocorreu um erro: Seu nome 'X' não foi encontrado no GEDCOM."` | 🟢 |
| Raiz ambígua | Usa o primeiro registro e **avisa** a contagem e os ids | 🟢 |
| Colunas de nome/cM ausentes | `DnaCsvSemColunas` acionável com separador, colunas e linhas tortas | 🟢 |
| CSV em `latin-1` | Recuo de encoding | 🟢 |
| CSV com preâmbulo | Cabeçalho localizado; aviso com a linha usada | 🟢 |
| CSV com linhas tortas | Análise prossegue; aviso com contagem e números de linha | 🟢 |
| Match sem candidato | Descarte com `reason` — ver a tabela de descartes abaixo | 🟢 |
| Candidato aceito sem caminho documental | **Não é descartado.** Entra no resultado com as quatro seções; o confronto responde `INCONCLUSIVO` | 🟢 |
| Mais de um kit, `total_cm` de um deles ausente | Aquele kit é `INCONCLUSIVO`; o estado final segue o mais conservador | 🟢 |
| Nenhum resultado | Avisos do arquivo anexados à mensagem | 🟢 |
| `cM ≤ 0` ou não numérico no CSV | `possible_relationships` devolve **lista vazia** e confiança `indeterminada` — **não** o literal de relação distante | 🟢 |
| Persistência desabilitada (`registro` nulo ou sem referência) | Nada é gravado; a tela **não muda um byte** | 🟢 |
| Driver `psycopg2` ausente | Aviso `Histórico não registrado: o driver do banco não está instalado neste interpretador (…)` | 🟢 |
| Banco fora ou erro no SQL | Aviso `Histórico não registrado: Tipo: msg`; o resultado chega inteiro | 🟢 |
| Falha na projeção | O mesmo tratamento: aviso, e a análise é exibida | 🟢 |
| CSV da lista **e** arquivo enviado no mesmo formulário | A **referência vence**; o arquivo é ignorado | 🟢 |

## Descartes — o que o operador faz com cada motivo

> **Decisão de produto de 2026-10-05** (`questions.md#pergunta-5`), mantida: a lista de descartados **não é só auditoria** — o operador **age** sobre ela. É o que sustenta `RF-27` como `Must`.
>
> O motivo **já traz os números** da decisão (`given`, `final`, `inter`, `jacc`) justamente para permitir esse julgamento.

| Motivo (literal) | O que significa | Ação esperada do operador |
| --- | --- | --- |
| `"sem candidatos por sobrenome (abreviação/corrupção?)"` | Nenhum candidato: o sobrenome não existe na árvore, nem por prefixo de 3 caracteres | **Conferir a grafia** — abreviação, mojibake no export, ou nome de casada que não existe no GEDCOM 🟢 |
| `"sem sobrenome em comum (filtro anti-falso-positivo)"` | Houve candidato, mas a interseção de sobrenomes ficou **vazia** e não houve acerto de sufixo | Verificar se o match usa **outro sobrenome** (casamento, adoção) ou se o GEDCOM está com o nome incompleto 🟢 |
| `"score insuficiente ou conflito de sobrenome (given=…, final=…, inter=…/…, jacc=…)"` | Houve candidato, mas a aceitação não passou. **O motivo carrega os quatro números** | Decidir **caso a caso** se é a mesma pessoa: os números dizem *quão perto* chegou. É o descarte mais informativo da lista 🟢 |
| `"não encontrado"` (padrão, quando não há motivo específico) | O match não casou e nenhum motivo detalhado foi registrado | Verificar se o **ramo está cadastrado** na árvore — pode ser ausência de dado, não de correspondência 🟢 |

**Consequência de design:** o motivo **não pode ser encurtado nem resumido** na tela. Os quatro números do terceiro motivo são a informação que permite ao operador agir; trocá-los por um rótulo genérico destruiria a utilidade da lista. 🟢

## Dependências

| Dependência | Versão | Como usa | Conf. |
| --- | --- | --- | --- |
| `busca-caminho` (unit) | — | `core/documentary_relationship.py` — caminho, MRCA e dossiê de homônimos — é **compartilhado** pelas duas units; `modules.json` declara `["busca-caminho", "upload-gedcom"]` | 🟢 |
| `upload-gedcom` (unit) | — | A árvore entra **por parâmetro**; a unit não parseia e não publica estado (`ADR-24`) | 🟢 |
| `tela-de-entrada` (unit) | — | Fornece `_arvore_do_formulario` e a lista de CSVs escolhível | 🟢 |
| `ports/` | — | A porta `RegistroDeAnalises` e o adaptador Postgres; a unit **não** conhece `psycopg2` (`ADR-25`, `ADR-27`) | 🟢 |
| **pandas** | 3.0.6 | `read_csv`, agrupamento vetorizado, `attrs` como canal de metadados | 🟢 |
| **thefuzz** | 0.22.1 | `fuzz.ratio`, `token_sort_ratio`, `partial_ratio` | 🟢 |
| **RapidFuzz** | 3.14.6 (transitiva) | **Backend real** do `thefuzz` — decide o matching | 🟢 |
| **python-Levenshtein** | 0.27.5 (transitiva) | Aceleração em C | 🟢 |
| **ged4py** | 0.5.5 | Via `core/registro.py`, que é **cópia literal do oráculo** | 🟢 |
| **psycopg2-binary** | 2.9.13 | **Pinado e ausente do `.venv/`** — por isso o import é preguiçoso e a persistência fica desligada no host | 🔴 |
| Fonte externa | SCP 4.0 (mar/2020, 59.714 envios) | Tabela **embutida** de 27 relações publicadas | 🟢 |

## Decisões de Design Identificadas

| Decisão | Evidência no código | Confiança |
| --- | --- | --- |
| **Separar os três eixos** e confrontá-los sem alterá-los | `core/dna_analysis.py:1-31`; `evidence_comparison.py:8-29` | 🟢 |
| **O DNA não altera o parentesco documental**; conflito vira aviso e causas | `evidence_comparison.py:8-11` | 🟢 |
| **O cM nunca é usado sozinho** — os dois antipadrões são proibidos nominalmente | `core/dna_analysis.py:16-23` | 🟢 |
| **Confronto por sobreposição de faixas**, e não por distância em meioses | `evidence_comparison.py:20-28` | 🟢 |
| **Agregação pelo mais conservador** entre kits | `evidence_comparison.py:225-235` | 🟢 |
| **Chave de evidência é (nome, kit)**; a sentinela tem espaço à esquerda | `genetic_evidence.py:SEM_KIT` | 🟢 |
| **`totals.cm = None`** quando há mais de um kit — o número honesto | `genetic_evidence.py:evidence_for` | 🟢 |
| **cM sem arredondamento no núcleo**; arredondar é só apresentação | `tests/test_formatacao_cm.py`; `ADR-20` | 🟢 |
| **Nenhuma faixa é inventada** quando a fonte não publica; usa-se envoltória por meioses | `relationship_hypotheses.py:meioses_window` | 🟢 |
| **`df.attrs` como canal de metadados**, sem mudar a assinatura de `read_csv_with_fallback` | `csv_ingest.py:170-175` | 🟢 |
| **Quarto critério de desempate: menor `xref_id`** — implementa a decisão humana de 2026-10-05 | `matching.py:116-125` | 🟢 |
| **O cM não decide aceitação**; só influencia o limiar de Jaccard | `matching.py`; teste de caracterização | 🟢 |
| **Cache de índices por análise** — não altera decisão nenhuma, só o custo | `matching.py:27-59` | 🟢 |
| **Limiares literais, sem constantes nomeadas** — deliberado (`ADR-08`) | `matching.py` | 🟡 |
| **Ordem documental-primeiro**, com justificativa medida (71 conexões, 64 sem caminho) | `core/dna_analysis.py:_ordem` | 🟢 |
| A projeção é **pura** e pública, para ser testada **sem banco** | `application/dna_analysis.py:60-63` | 🟢 |
| O pareamento kit ↔ veredito é **por índice**, não por rótulo | `application/dna_analysis.py:129-144` | 🟢 |
| O **papel do nó** é derivado com corte no MRCA; sem MRCA, no penúltimo nó | `application/dna_analysis.py:100-126` | 🟢 |
| A persistência fica **depois e fora** da decisão; falha vira aviso | `application/dna_analysis.py:271-284` | 🟢 |
| O import do driver é **preguiçoso** e nada acontece na construção | `ports/adaptadores.py:243-297` | 🟢 |
| Uma **conexão** e **uma transação** por análise, sem pool | `ports/adaptadores.py:285-297` | 🟢 |
| Tabela de tradução de **funções**, não mapa de classe → constante: sete das nove mensagens congeladas interpolam valores | `application/traducao.py:3-9` | 🟢 |
| As **cinco exceções são irmãs**; `ErroDeDominio(ValueError)` para não reescrever quatro asserções | `core/erros.py:1-14` | 🟢 |
| O **motivo** da recusa continua na exceção; só a apresentação deixou de exibi-lo | `core/erros.py:16-26` | 🟢 |
| **`cm_estimator` fora do fluxo**, sem reexportação de compatibilidade | `cm_estimator.py:1`; a superfície em `core/dna_analysis` **saiu** nesta rodada | 🟢 |

## Estado Interno

**A unit não publica estado de processo.** 🟢

| Estado | Escopo | Observação | Conf. |
| --- | --- | --- | --- |
| `people`, `families`, `graph`, `child_to_family` | por requisição | Entram **por parâmetro**; nenhum módulo de `core/` escreve variável global de dados — a corrida entre threads **deixou de existir** estruturalmente (`ADR-24`) | 🟢 |
| `ged_index`, `surname_index`, `features`, `documental_por_pessoa`, `dossie_por_nome`, resolvedor de diagrama | local da requisição | Caches de deduplicação **dentro** da análise | 🟢 |
| `df` e seus `attrs`, `evidencias`, `results_list`, `skipped_matches` | local da requisição | Transitórios; renderizados e descartados | 🟢 |
| `_REGISTRO` | processo | Guarda **apenas a string de conexão**: não abre conexão, não valida a URL, não toca a rede (`BR-D-83`) | 🟢 |
| `DONO_DO_PROCESSO` | processo | `"unico"`; vira `owner_id` na gravação e **não** filtra nada (`ADR-26`) | 🟢 |

> 🟢 A persistência **é** durável, mas fica **fora** deste estado: ela não é lida por nenhum caminho da análise. Repetir a análise com o mesmo CSV recalcula tudo do zero — e agora **também grava uma segunda linha** no histórico, porque nada deduplica análises repetidas. 🟡

## Observabilidade

| O quê | Onde | Observação |
|-------|------|------------|
| **Nenhum log** | — | A unit não registra nada: nem a análise, nem os descartes, nem a falha de persistência 🔴 |
| **Nenhuma métrica ou trace** | — | Não há contagem de conexões por análise nem tempo de matching 🔴 |
| Aviso de persistência na tela | `application/dna_analysis.py:283-284`, `ports/adaptadores.py:283-284`, `:294` | É a única visibilidade de que o histórico não foi gravado — e ela **não** vai para o log 🟡 |
| `skipped_matches` na tela | `app.py` | A lista auditável dos descartes é, na prática, o instrumento de diagnóstico do operador 🟢 |
| Avisos (`warnings[].code` + `message`) | `genetic_evidence.py`, `documentary_relationship.py` | Canal de diagnóstico de granularidade fina — `state-machines.md` §6 🟢 |

## Riscos e Lacunas

- 🟡 **`L-29` / `P-07` — dado pessoal persistido sem retenção: DECIDIDO em 2026-10-10.** `analysis_person` guarda `xref`, `nome`, `sexo`, `nascimento`, `local_nascimento` e `falecimento` de **todas** as pessoas que a análise tocou — inclusive **pessoas vivas** —, e não há expurgo, retenção nem consentimento. Nem apagar a árvore apaga o retrato: desde que a persistência existe, o dado **sobrevive ao arquivo de origem**. **Decisão humana: o uso do legado com dado de TERCEIROS fica PROIBIDO** — o sistema é ferramenta da própria árvore do operador —, e retenção, expurgo e consentimento passam a **requisito do sistema alvo** (`TM-04`). É a mesma solução que o projeto adotou em 2026-10-05 para os quatro requisitos encaminhados: construir retenção aqui significaria construir o que a Onda 3/5 da migração substitui. ⚠️ **Consequência que a decisão não elimina:** como nada deduplica análises repetidas, cada repetição **multiplica** o dado persistido — e agora isso está declarado, com a trilha de execuções como justificativa.
- 🟡 **`L-28` / `X-05` — não há teste de caminho feliz de INSERT: DECIDIDO em 2026-10-10, e a cobertura remedida dá o número do risco.** Os testes de persistência exercitam a persistência **desabilitada** e **indisponível** por desenho, porque o driver não existe no `.venv`. Erro de SQL, de ordem de FK ou de tipo só apareceria **dentro do contêiner** — que é onde ninguém roda a suíte. **A remedição de cobertura de 2026-10-10 mostra `ports/adaptadores.py` com 73 %, a PIOR do projeto**, exatamente o módulo onde vive `_escrever`. **Decisão humana: criar um ambiente de teste COM o driver** — venv dedicado ou alvo de teste dentro do `docker-compose` —, com a ressalva explícita de **não** instalar o driver no `.venv/` oficial, que é o interpretador da paridade e foi realinhado de propósito em 2026-10-05. Agendado para depois do Passo 4.
- 🔴 **Endogamia e colapso de pedigree não são corrigidos.** O colapso **é detectado** no lado documental (aviso `colapso_de_pedigree`), mas **não altera o veredito**: nesses casos o cM lido é um teto otimista. A endogamia não é nem detectada.
- 🔴 **Faltam justamente as relações mais distantes** (`1C4R`, `1C5R`, `1C6R`, `3C2R`, bisavôs distantes): as 6 não publicadas na 4.0, que é onde o caso real deste repositório cai. A envoltória por meioses mitiga, sem substituir a fonte.
- 🟢→ **`L-24` / `E-05` — o cache de nomes do módulo documental: CONFIRMADO POR EXECUÇÃO em 2026-10-10.** A chave é `(len(people), chaves[0], chaves[-1])`. O experimento provou que duas árvores do **mesmo tamanho** com os **mesmos xrefs extremos** compartilham o índice, e que o dossiê da segunda cita um xref **que não existe nela**, degradando em silêncio. Esta unit **consome** esse dossiê (`BR-D-22` na raiz ambígua e `BR-D-32` na identidade ambígua), então **a contaminação alcança os avisos desta unit** — era `[Verificar]` e deixou de ser. A correção foi **aceita** e será executada depois do Passo 4. Detalhe em `busca-caminho/design.md` § Riscos e `flowcharts/busca-caminho.md` §13.
- 🟡 **`_avaliar_kit` recebe `meioses_documental` e não o usa.** Superfície morta que **convida** a reintroduzir o critério por meioses — que o próprio módulo documenta como inválido. Um parâmetro que existe e não é lido é um convite ao erro futuro, não uma folga inofensiva.
- 🟡 **`INCONCLUSIVO` é o último da ordem de conservadorismo.** Um kit **sem cM utilizável** não rebaixa o resultado quando outro kit é `COMPATIVEL`: a ausência de dado nunca protege contra uma conclusão otimista de outro kit.
- 🟡 **Os quatro estados são também nomes de classe CSS** (`badge estado-{{ status }}`), e **não há teste** que compare o nome do estado com a folha de estilo: renomear um estado quebra a cor sem quebrar a suíte.
- 🟡 **`CAUSAS_POSSIVEL` tem 8 itens, e o catálogo afirma 9** (`code-analysis.md` §4.4, `modules.json` `BR-D-35`). Medido por importação: `[0] + [3:8] + [10:]` = 1 + 5 + 2.
- 🟡 **`COMMON_SURNAMES` — o design de 2026-10-05 estava errado, e a medição explica por quê.** Ele afirmava "15 entradas, 14 efetivas". O literal é um **`set` com `souza` duas vezes**: 16 literais, **15 efetivas** — o que confere com o catálogo. Contar em execução dá 15 únicos porque o `set` colapsa a duplicata **na construção**; só a leitura do fonte revela os 16. Correção registrada.
- 🟡 **O número `0,33` do relaxamento de Jaccard é heurística sem calibração**, confirmado por você em 2026-10-05 como "um chute que funcionou na prática".
- 🟡 **A fonte não publica mediana**, e a coluna "Range" **exclui 1 % dos envios** — a janela do confronto herda as duas limitações. Quem reimplementar **não deve** inventar mediana nem tratar a faixa como intervalo observado completo.
- 🟡 **Cobertura de exportadores de CSV:** a regex de ID `[A-Z]{2}\d{7}` é específica de um padrão (GEDmatch), sem prova de generalidade.
- 🟡 **O caminho indireto não passa pela checagem de plausibilidade de datas**, que existe só no caminho direto.
- 🟡 **`ErroDeDominio` herda de `ValueError`.** Consequência já declarada no código: nenhum `except ValueError` pode passar a distinguir casos pela **mensagem** — a distinção é sempre pelo **tipo**.
- 🟡 **Divergência de versão de `RapidFuzz`** entre o pin e o `.venv` pode mudar o matching sem que uma linha de código mude (`L-19`, `adrs/13`).
- 🟡 **Duas análises iguais gravam duas linhas.** Nada no histórico deduplica uma análise repetida: o mesmo CSV com o mesmo `root_name` produz um segundo `dna_analysis`. Não há decisão registrada sobre isso. **[Verificar]**
- 🟢 **A divergência viva de 2026-10-05 está fechada.** O determinismo do desempate foi implementado (`BR-D-63`) e congelado por `tests/test_characterization_matching.py` nas duas direções.
- 🟢 **A persistência não pode bloquear a análise**, e isso é testado: os dois avisos (falha na projeção e falha na gravação) chegam à tela sem impedir o resultado.

---

*Gerado pelo Reversa-Writer em 2026-10-10 (re-extração). Substitui a versão de 2026-10-05.*

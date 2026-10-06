# Unit `analise-dna` — Design Técnico

> Unit do tipo **endpoint** — `POST /` com `action=dna_analysis`.
> Re-extração de **2026-10-05** (nível **Completo**). Substitui o design de 2026-09-30, que descrevia um pipeline único de matching **sem** as três etapas separadas e **sem** o confronto.
> Escala de confiança: 🟢 CONFIRMADO | 🟡 INFERIDO | 🔴 LACUNA

---

## Interface

### Endpoint HTTP

| Método | Caminho | Entrada | Saída | Status codes |
| --- | --- | --- | --- | --- |
| `POST` | `/` | `action=dna_analysis`, `gedcom_filename`, `root_name`, arquivo no campo `matches_csv` | `index.html` com `dna_results`, `skipped_matches`, `message`, `success` | `200` sempre — erro de negócio vira mensagem na tela; `413` se o corpo exceder 16 MB 🟢 |

### Símbolos

| Símbolo | Arquivo:linha | Assinatura | Retorno | Observação |
| --- | --- | --- | --- | --- |
| `dna_analysis` | `dna_analysis.py:83` | `(csv_path: str, root_name: str)` | `(results_sorted, skipped, message)` | **Lança `ValueError`** em raiz ausente ou colunas faltantes 🟢 |
| `_montar_diagrama` | `dna_analysis.py:56` | `(documentary, root_id, pid)` | `str \| None` | Mermaid do caminho **documental**, ou `None` 🟢 |
| `_observacoes` | `dna_analysis.py:65` | `(documentary, evidence, comparison, extra)` | `list[str]` | Deduplicada, preservando a ordem de origem 🟢 |
| `_ordem` | `dna_analysis.py:226` | `(resultado)` | `tuple` | `(0 se tem caminho senão 1, -cM)` 🟢 |
| `read_csv_with_fallback` | `csv_ingest.py:140` | `(path)` | `DataFrame` com `attrs` | `utf-8` → `latin-1`, separador, preâmbulo, linha torta 🟢 |
| `detectar_separador` | `csv_ingest.py:76` | `(path, encoding)` | `str` | Empate fica com a vírgula 🟢 |
| `localizar_cabecalho` | `csv_ingest.py:93` | `(path, sep, encoding)` | `int` (0-based) | Três guardas contra falso positivo 🟢 |
| `linhas_irregulares` | `csv_ingest.py:126` | `(path, sep, encoding, cabecalho)` | `list[int]` (1-based) | Números de linha das linhas tortas 🟢 |
| `detect_columns` | `csv_ingest.py:185` | `(df)` | `(name, cm, match_id, email)` | Detecção por papel 🟢 |
| `aggregate_matches` | `csv_ingest.py:198` | `(df, name_col, cm_col, match_id_col, match_email_col)` | `DataFrame` | Agrupa por `_group_key` e **soma** cM 🟢 |
| `build_genetic_evidence` | `genetic_evidence.py:115` | `(df)` | `(evidencias, avisos)` | Agrupa por **(nome, kit)** 🟢 |
| `detect_segment_columns` | `genetic_evidence.py:46` | `(df)` | `dict` de colunas por papel | SNPs, cromossomo, início, fim, fonte, kit, e-mail 🟢 |
| `evidence_for` | `genetic_evidence.py:214` | `(dossie, avisos, kit_key)` | `dict` de evidência | **Nunca soma kits** 🟢 |
| `possible_relationships` | `relationship_hypotheses.py:161` | `(total_cm)` | `dict` (lista + confiança + leitura) | Sempre lista 🟢 |
| `hypotheses_for_evidence` | `relationship_hypotheses.py:208` | `(evidence)` | `list[dict]` | Um bloco por kit 🟢 |
| `row_for_key` | `relationship_hypotheses.py:106` | `(key: str)` | `dict \| None` | Faixa publicada para a relação exata 🟢 |
| `meioses_window` | `relationship_hypotheses.py:120` | `(meioses: int)` | `dict \| None` | Envoltória das publicadas com o mesmo número de meioses 🟢 |
| `compare` | `evidence_comparison.py:150` | `(documentary, hypotheses, evidence)` | `dict` (estado + causas + detalhe) | **O confronto** 🟢 |
| `_avaliar_kit` | `evidence_comparison.py:75` | `(bloco, janela, meioses_documental)` | `dict` (status + note) | Estado de **um** kit 🟢 |
| `_janela_do_documental` | `evidence_comparison.py:116` | `(documentary)` | `(janela, motivo)` | Faixa exata, ou envoltória, ou nada 🟢 |
| `build_ged_indexes` | `matching.py:27` | `()` | `(ged_index, surname_index, features)` | Cache de atributos normalizados 🟢 |
| `match_candidates` | `matching.py:62` | `(match_name, cm_value, ged_index, surname_index, features)` | `(candidate_pids, reason)` | Scoring e aceitação 🟢 |
| `norm_name` | `name_normalization.py:52` | `(s)` | `str` | NFKD, sem diacríticos, minúsculas 🟢 |
| `split_name_pt` | `name_normalization.py:77` | `(s)` | `(given, surnames, suffixes)` | Decomposição pt-BR 🟢 |
| `soft_prefix_jaccard` | `name_normalization.py:106` | `(a, b, min_pref=4, min_len=2)` | `float` | Compara conjuntos de prefixos de 4 quando há token curto 🟢 |
| `documentary_relationship` | `documentary_relationship.py:436` | `(a_id, b_id, homonyms=None)` | `dict` | **Nunca lê cM** 🟢 |
| `homonym_dossier` | `documentary_relationship.py:205` | `(name_query, similar_ids)` | `dict` | Dossiê de ambiguidade 🟢 |
| `get_relationships_by_cm` | `cm_estimator.py:53` | `(cm_value)` | `list[str]` | **Legado fora do fluxo** 🟢 |

## Fluxo Principal

### Camada de rota (`app.py:131-159`)

1. `app.py:131-136` — recupera `gedcom_filename`, valida presença e **forma**, e resolve o caminho em disco. 🟢
2. `app.py:137` — **re-parseia o GEDCOM** e reconstrói o grafo, **antes** de ramificar por `action`. 🟢
3. `app.py:141-142` — sem `matches_csv` ou com nome vazio → `"Por favor, carregue o arquivo CSV de matches."`, preservando `all_names`. 🟢
4. `app.py:144-146` — grava o CSV sob chave de conteúdo (**sem** validação de conteúdo). 🟢
5. `app.py:148` — `dna_analysis_flow(matches_path, root_name)`. 🟢
6. `app.py:149-157` — renderiza com `dna_results`, `skipped_matches`, `message`, `success=True`. 🟢
7. `app.py:158-159` — exceção → `"Ocorreu um erro: {e}"`, `success=False`. 🟢

### Núcleo — orquestração das três etapas (`dna_analysis.py:83-236`)

1. `:90-93` — resolve a raiz por **substring case-insensitive** sobre `get_name`; sem resultado → `ValueError`. Usa `root_person_ids[0]`. 🟢
2. `:95-97` — `read_csv_with_fallback` e leitura dos `attrs` (`linhas_ignoradas`, `linhas_antes_do_cabecalho`). 🟢
3. `:110-123` — `detect_columns`; faltando nome ou cM → `ValueError` **acionável** com separador, colunas encontradas e as linhas tortas. 🟢
4. `:125-141` — monta os avisos do arquivo (preâmbulo e linhas descartadas). 🟢
5. `:143` — **Etapa 2**: `build_genetic_evidence(df)` → evidências por (nome, kit) + avisos. 🟢
6. `:144` — `build_ged_indexes()` → índices e cache de features. 🟢
7. `:146-153` — dossiê de homônimos da **raiz**; se ambígua, avisa quantos e quais. 🟢
8. `:166-171` — para cada **(nome, kit)**: `match_candidates` com o **cM do kit**. 🟢
9. `:173-180` — sem candidatos → descarte com o `reason`. 🟢
10. `:187-196` — para cada candidato, **Etapa 1**: `documentary_relationship` (com o dossiê em cache por nome); escolhe o **primeiro que tiver caminho**; sem nenhum, usa o primeiro da lista. 🟢
11. `:199-200` — **Etapa 3a**: `evidence_for` + `hypotheses_for_evidence`. 🟢
12. `:201` — **Etapa 3b**: `compare(documentary, hypotheses, evidence)`. 🟢
13. `:204-218` — monta o item de resultado, com o diagrama do caminho **documental**. 🟢
14. `:226-230` — ordena por `(tem caminho, −cM)`. 🟢
15. `:231-235` — mensagem `"{n} conexões encontradas. {m} descartadas."`; **sem resultados**, anexa os avisos do arquivo. 🟢

> **O dossiê de homônimos é calculado uma vez por nome** (`:160-164`), e não uma vez por candidato: a varredura custa cerca de 35 mil nomes, e recalculá-la por candidato seria o gargalo da análise. 🟢

### Leitura tolerante do CSV (`csv_ingest.py`)

| Passo | Regra | Linha |
| --- | --- | --- |
| Encoding | `utf-8`; na falha `latin-1` | `:147-154` |
| Separador | Conta `,` `;` TAB `\|` no cabeçalho; **maior vence**, empate fica com a vírgula | `:76-90` |
| Cabeçalho | Número de campos **modal** entre linhas com ≥ 2 campos, exigindo frequência ≥ 2, primeira linha divergente e posição dentro das 10 primeiras | `:93-123` |
| Preâmbulo | Linhas antes do cabeçalho são reportadas à parte e **não** contam como linha torta | `:134-137` |
| Linha torta | No erro de tokenização, **relê** com `on_bad_lines="skip"` e registra os números de linha em `df.attrs` | `:157-173` |
| Erro final | `ValueError` em português listando as tentativas e o que conferir | `:177-182` |

### Evidência genética por (nome, kit) (`genetic_evidence.py`)

1. `:59-76` — detecta as colunas por papel, incluindo a coluna de **kit** (nome casando `kit|gedmatch|teste|test` com > 50 % dos valores em `[A-Z]{1,3}\d{4,8}`; senão, > 30 % em `[A-Z]{2}\d{7}`). 🟢
2. `:134-140` — sem coluna de kit, o **e-mail** assume o papel; sem ambos, a chave é `SEM-KIT`. 🟢
3. `:157-161` — acumula `total_cm` **sem `round`**. 🟢
4. `:193-200` — ordena segmentos por cM decrescente e cromossomos por tamanho. 🟢
5. `:203-204` — maior segmento abaixo de **15 cM** → `weak_segment` + aviso. 🟢
6. `:175-183` — mais de um kit para o mesmo nome → aviso `multiplos_kits`, **cada kit separado**. 🟢

### Confronto (`evidence_comparison.py:150-244`)

1. `:161-171` — o dicionário nasce com `status = "INCONCLUSIVO"` e `observations` acumulando os avisos relevantes do documental (`data_impossivel`, `colapso_de_pedigree`, `caminhos_multiplos`). 🟢
2. `:177-181` — sem DNA → `INCONCLUSIVO`, registrando que o documental vale por si. 🟢
3. `:183-190` — com DNA mas **sem caminho** → `INCONCLUSIVO`: nenhum caminho é inventado a partir do DNA. 🟢
4. `:192-201` — identidade ambígua → `INCONCLUSIVO`, listando os registros. 🟢
5. `:203-208` — sem faixa publicada **nem** janela por meioses → `INCONCLUSIVO`. 🟢
6. `:210-214` — registra `method` (`scp40:<nome>` ou `scp40:meioses=<n>`) e `expected_range`; se a janela veio da envoltória, a nota explica por quê. 🟢
7. `:216-223` — avalia **cada kit** com `_avaliar_kit` e registra `per_kit`. 🟢
8. `:225-235` — estado final = **o mais conservador**, e o rol de causas conforme o estado. 🟢

## Fluxos Alternativos

| Condição | Comportamento | Conf. |
| --- | --- | --- |
| Sem GEDCOM carregado, ou arquivo removido | Erro antes de qualquer análise (`app.py:131-136`) | 🟢 |
| Sem CSV | `"Por favor, carregue o arquivo CSV de matches."`, preservando a lista de nomes | 🟢 |
| Raiz não encontrada | `ValueError` → `"Ocorreu um erro: Seu nome 'X' não foi encontrado no GEDCOM."` | 🟢 |
| Raiz ambígua | Usa o primeiro registro e **avisa** a contagem e os ids | 🟢 |
| Colunas de nome/cM ausentes | `ValueError` acionável com separador, colunas e linhas tortas | 🟢 |
| CSV em `latin-1` | Recuo de encoding | 🟢 |
| CSV com preâmbulo | Cabeçalho localizado; aviso com a linha usada | 🟢 |
| CSV com linhas tortas | Análise prossegue; aviso com contagem e números de linha | 🟢 |
| Match sem candidato | Descarte com `reason` (`"sem candidatos por sobrenome (abreviação/corrupção?)"` ou `"sem sobrenome em comum (filtro anti-falso-positivo)"` ou `"score insuficiente ou conflito de sobrenome (...)"`) | 🟢 |
| Candidato aceito sem caminho documental | **Não é descartado.** Entra no resultado com as quatro seções; o confronto responde `INCONCLUSIVO` | 🟢 |
| Mais de um kit, `total_cm` de um deles ausente | Aquele kit é `INCONCLUSIVO`; o estado final segue o mais conservador | 🟢 |
| Nenhum resultado | Avisos do arquivo anexados à mensagem | 🟢 |
| `cM ≤ 0` ou não numérico no CSV | `possible_relationships` devolve **lista vazia** e confiança `indeterminada` — **não** o literal de relação distante | 🟢 |

## Discartes — o que o operador faz com cada motivo

> **Decisão de produto de 2026-10-05** (`questions.md#pergunta-5`): a lista de descartados **não é só auditoria** — você **age** sobre ela. Isso eleva `RF-23` de `Should` para `Must` e transforma cada motivo em um **convite à ação**, com o que conferir.
>
> O motivo **já traz os números** da decisão (`given`, `final`, `inter`, `jacc`) justamente para permitir esse julgamento. O que faltava era declarar a ação esperada.

| Motivo (literal) | O que significa | Ação esperada do operador |
| --- | --- | --- |
| `"sem candidatos por sobrenome (abreviação/corrupção?)"` | O nome do CSV não produziu **nenhum** candidato: o sobrenome não existe na árvore, nem por prefixo de 3 caracteres | **Conferir a grafia** — abreviação, mojibake no export, ou nome de casada que não existe no GEDCOM 🟢 |
| `"sem sobrenome em comum (filtro anti-falso-positivo)"` | Houve candidato por sobrenome, mas a interseção de sobrenomes ficou **vazia** e não houve acerto de sufixo | Verificar se o match usa **outro sobrenome** (casamento, adoção) ou se o GEDCOM está com o nome incompleto 🟢 |
| `"score insuficiente ou conflito de sobrenome (given=…, final=…, inter=…/…, jacc=…)"` | Houve candidato, mas a aceitação não passou. **O motivo carrega os quatro números** da decisão | Decidir **caso a caso** se é a mesma pessoa: os números dizem *quão perto* chegou. É o descarte mais informativo da lista 🟢 |
| `"não encontrado"` (padrão, quando não há motivo específico) | O match não casou e nenhum motivo detalhado foi registrado | Verificar se o **ramo está cadastrado** na árvore — pode ser ausência de dado, não de correspondência 🟢 |

**Consequência de design:** o motivo **não pode ser encurtado nem resumido** na tela. Os quatro números do terceiro motivo são a informação que permite ao operador agir; trocá-los por um rótulo genérico destruiria a utilidade da lista.

| Dependência | Versão | Como usa | Conf. |
| --- | --- | --- | --- |
| **pandas** | 3.0.3 | `read_csv`, agrupamento vetorizado, `attrs` como canal de metadados | 🟢 |
| **thefuzz** | 0.22.1 | `fuzz.ratio`, `token_sort_ratio`, `partial_ratio` | 🟢 |
| **RapidFuzz** | 3.14.5 (transitiva) | **Backend real** do `thefuzz` — decide o matching | 🟢 |
| **python-Levenshtein** | 0.27.3 (transitiva) | Aceleração em C | 🟢 |
| Unit `upload-gedcom` | — | Consome `people`, `families`, `graph`, `child_to_family` | 🟢 |
| Unit `busca-caminho` | — | Usa `path_finding`, `family_navigation`, `documentary_relationship` e `mermaid_render` | 🟢 |
| `utils/text_cleaning` | — | Autoridade única de limpeza de nome (ADR-07) | 🟢 |
| `utils/number_format` | — | Formatação de cM **só** na tela (ADR-20) | 🟢 |
| Fonte externa | SCP 4.0 (mar/2020, 59.714 envios) | Tabela **embutida** de 27 relações publicadas | 🟢 |

## Decisões de Design Identificadas

| Decisão | Evidência no código | Confiança |
| --- | --- | --- |
| **Separar os três eixos** e confrontá-los sem alterá-los | `dna_analysis.py:1-31`; `evidence_comparison.py:8-29` | 🟢 |
| **O DNA não altera o parentesco documental**; conflito vira aviso e causas | `evidence_comparison.py:8-11` | 🟢 |
| **O cM nunca é usado sozinho** — os dois antipadrões são proibidos nominalmente | `dna_analysis.py:16-23` | 🟢 |
| **Rótulo "Relacionamento Provável (DNA)" removido**; agora é "Possibilidades de parentesco pelo DNA" | `dna_analysis.py:22-23` | 🟢 |
| **Confronto por sobreposição de faixas**, e não por distância em meioses | `evidence_comparison.py:89-105` | 🟢 |
| **Agregação pelo mais conservador** entre kits | `evidence_comparison.py:225-227` | 🟢 |
| **Chave de evidência é (nome, kit)**; nunca somar kits | `genetic_evidence.py:154` | 🟢 |
| **`totals.cm = None`** quando há mais de um kit — o número honesto | `genetic_evidence.py:232-234` | 🟢 |
| **cM sem arredondamento no núcleo**; arredondar é só apresentação | `genetic_evidence.py:162-166`; ADR-20 | 🟢 |
| **Nenhuma faixa é inventada** quando a fonte não publica; usa-se envoltória por meioses | `relationship_hypotheses.py:96-137` | 🟢 |
| **`df.attrs` como canal de metadados**, para não quebrar a assinatura de `read_csv_with_fallback` | `csv_ingest.py:170-174` | 🟢 |
| **`map(str)` no lugar de `astype(str)`** — em coluna de objeto, `astype` preserva `NaN` como `float` e o `demojibake` estoura | `csv_ingest.py:204-222` | 🟢 |
| **Cache de índices por análise** — não altera nenhuma decisão, só o custo | `matching.py:27-59` | 🟢 |
| **Limiares literais, sem constantes nomeadas** — deliberado (ADR-08) | `matching.py:140-155` | 🟢 |
| **Ordem documental-primeiro**, com justificativa medida (71 conexões, 64 sem caminho) | `dna_analysis.py:220-228` | 🟢 |
| **`cm_estimator` fora do fluxo**, reexportado por compatibilidade | `cm_estimator.py:1`, `:21`; `dna_analysis.py:25-30` | 🟢 |
| **Desempate em QUATRO critérios**: os três do legado (sobrenomes em comum, prenome, score) **mais o menor `xref_id`** como critério final, acrescentado em 2026-10-05 | `matching.py:96-111` | 🟢 |

## Estado Interno

| Estado | Escopo | Observação | Conf. |
| --- | --- | --- | --- |
| `people`, `families`, `graph`, `child_to_family` | global do processo | Produzidos pelo upload; **lidos**, não escritos | 🟢 |
| `ged_index`, `surname_index`, `features` | local da requisição | Reconstruídos a cada análise | 🟢 |
| `df`, `evidencias` | local da requisição | DataFrames e dicionários transitórios | 🟢 |
| `documental_por_pessoa`, `dossie_por_nome` | local da requisição | Caches de deduplicação **dentro** da análise | 🟢 |
| `results_list`, `skipped_matches` | local da requisição | Renderizados e descartados | 🟢 |

> **Nada é persistido.** Repetir a análise com o mesmo CSV recalcula tudo do zero, inclusive o re-parse do GEDCOM. 🔴 Não há decisão de negócio registrada sobre isso (`L-21`).

## Observabilidade

- **Nenhum `logging`, métrica ou trace é emitido.** 🔴
- A lista de `skipped_matches` funciona como **auditoria funcional**: é a única visibilidade do motivo de um match não aparecer. 🟢
- Os avisos (`warnings[].code` + `message`) são o canal de diagnóstico de granularidade fina — ver `state-machines.md` §6. 🟢
- A instrumentação de paridade (oráculo, harness, fixtures) vive em `_reversa_sdd/` e **não faz parte da aplicação**. 🟢

## Riscos e Lacunas

- 🟢 **`RF-26` (determinismo) — DECIDIDO E IMPLEMENTADO em 2026-10-05.** O laço percorre um `set` (`matching.py:73`, `:91`), cuja ordem muda por `PYTHONHASHSEED`. A decisão de 2026-09-30 (retomada em `questions.md#pergunta-1`) foi corrigir **o legado**: foi acrescentado um **quarto critério** — em empate triplo, vence o **menor `xref_id`** lexicográfico (`:107-110`). **É a segunda divergência deliberada do legado e a primeira que muda comportamento:** fora do empate triplo, nada muda. Verificado por **2 testes novos** em `tests/test_characterization_matching.py`. 🟢
- 🔴 **A tabela do SCP 4.0 não atende endogamia nem colapso de pedigree**, e o código registra isso. O colapso **é detectado** no lado documental (aviso `colapso_de_pedigree`), mas **não altera o veredito** — nesses casos o cM lido é um teto otimista (`L-17`, `adrs/21`). 🟡
- 🔴 **Faltam as relações mais distantes** na versão 4.0 (`1C4R`, `1C5R`, `1C6R`, `3C2R` e os bisavós distantes), que é onde o caso real deste repositório cai. A envoltória por meioses mitiga, sem substituir a fonte (`L-18`). 🟡
- 🔴 **A fonte não publica mediana** e a faixa **exclui 1 % dos envios**. Quem reimplementar **não deve** inventar mediana nem tratar a faixa como intervalo observado completo. 🟡
- 🟡 **`L-14` FECHADA em 2026-10-05 — o `0,33` é heurística, não calibração.** Confirmado por você: foi um **chute que funcionou na prática**. A decisão de manter o relaxamento continua 🟢 (2026-08-03); o que muda é a **autoridade do número**, que passa a ser declarado **ajustável** em vez de literal com aparência de medição. Quem reimplementar pode tratá-lo como parâmetro. 🟡
- 🟡 **Cobertura de exportadores de CSV**: a regex de ID `[A-Z]{2}\d{7}` é específica de um padrão (GEDmatch), sem prova de generalidade. 🟡
- 🟡 **O caminho indireto não passa pela checagem de plausibilidade de datas**, que existe só no caminho direto. 🟡
- 🟡 **`COMMON_SURNAMES` tem `souza` duas vezes** (15 entradas, 14 efetivas) — inofensivo em `set`, mas impreciso para quem contar. 🟢
- 🟡 **Divergência de versão do `RapidFuzz`** entre o pin e o `.venv` pode mudar o matching sem uma linha de código mudar (`L-19`, `adrs/13`). 🟢
- 🟡 **Os limiares de aceitação não têm ponto único de mudança**: estão como literais dentro de cinco ramos. Ajustar a generosidade do matching exige editar cada um. 🟢

---

*Gerado pelo Reversa-Writer em 2026-10-05 (re-extração, nível completo).*

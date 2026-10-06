# Análise de Código — analisador-genealogico

> Nível de documentação: **Completo** (`state.json` → `doc_level`)
> Re-extração de 2026-10-05. Substitui a análise de 2026-09-30, que descrevia a raiz `analisador-genealogico/` e o pacote `reconstructed/`.
> Snapshot da versão substituída: `.reversa/snapshots/2026-10-05-pre-reextracao/`
> Escala de confiança: 🟢 CONFIRMADO | 🟡 INFERIDO | 🔴 LACUNA
> ⚠️ **Contagens e citações de linha atualizadas pela revisão de 2026-10-05.** As correções de código decididas nas respostas às perguntas deslocaram linhas em `app.py` (+5), `matching.py` (+6) e `genetic_evidence.py` (+5), e somaram **+16 linhas a `src/`**. **Todas as citações de linha deste artefato foram reescritas e reconferidas contra o código atual.**
> Fluxogramas por módulo: `_reversa_sdd/flowcharts/` · Dicionário de dados: `_reversa_sdd/data-dictionary.md`

---

## 1. Visão Geral da Escavação

| Unidade funcional | Arquivos analisados | Linhas | Regras catalogadas |
| --- | --- | ---: | ---: |
| `upload-gedcom` | `parsers/gedcom_parser.py`, `core/gedcom_state.py`, `utils/validate.py`, `utils/text_cleaning.py` | 312 | 20 |
| `analise-dna` | `core/dna_analysis.py`, `genetic_evidence.py`, `relationship_hypotheses.py`, `evidence_comparison.py`, `matching.py`, `name_normalization.py`, `cm_estimator.py`, `parsers/csv_ingest.py` | 1577 | 62 |
| `busca-caminho` | `core/path_search.py`, `path_finding.py`, `family_navigation.py`, `documentary_relationship.py`, `reporting/mermaid_render.py` | 1275 | 36 |
| Transversal | `app.py`, `utils/number_format.py` | 321 | 16 (as BR-U de porta de entrada e formatação, contadas em §2.5) |
| **Total** | 22 módulos em `src/` | **3489** | **118** |

> A atribuição de arquivo a unidade é do Arqueólogo e segue a responsabilidade declarada na docstring de cada módulo. Arquivos transversais aparecem na unidade que os consome com mais peso e estão marcados como tal.

**Método de contagem:** `[System.IO.File]::ReadAllLines` (conta linhas em branco). A causa raiz de contagens truncadas em artefatos anteriores é o uso de `Get-Content | Measure-Object -Line`, que as ignora.

**Correção de rota em relação à extração anterior.** A análise de 2026-09-30 descrevia três unidades apoiadas em `reconstructed/` com 1086 linhas. O código de hoje tem **3489 linhas** de Python em `src/`, quatro pacotes por responsabilidade e uma capacidade inteira — o confronto GEDCOM × DNA — que não existia em nenhuma spec. O que segue foi extraído do código atual, e não herdado.

---

## 2. Unidade `upload-gedcom`

### 2.1 Escopo e arquivos

| Arquivo | Linhas | Responsabilidade |
| --- | ---: | --- |
| `src/parsers/gedcom_parser.py` | 69 | Traduzir o GEDCOM em registros e no grafo; substituir o estado. |
| `src/core/gedcom_state.py` | 52 | Registro do estado do processo e acesso aos registros. |
| `src/utils/validate.py` | 105 | Toda a decisão sobre o que pode ser gravado: nome visível, chave e conteúdo. |
| `src/utils/text_cleaning.py` | 86 | Autoridade única da limpeza de mojibake. |
| *(transversal)* `src/app.py` | 267 | Ramo `upload_gedcom` da rota, guarda de upload e resolução do caminho armazenado. |

Fluxo completo: `flowcharts/upload-gedcom.md`.

### 2.2 Funções principais

| Função | Arquivo:linha | Parâmetros | Retorno | Confiança |
| --- | --- | --- | --- | --- |
| `index` | `app.py:113` | — (lê `request`) | HTML renderizado (ou 413) | 🟢 |
| `_pasta_uploads` | `app.py:42` | — | `str` (caminho absoluto da pasta) | 🟢 |
| `_guardar_upload` | `app.py:75` | `arquivo`, `kind: str` | `(caminho, motivo)` | 🟢 |
| `_resolver_caminho_armazenado` | `app.py:99` | `nome_recebido` | `str \| None` | 🟢 |
| `_requisicao_grande` | `app.py:66` | `_erro` | `(HTML, 413)` | 🟢 |
| `load_gedcom_and_build_graph` | `gedcom_parser.py:50` | `file_path: str` | `list[str]` (nomes ordenados) | 🟢 |
| `build_graph_from_parser` | `gedcom_parser.py:18` | `people_dict: dict`, `parser` | `(nx.Graph, dict)` | 🟢 |
| `ref_id` | `gedcom_state.py:33` | `val` | `str` | 🟢 |
| `get_name` | `gedcom_state.py:38` | `person` | `str` | 🟢 |
| `nome_visivel_seguro` | `validate.py:40` | `nome_original` | `str` | 🟢 |
| `chave_de_armazenamento` | `validate.py:68` | `conteudo: bytes` | `str` (16 hex) | 🟢 |
| `nome_do_arquivo_armazenado` | `validate.py:73` | `chave: str`, `nome_original` | `str` | 🟢 |
| `chave_recebida_e_valida` | `validate.py:78` | `nome_recebido` | `bool` | 🟢 |
| `validar_conteudo_gedcom` | `validate.py:90` | `conteudo: bytes` | `str \| None` (motivo ou aceite) | 🟢 |
| `strip_bad_utf` | `text_cleaning.py:37` | `s` | `str` | 🟢 |
| `demojibake` | `text_cleaning.py:56` | `s` | `str` | 🟢 |
| `formatar_cm` | `number_format.py:17` | `valor` | `str` | 🟢 |
| `formatar_inteiro` | `number_format.py:41` | `valor` | `str` | 🟢 |

### 2.3 Algoritmos e lógica não trivial

**Derivação da chave de armazenamento.** `hashlib.sha256(conteudo).hexdigest()[:16]`. É derivação por conteúdo, e não UUID aleatório, por uma razão de contrato: o formulário devolve `gedcom_filename` no POST seguinte, então a mesma árvore reenviada **precisa** produzir a mesma chave. Um valor aleatório quebraria a continuidade entre as requisições. 🟢

**Forma fechada da chave.** `^[0-9a-f]{16}__[A-Za-z0-9._-]+$`. A validação é por forma, e não por lista negra: como a expressão exclui `/`, `\` e `..`, um valor manipulado **não tem como** escapar da pasta de upload. É a defesa do critério 5 do `BUG-20260929-QMLY`. 🟢

**Validação de conteúdo estreita e deliberada.** Apenas o cabeçalho `0 HEAD` é verificado, após remover um BOM UTF-8 e espaços à esquerda. A gramática do GEDCOM fica com o `ged4py`, que já a implementa. Comandos de controle não são escapados: o byte NUL causa recusa explícita. 🟢

**Preservação da extensão no nome visível.** `rpartition(".")` divide o nome em raiz e extensão; a extensão é **preservada**, não fixada em `.ged`. Fixá-la renomeava o CSV de DNA para `<...>.csv.ged` e quebrava a análise — regressão do `BUG-20260929-QMLY`, corrigida em 2026-10-02. Um nome sem extensão nenhuma recebe `.ged`. 🟢

**Construção do grafo bidirecional.** Um `nx.Graph` recebe um nó por pessoa (`type="person"`, `label` do nome formatado) e um nó por família (`type="family"`, `label="Familia"`), com arestas pessoa↔família para HUSB, WIFE e cada CHIL. Em paralelo, `child_to_family` mapeia filho → **lista** de famílias, porque uma pessoa pode ser filha em mais de uma. 🟢

**Assimetria de substituição do estado.** `people`, `families` e `child_to_family` são mutados *in place* (`clear()` + `update()`), para que os bindings importados no topo pelos outros módulos continuem apontando para o objeto vivo. `graph` é **reatribuído** — e é exatamente por isso que quem o consome o importa **dentro da função**. O contador `versao` é incrementado a cada carga; ele existe porque `id()` não muda com mutação *in place*, e índices derivados (nome normalizado → ids) precisam de um sinal de invalidação que o rebind não fornece. 🟢

**Limpeza de mojibake em dois estágios.** `strip_bad_utf` aplica um mapa de pares conhecidos e depois troca por espaço tudo o que não case com `[\w\sÁ-ú'-]`. `demojibake` só tenta o round-trip `latin1 → utf-8` quando há indício de mojibake na string, e **descarta o resultado** se ele ainda contiver caractere de substituição, `Ã` ou `A�` — preferindo o original a um palpite pior. 🟢

### 2.4 Estruturas de dados

| Estrutura | Onde | Forma | Confiança |
| --- | --- | --- | --- |
| `people` | `gedcom_state.py:20` | `dict[str, registro ged4py INDI]` indexado por `xref_id` | 🟢 |
| `families` | `gedcom_state.py:21` | `dict[str, registro ged4py FAM]` indexado por `xref_id` | 🟢 |
| `graph` | `gedcom_state.py:22` | `networkx.Graph` não direcionado, bipartido pessoa↔família | 🟢 |
| `child_to_family` | `gedcom_state.py:23` | `dict[str, list[str]]` — filho → famílias onde aparece como CHIL | 🟢 |
| `versao` | `gedcom_state.py:30` | `int`, contador de carregamentos (sinal de invalidação) | 🟢 |
| Mapa de mojibake | `text_cleaning.py:41-50` | `dict[str, str]` | 🟢 |
| Tupla de retorno do upload | `app.py:75` | `(caminho_completo, motivo)` — `motivo` é `None` no sucesso | 🟢 |

Dicionário de dados completo (campos, tipos, obrigatoriedade e valores padrão): `data-dictionary.md`.

### 2.5 Regras de negócio catalogadas

| ID | Regra | Local | Confiança |
| --- | --- | --- | --- |
| BR-U-01 | O upload só ocorre em `POST` com `action=upload_gedcom`; qualquer outro `action` cai nos ramos de análise ou de busca. | `app.py:115-116` | 🟢 |
| BR-U-02 | Sem o campo `gedcom` na requisição: `Nenhum arquivo GEDCOM enviado.` | `app.py:117-118` | 🟢 |
| BR-U-03 | Com `filename` vazio: `Nenhum arquivo selecionado.` | `app.py:120-121` | 🟢 |
| BR-U-04 | O conteúdo é lido **inteiro** e validado **antes** de qualquer gravação em disco. | `app.py:85-88` | 🟢 |
| BR-U-05 | GEDCOM aceitável = após remover BOM UTF-8 e espaços à esquerda, começa com `0 HEAD`. | `validate.py:97-104` | 🟢 |
| BR-U-06 | Conteúdo vazio é recusado com o motivo `arquivo vazio`. | `validate.py:97-98` | 🟢 |
| BR-U-07 | Conteúdo com byte NUL é recusado com o motivo `conteudo binario`. | `validate.py:99-100` | 🟢 |
| BR-U-08 | A chave de armazenamento é o sha256 do conteúdo truncado em 16 hexadecimais: mesmo conteúdo, mesma chave. | `validate.py:68-70` | 🟢 |
| BR-U-09 | O nome final é `<chave>__<nome visível>`; o nome do cliente **nunca** compõe o caminho. | `validate.py:73-75` | 🟢 |
| BR-U-10 | No nome visível, `/`, `\` e NUL viram `_`; acentos, espaços e a extensão original são preservados. | `validate.py:40-65` | 🟢 |
| BR-U-11 | Nome visível vazio (ou só pontos) vira `arvore.ged`; nome sem extensão recebe `.ged`. | `validate.py:52-65` | 🟢 |
| BR-U-12 | Arquivo já existente com a mesma chave **não** é reescrito. | `app.py:93-95` | 🟢 |
| BR-U-13 | O valor devolvido pelo armazenamento é o **caminho completo**; quem lê depois usa exatamente o que foi escrito. | `app.py:75-96` | 🟢 |
| BR-U-14 | `gedcom_filename` recebido do formulário é aceito apenas na forma `<16 hex>__<nome>`; fora disso: `Erro: Arquivo 'X' não existe mais.` | `app.py:131-136`, `validate.py:78-87` | 🟢 |
| BR-U-15 | Requisição sem `gedcom_filename`: `Erro: Arquivo GEDCOM não encontrado.` | `app.py:132-133` | 🟢 |
| BR-U-16 | Corpo de requisição acima de 16 MB é recusado pelo Flask com 413 e a mensagem `Arquivo maior que o limite de 16 MB.` | `app.py:32`, `app.py:65-72` | 🟢 |
| BR-U-17 | Falha de parse vira `Erro ao processar GEDCOM: <exceção>` na tela; nada é persistido. | `app.py:128-129` | 🟢 |
| BR-U-18 | Família sem `xref_id` é ignorada; arestas só são criadas para nós existentes no grafo. | `gedcom_parser.py:26-27`, `:40-46` | 🟢 |
| BR-U-19 | A lista de nomes devolvida é **ordenada** e tem exatamente um item por pessoa carregada. | `gedcom_parser.py:68` | 🟢 |
| BR-U-20 | `get_name` devolve string vazia quando o registro tem `Name` mas o formato resulta vazio; o literal `Sem Nome` só aparece quando não há `name`. | `gedcom_state.py:38-52` | 🟢 |

### 2.6 Constantes, parâmetros e configuração

| Nome | Valor | Onde | Observação |
| --- | --- | --- | --- |
| `CABECALHO_GEDCOM` | `"0 HEAD"` | `validate.py:26` | Declaração que abre todo GEDCOM válido. |
| `_SEPARADOR` | `"__"` | `validate.py:31` | Separador entre chave e nome visível. |
| `_FORMATO_CHAVE` | `^[0-9a-f]{16}__[A-Za-z0-9._-]+$` | `validate.py:32` | Forma fechada; é a defesa contra escape de caminho. |
| `BOM_UTF8` | `b"\xef\xbb\xbf"` | `validate.py:37` | Removido uma única vez, no início. |
| `MAX_CONTENT_LENGTH` | `16 * 1024 * 1024` | `app.py:32` | Teto de corpo de requisição. |
| `UPLOAD_FOLDER` | `"uploads"` | `app.py:39` | Resolvido por `_pasta_uploads()`, ancorado no arquivo do app. |
| `ANALISADOR_UPLOAD_FOLDER` | *(sem padrão)* | `app.py:54` | Variável de ambiente que redireciona a pasta; usada pelos testes. |
| `app.secret_key` | `'f@milyse@rch_dna_edition_v16'` | `app.py:22` | **Dívida herdada**: segredo embutido no código. |
| Mapa de mojibake | 18 entradas | `text_cleaning.py:41-50` | Ver observação em §2.7. |
| `CASAS` | `2` | `number_format.py:14` | Teto de casas decimais na exibição (não é número fixo). |

### 2.7 Observações e lacunas

* 🔴 **Segredo embutido.** `app.secret_key` é literal no código desde o legado. Em sistema sem autenticação o impacto é baixo, mas o valor está versionado.
* 🟡 **Mapa de mojibake com chave duplicada e mapeamento identidade.** Medido por AST: **18 entradas, 17 chaves efetivas**. `"A�"` aparece duas vezes (a segunda prevalece; ambas apontam para `ç`) e `"Ã": "Ã"` é um no-op.
* 🟢 **A faixa `Á-ú` na expressão de limpeza é redundante — e isso é bom.** Verificado por execução: `\w` é Unicode-aware em Python 3, então `ñ`, `Ñ`, `ý`, `ÿ`, `ö`, `ç` e `ã` sobrevivem por `\w` independentemente da faixa. O que a substituição remove é pontuação e símbolo, trocados por espaço (medido: `a+b;c(d)e[f]` → `a b c d e f`, **com espaço final**).
* 🟡 **`validar_conteudo_gedcom` é chamada apenas para `kind == "gedcom"`** (`app.py:86`). O CSV de DNA **não** tem validação de conteúdo — só de forma de nome. É coerente com o contrato herdado (o CSV é lido de forma tolerante por `csv_ingest`), mas significa que um CSV arbitrário é gravado em disco antes de qualquer verificação.
* 🟢 **A pasta de upload é criada no import**, a partir da **mesma** função que a resolve (`app.py:62`), de modo que o diretório criado e o procurado não podem divergir.
* 🟢 **Nada é persistido entre requisições**: o GEDCOM é re-parseado a cada `POST`, e o estado vive no processo.

---

## 3. Unidade `analise-dna`

Esta é a unidade que **mais cresceu** desde a extração anterior. O que era um fluxo único de matching passou a ser uma orquestração de três etapas independentes, e é a razão de existir desta re-extração.

### 3.1 Escopo e arquivos

| Arquivo | Linhas | Responsabilidade |
| --- | ---: | --- |
| `src/parsers/csv_ingest.py` | 227 | Ler o CSV tolerando encoding, separador, preâmbulo e linha torta; achar as colunas; agregar cM por match. |
| `src/core/genetic_evidence.py` | 264 | Evidência genética descritiva por (pessoa, kit). Não conhece o GEDCOM. |
| `src/core/relationship_hypotheses.py` | 229 | cM → possibilidades, pela tabela publicada do Shared cM Project 4.0. |
| `src/core/evidence_comparison.py` | 247 | Confronto entre documento e genética: quatro estados, com o porquê. |
| `src/core/dna_analysis.py` | 250 | Orquestra as três etapas e monta o payload da tela. |
| `src/core/matching.py` | 162 | Índices do GEDCOM e decisão de aceitação de candidatos. |
| `src/core/name_normalization.py` | 122 | Normalização, decomposição de nomes e o vocabulário que isso usa. |
| `src/core/cm_estimator.py` | 65 | **Legado fora do fluxo**, mantido só como superfície de compatibilidade. |

Fluxo completo: `flowcharts/analise-dna.md`.

### 3.2 Funções principais

| Função | Arquivo:linha | Parâmetros | Retorno | Confiança |
| --- | --- | --- | --- | --- |
| `dna_analysis` | `dna_analysis.py:83` | `csv_path: str`, `root_name: str` | `(results_sorted, skipped, message)` | 🟢 |
| `_montar_diagrama` | `dna_analysis.py:56` | `documentary`, `root_id`, `pid` | `str \| None` (Mermaid) | 🟢 |
| `_observacoes` | `dna_analysis.py:65` | `documentary`, `evidence`, `comparison`, `extra` | `list[str]` deduplicada | 🟢 |
| `read_csv_with_fallback` | `csv_ingest.py:140` | `path` | `DataFrame` (com `attrs`) | 🟢 |
| `detectar_separador` | `csv_ingest.py:76` | `path`, `encoding` | `str` | 🟢 |
| `localizar_cabecalho` | `csv_ingest.py:93` | `path`, `sep`, `encoding` | `int` (índice 0-based) | 🟢 |
| `linhas_irregulares` | `csv_ingest.py:126` | `path`, `sep`, `encoding`, `cabecalho` | `list[int]` (1-based) | 🟢 |
| `detect_columns` | `csv_ingest.py:185` | `df` | `(name, cm, match_id, email)` | 🟢 |
| `aggregate_matches` | `csv_ingest.py:198` | `df`, `name_col`, `cm_col`, `match_id_col`, `match_email_col` | `DataFrame` | 🟢 |
| `build_genetic_evidence` | `genetic_evidence.py:115` | `df` | `(evidencias, avisos)` | 🟢 |
| `detect_segment_columns` | `genetic_evidence.py:46` | `df` | `dict` de colunas por papel | 🟢 |
| `evidence_for` | `genetic_evidence.py:214` | `dossie`, `avisos`, `kit_key` | `dict` de evidência | 🟢 |
| `possible_relationships` | `relationship_hypotheses.py:161` | `total_cm` | `dict` (lista + confiança + leitura) | 🟢 |
| `hypotheses_for_evidence` | `relationship_hypotheses.py:208` | `evidence` | `list[dict]` (uma por kit) | 🟢 |
| `row_for_key` | `relationship_hypotheses.py:106` | `key: str` | `dict \| None` | 🟢 |
| `rows_by_meioses` | `relationship_hypotheses.py:115` | `meioses: int` | `list[dict]` | 🟢 |
| `meioses_window` | `relationship_hypotheses.py:120` | `meioses: int` | `dict \| None` | 🟢 |
| `compare` | `evidence_comparison.py:150` | `documentary`, `hypotheses`, `evidence` | `dict` (estado + causas + detalhe) | 🟢 |
| `_avaliar_kit` | `evidence_comparison.py:75` | `bloco`, `janela`, `meioses_documental` | `dict` (status + note) | 🟢 |
| `_janela_do_documental` | `evidence_comparison.py:116` | `documentary` | `(janela, motivo)` | 🟢 |
| `build_ged_indexes` | `matching.py:27` | — | `(ged_index, surname_index, features)` | 🟢 |
| `match_candidates` | `matching.py:62` | `match_name`, `cm_value`, `ged_index`, `surname_index`, `features` | `(candidate_pids, reason)` | 🟢 |
| `norm_name` | `name_normalization.py:52` | `s` | `str` (forma comparável) | 🟢 |
| `split_name_pt` | `name_normalization.py:77` | `s` | `(given, surnames, suffixes)` | 🟢 |
| `surname_core_tokens` | `name_normalization.py:66` | `name`, `keep_last=3` | `(base, suffixes)` | 🟢 |
| `soft_prefix_jaccard` | `name_normalization.py:106` | `a`, `b`, `min_pref=4`, `min_len=2` | `float` | 🟢 |
| `get_relationships_by_cm` | `cm_estimator.py:53` | `cm_value` | `list[str]` | 🟢 |

### 3.3 Algoritmos e lógica não trivial

**Leitura tolerante em quatro frentes.** `read_csv_with_fallback` tenta `utf-8` e, na falha, `latin-1`; detecta o separador pelo cabeçalho entre `,`, `;`, TAB e `|`; localiza a linha do cabeçalho quando há preâmbulo; e, no erro de tokenização do pandas, **relê** o arquivo com `on_bad_lines="skip"` em vez de derrubar a análise. O que foi descartado não desaparece: vai para `df.attrs["linhas_ignoradas"]`, com os números de linha, e a tela publica a contagem. A escolha de `attrs` como canal é deliberada — trocar o retorno por tupla quebraria `dna_analysis` e o `__all__` que os reexporta. 🟢

**Localização do cabeçalho com três guardas.** O cabeçalho é a primeira linha cujo número de campos é o **modal entre as linhas com 2 ou mais campos**, e a decisão exige frequência ≥ 2, primeira linha com número diferente do modal, e a linha dentro das primeiras 10. As guardas existem contra dois falsos positivos medidos: um arquivo **sem** cabeçalho não pode perder sua primeira linha de dados, e um arquivo que não é tabela (um GEDCOM com uma linha contendo vírgula) não pode eleger essa linha como cabeçalho e esconder o problema real. 🟢

**Agrupamento de cM por chave composta.** `_group_key` = nome normalizado (com `demojibake`) + `" | "` + cauda, onde a cauda é o id em maiúsculas, ou o e-mail normalizado, ou nada. A montagem é vetorizada: o nome é normalizado **uma vez por nome distinto**, e não por linha. `map(str)` é obrigatório no lugar de `astype(str)` porque, em coluna de objeto, o `astype` do pandas preserva `NaN` como `float` e o `demojibake` estoura. 🟢

**Chave de evidência é (nome, kit), nunca só nome.** Duas linhas com o mesmo nome e kits diferentes são **duas** evidências. Sem coluna de kit e sem e-mail, o agrupamento cai para o nome e a evidência sai marcada com o aviso `kit_ausente` — sem isso, dois laboratórios distintos virariam um match só, com cM somado. Quando há mais de um kit e não se sabe qual é a pessoa do GEDCOM, `totals.cm` é `None`: é o número honesto. 🟢

**Soma de cM sem arredondamento.** `registrada["total_cm"] + cm`, sem `round`. O contrato está congelado em `tests/test_formatacao_cm.py`: o float somado permanece exato (`19.200000000000003`) e o arredondamento acontece **só** na formatação de saída, porque a paridade contra o oráculo exige igualdade exata. 🟢

**Tradução de cM em possibilidades.** 27 relações publicadas do Shared cM Project 4.0, com `meioses` (número de saltos pai-filho) como a grandeza que o cM mede. Relações diferentes com o mesmo número de meioses se sobrepõem — é por isso que a resposta é **lista**. A confiança (`indeterminada`, `baixa`, `muito baixa`) é heurística **do projeto**, declarada como tal no próprio código: a fonte não define grau de confiança; quanto mais relações contêm o valor, menos o valor discrimina. 🟢

**Nada é inventado quando a fonte não publica.** Seis relações não são publicadas na 4.0 (`1C4R`, `1C5R`, `1C6R`, `3C2R`, 2º bisavô e 3º bisavô) — justamente as mais distantes. Em vez de inventar número, a janela passa a ser a **envoltória** das relações publicadas com o mesmo número de meioses; sem relação publicada naquele número, não há janela e o confronto fica INCONCLUSIVO. 🟢

**Máquina de estados do confronto.** Dado o par documental + genético: cM dentro da janela → `COMPATIVEL`; fora dela → `POSSIVEL` **apenas** quando alguma relação publicada que contém o valor tem faixa que **se sobrepõe** à janela documental (as distribuições se tocam e o cM não separa as leituras); caso contrário → `CONFLITANTE`. Distância em meioses **não** serve de critério aqui, e o código registra por quê: irmãos (1613–3488) e primos de 1º grau com uma remoção (102–980) estão a uma meioses de distância e mesmo assim não se sobrepõem. Sem DNA, sem caminho ou com identidade ambígua → `INCONCLUSIVO`. Com mais de um kit, o estado final é o **mais conservador** pela ordem `CONFLITANTE > POSSIVEL > COMPATIVEL > INCONCLUSIVO`. 🟢

**Scoring do matching preservado do legado.** `score = round(0.55·token_sort_ratio + 0.25·partial_ratio + 0.20·similaridade_do_prenome + bônus_de_sobrenome, 2)`, com `bônus = 8·interseção − 4·sobrenomes_comuns`. A seleção do melhor candidato é lexicográfica: mais sobrenomes em comum, depois melhor prenome, depois melhor score. Sobre esse score incidem cinco ramos de aceitação, um filtro anti-falso-positivo (sem sobrenome em comum e sem sufixo → descarta) e uma penalidade para tokens do meio do nome ausentes no GEDCOM. **Nenhum limiar foi alterado nesta extração.** 🟢

**Cache de índices por análise.** `build_ged_indexes` calcula `norm_name` e `surnames_set` uma vez por pessoa, porque o laço de candidatos os renormalizava cerca de 7 vezes por candidato, a cada match, para um valor que não depende do CSV. Medido no código: `norm_name` ≈ 41 µs e `surnames_set` ≈ 72 µs. A otimização não altera nenhuma decisão. 🟢

### 3.4 Estruturas de dados

| Estrutura | Onde | Forma | Confiança |
| --- | --- | --- | --- |
| `ged_index` | `matching.py:36` | `dict[str, list[str]]` — nome normalizado → ids | 🟢 |
| `surname_index` | `matching.py:37` | `dict[str, list[str]]` — sobrenome → ids | 🟢 |
| `features` | `matching.py:38` | `dict[str, dict]` com `norm`, `given_tokens`, `surnames` (set), `surnames_list`, `tokens` (set) | 🟢 |
| `evidencias` | `genetic_evidence.py:128` | `dict[str, dict[str, dict]]` — nome normalizado → kit → evidência | 🟢 |
| Evidência de kit | `genetic_evidence.py:154-161` | `kit`, `person_name_csv`, `source`, `total_cm`, `segments`, `records_used` (+ derivados: `segment_count`, `largest_segment_cm`, `snps_total`, `snps_largest_segment`, `chromosomes`, `method`, `weak_segment`) | 🟢 |
| Segmento | `genetic_evidence.py:168-174` | `chromosome`, `start`, `end`, `cm`, `snps` | 🟢 |
| Aviso | `genetic_evidence.py:182` | `{code, message}` — códigos: `multiplos_kits`, `kit_ausente`, `segmento_fraco`, `sem_evidencia` | 🟢 |
| `df.attrs` | `csv_ingest.py:170-174` | `separador`, `encoding`, `linhas_antes_do_cabecalho`, `linhas_ignoradas`, `erro_de_leitura` | 🟢 |
| Bloco de hipótese | `relationship_hypotheses.py:198-205` | `total_cm`, `possible_relationships`, `confidence`, `confidence_note`, `interpretation`, `reference` (+ `kit`, `segment_count`, `largest_segment_cm`) | 🟢 |
| Linha SCP 4.0 | `relationship_hypotheses.py:64-92` | tupla `(key, nome_en, nome_pt, meioses, average, range_low, range_high)` | 🟢 |
| Confronto | `evidence_comparison.py:161-171` | `status`, `label`, `message`, `causes`, `per_kit`, `method`, `expected_range`, `detail`, `observations` | 🟢 |
| Resultado da análise | `dna_analysis.py:204-218` | `match_name`, `csv_name`, `cm`, `kit`, `text_path`, `mermaid_data`, `documentary`, `genetic_evidence`, `hypotheses`, `comparison`, `observations`, `warnings` | 🟢 |
| Descartado | `dna_analysis.py:174-179` | `csv_name`, `kit`, `cm`, `motivo` | 🟢 |

### 3.5 Regras de negócio catalogadas

*Faixas: **01–11** leitura e agrupamento do CSV · **12–20** evidência genética · **21–26** possibilidades · **27–35** confronto · **36–43** orquestração · **44–53** matching · **54–62** normalização de nomes.*

| ID | Regra | Local | Confiança |
| --- | --- | --- | --- |
| BR-D-01 | O CSV é lido primeiro como `utf-8`; na falha, como `latin-1`. | `csv_ingest.py:147` | 🟢 |
| BR-D-02 | O separador é decidido pelo cabeçalho, entre vírgula, ponto e vírgula, TAB e barra vertical: vence a maior contagem; empate fica com a vírgula. | `csv_ingest.py:46`, `:88-90` | 🟢 |
| BR-D-03 | O cabeçalho é a primeira linha cujo número de campos é o modal entre linhas com 2 ou mais campos, exigindo frequência ≥ 2, primeira linha divergente e posição dentro das 10 primeiras linhas. | `csv_ingest.py:93-123` | 🟢 |
| BR-D-04 | Linhas antes do cabeçalho são preâmbulo, reportadas à parte; não contam como linha torta. | `csv_ingest.py:134-137` | 🟢 |
| BR-D-05 | Linha com número de campos diferente do cabeçalho **não** derruba a análise: o arquivo é relido descartando essas linhas, e elas são reportadas. | `csv_ingest.py:157-167`, `:173` | 🟢 |
| BR-D-06 | Se nenhuma tentativa produz tabela utilizável, o erro é um `ValueError` em português que lista as tentativas e diz o que conferir. | `csv_ingest.py:177-182` | 🟢 |
| BR-D-07 | Os nomes das colunas são normalizados com `strip`. | `csv_ingest.py:169` | 🟢 |
| BR-D-08 | Coluna de nome: `Name`, `MatchedName` ou `Nome`. Coluna de cM: `cM`, `TotalCM` ou `Total cM`. | `csv_ingest.py:186-187` | 🟢 |
| BR-D-09 | Coluna de ID de match: a primeira em que mais de 30% dos valores casam `[A-Z]{2}\d{7}`. | `csv_ingest.py:190-192` | 🟢 |
| BR-D-10 | Coluna de e-mail: a **última** cujo nome contém `mail`. | `csv_ingest.py:193-194` | 🟢 |
| BR-D-11 | O agrupamento soma cM por `nome normalizado + cauda`, com a cauda sendo id, e-mail ou nada. | `csv_ingest.py:204-222` | 🟢 |
| BR-D-12 | A evidência é agrupada por **(nome, kit)**; linhas com o mesmo nome e kits diferentes são evidências separadas. | `genetic_evidence.py:154` | 🟢 |
| BR-D-13 | Sem coluna de kit, o e-mail assume o papel de kit; sem ambos, a chave é `SEM-KIT` e sai o aviso `kit_ausente`. | `genetic_evidence.py:139-145`, `:189-196` | 🟢 |
| BR-D-14 | Mais de um kit para o mesmo nome gera o aviso `multiplos_kits`, e nenhum total é somado entre kits. | `genetic_evidence.py:180-188` | 🟢 |
| BR-D-15 | O cM acumulado **não** é arredondado; o arredondamento é só de apresentação. | `genetic_evidence.py:162-166` | 🟢 |
| BR-D-16 | A coluna de kit é a que tem nome casando `kit\|gedmatch\|teste\|test` com mais de 50% dos valores em `[A-Z]{1,3}\d{4,8}`; senão, a que tem mais de 30% em `[A-Z]{2}\d{7}`. | `genetic_evidence.py:71-81` | 🟢 |
| BR-D-17 | O maior segmento abaixo de **15 cM** marca a evidência como fraca e gera o aviso `segmento_fraco`. | `genetic_evidence.py:31`, `:208-209`, `:243-250` | 🟢 |
| BR-D-18 | Os segmentos são ordenados por cM decrescente; os cromossomos, por tamanho e depois por valor. | `genetic_evidence.py:198`, `:204-205` | 🟢 |
| BR-D-19 | Sem kit informado, `evidence_for` reúne os kits **sem somar** cM e deixa `totals.cm` como `None` quando há mais de um. | `genetic_evidence.py:232-234` | 🟢 |
| BR-D-20 | Sem evidência genética, o retorno é `available: False` com o aviso `sem_evidencia`. | `genetic_evidence.py:221-230` | 🟢 |
| BR-D-21 | cM vira **lista** de possibilidades pela tabela do Shared cM Project 4.0; nunca um parentesco único. | `relationship_hypotheses.py:161-205` | 🟢 |
| BR-D-22 | As candidatas são ordenadas por distância da média (e, em empate, pelo nome). | `relationship_hypotheses.py:184` | 🟢 |
| BR-D-23 | A confiança da lista é heurística do projeto: 0 candidatas → indeterminada; 1 a 3 → baixa; 4 a 6 → muito baixa; mais de 6 → muito baixa. | `relationship_hypotheses.py:140-158` | 🟢 |
| BR-D-24 | Valor sem cobertura publicada devolve lista vazia e a leitura de que **isso não descarta parentesco**. | `relationship_hypotheses.py:193-196` | 🟢 |
| BR-D-25 | Seis relações não são publicadas na 4.0 e não recebem número inventado: `1C4R`, `1C5R`, `1C6R`, `3C2R`, 2º bisavô/avó, 3º bisavô/avó. | `relationship_hypotheses.py:96-103` | 🟢 |
| BR-D-26 | Sem faixa publicada para a relação exata, a janela é a envoltória das relações publicadas com o mesmo número de meioses. | `relationship_hypotheses.py:120-137` | 🟢 |
| BR-D-27 | O confronto devolve sempre um de quatro estados: `COMPATIVEL`, `POSSIVEL`, `CONFLITANTE`, `INCONCLUSIVO`, cada um com mensagem própria. | `evidence_comparison.py:34-51` | 🟢 |
| BR-D-28 | cM dentro da janela esperada → `COMPATIVEL`. | `evidence_comparison.py:85-87` | 🟢 |
| BR-D-29 | cM fora da janela → `POSSIVEL` quando alguma relação publicada que contém o valor tem faixa que se sobrepõe à janela; caso contrário → `CONFLITANTE`. | `evidence_comparison.py:89-113` | 🟢 |
| BR-D-30 | Sem evidência genética → `INCONCLUSIVO`, com o registro de que o parentesco documental continua valendo por si. | `evidence_comparison.py:177-181` | 🟢 |
| BR-D-31 | Com DNA mas sem caminho documental → `INCONCLUSIVO`: nenhum caminho é inventado a partir do DNA. | `evidence_comparison.py:183-190` | 🟢 |
| BR-D-32 | Identidade ambígua → `INCONCLUSIVO`, listando os registros homônimos. | `evidence_comparison.py:192-201` | 🟢 |
| BR-D-33 | Sem faixa publicada (nem por meioses) → `INCONCLUSIVO`, dizendo que o parentesco documental segue registrado mas não é confrontável. | `evidence_comparison.py:203-208` | 🟢 |
| BR-D-34 | Com mais de um kit, o estado final é o mais conservador na ordem `CONFLITANTE > POSSIVEL > COMPATIVEL > INCONCLUSIVO`. | `evidence_comparison.py:225-238` | 🟢 |
| BR-D-35 | `CONFLITANTE` recebe o rol completo de 12 causas possíveis; `POSSIVEL` recebe um subconjunto de 9. | `evidence_comparison.py:55-72`, `:232-235` | 🟢 |
| BR-D-36 | A raiz é resolvida por substring do nome, sem diferenciar maiúsculas; não encontrada → `Seu nome 'X' não foi encontrado no GEDCOM.` | `dna_analysis.py:90-92` | 🟢 |
| BR-D-37 | Raiz ambígua usa o **primeiro** registro e avisa quantos e quais são. | `dna_analysis.py:146-153` | 🟢 |
| BR-D-38 | O matching recebe o cM **do kit**, nunca a soma de kits diferentes. | `dna_analysis.py:170-171` | 🟢 |
| BR-D-39 | Entre os candidatos, é escolhido o primeiro que tenha caminho documental; se nenhum tiver, o primeiro da lista. | `dna_analysis.py:194-196` | 🟢 |
| BR-D-40 | O dossiê de homônimos é calculado uma vez por nome, e não uma vez por candidato. | `dna_analysis.py:160-164` | 🟢 |
| BR-D-41 | A ordem de apresentação é: primeiro os que têm caminho documental, depois cM decrescente. | `dna_analysis.py:226-230` | 🟢 |
| BR-D-42 | A mensagem final tem a forma `N conexões encontradas. M descartadas.` | `dna_analysis.py:231` | 🟢 |
| BR-D-43 | Sem nenhum resultado, os avisos do arquivo são anexados à mensagem, porque não há cartão na tela onde eles apareçam. | `dna_analysis.py:232-235` | 🟢 |
| BR-D-44 | O matching exato é por `norm_name` sobre o índice de nomes do GEDCOM. | `matching.py:64-65` | 🟢 |
| BR-D-45 | Sem acerto exato, o candidato é buscado por sobrenome; sem nenhum, por prefixo de 3 letras dos sobrenomes do CSV. | `matching.py:69-84` | 🟢 |
| BR-D-46 | `score = 0.55·token_sort_ratio + 0.25·partial_ratio + 0.20·similaridade_do_prenome + (8·interseção − 4·sobrenomes_comuns)`, arredondado em 2 casas. | `matching.py:99-101` | 🟢 |
| BR-D-47 | O melhor candidato é escolhido por: mais sobrenomes em comum, depois melhor prenome, depois melhor score. | `matching.py:107-112` | 🟢 |
| BR-D-48 | Sem sobrenome em comum e sem sufixo coincidente, o candidato é descartado (filtro anti-falso-positivo). | `matching.py:121-124` | 🟢 |
| BR-D-49 | Com 2 ou mais sobrenomes no CSV, exige-se Jaccard de prefixo ≥ 0,50 — e ≥ 0,33 quando o cM é ≥ 150 e o prenome não é genérico. | `matching.py:130-136` | 🟢 |
| BR-D-50 | Prenome genérico exige pelo menos 2 sobrenomes em comum; prenome não genérico exige pelo menos 1. | `matching.py:126-128` | 🟢 |
| BR-D-51 | Aceitação por cinco ramos alternativos, com limiares explícitos de `given`, `score`, interseção e Jaccard. | `matching.py:140-149` | 🟢 |
| BR-D-52 | Ramo adicional: prefixo de sobrenome do CSV coincidindo com sobrenome do GEDCOM e `given ≥ 90`, `score ≥ 86`, interseção ≥ 1. | `matching.py:151-155` | 🟢 |
| BR-D-53 | Tokens do meio do nome ausentes no GEDCOM exigem `score ≥ 96` e `given ≥ 92` para manter a aceitação; o motivo da recusa é registrado. | `matching.py:157-166` | 🟢 |
| BR-D-54 | `norm_name`: limpa mojibake, decompõe NFKD, remove diacríticos, troca `/` e pontuação por espaço, minúsculas e colapsa espaços. | `name_normalization.py:52-59` | 🟢 |
| BR-D-55 | `STOP_WORDS` = `de`, `da`, `do`, `das`, `dos`, `e`. | `name_normalization.py:22` | 🟢 |
| BR-D-56 | `GENERIC_GIVENS` = 20 prenomes comuns (com variantes acentuadas). | `name_normalization.py:25-29` | 🟢 |
| BR-D-57 | `SURNAME_SUFFIXES` = `filho`, `neto`, `junior`, `júnior`, `sobrinho`. | `name_normalization.py:32` | 🟢 |
| BR-D-58 | `COMMON_SURNAMES` = 15 sobrenomes únicos; `souza` aparece duas vezes na lista literal. | `name_normalization.py:35-38` | 🟢 |
| BR-D-59 | `SURNAME_EQUIV` unifica `netto→neto` e `gouvea`/`gouvêa`/`gouvéia→gouveia`. | `name_normalization.py:41-46` | 🟢 |
| BR-D-60 | O prenome é o primeiro token que não é stop word nem genérico; os sobrenomes são os **últimos 3** tokens úteis, sem genéricos, com equivalências aplicadas; sufixos são separados. | `name_normalization.py:66-83` | 🟢 |
| BR-D-61 | `soft_prefix_jaccard` compara conjuntos de prefixos de 4 caracteres quando algum lado tem token curto (≤ 4) ou terminando em ponto. | `name_normalization.py:106-122` | 🟢 |
| BR-D-62 | `get_relationships_by_cm` (legado) devolve **lista**; cM ≤ 0 ou não numérico devolvem lista vazia; o literal de relação distante só aparece para positivo fora de todas as faixas. | `cm_estimator.py:53-65` | 🟢 |

### 3.6 Constantes, parâmetros e configuração

| Nome | Valor | Onde | Observação |
| --- | --- | --- | --- |
| `SEPARADORES` | vírgula, ponto e vírgula, TAB, barra vertical | `csv_ingest.py:46` | A ordem importa no empate: a vírgula é o padrão do GEDmatch. |
| `LIMITE_DE_PREAMBULO` | `10` | `csv_ingest.py:51` | Teto de linhas examinadas antes do cabeçalho. |
| `LIMITE_SEGMENTO_FRACO` | `15.0` | `genetic_evidence.py:31` | **Critério do projeto**, não da fonte. |
| Regex de kit | `[A-Z]{2}\d{7}` (estreito) · `[A-Z]{1,3}\d{4,8}` (largo) · nome casando `kit\|gedmatch\|teste\|test` | `genetic_evidence.py:41-43` | O largo só vale para coluna cujo nome fala de kit. |
| `SCP40_ROWS` | 27 relações | `relationship_hypotheses.py:64-92` | Tabela publicada do Shared cM Project 4.0. |
| `SCP40_NOT_PUBLISHED` | 6 relações | `relationship_hypotheses.py:96-103` | Lista para dizer "não há faixa publicada" em vez de inventar. |
| `SCP40_META` | versão 4.0, março/2020, 59.714 envios | `relationship_hypotheses.py:48-58` | Fonte declarada, com a definição de "faixa" (1% removido nas pontas). |
| `CAUSAS_POSSIVEIS` | 12 itens | `evidence_comparison.py:55-68` | Rol de causas para o operador considerar; não é diagnóstico automático. |
| `STATUS_LABEL` | 4 rótulos em português | `evidence_comparison.py:34-39` | `COMPATIVEL`, `POSSIVEL`, `CONFLITANTE`, `INCONCLUSIVO`. |
| Pesos do score | `0.55` / `0.25` / `0.20` | `matching.py:101` | Herdados do legado; não alterados nesta extração. |
| Bônus de sobrenome | `+8.0` por interseção, `−4.0` por sobrenome comum | `matching.py:100` | Idem. |
| Limiar de cM no Jaccard | `150` | `matching.py:134` | Abaixo disso o limiar fica em 0,50. |
| `STOP_WORDS`, `GENERIC_GIVENS`, `SURNAME_SUFFIXES`, `COMMON_SURNAMES`, `SURNAME_EQUIV`, `SHORT_KEEP` | ver BR-D-55 a BR-D-59 | `name_normalization.py:22-49` | Vocabulário de domínio do matching. |
| `SHARED_CM_DATA` | 9 faixas escritas à mão | `cm_estimator.py:40-50` | **Legado fora do fluxo**, sem fonte verificável (decisão humana de 2026-09-30). |

### 3.7 Observações e lacunas

* 🟡 **A fonte do Shared cM 4.0 não publica mediana**, e o código registra isso: existe `average`, não existe `median`. Quem reimplementar não deve inventar mediana a partir das faixas.
* 🟡 **A coluna "Range" da fonte exclui 1% dos envios** (0,5% em cada ponta). O código declara que a faixa **não** é o intervalo observado completo — e a janela do confronto herda essa limitação.
* 🔴 **Endogamia e colapso de pedigree não são corrigidos.** A própria fonte declara que as estatísticas "não atendem colapso de pedigree ou endogamia". O valor lido é, portanto, um teto otimista nesses casos. O confronto lista "colapso de pedigree" e "endogamia" entre as causas possíveis de conflito, mas não os detecta.
* 🟡 **Faltam justamente as relações mais distantes** (`1C4R`, `1C5R`, `1C6R`, `3C2R`, bisavôs distantes), que é onde o caso real deste repositório costuma cair. O tratamento por envoltória de meioses mitiga, sem substituir a fonte.
* 🟡 **`COMMON_SURNAMES` tem uma duplicata literal** (`souza`), então são 15 entradas e 14 sobrenomes efetivos. Inofensivo (é um `set`), mas é imprecisão de leitura para quem contar as linhas.
* 🟡 **`LIMITE_SEGMENTO_FRACO` é heurística do projeto apresentada ao lado de números publicados.** O código pede que a tela a apresente como critério do projeto — a verificação dessa apresentação é da interface, não deste módulo.
* 🟢 **`cm_estimator` não é consultado pelo fluxo nem pela interface.** Confirmado por varredura de imports: quem o importa é o `__all__` do `dna_analysis`, o harness de paridade e a suíte de testes.
* 🟢 **O `ValueError` de colunas ausentes é acionável de propósito**: diz o separador usado, as colunas encontradas, as linhas divergentes e a causa provável — antes, o operador via o erro cru do pandas em inglês.

---

## 4. Unidade `busca-caminho`

### 4.1 Escopo e arquivos

| Arquivo | Linhas | Responsabilidade |
| --- | ---: | --- |
| `src/core/documentary_relationship.py` | 576 | Parentesco **documental** completo: caminho, ancestral comum, graus, homônimos, caminhos múltiplos, colapso de pedigree e evidência de cada salto. |
| `src/reporting/mermaid_render.py` | 289 | Emissão do diagrama Mermaid e o contrato de escape do rótulo. |
| `src/core/path_search.py` | 219 | Fachada do fluxo de busca: resolve pessoas, escolhe entre homônimos, decide direto × indireto. |
| `src/core/family_navigation.py` | 106 | Resolução de pessoa por nome e navegação de parentesco (pais, cônjuges, casamento). |
| `src/core/path_finding.py` | 85 | Os dois algoritmos: BFS bidirecional por pais e caminho curto no grafo de famílias. |

Fluxo completo: `flowcharts/busca-caminho.md`.

### 4.2 Funções principais

| Função | Arquivo:linha | Parâmetros | Retorno | Confiança |
| --- | --- | --- | --- | --- |
| `path_search` | `path_search.py:126` | `person1_name: str`, `person2_name: str` | `(path_result, msg, success)` | 🟢 |
| `_candidatos` | `path_search.py:74` | `nome`, `ids_do_legado` | `(dossie, candidatos)` | 🟢 |
| `_homonimos` | `path_search.py:92` | `person1_name`, `person2_name`, `p1_ids`, `p2_ids` | `dict` | 🟢 |
| `documentary_relationship` | `documentary_relationship.py:436` | `a_id`, `b_id`, `homonyms` | `dict` | 🟢 |
| `documentary_label` | `documentary_relationship.py:290` | `deg_a: int`, `deg_b: int` | `dict` (key, label, meioses) | 🟢 |
| `person_summary` | `documentary_relationship.py:127` | `person_id` | `dict` (ficha) | 🟢 |
| `homonym_dossier` | `documentary_relationship.py:205` | `name_query`, `similar_ids` | `dict` | 🟢 |
| `hop_evidence` | `documentary_relationship.py:233` | `child_id`, `parent_id` | `dict` | 🟢 |
| `find_all_common_ancestors` | `documentary_relationship.py:408` | `a_id`, `b_id`, `max_depth=12`, `limit=12` | `list[dict]` | 🟢 |
| `parse_year` | `documentary_relationship.py:58` | `date_value` | `int \| None` | 🟢 |
| `birth_date` / `death_date` | `documentary_relationship.py:84`, `:88` | `pid` | `str \| None` | 🟢 |
| `get_children` | `documentary_relationship.py:112` | `person_id` | `list[str]` | 🟢 |
| `normalizar` | `documentary_relationship.py:150` | `nome: str` | `str` | 🟢 |
| `find_person_by_name` | `family_navigation.py:21` | `name_query` | `list[str]` | 🟢 |
| `get_parents` | `family_navigation.py:29` | `person_id` | `list[str]` | 🟢 |
| `get_spouses` | `family_navigation.py:51` | `person_id` | `list[str]` | 🟢 |
| `are_spouses` | `family_navigation.py:78` | `a_id`, `b_id` | `bool` | 🟢 |
| `split_path_by_marriage` | `family_navigation.py:82` | `person_path` | `(left, right, par)` | 🟢 |
| `pick_spouse_for_couple` | `family_navigation.py:93` | `person_id`, `candidate_path` | `str \| None` | 🟢 |
| `exclude_tail` | `family_navigation.py:104` | `seq`, `n=1` | `list` | 🟢 |
| `find_ancestral_path` | `path_finding.py:51` | `start_id`, `end_id`, `max_depth=20` | `(path, ancestral)` | 🟢 |
| `find_indirect_path` | `path_finding.py:31` | `start_id`, `end_id`, `max_hops=40` | `list[str] \| None` | 🟢 |
| `_mermaid_sid` | `mermaid_render.py:26` | `raw` | `str` (id de nó) | 🟢 |
| `_mermaid_label` | `mermaid_render.py:50` | `txt` | `str` (rótulo seguro) | 🟢 |
| `generate_mermaid_graph` | `mermaid_render.py:63` | `path`, `p1_id`, `p2_id`, `common_ancestor_id` | `str` (Mermaid) | 🟢 |
| `generate_mermaid_graph_indirect_bridge` | `mermaid_render.py:112` | `p1_id`, `p2_id`, `person_path` | `str` (Mermaid) | 🟢 |

### 4.3 Algoritmos e lógica não trivial

**BFS bidirecional por pais.** Duas fronteiras partem de cada pessoa e sobem por `get_parents`; a cada iteração **um** nível de **um** dos lados é expandido, alternadamente. O encontro é detectado quando o nó recém-expandido já está no conjunto visitado do outro lado, e o caminho é a concatenação dos dois percursos sem repetir o ponto de encontro. O teto é de **20 iterações de profundidade**, e não de gerações. 🟢

**Caminho indireto com compressão de famílias.** `nx.shortest_path` (BFS não ponderado) roda sobre o grafo bipartido pessoa↔família, com teto de 40 arestas; depois os nós de família são removidos, deixando só pessoas. O `graph` é importado **dentro da função**, porque `load_gedcom_and_build_graph` o **reatribui** — um import no topo ficaria preso ao grafo antigo (ou a `None`). 🟢

**Tradução de graus em parentesco.** `documentary_label` converte (subidas de A, subidas de B) até o ancestral comum em três coisas: rótulo legível, **chave canônica** (que depois casa com a tabela do Shared cM Project) e **meioses** — os saltos pai-filho entre as duas pessoas, que é a grandeza que o cM mede. Linha direta usa prefixo `bis` repetido `n−2` vezes; colateral com menor grau 1 vira irmãos, tio/tia ou tio/tia-avô; o resto vira primos de `g` grau com `r` remoções. 🟢

**Evidência de cada salto, com idade implícita.** `hop_evidence` localiza a família (FAMC/CHIL, com fallback por `child_to_family`), devolve o casal declarado e as datas, e calcula `age_at_birth = ano_do_filho − ano_do_genitor`. Idade fora de **12–70** marca `plausible: False` e gera o aviso `data_impossivel` — **sem invalidar o vínculo**. `plausible` é `None` quando falta data para julgar. 🟢

**Colapso de pedigree por contagem de cadeias.** `_cadeias_ate` conta quantos percursos distintos de pais levam de uma pessoa a um mesmo ancestral, parando em 8. Mais de uma cadeia até o mesmo ancestral é a assinatura de colapso/endogamia, e vira o aviso `colapso_de_pedigree` com o nome do ancestral e o número de cadeias. 🟢

**Escolha entre homônimos sem varredura infinita.** O dossiê compara nomes **sem acento** e com correção de mojibake, porque `find_person_by_name` compara com acento e um CSV sem acento não encontraria o registro GEDCOM. Com homônimos dos dois lados, são testadas até **5 × 5** combinações, em cache, e vence a primeira que tiver caminho. 🟢

**Contrato de escape do rótulo Mermaid.** Normaliza NFC, converte espaço inquebrável, travessões e aspas curvas, troca aspas duplas por apóstrofo, achata quebras de linha, aplica **lista branca** e converte `&`, `<` e `>` em entidades. A lista branca substituiu uma lista negra que era **furada pela crase** (`BUG-20260929-J6PQ`); a versão seguinte era estreita demais e descartava 14 caracteres sem intenção (`BUG-20261002-T4ZM`). 🟢

**Subgrafo com fechamento garantido.** O `end` de cada `subgraph` do diagrama indireto é escrito pelo fim de um `contextmanager`, e não por uma linha que alguém precisa posicionar: um `end` a mais ou a menos muda a árvore do diagrama **sem levantar erro nenhum** — risco registrado na `OPP-20260929-H2YY`. 🟢

### 4.4 Estruturas de dados

| Estrutura | Onde | Forma | Confiança |
| --- | --- | --- | --- |
| Resultado do parentesco | `documentary_relationship.py:551-568` | `status`, `source`, `label`, `relationship_key`, `meioses`, `degrees`, `person_a`, `person_b`, `common_ancestor`, `common_ancestors`, `path`, `additional_paths`, `evidence`, `homonyms`, `ambiguous_identity`, `warnings` | 🟢 |
| Ficha de pessoa | `documentary_relationship.py:129-143` | `id`, `name`, `sex`, `birth`, `birth_year`, `birth_place`, `death`, `death_year`, `parents`, `parent_names`, `spouses`, `children`, `family_as_child` | 🟢 |
| Evidência de salto | `documentary_relationship.py:267-280` | `child_id`, `child_name`, `child_birth`, `parent_id`, `parent_name`, `parent_birth`, `family_id`, `family_husband`, `family_wife`, `age_at_birth`, `plausible`, `link_source` | 🟢 |
| Dossiê de homônimos | `documentary_relationship.py:217-226` | `query`, `exact_count`, `exact_matches`, `similar_count`, `similar_matches`, `ambiguous`, `differences`, `identical_data` | 🟢 |
| Ancestral comum | `documentary_relationship.py:415-422` | `id`, `name`, `distance_a`, `distance_b`, `total_meioses`, `birth` | 🟢 |
| Índice de nomes | `documentary_relationship.py:185-202` | `{"versao": int, "mapa": dict}` — cache invalidado por `gedcom_state.versao` | 🟢 |
| Resultado da busca | `path_search.py:194-201` | `person1_name`, `person2_name`, `text_path`, `mermaid_data`, `documentary`, `observations` | 🟢 |

### 4.5 Regras de negócio catalogadas

*Faixas: **01–08** resolução e navegação · **09–17** parentesco documental · **18–27** fluxo da busca · **28–36** apresentação e diagrama.*

| ID | Regra | Local | Confiança |
| --- | --- | --- | --- |
| BR-C-01 | A pessoa é resolvida por nome: match **exato** sem diferenciar maiúsculas; sem exato, por **substring**. | `family_navigation.py:21-26` | 🟢 |
| BR-C-02 | Os pais vêm do `FAMC` da pessoa; sem `FAMC`, do índice `child_to_family`. Pais duplicados são removidos. | `family_navigation.py:29-48` | 🟢 |
| BR-C-03 | Os cônjuges vêm dos `FAMS`; **só quando essa lista fica vazia** roda a varredura global de todas as famílias. | `family_navigation.py:51-75` | 🟢 |
| BR-C-04 | A busca direta é BFS **bidirecional** subindo por pais, com teto de **20 iterações de profundidade**. | `path_finding.py:51-85`, `:25` | 🟢 |
| BR-C-05 | Se as duas pessoas são a mesma, o caminho é ela própria e ela é o ancestral. | `path_finding.py:58-59` | 🟢 |
| BR-C-06 | A cada iteração, **um** nível de **um** dos lados é expandido, alternadamente; o encontro é o nó que já consta no conjunto visitado do outro lado. | `path_finding.py:60-84` | 🟢 |
| BR-C-07 | A busca indireta usa o caminho mais curto no grafo pessoa↔família, com teto de **40 arestas**; os nós de família são comprimidos e restam só pessoas (2 ou mais). | `path_finding.py:31-48`, `:28` | 🟢 |
| BR-C-08 | O grafo é importado **dentro** da função, porque é reatribuído a cada parse. | `path_finding.py:38` | 🟢 |
| BR-C-09 | Sem os dois registros no GEDCOM, o parentesco devolve `status: not_found` com o aviso `pessoa_ausente`. | `documentary_relationship.py:443-446` | 🟢 |
| BR-C-10 | Sem caminho dentro do teto, o aviso diz explicitamente que isso **não prova** ausência de parentesco. | `documentary_relationship.py:452-466` | 🟢 |
| BR-C-11 | Os graus são as posições do ancestral comum no caminho: subidas de A até ele, e dele até B. | `documentary_relationship.py:486-488` | 🟢 |
| BR-C-12 | Linha direta (um dos graus é 0): 1 → pai/mãe; 2 → avô/avó; n → com prefixo `bis` repetido `n−2` vezes. | `documentary_relationship.py:302-313` | 🟢 |
| BR-C-13 | Colateral com menor grau 1: (1,1) irmãos; (1,2) tio/tia; (1,n) tio/tia com `bis` repetido `n−3` vezes. | `documentary_relationship.py:317-330` | 🟢 |
| BR-C-14 | Demais colaterais: chave `gC` ou `gCrR`, com grau `= menor−1` e remoções `= maior−menor`. | `documentary_relationship.py:332-340` | 🟢 |
| BR-C-15 | Cada salto do caminho carrega a evidência do registro que o sustenta: família, casal declarado, datas e idade implícita. | `documentary_relationship.py:233-280`, `:490-495` | 🟢 |
| BR-C-16 | Idade do genitor no nascimento do filho fora da faixa **12–70** marca `plausible: False` e gera o aviso `data_impossivel`; **o vínculo não é invalidado**. | `documentary_relationship.py:41-42`, `:265`, `:497-507` | 🟢 |
| BR-C-17 | Sem data para julgar, `plausible` é `None` (não é falso). | `documentary_relationship.py:265` | 🟢 |
| BR-C-18 | O ano é o primeiro número de 3 ou 4 dígitos da data; `ABOUT`/`BEFORE` são tolerados e **não** normalizados, e o texto original fica na evidência. | `documentary_relationship.py:55-69` | 🟢 |
| BR-C-19 | Todos os ancestrais comuns são enumerados até **12** níveis, limitados a **12**, ordenados por meioses totais, depois maior distância, depois nome. | `documentary_relationship.py:408-424`, `:47` | 🟢 |
| BR-C-20 | Caminhos alternativos são listados e **nenhum é descartado**; a existência gera o aviso `caminhos_multiplos`. | `documentary_relationship.py:509-525` | 🟢 |
| BR-C-21 | Mais de uma cadeia de pais até o mesmo ancestral gera o aviso `colapso_de_pedigree`, com o ancestral e a contagem (teto de 8 cadeias). | `documentary_relationship.py:361-382`, `:527-539`, `:48` | 🟢 |
| BR-C-22 | O índice nome→ids é reconstruído apenas quando `gedcom_state.versao` muda, e não pelo tamanho de `people`. | `documentary_relationship.py:185-202` | 🟢 |
| BR-C-23 | A comparação de nomes ignora acento e aplica a correção de mojibake antes de comparar. | `documentary_relationship.py:150-161` | 🟢 |
| BR-C-24 | O dossiê devolve **todos** os registros possíveis, sem escolher; `ambiguous` é verdadeiro com mais de um nome exato. | `documentary_relationship.py:205-226` | 🟢 |
| BR-C-25 | Com identidade ambígua, o parentesco sai com `status: ambiguous` e o aviso `homonimo`, pedindo conferência das fichas. | `documentary_relationship.py:541-549`, `:552` | 🟢 |
| BR-C-26 | Pessoa 1 ou 2 não encontrada: mensagem `Pessoa N 'X' não encontrada.` e `success = False`. | `path_search.py:138-141` | 🟢 |
| BR-C-27 | Com homônimos, até **5 × 5** combinações são testadas (em cache) e vence a **primeira que tiver caminho**; sem nenhuma, usa-se o primeiro id de cada lado. | `path_search.py:150-167`, `:71` | 🟢 |
| BR-C-28 | Caminho por ancestral comum: mensagem `Conexão direta encontrada (ancestral comum).` | `path_search.py:176` | 🟢 |
| BR-C-29 | Sem caminho direto, tenta-se o indireto; sem indireto, `Nenhuma conexão encontrada entre 'X' e 'Y'.` com `success = True`. | `path_search.py:178-182` | 🟢 |
| BR-C-30 | Conexão indireta vira `status: affinity`, com rótulo "Sem ancestral comum: conexão por afinidade (casamento)" e o aviso de afinidade. | `path_search.py:183-192`, `:66-67` | 🟢 |
| BR-C-31 | A conexão por afinidade **nunca** é apresentada como parentesco consanguíneo — o aviso é explícito e em maiúsculas. | `path_search.py:66-67` | 🟢 |
| BR-C-32 | O rótulo Mermaid passa por NFC, converte espaço inquebrável, travessões e aspas curvas, troca aspa dupla por apóstrofo e achata quebras de linha. | `mermaid_render.py:50-58` | 🟢 |
| BR-C-33 | O rótulo usa **lista branca** de caracteres: o que não está nela é removido, e `&`, `<`, `>` viram entidades HTML. | `mermaid_render.py:47`, `:59-60` | 🟢 |
| BR-C-34 | O id de nó Mermaid mantém apenas `[A-Za-z0-9_]`, remove `@`, troca `+` por `_` e recebe o prefixo `N_`. | `mermaid_render.py:26-31` | 🟢 |
| BR-C-35 | No diagrama direto, o casal do ancestral comum (ancestral + primeiro cônjuge) vira **um** nó quando o ancestral não está numa das pontas do caminho. | `mermaid_render.py:69-86` | 🟢 |
| BR-C-36 | Cada `subgraph` do diagrama indireto é fechado pelo fim de um `contextmanager`, e não por linha posicionada à mão. | `mermaid_render.py:160-175` | 🟢 |

### 4.6 Constantes, parâmetros e configuração

| Nome | Valor | Onde | Observação |
| --- | --- | --- | --- |
| `MAX_DEPTH` | `20` | `path_finding.py:25` | Teto de **iterações** do BFS bidirecional, não de gerações. Decisão humana de 2026-09-30: preservar a fidelidade ao legado. |
| `MAX_HOPS` | `40` | `path_finding.py:28` | Teto de arestas no grafo de famílias. |
| `MAX_DEPTH_ALTERNATIVOS` | `12` | `documentary_relationship.py:47` | Teto da enumeração de ancestrais comuns. |
| `LIMITE_DE_CADEIAS` | `8` | `documentary_relationship.py:48` | Teto da contagem de cadeias (colapso de pedigree). |
| `LIMITE_DE_CANDIDATOS` | `5` | `path_search.py:71` | Teto por lado nas combinações com homônimos. |
| Limite de ancestrais comuns | `12` | `documentary_relationship.py:408` | Parâmetro `limit`. |
| `IDADE_MINIMA_GENITOR` / `IDADE_MAXIMA_GENITOR` | `12` / `70` | `documentary_relationship.py:41-42` | Não é regra biológica: é filtro de evidência. |
| `AVISO_AFINIDADE` | texto fixo | `path_search.py:66-67` | Mensagem que impede a leitura da afinidade como consanguinidade. |
| `_LABEL_SEGURO` | lista branca (regex negada) | `mermaid_render.py:47` | Documentada no próprio código, com os dois bugs que a moldaram. |
| Cores dos nós | verde `#e8f5e9` (pessoa 1), vermelho `#ffebee` (pessoa 2), amarelo `#fff9c4` (ancestral/casal), âmbar `#fff8e1` (cônjuges) | `mermaid_render.py:105-108`, `:286-287` | Papel visual de cada nó. |
| Direção do diagrama | `flowchart BT` | `mermaid_render.py:66`, `:157` | Base para o topo. |

### 4.7 Observações e lacunas

* 🟢 **O teto de 20 corta em silêncio, e isso é contrato aceito.** Decisão humana de 2026-09-30: nenhum requisito novo — o caminho simplesmente não é encontrado, e o aviso diz que isso não prova ausência de parentesco.
* 🟢 **A varredura de `get_spouses` é condicional, e isso é contrato explícito.** Se a pessoa tem um `FAMS` que resolve e outro que não, o fallback **não roda** e o cônjuge da segunda família desaparece do resultado. Documentado como decisão, com o aviso de que torná-la complementar mudaria o resultado.
* 🟡 **`get_children` varre todas as famílias do arquivo** a cada chamada, sem índice — diferente de `get_parents`, que usa `child_to_family`. Em `person_summary`, que é chamada por homônimo, isso custa uma varredura completa por ficha.
* 🟡 **O caminho indireto não é validado quanto a datas.** A checagem de 12–70 anos existe apenas sobre os saltos do caminho **direto** (`hop_evidence`); a ponte por casamento não passa por ela.
* 🟡 **`_cadeias_ate` e `_cadeia_curta` sobem por pais com teto de 12**, então colapso de pedigree além desse teto não é detectado — e o aviso não distingue "sem colapso" de "colapso fora do alcance".
* 🔴 **`person_a` e `person_b` são fichas completas incluídas em cada resultado.** Na análise de DNA com 71 conexões, são 142 fichas montadas (cada uma varrendo famílias) para uma tela que exibe poucas — custo real, sem limite medido.

---

## 5. Dados Transversais

O dicionário de dados consolidado — campos, tipos, obrigatoriedade, valores padrão e origem de cada estrutura — está em **`data-dictionary.md`**. Ele cobre:

* as entidades do GEDCOM em memória (`people`, `families`, `graph`, `child_to_family`, `versao`);
* as estruturas do CSV e da evidência genética (evidência por kit, segmento, `df.attrs`, aviso);
* as estruturas de decisão (hipótese por kit, confronto, resultado da análise, descartado);
* as estruturas do parentesco documental (resultado, ficha de pessoa, evidência de salto, dossiê de homônimos, ancestral comum);
* os parâmetros de configuração por ambiente e as constantes de domínio.

---

## 6. Dívidas Técnicas e Observações Consolidadas

| # | Dívida / observação | Local | Gravidade | Confiança |
| ---: | --- | --- | --- | --- |
| 1 | `app.secret_key` embutido no código, herdado do legado. | `app.py:22` | Baixa (não há autenticação) | 🟢 |
| 2 | Estado global mutável em `core/gedcom_state.py`: um processo atende um operador por vez, e duas instâncias seriam dois estados. É a razão da guarda de instância única. | `gedcom_state.py:19-30`, `app.py:205-257` | Alta para multiusuário | 🟢 |
| 3 | Nenhum resultado é persistido; o GEDCOM é re-parseado a cada `POST`. | `app.py:126`, `:137` | Média (custo) | 🟢 |
| 4 | O teto de 20 iterações do BFS corta em silêncio. | `path_finding.py:25` | Média (contrato aceito) | 🟢 |
| 5 | `get_spouses` esconde cônjuges quando o primeiro `FAMS` resolve. | `family_navigation.py:66-75` | Média (contrato aceito) | 🟢 |
| 6 | `get_children` varre todas as famílias, sem índice. | `documentary_relationship.py:112-124` | Média (custo) | 🟢 |
| 7 | Fichas completas por pessoa em cada resultado (142 no caso real de 71 conexões). | `documentary_relationship.py:127-143`, `:558-559` | Média (custo) | 🟢 |
| 8 | Caminho indireto não passa pela checagem de plausibilidade de datas. | `path_search.py:178-192` | Média | 🟡 |
| 9 | O CSV de DNA não tem validação de conteúdo, só de forma de nome. | `app.py:86` | Média | 🟢 |
| 10 | `cm_estimator` segue no repositório como legado fora do fluxo, com faixas sem fonte verificável. | `cm_estimator.py` | Baixa (declarada) | 🟢 |
| 11 | `COMMON_SURNAMES` tem duplicata literal; o mapa de mojibake tem chave duplicada e um no-op. | `name_normalization.py:36`, `text_cleaning.py:41-50` | Baixa | 🟢 |
| 12 | Divergência de versões entre o `.venv` e o `requirements.txt`, incluindo o `RapidFuzz` que decide o matching. | `.venv/`, `requirements.txt` | **Alta** (resultado pode divergir) | 🟢 |
| 13 | Endogamia e colapso de pedigree não são corrigidos no confronto: o cM lido é um teto otimista nesses casos. | `evidence_comparison.py:55-68` | Média (declarada na fonte) | 🟢 |
| 14 | Relações mais distantes não publicadas na versão 4.0 da fonte, que é onde o caso real cai. | `relationship_hypotheses.py:96-103` | Média | 🟢 |
| 15 | `LIMITE_SEGMENTO_FRACO` é heurística do projeto apresentada ao lado de números publicados. | `genetic_evidence.py:31` | Baixa | 🟢 |
| 16 | Cobertura de testes não medida (sem `pytest-cov`). | — | Média | 🟡 |

---

*Gerado pelo Reversa-Archaeologist em 2026-10-05 (re-extração). Fim da análise técnica consolidada.*

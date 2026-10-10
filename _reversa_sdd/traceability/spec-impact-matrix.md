# Matriz de Impacto entre Componentes — analisador-genealogico

> Nível de documentação: **Completo** (`state.json` → `doc_level`)
> Re-extração de **2026-10-10**. Substitui o artefato de 2026-10-05, que descrevia **4 unidades**, **19 componentes** e dois ciclos de pacote.
> Snapshot da versão substituída: `.reversa/snapshots/2026-10-10-pre-reextracao/traceability/spec-impact-matrix.md`
> Escala de confiança: 🟢 CONFIRMADO | 🟡 INFERIDO | 🔴 LACUNA
> Contexto: `architecture.md` · `c4-components.md` · `erd-complete.md` · `domain.md`

---

## 1. Para que serve esta matriz

Antes de alterar **qualquer** componente, ela responde: *o que mais quebra?* A ordem de leitura é a das seções — da estrutura (A, B) para o risco concreto (C, D, E).

### Legenda dos marcadores

| Símbolo | Significado |
| --- | --- |
| ● | **Impacto direto** — o componente implementa a unidade, ou é ponto único de mudança para ela |
| ○ | **Impacto indireto** — o componente consome e **propaga** a mudança, sem implementar a regra |
| — | Sem impacto |

> ⚠️ **Nota de validade.** As specs de unidade (`<unit>/requirements.md`, `design.md`, `tasks.md`) são as de **2026-10-05** e serão **regeradas na Fase 4**. Por isso a matriz é expressa em termos de **unidade funcional + artefato**, e não de linha de spec — ela continua válida depois da regeneração.

**As cinco unidades funcionais** (decisão `[specs] granularity = endpoint`, persistida em `.reversa/config.toml`):

| Unidade | Superfície | Implementação |
| --- | --- | --- |
| `upload-gedcom` | `POST action=upload_gedcom` | `application/upload_gedcom.py`, `application/reenvio.py`, `utils/validate.py`, `parsers/gedcom_parser.py`, `utils/text_cleaning.py`, `ports/adaptadores.py` |
| `tela-de-entrada` | `GET /` + `POST aposentar_arquivo` e `selecionar_arvore` | `reporting/lista_de_arquivos.py`, `app.py`, `utils/validate.py` |
| `analise-dna` | `POST action=dna_analysis` | `application/dna_analysis.py`, `dna_analysis.py` (core), + 8 módulos de `core/`, `parsers/csv_ingest.py`, `application/traducao.py`, `ports/*` (registro) |
| `busca-caminho` | `POST action=path_search` | `application/path_search.py`, `core/path_search.py`, `path_finding.py`, `family_navigation.py`, `documentary_relationship.py`, `diagram_domain.py`, `reporting/mermaid_render.py` |
| `recursos-da-tela` | `GET /banner.png` e `GET /apple-touch-icon.png` | `app.py`, `src/assets/*`, `tests/{icone_de_atalho,banner_da_tela}.py` (as receitas) |

---

## 2. Matriz A — Componente × Unidade funcional

| Componente | `upload-gedcom` | `tela-de-entrada` | `analise-dna` | `busca-caminho` | `recursos-da-tela` |
| --- | :---: | :---: | :---: | :---: | :---: |
| `app.py` | ● | ● | ● | ● | ● |
| `application/upload_gedcom.py` | ● | — | — | — | — |
| `application/reenvio.py` | ● | ○ | ○ | — | — |
| `application/dna_analysis.py` | — | — | ● | — | — |
| `application/path_search.py` | — | — | — | ● | — |
| `application/traducao.py` | ● | ○ | ● | ● | — |
| `application/__init__.py` | ○ | ○ | ○ | ● | — |
| `ports/__init__.py` | ● | ● | ● | ○ | — |
| `ports/adaptadores.py` | ● | ● | ● | ○ | — |
| `utils/validate.py` | ● | ● | ○ | ○ | — |
| `utils/text_cleaning.py` | ● | — | ● | ● | — |
| `utils/name_keys.py` | — | — | ● | ○ | — |
| `utils/number_format.py` | — | ● | ● | ○ | — |
| `parsers/gedcom_parser.py` | ● | ● | ○ | ○ | — |
| `parsers/csv_ingest.py` | — | — | ● | — | — |
| `core/registro.py` | ● | ○ | ● | ● | — |
| `core/erros.py` | ● | ○ | ● | ● | — |
| `core/name_normalization.py` | — | — | ● | ○ | — |
| `core/matching.py` | — | — | ● | — | — |
| `core/family_navigation.py` | — | — | ○ | ● | — |
| `core/path_finding.py` | — | — | ○ | ● | — |
| `core/documentary_relationship.py` | — | — | ● | ● | — |
| `core/diagram_domain.py` | — | — | ● | ● | — |
| `core/genetic_evidence.py` | — | — | ● | — | — |
| `core/relationship_hypotheses.py` | — | — | ● | — | — |
| `core/evidence_comparison.py` | — | — | ● | — | — |
| `core/path_search.py` | — | — | ○ | ● | — |
| `core/dna_analysis.py` | — | — | ● | ○ | — |
| `core/cm_estimator.py` | — | — | ○ *(legado)* | — | — |
| `reporting/mermaid_render.py` | — | — | ● | ● | — |
| `reporting/lista_de_arquivos.py` | — | ● | — | — | — |
| `tests/icone_de_atalho.py` · `banner_da_tela.py` | — | — | — | — | ● |

**Leitura dos cinco componentes que atravessam tudo:**

| Componente | Por que atravessa | Risco ao alterar |
| --- | --- | --- |
| `app.py` | Único ponto de entrada: valida, **escolhe o render pelo desfecho**, monta as listas, serve as artes, grava, aposenta, re-parseia e sobe o servidor | **Alto** — a ordem dos ramos (aposentar **antes** de resolver a árvore) e a degradação das rotas de arte são contrato |
| `ports/__init__.py` + `adaptadores.py` | Toda a interação com disco e banco passa por aqui, e **as assinaturas são o contrato da Onda 3** | **Alto** — `dono` obrigatório e sem valor padrão; um segundo método no `CarregadorDeArvores` **exige reabrir a `D-02`** |
| `utils/validate.py` | Toda a decisão sobre o que pode ser gravado **e lido**, hoje em **duas** perguntas distintas | **Alto (segurança)** — a forma de nome é a defesa contra escape; e a tela pergunta a **mesma** função que o resolvedor |
| `utils/text_cleaning.py` | Decide a **comparação de nomes** em 5 consumidores | **Alto** — duas cópias divergentes já produziram 5 de 9 casos errados (`ADR-07`) |
| `core/registro.py` | `get_name` e `ref_id`, usados por quase todo o núcleo | **Alto** — `get_name` é **cópia literal do oráculo**, e "melhorá-la" quebra a paridade (`DIV-001`) |

---

## 3. Matriz B — Componente × Artefato de documentação

● = é **fonte primária** do artefato · ○ = contribui · — = não aparece

| Componente | `code-analysis.md` | `data-dictionary.md` | `flowcharts/` | `domain.md` | `architecture.md` | `erd-complete.md` | `adrs/` |
| --- | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| `app.py` | ● | ● | ● | ● | ● | ● | ● |
| `application/*` (6) | ● | ● | ● | ● | ● | ● | ● |
| `ports/*` (2) | ● | ● | ● | ● | ● | ● | ● |
| `utils/validate.py` | ● | ● | ● | ● | ○ | ● | ● |
| `utils/text_cleaning.py` | ● | ○ | ○ | ● | ○ | ○ | ● |
| `utils/name_keys.py` | ● | ○ | ○ | ○ | ○ | ○ | ● |
| `utils/number_format.py` | ● | ○ | ○ | ○ | ○ | ○ | ○ |
| `parsers/gedcom_parser.py` | ● | ● | ● | ● | ● | ● | ● |
| `parsers/csv_ingest.py` | ● | ● | ● | ● | ○ | ● | ● |
| `core/registro.py` | ● | ● | ○ | ● | ○ | ● | ● |
| `core/erros.py` | ● | ● | ● | ● | ○ | ○ | ● |
| `core/name_normalization.py` | ● | ○ | ○ | ● | ○ | ○ | ○ |
| `core/matching.py` | ● | ○ | ● | ● | ● | ○ | ● |
| `core/family_navigation.py` | ● | ○ | ● | ● | ○ | ● | ○ |
| `core/path_finding.py` | ● | ○ | ● | ● | ○ | ○ | ○ |
| `core/documentary_relationship.py` | ● | ● | ● | ● | ● | ● | ● |
| `core/diagram_domain.py` | ● | ○ | ● | ○ | ● | ● | ● |
| `core/genetic_evidence.py` | ● | ● | ● | ● | ○ | ● | ● |
| `core/relationship_hypotheses.py` | ● | ● | ● | ● | ● | ● | ● |
| `core/evidence_comparison.py` | ● | ● | ● | ● | ● | ● | ● |
| `core/path_search.py` | ● | ● | ● | ● | ○ | ● | ● |
| `core/dna_analysis.py` | ● | ● | ● | ● | ● | ● | ● |
| `core/cm_estimator.py` | ● | ○ | ○ | ● | ○ | ○ | ● |
| `reporting/mermaid_render.py` | ● | ○ | ● | ● | ○ | ○ | ● |
| `reporting/lista_de_arquivos.py` | ● | ● | ● | ● | ● | ● | ● |
| `src/assets/*` + receitas | ● | ○ | ● | ● | ● | ○ | ● |

**Os componentes que alimentam mais ADRs** são os que **já mudaram de decisão** alguma vez: `app.py`, `application/*`, `ports/*`, `validate`, `gedcom_parser`, `documentary_relationship`, `diagram_domain`, `genetic_evidence`, `relationship_hypotheses`, `evidence_comparison`, `path_search`, `dna_analysis`, `mermaid_render` e `lista_de_arquivos`. **Concentração de decisões = concentração de risco de reimplementação.**

---

## 4. Matriz C — Componente × Área de teste

> **Nota de método:** o artefato anterior tinha **uma coluna por arquivo de teste** (11 colunas). Com **39 arquivos de teste**, isso deixou de ser legível. As colunas passaram a ser **áreas**, e cada uma nomeia os arquivos que a compõem. A perda é de granularidade por arquivo; o ganho é que a matriz continua utilizável.

● = coberto diretamente · ○ = exercitado de passagem · — = não coberto

| Componente | upload e segurança | fronteira e erros | portas e armazenamento | lista e reenvio | DNA e confronto | matching | caminho e Mermaid | projeção e persistência | servidor e arte |
| --- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| `app.py` | ● | ● | ○ | ● | ○ | — | — | — | ● |
| `application/upload_gedcom.py` | ● | ● | ○ | ○ | — | — | — | — | — |
| `application/reenvio.py` | ● | ○ | ● | ● | — | — | — | — | — |
| `application/dna_analysis.py` | — | ○ | ○ | — | ● | ○ | — | ● | — |
| `application/path_search.py` | — | ● | — | — | — | — | ● | — | — |
| `application/traducao.py` | ○ | ● | — | — | ○ | — | — | — | — |
| `ports/__init__.py` | ○ | ● | ● | ○ | — | — | — | ● | — |
| `ports/adaptadores.py` | ● | ● | ● | ● | — | — | — | ● | — |
| `utils/validate.py` | ● | ● | ● | ● | — | — | — | — | — |
| `utils/text_cleaning.py` | ○ | — | — | — | ○ | ○ | — | — | — |
| `utils/name_keys.py` | — | — | — | — | ○ | ● | — | — | — |
| `utils/number_format.py` | — | — | — | ○ | ● | — | — | — | — |
| `parsers/gedcom_parser.py` | ● | ● | ● | ○ | ● | ● | ● | — | — |
| `parsers/csv_ingest.py` | — | ● | — | — | ● | ○ | — | — | — |
| `core/registro.py` | ● | — | — | — | ○ | ○ | ○ | — | — |
| `core/erros.py` | ○ | ● | ○ | — | ○ | — | — | — | — |
| `core/name_normalization.py` | — | — | — | — | ○ | ● | — | — | — |
| `core/matching.py` | — | — | — | — | ● | ● | — | — | — |
| `core/family_navigation.py` | — | — | — | — | — | — | ● | — | — |
| `core/path_finding.py` | — | — | — | — | — | — | ● | — | — |
| `core/documentary_relationship.py` | — | — | — | — | ● | — | ● | — | — |
| `core/diagram_domain.py` | — | — | — | — | — | — | ○ | — | — |
| `core/genetic_evidence.py` | — | — | — | — | ● | — | — | — | — |
| `core/relationship_hypotheses.py` | — | — | — | — | ● | — | — | — | — |
| `core/evidence_comparison.py` | — | — | — | — | ● | — | — | — | — |
| `core/path_search.py` | — | — | — | — | — | — | ● | — | — |
| `core/dna_analysis.py` | — | ○ | — | — | ● | ● | — | ● | — |
| `core/cm_estimator.py` | — | — | — | — | ● | — | — | — | — |
| `reporting/mermaid_render.py` | — | — | — | — | — | — | ● | — | — |
| `reporting/lista_de_arquivos.py` | — | — | ○ | ● | — | — | — | — | — |
| receitas de arte | — | — | — | — | — | — | — | — | ● |

**Áreas e arquivos:**

| Área | Arquivos |
| --- | --- |
| upload e segurança | `test_upload`, `test_upload_seguranca`, `test_forma_da_referencia`, `test_gedcom_ilegivel_nao_derruba`, `test_documentacao_do_upload`, `test_arvore_devolvida` |
| fronteira e erros | `test_erros_de_dominio`, `test_traducao_de_erros`, `test_desfecho_do_resultado`, `test_dependencias_nucleo` |
| portas e armazenamento | `test_porta_de_armazenamento`, `test_guardas_do_armazenamento`, `test_manutencao_de_uploads`, `test_ambiente_temporario_da_suite` |
| lista e reenvio | `test_lista_de_arquivos`, `test_lista_na_tela`, `test_aposentar_arquivo`, `test_reenvio_do_arquivo`, `test_reenvio_do_csv`, `test_campo_de_escolha_do_csv`, `test_voltar_para_a_lista` |
| DNA e confronto | `test_confrontacao_gedcom_dna`, `test_dna_analysis`, `test_domain`, `test_formatacao_cm` |
| matching | `test_characterization_matching` |
| caminho e Mermaid | `test_path_search`, `test_characterization_mermaid`, `test_mermaid_escape` |
| projeção e persistência | `test_projecao_da_analise`, `test_registro_de_analises`, `test_persistencia_desabilitada`, `test_persistencia_indisponivel` |
| servidor e arte | `test_servidor_producao`, `test_icone_de_atalho`, `test_banner_do_topo`, `test_deriva_da_arte`, `test_rodar_paridade` |

### 🔴 Cobertura desigual — leitura da matriz

| Situação | Componentes | Comentário |
| --- | --- | --- |
| **Bem cobertos** | `validate` (upload + segurança + portas + lista), `documentary_relationship` + `evidence_comparison` + `relationship_hypotheses` (a área de DNA e confronto), `mermaid_render` (caracterização + escape) | As áreas que **já tiveram bug ou decisão humana** ganharam rede de segurança |
| **Cobertos por um único arquivo** | `number_format` (só `test_formatacao_cm`), `matching` (só caracterização) e `lista_de_arquivos` (só a área de lista) | Rede fina: uma regressão fora do caso caracterizado passa |
| **Só exercitados de passagem** | `csv_ingest` fora da área de DNA; `family_navigation` e `path_finding` fora da área de caminho; `diagram_domain` inteiro | Sem teste de unidade dedicado |
| **Sem cobertura dedicada** | `core/cm_estimator.py` — cobertura **declaradamente de compatibilidade**: ele existe **porque** o teste o exercita | Coerente com `ADR-19` |
| **🔴 Sem teste do caminho de gravação** | `ports/adaptadores.py` (`RegistroDeAnalisesPostgres._escrever`) | A área de persistência exercita os estados **degradados**, por desenho. Erro de SQL, de ordem de FK ou de tipo só apareceria no contêiner (`L-28`) |
| **🔴 Sem teste do ambiente de arte** | `src/assets/*` | Os testes rodam no host, onde `docs/` existe; a degradação **dentro do container** não é verificada |

> **`test_servidor_producao.py` analisa o `app.py` por AST** em vez de executá-lo — cobre o **bloco de entrada**, não a rota.

---

## 5. Matriz D — Constante compartilhada × Consumidores

Esta é a matriz **mais acionável** do documento: em um sistema cujo comportamento é decidido por limiares, mudar um número propaga silenciosamente.

| Constante | Valor | Definida em | Consumidores | Propaga para | Conf. |
| --- | --- | --- | --- | --- | --- |
| `MAX_DEPTH` | `20` | `core/path_finding.py` | `find_ancestral_path`, `documentary_relationship` | ⚠️ **A mensagem do aviso `sem_caminho` interpola o valor** — mudar a constante **muda texto que o operador lê** | 🟢 |
| `MAX_HOPS` | `40` | idem | `find_indirect_path` | Teto do caminho indireto, contado em **arestas do grafo bipartido** (≈ metade em vínculos entre pessoas) | 🟢 |
| `IDADE_MINIMA_GENITOR` / `IDADE_MAXIMA_GENITOR` | `12` / `70` | `documentary_relationship.py` | `hop_evidence` | Campo `plausible` e aviso `data_impossivel` (com as idades no texto) | 🟢 |
| `MAX_DEPTH_ALTERNATIVOS` | `12` | idem | `find_all_common_ancestors`, `_cadeias_ate` | Cardinalidade de `common_ancestors` e detecção de colapso | 🟢 |
| `LIMITE_DE_CADEIAS` | `8` | idem | `_cadeias_ate` | Aviso `colapso_de_pedigree` — **teto do que é detectável**, e o número exibido é um **piso** | 🟢 |
| `LIMITE_DE_CANDIDATOS` | `5` | `core/path_search.py` | Combinador 5×5 de homônimos | Qual registro vence na busca com nomes repetidos | 🟢 |
| `LIMITE_SEGMENTO_FRACO` | `15.0` | `core/genetic_evidence.py` | `weak_segment` | Aviso `segmento_fraco` — **heurística do projeto** (`ADR-19`) | 🟢 |
| `LIMITE_DE_PREAMBULO` | `10` | `parsers/csv_ingest.py` | `localizar_cabecalho` | Onde o cabeçalho do CSV pode estar | 🟢 |
| `TETO_DE_UPLOAD_EM_BYTES` / `_EM_MB` | 16 MB | `app.py` | Guarda de corpo | ⚠️ **A mensagem `413` interpola o valor em MB** — mudar a constante muda texto de contrato | 🟢 |
| `SEPARADORES` | `,` `;` TAB `\|` | `parsers/csv_ingest.py` | `detectar_separador` | ⚠️ **A ordem importa**: no empate vence a vírgula | 🟢 |
| `SCP40_ROWS` / `SCP40_NOT_PUBLISHED` | 27 / 6 relações | `core/relationship_hypotheses.py` | `possible_relationships`, `hypotheses_for_evidence`, `_janela_do_documental` | ⚠️ **Altera o confronto inteiro**: as janelas e os 4 estados derivam daqui | 🟢 |
| `CAUSAS_POSSIVEIS` / `CAUSAS_POSSIVEL` | 12 / **8** itens | `core/evidence_comparison.py` | `compare` | Texto do rol de causas. ⚠️ **Revisor, 2026-10-10:** esta linha dizia 9; a medição por importação dá **8** | 🟢 |
| Pesos do score | `0.55` / `0.25` / `0.20` | `core/matching.py` | `match_candidates` | 🔴 **Quem é aceito no matching** | 🟢 |
| Bônus de sobrenome | `+8.0` / `−4.0` | idem | `match_candidates` | Idem | 🟢 |
| Limiar de cM do Jaccard | `150` | idem | Ramo do Jaccard 0,33 | Idem — **decisão humana** de 2026-08-03 | 🟢 |
| **4º critério de desempate** | menor `xref_id` | idem | `match_candidates` | 🔴 Quem vence o empate exato — **implementado em 2026-10-06** | 🟢 |
| Limiares dos 5 ramos de aceite | literais, **não constantes** | idem | `match_candidates` | 🔴 **Quem é aceito** — `100/0,67`, `80/0,50`, `86/0,80`, `92`, `88`, e o rebaixamento `96/92` | 🟢 |
| `STOP_WORDS`, `GENERIC_GIVENS`, `SURNAME_SUFFIXES`, `COMMON_SURNAMES`, `SURNAME_EQUIV` | ver `core/name_normalization.py` | idem | `split_name_pt`, `surnames_set`, `match_candidates` | 🔴 Decompõe o nome e decide o prenome/sobrenomes de **todo** o matching | 🟢 |
| `SEM_KIT` | `" SEM-KIT"` *(espaço à esquerda)* | `core/genetic_evidence.py` | `build_genetic_evidence`, `evidence_for` | ⚠️ **O espaço é a defesa contra colisão** — removê-lo recria o `E-03` | 🟢 |
| `PASTA_DE_APOSENTADOS` | `_aposentados` | `ports/adaptadores.py` | `aposentar`, `listar` | ⚠️ **O nome da subpasta é o que faz o arquivo sumir da lista** — `listar` ignora subdiretório | 🟢 |
| `DONO_DO_PROCESSO` | `"unico"` | `app.py` | Os quatro pontos que fornecem o dono | ⚠️ Não é mecanismo de segurança; nenhum comportamento depende dele | 🟢 |
| `_LABEL_SEGURO` | lista branca (regex negada) | `reporting/mermaid_render.py` | `_mermaid_label` | 🔴 Dois bugs de escape nasceram aqui (`J6PQ`, `T4ZM`) | 🟢 |
| `ARTE_DO_ICONE` / `ARTE_DO_TOPO` | caminhos em `src/assets/` | `app.py` | As duas rotas de arte | ⚠️ Ficam em `app.config` para o **caso de ausência** ser testável sem tocar no repositório | 🟢 |
| `CLARO_MINIMO` / `SATURACAO_MAXIMA` / `SATURACAO_MINIMA_ESCURA` | `160` / `50` / `12` | `tests/banner_da_tela.py` | `_e_fundo` | 🔴 Decidem o que é fundo: baixar o brilho **come a arte**, alargar a saturação **deixa o quadriculado** | 🟢 |
| `TAMANHO_ESPERADO` | `16504` bytes | `tests/icone_de_atalho.py` | O teste de deriva e o de rota | ⚠️ Âncora contra reamostragem, fundo ou compressão diferentes | 🟢 |
| `SHA_DA_TELA` | `17240e5a…` | `tests/test_icone_de_atalho.py` | O teste de invariante de tela | ⚠️ **Mantido à mão** — atualizado três vezes em 2026-10-10 | 🟡 |

### 🔴 Os três achados desta matriz

1. **`MAX_DEPTH` e `TETO_DE_UPLOAD_EM_BYTES` estão embutidos em mensagens que o operador lê.** Mudar o número **não é** mudança de parâmetro: é **mudança de texto de contrato**, que goldens e testes podem fixar.
2. **Os limiares de aceitação do matching continuam sem ponto único de mudança.** É consequência direta do `ADR-08` (não criar constantes que o legado não tinha), e o custo — não registrado naquele ADR — é que alterar a "generosidade" do matching exige editar literais dentro de **cinco** ramos condicionais.
3. **`SHA_DA_TELA` e as constantes da receita de arte são o oposto:** são números medidos, mantidos à mão, e cada um tem um teste que **prova que ele detecta** a mudança que existe para detectar. A diferença é que esses dois guardam **fidelidade de artefato**, e não regra de negócio.

---

## 6. Matriz E — Componente × Defeito registrado (SPEC ↔ CODE ↔ TEST ↔ BUG)

| Bug | Severidade | Componentes afetados | Teste de regressão | Estado |
| --- | --- | --- | --- | --- |
| `BUG-20260929-QMLY` — upload sem limites | Alta | `app.py`, `utils/validate.py`, `ports/adaptadores.py` | `test_upload_seguranca` | ✅ Corrigido |
| `BUG-20260929-J6PQ` — escape incompleto no rótulo Mermaid | Alta | `reporting/mermaid_render.py` | `test_mermaid_escape` | ✅ Corrigido |
| `BUG-20261002-T4ZM` — rótulo descarta caracteres inertes | Média | idem | `test_mermaid_escape` | ✅ Corrigido |
| `BUG-20260929-BJJH` — exposição de árvore entre usuários | **Crítica / P0** | `app.py`, `templates/index.html`, `ports/adaptadores.py`, `init.sql` | **Nenhum** — inaplicável ao legado (sem identidade) | ⚠️ **Aberto**, mitigado por aceite de risco. **Metade fechou**: a troca de árvore entre threads tornou-se impossível |
| `BUG-20261004-EWSJ` — badge de cM com ruído de ponto flutuante | Baixa | `utils/number_format.py`, `app.py` | `test_formatacao_cm` | ✅ Corrigido |
| `BUG-20261009-6RKP` — arquivo com acento inalcançável | **Alta** | `utils/validate.py`, `app.py`, `reporting/lista_de_arquivos.py` | `test_forma_da_referencia`, `test_lista_de_arquivos` | ✅ **Corrigido em 2026-10-10** (`RN-20`) |

**Observações de rastreabilidade:**

- **`reporting/mermaid_render.py` continua sendo o componente com mais defeitos registrados** (2 de 6) e o único cuja correção precisou ser **refeita**. É o componente com maior densidade de contrato implícito.
- 🔴 **O `BUG-20260929-BJJH` é o único defeito crítico sem teste de regressão**, e não por descuido: o critério de aceite é **inaplicável** ao legado por não existir identidade. A cobertura pertence à Onda 3.
- 🟢 **O `BUG-20261009-6RKP` é o defeito mais instrutivo da rodada**, porque nasceu de uma **defesa**: a validação por alfabeto fechado recusava o que o próprio gravador produzia. Ele mostra que validação mais estreita que o produtor é defeito, e não rigor.
- 🔴 **Quatro componentes nunca tiveram defeito registrado nem decisão humana verificada**: `utils/number_format.py`, `core/genetic_evidence.py`, `core/relationship_hypotheses.py` e `core/path_finding.py`. Nos três últimos, isso **não** significa baixo risco — todos alimentam o veredito do confronto.

---

## 7. Componentes de maior alcance (ordem de risco)

| # | Componente | Dependents diretos | Por que é o mais arriscado de alterar |
| ---: | --- | ---: | --- |
| 1 | `app.py` | 8 (as quatro ações, as duas artes e o processador de contexto **passam por ele**) | Único ponto de entrada; a **ordem dos ramos** é regra, e a degradação das artes é contrato |
| 2 | `ports/adaptadores.py` + `ports/__init__.py` | 5 | Toda a interação com disco e banco; **as assinaturas são o contrato da Onda 3**, e o `dono` é obrigatório sem comportamento |
| 3 | `core/documentary_relationship.py` | 2 + testes | 531 linhas: decide o parentesco, o rótulo, a janela de cM, 7 códigos de aviso **e** o cache de nomes — quase toda a coluna "documental" do domínio |
| 4 | `utils/validate.py` | 4 | Decide o que pode ser gravado **e** lido; a tela e o resolvedor perguntam a **mesma** função, e a forma de nome é a defesa contra escape |
| 5 | `utils/text_cleaning.py` | 5 | Decide a comparação de nomes em todo o sistema; a divergência entre duas cópias já custou 5 de 9 casos |
| 6 | `core/relationship_hypotheses.py` | 2 | A tabela e as janelas determinam **os quatro estados**; é o único módulo sem dependência de projeto |
| 7 | `reporting/mermaid_render.py` | 2 | Gramática de terceiro + 2 bugs de escape; o contrato é uma **lista branca** com ordem de operações obrigatória |
| 8 | `utils/number_format.py` | 2 | **A menor cobertura medida do projeto: 53 %** — e é a autoridade de **todo** número exibido |
| 9 | `core/diagram_domain.py` | 3 | É a costura que **mantém `reporting/` sem importar `core`**; alterá-lo reabre o ciclo |
| 10 | `tests/icone_de_atalho.py` · `banner_da_tela.py` | 3 | São a **fonte única** de duas artes: uma mudança aqui só é segura com o teste de deriva ao lado |

---

## 8. Lacunas da matriz 🔴

| ID | Lacuna | Conf. |
| --- | --- | --- |
| **X-01** | **A matriz não tem coluna de rastreabilidade para as specs de unidade**, porque elas serão regeradas na Fase 4. Depois da regeneração, esta matriz deve ser **relida contra as specs novas** — é a primeira coisa a fazer quando o Redator concluir. As unidades passaram de 4 para **5** nesta rodada. | 🔴 |
| **X-02** | **Não há vínculo automático SPEC ↔ CODE ↔ TEST ↔ BUG.** As matrizes de `_reversa_bugs/*/generated/` derivam das specs de **2026-10-05** e ancoram em contratos que esta rodada reescreveu. Esta matriz é **manual**. | 🔴 |
| **X-03** | **A cobertura de linha foi REMEDIDA em 2026-10-10 pelo Revisor** (`pytest-cov` no `.venv`, `DATABASE_URL` limpa): **`src/` = 89 %** (2.081 instruções, 228 não cobertas; eram 83 % em 2026-10-05, sobre um `src/` que dobrou de tamanho). **A pior cobertura trocou de dono:** `ports/adaptadores.py` **73 %** — e é exatamente o módulo cujo caminho de gravação não tem teste feliz (`L-28`/`X-05`); `app.py` **77 %**; `relationship_hypotheses` **78 %**; `mermaid_render` **78 %**; `name_normalization` **81 %**; `matching` **86 %**; `number_format` **87 %** (era **53 %**, a pior da rodada anterior); `evidence_comparison` **89 %**. **Decisão humana de 2026-10-10: remedir** — e o número encontrado é *acionável*: a pior cobertura do projeto está no módulo onde a lacuna já apontava. | 🟢 |
| **X-04** | **A ordem de inserção das arestas do grafo continua sem teste.** Ela determina qual caminho o `shortest_path` devolve e é a lacuna `E-01` do ERD. | 🟡 |
| **X-05** | 🔴 **NOVA: o caminho de gravação no banco não tem teste.** `RegistroDeAnalisesPostgres._escrever` (a ordem das FKs, os tipos, as transações) só é exercitado no contêiner. `L-28` / `E-07`. | 🟢 |
| **X-06** | 🔴 **NOVA: a arte derivada não é verificada no ambiente do container.** Os testes rodam no host, onde `docs/` existe. Se a arte falhar na imagem, a degradação é o `404` — exatamente o caso que a escolha de `src/assets/` existe para evitar. | 🟢 |
| **X-07** | 🟡 **NOVA: a coluna "área de teste" perdeu granularidade por arquivo.** Com 39 arquivos, uma coluna por arquivo deixou de ser legível; o mapa área → arquivos está na §4. | 🟢 |

---

*Gerado pelo Reversa-Architect em 2026-10-10 (re-extração, nível completo).*

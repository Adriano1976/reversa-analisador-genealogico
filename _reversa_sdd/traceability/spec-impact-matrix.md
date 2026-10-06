# Matriz de Impacto entre Componentes — analisador-genealogico

> Nível de documentação: **Completo** (`state.json` → `doc_level`)
> Re-extração de **2026-10-05**. Artefato **novo** — o nível `essencial` não o gera.
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

> ⚠️ **Nota de validade.** As specs de unidade (`<unit>/requirements.md`, `design.md`, `tasks.md`) são as de **2026-09-30** e serão **regeradas na Fase 4** pelo Redator. Por isso a matriz é expressa em termos de **unidade funcional + artefato**, e não de linha de spec — ela continua válida depois da regeneração.

**As quatro unidades funcionais** (decisão `[specs] granularity = endpoint`, persistida em `.reversa/config.toml`):

| Unidade | Superfície | Implementação |
| --- | --- | --- |
| `upload-gedcom` | `POST action=upload_gedcom` | `parsers/gedcom_parser.py`, `core/gedcom_state.py`, `utils/validate.py`, `utils/text_cleaning.py` |
| `analise-dna` | `POST action=dna_analysis` | `core/dna_analysis.py` + 7 módulos de `core/` + `parsers/csv_ingest.py` |
| `busca-caminho` | `POST action=path_search` | `core/path_search.py`, `path_finding.py`, `family_navigation.py`, `documentary_relationship.py`, `reporting/mermaid_render.py` |
| Transversal | `GET /` + os três ramos | `app.py`, `utils/number_format.py` |

---

## 2. Matriz A — Componente × Unidade funcional

| Componente | `upload-gedcom` | `analise-dna` | `busca-caminho` | Transversal |
| --- | :---: | :---: | :---: | :---: |
| `app.py` | ● | ● | ● | ● |
| `utils/validate.py` | ● | ○ | ○ | ● |
| `utils/number_format.py` | — | ● | ○ | ● |
| `utils/text_cleaning.py` | ● | ● | ● | ○ |
| `parsers/gedcom_parser.py` | ● | ○ | ○ | ○ |
| `parsers/csv_ingest.py` | — | ● | — | — |
| `core/gedcom_state.py` | ● | ● | ● | ● |
| `core/name_normalization.py` | — | ● | ○ | — |
| `core/matching.py` | — | ● | — | — |
| `core/family_navigation.py` | — | ○ | ● | — |
| `core/path_finding.py` | — | ○ | ● | — |
| `core/documentary_relationship.py` | — | ● | ● | — |
| `core/genetic_evidence.py` | — | ● | — | — |
| `core/relationship_hypotheses.py` | — | ● | — | — |
| `core/evidence_comparison.py` | — | ● | — | — |
| `core/path_search.py` | — | ○ | ● | — |
| `core/dna_analysis.py` | — | ● | ○ | — |
| `core/cm_estimator.py` | — | ○ *(legado)* | — | — |
| `reporting/mermaid_render.py` | — | ● | ● | — |

**Leitura dos quatro transversais que aparecem em tudo:**

| Componente | Por que atravessa | Risco ao alterar |
| --- | --- | --- |
| `core/gedcom_state.py` | É o **estado compartilhado**: importado por **8 dos 19 módulos** | **Máximo.** As assimetrias (mutação *in place* vs reatribuição) são contrato, não estilo |
| `app.py` | Único ponto de entrada; valida, grava, re-parseia e renderiza | Alto — a ordem das guardas e a re-parse antes de ramificar são contrato |
| `utils/text_cleaning.py` | Decide a **comparação de nomes** em 5 consumidores | Alto — duas cópias divergentes já produziram 5 de 9 casos errados (ADR-07) |
| `utils/validate.py` | Toda a decisão sobre o que pode ser gravado e lido | **Alto (segurança)** — a validação por forma é a defesa contra escape de caminho |

---

## 3. Matriz B — Componente × Artefato de documentação

● = é **fonte primária** do artefato · ○ = contribui · — = não aparece

| Componente | `code-analysis.md` | `data-dictionary.md` | `flowcharts/` | `domain.md` | `architecture.md` | `erd-complete.md` | `adrs/` |
| --- | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| `app.py` | ● | ● | ● | ● | ● | ● | ○ |
| `utils/validate.py` | ● | ● | ● | ● | ○ | ● | ○ |
| `utils/number_format.py` | ● | ○ | ○ | ○ | ○ | ○ | ○ |
| `utils/text_cleaning.py` | ● | ○ | ○ | ● | ○ | ○ | ● |
| `parsers/gedcom_parser.py` | ● | ● | ● | ● | ● | ● | ○ |
| `parsers/csv_ingest.py` | ● | ● | ● | ● | ○ | ● | ● |
| `core/gedcom_state.py` | ● | ● | ● | ● | ● | ● | ○ |
| `core/name_normalization.py` | ● | ○ | ○ | ● | ○ | ○ | ○ |
| `core/matching.py` | ● | ○ | ● | ● | ● | ○ | ● |
| `core/family_navigation.py` | ● | ○ | ● | ● | ○ | ● | ○ |
| `core/path_finding.py` | ● | ○ | ● | ● | ○ | ○ | ○ |
| `core/documentary_relationship.py` | ● | ● | ● | ● | ● | ● | ● |
| `core/genetic_evidence.py` | ● | ● | ● | ● | ○ | ● | ● |
| `core/relationship_hypotheses.py` | ● | ● | ● | ● | ● | ● | ● |
| `core/evidence_comparison.py` | ● | ● | ● | ● | ● | ● | ● |
| `core/path_search.py` | ● | ● | ● | ● | ○ | ● | ● |
| `core/dna_analysis.py` | ● | ● | ● | ● | ● | ● | ● |
| `core/cm_estimator.py` | ● | ○ | ○ | ● | ○ | ○ | ● |
| `reporting/mermaid_render.py` | ● | ○ | ● | ● | ○ | ○ | ● |

**Os 6 componentes que alimentam os 23 ADRs** (● na última coluna) são os que **já mudaram de decisão** alguma vez: `text_cleaning`, `csv_ingest`, `matching`, `documentary_relationship`, `genetic_evidence`, `relationship_hypotheses`, `evidence_comparison`, `path_search`, `dna_analysis`, `cm_estimator`, `mermaid_render`. **Concentração de decisões = concentração de risco de reimplementação.**

---

## 4. Matriz C — Componente × Teste

● = coberto diretamente · ○ = exercitado de passagem · — = não coberto

| Componente | `test_domain` | `test_upload` | `test_upload_seguranca` | `test_path_search` | `test_dna_analysis` | `test_formatacao_cm` | `test_charac_matching` | `test_charac_mermaid` | `test_mermaid_escape` | `test_confrontacao` | `test_servidor_producao` |
| --- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| `app.py` | — | ○ | ● | ○ | ○ | ● | — | — | — | — | ● |
| `utils/validate.py` | — | ○ | ● | — | — | — | — | — | — | — | — |
| `utils/number_format.py` | — | — | — | — | — | ● | — | — | — | — | — |
| `utils/text_cleaning.py` | ● | ○ | — | — | ○ | — | ○ | — | — | ○ | — |
| `parsers/gedcom_parser.py` | — | ● | — | ● | ● | ● | ● | ● | ● | ● | — |
| `parsers/csv_ingest.py` | — | — | — | — | ● | ○ | ○ | — | — | ● | — |
| `core/gedcom_state.py` | — | ● | — | ● | ● | — | ● | ● | — | — | — |
| `core/name_normalization.py` | — | — | — | — | ○ | — | ● | — | — | — | — |
| `core/matching.py` | — | — | — | — | ● | — | ● | — | — | — | — |
| `core/family_navigation.py` | — | — | — | ● | — | — | — | ○ | — | ● | — |
| `core/path_finding.py` | — | — | — | ● | — | — | — | ○ | — | ● | — |
| `core/documentary_relationship.py` | — | — | — | ● | — | — | — | — | — | ● | — |
| `core/genetic_evidence.py` | — | — | — | — | ○ | ● | — | — | — | ● | — |
| `core/relationship_hypotheses.py` | — | — | — | — | ○ | — | — | — | — | ● | — |
| `core/evidence_comparison.py` | — | — | — | — | — | — | — | — | — | ● | — |
| `core/path_search.py` | — | — | — | ● | — | — | — | ● | ● | ● | — |
| `core/dna_analysis.py` | — | — | — | — | ● | ● | ● | — | — | ● | — |
| `core/cm_estimator.py` | — | — | — | — | ● | — | — | — | — | — | — |
| `reporting/mermaid_render.py` | — | — | — | ○ | — | — | — | ● | ● | — | — |

### 🔴 Cobertura desigual — leitura da matriz

| Situação | Componentes | Comentário |
| --- | --- | --- |
| **Bem cobertos** | `validate` (425 linhas / 33 funções), `evidence_comparison` + `relationship_hypotheses` + `documentary_relationship` (922 linhas / 27 funções), `mermaid_render` (caracterização + contrato de escape) | As três áreas que **já tiveram bug ou decisão humana** ganharam rede de segurança |
| **Cobertos por um único arquivo** | `number_format` (só `test_formatacao_cm`) e `matching` (só caracterização + `test_dna_analysis`) | Rede fina: uma regressão fora do caso caracterizado passa |
| **Só exercitados de passagem** | `csv_ingest` fora de `test_confrontacao`; `family_navigation` e `path_finding` fora de `test_path_search` | Sem teste de unidade dedicado |
| **Sem cobertura dedicada** | `core/cm_estimator.py` é o único componente cuja cobertura é **declaradamente de compatibilidade** — ele existe **porque** o teste o exercita | Coerente com ADR-19 |

> **`test_servidor_producao.py` analisa o `app.py` por AST** em vez de executá-lo — cobre o **bloco de entrada**, não a rota. `app.py` aparece em 5 arquivos, mas a **rota em si** (guardas e despacho) só é exercitada de passagem.

---

## 5. Matriz D — Constante compartilhada × Consumidores

Esta é a matriz **mais acionável** do documento: em um sistema cujo comportamento é decidido por limiares, mudar um número propaga silenciosamente.

| Constante | Valor | Definida em | Consumidores | Propaga para | Conf. |
| --- | --- | --- | --- | --- | --- |
| `MAX_DEPTH` | `20` | `path_finding.py:25` | `find_ancestral_path`, `documentary_relationship.documentary_relationship`, `path_search` (reexporta) | ⚠️ **A mensagem de contrato do aviso `sem_caminho` interpola o valor** (`documentary_relationship.py:455-457`) — mudar a constante **muda texto que o operador lê** | 🟢 |
| `MAX_HOPS` | `40` | `path_finding.py:28` | `find_indirect_path`, `path_search` | Teto do caminho indireto; define `affinity` | 🟢 |
| `IDADE_MINIMA_GENITOR` / `IDADE_MAXIMA_GENITOR` | `12` / `70` | `documentary_relationship.py:41-42` | `hop_evidence` | Campo `plausible` e aviso `data_impossivel` (com as idades e datas no texto) | 🟢 |
| `MAX_DEPTH_ALTERNATIVOS` | `12` | `documentary_relationship.py:47` | `find_all_common_ancestors`, `_cadeias_ate` | Cardinalidade de `common_ancestors` e detecção de colapso | 🟢 |
| `LIMITE_DE_CADEIAS` | `8` | `documentary_relationship.py:48` | `_cadeias_ate` | Aviso `colapso_de_pedigree` — **teto do que é detectável** | 🟢 |
| `LIMITE_DE_CANDIDATOS` | `5` | `path_search.py:71` | Combinador 5×5 de homônimos | Qual registro vence na busca com nomes repetidos | 🟢 |
| `LIMITE_SEGMENTO_FRACO` | `15.0` | `genetic_evidence.py:31` | `weak_segment` | Aviso `segmento_fraco` — **heurística do projeto** (ADR-19) | 🟢 |
| `LIMITE_DE_PREAMBULO` | `10` | `csv_ingest.py:51` | `localizar_cabecalho` | Onde o cabeçalho do CSV pode estar | 🟢 |
| `MAX_CONTENT_LENGTH` | 16 MB | `app.py:32` | Guarda de corpo | ⚠️ **A mensagem `413` interpola o valor em MB** — mudar a constante muda texto de contrato | 🟢 |
| `_FORMATO_CHAVE` | `^[0-9a-f]{16}__[A-Za-z0-9._-]+$` | `validate.py:32` | `chave_recebida_e_valida` | 🔴 **Defesa de segurança**: afrouxá-la reabre o escape de caminho do `BUG-20260929-QMLY` | 🟢 |
| `CABECALHO_GEDCOM` | `0 HEAD` | `validate.py:26` | `validar_conteudo_gedcom` | O que é aceito como GEDCOM | 🟢 |
| `CASAS` | `2` | `number_format.py:14` | `formatar_cm` | **Todo** número exibido na tela | 🟢 |
| `SEPARADORES` | `,` `;` TAB `\|` | `csv_ingest.py:46` | `detectar_separador` | ⚠️ **A ordem importa**: no empate vence a vírgula | 🟢 |
| `SCP40_ROWS` / `SCP40_NOT_PUBLISHED` | 27 / 6 relações | `relationship_hypotheses.py:64-103` | `possible_relationships`, `hypotheses_for_evidence`, `_janela_do_documental` | ⚠️ **Altera o confronto inteiro**: as janelas e os 4 estados derivam daqui | 🟢 |
| `CAUSAS_POSSIVEIS` / `CAUSAS_POSSIVEL` | 12 / 9 itens | `evidence_comparison.py:55-72` | `compare` | Texto do rol de causas em `CONFLITANTE` e `POSSIVEL` | 🟢 |
| Pesos do score | `0.55` / `0.25` / `0.20` | `matching.py:101` | `match_candidates` | 🔴 **Quem é aceito no matching** | 🟢 |
| Bônus de sobrenome | `+8.0` / `−4.0` | `matching.py:100` | `match_candidates` | Idem | 🟢 |
| Limiar de cM do Jaccard | `150` | `matching.py:134` | Ramo do Jaccard 0,33 | Idem — **decisão humana** de 2026-08-03 | 🟢 |
| Limiares dos 5 ramos de aceite | ver `matching.py:140-155` | **literais, não constantes** | `match_candidates` | 🔴 **Quem é aceito** — `100/0,67`, `80/0,50`, `86/0,80`, `92`, `88`, e o rebaixamento `96/92` de `:161` | 🟢 |
| `STOP_WORDS`, `GENERIC_GIVENS`, `SURNAME_SUFFIXES`, `COMMON_SURNAMES`, `SURNAME_EQUIV` | ver `name_normalization.py:22-49` | idem | `split_name_pt`, `surnames_set`, `match_candidates` | 🔴 Decompõe o nome e decide o prenome/sobrenomes de **todo** o matching | 🟢 |

### 🔴 O achado desta matriz: dois limiares de contrato e um ponto sem ponto único

1. **`MAX_DEPTH` e `MAX_CONTENT_LENGTH` estão embutidos em mensagens que o operador lê.** Mudar o número **não é** uma mudança de parâmetro: é uma **mudança de texto de contrato**, que goldens e testes podem fixar. Quem reimplementar precisa decidir se a mensagem continua interpolando.
2. **Os limiares de aceitação do matching não são constantes nomeadas.** Isso é **consequência direta do ADR-08** (não criar constantes que o legado não tinha), e tem um custo que o ADR não registrou: **não existe ponto único de mudança** para a regra mais sensível do sistema. Alterar a "generosidade" do matching exige editar literais dentro de cinco ramos condicionais.

---

## 6. Matriz E — Componente × Defeito registrado (SPEC ↔ CODE ↔ TEST ↔ BUG)

| Bug | Severidade | Componentes afetados | Teste de regressão | Estado |
| --- | --- | --- | --- | --- |
| `BUG-20260929-QMLY` — upload sem limites | Alta | `app.py`, `utils/validate.py` | `test_upload_seguranca.py` (425 linhas, 33 funções) | ✅ Corrigido |
| `BUG-20260929-J6PQ` — escape incompleto no rótulo Mermaid | Alta | `reporting/mermaid_render.py` | `test_mermaid_escape.py` (19 testes novos) | ✅ Corrigido |
| `BUG-20261002-T4ZM` — rótulo descarta caracteres inertes | Média | `reporting/mermaid_render.py` | `test_mermaid_escape.py` | ✅ Corrigido |
| `BUG-20260929-BJJH` — exposição de árvore entre usuários | **Crítica / P0** | `core/gedcom_state.py`, `app.py`, `templates/index.html` | **Nenhum** — inaplicável ao legado (sem identidade) | ⚠️ **Aberto**, mitigado por aceite de risco |
| `BUG-20261004-EWSJ` — badge de cM com ruído de ponto flutuante | Baixa | `utils/number_format.py`, `app.py`, `templates/index.html` | `test_formatacao_cm.py` | ✅ Corrigido |

**Observações de rastreabilidade:**

- **`reporting/mermaid_render.py` é o componente com mais defeitos registrados** (2 de 5) e o único cuja correção precisou ser **refeita** — a primeira versão da lista branca era estreita demais. É o componente com maior densidade de contrato implícito.
- 🔴 **O `BUG-20260929-BJJH` é o único defeito crítico sem teste de regressão**, e não por descuido: o critério de aceite dele ("requisição à árvore de outro dono responde 404") é **inaplicável** ao legado por não existir identidade. A cobertura dele pertence à Onda 3 da migração (ADR-18).
- 🔴 **4 componentes nunca tiveram defeito registrado nem decisão humana verificada**: `utils/number_format.py`, `core/genetic_evidence.py`, `core/relationship_hypotheses.py` e `core/path_finding.py`. Nos três últimos, isso **não** significa baixo risco — todos alimentam o veredito do confronto.

---

## 7. Componentes de maior alcance (ordem de risco)

| # | Componente | Dependents diretos | Por que é o mais arriscado de alterar |
| ---: | --- | ---: | --- |
| 1 | `core/gedcom_state.py` | **8** | É o estado global; as regras de mutação *in place* vs reatribuição são contrato, e o `versao` é o único sinal de invalidação |
| 2 | `core/documentary_relationship.py` | 2 + testes | 576 linhas, decide o parentesco, o rótulo, a janela de cM e 7 códigos de aviso — quase toda a coluna "documental" do domínio |
| 3 | `utils/text_cleaning.py` | 5 | Decide a comparação de nomes em todo o sistema; a divergência entre duas cópias já custou 5 de 9 casos |
| 4 | `core/relationship_hypotheses.py` | 2 | A tabela e as janelas determinam **os quatro estados** do confronto; é o único módulo sem dependência de projeto |
| 5 | `reporting/mermaid_render.py` | 2 | Gramática de terceiro + 2 bugs de escape; o contrato é uma **lista branca** com ordem de operações obrigatória |
| 6 | `utils/number_format.py` | 2 | **A menor cobertura medida do projeto: 53 %** — e é a autoridade de **todo** número exibido na tela |

---

## 8. Lacunas da matriz 🔴

| ID | Lacuna | Conf. |
| --- | --- | --- |
| **X-01** | **A matriz não tem coluna de rastreabilidade para as specs de unidade**, porque elas serão regeradas na Fase 4 e as atuais (`2026-09-30`) descrevem o código anterior ao refactor. Depois da regeneração, esta matriz deve ser **relida contra as specs novas** — é a primeira coisa a fazer quando o Redator concluir. | 🔴 |
| **X-02** | **Não há vínculo automático SPEC ↔ CODE ↔ TEST.** As matrizes de `_reversa_bugs/*/generated/` derivam das specs de 2026-09-30 e estão defasadas. Esta matriz é **manual** e precisa de releitura a cada rodada. | 🔴 |
| **X-03** | **Três componentes de alto risco têm pouca cobertura dedicada.** A medição de 2026-10-05 (com `pytest-cov`) dá nome ao risco: `number_format` **53 %**, `relationship_hypotheses` **76 %**, `mermaid_render` **78 %**, `evidence_comparison` **83 %** — contra 98 % de `validate` e 97 % de `dna_analysis`. Cobertura **global de `src/`: 83 %** (1.520 instruções, 253 descobertas). | 🟡 medida |
| **X-04** | **A ordem de inserção das arestas do grafo não está sob teste.** Ela determina qual caminho o `shortest_path` devolve (`BR-MIGRAR-024`) e é a lacuna `E-01` do ERD. Não há teste que congele essa ordem. | 🟡 |

---

*Gerado pelo Reversa-Architect em 2026-10-05 (re-extração, nível completo).*

# Code-Spec Matrix — analisador-genealogico

> Nível de documentação: **Completo** (`state.json` → `doc_level`)
> Re-extração de **2026-10-05**. Artefato **novo** — o nível `essencial` não o gera.
> Este arquivo responde à pergunta: **por arquivo do legado, qual unit cobre o quê?**
> Compartilha o escopo com `spec-impact-matrix.md` (que faz o caminho inverso: de componente para impacto). Visão geral: `architecture.md`
> Escala de confiança: 🟢 CONFIRMADO | 🟡 INFERIDO | 🔴 LACUNA

---

## 1. Como ler

| Marcador | Significado |
| --- | --- |
| 🟢 | **Coberto diretamente** — há requisito, design e tarefa na unit correspondente |
| 🟡 | **Coberto parcialmente** — só por compatibilidade, ou compartilhado entre units sem dono explícito |
| **n/a** | **Sem unit correspondente** — arquivo de infraestrutura, vazio ou fora do escopo de runtime |

**As três units** seguem a granularidade `endpoint` (`config.toml [specs]`): `upload-gedcom`, `analise-dna`, `busca-caminho`. O que não pertence a nenhuma delas é **transversal** e está coberto por `architecture.md`, `domain.md`, `c4-*.md` e `contracts.md` das units que o consomem.

---

## 2. Arquivos de código (`src/`)

| Arquivo do legado | Unit correspondente | Cobertura | Observação |
| --- | --- | --- | --- |
| `src/app.py` | **transversal** + as três units | 🟢 | Rota única; cada ramo de `action` pertence a uma unit; o bloco de entrada (waitress, instância única) é transversal |
| `src/parsers/gedcom_parser.py` | `upload-gedcom` | 🟢 | Traduz GEDCOM em registros e grafo; **substitui** o estado |
| `src/parsers/csv_ingest.py` | `analise-dna` | 🟢 | Leitura tolerante, colunas por papel, agregação de cM |
| `src/parsers/__init__.py` | — | **n/a** | Vazio |
| `src/core/gedcom_state.py` | **transversal** | 🟢 | Estado do processo consumido pelas três units; coberto em `contracts.md` §3 de `upload-gedcom` |
| `src/core/documentary_relationship.py` | `busca-caminho` (+ `analise-dna`) | 🟢 | Parentesco documental; compartilhado — a mesma função serve as duas units |
| `src/core/genetic_evidence.py` | `analise-dna` | 🟢 | Evidência por (nome, kit) |
| `src/core/relationship_hypotheses.py` | `analise-dna` | 🟢 | Possibilidades pela tabela publicada |
| `src/core/evidence_comparison.py` | `analise-dna` | 🟢 | O confronto em quatro estados |
| `src/core/dna_analysis.py` | `analise-dna` | 🟢 | Orquestra as três etapas |
| `src/core/matching.py` | `analise-dna` | 🟢 | Índices e decisão de aceitação |
| `src/core/name_normalization.py` | `analise-dna` | 🟢 | Normalização e vocabulário do matching |
| `src/core/cm_estimator.py` | `analise-dna` | 🟡 | **LEGADO fora do fluxo.** Coberto **apenas como superfície de compatibilidade** (`RF-25`, `T-32`) |
| `src/core/path_search.py` | `busca-caminho` | 🟢 | Fachada da busca |
| `src/core/path_finding.py` | `busca-caminho` | 🟢 | BFS bidirecional e caminho indireto |
| `src/core/family_navigation.py` | `busca-caminho` | 🟢 | Resolução de pessoa e navegação familiar |
| `src/core/__init__.py` | — | **n/a** | Vazio |
| `src/reporting/mermaid_render.py` | `busca-caminho` (+ `analise-dna`) | 🟢 | Diagrama e **contrato de escape**; a unit de DNA consome o diagrama direto |
| `src/reporting/__init__.py` | — | **n/a** | Vazio |
| `src/utils/validate.py` | `upload-gedcom` | 🟢 | Autoridade do que pode ser gravado |
| `src/utils/text_cleaning.py` | **transversal** | 🟢 | Autoridade única de mojibake; consumida por `upload-gedcom`, `analise-dna` e `busca-caminho` |
| `src/utils/number_format.py` | **transversal** | 🟢 | Autoridade de exibição numérica; consumida pela tela da unit `analise-dna` |
| `src/utils/__init__.py` | — | **n/a** | Vazio |
| `src/templates/index.html` | **transversal** | 🟢 | Tela única; contém os formulários das três units e as quatro seções do resultado |

**Subtotal:** 24 arquivos — **19 🟢** · **1 🟡** · **4 n/a**

---

## 3. Arquivos de teste (`tests/`)

| Arquivo do legado | Unit coberta | Cobertura | Observação |
| --- | --- | --- | --- |
| `tests/test_upload.py` | `upload-gedcom` | 🟢 | Carga, grafo, tipos de nó, recarga |
| `tests/test_upload_seguranca.py` | `upload-gedcom` | 🟢 | 425 linhas, 33 funções: teto, chave de conteúdo, recusa de GEDCOM |
| `tests/test_domain.py` | `upload-gedcom` | 🟢 | Limpeza de mojibake (o nome do arquivo é histórico) |
| `tests/test_path_search.py` | `busca-caminho` | 🟢 | Direta, indireta, sem conexão, pessoas idênticas |
| `tests/test_characterization_mermaid.py` | `busca-caminho` | 🟢 | Congela a saída do diagrama |
| `tests/test_mermaid_escape.py` | `busca-caminho` | 🟢 | Contrato de escape do rótulo |
| `tests/test_dna_analysis.py` | `analise-dna` | 🟢 | Pipeline, colunas, agregação, compatibilidade do `cm_estimator` |
| `tests/test_characterization_matching.py` | `analise-dna` | 🟢 | Congela a decisão de matching |
| `tests/test_formatacao_cm.py` | `analise-dna` + transversal | 🟢 | Congela o **não arredondamento** do cM no núcleo |
| `tests/test_confrontacao_gedcom_dna.py` | `analise-dna` (+ `busca-caminho`) | 🟢 | 922 linhas, 27 funções: as três etapas e o confronto |
| `tests/test_servidor_producao.py` | **transversal** | 🟢 | Bloco de entrada, instância única, padrão de endereço (analisa `app.py` por AST) |
| `tests/fixtures/sample_gedcom.py` | — | **n/a** | Gerador de fixture, não é teste |
| `tests/fixtures/sample_dna.py` | — | **n/a** | Gerador de fixture, não é teste |

**Subtotal:** 13 arquivos — **11 🟢** · **2 n/a**

---

## 4. Configuração e infraestrutura

| Arquivo | Unit | Cobertura | Observação |
| --- | --- | --- | --- |
| `requirements.txt` | **transversal** | 🟢 | As seis dependências diretas pinadas (`adrs/13`); documentado em `architecture.md` §7 |
| `pytest.ini` | — | **n/a** | `testpaths = tests` |
| `pyrefly.toml` | — | **n/a** | `search-path = ["src"]` |
| `.vscode/settings.json` | — | **n/a** | `python.analysis.extraPaths = ["./src"]` |
| `.markdownlint-cli2.jsonc` | — | **n/a** | Regras de lint do repositório |
| `.gitignore`, `.gitattributes` | — | **n/a** | Versionamento |
| `.github/workflows/deploy-pages.yml` | — | **n/a** | Escuta a branch `main`, que não existe: não dispara por push. Quem publica é `master` / `docs`. **Não há pipeline de teste, build ou análise estática** |
| `README.md` | — | **n/a** | Única superfície de documentação em dia (2026-10-05) |
| `LICENSE` | — | **n/a** | MIT |
| `plugins/dsh-markdownlint/` | — | **n/a** | Sub-projeto Node/JavaScript fora do runtime |
| `docs/` | — | **n/a** | **Pasta publicada no GitHub Pages** (source `master`, folder `/docs`); cópia do mini-site de `_reversa_docs/` |
| `_reversa_*/`, `.reversa/`, `.agents/` | — | **n/a** | Framework Reversa |

---

## 5. Cobertura estimada

| Escopo | Arquivos | Cobertos por alguma unit | Parcial | Sem unit | **% coberto** |
| --- | ---: | ---: | ---: | ---: | ---: |
| `src/` (código de runtime) | 24 | 19 | 1 | 4 | **83,3 %** |
| `tests/` | 13 | 11 | 0 | 2 | **84,6 %** |
| **Runtime total (`src/` + `tests/`)** | **37** | **30** | **1** | **6** | **83,8 %** |

> **Contando o parcial como coberto** (o `cm_estimator` está coberto como superfície de compatibilidade, com requisito e tarefa próprios), a cobertura sobe para **31 de 37 = 83,8 %**, e a cobertura do **código de runtime** para **20 de 24 = 83,3 %**.
>
> Os **4 arquivos `n/a` de `src/` são `__init__.py` vazios**, e os **2 de `tests/` são geradores de fixture** — nenhum dos seis contém comportamento a especificar. **Excluindo-os do denominador, a cobertura é 31 de 31 = 100 %.**

### Arquivos sem unit correspondente — e por quê

| Arquivo | Por que não tem unit |
| --- | --- |
| `src/parsers/__init__.py`, `src/core/__init__.py`, `src/reporting/__init__.py`, `src/utils/__init__.py` | **Vazios.** Não há comportamento a especificar |
| `tests/fixtures/sample_gedcom.py`, `tests/fixtures/sample_dna.py` | **Geradores de fixture**, não testes: produzem o GEDCOM e o CSV usados pela suíte |

> **Não há arquivo de runtime sem cobertura.** O único caso limítrofe é `cm_estimator.py`, que **existe** em runtime mas está **fora do fluxo** — e por isso recebeu requisito próprio (`RF-25`) e tarefa própria (`T-32`), em vez de ficar sem dono.

---

## 6. Lacunas desta matriz 🔴

| ID | Lacuna | Conf. |
| --- | --- | --- |
| **CS-01** | **O `app.py` é o único arquivo com três donos.** Cada ramo de `action` pertence a uma unit, mas a **ordem das guardas** e a **re-parse antes de ramificar** (`:126-132`) atravessam as três e estão especificadas em cada uma delas — o que significa que uma mudança ali exige atualizar **três** specs. | 🟢 |
| **CS-02** | **`documentary_relationship.py` e `mermaid_render.py` são compartilhados** entre `busca-caminho` e `analise-dna`. A matriz atribui a `busca-caminho` como dona, mas a unit de DNA depende do comportamento deles — há acoplamento entre specs, não só entre módulos. | 🟢 |
| **CS-03** | **Não há rastreabilidade automática** entre esta matriz e as specs de unidade: ela é manual e precisa de releitura quando as specs mudam. As matrizes de `_reversa_bugs/*/generated/` derivam das specs de 2026-09-30 e estão defasadas. | 🔴 |
| **CS-04** | **A cobertura é de arquivo, não de comportamento.** "🟢 coberto" significa que há requisito, design e tarefa para o arquivo — **não** que todo caminho de execução dele esteja especificado. Não há medição de cobertura de linha ou de ramo. | 🔴 |
| **CS-05** | **Zero arquivos sem unit no runtime**, o que parece bom demais: o efeito real é que **quase tudo depende de `gedcom_state`**, e um arquivo central compartilhado por 8 módulos não pode ser "de uma unit". A matriz esconde essa concentração — ela está visível na **Matriz D** de `spec-impact-matrix.md`. | 🟢 |

---

*Gerado pelo Reversa-Writer em 2026-10-05 (re-extração, nível completo).*

# Code-Spec Matrix — analisador-genealogico

> Nível de documentação: **Completo** (`state.json` → `doc_level`)
> Re-extração de **2026-10-10**. Substitui a versão de 2026-10-05, que mapeava **3 units** e um `src/` de 24 arquivos. Hoje são **5 units** e **35 arquivos Python**.
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

**As cinco units** seguem a granularidade `endpoint` (`config.toml [specs]`): `upload-gedcom`, `tela-de-entrada`, `analise-dna`, `busca-caminho` e `recursos-da-tela`. Duas delas são **novas** nesta rodada: `tela-de-entrada` (as duas abas, escolher da lista, aposentar) e `recursos-da-tela` (as duas rotas de arte). O que não pertence a nenhuma delas é **transversal** e está coberto por `architecture.md`, `domain.md`, `c4-*.md` e pelos `contracts.md` das units que o consomem.

---

## 2. Arquivos de código (`src/`)

### 2.1 Borda e aplicação

| Arquivo do legado | Unit correspondente | Cobertura | Observação |
| --- | --- | --- | --- |
| `src/app.py` | **transversal** + as cinco units | 🟢 | Rota única com cinco ramos de `action`, mais as duas rotas de arte e o bloco de entrada. **Cresceu de 267 para 559 linhas úteis** |
| `src/application/__init__.py` | `busca-caminho` (+ as outras) | 🟢 | O enum `Desfecho` e `nomes_de_exibicao`, compartilhada pelos três fluxos |
| `src/application/upload_gedcom.py` | `upload-gedcom` | 🟢 | Caso de uso do envio |
| `src/application/reenvio.py` | `upload-gedcom` (+ `analise-dna`) | 🟢 | A regra de reenvio com substituição, usada pelo GEDCOM **e** pelo CSV |
| `src/application/dna_analysis.py` | `analise-dna` | 🟢 | Caso de uso, projeção pura e registro |
| `src/application/path_search.py` | `busca-caminho` | 🟢 | Caso de uso com o desfecho em três valores |
| `src/application/traducao.py` | **transversal** | 🟢 | Tabela de tradução de exceção → literal de tela e status; consumida pelas units que levantam erro de domínio |

### 2.2 Portas e adaptadores

| Arquivo do legado | Unit correspondente | Cobertura | Observação |
| --- | --- | --- | --- |
| `src/ports/__init__.py` | **transversal** | 🟢 | As quatro portas e os payloads planos: `EntradaArmazenada`, `AnaliseParaRegistrar`, `PessoaDaAnalise`, `KitDaAnalise`, `ConexaoDaAnalise`, `DescartadoDaAnalise` |
| `src/ports/adaptadores.py` | **transversal** (+ `tela-de-entrada`, `upload-gedcom`, `analise-dna`) | 🟢 | `ArmazenamentoEmDisco`, `CarregadorDeArvoresGedcom` e `RegistroDeAnalisesPostgres` |

### 2.3 Núcleo

| Arquivo do legado | Unit correspondente | Cobertura | Observação |
| --- | --- | --- | --- |
| `src/core/documentary_relationship.py` | `busca-caminho` (+ `analise-dna`) | 🟢 | Parentesco documental; **compartilhado** — a mesma função serve as duas units |
| `src/core/path_search.py` | `busca-caminho` | 🟢 | Fachada da busca |
| `src/core/path_finding.py` | `busca-caminho` | 🟢 | BFS bidirecional e caminho indireto **sobre a árvore recebida** |
| `src/core/family_navigation.py` | `busca-caminho` | 🟢 | Resolução de pessoa e navegação familiar |
| `src/core/diagram_domain.py` | `busca-caminho` | 🟢 | **O resolvedor de diagrama** — as sete consultas que o renderizador recebe |
| `src/core/dna_analysis.py` | `analise-dna` | 🟢 | Orquestra os três eixos |
| `src/core/genetic_evidence.py` | `analise-dna` | 🟢 | Evidência por (nome, kit) |
| `src/core/relationship_hypotheses.py` | `analise-dna` | 🟢 | Possibilidades pela tabela publicada |
| `src/core/evidence_comparison.py` | `analise-dna` | 🟢 | O confronto em quatro estados |
| `src/core/matching.py` | `analise-dna` | 🟢 | Índices e decisão de aceitação, com o desempate em quatro níveis |
| `src/core/name_normalization.py` | `analise-dna` | 🟢 | Normalização e vocabulário do matching |
| `src/core/registro.py` | `analise-dna` (+ `upload-gedcom`) | 🟢 | `get_name` e `ref_id` — **cópia literal do oráculo** |
| `src/core/erros.py` | **transversal** | 🟢 | As cinco exceções de domínio irmãs |
| `src/core/cm_estimator.py` | `analise-dna` | 🟡 | **LEGADO fora do fluxo.** Coberto **apenas como superfície de compatibilidade** (`RF-34`) |
| `src/core/__init__.py` | — | **n/a** | Vazio |

### 2.4 Parsers, apresentação e utilidades

| Arquivo do legado | Unit correspondente | Cobertura | Observação |
| --- | --- | --- | --- |
| `src/parsers/gedcom_parser.py` | `upload-gedcom` | 🟢 | Traduz GEDCOM em registros e grafo; **devolve** a árvore |
| `src/parsers/csv_ingest.py` | `analise-dna` | 🟢 | Leitura tolerante, colunas por papel, agregação de cM |
| `src/parsers/__init__.py` | — | **n/a** | Vazio |
| `src/reporting/lista_de_arquivos.py` | `tela-de-entrada` | 🟢 | Funções **puras** que transformam entradas da pasta em itens de aba |
| `src/reporting/mermaid_render.py` | `busca-caminho` (+ `analise-dna`) | 🟢 | Diagrama e **contrato de escape**; **não importa `core`** |
| `src/reporting/__init__.py` | — | **n/a** | Vazio |
| `src/utils/validate.py` | `upload-gedcom` (+ `tela-de-entrada`) | 🟢 | Autoridade do que pode ser gravado **e** da forma do nome armazenado |
| `src/utils/text_cleaning.py` | **transversal** | 🟢 | Autoridade única de mojibake |
| `src/utils/number_format.py` | **transversal** | 🟢 | Autoridade de exibição numérica |
| `src/utils/name_keys.py` | `analise-dna` | 🟢 | `norm_name` |
| `src/utils/__init__.py` | — | **n/a** | Vazio |
| `src/templates/index.html` | **transversal** | 🟢 | Tela única: as duas abas, os cinco formulários, as seções de resultado e a masthead |
| `src/assets/apple-touch-icon.png` | `recursos-da-tela` | 🟢 | Arte **derivada**, commitada |
| `src/assets/banner-da-tela.png` | `recursos-da-tela` | 🟢 | Arte **derivada**, commitada |

**Subtotal de `src/`: 38 arquivos — 33 🟢 · 1 🟡 · 4 n/a**
*(35 arquivos `.py`, dos quais 30 🟢 · 1 🟡 · 4 n/a, mais `index.html` e as 2 artes, todos 🟢.)*

---

## 3. Arquivos de teste (`tests/`)

### 3.1 Contratos das units

| Arquivo | Unit coberta | Cobertura | Observação |
| --- | --- | --- | --- |
| `test_upload.py`, `test_upload_seguranca.py`, `test_domain.py` | `upload-gedcom` | 🟢 | Carga, grafo, teto, chave de conteúdo e limpeza de mojibake |
| `test_forma_da_referencia.py` | `upload-gedcom` + `tela-de-entrada` | 🟢 | A elegibilidade por **forma de nome**, nas duas funções |
| `test_reenvio_do_arquivo.py`, `test_reenvio_do_csv.py` | `upload-gedcom` + `analise-dna` | 🟢 | Os três desfechos do reenvio, nos dois tipos de arquivo |
| `test_porta_de_armazenamento.py`, `test_guardas_do_armazenamento.py` | `upload-gedcom` + `tela-de-entrada` | 🟢 | `guardar`, `resolver`, `listar` e `aposentar` |
| `test_manutencao_de_uploads.py` | `tela-de-entrada` | 🟢 | O que a tela enxerga depois de mexer na pasta |
| `test_lista_de_arquivos.py`, `test_lista_na_tela.py`, `test_tabela_da_tela.py` | `tela-de-entrada` | 🟢 | Função pura, processador de contexto e tabela |
| `test_aposentar_arquivo.py`, `test_voltar_para_a_lista.py` | `tela-de-entrada` | 🟢 | As duas ações da lista, incluindo a **ordem dos ramos** |
| `test_dna_analysis.py`, `test_characterization_matching.py`, `test_formatacao_cm.py`, `test_confrontacao_gedcom_dna.py` | `analise-dna` | 🟢 | Pipeline, caracterização, contrato de cM e o confronto |
| `test_projecao_da_analise.py`, `test_registro_de_analises.py` | `analise-dna` | 🟢 | Projeção **sem banco** e registro |
| `test_persistencia_desabilitada.py`, `test_persistencia_indisponivel.py` | `analise-dna` | 🟢 | Os dois estados degradados da persistência |
| `test_traducao_de_erros.py`, `test_erros_de_dominio.py` | `analise-dna` (+ transversais) | 🟢 | A tabela de tradução e a hierarquia das exceções |
| `test_campo_de_escolha_do_csv.py` | `analise-dna` + `tela-de-entrada` | 🟢 | Precedência da referência sobre o arquivo |
| `test_path_search.py`, `test_characterization_mermaid.py`, `test_mermaid_escape.py` | `busca-caminho` | 🟢 | Fluxo, caracterização e o contrato de escape |
| `test_desfecho_do_resultado.py` | `busca-caminho` | 🟢 | Os três valores do desfecho |
| `test_icone_de_atalho.py`, `test_banner_do_topo.py`, `test_deriva_da_arte.py` | `recursos-da-tela` | 🟢 | Contrato das rotas, IHDR, masthead, resíduo, 11 pontos e a deriva |

### 3.2 Transversais e infraestrutura de teste

| Arquivo | Unit coberta | Cobertura | Observação |
| --- | --- | --- | --- |
| `test_arvore_devolvida.py` | **transversal** | 🟢 | A árvore como **valor**, sem estado global |
| `test_dependencias_nucleo.py` | **transversal** | 🟢 | As dependências entre pacotes — é o que prova que `reporting/` não importa `core` |
| `test_servidor_producao.py` | **transversal** | 🟢 | Bloco de entrada, instância única e padrão de endereço (analisa `app.py` por AST) |
| `test_ambiente_temporario_da_suite.py` | **transversal** | 🟢 | Isolamento da suíte em relação à pasta real |
| `test_gedcom_ilegivel_nao_derruba.py` | `tela-de-entrada` (+ `analise-dna`) | 🟢 | A guarda de parse introduzida em 2026-10-10 |
| `test_documentacao_do_upload.py` | **transversal** | 🟢 | Documentação do caminho de upload |
| `test_rodar_paridade.py` | **transversal** | 🟢 | Guarda do harness de paridade |
| `conftest.py` | — | **n/a** | Fixtures da suíte |
| `icone_de_atalho.py`, `banner_da_tela.py` | `recursos-da-tela` | 🟢 | **As receitas** de derivação — código de teste por decisão |
| `manutencao_de_uploads.py`, `rodar_paridade.py` | — | **n/a** | Utilitários de manutenção e de execução, não testes |
| `fixtures/sample_gedcom.py`, `fixtures/sample_dna.py`, `fixtures/helpers.py`, `fixtures/arvore_atual.py` | — | **n/a** | Geradores de fixture |

**Subtotal de `tests/`: 48 arquivos — 40 🟢 · 0 🟡 · 8 n/a**
*(39 arquivos `test_*.py`, 5 módulos de apoio, 4 fixtures.)*

---

## 4. Configuração e infraestrutura

| Arquivo | Unit | Cobertura | Observação |
| --- | --- | --- | --- |
| `requirements.txt` | **transversal** | 🟢 | **Oito** dependências diretas **pinadas**, agora realinhadas ao `.venv` (`networkx==3.7`, `pandas==3.0.6`, `ged4py==0.5.5`); `psycopg2-binary` entra só para o adaptador de registro. **A biblioteca de imagem não está aqui** |
| `docker-compose.yml`, `docker/**` | **transversal** | 🟢 | Dois serviços (aplicação e banco), documentados em `adrs/28` |
| `.dockerignore` | `recursos-da-tela` (+ transversal) | 🟢 | Lista de **permissão** — é ela que decide onde a arte pode morar, e ela reexclui `src/uploads/` |
| `init.sql` | `analise-dna` | 🟢 | As **6 tabelas** idempotentes do histórico; **primeiro esquema físico do projeto** |
| `.gitignore` | **transversal** | 🟢 | A linha `uploads/` (com barra) é a garantia material de que os arquivos do operador não entram no versionamento |
| `pytest.ini` | — | **n/a** | `testpaths = tests` |
| `pyrefly.toml` | — | **n/a** | `search-path = ["src"]` |
| `.vscode/settings.json` | — | **n/a** | `python.analysis.extraPaths = ["./src"]` |
| `.markdownlint-cli2.jsonc` | — | **n/a** | Regras de lint do repositório |
| `publicar_docs.py` | — | **n/a** | Publica o mini-site; **não lê** `_reversa_sdd/addenda/` |
| `.github/workflows/deploy-pages.yml` | — | **n/a** | Escuta a branch `main`, que não existe: não dispara por push. Quem publica é `master` / `docs`. **Não há pipeline de teste, build ou análise estática** |
| `README.md` | — | **n/a** | Superfície de documentação do repositório |
| `LICENSE` | — | **n/a** | MIT |
| `plugins/dsh-markdownlint/` | — | **n/a** | Sub-projeto Node/JavaScript fora do runtime |
| `docs/` | — | **n/a** | **Pasta publicada no GitHub Pages**; contém as **fontes canônicas** da arte e a cópia do mini-site |
| `src/uploads/` · `src/assets/` | ver §2.4 | — | `uploads/` é **dado real do operador** (13 arquivos, incluindo um GEDCOM de 5,3 MB), fora do versionamento e fora do contexto de build. `assets/` é arte **commitada** |
| `_reversa_*/`, `.reversa/`, `.agents/` | — | **n/a** | Framework Reversa |

---

## 5. Cobertura estimada

| Escopo | Arquivos | Cobertos por alguma unit | Parcial | Sem unit | **% coberto** |
| --- | ---: | ---: | ---: | ---: | ---: |
| `src/` (código de runtime, `.py`) | 35 | 30 | 1 | 4 | **88,6 %** |
| `tests/` | 48 | 40 | 0 | 8 | **83,3 %** |
| **Runtime total (`src/` + `tests/`)** | **83** | **70** | **1** | **12** | **85,5 %** |

> **Convenção:** `% coberto` conta o parcial como coberto — é a mesma convenção da versão anterior, para que os números sejam comparáveis.
>
> Os **4 arquivos `n/a` de `src/` são `__init__.py` vazios**, e os **8 de `tests/` são geradores de fixture e utilitários de execução** — nenhum deles contém comportamento de negócio a especificar. **Excluindo-os do denominador, a cobertura é 71 de 71 = 100 %.**
>
> ⚠️ **A cobertura de `src/` SUBIU de 83,3 % para 88,6 %**, e por um motivo específico: o `src/` quase dobrou de tamanho (24 → 35 arquivos), mas os arquivos novos — `ports/`, `application/`, `diagram_domain.py`, `registro.py`, `erros.py`, `name_keys.py`, `lista_de_arquivos.py` — **entraram já com unit e especificação**, porque nasceram de features deste ciclo. O que permanece sem unit é exatamente o mesmo **tipo** de arquivo de antes: `__init__.py` vazios e geradores de fixture.

### Arquivos sem unit correspondente — e por quê

| Arquivo | Por que não tem unit |
| --- | --- |
| `src/parsers/__init__.py`, `src/core/__init__.py`, `src/reporting/__init__.py`, `src/utils/__init__.py`, `src/ports/__init__.py`… | **Vazios ou quase.** Não há comportamento a especificar — ver `CS-06` |
| `tests/fixtures/*.py`, `tests/conftest.py`, `tests/manutencao_de_uploads.py`, `tests/rodar_paridade.py` | **Geradores de fixture e utilitários de execução**, não testes de contrato |
| `publicar_docs.py`, `plugins/`, `docs/` | **Fora do escopo de runtime**: publicação, sub-projeto e ativo publicado |

---

## 6. Lacunas desta matriz 🔴

| ID | Lacuna | Conf. |
| --- | --- | --- |
| **CS-01** | **O `app.py` é o único arquivo com cinco donos.** Cada ramo de `action` pertence a uma unit, mas a **ordem das guardas** — aposentar **antes** de resolver a árvore — atravessa duas delas, e a resolução da árvore é consumida por três. Uma mudança ali exige atualizar **três specs**. O arquivo **cresceu mais que o dobro** nesta rodada (267 → 559 linhas úteis), e é o ponto de maior acoplamento entre specs. | 🟢 |
| **CS-02** | **`documentary_relationship.py` é compartilhado** entre `busca-caminho` e `analise-dna`, e `mermaid_render.py` também. A matriz atribui o primeiro a `busca-caminho` como dona, mas a unit de DNA **depende do comportamento dele** — há acoplamento entre specs, não só entre módulos. O achado `L-24` (colisão do cache de nomes) mostra o custo: **uma** regra em `busca-caminho` degrada silenciosamente os avisos de identidade ambígua de `analise-dna`. | 🟢 |
| **CS-03** | **Não há rastreabilidade automática** entre esta matriz e as specs de unidade: ela é manual e precisa de releitura quando as specs mudam. As matrizes de `_reversa_bugs/*/generated/` derivam das specs de **2026-09-30** e estão defasadas. | 🔴 |
| **CS-04** | **A cobertura é de arquivo, não de comportamento.** "🟢 coberto" significa que há requisito, design e tarefa para o arquivo — **não** que todo caminho de execução dele esteja especificado. Não há medição de cobertura de linha ou de ramo. | 🔴 |
| **CS-05** | ✅ **SUPERADA em 2026-10-10.** A versão anterior dizia que "quase tudo depende de `gedcom_state`, e um arquivo central compartilhado por 8 módulos não pode ser de uma unit". O módulo **deixou de existir**: a árvore é um **valor** que entra por parâmetro (`ADR-24`). A concentração que a matriz escondia **foi eliminada**, e não apenas documentada. | 🟢 |
| **CS-06** | ✅ **RESOLVIDA em 2026-10-10 pelo Revisor.** O bytecode órfão `src/core/__pycache__/gedcom_state.cpython-314.pyc` foi **removido** por decisão humana. Reverificado depois da remoção: **nenhum** bytecode de `src/` ficou sem o `.py` correspondente (os outros 34 conferem). | 🟢 |
| **CS-07** | **Duas units novas entraram sem arquivo próprio.** `tela-de-entrada` tem **um** arquivo puro (`lista_de_arquivos.py`) e o resto em `app.py`; `recursos-da-tela` tem **zero** arquivos de módulo — só duas rotas em `app.py` e duas receitas em `tests/`. A granularidade `endpoint` permite isso, mas significa que **a unit não corresponde a uma unidade de arquivo**, e a matriz deixa de ser suficiente para localizar o código de uma unit sem ler o `app.py`. | 🟢 |
| **CS-08** | **`src/uploads/` contém dado real dentro da árvore do projeto** — 13 arquivos e 4 aposentados, incluindo um GEDCOM de 5,3 MB. Está fora do versionamento (`.gitignore`) e fora do contexto de build (`.dockerignore`), mas **está no disco do desenvolvedor**, e a suíte precisa de isolamento para não escrever nele. Há teste para o isolamento (`test_ambiente_temporario_da_suite.py`). | 🟢 |

---

*Gerado pelo Reversa-Writer em 2026-10-10 (re-extração). Substitui a versão de 2026-10-05.*

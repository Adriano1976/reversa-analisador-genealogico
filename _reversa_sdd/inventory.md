# Inventário do Sistema Legado — analisador-genealogico

> Nível de documentação: **Completo** (`state.json` → `doc_level`, decidido em 2026-10-05; coincide com `.reversa/config.toml [analysis]`, que também diz `completo`).
> Re-extração de 2026-10-05. Substitui o inventário de 2026-09-30, que descrevia a raiz `analisador-genealogico/` e o pacote `reconstructed/`.
> Snapshot da versão substituída: `.reversa/snapshots/2026-10-05-pre-reextracao/`
> Escala de confiança: 🟢 CONFIRMADO | 🟡 INFERIDO | 🔴 LACUNA
> ⚠️ **Contagens atualizadas pela revisão de 2026-10-05.** As correções de código decididas nas respostas às perguntas (`matching.py`, `app.py`, `genetic_evidence.py`) somaram **+16 linhas a `src/`** e **+103 a `tests/`**. Os números deste inventário são **pós-revisão**: `src/**.py` = 3.489 · `tests/**.py` = 3.060 · `app.py` = 267 · 129 funções de teste · 179 itens coletados.
> 🔧 **Correção de 2026-10-08.** O vault Obsidian deixou de existir no repositório: a pasta
> `.obsidian/` e os arquivos de navegação em `docs/` (`00 - Dashboard.md`, `Mapa Geral.md` e os
> cinco `Mapa *.canvas`) foram removidos nesta data. As referências ao vault nestes artefatos
> foram ajustadas junto; `docs/` segue existindo como cópia do mini-site de `_reversa_docs/`.
> 📌 **`docs/` não é resíduo: é a pasta publicada no GitHub Pages** (source `master`, folder `/docs`),
> e é preservada por isso. O workflow `.github/workflows/deploy-pages.yml` mira `_reversa_docs/`,
> mas escuta a branch `main` — inexistente — logo não dispara por push.

---

## 1. Visão Geral

* **Nome do Projeto:** analisador-genealogico (Genetic Genealogy Path Analyzer) 🟢
* **Descrição:** Aplicação web Flask para genealogistas genéticos que identifica, calcula e visualiza conexões genealógicas entre uma pessoa raiz e correspondentes de DNA, cruzando árvores GEDCOM (`.ged`) com listas de segmentos de DNA (`.csv`) — e que, desde a regra final da análise (2026-10), **separa três coisas que nunca se contaminam**: parentesco documental (o que o GEDCOM afirma), evidência genética (o que o arquivo de DNA informa) e o confronto entre as duas, que devolve um de quatro estados. 🟢
* **Linguagem Principal:** Python 3 — **3.14.6** verificado por execução, tanto no interpretador global quanto em `.venv/`. 🟢
* **Framework Principal:** Flask 3.1.3, servido em produção por **waitress 3.0.2** a partir do bloco de entrada. 🟢
* **Arquitetura:** Aplicação web Flask com renderização server-side (Jinja2), em **camada de rota fina + pacotes internos por responsabilidade** (`parsers/`, `core/`, `reporting/`, `utils/`), com estado em memória do processo e sem banco de dados. 🟢

> **Mudança estrutural em relação à extração anterior (2026-09-30).** Quatro mudanças de forma, todas confirmadas por varredura:
>
> 1. A raiz de código deixou de ser `analisador-genealogico/` e passou a ser **`src/`** (feature `003-renomear-pasta-app-para-src`).
> 2. O pacote `reconstructed/` **deixou de existir**, substituído por quatro pacotes de primeiro nível: `core/`, `parsers/`, `reporting/` e `utils/` (série de refatoração `OPP-20261003-*`).
> 3. O `app.py` passou de 84 para **267 linhas**: ganhou teto de corpo de requisição, tratamento de `413`, filtros de template, upload ancorado no arquivo e a guarda de instância única no bloco de entrada.
> 4. Nasceu a **regra final da análise** (confronto GEDCOM × DNA com quatro estados), com oito módulos novos em `core/` e um arquivo de teste de 922 linhas. Nada disso existe em qualquer spec da extração anterior.
>
> **Nota de contagem:** as linhas deste inventário foram obtidas por `[System.IO.File]::ReadAllLines`, que **conta linhas em branco** — ao contrário de `Get-Content | Measure-Object -Line`, que as ignora e foi a causa de contagens truncadas em artefatos anteriores.

---

## 2. Estrutura de Árvore de Diretórios

Excluídos: `.git/`, `.agents/` e `.reversa/` (framework Reversa, não é sistema legado), `_reversa_*/` (artefatos do framework), `__pycache__/`, `.pytest_cache/`, `.pytest-tmp/`, `.venv/`, `node_modules/`, `uploads/` e `src/uploads/` (dados do usuário em runtime).

```text
/
├── src/                             # Raiz de código da aplicação
│   ├── app.py                       # Camada de rota Flask + bloco de entrada waitress (267 linhas)
│   ├── parsers/                     # Leitura do mundo de fora
│   │   ├── __init__.py
│   │   ├── gedcom_parser.py         # GEDCOM -> registros + grafo networkx (69)
│   │   └── csv_ingest.py            # CSV de matches: encoding, separador, preâmbulo, linha torta (227)
│   ├── core/                        # Decisão sobre o que foi lido, sem saber de HTTP
│   │   ├── __init__.py
│   │   ├── documentary_relationship.py  # Parentesco DOCUMENTAL: caminho, MRCA, homônimos, colapso de pedigree (576)
│   │   ├── genetic_evidence.py      # Evidência GENÉTICA: kits, cM, segmentos, SNPs, cromossomo (264)
│   │   ├── relationship_hypotheses.py   # cM -> possibilidades (Shared cM Project 4.0) (229)
│   │   ├── evidence_comparison.py   # Confronto: COMPATÍVEL / POSSÍVEL / CONFLITANTE / INCONCLUSIVO (247)
│   │   ├── cm_estimator.py          # LEGADO: faixas de cM escritas à mão, fora do fluxo (65)
│   │   ├── dna_analysis.py          # Orquestra as três etapas do cruzamento (250)
│   │   ├── matching.py              # Índices do GEDCOM e decisão de aceitação de candidatos (162)
│   │   ├── name_normalization.py    # Normalização e decomposição de nomes (122)
│   │   ├── path_search.py           # Fachada da busca de caminhos (219)
│   │   ├── path_finding.py          # Caminho direto (MRCA) e indireto (afinidade) (85)
│   │   ├── family_navigation.py     # Resolução de pessoa por nome e navegação (106)
│   │   └── gedcom_state.py          # Estado do processo: people, families, graph, versão (52)
│   ├── reporting/
│   │   ├── __init__.py
│   │   └── mermaid_render.py        # Diagrama Mermaid e contrato de escape do rótulo (289)
│   ├── utils/
│   │   ├── __init__.py
│   │   ├── text_cleaning.py         # Autoridade única de limpeza de mojibake (86)
│   │   ├── validate.py              # Validação do upload: nome, chave de conteúdo, GEDCOM (105)
│   │   └── number_format.py         # Formato dos números na tela (cm_br, inteiro_br) (54)
│   ├── templates/
│   │   └── index.html               # Única tela da aplicação (525 linhas)
│   └── uploads/                     # Runtime: arquivos enviados (não versionado)
├── tests/                           # 11 arquivos de teste + 2 geradores de fixture
│   ├── fixtures/
│   │   ├── sample_gedcom.py
│   │   └── sample_dna.py
│   ├── test_domain.py
│   ├── test_upload.py
│   ├── test_upload_seguranca.py
│   ├── test_path_search.py
│   ├── test_dna_analysis.py
│   ├── test_formatacao_cm.py
│   ├── test_characterization_matching.py
│   ├── test_characterization_mermaid.py
│   ├── test_mermaid_escape.py
│   ├── test_confrontacao_gedcom_dna.py
│   └── test_servidor_producao.py
├── plugins/
│   └── dsh-markdownlint/            # Plugin Node do harness DSH (sub-projeto à parte, ver §7)
├── docs/                            # Mini-site PUBLICADO no GitHub Pages (master /docs)
├── .github/
│   ├── workflows/deploy-pages.yml   # Dormante: escuta 'main', inexistente. Quem publica e docs/
│   └── skills/                      # 5 skills auxiliares (naming, jsdoc, docstring, readme, security)
├── .vscode/settings.json            # python.analysis.extraPaths = ./src + regras do markdownlint
├── .markdownlint-cli2.jsonc         # Regras de lint do Markdown deste repositório
├── pytest.ini                       # testpaths = tests
├── pyrefly.toml                     # search-path = ["src"]
├── requirements.txt                 # 6 dependências diretas, TODAS com versão fixada
├── README.md                        # Documentação do projeto (atualizada em 2026-10-05)
├── LICENSE                          # MIT
├── AGENTS.md / GEMINI.md            # Instruções do framework Reversa
├── .gitignore / .gitattributes
└── uploads/                         # Runtime legado da raiz (4 arquivos); a aplicação usa src/uploads/
```

**Ausências confirmadas:** `static/` não existe, DAL/DDL/migrations não existem, `Dockerfile`/`docker-compose.yml` não existem. O README herdado do módulo (`analisador-genealogico/README.md`) e o `.gitignore.txt` do módulo foram **removidos** na feature 003. 🟢

---

## 3. Mapeamento por Módulo / Componente

> A atribuição de cada arquivo a uma unidade funcional é do Scout e **está sujeita à revisão do Arqueólogo** — os módulos de `core/` são deliberadamente de responsabilidade única, e alguns servem a mais de um fluxo.

| Arquivo | Linhas | Responsabilidade | Tecnologias |
| --- | --- | --- | --- |
| `src/app.py` | 267 | Camada de rota. Rota única `index()` `GET`/`POST`, despacho por `request.form["action"]`; teto de corpo (`MAX_CONTENT_LENGTH`), handler de `413`, filtros `cm_br`/`inteiro_br`, upload ancorado no arquivo do app e bloco de entrada com waitress + guarda de instância única. | Flask, waitress, socket |
| `parsers/gedcom_parser.py` | 69 | Traduz o GEDCOM em registros e no grafo; incrementa a versão de estado. | ged4py, networkx |
| `parsers/csv_ingest.py` | 227 | Lê o CSV de matches tolerando separador, preâmbulo e linha torta; fallback de encoding; agrega cM por match. | pandas |
| `core/gedcom_state.py` | 52 | Registro do estado do processo (singleton não persistente): `people`, `families`, `graph`, `child_to_family` e o contador `versao`, que é o sinal de invalidação de índices derivados. | stdlib |
| `core/documentary_relationship.py` | 576 | **Parentesco documental**: caminho, ancestral comum, distância geracional, homônimos, caminhos múltiplos, colapso de pedigree e a evidência de cada salto. | networkx |
| `core/genetic_evidence.py` | 264 | **Evidência genética**: kit, fonte, cM total, segmentos, maior segmento, SNPs, cromossomo e posições; nunca soma kits diferentes. | pandas |
| `core/relationship_hypotheses.py` | 229 | Traduz cM em **possibilidades** de parentesco pela tabela publicada do Shared cM Project 4.0. | stdlib |
| `core/evidence_comparison.py` | 247 | **Confronto** entre documento e genética, devolvendo um dos quatro estados. | stdlib |
| `core/cm_estimator.py` | 65 | **Legado fora do fluxo**: as nove faixas de cM escritas à mão, mantidas como superfície de compatibilidade. O próprio módulo declara "não usar em código novo". | stdlib |
| `core/dna_analysis.py` | 250 | Orquestra as três etapas do cruzamento e monta o payload consumido pelo template. | pandas |
| `core/matching.py` | 162 | Índices do GEDCOM e decisão de aceitação de candidatos (matching difuso e filtros anti-falso-positivo). | thefuzz, RapidFuzz |
| `core/name_normalization.py` | 122 | Normalização e decomposição de nomes, e o vocabulário que isso usa. | stdlib |
| `core/path_search.py` | 219 | Fachada da busca de caminhos, consumida por `app.py`. | networkx |
| `core/path_finding.py` | 85 | Caminho direto por ancestral comum (BFS bidirecional) e indireto por afinidade. | networkx |
| `core/family_navigation.py` | 106 | Resolução de pessoa por nome e navegação de parentesco (pais, cônjuges). | networkx |
| `reporting/mermaid_render.py` | 289 | Emissão do diagrama Mermaid e o contrato de escape do rótulo (lista branca). | stdlib |
| `utils/text_cleaning.py` | 86 | Autoridade única da limpeza de mojibake (`strip_bad_utf`, `demojibake`). | stdlib |
| `utils/validate.py` | 105 | Validação do upload: nome visível, chave derivada do conteúdo e reconhecimento de GEDCOM. Módulo puro, sem Flask e sem disco. | stdlib |
| `utils/number_format.py` | 54 | Autoridade única da exibição numérica (`formatar_cm`, `formatar_inteiro`). | stdlib |
| `templates/index.html` | 525 | Única tela: upload, abas de busca e de análise, **as quatro seções do resultado** e o confronto, alertas e spinner. Bootstrap 5.3.3 e Mermaid 10 por CDN; `securityLevel: 'strict'`. | HTML5, Jinja2, Bootstrap 5, Mermaid |
| `tests/` (11 arquivos) | 3060 | Suíte de testes, incluindo dois arquivos de caracterização, o contrato de escape Mermaid, a regra final do confronto e a segurança do upload. | pytest 9.1.1 |
| `src/uploads/` | — | Arquivos enviados em runtime, gravados sob chave derivada do conteúdo. Não versionado. | Sistema de arquivos |

> Contagem por `[System.IO.File]::ReadAllLines`. Totais: `src/**.py` = **3489** linhas; template = **525**; `tests/**.py` = **3060**.

---

## 4. Pontos de Entrada (Entry Points) e Configurações

* **Aplicação Principal:** `src/app.py`. Importa o app Flask; sob `__main__` sobe por **waitress**, não pelo servidor de desenvolvimento. 🟢
* **Interface Web:** `src/templates/index.html` (única tela). 🟢
* **Rotas Flask — superfície completa:** 🟢

| Método | Rota | `action` | Linha | Comportamento |
| --- | --- | --- | --- | --- |
| GET | `/` | — | 107 | Renderiza o formulário inicial de upload. |
| POST | `/` | `upload_gedcom` | 111 | Valida o conteúdo como GEDCOM, grava sob chave derivada do conteúdo e carrega a árvore. |
| POST | `/` | `dna_analysis` | 134 | Processa `matches_csv` + `root_name` contra a árvore carregada. |
| POST | `/` | `path_search` | 156 | Busca caminho entre `person1_name` e `person2_name`. |

> A superfície HTTP é a **mesma** da extração anterior: nenhuma rota ou valor de `action` foi criado, renomeado ou removido. O que cresceu foi o conteúdo do resultado de `dna_analysis`, que agora traz as quatro seções e o confronto. 🟢

* **Variáveis de ambiente (todas com padrão declarado no código):** 🟢

| Variável | Padrão | Efeito |
| --- | --- | --- |
| `ANALISADOR_HOST` | `127.0.0.1` | Endereço de escuta. Abrir para a rede é ato explícito. |
| `ANALISADOR_PORT` | `5000` | Porta de escuta. |
| `ANALISADOR_THREADS` | `4` | Threads do servidor. |
| `ANALISADOR_UPLOAD_FOLDER` | — (cai no padrão) | Redireciona a pasta de upload; usado pelos testes para não escrever na pasta real. |

* **Configurações internas:** ~~`app.secret_key` embutido no código (`'f@milyse@rch_dna_edition_v16'`)~~ **removido em 2026-10-05** (correção do Revisor — não tinha consumidor: `flask.session` nunca foi importado); `MAX_CONTENT_LENGTH = 16 MB` com handler de `413` em português; `UPLOAD_FOLDER = "uploads"` resolvido por `_pasta_uploads()`, **ancorado no arquivo do app** (o caminho de escrita e o de leitura são o mesmo, sempre); guarda de instância única por socket ligado antes de servir, com `SO_EXCLUSIVEADDRUSE` no Windows. 🟢
* **Configurações de ferramentas:** `pytest.ini` (`testpaths = tests`), `pyrefly.toml` (`search-path = ["src"]`), `.vscode/settings.json` (`python.analysis.extraPaths = ["./src"]`), `.markdownlint-cli2.jsonc` (regras de lint do repositório). 🟢
* **CI/CD:** **passou a existir.** `.github/workflows/deploy-pages.yml` publica a pasta `_reversa_docs/` no GitHub Pages a cada push em `main`. Não há pipeline de teste, de build nem de análise estática. 🟢
* **Docker:** ausente. 🟢
* **Skills auxiliares:** `.github/skills/` contém cinco definições (`git-naming-conventions`, `jsdoc-documenter`, `python-docstring-generator`, `readme-blueprint-generator`, `security-code-audit`). São apoio de desenvolvimento, não fazem parte do runtime. 🟢

---

## 5. Banco de Dados e Armazenamento

* **Banco de dados:** **ausente**. Nenhum DDL, migration, schema ou ORM model no projeto. 🟢
* **Estado em memória:** `core/gedcom_state.py` é o registro único do processo — `people`, `families`, `graph` e `child_to_family`, mais o contador `versao`. `people`, `families` e `child_to_family` são mutados *in place* (`clear()` + `update()`) para que o binding importado no topo continue apontando para o objeto vivo; `graph` é **reatribuído**, e por isso quem o consome o importa dentro da função. O contador `versao` existe porque `id()` não muda com mutação *in place*, e índices derivados precisam de um sinal de invalidação. 🟢
* **Arquivos enviados:** gravados em `src/uploads/` (ou no caminho de `ANALISADOR_UPLOAD_FOLDER`) sob **chave derivada do conteúdo** do arquivo, com a extensão original preservada. O caminho completo é o que circula entre as funções — nunca o nome solto. 🟢
* **Persistência de resultado:** **nenhuma**. Nada é gravado entre requisições; a árvore é reconstruída a partir do arquivo a cada `POST`. 🟢
* **Dados do usuário:** 15 arquivos em `src/uploads/` e 4 em `uploads/` (local legado da raiz, anterior à ancoragem). Nenhum é versionado — `.gitignore` cobre `uploads/` em qualquer profundidade. 🟢

---

## 6. Cobertura de Testes

| Métrica | Valor |
| --- | --- |
| Framework | **pytest 9.1.1** (`pytest.ini`) 🟢 |
| Arquivos de teste | **11** 🟢 |
| Funções `def test_` | **129** 🟢 |
| Itens coletados por `pytest --collect-only` | **179** 🟢 (a diferença vem de testes parametrizados) |
| Linhas de teste | **3060** 🟢 |
| Geradores de fixture | 2 (`tests/fixtures/sample_gedcom.py`, `sample_dna.py`) 🟢 |
| Cobertura estimada | Não medida — sem `pytest-cov` nem configuração de cobertura. 🟡 |

**Tipos de teste presentes:** unitários por módulo (`domain`, `upload`, `path_search`, `dna_analysis`, `formatacao_cm`), **caracterização** de matching e de Mermaid (congelam a saída observável), contrato de **escape de rótulo Mermaid**, **regra final do confronto** (`test_confrontacao_gedcom_dna.py`, 922 linhas, 27 funções) e **segurança do upload** (`test_upload_seguranca.py`, 425 linhas, 33 funções: teto de requisição, chave derivada do conteúdo, recusa de GEDCOM inválido), além do bloco de entrada (`test_servidor_producao.py`: servidor de produção, instância única, padrão do endereço).

> Comparativo com a extração anterior: 7 arquivos / 52 funções / 86 itens / 1134 linhas → **11 arquivos / 129 funções / 179 itens / 3060 linhas**.

---

## 7. Escopo Excluído deste Inventário

Os itens abaixo vivem no repositório e foram deliberadamente **deixados fora** do escopo do sistema em runtime, para não serem confundidos com a arquitetura da aplicação:

| Caminho | Natureza |
| --- | --- |
| `plugins/dsh-markdownlint/` | Sub-projeto **Node/JavaScript** independente: plugin host do harness DSH que expõe a ferramenta `markdown_lint` sobre o `markdownlint-cli2`. Tem `package.json`, `node_modules/` e smoke próprio. Não é importado pela aplicação Python. 🟢 |
| `docs/` | **Pasta publicada no GitHub Pages**: source `master`, folder `/docs` → <https://adriano1976.github.io/reversa-analisador-genealogico/>. É cópia do mini-site de `_reversa_docs/`, sincronizada à mão por `xcopy`; sem `.nojekyll`, o Jekyll não publica nada que comece com ponto. Não é sistema. 🟢 |
| `.github/skills/` | Cinco skills auxiliares de desenvolvimento. 🟢 |
| `_reversa_sdd/`, `_reversa_forward/`, `_reversa_bugs/`, `_reversa_refactor/`, `_reversa_docs/`, `.reversa/`, `.agents/` | Framework Reversa e seus artefatos. 🟢 |
| `.pytest-tmp/` | Resíduo de execução de testes (gitignored), não versionado. 🟡 |
| `uploads/` (raiz) | Local de upload anterior à ancoragem no arquivo do app. Mantido apenas como dado. 🟢 |

---

## 8. Sugestão de Organização das Specs (Scout)

* **`granularity`:** `endpoint` 🟢
* **Razão:** a superfície continua sendo um **roteamento centralizado** de rota única com despacho por campo `action`, e os **três** valores distintos de `action` delimitam exatamente três unidades funcionais. A refatoração mudou onde o código mora, não a superfície.
* **Sinais observados:**

| Sinal | Evidência |
| --- | --- |
| Roteamento centralizado | `src/app.py:112` (`@app.route("/", methods=["GET", "POST"])`), despacho por `request.form.get("action")` em `src/app.py:115`, com os três ramos em `:116`, `:139` e `:161` |

> **Decisão já persistida.** `.reversa/config.toml` → `[specs]` contém a decisão de 2026-08-03: `layout = "feature-folder"`, `granularity = "endpoint"`, `scout_suggestion = "endpoint"`. Esta sugestão **confirma** a decisão existente; conforme a regra de imutabilidade do `surface-schema.md`, o campo `scout_suggestion` **não** é reescrito pelo orquestrador, e o passo de organização das specs é pulado nesta rodada. `.reversa/config.user.toml` não tem override de `[specs]` (verificado).

---

*Gerado pelo Reversa-Scout em 2026-10-05 (re-extração).*

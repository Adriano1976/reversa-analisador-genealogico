# Inventário do Sistema Legado — analisador-genealogico

> **Rodada:** re-extração de 2026-10-10 (quarta extração; anteriores em 2026-08-03, 2026-09-30 e 2026-10-05). Substitui o inventário de 2026-10-05, que descrevia o sistema **sem** `ports/`, **sem** persistência, **sem** Docker e **sem** a lista de arquivos da tela.
> **Autor:** Scout · **Nível de documentação:** completo · **Idioma:** Português
> **Snapshot da versão substituída:** `.reversa/snapshots/2026-10-10-pre-reextracao/` (83 arquivos, 967 KB, sha256 por arquivo no `_MANIFEST.txt`)
> **Código medido em:** HEAD `980502c` (2026-10-10), árvore de trabalho limpa, 246 commits. Não houve alteração do legado nesta fase.
> **Escala de confiança:** 🟢 CONFIRMADO | 🟡 INFERIDO | 🔴 LACUNA
> **Método de contagem:** "linhas úteis" = linhas não vazias (`Get-Content | Measure-Object -Line`); "linhas cruas" = total do arquivo, incluindo vazias. Os dois números são declarados porque a diferença entre eles já causou contagem truncada em artefatos anteriores.

---

## 1. Visão Geral

* **Nome do Projeto:** analisador-genealogico (Genetic Genealogy Path Analyzer) 🟢
* **Descrição:** aplicação web Flask para genealogia genética. Cruza uma árvore GEDCOM (`.ged`) com uma lista de matches de DNA (`.csv`) e apresenta **três coisas separadas, que nunca se contaminam**: o parentesco documental que o GEDCOM afirma, a evidência genética que o CSV informa, e o **confronto** entre as duas, que devolve um de quatro estados (`COMPATIVEL`, `POSSIVEL`, `CONFLITANTE`, `INCONCLUSIVO`). 🟢
* **Linguagem principal:** Python **3.14.6** verificado por execução no `.venv/` — que, desde a decisão de 2026-10-05 (`questions.md#pergunta-11`), é o interpretador **oficial** do projeto. 🟢
* **Framework principal:** Flask 3.1.3, servido por **waitress 3.0.2**. 🟢
* **Arquitetura:** hexagonal, em quatro anéis — `src/app.py` (borda web) → `src/application/` (casos de uso) → `src/ports/` (portas e adaptadores) → `src/core/` (domínio puro, sem HTTP e sem banco), com `parsers/`, `reporting/` e `utils/` de apoio. **O estado global do processo deixou de existir** (`core/gedcom_state.py` foi apagado no `T023` da feature 007): a árvore passou a ser parâmetro. 🟢
* **Tamanho:** 5.130 linhas Python úteis em `src/` (35 arquivos) e 8.959 em `tests/` (48 arquivos); 182 `def`/`class` em `src/`. 🟢
* **Suíte:** **536 itens coletados — 527 passam, 9 pulados, 0 falham** (§6). 🟢

> **Divergência de ambiente medida nesta fase:** com `DATABASE_URL` presente no ambiente do processo (como estava no shell desta sessão, herdado do `.env`) e sem o driver `psycopg2` no `.venv`, **dois** testes de `test_persistencia_desabilitada.py` falham. Removendo a variável, os três passam e a suíte fecha em 527/9/0. Ver §9.1. 🟢

### 1.1 O que mudou desde a extração de 2026-10-05

O `_reversa_sdd/` atual descreve o sistema de 2026-10-05. Entre aquela data e 2026-10-10 entraram nove features em `_reversa_forward/` (005 a 012) e os adendos correspondentes. O que nasceu **sem spec principal**:

| Mudança | Evidência no código | Registro existente |
| --- | --- | --- |
| Núcleo puro, sem estado global | `src/core/gedcom_state.py` **deletado**; a árvore virou parâmetro | adendos 005 e 007 |
| Fronteira de aplicação | `src/application/` (5 casos de uso) + `src/ports/adaptadores.py` | adendo 006 |
| Persistência histórica | `init.sql` (6 tabelas), `RegistroDeAnalisesPostgres`, `psycopg2-binary` no pin | adendo 008 |
| Conteinerização | `docker/Dockerfile`, `docker-compose.yml`, `.dockerignore`, `.env` | adendo 008 |
| Armazenamento por conteúdo + aposentadoria | chave `sha256` truncada, `aposentar()`, `_aposentados/` | adendos 010 e 011 |
| Substituição no reenvio | `application/reenvio.py`, desfecho `substituido` | adendo 011 |
| Lista de arquivos na tela | `reporting/lista_de_arquivos.py`, duas abas, "Abrir" e "Aposentar" | adendos 011 e 012 |
| Erros de domínio tipados | `src/core/erros.py` + `application/traducao.py` | adendo 006 |
| Registro da análise | `src/core/registro.py` + projeção do resultado | adendo 008 |
| Arte do topo e ícone de atalho | `GET /banner.png` e `GET /apple-touch-icon.png` | adendos 009 e 011 |
| Domínio de diagrama isolado | `src/core/diagram_domain.py` | adendo 006 |
| CI/CD removido | `.github/workflows/` **não existe mais** (removido em 2026-10-08) | — |

---

## 2. Estrutura de Árvore de Diretórios

Excluídos desta árvore: `.git/`, `.agents/` e `.reversa/` (framework Reversa), `_reversa_*/` (artefatos do framework), `.venv/`, `node_modules/`, `__pycache__/`, `.pytest_cache/`, `.parity-run-*/`, `.parity-tmp/` e o **conteúdo** de `src/uploads/` (dado real do operador).

```text
/
├── src/                             # Raiz de código da aplicação
│   ├── app.py                       # Borda web: 4 rotas, 5 ações de POST, filtros, montagem das portas, waitress (559 úteis / 625 cruas)
│   ├── application/                 # Casos de uso (fronteira) — 627 linhas
│   │   ├── __init__.py              # `Desfecho`, `nomes_de_exibicao`
│   │   ├── upload_gedcom.py         # caso de uso do envio
│   │   ├── dna_analysis.py          # caso de uso da análise de DNA
│   │   ├── path_search.py           # caso de uso da busca de caminho
│   │   ├── reenvio.py               # armazenar com substituição (GEDCOM e CSV)
│   │   └── traducao.py              # ErroDeDominio -> mensagem de contrato
│   ├── core/                        # Domínio puro, sem HTTP e sem banco — 2.257 linhas
│   │   ├── documentary_relationship.py · path_search.py · path_finding.py · family_navigation.py
│   │   ├── genetic_evidence.py · relationship_hypotheses.py · evidence_comparison.py
│   │   ├── dna_analysis.py · matching.py · name_normalization.py · cm_estimator.py (legado fora do fluxo)
│   │   ├── diagram_domain.py · registro.py · erros.py
│   ├── parsers/                     # Leitura do mundo de fora — 256 linhas
│   │   ├── gedcom_parser.py · csv_ingest.py
│   ├── ports/                       # Portas e adaptadores concretos — 669 linhas
│   │   ├── adaptadores.py           # ArmazenamentoEmDisco, CarregadorDeArvoresGedcom, RegistroDeAnalisesPostgres
│   ├── reporting/                   # 421 linhas
│   │   ├── mermaid_render.py · lista_de_arquivos.py
│   ├── utils/                       # 341 linhas
│   │   ├── text_cleaning.py · validate.py · number_format.py · name_keys.py
│   ├── templates/index.html         # Tela única (731 úteis)
│   ├── assets/                      # apple-touch-icon.png, banner-da-tela.png (artes DERIVADAS)
│   └── uploads/                     # Pasta canônica de dados: 13 arquivos + _aposentados/ com 3
├── tests/                           # 39 test_*.py + 9 de apoio — 8.959 linhas úteis
├── docker/Dockerfile                # python:3.14-slim
├── docker-compose.yml               # serviços db (postgres:16-alpine) e app
├── init.sql                         # esquema idempotente das 6 tabelas do histórico (189 linhas)
├── requirements.txt                 # 9 dependências diretas, todas com `==`
├── pytest.ini · pyrefly.toml · .markdownlint-cli2.jsonc · .dockerignore · .gitignore · .gitattributes
├── .env                             # credenciais do banco local — NÃO versionado
├── publicar_docs.py                 # publica `_reversa_docs/` em `docs/`
├── README.md                        # documentação viva do repositório (36 KB, em dia)
├── AGENTS.md · GEMINI.md · LICENSE
├── plugins/dsh-markdownlint/        # sub-projeto Node (lint de Markdown), fora do runtime
└── docs/                            # cópia publicada do mini-site (10 páginas HTML)
```

**Ausências confirmadas:** `static/` (proibida pelo `W004`), `migrations/`, ORM, `Dockerfile` na raiz (ele mora em `docker/`), pipeline de teste/build e qualquer workflow de CI. 🟢

---

## 3. Mapeamento por Módulo / Componente

### 3.1 Pacotes de código

| Pacote | Arquivos | Linhas úteis | Responsabilidade | Tecnologias |
| --- | ---: | ---: | --- | --- |
| `src/app.py` | 1 | 559 | Borda web: rota `/` (GET/POST) com despacho por `action`, rotas de arte, processador de contexto das listas, teto de 16 MB, handler de `413`, 4 filtros de template, montagem única das portas e bloco `__main__` com waitress + guarda de instância única | Flask, waitress, socket |
| `src/application/` | 6 | 627 | Casos de uso: orquestram núcleo + portas sem conhecer HTTP | stdlib |
| `src/core/` | 15 | 2.257 | Domínio puro: parentesco documental, evidência genética, hipóteses, confronto, matching, busca de caminho, registro e erros | networkx, thefuzz/RapidFuzz, pandas |
| `src/parsers/` | 3 | 256 | Leitura de GEDCOM (ged4py) e de CSV (pandas, com fallback de encoding) | ged4py, pandas |
| `src/ports/` | 2 | 669 | Portas (protocolos) e adaptadores concretos: disco, carregador de árvores, registro Postgres | psycopg2 (preguiçoso) |
| `src/reporting/` | 3 | 421 | Renderização Mermaid e funções puras da lista de arquivos | stdlib |
| `src/utils/` | 5 | 341 | Limpeza de texto, validação, formatação numérica, chaves de nome | stdlib |
| `src/templates/index.html` | 1 | 731 | Tela única: formulário, duas abas de lista, seleção, aposentadoria e as seções de resultado | Jinja2, Bootstrap 5.3.3, Mermaid 10 (CDN) |
| `tests/` | 48 | 8.959 | 536 itens de teste | pytest 9.1.1, pytest-cov |

### 3.2 Unidades funcionais do sistema (o contrato que o operador enxerga)

> A atribuição de cada arquivo a uma unidade é do Scout e **está sujeita à revisão do Arqueólogo**: vários módulos de `core/` servem a mais de um fluxo.

| Módulo | Contrato | Arquivos-chave |
| --- | --- | --- |
| `upload-gedcom` | `POST /` com `action=upload_gedcom`: envio, validação de **conteúdo**, chave derivada do conteúdo, reenvio com substituição | `application/upload_gedcom.py`, `application/reenvio.py`, `parsers/gedcom_parser.py`, `utils/validate.py`, `utils/text_cleaning.py` |
| `tela-de-entrada` | `GET /` (as duas abas, **sempre**) + `action=selecionar_arvore` + `action=aposentar_arquivo` | `app.py` (`index`, `_listas_da_tela`), `reporting/lista_de_arquivos.py`, `templates/index.html` |
| `analise-dna` | `POST /` com `action=dna_analysis`, com o CSV vindo do formulário **ou** da lista | `application/dna_analysis.py`, `core/{dna_analysis,matching,genetic_evidence,relationship_hypotheses,evidence_comparison,name_normalization,registro}`, `parsers/csv_ingest.py` |
| `busca-caminho` | `POST /` com `action=path_search` | `application/path_search.py`, `core/{path_search,path_finding,family_navigation,documentary_relationship}`, `reporting/mermaid_render.py` |
| `recursos-da-tela` | `GET /banner.png` e `GET /apple-touch-icon.png` | `app.py` (rotas de arte), `src/assets/*.png`, `tests/{banner_da_tela,icone_de_atalho}.py` |

**Capacidade transversal sem endpoint próprio:** a **persistência histórica** (`ports/adaptadores.py` + `init.sql` + `core/registro.py`). Ela tem um único consumidor — o caso de uso de DNA — e por isso é documentada dentro de `analise-dna`, com o esquema físico em `erd-complete.md`. 🟢

---

## 4. Pontos de Entrada (Entry Points) e Configurações

* **Aplicação principal:** `src/app.py`. Importá-lo devolve o objeto `app` (a suíte e o harness de paridade fazem isso); sob `__main__` ele sobe por **waitress**, com socket ligado antes de servir e guarda de exclusividade de instância. 🟢
* **Interface web:** `src/templates/index.html` (única tela). 🟢
* **Superfície HTTP completa:** 🟢

| Método | Rota | `action` | Comportamento |
| --- | --- | --- | --- |
| GET | `/` | — | Tela de entrada; as duas listas entram por processador de contexto, em **toda** renderização |
| POST | `/` | `upload_gedcom` | Valida o conteúdo como GEDCOM, grava sob chave de conteúdo e carrega a árvore |
| POST | `/` | `aposentar_arquivo` | Tira o arquivo da lista **movendo** para `_aposentados/`; nada é apagado |
| POST | `/` | `selecionar_arvore` | Escolhe a árvore clicando na lista (mesmo estado que o envio produz) |
| POST | `/` | `dna_analysis` | Roda a análise; o CSV vem do formulário ou da lista, com precedência para a lista |
| POST | `/` | `path_search` | Busca caminho entre `person1_name` e `person2_name` |
| GET | `/banner.png` | — | Arte do topo (feature 011); ausente devolve `404` e nada mais muda |
| GET | `/apple-touch-icon.png` | — | Ícone de atalho (feature 009); escrita recusada com `405` pelo roteador |

* **Variáveis de ambiente (todas com padrão declarado no código):** 🟢

| Variável | Padrão | Efeito |
| --- | --- | --- |
| `ANALISADOR_HOST` | `127.0.0.1` | Endereço de escuta; atender a rede é ato explícito |
| `ANALISADOR_PORT` | `5000` | Porta de escuta |
| `ANALISADOR_THREADS` | `4` | Threads do waitress |
| `ANALISADOR_UPLOAD_FOLDER` | derivado de `__file__` | Redireciona a pasta de uploads (usada pelos testes) |
| `DATABASE_URL` | ausente | Presente liga o registro histórico; ausente mantém o registrador **nulo** |

* **Configurações internas:** teto de corpo de requisição de 16 MB nomeado (`TETO_DE_UPLOAD_EM_BYTES`) com handler de `413` em português; `app.secret_key` **removido** em 2026-10-05 (não tinha consumidor); pasta de upload resolvida **e** criada pela mesma função ancorada no arquivo do app; quatro filtros de template (`cm_br`, `inteiro_br`, `data_br`, `rotulo_do_arquivo`); `DONO_DO_PROCESSO = "unico"`, declarado como marcador de costura e **não** como mecanismo de segurança. 🟢
* **CI/CD:** **ausente.** O workflow de GitHub Pages existiu entre 2026-10-05 e 2026-10-08 e foi removido; quem publica o mini-site hoje é `python publicar_docs.py`. Não há pipeline de teste, build ou análise estática. 🟢
* **Docker:** **presente.** `docker/Dockerfile` (`python:3.14-slim`, contexto de build na raiz, `COPY` estreito) e `docker-compose.yml` (dois serviços, portas só no loopback, volume nomeado para o banco e bind mount para os uploads). 🟢
* **Skills auxiliares:** `.github/skills/` tem seis definições de apoio ao desenvolvimento; não fazem parte do runtime. 🟢

---

## 5. Banco de Dados e Armazenamento

**Dois regimes, deliberadamente diferentes** (`D-08` da feature 008): 🟢

1. **Sistema de arquivos — os dados de entrada.** `src/uploads/` é a pasta canônica, ancorada em `__file__`. Hoje: **13 arquivos** (entre eles o GEDCOM real de 5,3 MB) e **3 em `_aposentados/`**. A chave de armazenamento é `^[0-9a-f]{16}__[A-Za-z0-9._-]+$` — 16 hexadecimais do `sha256` do conteúdo mais o nome visível. A **aposentadoria move**, nunca apaga; o reenvio de conteúdo novo **substitui** a versão anterior, que vai para a mesma pasta.
2. **PostgreSQL 16 — o histórico das análises.** `init.sql` (189 linhas) é **idempotente** (`CREATE TABLE IF NOT EXISTS`, nenhum `DROP`) e cria **6 tabelas**: `dna_analysis`, `analysis_person`, `match_result`, `match_path_node`, `match_kit`, `skipped_match`. O DDL é **parcialmente herdado** de `_reversa_sdd/migration/target_data_model.md` (congelado em 2026-09-28, **anterior** ao confronto), com quatro extensões marcadas no próprio arquivo. A árvore **não é duplicada** no banco (`RN-04`): continua sendo o arquivo imutável de `src/uploads/`, referenciado por `tree_ref`.

* **Sem ORM, sem runner de migração, sem tabela de versão de esquema.** Limite declarado no `init.sql`: mudança de esquema depois da primeira subida exige `docker compose down -v` (perdendo o histórico) ou `ALTER TABLE` manual. 🟢
* **Os três estados do registro** (`D-02`): sem `DATABASE_URL` → registrador **nulo** e tela inalterada; com a variável e o banco respondendo → grava; com a variável e a gravação falhando → **a análise conclui e é exibida**, com aviso não bloqueante (`RN-13`). O `import psycopg2` é **preguiçoso**, dentro do método de gravação. 🟢
* **Sem autenticação, sem sessão e sem papéis** — nenhuma tabela de usuário é criada, e `owner_id` existe sem FK e sem índice de escopo (`RN-10`). 🟢

---

## 6. Cobertura de Testes

| Métrica | Valor |
| --- | --- |
| Framework | **pytest 9.1.1** (+ pytest-cov 7.1.0 e coverage 7.16.2, no `.venv`) 🟢 |
| Arquivos | **39** `test_*.py` + **9** de apoio (`conftest.py`, `fixtures/` ×4, `banner_da_tela.py`, `icone_de_atalho.py`, `manutencao_de_uploads.py`, `rodar_paridade.py`) 🟢 |
| Funções `def test_` | **418** 🟢 |
| Itens coletados (`--collect-only`) | **536** 🟢 |
| Resultado medido nesta fase | **527 passam, 9 pulados, 0 falham** (66 s, `.venv`, sem `DATABASE_URL` no ambiente) 🟢 |
| Linhas de teste | **8.959** úteis / 11.256 cruas 🟢 |
| Cobertura de código | não remedida nesta fase (a revisão de 2026-10-05 mediu 83 % de `src/`) 🟡 |

**Maiores arquivos de teste:** `test_upload_seguranca.py` (36 funções), `test_lista_de_arquivos.py` (31), `test_confrontacao_gedcom_dna.py` (28), `test_aposentar_arquivo.py` (25), `test_manutencao_de_uploads.py` (19).

**Módulos sem teste de unidade dedicado:** `core/family_navigation.py`, `core/path_finding.py`, `parsers/csv_ingest.py` — exercitados de passagem. 🟡

**Instrumentação fora do pytest:** `_reversa_sdd/parity/harness.py` (harness diferencial contra o oráculo congelado) e `tests/rodar_paridade.py`; `tests/fixtures/arvore_atual.py` gera a árvore usada pelos testes.

---

## 7. Escopo Excluído deste Inventário

| Caminho | Natureza |
| --- | --- |
| `.agents/skills/` | Instalação do framework Reversa — sozinha, responde pela maior parte dos 167 `.md` do repositório 🟢 |
| `.github/skills/` | Seis skills auxiliares de agente (readme, docstring, naming, auditoria de segurança) 🟢 |
| `_reversa_sdd/` `_reversa_docs/` `_reversa_forward/` `_reversa_bugs/` `_reversa_refactor/` | Artefatos do framework Reversa 🟢 |
| `docs/` | Cópia **publicada** do mini-site, gerada por `publicar_docs.py`; o fonte é `_reversa_docs/` 🟢 |
| `plugins/dsh-markdownlint/` | Sub-projeto **Node/JavaScript** independente: plugin host que expõe `markdown_lint` sobre o `markdownlint-cli2`. Não é importado pela aplicação Python 🟢 |
| `.venv/`, `node_modules/`, `__pycache__/`, `.pytest_cache/`, `.parity-run-*/`, `.parity-tmp/`, `.coverage` | Ambientes e resíduos de execução 🟢 |
| `src/uploads/` (conteúdo) | Dado real do operador; o Princípio I do projeto proíbe versioná-lo ou expô-lo 🟢 |

---

## 8. Sugestão de Organização das Specs (Scout)

* **`granularity`:** `endpoint` 🟢
* **Razão:** a aplicação continua com **roteamento centralizado** — uma única rota `/` que despacha por `request.form.get("action")` —, e o contrato observável de cada fluxo é a **ação HTTP**, não o pacote de código por onde ela passa (a refatoração mudou onde o código mora, não a superfície). As três ações de análise somam-se hoje às ações da tela e às duas rotas de arte. 🟢
* **Sinais observados:**

| Sinal | Evidência |
| --- | --- |
| Roteamento centralizado | `src/app.py` — `@app.route("/", methods=["GET", "POST"])` com despacho por `request.form.get("action")` em 5 ramos, mais `@app.route("/banner.png")` e `@app.route("/apple-touch-icon.png")`, ambas só `GET` |

> **Decisão já persistida.** `.reversa/config.toml` → `[specs]` contém a decisão de 2026-08-03: `layout = "feature-folder"`, `granularity = "endpoint"`, `scout_suggestion = "endpoint"`. Esta sugestão **confirma** a decisão existente; pela regra de imutabilidade do `surface-schema.md`, `scout_suggestion` **não** é reescrito, e o passo 3 é pulado nesta rodada. `.reversa/config.user.toml` **não** tem seção `[specs]` (verificado). 🟢

---

## 9. Achados do Scout para as fases seguintes

1. **`psycopg2-binary==2.9.13` está declarado e NÃO está instalado no `.venv`.** 🔴 O pin diz que o driver é dependência da aplicação; o interpretador oficial não o tem. O código sobrevive a isso por desenho (import preguiçoso + aviso não bloqueante), então nada quebra — mas a situação é o **inverso** da rodada anterior, que realinhou o pin ao `.venv` para encerrar justamente uma divergência de ambiente. Candidato a lacuna para o Revisor.
2. **O resultado da suíte depende do ambiente.** 🟢 Medido: sem `DATABASE_URL` → 527 passam / 9 pulados / 0 falham; com `DATABASE_URL` presente (e sem `psycopg2`) → 525 / 9 / **2 falham** em `test_persistencia_desabilitada.py`. A premissa "a variável não existe no ambiente" não está declarada pelo teste.
3. **`.env` contém credencial em claro** (usuário, senha, banco e `DATABASE_URL`). 🟢 Está no `.gitignore` (linha 6) e **nenhum valor foi transcrito para os artefatos desta extração**. O `docker-compose.yml` usa `${VAR:?}` de propósito, para não versionar credencial com valor padrão.
4. **`src/core/gedcom_state.py` não existe mais**, mas sobrou `src/core/__pycache__/gedcom_state.cpython-314.pyc`. 🟡 Resíduo de bytecode, não código morto vivo — mas pode induzir a erro quem inventariar por `__pycache__`.
5. **O mini-site está defasado.** 🟢 `_reversa_docs/` (e a cópia `docs/`) foram regenerados em 2026-10-08, antes das features 009 a 012, e o gerador **não lê** `_reversa_sdd/addenda/`. É o primeiro passo pós-extração previsto no pedido.
6. **As matrizes de `_reversa_bugs/*/generated/` derivam das specs de 2026-10-05** e ancoram em `_reversa_sdd/upload-gedcom/contracts.md#2.1` e `_reversa_sdd/domain.md#3.5`, que esta rodada reescreve. 🟢 Por isso `/reversa-debugger-graph` deve ser o **último** passo depois da extração.
7. **O `README.md` é a superfície de documentação mais confiável do repositório** (36 KB, atualizado em 2026-10-10: descreve a lista de arquivos, a aposentadoria, o reenvio e a pasta canônica). 🟢 Nenhum artefato do Reversa pode contradizê-lo sem medir o código.
8. **Zero marcadores `TODO`/`FIXME`/`XXX`/`HACK` em `src/`.** 🟢 Não há intenção não implementada declarada no código; as declarações de legado vivem em docstring e comentário (`cm_estimator.py` é o caso explícito).
9. **A árvore de trabalho estava limpa** na abertura da rodada (`git status --porcelain` vazio) e o legado **não foi tocado** nesta fase. 🟢

---

*Gerado pelo Reversa-Scout em 2026-10-10 (re-extração).*

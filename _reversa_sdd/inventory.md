# Inventário do Sistema Legado — analisador-genealogico

> Nível de documentação: **Essencial** (`state.json` → `doc_level`)
> Re-extração de 2026-09-30. Substitui o inventário de 2026-08-03, que descrevia o monolito de 887 linhas.
> Escala de confiança: 🟢 CONFIRMADO | 🟡 INFERIDO | 🔴 LACUNA

---

## 1. Visão Geral

* **Nome do Projeto:** analisador-genealogico (Genetic Genealogy Path Analyzer)
* **Descrição:** Aplicação web Flask para genealogistas genéticos que identifica, calcula e visualiza conexões genealógicas entre uma pessoa raiz e correspondentes de DNA, cruzando árvores GEDCOM (.ged) com listas de segmentos de DNA (.csv). 🟢
* **Linguagem Principal:** Python 3 — **Python 3.14.6** instalado e verificado por execução. 🟢
* **Framework Principal:** Flask 3.1.3 🟢
* **Arquitetura:** Aplicação web Flask com renderização server-side (Jinja2), em **camada de rota fina + pacote de módulos internos**. 🟢

> **Mudança estrutural em relação à extração anterior.** O que era um monolito de 887 linhas (`app.py`) virou uma **camada de apresentação de 84 linhas** que delega a três fluxos. A lógica de negócio reside em `analisador-genealogico/reconstructed/` (1086 linhas). Nenhuma rota nova foi criada: a superfície HTTP é a mesma.
>
> **Nota de contagem:** os números desta seção são os de **2026-09-30, após** a remoção das entidades mortas de `domain.py` (115 → 84 linhas). Na extração anterior à remoção, `reconstructed/` tinha 1117 linhas e o total de Python era 1201.

---

## 2. Estrutura de Árvore de Diretórios

Excluídos: `.git/`, `.agents/` (framework Reversa instalado, não é sistema legado), `.reversa/`, `_reversa_*/`, `__pycache__/`, `.pytest_cache/`, `uploads/`, `.vscode/`.

```
/
├── analisador-genealogico/
│   ├── app.py                       # Camada de rota Flask (84 linhas) — delega aos módulos internos
│   ├── requirements.txt             # 6 dependências diretas, nenhuma com versão fixada
│   ├── README.md                    # Documentação original do projeto (EN)
│   ├── .gitignore.txt               # Regras de ignore (nome com sufixo .txt, provavelmente acidental)
│   ├── reconstructed/               # Núcleo de negócio extraído do monolito
│   │   ├── __init__.py
│   │   ├── domain.py                # Limpeza de nome GEDCOM (84 linhas; era 115 antes da remoção das entidades mortas)
│   │   ├── upload.py                # Parse GEDCOM, grafo, carga de estado global (100 linhas)
│   │   ├── path_search.py           # Busca de caminho direto/indireto + emissão Mermaid (506 linhas)
│   │   └── dna_analysis.py          # Matching difuso, agregação de cM, faixas de relação (395 linhas)
│   ├── templates/
│   │   └── index.html               # Única tela da aplicação (200 linhas)
│   └── uploads/                     # Arquivos .ged/.csv enviados (runtime, não versionados)
├── tests/                           # 7 arquivos de teste + 2 geradores de fixture
│   ├── fixtures/
│   │   ├── sample_gedcom.py
│   │   └── sample_dna.py
│   ├── test_domain.py
│   ├── test_upload.py
│   ├── test_path_search.py
│   ├── test_dna_analysis.py
│   ├── test_characterization_mermaid.py
│   ├── test_characterization_matching.py
│   └── test_mermaid_escape.py
├── pytest.ini                       # testpaths = tests
├── pyrefly.toml                     # search-path = ["analisador-genealogico"]
├── README.md                        # README raiz do repositório
├── LICENSE                          # MIT
├── AGENTS.md / GEMINI.md            # Instruções do framework Reversa
└── uploads/                         # Dados de trabalho na raiz (3 arquivos)
```

**Ausências notáveis em relação à extração anterior:** `static/` **não existe mais** (era resíduo do Pyvis, removido) e `app.py` **não declara mais** `STATIC_FOLDER`. 🟢

---

## 3. Mapeamento por Módulo / Componente

| Módulo / Arquivo | Linhas | Responsabilidade | Tecnologias |
| --- | --- | --- | --- |
| `app.py` | 84 | Camada de rota. Rota única `index()` com `GET`/`POST`; despacho por `request.form["action"]`; validação de arquivo e mensagens de erro; delega aos módulos internos. | Flask |
| `reconstructed/domain.py` | 84 | Limpeza/correção de mojibake de nomes GEDCOM (`strip_bad_utf`, `demojibake`). **Era 115 linhas** — as entidades `Family`, `GenealogyGraph` e `DNAGroup` foram removidas em 2026-09-30 por serem arquitetura abandonada. | stdlib |
| `reconstructed/upload.py` | 100 | Abre o GEDCOM com `ged4py`, popula o **estado global** (`people`, `families`, `graph`, `child_to_family`) e devolve a lista de nomes. | ged4py, networkx |
| `reconstructed/path_search.py` | 506 | Busca de caminho direto e indireto (ponte matrimonial), decomposição do caminho e emissão do grafo Mermaid com escape de rótulo. | networkx |
| `reconstructed/dna_analysis.py` | 395 | Agregação de segmentos cM por chave (nome + ID/email), matching difuso, regras de aceitação, faixas de relação por cM, auditoria de descartados. | pandas, thefuzz, RapidFuzz |
| `templates/index.html` | 200 | Única tela: upload de GEDCOM, abas de busca de caminho e análise de DNA, exibição de resultados, alertas e spinner. Bootstrap 5 e Mermaid 10 via CDN. | HTML5, Bootstrap 5, Mermaid |
| `tests/` (7 arquivos) | 1197 | Suíte de testes, incluindo dois arquivos de **caracterização** que congelam saída de matching e de Mermaid. | pytest |
| `uploads/` | — | Armazenamento dos arquivos enviados durante a sessão. Sem persistência de resultados. | Sistema de arquivos |

> Contagem de linhas obtida por `[System.IO.File]::ReadAllLines` — inclui a linha vazia final quando o arquivo termina em newline.

---

## 4. Pontos de Entrada (Entry Points) e Configurações

* **Aplicação Principal:** `analisador-genealogico/app.py` — `app = Flask(__name__)`, `if __name__ == "__main__": app.run(debug=True)`. 🟢* **Interface Web:** `analisador-genealogico/templates/index.html` (única tela). 🟢
* **Rotas Flask — superfície completa:**

| Método | Rota | `action` | Comportamento |
| --- | --- | --- | --- |
| GET | `/` | — | Renderiza o formulário inicial de upload. 🟢 |
| POST | `/` | `upload_gedcom` | Salva o `.ged` em `uploads/` e carrega a árvore. |
| POST | `/` | `path_search` | Busca caminho entre `person1_name` e `person2_name`. |
| POST | `/` | `dna_analysis` | Processa `matches_csv` + `root_name` contra a árvore carregada. |

> **Observação de nomenclatura:** o valor do campo `action` para análise de DNA é **`dna_analysis`**. A extração anterior registrava `process_dna` — nome que **não existe** no código atual. Corrigido aqui. 🟢

* **Configurações Internas:**
  * `app.secret_key` = `'f@milyse@rch_dna_edition_v16'` — segredo embutido no código. 🟢
  * `UPLOAD_FOLDER` = `"uploads"`, com `os.makedirs(UPLOAD_FOLDER, exist_ok=True)`. 🟢
  * `STATIC_FOLDER` — **removido**; não há mais criação da pasta `static/`. 🟢
* **Configurações de ferramentas:** `pytest.ini` (`testpaths = tests`) e `pyrefly.toml` (`search-path = ["analisador-genealogico"]`, necessário para o import `reconstructed.*`). 🟢
* **CI/CD:** ausente — sem `.github/workflows`, `Jenkinsfile` ou `.gitlab-ci.yml`. 🟢
* **Docker:** ausente — sem `Dockerfile` ou `docker-compose.yml`. 🟢

---

## 5. Banco de Dados e Armazenamento

* **Banco de Dados Relacional/NoSQL:** **ausente**. Nenhum DDL, migration, schema ou ORM model no projeto. 🟢
* **Estado em Memória (global mutável):** dicionários `people` e `families`, grafo `networkx`, e mapa `child_to_family`, populados por `upload.py` e lidos por `path_search.py` e `dna_analysis.py`. 🟢
* **Persistência:** apenas os arquivos enviados em `uploads/`. Resultados não são persistidos entre requisições — o GEDCOM é **re-parseado a cada POST**. 🟢

---

## 6. Cobertura de Testes

| Métrica | Valor |
| --- | --- |
| Framework | **pytest** (`pytest.ini`) 🟢 |
| Arquivos de teste | **7** (5 unitários + 2 de caracterização) 🟢 |
| Funções `def test_` | **52** 🟢 (eram 61 antes da remoção de 9 testes das entidades extintas) |
| Itens coletados por `pytest --collect-only` | **86** 🟢 (eram 95; 85 passam, 1 erra por restrição de sandbox) |
| Linhas de teste | **1134** 🟢 |
| Cobertura estimada | Não medida — sem `pytest-cov` nem configuração de cobertura. 🟡 |

**Tipos de teste presentes:** unitários por módulo (`domain`, `upload`, `path_search`, `dna_analysis`), **caracterização de matching** e **caracterização de Mermaid** (congelam a saída observável) e um arquivo dedicado ao **escape de rótulo Mermaid** (`test_mermaid_escape.py`).

---

## 7. Sugestão de Organização das Specs (Scout)

* **`granularity`:** `endpoint`
* **Razão:** A superfície é um **roteamento centralizado** de rota única com despacho por campo `action`; os três valores distintos de `action` delimitam exatamente três unidades funcionais.
* **Sinais observados:**

| Sinal | Evidência |
| --- | --- |
| Roteamento centralizado | `analisador-genealogico/app.py` — decorador `@app.route("/", methods=["GET", "POST"])`, despacho por `request.form.get("action")` nas linhas 21, 44 e 65 |

> **Decisão já persistida.** `.reversa/config.toml` → `[specs]` já contém a decisão de 2026-08-03: `layout = "feature-folder"`, `granularity = "endpoint"`, `scout_suggestion = "endpoint"`. Esta sugestão **confirma** a decisão existente; conforme a regra de imutabilidade, o campo `scout_suggestion` **não** é reescrito pelo orquestrador.

---

*Gerado pelo Reversa-Scout em 2026-09-30 (re-extração).*

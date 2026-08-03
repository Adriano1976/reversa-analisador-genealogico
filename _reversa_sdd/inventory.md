# Inventário do Sistema Legado — analisador-genealogico

> Gerado pelo **Scout** em 2026-08-03
> Nível de documentação: **Completo**

---

## 1. Visão Geral

* **Nome do Projeto:** analisador-genealogico (Genetic Genealogy Path Analyzer)
* **Descrição:** Aplicação web em Flask para genealogistas genéticos que identifica, calcula e visualiza conexões genealógicas entre uma pessoa raiz e correspondentes de DNA, cruzando árvores GEDCOM (.ged) com listas de segmentos de DNA (.csv).
* **Linguagem Principal:** Python 3
* **Framework Principal:** Flask
* **Arquitetura:** Monolito Web (Server-Side Rendering com Flask + Jinja2)

---

## 2. Estrutura de Árvore de Diretórios

```
analisador-genealogico/
├── app.py                      # Aplicação Flask principal, parser GEDCOM, matching difuso, grafos NetworkX e rotas
├── requirements.txt            # Dependências Python do projeto
├── README.md                   # Documentação original do projeto
├── .gitignore.txt              # Regras de ignorar arquivos no Git
├── static/
│   └── graph_path_search.html  # Visualização HTML estática/gerada dos grafos de caminho
├── templates/
│   └── index.html              # Template principal Bootstrap 5 com formulários de upload e busca
└── uploads/                    # Diretório de armazenamento temporário dos arquivos GEDCOM e CSV enviados
```

---

## 3. Mapeamento por Módulo / Componente

| Módulo / Arquivo | Responsabilidade | Tecnologias Utilizadas |
| --- | --- | --- |
| `app.py` | Servidor web Flask, parsing de GEDCOM (`ged4py`), normalização e matching difuso de nomes (`thefuzz`), manipulação de DataFrame CSV (`pandas`), cálculo de menor caminho em grafos (`networkx`), agrupamento de cM e rotas de processamento. | Python 3, Flask, NetworkX, Pandas, Ged4py, TheFuzz |
| `templates/index.html` | Interface do usuário (Upload de GEDCOM/CSV, seletor de pessoa raiz, formulário de busca de caminho direta/indireta, exibição de resultados e alertas). | HTML5, Bootstrap 5, Mermaid.js |
| `static/graph_path_search.html` | Página estática gerada para renderizar grafos interativos de redes de parentesco. | HTML, Pyvis |
| `uploads/` | Armazenamento de arquivos `.ged` e `.csv` durante a sessão de análise. | Sistema de arquivos local |

---

## 4. Pontos de Entrada (Entry Points) & Configurações

* **Aplicação Principal:** `app.py` (`app = Flask(__name__)`, `if __name__ == "__main__": app.run(debug=True)`)
* **Interface Web:** `templates/index.html`
* **Rotas Flask:**
  * `GET /` — Exibe formulário inicial de upload de GEDCOM.
  * `POST /` (`action="process_dna"`) — Processa arquivo GEDCOM + CSV de DNA e exibe conexões e predição de cM.
  * `POST /` (`action="path_search"`) — Busca caminho direto ou indireto entre duas pessoas da árvore GEDCOM.
* **Configurações Internas:**
  * `app.secret_key` = `'f@milyse@rch_dna_edition_v16'`
  * `UPLOAD_FOLDER` = `"uploads"`
  * `STATIC_FOLDER` = `"static"`

---

## 5. Banco de Dados & Armazenamento

* **Banco de Dados Relacional/NoSQL:** Ausente (não utiliza SGBD).
* **Estrutura de Dados em Memória:**
  * Dicionários `people` e `families` para representar o GEDCOM.
  * Grafo `networkx.Graph` e `networkx.DiGraph` para representar pessoas, famílias e relações de parentesco/afinidade.
* **Persistência Temporária:** Arquivos físicos enviados via upload salvos na pasta `uploads/`.

---

## 6. Cobertura de Testes e CI/CD

* **Framework de Testes:** Nenhum detectado.
* **Arquivos de Teste:** 0 arquivos.
* **CI/CD:** Nenhum workflow configurado (ausência de `.github/workflows`, `Jenkinsfile` ou `.gitlab-ci.yml`).
* **Docker:** Não possui `Dockerfile` nem `docker-compose.yml`.

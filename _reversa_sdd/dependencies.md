# Mapeamento de Dependências — analisador-genealogico

> Gerado pelo **Scout** em 2026-08-03

---

## 1. Gerenciador de Pacotes

* **Ecosistema:** Python
* **Gerenciador:** `pip` (`requirements.txt`)

---

## 2. Dependências Diretas (`requirements.txt`)

| Pacote | Versão Especificada | Categoria | Finalidade no Projeto |
| --- | --- | --- | --- |
| **Flask** | *Não fixada* | Framework Web | Roteamento HTTP, renderização de templates Jinja2 e servidor WSGI local. |
| **ged4py** | *Não fixada* | Parser | Parsing e navegação estruturada de arquivos GEDCOM (.ged). |
| **networkx** | *Não fixada* | Grafos & Algoritmos | Construção do grafo familiar e cálculo de menor caminho (`shortest_path`). |
| **pandas** | *Não fixada* | Análise de Dados | Leitura, limpeza e agregação de dados de segmentos cM em arquivos CSV de DNA. |
| **thefuzz** | *Não fixada* | Matching de Texto | Cálculo de distância e similaridade difusa (`ratio`, `token_sort_ratio`) entre nomes do GEDCOM e do CSV. |
| **python-Levenshtein** | *Não fixada* | Performance / C extension | Aceleração C para o `thefuzz`. |
| **pyvis** | *Não fixada* | Visualização de Grafos | Geração de grafos de parentesco interativos em HTML estático/dinâmico. |
| **matplotlib** | *Não fixada* | Plotagem | Suporte/fallback a visualizações gráficas de redes. |
| **gunicorn** | *Não fixada* | Servidor de Produção | HTTP WSGI server para deploy em produção (ex: Heroku, Render, AWS). |

---

## 3. Avaliação de Riscos de Dependências

> [!WARNING]
> **Versões Não Fixadas (Unpinned Dependencies):** O arquivo `requirements.txt` não especifica versões para nenhuma das dependências (ex: `Flask` em vez de `Flask==3.0.0`). Isso pode ocasionar breaking changes durante instalações em novos ambientes.

> [!NOTE]
> **Compatibilidade C-Extension:** `python-Levenshtein` requer toolchain de compilação C/C++ caso não haja wheel binário disponível no sistema operacional alvo.

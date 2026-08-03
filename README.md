# analisador-genealogico (Analisador de Caminhos em Genealogia Genética)

![Version](https://img.shields.io/badge/version-1.0-blue.svg)
![Python](https://img.shields.io/badge/python-3.x-blue.svg)
![Flask](https://img.shields.io/badge/flask-app-green.svg)

## Nome e Descrição do Projeto

**analisador-genealogico** é uma aplicação web desenvolvida para genealogistas genéticos. Seu objetivo principal é identificar, calcular e visualizar conexões genealógicas entre uma pessoa raiz e suas correspondências de DNA, cruzando árvores GEDCOM (`.ged`) com listas de segmentos de DNA (`.csv`).

## Stack Tecnológica

O projeto conta com uma stack web moderna em Python, sem a necessidade de um banco de dados persistente:

- **Linguagem Principal:** Python 3
- **Framework Web:** Flask
- **Processamento de Dados:** Pandas (manipulação de CSV)
- **Grafos & Algoritmos:** NetworkX (busca de caminhos, BFS)
- **Leitura de GEDCOM:** Ged4py
- **Busca Aproximada (Fuzzy Matching):** TheFuzz
- **Frontend & UI:** HTML5, Jinja2, Bootstrap 5, Mermaid.js, Pyvis

## Arquitetura do Projeto

O sistema opera como um **Servidor Web Monolítico** com renderização do lado do servidor (SSR). Ele funciona puramente como uma ferramenta de análise sob demanda:

- **Gerenciamento de Estado:** Totalmente em memória (dicionários e grafos `networkx`). Não há banco de dados persistente. O estado é calculado por sessão/requisição.
- **Armazenamento de Arquivos:** Os arquivos enviados (`.ged` e `.csv`) são armazenados temporariamente em um diretório `uploads/` durante o processamento.
- **Fluxo de Processamento:** Ao receber uma requisição `POST`, o arquivo GEDCOM é processado e convertido em um grafo, as correspondências de DNA são agregadas a partir do CSV, e um algoritmo de busca de nomes por aproximação (*fuzzy matching*) é usado para encontrar caminhos até a pessoa raiz.

```mermaid
flowchart LR
    U["Genealogista Genético"]
    S(["analisador-genealogico"])
    C1[".ged (GEDCOM)"]:::ext
    C2[".csv (Matches de DNA)"]:::ext

    U -->|"upload GEDCOM + CSV"| S
    S -->|"parsing (análise)"| C1
    S -->|"agregando cM"| C2
```

## Começando (Getting Started)

### Pré-requisitos
- Python 3.x
- pip (gerenciador de pacotes do Python)

### Instalação e Configuração

1. Clone ou navegue até o diretório do repositório.
2. Instale as dependências necessárias:
   ```bash
   pip install -r requirements.txt
   ```
3. Execute a aplicação Flask:
   ```bash
   python app.py
   ```
4. Acesse a interface web em `http://127.0.0.1:5000/`.

## Estrutura do Projeto

```text
analisador-genealogico/
├── app.py                      # Aplicação Flask principal, parsing, rotas, lógica de grafos
├── requirements.txt            # Dependências do Python
├── static/
│   └── graph_path_search.html  # HTML estático gerado para grafos interativos (Pyvis)
├── templates/
│   └── index.html              # Template principal da UI (Bootstrap 5, Mermaid.js)
└── uploads/                    # Armazenamento temporário para os arquivos GEDCOM e CSV recebidos
```

## Principais Funcionalidades

- **Integração de GEDCOM & CSV:** Mescla a topologia da árvore (GEDCOM) com os dados genéticos (CSV).
- **Busca Aproximada de Nomes:** Algoritmo avançado para contornar "mojibake" (corrupção de codificação) e combinar nomes apesar de variações de grafia ou abreviações.
- **Previsões baseadas em cM:** Mapeia DNA compartilhado (centiMorgans) para prováveis graus de parentesco biológico.
- **Busca de Ancestrais Diretos:** Encontra o Ancestral Comum Mais Recente (MRCA - *Most Recent Common Ancestor*) e o caminho direto até 20 gerações de profundidade.
- **Busca de Caminhos Indiretos (Afinidade):** Utiliza uma Busca em Largura (BFS - *Breadth-First Search*) como alternativa para encontrar conexões por casamento e outras pontes de afinidade (até 40 saltos).
- **Redes Visuais:** Renderiza os caminhos da árvore genealógica de forma dinâmica usando Mermaid.js e Pyvis.

## Fluxo de Desenvolvimento

Atualmente, o projeto opera como uma base de código monolítica isolada (`app.py` possui cerca de 888 linhas).
- **CI/CD:** Não há pipelines de implantação automatizada ou arquivos Docker (Dockerfiles) configurados.
- **Deploy:** O `requirements.txt` inclui o Gunicorn, indicando um setup comum de implantação em produção padrão WSGI (ex: Heroku, AWS).

## Padrões de Código

- Toda a lógica está fortemente integrada dentro do `app.py`.
- Dicionários (`people`, `families`) e grafos do NetworkX são as principais estruturas de dados para o gerenciamento de memória.
- Lógicas complexas de leitura e extração de dados (como limpar caracteres corrompidos via `demojibake`) são isoladas em funções auxiliares específicas antes do processamento dos caminhos nos grafos.

## Testes

- **Abordagem de Testes:** Atualmente, há uma ausência de testes unitários ou de integração automatizados (não foram detectados frameworks ou arquivos de testes). Quaisquer mudanças devem ser verificadas manualmente através da interface web fazendo o upload de arquivos `.ged` e `.csv` de teste.

## Contribuindo

Ao contribuir para este projeto, por favor, considere as seguintes diretrizes:
1. Garanta que ajustes na lógica de *fuzzy matching* não aumentem os falsos positivos.
2. Se modificar os caminhos dos grafos (`networkx`), esteja ciente da sobrecarga de memória, uma vez que o estado é recalculado a cada requisição `POST`.
3. Evite adicionar requisitos de banco de dados persistente sem uma refatoração estrutural.
4. Adicione testes básicos para novas funcionalidades algorítmicas (como `find_ancestral_path` ou `find_indirect_path`) para melhorar a robustez do sistema.

## Autoria e Créditos
- Autor do Código Legado: [Sandro Azevedo](https://github.com/sssazevedo/analisador-genealogico)
- Autor do projeto Reversa: [Adriano Santos](https://github.com/Adriano1976)
- Autor do Framework Reversa: [Sandeco](https://github.com/sandeco/reversa)
- Fonte do Código Legado: [analisador-genealogico](https://github.com/sssazevedo/analisador-genealogico/tree/main)

## Licença

*(Nenhuma informação de licença foi fornecida explicitamente na documentação.)*

##
 
<br><br>

<div align="center">
  <p><b><h3> Contagem de visitantes </h3></b></p>  
  <img src="https://vbr.nathanchung.dev/badge?page_id=Adriano1976/reversa-analisador-genealogico" style="height: 30px;" />
   <br>
  <img width="100%" src="https://capsule-render.vercel.app/api?type=waving&color=87CEFA&height=120&section=footer"/>
</div>

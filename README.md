# analisador-genealogico (Analisador de Caminhos em Genealogia Genética)

![Version](https://img.shields.io/badge/version-1.0-blue.svg)
![Python](https://img.shields.io/badge/python-3.x-blue.svg)
![Flask](https://img.shields.io/badge/flask-app-green.svg)

## Nome e Descrição do Projeto

**analisador-genealogico** é uma aplicação web desenvolvida para genealogistas genéticos. Seu objetivo principal é identificar, calcular e visualizar conexões genealógicas entre uma pessoa raiz e suas correspondências de DNA, cruzando árvores GEDCOM (`.ged`) com listas de segmentos de DNA (`.csv`).

## Regra de análise (GEDCOM, DNA e confronto)

A aplicação separa rigorosamente três coisas, e nunca deixa uma contaminar a outra:

1. **Parentesco documental** — o que o GEDCOM afirma: caminho, ancestral comum, distância geracional, homônimos, caminhos múltiplos, colapso de pedigree e a evidência de cada salto (registro de família e datas).
2. **Evidência genética** — o que o arquivo de DNA informa: kit, fonte, cM total, segmentos, maior segmento, SNPs, cromossomo e posições.
3. **Possibilidades e confronto** — o cM vira uma **lista** de relacionamentos compatíveis pela tabela publicada do Shared cM Project 4.0, e o confronto devolve um dos quatro estados:

| Estado | Significado |
|---|---|
| **COMPATÍVEL** | o parentesco documental não entra em conflito evidente com o cM observado |
| **POSSÍVEL** | a evidência permite o relacionamento, mas não confirma o caminho documental |
| **CONFLITANTE** | a incompatibilidade é significativa; verifique as causas listadas |
| **INCONCLUSIVO** | os dados não permitem avaliar (sem DNA, sem caminho, homônimo ou sem faixa publicada) |

Três invariantes que o código e a interface respeitam:

- **O GEDCOM determina o parentesco documental.** O DNA não altera, não corrige e não cria caminho genealógico.
- **O cM não é usado sozinho para afirmar parentesco.** `cM → conjunto de possibilidades`, nunca `cM → parentesco único`.
- **DNA compartilhado não confirma o caminho.** O máximo que a tela afirma é que existe compartilhamento; o parentesco documental é apresentado em seção própria, com fonte declarada.

## Stack Tecnológica

O projeto conta com uma stack web moderna em Python, sem a necessidade de um banco de dados persistente:

- **Linguagem Principal:** Python 3
- **Framework Web:** Flask
- **Processamento de Dados:** Pandas (manipulação de CSV)
- **Grafos & Algoritmos:** NetworkX (busca de caminhos, BFS)
- **Leitura de GEDCOM:** Ged4py
- **Busca Aproximada (Fuzzy Matching):** TheFuzz
- **Frontend & UI:** HTML5, Jinja2, Bootstrap 5, Mermaid.js

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
2. Instale as dependências necessárias (o `requirements.txt` fica na raiz do repositório):
   ```bash
   pip install -r requirements.txt
   ```
3. Execute a aplicação (a partir da raiz do repositório). O ponto de entrada sobe a aplicação por um servidor WSGI de produção, e não pelo servidor de desenvolvimento do Flask:
   ```bash
   python src/app.py
   ```
4. Acesse a interface web em `http://127.0.0.1:5000/`. O endereço padrão atende **apenas a máquina local**; abrir para a rede é um ato explícito, descrito a seguir.

### Configuração de execução

O bloco de entrada lê três variáveis de ambiente. Todas têm padrão declarado no código, então nada precisa ser definido para subir a aplicação:

| Variável | Padrão | Para que serve |
|---|---|---|
| `ANALISADOR_HOST` | `127.0.0.1` | endereço de escuta. O padrão atende apenas a máquina local; use `0.0.0.0` para atender a rede |
| `ANALISADOR_PORT` | `5000` | porta de escuta |
| `ANALISADOR_THREADS` | `4` | número de threads do servidor |

#### Abrir a aplicação para a rede

> **A aplicação não tem autenticação.** Qualquer equipamento que alcance a porta vê a interface e pode enviar arquivos. É por isso que o padrão é fechado, e é por isso que abrir tem de ser decisão de quem opera, e não o que acontece por omissão.

No PowerShell, a partir da raiz do repositório:

```powershell
$env:ANALISADOR_HOST = "0.0.0.0"
python src/app.py
```

A inicialização informa o endereço em uso (`Servindo com waitress em http://0.0.0.0:5000 ...`). De outro equipamento da mesma rede, acesse `http://<ip-da-máquina>:5000/`. Em rede compartilhada, mantenha o padrão e não defina a variável.

#### Uma instância por vez

A aplicação **recusa subir** se já houver uma instância atendendo no endereço e na porta configurados. A segunda execução termina com código de saída diferente de zero e uma mensagem que nomeia o endereço e a porta:

```text
Recusando subir: 127.0.0.1:5000 ja esta em uso (...). Encerre o processo que ja esta no ar, ou suba esta instancia em outra porta com ANALISADOR_PORT.
```

O trecho entre parênteses é o diagnóstico do sistema operacional, no idioma dele, e por isso não aparece aqui literalmente. O motivo da recusa é o modelo de estado: a árvore enviada vive na memória de cada processo, então duas instâncias seriam dois estados independentes, e a mesma pessoa poderia receber "nenhuma árvore carregada" logo depois de enviar um GEDCOM. Encerre a instância anterior (Ctrl+C na janela dela) antes de subir outra, ou suba a nova em outra porta com `ANALISADOR_PORT`.

## Estrutura do Projeto

```text
src/                            # raiz de código da aplicação
├── app.py                      # Aplicação Flask: rotas e orquestração das requisições
├── parsers/                    # Leitura do mundo de fora: o arquivo GEDCOM e o CSV de matches
│   ├── gedcom_parser.py        # Leitura do GEDCOM e construção do grafo networkx
│   └── csv_ingest.py           # Leitura do CSV de matches e agregação de cM por segmento
├── core/                       # Decisão sobre o que foi lido, sem saber de HTTP
│   ├── documentary_relationship.py  # Parentesco DOCUMENTAL: caminho, MRCA, homônimos, caminhos múltiplos, colapso de pedigree, datas
│   ├── genetic_evidence.py     # Evidência GENÉTICA: kits, cM, segmentos, SNPs, cromossomo, posições (nunca soma kits diferentes)
│   ├── relationship_hypotheses.py   # cM → possibilidades, pela tabela publicada do Shared cM Project 4.0
│   ├── evidence_comparison.py  # Confronto GEDCOM × DNA: COMPATÍVEL / POSSÍVEL / CONFLITANTE / INCONCLUSIVO
│   ├── cm_estimator.py         # LEGADO: faixas de cM escritas à mão, mantidas só como superfície de compatibilidade
│   ├── matching.py             # Índices do GEDCOM e decisão de aceitação de candidatos
│   ├── name_normalization.py   # Normalização e decomposição de nomes (norm_name, split_name_pt)
│   ├── path_finding.py         # Busca direta por ancestral comum (MRCA) e indireta por afinidade
│   ├── family_navigation.py    # Resolução de pessoa por nome e navegação de parentesco
│   ├── gedcom_state.py         # Estado do GEDCOM carregado: pessoas, famílias e grafo
│   ├── path_search.py          # Fachada da busca de caminhos, consumida pelo app.py
│   └── dna_analysis.py         # Orquestra as três etapas do cruzamento, consumida pelo app.py
├── reporting/                  # Transformação de resultado em apresentação
│   └── mermaid_render.py       # Emissão do diagrama Mermaid e contrato de escape do rótulo
├── utils/                      # Ferramentas utilitárias, sem papel no núcleo
│   ├── text_cleaning.py        # Autoridade única de limpeza de mojibake (strip_bad_utf, demojibake)
│   └── validate.py             # Validação do upload: nome visível, chave de conteúdo e GEDCOM
├── templates/
│   └── index.html              # Template principal da UI (Bootstrap 5, Mermaid.js)
└── uploads/                    # Criado em tempo de execução pelo app.py; recebe os arquivos enviados e não é versionado
```

Na raiz do repositório ficam `requirements.txt`, `pytest.ini`, `pyrefly.toml` e este `README.md`. A documentação original do projeto, em inglês, e o arquivo de ignore do módulo foram removidos: o primeiro anunciava uma biblioteca que o projeto abandonou na migração para Mermaid, e o segundo só continha regra para um artefato que o projeto deixou de gerar.

### Pastas do Framework Reversa

Os artefatos do Reversa ficam na raiz do repositório e não fazem parte do runtime da aplicação:

```text
.reversa/            # Configuração, estado, princípios, hooks e snapshots do framework
.agents/skills/      # Skills dos agentes do Reversa instalados
_reversa_sdd/        # Especificações extraídas do legado (o output_folder do framework)
_reversa_forward/    # Pipelines de evolução do código a partir das specs
_reversa_bugs/       # Intake, triagem e rastreabilidade de bugs
_reversa_refactor/   # Inventário de oportunidades de refatoração e suas transformações
_reversa_docs/       # Mini-site HTML de documentação (publicado no GitHub Pages)
```

A política de escrita do Reversa é definida em `.reversa/reversa-config.json`. Neste projeto `allowLegacyEdits` é `true`, com `allowedPaths` cobrindo `src/**`, `tests/**`, `README.md`, `pyrefly.toml`, `.vscode/**`, `requirements.txt` e `analisador-genealogico/**`; escritas fora desses caminhos são recusadas pelo framework.

O último glob é herança da árvore anterior à feature `003-renomear-pasta-app-para-src`: a pasta `analisador-genealogico/` deixou de existir quando a raiz de código passou a ser `src/`, e o caminho segue liberado sem corresponder a nada. Ele é inofensivo, e a remoção é ato exclusivo do usuário, porque `reversa-config.json` não é editado por agente.

### Testes

```text
tests/
├── fixtures/
│   ├── sample_dna.py                   # GEDCOM e CSVs sintéticos para análise de DNA
│   └── sample_gedcom.py                # GEDCOM sintético para parsing e busca de caminhos
├── test_domain.py                      # Limpeza de mojibake de nomes GEDCOM
├── test_upload.py                      # Parsing de GEDCOM e construção do grafo
├── test_path_search.py                 # Busca de ancestrais diretos e caminhos por afinidade
├── test_dna_analysis.py                # Agregação de segmentos, fuzzy matching e previsões por cM
├── test_characterization_matching.py   # Caracterização: congela a decisão de matching e a forma do payload
├── test_characterization_mermaid.py    # Caracterização: congela a saída do diagrama Mermaid
├── test_confrontacao_gedcom_dna.py     # Regra final: os 10 cenários exigidos (GEDCOM, DNA, confronto, homônimos, múltiplos kits)
├── test_mermaid_escape.py              # Contrato de escape do rótulo Mermaid
├── test_servidor_producao.py           # Bloco de entrada: servidor de produção, guarda de instância única e padrão do endereço
└── test_upload_seguranca.py            # Teto de requisição, chave derivada do conteúdo e recusa de GEDCOM inválido
```

## Principais Funcionalidades

- **Integração de GEDCOM & CSV:** Cruza a topologia da árvore (GEDCOM) com os dados genéticos (CSV) **sem misturar as duas evidências**, que aparecem em seções separadas do resultado.
- **Busca Aproximada de Nomes:** Algoritmo avançado para contornar "mojibake" (corrupção de codificação) e combinar nomes apesar de variações de grafia ou abreviações.
- **Possibilidades pelo DNA (Shared cM Project 4.0):** Traduz o cM compartilhado em uma **lista** de relacionamentos compatíveis, com faixa e média da fonte. Nunca devolve um parentesco único e nunca apresenta o cM como confirmação.
- **Confrontação GEDCOM × DNA:** Compara o parentesco documental com a evidência genética e devolve COMPATÍVEL, POSSÍVEL, CONFLITANTE ou INCONCLUSIVO, com a explicação e a lista de causas a verificar quando há conflito.
- **Alertas de plausibilidade documental:** Sinaliza vínculo cronologicamente impossível (genitor nascido depois do filho), homônimos com ficha comparável (ID, datas, locais, pais, cônjuges, filhos), caminhos genealógicos múltiplos e colapso de pedigree/endogamia.
- **Busca de Ancestrais Diretos:** Encontra o Ancestral Comum Mais Recente (MRCA - *Most Recent Common Ancestor*) e o caminho direto, com teto de 20 iterações de profundidade no BFS bidirecional.
- **Busca de Caminhos Indiretos (Afinidade):** Utiliza uma Busca em Largura (BFS - *Breadth-First Search*) como alternativa para encontrar conexões por casamento e outras pontes de afinidade (até 40 saltos).
- **Redes Visuais:** Renderiza os caminhos da árvore genealógica de forma dinâmica usando Mermaid.js.

## Fluxo de Desenvolvimento

O projeto originalmente monolítico (o `app.py` legado possuía cerca de 888 linhas) foi **reconstruído e modularizado** com o framework [Reversa](https://github.com/sandeco/reversa): a lógica foi extraída para `src/`, organizada nos pacotes `parsers/`, `core/`, `reporting/` e `utils/`, e o `app.py` passou a apenas orquestrar as rotas Flask (251 linhas — o crescimento sobre as 84 originais vem da validação de upload introduzida pela correção do BUG-20260929-QMLY e do bloco de entrada que sobe o servidor de produção).
- **CI/CD:** Não há pipeline de build ou de testes automatizado. O único workflow é o `.github/workflows/deploy-pages.yml`, que publica o mini-site de `_reversa_docs/` no GitHub Pages e dispara em pushes para a branch `main` (a branch principal do repositório é `master`). Não há Dockerfile nem `docker-compose.yml`.
- **Deploy:** O servidor de produção é o `waitress`, que roda em Windows sem compilação, e o `requirements.txt` fixa cada dependência com `==`, nas versões validadas nesta máquina em Python 3.14. A execução é o próprio `python src/app.py`, com as variáveis de ambiente documentadas acima; não há passo de build nem arquivo de configuração de servidor.

## Padrões de Código

- A lógica de negócio está modularizada em `src/`, nos pacotes `parsers/`, `core/`, `reporting/` e `utils/`, separada da camada web (`app.py`).
- A regra final da análise vive em quatro módulos de responsabilidade única, sem ciclo entre eles: `documentary_relationship` (GEDCOM), `genetic_evidence` (CSV), `relationship_hypotheses` (Shared cM Project 4.0) e `evidence_comparison` (confronto). Nenhum deles conhece HTTP, e **nenhum deles deixa o DNA alterar o parentesco documental**.
- Números exibidos passam por `utils/number_format.py`, autoridade única do formato (`cm_br` para cM e `inteiro_br` para SNPs e posições). O arredondamento é só de apresentação: o `float` somado permanece exato no estado.
- O estado é mantido **em memória** (dicionários `people`, `families` e grafos `networkx`), não persistente, recalculado por sessão/requisição.
- As rotinas de limpeza de caracteres corrompidos (`demojibake`, `strip_bad_utf`) ficam em `text_cleaning.py`, como autoridade única. As entidades `Family`, `GenealogyGraph` e `DNAGroup` viviam ali como arquitetura abandonada — nenhuma era instanciada em produção — e foram removidas em 2026-09-30.
- Busca de caminhos em `path_finding.py`: direto por MRCA (teto de 20 iterações de profundidade) e indireto por afinidade (até 40 saltos). A emissão do diagrama e o contrato de escape do rótulo ficam em `mermaid_render.py`, e `path_search.py` é a fachada consumida pelo `app.py`.
- Cruzamento GEDCOM × CSV, fuzzy matching e previsão de parentesco por faixas de cM em `dna_analysis.py` (fachada), com a leitura do CSV em `csv_ingest.py`, a decisão de aceitação de candidatos em `matching.py` e a normalização de nomes em `name_normalization.py`.
- Validação do upload (teto de requisição, chave de armazenamento derivada do conteúdo e recusa de GEDCOM inválido) em `validate.py`.

## Testes

- **Abordagem de Testes:** A suíte automatizada usa **pytest** (`pytest.ini` aponta para `tests/`) e conta com **119 funções de teste** — o total coletado é **166** — cobrindo limpeza de mojibake, parsing de GEDCOM, construção de grafo, busca de caminhos, análise de DNA (agregação de segmentos, fuzzy matching e possibilidades por cM), a regra final da análise (parentesco documental, evidência genética, possibilidades, confronto e os dez cenários de `test_confrontacao_gedcom_dna.py`), caracterização de matching e de Mermaid, segurança do upload e o bloco de entrada do `app.py` (qual servidor sobe, a guarda de instância única e o padrão do endereço de escuta).
- **Como rodar (da raiz do repositório, onde está o `pytest.ini`):**
  ```bash
  pip install -r requirements.txt pytest
  pytest
  ```

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
- Documentação Antes: [mini-site do projeto](https://adriano1976.github.io/_reversa_docs/)
- Documentação Depois: [mini-site do projeto](https://adriano1976.github.io/_reversa_docs_v2/)

## Licença

Este repositório inclui um arquivo LICENSE com os termos de licenciamento. Consulte `LICENSE` para detalhes.

##
 
<br><br>

<div align="center">
  <p><b><h3> Contagem de visitantes </h3></b></p>  
  <img src="https://vbr.nathanchung.dev/badge?page_id=Adriano1976/reversa-analisador-genealogico" style="height: 30px;" />
   <br>
  <img width="100%" src="https://capsule-render.vercel.app/api?type=waving&color=87CEFA&height=120&section=footer"/>
</div>

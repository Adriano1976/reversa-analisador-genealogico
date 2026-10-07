# Investigation: fronteira de aplicação em `src/` (Onda 2 do cutover)

> Identificador: `006-fronteira-aplicacao-ports`
> Data: `2026-10-07`
> Requirements: `_reversa_forward/006-fronteira-aplicacao-ports/requirements.md`

## 1. Pergunta de investigação

Esta feature não pesquisa tecnologia nova. Ela pesquisa **uma** coisa: qual é o menor conjunto de traços que transforma `index()` numa borda fina sem alterar nenhum comportamento observável, dentro de um alvo que é `src/` com Flask — e não o projeto `analisador/` com FastAPI que os artefatos de migração pressupunham.

As perguntas derivadas, em ordem de impacto:

1. Onde vive a hierarquia de exceção, dado que quem **detecta** as condições são o núcleo e o parser, e o núcleo não pode importar a borda?
2. Quantas portas são realmente necessárias para os três fluxos, e alguma delas é orquestração disfarçada?
3. O que atravessa da aplicação para o adaptador, dado que as mensagens de tela são contrato congelado?
4. O que fazer com `load_gedcom_and_build_graph`, que ficou como casca de compatibilidade no `T009` e cujo último consumidor é a suíte?
5. Qual é a forma que permite o `dna_analysis` sair por último sem deixar o `app.py` num estado misto insustentável?

## 2. Estado atual medido

Não por leitura: por varredura do código em 2026-10-07.

| Medida | Valor | Método |
|---|---|---|
| Linhas de `src/app.py` | 344 | contagem de linhas do arquivo; o `harness` do Scout registrava 262 antes da feature 005 |
| Blocos de orquestração dentro de `index()` | 3 (`upload_gedcom`, `dna_analysis`, `path_search`) | leitura de `index()`, linhas 174–249 |
| `except Exception` genéricos | 3 | `app.py:190`, `:231`, `:245` |
| Pontos que levantam erro de domínio | 4 | `dna_analysis.py:127`, `:152`; `genetic_evidence.py:125`; `csv_ingest.py:177` |
| Classes de exceção próprias no projeto | **0** | varredura por `class .*(Error\|Exception)` em `src/`: nenhuma |
| Asserções que exigem `pytest.raises(ValueError)` | 4 | `test_confrontacao_gedcom_dna.py:920`, `:936`; `test_dna_analysis.py:219`, `:241` |
| Montagens de `Dependencias` em `app.py` | **2** | `:32` (módulo) e `:217` (a cada requisição de DNA, com os mesmos cinco argumentos) |
| Consumidores de produção de `load_gedcom_and_build_graph` | **0** | varredura em `src/`: `app.py:21` importa `carregar_arvore`; `harness.py` consome `carregar_arvore` |
| Consumidores de teste da casca | 3 arquivos | `test_upload.py` (2 pontos), `test_arvore_devolvida.py`, e um comentário em `fixtures/arvore_atual.py` |
| Golden files de tela capturados | 7 de 8 | `screens/golden/manifest.yaml`, `present: true` em 7 entradas; `present: false` na que exige navegador headless |

## 3. Alternativas avaliadas

### 3.1 Onde vive a hierarquia de exceção

| Alternativa | A favor | Contra | Veredito |
|---|---|---|---|
| **`src/core/erros.py`, importado por `core/` e `parsers/`** | Cada ponto que detecta levanta o tipo certo; a direção do import é a que `RF-13` permite (`parsers/` → `core/` já existe) | Põe vocabulário de falha da aplicação dentro do núcleo | **Escolhida** (`D-01`) |
| `src/application/excecoes.py` | Mantém o núcleo sem noção de "erro de aplicação" | Obriga `core/` a importar `application/`, que é exatamente a inversão que `RF-13` proíbe e que o teste de dependências cobra | Descartada |
| Pacote `src/dominio/` novo | Separação limpa em teoria | Cria uma quarta camada de topo para cinco classes, e nenhuma decisão de topologia pediu isso — `topology_decision.md#Decisão do usuário` fixou a fronteira em `application/`, `ports/`, `adapters/`, `api/`, `presentation/` | Descartada |
| Manter `ValueError` e traduzir no caso de uso | Não toca no núcleo | O núcleo segue sem contrato tipado, que é metade do pré-requisito "contrato tipado" do `cutover_plan.md` | Descartada |

**Achado que decidiu o ponto.** A herança de `ValueError` não é preferência: é o que faz as quatro asserções existentes continuarem válidas. Isso foi verificado por leitura das quatro, e cada uma confere **também o texto** da mensagem. Ou seja, a hierarquia nova tem duas obrigações simultâneas de compatibilidade — o **tipo** capturável e o **texto** preservado — e é por isso que a decisão `D-01` separa as duas: o tipo muda e o texto não.

### 3.2 Quantas portas, e quais

| Alternativa | A favor | Contra | Veredito |
|---|---|---|---|
| Duas portas: armazenamento e carregador de árvore | Cobre os dois I/O reais dos três fluxos; ambas têm método único | Nenhum | **Escolhida** (`D-02`) |
| Uma porta só, de armazenamento | Mínimo absoluto | Os casos de uso passariam a importar `parsers.gedcom_parser` para obter a árvore, acoplando aplicação a borda | Descartada |
| O caso de uso recebe a árvore pronta, sem porta de carregador | Zero porta nova | O adaptador passaria a resolver caminho e parsear **antes** de chamar o caso de uso, em dois dos três ramos — lógica de borda duplicada, e a resolução de referência é justamente o que `_gedcom_do_formulario()` centralizou em 2026-10-06 | Descartada |
| Três portas, incluindo `RepositorioDeArvores` **com** adaptador em memória | Prepara a Onda 3 "de verdade" | Um adaptador em memória com estado reintroduziria o estado global que a feature 005 removeu — a mesma classe de defeito, com outro nome | Descartada como adaptador; a porta entra **sem consumidor** (`D-03`) |

**Achado.** A porta do carregador de árvore não é orquestração disfarçada, mas está no limite: ela existe porque a **resolução da referência** (validar a forma da chave e conferir existência) é regra de borda que hoje vive em `_resolver_caminho_armazenado()`. Se essa porta ganhar um segundo método, a decisão está errada. O `/reversa-audit` deve verificar esse ponto explicitamente.

### 3.3 O que atravessa da aplicação para o adaptador

O `requirements.md` fixou resultado tipado (`RF-20`) e, ao mesmo tempo, obriga a preservar nove literais de tela (`RN-04`). As duas coisas são compatíveis **apenas** se a mensagem for um **campo declarado** do resultado, e não texto montado na aplicação. A alternativa — o caso de uso devolver a mensagem já formatada como "a mensagem da tela" — colocaria a aplicação escolhendo texto de interface, que é a violação de fronteira que a feature existe para corrigir ("domínio emite apresentação", diagnosticada em `topology_decision.md#Diagnóstico estrutural`).

| Alternativa | A favor | Contra | Veredito |
|---|---|---|---|
| Campo declarado no resultado tipado | Preserva o literal e mantém a aplicação ignorante de template | Exige que o tipo do campo seja explícito sobre ser texto de contrato | **Escolhida** (`RF-20`) |
| Mapa de classe → string constante no adaptador | Simples | **Não funciona:** 7 das 9 mensagens interpolam valores | Descartada (`D-04`) |
| `str(excecao)` jogado no template | Zero tradução | Acopla o texto de tela ao texto da exceção; mudar um quebra o outro, e o `"Ocorreu um erro: "` que o teste prende é prefixo que a exceção não carrega | Descartada |

### 3.4 A casca `load_gedcom_and_build_graph`

| Alternativa | A favor | Contra | Veredito |
|---|---|---|---|
| Remover, migrando os 3 consumidores de teste para `carregar_arvore` | Fecha a superfície morta que o `T023` deveria ter absorvido; `RF-12` da feature 005 já declarou a política de não manter nome histórico sem consumidor | Mexe em teste, ainda que preservando asserções | **Escolhida** (`D-06`) |
| Manter marcada como legado | Zero risco | Deixa em produção uma função que nenhum código de produção chama, com docstring que afirma o falso ("a suite e o harness dependem da lista") | Descartada |

## 4. Padrões aplicáveis

Os três já estão decididos nos artefatos de migração; esta feature é a primeira que os materializa de fato.

| Padrão | Onde está decidido | Como esta feature o aplica |
|---|---|---|
| **Ports & Adapters** (hexagonal) | `topology_decision.md#Topologia moderna proposta` | `ports/` com `Protocol`; adaptadores concretos que delegam para `utils/validate.py` e `parsers/gedcom_parser.py`; o núcleo não conhece nenhum dos dois |
| **Branch by Abstraction** | escolha do usuário em 2026-10-07, registrada em `requirements.md` §4 | A fronteira é extraída **no lugar**, sobre o `src/` que já roda, com o orquestrador antigo (`index()`) reduzido a adaptador. Nada é reescrito em projeto paralelo |
| **Dependency Injection** (manual) | `paradigm_decision.md#Paradigma natural inferido`, adaptado: não há `Depends()` sem FastAPI | O adaptador monta as dependências e as passa ao caso de uso como parâmetro. É DI por parâmetro explícito, que é a forma que o núcleo de funções puras aceita |

### Padrões **não** aplicados, e por quê

- **Repository com persistência.** `RepositorioDeArvores` entra como contrato, **sem** implementação e **sem** consumidor. Criar um adaptador em memória seria reintroduzir estado global com nome novo. A implementação é da Onda 3.
- **Unit of Work.** Só faz sentido com transação, e não há banco. `topology_decision.md` previa `ports/unit_of_work.py`; ele **não** entra nesta onda por não ter o que delimitar.
- **Eventos de domínio.** `topology_decision.md#Implicações pendentes` é explícito: "PARADIGMA NÃO É EVENT-DRIVEN. Não inventar eventos de domínio."
- **`api/routers/` com FastAPI.** `RN-05` e a decisão de 2026-10-07 mantêm o Flask como adaptador de entrada. Sem aplicação HTTP nova não há `routers/`, `schemas/` de payload nem `errors.py` de status — a tabela de tradução existe, testável, em `src/application/`.

## 5. ADRs do legado que restringem esta feature

| ADR | Restrição que impõe |
|---|---|
| `_reversa_sdd/adrs/02-camada-de-rota-fina.md` | "O `app.py` deixa de conter regra de negócio." É o ADR que esta feature **executa**: a Onda 2 é a continuação direta dele, agora com portas explícitas |
| `_reversa_sdd/adrs/16-leitura-tolerante-do-csv.md` | "Descarte reportado em vez de falha." O fallback de encoding e a leitura tolerante **não** podem virar exceção: `RF-11` e `RN-03` os preservam |
| `_reversa_sdd/adrs/17-upload-por-chave-de-conteudo.md` | A chave derivada do conteúdo, o teto de corpo e a extensão preservada formam **um** movimento. A porta de armazenamento tem de carregar os três juntos, e é por isso que `RF-09` exige o reuso por conteúdo |
| `_reversa_sdd/adrs/18-single-tenant-por-aceite-de-risco.md` | O sistema é single-tenant **por aceite de risco declarado**, não por esquecimento. `owner_id` entra como parâmetro obrigatório de contrato e **sem** comportamento — declarar isolamento implementado seria contrariar o ADR |
| `_reversa_sdd/adrs/20-formatacao-numerica-so-na-apresentacao.md` | A formatação numérica tem autoridade única e mora na apresentação. O resultado tipado do caso de uso **não** pode pré-formatar número: os filtros `cm_br` e `inteiro_br` continuam sendo aplicados pelo template |

## 6. Fontes externas

A feature não introduz dependência nova — nenhuma biblioteca é acrescentada ao `requirements.txt`. O que ela usa da linguagem:

- `typing.Protocol` (PEP 544) para as portas: permite contrato estrutural sem herança, o que mantém os adaptadores desacoplados da porta. Já disponível na biblioteca padrão do interpretador do projeto.
- `dataclasses` para os resultados tipados: mesma biblioteca padrão, sem dependência nova.
- Português como idioma de identificadores de domínio, seguindo o que o repositório já faz (`carregar_arvore`, `chave_de_armazenamento`, `nome_do_arquivo_armazenado`). Os três nomes de exceção que o `paradigm_decision.md` grafou em inglês (`RootPersonNotFound`, `UnsupportedGedcom`, `DnaCsvMissingColumns`) foram mantidos como **referência** no `requirements.md` e traduzidos na implementação, porque o resto do vocabulário de domínio é em português e misturar os dois idiomas na mesma hierarquia seria pior que a divergência de grafia com o artefato de migração.

## 7. O que esta investigação **não** resolveu

1. **Se `core/erros.py` é o lugar definitivo.** A decisão `D-01` é 🟡, não 🟢, e a razão é honesta: ela resolve o problema de direção de import, mas coloca dentro do núcleo um vocabulário ("erro de domínio", "não suportado") que tem sabor de fronteira. A alternativa de um pacote `dominio/` foi descartada por não ter sido pedida pela topologia, não por ser tecnicamente pior. Se a Onda 3 introduzir um bounded context real, este é o primeiro candidato a mudar de lugar.
2. **O custo real da porta do carregador de árvore.** Ela preserva o parse único por requisição, mas **não** elimina o re-parse por requisição: `path_search` e `dna_analysis` continuam re-parseando o GEDCOM a cada POST, como hoje (`domain.md#4` registra isso como contrato). Eliminar o re-parse exige persistência, que é a Onda 3. Nenhuma melhoria de desempenho é prometida aqui.
3. **O comportamento do mapeamento exceção → status HTTP.** A tabela nasce com a coluna de status, mas **nenhum consumidor a exercita** nesta onda, porque não há API nova. `RF-18` cobre isso com teste direto, o que é o melhor que se pode fazer sem inventar uma aplicação HTTP só para consumir a tabela.

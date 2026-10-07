# Data Delta: fronteira de aplicação em `src/` (Onda 2 do cutover)

> Identificador: `006-fronteira-aplicacao-ports`
> Data: `2026-10-07`
> Modelo extraído de referência: `_reversa_sdd/erd-complete.md`, `_reversa_sdd/data-dictionary.md`, `_reversa_sdd/architecture.md#4`
> Requirements: `_reversa_forward/006-fronteira-aplicacao-ports/requirements.md`

## 0. Veredito em uma linha

**Não há delta de dados.** Esta feature reorganiza quem chama o quê. Nenhuma estrutura de domínio é criada, alterada, removida ou migrada; nenhum campo muda de nome ou de tipo; nada passa a ser persistido. O que aparece são **tipos de resultado em memória** e **classes de exceção**, e nenhum dos dois é dado de domínio.

## 1. Entidades do ERD — verificação uma a uma

`_reversa_sdd/erd-complete.md` documenta 27 estruturas. As que o sistema realmente usa em fluxo são quatro mais uma já extinta. Conferência:

| # | Estrutura | Onda 2 | Observação |
|---|---|---|---|
| 1 | `PESSOA` | **inalterada** | Nenhum campo acrescentado, removido, renomeado ou retipado. A forma do registro continua sendo `SubRecord` do `ged4py`, consumida por `get_name` e `ref_id` em `core/registro.py` |
| 2 | `FAMILIA` | **inalterada** | Idem |
| 3 | `GRAFO_BIPARTIDO` | **inalterada** | Continua `networkx.Graph` **não direcionado e sem tipo de aresta**. A tipagem de filiação vs. casamento **não** entra aqui — é o conflito do Princípio IV, herdado e declarado em `roadmap.md` §2 |
| 4 | `CHILD_TO_FAMILY` | **inalterada** | Idem |
| 5 | `ESTADO_VERSAO` | **já extinta** | Apagada pela feature 005 junto com `core/gedcom_state.py`. Este documento a registra apenas para não deixar a lacuna em aberto |
| — | `DNA_MATCH` e demais estruturas derivadas do CSV | **inalteradas** | A chave de evidência continua `(nome, kit)`; a acumulação de cM continua sem arredondamento (`BR-D-15`) |
| — | 22 estruturas restantes do ERD | **não tocadas** | A feature não chega perto delas |

**Forma da árvore.** A tupla `Arvore = (people, families, graph, child_to_family)` atravessa a fronteira **sem alteração**. O `requirements.md` fixa isso em `RF-09` e `RF-11`; o `data-delta.md` da feature 005 registra a ordem de inserção como contrato de paridade (tag `@ordem`), e a extração não troca nenhuma estrutura por outra cujo percurso não preserve a ordem.

## 2. Estruturas novas — e por que não são dados de domínio

| Estrutura nova | Onde | Natureza | Persistida? |
|---|---|---|---|
| `ResultadoDeUpload` | `src/application/` | Valor de retorno do caso de uso: referência armazenada, nome exibido do arquivo, lista ordenada de nomes, mensagem de contrato | não |
| `ResultadoDeBuscaDeCaminho` | `src/application/` | Valor de retorno: `path_result`, lista de observações, mensagem de contrato, indicador de sucesso | não |
| `ResultadoDeAnaliseDeDna` | `src/application/` | Valor de retorno: resultados ordenados, descartados, mensagem de contrato | não |
| `ErroDeDominio` e os cinco tipos abaixo | `src/core/erros.py` | Vocabulário de falha | não |
| `Protocol` das três portas | `src/ports/` | Contrato de fronteira | não |

Nenhuma dessas estruturas é entidade, agregado ou value object. Elas não têm ciclo de vida, não têm identidade e não sobrevivem à requisição. **Se alguma delas um dia precisar ser persistida, isso deixa de ser Onda 2 e passa a ser a Onda 3** — e é exatamente por isso que a distinção está registrada aqui.

### Sobre a mensagem de contrato dentro do resultado

O `RF-20` proíbe que detalhe de apresentação atravesse a fronteira, e ao mesmo tempo `RN-04` obriga a preservar nove literais de tela. A resolução registrada no `requirements.md` §4 é que a mensagem viaja como **campo declarado** do resultado, não como texto montado na aplicação.

Consequência de modelagem, que este documento precisa registrar: o campo de mensagem é **dado de contrato congelado**, não dado de domínio. Quem o consome é o adaptador de entrada, para o template. Um segundo consumidor — a API nova, na Onda 3 — provavelmente **não** deve exibir esse texto ao cliente: ele é redação de tela do Flask, e a decisão de 2026-10-07 (`RN-05`) já separa os dois caminhos. Um reimplementador que tratar esse campo como dado de domínio vai carregar texto de interface para dentro da API.

## 3. Migrações necessárias

**Nenhuma.** Não há SGBD, não há schema, não há arquivo em formato próprio.

- Sem ETL, sem backfill, sem captura de delta, sem janela de congelamento de escrita.
- Sem migration de schema: não existe schema.
- Sem conversão de arquivo: os formatos de entrada (GEDCOM, CSV de matches) não são tocados.
- O único artefato em disco com papel de estado é a pasta `src/uploads/`, e ela **não** muda de leiaute: a chave derivada do conteúdo, a forma `^[0-9a-f]{16}__[A-Za-z0-9._-]+$` e a preservação da extensão continuam idênticas (`ADR-17`, `RF-09`).
- **Nada é removido.** Esta é uma feature aditiva em termos de estrutura: as estruturas novas convivem com as antigas, que não mudam.

## 4. Impacto em disco

| Caminho | Efeito |
|---|---|
| `src/core/gedcom_state.py` | **já apagado** pela feature 005; nada a fazer |
| `src/core/erros.py` | **novo** — cinco classes mais a raiz |
| `src/application/` | **novo** — três casos de uso e a tabela de tradução |
| `src/ports/` | **novo** — três `Protocol` e dois adaptadores concretos |
| `src/utils/validate.py` | **inalterado** — continua sendo a autoridade da regra de upload |
| `src/uploads/` | **leiaute inalterado**. A verificação manual produz resíduo ali, e o `_clean_residue.py` **não** o remove (`OBS-10`) |

## 5. Delta contra o que a extração antecipava

`_reversa_forward/005-nucleo-puro-src/data-delta.md` contém uma antecipação que **não se materializou** e que este documento corrige, para que ninguém a leia como pendência:

> "Quando o `T023` remover o estado ... a identidade volta a ser chave válida."

**Não volta.** O `T023` removeu o estado, e o `core/documentary_relationship.py` passou a invalidar o índice de nomes por chave **derivada do conteúdo** de `people` — `_chave_de(people)` devolve `(len(people), chaves[0], chaves[-1])`. `id()` foi **explicitamente rejeitado** como chave, porque é reciclado pelo interpretador e o defeito apareceria só sob carga. O comentário no código foi corrigido na feature 005; o texto do `data-delta.md` daquela feature não foi reescrito, e a correção fica registrada aqui.

**Consequência para esta feature:** nada. A porta do carregador de árvore devolve a árvore; quem a consome não assume nada sobre identidade de objeto. A regra do cache permanece como está, e o `W004` da feature 005 continua sendo o guarda.

## 6. Delta de dívidas do modelo

| Dívida (`architecture.md#7`) | Onda 2 | Por quê |
|---|---|---|
| #3 — contaminação entre requisições concorrentes | **INALTERADA** | A guarda de exclusividade continua de processo, não de thread. `RN-06` proíbe declarar o contrário, e há cenário negativo que recusa a entrega que o fizer |
| #4 — ausência de identidade e isolamento | **INALTERADA** | `owner_id` entra como parâmetro **obrigatório de contrato** e sem comportamento. Declarar isolamento implementado contrariaria o `ADR-18` (single-tenant por aceite de risco) |
| #8 — nada é persistido entre requisições | **INALTERADA** | Persistência é a Onda 3. O re-parse por requisição **continua**, e nenhuma melhoria de desempenho é prometida |
| #9 — o caminho indireto não passa pela checagem de datas | **INALTERADA** | Núcleo congelado; não tocado |
| #10 — o CSV de DNA não tem validação de conteúdo | **INALTERADA, e de propósito** | Corrigir muda comportamento observável e quebra paridade. Pelo Princípio II, é feature própria. A assimetria com o GEDCOM, que é validado antes de gravar, fica declarada |
| #17 — superfícies de compatibilidade | **INALTERADA** | Já fechada pela feature 005. Esta feature **não** reabre nenhuma: a remoção de `load_gedcom_and_build_graph` (`D-06`) é o resíduo da mesma política, não uma superfície nova |
| #18 — `cm_estimator` em disco | **INALTERADA** | Sem reexport e sem consumidor; fora do fluxo |

## 7. O que um reimplementador precisa saber

1. **Não há dado a migrar.** Qualquer documento desta feature que sugira ETL, backfill ou conversão está errado; `topology_decision.md#Implicações pendentes` já registrava que o `data_migration_plan` do pipeline é de **modelagem nova**, não de conversão.
2. **A tupla da árvore é o contrato.** `(people, families, graph, child_to_family)`, nessa ordem, com `people` e `families` como `dict` e o grafo como `nx.Graph` não direcionado. Trocar por uma estrutura cujo percurso não preserve a ordem de inserção quebra a paridade mesmo que o conteúdo seja igual.
3. **O grafo continua sem tipo de aresta.** Esta feature não corrige o Princípio IV e não deve ser citada como se tivesse corrigido.
4. **`id()` nunca é chave de cache.** O `W004` da feature 005 existe para isso.
5. **Nada nesta feature é persistido, e nada nesta feature é dado de domínio.** Se um dos tipos novos precisar de identidade ou ciclo de vida, a feature mudou de onda.

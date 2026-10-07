# Actions: fronteira de aplicação em `src/` — `application/` + `ports/` (Onda 2 do cutover)

> Identificador: `006-fronteira-aplicacao-ports`
> Data: `2026-10-07`
> Roadmap: `_reversa_forward/006-fronteira-aplicacao-ports/roadmap.md`

## Resumo

| Métrica | Valor |
|---------|-------|
| Total de ações | **31** |
| Paralelizáveis (`[//]`) | **4** (`T004`, `T006`, `T009`, `T015`) |
| Maior cadeia de dependência | **7 ações** (6 elos), por dois caminhos: `T001` → `T003` → `T010` → `T007` → `T011` → `T016` → `T019` e `T001` → `T003` → `T010` → `T007` → `T013` → `T018` → `T023` |
| Linha de base a preservar | `178 passed, 15 errors` e paridade `100%` em 6 fixtures, exit 0 (feature 005) |

**Composição:** 8 ações de preparação, 2 de teste, 5 de núcleo, 5 de integração e 11 de polimento.

> ⚠️ **A ordem não é preferência, é o plano.** `D-08` fixa a sequência de extração — `upload_gedcom` → `path_search` → `dna_analysis` — e `D-09` exige medir suíte e paridade **ao fim de cada bloco**, não só no fim. As ações `T019`, `T021`, `T022` e `T023` são os quatro pontos de medição. Medir só no fim tornaria impossível atribuir uma regressão ao bloco que a introduziu, que foi exatamente o que aconteceu no `T023` da feature 005: duas metades de uma ação executadas na ordem errada, 49 falhas sem ponto de atribuição.

> ⚠️ **A ordem das ações de preparação também é o plano.** `T002` (trocar o tipo levantado em `core/dna_analysis.py`) vem **antes** de `T015` (remover a casca `load_gedcom_and_build_graph`), e `T015` depende de `T011` e `T013` — as duas extrações que tiraram os últimos consumidores de produção da casca. Remover a casca antes de as extrações existirem deixaria o `app.py` sem caminho até o parse.

## Fase 1, Preparação

| ID | Descrição | Dependências | Paralelismo | Arquivo alvo | Confidência | Status |
|----|-----------|--------------|-------------|--------------|-------------|--------|
| T001 | Criar `src/core/erros.py` com a raiz `ErroDeDominio(ValueError)` e os **quatro** tipos abaixo dela — `PessoaNaoEncontrada`, `GedcomNaoSuportado`, `DnaCsvSemColunas`, `CsvIlegivel` —, cada um com docstring que declara o que **detecta**, quem o levanta e por que herda de `ValueError` (as quatro asserções da suíte capturam esse tipo). **Não** criar `ArmazenamentoInvalido`: o achado `A002` o descartou porque o adaptador de armazenamento nunca o levantaria | - | - | `src/core/erros.py` | 🟡 | `[ ]` |
| T002 | Trocar o tipo levantado nos dois pontos de `dna_analysis` — `PessoaNaoEncontrada` em `:127` e `DnaCsvSemColunas` em `:152` — **preservando o texto literal de cada mensagem ao caractere** e sem tocar em mais nada do módulo | T001 | - | `src/core/dna_analysis.py` | 🟢 | `[ ]` |
| T003 | Trocar o tipo levantado em `genetic_evidence.py:125` para `DnaCsvSemColunas`, preservando o texto, e em `csv_ingest.py:177` para `CsvIlegivel` (**`RF-21`**), também preservando o texto — sem tocar no fallback de encoding Latin-1 de nenhum dos dois | T001 | - | `src/core/genetic_evidence.py`, `src/parsers/csv_ingest.py` | 🟢 | `[ ]` |
| T004 | Extrair o teto de upload de `app.py:52` para constante nomeada no adaptador de entrada, com o valor intacto (`16 * 1024 * 1024`), docstring com a origem (`BUG-20260929-QMLY`) e um derivado em MB para a mensagem de `413` | - | `[//]` | `src/app.py` | 🟢 | `[ ]` |
| T005 | Criar `src/ports/__init__.py` com o `Protocol` de armazenamento de arquivo: um método que recebe conteúdo, nome original e tipo, valida antes de gravar e devolve a referência armazenada; e outro que resolve uma referência recebida para caminho, devolvendo ausência quando a forma é inválida ou o arquivo não existe | - | - | `src/ports/__init__.py` | 🟢 | `[ ]` |
| T006 | Acrescentar ao mesmo módulo o `Protocol` do carregador de árvore, com **um único** método que recebe uma referência e devolve a árvore | T005 | `[//]` | `src/ports/__init__.py` | 🟡 | `[ ]` |
| T007 | Criar `src/ports/adaptadores.py` com `ArmazenamentoEmDisco`, que delega para `utils/validate.py` — chave derivada do conteúdo, nome armazenado, validação de forma e validação de conteúdo **antes** de gravar — e com o carregador de árvore que resolve a referência e chama `carregar_arvore` | T005, T006 | - | `src/ports/adaptadores.py` | 🟢 | `[ ]` |
| T008 | Declarar no mesmo módulo o `Protocol` de repositório de árvores, com o dono como parâmetro **obrigatório** e sem implementação e sem consumidor, com docstring que declara ser contrato para a Onda 3 e **não** funcionalidade pronta | T005 | - | `src/ports/__init__.py` | 🟢 | `[ ]` |

> **Por que `T006` é paralela, se compartilha arquivo com `T005`.** O critério do Reversa exige arquivos alvo **diferentes**, e este é o único par do documento que o viola. Está marcada `[//]` mesmo assim porque a alternativa — declarar as duas portas numa ação só — juntaria duas asserções verificáveis separadamente, e o `T005` é a porta de armazenamento com duas operações enquanto o `T006` é uma porta de um método só. Se o executor preferir respeitar o critério ao pé da letra, execute `T006` depois de `T005`: o custo é de segundos e nenhuma dependência real é quebrada.

> **Sobre a confidência de `T001` (🟡).** A decisão `D-01` é 🟡: a hierarquia em `core/` resolve a direção de import, mas coloca dentro do núcleo um vocabulário com sabor de fronteira. As demais ações herdam 🟢 porque as decisões que as sustentam são confirmadas por leitura de código ou por regra 🟢 do legado.

> **Sobre a confidência de `T006` (🟡).** A decisão `D-02` é 🟡 e tem uma condição declarada: a porta do carregador tem **um** método, e se precisar de um segundo, a decisão está errada. O `/reversa-audit` deve verificar esse ponto quando reexecutado.

## Fase 2, Testes

| ID | Descrição | Dependências | Paralelismo | Arquivo alvo | Confidência | Status |
|----|-----------|--------------|-------------|--------------|-------------|--------|
| T009 | Escrever o teste que prova que cada tipo novo é capturável como `ValueError` **e** que a raiz `ErroDeDominio` captura os cinco — o teste que sustenta a `RF-05` e que impede a herança de ser removida numa refatoração futura | T001 | `[//]` | `tests/test_erros_de_dominio.py` | 🟢 | `[ ]` |
| T010 | Escrever o teste que prova que o caminho negativo do núcleo continua levantando exceção no mesmo ponto: confirmar que os quatro pontos migrados em `T002` e `T003` levantam os tipos novos e que a mensagem de cada um é o literal esperado, um a um | T002, T003 | - | `tests/test_erros_de_dominio.py` | 🟢 | `[ ]` |

## Fase 3, Núcleo

| ID | Descrição | Dependências | Paralelismo | Arquivo alvo | Confidência | Status |
|----|-----------|--------------|-------------|--------------|-------------|--------|
| T011 | Escrever o caso de uso `upload_gedcom` em `src/application/upload_gedcom.py`: recebe o arquivo, a identidade do dono e o armazenamento por parâmetro, valida pelo port, carrega a árvore pelo carregador e devolve resultado tipado com a referência, o nome exibido, a lista ordenada de nomes e a mensagem de contrato | T007 | - | `src/application/upload_gedcom.py` | 🟢 | `[ ]` |
| T012 | Escrever o caso de uso `path_search` em `src/application/path_search.py`: recebe os dois nomes, a árvore, as dependências de diagrama e a identidade do dono, chama `core.path_search.path_search` e devolve resultado tipado — sem nome de campo de template, sem `success=` e sem contexto de renderização. O resultado carrega o **desfecho** de três valores (`RESULTADO` para sucesso com payload, `SEM_RESULTADO` para sucesso sem payload, `ERRO_DE_ENTRADA` para falha sinalizada pelo núcleo), derivado do payload e do indicador de sucesso que o núcleo devolve — **nunca** do texto da mensagem (`D-11`). O núcleo **não** é alterado (`D-12`) | T007 | - | `src/application/path_search.py` | 🟢 | `[ ]` |
| T013 | Escrever o caso de uso `dna_analysis` em `src/application/dna_analysis.py`: recebe a referência do CSV, o nome da raiz, a árvore, `Dependencias` e a identidade do dono, chama o fluxo do núcleo e devolve resultado tipado com resultados, descartados e mensagem de contrato | T007 | - | `src/application/dna_analysis.py` | 🟢 | `[ ]` |
| T014 | Escrever a tabela de tradução em `src/application/traducao.py`: para cada tipo de `core/erros.py`, uma **função** que recebe a exceção e devolve a mensagem literal da tela e o status HTTP correspondente — função e não mapa, porque sete das nove mensagens congeladas interpolam valores | T001 | - | `src/application/traducao.py` | 🟢 | `[ ]` |
| T015 | Remover a casca `load_gedcom_and_build_graph` de `parsers/gedcom_parser.py` e migrar os três consumidores de teste para `carregar_arvore`, preservando todas as asserções — inclusive as de `tests/test_upload.py` e `tests/test_arvore_devolvida.py` — sem remover nem desabilitar teste | T011, T013 | `[//]` | `src/parsers/gedcom_parser.py`, `tests/test_upload.py`, `tests/test_arvore_devolvida.py` | 🟢 | `[ ]` |

> **`T015` está marcada `[//]` com reserva.** Ela toca quatro arquivos, e o critério pede até três arquivos não relacionados. Os quatro são relacionados — a remoção de uma função e a migração dos seus três consumidores —, então a ação continua atômica e cabe num turno. A marca `[//]` existe porque ela **não depende** das outras quatro ações da fase; o arquivo alvo principal é o parser.

> **Sobre `T015` e `RF-12`.** A remoção fecha o resíduo da política que a feature 005 adotou: superfície histórica sem consumidor não sobrevive. **Nenhum** consumidor de produção existe hoje — `app.py:21` importa `carregar_arvore` e o coletor do harness também, verificado por varredura. Se ao executar aparecer um consumidor de produção, a ação **para** e o achado sobe como desvio declarado, porque significaria que a varredura estava errada.

## Fase 4, Integração

| ID | Descrição | Dependências | Paralelismo | Arquivo alvo | Confidência | Status |
|----|-----------|--------------|-------------|--------------|-------------|--------|
| T016 | Fazer `index()` chamar o caso de uso `upload_gedcom` no ramo de upload, passando o armazenamento e o carregador montados na borda — **sem** mover para a rota nenhuma decisão que tenha ido para o caso de uso | T004, T011, T014 | - | `src/app.py` | 🟢 | `[ ]` |
| T017 | Fazer `index()` chamar o caso de uso `path_search` no ramo de busca, montando as dependências de diagrama na borda e passando o dono | T012, T014 | - | `src/app.py` | 🟢 | `[ ]` |
| T018 | Fazer `index()` chamar o caso de uso `dna_analysis` no ramo de DNA, injetando `Dependencias` pelo caso de uso e **removendo a montagem duplicada** que hoje existe em `app.py:217` (`D-05`) | T013, T014 | - | `src/app.py` | 🟢 | `[ ]` |
| T019 | Substituir os três `except Exception` genéricos de `index()` pela captura de `ErroDeDominio` traduzida pela tabela, e derivar o `success=` do template e o modo de renderização do **campo de desfecho** do resultado — nunca do texto da mensagem —, mantendo o `except Exception` de último recurso com o literal `"Ocorreu um erro: {e}"` intacto: o teste `tests/test_upload_seguranca.py:412` prende esse texto no HTML | T016, T017, T018 | - | `src/app.py` | 🟢 | `[ ]` |
| T020 | Verificar que nenhuma sequência de passos de domínio sobrou em `index()`: varredura por chamada a parser, agregador de CSV, resolvedor de diagrama e aos dois fluxos do núcleo, registrando a saída como evidência | T019 | - | `_reversa_forward/006-fronteira-aplicacao-ports/evidence/` | 🟢 | `[ ]` |

> **`T004` e `T016` a `T019` são sequenciais de fato — cinco ações, um arquivo.** Todas editam `src/app.py`, e é por isso que **nenhuma** delas leva `[//]`: o critério do Reversa exige arquivos alvo diferentes, e elas não o cumprem entre si. `T004` (o teto) vem primeiro, na Fase 1; `T016`, `T017` e `T018` mexem em ramos distintos de `index()` mas no mesmo arquivo, e `T019` só entra depois das três. Executá-las fora de ordem ou em paralelo é o caminho direto para o defeito que o `T023` da feature 005 produziu — duas metades de uma ação aplicadas na ordem errada, 49 falhas.

> **Sobre `T019`.** O `except Exception` de último recurso **não** pode ser removido: ele é o que produz `"Erro ao processar GEDCOM: {e}"` e `"Ocorreu um erro: {e}"` para tudo que **não** é erro de domínio — e é o caminho de produção para `CsvIlegivel` antes de `T003` o tipar. A ordem importa: `T019` só entra depois de os três casos de uso existirem, senão não há o que traduzir.

## Fase 5, Polimento

| ID | Descrição | Dependências | Paralelismo | Arquivo alvo | Confidência | Status |
|----|-----------|--------------|-------------|--------------|-------------|--------|
| T021 | Medir e registrar o resultado do bloco 1 (`upload_gedcom`): suíte completa e paridade nas 6 fixtures, comparando com a linha de base registrada no `T004` da feature 005 (`178 passed, 15 errors` e 100% de paridade) e guardando a saída como evidência | T016 | - | `_reversa_forward/006-fronteira-aplicacao-ports/evidence/` | 🟢 | `[ ]` |
| T022 | Medir e registrar o resultado do bloco 2 (`path_search`): suíte e paridade, mesma comparação | T017 | - | `_reversa_forward/006-fronteira-aplicacao-ports/evidence/` | 🟢 | `[ ]` |
| T023 | Medir e registrar o resultado do bloco 3 (`dna_analysis`) e o resultado final: suíte, paridade e a contagem de testes, confirmando que nenhum teste foi removido, desabilitado ou reescrito | T018, T015 | - | `_reversa_forward/006-fronteira-aplicacao-ports/evidence/` | 🟢 | `[ ]` |
| T024 | Escrever o teste direto da tabela de tradução que prova o mapeamento exceção → status HTTP (`RF-18`), sem subir aplicação HTTP nova, com a coluna de status marcada como sem consumidor nesta onda | T014 | - | `tests/test_traducao_de_erros.py` | 🟡 | `[ ]` |
| T025 | Executar a verificação manual de ponta a ponta do `onboarding.md` — servidor por `waitress`, `HTTP 200`, formulário, upload, DNA, busca de caminho nos dois modos e as três mensagens negativas — e limpar o resíduo de `src/uploads/` conferindo `git status` contra a linha de base (Princípio I) | T023, T024 | - | `_reversa_forward/006-fronteira-aplicacao-ports/evidence/` | 🟢 | `[ ]` |
| T026 | Escrever o teste que prova que o modo de renderização vem do **desfecho** e não do texto: com desfecho `SEM_RESULTADO`, o adaptador exibe "nenhuma conexão encontrada" como resultado bem-sucedido, e alterar o texto da mensagem **não** muda o modo escolhido (achado `A003`, `RF-06` e `RF-20`) | T012, T014 | - | `tests/test_desfecho_do_resultado.py` | 🟢 | `[ ]` |
| T027 | Escrever o teste que prova que a validação de conteúdo do GEDCOM acontece **antes** da gravação: um conteúdo inválido produz a exceção de GEDCOM não reconhecido e a pasta de upload continua vazia (`RF-10`) | T007, T011 | - | `tests/test_porta_de_armazenamento.py` | 🟢 | `[ ]` |
| T028 | Escrever o teste que prova que o contrato do repositório de árvores exige o dono: uma chamada montada sem o parâmetro é recusada pelo próprio contrato (`RF-08`) | T008 | - | `tests/test_porta_de_armazenamento.py` | 🟡 | `[ ]` |
| T029 | Estender o teste da tabela de tradução com o caso de GEDCOM não reconhecido, provando que a moldura literal `"Arquivo não reconhecido como GEDCOM: {motivo}."` é montada **na tradução** e que a exceção carrega apenas o motivo (`RF-03`, `A002`) | T014 | - | `tests/test_traducao_de_erros.py` | 🟢 | `[ ]` |
| T030 | Estender o teste existente de upload acima do teto para conferir o **literal** `"Arquivo maior que o limite de 16 MB."` na resposta, e não apenas o status `413` e a ausência de gravação, como `tests/test_upload_seguranca.py:154` faz hoje | T016 | - | `tests/test_upload_seguranca.py` | 🟢 | `[ ]` |
| T031 | Escrever o teste dos dois literais negativos de upload que hoje não têm cobertura — campo de arquivo ausente → `"Nenhum arquivo GEDCOM enviado."` e nome de arquivo vazio → `"Nenhum arquivo selecionado."` —, com o texto conferido ao caractere (achado `A005`) | T016 | - | `tests/test_upload_seguranca.py` | 🟢 | `[ ]` |

> **`T030` e `T031` não levam `[//]`.** As duas editam `tests/test_upload_seguranca.py` e o critério de paralelismo exige arquivos alvo diferentes — a mesma razão pela qual as cinco ações de `src/app.py` também não levam a marca.

> **`T026` a `T031` nasceram da auditoria, e não do plano original.** `T026` e `T029` fecham o achado `A003` e a lacuna de rastreabilidade do `A002`; `T027`, `T028`, `T030` e `T031` fecham o `A005`, que registrou quatro cenários Gherkin sem ação que os verificasse. Nenhuma delas executa trabalho novo de produto: todas verificam comportamento que os requisitos já exigiam e que nenhuma ação media.

> **Os quatro pontos de medição são o portão de `D-09`.** `T020` mede forma (a fronteira existe), e `T021` a `T023` medem comportamento (nada mudou). Um bloco que fecha sem a sua medição registrada não fecha — é a única forma de uma regressão continuar atribuível ao bloco que a introduziu.

## Notas de execução

> Reservado para `/reversa-coding` registrar avisos ou observações que surgiram durante a execução.
> Não use isso para corrigir ações, edits manuais ficam fora desse arquivo, vão direto no código.

## Histórico de alterações

| Data | Alteração | Autor |
|------|-----------|-------|
| 2026-10-07 | Versão inicial gerada por `/reversa-to-do` | reversa |
| 2026-10-07 | Revisão pós-auditoria (`audit/cross-check.md`): `T001` passa a criar **quatro** tipos (`A002`); `T012` e `T019` passam a declarar e a consumir o **campo de desfecho** (`A003`, `D-11`); `T026` a `T031` acrescentadas para os cenários Gherkin sem verificação (`A005`) e para o caso de tradução do GEDCOM não reconhecido (`A002`). Total de 25 para 31 ações | reversa |

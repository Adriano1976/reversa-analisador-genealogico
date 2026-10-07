# Roadmap: fronteira de aplicação em `src/` — `application/` + `ports/` (Onda 2 do cutover)

> Identificador: `006-fronteira-aplicacao-ports`
> Data: `2026-10-07`
> Requirements: `_reversa_forward/006-fronteira-aplicacao-ports/requirements.md`
> Confidência: 🟢 CONFIRMADO, 🟡 INFERIDO, 🔴 LACUNA

## 1. Resumo da abordagem

A orquestração dos três fluxos sai de `index()` e vira três casos de uso em `src/application/`, um por fluxo, na ordem `upload_gedcom` → `path_search` → `dna_analysis`. Cada caso de uso declara o que precisa por parâmetro — a árvore, a identidade do dono, o armazenamento, o carregador de árvore — e devolve um **resultado tipado**; nenhum detalhe de template atravessa essa fronteira.

O sinal de erro ganha hierarquia própria: `ErroDeDominio(ValueError)` como raiz, com `PessoaNaoEncontrada`, `GedcomNaoSuportado`, `DnaCsvSemColunas` e `CsvIlegivel` abaixo dela. A herança de `ValueError` é o que preserva as quatro asserções existentes da suíte sem reescrevê-las. Um quinto tipo, `ArmazenamentoInvalido`, foi **descartado** na auditoria: o adaptador de armazenamento nunca o levantaria, porque a validação devolve motivo em texto.

O resultado tipado carrega **três** coisas que o adaptador precisa e não pode inferir: os dados do fluxo, a mensagem de contrato congelada e um campo de **desfecho** de três valores (`RESULTADO`, `SEM_RESULTADO`, `ERRO_DE_ENTRADA`), do qual o adaptador deriva o `success=` do template. Sem esse campo, o adaptador teria de decidir o modo de renderização lendo o texto da mensagem.

**A assinatura do núcleo não muda.** O harness compara o indicador de sucesso dos fluxos contra o oráculo e nove asserções dependem da tupla de três: o caso de uso lê o que o núcleo já devolve.

Duas portas são criadas em `src/ports/`: armazenamento de arquivo e carregador de árvore. Um terceiro contrato, `RepositorioDeArvores`, entra **declarado e sem consumidor** — é o lugar tipado onde a Onda 3 vai pendurar `owner_id`. O adaptador de entrada (`app.py`) fica fino: recebe HTTP, chama o caso de uso e traduz o resultado ou a exceção para o template, com os literais congelados preservados ao caractere.

## 2. Princípios aplicados

| Princípio | Como a feature se relaciona | Status |
|-----------|------------------------------|--------|
| I. Dados reais de DNA/GEDCOM nunca entram no versionamento | Respeita. Nenhuma fixture nova usa dado real; a verificação manual usa os geradores sintéticos de `tests/fixtures/` e a ação de encerramento confere `git status` contra `src/uploads/` | respeita |
| II. Comportamento observável é preservado em refatoração | **É o princípio que governa esta feature.** A entrega é refactor: mesmas entradas, mesmas saídas, mesmos literais de tela, mesmos status. As duas exceções que a entrega **não** corrige de propósito — referência pendente no GEDCOM e ausência de validação de conteúdo no CSV de DNA — estão declaradas como tais, porque corrigi-las seria mudança de comportamento e percorreria o fluxo de requisito | respeita |
| III. Nenhuma mudança sem teste que a cubra | Respeita. As quatro asserções de `ValueError` continuam passando por herança, o que é verificação de que a hierarquia nova não quebrou o contrato antigo; os casos de uso ganham teste próprio de execução sem HTTP | respeita |
| IV. Arestas do grafo são tipadas | **Não é tocado por esta feature, e o conflito permanece.** A tipagem de aresta continua ausente e `find_indirect_path` continua contando filiação e casamento como o mesmo salto. A feature 005 registrou o conflito e o manteve aberto; esta não o fecha nem o agrava. Pelo Princípio II, a tipagem é mudança de comportamento e exige feature própria | conflita (herdado, declarado) |
| V. Toda suposição de genealogia genética cita a fonte | Respeita. Nenhum número de domínio é criado, alterado ou reinterpretado. A única constante nova é o teto de 16 MB, que já existe em `app.py:52` e é movido sem alteração de valor | respeita |

> **Sobre o Princípio IV.** Ele não é violado *por esta feature* — a violação é anterior e está documentada em `_reversa_forward/005-nucleo-puro-src/requirements.md` §4. O registro aqui serve para que ninguém leia "a Onda 2 fechou a fronteira" como "o grafo passou a distinguir filiação de casamento". Não passou.

## 3. Decisões técnicas

| ID | Decisão | Justificativa | Alternativas descartadas | Confidência |
|----|---------|----------------|--------------------------|-------------|
| D-01 | Os módulos de exceção ficam em `src/core/erros.py`, e **tanto `core/` quanto `parsers/` importam de lá** | Quem **detecta** cada condição é o núcleo (`dna_analysis`), o parser (`genetic_evidence`, `csv_ingest`) e o caso de uso de upload (ao receber o motivo da recusa de armazenamento). Com a hierarquia em `core/`, cada ponto levanta o tipo certo e o núcleo não precisa conhecer a borda. A alternativa — tipos em `application/` — exigiria que `core/` importasse `application/`, invertendo a direção que `RF-13` proíbe | (a) `src/application/excecoes.py`, exige import invertido; (b) pacote `src/dominio/` novo só para exceções, cria uma quarta camada para quatro classes; (c) traduzir `ValueError` no caso de uso, o que perde a tipagem no núcleo — que é o ponto da Onda 2; (d) um quinto tipo, `ArmazenamentoInvalido`, **descartado** no achado `A002`: o adaptador de armazenamento nunca o levantaria, porque `validate.py` devolve motivo em texto e não exceção | 🟡 |
| D-02 | A árvore é carregada por uma **porta injetada** (`CarregadorDeArvores`), e não por import do parser dentro dos casos de uso | Os casos de uso precisam da árvore nos três fluxos, e a rota já a parseia **uma vez por requisição** antes de ramificar. Sem a porta, o `upload_gedcom` parsearia por dentro do caso de uso e o `path_search`/`dna_analysis` receberiam a árvore de fora — o mesmo trabalho resolvido de duas formas. Com a porta, existe **um** lugar que resolve caminho e parseia, e os casos de uso ficam testáveis com um carregador falso | (a) o caso de uso importa `parsers.gedcom_parser` — acopla a aplicação a um pacote de borda, contra a intenção de `RF-01`; (b) o caso de uso chama o parser recebido por parâmetro e o adaptador repete a resolução de caminho em dois ramos — duplica lógica de borda; (c) aceitar **dois** parses por requisição de DNA ou de busca, para deixar o caso de uso se virar — piora o custo sem ganho de fronteira | 🟡 |
| D-03 | `RepositorioDeArvores` entra **declarado e sem consumidor**, como `Protocol` em `src/ports/` | `RF-08` exige que o dono seja parâmetro obrigatório do contrato **desde já**, porque adiar reabriria toda assinatura de porta na Onda 3. Declarar sem consumidor dá o lugar tipado onde a persistência vai encaixar, sem inventar comportamento: nenhum caso de uso o chama nesta onda. Isto é dívida técnica de **baixa gravidade** aceita de propósito — o registro fica em `regression-watch.md` no `/reversa-coding` | (a) adiar o contrato para a Onda 3, contra `RF-08`; (b) criar já um adaptador em memória com estado, o que reintroduziria o estado global que a feature 005 removeu | 🟢 |
| D-04 | O adaptador de entrada traduz exceção → literal por uma **tabela de funções**, e não por mapa de classe para string constante | Sete das nove mensagens congeladas de `12-paridade-telas.feature` interpolam valores (`"Pessoa 1 'X' não encontrada."`). Um mapa de classe para string não consegue construí-las; a tradução precisa receber a exceção e devolver o texto montado | (a) mapa de classe para constante, não cobre mensagem interpolada; (b) `str(excecao)` direto no template, o que acopla o texto de tela ao texto da exceção e torna impossível mudar uma sem a outra; (c) `match` estrutural espalhado pelos ramos da rota, que é a duplicação que a feature existe para remover | 🟢 |
| D-05 | `_DEPENDENCIAS` (a classe `Dependencias` do núcleo) continua sendo montada na borda e **injetada no caso de uso**, que a repassa ao fluxo de DNA | Decisão de 2026-10-07 já registrada em `requirements.md` §4: `Dependencias` permanece em `core/dna_analysis.py` e `ports/` não declara Protocolo para ela. O que muda é apenas **quem** a monta: sai de dentro do ramo da rota e passa a ser parâmetro do caso de uso, o que também corrige a montagem duplicada que existe hoje (`app.py:32` monta uma e `app.py:217` monta outra idêntica a cada requisição de DNA) | (a) mover `Dependencias` para `ports/`, mexendo na assinatura que a feature 005 estabilizou; (b) deixar o caso de uso montar a sua própria, que é o defeito latente de `RF-14` | 🟢 |
| D-06 | `load_gedcom_and_build_graph` é **removida** junto com a extração, e o `harness.py` deixa de citá-la | Ela ficou como casca de compatibilidade no `T009` e o `T023` deveria tê-la absorvido. Hoje **nenhum código de produção a consome**: `app.py:21` importa `carregar_arvore` e o coletor do harness também. Os únicos consumidores são `tests/test_upload.py`, `tests/test_arvore_devolvida.py` e um comentário em `tests/fixtures/arvore_atual.py`. A docstring ainda afirma que "a suite e o harness dependem da lista", o que a varredura desmente | (a) manter a casca, deixando superfície morta — exatamente a dívida #17 que a feature 005 fechou; (b) manter e marcar `# noqa`, sem resolver | 🟢 |
| D-07 | `AnalisadorDeUpload` e `ArmazenamentoEmDisco` nascem como **adaptadores concretos em `ports/`**, que delegam para `src/utils/validate.py` | As quatro funções de `validate.py` (chave por conteúdo, nome armazenado, validação de forma, validação de conteúdo) já são exatamente o contrato da porta. O adaptador não as reimplementa: ele as chama. Isso mantém a autoridade da regra em um só arquivo e evita que a extração vire uma segunda cópia da validação | (a) mover a lógica para dentro do adaptador, duplicando a autoridade; (b) deixar a rota chamar `validate.py` direto, mantendo a validação na borda HTTP em vez de atrás da porta | 🟢 |
| D-08 | A ordem de execução do `roadmap` põe o `dna_analysis` **por último**, em ação própria | Decisão `1-d` de 2026-10-07. O `upload_gedcom` prova o padrão com o fluxo mais curto; o `path_search` acrescenta a porta do carregador e o resolvedor de diagrama; o `dna_analysis` concentra as duas exceções tipadas do núcleo e três mensagens congeladas, e é onde há mais a perder | (a) os três de uma vez, sem ponto de parada; (b) começar pelo DNA, que é o mais arriscado logo no primeiro passo | 🟢 |
| D-09 | A verificação de paridade e a suíte rodam **ao fim de cada um dos três blocos**, não só no fim | `RF-16` exige não reduzir a suíte e `RF-15` exige 100% de paridade. Medir só no fim tornaria impossível atribuir uma regressão ao bloco que a introduziu — foi exatamente o que aconteceu no `T023` da feature 005, onde a ordem das duas metades da ação produziu 49 falhas sem ponto de atribuição | (a) medir só no fim; (b) medir por ação, que é ruído: as ações de um mesmo bloco não são independentes | 🟢 |
| D-10 | O teto de upload de 16 MB é movido para o adaptador de entrada como **constante nomeada**, com o valor intacto e a origem citada | `app.py:52` tem o literal `16 * 1024 * 1024`. A `RN-01` permite nomear constantes e proíbe alterar valores; nomear dá ponto único de mudança e permite ao teste referenciar a constante em vez de repetir o número. A mensagem de `413` interpola o teto em MB (`"Arquivo maior que o limite de 16 MB."`), então a constante precisa ser legível também nessa forma | (a) deixar o literal, contra o hábito que a Onda 2 quer estabelecer; (b) mover o teto para `ports/`, que não é o lugar de parâmetro de transporte HTTP | 🟢 |
| D-11 | O resultado tipado carrega um campo de **desfecho**, com três valores, e o adaptador deriva dele o `success=` do template e o modo de renderização | Achado `A003` da auditoria. Hoje a rota distingue "pessoa não encontrada" (`success=False`) de "nenhuma conexão encontrada" (`success=True` com resultado vazio) por uma linha em `app.py:240`, e a `RF-20` proíbe que o parâmetro `success=` atravesse a fronteira. Sem um campo que carregue o **fato**, o adaptador teria de inferi-lo do **texto da mensagem** — o que daria ao literal de tela autoridade semântica, exatamente o que a `RF-20` existe para impedir. Os três valores (`RESULTADO`, `SEM_RESULTADO`, `ERRO_DE_ENTRADA`) são derivados de dois insumos que o núcleo **já** sinaliza: a presença de payload e o indicador de sucesso | (a) enumeração com um quarto valor para "entrada inválida": **recusada**, porque nenhum caminho o preencheria — toda entrada inválida que não vem do núcleo já é exceção, e exceção interrompe o fluxo. Seria o mesmo tipo zumbi que o `A002` mandou remover; (b) deixar o adaptador inferir do texto, que é a opção que o achado condena; (c) fazer "pessoa não encontrada" virar exceção **dentro do núcleo**, que mudaria o que o harness observa e produziria divergência de paridade | 🟢 |
| D-12 | A assinatura de retorno do núcleo é **congelada**: a extração não altera a tupla que `path_search` e `dna_analysis` devolvem, nem o indicador de sucesso que ela carrega | Restrição dura, verificada em código: `_reversa_sdd/parity/harness.py:211` e `:412` comparam `_CTX.get("success")` contra o oráculo, e nove asserções de teste desempacotam a tupla de três (`tests/test_path_search.py:70`, `:80`, `:95`; `test_characterization_mermaid.py:129`; `test_mermaid_escape.py:109`; `test_confrontacao_gedcom_dna.py:502`, `:566`, `:810`). Acrescentar um campo à árvore (`Tree`) ou trocar o retorno dos fluxos por resultado tipado quebraria paridade e suíte ao mesmo tempo | (a) o caso de uso devolver o resultado do núcleo sem tocá-lo, que é o que esta decisão fixa; (b) "aproveitar a extração" para modernizar a assinatura do núcleo, contra a `RF-06` e o `RF-15` | 🟢 |

## 4. Premissas

Nenhuma. O `requirements.md` desta feature foi fechado com **zero** marcadores `[DÚVIDA]`: as três dúvidas da versão inicial e as duas acrescentadas pelo próprio `/reversa-clarify` foram resolvidas na sessão de 2026-10-07 e estão registradas na §9 daquele documento. Nada aqui depende de premissa não decidida.

## 5. Delta arquitetural

| Componente | Arquivo de origem no legado | Tipo de mudança | Resumo |
|------------|------------------------------|-----------------|--------|
| `src/api/` (citado em `topology_decision.md#Notas`) | `_reversa_sdd/migration/topology_decision.md#Notas` | **não criado nesta onda** | Decisão de 2026-10-07: o Flask permanece como adaptador de entrada, então não há `api/routers/`, `api/schemas/` nem `api/errors.py` agora. O mapeamento exceção → status existe como tabela testável em `src/application/`, sem aplicação HTTP nova |
| `src/application/` | `_reversa_sdd/migration/topology_decision.md#Notas` | componente-novo | Três casos de uso — `upload_gedcom`, `path_search`, `dna_analysis` — mais a tabela de tradução exceção → mensagem/status. É a camada que não existia |
| `src/ports/` | `_reversa_sdd/migration/topology_decision.md#Notas` | componente-novo | `Protocol` de armazenamento de arquivo, de carregador de árvore e de repositório de árvores; mais os dois adaptadores concretos que satisfazem os dois primeiros |
| `src/core/erros.py` | `_reversa_sdd/architecture.md#3` | componente-novo | A raiz `ErroDeDominio(ValueError)` e os **quatro** tipos abaixo dela (`PessoaNaoEncontrada`, `GedcomNaoSuportado`, `DnaCsvSemColunas`, `CsvIlegivel`). Não é limiar nem regra: é o vocabulário de falha que o núcleo passa a usar. Cada tipo carrega **apenas** a mensagem do seu ponto de detecção — a moldura de apresentação fica na tabela de tradução |
| `index()` em `src/app.py` | `_reversa_sdd/architecture.md#1` | contrato-alterado | Deixa de orquestrar. Passa a: ler a requisição, chamar o caso de uso, traduzir o resultado ou a exceção, renderizar. Perde as três sequências de passos de domínio e os três `except Exception` genéricos |
| `core/dna_analysis.py` | `_reversa_sdd/architecture.md#3` | regra-alterada | Os dois `raise ValueError` (`:127` e `:152`) passam a levantar `PessoaNaoEncontrada` e `DnaCsvSemColunas`, **com o texto intacto**. `Dependencias` permanece onde está |
| `core/genetic_evidence.py` | `_reversa_sdd/architecture.md#3` | regra-alterada | O `raise ValueError` de `:125` passa a levantar `DnaCsvSemColunas`, com o texto intacto |
| `parsers/csv_ingest.py` | `_reversa_sdd/architecture.md#3` | regra-alterada | O `raise ValueError` de `:177` passa a levantar `CsvIlegivel`, com o texto intacto — é o que a **`RF-21`** exige, fechando a lacuna de rastreabilidade que o achado `A002` encontrou (o tipo já tinha ponto de levantamento e teste, e passava sem requisito que o autorizasse). O fallback de encoding Latin-1 **não** é tocado (`RN-03`, `RF-11`) |
| `parsers/gedcom_parser.py` | `_reversa_sdd/architecture.md#3` | componente-extinto (parcial) | A casca `load_gedcom_and_build_graph` é removida (`D-06`). `carregar_arvore` e o `Tree` permanecem idênticos — **a forma da árvore não é alterada** (`D-12`) |
| `core/path_search.py` | `_reversa_sdd/architecture.md#3` | presença | **Nenhuma alteração.** A tupla de retorno e o indicador de sucesso são contrato observado pelo harness e por nove asserções de teste (`D-12`). O caso de uso lê esse retorno; não o reescreve |
| `core/dna_analysis.py`, fluxo de análise | `_reversa_sdd/architecture.md#3` | presença | **Nenhuma alteração na assinatura.** O fluxo continua devolvendo `(resultados, descartados, mensagem)`; o caso de uso o consome como está |
| `src/utils/validate.py` | `_reversa_sdd/architecture.md#3` | presença | **Nenhuma alteração.** As quatro funções continuam sendo a autoridade da regra de upload; o adaptador de armazenamento apenas as chama (`D-07`) |
| `_reversa_sdd/parity/harness.py` | `_reversa_sdd/migration/parity_harness.md` | presença | **Nenhuma alteração funcional.** Ele já consome `carregar_arvore`; só sai a menção textual a `load_gedcom_and_build_graph` no comentário, se houver |
| Dívida #3 (`architecture.md#7`) | `_reversa_sdd/architecture.md#7` | presença | **INALTERADA.** A guarda de exclusividade continua de processo, não de thread. `RN-06` proíbe declarar o contrário |
| Dívida #5 (`architecture.md#7`) | `_reversa_sdd/architecture.md#7` | presença | **INALTERADA.** Os ciclos `core/` ↔ `reporting/` e `core/` ↔ `parsers/` continuam. Esta feature não os toca |
| Dívida #10 (`architecture.md#7`) | `_reversa_sdd/architecture.md#7` | presença | **INALTERADA de propósito.** O CSV de DNA continua sem validação de conteúdo. A assimetria com o GEDCOM, que é validado antes de gravar, é preservada |
| Dívida #18 (`architecture.md#7`) | `_reversa_sdd/architecture.md#7` | presença | **INALTERADA.** `cm_estimator.py` permanece em disco, sem reexport |

## 6. Delta no modelo de dados

- Resumo das mudanças: **nenhuma no modelo.** Nenhum campo de `PESSOA`, `FAMILIA`, `GRAFO_BIPARTIDO` ou `CHILD_TO_FAMILY` é acrescentado, removido, renomeado ou retipado, e nenhum arquivo migra de formato. O que nasce são **três tipos de resultado** e **uma hierarquia de exceção** — estruturas em memória, sem persistência e sem schema. A dívida #8 ("nada é persistido entre requisições") continua aberta, e a dívida #10 continua com a assimetria declarada.
- Detalhe completo em: `_reversa_forward/006-fronteira-aplicacao-ports/data-delta.md`

## 7. Delta de contratos externos

| Contrato | Tipo | Arquivo de detalhe |
|----------|------|--------------------|
| `POST /` (as três `action` do formulário) | HTTP | **não alterado** — mesmas rotas, mesmos campos, mesmos status, mesmos literais. O diretório `interfaces/` **não** é criado nesta onda, conforme a regra do skill: `RN-05` determina que o contrato JSON com `404`/`422` só existe junto com a API nova, e ela não é desta onda. A tabela de tradução que o materializará fica em `src/application/`, testável, com um cabeçalho de `Status HTTP` sem consumidor ainda |

## 8. Plano de migração

> Não há dados a migrar: o sistema não tem SGBD e nada é persistido entre requisições. A "migração" aqui é de **código**, e o plano abaixo é a ordem de execução em blocos, cada um deles com parada e medição própria (`D-09`).

1. **Bloco 0 — fundação.** Criar `src/core/erros.py` com a hierarquia; apontar os quatro pontos que hoje levantam `ValueError` para os tipos novos, **sem tocar em nenhum texto**; criar `src/application/` e `src/ports/` com as portas e os adaptadores; mover o teto de 16 MB para constante nomeada. Medir: suíte e paridade.
2. **Bloco 1 — `upload_gedcom`.** Extrair o fluxo de upload para o caso de uso, com o adaptador de armazenamento atrás da porta e resultado tipado. `index()` passa a chamar o caso de uso. Medir: suíte, paridade e o cenário de upload da verificação manual.
3. **Bloco 2 — `path_search`.** Extrair o fluxo de busca, introduzindo a porta do carregador de árvore. Medir: suíte, paridade e a busca de caminho da verificação manual.
4. **Bloco 3 — `dna_analysis`.** Extrair o fluxo mais longo, injetando `Dependencias` pelo caso de uso e removendo a montagem duplicada. Remover a casca `load_gedcom_and_build_graph` e o último consumidor de teste. Medir: suíte, paridade e a análise de DNA da verificação manual.
5. **Bloco 4 — fechamento.** Verificar que `index()` não contém passo de domínio; conferir que nenhum literal de tela mudou; rodar a verificação manual de ponta a ponta; limpar resíduo de `src/uploads/` e conferir `git status` (Princípio I).

## 9. Riscos e mitigações

| Risco | Impacto | Probabilidade | Mitigação |
|-------|---------|---------------|-----------|
| Algum dos nove literais congelados muda de texto na tradução | alto | média | A tradução é por função que recebe a exceção, e o teste compara os literais da tabela contra a lista de `12-paridade-telas.feature`, um a um. Além disso, `tests/test_upload_seguranca.py:412` prende o literal `"Ocorreu um erro"` no HTML renderizado |
| `core/` passa a importar `parsers/` ou `application/` por causa das exceções | alto | baixa | `D-01` põe a hierarquia em `core/`, na direção permitida. Os quatro guardas de `tests/test_dependencias_nucleo.py` continuam valendo e são a verificação |
| A porta do carregador de árvore vira orquestração disfarçada no adaptador | médio | média | A porta tem **um** método, recebe a referência e devolve a árvore; nada mais. Se ela precisar de um segundo método, a decisão `D-02` está errada e o `/reversa-audit` deve pegá-la |
| `RepositorioDeArvores` sem consumidor ser lido como funcionalidade pronta | médio | média | `D-03` declara o item como dívida de baixa gravidade e `regression-watch.md` deve carregar o aviso no `/reversa-coding`, no mesmo padrão do `W003` da feature 005 |
| A extração do DNA mexer em `dna_analysis` além do `raise`, alterando resultado | alto | baixa | A ação do DNA **só** troca o tipo levantado, mantendo o texto; qualquer edição adicional é escopo novo e volta para o requirements. A paridade nas 6 fixtures e o probe de aceitação são a rede |
| A ordem das três extrações ser embaralhada na execução | médio | média | `D-08` fixa a ordem e `D-09` exige medição por bloco. O precedente do `T023` da feature 005 — duas metades de uma ação executadas na ordem errada, 49 falhas — está registrado aqui como razão |
| O resíduo da verificação manual ficar em `src/uploads/` e violar o Princípio I | baixo | alta | Ação de encerramento roda `git status` e confere; o `_clean_residue.py` **não** limpa essa pasta (`OBS-10`) |
| A remoção da casca `load_gedcom_and_build_graph` quebrar teste que a use como atalho | baixo | alta | Os três consumidores são de teste e migram para `carregar_arvore` no mesmo passo; as asserções são preservadas |

## 10. Critério de pronto

- [ ] Todas as ações do `actions.md` marcadas `[X]`
- [ ] `cross-check.md` (se executado) sem CRITICAL nem HIGH
- [ ] `regression-watch.md` gerado, **incluindo o aviso de que `RepositorioDeArvores` não tem consumidor**
- [ ] Nenhuma sequência de passos de domínio permanece em `index()` (`RF-01`)
- [ ] Nenhum literal de tela alterado, aferido contra os 7 golden files e contra a lista de `12-paridade-telas.feature` (`RF-06`, `RF-17`)
- [ ] Paridade diferencial em 100% nas 6 fixtures, exit 0 (`RF-15`)
- [ ] Suíte com **178 aprovados, 0 falhas esperadas, 15 erros de ambiente** — nenhum teste removido, desabilitado ou reescrito (`RF-16`)
- [ ] Verificação manual do `onboarding.md` executada e registrada em `evidence/`
- [ ] `git status` sem resíduo de `src/uploads/` e sem arquivo de instrumento não rastreado
- [ ] Nenhuma afirmação, em nenhum artefato da feature, de que a dívida #3 foi fechada (`RN-06`)

## 11. Histórico de alterações

| Data | Alteração | Autor |
|------|-----------|-------|
| 2026-10-07 | Versão inicial gerada por `/reversa-plan` | reversa |
| 2026-10-07 | Revisão pós-auditoria (`audit/cross-check.md`): `D-01` passa a quatro tipos com o `ArmazenamentoInvalido` descartado (`A002`); `D-11` acrescentada, fixando o campo de desfecho de três valores (`A003`); `D-12` acrescentada, congelando a assinatura de retorno do núcleo com a medição que a sustenta; delta arquitetural ganha as três linhas de "presença" que registram que o núcleo não é tocado | reversa |

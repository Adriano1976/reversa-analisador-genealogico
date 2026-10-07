# Adendo: fronteira de aplicação em `src/` — `application/` + `ports/` (Onda 2 do cutover)

> Identificador da feature: `006-fronteira-aplicacao-ports`
> Data: `2026-10-07`
> Cenário: **legado** (âncora em `_reversa_sdd/architecture.md` + `_reversa_sdd/domain.md`)

## Vigência

Vigente desde 2026-10-07.

## Resumo da entrega

A Onda 2 do `cutover_plan.md` exigia uma fronteira de aplicação com contrato
tipado, exceções de domínio e status HTTP semântico. A entrega **tirou a
orquestração de `index()`** e a colocou em três casos de uso — `upload_gedcom`,
`path_search` e `dna_analysis` —, atrás de três portas declaradas em
`src/ports/`: o armazenamento de arquivo, o carregador de árvores e o repositório
de árvores (este último **declarado sem implementação e sem consumidor**, como
contrato para a Onda 3). As condições de erro que antes viajavam como string de
retorno ou `except Exception` genérico passaram a ser **exceções de domínio
tipadas**, com raiz `ErroDeDominio(ValueError)`, e o adaptador de entrada traduz
cada uma de volta ao literal exato da tela.

**O alvo da migração é `src/`, com Flask servido por waitress.** Não existe e não
foi criado nenhum projeto `analisador/`; FastAPI, PostgreSQL e React continuam
especificados em `_reversa_sdd/migration/` e ficam para ondas posteriores. Os
artefatos de migração **não foram reescritos** — a divergência entre o esboço de
árvore de `topology_decision.md#Notas`, que pressupunha `analisador/`, e o alvo
real está declarada em vez de silenciada (decisão de 2026-10-07).

**Nenhum resultado de domínio mudou.** Nenhum limiar, peso, ordem de avaliação ou
critério do matching e do caminho foi alterado (`RN-01`), e isso foi verificado
por medição, não por inspeção.

**Progresso: 31 de 31 ações concluídas**, nenhuma aberta em `actions.md`.

| Prova | Resultado |
|---|---|
| Paridade diferencial contra o oráculo congelado | **100 %** nas 6 fixtures, exit 0 |
| Suíte | **231 aprovados, 0 falhas de código, 15 erros de ambiente** |
| Linha de base (feature 005) | 178 aprovados e **os mesmos 15 erros** |
| Mensagens de tela (19 casos: status, classe do alerta e texto) | **zero divergência** contra o `app.py` anterior à extração |
| Varredura de forma de `index()` | **APROVADO** — zero chamada de domínio |
| Verificação manual de ponta a ponta | **APROVADO** — `waitress`, os sete passos do onboarding |

A diferença de 53 aprovados é integralmente **verificação nova** — 13 em
`test_erros_de_dominio.py`, 17 em `test_traducao_de_erros.py`, 12 em
`test_desfecho_do_resultado.py`, 8 em `test_porta_de_armazenamento.py` e 3
acrescentados em `test_upload_seguranca.py` — e **nenhum teste de produto foi
removido ou desabilitado**. Os dois testes migrados (`test_upload.py`,
`test_arvore_devolvida.py`) mantiveram as asserções; dois deles só trocaram de
nome, porque o antigo falava de um estado global que não existe desde a feature
005.

## Impacto por artefato da extração

| Artefato | Seção | Tipo de impacto | Delta |
|---|---|---|---|
| `_reversa_sdd/architecture.md` | `#1` (Visão Geral) | `regra-alterada` | A orquestração dos três fluxos **saiu da rota**. Leia "a rota recebe o HTTP, orquestra e responde" como: a rota **adapta**, o caso de uso **orquestra** e o núcleo **decide**. A contagem de linhas do `src/app.py` caiu — medido agora: **335 linhas** (o §1 dizia 267, já defasado antes desta feature) |
| `_reversa_sdd/architecture.md` | `#3` (Componentes e estrutura de pacotes) | `componente-novo` | Dois pacotes que **não existem** no inventário: `application/` (4 módulos: `__init__`, `upload_gedcom`, `path_search`, `dna_analysis`, mais `traducao`) e `ports/` (o `__init__.py` declara os três `Protocol`, e `adaptadores.py` traz as implementações). `core/` ganha `erros.py`. Medido: **26 módulos em 6 pacotes** — eram 20 em 4 antes desta feature. ⚠️ Os números do §3 (19 módulos, 4 pacotes) **já estavam defasados antes** desta feature; o valor acima é medido, não reconciliado com o texto original |
| `_reversa_sdd/architecture.md` | `#3` (`parsers/`) | `componente-extinto` | `load_gedcom_and_build_graph` **saiu de `parsers/gedcom_parser.py`**. `carregar_arvore` e o `Tree` continuam **idênticos** — a forma da árvore é contrato de paridade e não foi tocada |
| `_reversa_sdd/architecture.md` | `#5` (O Fluxo que Define o Sistema) | `regra-alterada` | O fluxo agora atravessa **caso de uso e porta**: a rota não fala mais com `parsers/` nem chama o núcleo diretamente. As dependências de borda do núcleo continuam montadas na borda e injetadas, e passaram a ter **um único ponto de montagem** (havia dois) |
| `_reversa_sdd/architecture.md` | `#7` (Dívidas), #3 e #4 | `presença` | ❌ **INALTERADAS.** Nenhum comportamento de isolamento entre donos foi implementado (`RN-06`). O `dono` entrou como **parâmetro obrigatório** das portas e dos casos de uso, sem comportamento — é costura para a Onda 3. Leia a assinatura como lugar reservado, nunca como funcionalidade |
| `_reversa_sdd/architecture.md` | `#7` (Dívidas), #5 | `presença` | ❌ **INALTERADA.** Os ciclos `core/` ↔ `reporting/` e `core/` ↔ `parsers/` continuam idênticos. Esta feature moveu a orquestração, não as dependências entre pacotes. O núcleo continua sem importar `application/` ou `ports/` (guarda automática) |
| `_reversa_sdd/architecture.md` | `#7` (Dívidas), #10 | `presença` | ❌ **INALTERADA DE PROPÓSITO.** O CSV de DNA continua **sem validação de conteúdo**, e continua sendo gravado antes de qualquer verificação — diferente do GEDCOM. É assimetria preservada porque corrigi-la muda comportamento observável e quebraria paridade |
| `_reversa_sdd/architecture.md` | `#7` (Dívidas), #17 | `regra-alterada` | O resíduo da política foi fechado **de novo**: `load_gedcom_and_build_graph` era superfície histórica **sem consumidor de produção** (varredura confirmou zero) e foi removida |
| `_reversa_sdd/domain.md` | `#5.1` (Camada de rota) | `delta-de-contrato-externo` | As dez mensagens continuam **literais e nos mesmos casos**, mas a coluna "Local" aponta linhas do `app.py` anterior. A moldura de apresentação agora vive em **`src/application/traducao.py`**, e o motivo (ex.: `"arquivo vazio"`) vem dentro da exceção. Leia a tabela como contrato **preservado**, com o local de produção deslocado |
| `_reversa_sdd/domain.md` | `#5.2` (Núcleo) | `regra-alterada` | Os **textos não mudaram**; o **tipo** mudou. `"Seu nome '{root}' não foi encontrado no GEDCOM."` é agora `PessoaNaoEncontrada`; as duas variantes de colunas ausentes são `DnaCsvSemColunas`; a falha total de leitura do CSV é `CsvIlegivel`. Todos herdam de `ErroDeDominio(ValueError)`, e é essa herança que mantém válidas as quatro asserções de `pytest.raises(ValueError)` da suíte |
| `_reversa_sdd/domain.md` | `#3.5` (Upload e armazenamento) | `regra-alterada` | A regra **não mudou**: a validação de conteúdo acontece antes de gravar e conteúdo já armazenado não é regravado. O que mudou é que ela agora está atrás da porta `ArmazenamentoDeArquivos`, que **delega** para `utils/validate.py` — a autoridade da regra continua sendo um arquivo só |
| `_reversa_sdd/domain.md` | `#3.6` (Leitura tolerante do CSV) | `regra-alterada` | O fallback de encoding Latin-1 continua alcançável e nenhuma exceção de domínio o intercepta. O que mudou é a **sinalização da falha total**: `CsvIlegivel` em vez de `ValueError` genérico (`RF-21`), fechando a lacuna de rastreabilidade do achado `A002` da auditoria |
| `_reversa_sdd/domain.md` | `#2`, `#3.1`–`#3.4`, `#3.7`, `#4` | `presença` | **NENHUMA regra de negócio criada, alterada ou removida.** É a `RN-01` da feature, sustentada pela paridade em 100 % e pelas 19 mensagens idênticas. Inclui a ordem de apresentação dos resultados (`#3.7`) e a regra de que "não achei" não é erro |
| `_reversa_sdd/c4-components.md` | "Camada de rota" e "Inventário de componentes" | `componente-novo` | `application/`, `ports/` e `core/erros.py` **não estão no inventário**. Acrescentar. A camada de rota deixa de conter a orquestração |
| `_reversa_sdd/c4-components.md` | "Cadeia de dependência dos três fluxos" | `regra-alterada` | A cadeia do fluxo de upload cita `gedcom_parser.load_gedcom_and_build_graph` e `gedcom_state`, **nenhum dos dois existente**. A cadeia passa por `upload_gedcom` (caso de uso) → `ArmazenamentoDeArquivos` + `CarregadorDeArvores` (portas) → `carregar_arvore` |
| `_reversa_sdd/c4-components.md` | "Superfícies de compatibilidade (dívida assumida)" | `regra-alterada` | Nenhuma superfície de compatibilidade foi criada por esta feature. A que existia foi **removida** |
| `_reversa_sdd/code-analysis.md` | `#2.2` (Funções principais) | `componente-extinto` | A linha de `load_gedcom_and_build_graph` (`:53`) descreve função que **não existe mais** |
| `_reversa_sdd/code-analysis.md` | `#4.3` (Algoritmos e lógica não trivial) | `regra-alterada` | A justificativa registrada para o import dentro da função — "porque `load_gedcom_and_build_graph` **reatribui** o grafo" — já não valia desde a feature 005 e agora é duplamente falsa: a função não existe |
| `_reversa_sdd/flowcharts/upload-gedcom.md` | `#1` (fluxo principal) e `#2` (requisição seguinte) | `regra-alterada` | Os dois fluxogramas mandam para `load_gedcom_and_build_graph` (`:28` e `:52`). O passo agora é a porta `CarregadorDeArvores`, que resolve a referência e chama `carregar_arvore`; e o fluxo inteiro passa pelo caso de uso `upload_gedcom`. As guardas de formulário continuam na rota |
| `_reversa_sdd/upload-gedcom/design.md` | `### Símbolos` e `### Núcleo — parsing e publicação` | `componente-extinto` | O símbolo `load_gedcom_and_build_graph` (`gedcom_parser.py:50`) e a seção que descreve o retorno `list[str]` descrevem função removida. A seção `### Camada de rota (app.py:114-129)` também mudou de forma: a rota não faz mais o parse |
| `_reversa_sdd/upload-gedcom/requirements.md` | `## Rastreabilidade de Código` | `componente-extinto` | A linha `:148` aponta `load_gedcom_and_build_graph :50-69`, removed |

> **Nota sobre `c4-components.md`, `code-analysis.md`, `flowcharts/` e
> `upload-gedcom/`.** Nenhum desses artefatos é citado no `requirements.md` da
> feature. Todos foram incluídos aqui por **varredura**: os quatro afirmam a casca
> removida como parte do sistema atual. Um adendo que os omitisse deixaria a
> extração mentindo em quatro lugares.

## O que a extração **não** precisa mudar

Esta é a parte que costuma ser esquecida num adendo, e aqui ela é grande — porque a
feature foi desenhada para não mudar comportamento:

- **As regras de negócio.** Nenhuma foi criada, alterada ou removida. Os cinco
  ramos de aceitação do matching, o score difuso, o teto de 20 saltos do BFS
  bidirecional, o teto de 40 do caminho indireto, as nove faixas de cM que se
  sobrepõem e a ordem de apresentação continuam **intactos**.
- **O contrato de mensagens.** As dez mensagens da camada de rota (`domain.md#5.1`)
  e as nove congeladas de `12-paridade-telas.feature` continuam **ao caractere**,
  cada uma no mesmo caso, inclusive nos trechos interpolados. Medido em 19 casos
  com comparação de **status, classe do alerta e texto**.
- **A distinção "não achei" × "entrada inválida".** "Nenhuma conexão encontrada"
  continua saindo **com sucesso** e pessoa não encontrada **com erro**, e os dois
  casos têm o mesmo status HTTP. O que mudou é **onde** a distinção mora: antes era
  uma linha na rota; agora é um campo de **desfecho** do resultado tipado, para que
  o adaptador nunca precise inferi-la do texto da mensagem.
- **A forma dos dados.** O `Tree` continua a tupla de quatro elementos, a ordem de
  inserção segue contrato de paridade (tag `@ordem`) e **a assinatura de retorno do
  núcleo é congelada**: `path_search` e `dna_analysis` continuam devolvendo a tupla
  de três com o indicador de sucesso. O campo de desfecho vive no resultado do
  caso de uso, nunca no núcleo.
- **Os 15 erros de ambiente da suíte.** São **exatamente os mesmos** de antes desta
  feature, no mesmo arquivo, pela mesma causa. Não são regressão e não foram
  introduzidos aqui — ver "Lacunas declaradas".
- **A superfície HTTP.** Mesmas rotas, mesmos campos de formulário, mesmos status,
  mesmo template. O handler de `413` continua respondendo `413` com o mesmo literal
  de 16 MB, e o teto continua com o mesmo valor — só ganhou nome.

## Regras sob vigilância

`W005` a `W019`, definidos em
`_reversa_forward/006-fronteira-aplicacao-ports/regression-watch.md`, mais as
observações `OBS-11` a `OBS-20` do mesmo arquivo.

| Item | Cobre (índice) |
|---|---|
| `W005` | Literais de tela ao caractere, caso a caso |
| `W006` | Exceções de domínio capturáveis como `ValueError` |
| `W007` | "Não achei" é sucesso; pessoa não encontrada é erro |
| `W008` | Aviso de afinidade presente e em maiúsculas |
| `W009` | A casca `load_gedcom_and_build_graph` não volta |
| `W010` | `index()` sem passo de domínio |
| `W011` | Teto de upload: valor e mensagem |
| `W012` | Chave por conteúdo, validação antes da gravação |
| `W013` | Fallback Latin-1 do CSV |
| `W014` | Fallback de nome (`AMB-024`) |
| `W015` | Ponto único de montagem de `Dependencias` |
| `W016` | Assinatura de retorno do núcleo congelada |
| `W017` | Nenhum teste removido ou desabilitado |
| `W018` | Paridade em 100 % |
| `W019` | Divergência declarada: cabeçalho do resultado de DNA |

**Quatro itens merecem leitura explícita.** O `W007` existe para que ninguém
"simplifique" o desfecho para dois valores: os dois casos que ele separa têm o
mesmo status HTTP, e colapsá-los muda o que o operador vê. O `W016` guarda a
restrição dura da onda — o núcleo **não** foi modernizado, porque o harness compara
o indicador de sucesso contra o oráculo e nove asserções desempacotam a tupla. O
`W019` registra uma divergência **anterior a esta feature** entre o Gherkin
congelado e o template, que este adendo **não** resolve: o template não foi tocado,
porque mudar literal visível é o que a `RN-04` proíbe. E o `W009` fecha uma
superfície que a feature 005 já tinha declarado como dívida.

## O que fica fora deste adendo

1. **Os artefatos de migração (`_reversa_sdd/migration/`).** Este adendo anota a
   **extração**. A divergência entre a árvore de destino esboçada em
   `topology_decision.md#Notas` — que pressupunha um projeto `analisador/` — e o
   alvo real (`src/`, Flask + waitress) está **declarada como decisão** na sessão
   de 2026-10-07 e registrada em
   `_reversa_forward/006-fronteira-aplicacao-ports/requirements.md` §4. Os artefatos
   de migração não foram reescritos e continuam válidos como **plano de ondas
   futuras** (FastAPI, PostgreSQL, React).
2. **Os defeitos de ambiente desta máquina.** Não são do sistema extraído e não
   pertencem à extração. Estão em `regression-watch.md` (`OBS-12`, `OBS-13`) e em
   `_reversa_forward/006-fronteira-aplicacao-ports/evidence/README-evidencias.md`
   §2, com o inventário e o comando de remoção.

## Lacunas declaradas

Nem tudo neste adendo é uma afirmação verificada. O que segue é limite de
conhecimento, e não omissão:

1. **Os 15 erros de ambiente têm causa identificada, e ela não é `TEMP`.** Nesta
   máquina, `os.mkdir(caminho, 0o700)` cria um diretório que não pode ser listado,
   escrito nem apagado — nem pelo dono. O `tmp_path_factory` do pytest cria o
   diretório-base exatamente com esse modo, e é por isso que os 15 testes de rota
   morrem no `setup`. A anotação da feature 005 ("precisa de `TEMP`/`TMP`
   gravável") está **incompleta**: escrever dentro de um diretório criado por
   `mkdtemp` também é negado. Enquanto isso não for corrigido, **todo teste novo
   deve evitar `tmp_path`**.
2. **Existem 13 diretórios presos no workspace, oito deles anteriores a esta
   feature** (`.pytest-tmp/*`, `_reversa_refactor/.pytest-baseline`). A remoção
   exige shell elevado; o comando em lote está na evidência. **Cinco foram criados
   nesta rodada**, um deles dentro de `tests/`, e a coleta da suíte só não aborta
   por causa de um `collect_ignore` em `tests/conftest.py`.
3. **Os três blocos da `D-08`/`D-09` foram integrados numa reescrita só do
   `app.py`**, e a medição de comportamento foi feita **uma vez**, ao fim, com uma
   sonda que atribui divergência por **nome de caso** e não por bloco. Medir antes
   da integração teria sido vazio, porque os casos de uso são aditivos. Está
   declarado nas "Notas de execução" do `actions.md`.
4. **A `D-06` do roadmap está errada em um ponto, e o adendo não a corrige.** Ela
   afirma que o `harness.py` "já consome `carregar_arvore`" e que só sairia uma
   menção textual. Medido: o coletor do **candidato** chamava a casca de fato, com
   parse duplo por fixture. O coletor foi migrado e a paridade remedida (100 %), mas
   **quem ler o roadmap da feature deve saber que aquela linha não descreve o que
   existia**.
5. **O status HTTP de `PessoaNaoEncontrada` é `404`, e `422` para os outros três.**
   O `requirements.md` fixa os dois códigos e **não diz qual é qual**. A escolha é
   do executor e está no docstring de `application/traducao.py`. Nenhuma tela lê
   essa coluna nesta onda (`RN-05`), e há um teste que prova isso.
6. **`Dependencias` continua sendo uma classe concreta do núcleo**, e não uma
   interface da fronteira. Nenhum `Protocol` de `ports/` a substitui nesta onda — é
   limite declarado da decisão de 2026-10-07, e não esquecimento. O contrato entre
   núcleo e fronteira para a leitura de CSV e a emissão de diagrama continua sendo
   a assinatura que a feature 005 estabilizou.
7. **`AnalisadorDeUpload`, nomeado na `D-07`, não existe como classe.** Os dois
   nomes da decisão descrevem a mesma responsabilidade, e a ação fixou um só,
   `ArmazenamentoEmDisco`. Não há componente faltando — mas quem procurar o nome no
   código não vai encontrá-lo.
8. **A verificação manual não deixa resíduo nesta rodada**, porque a pasta de
   upload foi apontada para um diretório descartável em vez de `src/uploads/`.
   `src/uploads/` ficou com as mesmas 32 entradas de antes da feature.

## Fontes

- `_reversa_forward/006-fronteira-aplicacao-ports/legacy-impact.md` (fonte principal do delta)
- `_reversa_forward/006-fronteira-aplicacao-ports/regression-watch.md` (`W005` a `W019`, `OBS-11` a `OBS-20`)
- `_reversa_forward/006-fronteira-aplicacao-ports/requirements.md` (objetivo, `RN-01` a `RN-06`, `RF-01` a `RF-21` e a decisão do alvo da migração)
- `_reversa_forward/006-fronteira-aplicacao-ports/roadmap.md` (`D-01` a `D-12`)
- `_reversa_forward/006-fronteira-aplicacao-ports/actions.md` (31 de 31 ações concluídas, e as Notas de execução)
- `_reversa_forward/006-fronteira-aplicacao-ports/progress.jsonl` (31 eventos)
- `_reversa_forward/006-fronteira-aplicacao-ports/data-delta.md` (sem delta de dados)
- `_reversa_forward/006-fronteira-aplicacao-ports/audit/cross-check.md` (os sete findings que a feature fechou)
- `_reversa_forward/006-fronteira-aplicacao-ports/evidence/README-evidencias.md` (os quatro instrumentos e os defeitos de ambiente)
- `_reversa_forward/006-fronteira-aplicacao-ports/evidence/T021-medicao-bloco-1.md`, `T022-medicao-bloco-2.md`, `T023-medicao-bloco-3.md` (medições)
- `_reversa_forward/006-fronteira-aplicacao-ports/evidence/T025-verificacao-manual.md` (aceite de ponta a ponta)
- `_reversa_sdd/architecture.md`, `_reversa_sdd/domain.md`, `_reversa_sdd/c4-components.md`, `_reversa_sdd/code-analysis.md`, `_reversa_sdd/flowcharts/upload-gedcom.md`, `_reversa_sdd/upload-gedcom/` (conferência de nomes de seção)

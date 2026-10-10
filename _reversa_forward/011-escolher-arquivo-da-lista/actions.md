# Actions: Escolher arquivo da lista

> Identificador: `011-escolher-arquivo-da-lista`
> Data: `2026-10-09`
> Roadmap: `_reversa_forward/011-escolher-arquivo-da-lista/roadmap.md`

## Resumo

| Métrica | Valor |
|---------|-------|
| Total de ações | 40 |
| Paralelizáveis (`[//]`) | 24 |
| Maior cadeia de dependência | 12 (`T001 → T005 → T014 → T015 → T016 → T019 → T020 → T021 → T022 → T023 → T031 → T032`) |

> **Três notas de leitura.** (1) Onde a coluna "Arquivo alvo" nomeia `evidence/…`, a ação é de
> **execução e medição**, e o arquivo alvo é a evidência que ela produz — a pasta `evidence/` desta
> feature ainda não existe, e nasce no primeiro passo que escrever nela. (2) A `T032` é do estágio
> `/reversa-sync`, que é quem cria adendos neste projeto; ela fica aqui porque o risco da §9 do
> `roadmap.md` declara a divergência "em `legacy-impact.md` **e no adendo**". (3) A convenção do `[//]`
> está na primeira nota de execução, e ela é mais estreita que a do template.

## Fase 1, Preparação

| ID | Descrição | Dependências | Paralelismo | Arquivo alvo | Confidência | Status |
|----|-----------|--------------|-------------|--------------|-------------|--------|
| T001 | Rodar a suíte completa **antes de qualquer edição** e registrar a contagem obtida, com `DATABASE_URL` ausente do ambiente (a feature 012 mediu `335 passed, 9 skipped`; a contagem de agora é o que vale) | - | `[//]` | `_reversa_forward/011-escolher-arquivo-da-lista/evidence/T001-suite-antes.txt` | 🟢 | [X] |
| T002 | Rodar a paridade pelo invólucro `tests/rodar_paridade.py` **antes de qualquer edição** e registrar o `PARIDADE … %` obtido — é a metade "antes" da premissa de §4 do roadmap | - | `[//]` | `_reversa_forward/011-escolher-arquivo-da-lista/evidence/T002-paridade-antes.txt` | 🟢 | [X] |
| T003 | Levantar o inventário por `sha256` da pasta `src/uploads` — nome, bytes e totais — e conferir que ela está no estado que o plano supõe: **19 arquivos e 29.166.183 bytes** (`RF-08`) | - | `[//]` | `_reversa_forward/011-escolher-arquivo-da-lista/evidence/T003-inventario-antes.txt` | 🟢 | [X] |
| T004 | Registrar o estado do git antes de editar — `git status --porcelain` e o commit de `HEAD` — para que o "núcleo intocado" da `T026` tenha linha de base | - | `[//]` | `_reversa_forward/011-escolher-arquivo-da-lista/evidence/T004-git-antes.txt` | 🟢 | [X] |

## Fase 2, Testes

| ID | Descrição | Dependências | Paralelismo | Arquivo alvo | Confidência | Status |
|----|-----------|--------------|-------------|--------------|-------------|--------|
| T005 | Escrever o teste da função pura sobre nomes **sintéticos**, cobrindo os quatro casos de agrupamento medidos — com chave, com **chave vazada** no nome visível, sem chave, e dois arquivos com a mesma chave — mais os casos de **partição por extensão** (`.ged`, `.csv` e um nome de outra extensão, que não entra em aba nenhuma), provando o agrupamento, a contagem do grupo, a marca de sem chave, a ordem por data decrescente a extensão que decide a aba, e o **alcance por referência** de cada item — nome com acento e nome sem chave marcados como **indisponíveis** com o motivo, e o nome ASCII com chave marcado como disponível (`RN-01`, `RN-02`, `RN-03`, `RN-10`, `RN-11`, `D-09`, `D-10`, `D-11`) | T001 | `[//]` | `tests/test_lista_de_arquivos.py` | 🟢 | [X] |
| T006 | Escrever o teste de `listar()` pela porta: sobre pasta temporária povoada devolve nome armazenado, bytes e data; sobre pasta **ausente** devolve lista vazia em vez de exceção (`D-01`, `D-07`) | T001 | `[//]` | `tests/test_porta_de_armazenamento.py` | 🟢 | [X] |
| T007 | Escrever o teste de rota do `GET /` **sem envio prévio**: responde `200` e entrega as duas listas, com um item por conteúdo (`RF-06`) | T001 | `[//]` | `tests/test_lista_na_tela.py` | 🟢 | [X] |
| T008 | Escrever o teste de rota do **estado vazio**: sem arquivo do tipo na pasta, a aba orienta o envio e a resposta continua `200` (`RF-07`, `D-07`) | T007 | - | `tests/test_lista_na_tela.py` | 🟢 | [X] |
| T009 | Escrever o teste de rota da **referência do CSV**: com `matches_csv_filename` a análise conclui sem arquivo, a referência **vence** o arquivo quando os dois vêm, e o envio só com `matches_csv` continua concluindo como hoje (`RF-04`, `RN-04`, `D-03`) | T001 | `[//]` | `tests/test_dna_analysis.py` | 🟢 | [X] |
| T010 | Escrever o teste de rota de **escolher a árvore da lista** e submeter a busca de caminho, sem novo envio de arquivo, mais o **caso negativo**: forçar o uso de um item **indisponível** (nome com acento, ou sem chave) é recusado **com mensagem na tela, sem `500` e sem árvore carregada**, e o arquivo **continua na lista**. **Não fixe o literal** da mensagem — ele é hoje o falso "não existe mais" do defeito `A007` — e **não** monte arquivo sintético de nome ASCII com conteúdo inválido: esse caminho derruba a requisição com `500` (`A008`) e não é o caso real (`RF-02`, `D-08`, `RN-09`, `RN-11`) | T001 | `[//]` | `tests/test_path_search.py` | 🟢 | [X] |
| T011 | Escrever o teste de rota do **envio pela aba**: valida o conteúdo antes de gravar, grava sob chave de conteúdo e o arquivo novo passa a aparecer na lista (`RF-05`) | T001 | `[//]` | `tests/test_upload.py` | 🟢 | [X] |

## Fase 3, Núcleo

| ID | Descrição | Dependências | Paralelismo | Arquivo alvo | Confidência | Status |
|----|-----------|--------------|-------------|--------------|-------------|--------|
| T012 | Declarar `listar(dono)` no `Protocol` `ArmazenamentoDeArquivos`, com o retorno tipado da entrada da lista, e atualizar o docstring do módulo — a tabela de portas passa de 2 para 3 métodos e a frase final "Nenhum metodo novo foi criado em nenhuma porta" deixa de valer (`D-01`) | T006 | `[//]` | `src/ports/__init__.py` | 🟢 | [X] |
| T013 | Implementar `listar(dono)` em `ArmazenamentoEmDisco`, lendo **só** o nome do diretório e os atributos do arquivo — sem abrir conteúdo nenhum e sem filtrar nada — e devolvendo lista vazia quando a pasta não existe (RNF de desempenho, `D-01`, `D-07`, `D-08`) | T012 | - | `src/ports/adaptadores.py` | 🟢 | [X] |
| T014 | Acrescentar a `src/utils/validate.py` a decomposição do nome armazenado em `(chave, nome visível)`, **reusando** `_FORMATO_CHAVE` em vez de escrever um segundo padrão para a mesma regra (`D-02`) | T005 | `[//]` | `src/utils/validate.py` | 🟢 | [X] |
| T015 | Escrever a função pura de apresentação em `src/reporting/lista_de_arquivos.py`: **seleciona pela extensão do nome visível** (`RN-03`, `D-10`), agrupa pela chave, marca o arquivo sem chave como item próprio, calcula contagem e tamanho, **decide o alcance de cada item com `chave_recebida_e_valida` — a mesma função que o resolvedor aplica — e deriva o motivo quando o item não é alcançável**, e ordena por data decrescente (`RN-01`, `RN-02`, `RN-03`, `RN-10`, `RN-11`, `D-10`, `D-11`, RNF de desempenho) | T014 | - | `src/reporting/lista_de_arquivos.py` | 🟢 | [X] |
| T016 | Aplicar na mesma função a regra do **nome exibido sem chave vazada** quando o grupo tem nomes visíveis diferentes — o caso medido da chave `080e7943572d2652` (`D-09`) | T015 | - | `src/reporting/lista_de_arquivos.py` | 🟢 | [X] |

## Fase 4, Integração

| ID | Descrição | Dependências | Paralelismo | Arquivo alvo | Confidência | Status |
|----|-----------|--------------|-------------|--------------|-------------|--------|
| T017 | O `GET /` monta as duas listas a partir da porta e as entrega ao template no contexto — sem `os.listdir` na rota e sem remover nenhuma variável de contexto existente (`D-01`, `D-04`, `RF-06`) | T015 | `[//]` | `src/app.py` | 🟢 | [X] |
| T018 | O ramo `dna_analysis` passa a aceitar `matches_csv_filename`, com a referência tendo **precedência** sobre o arquivo e o caminho antigo intocado quando ela não vem (`D-03`, `RN-04`, `RF-04`) | T017, T009 | - | `src/app.py` | 🟢 | [X] |
| T019 | O ramo `{% if not gedcom_filename %}` deixa de ser formulário de envio e passa a renderizar as duas abas com as listas, com o envio movido para dentro de cada aba (`D-04`, `RF-06`) | T007, T010, T011, T016 | `[//]` | `src/templates/index.html` | 🟢 | [X] |
| T020 | Cada item das duas listas exibe nome visível, tamanho, data e a contagem do grupo; o item sem chave traz a marca de que é anterior à chave por conteúdo, e o item **não alcançável por referência** traz a marca de **indisponível**, com o motivo, sem que a escolha seja oferecida como se fosse funcionar (`RN-02`, `RN-10`, `RN-11`, `RF-09`, `D-09`, `D-11`) | T019 | - | `src/templates/index.html` | 🟢 | [X] |
| T021 | A aba de DNA ganha o campo de escolha que preenche `matches_csv_filename`, mantendo o envio de arquivo como a outra via de entrada (`RN-04`, `D-03`) | T020 | - | `src/templates/index.html` | 🟢 | [X] |
| T022 | O estado vazio de cada aba orienta o envio de um arquivo e não falha (`RF-07`, `D-07`) | T008, T021 | - | `src/templates/index.html` | 🟢 | [X] |

## Fase 5, Polimento

| ID | Descrição | Dependências | Paralelismo | Arquivo alvo | Confidência | Status |
|----|-----------|--------------|-------------|--------------|-------------|--------|
| T023 | Rodar a suíte **depois** e registrar a contagem, comparando com a linha de base da `T001` — é a metade "depois" que sustenta "não houve regressão" | T018, T022 | `[//]` | `_reversa_forward/011-escolher-arquivo-da-lista/evidence/T023-suite-depois.txt` | 🟢 | [X] |
| T024 | Rodar a paridade pelo invólucro **depois** da mudança de template e registrar o resultado, que tem de ser `PARIDADE 100 %` (premissa de §4 e risco de §9 do roadmap) | T018, T022 | `[//]` | `_reversa_forward/011-escolher-arquivo-da-lista/evidence/T024-paridade-depois.txt` | 🟢 | [X] |
| T025 | Levantar o inventário por `sha256` **depois** de percorrer as duas abas e o envio, e comparar com o da `T003`: idêntico (`RF-08`) | T018, T022 | `[//]` | `_reversa_forward/011-escolher-arquivo-da-lista/evidence/T025-inventario-depois.txt` | 🟢 | [X] |
| T026 | Provar que o núcleo não foi tocado: `git diff -- src/core src/parsers src/application` **vazio**, contra o estado registrado na `T004` | T018, T022 | `[//]` | `_reversa_forward/011-escolher-arquivo-da-lista/evidence/T026-nucleo-intocado.txt` | 🟢 | [X] |
| T027 | Provar que o golden `SCR-001` **não** foi alterado, pelo `git status` de `_reversa_sdd/screens/golden/` e pelo `sha256` do arquivo — é a execução do `D-05` | T018, T022 | `[//]` | `_reversa_forward/011-escolher-arquivo-da-lista/evidence/T027-golden-intocado.txt` | 🟢 | [X] |
| T028 | Atualizar o `README.md`: a tela de entrada descrita deixa de existir, e as listas das duas abas entram no lugar dela (RNF de documentação) | T018, T022 | `[//]` | `README.md` | 🟢 | [ ] |
| T029 | Escrever o `legacy-impact.md` registrando que a aplicação atual deixa de ter o estado inicial do legado, e o que isso significa para o pipeline de migração que ancorou cenários em `SCR-001` (`D-06`) | T018, T022 | `[//]` | `_reversa_forward/011-escolher-arquivo-da-lista/legacy-impact.md` | 🟢 | [X] |
| T030 | Escrever o `regression-watch.md` com os itens de vigilância, o que cada um vigia e o sintoma que o dispara | T018, T022 | `[//]` | `_reversa_forward/011-escolher-arquivo-da-lista/regression-watch.md` | 🟢 | [X] |
| T031 | Revisar o `onboarding.md` desta feature e preencher a tabela de resultados medidos com o que cada passo efetivamente produziu | T023, T024, T025, T027 | - | `_reversa_forward/011-escolher-arquivo-da-lista/onboarding.md` | 🟢 | [X] |
| T032 | Escrever o adendo `_reversa_sdd/addenda/011-escolher-arquivo-da-lista.md`: o campo opcional novo do contrato, a **pré-condição 🟢 de `_reversa_sdd/domain.md` §4 como `regra-alterada`**, a tela nova das duas abas e a divergência declarada. **Estágio `/reversa-sync`** (`D-06`) | T029, T030, T031 | - | `_reversa_sdd/addenda/011-escolher-arquivo-da-lista.md` | 🟢 | [X] |
| T033 | Formatar o rótulo da lista: tirar a **última extensão** e trocar os **símbolos por espaço**, sem tocar na partição por aba nem na referência enviada ao formulário (`RN-13`) | T016 | `[//]` | `src/reporting/lista_de_arquivos.py` | 🟢 | [X] |
| T034 | Botão verde **"Abrir"** e botão vermelho **"Apagar"** em cada item; "Apagar" **aposenta** (move para `<pasta>/_aposentados/`, não apaga), com **confirmação** que cita o arquivo, e ganha `aposentar` na porta de armazenamento, validação de nome simples e ramo de rota (`RN-14`) | T016, T018, T019 | `[//]` | `src/ports/adaptadores.py`, `src/app.py`, `src/templates/index.html` | 🟢 | [X] |
| T035 | A lista vira **tabela com colunas** ("Nome", "Situacao", "Arquivos", "Tamanho", "Enviado em", "Gerenciar"), com o visto verde do disponivel e o motivo escrito do indisponivel. A coluna "Numero" da tela de referencia NAO existe: a aplicacao nao tem identificador publico de arvore, e a chave de conteudo nao pode ocupar esse lugar (`D-09`) | T019 | - | `src/templates/index.html` | 🟢 | [X] |
| T036 | O titulo em texto do topo vira a **arte enviada pelo operador**: rota `GET /banner.png` servindo uma renderizacao DERIVADA (a fonte veio em `RGB` com o quadriculado de transparencia gravado), e o `<h1>` passa a envolver a imagem com o texto no `alt` (`RN-16`) | T019 | - | `src/app.py`, `src/templates/index.html`, `src/assets/banner-da-tela.png` | 🟢 | [X] |
| T037 | O reenvio passa a ter **tres desfechos distintos**: identico avisa "ja estava armazenado", mesmo nome com conteudo diferente **substitui** (aposentando a versao anterior) e nome novo mantem o literal congelado (`RN-17`) | T011, T034 | - | `src/application/upload_gedcom.py` | 🟢 | [X] |
| T038 | A regra do reenvio (`RN-17`) passa a valer tambem para o **CSV**, que entra pelo formulario de analise: a decisao e EXTRAIDA para `application/reenvio.py`, para nao haver duas verdades sobre a mesma regra, e o aviso da substituicao acompanha a mensagem do resultado sem substitui-la | T037 | - | `src/application/reenvio.py`, `src/app.py` | 🟢 | [X] |
| T039 | A mensagem de conteudo recusado vira **uma frase fixa** ("Arquivo não reconhecido como GEDCOM. Favor, enviar o arquivo correto."), sem o motivo tecnico dentro; o motivo continua na excecao (`RN-18`) | T014 | - | `src/application/traducao.py` | 🟢 | [X] |
| T040 | A tela da arvore escolhida ganha o **caminho de volta** (`<a href="/">`, um GET) e passa a dizer **qual arvore esta aberta**, pelo nome visivel, sem a chave (`RN-19`) | T019 | - | `src/templates/index.html`, `src/app.py` | 🟢 | [X] |

## Notas de execução

- **Convenção do `[//]`, mais estreita que a do template.** Ele marca a ação que roda em paralelo com as
  demais `[//]` **da mesma fase**: sem dependência entre si e sem arquivo alvo compartilhado. Depender da
  linha de base (`T001`–`T004`) não desmarca — a linha de base é um portão único, e tratá-la como
  bloqueio de paralelismo faria todas as 28 ações seguintes perderem a marca sem que isso descrevesse
  nada real.
- **A suíte roda com `DATABASE_URL` ausente.** Medido na feature 012: com a variável no ambiente, dois
  testes de `tests/test_persistencia_desabilitada.py` falham e a contagem vira
  `325 passed, 2 failed, 9 skipped`. Não é regressão desta feature, e a `T023` seria lida errado se a
  variável estivesse no ambiente.
- **`listar(dono)` — decidido aqui, não no roadmap.** O `D-01` escreve `listar()` sem assinatura. A
  doutrina declarada no docstring do `src/ports/__init__.py` diz que `dono` é **obrigatório e último** em
  toda porta, e o motivo registrado lá é literalmente o custo de "acrescentá-lo depois", reabrindo toda
  assinatura e todos os chamadores. Aplicada ao método novo, a assinatura é `listar(self, dono)`, e a
  `T006` acrescenta uma linha na tabela de `TestContratoDoArmazenamento` (`test_porta_de_armazenamento.py:463-471`)
  para `listar`, que passa a exigir a mesma forma no contrato e no adaptador. **Se o executor discordar
  desta leitura, o certo é reabrir a decisão, não contornar o teste.**
- **`src/ports/__init__.py` muda de TEXTO, e o texto era uma afirmação de escopo.** A frase final do
  docstring — "Nenhum metodo novo foi criado em nenhuma porta." — e a tabela de portas (que declara 2
  métodos para `ArmazenamentoDeArquivos`) deixam de ser verdade com o `listar`. Varredura feita: nenhum
  teste prende essas frases, então a correção é de documentação. Ela é obrigatória mesmo assim — um
  docstring que afirma o contrário do código é pior que nenhum, e é o tipo de resíduo que o
  `/reversa-audit` cobra depois.
- **`adaptadores.__all__` NÃO muda.** `listar` é método, e a lista literal de
  `tests/test_porta_de_armazenamento.py:321-324` prende **classes** (`ArmazenamentoEmDisco`,
  `CarregadorDeArvoresGedcom`, `RegistroDeAnalisesPostgres`). Nenhum nome novo entra ali, e o quarto
  nome continua sendo motivo para reabrir a `D-03` da feature 006 — esta feature não é exceção.
- **`src/utils/validate.py` é tocado, e o critério de pronto não o protege.** O `git diff` exigido é
  `-- src/core src/parsers src/application`; `src/utils/` fica de fora de propósito, porque a
  decomposição do nome pertence ao módulo que já é dono da forma do nome (`D-02`). Varredura feita:
  nenhum teste afirma o conjunto de funções de `validate`, então o acréscimo é aditivo.
- **As fixtures de teste da lista são sintéticas.** É o Princípio I levado ao teste: o inventário real da
  pasta (19 nomes de arquivo de dados genealógicos reais do operador) **não** entra em teste nenhum. Os
  quatro casos da `T005` são construídos com nomes inventados, e o que se copia deles é a **forma**
  (com chave, chave vazada, sem chave, chave repetida), não o conteúdo.
- **A `T027` mede um golden que a feature não deve tocar — e é a prova do `D-05`.** Se o `sha256` do
  `SCR-001` mudar, a leitura de que o golden captura o oráculo legado congelado estava errada, a premissa
  cai e o instrumento de paridade de tela precisa ser reaberto. Falhar aqui é sinal, não ruído.
- **O alcance de um item é decidido por `chave_recebida_e_valida`, nunca por um teste novo (`D-11`).**
  É a **mesma** função que `ArmazenamentoEmDisco.resolver` aplica (`adaptadores.py:93`). Escrever um
  segundo teste de alcance — mesmo "equivalente" — cria a possibilidade de a marca da tela dizer
  "disponível" e o resolvedor recusar, que é exatamente o defeito que a `D-11` existe para não repetir.
- **O defeito de raiz NÃO é desta feature.** O gravador preserva acento no nome visível
  (`validate.py:40-65`) e o resolvedor recusa acento (`validate.py:32`); é isso que torna 3 dos 6 itens
  inalcançáveis, e consertar isso mexe na defesa contra escape de caminho. Fica registrado como **bug
  próprio** (`A007` da auditoria), fora das 32 ações. A `011` **marca** o item: não esconde, não
  conserta e não promete que ele volta a funcionar.
- **A `T018` e a `T019` são ramos paralelos, e a `T023` espera os dois.** A `T018` mexe na rota e a
  `T019` no template; a suíte e a paridade só fazem sentido depois de ambas, por isso a Fase 5 depende de
  `T018` **e** `T022`, e não só da última ação da fase anterior.

## Histórico de alterações

| Data | Alteração | Autor |
|------|-----------|-------|
| 2026-10-09 | Versão inicial gerada por `/reversa-to-do` | reversa |
| 2026-10-09 | Correção vinda do `/reversa-audit`: `RN-03`/`D-10` citados em `T005` e `T015` (`A001`); `D-08` citado em `T013` e o caso negativo entrou na `T010` (`A002`); `domain.md` §4 declarado na `T032` (`A003`) | reversa |
| 2026-10-09 | Correção vinda do `/reversa-audit` (`A007`, `CRITICAL`): `T005`, `T015` e `T020` passam a cobrir o **item indisponível** (`RN-11`, `RF-09`, `D-11`). Nenhum ID novo, nenhuma dependência nova — as contagens do resumo seguem 32 / 22 / 12 | reversa |
| 2026-10-10 | `T040` acrescentada por **pergunta do operador** ("como voltar para a tela inicial?"). Total 39 → 40. Medido antes de decidir: a tela de busca tinha ZERO `<a href>` e nao dizia qual arvore estava aberta. Escolhido LINK e nao `action`, para nao passar pelo despacho da rota | reversa |
| 2026-10-10 | `T039` acrescentada por **pedido do operador**: mensagem unica para conteudo recusado (`RN-18`). Total 38 → 39. Custo DECLARADO: as tres recusas (vazio, byte nulo, sem cabecalho) passam a ter o mesmo texto, e o operador perde a pista de qual foi; o motivo continua dentro da excecao | reversa |
| 2026-10-10 | `T038` acrescentada por **pedido do operador**: a `RN-17` vale tambem para o CSV. Total 37 → 38; paralelizáveis seguem 24. A regra foi EXTRAÍDA para `application/reenvio.py` em vez de copiada para o ramo da rota: copiar criaria duas verdades sobre a mesma decisão | reversa |
| 2026-10-10 | `T037` acrescentada por **pedido do operador**: avisar no reenvio identico e substituir a versao anterior quando o conteudo muda. Total 36 → 37; paralelizáveis seguem 24. O teste de SEGURANÇA `test_dois_envios_de_mesmo_nome_nao_se_perdem` (Critério 4 do `BUG-20260929-QMLY`) passou a buscar de forma **recursiva**: o critério é "o conteúdo não se perde", e a versão anterior agora fica em `_aposentados/` — a asserção exigindo os DOIS conteúdos no disco não foi afrouxada | reversa |
| 2026-10-10 | `T036` acrescentada por **pedido do operador**: o titulo do topo vira a arte que ele enviou. Total 35 → 36; paralelizáveis seguem 24, porque a ação escreve o MESMO `index.html` da `T019` e por isso **não** é `[//]`. O `SHA_DA_TELA` de `test_icone_de_atalho.py` foi atualizado de `e18d1749…` (25.825 bytes) para `c1048cef…` (26.007), porque o `<h1>` aparece nos dois ramos da tela | reversa |
| 2026-10-10 | `T035` acrescentada por **pedido do operador**: a lista vira tabela com colunas. Total 34 → 35. Parâmetros seguem 24: a `T035` **não** é `[//]`, porque escreve o MESMO `src/templates/index.html` da `T019` e a convenção proíbe duas `[//]` no mesmo arquivo alvo — corrigido depois de o verificador acusar a colisão. A tela vazia fica **byte a byte igual**, porque a tabela vive dentro do ramo da lista — o `SHA_DA_TELA` de `test_icone_de_atalho.py` não precisou de atualização, e isso foi verificado | reversa |
| 2026-10-10 | `T034` acrescentada por **pedido do operador**: botão verde "Abrir" e botão vermelho "Apagar", com `aposentar` na porta de armazenamento (`RN-14`). Total 33 → 34 e paralelizáveis 23 → 24. A aplicação passa a MOVER arquivo, o que nenhum caminho do código fazia; a `RN-07` (nunca apagar) ganhou teste próprio | reversa |
| 2026-10-10 | `T033` acrescentada por **pedido do operador**: o rótulo da lista passa a sair sem a última extensão e sem os símbolos (`RN-13`). Total 32 → 33 e paralelizáveis 22 → 23 (a ação é `[//]`, e depende só da `T016`); a maior cadeia não muda, porque a `T033` é folha | reversa |

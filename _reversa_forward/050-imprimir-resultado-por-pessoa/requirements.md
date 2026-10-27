# Requirements: impressão do resultado por pessoa

> Identificador: `050-imprimir-resultado-por-pessoa`
> Data: `2026-10-26`
> Pasta da extração reversa: `_reversa_sdd/`
> Confidência: 🟢 CONFIRMADO, 🟡 INFERIDO, 🔴 LACUNA / DÚVIDA

## 1. Resumo executivo

A análise de DNA só existe enquanto a resposta está na tela: 68 cartões num documento único, entregues
por um `POST` que reparseia a árvore e não deixa nada gravado no servidor. O operador lê, mas não
consegue tirar dali a conexão de uma pessoa.

Esta feature acrescenta, em cada cartão "Análise de conexão com ...", o comando de **imprimir aquela
pessoa**: o cartão inteiro — as cinco seções, os blocos que a tela nasce recolhida e o diagrama do
caminho — num documento que se sustenta sozinho, com a identificação da análise e a numeração de
folha.

Nenhuma rota, `action`, dependência ou gravação nova: o papel — ou o PDF escolhido no diálogo do
navegador — sai do documento que já chegou ao navegador, e a análise não é recalculada. O problema
que resolve: a conexão deixa de depender da tela acesa para ser conferida, anotada ou levada a uma
reunião. O registro é o cartão inteiro, e o diagrama do caminho ganha folha própria no fim do
documento. Fica fora desta versão, por decisão de 2026-10-26: imprimir a **lista inteira**, uma
pessoa por folha.

## 2. Contexto a partir do legado

| Fonte | Trecho relevante | Confidência |
|-------|------------------|-------------|
| `_reversa_sdd/architecture.md#1` | **Análise sob demanda**: a cada `POST` a árvore é obtida da referência e viaja como argumento até o fim da requisição; não há estado de domínio no processo. O resultado existe na resposta e em nenhum outro lugar | 🟢 |
| `_reversa_sdd/architecture.md#3` | A tela é **um** template (`src/templates/index.html`) e a folha de estilo é servida por `GET /app.css`; não há rota de JavaScript de aplicação | 🟢 |
| `_reversa_sdd/domain.md#2.1` | Os **quatro estados** do confronto: o cartão exibe o que o núcleo decidiu, não recalcula nada | 🟢 |
| `_reversa_sdd/domain.md#3.9` | Ordem de apresentação: documental primeiro, cM decrescente. O código declara que **não é ordem de confiança** | 🟢 |
| `_reversa_sdd/domain.md#5` | **29 literais** de mensagem ao usuário, dos quais **7** são provados por golden file: texto de tela é contrato | 🟢 |
| `_reversa_sdd/analise-dna/contracts.md#6.1` | O **item de resultado** que a tela consome: `match_name`, `csv_name`, `cm`, `text_path`, `mermaid_data`, as quatro seções, `observations`, `warnings` | 🟢 |
| `_reversa_sdd/analise-dna/contracts.md#6.2` | Os **descartes** são bloco da análise, não do cartão — e não entram no documento de uma pessoa | 🟢 |
| `_reversa_sdd/analise-dna/requirements.md#apresentação` | `BR-D-41` a `BR-D-43`, `BR-D-65` e `BR-D-66`: ordem, mensagem final, observações deduplicadas e **diagrama só com caminho documental** | 🟢 |
| `_reversa_sdd/addenda/036-refino-do-cartao-de-resultado.md` | O cartão em **três faixas**; nenhum texto visível mudou; a árvore `details → summary → card-header → h5` é contrato (`W002`) e não recebe `div` no cabeçalho | 🟢 |
| `_reversa_sdd/addenda/018-cartao-de-resultado-recolhivel.md` | O cartão nasce **fechado** e "nada sai do documento": o recolhimento é visual, não remove conteúdo | 🟢 |
| `_reversa_sdd/addenda/019-a-tabela-do-indice-saiu.md` | Sem a tabela do índice, o cabeçalho do cartão é a lista de resumos: nome, cM, parentesco, janela de vida, profundidade e vereditos | 🟢 |
| `_reversa_sdd/addenda/046-paginacao-dos-resultados.md` | A paginação é **camada de apresentação**: os cartões continuam no HTML e o script marca `hidden`; cada `POST` reexecuta a análise (**12 a 31 s** no arquivo real) | 🟢 |
| `_reversa_sdd/addenda/035-lista-de-trabalho-dos-descartes.md` | Precedente de "levar para fora": o CSV dos descartes sai por uma rota própria montada a partir do campo oculto que **já está no HTML**, sem reexecutar a análise | 🟢 |
| `_reversa_sdd/addenda/049-sistema-de-log.md` | A auditoria cobre **ações de servidor** (envio, reenvio, aposentar, análise, busca); imprimir não é uma delas | 🟢 |
| `_reversa_sdd/parity/harness.py#L191` | O harness de paridade **substitui o render por captura de contexto**: ele observa o domínio, não o HTML | 🟢 |
| `.reversa/principles.md#i` | Dado real de terceiros nunca entra no versionamento — nem em fixture, **golden file, captura de tela**, log ou documentação | 🟢 |
| `.reversa/principles.md#ii` | Comportamento observável é preservado em refatoração; mudança de comportamento percorre o fluxo de requisito | 🟢 |
| `.reversa/principles.md#iii` | Nenhuma mudança sem teste que a cubra | 🟢 |
| `tests/test_icone_de_atalho.py#L189` | `SHA_DA_TELA` é invariante mantido **à mão** (46.477 bytes, `5fc0b929…`): um script novo muda a tela vazia e a troca tem de ser declarada no próprio arquivo | 🟢 |
| `_reversa_sdd/screens/golden/manifest.yaml` | As 8 telas literais são **estados vazios**; o cartão de resultado não é uma delas | 🟢 |

> **Glossário mínimo deste documento:** **cM** (centimorgan, a unidade de DNA compartilhado que o
> relatório traz), **CSV** (a lista de matches do teste de DNA), **cartão** (o bloco de uma conexão na
> tela) e **folha** (a página impressa). "Documento" é o conteúdo; "folha" é o papel.

## 3. Personas e cenários de uso

| Persona | Objetivo | Cenário-chave |
|---------|----------|---------------|
| Operador do analisador | Levar uma conexão para fora do computador | Imprime a conexão de uma pessoa e leva a folha para conferir com o registro de cartório ou com o arquivo da família |
| Operador, sem terminal | Guardar uma conexão para depois | Escolhe "Salvar como PDF" no diálogo do navegador e arquiva o documento de uma pessoa, com a identificação da análise |
| Operador que estuda a lista | Comparar poucas conexões lado a lado | Imprime três conexões, uma por folha, e as põe na mesa — cada folha se identifica sozinha |
| Quem reimplementa o sistema | Saber que imprimir não é endpoint | Lê que não há rota, `action`, parâmetro, dependência nem gravação nova |

## 4. Regras de negócio novas ou alteradas

1. **RN-01 — Um documento, uma pessoa.** O comando imprime o cartão daquela conexão e só ele; nenhum
   outro cartão, nenhum bloco da análise (descartes, observações do arquivo) e nenhuma parte da
   tela entram no documento. 🟢
   - Origem no legado: `_reversa_sdd/analise-dna/contracts.md#6.1` (o item de resultado é o cartão) e
     `#6.2` (os descartes são da análise)
   - Tipo: nova

2. **RN-02 — A folha se sustenta sem a tela.** O documento carrega a identificação da análise — a
   árvore, o CSV usado, a raiz analisada e o momento da impressão — e um rodapé com a origem da
   análise em toda folha. Sem isso, duas folhas impressas em dias diferentes não se distinguem. 🟡
   (ajustada em 2026-10-26: a posição da folha saiu, porque o documento não numera páginas)
   - Origem no legado: `_reversa_sdd/addenda/036-refino-do-cartao-de-resultado.md` (o cartão foi
     desenhado para ser lido dentro da página, que dá o contexto); os três primeiros campos já
     existem no template do resultado (`gedcom_filename`, `csv_filename_usado`, `root_name_usado`)
   - Tipo: nova

3. **RN-03 — O documento é o cartão inteiro, inclusive o que nasce recolhido.** O recolhimento é
   recurso de leitura em tela, não ocultação: a tabela de evidências por salto, os homônimos, os
   ancestrais comuns, os caminhos adicionais, a árvore sugerida e o diagrama saem na folha. Duas
   pessoas que imprimem a mesma conexão têm de obter o mesmo conteúdo e os mesmos valores; o único
   campo que varia é o momento da impressão. 🟢
   - Origem no legado: `_reversa_sdd/addenda/018-cartao-de-resultado-recolhivel.md` ("nada sai do
     documento") e `_reversa_sdd/addenda/046-paginacao-dos-resultados.md` (os cartões continuam no
     HTML)
   - Tipo: nova

4. **RN-04 — Controle de tela não vira conteúdo de papel.** Botões, seletor de tamanho de página,
   números de página, o "Voltar", o indicador de abrir/fechar, links e avisos de interface não saem na
   folha; o que é ação não é registro. 🟢
   - Origem no legado: `_reversa_sdd/addenda/046-paginacao-dos-resultados.md` (o controle de paginação
     é apresentação) e `_reversa_sdd/addenda/036-refino-do-cartao-de-resultado.md` (o "Voltar" e o
     chevron são navegação)
   - Tipo: nova

5. **RN-05 — Imprimir não produz resultado novo.** Nada do resultado é recalculado, reinterpretado ou
   completado: o documento mostra o cartão que a análise produziu, com os mesmos números, os mesmos
   vereditos e a mesma ordem da lista. A **diagramação** do documento pode mudar pela `RN-07` — o
   desenho vai para o fim —, e nenhum valor ou posição de resultado muda por causa disso. 🟢
   - Origem no legado: `_reversa_sdd/analise-dna/requirements.md#apresentação` (`BR-D-75`: a projeção
     é pura e não recalcula cM)
   - Tipo: nova

6. **RN-06 — Nenhum dado pessoal novo, e nada gravado.** O documento não acrescenta e-mail,
   identificador de kit ou nome que a tela já não mostre; nada é enviado ao servidor, nada é gravado
   em disco e nenhum artefato da impressão (PDF, captura, HTML) entra no repositório. 🟢
   - Origem no legado: `.reversa/principles.md#i` e `_reversa_sdd/addenda/049-sistema-de-log.md`
     (a identificação de arquivo na auditoria é a chave de conteúdo; aqui o documento é do operador e
     não é persistido — a divergência é declarada em `RN-08`)
   - Tipo: nova

7. **RN-07 — O desenho tem folha própria, e só existe com caminho.** Quando a conexão tem caminho
   documental, o diagrama é impresso numa folha própria, no fim do documento, depois de todas as
   seções: ele não interrompe a leitura nem é cortado no meio de uma tabela. Quando não há caminho
   (`BR-D-66`), não há desenho e nenhuma folha é reservada — a folha mostra o caminho textual e o
   aviso que a tela mostra. 🟢 (decidido em 2026-10-26)
   - Origem no legado: `_reversa_sdd/analise-dna/requirements.md#apresentação` (`BR-D-66`)
   - Tipo: nova

8. **RN-08 — A impressão não deixa rastro no servidor.** Não há requisição, então não há linha de
   auditoria da feature 049 para o ato de imprimir. É consequência declarada da escolha de imprimir
   no navegador, e não esquecimento: o ato de imprimir é do operador, sobre um documento que já estava
   na tela. 🟡
   - Origem no legado: `_reversa_sdd/addenda/049-sistema-de-log.md` (`RN-04`: só ações de servidor
     são auditáveis)
   - Tipo: nova

9. **RN-09 — A tela não muda.** Nenhum literal existente, contagem, ordem, selo ou cartão é alterado;
   o controle de impressão é **aditivo**. O que a tela mostra hoje continua byte a byte, exceto o
   trecho de script que a impressão acrescentar — e essa troca é declarada no invariante de tela. 🟢
   - Origem no legado: `.reversa/principles.md#ii` e `_reversa_sdd/domain.md#5` (texto de tela é
     contrato; 7 literais presos por golden)
   - Tipo: nova — **não é refactor**: a feature acrescenta comportamento observável, e por isso
     percorre o fluxo de requisito em vez de se apresentar como mudança de estrutura

## 5. Requisitos Funcionais

| ID | Requisito | Prioridade | Critério de aceite | Confidência |
|----|-----------|------------|--------------------|-------------|
| RF-01 | Cada cartão de resultado tem um comando de impressão no cabeçalho, ao lado do "Voltar", visível com o cartão fechado e sem abrir nem fechar o cartão ao ser acionado | Must | O HTML de uma análise com conexões traz, por cartão, um botão no cabeçalho cujo nome acessível identifica a pessoa daquele cartão; acioná-lo não muda o estado aberto/fechado | 🟢 |
| RF-02 | Acionar o comando abre o diálogo de impressão do navegador com o documento daquela pessoa e de mais ninguém | Must | O documento contém o título "Análise de conexão com <nome>" e não contém o cartão de nenhuma outra pessoa da mesma análise | 🟢 |
| RF-03 | O documento contém o cartão inteiro, com as cinco seções e os blocos recolhidos expandidos | Must | Uma conexão com tabela de evidências fechada na tela sai impressa com a tabela; o mesmo vale para homônimos, ancestrais comuns, caminhos adicionais e árvore sugerida | 🟢 |
| RF-04 | O documento carrega a identificação da análise e um rodapé com a origem em toda folha | Must | A primeira página identifica a árvore, o CSV e a raiz analisada; todas as páginas trazem a origem. A numeração de página, quando aparecer, é a do diálogo do navegador — o documento não a produz | 🟢 |
| RF-05 | O diagrama do caminho, quando existe, é impresso em folha própria no fim do documento; sem caminho, o texto do caminho ocupa o lugar e nenhuma folha é reservada | Must | Com caminho documental, o desenho abre uma folha própria depois das seções; sem caminho, há o texto e nenhum quadro vazio | 🟢 |
| RF-06 | Os controles de tela não saem na folha | Must | O documento não contém botões (inclusive o próprio comando de impressão), seletor de página, números de página, "Voltar" nem indicador de abrir/fechar | 🟢 |
| RF-07 | A impressão não altera o estado da tela | Must | Depois de imprimir ou de cancelar o diálogo, o cartão volta a fechado/aberto como estava e a página corrente da lista não muda | 🟡 |
| RF-08 | A impressão não faz requisição ao servidor e não reexecuta a análise | Must | Nenhuma requisição nova é observada durante a impressão, e nenhum resultado muda | 🟢 |
| RF-09 | O comando é operável por teclado e anunciado por leitor de tela, sem depender de hover nem de cor | Must | O controle recebe foco pela ordem de tabulação, tem nome acessível e acioná-lo não abre nem fecha o cartão | 🟢 |
| RF-10 | A marcação do documento nasce no HTML servido, e não no navegador | Must | Um teste que lê a resposta do `POST` encontra o comando e o cabeçalho de identificação sem executar script | 🟢 |
| RF-11 | Nenhum texto, contagem, ordem ou cartão existente muda | Must | O cartão renderizado mantém os literais e a estrutura que os testes atuais prendem; a tela de entrada vazia só muda no script declarado, com o invariante atualizado no mesmo commit | 🟢 |

## 6. Requisitos Não Funcionais

| Tipo | Requisito | Evidência ou justificativa | Confidência |
|------|-----------|----------------------------|-------------|
| Papel | O documento é legível em preto e branco: nenhum estado depende **só** de cor, porque os selos já carregam texto e os avisos são frases | `_reversa_sdd/addenda/036-refino-do-cartao-de-resultado.md` (contrastes de 5,56:1 a 10,87:1 no claro) | 🟡 |
| Independência externa | Sem internet, o essencial (texto, tabelas, caminho) continua legível; o desenho é o único elemento que pode faltar, e faltar não pode virar quadro vazio | O projeto já declara degradação por CDN na fonte e nas artes (`src/templates/index.html#L96-L104`) | 🟡 |
| Prontidão | O diálogo não abre antes de o documento estar pronto: o desenho pendente não pode ser capturado em branco | `_reversa_sdd/addenda/046-paginacao-dos-resultados.md` (a ordem "revelar antes de abrir" é contrato, pelo mesmo motivo) | 🟡 |
| Desempenho | Zero requisição e zero reexecução do núcleo; a análise custa 12 a 31 s e imprimir não pode pagar isso de novo | `_reversa_sdd/addenda/046-paginacao-dos-resultados.md` | 🟢 |
| Privacidade | Nada é gravado no servidor, no repositório, em golden ou em fixture; o documento impresso é do operador e não vira artefato do projeto | `.reversa/principles.md#i` e `_reversa_sdd/addenda/049-sistema-de-log.md` | 🟢 |
| Testabilidade | O teste mede **documento e folha de estilo**, nunca aparência executada: a marcação nasce no HTML e as regras de impressão são presas por par template ↔ folha | `tests/test_paginacao_na_tela.py#L17` ("testa markup renderizado e não executa JavaScript") | 🟢 |
| Paridade | A mudança é de template e folha; o harness compara contexto, não HTML, então nenhuma fixture de paridade deve mudar | `_reversa_sdd/parity/harness.py#L191` | 🟢 |
| Compatibilidade | O operador usa mais de um navegador (resposta de 2026-10-26); a folha tem de sair no último Chrome, Edge, Firefox e Safari de desktop, e o diálogo é o do sistema, não um componente próprio | Sessão de 2026-10-26; as versões mínimas exatas e a verificação cruzada ficam para o plano | 🟢 |
| Observabilidade | Nenhuma linha de log nova: imprimir não é evento de servidor, e a feature 049 não ganha ação de auditoria para isso | `_reversa_sdd/addenda/049-sistema-de-log.md` | 🟡 |
| Tamanho | Se a identificação nascer no HTML de cada cartão, são até 68 cabeçalhos por análise, num documento que já mede ≈ 3,9 MB; o acréscimo tem de ser medido no plano | `_reversa_sdd/addenda/046-paginacao-dos-resultados.md` | 🟡 |
| Acessibilidade | O comando tem nome acessível, entra na ordem de foco e não sequestra o cabeçalho do cartão | `_reversa_sdd/addenda/037-redesenho-das-tres-fases.md` (ARIA própria do combobox, mesmo princípio) | 🟢 |
| Suíte | O último marco registrado é 1.686 passam / 9 pulados, sem falha; a entrega acrescenta testes e não ajusta teste existente para passar, e o número é medido de novo no plano | `_reversa_sdd/addenda/049-sistema-de-log.md`, atualização de 2026-10-26 | 🟡 |

## 7. Critérios de Aceitação

```gherkin
Cenário: Imprimir uma conexão isola uma pessoa
  Dado uma análise com várias conexões
  Quando o operador aciona o comando de impressão do cartão de uma pessoa
  Então o documento começa pelo título "Análise de conexão com" e o nome daquela pessoa
  E o documento não contém o cartão de nenhuma outra pessoa da mesma análise

Cenário: O comando fica no cabeçalho do cartão
  Dado um cartão de resultado fechado
  Quando o operador olha o cabeçalho
  Então o comando de impressão está visível ao lado do "Voltar"
  E acioná-lo não abre nem fecha o cartão

Cenário: O documento é o cartão inteiro
  Dado um cartão cuja tabela de evidências por salto está recolhida na tela
  Quando a conexão é impressa
  Então a tabela de evidências está no documento
  E os blocos de homônimos, ancestrais comuns, caminhos adicionais e árvore sugerida também

Cenário: A folha se identifica
  Dado que o operador escolheu uma conexão
  Quando a conexão é impressa
  Então a primeira página identifica a árvore, o CSV e a raiz analisada
  E todas as páginas trazem a origem
  E nenhuma numeração de página é produzida pelo documento

Cenário: O desenho tem folha própria
  Dado uma conexão com caminho documental
  Quando a conexão é impressa
  Então o diagrama do caminho aparece numa folha própria, no fim do documento
  E nenhuma seção ou tabela é dividida por ele

Cenário: Sem caminho documental, o documento não inventa desenho
  Dado uma conexão sem caminho documental
  Quando a conexão é impressa
  Então a folha traz o texto do caminho e o aviso que a tela mostra
  E não há quadro de diagrama vazio nem espaço reservado

Cenário: A tela não vai para o papel
  Dado uma análise paginada de 10 em 10
  Quando uma conexão é impressa
  Então o documento não contém o formulário, a barra das fases, o controle de paginação, o "Voltar", o indicador de abrir/fechar nem o próprio comando de impressão

Cenário: A tela volta ao que era
  Dado o cartão fechado e a lista na página 2
  Quando o operador imprime e fecha o diálogo, com ou sem imprimir
  Então o cartão continua fechado
  E a lista continua na página 2

Cenário: Imprimir não chama o servidor
  Dado uma análise exibida na tela
  Quando o operador aciona o comando de impressão
  Então nenhuma requisição nova é feita
  E a análise não é recalculada nem recarregada

Cenário: O comando é alcançável sem mouse
  Dado que o operador navega por teclado
  Quando o foco chega ao comando do cartão
  Então o controle anuncia a pessoa daquela conexão
  E acioná-lo não abre nem fecha o cartão

Cenário: Sem resultado, não há o que imprimir
  Dado a tela de entrada sem análise executada
  Quando a página é servida
  Então não existe comando de impressão em lugar nenhum
  E o HTML da tela vazia difere do anterior apenas no script declarado, com o invariante de tela atualizado

Cenário: A marcação nasce no servidor
  Dado que a suíte não executa script
  Quando o teste lê a resposta da análise
  Então o comando e o cabeçalho de identificação já estão no HTML
```

## 8. Prioridade MoSCoW

| Item | MoSCoW | Justificativa |
|------|--------|---------------|
| RF-01, RF-02 | Must | É o pedido: um comando por pessoa que imprima aquela pessoa |
| RF-03 | Must | Imprimir um cartão pela metade é pior que não imprimir: a folha não diz que está incompleta |
| RF-04 | Must | Sem identificação, a folha não se sustenta fora da tela e duas impressões não se distinguem |
| RF-06 | Must | Botão impresso em papel é ruído que o operador não pode corrigir depois |
| RF-07 | Must | Uma impressão que deixa a tela mudada cobra do operador o preço de uma ação que não pediu |
| RF-08 | Must | Reexecutar a análise custa 12 a 31 s e não devolve nada que o documento já não tenha |
| RF-09 | Must | O operador já navega por teclado; um controle só de mouse exclui quem usa leitor de tela |
| RF-10, RF-11 | Must | Princípio III: sem teste que prenda marcação e folha, a feature não é verificável |
| RF-05 | Must | O operador escolheu folha própria para o desenho em 2026-10-26; sem ela, o caminho textual sozinho perde o que se leva para a mesa |
| RNF de papel e legibilidade | Should | O operador pode imprimir em colorida; preto e branco é o caso comum |
| RNF de tamanho | Could | O acréscimo de bytes é medido e aceitável se ficar na ordem de dezenas de KB |
| Imprimir a lista inteira, uma pessoa por folha | Fora do escopo | Decidido em 2026-10-26: esta feature entrega o comando do cartão; a lista inteira, se voltar, entra como feature própria |

## 9. Esclarecimentos

### Sessão 2026-10-26

- **Q:** A impressão é de uma pessoa por vez, ou a lista inteira também?
  **R:** **Só o comando do cartão, uma pessoa por vez.** Imprimir todas as conexões, uma por folha,
  fica fora desta feature: com 68 conexões medidas, a lista inteira teria de revelar o que a
  paginação esconde e mudaria a natureza do documento. Se voltar, entra como feature própria.

- **Q:** O que sai na folha?
  **R:** **O registro completo do cartão** — as cinco seções, os blocos recolhidos expandidos e o
  diagrama —, tipicamente de três a oito folhas por pessoa. A ficha resumida de uma folha fica para
  depois, se fizer falta.

- **Q:** O diagrama do caminho entra no papel?
  **R:** **Entra, em folha própria no fim do documento**, depois de todas as seções, para não
  interromper a leitura nem ser dividido no meio de uma tabela. Sem caminho documental não há desenho
  nem folha reservada.

- **Q:** Onde fica o comando de imprimir?
  **R:** **No cabeçalho do cartão, ao lado do "Voltar"**, visível com o cartão fechado. Acioná-lo não
  pode abrir nem fechar o cartão — o cabeçalho inteiro é o alvo do recolhimento, e o comando é um
  controle dentro dele.

- **Q:** Qual navegador o operador usa?
  **R:** **Mais de um.** A folha tem de sair no último Chrome, Edge, Firefox e Safari de desktop; as
  versões mínimas e a verificação cruzada são decisão da fase de plano.

### Sessão 2026-10-26, segunda rodada (fechamento da auditoria)

- **Q:** O `RF-04` pedia "página N de M", e o plano provou que o documento não consegue numerar folhas.
  **R:** **A numeração sai do requisito.** Fica "a identificação no topo e a origem em toda folha"; a
  numeração, quando aparecer, é a do diálogo do navegador. O `RF-04` foi reescrito e passou a 🟢.

- **Q:** O critério do `RF-02` diz "não contém o nome de nenhuma outra pessoa", mas o cartão imprime
  nomes no caminho, na tabela de evidências e nos homônimos.
  **R:** **O critério passa a falar do cartão**, como o cenário já dizia: o documento não contém o
  **cartão** de nenhuma outra pessoa. Nomes de terceiros no caminho e nas evidências são conteúdo
  daquela conexão, não de outra.

- **Q:** A `RN-02` pede o momento da impressão e a `RN-03` exige o mesmo documento para duas
  impressões.
  **R:** **O carimbo fica, e a `RN-03` passa a exigir o mesmo conteúdo e os mesmos valores** — o
  momento da impressão é o único campo que varia entre duas folhas da mesma conexão.

- **Q:** A `RN-05` diz que imprimir não reordena, e a `RN-07` manda o desenho para o fim do documento.
  **R:** **A `RN-05` distingue resultado de diagramação:** nenhum valor ou posição de resultado muda; a
  diagramação pode mudar pela `RN-07`.

## 10. Lacunas

Nenhuma dúvida de produto em aberto. As três que existiam — lote, extensão do documento e diagrama —
foram resolvidas na sessão de 2026-10-26 e estão registradas em §9; as decisões correspondentes
viraram `RN-03`, `RN-07`, `RF-01` e `RF-05`.

**Pontos técnicos, de verificação na fase de plano:**

- 🟡 **A análise não tem data.** A `RN-02` pede o momento da impressão, e a resposta do `POST` não
  carrega instante nenhum. **Resolvido no plano:** o `<time>` é preenchido no navegador no ato de
  imprimir, o teste prende o lugar e não o valor, e a `RN-03` foi ajustada em 2026-10-26 para admitir
  essa variação.

- 🟡 **Versões mínimas de navegador.** O operador usa mais de um (resposta de 2026-10-26), mas o
  projeto não declara versão nenhuma. Fixar o mínimo — último Chrome, Edge, Firefox e Safari de
  desktop — e a verificação cruzada é decisão do plano; o diálogo, as margens e a quebra de página
  variam entre eles.

- 🟡 **Custo de bytes.** Se a identificação da `RN-02` nascer no HTML de cada cartão, são até 68
  cabeçalhos por análise (≈ 3,9 MB de HTML já medidos). A alternativa — montar a identificação na hora
  de imprimir — é mais barata e invisível para a suíte, que não executa script.

- 🟡 **O "não alternar" do cartão é comportamento de script.** A suíte não executa JavaScript: o teste
  prende que o controle é um botão dentro do cabeçalho e que a marcação não ganhou `div` nova (`W002`
  da 036), mas o efeito de o clique não recolher o cartão só se verifica em navegador. Registrar como
  cobertura parcial, como a 030 fez com o binário `dot`.

- 🟡 **Quebra de página controlada.** A folha própria do diagrama e a proibição de dividir tabelas
  dependem de regras de impressão que variam entre navegadores; a verificação é manual, e o documento
  não pode depender dela para ficar correto.

- 🟡 **Colisão com os invariantes de tela.** O controle entra dentro do cabeçalho do cartão, que a
  feature 036 prende sem `div` nova (`W002`); e o script novo muda a tela vazia, o que exige a
  declaração do `SHA_DA_TELA` no mesmo commit. Nenhum dos dois é bloqueio, mas os dois são obrigação
  de teste.

- 🟡 **A impressão não é auditada** (`RN-08`). Quem precisa de prova de que uma folha com dado pessoal
  saiu do sistema não a terá: o evento não chega ao servidor. É aceitável enquanto o documento for do
  operador, e deixa de ser se a impressão virar entrega a terceiros.

- 🟡 **A árvore de trabalho tem mudanças não commitadas** anteriores a esta feature (o ajuste do
  diagrama de parentesco de 2026-10-26, que já moveu o `SHA_DA_TELA`). O plano parte do estado medido
  na árvore, não do `HEAD`, e a suíte precisa ser medida de novo antes de fixar o marco.

## 11. Histórico de alterações

| Data | Alteração | Autor |
|------|-----------|-------|
| 2026-10-26 | Versão inicial gerada por `/reversa-requirements` a partir do pedido "imprimir o resultado de 'Análise de conexão com ...' para cada pessoa" | reversa |
| 2026-10-26 | Sessão de esclarecimentos: 5 respostas integradas (`RN-03`, `RN-07`, `RF-01`, `RF-05`, RNF de compatibilidade); as três dúvidas zeradas | reversa |
| 2026-10-26 | Segunda sessão (fechamento da auditoria): `RF-04` sem numeração de página, critério do `RF-02` corrigido, `RN-03` e `RN-05` ajustadas e `RN-02` sem posição de folha | reversa |

## Emendas

### E001, 2026-10-27

O que muda: ao salvar a impressão em PDF, o nome sugerido do arquivo passa a ser "Análise de conexão
com <nome da pessoa>", e não o título fixo da página.
Motivo: hoje qualquer pessoa imprime com o mesmo nome ("Analisador de Conexões Genealógicas.pdf"), e o
operador precisa renomear o arquivo à mão depois de salvar. O nome é a primeira identificação da
folha, e ele não dizia de quem era.
Arquivos previstos: `src/templates/index.html` (script da impressão) e
`tests/test_impressao_do_resultado.py`.

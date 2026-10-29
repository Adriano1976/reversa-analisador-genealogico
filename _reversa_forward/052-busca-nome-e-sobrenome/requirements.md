# Requirements: busca por nome e sobrenome em GEDCOM e CSV

> Identificador: `052-busca-nome-e-sobrenome`
> Data: `2026-10-28`
> Pasta da extração reversa: `_reversa_sdd/`
> Confidência: 🟢 CONFIRMADO, 🟡 INFERIDO, 🔴 LACUNA / DÚVIDA

## 1. Resumo executivo

O sistema cruza árvore genealógica e relatório de DNA, mas **não tem busca**: para achar uma pessoa é preciso já saber o nome que está no arquivo. O único auxílio é um combobox embutido que só existe depois de uma árvore aberta, não abre ao digitar, mostra os primeiros 50 nomes na ordem da árvore e não alcança o CSV. Esta feature entrega **um campo de busca por nome ou por sobrenome — um termo, duas fontes** — que devolve a ficha da pessoa na árvore e a linha do match no relatório de DNA, com ordem determinística e servida pelo servidor. Ela é também o substituto que o `P-03` exige para que a lista completa de nomes pare de viajar em toda resposta.

## 2. Contexto a partir do legado

| Fonte | Trecho relevante | Confidência |
|-------|------------------|-------------|
| `_reversa_sdd/permissions.md#4.3` | Até 2026-10-26 a autenticação estava fora de cobertura e **a lista completa de nomes ia no HTML**; a chave de conteúdo fazia o papel de sessão | 🟢 |
| `_reversa_sdd/permissions.md#6` | `P-03` **decidida em 2026-10-05**: a exposição de `all_names` deve ser restringida, e a restrição exige **busca no servidor** (Onda 4) | 🟢 |
| `_reversa_sdd/gaps.md#6` | Requisito nº 3 encaminhado ao alvo: "restringir a exposição da lista completa de nomes"; removê-la hoje quebraria a busca sem substituto | 🟢 |
| `_reversa_sdd/domain.md#3.6` | As duas listas entram em **toda** renderização por processador de contexto; a rota tem 23 `render_template`, 12 deles passam `gedcom_filename` | 🟢 |
| `_reversa_sdd/domain.md#5` | Texto de tela é **contrato**: 29 literais catalogados, dos quais golden e paridade dependem | 🟢 |
| `_reversa_sdd/domain.md#3.4` | O matching difuso de nomes é decisão de domínio; o cM **não** decide aceitação | 🟢 |
| `_reversa_sdd/domain.md#3.9` | A ordem de apresentação é decisão deliberada, declarada como "não é ordem de confiança" | 🟢 |
| `_reversa_sdd/architecture.md#1` | Monolito de um processo; a borda valida entrada, despacha por `action` e escolhe o render pelo desfecho | 🟢 |
| `_reversa_sdd/architecture.md#3` | A tela é um template (`index.html`); as portas são a fronteira que a Onda 3 estende | 🟢 |
| `_reversa_sdd/code-analysis.md#5.7` | `L-24` (colisão da chave do cache de nomes), `L-25` (ordem sensível a `PYTHONHASHSEED`) e `get_children` sem índice | 🟢 |
| `_reversa_sdd/addenda/037-redesenho-das-tres-fases.md` | Três fases; o combobox de nomes tem teto de **50**, filtro sem acento, teclado e ARIA próprios, e o texto digitado continua livre | 🟢 |
| `_reversa_sdd/addenda/048-indice-de-nomes-sem-colisao.md` | O índice de nomes deixou de ser estado de módulo e passou a ser **preso ao grafo da árvore**; sem estado compartilhado não há colisão | 🟢 |
| `_reversa_sdd/addenda/051-login-google-e-isolamento.md` | O `dono` virou escopo efetivo; recurso de outro dono responde como inexistente; a lista de nomes continua no HTML, agora só para quem está autenticado | 🟢 |
| `src/templates/index.html#L601` | `all_names` viaja como bloco `application/json` `#nomes-da-arvore`, **só** com árvore aberta | 🟢 |
| `src/templates/index.html#L665-L669` | O filtro do combobox é `indexOf` sobre o nome completo normalizado **no cliente** | 🟢 |
| `src/templates/index.html#L714-L721` | A lista abre no `↓` e no foco de um campo que já tem texto; o `input` só refiltra se a lista já está aberta | 🟢 |
| `tests/test_combobox_de_nomes.py#L11-L15` | O comportamento de abertura **não é preso por teste**; vive em checklist manual (`D-14`), porque não há executor de JS | 🟢 |
| `src/core/homonimos.py#L71-L93` | `_indice_por_nome` varre as pessoas uma vez e prende o mapa ao grafo; a varredura de 35 mil pessoas custa ~0,9 s | 🟢 |
| `src/core/homonimos.py#L96` | `homonym_dossier` devolve as fichas dos homônimos e o sinal de ambiguidade | 🟢 |
| `src/utils/name_keys.py#L25` e `src/core/homonimos.py#L34` | Existem **dois normalizadores**: um remove pontuação e barra, o outro não; ambos baixam caixa e tiram acento | 🟢 |
| `src/core/matching.py` (via `core/name_normalization`) | O `matching` da análise de DNA consome `norm_name`, o normalizador de `utils/` | 🟢 |
| `_reversa_sdd/parity/harness.py#L211-L221` | O harness de paridade compara `success`, `message`, `dna_results`, `skipped_matches` e `gedcom_filename`; **nunca** `all_names` | 🟢 |
| `tests/test_icone_de_atalho.py#L144-L146` | `SHA_DA_TELA` mede `GET /` com pasta de upload vazia, e é atualizado à mão a cada mudança declarada | 🟢 |
| `.reversa/principles.md#i` | Dado real de DNA/GEDCOM nunca entra em repositório, fixture, golden, log ou documentação | 🟢 |
| `.reversa/principles.md#ii` | Comportamento observável é preservado; mudar comportamento é feature, não refactor | 🟢 |
| `.reversa/principles.md#iii` | Nenhuma mudança sem teste que a cubra | 🟢 |

> **Glossário mínimo deste documento.** **Termo** é o texto que o operador digita, preservado como
> escreveu; **token** é uma palavra do nome depois de normalizada (sem acento e em caixa baixa);
> **fonte** é um arquivo aberto sobre o qual a busca roda — a árvore GEDCOM ou o relatório de
> matches; **ficha** é o retrato de uma pessoa da árvore (nome, nascimento, falecimento, pais,
> filhos, xref); **acerto** é um resultado da busca; **índice** é o mapa derivado da árvore que
> torna a busca barata; **escopo** é o recorte por dono herdado da feature 051; **GEDCOM** é o
> formato do arquivo de árvore genealógica; **CSV** é o relatório de matches de DNA exportado pelo
> serviço de testes.

## 3. Personas e cenários de uso

| Persona | Objetivo | Cenário-chave |
|---------|----------|---------------|
| Operador (dono da instalação) | Achar uma pessoa sabendo só o sobrenome | Digita `Silva`, vê as fichas dos Silva da árvore e escolhe uma delas |
| Operador analisando DNA | Saber se um match do relatório existe na árvore | Digita o nome do match, vê a linha com kit e cM e, quando existe, o atalho para a ficha |
| Operador com sessão sem árvore | Entender por que não há busca | A tela explica que a busca roda sobre o que está aberto e aponta a fase 1 |
| Quem reimplementa o sistema | Saber o que é contrato | Lê que a busca é leitura, que não altera resultado de análise e que a ordem é determinística |

## 4. Regras de negócio novas ou alteradas

1. **RN-01 — A busca é leitura.** Nenhuma busca grava, move ou apaga arquivo, e nenhuma busca cria, altera ou completa resultado de análise, histórico ou trilha: a busca **não** entra na trilha de auditoria (decisão de 2026-10-28, §9), e a auditoria passa a ser devida na entrega que retirar o `all_names`. 🟢
   - Origem no legado: `_reversa_sdd/domain.md#3.7` (a persistência fica fora da decisão) e `.reversa/principles.md#ii`
   - Tipo: nova

2. **RN-02 — Um campo, e o modo vem do termo.** O campo aceita nome inteiro ou um único token de prenome/sobrenome; o tratamento é derivado da **contagem de tokens do termo** (1 token casa contra prenome e sobrenome; 2 ou mais exige todos, tolerando ordem e partículas), nunca escolhido em controle separado. 🟡
   - Origem no legado: `_reversa_sdd/addenda/037-redesenho-das-tres-fases.md` ("o texto digitado continua livre")
   - Tipo: nova

3. **RN-03 — A busca é sobre o que está aberto, e nunca cruza donos.** A busca só alcança a árvore e o relatório do dono da sessão; referência de outro dono é tratada como **inexistente**, com a mesma resposta de arquivo que não existe. 🟢
   - Origem no legado: `_reversa_sdd/addenda/051-login-google-e-isolamento.md` e `_reversa_sdd/permissions.md#3`
   - Tipo: herdada da 051

4. **RN-04 — A ordem é determinística.** Dois acertos com a mesma pontuação são desempatados por chave total (nome normalizado e, por último, o identificador da pessoa); a mesma entrada produz a mesma lista na mesma máquina e em qualquer `PYTHONHASHSEED`. 🟢
   - Origem no legado: `_reversa_sdd/code-analysis.md#5.7` (`L-25`) e `_reversa_sdd/domain.md#3.9`
   - Tipo: nova

5. **RN-05 — Cada fonte responde à sua pergunta.** A árvore responde "quem é esta pessoa e como ela se liga"; o relatório de matches responde "este testado está na árvore, com quantos cM". As duas respostas aparecem **separadas e rotuladas**, e o acerto do relatório só se referencia à ficha quando o nome resolve na árvore. 🟢
   - Origem no legado: `_reversa_sdd/domain.md#2` (três eixos que não se contaminam)
   - Tipo: nova

6. **RN-06 — A busca não muda resultado de análise.** Cada fonte normaliza com o normalizador que **já usa** (a unificação dos dois é entrega própria, §9); o ranking da busca não é reaproveitado pelo matching; e o índice é preso à árvore, nunca estado de módulo. 🟢
   - Origem no legado: `_reversa_sdd/addenda/048-indice-de-nomes-sem-colisao.md`, `_reversa_sdd/code-analysis.md#5.7` (`L-24`) e `.reversa/principles.md#ii`
   - Tipo: nova

7. **RN-07 — Limite declarado, total declarado.** Cada seção exibe no máximo **50** acertos e declara o total encontrado; o limite não pode ser silencioso. 🟢
   - Origem no legado: `_reversa_sdd/addenda/037-redesenho-das-tres-fases.md` (teto de 50 do combobox)
   - Tipo: nova

8. **RN-08 — Sem resultado não é erro.** Termo sem acerto produz a mensagem de "não encontrado", preserva o termo digitado e não grava nada; não há resposta de erro nem exceção para o operador. 🟢
   - Origem no legado: `_reversa_sdd/domain.md#5` (mensagens de estado) e `_reversa_sdd/domain.md#5.2`
   - Tipo: nova

9. **RN-09 — O filtro é largo, e a ordem separa o ruído.** O casamento do termo é por trecho em qualquer posição do token, e a pontuação do acerto cresce quando o trecho cai no início do token; nenhum acerto é descartado por posição. 🟢
   - Origem no legado: `_reversa_sdd/addenda/037-redesenho-das-tres-fases.md` (o filtro atual é `indexOf` sobre o nome completo) e a sessão de esclarecimentos de 2026-10-28 (§9)
   - Tipo: nova

## 5. Requisitos Funcionais

| ID | Requisito | Prioridade | Critério de aceite | Confidência |
|----|-----------|------------|--------------------|-------------|
| RF-01 | A tela oferece um campo de busca por nome ou sobrenome, no cabeçalho e acima das fases, visível quando há árvore aberta | Must | Com árvore aberta, o campo aparece com rótulo acessível em `GET /`; sem árvore, a tela explica que a busca roda sobre o que está aberto e aponta a fase 1 | 🟢 |
| RF-02 | A busca na árvore encontra por nome completo, ignorando acento, caixa e pontuação | Must | `José da Silva`, `jose da silva` e `JOSE DA SILVA` produzem o mesmo conjunto de acertos | 🟢 |
| RF-03 | A busca na árvore encontra por um token isolado de prenome **ou** de sobrenome, em qualquer posição do token | Must | `Silva` devolve as pessoas com Silva entre os sobrenomes; `ilva` devolve as mesmas pessoas; e, no mesmo conjunto, quem tem o token iniciado por `Sil` aparece antes de quem apenas o contém | 🟢 |
| RF-04 | A busca no relatório de matches encontra pelo nome do match | Must | `Roberto Souza` devolve a linha do match com o nome do arquivo de origem, o kit e o cM | 🟢 |
| RF-05 | O acerto da árvore traz ficha suficiente para identificar a pessoa | Should | A ficha exibe nome, nascimento, falecimento, pais, filhos e identificador; campo ausente aparece como ausente, nunca inventado | 🟢 |
| RF-06 | O acerto do relatório de matches traz cM e kit, e o arquivo de origem | Should | A linha exibe o cM somado do match e o kit quando ele existe; sem kit, o campo aparece vazio sem alterar o cM | 🟢 |
| RF-07 | O acerto do relatório referencia a ficha quando o nome resolve na árvore | Should | Nome presente na árvore gera o caminho para a ficha; nome ausente não gera caminho e não produz erro | 🟡 |
| RF-08 | A busca só devolve dado do dono da sessão | Must | Com dois donos, a busca de A nunca devolve acerto de B; a referência de B apresentada por A responde como inexistente, nunca como proibida | 🟢 |
| RF-09 | Termo sem acerto informa a ausência e preserva o termo | Must | A resposta diz que não encontrou, o campo mantém o texto digitado e nenhuma linha é gravada | 🟢 |
| RF-10 | O texto digitado é livre; nenhum campo vira seleção obrigatória | Must | É possível buscar por nome parcial e submeter sem escolher acerto; o termo chega ao servidor exatamente como foi escrito | 🟢 |
| RF-11 | A busca não altera resultado de análise | Must | Executar uma análise antes e depois de buscas produz o mesmo veredito, o mesmo número de conexões e os mesmos descartados | 🟢 |
| RF-12 | O número de acertos por seção é limitado e o total é declarado | Should | Com mais de 50 acertos numa seção, a tela mostra 50 e declara o total encontrado | 🟢 |
| RF-13 | Relatório de matches ilegível não derruba a busca: a seção do CSV é omitida e a tela diz o motivo | Should | Com CSV ilegível, a seção do CSV não aparece, a linha de aviso traz o texto acionável e a seção da árvore continua respondendo | 🟢 |

## 6. Requisitos Não Funcionais

| Tipo | Requisito | Evidência ou justificativa | Confidência |
|------|-----------|----------------------------|-------------|
| Desempenho | A segunda busca na **mesma** árvore não reconstrói o índice; a construção acontece uma vez por árvore aberta | `src/core/homonimos.py#L71-L93`: a varredura de 35 mil pessoas custa ~0,9 s, e o mapa é preso ao grafo | 🟢 |
| Desempenho | O custo de uma busca não cresce com o número de buscas anteriores na mesma árvore | Sem estado por consulta, não há acumulação; a memória do índice é a memória da árvore | 🟡 |
| Determinismo | A mesma entrada produz a mesma ordem, em qualquer `PYTHONHASHSEED` | `L-25` em `_reversa_sdd/code-analysis.md#5.7` é a classe de defeito a não repetir | 🟢 |
| Concorrência | Duas buscas simultâneas não compartilham estado mutável, e o índice acompanha a árvore que a requisição usa | `_reversa_sdd/architecture.md#2` (processo multi-thread) e `addenda/048` (o índice é preso ao grafo, não é variável de módulo) | 🟢 |
| Testabilidade | O resultado da busca é entregue por resposta de servidor e verificável na suíte, sem navegador | Hoje o combobox não é preso por teste (`tests/test_combobox_de_nomes.py#L11-L15`, `D-14`) | 🟢 |
| Segurança | A busca nunca devolve nome de outro dono, e a recusa é indistinguível de inexistência | Regra do dono entregue pela 051 (`_reversa_sdd/permissions.md#3` e `addenda/051`) | 🟢 |
| Privacidade | A feature não aumenta o que é persistido: nenhum acerto é gravado, e o dado exibido é o que a árvore já continha | `.reversa/principles.md#i` e `_reversa_sdd/permissions.md#6` (`P-07`) | 🟢 |
| Acessibilidade | O campo tem rótulo associado, foco visível e o resultado é anunciado; a busca funciona sem script no cliente | Os artefatos de acessibilidade do projeto tratam ARIA própria (`addenda/036`, `addenda/037`) | 🟢 |
| Compatibilidade | Os 29 literais de tela catalogados continuam intactos; o texto novo entra no contrato de mensagens | `_reversa_sdd/domain.md#5` | 🟢 |
| Compatibilidade | Se a tela vazia mudar de bytes, `SHA_DA_TELA` é remedido e declarado no mesmo commit | `tests/test_icone_de_atalho.py#L144-L146`; a busca no cabeçalho só aparece com árvore aberta, e por isso não deve tocar o hash | 🟢 |
| Paridade | A entrega não altera o que o harness de paridade observa | `_reversa_sdd/parity/harness.py#L211-L221` lê `success`, `message`, `dna_results`, `skipped_matches` e `gedcom_filename` | 🟢 |
| Arquitetura | A busca é servida por trás de uma porta, com um adaptador por fonte, para que uma terceira fonte não altere o domínio | `_reversa_sdd/architecture.md#3` e os `ADR-25`/`ADR-34` (fronteira de aplicação e ausência de ciclo) | 🟢 |
| Arquitetura | O critério de casamento é substituível e testável isoladamente, e a ordem dos critérios é declaração de negócio | Separação entre decisão de domínio e apresentação, como em `domain.md#3.4` | 🟡 |
| Dependências | Nenhuma dependência obrigatória nova: a ausência de um pacote não pode impedir `import app` | `L-26` (`psycopg2` pinado e ausente do `.venv`, com import preguiçoso); qualquer adoção exige medição antes, não escolha por preferência | 🟢 |
| Suíte | O marco é **1.745 passam / 9 pulados / 4 falham**, e as 4 falhas são pré-existentes; a entrega acrescenta testes e não ajusta teste alheio | `_reversa_sdd/addenda/051-login-google-e-isolamento.md` | 🟢 |
| Fixtures | Toda verificação usa árvore e relatório **sintéticos** | `.reversa/principles.md#i` | 🟢 |

## 7. Critérios de Aceitação

```gherkin
Cenário: Buscar por nome completo na árvore
  Dado que existe uma árvore aberta com a pessoa "José da Silva"
  Quando o operador busca "jose da silva"
  Então o acerto aparece com a ficha da pessoa
  E o identificador da pessoa aparece no acerto

Cenário: Buscar por sobrenome isolado
  Dado que a árvore aberta tem três pessoas com o sobrenome Silva
  Quando o operador busca "Silva"
  Então os três aparecem na seção da árvore
  E a ordem é a mesma em duas buscas seguidas

Cenário: Buscar pelo nome de um match no relatório
  Dado que a árvore está aberta e há um relatório de matches selecionado
  Quando o operador busca um nome que existe no relatório
  Então o acerto aparece na seção do relatório com o kit e o cM
  E o nome do arquivo de origem é exibido

Cenário: O match que também está na árvore
  Dado um nome presente no relatório e na árvore
  Quando o operador busca por esse nome
  Então aparecem as duas seções
  E o acerto do relatório oferece o caminho para a ficha

Cenário: Termo sem nenhum acerto
  Dado que nenhum nome da árvore contém o termo
  Quando o operador busca "Zzzz"
  Então a tela informa que não encontrou
  E o campo mantém o texto digitado
  E nada é gravado

Cenário: A busca não devolve dado de outro dono
  Dado que A tem uma árvore com acertos para o termo
  E B está autenticado com a própria árvore
  Quando B busca pelo termo
  Então nenhum acerto de A aparece
  E nenhum nome de A aparece no corpo da resposta

Cenário: A busca não altera o resultado da análise
  Dado que uma análise de DNA foi executada e o resultado anotado
  Quando o operador faz buscas por nome e repete a análise
  Então o veredito, o número de conexões e os descartados são os mesmos

Cenário: Mais acertos do que o limite
  Dado que o termo casa com mais de 50 pessoas
  Quando a busca é executada
  Então a seção mostra 50 acertos
  E a tela declara o total encontrado

Cenário: Sem árvore, a busca explica o que falta
  Dado que não há árvore aberta
  Quando o operador procura o campo de busca
  Então a tela explica que a busca roda sobre o que está aberto
  E aponta a fase 1

Cenário: O termo é livre e não exige escolher acerto
  Dado que existe árvore aberta
  Quando o operador digita apenas "Mar" e submete sem escolher nenhum acerto
  Então a busca executa com o termo "Mar"
  E nenhum campo exige seleção

Cenário: O relatório de matches não pôde ser lido
  Dado que a árvore está aberta e o relatório selecionado é ilegível
  Quando o operador faz uma busca
  Então a seção da árvore responde normalmente
  E a seção do CSV não aparece
  E a tela diz que o relatório não pôde ser lido
```

## 8. Prioridade MoSCoW

| Item | MoSCoW | Justificativa |
|------|--------|---------------|
| RF-01, RF-02, RF-03 | Must | É o pedido: um campo que encontre por nome e por sobrenome |
| RF-04 | Must | Sem a segunda fonte, "tanto `.csv` quanto `.ged`" não é atendido |
| RF-08 | Must | Busca sem escopo é vazamento do dado que a 051 protegeu |
| RF-11 | Must | A busca não pode custar o resultado que o sistema existe para entregar |
| RF-09, RF-10 | Must | Termo livre e ausência de resultado são o caso comum, não a exceção |
| RF-05, RF-06, RF-07 | Should | A ficha e a referência cruzada são o que diferencia busca de filtro |
| RF-12 | Should | O limite protege a tela; o total declarado evita o limite silencioso |
| RF-13 | Should | A falha de uma fonte não pode custar a resposta da outra |
| Busca por data, local ou identificador | Fora do escopo | O pedido é nome ou sobrenome |
| Busca global entre árvores armazenadas | Fora do escopo | A busca roda sobre o que está aberto; cruzar árvores exige decidir precedência e custo |
| Remover `all_names` do HTML | Fora desta entrega | Decidido em §9 (2026-10-28): a remoção é a entrega seguinte, depois que a busca provar que substitui o autocomplete |
| Auditar a busca na trilha da 049 | Fora desta entrega | Enquanto o `all_names` viaja no HTML, auditar a busca não acrescenta evidência (§9); a auditoria entra junto com a remoção |
| Casamento aproximado (erro de digitação) | Could | Só com medição que justifique; a ausência dele não bloqueia a busca |

## 9. Esclarecimentos

### Sessão 2026-10-28

- **Q:** O `all_names` sai do HTML nesta entrega, ou a busca convive com ele?
  **R:** **Fica nesta entrega.** O `P-03` pede substituto, não remoção: a ordem é provar a busca e só então retirar o bloco. Ficam declaradas três consequências: o payload de nomes continua em toda resposta com árvore aberta; o bloco JSON e seus três testes de segurança permanecem intocados; e a remoção vira entrega própria, com o autocomplete passando a consumir a busca, cujo critério é "o operador preenche os três campos sem o bloco".

- **Q:** A busca deixa linha na trilha de auditoria da feature 049?
  **R:** **Não, e isto decorre da resposta anterior.** A resposta com árvore aberta já entrega a lista completa de nomes no HTML: auditar a busca enquanto a página entrega tudo não acrescenta evidência nenhuma. A auditoria passa a ser devida na entrega que retirar o `all_names`, e aí na forma "sem o termo, com contagem e desfecho" — o termo pode conter nome de pessoa (princípio I e a máscara da 049).

- **Q:** Os dois normalizadores são unificados nesta entrega?
  **R:** **Não.** Unificar muda resultado de análise para nome com apóstrofo, hífen ou barra, o que é mudança de comportamento (princípio II), não refactor. E a busca deve concordar **dentro** de cada fonte — com o dossiê na árvore e com o matching no CSV —, o que a unificação **entre** fontes não garante. A dívida fica registrada e vira entrega própria, com medição de paridade.

- **Q:** O casamento do termo é por prefixo do token ou por trecho em qualquer posição?
  **R:** **Trecho em qualquer posição**, com o prefixo pontuando acima do meio de token. O autocomplete atual já casa por trecho, e adotar só prefixo perderia resultados que o operador obtém hoje sem ninguém ter pedido. Filtro largo, ordenação que separa qualidade de ruído; o custo da varredura é medido na fase de plano.

- **Q:** O relatório de matches selecionado não pôde ser lido — o que a tela faz?
  **R:** **A seção do CSV não aparece, com uma linha dizendo que o relatório não pôde ser lido.** Uma seção vazia seria indistinguível de "não encontrei", que é o que a `RN-08` proíbe confundir; e derrubar a busca inteira tiraria a resposta da árvore, que continua válida. O texto acionável já existe e é reaproveitado.

## 10. Lacunas

### Dúvidas de produto

Nenhuma. As três de 2026-10-28 — destino do `all_names`, auditoria da busca e unificação dos normalizadores — foram decididas na sessão de esclarecimentos (§9), e cada uma virou regra ou restrição de escopo neste documento.

### Pontos técnicos, de verificação na fase de plano

- 🟡 **Ordem do nome no CSV.** `split_name_pt` assume prenome primeiro; export de teste costuma vir `SILVA, MARIA`. O adaptador reordena ou o termo aceita as duas ordens?
- 🟡 **Sobrenome composto e partícula.** "Silva e Souza", "dos Santos": conjunto de tokens ou trecho contíguo? Muda o ranking e o teste.
- 🟡 **Posição do campo.** O declarado é o cabeçalho acima das fases, renderizado sob a mesma condição dos demais campos (árvore aberta), o que mantém `SHA_DA_TELA` intacto. A alternativa — barra sempre visível — custa a remedição declarada do hash.
- 🟡 **A busca roda sem relatório selecionado?** A seção do CSV só pode existir quando há relatório na sessão; a ausência dela precisa ser dita, e não confundida com "nada encontrado" (a `RF-13` cobre o caso do relatório ilegível, não o do relatório não escolhido).
- 🟡 **Terceira fonte.** A porta precisa acomodar a árvore (em memória, com índice) e o relatório (tabela lida por arquivo) sem que o caso de uso conheça a diferença — a verificação é no plano, com a assinatura da porta.
- 🟡 **Custo da construção do índice com a segunda visão.** A visão por token é construída na mesma varredura; medir o acréscimo sobre os ~0,9 s medidos, em vez de supor.
- 🟡 **Custo da varredura por trecho.** O casamento em qualquer posição é linear no dicionário de tokens; medir com a árvore real e registrar o número, para que a `RN-09` não vire suposição.
- 🟡 **Uma resposta por busca ou uma rota com estado?** A página tem 23 `render_template` (`domain.md#3.6`); a escolha entre devolver a tela inteira e devolver a área de resultado afeta os 12 pontos que passam `gedcom_filename`.

## 11. Histórico de alterações

| Data | Alteração | Autor |
|------|-----------|-------|
| 2026-10-28 | Versão inicial gerada por `/reversa-requirements` a partir do pedido de busca por nome/sobrenome sobre `.ged` e `.csv`, ancorada no `P-03` e nos adendos 037, 048 e 051 | reversa |
| 2026-10-28 | Sessão de esclarecimentos `/reversa-clarify`: as três dúvidas de produto resolvidas e duas perguntas de comportamento e falha respondidas; entram RN-09, RF-13 e um cenário; marcadores zerados | reversa |

# Interface: formulário HTTP de `POST /` e a tela de `GET /`

> Identificador da feature: `011-escolher-arquivo-da-lista`
> Data: `2026-10-09`
> Contrato de origem: `_reversa_sdd/openapi/index.yaml:62-180`, `_reversa_sdd/upload-gedcom/contracts.md#1`,
> `_reversa_sdd/analise-dna/contracts.md#1`
> Tipo: **HTTP (formulário)** — a rota é única e o despacho é pelo campo `action`

Este é o único contrato externo que a feature toca. Ele muda em **um** ponto do `POST` (campo novo e
opcional no ramo `dna_analysis`) e no que o `GET /` renderiza. **Nenhuma `action` é criada, renomeada ou
removida, e nenhum campo existente desaparece** (`RN-08`).

## 1. `GET /` — a tela

| Aspecto | Antes | Depois |
|---------|-------|--------|
| Estado sem `gedcom_filename` | Formulário de envio de GEDCOM, e **nada mais** — a única forma de ver as abas era enviar um arquivo | As **duas abas** com as listas de arquivos armazenados, cada uma com o seu próprio envio |
| Estado com `gedcom_filename` | As duas abas com os formulários | As duas abas com as listas, a árvore escolhida marcada, e os formulários |
| Status | `200` | `200` (inalterado) |
| Variáveis de contexto | `gedcom_filename`, `all_names`, … | **acrescenta** as listas; nenhuma variável existente é removida |

> **A variável de contexto nova é invisível para o instrumento de paridade.** O `harness.py:191`
> intercepta `render_template` e o `:211-221` lê chaves **nomeadas** (`success`, `message`,
> `dna_results`, `skipped_matches`, `gedcom_filename`). Acrescentar chave não muda nenhuma delas, e o
> harness **não** faz `GET /`.

### 1.1 O que a lista mostra

| Coluna | Origem | Observação |
|--------|--------|------------|
| Nome visível | a parte depois do separador `__` no nome armazenado | é o que o operador reconhece |
| Tamanho e data | atributos do arquivo, lidos pela porta | **não** é conteúdo: a listagem não lê byte de arquivo |
| Contagem | quantos arquivos compartilham aquele conteúdo | presente só quando é mais de um |
| Marca de "sem chave" | ausência da chave de 16 hexadecimais no início do nome | arquivo anterior à chave por conteúdo (`RN-10`) |
| Marca de "**indisponível**" | o nome armazenado **não passa** na forma fechada de `utils/validate.py:32`, a mesma que o resolvedor aplica | arquivo que a referência **não alcança** — nome visível com acento, ou sem chave (`RN-11`, `D-11`). O item **continua na lista**, com o motivo, e a escolha não é oferecida como se fosse funcionar |

## 2. `POST /` com `action=dna_analysis`

### 2.1 Antes

| Campo | Local | Obrigatório |
|-------|-------|-------------|
| `action` | `form` | sim — literal `dna_analysis` |
| `gedcom_filename` | `form` | sim — chave de conteúdo da árvore |
| `root_name` | `form` | sim |
| `matches_csv` | **`files`** | **sim** |

### 2.2 Depois

| Campo | Local | Obrigatório | Mudança |
|-------|-------|-------------|---------|
| `action` | `form` | sim | — |
| `gedcom_filename` | `form` | sim | — |
| `root_name` | `form` | sim | — |
| `matches_csv` | `files` | **condicional** | deixa de ser obrigatório **quando** a referência vem |
| `matches_csv_filename` | `form` | **novo, opcional** | o **nome armazenado** do CSV escolhido na lista |

**Regra de precedência:** quando `matches_csv_filename` vem preenchido, ele é a fonte do CSV e o
arquivo é ignorado; quando não vem, o comportamento é **exatamente o de hoje**. Um pedido sem nenhum
dos dois é erro de formulário, com a mesma mensagem atual de arquivo ausente.

### 2.3 Por que campo novo, e não reaproveitar `matches_csv`

1. **Dois `input` com o mesmo nome no mesmo formulário se atropelam.** A aba de DNA tem, ao mesmo
   tempo, a lista de escolha e o envio de arquivo; se ambos se chamassem `matches_csv`, o navegador
   enviaria os dois e o servidor teria de adivinhar qual vale.
2. **O campo mudaria de lugar no contrato.** Hoje `matches_csv` está em `files` (`contracts.md#1.1`);
   aceitá-lo também em `form` é mudança de contrato, não acréscimo.
3. **Reaproveitar apagaria a prova.** A paridade e os testes de rota enviam `matches_csv` como arquivo.
   Mantendo o campo e acrescentando outro, o caminho antigo continua exercitado **exatamente** como
   está — a mudança é aditiva, e a paridade de 100 % segue medindo o que media.

## 3. `POST /` com `action=path_search`

**Sem mudança de contrato.** A árvore escolhida na lista preenche o **mesmo** campo oculto
`gedcom_filename` que o formulário já devolvia entre requisições (`upload-gedcom/contracts.md#3`). O
que muda é **como** ele é preenchido — pela lista, em vez de por um envio anterior — e não o campo.

| Campo | Local | Obrigatório | Mudança |
|-------|-------|-------------|---------|
| `action`, `gedcom_filename`, `person1_name`, `person2_name` | `form` | sim | **nenhuma** |

## 4. `POST /` com `action=upload_gedcom`

**Sem mudança de contrato.** O envio se muda de lugar na tela (de uma tela de entrada para dentro da
aba), mas o pedido é o mesmo: `multipart/form-data` com `action=upload_gedcom` e o arquivo em `gedcom`.
A validação de conteúdo antes de gravar e a gravação sob chave de conteúdo ficam intactas.

| Campo | Local | Obrigatório | Mudança |
|-------|-------|-------------|---------|
| `action` | `form` | sim | — |
| `gedcom` | `files` | sim | — |

## 5. Erros e limites

| Situação | Antes | Depois |
|----------|-------|--------|
| Corpo acima de 16 MB | `413` com a mensagem do teto | **igual** — o campo novo é curto e não altera o teto |
| Referência de árvore que não resolve | `200` com `Erro: Arquivo '{ref}' não existe mais.` | **igual** — a mensagem é do caminho de uso, `_arvore_do_formulario()` |
| Referência de CSV que não resolve | não existia (o CSV vinha no corpo) | mesma classe de mensagem do caminho de uso; a tela continua utilizável |
| Arquivo escolhido que a referência **não alcança** (nome visível com acento, ou sem chave) | a referência sempre resolvia, porque o arquivo vinha de um envio validado | **`200` com `Erro: Arquivo '…' não existe mais.`** — mensagem **falsa**, medida contra a pasta real: o arquivo existe. É **defeito de raiz** (`A007` da auditoria), fora do escopo desta feature; aqui o item é exibido **marcado como indisponível**, com o motivo (`RN-11`, `D-11`) |
| Arquivo escolhido cujo **conteúdo** não serve ao uso | `Arquivo não reconhecido como GEDCOM: {motivo}.` | **igual** — é a resposta esperada para o caso `Famílias_Sergipanas.csv.ged` (`RN-09`) **no caminho de envio**; por referência, a validação de conteúdo não roda, e o que decide é o alcance acima |

## 6. Idempotência e estado

Nada muda aqui: a aplicação continua **sem estado entre requisições**. A escolha viaja por campo de
formulário, e nada é lembrado ao fechar a página (`RN-05`, resposta da §9). A lista é derivada do disco
a cada renderização.

## 7. `POST /` com `action=selecionar_arvore` — a escolha da árvore na lista

> **Numerada 7, e colocada no fim, de propósito.** As seções 1 a 6 já existiam e já eram citadas por
> outros artefatos (`§2.2` aqui e na auditoria, `§5` na auditoria). Renumerar as seguintes quebraria
> essas citações, então a seção nova recebe o próximo número livre e vai para o fim do arquivo, onde a
> ordem dos números é a ordem de leitura.

**Quarta `action` do contrato**, acrescentada em 2026-10-09 pela própria feature 011, depois de a
primeira versão da tela ter sido medida no navegador.

| Campo | Local | Obrigatório | Mudança |
|-------|-------|-------------|---------|
| `action` | `form` | sim | **novo** — literal `selecionar_arvore` |
| `gedcom_filename` | `form` | sim | — é o **mesmo** campo oculto que a árvore já usava entre requisições |

**Por que ela existe.** A lista entregava os itens como **texto puro**: sem `select`, sem `radio`, sem
link e sem formulário. O operador via as árvores e **não podia escolher nenhuma** — a tela dizia
"Escolha uma árvore que já está armazenada" e não oferecia como. O `RF-02` exige "escolher a árvore a ser
usada", e isso não estava satisfeito. Medido no navegador, não deduzido.

**Por que não bastava o que já existia.** `path_search` exige `person1_name` e `person2_name`: não serve
para "escolher e ver a tela". E um `action` desconhecido cai no `return render_template("index.html")` do
fim de `index()`, que renderiza **sem** `gedcom_filename` — a árvore resolvida seria descartada e o
clique não faria nada.

**Efeito:** renderiza a tela no estado "árvore escolhida", o **mesmo** que o envio produz. Nada é lido
além do parse que a resolução da referência já faz, e **nada é escrito**.

**Consequência para a `RN-08`:** ela dizia que as **três** `action` mantêm nome e campos. Continuam
mantendo, e agora são **quatro**. Nenhum campo existente mudou por causa desta.

> **Só o item disponível ganha o botão.** Os arquivos que a referência não alcança continuam listados,
> com o motivo, e **não** são oferecidos como se funcionassem (`RN-11`, `D-11`): clicar neles só
> produziria a mensagem falsa de arquivo inexistente.

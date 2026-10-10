# Unit `tela-de-entrada` — Contratos

> Re-extração de **2026-10-10** (nível **Completo**). Unit **nova** — não substitui artefato anterior: nasceu nas features `011` e `012`, e nas três extrações anteriores `GET /` era só um formulário de envio.
> Este arquivo fixa **o que atravessa a fronteira** da unit: o contrato HTTP, o contrato da listagem, o contrato de aposentar, o contrato de escolher a árvore e o contrato de mensagens.
> Escala de confiança: 🟢 CONFIRMADO | 🟡 INFERIDO | 🔴 LACUNA

---

## 1. Contrato HTTP

| Método | Caminho | Entrada | Status | Corpo da resposta |
| --- | --- | --- | --- | --- |
| `GET` | `/` | — | `200` | HTML da tela, **com as duas abas já preenchidas** e sem `gedcom_filename` |
| `POST` | `/` (`action=aposentar_arquivo`) | `form` com `arquivo_a_aposentar` | `200` | HTML com `message` e `success` |
| `POST` | `/` (`action=selecionar_arvore`) | `form` com `gedcom_filename` | `200` | HTML com `gedcom_filename` + `all_names` |

> 🟢 **Não há contrato JSON, `redirect`, `201`, `204`, `400` nem `404`.** Toda recusa **desta unit** é HTML com status `200` e `success=false`. As duas ações são **idempotentes do ponto de vista do transporte**: nenhuma delas responde com redirect, e recarregar a resposta não repete o efeito (o `POST` é reenviado pelo navegador, mas a segunda tentativa de aposentar devolve o fracasso e não move nada).
>
> 🟢 **O `POST /` é multiplexado por `action`.** Esta unit **não** responde sozinha por nenhuma rota exclusiva: ela compartilha `POST /` com `upload_gedcom`, `dna_analysis` e `path_search`. É a mesma rota, o mesmo template e o mesmo par `message`/`success` — muda o ramo.

### 1.1 Contrato da requisição

| Campo | Local | Obrigatório | Forma aceita | Recusa |
| --- | --- | --- | --- | --- |
| `action` | `form` | sim | literal `aposentar_arquivo` ou `selecionar_arvore` | outro valor não entra nestes ramos 🟢 |
| `arquivo_a_aposentar` | `form` | sim, em `aposentar_arquivo` | **nome armazenado** — `<16 hex>__<nome visível>` ou o nome cru de arquivo sem chave | ausente ou inválido → `False` → mensagem de fracasso §5 🟢 |
| `gedcom_filename` | `form` | sim, em `selecionar_arvore` | **nome armazenado** | ausente → `"Erro: Arquivo GEDCOM não encontrado."` 🟢 |

> 🟢 **A entrada das duas ações é o NOME ARMAZENADO, nunca um caminho e nunca um identificador público.** É o mesmo valor que a tela recebe do contexto (`item.nome_armazenado`) e devolve no campo oculto. Não existe identificador de árvore nesta aplicação, e a chave de conteúdo **não** ocupa esse lugar (`D-09`).

### 1.2 Contrato da resposta (variáveis do template)

| Variável | Tipo | Quando vem | Significado |
| --- | --- | --- | --- |
| `arvores_da_lista` | `list[ItemDaLista]` | **em toda** renderização | Itens da aba de árvores (`.ged`) — ver §2 |
| `relatorios_da_lista` | `list[ItemDaLista]` | **em toda** renderização | Itens da aba de relatórios (`.csv`) — ver §2 |
| `gedcom_filename` | `str \| None` | `GET /` **não**; `selecionar_arvore` **sim**; demais ações passam adiante | A referência da árvore aberta 🟢 |
| `all_names` | `list[str]` | junto com `gedcom_filename` | Nomes da árvore, para o `<datalist>` 🟢 |
| `message` | `str` | quando há algo a dizer | Texto ao operador — ver §5 |
| `success` | `bool` | quando há `message` | `True` só nos caminhos de sucesso |

> ⚠️ **As duas primeiras linhas são o contrato que não depende da ação.** Elas vêm do **processador de contexto**, e não da rota: qualquer `render_template("index.html", …)` as recebe, inclusive as renderizações que **não** são desta unit. Um consumidor que renderize `index.html` por conta própria recebe as listas de graça — e é por isso que a unit não publica estado: ela publica **contexto**. 🟢

---

## 2. Contrato da listagem

### 2.1 O que cada item mostra

| Campo do item | Origem | Forma | Observação |
| --- | --- | --- | --- |
| `nome_exibido` | rótulo do grupo (§2.3) | `str` | **Nunca** contém a chave de conteúdo 🟢 |
| `nome_armazenado` | nome do **representante** no disco | `str` | É o valor que o formulário devolve; pode conter a chave 🟢 |
| `chave` | prefixo de 16 hexadecimais, ou `None` | `str \| None` | `None` = arquivo anterior à chave por conteúdo 🟢 |
| `quantidade` | número de arquivos do grupo | `int ≥ 1` | Conta **arquivos**, não versões úteis 🟡 |
| `bytes` | **soma** dos bytes do grupo | `int ≥ 0` | Não é o tamanho do representante 🟢 |
| `modificado_em` | `st_mtime` do representante | `float` | Exibido por filtro `data_br` 🟢 |
| `disponivel` | `pode_ser_usado(nome_armazenado)` | `bool` | Mesma função do resolvedor 🟢 |
| `motivo_indisponivel` | `motivo_de_indisponibilidade(...)` | `str \| None` | `None` quando disponível 🟢 |

> 🟢 `nome_exibido` e `nome_armazenado` **nunca** são a mesma string, e o template usa o primeiro. A chave é assunto do armazenamento; o rótulo existe para que o operador reconheça o arquivo.

### 2.2 Partição das abas e agrupamento

| Regra | Contrato |
| --- | --- |
| Aba | Decidida por `nome_visivel.endswith(".ged")` / `.endswith(".csv")` — extensão do nome **cru** 🟢 |
| Fora das abas | Arquivo cujo nome visível não termina em `.ged` nem `.csv` (ex.: `.xlsx`) **não aparece em aba nenhuma** 🟢 |
| Grupo "com chave" | Chave do grupo = os 16 hexadecimais; dois arquivos de mesma chave = **um** item 🟢 |
| Grupo "sem chave" | Chave do grupo = o **nome armazenado inteiro**; nunca agrupa com outro 🟢 |
| Representante | O de **maior `mtime`** do grupo; define `nome_armazenado`, `modificado_em`, `disponivel` e `motivo_indisponivel` 🟢 |
| Ordem | `mtime` decrescente; empate pelo `nome_exibido` 🟢 |

> 🟢 **`planilha.csv.ged` entra na aba de árvores** e não na de relatórios: quem decide é o nome, e é o `D-08` que decidiu que a listagem **não filtra por conteúdo**. Recusá-lo é papel do **uso**.

### 2.3 Rótulo

| Entrada | Saída | Regra |
| --- | --- | --- |
| `Famílias_Sergipanas.csv` | `Famílias Sergipanas` | Última extensão removida; símbolos → espaço; acentos preservados 🟢 |
| `Backup-Arvore-Sandro-12-11-2024.ged` | `Backup Arvore Sandro 12 11 2024` | Idem 🟢 |
| `planilha.csv.ged` | `planilha csv` | **Só a última** extensão sai: o `.csv` do meio é informação 🟢 |
| `.ged` | `.ged` | Ponto inicial não é extensão — nunca produz rótulo vazio 🟢 |
| `arvore.ged` sem extensão nenhuma | `arvore` | — 🟢 |

> 🟢 **Nenhum rótulo contém `<16 hex>__`.** Quando o grupo tem um visível sem chave, ele é o escolhido; quando **todos** têm chave, a chave é retirada do primeiro em ordem alfabética. Mostrar a chave crua é pior do que mostrar um rótulo sem ela.

### 2.4 Disponibilidade e os dois motivos

| `motivo_indisponivel` | Quando | Literal exato |
| --- | --- | --- |
| `SEM_CHAVE` | o nome não tem os 16 hexadecimais | `sem chave de conteúdo no nome` 🟢 |
| `FORA_DA_FORMA` | tem chave, e a parte visível é recusada como nome | `nome com caractere que a referência não aceita` 🟢 |
| `None` | a referência alcança o arquivo | — 🟢 |

> ⚠️ **`L-30` — o segundo motivo ficou praticamente inalcançável em 2026-10-10.** Ele foi escrito para o acento e o espaço, que a **forma fechada** recusava. A forma fechada foi removida (`RN-20`, `ADR-32`) e a elegibilidade passou a exigir apenas que a parte visível seja um **nome**; acento e espaço agora **passam**. Consequência verificada: `94e2402671702cac__Famílias_Sergipanas.csv` é **disponível**. O ramo do template continua correto e o literal continua no contrato; o que mudou é a probabilidade de ele aparecer. **Requer decisão humana** (ver `tasks.md`, lacuna 1).

---

## 3. Contrato de aposentar

| Propriedade | Contrato |
| --- | --- |
| Efeito | `os.replace` do arquivo para `<pasta de upload>/_aposentados/<nome armazenado>` 🟢 |
| **Nada é apagado** | O arquivo permanece no disco, íntegro e com o mesmo nome; desfazer é mover de volta 🟢 |
| Efeito na lista | O arquivo sai da lista **sem filtro novo**: `listar` ignora subdiretório 🟢 |
| Alcance | Aceita também arquivo **sem chave** — são justamente os inalcançáveis que o operador mais quer tirar da lista 🟢 |
| Contenção (1ª camada) | Recusa `/`, `\`, NUL, `.`, `..`, vazio, e valor que não seja igual ao próprio `basename` 🟢 |
| Contenção (2ª camada) | Recusa quando `dirname(abspath(origem))` não é exatamente a pasta de upload 🟢 |
| Colisão | Sufixo `.1` a `.99`; esgotadas as 99, devolve `False` **sem** mover 🟢 |
| Escreve fora da pasta | **Nunca** 🟢 |
| Depende de árvore | **Não** — é por isso que o ramo vem antes de `_arvore_do_formulario` 🟢 |

> 🟢 **A ordem dos ramos é contrato, não detalhe de implementação.** `_arvore_do_formulario` resolve e **parseia** a árvore escolhida, e a árvore escolhida pode ser exatamente a que se está aposentando. Se a resolução viesse primeiro, o parse falharia **depois** do move e a tela diria "arquivo não existe mais" sobre uma ação que **deu certo**.

---

## 4. Contrato de escolher a árvore

| Etapa | Contrato |
| --- | --- |
| Entrada | `gedcom_filename` = nome armazenado 🟢 |
| Resolução | Pela porta (`chave_recebida_e_valida` + `os.path.exists`), dentro do carregador 🟢 |
| Parse | Ocorre **sempre** nesta ação, porque a árvore é o produto dela 🟢 |
| Saída | `gedcom_filename` + `all_names` — o mesmo par que o envio produz 🟢 |
| Efeito em disco | **Nenhum** 🟢 |
| Referência que não resolve | `Erro: Arquivo 'ROTULO' não existe mais.` — com o **rótulo**, não a chave 🟢 |
| Referência ausente | `Erro: Arquivo GEDCOM não encontrado.` 🟢 |
| Conteúdo ilegível | Mensagem de arquivo ilegível + `app.logger.exception`; **nunca** `500` 🟢 |
| Seleção silenciosa | **Não há**: o operador vê a faixa "Árvore aberta: ROTULO" 🟢 |

> 🟢 **A mensagem usa o rótulo, e não a referência.** Ela é produzida por `rotulo_de_referencia`, a mesma função que formata os nomes da lista, e é o único caminho de mensagem desta unit que não pode vazar a chave.

---

## 5. Contrato de mensagens

Literais **congelados** — consumidos por testes de rota e pelo golden `SCR-G01`/`SCR-G02` do harness de paridade. Não reescrever.

| Situação | Literal | `success` |
| --- | --- | --- |
| Aposentar com êxito | `'{ROTULO}' saiu da lista. O arquivo não foi apagado: ele continua guardado, inteiro, na pasta de aposentados.` | `True` 🟢 |
| Aposentar sem êxito | `Não foi possível aposentar o arquivo: ele não está mais na pasta.` | `False` 🟢 |
| `gedcom_filename` ausente no `POST` | `Erro: Arquivo GEDCOM não encontrado.` | `False` 🟢 |
| Referência não resolve | `Erro: Arquivo '{ROTULO}' não existe mais.` | `False` 🟢 |
| GEDCOM alcançado não parseia | `Erro: o arquivo '{ROTULO}' não pôde ser lido como GEDCOM. Ele pode estar corrompido, vazio, ou não ser um GEDCOM de verdade.` | `False` 🟢 |
| Lista de árvores vazia | `Nenhuma árvore armazenada ainda. Envie uma para começar.` | — (não é `message`) 🟢 |
| Lista de relatórios vazia | `Nenhum relatório de matches armazenado ainda. Ele aparece aqui depois da primeira análise de DNA que usar um arquivo CSV — e para chegar lá é preciso ter uma árvore, que se envia na aba Buscar Conexão no GEDCOM.` | — 🟢 |
| Confirmação do navegador, no botão Apagar | `Apagar "{NOME_EXIBIDO}"? Ele sai da lista e continua guardado no disco, na pasta de aposentados.` | — (JS) 🟢 |

> ⚠️ **A palavra do botão e a palavra da mensagem discordam de propósito.** O botão diz **Apagar** porque é isso que o operador reconhece; a mensagem diz que **não foi apagado** porque é isso que aconteceu. A confirmação do navegador carrega as duas informações na mesma frase, e é o único aviso **antes** do efeito.

---

## 6. Contrato de falha

| Falha | Desfecho | O que **não** acontece |
| --- | --- | --- |
| Pasta de upload ausente | `listar` → `[]`; a tela mostra o estado vazio | Não cria diretório 🟢 |
| Entrada que sumiu entre `listdir` e `stat` | Entrada pulada na listagem | Não levanta 🟢 |
| Data que `datetime.fromtimestamp` não converte | Célula vazia | Não devolve `500` 🟢 |
| Arquivo não é `str`/é vazio em `decompor_nome_armazenado` | `(None, "")` | Não levanta 🟢 |
| `arquivo_a_aposentar` com caminho ou `..` | `False`; mensagem de fracasso | Não move, não escreve fora da pasta 🟢 |
| 100 colisões em `_aposentados/` | `False`; mensagem de fracasso | Não sobrescreve 🟢 |
| GEDCOM ilegível alcançado pela referência | Mensagem em português; traceback no log | Não devolve `500`; não mostra traceback 🟢 |

> 🟢 **A unit tem cinco degradações silenciosas e nenhuma delas é um `500`.** O único caminho de exceção previsto é o do parser, e ele é convertido em mensagem **antes** de sair da rota.

---

## 7. Compatibilidade e versionamento

| Item | Situação |
| --- | --- |
| Substitui artefato anterior | **Não** — unit nova, sem antecessor 🟢 |
| Contrato congelado por | testes de rota (`test_lista_na_tela.py`, `test_tabela_da_tela.py`, `test_aposentar_arquivo.py`) e goldens `SCR-002`/`SCR-G01`/`SCR-G02` 🟢 |
| Cobertura do harness de paridade | **Nenhuma sobre as listas**, por construção: o harness substitui `render_template` e o processador de contexto não roda 🟢 |
| O que quebra consumidores | Mudar os literais de §5, a forma do item de §2.1, ou a **ordem dos ramos** de §3 🟡 |
| O que **não** é contrato | A ordem das abas no HTML, o texto do botão, o `title` das colunas, o `aria-label` 🟡 |
| Dependência a jusante | `analise-dna` e `busca-caminho` consomem o `gedcom_filename` que esta unit entrega 🟢 |

> 🟡 **A ausência de cobertura pelo harness é uma lacuna conhecida do instrumento**, não desta unit: quem a cobre é a suíte, com **132** testes em **8** arquivos. Ver `code-analysis.md` §3.5.

---

*Gerado pelo Reversa-Writer em 2026-10-10 (re-extração). Unit nova.*

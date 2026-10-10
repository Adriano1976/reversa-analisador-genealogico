# Unit `upload-gedcom` — Contratos

> Re-extração de **2026-10-10** (nível **Completo**). Substitui o artefato de 2026-10-05, que fixava o **estado global** como contrato de saída e o **alfabeto fechado** como defesa única.
> Este arquivo fixa **o que atravessa a fronteira** da unit: o contrato HTTP, o contrato em disco, o contrato da árvore, o contrato de reenvio e o contrato de mensagens.
> Escala de confiança: 🟢 CONFIRMADO | 🟡 INFERIDO | 🔴 LACUNA

---

## 1. Contrato HTTP

| Método | Caminho | Entrada | Status | Corpo da resposta |
| --- | --- | --- | --- | --- |
| `GET` | `/` | — | `200` | HTML da tela, com o formulário **e as duas abas de lista** |
| `POST` | `/` (`action=upload_gedcom`) | `multipart/form-data` com o arquivo no campo `gedcom` | `200` | HTML com `message`, `success` e, no sucesso, `gedcom_filename` + `all_names` |
| `POST` | `/` (qualquer `action`) | corpo acima de **16 MB** | **`413`** | HTML com `"Arquivo maior que o limite de 16 MB."` e `success=false` |

> 🟢 **Não há contrato JSON, redirect, `201`, `400` ou `409`.** Toda recusa de **negócio** é HTML com status `200` e `success=false`. A única recusa de **transporte** é o `413`, e ela acontece **antes** de a rota executar.

### 1.1 Contrato da requisição

| Campo | Local | Obrigatório | Forma aceita | Recusa |
| --- | --- | --- | --- | --- |
| `action` | `form` | sim | literal `upload_gedcom` | outro valor não entra neste ramo 🟢 |
| `gedcom` | `files` | sim | arquivo; `filename` não vazio | `"Nenhum arquivo GEDCOM enviado."` / `"Nenhum arquivo selecionado."` 🟢 |

### 1.2 Contrato da resposta (variáveis do template)

| Variável | Tipo | Quando vem | Significado |
| --- | --- | --- | --- |
| `message` | `str` | **sempre** | Texto ao operador — ver §6 |
| `success` | `bool` | sempre no `POST` | `True` só quando a árvore foi carregada |
| `gedcom_filename` | `str` | no sucesso e nos erros pós-upload | A **referência** (`<16 hex>__<nome visível>`), não o nome original 🟢 |
| `all_names` | `list[str]` | no sucesso e nos erros pós-upload | Lista **ordenada** de nomes da árvore carregada 🟢 |

> ⚠️ **Assimetria deliberada de nomes:** o `message` de sucesso cita o **nome original enviado** (`"Arquivo 'exemplo.ged' carregado!"`), enquanto `gedcom_filename` carrega a **referência**. Um é para o operador reconhecer o arquivo; o outro é para o sistema endereçá-lo. Confundir os dois foi a origem de uma falha real: a rota de DNA passava o nome ao parser, que procurava o CSV no diretório corrente e falhava com `No such file or directory`. 🟢

---

## 2. Contrato em disco

### 2.1 Nome do arquivo

```text
<16 hexadecimais>__<nome visível>
```

| Parte | Regra | Invariante |
| --- | --- | --- |
| Chave (16 hex) | `sha256(conteudo).hexdigest()[:16]` | **Mesmo conteúdo → mesma chave**, entre requisições e entre processos 🟢 |
| Separador | literal `__` | Fixo 🟢 |
| Nome visível | nome do cliente saneado | `/`, `\`, NUL → `_`; **acentos, espaços** e a **extensão original** preservados; vazio ou só pontos → `arvore.ged`; sem extensão → recebe `.ged` 🟢 |

### 2.2 A elegibilidade da referência tem DUAS formas, e isso é o contrato

| Uso | Função | Critério | Por quê |
| --- | --- | --- | --- |
| **Ler** | `chave_recebida_e_valida` | forma canônica `<16 hex>__<nome visível>` | É o que impede um valor manipulado de apontar para fora da pasta |
| **Aposentar** | `referencia_de_arquivo_da_pasta` | qualquer **nome simples**: sem barra, barra invertida, NUL, `.`, `..`, vazio; e `basename` de si mesmo | Os arquivos **sem chave** são os inalcançáveis, e são justamente os que o operador mais quer tirar da lista |

> 🔴 **A defesa contra escape é por FORMA, e não por lista negra** — em ambas. A forma fechada, sozinha, era **mais estreita que o gravador**: ela recusava acento e espaço que o próprio sistema **preserva de propósito**, e **quatro arquivos reais** ficaram inalcançáveis, com a tela dizendo que **não existiam** (`BUG-20261009-6RKP` / `RN-20`). 🟢
>
> 🟢 **`resolver` NÃO afrouxou.** Ler por referência continua exigindo a chave. É essa separação — duas perguntas, duas funções — que permite afrouxar a aposentadoria **sem** afrouxar a leitura.

### 2.3 Pasta

| Propriedade | Valor |
| --- | --- |
| Padrão | `<diretório do app>/uploads` — **ancorada no arquivo do app**, não no diretório corrente 🟢 |
| Sobreposição | `ANALISADOR_UPLOAD_FOLDER` (usada pelos testes) 🟢 |
| Subpasta de aposentados | `_aposentados` — **dentro** da pasta de upload, para que `listar` a ignore por já ignorar subdiretório 🟢 |
| Idempotência | arquivo com a mesma chave **não é reescrito** 🟢 |
| Remoção | o sistema **nunca** apaga um arquivo enviado (`RN-07`) 🟢 |
| Listagem | lê nome, tamanho e data; **não abre conteúdo**; **não cria** a pasta se ela não existir 🟢 |

---

## 3. Contrato da árvore (o que esta unit devolve)

**A unit não publica estado. Ela devolve um valor.**

| Posição | Nome | Tipo | Chave → valor |
| --- | --- | --- | --- |
| `arvore[0]` | `people` | `dict` | `xref_id` → registro `ged4py` INDI |
| `arvore[1]` | `families` | `dict` | `xref_id` → registro `ged4py` FAM |
| `arvore[2]` | `graph` | `networkx.Graph` | nós de pessoa (`type="person"`) e de família (`type="family"`) |
| `arvore[3]` | `child_to_family` | `dict[str, list[str]]` | `xref_id` do filho → **lista** de famílias |

**Quatro invariantes que quem reimplementar precisa honrar:**

1. **A árvore é um valor, e não uma variável de módulo.** Cada chamada produz um objeto independente; duas árvores podem coexistir no mesmo processo sem se contaminar. 🟢
2. **A tupla tem quatro posições, nessa ordem**, e é assim que ela entra em **toda** função do núcleo — o parâmetro se chama `arvore` e vem **primeiro**. 🟢
3. **Não existe contador de versão nem sinal de invalidação.** O que precisa de invalidação (o cache de nomes de `documentary_relationship`) deriva a chave do **conteúdo** recebido. ⚠️ **É dessa necessidade que nasce a lacuna `L-24`.** 🟡
4. **Não há sessão.** O que faz o papel de identificador de continuidade é a **chave de conteúdo**, devolvida ao navegador — e ela **não é segredo nem tem verificação de propriedade** (`permissions.md` §4). 🟢

---

## 4. Contrato de reenvio (novo)

**A foto de antes é o contrato.** `guardar_com_substituicao` chama `listar` **antes** de `guardar`, e é a única coisa que separa "já existia" de "acabou de nascer".

| Desfecho | Guarda (na ordem de precedência) | Mensagem |
| --- | --- | --- |
| `substituido` | aposentou **≥ 1** versão anterior de mesmo nome visível | `"Arquivo 'X' atualizado: a versão anterior saiu da lista e continua guardada, inteira, na pasta de aposentados."` |
| `identico` | aposentou **0** **e** a referência constava da foto de antes | `"Arquivo 'X' já estava armazenado com o mesmo conteúdo: nada mudou."` |
| `novo` | aposentou **0** **e** a referência **não** constava | `"Arquivo 'NOME ORIGINAL' carregado!"` — **literal congelado** |

| Regra | Consequência |
| --- | --- |
| A versão nova é gravada **antes** de a aposentadoria acontecer | O arquivo novo existe mesmo que a aposentadoria falhe |
| **Todas** as versões anteriores de mesmo nome visível são aposentadas | O acúmulo que existia antes da `RN-17` é limpo no primeiro reenvio |
| A colisão em `_aposentados/` recebe sufixo, e **nunca** sobrescreve | Depois de 99 tentativas, a operação **desiste** |
| O desfecho **não é persistido** | 🔴 Não há como auditar substituições depois do envio (`M-07`) |

---

## 5. Contrato de conteúdo aceito

| Verificação | Regra | Motivo da recusa |
| --- | --- | --- |
| Vazio | `len(conteudo) == 0` | `arquivo vazio` 🟢 |
| Binário | contém `b"\x00"` | `conteudo binario` 🟢 |
| Cabeçalho | após remover **um** BOM UTF-8 e os espaços à esquerda, os 6 primeiros bytes são `0 HEAD` | `não começa com a declaração 0 HEAD` 🟢 |

> ⚠️ **Os três motivos existem dentro da exceção, e NÃO aparecem na tela.** Desde a `RN-18` a mensagem é **fixa** para as três recusas. O motivo permanece acessível por `str(erro)` — a um passo de quem depura, e fora da vista do operador.

**O que este contrato deliberadamente NÃO verifica:**

| Não verificado | Por quê | Conf. |
| --- | --- | --- |
| Extensão do arquivo | `RISK-007` autoriza o relaxamento para não rejeitar GEDCOM de exportador legítimo | 🟢 |
| Tipo MIME | idem — o MIME do navegador não é confiável e não agrega | 🟢 |
| Gramática GEDCOM | Fica com o `ged4py`, que já a implementa. A validação aqui é **estreita de propósito** | 🟢 |
| Conteúdo do **CSV** | Só o GEDCOM passa por esta validação; o CSV tem apenas a forma do nome verificada — **e usa a mesma função de reenvio** | 🟢 |

---

## 6. Contrato de mensagens

Texto de **contrato**, não prosa: goldens de tela e o harness de paridade dependem de literais.

| Literal | Categoria |
| --- | --- |
| `"Nenhum arquivo GEDCOM enviado."` | Erro de entrada |
| `"Nenhum arquivo selecionado."` | Erro de entrada |
| `"Arquivo '{nome original}' carregado!"` | Sucesso — desfecho `novo` — **literal congelado** |
| `"Arquivo '{X}' já estava armazenado com o mesmo conteúdo: nada mudou."` | Sucesso — desfecho `identico` |
| `"Arquivo '{X}' atualizado: a versão anterior saiu da lista e continua guardada, inteira, na pasta de aposentados."` | Sucesso — desfecho `substituido` |
| `"'{ROTULO}' saiu da lista. O arquivo não foi apagado: ele continua guardado, inteiro, na pasta de aposentados."` | Sucesso — aposentadoria manual |
| `"Não foi possível aposentar o arquivo: ele não está mais na pasta."` | Erro de estado |
| `"Arquivo não reconhecido como GEDCOM. Favor, enviar o arquivo correto."` | Erro de conteúdo — **texto fixo desde a `RN-18`** |
| `"Erro ao processar GEDCOM: {e}"` | Erro inesperado no ramo |
| `"Erro: Arquivo GEDCOM não encontrado."` | Erro de entrada |
| `"Erro: Arquivo '{referência}' não existe mais."` | Erro de estado |
| `"Erro: o arquivo '{rotulo}' não pôde ser lido como GEDCOM. Ele pode estar corrompido, vazio, ou não ser um GEDCOM de verdade."` | Erro de parse |
| `"Arquivo maior que o limite de {n} MB."` | Recusa por tamanho (`413`) |
| `"Sem Nome"` — **apenas** quando não há `name` | Fallback de exibição |
| `""` (string vazia) — quando há `Name` com formato vazio | Contrato de paridade |
| `"arvore.ged"` | Fallback de nome |

> ⚠️ **Duas mensagens interpolam constantes:** `"Arquivo maior que o limite de {n} MB."` embute o teto de corpo. Mudar o número é mudar **texto de contrato**, e não apenas um parâmetro (`spec-impact-matrix.md` §5). 🟢
> ⚠️ **`""` não é "erro de dado": é o valor correto.** Trata-se do contrato de paridade `DIV-001`; convertê-lo em `"Sem Nome"` reintroduz a única divergência de comportamento já encontrada entre legado e reconstrução. 🟢

---

## 7. Contrato de falha

| Situação | O que **é** garantido | O que **não** é |
| --- | --- | --- |
| Conteúdo recusado | Nenhum byte gravado; mensagem única | O motivo não aparece na tela (só em `str(erro)`) 🟢 |
| Corpo acima do teto | Nenhum byte lido nem gravado; `413` | — 🟢 |
| Parse falha | Nada é publicado, porque não há estado a publicar; mensagem ao operador | Nada é registrado em log ou auditoria 🔴 |
| Referência manipulada | Recusa por forma nas **duas** funções; nenhum caminho fora de `uploads/` é aberto | Não há verificação de **propriedade** da referência 🔴 |
| Aposentadoria | O arquivo é movido; nada é apagado; colisão recebe sufixo | Não há como desfazer pela aplicação 🟡 |
| Disco cheio ou sem permissão | A exceção sobe e é capturada pelo `try` da rota | Não há retry, alerta ou degradação controlada 🟡 |
| Requisição concorrente sobre a árvore | ✅ **Garantido desde 2026-10-07:** cada requisição tem a **sua** árvore | — 🟢 |
| Requisição concorrente sobre o **disco** | — | **Não há garantia:** `guardar` e `aposentar` verificam e depois agem 🟡 |

---

## 8. Compatibilidade e versionamento

| Elemento do contrato | Estabilidade exigida | Consequência de mudar |
| --- | --- | --- |
| Forma do nome em disco | **Alta** | Quebra a continuidade entre requisições: o formulário devolve o valor no `POST` seguinte |
| Forma canônica da chave (leitura) | **Alta (segurança)** | Afrouxar demais reabre o escape de caminho do `BUG-20260929-QMLY` |
| Forma de nome da aposentadoria | **Alta** | Estreitar demais reabre o `BUG-20261009-6RKP`: o arquivo com acento volta a ser inalcançável |
| Nome do campo `gedcom_filename` | **Alta** | Quebra o template e todos os `POST` de análise |
| Valores de `action` | **Alta** | É a **granularidade das units** (`config.toml [specs]`) |
| **Forma da árvore (tupla de 4 posições)** | **Alta** | Todo o núcleo a recebe por parâmetro; mudar a ordem quebra todos os fluxos |
| Literais das mensagens | Média | Goldens de tela e harness de paridade dependem deles |
| O literal congelado de `novo` | **Alta** | É o que a paridade de tela consome |
| Preservação da extensão | Média | Fixá-la em `.ged` quebra a unit `analise-dna` |
| Valor do teto de corpo | Média | Altera o texto da mensagem de `413` |
| Nome da subpasta `_aposentados` | Média | É o que faz o arquivo sumir da lista sem filtro novo; renomear exigiria um filtro que hoje não existe |

---

*Gerado pelo Reversa-Writer em 2026-10-10 (re-extração, nível completo).*

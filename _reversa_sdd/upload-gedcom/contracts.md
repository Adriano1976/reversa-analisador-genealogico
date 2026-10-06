# Unit `upload-gedcom` — Contratos

> Re-extração de **2026-10-05** (nível **Completo**). Artefato novo: o nível `essencial` não o gerava.
> Este arquivo fixa **o que atravessa a fronteira** da unit: o contrato HTTP, o contrato em disco, o contrato de estado e o contrato de mensagens.
> Escala de confiança: 🟢 CONFIRMADO | 🟡 INFERIDO | 🔴 LACUNA

---

## 1. Contrato HTTP

| Método | Caminho | Entrada | Status | Corpo da resposta |
| --- | --- | --- | --- | --- |
| `GET` | `/` | — | `200` | HTML da tela, sem estado |
| `POST` | `/` (`action=upload_gedcom`) | `multipart/form-data` com o arquivo no campo `gedcom` | `200` | HTML com `message`, `success` e, no sucesso, `gedcom_filename` + `all_names` |
| `POST` | `/` (qualquer `action`) | corpo acima de **16 MB** | **`413`** | HTML com `"Arquivo maior que o limite de 16 MB."` e `success=false` |

> 🟢 **Não há contrato JSON, redirect, `201`, `400` ou `409`.** Toda recusa de **negócio** é HTML com status `200` e `success=false`. A única recusa de **transporte** é o `413`, e ele acontece **antes** de a rota executar.

### 1.1 Contrato da requisição

| Campo | Local | Obrigatório | Forma aceita | Recusa |
| --- | --- | --- | --- | --- |
| `action` | `form` | sim | literal `upload_gedcom` | outro valor não entra neste ramo 🟢 |
| `gedcom` | `files` | sim | arquivo; `filename` não vazio | `"Nenhum arquivo GEDCOM enviado."` / `"Nenhum arquivo selecionado."` 🟢 |

### 1.2 Contrato da resposta (variáveis do template)

| Variável | Tipo | Quando vem | Significado |
| --- | --- | --- | --- |
| `message` | `str` | **sempre** | Texto ao operador — ver §5 |
| `success` | `bool` | sempre no `POST` | `True` só quando a árvore foi carregada |
| `gedcom_filename` | `str` | no sucesso e nos erros pós-upload | O **nome armazenado** (`<16 hex>__<nome visível>`), não o nome original 🟢 |
| `all_names` | `list[str]` | no sucesso e nos erros pós-upload | Lista **ordenada** de nomes da árvore carregada 🟢 |

> ⚠️ **Assimetria deliberada de nomes:** o `message` de sucesso cita o **nome original enviado** (`"Arquivo 'exemplo.ged' carregado!"`), enquanto `gedcom_filename` carrega o **nome armazenado**. Um é para o operador reconhecer o arquivo; o outro é para o sistema endereçá-lo. Confundir os dois foi a origem de uma falha real: a rota de DNA passava o nome ao parser, que procurava o CSV no diretório corrente e falhava com `No such file or directory`. 🟢

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
| Nome visível | nome do cliente saneado | `/`, `\`, NUL → `_`; acentos, espaços e **extensão original** preservados; vazio ou só pontos → `arvore.ged`; sem extensão → recebe `.ged` 🟢 |

**Forma fechada, verificada em toda leitura:** `^[0-9a-f]{16}__[A-Za-z0-9._-]+$`

> 🔴 **Este é o contrato de segurança da unit.** A expressão exclui `/`, `\` e `..`, de modo que um valor vindo do formulário **não tem como** escapar da pasta de upload. Afrouxá-la reabre o `BUG-20260929-QMLY`. É validação **por forma**, e não por lista negra — não há caracteres proibidos a enumerar. 🟢

### 2.2 Pasta

| Propriedade | Valor |
| --- | --- |
| Padrão | `<diretório do app>/uploads` — **ancorada no arquivo do app**, não no diretório corrente 🟢 |
| Sobreposição | `ANALISADOR_UPLOAD_FOLDER` (usada pelos testes) 🟢 |
| Criação | no **import**, pela **mesma** função que a resolve — o diretório criado e o procurado não podem divergir 🟢 |
| Idempotência | arquivo com a mesma chave **não é reescrito** 🟢 |
| Remoção | o sistema **nunca** apaga um arquivo enviado 🟢 |

---

## 3. Contrato de estado (entre requisições)

Publicado por esta unit e consumido pelas outras duas:

| Global | Tipo | Chave → valor | Substituição |
| --- | --- | --- | --- |
| `people` | `dict` | `xref_id` → registro `ged4py` INDI | `clear()` + `update()` — **identidade de objeto preservada** 🟢 |
| `families` | `dict` | `xref_id` → registro `ged4py` FAM | idem 🟢 |
| `child_to_family` | `dict[str, list[str]]` | `xref_id` do filho → **lista** de famílias | idem 🟢 |
| `graph` | `networkx.Graph` | nós de pessoa e de família | **reatribuído** 🟢 |
| `versao` | `int` | contador de cargas | `+= 1` a cada carga 🟢 |

**Três invariantes que quem reimplementar precisa honrar:**

1. **A assimetria de substituição é contrato.** Os três `dict` são mutados *in place* para que os bindings importados **no topo** pelos outros módulos continuem apontando para o objeto vivo. O `graph` é reatribuído — e é **exatamente por isso** que quem o consome o importa **dentro da função** (`path_finding.py:38`). Um import no topo ficaria preso ao grafo antigo, ou a `None`. 🟢
2. **`versao` não é decorativo.** Ele existe porque `id()` **não** muda com mutação *in place*, e dois GEDCOMs diferentes podem ter a mesma contagem de pessoas. É o único sinal de invalidação do índice `nome normalizado → ids` (`documentary_relationship.py:185-202`). 🟢
3. **Não há sessão.** O estado vive no **processo**. O que faz o papel de identificador de continuidade é a **chave de conteúdo**, devolvida ao navegador em campo oculto — e ela não é segredo nem tem verificação de propriedade (`permissions.md` §4). 🟢

---

## 4. Contrato de conteúdo aceito

| Verificação | Regra | Motivo da recusa |
| --- | --- | --- |
| Vazio | `len(conteudo) == 0` | `arquivo vazio` 🟢 |
| Binário | contém `b"\x00"` | `conteudo binario` 🟢 |
| Cabeçalho | após remover **um** BOM UTF-8 e os espaços à esquerda, os 6 primeiros bytes são `0 HEAD` | `não começa com a declaração 0 HEAD` 🟢 |

**O que este contrato deliberadamente NÃO verifica:**

| Não verificado | Por quê | Conf. |
| --- | --- | --- |
| Extensão do arquivo | `RISK-007` autoriza o relaxamento para não rejeitar GEDCOM de exportador legítimo | 🟢 |
| Tipo MIME | idem — o MIME do navegador não é confiável e não agrega | 🟢 |
| Gramática GEDCOM | Fica com o `ged4py`, que já a implementa. A validação aqui é **estreita de propósito** | 🟢 |
| Conteúdo do **CSV** | Só o GEDCOM passa por esta validação; o CSV tem apenas a forma do nome verificada | 🟢 |

---

## 5. Contrato de mensagens

Texto de **contrato**, não prosa: goldens de tela e o harness de paridade dependem de literais.

| Literal | Local | Categoria |
| --- | --- | --- |
| `"Nenhum arquivo GEDCOM enviado."` | `app.py:118` | Erro de entrada |
| `"Nenhum arquivo selecionado."` | `app.py:121` | Erro de entrada |
| `"Arquivo '{nome original}' carregado!"` | `app.py:127` | Sucesso |
| `"Arquivo não reconhecido como GEDCOM: {motivo}."` | `app.py:88` | Erro de conteúdo |
| `"Erro ao processar GEDCOM: {e}"` | `app.py:129` | Erro de parse |
| `"Erro: Arquivo GEDCOM não encontrado."` | `app.py:133` | Erro de entrada |
| `"Erro: Arquivo '{chave}' não existe mais."` | `app.py:136` | Erro de estado |
| `"Arquivo maior que o limite de {n} MB."` | `app.py:70` | Recusa por tamanho (`413`) |
| `"Sem Nome"` — **apenas** quando não há `name` | `gedcom_state.py:43`, `:52` | Fallback de exibição |
| `""` (string vazia) — quando há `Name` com formato vazio | `gedcom_state.py:52` | Contrato de paridade |
| `"arvore.ged"` | `validate.py:53`, `:63` | Fallback de nome |

> ⚠️ **Duas mensagens interpolam constantes:** `"Arquivo maior que o limite de {n} MB."` embute `MAX_CONTENT_LENGTH`. Mudar o número é mudar **texto de contrato**, e não apenas um parâmetro (`spec-impact-matrix.md` §5). 🟢
> ⚠️ **`""` não é "erro de dado": é o valor correto.** Trata-se do contrato de paridade `DIV-001`; convertê-lo em `"Sem Nome"` reintroduz a única divergência de comportamento já encontrada entre legado e reconstrução. 🟢

---

## 6. Contrato de falha

| Situação | O que **é** garantido | O que **não** é |
| --- | --- | --- |
| Conteúdo recusado | Nenhum byte gravado; mensagem nomeada | — 🟢 |
| Corpo acima do teto | Nenhum byte lido nem gravado; `413` | — 🟢 |
| Parse falha | Estado **anterior** preservado (a mutação só ocorre após parse bem-sucedido); mensagem ao operador | Nada é registrado em log ou auditoria 🔴 |
| Chave manipulada | Recusa por forma; nenhum caminho fora de `uploads/` é aberto | Não há verificação de **propriedade** da chave 🔴 |
| Disco cheio ou sem permissão | A exceção sobe e é capturada pelo `try` da rota, virando `"Erro ao processar GEDCOM: {e}"` | Não há retry, alerta ou degradação controlada 🟡 |
| Requisição concorrente | — | **Não há garantia de isolamento**: o estado é global de processo com 4 threads (`L-16`) 🟡 |

---

## 7. Compatibilidade e versionamento

| Elemento do contrato | Estabilidade exigida | Consequência de mudar |
| --- | --- | --- |
| Forma do nome em disco | **Alta** | Quebra a continuidade entre requisições: o formulário devolve o valor no `POST` seguinte |
| Forma fechada da chave | **Alta (segurança)** | Afrouxar reabre o escape de caminho do QMLY |
| Nome do campo `gedcom_filename` | **Alta** | Quebra o template e todos os `POST` de análise |
| Valores de `action` | **Alta** | É a **granularidade das units** (`config.toml [specs]`) |
| Literais das mensagens | Média | Goldens de tela e harness de paridade dependem deles |
| Preservação da extensão | Média | Fixá-la em `.ged` quebra a unidade `analise-dna` |
| Valor do teto de corpo | Média | Altera o texto da mensagem de `413` |

---

*Gerado pelo Reversa-Writer em 2026-10-05 (re-extração, nível completo).*

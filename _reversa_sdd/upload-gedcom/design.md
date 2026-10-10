# Unit `upload-gedcom` — Design Técnico

> Unit do tipo **endpoint** — `POST /` com `action=upload_gedcom`.
> Re-extração de **2026-10-10** (nível **Completo**). Substitui o design de 2026-10-05, que descrevia o estado global, o alfabeto fechado e a ausência de reenvio.
> Escala de confiança: 🟢 CONFIRMADO | 🟡 INFERIDO | 🔴 LACUNA

---

## Interface

### Endpoint HTTP

| Método | Caminho | Entrada | Saída | Status codes |
| --- | --- | --- | --- | --- |
| `GET` | `/` | — | `index.html` com o formulário **e as duas abas de lista** | `200` 🟢 |
| `POST` | `/` | `multipart/form-data` com `action=upload_gedcom` e o arquivo no campo `gedcom` | `index.html` com `gedcom_filename`, `all_names` e `message` | `200` em sucesso **e em erro de negócio**; **`413`** quando o corpo excede 16 MB 🟢 |

> **A unit não responde `4xx` por erro de negócio.** Toda recusa de conteúdo é renderizada como HTML com `success=False` e status `200`. A **única** exceção é o teto de corpo, recusado pelo Flask **antes** de a rota executar. 🟢

### Símbolos

| Símbolo | Arquivo | Assinatura | Retorno | Observação |
| --- | --- | --- | --- | --- |
| `upload_gedcom` | `application/upload_gedcom.py` | `(conteudo, nome_original, dono, armazenamento, carregador)` | `ResultadoDeUpload` | Caso de uso: transforma o motivo em texto na **exceção tipada** 🟢 |
| `guardar_com_substituicao` | `application/reenvio.py` | `(armazenamento, conteudo, nome_original, tipo, dono)` | `Armazenado` | Foto de antes + aposentadoria + desfecho 🟢 |
| `_pasta_uploads` | `app.py` | `()` | `str` | Ancorada no arquivo do app; `ANALISADOR_UPLOAD_FOLDER` sobrepõe 🟢 |
| `_arvore_do_formulario` | `app.py` | `()` | `(referencia, arvore, erro)` | Distingue **não existe** de **não pôde ser lido** 🟢 |
| `validar_conteudo_gedcom` | `utils/validate.py` | `(conteudo: bytes)` | `str \| None` | Motivo da recusa, ou `None` 🟢 |
| `chave_de_armazenamento` | `utils/validate.py` | `(conteudo: bytes)` | `str` (16 hex) | `sha256(conteudo).hexdigest()[:16]` 🟢 |
| `nome_do_arquivo_armazenado` | `utils/validate.py` | `(chave, nome_original)` | `str` | `chave + "__" + nome_visivel_seguro(...)` 🟢 |
| `nome_visivel_seguro` | `utils/validate.py` | `(nome_original)` | `str` | Preserva a extensão; nunca vazio 🟢 |
| `chave_recebida_e_valida` | `utils/validate.py` | `(referencia)` | `bool` | **"tem chave?"** — é o que `resolver` exige 🟢 |
| `referencia_de_arquivo_da_pasta` | `utils/validate.py` | `(referencia)` | `bool` | **"posso tratar como nome?"** — mais permissiva, é o que `aposentar` exige 🟢 |
| `pode_ser_usado` / `motivo_de_indisponibilidade` | `utils/validate.py` | `(nome)` | `bool` / `str \| None` | A tela pergunta a **mesma** função que o resolvedor 🟢 |
| `carregar_arvore` | `parsers/gedcom_parser.py` | `(caminho: str)` | `(people, families, graph, child_to_family)` | **Devolve a árvore como valor** 🟢 |
| `guardar` | `ports/adaptadores.py` | `(conteudo, nome_original, tipo, dono)` | `(caminho, motivo)` | Valida **antes** de gravar; não reescreve 🟢 |
| `resolver` | `ports/adaptadores.py` | `(referencia, dono)` | `str \| None` | Valida a forma **antes** de `os.path.exists` 🟢 |
| `listar` | `ports/adaptadores.py` | `(dono)` | `list[EntradaArmazenada]` | `os.listdir` + `os.stat`, **sem `open`** 🟢 |
| `aposentar` | `ports/adaptadores.py` | `(referencia, dono)` | `bool` | `os.replace` para `_aposentados/`; nunca apaga 🟢 |
| `get_name` / `ref_id` | `core/registro.py` | `(person)` / `(val)` | `str` | **Cópia literal do oráculo** — não "melhorar" 🟢 |
| `strip_bad_utf` / `demojibake` | `utils/text_cleaning.py` | `(s)` | `str` | Autoridade única da limpeza 🟢 |

> 🟢 **`dono` está em todas as assinaturas da porta e é ignorado nos quatro métodos do armazenamento.** Ele chega **por chamada**, e não pela construção do adaptador, porque os adaptadores são **singletons de processo** montados no import de `app.py`.

## Fluxo Principal

### Borda (`app.py`, ramo `upload_gedcom`)

1. Se `request.method == "POST"`, lê `action = request.form.get("action")`. 🟢
2. `action == "upload_gedcom"`; se `"gedcom" not in request.files` → `"Nenhum arquivo GEDCOM enviado."` com `success=False`. 🟢
3. Se `gedcom_file.filename == ''` → `"Nenhum arquivo selecionado."`. 🟢
4. `caso_de_uso_de_upload(gedcom_file.read(), gedcom_file.filename, DONO_DO_PROCESSO, _ARMAZENAMENTO, _CARREGADOR)`, dentro de `try`. 🟢
5. Erro de domínio → `traduzir(erro).mensagem` com `success=False`; qualquer outra exceção → `"Erro ao processar GEDCOM: {e}"`. 🟢
6. Sucesso → renderiza com `gedcom_filename=resultado.referencia`, `all_names=resultado.nomes`, `message` e `success=True`. 🟢

### Caso de uso (`application/upload_gedcom.py` → `application/reenvio.py`)

1. **Foto de ANTES:** `listar(dono)` e guarda os **nomes** — **antes** de qualquer escrita. 🟢
2. `guardar(conteudo, nome_original, tipo, dono)`: valida o conteúdo (só se `tipo == "gedcom"`), deriva a chave e grava **somente se o caminho não existir**. 🟢
3. `motivo` preenchido → o caso de uso **levanta `GedcomNaoSuportado`**. O adaptador **não** levanta exceção de domínio (`A002`). 🟢
4. **Aposentadoria:** cada versão anterior de **mesmo nome visível** é movida para `_aposentados/`. Podem ser **várias** — o reenvio limpa o acúmulo que existia antes da `RN-17`. 🟢
5. **Desfecho**, na ordem de precedência: `substituido` (aposentou ≥ 1) → `identico` (aposentou 0 **e** a referência constava da foto) → `novo`. 🟢
6. `carregador.carregar(referencia, dono)` → `resolver` valida a forma e chama `carregar_arvore`. 🟢
7. `nomes_de_exibicao(arvore)` devolve a lista ordenada. 🟢

> 🟢 **A ordem de decisão do desfecho é a regra, e a precedência é do `substituido`.** Um reenvio pode ser simultaneamente "o conteúdo já existia" e "havia versão anterior": o código decide pelo que foi **movido**.

### Núcleo — parsing (`parsers/gedcom_parser.py`)

1. `carregar_arvore(caminho)` abre o arquivo com `GedcomReader` e monta `people` e `families` indexados por `xref_id`. 🟢
2. Constrói o grafo: um nó por pessoa (`type="person"`) e por família (`type="family"`); para cada `FAM`, extrai `HUSB`, `WIFE` e cada `CHIL`, acumulando `child_to_family[cid].append(fam_id)`. 🟢
3. Cria aresta para marido, esposa e cada filho **apenas se o nó existir**. 🟢
4. **Devolve `(people, families, graph, child_to_family)`.** Não escreve nada fora da tupla. 🟢

> 🟢 **O que desapareceu:** a mutação *in place* de `people`/`families`/`child_to_family`, a reatribuição de `graph`, o contador `versao` e a casca `load_gedcom_and_build_graph`. O parse **não publica**: ele **devolve**.

## Fluxos Alternativos

| Condição | Comportamento | Conf. |
| --- | --- | --- |
| Sem o campo `gedcom` | `"Nenhum arquivo GEDCOM enviado."`, nada é gravado | 🟢 |
| `filename` vazio | `"Nenhum arquivo selecionado."`, nada é gravado | 🟢 |
| Conteúdo vazio, com NUL, ou sem `0 HEAD` | `"Arquivo não reconhecido como GEDCOM. Favor, enviar o arquivo correto."` (**mesmo texto nos três**) | 🟢 |
| Corpo acima de 16 MB | `HTTP 413` com `"Arquivo maior que o limite de 16 MB."`; o corpo **não** é lido | 🟢 |
| Mesma referência já em disco | Arquivo **não** é reescrito; desfecho `identico` | 🟢 |
| Mesmo nome visível com conteúdo novo | Versão anterior **aposentada**; desfecho `substituido` | 🟢 |
| Nome visível inédito | Nada é aposentado; desfecho `novo` | 🟢 |
| Colisão em `_aposentados/` | Sufixo `.1`…`.99`; esgotado, devolve `False` **sem** sobrescrever | 🟢 |
| Exceção no parse | `"Erro: o arquivo 'X' não pôde ser lido como GEDCOM. …"`; nada é publicado, porque não há estado a publicar | 🟢 |
| `FAM` sem `xref_id` | Ignorada por completo, sem erro | 🟢 |
| `HUSB`/`WIFE`/`CHIL` apontando para xref inexistente | A aresta é descartada **em silêncio**; a referência permanece nos sub-registros | 🟢 |
| Referência sem chave, mas com forma de nome válida, na **leitura** | `resolver` devolve `None` → `"Erro: Arquivo '{referência}' não existe mais."` | 🟢 |
| Referência com **acento** na leitura | **Aceita** (é o caso do `BUG-20261009-6RKP`) | 🟢 |
| Referência é um caminho (`../../etc/passwd`) | Recusada por forma, nas **duas** funções | 🟢 |

## Dependências

| Dependência | Versão | Como usa | Conf. |
| --- | --- | --- | --- |
| **ged4py** | 0.5.5 (pin do `.venv`, interpretador oficial) | `GedcomReader` para `records0("INDI")`/`records0("FAM")` e acesso a sub-registros | 🟢 |
| **networkx** | 3.7 | `nx.Graph`, `add_node`, `add_edge`, `has_node` | 🟢 |
| **Flask** | 3.1.3 | Rota, `request.files`, `request.form`, `render_template`, `MAX_CONTENT_LENGTH` | 🟢 |
| **werkzeug** | transitiva | `RequestEntityTooLarge` para o handler de `413` | 🟢 |
| **waitress** | 3.0.2 | Servidor de produção do bloco de entrada | 🟢 |
| **Sistema de arquivos** | — | `src/uploads/` e `src/uploads/_aposentados/` | 🟢 |
| Units internas | — | **Nenhuma.** Esta é a base: `tela-de-entrada`, `analise-dna` e `busca-caminho` dependem dela | 🟢 |

## Decisões de Design Identificadas

| Decisão | Evidência no código | Confiança |
| --- | --- | --- |
| **Chave derivada do conteúdo**, e não UUID aleatório, porque o formulário devolve o valor no `POST` seguinte | `utils/validate.py:chave_de_armazenamento`; `adrs/17` | 🟢 |
| **Elegibilidade por FORMA DE NOME**, com **duas funções** para duas perguntas distintas | `utils/validate.py`; `adrs/32`; `RN-20` | 🟢 |
| **A árvore entra e sai por parâmetro** — o parse devolve valor e não publica estado | `parsers/gedcom_parser.py:carregar_arvore`; `adrs/24` | 🟢 |
| **A foto de antes é tirada ANTES de guardar** — é o que permite distinguir `identico` de `novo` | `application/reenvio.py`; `adrs/31` | 🟢 |
| **Aposentar move, não apaga**, e a subpasta fica **dentro** da pasta de upload para que `listar` já a ignore | `ports/adaptadores.py`; `adrs/30` | 🟢 |
| **Sufixo numérico em vez de sobrescrever** aposentado — para nomes sem chave o nome não carrega conteúdo | `ports/adaptadores.py:aposentar` | 🟢 |
| **Duas camadas de defesa na aposentadoria:** forma de nome **e** conferência do `dirname` | idem | 🟢 |
| **O `dono` é exigido em todas as assinaturas e ignorado nos quatro métodos** | `ports/__init__.py`, `ports/adaptadores.py`; `adrs/26` | 🟢 |
| **O adaptador não levanta exceção de domínio** — devolve motivo em texto, e o caso de uso o tipifica | `A002`; `application/upload_gedcom.py` | 🟢 |
| **Mensagem de recusa de conteúdo FIXA**, com o motivo preservado dentro da exceção | `application/traducao.py`; `RN-18` | 🟢 |
| **Teto de corpo aplicado antes de ler** — a ausência dele fazia o multipart inteiro ser gravado em disco antes de qualquer verificação | `app.py:TETO_DE_UPLOAD_EM_BYTES` | 🟢 |
| **A extensão original é preservada**, e não fixada em `.ged` — fixá-la quebrou o CSV de DNA | `utils/validate.py:nome_visivel_seguro` | 🟢 |
| **Pasta de upload ancorada no arquivo do app**, e não relativa ao diretório corrente | `app.py:_pasta_uploads` | 🟢 |
| **O retorno é o caminho completo**, nunca o nome | `ports/adaptadores.py:guardar` | 🟢 |
| **`get_name` não trata formato vazio** — é paridade com o oráculo, não descuido | `core/registro.py`; `DIV-001` | 🟢 |
| Validação de conteúdo **estreita de propósito**: só o cabeçalho; a gramática fica com o `ged4py` | `utils/validate.py:validar_conteudo_gedcom` | 🟢 |
| **O CSV não passa por validação de conteúdo** — e usa a **mesma** função de reenvio | `ports/adaptadores.py:guardar`; `application/reenvio.py` | 🟢 |
| **`listar` não abre arquivo nenhum** — extensão decide a aba, e a ordem é por `mtime` | `ports/adaptadores.py:listar`; `adrs/28` (empacotamento) | 🟢 |

## Estado Interno

| Onde | O que | Como evolui | Conf. |
| --- | --- | --- | --- |
| **Retorno do parse** | a tupla `(people, families, graph, child_to_family)` | **Criada a cada chamada.** É um valor que viaja por parâmetro até o fim da requisição | 🟢 |
| `_ARMAZENAMENTO` / `_CARREGADOR` | adaptadores concretos | **Singletons de processo**, montados **uma vez** no import de `app.py` | 🟢 |
| `_DEPENDENCIAS` | as quatro funções de CSV e as duas de diagrama | idem — até a extração havia uma segunda montagem por requisição (`T018`) | 🟢 |
| `DONO_DO_PROCESSO` | literal `"unico"` | Constante; único lugar onde o valor do dono é declarado | 🟢 |
| Arquivo enviado | `<pasta>/<chave>__<nome visível>` | **Conteúdo imutável** (mesma chave não é reescrita); **posição mutável** (pasta ↔ `_aposentados/`) | 🟢 |

> 🟢 **Não há mais estado de domínio no processo.** O que sobrevive à requisição é o **arquivo** — e a única coisa que muda nele é a pasta em que ele está.
> 🟢 **Não há sessão.** A chave de conteúdo, devolvida ao navegador, é **identificador, não segredo**, e **não há verificação de propriedade** (`permissions.md` §4).

## Observabilidade

- **Nenhum `logging`, métrica ou trace é emitido pela unit.** 🔴
- Erros de parse chegam ao operador apenas como `message` no template. 🟢
- A única saída textual do sistema é o `print` de inicialização do servidor. 🟢
- 🟡 **O desfecho do reenvio não é registrado em lugar nenhum** (`M-07`): depois do envio, o sistema não sabe dizer se aquele arquivo foi novo, idêntico ou substituto — a informação morreu com a resposta.
- 🟡 **O estado "aposentado" não é consultável pela aplicação** (`M-05`): quem sabe que um arquivo foi aposentado é o sistema de arquivos, e não há coluna nem índice.
- A instrumentação de desenvolvimento (oráculo, harness de paridade, goldens) vive em `_reversa_sdd/` e **não faz parte da aplicação**. 🟢

## Riscos e Lacunas

- 🟡 **A foto de antes não é atômica em relação à escrita.** Se `listar` devolver um retrato incompleto, um caso `identico` pode ser classificado como `novo`. É a mesma corrida de armazenamento da dívida #3 — mecanismo 🟢, alcance não medido 🟡.
- 🔴 **`"Sem Nome"` é praticamente inalcançável a partir de registros `INDI` reais.** O `ged4py` entrega um objeto `Name` cujo `.format()` é `''` mesmo quando a tag `NAME` é removida. O literal teve **zero ocorrências** medidas em 55.523 nomes reais. Não é bug: é detalhe de contrato que **precisa ser preservado**. 🟢
- 🔴 **A chave de conteúdo não é segredo e não tem dono.** Quem a conhece carrega a árvore correspondente — `BUG-20260929-BJJH`, mantido por **aceite de risco** com condição de reabertura nomeada (`adrs/18`). O `dono` que a feature 007 acrescentou **não** mudou isso (`adrs/26`). 🟡
- 🟡 **O CSV de DNA continua sem validação de conteúdo** (`tipo == "csv"` pula a validação). A assimetria em relação ao GEDCOM é dívida preservada de propósito (`P-05`).
- 🟡 **`aposentar` é irreversível pelo sistema e reversível pelo operador**, que precisa saber onde a pasta fica. Não há "desaposentar" na tela, porque a aplicação não enxerga o estado aposentado.
- 🟡 **Sem validação de extensão ou tipo MIME** — decisão deliberada (`RISK-007`), para não rejeitar GEDCOM de exportador legítimo.
- 🔴 **O `RuntimeError` de "árvore recém-gravada que não pôde ser relida" é inalcançável em execução.** Existe para o checador de tipos estreitar a união do retorno.
- 🟢 **Resolvido em 2026-10-10:** o arquivo com acento voltou a ser alcançável (`BUG-20261009-6RKP`, `RN-20`).
- 🟢 **Resolvido em 2026-10-07:** o estado global saiu, e com ele a contaminação entre requisições concorrentes (`L-16` fechada).

---

*Gerado pelo Reversa-Writer em 2026-10-10 (re-extração, nível completo).*

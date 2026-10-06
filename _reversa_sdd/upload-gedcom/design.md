# Unit `upload-gedcom` — Design Técnico

> Unit do tipo **endpoint** — `POST /` com `action=upload_gedcom`.
> Re-extração de **2026-10-05** (nível **Completo**). Substitui o design de 2026-09-30.
> Escala de confiança: 🟢 CONFIRMADO | 🟡 INFERIDO | 🔴 LACUNA

---

## Interface

### Endpoint HTTP

| Método | Caminho | Entrada | Saída | Status codes |
| --- | --- | --- | --- | --- |
| `GET` | `/` | — | `index.html` com o formulário de upload | `200` 🟢 |
| `POST` | `/` | `multipart/form-data` com `action=upload_gedcom` e o arquivo no campo `gedcom` | `index.html` com `gedcom_filename`, `all_names` e `message` | `200` em sucesso e em erro de negócio; **`413`** quando o corpo excede 16 MB 🟢 |

> **A unit não responde `4xx` por erro de negócio.** Toda recusa de conteúdo é renderizada como HTML com `success=False` e status `200`. A **única** exceção é o teto de corpo, que é recusado pelo Flask **antes** de a rota executar. 🟢

### Símbolos

| Símbolo | Arquivo:linha | Assinatura | Retorno | Observação |
| --- | --- | --- | --- | --- |
| `_pasta_uploads` | `app.py:42` | `()` | `str` | Pasta ancorada no arquivo do app; `ANALISADOR_UPLOAD_FOLDER` sobrepõe 🟢 |
| `_guardar_upload` | `app.py:75` | `(arquivo, kind: str)` | `(caminho, motivo)` | `motivo` é `None` no sucesso; `caminho` é **completo** 🟢 |
| `_resolver_caminho_armazenado` | `app.py:99` | `(nome_recebido)` | `str \| None` | Valida a **forma** antes de compor o caminho 🟢 |
| `_requisicao_grande` | `app.py:66` | `(_erro)` | `(HTML, 413)` | Handler de `RequestEntityTooLarge` 🟢 |
| `validar_conteudo_gedcom` | `validate.py:90` | `(conteudo: bytes)` | `str \| None` | Motivo da recusa, ou `None` 🟢 |
| `chave_de_armazenamento` | `validate.py:68` | `(conteudo: bytes)` | `str` (16 hex) | `sha256(conteudo).hexdigest()[:16]` 🟢 |
| `nome_do_arquivo_armazenado` | `validate.py:73` | `(chave, nome_original)` | `str` | `chave + "__" + nome_visivel_seguro(...)` 🟢 |
| `nome_visivel_seguro` | `validate.py:40` | `(nome_original)` | `str` | Preserva a extensão; nunca vazio 🟢 |
| `chave_recebida_e_valida` | `validate.py:78` | `(nome_recebido)` | `bool` | Casa `^[0-9a-f]{16}__[A-Za-z0-9._-]+$` 🟢 |
| `load_gedcom_and_build_graph` | `gedcom_parser.py:50` | `(file_path: str)` | `list[str]` | Substitui o estado; devolve nomes ordenados 🟢 |
| `build_graph_from_parser` | `gedcom_parser.py:18` | `(people_dict, parser)` | `(nx.Graph, dict)` | Grafo + `child_to_family` 🟢 |
| `ref_id` | `gedcom_state.py:33` | `(val)` | `str` | Aceita objeto ged4py ou string 🟢 |
| `get_name` | `gedcom_state.py:38` | `(person)` | `str` | `person.name.format()` se `person and person.name`; senão `"Sem Nome"` 🟢 |
| `strip_bad_utf` | `text_cleaning.py:37` | `(s)` | `str` | Mapa de 18 pares + remoção por regex 🟢 |
| `demojibake` | `text_cleaning.py:56` | `(s)` | `str` | *Round-trip* `latin1 → utf-8`, condicional 🟢 |

## Fluxo Principal

### Camada de rota (`app.py:114-129`)

1. `app.py:114-115` — se `request.method == "POST"`, lê `action = request.form.get("action")`. 🟢
2. `app.py:116-118` — `action == "upload_gedcom"`; se `"gedcom" not in request.files` → `"Nenhum arquivo GEDCOM enviado."` com `success=False`. 🟢
3. `app.py:119-121` — se `gedcom_file.filename == ''` → `"Nenhum arquivo selecionado."`. 🟢
4. `app.py:123` — `_guardar_upload(gedcom_file, "gedcom")`, dentro de `try`. 🟢
5. `app.py:85-88` — o conteúdo é lido **inteiro** (`arquivo.read()`) e validado; recusa devolve `(None, motivo)`. 🟢
6. `app.py:90-96` — chave, nome final e caminho; **só grava se o arquivo não existir**. 🟢
7. `app.py:126` — `load_gedcom_and_build_graph(caminho_armazenado)`. 🟢
8. `app.py:127` — renderiza com `gedcom_filename=os.path.basename(caminho_armazenado)`, `all_names` e `"Arquivo '{gedcom_file.filename}' carregado!"`. 🟢
9. `app.py:128-129` — qualquer exceção → `"Erro ao processar GEDCOM: {e}"`, `success=False`. 🟢

> **Detalhe de contrato:** a mensagem de sucesso usa o **nome original enviado pelo cliente** (`gedcom_file.filename`), enquanto o campo `gedcom_filename` leva o **nome armazenado** (chave + nome visível). São duas coisas diferentes, de propósito: uma é para o operador reconhecer o arquivo, a outra é para o sistema endereçá-lo. 🟢

### Núcleo — parsing e publicação (`gedcom_parser.py:50-69`)

1. `:56` — `new_people = {ref_id(i.xref_id): i for i in parser.records0("INDI")}`. 🟢
2. `:57` — `new_families = {ref_id(f.xref_id): f for f in parser.records0("FAM")}`. 🟢
3. `:59-63` — `build_graph_from_parser(...)` devolve `(novo_grafo, novo_child_to_family)`. 🟢
4. `:65-66` — **publicação assimétrica**: `people.clear()` + `people.update(new_people)` (idem `families` e `child_to_family`); `graph` é **reatribuído**. 🟢
5. `:67` — `versao` é incrementado. 🟢
6. `:68` — `all_names = sorted([get_name(p) for p in people.values()])`. 🟢

### Núcleo — construção do grafo (`gedcom_parser.py:18-48`)

1. `:19-20` — cria `nx.Graph()` e `child_to_family = {}`. 🟢
2. `:22-23` — um nó por pessoa: `type="person"`, `label=get_name(person)`. 🟢
3. `:25-27` — para cada `FAM`: sem `xref_id` → `continue`; senão nó `type="family"`, `label="Familia"`. 🟢
4. `:30-38` — varre os sub-registros: `HUSB` → marido; `WIFE` → esposa; cada `CHIL` → acumula **e** registra `child_to_family[cid].append(fam_id)`. 🟢
5. `:40-46` — cria aresta para marido, esposa e cada filho **apenas se o nó existir**. 🟢

## Fluxos Alternativos

| Condição | Comportamento | Conf. |
| --- | --- | --- |
| Sem o campo `gedcom` | `"Nenhum arquivo GEDCOM enviado."`, nada é gravado | 🟢 |
| `filename` vazio | `"Nenhum arquivo selecionado."`, nada é gravado | 🟢 |
| Conteúdo vazio | `"Arquivo não reconhecido como GEDCOM: arquivo vazio."` | 🟢 |
| Conteúdo com byte NUL | `"Arquivo não reconhecido como GEDCOM: conteudo binario."` | 🟢 |
| Conteúdo sem `0 HEAD` | `"Arquivo não reconhecido como GEDCOM: não começa com a declaração 0 HEAD."` | 🟢 |
| Corpo acima de 16 MB | `HTTP 413` com `"Arquivo maior que o limite de 16 MB."`; o corpo **não** é lido | 🟢 |
| Mesma chave já em disco | Arquivo **não** é reescrito; o fluxo segue normalmente | 🟢 |
| Exceção no parse | `"Erro ao processar GEDCOM: {e}"`; as globais **não** são tocadas, porque a mutação só ocorre depois do parse bem-sucedido | 🟢 |
| `FAM` sem `xref_id` | Ignorada por completo, sem erro | 🟢 |
| `HUSB`/`WIFE`/`CHIL` apontando para xref inexistente | A aresta é descartada **em silêncio**; a referência permanece nos sub-registros | 🟢 |
| Requisição de análise com chave ausente | `"Erro: Arquivo GEDCOM não encontrado."` | 🟢 |
| Requisição de análise com chave fora da forma, ou arquivo removido | `"Erro: Arquivo '{valor}' não existe mais."` | 🟢 |
| Nome visível vazio ou só pontos | Vira `arvore.ged` | 🟢 |
| Nome visível sem extensão | Recebe `.ged` | 🟢 |

## Dependências

| Dependência | Versão | Como usa | Conf. |
| --- | --- | --- | --- |
| **ged4py** | 0.5.2 | `GedcomReader` para `records0("INDI")`/`records0("FAM")` e acesso a sub-registros | 🟢 |
| **networkx** | 3.6.1 | `nx.Graph`, `add_node`, `add_edge`, `has_node` | 🟢 |
| **Flask** | 3.1.3 | Rota única, `request.files`, `request.form`, `render_template`, `MAX_CONTENT_LENGTH` | 🟢 |
| **werkzeug** | transitiva | `RequestEntityTooLarge` para o handler de `413` | 🟢 |
| **waitress** | 3.0.2 | Servidor de produção do bloco de entrada | 🟢 |
| **Sistema de arquivos** | — | `src/uploads/`, criada no **import** pela mesma função que a resolve | 🟢 |
| Units internas | — | **Nenhuma.** Esta é a base: as outras duas dependem dela, não o contrário | 🟢 |

## Decisões de Design Identificadas

| Decisão | Evidência no código | Confiança |
| --- | --- | --- |
| **Chave derivada do conteúdo**, e não UUID aleatório, porque o formulário devolve o valor no `POST` seguinte | `validate.py:13-16`, `:68-70` | 🟢 |
| **Validação da chave por forma fechada**, e não por lista negra | `validate.py:28-32` | 🟢 |
| **Teto de corpo aplicado antes de ler** — a ausência dele fazia o multipart inteiro ser gravado em disco antes de qualquer verificação | `app.py:29-32` | 🟢 |
| **A extensão original é preservada**, e não fixada em `.ged` — fixá-la quebrou o CSV de DNA | `validate.py:55-58` | 🟢 |
| **Mutação *in place*** para `people`/`families`/`child_to_family`, e **reatribuição** para `graph` | `gedcom_parser.py:65-66`; `path_finding.py:38` | 🟢 |
| **`versao` como sinal de invalidação**, porque `id()` não muda com mutação *in place* | `gedcom_state.py:30`; `documentary_relationship.py:185-202` | 🟢 |
| **Pasta de upload ancorada no arquivo do app**, e não relativa ao diretório corrente | `app.py:42-57` | 🟢 |
| **O retorno é o caminho completo**, nunca o nome — nome e caminho não são intercambiáveis | `app.py:75-84` | 🟢 |
| **`get_name` não trata formato vazio** — é paridade com o oráculo, não descuido | `gedcom_state.py:45-52` | 🟢 |
| Validação de conteúdo **estreita de propósito**: só o cabeçalho; a gramática fica com o `ged4py` | `validate.py:93-95` | 🟢 |
| **O CSV não passa por validação de conteúdo** — só o GEDCOM passa | `app.py:86` | 🟢 |
| Estado global mutável, singleton por processo, sem injeção de dependência | `gedcom_state.py:19-30` | 🟢 |

## Estado Interno

| Campo | Onde | Como evolui | Conf. |
| --- | --- | --- | --- |
| `people` | `gedcom_state.py:20` | `clear()` + `update()` a cada carga — **identidade de objeto preservada** | 🟢 |
| `families` | `gedcom_state.py:21` | idem | 🟢 |
| `child_to_family` | `gedcom_state.py:23` | idem | 🟢 |
| `graph` | `gedcom_state.py:22` | **Reatribuído** a cada carga | 🟢 |
| `versao` | `gedcom_state.py:30` | `+= 1` a cada carga | 🟢 |
| Arquivo enviado | `src/uploads/` | Imutável: mesma chave **não** é reescrita; nunca é apagado pelo sistema | 🟢 |

> **Não há sessão.** O estado sobrevive à requisição porque vive no **processo**, e não porque está associado a um usuário. É a chave de conteúdo, devolvida ao navegador, que faz o papel de identificador de continuidade — e ela **não é segredo nem tem verificação de propriedade** (`permissions.md` §4). 🟢

## Observabilidade

- **Nenhum `logging`, métrica ou trace é emitido pela unit.** 🔴
- Erros de parse chegam ao usuário apenas como `message` no template (`app.py:129`). 🟢
- A única saída textual do sistema é o `print` de inicialização do servidor (`app.py:259-263`). 🟢
- A instrumentação de desenvolvimento (oráculo congelado, harness de paridade, goldens) vive em `_reversa_sdd/` e **não faz parte da aplicação**. 🟢

## Riscos e Lacunas

- 🔴 **`"Sem Nome"` é praticamente inalcançável a partir de registros `INDI` reais.** O `ged4py` entrega um objeto `Name` cujo `.format()` é `''` mesmo quando a tag `NAME` é removida; e um registro sem o atributo `name` faz o `ged4py` levantar `AttributeError`, que o curto-circuito `person and` nunca alcança. O literal teve **zero ocorrências** medidas em 55.523 nomes reais. Não é bug: é detalhe de contrato que **precisa ser preservado**. 🟢
- 🔴 **A chave de conteúdo não é segredo e não tem dono.** Quem a conhece carrega a árvore correspondente. Isso é o `BUG-20260929-BJJH`, mantido por **aceite de risco** com condição de reabertura nomeada (`adrs/18`). 🟢
- 🔴 **Estado global compartilhado, com 4 threads.** Duas requisições simultâneas podem trocar de árvore entre o parse e o uso (`L-16` em `domain.md` §7). Não medido. 🟡
- 🟡 **O CSV de DNA não passa por validação de conteúdo** (`app.py:86`): a assimetria em relação ao GEDCOM é coerente com a leitura tolerante (ADR-16), mas não há registro de que tenha sido decidida de propósito (`P-05`). 🟡
- 🟢 **`app.secret_key` — REMOVIDO em 2026-10-05 por decisão sua.** Não tinha consumidor: `flask.session` nunca foi importado e nenhum cookie era emitido. O literal estava versionado e seria a chave de forja de sessão caso alguém introduzisse `session` (`P-04`, fechada). Nenhum consumidor foi afetado. 🟢
- 🟡 **Sem validação de extensão ou tipo MIME** — decisão deliberada (`RISK-007`), para não rejeitar GEDCOM de exportador legítimo. 🟢
- 🟡 **Nada é persistido entre requisições**, exceto o arquivo: o GEDCOM é re-parseado a cada `POST`. Custo real, sem limite medido (`L-21`). 🟢
- 🟢 **Resolvido em 2026-09-30:** `Family`, `GenealogyGraph` e `DNAGroup` foram **removidas** por serem arquitetura abandonada (`adrs/09`). O que hoje faz o papel de "modelo" são o `dict` e o objeto do `networkx`. 🟢

---

*Gerado pelo Reversa-Writer em 2026-10-05 (re-extração, nível completo).*

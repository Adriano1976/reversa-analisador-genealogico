# upload-gedcom, Design Técnico

> Unit do tipo **endpoint** — `POST /` com `action=upload_gedcom`.
> Nível de documentação: **Essencial**. Escala: 🟢 CONFIRMADO | 🟡 INFERIDO | 🔴 LACUNA
> Re-extração de 2026-09-30. Substitui o design de 2026-08-03.

## Interface

### Endpoint HTTP (formulário multipart)

| Método | Caminho | Entrada | Saída | Status codes |
|--------|---------|---------|-------|--------------|
| GET | `/` | — | `index.html` com formulário de upload | 200 🟢 |
| POST | `/` | `action=upload_gedcom`, arquivo no campo `gedcom` | `index.html` com `gedcom_filename`, `all_names` e `message` | 200 sempre — **não há redirect nem 4xx**; o erro vira mensagem na tela 🟢 |

> O sistema **nunca** responde 400/500 ao usuário por erro de negócio: toda falha é renderizada como HTML com `success=False`. A única exceção não tratada seria um erro fora dos blocos `try`. 🟢

### Símbolos do núcleo

| Símbolo | Assinatura | Retorno | Observação |
|---------|-----------|---------|------------|
| `load_gedcom_and_build_graph` | `(file_path: str)` | `list[str]` | Substitui as globais `people`, `families`, `graph`, `child_to_family` in-place 🟢 |
| `build_graph_from_parser` | `(people_dict: dict, parser)` | `(nx.Graph, dict)` | Grafo não-direcionado + índice filho→famílias 🟢 |
| `get_name` | `(person)` | `str` | `person.name.format()` se `person and person.name`; senão `"Sem Nome"` 🟢 |
| `ref_id` | `(val)` | `str` | `getattr(val, "xref_id", val)` — aceita objeto ged4py ou string 🟢 |
| `ensure_dirs` | `()` | `None` | `os.makedirs("uploads", exist_ok=True)` 🟢 |
| `strip_bad_utf` | `(s)` | `str` | Mapa de 18 pares de mojibake + remoção por regex 🟢 |
| `demojibake` | `(s)` | `str` | Round-trip `latin1 → utf-8`, condicional 🟢 |

### Contrato de estado global

| Global | Tipo | Chave → Valor |
|--------|------|---------------|
| `people` | `dict` | `xref_id` → registro `INDI` do ged4py 🟢 |
| `families` | `dict` | `xref_id` → registro `FAM` do ged4py 🟢 |
| `graph` | `nx.Graph \| None` | nós de pessoa (`type="person"`) e de família (`type="family"`) 🟢 |
| `child_to_family` | `dict[str, list[str]]` | `xref_id` do filho → lista de famílias onde aparece como `CHIL` 🟢 |

## Fluxo Principal

### Camada de rota (`app.py:19-34`)

1. `app.py:20-22` — `POST` com `action == "upload_gedcom"`. 🟢
2. `app.py:23-24` — se `"gedcom" not in request.files` → renderiza com `"Nenhum arquivo GEDCOM enviado."`, `success=False`. 🟢
3. `app.py:25-27` — se `gedcom_file.filename == ''` → `"Nenhum arquivo selecionado."`. 🟢
4. `app.py:29-30` — salva em `uploads/<filename>`. 🟢
5. `app.py:31` — chama `load_gedcom_and_build_graph(gedcom_path)`. 🟢
6. `app.py:32` — renderiza com `gedcom_filename`, `all_names` e `"Arquivo '{nome}' carregado!"`. 🟢
7. `app.py:33-34` — qualquer exceção → `"Erro ao processar GEDCOM: {e}"`, `success=False`. 🟢

### Núcleo — parsing e publicação (`upload.py:82-100`)

1. `upload.py:88` — abre `GedcomReader(file_path)` como context manager. 🟢
2. `upload.py:89` — `new_people = {ref_id(i.xref_id): i for i in parser.records0("INDI")}`. 🟢
3. `upload.py:90` — `new_families = {ref_id(f.xref_id): f for f in parser.records0("FAM")}`. 🟢
4. `upload.py:91` — `build_graph_from_parser(new_people, parser)` devolve `(new_graph, new_child_to_family)`. 🟢
5. `upload.py:95-98` — **publicação in-place**: `people.clear(); people.update(new_people)`, idem para `families` e `child_to_family`; e `graph = new_graph` (rebind, não mutação — ver Decisões). 🟢
6. `upload.py:99` — `all_names = sorted([get_name(p) for p in people.values()])`. 🟢
7. `upload.py:100` — devolve `all_names`. 🟢

### Núcleo — construção do grafo (`upload.py:50-79`)

1. `upload.py:52-53` — cria `nx.Graph()` e `c2f = {}`. 🟢
2. `upload.py:54-55` — para cada pessoa, `add_node(pid, label=get_name(person), type="person")`. 🟢
3. `upload.py:56-60` — para cada `FAM`: se `xref_id` ausente, `continue`; senão `add_node(fam_id, label="Familia", type="family")`. 🟢
4. `upload.py:63-71` — varre `sub_records` da família: `HUSB` → `husband_id`; `WIFE` → `wife_id`; `CHIL` → acumula em `child_ids` **e** registra `c2f[cid].append(fam_id)`. 🟢
5. `upload.py:72-78` — cria aresta para marido, esposa e cada filho, **apenas se o nó existir** (`g.has_node`). 🟢
6. `upload.py:79` — devolve `(g, c2f)`. 🟢

## Fluxos Alternativos

- **Sem arquivo no campo `gedcom`:** renderiza erro, não grava nada. 🟢
- **Arquivo com nome vazio:** renderiza erro, não grava nada. 🟢
- **Exceção no parse (GEDCOM malformado):** a exceção sobe do `with` e é capturada em `app.py:33`; as globais **não** são tocadas, porque a mutação só ocorre depois do parse bem-sucedido (`upload.py:95`). Estado anterior preservado. 🟢
- **`FAM` sem `xref_id`:** ignorada, sem erro. 🟢
- **Referência para pessoa inexistente (`HUSB`/`WIFE`/`CHIL` órfão):** a aresta é descartada em silêncio por `g.has_node`; a referência permanece nos `sub_records` e pode reaparecer via `child_to_family`. 🟡
- **Pessoa sem o atributo `name`:** `get_name` devolve `"Sem Nome"`. 🔴 Inalcançável a partir de registros `INDI` reais (ver Riscos e Lacunas). 🟢
- **Recarga de árvore:** substituição integral; nenhum resíduo da anterior. 🟢

## Dependências

| Dependência | Versão | Como usa |
|-------------|--------|----------|
| **ged4py** | 0.5.2 | `GedcomReader` para `records0("INDI")` / `records0("FAM")` e acesso a `sub_records` 🟢 |
| **networkx** | 3.6.1 | `nx.Graph`, `add_node`, `add_edge`, `has_node` 🟢 |
| **Flask** | 3.1.3 | Rota única, `request.files`, `render_template` 🟢 |
| **Depende de unit interna: nenhuma** | — | `upload` é a base; as outras units dependem dele, não o contrário 🟢 |
| **Sistema de arquivos** | — | `uploads/`, criada no boot por `os.makedirs(..., exist_ok=True)` 🟢 |

## Decisões de Design Identificadas

| Decisão | Evidência no código | Confiança |
|---------|---------------------|-----------|
| Estado em memória global, singleton por processo, sem injeção de dependência | `upload.py:16-19` | 🟢 |
| **Mutação in-place (`clear()` + `update()`) em vez de rebind** para `people`, `families` e `child_to_family`, para que referências importadas por outros módulos continuem válidas | `upload.py:92-98` (comentário explícito) | 🟢 |
| **`graph` é exceção: sofre rebind**, e por isso `find_indirect_path` o importa *dentro* da função | `upload.py:97` vs `path_search.py:131` | 🟢 |
| Re-parse integral a cada POST, sem cache | `app.py:31`, `:42` | 🟢 |
| Arquivo salvo com o nome original do cliente, sem sanitização | `app.py:29` | 🟢 |
| Pasta de upload fixa, criada no boot | `upload.py:21`, `:24-25` | 🟢 |
| Nenhuma validação de extensão, tipo ou tamanho | `app.py:23-30` | 🟢 |

## Estado Interno

Preenchido por este fluxo e mantido para os seguintes:

| Campo | Onde vive | Como evolui |
|-------|-----------|-------------|
| `people` | `upload.py:16` | `clear()` + `update()` a cada carga 🟢 |
| `families` | `upload.py:17` | `clear()` + `update()` a cada carga 🟢 |
| `graph` | `upload.py:18` | Rebind a cada carga 🟢 |
| `child_to_family` | `upload.py:19` | `clear()` + `update()` a cada carga 🟢 |
| Arquivo `.ged` | `uploads/` | Sobrescrito se o nome colidir 🟢 |

> **Não há sessão.** O estado sobrevive à requisição porque vive no processo, não porque está associado a um usuário. Qualquer visitante subsequente vê a última árvore carregada. 🟢

## Observabilidade

- Nenhum `logging`, métrica ou trace é emitido pela unit. 🔴
- Erros de parse chegam ao usuário como `message` no template (`app.py:34`). 🟢
- A instrumentação de desenvolvimento (oráculo congelado, harness de paridade, goldens) vive em `_reversa_sdd/` e **não faz parte da aplicação**. 🟢

## Riscos e Lacunas

- 🔴 **`"Sem Nome"` é inalcançável a partir de `INDI` reais.** O `ged4py` entrega um objeto `Name` cujo `.format()` é `''` mesmo quando a tag `NAME` é removida; e um registro sem o atributo `name` faz o `ged4py` levantar `AttributeError`, que o curto-circuito `person and` nunca alcança. Consequência: o literal tem **0 ocorrências** medidas em 55.523 nomes reais. Não é bug, é detalhe de contrato que precisa ser preservado. 🟢
- 🔴 **Sem validação de extensão/tamanho.** Limitação **aceita pelo usuário** para uso local (`questions.md#3`); documentar como limitação, não como pendência.
- 🔴 **Colisão de nome sobrescreve.** Mesma decisão acima. `BUG-20260929-QMLY-upload-sem-limites` registra a lacuna.
- 🔴 **Estado global compartilhado.** Sem isolamento entre usuários ou requisições; quebra em deploy multi-worker. Risco registrado em `migration/risk_register.md`.
- 🟡 **`secret_key` hardcoded** (`app.py:11`) — irrelevante hoje porque não há sessão, mas é um cheiro.
- 🟢 **RESOLVIDO em 2026-09-30 — entidades decorativas removidas.** `Family`, `GenealogyGraph` e `DNAGroup` foram **removidas** de `reconstructed/domain.py` por decisão do usuário (`questions.md#pergunta-3`): arquitetura abandonada, não preparação futura. Nenhuma era instanciada em caminho de produção. A remoção levou `domain.py` de 115 para 84 linhas e exigiu retirar 9 testes de `tests/test_domain.py` que exercitavam as classes extintas. Suíte: 95 → 86 itens coletados.
  - O que **permanece** em `domain.py` é apenas o que é de fato consumido: `strip_bad_utf` e `demojibake`.
  - A contradição do `networkx.MultiGraph` no docstring de `GenealogyGraph` (`domain.py:77`) **desapareceu junto com a classe**.

---

*Gerado pelo Reversa-Writer em 2026-09-30 (re-extração).*

# Data Delta: desacoplamento de nós e gerações virtuais

> Identificador: `029-desacoplamento-de-nos`
> Data: `2026-10-18`
> Modelo extraído de referência: `_reversa_sdd/erd-complete.md` (42 estruturas, 6 tabelas),
> `_reversa_sdd/data-dictionary.md` §4 (estruturas em memória) e §11 (árvore GEDCOM).

## 1. Resumo

**Nenhuma estrutura persistente nova, nenhuma coluna, nenhuma migração.** Tudo o que a feature cria
vive em memória, dentro de uma cópia do grafo, e morre com a chamada. O banco continua com as 6
tabelas atuais e **nenhuma linha é escrita**.

O que muda, em três linhas:

1. **Entram dois tipos de nó sintético** no grafo em memória (`virtual` e `virtual-family`).
2. **Entra uma chave aditiva** no retorno de `validar_arquivos`: `documental`, por comparação.
3. **Entra uma estrutura de saída** (`sugestao`), com o contrato de §4.7 do requirements.

## 2. Entradas

| Entrada | Tipo | Origem | Já existe? |
|---------|------|--------|------------|
| `arvore` | `tuple(people, families, graph, child_to_family)` | `parsers.gedcom_parser.carregar_arvore` | sim — só é lida |
| `documental` | `dict` | `core.documentary_relationship.documentary_relationship` | sim — é o dicionário completo |
| `resultado` | `dict` | `core.validator.validar_comparacao` | sim — contrato de §4.5 da `028` |
| `doador_id` | `str` | raiz resolvida por nome | sim |

> **Por que duas entradas e não uma:** `resultado` tem `status`, `codigos`, `mrca_estimado` e
> `geracoes_documentais`, mas **não** tem `path.ids` nem `evidence`. Sem `documental` não há como
> saber onde está a junção. Ver `roadmap.md` D-04.

## 3. Saída

Uma `sugestao` por comparação com status de erro. Contrato completo:

| Campo | Tipo | Observação |
|-------|------|------------|
| `natureza` | `"sugestao"` | literal fixo, para a borda nunca confundir com resultado |
| `status_origem` | `str` | o status que disparou |
| `grafo` | `nx.Graph \| None` | a cópia transformada |
| `doador` | `{"id", "nome"}` | nunca alterado |
| `ancestral` | `{"id", "nome", "ano"}` | `ano` pode ser `None` |
| `juncao` | `{"familia_id", "pai_id", "filho_id", "lado", "aresta_removida"}` | `None` sem sugestão |
| `hiato` | `{"calculado", "aplicado", "por_lado"}` | `por_lado` = `{"doador": k, "match": k}` |
| `geracoes_virtuais` | `list[{"id", "label", "lado", "ordem", "nascimento_estimado"}]` | `nascimento_estimado` = `{"ano_min", "ano_max"}` |
| `familias_virtuais` | `list[str]` | ids das famílias sintéticas |
| `nos_adicionados` | `list[str]` | ordem determinística |
| `arestas_adicionadas` | `list[tuple[str, str]]` | pares ordenados |
| `arestas_removidas` | `list[tuple[str, str]]` | pares ordenados |
| `ramo_base` | `{"ids", "arestas", "intacto"}` | `ids` inclui o ancestral |
| `justificativa` | `str` | uma frase para o operador |
| `avisos` | `list[{"codigo", "mensagem"}]` | ordem de §4.4 do requirements |

## 4. Atributos dos nós sintéticos

Nó de pessoa virtual:

| Atributo | Valor | Por quê |
|----------|-------|---------|
| `label` | `"Geração <k>"` | rótulo honesto: posição, não pessoa |
| `type` | `"virtual"` | distingue de `"person"` em qualquer travessia |
| `origem` | `"estimado"` | marca o dado como derivado |
| `justificativa` | texto curto | por que aquela geração foi inserida |
| `nascimento_estimado` | `{"ano_min": int, "ano_max": int}` | faixa, nunca data exata |

**Não existem** `name`, `sex`, `birth`, `death` nesses nós. É a diferença entre "posição sugerida" e
"pessoa inventada" (RN-11), e é o que impede a sugestão de virar dado falso ao ser lida por outro
programa.

Nó de família virtual:

| Atributo | Valor |
|----------|-------|
| `label` | `"Familia virtual"` |
| `type` | `"virtual-family"` |

## 5. Topologia exata do exemplo do requirements

Doador nascido em 1985, ancestral em 1650, `a_up = 2`, `k = 4` (cM estima 6 gerações).

**Antes** (3 pessoas, 2 famílias):

```
Donor — F1 — Pai
          |
          F2 — MRCA
```

**Depois** (7 pessoas, 6 famílias), com a aresta `F2—MRCA` removida:

```
Donor — F1 — Pai — F2
                     |
                    V4 — Fv4 — V3 — Fv3 — V2 — Fv2 — V1 — Fv1 — MRCA
```

As quatro famílias `Fv1..Fv4` são sintéticas; `F2` é a família que já existia no topo do ramo e é
reaproveitada como última ligação. Contando as arestas: cada pessoa virtual tem grau 2 (uma família
acima, uma abaixo), e o grafo continua bipartido — nenhuma aresta pessoa↔pessoa é criada.

## 6. Emenda na `028`: chave `documental`

`validar_arquivos` ganha o parâmetro `incluir_documental: bool = False`. Com `True`, cada item de
`comparacoes` recebe a chave `documental` — **o mesmo objeto** já montado no laço, não uma cópia.

| Situação | Antes | Depois |
|----------|-------|--------|
| Chamada sem o parâmetro | 6 chaves por comparação | **6 chaves, idênticas** — contrato preservado |
| Chamada com `incluir_documental=True` | — | 7 chaves; a nova é `documental` |

Nenhum teste da `028` compara o conjunto exato de chaves (verificado em
`tests/test_validacao_de_arquivos.py`: as asserções são por chave), então a emenda é segura.

## 7. Impacto no ERD e no banco

| Item | Impacto |
|------|---------|
| Tabelas novas | nenhuma |
| Colunas novas | nenhuma |
| Índices | nenhum |
| Migração | nenhuma |
| Escrita no banco | nenhuma |
| `analysis_person` / `match_result` / `match_path_node` | intocadas |
| Retenção de dado pessoal (`L-29`) | inalterada — a feature **não** grava nada |

`_reversa_sdd/erd-complete.md` continua com 42 estruturas. As estruturas em memória que a feature
acrescenta (`sugestao`, `juncao`, `geracoes_virtuais`) não entram no ERD porque não são domínio
persistente — são payload de uma chamada, como `MrcaEstimado` na `028`.

## 8. Compatibilidade e migração

n/a. Não há dado a migrar. A única alteração de contrato é aditiva e desligada por padrão; a
verificação é o teste que compara o retorno antigo com o novo sem o parâmetro.

## 9. O que **não** muda

- `people`, `families`, `graph` e `child_to_family` recebidos — lidos, nunca mutados.
- `COMPATIVEL`, `POSSIVEL`, `CONFLITANTE`, `INCONCLUSIVO` — nem texto, nem classe CSS.
- `VALIDADO`, `INCONCLUSIVO`, `ERRO CRONICO / QUEBRA DE LINHA` — literais preservados.
- `core.validator`, `core.documentary_relationship`, `core.path_finding` — nenhuma linha alterada.
- `app.py`, template, CSS, `init.sql`, `requirements.txt` — intocados.

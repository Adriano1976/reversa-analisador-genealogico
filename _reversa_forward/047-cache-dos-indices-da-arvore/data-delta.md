# Data Delta: cache dos índices derivados da árvore

> Identificador: `047-cache-dos-indices-da-arvore`
> Data: `2026-10-24`
> Modelo extraído: `_reversa_sdd/erd-complete.md` e `_reversa_sdd/data-dictionary.md`

## 1. Resumo

Nenhum campo persistido nasce, muda ou morre. A feature acrescenta **duas estruturas em
memória**, ambas com vida limitada ao processo:

1. `CACHE_DE_ARVORES` — a árvore parseada, no adaptador de portas.
2. `_índices_de_matching` — atributo preso ao grafo da árvore.

## 2. Estrutura nova: `CACHE_DE_ARVORES`

| Aspecto | Valor |
|---|---|
| Onde vive | `src/ports/adaptadores.py`, em `CarregadorDeArvoresGedcom` |
| Tipo | `OrderedDict` com teto (LRU) |
| Chave | `(caminho absoluto, mtime_ns, tamanho)` |
| Valor | a tupla-árvore `(people, families, graph, child_to_family)` |
| Teto padrão | 1 |
| Configuração | `ANALISADOR_CACHE_DE_ARVORE` (liga/desliga) e `ANALISADOR_CACHE_DE_ARVORE_CAPACIDADE` (teto) |
| Persiste | não — morre com o processo |
| Invalidação | `mtime_ns` ou tamanho diferentes; arquivo ausente |
| Memória | ~340 MB por árvore (medido) |

## 3. Estrutura nova: `_índices_de_matching`

| Aspecto | Valor |
|---|---|
| Onde vive | atributo do objeto `graph` (`arvore[2]`), em `core/matching.py` |
| Tipo | tupla `(ged_index, surname_index, features)` |
| Chave | o próprio objeto do grafo — nenhuma chave derivada de conteúdo |
| Persiste | não — morre com a árvore |
| Invalidado por | nada além da morte da árvore; a árvore já invalida pelo arquivo |
| Memória | ~31 MB (medido) |

Conteúdo: 17.590 chaves de nome, 6.397 sobrenomes e 19.403 fichas de atributos.

## 4. O que muda nos artefatos da extração

| Artefato | Seção | Tipo de impacto | Delta |
|---|---|---|---|
| `erd-complete.md` | `#7` (inventário das 42 estruturas) | componente-novo | Entra `CACHE_DE_ARVORES`; a contagem de 42 estruturas sobe para 43 |
| `architecture.md` | `#4` (quadro "onde o dado vive") | delta-de-dados | Memória de módulo: 1 → 2 estruturas |
| `data-dictionary.md` | entradas de memória | delta-de-dados | Entrada nova para `CACHE_DE_ARVORES` e para o atributo do grafo |
| `architecture.md` | `#1` | regra-alterada | "Não há cache entre requisições" deixa de valer |

## 5. Migração

n/a. Não há dado persistido, nem esquema, nem versão de formato. A estrutura nasce vazia e morre
com o processo; desligar a variável de ambiente devolve o comportamento anterior sem resíduo.

## 6. Privacidade

A árvore em memória contém dado pessoal de terceiros — é a mesma árvore que já existia durante a
requisição, agora por mais tempo. Ela **não** é escrita em disco, não é logada e não é serializada.
O `/reversa-sync` deve registrar esse prolongamento de retenção em memória.

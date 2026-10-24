# Legacy Impact: índice de nomes sem colisão entre árvores

> Feature: `048-indice-de-nomes-sem-colisao`
> Data: `2026-10-24`
> Política de edição do legado: `allowLegacyEdits: true`, com `src/**` e `tests/**` liberados

## Arquivos afetados

| Arquivo afetado | Componente | Tipo | Severidade | Justificativa |
|---|---|---|---|---|
| `src/core/homonimos.py` | `homonimos` (units `analise-dna` e `busca-caminho`) | `regra-alterada` | **HIGH** | O índice de nomes deixa de ser cache de módulo e passa a viver preso ao grafo da árvore |
| `src/core/homonimos.py` (`_INDICE_DE_NOMES`, `_chave_de`) | `CACHE_DE_NOMES` | `componente-extinto` | MEDIUM | O cache de módulo e a chave de invalidação foram removidos |
| `tests/test_indice_de_nomes_do_documental.py` | — (teste) | `componente-novo` | LOW | Arquivo reescrito: 6 guardas da implementação antiga saíram, 7 testes do invariante novo entraram |

## Diff conceitual por componente

**`_indice_por_nome`.** Antes: comparava `(len, primeira chave, última chave)` com o global e
reconstruía o mapa quando a chave mudava. Agora: procura o mapa num atributo do grafo da árvore,
constrói se não existir e prende o resultado ali. Não há chave, não há global, não há publicação
em dois tempos — a corrida que a transformação de 2026-10-24 fechou com uma tupla atômica deixa
de ter onde acontecer.

**`_chave_de`.** Removida. A função existia só para derivar a chave que agora não existe.

**Testes.** O arquivo anterior lia o módulo por AST para garantir que a tupla `_INDICE_DE_NOMES`
fosse publicada de uma vez. Com o estado removido, essas guardas perderam objeto; o arquivo passou
a guardar o invariante novo (cada árvore tem o seu mapa) e a proibir a volta do estado de módulo.

## Regras preservadas

- Regras de matching, limiares e desempate determinístico.
- Conteúdo e ordem do dossiê de homônimos (`exact_count`, fichas, campos).
- `homonym_dossier` como autoridade única sobre "mesmo nome" (acento e mojibake).
- Regra 2 do adendo `bug-BUG-20261021-7O7V-v001`: derivado nasce e morre com a árvore, sem chave
  que possa colidir — agora cumprida também pelo índice de nomes.
- `L-25` (ordem sensível a `PYTHONHASHSEED` em `common_ancestors`): **intocada**.

## Regras modificadas

- **`CACHE_DE_NOMES`** deixa de ser memória de módulo e passa a ser memória da árvore.
- **`L-24`** (colisão da chave do cache de nomes) deixa de existir: não há chave para colidir.
- **A corrida entre requisições** sobre o índice deixa de existir por construção, e não por
  publicação atômica.

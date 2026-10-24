# Adendo: o índice de nomes deixou de ser estado de módulo

> Identificador: `048-indice-de-nomes-sem-colisao`
> Data: `2026-10-24`
> Cenário: **legado** (âncora em `_reversa_sdd/domain.md#7-lacunas` e `_reversa_sdd/busca-caminho/design.md`)

## Vigência

Vigente desde 2026-10-24.

## Resumo da entrega

O índice de nomes do módulo de homônimos era o **último estado de módulo do núcleo**. Ele era
chaveado por `(quantidade de pessoas, primeiro xref, último xref)`, e duas árvores com o mesmo
número de pessoas e os mesmos xrefs extremos produziam a **mesma chave** — o dossiê da segunda
citava `xref` da primeira e degradava para `"Sem Nome"`, sem exceção e sem aviso. O defeito foi
confirmado por execução em 2026-10-10 e estava registrado como a lacuna `L-24`.

A correção **não** foi endurecer a chave: foi tirá-la de cena. O mapa passou a ser preso ao
**grafo da árvore**, como `fichas_da_pessoa._indice_de_filhos` e os índices de matching da feature
047. Sem estado compartilhado, não há colisão possível; sem chave, não há o que derivar — e derivar
dos nomes custaria a mesma varredura que construir o índice.

**10 de 10 ações concluídas.** Suíte: **1656 passed, 9 skipped**. O dossiê de referência ficou
idêntico (mesmos ids, ordem, `exact_count` e os 13 campos de ficha). Custo: três consultas na mesma
árvore percorrem as pessoas **uma vez** (3 chamadas de `get_name`, uma por pessoa).

**Nota de retenção (privacidade).** Aqui a mudança é o oposto da feature 047: o mapa de nomes
deixa de sobreviver à requisição. Ele só permanece em memória se a própria árvore permanecer, e
isso só acontece com o cache da 047 ligado. É **redução** de retenção, não aumento.

## Impacto por artefato da extração

| Artefato | Seção | Tipo de impacto | Delta |
|---|---|---|---|
| `_reversa_sdd/domain.md` | §7 (lacunas) | `regra-removida` | `L-24` deixa de existir: não há chave para colidir e o índice não é compartilhado entre árvores |
| `_reversa_sdd/architecture.md` | §4 (onde o dado vive) | `delta-de-dados` | A memória de módulo cai de **2** para **1** estrutura (`CACHE_DE_ARVORES`); `CACHE_DE_NOMES` passa para a linha da árvore |
| `_reversa_sdd/erd-complete.md` | §7 (inventário das 42 estruturas) | `delta-de-dados` | `CACHE_DE_NOMES` muda da coluna "módulo" para "árvore", ao lado de `CHILD_TO_FAMILY` |
| `_reversa_sdd/data-dictionary.md` | entrada do cache de nomes | `delta-de-dados` | Some a chave `(len, primeira, última)`; o mapa é atributo do grafo e morre com a árvore |
| `_reversa_sdd/busca-caminho/design.md` | §Riscos e Lacunas | `regra-removida` | O risco de contaminação entre árvores deixa de existir |

## Regras sob vigilância

`W001`, `W002`, `W003`, `W004` — em
`_reversa_forward/048-indice-de-nomes-sem-colisao/regression-watch.md`.

## Fontes

- `_reversa_forward/048-indice-de-nomes-sem-colisao/requirements.md`
- `_reversa_forward/048-indice-de-nomes-sem-colisao/roadmap.md`
- `_reversa_forward/048-indice-de-nomes-sem-colisao/legacy-impact.md`
- `_reversa_forward/048-indice-de-nomes-sem-colisao/regression-watch.md`
- `_reversa_forward/048-indice-de-nomes-sem-colisao/progress.jsonl`
- `_reversa_forward/048-indice-de-nomes-sem-colisao/evidence/depois.md`
- `_reversa_forward/048-indice-de-nomes-sem-colisao/evidence/verificacoes.md`

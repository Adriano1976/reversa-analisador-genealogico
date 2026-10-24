# Data Delta: índice de nomes sem colisão entre árvores

> Identificador: `048-indice-de-nomes-sem-colisao`
> Data: `2026-10-24`
> Modelo extraído: `_reversa_sdd/erd-complete.md` e `_reversa_sdd/data-dictionary.md`

## 1. Resumo

Nenhum campo persistido nasce, muda ou morre. A estrutura `CACHE_DE_NOMES` **muda de dono**: deixa
de ser memória de módulo e passa a ser memória da árvore.

## 2. A estrutura `CACHE_DE_NOMES`

| Aspecto | Antes | Depois |
|---|---|---|
| Onde vive | variável de módulo em `core/homonimos.py` | atributo do grafo (`arvore[2]`) |
| Chave de invalidação | `(len, primeira chave, última chave)` | **nenhuma** — a vida do mapa é a vida da árvore |
| Tempo de vida | processo inteiro, trocado a cada GEDCOM | a árvore; com o cache da 047, o mesmo que ela |
| Colisão entre árvores | possível (defeito `L-24`) | impossível por construção |
| Conteúdo | `{nome normalizado: [xrefs]}` | igual |
| Custo de construção | ~0,9 s por 35 mil pessoas | igual, uma vez por árvore |
| Persistência | não | não |

## 3. Estruturas removidas

- `_INDICE_DE_NOMES` (variável de módulo).
- `_chave_de(people)` (função de chave).

## 4. O que muda nos artefatos da extração

| Artefato | Seção | Tipo de impacto | Delta |
|---|---|---|---|
| `_reversa_sdd/erd-complete.md` | `#7` (inventário) | `delta-de-dados` | `CACHE_DE_NOMES` sai da coluna "módulo" e entra na coluna "árvore" |
| `_reversa_sdd/architecture.md` | `#4` (onde o dado vive) | `delta-de-dados` | Memória de módulo: 2 → 1 estrutura (`CACHE_DE_ARVORES`); o índice passa para a linha da requisição |
| `_reversa_sdd/data-dictionary.md` | entrada do cache de nomes | `delta-de-dados` | Some a chave; o mapa é preso à árvore |
| `_reversa_sdd/busca-caminho/design.md` | `#riscos-e-lacunas` | `regra-removida` | A lacuna `L-24` deixa de existir |

## 5. Migração

n/a. Não há dado persistido nem esquema. A estrutura antiga morre com o processo.

## 6. Privacidade

O mapa contém nomes normalizados e `xrefs` — dado pessoal que já circulava na árvore. Ele deixa de
sobreviver à requisição, exceto quando a árvore sobrevive (cache da 047). É uma **redução** de
retenção em relação ao estado atual.

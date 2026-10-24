# Regression Watch: índice de nomes sem colisão entre árvores

> Feature: `048-indice-de-nomes-sem-colisao`
> Data: `2026-10-24`

## Itens sob vigilância

| ID | Origem (arquivo, seção) | Regra esperada após a mudança | Tipo de verificação | Sinal de violação |
|---|---|---|---|---|
| `W001` | `src/core/homonimos.py` | O módulo não declara `_INDICE_DE_NOMES`, não define `_chave_de` e não escreve em `global` | `ausência` | Qualquer um dos três reaparece no fonte |
| `W002` | `_reversa_sdd/domain.md#7-lacunas` (`L-24`) | Duas árvores de mesmo tamanho e mesmos xrefs extremos não compartilham o mapa | `presença` | Um nome exclusivo de uma árvore aparecer no mapa da outra |
| `W003` | `_reversa_sdd/busca-caminho/design.md#riscos-e-lacunas` | O dossiê de homônimos é idêntico ao de antes da mudança | `presença` | Ids, ordem, `exact_count` ou fichas diferentes |
| `W004` | `_reversa_sdd/data-dictionary.md` | O índice é construído uma vez por árvore | `presença` | Contagem de `get_name` crescendo a cada consulta |

## Histórico de re-extrações

## Arquivadas

## Observações

- `L-25` (ordem de `common_ancestors` sensível a `PYTHONHASHSEED`) continua aberto e fora desta
  feature; não confundir com `W002`.
- **Privacidade:** o mapa de nomes deixa de sobreviver à requisição. É uma **redução** de retenção
  em relação ao estado anterior — o oposto do que a feature 047 fez com a árvore.
- O custo de ~0,9 s por árvore não muda; ele só deixa de ser pago de novo quando a mesma árvore
  é reusada (com o cache da feature 047 ligado).

# Linha de base (antes da feature)

> Feature: `048-indice-de-nomes-sem-colisao`
> Data: `2026-10-24`
> Suíte: `1655 passed, 9 skipped`

## Dossiê de referência

Árvore sintética de 3 pessoas, com dois homônimos (`Joao Silva`, nascidos em 1900 e 1950) e uma
pessoa distinta (`Maria Souza`). Consulta: `homonym_dossier(arvore, "Joao Silva")`.

```json
{
  "exact_count": 2,
  "ids": ["@I1@", "@I2@"],
  "nomes": ["Joao Silva", "Joao Silva"],
  "ordem_dos_campos": ["birth", "birth_place", "birth_year", "children", "death",
                       "death_year", "family_as_child", "id", "name", "parent_names",
                       "parents", "sex", "spouses"]
}
```

## Como usar

Depois da mudança, o mesmo script e a mesma árvore têm de devolver **este** dossiê: mesmos ids,
mesma ordem, mesmo `exact_count` e as mesmas chaves de ficha. Qualquer diferença é mudança de
comportamento, não correção — e a feature não pode mudar comportamento.

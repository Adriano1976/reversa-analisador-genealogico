# T023 — Conferência de escopo

> Feature: `008-persistencia-postgres-docker` · Data: `2026-10-08` · Ação: `T023`
> (`RN-01`, `RN-10`, `W016`)

## O que foi conferido, e o resultado

| Verificação | Resultado |
|---|---|
| `src/core/`, `src/parsers/`, `src/reporting/`, `src/utils/` | **nenhum alterado** — `git status` vazio para os quatro |
| `pytest.ini` | **intocado** |
| `.gitignore` | **intocado** |
| `README.md` | **intocado** |
| `pyrefly.toml` | **intocado** |
| `.markdownlint-cli2.jsonc` | **intocado** |
| `_reversa_sdd/migration/` | **intocado** — os artefatos de migração continuam preservados sem regeneração desde 2026-09-28 |
| Algum índice, `CHECK` ou consulta começando por `owner_id`? | **não** |
| A assinatura de retorno do núcleo (`W016`) | **preservada** |

## A `RN-01` é verificável por `diff`, e não por afirmação

O comando:

```powershell
git status --short src/core src/parsers src/reporting src/utils
```

devolveu **vazio**. É a prova de que a persistência é camada de saída: **nenhum módulo do
núcleo conhece o banco**, porque nenhum arquivo do núcleo foi tocado. A guarda automática que
a feature 006 deixou — o núcleo não importar `application/` nem `ports/` — continua valendo
pelo mesmo motivo: nada foi acrescentado lá para violá-la.

E a assinatura congelada segue congelada:

```
src/core/dna_analysis.py:276:    return results_sorted, skipped_matches, message
```

A tupla de três continua igual, e o `Tree` continua com quatro elementos. É o `W016`, e a
paridade nas 6 fixtures é a rede que o confirma por comportamento.

## O `owner_id`: existe como coluna, e em nenhum outro lugar

As três ocorrências de `owner_id` no que a feature escreveu:

```
init.sql:26             owner_id  TEXT NOT NULL,   -- o `dono`. SEM FK e SEM indice de escopo (RN-10)
init.sql:182            -- NENHUM indice comeca por `owner_id`, ao contrario do alvo...
adaptadores.py:188      (owner_id, tree_ref, match_file_ref, root_name_input, root_person_xref, ...
```

- a **declaração** da coluna, com o comentário que diz o que ela não é;
- o **comentário** que declara a ausência de índice, e a razão;
- a **lista de colunas de um `INSERT`** — onde o valor entra, e de onde nunca sai.

Nenhum `CREATE INDEX`, nenhum `CHECK`, nenhuma cláusula `WHERE`. E as três dimensões de
`data-delta.md` §4 e `roadmap.md` §10 ficam conferidas: **nenhum índice começa por `owner_id`**,
e o índice de cM do alvo (`ix_match_analysis_cm`) **não** foi criado.

⚠️ **A ausência é a informação.** Um índice de escopo seria a única coisa neste esquema a
insinuar um isolamento que **não existe** — as dívidas #3 e #4 seguem abertas, e a `RN-10`
proíbe que qualquer artefato desta feature sugira o contrário.

## O que este passo **não** confere

- **Não confere que nenhum teste foi enfraquecido.** O `git diff` de
  `tests/test_porta_de_armazenamento.py` mostra a mudança, e ela é a atualização da lista
  literal de `__all__` — com a docstring dizendo por quê. O arquivo não foi removido, nenhum
  teste foi desabilitado, e a segunda metade (a que prova que nenhum adaptador implementa o
  `RepositorioDeArvores`) segue intacta e passando.
- **Não confere os arquivos de teste NOVOS**, porque eles não existiam e não há diff a fazer.
  Eles são `componente-novo` no `legacy-impact.md`.

# Mitigacao aplicada ao BUG-20261009-6RKP

Data: 2026-10-09.  Pasta: `src/uploads`.
Antes: 19 arquivos, 29166183 bytes.

## Renomeacoes aplicadas

| Nome antes | Nome depois | sha256 (do conteudo) | Bytes |
|---|---|---|---|
| `50a3dd36fea8f8bb__Famílias_Sergipanas.csv` | `50a3dd36fea8f8bb__Familias_Sergipanas.csv` | `50a3dd36fea8f8bb` | 30591 |
| `94e2402671702cac__Famílias_Sergipanas.csv` | `94e2402671702cac__Familias_Sergipanas.csv` | `94e2402671702cac` | 30968 |
| `94e2402671702cac__Famílias_Sergipanas.csv.ged` | `94e2402671702cac__Familias_Sergipanas.csv.ged` | `94e2402671702cac` | 30968 |
| `b70889273a505a5d__Familias Sergipanas.xlsx` | `b70889273a505a5d__Familias_Sergipanas.xlsx` | `b70889273a505a5d` | 138024 |

## Prova 1: so os nomes mudaram

- multiconjunto de `sha256`+bytes ANTES:  19 arquivos, 14 conteudos distintos
- multiconjunto de `sha256`+bytes DEPOIS: 19 arquivos, 14 conteudos distintos
- **identicos? SIM**

## Prova 2: alcance por referencia, depois

- alcancaveis: 16 de 19
- ainda inalcancaveis: 3
  - `Adriano_Santos.ged`
  - `Arvore_Unificada_Oficial_V1_2.ged`
  - `Famílias_Sergipanas.csv`

## O que a mitigacao NAO resolve (vai para o fix)

- `Adriano_Santos.ged` — sem chave no nome, e **duplicata byte a byte** de `b3211a52a933fdd0__Adriano_Santos.ged`. Renomear para a chave do gemeo colidiria; nao ha renomeacao possivel.
- `Arvore_Unificada_Oficial_V1_2.ged` — sem chave no nome, e **duplicata byte a byte** de `080e7943572d2652__080e7943572d2652__Arvore_Unificada_Oficial_V1_2.ged`, `080e7943572d2652__Arvore_Unificada_Oficial_V1_2.ged`. Renomear para a chave do gemeo colidiria; nao ha renomeacao possivel.
- `Famílias_Sergipanas.csv` — sem chave no nome, e **duplicata byte a byte** de `94e2402671702cac__Familias_Sergipanas.csv`, `94e2402671702cac__Familias_Sergipanas.csv.ged`. Renomear para a chave do gemeo colidiria; nao ha renomeacao possivel.

## Referencias historicas

Documentos em `_reversa_forward/`, `_reversa_sdd/` e `_reversa_bugs/` que citam os nomes
ANTIGOS continuam citando-os: sao registro historico e nao serao reescritos. O mapeamento
acima e o que permite reler esses documentos. Mitigacao e `temporary: true` — o fix decide
qual lado da contradicao cede, e o resultado pode tornar estas renomeacoes desnecessarias.

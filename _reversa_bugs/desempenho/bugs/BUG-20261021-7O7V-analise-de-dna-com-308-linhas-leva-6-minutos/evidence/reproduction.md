# Cápsula de reprodução, 2026-10-21

## Ambiente

| Campo | Valor |
|---|---|
| Commit base | `1befc8d` (`master`, 2026-10-21) |
| Sistema | Windows, 4 processadores logicos |
| Runtime | Python 3.14.6 do `.venv/` |
| Dependencias de borda | as mesmas de `src/app.py` (`Dependencias` com `read_csv_with_fallback`, `detect_columns`, `aggregate_matches`, os tres emissores Mermaid) |
| Dado | SINTETICO, gerado pelo proprio probe. Nenhum arquivo de `src/uploads/` foi lido (Principio I) |

## Comando

```powershell
.\.venv\Scripts\python.exe _reversa_bugs\desempenho\probes\medir_fases.py --pessoas 19403 --exatas 100 --pool 208
.\.venv\Scripts\python.exe _reversa_bugs\desempenho\probes\medir_fases.py --pessoas 19403 --exatas 100 --pool 208 --perfil
```

Exit code: `0` nas duas execucoes. Taxa: 2 de 2 execucoes com os mesmos contadores.
Classificacao: `deterministic` (mesmos 101 resultados e 208 descartes).

## Resultado sem perfil

| Fase | Tempo |
|---|---|
| `carregar_arvore` (parse) | 10,41 s |
| `dna_analysis` (analise) | 42,68 s |
| Total | 53,08 s |
| Cartoes | 101 |
| Descartes | 208 |

## Resultado com `cProfile`

| Fase | Tempo |
|---|---|
| Parse | 10,63 s |
| Analise (perfilada, com overhead) | 119,87 s |

Topo por tempo cumulativo:

| Chamadas | Tempo cum. | Funcao |
|---:|---:|---|
| 1024 | 67,15 s | `person_summary` (`documentary_relationship.py:198`) |
| 1024 | 66,74 s | `get_children` (`documentary_relationship.py:182`) |
| 102 | 41,19 s | `homonym_dossier` (`documentary_relationship.py:301`) |
| 221 | 38,52 s | `_dossie` (`dna_analysis.py:524`) |
| 309 | 34,61 s | `avaliar_candidatos` (`matching.py:89`) |
| 120 | 24,18 s | `_diferencas` (`documentary_relationship.py:235`) |
| 7.972.194 | 33,53 s | `builtins.next` |
| 1.408.660 | 16,85 s | `thefuzz` `_rapidfuzz_scorer` |
| 1 | 12,76 s | `build_ged_indexes` (`matching.py:48`) |

## Leitura

1. `get_children` varre **todas as familias** por chamada, e `person_summary` e chamado 1.024
   vezes para 101 cartoes. O `next(...)` sobre `sub_records` duas vezes por familia e o
   desperdicio medido: 7,97 milhoes de chamadas a `next`.
2. `_diferencas` e chamado **duas vezes** por dossie (uma para `differences`, outra dentro de
   `identical_data`), e cada chamada remonta `person_summary` de todos os ids exatos.
3. `avaliar_candidatos` roda tres razoes difusas por candidato do pool (1,4 milhao de
   chamadas ao rapidfuzz nas 309 linhas).

## Limite desta reproducao

O caso do operador tem **6 minutos**; este reproduz **53 s**. A diferenca e atribuida ao
dado real: arvore conectada (a sintetica e uma floresta de familias isoladas, entao quase
nenhum caminho e encontrado e `documental_nao_encontrado` domina), mais familias e pools de
sobrenome maiores. **O tempo de 6 minutos NAO foi reproduzido** e a atribuicao ao dado real
e hipotese. O que esta confirmado e o custo relativo das funcoes acima no mesmo caminho de
codigo.

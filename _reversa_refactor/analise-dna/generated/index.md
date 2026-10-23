<!-- GENERATED, DO NOT EDIT: regenerado por /reversa-refactor em 2026-10-23T03:45:00-03:00 a partir de 13 oportunidades -->
<!-- Historico: gerado em 2026-09-30 por 8 oportunidades e atualizado a mao em 2026-10-01 (NUMT e ZV52 para applied). -->
<!-- Regenerado em 2026-10-08 pelo /reversa-refactor com a OPP-20261008-JXQN. -->
<!-- Regenerado em 2026-10-23 pelo /reversa-refactor com as OPPs 35-38 e reconciliado no mesmo dia: evidencia de suite substituida pela medicao real e diffs de reversao gerados. -->

# Indice de qualidade de codigo - analise-dna

> Gerado em `2026-10-23T03:45:00-03:00`. Fonte de verdade: `../opportunities/*.md`. Ordenado por `display_number`.

## Oportunidades

| # | ID | Verbo | Confianca | Impacto | Custo | Estado | Retorno esperado |
|---|----|-------|-----------|---------|-------|--------|------------------|
| #1 | `OPP-20260929-AU76` | optimize | 🟢 green | hotpath. O laco roda uma vez por match do CSV e renormaliza o mesmo candidato a cada match | low | applied | cerca de 3 vezes menos tempo por match, sem alterar nenhum resultado |
| #2 | `OPP-20260929-32Q7` | prune | 🟢 green | custo de construcao pago em toda analise e uma afirmacao falsa na documentacao do modulo | low | applied | remove cerca de um terco do custo de build_ged_indexes e alinha o docstring ao codigo |
| #3 | `OPP-20260929-ZV52` | modularize | 🟡 yellow | acoplamento e clareza. E o modulo mais dificil de testar em partes e o que mais muda | medium | applied | cada responsabilidade testavel isoladamente, sem tocar em nenhuma regra de negocio |
| #4 | `OPP-20260929-4LE3` | modularize | 🟢 green | risco de correcao no lugar errado. Quem for ajustar mojibake tem dois alvos plausiveis | low | applied | uma unica autoridade sobre limpeza de nome, com a divergencia documentada em vez de escondida |
| #11 | `OPP-20260929-4MGR` | optimize | 🟢 green | hotpath. O indice passou a ser a fase mais cara da analise, e e chamado uma vez por analise | low | applied | cerca de 2,7x menos normalizacoes na construcao do indice, sem alterar nenhum resultado |
| #12 | `OPP-20260929-NUMT` | optimize | 🟢 green | custo que cresce linearmente com o CSV, e CSV de GEDmatch tem milhares de linhas | medium | applied | ingestao proporcional ao tamanho real do arquivo, nao ao numero de chamadas Python |
| #13 | `OPP-20260929-IM3Q` | prune | 🟢 green | superficie de instalacao e tempo de build de ambiente, sem nenhum ganho em troca | low | applied | uma dependencia nativa a menos para compilar em cada ambiente novo |
| #16 | `OPP-20260929-U2NK` | prune | 🟢 green | clareza do modulo e uma pista falsa sobre onde a regex de ID vive | low | applied | uma linha a menos e nenhuma ambiguidade sobre a origem da regex de ID |
| #34 | `OPP-20261008-JXQN` | prune | 🟢 green | fecha a defesa textual do ADR-19 e a divida #18, tirando 65 linhas de heuristica ja retirada do fluxo | low | proposed (orfao suspeito) | 65 linhas e 2 testes a menos de heuristica aposentada |
| #35 | `OPP-20261023-MPRA` | modularize | 🟢 green | dois papeis distintos (caso de uso + projecao pura) no mesmo modulo crescem por razoes diferentes | low | **applied** | dna_analysis.py de 345 para 128 linhas; projecao_analise.py com 293 |
| #36 | `OPP-20261023-CLSM` | restructure | 🟢 green | 7 funcoes soltas de projecao sem contrato de objeto; padrao Mapper ausente na camada application | medium | **applied** | classe ProjetorDeAnalise com 6 metodos privados e `projetar`; fachada preservada |
| #37 | `OPP-20261023-DONO` | standardize | 🟢 green | parametro `dono` preservado como costura arquitetural, com docstring que nao dizia para onde o valor vai | low | **applied** | docstring alinhada ao ADR-26 e a coluna `owner_id TEXT NOT NULL`; prune recusado |
| #38 | `OPP-20261023-KITS` | simplify | 🟢 green | indexacao manual com guarda de tamanho em `_kits` | low | **applied** | tupla direta com `zip_longest` e fatia; sem estado intermediario |

## Transformacoes

| OPP | Estado | Registro | Diff de reversao | Rede de seguranca |
|-----|--------|----------|------------------|-------------------|
| `OPP-20260929-AU76` | applied | sim | sim | 3 artefato(s) |
| `OPP-20260929-32Q7` | applied | sim | sim | 4 artefato(s) |
| `OPP-20260929-ZV52` | applied | sim | sim | 1 artefato(s) |
| `OPP-20260929-4MGR` | applied | - | sim | 2 artefato(s) |
| `OPP-20260929-NUMT` | applied | sim | sim | 1 artefato(s) |
| `OPP-20260929-IM3Q` | applied | - | sim | 1 artefato(s) |
| `OPP-20260929-U2NK` | applied | - | sim | 2 artefato(s) |
| `OPP-20261008-JXQN` | proposed | sim | - | 0 artefato(s) |
| `OPP-20261023-MPRA` | applied | [transformation.md](../transformations/OPP-20261023-MPRA-mistura-caso-uso-projecao/transformation.md) | `CHG-LOTE-extracao-e-mapper.diff` (586 linhas) | 1615 passed, 9 skipped no lote |
| `OPP-20261023-CLSM` | applied | [transformation.md](../transformations/OPP-20261023-CLSM-funcoes-projecao-sem-classe-mapper/transformation.md) | o mesmo `CHG-LOTE` (empilhado) | 1615 passed, 9 skipped no lote |
| `OPP-20261023-DONO` | applied | [transformation.md](../transformations/OPP-20261023-DONO-parametro-dono-sem-comportamento/transformation.md) | o mesmo `CHG-LOTE` (empilhado) | 1615 passed, 9 skipped no lote |
| `OPP-20261023-KITS` | applied | [transformation.md](../transformations/OPP-20261023-KITS-indexacao-manual-zip-longest/transformation.md) | o mesmo `CHG-LOTE` (empilhado) | 1615 passed, 9 skipped no lote |

## Auditoria de 2026-10-23

As quatro transformacoes de `analise-dna` foram aplicadas em sequencia pela sessao
que depois parou. O codigo estava correto e a suite verde, mas o registro nao
fechava:

| Constatacao | Correcao |
|---|---|
| nenhuma das quatro tinha diff de reversao, embora o indice dissesse "diff proposto: sim" | `CHG-LOTE-extracao-e-mapper.diff` gerado do `HEAD 221b6c1` e verificado por aplicacao |
| `MPRA` dizia "suite rodando em background" no corpo e "preservado" na evidencia, ao mesmo tempo | Registro reescrito com a medicao real |
| os arquivos de suite declaravam `pytest 8.3.2`, `pyproject.toml` e 2 falhas de `graphviz` | Substituidos pela medicao real do `.venv`: 1615 passed, 9 skipped |
| `DONO` estava como `verb: prune` aplicado, sem `death-proof`, e sem poda nenhuma | `verb` corrigido para `standardize`; recusa do prune registrada na oportunidade |
| a prova de equivalencia de `KITS` estava errada para `avaliacoes` mais longa | Corrigida: a fatia `avaliacoes[:len(kits)]` e o que preserva o truncamento |
| `MPRA` dizia 126 linhas em `dna_analysis.py` | O arquivo tem 128 |

O diff unico cobre as quatro etapas porque elas foram empilhadas antes da
captura: `dna_analysis.py` e `projecao_analise.py` so sao reproduzidos pelo
conjunto. A reversao, portanto, e em bloco.

## Legenda

- Confianca: 🟢 coberto e entendido | 🟡 parcial | 🔴 sem prova de comportamento
- Custo: `low` | `medium` | `high`
- Estado: `proposed` | `approved` | `applied` | `reverted` | `declined`
- `promoted_to: null` marca orfao suspeito: sem referencia estatica provada morta, e o podador nao remove

---
*Gerado pelo Reversa-Refactor em 2026-10-08. Atualizado em 2026-10-23 com as OPPs 35-38 e reconciliado no mesmo dia.*

<!-- GENERATED, DO NOT EDIT: regenerado por /reversa-refactor em 2026-10-23T15:35:00-03:00 a partir de 19 oportunidades -->
<!-- Historico: gerado em 2026-09-30 por 8 oportunidades e atualizado a mao em 2026-10-01 (NUMT e ZV52 para applied). -->
<!-- Regenerado em 2026-10-08 pelo /reversa-refactor com a OPP-20261008-JXQN. -->
<!-- Regenerado em 2026-10-23 pelo /reversa-refactor com as OPPs 35-38 e reconciliado no mesmo dia: evidencia de suite substituida pela medicao real e diffs de reversao gerados. -->
<!-- Regenerado em 2026-10-23 pelo /reversa-refactor com as OPPs 46-48: auditoria de src/core/dna_analysis.py (OO, padrao, coesao, acoplamento e codigo morto). -->
<!-- Aplicadas no mesmo dia: DOCF (#48), ORQA (#46) com a guarda por AST que ela exigiu, ETAP (#49) e CTAO (#47). Fecha a auditoria de 2026-10-23. -->

# Indice de qualidade de codigo - analise-dna

> Gerado em `2026-10-23T15:02:00-03:00`. Fonte de verdade: `../opportunities/*.md`. Ordenado por `display_number`.

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
| #34 | `OPP-20261008-JXQN` | prune | 🟢 green | fecha a defesa textual do ADR-19 e a divida #18, tirando 65 linhas de heuristica ja retirada do fluxo | low | **declined** | nao executada: remover o modulo aposenta uma dimensao da paridade e exige decisao sobre RF-25/BR-D-62 e liberacao de `_reversa_sdd/**` |
| #35 | `OPP-20261023-MPRA` | modularize | 🟢 green | dois papeis distintos (caso de uso + projecao pura) no mesmo modulo crescem por razoes diferentes | low | **applied** | dna_analysis.py de 345 para 128 linhas; projecao_analise.py com 293 |
| #36 | `OPP-20261023-CLSM` | restructure | 🟢 green | 7 funcoes soltas de projecao sem contrato de objeto; padrao Mapper ausente na camada application | medium | **applied** | classe ProjetorDeAnalise com 6 metodos privados e `projetar`; fachada preservada |
| #37 | `OPP-20261023-DONO` | standardize | 🟢 green | parametro `dono` preservado como costura arquitetural, com docstring que nao dizia para onde o valor vai | low | **applied** | docstring alinhada ao ADR-26 e a coluna `owner_id TEXT NOT NULL`; prune recusado |
| #38 | `OPP-20261023-KITS` | simplify | 🟢 green | indexacao manual com guarda de tamanho em `_kits` | low | **applied** | tupla direta com `zip_longest` e fatia; sem estado intermediario |
| #46 | `OPP-20261023-ORQA` | restructure | 🟢 green | hotpath por execucao (142 cartoes por analise) e por mudanca (18 commits, 1.283 linhas somadas): `dna_analysis` tinha 553 linhas e o laco por kit, 370 | medium | **applied** | `dna_analysis` de 539 para 205 linhas; `_cartao_do_kit` com contexto de 13 campos |
| #47 | `OPP-20261023-CTAO` | modularize | 🟢 green | cinco razoes para mudar no mesmo arquivo e o contrato de 40 chaves escrito duas vezes, ja em ordens diferentes | medium | **applied** | oito modulos de 43 a 470 linhas; `dna_analysis.py` de 1.258 para 321 |
| #48 | `OPP-20261023-DOCF` | prune | 🟢 green | docstring orfao de 14 linhas lido como documentacao viva, e `DNAAnalyzer` em `__all__` sem nenhum consumidor | low | **applied** | 15 linhas a menos; modulo de 1.108 para 1.094 |
| #49 | `OPP-20261023-ETAP` | restructure | 🟢 green | `_cartao_do_kit` com 368 linhas e catorze etapas encadeadas sem fronteira interna; a ORQA deixou o estado no contexto, entao cada extracao custa 3 a 5 parametros | medium | **applied** | `_cartao_do_kit` de 368 para 224 linhas, com seis etapas nomeadas |
| #50 | `OPP-20261023-UNCA` | restructure | 🟢 green | contrato de 40 chaves escrito duas vezes, ja divergente na ordem, e nenhum teste fixando o conjunto | low | **applied** | tupla canonica e dois testes que comparam o conjunto de chaves de cada construtor |
| #51 | `OPP-20261023-GRDA` | standardize | 🟢 green | o ADR-19 proibe uso novo de `cm_estimator` e nada verifica; um import novo passa em silencio | low | **applied** | guarda por AST que reprova import de `cm_estimator` em `src/`, com prova negativa |

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
| `OPP-20261023-DOCF` | applied | [transformation.md](../transformations/OPP-20261023-DOCF-sobras-sem-efeito/transformation.md) | `CHG-001-docstring-orfao-e-nome-morto.diff` (33 linhas) | 1625 passed, 9 skipped antes e depois |
| `OPP-20261023-ORQA` | applied | [transformation.md](../transformations/OPP-20261023-ORQA-fluxo-de-553-linhas-sem-fronteira/transformation.md) | `CHG-001-contexto-e-passo-por-kit.diff` e `CHG-002-guarda-por-ast.diff` | 1625 passed, 9 skipped; digest identico em 3 cenarios |
| `OPP-20261023-ETAP` | applied | [transformation.md](../transformations/OPP-20261023-ETAP-etapas-do-passo-por-kit/transformation.md) | `CHG-001-seis-etapas-do-passo-por-kit.diff` (394 linhas) | 1625 passed, 9 skipped; digest identico |
| `OPP-20261023-CTAO` | applied | [transformation.md](../transformations/OPP-20261023-CTAO-cinco-razoes-para-mudar/transformation.md) | `CHG-001-oito-modulos.diff` e `CHG-002-referencias-aos-testes.diff` | 1625 passed, 9 skipped; digest identico |
| `OPP-20261023-UNCA` | applied | [transformation.md](../transformations/OPP-20261023-UNCA-contrato-do-cartao-duplicado/transformation.md) | `CHG-001-contrato-e-guarda.diff` (154 linhas) | 1627 passed, 9 skipped; digest identico |
| `OPP-20261023-GRDA` | applied | [transformation.md](../transformations/OPP-20261023-GRDA-guarda-do-cm-estimator/transformation.md) | `CHG-001-guarda-do-cm-estimator.diff` (91 linhas) | 1629 passed, 9 skipped |

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

## Auditoria de 2026-10-23: as quatro configuracoes em `src/core/dna_analysis.py`

Pedido do usuario: verificar orientacao a objeto, padrao de projeto, alta coesao e
baixo acoplamento, achar funcao sem utilidade, limpar o codigo e, se possivel,
dividir em modulos menores. Medicao sobre o arquivo de **1.108 linhas**:

| Configuracao | Situacao | Evidencia medida |
|---|---|---|
| Orientacao a objeto | 🟡 parcial, e nao por acidente | o modulo tem **uma** classe, `Dependencias`, que e um Parameter Object. O nucleo ja tem o idioma OO em `core/endogamia.py` (5 `@dataclass(frozen=True, slots=True)` e a classe de servico `DNAAnalyzer`). Converter o modulo inteiro continua fora do escopo: `_reversa_sdd/migration/paradigm_decision.md` recusa reificar matching e busca como objetos com estado |
| Padrao de projeto | 🟡 parcial | Parameter Object (`Dependencias`) e Facade (`__all__` com 15 nomes). O Mapper (`ProjetorDeAnalise`) esta em `application/`, nao aqui. Os dois padroes presentes sao adequados; o que sobrevive sem consumidor interno e a fachada |
| Alta coesao | 🔴 baixa no modulo, 🟢 alta nas funcoes | **cinco razoes para mudar** no mesmo arquivo. Oito das dez funcoes tem 61 linhas ou menos e uma responsabilidade clara; o problema esta no arquivo, nao nas funcoes |
| Baixo acoplamento | 🟡 no modulo, 🔴 em um ponto | 56 nomes importados de 21 modulos. `Dependencias` nasceu aqui e e consumida por `src/core/path_search.py` e `src/app.py` sem dono declarado: e o acoplamento concreto a resolver |

### Funcao sem utilidade: a resposta medida

**Nenhuma funcao inteira e orfa.** As 10 funcoes de nivel de modulo e a classe tem
chamador. O peso morto que existe e outro, e esta medido:

| Sobra | Tamanho | Prova |
|---|---|---|
| docstring orfao dentro de `dna_analysis` (558-571) | 14 linhas | `ast` mostra `Expr(Constant(str))`, sem efeito |
| `DNAAnalyzer` em `__all__` | 1 nome | zero importacoes do nome a partir deste modulo em todo o projeto |
| `Dependencias.aggregate_matches` | 1 atributo | atribuido e nunca lido, mas e argumento posicional obrigatorio de 34 chamadores em caminho nao liberado |

As duas primeiras viram a `OPP-20261023-DOCF`. A terceira **nao** vira poda, e a
recusa esta registrada na propria oportunidade.

### Oportunidades abertas

| # | ID | Verbo | Custo | O que resolve |
|---|---|---|---|---|
| #46 | `OPP-20261023-ORQA` | restructure | medium | **applied em 2026-10-23**: `dna_analysis` de 539 para 205 linhas; `_cartao_do_kit` com contexto de 13 campos |
| #47 | `OPP-20261023-CTAO` | modularize | medium | **applied em 2026-10-23**: oito modulos de 43 a 470 linhas; `dna_analysis.py` de 1.258 para 321 |
| #48 | `OPP-20261023-DOCF` | prune | low | **applied em 2026-10-23**: docstring orfao e nome morto no `__all__` removidos; 1.108 para 1.094 linhas |
| #49 | `OPP-20261023-ETAP` | restructure | medium | **applied em 2026-10-23**: `_cartao_do_kit` de 368 para 224 linhas, com seis etapas nomeadas |
| #50 | `OPP-20261023-UNCA` | restructure | low | **applied em 2026-10-23**: tupla canonica das 40 chaves e dois testes que comparam o conjunto |

A auditoria esta fechada. A `JXQN` (#34) foi **declinada** em 2026-10-23: remover
`cm_estimator` aposentaria uma dimensao da matriz de paridade e exigiria decisao sobre
`RF-25`/`BR-D-62`, mais a liberacao de `_reversa_sdd/**`. No lugar dela ficou a
`GRDA` (#51), que transforma a defesa textual do ADR-19 em defesa estrutural sem tocar
em instrumento congelado.

Medicao ao longo da sessao: **1625 passed, 9 skipped** em 105,64 s (antes da
`DOCF`), 106,01 s (depois dela), 108,78 s (depois da `ORQA`), 95,87 s (depois da
`ETAP`) e 96,61 s (depois da `CTAO`).

## Legenda

- Confianca: 🟢 coberto e entendido | 🟡 parcial | 🔴 sem prova de comportamento
- Custo: `low` | `medium` | `high`
- Estado: `proposed` | `approved` | `applied` | `reverted` | `declined`
- `promoted_to: null` marca orfao suspeito: sem referencia estatica provada morta, e o podador nao remove

---
*Gerado pelo Reversa-Refactor em 2026-10-08. Atualizado em 2026-10-23 com as OPPs 35-38, reconciliado no mesmo dia, com as OPPs 46-48 na auditoria de `src/core/dna_analysis.py` e com as OPPs 46, 48 e 49 aplicadas na sequencia.*

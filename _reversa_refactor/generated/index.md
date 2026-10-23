<!-- GENERATED, DO NOT EDIT: regenerado por /reversa-refactor em 2026-10-23 a partir de 48 oportunidades -->
<!-- Atualizado a mao em 2026-10-01: OPP-20260929-5XGJ, OPP-20260929-NUMT, OPP-20260929-ZV52, OPP-20260929-UXEF e OPP-20260929-H2YY passaram a applied. O gerador nao foi reexecutado. -->
<!-- Atualizado em 2026-10-06 pela auditoria das quatro configuracoes pedidas pelo usuario: 6 oportunidades novas (#27 a #32), contexto arquitetura-src e contrato-de-dados-src. -->
<!-- Reconciliado em 2026-10-06: OPP-20260929-EHNZ marcada declined (alvos mortos e conteudo duplicado por OPP-20261006-3WR5) e alvos da OPP-20261003-PAST corrigidos. -->
<!-- Reconciliado em 2026-10-23: lote de analise-dna (OPPs 35-38) e de tela-de-entrada (OPPs 39-43) fechado. DISP passou a applied; evidencia de suite fabricada foi substituida por medicao real; diffs de reversao gerados e verificados. -->
<!-- FACT (#42) aprovada em plano e em diff e aplicada em 2026-10-23: create_app + 6 testes; suite 1621 passed, 9 skipped. -->
<!-- ESTD (#44) aplicada em 2026-10-23: injeção de _ARMAZENAMENTO, _CARREGADOR, _REGISTRO e _DEPENDENCIAS por instância; suite 1625 passed, 9 skipped. -->
<!-- RDME (#45) aplicada em 2026-10-23: README alinhado ao codigo, 54 arquivos na arvore; suite 1625 passed, 9 skipped. -->
<!-- OPPs 46-48 abertas em 2026-10-23 na auditoria de src/core/dna_analysis.py (OO, padrao, coesao, acoplamento, codigo morto): ORQA, CTAO e DOCF. DOCF, ORQA e ETAP (#49, fase 2 da ORQA) foram aplicadas no mesmo dia. -->

# Registro de qualidade de código · visão global

> Gerado em `2026-10-23`. Ordenado por retorno estimado, não por estética.

Contextos: analise-dna, arquitetura-src, busca-caminho, contrato-de-dados-src, documentacao-sdd, documentacao-do-projeto, pacote-reconstructed, tela-de-entrada, upload-gedcom, verificacao-de-tipos. Total: **51 oportunidades**, sendo **42 aplicadas**, **1 aplicada em parte** (`OPP-20261006-LIGH`), **5 declined** e **3 que permanecem `proposed`**.

## Lote de 2026-10-23: analise-dna e tela-de-entrada

Duas frentes foram abertas no mesmo dia. A primeira (analise-dna) fechou; a segunda
(tela-de-entrada) parou de madrugada, com o código aplicado e o registro pela metade.

| # | ID | Contexto | Verbo | Estado | Resultado |
|---|---|---|---|---|---|
| #35 | `OPP-20261023-MPRA` | analise-dna | modularize | **applied** | projeção fora do caso de uso: 345 → 128 linhas, novo `projecao_analise.py` com 293 |
| #36 | `OPP-20261023-CLSM` | analise-dna | restructure | **applied** | classe `ProjetorDeAnalise` (Mapper) com 6 métodos privados e `projetar` |
| #37 | `OPP-20261023-DONO` | analise-dna | standardize | **applied** | docstring do `dono` alinhada ao ADR-26; o prune foi recusado |
| #38 | `OPP-20261023-KITS` | analise-dna | simplify | **applied** | `_kits` com `zip_longest` e fatia, sem lista mutável |
| #39 | `OPP-20261023-DISP` | tela-de-entrada | restructure | **applied** | `index()` de 234 → 19 linhas; 5 handlers e dois mapas de ação |
| #40 | `OPP-20261023-ASST` | tela-de-entrada | modularize | **applied** | Blueprint `assets_bp` em `src/web/rotas_assets.py`; `app.py` de 888 → 737 |
| #43 | `OPP-20261023-DEAD` | tela-de-entrada | prune | **applied** | guarda inalcançável unificada; checagem mantida para estreitar tipo |
| #41 | `OPP-20261023-SERV` | tela-de-entrada | decouple | **declined** | `tests/test_servidor_producao.py` exige o bloco de servidor no AST de `app.py` |
| #42 | `OPP-20261023-FACT` | tela-de-entrada | modularize | **applied** | `create_app(config=None)` com 6 testes; isolamento de configuração, não de estado |
| #44 | `OPP-20261023-ESTD` | tela-de-entrada | decouple | **applied** | 10 leituras de global em handlers viraram 0; 4 dependências injetáveis |
| #45 | `OPP-20261023-RDME` | documentacao-do-projeto | standardize | **applied** | README alinhado: 54 arquivos na árvore, 0 faltando |

### O que a conciliação de 2026-10-23 encontrou

O código das sete transformações aplicadas estava correto e a suíte verde, mas o
registro não fechava:

| Constatação | Correção |
|---|---|
| `DISP` aplicada no código, marcada `proposed`, sem `transformation.md` | Registro escrito, estado corrigido, diff real gerado |
| o `proposed.diff` de `DISP` era um esboço com `...` e não aplicava | Removido e substituído por `CHG-001-despachador-de-acoes.diff` |
| nenhuma das sete tinha diff de reversão, embora os índices dissessem "sim" | Seis diffs gerados e verificados por aplicação em cadeia |
| os arquivos de suíte declaravam `Python 3.12.3`, `pytest 8.3.2` e `pyproject.toml`, que o projeto não tem | Substituídos pela medição real nas duas pontas do lote |
| `MPRA` dizia "suite rodando em background" e "preservado" ao mesmo tempo | Registro reescrito |
| `DONO` estava como `prune` aplicado, sem poda e sem `death-proof` | Verbo corrigido para `standardize`; recusa registrada |
| a prova de equivalência de `KITS` estava errada para `avaliacoes` mais longa | Corrigida com a fatia `avaliacoes[:len(kits)]` |
| a extração de `ASST` deixou `build_only`, re-exportações sem efeito e `import json` sem uso | Removidos; `url_for` do template aponta para `assets.descartes_em_csv` |

Medição real do lote, nesta sessão:

| Momento | Resultado |
|---|---|
| linha de base `HEAD 221b6c1` (cópia limpa) | **1615 passed, 9 skipped** em 190,29 s |
| working tree depois do lote e da limpeza | **1615 passed, 9 skipped** em 197,00 s |
| verificação de tipos | **não medida**: `pyrefly` não está instalado no `.venv` |

## Auditoria de 2026-10-23: `src/core/dna_analysis.py`

Segunda frente do dia, aberta por pedido do usuário sobre um arquivo específico e
com as mesmas quatro configurações da auditoria de 2026-10-06. O alvo tem **1.108
linhas**, e o levantamento abriu três oportunidades e recusou uma quarta:

| # | ID | Verbo | Custo | Estado | Resultado esperado |
|---|---|---|---|---|---|
| #46 | `OPP-20261023-ORQA` | restructure | medium | **applied** | `dna_analysis` de 539 para 205 linhas; `_cartao_do_kit` com contexto de 13 campos |
| #47 | `OPP-20261023-CTAO` | modularize | medium | **applied** | oito módulos de 43 a 470 linhas; `dna_analysis.py` de 1.258 para 321 |
| #48 | `OPP-20261023-DOCF` | prune | low | **applied** | 1.108 → 1.094 linhas, uma única docstring por função |
| #49 | `OPP-20261023-ETAP` | restructure | medium | **applied** | `_cartao_do_kit` de 368 para 224 linhas, com seis etapas nomeadas |
| #50 | `OPP-20261023-UNCA` | restructure | low | **applied** | as 40 chaves do cartão declaradas uma vez e guardadas por teste |
| #51 | `OPP-20261023-GRDA` | standardize | low | **applied** | guarda por AST contra uso novo de `cm_estimator`, com prova negativa |
| #34 | `OPP-20261008-JXQN` | prune | low | **declined** | remover o módulo aposenta uma dimensão da paridade e exige decisão de spec |

Diagnóstico, com medição:

| Configuração | Situação | Evidência |
|---|---|---|
| Orientação a objeto | 🟡 parcial | uma classe (`Dependencias`, Parameter Object). O núcleo já usa `@dataclass(frozen=True, slots=True)` em `core/endogamia.py`; converter o módulo inteiro segue fora do escopo (`paradigm_decision.md`) |
| Padrão de projeto | 🟡 parcial | Parameter Object e Facade. A Fachada é o único padrão que sobrevive sem consumidor interno |
| Alta coesão | 🔴 baixa no módulo | cinco razões para mudar no mesmo arquivo; oito das dez funções têm 61 linhas ou menos |
| Baixo acoplamento | 🟡 no módulo, 🔴 em um ponto | 56 nomes de 21 módulos; `Dependencias` é consumida por `core/path_search.py` sem dono declarado |

**Função sem utilidade: nenhuma inteira.** As 10 funções e a classe têm chamador. O
peso morto medido é um docstring órfão de 14 linhas e um nome em `__all__` sem
consumidor, ambos na `DOCF`, podados no mesmo dia.

**O que foi recusado, e por quê.** A fachada de 12 imports sem uso no corpo tem
consumidor real, dois instrumentos congelados de `_reversa_sdd/parity/` e um teste,
e o módulo de origem já está carregado por outros caminhos: o ganho em tempo é nulo
e a config não libera `_reversa_sdd/**`. Remover `Dependencias.aggregate_matches`
quebraria 34 chamadores em `_reversa_bugs/_sondas-matching/`, também fora dos globs.
Nenhuma das duas virou oportunidade.

## Reconciliação de 2026-10-06

O levantamento das oportunidades em aberto encontrou duas desatualizações de registro, ambas
corrigidas sem tocar em código do projeto:

| Oportunidade | Problema | Ação |
|---|---|---|
| `OPP-20260929-EHNZ` (#10) | Alvos em `analisador-genealogico/reconstructed/*.py`, raiz extinta em 2026-10-03; conteúdo duplicado pela `OPP-20261006-3WR5` | Marcada `declined` com `superseded_by`, preservando o registro e o encaminhamento ao Forward |
| `OPP-20261003-PAST` (#25) | Alvos em `src/reconstructed/...`, nível de pacote apagado pela `OPP-20261003-FLAT` | Alvos reescritos para `src/parsers/`, `src/reporting/`, `src/core/gedcom_state.py` e `src/core/dna_analysis.py` |

Nenhuma das duas mudanças altera escopo, custo ou risco do trabalho proposto.

## Auditoria de 2026-10-06: as quatro configurações pedidas

Diagnóstico sobre `src/` (22 módulos, 3.473 linhas), com evidência medida:

| Configuração | Situação | Evidência |
|---|---|---|
| Orientação a objeto | ❌ ausente por decisão | zero `class` e zero `@dataclass` em `src/` |
| Padrão de projeto | ❌ ausente | nenhuma fábrica, repositório, estratégia ou injeção; o único padrão é o singleton de estado global |
| Alta coesão | 🟡 parcial | excelente por pacote e módulo, ausente no nível de dado |
| Baixo acoplamento | 🔴 ausente | 2 ciclos de import em nível de pacote e estado global importado por 9 módulos |

> **Atualização de 2026-10-23:** o quadro acima deixou de valer em dois pontos. Existe
> agora uma classe de domínio aplicado (`ProjetorDeAnalise`, Mapper) e existe um
> Blueprint de rotas (`assets_bp`). Não é "o projeto adotou OO": são dois pontos de
> padrão onde havia uma dor concreta — projeção pura e entrega de assets.

As seis oportunidades novas de 2026-10-06:

| # | ID | Contexto | Verbo | Custo | Estado | O que resolve |
|---|----|----------|-------|-------|--------|---------------|
| #32 | `OPP-20261006-4KMB` | arquitetura-src | restructure | low | **applied** | guarda de leitura do GEDCOM duplicada em `app.py` |
| #28 | `OPP-20261006-ULVW` | arquitetura-src | decouple | medium | **applied** | ciclo `core/` ↔ `reporting/`, extinto por injeção do resolvedor |
| #27 | `OPP-20261006-3WR5` | arquitetura-src | decouple | high | **declined** | estado global mutável: spec fixa o comportamento, mitigação não autorizada, e a Onda 3 já descarta o mecanismo |
| #29 | `OPP-20261006-LIGH` | arquitetura-src | decouple | medium | **partially-applied** | ciclo `core/` ↔ `parsers/`: aresta do `csv_ingest` resolvida, a do `gedcom_parser` bloqueada por spec |
| #30 | `OPP-20261006-ESKO` | contrato-de-dados-src | standardize | medium | **applied** | superfície de compatibilidade de `path_search` reduzida de 18 nomes para 1 |
| #31 | `OPP-20261006-YTSH` | contrato-de-dados-src | modularize | high | proposed | contrato dos dicionários de domínio vive só no documento |
| #33 | `OPP-20261006-W4KD` | documentacao-sdd | standardize | low | proposed | specs afirmam que `reporting/` importa `core`, e os dois módulos novos não existem em artefato algum |

## Itens que NÃO devem ser roteados como refactor

| ID | Destino correto | Motivo |
|----|-----------------|--------|
| `OPP-20260929-EHNZ` | **declined** em 2026-10-06 | Alvos mortos e conteúdo duplicado por `OPP-20261006-3WR5`; o encaminhamento ao Forward foi transportado para lá |
| `OPP-20261006-3WR5` | **declined** em 2026-10-06 | Comportamento fixado por `upload-gedcom/requirements.md:23` e `design.md:33`; mitigação no legado nunca autorizada (`questions.md:262-264`); a Onda 3 já descarta o mecanismo (`discard_log.md` BR-DESCARTAR-001) |
| `OPP-20261003-PAST` | **declined** em 2026-10-06 | Alcance medido de 89 ocorrências em 18 arquivos, perda de precisão nos dois nomes de módulo e quebra de uma sonda de bug em `_reversa_bugs/`, sem ganho funcional |
| `OPP-20261023-SERV` | **declined** em 2026-10-23 | `tests/test_servidor_producao.py` lê o AST de `src/app.py` e exige o bloco `if __name__ == "__main__":` com socket e Waitress no arquivo |
| `OPP-20261008-JXQN` | **declined** em 2026-10-23 | Remover `cm_estimator` aposenta uma dimensão da matriz de paridade (`harness.py`) e exige decisão sobre `RF-25`/`BR-D-62` e liberação de `_reversa_sdd/**`. A metade que cabe no refactor virou a `OPP-20261023-GRDA` |
| `OPP-20260929-DW3U` (opção A) | Decisão humana antes | Remover as entidades derruba testes de `tests/test_domain.py`: mesmo dilema de linha de base |
| `OPP-20260929-DW3U` (opção C) | Forward | Dar consumidor às entidades reescreve `upload.py`: mudança de comportamento |
| poda do pool por `given_index` | Forward | Muda qual candidato vence: mudança de comportamento |
| `OPP-20261006-YTSH` | `/reversa-requirements` | Eliminar a variação de chaves entre ramos muda a forma dos dados de modo observável para o template |
| orientação a objeto e padrões de projeto | `/reversa-requirements` ou `_reversa_sdd/migration/` | `paradigm_decision.md` escolheu Híbrido e proíbe aggregates com estado no núcleo de cálculo |
| `OPP-20261003-INIT` | Decisão humana antes | Contradiz a RN-01 |

## Ordem sugerida de ataque

| Ordem | ID | Verbo | Custo | Comando |
|-------|----|-------|-------|---------|
| ~~1~~ | ~~`OPP-20261006-4KMB`~~ | restructure | low | **aplicada em 2026-10-06** |
| ~~2~~ | ~~`OPP-20261006-ULVW`~~ | decouple | medium | **aplicada em 2026-10-06** |
| ~~3~~ | ~~`OPP-20261006-LIGH`~~ | decouple | medium | **aplicada em parte em 2026-10-06**; a aresta restante vai ao Forward |
| ~~4~~ | ~~`OPP-20261006-ESKO`~~ | standardize | medium | **aplicada em 2026-10-06** |
| ~~5~~ | ~~`OPP-20261023-MPRA`~~ | modularize | low | **aplicada em 2026-10-23** |
| ~~6~~ | ~~`OPP-20261023-CLSM`~~ | restructure | medium | **aplicada em 2026-10-23** |
| ~~7~~ | ~~`OPP-20261023-KITS`~~ | simplify | low | **aplicada em 2026-10-23** |
| ~~8~~ | ~~`OPP-20261023-DONO`~~ | standardize | low | **aplicada em 2026-10-23** (prune recusado) |
| ~~9~~ | ~~`OPP-20261023-ASST`~~ | modularize | low | **aplicada em 2026-10-23** |
| ~~10~~ | ~~`OPP-20261023-DEAD`~~ | prune | low | **aplicada em 2026-10-23** |
| ~~11~~ | ~~`OPP-20261023-DISP`~~ | restructure | medium | **aplicada em 2026-10-23** |
| ~~12~~ | ~~`OPP-20261023-FACT`~~ | modularize | medium | **aplicada em 2026-10-23** (composition root + 6 testes) |
| ~~13~~ | ~~`OPP-20261023-ESTD`~~ | decouple | medium | **aplicada em 2026-10-23** (estado de borda injetável) |
| ~~14~~ | ~~`OPP-20261023-RDME`~~ | standardize | low | **aplicada em 2026-10-23** (README alinhado) |
| 15 | `OPP-20261006-3WR5` | decouple | high | `/reversa-decouple OPP-20261006-3WR5` (só depois de decisão humana) |
| 16 | `OPP-20261006-YTSH` | modularize | high | `/reversa-requirements` (não é refactor) |
| ~~17~~ | ~~`OPP-20261023-DOCF`~~ | prune | low | **aplicada em 2026-10-23** (1.108 → 1.094 linhas; suíte 1625/9) |
| ~~18~~ | ~~`OPP-20261023-ORQA`~~ | restructure | medium | **aplicada em 2026-10-23** (dna_analysis de 539 para 205 linhas; suíte 1625/9) |
| ~~19~~ | ~~`OPP-20261023-CTAO`~~ | modularize | medium | **aplicada em 2026-10-23** (oito módulos; `dna_analysis.py` de 1.258 para 321 linhas) |
| ~~20~~ | ~~`OPP-20261023-ETAP`~~ | restructure | medium | **aplicada em 2026-10-23** (`_cartao_do_kit` de 368 para 224 linhas; suíte 1625/9) |
| ~~21~~ | ~~`OPP-20261023-UNCA`~~ | restructure | low | **aplicada em 2026-10-23** (contrato de 40 chaves + 2 testes; suíte 1627/9) |
| ~~22~~ | ~~`OPP-20261023-GRDA`~~ | standardize | low | **aplicada em 2026-10-23** (guarda do `cm_estimator`; suíte 1629/9) |

## Por contexto

| Contexto | Oportunidades | Caminho |
|----------|---------------|---------|
| `analise-dna` | 19 | `_reversa_refactor/analise-dna/` |
| `arquitetura-src` | 4 | `_reversa_refactor/arquitetura-src/` |
| `busca-caminho` | 4 | `_reversa_refactor/busca-caminho/` |
| `contrato-de-dados-src` | 2 | `_reversa_refactor/contrato-de-dados-src/` |
| `documentacao-sdd` | 1 | `_reversa_refactor/documentacao-sdd/` |
| `documentacao-do-projeto` | 1 (applied) | `_reversa_refactor/documentacao-do-projeto/` |
| `pacote-reconstructed` | 9 | `_reversa_refactor/pacote-reconstructed/` |
| `tela-de-entrada` | 6 (5 applied, 1 declined) | `_reversa_refactor/tela-de-entrada/` |
| `upload-gedcom` | 4 (1 declined) | `_reversa_refactor/upload-gedcom/` |
| `verificacao-de-tipos` | 1 | `_reversa_refactor/verificacao-de-tipos/` |

## Roteamento aprovado em 2026-09-29

Ordem de encadeamento definida pelo usuário. As 11 primeiras foram aplicadas sob o gate de edição do legado liberado; as demais seguem a mesma ordem e param no gate até serem autorizadas.

| Ordem | ID | Comando |
|-------|----|---------|
| 1 | `OPP-20260929-TPSH` | `/reversa-restructure OPP-20260929-TPSH` |
| 2 | `OPP-20260929-AU76` | `/reversa-optimize OPP-20260929-AU76` |
| 3 | `OPP-20260929-32Q7` | `/reversa-prune OPP-20260929-32Q7` |
| 4 | `OPP-20260929-SEQO` | `/reversa-prune OPP-20260929-SEQO` |

## Linha de base medida

| Data | Verificação | Resultado |
|---|---|---|
| 2026-10-06 | Suíte (`py -3.14 -m pytest -q`) | 164 passam, 15 erros de ambiente (`PermissionError` do sandbox em `tmp_path`) |
| 2026-10-06 | Tipos (`py -3.14 -m pyrefly check src`) | 27 erros |
| 2026-10-23 | Suíte no `HEAD 221b6c1` (cópia limpa) | **1615 passed, 9 skipped** em 190,29 s |
| 2026-10-23 | Suíte no working tree depois do lote | **1615 passed, 9 skipped** em 197,00 s |
| 2026-10-23 | Suíte depois da FACT (`create_app` + 6 testes) | **1621 passed, 9 skipped** em 294,19 s |
| 2026-10-23 | Suíte depois da ESTD (estado injetável + 4 testes) | **1625 passed, 9 skipped** em 157,14 s |
| 2026-10-23 | Suíte depois do README (só documentação) | **1625 passed, 9 skipped** em 74,14 s |
| 2026-10-23 | Suíte antes da `DOCF` | **1625 passed, 9 skipped** em 105,64 s |
| 2026-10-23 | Suíte depois da `DOCF` (15 linhas podadas) | **1625 passed, 9 skipped** em 106,01 s |
| 2026-10-23 | Suíte depois da `ORQA`, fase 1 | **1625 passed, 9 skipped** em 108,78 s |
| 2026-10-23 | Suíte depois da `ETAP` (seis etapas) | **1625 passed, 9 skipped** em 95,87 s |
| 2026-10-23 | Suíte depois da `CTAO` (oito módulos) | **1625 passed, 9 skipped** em 96,61 s |
| 2026-10-23 | Suíte depois da `UNCA` (contrato + 2 testes) | **1627 passed, 9 skipped** em 116,88 s |
| 2026-10-23 | Suíte depois da `GRDA` (guarda do `cm_estimator`) | **1629 passed, 9 skipped** em 117,52 s |
| 2026-10-23 | Tipos | não medidos: `pyrefly` não está instalado no `.venv` |

---
*Gerado pelo Reversa-Refactor em 2026-10-06. Atualizado em 2026-10-23 com o lote de analise-dna e tela-de-entrada e com a auditoria de `src/core/dna_analysis.py`.*

<!--
Actions da feature 057 — Distribuição por cromossomo.
IDs estáveis, nunca reciclados. Status inicial [ ]. /reversa-coding muda para [X].
-->

# Actions: Distribuição por cromossomo

> Identificador: `057-distribuicao-por-cromossomo`
> Data: `2026-11-10`
> Roadmap: `_reversa_forward/057-distribuicao-por-cromossomo/roadmap.md`

## Resumo

| Métrica | Valor |
|---------|-------|
| Total de ações | 18 |
| Paralelizáveis (`[//]`) | 12 |
| Maior cadeia de dependência | 8 (T001 → T004 → T008 → T011 → T012 → T013 → T015 → T016) |

## Fase 1, Preparação

| ID | Descrição | Dependências | Paralelismo | Arquivo alvo | Confidência | Status |
|----|-----------|--------------|-------------|--------------|-------------|--------|
| T001 | Acrescentar a fixture `DNA_CSV_SEGMENTOS_DISTRIBUICAO` (11 segmentos, 3 cromossomos, um kit repetido em dois cromossomos) ao módulo de fixtures sintéticas | - | `[//]` | `tests/fixtures/sample_dna.py` | 🟢 | `[X]` |
| T002 | Criar `src/core/distribuicao.py` com o dataclass `ResumoDoCromossomo` (`frozen`, `slots`) e a assinatura documentada de `distribuicao_por_cromossomo`, sem lógica | - | `[//]` | `src/core/distribuicao.py` | 🟢 | `[X]` |
| T003 | Criar `src/reporting/distribuicao.py` com as constantes de passo de eixo (`PASSOS_DE_MATCHES`, `PASSOS_DE_CM`, `MARCAS_POR_EIXO`) e a assinatura documentada de `montar_distribuicao`, sem lógica | - | `[//]` | `src/reporting/distribuicao.py` | 🟢 | `[X]` |

## Fase 2, Testes

| ID | Descrição | Dependências | Paralelismo | Arquivo alvo | Confidência | Status |
|----|-----------|--------------|-------------|--------------|-------------|--------|
| T004 | Testes do núcleo: ordem natural (`9` antes de `10`), `RN-02` (kit em duas regiões do mesmo cromossomo conta uma vez), `RN-03` (média simples do segmento escolhido por kit), `RN-06` (cromossomo sem região não entra) e lista vazia | T001, T002 | `[//]` | `tests/test_distribuicao.py` | 🟢 | `[X]` |
| T005 | Testes da projeção: dicionários com `cromossomo`, `kits` (int) e `cm_medio`, sem formatação nem geometria, e sem mutar o resumo | T001 | `[//]` | `tests/test_projecao_da_distribuicao.py` | 🟢 | `[X]` |
| T006 | Testes do desenho: eixo sempre do zero (`RN-08`), topo "redondo" ≥ maior valor, quatro marcas, altura proporcional ao topo e lado do cartão pela posição da coluna | T001, T003 | `[//]` | `tests/test_grafico_da_distribuicao.py` | 🟡 | `[X]` |
| T007 | Teste de ordem compartilhada: o núcleo e `reporting/ideograma.py` produzem a mesma sequência para o mesmo conjunto de cromossomos (`D-09`) | T002 | `[//]` | `tests/test_distribuicao.py` | 🟢 | `[X]` |

## Fase 3, Núcleo

| ID | Descrição | Dependências | Paralelismo | Arquivo alvo | Confidência | Status |
|----|-----------|--------------|-------------|--------------|-------------|--------|
| T008 | Implementar `distribuicao_por_cromossomo`: agrupar por cromossomo, escolher o segmento de maior cM por kit (`D-12`), calcular a média e ordenar em ordem natural | T004 | - | `src/core/distribuicao.py` | 🟡 | `[X]` |
| T009 | Implementar `projetar_distribuicao`: resumo para dicionário de tela, com `kits` já contado | T005 | - | `src/application/distribuicao.py` | 🟢 | `[X]` |
| T010 | Implementar `montar_distribuicao`: topo redondo por eixo, quatro marcas de zero ao topo, altura em % e lado do cartão | T006 | - | `src/reporting/distribuicao.py` | 🟡 | `[X]` |

## Fase 4, Integração

| ID | Descrição | Dependências | Paralelismo | Arquivo alvo | Confidência | Status |
|----|-----------|--------------|-------------|--------------|-------------|--------|
| T011 | Acrescentar `distribuicao: tuple = ()` a `ResultadoDeAnalise` e chamar `distribuicao_por_cromossomo` sobre as regiões classificadas, em `try/except` que devolve tupla vazia (`D-02`, `D-03`) | T008 | - | `src/application/dna_analysis.py` | 🟢 | `[X]` |
| T012 | Projetar e desenhar no fluxo da análise de DNA: `distribuicao_dados` e `grafico_da_distribuicao` no contexto do template | T009, T010, T011 | - | `src/app.py` | 🟢 | `[X]` |
| T013 | Inserir o sub-bloco "Distribuição por cromossomo" **entre a legenda do ideograma e a lista de regiões**, com duas colunas de barra, eixos, legenda e cartão do hover reaproveitando `.dica` (`D-10`) | T012 | `[//]` | `src/templates/index.html` | 🟢 | `[X]` |
| T014 | Estilos do gráfico: coluna dupla por cromossomo, altura em %, eixos e marcas, rótulo `Chr N` girado, cores `--primary`/`--ink` (`D-06`, `D-07`) | - | `[//]` | `src/assets/app.css` | 🟢 | `[X]` |
| T015 | Teste de contrato da tela: o sub-bloco aparece entre a legenda e a primeira região, com os dois eixos rotulados e a legenda da origem; sem região, nenhum vestígio do gráfico no HTML | T013, T014 | - | `tests/test_contrato_das_regioes.py` | 🟢 | `[X]` |

## Fase 5, Polimento

| ID | Descrição | Dependências | Paralelismo | Arquivo alvo | Confidência | Status |
|----|-----------|--------------|-------------|--------------|-------------|--------|
| T016 | Medir `SHA_DA_TELA` e registrar em `evidence/SHA_DA_TELA.md` (esperado: inalterado, 52.497 bytes) | T015 | `[//]` | `_reversa_forward/057-distribuicao-por-cromossomo/evidence/SHA_DA_TELA.md` | 🟢 | `[X]` |
| T017 | Gerar `regression-watch.md` da feature, com o item do eixo do zero, o da deduplicação por kit e o da posição do sub-bloco | T015 | `[//]` | `_reversa_forward/057-distribuicao-por-cromossomo/regression-watch.md` | 🟢 | `[X]` |
| T018 | Atualizar o item "Regiões compartilhadas" do README com o gráfico e registrar as medições do parse/desenho em `evidence/medicoes.md` | T015 | `[//]` | `README.md` | 🟢 | `[X]` |

## Notas de execução

## Histórico de alterações

| Data | Alteração | Autor |
|------|-----------|-------|
| 2026-11-10 | Versão inicial gerada por `/reversa-to-do` | reversa |

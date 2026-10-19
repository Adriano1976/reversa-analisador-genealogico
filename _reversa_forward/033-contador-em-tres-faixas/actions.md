# 033 — Ações

| # | Ação | Status | Arquivos |
|---|------|--------|----------|
| T001 | Medir, no GEDCOM real, quantos cartões têm caminho, quantos foram recusados pela janela de vida e quantos têm árvore sugerida, nas quatro árvores ativas | [X] | `evidence/medicoes.md` |
| T002 | Confirmar que a sugestão só existe onde há caminho documental (gates de `arvore_sugerida` e `mermaid_da_sugestao`) | [X] | `requirements.md#3` |
| T003 | Reescrever a frase do topo em três faixas mutuamente exclusivas, fechando a conta | [X] | `src/templates/index.html` |
| T004 | Contar a árvore sugerida em frase própria, com a mesma condição do bloco do cartão | [X] | `src/templates/index.html` |
| T005 | Garantir que a faixa dos recusados só apareça quando existe | [X] | `src/templates/index.html` |
| T006 | Acrescentar `documentary_do_registro` e o helper `resultado_recusado_pela_idade` às fixtures de cartão | [X] | `tests/fixtures/resultado_para_cartao.py` |
| T007 | Cobrir as três faixas, a exclusividade, o singular/plural e a sugestão-sem-desenho | [X] | `tests/test_contador_em_tres_faixas.py` |
| T008 | Provar que o cartão recusado continua dizendo "não encontrado" (a contagem não muda a regra) | [X] | `tests/test_contador_em_tres_faixas.py` |
| T009 | Registrar a medição e a sonda reprodutível como evidência | [X] | `evidence/` |
| T010 | Convergir na extração (adendo e `active-requirements.json`) | [X] | `_reversa_sdd/addenda/033-contador-em-tres-faixas.md` |

## Nota de execução

T001 mediu **9 caminhos** na árvore real, dos quais **6** apresentados e **3** recusados pela
janela de vida — o número que a frase antiga escondia. A mesma medição mostrou **0 cartões**
com árvore sugerida naquele par de arquivos, o que sustenta a decisão de não tratar a
sugestão como faixa: hoje ela não acrescentaria ninguém.

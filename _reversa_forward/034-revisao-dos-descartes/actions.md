# 034 — Ações

| # | Ação | Status | Arquivos |
|---|------|--------|----------|
| T001 | `match_candidates` devolve o candidato melhor avaliado (id, given, final, jacc) sem mudar a aceitação | [ ] | `src/core/matching.py` |
| T002 | Atualizar o call site da análise para o novo retorno | [ ] | `src/core/dna_analysis.py` |
| T003 | Levar o candidato ao `DescartadoDaAnalise` | [ ] | `src/application/dna_analysis.py`, `src/ports/__init__.py` |
| T004 | Coluna do candidato no bloco dos descartados | [ ] | `src/templates/index.html` |
| T005 | Botão "usar este candidato" apenas quando há candidato plausível | [ ] | `src/templates/index.html` |
| T006 | Rota de promoção: refazer a análise daquele kit com o nó fixado | [ ] | `src/app.py`, `src/application/dna_analysis.py` |
| T007 | Cartão promovido registra o motivo original como observação | [ ] | `src/core/dna_analysis.py` |
| T008 | Testes de núcleo: retorno do candidato e aceitação intacta | [ ] | `tests/` |
| T009 | Testes de tela: coluna, botão e ausência de botão | [ ] | `tests/` |
| T010 | Suíte completa e adendo | [ ] | `_reversa_sdd/addenda/034-revisao-dos-descartes.md` |

## Nota de execução

Escopo definido pelas medições de `evidence/medicoes.md`: **76** descartes com candidato
compatível na Tratado e **15** na Adriano V2; teto de ganho em "com caminho" de **+7** e **+1**.
Os 288 e 431 sem candidato nenhum não entram: não há o que revisar.

# 035 — Ações

| # | Ação | Status | Arquivos |
|---|------|--------|----------|
| T001 | Formatador puro do CSV, com BOM, `;`, decimal com vírgula e guarda contra fórmula | [X] | `src/reporting/csv_de_descartes.py` |
| T002 | Exportar só o candidato compatível | [X] | `src/reporting/csv_de_descartes.py` |
| T003 | Rota `POST /descartes.csv`, que recebe o JSON da tela e devolve o arquivo | [X] | `src/app.py` |
| T004 | Botão e campo oculto no bloco dos descartados | [X] | `src/templates/index.html` |
| T005 | Testes do formatador, da rota e da tela | [X] | `tests/test_csv_de_descartes.py` |
| T006 | Suíte completa, reinício do servidor e adendo | [X] | `_reversa_sdd/addenda/035-lista-de-trabalho-dos-descartes.md` |

## Nota de execução

Medido no GEDCOM real (`..._V1_2_Tratado.ged` + CSV ativo): a planilha sai com **367
linhas** (cabeçalho + 366 descartes) e **58 KB**; **76 linhas** trazem candidato
compatível. As outras 290 saem com as colunas de candidato vazias e o `Motivo` intacto —
é a lista de nomes a cadastrar.

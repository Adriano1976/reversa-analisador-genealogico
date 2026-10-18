# Conferência da tela (2026-10-17)

> Feature `026-polimento-visual-da-tela` — ação `T011`.

## O que foi conferido, e com qual instrumento

A conferência foi feita por **medição automática** dos valores efetivos e dos contratos de rota. Não
houve inspeção visual em navegador nesta rodada; o passo a passo para a conferência humana está no
`onboarding.md` (passos 2 a 5) e continua recomendado.

| Item | Instrumento | Resultado |
|------|-------------|-----------|
| A folha é servida com `text/css` e `ETag` | `tests/test_estilo_da_tela.py::TestRotaDaFolha` | 200, `text/css`, `ETag` presente, `304` na rebusca |
| O selo `INCONCLUSIVO` tem fundo próprio e texto branco legível nos dois temas | `tests/test_estilo_da_tela.py::TestOContrasteDosSelos` (resolve `var()` pela cascata) | verde; fundo `#6A6150`, texto `#fff`, **6,11:1** |
| O alias com `--muted` seria reprovado | mesma classe, tema escuro | branco sobre `#A99F88` = **2,62:1** — o teste reprova a troca |
| O documento não mudou | `tests/test_icone_de_atalho.py::test_a_tela_nao_mudou_sem_mudanca_declarada` | `sha256` = `c4a34f7b…`, 30.781 bytes |
| O ícone de atalho continua sem declaração | `tests/test_icone_de_atalho.py::test_a_tela_nao_declara_o_icone_de_atalho` | verde |
| O favicon continua embutido | `test_a_tela_mantem_o_icone_da_aba_embutido` | 1 `rel="icon"`, 1 `data:image` |
| `favicon.ico` continua sem resposta | `test_os_caminhos_nao_servidos_continuam_sem_resposta` | 404 |
| O `h1` não ganhou `visually-hidden` | `tests/test_banner_do_topo.py::test_o_titulo_do_produto_esta_sempre_visivel` | verde |
| Os quatro tokens mortos sumiram | `Select-String` na folha | 0 ocorrências |

## Valores efetivos do selo

| Estado | Fundo | Texto | Contraste |
|--------|-------|-------|-----------|
| `COMPATIVEL` | `#2F6B3A` | `#fff` | 6,39:1 |
| `POSSIVEL` | `#7A4F00` | `#fff` | 7,13:1 |
| `CONFLITANTE` | `#A8321F` | `#fff` | 6,69:1 |
| `INCONCLUSIVO` | `#6A6150` | `#fff` | 6,11:1 |

Os quatro valores são os mesmos de antes da feature: a mudança não altera nenhuma cor aplicada.

## O que fica pendente para o operador

A conferência visual (olho no selo, nos dois temas, com o navegador) não substitui nem é substituída
pela medição: ela confirma que a folha **chegou** ao navegador. O roteiro está no `onboarding.md`
passos 2 a 5, incluindo o trecho de console que cria um selo de inspeção sem usar dado real.

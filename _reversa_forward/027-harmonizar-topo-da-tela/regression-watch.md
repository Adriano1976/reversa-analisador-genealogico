# Regression Watch: harmonização visual do topo da tela

> Identificador: `027-harmonizar-topo-da-tela`
> Data: `2026-10-17`

## Watch principal

| ID | Origem (arquivo, seção) | Regra esperada após a mudança | Tipo de verificação | Sinal de violação |
|----|-------------------------|-------------------------------|---------------------|-------------------|
| W001 | `src/assets/app.css`, `:root` e tema escuro; `RF-02` | Os quatro tokens `--sucesso-bg`, `--sucesso-line`, `--perigo-bg` e `--perigo-line` existem nos dois temas | `presença` | Um dos tokens some ou fica só no tema claro |
| W002 | `src/assets/app.css`, comentário dos alertas; `RF-10` | O comentário traz os oito contrastes medidos e o alerta mantém texto ≥ 4,5:1 e borda ≥ 3:1 | `redação` | Os números somem ou o contraste cai |
| W003 | `src/assets/app.css`, `@media (min-width:576px)`; `RF-03` | `.d-grid > .btn` tem largura natural acima de 576 px e total abaixo | `presença` | A regra some ou a ação volta a ser barra no desktop |
| W004 | `src/assets/app.css`; `RF-04` | `h1` com máximo de 2,2 rem e arte com máximo de 280 px | `presença` | O `clamp` volta a 2,5 rem ou a arte a 320 px |
| W005 | `tests/test_banner_do_topo.py:270-298`; `RN-24` | A introdução continua com `row justify-content-center` + `col-lg-*` e o HTML servido não tem `text-start` | `presença` | O teste da `RN-24` falha ou `text-start` aparece no HTML |
| W006 | `tests/test_icone_de_atalho.py`, `SHA_DA_TELA`; `RF-08` | O hash continua `c4a34f7b…` e o teste do hash verde | `presença` | O hash muda sem uma mudança de tela declarada |
| W007 | `src/assets/app.css`; `RN-08` | Nenhum seletor de `.badge`, `.cartao-do-resultado`, `bg-secondary` ou das cores do resultado é tocado | `ausência` | Uma regra nova alcança o rodapé, inclusive o `alert-warning` do cartão de DNA |

## Observações

- **OBS-01** 🟡 A conferência visual humana não foi executada nesta rodada (sem navegador). A
  verificação foi por medição (`evidence/depois/tela.md`); o `onboarding.md` passos 2 a 5 cobre,
  inclusive o X do alerta nos dois temas.
- **OBS-02** 🟡 A entrega da feature 026 continua **sem commit** na árvore; o delta da 027 foi medido
  contra as cópias do baseline (`evidence/antes/app.css` e `index.html`) para não misturar as duas.
- **OBS-03** 🟡 O comentário da masthead é **Jinja** e não chega ao HTML; por isso o `SHA_DA_TELA` não
  se move. Quem for editar aquele bloco deve saber que o conteúdo do comentário não afeta a tela.

## Histórico de re-extrações

| Data | Re-extração | Resultado |
|------|-------------|-----------|
| — | — | Aguardando a próxima execução de `/reversa` |

## Arquivadas

| ID | Motivo | Data |
|----|--------|------|
| — | — | — |

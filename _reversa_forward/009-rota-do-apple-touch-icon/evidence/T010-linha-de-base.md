# T010 — Linha de base e prova do "falha antes"

> Feature: `009-rota-do-apple-touch-icon` · Ação: `T010` · Data: `2026-10-08`
> Registro bruto: `evidence/_t010_suite.txt`

## Linha de base herdada

| Medida | Antes desta feature |
|---|---|
| Suíte | `282 passed, 8 skipped` |
| Paridade diferencial | `100 %` nas 6 fixtures, exit 0 |

## Depois desta feature

```
=== SUITE ===
302 passed, 8 skipped in 107.29s (0:01:47)

=== PARIDADE ===
RESULTADO: PARIDADE 100%% (zero divergencia)
```

| Medida | Antes | Depois | Delta |
|---|---|---|---|
| Aprovados | 282 | **302** | **+20** |
| Pulados | 8 | 8 | 0 |
| Falhas | 0 | **0** | 0 |
| Paridade | 100 % | **100 %** | 0 |

Os **+20** são exatamente os testes que esta feature escreveu: 15 em
`tests/test_icone_de_atalho.py` e 5 em `tests/test_deriva_da_arte.py`. **Nenhum teste foi
removido, renomeado ou desabilitado**, e os 8 pulados são os mesmos de antes — são do
adaptador de banco da feature 008, que exige driver e `DATABASE_URL`.

## A paridade foi medida, e não presumida

O núcleo **não foi tocado** — o `T012` prova isso por `diff` vazio em `src/core/`,
`src/parsers/`, `src/reporting/` e `src/utils/`. A paridade em 100 % era, portanto,
**esperada por construção**.

E é exatamente por isso que ela foi **medida**: uma feature que não toca o núcleo é
precisamente o caso em que ninguém confere, e o instrumento de paridade é a única coisa
que distingue "não toquei" de "não percebi que toquei".

## Prova do "falha antes" (`RF-08`, `Princípio III`)

Antes de a rota existir, os dois arquivos novos foram executados:

```
5 failed, 3 passed
FAILED test_a_rota_do_icone_responde_200
FAILED test_o_tipo_de_conteudo_e_de_imagem
FAILED test_o_icone_tem_180_por_180
FAILED test_o_icone_nao_tem_canal_alfa
FAILED test_o_tamanho_e_o_da_receita
```

As **5 falhas** são as que dependem da rota, e todas falharam com `404`. Os **3 aprovados**
são as guardas da tela (`GET /` byte a byte, template sem declaração do ícone, ícone da aba
embutido) — que já eram verdadeiros e continuam sendo.

Isso é o que o `RF-08` pede: um teste que **viu o vermelho**. Um teste escrito depois do
código passa sem nunca ter falhado, e não prova nada sobre a mudança.

Depois da rota: **20 passed** nos dois arquivos.

## Leitura honesta dos números

- O salto de 282 para 302 **não** significa que a suíte ficou 7 % melhor. Significa que
  esta feature acrescentou 20 testes sobre um contrato pequeno — e que 5 deles são guardas
  de não-regressão (a tela não muda, o template não é tocado, o ícone da aba continua
  embutido), não cobertura de comportamento novo.
- A paridade em 100 % **não** é conquista desta entrega; é a ausência dela no núcleo.

## Fontes

- `evidence/_t010_suite.txt` (saída bruta das duas execuções)
- `_reversa_forward/009-rota-do-apple-touch-icon/actions.md` (a linha de base herdada no resumo)
- `.reversa/principles.md#III`

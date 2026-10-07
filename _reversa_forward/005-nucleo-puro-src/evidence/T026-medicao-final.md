# T026 — medição final

**Data:** 2026-10-07
**Ação:** `T026` — medir o resultado final e registrar a evidência: suíte e paridade
com a assinatura nova, comparando com a linha de base de `T004`.

## Comparação com a linha de base

| Medição | Linha de base (`T004`) | Resultado final (`T026`) | Δ |
| --- | --- | --- | --- |
| Suíte | `164 passed, 15 errors` | **`178 passed, 0 xfailed, 15 errors`** | **+14 passed** |
| Falhas esperadas (`xfail`) | 0 | **0** | 0 |
| Paridade | 100% nas 6 fixtures | **100% nas 6 fixtures** | 0 |
| Exit code do harness | 0 | **0** | 0 |

**A conta dos 14 a mais fecha, e nenhum teste foi removido para chegar nela:**

| Origem | Testes | Observação |
| --- | --- | --- |
| `tests/test_dependencias_nucleo.py` | 8 | guardas estruturais (`RF-01`, `RF-08`, `RF-09`, `RN-04`) + 3 caminhos negativos + 3 do comparador (`T030`) |
| `tests/test_arvore_devolvida.py` | 5 | forma e completude da árvore devolvida (`RF-13`) |
| Verificação de mãos dadas | +1 | `test_transicao_ainda_atualiza_o_estado_global` saiu em `T023` — o próprio docstring mandava removê-lo, e não "consertá-lo" |

14 testes novos menos 1 removido = **+13**. O total da suíte foi de 164 para 177
nesse ponto, e de 177 para **178** quando o `xfail` da guarda de estado saiu: o
teste passou a contar como aprovado em vez de "falha esperada".

**O `xfailed` foi a zero, e isso é o objeto da feature.** Ele existia porque a
afirmação "o núcleo não declara estado mutável de módulo" era **falsa** enquanto
`src/core/gedcom_state.py` existisse. Uma suíte com `xfail` é uma suíte que
declara uma pendência conhecida; zero `xfail` significa que não há pendência
declarada.

## Estado final do núcleo

O `src/core/` é um conjunto de **funções puras** sobre uma árvore que o chamador
entrega:

| Guarda | Regra | Estado |
| --- | --- | --- |
| Não importa framework | `RF-08` | ✅ verde |
| Não faz I/O nem depende de plataforma | `RN-04` | ✅ verde |
| Não declara estado mutável de módulo | `RF-01` | ✅ verde (era `xfail`) |
| Não importa `parsers/` nem `reporting/` | `RF-09` | ✅ verde |

Todas as quatro provadas **nos dois sentidos** (`T024`): passam com o núcleo limpo
e falham quando a violação é introduzida de propósito.

## Resíduo de texto

`src/core/gedcom_state.py` **não existe mais**. Nenhum módulo de `src/` o importa.
Restam 12 menções, **todas em comentário ou docstring**, que descrevem o mecanismo
extinto:

- `src/utils/text_cleaning.py` (3), `src/core/family_navigation.py` (1),
  `src/core/path_search.py` (2), `src/app.py` (1), `src/core/diagram_domain.py` (1),
  `src/core/registro.py` (1), `src/reporting/mermaid_render.py` (1),
  `src/core/documentary_relationship.py` (2)

Elas são o alvo de `T027` (README) e `T028` (docstrings). Uma docstring que mente
sobre o mecanismo é pior que docstring nenhuma — foi assim que a `D-06` precisou
de justificativa explícita.

## Reprodução

```bash
# suíte (TEMP gravável é necessário: ver "Erros de ambiente")
python -m pytest -q
# paridade
python _reversa_sdd/parity/harness.py
```

## Erros de ambiente (pré-existentes, não são regressão)

Os 15 erros são todos de `setup` em `tests/test_upload_seguranca.py`:
`PermissionError [WinError 5]` ao criar o diretório temporário do pytest. Eles
existem desde a linha de base de `T004` (que já media "15 errors") e não mudaram de
número nem de causa em nenhuma ação desta feature. A suíte precisa de `TEMP`/`TMP`
gravável.

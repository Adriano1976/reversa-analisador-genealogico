---
schema_version: 1
id: OPP-20261023-DOCF
verb: prune
state: applied
safety_net:
  kind: existing
  green_before: true
  green_after: true
preservation:
  method: death-proof
  evidence:
    - before-after/death-proof.py
    - before-after/death-proof-antes.txt
    - before-after/death-proof-depois.txt
    - before-after/suite-antes.txt
    - before-after/suite-depois.txt
measurement:
  before: 1.108 linhas de módulo e 15 nomes em __all__
  after: 1.094 linhas de módulo e 14 nomes em __all__
change_set:
  - chg: CHG-001
    file: src/core/dna_analysis.py
    purpose: remove o docstring órfão de 14 linhas e o nome DNAAnalyzer de __all__
approval:
  by: user
  at: 2026-10-23T14:39:06-03:00
  plan_at: 2026-10-23T14:39:06-03:00
reversible_via: [CHG-001-docstring-orfao-e-nome-morto.diff]
---

## O que foi removido

Uma poda de duas sobras sem efeito, sem uma linha de lógica tocada.

| # | Trecho | Tamanho | Classificação |
|---|---|---|---|
| 1 | expressão de string solta dentro de `dna_analysis`, linhas 558-571 | 14 linhas | **morto** |
| 2 | `"DNAAnalyzer"` em `__all__`, linha 1103 | 1 nome | **morto** |

**Nada mais foi tocado.** A tarja do módulo, os imports, o corpo de `dna_analysis`,
`_ordem` e os demais nomes de `__all__` seguem idênticos.

## Prova de morte, por trecho

### Trecho 1: a string solta

```text
dentro de dna_analysis: linhas 558-571 (14 linhas)
tipo do no: Expr(Constant)
efeito colateral possivel: nao (constante string)
```

O trecho está logo depois de `analisador_de_dna = DNAAnalyzer()`. Tem forma de
docstring, mas a docstring de uma função é o **primeiro** statement, e o primeiro é
o da linha 541. Sendo o segundo, o interpretador o avalia e descarta.

A docstring real não muda, e isso foi medido antes e depois:

| Momento | `inspect.getdoc(dna_analysis)` |
|---|---|
| antes | 585 caracteres, começa com `Executa a analise de DNA e devolve ...` |
| depois | a função nem aparece mais no relatório de strings soltas: `nenhuma encontrada` |

### Trecho 2: o nome em `__all__`

```text
__all__ tem 15 nomes
'DNAAnalyzer' em __all__: True
consumidores de DNAAnalyzer por este modulo: 0
'import *' do modulo no projeto: 0
```

`DNAAnalyzer` continua importado da linha 47 e usado na linha 557. O que saiu foi a
declaração de exportação, que só governa `from ... import *`, e não há nenhum no
projeto. A classe segue em `core/endogamia.py` e é de lá que
`tests/test_endogamia.py` a importa.

## O que NÃO foi removido, e por quê

| Candidato | Medição | Classificação |
|---|---|---|
| `Dependencias.aggregate_matches` | atribuído na linha 130 e nunca lido | **órfão suspeito** (`promoted_to: null`): é argumento posicional obrigatório de 34 chamadores em `_reversa_bugs/_sondas-matching/` e `_reversa_sdd/parity/`, caminhos fora dos globs liberados. Remover quebraria instrumentos congelados |
| `Dependencias.generate_mermaid_indirect` | lido em `src/core/path_search.py:187` | não é morto |
| 12 imports sem uso no corpo | consumidos por `__all__` em `_reversa_sdd/parity/_collect_cand.py`, `_check_split_types.py` e `tests/test_characterization_matching.py` | não é morto, e o ganho em tempo é nulo: os módulos de origem já estão carregados |
| `getattr(deps, "anotar_profundidade", None)` | o slot sempre existe | não removido: cerimônia de uma linha, sem efeito em leitura nem comportamento |

## Conferência contra a alma

**D1** ancora a separação dos três eixos na seção "Regra absoluta (nao regredir)" do
cabeçalho, linhas 23-30, que não foi tocada. **D2** declara o núcleo puro e a árvore
como valor de entrada. Nenhum dos dois candidatos implementa regra de negócio
confirmada: um era texto descartado pelo interpretador, o outro uma declaração de
exportação.

## Rede de segurança

| Momento | Resultado | Evidência |
|---|---|---|
| antes | **1625 passed, 9 skipped** em 105,64 s | `before-after/suite-antes.txt` |
| depois | **1625 passed, 9 skipped** em 106,01 s | `before-after/suite-depois.txt` |

Mesma contagem, mesmas 9 exclusões. Nenhum teste novo foi escrito: a remoção é de
código que nenhum teste alcançava.

## Reversão

`git apply -R CHG-001-docstring-orfao-e-nome-morto.diff` devolve o arquivo ao estado
anterior. O diff foi verificado com `git apply --check` antes da aplicação (exit 0) e
aplicado com `git apply` (exit 0).

## Nota sobre as duas provas

O script `death-proof.py` roda nos dois estados e é o mesmo arquivo. No estado
**antes** ele encontra as duas sobras; no estado **depois** ele imprime
`candidato 1: nenhuma encontrada` e encerra com código 1, que é o sinal de
"candidato ausente" do próprio script, e não uma falha. Os dois relatórios brutos
estão em `before-after/`.

---
*Aplicado em 2026-10-23 pelo Reversa-Refactor, sob gate de plano e de diff aprovados pelo usuário.*

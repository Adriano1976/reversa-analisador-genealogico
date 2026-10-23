---
schema_version: 1
id: OPP-20261023-MPRA
verb: modularize
state: applied
safety_net:
  kind: existing
  green_before: true
  green_after: true
preservation:
  method: tests
  evidence:
    - before-after/suite-antes.txt
    - before-after/suite-depois.txt
measurement:
  before: "src/application/dna_analysis.py com 345 linhas e dois papeis (caso de uso + projecao)"
  after: "src/application/dna_analysis.py com 128 linhas (caso de uso + re-export) e src/application/projecao_analise.py com 293 linhas (projecao pura)"
change_set:
  - chg: CHG-LOTE
    file: src/application/projecao_analise.py
    purpose: novo modulo com a projecao pura (seis auxiliares + ponto de entrada)
  - chg: CHG-LOTE
    file: src/application/dna_analysis.py
    purpose: remove o bloco de projecao e passa a importar de `application.projecao_analise`
approval:
  by: user
  at: 2026-10-23T00:20:53-03:00
reversible_via: [CHG-LOTE-extracao-e-mapper.diff]
---

# Transformacao: OPP-20261023-MPRA (projecao fora do caso de uso)

## O que mudou

O bloco de projecao que vivia no fim de `src/application/dna_analysis.py` passou
para `src/application/projecao_analise.py`. O caso de uso continua no mesmo
modulo e importa o ponto de entrada:

```python
from application.projecao_analise import ProjetorDeAnalise, projetar_analise  # noqa: F401
```

`dna_analysis.py` caiu de 345 para 128 linhas; `projecao_analise.py` nasceu com
293. O `__all__` do modulo antigo mantem `projetar_analise`, e ha uma fachada
funcional no modulo novo, para os importadores que ja faziam
`from application.dna_analysis import projetar_analise`.

## Diff acumulado, e por que

O diff deste diretorio cobre as **quatro** transformacoes empilhadas de
`analise-dna` (MPRA, CLSM, KITS e DONO). As quatro foram aplicadas no mesmo
working tree, sem captura de estado intermediario, e os arquivos finais so podem
ser reproduzidos pelo conjunto. Por isso `reversible_via` aponta para
`CHG-LOTE-extracao-e-mapper.diff` nas quatro: a reversao e em bloco, e o diff foi
verificado por aplicacao sobre o `HEAD 221b6c1`, reproduzindo os dois arquivos
byte a byte.

A separacao de MPRA, isolada, e a que moveu o bloco; a classe (`CLSM`) e o
`zip_longest` (`KITS`) vieram depois, sobre o modulo novo. O diff unico nao
distingue as tres etapas.

## Rede de seguranca

| Momento | Resultado |
|---|---|
| linha de base HEAD 221b6c1 | 1615 passed, 9 skipped |
| working tree depois do lote | 1615 passed, 9 skipped |

Medicao do lote combinado; ver [suite-antes.txt](before-after/suite-antes.txt) e
[suite-depois.txt](before-after/suite-depois.txt).

## Correcao de registro

O `transformation.md` anterior deste diretorio dizia, no corpo, "Depois: pendente
- suite rodando em background", enquanto o `suite-depois.txt` ao lado afirmava
veredito preservado. As duas coisas nao podiam ser verdade ao mesmo tempo. Os
arquivos de suite tambem estavam em formato de outro ambiente (`pytest 8.3.2`,
`pyproject.toml`, 2 falhas de `graphviz`) e foram substituidos pela medicao real.

A contagem final de linhas tambem foi corrigida: o registro anterior dizia 126
linhas em `dna_analysis.py`; o arquivo tem 128.

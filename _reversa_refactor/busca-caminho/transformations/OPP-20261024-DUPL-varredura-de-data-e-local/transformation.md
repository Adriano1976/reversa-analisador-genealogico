---
schema_version: 1
id: OPP-20261024-DUPL
verb: simplify
state: applied
safety_net:
  kind: existing
  green_before: true
  green_after: true
preservation:
  method: equivalence-proof
  evidence:
    - before-after/prova-de-equivalencia.txt
    - before-after/controle-negativo.txt
    - before-after/suite-antes.txt
    - before-after/suite-depois.txt
    - CHG-001.diff
measurement:
  before: >
    Duas funcoes de 10 linhas identicas com uma constante trocada (20 linhas no total); dois
    lacos "primeira familia que liga" no mesmo `hop_evidence`, com o conjunto de pais remontado
    nas duas; 21 linhas de `hop_evidence` para responder a pergunta.
  after: >
    Uma varredura de 10 linhas e duas funcoes de 1 linha de corpo (14 linhas no total); um laco
    so, dentro de `_familia_que_liga`; 8 linhas de `hop_evidence` ate a evidencia de datas.
    Modulo de 777 para 780 linhas, porque os dois helpers novos trazem docstring propria.
change_set:
  - chg: CHG-001
    file: src/core/documentary_relationship.py
    purpose: >
      `_sub_valor` no lugar de `_data_de` e `_local_de` duplicadas; `_pais_da_familia` e
      `_familia_que_liga` no lugar dos dois lacos de `hop_evidence`
approval:
  by: user
  at: 2026-10-24T01:52:00-03:00
reversible_via: [CHG-001.diff]
---

## O que estava duplicado

Duas funcoes de dez linhas, identicas, com uma constante trocada:

```python
def _data_de(people, pid, tag):          # linhas 92 a 101
    pessoa = people.get(pid)
    if not pessoa:
        return None
    for rec in pessoa.sub_records:
        if rec.tag == tag:
            for sub in rec.sub_records:
                if sub.tag == "DATE":
                    return str(sub.value)
    return None

def _local_de(people, pid, tag):         # linhas 112 a 121
    ...                                   # o mesmo, com "PLAC"
```

E, dentro de `hop_evidence`, a pergunta "em qual familia esta pessoa e HUSB ou WIFE"
respondida duas vezes, com o conjunto de pais remontado nas duas:

```python
    for famc in _ids(people, "FAMC", child_id):
        candidata = families.get(famc)
        if candidata and parent_id in {ref_id(r.value) for r in candidata.sub_records if r.tag in ("HUSB", "WIFE")}:
            familia_id = famc
            break
    if familia_id is None:
        for fam_id in arvore[3].get(child_id, []):
            fam = families.get(fam_id)
            if not fam:
                continue
            pais = {ref_id(r.value) for r in fam.sub_records if r.tag in ("HUSB", "WIFE")}
            if parent_id in pais:
                familia_id = fam_id
                break
```

Vinte e uma linhas para responder uma coisa, com a regra "a primeira familia que liga
vence" escrita duas vezes e sem nome.

## Por que a complexidade era acidental

Nada ali era regra de negocio: a regra unica e "primeiro DATE dentro de BIRT" e "primeira
familia que liga". A duplicacao nao protegia nada. O risco estava no dia em que a leitura de
DATE ganhasse um caso de fallback: PLAC ficaria para tras em silencio, e a ficha passaria a
mostrar local de nascimento ausente so para algumas pessoas.

## O que foi feito

`CHG-001`:

1. `_sub_valor(people, pid, tag, sub_tag)` com a varredura unica;
2. `_data_de` e `_local_de` como duas linhas cada, chamando com `"DATE"` e `"PLAC"`;
3. `_pais_da_familia(familia)` e `_familia_que_liga(families, candidatos, parent_id)`;
4. `hop_evidence` com duas chamadas no lugar dos dois lacos.

## O que ficou de fora, e a medicao que decidiu

A oportunidade propunha tambem um `_casal_da_familia` para as quatro leituras de HUSB e
WIFE. Foi descartado depois de medido: em `_construir_indice_de_filhos` o casal e os filhos
saem na MESMA passada, e `hop_evidence` precisa so do primeiro de cada, o que `next()` ja
resolve em uma linha. O helper teria mais linhas do que as quatro que substituiria e
acrescentaria uma passada sobre `sub_records`.

## Prova de equivalencia

Comparacao da versao de `HEAD` com a versao aplicada, funcao por funcao, sobre a arvore real
de 35.459 pessoas e 6.930 familias:

| Funcao | Casos | Divergencias |
|---|---|---|
| `_data_de` | 20.005 | 0 |
| `_local_de` | 20.005 | 0 |
| `hop_evidence` | 46.487 | 0 |

Casos: 4.000 pessoas x 5 tags mais um id ausente, em cada leitor; todas as arestas
declaradas do arquivo (cada CHIL x cada HUSB ou WIFE); 300 pares sem vinculo; id de filho e
de genitor inexistentes.

**O instrumento foi calibrado antes**: com uma diferenca injetada de proposito em
`_data_de`, o mesmo script acusou 221 divergencias e mostrou o texto exato que mudou
(`(um 1120)` virando `(UM 1120)`), enquanto as outras duas funcoes seguiam em zero. Um
"0 divergencias" sem esse controle nao seria prova de nada.

## Rede de seguranca

Suite completa antes e depois: **1635 passed, 9 skipped** nas duas pontas. Nenhum teste
mudou de estado, nenhuma assercao afrouxada. A transformacao nao acrescenta teste
permanente: o comportamento ja e coberto por `tests/test_confrontacao_gedcom_dna.py`
(vinculo com data impossivel), `tests/test_desempenho_das_fichas.py` e pelo harness de
paridade de `_reversa_sdd/parity/`.

## Fronteira de comportamento

Nenhuma. Mesma saida em todos os 86.497 casos comparados, incluindo os de beco: BIRT sem
DATE, BIRT sem PLAC, pessoa ausente do dicionario, registro sem sub-registros, dois BIRT no
mesmo registro, FAMC orfao, familia ausente do dicionario, pai que nao e conjuge.

O modulo passou de 777 para 780 linhas. Ele cresceu porque os dois helpers novos trazem
docstring e espacamento proprios; o que diminuiu foi o numero de lugares em que a mesma
regra aparece escrita.

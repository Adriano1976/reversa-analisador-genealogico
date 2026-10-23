---
schema_version: 1
id: OPP-20261023-CLSM
verb: restructure
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
  before: "sete funcoes soltas de projecao, sem contrato de objeto, espalhadas pelo modulo"
  after: "classe ProjetorDeAnalise com seis metodos privados e um ponto publico (`projetar`), mais a fachada `projetar_analise`"
change_set:
  - chg: CHG-LOTE
    file: src/application/projecao_analise.py
    purpose: agrupa as seis funcoes de projecao na classe ProjetorDeAnalise e expoe `projetar`
  - chg: CHG-LOTE
    file: src/application/dna_analysis.py
    purpose: re-exporta `ProjetorDeAnalise` ao lado de `projetar_analise`
approval:
  by: user
  at: 2026-10-23T00:44:54-03:00
reversible_via: [../OPP-20261023-MPRA-mistura-caso-uso-projecao/CHG-LOTE-extracao-e-mapper.diff]
---

# Transformacao: OPP-20261023-CLSM (Mapper como classe)

## O que mudou

As seis funcoes de projecao e o ponto de entrada viraram a classe
`ProjetorDeAnalise`:

| Membro | Tipo | Papel |
|---|---|---|
| `_juntar` | staticmethod | consolida pessoa no retrato por xref |
| `_ficha` | staticmethod | `person_summary` para `PessoaDaAnalise` |
| `_papeis_do_caminho` | staticmethod | deriva ascendente/descendente no caminho |
| `_kits` | classmethod | pareia metadados e veredito por indice |
| `_pessoas` | classmethod | monta o retrato e resolve a raiz |
| `_conexao` | classmethod | projeta uma conexao |
| `projetar` | classmethod | ponto publico |

`projetar_analise` continua existindo como fachada funcional, e os nomes
`_juntar`, `_ficha`, `_papeis_do_caminho`, `_kits`, `_pessoas` e `_conexao` sao
re-exportados no nivel do modulo (`_juntar = ProjetorDeAnalise._juntar` e
equivalentes). Os aliases existem para nao quebrar importadores que alcancavam os
auxiliares privados; nenhum teste do projeto depende deles, mas o custo de manter
e uma linha por nome.

## Observacao sobre o resultado

`_kits` esta declarado como `classmethod` e nao usa `cls`. E residuo da conversao
mecanica de funcao para metodo, nao decisao: poderia ser `staticmethod` sem
alterar comportamento. Ficou como esta para nao acrescentar um quarto passo a um
lote que ja estava empilhado; fica registrado como ajuste cosmetico possivel.

## Diff acumulado

O diff e o mesmo das quatro transformacoes de `analise-dna`, pelo motivo
declarado em `OPP-20261023-MPRA`: as etapas foram empilhadas antes da captura.
`CHG-LOTE-extracao-e-mapper.diff` reproduz os dois arquivos a partir do `HEAD`.

## Rede de seguranca

| Momento | Resultado |
|---|---|
| linha de base HEAD 221b6c1 | 1615 passed, 9 skipped |
| working tree depois do lote | 1615 passed, 9 skipped |

Ver [suite-antes.txt](before-after/suite-antes.txt) e
[suite-depois.txt](before-after/suite-depois.txt). Os arquivos herdados, que
declaravam outro ambiente, foram substituidos pela medicao real desta sessao.

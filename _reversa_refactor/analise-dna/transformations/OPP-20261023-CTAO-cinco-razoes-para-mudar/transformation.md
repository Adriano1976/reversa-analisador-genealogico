---
schema_version: 1
id: OPP-20261023-CTAO
verb: modularize
state: applied
safety_net:
  kind: existing
  green_before: true
  green_after: true
preservation:
  method: equivalence-proof
  evidence:
    - safety-net/equivalencia-no-projeto.txt
    - ../OPP-20261023-ORQA-fluxo-de-553-linhas-sem-fronteira/safety-net/equivalencia.py
measurement:
  before: >
    um módulo de 1.258 linhas com 19 símbolos e nove responsabilidades
  after: >
    oito arquivos de 43 a 470 linhas, um por responsabilidade; `dna_analysis.py`
    de 1.258 para 321 linhas
change_set:
  - chg: CHG-001
    file: src/core/dna_analysis.py
    purpose: >
      reduz o arquivo ao caso de uso, à ordem de apresentação e à fachada, e move
      sete módulos novos para `src/core/`
  - chg: CHG-001
    file: src/core/dependencias.py
    purpose: o contrato de borda do núcleo, com endereço próprio
  - chg: CHG-001
    file: src/core/contexto_da_analise.py
    purpose: o estado que não muda entre kits, com os dois caches
  - chg: CHG-001
    file: src/core/rotulos_do_cartao.py
    purpose: as palavras e as classes CSS que o operador lê
  - chg: CHG-001
    file: src/core/validacao_no_cartao.py
    purpose: o veredito de viabilidade temporal
  - chg: CHG-001
    file: src/core/endogamia_no_cartao.py
    purpose: o diagnóstico estrutural, o selo e a frase da seção 5
  - chg: CHG-001
    file: src/core/passo_por_kit.py
    purpose: o pipeline que transforma um kit em cartão ou descarte
  - chg: CHG-001
    file: src/core/cartao_sem_correspondencia.py
    purpose: o cartão do match sem pessoa no GEDCOM
  - chg: CHG-002
    file: tests/test_profundidade_do_caminho.py
    purpose: a guarda passa a ler `passo_por_kit.py`, onde a regra está agora
  - chg: CHG-002
    file: tests/test_veredito_no_nucleo.py
    purpose: o espião do validador passa a morar no módulo que faz a chamada
approval:
  by: user
  at: 2026-10-23T15:20:25-03:00
  plan_at: 2026-10-23T15:10:10-03:00
reversible_via:
  - CHG-001-oito-modulos.diff
  - CHG-002-referencias-aos-testes.diff
---

## A distribuição, antes e depois

| Arquivo | Responsabilidade | Linhas |
|---|---|---|
| `core/dependencias.py` | o contrato de borda | 43 |
| `core/contexto_da_analise.py` | estado entre kits e cache do dossiê | 57 |
| `core/rotulos_do_cartao.py` | palavras e classes CSS | 152 |
| `core/validacao_no_cartao.py` | veredito temporal | 72 |
| `core/endogamia_no_cartao.py` | diagnóstico estrutural e selo | 109 |
| `core/passo_por_kit.py` | um kit vira cartão ou descarte | 470 |
| `core/cartao_sem_correspondencia.py` | cartão do match sem pessoa | 139 |
| `core/dna_analysis.py` | caso de uso, ordem e fachada | 321 |

Um arquivo de 1.258 linhas virou oito, de 43 a 470. O total subiu para 1.363 por
cabeçalho de módulo, docstring e imports.

## O grafo

```
dna_analysis
  ├─ passo_por_kit ─┬─ contexto_da_analise ── dependencias
  │                 ├─ endogamia_no_cartao ── rotulos_do_cartao
  │                 └─ validacao_no_cartao ── rotulos_do_cartao
  └─ cartao_sem_correspondencia ── passo_por_kit
```

Estritamente descendente. Nenhum módulo folha importa um módulo que o importa, e
`core/` continua importando só `utils/`, como o D2 da alma exige.

## Fronteiras preservadas

- A assinatura de `dna_analysis` não mudou.
- `_ordem` continua em `core/dna_analysis.py`, onde `design.md` a ancora.
- A fachada de compatibilidade continua: `__all__` com 14 nomes, todos resolvidos,
  mais `_montar_diagrama`, `_observacoes`, `_observacao_estrutural` e
  `_selo_da_endogamia` reexportados para os instrumentos congelados.
- `core/path_search.py` não foi tocado e continua consumindo `Dependencias`.

## Desvio documental declarado

`analise-dna/requirements.md:296` afirma que `_montar_diagrama` e `_observacoes`
moram em `src/core/dna_analysis.py`. Os dois foram para `passo_por_kit.py`. A
reexportação mantém o caminho de import da spec válido; a imprecisão é sobre o
arquivo físico. `_reversa_sdd/**` não está em caminho liberado para corrigir, e é o
mesmo tipo de desvio que a `OPP-20261006-W4KD` registra.

## O fail do primeiro gate

O `CHG-001` foi aplicado e a suíte voltou com **2 failed, 1623 passed**. Os dois
testes apontavam para o arquivo antigo:

| Teste | Causa | Correção |
|---|---|---|
| `test_profundidade_do_caminho.py::test_o_nucleo_exige_impossivel_e_caminho_para_vetar` | lia `src/core/dna_analysis.py`; a regra foi para `passo_por_kit.py` | o caminho lido acompanha; as asserções são as mesmas |
| `test_veredito_no_nucleo.py::test_uma_chamada_ao_validador_por_resultado` | patcheava `core.dna_analysis.validar_comparacao`; a chamada foi para `core.validacao_no_cartao` | o espião passa a morar no módulo que chama |

O diff foi **revertido** antes de qualquer tentativa, o projeto voltou ao verde, e as
duas correções entraram como `CHG-002`, separadas do diff de código, para poderem
ser lidas sozinhas. Nenhuma asserção foi afrouxada: uma mudou de arquivo lido, a
outra de módulo patcheado.

## Prova

| Verificação | Resultado |
|---|---|
| digest de equivalência, 3 cenários | `b8d186c8…b570b5dd`, idêntico ao de antes da ORQA |
| import dos oito módulos, mais `path_search` | ok |
| `__all__` resolvido por inteiro | 14 de 14 |
| imports sem uso nos sete módulos novos | 0 |
| suíte antes | **1625 passed, 9 skipped** em 95,87 s |
| suíte depois de `CHG-001` sozinho | **2 failed, 1623 passed** em 84,85 s (revertido) |
| suíte depois dos dois `CHG` | **1625 passed, 9 skipped** em 96,61 s |

## O que ficou para depois

Os dois construtores de cartão, de 40 e 41 chaves, agora moram em arquivos
vizinhos: `_cartao_do_kit` em `passo_por_kit.py` e `_cartao_sem_correspondencia` em
`cartao_sem_correspondencia.py`. A duplicação do contrato passou a ser visível e
pode ser tratada numa oportunidade própria, que não é `modularize`.

## Reversão

`git apply -R` nos dois diffs, na ordem inversa.

---
*Aplicado em 2026-10-23 pelo Reversa-Refactor, sob gate de plano e de diff aprovados pelo usuário.*

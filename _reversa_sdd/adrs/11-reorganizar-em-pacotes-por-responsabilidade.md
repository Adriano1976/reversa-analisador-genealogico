# ADR-11 — Reorganizar `reconstructed/` em pacotes por responsabilidade

- **Status:** Aceito e executado
- **Data da decisão:** 2026-10-01 a 2026-10-03
- **Commit(s):** `60ad797` (separa upload), `073b02a` (reorganiza em quatro pacotes), `2a98289` (divide `dna_analysis`), `1212b19` (divide `path_search`), `d673406`, `e40aaa4`, `e0774a6`
- **Confiança:** 🟢 CONFIRMADO

## Contexto

O pacote `reconstructed/` acumulava responsabilidades por **acréscimo histórico**: quatro módulos, sendo dois deles grandes o suficiente para conter fluxos inteiros (`dna_analysis.py` misturava leitura de CSV, matching, faixas de cM, análise e montagem de tela; `path_search.py` misturava busca, navegação e emissão de diagrama). A fronteira entre "ler o mundo de fora", "decidir sobre o que foi lido" e "apresentar" não existia.

## Decisão

Reorganizar em **quatro pacotes de primeiro nível, por responsabilidade**:

| Pacote | Responsabilidade |
| --- | --- |
| `parsers/` | Leitura e tradução do mundo de fora (GEDCOM, CSV) |
| `core/` | Decisão de domínio, **sem saber de HTTP** |
| `reporting/` | Emissão de diagrama e do contrato de escape |
| `utils/` | Autoridades únicas transversais (limpeza, validação, formato) |

Aplicado em série, com as transformações registradas uma a uma (`OPP-*`) no `_reversa_sdd/addenda/003-refactor-code-quality.md`.

## Evidência

- `073b02a` — "refactor(src): reorganiza reconstructed em core, parsers, reporting e utils".
- Composição atual, verificada: `core/` (12 módulos + `__init__`), `parsers/` (2 + `__init__`), `reporting/` (1 + `__init__`), `utils/` (3 + `__init__`).
- Divisões específicas: `dna_analysis.py` → `matching.py` + `name_normalization.py` + `cm_estimator.py` (`2a98289`); `path_search.py` → `path_search.py` (fachada) + `path_finding.py` + `family_navigation.py` + `documentary_relationship.py` (`1212b19`).
- A reorganização foi **pré-requisito** da regra final da análise (ADR-14): sem `core/` separado de `reporting/`, a separação dos três eixos não teria onde morar.

## Justificativa

A responsabilidade declarada de cada módulo é a fronteira que permite **testar decisão sem HTTP** e **trocar apresentação sem tocar domínio**. Foi essa fronteira que tornou possível, semanas depois, extrair o confronto como máquina de estados própria (`state-machines.md` §3).

## Consequências

- ✅ `code-analysis.md` consegue hoje atribuir **um arquivo a uma unidade funcional** com base na docstring de responsabilidade de cada módulo, e a soma das quatro unidades **fecha exatamente** as 3.489 linhas de `src/`.
- ✅ A separação `parsers/` × `core/` é o que garante, por construção, as duas proibições do domínio: `genetic_evidence` **não importa** o GEDCOM e `documentary_relationship` **não lê cM`.
- ⚠️ **Custo deliberado: as "superfícies de compatibilidade".** Vários módulos mantêm um `__all__` que **reexporta nomes históricos** que já não usam (ex.: `path_search.py:61-64` declara explicitamente que `are_spouses`, `MAX_DEPTH`, `_mermaid_label` e outros "não são usados por `path_search`" e estão ali só por compatibilidade, porque testes e sondas os importam dali). Isso é **dívida técnica de teste**, não de produção.
- ⚠️ **A divisão de `dna_analysis` deixou um resíduo:** `cm_estimator` permanece no pacote como legado fora do fluxo (ADR-19), reexportado por `dna_analysis`. É a exceção declarada à regra de responsabilidade única.

## Alternativas consideradas

- **Manter `reconstructed/` e apenas dividir os arquivos grandes.** Descartada: preservaria o nome que descreve **como** o código nasceu ("reconstruído") em vez do que ele **é**.
- **Reorganizar por camada técnica (`models/`, `services/`, `views/`).** Descartada implicitamente: a escolha foi por **responsabilidade de domínio**, coerente com a separação dos três eixos que viria no ADR-14.

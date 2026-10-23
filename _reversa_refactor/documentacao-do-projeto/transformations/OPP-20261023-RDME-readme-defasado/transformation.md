---
schema_version: 1
id: OPP-20261023-RDME
verb: standardize
state: applied
safety_net:
  kind: existing
  green_before: true
  green_after: true
preservation:
  method: pattern-only
  evidence:
    - safety-net/arvore-conferida.txt
    - safety-net/suite-depois.txt
    - safety-net/markdownlint.txt
measurement:
  before: "README com 6 modulos ausentes na arvore, sem src/web/ e contagem de 49 arquivos e 12.715 linhas nao reproduzivel"
  after: "README com 54 arquivos na arvore, src/web/ e projecao; 55 arquivos .py, 11.099 linhas nao vazias e 59 arquivos no total, com metodo declarado"
change_set:
  - chg: CHG-001
    file: README.md
    purpose: alinha o paragrafo de arquitetura, a arvore de src/, a linha do app.py e a contagem ao codigo
approval:
  by: user
  at: 2026-10-23T13:47:49-03:00
reversible_via: [CHG-001-readme-alinhado.diff]
---

# Transformacao: OPP-20261023-RDME (README alinhado ao codigo)

## Padrao detectado

O README descreve a estrutura em uma arvore de diretorios com uma linha por
modulo, e a arquitetura em um paragrafo que nomeia os pacotes. A contagem da raiz
de `src/` existia sem metodo. O lote seguiu esse padrao: uma linha por modulo novo,
o mesmo formato de comentario e a contagem com o metodo declarado ao lado.

## O que mudou

| Trecho | Antes | Depois |
|---|---|---|
| paragrafo de arquitetura | `src/app.py` era a borda HTTP | borda e `src/app.py` com `create_app()` mais `src/web/` |
| linha do `app.py` | 5 rotas, 5 actions, montagem das dependencias | `create_app`, Blueprint de assets e estado de borda injetavel |
| `application/` | 7 modulos | 8, com `projecao_analise.py` |
| `core/` | 21 modulos | 26, com `cobertura_do_arquivo`, `fontes_de_laboratorio`, `graus_de_parentesco`, `qualidade_da_medida` e `sem_correspondencia` |
| `web/` | ausente | `__init__.py` e `rotas_assets.py` |
| contagem | 49 arquivos, 12.715 linhas | 55 `.py` com 11.099 linhas nao vazias; 59 arquivos no total, com data e exclusoes |

O lote tem 16 insercoes e 6 remocoes em um unico arquivo.

## O que NAO mudou

- nenhuma linha de `src/`, `tests/` ou de qualquer artefato de `_reversa_sdd/`;
- nenhuma rota, mensagem, status ou comportamento;
- o restante do README, fora dos seis hunks.

## Prova

| Verificacao | Resultado |
|---|---|
| arvore nova conferida contra o disco | 54 arquivos, 0 faltando |
| suite completa | 1625 passed, 9 skipped em 74,14 s |
| `git diff --check` | sem erro de whitespace |
| `markdownlint-cli2` | nao executado: sem `node_modules`; `npx` nao foi usado para baixar da rede |

A suite foi rodada como confirmacao de que a padronizacao nao tocou em semantica,
e nao porque documentacao tenha comportamento. O numero e identico ao estado
anterior. Evidencia em [arvore-conferida.txt](safety-net/arvore-conferida.txt),
[suite-depois.txt](safety-net/suite-depois.txt) e
[markdownlint.txt](safety-net/markdownlint.txt).

## Reversibilidade

`CHG-001-readme-alinhado.diff` aplica os seis hunks e reverte pelo mesmo diff.
Nao ha arquivo novo nem removido.

---
schema_version: 1
id: OPP-20260929-5XGJ
verb: standardize
state: applied
safety_net:
  kind: existing
  green_before: true
  green_after: true
preservation:
  method: pattern-only
  evidence:
    - before-after/equivalence-proof.txt
    - safety-net/pytest-after-apply.txt
change_set:
  - chg: CHG-001
    kind: code
    artifact: analisador-genealogico/reconstructed/path_search.py
    purpose: Unifica o contrato de import com `.upload` em um único lugar, move `ref_id` do rodapé para o topo e documenta por que `graph` não pode seguir a mesma regra
    diff: CHG-001.diff
approval:
  by: user
  at: 2026-10-01T03:40:56-03:00
reversible_via: [CHG-001.diff]
---

## Padrão detectado

O projeto pratica uma regra única e consistente em todos os módulos: `from __future__ import annotations`
primeiro, stdlib, linha em branco, terceiros, linha em branco, e os imports relativos ao final do bloco,
todos no topo do arquivo e em ordem alfabética.

| Módulo | Imports relativos | Onde |
|--------|-------------------|------|
| `reconstructed/upload.py` | nenhum | n/a |
| `reconstructed/domain.py` | nenhum | n/a |
| `reconstructed/dna_analysis.py` | `.domain`, `.path_search`, `.upload` | topo, linhas 22 a 24 |
| `reconstructed/path_search.py` | `.upload` | linha 20, **e também 131 e 506** |
| `app.py` | `reconstructed.*` | topo, linhas 5 a 7 |

`path_search.py` era a **única** exceção, e a única ocorrência de `# noqa: E402` em todo o projeto.

## O que foi feito

Três mudanças, todas de organização de import. Nenhum corpo de função foi tocado e nenhuma saída muda.

| # | Antes | Depois |
|---|-------|--------|
| 1 | `from .upload import child_to_family, families, get_name, people` (linha 20) | a mesma linha com `ref_id` acrescentado, precedida de um bloco de 4 linhas que enuncia o contrato |
| 2 | `from .upload import graph` (linha 131, sem explicação) | a mesma linha, precedida de um comentário de 2 linhas dizendo que `graph` é reatribuído |
| 3 | `# Re-exporta ref_id ...` mais `from .upload import ref_id  # noqa: E402` (linhas 505 e 506) | removidos; `ref_id` passa a vir do import do topo |

O `# noqa: E402` suprimia um aviso que **ninguém emite**: não há ruff, flake8, setup.cfg nem pyproject
no projeto. A supressão era decorativa desde sempre.

## Uma coisa que já estava resolvida

O comentário do rodapé dizia "Re-exporta `ref_id` usado internamente". Varredura no repositório
inteiro: `ref_id` é importado de `reconstructed.upload` em `tests/test_upload.py:20`, e **nenhum**
arquivo o importa de `path_search`. Ou seja, o "re-export" não tinha consumidor.

Ainda assim, a mudança o preserva de graça: como `ref_id` passou a integrar o import do topo, o nome
continua existindo no namespace do módulo. Nada que porventura dependesse disso quebra.

## Prova

Além da conferência de padrão, que é o método declarado para padronização, rodei duas provas
mecânicas, porque a mudança toca exatamente o mecanismo que o comentário descreve.

**Equivalência, com importação real do módulo** (`before-after/equivalence-proof.txt`):

| Verificação | Resultado |
|-------------|-----------|
| `P.ref_id is U.ref_id` | `True`, o re-export sobreviveu |
| `U.graph` antes do parse | `None` |
| `U.graph` depois do parse | 5 nós, 3 arestas |
| `find_indirect_path(@I1@, @I2@)` depois do rebind | caminho de 2 nós |
| `P.people is U.people`, `P.families is U.families` | `True`, os mutados continuam vivos |
| `U.get_name is P.get_name` | `True` |

O quarto item é o que importa: prova que o import tardio de `graph` **continua captando a
reatribuição**. Se a padronização tivesse movido `graph` para o topo, este teste devolveria `None`.

**Harness de paridade diferencial** (`_reversa_sdd/parity/harness.py`), reexecutado depois da mudança:
**PARIDADE 100%, zero divergência** nas 6 fixtures GEDCOM. Amostra de pares reduzida a 3x3 em vez dos
40x40 padrão; o resto da coleta foi completo.

**Suíte completa**: `85 passed, 1 error`. Idêntico ao estado anterior à mudança. O erro é o
`PermissionError` do sandbox em `test_ensure_dirs_creates_uploads`, que reproduz em qualquer
`--basetemp` e não tem relação com esta transformação.

## Estado do arquivo

| Arquivo | Antes | Depois |
|---------|-------|--------|
| `reconstructed/path_search.py` | 506 linhas | 508 linhas |
| Ocorrências de `noqa: E402` no projeto | 1 | 0 |

## Conferência contra a alma

Nenhuma regra de negócio é tocada. O contrato de import documentado é uma consequência direta de
`upload.py:15-19` declarar estado global mutável e de `load_gedcom_and_build_graph` reatribuir `graph`.
A decisão de manter o estado global é preservada exatamente como está: esta transformação não a
questiona, apenas torna explícito o que quem lê precisava descobrir. A
`OPP-20260929-EHNZ` continua sendo o lugar certo para discutir o acoplamento em si.

## Reversão

Por `git apply -R CHG-001.diff`, ou por
`git checkout -- analisador-genealogico/reconstructed/path_search.py`.

---
*Gerado pelo Reversa-Standardize em 2026-10-01.*

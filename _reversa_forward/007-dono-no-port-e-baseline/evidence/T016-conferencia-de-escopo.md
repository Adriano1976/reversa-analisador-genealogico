# T016 — conferência de escopo

> Rodada de `/reversa-coding`, 2026-10-07.
> O que esta conferência responde: **a feature mexeu em alguma coisa que não devia?**

## 1. Os arquivos alterados, e só eles

```text
 src/app.py                                  |  31 ++-
 src/application/upload_gedcom.py            |  14 +-
 src/ports/__init__.py                       |  51 ++-
 src/ports/adaptadores.py                    |  28 ++-
 tests/conftest.py                           | 124 +++++++---
 tests/test_porta_de_armazenamento.py        | 259 ++++++++++++++++++++-
```

São **seis** arquivos rastreados, e são exatamente os seis que o `roadmap.md` §5
declarou. Mais um arquivo **novo**, não rastreado:
`tests/test_ambiente_temporario_da_suite.py`.

Os três arquivos de `_reversa_forward/003-...` e `.reversa/active-requirements.json`
já estavam modificados **antes** desta feature (a `003` está pausada) e não foram
tocados por ela.

## 2. O que não podia mudar, e não mudou

| Alvo | Verificação | Resultado |
|---|---|---|
| `src/core/` | `git diff --name-only` | **sem alteração** |
| `src/parsers/` | `git diff --name-only` | **sem alteração** |
| `src/reporting/` | `git diff --name-only` | **sem alteração** |
| `src/utils/` | `git diff --name-only` | **sem alteração** |
| `pytest.ini` | `git diff` | **intocado** — e está fora de `allowedPaths` |
| `.gitignore` | `git diff` | **intocado** — e está fora de `allowedPaths` |
| `tests/test_upload_seguranca.py` | `git diff --stat` | **VAZIO** — nenhuma alteração, é a `RF-06` |

A ausência de alteração em `src/core/` é a `RF-11` medida: a assinatura de retorno
do núcleo continua congelada, e nenhuma constante de domínio foi tocada. A paridade
em 100 % no `T014` é a segunda metade da mesma prova.

## 3. Os 13 diretórios presos continuam presos, e isso é o esperado

| Caminho | Existe | Listável |
|---|---|---|
| `.pytest-tmp/final` | sim | **não** |
| `.pytest-tmp/pytest-of-Adriano Santos` | sim | **não** |
| `.pytest-tmp/refactor-run` | sim | **não** |
| `.pytest-tmp/run` | sim | **não** |
| `.pytest-tmp/run1` | sim | **não** |
| `.pytest-tmp/run2` | sim | **não** |
| `.pytest-tmp/verify` | sim | **não** |
| `_reversa_refactor/.pytest-baseline` | sim | **não** |
| `_probe_acl/os_mkdir_700` | sim | **não** |
| `_probe_acl/path_mkdir_700` | sim | **não** |
| `_probe_acl2/sete` | sim | **não** |
| `src/uploads/_pytest` | sim | **não** |
| `tests/_basetemp_probe` | sim | **não** |

(12 caminhos de topo, 13 diretórios inacessíveis: `_probe_acl` e `_probe_acl2` são
listáveis e os seus três filhos **não** são.)

**Nenhum foi removido**, por decisão registrada na sessão de esclarecimento: eles
são resíduo de execução, não defeito do produto, e a remoção exige shell elevado —
privilégio que a sessão não tem. O que a feature fez foi **impedir que novos
apareçam**: a partir do Bloco 0 a suíte não cria mais o diretório-base com `0o700`.

Por isso o `collect_ignore = ["_basetemp_probe"]` de `tests/conftest.py`
**permanece**. Sem ele, o pytest desce no diretório preso e a coleta da suíte
aborta inteira.

O inventário com o comando de remoção em lote está em
`_reversa_forward/006-fronteira-aplicacao-ports/evidence/README-evidencias.md` §2.2.

## 4. Resíduo de instrumento: encontrado, limpo, e um achado

O instrumento de paridade (`_reversa_sdd/parity/harness.py`) escreve **quatro**
artefatos de trabalho no workspace, e os recria a cada execução:

| Artefato | Coberto pelo `.gitignore`? | Situação |
|---|---|---|
| `.parity-run-oracle/` | **sim** | removido nesta limpeza |
| `.parity-run-cand/` | **NÃO** | removido nesta limpeza |
| `_reversa_sdd/parity/_collect_oracle.py` | **NÃO** | removido nesta limpeza |
| `_reversa_sdd/parity/_collect_cand.py` | **NÃO** | removido nesta limpeza |

A remoção é segura **por construção**: `run_collector` (`harness.py:458-462`) grava
`os.path.join(HERE, "_collect_%s.py" % tag)` e faz `os.makedirs(run_dir,
exist_ok=True)` a cada chamada. Não existe estado a preservar.

🔴 **Achado, para ato do usuário:** `.parity-run-cand/` **não** está no `.gitignore`,
enquanto o irmão `.parity-run-oracle/` está. Consequência: **toda** execução do
harness deixa o workspace sujo de `git status`, o que já acontecia antes desta
feature. Corrigir isso é acrescentar uma linha ao `.gitignore` — arquivo que **não
está** em `allowedPaths`, então a correção é ato do usuário e fica registrada aqui
em vez de silenciada.

⚠️ **A mesma consequência do `tests/.tmp/`**, também fora de `allowedPaths`: a rede
contra resíduo é a remoção, e não uma linha de ignore. As duas linhas sugeridas são:

```gitignore
tests/.tmp/
.parity-run-cand/
```

## 5. Estado do `git status` ao fim da rodada

```text
 M .reversa/active-requirements.json                       (pre-existente, feature 003)
 M _reversa_forward/003-.../actions.md                     (pre-existente, feature 003)
 M _reversa_forward/003-.../progress.jsonl                 (pre-existente, feature 003)
 M src/app.py
 M src/application/upload_gedcom.py
 M src/ports/__init__.py
 M src/ports/adaptadores.py
 M tests/conftest.py
 M tests/test_porta_de_armazenamento.py
?? _reversa_forward/007-dono-no-port-e-baseline/
?? tests/test_ambiente_temporario_da_suite.py
```

Nenhum resíduo de `src/uploads/`, de `tests/.tmp/` nem de instrumento. Os dois
`??` são a feature nova — artefatos e o arquivo de teste que ela acrescenta.

## 6. Atualização — as duas linhas do `.gitignore` foram acrescentadas

⚠️ **Este `git status` não é mais o estado atual do workspace, e a diferença é
esta:** as duas linhas sugeridas na §4 **foram acrescentadas** ao `.gitignore`.

```diff
 .parity-run-oracle/
 .parity-tmp/
 .pytest-tmp/
+tests/.tmp/
+.parity-run-cand/
 _reversa_sdd/parity/_obs_*.json
```

**Autoria e momento, para o registro não ficar ambíguo.** A alteração foi feita
**fora desta sessão**: nenhum comando desta rodada escreve em `.gitignore` — o
arquivo está fora de `allowedPaths`, e a §2 acima o mediu como **intocado** no
momento da conferência. O `mtime` do arquivo é `2026-10-07 15:41:42`, segundos
depois de o relatório do `/reversa-coding` publicar a sugestão. É o **ato do
usuário** que a §4 pedia, e ele veio antes do `/reversa-sync`.

**Verificado, e não presumido.** Os dois padrões foram medidos com arquivo dentro
dos diretórios — diretório vazio não serve para medir `.gitignore`, porque o git não
rastreia diretório vazio de qualquer forma:

```text
$ git check-ignore -v "tests/.tmp/_probe_ignore/x.txt" ".parity-run-cand/x.txt"
.gitignore:22:tests/.tmp/          tests/.tmp/_probe_ignore/x.txt
.gitignore:23:.parity-run-cand/    .parity-run-cand/x.txt

$ git status --short   (com os dois diretórios criados e um arquivo em cada)
  -> não lista nenhum dos dois
```

Consequência: as duas pastas de resíduo que este documento registra na §4 deixam de
aparecer no `git status` a partir de agora. O resíduo **em disco** continua existindo
enquanto o instrumento rodar; o que muda é ele deixar de ser um item não rastreado.
As pastas de teste usadas nesta verificação foram removidas.

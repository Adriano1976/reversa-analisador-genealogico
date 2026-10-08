# Limpeza dos diretórios presos, em 2026-10-08

Registro da remoção do resíduo de ACL que a feature `006-fronteira-aplicacao-ports` inventariou
como **13 diretórios presos** e que, em 2026-10-08, eram **22**. Diferente de outras evidências desta
feature, este arquivo é posterior ao fechamento dela: nasceu da execução da `OPP-20261008-JXQN` do
registro `_reversa_refactor/`, no contexto `analise-dna`.

O inventário original e o comando em lote de então estão em `README-evidencias.md` §2.2, e ficam
como estão: são o registro datado da feature. Este arquivo é o delta.

## O que são esses diretórios

Diretórios criados com `mode=0o700` por `TempPathFactory.getbasetemp()` do pytest, ou por
experimentos de ACL feitos à mão, num sistema de arquivos que traduz aquele modo para uma ACL que
**recusa `os.scandir`** para o próprio dono. O efeito prático: o diretório existe, aparece na
listagem do pai e não pode ser lido, percorrido nem removido por um shell comum.

Não são regressão do produto. São resíduo de execução, e o custo deles é real: já abortaram o
`docker build` (o que motivou o `.dockerignore` virar lista de permissão, `D-18`), já obrigaram uma
linha de `collect_ignore` no `tests/conftest.py` para a coleta não abortar inteira, e já consumiram
tempo em pelo menos três features.

## Receita que funciona

Ordem obrigatória, num shell **elevado**:

```powershell
takeown /f <diretorio> /a
icacls <diretorio> /reset
```

Medido em 2026-10-08: sem elevação, `takeown` responde *"o usuário que fez logon não tem privilégios
administrativos"* e `icacls` responde *"Acesso negado"*. **Depois do `icacls /reset`, a remoção
funciona sem elevação**, porque as permissões herdadas voltam e o diretório passa a se comportar
como qualquer outro. Para os 22 deste dia, bastou uma passada de `takeown` mais `icacls /reset`; a
deleção em si foi feita depois, sem elevação.

### Armadilha do PowerShell, medida neste dia

`rd` e `del` são **aliases de `Remove-Item`** no PowerShell. Um script escrito com sintaxe de `cmd`
falha assim, diretório por diretório:

```text
Remove-Item : Não é possível localizar um parâmetro posicional que aceite o argumento '/q'.
```

Use `Remove-Item -LiteralPath <dir> -Recurse -Force`, ou então `cmd /c rd /s /q <dir>`.

## Removidos em 2026-10-08

### Vazios, removidos sem elevação (5)

| Diretório |
|---|
| `tests/_basetemp_ok` |
| `_reversa_bugs/busca-caminho/bugs/BUG-20260929-J6PQ-escape-incompleto-mermaid/fix` |
| `_reversa_bugs/busca-caminho/bugs/BUG-20261002-T4ZM-rotulo-descarta-caracteres-inertes/fix` |
| `_reversa_refactor/arquitetura-src/transformations/OPP-20261006-ESKO-superficie-de-compatibilidade/before-after` |
| `_reversa_refactor/arquitetura-src/transformations/OPP-20261006-LIGH-aresta-csv-ingest/before-after` |

`os.rmdir` foi usado: ele recusa diretório não vazio, então nenhum arquivo foi perdido.

### Presos, removidos após o `icacls /reset` (14)

| Diretório |
|---|
| `tests/_basetemp_probe` |
| `src/uploads/_pytest` |
| `_reversa_refactor/.pytest-baseline` |
| `_reversa_forward/008-persistencia-postgres-docker/.probe/tmp/pip-build-tracker-4ap6k881` |
| `_reversa_forward/008-persistencia-postgres-docker/.probe/tmp/pip-build-tracker-rdp810dc` |
| `_reversa_forward/008-persistencia-postgres-docker/.probe/tmp/pip-build-tracker-ynfyvhng` |
| `_reversa_forward/008-persistencia-postgres-docker/.probe/tmp/pip-download-4liezde1` |
| `_reversa_forward/008-persistencia-postgres-docker/.probe/tmp/pip-download-5w482oq2` |
| `_reversa_forward/008-persistencia-postgres-docker/.probe/tmp/pip-download-ef796gg6` |
| `_reversa_forward/008-persistencia-postgres-docker/.probe/tmp/pip-unpack-_decj2do` |
| `_reversa_forward/008-persistencia-postgres-docker/.probe/tmp/pip-unpack-o1w9li49` |
| `_reversa_forward/008-persistencia-postgres-docker/.probe/tmp/pip-unpack-sfuexdkx` |
| `_reversa_forward/008-persistencia-postgres-docker/.probe/tmp` |
| `_reversa_forward/008-persistencia-postgres-docker/.probe` |

Os dois últimos ficaram vazios depois dos nove `pip-*` e foram removidos na sequência.

### Cicatriz no código, fechada

Com `tests/_basetemp_probe` fora, a linha `collect_ignore = ["_basetemp_probe"]` do
`tests/conftest.py` perdeu a razão e foi removida, junto da reescrita da seção 4 do docstring do
mesmo arquivo. Enquanto o diretório existisse, remover a linha faria a **coleta inteira abortar** com
`PermissionError`, e a suíte ficaria cega por um diretório vazio.

## Resgate antes da limpeza do `.pytest-tmp`

Medido em 2026-10-08: `.pytest-tmp/` não guarda apenas diretórios vazios. Ele tem **72 arquivos
soltos** (36 `.py`, 22 `.ged`, 11 `.txt`, 2 `.diff`, 1 `.md`, 250,6 KB) e 26 subdiretórios, todos
fora do versionamento. Documentação e registros citam caminhos `.pytest-tmp/<algo>` em **54
ocorrências**, com 21 alvos distintos, e **6 desses alvos já não existem** (`baseline`,
`pytest-of-Adriano`, `qmly-run`, `tdprobe`, `uxef-ensaio`, `zv52-ensaio`). A decadência já estava em
curso antes desta limpeza.

Quatro arquivos ainda citados eram a **única cópia em disco**, então foram copiados para o registro
que os cita, antes de qualquer remoção:

| Arquivo | Destino | Quem cita |
|---|---|---|
| `probe_mermaid.py` | `_reversa_bugs/busca-caminho/bugs/BUG-20260929-J6PQ-.../evidence/` | `verificacao-codigo.md` |
| `probe-qmly.py` | `_reversa_bugs/upload-gedcom/bugs/BUG-20260929-QMLY-.../evidence/` | `LEIA-ME-sonda.md`, `reproduction.md` |
| `probe-qmly-saida.txt` | `_reversa_bugs/upload-gedcom/bugs/BUG-20260929-QMLY-.../evidence/` | `bug.md`, `verificacao-medida.md` |
| `probe_fuzzy_profile.py` | `_reversa_refactor/analise-dna/transformations/OPP-20260929-AU76-cache-de-atributos/before-after/` | `OPP-20260929-AU76-...md` |

**Correção de um registro:** o `verificacao-codigo.md` do `BUG-20260929-J6PQ` afirmava que
`probe_mermaid.py` tinha "cópia durável em `evidence/probe_mermaid.py`". Essa cópia **não existia**
até esta data. Com o resgate acima, a afirmação passa a ser verdadeira.

## O que ainda falta, e por quê

Dez diretórios seguem em disco. Todos já estão **listáveis** desde o `icacls /reset`, então a
remoção deles **não precisa mais de elevação**:

| Diretório | Por que ainda está lá |
|---|---|
| `.pytest-tmp/final`, `.pytest-tmp/pytest-of-Adriano Santos`, `.pytest-tmp/refactor-run`, `.pytest-tmp/run`, `.pytest-tmp/run1`, `.pytest-tmp/run2`, `.pytest-tmp/verify` | `.pytest-tmp/**` não está em `allowedPaths` de `.reversa/reversa-config.json`, e o agente obedece à política |
| `_probe_acl/os_mkdir_700`, `_probe_acl/path_mkdir_700`, `_probe_acl2/sete` | idem: `_probe_acl*/**` não está liberado |

Junto deles, o mesmo motivo de política mantém o resíduo não travado: a pasta `.pytest-tmp/`
inteira (72 arquivos e 26 subdiretórios, dos quais 19 vazios), `.parity-run-cand/`,
`.parity-run-oracle/`, `.pytest_cache/`, `__pycache__/` da raiz, a pasta órfã `uploads/` (8,04 MB,
com 3 dos 4 arquivos idênticos byte a byte a cópias em `src/uploads/`) e os quatro
`_reversa_docs/.backup-*` (5,16 MB). Com o resgate da seção anterior, apagar `.pytest-tmp/` inteira
não destrói nenhuma evidência citada.

O bloco corrigido para fechar isso está na conversa, e não foi gravado aqui porque a remoção é ato do
operador, não deste registro.

---
*Gerado pelo Reversa-Refactor em 2026-10-08, a partir da execução da `OPP-20261008-JXQN`.*

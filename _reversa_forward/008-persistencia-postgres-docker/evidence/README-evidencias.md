# Evidências: instrumentos, resíduos e defeitos de ambiente

> Feature: `008-persistencia-postgres-docker` · Data: `2026-10-08` · Ação: `T024`

Este arquivo existe para que a próxima pessoa — e a próxima extração — não atribuam à feature
o que é do ambiente, e não tropecem no que já foi medido.

## 1. Instrumentos desta rodada

| Instrumento | O que é | Onde a saída está |
|---|---|---|
| `_bloco0-build.log` | Saída bruta do `docker compose build --progress plain`, de onde saiu o **contexto de 250,70 kB** | `evidence/` |
| `_t020_verificar_adapter.py` | Script **executado dentro do contêiner** com `docker compose exec app python`. Faz as **24** verificações que o `T014` não pode fazer no host: dois kits sem soma, ordem, estados por kit, ida e volta do cM nas seis fronteiras, `NULL` em vez de zero, aviso em vez de exceção e transação única | `evidence/T020-ponta-a-ponta.md` |
| `_tmp_e2e/arvore.ged` | GEDCOM **sintético** (cinco pessoas), de `tests/fixtures/sample_dna.py` | — |
| `_tmp_e2e/matches.csv`, `matches_dois_kits.csv` | CSVs **sintéticos**. O segundo usa kits `AA1234567`/`BB7654321` — e o padrão do valor **importa**, ver §3 | — |
| `T010-pre-medicao-parcial-sem-motor.md` | A metade do `T010` que não precisa do motor, medida **antes** de o motor subir | `evidence/` |

⚠️ **Nenhum instrumento desta rodada usou dado real.** O `src/uploads/` do host tem o GEDCOM
real do operador, e ele não foi lido, copiado nem citado em nenhum passo.

## 2. Resíduo dentro do projeto: `.probe/`

```
_reversa_forward/008-persistencia-postgres-docker/.probe/tmp/pip-*
```

**20 entradas ilegíveis**, criadas por esta sessão quando a sonda de `pip` falhou
(`investigation.md` M-06). Elas nasceram com `0o700`, e nesta máquina um diretório criado
assim não é listável nem removível. **Nenhum dos três métodos comuns funciona:**

| Tentativa | Resultado |
|---|---|
| `Remove-Item -Recurse -Force` | falha |
| `cmd /c rd /s /q` | "Acesso negado" em 20 arquivos |
| `icacls /reset /t` | "Processados com sucesso 0 arquivos; falha no processamento de 20" |

A remoção exige **shell elevado**:

```powershell
takeown /f _reversa_forward\008-persistencia-postgres-docker\.probe /a
icacls _reversa_forward\008-persistencia-postgres-docker\.probe /reset /t
rd /s /q _reversa_forward\008-persistencia-postgres-docker\.probe
```

**Consequência enquanto ele existir:** o `.dockerignore` da raiz precisa mantê-lo fora do
contexto de build, e a **lista de permissão** da `D-18` já faz isso — `_reversa_*/` está fora
por construção. É por isso que o `T008` construiu sem tropeçar nele.

## 3. Defeitos de ambiente medidos nesta rodada

| Defeito | Sintoma | Onde está medido |
|---|---|---|
| **`pip` não instala no `.venv/` do host** | `Errno 13 Permission denied` no diretório que o `pip` cria com `0o700`. Apontar `TEMP`/`TMP` para dentro do workspace **não resolve** | `OBS-02`, `OBS-15`, `investigation.md` M-06 |
| **O CLI do Docker precisa de named pipe** | `permission denied ... npipe:////./pipe/dockerDesktopLinuxEngine`. O modo confinado bloqueia named pipes, então **cada comando Docker exige autorização** | `OBS-12` |
| **22 diretórios presos na raiz** | Recusam `os.scandir`. Dez deles **não** casavam com a lista de exclusão original, e derrubariam o `docker build` | `A002` da auditoria, `D-18` |
| **O motor do Docker não estava em execução** | `unable to get image 'genealogia-app'`. O CLI estava instalado | `OBS-08`, resolvido em `OBS-11` |

⚠️ **Nenhum dos quatro é defeito do produto nem desta feature.** Os quatro são anteriores a
ela, com exceção dos 12 diretórios do `.probe/`, que são desta sessão e estão declarados na §2.

## 4. Consequência prática para quem for repetir a verificação

1. **`pip` não funciona no host.** Para conferir disponibilidade de pacote, use a API do PyPI.
   Para executar código que precise do driver, use o **contêiner** — foi o que o `T020` fez.
2. **Todo comando Docker precisa de autorização.** Agrupe o que puder num comando só: foi
   assim que o Bloco 0 (`T008`–`T010`) rodou de uma vez.
3. **A suíte roda SEM `DATABASE_URL`.** Com a variável definida ela dá **duas** falhas
   **de propósito** — o guarda do arquivo do estado desabilitado. Ver `T022`.
4. **Fixture sintética com dois kits exige valor no padrão `[A-Z]{1,3}\d{4,8}`.** Com `KIT-A`
   a coluna de kit **não é detectada**, as duas linhas viram um match `SEM-KIT` e o cM é somado
   — e o resultado parece defeito de agregação da persistência. Ver `OBS-22`.

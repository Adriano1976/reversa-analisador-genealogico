# T001 — Pré-requisito de permissão

> Feature: `008-persistencia-postgres-docker`
> Data: `2026-10-08`
> Ação: `T001` do `actions.md` — "Verificar o pré-requisito de permissão"
> **Veredito: NÃO ATENDIDO. O Bloco 0 para aqui.**

## 1. O que foi lido

`.reversa/reversa-config.json`, na íntegra e sem edição:

```json
{ "version": 1,
"allowLegacyEdits": true,
  "allowedPaths": ["analisador-genealogico/**", "tests/**", "README.md", "pyrefly.toml",
                 "src/**", ".vscode/**", "requirements.txt", ".markdownlint-cli2.jsonc"]
}
```

- `allowLegacyEdits`: **`true`** — a edição do legado está liberada.
- `allowedPaths`: **não vazio** — então a liberação **não** é irrestrita: vale só para os
  caminhos que casam com algum glob da lista.

## 2. O que a feature precisa escrever, e o que casa

| Caminho exigido pela feature | Ação que escreve | Glob que casa? | Situação |
|---|---|---|---|
| `.dockerignore` (raiz) | `T002` | **nenhum** | 🛑 recusado |
| `docker/Dockerfile` | `T003` | **nenhum** | 🛑 recusado |
| `init.sql` (raiz) | `T004`, `T005` | **nenhum** | 🛑 recusado |
| `docker-compose.yml` (raiz) | `T006` | **nenhum** | 🛑 recusado |
| `requirements.txt` | `T007` | `requirements.txt` | ✅ liberado |
| `src/**` (porta, adaptador, caso de uso, borda, template) | `T012`–`T017` | `src/**` | ✅ liberado |
| `tests/**` (testes novos) | `T014`, `T018`, `T019` | `tests/**` | ✅ liberado |

**Quatro dos sete caminhos estão fora da política**, e são exatamente os quatro que o
`T001` foi escrito para conferir: `docker/**`, `docker-compose.yml`, `init.sql` e
`.dockerignore`.

## 3. Por que a execução para, e não contorna

A política de edição do legado do Reversa é explícita: com `allowLegacyEdits: true` e
`allowedPaths` não vazio, **escreve-se apenas em caminhos que casem com algum glob da lista**.
Os quatro caminhos acima não casam. Escrevê-los seria violar a regra do projeto, e o
`actions.md` já declara o que fazer nesse caso:

> A política de edição do legado precisa liberar `docker/**`, `docker-compose.yml`,
> `init.sql` e `.dockerignore` antes de qualquer escrita na raiz. O Reversa **não** edita
> `.reversa/reversa-config.json` por iniciativa própria: a liberação é ato do usuário.

O `T001` **não falhou**: ele executou a verificação e chegou ao veredito que existia para
produzir. O que não pode começar é o `T002`, e com ele o Bloco 0.

⚠️ **Nenhum contorno foi tentado, e a razão é de natureza, não de conveniência.** O
`docker-compose.yml`, o `init.sql` e o `.dockerignore` poderiam ser escritos "por fora" — mas
o ponto do `T001` é justamente que a liberação seja **ato do usuário**, verificável no
arquivo de configuração, e não uma decisão do agente executando a feature que a regra
restringe.

## 4. O que o usuário precisa editar

Acrescentar **três** entradas a `allowedPaths` em `.reversa/reversa-config.json` —
`docker/**` cobre o `Dockerfile`, `init.sql` e o `docker-compose.yml` vão na raiz, e o
`.dockerignore` também:

```json
"allowedPaths": ["analisador-genealogico/**", "tests/**", "README.md", "pyrefly.toml",
                 "src/**", ".vscode/**", "requirements.txt", ".markdownlint-cli2.jsonc",
                 "docker/**", "docker-compose.yml", "init.sql", ".dockerignore"]
```

Com a lista acima, os sete caminhos da §2 passam a casar. **Este arquivo é do usuário**: o
Reversa não o edita, nem a pedido da conversa.

## 5. Segundo impedimento, medido na mesma rodada

Mesmo com a liberação acima, o `T007` tem **duas** metades, e a segunda não é executável
nesta máquina:

```
.venv\Scripts\python.exe -m pip install --dry-run --no-deps psycopg2-binary
→ ERROR: Could not install packages due to an OSError: [Errno 13] Permission denied:
  'C:\Users\venda\AppData\Local\Temp\dsh-UZ9O8Y\pip-unpack-fplmmb3h\
   psycopg2_binary-2.9.13-cp314-cp314-win_amd64.whl.metadata'
```

É o **mesmo defeito de `0o700`** já documentado em `tests/conftest.py` §1 e no adendo da
feature 007, e já medido nesta sessão em `investigation.md` (`M-06`): o `pip` cria o
diretório de trabalho por `tempfile.mkdtemp`, e um diretório criado com `0o700` nesta
máquina não é listável, gravável nem removível. Apontar `TEMP`/`TMP` para dentro do
workspace **não resolve** — foi tentado e falhou igual.

Consequências, e elas são de desenho, não de execução:

| Onde o `pip install` roda | Funciona? |
|---|---|
| No **`.venv` do host** (pré-requisito do `onboarding.md` §2, e o que o `T014` precisa) | ❌ **não** — é onde o defeito morde |
| Dentro do **contêiner** (`RUN pip install` no `Dockerfile` do `T003`) | ✅ **sim** — o `build` roda no sistema de arquivos Linux do contêiner, sem a ACL do Windows |

**CORREÇÃO DE ATRIBUIÇÃO, feita na reexecução do `T001`.** A versão anterior deste documento
afirmava que "o `T007` fica bloqueado na metade local". Isso estava **errado**: o `T007` como
escrito no `actions.md` manda apenas **acrescentar o pin ao `requirements.txt`** — ele **não**
tem passo de instalação. Quem depende do `pip install` é o `T014` (o teste do adaptador roda
no `.venv` do host contra o banco do compose) e o pré-requisito §2 do `onboarding.md`. O
`T007` foi executado e concluído sem obstáculo.

## 6. O que **não** foi feito

- Nenhum dos quatro arquivos recusados foi criado, nem por caminho alternativo.
- Nenhum arquivo do legado foi tocado nesta rodada. `git status` deve estar limpo quanto a
  `src/`, `tests/`, `requirements.txt`, `pytest.ini`, `.gitignore` e `_reversa_sdd/`.
- `actions.md` mantém `T002` a `T026` em `[ ]`. Apenas o `T001` foi marcado `[X]`.
- Nenhuma linha de código de produção foi escrita.

Tudo isso vale para a **primeira** execução. A reexecução da seção seguinte muda o quadro.

## 7. Reexecução: veredito **ATENDIDO**

Executada na mesma rodada, depois de o usuário editar o arquivo de configuração:

```json
"allowedPaths": ["analisador-genealogico/**", "tests/**", "README.md", "pyrefly.toml",
                 "src/**", ".vscode/**", "requirements.txt", ".markdownlint-cli2.jsonc",
                "docker/**", "docker-compose.yml", "init.sql", ".dockerignore"]
```

**Os quatro caminhos agora casam**, e o Bloco 0 pôde começar. Nenhum contorno foi usado, e a
liberação foi **ato do usuário**, exatamente como a §4 exigia — que era o ponto do `T001`.

Resultado da execução que se seguiu, e ela para num bloqueio **novo**:

| Ação | Veredito |
|---|---|
| `T001` | ✅ **ATENDIDO** |
| `T002`, `T003`, `T004`, `T005`, `T006`, `T007` | ✅ **concluídas** — seis arquivos escritos, nenhum deles tocando o legado em `src/` ou `tests/` |
| `T008` | 🛑 **FALHOU** — o motor do Docker não está em execução, e a falha é dele, não da feature: `unable to get image 'genealogia-app': permission denied while trying to connect to the docker API at npipe:////./pipe/dockerDesktopLinuxEngine` |

A verificação de `T006` que **não** precisa do motor passou: `docker compose config --quiet`
devolveu **exit 0**, com dois serviços (`db`, `app`), um volume nomeado (`dados_do_banco`) e as
portas publicadas em `127.0.0.1` (`5080` e `5432`).

E o guarda de credencial do `RF-11` foi **verificado em execução**, não só por leitura: sem
`.env`, o `docker compose up` para com

```
error while interpolating services.db.environment.POSTGRES_USER:
required variable POSTGRES_USER is missing a value: defina POSTGRES_USER no .env
```

que é o `${VAR:?}` funcionando — e é a prova de que não existe credencial com valor padrão em
arquivo versionado.

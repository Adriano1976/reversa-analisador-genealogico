# ADR-28 — Docker em dois serviços, com `.dockerignore` como lista de permissão

- **Status:** Aceito e **vigente**
- **Data da decisão:** 2026-10-08
- **Commit(s):** `80964c4` ("empacota a aplicacao com postgres em dois servicos"), dentro do ciclo `008-persistencia-postgres-docker`
- **Confiança:** 🟢 CONFIRMADO

## Contexto

O `ADR-27` introduziu a necessidade de um PostgreSQL. Isso trouxe duas perguntas de execução que o projeto não tinha: **como o operador sobe as duas peças juntas**, e **o que entra no contexto de build**.

A segunda pergunta tem um histórico ruim no repositório. A primeira tentativa de `.dockerignore` foi uma **lista de negação** — negar o que se conhece —, e ela **falhou de forma medida**: a raiz tem 22 diretórios que recusam `os.scandir` (sete em `.pytest-tmp/`, dois em `_probe_acl/`, um em `_probe_acl2/` e doze sob `_reversa_*/`), e a lista cobria apenas 12 deles. `docker build` percorre o contexto inteiro e **aborta no primeiro diretório ilegível**.

## Decisão

1. **Dois serviços** em `docker-compose.yml` — `db` e `app` —, com as duas portas publicadas **em `127.0.0.1`** (`127.0.0.1:5080:5000` e `127.0.0.1:5432:5432`).
2. **Variáveis obrigatórias com `${VAR:?}`**, para que uma credencial ausente **aborte a subida** em vez de subir com padrão inseguro.
3. **`.dockerignore` como lista de PERMISSÃO:** `*` primeiro, depois `!requirements.txt`, `!src/` e `!src/**`. O que não está nomeado **não entra** — nem o resíduo de hoje, nem o de amanhã.
4. **Reexclusões depois do `!src/**`**, porque a última regra que casa vence: `src/uploads/` (dado real do operador), `**/__pycache__/` e `**/*.pyc`.
5. **`init.sql` idempotente por requisito**, montado em `/docker-entrypoint-initdb.d/`.

## Evidência

- `.dockerignore` abre com o comentário que registra a falha da lista de negação e os 22 diretórios medidos.
- `docker-compose.yml` usa `${VAR:?}` nas credenciais e publica as duas portas em `127.0.0.1`.
- `docker/Dockerfile` parte de `python:3.14-slim`, a mesma linha de versão do interpretador oficial.
- `init.sql` usa `CREATE TABLE IF NOT EXISTS` em tudo e **não tem nenhum `DROP`** — o comentário declara que a idempotência é `RF-12`, requisito, e não consequência: o entrypoint só roda os scripts quando o diretório de dados está vazio, o que cobre a primeira subida mas **não** uma reexecução manual.
- **A arte de runtime obedece a esta decisão.** `src/assets/` é o único caminho de arte que entra na imagem, e o motivo está declarado no `app.py` e em `tests/icone_de_atalho.py`: arte em `docs/` responderia 200 na máquina de desenvolvimento e **404 dentro do container** — falha silenciosa no ambiente do operador. Ver `ADR-29`.

## Justificativa

**Uma lista de permissão envelhece melhor que uma de negação.** A negação precisa ser atualizada a cada diretório novo que apareça; a permissão protege o que não foi previsto. O custo é ter de nomear explicitamente o que entra — e, no caso deste repositório, o que entra é pouco: um arquivo de dependências e uma pasta.

## Consequências

- 🟢 **`src/uploads/` fora da imagem é a consequência mais importante**, e ela é de privacidade: a pasta carrega 13 arquivos do operador, incluindo um GEDCOM de 5,3 MB. Enviá-los ao daemon do Docker seria a mesma classe de exposição que o Princípio I proíbe.
- 🟢 **A decisão de onde mora a arte passou a ser derivada daqui**, e não estética: `ADR-29`.
- 🔴 **Limite declarado no próprio `init.sql`:** `CREATE TABLE IF NOT EXISTS` **não altera** tabela existente. Uma mudança de esquema depois da primeira subida exige `docker compose down -v` (perdendo o histórico) ou `ALTER TABLE` manual. **Não há tabela de versão de esquema nem runner de migração** — sem migração para aplicar, ela seria decoração.
- 🟡 **As credenciais vivem em `.env`**, em claro, no host (`P-06`). O arquivo está no `.gitignore` e **não** entra na imagem, mas é lido pelo `docker-compose`.
- 🟢 **Cinco tabelas do alvo NÃO foram criadas** — `app_user`, `consent_record`, `data_retention_policy`, `access_audit` e `uploaded_file` —, e a ausência de `data_retention_policy` é a que mais pesa hoje, dado o `L-29`.

# T009 — Idempotência do `init.sql`

> Feature: `008-persistencia-postgres-docker` · Data: `2026-10-08` · Ação: `T009` (`RF-12`, `D-07`)

## O que foi medido

```powershell
$q = "SELECT count(*) FROM information_schema.tables WHERE table_schema='public';"
docker compose exec -T db psql -U genealogia -d genealogia -tAc $q
docker compose exec -T db psql -U genealogia -d genealogia -f /docker-entrypoint-initdb.d/init.sql
docker compose exec -T db psql -U genealogia -d genealogia -tAc $q
```

| Medição | Resultado |
|---|---|
| Tabelas **antes** da reexecução | **6** |
| Saída da reexecução | apenas `NOTICE: relation "<nome>" already exists, skipping` — nenhum erro |
| Tabelas **depois** da reexecução | **6** |

A saída completa da reexecução termina assim:

```
psql:/docker-entrypoint-initdb.d/init.sql:146: NOTICE:  relation "ix_match_kit_match" already exists, skipping
psql:/docker-entrypoint-initdb.d/init.sql:160: NOTICE:  relation "skipped_match" already exists, skipping
psql:/docker-entrypoint-initdb.d/init.sql:162: NOTICE:  relation "ix_skipped_match_analysis" already exists, skipping
```

## O que este passo prova, e o que ele economiza

- **`RF-12` está atendido**, e não por leitura: o arquivo foi executado **duas vezes** contra o
  mesmo banco, a contagem ficou em **6**, e o `NOTICE ... skipping` é o PostgreSQL confirmando
  que o `IF NOT EXISTS` pegou. **Nenhum `DROP` foi executado** — se houvesse um, a segunda
  contagem seria 6 mas o histórico estaria perdido, e o teste que pega isso é o `T020`, que
  insere uma análise antes de reexecutar.
- **O `A001` da auditoria está fechado por medição.** Ele dizia que a idempotência não tinha
  ação correspondente; as descrições do `T004`/`T005` passaram a exigi-la, e este passo é a
  prova de que a exigência chegou ao arquivo.
- **A montagem do `init.sql` no entrypoint funciona** — era o outro ponto do `A001`. O caminho
  `/docker-entrypoint-initdb.d/init.sql` existe dentro do contêiner e é legível, o que depende
  do bind mount declarado no `T006`.

## O que este passo **não** prova

Que o `init.sql` cria o esquema correto. O entrypoint só o executa com o diretório de dados
**vazio**, e a contagem de 6 na primeira medição é o efeito disso — mas ela não diz que as seis
tabelas têm as colunas certas. Quem prova isso é o `T014` (a ida e volta dos valores) e o
`T020` (a gravação ponta a ponta).

# T003 - servico app recriado, /app/src/uploads de volta

# Gerado em: 2026-10-09
# Comando: docker compose up -d

## Saida do comando

    Container genealogia-db-1 Running
    Container genealogia-app-1 Recreate
    Container genealogia-app-1 Recreated
    Container genealogia-app-1 Starting
    Container genealogia-app-1 Started

## Estado depois (docker compose ps)

| Servico | CREATED | STATUS | PORTS |
|---|---|---|---|
| app | 13 seconds ago | Up 1 second | 127.0.0.1:5080->5000/tcp |
| db | 2 hours ago | Up 2 hours (healthy) | 127.0.0.1:5432->5432/tcp |

O banco **nao** foi recriado: mesmo `CREATED`, mesmo volume nomeado, `healthy`. Nenhum `down -v` foi
executado. A saida do proprio compose confirma: `genealogia-db-1 Running`, sem `Recreate`.

## /app/src/uploads dentro do container

    $ docker compose exec -T app sh -c 'ls -A /app/src/uploads | wc -l'
    36

Amostra das tres primeiras entradas, identicas as da pasta do host:

    080e7943572d2652__080e7943572d2652__Arvore_Unificada_Oficial_V1_2.ged
    080e7943572d2652__Arvore_Unificada_Oficial_V1_2.ged
    0e85a4f3052e19e3__Genealogia_Mineira.csv

Antes desta acao, o mesmo comando respondia `ls: cannot access '/app/src/uploads': No such file or
directory` — o *bind mount* apontava para `D:/dados-genealogicos/uploads`, que deixou de existir.

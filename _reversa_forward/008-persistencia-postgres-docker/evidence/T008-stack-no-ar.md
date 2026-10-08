# T008 — O stack no ar

> Feature: `008-persistencia-postgres-docker` · Data: `2026-10-08` · Ação: `T008` (`RF-01`)

## Comandos e resultados

| Passo | Comando | Resultado |
|---|---|---|
| Build | `docker compose build --progress plain` | **exit 0** — imagem `genealogia-app:latest` construída. Log bruto em `evidence/_bloco0-build.log` |
| Subida | `docker compose up -d` | **exit 0** |
| Estado | `docker compose ps` | **dois** serviços no ar (abaixo) |
| Prontidão do banco | `docker compose exec -T db pg_isready` | `accepting connections` após **3 s** |
| Aplicação | `curl.exe -s -o NUL -w "%{http_code}" http://127.0.0.1:5080/` | **`200`** após **4 s** |

```
NAME               IMAGE                COMMAND                  SERVICE   STATUS                   PORTS
genealogia-app-1   genealogia-app       "python src/app.py"      app       Up                       127.0.0.1:5080->5000/tcp
genealogia-db-1    postgres:16-alpine   "docker-entrypoint.s…"   db        Up (healthy)             127.0.0.1:5432->5432/tcp
```

## O que este passo prova

- **`RF-01`**: os dois serviços sobem com **um** comando, e as portas são publicadas **só em
  `127.0.0.1`** — nem a aplicação nem o banco ficam expostos fora do host.
- **`D-10` funcionou como desenhado**: `ANALISADOR_HOST=0.0.0.0` **dentro** do contêiner, com a
  publicação em `127.0.0.1` no host. A aplicação responde em 4 s.
- **`D-09` funcionou como desenhado**: o `db` aparece `(healthy)` e o `app` subiu **sem esperar**
  por isso — a ordenação do `depends_on` curto aconteceu, e o portão de saúde não existe.
- **A hipótese em aberto do `T010` foi aposentada:** o `RUN pip install --no-cache-dir -r
  requirements.txt` instalou os **nove** pacotes no `python:3.14-slim` **sem compilar nada**.
  Existiam wheels `manylinux` para `cp314` de `pandas 3.0.6` e `networkx 3.7`, que era o que o
  `M-04` não tinha medido (ele mediu Windows).

## Observação de ambiente

O motor do Docker não estava em execução, e **o CLI precisa de acesso a named pipe**, que o
modo confinado do harness bloqueia. A execução exigiu autorização explícita do usuário para
esta rodada. Fica registrado porque é a **terceira** parada por ambiente desta feature, e
nenhuma das três é defeito do produto.

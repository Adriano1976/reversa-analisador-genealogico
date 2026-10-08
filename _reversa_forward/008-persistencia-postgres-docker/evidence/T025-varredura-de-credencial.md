# T025 — Varredura de credencial

> Feature: `008-persistencia-postgres-docker` · Data: `2026-10-08` · Ação: `T025` (`RF-11`)

## As nove verificações

| # | Verificação | Resultado |
|---|---|---|
| 1 | O **valor** da senha aparece em algum arquivo do projeto? | **2 ocorrências — as duas no `.env`** (linhas 14 e 16: `POSTGRES_PASSWORD=` e dentro de `DATABASE_URL=`) |
| 2 | Quem cita os **nomes** das variáveis? | `src/app.py`, `src/application/dna_analysis.py`, `docker-compose.yml` e os quatro testes novos |
| 3 | Existe `.env.example`? | **não** |
| 4 | O `.env` está ignorado? | **sim** — `git check-ignore -v` responde `.gitignore:6:.env` |
| 5 | O template cita credencial? | **0 ocorrências** |
| 6 | O `docker compose config` imprime o valor? | **sim** — ver §2 |
| 7 | As **camadas** da imagem citam credencial? | **0 camadas** |
| 8 | O **ambiente dentro** da imagem tem credencial? | **0 variáveis** com `postgres` |
| 9 | Existe arquivo `.env` dentro da imagem? | **nenhum** |

E o que a imagem contém em `/app` é exatamente o que o `COPY` estreito do `Dockerfile` copia:

```
/app:  requirements.txt  src
/app/src:  app.py  application  core  parsers  ports  reporting  templates  utils
/app/src/uploads:  AUSENTE
```

**`/app/src/uploads` ausente é o Princípio I confirmado de novo**, agora por dentro da imagem.

## Onde a senha está, e por que está certo

As duas únicas ocorrências do valor são **no `.env`** — o arquivo que existe para isso, que o
`.gitignore` exclui (linha 6) e que **não é versionado**. Nos lugares onde a variável é
**citada**, o que aparece é o **nome**, nunca o valor:

- `docker-compose.yml`: `${POSTGRES_PASSWORD:?defina POSTGRES_PASSWORD no .env}` — referência
  com guarda, sem valor padrão, que é o `RF-11` funcionando;
- `src/app.py`: `os.environ.get("DATABASE_URL")` — leitura;
- `src/application/dna_analysis.py`: menção em prosa, no docstring;
- os quatro testes: menções em docstring e nas fixtures.

## §2 O `docker compose config` imprime o valor — e isso **não** é vazamento

```
docker compose config  ->  ... DATABASE_URL: postgresql://genealogia:<senha>@db:5432/genealogia
```

**É comportamento do Compose, e não um defeito desta feature:** o `config` resolve as
variáveis do `.env` e mostra o resultado, por definição. Um `grep` na saída encontra o valor.

⚠️ **O que isso significa na prática**, e fica registrado: **quem rodar `docker compose config`
num terminal expõe a senha na tela** — e, se redirecionar para um arquivo, no arquivo. Não há
como o Compose mascarar isso; a mitigação é não redirecionar a saída para lugar nenhum
versionado. Vale para o `.env` inteiro e para qualquer projeto com Compose, não só este.

## O que esta varredura **não** prova

- **Que a senha nunca apareceu em lugar nenhum fora do projeto.** O que se mediu é o estado
  atual dos arquivos; um valor que já tenha passado por um log ou por um terminal não é
  detectável por varredura.
- **Que a imagem é imune a credencial futura.** Ela é hoje porque a lista de **permissão** do
  `.dockerignore` só deixa entrar `requirements.txt` e `src/**`, e porque o `.env` fica na raiz.
  Quem acrescentar um `COPY` mais largo quebra isso sem que esta varredura seja reexecutada.

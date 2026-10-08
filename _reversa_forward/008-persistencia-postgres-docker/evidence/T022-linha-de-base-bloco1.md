# T022 — Linha de base vigente do Bloco 1

> Feature: `008-persistencia-postgres-docker` · Data: `2026-10-08` · Ação: `T022`
> (`RF-13`, `D-14`, `D-17`)

## Os dois números, com o comando ao lado

```powershell
# A) o estado SUPORTADO da suite: sem a variavel
.venv\Scripts\python.exe -m pytest -q
-> 282 passed, 8 skipped in 43.54s

# B) com DATABASE_URL definida e apontando para o banco que esta no ar
.venv\Scripts\python.exe -m pytest -q
-> 2 failed, 280 passed, 8 skipped in 41.59s
```

| Estado | Resultado |
|---|---|
| **Sem** `DATABASE_URL` — o estado suportado | **`282 passed, 8 skipped`** |
| **Com** `DATABASE_URL`, banco no ar | **`2 failed, 280 passed, 8 skipped`** |
| Linha de base herdada (antes da feature) | `261 passed` |
| Linha de base do Bloco 0 | `261 passed` + `PARIDADE 100 %` |

**A aritmética fecha:** `261` + **21** testes desta feature = `282`. Os 8 pulos são o `T014` e
as seis parametrizações dele.

## O `2 failed` do estado B **é de propósito**, e os dois têm nome

```
FAILED tests/test_persistencia_desabilitada.py::test_guarda_contra_teste_vacuamente_verde
FAILED tests/test_persistencia_desabilitada.py::test_a_analise_sai_igual_e_sem_aviso
```

1. **`test_guarda_contra_teste_vacuamente_verde`** afirma, de caso pensado, que a variável
   **não** está no ambiente. O docstring diz por quê: *"Se a variável existisse, nada abaixo
   mediria o estado desabilitado"*. Ela falha exatamente quando o arquivo deixaria de medir o
   que promete.
2. **`test_a_analise_sai_igual_e_sem_aviso`** usa o cliente que `cliente_de_upload` carregou
   **com** a variável definida. Com ela, `_REGISTRO` deixa de ser nulo, a análise tenta
   gravar, e no `.venv/` do host a tentativa falha por ausência do driver — o aviso aparece, e
   a asserção de que ele **não** aparece cai.

⚠️ **O custo dessa escolha, declarado.** Um desenvolvedor que tenha `DATABASE_URL` exportado no
ambiente vê **duas falhas** que parecem regressão e não são. A alternativa seria o
`cliente_sem_url` recarregar o app depois de limpar a variável, e aí a suíte passaria nos dois
estados — mas passaria **medindo o estado forçado pela fixture**, e não o estado do ambiente.
O projeto escolheu **arrestar em vez de silenciar**: o contrato da `D-17` é que a suíte roda
**sem** a variável, e o guarda torna esse contrato exigido em vez de suposto.

## O que o `T014` faz nos dois estados: nada — ele é pulado nos dois

O `skipif` exige `DATABASE_URL` **e** o driver `psycopg2` no interpretador. O `.venv/` do host
não tem o driver e não consegue ter (`OBS-15`, o defeito de `0o700` no `pip`). Então o segundo
número da suíte **não** executa o `T014` — e é por isso que a substância dele foi verificada
dentro do contêiner, no `T020`, com **24 verificações e 0 falhas**.

⚠️ **Um teste pulado não é um teste que passou**, e é por isso que os dois números estão nesta
tabela lado a lado em vez de resumidos num só.

## Sobre o tempo

| Medição | Duração |
|---|---|
| Sem `DATABASE_URL` | 43,5 s (58,8 s na primeira execução desta rodada) |
| Com `DATABASE_URL` | 41,6 s |
| Linha de base, antes do plano | 27,1 s |
| Bloco 0, com os contêineres recém-subidos | 62,2 s |

A variação entre 34 s e 62 s **não acompanha nenhuma mudança de código**: o conjunto de testes
é o mesmo, e a explicação provável é concorrência de CPU e disco com os contêineres e com os
builds. Fica como **observação** (`OBS-14`), e não como achado: ela não se reproduz de forma
consistente, e nenhuma medição a liga à feature.

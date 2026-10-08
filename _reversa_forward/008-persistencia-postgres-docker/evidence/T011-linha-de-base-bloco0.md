# T011 — Linha de base do Bloco 0 (o portão)

> Feature: `008-persistencia-postgres-docker` · Data: `2026-10-08` · Ação: `T011` (`RF-13`, `D-14`)

## As duas medições, com o comando ao lado

```powershell
Test-Path env:DATABASE_URL        # → False
.venv\Scripts\python.exe -m pytest -q
.venv\Scripts\python.exe _reversa_sdd\parity\harness.py
```

| Medição | Linha de base (2026-10-08, antes do plano) | **Bloco 0** | Veredito |
|---|---|---|---|
| Suíte completa, **sem** `DATABASE_URL` | `261 passed` | **`261 passed`** — 0 falhas, 0 erros | ✅ **inalterada** |
| Paridade diferencial | `PARIDADE 100 %`, exit 0 | **`PARIDADE 100 %`**, exit 0 | ✅ **inalterada** |

**O portão do Bloco 0 está verde.** Nenhuma linha de Python de produção foi escrita nesta
metade da feature, e as duas medições confirmam isso por comportamento, não por inspeção.

## Observação medida, e ela **não** é atribuída à feature

O tempo da suíte passou de **27,14 s** (linha de base) para **62,23 s** agora. O conjunto é o
mesmo — `261 passed` nos dois, com `DATABASE_URL` ausente nos dois —, e **nenhuma linha de
`src/` ou `tests/` foi alterada**. A explicação mais provável é concorrência de recursos: os
dois contêineres estão no ar durante a segunda medição, e o banco e a aplicação consomem CPU e
disco do host.

**Não é atribuído à feature**, e fica registrado como observação para o `T022`, que vai medir a
suíte outra vez com e sem o stack. Se o `T022` reproduzir a diferença com os contêineres
parados, aí deixa de ser observação e vira achado.

## O que este passo prova, e por que ele é o portão

Ele é a única medição que pode dizer **"a infraestrutura não tocou o produto"**. O Bloco 0
escreveu cinco arquivos — `.dockerignore`, `docker/Dockerfile`, `init.sql`,
`docker-compose.yml` e uma linha do `requirements.txt` — e subiu dois contêineres. Se a suíte ou
a paridade tivessem se movido aqui, a causa seria de **infraestrutura**, com ponto de atribuição
nomeado: um `pip install` que trocou versão, ou um arquivo de produção tocado por engano.

Nenhuma das duas se moveu. **O Bloco 1 pode começar**, e o `T012` deixa de ter dependência
aberta.

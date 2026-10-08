# T010 — pré-medição parcial do contexto de build, sem o motor do Docker

> Feature: `008-persistencia-postgres-docker`
> Data: `2026-10-08`
> **Este documento NÃO substitui o `T010`.** O `T010` continua `[ ]` e continua exigindo o
> motor do Docker em execução. O que está aqui é a metade da medição que **não** depende dele,
> registrada para que a próxima rodada já saiba o que esperar.

## 1. Por que esta medição foi antecipada

O `T008` falhou porque o motor do Docker não está em execução, e isso bloqueia `T009`, `T010` e
o portão `T011`. Das quatro perguntas que o `T010` responde, **três** podem ser respondidas sem
o motor, e as três são as que decidem se o `docker build` vai falhar:

1. `src/uploads/` — com o GEDCOM real de 5,3 MB — entra no contexto? (**Princípio I**)
2. Existe diretório ilegível dentro do contexto? (é o que faz o `build` abortar)
3. Qual é o tamanho do contexto?

## 2. O que foi medido

Varredura do sistema de arquivos, aplicando a regra do `.dockerignore` do `T002`: `*` na
primeira linha, `!requirements.txt`, `!src/`, `!src/**`, e `src/uploads/` com
`**/__pycache__/` e `**/*.pyc` reexcluídos no fim. O contexto é, portanto,
`requirements.txt` + tudo sob `src/`, menos as reexclusões.

| Medição | Valor |
|---|---|
| `src/` — pastas / arquivos | 16 / 100 |
| `src/` — tamanho bruto | **23,1 MB** |
| `src/uploads/` — arquivos | 32 |
| `src/uploads/` — tamanho | **22,6 MB** — e é **REEXCLUÍDO** do contexto |
| **Contexto efetivo** | **≈ 0,5 MB** + `requirements.txt` (1,4 KB) |
| `requirements.txt` | 1,4 KB |

E o achado que mais importa:

**O único diretório ilegível sob `src/` é `src\uploads\_pytest`** — e ele está **dentro** de
`src/uploads/`, que a lista de permissão reexclui. Ou seja: o diretório que derrubaria o
`docker build` sai do contexto pela **mesma regra** que protege o dado real. Não há dois
problemas para resolver; há um.

> Confere com o que a extração já registrava: o Achado C do `actions.md` da feature 007
> menciona `src/uploads/_pytest` como o diretório preso que aquela rodada criou tentando
> `--basetemp`. Ele continua lá.

## 3. O que esta medição prova, e o que ela **não** prova

**Prova, e é robusto a detalhe de regra:** `src/uploads/` está fora do contexto. A conclusão
segue de **contenção de caminho** — o diretório ilegível mora dentro do diretório reexcluído —
e não depende de a minha leitura das regras do `.dockerignore` estar exata em todos os casos
de borda.

**Não prova:** que o Docker concorda com a minha emulação. O `.dockerignore` é interpretado
pelo próprio Docker, e é ele quem decide. Duas coisas só o `T010` de verdade fecha:

- o número que o `docker build` reporta em `transferring context`;
- a prova por `docker run` de que `src/uploads/` **não existe** na imagem.

**Também não prova** que a imagem constrói. O `RUN pip install --no-cache-dir -r
requirements.txt` do `Dockerfile` baixa e instala nove pacotes, entre eles `pandas 3.0.6` e
`networkx 3.7` para `cp314`. Existem wheels `cp314` para Windows, que foi o que o `M-04` mediu;
**para Linux não foi medido**, e é o que o build vai usar. Se algum deles não tiver wheel
`manylinux` para `cp314`, o build tenta compilar e pode falhar — e isso é uma hipótese
**aberta**, não um problema conhecido.

## 4. O que fazer quando o motor subir

Rodar o `T010` como escrito, e comparar com os números da §2. Divergência no tamanho do
contexto significa que a minha emulação da lista de permissão está errada e que o `.dockerignore`
precisa de ajuste — o que é informação, não defeito.

# T010 — Contexto de build e a imagem

> Feature: `008-persistencia-postgres-docker` · Data: `2026-10-08` · Ação: `T010` (`D-11`, `D-18`, Princípio I)

## As duas metades do `T010`

### 1. Tamanho do contexto

Do log bruto do build (`evidence/_bloco0-build.log`):

```
#5 transferring context: 1.32kB 0.0s done
#6 [internal] load build context
#6 transferring context: 250.70kB 0.6s done
```

**Contexto efetivo: 250,70 kB.** Contra os 23,1 MB de `src/` bruto e os **22,6 MB** de
`src/uploads/` — ou seja, o dado real do operador **não** foi para o daemon.

A pré-medição offline (em `T010-pre-medicao-parcial-sem-motor.md`) havia estimado ≈ 0,5 MB. O
valor real é **250,7 kB**: mesma ordem de grandeza, e a diferença é a emulação das regras do
`.dockerignore` contra a implementação real do Docker. Registrado porque era exatamente o que a
pré-medição disse que só o `T010` poderia fechar.

### 2. O dado real está na imagem?

```powershell
docker run --rm genealogia-app sh -c "ls /app/src/uploads 2>/dev/null && echo PRESENTE || echo AUSENTE"
→ AUSENTE
```

**`src/uploads/` não existe na imagem.** O GEDCOM real de 5,3 MB do operador — que no host
ocupa 22,6 MB entre 32 arquivos — **não** foi enviado ao daemon nem copiado para nenhuma camada.

## O que este passo prova

- **O Princípio I está protegido por medição**, não por argumento. Era o risco de maior
  gravidade do §9 do `roadmap.md`, e ele está fechado.
- **`D-18` funciona.** A lista de **permissão** do `.dockerignore` exclui tudo o que não está
  nomeado, e é por isso que o contexto caiu de 23,1 MB para 250,7 kB.
- **`D-11` funciona.** O `.dockerignore` **na raiz** foi lido — se estivesse em `docker/`, o
  Docker o ignoraria e o contexto carregaria `src/uploads/`.

## O que este passo **não** prova

- **Que nenhum diretório ilegível entrou no contexto.** O alvo era `src/uploads/_pytest`, o
  único ilegível sob `src/`, e ele mora dentro do diretório reexcluído. O build ter **passado**
  é a evidência indireta de que nenhum diretório ilegível foi percorrido: um `docker build`
  aborta ao encontrá-lo. A evidência direta seria a falha, e ela não aconteceu.
- **Que a imagem é mínima.** O `COPY` é estreito e o contexto é de 250 kB, mas não se mediu o
  tamanho da imagem nem o que ela contém além de `/app/src` e das dependências.

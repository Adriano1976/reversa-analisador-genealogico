# T008 — A arte entra na imagem, e não só no host

> Feature: `009-rota-do-apple-touch-icon` · Ação: `T008` · Data: `2026-10-08`
> Comando: `docker compose up -d --build app` + `docker compose exec -T app ls -l /app/src/assets`
> Registro bruto: `evidence/_t008_t009_conteiner.txt`

## O que esta ação existe para pegar

A falha silenciosa do `RF-04`: a rota responde `200` na máquina de desenvolvimento, servida
de um arquivo **fora** do contexto de build, e responde `404` na imagem publicada. O
`.dockerignore` deste projeto é **lista de permissão** (`*`, depois `!requirements.txt`,
`!src/`, `!src/**`), então qualquer arte fora de `src/` simplesmente **não existe** dentro
do contêiner — e nada avisa.

## Medição

Reconstrução:

```
 Container genealogia-app-1 Recreate
 Container genealogia-app-1 Recreated
 Container genealogia-app-1 Starting
 Container genealogia-app-1 Started
```

O arquivo, **dentro** do contêiner:

```
total 20
-rwxr-xr-x 1 root root 16504 Oct  8 18:44 apple-touch-icon.png
```

| Verificação | Esperado | Medido |
|---|---|---|
| O arquivo existe em `/app/src/assets/` | sim | ✅ sim |
| Tamanho | 16.504 bytes | ✅ **16.504** |
| `src/static` continua ausente na imagem | ausente | ✅ `cannot access '/app/src/static': No such file or directory` |

> O erro de `ls` no stderr é o **resultado desejado** nesta linha: ele é a prova de que a
> pasta proibida pelo `W004` não existe dentro da imagem. Não é falha da ação.

## Por que o tamanho é a mesma âncora da `T003`

16.504 bytes é o número da receita. Se a arte tivesse sido copiada em outra resolução,
comprimida de outro jeito ou servida transparente, este número seria outro — e é por isso
que ele serve como conferência barata em três lugares independentes: a receita, a sonda
`T003` e o arquivo dentro da imagem.

## Veredito

**APROVADO.** A arte existe na imagem, com o tamanho da receita, e a pasta proibida
continua ausente. O `RF-04` está satisfeito no ambiente que o operador usa, e não apenas
no host.

## Fontes

- `evidence/_t008_t009_conteiner.txt` (saída bruta)
- `.dockerignore` na raiz (a lista de permissão)
- `_reversa_forward/009-rota-do-apple-touch-icon/roadmap.md` (`D-03`)

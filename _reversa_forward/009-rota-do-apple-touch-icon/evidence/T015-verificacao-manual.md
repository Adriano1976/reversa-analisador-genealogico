# T015 — Verificação manual pelo `onboarding.md`

> Feature: `009-rota-do-apple-touch-icon` · Ação: `T015` · Data: `2026-10-08`
> Registro bruto: `evidence/_t015_manual.txt`

## 1. O que foi executado

Os passos do `onboarding.md` que o **host** e o **contêiner** provam. O passo 8 — a prova
no celular — **não** foi executado, e a §5 deste arquivo declara o motivo.

### Passo 4 — o conteúdo servido

```
HTTP/1.1 200 OK
Cache-Control: no-cache
Content-Length: 16504
Content-Type: image/png
Etag: "1791485083.0-16504-4142140804"
Last-Modified: Thu, 08 Oct 2026 18:44:43 GMT
bytes no disco : 16504
```

| Campo | Esperado | Medido |
|---|---|---|
| Status | `200` | ✅ `200` |
| Tipo | `image/png` | ✅ `image/png` |
| Tamanho | 16.504 | ✅ **16.504** |
| Validade de cache | **nenhuma** | ✅ **`no-cache`** |
| Marca de versão | presente | ✅ `ETag` |

### Passo 4b — sonda de conteúdo sobre o que veio pela rede

```
dimensoes IHDR : (180, 180)
tipo de cor    : 2 (2 = sem canal alfa)
cantos         : [(255, 255, 255), (255, 255, 255), (255, 255, 255), (255, 255, 255)]
```

Os quatro requisitos de imagem conferidos **sobre o corpo que a rede entregou**, e não
sobre o arquivo em disco: dimensão (`RF-02`), ausência de canal alfa (`RF-03`), fundo
branco nos cantos (`RN-04`).

### Passo 5 — revalidação

```
etag usado     : "1791485083.0-16504-4142140804"
status         : 304
bytes no corpo : 0
```

O `304` **sem corpo** é o que a `D-05` decidiu: revalidação barata pelo `ETag`, sem
validade declarada que congelaria o cliente.

### Passo 5b — a tela não mudou

```
GET / bytes    : 23906  (linha de base: 23906)
```

O número é **exatamente** o da linha de base medida antes de a rota existir. O `RF-05` está
provado no ambiente real, e não só no cliente de teste.

### Passo 7 — a pasta proibida

```
src/static existe: False
```

### Passos 3 e 6 — contêiner

Executados em `T008` e `T009`, com registro próprio: a arte está dentro da imagem
(16.504 bytes) e a rota responde `200` **de dentro**, com `cache-control: no-cache`.

## 2. Uma medição que falhou, e que **não** virou resultado

A primeira tentativa usou `Invoke-WebRequest` e falhou inteira: o PowerShell está em modo
`NonInteractive` e o cmdlet tenta abrir um prompt que não existe. O bloco de erro do script
imprimiu `status= bytes=0 (304 nao traz corpo)` — que **parece** a resposta certa e não é:
era o `catch` de uma exceção, com `$r` nulo.

A medição foi refeita com `curl.exe`, e é a da §1. **Registro isto porque o número errado
tinha a forma do número certo**, e um leitor futuro que encontrasse aquele fragmento no
histórico poderia tomá-lo por medição.

## 3. Resultado consolidado

| Passo do onboarding | Resultado |
|---|---|
| 2 — linha de base (`404` antes) | ✅ registrada em `T010` |
| 3 — aplicar e subir | ✅ `T008` |
| 4 — conteúdo servido | ✅ `200`, `image/png`, 16.504 bytes, `no-cache` |
| 4b — dimensão, opacidade, cantos | ✅ 180×180, tipo de cor 2, quatro cantos brancos |
| 5 — revalidação | ✅ `304`, corpo vazio |
| 5b — tela imutável | ✅ 23.906 bytes, igual à linha de base |
| 6 — dentro do contêiner | ✅ `T008`, `T009` |
| 7 — `src/static` ausente | ✅ ausente no host e na imagem |
| **8 — aparelho real** | ❌ **NÃO EXECUTADO** |
| 10 — encerrar e limpar | ✅ sem resíduo novo; `icone-servido.png` removido |

## 4. A ação está concluída, e a feature não está

A `T015` cobre o que era executável por comando. Ela **não** fecha o critério de pronto
inteiro: o item da prova em aparelho real continua aberto, e é do operador.

## 5. A prova que falta, e por que ela não foi feita

O `onboarding.md` §8 depende de um celular na mesma rede. Além disso, ele exige alterar a
publicação de porta do `docker-compose.yml` de `127.0.0.1` para `0.0.0.0` **na máquina do
operador** — e enquanto estiver assim, qualquer pessoa da rede alcança a aplicação, que
continua **sem autenticação** e single-tenant (dívida #4 aberta, `BUG-20260929-BJJH`).

Ninguém nesta sessão executou esse passo, e **nenhum comando desta feature o substitui**.
Ele fica registrado como a lacuna `OBS-30` do `regression-watch.md` e como
`investigation.md` §6.1.

## 6. Estado do workspace durante a execução

Duas interferências de **outra sessão**, registradas porque afetam a leitura do histórico:

1. **`src/app.py` foi tocado entre a leitura e a edição** desta sessão. O conteúdo estava
   idêntico (`git status` limpo, mesmo número de linhas, mesmo import) — o commit da outra
   sessão reescreveu o arquivo e restaurou o `mtime`. A edição foi refeita após reconferir.
2. **Artefatos desta feature foram commitados em curso** por outra sessão
   (`ca8e477`, "abre o ciclo 009"), incluindo a versão **inicial** do `requirements.md`, e a
   `.markdownlint-cli2.jsonc` foi alterada para ignorar `_reversa_forward/**` (`OBS-35`).

Nada disso foi causado por esta execução, e nada foi revertido.

## Fontes

- `evidence/_t015_manual.txt` (saída bruta)
- `_reversa_forward/009-rota-do-apple-touch-icon/onboarding.md` (os passos)
- `evidence/T008-arte-na-imagem.md`, `evidence/T009-rota-no-conteiner.md`

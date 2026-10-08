# T009 — A rota responde de dentro do contêiner

> Feature: `009-rota-do-apple-touch-icon` · Ação: `T009` · Data: `2026-10-08`
> Registro bruto: `evidence/_t008_t009_conteiner.txt`

## Por que esta ação é separada da `T008`

As duas parecem olhar a mesma coisa e **não olham**. A `T008` prova que o arquivo está na
imagem; esta prova que a **rota** o encontra e o serve. Um arquivo presente com a rota
quebrada — caminho montado errado, `root_path` diferente, exceção silenciosa — passaria na
`T008` e falharia aqui.

O detalhe que faz a diferença: de dentro do contêiner, a porta é a **do contêiner**, e não
a `5080` publicada no host.

## Medição — de dentro do contêiner

```
status 200
tipo image/png
bytes 16504
etag "1791485083.0-16504-4142140804"
cache-control no-cache
```

| Verificação | Requisito | Medido |
|---|---|---|
| Status | `RF-01` | ✅ **200** |
| Tipo de conteúdo | `RF-01` | ✅ `image/png` |
| Tamanho do corpo | `RF-02`/`RF-03` | ✅ **16.504 bytes** |
| Marca de versão presente | `RF-07` | ✅ `ETag` emitido |
| **Sem validade longa** | `RF-07`, `D-05` | ✅ **`no-cache`** |

> `Cache-Control: no-cache` é exatamente o que a `D-05` decidiu: revalidação barata pelo
> `ETag`, e **nenhuma** validade declarada. Não há `max-age`. Uma arte que foi trocada duas
> vezes em um único dia não pode ser congelada no cliente por um ano.

## Medição — do host, pela porta publicada

```
GET /apple-touch-icon.png -> 200  (16504 bytes)
GET /                     -> 200  (23906 bytes)
GET /favicon.ico          -> 404
```

Duas linhas valem destaque:

- **`GET /` devolve 23.906 bytes** — exatamente o mesmo número medido **antes** de a rota
  existir, e o mesmo `sha256` (`4b7f0b0c…`) que o teste `test_a_tela_nao_mudou_um_byte`
  prende. O `RF-05` está provado no ambiente real, e não apenas no cliente de teste.
- **`/favicon.ico` continua `404`** — a `RN-09` no ar. Nenhum caminho sem consumidor foi
  criado, e o navegador de desktop continua usando o ícone **declarado** no documento.

## Veredito

**APROVADO.** A rota serve a arte certa, com a política de cache decidida, de dentro da
imagem e pela porta publicada, sem tocar em nada que já existia.

## Fontes

- `evidence/_t008_t009_conteiner.txt` (saída bruta)
- `_reversa_forward/009-rota-do-apple-touch-icon/interfaces/apple-touch-icon.md` (o contrato)
- `_reversa_forward/009-rota-do-apple-touch-icon/roadmap.md` (`D-04`, `D-05`, `D-06`, `D-07`)

# Contrato HTTP — recursos embutidos da tela

> Identificador: `054-embutir-bootstrap-e-mermaid`
> Data: `2026-10-31`
> Blueprint: `assets_bp` (`src/web/rotas_assets.py`)
> Status: contrato novo, proposto pelo `roadmap.md` (`D-03`, `D-04`, `D-10`, `D-12`)

## 1. Superfície

| Método | Caminho | Endpoint | Corpo servido | Tipo de mídia |
|--------|---------|----------|---------------|---------------|
| GET | `/bootstrap.css` | `assets.biblioteca_css` | `src/assets/bootstrap.min.css` (Bootstrap 5.3.3) | `text/css` |
| GET | `/bootstrap.js` | `assets.biblioteca_js` | `src/assets/bootstrap.bundle.min.js` (5.3.3) | `text/javascript` |
| GET | `/mermaid.js` | `assets.mermaid` | `src/assets/mermaid.min.js` (10.9.8) | `text/javascript` |
| GET | `/fontes.css` | `assets.folha_de_fontes` | `src/assets/fontes.css` | `text/css` |
| GET | `/fontes/<arquivo>.woff2` | `assets.fonte` | `src/assets/fontes/<arquivo>.woff2` | `font/woff2` |

Somente `GET`. Qualquer outro método recebe `405` do roteador, sem corpo e sem tocar em disco.

## 2. Requisição

Sem parâmetros de consulta obrigatórios. `?v=<versão>` é aceito e **ignorado** pelo servidor: existe só para
invalidar cache no navegador (`D-12`). Nenhum cabeçalho de requisição é exigido; `Range` não é suportado (o
`send_file` do Flask responde o recurso inteiro).

## 3. Resposta de sucesso

```
HTTP/1.1 200 OK
Content-Type: text/css
Content-Length: 232803
ETag: "<hash do arquivo>"
Last-Modified: <mtime>
X-Frame-Options: DENY
```

Regras:

1. O corpo é **byte a byte** o arquivo em disco, sem transformação, compressão em disco ou reescrita.
2. O `Content-Length` é o tamanho real; os tamanhos medidos em 2026-10-31 são 232.803, 80.721 e 3.337.857 bytes
   para as três bibliotecas, cerca de 17 KB para a folha de fontes e o tamanho de cada `woff2`.
3. `X-Frame-Options: DENY` vem do `after_request` da borda, como em todas as respostas — a rota não o define.
4. `X-Request-ID` e a linha de acesso continuam vindo do registro da feature 049.

## 4. Cache e revalidação

| Situação | Comportamento |
|----------|---------------|
| Primeira requisição | `200` com `ETag` e `Last-Modified` |
| Rebusca com `If-None-Match` igual | `304`, sem corpo |
| Rebusca após o arquivo mudar | `200` com `ETag` novo |
| Arquivo substituído sem trocar o `?v=` | o navegador revalida e recebe `200`; o `?v=` é conveniência, não correção de cache |

Não há `Cache-Control` novo: o regime é o mesmo das artes (validação barata por `ETag`, sem validade longa). A
política de `no-store` das telas de identidade **não** alcança estes recursos — eles são públicos por decisão
(`RN-06`).

## 5. Autenticação e autorização

Públicos. Os cinco endpoints entram em `PUBLICOS` (`src/web/sessao.py`), como `/app.css`, `/banner.png` e
`/apple-touch-icon.png`. Sem isso, a tela de entrada — servida a quem não tem sessão — perderia o estilo.

## 6. Erros

| Situação | Resposta | Corpo |
|----------|----------|-------|
| Arquivo do conjunto ausente no disco | `404` | vazio |
| Nome de `woff2` fora do conjunto fechado | `404` | vazio |
| Nome de `woff2` com separador, `..` ou NUL | `404` | vazio |
| Arquivo de biblioteca ausente (`config` apontando para nada) | `404` | vazio |
| Método diferente de `GET` | `405` | do Flask |

`404` e nunca `500`: o mesmo regime da arte e da folha, em que arquivo ausente degrada a tela sem derrubar a
aplicação. Nenhum erro revela caminho absoluto nem confirma a existência de arquivo fora do conjunto.

## 7. Idempotência, concorrência e tempo

- `GET` é idempotente e sem efeito colateral; não há escrita, trava ou estado de processo novo.
- Não há timeout próprio: a resposta é leitura de disco seguida de envio.
- Duas requisições simultâneas leem o mesmo arquivo independentemente — o `send_file` abre um descritor por
  resposta.

## 8. Limites e medição

- A soma dos recursos de uma carga completa da tela principal é **3.852.849 bytes** (~3,67 MiB) na primeira visita;
  nas seguintes, só o que mudou volta a ser baixado.
- O teto declarado no `requirements.md` é de 4 MB para a soma dos arquivos embutidos.
- O tempo de resposta de cada rota e o peso total por página entram na medição da feature e no adendo.

## 9. Compatibilidade

Nenhuma rota existente muda de contrato: `/`, `/app.css`, `/banner.png`, `/apple-touch-icon.png`, `/favicon.png`,
`/descartes.csv`, `/busca` e as rotas de identidade permanecem idênticas em método, status e corpo.

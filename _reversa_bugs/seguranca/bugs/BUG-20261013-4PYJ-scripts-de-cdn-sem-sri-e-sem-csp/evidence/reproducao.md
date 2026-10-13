# Reproducao: scripts de CDN sem integridade e ausencia de CSP

**Ambiente da medicao:** Windows, Python 3.14.6 do `.venv/` do repositorio, app servido por
waitress na porta 5099 em loopback.

## Passos

1. Subir o app em loopback.
2. `GET /` e inspecionar a resposta: cabecalhos e as tags `<script>` e `<link>` do HTML.

## Observado

Cabecalhos da resposta (lista completa):

```
content-length: 28858
content-type: text/html; charset=utf-8
date: Tue, 13 Oct 2026 14:49:20 GMT
server: waitress
```

Ausentes, entre outros: `Content-Security-Policy`, `X-Frame-Options`,
`X-Content-Type-Options`, `Referrer-Policy`, `Strict-Transport-Security`.

Tags de script com origem externa (as duas sem `integrity` e sem `crossorigin`):

```html
<script src="https://cdn.jsdelivr.net/npm/mermaid@10/dist/mermaid.min.js">
<script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.3/dist/js/bootstrap.bundle.min.js">
```

Outras origens externas carregadas pela pagina, tambem sem integridade:

- `https://cdn.jsdelivr.net/npm/bootstrap@5.3.3/dist/css/bootstrap.min.css`
- `https://fonts.googleapis.com` e a folha `css2?family=Newsreader...&family=IBM+Plex+Sans...`
- `https://fonts.gstatic.com`

## Origem no codigo

`src/templates/index.html:120` (mermaid) e `:823` (bootstrap bundle); a folha em `:90` e as
fontes em `:100-102`. O projeto nao emite cabecalho de seguranca em lugar nenhum
(`src/app.py` registra apenas `MAX_CONTENT_LENGTH`, `TRUSTED_HOSTS` e os filtros de
template).

## O que este defeito e, e o que nao e

E ausencia de controle: nao ha SRI nem CSP, entao o codigo executado na origem da aplicacao
e exatamente o que o CDN entregar no momento da carga, e nao existe segundo mecanismo que
limite o que um script comprometido faria. Nao foi medido nenhum comprometimento do CDN, e
nao houve teste com navegador (a consequencia de um SRI ausente e comportamento de
navegador documentado).

## Evidencia bruta

- `estatico.json`: cabecalhos completos, tags de script, lista de origens externas e as
  varreduras de formulario.
- `estatico-get-index.html`: HTML cru de `GET /`.
- Sonda: `_reversa_bugs/_sondas-seguranca/sondas_http.py` (grupo `estatico`).

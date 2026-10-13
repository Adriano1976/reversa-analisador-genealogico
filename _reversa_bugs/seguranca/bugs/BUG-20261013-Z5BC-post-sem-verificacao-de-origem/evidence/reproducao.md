# Reproducao: POST que muda estado sem verificacao de origem nem token

**Ambiente da medicao:** Windows, Python 3.14.6 do `.venv/` do repositorio, app servido por
waitress na porta 5099 em loopback, pasta de upload desviada para um diretorio temporario,
dados sinteticos.

## Passos

1. Subir o app em loopback.
2. `POST /` com `action=upload_gedcom`, o campo `gedcom` com `arvore_valida.ged`, e os
   cabecalhos `Origin: http://atacante.exemplo` e
   `Referer: http://atacante.exemplo/pagina-hostil.html`.
3. Ler a resposta e a pasta de upload.
4. Com a referencia devolvida pelo passo 2, `POST /` com `action=aposentar_arquivo` e
   `arquivo_a_aposentar=<referencia>`, com os **mesmos** cabecalhos hostis.
5. Repetir os dois passos sem `Origin` nem `Referer`.

## Observado

| Requisicao | Cabecalhos | Resultado |
|---|---|---|
| Upload | `Origin` e `Referer` hostis | **200**, `Arquivo 'arvore_valida.ged' carregado!`, arquivo criado (`...__arvore_valida.ged`) |
| Upload | sem `Origin` nem `Referer` | **200**, mesmo resultado |
| `aposentar_arquivo` | `Origin` e `Referer` hostis | **200**, `'arvore valida' saiu da lista`, arquivo movido para `_aposentados/` (709 bytes, integro) |
| `aposentar_arquivo` | sem `Origin` nem `Referer` | **200**, mesmo resultado |

Complemento medido na mesma resposta de `GET /`:

- nenhum campo de token em nenhum formulario (`csrf`, `_csrf`, `csrf_token`,
  `authenticity_token`, `__RequestVerificationToken`: nenhum presente);
- nenhum `Set-Cookie` em nenhuma resposta, ou seja, nao ha sessao a que amarrar um token;
- `Host: 127.0.0.1:5099` com `Origin` hostil e **aceito**: a lista de `TRUSTED_HOSTS`
  fecha o DNS rebinding (Host com dominio do atacante responde 400), nao o CSRF de uma
  pagina que endereca `127.0.0.1` diretamente.

## Origem no codigo

`src/app.py:506-563`: a rota le `request.form.get("action")` e executa
`upload_gedcom` ou `aposentar_arquivo` sem ler `Origin`, `Referer` ou qualquer campo de
token. As duas acoes de estado estao em formularios sem campo oculto de token
(`src/templates/index.html:58-73` para o botao de aposentar e `:263-272` para o envio).

## O que nao foi medido

Nao houve teste com navegador real: o que esta medido e a resposta do servidor a uma
requisicao com `Origin` de outro site. A conclusao de que uma pagina hostil consegue
disparar esse POST depende do navegador do operador (o pedido e um POST de formulario
simples, sem preflight) e de a aplicacao estar no ar quando a pagina for aberta.

## Evidencia bruta

- `origem.json`: os quatro casos, com as mensagens e o retrato da pasta de aposentados.
- `origem-upload.html` e `origem-aposentar-com_origin_hostil.html`: HTML cru.
- `estatico.json`: a varredura de formularios e a ausencia de campo de token.
- Sonda: `_reversa_bugs/_sondas-seguranca/sondas_http.py` (grupo `origem`).

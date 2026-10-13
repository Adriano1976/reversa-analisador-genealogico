# Reproducao: resposta sem protecao de enquadramento

**Ambiente da medicao:** Windows, Python 3.14.6 do `.venv/` do repositorio, app servido por
waitress na porta 5099 em loopback, dados sinteticos.

## Passos

1. Subir o app em loopback.
2. `GET /` e inspecionar os cabecalhos de resposta e o HTML do formulario que contem a acao
   destrutiva.

## Observado

- Nenhum `X-Frame-Options`.
- Nenhum `Content-Security-Policy` (portanto nenhum `frame-ancestors`).
- Cabecalhos da resposta: `content-length`, `content-type`, `date`, `server: waitress`.
- O formulario da acao destrutiva esta na propria pagina:

```html
<form method="POST" class="m-0"
      onsubmit='return confirm(("Apagar \"<nome>\"? Ele sai da lista e continua guardado no disco, na pasta de aposentados."));'>
  <input type="hidden" name="action" value="aposentar_arquivo">
  <input type="hidden" name="arquivo_a_aposentar" value="<nome armazenado>">
```

## Por que importa

O botao faz o arquivo sair da lista do operador (sem apagar, conforme a `RN-14`), e a
pagina nao tem nenhum controle que impeça outra origem de enquadra-la:

1. Nao existe cabecalho que recuse o enquadramento.
2. A acao de estado nao tem token nem verificacao de origem (o defeito
   `BUG-20261013-Z5BC`), entao uma pagina que consiga sobrepor a interface pode disparar a
   submissao sem que o operador veja o que clicou.

O `confirm()` do `onsubmit` e uma barreira de interface: ele aparece na janela enquadrada e
pede uma confirmacao, o que reduz o risco de um clique unico acidental, mas nao e um
controle de servidor.

## O que nao foi medido

Nao houve teste com navegador real (criar uma pagina com `<iframe src="http://127.0.0.1:...">`
e observar a carga). O que esta medido e a **ausencia dos dois controles** na resposta HTTP;
que um navegador enquadre a pagina sem eles e comportamento padrao documentado.

## Evidencia bruta

- `estatico.json`: a lista de cabecalhos ausentes e a presenca do formulario.
- `estatico-get-index.html`: HTML cru de `GET /`.
- Sonda: `_reversa_bugs/_sondas-seguranca/sondas_http.py` (grupo `estatico`).

---
schema_version: 1
id: BUG-20261013-Z5BC
display_number: 10
title: POST que muda estado sem verificacao de origem nem token
status: open
phase: triaging
severity: medium
priority: P2
created: 2026-10-13
updated: 2026-10-13

origin:
  type: inspection
  external_ref:
    provider: security-audit
    id: checklist-auditoria-reversa-analisador-genealogico.md#1
area: analisador-genealogico
module: upload
feature: upload-gedcom
labels: [seguranca, borda-http, csrf, spec-gap]

visibility: restricted
security_suspected: true

reproduction:
  classification: deterministic
  rate: "4/4"
  suspected_triggers: []

blocking: []

relationships:
  - bug: BUG-20260929-BJJH
    type: related-to
    state: supported
    evidence:
      - ref: _reversa_sdd/permissions.md
        observation: >-
          A ausencia de identidade e o que da consequencia ao CSRF: sem sessao e sem credencial, a
          requisicao cruzada nao precisa se passar por ninguem, porque nao ha ninguem a representar.
      - ref: _reversa_bugs/seguranca/inspections/checklist-20261013/RESULTADOS-DO-CHECKLIST.md
        observation: >-
          Medido: nenhum Set-Cookie em nenhuma resposta e nenhum campo de token em nenhum
          formulario da tela.

traceability:
  specs:
    - _reversa_sdd/permissions.md#1
    - _reversa_sdd/permissions.md#3
    - _reversa_sdd/permissions.md#6
    - _reversa_sdd/domain.md#4
    - _reversa_sdd/openapi/index.yaml
    - _reversa_sdd/addenda/014-endurecimento-da-borda.md#a-lista-de-host-o-que-ela-defende-e-o-que-ela-não-é
    - _reversa_sdd/adrs/18-single-tenant-por-aceite-de-risco.md#decisão
  affected_code:
    - src/app.py
    - src/templates/index.html
  root_cause: null
  reproduction_tests: []
  regression_tests: []

spec_verdict: null

change_set: []

closure:
  policy: local-software
  satisfied: false
resolution_kind: null
---

# POST que muda estado sem verificacao de origem nem token

## Summary

A unica rota que muda estado (`GET|POST /`) despacha por `request.form.get("action")` e executa
`upload_gedcom` ou `aposentar_arquivo` sem ler `Origin`, `Referer` ou qualquer campo de token.
Medido com cabecalhos de outro site:

| Requisicao | Cabecalhos | Resultado |
|---|---|---|
| Upload de GEDCOM | `Origin: http://atacante.exemplo`, `Referer: http://atacante.exemplo/pagina-hostil.html` | **200**, arquivo gravado, `Arquivo 'arvore_valida.ged' carregado!` |
| `aposentar_arquivo` | os mesmos cabecalhos hostis | **200**, arquivo movido para `_aposentados/` (709 bytes, integro) |
| Ambos | sem `Origin` nem `Referer` | **200**, mesmo resultado |

Complemento medido na mesma resposta de `GET /`: nenhum campo `csrf`, `_csrf`, `csrf_token`,
`authenticity_token` ou `__RequestVerificationToken` em nenhum formulario, e nenhum `Set-Cookie`
em nenhuma resposta. Nao ha sessao a que amarrar um token, e nao ha verificacao de procedencia.

**A lista de `Host` nao fecha este vetor, e isso foi medido.** `Host: 127.0.0.1:5099` com `Origin`
hostil e **aceito**; o que a lista recusa e o `Host` de outro dominio (400), que e o DNS rebinding.
Uma pagina hostil que simplesmente endereça `127.0.0.1` passa pela lista.

## Expected Behavior

Nenhum artefato da spec efetiva especifica verificacao de procedencia (`spec-gap`). O que existe e
a **declaracao de ausencia**, e ela e explicita:

- `_reversa_sdd/permissions.md#3` define o escopo da matriz de permissoes: *"todas as permissoes
  valem para **qualquer** solicitante, sem credencial"*.
- `_reversa_sdd/permissions.md#6` (`P-08`) registra que as rotas publicas **nao verificam origem** e
  conta *"7 rotas, nenhuma com credencial"*.
- `_reversa_sdd/domain.md#4` descreve o fluxo por `action` sem nenhuma pre-condicao de procedencia.
- `_reversa_sdd/openapi/index.yaml` documenta `POST /` com as cinco `action` e o corpo multipart,
  sem qualquer cabecalho de origem ou token.
- `_reversa_sdd/adrs/18-single-tenant-por-aceite-de-risco.md#decisão` e
  `_reversa_sdd/addenda/014-endurecimento-da-borda.md#a-lista-de-host-o-que-ela-defende-e-o-que-ela-não-é`
  declaram que a lista de `Host` **nao e autenticacao** e fecha apenas um vetor de navegador
  (DNS rebinding), com a frase: *"nada aqui deixa a aplicacao segura para expor."*

Ou seja: o projeto **decidiu nao ter identidade** e **decidiu fechar** o DNS rebinding; nao decidiu
nada sobre a requisicao cruzada simples, que continua funcionando. O comportamento esperado, para
uma aplicacao que ja reconheceu o vetor de navegador, e fechar o outro lado: ou verificar
`Origin`/`Referer` e recusar o que nao for a propria origem, ou exigir token de formulario, ou
declarar por escrito que a requisicao cruzada e aceita como consequencia do aceite de risco.

## Actual Behavior

`src/app.py:506-563`: a rota le `action` e executa; `src/templates/index.html:58-73` (botao
"Apagar", com `onsubmit` de `confirm`) e `:263-272` (envio de GEDCOM) nao tem campo oculto de
token. Nao ha `flask.session` em lugar nenhum: `app.secret_key` foi removido em 2026-10-05
justamente por nao ter consumidor (`P-04`).

## Steps to Reproduce

1. Subir o app em loopback, com pasta de upload desviada e dados sinteticos.
2. `POST /` com `action=upload_gedcom`, `filename="arvore_valida.ged"`, `Origin` e `Referer` de
   outro site.
3. Repetir com `action=aposentar_arquivo` e `arquivo_a_aposentar` igual a referencia devolvida.
4. Conferir que a pasta de upload e a de aposentados mudaram, e que nenhuma resposta emitiu
   `Set-Cookie`.

Passo a passo completo: `evidence/reproducao.md`.

## Evidence

- `evidence/origem.json`: os quatro casos, com mensagens e retrato da pasta de aposentados.
- `evidence/origem-upload.html` e `evidence/origem-aposentar-com_origin_hostil.html`: HTML cru.
- `evidence/estatico.json`: varredura dos formularios e ausencia de campo de token.
- `_reversa_bugs/seguranca/inspections/checklist-20261013/RESULTADOS-DO-CHECKLIST.md` item 1.

## Suspected Area

`src/app.py` (rota `index`, ramos `upload_gedcom` e `aposentar_arquivo`) e
`src/templates/index.html` (os dois formularios de estado).

## Acceptance Criteria

1. Decisao humana registrada: fechar, ou declarar aceito com a consequencia escrita. Nao existe
   hoje nem uma coisa nem outra.
2. Se fechar por origem: requisicao com `Origin` ou `Referer` de outro site recebe recusa, e a
   requisicao sem os dois cabecalhos continua funcionando (o `curl` do operador nao pode quebrar).
3. Se fechar por token: o token tem de sobreviver sem sessao, ou a sessao passa a existir com
   `secret_key` gerada e nunca versionada (`P-04`).
4. A recusa nao pode transformar a acao destrutiva em algo mais facil de disparar: a acao de
   aposentar continua exigindo o `confirm()` da tela e a referencia exata.
5. Teste de regressao que falha se um `POST` de estado for aceito com `Origin` de terceiro.

## Traceability

| Item | Valor |
|---|---|
| Specs | `_reversa_sdd/permissions.md#1`, `#3`, `#6` (`P-08`, `P-04`), `_reversa_sdd/domain.md#4`, `_reversa_sdd/openapi/index.yaml` (`POST /`), `_reversa_sdd/addenda/014-endurecimento-da-borda.md#a-lista-de-host-o-que-ela-defende-e-o-que-ela-não-é`, `_reversa_sdd/adrs/18-single-tenant-por-aceite-de-risco.md#decisão` |
| Veredito preliminar | `spec-gap`: a spec declara a ausencia de identidade e de credencial, e nao especifica procedencia em nenhum lugar |
| Codigo afetado | `src/app.py:506-563`, `src/templates/index.html:58-73`, `:263-272` |
| Causa raiz | nao preenchida (o registro nao corrige) |
| Testes de reproducao | a escrever: nenhum teste asserta recusa por `Origin` nem presenca de token |
| Testes existentes vizinhos | `tests/test_host_permitido.py::TestOAlcanceDaRecusa` (prende a recusa por `Host`, inclusive no `POST /`, que e o controle vizinho e **nao** cobre origem), `tests/test_upload_seguranca.py::TestReproducao`, `tests/test_aposentar_arquivo.py` (exercitam `POST /` sem `Origin`, sem assertar recusa) |

## Resolution

Nao preenchida. Este registro documenta e nao corrige; a correcao e do `/reversa-debugger-fix`.

## Agent Notes

- **Prioridade depende do modo de operacao.** No loopback, o atacante ainda precisa do navegador do
  operador aberto numa pagina hostil; no modo com `ANALISADOR_HOSTS_PERMITIDOS` preenchido, o
  alcance e maior. Reclassificar antes de expor, como o proprio checklist manda.
- **Nao repetir o erro de confundir isto com autenticacao.** Adicionar verificacao de origem **nao**
  cria identidade: `curl` continua entrando. O que muda e o vetor de navegador.
- **Cuidado com o `confirm()` do `onsubmit`.** Ele e barreira de interface, nao de servidor, e nao
  impede um clique encenado. Ver o `BUG-20261013-X7EN`, que e o outro lado da mesma moeda.
- **`app.secret_key` nao pode voltar versionada.** A `P-04` registra por que o literal foi removido.
  Se o fix introduzir sessao, a chave vem do ambiente.
- **Sem proposta de taxonomia nova:** `module: upload` cobre as duas acoes de estado; a segunda
  (`aposentar_arquivo`) pertence a `tela-de-entrada` na extracao, unidade que ainda nao tem valor
  no `taxonomy.yaml`. Fica proposto, para decisao humana, acrescentar `tela-de-entrada` a
  `feature`.

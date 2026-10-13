---
schema_version: 1
id: BUG-20261013-4PYJ
display_number: 11
title: Scripts de CDN sem integridade e ausencia de Content-Security-Policy
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
    id: checklist-auditoria-reversa-analisador-genealogico.md#5
area: analisador-genealogico
module: unclassified
feature: unclassified
labels: [seguranca, supply-chain, borda-http, spec-gap]

visibility: restricted
security_suspected: true

reproduction:
  classification: deterministic
  rate: "1/1"
  suspected_triggers: []

blocking: []

relationships: []

traceability:
  specs:
    - _reversa_sdd/architecture.md#6
    - _reversa_sdd/c4-containers.md#2
    - _reversa_sdd/c4-context.md
    - _reversa_sdd/adrs/03-mermaid-no-cliente.md#decisão
    - _reversa_sdd/addenda/013-revisao-de-design-da-tela.md#dívidas-declaradas-não-fechadas
    - _reversa_sdd/addenda/001-reconstrua-o-conteudo-da-index.md
  affected_code:
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

# Scripts de CDN sem integridade e ausencia de Content-Security-Policy

## Summary

A tela carrega duas bibliotecas de terceiros por CDN **sem atributo `integrity` e sem
`crossorigin`**, e nenhuma resposta da aplicacao emite `Content-Security-Policy`. Medido em
`GET /` (resposta real):

```html
<script src="https://cdn.jsdelivr.net/npm/mermaid@10/dist/mermaid.min.js">
<script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.3/dist/js/bootstrap.bundle.min.js">
```

Tambem vem de CDN sem integridade a folha do Bootstrap
(`.../bootstrap@5.3.3/dist/css/bootstrap.min.css`) e as fontes do Google
(`fonts.googleapis.com`, `fonts.gstatic.com`).

Cabecalhos da resposta, na lista completa: `content-length`, `content-type`, `date`,
`server: waitress`. Ausentes: `Content-Security-Policy`, `X-Frame-Options`,
`X-Content-Type-Options`, `Referrer-Policy`, `Strict-Transport-Security`.

O efeito e que o codigo executado na origem da aplicacao e exatamente o que o CDN entregar no
momento da carga do script, e **nao ha segundo mecanismo** que limite o que esse codigo poderia
fazer com a tela, com os dados de DNA em memoria do DOM e com os formularios de estado.

## Expected Behavior

A spec **determina o CDN** e **nunca especifica controle de integridade**:

- `_reversa_sdd/architecture.md#6` e `_reversa_sdd/c4-containers.md#2` declaram "Bootstrap 5.3.3 e
  Mermaid 10 por CDN" como integracao externa, com HTTPS.
- `_reversa_sdd/c4-context.md` registra o "CDN web" como o unico trafego de saida feito pelo
  navegador do usuario, e nota que o Mermaid e inicializado com `securityLevel: 'strict'`.
- `_reversa_sdd/adrs/03-mermaid-no-cliente.md#decisão` fixa a decisao de renderizar no cliente com
  Mermaid por CDN.
- `_reversa_sdd/addenda/013-revisao-de-design-da-tela.md#dívidas-declaradas-não-fechadas` (`D-06`)
  reconhece o Google Fonts como **terceiro** host de CDN e o classifica como "decisao a declarar".
- `_reversa_sdd/addenda/001-reconstrua-o-conteudo-da-index.md` registra a unica decisao de
  seguranca de front-end do projeto: o Mermaid passou a `securityLevel: 'strict'`, fechando XSS
  vindo dos arquivos do usuario.

Nao existe nenhuma ocorrencia de "Content-Security-Policy", "integrity", "crossorigin", "SRI",
"X-Frame-Options" ou "frame-ancestors" em toda a `_reversa_sdd/` (`spec-gap`). O projeto decidiu
**quais** bibliotecas externas usar e **nao decidiu** como garantir que o que chega e o que se
pretendia. O comportamento esperado: cada `<script src="https://...">` acompanhado de
`integrity` mais `crossorigin`, ou o arquivo hospedado pela propria aplicacao; e, na resposta, um
`Content-Security-Policy` que declare de onde script e estilo podem vir.

## Actual Behavior

`src/templates/index.html:120` (mermaid) e `:823` (bootstrap bundle) sem `integrity`; a folha em
`:90` e as fontes em `:100-102` tambem sem. `src/app.py` nao registra nenhum `@app.after_request`
nem cabecalho de seguranca: a resposta carrega apenas o que o Flask e o waitress emitem.

## Steps to Reproduce

1. Subir o app em loopback.
2. `GET /` e inspecionar a lista de cabecalhos e as tags `<script src>` e `<link href>` do HTML.

Passo a passo completo: `evidence/reproducao.md`.

## Evidence

- `evidence/estatico.json`: cabecalhos completos, tags de script sem `integrity`, lista de origens
  externas e as varreduras de formulario.
- `evidence/estatico-get-index.html`: HTML cru de `GET /`.
- `_reversa_bugs/seguranca/inspections/checklist-20261013/RESULTADOS-DO-CHECKLIST.md` item 5.

## Suspected Area

`src/templates/index.html` (as quatro origens externas) e a montagem do app em `src/app.py` (onde
um cabecalho de resposta teria de ser emitido).

## Acceptance Criteria

1. Cada `<script src="https://...">` tem `integrity` e `crossorigin`, ou o arquivo passa a ser
   servido pela aplicacao (como a folha `app.css` ja e).
2. A resposta de `GET /` emite `Content-Security-Policy` com `default-src 'self'` e a lista
   explicita dos hosts de CDN aceitos, incluindo `frame-ancestors` (ver
   `BUG-20261013-X7EN`, que e a metade de enquadramento do mesmo problema).
3. O `securityLevel: 'strict'` do Mermaid continua como esta: ele e outra defesa e nao foi
   substituto nem substituto dele.
4. Teste de regressao que falha se uma tag `<script src="http...">` sem `integrity` aparecer no
   HTML servido, e se o cabecalho CSP sumir.

## Traceability

| Item | Valor |
|---|---|
| Specs | `_reversa_sdd/architecture.md#6`, `_reversa_sdd/c4-containers.md#2`, `_reversa_sdd/c4-context.md`, `_reversa_sdd/adrs/03-mermaid-no-cliente.md#decisão`, `_reversa_sdd/addenda/013-revisao-de-design-da-tela.md#dívidas-declaradas-não-fechadas` (`D-06`), `_reversa_sdd/addenda/001-reconstrua-o-conteudo-da-index.md` |
| Veredito preliminar | `spec-gap`: a spec determina o CDN e nao especifica nenhum controle de integridade ou de politica de conteudo |
| Codigo afetado | `src/templates/index.html:90`, `:100-102`, `:120`, `:823` |
| Causa raiz | nao preenchida (o registro nao corrige) |
| Testes de reproducao | a escrever: nenhum teste asserta presenca de `integrity` ou de CSP |
| Testes existentes vizinhos | `tests/test_icone_de_atalho.py::test_a_tela_nao_mudou_um_byte` (`SHA_DA_TELA` do HTML de `GET /`, mantido a mao: **adicionar `integrity` muda o hash e quebra este teste**), `tests/test_host_permitido.py` (unico arquivo que asserta cabecalho de seguranca, e so a recusa por `Host`) |

## Resolution

Nao preenchida. Este registro documenta e nao corrige; a correcao e do `/reversa-debugger-fix`.

## Agent Notes

- **Ordem pratica: primeiro o CSP, depois o SRI.** O cabecalho nao toca o HTML e nao mexe no
  `SHA_DA_TELA`; o `integrity` mexe, e por isso exige a declaracao de adendo prevista no proprio
  comentario de `tests/test_icone_de_atalho.py` antes de o hash ser atualizado.
- **O `integrity` do Mermaid exige escolher a versao exata.** Hoje a URL e `mermaid@10` (faixa
  flutuante): nao ha hash estavel para uma faixa. Fixar a versao (`10.x.y`) e parte do conserto, e
  isso e mudanca de dependencia de front-end, com adendo.
- **Fontes do Google ficam de fora do SRI** (CSS de resposta varia por `User-Agent`); o caminho
  honesto para elas e CSP com host explicito, ou fonte local. O `D-06` do adendo 013 ja registra
  que carregar fonte de terceiro e decisao a declarar.
- **Proposta de taxonomia:** `module` e `feature` ficaram `unclassified` porque o
  `taxonomy.yaml` nao tem valor para a camada de apresentacao. Proponho acrescentar
  `module: apresentacao` (assets e borda de front-end) e `feature: tela-de-entrada`, que ja existe
  como unidade em `_reversa_sdd/tela-de-entrada/`. Decisao humana.

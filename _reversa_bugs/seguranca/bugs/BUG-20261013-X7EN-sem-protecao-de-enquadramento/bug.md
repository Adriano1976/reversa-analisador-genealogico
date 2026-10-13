---
schema_version: 1
id: BUG-20261013-X7EN
display_number: 12
title: Resposta sem protecao de enquadramento na pagina com acao destrutiva
status: resolved
phase: delivering
severity: medium
priority: P2
created: 2026-10-13
updated: 2026-10-13

origin:
  type: inspection
  external_ref:
    provider: security-audit
    id: checklist-auditoria-reversa-analisador-genealogico.md#6
area: analisador-genealogico
module: unclassified
feature: unclassified
labels: [seguranca, borda-http, clickjacking, spec-gap]

visibility: restricted
security_suspected: true

reproduction:
  classification: deterministic
  rate: "1/1"
  suspected_triggers: []

blocking: []

relationships:
  - bug: BUG-20261013-Z5BC
    type: related-to
    state: supported
    evidence:
      - ref: _reversa_bugs/seguranca/inspections/checklist-20261013/RESULTADOS-DO-CHECKLIST.md
        observation: >-
          Os dois se compoem: sem controle de enquadramento a pagina pode ser sobreposta, e sem
          verificacao de origem a submissao disparada por ela e aceita. O segundo foi medido aceito
          com Origin hostil.

traceability:
  specs:
    - _reversa_sdd/openapi/index.yaml
    - _reversa_sdd/recursos-da-tela/contracts.md#1
    - _reversa_sdd/domain.md#4
    - _reversa_sdd/permissions.md#3
    - _reversa_sdd/addenda/014-endurecimento-da-borda.md#a-lista-de-host-o-que-ela-defende-e-o-que-ela-não-é
  affected_code:
    - src/app.py
    - src/templates/index.html
  root_cause:
    state: confirmed
    hypothesis: >-
      `src/app.py` nao registra `after_request` nem emite cabecalho por rota, entao a resposta carrega
      apenas o que o Flask e o waitress produzem. Nenhum artefato da spec efetiva previu controle de
      enquadramento, e a unica defesa de borda especificada (a lista de `Host`) declara explicitamente
      que nao e protecao de enquadramento nem de origem.
    causal_path:
      - "A resposta de `GET /` traz apenas `content-length`, `content-type`, `date` e `server: waitress` (medido)."
      - "`src/app.py` nao tem `@app.after_request` nem cabecalho por rota; o template tambem nao os declara."
      - "O formulario da acao destrutiva (`action=aposentar_arquivo`) vive nessa pagina (src/templates/index.html:68-73), e o `confirm()` do `onsubmit` e barreira de interface, nao de servidor."
      - "Sem `X-Frame-Options` nem `frame-ancestors`, nada impede outra origem de enquadrar a unica pagina do sistema."
    evidence:
      - ref: evidence/estatico.json
        observation: >-
          Lista de cabecalhos ausentes (`content-security-policy`, `x-frame-options`, `x-content-type-options`,
          `referrer-policy`, `strict-transport-security`) e a presenca do formulario destrutivo.
      - ref: evidence/estatico-get-index.html
        observation: >-
          HTML cru de `GET /`, com os cabecalhos completos da resposta: so `content-length`, `content-type`,
          `date` e `server`.
      - ref: _reversa_bugs/seguranca/inspections/checklist-20261013/RESULTADOS-DO-CHECKLIST.md
        observation: >-
          Item 6, que separa o que foi medido (ausencia dos dois controles na resposta HTTP) do que ficou
          inferido (o navegador enquadrar a pagina sem eles).
    code_refs:
      - file: src/app.py
        symbol: index
        commit: c670788
      - file: src/templates/index.html
        symbol: formulario de aposentar_arquivo
        commit: c670788
  reproduction_tests:
    - tests/test_cabecalho_de_enquadramento.py::TestReproducao::test_toda_resposta_traz_o_cabecalho_de_enquadramento
  regression_tests:
    - tests/test_cabecalho_de_enquadramento.py::TestRegressao::test_o_corpo_da_tela_continua_o_mesmo
    - tests/test_cabecalho_de_enquadramento.py::TestRegressao::test_o_cabecalho_nao_acrescenta_nem_remove_byte_do_corpo
    - tests/test_icone_de_atalho.py::test_a_tela_nao_mudou_um_byte

spec_verdict: spec-gap

change_set:
  - id: CHG-001
    kind: code
    artifact: src/app.py
    purpose: >-
      `@app.after_request` que acrescenta `X-Frame-Options: DENY` a TODA resposta, com o motivo
      escrito no codigo. Aplicado e verificado em 2026-10-13.
    diff: fix/CHG-001.diff
  - id: CHG-002
    kind: specification
    artifact: _reversa_sdd/addenda/bug-BUG-20261013-X7EN-v001.md
    purpose: >-
      Adendo ADITIVO que especifica o cabecalho de enquadramento pela primeira vez (`spec-gap`
      recomendado) e registra que o `Content-Security-Policy` ficou de fora, com o motivo.
    diff: fix/CHG-002.diff
  - id: CHG-003
    kind: test
    artifact: tests/test_cabecalho_de_enquadramento.py
    purpose: >-
      Reproducao (o cabecalho ausente nas QUATRO rotas) e regressao (corpo da tela, ancoras de
      contrato e `content-length`).
    diff: fix/CHG-003.diff

closure:
  policy: local-software
  satisfied: true
resolution_kind: fixed
---

# Resposta sem protecao de enquadramento na pagina com acao destrutiva

## Summary

A resposta de `GET /` nao emite `X-Frame-Options` nem `Content-Security-Policy` com
`frame-ancestors`, e essa pagina contem o formulario da acao destrutiva:

```html
<form method="POST" class="m-0"
      onsubmit='return confirm("Apagar \"<nome>\"? ...");'>
  <input type="hidden" name="action" value="aposentar_arquivo">
  <input type="hidden" name="arquivo_a_aposentar" value="<nome armazenado>">
```

Medido: cabecalhos da resposta de `GET /` sao `content-length`, `content-type`, `date` e
`server: waitress` (nenhum cabecalho de enquadramento ou de politica). A acao de aposentar faz o
arquivo sair da lista do operador (sem apagar, conforme a `RN-14`), e nao ha nada na resposta que
impeça outra origem de enquadrar a pagina.

O `confirm()` do `onsubmit` aparece na janela enquadrada e pede confirmacao: e barreira de
interface e reduz o risco de clique unico acidental, mas nao e controle de servidor. E o
`BUG-20261013-Z5BC` mostra que a submissao em si nao e verificada por origem, entao os dois
defeitos se compoem.

## Expected Behavior

Nenhum artefato da spec efetiva preve cabecalho de enquadramento (`spec-gap`):

- `_reversa_sdd/openapi/index.yaml` contrata `GET /` como `200` e `text/html`, sem bloco de
  cabecalhos de seguranca.
- `_reversa_sdd/recursos-da-tela/contracts.md#1` lista os cabecalhos das rotas de arte
  (`Content-Type`, `ETag`) e nada de enquadramento.
- `_reversa_sdd/domain.md#4` descreve "abrir `/`" como renderizar a tela com as duas listas.
- `_reversa_sdd/permissions.md#3` cita como unico controle de borda declarado a recusa de escrita
  nas rotas de arte, feita pelo roteador com `405`.
- `_reversa_sdd/addenda/014-endurecimento-da-borda.md#a-lista-de-host-o-que-ela-defende-e-o-que-ela-não-é`
  declara que a recusa por `Host` cobre as rotas "inclusive o `POST` da acao destrutiva", e
  **nao** se apresenta como protecao de enquadramento nem de origem.

O projeto ja decidiu defender o vetor de **navegador** uma vez (o DNS rebinding, pelo `Host`).
O comportamento esperado e completar essa defesa: `X-Frame-Options: DENY` ou
`Content-Security-Policy: frame-ancestors 'none'` nas respostas da aplicacao.

## Actual Behavior

`src/app.py` nao emite cabecalho de enquadramento em lugar nenhum (nao ha `after_request` nem
cabecalho por rota); `src/templates/index.html:68-73` e o formulario da acao destrutiva, dentro da
unica tela do sistema.

## Steps to Reproduce

1. Subir o app em loopback.
2. `GET /` e inspecionar os cabecalhos de resposta, procurando `X-Frame-Options` e
   `Content-Security-Policy`.
3. (Nao executado nesta inspecao) abrir uma pagina local com `<iframe src="http://127.0.0.1:<porta>">`
   e observar se a aplicacao carrega dentro dela.

Passo a passo completo: `evidence/reproducao.md`.

## Evidence

- `evidence/estatico.json`: lista de cabecalhos ausentes e presenca do formulario destrutivo.
- `evidence/estatico-get-index.html`: HTML cru de `GET /`.
- `_reversa_bugs/seguranca/inspections/checklist-20261013/RESULTADOS-DO-CHECKLIST.md` item 6.

## Suspected Area

`src/app.py` (ponto unico onde um cabecalho de resposta entraria) e
`src/templates/index.html:68-73`.

## Acceptance Criteria

1. A resposta de `GET /` (e das demais rotas de HTML) traz `X-Frame-Options: DENY` ou
   `Content-Security-Policy` com `frame-ancestors 'none'`.
2. A defesa vale para todas as rotas que renderizam a tela, nao so para `/`.
3. Teste de regressao que falha se o cabecalho sumir.
4. O `confirm()` do botao de aposentar permanece: ele e defesa adicional, nao substituta.

## Traceability

| Item | Valor |
|---|---|
| Specs | `_reversa_sdd/openapi/index.yaml` (`GET /`), `_reversa_sdd/recursos-da-tela/contracts.md#1`, `_reversa_sdd/domain.md#4`, `_reversa_sdd/permissions.md#3`, `_reversa_sdd/addenda/014-endurecimento-da-borda.md#a-lista-de-host-o-que-ela-defende-e-o-que-ela-não-é` |
| Veredito preliminar | `spec-gap`: nenhum artefato preve cabecalho de enquadramento; o unico controle de borda especificado e a lista de `Host` |
| Codigo afetado | `src/app.py`, `src/templates/index.html:68-73` |
| Causa raiz | `confirmed` (2026-10-13): `src/app.py` nao emite cabecalho de enquadramento em lugar nenhum, e nenhuma spec previu um. Caminho causal e evidencias no bloco YAML desta seção; plano em `fix/plan.html` |
| Testes de reproducao | a escrever: nenhum teste le `X-Frame-Options` nem `Content-Security-Policy` |
| Testes existentes vizinhos | `tests/test_host_permitido.py::test_o_que_nao_esta_na_lista_e_recusado` e `::TestOAlcanceDaRecusa` (unicos que assertam cabecalho de seguranca, e so a recusa por `Host`) |

## Resolution

**Correcao aplicada e provada em 2026-10-13. O fechamento aguarda o veredito de spec (etapa 7),
que e decisao humana.**

### Causa raiz (final)

`confirmed` — `src/app.py` nao registrava `after_request` nem emitia cabecalho por rota, e nenhum
artefato da spec efetiva previu controle de enquadramento: **zero ocorrencias** de
`Content-Security-Policy`, `X-Frame-Options` e `frame-ancestors` em toda a `_reversa_sdd/`. O
caminho causal e as evidencias estao no bloco YAML desta secao.

### Correction Change Set aplicado

| CHG | Tipo | Artefato | Diff |
|---|---|---|---|
| CHG-001 | `code` | `src/app.py` | `fix/CHG-001.diff` |
| CHG-002 | `specification` | `_reversa_sdd/addenda/bug-BUG-20261013-X7EN-v001.md` | `fix/CHG-002.diff` |
| CHG-003 | `test` | `tests/test_cabecalho_de_enquadramento.py` | `fix/CHG-003.diff` |

### Testes: vermelho antes, verde depois

| Momento | Comando | Resultado | Evidencia |
|---|---|---|---|
| Gate 1, **antes** do change set | `pytest tests/test_cabecalho_de_enquadramento.py tests/test_nome_com_dois_pontos.py` | **8 falhas / 12 passes** — as 4 reproducoes do cabecalho (uma por rota) e as 4 do `:` | `fix/gate1-testes-falham.txt` |
| Gate 2, **depois** | o mesmo comando | **20 passes** | `fix/gate2-testes-passam.txt` |
| Regressao ampla | `pytest` (suite inteira) | **625 passam / 9 pulados / 0 falham** | `fix/gate2-suite.txt` |
| Paridade diferencial | `tests/rodar_paridade.py` | **100 %, zero divergencia, exit 0** | `fix/gate2-paridade.txt` |

O invariante `SHA_DA_TELA` de `tests/test_icone_de_atalho.py` **continua valido**: esta correcao e
de cabecalho, e nenhum byte do HTML mudou — que e exatamente o que o teste de regressao prende.

### Veredito de spec: recomendado `spec-gap` (aguardando confirmacao)

Nao existia spec de enquadramento, entao o adendo e **aditivo** e especifica o comportamento pela
primeira vez, sem fingir que emenda secao inexistente. Se o operador preferir
`spec-desatualizada`, muda a linha de veredito do adendo e o campo `spec_verdict`; o corpo do
adendo nao muda.

### O que NAO entrou, e por que

`Content-Security-Policy` (o defeito irmao `BUG-20261013-4PYJ`) e a verificacao de origem
(`BUG-20261013-Z5BC`) ficaram **fora desta sessao por decisao registrada**. O par fica incompleto
de proposito, e o adendo diz isso com todas as letras.


## Agent Notes

- **Correcao de uma linha, no lugar certo: um `after_request` ou o cabecalho junto do erro.** Nao
  vale a pena tocar template: o hash `SHA_DA_TELA` nao deve mudar por causa de cabecalho.
- **Nao medido: o enquadramento de verdade.** Nao houve teste com navegador. Se o fix quiser
  fechar com evidencia propria, o harness de paridade (`_reversa_sdd/parity/harness.py`) nao serve
  para isso: e comparacao de conteudo, nao de cabecalho de resposta.
- **Este bug e o irmao do `BUG-20261013-4PYJ`.** Um CSP unico resolve as duas metades
  (`frame-ancestors` e `default-src`), e e a correcao com melhor relacao custo-beneficio do
  conjunto. Se os dois forem corrigidos juntos, o adendo e um so.
- **Proposta de taxonomia:** `module` e `feature` ficaram `unclassified` porque o `taxonomy.yaml`
  nao tem valor para a borda de apresentacao. Proponho `module: apresentacao` e
  `feature: tela-de-entrada`. Decisao humana.

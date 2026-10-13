---
schema_version: 1
id: BUG-20261013-GTAY
display_number: 9
title: Falha de persistencia devolve o texto do driver do banco na pagina
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
    id: checklist-auditoria-reversa-analisador-genealogico.md#9
area: analisador-genealogico
module: dna-analysis
feature: analise-dna
labels: [seguranca, contrato-congelado, vazamento-de-detalhe-interno]

visibility: restricted
security_suspected: true

reproduction:
  classification: deterministic
  rate: "2/2"
  suspected_triggers: []

blocking: []

relationships: []

traceability:
  specs:
    - _reversa_sdd/analise-dna/contracts.md#6
    - _reversa_sdd/analise-dna/design.md#5
    - _reversa_sdd/domain.md#5.2
    - _reversa_sdd/domain.md#3.7
    - _reversa_sdd/openapi/index.yaml
    - _reversa_sdd/adrs/33-desfecho-em-tres-valores-e-projecao-pura.md#consequências
    - _reversa_sdd/addenda/008-persistencia-postgres-docker.md
  affected_code:
    - src/ports/adaptadores.py
    - src/application/dna_analysis.py
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

# Falha de persistencia devolve o texto do driver do banco na pagina

## Summary

Quando a gravacao do historico falha, o aviso nao bloqueante que a tela exibe carrega o **nome do
tipo da excecao e o texto inteiro do driver**. Medido nos dois estados possiveis do ambiente:

- **Driver ausente** (que e o estado real do `.venv/` do repositorio, divida `L-26`):
  `Historico nao registrado: o driver do banco nao esta instalado neste interpretador (No module named 'psycopg2').`
- **Driver presente e banco recusando** (medido com um duble sintetico declarado, porque o driver
  real nao esta instalado): `Historico nao registrado: OperationalError: connection to server at
  "127.0.0.1", port 5432 failed: FATAL: password authentication failed for user "analisador-sonda"`.

O segundo caso mostra o alcance: **host, porta e usuario do banco** na resposta HTTP. O texto e do
duble (valores inventados), mas o que a medicao prova e o formato do que a aplicacao repassa:
`f"Historico nao registrado: {type(erro).__name__}: {erro}"`.

O comportamento prescrito de fundo continua valendo e nao esta em causa: a `RN-13` exige que a
persistencia **nunca** bloqueie o resultado, e ela nao bloqueia.

## Expected Behavior

O aviso existe por contrato, e o **texto de erro dentro dele nao tem decisao registrada**:

- `_reversa_sdd/analise-dna/contracts.md#6` fixa os tres literais: `Historico nao registrado: o
  driver do banco nao esta instalado neste interpretador ({erro}).`, `... falha ao preparar os
  dados ({Tipo}: {msg}).` e `... {Tipo}: {msg}` para "banco fora ou erro de SQL".
- `_reversa_sdd/analise-dna/design.md#5` lista os dois primeiros como comportamento esperado.
- `_reversa_sdd/domain.md#5.2` repete os dois literais e `_reversa_sdd/domain.md#3.7` declara que
  "o texto `Historico nao registrado: ...` e o unico sinal que o operador tem".
- `_reversa_sdd/openapi/index.yaml` documenta `aviso_de_persistencia` no payload da resposta, com
  exemplo do literal do driver ausente.

A spec **prescreve o formato** (`{Tipo}: {msg}`) e **nunca avaliou o conteudo**: o que o driver
real coloca em `{msg}` (host, porta, usuario, as vezes nome da base) nao foi objeto de decisao, e o
duble medido mostra que a aplicacao repassa sem filtro. Do lado de seguranca, o esperado e a tela
dizer que o historico nao foi gravado e o operador poder agir (conferir o banco), sem publicar a
topologia nem o usuario do banco no HTML.

## Actual Behavior

`src/ports/adaptadores.py:294-314`:

```python
except Exception as erro:
    return None, f"Histórico não registrado: {type(erro).__name__}: {erro}"
```

O valor volta como `aviso_de_persistencia` em `ResultadoDeAnalise`
(`src/application/dna_analysis.py:271-291`) e o template o renderiza em
`src/templates/index.html:401-403` (`<div class="alerta-aviso" role="alert">`).

Nao ha filtro em nenhum dos tres pontos. O ramo do `ImportError`
(`src/ports/adaptadores.py:297-301`) tem o mesmo formato e ja publica o nome do modulo ausente.

## Steps to Reproduce

Caso 1 (driver ausente, estado real do `.venv/`):

1. Subir o app com `DATABASE_URL` apontando para um banco qualquer (valores inventados) e **sem**
   `psycopg2` instalado no interpretador.
2. `POST /` com `action=dna_analysis`, uma arvore sintetica e um CSV sintetico de matches.
3. Ler o bloco `aviso_de_persistencia` do HTML.

Caso 2 (driver presente e conexao recusada):

1. Subir o app com o mesmo `DATABASE_URL` e o `PYTHONPATH` apontando para o duble declarado
   `_reversa_bugs/_sondas-seguranca/stub/psycopg2/`.
2. Repetir a analise e ler o aviso.

Passo a passo completo: `evidence/reproducao.md`.

## Evidence

- `evidence/persistencia-sem-driver.json`: caso 1 (estado real do interpretador oficial).
- `evidence/persistencia-com-duble.json`: caso 2, com o texto do driver no aviso.
- `evidence/duble-psycopg2.py`: o duble, para conferencia (host, porta, usuario e base inventados).
- `_reversa_bugs/seguranca/inspections/checklist-20261013/RESULTADOS-DO-CHECKLIST.md` item 9.

## Suspected Area

`src/ports/adaptadores.py` (`RegistroDeAnalisesPostgres.registrar`, linha 311) e a projecao em
`src/application/dna_analysis.py`; o destino e `src/templates/index.html:401-403`.

## Acceptance Criteria

1. O aviso continua **nao bloqueante** e continua aparecendo uma unica vez (contrato da `RN-13` e
   dos testes de persistencia).
2. O aviso nao publica host, porta, usuario, nome de base, string de conexao nem o nome do modulo
   do driver. Uma frase propria dizendo que o historico nao foi gravado, com o detalhe no log.
3. Os literais de `analise-dna/contracts.md#6` e `domain.md#5.2` sao atualizados por adendo
   versionado, com decisao humana, antes da mudanca de texto.
4. Teste de regressao que falha se o corpo de uma resposta contiver `password`, `port`, `user` ou
   a `DATABASE_URL` de teste.

## Traceability

| Item | Valor |
|---|---|
| Specs | `_reversa_sdd/analise-dna/contracts.md#6`, `_reversa_sdd/analise-dna/design.md#5`, `_reversa_sdd/domain.md#5.2`, `_reversa_sdd/domain.md#3.7`, `_reversa_sdd/openapi/index.yaml` (`aviso_de_persistencia`), `_reversa_sdd/adrs/33-desfecho-em-tres-valores-e-projecao-pura.md#consequências` |
| Veredito preliminar | O **formato** e prescrito (`{Tipo}: {msg}`), o **conteudo** de `{msg}` nunca foi decidido. `spec_verdict` fica **nulo**: revogar ou emendar o literal e decisao humana |
| Codigo afetado | `src/ports/adaptadores.py:294-314`, `src/application/dna_analysis.py:271-291`, `src/templates/index.html:401-403` |
| Causa raiz | nao preenchida (o registro nao corrige) |
| Testes de reproducao | a escrever: nenhum teste asserta ausencia de detalhe do banco no corpo |
| Testes existentes vizinhos | `tests/test_persistencia_indisponivel.py::test_o_aviso_nao_bloqueante_aparece` (prende a presenca do prefixo), `::test_o_adaptador_nao_levanta_e_devolve_o_motivo_em_texto` (prende so `len(aviso) > 30`, o que na pratica protege a interpolacao), `tests/test_persistencia_desabilitada.py::test_a_analise_sai_igual_e_sem_aviso` (prende a ausencia) |

## Resolution

Nao preenchida. Este registro documenta e nao corrige; a correcao e do `/reversa-debugger-fix`.

## Agent Notes

- **Nao quebre a `RN-13`.** A tentacao de "resolver" isto deixando a excecao subir esta proibida
  pelo contrato: a analise ja foi calculada e o historico e beneficio, nunca condicao para ver o
  resultado. A correcao e de **texto**, nao de fluxo.
- **O `ImportError` tambem vaza, e de outro jeito.** O ramo de driver ausente publica
  `No module named 'psycopg2'` na tela, e ele e o caso que ocorre de fato no interpretador oficial
  hoje. Qualquer correcao precisa cobrir os dois ramos.
- **O gatilho do caso 2 e duble, e esta declarado.** Se o fix quiser medir o driver real, ele
  precisa do `psycopg2` no interpretador (divida `L-26`) ou do conteiner, e isso muda o ambiente
  da suite (`L-27`).
- **Contexto de dado pessoal.** `P-06` registra credencial em claro no `.env`; publicar host e
  usuario do banco na pagina de uma aplicacao que ja persiste dado de pessoas vivas (`L-29`)
  aumenta a superficie sem ganho para o operador.
- **Se o fix tocar a tela, o `SHA_DA_TELA` de `tests/test_icone_de_atalho.py` muda** e exige a
  declaracao prevista no proprio arquivo.

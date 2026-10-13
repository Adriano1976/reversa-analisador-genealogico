---
schema_version: 1
id: BUG-20261013-WREC
display_number: 8
title: Resposta de erro devolve o texto cru da excecao, com o caminho absoluto do servidor
status: open
phase: triaging
severity: high
priority: P1
created: 2026-10-13
updated: 2026-10-13

origin:
  type: inspection
  external_ref:
    provider: security-audit
    id: checklist-auditoria-reversa-analisador-genealogico.md#8
area: analisador-genealogico
module: upload
feature: upload-gedcom
labels: [seguranca, contrato-congelado, divida-declarada-E-01, vazamento-de-detalhe-interno]

visibility: restricted
security_suspected: true

reproduction:
  classification: deterministic
  rate: "1/1"
  suspected_triggers: []

blocking: []

relationships:
  - bug: BUG-20261013-GTAY
    type: related-to
    state: supported
    evidence:
      - ref: _reversa_bugs/seguranca/inspections/checklist-20261013/RESULTADOS-DO-CHECKLIST.md
        observation: >-
          Mesma classe e mesma causa: um literal de tela interpola o texto de uma excecao vinda de
          fora do dominio. Aqui o caminho absoluto do sistema de arquivos; la o texto do driver do
          banco.

traceability:
  specs:
    - _reversa_sdd/upload-gedcom/contracts.md#6
    - _reversa_sdd/upload-gedcom/design.md#5
    - _reversa_sdd/domain.md#5.1
    - _reversa_sdd/analise-dna/contracts.md#6
    - _reversa_sdd/busca-caminho/contracts.md#6
    - _reversa_sdd/addenda/014-endurecimento-da-borda.md#o-que-não-mudou-e-por-que
    - _reversa_sdd/addenda/014-endurecimento-da-borda.md#dívidas-declaradas-não-fechadas
  affected_code:
    - src/app.py
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

# Resposta de erro devolve o texto cru da excecao, com o caminho absoluto do servidor

## Summary

Os tres `except Exception` de ultimo recurso da rota interpolam o texto da excecao no HTML
devolvido ao navegador. A medicao provocou um erro de sistema de arquivos no ramo de envio e a
resposta 200 trouxe, no corpo:

```
Erro ao processar GEDCOM: [Errno 13] Permission denied:
'C:\Users\venda\AppData\Local\Temp\dsh-cvAZP4\reversa-chec-seg\uploads\7b682362af68f7c0__sonda_dir.ged'
```

Ou seja: o `errno` cru do sistema operacional, o texto do sistema (`Permission denied`) e o
**caminho absoluto da pasta de upload**, que carrega o nome de usuario da sessao do sistema. Quem
alcanca a aplicacao pelo navegador recebe a geografia do servidor sem pedir.

**Este vazamento e comportamento declarado.** A revisao adversarial que originou o adendo
`014-endurecimento-da-borda` propos trocar as duas mensagens por uma frase generica, e a decisao
registrada foi manter os literais intactos, porque sao contrato congelado. A divida esta nomeada
no proprio adendo como **`E-01`**. Este registro nao reabre a decisao: ele guarda a **ocorrencia
medida** (que o `{e}` carrega caminho absoluto e nome de usuario, e nao apenas um texto generico)
e a consequencia de seguranca que a decisao de 2026-10-11 nao avaliou.

## Expected Behavior

Comportamento **prescrito**, e por isso o defeito precisa de decisao humana, nao de edicao
pontual:

- `_reversa_sdd/upload-gedcom/contracts.md#6` fixa o literal `"Erro ao processar GEDCOM: {e}"`.
- `_reversa_sdd/upload-gedcom/design.md#5` repete o mesmo no fluxo alternativo.
- `_reversa_sdd/domain.md#5.1`, `_reversa_sdd/analise-dna/contracts.md#6` (`BR-D-93`) e
  `_reversa_sdd/busca-caminho/contracts.md#6` (`BR-C-65`) fixam o irmao `"Ocorreu um erro: {e}"`.
- `_reversa_sdd/addenda/014-endurecimento-da-borda.md#o-que-não-mudou-e-por-que` diz, com todas
  as letras: *"O vazamento de `{e}` e, portanto, comportamento declarado, nao um defeito que
  passou. Quem quiser muda-lo precisa de uma decisao que revogue os literais nos tres contratos,
  e nao de uma edicao pontual."*
- `_reversa_sdd/addenda/014-endurecimento-da-borda.md#dívidas-declaradas-não-fechadas` registra
  `E-01` com gravidade 🟡.

O comportamento esperado, do lado de seguranca, e o que o proprio adendo descreve como objetivo
da revisao: **o operador le uma frase que diz o que aconteceu, e o detalhe tecnico fica no log**
(o item 4 do mesmo adendo ja fez a metade do log com `app.logger.exception`). O que falta e a
metade do texto.

## Actual Behavior

`src/app.py:533-538`:

```python
except Exception as e:
    app.logger.exception("falha inesperada no envio de GEDCOM")
    return render_template("index.html", message=f"Erro ao processar GEDCOM: {e}", success=False)
```

O mesmo padrao esta em `src/app.py:678-680` (analise de DNA, `Ocorreu um erro: {e}`) e em
`src/app.py:707-710` (busca de caminho, idem). A medicao exercitou o ramo de envio; os outros dois
sao o mesmo texto de codigo em outro ramo.

O gatilho medido foi um caso de sistema de arquivos: um **diretorio** ocupando o nome armazenado
esperado (`<chave>__sonda_dir.ged`). A guarda de existencia de `guardar`
(`src/ports/adaptadores.py:84`) pula a gravacao e a releitura da arvore tenta abrir um diretorio
com o parser. Nao e preciso um arquivo malformado: o GEDCOM truncado (`0 HEAD` sem `TRLR`) foi
**aceito** pelo `ged4py` e respondeu `carregado!`, ou seja, o vazamento exige uma falha que nao
seja de dominio (erro de sistema de arquivos, por exemplo).

## Steps to Reproduce

1. Subir o app com a pasta de upload desviada para um diretorio temporario e dados sinteticos.
2. Calcular a chave de conteudo da fixture: `sha256("arvore_valida.ged")[:16]` = `7b682362af68f7c0`.
3. Criar um **diretorio** `<pasta-de-upload>/7b682362af68f7c0__sonda_dir.ged`.
4. `POST /` com `action=upload_gedcom`, `filename="sonda_dir.ged"` e o conteudo da fixture.
5. Ler o corpo da resposta 200.

Passo a passo completo: `evidence/reproducao.md`.

## Evidence

- `evidence/erro.json`: mensagens extraidas da resposta e o texto de excecao na pagina.
- `evidence/erro-diretorio-no-lugar-do-arquivo.html`: HTML cru da resposta, com o caminho
  absoluto no corpo.
- `_reversa_bugs/seguranca/inspections/checklist-20261013/RESULTADOS-DO-CHECKLIST.md` item 8.

## Suspected Area

`src/app.py`, os tres `except Exception` de ultimo recurso (`:533-538`, `:678-680`, `:707-710`).
A origem do texto esta fora do projeto (`os`, `ged4py`, `psycopg2`); o que o projeto decide e o
que faz com ele.

## Acceptance Criteria

1. Decisao humana registrada sobre os quatro literais (`upload-gedcom/contracts.md#6`,
   `domain.md#5.1`, `analise-dna/contracts.md#6`, `busca-caminho/contracts.md#6`), em adendo
   versionado, antes de qualquer alteracao de texto.
2. Se a decisao for revogar: nenhuma resposta HTTP carrega caminho de sistema de arquivos, nome de
   usuario do sistema, `errno` cru ou texto de biblioteca; o rastro tecnico continua no log.
3. Se a decisao for manter: fica registrado, no mesmo adendo, que o caminho absoluto do servidor e
   parte do contrato de tela, e o `E-01` sobe de gravidade com a ocorrencia medida anexada.
4. Teste de regressao que falha se um caminho de arquivo do servidor aparecer no corpo de uma
   resposta, independentemente do ramo que o produziu.

## Traceability

| Item | Valor |
|---|---|
| Specs | `_reversa_sdd/upload-gedcom/contracts.md#6`, `_reversa_sdd/upload-gedcom/design.md#5`, `_reversa_sdd/domain.md#5.1`, `_reversa_sdd/analise-dna/contracts.md#6`, `_reversa_sdd/busca-caminho/contracts.md#6`, `_reversa_sdd/addenda/014-endurecimento-da-borda.md#o-que-não-mudou-e-por-que` |
| Veredito preliminar | O literal e **contrato congelado**, e o adendo 014 declara o vazamento como comportamento aceito (`E-01`). `spec_verdict` fica **nulo**: revogar o literal e decisao humana |
| Codigo afetado | `src/app.py:533-538`, `:678-680`, `:707-710` |
| Causa raiz | nao preenchida (o registro nao corrige) |
| Testes de reproducao | a escrever: nenhum teste atual asserta ausencia de caminho do servidor no corpo |
| Testes existentes vizinhos | `tests/test_traducao_de_erros.py` (prende o prefixo `Ocorreu um erro: ` com `{e}` para as tres excecoes de DNA), `tests/test_upload_seguranca.py::TestExtensaoPreservada::test_fluxo_completo_de_analise_de_dna` (`"Ocorreu um erro" not in texto` no caminho feliz) |

## Resolution

Nao preenchida. Este registro documenta e nao corrige; a correcao e do `/reversa-debugger-fix`,
e ela depende da decisao humana sobre os literais.

## Agent Notes

- **Nao "conserte" este bug com uma edicao pontual.** Trocar `f"... {e}"` por uma frase fixa em um
  ramo quebra a paridade de tela e contraria o `T019` da `_reversa_forward/006/actions.md`, que
  manda manter o `except Exception` de ultimo recurso com o literal intacto. O caminho e adendo.
- **A ocorrencia medida e mais forte do que a divida registrada.** O `E-01` fala em "mostrar `{e}`
  ao operador"; o que se mediu e um caminho absoluto com nome de usuario. Se a decisao for manter,
  a descricao do `E-01` deve mudar para refletir isso.
- **Nao confundir com `RN-21`.** O caminho de GEDCOM ilegivel na referencia **ja** tem frase
  propria e fixa (`_arvore_do_formulario`, `src/app.py:306-316`), com o traceback no log. Este bug
  e o que sobra fora dessa guarda.
- **Se o fix tocar a tela, o `SHA_DA_TELA` de `tests/test_icone_de_atalho.py` muda** e precisa da
  declaracao prevista no proprio arquivo (o hash e invariante mantido a mao).
- **Sem proposta de taxonomia nova:** o ramo medido e `module: upload`; os outros dois irmaos do
  mesmo padrao vivem em `dna-analysis` e `path-search`, e estao citados em `affected_code` por
  arquivo.

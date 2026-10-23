---
schema_version: 1
id: OPP-20261023-DEAD
verb: prune
state: applied
safety_net:
  kind: existing
  green_before: true
  green_after: true
preservation:
  method: death-proof
  evidence:
    - before-after/prova-de-inalcancabilidade.txt
    - before-after/suite-antes.txt
    - before-after/suite-depois.txt
measurement:
  before: "index(): 6 linhas em duas guardas consecutivas, com comentario declarando o segundo ramo inalcancavel"
  after: "index(): 2 linhas em uma guarda unica, com o mesmo estreitamento de tipo"
change_set:
  - chg: CHG-001
    file: src/app.py
    purpose: unifica as duas guardas de `_arvore_do_formulario` em uma unica condicao
approval:
  by: user
  at: 2026-10-23T03:08:01-03:00
reversible_via: [CHG-001-guarda-unificada.diff]
---

# Transformacao: OPP-20261023-DEAD (guarda inalcancavel da arvore)

## O que mudou

Em `src/app.py`, dentro de `index()`, as duas guardas consecutivas de
`_arvore_do_formulario()` viraram uma:

```python
# antes
if erro is not None:
    return render_template("index.html", message=erro, success=False)
if arvore is None:
    # Inalcancavel em execucao: `erro` e `arvore` sao preenchidos juntos.
    # Existe para o checador de tipos estreitar a uniao do retorno.
    return render_template("index.html", message="Erro: Arquivo GEDCOM não encontrado.", success=False)

# depois
if erro is not None or arvore is None:
    return render_template("index.html", message=erro or "Erro: Arquivo GEDCOM não encontrado.", success=False)
```

O ramo de renderizacao que era inalcancavel saiu. A comparacao `arvore is None`
**permaneceu** dentro da condicao unica, porque e ela que estreita o tipo para o
checador: a docstring da propria funcao declara que `erro is not None` nao
estreita o segundo elemento da tupla. Prova em
[prova-de-inalcancabilidade.txt](before-after/prova-de-inalcancabilidade.txt).

## O que esta transformacao NAO fez

Nao removeu a checagem `arvore is None`, apesar do titulo da oportunidade. O que
era morto era a **resposta** daquele ramo (uma segunda mensagem de erro com o
mesmo texto-base); a condicao continua necessaria para o tipo. O valor devolvido
para qualquer entrada observavel e o mesmo de antes.

## Reversibilidade

`CHG-001-guarda-unificada.diff` foi reconstruido a partir do `HEAD 221b6c1` e
**verificado por aplicacao em cadeia**: DEAD, depois ASST, depois DISP reproduzem
o `src/app.py` atual byte a byte. A verificacao esta descrita no README do
registro, secao do lote de 2026-10-23.

O `proposed.diff` que existia neste diretorio foi absorvido por `CHG-001` e
removido, para nao deixar dois diffs concorrentes do mesmo hunk.

## Rede de seguranca

A suite foi medida nesta sessao, nas duas pontas reais do lote (ver
[suite-antes.txt](before-after/suite-antes.txt) e
[suite-depois.txt](before-after/suite-depois.txt)):

| Momento | Resultado |
|---|---|
| linha de base HEAD 221b6c1 | 1615 passed, 9 skipped |
| working tree depois do lote | 1615 passed, 9 skipped |

Os arquivos de suite herdados da sessao interrompida foram substituidos: eles
declaravam `Python 3.12.3`, `pytest 8.3.2` e `configfile: pyproject.toml`, e este
projeto nao tem `pyproject.toml` nem usa esse interpretador. Nao eram evidencia
deste ambiente.

## Aprovacao

O horario acima e o da gravacao em disco do `src/app.py` transformado. A sessao
interrompida nao deixou registro de gate em artefato para esta transformacao; a
conciliacao de 2026-10-23 apenas reconstruiu e verificou o diff.

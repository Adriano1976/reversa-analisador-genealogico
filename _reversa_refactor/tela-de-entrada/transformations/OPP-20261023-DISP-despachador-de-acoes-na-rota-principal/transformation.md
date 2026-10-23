---
schema_version: 1
id: OPP-20261023-DISP
verb: restructure
state: applied
safety_net:
  kind: existing
  green_before: true
  green_after: true
preservation:
  method: tests
  evidence:
    - before-after/suite-antes.txt
    - before-after/suite-depois.txt
measurement:
  before: "index(): 234 linhas, cascata de cinco ramos `if` com parsing de formulario, caso de uso, try/except e render_template repetidos"
  after: "index(): 19 linhas de despacho; cinco handlers dedicados; dois mapas de acao (`_ACOES_PRE_ARVORE` e `_ACOES_COM_ARVORE`)"
change_set:
  - chg: CHG-001
    file: src/app.py
    purpose: extrai as cinco acoes para handlers e troca a cascata de `if` por dois mapas de despacho
approval:
  by: user
  at: 2026-10-23T03:08:01-03:00
reversible_via: [CHG-001-despachador-de-acoes.diff]
---

# Transformacao: OPP-20261023-DISP (Action Dispatcher na rota principal)

## O que mudou

`index()` deixou de ser um corpo de 234 linhas e passou a ser um despachante de 19:

```python
@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        action = request.form.get("action")
        handler_pre = _ACOES_PRE_ARVORE.get(action)
        if handler_pre:
            return handler_pre()

        gedcom_filename, arvore, erro = _arvore_do_formulario()
        if erro is not None or arvore is None:
            return render_template("index.html", message=erro or "Erro: Arquivo GEDCOM não encontrado.", success=False)
        all_names = nomes_de_exibicao(arvore)

        handler_arvore = _ACOES_COM_ARVORE.get(action)
        if handler_arvore:
            return handler_arvore(gedcom_filename, arvore, all_names)

    return render_template("index.html")
```

Os cinco handlers ficam no mesmo modulo, na ordem em que eram ramos:
`_acao_upload_gedcom`, `_acao_aposentar_arquivo`, `_acao_selecionar_arvore`,
`_acao_dna_analysis` e `_acao_path_search`.

## Por que dois mapas, e nao um

A ordem dos ramos era regra, nao estilo: `upload_gedcom` e `aposentar_arquivo`
precisam rodar **antes** de `_arvore_do_formulario()`. No caso de
`aposentar_arquivo` a razao e medida: a funcao resolve e parseia a arvore
escolhida, e a arvore escolhida pode ser exatamente a que se esta aposentando;
depois do move, o parse falharia e o operador leria "arquivo nao existe mais" no
lugar da confirmacao. Separar em `_ACOES_PRE_ARVORE` e `_ACOES_COM_ARVORE`
preserva essa precedencia de forma explicita, sem comentario defensivo.

## Equivalencia de comportamento

| Situacao | Antes | Depois |
|---|---|---|
| `action` desconhecida | cai no `return render_template("index.html")` do fim | cai no mesmo `return`, porque `dict.get` devolve `None` |
| `action` pre-arvore | executa antes do parse da arvore | identico, pelo primeiro mapa |
| `action` com arvore ausente | `erro` preenchido, renderiza com `success=False` | identico |
| excecao de cliente (`HTTPException`) | `raise` | identico, dentro do handler |
| erro inesperado | `app.logger.exception` + mensagem | identico |

Os literais de mensagem, as chaves de contexto e os `try/except` foram
transportados sem reescrita. O unico texto novo e o fallback
`"Erro: Arquivo GEDCOM não encontrado."`, que ja era o da guarda unificada pela
`OPP-20261023-DEAD` e nunca e alcancado quando `erro` e nulo.

## O `proposed.diff` anterior era um esboco

O arquivo `proposed.diff` que a sessao interrompida deixou tinha reticencias no
lugar do corpo (`... (230 linhas procedurais)`) e nao aplicava. Ele foi removido e
substituido por `CHG-001-despachador-de-acoes.diff`, gerado do `HEAD 221b6c1` e
verificado em cadeia com DEAD e ASST: os tres diffs, aplicados nessa ordem,
reproduzem o `src/app.py` atual byte a byte.

O `plan.md` deste diretorio declarava o alvo em "linhas 415-645" e a oportunidade
em "560-792". Nenhuma das duas e a linha de base: no `HEAD 221b6c1`, `index()`
comeca na linha 561 e termina na 794. O plano foi corrigido no ponto de alvo e
recebeu nota de execucao; o corpo original foi preservado.

## Rede de seguranca

| Momento | Resultado |
|---|---|
| linha de base HEAD 221b6c1 | 1615 passed, 9 skipped |
| working tree depois do lote | 1615 passed, 9 skipped |

Medicao do lote combinado; ver [suite-antes.txt](before-after/suite-antes.txt) e
[suite-depois.txt](before-after/suite-depois.txt). A suite cobre as cinco acoes
por rota, incluindo `tests/test_csv_de_descartes.py`,
`tests/test_cartao_em_tres_faixas.py`, `tests/test_endogamia.py` e os testes de
persistencia e de tela que passam por `index()`.

## Aprovacao e lacuna de registro

O horario acima e o da gravacao em disco do `src/app.py` transformado. Esta
transformacao foi a unica do lote que parou **sem registro nenhum**: nao existia
`transformation.md`, o indice ainda a marcava `proposed`, e o unico artefato era o
esboco de diff. A conciliacao de 2026-10-23 reconstruiu o diff, mediu a suite real
e fechou o registro. Nao ha, portanto, captura do gate original: ha a prova de
que o estado aplicado preserva o comportamento.

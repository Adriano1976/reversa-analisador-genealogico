---
schema_version: 1
id: OPP-20261023-DISP
display_number: 39
context: tela-de-entrada
verb: restructure
title: Monolito da rota principal index com switch de action substituível por Action Dispatcher
target:
  files: [src/app.py]
  symbol: index (linhas 561-794 na linha de base HEAD 221b6c1)
smell: >
  A funcao index() acumula 232 linhas contendo 5 acoes distintas de negocio
  (upload_gedcom, aposentar_arquivo, selecionar_arvore, dna_analysis, path_search)
  em uma cascata de if/elif baseada em request.form.get("action"). Cada bloco
  mistura parsing de formulario, invocacao de casos de uso, tratamento de excecoes
  e renderizacao de template.
roi:
  confidence: green
  impact: >
    Introduz o padrao de projeto Action Dispatcher / Command. Cada acao passa a ter
    seu handler isolado, com alta coesao e baixo acoplamento. A funcao index()
    fica enxuta (~20 linhas), apenas delegando o despacho da acao.
  cost: medium
  est_return: >
    index() reduzida de 232 para ~20 linhas. Cada acao em funcao ou classe handler dedicada.
state: applied
promoted_to: null
traceability:
  soul: []
  specs:
    - _reversa_sdd/tela-de-entrada/design.md
    - _reversa_sdd/adrs/25-fronteira-de-aplicacao-portas.md
---

## Antes observado

Em `src/app.py:560-792`, a rota `index` opera como um despachador procedural longo:

```python
@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        action = request.form.get("action")
        if action == "upload_gedcom":
            ...
        if action == "aposentar_arquivo":
            ...
        gedcom_filename, arvore, erro = _arvore_do_formulario()
        ...
        if action == "selecionar_arvore":
            ...
        if action == "dna_analysis":
            ...
        if action == "path_search":
            ...
    return render_template("index.html")
```

Cada ramo repete tratamento de erros (`ErroDeDominio`, `HTTPException`, `Exception`),
monta parametros complexos e chama `render_template`.

## Transformação proposta

Implementar o padrao Action Dispatcher com handlers especializados para cada acao:

```python
ACTION_HANDLERS = {
    "upload_gedcom": lidar_com_upload_gedcom,
    "aposentar_arquivo": lidar_com_aposentar_arquivo,
    "selecionar_arvore": lidar_com_selecionar_arvore,
    "dna_analysis": lidar_com_dna_analysis,
    "path_search": lidar_com_path_search,
}
```

A rota `index` se torna um despachante limpo e extensivel.

## Rede de segurança

A suite existente cobre exaustivamente todas as acoes da rota `index` atraves de
`tests/test_cartao_em_tres_faixas.py`, `tests/test_csv_de_descartes.py`,
`tests/test_endogamia.py`, `tests/test_confrontacao_gedcom_dna.py` e testes de integracao.

## Registro de aplicação (2026-10-23)

Aplicada em `src/app.py`. `index()` passou de 234 para 19 linhas; as cinco acoes
viraram handlers dedicados, e a precedencia pre-arvore ficou explicita em dois
mapas de acao (`_ACOES_PRE_ARVORE` e `_ACOES_COM_ARVORE`).

- Transformacao: `transformations/OPP-20261023-DISP-despachador-de-acoes-na-rota-principal/transformation.md`
- Diff de reversao: `.../CHG-001-despachador-de-acoes.diff`
- Suite: 1615 passed, 9 skipped na linha de base HEAD 221b6c1 e 1615 passed,
  9 skipped depois do lote.

O `proposed.diff` que a sessao interrompida deixou era um esboco com reticencias,
nao um diff aplicavel; foi substituido pelo diff real, verificado por aplicacao em
cadeia com as transformacoes DEAD e ASST.

---
*Gerado pelo Reversa-Refactor em 2026-10-23.*

---
schema_version: 1
id: OPP-20261023-DEAD
display_number: 43
context: tela-de-entrada
verb: prune
title: Remoção de verificação inalcançável de arvore is None na rota principal
target:
  files: [src/app.py]
  symbol: index (linhas 622-625)
smell: >
  A rota index() possui uma verificacao defensiva if arvore is None que o proprio
  comentario declara como "Inalcancavel em execucao: erro e arvore sao preenchidos juntos".
  A funcao _arvore_do_formulario() garante que se erro is None, arvore e um objeto valido.
roi:
  confidence: green
  impact: >
    Remove codigo inalcancavel comprovado e simplifica o fluxo de guarda de entrada.
  cost: low
  est_return: >
    Remocao de 4 linhas de codigo morto com prova de inalcancabilidade.
state: applied
promoted_to: null
traceability:
  soul: []
  specs:
    - _reversa_sdd/tela-de-entrada/requirements.md
---

## Antes observado

Em `src/app.py:619-626`:

```python
        gedcom_filename, arvore, erro = _arvore_do_formulario()
        if erro is not None:
            return render_template("index.html", message=erro, success=False)
        if arvore is None:
            # Inalcancavel em execucao: `erro` e `arvore` sao preenchidos juntos.
            # Existe para o checador de tipos estreitar a uniao do retorno.
            return render_template("index.html", message="Erro: Arquivo GEDCOM não encontrado.", success=False)
        all_names = nomes_de_exibicao(arvore)
```

## Transformação proposta

Remover a guarda inalcancavel utilizando tipagem formal ou `assert arvore is not None` para o checador
de tipos, eliminando o ramo morto:

```python
        gedcom_filename, arvore, erro = _arvore_do_formulario()
        if erro is not None or arvore is None:
            return render_template("index.html", message=erro or "Erro: Arquivo GEDCOM não encontrado.", success=False)
        all_names = nomes_de_exibicao(arvore)
```

## Prova de inalcançabilidade

A funcao `_arvore_do_formulario()` possui apenas 3 caminhos de retorno:
1. `return None, None, "Erro: Arquivo GEDCOM não encontrado."`
2. `return None, None, ("Erro: o arquivo... não pôde ser lido...")`
3. `return None, None, f"Erro: Arquivo... não existe mais."`
4. `return referencia, arvore, None`

Quando `erro is None`, a execucao obrigatoriamente veio do caminho 4, onde `arvore` e um objeto valido.

---
*Gerado pelo Reversa-Refactor em 2026-10-23.*

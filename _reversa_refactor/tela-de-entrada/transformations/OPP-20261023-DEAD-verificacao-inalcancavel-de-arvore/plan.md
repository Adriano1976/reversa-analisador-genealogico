# Plano de Transformação: OPP-20261023-DEAD

- **ID**: OPP-20261023-DEAD (#43)
- **Especialista**: prune
- **Alvo**: `src/app.py` (função `index()`, linhas 619-625 na linha de base HEAD 221b6c1)
- **Objetivo**: Eliminar bloco inalcançável `if arvore is None` que duplica render_template com código morto comprovado.

## Análise de Inalcançabilidade

A função `_arvore_do_formulario()` possui a assinatura `tuple[str | None, object | None, str | None]`.
Em todos os seus 4 caminhos de retorno:
1. `return None, None, "Erro: Arquivo GEDCOM não encontrado."`
2. `return None, None, ("Erro: o arquivo... não pôde ser lido...")`
3. `return None, None, f"Erro: Arquivo... não existe mais."`
4. `return referencia, arvore, None`

Se `erro is not None`, a função entra na guarda da linha 620 e retorna o erro para a tela.
Logo, após `if erro is not None:`, a variável `arvore` é necessariamente um objeto válido.
O bloco subsequente `if arvore is None:` nunca é executado em tempo de execução, servindo apenas para estreitamento de tipo.

## Modificação Proposta

Unificar a checagem em uma guarda única concisa:
```python
        gedcom_filename, arvore, erro = _arvore_do_formulario()
        if erro is not None or arvore is None:
            return render_template("index.html", message=erro or "Erro: Arquivo GEDCOM não encontrado.", success=False)
        all_names = nomes_de_exibicao(arvore)
```

Isso elimina o código morto inalcançável, reduz duplicações e mantém a garantia estática do verificador de tipos sem alterar nenhum comportamento funcional da rota.

## Execução (2026-10-23)

Transformação aplicada. O diff real está em `CHG-001-guarda-unificada.diff`, com o
hunk em 617-628 do `HEAD 221b6c1`. O `proposed.diff` original foi absorvido por
ele e removido.

Ressalva registrada no `transformation.md`: o ramo de renderização morto saiu, mas
a condição `arvore is None` continua dentro da guarda única, porque é ela que
estreita o tipo — a docstring de `_arvore_do_formulario` declara que
`erro is not None` não estreita o segundo elemento da tupla.

A suíte real foi medida nas duas pontas do lote nesta sessão: 1615 passed,
9 skipped antes e depois.

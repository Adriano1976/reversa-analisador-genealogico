"""Qual forma de `{% if %}` deixa a tela de ENTRADA byte a byte igual?

O bloco de observacoes do arquivo entra no meio de `#results-area`, entre a guarda
de `aviso_de_persistencia` e a guarda de `dna_results`. Na tela de ENTRADA as duas
sao falsas, mas o texto literal entre as tags continua sendo emitido — e o hash
dessa pagina e contrato congelado (`tests/test_icone_de_atalho.py`, `SHA_DA_TELA`).

Medido: com o comentario e o `if` sem controle de whitespace, a entrada ganha
linhas em branco. Esta sonda descobre a combinacao neutra, em vez de tentar
adivinhar — o `-` do Jinja age no texto literal imediatamente antes ou depois da
tag, e o efeito de cada um nao e obvio quando ha um comentario no meio.

Uso: .\\.venv\\Scripts\\python.exe _reversa_bugs\\_sondas-matching\\whitespace_jinja.py
"""

import jinja2

ENV = jinja2.Environment(undefined=jinja2.Undefined)

# `§` e `¶` evitam escapes de chave dentro das f-strings.
ABRE, FECHA = "\x7b%", "%\x7d"


def _tag(conteudo):
    return ABRE + conteudo + FECHA


BASE = (
    "                <div id=\"results-area\">\n"
    "                    " + _tag(" if aviso_de_persistencia ") + "\n"
    "                        <div>x</div>\n"
    "                    " + _tag(" endif ") + "\n"
    "                    " + _tag(" if dna_results ") + "\n"
    "                        <h2>r</h2>\n"
    "                    " + _tag(" endif ") + "\n"
    "                </div>\n"
)

CORPO = (
    "                        <div class=\"bloco\">conteudo</div>\n"
    "                    " + _tag("- endif") + "\n"
)

COMENTARIO = "                    {#%s c %s#}\n"


def montar(dash_comentario_abre, dash_comentario_fecha, dash_if, dash_fim, dash_if_final):
    return (
        "                <div id=\"results-area\">\n"
        "                    " + _tag(" if aviso_de_persistencia ") + "\n"
        "                        <div>x</div>\n"
        "                    " + _tag(" endif ") + "\n"
        + COMENTARIO % (dash_comentario_abre, dash_comentario_fecha)
        + "                    " + ABRE + dash_if + " if observacoes_do_arquivo " + FECHA + "\n"
        + CORPO
        + "                    " + ABRE + dash_if_final + " if dna_results " + FECHA + "\n"
        "                        <h2>r</h2>\n"
        "                    " + _tag(" endif ") + "\n"
        "                </div>\n"
    )


def main():
    esperado = ENV.from_string(BASE).render()
    print(f"referencia (sem o bloco): {len(esperado)} bytes")
    print()
    # (abre, fecha, dash_if, dash_fim, dash_if_final)
    variantes = {
        "sem dash nenhum":                 ("", "", "", "-", ""),
        "comentario com dash dos dois lados": ("-", "-", "", "-", ""),
        "comentario abre + if com dash":   ("-", "", "-", "-", ""),
        "comentario fecha + if com dash":  ("", "-", "-", "-", ""),
        "tres dashes (abre, fecha, if)":   ("-", "-", "-", "-", ""),
        "if com dash, sem dash no comentario": ("", "", "-", "-", ""),
    }
    for nome, argumentos in variantes.items():
        texto = montar(*argumentos)
        try:
            saida = ENV.from_string(texto).render()
        except jinja2.TemplateSyntaxError as erro:
            print(f"  {nome:<38} ERRO DE SINTAXE: {erro}")
            continue
        delta = len(saida) - len(esperado)
        marca = "NEUTRA" if saida == esperado else f"delta {delta:+d} bytes"
        print(f"  {nome:<38} {marca}")

    print()
    print("A variante neutra e a que pode ser usada sem tocar em `SHA_DA_TELA`.")


if __name__ == "__main__":
    main()

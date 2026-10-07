"""T011 — varredura de forma do dono no codigo de producao.

## Por que uma varredura, e nao um teste de execucao

A `RF-03` exige que nenhum chamador "invente um valor no proprio local", e a
`RF-04` exige que a constante de dono seja **unica** e que o lugar onde ela vive
**declare** que nao ha isolamento e que a divida #3 nao e tratada.

Nenhuma das duas coisas e observavel em execucao. Passar `DONO_DO_PROCESSO` ou o
literal `"unico"` produz **exatamente o mesmo comportamento** — a chave vem do
conteudo, e o dono nao participa de decisao nenhuma. Um teste de execucao mediria
o resultado, que e igual nos dois casos, e passaria verde sobre a violacao.

E o mesmo motivo pelo qual a feature 006 precisou do `_t020_varredura.py`.

## O que ele mede

1. **Todos os chamadores passam o dono.** Toda chamada de producao a `guardar`,
   `resolver` ou `carregar` tem de passar, na ultima posicao ou por palavra-chave,
   uma expressao que **nao seja literal**. Um `"unico"` escrito no local reprova.
2. **A contagem de chamadores e a esperada.** Sao **5** hoje. A contagem entra
   como asserção porque uma lacuna na enumeracao dos chamadores ja custou uma
   rodada nesta feature: a decomposicao contou os chamadores de `guardar` e de
   `resolver`, nao contou os de `carregar`, e o `upload_gedcom` ficou de fora — 11
   testes falharam. Acrescentar um chamador novo obriga a revisar o dono dele.
3. **A constante de dono e unica.** Exatamente **uma** atribuicao de modulo cujo
   nome contem `DONO`, em `src/app.py`.
4. **O lugar declara o que a `RF-04` exige.** O bloco de comentario imediatamente
   acima da constante nomeia a ausencia de isolamento e a **divida #3**.

Uso:

    .venv\\Scripts\\python.exe _t011_varredura.py

Sai 0 quando as quatro coisas valem, 1 caso contrario. A saida vai para
`T011-varredura.txt`.
"""
from __future__ import annotations

import ast
import io
import os
import sys

FEATURE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
EVIDENCIA = os.path.join(FEATURE, "evidence", "T011-varredura.txt")
PROJETO = os.path.dirname(os.path.dirname(FEATURE))
SRC = os.path.join(PROJETO, "src")

METODOS_DE_PORTA = ("guardar", "resolver", "carregar")
CHAMADORES_ESPERADOS = 5


def arquivos_de_producao() -> list[str]:
    encontrados = []
    for raiz, _, nomes in os.walk(SRC):
        for nome in sorted(nomes):
            if nome.endswith(".py"):
                encontrados.append(os.path.join(raiz, nome))
    return sorted(encontrados)


def chamadas_de_porta(arvore: ast.AST):
    """Todas as chamadas `algo.metodo(...)` com metodo de porta."""
    for no in ast.walk(arvore):
        if not isinstance(no, ast.Call):
            continue
        func = no.func
        if isinstance(func, ast.Attribute) and func.attr in METODOS_DE_PORTA:
            yield no


def expressao_do_dono(chamada: ast.Call) -> ast.expr | None:
    """A expressao passada como dono, por palavra-chave ou na ultima posicao."""
    for palavra, valor in chamada.keywords:
        if palavra == "dono":
            return valor
    if chamada.args:
        return chamada.args[-1]
    return None


def varrer_chamadores(saida: io.StringIO) -> list[str]:
    problemas: list[str] = []
    total = 0
    for caminho in arquivos_de_producao():
        with open(caminho, encoding="utf-8") as arquivo:
            fonte = arquivo.read()
        arvore = ast.parse(fonte, filename=caminho)
        for chamada in chamadas_de_porta(arvore):
            total += 1
            relativo = os.path.relpath(caminho, PROJETO).replace("\\", "/")
            nome = chamada.func.attr
            dono = expressao_do_dono(chamada)

            if dono is None:
                problemas.append(
                    f"{relativo}:{chamada.lineno} {nome}() sem argumento de dono")
                saida.write(f"  FALHA {relativo}:{chamada.lineno} {nome}() -> SEM DONO\n")
                continue

            if isinstance(dono, ast.Constant):
                problemas.append(
                    f"{relativo}:{chamada.lineno} {nome}() passa o literal "
                    f"{dono.value!r} no proprio local")
                saida.write(
                    f"  FALHA {relativo}:{chamada.lineno} {nome}() -> "
                    f"LITERAL {dono.value!r}\n")
                continue

            saida.write(
                f"  ok    {relativo}:{chamada.lineno} {nome}() -> "
                f"{ast.unparse(dono)}\n")

    if total != CHAMADORES_ESPERADOS:
        problemas.append(
            f"a varredura encontrou {total} chamadores de porta em producao, e o "
            f"esperado sao {CHAMADORES_ESPERADOS}: a enumeracao dos chamadores "
            "mudou e o dono de cada um precisa ser revisto")
    saida.write(f"\n  chamadores de porta encontrados: {total} "
                f"(esperado {CHAMADORES_ESPERADOS})\n")
    return problemas


def varrer_constante(saida: io.StringIO) -> list[str]:
    problemas: list[str] = []
    atribuicoes: list[tuple[str, int, str]] = []

    for caminho in arquivos_de_producao():
        with open(caminho, encoding="utf-8") as arquivo:
            fonte = arquivo.read()
        linhas = fonte.splitlines()
        arvore = ast.parse(fonte, filename=caminho)
        for no in ast.walk(arvore):
            if not isinstance(no, ast.Assign):
                continue
            for alvo in no.targets:
                if isinstance(alvo, ast.Name) and "DONO" in alvo.id:
                    relativo = os.path.relpath(caminho, PROJETO).replace("\\", "/")
                    atribuicoes.append((relativo, no.lineno, alvo.id))

    saida.write(f"\n  atribuicoes de constante de dono: {len(atribuicoes)}\n")
    for relativo, linha, nome in atribuicoes:
        saida.write(f"    {relativo}:{linha} {nome}\n")

    if len(atribuicoes) != 1:
        problemas.append(
            f"existem {len(atribuicoes)} atribuicoes de constante de dono em "
            f"producao ({atribuicoes}): a RF-04 exige UM lugar unico")
        return problemas

    relativo, linha, nome = atribuicoes[0]
    caminho = os.path.join(PROJETO, relativo)
    with open(caminho, encoding="utf-8") as arquivo:
        linhas = arquivo.read().splitlines()
    bloco = "\n".join(linhas[max(0, linha - 30):linha])

    faltando = []
    if "isolamento" not in bloco:
        faltando.append("nao declara a ausencia de isolamento")
    if "#3" not in bloco:
        faltando.append("nao nomeia a divida #3")
    if "SEGURANCA" not in bloco.upper():
        faltando.append("nao declara que o dono nao e mecanismo de seguranca")
    if faltando:
        problemas.append(
            f"o bloco acima de {relativo}:{linha} ({nome}) " + "; ".join(faltando))
        saida.write(f"  FALHA bloco de {nome}: " + "; ".join(faltando) + "\n")
    else:
        saida.write(
            f"  ok    o bloco acima de {relativo}:{linha} ({nome}) declara a "
            "ausencia de isolamento, a divida #3 e a nao-seguranca\n")
    return problemas


def main() -> int:
    if not os.path.isdir(SRC):
        print(f"src/ nao encontrado em {SRC}")
        return 1

    saida = io.StringIO()
    arquivos = arquivos_de_producao()
    saida.write(f"arquivos de producao varridos: {len(arquivos)}\n\n")
    saida.write("1 e 2. chamadores de porta em producao\n")
    problemas = varrer_chamadores(saida)
    saida.write("\n3 e 4. a constante de dono\n")
    problemas += varrer_constante(saida)

    # Guarda contra verde vacuo: sem arquivo lido, ou sem chamador achado, a
    # varredura nao mediu nada e nao pode declarar conformidade.
    if len(arquivos) == 0:
        problemas.append("nenhum arquivo de producao foi lido: a varredura nao mediu nada")

    saida.write("\n" + "=" * 70 + "\n")
    if problemas:
        saida.write("RESULTADO: REPROVADO\n")
        for problema in problemas:
            saida.write(f"  - {problema}\n")
    else:
        saida.write("RESULTADO: APROVADO\n")
        saida.write("  todo chamador de producao passa o dono, sem literal no local;\n")
        saida.write("  a constante de dono e unica e o lugar dela declara o que a RF-04 exige\n")
    saida.write("=" * 70 + "\n")

    texto = saida.getvalue()
    print(texto)
    with open(EVIDENCIA, "w", encoding="utf-8", newline="\n") as arquivo:
        arquivo.write(texto)
    return 1 if problemas else 0


if __name__ == "__main__":
    sys.exit(main())

"""Prova que a padronizacao nao mexeu em nada alem de nomes e comentarios.

1. Compara o CODIGO de `text_cleaning.py` com a copia pristina de `domain.py`,
   por AST e sem os docstrings. Nenhum comando pode ter mudado.
2. Compara tambem linha a linha, para nomear exatamente o que mudou fora do codigo.
3. Confere que a arvore do README lista exatamente os modulos que existem.
4. Confere que os consumidores apontam para o nome novo.
"""
from __future__ import annotations

import ast
import difflib
import os

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", "..", "..", ".."))
ANTES = os.path.join(HERE, "before-after", "domain.antes.py")
ATUAL = os.path.join(ROOT, "src", "reconstructed", "text_cleaning.py")
PACOTE = os.path.join(ROOT, "src", "reconstructed")


def codigo_sem_docstring(caminho):
    """AST do modulo com todo docstring removido: prova de identidade do codigo."""
    with open(caminho, encoding="utf-8") as fh:
        arvore = ast.parse(fh.read())
    for no in ast.walk(arvore):
        corpo = getattr(no, "body", None)
        if (isinstance(corpo, list) and corpo
                and isinstance(corpo[0], ast.Expr)
                and isinstance(corpo[0].value, ast.Constant)
                and isinstance(corpo[0].value.value, str)):
            corpo.pop(0)
    return ast.dump(arvore)


def linhas(caminho):
    with open(caminho, encoding="utf-8") as fh:
        return fh.read().splitlines()


def fim_do_docstring(caminho):
    """Linha em que o docstring do modulo termina."""
    with open(caminho, encoding="utf-8") as fh:
        arvore = ast.parse(fh.read())
    primeiro = arvore.body[0]
    if not (isinstance(primeiro, ast.Expr) and isinstance(primeiro.value, ast.Constant)):
        raise SystemExit("o primeiro comando de %s nao e um docstring" % caminho)
    return primeiro.end_lineno


def arvore_do_readme():
    """Nomes de arquivo listados na arvore de `src/` do README."""
    nomes = []
    dentro = False
    for linha in linhas(os.path.join(ROOT, "README.md")):
        if linha.strip().startswith("src/") and "raiz de código" in linha:
            dentro = True
            continue
        if dentro and linha.strip() == "```":
            break
        if dentro and ".py" in linha:
            nome = linha.split("#")[0].strip().rsplit(" ", 1)[-1].split("/")[-1]
            if nome.endswith(".py"):
                nomes.append(nome)
    return sorted(set(nomes))


def modulos_reais():
    """Nomes de arquivo que existem, sem os marcadores de pacote."""
    nomes = ["app.py"]
    for raiz, dirs, arquivos in os.walk(PACOTE):
        dirs[:] = [d for d in dirs if d != "__pycache__"]
        for nome in sorted(arquivos):
            if nome.endswith(".py"):
                nomes.append(nome)
    # `__init__.py` e marcador de pacote e nao entra na arvore do README, por
    # convencao do proprio README. Sao dois arquivos com o mesmo nome, e compara-los
    # por nome colapsaria os dois em um.
    return sorted(set(n for n in nomes if n != "__init__.py"))


def main() -> int:
    falhas = []
    print("=" * 78)
    print("VERIFICACAO DA PADRONIZACAO LMAY")
    print("=" * 78)

    print("\n1. CODIGO, COMPARADO POR AST E SEM OS DOCSTRINGS")
    if codigo_sem_docstring(ANTES) == codigo_sem_docstring(ATUAL):
        print("   identico: nenhum comando, chamada, literal ou expressao mudou")
    else:
        falhas.append("o AST do modulo mudou")
        print("   O AST MUDOU")

    print("\n2. O QUE MUDOU FORA DO CODIGO")
    a, b = linhas(ANTES), linhas(ATUAL)
    fim_doc_antes = fim_do_docstring(ANTES)
    fim_doc_atual = fim_do_docstring(ATUAL)
    print("   linhas: antes %d, depois %d" % (len(a), len(b)))
    print("   docstring do modulo: antes termina na linha %d, depois na %d"
          % (fim_doc_antes, fim_doc_atual))

    dentro_doc, comentario, outro = [], [], []
    for tag, i1, i2, j1, j2 in difflib.SequenceMatcher(None, a, b).get_opcodes():
        if tag == "equal":
            continue
        for k in range(i1, i2):
            (dentro_doc if k < fim_doc_antes else
             comentario if a[k].lstrip().startswith("#") else outro).append(("- " + a[k].strip()))
        for k in range(j1, j2):
            (dentro_doc if k < fim_doc_atual else
             comentario if b[k].lstrip().startswith("#") else outro).append(("+ " + b[k].strip()))

    print("   linhas trocadas dentro do docstring do modulo : %d" % len(dentro_doc))
    print("   linhas de comentario trocadas                  : %d" % len(comentario))
    for linha in comentario:
        print("     %s" % linha)
    print("   linhas de OUTRO tipo trocadas                  : %d" % len(outro))
    for linha in outro:
        print("     %s" % linha)
    if outro:
        falhas.append("mudou linha que nao e comentario nem docstring")

    print("\n3. ARVORE DO README x MODULOS QUE EXISTEM")
    na_arvore, reais = arvore_do_readme(), modulos_reais()
    print("   na arvore do README : %d" % len(na_arvore))
    print("   arquivos que existem: %d  (sem `__init__.py`, que e marcador de pacote)" % len(reais))
    sobra = sorted(set(na_arvore) - set(reais))
    falta = sorted(set(reais) - set(na_arvore))
    if sobra:
        falhas.append("README lista arquivo que nao existe: %s" % ", ".join(sobra))
        print("   LISTA E NAO EXISTE: %s" % ", ".join(sobra))
    if falta:
        falhas.append("README nao lista arquivo que existe: %s" % ", ".join(falta))
        print("   EXISTE E NAO ESTA LISTADO: %s" % ", ".join(falta))
    if not sobra and not falta:
        print("   a arvore do README bate com o disco, arquivo por arquivo")

    print("\n4. CONSUMIDORES APONTAM PARA O NOME NOVO")
    consumidores = {
        "src/reconstructed/csv_ingest.py": "from .text_cleaning import demojibake",
        "src/reconstructed/name_normalization.py": "from .text_cleaning import strip_bad_utf",
        "src/reconstructed/dna_analysis.py": "from .text_cleaning import demojibake, strip_bad_utf",
        "tests/test_domain.py": "from reconstructed.text_cleaning import (",
    }
    for rel, esperado in consumidores.items():
        with open(os.path.join(ROOT, rel), encoding="utf-8") as fh:
            achou = esperado in fh.read()
        print("   %-44s %s" % (rel, "ok" if achou else "NAO ENCONTRADO"))
        if not achou:
            falhas.append("%s nao importa do nome novo" % rel)

    with open(os.path.join(ROOT, "_reversa_sdd", "parity", "harness.py"), encoding="utf-8") as fh:
        h = fh.read()
    alvo = "from reconstructed import text_cleaning as DM"
    print("   %-44s %s" % ("_reversa_sdd/parity/harness.py (dentro de string)",
                           "ok" if alvo in h else "NAO ENCONTRADO"))
    if alvo not in h:
        falhas.append("o import do harness, que vive dentro de uma string, nao foi atualizado")

    print()
    print("=" * 78)
    if falhas:
        print("RESULTADO: %d FALHA(S)" % len(falhas))
        for f in falhas:
            print("  " + f)
    else:
        print("RESULTADO: PADRONIZACAO CONFERIDA")
        print("  codigo intacto por AST, mudancas so em comentario e docstring,")
        print("  arvore do README coerente com o disco, consumidores no nome novo")
    print("=" * 78)
    return 1 if falhas else 0


if __name__ == "__main__":
    raise SystemExit(main())

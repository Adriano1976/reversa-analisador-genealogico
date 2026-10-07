"""T014: atualiza o ENCANAMENTO dos testes que chamam o documentary_relationship.

Preserva 100% das assercoes: so muda a origem da arvore. A funcao `_arvore()`
monta a tupla na hora da chamada, para funcionar tambem nos testes que carregam
o GEDCOM dentro do proprio teste.
"""
import io
import re

ARQUIVOS = [
    r"tests/test_confrontacao_gedcom_dna.py",
    r"tests/test_characterization_mermaid.py",
    r"tests/test_dna_analysis.py",
    r"tests/test_formatacao_cm.py",
]

HELPER = '''

def _arvore():
    """A arvore na forma que o nucleo passou a receber (feature 005, T014).

    Leu-se o estado no momento da chamada de proposito: varios testes carregam o
    GEDCOM dentro do proprio corpo, e uma constante de modulo capturaria o
    dicionario vazio.
    """
    from core import gedcom_state as _gs
    return (_gs.people, _gs.families, _gs.graph, _gs.child_to_family)
'''


def main() -> int:
    for caminho in ARQUIVOS:
        texto = io.open(caminho, encoding="utf-8").read()
        if "def _arvore():" in texto:
            print("  ja tem helper: %s" % caminho)
            continue
        n1 = len(re.findall(r"(?<![\w.])documentary_relationship\(", texto))
        n2 = len(re.findall(r"(?<![\w.])homonym_dossier\(", texto))
        if not n1 and not n2:
            print("  sem chamadas: %s" % caminho)
            continue
        texto = re.sub(r"(?<![\w.])documentary_relationship\(", "documentary_relationship(_arvore(), ", texto)
        texto = re.sub(r"(?<![\w.])homonym_dossier\(", "homonym_dossier(_arvore(), ", texto)
        # ancora: depois do ultimo import do topo. Usa a linha do import de gedcom_state.
        linhas = texto.splitlines(keepends=True)
        alvo = None
        for i, linha in enumerate(linhas):
            if linha.startswith("import ") or linha.startswith("from "):
                alvo = i
        if alvo is None:
            print("  ABORTADO (sem imports): %s" % caminho)
            return 1
        linhas.insert(alvo + 1, HELPER)
        io.open(caminho, "w", encoding="utf-8", newline="").write("".join(linhas))
        print("  atualizado: %s (%d + %d chamadas)" % (caminho, n1, n2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

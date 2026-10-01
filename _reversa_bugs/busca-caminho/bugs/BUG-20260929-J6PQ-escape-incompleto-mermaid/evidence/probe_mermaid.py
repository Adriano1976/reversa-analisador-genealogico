"""Sonda de diagnostico (nao altera codigo-fonte).

Verifica se o rotulo Mermaid montado por generate_mermaid_graph sobrevive a
nomes hostis vindos do GEDCOM. Somente leitura: substitui o dict `people` do
modulo em memoria, nunca toca arquivo do projeto.
"""
import sys

sys.path.insert(0, r"D:\Projetos\reversa_analisador_gelealogico\analisador-genealogico")

from reconstructed import path_search as ps  # noqa: E402


class Name:
    def __init__(self, s):
        self._s = s

    def format(self):
        return self._s


class Person:
    def __init__(self, s):
        self.name = Name(s)


CASES = [
    ("html-tag", '</div><script>alert(1)</script>'),
    ("aspas-fecha-no", 'Joao"] --> N_evil["x'),
    ("colchete", 'Joao] --> N_evil["pwn'),
    ("quebra-linha", 'Joao\nN_evil["x"]'),
    ("e-comercial", 'A & B'),
    ("crase", 'Joao`x`'),
    ("callbacks-mermaid", 'click N_evil href "javascript:alert(1)"'),
    ("ponto-e-virgula", 'Joao;%%{init: {"theme":"dark"}}%%'),
]

for tag, payload in CASES:
    ps.people = {"@I1@": Person(payload), "@I2@": Person("Alvo")}
    out = ps.generate_mermaid_graph(["@I1@", "@I2@"], "@I1@", "@I2@", None)
    print("=== " + tag)
    print(out)
    print()

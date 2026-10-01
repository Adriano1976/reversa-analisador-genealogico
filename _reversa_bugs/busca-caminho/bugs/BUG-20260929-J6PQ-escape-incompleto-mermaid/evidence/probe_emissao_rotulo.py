"""Re-verificacao do BUG-20260929-J6PQ depois da OPP-20260929-TPSH.

A TPSH unificou as duas copias de `lab()` numa funcao de modulo, e o bug
registrado cita essas duas copias. Esta sonda mede o formato real de emissao
do rotulo e se o texto hostil consegue encerra-lo.

Somente leitura: substitui o dict `people` do modulo apenas em memoria.
"""
import sys

sys.path.insert(0, "analisador-genealogico")

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
    ("html-tag", "</div><script>alert(1)</script>"),
    ("aspas-fecha-no", 'Joao"] --> N_evil["x'),
    ("colchete", 'Joao] --> N_evil["pwn'),
    ("quebra-de-linha", 'Joao\nN_evil["x"]'),
    ("e-comercial", "A & B"),
    ("crase", "Joao`x`"),
    ("palavra-chave-end", "Ana end"),
    ("palavra-chave-subgraph", "Ana subgraph"),
    ("callback-mermaid", 'click N_evil href "javascript:alert(1)"'),
    ("diretiva-init", 'Joao;%%{init: {"theme":"dark"}}%%'),
]

print("re-verificacao do J6PQ depois da TPSH")
print("=" * 78)
print("Pergunta: o payload consegue encerrar o rotulo antes das aspas de fechamento?")
print()

for tag, payload in CASES:
    ps.people = {"@I1@": Person(payload), "@I2@": Person("Alvo")}
    out = ps.generate_mermaid_graph(["@I1@", "@I2@"], "@I1@", "@I2@", None)
    linhas_no = [ln for ln in out.splitlines() if ln.startswith("N_") and '["' in ln]
    emitido = linhas_no[0] if linhas_no else "(sem no)"

    esc = ps._mermaid_label(payload)
    tem_aspas = '"' in payload
    aspas_sobrevivem = '"' in esc

    print("[" + tag + "]")
    print("  payload bruto : " + repr(payload))
    print("  label escapado: " + repr(esc))
    print("  linha emitida : " + emitido)
    sobrevive = "SIM" if aspas_sobrevivem else "nao"
    print("  payload tem aspas duplas: " + ("SIM" if tem_aspas else "nao")
          + " | aspas sobrevivem no label: " + sobrevive)
    print()

print("=" * 78)
print("Formato de emissao (path_search.py:235):")
print('  lines.append(f\'{node_sid}["{node_name}"]\')')
print()
print("O rotulo e delimitado por aspas duplas. O unico caractere capaz de")
print("encerra-lo antes do fim e a propria aspa dupla, e o escape a substitui")
print("por apostrofo (path_search.py:201). Colchete, crase e palavra-chave")
print("ficam dentro das aspas, onde a gramatica do flowchart nao os le como")
print("sintaxe.")

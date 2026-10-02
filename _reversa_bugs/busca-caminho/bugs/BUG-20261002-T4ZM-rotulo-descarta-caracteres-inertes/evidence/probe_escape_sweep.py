"""Varredura caractere a caractere do escape do rotulo Mermaid.

Mede, para cada caractere ASCII imprimivel, o que o oraculo congelado produz e o
que o candidato produz. Serve para enumerar exatamente quais caracteres o
candidato passou a descartar que o legado preservava.

Roda em DOIS processos separados, de proposito: o oraculo mantem estado global
mutavel, e importar os dois no mesmo processo contaminaria o candidato.

Uso:
    py -3.14 probe_escape_sweep.py --oracle
    py -3.14 probe_escape_sweep.py --cand

Cada caractere e testado no MEIO de um nome, que e onde ele apareceria de fato.
"""
import argparse
import importlib.util
import os
import sys

RAIZ = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))))
ORACULO = os.path.join(RAIZ, "_reversa_sdd", "oracle", "app_legacy_e43ca22.py")
CAND = os.path.join(RAIZ, "analisador-genealogico")
CWD_ISOLADO = os.path.join(RAIZ, ".pytest-tmp", "oracle-check", "cwd")


class Name:
    def __init__(self, s):
        self._s = s

    def format(self):
        return self._s


class Person:
    def __init__(self, s):
        self.name = Name(s)


def carregar(modo):
    if modo == "oracle":
        # O import do monolito cria uploads/ e static/ no diretorio de trabalho.
        os.makedirs(CWD_ISOLADO, exist_ok=True)
        os.chdir(CWD_ISOLADO)
        spec = importlib.util.spec_from_file_location("oraculo", ORACULO)
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        return mod
    sys.path.insert(0, CAND)
    from reconstructed import mermaid_render
    return mermaid_render


ap = argparse.ArgumentParser()
ap.add_argument("--oracle", action="store_true")
ap.add_argument("--cand", action="store_true")
args = ap.parse_args()
modo = "oracle" if args.oracle else "cand"
mod = carregar(modo)

print("lado: " + modo)
print("modulo: " + mod.__name__)
print()
for codigo in range(0x20, 0x7F):
    ch = chr(codigo)
    payload = "Ana%sSilva" % ch
    mod.people = {"@I1@": Person(payload), "@I2@": Person("Alvo")}
    try:
        saida = mod.generate_mermaid_graph(["@I1@", "@I2@"], "@I1@", "@I2@", None)
        linha = [ln for ln in saida.splitlines() if "N_I1" in ln and "[" in ln]
        rotulo = linha[0].split('["', 1)[1].rsplit('"]', 1)[0] if linha else "(sem no)"
    except Exception as e:
        rotulo = "(ERRO: %s)" % type(e).__name__
    print("%02X\t%r\t%s" % (codigo, ch, rotulo))

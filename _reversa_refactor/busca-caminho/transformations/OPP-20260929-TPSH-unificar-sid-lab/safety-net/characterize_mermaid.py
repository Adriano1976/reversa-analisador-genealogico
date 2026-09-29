"""Rede de segurança por caracterizacao (Feathers) para a OPP-20260929-TPSH.

Congela a saida Mermaid atual das duas funcoes de render, byte a byte,
INCLUINDO o que parecer errado. Nao julga, nao corrige: fixa o comportamento
de hoje para detectar qualquer mudanca depois da refatoracao.

Nao escreve em nenhum arquivo do projeto. O golden fica ao lado deste script,
dentro de _reversa_refactor/.

Uso:
    py -3.14 characterize_mermaid.py --capture    grava o golden
    py -3.14 characterize_mermaid.py              compara com o golden
"""
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
GOLDEN = os.path.join(HERE, "mermaid-golden.json")


def _achar_raiz(inicio):
    """Sobe diretorios ate achar a raiz do projeto (tem analisador-genealogico e tests)."""
    cur = inicio
    while True:
        if (os.path.isdir(os.path.join(cur, "analisador-genealogico"))
                and os.path.isdir(os.path.join(cur, "tests"))):
            return cur
        pai = os.path.dirname(cur)
        if pai == cur:
            raise RuntimeError("raiz do projeto nao encontrada a partir de " + inicio)
        cur = pai


ROOT = _achar_raiz(HERE)

sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.join(ROOT, "analisador-genealogico"))

# Permite provar a equivalencia contra uma copia transformada, sem tocar no projeto.
_SHADOW = os.environ.get("RECONSTRUCTED_SHADOW")
if _SHADOW and os.path.isdir(_SHADOW):
    sys.path.insert(0, _SHADOW)
    print(f"[caracterizacao] pacote reconstructed vem da sombra: {_SHADOW}")

import tempfile  # noqa: E402

from tests.fixtures.sample_gedcom import SAMPLE_GED  # noqa: E402

from reconstructed import upload  # noqa: E402
from reconstructed.path_search import path_search  # noqa: E402

# Pares que exercitam os TRES caminhos de render (dois deles usam sid/lab proprios):
# direto, indireto por afinidade (a funcao duplicada) e trivial.
CASES = [
    ("direto-carlos-ana", "Carlos Silva", "Ana Silva"),
    ("indireto-carlos-bia", "Carlos Silva", "Bia Oliveira"),
    ("trivial-carlos-carlos", "Carlos Silva", "Carlos Silva"),
    ("sem-conexao", "Carlos Silva", "Lone Ranger"),
]


def carregar():
    fd, path = tempfile.mkstemp(suffix=".ged")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            f.write(SAMPLE_GED)
        upload.load_gedcom_and_build_graph(path)
    finally:
        os.remove(path)


def capturar():
    carregar()
    out = {}
    for nome, p1, p2 in CASES:
        result, msg, success = path_search(p1, p2)
        out[nome] = {
            "msg": msg,
            "success": success,
            "text_path": (result or {}).get("text_path"),
            "mermaid_data": (result or {}).get("mermaid_data"),
        }
    return out


def main():
    capturado = capturar()
    if "--capture" in sys.argv:
        with open(GOLDEN, "w", encoding="utf-8") as f:
            json.dump(capturado, f, ensure_ascii=False, indent=2, sort_keys=True)
        print(f"golden gravado: {GOLDEN}")
        for k, v in capturado.items():
            n = len((v["mermaid_data"] or "").splitlines())
            print(f"  {k:<24} linhas de mermaid: {n}")
        return 0

    if not os.path.exists(GOLDEN):
        print("ERRO: golden ausente. Rode com --capture primeiro.")
        return 2
    with open(GOLDEN, encoding="utf-8") as f:
        esperado = json.load(f)

    falhas = []
    for k in sorted(esperado):
        if k not in capturado:
            falhas.append(f"{k}: caso desapareceu")
            continue
        if capturado[k] != esperado[k]:
            falhas.append(f"{k}: saida divergiu do golden")
            for campo in esperado[k]:
                if capturado[k].get(campo) != esperado[k][campo]:
                    falhas.append(f"    campo {campo} mudou")
    for k in sorted(capturado):
        if k not in esperado:
            falhas.append(f"{k}: caso novo sem golden")

    total_linhas = sum(len((v["mermaid_data"] or "").splitlines()) for v in esperado.values())
    if falhas:
        print(f"CARACTERIZACAO VERMELHA ({len(falhas)} divergencias)")
        for f_ in falhas:
            print("  " + f_)
        return 1
    print(f"CARACTERIZACAO VERDE: {len(esperado)} casos, {total_linhas} linhas de Mermaid identicas ao golden")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

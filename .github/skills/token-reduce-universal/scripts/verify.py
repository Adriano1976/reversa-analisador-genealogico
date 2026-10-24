#!/usr/bin/env python3
"""verify.py - confere se um texto comprimido preservou o que nao pode se perder.

Uso:
  python verify.py ORIGINAL COMPRIMIDO [--json] [--ignore idents,quoted]

ORIGINAL e COMPRIMIDO sao caminhos de arquivo. Codigos de saida:
  0 = PASS ou WARN   2 = FAIL (numero/URL/e-mail/caminho/codigo/negacao perdidos)
Checa: numeros e tokens com digito, URLs, e-mails, caminhos, codigo (bloco e inline),
identificadores, trechos entre aspas, e contagem de negacoes/obrigacoes (pt/en/es).
"""
import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import _lib  # noqa: E402


def main():
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass
    p = argparse.ArgumentParser()
    p.add_argument("original")
    p.add_argument("compressed")
    p.add_argument("--json", action="store_true")
    p.add_argument("--ignore", default="")
    a = p.parse_args()
    o = Path(a.original).read_text(encoding="utf-8", errors="replace")
    c = Path(a.compressed).read_text(encoding="utf-8", errors="replace")
    ignore = {x.strip() for x in a.ignore.split(",") if x.strip()}
    v = _lib.verify(o, c, ignore)
    tb, m = _lib.count_tokens(o)
    ta, _ = _lib.count_tokens(c)
    v["tokens"] = {"before": tb, "after": ta, "kept_fraction": round(ta / tb, 3) if tb else 1.0, "method": m}
    if a.json:
        print(json.dumps(v, ensure_ascii=False, indent=2))
    else:
        print(f"Status: {v['status']}  |  tokens {tb} -> {ta} ({v['tokens']['kept_fraction']:.0%}, {m})")
        for k, val in v["issues"].items():
            tag = "CRITICO" if k in v["critical"] else "aviso"
            print(f"  [{tag}] {k}: {json.dumps(val, ensure_ascii=False)}")
        if v["status"] == "FAIL":
            print("Restaure os itens criticos acima (ou, se for reformulacao legitima de negacao, "
                  "confirme manualmente e rode com --ignore negations).")
    sys.exit(2 if v["status"] == "FAIL" else 0)


if __name__ == "__main__":
    main()

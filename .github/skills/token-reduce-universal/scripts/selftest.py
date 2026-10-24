#!/usr/bin/env python3
"""selftest.py - teste rapido de sanidade (sem rede, sem dependencias).

Uso: python selftest.py   -> imprime OK ou aponta a falha (exit 1).
"""
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import _lib  # noqa: E402

SAMPLE = HERE.parent / "assets" / "sample-input.md"


def main():
    text = SAMPLE.read_text(encoding="utf-8")
    for level in (1, 2, 3, 4):
        r = _lib.compress_lite(text, level=level)
        v = _lib.verify(text, r["text"])
        assert v["status"] != "FAIL", f"nivel {level}: {v['issues']}"
        assert r["tokens_after"] < r["tokens_before"], f"nivel {level}: sem reducao"
    # o verificador precisa DETECTAR perdas
    bad = _lib.verify("Nao grave 1000ms em https://a.io/x", "Grave em https://a.io/x")
    assert bad["status"] == "FAIL" and {"numbers", "negations"} <= set(bad["critical"]), bad
    # idempotencia razoavel: comprimir de novo nao quebra nada
    once = _lib.compress_lite(text, level=2)["text"]
    twice = _lib.compress_lite(once, level=2)["text"]
    assert _lib.verify(once, twice)["status"] != "FAIL"
    print("OK - token-reduce-universal funcionando.")


if __name__ == "__main__":
    try:
        main()
    except AssertionError as e:
        print(f"FALHOU: {e}")
        sys.exit(1)

"""Deriva _reversa_docs/assets/data/features-index.json do SDD de 2026-10-05.

Uso: python .reversa/_docs_extract_features.py
"""
import sys

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except AttributeError:
        pass

import json
import re
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SDD = ROOT / "_reversa_sdd"
OUT = ROOT / "_reversa_docs" / "assets" / "data" / "features-index.json"

TITULOS = {
    "upload-gedcom": "Upload e parsing de GEDCOM",
    "analise-dna": "Analise de DNA e confronto",
    "busca-caminho": "Busca de caminho genealogico",
}

ACOES = {
    "upload-gedcom": "action=upload_gedcom",
    "analise-dna": "action=dna_analysis",
    "busca-caminho": "action=path_search",
}


def primeira_frase(txt: str) -> str:
    t = " ".join(txt.split())
    m = re.search(r"(.{40,400}?\.)\s", t)
    return m.group(1) if m else t[:300]


def visao_geral(txt: str) -> str:
    m = re.search(r"##\s+Vis[ãa]o Geral\s*\n+(.+?)(?:\n\n|\n##)", txt, flags=re.S)
    return primeira_frase(m.group(1)) if m else ""


def main():
    specs = []
    for d in sorted(SDD.iterdir()):
        req = d / "requirements.md"
        if not d.is_dir() or not req.exists():
            continue
        txt = req.read_text(encoding="utf-8", errors="replace")
        tasks = d / "tasks.md"
        ttxt = tasks.read_text(encoding="utf-8", errors="replace") if tasks.exists() else ""
        files = {}
        for nome in ("requirements.md", "design.md", "tasks.md", "contracts.md"):
            f = d / nome
            if f.exists():
                files[nome] = len(f.read_text(encoding="utf-8", errors="replace").splitlines())
        specs.append({
            "id": d.name,
            "slug": d.name,
            "title": TITULOS.get(d.name, d.name),
            "endpoint": ACOES.get(d.name, ""),
            "summary": visao_geral(txt) or primeira_frase(txt),
            "hasRequirements": True,
            "counts": {
                "requisitosFuncionais": len(set(re.findall(r"\bRF-\d+\b", txt))),
                "criteriosGherkin": len(re.findall(r"^\s*(?:\*\*)?Dado\b", txt, flags=re.M)),
                "tarefas": len(set(re.findall(r"\bT-\d{2,3}\b", ttxt))),
                "arquivos": files,
            },
        })

    doc = {
        "schemaVersion": 1,
        "generatedAt": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "project": "analisador-genealogico",
        "sourceStamp": "SDD re-extraido em 2026-10-05 (nivel completo)",
        "specs": specs,
    }
    OUT.write_text(json.dumps(doc, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print("features-index.json: %d specs" % len(specs))
    for s in specs:
        c = s["counts"]
        print("  %-14s RF=%-3d gherkin=%-3d tarefas=%-3d %s" % (s["id"], c["requisitosFuncionais"],
                                                                c["criteriosGherkin"], c["tarefas"],
                                                                ",".join("%s:%d" % kv for kv in c["arquivos"].items())))
        print("     %s" % s["summary"][:150])


if __name__ == "__main__":
    main()

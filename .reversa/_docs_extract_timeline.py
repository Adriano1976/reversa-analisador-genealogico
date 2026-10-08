"""Analyst, passo 3 estendido: monta timeline.json a partir de TRES fontes.

  1. cronica (.reversa/chronicle.md) - preservada verbatim do arquivo atual
  2. checkpoints de .reversa/state.json - preservados do arquivo atual
  3. NOVO: _reversa_forward/*/progress.jsonl - o ciclo forward, agregado por
     (feature, dia), marcado como fora da cronica

A cronica esta parada em 2026-10-01 e os checkpoints do state.json terminam em
2026-10-06, entao sem a terceira fonte a linha do tempo nao cobriria as features
005 a 008.

Uso: python .reversa/_docs_extract_timeline.py
"""
import sys

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except AttributeError:
        pass

import json
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DOCS = ROOT / "_reversa_docs"
TIMELINE = DOCS / "assets" / "data" / "timeline.json"
FORWARD = ROOT / "_reversa_forward"

LIMITE_NOTA = 150
MAX_NOTAS = 4


def notas_de(registros):
    saida = []
    for r in registros:
        n = (r.get("nota") or r.get("note") or "").strip()
        if not n:
            continue
        n = " ".join(n.split())
        if len(n) > LIMITE_NOTA:
            n = n[: LIMITE_NOTA - 1].rstrip() + "..."
        saida.append("%s: %s" % (r.get("action", "?"), n))
    saida.sort(key=len, reverse=True)
    return saida[:MAX_NOTAS]


def eventos_do_forward():
    eventos = []
    for d in sorted(FORWARD.iterdir()):
        if not d.is_dir():
            continue
        p = d / "progress.jsonl"
        if not p.exists():
            continue
        registros = []
        for linha in p.read_text(encoding="utf-8", errors="replace").splitlines():
            if not linha.strip():
                continue
            try:
                registros.append(json.loads(linha))
            except ValueError:
                continue
        if not registros:
            continue

        por_dia = defaultdict(list)
        for r in registros:
            dia = (r.get("ts") or "")[:10]
            if dia:
                por_dia[dia].append(r)

        fid = d.name.split("-")[0]
        nome = "-".join(d.name.split("-")[1:])
        for dia in sorted(por_dia):
            grupo = por_dia[dia]
            st = Counter(r.get("status", "?") for r in grupo)
            quando = max((r.get("ts") or "") for r in grupo)
            resumo = ", ".join("%d %s" % (n, s) for s, n in sorted(st.items()))
            partes = ["%d ação(ões) em %s (%s)." % (len(grupo), dia, resumo)]
            partes += notas_de(grupo)
            eventos.append({
                "id": "f%s-%s" % (fid, dia.replace("-", "")),
                "date": quando,
                "agent": "reversa-forward",
                "category": "forward",
                "title": "%s: %s" % (nome, dia),
                "detail": " ".join(partes),
                "source": "progress.jsonl",
                "foraDaCronica": True,
                "feature": d.name,
                "featureId": fid,
            })
    return eventos


def main():
    base = json.loads(TIMELINE.read_text(encoding="utf-8"))
    antigos = base["events"]
    cronica = [e for e in antigos if e.get("source") == "chronicle"]
    estado = [e for e in antigos if e.get("source") == "state.json"]
    outros = [e for e in antigos if e.get("source") not in ("chronicle", "state.json", "progress.jsonl")]

    print("base: %d eventos (%d cronica, %d state.json, %d sem fonte declarada)"
          % (len(antigos), len(cronica), len(estado), len(outros)))

    forward = eventos_do_forward()
    print("terceira fonte (progress.jsonl): %d eventos agregados por feature e dia" % len(forward))
    for e in forward:
        print("   %s  %-42s %s" % (e["date"][:10], e["title"], e["detail"][:70]))

    eventos = cronica + estado + outros + forward
    eventos.sort(key=lambda e: (e.get("date") or "", e.get("id") or ""))

    novo = {
        "schemaVersion": base.get("schemaVersion", 1),
        "generatedAt": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "sourceName": ("cronica ate 2026-09-30, eventos de .reversa/state.json a partir de 2026-10-05 "
                       "e eventos do ciclo forward a partir de 2026-08-11, todos os posteriores marcados "
                       "como fora da cronica"),
        "project": base.get("project", "analisador-genealogico"),
        "sources": [
            {"id": "chronicle", "path": ".reversa/chronicle.md", "eventos": len(cronica),
             "ultimo": max((e["date"] for e in cronica), default=None)},
            {"id": "state.json", "path": ".reversa/state.json", "eventos": len(estado),
             "ultimo": max((e["date"] for e in estado), default=None)},
            {"id": "progress.jsonl", "path": "_reversa_forward/*/progress.jsonl", "eventos": len(forward),
             "ultimo": max((e["date"] for e in forward), default=None)},
        ],
        "events": eventos,
    }
    TIMELINE.write_text(json.dumps(novo, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    print()
    print("timeline.json: %d eventos (antes %d)" % (len(eventos), len(antigos)))
    print("intervalo: %s .. %s" % (eventos[0]["date"], eventos[-1]["date"]))
    print("por fonte: %s" % Counter(e.get("source") for e in eventos))
    print("por categoria: %s" % Counter(e.get("category") for e in eventos))


if __name__ == "__main__":
    main()

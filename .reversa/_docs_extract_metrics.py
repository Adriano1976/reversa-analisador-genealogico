"""Deriva _reversa_docs/assets/data/metrics.json a partir de modules.json/deps.json
e conta, por regex, os numeros do SDD que sao contaveis de forma exata.

Uso: python .reversa/_docs_extract_metrics.py
"""
import sys

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except AttributeError:
        pass

import json
import re
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "_reversa_docs" / "assets" / "data"
SDD = ROOT / "_reversa_sdd"

FEATURES = ["upload-gedcom", "analise-dna", "busca-caminho"]


def load(p):
    return json.loads(p.read_text(encoding="utf-8"))


def histogram(locs):
    bins = [0, 50, 100, 200, 500, 1000, 5000]
    counts = []
    for i, lo in enumerate(bins):
        hi = bins[i + 1] if i + 1 < len(bins) else None
        if hi is None:
            counts.append(sum(1 for x in locs if x >= lo))
        else:
            counts.append(sum(1 for x in locs if lo <= x < hi))
    return {"bins": bins, "counts": counts,
            "labels": ["<50", "50-99", "100-199", "200-499", "500-999", "1000-4999", ">=5000"]}


def sdd_counts():
    out = {}
    rf_total = 0
    rf_por_feature = {}
    for f in FEATURES:
        req = SDD / f / "requirements.md"
        if req.exists():
            txt = req.read_text(encoding="utf-8", errors="replace")
            ids = sorted(set(re.findall(r"\bRF-\d+\b", txt)))
            rf_por_feature[f] = len(ids)
            rf_total += len(ids)
        tasks = SDD / f / "tasks.md"
        if tasks.exists():
            txt = tasks.read_text(encoding="utf-8", errors="replace")
            tids = sorted(set(re.findall(r"\bT-?\d{2,3}\b", txt)))
            out.setdefault("tasks", {})[f] = len(tids)
        des = SDD / f / "requirements.md"
        if des.exists():
            txt = des.read_text(encoding="utf-8", errors="replace")
            cen = re.findall(r"^\s*(?:\*\*)?Dado\b", txt, flags=re.M)
            out.setdefault("gherkin", {})[f] = len(cen)
    out["rfTotal"] = rf_total
    out["rfPorFeature"] = rf_por_feature

    adrs = sorted((SDD / "adrs").glob("*.md")) if (SDD / "adrs").is_dir() else []
    out["adrs"] = len(adrs)
    out["adrIds"] = [a.stem for a in adrs]

    gaps = SDD / "gaps.md"
    if gaps.exists():
        txt = gaps.read_text(encoding="utf-8", errors="replace")
        linhas = txt.splitlines()
        # Seccoes 2 (critica), 3 (moderadas) e 4 (cosmeticas) = lacunas abertas.
        abertas, secao = [], None
        criticas = []
        for l in linhas:
            m = re.match(r"^##\s+(\d)\.", l)
            if m:
                secao = m.group(1)
                continue
            if secao in ("2", "3", "4") and l.strip().startswith("|"):
                if re.match(r"^\|[\s:\-|]+\|$", l.strip()) or l.strip().lower().startswith("| id"):
                    continue
                abertas.append(l)
                if secao == "2":
                    criticas.append(l)
        out["gapsAbertasLinhas"] = len(abertas)
        out["gapsAbertasIds"] = len(set(re.findall(r"\b[A-Z]-\d+\b", "\n".join(abertas))))
        out["gapsCriticas"] = len(criticas)
        txt_resumo = txt.split("## 8.")[-1] if "## 8." in txt else ""
        out["gapsFechadasNaRodada"] = int(m.group(1)) if (m := re.search(r"##\s+5\.\s+Fechadas nesta rodada\s+[—-]?\s*(\d+)", txt)) else None

    conf = SDD / "confidence-report.md"
    if conf.exists():
        txt = conf.read_text(encoding="utf-8", errors="replace")
        out["confidenceMd"] = str(conf.relative_to(ROOT)).replace("\\", "/")
        m = re.findall(r"(\d{1,3},\d)\s*%", txt)
        out["percentuaisCitados"] = sorted(set(m))
    return out


def main():
    mods = load(DATA / "modules.json")
    deps = load(DATA / "deps.json")
    modules = mods["modules"]
    now = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

    by_folder = defaultdict(lambda: {"loc": 0, "modules": 0, "complexity": 0})
    for m in modules:
        b = by_folder[m["folder"]]
        b["loc"] += m["loc"]
        b["modules"] += 1
        b["complexity"] += m["complexity"]
    treemap = [{"folder": k, **v} for k, v in sorted(by_folder.items(), key=lambda kv: -kv[1]["loc"])]

    top = sorted(modules, key=lambda m: (-m["complexity"], -m["loc"]))[:20]
    top_complexity = [{"id": m["path"], "name": m["name"], "folder": m["folder"],
                       "complexity": m["complexity"], "loc": m["loc"]} for m in top]

    langs = defaultdict(lambda: {"modules": 0, "loc": 0})
    for m in modules:
        langs[m["language"]]["modules"] += 1
        langs[m["language"]]["loc"] += m["loc"]
    language_distribution = [{"language": k, **v} for k, v in sorted(langs.items(), key=lambda kv: -kv[1]["loc"])]

    peso = Counter()
    for i in deps.get("imports", []):
        if i["to"] == "externo":
            continue
        peso[(i["from"], i["to"])] += 1
    por_par = Counter()
    for (origem, destino), n in peso.items():
        if origem == "src/app.py":
            pkg = "app"
        elif origem.startswith("tests/"):
            pkg = "tests"
        else:
            pkg = origem.split("/")[1]
        por_par[(pkg, destino)] += n
    links = [{"source": a, "target": b, "value": n} for (a, b), n in sorted(por_par.items())]
    sankey = {"nodes": [{"id": n} for n in deps["nodes"]], "links": links}

    sdd = sdd_counts()
    metrics = {
        "schemaVersion": 1,
        "generatedAt": now,
        "source": "modules.json + deps.json (extracao deterministica de 2026-10-06) e contagens do SDD de 2026-10-05",
        "code": {
            "modules": len(modules),
            "locNaoVazio": mods["summary"]["locTotal"],
            "locSrcPython": mods["summary"]["locSrcPython"],
            "locTests": mods["summary"]["locTests"],
            "complexityTotal": mods["summary"]["complexityTotal"],
            "pastas": len(by_folder),
            "pacotes": len(deps["nodes"]),
            "arestasDePacote": len(deps["edges"]),
            "ciclos": len(deps["cycles"]),
        },
        "treemap_loc_by_folder": treemap,
        "top_complexity": top_complexity,
        "loc_histogram": histogram([m["loc"] for m in modules]),
        "dependency_sankey": sankey,
        "language_distribution": language_distribution,
        "sdd": sdd,
    }
    (DATA / "metrics.json").write_text(json.dumps(metrics, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    print("metrics.json gravado")
    print("  code:", metrics["code"])
    print("  treemap:", [(t["folder"], t["loc"]) for t in treemap])
    print("  top complexity:", [(t["name"], t["complexity"], t["loc"]) for t in top_complexity[:6]])
    print("  histogram:", metrics["loc_histogram"]["counts"])
    print("  sankey links:", [(l["source"], l["target"], l["value"]) for l in links])
    print("  languages:", language_distribution)
    print("  sdd:", json.dumps(sdd, ensure_ascii=False))


if __name__ == "__main__":
    main()

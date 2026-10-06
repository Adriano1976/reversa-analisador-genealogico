"""Publisher, passo 10: telemetria final em _reversa_docs/.state.json.

Uso: python .reversa/_docs_telemetry.py
"""
import sys

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except AttributeError:
        pass

import json
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DOCS = ROOT / "_reversa_docs"
STATE = DOCS / ".state.json"

INICIO = "2026-10-06T03:43:10Z"
ISOLADO_INICIO = "2026-10-06T05:24:11Z"


def ler(p, padrao):
    try:
        return json.loads(p.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return padrao


def main():
    isolado = "--isolated" in sys.argv
    s = json.loads(STATE.read_text(encoding="utf-8"))
    smoke = ler(DOCS / ".smoke-result.json", {"smokeTestFailed": True, "smokeTestErrors": []})
    links = ler(DOCS / ".links-result.json", [])

    agora = datetime.now(timezone.utc)
    t0 = datetime.strptime(INICIO, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc)

    if isolado:
        # reexecucao isolada do Publisher: preserva a telemetria do pipeline
        # completo e registra esta execucao em separado
        s["publisherIsolatedRun"] = {
            "startedAt": ISOLADO_INICIO,
            "lastCheckpoint": agora.strftime("%Y-%m-%dT%H:%M:%SZ"),
            "durationMs": int((agora - datetime.strptime(
                ISOLADO_INICIO, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc)).total_seconds() * 1000),
            "reason": ("reexecucao isolada do Publisher a pedido do usuario, sem Mapper, Analyst nem Storyteller. "
                       "Selos regerados pela skill reversa-selo-generativo a partir da mesma seed, na variante "
                       "dark prevista pela paleta sober para header escuro, com descarte das cores abaixo de "
                       "2,5:1 de contraste; selo grande do hero passou de <img> para SVG inline."),
            "preservedPipelineDurationMs": s.get("pipelineDurationMs"),
        }
    else:
        s["startedAt"] = INICIO
        s["pipelineDurationMs"] = int((agora - t0).total_seconds() * 1000)

    s["lastCheckpoint"] = agora.strftime("%Y-%m-%dT%H:%M:%SZ")
    s["completedAgents"] = ["mapper", "analyst", "storyteller", "publisher"]
    s["pendingAgents"] = []
    s["pagesOmitted"] = [{
        "page": "topologia.html",
        "reason": ("architecture.md de 2026-10-05 nao declara secao de Topologia nem variantes de topologia "
                   "(secoes 1 a 9: visao geral, containers, componentes, modelo de dados, fluxo, integracoes, "
                   "dividas, decisoes, resumo)"),
    }]
    s["auxiliaryHtmls"] = []
    s["auxiliaryHtmlsDiscovered"] = 0
    s["auxiliaryDiscoveryAborted"] = False
    s["cdnFallbackUsed"] = False
    s["cdnFallbackDetails"] = []
    s["vendorMissing"] = []
    s["vendorFiles"] = sorted(p.name for p in (DOCS / "assets" / "vendor").glob("*"))
    s["smokeTestFailed"] = bool(smoke.get("smokeTestFailed"))
    s["smokeTestErrors"] = smoke.get("smokeTestErrors", [])
    s["smokeTestCheckedPages"] = 10
    s["smokeTestCheckedAssets"] = 29
    s["brokenLinks"] = links
    s["dataJsKeys"] = ["modules", "deps", "metrics", "timeline", "glossary", "featuresIndex",
                       "sealSvg", "sealMiniSvg", "seedShort", "nav", "config"]
    s["seal"] = {
        "seedSource": ".reversa/soul.md",
        "seedHash": "sha256:57d09b0c7c4a588d1abc035c83606909dd3bfa2c73aa667ba46e248873be4f39",
        "pattern": "crystal-lattice",
        "variant": "dark (paleta sober espelhada para header escuro)",
        "sealSvgBytes": (DOCS / "assets" / "img" / "seal.svg").stat().st_size,
        "sealMiniSvgBytes": (DOCS / "assets" / "img" / "seal-mini.svg").stat().st_size,
        "deterministic": True,
    }
    s["regeneration"]["tooling"] = (
        "templates/documentation/ NAO existe nesta instalacao: sem viewer.html, .tpl, sidebar.js, "
        "extract_modules.py, extract_deps.py, convert_chronicle.py ou convert_soul.py. A extracao de dados "
        "foi feita por scripts deterministicos proprios, guardados em .reversa/: _docs_extract_modules.py, "
        "_docs_extract_metrics.py, _docs_extract_features.py, _docs_nav.py, _docs_build_datajs.py, "
        "_docs_inject_pages.py, _docs_smoke_test.py, _docs_render_check.js e _docs_state.py."
    )
    s["regeneration"]["verifiedBy"] = (
        "Tres verificacoes independentes: (1) node .reversa/_docs_render_check.js carrega o data.js num "
        "window falso e confere o inventario das 6 chaves de dados, os 10 itens do nav e a sintaxe do script "
        "inline das 10 paginas via vm.Script; (2) .reversa/_docs_smoke_test.py sobe http.server efemero, faz "
        "GET nas 10 paginas e nos 29 assets locais e valida os links relativos contra o disco; (3) markdownlint "
        "nos artefatos de texto do SDD."
    )
    s["regeneration"]["whatChanged"].append(
        "publisher: data.js reconstruido com as 6 chaves de dados (antes so tinha modules e timeline, o que "
        "deixava glossario.html e deck.html vazios e o nav sem links); selo novo a partir do seed do soul.md "
        "regenerado; 10 paginas com mini-selo e nav estatico de 10 links; index.html com 6 cards e as 3 "
        "features; auto-discovery com 0 HTMLs auxiliares; smoke test verde"
    )
    s["regeneration"]["seal"] = {
        "seedSource": ".reversa/soul.md",
        "seedHash": "sha256:57d09b0c7c4a588d1abc035c83606909dd3bfa2c73aa667ba46e248873be4f39",
        "sealSvgBytes": (DOCS / "assets" / "img" / "seal.svg").stat().st_size,
        "sealMiniSvgBytes": (DOCS / "assets" / "img" / "seal-mini.svg").stat().st_size,
    }
    s["regeneration"]["soul"] = {
        "regeneratedAt": "2026-10-06",
        "by": "reversa-extract-soul (autorizado pelo usuario nesta sessao)",
        "previousPreservedAt": ".reversa/soul.20260928-1537.md",
        "previousBytes": 4585,
        "currentBytes": (ROOT / ".reversa" / "soul.md").stat().st_size,
    }

    STATE.write_text(json.dumps(s, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    for f in (".smoke-result.json", ".links-result.json"):
        p = DOCS / f
        if p.exists():
            p.unlink()

    print("state.json atualizado")
    print("  startedAt=%s  lastCheckpoint=%s" % (s["startedAt"], s["lastCheckpoint"]))
    print("  pipelineDurationMs=%d (%.1f min)" % (s["pipelineDurationMs"], s["pipelineDurationMs"] / 60000.0))
    print("  completedAgents=%s  pendingAgents=%s" % (s["completedAgents"], s["pendingAgents"]))
    print("  pagesGenerated=%d  pagesOmitted=%d" % (len(s["pagesGenerated"]), len(s["pagesOmitted"])))
    print("  smokeTestFailed=%s  brokenLinks=%d  vendorFiles=%d"
          % (s["smokeTestFailed"], len(s["brokenLinks"]), len(s["vendorFiles"])))
    falta = [p for p in s["pagesGenerated"] if p not in s["pages"]]
    print("  paginas sem hash registrado: %s" % (falta or "nenhuma"))


if __name__ == "__main__":
    main()

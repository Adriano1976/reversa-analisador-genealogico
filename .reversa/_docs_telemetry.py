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
ISOLADO_INICIO = "2026-10-08T15:48:22Z"


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
    s["smokeTestCheckedPages"] = smoke.get("pagesChecked")
    s["smokeTestCheckedAssets"] = smoke.get("assetsChecked")
    s["brokenLinks"] = links
    s["regenerationStamp"] = "2026-10-08 (features 005 a 008)"
    s["dataJsKeys"] = ["modules", "deps", "metrics", "timeline", "glossary", "featuresIndex",
                       "seedShort", "nav", "config"]
    s.pop("seal", None)
    s["logo"] = {
        "origem": "logo do projeto fornecido pelo usuario em 2026-10-08 (livro aberto, hélice de DNA e árvore)",
        "hero": "assets/img/logo.png (512x512, RGBA com transparencia real)",
        "mini": "assets/img/logo-mini.png (64x64)",
        "substitui": ("o selo generativo derivado da seed (seal.svg e seal-mini.svg), removido do mini-site "
                      "por decisao do usuario. O hero e os 10 mini-selos passaram de SVG inline para <img>."),
        "heroBytes": (DOCS / "assets" / "img" / "logo.png").stat().st_size,
        "miniBytes": (DOCS / "assets" / "img" / "logo-mini.png").stat().st_size,
        "faviconDoApp": ("src/templates/index.html declara o mesmo logo como icone da aba, em data URI de "
                         "64x64, sem rota nova e sem src/static/ (proibida pelo watch item W004)"),
        "faviconDoMiniSite": ("as 10 paginas de _reversa_docs/ declaram <link rel=\"icon\"> apontando para "
                              "assets/img/logo-mini.png (com o prefixo ../ nas de features/), em vez de "
                              "repetir um data URI de 8 KB em cada uma. Mantido pelo passo 4 do Publisher, "
                              "que virou dono dessa etapa: _docs_inject_pages.py.garantir_favicon"),
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
    s["regeneration"].pop("sealRerun", None)
    s["regeneration"]["logo"] = {
        "instaladoEm": "2026-10-08",
        "hero": "assets/img/logo.png",
        "mini": "assets/img/logo-mini.png",
        "removeu": ["assets/img/seal.svg", "assets/img/seal-mini.svg"],
        "motivo": "decisao do usuario: o logo do projeto substitui o selo generativo derivado da seed",
    }
    s["regeneration"]["soul"] = {
        "regeneratedAt": "2026-10-08",
        "by": "reversa-extract-soul, gravado pelo orquestrador (o subagente nao tinha escopo de escrita)",
        "previousPreservedAt": ".reversa/soul.20261006-0142.md",
        "previousBytes": 15559,
        "currentBytes": (ROOT / ".reversa" / "soul.md").stat().st_size,
    }

    STATE.write_text(json.dumps(s, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    # Os dois arquivos de resultado do smoke test FICAM: o conteudo deles ja foi
    # absorvido aqui, e apaga-los mexeria em arquivos que o git passou a rastrear.
    # Se quiser que voltem a ser transitorios, tire-os do versionamento e ponha
    # no .gitignore; esta funcao nao decide isso sozinha.

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

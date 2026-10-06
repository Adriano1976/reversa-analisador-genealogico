"""Atualiza _reversa_docs/.state.json depois de cada agente do Time Reversa Docs.

Uso:
  python .reversa/_docs_state.py <agente> <paginas separadas por virgula> [<nota>]

Ex.:
  python .reversa/_docs_state.py mapper "arquitetura.html,modulos.html" "Code City e grafo regenerados"
"""
import sys

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except AttributeError:
        pass

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
STATE = ROOT / "_reversa_docs" / ".state.json"
DOCS = ROOT / "_reversa_docs"

ORDER = ["mapper", "analyst", "storyteller", "publisher"]
TODAY = "2026-10-06T00:43:10Z"


def sha(p: Path) -> str:
    return "sha256:" + hashlib.sha256(p.read_bytes()).hexdigest()


def main():
    agent = sys.argv[1]
    pages = [p for p in sys.argv[2].split(",") if p.strip()]
    note = sys.argv[3] if len(sys.argv) > 3 else ""

    state = json.loads(STATE.read_text(encoding="utf-8"))

    if agent == "mapper":
        if "regeneration" in state:
            antigo = state.pop("regeneration")
            state.setdefault("history", []).append({
                "startedAt": "2026-10-01T03:30:00Z",
                "lastCheckpoint": "2026-10-01T03:47:11Z",
                "pipelineDurationMs": 900000,
                "note": "Regeneracao anterior. " + antigo.get("reason", "")[:400],
            })
        state["completedAgents"] = []
        state["pendingAgents"] = []
        state["regeneration"] = {
            "kind": "re-extração completa do mini-site",
            "reason": ("O mini-site havia sido gerado em 2026-10-01 e descrevia o código anterior ao refactor "
                       "que achatou `analisador-genealogico/reconstructed/` para `src/`, e o SDD anterior à "
                       "re-extração de 2026-10-05. Todos os caminhos de módulo, as contagens, as métricas e as "
                       "3 features estavam defasados."),
            "backup": ".backup-20261006-004310/",
            "sourceStamp": "re-extração do SDD de 2026-10-05",
            "whatChanged": [],
        }

    agent_full = "reversa-docs-%s" % agent
    for p in pages:
        f = DOCS / p
        if not f.exists():
            print("AVISO: pagina inexistente, nao registrada: %s" % p)
            continue
        state["pages"][p] = {"status": "created", "agent": agent_full, "hash": sha(f)}
        if p.endswith(".html") and p not in state["pagesGenerated"]:
            state["pagesGenerated"].append(p)

    if agent not in state["completedAgents"]:
        state["completedAgents"].append(agent)
    state["pendingAgents"] = [a for a in ORDER if a not in state["completedAgents"]]
    state["lastCheckpoint"] = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

    if note:
        state["regeneration"]["whatChanged"].append("%s: %s" % (agent, note))

    STATE.write_text(json.dumps(state, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    print("agente=%s paginas=%d completos=%s pendentes=%s"
          % (agent, len(pages), state["completedAgents"], state["pendingAgents"]))
    for p in pages:
        if (DOCS / p).exists():
            print("  %-38s %s" % (p, sha(DOCS / p)[:23]))


if __name__ == "__main__":
    main()

"""Ajusta a telemetria de _reversa_docs/.state.json para descrever a rodada de
2026-10-08 como o que ela foi: uma regeneracao completa com soul mais os quatro
agentes, e nao uma reexecucao isolada do Publisher.

Uso: python .reversa/_docs_runs.py
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
STATE = ROOT / "_reversa_docs" / ".state.json"

INICIO_20261008 = "2026-10-08T15:48:22Z"


def main():
    s = json.loads(STATE.read_text(encoding="utf-8"))
    agora = datetime.now(timezone.utc)
    t0 = datetime.strptime(INICIO_20261008, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc)
    dur = int((agora - t0).total_seconds() * 1000)

    antigo = s.pop("publisherIsolatedRun", None)
    if antigo:
        antigo["kind"] = "reexecucao isolada do Publisher, sem Mapper, Analyst nem Storyteller"
        s["publisherIsolatedRun"] = antigo

    s["startedAt"] = INICIO_20261008
    s["pipelineDurationMs"] = dur
    s["lastCheckpoint"] = agora.strftime("%Y-%m-%dT%H:%M:%SZ")
    s["runs"] = [
        {
            "startedAt": "2026-10-06T03:43:10Z",
            "durationMs": 5119324,
            "agents": ["mapper", "analyst", "storyteller", "publisher"],
            "note": ("primeira regeneracao completa, sobre a re-extracao do SDD de 2026-10-05. "
                     "10 paginas, 37 modulos, 5966 linhas, 2 ciclos de pacote."),
        },
        {
            "startedAt": INICIO_20261008,
            "durationMs": dur,
            "agents": ["extract-soul", "mapper", "analyst", "storyteller", "publisher"],
            "note": ("regeneracao completa sobre o codigo de 2026-10-08, depois das features 005 a 008: "
                     "soul.md reescrito, 61 modulos, 9972 linhas, 10 pastas, 8 pacotes, 20 arestas, "
                     "0 ciclos, 96 eventos de timeline e 44 conceitos de glossario."),
        },
    ]
    s["cycleFinding"] = {
        "medido": "0 ciclos de pacote entre os 8 pacotes, contra 2 na extracao de 2026-10-05",
        "atribuicao": ("dois commits diretos, fora de qualquer feature do ciclo forward: 2443273, que moveu "
                       "norm_name para utils e quebrou core<->parsers, e 87bcea5, que injetou o resolvedor de "
                       "diagrama e quebrou core<->reporting, em 2026-10-06"),
        "contradicao_registrada": ("o _reversa_sdd/architecture.md e os adendos 005, 006 e 007 registram a "
                                   "divida #5 como presente ou inalterada. Os adendos estao certos sobre as "
                                   "features nao terem tocado os ciclos, mas nenhum artefato declara a quebra, "
                                   "que veio de commits diretos. Registrado como L7 no soul.md."),
    }

    STATE.write_text(json.dumps(s, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print("state.json: runs=%d  startedAt=%s  duracao=%.1f min"
          % (len(s["runs"]), s["startedAt"], dur / 60000.0))
    print("cycleFinding registrado")
    print("whatChanged: %d entradas" % len(s["regeneration"]["whatChanged"]))
    for w in s["regeneration"]["whatChanged"]:
        print("  - %s..." % w[:95])


if __name__ == "__main__":
    main()

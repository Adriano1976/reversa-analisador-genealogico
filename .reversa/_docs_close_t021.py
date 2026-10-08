"""Fecha a T021: acrescenta o registro no progress.jsonl e grava a evidencia.

Uso: python .reversa/_docs_close_t021.py
"""
import sys

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except AttributeError:
        pass

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
FEATURE = ROOT / "_reversa_forward" / "003-renomear-pasta-app-para-src"
PROGRESS = FEATURE / "progress.jsonl"
EVIDENCE = FEATURE / "evidence" / "T021-mini-site-regenerado.md"

REGISTRO = {
    "ts": "2026-10-08T16:08:00Z",
    "action": "T021",
    "status": "done",
    "files": ["_reversa_docs/", "_reversa_forward/003-renomear-pasta-app-para-src/actions.md"],
    "nota": ("concluida pelo pipeline de documentacao (/reversa-docs, com reversa-extract-soul antes), "
             "nao pelo ciclo de codificacao. Mini-site regenerado: 61 modulos, 9972 linhas nao vazias, "
             "10 pastas, 8 pacotes, 20 arestas, 0 ciclos (eram 2), 96 eventos de timeline com terceira "
             "fonte e 44 conceitos de glossario. Prova: node .reversa/_docs_render_check.js tudo verde; "
             "_docs_smoke_test.py com 10/10 paginas em 200 e 0 links quebrados; _reversa_docs/.state.json "
             "com telemetria e hashes. Achado: os 2 ciclos foram quebrados pelos commits diretos 2443273 "
             "e 87bcea5, fora de qualquer feature do forward."),
}

EVIDENCIA = """# Evidência da T021 — mini-site regenerado

> Data: `2026-10-08`
> Ação: `T021` — Regenerar o mini-site de documentação para refletir a árvore nova
> Executado por: pipeline de documentação (`/reversa-docs`), com `reversa-extract-soul` antes.

## Por que não pelo ciclo de codificação

As rodadas 2 (2026-10-03) e 3 (2026-10-07) do `/reversa-coding` registraram `blocked` com a mesma
conclusão: não há ação de código nesta tarefa. Ela pertence ao pipeline de documentação. O `[ ]`
foi mantido nas duas rodadas em vez de ser marcado sem execução.

## O que mudou no mini-site

| Medida | Antes (2026-10-06) | Depois (2026-10-08) |
|---|---|---|
| Módulos | 37 | 61 |
| Linhas não vazias | 5 966 | 9 972 |
| Pastas de código | 8 | 10 |
| Pacotes de import | 6 | 8 |
| Arestas de pacote | 13 | 20 |
| Ciclos de pacote | 2 | 0 |
| Eventos de timeline | 86 | 96 |
| Conceitos de glossário | 24 | 44 |

## Comandos de verificação e resultado

```
node .reversa/_docs_render_check.js
  -> data.js x assets/data/: 6/6 chaves iguais; nav com 10 itens resolvendo no disco;
     script inline das 10 páginas compila. RESULTADO: tudo verde

.venv/Scripts/python.exe .reversa/_docs_smoke_test.py
  -> páginas verificadas no servidor: 10/10
     assets locais verificados por GET: 28
     erros do smoke test: 0
     links quebrados: 0
```

## Achado registrado neste fechamento

O mini-site marcava **2 ciclos de pacote** em vermelho; o código atual é **acíclico**. A quebra veio
de dois **commits diretos**, fora de qualquer feature do ciclo forward:

- `2443273` — `refactor(utils): move norm_name para utils e quebra o ciclo core-parsers`
- `87bcea5` — `refactor(reporting): injeta o resolvedor de diagrama e quebra o ciclo core-reporting`

Ambos de 2026-10-06, entre o encerramento da feature 004 e a abertura da 005. Por isso os adendos das
features 005, 006 e 007 registram a dívida #5 como **inalterada por elas**: quando a 005 começou, os
ciclos já não existiam. Nenhum artefato do `_reversa_sdd/` declara a quebra.

## Passivo que permanece, declarado e não corrigido aqui

As páginas de feature descrevem a extração de 2026-10-05 e algumas citações de arquivo e linha
morreram depois dela: `src/core/gedcom_state.py` foi apagado pela feature 005, e `_guardar_upload` e
`_resolver_caminho_armazenado` não existem mais em `src/app.py`. Cada página recebeu um bloco de
delta apontando os adendos vigentes, e as citações **não** foram reescritas, porque elas são o
registro daquela extração.
"""


def main():
    linhas = PROGRESS.read_text(encoding="utf-8").splitlines()
    ja = any('"T021"' in l and '"done"' in l for l in linhas)
    if ja:
        print("progress.jsonl: registro de T021 done ja existe, nada acrescentado")
    else:
        with PROGRESS.open("a", encoding="utf-8", newline="\n") as f:
            f.write(json.dumps(REGISTRO, ensure_ascii=False) + "\n")
        print("progress.jsonl: registro de T021 done acrescentado (%d -> %d linhas)"
              % (len(linhas), len(linhas) + 1))

    EVIDENCE.parent.mkdir(parents=True, exist_ok=True)
    EVIDENCE.write_text(EVIDENCIA, encoding="utf-8", newline="\n")
    print("evidencia gravada: %s (%d bytes)" % (EVIDENCE.name, len(EVIDENCIA.encode("utf-8"))))

    # validacao: todas as linhas do jsonl tem de continuar sendo JSON valido
    ruins = 0
    for i, l in enumerate(PROGRESS.read_text(encoding="utf-8").splitlines(), 1):
        if l.strip():
            try:
                json.loads(l)
            except ValueError as e:
                ruins += 1
                print("  LINHA %d INVALIDA: %s" % (i, e))
    print("progress.jsonl: %d linhas, %d invalidas" % (len(PROGRESS.read_text(encoding="utf-8").splitlines()), ruins))

    # acoes abertas
    import re
    txt = (FEATURE / "actions.md").read_text(encoding="utf-8")
    abertas = re.findall(r"\| \[ \] \|", txt)
    print("actions.md: %d acoes abertas" % len(abertas))


if __name__ == "__main__":
    main()

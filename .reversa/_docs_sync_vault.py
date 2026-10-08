"""Sincroniza _reversa_docs/ para docs/ (a copia do vault do Obsidian).

Regras:
  - copia todo arquivo de _reversa_docs/ (menos .backup-*) para docs/, preservando
    a estrutura de pastas;
  - remove de docs/ os arquivos do mini-site que deixaram de existir na origem,
    hoje apenas assets/img/seal.svg e assets/img/seal-mini.svg;
  - NAO toca nos arquivos do Obsidian (Markdown e .canvas) nem nos .backup-* que
    ja existem dentro de docs/.

Uso: python .reversa/_docs_sync_vault.py [--seco]
"""
import sys

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except AttributeError:
        pass

import hashlib
import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
ORIGEM = ROOT / "_reversa_docs"
DESTINO = ROOT / "docs"

# arquivos que pertenciam a copia antiga do mini-site e nao existem mais
OBSOLETOS = ["assets/img/seal.svg", "assets/img/seal-mini.svg"]


def sha(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


def arquivos(base: Path):
    for p in base.rglob("*"):
        if p.is_file() and ".backup-" not in p.relative_to(base).as_posix():
            yield p.relative_to(base).as_posix()


def main():
    seco = "--seco" in sys.argv
    if not DESTINO.exists():
        print("ERRO: %s nao existe" % DESTINO)
        return 2

    copiados, iguais = [], 0
    for rel in sorted(arquivos(ORIGEM)):
        src = ORIGEM / rel
        dst = DESTINO / rel
        if dst.exists() and sha(src) == sha(dst):
            iguais += 1
            continue
        if not seco:
            dst.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(src, dst)
        copiados.append(rel)

    removidos = []
    for rel in OBSOLETOS:
        dst = DESTINO / rel
        if dst.exists():
            if not seco:
                dst.unlink()
            removidos.append(rel)

    print("arquivos na origem: %d" % len(list(arquivos(ORIGEM))))
    print("ja identicos: %d" % iguais)
    print("copiados/atualizados: %d" % len(copiados))
    for c in copiados:
        print("   %s" % c)
    print("removidos do vault (nao existem mais na origem): %d" % len(removidos))
    for r in removidos:
        print("   %s" % r)

    # verificacao final: os dois lados batem para o conjunto do mini-site
    faltando, divergentes = [], []
    for rel in arquivos(ORIGEM):
        dst = DESTINO / rel
        if not dst.exists():
            faltando.append(rel)
        elif sha(ORIGEM / rel) != sha(dst):
            divergentes.append(rel)
    print()
    print("verificacao: faltando=%s divergentes=%s" % (faltando or "nenhum", divergentes or "nenhum"))

    obsidian = sorted(p.name for p in DESTINO.glob("*.md")) + sorted(p.name for p in DESTINO.glob("*.canvas"))
    print("arquivos do Obsidian preservados: %s" % obsidian)
    return 0 if not faltando and not divergentes else 1


if __name__ == "__main__":
    sys.exit(main())

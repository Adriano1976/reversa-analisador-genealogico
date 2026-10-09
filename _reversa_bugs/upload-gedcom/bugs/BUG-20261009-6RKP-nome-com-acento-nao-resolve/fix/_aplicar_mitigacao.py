"""Mitigacao do BUG-20261009-6RKP: renomear os arquivos inalcancaveis por referencia.

APROVADO pelo operador em 2026-10-09 (gate de reparo de dados), na forma:
renomear os 4 arquivos com chave, com MANIFESTO em vez de copia fisica.
Os 3 sem chave NAO entram: sao duplicatas byte a byte de arquivos com chave, e renomear colidiria.

Garantias que este instrumento PROVA, e nao promete:
  1. o multiconjunto de sha256 da pasta e IDENTICO antes e depois (so nomes mudam, conteudo nao);
  2. cada nome novo passa em `chave_recebida_e_valida`;
  3. nenhum nome novo colide com arquivo existente (fail-closed);
  4. os arquivos que passam a ser alcancaveis sao exatamente os 4.
"""
from __future__ import annotations

import hashlib
import re
import sys
import unicodedata
from collections import Counter
from pathlib import Path

RAIZ = None


def _raiz(inicio: Path) -> Path:
    for c in [inicio, *inicio.parents]:
        if (c / "src" / "utils" / "validate.py").is_file() and (c / "_reversa_forward").is_dir():
            return c
    raise SystemExit("raiz nao encontrada")


RAIZ = _raiz(Path(__file__).resolve().parent)
PASTA = RAIZ / "src" / "uploads"
FIX = Path(__file__).resolve().parent
sys.path.insert(0, str(RAIZ / "src"))

from utils.validate import chave_recebida_e_valida, nome_visivel_seguro  # noqa: E402

_PREFIXO_CHAVE = re.compile(r"^[0-9a-f]{16}__")


def sha256_bytes(dados: bytes) -> str:
    return hashlib.sha256(dados).hexdigest()


def inventario() -> dict[str, tuple[str, int]]:
    """nome -> (sha256, bytes)"""
    saida = {}
    for p in sorted(PASTA.iterdir()):
        if p.is_file():
            b = p.read_bytes()
            saida[p.name] = (sha256_bytes(b), len(b))
    return saida


def multiconjunto(inv: dict[str, tuple[str, int]]) -> Counter:
    """Contagem por (sha256, bytes). E o que prova que so os NOMES mudaram."""
    return Counter(v for v in inv.values())


def asciiizar(nome: str) -> str:
    return "".join(c for c in unicodedata.normalize("NFD", nome)
                   if unicodedata.category(c) != "Mn").replace(" ", "_")


def main() -> None:
    antes = inventario()
    antes_mc = multiconjunto(antes)
    linhas: list[str] = []

    def log(t: str = "") -> None:
        print(t)
        linhas.append(t)

    log("# Mitigacao aplicada ao BUG-20261009-6RKP")
    log()
    log(f"Data: 2026-10-09.  Pasta: `src/uploads`.")
    log(f"Antes: {len(antes)} arquivos, {sum(v[1] for v in antes.values())} bytes.")
    log()

    # --- plano, recalculado na hora (fail-closed) ---
    aplicaveis: list[tuple[str, str]] = []
    recusados_sem_chave: list[str] = []
    for nome in sorted(antes):
        if chave_recebida_e_valida(nome):
            continue
        if _PREFIXO_CHAVE.match(nome):
            chave, visivel = nome.split("__", 1)
            novo = f"{chave}__{asciiizar(visivel)}"
            if not chave_recebida_e_valida(novo):
                raise SystemExit(f"ABORTADO: nome novo invalido para {nome!r}: {novo!r}")
            if (PASTA / novo).exists():
                raise SystemExit(f"ABORTADO: colisao — {novo!r} ja existe")
            if nome_visivel_seguro(asciiizar(visivel)) != asciiizar(visivel):
                raise SystemExit(f"ABORTADO: o gravador alteraria {novo!r}")
            aplicaveis.append((nome, novo))
        else:
            recusados_sem_chave.append(nome)

    log("## Renomeacoes aplicadas")
    log()
    log("| Nome antes | Nome depois | sha256 (do conteudo) | Bytes |")
    log("|---|---|---|---|")
    for nome, novo in aplicaveis:
        h, n = antes[nome]
        (PASTA / nome).rename(PASTA / novo)
        log(f"| `{nome}` | `{novo}` | `{h[:16]}` | {n} |")

    depois = inventario()
    depois_mc = multiconjunto(depois)

    log()
    log("## Prova 1: so os nomes mudaram")
    log()
    log(f"- multiconjunto de `sha256`+bytes ANTES:  {sum(antes_mc.values())} arquivos, "
        f"{len(antes_mc)} conteudos distintos")
    log(f"- multiconjunto de `sha256`+bytes DEPOIS: {sum(depois_mc.values())} arquivos, "
        f"{len(depois_mc)} conteudos distintos")
    log(f"- **identicos? {'SIM' if antes_mc == depois_mc else 'NAO'}**")
    if antes_mc != depois_mc:
        raise SystemExit("ABORTADO: o conteudo da pasta mudou — reverter e investigar")

    log()
    log("## Prova 2: alcance por referencia, depois")
    log()
    ainda = [n for n in sorted(depois) if not chave_recebida_e_valida(n)]
    log(f"- alcancaveis: {len(depois) - len(ainda)} de {len(depois)}")
    log(f"- ainda inalcancaveis: {len(ainda)}")
    for n in ainda:
        log(f"  - `{n}`")

    log()
    log("## O que a mitigacao NAO resolve (vai para o fix)")
    log()
    for n in recusados_sem_chave:
        h, _ = depois[n]
        gemeos = [m for m, (hh, _) in depois.items() if hh == h and m != n]
        log(f"- `{n}` — sem chave no nome, e **duplicata byte a byte** de "
            f"{', '.join('`' + g + '`' for g in gemeos) or 'nenhum'}. "
            f"Renomear para a chave do gemeo colidiria; nao ha renomeacao possivel.")

    log()
    log("## Referencias historicas")
    log()
    log("Documentos em `_reversa_forward/`, `_reversa_sdd/` e `_reversa_bugs/` que citam os nomes")
    log("ANTIGOS continuam citando-os: sao registro historico e nao serao reescritos. O mapeamento")
    log("acima e o que permite reler esses documentos. Mitigacao e `temporary: true` — o fix decide")
    log("qual lado da contradicao cede, e o resultado pode tornar estas renomeacoes desnecessarias.")

    (FIX / "manifesto-renomeacao.md").write_text("\n".join(linhas) + "\n", encoding="utf-8")
    (FIX / "renomeacao.txt").write_text("\n".join(linhas) + "\n", encoding="utf-8")
    print()
    print("manifesto:", FIX / "manifesto-renomeacao.md")


if __name__ == "__main__":
    main()

"""Dry-run da mitigacao: renomear os arquivos inalcancaveis por referencia.

NAO ESCREVE NADA. So calcula o plano, confere os nomes novos contra a forma fechada e procura
colisoes, referencias no repositorio e duplicatas.

Regra da mitigacao: preservar a CHAVE (que vem do conteudo) e tornar o NOME VISIVEL ASCII.
"""
from __future__ import annotations

import hashlib
import os
import re
import sys
import unicodedata
from pathlib import Path

def _raiz_do_repositorio(inicio: Path) -> Path:
    """Sobe ate achar a raiz que tenha `src/` e `_reversa_forward/` (contar `parents[N]` e fragil)."""
    for candidato in [inicio, *inicio.parents]:
        if (candidato / "src" / "utils" / "validate.py").is_file() and (candidato / "_reversa_forward").is_dir():
            return candidato
    raise SystemExit("nao achei a raiz do repositorio a partir de " + str(inicio))


RAIZ = _raiz_do_repositorio(Path(__file__).resolve().parent)
PASTA = RAIZ / "src" / "uploads"
sys.path.insert(0, str(RAIZ / "src"))

from utils.validate import (  # noqa: E402
    chave_recebida_e_valida,
    nome_visivel_seguro,
)

# O prefixo de chave, SOZINHO. Nao serve `_FORMATO_CHAVE` aqui: ele exige o nome INTEIRO valido,
# e todo nome desta lista ja falhou nessa validacao (e por isso esta na lista).
_PREFIXO_CHAVE = re.compile(r"^[0-9a-f]{16}__")


def asciiizar(nome: str) -> str:
    """Remove acentos (NFD + descarte de marcas) e troca espaco por underscore."""
    sem_acento = "".join(c for c in unicodedata.normalize("NFD", nome)
                         if unicodedata.category(c) != "Mn")
    return sem_acento.replace(" ", "_")


def sha256(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


def main() -> None:
    arquivos = sorted(p for p in PASTA.iterdir() if p.is_file())
    print(f"pasta: {PASTA}")
    print(f"arquivos: {len(arquivos)}, bytes: {sum(p.stat().st_size for p in arquivos)}")
    print()

    recusados = [p for p in arquivos if not chave_recebida_e_valida(p.name)]
    print(f"recusados por referencia: {len(recusados)}")
    print()

    # --- duplicatas por conteudo, para tratar os sem chave ---
    por_hash: dict[str, list[str]] = {}
    for p in arquivos:
        por_hash.setdefault(sha256(p), []).append(p.name)

    aplicaveis: list[tuple[Path, str]] = []
    nao_aplicaveis: list[tuple[Path, str]] = []

    print("=" * 100)
    print("PLANO")
    print("=" * 100)
    for p in recusados:
        nome = p.name
        if _PREFIXO_CHAVE.match(nome):
            visivel = nome.split("__", 1)[1]
            chave = nome.split("__", 1)[0]
            novo_visivel = asciiizar(visivel)
            novo = f"{chave}__{novo_visivel}"
            ja_existe = (PASTA / novo).exists()
            passa = chave_recebida_e_valida(novo)
            print()
            print(f"  ATUAL     {nome}")
            print(f"  NOVO      {novo}")
            print(f"  passa?    {passa}   colide com arquivo existente? {ja_existe}")
            if passa and not ja_existe and novo != nome:
                aplicaveis.append((p, novo))
            else:
                nao_aplicaveis.append((p, "nome novo invalido ou colidente"))
        else:
            h = sha256(p)
            gemeos = [n for n in por_hash[h] if n != nome]
            print()
            print(f"  ATUAL     {nome}")
            print(f"  SEM CHAVE: a forma exige 16 hexadecimais. Nao ha como renomear sem INVENTAR uma chave.")
            print(f"  conteudo  sha256 {h[:16]}...  gemeos com chave: {gemeos or 'NENHUM'}")
            if gemeos:
                print(f"  -> e DUPLICATA de {gemeos[0]}; renomear para a chave do gemeo COLIDIRIA com ele.")
                nao_aplicaveis.append((p, "sem chave e duplicata de arquivo com chave"))
            else:
                nao_aplicaveis.append((p, "sem chave, sem gemeo: renomear exigiria inventar chave"))

    print()
    print("=" * 100)
    print(f"APLICAVEIS: {len(aplicaveis)}")
    for p, novo in aplicaveis:
        print(f"   {p.name}  ->  {novo}   ({p.stat().st_size} bytes)")
    print()
    print(f"NAO APLICAVEIS: {len(nao_aplicaveis)}")
    for p, motivo in nao_aplicaveis:
        print(f"   {p.name}   ({motivo})")

    # --- o nome visivel novo continua preservado pelo gravador? ---
    print()
    print("=" * 100)
    print("CONSISTENCIA COM O GRAVADOR (nome_visivel_seguro nao deve alterar o que eu proponho)")
    for _, novo in aplicaveis:
        chave, visivel = novo.split("__", 1)
        recomposto = nome_visivel_seguro(visivel)
        marca = "OK" if recomposto == visivel else f"DIVERGE -> {recomposto}"
        print(f"   {visivel:<44} {marca}")

    # --- referencias no repositorio ---
    print()
    print("=" * 100)
    print("REFERENCIAS AOS NOMES ATUAIS DENTRO DO REPOSITORIO (fora da pasta de uploads)")
    alvos = [p.name for p, _ in aplicaveis] + [p.name for p, _ in nao_aplicaveis]
    achados = 0
    for raiz in (RAIZ / "src", RAIZ / "tests", RAIZ / "_reversa_sdd", RAIZ / "_reversa_forward",
                 RAIZ / "_reversa_bugs", RAIZ / "docker", RAIZ / "docs"):
        if not raiz.exists():
            continue
        for caminho in raiz.rglob("*"):
            if not caminho.is_file() or caminho.stat().st_size > 2_000_000:
                continue
            if caminho.suffix.lower() in {".png", ".jpg", ".xlsx", ".ged", ".csv", ".pyc"}:
                continue
            try:
                texto = caminho.read_text(encoding="utf-8", errors="ignore")
            except OSError:
                continue
            for alvo in alvos:
                if alvo in texto:
                    print(f"   {caminho.relative_to(RAIZ)}  menciona  {alvo}")
                    achados += 1
    if not achados:
        print("   nenhuma referencia encontrada")


if __name__ == "__main__":
    main()

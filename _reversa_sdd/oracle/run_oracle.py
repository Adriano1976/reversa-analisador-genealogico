#!/usr/bin/env python
"""
run_oracle.py — Runner do oráculo congelado do Reversa.

Executa o monolito original (`app_legacy_e43ca22.py`, extraído do commit e43ca22)
em ISOLAMENTO e imprime um resumo verificável do comportamento.

Por que este runner existe (e por que não executar o app.py do legado):
    `analisador-genealogico/app.py` foi reduzido de 887 para 86 linhas pelo commit
    3ed0179 e HOJE é um wrapper que importa `reconstructed/`. Usá-lo como oráculo
    produziria VALIDAÇÃO CIRCULAR (RISK-002). Ver ORACLE_MANIFEST.md.

Duas armadilhas que este runner neutraliza:
    1. O import do oráculo executa os.makedirs("uploads") e os.makedirs("static")
       com caminhos RELATIVOS (L15-18). Por isso copiamos o oráculo para um
       diretório de execução e fazemos chdir ANTES de importar. Assim ele nunca
       polui o repositório nem toca nos dados reais em analisador-genealogico/uploads/.
    2. As saídas contêm '↔' (U+2194), que o console Windows (cp1252) não codifica.
       Por isso forçamos UTF-8 em stdout.

O oráculo é SOMENTE LEITURA. Este runner nunca escreve no legado.
"""
from __future__ import annotations

import argparse
import importlib.util
import os
import shutil
import sys

# UTF-8 em stdout, antes de qualquer print (armadilha 2)
try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

ORACLE_NAME = "app_legacy_e43ca22.py"
DEFAULT_RELATIVE_ORACLE = os.path.join("_reversa_sdd", "oracle", ORACLE_NAME)
DEFAULT_RELATIVE_UPLOADS = os.path.join("analisador-genealogico", "uploads")
RUN_DIR_NAME = ".oracle-run"


def repo_root() -> str:
    """Sobe a partir deste arquivo até a raiz do projeto (onde está AGENTS.md)."""
    here = os.path.dirname(os.path.abspath(__file__))
    cur = here
    for _ in range(8):
        if os.path.exists(os.path.join(cur, "AGENTS.md")):
            return cur
        parent = os.path.dirname(cur)
        if parent == cur:
            break
        cur = parent
    return os.path.dirname(os.path.dirname(here))  # fallback: _reversa_sdd/.. -> raiz


def load_oracle(root: str):
    """Importa o oráculo isolado em diretório de execução (armadilha 1)."""
    oracle_path = os.path.join(root, DEFAULT_RELATIVE_ORACLE)
    if not os.path.exists(oracle_path):
        sys.exit(
            "ERRO: oráculo não encontrado em %s\n"
            "Extraia-o com:\n"
            "  git show e43ca22:analisador-genealogico/app.py > <destino>\n"
            "ATENÇÃO: no PowerShell, '>' grava UTF-16 e corrompe o arquivo.\n"
            "Use extração byte-exata (ver ORACLE_MANIFEST.md) ou git cat-file." % oracle_path
        )

    run_dir = os.path.join(root, RUN_DIR_NAME)
    shutil.rmtree(run_dir, ignore_errors=True)
    os.makedirs(run_dir)

    local = os.path.join(run_dir, "app_legacy.py")
    shutil.copyfile(oracle_path, local)

    previous_cwd = os.getcwd()
    os.chdir(run_dir)  # neutraliza o makedirs relativo do oráculo
    try:
        spec = importlib.util.spec_from_file_location("oracle", local)
        module = importlib.util.module_from_spec(spec)
        sys.modules["oracle"] = module
        spec.loader.exec_module(module)
    finally:
        os.chdir(previous_cwd)
    return module, run_dir


def main() -> int:
    root = repo_root()
    parser = argparse.ArgumentParser(
        description="Executa o oráculo congelado e mostra um resumo verificável."
    )
    parser.add_argument(
        "--gedcom",
        default=None,
        help="Caminho do .ged a parsear. Padrão: o maior .ged em analisador-genealogico/uploads/.",
    )
    parser.add_argument(
        "--cm",
        type=float,
        default=None,
        help="Valor de cM para consultar a tabela de relação (ex.: --cm 50).",
    )
    parser.add_argument(
        "--quiet", action="store_true", help="Imprime apenas OK/FALHA (para uso em script)."
    )
    args = parser.parse_args()

    module, run_dir = load_oracle(root)

    # escolhe o GEDCOM
    gedcom = args.gedcom
    if gedcom is None:
        uploads = os.path.join(root, DEFAULT_RELATIVE_UPLOADS)
        if not os.path.isdir(uploads):
            print("AVISO: pasta de uploads não encontrada; nenhum GEDCOM para parsear.")
            print("ORACULO CARREGADO OK (sem parse)")
            shutil.rmtree(run_dir, ignore_errors=True)
            return 0
        cands = [
            os.path.join(uploads, f)
            for f in os.listdir(uploads)
            if f.lower().endswith(".ged")
        ]
        if not cands:
            print("AVISO: nenhum .ged em %s" % uploads)
            print("ORACULO CARREGADO OK (sem parse)")
            shutil.rmtree(run_dir, ignore_errors=True)
            return 0
        gedcom = max(cands, key=os.path.getsize)

    if not os.path.exists(gedcom):
        shutil.rmtree(run_dir, ignore_errors=True)
        sys.exit("ERRO: GEDCOM não encontrado: %s" % gedcom)

    try:
        names = module.load_gedcom_and_build_graph(gedcom)
        people = len(module.people)
        families = len(module.families)
        nodes = module.graph.number_of_nodes()
        edges = module.graph.number_of_edges()
        sorted_ok = names == sorted(names)

        if args.quiet:
            print("OK pessoas=%d familias=%d nos=%d arestas=%d" % (people, families, nodes, edges))
        else:
            print("ORACULO OK")
            print("  gedcom   : %s (%d bytes)" % (os.path.basename(gedcom), os.path.getsize(gedcom)))
            print("  pessoas  : %d" % people)
            print("  familias : %d" % families)
            print("  grafo    : %d nos / %d arestas" % (nodes, edges))
            print("  nomes    : %d | ordenados alfabeticamente: %s" % (len(names), sorted_ok))
            if names:
                print("  1o nome  : %s" % names[0])

        if args.cm is not None:
            rel = module.get_relationships_by_cm(args.cm)
            if args.quiet:
                print("cm=%g faixas=%d" % (args.cm, len(rel)))
            else:
                print("  %g cM   -> %d faixa(s): %s" % (args.cm, len(rel), " | ".join(rel) or "(lista vazia)"))
                print("           ^^ o oraculo retorna LISTA: as faixas se sobrepoem.")
    finally:
        shutil.rmtree(run_dir, ignore_errors=True)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())

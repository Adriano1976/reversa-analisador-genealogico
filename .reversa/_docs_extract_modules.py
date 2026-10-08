"""Extrator determinista de modules.json e deps.json para o mini-site /reversa-docs.

Le a arvore de codigo atual do projeto legado (src/, tests/) e produz:
  - _reversa_docs/assets/data/modules.json  (um registro por arquivo, LOC nao-vazio,
    complexidade por contagem de nos de decisao do AST, docstring como descricao)
  - _reversa_docs/assets/data/deps.json     (grafo agregado por pacote de primeiro nivel,
    com deteccao de ciclos via networkx)

Uso: python .reversa/_docs_extract_modules.py
"""
import sys

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except AttributeError:
        pass

import ast
import json
import os
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUT_MODULES = ROOT / "_reversa_docs" / "assets" / "data" / "modules.json"
OUT_DEPS = ROOT / "_reversa_docs" / "assets" / "data" / "deps.json"

SKIP_DIRS = {".git", ".venv", "venv", "__pycache__", "node_modules", ".reversa",
             "_reversa_sdd", "_reversa_docs", "_reversa_forward", ".agents",
             ".pytest_cache", ".vscode", ".mypy_cache", ".ruff_cache"}

DECISION_NODES = (ast.If, ast.For, ast.AsyncFor, ast.While, ast.ExceptHandler,
                  ast.BoolOp, ast.IfExp, ast.comprehension, ast.Assert,
                  ast.Match, ast.Try)

# Pasta de origem -> tipo do modulo. Regra mecanica, declarada no proprio JSON.
TYPE_BY_TOP = {
    "application": "application",
    "core": "domain",
    "parsers": "parser",
    "ports": "port",
    "reporting": "reporting",
    "utils": "utility",
}

DESCRICOES_MANUAIS = {
    "src/app.py": "Camada web Flask: rota unica / com despacho por action (upload_gedcom, path_analysis, dna_analysis) e inicializacao do servidor de producao.",
}

FOLDER_LABEL = {
    "src/": "src/",
    "src/application/": "application/",
    "src/core/": "core/",
    "src/parsers/": "parsers/",
    "src/ports/": "ports/",
    "src/reporting/": "reporting/",
    "src/utils/": "utils/",
    "src/templates/": "templates/",
    "tests/": "tests/",
    "tests/fixtures/": "tests/fixtures/",
}


def rel(p: Path) -> str:
    return p.relative_to(ROOT).as_posix()


def iter_source_files():
    exts = {".py", ".html", ".js", ".css"}
    for top in ("src", "tests"):
        base = ROOT / top
        if not base.is_dir():
            continue
        for dirpath, dirnames, filenames in os.walk(base):
            dirnames[:] = [d for d in dirnames if d not in SKIP_DIRS]
            for fn in sorted(filenames):
                p = Path(dirpath) / fn
                if p.suffix.lower() in exts:
                    yield p


def nonempty_loc(p: Path) -> int:
    try:
        txt = p.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return 0
    return sum(1 for line in txt.splitlines() if line.strip())


def parse_py(p: Path):
    try:
        src = p.read_text(encoding="utf-8", errors="replace")
        tree = ast.parse(src)
    except (OSError, SyntaxError):
        return None, None, None
    return src, tree, ast.get_docstring(tree, clean=True)


def count_complexity(tree) -> int:
    if tree is None:
        return 0
    return sum(1 for n in ast.walk(tree) if isinstance(n, DECISION_NODES))


def count_defs(tree):
    if tree is None:
        return 0, 0
    fns = sum(1 for n in ast.walk(tree) if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef)))
    cls = sum(1 for n in ast.walk(tree) if isinstance(n, ast.ClassDef))
    return fns, cls


def first_sentence(text: str, limit: int = 240) -> str:
    if not text:
        return ""
    line = " ".join(text.strip().split())
    for sep in (". ", ".\n"):
        if sep in line:
            line = line.split(sep)[0] + "."
            break
    if len(line) > limit:
        line = line[: limit - 1].rstrip() + "..."
    return line


def classify(p: Path) -> tuple:
    """Devolve (type, folder, id)."""
    r = rel(p)
    parts = r.split("/")
    name = p.name

    if name == "__init__.py":
        pkgdir = "/".join(parts[:-1]) + "/"
        folder = FOLDER_LABEL.get(pkgdir, pkgdir)
        mid = "pkg-%s" % parts[-2] if len(parts) >= 2 else "pkg-root"
        return "config", folder, mid
    if r.startswith("src/templates/"):
        return "frontend", "templates/", "frontend"
    if r.startswith("tests/fixtures/"):
        return "fixture", "tests/fixtures/", Path(name).stem.replace("_", "-")
    if r.startswith("tests/"):
        base = Path(name).stem
        if base.startswith("test_"):
            base = base[len("test_"):]
        return "test", "tests/", base.replace("_", "-")
    if r == "src/app.py":
        return "entrypoint", "src/", "app"

    top = parts[1] if len(parts) > 2 else ""
    mtype = TYPE_BY_TOP.get(top, "domain")
    folder = FOLDER_LABEL.get("src/%s/" % top, "src/%s/" % top)
    return mtype, folder, Path(name).stem.replace("_", "-")


def module_entry(p: Path):
    r = rel(p)
    mtype, folder, mid = classify(p)
    loc = nonempty_loc(p)
    src, tree, doc = (None, None, None)
    fns = cls = 0
    cx = 0
    if p.suffix.lower() == ".py":
        src, tree, doc = parse_py(p)
        fns, cls = count_defs(tree)
        cx = count_complexity(tree)
    desc = DESCRICOES_MANUAIS.get(r) or first_sentence(doc or "")
    return {
        "id": mid,
        "name": p.name,
        "path": r,
        "type": mtype,
        "language": {"py": "python", "html": "html", "js": "javascript", "css": "css"}[p.suffix.lstrip(".").lower()],
        "folder": folder,
        "loc": loc,
        "complexity": cx,
        "functions": fns,
        "classes": cls,
        "description": desc,
    }


def internal_edges(files):
    """Arestas de import entre pacotes de primeiro nivel (src/ e a raiz de import)."""
    tops = {}
    for p in files:
        if p.suffix != ".py" or "__pycache__" in p.parts:
            continue
        r = rel(p)
        if r.startswith("src/"):
            pkg = r.split("/")[1] if r.count("/") > 1 else "app"
            pkg = "app" if r == "src/app.py" else pkg
        elif r.startswith("tests/"):
            pkg = "tests"
        else:
            continue
        tops.setdefault(pkg, []).append(p)

    edges = set()
    detail = []
    for pkg, plist in sorted(tops.items()):
        for p in plist:
            src, tree, _ = parse_py(p)
            if tree is None:
                continue
            for node in ast.walk(tree):
                alvo = None
                if isinstance(node, ast.Import):
                    for a in node.names:
                        alvo = a.name.split(".")[0]
                        if alvo in tops and alvo != pkg:
                            edges.add((pkg, alvo))
                            detail.append({"from": rel(p), "import": a.name, "to": alvo})
                        elif alvo not in ("os", "sys", "json", "re", "ast", "socket", "errno", "csv",
                                          "math", "collections", "itertools", "dataclasses", "typing",
                                          "pathlib", "hashlib", "unicodedata", "time", "functools",
                                          "datetime", "io", "tempfile", "shutil", "threading", "logging",
                                          "unittest", "pytest", "flask", "ged4py", "networkx", "pandas",
                                          "thefuzz", "rapidfuzz", "waitress", "werkzeug", "jinja2"):
                            detail.append({"from": rel(p), "import": a.name, "to": "externo"})
                elif isinstance(node, ast.ImportFrom):
                    if node.level and node.level > 0:
                        # import relativo: resolve pelo pacote do proprio arquivo
                        base = p.parent
                        for _ in range(node.level - 1):
                            base = base.parent
                        alvo = node.module.split(".")[0] if node.module else base.name
                    else:
                        alvo = (node.module or "").split(".")[0]
                    if alvo in tops and alvo != pkg:
                        edges.add((pkg, alvo))
                        detail.append({"from": rel(p), "import": node.module or ".", "to": alvo})
                    elif alvo and alvo not in tops:
                        if alvo not in ("os", "sys", "json", "re", "ast", "socket", "errno", "csv",
                                        "math", "collections", "itertools", "dataclasses", "typing",
                                        "pathlib", "hashlib", "unicodedata", "time", "functools",
                                        "datetime", "io", "tempfile", "shutil", "threading", "logging",
                                        "unittest", "pytest", "flask", "ged4py", "networkx", "pandas",
                                        "thefuzz", "rapidfuzz", "waitress", "werkzeug", "jinja2"):
                            detail.append({"from": rel(p), "import": alvo, "to": "externo"})
    return sorted(edges), detail


def detect_cycles(nodes, edges):
    try:
        import networkx as nx
    except ImportError:
        return []
    g = nx.DiGraph()
    g.add_nodes_from(nodes)
    g.add_edges_from(edges)
    return [list(c) for c in nx.simple_cycles(g)]


def main():
    files = sorted(iter_source_files())
    modules = [module_entry(p) for p in files]
    modules = [m for m in modules if m["loc"] > 0]

    total_loc = sum(m["loc"] for m in modules)
    src_py = [m for m in modules if m["path"].startswith("src/") and m["language"] == "python"]
    tst = [m for m in modules if m["path"].startswith("tests/")]
    now = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

    mod_doc = {
        "schemaVersion": 1,
        "generatedAt": now,
        "project": "analisador-genealogico",
        "language": "Python/Flask",
        "extraction": {
            "method": "inline (templates/documentation/scripts/extract_modules.py ausente nesta instalacao)",
            "loc": "linhas nao-vazias",
            "complexity": "contagem de nos de decisao do AST (If, For, While, ExceptHandler, BoolOp, IfExp, comprehension, Assert, Match, Try)",
            "description": "primeira frase da docstring do modulo, ou texto curado a mao quando nao ha docstring",
            "typeRule": "papel derivado da pasta de origem",
        },
        "summary": {
            "modules": len(modules),
            "locTotal": total_loc,
            "locSrcPython": sum(m["loc"] for m in src_py),
            "locTests": sum(m["loc"] for m in tst),
            "byFolder": {},
            "byType": {},
            "complexityTotal": sum(m["complexity"] for m in modules),
        },
        "modules": sorted(modules, key=lambda m: (-m["loc"], m["path"])),
    }
    for m in modules:
        mod_doc["summary"]["byFolder"][m["folder"]] = mod_doc["summary"]["byFolder"].get(m["folder"], 0) + m["loc"]
        mod_doc["summary"]["byType"][m["type"]] = mod_doc["summary"]["byType"].get(m["type"], 0) + 1

    edges, detail = internal_edges(files)
    nodes = sorted({e[0] for e in edges} | {e[1] for e in edges})
    cycles = detect_cycles(nodes, edges)

    deps_doc = {
        "schemaVersion": 1,
        "generatedAt": now,
        "project": "analisador-genealogico",
        "language": "Python/Flask",
        "aggregation": "pacote de primeiro nivel (src/ e a raiz de import: app, core, parsers, reporting, utils, tests)",
        "nodes": nodes,
        "edges": [{"source": a, "target": b} for a, b in edges],
        "cycles": cycles,
        "imports": detail,
        "summary": {
            "nodes": len(nodes),
            "edges": len(edges),
            "cycles": len(cycles),
            "internalImports": len(detail),
        },
    }

    OUT_MODULES.parent.mkdir(parents=True, exist_ok=True)
    OUT_MODULES.write_text(json.dumps(mod_doc, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    OUT_DEPS.write_text(json.dumps(deps_doc, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    print("modules.json: %d modulos, %d LOC nao-vazio" % (len(modules), total_loc))
    print("  por pasta: %s" % mod_doc["summary"]["byFolder"])
    print("  por tipo:  %s" % mod_doc["summary"]["byType"])
    print("  src python=%d  testes=%d  frontend=%s"
          % (mod_doc["summary"]["locSrcPython"], mod_doc["summary"]["locTests"],
             [m["loc"] for m in modules if m["type"] == "frontend"]))
    print("deps.json: %d nos, %d arestas, %d ciclos" % (len(nodes), len(edges), len(cycles)))
    for c in cycles:
        print("  ciclo: %s" % " -> ".join(c + [c[0]]))
    sem = [m["path"] for m in modules if m["language"] == "python" and not m["description"]]
    if sem:
        print("sem descricao (%d): %s" % (len(sem), sem))


if __name__ == "__main__":
    main()

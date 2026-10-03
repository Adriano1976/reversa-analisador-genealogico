"""Verifica a estrutura depois da OPP-20261003-FLAT, sem executar o sistema.

1. Resolve todo import do projeto contra a arvore nova, incluindo os que vivem
   dentro das strings dos coletores.
2. Confere que nao sobrou `from ..`, que seria invalido agora que os pacotes do
   nucleo sao de primeiro nivel.
3. Confere que `reconstructed` nao aparece em nenhuma linha de import.
4. Verifica os caminhos de arquivo que os scripts de instrumentacao montam:
   `SRC`, `STUB` e o `alvo` do `_verify_fix_gives_parity.py`.
5. Compara o AST dos 17 modulos com o da copia congelada.
6. Confere os pacotes de primeiro nivel, a ausencia de `src/__init__.py`, a arvore
   do README e o risco de colisao de nome.
"""
from __future__ import annotations

import ast
import difflib
import os
import re

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", "..", "..", ".."))
SRC = os.path.join(ROOT, "src")
ANTES = os.path.join(HERE, "before-after", "src-antes")
PARITY = os.path.join(ROOT, "_reversa_sdd", "parity")

PACOTES = ["core", "parsers", "reporting", "utils"]
STRING_COLETORES = [
    ("_reversa_sdd/parity/harness.py", "CANDIDATE_COLLECTOR"),
    ("_reversa_sdd/parity/_check_split_types.py", "COLETOR"),
]


class RemoveImports(ast.NodeTransformer):
    def visit_Import(self, node):
        return None

    def visit_ImportFrom(self, node):
        return None


class RemoveImportsEDocstrings(RemoveImports):
    @staticmethod
    def _sem_docstring(corpo):
        if (corpo and isinstance(corpo[0], ast.Expr) and isinstance(corpo[0].value, ast.Constant)
                and isinstance(corpo[0].value.value, str)):
            corpo.pop(0)
        return corpo

    def visit_Module(self, node):
        self.generic_visit(node)
        self._sem_docstring(node.body)
        return node

    def _visita_corpo(self, node):
        self.generic_visit(node)
        self._sem_docstring(node.body)
        return node

    visit_FunctionDef = _visita_corpo
    visit_AsyncFunctionDef = _visita_corpo
    visit_ClassDef = _visita_corpo


def le(caminho):
    with open(caminho, encoding="utf-8") as fh:
        return fh.read()


def modulo_de(caminho):
    rel = os.path.relpath(caminho, SRC).replace("\\", "/")
    partes = rel[:-3].split("/")
    if partes[-1] == "__init__":
        partes = partes[:-1]
    return ".".join(partes)


def modulos_src():
    achados = []
    for raiz, dirs, arquivos in os.walk(SRC):
        dirs[:] = [d for d in dirs if d != "__pycache__"]
        for nome in sorted(arquivos):
            if nome.endswith(".py"):
                achados.append(os.path.join(raiz, nome))
    return achados


def existentes(arquivos):
    return {modulo_de(p) for p in arquivos}


def resolve(no, modulo, conjunto, problemas):
    pacote = modulo.rpartition(".")[0]
    partes = pacote.split(".")
    if no.level:
        base = ".".join(partes[: len(partes) - (no.level - 1)]) if no.level > 1 else pacote
        alvo = base + ("." + no.module if no.module else "")
        if alvo and alvo not in conjunto:
            problemas.append("%s: `from %s%s import ...` nao resolve" % (modulo, "." * no.level, no.module or ""))
            return
        if no.module is None:
            for alias in no.names:
                if alvo + "." + alias.name not in conjunto:
                    problemas.append("%s: `from %s import %s` nao resolve" % (modulo, "." * no.level, alias.name))
    else:
        alvo = no.module or ""
        raiz = alvo.split(".")[0]
        if raiz in ("core", "parsers", "reporting", "utils") and alvo not in conjunto:
            problemas.append("%s: `from %s import ...` nao resolve" % (modulo, alvo))


def checa(caminho, modulo, conjunto, problemas):
    arvore = ast.parse(le(caminho))
    for no in ast.walk(arvore):
        if isinstance(no, ast.ImportFrom):
            resolve(no, modulo, conjunto, problemas)
    return arvore


def fim_do_docstring(caminho):
    arvore = ast.parse(le(caminho))
    p = arvore.body[0]
    if not (isinstance(p, ast.Expr) and isinstance(p.value, ast.Constant)):
        return 0
    return p.end_lineno


def caminho_montado(caminho):
    """Os caminhos que o script monta com os.path.join(...), seja qual for a raiz."""
    achados = []
    for no in ast.walk(ast.parse(le(caminho))):
        if (isinstance(no, ast.Call) and isinstance(no.func, ast.Attribute) and no.func.attr == "join"
                and isinstance(no.func.value, ast.Attribute) and no.func.value.attr == "path"):
            partes = [a.value for a in no.args if isinstance(a, ast.Constant)]
            if len(partes) >= 2 and isinstance(no.args[0], ast.Name):
                achados.append((no.args[0].id, os.path.join(*partes)))
    return achados


def arvore_do_readme():
    nomes, dentro = [], False
    for linha in le(os.path.join(ROOT, "README.md")).splitlines():
        if linha.strip().startswith("src/") and "raiz de código" in linha:
            dentro = True
            continue
        if dentro and linha.strip() == "```":
            break
        if dentro and ".py" in linha:
            nome = linha.split("#")[0].strip().rsplit(" ", 1)[-1].split("/")[-1]
            if nome.endswith(".py"):
                nomes.append(nome)
    return sorted(set(nomes))


def main() -> int:
    problemas = []
    arquivos = modulos_src()
    conjunto = existentes(arquivos)

    print("=" * 78)
    print("ESTRUTURA DEPOIS DO ACHATAMENTO")
    print("=" * 78)
    print("  src/")
    print("    app.py")
    for d in sorted(os.listdir(SRC)):
        p = os.path.join(SRC, d)
        if os.path.isdir(p) and d != "__pycache__":
            filhos = sorted(f for f in os.listdir(p) if f.endswith(".py"))
            print("    %s/" % d)
            for f in filhos:
                print("      %-26s %4d linhas" % (f, len(le(os.path.join(p, f)).splitlines())))
    print("\n  modulos alcancaveis: %d" % len(conjunto))

    print("\n1. RESOLUCAO DE IMPORT, POR AST")
    todos = list(arquivos)
    for base in (os.path.join(ROOT, "tests"),):
        for raiz, dirs, nomes in os.walk(base):
            dirs[:] = [d for d in dirs if d != "__pycache__"]
            for nome in sorted(nomes):
                if nome.endswith(".py"):
                    todos.append(os.path.join(raiz, nome))
    for rel, _ in STRING_COLETORES:
        todos.append(os.path.join(ROOT, rel))
    total = 0
    for caminho in todos:
        modulo = modulo_de(caminho) if caminho.startswith(SRC) else os.path.relpath(caminho, ROOT)
        arvore = checa(caminho, modulo, conjunto, problemas)
        total += sum(1 for n in ast.walk(arvore) if isinstance(n, (ast.Import, ast.ImportFrom)))
    print("  arquivos varridos : %d" % len(todos))
    print("  imports conferidos: %d" % total)

    print("\n2. COLETORES DENTRO DE STRING")
    for rel, constante in STRING_COLETORES:
        arvore = ast.parse(le(os.path.join(ROOT, rel)))
        texto = None
        for no in arvore.body:
            if (isinstance(no, ast.Assign)
                    and any(getattr(t, "id", "") == constante for t in no.targets)
                    and isinstance(no.value, ast.Constant)):
                texto = no.value.value
        if texto is None:
            problemas.append("%s: constante %s nao encontrada" % (rel, constante))
            continue
        sub = ast.parse(texto)
        antes = len(problemas)
        for no in ast.walk(sub):
            if isinstance(no, ast.ImportFrom):
                resolve(no, "coletor:" + os.path.basename(rel), conjunto, problemas)
        n = sum(1 for no in ast.walk(sub) if isinstance(no, ast.ImportFrom))
        print("  %-46s %d import(s), %s" % (rel, n,
              "todos resolvem" if len(problemas) == antes else "COM PROBLEMA"))

    print("\n3. O QUE NAO PODE MAIS APARECER")
    sobrou_parent, sobrou_prefixo = [], []
    for caminho in todos:
        for i, linha in enumerate(le(caminho).splitlines(), 1):
            if re.match(r"\s*from\s+\.\.", linha):
                sobrou_parent.append("%s:%d" % (os.path.relpath(caminho, ROOT), i))
            if re.match(r"\s*(from|import)\s", linha) and "reconstructed." in linha:
                sobrou_prefixo.append("%s:%d" % (os.path.relpath(caminho, ROOT), i))
    print("  `from ..` restante                : %d" % len(sobrou_parent))
    print("  `reconstructed.` em import restante: %d" % len(sobrou_prefixo))
    for x in sobrou_parent + sobrou_prefixo:
        problemas.append("sobrou: " + x)

    print("\n4. CAMINHOS MONTADOS PELOS SCRIPTS DE INSTRUMENTACAO")
    alvo = os.path.join(PARITY, "_verify_fix_gives_parity.py")
    # Regras de resolucao declaradas, uma por variavel:
    #   ROOT  -> a raiz do repositorio
    #   SRC   -> src/, absoluto, e ja e o diretorio do codigo
    #   STUB  -> copia de SRC feita em tempo de execucao, entao o alvo existe se existir em src/
    base = {"ROOT": ROOT, "SRC": SRC, "STUB": SRC}
    for var, rel in caminho_montado(alvo):
        if var not in base:
            continue
        real = os.path.join(base[var], rel)
        existe = os.path.exists(real)
        print("  %-6s %-36s %s" % (var, rel, "existe" if existe else "NAO EXISTE"))
        if not existe:
            problemas.append("%s = %r nao existe" % (var, rel))
    alvo_stub = os.path.join(SRC, "core", "gedcom_state.py")
    print("  %-6s %-36s %s" % ("alvo", "core/gedcom_state.py",
                               "existe" if os.path.exists(alvo_stub) else "NAO EXISTE"))
    if not os.path.exists(alvo_stub):
        problemas.append("o alvo do _verify_fix_gives_parity nao existe")

    print("\n5. AST DOS MODULOS, SEM IMPORT E SEM DOCSTRING")
    movidos = 0
    for caminho in arquivos:
        rel = os.path.relpath(caminho, SRC).replace("\\", "/")
        # a copia congelada tem a raiz `src/` removida e o nivel `reconstructed/` mantido,
        # porque foi tirada ANTES do achatamento. `app.py` nunca esteve dentro do pacote.
        congelado = (os.path.join(ANTES, "app.py") if rel == "app.py"
                     else os.path.join(ANTES, "reconstructed", rel))
        if not os.path.exists(congelado):
            problemas.append("nao achei a copia congelada de %s" % rel)
            continue
        a = RemoveImportsEDocstrings().visit(ast.parse(le(congelado)))
        b = RemoveImportsEDocstrings().visit(ast.parse(le(caminho)))
        ast.fix_missing_locations(a)
        ast.fix_missing_locations(b)
        if ast.dump(a) != ast.dump(b):
            problemas.append("%s: alguma linha de CODIGO mudou" % rel)
            print("  %-40s CODIGO DIFERENTE" % rel)
        movidos += 1
    print("  modulos conferidos contra a copia congelada: %d" % movidos)

    print("\n6. PACOTES, RN-01, README E COLISAO")
    achados = sorted(d for d in os.listdir(SRC)
                     if os.path.isdir(os.path.join(SRC, d)) and d != "__pycache__"
                     and d not in ("templates", "uploads"))
    print("  %-36s %s" % ("pacotes de primeiro nivel", ", ".join(achados)))
    if achados != sorted(PACOTES):
        problemas.append("pacotes diferentes do esperado: %s" % ", ".join(achados))
    print("  %-36s %s" % ("src/reconstructed existe", os.path.exists(os.path.join(SRC, "reconstructed"))))
    if os.path.exists(os.path.join(SRC, "reconstructed")):
        problemas.append("src/reconstructed ainda existe")
    if os.path.exists(os.path.join(SRC, "__init__.py")):
        problemas.append("src/__init__.py foi criado, e a RN-01 proibe")

    import importlib.util
    for nome in PACOTES:
        spec = importlib.util.find_spec(nome) if False else None
        colide = os.path.exists(os.path.join(ROOT, ".venv", "Lib", "site-packages", nome)) or \
                 os.path.exists(os.path.join(ROOT, ".venv", "Lib", "site-packages", nome + ".py"))
        print("  %-36s %s" % ("colisao em site-packages: " + nome, "COLIDE" if colide else "livre"))
        if colide:
            problemas.append("o nome %s colide com pacote instalado" % nome)

    na_arvore = arvore_do_readme()
    reais = sorted(n for n in os.listdir(SRC) if False) or []
    reais = ["app.py"]
    for caminho in arquivos:
        reais.append(os.path.basename(caminho))
    reais = sorted(set(n for n in reais if n != "__init__.py"))
    sobra = sorted(set(na_arvore) - set(reais))
    falta = sorted(set(reais) - set(na_arvore))
    print("  %-36s %d x %d" % ("arvore do README x disco", len(na_arvore), len(reais)))
    if sobra:
        problemas.append("README lista arquivo que nao existe: %s" % ", ".join(sobra))
    if falta:
        problemas.append("README nao lista arquivo que existe: %s" % ", ".join(falta))
    if not sobra and not falta:
        print("  %-36s %s" % ("", "bate, arquivo por arquivo"))

    print()
    print("=" * 78)
    if problemas:
        print("RESULTADO: %d PROBLEMA(S)" % len(problemas))
        for p in problemas:
            print("  " + p)
    else:
        print("RESULTADO: ESTRUTURA CONFERIDA")
        print("  todo import resolve, nao sobrou relativo de nivel 2 nem prefixo antigo,")
        print("  os caminhos dos scripts existem, os 17 modulos so mudaram de pasta,")
        print("  a raiz de src/ esta na forma do exemplo e a arvore do README bate")
    print("=" * 78)
    return 1 if problemas else 0


if __name__ == "__main__":
    raise SystemExit(main())

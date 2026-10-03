"""Verifica a estrutura depois da OPP-20261003-GUE7, sem executar o sistema.

1. Monta o conjunto de nomes de modulo que existem em `src/` e resolve TODO import
   relativo e todo import de `reconstructed.*` contra ele. Um import que nao
   resolve e erro, mesmo que a suite nunca chegue nele.
2. Faz o mesmo para os dois coletores que vivem DENTRO DE STRING no harness de
   paridade e no `_check_split_types.py`. Este e o ponto que leitura de AST nao
   enxerga quando o alvo e o arquivo, e enxerga quando o alvo e o texto da string.
3. Compara o AST de cada modulo movido com o da copia congelada, tirando as linhas
   de import: prova que so o import mudou.
"""
from __future__ import annotations

import ast
import os

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", "..", "..", ".."))
SRC = os.path.join(ROOT, "src")
PACOTE = os.path.join(SRC, "reconstructed")
ANTES = os.path.join(HERE, "before-after", "src-antes")
PARITY = os.path.join(ROOT, "_reversa_sdd", "parity")

MOVES = [
    ("gedcom_parser.py", "parsers/gedcom_parser.py"),
    ("csv_ingest.py", "parsers/csv_ingest.py"),
    ("matching.py", "core/matching.py"),
    ("name_normalization.py", "core/name_normalization.py"),
    ("path_finding.py", "core/path_finding.py"),
    ("family_navigation.py", "core/family_navigation.py"),
    ("mermaid_render.py", "reporting/mermaid_render.py"),
]

STRING_COLETORES = [
    ("_reversa_sdd/parity/harness.py", "CANDIDATE_COLLECTOR"),
    ("_reversa_sdd/parity/_check_split_types.py", "COLETOR"),
]


class RemoveImports(ast.NodeTransformer):
    def visit_Import(self, node):
        return None

    def visit_ImportFrom(self, node):
        return None


def le(caminho):
    with open(caminho, encoding="utf-8") as fh:
        return fh.read()


def ast_sem_imports(caminho):
    arvore = RemoveImports().visit(ast.parse(le(caminho)))
    ast.fix_missing_locations(arvore)
    return ast.dump(arvore)


def modulo_de(caminho):
    """src/reconstructed/core/matching.py -> reconstructed.core.matching"""
    rel = os.path.relpath(caminho, SRC).replace("\\", "/")
    partes = rel[:-3].split("/")
    if partes[-1] == "__init__":
        partes = partes[:-1]
    return ".".join(partes)


def existentes():
    nomes = set()
    for raiz, dirs, arquivos in os.walk(SRC):
        dirs[:] = [d for d in dirs if d != "__pycache__"]
        for nome in arquivos:
            if nome.endswith(".py"):
                nomes.add(modulo_de(os.path.join(raiz, nome)))
    return nomes


def resolve(no, modulo, existentes_set, problemas):
    """Resolve um ImportFrom e reporta o que nao existe."""
    pacote = modulo.rpartition(".")[0]
    partes = pacote.split(".")

    if no.level:
        base = ".".join(partes[: len(partes) - (no.level - 1)]) if no.level > 1 else pacote
        alvo = base + ("." + no.module if no.module else "")
        if alvo and alvo not in existentes_set:
            problemas.append("%s: `from %s%s import ...` nao resolve" %
                             (modulo, "." * no.level, no.module or ""))
            return
        if no.module is None:
            for alias in no.names:
                sub = alvo + "." + alias.name
                if sub not in existentes_set:
                    problemas.append("%s: `from %s import %s` nao resolve" %
                                     (modulo, "." * no.level, alias.name))
    else:
        alvo = no.module or ""
        if alvo.startswith("reconstructed"):
            if alvo not in existentes_set:
                problemas.append("%s: `from %s import ...` nao resolve" % (modulo, alvo))
                return
            for alias in no.names:
                sub = alvo + "." + alias.name
                if sub not in existentes_set and sub.rpartition(".")[0] in existentes_set:
                    continue


def checa_arquivo(caminho, modulo, existentes_set, problemas, recolhidos):
    arvore = ast.parse(le(caminho))
    for no in ast.walk(arvore):
        if isinstance(no, ast.ImportFrom):
            recolhidos.append(no)
            resolve(no, modulo, existentes_set, problemas)
        elif isinstance(no, ast.Import):
            for alias in no.names:
                if alias.name.startswith("reconstructed") and alias.name not in existentes_set:
                    problemas.append("%s: `import %s` nao resolve" % (modulo, alias.name))
    return arvore


def arvore_do_readme():
    """Nomes de arquivo listados na arvore de `src/` do README."""
    nomes = []
    dentro = False
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


def arquivos_reais():
    nomes = ["app.py"]
    for raiz, dirs, arquivos in os.walk(SRC):
        dirs[:] = [d for d in dirs if d != "__pycache__"]
        for nome in arquivos:
            if nome.endswith(".py"):
                nomes.append(nome)
    return sorted(set(n for n in nomes if n != "__init__.py"))


def main() -> int:
    problemas = []
    existentes_set = existentes()

    print("=" * 78)
    print("ESTRUTURA DO PACOTE DEPOIS DA GUE7")
    print("=" * 78)
    for raiz, dirs, arquivos in os.walk(PACOTE):
        dirs[:] = [d for d in dirs if d != "__pycache__"]
        rel = os.path.relpath(raiz, os.path.dirname(PACOTE)).replace("\\", "/")
        print("  %s/" % rel)
        for nome in sorted(arquivos):
            if nome.endswith(".py"):
                print("    %-28s %4d linhas" % (nome, len(le(os.path.join(raiz, nome)).splitlines())))
    print("\n  modulos alcancaveis: %d" % len(existentes_set))

    print("\n1. RESOLUCAO DE IMPORT, POR AST")
    arquivos = []
    for base in (SRC, os.path.join(ROOT, "tests")):
        for raiz, dirs, nomes in os.walk(base):
            dirs[:] = [d for d in dirs if d != "__pycache__"]
            for nome in sorted(nomes):
                if nome.endswith(".py"):
                    arquivos.append(os.path.join(raiz, nome))
    for rel, _ in STRING_COLETORES:
        arquivos.append(os.path.join(ROOT, rel))

    total_imports = 0
    for caminho in arquivos:
        modulo = modulo_de(caminho) if caminho.startswith(SRC) else os.path.relpath(caminho, ROOT)
        arvore = checa_arquivo(caminho, modulo, existentes_set, problemas, [])
        total_imports += sum(1 for n in ast.walk(arvore) if isinstance(n, (ast.Import, ast.ImportFrom)))
    print("  arquivos varridos : %d" % len(arquivos))
    print("  imports conferidos: %d" % total_imports)

    print("\n2. OS COLETORES QUE VIVEM DENTRO DE STRING")
    for rel, constante in STRING_COLETORES:
        arvore = ast.parse(le(os.path.join(ROOT, rel)))
        texto = None
        for no in arvore.body:
            if (isinstance(no, ast.Assign)
                    and any(getattr(t, "id", "") == constante for t in no.targets)
                    and isinstance(no.value, ast.Constant)):
                texto = no.value.value
        if texto is None:
            problemas.append("%s: nao achei a constante %s" % (rel, constante))
            print("  %-46s NAO ENCONTRADA" % rel)
            continue
        sub = ast.parse(texto)
        antes = len(problemas)
        for no in ast.walk(sub):
            if isinstance(no, ast.ImportFrom):
                resolve(no, "coletor:" + os.path.basename(rel), existentes_set, problemas)
        n = sum(1 for no in ast.walk(sub) if isinstance(no, ast.ImportFrom))
        print("  %-46s %d import(s) dentro da string, %s"
              % (rel, n, "todos resolvem" if len(problemas) == antes else "COM PROBLEMA"))

    print("\n3. AST DOS MODULOS MOVIDOS, SEM AS LINHAS DE IMPORT")
    for origem, destino in MOVES:
        a = ast_sem_imports(os.path.join(ANTES, "reconstructed", origem))
        b = ast_sem_imports(os.path.join(PACOTE, destino))
        igual = a == b
        print("  %-40s %s" % (origem + " -> " + destino, "identico" if igual else "DIFERENTE"))
        if not igual:
            problemas.append("%s: o codigo mudou, e nao so o import" % destino)

    print("\n4. AS DUAS FACHADAS CONTINUAM ALCANCAVEIS")
    for fachada in ("reconstructed.path_search", "reconstructed.dna_analysis"):
        ok = fachada in existentes_set
        print("  %-36s %s" % (fachada, "existe" if ok else "NAO EXISTE"))
        if not ok:
            problemas.append("%s desapareceu" % fachada)

    esperado = {"parsers", "core", "reporting"}
    achados = {d for d in os.listdir(PACOTE)
               if os.path.isdir(os.path.join(PACOTE, d)) and d != "__pycache__"}
    print("\n5. SUBPACOTES")
    print("  na arvore   : %s" % ", ".join(sorted(achados)))
    print("  esperados   : %s" % ", ".join(sorted(esperado)))
    if achados != esperado:
        problemas.append("subpacotes diferentes do esperado")
    if os.path.exists(os.path.join(SRC, "__init__.py")):
        problemas.append("src/__init__.py foi criado, e a RN-01 proibe")

    print("\n6. ARVORE DO README x MODULOS QUE EXISTEM")
    na_arvore, reais = arvore_do_readme(), arquivos_reais()
    print("  na arvore do README : %d" % len(na_arvore))
    print("  arquivos que existem: %d  (sem `__init__.py`, que e marcador de pacote)" % len(reais))
    sobra = sorted(set(na_arvore) - set(reais))
    falta = sorted(set(reais) - set(na_arvore))
    if sobra:
        problemas.append("README lista arquivo que nao existe: %s" % ", ".join(sobra))
        print("  LISTA E NAO EXISTE: %s" % ", ".join(sobra))
    if falta:
        problemas.append("README nao lista arquivo que existe: %s" % ", ".join(falta))
        print("  EXISTE E NAO ESTA LISTADO: %s" % ", ".join(falta))
    if not sobra and not falta:
        print("  a arvore do README bate com o disco, arquivo por arquivo")

    print()
    print("=" * 78)
    if problemas:
        print("RESULTADO: %d PROBLEMA(S)" % len(problemas))
        for p in problemas:
            print("  " + p)
    else:
        print("RESULTADO: ESTRUTURA CONFERIDA")
        print("  todo import resolve, os dois coletores embutidos resolvem,")
        print("  os sete modulos so mudaram de caminho, as fachadas estao de pe")
    print("=" * 78)
    return 1 if problemas else 0


if __name__ == "__main__":
    raise SystemExit(main())

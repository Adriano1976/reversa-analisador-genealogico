"""Verifica a estrutura depois do lote A da OPP-20261003-RAIZ, sem executar o sistema.

1. Monta o conjunto de nomes de modulo que existem em `src/` e resolve TODO import
   relativo e todo import de `reconstructed.*` contra ele.
2. Faz o mesmo para os coletores que vivem DENTRO DE STRING no harness e no
   `_check_split_types.py`.
3. Resolve os caminhos de arquivo que os scripts de instrumentacao montam com
   `os.path.join(STUB, ...)`. Este e o ponto que nenhum gate enxerga: o
   `_verify_fix_gives_parity.py` abre `gedcom_state.py` por nome, e ele nao e
   executado pela suite nem pela paridade.
4. Compara o AST de cada modulo movido com o da copia congelada, tirando as linhas
   de import. Os tres que nao importam o pacote tem de ser identicos ATE nos imports.
5. Confere as fachadas, os subpacotes, a ausencia de `src/__init__.py` e a arvore do README.
"""
from __future__ import annotations

import ast
import difflib
import os
import re

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", "..", "..", ".."))
SRC = os.path.join(ROOT, "src")
PACOTE = os.path.join(SRC, "reconstructed")
ANTES = os.path.join(HERE, "before-after", "src-antes")
PARITY = os.path.join(ROOT, "_reversa_sdd", "parity")

MOVES = [
    ("gedcom_state.py", "core/gedcom_state.py"),
    ("path_search.py", "core/path_search.py"),
    ("dna_analysis.py", "core/dna_analysis.py"),
    ("text_cleaning.py", "utils/text_cleaning.py"),
    ("validate.py", "utils/validate.py"),
]

# Os tres que nao importam nada do pacote: o AST tem de ser identico ate nos imports.
SEM_IMPORT_INTERNO = {"gedcom_state.py", "text_cleaning.py", "validate.py"}

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
    """Remove tambem o docstring de todo modulo, funcao e classe.

    Serve para provar que nenhuma linha de CODIGO mudou, deixando de fora as duas
    coisas que esta transformacao pode legitimamente tocar: import e docstring.
    """

    @staticmethod
    def _sem_docstring(corpo):
        if (corpo and isinstance(corpo[0], ast.Expr)
                and isinstance(corpo[0].value, ast.Constant)
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


def ast_sem_imports(caminho):
    arvore = RemoveImports().visit(ast.parse(le(caminho)))
    ast.fix_missing_locations(arvore)
    return ast.dump(arvore)


def fim_do_docstring(caminho):
    """Linha em que o docstring do modulo termina."""
    arvore = ast.parse(le(caminho))
    primeiro = arvore.body[0]
    if not (isinstance(primeiro, ast.Expr) and isinstance(primeiro.value, ast.Constant)):
        return 0
    return primeiro.end_lineno


def modulo_de(caminho):
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
                if alvo + "." + alias.name not in existentes_set:
                    problemas.append("%s: `from %s import %s` nao resolve" %
                                     (modulo, "." * no.level, alias.name))
    else:
        alvo = no.module or ""
        if alvo.startswith("reconstructed") and alvo not in existentes_set:
            problemas.append("%s: `from %s import ...` nao resolve" % (modulo, alvo))


def checa_arquivo(caminho, modulo, existentes_set, problemas):
    arvore = ast.parse(le(caminho))
    for no in ast.walk(arvore):
        if isinstance(no, ast.ImportFrom):
            resolve(no, modulo, existentes_set, problemas)
        elif isinstance(no, ast.Import):
            for alias in no.names:
                if alias.name.startswith("reconstructed") and alias.name not in existentes_set:
                    problemas.append("%s: `import %s` nao resolve" % (modulo, alias.name))
    return arvore


def caminhos_de_stub(caminho):
    """Extrai os caminhos que o script monta com os primeiros argumentos STUB.

    A forma e `os.path.join(STUB, "core", "gedcom_state.py")`. O `STUB` e o
    PRIMEIRO ARGUMENTO, e nao o valor da funcao: `no.func.value` aqui e `os.path`.
    """
    achados = []
    for no in ast.walk(ast.parse(le(caminho))):
        if not (isinstance(no, ast.Call) and isinstance(no.func, ast.Attribute)
                and no.func.attr == "join"):
            continue
        if not (no.args and isinstance(no.args[0], ast.Name) and no.args[0].id == "STUB"):
            continue
        partes = [a.value for a in no.args[1:] if isinstance(a, ast.Constant)]
        if partes:
            achados.append(os.path.join(*partes))
    return achados


def arvore_do_readme():
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
    print("ESTRUTURA DO PACOTE DEPOIS DO LOTE A DA RAIZ")
    print("=" * 78)
    for raiz, dirs, arquivos in os.walk(PACOTE):
        dirs[:] = [d for d in dirs if d != "__pycache__"]
        rel = os.path.relpath(raiz, os.path.dirname(PACOTE)).replace("\\", "/")
        print("  %s/" % rel)
        for nome in sorted(arquivos):
            if nome.endswith(".py"):
                print("    %-26s %4d linhas" % (nome, len(le(os.path.join(raiz, nome)).splitlines())))
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
    total = 0
    for caminho in arquivos:
        modulo = modulo_de(caminho) if caminho.startswith(SRC) else os.path.relpath(caminho, ROOT)
        arvore = checa_arquivo(caminho, modulo, existentes_set, problemas)
        total += sum(1 for n in ast.walk(arvore) if isinstance(n, (ast.Import, ast.ImportFrom)))
    print("  arquivos varridos : %d" % len(arquivos))
    print("  imports conferidos: %d" % total)

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
        print("  %-46s %d import(s), %s" % (rel, n,
              "todos resolvem" if len(problemas) == antes else "COM PROBLEMA"))

    print("\n3. CAMINHOS DE ARQUIVO MONTADOS POR SCRIPT DE INSTRUMENTACAO")
    for nome in ("_verify_fix_gives_parity.py",):
        caminho = os.path.join(PARITY, nome)
        achados = caminhos_de_stub(caminho)
        if not achados:
            problemas.append("%s: nao achei caminho montado com STUB" % nome)
            print("  %-46s nenhum caminho encontrado" % nome)
        for rel in achados:
            real = os.path.join(PACOTE, rel)
            existe = os.path.exists(real)
            print("  %-46s %-32s %s" % (nome, rel, "existe" if existe else "NAO EXISTE"))
            if not existe:
                problemas.append("%s: o caminho %r nao existe no pacote" % (nome, rel))

    print("\n4. AST DOS MODULOS MOVIDOS")
    for origem, destino in MOVES:
        c_antes = os.path.join(ANTES, "reconstructed", origem)
        c_depois = os.path.join(PACOTE, destino)

        # (a) codigo puro: sem import e sem docstring, tem de ser identico.
        arvore_a = RemoveImportsEDocstrings().visit(ast.parse(le(c_antes)))
        arvore_b = RemoveImportsEDocstrings().visit(ast.parse(le(c_depois)))
        ast.fix_missing_locations(arvore_a)
        ast.fix_missing_locations(arvore_b)
        if ast.dump(arvore_a) == ast.dump(arvore_b):
            print("  %-42s codigo identico" % (origem + " -> " + destino))
        else:
            problemas.append("%s: alguma linha de CODIGO mudou" % destino)
            print("  %-42s CODIGO DIFERENTE" % (origem + " -> " + destino))

        # (b) classificacao de cada linha trocada: import, docstring, comentario ou OUTRO.
        a, b = le(c_antes).splitlines(), le(c_depois).splitlines()
        fim_doc_antes = fim_do_docstring(c_antes)
        fim_doc_depois = fim_do_docstring(c_depois)
        import_, doc, comentario, outro = 0, 0, 0, 0
        for tag, i1, i2, j1, j2 in difflib.SequenceMatcher(None, a, b).get_opcodes():
            if tag == "equal":
                continue
            for k in range(i1, i2):
                if re.match(r"\s*(from|import)\s", a[k]):
                    import_ += 1
                elif k < fim_doc_antes:
                    doc += 1
                elif a[k].lstrip().startswith("#"):
                    comentario += 1
                else:
                    outro += 1
                    print("     OUTRO (antes) : %s" % a[k].strip())
            for k in range(j1, j2):
                if re.match(r"\s*(from|import)\s", b[k]):
                    import_ += 1
                elif k < fim_doc_depois:
                    doc += 1
                elif b[k].lstrip().startswith("#"):
                    comentario += 1
                else:
                    outro += 1
                    print("     OUTRO (depois): %s" % b[k].strip())
        print("  %-42s linhas trocadas: %d import, %d docstring, %d comentario, %d outro"
              % ("", import_, doc, comentario, outro))
        if outro:
            problemas.append("%s: %d linha(s) que nao sao import, docstring nem comentario"
                             % (destino, outro))

        if origem in SEM_IMPORT_INTERNO:
            bruto = le(c_antes) == le(c_depois)
            print("  %-42s %s" % ("   sem import interno:",
                                  "byte a byte identico" if bruto else "DIVERGE"))
            if not bruto:
                problemas.append("%s: deveria ser byte a byte identico" % destino)

    print("\n5. FACHADAS, SUBPACOTES E A ARVORE DO README")
    for fachada in ("reconstructed.core.path_search", "reconstructed.core.dna_analysis"):
        ok = fachada in existentes_set
        print("  %-38s %s" % (fachada, "existe" if ok else "NAO EXISTE"))
        if not ok:
            problemas.append("%s desapareceu" % fachada)

    esperado = {"core", "parsers", "reporting", "utils"}
    achados = {d for d in os.listdir(PACOTE)
               if os.path.isdir(os.path.join(PACOTE, d)) and d != "__pycache__"}
    print("  %-38s %s" % ("subpacotes", ", ".join(sorted(achados))))
    if achados != esperado:
        problemas.append("subpacotes diferentes do esperado: %s" % ", ".join(sorted(achados)))

    soltos = [n for n in os.listdir(PACOTE)
              if n.endswith(".py") and n != "__init__.py"]
    print("  %-38s %d %s" % ("modulos soltos na raiz do pacote", len(soltos), soltos or ""))
    if soltos:
        problemas.append("ainda ha modulo solto na raiz: %s" % ", ".join(soltos))

    if os.path.exists(os.path.join(SRC, "__init__.py")):
        problemas.append("src/__init__.py foi criado, e a RN-01 proibe")
    if not os.path.exists(os.path.join(PACOTE, "utils", "__init__.py")):
        problemas.append("utils/__init__.py nao existe")

    na_arvore, reais = arvore_do_readme(), arquivos_reais()
    sobra = sorted(set(na_arvore) - set(reais))
    falta = sorted(set(reais) - set(na_arvore))
    print("  %-38s %s" % ("arvore do README x disco", "%d x %d" % (len(na_arvore), len(reais))))
    if sobra:
        problemas.append("README lista arquivo que nao existe: %s" % ", ".join(sobra))
    if falta:
        problemas.append("README nao lista arquivo que existe: %s" % ", ".join(falta))
    if not sobra and not falta:
        print("  %-38s %s" % ("", "bate, arquivo por arquivo"))

    print()
    print("=" * 78)
    if problemas:
        print("RESULTADO: %d PROBLEMA(S)" % len(problemas))
        for p in problemas:
            print("  " + p)
    else:
        print("RESULTADO: ESTRUTURA CONFERIDA")
        print("  todo import resolve, os coletores embutidos resolvem, o caminho do")
        print("  _verify_fix_gives_parity existe, os cinco modulos so mudaram de pasta,")
        print("  a raiz do pacote esta limpa e a arvore do README bate com o disco")
    print("=" * 78)
    return 1 if problemas else 0


if __name__ == "__main__":
    raise SystemExit(main())

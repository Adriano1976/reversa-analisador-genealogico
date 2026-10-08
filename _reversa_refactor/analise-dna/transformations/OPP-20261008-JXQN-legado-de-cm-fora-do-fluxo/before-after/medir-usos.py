"""Prova de uso de core.cm_estimator: varredura completa, com deteccao de literal.

Motivo do script: a prova de morte do verbo `prune` exige varrer *todos* os usos,
e nao uma amostra. Uma varredura textual simples confunde duas coisas muito
diferentes:

  - um `import` de verdade, que o interpretador executa ao carregar o modulo;
  - uma linha que apenas *parece* um import porque esta dentro de um literal de
    string, e que so vira codigo se alguem escrever aquele texto em disco e
    executa-lo.

O harness de paridade faz exatamente a segunda coisa. Por isso este script usa
`tokenize` para descobrir quais linhas estao cobertas por um token STRING, e
classifica cada ocorrencia como `codigo` ou `literal`.

Sem argumentos. Uso:  python medir-usos.py
Escreve prova-de-uso.txt ao lado deste arquivo, em UTF-8 sem BOM.
"""
from __future__ import annotations

import io
import os
import re
import tokenize

ALVO = ("cm_estimator", "SHARED_CM_DATA", "get_relationships_by_cm")
RAIZ = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "..", "..", ".."))
SAIDA = os.path.join(os.path.dirname(os.path.abspath(__file__)), "prova-de-uso.txt")

IGNORAR_DIR = {".venv", ".git", "node_modules", "__pycache__", ".pytest_cache", ".pytest-tmp"}
EXTENSOES = {".py", ".md", ".html", ".json", ".toml", ".ini", ".yml", ".yaml", ".js", ".txt", ".canvas", ".jsonl"}
PADRAO = re.compile("|".join(ALVO))


def spans(caminho):
    """Spans (linha, coluna) de STRING e de COMMENT, para arquivos .py.

    Granularidade de COLUNA, e nao de linha: uma linha como
    `assert "x" in f(y)` contem um STRING e ainda assim e codigo executavel.
    """
    strings, comentarios = [], []
    try:
        with open(caminho, "rb") as fh:
            for tok in tokenize.tokenize(fh.readline):
                if tok.type == tokenize.STRING:
                    strings.append(tok.start + tok.end)
                elif tok.type == tokenize.COMMENT:
                    comentarios.append(tok.start + tok.end)
    except (tokenize.TokenError, SyntaxError, UnicodeDecodeError, OSError):
        return None, None
    return strings, comentarios


def dentro(lista, linha, coluna):
    for sr, sc, er, ec in lista:
        if sr == er:
            if linha == sr and sc <= coluna < ec:
                return True
        elif (linha, coluna) >= (sr, sc) and (linha, coluna) < (er, ec):
            return True
    return False


def categoria(rel):
    if rel.startswith("src/") or rel.startswith("tests/"):
        return "alvo (codigo do projeto)"
    if rel.startswith("_reversa_sdd/oracle/"):
        return "oraculo congelado (copia propria)"
    if rel.startswith("_reversa_sdd/parity/"):
        return "harness de paridade"
    if rel.startswith("_reversa_forward/") or rel.startswith("_reversa_bugs/"):
        return "artefato do framework (evidencia datada)"
    if rel.startswith("_reversa_refactor/"):
        return "artefato do framework (registro de refactor)"
    if rel.startswith("_reversa_sdd/") or rel.startswith("_reversa_docs/"):
        return "documentacao do framework"
    if rel.startswith("docs/"):
        return "documentacao local"
    return "outro"


achados = []
for dp, dn, fn in os.walk(RAIZ):
    dn[:] = [d for d in dn if d not in IGNORAR_DIR]
    for nome in fn:
        if os.path.splitext(nome)[1].lower() not in EXTENSOES:
            continue
        caminho = os.path.join(dp, nome)
        rel = os.path.relpath(caminho, RAIZ).replace(os.sep, "/")
        try:
            texto = open(caminho, encoding="utf-8", errors="replace").read()
        except OSError:
            continue
        if not PADRAO.search(texto):
            continue
        strs, coments = spans(caminho) if nome.endswith(".py") else (None, None)
        for i, linha in enumerate(texto.splitlines(), start=1):
            achado = PADRAO.search(linha)
            if not achado:
                continue
            if strs is None:
                natureza = "texto"
            elif dentro(strs, i, achado.start()):
                natureza = "LITERAL"
            elif dentro(coments, i, achado.start()):
                natureza = "comentario"
            else:
                natureza = "codigo"
            achados.append((rel, i, natureza, linha.strip()))

partes = []
partes.append("PROVA DE USO de core.cm_estimator (SHARED_CM_DATA e get_relationships_by_cm)")
partes.append("Varredura: repositorio inteiro, excluindo " + ", ".join(sorted(IGNORAR_DIR)) + ".")
partes.append("Deteccao de literal: tokenize.STRING, por arquivo .py.")
partes.append("Total de ocorrencias: %d em %d arquivos." % (len(achados), len({a[0] for a in achados})))
partes.append("")
partes.append("Ocorrencias em que a linha e CODIGO EXECUTAVEL pelo interpretador ao carregar o arquivo:")
partes.append("")
vivos = [a for a in achados if a[2] == "codigo"]
if vivos:
    for rel, i, nat, txt in vivos:
        partes.append("  [%s] %s:%d" % (categoria(rel), rel, i))
        partes.append("      %s" % txt)
else:
    partes.append("  NENHUMA")
partes.append("")
partes.append("Ocorrencias em que a linha esta dentro de LITERAL de string (so vira codigo se o texto for")
partes.append("escrito em disco e executado):")
partes.append("")
for rel, i, nat, txt in [a for a in achados if a[2] == "LITERAL"]:
    partes.append("  [%s] %s:%d" % (categoria(rel), rel, i))
    partes.append("      %s" % txt)
partes.append("")
partes.append("Ocorrencias em COMENTARIO (nao executam nada):")
partes.append("")
coments = [a for a in achados if a[2] == "comentario"]
if coments:
    for rel, i, nat, txt in coments:
        partes.append("  [%s] %s:%d" % (categoria(rel), rel, i))
        partes.append("      %s" % txt)
else:
    partes.append("  NENHUMA")
partes.append("")
partes.append("Ocorrencias em arquivos que nao sao Python (documentacao e artefatos):")
partes.append("")
por_cat = {}
for rel, i, nat, txt in achados:
    if nat == "texto":
        por_cat.setdefault(categoria(rel), []).append((rel, i))
for cat in sorted(por_cat):
    partes.append("  %s: %d ocorrencia(s) em %d arquivo(s)" % (cat, len(por_cat[cat]), len({r for r, _ in por_cat[cat]})))
partes.append("")
partes.append("Contagem por categoria (todas as naturezas):")
todas = {}
for rel, i, nat, txt in achados:
    todas[categoria(rel)] = todas.get(categoria(rel), 0) + 1
for cat in sorted(todas):
    partes.append("  %-46s %d" % (cat, todas[cat]))
partes.append("")
partes.append("Leitura: o modulo NAO esta morto. Existe referencia de codigo executavel em")
partes.append("tests/test_dna_analysis.py, e existe referencia carregada por string no coletor embutido")
partes.append("do harness de paridade. As duas condicoes do verbo prune falham, uma por cada motivo.")

texto_final = "\n".join(partes) + "\n"
import tempfile
fd, tmp = tempfile.mkstemp(dir=os.path.dirname(SAIDA), prefix=".tmp-", suffix=".txt")
with os.fdopen(fd, "wb") as fh:
    fh.write(texto_final.encode("utf-8"))
os.replace(tmp, SAIDA)
print("raiz varrida: %s" % RAIZ)
print("prova-de-uso.txt gravado: %d ocorrencias em %d arquivos"
      % (len(achados), len({a[0] for a in achados})))
print("codigo executavel: %d | literal de string: %d | comentario: %d | nao-python: %d"
      % (len(vivos),
         len([a for a in achados if a[2] == "LITERAL"]),
         len([a for a in achados if a[2] == "comentario"]),
         len([a for a in achados if a[2] == "texto"])))

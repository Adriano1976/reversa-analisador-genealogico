"""Constroi a simplificacao da ponte e ensaia contra um pacote espelho.

NAO toca na arvore legada. Faz, em ordem:

  1. le `mermaid_render.py` e extrai, byte a byte do original, os trechos que NAO
     mudam (`norm_ids`, `split_at`, `add_node`, `add_chain`), para que a copia
     deles nao dependa de eu redigitar;
  2. remonta a funcao alvo com o subgrafo atomico e o helper do casal;
  3. confere que compila e que os trechos extraidos aparecem verbatim;
  4. escreve o pacote espelho;
  5. roda `caracterizar.py` contra o espelho e compara o digest com o de antes;
  6. gera o diff.

Uso:
    python <este script>
"""

from __future__ import annotations

import ast
import difflib
import hashlib
import os
import re
import shutil
import subprocess
import sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                    "..", "..", "..", "..", ".."))
REL = "analisador-genealogico/reconstructed/mermaid_render.py"
ORIG = os.path.join(ROOT, REL)
ESPELHO = os.path.join(ROOT, ".pytest-tmp", "h2yy-proposta")
AQUI = os.path.dirname(os.path.abspath(__file__))
SAIDA_DIFF = os.path.join(os.path.dirname(AQUI), "CHG-001.diff")
ALVO_FN = "generate_mermaid_graph_indirect_bridge"

IMPORT_ANTES = "import unicodedata\n\nfrom .family_navigation import ("
IMPORT_DEPOIS = ("import unicodedata\nfrom contextlib import contextmanager\n\n"
                 "from .family_navigation import (")

TEMPLATE = '''def generate_mermaid_graph_indirect_bridge(p1_id, p2_id, person_path):
    sid, lab = _mermaid_sid, _mermaid_label

<<<NORM_IDS>>>

    left, right, spouses = split_path_by_marriage(person_path)
    if not spouses:
        return generate_mermaid_graph(person_path, p1_id, p2_id, None)

    A, B = map(str, spouses)
    p1_id, p2_id = str(p1_id), str(p2_id)

    is_direct_connection_to_p2 = (p2_id == B)

    path_p1_A, ca1 = find_ancestral_path(p1_id, A)
    if not path_p1_A:
        return generate_mermaid_graph(person_path, p1_id, p2_id, None)

    spouse_ca1 = pick_spouse_for_couple(ca1, candidate_path=path_p1_A)

<<<SPLIT_AT>>>

    r1_down, r1_up_from_A = split_at(path_p1_A, ca1)

    couple1_id = None
    couple1_label = None
    if spouse_ca1:
        couple1_id = sid("+".join(sorted([str(ca1), str(spouse_ca1)])))
        couple1_label = f'{lab(get_name(people.get(ca1)))} &amp; {lab(get_name(people.get(spouse_ca1)))}'

    lines = ["flowchart BT"]
    seen = set()

    @contextmanager
    def subgrafo(header):
        """Abre o subgrafo, escreve a direcao e o fecha ao fim do bloco.

        O fechamento deixa de ser uma linha que alguem precisa posicionar no meio
        do fluxo: ele e o fim do `with`. Um `end` a mais ou a menos muda a arvore
        do diagrama sem levantar erro nenhum, e era exatamente esse o risco
        registrado na OPP-20260929-H2YY.

        Sem try/finally de proposito: `end` so e escrito se o corpo terminar, que
        e o comportamento da sequencia de append que este helper substitui.
        """
        lines.append("subgraph %s" % header)
        lines.append("direction BT")
        yield
        lines.append("end")

<<<ADD_NODE>>>

<<<ADD_CHAIN>>>

    def emit_couple_or_ancestor(couple_id, couple_label, ca, left_col, right_col):
        """Emite o par de conjuge, ou o ancestral quando nao ha par, e liga as colunas.

        O destino das setas difere entre os dois casos: o par ja chega como id de
        no, e o ancestral ainda precisa passar por `sid`. Assumir que o mesmo id
        serve para os dois muda a saida nos casos com conjuge.
        """
        if couple_id:
            lines.append(f'{couple_id}["{couple_label}"]')
            alvo = couple_id
        else:
            add_node(ca)
            alvo = sid(ca)
        if left_col:
            lines.append(f'{sid(left_col[-1])} --> {alvo}')
        if right_col:
            lines.append(f'{sid(right_col[-1])} --> {alvo}')

    with subgrafo("COLUMNS"):
        with subgrafo("ESQ[Ramo 1]"):
            with subgrafo("ESQ_COLS"):
                left_col_r1 = exclude_tail(r1_down, n=1)
                right_col_r1 = exclude_tail(r1_up_from_A, n=1)

                if left_col_r1:
                    with subgrafo("ESQ_L[ ]"):
                        add_chain(left_col_r1)
                if right_col_r1:
                    with subgrafo("ESQ_R[ ]"):
                        add_chain(right_col_r1)

            emit_couple_or_ancestor(couple1_id, couple1_label, ca1, left_col_r1, right_col_r1)

        if is_direct_connection_to_p2:
            with subgrafo("DIR[Ramo 2]"):
                add_node(p2_id)
            right_col_r2 = []
            couple2_id, ca2 = None, None
        else:
            path_p2_B, ca2 = find_ancestral_path(p2_id, B)
            if not path_p2_B:
                return generate_mermaid_graph(person_path, p1_id, p2_id, None)

            spouse_ca2 = pick_spouse_for_couple(ca2, candidate_path=path_p2_B)
            r2_down, r2_up_from_B = split_at(path_p2_B, ca2)

            couple2_id = None
            couple2_label = None
            if spouse_ca2:
                couple2_id = sid("+".join(sorted([str(ca2), str(spouse_ca2)])))
                couple2_label = f'{lab(get_name(people.get(ca2)))} &amp; {lab(get_name(people.get(spouse_ca2)))}'

            with subgrafo("DIR[Ramo 2]"):
                with subgrafo("DIR_COLS"):
                    left_col_r2 = exclude_tail(r2_up_from_B, n=1)
                    right_col_r2 = exclude_tail(r2_down, n=1)

                    if left_col_r2:
                        with subgrafo("DIR_L[ ]"):
                            add_chain(left_col_r2)
                    if right_col_r2:
                        with subgrafo("DIR_R[ ]"):
                            add_chain(right_col_r2)

                emit_couple_or_ancestor(couple2_id, couple2_label, ca2, left_col_r2, right_col_r2)

        A_anchor = sid(f"{A}_anc")
        B_anchor = sid(f"{B}_anc")
        lines += [
            f'{A_anchor}[" "]',
            f'{B_anchor}[" "]',
            f'style {A_anchor} fill:transparent,stroke:transparent,stroke-width:0',
            f'style {B_anchor} fill:transparent,stroke:transparent,stroke-width:0',
            f'{sid(A)} --- {A_anchor}',
            f'{B_anchor} --- {sid(B)}',
            f'{A_anchor} --- |Casamento| {B_anchor}',
        ]

    if left_col_r1:
        lines.append(f'style {sid(p1_id)} fill:#e8f5e9,stroke:#66bb6a,stroke-width:2px')

    if is_direct_connection_to_p2 or right_col_r2:
        lines.append(f'style {sid(p2_id)} fill:#ffebee,stroke:#ef5350,stroke-width:2px')

    if couple1_id:
        lines.append(f'style {couple1_id} fill:#fff9c4,stroke:#fbc02d,stroke-width:2px')
    elif ca1:
        lines.append(f'style {sid(ca1)} fill:#fff9c4,stroke:#fbc02d,stroke-width:2px')

    if couple2_id:
        lines.append(f'style {couple2_id} fill:#fff9c4,stroke:#fbc02d,stroke-width:2px')
    elif ca2:
        lines.append(f'style {sid(ca2)} fill:#fff9c4,stroke:#fbc02d,stroke-width:2px')

    lines.append(f'style {sid(A)} fill:#fff8e1,stroke:#f6a821,stroke-width:2px')
    lines.append(f'style {sid(B)} fill:#fff8e1,stroke:#f6a821,stroke-width:2px')

    return "\\n".join(lines)
'''


def main() -> int:
    src = open(ORIG, encoding="utf-8", newline="").read()
    linhas = src.splitlines(keepends=True)
    arvore = ast.parse(src)

    fn = next(n for n in arvore.body
              if isinstance(n, ast.FunctionDef) and n.name == ALVO_FN)
    ini, fim = fn.lineno, fn.end_lineno

    blocos = {}
    for n in fn.body:
        if isinstance(n, ast.FunctionDef) and n.name in ("norm_ids", "split_at",
                                                        "add_node", "add_chain"):
            blocos[n.name] = "".join(linhas[n.lineno - 1:n.end_lineno]).rstrip("\n")

    faltando = [b for b in ("norm_ids", "split_at", "add_node", "add_chain") if b not in blocos]
    assert not faltando, "nao achei os trechos: %s" % faltando

    nova = TEMPLATE
    for chave, marcador in (("norm_ids", "<<<NORM_IDS>>>"), ("split_at", "<<<SPLIT_AT>>>"),
                            ("add_node", "<<<ADD_NODE>>>"), ("add_chain", "<<<ADD_CHAIN>>>")):
        nova = nova.replace(marcador, blocos[chave])

    novo_modulo = "".join(linhas[:ini - 1]) + nova + "".join(linhas[fim:])
    assert novo_modulo.count(IMPORT_ANTES) == 1, "ancora do import nao e unica"
    novo_modulo = novo_modulo.replace(IMPORT_ANTES, IMPORT_DEPOIS, 1)

    compile(novo_modulo, "mermaid_render.py", "exec")

    problemas = []
    for nome, bloco in blocos.items():
        if novo_modulo.count(bloco) != 1:
            problemas.append("trecho %s aparece %d vezes" % (nome, novo_modulo.count(bloco)))
    for marca in ("<<<", ">>>"):
        if marca in novo_modulo:
            problemas.append("marcador %s sobrou no texto" % marca)

    def linhas_de(t):
        return t.count("\n") + (0 if t.endswith("\n") else 1)

    print("funcao alvo           : %s, linhas %d-%d (%d linhas)"
          % (ALVO_FN, ini, fim, fim - ini + 1))
    print("trechos preservados   : %s" % ", ".join(sorted(blocos)))
    print("problemas de verbatim : %d" % len(problemas))
    for p in problemas:
        print("   " + p)

    destino_dir = os.path.join(ESPELHO, "analisador-genealogico", "reconstructed")
    os.makedirs(destino_dir, exist_ok=True)
    if not os.path.isdir(os.path.join(ESPELHO, "analisador-genealogico", "reconstructed")):
        print("espelho nao preparado")
        return 2
    with open(os.path.join(destino_dir, "mermaid_render.py"), "w",
              encoding="utf-8", newline="\n") as fh:
        fh.write(novo_modulo)

    print("funcao depois         : %d linhas (antes %d)"
          % (len(nova.rstrip("\n").splitlines()), fim - ini + 1))
    print("modulo antes/depois   : %d / %d linhas" % (linhas_de(src), linhas_de(novo_modulo)))

    # --- ensaio: caracterizacao contra o espelho ---------------------------
    carac = os.path.join(AQUI, "caracterizar.py")
    r = subprocess.run([sys.executable, carac,
                        os.path.join(ESPELHO, "analisador-genealogico"), "ensaio"],
                       capture_output=True, cwd=ROOT)
    if r.returncode != 0:
        print("caracterizacao do espelho FALHOU:\n%s" % r.stderr.decode()[-3000:])
        return 1
    d_espelho = re.search(r"digest da caracterizacao : ([0-9a-f]+)", r.stdout.decode())
    d_antes = re.search(r"digest da caracterizacao : ([0-9a-f]+)",
                        open(os.path.join(AQUI, "caracterizacao-antes.txt"), encoding="utf-8").read())
    print("")
    print("digest antes          : %s" % (d_antes.group(1) if d_antes else "?"))
    print("digest espelho        : %s" % (d_espelho.group(1) if d_espelho else "?"))
    igual = bool(d_antes and d_espelho and d_antes.group(1) == d_espelho.group(1))
    print("VEREDITO              : %s" % ("IDENTICO nos 298 casos" if igual else "DIVERGENTE"))

    # --- diff ---------------------------------------------------------------
    def blob(t):
        d = t.encode("utf-8")
        return hashlib.sha1(b"blob " + str(len(d)).encode() + b"\0" + d).hexdigest()

    diff = list(difflib.unified_diff(linhas, novo_modulo.splitlines(keepends=True),
                                     fromfile="a/" + REL, tofile="b/" + REL, n=3))
    conteudo = "".join(["diff --git a/%s b/%s\n" % (REL, REL),
                        "index %s..%s 100644\n" % (blob(src)[:7], blob(novo_modulo)[:7])] + diff)
    with open(SAIDA_DIFF, "w", encoding="utf-8", newline="\n") as fh:
        fh.write(conteudo)
    print("diff escrito          : %s (%d bytes)"
          % (os.path.relpath(SAIDA_DIFF, ROOT), len(conteudo.encode("utf-8"))))
    return 1 if (problemas or not igual) else 0


if __name__ == "__main__":
    raise SystemExit(main())

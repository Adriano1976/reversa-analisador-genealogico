"""Prova de equivalencia da OPP-20260929-AU76: versao atual x versao otimizada.

Carrega a MESMA base sintetica nas duas variantes do pacote (projeto e sombra) e
compara, campo a campo:

  1. match_candidates: lista de candidatos E a string de motivo, para um corpus
     deterministico mais 2.000 casos pseudoaleatorios com semente fixa.
  2. dna_analysis: a saida completa do fluxo (resultados, descartados, mensagem)
     para os CSVs sinteticos das fixtures.

Inclui os casos de borda exigidos pelo protocolo: vazio, nulo, limites de cM e
nomes degenerados. Nenhum dado real e usado e nenhum arquivo do projeto muda.
"""
import importlib
import inspect
import os
import pathlib
import random
import sys
import tempfile

ROOT = pathlib.Path(r"D:\Projetos\reversa_analisador_gelealogico")
# Variante A e a linha de base; B e a versao sob teste. Por padrao, A e o projeto
# e B e a sombra. Depois de aplicar no projeto, aponte A para .pytest-tmp/baseline.
REAL = pathlib.Path(os.environ.get("VARIANT_A_DIR", str(ROOT / "analisador-genealogico")))
SHADOW = pathlib.Path(os.environ.get("VARIANT_B_DIR", str(ROOT / ".pytest-tmp" / "shadow")))

sys.path.insert(0, str(ROOT))
from tests.fixtures.sample_dna import (  # noqa: E402
    DNA_CSV_DUPLICATED, DNA_CSV_NO_INTERSECTION, DNA_CSV_UTF8, DNA_GED,
)

GIVENS = ["Maria", "Jose", "Ana", "Joao", "Carlos", "Fernanda", "Ricardo",
          "Beatriz", "Joaquim", "Marta", "Lone", "Paulo", "Helena"]
SURNS = ["Silva", "Souza", "Oliveira", "Santos", "Pereira", "Ferreira",
         "Almeida", "Costa", "Rodrigues", "Lima", "Ranger", "Gomes"]

BORDAS = [
    "", " ", None, "a", "de da do", "Silva", "silva",
    "CARLOS SILVA SOUZA", "carlos silva souza",
    "Carlos Silva Souza Filho", "Carlos Silva Junior", "Carlos Silva Neto",
    "Carlos Silv Sou", "C. Silva", "Carlos Silva-Souza", "Silva, Carlos",
    "Carlos  Silva   Souza", "JoA?o Silva", "Ã§ Carlos Silva",
    "Ana Silva Souza Ferreira", "Maria Jose Silva Souza Oliveira",
    "Carlos " + "Souza " * 40,
]
CMS = [0, -1, 10, 100, 149.9, 150, 500, 3720, None]


def carregar_variante(dir_pacote):
    """Importa o pacote reconstructed a partir de um diretorio especifico."""
    for k in list(sys.modules):
        if k == "reconstructed" or k.startswith("reconstructed."):
            del sys.modules[k]
    for p in (str(REAL), str(SHADOW)):
        while p in sys.path:
            sys.path.remove(p)
    sys.path.insert(0, str(dir_pacote))
    upload = importlib.import_module("reconstructed.upload")
    dna = importlib.import_module("reconstructed.dna_analysis")
    return upload, dna


def carregar_ged(upload, ged_text):
    fd, path = tempfile.mkstemp(suffix=".ged")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            f.write(ged_text)
        upload.load_gedcom_and_build_graph(path)
    finally:
        os.remove(path)


def chamar_match(dna, indices, nome, cm):
    """Chama match_candidates respeitando a aridade real da variante.

    Detecta pela assinatura, nao pelo tamanho da tupla: assim funciona tanto na
    versao com o cache recém acrescentado quanto na versao empilhada que poda o
    given_index depois. O cache e sempre o ULTIMO item da tupla de indices.
    """
    if len(inspect.signature(dna.match_candidates).parameters) >= 5:
        return dna.match_candidates(nome, cm, indices[0], indices[1], indices[-1])
    return dna.match_candidates(nome, cm, indices[0], indices[1])


def corpus():
    casos = [(n, cm) for n in BORDAS for cm in CMS]
    rnd = random.Random(20260929)
    for _ in range(2000):
        n = rnd.randint(1, 4)
        nome = " ".join(rnd.choice(GIVENS if i == 0 else SURNS) for i in range(n))
        if rnd.random() < 0.3:
            nome = nome.upper()
        if rnd.random() < 0.2:
            nome += rnd.choice([" Filho", " Neto", " Junior", " de Souza"])
        if rnd.random() < 0.15:
            nome = nome[: max(1, len(nome) // 2)]
        casos.append((nome, rnd.choice(CMS)))
    return casos


def comparar_match(D_old, D_new, idx_old, idx_new):
    divergencias = []
    casos = corpus()
    for nome, cm in casos:
        a = chamar_match(D_old, idx_old, nome, cm)
        b = chamar_match(D_new, idx_new, nome, cm)
        if a != b:
            divergencias.append((nome, cm, a, b))
    return len(casos), divergencias


def escrever_csv(conteudo, sufixo=".csv"):
    fd, path = tempfile.mkstemp(suffix=sufixo)
    with os.fdopen(fd, "w", encoding="utf-8", newline="") as f:
        f.write(conteudo)
    return path


def comparar_pipeline(D_old, D_new):
    divergencias = []
    fontes = {
        "utf8": DNA_CSV_UTF8,
        "duplicado": DNA_CSV_DUPLICATED,
        "sem-intersecao": DNA_CSV_NO_INTERSECTION,
    }
    rnd = random.Random(7)
    linhas = ["Name,cM,Email"]
    for i in range(60):
        nome = f"{rnd.choice(GIVENS)} {rnd.choice(SURNS)} {rnd.choice(SURNS)}"
        linhas.append(f"{nome},{rnd.choice([50, 150, 300, 537, 1200])},m{i}@x.com")
    fontes["massa"] = "\n".join(linhas) + "\n"

    for tag, conteudo in fontes.items():
        path = escrever_csv(conteudo)
        try:
            for raiz in ("Carlos Silva", "Ana Silva Souza"):
                a = D_old.dna_analysis(path, raiz)
                b = D_new.dna_analysis(path, raiz)
                if a != b:
                    divergencias.append((tag, raiz, a, b))
        finally:
            os.remove(path)
    return len(fontes) * 2, divergencias


def main():
    if not SHADOW.is_dir():
        print("ERRO: sombra ausente. Rode .pytest-tmp/shadow_opt_build.py antes.")
        return 2

    U_old, D_old = carregar_variante(REAL)
    carregar_ged(U_old, DNA_GED)
    idx_old = D_old.build_ged_indexes()

    U_new, D_new = carregar_variante(SHADOW)
    carregar_ged(U_new, DNA_GED)
    idx_new = D_new.build_ged_indexes()

    print(f"variante atual     : {D_old.__file__}")
    print(f"variante otimizada : {D_new.__file__}")
    ultimo = idx_new[-1]
    campos = sorted(next(iter(ultimo.values()))) if isinstance(ultimo, dict) and ultimo else "sem cache"
    print(f"campos do cache    : {campos}")

    n1, d1 = comparar_match(D_old, D_new, idx_old, idx_new)
    n2, d2 = comparar_pipeline(D_old, D_new)

    print(f"\nmatch_candidates : {n1} casos comparados, {len(d1)} divergencias")
    for nome, cm, a, b in d1[:5]:
        print(f"  DIVERGE nome={nome!r} cm={cm!r}\n    atual={a}\n    nova ={b}")
    print(f"dna_analysis     : {n2} execucoes comparadas, {len(d2)} divergencias")
    for tag, raiz, a, b in d2[:3]:
        print(f"  DIVERGE fonte={tag} raiz={raiz!r}\n    atual={str(a)[:200]}\n    nova ={str(b)[:200]}")

    if d1 or d2:
        print("\nEQUIVALENCIA VERMELHA")
        return 1
    print(f"\nEQUIVALENCIA VERDE: {n1 + n2} comparacoes identicas (inclui vazio, nulo e limites de cM)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

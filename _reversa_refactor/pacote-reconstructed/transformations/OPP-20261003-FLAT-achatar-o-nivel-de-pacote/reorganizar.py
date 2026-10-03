"""Aplica a OPP-20261003-FLAT: achata o nivel de pacote.

Ordem, e nada e escrito antes de todas as assercoes passarem:

 1. sobe os quatro subpacotes para `src/` e apaga `reconstructed/`;
 2. regra 1: os imports entre subpacotes deixam de poder ser relativos, porque os
    pacotes passam a ser de primeiro nivel. `from ..X` vira `from X`;
 3. regra 2: o prefixo `reconstructed.` sai das linhas de import;
 4. corrige as citacoes em prosa, incluindo as duas linhas de CODIGO do
    `_verify_fix_gives_parity.py`, que apontam para o diretorio que deixa de existir;
 5. atualiza a arvore do README, o comentario do `pyrefly.toml` e o watch `W001`.

As contagens de 2 e 3 sao medidas antes e conferidas: se uma linha a mais aparecer, o
script aborta em vez de aplicar pela metade.
"""
from __future__ import annotations

import os
import re
import shutil

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", "..", "..", ".."))

PASTA = "reconstructed"
ALVO = os.path.join(ROOT, "src", PASTA)

SUBPACOTES = ["core", "parsers", "reporting", "utils"]

# ------------------------------------------------------------------ regra 1
REGRA_1 = [
    "src/reconstructed/core/dna_analysis.py",
    "src/reconstructed/core/name_normalization.py",
    "src/reconstructed/core/path_search.py",
    "src/reconstructed/parsers/csv_ingest.py",
    "src/reconstructed/parsers/gedcom_parser.py",
    "src/reconstructed/reporting/mermaid_render.py",
]
ESPERADO_1 = 12

# ------------------------------------------------------------------ regra 2
REGRA_2 = [
    "src/app.py",
    "tests/test_upload.py",
    "tests/test_path_search.py",
    "tests/test_dna_analysis.py",
    "tests/test_characterization_matching.py",
    "tests/test_characterization_mermaid.py",
    "tests/test_mermaid_escape.py",
    "tests/test_domain.py",
    "tests/test_upload_seguranca.py",
    "_reversa_sdd/parity/harness.py",
    "_reversa_sdd/parity/_check_split_types.py",
]
ESPERADO_2 = 31

# ------------------------------------------------------------------ prosa
PROSA = [
    ("src/core/path_search.py", [
        ("importam nomes daqui: `app.py`, `reconstructed/core/dna_analysis.py`,",
         "importam nomes daqui: `app.py`, `core/dna_analysis.py`,"),
    ]),
    ("tests/test_upload_seguranca.py", [
        ('"""Import tardio de `reconstructed.validate`.', '"""Import tardio de `utils.validate`.'),
    ]),
    ("_reversa_sdd/parity/_verify_fix_gives_parity.py", [
        ('SRC = os.path.join(ROOT, "src", "reconstructed")', 'SRC = os.path.join(ROOT, "src")'),
        ('STUB = os.path.join(ROOT, ".parity-stub", "reconstructed")',
         'STUB = os.path.join(ROOT, ".parity-stub")'),
        ("Metodo: copia `reconstructed/` para um diretorio temporario, substitui `get_name`",
         "Metodo: copia `src/` para um diretorio temporario, substitui `get_name`"),
        ("NAO toca em `src/reconstructed/` (artefato de trabalho anterior).",
         "NAO toca em `src/` (artefato de trabalho anterior)."),
        ("# resolve `reconstructed` como NAMESPACE PACKAGE do diretorio de trabalho — cria",
         "# resolve `core` como NAMESPACE PACKAGE do diretorio de trabalho — cria"),
        ("# erro que aparece e `cannot import name 'upload' from 'reconstructed'",
         "# erro que aparece e `cannot import name 'gedcom_state' from 'core'"),
    ]),
    ("_reversa_sdd/parity/harness.py", [
        ("wrapper de 86 linhas que importa `reconstructed/`, e usa-lo produz validacao",
         "wrapper de 86 linhas que importa `src/`, e usa-lo produz validacao"),
        ('print("candidato : src/reconstructed/")', 'print("candidato : src/")'),
    ]),
    ("pyrefly.toml", [
        ("# Adiciona o diretório onde o pacote `reconstructed` realmente reside,",
         "# Adiciona o diretório onde os pacotes do núcleo realmente residem,"),
    ]),
    ("README.md", [
        ("├── reconstructed/              # Pacote com a lógica reconstruída e modularizada\n"
         "│   ├── parsers/                # Leitura do mundo de fora: o arquivo GEDCOM e o CSV de matches\n"
         "│   │   ├── gedcom_parser.py    # Leitura do GEDCOM e construção do grafo networkx\n"
         "│   │   └── csv_ingest.py       # Leitura do CSV de matches e agregação de cM por segmento\n"
         "│   ├── core/                   # Decisão sobre o que foi lido, sem saber de HTTP\n"
         "│   │   ├── cm_estimator.py     # Tradução de cM em relações prováveis (faixas heurísticas)\n"
         "│   │   ├── matching.py         # Índices do GEDCOM e decisão de aceitação de candidatos\n"
         "│   │   ├── name_normalization.py  # Normalização e decomposição de nomes (norm_name, split_name_pt)\n"
         "│   │   ├── path_finding.py     # Busca direta por ancestral comum (MRCA) e indireta por afinidade\n"
         "│   │   ├── family_navigation.py   # Resolução de pessoa por nome e navegação de parentesco\n"
         "│   │   ├── gedcom_state.py     # Estado do GEDCOM carregado: pessoas, famílias e grafo\n"
         "│   │   ├── path_search.py      # Fachada da busca de caminhos, consumida pelo app.py\n"
         "│   │   └── dna_analysis.py     # Fachada do cruzamento GEDCOM × CSV, consumida pelo app.py\n"
         "│   ├── reporting/              # Transformação de resultado em apresentação\n"
         "│   │   └── mermaid_render.py   # Emissão do diagrama Mermaid e contrato de escape do rótulo\n"
         "│   └── utils/                  # Ferramentas utilitárias, sem papel no núcleo\n"
         "│       ├── text_cleaning.py    # Autoridade única de limpeza de mojibake (strip_bad_utf, demojibake)\n"
         "│       └── validate.py         # Validação do upload: nome visível, chave de conteúdo e GEDCOM",
         "├── parsers/                    # Leitura do mundo de fora: o arquivo GEDCOM e o CSV de matches\n"
         "│   ├── gedcom_parser.py        # Leitura do GEDCOM e construção do grafo networkx\n"
         "│   └── csv_ingest.py           # Leitura do CSV de matches e agregação de cM por segmento\n"
         "├── core/                       # Decisão sobre o que foi lido, sem saber de HTTP\n"
         "│   ├── cm_estimator.py         # Tradução de cM em relações prováveis (faixas heurísticas)\n"
         "│   ├── matching.py             # Índices do GEDCOM e decisão de aceitação de candidatos\n"
         "│   ├── name_normalization.py   # Normalização e decomposição de nomes (norm_name, split_name_pt)\n"
         "│   ├── path_finding.py         # Busca direta por ancestral comum (MRCA) e indireta por afinidade\n"
         "│   ├── family_navigation.py    # Resolução de pessoa por nome e navegação de parentesco\n"
         "│   ├── gedcom_state.py         # Estado do GEDCOM carregado: pessoas, famílias e grafo\n"
         "│   ├── path_search.py          # Fachada da busca de caminhos, consumida pelo app.py\n"
         "│   └── dna_analysis.py         # Fachada do cruzamento GEDCOM × CSV, consumida pelo app.py\n"
         "├── reporting/                  # Transformação de resultado em apresentação\n"
         "│   └── mermaid_render.py       # Emissão do diagrama Mermaid e contrato de escape do rótulo\n"
         "├── utils/                      # Ferramentas utilitárias, sem papel no núcleo\n"
         "│   ├── text_cleaning.py        # Autoridade única de limpeza de mojibake (strip_bad_utf, demojibake)\n"
         "│   └── validate.py             # Validação do upload: nome visível, chave de conteúdo e GEDCOM"),
        ("a lógica foi extraída para o pacote `reconstructed/`, e o `app.py` passou a apenas orquestrar",
         "a lógica foi extraída para `src/`, organizada nos pacotes `parsers/`, `core/`, `reporting/` e `utils/`, e o `app.py` passou a apenas orquestrar"),
        ("- A lógica de negócio está modularizada no pacote `reconstructed/`, separada da camada web (`app.py`).",
         "- A lógica de negócio está modularizada em `src/`, nos pacotes `parsers/`, `core/`, `reporting/` e `utils/`, separada da camada web (`app.py`)."),
    ]),
]

# ------------------------------------------------------------------ watch
WATCH = "_reversa_forward/003-renomear-pasta-app-para-src/regression-watch.md"
W001_ANTES = ("| W001 | `_reversa_sdd/inventory.md#2`, `#4` | A raiz de código se chama `src/` e o pacote do núcleo continua "
              "sendo importado pelo mesmo nome, `reconstructed.*` | presença | Reaparecimento de um diretório com o nome "
              "antigo contendo código, ou mudança do nome do pacote do núcleo |")
W001_DEPOIS = ("| W001 | `_reversa_sdd/inventory.md#2`, `#4` | A raiz de código se chama `src/` e o núcleo é importado "
               "direto dela, como os pacotes de primeiro nível `parsers.*`, `core.*`, `reporting.*` e `utils.*`, sem "
               "nível de pacote intermediário | presença | Reaparecimento de um diretório com o nome antigo contendo "
               "código, reaparecimento do nível `reconstructed`, ou mudança dos nomes dos pacotes do núcleo |")
NOTA_WATCH = ("\n> **Atualização 2026-10-03, `OPP-20261003-FLAT`.** O `W001` vigiava `reconstructed.*`. A transformação "
              "`FLAT` apagou esse nível de pacote, e o núcleo passou a ser importado direto de `src/` como `core.*`, "
              "`parsers.*`, `reporting.*` e `utils.*`. A condição foi reescrita para a nova identidade. A avaliação está "
              "em `_reversa_refactor/pacote-reconstructed/transformations/OPP-20261003-FLAT-achatar-o-nivel-de-pacote/transformation.md`, "
              "e nenhuma regra de negócio mudou: a suíte e a paridade foram remedidas. A observação `O5` perde o objeto, "
              "porque o `__init__.py` que ela cita deixou de existir.\n")


def le(caminho):
    with open(caminho, encoding="utf-8") as fh:
        return fh.read()


def grava(caminho, texto):
    with open(caminho, "w", encoding="utf-8", newline="") as fh:
        fh.write(texto)


def caminho_pos(rel):
    """src/reconstructed/core/x.py -> src/core/x.py"""
    return rel.replace("src/reconstructed/", "src/", 1)


def caminho_pre(rel):
    """O inverso, para a validacao, que acontece antes da movimentacao.

    `src/app.py` fica de fora: ele nunca esteve dentro do pacote.
    """
    if rel.startswith("src/") and rel != "src/app.py" and not rel.startswith("src/reconstructed/"):
        return rel.replace("src/", "src/reconstructed/", 1)
    return rel


def main() -> int:
    falhas = []

    print("=" * 78)
    print("FASE 1, VALIDACAO: nada foi escrito ainda")
    print("=" * 78)
    if not os.path.isdir(ALVO):
        print("  o diretorio %s nao existe" % PASTA)
        return 1
    print("  conteudo de %s/: %s" % (PASTA, ", ".join(sorted(os.listdir(ALVO)))))

    for rel in REGRA_1 + REGRA_2 + [p for p, _ in PROSA]:
        if not os.path.exists(os.path.join(ROOT, caminho_pre(rel))):
            falhas.append("%s nao existe" % rel)

    n1 = n2 = 0
    for rel in REGRA_1:
        for linha in le(os.path.join(ROOT, rel)).splitlines():
            if linha.lstrip().startswith("from .."):
                n1 += 1
    for rel in REGRA_2:
        for linha in le(os.path.join(ROOT, rel)).splitlines():
            if re.match(r"\s*(from|import)\s", linha) and "reconstructed." in linha:
                n2 += 1
    print("  regra 1, `from ..` a converter : %d (esperado %d)" % (n1, ESPERADO_1))
    print("  regra 2, prefixo a remover     : %d (esperado %d)" % (n2, ESPERADO_2))
    if n1 != ESPERADO_1:
        falhas.append("regra 1: %d linhas, esperado %d" % (n1, ESPERADO_1))
    if n2 != ESPERADO_2:
        falhas.append("regra 2: %d linhas, esperado %d" % (n2, ESPERADO_2))
    for rel, pares in PROSA:
        texto = le(os.path.join(ROOT, caminho_pre(rel)))
        for antes, depois in pares:
            if texto.count(antes) != 1:
                falhas.append("%s: o trecho aparece %d vezes: %r" % (rel, texto.count(antes), antes[:60]))
    if falhas:
        print("\n  ABORTADO, %d problema(s):" % len(falhas))
        for f in falhas:
            print("    " + f)
        return 1
    print("  todas as contagens e todos os trechos conferem")

    print("\nFASE 2, SUBIR OS QUATRO SUBPACOTES")
    for nome in SUBPACOTES:
        de = os.path.join(ALVO, nome)
        para = os.path.join(ROOT, "src", nome)
        if os.path.exists(para):
            falhas.append("ja existe: src/%s" % nome)
            continue
        shutil.move(de, para)
        print("  reconstructed/%-11s -> src/%s" % (nome, nome))

    print("\nFASE 3, APAGAR O NIVEL DE PACOTE")
    restante = sorted(os.listdir(ALVO))
    print("  o que sobrou em reconstructed/: %s" % ", ".join(restante))
    if restante != ["__init__.py"]:
        falhas.append("sobrou mais do que o __init__.py: %s" % ", ".join(restante))
    else:
        os.remove(os.path.join(ALVO, "__init__.py"))
        os.rmdir(ALVO)
        print("  removido src/reconstructed/__init__.py e o diretorio reconstructed/")

    print("\nFASE 4, REGRA 1: `from ..` VIRA ABSOLUTO")
    for rel in REGRA_1:
        caminho = os.path.join(ROOT, caminho_pos(rel))
        linhas = le(caminho).splitlines(keepends=True)
        feitas = 0
        for i, linha in enumerate(linhas):
            if linha.lstrip().startswith("from .."):
                linhas[i] = linha.replace("from ..", "from ", 1)
                feitas += 1
        grava(caminho, "".join(linhas))
        print("  %-46s %d" % (caminho_pos(rel), feitas))

    print("\nFASE 5, REGRA 2: O PREFIXO `reconstructed.` SAI")
    for rel in REGRA_2:
        caminho = os.path.join(ROOT, rel)
        linhas = le(caminho).splitlines(keepends=True)
        feitas = 0
        for i, linha in enumerate(linhas):
            if re.match(r"\s*(from|import)\s", linha) and "reconstructed." in linha:
                linhas[i] = linha.replace("reconstructed.", "")
                feitas += 1
        grava(caminho, "".join(linhas))
        print("  %-46s %d" % (rel, feitas))

    print("\nFASE 6, PROSA, README, PYREFLY E WATCH")
    for rel, pares in PROSA:
        caminho = os.path.join(ROOT, rel)
        texto = le(caminho)
        for antes, depois in pares:
            if texto.count(antes) != 1:
                falhas.append("%s: %r deixou de ser unico" % (rel, antes[:50]))
                continue
            texto = texto.replace(antes, depois)
        grava(caminho, texto)
        print("  %-52s %d" % (rel, len(pares)))

    caminho_watch = os.path.join(ROOT, WATCH)
    texto = le(caminho_watch)
    if texto.count(W001_ANTES) != 1:
        falhas.append("W001: a linha nao foi encontrada exatamente uma vez")
    else:
        texto = texto.replace(W001_ANTES, W001_DEPOIS)
        if "## Observações" in texto:
            texto = texto.replace("## Observações", NOTA_WATCH + "\n## Observações", 1)
        grava(caminho_watch, texto)
        print("  %-52s W001 reescrito" % WATCH)

    print()
    print("=" * 78)
    if falhas:
        print("RESULTADO: %d PROBLEMA(S)" % len(falhas))
        for f in falhas:
            print("  " + f)
        return 1
    print("RESULTADO: NIVEL DE PACOTE ACHATADO")
    print("  quatro subpacotes subiram, reconstructed/ foi apagado,")
    print("  %d imports viraram absolutos, %d perderam o prefixo" % (n1, n2))
    print("=" * 78)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

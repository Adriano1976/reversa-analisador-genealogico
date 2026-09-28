"""Gera as fixtures que o harness diferencial consome.

Os `tests/fixtures/*.py` existentes sao GERADORES Python (constantes string), nao
arquivos `.ged`/`.csv` consumiveis pelo oraculo via `GedcomReader(file_path)`. Este
script materializa os arquivos.

Saida em `_reversa_sdd/parity/fixtures/`:
  - gedcom/: arquivos .ged (sinteticos + casos de borda)
  - dna/: arquivos .csv de matches

Uso:
    python _reversa_sdd/parity/make_fixtures.py
"""
from __future__ import annotations

import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
FIX = os.path.join(HERE, "fixtures")

# ---------------------------------------------------------------- GEDCOMs

# Arvore basica (do tests/fixtures/sample_gedcom.py), com acentos REAIS para
# exercitar mojibake/normalizacao no mesmo caminho do dado real.
GED_BASIC = """0 HEAD
1 SOUR PARITY
1 GEDC
2 VERS 5.5.1
2 FORM LINEAGE-LINKED
0 @I1@ INDI
1 NAME João /Silva/
1 SEX M
0 @I2@ INDI
1 NAME Maria /Souza/
1 SEX F
0 @I3@ INDI
1 NAME Carlos /Silva/
1 SEX M
1 FAMC @F1@
1 FAMS @F2@
0 @I4@ INDI
1 NAME Ana /Silva/
1 SEX F
1 FAMC @F1@
0 @I5@ INDI
1 NAME Bia /Oliveira/
1 SEX F
1 FAMS @F2@
0 @I6@ INDI
1 NAME Diego /Silva/
1 SEX M
1 FAMC @F2@
0 @I9@ INDI
1 NAME Lone /Ranger/
1 SEX M
0 @F1@ FAM
1 HUSB @I1@
1 WIFE @I2@
1 CHIL @I3@
1 CHIL @I4@
0 @F2@ FAM
1 HUSB @I3@
1 WIFE @I5@
1 CHIL @I6@
0 TRLR
"""

# Arvore com grafias variantes, nomes genericos e sufixos salvadores.
# Exercita BR-MIGRAR-006/007/011/012 (RISK-003: tabelas que so existem no codigo).
GED_VARIANTS = """0 HEAD
1 SOUR PARITY
1 GEDC
2 VERS 5.5.1
2 FORM LINEAGE-LINKED
0 @J1@ INDI
1 NAME José /Gouveia Netto/
1 SEX M
0 @J2@ INDI
1 NAME Maria /Silva Santos/
1 SEX F
0 @J3@ INDI
1 NAME José /Gouveia Neto/ Filho
1 SEX M
1 FAMC @G1@
0 @J4@ INDI
1 NAME Maria /Silva Santos/ Souza
1 SEX F
1 FAMC @G1@
0 @J5@ INDI
1 NAME João /Gouvêa Netto/
1 SEX M
0 @J6@ INDI
1 NAME Ana /Pereira/
1 SEX F
1 FAMS @G2@
0 @G1@ FAM
1 HUSB @J1@
1 WIFE @J2@
1 CHIL @J3@
1 CHIL @J4@
0 @G2@ FAM
1 HUSB @J3@
1 WIFE @J6@
1 CHIL @J4@
0 TRLR
"""

# Arvore com nome AUSENTE (sem tag NAME) e nome com formato vazio.
# Exercita a correcao factual de BR-MIGRAR-003 (AMB-024).
GED_NO_NAME = """0 HEAD
1 SOUR PARITY
1 GEDC
2 VERS 5.5.1
2 FORM LINEAGE-LINKED
0 @K1@ INDI
1 SEX M
0 @K2@ INDI
1 NAME Carlos /Silva/
1 SEX M
1 FAMC @H1@
0 @K3@ INDI
1 NAME //
1 SEX F
1 FAMC @H1@
0 @H1@ FAM
1 HUSB @K1@
1 CHIL @K2@
1 CHIL @K3@
0 TRLR
"""

# Arvore com encoding Latin-1 (mojibake) — gravada como bytes latin-1.
GED_MOJIBAKE = """0 HEAD
1 SOUR PARITY
1 GEDC
2 VERS 5.5.1
2 FORM LINEAGE-LINKED
0 @L1@ INDI
1 NAME JoÃ£o /Silva/
1 SEX M
0 @L2@ INDI
1 NAME ConceiÃ§Ã£o /Gouvea/
1 SEX F
0 @L3@ INDI
1 NAME Ana /Silva/
1 SEX F
1 FAMC @M1@
0 @M1@ FAM
1 HUSB @L1@
1 WIFE @L2@
1 CHIL @L3@
0 TRLR
"""

# Arvore maior: cadeia de 25 geracoes, para exercitar o limite max_depth=20
# (BR-MIGRAR-023: estourar o limite MUDA O FLUXO, nao e so performance).
def _ged_deep(levels: int = 25) -> str:
    lines = ["0 HEAD", "1 SOUR PARITY", "1 GEDC", "2 VERS 5.5.1", "2 FORM LINEAGE-LINKED"]
    for i in range(1, levels + 1):
        lines += ["0 @D%d@ INDI" % i, "1 NAME Pessoa%d /Cadeia/" % i, "1 SEX M"]
        if i > 1:
            lines.append("1 FAMC @FD%d@" % (i - 1))
    for i in range(1, levels):
        lines += ["0 @FD%d@ FAM" % i, "1 HUSB @D%d@" % i, "1 CHIL @D%d@" % (i + 1)]
    lines.append("0 TRLR")
    return "\n".join(lines) + "\n"


# Arvore com multiplas afinidades (exercita RISK-011: split_path_by_marriage)
GED_AFFINITY = """0 HEAD
1 SOUR PARITY
1 GEDC
2 VERS 5.5.1
2 FORM LINEAGE-LINKED
0 @A1@ INDI
1 NAME Alfa /Um/
1 SEX M
0 @A2@ INDI
1 NAME Beta /Dois/
1 SEX F
0 @A3@ INDI
1 NAME Gama /Tres/
1 SEX M
0 @A4@ INDI
1 NAME Delta /Quatro/
1 SEX F
0 @A5@ INDI
1 NAME Epsilon /Cinco/
1 SEX M
0 @A6@ INDI
1 NAME Zeta /Seis/
1 SEX F
0 @AF1@ FAM
1 HUSB @A1@
1 WIFE @A2@
0 @AF2@ FAM
1 HUSB @A3@
1 WIFE @A4@
0 @AF3@ FAM
1 HUSB @A5@
1 WIFE @A6@
0 TRLR
"""

# ---------------------------------------------------------------- CSVs de DNA

CSV_UTF8 = "Name,cM,Email\nAna Silva,200,ana@x.com\n"
CSV_DUPLICATED = "Name,cM\nAna Silva,387\nAna Silva,150\n"
CSV_NO_INTERSECTION = "Name,cM\nZzz Ninguem dos Santos,150\n"
CSV_GENERIC = "Name,cM\nMaria Souza,300\n"
CSV_CM_BOUNDARIES = (
    "Name,cM\n"
    "Ana Silva,0\n"
    "Ana Silva,-5\n"
    "Ana Silva,15\n"
    "Ana Silva,50\n"
    "Ana Silva,300\n"
    "Ana Silva,3400\n"
)
CSV_LATIN1 = "Name,cM\nConceição Gouvea,200\n"
CSV_MISSING_COL = "NomeCompleto,Total\nAna Silva,200\n"


def main() -> int:
    gdir = os.path.join(FIX, "gedcom")
    ddir = os.path.join(FIX, "dna")
    os.makedirs(gdir, exist_ok=True)
    os.makedirs(ddir, exist_ok=True)

    escritos = []

    def w(path, text, encoding="utf-8"):
        with open(path, "w", encoding=encoding, newline="\n") as fh:
            fh.write(text)
        escritos.append(path)

    w(os.path.join(gdir, "basic.ged"), GED_BASIC)
    w(os.path.join(gdir, "variants.ged"), GED_VARIANTS)
    w(os.path.join(gdir, "no_name.ged"), GED_NO_NAME)
    w(os.path.join(gdir, "mojibake_latin1.ged"), GED_MOJIBAKE, encoding="latin-1")
    w(os.path.join(gdir, "deep25.ged"), _ged_deep(25))
    w(os.path.join(gdir, "affinity.ged"), GED_AFFINITY)

    w(os.path.join(ddir, "utf8.csv"), CSV_UTF8)
    w(os.path.join(ddir, "duplicated.csv"), CSV_DUPLICATED)
    w(os.path.join(ddir, "no_intersection.csv"), CSV_NO_INTERSECTION)
    w(os.path.join(ddir, "generic.csv"), CSV_GENERIC)
    w(os.path.join(ddir, "cm_boundaries.csv"), CSV_CM_BOUNDARIES)
    w(os.path.join(ddir, "latin1.csv"), CSV_LATIN1, encoding="latin-1")
    w(os.path.join(ddir, "missing_col.csv"), CSV_MISSING_COL)

    for p in escritos:
        print("  %-46s %6d bytes" % (os.path.relpath(p, ROOT), os.path.getsize(p)))
    print("\n%d fixtures escritas em %s" % (len(escritos), os.path.relpath(FIX, ROOT)))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

"""GEDCOM sintético com sobrenomes ricos para testes do matching de DNA.

Estrutura:
  F1: @I10@ (Joaquim Silva) x @I11@ (Marta Souza)
        ├─ @I12@ (Carlos Silva Souza)   — raiz para o teste
        ├─ @I13@ (Ana Silva Souza)      — irmã, alvo do match
        └─ @I90@ (Lone Ranger)          — sem famílias
"""
DNA_GED = """0 HEAD
1 SOUR TEST
1 GEDC
2 VERS 5.5.1
2 FORM LINEAGE-LINKED
0 @I10@ INDI
1 NAME Joaquim /Silva/
1 SEX M
0 @I11@ INDI
1 NAME Marta /Souza/
1 SEX F
0 @I12@ INDI
1 NAME Carlos /Silva/ Souza
1 SEX M
1 FAMC @F10@
0 @I13@ INDI
1 NAME Ana /Silva/ Souza
1 SEX F
1 FAMC @F10@
0 @I90@ INDI
1 NAME Lone /Ranger/
1 SEX M
0 @F10@ FAM
1 HUSB @I10@
1 WIFE @I11@
1 CHIL @I12@
1 CHIL @I13@
0 TRLR
"""

# CSV UTF-8: match com a irmã (Ana Silva Souza) -> caminho ancestral até Carlos.
DNA_CSV_UTF8 = "Name,cM,Email\nAna Silva Souza,200,ana@x.com\n"
# Versão Latin-1 (iso-8859-1, com "Ferreira") para testar o fallback de encoding.
DNA_CSV_LATIN1_RAW = b"Name,cM\nAna Silva Souza Ferreira,200\n"

# Match com sobrenome sem interseção -> rejeitado (anti-falso-positivo).
DNA_CSV_NO_INTERSECTION = "Name,cM\nZzz Ninguem dos Santos,150\n"

# Segmentos duplicados do mesmo match -> cM somados: 387 + 150 = 537.
DNA_CSV_DUPLICATED = "Name,cM\nAna Silva Souza,387\nAna Silva Souza,150\n"
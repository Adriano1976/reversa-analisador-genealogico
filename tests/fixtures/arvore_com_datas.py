"""GEDCOMs sintéticos com datas para os testes do validador de dados.

Nenhum nome, kit ou data real: é tudo inventado para exercitar as regras de
viabilidade temporal. A árvore válida tem um doador nascido em 1970 e um match
nascido em 1950, primos de 1º grau, com MRCA em 1900.

Estrutura da árvore válida:

    @I10@ (Ancestral, 1900) x @I11@ (Ancestrala, 1902)
      ├─ @I2@ (Pai, 1945) x @I3@ (Mae, 1948)
      │    └─ @I1@ (Doador, 1970)
      └─ @I5@ (Tia, 1925) x @I6@ (Tio, 1922)
           └─ @I4@ (Primo, 1950)

O caminho do doador ao match tem 4 meioses (2 de cada lado); o MRCA é @I10@.
"""
from __future__ import annotations

GED_VALIDO = """0 HEAD
1 SOUR TEST
1 GEDC
2 VERS 5.5.1
2 FORM LINEAGE-LINKED
0 @I1@ INDI
1 NAME Doador /Sintetico/
1 SEX M
1 BIRT
2 DATE 1970
1 FAMC @F1@
0 @I2@ INDI
1 NAME Pai /Sintetico/
1 SEX M
1 BIRT
2 DATE 1945
1 FAMC @F2@
1 FAMS @F1@
0 @I3@ INDI
1 NAME Mae /Sintetica/
1 SEX F
1 BIRT
2 DATE 1948
1 FAMS @F1@
0 @I4@ INDI
1 NAME Primo /Sintetico/
1 SEX M
1 BIRT
2 DATE 1950
1 FAMC @F3@
0 @I5@ INDI
1 NAME Tia /Sintetica/
1 SEX F
1 BIRT
2 DATE 1925
1 FAMC @F2@
1 FAMS @F3@
0 @I6@ INDI
1 NAME Tio /Sintetico/
1 SEX M
1 BIRT
2 DATE 1922
1 FAMS @F3@
0 @I10@ INDI
1 NAME Ancestral /Sintetico/
1 SEX M
1 BIRT
2 DATE 1900
1 FAMS @F2@
0 @I11@ INDI
1 NAME Ancestrala /Sintetica/
1 SEX F
1 BIRT
2 DATE 1902
1 FAMS @F2@
0 @F1@ FAM
1 HUSB @I2@
1 WIFE @I3@
1 CHIL @I1@
0 @F2@ FAM
1 HUSB @I10@
1 WIFE @I11@
1 CHIL @I2@
1 CHIL @I5@
0 @F3@ FAM
1 HUSB @I6@
1 WIFE @I5@
1 CHIL @I4@
0 TRLR
"""

GED_DOADOR_VIVO_SECULO_XVII = """0 HEAD
1 SOUR TEST
1 GEDC
2 VERS 5.5.1
2 FORM LINEAGE-LINKED
0 @I1@ INDI
1 NAME Doador /Sintetico/
1 SEX M
1 BIRT
2 DATE 1985
1 FAMC @F1@
0 @I2@ INDI
1 NAME Pai /Sintetico/
1 SEX M
1 BIRT
2 DATE 1960
1 FAMC @F2@
1 FAMS @F1@
0 @I3@ INDI
1 NAME Mae /Sintetica/
1 SEX F
1 BIRT
2 DATE 1962
1 FAMS @F1@
0 @I4@ INDI
1 NAME Primo /Sintetico/
1 SEX M
1 BIRT
2 DATE 1950
1 FAMC @F3@
0 @I5@ INDI
1 NAME Tia /Sintetica/
1 SEX F
1 BIRT
2 DATE 1925
1 FAMC @F2@
1 FAMS @F3@
0 @I6@ INDI
1 NAME Tio /Sintetico/
1 SEX M
1 BIRT
2 DATE 1922
1 FAMS @F3@
0 @I10@ INDI
1 NAME Ancestral /Sintetico/
1 SEX M
1 BIRT
2 DATE 1650
1 FAMS @F2@
0 @I11@ INDI
1 NAME Ancestrala /Sintetica/
1 SEX F
1 BIRT
2 DATE 1652
1 FAMS @F2@
0 @F1@ FAM
1 HUSB @I2@
1 WIFE @I3@
1 CHIL @I1@
0 @F2@ FAM
1 HUSB @I10@
1 WIFE @I11@
1 CHIL @I2@
1 CHIL @I5@
0 @F3@ FAM
1 HUSB @I6@
1 WIFE @I5@
1 CHIL @I4@
0 TRLR
"""

GED_SEM_DATA = """0 HEAD
1 SOUR TEST
1 GEDC
2 VERS 5.5.1
2 FORM LINEAGE-LINKED
0 @I1@ INDI
1 NAME Doador /Sintetico/
1 SEX M
1 BIRT
2 DATE 1970
1 FAMC @F1@
0 @I2@ INDI
1 NAME Pai /Sintetico/
1 SEX M
1 BIRT
2 DATE 1945
1 FAMC @F2@
1 FAMS @F1@
0 @I3@ INDI
1 NAME Mae /Sintetica/
1 SEX F
1 BIRT
2 DATE 1948
1 FAMS @F1@
0 @I4@ INDI
1 NAME Primo /Sintetico/
1 SEX M
1 FAMC @F3@
0 @I5@ INDI
1 NAME Tia /Sintetica/
1 SEX F
1 BIRT
2 DATE 1925
1 FAMC @F2@
1 FAMS @F3@
0 @I6@ INDI
1 NAME Tio /Sintetico/
1 SEX M
1 BIRT
2 DATE 1922
1 FAMS @F3@
0 @I10@ INDI
1 NAME Ancestral /Sintetico/
1 SEX M
1 BIRT
2 DATE 1900
1 FAMS @F2@
0 @I11@ INDI
1 NAME Ancestrala /Sintetica/
1 SEX F
1 BIRT
2 DATE 1902
1 FAMS @F2@
0 @F1@ FAM
1 HUSB @I2@
1 WIFE @I3@
1 CHIL @I1@
0 @F2@ FAM
1 HUSB @I10@
1 WIFE @I11@
1 CHIL @I2@
1 CHIL @I5@
0 @F3@ FAM
1 HUSB @I6@
1 WIFE @I5@
1 CHIL @I4@
0 TRLR
"""

CSV_UM_KIT = "Name,cM,Kit\nPrimo Sintetico,800,AB1234567\n"

CSV_DOIS_KITS = (
    "Name,cM,Kit\n"
    "Primo Sintetico,800,AB1234567\n"
    "Primo Sintetico,20,CD7654321\n"
)

CSV_SEM_MATCH = "Name,cM,Kit\nNinguem,100,AB1234567\n"

CSV_VAZIO = "Name,cM,Kit\n"

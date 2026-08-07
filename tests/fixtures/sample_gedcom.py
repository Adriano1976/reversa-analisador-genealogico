"""GEDCOM sintético mínimo para os testes do Reconstructor.

Árvore construída:
  F1: @I1@ (Avô João)  x  @I2@ (Avó Maria)
        ├─ @I3@ (Carlos)   — filho
        └─ @I4@ (Ana)      — filha
  F2: @I3@ (Carlos) x @I5@ (Bia)  -> @I6@ (Diego)

Casos de teste:
- Direto:  Carlos (I3) e Ana (I4) -> ancestral comum I1/I2
- Indireto: Carlos (I3) e Bia (I5) -> casamento em F2
- Inexistente: "Zzz Ninguém"
- Sem conexão: @I9@ (Lone Ranger, sem famílias)
- Idênticas: Carlos e Carlos
"""
SAMPLE_GED = """0 HEAD
1 SOUR TEST
1 GEDC
2 VERS 5.5.1
2 FORM LINEAGE-LINKED
0 @I1@ INDI
1 NAME Joao /Silva/
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

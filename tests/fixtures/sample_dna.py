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

# ---------------------------------------------------------------------------
# Feature 040 — fonte suja e medida
# ---------------------------------------------------------------------------

# A coluna `Source` como ela chega de verdade: texto de formulário, empresa não confirmada,
# haplogrupo na coluna errada e um laboratório grafado com caixa alta. Nenhum valor é de
# arquivo real: são as FORMAS medidas em 2026-10-22, com nomes sintéticos.
DNA_CSV_FONTE_SUJA = (
    "Name,cM,Chromosome,SNPs,Kit,Source\n"
    "Ana Silva Souza,200,1,1500,AB1234567,Outro (insira o nome abaixo)\n"
)

# Medida robusta: total e maior bloco acima de 15 cM, SNPs acima de 900.
DNA_CSV_MEDIDA_ROBUSTA = (
    "Name,cM,Chromosome,SNPs,Kit,Source\n"
    "Ana Silva Souza,200,1,1500,AB1234567,Genera\n"
)

# Medida parcial: total 16 cM (passa de 15), maior bloco 8 cM (não passa).
DNA_CSV_MEDIDA_PARCIAL = (
    "Name,cM,Chromosome,SNPs,Kit,Source\n"
    "Ana Silva Souza,8,1,500,AB1234567,Genera\n"
    "Ana Silva Souza,8,2,500,AB1234567,Genera\n"
)

# Medida insuficiente: total 9 cM, abaixo do piso de 15.
DNA_CSV_MEDIDA_INSUFICIENTE = (
    "Name,cM,Chromosome,SNPs,Kit,Source\n"
    "Ana Silva Souza,9,1,500,AB1234567,Genera\n"
)

# O mesmo kit declarando dois laboratórios: alimenta o aviso `fontes_divergentes`.
DNA_CSV_FONTES_DIVERGENTES = (
    "Name,cM,Chromosome,SNPs,Kit,Source\n"
    "Ana Silva Souza,100,1,900,AB1234567,Genera\n"
    "Ana Silva Souza,100,2,900,AB1234567,MyHeritage\n"
)

# Nome de projeto na coluna de fonte: o valor nao e' laboratorio e o cartao precisa dizer o que e'.
DNA_CSV_FONTE_NOME_DE_PROJETO = (
    "Name,cM,Chromosome,SNPs,Kit,Source\n"
    "Ana Silva Souza,200,1,1500,AB1234567,Migration - F2 - T\n"
)

# Celula de fonte vazia (aqui, `-`): nao ha texto util para mostrar na etiqueta.
DNA_CSV_FONTE_VAZIA = (
    "Name,cM,Chromosome,SNPs,Kit,Source\n"
    "Ana Silva Souza,200,1,1500,AB1234567,-\n"
)

# ---------------------------------------------------------------------------
# Feature 044 — o destaque da hipotese mais proxima
# ---------------------------------------------------------------------------

# 154,5 cM: o UNICO valor do arquivo real em que tres relacoes ficam dentro da banda
# de 1,5x (distancias 32,5 / 34,5 / 37,5 da media). E o cartao da "Clezia Santos",
# reproduzido com nome sintetico.
DNA_CSV_HIPOTESE_TRES_DESTAQUES = (
    "Name,cM,Chromosome,SNPs,Kit,Source\n"
    "Ana Silva Souza,154.5,1,1500,AB1234567,Genera\n"
)

# 42,6 cM: duas relacoes dentro da banda, e as duas sao vizinhas de uma remocao
# (Primos de 3º grau 1x removido e Primos de 4º grau) — o que o cM nao distingue.
DNA_CSV_HIPOTESE_DOIS_DESTAQUES = (
    "Name,cM,Chromosome,SNPs,Kit,Source\n"
    "Ana Silva Souza,42.6,1,1500,AB1234567,Genera\n"
)
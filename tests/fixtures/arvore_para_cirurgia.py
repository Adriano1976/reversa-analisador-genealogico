"""GEDCOMs sintéticos para os testes da cirurgia do grafo.

Nenhum nome, kit ou data real: tudo inventado. Três árvores, cada uma com um
propósito:

- ``GED_SALTO_IMPOSSIVEL`` — doador vivo (1985) ligado a um ancestral de 1650 por
  **duas** gerações no lado do doador. É o caso que motiva a feature: o salto
  I10→I2 tem 310 anos e a idade por lado dá 167,5 anos por geração.
- ``GED_LINHA_VALIDA`` — doador (1970) e match (1950), primos de 1º grau, MRCA em
  1900. Todos os saltos plausíveis: serve para provar que ``VALIDADO`` **não** gera
  sugestão.
- ``GED_MATCH_SEM_FAMILIA`` — o match não tem registro de família, então não há
  caminho documental. Serve para ``SEM_CAMINHO_DOCUMENTAL``.
- ``GED_DOIS_LADOS`` — o ancestral tem **dois** filhos em famílias diferentes, e as
  duas linhas têm salto implausível (1650 → 1960 no lado do doador; 1650 → 1918 no
  lado do match). Serve para as duas junções distintas e para a divisão proporcional.

## Por que não há uma árvore "por casamento"

``documentary_relationship`` nunca devolve ``status="affinity"``: a afinidade nasce
em ``core.path_search`` (caminho indireto por ``nx.shortest_path``), não no
parentesco documental. Um GEDCOM aqui não produziria o caso; por isso o cenário de
afinidade é exercitado com um ``documental`` montado à mão nos testes. A árvore
com casamento (``F1``: I2 x I3) serve ao teste de "casamento nunca é cortado",
que tenta cortar uma aresta entre cônjuges.
"""
from __future__ import annotations

GED_SALTO_IMPOSSIVEL = """0 HEAD
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
2 DATE 1710
1 FAMC @F3@
0 @I5@ INDI
1 NAME Tia /Sintetica/
1 SEX F
1 BIRT
2 DATE 1680
1 FAMC @F2@
1 FAMS @F3@
0 @I6@ INDI
1 NAME Tio /Sintetico/
1 SEX M
1 BIRT
2 DATE 1678
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

GED_LINHA_VALIDA = """0 HEAD
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

GED_MATCH_SEM_FAMILIA = """0 HEAD
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
0 @F1@ FAM
1 HUSB @I2@
1 WIFE @I3@
1 CHIL @I1@
0 TRLR
"""

GED_DOIS_LADOS = """0 HEAD
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
0 @I10@ INDI
1 NAME Ancestral /Sintetico/
1 SEX M
1 BIRT
2 DATE 1650
1 FAMS @F2@
1 FAMS @F4@
0 @I11@ INDI
1 NAME Ancestrala /Sintetica/
1 SEX F
1 BIRT
2 DATE 1652
1 FAMS @F2@
1 FAMS @F4@
0 @I12@ INDI
1 NAME Tio-Avo /Sintetico/
1 SEX M
1 BIRT
2 DATE 1918
1 FAMC @F4@
1 FAMS @F5@
0 @I13@ INDI
1 NAME Primo Distante /Sintetico/
1 SEX M
1 BIRT
2 DATE 1940
1 FAMC @F5@
0 @I14@ INDI
1 NAME Esposa /Sintetica/
1 SEX F
1 BIRT
2 DATE 1920
1 FAMS @F5@
0 @F1@ FAM
1 HUSB @I2@
1 WIFE @I3@
1 CHIL @I1@
0 @F2@ FAM
1 HUSB @I10@
1 WIFE @I11@
1 CHIL @I2@
0 @F4@ FAM
1 HUSB @I10@
1 WIFE @I11@
1 CHIL @I12@
0 @F5@ FAM
1 HUSB @I12@
1 WIFE @I14@
1 CHIL @I13@
0 TRLR
"""

#: cM baixo: a envoltória publicada alcança relações distantes, o que produz um
#: número de gerações estimadas bem maior que as 2 documentadas — é o que gera hiato.
CSV_SALTO = "Name,cM,Kit\nPrimo Sintetico,25,AB1234567\n"

#: cM alto: relação próxima, compatível com o caminho de 4 meioses da árvore válida.
CSV_VALIDO = "Name,cM,Kit\nPrimo Sintetico,800,AB1234567\n"

#: Um kit quebrado e um validado para o mesmo nome, para o teste de agregação.
CSV_DOIS_KITS = (
    "Name,cM,Kit\n"
    "Primo Sintetico,800,AB1234567\n"
    "Primo Sintetico,25,CD7654321\n"
)

#: Kit cujo nome não existe na árvore.
CSV_SEM_MATCH = "Name,cM,Kit\nNinguem,100,AB1234567\n"

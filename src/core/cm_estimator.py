"""Estimador de parentesco por faixas de cM.

Extraido de `dna_analysis.py` pela OPP-20261003-RGKA. Responsabilidade unica:
traduzir um valor de cM (soma dos segmentos de um match) na lista das relacoes
provaveis daquela faixa. Nao conhece grafo, GEDCOM, CSV nem fluxo de analise.

Nenhum valor de faixa e nenhuma ordem de avaliacao foram alterados na extracao.

## Origem da tabela (principio V)

`SHARED_CM_DATA` **nao tem fonte externa verificavel**. As nove faixas foram
escritas a mao, e a decisao humana de 2026-09-30 (`_reversa_sdd/questions.md`,
pergunta 5) determina declara-las como heuristica, nao como tabela canonica:

- `_reversa_sdd/analise-dna/requirements.md` RF-10a: as faixas sao heuristicas
  sem fonte verificavel, e a reimplementacao pode trata-las como parametro
  ajustavel.
- A sobreposicao de ate quatro faixas e consequencia do metodo de escrita a
  mao, e nao do Shared cM Project.
- O `README.md` menciona o Shared cM Project, mas nao registra versao nem os
  dados que teriam gerado estas faixas.
- `_reversa_sdd/domain.md` registra a lacuna L-07.

O principio V pede referencia e data de consulta. Nao existe referencia a citar:
o que este comentario declara e a ausencia dela, para que nenhum leitor tome as
faixas por calibradas. Se a versao usada como inspiracao for recuperada, este e
o unico lugar a atualizar.

Declarado em 2026-10-03, sobre decisao humana de 2026-09-30.
"""

SHARED_CM_DATA = [
    {"range": (3300, 3720), "relationship": "Pai/Mãe ↔ Filho(a)"},
    {"range": (2200, 3400), "relationship": "Irmãos completos"},
    {"range": (1317, 2312), "relationship": "Avós/Netos, Tios/Tias ↔ Sobrinhos(as), Meios-irmãos"},
    {"range": (553, 1330), "relationship": "Primos de 1º grau"},
    {"range": (200, 850), "relationship": "Primos de 1º grau (1× removido), Meios-primos, Tios-avós ↔ Sobrinhos-netos"},
    {"range": (46, 515), "relationship": "Primos de 2º grau"},
    {"range": (30, 350), "relationship": "Primos de 2º grau (1× removido), Primos de 3º grau"},
    {"range": (10, 220), "relationship": "Primos de 3º grau (1× removido), Primos de 4º grau"},
    {"range": (0, 110), "relationship": "Primos de 4º/5º grau ou mais distantes"},
]


def get_relationships_by_cm(cm_value):
    """Devolve as relações prováveis da faixa em que `cm_value` cai.

    Contrato (D-17 da extração): o retorno é **sempre uma lista**. `cM` menor ou
    igual a zero, ou valor não numérico, devolvem lista **vazia**. O literal
    "Relação distante ou indeterminada" só aparece para número positivo que não
    cai em nenhuma das nove faixas. Como as faixas se sobrepõem, a lista pode
    trazer mais de uma relação, e a ordem é a da tabela acima.
    """
    if not isinstance(cm_value, (int, float)) or cm_value <= 0:
        return []
    poss = [item["relationship"] for item in SHARED_CM_DATA if item["range"][0] <= cm_value <= item["range"][1]]
    return poss if poss else ["Relação distante ou indeterminada"]

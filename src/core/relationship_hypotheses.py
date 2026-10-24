"""Possibilidades de parentesco a partir do cM observado.

Responsabilidade unica: traduzir um total de cM em **possibilidades** de
parentesco, usando a tabela publicada do Shared cM Project 4.0. Nunca devolve um
parentesco unico, nunca "confirma" nada e nunca le o GEDCOM.

## Regra do projeto

cM -> conjunto de possibilidades. O parentesco documental vem do GEDCOM
(`core.documentary_relationship`) e nao e tocado por este modulo. A comparacao
entre os dois mora em `core.evidence_comparison`.

## Fonte (Shared cM Project 4.0)

- Bettinger, B. T. *The Shared cM Project Version 4.0 (March 2020)*, PDF oficial:
  https://thegeneticgenealogist.com/wp-content/uploads/2020/03/Shared-cM-Project-Version-4.pdf
- DNA Painter, *Shared cM Project 4.0 tool*:
  https://dnapainter.com/tools/sharedcmv4
- Anuncio da versao: https://thegeneticgenealogist.com/2020/03/27/version-4-0-march-2020-update-to-the-shared-cm-project/
- 59.714 envios ate 08/07/2019; 55.418 usados nas 48 relacoes analisadas.

O que a fonte diz e o que ela **nao** diz, porque isso muda a leitura da tela:

- A coluna "Range" da fonte e, literalmente, "Range (low to high; 99th
  percentile)": 1% dos envios foi removido (0,5% em cada ponta) antes de reportar
  minimo e maximo. Nao e o intervalo observado completo.
- **A versao 4.0 nao publica mediana** para relacao nenhuma (so numero de envios,
  minimo, media, maximo e desvio padrao). Por isso `average` existe aqui e
  `median` nao.
- As distribuicoes **se sobrepoem**: a propria fonte registra que "o cM total nao
  pode ser utilizado para diferenciar meios-irmaos de tio/tia" (PDF, p.49).
- **Endogamia e colapso de pedigree aumentam** o cM compartilhado para o mesmo
  parentesco genealogico (PDF, p.1), e as estatisticas "nao atendem colapso de
  pedigree ou endogamia" (DNA Painter). O valor lido, portanto, e um teto otimista
  nesses casos.
- Para relacoes cujo minimo e 0 cM, **a media so considera quem compartilha DNA
  detectavel** (PDF, p.4). Nao e a media de todos os primos de 5º grau, e sim a
  dos que compartilham algo.
- A fonte **nao afirma** nada sobre "segmento abaixo de X cM e falso positivo".
  O limite `LIMITE_SEGMENTO_FRACO` de `core.genetic_evidence` e criterio do
  projeto, e a tela deve apresenta-lo como tal.
- Relacoes **nao publicadas** na 4.0 (nao invente numero para elas): 1C4R, 1C5R,
  1C6R, 3C2R, 2º bisavô/avó e 3º bisavô/avó. Faltam justamente as mais distantes,
  que e onde o caso real deste repositorio cai.

## O antepassado comum nao vem da fonte, e sim da definicao

A coluna "Antepassado comum mais recente" do bloco 3 nao e um dado do Shared cM
Project: e a **definicao** de cada parentesco. Primo de 2º grau tem os bisavos como
antepassado comum porque e isso que "primo de 2º grau" quer dizer — nao porque a
fonte publicou. Por isso ela nao tem versao, nao envelhece com a 5.0 e nao precisa
de ressalva estatistica.

A tabela `GRAUS_ATE_O_MRCA` guarda, por chave publicada, quantas geracoes cada lado
sobe ate o antepassado. `tests/test_mrca_e_posicao_na_faixa.py` faz a **ida e
volta**: joga esses graus em `core.documentary_relationship.documentary_label` e
exige que a chave devolvida seja a mesma. Duas fontes que discordem quebram o
teste, e nao a tela.

## O destaque e' heuristica do projeto, como a confianca

A fonte **nao ranqueia** nada: publica faixa e media por relacao, e declara que as
distribuicoes se sobrepoem. O bloco 3 da tela aponta ate tres relacoes mesmo assim,
porque a pergunta "qual delas?" e' do operador — e a resposta e' do projeto, nao da
fonte. Duas constantes fazem o corte: `BANDA_DE_DESTAQUE` (1,5x a menor distancia) e
`MAXIMO_DE_DESTAQUES` (3).

O que impede o destaque de virar veredito nao e' a constante, e' o texto: o rotulo
fala em "media publicada", a ressalva diz **entre quantas** relacoes a escolha foi
feita e nega confirmacao. Retirar qualquer uma dessas tres partes muda a natureza do
bloco — e' o mesmo cuidado que `_confianca` pede ao se declarar heuristica.
"""
from __future__ import annotations

from typing import TypedDict

from .graus_de_parentesco import nome_do_grau, nome_do_primo

SCP40_META = {
    "version": "4.0",
    "release": "março de 2020",
    "sample_size": 59714,
    "range_definition": "faixa (mínimo–máximo) após remoção de 1% dos envios (0,5% em cada ponta); "
                        "não é o intervalo observado completo",
    "sources": [
        "https://thegeneticgenealogist.com/wp-content/uploads/2020/03/Shared-cM-Project-Version-4.pdf",
        "https://dnapainter.com/tools/sharedcmv4",
    ],
}

# (chave interna, nome na fonte, nome em português, meioses, média, mínimo, máximo)
# `meioses` = número de saltos pai-filho entre as duas pessoas; é a grandeza que o
# cM mede. Relações diferentes com o mesmo número de meioses se sobrepõem — é por
# isso que a resposta é uma lista.
SCP40_ROWS = [
    ("PARENT_CHILD", "Parent/Child", "Pai/Mãe ↔ Filho(a)", 1, 3485, 3330, 3720),
    ("SIBLINGS", "Sibling", "Irmãos completos", 2, 2613, 1613, 3488),
    ("HALF_SIBLINGS", "Half Sibling", "Meios-irmãos", 2, 1759, 1160, 2436),
    ("GRANDPARENT", "Grandparent/Grandchild", "Avô/Avó ↔ Neto(a)", 2, 1754, 984, 2462),
    ("AUNT_UNCLE", "Aunt / Uncle", "Tio/Tia ↔ Sobrinho(a)", 3, 1741, 1201, 2282),
    ("DIRECT_3", "Great-Grandparent/Great-Grandchild", "Bisavô/Bisavó ↔ Bisneto(a)", 3, 887, 485, 1486),
    ("GREAT_AUNT_1", "Great-Aunt / Uncle", "Tio/Tia-avô/avó ↔ Sobrinho(a)-neto(a)", 4, 850, 330, 1467),
    ("GREAT_AUNT_2", "Great-Great-Aunt / Uncle", "Tio/Tia-bisavô/avó ↔ Sobrinho(a)-bisneto(a)", 5, 420, 186, 713),
    ("1C", "1C", "Primos de 1º grau", 2, 866, 396, 1397),
    ("1C1R", "1C1R", nome_do_primo(1, 1), 3, 433, 102, 980),
    ("1C2R", "1C2R", nome_do_primo(1, 2), 4, 221, 33, 471),
    ("1C3R", "1C3R", nome_do_primo(1, 3), 5, 117, 25, 238),
    ("2C", "2C", "Primos de 2º grau", 4, 229, 41, 592),
    ("2C1R", "2C1R", nome_do_primo(2, 1), 5, 122, 14, 353),
    ("2C2R", "2C2R", nome_do_primo(2, 2), 6, 71, 0, 244),
    ("2C3R", "2C3R", nome_do_primo(2, 3), 7, 51, 0, 154),
    ("3C", "3C", "Primos de 3º grau", 6, 73, 0, 234),
    ("3C1R", "3C1R", nome_do_primo(3, 1), 7, 48, 0, 192),
    ("4C", "4C", "Primos de 4º grau", 8, 35, 0, 139),
    ("4C1R", "4C1R", nome_do_primo(4, 1), 9, 28, 0, 126),
    ("5C", "5C", "Primos de 5º grau", 10, 25, 0, 117),
    ("5C1R", "5C1R", nome_do_primo(5, 1), 11, 21, 0, 80),
    ("6C", "6C", "Primos de 6º grau", 12, 18, 0, 71),
    ("7C", "7C", "Primos de 7º grau", 14, 14, 0, 57),
    ("8C", "8C", "Primos de 8º grau", 16, 11, 0, 42),
    ("HALF_1C", "Half 1C", "Meio-primos de 1º grau", 3, 449, 156, 979),
    ("HALF_2C", "Half 2C", "Meio-primos de 2º grau", 5, 120, 10, 325),
]

# Relações que a 4.0 não publica. A lista existe para que o confronto saiba
# dizer "não há faixa publicada" em vez de inventar uma.
#
# O texto das entradas `DIRECT_*` seguia a série `2º bisavô`, `3º bisavô`, que não é a
# nomenclatura corrente — a série em português é `bisavô → trisavô → tetravô → pentavô`
# (ver `documentary_label.nome_do_grau`, e `tests/test_rotulos_de_parentesco.py`). Alinhado
# em 2026-10-14 com a mesma correção que tirou `bisbisavô` dos rótulos de parentesco.
SCP40_NOT_PUBLISHED = {
    "1C4R": "não analisada na versão 4.0",
    "1C5R": "não analisada na versão 4.0",
    "1C6R": "não analisada na versão 4.0",
    "3C2R": "não analisada na versão 4.0",
    "DIRECT_4": "trisavô/avó: não analisada na versão 4.0",
    "DIRECT_5": "tetravô/avó: não analisada na versão 4.0",
}


# Quantas geracoes cada lado sobe ate o antepassado comum mais recente
# Nao e dado da fonte: e a definicao de cada parentesco. Primo de 2º grau -> bisavos.
# As chaves sao as mesmas de `SCP40_ROWS`, e o teste de ida e volta garante que os
# graus aqui concordam com `core.documentary_relationship.documentary_label`.
GRAUS_ATE_O_MRCA = {
    "PARENT_CHILD": (0, 1),
    "SIBLINGS": (1, 1),
    "GRANDPARENT": (0, 2),
    "AUNT_UNCLE": (1, 2),
    "DIRECT_3": (0, 3),
    "GREAT_AUNT_1": (1, 3),
    "GREAT_AUNT_2": (1, 4),
    "1C": (2, 2),
    "1C1R": (2, 3),
    "1C2R": (2, 4),
    "1C3R": (2, 5),
    "2C": (3, 3),
    "2C1R": (3, 4),
    "2C2R": (3, 5),
    "2C3R": (3, 6),
    "3C": (4, 4),
    "3C1R": (4, 5),
    "4C": (5, 5),
    "4C1R": (5, 6),
    "5C": (6, 6),
    "5C1R": (6, 7),
    "6C": (7, 7),
    "7C": (8, 8),
    "8C": (9, 9),
}

# As tres meias-relacoes ficam FORA de `GRAUS_ATE_O_MRCA` de proposito: o grau delas
# e o mesmo do equivalente completo, e e justamente isso que `documentary_label` nao
# consegue dizer — `(1,1)` devolve SIBLINGS, e nao HALF_SIBLINGS. O que muda nao e a
# profundidade, e sim quantos dos dois lados do casal sao compartilhados.
GRAUS_DAS_MEIAS_RELACOES = {
    "HALF_SIBLINGS": (1, 1),
    "HALF_1C": (2, 2),
    "HALF_2C": (3, 3),
}

#: Rotulo da posicao do valor observado dentro da faixa publicada. Descreve a fonte;
#: nao e probabilidade, e nao soma nada com nada.
POSICOES_NA_FAIXA = {
    "ponta_inferior": "na ponta inferior",
    "abaixo_do_centro": "abaixo do centro",
    "centro": "no centro",
    "acima_do_centro": "acima do centro",
    "ponta_superior": "na ponta superior",
}

# O DESTAQUE: a tela aponta a hipotese mais proxima, e diz com que criterio
# A fonte nao ranqueia nada — ela publica faixa e media por relacao. O destaque e'
# heuristica DO PROJETO, como `_confianca`, e a tela precisa apresenta-lo como tal.
#
# Duas constantes, e a segunda existe para o cartao nao virar um segundo bloco 3:
#
# - BANDA_DE_DESTAQUE: a segunda (e a terceira) so' e' destacada quando a distancia
#   dela a media nao passa deste fator vezes a distancia da primeira. Sem banda, o
#   destaque seria um numero fixo de linhas escolhidas por nada.
# - MAXIMO_DE_DESTAQUES: teto, para que um empate largo nao vire lista nova.
#
# Medido em 2026-10-22 nos 456 kits do arquivo real (`Famílias_Sergipanas.csv`), com
# a banda de 1,5x: **423 com um destaque, 32 com dois, 1 com tres**. A mediana de
# d2/d1 e' 1,88 — a segunda costuma estar quase duas vezes mais longe que a primeira.
# Os 32 casos de dois sao, quase todos, vizinhos de UMA geracao de diferenca (4C com
# 4C1R, 5C com 5C1R): exatamente o que o cM nao distingue. O unico caso de tres e' o
# kit AZ4078391, com 154,5 cM.
BANDA_DE_DESTAQUE = 1.5
MAXIMO_DE_DESTAQUES = 3

ROTULOS_DE_DESTAQUE = {
    1: "Hipótese mais próxima da média publicada",
    2: "Duas relações praticamente empatadas pela distância da média",
    3: "Três relações praticamente empatadas pela distância da média",
}


def _geracoes(quantidade: int) -> str:
    """`1 geração acima` / `3 gerações acima` — o singular e um caso a parte."""
    return "1 geração" if quantidade == 1 else f"{quantidade} gerações"


def graus_ate_o_mrca(chave: str):
    """As duas subidas ate o antepassado comum, ou None para chave desconhecida."""
    return GRAUS_ATE_O_MRCA.get(chave) or GRAUS_DAS_MEIAS_RELACOES.get(chave)


def mrca_da_relacao(chave: str):
    """Onde procurar o antepassado comum, em palavras, para a chave canonica.

    Devolve `graus`, `rotulo` e `detalhe`. O rotulo e o conjunto de antepassados
    (`bisavós`); o detalhe diz a profundidade e, quando os dois lados nao sobem o
    mesmo numero de geracoes, diz que sao dois. A profundidade e **por lado** porque
    numa relacao com diferenca de geracao — "primo de 2º grau dos pais", o 2C1R — o antepassado
    esta a 3 geracoes de uma pessoa e a 4 da outra. Escolher um dos lados seria
    inventar qual das duas pessoas e a raiz.
    """
    graus = graus_ate_o_mrca(chave)
    if not graus:
        return None

    baixo, alto = graus
    meia = chave in GRAUS_DAS_MEIAS_RELACOES

    if baixo == alto:
        palavra = nome_do_grau(alto, plural_ancestral=True)
        rotulo = f"{palavra} (um de dois)" if meia else palavra
        detalhe = f"{_geracoes(alto)} acima, nos dois lados"
        if meia:
            detalhe += f"; só um dos {palavra} é compartilhado"
        return {"graus": [baixo, alto], "rotulo": rotulo, "detalhe": detalhe}

    maior = max(baixo, alto)
    if 0 in (baixo, alto):
        # Ascendente direto: de um lado o antepassado E a outra pessoa.
        return {
            "graus": [baixo, alto],
            "rotulo": nome_do_grau(maior, plural_ancestral=True),
            "detalhe": f"{_geracoes(maior)} acima; um dos dois é o próprio antepassado",
        }

    return {
        "graus": [baixo, alto],
        "rotulo": (f"{nome_do_grau(baixo, plural_ancestral=True)} "
                   f"e {nome_do_grau(alto, plural_ancestral=True)}"),
        "detalhe": f"{baixo} e {alto} gerações acima",
    }


def destaque_das_candidatas(candidatas: list, total_cm: float):
    """O bloco de destaque do cartao, ou None sem candidata.

    Escolhe as candidatas cuja distancia a media nao passa de `BANDA_DE_DESTAQUE`
    vezes a MENOR distancia, no maximo `MAXIMO_DE_DESTAQUES`. Marca cada escolhida
    com `destaque=True` na propria candidata (a lista continua inteira: o destaque
    e' leitura, nao substituicao).

    Devolve `quantidade`, `rotulo`, `itens` (nome, distancia, media e onde procurar)
    e `ressalva` — a frase que impede o destaque de ser lido como conclusao. O
    numero de relacoes compativeis entra na ressalva porque e' o que o destaque
    esconde: uma hipotese destacada entre 13 nao tem a forca de uma entre duas.
    """
    if not candidatas:
        return None

    distancias = [abs(c["average"] - total_cm) for c in candidatas]
    limite = min(distancias) * BANDA_DE_DESTAQUE
    escolhidas = [c for c in candidatas if abs(c["average"] - total_cm) <= limite]
    escolhidas = escolhidas[:MAXIMO_DE_DESTAQUES]

    for candidata in candidatas:
        candidata["destaque"] = False
    for candidata in escolhidas:
        candidata["destaque"] = True

    itens = [{
        "nome": candidata["name_pt"],
        "distancia": round(abs(candidata["average"] - total_cm), 1),
        "media": candidata["average"],
        "onde": (candidata.get("mrca") or {}).get("rotulo"),
        "mrca": candidata.get("mrca"),
    } for candidata in escolhidas]

    quantidade = len(itens)
    total = len(candidatas)
    if total == 1:
        abertura = "A única relação compatível"
    else:
        abertura = f"Entre as {total} relações compatíveis"
    if quantidade == 1:
        fecho = ("esta é a mais próxima da média das faixas publicadas — e isso não é "
                 "confirmação: o parentesco documental continua vindo do GEDCOM.")
    else:
        fecho = ("estas são as mais próximas da média das faixas publicadas — e isso não é "
                 "confirmação: o parentesco documental continua vindo do GEDCOM.")

    return {
        "quantidade": quantidade,
        "rotulo": ROTULOS_DE_DESTAQUE[quantidade],
        "itens": itens,
        "ressalva": f"{abertura}, {fecho}",
    }


def posicao_na_faixa(total_cm: float, faixa_baixa: float, faixa_alta: float) -> dict:
    """Onde o valor observado cai DENTRO da faixa publicada da relacao.

    Nao e probabilidade e nao e "confianca": e a leitura da faixa publicada contra o
    numero observado. Serve para o operador ver o que a lista hoje esconde — um
    valor na ponta inferior da faixa de `Primos de 1º grau` e tecnicamente
    compativel e, ao mesmo tempo, o membro mais fraco daquela faixa.
    """
    largura = faixa_alta - faixa_baixa
    if largura <= 0:
        fracao = 0.5
    else:
        fracao = (float(total_cm) - faixa_baixa) / largura
        fracao = min(1.0, max(0.0, fracao))

    if fracao <= 0.15:
        chave = "ponta_inferior"
    elif fracao <= 0.40:
        chave = "abaixo_do_centro"
    elif fracao < 0.60:
        chave = "centro"
    elif fracao < 0.85:
        chave = "acima_do_centro"
    else:
        chave = "ponta_superior"

    return {
        "fracao": round(fracao, 4),
        "percentual": int(round(fracao * 100)),
        "chave": chave,
        "rotulo": POSICOES_NA_FAIXA[chave],
    }


class LinhaDoScp(TypedDict):
    """Uma linha publicada do Shared cM Project 4.0, na forma que o confronto le.

    Tipada porque o dicionario mistura `str` e `int`: sem anotacao, quem indexava
    `range_low` recebia `str | int` e precisava de `# type: ignore` para somar.
    """

    key: str
    name_en: str
    name_pt: str
    meioses: int
    average: float
    range_low: int
    range_high: int


class JanelaDeMeioses(TypedDict):
    """A envoltoria publicada para um numero de meioses, na forma que o confronto le.

    Tipada pelo mesmo motivo de `LinhaDoScp`: o dicionario mistura `int` e `list[str]`, e
    sem anotacao `janela["rows"]` chegava ao `str.join` de `evidence_comparison` como
    `int | list[str]`.
    """

    meioses: int
    range_low: int
    range_high: int
    average: int
    rows: list[str]


def row_for_key(key: str) -> LinhaDoScp | None:
    """Linha publicada do Shared cM 4.0 para a chave canonica, ou None."""
    for chave, nome_en, nome_pt, meioses, media, baixo, alto in SCP40_ROWS:
        if chave == key:
            return {"key": chave, "name_en": nome_en, "name_pt": nome_pt, "meioses": meioses,
                    "average": media, "range_low": baixo, "range_high": alto}
    return None


def rows_by_meioses(meioses: int) -> list:
    """Todas as linhas publicadas com o mesmo numero de meioses."""
    return [row_for_key(c[0]) for c in SCP40_ROWS if c[3] == meioses]


def meioses_maximo_publicado() -> int:
    """O maior numero de meioses que a versao 4.0 calibra.

    Existe para o confronto poder distinguir duas razoes diferentes de "nao ha janela":
    a relacao nao foi publicada mas o numero de meioses TEM linhas publicadas (ai a
    envoltoria resolve), e a relacao e mais PROFUNDA do que qualquer coisa que a fonte
    calibra. A segunda e uma constatacao sobre o alcance da fonte, e nao uma lacuna da
    tabela — e o operador precisa ouvir a diferenca. Ver `core.evidence_comparison`.
    """
    return max(linha[3] for linha in SCP40_ROWS)


def meioses_publicados() -> list:
    """Os numeros de meioses que a versao 4.0 calibra, em ordem.

    Existe pela mesma razao de `meioses_maximo_publicado`: ha duas razoes diferentes de
    "nao ha janela", e as duas precisam ser ditas com precisao. Quando a relacao cai num
    numero que a fonte simplesmente NAO publica (13 meioses, por exemplo, entre 12 e 14),
    dizer "a fonte nao calibra" seria falso — ela calibra 12 e 14. Ver
    `core.evidence_comparison`.
    """
    return sorted({linha[3] for linha in SCP40_ROWS})


def meioses_window(meioses: int) -> JanelaDeMeioses | None:
    """Janela de compatibilidade para uma contagem de meioses, tirada da fonte.

    Usada quando a relacao exata **nao** foi publicada na 4.0 (caso de 1C6R):
    em vez de inventar numero, reunimos as relacoes publicadas com o MESMO numero
    de meioses e usamos a envoltoria das faixas delas. Sem relacao publicada
    naquele numero de meioses, nao ha janela — e o confronto fica inconclusivo.
    """
    linhas = rows_by_meioses(meioses)
    if not linhas:
        return None
    return {
        "meioses": meioses,
        "range_low": min(l["range_low"] for l in linhas),
        "range_high": max(l["range_high"] for l in linhas),
        "average": round(sum(l["average"] for l in linhas) / len(linhas)),
        "rows": [l["name_en"] for l in linhas],
    }


def _confianca(qtd: int, cm) -> tuple:
    """Confianca da lista, pelo criterio explicito do projeto (nao da fonte).

    Quanto mais relacoes publicadas contem o valor, menos o valor discrimina.
    A fonte do Shared cM nao define grau de confianca algum; isto e heuristica
    declarada, e a tela deve apresenta-la como tal.
    """
    if cm is None or cm <= 0:
        return "indeterminada", "Não há valor de cM válido para avaliar."
    if qtd == 0:
        return "indeterminada", "Nenhuma relação publicada na versão 4.0 cobre exatamente este valor."
    if qtd == 1:
        return "baixa", ("Apenas uma relação publicada cobre este valor — e ainda assim a fonte alerta "
                         "que as distribuições se sobrepõem.")
    if qtd <= 3:
        return "baixa", f"{qtd} relações publicadas cobrem este valor; o cM não distingue qual delas é a verdadeira."
    if qtd <= 6:
        return "muito baixa", f"{qtd} relações publicadas cobrem este valor: a sobreposição é ampla."
    return "muito baixa", f"{qtd} relações publicadas cobrem este valor — nesta faixa o cM praticamente não discrimina."


def possible_relationships(total_cm) -> dict:
    """Estrutura do contrato: total_cm + possibilidades + confianca + leitura.

    Devolve SEMPRE lista em `possible_relationships`, inclusive vazia, e nunca um
    unico parentesco afirmado como conclusao.
    """
    if total_cm is None:
        return {
            "total_cm": None,
            "possible_relationships": [],
            "confidence": "indeterminada",
            "interpretation": "Sem valor de cM utilizável: não é possível listar possibilidades.",
            "reference": SCP40_META,
        }

    cm = float(total_cm)
    candidatas = []
    for chave, nome_en, nome_pt, meioses, media, baixo, alto in SCP40_ROWS:
        if baixo <= cm <= alto:
            candidatas.append({
                "key": chave, "name_en": nome_en, "name_pt": nome_pt, "meioses": meioses,
                "average": media, "range_low": baixo, "range_high": alto,
                # A distancia a media e' a grandeza que ORDENA a lista, e agora tambem a
                # que decide o destaque. Vai no payload para a tela poder dizer
                # "32,5 cM da media" em vez de pedir que o operador acredite na ordem.
                "distancia_da_media": round(abs(media - cm), 1),
                "destaque": False,
                # Duas colunas que nao vem do cM: onde procurar o antepassado comum
                # (definicao do parentesco) e onde o valor cai dentro da faixa
                # publicada (leitura da fonte). Ver `mrca_da_relacao` e
                # `posicao_na_faixa`.
                "mrca": mrca_da_relacao(chave),
                "posicao": posicao_na_faixa(cm, baixo, alto),
            })
    candidatas.sort(key=lambda c: (abs(c["average"] - cm), c["name_en"]))
    bloco_destaque = destaque_das_candidatas(candidatas, cm)

    confianca, explicacao = _confianca(len(candidatas), cm)
    if candidatas:
        leitura = (f"{len(candidatas)} relação(ões) publicada(s) na versão 4.0 do Shared cM Project "
                   f"admitem {cm:g} cM. Essas relações têm distribuições sobrepostas: o valor observado "
                   "não identifica qual delas é a verdadeira. Quanto mais distante a relação, maior a "
                   "cautela, porque a média das relações distantes só considera quem compartilha DNA "
                   "detectável.")
    else:
        leitura = (f"Nenhuma relação publicada na versão 4.0 cobre exatamente {cm:g} cM. Isso não "
                   "descarta parentesco: pode ser uma relação não analisada pela fonte ou um valor "
                   "afetado por agregação, endogamia ou limiar da empresa de teste.")

    return {
        "total_cm": cm,
        "possible_relationships": candidatas,
        # O destaque e' a UNICA leitura de "qual delas" que o bloco faz, e ele vem
        # com o criterio, com a contagem e com a negativa dentro de `ressalva`.
        "destaque": bloco_destaque,
        "confidence": confianca,
        "confidence_note": explicacao,
        "interpretation": leitura,
        "reference": SCP40_META,
    }


def hypotheses_for_evidence(evidence: dict) -> list:
    """Uma lista de hipoteses por KIT — nunca uma hipotese sobre a soma de kits.

    Sem evidencia, devolve lista vazia: sem DNA nao ha possibilidade de parentesco
    pelo DNA a listar (e o confronto dira que e inconclusivo, nao que e compativel).
    """
    if not evidence or not evidence.get("available"):
        return []
    blocos = []
    for kit in evidence.get("kits", []):
        bloco = possible_relationships(kit.get("total_cm"))
        bloco["kit"] = kit.get("kit")
        bloco["segment_count"] = kit.get("segment_count")
        bloco["largest_segment_cm"] = kit.get("largest_segment_cm")
        # A estimativa de geracoes ate o MRCA do proprio kit. Viaja junto porque e o unico
        # numero do arquivo de DNA que fala de PROFUNDIDADE, e o confronto precisa dele
        # para dizer o que a falta de faixa publicada deixa em aberto. Ver
        # `core.profundidade_do_caminho`.
        bloco["mrca_generations"] = kit.get("mrca_generations")
        blocos.append(bloco)
    return blocos


__all__ = [
    "SCP40_ROWS", "SCP40_META", "SCP40_NOT_PUBLISHED", "row_for_key", "rows_by_meioses",
    "meioses_window", "meioses_maximo_publicado", "meioses_publicados",
    "GRAUS_ATE_O_MRCA", "GRAUS_DAS_MEIAS_RELACOES", "POSICOES_NA_FAIXA",
    "BANDA_DE_DESTAQUE", "MAXIMO_DE_DESTAQUES", "ROTULOS_DE_DESTAQUE",
    "graus_ate_o_mrca", "mrca_da_relacao", "posicao_na_faixa", "destaque_das_candidatas",
    "possible_relationships", "hypotheses_for_evidence",
]

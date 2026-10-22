"""O nome do avo, do neto e do antepassado comum, por grau.

Responsabilidade unica: a serie portuguesa do parentesco em grau —
`avô → bisavô → trisavô → tetravô → pentavô → hexavô → heptavô → octavô → nonavô` —
nas tres formas de que o projeto precisa dela:

- o **ancestral**, no singular: `bisavô/avó` — usado no rotulo do parentesco;
- o **descendente**, no singular: `bisneto(a)` — usado no rotulo do parentesco;
- o conjunto de **antepassados comuns**, no plural: `bisavós` — usado na coluna
  "Antepassado comum mais recente" do bloco 3 da tela.

## Por que este modulo existe separado de `core.documentary_relationship`

A serie tem uma fonte so (a nomenclatura genealogica corrente) e tres consumidores.
Mas `core.documentary_relationship` importa `core.path_finding`, que importa
`networkx`; e `core.relationship_hypotheses` — a tabela do Shared cM Project, que
precisa do plural — e um modulo **sem import nenhum**, de proposito: ele traduz cM
em possibilidades e nao deve arrastar o grafo para dentro do caminho do CSV.
Manter a serie la obrigaria a escolher entre duplicar as palavras ou criar
`relationship_hypotheses -> path_finding`. Este modulo corta as duas saidas: nao
importa nada, e os dois lados o importam.

`core.documentary_relationship` **reexporta** `nome_do_grau`, entao o nome continua
valendo para quem ja o importava de la.

## O defeito que a serie corrige (2026-10-14)

O codigo montava a palavra repetindo `"bis" * (acima - 2)`, o que produzia
`bisbisavô`, `bisbisbisavô` e — no cartao da Margarida — a palavra de 64 caracteres
`Tio/Tia-bisbisbisbisbisbisbisbisavô/avó ↔ Sobrinho(a)-bisbisbisbisbisbisbisbisneto(a)`.
`bisbisavô` nao existe em portugues: o prefixo do terceiro grau e `tris-`, e nao
`bis-` repetido. O rotulo aparecia em 1 dos 62 cartoes da analise real; a varredura
de (0,0) a (12,12) mostrou que o defeito atingia todo grau a partir do quarto.

## As palavras vao INTEIRAS na tabela, e nao como prefixo + radical

A primeira versao daquela correcao concatenava prefixo e radical e produziu
`tetraavô` e `pentaavô`: os prefixos `tetra-` e `penta-` ja terminam em vogal, e o
radical comeca com outra. A forma correta contrai (`tetravô`, `pentavô`), e nao
alonga. Guardar a palavra pronta elimina a classe inteira desse erro — e ha teste
para cada grau, justamente porque concatenar aqui e tentador.

## O plural e tabela, e nao `+ "s"` (2026-10-22)

`avô` faz `avós`, e nao `avôs`: o acento muda junto com o numero, e a mesma regra
vale para `bisavós`, `trisavós`, `tetravós`. Derivar o plural com `+ "s"`
produziria `avôs` — que ninguem escreve. Por isso o plural tambem esta escrito na
terceira coluna da tabela.

`trisneto`, e nao `trineto`: mesma familia de `bisneto`, mesmo radical.
"""
from __future__ import annotations

#: Ordinal em algarismo para os graus acima da serie (11 em diante).
#: A contagem comeca no AVO, e nao no bisavo: 11 geracoes sao `9º avô`.
ROMANO = {1: "1º", 2: "2º", 3: "3º", 4: "4º", 5: "5º", 6: "6º", 7: "7º", 8: "8º", 9: "9º", 10: "10º"}

#: grau -> (ancestral no singular, descendente no singular, antepassados comuns no plural)
_PALAVRAS_DO_GRAU = {
    3: ("bisavô/avó", "bisneto(a)", "bisavós"),
    4: ("trisavô/avó", "trisneto(a)", "trisavós"),
    5: ("tetravô/avó", "tetraneto(a)", "tetravós"),
    6: ("pentavô/avó", "pentaneto(a)", "pentavós"),
    7: ("hexavô/avó", "hexaneto(a)", "hexavós"),
    8: ("heptavô/avó", "heptaneto(a)", "heptavós"),
    9: ("octavô/avó", "octaneto(a)", "octavós"),
    10: ("nonavô/avó", "nonaneto(a)", "nonavós"),
}

#: Os dois primeiros graus nao seguem a serie, porque nao tem prefixo: `pai/mae` e
#: `avô/avó`. Ficam aqui para que `nome_do_grau(1)` nao devolva `avô` — o grau 1 e o
#: genitor, e o codigo antigo so nao errava porque ninguem o chamava com 1.
_PRIMEIROS_GRAUS = {
    1: ("pai/mãe", "filho(a)", "pais"),
    2: ("avô/avó", "neto(a)", "avós"),
}


def nome_do_grau(graus: int, plural_neto: bool = False, plural_ancestral: bool = False) -> str:
    """`avô`/`avó` (ou `neto`/`neta`, ou `avós`) com o grau, em portugues correto.

    `graus=2` e o avo, `3` o bisavo, `4` o trisavo. Acima de `10` a serie continua
    com o ordinal em algarismo — `11º avô` — porque `undecavô` e forma que quase
    ninguem reconhece, e um rotulo que o operador nao entende e pior que um numerado.

    `plural_neto` devolve o descendente (`bisneto(a)`). `plural_ancestral` devolve o
    conjunto de antepassados comuns (`bisavós`), que e a forma que a coluna do
    antepassado comum mais recente usa: o ancestral de um primo de 2º grau sao os
    **bisavós**, e nao "o bisavô/avó". Os dois plurais nunca sao pedidos juntos.
    """
    if graus <= 1:
        if plural_ancestral:
            return "pais"
        return "filho(a)" if plural_neto else "pai/mãe"

    palavras = _PALAVRAS_DO_GRAU.get(graus) or _PRIMEIROS_GRAUS.get(graus)
    if palavras:
        if plural_ancestral:
            return palavras[2]
        return palavras[1] if plural_neto else palavras[0]

    ordinal = ROMANO.get(graus - 2, f"{graus - 2}º")
    if plural_ancestral:
        return f"{ordinal} avós"
    return f"{ordinal} {'neto(a)' if plural_neto else 'avô/avó'}"


__all__ = ["ROMANO", "nome_do_grau"]

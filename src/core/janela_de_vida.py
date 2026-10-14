"""Janela de vida: a pessoa que a arvore devolveu pode ter doado aquele DNA?

## Por que este modulo existe

O casamento entre o relatorio de DNA e a arvore e **por nome**, e o resultado e apresentado como
parentesco documental. Quando o nome do CSV casa com uma pessoa de outro seculo, o cartao
afirma um parentesco que a propria data do registro contradiz.

O caso medido, em 2026-10-14, sobre `Arvore_Unificada_Oficial_V1_2.ged` +
`Familias_Sergipanas.csv`: o kit `TG8027863` (25,4 cM) chama-se "Manoel Vieira da Silva" e o
GEDmatch informa, para esse kit, nascimento em **1936**; a arvore tem **quatro** registros com
esse nome, e o motor escolheu o de **1793** — 233 anos em 2026. O cartao exibia "Primos de 1o
grau com 7x remocao" com ancestral comum nascido em **ABT 1720**.

Medido nos 62 cartoes da analise real: **10** escolhas com janela de vida impossivel, das quais
**9 nao tem candidato melhor** — a arvore simplesmente nao contem a pessoa certa. Nenhuma regra
conserta isso. O que este modulo faz e **parar de afirmar**: o cartao passa a dizer que a
identidade nao fecha, em vez de apresentar o parentesco como bom.

## Este modulo NAO escolhe pessoa e NAO descarta match

Ele so **compara a data do registro com a janela em que um doador de DNA pode existir** e
devolve um estado. `core.matching` continua intacto, e a escolha continua a mesma. A diferenca e
que ela deixa de ser silenciosa. Descartar o cartao estava descartado por medicao: 1 dos 2
cartoes que a regra mudaria seria **perdido** junto com a evidencia genetica, e o operador nao
pode perder dado por causa de uma suspeita.

## O teste e ASSIMETRICO, e e isso que o torna seguro

A comparacao e `idade > LIMITE`. Ela acusa quando o registro da arvore e **jovem demais** para a
distancia — alguem nascido em 1673 apresentado como match de DNA. Ela **nunca** acusa um
ancestral legitimo, porque o teste e sobre o **match** (quem doou o DNA), e nao sobre os nos do
caminho. Trocar isso por uma faixa estreita ("a idade tem de ficar entre X e Y") comecaria a
descartar parentesco verdadeiro — e nao e o que esta aqui.

## Os dois limiares, e por que estes

`IDADE_IMPOSSIVEL = 122` e `IDADE_SUSPEITA = 105`.

- **122** e o recorde humano **verificado** (Jeanne Calment, 1875-1997). Acima disso nao existe
  pessoa documentada: e dado errado, e nao excecao. Por isso este e o limite duro.
- **105** e o limiar de **aviso**. Ninguem usa kit de DNA comercial habitualmente nessa idade, e
  o espaco entre 105 e 122 existe para nao tratar como absurdo o caso rarissimo do centenario
  que testou.

Nao sao numeros calibrados: sao heuristicos declarados, como o `0.33` do Jaccard e os limiares
de prenome de `identidade_do_match`. **E o numero nao e sensivel**: medido nos 62 cartoes, os
marcados tem de 116 a 666 anos, entao qualquer limiar entre 100 e 110 da o mesmo resultado. O
mais apertado (116 anos) esta 11 anos acima do aviso e 6 abaixo do teto.

## A ancora e o proprio dado, e nao o relogio

`ano_de_referencia` e `max(ano_atual, nascimento_da_raiz + IDADE_MINIMA_DE_GERACAO)`. Ancorar no
ano corrente sozinho faria a mesma analise mudar de resultado em 2035; ancorar no nascimento da
raiz sozinho quebraria quando a raiz e uma pessoa viva de agora. O `max` cobre os dois casos, e
e reproduzivel: mesma arvore, mesmo veredicto.
"""
from __future__ import annotations

from .documentary_relationship import parse_year

#: Acima disto e impossivel: recorde humano verificado. Ver o docstring do modulo.
IDADE_IMPOSSIVEL = 122

#: Acima disto, avisa. Heuristico declarado — ninguem testa DNA comercial aos 105.
IDADE_SUSPEITA = 105

#: Idade minima entre a raiz e o match mais jovem possivel, para a ancora da referencia.
#: Serve so para o piso do `max`; nao e limiar de aceitacao de nada.
IDADE_MINIMA_DE_GERACAO = 16

#: Qualificadores de data do GEDCOM que indicam estimativa, e nao data exata.
_QUALIFICADORES = ("ABT", "EST", "CAL", "BEF", "AFT", "CIRCA", "APPROX")

POSSIVEL = "possivel"
SUSPEITA = "suspeita"
IMPOSSIVEL = "impossivel"
SEM_DATA = "sem_data"
DATA_IMPRECISA = "data_imprecisa"


def ano_de_referencia(ano_atual: int, ano_de_nascimento_da_raiz: int | str | None) -> int:
    """Ano contra o qual a idade e medida. Ver o docstring do modulo."""
    ano_raiz = parse_year(ano_de_nascimento_da_raiz)
    if ano_raiz is None:
        return ano_atual
    return max(ano_atual, ano_raiz + IDADE_MINIMA_DE_GERACAO)


def _e_imprecisa(data_gedcom: str) -> bool:
    """`ABT 1852`, `BEF 1878`, `CAL 1900` — data estimada, e nao exata."""
    texto = (data_gedcom or "").upper()
    return any(qualificador in texto for qualificador in _QUALIFICADORES)


def conferir_janela_de_vida(data_de_nascimento: str | None, ano_referencia: int) -> tuple[str, int | None, bool]:
    """Estado da janela de vida.

    Devolve `(estado, idade_no_ano_de_referencia, data_imprecisa)`.

    - `sem_data` — o registro nao traz nascimento. NAO e suspeita: nao saber nao e o mesmo que
      ser impossivel, e marcar aqui encheria a tela de aviso sem informacao nenhuma;
    - `data_imprecisa` — traz ano, mas estimado (`ABT 1852`). O ano e usado, e o cartao diz que
      a data e estimada;
    - `impossivel` — acima de `IDADE_IMPOSSIVEL`;
    - `suspeita` — acima de `IDADE_SUSPEITA`, dentro do possivel;
    - `possivel` — o resto.
    """
    ano = parse_year(data_de_nascimento)
    if ano is None:
        return (SEM_DATA, None, False)

    idade = ano_referencia - ano
    imprecisa = _e_imprecisa(data_de_nascimento or "")

    if idade > IDADE_IMPOSSIVEL:
        return (IMPOSSIVEL, idade, imprecisa)
    if idade > IDADE_SUSPEITA:
        return (SUSPEITA, idade, imprecisa)
    if imprecisa:
        return (DATA_IMPRECISA, idade, True)
    return (POSSIVEL, idade, False)


def aviso_da_janela(estado: str, idade: int | None, nome_no_csv: str, nome_na_arvore: str,
                    data_na_arvore: str | None, ano_referencia: int) -> str:
    """A divergencia escrita para o operador. String vazia quando nao ha o que dizer."""
    if estado in (POSSIVEL, SEM_DATA):
        return ""

    if estado == IMPOSSIVEL:
        return (f"O relatório de DNA traz “{nome_no_csv}” e a pessoa escolhida no GEDCOM é "
                f"“{nome_na_arvore}”, com nascimento em {data_na_arvore} — "
                f"{idade} anos em {ano_referencia}. Nenhuma pessoa com essa idade pode ter "
                "doado DNA: ou o registro é de outra pessoa com o mesmo nome, ou falta o "
                "vínculo que liga o doador a esta árvore. O parentesco abaixo é o do registro "
                "escolhido, e não pode ser lido como o do doador.")

    if estado == SUSPEITA:
        return (f"O relatório de DNA traz “{nome_no_csv}” e a pessoa escolhida no GEDCOM é "
                f"“{nome_na_arvore}”, com nascimento em {data_na_arvore} — "
                f"{idade} anos em {ano_referencia}. A idade está acima do plausível para quem "
                "usa um kit de DNA; confirme se é a mesma pessoa antes de usar as conclusões.")

    if estado == DATA_IMPRECISA:
        return (f"A data de nascimento de “{nome_na_arvore}” é estimada ({data_na_arvore}): "
                f"pela estimativa seriam {idade} anos em {ano_referencia}. Anos estimados não "
                "confirmam nem descartam a identidade — confira a fonte do dado.")

    return ""


__all__ = [
    "IDADE_IMPOSSIVEL",
    "IDADE_SUSPEITA",
    "IDADE_MINIMA_DE_GERACAO",
    "POSSIVEL",
    "SUSPEITA",
    "IMPOSSIVEL",
    "SEM_DATA",
    "DATA_IMPRECISA",
    "ano_de_referencia",
    "conferir_janela_de_vida",
    "aviso_da_janela",
]

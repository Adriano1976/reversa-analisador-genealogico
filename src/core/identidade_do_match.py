"""Identidade do match: o nome do CSV e a pessoa escolhida no GEDCOM sao a mesma?

## Por que este modulo existe

O casamento entre o relatorio de DNA e a arvore e **por nome**, e o nome do CSV nao e
unico nem canonico: o GEDmatch/MyHeritage exporta o que o dono do kit digitou. Quando o
nome do CSV nao encontra correspondencia exata, `core.matching` decide por similaridade —
e essa decisao pode **escolher outra pessoa** da familia, tipicamente alguem que
compartilha os sobrenomes e tem um prenome parecido.

O caso medido, em 2026-10-13, sobre `Arvore_Unificada_Oficial_V1_2.ged` +
`Familias_Sergipanas.csv`: o CSV traz `Therezinha Carvalho do Nascimento Souza` e o
GEDCOM tem `Therezinha Carvalho do /Nascimento/` **sem** o `Souza`; o desempate de
`matching.py` prefere `Soraia Carvalho do Nascimento Souza`, que tem os **tres**
sobrenomes do CSV contra dois da Therezinha. O cartao saiu com o cM da Therezinha sob o
nome da Soraia, e nenhum aviso dizia que a identificacao tinha sido duvidosa.

## Este modulo NAO escolhe pessoa

Ele so **compara o que foi escolhido com o que o CSV pediu** e devolve um estado. Nao
mexe em limiar, peso, ramo de aceitacao ou desempate: `matching.py` continua intacto, e
o resultado da analise nao muda por causa deste modulo. A escolha e apenas **rotulada**.

## Os tres estados

- `CONFIRMADA` — o nome normalizado do CSV e igual ao nome normalizado da pessoa da
  arvore. E o portao de entrada do matching (`ged_index`), entao estado exato.
- `GRAFIA` — o prenome e o mesmo, e o que difere e acento, ordem, abreviacao ou um
  sobrenome a mais ou a menos (`Camila` x `Camilla`, `Manoel Vieira da Silva` x
  `Manoel da Silva Vieira`, `Maria Ivanda ... SantAnna` x `Sant'Anna`). E a variacao que
  o sistema existe para absorver: **nao alarmar** e o comportamento correto.
- `A_CONFIRMAR` — o **prenome e outro** e a semelhanca do nome inteiro passou do limiar
  que a propria aceitacao exigia. Isso e a assinatura do falso positivo: o nome parecido
  veio do sobrenome, nao da pessoa. E o estado que a tela precisa mostrar.

## Os dois limiares, e por que estes

`LIMITE_PREMONE = 12` e `MIN_SEMELHANCA_PREMONE = 85`.

Nao sao numeros calibrados: sao o corte que separou o sinal do ruido nos dados reais, e
estao declarados como heuristicos ajustaveis, como o `0.33` do Jaccard. O que os
justifica:

- o corte do prenome e do **pre nome**: a comparacao usa so os 12 primeiros caracteres,
  porque em portugues o primeiro nome nao passa disso — sem o corte, um `Therezinha` x
  `Therezinha` com sobrenomes longos diferentes seria dado como semelhante pelo nome
  inteiro;
- `85` e o piso que a propria aceitacao ja usava para prenome nos ramos principais
  (`best_g >= 85` em `matching.py`), entao o limiar nao introduz um numero novo;
- um prenome **abreviado** (`Luiz Claúdio` x `Claudio`) passa pelo prefixo de 3 letras:
  e a mesma pessoa com um nome a mais, nao outra pessoa.

Medido nos dois arquivos reais: 36 cartoes `CONFIRMADA`, 16 `GRAFIA` e 10 `A_CONFIRMAR`
— e os 10 incluem os cinco falsos positivos evidentes (`Soraia` no lugar de
`Therezinha`, `Bernardina` no lugar de `Benigna`, `José Ariocy` no lugar de `Darcy`,
`Dionel` no lugar de `Silva Dantas`, `Raul` no lugar de `Maria Resende`).
"""
from __future__ import annotations

from thefuzz import fuzz

from .name_normalization import norm_name

#: Estados possiveis da identificacao. Sao os valores que a tela le.
CONFIRMADA = "confirmada"
GRAFIA = "grafia"
A_CONFIRMAR = "a_confirmar"

#: Ver o docstring do modulo: heuristico declarado, e nao numero calibrado.
LIMITE_PREMONE = 12
MIN_SEMELHANCA_PREMONE = 85
PREFIXO_MINIMO = 3


def _prenome(nome: str) -> str:
    """O primeiro token do nome normalizado; string vazia quando nao ha nome."""
    partes = norm_name(nome or "").split()
    return partes[0] if partes else ""


def conferir(nome_no_csv: str, nome_na_arvore: str) -> str:
    """Estado da identificacao entre o nome pedido pelo CSV e a pessoa escolhida.

    Funcao pura: mesmo par de nomes, mesmo estado, sempre. `nome_na_arvore` vazio
    (payload antigo, sem pessoa resolvida) devolve `A_CONFIRMAR`, porque sem pessoa
    nao ha o que confirmar — e calar seria afirmar o que nao se sabe.
    """
    if not (nome_na_arvore or "").strip():
        return A_CONFIRMAR

    normalizado_csv = norm_name(nome_no_csv or "")
    normalizado_arvore = norm_name(nome_na_arvore)
    if normalizado_csv == normalizado_arvore:
        return CONFIRMADA

    prenome_csv = _prenome(nome_no_csv)
    prenome_arvore = _prenome(nome_na_arvore)
    if prenome_csv == prenome_arvore:
        return GRAFIA

    corte_csv = prenome_csv[:LIMITE_PREMONE]
    corte_arvore = prenome_arvore[:LIMITE_PREMONE]
    if (fuzz.ratio(corte_csv, corte_arvore) >= MIN_SEMELHANCA_PREMONE
            or corte_csv[:PREFIXO_MINIMO] == corte_arvore[:PREFIXO_MINIMO]):
        # Mesmo prenome com um pedaco a mais (`luiz claudio` x `claudio`,
        # `vicente giuliano` x `giuliano`): a pessoa e a mesma, o nome e que veio maior.
        return GRAFIA
    return A_CONFIRMAR


def nomes_divergentes(nome_no_csv: str, nome_na_arvore: str) -> str:
    """A divergencia escrita para o operador, sem veredito e sem culpar o arquivo.

    Devolve string vazia quando nao ha o que dizer (`CONFIRMADA`): a tela nao deve
    renderizar aviso nenhum nesse caso, e uma frase vazia e mais dificil de usar por
    engano do que um `None` tratado a parte.
    """
    estado = conferir(nome_no_csv, nome_na_arvore)
    if estado == CONFIRMADA:
        return ""
    if estado == GRAFIA:
        return ""
    return (f"O relatório de DNA traz “{nome_no_csv}” e a pessoa escolhida no GEDCOM é "
            f"“{nome_na_arvore}”. Os sobrenomes coincidem, mas o prenome não: a conexão "
            "pode pertencer a outra pessoa da mesma família.")


__all__ = [
    "CONFIRMADA",
    "GRAFIA",
    "A_CONFIRMAR",
    "LIMITE_PREMONE",
    "MIN_SEMELHANCA_PREMONE",
    "PREFIXO_MINIMO",
    "conferir",
    "nomes_divergentes",
]

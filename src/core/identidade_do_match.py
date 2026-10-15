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
  arvore, **e o nome tem mais de uma palavra**. E o portao de entrada do matching
  (`ged_index`), entao estado exato. Nome de uma palavra so (`Margarida`) NAO confirma:
  ver abaixo.
- `GRAFIA` — o prenome e o mesmo, e o que difere e acento, ordem, abreviacao ou um
  sobrenome a mais ou a menos (`Camila` x `Camilla`, `Manoel Vieira da Silva` x
  `Manoel da Silva Vieira`, `Maria Ivanda ... SantAnna` x `Sant'Anna`). E a variacao que
  o sistema existe para absorver: **nao alarmar** e o comportamento correto.
- `A_CONFIRMAR` — o **prenome e outro** e a semelhanca do nome inteiro passou do limiar
  que a propria aceitacao exigia. Isso e a assinatura do falso positivo: o nome parecido
  veio do sobrenome, nao da pessoa. E o estado que a tela precisa mostrar.
  **Tambem e o estado de um nome de uma palavra so**, pelo motivo da secao seguinte.

## Nome de uma palavra so nao identifica ninguem

Medido em 2026-10-14 sobre os dois arquivos reais: tres cartoes trazem no relatorio um nome
sem segunda parte que discrimine. O caso que importa e o kit `ZC1171551`, cujo nome e
`"Margarida"` — **uma palavra** —, e a arvore tem **oito** registros com esse nome exato.

Com uma palavra so, todo termo de semelhanca da nota do matching fica **igual** entre os
oito candidatos; a ordem entre eles e do desempate congelado, nao de evidencia. Dois deles
tem caminho ate a raiz — um nascido em 1673 e um sem data —, e a escolha entre os dois foi
essa ordenacao. O cartao saiu com o de 1673, 353 anos, e o eixo da identidade dizia
`CONFIRMADA`.

Um casamento exato de `"Margarida"` com `"Margarida"` confirma que a **palavra** e a mesma.
Nao confirma que a pessoa e. Sem segunda palavra nao ha o que comparar.

O corte e por **numero de palavras**, e nao por "nao tem sobrenome", porque `split_name_pt`
chama `natividade` de prenome quando o nome comeca por um prenome generico
(`Maria Natividade`, `Jose Francisco Alves`) — e esses nomes **tem** parte que discrimina.
Marca-los seria transformar o aviso em ruido.

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

Medido em **2026-10-14**, sobre os 62 cartoes da analise atual: 36 `CONFIRMADA`,
16 `GRAFIA` e 10 `A_CONFIRMAR` — e os 10 incluem os cinco falsos positivos evidentes
(`Soraia` no lugar de `Therezinha`, `Bernardina` no lugar de `Benigna`, `José Ariocy` no lugar
de `Darcy`, `Dionel` no lugar de `Silva Dantas`, `Raul` no lugar de `Maria Resende`).

Sob a regra anterior a esta data a distribuicao seria **37 / 16 / 9**: o unico cartao que a
regra move e o `Margarida`, que era `CONFIRMADA` por igualdade exata. Os numeros que este
docstring trazia antes (36 / 16 / 10, de 2026-10-13) **coincidem por acaso** com os de hoje e
mediam outra analise: foram colhidos antes de a busca de ancestral comum ser corrigida, que
mudou quais cartoes tem caminho e, com isso, quem e a pessoa escolhida em alguns deles.
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


def _e_um_prenome_so(nome: str) -> bool:
    """O nome do relatorio e uma palavra so, sem segunda parte para comparar?

    Ver `conferir` para o caso medido. Um nome de duas ou mais palavras tem, no minimo, duas
    partes que a busca por nome confronta — e a partir dai quem julga e `core.matching`.
    """
    return len(norm_name(nome or "").split()) == 1


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

    # UM PRENOME SO NAO IDENTIFICA NINGUEM.
    #
    # Medido em 2026-10-14: o kit `ZC1171551` traz `"Margarida"` — uma palavra —, e a arvore
    # tem OITO registros com esse nome exato. Com uma palavra so nao ha segunda parte para
    # comparar: TODO termo de semelhanca da nota fica igual entre os oito candidatos, e quem
    # decide e o desempate congelado, nao a evidencia. Dos oito, dois tem caminho ate a raiz,
    # e a escolha entre eles foi essa ordenacao — nao um dado.
    #
    # O corte e por NUMERO DE PALAVRAS, e nao por "nao tem sobrenome": `split_name_pt` chama
    # `natividade` de prenome quando o nome comeca por um prenome generico (`Maria Natividade`,
    # `Jose Francisco Alves`), e esses nomes TEM parte que discrimina. Marca-los seria
    # transformar o aviso em ruido — e ruido nao avisa.
    if _e_um_prenome_so(nome_no_csv):
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
    if _e_um_prenome_so(nome_no_csv):
        # A frase generica abaixo fala de sobrenomes, e aqui o relatorio nao trouxe nenhum:
        # repeti-la seria dizer uma coisa que nao aconteceu.
        return (f"O relatório de DNA traz “{nome_no_csv}” e a pessoa escolhida no GEDCOM é "
                f"“{nome_na_arvore}”. O relatório traz um prenome só, sem sobrenome, e "
                "prenome se repete: o nome sozinho não diz de quem é a conexão. Confira a pessoa "
                "pelos pais, pelo cônjuge ou pelas datas antes de usar as conclusões.")
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

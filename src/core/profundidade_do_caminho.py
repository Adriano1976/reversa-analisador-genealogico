"""Profundidade do caminho documental contra a estimativa do PROPRIO kit.

## O que este modulo acrescenta ao que ja existia

Duas verificacoes ja existiam, e elas nao cobrem este caso:

- a **janela de vida** (`core.janela_de_vida`) pergunta se a pessoa escolhida no GEDCOM
  pode ter doado aquele DNA. Ela pega o registro de 1793 apresentado como match;
- o **confronto** (`core.evidence_comparison`) pergunta se o cM cabe na faixa publicada
  para o parentesco documental.

Falta a pergunta que nao depende de ninguem estar vivo: **a arvore afirma a mesma
profundidade que o kit informa?** Medido em 2026-10-14 nos 62 cartoes reais, existe um
cartao em que as duas primeiras verificacoes ficam caladas e esta acusa: kit `XS4787142`,
19,2 cM, "Primos de 8º grau com 2× remoção", doadora nascida em **1976** — idade
perfeitamente plausivel, entao a janela de vida nao tem o que dizer. A arvore afirma
**10,0** geracoes medias ate o ancestral comum; o proprio relatorio de DNA, na coluna
`MRCA` que o app lia e descartava, estima **4,77** para esse kit. A arvore afirma mais que
o dobro.

## De onde vem o numero do DNA, e por que nao foi inventado aqui

Nao ha tabela nova neste modulo. `MRCA` e uma coluna do proprio CSV de matches (270 de 270
kits do arquivo real a trazem), preenchida pela estimativa do GEDmatch para aquele kit, e
que `parsers/csv_ingest` recebia e jogava fora: `aggregate_matches` preservava apenas
`Name` e `cM`. Quem a traz de volta e a evidencia genetica (`core.genetic_evidence`), que e
o modulo dono do que o arquivo de DNA afirma.

## As duas grandezas comparadas

`geracoes_documentais = meioses / 2`. A divisao nao e arbitraria: `MRCA` e um numero so
para o PAR, enquanto `meioses` conta os saltos pai-filho dos DOIS lados. O GEDmatch informa
geracoes de um lado ate o ancestral comum, entao o comparavel e a media dos dois lados.
Calibragem medida em dois cartoes independentes, sem nenhum ajuste: `1C7R` (11 meioses,
media 5,5) contra `MRCA` 4,57; `1C6R` (8 meioses, media 4,0) contra `MRCA` 5,19. Os dois
pares batem, e e isso que autoriza dividir por dois.

## Os limiares, e por que estes

`LIMIAR_DE_DIVERGENCIA = 2.0` e `LIMIAR_DE_ATENCAO = 1.5`.

A estimativa `MRCA` e **derivada do cM** e tem incerteza propria: uma razao de 1,3 entre a
arvore e o kit esta dentro do ruido de quem estima geracoes a partir de um valor de
segmento. **Dobro** nao esta: e a afirmacao de que o caminho documental tem duas vezes
mais geracoes do que o cM sustenta, o que costuma ser elo ausente entre a geracao
documentada e o doador, e nao parentesco mais remoto. Medido nos 62 cartoes: em 1,3 a regra
marcaria 6 cartoes (cinco deles sao o MESMO ancestral contado cinco vezes, com razoes entre
1,45 e 2,10), e em 2,0 marca 1. O 1,5 existe para o operador poder ver o numero antes do
limiar duro — e nao para decidir por ele.

## Este modulo NAO escolhe pessoa, NAO descarta match e NAO muda veredito

Ele devolve um estado, um numero e um texto. `core.matching` e
`core.evidence_comparison` ficam intactos, e os quatro estados do confronto continuam
quatro — a fronteira esta declarada em `RF-19`, `BR-D-27` e no ADR-15, que decidiu que
ausencia de faixa publicada nao vira veredito. Aqui tambem nao vira: a divergencia de
profundidade **avisa**.
"""
from __future__ import annotations

#: A partir daqui a arvore afirma o dobro de geracoes que o kit informa. Ver o docstring.
LIMIAR_DE_DIVERGENCIA = 2.0

#: A partir daqui o numero e mostrado como atencao, sem afirmar divergencia.
LIMIAR_DE_ATENCAO = 1.5

SEM_DADO = "sem_dado"
CONCORDA = "concorda"
ATENCAO = "atencao"
DIVERGENCIA = "divergencia"


def conferir_profundidade(meioses, geracoes_do_kit):
    """Estado da profundidade. Devolve `(estado, razao, geracoes_documentais)`.

    - `sem_dado` — falta o caminho documental, as meioses ou a estimativa do kit. NAO e
      suspeita: nao saber nao e o mesmo que divergir, e marcar aqui encheria a tela sem
      informacao nenhuma;
    - `concorda` — a arvore e o kit afirmam profundidades compativeis;
    - `atencao` — a arvore afirma entre `LIMIAR_DE_ATENCAO` e `LIMIAR_DE_DIVERGENCIA`
      vezes a profundidade do kit;
    - `divergencia` — afirmam `LIMIAR_DE_DIVERGENCIA` vezes ou mais.
    """
    if not meioses or geracoes_do_kit is None or geracoes_do_kit <= 0:
        return (SEM_DADO, None, None)

    documentais = meioses / 2
    razao = documentais / geracoes_do_kit
    if razao >= LIMIAR_DE_DIVERGENCIA:
        return (DIVERGENCIA, razao, documentais)
    if razao >= LIMIAR_DE_ATENCAO:
        return (ATENCAO, razao, documentais)
    return (CONCORDA, razao, documentais)


def no_na_profundidade_sugerida(caminho, indice_ancestral, geracoes_do_kit):
    """Id do no do PROPRIO caminho que esta na profundidade que o kit sugere.

    O caminho vai da raiz ate o match (`caminho[0]` a raiz, `caminho[-1]` o match), com o
    ancestral comum em `indice_ancestral`. Subindo `k` geracoes a partir do match chega-se
    a `caminho[len-1-k]`. Devolve `None` quando esse ponto cai no proprio ancestral comum
    (ai nao ha o que marcar alem dele) ou acima dele — caso em que o GEDCOM nao alcanca a
    profundidade sugerida pelo DNA. **Nenhum no e criado aqui**: o que este modulo aponta e
    sempre uma pessoa que ja esta no caminho documental.
    """
    if not caminho or geracoes_do_kit is None:
        return None
    alvo = int(round(geracoes_do_kit))
    if alvo <= 0:
        return None
    indice = len(caminho) - 1 - alvo
    if indice <= indice_ancestral or indice >= len(caminho) - 1:
        return None
    return caminho[indice]


def _numero(valor, casas: int = 1) -> str:
    """Decimal com virgula, como o resto da tela (`cm_br`)."""
    return f"{valor:.{casas}f}".replace(".", ",")


def aviso_da_profundidade(estado, nome_no_csv, nome_na_arvore, geracoes_documentais,
                          geracoes_do_kit, razao):
    """A divergencia escrita para o operador. String vazia quando nao ha o que dizer."""
    if estado in (SEM_DADO, CONCORDA):
        return ""

    if geracoes_documentais is None or geracoes_do_kit is None or razao is None:
        return ""

    comum = (f"A árvore liga “{nome_no_csv}” a “{nome_na_arvore}” por "
             f"{_numero(geracoes_documentais)} gerações até o ancestral comum. O próprio relatório "
             f"de DNA estima {_numero(geracoes_do_kit, 2)} gerações até o MRCA deste kit — "
             f"{_numero(razao)}× menos.")

    if estado == DIVERGENCIA:
        return (comum + " Um caminho documental com o dobro da profundidade que o cM sustenta "
                "costuma indicar elo ausente entre a geração documentada e o doador, e não "
                "parentesco mais distante. O parentesco abaixo é o do registro escolhido, e o "
                "vínculo real pode ser mais próximo do que ele afirma.")

    return (comum + " A diferença ainda cabe na incerteza de uma estimativa feita a partir do "
            "cM, mas é o número a conferir antes de usar as conclusões.")


def resumo_da_profundidade(estado, geracoes_documentais, geracoes_do_kit) -> str:
    """A leitura CURTA do diagrama, em uma frase. String vazia quando nao ha o que dizer.

    Nasceu dentro de `reporting.mermaid_render`, como um no solto ao lado do desenho. Ele
    saiu de la por dois motivos: um texto de dominio nao pertence ao renderizador, e um no
    solto num `flowchart` fica parecendo um parente — o operador ve uma caixa no grafo e
    espera que ela seja uma pessoa ou um vinculo. Agora a frase e um bloco de texto na
    legenda, separada do desenho, que foi onde ela sempre deveria ter estado.

    O texto e o MESMO que o no mostrava, palavra por palavra: mudou de lugar, nao de
    conteudo. Ver `aviso_da_profundidade` para a versao longa, que e o alerta do cartao.
    """
    if estado not in (ATENCAO, DIVERGENCIA):
        return ""
    if geracoes_documentais is None or geracoes_do_kit is None:
        return ""

    if estado == DIVERGENCIA:
        return (f"Elo documental não confirmado pelo DNA: a árvore afirma "
                f"{_numero(geracoes_documentais)} gerações até o ancestral comum, e este kit "
                f"estima {_numero(geracoes_do_kit)}.")
    return (f"Confira a profundidade: a árvore afirma {_numero(geracoes_documentais)} gerações "
            f"até o ancestral comum; este kit estima {_numero(geracoes_do_kit)}.")


__all__ = [
    "LIMIAR_DE_DIVERGENCIA",
    "LIMIAR_DE_ATENCAO",
    "SEM_DADO",
    "CONCORDA",
    "ATENCAO",
    "DIVERGENCIA",
    "conferir_profundidade",
    "no_na_profundidade_sugerida",
    "aviso_da_profundidade",
    "resumo_da_profundidade",
]

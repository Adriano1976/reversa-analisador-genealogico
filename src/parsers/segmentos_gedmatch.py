"""Adapter de entrada do CSV de segmentos do GEDmatch.

Responsabilidade unica: transformar o arquivo de matches em segmentos tipados e
**limpos**, sem decidir regra de negocio. A leitura em si (encoding, separador,
preambulo e linha torta) continua em `parsers.csv_ingest`; aqui ficam a
normalizacao numerica da coluna de cM e a conversao para `SegmentoDeGedmatch`.

## Por que `pd.to_numeric(errors="coerce")`

O CSV do GEDmatch mistura tipos na coluna de centimorgans: valor numerico, texto
(`"n/d"`, `"N/A"`), celula vazia e, em export com configuracao regional, virgula
decimal. `float(valor)` levanta nesses casos, e um `except` por linha espalharia
try/except pelo fluxo. O `to_numeric(errors="coerce")` resolve de uma vez: o que
nao e numero vira `NaN`, que e contabilizado e descartado — e nao vira zero, que
inventaria um segmento.

## O que este modulo NAO faz

- **Nao aplica o filtro de 10 cM.** O limiar e regra de dominio
  (`core.endogamia.DNAAnalyzer`); o adapter so entrega o dado limpo. Se
  filtrasse aqui, a regra ficaria em dois lugares e a tela nao conseguiria
  distinguir "o arquivo nao tinha segmento" de "o filtro descartou tudo".
- Nao agrupa por kit nem soma cM: isso e `core.genetic_evidence`.
- Nao formata texto de tela.
"""
from __future__ import annotations

import math
from dataclasses import dataclass

import pandas as pd

from core.erros import DnaCsvSemColunas
from core.genetic_evidence import detect_segment_columns
from utils.text_cleaning import demojibake

from .csv_ingest import read_csv_with_fallback


@dataclass(frozen=True, slots=True)
class SegmentoDeGedmatch:
    """Uma linha de segmento, ja com cM numerico.

    `linha` e a posicao 1-based entre as linhas de DADOS do DataFrame (nao a
    linha fisica do arquivo, que pode ter preambulo): serve para o operador
    localizar a origem sem prometer uma numeracao que o `skiprows` desloca.
    """

    pessoa: str
    centimorgans: float
    kit: str | None = None
    cromossomo: str | None = None
    inicio: int | None = None
    fim: int | None = None
    snps: int | None = None
    linha: int = 0


@dataclass(frozen=True, slots=True)
class LeituraDeSegmentos:
    """Resultado da leitura: segmentos utilizaveis e o que foi descartado."""

    segmentos: tuple[SegmentoDeGedmatch, ...]
    linhas: int
    linhas_sem_cm: tuple[int, ...]
    linhas_sem_nome: int
    avisos: tuple[str, ...]


def _texto(valor: object) -> str:
    """String limpa de celula; `NaN`/`None` viram string vazia."""
    if valor is None:
        return ""
    texto = str(valor).strip()
    return "" if texto.lower() in ("nan", "none", "<na>") else texto


def _inteiro(valor: object) -> int | None:
    """Inteiro tolerante; texto invalido vira `None`."""
    if valor is None:
        return None
    try:
        numero = float(valor)  # type: ignore[arg-type]
    except (TypeError, ValueError):
        return None
    return int(numero) if math.isfinite(numero) else None


def _cm_numerico(serie: pd.Series) -> pd.Series:
    """Coluna de cM como float, com `NaN` onde nao ha numero.

    A primeira tentativa e o `to_numeric` direto. O fallback de virgula decimal
    so roda nas celulas que falharam — e apenas nelas —, porque trocar toda
    virgula por ponto antes poderia transformar um separador de milhar em
    decimal. Export do GEDmatch usa ponto; a virgula aparece em planilha salva
    em configuracao brasileira, e recusar esse arquivo seria recusar o do
    operador.
    """
    numero = pd.to_numeric(serie, errors="coerce")
    if numero.isna().any():
        alternativa = pd.to_numeric(
            serie.astype("string").str.strip().str.replace(",", ".", regex=False),
            errors="coerce",
        )
        numero = numero.fillna(alternativa)
    return numero.astype("float64")


def segmentos_do_dataframe(df: pd.DataFrame) -> LeituraDeSegmentos:
    """Converte o DataFrame ja lido em segmentos limpos.

    Separado de `ler_segmentos_gedmatch` para quem ja tem o DataFrame — o fluxo
    de DNA le o arquivo uma vez, e reabrir o CSV para contar segmentos seria
    I/O duplicado.
    """
    colunas = detect_segment_columns(df)
    if not colunas["name"] or not colunas["cm"]:
        raise DnaCsvSemColunas("Colunas de Nome e cM não encontradas no CSV.")

    cm = _cm_numerico(df[colunas["cm"]])
    segmentos: list[SegmentoDeGedmatch] = []
    linhas_sem_cm: list[int] = []
    linhas_sem_nome = 0

    for posicao, (_, linha) in enumerate(df.iterrows(), start=1):
        # `iloc` pela POSICAO, e nao `.loc` pelo rotulo: o adapter nao pode
        # depender de o DataFrame recebido ter indice unico.
        valor_cm = cm.iloc[posicao - 1]
        # `NaN` e o sentinela do `to_numeric`; `math.isfinite` o recusa sem
        # importar numpy para o adapter.
        if not math.isfinite(float(valor_cm)):
            linhas_sem_cm.append(posicao)
            continue
        nome = _texto(linha[colunas["name"]])
        if not nome:
            linhas_sem_nome += 1
            continue
        segmentos.append(
            SegmentoDeGedmatch(
                pessoa=demojibake(nome),
                centimorgans=float(valor_cm),
                kit=(_texto(linha[colunas["kit"]]).upper() or None) if colunas["kit"] else None,
                cromossomo=_texto(linha[colunas["chromosome"]]) if colunas["chromosome"] else None,
                inicio=_inteiro(linha[colunas["start"]]) if colunas["start"] else None,
                fim=_inteiro(linha[colunas["end"]]) if colunas["end"] else None,
                snps=_inteiro(linha[colunas["snps"]]) if colunas["snps"] else None,
                linha=posicao,
            )
        )

    avisos: list[str] = []
    if linhas_sem_cm:
        amostra = ", ".join(str(numero) for numero in linhas_sem_cm[:10])
        if len(linhas_sem_cm) > 10:
            amostra += "…"
        avisos.append(
            f"{len(linhas_sem_cm)} linha(s) sem cM numérico foram descartadas "
            f"(linha(s) de dados {amostra}). O valor não foi tratado como zero."
        )
    if linhas_sem_nome:
        avisos.append(
            f"{linhas_sem_nome} linha(s) com cM válido não tinham nome e foram descartadas."
        )
    if not segmentos:
        avisos.append(
            "Nenhum segmento com cM numérico e nome foi encontrado no CSV; "
            "não há evidência genética utilizável."
        )

    return LeituraDeSegmentos(
        segmentos=tuple(segmentos),
        linhas=len(df),
        linhas_sem_cm=tuple(linhas_sem_cm),
        linhas_sem_nome=linhas_sem_nome,
        avisos=tuple(avisos),
    )


def ler_segmentos_gedmatch(caminho: str) -> LeituraDeSegmentos:
    """Le o CSV do GEDmatch e devolve os segmentos limpos.

    Usa `read_csv_with_fallback` para herdar todo o tratamento ja existente de
    encoding, separador, preambulo e linha torta — o adapter nao reimplementa
    leitura de CSV.
    """
    return segmentos_do_dataframe(read_csv_with_fallback(caminho))


__all__ = [
    "SegmentoDeGedmatch",
    "LeituraDeSegmentos",
    "ler_segmentos_gedmatch",
    "segmentos_do_dataframe",
]

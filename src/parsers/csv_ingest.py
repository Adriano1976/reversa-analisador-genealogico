"""Leitura do CSV de matches: encoding, separador e agregacao por match.

Extraido de `dna_analysis.py` pela OPP-20260929-ZV52 e ampliado na correcao do
erro de carregamento relatado em 2026-10. Responsabilidade unica: ler o arquivo
tolerando encoding E separador, achar o cabecalho e reduzir varias linhas do
mesmo match a uma, somando os cM dos segmentos.

## O que a leitura tolera, e o que ela reporta

- **encoding**: utf-8 e, se falhar, latin-1 (comportamento original, preservado).
- **separador**: `,`, `;`, TAB e `|`, decidido pelo cabecalho. Antes so a virgula
  era aceita, e um export com ponto e virgula virava UMA coluna — a analise
  morria depois, com "Colunas de Nome e cM nao encontradas", sem dizer por que.
- **preambulo antes do cabecalho**: muitos exports trazem linhas de titulo antes
  da linha de colunas. O cabecalho passa a ser localizado (ver
  `localizar_cabecalho`) e as linhas anteriores sao reportadas.
- **linha com numero de campos diferente do cabecalho**: o pandas abortava a
  leitura inteira com `Error tokenizing data. C error: Expected 1 fields in line
  4, saw 2`, que chegava crua (e em ingles) na tela do operador. Agora o arquivo
  e relido descartando essas linhas, e o que foi descartado sai em
  `df.attrs["linhas_ignoradas"]` para a tela publicar o aviso. Nada e escondido:
  o consumidor le esses attrs e mostra a contagem e os numeros de linha.
- **arquivo que nao e lista de matches** (ex.: o GEDCOM enviado por engano): a
  leitura devolve o que der, `detect_columns` nao acha Nome/cM, e `dna_analysis`
  levanta um erro que diz o separador usado, as colunas encontradas, as linhas
  divergentes e a causa provavel — em portugues, sem vazar o texto do erro do
  pandas.

Os `attrs` do DataFrame sao o canal escolhido porque a assinatura de
`read_csv_with_fallback` e contrato: `dna_analysis` e `__all__` a reexportam, e
trocar o retorno por tupla quebraria esses consumidores.
"""
from __future__ import annotations

import csv
import io
from collections import Counter

import pandas as pd

from utils.name_keys import norm_name
from utils.text_cleaning import demojibake

# Ordem importa no empate: a virgula e o formato padrao do GEDmatch e o que o
# fluxo sempre aceitou.
SEPARADORES = (",", ";", "\t", "|")

# Teto de linhas examinadas antes do cabecalho. Preambulo de export e curto; um
# arquivo com dezenas de linhas "diferentes" no inicio nao e preambulo, e sim
# arquivo que nao e tabela.
LIMITE_DE_PREAMBULO = 10


def _texto(path, encoding, limite=None):
    with open(path, "r", encoding=encoding, errors="replace", newline="") as fh:
        return fh.read() if limite is None else fh.read(limite)


def _linhas_csv(path, sep, encoding):
    texto = _texto(path, encoding)
    if not texto:
        return []
    try:
        return list(csv.reader(io.StringIO(texto), delimiter=sep))
    except csv.Error:
        return []


def _primeira_linha_util(texto):
    for linha in texto.splitlines():
        if linha.strip():
            return linha
    return ""


def detectar_separador(path, encoding="utf-8") -> str:
    """Separador mais provavel do arquivo, decidido pelo cabecalho.

    Conta ocorrencias de cada candidato na primeira linha nao vazia e escolhe a
    de maior contagem. Escolha explicita em vez de `csv.Sniffer`: o sniffer erra
    em arquivo de uma coluna so, e um TAB ou ponto e virgula dentro de um nome
    seria pior do que simplesmente nao detectar (nesse caso fica a virgula, e o
    erro de colunas ausentes explica o que foi lido).
    """
    cabecalho = _primeira_linha_util(_texto(path, encoding, limite=8192))
    if not cabecalho:
        return ","
    contagens = {sep: cabecalho.count(sep) for sep in SEPARADORES}
    melhor = max(SEPARADORES, key=lambda sep: contagens[sep])
    return melhor if contagens[melhor] else ","


def localizar_cabecalho(path, sep, encoding="utf-8") -> int:
    """Indice (0-based) da linha do cabecalho; 0 quando ja e a primeira.

    O cabecalho e a primeira linha cujo numero de campos e o **modal entre as
    linhas com 2 ou mais campos**, e a decisao exige: (a) que esse modal apareca
    pelo menos DUAS vezes — um cabecalho precisa de ao menos uma linha de dados
    para ser um cabecalho; (b) que a primeira linha nao tenha esse numero de
    campos; (c) que a linha esteja entre as primeiras `LIMITE_DE_PREAMBULO`.

    As guardas existem contra dois falsos positivos medidos: um arquivo SEM
    cabecalho (cuja primeira linha de dados ja tem o numero de campos dos dados)
    nao pode perder a primeira linha; e um arquivo que nao e tabela (ex.: um
    GEDCOM com UMA linha contendo virgula) nao pode eleger essa linha como
    cabecalho e esconder o problema real.

    A contagem usa `csv.reader`, que respeita aspas, inclusive com quebra de
    linha dentro do campo.
    """
    linhas = _linhas_csv(path, sep, encoding)
    if not linhas:
        return 0
    contagens = Counter(len(linha) for linha in linhas if len(linha) >= 2)
    if not contagens:
        return 0
    modal, frequencia = contagens.most_common(1)[0]
    if frequencia < 2 or len(linhas[0]) == modal:
        return 0
    for indice, linha in enumerate(linhas[:LIMITE_DE_PREAMBULO]):
        if len(linha) == modal:
            return indice
    return 0


def linhas_irregulares(path, sep, encoding="utf-8", cabecalho=None) -> list:
    """Numeros (1-based) das linhas cujo numero de campos difere do cabecalho."""
    linhas = _linhas_csv(path, sep, encoding)
    if not linhas:
        return []
    if cabecalho is None:
        cabecalho = localizar_cabecalho(path, sep, encoding)
    esperado = len(linhas[cabecalho])
    # As linhas ANTES do cabecalho sao preambulo, nao linha torta: quem as
    # reporta e `linhas_antes_do_cabecalho`.
    return [indice + 1 for indice, linha in enumerate(linhas)
            if indice > cabecalho and len(linha) != esperado]


def read_csv_with_fallback(path):
    """Le o CSV devolvendo DataFrame; tolera encoding, separador, preambulo e linha torta.

    Levanta `ValueError` com causa em portugues apenas quando nenhuma tentativa
    produz tabela utilizavel.
    """
    problemas = []
    for encoding in ("utf-8", "latin-1"):
        sep = detectar_separador(path, encoding)
        cabecalho = localizar_cabecalho(path, sep, encoding)
        ignoradas, erro_de_leitura = [], None
        extra = {"skiprows": cabecalho} if cabecalho else {}
        try:
            df = pd.read_csv(path, sep=sep, encoding=encoding, skipinitialspace=True, **extra)
        except UnicodeDecodeError as erro:
            problemas.append(f"encoding {encoding} recusado ({erro.reason})")
            continue
        except pd.errors.ParserError as erro:
            # Linha torta nao derruba a analise inteira. O que for descartado
            # nesta releitura e reportado em `df.attrs`, e nao em silencio.
            ignoradas = linhas_irregulares(path, sep, encoding, cabecalho)
            erro_de_leitura = str(erro)
            try:
                df = pd.read_csv(path, sep=sep, encoding=encoding, skipinitialspace=True,
                                 on_bad_lines="skip", **extra)
            except Exception as erro_de_novo:  # pragma: no cover - erro do proprio pandas
                problemas.append(f"leitura com separador {sep!r} ({erro_de_novo})")
                continue

        df.columns = [str(col).strip() for col in df.columns]
        df.attrs["separador"] = sep
        df.attrs["encoding"] = encoding
        df.attrs["linhas_antes_do_cabecalho"] = cabecalho
        df.attrs["linhas_ignoradas"] = ignoradas
        df.attrs["erro_de_leitura"] = erro_de_leitura
        return df

    raise ValueError(
        "Não foi possível ler o arquivo CSV. Tentativas feitas: "
        + ("; ".join(problemas) or "nenhuma produziu tabela utilizável")
        + ". Confira se o arquivo enviado é a lista de matches de DNA "
          "(CSV com colunas de nome e de cM) e não o GEDCOM ou outro arquivo."
    )


def detect_columns(df):
    name_col = next((col for col in ["Name", "MatchedName", "Nome"] if col in df.columns), None)
    cm_col = next((col for col in ["cM", "TotalCM", "Total cM"] if col in df.columns), None)
    # Para na primeira coluna que casa: a lista completa era montada para depois pegar
    # o primeiro elemento, e a semantica sempre foi "a primeira que casa".
    match_id_col = next(
        (c for c in df.columns
         if df[c].astype(str).str.fullmatch(r"[A-Z]{2}\d{7}").mean() > 0.3), None)
    email_cols = [c for c in df.columns if "mail" in c.lower()]
    match_email_col = email_cols[-1] if email_cols else None
    return name_col, cm_col, match_id_col, match_email_col


def aggregate_matches(df, name_col, cm_col, match_id_col, match_email_col):
    # Chave montada por operacao de coluna. `apply(axis=1)` montava uma Series por
    # linha; aqui o nome e normalizado uma vez por nome DISTINTO, nao por linha.
    #
    # `map(str)` e obrigatorio no lugar de `astype(str)`: em coluna de objeto o
    # `astype(str)` do pandas preserva o NaN como float, e `demojibake` estoura.
    nomes = df[name_col].map(str)
    mapa = {v: norm_name(demojibake(v)) for v in nomes.drop_duplicates()}
    name_key = nomes.map(mapa)
    if match_id_col:
        cauda = df[match_id_col].map(str).str.strip().str.upper()
    elif match_email_col:
        emails = df[match_email_col].map(str)
        cauda = emails.map({v: norm_name(v) for v in emails.drop_duplicates()})
    else:
        cauda = None
    df["_group_key"] = name_key if cauda is None else name_key + " | " + cauda
    aggregated = (
        df.groupby("_group_key", as_index=False)
        .agg({cm_col: "sum"})
        .merge(
            df[["_group_key", name_col]].drop_duplicates("_group_key"),
            on="_group_key", how="left",
        )
    )
    return aggregated


__all__ = ["read_csv_with_fallback", "detect_columns", "aggregate_matches",
           "detectar_separador", "localizar_cabecalho", "linhas_irregulares", "SEPARADORES"]

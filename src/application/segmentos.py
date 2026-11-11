"""Projecao da tabela de segmentos para a tela (feature 058).

Pura: nao reordena (a ordem vem do nucleo), nao formata numero e nao calcula geometria.
Mesma regra de `application.regioes`: o template nao importa `core/` (`ADR-34`).

Deriva duas coisas que so' fazem sentido na apresentacao:

- `extensao_mb`, de `fim - inicio`, para a regiao nao ter duas fontes do mesmo numero;
- `chave_de_busca`, o texto da linha sem acento e em minusculas, que o script da tela
  compara com o que o operador digita.
"""
from __future__ import annotations

import unicodedata


def _sem_acento(texto: str) -> str:
    """Minusculas e sem acento, para a busca nao depender de como o nome foi digitado."""
    # pyrefly: ignore[unnecessary-type-conversion]
    decomposto = unicodedata.normalize("NFKD", str(texto).lower())
    return "".join(letra for letra in decomposto if not unicodedata.combining(letra))


def projetar_segmentos(segmentos) -> list[dict]:
    """Converte os segmentos do nucleo em dicionarios de apresentacao."""
    linhas = []
    for segmento in segmentos or ():
        linha = {
            "regiao": segmento.regiao_indice,
            "cromossomo": segmento.cromossomo,
            "inicio": segmento.inicio,
            "fim": segmento.fim,
            "extensao_mb": round((segmento.fim - segmento.inicio) / 1_000_000, 2),
            "cm": segmento.cm,
            "kit": segmento.kit,
            "nome": segmento.nome,
            "desfecho": segmento.desfecho,
            "desfecho_chave": segmento.desfecho_chave,
        }
        linha["chave_de_busca"] = _sem_acento(
            f"{segmento.cromossomo} {segmento.kit} {segmento.nome}"
        )
        linhas.append(linha)
    return linhas


def cromossomos_das_linhas(linhas) -> list[str]:
    """Cromossomos na ordem em que aparecem, que ja' e' a ordem natural da tabela."""
    vistos: list[str] = []
    for linha in linhas or ():
        cromossomo = linha.get("cromossomo")
        if cromossomo and cromossomo not in vistos:
            vistos.append(cromossomo)
    return vistos


__all__ = ["cromossomos_das_linhas", "projetar_segmentos"]

"""CSV das regiões compartilhadas (feature 056, `RF-08`).

Mesmo dialeto de `csv_de_descartes`: ponto e vírgula (o Excel em português trata
`,` como decimal), BOM no começo, decimal com vírgula e desarme de fórmula.

Função pura: recebe as regiões já projetadas em dicionários pela camada de
aplicação e devolve texto. Não lê arquivo, não fala com a rede e **não importa
`core/`** (`ADR-34`).
"""
from __future__ import annotations

import csv
import io

CABECALHO = (
    "Cromossomo",
    "Início (pb)",
    "Fim (pb)",
    "Extensão (Mb)",
    "Kits",
    "cM mínimo",
    "cM máximo",
    "Desfecho",
    "Alerta",
    "Membros",
    "Ancestral comum",
    "Motivo",
)

_PERIGOSOS = ("=", "+", "-", "@")


def _texto(valor) -> str:
    if valor is None:
        return ""
    texto = str(valor)
    if texto.startswith(_PERIGOSOS):
        return "'" + texto
    return texto


def _numero(valor) -> str:
    if valor is None or valor == "":
        return ""
    try:
        texto = f"{float(valor):.2f}".rstrip("0").rstrip(".")
        return texto.replace(".", ",")
    except (TypeError, ValueError):
        return _texto(valor)


def csv_das_regioes(itens) -> str:
    """Uma linha por região, no formato que o operador abre na planilha."""
    saida = io.StringIO()
    escritor = csv.writer(saida, delimiter=";", lineterminator="\r\n")
    escritor.writerow(CABECALHO)
    for item in itens or ():
        escritor.writerow([
            _texto(item.get("cromossomo")),
            _texto(item.get("inicio")),
            _texto(item.get("fim")),
            _numero(item.get("extensao_mb")),
            _texto(item.get("kits")),
            _numero(item.get("cm_minimo")),
            _numero(item.get("cm_maximo")),
            _texto(item.get("desfecho")),
            _texto(item.get("alerta") or ""),
            _texto(item.get("membros")),
            _texto(item.get("ancestrais")),
            _texto(item.get("motivo")),
        ])
    return "\ufeff" + saida.getvalue()


__all__ = ["CABECALHO", "csv_das_regioes"]

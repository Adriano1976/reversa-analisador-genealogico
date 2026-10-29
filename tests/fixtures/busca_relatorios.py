"""Relatorios sinteticos de matches para os testes da busca (feature 052).

O CSV e minimo de proposito: `Name` e `Total cM` sao as duas colunas que a leitura
tolera obrigar, e o `Kit` entra porque o card do relatorio mostra kit e cM
(`RF-06`). Dois nomes, para que o teste possa provar que um acerta e o outro nao.

`CSV_DE_MATCHES` tem um nome que TAMBEM existe na arvore de referencia
(`Maria /dos Santos/` nao: `Maria Silva` sim) — e o par que exercita a referencia
cruzada do `RF-07`.
"""
from __future__ import annotations

#: Relatorio valido: um nome que existe na arvore de referencia e outro que nao.
CSV_DE_MATCHES = (
    "Name,Total cM,Kit\n"
    "Maria Silva,120.0,AB123\n"
    "Roberto Nogueira,45.5,CD456\n"
)

#: Relatorio com uma linha de preambulo antes do cabecalho, que a leitura ja tolera.
CSV_COM_PREAMBULO = (
    "Relatorio exportado pelo Ancestor Projects\n"
    "Name,Total cM,Kit\n"
    "Maria Silva,120.0,AB123\n"
)

#: Conteudo que NAO e tabela de matches. Existe para o teste do aviso de relatorio
#: ilegivel (`RF-13`) no adaptador, quando a leitura devolve vazio em vez de levantar.
CSV_SEM_COLUNAS = "isto nao e um relatorio de matches\nnem uma tabela\n"


__all__ = ["CSV_COM_PREAMBULO", "CSV_DE_MATCHES", "CSV_SEM_COLUNAS"]

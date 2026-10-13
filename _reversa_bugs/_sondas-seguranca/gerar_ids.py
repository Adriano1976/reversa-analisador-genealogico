"""Gera os IDs canonicos dos bugs desta sessao (BUG-<data>-<4 chars base32>).

Regra do `/reversa-debugger` (Etapa 2.2): o sufixo sao 4 caracteres base32 derivados de
hash curto de titulo + data + hora. Este script e o registro de como os IDs foram
derivados, para que qualquer pessoa possa reconferir.

Uso: python gerar_ids.py
"""
import base64
import hashlib
import json

DATA = "20261013"
HORA = "1305"

TITULOS = [
    ("nome-com-dois-pontos-fluxo-ntfs",
     "Nome de arquivo com dois pontos grava a arvore num fluxo alternativo NTFS e a torna inalcancavel"),
    ("texto-de-excecao-cru-com-caminho-do-servidor",
     "Resposta de erro devolve o texto cru da excecao, com o caminho absoluto do servidor"),
    ("texto-do-driver-do-banco-na-pagina",
     "Falha de persistencia devolve o texto do driver do banco na pagina"),
    ("post-sem-verificacao-de-origem",
     "POST que muda estado sem verificacao de origem nem token"),
    ("scripts-de-cdn-sem-sri-e-sem-csp",
     "Scripts de CDN sem integridade e ausencia de Content-Security-Policy"),
    ("sem-protecao-de-enquadramento",
     "Resposta sem protecao de enquadramento na pagina com acao destrutiva"),
]


def sufixo(titulo):
    semente = f"{titulo}|{DATA}|{HORA}".encode("utf-8")
    resumo = hashlib.sha256(semente).digest()[:5]
    return base64.b32encode(resumo).decode("ascii")[:4]


def main():
    linhas = []
    for indice, (slug, titulo) in enumerate(TITULOS, start=7):
        linhas.append({
            "display_number": indice,
            "id": f"BUG-{DATA}-{sufixo(titulo)}",
            "slug": slug,
            "title": titulo,
        })
    print(json.dumps(linhas, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()

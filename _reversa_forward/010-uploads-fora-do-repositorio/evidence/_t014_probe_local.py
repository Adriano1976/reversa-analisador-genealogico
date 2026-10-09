"""Sonda de T014: prova a continuidade entre requisicoes com a pasta fora do repositorio.

Roda contra a aplicacao **de verdade**, subida com `ANALISADOR_UPLOAD_FOLDER` apontando
para o destino canonico (`D:\\dados-genealogicos\\uploads`). Envia a fixture **sintetica**
`basic.ged` e a fixture de DNA `cm_boundaries.csv` — nunca dado real do operador
(Principio I de `.reversa/principles.md`).

O que ela mede:

1. o `POST action=upload_gedcom` conclui e devolve o nome armazenado (a continuidade
   depende desse valor voltar no campo oculto `gedcom_filename`);
2. o `POST action=path_search` com duas pessoas da arvore conclui;
3. o `POST action=dna_analysis` com o CSV conclui;
4. **nenhuma** resposta diz "nao existe mais" — que e o sintoma exato de a referencia
   apontar para a outra raiz.

Uso:  .venv\\Scripts\\python.exe _reversa_forward\\010-...\\evidence\\_t014_probe_local.py
"""
from __future__ import annotations

import os
import re
import sys
import urllib.request
from datetime import datetime, timezone

BASE = sys.argv[1] if len(sys.argv) > 1 else "http://127.0.0.1:5000/"
RAIZ = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
GEDCOM = os.path.join(RAIZ, "_reversa_sdd", "parity", "fixtures", "gedcom", "basic.ged")
CSV = os.path.join(RAIZ, "_reversa_sdd", "parity", "fixtures", "dna", "cm_boundaries.csv")
# Nomes SEM acento de proposito: o parser le GEDCOM em latin-1 (o harness faz o mesmo,
# `harness.py:200`) e o formulario chega em UTF-8 — procurar "Joao" acentuado nao
# encontra nada, e a sonda mediria o proprio erro de codificacao em vez da pasta.
PESSOA_1 = "Carlos Silva"
PESSOA_2 = "Diego Silva"


def conteudo_unico_do_gedcom() -> bytes:
    """A fixture com um marcador unico no cabecalho.

    Sem conteudo unico o upload nao cria arquivo novo (a chave vem do conteudo e o
    arquivo ja existe nos dois lados), e a contagem das pastas nao prova **onde** a
    escrita caiu — que e exatamente o que esta sonda existe para provar.
    """
    with open(GEDCOM, "rb") as fh:
        original = fh.read()
    momento = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ").encode()
    return original.replace(b"1 SOUR PARITY", b"1 SOUR SONDA-T014-" + momento, 1)



def post_multipart(campos: dict, arquivos: dict) -> tuple:
    fronteira = "----sonda010"
    partes = []
    for nome, valor in campos.items():
        partes.append(("--" + fronteira + "\r\n").encode())
        partes.append(('Content-Disposition: form-data; name="%s"\r\n\r\n' % nome).encode())
        partes.append(str(valor).encode("utf-8") + b"\r\n")
    for nome, (nome_arquivo, conteudo) in arquivos.items():
        partes.append(("--" + fronteira + "\r\n").encode())
        partes.append(('Content-Disposition: form-data; name="%s"; filename="%s"\r\n'
                       % (nome, nome_arquivo)).encode())
        partes.append(b"Content-Type: application/octet-stream\r\n\r\n")
        partes.append(conteudo + b"\r\n")
    partes.append(("--" + fronteira + "--\r\n").encode())
    pedido = urllib.request.Request(
        BASE, data=b"".join(partes),
        headers={"Content-Type": "multipart/form-data; boundary=" + fronteira},
    )
    with urllib.request.urlopen(pedido, timeout=120) as resposta:
        return resposta.status, resposta.read().decode("utf-8", "replace")


def alerta(pagina: str) -> str:
    achados = re.findall(r'<div class="alert[^"]*"[^>]*>\s*([^<]+)', pagina)
    return " | ".join(a.strip() for a in achados) or "(sem alerta)"


def referencia(pagina: str) -> str | None:
    achado = re.search(r'name="gedcom_filename" value="([^"]+)"', pagina)
    return achado.group(1) if achado else None


def main() -> int:
    gedcom = conteudo_unico_do_gedcom()
    with open(CSV, "rb") as fh:
        csv = fh.read()

    print("1) upload da arvore sintetica (conteudo unico, nome visivel proprio)")
    status, pagina = post_multipart(
        {"action": "upload_gedcom"}, {"gedcom": ("sonda_t014.ged", gedcom)})
    referencia_arvore = referencia(pagina)
    print("   HTTP %s | alerta: %s" % (status, alerta(pagina)))
    print("   referencia devolvida: %s" % referencia_arvore)
    if not referencia_arvore:
        print("   REPROVADO: o upload nao devolveu a referencia")
        return 1

    print("2) busca de caminho entre %s e %s" % (PESSOA_1, PESSOA_2))
    status, pagina = post_multipart(
        {"action": "path_search", "gedcom_filename": referencia_arvore,
         "person1_name": PESSOA_1, "person2_name": PESSOA_2}, {})
    print("   HTTP %s | alerta: %s" % (status, alerta(pagina)))
    print("   mermaid presente: %s" % ("mermaid" in pagina.lower()))
    if "não encontrada" in pagina or "nao encontrada" in pagina:
        print("   REPROVADO: a busca nao encontrou a pessoa (nome ou codificacao)")
        return 1

    print("3) analise de DNA com a fixture de CSV, em nome visivel proprio")
    status, pagina = post_multipart(
        {"action": "dna_analysis", "gedcom_filename": referencia_arvore,
         "root_name": PESSOA_1}, {"matches_csv": ("sonda_t014.csv", csv)})
    print("   HTTP %s | alerta: %s" % (status, alerta(pagina)))
    if "não foi encontrado no GEDCOM" in pagina:
        print("   REPROVADO: a raiz da analise nao foi encontrada")
        return 1

    print("4) varredura do sintoma de referencia quebrada")
    if "não existe mais" in pagina:
        print("   REPROVADO: a resposta diz que o arquivo nao existe mais")
        return 1
    print("   OK: nenhuma resposta diz 'nao existe mais'")
    return 0


if __name__ == "__main__":
    sys.exit(main())

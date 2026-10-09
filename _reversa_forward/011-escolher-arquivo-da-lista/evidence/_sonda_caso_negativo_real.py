"""Sonda 2: o caso negativo com o arquivo REAL da pasta canonica, em modo somente leitura.

A sonda 1 usou um CSV sintetico de duas linhas e deu `OSError` -> HTTP 500. O desfecho pode
depender do tamanho/forma do arquivo (o `ged4py` pode falhar no cabecalho OU parsear sem
registros). Entao o caso que importa e o arquivo que existe de verdade na pasta.

Esta sonda NAO COPIA nada para dentro do repositorio: ela aponta a aplicacao para a pasta real
e apenas LE. O inventario por sha256 antes e depois prova que nada foi escrito.
"""
from __future__ import annotations

import hashlib
import importlib.util
import logging
import os
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[3]
PASTA_APP = RAIZ / "src"
UPLOADS = PASTA_APP / "uploads"

ALVO_CSV_COM_GED = "94e2402671702cac__Famílias_Sergipanas.csv.ged"
ALVO_CSV_PURO = "94e2402671702cac__Famílias_Sergipanas.csv"
ALVO_GED_VALIDO = "4ee53cbc4914fadd__Backup-Arvore-Sandro-12-11-2024.ged"


def inventario() -> dict[str, str]:
    return {
        p.name: hashlib.sha256(p.read_bytes()).hexdigest()
        for p in sorted(UPLOADS.iterdir()) if p.is_file()
    }


def carregar_app():
    os.environ["ANALISADOR_UPLOAD_FOLDER"] = str(UPLOADS)
    for caminho in (str(RAIZ), str(PASTA_APP)):
        if caminho not in sys.path:
            sys.path.insert(0, caminho)
    spec = importlib.util.spec_from_file_location("_app_sonda_011b", str(PASTA_APP / "app.py"))
    modulo = importlib.util.module_from_spec(spec)
    modulo.__file__ = str(PASTA_APP / "app.py")
    spec.loader.exec_module(modulo)
    modulo.app.root_path = str(PASTA_APP)
    return modulo.app


def resumir(resposta) -> str:
    corpo = resposta.get_data(as_text=True)
    for alvo in ("não reconhecido como GEDCOM", "Ocorreu um erro", "Erro ao processar GEDCOM",
                 "não existe mais", "não encontrada"):
        if alvo in corpo:
            return f'mensagem contem: "{alvo}"'
    return "(nenhuma mensagem de contrato conhecida no corpo)"


def main() -> None:
    logging.disable(logging.CRITICAL)
    antes = inventario()
    print(f"inventario ANTES: {len(antes)} arquivos")
    print()

    app = carregar_app()
    cliente = app.test_client()

    r = cliente.get("/")
    print(f"GET  /                                        -> {r.status_code}")

    casos = [
        ("CSV real com nome .ged (aba de arvore)", ALVO_CSV_COM_GED),
        ("CSV real no nome puro (aba de DNA)", ALVO_CSV_PURO),
        ("GEDCOM valido real", ALVO_GED_VALIDO),
    ]
    for rotulo, nome in casos:
        if not (UPLOADS / nome).exists():
            print(f"POST path_search  {rotulo:<40} -> ARQUIVO AUSENTE")
            continue
        r = cliente.post("/", data={
            "action": "path_search",
            "gedcom_filename": nome,
            "person1_name": "Maria",
            "person2_name": "Joao",
        })
        print(f"POST path_search  {rotulo:<40} -> {r.status_code}  {resumir(r)}")

    r = cliente.post("/", data={
        "action": "dna_analysis",
        "gedcom_filename": ALVO_CSV_COM_GED,
        "root_name": "Maria",
    })
    print(f"POST dna_analysis (CSV com nome .ged)          -> {r.status_code}  {resumir(r)}")

    print()
    depois = inventario()
    print(f"inventario DEPOIS: {len(depois)} arquivos")
    if antes == depois:
        print("VEREDITO: pasta IDENTICA -- nada foi escrito, nada foi lido como conteudo novo")
    else:
        print("VEREDITO: A PASTA MUDOU -- investigar")
        for nome in sorted(set(antes) | set(depois)):
            if antes.get(nome) != depois.get(nome):
                print("  diferente:", nome)


if __name__ == "__main__":
    main()

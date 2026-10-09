"""Sonda: qual mensagem o operador recebe ao ESCOLHER um arquivo cujo conteudo nao serve.

Motivo: a `§7` do `requirements.md` e o `§5` do `interfaces/formulario-http.md` afirmam que a
resposta e `Arquivo nao reconhecido como GEDCOM: {motivo}.`. A leitura do codigo sugere outra
coisa: essa mensagem nasce em `application/traducao.py:86` a partir de um `ErroDeDominio`, e o
`ErroDeDominio` nasce da VALIDACAO DE CONTEUDO, que so roda no caminho de ENVIO
(`ArmazenamentoEmDisco.guardar` -> `validar_conteudo_gedcom`). Arquivo escolhido por referencia
nao passa por `guardar`: ele vai direto ao parser (`carregar_arvore`), e o ramo da rota cai no
`except Exception` generico.

Esta sonda mede o desfecho real, em vez de supor.
"""
from __future__ import annotations

import importlib.util
import os
import shutil
import sys
from pathlib import Path

def _raiz_do_repositorio(inicio):
    """Sobe ate a raiz que tenha `src/utils/validate.py` (contar `parents[N]` quebra ao mover o arquivo)."""
    import pathlib
    for candidato in [inicio, *inicio.parents]:
        if (candidato / "src" / "utils" / "validate.py").is_file():
            return candidato
    raise SystemExit("raiz do repositorio nao encontrada a partir de " + str(inicio))


RAIZ = _raiz_do_repositorio(Path(__file__).resolve().parent)
PASTA_APP = RAIZ / "src"
TEMP = RAIZ / "tests" / ".tmp" / "sonda-011"

CHAVE_CSV = "94e2402671702cac"
NOME_CSV_COM_GED = f"{CHAVE_CSV}__Familias_Sergipanas.csv.ged"

CONTEUDO_CSV = (
    "Match Name,Chromosome,Start Location,End Location,Centimorgans (cM),SNPs\n"
    "Maria Souza,1,1000,5000,120.5,3000\n"
).encode("utf-8")

CONTEUDO_TEXTO = b"isto nao e um GEDCOM nem um CSV de matches\n"


def montar_pasta() -> str:
    if TEMP.exists():
        shutil.rmtree(TEMP, ignore_errors=True)
    TEMP.mkdir(parents=True)
    (TEMP / NOME_CSV_COM_GED).write_bytes(CONTEUDO_CSV)
    (TEMP / "0000000000000001__texto_qualquer.ged").write_bytes(CONTEUDO_TEXTO)
    (TEMP / "0000000000000002__vazio.ged").write_bytes(b"")
    return str(TEMP)


def carregar_app():
    os.environ["ANALISADOR_UPLOAD_FOLDER"] = montar_pasta()
    for caminho in (str(RAIZ), str(PASTA_APP)):
        if caminho not in sys.path:
            sys.path.insert(0, caminho)
    spec = importlib.util.spec_from_file_location("_app_sonda_011", str(PASTA_APP / "app.py"))
    modulo = importlib.util.module_from_spec(spec)
    modulo.__file__ = str(PASTA_APP / "app.py")
    spec.loader.exec_module(modulo)
    modulo.app.root_path = str(PASTA_APP)
    return modulo.app


def resumir(resposta) -> str:
    corpo = resposta.get_data(as_text=True)
    marcas = []
    for alvo in ("não reconhecido como GEDCOM", "Ocorreu um erro", "Erro ao processar GEDCOM",
                 "não existe mais"):
        if alvo in corpo:
            marcas.append(alvo)
    return " | ".join(marcas) if marcas else "(nenhuma mensagem conhecida encontrada)"


def main() -> None:
    app = carregar_app()
    cliente = app.test_client()

    print("pasta da sonda:", TEMP)
    print("arquivos:", sorted(p.name for p in TEMP.iterdir()))
    print()

    # --- 1. GET / (nao deve falhar) ---
    r = cliente.get("/")
    print(f"GET  /                              -> {r.status_code}")

    # --- 2. escolher o CSV-com-nome-de-GEDCOM na busca de caminho ---
    for nome in (NOME_CSV_COM_GED, "0000000000000001__texto_qualquer.ged",
                 "0000000000000002__vazio.ged"):
        r = cliente.post("/", data={
            "action": "path_search",
            "gedcom_filename": nome,
            "person1_name": "Maria",
            "person2_name": "Joao",
        })
        print(f"POST path_search  {nome[:34]:<34} -> {r.status_code}  {resumir(r)}")

    # --- 3. escolher o CSV-com-nome-de-GEDCOM na analise de DNA (sem arquivo) ---
    r = cliente.post("/", data={
        "action": "dna_analysis",
        "gedcom_filename": NOME_CSV_COM_GED,
        "root_name": "Maria",
    })
    print(f"POST dna_analysis {NOME_CSV_COM_GED[:34]:<34} -> {r.status_code}  {resumir(r)}")

    # --- 4. controle: enviar o MESMO conteudo pela tela de envio ---
    import io
    r = cliente.post("/", data={
        "action": "upload_gedcom",
        "gedcom": (io.BytesIO(CONTEUDO_CSV), "Familias_Sergipanas.csv.ged"),
    }, content_type="multipart/form-data")
    print(f"POST upload_gedcom (mesmo conteudo)      -> {r.status_code}  {resumir(r)}")

    shutil.rmtree(TEMP, ignore_errors=True)


if __name__ == "__main__":
    main()

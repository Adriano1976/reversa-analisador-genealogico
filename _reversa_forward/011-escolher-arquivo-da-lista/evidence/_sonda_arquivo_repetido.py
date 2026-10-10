"""Sonda: o que acontece quando o operador carrega um arquivo REPETIDO.

Feature `011-escolher-arquivo-da-lista`. Leitura, medicao e nada mais: roda contra uma pasta
temporaria e nao toca em `src/uploads`.

## Os tres casos, e por que cada um e diferente

1. **Mesmo conteudo, mesmo nome.** A chave vem do conteudo (`RF-09`), entao o caminho e o
   mesmo e a gravacao nao acontece de novo.
2. **Mesmo conteudo, nome DIFERENTE.** A chave e igual, mas o nome visivel faz parte do nome
   armazenado — entao nasce um SEGUNDO arquivo com o mesmo conteudo. E o caso que a pasta real
   mostra em `94e2402671702cac__Familias_Sergipanas.csv` e `....csv.ged`.
3. **Arquivo que foi APOSENTADO.** Ele saiu da pasta de upload; a checagem de existencia e
   feita na pasta de upload, entao o mesmo envio o traz DE VOLTA.

## Como rodar

    .venv\\Scripts\\python.exe _reversa_forward/011-escolher-arquivo-da-lista/evidence/_sonda_arquivo_repetido.py
"""
from __future__ import annotations

import importlib.util
import io
import os
import re
import shutil
import sys
import uuid

_RAIZ = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", ".."))
sys.path.insert(0, _RAIZ)
sys.path.insert(0, os.path.join(_RAIZ, "src"))

GEDCOM = (
    "0 HEAD\n1 SOUR TESTE\n1 GEDC\n2 VERS 5.5.1\n2 FORM LINEAGE-LINKED\n"
    "0 @I1@ INDI\n1 NAME Maria /Souza/\n1 SEX F\n0 TRLR\n"
).encode("utf-8")


def _montar_app(pasta_de_uploads: str):
    os.environ["ANALISADOR_UPLOAD_FOLDER"] = pasta_de_uploads
    caminho = os.path.join(_RAIZ, "src", "app.py")
    spec = importlib.util.spec_from_file_location("_app_sonda", caminho)
    modulo = importlib.util.module_from_spec(spec)
    modulo.__file__ = caminho
    spec.loader.exec_module(modulo)
    modulo.app.root_path = os.path.join(_RAIZ, "src")
    return modulo.app


def _enviar(cliente, nome_visivel: str, conteudo: bytes = GEDCOM) -> str:
    resposta = cliente.post("/", data={
        "action": "upload_gedcom",
        "gedcom": (io.BytesIO(conteudo), nome_visivel),
    }, content_type="multipart/form-data")
    corpo = resposta.get_data(as_text=True)
    alerta = re.search(r'role="alert">\s*([^<]+)', corpo)
    return (alerta.group(1).strip() if alerta else "(sem mensagem)")


def _linhas_da_tabela(cliente) -> list[str]:
    """As linhas da aba de arvore, como a tela as mostra."""
    corpo = cliente.get("/").get_data(as_text=True)
    tabelas = re.findall(r"(?s)<table.*?</table>", corpo)
    if not tabelas:
        return ["(nenhuma tabela)"]
    saida = []
    for linha in re.findall(r"(?s)<tr>(.*?)</tr>", tabelas[0])[1:]:
        celulas = [
            re.sub(r"\s+", " ", re.sub(r"<[^>]+>", "", c)).strip()
            for c in re.findall(r"(?s)<td[^>]*>(.*?)</td>", linha)
        ]
        saida.append(" | ".join(celulas))
    return saida or ["(tabela so com cabecalho)"]


def _pasta(pasta: str) -> list[str]:
    return sorted(os.listdir(pasta))


def main() -> int:
    base = os.path.join(_RAIZ, "tests", ".tmp", uuid.uuid4().hex)
    uploads = os.path.join(base, "uploads")
    os.makedirs(uploads)
    try:
        app = _montar_app(uploads)
        cliente = app.test_client()

        print("=" * 78)
        print("CASO 1: mesmo conteudo, MESMO nome, enviado duas vezes")
        print("=" * 78)
        print("  1o envio ->", _enviar(cliente, "arvore.ged"))
        print("  pasta:", _pasta(uploads))
        print("  2o envio ->", _enviar(cliente, "arvore.ged"))
        print("  pasta:", _pasta(uploads))
        print("  linhas na tela:")
        for linha in _linhas_da_tabela(cliente):
            print("   ", linha)

        print()
        print("=" * 78)
        print("CASO 2: mesmo conteudo, nome DIFERENTE")
        print("=" * 78)
        print("  envio de 'arvore-copia.ged' ->", _enviar(cliente, "arvore-copia.ged"))
        print("  pasta:", _pasta(uploads))
        print("  linhas na tela:")
        for linha in _linhas_da_tabela(cliente):
            print("   ", linha)

        print()
        print("=" * 78)
        print("CASO 3: o arquivo e aposentado, e depois enviado de novo")
        print("=" * 78)
        alvo = "arvore.ged"
        armazenado = next((n for n in _pasta(uploads) if n.endswith("__" + alvo)), None)
        print("  aposentando", armazenado)
        cliente.post("/", data={"action": "aposentar_arquivo", "arquivo_a_aposentar": armazenado})
        print("  pasta de upload:", _pasta(uploads))
        print("  pasta de aposentados:", _pasta(os.path.join(uploads, "_aposentados")))
        print("  linhas na tela:")
        for linha in _linhas_da_tabela(cliente):
            print("   ", linha)
        print("  reenviando o MESMO arquivo ->", _enviar(cliente, alvo))
        print("  pasta de upload:", _pasta(uploads))
        print("  pasta de aposentados:", _pasta(os.path.join(uploads, "_aposentados")))
        print("  linhas na tela:")
        for linha in _linhas_da_tabela(cliente):
            print("   ", linha)

        print()
        print("=" * 78)
        print("CASO 4: mesmo nome, conteudo DIFERENTE -- o arquivo ATUALIZADO")
        print("=" * 78)
        atualizado = GEDCOM.replace(b"0 TRLR", b"1 NOTE versao dois\n0 TRLR")
        print("  envio de", alvo, "com conteudo novo ->", _enviar(cliente, alvo, atualizado))
        print("  pasta de upload:", [n for n in _pasta(uploads) if not n.startswith("_")])
        print("  pasta de aposentados:", _pasta(os.path.join(uploads, "_aposentados")))
        print("  linhas na tela:")
        for linha in _linhas_da_tabela(cliente):
            print("   ", linha)
        return 0
    finally:
        try:
            os.chdir(_RAIZ)
        except OSError:
            pass
        shutil.rmtree(base, ignore_errors=True)


if __name__ == "__main__":
    raise SystemExit(main())

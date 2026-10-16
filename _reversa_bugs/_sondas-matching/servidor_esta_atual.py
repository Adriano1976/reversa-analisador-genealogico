"""O servidor que esta' no ar serve o codigo da arvore de trabalho, ou esta' velho?

A tela de entrada NAO tem um unico HTML: ela muda conforme a pasta de upload. O hash
congelado em `tests/test_icone_de_atalho.py` mede a tela com a pasta VAZIA (o fixture usa
`tmp_path`). O servidor no ar usa `src/uploads`, que nao esta' vazia — entao o hash dele
ser diferente do declarado nao prova nada por si so'.

Esta sonda renderiza `GET /` em processo, com a MESMA pasta que o servidor usa, e compara
byte a byte com o que o servidor devolveu. Se baterem, o processo no ar esta' atual.

Uso:
  .\\.venv\\Scripts\\python.exe _reversa_bugs\\_sondas-matching\\servidor_esta_atual.py <pagina_salva.html>
"""

import hashlib
import importlib.util
import os
import sys
import urllib.request

R = r"D:\Projetos\reversa_analisador_gelealogico"
PASTA_APP = os.path.join(R, "src")


def corpo_do_servidor(url="http://127.0.0.1:5000/", destino=None):
    with urllib.request.urlopen(url, timeout=10) as r:
        corpo = r.read()
    if destino:
        with open(destino, "wb") as fh:
            fh.write(corpo)
    return corpo


def corpo_renderizado_em_processo():
    for p in (R, PASTA_APP):
        if p not in sys.path:
            sys.path.insert(0, p)
    caminho = os.path.join(PASTA_APP, "app.py")
    spec = importlib.util.spec_from_file_location("_app_sonda", caminho)
    modulo = importlib.util.module_from_spec(spec)
    modulo.__file__ = caminho
    spec.loader.exec_module(modulo)
    modulo.app.root_path = PASTA_APP
    with modulo.app.test_client() as cliente:
        return cliente.get("/").get_data()


def main():
    destino = sys.argv[1] if len(sys.argv) > 1 else None

    print(f"pasta de upload em uso (env): {os.environ.get('ANALISADOR_UPLOAD_FOLDER') or '(nao definida -> src/uploads)'}")
    uploads = os.path.join(PASTA_APP, "uploads")
    arquivos = sorted(f for f in os.listdir(uploads) if os.path.isfile(os.path.join(uploads, f)))
    print(f"arquivos na pasta: {len(arquivos)}")
    for f in arquivos:
        print(f"  {f}")

    servido = corpo_do_servidor(destino=destino)
    local = corpo_renderizado_em_processo()

    hs = hashlib.sha256(servido).hexdigest()
    hl = hashlib.sha256(local).hexdigest()
    print()
    print(f"servidor no ar : sha={hs}  bytes={len(servido)}")
    print(f"render local   : sha={hl}  bytes={len(local)}")
    print(f"IGUAIS         : {servido == local}")
    if servido != local:
        # Primeira linha em que divergem, para nao adivinhar onde esta' a diferenca.
        i = next((k for k in range(min(len(servido), len(local))) if servido[k] != local[k]),
                 min(len(servido), len(local)))
        print(f"primeira divergencia no byte {i}")
        print(f"  servidor: {servido[max(0, i - 80):i + 120]!r}")
        print(f"  local   : {local[max(0, i - 80):i + 120]!r}")


if __name__ == "__main__":
    main()

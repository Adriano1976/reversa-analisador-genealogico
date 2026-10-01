"""Prova de equivalencia da OPP-20260929-SEQO: o app continua com as mesmas rotas.

Compara o app.py atual com a copia podada, carregando os dois como modulos
distintos e contrastando:

  1. url_map completo: regra, metodos e endpoint de cada rota
  2. static_folder e static_url_path efetivos
  3. funcoes de view registradas

Roda com o diretorio de trabalho num temp, para que os makedirs do proprio app.py
nao criem pastas dentro do projeto.
"""
import importlib.util
import os
import pathlib
import sys

ROOT = pathlib.Path(r"D:\Projetos\reversa_analisador_gelealogico")
# A e a linha de base; B e a versao sob teste. Ver equivalence_matching.py.
REAL = pathlib.Path(os.environ.get(
    "VARIANT_A_FILE", str(ROOT / "analisador-genealogico" / "app.py")))
SHADOW = pathlib.Path(os.environ.get(
    "VARIANT_B_FILE", str(ROOT / ".pytest-tmp" / "shadow_app" / "app.py")))
TEMP = ROOT / ".pytest-tmp" / "temp"

TEMP.mkdir(parents=True, exist_ok=True)
os.chdir(TEMP)
sys.path.insert(0, str(ROOT / "analisador-genealogico"))


def carregar(caminho, nome):
    spec = importlib.util.spec_from_file_location(nome, caminho)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[nome] = mod
    spec.loader.exec_module(mod)
    return mod


def radiografar(mod):
    flask_app = mod.app
    rotas = sorted(
        (str(r.rule), ",".join(sorted(r.methods - {"HEAD", "OPTIONS"})), r.endpoint)
        for r in flask_app.url_map.iter_rules()
    )
    return {
        "rotas": rotas,
        # Comparacao relativa ao diretorio do proprio modulo: o caminho absoluto
        # difere por construcao, porque a copia sombra mora em outro diretorio.
        "static_folder_rel": os.path.relpath(
            str(flask_app.static_folder), os.path.dirname(mod.__file__)
        ).replace("\\", "/"),
        "static_url_path": flask_app.static_url_path,
        "views": sorted(flask_app.view_functions),
    }


def main():
    if not SHADOW.is_file():
        print("ERRO: sombra ausente. Rode .pytest-tmp/shadow_seqo_build.py antes.")
        return 2

    antes = radiografar(carregar(REAL, "app_antes"))
    depois = radiografar(carregar(SHADOW, "app_depois"))

    print(f"CWD do teste: {os.getcwd()}")
    print(f"\nrotas do app atual ({len(antes['rotas'])}):")
    for r in antes["rotas"]:
        print(f"  {r[1]:<10} {r[0]:<20} -> {r[2]}")
    print(f"static_folder    : {antes['static_folder_rel']} (relativo ao modulo)")
    print(f"static_url_path  : {antes['static_url_path']}")

    divergencias = []
    for campo in ("rotas", "static_folder_rel", "static_url_path", "views"):
        if antes[campo] != depois[campo]:
            divergencias.append((campo, antes[campo], depois[campo]))

    if divergencias:
        print("\nEQUIVALENCIA VERMELHA")
        for campo, a, b in divergencias:
            print(f"  {campo}:\n    antes ={a}\n    depois={b}")
        return 1

    print(f"\nEQUIVALENCIA VERDE: {len(antes['rotas'])} rotas, static_folder, "
          f"static_url_path e {len(antes['views'])} views identicos")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

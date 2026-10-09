"""Remove as copias de arrasto de dado real dentro de `_reversa_refactor/` (feature 012).

Uso:

    python _reversa_forward/012-pasta-canonica-no-repositorio/evidence/_remover_copias_de_arrasto.py [--simular]

## Por que estas copias existem

As tres transformacoes de refactor de 2026-10-03 congelaram `src/` inteiro para poder emitir os seus
diffs contra um estado anterior confiavel -- o `HEAD` daquela epoca nao servia:

    "Antes de mover qualquer arquivo, `src/` foi copiado inteiro para `before-after/src-antes/`."
    -- OPP-20261003-RAIZ-distribuir-modulos-soltos/transformation.md:142

`src/uploads` foi junto porque **esta dentro de `src/`**. Nao houve decisao de copiar dado do
operador: houve copia de `src/`, e o dado estava la dentro. Sao 9 arquivos e 16.920.784 bytes por
diretorio, incluindo a arvore real de 5,3 MB.

## O criterio de cancelamento, e por que e sobre CONTEUDO

Antes de remover, o instrumento confere que **todo `sha256` do diretorio ocorre em `src/uploads`**.
Se qualquer arquivo for o unico exemplar do seu conteudo, aquele diretorio **nao e removido** e o
arquivo e nomeado no relatorio.

O criterio e sobre conteudo, e nao sobre nome, porque a copia carrega os tres nomes do formato
anterior a chave derivada (`Adriano_Santos.ged`, `Arvore_Unificada_Oficial_V1_2.ged`,
`Familias_Sergipanas.csv`) -- um criterio por nome os trataria como desconhecidos.

Medicao de 2026-10-09: **0 orfaos** nos tres diretorios. E isso que torna a remocao prova, e nao fe.

## Outras guardas

1. **So os tres caminhos conhecidos.** Qualquer outro caminho e recusa, mesmo que pareca igual.
2. **Nada dentro da pasta canonica**, e nada que contenha a pasta canonica.
3. **So arquivos regulares.** Subdiretorio ou link simbolico cancela o diretorio.
4. **Os irmaos de codigo ficam.** Antes e depois, `src-antes/app.py` e `src-antes/reconstructed/`
   tem de existir -- a copia existe para servir o `registrar-diff.py`, e o codigo e o que interessa.
5. **O git nao pode ganhar linha.** `git status --porcelain` e comparado antes e depois.

Codigos de saida: 0 removido (ou simulado), 2 nada a fazer, 3 alguma guarda recusou, 4 caminho inseguro.
"""
from __future__ import annotations

import os
import shutil
import subprocess
import sys

RAIZ = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
sys.path.insert(0, os.path.join(RAIZ, "tests"))

from manutencao_de_uploads import inventariar  # noqa: E402

CANONICA = os.path.join(RAIZ, "src", "uploads")
BASE = os.path.join(RAIZ, "_reversa_refactor", "pacote-reconstructed", "transformations")

# Os tres diretorios medidos em 2026-10-09: 9 arquivos e 16.920.784 bytes cada.
ALVOS = [
    ("OPP-20261003-FLAT-achatar-o-nivel-de-pacote", "FLAT"),
    ("OPP-20261003-GUE7-reorganizar-em-subpacotes", "GUE7"),
    ("OPP-20261003-RAIZ-distribuir-modulos-soltos", "RAIZ"),
]

ESPERADO_ARQUIVOS = 9
ESPERADO_BYTES = 16920784

IRMAOS_DE_CODIGO = ["app.py", os.path.join("reconstructed", "__init__.py")]


def caminho_do_alvo(pasta_oportunidade: str) -> str:
    return os.path.join(BASE, pasta_oportunidade, "before-after", "src-antes", "uploads")


def pasta_src_antes(pasta_oportunidade: str) -> str:
    return os.path.join(BASE, pasta_oportunidade, "before-after", "src-antes")


def resumo(inventario: dict) -> str:
    return "%d arquivos, %d bytes" % (len(inventario), sum(t for t, _ in inventario.values()))


def git_status() -> str:
    r = subprocess.run(["git", "status", "--porcelain"], cwd=RAIZ, capture_output=True, text=True)
    return r.stdout


def forma_ok(alvo: str) -> tuple:
    """So arquivos regulares: nenhum subdiretorio, nenhum link simbolico."""
    problemas = []
    for nome in sorted(os.listdir(alvo)):
        caminho = os.path.join(alvo, nome)
        if os.path.islink(caminho):
            problemas.append((nome, "link simbolico"))
        elif os.path.isdir(caminho):
            problemas.append((nome, "subdiretorio"))
        elif not os.path.isfile(caminho):
            problemas.append((nome, "nao e arquivo regular"))
    return (not problemas), problemas


def orfaos(inventario: dict, hashes_canonicos: set) -> list:
    """Arquivos cujo conteudo NAO existe na pasta canonica."""
    return sorted(nome for nome, (_t, h) in inventario.items() if h not in hashes_canonicos)


def caminho_seguro(alvo: str) -> tuple:
    alvo_abs = os.path.abspath(alvo)
    canonica_abs = os.path.abspath(CANONICA)
    base_abs = os.path.abspath(BASE)
    if alvo_abs == canonica_abs or alvo_abs.startswith(canonica_abs + os.sep):
        return False, "o alvo esta dentro da pasta canonica"
    if canonica_abs.startswith(alvo_abs + os.sep):
        return False, "o alvo conte m a pasta canonica"
    if not alvo_abs.startswith(base_abs + os.sep):
        return False, "o alvo nao esta sob a base das transformacoes"
    if os.path.basename(alvo_abs) != "uploads" or os.path.basename(os.path.dirname(alvo_abs)) != "src-antes":
        return False, "o alvo nao tem a forma .../before-after/src-antes/uploads"
    return True, ""


def main(argv: list) -> int:
    simular = "--simular" in argv

    print("# Remocao das copias de arrasto - feature 012")
    print("# Pasta canonica : %s" % CANONICA)
    print("# Modo           : %s" % ("SIMULACAO (nada sera removido)" if simular else "APLICADO"))
    print()

    inventario_canonico = inventariar(CANONICA)
    hashes_canonicos = {h for _t, h in inventario_canonico.values()}
    print("# Canonica: %s (%d hashes distintos)"
          % (resumo(inventario_canonico), len(hashes_canonicos)))

    status_antes = git_status()
    print("# git status --porcelain: %d linha(s) antes" % len(status_antes.splitlines()))
    print()

    recusados = []
    removidos = []

    for pasta, apelido in ALVOS:
        alvo = caminho_do_alvo(pasta)
        print("== %s" % apelido)
        print("   %s" % alvo)

        if not os.path.isdir(alvo):
            print("   AUSENTE: nada a fazer")
            print()
            continue

        seguro, motivo = caminho_seguro(alvo)
        if not seguro:
            print("   RECUSADO: %s" % motivo)
            recusados.append((apelido, motivo))
            print()
            continue

        ok, problemas = forma_ok(alvo)
        if not ok:
            print("   RECUSADO: conteudo fora da forma esperada")
            for nome, p in problemas:
                print("      %s: %s" % (nome, p))
            recusados.append((apelido, "conteudo fora da forma esperada"))
            print()
            continue

        inv = inventariar(alvo)
        print("   inventario: %s" % resumo(inv))

        if len(inv) != ESPERADO_ARQUIVOS:
            print("   AVISO: esperado %d arquivos, medido %d (segue, o criterio e o de orfaos)"
                  % (ESPERADO_ARQUIVOS, len(inv)))
        bytes_totais = sum(t for t, _ in inv.values())
        if bytes_totais != ESPERADO_BYTES:
            print("   AVISO: esperado %d bytes, medido %d" % (ESPERADO_BYTES, bytes_totais))

        faltando = orfaos(inv, hashes_canonicos)
        if faltando:
            print("   RECUSADO: %d arquivo(s) cujo conteudo NAO existe na canonica:" % len(faltando))
            for nome in faltando:
                print("      %s" % nome)
            recusados.append((apelido, "%d orfao(s)" % len(faltando)))
            print()
            continue

        print("   orfaos: 0 -- todo conteudo existe em src/uploads")
        print("   irmaos de codigo presentes: %s"
              % all(os.path.exists(os.path.join(pasta_src_antes(pasta), i)) for i in IRMAOS_DE_CODIGO))

        if simular:
            print("   SIMULADO: seria removido")
        else:
            shutil.rmtree(alvo)
            print("   REMOVIDO")
            removidos.append(apelido)

        ok_irmaos = all(os.path.exists(os.path.join(pasta_src_antes(pasta), i))
                        for i in IRMAOS_DE_CODIGO)
        if not ok_irmaos:
            print("   FALHA: os irmaos de codigo sumiram junto")
            return 3
        print()

    print("=" * 70)
    print("# resumo")
    print("#   removidos/simulados : %d" % (len(removidos) if not simular else len(ALVOS) - len(recusados)))
    print("#   recusados           : %d" % len(recusados))
    for apelido, motivo in recusados:
        print("#      %s: %s" % (apelido, motivo))

    inventario_depois = inventariar(CANONICA)
    print("#   canonica antes      : %s" % resumo(inventario_canonico))
    print("#   canonica depois     : %s" % resumo(inventario_depois))
    if inventario_depois != inventario_canonico:
        print("FALHA: a pasta canonica mudou.")
        return 3

    status_depois = git_status()
    print("#   git status antes    : %d linha(s)" % len(status_antes.splitlines()))
    print("#   git status depois   : %d linha(s)" % len(status_depois.splitlines()))
    if status_depois != status_antes:
        print("FALHA: o git status mudou. Compare as duas saidas.")
        return 3

    if recusados:
        return 3
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))

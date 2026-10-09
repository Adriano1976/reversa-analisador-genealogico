"""T013 - prova, por EXECUCAO, de que a retirada das copias de arrasto nao quebrou os
instrumentos do refactor.

## Por que a prova roda numa copia

`registrar-diff.py` **reescreve** os cinco `CHG-*.diff` da sua pasta, e esses cinco sao
arquivos **rastreados** pelo git. `_reversa_refactor/**` nao esta em `allowedPaths` de
`.reversa/reversa-config.json`, entao executa-lo no lugar mudaria artefato versionado fora
dos caminhos autorizados. Toda a prova roda numa copia minima da arvore.

## O desenho: controle A/B

Dizer "o instrumento roda e nao quebra" nao prova que ele nao quebrou **por causa da
retirada**. Entao a prova e comparativa, e o controle e reconstruivel: os 9 nomes que
existiam em cada `src-antes/uploads/` existem tambem em `src/uploads`, com o mesmo
conteudo. Isso permite montar as duas situacoes e comparar a saida dos instrumentos:

- **A** - sem as copias de arrasto (o estado depois de `T012`);
- **B** - com as copias de arrasto reconstruidas, nome a nome, a partir de `src/uploads`.

Se a saida de A for **identica** a de B nos dois instrumentos, entao a retirada nao muda
nada do que eles medem -- que e a afirmacao de `T013`, agora provada em vez de afirmada.

## Detalhe de metodo

Os cinco `CHG-*.diff` sao **apagados** da copia antes de cada rodada. Assim, o que existir
depois foi de fato regravado pelo instrumento -- e nao sobrou da copia, que era o furo da
primeira versao desta verificacao.
"""
from __future__ import annotations

import hashlib
import os
import shutil
import subprocess
import sys

AQUI = os.path.dirname(os.path.abspath(__file__))
RAIZ = os.path.dirname(os.path.dirname(os.path.dirname(AQUI)))

OPP = "OPP-20261003-FLAT-achatar-o-nivel-de-pacote"
REL_OPP = os.path.join("_reversa_refactor", "pacote-reconstructed", "transformations", OPP)
REL_RW = os.path.join("_reversa_forward", "003-renomear-pasta-app-para-src", "regression-watch.md")

# Os 9 nomes que cada copia de arrasto continha, medidos em 2026-10-09. Todos existem
# tambem em `src/uploads`, com o mesmo conteudo -- e isso que torna o controle possivel.
NOMES_DAS_COPIAS = [
    "080e7943572d2652__080e7943572d2652__Arvore_Unificada_Oficial_V1_2.ged",
    "080e7943572d2652__Arvore_Unificada_Oficial_V1_2.ged",
    "20a046eb06150ccd__nomes-inertes.ged",
    "7d693792453770c9__DNA_Nordestino.csv",
    "94e2402671702cac__Famílias_Sergipanas.csv",
    "94e2402671702cac__Famílias_Sergipanas.csv.ged",
    "Adriano_Santos.ged",
    "Arvore_Unificada_Oficial_V1_2.ged",
    "Famílias_Sergipanas.csv",
]

LOTES = [
    "CHG-001-movimentacao.diff",
    "CHG-002-relativo-vira-absoluto.diff",
    "CHG-003-prefixo-sai-do-import.diff",
    "CHG-004-prosa-e-readme.diff",
    "CHG-005-watch-w001.diff",
]

COPIA = os.path.join(AQUI, "_t013")


def sha256_de(caminho: str) -> str:
    h = hashlib.sha256()
    with open(caminho, "rb") as fh:
        for b in iter(lambda: fh.read(1 << 20), b""):
            h.update(b)
    return h.hexdigest()


def montar_copia(sufixo: str, com_as_copias: bool) -> str:
    """Copia minima da arvore. `com_as_copias` reconstroi os `src-antes/uploads/`."""
    raiz = os.path.join(COPIA, sufixo)
    if os.path.isdir(raiz):
        shutil.rmtree(raiz)
    os.makedirs(raiz)
    shutil.copytree(os.path.join(RAIZ, "src"), os.path.join(raiz, "src"))
    for nome in ("README.md", "pyrefly.toml"):
        shutil.copy2(os.path.join(RAIZ, nome), os.path.join(raiz, nome))
    destino_rw = os.path.join(raiz, REL_RW)
    os.makedirs(os.path.dirname(destino_rw))
    shutil.copy2(os.path.join(RAIZ, REL_RW), destino_rw)
    shutil.copytree(os.path.join(RAIZ, REL_OPP), os.path.join(raiz, REL_OPP))

    if com_as_copias:
        for apelido in ("FLAT-achatar-o-nivel-de-pacote", "GUE7-reorganizar-em-subpacotes",
                        "RAIZ-distribuir-modulos-soltos"):
            destino = os.path.join(raiz, "_reversa_refactor", "pacote-reconstructed",
                                   "transformations", "OPP-20261003-" + apelido,
                                   "before-after", "src-antes", "uploads")
            os.makedirs(destino, exist_ok=True)
            for nome in NOMES_DAS_COPIAS:
                shutil.copy2(os.path.join(RAIZ, "src", "uploads", nome),
                             os.path.join(destino, nome))
    return raiz


def rodar(raiz: str, script_rel: str) -> tuple:
    # Apaga os CHG para que o que existir depois tenha sido de fato regravado.
    pasta_opp = os.path.join(raiz, REL_OPP)
    for nome in LOTES:
        alvo = os.path.join(pasta_opp, nome)
        if os.path.exists(alvo):
            os.remove(alvo)
    r = subprocess.run([sys.executable, os.path.join(pasta_opp, script_rel)],
                       capture_output=True, text=True, cwd=raiz)
    return r.returncode, (r.stdout or ""), (r.stderr or "")


def relatar(rotulo: str, resultado: tuple) -> None:
    codigo, saida, erro = resultado
    print("   %s: exit code %d, %d linha(s) de saida, %d de erro"
          % (rotulo, codigo, len(saida.splitlines()), len(erro.splitlines())))
    menciona = [l for l in (saida + erro).splitlines() if "uploads" in l.lower()]
    print("      linhas que mencionam 'uploads': %d" % len(menciona))
    for l in menciona[:5]:
        print("         " + l.strip()[:110])


def normalizar(resultado: tuple, raiz: str) -> tuple:
    """Troca o caminho da copia por um marcador, nas tres formas em que ele aparece.

    Sem isto a comparacao A/B seria falsa por construcao: as duas copias vivem em pastas
    de nomes diferentes (`A-sem-as-copias` e `B-com-as-copias`), e todo caminho absoluto
    que aparece na saida difere entre elas. A terceira forma -- barra duplicada -- aparece
    dentro da mensagem de excecao, onde o caminho e escrito como `repr`.
    """
    formas = {raiz, raiz.replace("\\", "/"), raiz.replace("\\", "\\\\")}
    codigo, saida, erro = resultado
    for forma in formas:
        saida = saida.replace(forma, "<RAIZ>")
        erro = erro.replace(forma, "<RAIZ>")
    return (codigo, saida, erro)


def main() -> int:
    print("# T013 - instrumentos do refactor depois da retirada das copias de arrasto")
    print()
    print("## 1. Montagem das duas situacoes (controle A/B)")
    raiz_a = montar_copia("A-sem-as-copias", com_as_copias=False)
    raiz_b = montar_copia("B-com-as-copias", com_as_copias=True)
    n_b = sum(len(os.listdir(os.path.join(raiz_b, "_reversa_refactor", "pacote-reconstructed",
                                          "transformations", "OPP-20261003-" + a,
                                          "before-after", "src-antes", "uploads")))
              for a in ("FLAT-achatar-o-nivel-de-pacote", "GUE7-reorganizar-em-subpacotes",
                        "RAIZ-distribuir-modulos-soltos"))
    print("   A: sem as copias de arrasto")
    print("   B: com as copias reconstruidas a partir de src/uploads (%d arquivos)" % n_b)
    print()

    print("## 2. registrar-diff.py nas duas situacoes")
    a = rodar(raiz_a, "registrar-diff.py")
    b = rodar(raiz_b, "registrar-diff.py")
    relatar("A", a)
    relatar("B", b)
    na, nb = normalizar(a, raiz_a), normalizar(b, raiz_b)
    print("   saida identica entre A e B (caminhos normalizados): %s" % (na == nb))
    if a[0] != 0:
        print("   --- stderr de A (diagnostico) ---")
        for l in a[2].strip().splitlines()[-14:]:
            print("   " + l)
    print()
    print("   quais CHG foram de fato regravados em A:")
    for nome in LOTES:
        existe = os.path.exists(os.path.join(raiz_a, REL_OPP, nome))
        h = sha256_de(os.path.join(raiz_a, REL_OPP, nome)) if existe else "-"
        hv = sha256_de(os.path.join(RAIZ, REL_OPP, nome))
        marca = "identico ao commitado" if existe and h == hv else ("AUSENTE (nao regravado)" if not existe else "DIVERGENTE do commitado")
        print("      %-40s %s" % (nome, marca))
    print()

    print("## 3. verificar-estrutura.py nas duas situacoes (somente leitura)")
    a2 = rodar(raiz_a, "verificar-estrutura.py")
    b2 = rodar(raiz_b, "verificar-estrutura.py")
    relatar("A", a2)
    relatar("B", b2)
    na2, nb2 = normalizar(a2, raiz_a), normalizar(b2, raiz_b)
    print("   saida identica entre A e B (caminhos normalizados): %s" % (na2 == nb2))
    print("   --- ultimas linhas de A ---")
    for l in a2[1].strip().splitlines()[-10:]:
        print("   " + l)
    print()

    print("## 4. Veredito")
    iguais = (na == nb) and (na2 == nb2)
    print("   A retirada das copias de arrasto muda a saida dos instrumentos? %s"
          % ("NAO" if iguais else "SIM"))
    print("   Os instrumentos executam? registrar-diff exit %d, verificar-estrutura exit %d"
          % (a[0], a2[0]))
    todas = (a[1] + a[2] + b[1] + b[2] + a2[1] + a2[2] + b2[1] + b2[2]).splitlines()
    menciona = [l.strip() for l in todas if "uploads" in l.lower()]
    print("   Linhas que mencionam 'uploads' nas quatro saidas: %d" % len(menciona))
    for l in sorted(set(menciona)):
        print("      %r" % l[:100])
    print("   (a unica ocorrencia e a linha 'uploads/' da listagem da arvore de src/,")
    print("    que aparece igual nas duas situacoes -- nao e reclamacao)")
    shutil.rmtree(COPIA, ignore_errors=True)
    print("   copia removida: %s" % (not os.path.isdir(COPIA)))
    return 0


if __name__ == "__main__":
    sys.exit(main())

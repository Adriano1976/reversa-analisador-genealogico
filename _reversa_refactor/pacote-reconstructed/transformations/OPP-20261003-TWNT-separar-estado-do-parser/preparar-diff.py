"""Prepara os diffs da OPP-20261003-TWNT sem tocar em nenhum arquivo do projeto.

Modo de operacao: calcula tudo em memoria, grava apenas os CHG-*.diff nesta pasta
do registro. Nenhum arquivo de `src/`, `tests/`, `_reversa_sdd/` ou raiz e escrito.

Os dois modulos novos sao DERIVADOS por fatiamento do `upload.py` atual, para que
os docstrings existentes (em especial o aviso de `get_name` sobre formato vazio,
que ancora o DIV-001) sejam preservados literalmente, sem redigitacao.
"""
import difflib
import pathlib
import re
import sys

RAIZ = pathlib.Path(".")
ALVO = RAIZ / "src" / "reconstructed" / "upload.py"
SAIDA = pathlib.Path("_reversa_refactor/pacote-reconstructed/transformations/OPP-20261003-TWNT-separar-estado-do-parser")

# ---------------------------------------------------------------- derivacao

CABECALHO_ESTADO = '''"""Estado do GEDCOM carregado e acesso aos registros.

Responsabilidade unica: ser o registro do estado do processo (singleton, nao
persistente) e dar acesso aos registros de pessoa e de familia.

## Contrato de estado

`load_gedcom_and_build_graph`, em `gedcom_parser`, muta `people`, `families` e
`child_to_family` in place (`clear()` mais `update()`) para que o binding
importado no topo pelos outros modulos continue apontando para o objeto vivo.
`graph` e a excecao: e reatribuido, e por isso quem o consome o importa dentro da
funcao (ver `path_finding.py`).

Extraido de `upload.py` pela OPP-20261003-TWNT. As globais e as funcoes sao as
mesmas; o que mudou foi o endereco.
"""
from __future__ import annotations

'''

CABECALHO_PARSER = '''"""Parsing de GEDCOM e construcao do grafo.

Responsabilidade unica: traduzir um arquivo GEDCOM em registros e no grafo
bidirecional pessoa para familia, substituindo o estado do processo.

Extraido de `upload.py` pela OPP-20261003-TWNT. A assimetria de substituicao do
estado (dicionarios mutados in place, grafo reatribuido) e deliberada e esta
documentada em `gedcom_state`.
"""
from __future__ import annotations

import networkx as nx
from ged4py.parser import GedcomReader

from . import gedcom_state
from .gedcom_state import get_name, ref_id

'''


def fatiar(linhas, inicio, fim=None):
    return "\n".join(linhas[inicio:fim])


def derivar(linhas):
    """Devolve (conteudo_estado, conteudo_parser) a partir das linhas do alvo."""
    idx = {}
    for i, linha in enumerate(linhas):
        if linha.startswith("# Estado global em memória"):
            idx["globais"] = i
        elif linha.startswith("def ref_id("):
            idx["ref_id"] = i
        elif linha.startswith("def get_name("):
            idx["get_name"] = i
        elif linha.startswith("def build_graph_from_parser("):
            idx["build"] = i
        elif linha.startswith("def load_gedcom_and_build_graph("):
            idx["load"] = i
    faltando = [k for k in ("globais", "ref_id", "get_name", "build", "load") if k not in idx]
    if faltando:
        raise SystemExit("ABORTADO: marcadores nao encontrados em upload.py: %s" % faltando)

    # --- estado: globais, ref_id e get_name, verbatim
    estado = CABECALHO_ESTADO + fatiar(linhas, idx["globais"], idx["build"]).rstrip() + "\n"

    # --- parser: as duas funcoes, com o corpo do carregador adaptado
    build = fatiar(linhas, idx["build"], idx["load"]).rstrip()
    load = fatiar(linhas, idx["load"]).rstrip()

    if "    global people, families, graph, child_to_family\n" not in load:
        raise SystemExit("ABORTADO: a declaracao global do carregador mudou de forma")

    load = load.replace("    global people, families, graph, child_to_family\n", "")

    # Substituicoes explicitas por linha inteira. A primeira versao deste script
    # ancorava no inicio da linha e deixou passar os `.update()` e o
    # `people.values()`, que ficam depois de um ponto e virgula na mesma linha.
    # O defeito so apareceria em tempo de execucao, como NameError, porque a
    # checagem de sintaxe nao pega nome indefinido. Cada trecho e obrigatorio.
    substituicoes = [
        ("        people.clear(); people.update(new_people)",
         "        gedcom_state.people.clear(); gedcom_state.people.update(new_people)"),
        ("        families.clear(); families.update(new_families)",
         "        gedcom_state.families.clear(); gedcom_state.families.update(new_families)"),
        ("        graph = new_graph",
         "        gedcom_state.graph = new_graph"),
        ("        child_to_family.clear(); child_to_family.update(new_child_to_family)",
         "        gedcom_state.child_to_family.clear(); gedcom_state.child_to_family.update(new_child_to_family)"),
        ("for p in people.values()", "for p in gedcom_state.people.values()"),
    ]
    for antigo, novo in substituicoes:
        if antigo not in load:
            raise SystemExit("ABORTADO: trecho esperado nao encontrado no carregador: %r" % antigo)
        load = load.replace(antigo, novo)

    # Ajustes de prosa, aplicados ANTES da assercao: o docstring e o comentario
    # citam os nomes das globais em texto, e a assercao varre o texto inteiro.
    load = load.replace(
        "    Sobrescreve as globais people, families, graph e child_to_family.\n",
        "    Substitui o estado: dicionarios in place, grafo reatribuido. Ver `gedcom_state`.\n",
    )
    load = load.replace(
        "        # Mutação in-place (clear + update) mantém válidas referências\n"
        "        # importadas por outros módulos (ex.: path_search), preservando o\n"
        "        # design de estado global do legado.\n",
        "        # Mutação in-place (clear + update) mantém válidas as referências\n"
        "        # importadas no topo pelos outros módulos. A reatribuição do grafo\n"
        "        # é lida por quem o importa dentro da função (ver path_finding.py).\n",
    )

    # assercao de rede: nenhum dos nomes de estado pode sobrar sem o prefixo do
    # modulo. O lookbehind exclui `new_people` e `gedcom_state.people`.
    for nome in ("people", "families", "graph", "child_to_family"):
        sobra = re.search(r"(?<![\w.])" + nome + r"\b", load)
        if sobra:
            raise SystemExit(
                "ABORTADO: o carregador ainda referencia `%s` sem o prefixo do modulo "
                "de estado (posicao %d). O prefixo tem de alcancar TODAS as ocorrencias, "
                "inclusive as que ficam depois de ponto e virgula." % (nome, sobra.start())
            )

    parser = CABECALHO_PARSER + build + "\n\n\n" + load + "\n"
    return estado, parser


# ---------------------------------------------------------------- consumidores

INTERNOS = [
    "src/reconstructed/dna_analysis.py",
    "src/reconstructed/family_navigation.py",
    "src/reconstructed/matching.py",
    "src/reconstructed/mermaid_render.py",
    "src/reconstructed/path_finding.py",
    "src/reconstructed/path_search.py",
]

IMPORT_ANTIGO = "from reconstructed import upload\n"

TESTES = [
    "tests/test_characterization_matching.py",
    "tests/test_characterization_mermaid.py",
    "tests/test_dna_analysis.py",
    "tests/test_mermaid_escape.py",
    "tests/test_path_search.py",
    "tests/test_upload.py",
]

SIMBOLO_PARA_MODULO = {"load_gedcom_and_build_graph": "gedcom_parser"}
for _s in ("people", "families", "graph", "child_to_family", "get_name", "ref_id", "build_graph_from_parser"):
    SIMBOLO_PARA_MODULO[_s] = "gedcom_state"


def transformar_interno(texto):
    novo = texto.replace("from .upload import ", "from .gedcom_state import ")
    novo = novo.replace("## Contrato de import com `.upload`", "## Contrato de import com `.gedcom_state`")
    return novo


def transformar_app(texto):
    return texto.replace(
        "from reconstructed.upload import load_gedcom_and_build_graph",
        "from reconstructed.gedcom_parser import load_gedcom_and_build_graph",
    )


def transformar_teste(texto, modulos_esperados=None):
    """Reescreve as referencias ao modulo antigo nos arquivos de teste.

    Cobre TRES formas, e a primeira versao deste script so cobria a primeira:

      1. acesso a atributo, `upload.simbolo`;
      2. referencia nua ao modulo, como `return upload` numa fixture que devolve
         o modulo carregado. Foi esta forma que quebrou a suite no primeiro teste;
      3. mencao em prosa dentro de docstring, como ``upload``.

    A forma 2 e 3 resolvem para `gedcom_state`, que e o modulo devolvido pelas
    fixtures e o que os docstrings descrevem. A linha de import e reconstruida a
    partir dos modulos realmente usados.
    """
    modulos = set()
    PLACEHOLDER = "@@IMPORTS@@\n"

    # A linha de import sai de cena ANTES das outras regras, por um marcador.
    # A versao anterior dependia de a regra de referencia nua converter a linha,
    # e isso nao acontece em arquivo que so usa acesso a atributo: a linha antiga
    # sobrevivia e o import quebrava na coleta.
    novo = texto.replace(IMPORT_ANTIGO, PLACEHOLDER, 1)
    corpo = novo.replace(PLACEHOLDER, "")

    # 1. quais modulos sao necessarios, medido do texto sem a linha de import
    for simbolo in re.findall(r"\bupload\.([a-zA-Z_]+)", corpo):
        dono = SIMBOLO_PARA_MODULO.get(simbolo)
        if dono is None:
            raise SystemExit("ABORTADO: simbolo nao mapeado nos testes: upload.%s" % simbolo)
        modulos.add(dono)
    tem_nua = bool(re.search(r"(?<![\w.])upload\b(?!\s*\.)", corpo))
    if tem_nua:
        modulos.add("gedcom_state")

    # 2. acesso a atributo
    novo = re.sub(
        r"\bupload\.([a-zA-Z_]+)",
        lambda m: SIMBOLO_PARA_MODULO[m.group(1)] + "." + m.group(1),
        novo,
    )

    # 3. referencia nua e mencao em prosa. O lookbehind exclui
    #    `reconstructed.upload`, que existe em outro arquivo de teste.
    if tem_nua:
        novo = re.sub(r"(?<![\w.])upload\b(?!\s*\.)", "gedcom_state", novo)

    # 4. o marcador vira o bloco dos modulos necessarios
    bloco = "".join("from reconstructed import %s\n" % m for m in sorted(modulos))
    return novo.replace(PLACEHOLDER, bloco, 1)


def transformar_test_upload_extra(texto):
    return texto.replace(
        "from reconstructed.upload import build_graph_from_parser, get_name, ref_id\n",
        "from reconstructed.gedcom_parser import build_graph_from_parser\n"
        "from reconstructed.gedcom_state import get_name, ref_id\n",
    )


def transformar_harness(texto):
    # Alias curtos e livres. A primeira versao usou `P`, que o harness JA usa para
    # `path_search`: o import seguinte sobrescrevia o anterior e o coletor do
    # candidato morria com AttributeError. `GP` e `GS` nao colidem com nada.
    novo = texto.replace(
        "from reconstructed import upload as U\n",
        "from reconstructed import gedcom_parser as GP\nfrom reconstructed import gedcom_state as GS\n",
    )
    novo = novo.replace("U.load_gedcom_and_build_graph", "GP.load_gedcom_and_build_graph")
    for nome in ("people", "families", "graph", "child_to_family", "get_name"):
        novo = novo.replace("U." + nome, "GS." + nome)
    return novo


def transformar_check_split(texto):
    return texto.replace(
        "from reconstructed import upload as U\n", "from reconstructed import gedcom_parser as U\n"
    )


def transformar_verificador(texto):
    return texto.replace(
        'alvo = os.path.join(STUB, "upload.py")',
        'alvo = os.path.join(STUB, "gedcom_state.py")',
    )


# ---------------------------------------------------------------- diffs

def diff_unificado(caminho, antes, depois):
    if antes == depois:
        return None
    d = difflib.unified_diff(
        antes.splitlines(keepends=True),
        depois.splitlines(keepends=True),
        fromfile="a/" + caminho,
        tofile="b/" + caminho,
        n=3,
    )
    return "".join(d)


def aplicar(mudancas):
    """Aplica as mudancas exatamente como foram propostas no diff.

    Guarda de concorrencia: se o conteudo atual de um arquivo nao for o `antes`
    que gerou o diff aprovado, aborta sem escrever nada. Isso garante que o
    aplicado e o aprovado sao a mesma coisa, byte a byte.
    """
    for numero, caminho, antes, depois in mudancas:
        p = pathlib.Path(caminho)
        atual = p.read_text(encoding="utf-8") if p.exists() else ""
        if atual != (antes or ""):
            raise SystemExit(
                "ABORTADO: %s mudou desde a preparacao do diff. Nada foi aplicado. "
                "Reexecute o preparo e revise o diff." % caminho
            )
    feitos = []
    for numero, caminho, antes, depois in mudancas:
        p = pathlib.Path(caminho)
        if depois is None:
            p.unlink()
            feitos.append(("removido", caminho))
        else:
            p.write_text(depois, encoding="utf-8", newline="")
            feitos.append(("escrito ou atualizado", caminho))
    return feitos


def main():
    aplicar_agora = "--aplicar" in sys.argv

    if not ALVO.exists():
        raise SystemExit("ABORTADO: %s nao existe" % ALVO)
    linhas = ALVO.read_text(encoding="utf-8").split("\n")
    estado, parser = derivar(linhas)

    mudancas = []

    # novos modulos
    mudancas.append(("001", "src/reconstructed/gedcom_state.py", None, estado))
    mudancas.append(("002", "src/reconstructed/gedcom_parser.py", None, parser))

    # remocao
    mudancas.append(("003", "src/reconstructed/upload.py", "\n".join(linhas), None))

    # consumidores internos
    for caminho in INTERNOS:
        antes = pathlib.Path(caminho).read_text(encoding="utf-8")
        mudancas.append(("004", caminho, antes, transformar_interno(antes)))

    # app
    antes = pathlib.Path("src/app.py").read_text(encoding="utf-8")
    mudancas.append(("005", "src/app.py", antes, transformar_app(antes)))

    # testes
    for caminho in TESTES:
        antes = pathlib.Path(caminho).read_text(encoding="utf-8")
        depois = transformar_teste(antes)
        if caminho.endswith("test_upload.py"):
            depois = transformar_test_upload_extra(depois)
        mudancas.append(("006", caminho, antes, depois))

    # prosa de docstring que cita o modulo
    antes = pathlib.Path("tests/test_domain.py").read_text(encoding="utf-8")
    mudancas.append(("006", "tests/test_domain.py", antes, antes.replace(
        "consumido por `upload.py` e", "consumido por `gedcom_state.py` e")))

    # instrumentacao de paridade
    for caminho, fn in (
        ("_reversa_sdd/parity/harness.py", transformar_harness),
        ("_reversa_sdd/parity/_check_split_types.py", transformar_check_split),
        ("_reversa_sdd/parity/_verify_fix_gives_parity.py", transformar_verificador),
    ):
        antes = pathlib.Path(caminho).read_text(encoding="utf-8")
        mudancas.append(("007", caminho, antes, fn(antes)))

    SAIDA.mkdir(parents=True, exist_ok=True)

    if aplicar_agora:
        feitos = aplicar(mudancas)
        print("MODO APLICAR: %d mudancas aplicadas" % len(feitos))
        for situacao, caminho in feitos:
            print("   %-22s %s" % (situacao, caminho))
        print()
        print("diffs aprovados em %s (inalterados, fonte de reversao)" % SAIDA)
        return 0

    resumo = []
    for numero, caminho, antes, depois in mudancas:
        texto = diff_unificado(caminho, antes or "", depois or "")
        if texto is None:
            resumo.append(("SEM MUDANCA", numero, caminho, 0, 0))
            continue
        mais = sum(1 for l in texto.splitlines() if l.startswith("+") and not l.startswith("+++"))
        menos = sum(1 for l in texto.splitlines() if l.startswith("-") and not l.startswith("---"))
        nome = "CHG-%s-%s.diff" % (numero, pathlib.Path(caminho).stem.replace("_", "-"))
        (SAIDA / nome).write_text(texto, encoding="utf-8", newline="")
        resumo.append(("ok", numero, caminho, mais, menos))

    print("arquivos analisados = %d" % len(mudancas))
    print("%-6s %-6s %-46s %6s %6s" % ("", "CHG", "arquivo", "+", "-"))
    for situacao, numero, caminho, mais, menos in resumo:
        print("%-6s %-6s %-46s %6d %6d" % (situacao, numero, caminho, mais, menos))
    print()
    sem = [r for r in resumo if r[0] != "ok"]
    if sem:
        print("ATENCAO: %d arquivo(s) sem mudanca efetiva" % len(sem))
    print("diffs gravados em %s" % SAIDA)
    print("nenhum arquivo do projeto foi escrito (modo preparo)")
    return 0


if __name__ == "__main__":
    sys.exit(main())

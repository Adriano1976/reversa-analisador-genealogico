"""O indice de nomes do parentesco documental e um par imutavel (OPP-20261024-CACH).

O estado de modulo era um dicionario de dois campos, `chave` e `mapa`, e a publicacao
acontecia em dois tempos: gravar o mapa, depois gravar a chave. Entre as duas escritas, e
tambem entre a escrita e o `return` que relia o global, outra requisicao podia publicar o
indice dela. Medido em 2026-10-24 com duas arvores e duas threads: a requisicao que pediu
a arvore alfa recebeu o indice da arvore beta.

A guarda principal e estrutural porque o defeito e da implementacao, nao do resultado:
nenhuma verificacao de saida distingue, de forma deterministica, um mapa correto de um
mapa trocado sem forcar o entrelacamento dentro da janela. Ela le o modulo por AST, no
mesmo idioma de `tests/test_profundidade_do_caminho.py` e `test_fronteira_da_cirurgia.py`.

O teste de estresse do fim e complemento, nao guarda: afirma um invariante que nunca pode
falhar no codigo correto, e que falha de vez em quando no codigo com a janela aberta.
"""
from __future__ import annotations

import ast
import os
import sys
import threading

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, RAIZ)
sys.path.insert(0, os.path.join(RAIZ, "src"))

from core import homonimos  # noqa: E402

CAMINHO_DO_MODULO = os.path.join(RAIZ, "src", "core", "homonimos.py")


class _Nome:
    """A unica coisa que `get_name` usa de um nome: `.format()`."""

    def __init__(self, texto: str) -> None:
        self._texto = texto

    def format(self) -> str:
        return self._texto


class _Pessoa:
    """A unica coisa que o indice de nomes usa de uma pessoa: `.name`."""

    def __init__(self, nome: str) -> None:
        self.name = _Nome(nome)


def _arvore_de(*nomes: str, prefixo: str = "I"):
    """Uma arvore minima, na forma de quatro posicoes que o nucleo recebe.

    O prefixo dos xref_id importa: a chave do cache e `(tamanho, primeira chave,
    ultima chave)`, entao duas arvores com os mesmos ids seriam consideradas a mesma
    coisa. Prefixos diferentes garantem que a invalidacao seja exercitada de fato.
    """
    people = {f"@{prefixo}{indice}@": _Pessoa(nome) for indice, nome in enumerate(nomes, 1)}
    return (people, {}, None, {})


def _fonte() -> str:
    with open(CAMINHO_DO_MODULO, encoding="utf-8") as arquivo:
        return arquivo.read()


def _funcao(texto: str, nome: str = "_indice_por_nome") -> ast.FunctionDef:
    for no in ast.walk(ast.parse(texto)):
        if isinstance(no, ast.FunctionDef) and no.name == nome:
            return no
    raise AssertionError(f"funcao {nome} nao encontrada no modulo")


def _subscritos_no_indice(funcao: ast.FunctionDef) -> list[int]:
    """Linhas em que o indice e lido por subscrito, como `_INDICE_DE_NOMES[...]`."""
    linhas = []
    for no in ast.walk(funcao):
        if isinstance(no, ast.Subscript) and isinstance(no.value, ast.Name):
            if no.value.id == "_INDICE_DE_NOMES":
                linhas.append(no.lineno)
    return sorted(linhas)


def _valor_inicial_do_indice(texto: str) -> ast.expr:
    """O valor da atribuicao de modulo, que pode ser anotada ou simples."""
    for no in ast.parse(texto).body:
        if isinstance(no, ast.AnnAssign):
            if isinstance(no.target, ast.Name) and no.target.id == "_INDICE_DE_NOMES":
                return no.value
        elif isinstance(no, ast.Assign):
            for alvo in no.targets:
                if isinstance(alvo, ast.Name) and alvo.id == "_INDICE_DE_NOMES":
                    return no.value
    raise AssertionError("o indice de nomes nao e atribuido no nivel do modulo")


# ---------------------------------------------------------------------------
# Guardas estruturais: o defeito mora na forma, nao na saida
# ---------------------------------------------------------------------------


def test_indice_nao_e_lido_por_subscrito_dentro_da_funcao():
    """`_INDICE_DE_NOMES["chave"]` e `_INDICE_DE_NOMES["mapa"]` sao a janela.

    Enquanto a publicacao for feita campo a campo, existe o intervalo entre as duas
    escritas, e a leitura do retorno relê o global em vez de devolver o que acabou de
    ser montado. A guarda proibe as duas coisas de uma vez: nenhum subscrito no indice
    dentro de `_indice_por_nome`.
    """
    linhas = _subscritos_no_indice(_funcao(_fonte()))

    assert linhas == [], (
        "o indice de nomes voltou a ser lido por subscrito dentro de `_indice_por_nome`, "
        f"nas linhas {linhas}. O par (chave, mapa) tem de ser publicado de uma vez, e o "
        "retorno tem de vir da variavel local."
    )


def test_indice_e_declarado_como_par_imutavel():
    """A declaracao de modulo tem de ser uma tupla de dois elementos."""
    valor = _valor_inicial_do_indice(_fonte())

    assert isinstance(valor, ast.Tuple), (
        "o valor inicial de `_INDICE_DE_NOMES` nao e uma tupla"
    )
    assert len(valor.elts) == 2, (
        "o par tem de ter exatamente dois elementos: a chave e o mapa"
    )


def test_indice_e_uma_tupla_de_dois_elementos_em_execucao():
    """A mesma exigencia, vista do objeto em tempo de execucao."""
    indice = homonimos._INDICE_DE_NOMES

    assert isinstance(indice, tuple)
    assert len(indice) == 2


# ---------------------------------------------------------------------------
# Caracterizacao do caminho simples
# ---------------------------------------------------------------------------


def test_duas_chamadas_com_a_mesma_arvore_devolvem_o_mesmo_mapa():
    """A segunda chamada acerta o cache: mesmo objeto, sem remontar."""
    arvore = _arvore_de("Ana Alfa", "Zeca Alfa", prefixo="A")

    primeiro = homonimos._indice_por_nome(arvore)
    segundo = homonimos._indice_por_nome(arvore)

    assert segundo is primeiro
    assert set(primeiro) == {"ana alfa", "zeca alfa"}


def test_arvore_nova_invalida_o_indice():
    """Trocar de arvore tem de trocar a chave e o mapa."""
    alfa = _arvore_de("Ana Alfa", prefixo="A")
    beta = _arvore_de("Bruno Beta", "Yara Beta", prefixo="B")

    mapa_alfa = homonimos._indice_por_nome(alfa)
    mapa_beta = homonimos._indice_por_nome(beta)

    assert set(mapa_alfa) == {"ana alfa"}
    assert set(mapa_beta) == {"bruno beta", "yara beta"}
    assert mapa_beta is not mapa_alfa


# ---------------------------------------------------------------------------
# Estresse: o invariante que nunca pode falhar
# ---------------------------------------------------------------------------


def test_nenhuma_requisicao_recebe_o_indice_de_outra_arvore():
    """Invariante sob carga: todo mapa devolvido fala da arvore que foi pedida.

    Este teste NAO e a guarda do defeito de 2026-10-24, e a medicao diz por que: com a
    janela aberta, 240 tentativas nao reproduziram o entrelacamento, porque o intervalo
    entre a escrita da chave e o retorno tem duas instrucoes. A prova daquele defeito
    foi deterministica, por instrumentacao do dicionario, e esta guardada em
    `_reversa_refactor/busca-caminho/transformations/`, na pasta da transformacao.

    O que este teste guarda e o invariante mais grosso: o indice devolvido nunca pode
    ser o de outra arvore, nem por cache compartilhado, nem por mapa reaproveitado. Ele
    nunca falha no codigo correto, e falharia de forma grosseira se alguem voltasse a
    publicar um mapa unico para todas as arvores.
    """
    alfa = _arvore_de(*[f"Alfa {i}" for i in range(400)], prefixo="A")
    beta = _arvore_de(*[f"Beta {i}" for i in range(401)], prefixo="B")

    trocadas: list[list[str]] = []
    intervalo_original = sys.getswitchinterval()
    sys.setswitchinterval(0.000001)
    try:
        for _ in range(40):
            largada = threading.Barrier(3)

            def trabalho(arvore, marca: str) -> None:
                largada.wait(timeout=20)
                mapa = homonimos._indice_por_nome(arvore)
                if not all(marca in nome for nome in mapa):
                    trocadas.append(sorted(mapa)[:3])

            a = threading.Thread(target=trabalho, args=(alfa, "alfa"))
            b = threading.Thread(target=trabalho, args=(beta, "beta"))
            a.start()
            b.start()
            largada.wait(timeout=20)
            a.join(timeout=20)
            b.join(timeout=20)
    finally:
        sys.setswitchinterval(intervalo_original)

    assert trocadas == [], (
        f"{len(trocadas)} requisicoes receberam o indice de outra arvore: {trocadas[:3]}"
    )

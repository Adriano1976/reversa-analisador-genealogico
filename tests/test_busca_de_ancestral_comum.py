"""A busca de ancestral comum: o encontro tem de ser testado no DESCOBRIMENTO.

## Por que este arquivo existe

`find_ancestral_path` e uma BFS bidirecional que sobe por pais a partir das duas pessoas. Ate
2026-10-13 ela comparava o no recem-retirado da fila com a fronteira oposta, e **nunca** o pai
no instante em que era descoberto. Isso produz falso negativo quando os dois lados não tem a
mesma profundidade — que e o caso comum, e não a exceção.

O caso medido, no GEDCOM real `Arvore_Unificada_Oficial_V1_2.ged`: `Adriano Santos`
(`@I6f405a00@`) e `Therezinha Carvalho do Nascimento Souza` (`@Ied60620a@`) tem **5 ancestrais
comuns** (9 passos de um lado, 6 do outro). A fronteira da Therezinha esgota os 67 ancestrais
dela e esvazia na oitava iteração; a da raiz ainda expandia. O laco fazia `break` quando uma
fila esvaziava, e os quatro ancestrais comuns **ja estavam nos dois conjuntos de visitados**,
sem que ninguem comparasse as duas listas. A tela dizia "Parentesco documental não encontrado"
para um par com caminho de 16 nos.

## A forma que reproduz o defeito, e por que ela e esta

O defeito **nao** se reproduz com dois lados simetricos: se os dois sobem a mesma altura, o
lado que chega testa o encontro na saida da fila e acha. O que quebra e a **assimetria** — um
lado com ancestralidade FUNDA e outro RASO, que e o que os cinco casos reais tem (a raiz sobe
16 niveis; a pessoa do CSV, 6 ou 7).

Por isso a arvore sintetica daqui e uma cadeia de 10 niveis de um lado e uma de 6 do outro,
ligadas por um ancestral comum no topo. Medido: com o codigo antigo o resultado era `None`;
com a correcao, o caminho inteiro. O `test_deteccao_do_defeito` no fim do arquivo prova que a
arvore da fixture realmente exercita o caso, e nao um caso simetrico que passaria nos dois
codigos — sem ele, este arquivo poderia estar medindo a si mesmo.
"""
from __future__ import annotations

import os
import sys
import tempfile
from collections import deque

import pytest

_RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
for _caminho in (_RAIZ, os.path.join(_RAIZ, "src")):
    if _caminho not in sys.path:
        sys.path.insert(0, _caminho)

from core.documentary_relationship import documentary_relationship  # noqa: E402
from core.family_navigation import get_parents  # noqa: E402
from core.path_finding import find_ancestral_path  # noqa: E402
from parsers.gedcom_parser import carregar_arvore  # noqa: E402

#: O ancestral comum fica a FUNDO_P1 passos de `@IP1@` e a RASO_P2 passos de `@IP2@`.
FUNDO_P1 = 10
RASO_P2 = 4

#: Pessoas no ramo raso, alem do proprio `@IP2@`: uma por salto ate o ancestral comum.
#: E o numero que a construcao de fato produz, e nao um valor escolhido a parte — a
#: construcao abaixo tem uma familia por salto.
PESSOAS_NO_RAMO_RASO = RASO_P2

#: Nos no caminho: a cadeia funda, a rasa e o ancestral comum, contado uma vez so.
NOS_NO_CAMINHO = FUNDO_P1 + PESSOAS_NO_RAMO_RASO + 1

#: A forma do nome do no `i` da cadeia. `norm_name` come o sobrenome entre barras, entao o
#: nome exibido e "Ancestral Nivel 3".
def _nome(i: int) -> str:
    return f"Ancestral Nivel {i} /Teste/"


def _montar_gedcom() -> str:
    """Cadeia comum no topo, com dois ramos de profundidades diferentes.

    ```
    @IP1@ --(10 niveis)--> @IANC@ <--(6 niveis)-- @IP2@
    ```

    `@IANC@` e o ancestral comum. O ramo de `@IP2@` termina nele — o pai de `@IANC@` nao
    existe no arquivo —, e e isso que faz a fronteira daquele lado esvaziar antes de o lado
    fundo chegar.
    """
    linhas = [
        "0 HEAD",
        "1 SOUR teste",
        "1 GEDC",
        "2 VERS 5.5.1",
        "2 FORM LINEAGE-LINKED",
        "1 CHAR UTF-8",
    ]

    def individuo(xref: str, nome: str) -> None:
        linhas.extend([f"0 {xref} INDI", f"1 NAME {nome}", "1 SEX M"])

    def familia(xref: str, filho: str, pai: str) -> None:
        linhas.extend([f"0 {xref} FAM", f"1 CHIL {filho}", f"1 HUSB {pai}"])

    # Ramo fundo: P1 -> nivel 1 -> ... -> nivel FUNDO_P1, que E o ancestral comum.
    individuo("@IP1@", _nome(0))
    for nivel in range(1, FUNDO_P1 + 1):
        individuo(f"@IA{nivel}@", _nome(nivel))
    for nivel in range(1, FUNDO_P1 + 1):
        filho = "@IP1@" if nivel == 1 else f"@IA{nivel - 1}@"
        familia(f"@FA{nivel}@", filho, f"@IA{nivel}@")

    ancestral_comum = f"@IA{FUNDO_P1}@"

    # Ramo raso: P2 -> B1 -> ... -> ancestral comum, com UM salto por familia. O numero de
    # pessoas do ramo e derivado de RASO_P2, entao a profundidade nao pode divergir do
    # constante sem que a construcao mude junto.
    individuo("@IP2@", "Descendente Raso /Teste/")
    for nivel in range(1, PESSOAS_NO_RAMO_RASO):
        individuo(f"@IB{nivel}@", _nome(nivel))
    for nivel in range(1, PESSOAS_NO_RAMO_RASO + 1):
        filho = "@IP2@" if nivel == 1 else f"@IB{nivel - 1}@"
        pai = ancestral_comum if nivel == PESSOAS_NO_RAMO_RASO else f"@IB{nivel}@"
        familia(f"@FB{nivel}@", filho, pai)

    linhas.append("0 TRLR")
    return "\n".join(linhas) + "\n"


@pytest.fixture(scope="module")
def arvore():
    """A arvore sintetica, pelo parser de producao."""
    fd, caminho = tempfile.mkstemp(suffix=".ged")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as arquivo:
            arquivo.write(_montar_gedcom())
        yield carregar_arvore(caminho)
    finally:
        os.remove(caminho)


ANCESTRAL_COMUM = f"@IA{FUNDO_P1}@"


class TestOEncontroAssimetrico:
    """O caso que o defeito derrubava: um lado fundo, outro raso."""

    def test_acha_o_caminho_entre_os_dois_ramos(self, arvore):
        caminho, comum = find_ancestral_path(arvore, "@IP1@", "@IP2@")
        assert caminho is not None, (
            "a busca devolveu None para um par que tem ancestral comum no arquivo: e o falso "
            "negativo que a comparacao no descobrimento fecha"
        )
        assert comum == ANCESTRAL_COMUM, (
            f"o ancestral comum devolvido foi {comum!r}, e o arquivo diz {ANCESTRAL_COMUM!r}"
        )

    def test_o_caminho_comeca_e_termina_nas_duas_pessoas(self, arvore):
        caminho, _comum = find_ancestral_path(arvore, "@IP1@", "@IP2@")
        assert caminho[0] == "@IP1@", "o caminho tem de comecar na primeira pessoa"
        assert caminho[-1] == "@IP2@", "o caminho tem de terminar na segunda pessoa"

    def test_o_caminho_tem_o_tamanho_da_arvore(self, arvore):
        """As duas cadeias mais o ancestral comum, que aparece uma vez so."""
        caminho, _comum = find_ancestral_path(arvore, "@IP1@", "@IP2@")
        assert len(caminho) == NOS_NO_CAMINHO, (
            f"o caminho tem {len(caminho)} nos e a arvore tem {NOS_NO_CAMINHO}: {caminho}"
        )

    def test_o_caminho_e_continuo_por_pais(self, arvore):
        """Cada salto depois do ancestral comum e um pai-de, na ordem certa.

        Este e o teste que separa "achou um caminho" de "achou O caminho": uma concatenacao
        errada das duas metades passaria nos testes de tamanho e falharia aqui.
        """
        caminho, comum = find_ancestral_path(arvore, "@IP1@", "@IP2@")
        corte = caminho.index(comum)

        for filho, pai in zip(caminho[:corte], caminho[1:corte + 1]):
            assert pai in get_parents(arvore, filho), (
                f"{pai} nao e pai de {filho}: a metade que SOBE esta errada"
            )
        # Depois do ancestral comum o caminho DESCE: a relacao se inverte.
        for pai, filho in zip(caminho[corte:-1], caminho[corte + 1:]):
            assert pai in get_parents(arvore, filho), (
                f"{pai} nao e pai de {filho}: a metade que DESCE esta errada, e e justamente "
                "a concatenação das duas metades que este arquivo prende"
            )

    def test_o_mesmo_par_na_ordem_inversa_da_o_mesmo_conjunto(self, arvore):
        """A busca e simetrica: trocar as pontas nao pode perder o caminho."""
        ida, comum_ida = find_ancestral_path(arvore, "@IP1@", "@IP2@")
        volta, comum_volta = find_ancestral_path(arvore, "@IP2@", "@IP1@")
        assert ida is not None and volta is not None
        assert comum_ida == comum_volta == ANCESTRAL_COMUM
        assert set(ida) == set(volta), (
            "as duas ordens usaram caminhos diferentes; o caminho e o mesmo conjunto de pessoas"
        )


class TestOQueJaFuncionavaContinua:
    """A correcao e aditiva: nao pode mudar o que ja achava, nem achar o que nao existe."""

    def test_pessoas_identicas(self, arvore):
        caminho, comum = find_ancestral_path(arvore, "@IP1@", "@IP1@")
        assert caminho == ["@IP1@"]
        assert comum == "@IP1@"

    def test_ancestral_comum_ate_um_descendente_dele(self, arvore):
        """`@IP2@` esta ABAIXO do ancestral comum, e a busca sobe dos dois lados.

        Eu esperava `None` aqui, raciocinando que "subir por pais" nao ligaria quem esta
        abaixo. Esta errado, e o codigo (antigo e novo) mostrou: a busca sobe a partir de
        `@IP2@` e **chega** ao ancestral comum, entao o caminho existe e tem a direcao
        invertida — `common` e o mesmo no, e a metade depois dele desce.

        O nome do parametro ("common_ancestor") descreve o NO, e nao o sentido da travessia,
        e e isso que este teste passa a fixar.
        """
        caminho, comum = find_ancestral_path(arvore, ANCESTRAL_COMUM, "@IP2@")
        assert comum == ANCESTRAL_COMUM
        assert caminho is not None, (
            "quem esta abaixo do ancestral comum tambem alcanca o no subindo por pais"
        )
        assert caminho[0] == ANCESTRAL_COMUM and caminho[-1] == "@IP2@"
        assert len(caminho) == PESSOAS_NO_RAMO_RASO + 1, (
            f"o caminho tinha de ser a descida direta ({PESSOAS_NO_RAMO_RASO + 1} nos) e veio "
            f"{caminho}"
        )

    def test_pessoa_inexistente_nao_quebra(self, arvore):
        caminho, comum = find_ancestral_path(arvore, "@INAOEXISTE@", "@IP1@")
        assert caminho is None and comum is None

    def test_o_teto_de_iteracoes_continua_encerrando_a_busca(self, arvore):
        """`MAX_DEPTH` nao era o defeito, e continua valendo como teto.

        Com teto pequeno, um par que exige mais iteracoes do que o teto devolve `None` — e
        devolver `None` por teto e diferente de devolver `None` por fila vazia, que era o
        defeito.
        """
        caminho, _comum = find_ancestral_path(arvore, "@IP1@", "@IP2@", max_depth=3)
        assert caminho is None, "com teto de 3 iteracoes a busca nao pode alcancar o ancestral"


class TestOCaminhoChegaAoParentescoDocumental:
    """O consumidor real: sem caminho, a tela diz "não encontrado"."""

    def test_o_parentesco_e_encontrado(self, arvore):
        documental = documentary_relationship(arvore, "@IP1@", "@IP2@")
        assert documental["status"] == "found", (
            f"o parentesco ficou {documental['status']!r}: o caminho existe e nao pode ser "
            "descartado a montante"
        )
        assert documental["path"]["ids"], "o caminho voltou vazio"
        assert documental["common_ancestor"]["id"] == ANCESTRAL_COMUM

    def test_a_observacao_de_sem_caminho_nao_aparece(self, arvore):
        documental = documentary_relationship(arvore, "@IP1@", "@IP2@")
        codigos = {aviso["code"] for aviso in documental["warnings"]}
        assert "sem_caminho" not in codigos


class TestODefeitoEraRealmenteExercitado:
    """A prova de que a fixture reproduz a ASSIMETRIA, e nao um caso simetrico.

    Sem esta classe, a arvore do arquivo poderia ser simetrica — e uma arvore simetrica passa
    tanto no codigo antigo quanto no corrigido, o que faria todos os testes acima medirem
    nada. A prova e a mesma do defeito real: com a comparacao na SAIDA da fila (o codigo
    antigo), este par devolve `None`.
    """

    def _busca_do_codigo_antigo(self, arvore, start_id, end_id, max_depth=20):
        """Copia fiel do corpo anterior a correcao, para medir a fixture."""
        q1, q2 = deque([(start_id, [start_id])]), deque([(end_id, [end_id])])
        visited1, visited2 = {start_id: [start_id]}, {end_id: [end_id]}
        if start_id == end_id:
            return ([start_id], start_id)
        for _depth in range(max_depth):
            q_size = len(q1)
            if not q_size:
                break
            for _ in range(q_size):
                curr_id, path = q1.popleft()
                if curr_id in visited2:
                    return (path + visited2[curr_id][::-1][1:], curr_id)
                for p_id in get_parents(arvore, curr_id):
                    if p_id not in visited1:
                        visited1[p_id] = path + [p_id]
                        q1.append((p_id, path + [p_id]))
            q_size = len(q2)
            if not q_size:
                break
            for _ in range(q_size):
                curr_id, path = q2.popleft()
                if curr_id in visited1:
                    return (visited1[curr_id] + path[::-1][1:], curr_id)
                for p_id in get_parents(arvore, curr_id):
                    if p_id not in visited2:
                        visited2[p_id] = path + [p_id]
                        q2.append((p_id, path + [p_id]))
        return (None, None)

    def test_o_codigo_antigo_falhava_nesta_arvore(self, arvore):
        antigo, _ = self._busca_do_codigo_antigo(arvore, "@IP1@", "@IP2@")
        assert antigo is None, (
            "a arvore da fixture NAO reproduz o defeito: o codigo antigo acha o caminho nela. "
            "Provavelmente as duas cadeias ficaram simetricas, e entao os testes deste arquivo "
            "passariam nos dois codigos — medindo nada"
        )

    def test_o_codigo_novo_acha_nesta_arvore(self, arvore):
        novo, comum = find_ancestral_path(arvore, "@IP1@", "@IP2@")
        assert novo is not None and comum == ANCESTRAL_COMUM

    def test_os_dois_lados_tem_profundidades_diferentes(self, arvore):
        """A assimetria e o que cria o defeito; se ela sumir, o arquivo perde o sentido."""
        def profundidade(pid: str) -> int:
            niveis, fila, vistos = 0, [pid], {pid}
            while fila:
                atual = fila.pop()
                pais = get_parents(arvore, atual)
                if pais:
                    niveis += 1
                    for pai in pais:
                        if pai not in vistos:
                            vistos.add(pai)
                            fila.append(pai)
            return niveis

        fundo = profundidade("@IP1@")
        raso = profundidade("@IP2@")
        assert fundo > raso, (
            f"as duas cadeias tem a mesma profundidade ({fundo} e {raso}): a fixture deixou de "
            "reproduzir a assimetria do defeito real"
        )

"""Testes da Tarefa 03 — Busca de Caminho (TT-01 a TT-05).

Carrega um GEDCOM sintético em memória e exercita o fluxo de busca
direta (ancestral comum), fallback indireto (afinidade), pessoa
inexistente, sem conexão e pessoas idênticas.
"""
import os
import sys
import tempfile

import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "src"))

from tests.fixtures.sample_gedcom import SAMPLE_GED

from parsers import gedcom_parser
from core.family_navigation import find_person_by_name
from core.path_finding import find_ancestral_path, find_indirect_path
from core.path_search import path_search
from tests.fixtures.helpers import arvore_de as _arvore_de
from tests.fixtures.helpers import deps as _deps
from tests.fixtures.arvore_atual import atual, guardar
from utils.validate import chave_de_armazenamento


@pytest.fixture(scope="module")
def loaded_tree():
    """Carrega o GEDCOM sintético uma única vez para toda a suíte.

    Devolve a ARVORE na forma que o nucleo passou a receber por parametro
    (feature 005, `T011`/`T012`): `(people, families, graph, child_to_family)`.
    A fixture antes devolvia o modulo de estado; as asserções nao mudaram.
    """
    fd, path = tempfile.mkstemp(suffix=".ged")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            f.write(SAMPLE_GED)
        # O parse DEVOLVE a arvore (feature 005). Antes devolvia so os nomes e
        # escrevia as globais de lado; por isso a fixture lia `gedcom_state`.
        # `guardar` registra a MESMA arvore que a suite usa, para o recurso de
        # transicao do helper (que recorre as globais) nunca ser acionado — ele
        # mistura a arvore de outro arquivo de teste.
        return guardar(gedcom_parser.carregar_arvore(path))
    finally:
        os.remove(path)


def test_person_lookup(loaded_tree):
    assert find_person_by_name(loaded_tree, "Carlos Silva") == ["@I3@"]
    assert "@I4@" in find_person_by_name(loaded_tree, "Ana Silva")
    assert find_person_by_name(loaded_tree, "Zzz Ninguém") == []


def test_direct_connection_trivial(loaded_tree):
    path, common = find_ancestral_path(loaded_tree, "@I3@", "@I3@")
    assert path == ["@I3@"]
    assert common == "@I3@"


def test_direct_connection_common_ancestor(loaded_tree):
    # TT-01: Carlos (I3) e Ana (I4) compartilham I1/I2.
    path, common = find_ancestral_path(loaded_tree, "@I3@", "@I4@")
    assert path is not None
    assert common in ("@I1@", "@I2@")


def test_path_search_direct(loaded_tree):
    result, msg, success = path_search("Carlos Silva", "Ana Silva", _deps(), atual())
    assert success is True
    assert msg == "Conexão direta encontrada (ancestral comum)."
    assert "Carlos Silva" in result["text_path"]
    assert "Ana Silva" in result["text_path"]
    assert result["mermaid_data"].startswith("flowchart BT")


def test_indirect_connection_via_marriage(loaded_tree):
    # TT-02: Carlos (I3) e Bia (I5) são casados (F2).
    result, msg, success = path_search("Carlos Silva", "Bia Oliveira", _deps(), atual())
    assert success is True
    assert msg == "Conexão indireta encontrada (via casamento/afinidade)."
    assert "Bia Oliveira" in result["text_path"]


def test_indirect_path_function(loaded_tree):
    person_path = find_indirect_path(loaded_tree, "@I3@", "@I5@", max_hops=40)
    assert person_path is not None
    assert "@I3@" in person_path
    assert "@I5@" in person_path


def test_person_not_found(loaded_tree):
    # TT-03: mensagem específica por pessoa.
    result, msg, success = path_search("Zzz Ninguém", "Carlos Silva", _deps(), atual())
    assert success is False
    assert "Pessoa 1 'Zzz Ninguém' não encontrada." == msg

    result, msg, success = path_search("Carlos Silva", "Zzz Ninguém", _deps(), atual())
    assert success is False
    assert "Pessoa 2 'Zzz Ninguém' não encontrada." == msg


def test_no_connection(loaded_tree):
    # TT-04: Lone Ranger não tem famílias; sem conexão com ninguém.
    result, msg, success = path_search("Carlos Silva", "Lone Ranger", _deps(), atual())
    assert success is True
    assert "Nenhuma conexão encontrada" in msg
    assert result is None


def test_identical_persons(loaded_tree):
    # TT-05: pessoas idênticas -> caminho trivial.
    result, msg, success = path_search("Carlos Silva", "Carlos Silva", _deps(), atual())
    assert success is True
    assert msg == "Conexão direta encontrada (ancestral comum)."
    assert result["text_path"] == "Carlos Silva"


class TestEscolherArvoreDaLista:
    """T010 (feature `011-escolher-arquivo-da-lista`) — a rota, escolhendo a arvore da lista.

    ## Por que esta classe mora AQUI, e o descompasso que isso cria

    Este arquivo mede o **nucleo** (`path_search`, `find_ancestral_path`), com arvore em memoria e sem
    HTTP; o docstring dele diz exatamente isso. A `T010` do plano fixou este arquivo como alvo, e a
    classe entra separada por isso. O leitor deve saber que a partir daqui o arquivo tem **dois
    assuntos**: acima, o nucleo puro; abaixo, a rota. Registrado como observacao na conclusao da
    feature, e nao corrigido em silencio.

    ## O que ela mede

    - `RF-02`: escolher a arvore na lista e submeter a busca **sem novo envio de arquivo**. O caminho
      antigo dependia de um envio anterior, que devolvia a referencia; aqui a referencia e escrita
      direto na pasta, que e o estado que a lista produz.
    - `D-08` + `RN-11`: forcar o uso de um item **indisponivel** (nome visivel com acento, que a forma
      fechada do resolvedor nao admite) e recusado **com mensagem, sem `500` e sem arvore carregada**,
      e o arquivo **continua na lista**.

    ## O que ela NAO faz, de proposito

    Nao fixa o literal da mensagem do caso negativo: o texto que o sistema devolve hoje e
    `Erro: Arquivo '...' nao existe mais.`, medido e **falso** para esse caso. O defeito de raiz esta
    registrado como `BUG-20261009-6RKP`, e um teste que congelasse esse literal transformaria o defeito
    em contrato. E nao monta arquivo sintetico de nome ASCII com conteudo invalido: esse caminho
    derruba a requisicao com `500` (`A008` da auditoria) e **nao** e o caso real.
    """

    @staticmethod
    def _guardar(pasta: str, nome: str, conteudo: str) -> str:
        with open(os.path.join(pasta, nome), "wb") as fh:
            fh.write(conteudo.encode("utf-8"))
        return nome

    def test_busca_conclui_com_a_arvore_escolhida_sem_envio_previo(self, cliente_de_upload):
        """`RF-02`: a referencia escolhida na lista basta. Nenhum `upload_gedcom` antes."""
        _app, cliente, pasta = cliente_de_upload
        chave = chave_de_armazenamento(SAMPLE_GED.encode("utf-8"))
        armazenado = self._guardar(pasta, f"{chave}__arvore.ged", SAMPLE_GED)

        resposta = cliente.post("/", data={
            "action": "path_search",
            "gedcom_filename": armazenado,
            "person1_name": "Carlos Silva",
            "person2_name": "Ana Silva",
        })

        corpo = resposta.get_data(as_text=True)
        assert resposta.status_code == 200
        assert "Conexão direta encontrada (ancestral comum)." in corpo, (
            "a busca nao concluiu com a arvore escolhida na lista: o caminho antigo exigia um envio "
            "previo, e a lista existe para tirar essa exigencia (RF-02)"
        )

    def test_item_indisponivel_e_recusado_sem_500_e_sem_carregar_arvore(self, cliente_de_upload):
        """`D-08`, `RN-11`: a recusa acontece no USO, com mensagem, e a tela continua utilizavel.

        O arquivo tem os 16 hexadecimais no inicio do nome, entao ele passa no prefixo; o que a forma
        fechada recusa e o **acento** no nome visivel. E o caso real medido, so que construido em pasta
        temporaria, porque a mitigacao de 2026-10-09 tirou os acentos da pasta de verdade.
        """
        _app, cliente, pasta = cliente_de_upload
        chave = chave_de_armazenamento(SAMPLE_GED.encode("utf-8"))
        armazenado = self._guardar(pasta, f"{chave}__Famílias.ged", SAMPLE_GED)

        resposta = cliente.post("/", data={
            "action": "path_search",
            "gedcom_filename": armazenado,
            "person1_name": "Carlos Silva",
            "person2_name": "Ana Silva",
        })
        corpo = resposta.get_data(as_text=True)

        assert resposta.status_code == 200, (
            "a recusa virou erro do servidor: uma referencia que nao resolve tem de continuar sendo "
            "mensagem na tela, e nao 500"
        )
        assert "Conexão direta encontrada" not in corpo, "uma arvore foi carregada apesar da recusa"
        assert corpo.strip(), "a recusa nao deixou mensagem nenhuma para o operador"
        assert os.path.isfile(os.path.join(pasta, armazenado)), (
            "o arquivo foi removido ou escondido: a lista nao filtra e nao altera a pasta (D-08, RF-08)"
        )

    def test_o_mesmo_item_continua_utilizavel_se_o_nome_nao_tiver_acento(self, cliente_de_upload):
        """O par do teste acima: sem o acento, o MESMO conteudo resolve.

        Sem este par, o teste anterior poderia estar passando por a busca estar quebrada para todo
        mundo, e nao por o item estar indisponivel.
        """
        _app, cliente, pasta = cliente_de_upload
        chave = chave_de_armazenamento(SAMPLE_GED.encode("utf-8"))
        armazenado = self._guardar(pasta, f"{chave}__Familias.ged", SAMPLE_GED)

        resposta = cliente.post("/", data={
            "action": "path_search",
            "gedcom_filename": armazenado,
            "person1_name": "Carlos Silva",
            "person2_name": "Ana Silva",
        })

        assert "Conexão direta encontrada (ancestral comum)." in resposta.get_data(as_text=True)

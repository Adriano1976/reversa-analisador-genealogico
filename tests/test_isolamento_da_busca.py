"""O portao do isolamento na busca (feature 052).

## O que este arquivo prende

- a busca de um dono nunca enxerga o acervo de outro, mesmo com a MESMA referencia
  apresentada;
- a recusa e `404` com o literal de inexistencia, nunca `403`, e o corpo nao carrega
  nome nenhum de quem nao e dono (`RN-06` da feature 051);
- a ausencia de candidatos nao vira erro: vira secao que nao resolve, e a rota traduz.

## Por que o teste e unitario no servico e na rota

O caminho de dois donos de verdade exige a entrada pelo provedor (feature 051). A
parte que a busca acrescenta — "a fonte resolve por dono" — se prova com um carregador
escopado, e a parte que a rota acrescenta — "nao resolve vira 404" — se prova na rota.
"""
from __future__ import annotations

import os
import sys

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
for _caminho in (RAIZ, os.path.join(RAIZ, "src")):
    if _caminho not in sys.path:
        sys.path.insert(0, _caminho)

from application.busca_de_nome import ServicoDeBusca  # noqa: E402
from fixtures.busca_arvores import GED_DA_BUSCA  # noqa: E402
from parsers.gedcom_parser import carregar_arvore  # noqa: E402
from ports.fontes_de_nomes import NomesDaArvoreGedcom  # noqa: E402

CHAVE = "080e7943572d2652"


class CarregadorEscopado:
    """Carregador de mentira: devolve a arvore so para o dono que a possui."""

    def __init__(self, dono: str, arvore) -> None:
        self._dono = dono
        self._arvore = arvore

    def carregar(self, referencia: str, dono: str):
        return self._arvore if dono == self._dono else None


def _arvore(tmp_path):
    caminho = tmp_path / "arvore.ged"
    caminho.write_text(GED_DA_BUSCA, encoding="utf-8")
    return carregar_arvore(str(caminho))


class TestOServicoNaoCruzaDonos:
    def test_o_dono_ve_o_proprio_acervo(self, tmp_path):
        servico = ServicoDeBusca((NomesDaArvoreGedcom(CarregadorEscopado("a", _arvore(tmp_path))),))

        resultado = servico.buscar("Silva", dono="a", referencias={"arvore": "ref"})

        assert resultado.encontrou
        assert not resultado.nao_resolveu

    def test_o_outro_dono_nao_resolve(self, tmp_path):
        servico = ServicoDeBusca((NomesDaArvoreGedcom(CarregadorEscopado("a", _arvore(tmp_path))),))

        resultado = servico.buscar("Silva", dono="b", referencias={"arvore": "ref"})

        assert resultado.nao_resolveu
        assert not resultado.encontrou
        assert all(not secao.acertos for secao in resultado.secoes)


class TestARotaNaoVaza:
    def test_o_corpo_do_404_nao_cita_nome_de_ninguem(self, cliente_de_upload, tmp_path):
        _app, cliente, _pasta = cliente_de_upload
        servico = ServicoDeBusca(
            (NomesDaArvoreGedcom(CarregadorEscopado("outro-dono", _arvore(tmp_path))),)
        )
        _app.extensions["busca"] = servico

        resposta = cliente.post(
            "/busca", data={"termo": "Silva", "gedcom_filename": f"{CHAVE}__arvore.ged"}
        )
        corpo = resposta.get_data(as_text=True)

        assert resposta.status_code == 404
        assert "Ana Silva" not in corpo
        assert "403" not in corpo

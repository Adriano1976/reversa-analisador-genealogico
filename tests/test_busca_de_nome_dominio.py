"""O nucleo da busca: termo, estrategias e ordem total (feature 052).

## O que este arquivo prende

- o termo deriva tokens e escopo da CONTAGEM, e nunca de um controle de tela;
- o acento e a caixa nao mudam o resultado (mesma autoridade do dossie);
- o prefixo pontua acima do meio de token (`RN-09`) — filtro largo, ordem que separa;
- a ordem e TOTAL: duas buscas iguais devolvem a mesma sequencia, e o empate cai no
  nome normalizado e depois no identificador (`RN-04`);
- o limite trunca a lista e NUNCA mente no total (`RN-07`).

## O que ele nao prende

A normalizacao de cada fonte — isso e da fonte, e tem teste proprio em
`test_busca_de_nome_fontes.py`.
"""
from __future__ import annotations

import os
import sys

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
for _caminho in (RAIZ, os.path.join(RAIZ, "src")):
    if _caminho not in sys.path:
        sys.path.insert(0, _caminho)

from core.busca_de_nome import (  # noqa: E402
    CasamentoCompleto,
    CasamentoExato,
    CasamentoPorPrefixo,
    CasamentoPorTrecho,
    BuscadorDeNomes,
    NomeParaBuscar,
    TermoDeBusca,
)
from core.homonimos import normalizar  # noqa: E402


def candidato(nome: str, identificador: str | None = None) -> NomeParaBuscar:
    forma = normalizar(nome)
    return NomeParaBuscar(
        identificador=identificador or f"@{forma.replace(' ', '-')}@",
        nome=nome,
        normalizado=forma,
        tokens=tuple(dict.fromkeys(forma.split())),
        origem="arvore",
    )


class TestOTermo:
    def test_um_token_e_escopo_de_token(self):
        termo = TermoDeBusca.de("Silva", normalizar)

        assert termo.tokens == ("silva",)
        assert termo.escopo == "token"

    def test_dois_tokens_e_escopo_de_nome(self):
        termo = TermoDeBusca.de("Maria Silva", normalizar)

        assert termo.tokens == ("maria", "silva")
        assert termo.escopo == "nome"

    def test_acento_e_caixa_nao_mudam_a_forma(self):
        assert TermoDeBusca.de("JOSÉ", normalizar).normalizado == normalizar("jose")

    def test_o_texto_digitado_e_preservado(self):
        """`RF-09`: o que volta para o campo e o que o operador escreveu."""
        termo = TermoDeBusca.de("  José da Silva  ", normalizar)

        assert termo.texto == "  José da Silva  "

    def test_termo_em_branco_e_vazio(self):
        assert TermoDeBusca.de("   ", normalizar).vazio


class TestAsEstrategias:
    def test_exato_so_casa_o_nome_inteiro(self):
        estrategia = CasamentoExato()

        assert estrategia.pontuar("ana silva", ("ana", "silva"), TermoDeBusca.de("Ana Silva", normalizar)) == 1.0
        assert estrategia.pontuar("ana silva souza", ("ana", "silva", "souza"), TermoDeBusca.de("Ana Silva", normalizar)) is None

    def test_completo_exige_todos_os_tokens(self):
        estrategia = CasamentoCompleto()
        termo = TermoDeBusca.de("Maria Silva", normalizar)

        assert estrategia.pontuar("silva maria", ("silva", "maria"), termo) is not None
        assert estrategia.pontuar("maria souza", ("maria", "souza"), termo) is None

    def test_prefixo_exige_o_inicio_do_token(self):
        estrategia = CasamentoPorPrefixo()
        termo = TermoDeBusca.de("sil", normalizar)

        assert estrategia.pontuar("maria silva", ("maria", "silva"), termo) is not None
        assert estrategia.pontuar("maria tosilva", ("maria", "tosilva"), termo) is None

    def test_trecho_casa_no_meio_do_token(self):
        estrategia = CasamentoPorTrecho()
        termo = TermoDeBusca.de("ilva", normalizar)

        assert estrategia.pontuar("maria silva", ("maria", "silva"), termo) is not None

    def test_o_prefixo_pontua_acima_do_trecho(self):
        """`RN-09`: o filtro e largo, e a ORDEM separa qualidade de ruido."""
        buscador = BuscadorDeNomes()
        termo = TermoDeBusca.de("silva", normalizar)
        candidatos = [
            candidato("Maria Tosilva"),
            candidato("Maria Silva"),
            candidato("Ana Silva"),
        ]

        acertos, total = buscador.acertos(candidatos, termo)

        assert total == 3
        assert acertos[0].pontuacao > acertos[-1].pontuacao
        assert {a.nome for a in acertos} == {"Maria Silva", "Ana Silva", "Maria Tosilva"}


class TestAOrdem:
    def test_a_ordem_e_estavel_entre_duas_buscas(self):
        buscador = BuscadorDeNomes()
        termo = TermoDeBusca.de("silva", normalizar)
        candidatos = [candidato("Ana Silva"), candidato("Carlos Silva"), candidato("Bia Silva")]

        primeira = [a.identificador for a in buscador.acertos(candidatos, termo)[0]]
        segunda = [a.identificador for a in buscador.acertos(list(reversed(candidatos)), termo)[0]]

        assert primeira == segunda

    def test_o_empate_cai_no_nome_e_no_identificador(self):
        buscador = BuscadorDeNomes()
        termo = TermoDeBusca.de("silva", normalizar)
        # Mesmo nome normalizado: o desempate tem de ser o identificador.
        candidatos = [candidato("Ana Silva", "b"), candidato("Ana Silva", "a")]

        acertos, _ = buscador.acertos(candidatos, termo)

        assert [a.identificador for a in acertos] == ["a", "b"]

    def test_o_limite_trunca_e_o_total_permanece(self):
        buscador = BuscadorDeNomes()
        termo = TermoDeBusca.de("silva", normalizar)
        candidatos = [candidato(f"Pessoa {n} Silva", str(n)) for n in range(10)]

        acertos, total = buscador.acertos(candidatos, termo, limite=3)

        assert len(acertos) == 3
        assert total == 10

    def test_termo_vazio_nao_devolve_nada(self):
        buscador = BuscadorDeNomes()

        acertos, total = buscador.acertos([candidato("Ana Silva")], TermoDeBusca.de("", normalizar))

        assert acertos == ()
        assert total == 0

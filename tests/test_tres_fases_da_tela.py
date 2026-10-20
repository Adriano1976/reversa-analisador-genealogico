"""As tres fases da tela de entrada (feature 037).

## O que este arquivo prende

- A navegacao passa a ser uma **barra lateral com tres fases**, e nao duas fileiras de abas.
- O conteudo de cada fase: a lista e o envio na fase 1; os dois campos na fase 2; o CSV e o
  nome na fase 3.
- As fases 2 e 3 **nao oferecem campo** sem arvore aberta, e dizem onde a arvore se abre.
- A fase ativa e decidida pelo servidor: fase 1 sem arvore, fase 2 com arvore aberta.
- Os contadores da fase 1 sao calculados da propria lista.
- Os literais congelados continuam identicos.

## O que ele NAO prende

Comportamento executado no navegador (abrir/fechar a lista do combobox, foco, teclado). O
projeto nao tem navegador headless nem executor de JS; essa fronteira esta declarada no
`roadmap.md` (`D-14`) e o checklist manual mora no `onboarding.md`.
"""
from __future__ import annotations

import os
import re
import sys

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
for _caminho in (RAIZ, os.path.join(RAIZ, "src"), os.path.join(RAIZ, "tests")):
    if _caminho not in sys.path:
        sys.path.insert(0, _caminho)

from fixtures.sample_gedcom import SAMPLE_GED  # noqa: E402

GEDCOM = SAMPLE_GED.encode("utf-8")

# Chave de conteudo valida (16 hexadecimais), a mesma usada em tests/test_tabela_da_tela.py.
CHAVE_A = "080e7943572d2652"
ARVORE = f"{CHAVE_A}__arvore.ged"

# Rotulos que a reorganizacao NAO pode renomear.
LITERAIS = [
    "Buscar Conexão no GEDCOM",
    "Analisador de DNA",
    "Árvores GEDCOM",
    "Enviar nova árvore",
    "Pessoa 1",
    "Pessoa 2",
    "Encontrar Conexão",
    "1. Lista de Matches (CSV)",
    "2. Seu Nome (como está no GEDCOM)",
    "Analisar Matches de DNA",
]

# Marcas que delimitam o fim de um painel quando ele nao e seguido por outro painel.
_FIM_DO_BLOCO = ('id="lista-de-nomes"', 'id="nomes-da-arvore"', 'id="loading"')


def _guardar(pasta: str, nome: str, conteudo: bytes = GEDCOM) -> str:
    caminho = os.path.join(pasta, nome)
    with open(caminho, "wb") as fh:
        fh.write(conteudo)
    return caminho


def _corpo(cliente) -> str:
    return cliente.get("/").get_data(as_text=True)


def _abrir_arvore(cliente_de_upload, nome: str = ARVORE) -> str:
    """Grava o GEDCOM na pasta e o abre pelo caminho real da tela (`selecionar_arvore`).

    Abrir de verdade, e nao so gravar o arquivo, e o que produz o estado com `gedcom_filename`
    — e e nesse estado que as fases 2 e 3 existem.
    """
    _app, cliente, pasta = cliente_de_upload
    _guardar(pasta, nome)
    resposta = cliente.post("/", data={"action": "selecionar_arvore", "gedcom_filename": nome})
    assert resposta.status_code == 200, f"abrir a arvore respondeu {resposta.status_code}"
    return resposta.get_data(as_text=True)


def _painel(corpo: str, numero: int) -> str:
    """O trecho do documento que pertence ao painel `fase-<numero>`."""
    inicio = corpo.index(f'id="fase-{numero}"')
    fim = len(corpo)
    for marca in (f'id="fase-{numero + 1}"',) + _FIM_DO_BLOCO:
        achado = corpo.find(marca, inicio + 1)
        if achado != -1:
            fim = min(fim, achado)
    return corpo[inicio:fim]


def _abertura(corpo: str, numero: int) -> str:
    """A tag de abertura do painel, do `<section` ate o primeiro `>`."""
    inicio = corpo.index(f'id="fase-{numero}"')
    comeco = corpo.rindex("<section", 0, inicio)
    return corpo[comeco:corpo.index(">", inicio)]


def _botao(corpo: str, numero: int) -> str:
    inicio = corpo.index(f'id="fase-{numero}-botao"')
    comeco = corpo.rindex("<button", 0, inicio)
    return corpo[comeco:corpo.index("</button>", inicio)]


class TestNavegacaoEmTresFases:
    def test_a_tela_tem_uma_barra_com_tres_fases(self, cliente_de_upload):
        _app, cliente, _pasta = cliente_de_upload

        corpo = _corpo(cliente)

        # Dois controles, um destino so: a barra lateral e as abas (`E006`).
        assert corpo.count('role="tablist"') == 2, "esperava a barra lateral e a fileira de abas"
        assert corpo.count('role="tabpanel"') == 3, "esperava tres paineis"
        for numero in (1, 2, 3):
            assert f'id="fase-{numero}"' in corpo, f"o painel da fase {numero} sumiu"
            assert f'id="fase-{numero}-botao"' in corpo, f"o botao da fase {numero} sumiu"
            assert f'id="aba-fase-{numero}"' in corpo, f"a aba da fase {numero} sumiu"

    def test_as_fases_tem_dois_controles_para_o_mesmo_painel(self, cliente_de_upload):
        """`E006`: a barra lateral e as abas apontam para os mesmos tres paineis.

        O risco de controle duplicado e o estado: sem a sincronia do script, os dois ficariam
        `aria-selected="true"` ao mesmo tempo. Aqui se prende o PAR de controles por fase.
        """
        _app, cliente, _pasta = cliente_de_upload

        corpo = _corpo(cliente)

        # O espaco depois do atributo separa a marcacao do `[role="tab"]` que vive no script.
        assert corpo.count('role="tab" ') == 6, "esperava dois controles por fase"
        for numero in (1, 2, 3):
            achados = re.findall(rf'role="tab"[^>]*data-bs-target="#fase-{numero}"', corpo)
            assert len(achados) == 2, f"a fase {numero} nao tem exatamente dois controles"

    def test_sem_arvore_a_fase_1_esta_ativa(self, cliente_de_upload):
        _app, cliente, _pasta = cliente_de_upload

        corpo = _corpo(cliente)

        assert 'aria-selected="true"' in _botao(corpo, 1)
        assert "active" in _abertura(corpo, 1), "a fase 1 nao nasceu ativa"
        assert "active" not in _abertura(corpo, 2)
        assert "active" not in _abertura(corpo, 3)

    def test_com_arvore_a_fase_2_esta_ativa(self, cliente_de_upload):
        corpo = _abrir_arvore(cliente_de_upload)

        assert 'aria-selected="true"' in _botao(corpo, 2), "a fase 2 devia abrir ativa"
        assert "active" in _abertura(corpo, 2)
        assert "active" not in _abertura(corpo, 1), "a fase 1 e a lista, nao o destino do envio"


class TestConteudoDasFases:
    def test_a_fase_1_tem_a_lista_e_o_envio_sem_arvore(self, cliente_de_upload):
        _app, cliente, _pasta = cliente_de_upload

        painel = _painel(_corpo(cliente), 1)

        assert 'value="upload_gedcom"' in painel, "o envio saiu da fase 1"
        assert "Nenhuma árvore armazenada ainda" in painel, "o estado vazio da lista sumiu"
        assert "<table" not in painel, "a tabela aparece sem nenhum arquivo"

    def test_a_fase_1_tem_a_lista_e_o_envio_com_arvore(self, cliente_de_upload):
        corpo = _abrir_arvore(cliente_de_upload)

        painel = _painel(corpo, 1)

        assert "<table" in painel, "a tabela saiu da fase 1"
        assert 'value="selecionar_arvore"' in painel
        assert 'value="upload_gedcom"' in painel, "o envio saiu da fase 1 com arvore aberta"

    def test_a_fase_2_tem_so_os_dois_campos(self, cliente_de_upload):
        painel = _painel(_abrir_arvore(cliente_de_upload), 2)

        assert 'name="person1_name"' in painel
        assert 'name="person2_name"' in painel
        assert "Encontrar Conexão" in painel
        assert 'type="file"' not in painel, "a fase 2 nao envia arquivo"

    def test_a_fase_3_tem_o_csv_e_o_nome(self, cliente_de_upload):
        painel = _painel(_abrir_arvore(cliente_de_upload), 3)

        assert 'name="matches_csv"' in painel
        assert 'name="root_name"' in painel
        assert "Analisar Matches de DNA" in painel


class TestEstadosVazios:
    def test_as_fases_2_e_3_nao_oferecem_campo_sem_arvore(self, cliente_de_upload):
        _app, cliente, _pasta = cliente_de_upload

        corpo = _corpo(cliente)

        for numero in (2, 3):
            painel = _painel(corpo, numero)
            assert 'name="person1_name"' not in painel, f"a fase {numero} ofereceu campo sem arvore"
            assert 'name="root_name"' not in painel, f"a fase {numero} ofereceu campo sem arvore"
            assert 'type="file"' not in painel, f"a fase {numero} ofereceu upload sem arvore"
            assert "<select" not in painel, f"a fase {numero} ofereceu selecao sem arvore"

    def test_o_estado_vazio_aponta_para_a_fase_1(self, cliente_de_upload):
        _app, cliente, _pasta = cliente_de_upload

        corpo = _corpo(cliente)

        for numero in (2, 3):
            painel = _painel(corpo, numero)
            assert re.search(r"fase 1", painel, re.I), (
                f"a fase {numero} nao diz que a arvore se abre na fase 1"
            )


class TestContadoresDaFase1:
    def test_os_contadores_contam_o_que_existe(self, cliente_de_upload):
        _app, cliente, pasta = cliente_de_upload
        _guardar(pasta, ARVORE)
        _guardar(pasta, "arvore_sem_chave.ged")

        corpo = _corpo(cliente)

        blocos = re.findall(r'<div class="contador">(.*?)</div>', corpo, re.S)
        assert len(blocos) == 2, "esperava exatamente dois contadores"
        numeros = [re.search(r"<strong>(\d+)</strong>", bloco).group(1) for bloco in blocos]
        assert numeros == ["2", "1"], f"contadores {numeros}, esperado total 2 e disponiveis 1"

    def test_sem_arvore_nao_ha_contador(self, cliente_de_upload):
        _app, cliente, _pasta = cliente_de_upload

        assert 'class="contador"' not in _corpo(cliente)


class TestCaixaDeStatus:
    def test_a_fase_1_nomeia_a_arvore_aberta_e_oferece_trocar(self, cliente_de_upload):
        painel = _painel(_abrir_arvore(cliente_de_upload), 1)

        assert "Árvore atualmente aberta" in painel, "a caixa de status da fase 1 sumiu"
        assert "escolher outra árvore" in painel, "o caminho de troca de arvore sumiu"

    def test_a_linha_de_arvore_aberta_saiu_de_cima_das_fases(self, cliente_de_upload):
        corpo = _abrir_arvore(cliente_de_upload)
        antes_da_barra = corpo[:corpo.index('role="tablist"')]

        assert "Árvore aberta:" not in antes_da_barra, (
            "a linha antiga continua acima das fases, duplicando a caixa de status"
        )

    def test_a_fase_2_nomeia_a_arvore_da_consulta(self, cliente_de_upload):
        painel = _painel(_abrir_arvore(cliente_de_upload), 2)

        assert "Consulta baseada em" in painel
        assert "Trocar árvore ativa" in painel


class TestLiteraisPreservados:
    def test_os_rotulos_congelados_continuam(self, cliente_de_upload):
        corpo = _abrir_arvore(cliente_de_upload)

        for literal in LITERAIS:
            assert literal in corpo, f"o rotulo {literal!r} sumiu da tela"

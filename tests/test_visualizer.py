"""Testes do texto DOT e das recusas do renderizador.

Nenhum teste deste arquivo precisa do Graphviz: o desenho é verificado por igualdade de
texto. A chamada real ao binário fica em `test_visualizer_render.py`, com `skipif`.
"""
from __future__ import annotations

import builtins
import os
import sys

import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "src"))

from reporting import visualizer as vz  # noqa: E402
from tests.fixtures import sugestao_para_desenho as fixo  # noqa: E402


def _linha_do_no(texto: str, no_id: str) -> str:
    alvo = f'"{no_id}" ['
    for linha in texto.splitlines():
        if linha.strip().startswith(alvo):
            return linha
    return ""


def _arestas(texto: str) -> list:
    return [linha.strip() for linha in texto.splitlines() if "->" in linha]


def _texto(**kwargs):
    return vz.texto_dot(fixo.sugestao(), fixo.resultado(**kwargs), fixo.documental())


# ---------------------------------------------------------------------------
# Estrutura e cores
# ---------------------------------------------------------------------------

def test_cabecalho_e_hierarquico_vertical():
    texto = _texto()

    assert texto.startswith("digraph arvore_sugerida {")
    assert "rankdir=TB;" in texto
    assert 'bgcolor="white";' in texto
    assert texto.rstrip().endswith("}")


def test_no_base_recebe_verde():
    linha = _linha_do_no(_texto(), fixo.DOADOR_ID)

    assert 'fillcolor="#a8e6cf"' in linha
    assert 'label="Doador Sintetico"' in linha


def test_no_documental_recebe_cinza_com_borda():
    linha = _linha_do_no(_texto(), fixo.PAI_ID)

    assert 'fillcolor="#f5f5f5"' in linha
    assert 'color="#666666"' in linha


def test_no_virtual_recebe_amarelo_e_rotulo_de_geracao():
    texto = _texto()
    linha = _linha_do_no(texto, fixo.VIRTUAL_1)

    assert 'fillcolor="#ffd3b6"' in linha
    assert 'label="Geração 1"' in linha
    assert "dashed" in linha


# ---------------------------------------------------------------------------
# Aresta rompida e cadeia sugerida
# ---------------------------------------------------------------------------

def test_aresta_rompida_e_tracejada_vermelha_e_rotulada():
    texto = _texto()
    alvo = f'"{fixo.ANCESTRAL_ID}" -> "{fixo.PAI_ID}"'
    linha = next(item for item in _arestas(texto) if item.startswith(alvo))

    assert "style=dashed" in linha
    assert "color=red" in linha
    assert f'label="{vz.ROTULO_QUEBRA}"' in linha


def test_cadeia_sugerida_liga_ancestral_ao_filho_por_dentro_das_geracoes():
    texto = _texto()

    assert f'"{fixo.ANCESTRAL_ID}" -> "{fixo.VIRTUAL_1}"' in texto
    assert f'"{fixo.VIRTUAL_1}" -> "{fixo.VIRTUAL_2}"' in texto
    assert f'"{fixo.VIRTUAL_2}" -> "{fixo.PAI_ID}"' in texto


def test_o_salto_rompido_nao_aparece_como_filiacao_comum():
    texto = _texto()
    alvo = f'"{fixo.ANCESTRAL_ID}" -> "{fixo.PAI_ID}"'
    filiacao = [item for item in _arestas(texto)
                if item.startswith(alvo) and 'color="#555555"' in item]

    assert filiacao == []


# ---------------------------------------------------------------------------
# Caixa de evidência
# ---------------------------------------------------------------------------

def test_caixa_de_evidencia_com_cm_e_geracoes():
    texto = _texto()

    assert "21.6 cM, 5.7 gerações - Incompatibilidade Biológica" in texto
    assert vz.TITULO_EVIDENCIA in texto
    assert f'"{vz.NO_EVIDENCIA}" -> "{fixo.DOADOR_ID}" [style=invis]' in texto


def test_caixa_sem_dado_usa_travessao_e_nao_inventa_numero():
    texto = vz.texto_dot(fixo.sugestao(), fixo.resultado(cm=None, geracoes=None),
                         fixo.documental())

    assert "— cM, — gerações" in texto


@pytest.mark.parametrize("codigo,esperado", [
    ("PROFUNDIDADE_TEMPORAL_INCOMPATIVEL", "Incompatibilidade Biológica"),
    ("GENITOR_FORA_DA_JANELA_BIOLOGICA", "Idade de genitor impossível"),
    ("CONFLITO_CM_DOCUMENTAL", "Conflito entre cM e documento"),
    ("CODIGO_QUE_NAO_EXISTE", "Quebra de linha documental"),
])
def test_veredito_por_codigo_critico(codigo, esperado):
    assert vz.veredito(fixo.resultado(codigo=codigo)) == esperado


def test_veredito_ignora_codigo_informativo():
    resultado = fixo.resultado()
    resultado["codigos"] = [
        {"codigo": "SEM_DATA_DE_NASCIMENTO", "severidade": "informativo", "mensagem": "x"},
        {"codigo": "MRCA_POSTERIOR_A_DESCENDENTE", "severidade": "critico", "mensagem": "y"},
    ]

    assert vz.veredito(resultado) == "MRCA posterior ao descendente"


# ---------------------------------------------------------------------------
# Escape e recorte
# ---------------------------------------------------------------------------

def test_escape_de_aspas_barra_e_acento():
    sugestao = fixo.sugestao()
    sugestao["grafo"].nodes[fixo.PAI_ID]["label"] = 'Pai "José" \\ Teste & Cia'
    texto = vz.texto_dot(sugestao, fixo.resultado(), fixo.documental())

    assert 'label="Pai \\"José\\" \\\\ Teste & Cia"' in texto
    # O modo HTML não é usado: `&` fica cru, sem virar entidade.
    assert "&amp;" not in texto


def test_recorte_nao_desenha_familia_nem_irmao_fora_do_caminho():
    texto = _texto()

    assert fixo.FAMILIA_JUNCAO not in texto
    assert fixo.FAMILIA_DOADOR not in texto
    assert fixo.IRMAO_ID not in texto


# ---------------------------------------------------------------------------
# Recusas
# ---------------------------------------------------------------------------

def test_sem_sugestao_nao_desenha():
    sugestao = fixo.sugestao()
    sugestao["grafo"] = None
    sugestao["avisos"] = [{"codigo": "HIATO_NAO_POSITIVO", "mensagem": "não há hiato"}]

    with pytest.raises(vz.ErroDeRenderizacao) as exc:
        vz.texto_dot(sugestao, fixo.resultado(), fixo.documental())

    assert exc.value.codigo == vz.SEM_SUGESTAO_PARA_DESENHAR
    assert "não há hiato" in exc.value.mensagem


def test_sem_caminho_documental_nao_desenha():
    with pytest.raises(vz.ErroDeRenderizacao) as exc:
        vz.texto_dot(fixo.sugestao(), fixo.resultado(), {"path": {"ids": []}})

    assert exc.value.codigo == vz.SEM_SUGESTAO_PARA_DESENHAR


def test_formato_nao_suportado_nao_grava(tmp_path):
    destino = str(tmp_path / "arvore.pdf")

    with pytest.raises(vz.ErroDeRenderizacao) as exc:
        vz.renderizar_arvore_sugerida(fixo.sugestao(), fixo.resultado(),
                                      fixo.documental(), destino)

    assert exc.value.codigo == vz.FORMATO_NAO_SUPORTADO
    assert list(tmp_path.iterdir()) == []


def test_formato_divergente_da_extensao(tmp_path):
    destino = str(tmp_path / "arvore.png")

    with pytest.raises(vz.ErroDeRenderizacao) as exc:
        vz.renderizar_arvore_sugerida(fixo.sugestao(), fixo.resultado(),
                                      fixo.documental(), destino, formato="svg")

    assert exc.value.codigo == vz.FORMATO_NAO_SUPORTADO
    assert list(tmp_path.iterdir()) == []


@pytest.mark.parametrize("destino", ["", "   ", None])
def test_destino_vazio(destino):
    with pytest.raises(vz.ErroDeRenderizacao) as exc:
        vz.renderizar_arvore_sugerida(fixo.sugestao(), fixo.resultado(),
                                      fixo.documental(), destino)

    assert exc.value.codigo == vz.DESTINO_OBRIGATORIO


def test_destino_sem_extensao(tmp_path):
    with pytest.raises(vz.ErroDeRenderizacao) as exc:
        vz.renderizar_arvore_sugerida(fixo.sugestao(), fixo.resultado(),
                                      fixo.documental(), str(tmp_path / "arvore"))

    assert exc.value.codigo == vz.DESTINO_OBRIGATORIO


def test_destino_com_pasta_inexistente(tmp_path):
    destino = str(tmp_path / "nao_existe" / "arvore.png")

    with pytest.raises(vz.ErroDeRenderizacao) as exc:
        vz.renderizar_arvore_sugerida(fixo.sugestao(), fixo.resultado(),
                                      fixo.documental(), destino)

    assert exc.value.codigo == vz.DESTINO_OBRIGATORIO


# ---------------------------------------------------------------------------
# Determinismo
# ---------------------------------------------------------------------------

def test_texto_dot_e_deterministico():
    primeiro = vz.texto_dot(fixo.sugestao(), fixo.resultado(), fixo.documental())
    segundo = vz.texto_dot(fixo.sugestao(), fixo.resultado(), fixo.documental())

    assert primeiro == segundo


# ---------------------------------------------------------------------------
# Dependência ausente
# ---------------------------------------------------------------------------

def test_dot_ausente_nao_grava_arquivo(tmp_path, monkeypatch):
    monkeypatch.setattr(vz.shutil, "which", lambda nome: None)
    destino = str(tmp_path / "arvore.png")

    with pytest.raises(vz.ErroDeRenderizacao) as exc:
        vz.renderizar_arvore_sugerida(fixo.sugestao(), fixo.resultado(),
                                      fixo.documental(), destino)

    assert exc.value.codigo == vz.DOT_AUSENTE
    assert "graphviz.org" in exc.value.mensagem
    assert list(tmp_path.iterdir()) == []


def test_graphviz_ausente_quando_o_pacote_nao_importa(tmp_path, monkeypatch):
    monkeypatch.setattr(vz.shutil, "which", lambda nome: "/usr/bin/dot")
    importacao_real = builtins.__import__

    def importacao_falsa(nome, *args, **kwargs):
        if nome == "graphviz":
            raise ImportError("sem graphviz")
        return importacao_real(nome, *args, **kwargs)

    monkeypatch.setattr(builtins, "__import__", importacao_falsa)
    destino = str(tmp_path / "arvore.png")

    with pytest.raises(vz.ErroDeRenderizacao) as exc:
        vz.renderizar_arvore_sugerida(fixo.sugestao(), fixo.resultado(),
                                      fixo.documental(), destino)

    assert exc.value.codigo == vz.GRAPHVIZ_AUSENTE
    assert list(tmp_path.iterdir()) == []

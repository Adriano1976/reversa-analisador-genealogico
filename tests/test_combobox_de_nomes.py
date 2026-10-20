"""O combobox de nomes da tela de entrada (feature 037).

## O que este arquivo prende

- A `<datalist>` saiu: os nomes passam a viajar num bloco `application/json`.
- O bloco JSON e **seguro**: um nome contendo `</script>` nao fecha a tag.
- Os tres campos de nome sao combobox declarado (`role`, `aria-expanded`, `aria-controls`).
- A lista e um `listbox`, e o script trata teclado e `aria-activedescendant`.
- O texto digitado continua livre: o campo nao virou `select`.

## O que ele NAO prende

Que a lista abre ao digitar, que o foco fica no campo ou que `Esc` fecha. Sem navegador
headless e sem executor de JS no projeto, esse comportamento vive no checklist manual
(`onboarding.md`, secao "Checklist manual") e esta declarado em `roadmap.md` `D-14`.
"""
from __future__ import annotations

import json
import os
import re
import sys

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
for _caminho in (RAIZ, os.path.join(RAIZ, "src"), os.path.join(RAIZ, "tests")):
    if _caminho not in sys.path:
        sys.path.insert(0, _caminho)

from fixtures.sample_gedcom import SAMPLE_GED  # noqa: E402

CHAVE_A = "080e7943572d2652"

# Nome com a sequencia que fecharia um bloco <script> se nao fosse escapada.
GEDCOM_COM_FECHAMENTO = (
    "0 HEAD\n1 SOUR TESTE\n1 GEDC\n2 VERS 5.5.1\n2 FORM LINEAGE-LINKED\n"
    "0 @I1@ INDI\n1 NAME Ana /Silva</script>/\n1 SEX F\n0 TRLR\n"
)

_BLOCO = r'<script type="application/json" id="nomes-da-arvore">(.*?)</script>'


def _guardar(pasta: str, nome: str, conteudo: bytes) -> str:
    caminho = os.path.join(pasta, nome)
    with open(caminho, "wb") as fh:
        fh.write(conteudo)
    return caminho


def _com_arvore(cliente_de_upload, conteudo: bytes = SAMPLE_GED.encode("utf-8")) -> str:
    """Grava a arvore e a ABRE pela tela; devolve o corpo da resposta.

    Abrir de verdade (e nao so gravar) e o que produz `gedcom_filename` e `all_names` no
    contexto — sem isso nao existe bloco JSON nem campo de nome.
    """
    _app, cliente, pasta = cliente_de_upload
    nome = f"{CHAVE_A}__arvore.ged"
    _guardar(pasta, nome, conteudo)
    resposta = cliente.post("/", data={"action": "selecionar_arvore", "gedcom_filename": nome})
    assert resposta.status_code == 200, f"abrir a arvore respondeu {resposta.status_code}"
    return resposta.get_data(as_text=True)


class TestOsNomesViajamEmJson:
    def test_a_datalist_saiu(self, cliente_de_upload):
        corpo = _com_arvore(cliente_de_upload)

        assert "<datalist" not in corpo, "a datalist continua no documento"
        assert "gedcom_names" not in corpo, "a ancora da datalist continua no documento"

    def test_o_bloco_json_traz_os_nomes_da_arvore(self, cliente_de_upload):
        corpo = _com_arvore(cliente_de_upload)
        achado = re.search(_BLOCO, corpo, re.S)

        assert achado, "o bloco application/json dos nomes nao existe"
        nomes = json.loads(achado.group(1))
        assert isinstance(nomes, list) and nomes, "o bloco nao trouxe uma lista de nomes"
        assert any("Carlos" in nome for nome in nomes), f"nomes inesperados: {nomes[:5]}"

    def test_nome_com_fechamento_de_script_nao_quebra_o_bloco(self, cliente_de_upload):
        """O perigo: um `<` cru no bloco fecharia a tag e deixaria o resto como HTML.

        A prova e dupla: o bloco inteiro, lido ate o primeiro `</script>`, tem de continuar
        sendo JSON valido, e nao pode conter `<` cru. Se o escape falhasse, a leitura pararia
        no fechamento que veio DENTRO do nome e o `json.loads` estouraria.
        """
        corpo = _com_arvore(cliente_de_upload, GEDCOM_COM_FECHAMENTO.encode("utf-8"))
        achado = re.search(_BLOCO, corpo, re.S)

        assert achado, "o bloco JSON sumiu quando o nome trouxe o fechamento de tag"
        assert "<" not in achado.group(1), "um `<` cru vazou para dentro do bloco JSON"
        nomes = json.loads(achado.group(1))
        assert any("Ana" in nome for nome in nomes), f"a pessoa do GEDCOM sumiu: {nomes}"

    def test_sem_arvore_nao_ha_bloco_nem_combobox(self, cliente_de_upload):
        _app, cliente, _pasta = cliente_de_upload

        corpo = cliente.get("/").get_data(as_text=True)

        assert 'id="nomes-da-arvore"' not in corpo, "o bloco de nomes aparece sem arvore"
        assert 'role="combobox"' not in corpo, "campo de nome aparece sem arvore"


class TestOCampoEDeclaradoComoCombobox:
    def test_os_tres_campos_de_nome_sao_combobox(self, cliente_de_upload):
        corpo = _com_arvore(cliente_de_upload)

        assert corpo.count('role="combobox"') == 3, "esperava os tres campos de nome como combobox"
        assert corpo.count('aria-controls="lista-de-nomes"') == 3, (
            "os campos nao apontam para a mesma lista"
        )
        assert corpo.count('aria-expanded="false"') >= 3, "o estado inicial da lista nao e declarado"

    def test_a_lista_e_um_listbox(self, cliente_de_upload):
        corpo = _com_arvore(cliente_de_upload)
        inicio = corpo.index('id="lista-de-nomes"')
        abertura = corpo[inicio:corpo.index(">", inicio)]

        assert 'role="listbox"' in abertura, "a lista nao se declara listbox"

    def test_o_script_trata_teclado_e_estado(self, cliente_de_upload):
        corpo = _com_arvore(cliente_de_upload)

        for marca in ("ArrowDown", "ArrowUp", "Escape", "Enter", "aria-activedescendant"):
            assert marca in corpo, f"o script nao trata {marca}"


class TestOTextoContinuaLivre:
    def test_o_campo_nao_ficou_somente_leitura(self, cliente_de_upload):
        corpo = _com_arvore(cliente_de_upload)

        for nome_do_campo in ("person1_name", "person2_name", "root_name"):
            achado = re.search(rf'<input[^>]*name="{nome_do_campo}"[^>]*>', corpo)
            assert achado, f"o campo {nome_do_campo} sumiu"
            assert "readonly" not in achado.group(0), f"{nome_do_campo} virou somente leitura"

    def test_os_nomes_dos_campos_nao_mudaram(self, cliente_de_upload):
        corpo = _com_arvore(cliente_de_upload)

        for nome_do_campo in ("person1_name", "person2_name", "root_name", "matches_csv"):
            assert f'name="{nome_do_campo}"' in corpo, f"o campo {nome_do_campo} foi renomeado"

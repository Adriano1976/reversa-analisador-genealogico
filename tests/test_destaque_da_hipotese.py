"""O destaque da hipótese mais próxima da média publicada (feature 044).

## A regra, e por que ela tem duas constantes

`BANDA_DE_DESTAQUE = 1,5` e `MAXIMO_DE_DESTAQUES = 3`. A segunda existe para o cartão
não virar um segundo bloco 3; a primeira existe porque a escolha precisa de um corte
declarado, e não do número redondo "três".

Medido em 2026-10-22 nos 456 kits do arquivo real: **423 com um destaque, 32 com dois,
1 com três**. Este arquivo prende as três situações em valores que existem no arquivo —
154,5 cM (três), 42,6 cM (dois) e 9,05 cM (um) —, para que uma mudança de banda apareça
como teste vermelho em vez de mudar a tela em silêncio.

## O que este arquivo NÃO mede

Não mede a redação: `Hipótese mais próxima da média publicada` pode virar outra frase
sem que a regra mude. E não mede a caixa no HTML — isso é `test_destaque_na_tela.py`.
"""
from __future__ import annotations

import json
import os
import sys

import pytest

_RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
for _caminho in (_RAIZ, os.path.join(_RAIZ, "src")):
    if _caminho not in sys.path:
        sys.path.insert(0, _caminho)

from core.relationship_hypotheses import (  # noqa: E402
    BANDA_DE_DESTAQUE,
    MAXIMO_DE_DESTAQUES,
    ROTULOS_DE_DESTAQUE,
    destaque_das_candidatas,
    possible_relationships,
)


def _candidata(nome, media):
    return {"name_pt": nome, "average": media, "mrca": {"rotulo": "bisavós"}}


class TestAsConstantes:
    def test_a_banda_e_o_teto_sao_os_medidos(self):
        assert BANDA_DE_DESTAQUE == 1.5
        assert MAXIMO_DE_DESTAQUES == 3

    def test_o_teto_nao_passa_de_tres(self):
        """Acima de três o bloco vira lista nova, e a tela perde o foco."""
        assert 1 <= MAXIMO_DE_DESTAQUES <= 3
        assert set(ROTULOS_DE_DESTAQUE) == {1, 2, 3}


class TestOsTresCasosDoArquivoReal:
    def test_uma_so_quando_o_dado_separa(self):
        bloco = possible_relationships(9.05)
        destaque = bloco["destaque"]
        assert destaque["quantidade"] == 1
        assert destaque["itens"][0]["nome"] == "Primos de 8º grau"
        assert destaque["itens"][0]["distancia"] == pytest.approx(1.9, abs=0.05)
        assert destaque["rotulo"] == ROTULOS_DE_DESTAQUE[1]

    def test_duas_quando_sao_vizinhos_de_uma_remocao(self):
        """42,6 cM: a segunda está a 7,6 da média, dentro de 1,5 × 5,4."""
        destaque = possible_relationships(42.6)["destaque"]
        assert destaque["quantidade"] == 2
        assert [item["nome"] for item in destaque["itens"]] == [
            "Primos de 3º grau (uma geração de diferença)",
            "Primos de 4º grau",
        ]

    def test_tres_no_unico_caso_do_arquivo(self):
        """154,5 cM — o cartão da Clezia: 32,5 / 34,5 / 37,5 da média."""
        destaque = possible_relationships(154.5)["destaque"]
        assert destaque["quantidade"] == 3
        assert [item["nome"] for item in destaque["itens"]] == [
            "Primos de 2º grau (uma geração de diferença)",
            "Meio-primos de 2º grau",
            "Primos de 1º grau (três gerações de diferença)",
        ]
        assert [item["distancia"] for item in destaque["itens"]] == [32.5, 34.5, 37.5]


class TestABanda:
    def test_a_segunda_so_entra_dentro_da_banda(self):
        candidatas = [_candidata("primeira", 100.0), _candidata("segunda", 110.0)]
        # cm = 100: distâncias 0 e 10; a banda é 0 × 1,5 = 0 -> só a primeira.
        destaque = destaque_das_candidatas(candidatas, 100.0)
        assert [item["nome"] for item in destaque["itens"]] == ["primeira"]

    def test_a_segunda_entra_no_limite_da_banda(self):
        candidatas = [_candidata("primeira", 110.0), _candidata("segunda", 115.0)]
        destaque = destaque_das_candidatas(candidatas, 100.0)
        assert [item["nome"] for item in destaque["itens"]] == ["primeira", "segunda"]

    def test_a_segunda_fica_de_fora_um_pouco_alem_da_banda(self):
        candidatas = [_candidata("primeira", 110.0), _candidata("segunda", 116.0)]
        destaque = destaque_das_candidatas(candidatas, 100.0)
        assert [item["nome"] for item in destaque["itens"]] == ["primeira"]

    def test_o_teto_corta_um_empate_largo(self):
        """Cinco candidatas a 10 da média caberiam na banda; o teto mostra três."""
        candidatas = [_candidata(f"r{n}", 110.0) for n in range(5)]
        destaque = destaque_das_candidatas(candidatas, 100.0)
        assert destaque["quantidade"] == MAXIMO_DE_DESTAQUES
        assert len(destaque["itens"]) == MAXIMO_DE_DESTAQUES

    def test_sem_candidata_nao_ha_destaque(self):
        assert destaque_das_candidatas([], 100.0) is None
        assert possible_relationships(5000)["destaque"] is None


class TestODestaqueNaoAbreAExcecaoDoParentescoUnico:
    """O destaque é leitura, não conclusão — e a lista continua inteira."""

    def test_a_lista_nao_perde_ninguem(self):
        bloco = possible_relationships(154.5)
        assert len(bloco["possible_relationships"]) == 9
        assert len(bloco["destaque"]["itens"]) == 3

    def test_as_marcadas_sao_exatamente_as_do_destaque(self):
        bloco = possible_relationships(154.5)
        marcadas = [c["name_pt"] for c in bloco["possible_relationships"] if c["destaque"]]
        assert marcadas == [item["nome"] for item in bloco["destaque"]["itens"]]

    def test_a_ressalva_diz_o_tamanho_do_conjunto_e_que_nao_ha_confirmacao(self):
        for cm in (9.05, 42.6, 154.5):
            bloco = possible_relationships(cm)
            ressalva = bloco["destaque"]["ressalva"]
            total = len(bloco["possible_relationships"])
            assert f"{total} relações compatíveis" in ressalva
            assert "não é confirmação" in ressalva, (
                "sem essa frase o destaque passa a ser lido como veredito"
            )
            assert "GEDCOM" in ressalva

    def test_todo_item_diz_onde_procurar(self):
        for cm in (9.05, 42.6, 154.5):
            for item in possible_relationships(cm)["destaque"]["itens"]:
                assert item["onde"], f"{item['nome']} foi destacado sem antepassado comum"

    def test_o_payload_atravessa_json(self):
        json.dumps(possible_relationships(154.5))

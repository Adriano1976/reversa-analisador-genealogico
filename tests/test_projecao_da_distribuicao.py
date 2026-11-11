"""Testes da projecao da distribuicao para a tela (feature 057).

A projecao nao formata numero nem calcula geometria: so troca o tipo de dominio
pelo dicionario que o template le (`ADR-34`).
"""
from __future__ import annotations

from application.distribuicao import projetar_distribuicao
from core.distribuicao import ResumoDoCromossomo


def _resumo(cromossomo="7", kits=("A1", "B2"), cm_medio=12.666666):
    return ResumoDoCromossomo(cromossomo=cromossomo, kits=tuple(kits), cm_medio=cm_medio)


def test_projecao_conta_os_kits_e_mantem_o_cm_cru():
    projetados = projetar_distribuicao((_resumo(),))

    assert projetados == [{"cromossomo": "7", "kits": 2, "cm_medio": 12.666666}]


def test_projecao_devolve_lista_vazia_sem_resumo():
    assert projetar_distribuicao(()) == []
    assert projetar_distribuicao(None) == []


def test_projecao_nao_muta_o_resumo():
    resumo = _resumo()
    [linha] = projetar_distribuicao((resumo,))

    linha["kits"] = 99

    assert resumo.kits == ("A1", "B2")
    assert resumo.cm_medio == 12.666666

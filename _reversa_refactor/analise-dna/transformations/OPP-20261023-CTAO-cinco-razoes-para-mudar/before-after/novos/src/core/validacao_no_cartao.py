"""O veredito de viabilidade temporal do cartao (feature 028).

Olha a linha documental de verdade, e nao o texto que a tela mostra: com a janela
de vida impossivel, o parentesco exibido vira "nao encontrado", mas a linha
existe e e sobre ela que o veredito fala.
"""
from __future__ import annotations

from .documentary_relationship import birth_date
from .registro import get_name
from .rotulos_do_cartao import (
    ROTULOS_DE_VALIDACAO,
    _aviso_da_validacao,
)
from .validator import (
    ComparacaoParaValidar,
    validar_comparacao,
)


def _validacao_do_cartao(arvore, root_id, documental, comparacao, kit, geracoes_do_kit,
                         ano_base, intervalo):
    """As quatro chaves que o cartao le, a partir do veredito da feature 028.

    ## Por que o veredito viaja no dicionario

    O template itera os dicionarios de resultado (`app.py` passa `resultado.resultados`
    para `dna_results`), e le `result.cm`, `result.comparison`, `result.documentary`.
    Um campo que nao esteja no dicionario nao aparece na tela. O precedente e o
    `confrontacao_rotulo`, que ja e rotulo humano produzido aqui.

    ## Por que `documental` e o ORIGINAL, e nao o apresentado

    Quando a janela de vida e impossivel, a tela troca o parentesco pelo "nao
    encontrado" (`documentary_do_registro` guarda o original). O veredito temporal e
    sobre a LINHA DOCUMENTAL, entao ele olha o caminho de verdade: julgar o cartao pelo
    texto que a tela mostra daria "inconclusivo" justamente nos casos em que a linha
    existe e esta quebrada.
    """
    pessoa_a = (documental or {}).get("person_a") or {}
    pessoa_b = (documental or {}).get("person_b") or {}
    doador = {
        "id": root_id,
        "nome": pessoa_a.get("name") or get_name(arvore[0].get(root_id)),
        "nascimento": pessoa_a.get("birth") or birth_date(arvore[0], root_id),
    }
    match = {
        "id": pessoa_b.get("id"),
        "nome": pessoa_b.get("name"),
        "nascimento": pessoa_b.get("birth"),
    }
    resultado = validar_comparacao(ComparacaoParaValidar(
        doador=doador,
        match=match,
        documental=documental,
        kit={"kit": kit.get("kit"), "total_cm": kit.get("total_cm"),
             "mrca_generations": geracoes_do_kit},
        ano_referencia=ano_base,
        intervalo_de_geracao=intervalo,
        comparacao_existente=comparacao,
    ))
    status = resultado.get("status") or ""
    rotulo, classe = ROTULOS_DE_VALIDACAO.get(status) or (None, None)
    chaves = {
        "validacao_status": status,
        "validacao_rotulo": rotulo,
        "validacao_classe": classe,
        # O aviso existe para o `title` do selo. Sem selo, ele nao teria onde aparecer, e
        # carregar texto que nenhuma tela le e a definicao de dado morto.
        "validacao_aviso": _aviso_da_validacao(resultado) if rotulo else None,
    }
    return chaves, resultado

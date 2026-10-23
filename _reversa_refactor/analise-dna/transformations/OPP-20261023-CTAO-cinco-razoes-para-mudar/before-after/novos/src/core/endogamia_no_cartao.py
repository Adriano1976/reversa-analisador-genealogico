"""O diagnostico de endogamia estrutural e o que dele aparece no cartao.

Le o grafo do GEDCOM e devolve o bloco da secao 2, o selo do cabecalho e a frase
da secao 5. Nao decide nada sobre o parentesco documental: so descreve a forma da
arvore.
"""
from __future__ import annotations

from .registro import (
    get_name,
    ref_id,
)
from .rotulos_do_cartao import (
    _explicacao_da_endogamia,
    _observacao_estrutural,
    _selo_da_endogamia,
)


def _nome_do_no(arvore, no) -> str:
    """Nome de exibicao de um no do grafo: pessoa, casal de familia ou o id.

    O diagnostico de reconvergencia pode cair num no de familia (o casal), e nao
    numa pessoa. Trocar o id por "HUSB × WIFE" e o que evita a tela mostrar
    `@F123@` para o operador.
    """
    if not no:
        return ""
    pessoas = arvore[0] if arvore else {}
    if no in pessoas:
        return get_name(pessoas[no])
    familias = arvore[1] if arvore and len(arvore) > 1 else {}
    familia = familias.get(no)
    if familia is not None:
        nomes = []
        for rec in familia.sub_records:
            if rec.tag in ("HUSB", "WIFE"):
                pid = ref_id(rec.value)
                if pid in pessoas:
                    nomes.append(get_name(pessoas[pid]))
        return " × ".join(nomes) if nomes else "Família"
    return no

def _endogamia_estrutural(contexto, pid, documentary, evidencia_mitigada):
    """Diagnostico de endogamia no grafo, selo do cabecalho e frase da secao 5.

    Extraida pela OPP-20261023-ETAP. Devolve
    `(arvore, selo, tem_caminho_documental, observacoes)`. O ultimo item e a
    frase que so existe quando o diagnostico estrutural acusou.
    """
    # A ENDOGAMIA ESTRUTURAL, no grafo do GEDCOM. Recebe o grafo por
    # parametro, converte para nao-direcionado quando preciso (o parser ja
    # entrega `nx.Graph`) e usa `nx.all_shortest_paths` entre a raiz e o
    # match. `NetworkXNoPath` e o caso do match sem ligacao documental: o
    # diagnostico volta vazio e o cartao continua sendo montado.
    diagnostico_de_endogamia = contexto.analisador.diagnosticar_endogamia(
        contexto.arvore[2], contexto.root_id, pid,
        mrca_id=(documentary.get("common_ancestor") or {}).get("id"))
    # O caminho DOCUMENTAL decide como o achado e apresentado: com ele, a
    # secao 1 e a secao 2 falam do mesmo par; sem ele, o selo vira "Sinal
    # estrutural na árvore" e o bloco explica que a busca documental parou
    # no teto de `MAX_DEPTH`, em vez de fingir que confirmou parentesco.
    tem_caminho_documental = bool((documentary.get("path") or {}).get("ids"))
    arvore_da_endogamia = diagnostico_de_endogamia.para_dicionario()
    # Nomes resolvidos: as reconvergencias sao o que a tela mostra; o
    # tronco comum fica no `details` recolhido. `mrca_nomes` permanece
    # como alias do tronco para nao quebrar consumidor do campo antigo.
    arvore_da_endogamia["mrca_nomes"] = [
        _nome_do_no(contexto.arvore, no) for no in diagnostico_de_endogamia.mrca_ids
    ]
    arvore_da_endogamia["tronco_comum_nomes"] = [
        _nome_do_no(contexto.arvore, no)
        for no in diagnostico_de_endogamia.tronco_comum_ids
    ]
    arvore_da_endogamia["reconvergencias"] = [
        {
            "divergencia_id": reconvergencia.divergencia_id,
            "divergencia_nome": _nome_do_no(contexto.arvore, reconvergencia.divergencia_id),
            "convergencia_id": reconvergencia.convergencia_id,
            "convergencia_nome": _nome_do_no(contexto.arvore, reconvergencia.convergencia_id),
            "trechos": [
                {
                    "ids": list(trecho),
                    "nomes": [_nome_do_no(contexto.arvore, no) for no in trecho],
                }
                for trecho in reconvergencia.trechos
            ],
        }
        for reconvergencia in diagnostico_de_endogamia.reconvergencias
    ]
    arvore_da_endogamia["explicacao"] = _explicacao_da_endogamia(
        diagnostico_de_endogamia, tem_caminho_documental)
    # O selo do cabecalho e decidido AQUI (o template so le os tres
    # campos), pela mesma razao dos rotulos de validacao: texto de tela
    # e regra, e o Jinja nao monta frase de dominio.
    selo_da_endogamia = _selo_da_endogamia(
        evidencia_mitigada, diagnostico_de_endogamia, tem_caminho_documental)

    # A SECAO 5 GUARDA SO O DIAGNOSTICO ESTRUTURAL. O detalhe numerico
    # do filtro (total bruto x mitigado, descartados, maior bloco) vive
    # no bloco proprio da secao 2. Repeti-lo aqui era a duplicacao que o
    # operador lia duas vezes no mesmo cartao.
    observacoes_da_endogamia = (
        [_observacao_estrutural(diagnostico_de_endogamia,
                                tem_caminho_documental)]
        if diagnostico_de_endogamia.endogamia_estrutural else []
    )
    return (arvore_da_endogamia, selo_da_endogamia,
            tem_caminho_documental, observacoes_da_endogamia)

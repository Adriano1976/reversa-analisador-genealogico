"""O cartao de um match sem nenhuma pessoa compativel na arvore.

Emenda 039/E002: o item recusado pela triagem vira cartao com o mesmo tratamento do
grupo "Parentesco documental nao encontrado". Nao decide nada: le o kit, o descarte
e a evidencia do proprio kit.
"""
from __future__ import annotations

from .documentary_relationship import person_summary
from .evidence_comparison import compare
from .genetic_evidence import evidence_for
from .passo_por_kit import _observacoes
from .relationship_hypotheses import hypotheses_for_evidence


def _cartao_sem_correspondencia(*, arvore, root_id, ano_base, kit, chave_nome, chave_kit,
                                por_kit, evidencia_mitigada, descarte, avisos, analisador):
    """Monta o cartao de um match sem nenhuma pessoa compativel na arvore (emenda 039/E002).

    O cartao tem o **mesmo tratamento** dos classificados "Parentesco documental nao
    encontrado": mesmo cabecalho, mesmo rotulo, as cinco secoes e o mesmo comportamento
    de recolhimento. O que ele NAO tem e pessoa do GEDCOM: `documentary.person_b` fica
    ausente, o caminho fica `None` e o diagrama nao existe.

    Nao decide nada: recebe o kit e o descarte ja produzidos, le a evidencia genetica do
    proprio kit e devolve o dicionario que a tela consome. A lista completa de descartes
    continua intacta; este cartao e' uma leitura dela, nao uma promocao.
    """
    pessoa_ausente = {
        "id": None, "name": None, "sex": None, "birth": None, "birth_year": None,
        "birth_place": None, "death": None, "death_year": None,
        "parents": [], "parent_names": [], "spouses": [], "children": [],
        "family_as_child": [],
    }
    aviso_sem = {
        "code": "sem_correspondencia",
        "message": ("Nenhuma pessoa com nome compatível foi encontrada no GEDCOM para este "
                    "match. O cM é um sinal de DNA; não há parentesco documental a afirmar."),
    }
    documentary = {
        "status": "not_found",
        "source": "GEDCOM",
        "label": "Parentesco documental não encontrado",
        "relationship_key": None,
        "meioses": None,
        "degrees": None,
        "person_a": person_summary(arvore, root_id),
        "person_b": pessoa_ausente,
        "common_ancestor": None,
        "path": None,
        "common_ancestors": [],
        "additional_paths": [],
        "evidence": [],
        "homonyms": {},
        "ambiguous_identity": False,
        "warnings": [aviso_sem],
    }

    evidence = evidence_for(por_kit, avisos=avisos, kit_key=chave_kit)
    hypotheses = hypotheses_for_evidence(evidence)
    comparison = compare(documentary, hypotheses, evidence)
    comparison["detail"] = (
        "Há evidência genética, mas nenhuma pessoa com nome compatível foi encontrada no "
        "GEDCOM. Nenhum caminho foi inventado a partir do DNA."
    )
    comparison["causes"] = [
        "o nome do CSV não corresponde a nenhum registro do GEDCOM",
        "o ramo do match pode não estar cadastrado na árvore",
        "nome de casada, grafia ou abreviação fora do GEDCOM",
    ]

    geracoes_do_kit = next(
        (k.get("mrca_generations") for k in ((evidence or {}).get("kits") or [])
         if k.get("mrca_generations")), None)
    arvore_da_endogamia = {
        "endogamia_estrutural": False,
        "explicacao": "Sem pessoa na árvore para diagnosticar endogamia estrutural.",
        "reconvergencias": [],
        "mrca_nomes": [],
        "tronco_comum_nomes": [],
    }
    endogamia = {
        **evidencia_mitigada.para_dicionario(),
        "selo": None,
        "limiares": {
            "segmento": analisador.cm_minimo_segmento,
            "maior_bloco": analisador.cm_minimo_maior_bloco,
        },
        "arvore": arvore_da_endogamia,
    }
    observations = list(_observacoes(documentary, evidence, comparison))

    return {
        "match_name": descarte["csv_name"],
        "csv_name": descarte["csv_name"],
        "identidade": "a_confirmar",
        "identidade_aviso": ("Nenhuma pessoa com nome compatível na árvore; não há registro "
                             "para comparar."),
        "janela_de_vida": "sem_dado",
        "idade_na_arvore": None,
        "data_de_nascimento": None,
        "data_imprecisa": False,
        "ano_de_referencia": ano_base,
        "janela_aviso": None,
        "profundidade": "sem_dado",
        "profundidade_razao": None,
        "geracoes_documentais": None,
        "geracoes_do_kit": geracoes_do_kit,
        "profundidade_no_sugerido": None,
        "profundidade_resumo": "Sem caminho documental para comparar.",
        "profundidade_aviso": None,
        "confrontacao_efetiva": (comparison or {}).get("status"),
        "confrontacao_rotulo": (comparison or {}).get("label"),
        "validacao_status": "INCONCLUSIVO",
        "validacao_rotulo": None,
        "validacao_classe": None,
        "validacao_aviso": None,
        "sugestao_geracoes": 0,
        "sugestao_resumo": None,
        "sugestao_mermaid": None,
        "sugestao_aviso": ("Sem pessoa na árvore, não há caminho documental para sugerir "
                           "correção."),
        "cm": kit["total_cm"],
        "kit": kit["kit"],
        "text_path": "",
        "mermaid_data": None,
        "documentary": documentary,
        "documentary_do_registro": None,
        "genetic_evidence": evidence,
        "hypotheses": hypotheses,
        "comparison": comparison,
        "endogamia": endogamia,
        "observations": observations,
        "promovido": None,
        # A marca que separa este cartao de um cartao ACEITO. `nomes_com_cartao_aceito`
        # a ignora (o item nao exclui a si mesmo) e a aplicacao a usa para contar.
        "sem_correspondencia": True,
        "warnings": (documentary.get("warnings") or []) + (evidence.get("warnings") or []),
    }

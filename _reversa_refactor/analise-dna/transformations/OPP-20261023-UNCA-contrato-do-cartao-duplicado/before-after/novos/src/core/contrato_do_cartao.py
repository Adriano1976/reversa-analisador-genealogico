"""As chaves do cartao de analise, declaradas em um lugar so.

Dois construtores montam o mesmo cartao:

- `core.passo_por_kit._cartao_do_kit`, o cartao de um kit que achou pessoa na arvore;
- `core.cartao_sem_correspondencia._cartao_sem_correspondencia`, o cartao do match que
  nao achou ninguem.

O segundo acrescenta uma chave a mais, `CHAVE_SEM_CORRESPONDENCIA`, e repete as outras
quarenta. As duas listas ja divergiram na ORDEM antes desta declaracao existir, e nada
avisava: o template le por nome, entao uma chave criada em um construtor e esquecida no
outro virava campo vazio na tela para metade dos cartoes.

A tupla e consumida por `tests/test_contrato_do_cartao.py`, que produz um cartao de cada
tipo e compara o conjunto de chaves. E a unica forma de a divergencia aparecer como
falha em vez de silencio.
"""
from __future__ import annotations

CHAVES_DO_CARTAO: tuple[str, ...] = (
    "match_name",
    "csv_name",
    "identidade",
    "identidade_aviso",
    "janela_de_vida",
    "idade_na_arvore",
    "data_de_nascimento",
    "data_imprecisa",
    "ano_de_referencia",
    "janela_aviso",
    "profundidade",
    "profundidade_razao",
    "geracoes_documentais",
    "geracoes_do_kit",
    "profundidade_no_sugerido",
    "profundidade_resumo",
    "profundidade_aviso",
    "confrontacao_efetiva",
    "confrontacao_rotulo",
    "validacao_status",
    "validacao_rotulo",
    "validacao_classe",
    "validacao_aviso",
    "sugestao_geracoes",
    "sugestao_resumo",
    "sugestao_mermaid",
    "sugestao_aviso",
    "cm",
    "kit",
    "text_path",
    "mermaid_data",
    "documentary",
    "documentary_do_registro",
    "genetic_evidence",
    "hypotheses",
    "comparison",
    "endogamia",
    "observations",
    "promovido",
    "warnings",
)

#: A unica chave que o cartao sem correspondencia acrescenta. O template a le para
#: separar os dois tipos na lista, e `nomes_com_cartao_aceito` a ignora.
CHAVE_SEM_CORRESPONDENCIA = "sem_correspondencia"

__all__ = ["CHAVE_SEM_CORRESPONDENCIA", "CHAVES_DO_CARTAO"]

"""Fase unica da OPP-20261023-CTAO, gerada fora do projeto.

Le `src/core/dna_analysis.py` e escreve os oito arquivos da fronteira nova em
`before-after/novos/src/core/`, mais a versao reduzida de `dna_analysis.py`.

Cada funcao e movida VERBATIM, por fatia de linha. Os imports de cada modulo novo
sao calculados por tokenize: procuram-se tokens NAME que pertencam ao mapa de
simbolos globais, e o mapa diz de que modulo cada um vem. Assim nenhum import
sobra e nenhum falta.

Nao toca no projeto. Roda da raiz:  python <este arquivo>
"""
from __future__ import annotations

import io
import pathlib
import tokenize

RAIZ = pathlib.Path(__file__).resolve().parents[4]
ALVO = RAIZ / "src" / "core" / "dna_analysis.py"
SAIDA = pathlib.Path(__file__).resolve().parent / "before-after" / "novos" / "src" / "core"

# Fatias 1-based inclusivas, medidas no arquivo de 1.258 linhas.
FATIAS = {
    "dependencias": [(115, 146)],
    "contexto_da_analise": [(149, 179), (577, 587)],
    "rotulos_do_cartao": [(233, 246), (249, 267), (295, 312), (315, 331), (334, 394)],
    "validacao_no_cartao": [(397, 448)],
    "endogamia_no_cartao": [(270, 292), (654, 719)],
    "passo_por_kit": [
        (182, 198), (201, 230), (590, 626), (629, 651),
        (722, 738), (741, 782), (785, 808), (811, 1034),
    ],
    "cartao_sem_correspondencia": [(451, 574)],
}
BLOCO_DNA_ANALYSIS = [(1, 41), (1037, 1241), (1244, 1258)]

# Simbolo -> modulo de onde ele vem. Quem nao esta no mapa e' local ou builtin.
MAPA = {
    # hipotese de compatibilidade e fachada
    "Dependencias": ".dependencias",
    # novos modulos internos
    "_ContextoDaAnalise": ".contexto_da_analise",
    "_dossie": ".contexto_da_analise",
    "ROTULOS_DE_VALIDACAO": ".rotulos_do_cartao",
    "_aviso_da_validacao": ".rotulos_do_cartao",
    "_explicacao_da_endogamia": ".rotulos_do_cartao",
    "_observacao_estrutural": ".rotulos_do_cartao",
    "_selo_da_endogamia": ".rotulos_do_cartao",
    "_validacao_do_cartao": ".validacao_no_cartao",
    "_nome_do_no": ".endogamia_no_cartao",
    "_endogamia_estrutural": ".endogamia_no_cartao",
    "_montar_diagrama": ".passo_por_kit",
    "_observacoes": ".passo_por_kit",
    "_recusa_do_kit": ".passo_por_kit",
    "_parentesco_do_kit": ".passo_por_kit",
    "_confronto_do_kit": ".passo_por_kit",
    "_profundidade_do_caminho": ".passo_por_kit",
    "_rotulo_do_confronto": ".passo_por_kit",
    "_cartao_do_kit": ".passo_por_kit",
    "_cartao_sem_correspondencia": ".cartao_sem_correspondencia",
    # modulos pre-existentes do nucleo
    "resolvedor_de_diagrama": ".diagram_domain",
    "CM_MINIMO_SEGMENTO": ".endogamia",
    "DNAAnalyzer": ".endogamia",
    "EvidenciaMitigada": ".endogamia",
    "MENSAGEM_ENDEROGAMIA": ".endogamia",
    "cobertura_do_arquivo": ".",
    "birth_date": ".documentary_relationship",
    "documental_nao_encontrado": ".documentary_relationship",
    "documentary_relationship": ".documentary_relationship",
    "homonym_dossier": ".documentary_relationship",
    "intervalo_de_geracao_mediano": ".documentary_relationship",
    "person_summary": ".documentary_relationship",
    "DnaCsvSemColunas": ".erros",
    "PessoaNaoEncontrada": ".erros",
    "compare": ".evidence_comparison",
    "build_genetic_evidence": ".genetic_evidence",
    "evidence_for": ".genetic_evidence",
    "conferir": ".identidade_do_match",
    "nomes_divergentes": ".identidade_do_match",
    "MAX_DEPTH": ".path_finding",
    "IMPOSSIVEL": ".janela_de_vida",
    "ano_de_referencia": ".janela_de_vida",
    "aviso_da_janela": ".janela_de_vida",
    "conferir_janela_de_vida": ".janela_de_vida",
    "ATENCAO": ".profundidade_do_caminho",
    "DIVERGENCIA": ".profundidade_do_caminho",
    "aviso_da_profundidade": ".profundidade_do_caminho",
    "conferir_profundidade": ".profundidade_do_caminho",
    "no_na_profundidade_sugerida": ".profundidade_do_caminho",
    "resumo_da_profundidade": ".profundidade_do_caminho",
    "avaliar_candidatos": ".matching",
    "build_ged_indexes": ".matching",
    "match_candidates": ".matching",
    "NAO_ENCONTRADO": ".motivos_do_descarte",
    "Motivo": ".motivos_do_descarte",
    "elegivel": ".sem_correspondencia",
    "nomes_com_cartao_aceito": ".sem_correspondencia",
    "drop_short_tokens": ".name_normalization",
    "norm_name": ".name_normalization",
    "soft_prefix_jaccard": ".name_normalization",
    "split_name_pt": ".name_normalization",
    "surname_core_tokens": ".name_normalization",
    "surnames_set": ".name_normalization",
    "token_prefixes": ".name_normalization",
    "top_given_tokens": ".name_normalization",
    "hypotheses_for_evidence": ".relationship_hypotheses",
    "demojibake": "utils.text_cleaning",
    "strip_bad_utf": "utils.text_cleaning",
    "get_name": ".registro",
    "ref_id": ".registro",
    "resumo_da_sugestao": ".cirurgia_do_grafo",
    "ERRO_CRONICO": ".validator",
    "VALIDADO": ".validator",
    "ComparacaoParaValidar": ".validator",
    "validar_comparacao": ".validator",
}

PROPRIOS = {
    "dependencias": {"Dependencias"},
    "contexto_da_analise": {"_ContextoDaAnalise", "_dossie"},
    "rotulos_do_cartao": {
        "ROTULOS_DE_VALIDACAO", "_aviso_da_validacao", "_explicacao_da_endogamia",
        "_observacao_estrutural", "_selo_da_endogamia",
    },
    "validacao_no_cartao": {"_validacao_do_cartao"},
    "endogamia_no_cartao": {"_nome_do_no", "_endogamia_estrutural"},
    "passo_por_kit": {
        "_montar_diagrama", "_observacoes", "_recusa_do_kit", "_parentesco_do_kit",
        "_confronto_do_kit", "_profundidade_do_caminho", "_rotulo_do_confronto",
        "_cartao_do_kit",
    },
    "cartao_sem_correspondencia": {"_cartao_sem_correspondencia"},
    "dna_analysis": {"dna_analysis"},
}

DOCSTRINGS = {
    "dependencias": '"""O que o nucleo consome de fora, entregue pela borda.\n\n'
    "A classe morava em `core/dna_analysis.py` e e consumida por `core/path_search.py`\n"
    "e por `src/app.py`. Saiu para ter endereco proprio: um contrato de tres\n"
    "consumidores nao deve morar dentro de um arquivo que muda por outro motivo.\n"
    '"""\n',
    "contexto_da_analise": '"""O estado que nao muda entre kits, com os dois caches da analise.\n\n'
    "`_ContextoDaAnalise` e um involucro congelado de entradas, nao um agregado de\n"
    "dominio: nao guarda invariante e nao decide nada. `_dossie` opera o cache de\n"
    "homonimos que vive nele, e existia como closure antes da OPP-20261023-ORQA.\n"
    '"""\n',
    "rotulos_do_cartao": '"""As palavras e as classes CSS que o operador le no cartao.\n\n'
    "Texto de tela e regra: o Jinja so testa se ha rotulo, e quem decide o rotulo, a\n"
    "cor e o `title` e este modulo. Separado do fluxo para que mudar uma frase nao\n"
    "encoste no pipeline.\n"
    '"""\n',
    "validacao_no_cartao": '"""O veredito de viabilidade temporal do cartao (feature 028).\n\n'
    "Olha a linha documental de verdade, e nao o texto que a tela mostra: com a janela\n"
    "de vida impossivel, o parentesco exibido vira \"nao encontrado\", mas a linha\n"
    "existe e e sobre ela que o veredito fala.\n"
    '"""\n',
    "endogamia_no_cartao": '"""O diagnostico de endogamia estrutural e o que dele aparece no cartao.\n\n'
    "Le o grafo do GEDCOM e devolve o bloco da secao 2, o selo do cabecalho e a frase\n"
    "da secao 5. Nao decide nada sobre o parentesco documental: so descreve a forma da\n"
    "arvore.\n"
    '"""\n',
    "passo_por_kit": '"""Um kit do CSV vira cartao, ou vira descarte quando nao ha candidato.\n\n'
    "E o pipeline de um unico kit, do casamento de nome a montagem do dicionario de 40\n"
    "chaves. Cada etapa tem nome proprio e recebe o contexto da analise, que carrega o\n"
    "estado compartilhado entre kits.\n"
    '"""\n',
    "cartao_sem_correspondencia": '"""O cartao de um match sem nenhuma pessoa compativel na arvore.\n\n'
    "Emenda 039/E002: o item recusado pela triagem vira cartao com o mesmo tratamento do\n"
    "grupo \"Parentesco documental nao encontrado\". Nao decide nada: le o kit, o descarte\n"
    "e a evidencia do proprio kit.\n"
    '"""\n',
}


def fatia(linhas, faixa):
    inicio, fim = faixa
    return "".join(linhas[inicio - 1 : fim])


def nomes_usados(texto: str) -> set[str]:
    usados = set()
    for token in tokenize.generate_tokens(io.StringIO(texto).readline):
        if token.type == tokenize.NAME:
            usados.add(token.string)
    return usados


def imports_para(nomes: set[str], proprio: str) -> str:
    por_modulo: dict[str, list[str]] = {}
    for nome in sorted(nomes):
        modulo = MAPA.get(nome)
        if modulo is None or nome in PROPRIOS[proprio]:
            continue
        por_modulo.setdefault(modulo, []).append(nome)

    linhas: list[str] = []
    if any(n in nomes for n in ("dataclass",)):
        linhas.append("from dataclasses import dataclass")
    if "datetime" in nomes:
        linhas.append("from datetime import datetime")

    locais = sorted(m for m in por_modulo if m.startswith(".") and m != ".")
    for modulo in locais:
        linhas.append(_from_import(modulo, por_modulo[modulo]))
    if "." in por_modulo:
        linhas.append("from . import " + ", ".join(por_modulo["."]))
    for modulo in sorted(m for m in por_modulo if not m.startswith(".")):
        linhas.append(_from_import(modulo, por_modulo[modulo]))
    return "\n".join(linhas) + "\n"


def _from_import(modulo: str, nomes: list[str]) -> str:
    if len(nomes) == 1:
        return f"from {modulo} import {nomes[0]}"
    corpo = "".join(f"    {nome},\n" for nome in nomes)
    return f"from {modulo} import (\n{corpo})"


def montar_modulo(nome: str, linhas: list[str]) -> str:
    corpo = "\n\n".join(fatia(linhas, faixa).rstrip("\n") for faixa in FATIAS[nome])
    usados = nomes_usados(corpo)
    texto = (
        DOCSTRINGS[nome]
        + "from __future__ import annotations\n\n"
        + imports_para(usados, nome)
        + "\n\n"
        + corpo
        + "\n"
    )
    return texto


def montar_dna_analysis(linhas: list[str]) -> str:
    docstring = fatia(linhas, (1, 41))
    corpo = "\n\n".join(
        fatia(linhas, faixa).rstrip("\n") for faixa in BLOCO_DNA_ANALYSIS[1:]
    )
    usados = nomes_usados(corpo)
    texto = docstring + "from __future__ import annotations\n\n"

    fachada = [
        "Dependencias",
        "_montar_diagrama",
        "_observacoes",
        "_observacao_estrutural",
        "_selo_da_endogamia",
    ]
    usados_com_fachada = usados | set(fachada) | {
        "build_ged_indexes", "match_candidates", "norm_name", "split_name_pt",
        "surnames_set", "top_given_tokens", "token_prefixes", "drop_short_tokens",
        "surname_core_tokens", "soft_prefix_jaccard", "strip_bad_utf", "demojibake",
    }
    texto += imports_para(usados_com_fachada, "dna_analysis")
    texto += (
        "\n# Reexportacoes de compatibilidade. Os instrumentos congelados de\n"
        "# `_reversa_sdd/parity/` e as sondas de bug importam estes nomes daqui, e a\n"
        "# linha de `analise-dna/requirements.md` que aponta `_montar_diagrama` e\n"
        "# `_observacoes` para este arquivo continua valida por este caminho.\n"
    )
    texto += "\n\n" + corpo + "\n"
    return texto


def main() -> int:
    texto = ALVO.read_text(encoding="utf-8")
    linhas = texto.splitlines(keepends=True)

    SAIDA.mkdir(parents=True, exist_ok=True)
    total = 0
    for nome in FATIAS:
        novo = montar_modulo(nome, linhas)
        compile(novo, nome, "exec")
        destino = SAIDA / f"{nome}.py"
        destino.write_bytes(novo.encode("utf-8"))
        total += len(novo.splitlines())
        print(f"  {nome:30s} {len(novo.splitlines()):5d} linhas")

    novo_dna = montar_dna_analysis(linhas)
    compile(novo_dna, "dna_analysis", "exec")
    (SAIDA / "dna_analysis.py").write_bytes(novo_dna.encode("utf-8"))
    print(f"  {'dna_analysis':30s} {len(novo_dna.splitlines()):5d} linhas")
    total += len(novo_dna.splitlines())
    print(f"total: {total} linhas em 8 arquivos (antes: {len(linhas)} em 1)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

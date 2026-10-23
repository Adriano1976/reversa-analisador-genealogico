"""Fase 1 da OPP-20261023-ORQA, gerada fora do projeto.

Le `src/core/dna_analysis.py` e escreve `before-after/depois.py` com:

1. `_ContextoDaAnalise`, o Parameter Object com os 13 campos que o laco por kit
   consumia do escopo de `dna_analysis`;
2. `_dossie` promovida de closure para funcao de modulo, operando o cache que
   passou a morar no contexto;
3. `_cartao_do_kit` com as 370 linhas do laco, movidas por tokenize (so NAME),
   de modo que comentarios e strings nao sao tocados;
4. o laco de `dna_analysis` reduzido a chamada, com o `continue` virando
   retorno do caso "sem candidato".

Nao toca no projeto. Roda da raiz:  python <este arquivo>
"""
from __future__ import annotations

import io
import pathlib
import sys
import tokenize

RAIZ = pathlib.Path(__file__).resolve().parents[4]
ALVO = RAIZ / "src" / "core" / "dna_analysis.py"
SAIDA = pathlib.Path(__file__).resolve().parent / "before-after" / "depois.py"

LINHA_INICIO_CORPO = 670   # 1-based, primeira linha do corpo do laco
LINHA_FIM_CORPO = 1037     # 1-based, ultima linha (`})` do append)
LINHA_FIM_S1 = 641         # `sem_candidatos = []`
LINHA_INICIO_S2 = 651      # primeiro comentario da costura ULVW
LINHA_FIM_S2 = 667         # linha em branco antes do `for`
LINHA_INICIO_S3 = 1038     # linha em branco depois do append

MAPA = {
    "analisador_de_dna": "contexto.analisador",
    "arvore": "contexto.arvore",
    "root_id": "contexto.root_id",
    "ged_index": "contexto.ged_index",
    "surname_index": "contexto.surname_index",
    "features": "contexto.features",
    "dominio": "contexto.dominio",
    "ano_base": "contexto.ano_base",
    "intervalo_de_geracao": "contexto.intervalo_de_geracao",
    "candidatos_fixos": "contexto.candidatos_fixos",
    "documental_por_pessoa": "contexto.documental_por_pessoa",
    "deps": "contexto.deps",
}


def reescrever_nomes(texto: str, mapa: dict[str, str]) -> tuple[str, int]:
    """Troca apenas tokens NAME. Comentarios e strings ficam intactos."""
    trocas = []
    for token in tokenize.generate_tokens(io.StringIO(texto).readline):
        if token.type == tokenize.NAME and token.string in mapa:
            trocas.append((token.start, token.end, mapa[token.string]))
    linhas = texto.splitlines(keepends=True)
    for (li, ci), (lf, cf), novo in reversed(trocas):
        if li != lf:
            raise SystemExit(f"token NAME multilinha em {li}:{ci}")
        linha = linhas[li - 1]
        linhas[li - 1] = linha[:ci] + novo + linha[cf:]
    return "".join(linhas), len(trocas)


def dedent(texto: str, espacos: int) -> str:
    saida = []
    for linha in texto.splitlines(keepends=True):
        if linha.strip() and linha.startswith(" " * espacos):
            saida.append(linha[espacos:])
        else:
            saida.append(linha)
    return "".join(saida)


CONTEXTO = '''@dataclass(frozen=True, slots=True)
class _ContextoDaAnalise:
    """O que a analise de DNA consome igual em todo kit, mais os dois caches.

    A classe existe por uma razao medida: o laco por kit capturava dezoito nomes
    do escopo de `dna_analysis`. Extrair o passo por kit sem ela produziria uma
    assinatura de dezoito parametros, que e o mesmo acoplamento com outra roupa.

    Congelada de proposito: os campos nao sao reatribuidos. Os dois dicionarios
    de cache (`documental_por_pessoa` e `dossie_por_nome`) sao preenchidos na
    primeira consulta e reaproveitados pelos kits seguintes, e e isso que evita
    repetir a varredura de cerca de 35 mil nomes a cada cartao.

    Nao e agregado de dominio: nao guarda invariante, nao decide nada e nao
    reifica o casamento nem a busca. E o mesmo formato que `core.endogamia` ja
    usa nos seus value objects.
    """

    arvore: tuple
    root_id: str
    deps: Dependencias
    ged_index: dict
    surname_index: dict
    features: dict
    dominio: dict
    ano_base: int
    intervalo_de_geracao: int
    analisador: DNAAnalyzer
    candidatos_fixos: dict
    documental_por_pessoa: dict
    dossie_por_nome: dict


'''

DOSSIE = '''def _dossie(contexto: _ContextoDaAnalise, nome: str, candidatos) -> dict:
    """Dossie de homonimos, uma vez por nome (a varredura custa ~35k nomes).

    Era uma closure de `dna_analysis`. Virou funcao de modulo porque o cache
    passou a viver no contexto: uma closure sobre uma variavel local de uma
    funcao de 539 linhas nao tinha como ser exercitada sozinha.
    """
    if nome not in contexto.dossie_por_nome:
        contexto.dossie_por_nome[nome] = homonym_dossier(
            contexto.arvore, nome, similar_ids=candidatos)
    return contexto.dossie_por_nome[nome]


'''

CABECALHO_CARTAO = '''def _cartao_do_kit(
    contexto: _ContextoDaAnalise,
    por_kit: dict,
    chave_kit: str,
    kit: dict,
    avisos_deste_cartao: list,
) -> tuple[dict | None, dict | None, EvidenciaMitigada]:
    """Um kit vira cartao, ou vira descarte quando nao ha candidato.

    Devolve `(cartao, descarte, evidencia_mitigada)`: exatamente um dos dois
    primeiros e `None`. O terceiro volta sempre porque o cartao sem
    correspondencia, montado depois do laco, precisa dele.

    As dezoito coisas que o corpo consumia do escopo de `dna_analysis` chegam
    por `contexto`; o que muda de um kit para outro chega por parametro.
    """
'''

NOVO_LACO = '''    # O contexto carrega o que nao muda entre kits e os dois caches que
    # sobrevivem de um cartao para o outro: o parentesco documental por pessoa e
    # o dossie de homonimos. Montado UMA vez, e depois do ano de referencia e do
    # intervalo de geracao, que sao entradas dele.
    contexto = _ContextoDaAnalise(
        arvore=arvore,
        root_id=root_id,
        deps=deps,
        ged_index=ged_index,
        surname_index=surname_index,
        features=features,
        dominio=dominio,
        ano_base=ano_base,
        intervalo_de_geracao=intervalo_de_geracao,
        analisador=analisador_de_dna,
        candidatos_fixos=candidatos_fixos,
        documental_por_pessoa={},
        dossie_por_nome={},
    )

    for chave_nome, por_kit in evidencias.items():
        for chave_kit, kit in por_kit.items():
            avisos_deste_cartao = [aviso for aviso in avisos_de_cartao
                                   if aviso.get("chave_nome") == chave_nome
                                   and aviso.get("chave_kit") == chave_kit]

            cartao, descarte, evidencia_mitigada = _cartao_do_kit(
                contexto, por_kit, chave_kit, kit, avisos_deste_cartao)
            if cartao is not None:
                results_list.append(cartao)
                continue

            skipped_matches.append(descarte)
            # FEATURE 039/E002: o mesmo item pode virar cartao na lista de resultados,
            # com o tratamento de "Parentesco documental nao encontrado". A lista
            # completa de descartes continua intacta; o cartao e' uma leitura dela.
            sem_candidatos.append({
                "kit": kit,
                "chave_nome": chave_nome,
                "chave_kit": chave_kit,
                "por_kit": por_kit,
                "evidencia_mitigada": evidencia_mitigada,
                "descarte": descarte,
                "avisos": avisos_deste_cartao,
            })
'''


def main() -> int:
    original = ALVO.read_text(encoding="utf-8")
    linhas = original.splitlines(keepends=True)

    corpo_bruto = "".join(linhas[LINHA_INICIO_CORPO - 1 : LINHA_FIM_CORPO])
    if "results_list.append({" not in corpo_bruto:
        raise SystemExit("ABORTA: o corpo nao termina no append do cartao")
    if linhas[LINHA_FIM_CORPO - 1].strip() != "})":
        raise SystemExit(f"ABORTA: linha {LINHA_FIM_CORPO} nao e o fecho do append")

    corpo = dedent(corpo_bruto, 8)
    corpo, trocas = reescrever_nomes(corpo, MAPA)
    print(f"nomes reescritos por tokenize: {trocas}")

    alvo_dossie = '_dossie(kit["person_name_csv"], candidate_pids)'
    if corpo.count(alvo_dossie) != 1:
        raise SystemExit("ABORTA: chamada de _dossie nao encontrada uma vez")
    corpo = corpo.replace(alvo_dossie, f"_dossie(contexto, {alvo_dossie[len('_dossie('):-1]})")

    linhas_corpo = corpo.splitlines(keepends=True)

    i_avisos = next(
        (
            i
            for i, l in enumerate(linhas_corpo)
            if l.strip().startswith(
                "avisos_deste_cartao = [aviso for aviso in avisos_de_cartao"
            )
        ),
        None,
    )
    if i_avisos is None:
        raise SystemExit("ABORTA: filtro de avisos por cartao nao encontrado")
    i_fim_avisos = next(
        i
        for i in range(i_avisos, len(linhas_corpo))
        if 'and aviso.get("chave_kit") == chave_kit]' in linhas_corpo[i]
    )
    fim = i_fim_avisos + 1
    if fim < len(linhas_corpo) and not linhas_corpo[fim].strip():
        fim += 1
    del linhas_corpo[i_avisos:fim]
    corpo = "".join(linhas_corpo)
    print("filtro de avisos movido para o chamador")

    i_skip = next(
        (i for i, l in enumerate(linhas_corpo) if l.strip() == "skipped_matches.append(descarte)"),
        None,
    )
    i_cont = next(
        (i for i, l in enumerate(linhas_corpo) if l.strip() == "continue"),
        None,
    )
    if i_skip is None or i_cont is None or i_skip > i_cont:
        raise SystemExit("ABORTA: bloco do descarte nao localizado")
    linhas_corpo[i_skip : i_cont + 1] = [
        "        return None, descarte, evidencia_mitigada\n"
    ]

    i_append = next(
        i for i, l in enumerate(linhas_corpo) if l.strip() == "results_list.append({"
    )
    linhas_corpo[i_append] = linhas_corpo[i_append].replace("results_list.append({", "return {")

    ultima = len(linhas_corpo) - 1
    if linhas_corpo[ultima].strip() != "})":
        raise SystemExit(f"ABORTA: ultima linha do corpo e {linhas_corpo[ultima]!r}")
    linhas_corpo[ultima] = "    }, None, evidencia_mitigada\n"

    corpo_final = "".join(linhas_corpo)
    if "skipped_matches" in corpo_final or "sem_candidatos" in corpo_final:
        raise SystemExit("ABORTA: acumuladores do chamador ficaram no corpo extraido")
    if "chave_nome" in corpo_final:
        raise SystemExit("ABORTA: o corpo extraido ainda usa chave_nome")

    novo = (
        "".join(linhas[:LINHA_FIM_S1])
        + "".join(linhas[LINHA_INICIO_S2 - 1 : LINHA_FIM_S2])
        + NOVO_LACO
        + "".join(linhas[LINHA_INICIO_S3 - 1 :])
    )

    substituicoes = [
        (
            "from datetime import datetime\n",
            "from dataclasses import dataclass\nfrom datetime import datetime\n",
        ),
        (
            "from .endogamia import CM_MINIMO_SEGMENTO, DNAAnalyzer, MENSAGEM_ENDEROGAMIA\n",
            "from .endogamia import (\n"
            "    CM_MINIMO_SEGMENTO,\n"
            "    DNAAnalyzer,\n"
            "    EvidenciaMitigada,\n"
            "    MENSAGEM_ENDEROGAMIA,\n"
            ")\n",
        ),
        (
            "        self.gerar_mermaid_da_sugestao = gerar_mermaid_da_sugestao\n\n\n\n"
            "def _montar_diagrama(",
            "        self.gerar_mermaid_da_sugestao = gerar_mermaid_da_sugestao\n\n\n"
            + CONTEXTO
            + "def _montar_diagrama(",
        ),
        (
            "\n\ndef dna_analysis(csv_path: str,",
            "\n\n" + DOSSIE + CABECALHO_CARTAO + "\n" + corpo_final + "\n\ndef dna_analysis(csv_path: str,",
        ),
    ]
    for antigo, novo_texto in substituicoes:
        if novo.count(antigo) != 1:
            raise SystemExit(f"ABORTA: ancora nao unica: {antigo[:60]!r}")
        novo = novo.replace(antigo, novo_texto)

    compile(novo, str(SAIDA), "exec")
    SAIDA.write_bytes(novo.encode("utf-8"))
    print(f"depois: {SAIDA} ({len(novo.splitlines())} linhas, compila)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

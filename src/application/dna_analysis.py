"""Caso de uso da analise de DNA (`T013`; `RF-01`, `RF-14`, `RF-20`).

Chama o fluxo do nucleo e devolve resultado tipado. Nao ha decisao de negocio
aqui: matching, ordem de apresentacao, cM e confronto continuam todos em
`core.dna_analysis` (`RN-01`).

## Por que o caminho do CSV entra pronto, e nao a referencia

O adaptador de entrada grava o CSV pelo port de armazenamento e passa o
**caminho** devolvido, que e o que `RF-09` fixa: `guardar` devolve o caminho
completo do arquivo e nunca um nome a ser remontado. O caminho e o que o fluxo do
nucleo precisa para ler — `deps.read_csv` recebe caminho.

## A persistencia historica (feature 008; `D-01`, `D-15`, `T015`)

O caso de uso passou a **receber a porta** `RegistroDeAnalises` e a chama-la
**depois** de o nucleo ter terminado. `registro` tem valor padrao `None`, e `None`
**e** o estado desabilitado da `D-02`: sem `DATABASE_URL` a borda monta um
registrador nulo, o comportamento e o de antes da feature, e a tela nao muda um
byte.

A projecao do resultado para o payload da porta vive **aqui**, e e **pura**: ela
le o que o nucleo devolveu e nada mais — nao chama funcao do nucleo, nao recalcula
cM, nao reordena e nao formata (`D-15`).
"""
from __future__ import annotations

import os
from dataclasses import dataclass

from core.dna_analysis import dna_analysis as fluxo_dna
from ports import (
    AnaliseParaRegistrar,
    ConexaoDaAnalise,
    DescartadoDaAnalise,
    KitDaAnalise,
    PessoaDaAnalise,
)


@dataclass(frozen=True)
class ResultadoDeAnalise:
    """Resultado da analise. Os campos nao sao nomes de campo de template (`RF-20`).

    O fluxo de DNA **nao** tem desfecho de tres valores: ele ou levanta excecao de
    dominio, ou devolve resultado com mensagem de contrato.

    `aviso_de_persistencia` e o **unico** campo que a feature 008 acrescentou, e ele
    tem valor padrao para que as construcoes existentes continuem validas. Nulo
    significa "nada a avisar" — gravado, ou persistencia desabilitada —, e nesse
    caso a tela nao renderiza nada (`D-02`, `RF-17`).
    """

    resultados: list
    descartados: list
    mensagem: str
    aviso_de_persistencia: str | None = None


# ---------------------------------------------------------------------------
# A projecao. Publica para poder ser exercitada sem banco: ela e pura, e o teste
# dela nao precisa de `DATABASE_URL` (`B003` da auditoria de 2026-10-08).
# ---------------------------------------------------------------------------


def _juntar(por_xref: dict, pessoa: PessoaDaAnalise | None) -> None:
    """Acrescenta uma pessoa ao retrato, e a ficha COMPLETA vence a identificacao.

    A mesma pessoa pode ser o match de uma conexao e um no do caminho de outra. Se
    a versao completa chegasse depois da incompleta e fosse descartada, os dados
    dela se perderiam — e o `analysis_person.completa` mentiria.
    """
    if pessoa is None or not pessoa.xref:
        return
    anterior = por_xref.get(pessoa.xref)
    if anterior is None:
        por_xref[pessoa.xref] = pessoa
    elif pessoa.completa and not anterior.completa:
        por_xref[pessoa.xref] = pessoa
    elif not anterior.completa and not pessoa.completa and anterior.nome is None:
        por_xref[pessoa.xref] = pessoa


def _ficha(ficha: dict | None, completa: bool) -> PessoaDaAnalise | None:
    """`person_summary` do resultado vira `PessoaDaAnalise`. Sem `id`, devolve `None`."""
    ficha = ficha or {}
    if not ficha.get("id"):
        return None
    return PessoaDaAnalise(
        xref=ficha["id"],
        nome=ficha.get("name"),
        sexo=ficha.get("sex"),
        nascimento=ficha.get("birth"),
        local_nascimento=ficha.get("birth_place"),
        falecimento=ficha.get("death"),
        completa=completa,
    )


def _papeis_do_caminho(documentary: dict) -> tuple[tuple[str, str], ...]:
    """Pares `(xref, papel)` do caminho documental, na ordem (`match_path_node`).

    O papel e **derivado**, e nao lido: o resultado do nucleo carrega o caminho
    como lista de identificadores e nomes (`path.ids`, `path.names`) e nao diz qual
    no e ascendente e qual e descendente. A derivacao usa o ancestral comum como
    divisor — ate ele sobe-se, depois dele desce-se.

    Quando o ancestral comum **nao** esta no caminho, o corte cai no **penultimo** no: o
    ultimo e sempre a pessoa alcancada, e chegar nela e descer. E um recuo
    declarado, nao um palpite silencioso — e `afinidade` nunca aparece aqui, porque
    quem atribui esse estado e `path_search.py`, e nao o fluxo de DNA
    (`state-machines.md#4`).

    O `max(0, ...)` cobre o caminho de um no so: sem segundo no, nao ha descida a
    marcar, e o unico no fica ascendente.
    """
    caminho = documentary.get("path") or {}
    ids = caminho.get("ids") or []
    if not ids:
        return ()
    mrca = (documentary.get("common_ancestor") or {}).get("id")
    corte = ids.index(mrca) if mrca in ids else max(0, len(ids) - 2)
    return tuple(
        (xref, "descendente" if posicao > corte else "ascendente")
        for posicao, xref in enumerate(ids)
    )


def _kits(evidence: dict, comparison: dict) -> tuple[KitDaAnalise, ...]:
    """Um `KitDaAnalise` por kit, com o cM **deste** kit (`RF-05`, `RN-06`).

    O pareamento entre metadados e veredito e **por indice**, e nao por rotulo:
    `hypotheses_for_evidence` percorre `evidence["kits"]` na ordem, e
    `evidence_comparison.compare` monta `per_kit` com `zip(hypotheses, avaliacoes)`.
    Como as duas listas seguem a mesma ordem, dois kits com o mesmo nome — ou ambos
    sem kit — nao se confundem. `source` vem da evidencia, porque `per_kit` nao o
    carrega.

    Quando `per_kit` esta **vazio**, o confronto terminou antes de avaliar kit por
    kit — acontece em INCONCLUSIVO por falta de DNA, de caminho ou de janela
    publicada. Nesse caso o kit herda o estado **final** da conexao, que e o que a
    tela mostra; e `status_note` fica nulo, porque nao houve avaliacao por kit para
    justificar um texto.
    """
    kits = (evidence or {}).get("kits") or []
    avaliacoes = (comparison or {}).get("per_kit") or []
    final = (comparison or {}).get("status") or "INCONCLUSIVO"
    blocos = []
    for posicao, kit in enumerate(kits):
        avaliacao = avaliacoes[posicao] if posicao < len(avaliacoes) else {}
        blocos.append(KitDaAnalise(
            ordinal=posicao,
            kit=kit.get("kit"),
            source=kit.get("source"),
            total_cm=kit.get("total_cm"),
            segment_count=kit.get("segment_count"),
            largest_segment_cm=kit.get("largest_segment_cm"),
            status=avaliacao.get("status") or final,
            status_note=avaliacao.get("note"),
        ))
    return tuple(blocos)


def _pessoas(resultados) -> tuple[tuple[PessoaDaAnalise, ...], str | None]:
    """Retrato das pessoas que a analise usou, uma vez cada (`RF-04`, `RN-04`).

    Devolve tambem a raiz resolvida — `documentary.person_a.id` da primeira conexao
    —, que e o unico lugar onde ela aparece no resultado: o nucleo nao a devolve em
    campo proprio, e resolve-la aqui outra vez duplicaria a regra de resolucao por
    nome (`D-15`).
    """
    por_xref: dict[str, PessoaDaAnalise] = {}
    raiz = None
    for resultado in resultados:
        documentary = resultado.get("documentary") or {}
        if raiz is None:
            raiz = (documentary.get("person_a") or {}).get("id")
        _juntar(por_xref, _ficha(documentary.get("person_a"), completa=True))
        _juntar(por_xref, _ficha(documentary.get("person_b"), completa=True))

        caminho = documentary.get("path") or {}
        ids = caminho.get("ids") or []
        nomes = caminho.get("names") or []
        for posicao, xref in enumerate(ids):
            if xref in por_xref:
                continue
            nome = nomes[posicao] if posicao < len(nomes) else None
            _juntar(por_xref, PessoaDaAnalise(xref=xref, nome=nome, completa=False))
    return tuple(por_xref.values()), raiz


def _conexao(ordinal: int, resultado: dict) -> ConexaoDaAnalise:
    """Uma conexao projetada. `ordinal` e a posicao na ordem APRESENTADA (`RN-08`)."""
    documentary = resultado.get("documentary") or {}
    comparison = resultado.get("comparison") or {}
    janela = comparison.get("expected_range") or {}
    return ConexaoDaAnalise(
        ordinal=ordinal,
        csv_name=resultado.get("csv_name") or "",
        matched_name=resultado.get("match_name") or "",
        matched_person_xref=(documentary.get("person_b") or {}).get("id"),
        comparison_status=comparison.get("status") or "INCONCLUSIVO",
        comparison_label=comparison.get("label") or "",
        comparison_detail=comparison.get("detail") or "",
        documentary_status=documentary.get("status") or "not_found",
        total_cm=resultado.get("cm"),
        relationship_key=documentary.get("relationship_key"),
        relationship_label=documentary.get("label"),
        meioses=documentary.get("meioses"),
        mrca_xref=(documentary.get("common_ancestor") or {}).get("id"),
        comparison_method=comparison.get("method"),
        expected_low=janela.get("low"),
        expected_high=janela.get("high"),
        expected_average=janela.get("average"),
        causes=tuple(comparison.get("causes") or ()),
        observations=tuple(resultado.get("observations") or ()),
        kits=_kits(resultado.get("genetic_evidence") or {}, comparison),
        caminho=_papeis_do_caminho(documentary),
    )


def projetar_analise(resultados, descartados, mensagem: str,
                     referencia_da_arvore: str, referencia_do_csv: str,
                     root_name: str) -> AnaliseParaRegistrar:
    """Projeta o resultado do nucleo no payload da porta (`D-15`).

    Funcao **pura** e sem efeito: le o que o nucleo devolveu e nada mais. A ordem
    das conexoes e a ordem em que elas chegaram — que ja e a ordem de apresentacao
    decidida pelo nucleo —, e ela vira `result_ordinal` sem reordenacao nenhuma
    (`RN-08`, `E-01`).
    """
    pessoas, raiz = _pessoas(resultados)
    return AnaliseParaRegistrar(
        tree_ref=referencia_da_arvore,
        match_file_ref=referencia_do_csv,
        root_name_input=root_name,
        message=mensagem,
        pessoas=pessoas,
        conexoes=tuple(_conexao(i, r) for i, r in enumerate(resultados)),
        descartados=tuple(
            DescartadoDaAnalise(
                ordinal=i,
                csv_name=descartado.get("csv_name") or "",
                reason=descartado.get("motivo") or "não encontrado",
                kit=descartado.get("kit"),
                total_cm=descartado.get("cm"),
            )
            for i, descartado in enumerate(descartados)
        ),
        root_person_xref=raiz,
        accepted_count=len(resultados),
        skipped_count=len(descartados),
    )


def dna_analysis(caminho_do_csv: str, root_name: str, arvore, deps,
                 dono: str, referencia_da_arvore: str | None = None,
                 registro=None) -> ResultadoDeAnalise:
    """Executa a analise e devolve `ResultadoDeAnalise`.

    `dono` **nao** e usado para comportamento nesta onda (`RN-06`, `RF-08`): esta na
    assinatura como costura, e nenhum isolamento e implementado.

    `referencia_da_arvore` e `registro` tem valor padrao, e **`None` em qualquer um
    dos dois significa nao registrar** — o estado desabilitado da `D-02`. Sem a
    referencia da arvore nao ha o que gravar: ela e a chave de conteudo que o
    `RF-03` exige, e inventa-la aqui seria criar um identificador que nao existe.
    """
    resultados, descartados, mensagem = fluxo_dna(caminho_do_csv, root_name, deps, arvore)

    aviso = None
    if registro is not None and referencia_da_arvore:
        try:
            analise = projetar_analise(
                resultados, descartados, mensagem, referencia_da_arvore,
                os.path.basename(caminho_do_csv), root_name,
            )
            _, aviso = registro.registrar(analise, dono)
        except Exception as erro:
            # A `RN-13` vale para as DUAS metades: nem a projecao nem a gravacao
            # podem impedir o resultado de chegar a tela. Uma excecao aqui seria a
            # persistencia bloqueando a analise — exatamente o que ela nao pode.
            aviso = ("Histórico não registrado: falha ao preparar os dados "
                     f"({type(erro).__name__}: {erro}).")

    return ResultadoDeAnalise(
        resultados=resultados,
        descartados=descartados,
        mensagem=mensagem,
        aviso_de_persistencia=aviso,
    )


__all__ = ["ResultadoDeAnalise", "dna_analysis", "projetar_analise"]

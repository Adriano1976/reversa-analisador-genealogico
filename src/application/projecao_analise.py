"""Projeção pura do resultado do núcleo para o payload da porta (`D-15`, `ADR-33`).

`ProjetorDeAnalise` é o Mapper: **puro e sem efeito colateral**, lê o que o núcleo
devolveu e nada mais — não chama função do núcleo, não recalcula cM, não reordena e
não formata (`D-15`). Por isso é exercitável sem `DATABASE_URL` e sem nenhuma
dependência de infraestrutura (`B003` da auditoria de 2026-10-08).

`ProjetorDeAnalise.projetar` (ou a fachada `projetar_analise`) recebe o triplete bruto
(`resultados`, `descartados`, `mensagem`) mais os metadados de rastreabilidade e
devolve `AnaliseParaRegistrar`, o payload tipado da porta `RegistroDeAnalises`.
"""
from __future__ import annotations

from itertools import zip_longest
from typing import Any, cast

from ports import (
    AnaliseParaRegistrar,
    CandidatoDoDescarte,
    ConexaoDaAnalise,
    DescartadoDaAnalise,
    KitDaAnalise,
    PessoaDaAnalise,
)


class ProjetorDeAnalise:
    """Mapeia o resultado bruto do nucleo para o payload da porta (`D-15`, `ADR-33`).

    Padrao Mapper/Projector: encapsula a projecao dos dados brutos no payload de contrato
    tipado das portas. Nao mantem estado interno mutavel.
    """

    @staticmethod
    def _juntar(por_xref: dict, pessoa: PessoaDaAnalise | None) -> None:
        """Acrescenta uma pessoa ao retrato; a ficha COMPLETA vence a identificacao.

        A mesma pessoa pode ser match de uma conexao e no do caminho de outra: se a
        versao completa chegasse depois e fosse descartada, seus dados se perderiam e o
        `analysis_person.completa` mentiria.
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

    @staticmethod
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

    @staticmethod
    def _papeis_do_caminho(documentary: dict) -> tuple[tuple[str, str], ...]:
        """Pares `(xref, papel)` do caminho documental, na ordem (`match_path_node`).

        O papel e **derivado**, nao lido: o caminho chega como `path.ids` e `path.names`,
        sem dizer qual no e ascendente e qual e descendente. O ancestral comum divide:
        ate ele sobe-se, depois desce-se. Sem ele no caminho, o corte cai no
        **penultimo** no — o ultimo e sempre a pessoa alcancada, e chegar nela e descer.
        E um recuo declarado, nao um palpite silencioso; `afinidade` nunca aparece aqui,
        porque quem atribui esse estado e `path_search.py`, e nao o fluxo de DNA
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

    @classmethod
    def _kits(cls, evidence: dict, comparison: dict) -> tuple[KitDaAnalise, ...]:
        """Um `KitDaAnalise` por kit, com o cM **deste** kit (`RF-05`, `RN-06`).

        O pareamento entre metadados e veredito e **por indice**, nao por rotulo:
        `hypotheses_for_evidence` percorre `evidence[\"kits\"]` na ordem, e
        `evidence_comparison.compare` monta `per_kit` com `zip(hypotheses, avaliacoes)`.
        As duas listas seguem a mesma ordem, entao dois kits com o mesmo nome — ou ambos
        sem kit — nao se confundem; `source` vem da evidencia, porque `per_kit` nao o
        carrega.

        Com `per_kit` **vazio**, o confronto terminou antes de avaliar kit por kit
        (INCONCLUSIVO por falta de DNA, de caminho ou de janela publicada): o kit herda o
        estado **final** da conexao, que e o que a tela mostra, e `status_note` fica
        nulo, porque nao houve avaliacao por kit que justificasse um texto.
        """
        kits = (evidence or {}).get("kits") or []
        avaliacoes = (comparison or {}).get("per_kit") or []
        final = (comparison or {}).get("status") or "INCONCLUSIVO"
        return tuple(
            KitDaAnalise(
                ordinal=posicao,
                kit=kit.get("kit"),
                source=kit.get("source"),
                total_cm=kit.get("total_cm"),
                segment_count=kit.get("segment_count"),
                largest_segment_cm=kit.get("largest_segment_cm"),
                status=avaliacao.get("status") or final,
                status_note=avaliacao.get("note"),
            )
            for posicao, (kit, avaliacao) in enumerate(
                zip_longest(kits, avaliacoes[:len(kits)], fillvalue={})
            )
        )

    @classmethod
    def _pessoas(cls, resultados) -> tuple[tuple[PessoaDaAnalise, ...], str | None]:
        """Retrato das pessoas que a analise usou, uma vez cada (`RF-04`, `RN-04`).

        Devolve tambem a raiz resolvida: `documentary.person_a.id` da primeira conexao,
        unico lugar onde ela aparece no resultado — o nucleo nao a devolve em campo
        proprio, e resolve-la aqui duplicaria a regra de resolucao por nome (`D-15`).
        """
        por_xref: dict[str, PessoaDaAnalise] = {}
        raiz = None
        for resultado in resultados:
            documentary = resultado.get("documentary") or {}
            if raiz is None:
                raiz = (documentary.get("person_a") or {}).get("id")
            cls._juntar(por_xref, cls._ficha(documentary.get("person_a"), completa=True))
            cls._juntar(por_xref, cls._ficha(documentary.get("person_b"), completa=True))

            caminho = documentary.get("path") or {}
            ids = caminho.get("ids") or []
            nomes = caminho.get("names") or []
            for posicao, xref in enumerate(ids):
                if xref in por_xref:
                    continue
                nome = nomes[posicao] if posicao < len(nomes) else None
                cls._juntar(por_xref, PessoaDaAnalise(xref=xref, nome=nome, completa=False))
        return tuple(por_xref.values()), raiz

    @classmethod
    def _conexao(cls, ordinal: int, resultado: dict[str, Any]) -> ConexaoDaAnalise:
        """Uma conexao projetada. `ordinal` e a posicao na ordem APRESENTADA (`RN-08`)."""
        # O nucleo devolve dicionario nao tipado (`D-15`): o `Any` fica no limite da
        # projecao, e a garantia de que `person_b` existe e o filtro de
        # `sem_correspondencia` em `projetar`.
        documentary: dict[str, Any] = resultado.get("documentary") or {}
        comparison = resultado.get("comparison") or {}
        janela = comparison.get("expected_range") or {}
        return ConexaoDaAnalise(
            ordinal=ordinal,
            csv_name=resultado.get("csv_name") or "",
            matched_name=resultado.get("match_name") or "",
            # `person_b` existe em toda conexao que chega aqui: `projetar` filtra as
            # marcadas com `sem_correspondencia` (`E002`) e a tabela `match_result`
            # ainda exige a FK. O `cast` documenta a garantia — em runtime, um valor
            # ausente continua chegando ao banco e falhando como antes, e a `RN-13`
            # transforma a falha em aviso.
            matched_person_xref=cast(str, (documentary.get("person_b") or {}).get("id")),
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
            kits=cls._kits(resultado.get("genetic_evidence") or {}, comparison),
            caminho=cls._papeis_do_caminho(documentary),
        )

    @classmethod
    def projetar(
        cls,
        resultados,
        descartados,
        mensagem: str,
        referencia_da_arvore: str,
        referencia_do_csv: str,
        root_name: str,
    ) -> AnaliseParaRegistrar:
        """Projeta o resultado do nucleo no payload da porta (`D-15`).

        Operacao **pura** e sem efeito colateral: le o que o nucleo devolveu e nada mais;
        a ordem das conexoes e a de chegada — que ja e a ordem de apresentacao decidida pelo
        nucleo — e vira `result_ordinal` sem reordenacao nenhuma (`RN-08`, `E-01`).

        FEATURE 039/E002: o cartao sem correspondencia e' uma leitura de TELA. A tabela
        `match_result` exige `matched_person_xref` NOT NULL com FK para `analysis_person`,
        e nao ha pessoa na arvore para esses cartoes; eles continuam registrados em
        `skipped_match`, como descartes. Por isso a projecao os filtra antes de montar as
        conexoes; a tela continua com eles.
        """
        resultados = [r for r in resultados if not r.get("sem_correspondencia")]
        pessoas, raiz = cls._pessoas(resultados)
        return AnaliseParaRegistrar(
            tree_ref=referencia_da_arvore,
            match_file_ref=referencia_do_csv,
            root_name_input=root_name,
            message=mensagem,
            pessoas=pessoas,
            conexoes=tuple(cls._conexao(i, r) for i, r in enumerate(resultados)),
            descartados=tuple(
                DescartadoDaAnalise(
                    ordinal=i,
                    csv_name=descartado.get("csv_name") or "",
                    reason=descartado.get("motivo") or "não encontrado",
                    # Feature 038: a causa e o detalhe viajam ao lado do texto, e nao no lugar
                    # dele. Ausentes nas recusas que nao vem do bloco de semelhanca.
                    reason_code=descartado.get("motivo_codigo") or "",
                    detail=descartado.get("motivo_detalhe") or "",
                    kit=descartado.get("kit"),
                    total_cm=descartado.get("cm"),
                    # Feature 034: a quem a arvore oferecia. Vazio quando a arvore nao
                    # tem ninguem compativel, o que separa "revisavel" de "sem saida".
                    candidatos=tuple(
                        CandidatoDoDescarte(
                            nome=candidato.get("nome") or "",
                            prenome=candidato.get("prenome"),
                            nota=candidato.get("nota"),
                            nascimento=candidato.get("nascimento"),
                            compativel=bool(candidato.get("compativel")),
                        )
                        for candidato in (descartado.get("candidatos") or ())
                    ),
                )
                for i, descartado in enumerate(descartados)
            ),
            root_person_xref=raiz,
            accepted_count=len(resultados),
            skipped_count=len(descartados),
        )


# Fachada pública e aliases de compatibilidade


def projetar_analise(
    resultados,
    descartados,
    mensagem: str,
    referencia_da_arvore: str,
    referencia_do_csv: str,
    root_name: str,
) -> AnaliseParaRegistrar:
    """Fachada funcional para ProjetorDeAnalise.projetar (`D-15`)."""
    return ProjetorDeAnalise.projetar(
        resultados=resultados,
        descartados=descartados,
        mensagem=mensagem,
        referencia_da_arvore=referencia_da_arvore,
        referencia_do_csv=referencia_do_csv,
        root_name=root_name,
    )


# Preservação de compatibilidade com chamadas internas ou testes
_juntar = ProjetorDeAnalise._juntar
_ficha = ProjetorDeAnalise._ficha
_papeis_do_caminho = ProjetorDeAnalise._papeis_do_caminho
_kits = ProjetorDeAnalise._kits
_pessoas = ProjetorDeAnalise._pessoas
_conexao = ProjetorDeAnalise._conexao

__all__: list[str] = ["ProjetorDeAnalise", "projetar_analise"]

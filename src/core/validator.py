"""Validação temporal de uma comparação DNA × GEDCOM.

O que este módulo responde: para cada comparação entre um kit de DNA e uma pessoa do
GEDCOM, ele devolve um dos três estados: ``VALIDADO`` — a linha documental é temporalmente
viável, o cM é compatível e não há contradição detectável; ``INCONCLUSIVO`` — falta dado, a
data é estimada, o cM não tem cobertura publicada, a identidade é ambígua ou há afinidade
no caminho; ou ``ERRO CRONICO / QUEBRA DE LINHA`` — há uma contradição biológica ou temporal
demonstrável: salto impossível, MRCA posterior ao descendente, idade por lado fora de
12–70, cM incompatível com a profundidade, MRCA fora da janela ou doador vivo em linha
incompatível.

``VALIDADO`` **não** é prova de parentesco: é a ausência de contradição com os dados
disponíveis. A decisão de negócio do projeto continua a mesma — o cM nunca afirma
parentesco sozinho e o DNA nunca reescreve o vínculo do GEDCOM.

De onde vêm os números: **12–70 anos por salto** em
`documentary_relationship.IDADE_MINIMA_GENITOR` e `IDADE_MAXIMA_GENITOR`, a mesma faixa que
`hop_evidence` já usa; **122 anos** em `janela_de_vida.IDADE_IMPOSSIVEL`, o recorde humano
verificado, acima do qual a pessoa não pode estar viva; **25 anos por geração** como prior
declarado do projeto para quando a árvore tem menos de 3 intervalos pai-filho datados — a
literatura não tem consenso e o intervalo varia por sexo e população: Fenner, J. N.
*Cross-cultural estimation of the human generation interval for use in genetics-based
population divergence studies*. Am J Phys Anthropol. 2005;128(2):415–423.
DOI: 10.1002/ajpa.20188. Consultado em 2026-10-18; e a tabela de cM do Shared cM Project
4.0, em `core.relationship_hypotheses`.

A coluna `meioses` da tabela SCP 4.0 não é o total do caminho: `SCP40_ROWS` traz, para
`1C`, `meioses = 2`, mas o caminho entre dois primos de 1º grau tem **4** saltos pai-filho
(2 de cada lado). O valor da tabela é a chave da relação, não o total que
`documentary_relationship` devolve; para estimar gerações, este módulo deriva o total da
chave (`1C` → 4, `2C` → 6, `1C1R` → 5) com `_meioses_totais_da_relacao`. Usar a coluna crua
subestimaria a profundidade pela metade.

Pureza: o módulo não lê arquivo, não consulta relógio e não usa estado global. A árvore não
entra aqui: a fachada (`application.validacao`) entrega datas, `degrees`, `meioses`,
`common_ancestor` e o kit já prontos, e o mesmo vale para `ano_referencia`, que entra por
parâmetro.
"""
from __future__ import annotations

import re
from dataclasses import dataclass
from statistics import median

from .documentary_relationship import (
    IDADE_MAXIMA_GENITOR,
    IDADE_MINIMA_GENITOR,
    parse_year,
)
from .janela_de_vida import IDADE_IMPOSSIVEL, data_imprecisa
from .relationship_hypotheses import possible_relationships

VALIDADO = "VALIDADO"
INCONCLUSIVO = "INCONCLUSIVO"
ERRO_CRONICO = "ERRO CRONICO / QUEBRA DE LINHA"

#: Prior declarado para quando a árvore não tem amostra suficiente. Ver o docstring.
INTERVALO_DE_GERACAO_PADRAO = 25.0

#: Tolerância da profundidade documental contra a envoltória publicada.
TOLERANCIA_DE_MEIOSES = 2

#: Tolerância da janela do MRCA, em gerações.
TOLERANCIA_DE_GERACOES = 2

_SEVERIDADE_ORDEM = {"critico": 0, "atencao": 1, "informativo": 2}
_STATUS_ORDEM = {ERRO_CRONICO: 0, INCONCLUSIVO: 1, VALIDADO: 2}

#: Relações diretas e laterais cujo total de meioses é o próprio valor da tabela.
_MEIOSES_POR_CHAVE = {
    "PARENT_CHILD": 1,
    "SIBLINGS": 2,
    "HALF_SIBLINGS": 2,
    "GRANDPARENT": 2,
    "AUNT_UNCLE": 3,
    "DIRECT_3": 3,
    "GREAT_AUNT_1": 4,
    "GREAT_AUNT_2": 5,
}


@dataclass(frozen=True)
class MrcaEstimado:
    """Estimativa do MRCA derivada do cM (e, quando houver, do `MRCA` do kit)."""

    ano: int | None
    ano_min: int | None
    ano_max: int | None
    geracoes: float | None
    metodo: str | None

    def as_dict(self) -> dict:
        return {
            "ano": self.ano,
            "ano_min": self.ano_min,
            "ano_max": self.ano_max,
            "geracoes": self.geracoes,
            "metodo": self.metodo,
        }


@dataclass(frozen=True)
class ComparacaoParaValidar:
    """Entrada do núcleo. A árvore já foi reduzida a estes valores pela fachada."""

    doador: dict
    match: dict
    documental: dict
    kit: dict
    ano_referencia: int
    intervalo_de_geracao: float | None = None
    comparacao_existente: dict | None = None


def _ano(valor) -> int | None:
    """Ano a partir de `int` ou do texto GEDCOM (`ABT 1852`, `1900`)."""
    if isinstance(valor, bool):
        return None
    if isinstance(valor, int):
        return valor
    return parse_year(valor)


def _float_positivo(valor) -> float | None:
    """Converte para float e devolve `None` quando não é um número positivo."""
    try:
        numero = float(valor)
    except (TypeError, ValueError):
        return None
    return numero if numero > 0 else None


def _meioses_totais_da_relacao(relacao: dict) -> int | None:
    """Total de saltos pai-filho da relação, derivado da chave canônica.

    A coluna `meioses` de `SCP40_ROWS` é a chave da relação, não o total do
    caminho (ver o docstring do módulo). Aqui a chave é traduzida de volta para
    o total que `documentary_label` devolveria.
    """
    chave = (relacao or {}).get("key")
    if not chave:
        return None
    if chave in _MEIOSES_POR_CHAVE:
        return _MEIOSES_POR_CHAVE[chave]

    meio_primo = re.fullmatch(r"HALF_(\d+)C", chave)
    if meio_primo:
        return 2 * (int(meio_primo.group(1)) + 1)

    primo = re.fullmatch(r"(\d+)C(?:(\d+)R)?", chave)
    if primo:
        grau = int(primo.group(1))
        removidos = int(primo.group(2) or 0)
        return 2 * (grau + 1) + removidos

    direto = re.fullmatch(r"DIRECT_(\d+)", chave)
    if direto:
        return int(direto.group(1))

    tio_avo = re.fullmatch(r"GREAT_AUNT_(\d+)", chave)
    if tio_avo:
        return int(tio_avo.group(1)) + 3

    return None


def _candidatos(cm) -> list:
    """Relações publicadas que contêm o cM, ou lista vazia."""
    numero = _float_positivo(cm)
    if numero is None:
        return []
    return list(possible_relationships(numero).get("possible_relationships") or [])


def _totais_das_relacoes(relacoes) -> list[int]:
    totais = []
    for relacao in relacoes or []:
        total = _meioses_totais_da_relacao(relacao)
        if total is not None:
            totais.append(total)
    return totais


def estimar_mrca(cm, nasc_doador, mrca_do_kit=None, relacoes=None,
                 intervalo_de_geracao=None) -> MrcaEstimado | None:
    """Estima o ano do MRCA a partir do cM do kit.

    Ordem: o `MRCA` do próprio kit (gerações por lado, quando o relatório traz a
    coluna); na falta dele, a mediana das meioses **totais** das relações
    publicadas que contêm o cM, dividida por 2. A janela vem do mínimo e do
    máximo dessas meioses; quando só o `MRCA` do kit existe, é o centro ± 2
    gerações. Sem cM ou sem nascimento do doador, devolve `None`.
    """
    ano_doador = _ano(nasc_doador)
    if ano_doador is None:
        return None

    numero_cm = _float_positivo(cm)
    if numero_cm is None:
        return None

    if relacoes is None:
        relacoes = _candidatos(numero_cm)
    totais = _totais_das_relacoes(relacoes)

    mrca_kit = _float_positivo(mrca_do_kit)
    if mrca_kit is not None:
        geracoes = mrca_kit
        metodo = "mrca_do_kit"
    elif totais:
        geracoes = median(totais) / 2
        metodo = "scp40:mediana"
    else:
        return None

    intervalo = _float_positivo(intervalo_de_geracao) or INTERVALO_DE_GERACAO_PADRAO
    ano = round(ano_doador - geracoes * intervalo)

    if totais:
        ano_min = round(ano_doador - (max(totais) / 2) * intervalo)
        ano_max = round(ano_doador - (min(totais) / 2) * intervalo)
    else:
        margem = TOLERANCIA_DE_GERACOES * intervalo
        ano_min = round(ano - margem)
        ano_max = round(ano + margem)

    return MrcaEstimado(ano=ano, ano_min=ano_min, ano_max=ano_max,
                        geracoes=geracoes, metodo=metodo)


def _codigo(codigo: str, severidade: str, mensagem: str) -> dict:
    return {"codigo": codigo, "severidade": severidade, "mensagem": mensagem}


def _resultado(status: str, motivo: str, codigos: dict, *, kit, cm, estimativa,
               mrca, mrca_ano, mrca_impreciso, a_up, b_up, meioses,
               comparacao_existente) -> dict:
    ordenados = sorted(codigos.values(),
                       key=lambda item: (_SEVERIDADE_ORDEM[item["severidade"]], item["codigo"]))
    total = meioses if isinstance(meioses, int) else a_up + b_up
    return {
        "status": status,
        "motivo": motivo,
        "codigos": ordenados,
        "kit": kit.get("kit"),
        "cm": cm,
        "mrca_estimado": estimativa.as_dict() if estimativa else None,
        "mrca_documentado": ({
            "id": mrca.get("id"),
            "nome": mrca.get("name"),
            "ano": mrca_ano,
            "impreciso": mrca_impreciso,
        } if mrca else None),
        "geracoes_documentais": {"doador": a_up, "match": b_up, "total": total},
        "comparacao_existente": (
            comparacao_existente.get("status")
            if isinstance(comparacao_existente, dict) else None
        ),
    }


def validar_comparacao(comparacao: ComparacaoParaValidar | dict) -> dict:
    """Valida UMA comparação e devolve o contrato de três status.

    A função é pura: não lê arquivo, não consulta relógio e não altera a entrada.
    """
    if isinstance(comparacao, dict):
        comparacao = ComparacaoParaValidar(**comparacao)

    doador = comparacao.doador or {}
    match = comparacao.match or {}
    documental = comparacao.documental or {}
    kit = comparacao.kit or {}
    ano_referencia = int(comparacao.ano_referencia)

    cm = _float_positivo(kit.get("total_cm"))
    doador_ano = _ano(doador.get("nascimento"))
    match_ano = _ano(match.get("nascimento"))
    mrca = documental.get("common_ancestor") or {}
    mrca_ano = _ano(mrca.get("birth"))
    mrca_impreciso = bool(mrca.get("birth")) and data_imprecisa(mrca.get("birth"))

    degrees = documental.get("degrees") or {}
    a_up = int(degrees.get("a_up") or 0)
    b_up = int(degrees.get("b_up") or 0)
    meioses = documental.get("meioses")
    if not isinstance(meioses, int):
        meioses = None

    path_ids = (documental.get("path") or {}).get("ids") or []
    status_documental = documental.get("status")
    ambigua = bool(
        documental.get("ambiguous_identity")
        or status_documental == "ambiguous"
        or (documental.get("homonyms") or {}).get("ambiguous")
    )

    codigos: dict[str, dict] = {}

    def add(codigo: str, severidade: str, mensagem: str) -> None:
        codigos.setdefault(codigo, _codigo(codigo, severidade, mensagem))

    def montar(status: str, motivo: str, estimativa=None) -> dict:
        return _resultado(status, motivo, codigos, kit=kit, cm=cm, estimativa=estimativa,
                          mrca=mrca, mrca_ano=mrca_ano, mrca_impreciso=mrca_impreciso,
                          a_up=a_up, b_up=b_up, meioses=meioses,
                          comparacao_existente=comparacao.comparacao_existente)

    if status_documental == "affinity":
        add("AFINIDADE_NAO_BIOLOGICA", "informativo",
            "O caminho chega ao outro ramo por casamento, não por filiação; "
            "o validador não trata afinidade como linhagem consanguínea.")
        return montar(INCONCLUSIVO, "Não foi possível validar: o caminho é por afinidade, não por filiação.")

    if status_documental in (None, "not_found") or not path_ids:
        add("SEM_CAMINHO_DOCUMENTAL", "informativo",
            "Nenhum caminho documental por filiação liga o doador ao match.")
        return montar(INCONCLUSIVO, "Não foi possível validar: não há caminho documental.")

    if ambigua:
        add("IDENTIDADE_AMBIGUA", "informativo",
            "Há mais de um registro compatível com o nome do match; a identidade não está resolvida.")

    # C1 — cada salto pai-filho datado precisa caber em 12–70.
    evidence = documental.get("evidence") or []
    trecho_sem_data = False
    for hop in evidence:
        if hop.get("plausible") is False:
            add("GENITOR_FORA_DA_JANELA_BIOLOGICA", "critico",
                f"O salto {hop.get('parent_name') or hop.get('parent_id')} → "
                f"{hop.get('child_name') or hop.get('child_id')} tem "
                f"{hop.get('age_at_birth')} anos, fora da faixa biológica de "
                f"{IDADE_MINIMA_GENITOR}–{IDADE_MAXIMA_GENITOR}.")
        if not hop.get("parent_birth") or not hop.get("child_birth"):
            trecho_sem_data = True
    if not evidence:
        trecho_sem_data = True
    if trecho_sem_data:
        add("SEM_DATA_DE_NASCIMENTO", "informativo",
            "Há pelo menos um trecho do caminho sem data de nascimento nos dois extremos.")

    # C2 — o MRCA não pode nascer depois (ou no mesmo ano) do descendente.
    if a_up > 0 and doador_ano is not None and mrca_ano is not None and mrca_ano >= doador_ano:
        add("MRCA_POSTERIOR_A_DESCENDENTE", "critico",
            f"O MRCA nasce em {mrca_ano}, depois (ou no mesmo ano) do doador, nascido em {doador_ano}.")
    if b_up > 0 and match_ano is not None and mrca_ano is not None and mrca_ano >= match_ano:
        add("MRCA_POSTERIOR_A_DESCENDENTE", "critico",
            f"O MRCA nasce em {mrca_ano}, depois (ou no mesmo ano) do match, nascido em {match_ano}.")

    # C3 — idade por lado.
    if a_up > 0 and doador_ano is not None and mrca_ano is not None:
        idade = (doador_ano - mrca_ano) / a_up
        if not (IDADE_MINIMA_GENITOR <= idade <= IDADE_MAXIMA_GENITOR):
            add("PROFUNDIDADE_TEMPORAL_INCOMPATIVEL", "critico",
                f"No lado do doador, {doador_ano - mrca_ano} anos em {a_up} geração(ões) "
                f"dão {idade:.1f} anos por geração, fora de "
                f"{IDADE_MINIMA_GENITOR}–{IDADE_MAXIMA_GENITOR}.")
    if b_up > 0 and match_ano is not None and mrca_ano is not None:
        idade = (match_ano - mrca_ano) / b_up
        if not (IDADE_MINIMA_GENITOR <= idade <= IDADE_MAXIMA_GENITOR):
            add("PROFUNDIDADE_TEMPORAL_INCOMPATIVEL", "critico",
                f"No lado do match, {match_ano - mrca_ano} anos em {b_up} geração(ões) "
                f"dão {idade:.1f} anos por geração, fora de "
                f"{IDADE_MINIMA_GENITOR}–{IDADE_MAXIMA_GENITOR}.")

    # C4 — cM × profundidade documental.
    comparacao_existente = comparacao.comparacao_existente or {}
    status_comp = comparacao_existente.get("status") if isinstance(comparacao_existente, dict) else None
    relacoes = _candidatos(cm)
    totais = _totais_das_relacoes(relacoes)

    if status_comp == "CONFLITANTE":
        add("CONFLITO_CM_DOCUMENTAL", "critico",
            "O confronto de quatro estados já classificou este par como CONFLITANTE.")
    elif status_comp == "POSSIVEL":
        add("COMPARACAO_POSSIVEL", "informativo",
            "O cM permite mais de uma leitura e não confirma o caminho documental.")
    elif status_comp == "INCONCLUSIVO":
        add("COMPARACAO_INCONCLUSIVA", "informativo",
            "O confronto de quatro estados não conseguiu avaliar a compatibilidade.")
    elif status_comp is None:
        if not totais:
            add("SEM_COBERTURA_DE_CM", "informativo",
                "O cM não cai em nenhuma relação publicada e o kit não traz uma estimativa de MRCA.")
        else:
            profundidade = meioses if meioses is not None else a_up + b_up
            if profundidade < min(totais) - TOLERANCIA_DE_MEIOSES:
                add("CM_INCOMPATIVEL_COM_PROFUNDIDADE", "critico",
                    f"A linha documental tem {profundidade} meioses, mas o cM só alcança "
                    f"profundidades a partir de {min(totais)} (tolerância de "
                    f"{TOLERANCIA_DE_MEIOSES}).")
            elif profundidade > max(totais) + TOLERANCIA_DE_MEIOSES:
                add("CM_INCOMPATIVEL_COM_PROFUNDIDADE", "critico",
                    f"A linha documental tem {profundidade} meioses, mas o cM só alcança "
                    f"profundidades até {max(totais)} (tolerância de "
                    f"{TOLERANCIA_DE_MEIOSES}).")

    # C5 — o MRCA documentado precisa caber na janela estimada pelo cM.
    estimativa = estimar_mrca(
        cm,
        doador.get("nascimento"),
        kit.get("mrca_generations"),
        relacoes=relacoes,
        intervalo_de_geracao=comparacao.intervalo_de_geracao,
    )
    if estimativa and mrca_ano is not None:
        intervalo = _float_positivo(comparacao.intervalo_de_geracao) or INTERVALO_DE_GERACAO_PADRAO
        margem = TOLERANCIA_DE_GERACOES * intervalo
        fora = (mrca_ano < (estimativa.ano_min or 0) - margem
                or mrca_ano > (estimativa.ano_max or 0) + margem)
        if fora:
            if mrca_impreciso:
                add("MRCA_DOCUMENTADO_FORA_DA_JANELA_ESTIMADO", "atencao",
                    f"O MRCA documentado ({mrca_ano}, estimado) fica fora da janela "
                    f"{estimativa.ano_min}–{estimativa.ano_max} com margem de {margem:.0f} anos.")
            else:
                add("MRCA_DOCUMENTADO_FORA_DA_JANELA", "critico",
                    f"O MRCA documentado ({mrca_ano}) fica fora da janela "
                    f"{estimativa.ano_min}–{estimativa.ano_max} com margem de {margem:.0f} anos.")
    elif estimativa is None:
        add("SEM_COBERTURA_DE_CM", "informativo",
            "Não foi possível estimar o MRCA a partir do cM disponível.")

    if doador_ano is None:
        add("SEM_DATA_DE_NASCIMENTO", "informativo",
            "O doador não tem data de nascimento utilizável.")
    if match_ano is None:
        add("SEM_DATA_DE_NASCIMENTO", "informativo",
            "O match não tem data de nascimento utilizável.")
    if mrca_ano is None:
        add("SEM_DATA_DE_NASCIMENTO", "informativo",
            "O MRCA documentado não tem data de nascimento.")
    if mrca_impreciso:
        add("DATA_ESTIMADA", "informativo",
            "A data do MRCA documentado é estimada; anos estimados não confirmam a linha.")

    # C6 — doador vivo em linha incompatível.
    doador_vivo = doador_ano is not None and (ano_referencia - doador_ano) <= IDADE_IMPOSSIVEL
    if doador_vivo and any(item["severidade"] == "critico" for item in codigos.values()):
        add("DOADOR_VIVO_EM_LINHA_INCOMPATIVEL", "critico",
            f"O doador está vivo ({ano_referencia - doador_ano} anos em {ano_referencia}) "
            "e a linha documental tem uma contradição biológica ou temporal.")

    criticos = [item for item in codigos.values() if item["severidade"] == "critico"]
    atencao = [item for item in codigos.values() if item["severidade"] == "atencao"]
    informativos = [item for item in codigos.values() if item["severidade"] == "informativo"]

    # Um erro pode ser provado com dado parcial; uma validação, não.
    evidencia_completa = bool(evidence) and all(
        hop.get("plausible") is True
        and hop.get("parent_birth")
        and hop.get("child_birth")
        for hop in evidence
    )
    pode_validar = (
        not criticos
        and not atencao
        and not informativos
        and cm is not None
        and status_comp in (None, "COMPATIVEL")
        and doador_ano is not None
        and match_ano is not None
        and mrca_ano is not None
        and not mrca_impreciso
        and len(path_ids) >= 2
        and not ambigua
        and evidencia_completa
        and estimativa is not None
    )

    if criticos:
        primeiro = sorted(criticos, key=lambda item: item["codigo"])[0]
        return montar(ERRO_CRONICO, "Linha documental inviável: " + primeiro["mensagem"],
                      estimativa=estimativa)
    if pode_validar:
        return montar(VALIDADO,
                      "A linha documental é temporalmente viável e o cM é compatível; "
                      "nenhuma contradição foi encontrada.",
                      estimativa=estimativa)

    referencia = (atencao or informativos)
    motivo = ("Não foi possível validar: " + referencia[0]["mensagem"]
              if referencia else "Não foi possível validar: faltam dados para concluir.")
    return montar(INCONCLUSIVO, motivo, estimativa=estimativa)


def agregar_resultados(resultados) -> dict:
    """Resumo de vários kits: o pior status vence (erro > inconclusivo > validado)."""
    lista = list(resultados or [])
    if not lista:
        return {
            "status": INCONCLUSIVO,
            "total": 0,
            "por_status": {VALIDADO: 0, INCONCLUSIVO: 0, ERRO_CRONICO: 0},
            "codigos": [_codigo("SEM_EVIDENCIA", "informativo",
                                "Nenhum kit de DNA utilizável no arquivo.")],
        }

    def status_de(item):
        valor = (item or {}).get("status")
        return valor if valor in _STATUS_ORDEM else INCONCLUSIVO

    final = min((status_de(item) for item in lista), key=lambda valor: _STATUS_ORDEM[valor])
    return {
        "status": final,
        "total": len(lista),
        "por_status": {
            VALIDADO: sum(1 for item in lista if status_de(item) == VALIDADO),
            INCONCLUSIVO: sum(1 for item in lista if status_de(item) == INCONCLUSIVO),
            ERRO_CRONICO: sum(1 for item in lista if status_de(item) == ERRO_CRONICO),
        },
    }


__all__ = [
    "VALIDADO",
    "INCONCLUSIVO",
    "ERRO_CRONICO",
    "INTERVALO_DE_GERACAO_PADRAO",
    "TOLERANCIA_DE_MEIOSES",
    "TOLERANCIA_DE_GERACOES",
    "ComparacaoParaValidar",
    "MrcaEstimado",
    "estimar_mrca",
    "validar_comparacao",
    "agregar_resultados",
]

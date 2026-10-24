"""As palavras e as classes CSS que o operador le no cartao.

Texto de tela e regra: o Jinja so testa se ha rotulo, e quem decide o rotulo, a
cor e o `title` e este modulo. Separado do fluxo para que mudar uma frase nao
encoste no pipeline.
"""
from __future__ import annotations

from .endogamia import (
    CM_MINIMO_SEGMENTO,
    MENSAGEM_ENDEROGAMIA,
)
from .path_finding import MAX_DEPTH
from .validator import (
    ERRO_CRONICO,
    VALIDADO,
)


# Veredito de validacao no cartao (feature 031)

#: Status -> (rotulo visivel, classe CSS). O mapa mora aqui, e nao no template,
#: porque decidir texto e cor e regra: o Jinja so testa se ha rotulo.
#:
#: `INCONCLUSIVO` NAO entra no mapa de proposito. Numa analise real sao 142 cartoes e
#: o inconclusivo e o caso mais comum; marcar quase todos nao marcaria nenhum. A
#: ausencia de selo significa "nao concluido", e a lista declara isso.
ROTULOS_DE_VALIDACAO = {
    VALIDADO: ("Validado", "validacao-valido"),
    ERRO_CRONICO: ("Linha em conflito", "validacao-conflito"),
}

def _aviso_da_validacao(resultado) -> str | None:
    """Status + motivo + primeiro codigo critico, para o `title` do selo.

    O literal de maquina vai AQUI, e nao no texto visivel: `ERRO CRONICO / QUEBRA DE
    LINHA` tem 31 caracteres sem acento, nao cabe num selo e e ruim de ler. Quem audita
    le no `title`, que e onde o literal continua disponivel.
    """
    status = (resultado or {}).get("status") or ""
    motivo = (resultado or {}).get("motivo") or ""
    criticos = [item for item in (resultado or {}).get("codigos") or []
                if item.get("severidade") == "critico"]
    if criticos:
        codigo = criticos[0].get("codigo")
        detalhe = f"{motivo} ({codigo})" if motivo else codigo
    else:
        detalhe = motivo
    if not detalhe:
        return status or None
    return f"{status}: {detalhe}" if status else detalhe

def _explicacao_da_endogamia(diagnostico, tem_caminho_documental: bool) -> str:
    """Frase que separa o achado ESTRUTURAL do parentesco documental.

    O caso que motivou o texto: um cartao dizia "Parentesco documental nao
    encontrado" na secao 1 e "Endogamia estrutural" no cabecalho. Os dois eram
    verdadeiros sobre eixos diferentes — a busca documental tem teto de
    `MAX_DEPTH` iteracoes, a de grafo nao —, mas lidos juntos pareciam
    contradicao. A frase diz qual e qual.
    """
    if diagnostico is None or not diagnostico.endogamia_estrutural:
        return ""
    if tem_caminho_documental:
        return ("Os caminhos mais curtos se bifurcam e voltam ao mesmo ancestral. "
                "Isso é colapso de pedigree (endogamia): o cM esperado sobe e a "
                "leitura do grau de parentesco fica menos confiável.")
    return (f"Sinal estrutural no grafo: há mais de um caminho mais curto, mas o "
            f"parentesco documental não foi encontrado dentro do limite de {MAX_DEPTH} "
            "iterações da busca documental. Isto não confirma um parentesco específico.")

def _observacao_estrutural(diagnostico, tem_caminho_documental: bool) -> str:
    """A frase da secao 5, qualificada pelo que a secao 1 conseguiu afirmar.

    Com caminho documental, a frase e a de contrato: `Endogamia estrutural
    confirmada na árvore`. Sem ele, a mesma estrutura existe, mas chamar de
    "confirmada" ao lado de "Parentesco documental nao encontrado" foi o que
    confundiu o operador no caso da Edneide — a frase passa a dizer o que foi e
    o que NAO foi encontrado.
    """
    if diagnostico is None or not diagnostico.endogamia_estrutural:
        return ""
    if tem_caminho_documental:
        return MENSAGEM_ENDEROGAMIA
    return (f"Sinal estrutural na árvore: {diagnostico.quantidade_de_caminhos} "
            f"caminhos mais curtos, mas o parentesco documental não foi encontrado "
            f"dentro do limite de {MAX_DEPTH} iterações. Isto não confirma um "
            "parentesco específico.")

def _selo_da_endogamia(evidencia, diagnostico, tem_caminho_documental: bool) -> dict | None:
    """Rotulo, classe e `title` do selo de endogamia do cabecalho.

    O selo e a UNICA parte da mitigacao visivel com o cartao fechado: o detalhe
    numerico fica na secao 2, e a frase estrutural completa fica na secao 5.
    Devolver `None` quando nao ha fato e o que impede a tela de marcar os 142
    cartoes com um selo que nao diz nada.

    A prioridade e o colapso de pedigree, que e o achado mais forte. Sem ele, o
    filtro aparece pelo numero de segmentos descartados; sem descarte, o bloco
    pequeno vira "Evidência fraca". A classe NAO pode conter `estado-`: a regra
    `.badge[class*="estado-"]` pinta o texto de branco, e os dois selos sao de
    aviso (fundo creme).

    ## "Endogamia" x "Sinal estrutural"

    Sem caminho documental, o selo diz **Sinal estrutural na árvore**: o grafo
    tem mais de uma rota, mas a secao 1 nao encontrou parentesco dentro do teto.
    Chamar isso de "Endogamia estrutural" sem a ressalva foi o que confundiu o
    operador no caso real da Edneide.
    """
    if diagnostico is not None and diagnostico.endogamia_estrutural:
        caminhos = diagnostico.quantidade_de_caminhos
        rotulo = ("Endogamia estrutural" if tem_caminho_documental
                  else "Sinal estrutural na árvore")
        if tem_caminho_documental:
            titulo = (f"{MENSAGEM_ENDEROGAMIA}: {caminhos} caminho(s) mais curto(s) "
                      "entre a raiz e o match.")
        else:
            # O `title` acompanha o rotulo: nao adianta o selo dizer "sinal" e o
            # tooltip dizer "confirmada" quando a secao 1 nao encontrou caminho.
            titulo = (f"Sinal estrutural na árvore: {caminhos} caminho(s) mais curto(s). "
                      f"O parentesco documental não foi encontrado dentro do limite de "
                      f"{MAX_DEPTH} iterações.")
        if evidencia.mensagem:
            titulo = f"{titulo} {evidencia.mensagem}"
        return {
            "rotulo": rotulo,
            "classe": "endogamia-estrutural",
            "titulo": titulo,
        }
    if evidencia.segmentos_descartados:
        return {
            "rotulo": (f"Filtro: {evidencia.segmentos_descartados} seg. abaixo de "
                       f"{CM_MINIMO_SEGMENTO:g} cM"),
            "classe": "endogamia-filtro",
            "titulo": evidencia.mensagem,
        }
    if evidencia.evidencia_fraca:
        return {
            "rotulo": "Evidência fraca",
            "classe": "endogamia-filtro",
            "titulo": evidencia.mensagem,
        }
    if evidencia.segmentos_sem_valor:
        return {
            "rotulo": "Segmentos sem cM",
            "classe": "endogamia-filtro",
            "titulo": evidencia.mensagem,
        }
    return None

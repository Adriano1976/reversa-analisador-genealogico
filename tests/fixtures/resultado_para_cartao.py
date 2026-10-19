"""Resultado de análise sintético para os testes de tela do cartão.

A tela lê os dicionários do núcleo (`dna_results`), então o teste de cartão precisa de um
dicionário com as chaves que o cabeçalho usa. Montar à mão é mais barato e mais estável do
que rodar a análise inteira só para olhar um selo — e o teste de integração do núcleo já
cobre o caminho real.

As duas classes vêm da folha (`validacao-valido`/`validacao-conflito`) e **não** contêm
`estado-`, que pintaria o texto de branco num selo sem preenchimento.
"""
from __future__ import annotations

ROTULOS = {
    "VALIDADO": ("Validado", "validacao-valido"),
    "ERRO CRONICO / QUEBRA DE LINHA": ("Linha em conflito", "validacao-conflito"),
}

AVISO_PADRAO = (
    "ERRO CRONICO / QUEBRA DE LINHA: Linha documental inviável: No lado do doador, 335 anos "
    "em 2 geração(ões) dão 167.5 anos por geração, fora de 12–70. "
    "(PROFUNDIDADE_TEMPORAL_INCOMPATIVEL)"
)


def resultado(status: str = "ERRO CRONICO / QUEBRA DE LINHA", **overrides) -> dict:
    """Um resultado no formato que o template consome.

    `status` só aceita os que concluem: o inconclusivo é testado passando os campos de
    validação nulos, que é como o núcleo devolve esse caso.
    """
    rotulo, classe = ROTULOS.get(status, (None, None))
    base = {
        "match_name": "Primo Sintetico",
        "csv_name": "Primo Sintetico",
        "cm": 21.6,
        "kit": "AB1234567",
        "text_path": "Doador Sintetico → Pai Sintetico → Ancestral Sintetico",
        "mermaid_data": "graph LR",
        "documentary": {
            "label": "Primos de 1º grau",
            "status": "found",
            "path": {"ids": ["@I1@", "@I2@", "@I10@"], "names": ["Doador", "Pai", "Ancestral"]},
        },
        # O parentesco ORIGINAL, guardado quando a janela de vida e' impossivel (adendo 016).
        # `None` significa que a regra nao foi acionada — o cartao comum, com caminho.
        "documentary_do_registro": None,
        "comparison": {"status": "CONFLITANTE", "label": "Conflitante"},
        "confrontacao_efetiva": "CONFLITANTE",
        "confrontacao_rotulo": "Conflitante",
        "identidade": "confirmada",
        "janela_de_vida": "ok",
        "profundidade": "ok",
        "validacao_status": status,
        "validacao_rotulo": rotulo,
        "validacao_classe": classe,
        "validacao_aviso": AVISO_PADRAO if rotulo else None,
        # A árvore sugerida (feature 032). Por padrão não há sugestão: cada helper
        # abaixo liga o caso que o teste precisa.
        "sugestao_geracoes": 0,
        "sugestao_resumo": None,
        "sugestao_mermaid": None,
        "sugestao_aviso": None,
    }
    base.update(overrides)
    return base


DIAGRAMA_DE_EXEMPLO = """graph TD
  classDef base fill:#a8e6cf,stroke:#4a7c68,stroke-width:2px
  classDef doc fill:#f5f5f5,stroke:#666666
  classDef virt fill:#ffd3b6,stroke:#a8724a,stroke-dasharray:4 3
  N_I1["Doador Sintetico"]:::base
  N_I2["Pai Sintetico"]:::doc
  N_I10["Ancestral Sintetico"]:::doc
  V1["Geração 1"]:::virt
  N_I1 --> N_I2
  N_I10 --> V1
  V1 --> N_I2
  N_I10 -.->|DESVIO DE CONEXÃO / QUEBRA DE LINHA| N_I2
  linkStyle 3 stroke:red,stroke-width:2px,stroke-dasharray:5 5"""


def resultado_com_sugestao(geracoes: int = 3, **overrides) -> dict:
    """Cartão em conflito com gerações a injetar: o bloco deve aparecer."""
    resumo = f"{geracoes} gerações sugeridas"
    base = resultado(**overrides)
    base.update({
        "sugestao_geracoes": geracoes,
        "sugestao_resumo": resumo,
        "sugestao_mermaid": DIAGRAMA_DE_EXEMPLO,
        "sugestao_aviso": None,
    })
    return base


def resultado_sem_geracoes_em_conflito(**overrides) -> dict:
    """Cartão em conflito, mas as duas medidas concordam: só a frase."""
    base = resultado(**overrides)
    base.update({
        "sugestao_geracoes": 0,
        "sugestao_resumo": None,
        "sugestao_mermaid": None,
        "sugestao_aviso": (
            "O cM estima 2 geração(ões) e a árvore já documenta 2: as duas medidas "
            "concordam, não há geração a inserir."),
    })
    return base


def resultado_inconclusivo(**overrides) -> dict:
    """O caso em que o veredito não conclui: `status` presente, os outros três nulos."""
    base = resultado(**overrides)
    base.update({
        "validacao_status": "INCONCLUSIVO",
        "validacao_rotulo": None,
        "validacao_classe": None,
        "validacao_aviso": None,
    })
    return base


def resultado_recusado_pela_idade(**overrides) -> dict:
    """Cartão cujo caminho existe no GEDCOM mas a janela de vida torna impossível.

    É o caso que a contagem em três faixas existe para não esconder: o parentesco
    apresentado é "não encontrado" (a regra do adendo 016), e o original fica em
    `documentary_do_registro`. Sem esta faixa a frase manda o operador procurar registro
    faltando quando o trabalho é procurar homônimo.
    """
    original = resultado()["documentary"]
    base = resultado(**overrides)
    base.update({
        "documentary": {
            "label": "Parentesco documental não encontrado",
            "status": "not_found",
            "path": None,
            "ambiguous_identity": False,
        },
        "documentary_do_registro": original,
        "janela_de_vida": "impossivel",
        "text_path": "",
        "mermaid_data": None,
    })
    return base


def resultado_sem_caminho(**overrides) -> dict:
    """Cartão sem caminho documental nenhum: só evidência genética."""
    base = resultado(**overrides)
    base.update({
        "documentary": {
            "label": "Parentesco documental não encontrado",
            "status": "not_found",
            "path": None,
            "ambiguous_identity": False,
        },
        "documentary_do_registro": None,
        "text_path": "",
        "mermaid_data": None,
    })
    return base

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
    }
    base.update(overrides)
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

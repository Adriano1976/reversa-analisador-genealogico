"""Teste de documentacao: a variavel da pasta de upload tem de estar no `README.md`.

Este teste **falha antes** de a documentacao ser corrigida — e essa e a intencao
(Principio III de `.reversa/principles.md`): a tabela de configuracoes do `README.md` e o
unico lugar que ensina que existe uma sobreposicao de processo para a pasta canonica. Sem
um teste que a prenda, a tabela volta a ficar incompleta na proxima edicao.

A partir da feature 012 a pasta canonica e `src/uploads`, **dentro** do repositorio, e a
variavel deixou de ser "o modo de operacao declarado": ela e a sobreposicao que a suite
(`tests/conftest.py`) e o involucro de paridade (`tests/rodar_paridade.py`) usam para nao
escreverem na pasta de dados do operador. A exigencia da linha na tabela **continua**; o
que mudou foi o motivo.

Nao e um teste de "texto bonito": ele exige que a variavel esteja na **mesma tabela** em
que vive `ANALISADOR_HOST`, que e a tabela de configuracao do processo, e que o caminho
documentado de execucao da paridade seja o involucro — e nao o `harness.py` direto, que
suja a pasta real.
"""
from __future__ import annotations

import os

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
README = os.path.join(RAIZ, "README.md")
VARIAVEL = "ANALISADOR_UPLOAD_FOLDER"
INVOLUCRO = "tests/rodar_paridade.py"


def _linhas() -> list:
    with open(README, encoding="utf-8") as fh:
        return fh.read().splitlines()


def _tabela_que_contem(linhas: list, agulha: str) -> list:
    """Bloco de linhas de tabela Markdown que contem a agulha."""
    for indice, linha in enumerate(linhas):
        if agulha in linha and linha.lstrip().startswith("|"):
            inicio = indice
            while inicio > 0 and linhas[inicio - 1].lstrip().startswith("|"):
                inicio -= 1
            fim = indice
            while fim + 1 < len(linhas) and linhas[fim + 1].lstrip().startswith("|"):
                fim += 1
            return linhas[inicio:fim + 1]
    return []


def test_variavel_esta_na_tabela_de_configuracao():
    linhas = _linhas()
    tabela = _tabela_que_contem(linhas, "`ANALISADOR_HOST`")

    assert tabela, "nao encontrei a tabela de configuracoes no README.md"
    assert any(VARIAVEL in linha for linha in tabela), (
        "a variavel %s tem de estar na tabela de configuracoes do README.md: ela e a "
        "sobreposicao que a suite e o involucro de paridade usam para nao escreverem na "
        "pasta de dados do operador" % VARIAVEL
    )


def test_caminho_documentado_da_paridade_e_o_involucro():
    # O README e escrito em PowerShell, com barra invertida nos caminhos: a comparacao
    # normaliza o separador, porque o que o teste exige e o CAMINHO documentado, nao o
    # estilo de separador de uma plataforma.
    conteudo = "\n".join(_linhas()).replace("\\", "/")

    assert INVOLUCRO in conteudo, (
        "o README.md tem de declarar %s como caminho de execucao da paridade: o "
        "harness.py direto escreve as sondas na pasta real do operador" % INVOLUCRO
    )

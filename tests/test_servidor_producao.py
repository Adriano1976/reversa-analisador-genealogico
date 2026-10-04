"""Bloco de entrada do aplicativo: o servidor em uso é o de produção.

O teste inspeciona o módulo `src/app.py` por leitura de AST e afirma o
comportamento do bloco `if __name__ == "__main__":`. Ele não importa o módulo, e
por isso não exige nem o servidor de produção nem o framework web instalados, e
não abre porta alguma.

Escolha registrada na decisão `D-06` do roadmap da feature `004-servidor-waitress`:
inspeção do módulo em vez de teste de fumaça contra porta efêmera, para cumprir o
princípio III pelo menor custo e sem flutuação.

Estado anterior à mudança: o bloco chamava o servidor de desenvolvimento com o
modo de depuração ligado, então as três afirmações abaixo falhavam.
"""
from __future__ import annotations

import ast
import os

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
APLICATIVO = os.path.join(RAIZ, "src", "app.py")


def _bloco_de_entrada() -> str:
    """Devolve o código-fonte do bloco `if __name__ == "__main__":` do app.py.

    A comparação é feita sobre o texto normalizado pelo `ast.unparse`, para não
    depender de aspas, indentação ou quebra de linha da redação original.
    """
    with open(APLICATIVO, encoding="utf-8") as fh:
        arvore = ast.parse(fh.read())
    for no in arvore.body:
        if isinstance(no, ast.If):
            condicao = ast.unparse(no.test)
            if "__name__" in condicao and "__main__" in condicao:
                return ast.unparse(no)
    raise AssertionError("nao encontrei o bloco de entrada em src/app.py")


def test_o_bloco_de_entrada_usa_o_servidor_de_producao():
    texto = _bloco_de_entrada()
    assert "serve(" in texto, "o bloco de entrada nao inicia o servidor de producao"
    assert "app.run(" not in texto, "o bloco de entrada ainda chama o servidor de desenvolvimento"


def test_o_bloco_de_entrada_declara_endereco_porta_e_concorrencia():
    texto = _bloco_de_entrada()
    for variavel in ("ANALISADOR_HOST", "ANALISADOR_PORT", "ANALISADOR_THREADS"):
        assert variavel in texto, f"o bloco de entrada nao le {variavel}"


def test_o_bloco_de_entrada_nao_liga_o_modo_de_depuracao():
    texto = _bloco_de_entrada()
    assert "debug" not in texto, "o bloco de entrada ainda liga o modo de depuracao"

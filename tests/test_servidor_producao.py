"""Bloco de entrada do aplicativo: o servidor em uso é o de produção.

O teste inspeciona o módulo `src/app.py` por leitura de AST e afirma o
comportamento do bloco `if __name__ == "__main__":`. Ele não importa o módulo, e
por isso não exige nem o servidor de produção nem o framework web instalados, e
não abre porta alguma.

Escolha registrada na decisão `D-06` do roadmap da feature `004-servidor-waitress`:
inspeção do módulo em vez de teste de fumaça contra porta efêmera, para cumprir o
princípio III pelo menor custo e sem flutuação.

**Primeira rodada.** Estado anterior à mudança: o bloco chamava o servidor de
desenvolvimento com o modo de depuração ligado, então as três primeiras
afirmações falhavam.

**Segunda rodada (`T014`), a guarda de exclusividade.** Estende a inspeção ao que
a revisão do `requirements.md` passou a exigir: a aplicação não coexiste consigo
mesma (`RN-05`, `RF-08`), o padrão do endereço atende apenas a máquina local
(`RN-03`, `RF-02`, `D-02` revista), e o servidor recebe o socket já ligado em vez
de criar o dele (`D-10`).

Duas dessas afirmações merecem justificativa, porque não são óbvias:

1. A entrega do socket pronto ao servidor **obriga** a não passar `host` nem
   `port`: o servidor levanta `ValueError` quando recebe `sockets` junto de
   qualquer um dos dois (`waitress/adjustments.py`, linhas 299 e 300). Uma
   afirmação que trave isso evita um erro que só apareceria subindo a aplicação.
2. O socket precisa estar **ligado** (`bind` e `listen`) dentro do bloco: com
   socket pronto, o servidor não faz `bind` (`waitress/server.py`, linha 101,
   `bind_socket=False`). Quem liga é este bloco.

A cobertura do endereço padrão entra aqui porque a `RF-02` é `Must` e a mudança
do padrão é uma das três mudanças observáveis da rodada: sem esta afirmação, a
`T017` seria mudança sem teste que a cubra, contra o princípio III.

A verificação **funcional** da recusa, com dois processos reais disputando a
porta, não vive aqui: ela é a verificação de onboarding registrada na `D-13` e no
`onboarding.md`, e é a única forma de provar que o sistema operacional de fato
recusa a segunda instância.
"""
from __future__ import annotations

import ast
import os

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
APLICATIVO = os.path.join(RAIZ, "src", "app.py")


def _no_do_bloco_de_entrada() -> ast.If:
    """Devolve o nó do bloco `if __name__ == "__main__":` do app.py."""
    with open(APLICATIVO, encoding="utf-8") as fh:
        arvore = ast.parse(fh.read())
    for no in arvore.body:
        if isinstance(no, ast.If):
            condicao = ast.unparse(no.test)
            if "__name__" in condicao and "__main__" in condicao:
                return no
    raise AssertionError("nao encontrei o bloco de entrada em src/app.py")


def _bloco_de_entrada() -> str:
    """Devolve o código-fonte do bloco `if __name__ == "__main__":` do app.py.

    A comparação é feita sobre o texto normalizado pelo `ast.unparse`, para não
    depender de aspas, indentação ou quebra de linha da redação original.
    """
    return ast.unparse(_no_do_bloco_de_entrada())


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


def test_o_bloco_de_entrada_cria_o_socket_de_escuta_com_uso_exclusivo():
    """O socket da aplicação tem de recusar a segunda instância no sistema."""
    texto = _bloco_de_entrada()
    assert "SO_EXCLUSIVEADDRUSE" in texto, (
        "o bloco de entrada nao marca o socket com uso exclusivo: no Windows, a "
        "plataforma permite duas instancias na mesma porta sem essa marca"
    )
    assert ".bind(" in texto, "o bloco de entrada nao liga o socket ao endereco e a porta"
    assert ".listen(" in texto, "o bloco de entrada nao poe o socket em escuta"


def test_o_bloco_de_entrada_entrega_o_socket_pronto_ao_servidor():
    """Com socket pronto, o servidor nao faz bind, e nao aceita host nem port."""
    texto = _bloco_de_entrada()
    assert "sockets=" in texto, "o bloco de entrada nao entrega o socket pronto ao servidor"
    assert "host=" not in texto, (
        "o bloco de entrada passa host junto de sockets, e o servidor levanta "
        "ValueError nessa combinacao"
    )
    assert "port=" not in texto, (
        "o bloco de entrada passa port junto de sockets, e o servidor levanta "
        "ValueError nessa combinacao"
    )


def test_o_bloco_de_entrada_recusa_a_segunda_instancia_com_saida_diferente_de_zero():
    """A recusa por porta ocupada termina o processo com SystemExit.

    A verificação é feita sobre a árvore, e não sobre o texto: o que importa é
    existir um caminho que trate `OSError` e levante `SystemExit` com mensagem,
    que é o que produz mensagem legível e código de saída diferente de zero. A
    mensagem crua do sistema operacional não serve como diagnóstico, e deixá-la
    subir não é recusa, é falha.
    """
    bloco = _no_do_bloco_de_entrada()
    for no in ast.walk(bloco):
        if not isinstance(no, ast.ExceptHandler):
            continue
        tratado = ast.unparse(no.type) if no.type is not None else ""
        if "OSError" not in tratado:
            continue
        for interno in ast.walk(no):
            if not isinstance(interno, ast.Raise) or not isinstance(interno.exc, ast.Call):
                continue
            if ast.unparse(interno.exc.func) != "SystemExit":
                continue
            assert interno.exc.args, (
                "a recusa levanta SystemExit sem mensagem: o operador nao sabe "
                "por que a aplicacao nao subiu"
            )
            return
    raise AssertionError(
        "o bloco de entrada nao recusa a subida quando o endereco e a porta ja "
        "estao em uso, com mensagem e codigo de saida diferente de zero"
    )


def test_o_padrao_do_endereco_atende_apenas_a_maquina_local():
    """`RF-02`: sem as variaveis definidas, a aplicacao nao atende a rede.

    A busca e feita sem as aspas, porque o texto normalizado pelo `ast.unparse`
    troca a aspa dupla pela simples quando nao ha escapamento. Comentario nao
    sobrevive a essa normalizacao, entao toda ocorrencia aqui e literal de codigo.
    """
    texto = _bloco_de_entrada()
    assert "127.0.0.1" in texto, (
        "o padrao do endereco de escuta nao e a maquina local: a aplicacao nao "
        "tem autenticacao alguma, e abrir para a rede tem de ser ato explicito"
    )
    assert "0.0.0.0" not in texto, (
        "o bloco de entrada ainda menciona o endereco que atende todas as "
        "interfaces, e o padrao tem de ser a maquina local"
    )

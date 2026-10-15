"""O seletor de arquivos oferece só o formato de cada aba — e isso NÃO é a barreira.

O pedido do operador: *"na hora de 'Enviar nova árvore' o usuário deve somente visualizar os
arquivos .ged para evitar o envio de arquivos de outros formatos. Essa regra deve ser aplicada
para arquivos do tipo .csv também."*

`accept` faz isso: filtra o que o seletor de arquivos mostra. O que ele **não** faz — e o
motivo deste arquivo existir — é impedir o envio:

- quem escolher "Todos os arquivos" no seletor manda o que quiser;
- arrastar o arquivo para dentro do campo ignora o `accept` por completo;
- e nao ha' nada do lado do servidor que olhe a extensao, de proposito.

A barreira de verdade e' a de **conteudo** (`utils.validate.validar_conteudo_gedcom` exige a
declaracao `0 HEAD`), e a `RISK-007` a mantem assim para nao recusar GEDCOM de exportador
legitimo com extensao atipica. O teste
`test_um_arquivo_de_extensao_estranha_com_conteudo_valido_e_aceito` existe para que ninguem
"conserte" o `accept` transformando-o em validacao — o que quebraria aquela regra.
"""
from __future__ import annotations

import io
import os
import re
import sys

import pytest

_RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
for _caminho in (_RAIZ, os.path.join(_RAIZ, "src")):
    if _caminho not in sys.path:
        sys.path.insert(0, _caminho)

TEMPLATE = os.path.join(_RAIZ, "src", "templates", "index.html")

GEDCOM_VALIDO = (
    "0 HEAD\n1 SOUR TESTE\n1 GEDC\n2 VERS 5.5.1\n2 FORM LINEAGE-LINKED\n"
    "0 @I1@ INDI\n1 NAME Maria /Souza/\n1 SEX F\n0 TRLR\n"
)
CHAVE_ARVORE = "080e7943572d2652"
ARVORE = f"{CHAVE_ARVORE}__arvore.ged"


def _guardar(pasta: str, nome: str, conteudo: bytes) -> None:
    with open(os.path.join(pasta, nome), "wb") as fh:
        fh.write(conteudo)


def _entrada(cliente) -> str:
    """A tela de ENTRADA — onde vive o campo "Enviar nova árvore"."""
    resposta = cliente.get("/")
    assert resposta.status_code == 200
    return resposta.get_data(as_text=True)


def _estado_com_arvore(cliente, pasta) -> str:
    """O estado carregado — onde vive o formulário da análise, com o campo do CSV.

    O campo do CSV **nao** existe na tela de entrada: ele pertence ao formulario de analise,
    que so' aparece depois de uma arvore estar carregada. Medir o `accept` dele na entrada
    passaria por vacuidade (a string nao estaria la', e o teste nao acusaria).
    """
    _guardar(pasta, ARVORE, GEDCOM_VALIDO.encode("utf-8"))
    resposta = cliente.post("/", data={"action": "selecionar_arvore",
                                       "gedcom_filename": ARVORE})
    assert resposta.status_code == 200
    return resposta.get_data(as_text=True)


def _campos_de_arquivo(pagina: str) -> list[str]:
    return re.findall(r'<input[^>]*type="file"[^>]*>', pagina)


class TestOQueOSeletorOferece:

    def test_o_campo_da_arvore_so_oferece_ged(self, cliente_de_upload):
        _app, cliente, _pasta = cliente_de_upload
        pagina = _entrada(cliente)
        campos = [c for c in _campos_de_arquivo(pagina) if 'id="gedcom"' in c]
        assert len(campos) == 1, f"campos do GEDCOM na tela de entrada: {campos}"
        assert 'accept=".ged"' in campos[0], (
            "o campo 'Enviar nova árvore' perdeu o filtro: o seletor volta a oferecer "
            f"qualquer arquivo. Campo medido: {campos[0]}"
        )

    def test_o_campo_do_csv_so_oferece_csv(self, cliente_de_upload):
        _app, cliente, pasta = cliente_de_upload
        pagina = _estado_com_arvore(cliente, pasta)
        campos = [c for c in _campos_de_arquivo(pagina) if 'id="matches_csv"' in c]
        assert len(campos) == 1, f"campos do CSV no estado carregado: {campos}"
        assert 'accept=".csv"' in campos[0], (
            "o campo de envio do relatório perdeu o filtro. Campo medido: " + campos[0]
        )

    def test_todo_campo_de_arquivo_da_tela_tem_filtro(self, cliente_de_upload):
        """Guarda contra o TERCEIRO campo: um `type="file"` novo entra sem `accept` e some.

        Um campo sem `accept` nao quebra nada — so' oferece o disco inteiro, que e' o
        comportamento que este pedido veio corrigir.
        """
        _app, cliente, pasta = cliente_de_upload
        paginas = {"entrada": _entrada(cliente)}
        paginas["carregado"] = _estado_com_arvore(cliente, pasta)
        vistos = 0
        for onde, pagina in paginas.items():
            for campo in _campos_de_arquivo(pagina):
                vistos += 1
                assert "accept=" in campo, f"campo sem filtro em {onde}: {campo}"
        assert vistos >= 2, f"nao encontrei os campos de arquivo para conferir: {vistos}"

    def test_o_filtro_e_por_extensao_e_nao_por_tipo_mime(self):
        """Extensão, e não MIME — e o motivo é medido, não estético.

        No Windows o `.csv` costuma estar registrado como `application/vnd.ms-excel`, e um
        `accept="text/csv"` faria o seletor ESCONDER arquivos `.csv` legitimas em algumas
        máquinas. A extensão é o que o operador vê e o que o app já usa para decidir a aba
        (`reporting.lista_de_arquivos`).
        """
        with open(TEMPLATE, encoding="utf-8") as arquivo:
            fonte = arquivo.read()
        for valor in re.findall(r'accept="([^"]+)"', fonte):
            assert valor.startswith("."), (
                f"o filtro {valor!r} nao e' por extensao: um tipo MIME pode esconder "
                "arquivo valido"
            )

    def test_o_gedcom_nao_oferece_gedcom_como_extensao(self):
        """Só `.ged`, porque é só `.ged` que entra na aba de árvores.

        `ABA_DE_ARVORES = ".ged"` e a comparacao e' `endswith`. Um arquivo `x.gedcom` nao
        entra em aba nenhuma — oferece-lo no seletor seria convidar o operador a enviar um
        arquivo que depois desaparece.
        """
        with open(TEMPLATE, encoding="utf-8") as arquivo:
            fonte = arquivo.read()
        assert 'accept=".ged"' in fonte
        assert 'accept=".gedcom"' not in fonte


class TestONadaDissoEBarreira:
    """O `accept` filtra o seletor; quem barra e' o conteudo."""

    def test_um_arquivo_de_extensao_estranha_com_conteudo_valido_e_aceito(self, cliente_de_upload):
        """`RISK-007`: recusar por extensao quebraria exportador legitimo.

        Este teste NAO elogia o comportamento — ele o PRENDE. Se alguem "melhorar" o
        `accept` transformando-o em validacao de extensao no servidor, este teste cai, e e'
        para cair: a decisao de aceitar por conteudo e' declarada.
        """
        _app, cliente, _pasta = cliente_de_upload
        resposta = cliente.post("/", data={
            "action": "upload_gedcom",
            "gedcom": (io.BytesIO(GEDCOM_VALIDO.encode("utf-8")), "arvore.txt"),
        })
        assert resposta.status_code == 200
        corpo = resposta.get_data(as_text=True)
        assert "carregado!" in corpo, (
            "o envio de um GEDCOM valido com extensao atipica deixou de ser aceito: a "
            "validacao passou a olhar a extensao, e a `RISK-007` manda olhar o conteudo"
        )

    def test_arquivo_sem_o_cabecalho_e_recusado_com_motivo(self, cliente_de_upload):
        """A barreira de verdade, e ela ja' existia antes deste pedido.

        A mensagem e' **generica de proposito**: `RN-18`/`T039` fixam UMA mensagem para
        conteudo recusado. O motivo especifico ("nao comeca com a declaracao 0 HEAD") e'
        calculado por `validar_conteudo_gedcom` e **nao chega a tela** — e' decisao declarada,
        e nao um defeito; por isso o teste prende a mensagem do contrato, e nao o detalhe.
        """
        _app, cliente, _pasta = cliente_de_upload
        resposta = cliente.post("/", data={
            "action": "upload_gedcom",
            "gedcom": (io.BytesIO(b"isto nao e' um gedcom\n"), "qualquer.ged"),
        })
        assert resposta.status_code == 200
        corpo = resposta.get_data(as_text=True)
        assert "não reconhecido como GEDCOM" in corpo, (
            "o operador mandou um arquivo que nao e' GEDCOM e a tela nao recusou: o `accept` "
            "do seletor nao pode ser a unica barreira"
        )

    def test_a_extensao_estranha_entra_e_fica_invisivel_o_defeito_medido(self, cliente_de_upload):
        """O que o `accept` evita, e o que ele NAO resolve.

        Enviar `arvore.txt` e' aceito (conteudo valido) e a tela responde "carregado!" — mas
        o arquivo nao entra em aba nenhuma, porque `itens_da_aba` filtra por extensao. Nada
        explica o sumico: e' o defeito que o filtro do seletor torna raro, nao impossivel.

        O complemento (dizer ao operador que a extensao nao pertence a aba nenhuma) esta
        declarado como pendente no adendo `021`.
        """
        _app, cliente, _pasta = cliente_de_upload
        cliente.post("/", data={
            "action": "upload_gedcom",
            "gedcom": (io.BytesIO(GEDCOM_VALIDO.encode("utf-8")), "arvore.txt"),
        })
        corpo = _entrada(cliente)
        assert "carregado!" not in corpo  # ja' foi, a mensagem nao persiste
        assert not re.search(r'name="gedcom_filename"\s+value="[^"]*arvore\.txt"', corpo), (
            "o arquivo com extensao atipica passou a aparecer na aba de arvores: se isso "
            "mudou de proposito, o filtro por extensao de `itens_da_aba` mudou junto"
        )

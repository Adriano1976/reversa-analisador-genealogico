"""T034 (feature `011-escolher-arquivo-da-lista`, regra `RN-14`): aposentar um arquivo.

## O que "apagar" significa neste projeto, e por que o nome do teste importa

O botao e vermelho e se chama "Apagar", mas a `RN-07` diz que a aplicacao **nunca
apaga** arquivo enviado. O que existe e **aposentar**: mover o arquivo para
`<pasta>/_aposentados/`, de onde ele desaparece da lista e continua inteiro no disco.
Todo teste deste arquivo que fala de "apagar" esta falando disso, e o mais importante
deles e `test_aposentar_nao_apaga_e_o_conteudo_esta_intacto` — se ele cair, a aplicacao
passou a destruir dado do operador.

## As duas camadas de defesa contra escape de pasta

A referencia que chega do formulario e um nome de arquivo, e nao um caminho. Os testes
de `TestReferenciaQueEscapa` cobrem as duas camadas: a validacao
(`referencia_de_arquivo_da_pasta`, em `utils/validate.py`) e a confirmacao do diretorio
pai, feita no adaptador com o caminho ja resolvido.

## Por que a validacao daqui NAO e a mesma do resolvedor

`resolver` exige a forma canonica `<16 hex>__<nome>`, e a aposentadoria **nao pode**
exigir: os tres arquivos sem chave da pasta real sao exatamente os inalcancaveis, e sao
os que o operador mais quer tirar da lista. `test_aposentar_arquivo_sem_chave_e_com_acento`
prende justamente isso — e ele falharia se alguem "corrigisse" a validacao para reusar
a do resolvedor.
"""
from __future__ import annotations

import os
import re
import sys

import pytest

_RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
for _caminho in (_RAIZ, os.path.join(_RAIZ, "src")):
    if _caminho not in sys.path:
        sys.path.insert(0, _caminho)

from ports.adaptadores import PASTA_DE_APOSENTADOS, ArmazenamentoEmDisco  # noqa: E402

GEDCOM = (
    "0 HEAD\n1 SOUR TESTE\n1 GEDC\n2 VERS 5.5.1\n2 FORM LINEAGE-LINKED\n"
    "0 @I1@ INDI\n1 NAME Maria /Souza/\n1 SEX F\n0 TRLR\n"
)

CHAVE = "080e7943572d2652"
NOME_COM_CHAVE = f"{CHAVE}__arvore.ged"


def _escrever(pasta: str, nome: str, conteudo: bytes) -> str:
    caminho = os.path.join(pasta, nome)
    with open(caminho, "wb") as fh:
        fh.write(conteudo)
    return caminho


class TestAposentarNoAdaptador:
    """`RN-14` no adaptador: o arquivo sai da pasta, e continua inteiro na subpasta."""

    def test_aposentar_move_o_arquivo_e_devolve_true(self, tmp_path):
        pasta = str(tmp_path)
        _escrever(pasta, NOME_COM_CHAVE, GEDCOM.encode("utf-8"))
        armazenamento = ArmazenamentoEmDisco(pasta)

        assert armazenamento.aposentar(NOME_COM_CHAVE, "unico") is True

        assert not os.path.exists(os.path.join(pasta, NOME_COM_CHAVE)), (
            "o arquivo continuou na pasta de upload: ele nao saiu da lista"
        )
        assert os.path.isfile(os.path.join(pasta, PASTA_DE_APOSENTADOS, NOME_COM_CHAVE))

    def test_aposentar_nao_apaga_e_o_conteudo_esta_intacto(self, tmp_path):
        """`RN-07`: o teste mais importante deste arquivo. Nada pode ser destruido."""
        pasta = str(tmp_path)
        conteudo = GEDCOM.encode("utf-8")
        _escrever(pasta, NOME_COM_CHAVE, conteudo)

        ArmazenamentoEmDisco(pasta).aposentar(NOME_COM_CHAVE, "unico")

        with open(os.path.join(pasta, PASTA_DE_APOSENTADOS, NOME_COM_CHAVE), "rb") as fh:
            assert fh.read() == conteudo, (
                "o conteudo do arquivo mudou: a aposentadoria deixou de ser reversivel"
            )

    def test_o_arquivo_aposentado_sai_da_listagem(self, tmp_path):
        """A subpasta nao e listada, e por isso nenhum filtro novo foi preciso."""
        pasta = str(tmp_path)
        _escrever(pasta, NOME_COM_CHAVE, GEDCOM.encode("utf-8"))
        armazenamento = ArmazenamentoEmDisco(pasta)

        assert [e.nome for e in armazenamento.listar("unico")] == [NOME_COM_CHAVE]

        armazenamento.aposentar(NOME_COM_CHAVE, "unico")

        assert armazenamento.listar("unico") == [], (
            "o arquivo aposentado continuou aparecendo na lista: a subpasta esta sendo lida"
        )

    def test_aposentar_arquivo_sem_chave_e_com_acento(self, tmp_path):
        """O caso MEDIDO que motivou a validacao mais permissiva.

        `Adriano_Santos.ged` e `Famílias_Sergipanas.csv` nao tem chave no nome, entao
        `resolver` os recusa. Se a aposentadoria usasse a MESMA validacao, os arquivos
        que o operador mais quer tirar da lista seriam os unicos que nao poderiam sair.
        """
        pasta = str(tmp_path)
        armazenamento = ArmazenamentoEmDisco(pasta)

        for nome in ("Adriano_Santos.ged", "Famílias_Sergipanas.csv", "planilha de dna.xlsx"):
            _escrever(pasta, nome, GEDCOM.encode("utf-8"))
            assert armazenamento.aposentar(nome, "unico") is True, (
                f"{nome!r} nao pode ser aposentado: a validacao esta exigindo a chave"
            )

        assert armazenamento.listar("unico") == []

    def test_aposentar_nao_sobrescreve_um_aposentado_existente(self, tmp_path):
        """Dois conteudos diferentes com o mesmo nome: os dois tem de sobreviver."""
        pasta = str(tmp_path)
        _escrever(pasta, "Adriano_Santos.ged", b"primeiro conteudo")
        armazenamento = ArmazenamentoEmDisco(pasta)
        armazenamento.aposentar("Adriano_Santos.ged", "unico")

        _escrever(pasta, "Adriano_Santos.ged", b"segundo conteudo")
        assert armazenamento.aposentar("Adriano_Santos.ged", "unico") is True

        aposentados = sorted(os.listdir(os.path.join(pasta, PASTA_DE_APOSENTADOS)))
        assert len(aposentados) == 2, (
            "a segunda aposentadoria sobrescreveu a primeira: um arquivo foi destruido (RN-07)"
        )
        with open(os.path.join(pasta, PASTA_DE_APOSENTADOS, "Adriano_Santos.ged"), "rb") as fh:
            assert fh.read() == b"primeiro conteudo", "o aposentado mais antigo foi sobrescrito"

    def test_aposentar_arquivo_inexistente_devolve_false(self, tmp_path):
        armazenamento = ArmazenamentoEmDisco(str(tmp_path))

        assert armazenamento.aposentar(NOME_COM_CHAVE, "unico") is False

    def test_aposentar_em_pasta_ausente_nao_e_excecao(self, tmp_path):
        """`D-07`: pasta ausente nao pode virar erro na tela."""
        armazenamento = ArmazenamentoEmDisco(os.path.join(str(tmp_path), "nao-existe"))

        assert armazenamento.aposentar(NOME_COM_CHAVE, "unico") is False
        assert not os.path.isdir(os.path.join(str(tmp_path), "nao-existe")), (
            "uma leitura/recusa criou pasta: efeito colateral escondido"
        )


class TestReferenciaQueEscapa:
    """A referencia tem de ser um NOME. Caminho, `.` e `..` sao recusados."""

    @pytest.mark.parametrize("referencia", [
        "../fora.ged",
        "..\\fora.ged",
        "sub/pasta.ged",
        "sub\\pasta.ged",
        "/etc/passwd",
        "C:\\Windows\\system.ini",
        "",
        ".",
        "..",
        "arq\x00vo.ged",
        None,
    ])
    def test_referencia_em_forma_de_caminho_e_recusada(self, tmp_path, referencia):
        pasta = os.path.join(str(tmp_path), "uploads")
        os.makedirs(pasta)
        fora = os.path.join(str(tmp_path), "fora.ged")
        with open(fora, "wb") as fh:
            fh.write(b"intocavel")
        armazenamento = ArmazenamentoEmDisco(pasta)

        assert armazenamento.aposentar(referencia, "unico") is False

        assert os.path.isfile(fora), "um arquivo FORA da pasta de upload foi movido"
        assert not os.path.isdir(os.path.join(pasta, PASTA_DE_APOSENTADOS)), (
            "a subpasta foi criada apesar da recusa: nada devia ter acontecido"
        )

    def test_referencia_valida_de_arquivo_real_e_aceita(self, tmp_path):
        """O contrapeso: a recusa nao pode ser um `False` constante.

        Sem esta assercao, `test_referencia_em_forma_de_caminho_e_recusada` ficaria verde
        com uma funcao que recusa tudo — inclusive o uso legitimo.
        """
        pasta = str(tmp_path)
        _escrever(pasta, "Adriano_Santos.ged", b"conteudo")

        assert ArmazenamentoEmDisco(pasta).aposentar("Adriano_Santos.ged", "unico") is True


# --- Rota e tela --------------------------------------------------------------


def _corpo(cliente) -> str:
    return cliente.get("/").get_data(as_text=True)


class TestBotoesDaTela:
    """`RN-14` e o pedido do operador: verde `Abrir` e vermelho `Apagar` em cada linha."""

    def test_o_botao_apagar_esta_em_todo_item_da_lista(self, cliente_de_upload):
        _app, cliente, pasta = cliente_de_upload
        _escrever(pasta, NOME_COM_CHAVE, GEDCOM.encode("utf-8"))

        corpo = _corpo(cliente)

        assert 'value="aposentar_arquivo"' in corpo, (
            "a tela nao oferece como apagar: nao ha formulario com a acao de aposentar"
        )
        assert f'name="arquivo_a_aposentar" value="{NOME_COM_CHAVE}"' in corpo, (
            "o formulario de apagar nao carrega a referencia do arquivo daquela linha"
        )

    def test_o_botao_apagar_e_vermelho(self, cliente_de_upload):
        _app, cliente, pasta = cliente_de_upload
        _escrever(pasta, NOME_COM_CHAVE, GEDCOM.encode("utf-8"))

        corpo = _corpo(cliente)

        assert 'class="btn btn-sm btn-danger">Apagar</button>' in corpo

    def test_o_botao_abrir_e_verde_e_continua_sendo_a_acao_de_escolha(self, cliente_de_upload):
        """O pedido era o ROTULO e a COR. A acao continua a mesma, e por isso nada de
        backend mudou no caminho de abrir (`T033`).
        """
        _app, cliente, pasta = cliente_de_upload
        _escrever(pasta, NOME_COM_CHAVE, GEDCOM.encode("utf-8"))

        corpo = _corpo(cliente)

        assert 'class="btn btn-sm btn-success">Abrir</button>' in corpo, (
            "o botao verde 'Abrir' nao esta na tela"
        )
        assert 'value="selecionar_arvore"' in corpo, (
            "o botao 'Abrir' deixou de chamar a acao de escolha: seria um botao sem rota"
        )
        assert "Usar esta árvore" not in corpo, "o rotulo antigo continua na tela"

    def test_a_aba_de_dna_tem_apagar_e_nao_tem_abrir(self, cliente_de_upload):
        """Nao ha acao que carregue um CSV sozinho: `Abrir` ali prometeria o que nao existe."""
        _app, cliente, pasta = cliente_de_upload
        _escrever(pasta, "94e2402671702cac__relatorio.csv", b"nome,cm\nMaria,100\n")

        corpo = _corpo(cliente)

        assert 'name="arquivo_a_aposentar" value="94e2402671702cac__relatorio.csv"' in corpo, (
            "a aba de DNA nao ganhou botao de apagar"
        )
        assert 'value="selecionar_arvore"' not in corpo, (
            "apareceu um 'Abrir' sem nenhuma arvore listada: so pode ter vindo da aba de DNA"
        )


class TestAposentarPelaRota:
    """`T034`: a acao nova, do formulario ate o disco."""

    def _aposentar(self, cliente, referencia):
        return cliente.post("/", data={
            "action": "aposentar_arquivo",
            "arquivo_a_aposentar": referencia,
        })

    def test_aposentar_tira_o_item_da_lista_e_confirma(self, cliente_de_upload):
        _app, cliente, pasta = cliente_de_upload
        _escrever(pasta, NOME_COM_CHAVE, GEDCOM.encode("utf-8"))

        resposta = self._aposentar(cliente, NOME_COM_CHAVE)
        corpo = resposta.get_data(as_text=True)

        assert resposta.status_code == 200
        assert "saiu da lista" in corpo, "a acao nao confirmou nada para o operador"
        assert not os.path.exists(os.path.join(pasta, NOME_COM_CHAVE))
        assert os.path.isfile(os.path.join(pasta, PASTA_DE_APOSENTADOS, NOME_COM_CHAVE))
        assert f'name="gedcom_filename" value="{NOME_COM_CHAVE}"' not in corpo, (
            "o item aposentado continua sendo oferecido na lista, agora sem arquivo por tras"
        )

    def test_a_confirmacao_diz_que_nada_foi_apagado(self, cliente_de_upload):
        """O botao diz "Apagar" e o dado nao some. A tela tem de dizer isso."""
        _app, cliente, pasta = cliente_de_upload
        _escrever(pasta, NOME_COM_CHAVE, GEDCOM.encode("utf-8"))

        corpo = self._aposentar(cliente, NOME_COM_CHAVE).get_data(as_text=True)

        assert "não foi apagado" in corpo, (
            "a mensagem nao avisa que o arquivo continua no disco: o operador vai achar que perdeu"
        )

    def test_a_confirmacao_nao_vaza_a_chave_de_conteudo(self, cliente_de_upload):
        """`D-09` vale para a mensagem tambem, e nao so para a lista."""
        _app, cliente, pasta = cliente_de_upload
        _escrever(pasta, NOME_COM_CHAVE, GEDCOM.encode("utf-8"))

        corpo = self._aposentar(cliente, NOME_COM_CHAVE).get_data(as_text=True)
        visivel = " ".join(re.findall(r">([^<]+)<", corpo))

        assert CHAVE not in visivel, "a chave de conteudo apareceu no texto da tela"
        assert "arvore" in visivel, "pre-condicao: a mensagem tem de estar no ar para medir algo"

    def test_aposentar_o_arquivo_que_estava_aberto_nao_derruba_a_tela(self, cliente_de_upload):
        """A ordem dos ramos da rota e a regra, nao estilo.

        O ramo de aposentar vem ANTES de `_arvore_do_formulario`. Se viesse depois, o
        parse da arvore aposentada falharia e o operador veria "arquivo nao existe mais"
        no lugar da confirmacao — a acao teria funcionado e a tela diria que nao.
        """
        _app, cliente, pasta = cliente_de_upload
        _escrever(pasta, NOME_COM_CHAVE, GEDCOM.encode("utf-8"))

        resposta = cliente.post("/", data={
            "action": "aposentar_arquivo",
            "arquivo_a_aposentar": NOME_COM_CHAVE,
            "gedcom_filename": NOME_COM_CHAVE,
        })
        corpo = resposta.get_data(as_text=True)

        assert resposta.status_code == 200
        assert "saiu da lista" in corpo, (
            "a tela respondeu com erro em vez de confirmar: o ramo de aposentar esta depois "
            "da resolucao da arvore, e o arquivo ja nao esta mais la"
        )

    def test_aposentar_arquivo_sem_chave_pela_rota(self, cliente_de_upload):
        """O item que o operador mais quer tirar da lista e o inalcancavel."""
        _app, cliente, pasta = cliente_de_upload
        _escrever(pasta, "arvore_sem_chave.ged", GEDCOM.encode("utf-8"))

        corpo = self._aposentar(cliente, "arvore_sem_chave.ged").get_data(as_text=True)

        assert "saiu da lista" in corpo
        assert os.path.isfile(os.path.join(pasta, PASTA_DE_APOSENTADOS, "arvore_sem_chave.ged"))

    def test_aposentar_arquivo_inexistente_avisa_sem_derrubar(self, cliente_de_upload):
        _app, cliente, _pasta = cliente_de_upload

        resposta = self._aposentar(cliente, NOME_COM_CHAVE)
        corpo = resposta.get_data(as_text=True)

        assert resposta.status_code == 200
        assert "Não foi possível aposentar" in corpo

    def test_a_rota_recusa_referencia_em_forma_de_caminho(self, cliente_de_upload):
        """A defesa de ponta a ponta: o arquivo fora da pasta nao pode ser tocado."""
        _app, cliente, pasta = cliente_de_upload
        fora = os.path.join(os.path.dirname(pasta), "fora.ged")
        _escrever(os.path.dirname(pasta), "fora.ged", GEDCOM.encode("utf-8"))

        corpo = self._aposentar(cliente, "../fora.ged").get_data(as_text=True)

        assert "Não foi possível aposentar" in corpo, "a rota aceitou um caminho como referencia"
        assert os.path.isfile(fora), "a rota moveu um arquivo de FORA da pasta de upload"
        assert not os.path.isdir(os.path.join(pasta, PASTA_DE_APOSENTADOS))


class TestConfirmacaoAntesDeApagar:
    """Confirmacao no botao vermelho, pedida pelo operador em 2026-10-10.

    ## O que estes testes medem, e o limite honesto deles

    Eles medem o **markup entregue**: que o formulario de apagar carrega um `onsubmit`
    com `confirm(...)`, que ele cita o arquivo daquela linha, e que nenhum outro
    formulario ganhou confirmacao. O que eles **nao** medem e o comportamento do
    navegador — nao ha motor de JavaScript na suite, e `confirm` e do navegador. A
    diferenca fica declarada de proposito: um teste que so prende a presenca do
    atributo nao prova que a caixa aparece, e chamar isso de prova seria falso.
    """

    @staticmethod
    def _confirmacoes(corpo: str) -> list[str]:
        """Os valores dos atributos `onsubmit` do corpo, sem depender de escape."""
        return re.findall(r"onsubmit='([^']*)'", corpo)

    def test_o_formulario_de_apagar_pede_confirmacao(self, cliente_de_upload):
        _app, cliente, pasta = cliente_de_upload
        _escrever(pasta, NOME_COM_CHAVE, GEDCOM.encode("utf-8"))

        corpo = _corpo(cliente)

        assert self._confirmacoes(corpo), (
            "o botao Apagar nao pede confirmacao: um clique errado tira o arquivo da lista"
        )
        assert "return confirm(" in self._confirmacoes(corpo)[0]

    def test_a_confirmacao_cita_o_arquivo_daquela_linha(self, cliente_de_upload):
        """Com dois itens na lista, a caixa tem de dizer QUAL esta sendo apagado."""
        _app, cliente, pasta = cliente_de_upload
        _escrever(pasta, NOME_COM_CHAVE, GEDCOM.encode("utf-8"))
        _escrever(pasta, "94e2402671702cac__relatorio.csv", b"nome,cm\nMaria,100\n")

        confirmacoes = self._confirmacoes(_corpo(cliente))

        assert len(confirmacoes) == 2, "cada botao Apagar tem de ter a sua confirmacao"
        assert any("arvore" in c for c in confirmacoes), "nenhuma confirmacao cita a arvore"
        assert any("relatorio" in c for c in confirmacoes), "nenhuma confirmacao cita o relatorio"

    def test_a_confirmacao_avisa_que_o_arquivo_nao_e_apagado(self, cliente_de_upload):
        _app, cliente, pasta = cliente_de_upload
        _escrever(pasta, NOME_COM_CHAVE, GEDCOM.encode("utf-8"))

        confirmacoes = self._confirmacoes(_corpo(cliente))

        assert any("continua guardado no disco" in c for c in confirmacoes), (
            "a caixa nao avisa que o arquivo sobrevive: o operador clicaria achando que perde"
        )

    def test_so_o_botao_de_apagar_pede_confirmacao(self, cliente_de_upload):
        """`Abrir` nao e destrutivo, e nao pode interromper o operador com uma caixa."""
        _app, cliente, pasta = cliente_de_upload
        _escrever(pasta, NOME_COM_CHAVE, GEDCOM.encode("utf-8"))

        corpo = _corpo(cliente)

        assert len(self._confirmacoes(corpo)) == len(re.findall(
            r'value="aposentar_arquivo"', corpo)), (
            "ha confirmacao em formulario que nao e o de apagar"
        )

    def test_nome_hostil_no_arquivo_nao_quebra_o_atributo(self, cliente_de_upload):
        """Um nome com apostrofo nao pode romper o atributo nem injetar JavaScript.

        O rotulo passa por `rotulo_limpo`, que troca todo simbolo por espaco — entao o
        valor que entra na mensagem e sempre palavra e espaco. O `tojson` do template nao
        depende disso, e este teste prende as duas metades: o atributo continua
        reconhecivel e o nome cru NAO aparece dentro dele.

        O nome hostil e so com apostrofo porque o Windows recusa `<` e `>` em nome de
        arquivo — medido, `OSError: [Errno 22] Invalid argument`. O apostrofo e o
        caractere que de fato quebraria um atributo delimitado por aspas simples, que e o
        caso deste template.
        """
        _app, cliente, pasta = cliente_de_upload
        _escrever(pasta, f"{CHAVE}__d'Agua.ged", GEDCOM.encode("utf-8"))

        resposta = cliente.get("/")
        corpo = resposta.get_data(as_text=True)
        confirmacoes = self._confirmacoes(corpo)

        assert resposta.status_code == 200
        assert len(confirmacoes) == 1, (
            "o atributo onsubmit foi rompido pelo apostrofo do nome do arquivo"
        )
        assert "d Agua" in confirmacoes[0], "o rotulo limpo nao chegou a confirmacao"
        assert "d'Agua" not in confirmacoes[0], (
            "o nome CRU entrou na mensagem: e por ali que o atributo quebraria"
        )

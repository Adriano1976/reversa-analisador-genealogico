"""`T042` (`A008` da auditoria): arquivo alcançável com conteúdo que o parser não lê.

## O defeito, como ele foi MEDIDO

`_arvore_do_formulario()` chamava `_CARREGADOR.carregar` **fora de qualquer `try`**, e os
`except` de `index()` começam depois dessa chamada. Resultado, reproduzido pela rota:

    POST / com gedcom_filename=0e85a4f3052e19e3__Genealogia_Mineira.csv
    -> 500
    OSError: Unexpected EOF while reading GEDCOM header

**10 dos 13 arquivos da pasta real** derrubavam o parser. A auditoria registrou o `A008` como
"não alcançável com os 19 arquivos de hoje", e o que se mediu depois é mais preciso: o caminho
de **clique** não chega lá — a aba de DNA não oferece "Abrir" —, mas a **requisição** chega, e a
aplicação não tem autenticação.

## O caso que este arquivo usa é o mais realista possível

Um arquivo cujo NOME termina em `.ged` e cujo CONTEÚDO é um CSV. Ele parece uma árvore na lista,
ganha o botão "Abrir", e não é GEDCOM nenhum. A pasta do operador **teve exatamente esse
arquivo** (`94e2402671702cac__Familias_Sergipanas.csv.ged`), e é o caso que a `RN-09` descreve:
a lista decide pelo nome, e não lê conteúdo.

## O que se prende aqui

1. a rota responde **mensagem**, e não `500`;
2. a mensagem diz o que houve, sem jargão;
3. a mensagem mostra o **rótulo**, e não a referência com a chave dentro (`D-09`);
4. o traceback **vai para o log**, porque antes ele não ia para lugar nenhum.
"""
from __future__ import annotations

import logging
import os
import re
import sys

_RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
for _caminho in (_RAIZ, os.path.join(_RAIZ, "src")):
    if _caminho not in sys.path:
        sys.path.insert(0, _caminho)

CHAVE = "94e2402671702cac"
# O nome termina em `.ged`, entao ele entra na aba de arvore e ganha botao "Abrir". O conteudo e
# um relatorio de DNA: nao e GEDCOM, e o parser nao tem como le-lo.
ARMAZENADO = f"{CHAVE}__planilha.csv.ged"
CONTEUDO_CSV = b"Match Name,Chromosome,Centimorgans (cM)\nMaria Souza,1,120.5\n"


def _guardar(pasta: str, nome: str, conteudo: bytes) -> None:
    with open(os.path.join(pasta, nome), "wb") as fh:
        fh.write(conteudo)


def _visivel(corpo: str) -> str:
    return " ".join(re.findall(r">([^<]+)<", corpo))


def _abrir(cliente, referencia: str = ARMAZENADO):
    """A acao que o botao "Abrir" dispara."""
    return cliente.post("/", data={
        "action": "selecionar_arvore",
        "gedcom_filename": referencia,
    })


class TestConteudoIlegivel:
    """A rota responde mensagem onde antes havia traceback."""

    def test_abrir_arquivo_ilegivel_nao_derruba_a_rota(self, cliente_de_upload):
        _app, cliente, pasta = cliente_de_upload
        _guardar(pasta, ARMAZENADO, CONTEUDO_CSV)

        resposta = _abrir(cliente)

        assert resposta.status_code == 200, (
            f"a rota respondeu {resposta.status_code} para um arquivo que a lista OFERECE: "
            "`_arvore_do_formulario` voltou a chamar o parser sem guarda (A008)"
        )

    def test_a_mensagem_diz_que_o_arquivo_nao_pode_ser_lido(self, cliente_de_upload):
        _app, cliente, pasta = cliente_de_upload
        _guardar(pasta, ARMAZENADO, CONTEUDO_CSV)

        corpo = _abrir(cliente).get_data(as_text=True)

        assert "não pôde ser lido como GEDCOM" in corpo, (
            "a tela nao explica o que aconteceu: o operador precisa saber que o arquivo existe e "
            "que o problema e o conteudo dele"
        )
        assert "OSError" not in corpo, "o traceback continua indo para a tela"
        assert "Traceback" not in corpo, "o traceback continua indo para a tela"

    def test_a_mensagem_mostra_o_rotulo_e_nao_a_chave(self, cliente_de_upload):
        """`D-09`: o erro era o ULTIMO lugar da tela que ainda mostrava a referencia crua."""
        _app, cliente, pasta = cliente_de_upload
        _guardar(pasta, ARMAZENADO, CONTEUDO_CSV)

        corpo = _abrir(cliente).get_data(as_text=True)
        visivel = _visivel(corpo)

        assert "planilha csv" in visivel, "a mensagem nao nomeia o arquivo pelo rotulo"
        assert CHAVE not in visivel, (
            "a chave de conteudo apareceu como TEXTO na mensagem de erro"
        )

    def test_o_traceback_vai_para_o_log(self, cliente_de_upload, caplog):
        """Antes, a tela mostrava o rastro e ninguem o registrava. Agora e o inverso."""
        _app, cliente, pasta = cliente_de_upload
        _guardar(pasta, ARMAZENADO, CONTEUDO_CSV)

        with caplog.at_level(logging.ERROR):
            _abrir(cliente)

        assert caplog.text.strip(), (
            "o erro nao foi registrado em log nenhum: sem a tela mostrando e sem log, o defeito "
            "fica invisivel para quem depura"
        )

    def test_os_outros_dois_fluxos_tambem_nao_derrubam(self, cliente_de_upload):
        """`_arvore_do_formulario` e a fonte unica das guardas: os tres fluxos passam por ela."""
        _app, cliente, pasta = cliente_de_upload
        _guardar(pasta, ARMAZENADO, CONTEUDO_CSV)

        busca = cliente.post("/", data={
            "action": "path_search", "gedcom_filename": ARMAZENADO,
            "person1_name": "Carlos Silva", "person2_name": "Ana Silva",
        })
        dna = cliente.post("/", data={
            "action": "dna_analysis", "gedcom_filename": ARMAZENADO,
            "root_name": "Carlos Silva Souza",
        })

        assert busca.status_code == 200, "a busca de caminho continua derrubando"
        assert dna.status_code == 200, "a analise de DNA continua derrubando"


class TestOArquivoContinuaIntacto:
    """A guarda e de LEITURA: ela nao pode mexer no arquivo nem esconde-lo da lista."""

    def test_o_arquivo_ilegivel_continua_na_pasta_e_na_lista(self, cliente_de_upload):
        _app, cliente, pasta = cliente_de_upload
        _guardar(pasta, ARMAZENADO, CONTEUDO_CSV)

        _abrir(cliente)

        assert os.path.isfile(os.path.join(pasta, ARMAZENADO)), "o arquivo foi removido ou movido"
        tela = cliente.get("/").get_data(as_text=True)
        assert f'name="arquivo_a_aposentar" value="{ARMAZENADO}"' in tela, (
            "o arquivo sumiu da lista depois de nao poder ser lido: a lista nao filtra por "
            "conteudo (`D-08`), e o operador precisa poder APAGA-LO"
        )

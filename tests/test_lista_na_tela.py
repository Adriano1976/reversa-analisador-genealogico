"""T007 e T008 (feature `011-escolher-arquivo-da-lista`): a tela de entrada passa a ter lista.

## O que este arquivo mede, e o que ele NAO mede

`RF-06` e o coracao da feature: hoje a tela de entrada exige um envio antes de mostrar qualquer coisa,
e o operador so descobre o que ja esta armazenado depois de enviar. Depois da `D-04`, o `GET /` entrega
as duas abas com as listas **sem envio previo**.

As assercoes sao feitas sobre o **HTML entregue**, e nao sobre as variaveis de contexto. E deliberado:
o que o operador ve e o corpo da resposta, e prender o nome das variaveis aqui acoplaria o teste a uma
escolha interna que o plano nao fixou. Quem depende do contexto e o instrumento de paridade, e ele le
chaves **nomeadas** (`harness.py:211-221`), nao o HTML.

O que fica de FORA de proposito: agrupamento e contagem. Aqueles sao da funcao pura e estao na `T005`;
duplicar aqui faria dois arquivos medirem a mesma regra.

## Estado esperado ANTES da T019

Vermelho. Com o ramo `{% if not gedcom_filename %}` ainda sendo um formulario de envio, o corpo nao
traz a lista, entao as assercoes de presenca falham. A de `200` passa nos dois estados — ela existe
para prender que a tela **nao pode** virar erro, nao para medir a mudanca.
"""
from __future__ import annotations

import os
import re
import sys

_RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
for _caminho in (_RAIZ, os.path.join(_RAIZ, "src")):
    if _caminho not in sys.path:
        sys.path.insert(0, _caminho)

# GEDCOM minimo e valido: e o que `utils/validate.py` exige, mas a listagem NAO valida conteudo —
# o arquivo e escrito direto na pasta justamente para que o teste nao dependa do caminho de envio.
GEDCOM = (
    "0 HEAD\n1 SOUR TESTE\n1 GEDC\n2 VERS 5.5.1\n2 FORM LINEAGE-LINKED\n"
    "0 @I1@ INDI\n1 NAME Maria /Souza/\n1 SEX F\n0 TRLR\n"
)
CSV = "Match Name,Chromosome,Centimorgans (cM)\nMaria Souza,1,120.5\n"

CHAVE_ARVORE = "080e7943572d2652"
CHAVE_DNA = "94e2402671702cac"
CHAVE_PLANILHA = "b70889273a505a5d"

# Rotulos literais da tela, ja existentes em `src/templates/index.html:67` e `:70`. Estao aqui para
# prender que a mudanca de `GET /` NAO renomeia a interface que o operador conhece.
ROTULO_ARVORE = "Buscar Conexão no GEDCOM"
ROTULO_DNA = "Analisador de DNA"

# Valor de `action` do envio: contrato existente, e o que a tela tem de continuar oferecendo dentro
# da aba depois de a tela de entrada deixar de ser um formulario solto (`RN-08`).
ACAO_DE_ENVIO = "upload_gedcom"


def _guardar(pasta: str, nome: str, conteudo: bytes) -> None:
    """Escreve o arquivo direto na pasta de upload. Sem passar pelo envio, de proposito."""
    with open(os.path.join(pasta, nome), "wb") as fh:
        fh.write(conteudo)


def _corpo(cliente) -> str:
    return cliente.get("/").get_data(as_text=True)


class TestTelaDeEntradaComArquivos:
    """T007 (`RF-06`): o `GET /` sem envio previo entrega as duas abas com as listas."""

    def test_a_raiz_responde_200_sem_envio_previo(self, cliente_de_upload):
        """`RF-06`: nenhum arquivo e exigido para chegar as abas."""
        _app, cliente, _pasta = cliente_de_upload

        assert cliente.get("/").status_code == 200

    def test_as_duas_abas_aparecem_sem_envio_previo(self, cliente_de_upload):
        _app, cliente, _pasta = cliente_de_upload

        corpo = _corpo(cliente)

        assert ROTULO_ARVORE in corpo, (
            "a aba de arvore nao apareceu no corpo do GET / sem envio previo: a D-04 nao foi aplicada"
        )
        assert ROTULO_DNA in corpo

    def test_o_nome_visivel_do_arquivo_armazenado_aparece_na_lista(self, cliente_de_upload):
        """`RF-01`: o operador tem de reconhecer o arquivo pelo nome que ele mesmo deu."""
        _app, cliente, pasta = cliente_de_upload
        _guardar(pasta, f"{CHAVE_ARVORE}__arvore.ged", GEDCOM.encode("utf-8"))

        corpo = _corpo(cliente)

        assert "arvore.ged" in corpo, (
            "o arquivo armazenado nao apareceu na lista: o GET / ainda nao monta as listas (T017)"
        )

    def test_o_relatorio_de_dna_aparece_na_aba_de_dna(self, cliente_de_upload):
        """`RF-03`: a aba de DNA lista os relatorios de CSV armazenados."""
        _app, cliente, pasta = cliente_de_upload
        _guardar(pasta, f"{CHAVE_DNA}__relatorio.csv", CSV.encode("utf-8"))

        assert "relatorio.csv" in _corpo(cliente)

    def test_a_chave_nao_vaza_para_o_corpo_da_tela(self, cliente_de_upload):
        """`D-09`: o operador ve o NOME, nunca a chave de conteudo.

        A assercao de PRESENCA vem primeiro de proposito. Sozinha, "a chave nao esta no corpo" passa
        **vaziamente** enquanto a lista nao existe — nao ha chave nenhuma para vazar. Emparelhada, o
        teste so fica verde quando a lista existe **e** exibe o nome visivel.
        """
        _app, cliente, pasta = cliente_de_upload
        _guardar(pasta, f"{CHAVE_ARVORE}__arvore.ged", GEDCOM.encode("utf-8"))

        corpo = _corpo(cliente)
        # "texto visivel" e o que fica ENTRE as tags. A assercao anterior procurava a chave no corpo
        # inteiro, e por isso passou a falhar quando o item virou controle de escolha: o nome
        # armazenado circula no campo oculto, e isso e CORRETO — e assim que a referencia viaja entre
        # requisicoes. O que o `D-09` proibe e a chave chegar aos OLHOS do operador.
        visivel = " ".join(re.findall(r">([^<]+)<", corpo))

        assert "arvore.ged" in visivel, (
            "pre-condicao: a lista tem de estar no ar para a assercao medir algo"
        )
        assert CHAVE_ARVORE not in visivel, (
            "a chave de conteudo apareceu como TEXTO na tela: o item tem de exibir o nome visivel, e "
            "nao a chave. No campo oculto ela pode — e precisa — circular"
        )

    def test_o_item_da_lista_e_um_controle_submetivel(self, cliente_de_upload):
        """`RF-02`, e o teste que FALTOU na primeira versao desta feature.

        A versao anterior desta classe asseria que o nome do arquivo **aparece** no corpo. Presenca nao
        e selecao: medido em 2026-10-09 no navegador, a lista era um `<li>` com texto, sem `select`,
        sem radio, sem link e sem formulario. O operador via as arvores e **nao podia escolher
        nenhuma** — a tela dizia "Escolha uma arvore" e nao oferecia como.

        Este teste prende o que faltava: que o item seja um **controle** que submete a escolha, com o
        nome ARMAZENADO no campo oculto que o resto da aplicacao ja usa.
        """
        _app, cliente, pasta = cliente_de_upload
        _guardar(pasta, f"{CHAVE_ARVORE}__arvore.ged", GEDCOM.encode("utf-8"))

        corpo = _corpo(cliente)

        assert f'name="gedcom_filename" value="{CHAVE_ARVORE}__arvore.ged"' in corpo, (
            "o item da lista nao carrega o nome ARMAZENADO num campo que possa ser submetido: e o que "
            "faz o clique virar escolha, e sem ele a lista e decorativa (RF-02)"
        )
        assert 'value="selecionar_arvore"' in corpo, (
            "nao ha ramo de rota que receba a escolha: um `action` fora dos tres conhecidos cai no "
            "renderizacao final SEM gedcom_filename, e a escolha seria descartada"
        )

    def test_escolher_a_arvore_da_lista_entrega_o_estado_de_arvore_escolhida(self, cliente_de_upload):
        """`RF-02`: o POST da escolha tem de renderizar as abas COM a arvore escolhida."""
        _app, cliente, pasta = cliente_de_upload
        nome = f"{CHAVE_ARVORE}__arvore.ged"
        _guardar(pasta, nome, GEDCOM.encode("utf-8"))

        resposta = cliente.post("/", data={
            "action": "selecionar_arvore",
            "gedcom_filename": nome,
        })
        corpo = resposta.get_data(as_text=True)

        assert resposta.status_code == 200
        assert f'value="{nome}"' in corpo, (
            "a escolha foi descartada: o formulario de busca nao recebeu o gedcom_filename, entao o "
            "operador clicaria e a tela voltaria ao estado de entrada"
        )

    def test_o_item_indisponivel_nao_ganha_botao_de_escolha(self, cliente_de_upload):
        """`D-11`: oferecer o que nao funciona e o defeito que a marca existe para evitar."""
        _app, cliente, pasta = cliente_de_upload
        _guardar(pasta, "arvore_sem_chave.ged", GEDCOM.encode("utf-8"))

        corpo = _corpo(cliente)

        assert "arvore_sem_chave.ged" in corpo, "pre-condicao: o indisponivel continua na lista"
        assert 'value="arvore_sem_chave.ged"' not in corpo, (
            "o item indisponivel ganhou botao de escolha: clicar nele so produziria a mensagem falsa "
            "de arquivo inexistente"
        )

    def test_arquivo_de_outra_extensao_nao_aparece_em_aba_nenhuma(self, cliente_de_upload):
        """`RN-03`/`D-10`: o `.xlsx` da pasta real nao entra em aba nenhuma, e continua no disco.

        Mesmo cuidado do teste da chave vazada: a assercao de ausencia sozinha passaria vaziamente
        com a lista ainda por construir. Com um `.ged` na pasta **e** a presenca exigida primeiro, o
        teste mede a particao, e nao a inexistencia da lista.
        """
        _app, cliente, pasta = cliente_de_upload
        _guardar(pasta, f"{CHAVE_ARVORE}__arvore.ged", GEDCOM.encode("utf-8"))
        _guardar(pasta, f"{CHAVE_PLANILHA}__planilha.xlsx", b"conteudo de planilha")

        corpo = _corpo(cliente)

        assert "arvore.ged" in corpo, "pre-condicao: a lista tem de estar no ar para a particao medir algo"
        assert "planilha.xlsx" not in corpo, (
            "o .xlsx entrou em alguma aba: a particao por extensao (RN-03, D-10) nao esta valendo"
        )
        assert os.path.isfile(os.path.join(pasta, f"{CHAVE_PLANILHA}__planilha.xlsx")), (
            "o arquivo foi escondido E removido: a lista nao pode alterar a pasta (RF-08)"
        )


class TestTelaDeEntradaSemArquivo:
    """T008 (`RF-07`, `D-07`): pasta sem arquivo do tipo orienta o envio e nao falha.

    ## Por que dois destes testes ja nascem VERDES, e isso e correto

    `test_pasta_vazia_responde_200`, `test_pasta_vazia_ainda_oferece_o_envio` e
    `test_pasta_vazia_nao_despeja_nome_de_arquivo` passam **antes** da `T019`, e vao continuar passando
    depois. Eles sao **guardas**, nao motores: prendem que a mudanca de tela nao estrague o estado
    vazio, e o valor deles aparece se uma regressao futura fizer a pasta vazia virar erro ou fizer a
    lista despejar nome de arquivo inexistente.

    O motor desta acao e `test_as_duas_abas_aparecem_tambem_no_estado_vazio`, que e vermelho hoje. Um
    teste de ausencia sozinho passa vaziamente enquanto a lista nao existe; por isso, nos testes desta
    classe que medem ausencia, ela vem acompanhada da presenca das abas.
    """

    def test_pasta_vazia_responde_200(self, cliente_de_upload):
        """O primeiro estado de uma instalacao nova. Nao e erro, e nao pode virar 500."""
        _app, cliente, _pasta = cliente_de_upload

        resposta = cliente.get("/")

        assert resposta.status_code == 200
        assert resposta.get_data(as_text=True).strip(), "corpo vazio nao orienta o operador a nada"

    def test_pasta_vazia_ainda_oferece_o_envio(self, cliente_de_upload):
        """`RF-05`: sem a lista, o envio e o unico caminho — e ele tem de continuar na tela."""
        _app, cliente, _pasta = cliente_de_upload

        corpo = _corpo(cliente)

        assert ACAO_DE_ENVIO in corpo, (
            "a aba vazia nao oferece o envio: o operador ficaria preso, e o RF-05 exige as duas vias"
        )

    def test_pasta_vazia_nao_despeja_nome_de_arquivo(self, cliente_de_upload):
        """Estado vazio e vazio: nada de item fantasma na lista."""
        _app, cliente, _pasta = cliente_de_upload

        corpo = _corpo(cliente)

        assert ".ged" not in corpo and ".csv" not in corpo, (
            "a tela mostrou nome de arquivo com a pasta vazia: a lista nao esta sendo derivada do disco"
        )

    def test_as_duas_abas_aparecem_tambem_no_estado_vazio(self, cliente_de_upload):
        """`D-04`: as abas aparecem SEMPRE, e nao so quando ha arquivo."""
        _app, cliente, _pasta = cliente_de_upload

        corpo = _corpo(cliente)

        assert ROTULO_ARVORE in corpo and ROTULO_DNA in corpo

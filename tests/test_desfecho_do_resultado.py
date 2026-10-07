"""O modo de renderizacao vem do DESFECHO, nunca do texto da mensagem (`T026`).

## O defeito que este arquivo impede de voltar

Antes, o ramo `path_search` de `index()` decidia entre cartao de resultado e
alerta de erro por uma unica linha. Na fronteira de aplicacao ha DOIS casos que o
operador ve de formas diferentes e que so se distinguem por um flag booleano do
nucleo:

| O que o nucleo devolve | Desfecho | O que a tela faz |
|---|---|---|
| `None`, `"Nenhuma conexao encontrada..."`, `True` | `SEM_RESULTADO` | cartao, **com sucesso** |
| `None`, `"Pessoa 1 'X' nao encontrada."`, `False` | `ERRO_DE_ENTRADA` | alerta de erro |

Se o adaptador inferisse o modo pelo TEXTO, o literal de tela passaria a ter
autoridade semantica — exatamente o que a `RF-20` proibe ao tirar o parametro
`success=` da fronteira. O teste central daqui e o que prova isso: com o MESMO
texto arbitrario, o modo muda conforme o flag.

## Estrutura

- **Unitario**: `application.path_search.path_search` com o fluxo do nucleo
  macaqueado, medindo o `desfecho` nos tres formatos que o nucleo produz.
- **Ponta a ponta**: POST real na rota, com o mesmo macaqueio, medindo a classe
  do `div` que o template renderiza.

Os dois sao necessarios: o unitario prova a DERIVACAO do desfecho, o de ponta a
ponta prova que o adaptador USA o desfecho. Um so deles deixaria metade do
caminho sem cobertura.
"""
import html
import io
import os
import re
import sys

import pytest

PROJETO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, PROJETO)
sys.path.insert(0, os.path.join(PROJETO, "src"))

from application import Desfecho  # noqa: E402
from application import path_search as modulo_de_busca  # noqa: E402

# GEDCOM minimo VALIDO, com a mesma forma da constante `GEDCOM_VALIDO` de
# `tests/test_upload_seguranca.py`. Nao pode ser simplificado: as duas rotas
# pos-upload passam por `_arvore_do_formulario`, que parseia de verdade pelo
# `ged4py` — um texto que apenas "parece" GEDCOM faria o teste falhar no parser,
# e nao no ponto que ele quer medir. As duas pessoas existem de proposito, para
# o fluxo real de busca (quando ele roda sem macaqueio) ter o que encontrar.
GEDCOM_VALIDO = (
    "0 HEAD\n"
    "1 SOUR TESTE\n"
    "1 GEDC\n"
    "2 VERS 5.5.1\n"
    "2 FORM LINEAGE-LINKED\n"
    "0 @I1@ INDI\n"
    "1 NAME Joao /Silva/\n"
    "1 SEX M\n"
    "0 @I2@ INDI\n"
    "1 NAME Maria /Souza/\n"
    "1 SEX F\n"
    "0 @F1@ FAM\n"
    "1 HUSB @I1@\n"
    "1 WIFE @I2@\n"
    "0 TRLR\n"
)

# Texto que nao se parece com nenhuma mensagem conhecida do projeto. E o
# insumo do teste central: se o adaptador inferisse o modo pelo texto, nao
# haveria como ele acertar aqui.
TEXTO_ARBITRARIO = "TEXTO ARBITRARIO DE TESTE"

REGEX_REFERENCIA = r'name="gedcom_filename" value="([^"]+)"'


def _substituir_fluxo_de_busca(monkeypatch, retorno):
    """Macqueia o global `fluxo_de_busca` do modulo do caso de uso.

    O macaqueio e no atributo do MODULO `application.path_search.py`, e nao em
    `core.path_search`: e o global que `path_search` consulta na hora da chamada
    (`application/path_search.py:58`). Trocar o do nucleo nao teria efeito algum
    sobre a aplicacao, que importou a referencia no topo do modulo — o teste
    ficaria verde medindo o fluxo de verdade.
    """
    monkeypatch.setattr(modulo_de_busca, "fluxo_de_busca", lambda *a, **k: retorno)


def _enviar_gedcom(client):
    """Upload pelo proprio client e devolve a referencia armazenada.

    A referencia tem de resolver para um arquivo EXISTENTE: `gedcom_filename`
    invalido faz `_arvore_do_formulario` responder
    `"Erro: Arquivo '...' nao existe mais."` antes de o caso de uso ser chamado,
    e o teste mediria a guarda de entrada em vez do desfecho. Como a chave e
    derivada do conteudo (sha256), o mesmo GEDCOM reenviado gera a mesma chave e
    a pasta temporaria nao acumula lixo entre testes.
    """
    pagina = client.post(
        "/",
        data={"action": "upload_gedcom",
              "gedcom": (io.BytesIO(GEDCOM_VALIDO.encode("utf-8")), "arvore.ged")},
        content_type="multipart/form-data",
    ).get_data(as_text=True)
    encontrado = re.search(REGEX_REFERENCIA, pagina)
    assert encontrado, (
        "o upload nao devolveu o campo oculto gedcom_filename; sem ele nao ha "
        "como montar o POST de busca de caminho"
    )
    return encontrado.group(1)


def _postar_busca(client, referencia, person1="Joao Silva", person2="Maria Souza"):
    """POST real no ramo `path_search` do formulario.

    O retorno e o HTML ja SEM as entidades que o Jinja emite: as mensagens de
    contrato do projeto tem apóstrofo (`"Pessoa 1 'X' nao encontrada."`) e o
    Jinja o escreve como `&#39;`, de modo que comparar o texto cru com a
    mensagem falharia por ESCAPE, e nao por o literal ter deixado de chegar a
    tela. Desescapar aqui mantem a assercao sobre o TEXTO, que e o que o
    operador le, e nao sobre a forma intermediaria do template.
    """
    return html.unescape(client.post(
        "/",
        data={"action": "path_search",
              "gedcom_filename": referencia,
              "person1_name": person1,
              "person2_name": person2},
    ).get_data(as_text=True))


# ---------------------------------------------------------------------------
# Unitario — a derivacao do desfecho
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("retorno, esperado", [
    pytest.param(({"person1_name": "X"}, "msg", True), Desfecho.RESULTADO,
                 id="payload-presente"),
    pytest.param((None, "msg", True), Desfecho.SEM_RESULTADO,
                 id="sem-payload-com-sucesso"),
    pytest.param((None, "msg", False), Desfecho.ERRO_DE_ENTRADA,
                 id="sem-payload-sem-sucesso"),
])
def test_desfecho_deriva_dos_tres_formatos_do_nucleo(monkeypatch, retorno, esperado):
    """Os TRES estados que `core.path_search` sinaliza tem de virar tres valores.

    A mensagem e sempre a MESMA (`"msg"`) nos tres casos de proposito: o
    desfecho nao pode depender dela. Se alguem trocar a derivacao por uma
    heuristica de texto, o primeiro e o terceiro caso continuariam passando
    (mensagens reais diferem) e so o segundo quebraria — por isso o texto e
    identico aqui.
    """
    _substituir_fluxo_de_busca(monkeypatch, retorno)

    resultado = modulo_de_busca.path_search("A", "B", arvore=None, deps=None,
                                            dono="unico")

    assert resultado.desfecho is esperado
    assert resultado.mensagem == "msg"
    assert resultado.dados is retorno[0]


def test_payload_tem_precedencia_sobre_o_flag_de_sucesso(monkeypatch):
    """`D-11`: payload presente e `RESULTADO` mesmo com o flag em falso.

    O nucleo nao produz este par hoje — por isso o caso e construido aqui. O
    que ele prende e a ORDEM dos testes em `_desfecho`
    (`application/path_search.py:74`): um `if sucesso` primeiro faria um payload
    validado virar alerta de erro, e o operador perderia um resultado que o
    nucleo entregou.
    """
    _substituir_fluxo_de_busca(monkeypatch, ({"person1_name": "X"}, "msg", False))

    resultado = modulo_de_busca.path_search("A", "B", arvore=None, deps=None,
                                            dono="unico")

    assert resultado.desfecho is Desfecho.RESULTADO
    assert resultado.dados == {"person1_name": "X"}


def test_desfecho_nao_e_derivado_da_mensagem(monkeypatch):
    """O TEXTO nao participa da derivacao: mensagem conhecida, desfecho do flag.

    A mensagem de "nenhuma conexao" e a que o adaptador antigo poderia ter usado
    como pista para escolher o cartao. Aqui ela vem acompanhada de
    `sucesso=False`, e o desfecho tem de ser `ERRO_DE_ENTRADA` mesmo assim. E o
    inverso do teste central de ponta a ponta: la o texto e arbitrario, aqui ele
    e o texto que "pediria" o outro modo.
    """
    mensagem_conhecida = "Nenhuma conexão encontrada entre 'X' e 'Y'."
    _substituir_fluxo_de_busca(monkeypatch, (None, mensagem_conhecida, False))

    resultado = modulo_de_busca.path_search("X", "Y", arvore=None, deps=None,
                                            dono="unico")

    assert resultado.desfecho is Desfecho.ERRO_DE_ENTRADA
    assert resultado.mensagem == mensagem_conhecida


def test_o_caso_de_uso_nao_consulta_a_mensagem_vinda_do_nucleo():
    """Defesa de leitura: `_desfecho` recebe os dois FLAGS, e nao a mensagem.

    O unitario acima prova o comportamento de hoje; este prende a assinatura que
    o torna possivel. Uma refatoracao que passasse a mensagem para dentro de
    `_desfecho` (para "melhorar" a decisao) reabriria a porta que a `RF-20`
    fechou, e nenhum teste de comportamento pegaria a mudanca enquanto a
    heuristica continuasse acertando os casos conhecidos.
    """
    import inspect

    assinatura = inspect.signature(modulo_de_busca._desfecho)

    assert list(assinatura.parameters) == ["dados", "sucesso"], (
        "a derivacao do desfecho passou a receber outro insumo; a RN/RF-20 "
        "proibe o texto da mensagem de participar da decisao"
    )


# ---------------------------------------------------------------------------
# Ponta a ponta — o adaptador USA o desfecho
# ---------------------------------------------------------------------------

def test_sem_resultado_renderiza_cartao_com_sucesso(cliente_de_upload, monkeypatch):
    """`(None, msg, True)` e o caso "nenhuma conexao": sucesso, SEM cartao.

    Ele e o caso que o adaptador antigo errava com mais facilidade, porque
    "nenhuma conexao encontrada" parece erro. A tela mostra a mensagem em
    `alert-success` e nao ha `path_result`, entao o bloco do cartao nao e
    renderizado — as duas assercoes medem exatamente isso.
    """
    _app, client, _pasta = cliente_de_upload
    referencia = _enviar_gedcom(client)
    mensagem = "Nenhuma conexão encontrada entre 'X' e 'Y'."
    _substituir_fluxo_de_busca(monkeypatch, (None, mensagem, True))

    pagina = _postar_busca(client, referencia)

    assert "alert-success" in pagina, "o caso 'sem resultado' perdeu o modo de sucesso"
    assert "alert-danger" not in pagina
    assert mensagem in pagina


def test_erro_de_entrada_renderiza_alerta_de_erro(cliente_de_upload, monkeypatch):
    """`(None, msg, False)` e "pessoa nao encontrada": alerta de erro.

    O par com o teste anterior e o ponto: mensagens parecidas, modos opostos, e
    a unica diferenca e o flag. Nenhum dos dois pode ser reconhecido pelo texto.
    """
    _app, client, _pasta = cliente_de_upload
    referencia = _enviar_gedcom(client)
    mensagem = "Pessoa 1 'X' não encontrada."
    _substituir_fluxo_de_busca(monkeypatch, (None, mensagem, False))

    pagina = _postar_busca(client, referencia)

    assert "alert-danger" in pagina, "o caso 'erro de entrada' perdeu o alerta"
    assert "alert-success" not in pagina
    assert mensagem in pagina


@pytest.mark.parametrize("sucesso, classe_esperada", [
    pytest.param(True, "alert-success",
                 id="flag-verdadeiro-renderiza-sucesso"),
    pytest.param(False, "alert-danger",
                 id="flag-falso-renderiza-erro"),
])
def test_mesmo_texto_arbitrario_muda_de_modo_apenas_pelo_flag(
        cliente_de_upload, monkeypatch, sucesso, classe_esperada):
    """O TESTE CENTRAL da `T026`: texto identico, modo oposto.

    `"TEXTO ARBITRARIO DE TESTE"` nao contem nenhuma palavra das mensagens
    conhecidas — nem "erro", nem "nao encontrada", nem "nenhuma conexao". Se o
    adaptador inferisse o modo do texto, os DOIS parametros deste teste
    renderizariam a mesma classe e um deles falharia. E o que ele existe para
    impedir: o literal de tela ganhando autoridade semantica.

    A assercao de ausencia da classe oposta e deliberada: `alert-success` contem
    a substring `alert-s`... e `alert-danger` nao; um teste que so checasse a
    presenca poderia passar com as duas classes no HTML (por exemplo se alguem
    renderizasse os dois alertas).
    """
    _app, client, _pasta = cliente_de_upload
    referencia = _enviar_gedcom(client)
    _substituir_fluxo_de_busca(monkeypatch, (None, TEXTO_ARBITRARIO, sucesso))

    pagina = _postar_busca(client, referencia)

    assert classe_esperada in pagina, (
        "o modo de renderizacao nao seguiu o flag de sucesso=%r" % sucesso
    )
    assert ("alert-danger" if classe_esperada == "alert-success"
            else "alert-success") not in pagina
    assert TEXTO_ARBITRARIO in pagina


def test_resultado_com_payload_renderiza_o_cartao(cliente_de_upload, monkeypatch):
    """`RESULTADO` leva o payload ao template: sem isso a tela perde o diagrama.

    O desfecho nao pode ser apenas "nao e erro": o cartao depende de
    `path_result` chegar ao template (`src/templates/index.html:457`). Um
    adaptador que tratasse `RESULTADO` como `SEM_RESULTADO` passaria nos testes
    de alerta e deixaria o operador sem diagrama — este teste fecha essa porta.

    O payload e minimo, mas com as chaves que o template LE sem guarda de
    existencia: `person1_name`, `person2_name`, `text_path` e `documentary` com
    `status`. Payload vazio faria o Jinja estourar em `Undefined`, e o teste
    mediria o template em vez do adaptador.
    """
    _app, client, _pasta = cliente_de_upload
    referencia = _enviar_gedcom(client)
    payload = {
        "person1_name": "Joao Silva",
        "person2_name": "Maria Souza",
        "text_path": "Joao Silva → Maria Souza",
        "mermaid_data": None,
        "documentary": {"status": "found", "label": "Ancestral comum",
                        "degrees": None, "meioses": None,
                        "common_ancestor": None, "homonyms": None},
        "observations": [],
    }
    _substituir_fluxo_de_busca(monkeypatch, (payload, "Conexão direta encontrada.", True))

    pagina = _postar_busca(client, referencia)

    assert "alert-success" in pagina
    assert "Conexão entre:" in pagina, "o cartao de resultado nao foi renderizado"
    assert "Joao Silva" in pagina


def test_referencia_invalida_nao_chega_ao_caso_de_uso(cliente_de_upload, monkeypatch):
    """Guarda de continuidade: referencia que nao existe para antes do caso de uso.

    Este teste NAO e sobre desfecho — e sobre a premissa dos outros quatro. Se
    `_arvore_do_formulario` deixar de barrar uma referencia inexistente, os
    testes acima passariam a medir a mensagem "nao existe mais" e ninguem
    notaria que o macaqueio nunca foi chamado. Aqui a sonda registra se o fluxo
    foi consultado, e a assercao diz que NAO foi.
    """
    chamadas = []

    def fluxo_espiao(*a, **k):
        chamadas.append(a)
        return None, "nunca deveria ser chamado", True

    monkeypatch.setattr(modulo_de_busca, "fluxo_de_busca", fluxo_espiao)
    _app, client, _pasta = cliente_de_upload

    pagina = _postar_busca(client, "0000000000000000__inexistente.ged")

    assert chamadas == [], "a guarda de entrada deixou passar referencia invalida"
    assert "alert-danger" in pagina
    assert "não existe mais" in pagina

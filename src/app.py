import errno
import os
import socket
import sys

from flask import Flask, render_template, request, send_file
from reporting.lista_de_arquivos import (
    ABA_DE_ARVORES,
    ABA_DE_DNA,
    formatar_data_br,
    itens_da_aba,
    rotulo_de_referencia,
)
from werkzeug.exceptions import HTTPException, RequestEntityTooLarge, SecurityError

from application import Desfecho, nomes_de_exibicao
from application.dna_analysis import dna_analysis as caso_de_uso_dna
from application.path_search import path_search as caso_de_uso_de_busca
from application.reenvio import SUBSTITUIDO, guardar_com_substituicao
from application.traducao import traduzir
from application.upload_gedcom import upload_gedcom as caso_de_uso_de_upload
from core.dna_analysis import Dependencias
from core.erros import ErroDeDominio
from parsers.csv_ingest import (
    aggregate_matches,
    detect_columns as detectar_colunas,
    read_csv_with_fallback,
)
from reporting.mermaid_render import (
    generate_mermaid_graph,
    generate_mermaid_graph_indirect_bridge,
)
from ports.adaptadores import (
    ArmazenamentoEmDisco,
    CarregadorDeArvoresGedcom,
    RegistroDeAnalisesPostgres,
)
from utils.number_format import formatar_cm, formatar_inteiro

# As dependencias de borda que o nucleo consome (RF-09): leitura de CSV e
# emissao de diagrama. Montadas UMA vez, aqui na borda, e injetadas nos fluxos
# pelo caso de uso (D-05). Ate a extracao havia uma segunda montagem identica
# dentro do ramo de DNA, a cada requisicao; ela saiu em `T018`.
_DEPENDENCIAS = Dependencias(
    read_csv_with_fallback,
    detectar_colunas,
    aggregate_matches,
    generate_mermaid_graph,
    generate_mermaid_graph_indirect_bridge,
)

# RN-06 e RF-04: NAO ha identidade de usuario. O dono e um marcador unico do
# processo, e existe porque a costura precisa estar na assinatura ANTES de a Onda
# 3 do cutover chegar — adiar reabriria toda assinatura de porta (RF-08 da 006).
#
# Este e o UNICO lugar onde o valor do dono e declarado, e os TRES pontos deste
# arquivo que fornecem o valor o citam: as duas chamadas de `guardar` (a do GEDCOM
# pelo caso de uso e a do CSV aqui) e a de `carregar`. Nenhum deles escreve o
# literal no proprio local. O caso de uso `upload_gedcom` apenas REPASSA o que
# recebe — ele nao declara nem escolhe identidade.
#
# >>> NAO E MECANISMO DE SEGURANCA. <<<
#
# Nao ha sessao, login nem papel no sistema (`_reversa_sdd/permissions.md`, P-01 a
# P-05). Nenhum comportamento de isolamento depende deste valor, e nenhuma entrega
# desta feature pode ser citada como tendo implementado isolamento. Duas dividas
# seguem ABERTAS por decisao, e este comentario existe para que a costura nao seja
# lida como conserto:
#
#   #4 — ausencia de identidade e de isolamento entre donos. O armazenamento
#        continua unico por processo: dois donos com o mesmo conteudo chegam ao
#        MESMO arquivo, e isso e a `RN-02`, nao um defeito.
#   #3 — contaminacao entre requisicoes concorrentes. A guarda de exclusividade do
#        bloco `__main__` e de PROCESSO, nao de thread, e este parametro NAO a
#        substitui.
DONO_DO_PROCESSO = "unico"

# --- Configuração ---
app = Flask(__name__)
# `app.secret_key` foi REMOVIDO em 2026-10-05 por decisao do usuario
# (_reversa_sdd/questions.md#pergunta-2). Ele nao tinha consumidor: `flask.session`
# nunca foi importado e nenhum cookie era emitido. O literal estava versionado no
# repositorio e seria a chave de forja de sessao no instante em que alguem
# introduzisse sessao para tratar isolamento entre usuarios - exatamente a Rota 2
# descartada do BUG-20260929-BJJH. Ver _reversa_sdd/permissions.md (P-04).

# Teto de corpo de requisicao. Ausente no legado, e a ausencia fazia o multipart
# inteiro ser gravado em disco antes de qualquer verificacao de negocio
# (BUG-20260929-QMLY). Acima do teto o Flask aborta com 413 antes de ler o corpo.
#
# O valor passa a ter nome (`T004`, `D-10`). A `RN-01` permite nomear constantes e
# proibe alterar valores: o numero e o MESMO, e o que muda e existir um ponto unico
# de mudanca — e o teste poder citar a constante em vez de repetir o literal.
TETO_DE_UPLOAD_EM_BYTES = 16 * 1024 * 1024

# Derivado do mesmo teto para a mensagem de `413`, que fala em MB e nao em bytes.
# A divisao fica aqui, ao lado da origem, para as duas formas do MESMO teto
# mudarem juntas se o valor mudar um dia.
TETO_DE_UPLOAD_EM_MB = TETO_DE_UPLOAD_EM_BYTES // (1024 * 1024)

# O teto ACIMA, na camada que RECEBE a conexao (`waitress.max_request_body_size`).
#
# POR QUE ELE E NECESSARIO. O `MAX_CONTENT_LENGTH` do Flask so age quando o Flask ja tem o
# `environ` na mao — e o waitress acumula o corpo inteiro ANTES disso. O padrao do waitress e de
# **1 GB**, entao o teto de 16 MB nao impedia nada na camada de baixo: o multipart inteiro
# chegava (e, acima de `inbuf_overflow`, deixava de caber so em memoria) para so entao virar
# `413`. Era a classe do BUG-20260929-QMLY sobrevivendo uma camada abaixo da correcao que a
# declarou fechada.
#
# POR QUE COM MARGEM, e nao o valor exato. Com o limite do waitress IGUAL ao do Flask, um arquivo
# logo acima do teto seria cortado pelo servidor e o operador leria o `413` cru do waitress, sem a
# mensagem da aplicacao. A margem de 1 MB deixa a faixa proxima do teto chegar ao Flask e receber
# "Arquivo maior que o limite de 16 MB."; muito acima disso, o corte e do servidor — e ai o custo
# evitado (receber centenas de MB para recusar no fim) vale mais do que a mensagem bonita.
MARGEM_DO_MULTIPART = 1024 * 1024

app.config["MAX_CONTENT_LENGTH"] = TETO_DE_UPLOAD_EM_BYTES

# Formato dos numeros que o operador le (BUG-20261004-EWSJ). O template pede o
# filtro; a regra mora em `utils/number_format.py`, que e a autoridade unica.
app.add_template_filter(formatar_cm, "cm_br")
app.add_template_filter(formatar_inteiro, "inteiro_br")
# A data da coluna "Enviado em". A conversao e a MESMA autoridade unica usada pela lista, em
# `reporting/lista_de_arquivos.py`, e nao um `strftime` solto no template: data que o sistema
# nao converte tem de virar celula vazia em um lugar so.
app.add_template_filter(formatar_data_br, "data_br")
# O nome VISIVEL da arvore aberta, a partir do `gedcom_filename` que a rota ja passa em todas
# as renderizacoes. E filtro, e nao parametro de contexto, de proposito: a rota tem oito
# `render_template` com `gedcom_filename`, e acrescentar um argumento em cada um seria oito
# lugares para esquecer um — o mesmo defeito que o processador de contexto resolveu para as
# listas. O filtro reusa `rotulo_de_referencia`, que ja existia para as mensagens, entao o nome
# sai SEM a chave de conteudo pelo mesmo caminho de sempre.
app.add_template_filter(rotulo_de_referencia, "rotulo_do_arquivo")

# --- Cabecalho `Host` (E-02 do adendo 014) ---
#
# O QUE ISTO DEFENDE, E O QUE NAO DEFENDE. Nao e autenticacao: o `Host` e um cabecalho que
# qualquer cliente que nao seja navegador forja em uma linha, entao quem alcanca a porta com
# `curl` continua entrando igual. O que ele fecha e um vetor de NAVEGADOR — o DNS rebinding: uma
# pagina hostil que o operador abra enquanto a aplicacao roda resolve o proprio dominio para
# `127.0.0.1`, e as requisicoes seguintes chegam aqui em MESMA ORIGEM, com o navegador
# obedecendo. Sem sessao e sem cookie, nao ha nada entre essa pagina e as arvores, os relatorios
# de DNA (dado pessoal sensivel) e a acao destrutiva de aposentar.
#
# A DEFESA E A LISTA, e nao um token: o navegador manda no `Host` o nome que o atacante escolheu,
# e e justamente esse nome que nao esta na lista. O Flask 3.1 le esta chave nativamente
# (`flask/app.py`, `config["TRUSTED_HOSTS"]`) e recusa o resto **antes** de chegar a rota,
# cobrindo as quatro rotas e as tres rotas de arquivo.
#
# A PORTA NAO PARTICIPA DA COMPARACAO: `127.0.0.1` sozinho libera `:5000` e `:5080`. E o que faz
# uma entrada cobrir o acesso local e o do container ao mesmo tempo — o defeito de configuracao
# que uma lista por porta convidaria.
HOSTS_PERMITIDOS_PADRAO = ("127.0.0.1", "localhost")

# Nomes a mais, separados por virgula. Existe para o acesso que sai do loopback — o celular na
# rede, com `ANALISADOR_HOST=0.0.0.0`, onde o `Host` e o IP da maquina. Sem esta variavel esse
# acesso responde `400`, e a pagina diz QUAL host foi recusado, entao o diagnostico esta na tela.
ANALISADOR_HOSTS_PERMITIDOS = "ANALISADOR_HOSTS_PERMITIDOS"


def _hosts_permitidos() -> list[str]:
    """A lista do `TRUSTED_HOSTS`: os padrao mais o que a variavel de ambiente acrescentar."""
    extras = os.environ.get(ANALISADOR_HOSTS_PERMITIDOS, "")
    return list(HOSTS_PERMITIDOS_PADRAO) + [
        nome.strip() for nome in extras.split(",") if nome.strip()
    ]


# Em `config`, e nao lida dentro do tratador, para o teste poder trocar a lista sem mexer no
# ambiente — o mesmo padrao das chaves de arte e da folha.
app.config["TRUSTED_HOSTS"] = _hosts_permitidos()

UPLOAD_FOLDER = "uploads"


def _pasta_uploads() -> str:
    """Pasta de upload, ancorada no arquivo do app.

    Era relativa ao diretorio corrente, o que dava dois nomes para o mesmo
    arquivo: o caminho de escrita e o de leitura podiam divergir quando o CWD
    mudava. Foi o que quebrou a analise de DNA na correcao do BUG-20260929-QMLY
    (o CSV era gravado em `uploads/<chave>` e procurado como `<chave>`).
    Ancorar no arquivo torna escrita e leitura o MESMO caminho, sempre.

    `ANALISADOR_UPLOAD_FOLDER` permite apontar a pasta para outro lugar, o que e
    usado pelos testes para nao escreverem na pasta real.
    """
    apontada = os.environ.get("ANALISADOR_UPLOAD_FOLDER")
    if apontada:
        return apontada
    return os.path.join(os.path.dirname(os.path.abspath(__file__)), UPLOAD_FOLDER)


# A pasta e criada a partir da MESMA funcao que a resolve, para o diretorio
# criado no import e o procurado nas requisicoes nao poderem divergir.
os.makedirs(_pasta_uploads(), exist_ok=True)

# Os adaptadores concretos das portas, montados na borda (RF-02, D-07). Nenhum
# caso de uso instancia estes: ele recebe a porta por parametro. A pasta e
# resolvida UMA vez, aqui, e nao a cada requisicao — a funcao acima le o
# ambiente, e o ambiente nao muda no meio do processo.
_ARMAZENAMENTO = ArmazenamentoEmDisco(_pasta_uploads())
_CARREGADOR = CarregadorDeArvoresGedcom(_ARMAZENAMENTO)

# A quarta porta: o registro historico da analise (feature 008, `D-01`). Montada
# aqui, no ponto unico de montagem da borda, pelo mesmo motivo das outras duas.
#
# A REGRA DOS TRES ESTADOS (`D-02`):
#
#   1. sem `DATABASE_URL` -> registrador **nulo** (`None`), e nada muda na tela. E
#      este estado que protege a paridade das 6 fixtures e os 261 testes: a suite e
#      o harness de paridade **importam este modulo**, e avisar quando a persistencia
#      esta desligada por configuracao mudaria o contrato congelado de tela;
#   2. com a variavel e o banco respondendo -> grava;
#   3. com a variavel e a gravacao falhando -> a analise conclui e e exibida, com
#      aviso NAO bloqueante (`RN-13`, `RF-17`).
#
# NENHUMA CONEXAO ACONTECE AQUI, e o `import psycopg2` e preguicoso, dentro do
# metodo de gravacao: sem as duas coisas, `import app` quebraria a suite e a
# paridade **por ambiente**, porque o driver nao esta instalado no `.venv/` do host.
DATABASE_URL = os.environ.get("DATABASE_URL")
_REGISTRO = RegistroDeAnalisesPostgres(DATABASE_URL) if DATABASE_URL else None


@app.errorhandler(RequestEntityTooLarge)
def _requisicao_grande(_erro):
    return render_template(
        "index.html",
        message=f"Arquivo maior que o limite de {TETO_DE_UPLOAD_EM_MB} MB.",
        success=False,
    ), 413


@app.errorhandler(SecurityError)
def _host_recusado(erro):
    """Registra a recusa de `Host` e devolve o `400` que o Werkzeug ja montou.

    Sem esta linha a recusa nao deixa rastro NENHUM: a pagina diz ao operador qual host foi
    recusado, mas quem nao estiver olhando o navegador — ou quem ler o log depois — nao descobre
    nada. E o unico sinal que faltava no E-02.

    O corpo da resposta NAO muda: devolver a propria excecao faz o Flask responder o mesmo `400`
    com a mesma frase ("Host 'X' is not trusted."), que e o que torna o diagnostico possivel sem
    consultar o codigo.

    ## Por que o valor sai de `headers`, e NAO de `request.host`

    Porque `request.host` **valida de novo** e levanta o mesmo `SecurityError` — dentro do tratador
    que existe para registra-lo. Medido: o log nunca acontecia e a excecao subia do lugar errado.
    O cabecalho cru nao passa pela validacao, e e exatamente o que se quer registrar aqui.
    """
    app.logger.warning(
        "requisicao recusada pelo cabecalho Host: %s", request.headers.get("host")
    )
    return erro


# --- Cabecalho de enquadramento (BUG-20261013-X7EN) ---
#
# O QUE ISTO DEFENDE. A tela unica do sistema carrega o formulario da acao destrutiva
# (`action=aposentar_arquivo`, `templates/index.html:68-73`). Sem controle de enquadramento,
# outra origem pode embutir a pagina num `<iframe>` e sobrepor a interface; o `confirm()` do
# botao e barreira de INTERFACE, e nao de servidor. E o mesmo vetor de NAVEGADOR que o
# `TRUSTED_HOSTS` acima reconheceu — com a diferenca de que a lista de `Host` fecha o DNS
# rebinding e nao fecha o enquadramento.
#
# POR QUE `X-Frame-Options`, E NAO `frame-ancestors`. Os dois resolvem, e o `X-Frame-Options` e
# o unico que nao depende de politica de conteudo para existir. O `Content-Security-Policy`
# fica com o `BUG-20261013-4PYJ`, que precisa acomodar os hosts de CDN e o script inline do
# `mermaid.initialize` — um CSP mal calibrado quebraria o diagrama e o estilo da tela.
#
# POR QUE `after_request`, E NAO NO TEMPLATE. Cabecalho nao e conteudo: no template ele seria
# repetido em cada resposta e ainda assim nao cobriria as rotas de arte. Aqui vale para TODA
# resposta, e o corpo nao muda um byte — e o que mantem valido o invariante `SHA_DA_TELA` de
# `tests/test_icone_de_atalho.py`, que mede a tela e nao a borda.
@app.after_request
def _sem_enquadramento_por_terceiro(resposta):
    resposta.headers["X-Frame-Options"] = "DENY"
    return resposta


def _arvore_do_formulario() -> tuple[str | None, object | None, str | None]:
    """Arvore pedida pelo formulario: devolve `(referencia, arvore, mensagem)`.

    Fonte unica das duas guardas de entrada dos fluxos pos-upload (analise de
    DNA e busca de caminho). Antes da OPP-20261006-4KMB o mesmo par de guardas
    estava escrito em `index()` com as duas mensagens duplicadas.

    A `referencia` volta junto porque e ela que o template devolve no campo oculto
    `gedcom_filename`, para a requisicao seguinte. E o valor RECEBIDO do
    formulario, e nao uma forma derivada do caminho: e assim que o contrato de
    continuidade entre requisicoes sempre funcionou.

    Ate `T016` da feature 006 esta funcao resolvia o caminho por
    `_resolver_caminho_armazenado` e chamava `carregar_arvore` direto — as duas
    coisas que a `RF-01` tira do adaptador de entrada. Agora quem resolve e quem
    parseia sao as portas: `CarregadorDeArvores` resolve a referencia e devolve a
    arvore, e `None` significa que a referencia nao aponta para arquivo existente.

    A uniao e explicita de proposito, e o chamador repete a guarda de `None`. O
    checador nao estreita o segundo elemento da tupla por `erro is not None`,
    entao sem as duas a chamada do carregador recebe `str | None`.

    ## O parse tem guarda, e o motivo foi MEDIDO

    Ate 2026-10-10 esta funcao chamava `_CARREGADOR.carregar` **fora de qualquer `try`**, e os
    `except` de `index()` comecam depois da chamada dela. Um arquivo que a referencia ALCANCA e
    cujo conteudo o `ged4py` nao consegue ler derrubava a requisicao com `500` e traceback, no
    lugar de dizer ao operador o que houve. Reproduzido pela rota:

        POST / com gedcom_filename=0e85a4f3052e19e3__Genealogia_Mineira.csv  ->  500
        OSError: Unexpected EOF while reading GEDCOM header

    E nao era caso de laboratorio: **10 dos 13 arquivos da pasta real** derrubavam o parser.
    Eles nao sao GEDCOM, e o `guardar` nunca os aceitaria como tal — mas o `guardar` e o caminho
    de ENVIO, e a pasta pode receber arquivo por fora da aplicacao. O que se mediu e que o
    caminho de CLIQUE nao chega la (a aba de DNA nao oferece "Abrir"), mas a REQUISICAO chega, e
    a aplicacao nao tem autenticacao.

    ## As mensagens usam o ROTULO, e nao a referencia

    As duas mensagens de erro montavam `f"... '{referencia}' ..."`, e `referencia` e o nome
    **armazenado** — que comeca com os 16 hexadecimais da chave de conteudo. O operador ve o
    NOME, nunca a chave, e o erro era o unico lugar da tela que ainda a mostrava. Agora as duas
    passam por `rotulo_de_referencia`, o mesmo formatador das outras mensagens.
    """
    referencia = request.form.get("gedcom_filename")
    if not referencia:
        return None, None, "Erro: Arquivo GEDCOM não encontrado."
    try:
        arvore = _CARREGADOR.carregar(referencia, DONO_DO_PROCESSO)
    except Exception:
        # O traceback vai para o LOG, e nao para a tela: o operador precisa de uma frase que
        # diga o que aconteceu, e quem depura precisa do rastro. Antes desta guarda os dois
        # ficavam sem nada — a tela mostrava o traceback e ninguem o registrava.
        app.logger.exception("GEDCOM alcancado pela referencia nao pode ser lido")
        return None, None, (
            f"Erro: o arquivo '{rotulo_de_referencia(referencia)}' não pôde ser lido como GEDCOM. "
            "Ele pode estar corrompido, vazio, ou não ser um GEDCOM de verdade."
        )
    if arvore is None:
        return None, None, f"Erro: Arquivo '{rotulo_de_referencia(referencia)}' não existe mais."
    return referencia, arvore, None


# --- Icone de atalho (feature 009) ---
#
# A ARTE SERVIDA AQUI NAO E A CANONICA. `docs/assets/img/logo.png` tem 32,5 % de pixels
# transparentes, e o sistema movel compoe transparencia sobre PRETO no icone de tela
# inicial: servir a canonica daria um quadrado preto com o desenho por cima, incluindo as
# aberturas internas entre folhas e galhos. O que esta rota serve e uma RENDERIZACAO
# DERIVADA - opaca, 180x180, composta sobre branco - e a receita que a produz tem fonte
# unica em `tests/icone_de_atalho.py`, com o teste de deriva ao lado dela.
#
# O CAMINHO E CONVENCAO, NAO ESCOLHA. Nao ha como declarar o icone de atalho no documento
# e ser obedecido: o sistema procura este caminho na raiz. Por isso a rota e um acrescimo
# PURO - o template nao e tocado, e o `GET /` continua byte a byte o mesmo (`RN-02`).
#
# POR QUE `src/assets/`: o `.dockerignore` deste projeto e lista de PERMISSAO (`*`, depois
# `!requirements.txt`, `!src/`, `!src/**`). Arte em qualquer outra pasta responderia 200
# na maquina de desenvolvimento e 404 dentro do container - falha silenciosa no ambiente
# que o operador usa. `src/static/` continua PROIBIDA pelo `W004`.
ARTE_DO_ICONE = os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "assets", "apple-touch-icon.png"
)
# Em `config` para que o caso de ausencia seja testavel sem tocar no repositorio: o teste
# aponta a chave para um caminho inexistente em vez de mexer na arte de verdade.
app.config["ARTE_DO_ICONE"] = ARTE_DO_ICONE


@app.route("/apple-touch-icon.png", methods=["GET"])
def icone_de_atalho():
    """Serve o icone de atalho (`RF-01`).

    Registrada SO com `GET`: a recusa de escrita sai do roteador com `405`, sem uma linha
    de validacao nossa que pudesse divergir da convencao.

    Sem `Cache-Control` de validade longa (`D-05`). A arte foi trocada duas vezes em um
    unico dia, e uma validade de um ano congelaria o cliente que ja tivesse buscado. O
    `ETag` que o proprio `send_file` emite responde `304` sem corpo na rebusca, e e isso
    que da a revalidacao barata sem prender o cliente.

    Arte ausente devolve `404` e **nada mais muda**: o atalho degrada para icone generico
    e nenhuma rota existente altera a resposta (`RN-08`).
    """
    caminho = app.config["ARTE_DO_ICONE"]
    if not os.path.isfile(caminho):
        return "", 404
    return send_file(caminho, mimetype="image/png")


# --- Arte do topo da tela (feature 011) ---
#
# A pedido do operador, o topo deixou de ser so texto e passou a ter a arte dele. O desenho da
# rota e o MESMO do icone de atalho acima, e pelas mesmas razoes: `GET` sozinho, para a recusa
# de escrita sair do roteador com `405` sem uma linha nossa que pudesse divergir da convencao;
# o `ETag` do `send_file` respondendo `304` sem corpo na rebusca; e **arte ausente devolve
# `404` e nada mais muda**, para a tela continuar de pe.
#
# A ARTE SERVIDA NAO E A QUE O OPERADOR ENVIOU. O arquivo que ele mandou chegou em `RGB`, sem
# canal alfa, com o quadriculado de transparencia **gravado no bitmap** — servir aquilo
# desenharia uma grade cinza atras do desenho. O que esta rota serve e uma RENDERIZACAO
# DERIVADA, com o fundo removido, e a receita que a produz tem fonte unica em
# `tests/banner_da_tela.py`, ao lado do teste de regressao da arte.
#
# `src/assets/`, e nao `docs/assets/`: o `.dockerignore` deste projeto e lista de PERMISSAO
# (`*`, depois `!src/`, `!src/**`), entao arte em `docs/` responderia 200 na maquina de
# desenvolvimento e 404 dentro do container — falha silenciosa no ambiente que o operador usa.
ARTE_DO_TOPO = os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "assets", "banner-da-tela.png"
)
# Em `config` pelo mesmo motivo do icone: o caso de ausencia fica testavel apontando a chave
# para um caminho inexistente, sem tocar na arte de verdade.
app.config["ARTE_DO_TOPO"] = ARTE_DO_TOPO


@app.route("/banner.png", methods=["GET"])
def banner_do_topo():
    """Serve a arte do topo da tela.

    Registrada so com `GET`, e sem validade longa de cache: e a mesma arte que muda ao sabor do
    pedido do operador, e o `ETag` ja da a revalidacao barata sem prender o cliente que ja a
    buscou uma vez.
    """
    caminho = app.config["ARTE_DO_TOPO"]
    if not os.path.isfile(caminho):
        return "", 404
    return send_file(caminho, mimetype="image/png")


# A arte do topo traz "Analisador Genealogico" DESENHADO nela, entao o `<h1>` fica `visually-hidden`
# enquanto ela responde: mostrar os dois nomearia o produto duas vezes, uma logo abaixo da outra. O
# `<h1>` nao sai do documento — ele continua sendo o titulo de nivel 1 para leitor de tela e buscador.
#
# A CONDICAO E DO SERVIDOR, e nao do navegador. O CSS nao sabe se uma imagem carregou, e o JS so
# descobriria depois de a pagina pintar — tarde para quem ja leu o topo. Aqui a pergunta e feita antes
# de renderizar, e `os.path.isfile` e a MESMA pergunta que a rota responde em `404`: as duas nao podem
# divergir.
#
# POR QUE ISSO IMPORTA. Sem a arte, esconder o `<h1>` deixaria o operador com o subtitulo em ingles e
# **nenhuma** identificacao do produto em portugues. Era o caso que o `RN-08` declara suportado (a arte
# pode faltar e a tela continua de pe) e que ficou descoberto quando o `<h1>` passou a ser escondido.
#
# Vem por processador de contexto, e nao por argumento nos oito `render_template`, pelo mesmo motivo das
# listas: seriam oito lugares para esquecer um.
@app.context_processor
def _arte_do_topo_disponivel():
    """`True` enquanto o arquivo da arte do topo estiver no disco.

    Lida de `app.config` a cada renderizacao, e nao capturada no import: e o que permite ao teste
    apontar `ARTE_DO_TOPO` para um caminho inexistente e medir a tela sem a arte.
    """
    return {"arte_do_topo_disponivel": os.path.isfile(app.config["ARTE_DO_TOPO"])}


# --- A folha de estilo da tela ---
#
# A identidade visual saiu do `<style>` embutido no template e passou a ser um ARQUIVO
# servido, com o MESMO desenho das duas rotas de arte acima: `GET` sozinho, para a recusa
# de escrita sair do roteador com `405`; o `ETag` do `send_file` respondendo `304` sem
# corpo na rebusca; e **arquivo ausente devolve `404` e nada mais muda** — a tela continua
# de pe, apenas sem a identidade visual, que e degradacao aceitavel.
#
# POR QUE UMA ROTA, E NAO `src/static/`. A pasta estatica e PROIBIDA pelo `W004` (feature
# 003), e o `RN-07` da feature 009 proibe CONFIGURAR diretorio estatico. `src/assets/` e a
# pasta que o `.dockerignore` deixa entrar na imagem (`!src/**`), entao o arquivo responde
# igual na maquina de desenvolvimento e dentro do container — servido de `src/templates/`
# ou da raiz, responderia `200` no host e `404` no ambiente do operador.
#
# SEM VALIDADE LONGA DE CACHE, pela mesma razao das duas artes: a folha muda ao sabor do
# pedido do operador, e uma validade longa congelaria o cliente que ja a tivesse buscado. O
# `ETag` ja da a revalidacao barata.
ESTILO_DA_TELA = os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "assets", "app.css"
)
# Em `config` para o caso de ausencia ser testavel sem tocar no arquivo, como nas artes.
app.config["ESTILO_DA_TELA"] = ESTILO_DA_TELA


@app.route("/app.css", methods=["GET"])
def estilo_da_tela():
    """Serve a folha de estilo da tela.

    O `mimetype` e declarado, e nao adivinhado pelo `send_file`: o navegador so aplica a
    folha se o `Content-Type` for `text/css`, e a extensao `.css` seria a unica coisa a
    sustenta-lo.
    """
    caminho = app.config["ESTILO_DA_TELA"]
    if not os.path.isfile(caminho):
        return "", 404
    return send_file(caminho, mimetype="text/css")


# --- As listas da tela (feature 011) ---
#
# O `GET /` entrega as duas abas com as listas **sempre**, e nao apenas depois de um envio.
# Como a tela precisa delas em TODA renderizacao, elas entram por um processador de contexto
# em vez de repetidas nos oito `render_template("index.html", ...)` da rota: repetir seria oito
# lugares para esquecer um, e o nono nasceria desatualizado.
#
# **Nao ha `os.listdir` aqui.** Quem le a pasta e a PORTA: a rota so compoe o que ela devolve.
# Foi a feature 006 que tirou o acesso a disco da borda, e um `listdir` neste arquivo o traria
# de volta — alem de tornar a listagem impossivel de testar sem pasta real.
#
# O que a listagem NAO faz, por decisao: nao abre conteudo e nao filtra arquivo nenhum. Separar
# as abas e marcar o item indisponivel e trabalho da funcao pura de `reporting/`, que decide
# pelo NOME.
#
# **O instrumento de paridade nao enxerga isto.** `harness.py:191` substitui
# `render_template` por uma captura de contexto, entao o processador nem chega a rodar; e as
# chaves que ele le (`:211-221`) continuam sendo as mesmas de antes. Acrescentar chave ao
# contexto e invisivel para ele, por construcao.
@app.context_processor
def _listas_da_tela():
    """As duas listas de arquivos armazenados, para as abas da tela de entrada.

    A selecao por extensao do nome visivel, o agrupamento pela chave e a ordem por data moram
    na funcao pura: aqui so se pergunta a ela duas vezes, uma por aba. As extensoes que
    decidem cada aba vem declaradas la, e nao escritas de novo neste arquivo — a particao tem
    um dono so.
    """
    entradas = _ARMAZENAMENTO.listar(DONO_DO_PROCESSO)
    return {
        "arvores_da_lista": itens_da_aba(entradas, ABA_DE_ARVORES),
        "relatorios_da_lista": itens_da_aba(entradas, ABA_DE_DNA),
    }


# --- Rota Principal ---
@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        action = request.form.get("action")
        if action == "upload_gedcom":
            if "gedcom" not in request.files:
                return render_template("index.html", message="Nenhum arquivo GEDCOM enviado.", success=False)
            gedcom_file = request.files["gedcom"]
            if gedcom_file.filename == '':
                return render_template("index.html", message="Nenhum arquivo selecionado.", success=False)
            try:
                resultado = caso_de_uso_de_upload(
                    gedcom_file.read(), gedcom_file.filename, DONO_DO_PROCESSO,
                    _ARMAZENAMENTO, _CARREGADOR)
                return render_template("index.html", gedcom_filename=resultado.referencia, all_names=resultado.nomes, message=resultado.mensagem, success=True)
            except ErroDeDominio as erro_de_dominio:
                # A recusa de conteudo passa por aqui. O texto e o MESMO de antes
                # da extracao (`Arquivo nao reconhecido como GEDCOM: ...`), e a
                # unica diferenca e que agora a condicao chega TIPADA: a moldura
                # e da tabela de traducao, e o motivo veio dentro da excecao.
                return render_template("index.html", message=traduzir(erro_de_dominio).mensagem, success=False)
            except HTTPException:
                # Erro do CLIENTE (campo obrigatorio ausente, corpo malformado) NAO e falha
                # inesperada nossa, e era engolido pelo `except Exception` logo abaixo: o operador
                # recebia **200** com o texto interno do Werkzeug na tela. Sobe para o Flask
                # responder o status certo, como ja acontece com o `413` do teto de upload.
                raise
            except Exception as e:
                # O LITERAL E CONTRATO CONGELADO (`upload-gedcom/contracts.md` secao de literais):
                # ele nao muda aqui. O que faltava era o RASTRO — a extracao registra "Nada e
                # registrado em log" como lacuna de gravidade alta, e esta linha e a que a fecha.
                app.logger.exception("falha inesperada no envio de GEDCOM")
                return render_template("index.html", message=f"Erro ao processar GEDCOM: {e}", success=False)

        if action == "aposentar_arquivo":
            # Aposentar um arquivo da lista (`RN-14`).
            #
            # ESTE RAMO VEM ANTES de `_arvore_do_formulario`, e a ordem e a regra, nao estilo:
            # `_arvore_do_formulario` resolve E PARSEIA a arvore escolhida, e a arvore
            # escolhida pode ser exatamente a que se esta aposentando. Depois do move, o parse
            # falharia e o operador leria "arquivo nao existe mais" no lugar da confirmacao — a
            # acao teria funcionado e a tela diria que nao.
            #
            # Nada e apagado: o arquivo sai da lista e continua no disco, em `_aposentados/`. A
            # mensagem diz isso com todas as letras, porque "apagar" e o que o botao parece
            # fazer, e o operador precisa saber que da para voltar.
            referencia = request.form.get("arquivo_a_aposentar")
            if _ARMAZENAMENTO.aposentar(referencia, DONO_DO_PROCESSO):
                return render_template(
                    "index.html",
                    message=(f"'{rotulo_de_referencia(referencia)}' saiu da lista. "
                             "O arquivo não foi apagado: ele continua guardado, inteiro, "
                             "na pasta de aposentados."),
                    success=True)
            return render_template(
                "index.html",
                message="Não foi possível aposentar o arquivo: ele não está mais na pasta.",
                success=False)

        gedcom_filename, arvore, erro = _arvore_do_formulario()
        if erro is not None:
            return render_template("index.html", message=erro, success=False)
        if arvore is None:
            # Inalcancavel em execucao: `erro` e `arvore` sao preenchidos juntos.
            # Existe para o checador de tipos estreitar a uniao do retorno.
            return render_template("index.html", message="Erro: Arquivo GEDCOM não encontrado.", success=False)
        all_names = nomes_de_exibicao(arvore)

        if action == "selecionar_arvore":
            # Escolher a arvore CLICANDO na lista. A referencia ja foi resolvida por
            # `_arvore_do_formulario`, e o unico trabalho deste ramo e renderizar o estado
            # "arvore escolhida" — o MESMO que o envio produz.
            #
            # O ramo existe porque, sem ele, esta `action` cairia no `return` do fim de
            # `index()`, que renderiza `index.html` SEM `gedcom_filename`: a arvore resolvida
            # seria descartada e o operador clicaria sem nada acontecer. Era o defeito medido
            # em 2026-10-09 — a lista mostrava as arvores e nao havia como escolher nenhuma.
            #
            # Nao ha efeito colateral: nenhum arquivo e lido alem do parse que
            # `_arvore_do_formulario` ja fez, e nada e escrito.
            return render_template("index.html", gedcom_filename=gedcom_filename, all_names=all_names)

        if action == "dna_analysis":
            try:
                # O `.strip()` alinha a analise de DNA com a busca de caminho, que ja o faz nos
                # dois nomes (`person1_name`/`person2_name`, logo abaixo). Sem ele, um espaco
                # colado junto ao nome — vindo do GEDCOM, de um export do Gedmatch ou de um
                # copiar-e-colar — fazia a pessoa NAO ser encontrada, e o operador lia
                # "Seu nome 'Carlos Silva Souza ' nao foi encontrado" sem entender por que.
                #
                # O VAZIO NAO PODE SEGUIR, e a razao e medida: o nucleo casa por
                # `root_name.lower() in nome` (`core/dna_analysis.py`), e `"" in "qualquer
                # coisa"` e **verdadeiro** — um nome que virasse vazio escolheria a PRIMEIRA
                # pessoa da arvore, em silencio, e a analise sairia com o parentesco errado. Por
                # isso o valor BRUTO volta quando o strip esvazia: o nucleo entao levanta
                # `PessoaNaoEncontrada` e o operador recebe a mensagem de sempre.
                nome_informado = request.form["root_name"]
                root_name = nome_informado.strip() or nome_informado

                # A referencia escolhida na LISTA tem **precedencia** sobre o arquivo, e o
                # campo novo e OPCIONAL. Quando ele nao vem, o caminho abaixo e exatamente o
                # de antes — mesma gravacao, mesma porta, mesma mensagem. Foi por isso que o
                # campo e NOVO em vez de reaproveitar `matches_csv`: reaproveitar apagaria a
                # prova de que o caminho antigo continua igual, e e essa prova que a paridade
                # e os testes de rota consomem.
                referencia_do_csv = request.form.get("matches_csv_filename")
                # `None` enquanto nao houver substituicao de versao do CSV. Inicializado aqui
                # porque os TRES caminhos abaixo — CSV da lista, CSV enviado e CSV substituido
                # — chegam ao MESMO `render_template` do fim.
                aviso_de_substituicao = None
                if referencia_do_csv:
                    caminho_do_csv = _ARMAZENAMENTO.resolver(referencia_do_csv, DONO_DO_PROCESSO)
                    if caminho_do_csv is None:
                        # Mesma classe de mensagem do caminho de uso da arvore: a tela continua
                        # utilizavel e o operador ve o que aconteceu. O texto e o mesmo de
                        # `_arvore_do_formulario` porque a causa e a mesma.
                        return render_template("index.html", gedcom_filename=gedcom_filename, all_names=all_names, message=f"Erro: Arquivo '{rotulo_de_referencia(referencia_do_csv)}' não existe mais.", success=False)
                else:
                    if "matches_csv" not in request.files or not request.files["matches_csv"].filename:
                        return render_template("index.html", gedcom_filename=gedcom_filename, all_names=all_names, message="Por favor, carregue o arquivo CSV de matches.", success=False)
                    matches_file = request.files["matches_csv"]

                    # A gravacao do CSV passa pela MESMA porta do GEDCOM. O tipo `"csv"` nao
                    # valida conteudo — a assimetria com o GEDCOM e a divida #10, preservada de
                    # proposito.
                    #
                    # A regra de reenvio e a MESMA do GEDCOM, pela mesma funcao — e nao um
                    # segundo bloco parecido. Antes disso, reenviar um CSV com conteudo novo
                    # deixava DUAS linhas de mesmo rotulo na aba de DNA: medido na pasta do
                    # operador, com dois `Familias_Sergipanas.csv`.
                    armazenado = guardar_com_substituicao(
                        _ARMAZENAMENTO, matches_file.read(), matches_file.filename,
                        "csv", DONO_DO_PROCESSO)
                    caminho_do_csv = armazenado.caminho
                    if armazenado.motivo is not None:
                        return render_template("index.html", gedcom_filename=gedcom_filename, all_names=all_names, message=armazenado.motivo, success=False)
                    if armazenado.desfecho == SUBSTITUIDO:
                        # O aviso entra DEPOIS da analise, junto do resultado: a analise e o
                        # assunto da tela, e a substituicao e uma nota sobre o insumo dela. Ele
                        # nao pode substituir a mensagem do resultado.
                        aviso_de_substituicao = (
                            f"O CSV '{armazenado.visivel}' substituiu a versão anterior, que "
                            "saiu da lista e continua guardada na pasta de aposentados."
                        )

                resultado = caso_de_uso_dna(
                    caminho_do_csv, root_name, arvore, _DEPENDENCIAS, DONO_DO_PROCESSO,
                    gedcom_filename, _REGISTRO)
                # O aviso da substituicao do CSV acompanha a mensagem do resultado, e nao a
                # substitui: a analise e o assunto da tela (`T038`).
                mensagem_final = resultado.mensagem
                if aviso_de_substituicao:
                    mensagem_final = f"{mensagem_final} {aviso_de_substituicao}"
                return render_template(
                    "index.html",
                    gedcom_filename=gedcom_filename,
                    all_names=all_names,
                    dna_results=resultado.resultados,
                    skipped_matches=resultado.descartados,
                    message=mensagem_final,
                    aviso_de_persistencia=resultado.aviso_de_persistencia,
                    success=True
                )
            except ErroDeDominio as erro_de_dominio:
                return render_template("index.html", gedcom_filename=gedcom_filename, all_names=all_names, message=traduzir(erro_de_dominio).mensagem, success=False)
            except HTTPException:
                # Ver a nota do ramo de envio: erro de cliente nao pode virar `200` com texto
                # interno. Aqui o caso concreto e `root_name` ausente, que levanta
                # `BadRequestKeyError` — e que respondia `200` dizendo "Ocorreu um erro: 400 Bad
                # Request: The browser (or proxy) sent a request that this server could not
                # understand."
                raise
            except Exception as e:
                app.logger.exception("falha inesperada na analise de DNA")
                return render_template("index.html", gedcom_filename=gedcom_filename, all_names=all_names, message=f"Ocorreu um erro: {e}", success=False)

        if action == "path_search":
            try:
                person1_name = request.form["person1_name"].strip()
                person2_name = request.form["person2_name"].strip()

                resultado = caso_de_uso_de_busca(
                    person1_name, person2_name, arvore, _DEPENDENCIAS, DONO_DO_PROCESSO)

                # O modo de renderizacao vem do DESFECHO, nunca do texto: sao dois
                # casos que o operador ve de formas diferentes e que hoje so se
                # distinguem por uma linha de codigo — "pessoa nao encontrada"
                # (alerta de erro) e "nenhuma conexao encontrada" (cartao, com
                # sucesso). `D-11`.
                if resultado.desfecho is Desfecho.ERRO_DE_ENTRADA:
                    return render_template("index.html", gedcom_filename=gedcom_filename, all_names=all_names,
                                           message=resultado.mensagem, success=False)
                return render_template("index.html", gedcom_filename=gedcom_filename, all_names=all_names,
                                       path_result=resultado.dados, message=resultado.mensagem, success=True)
            except ErroDeDominio as erro_de_dominio:
                return render_template("index.html", gedcom_filename=gedcom_filename, all_names=all_names,
                                       message=traduzir(erro_de_dominio).mensagem, success=False)
            except HTTPException:
                # Ver a nota do ramo de envio: erro de cliente nao pode virar `200` com texto
                # interno.
                raise
            except Exception as e:
                app.logger.exception("falha inesperada na busca de caminho")
                return render_template("index.html", gedcom_filename=gedcom_filename, all_names=all_names,
                                       message=f"Ocorreu um erro: {e}", success=False)

    return render_template("index.html")


if __name__ == "__main__":
    # Configuracao de execucao lida do ambiente, com os padroes declarados aqui.
    # Mesmo padrao ja praticado pelo projeto em `ANALISADOR_UPLOAD_FOLDER`.
    #
    # O padrao do endereco e a maquina local (RF-02). A aplicacao nao tem
    # autenticacao alguma, entao atender a rede passa a ser ato explicito de quem
    # opera, e nao o comportamento que acontece por omissao.
    endereco_de_escuta = os.environ.get("ANALISADOR_HOST", "127.0.0.1")
    porta_de_escuta = int(os.environ.get("ANALISADOR_PORT", "5000"))
    concorrencia = int(os.environ.get("ANALISADOR_THREADS", "4"))

    # O import fica aqui dentro de proposito. Este modulo e importado pela suite de
    # testes e pela instrumentacao de paridade, e um import no topo obrigaria o
    # servidor de producao instalado em quem so quer a aplicacao como objeto.
    try:
        from waitress import serve
    except ImportError:
        # A mensagem nomeia o pacote e o interpretador exato (D-08) e aponta para o
        # arquivo de dependencias, e nao para o pacote solto: desde a fixacao das
        # versoes, instalar o pacote avulso traria uma versao diferente da validada.
        raise SystemExit(
            "Servidor de producao ausente neste interpretador: o pacote waitress nao "
            "esta instalado. Instale a partir do arquivo de dependencias, com: "
            f"{sys.executable} -m pip install -r requirements.txt"
        )

    # --- Guarda de exclusividade (RN-05, RF-08) ---
    #
    # A medicao de 2026-10-04 mostrou que a plataforma NAO impede a coexistencia:
    # o servidor pede SO_REUSEADDR, e no Windows duas instancias escutam na mesma
    # porta ao mesmo tempo. Duas instancias compartilham o MESMO diretorio de
    # uploads (`src/uploads/`), entao gravam e leem os mesmos arquivos, e
    # requisicoes do mesmo operador caem em instancias diferentes. A exclusividade
    # e, portanto, responsabilidade daqui.
    #
    # Ate a feature 005 havia um motivo a mais — o estado global da arvore, que
    # fazia as duas instancias divergirem em memoria. O estado saiu, e o motivo que
    # fica e o armazenamento em disco.
    #
    # O socket e criado, marcado e LIGADO aqui, e entregue ja pronto ao servidor.
    # Com socket pronto o servidor nao faz bind (bind_socket=False), entao quem liga
    # e este bloco. O socket fica aberto ate o processo terminar: fechar para so
    # entao servir abriria uma janela entre fechar e servir, que e exatamente o que
    # a marca de uso exclusivo existe para nao ter.
    socket_de_escuta = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    if hasattr(socket, "SO_EXCLUSIVEADDRUSE"):
        # Windows: a porta fica exclusiva deste processo, e outra instancia recebe
        # erro no bind mesmo pedindo SO_REUSEADDR.
        socket_de_escuta.setsockopt(socket.SOL_SOCKET, socket.SO_EXCLUSIVEADDRUSE, 1)
    else:
        # Fora do Windows a marca nao existe, e o padrao da plataforma ja recusa a
        # segunda ligacao. Reintroduzir SO_REUSEADDR aqui traria de volta a
        # coexistencia que esta guarda existe para impedir.
        socket_de_escuta.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 0)
    # O servidor deixa o socket que ele mesmo cria em modo nao bloqueante; o socket
    # entra no lugar dele, e entra com a mesma postura.
    socket_de_escuta.setblocking(False)

    try:
        socket_de_escuta.bind((endereco_de_escuta, porta_de_escuta))
        socket_de_escuta.listen(socket.SOMAXCONN)
    except OSError as erro:
        socket_de_escuta.close()
        # O diagnostico separa os dois motivos porque eles pedem acoes diferentes:
        # porta ocupada se resolve encerrando quem esta no ar ou trocando de porta,
        # e endereco indisponivel se resolve corrigindo ANALISADOR_HOST. Medido em
        # 2026-10-04: porta ocupada chega com errno.EADDRINUSE, e endereco que nao
        # existe nesta maquina chega com 10049, que nao e EADDRINUSE.
        if erro.errno == errno.EADDRINUSE:
            motivo = f"{endereco_de_escuta}:{porta_de_escuta} ja esta em uso"
            saida = (
                "Encerre o processo que ja esta no ar, ou suba esta instancia em "
                "outra porta com ANALISADOR_PORT."
            )
        else:
            motivo = f"nao foi possivel escutar em {endereco_de_escuta}:{porta_de_escuta}"
            saida = (
                "Confira se ANALISADOR_HOST aponta para um endereco desta maquina e "
                "se ANALISADOR_PORT e uma porta valida."
            )
        # A mensagem nao afirma quem ocupa a porta: pode ser uma instancia anterior
        # desta aplicacao ou qualquer outro processo.
        raise SystemExit(f"Recusando subir: {motivo} ({erro.strerror or erro}). {saida}")

    print(
        f"Servindo com waitress em http://{endereco_de_escuta}:{porta_de_escuta} "
        f"com {concorrencia} threads",
        flush=True,
    )
    # `sockets` e mutuamente exclusivo de `host` e `port`: o servidor levanta
    # ValueError se receber `sockets` junto de qualquer um dos dois. Endereco e
    # porta ja estao no socket ligado.
    serve(app, sockets=[socket_de_escuta], threads=concorrencia,
          max_request_body_size=TETO_DE_UPLOAD_EM_BYTES + MARGEM_DO_MULTIPART)

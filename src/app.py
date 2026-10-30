from application.path_search import ResultadoDeBusca
from application.dna_analysis import ResultadoDeAnalise
from application.reenvio import ResultadoDeArmazenamento
from typing import Any
from application.upload_gedcom import ResultadoDeUpload
from werkzeug.datastructures.file_storage import FileStorage
from reporting.lista_de_arquivos import ItemDaLista
from ports.email_smtp import EmailPorSmtp
from typing import Literal
import errno
import logging
import os
import socket
import sys
from datetime import datetime, timedelta, timezone

from flask import Flask, current_app, g, render_template, request
from reporting.lista_de_arquivos import (
    ABA_DE_ARVORES,
    ABA_DE_DNA,
    formatar_data_br,
    itens_da_aba,
    rotulo_de_referencia,
)
from werkzeug.exceptions import HTTPException, RequestEntityTooLarge, SecurityError

from application import Desfecho, nomes_de_exibicao
from application.busca_de_nome import ServicoDeBusca
from application.cadastro import ServicoDeCadastro
from application.definir_senha import ServicoDeDefinirSenha
from application.dna_analysis import dna_analysis as caso_de_uso_dna
from application.entrada_com_senha import ServicoDeEntradaLocal
from application.limite import Limitador
from application.path_search import path_search as caso_de_uso_de_busca
from application.recuperacao import ServicoDeRecuperacao
from application.reenvio import SUBSTITUIDO, guardar_com_substituicao
from application.sessao_da_conta import VerificadorDeVersao
from application.traducao import traduzir
from application.upload_gedcom import upload_gedcom as caso_de_uso_de_upload
from application.vinculo import VinculoDeIdentidade
from core.dna_analysis import Dependencias
from core.erros import ErroDeDominio
from parsers.csv_ingest import (
    aggregate_matches,
    detect_columns as detectar_colunas,
    read_csv_with_fallback,
)
from reporting.mermaid_render import (
    anotar_profundidade,
    generate_mermaid_graph,
    generate_mermaid_graph_indirect_bridge,
    mermaid_da_sugestao,
)
from web.autenticacao import ServicoDeEntrada, servico_do_ambiente
from web.modo import GOOGLE, RecusaDeSubida, ler as ler_modo
from web.rotas_assets import assets_bp
from web.rotas_auth import auth_bp
from web.rotas_busca import busca_bp
from web.rotas_conta import conta_bp
from web.sessao import instalar_guarda
from web.hooks_de_registro import (
    instalar as instalar_registro,
    ip_do_cliente,
    origem_da_requisicao,
)
from ports.adaptadores import (
    ArmazenamentoEmDisco,
    CarregadorDeArvoresGedcom,
    RegistroDeAnalisesPostgres,
)
from ports.contas_em_arquivo import ContasEmArquivo
from ports.email_smtp import TransporteNulo, transporte_do_ambiente
from ports.fontes_de_nomes import NomesDaArvoreGedcom, NomesDoArquivoDeMatches
from utils import logs
from utils.auditoria import registrar as auditar
from utils.number_format import formatar_cm, formatar_inteiro, formatar_tamanho

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
    anotar_profundidade,
    # O emissor da arvore sugerida entra pelo mesmo seam (feature 032): `core/` nao
    # pode importar `reporting/` (ADR-34), entao quem monta o texto e a borda.
    mermaid_da_sugestao,
)

# O dono do caminho SEM entrada (feature 051). Com a autenticacao ligada, o valor
# vem da sessao (`g.dono`) e este literal nao e usado; sem ela, e o que a suite e o
# harness de paridade exercitam — o modo em que a aplicacao sobe apenas por import,
# nunca por servidor, porque a subida recusa sem as cinco variaveis.
#
# A divida #4 (ausencia de isolamento) FECHA na feature 051: o `dono` passa a
# escopar o armazenamento e o historico. A #3 (corrida sobre o disco) continua
# aberta, e este literal nao tem relacao com ela.
DONO_DO_PROCESSO = "unico"


def _dono() -> str:
    """O dono da requisicao: o `sub` da conta quando ha entrada; o marcador quando nao ha.

    A sessao e assinada, e o `sub` ja passou pela guarda; o literal e o caminho sem
    autenticacao, exercitado pela suite e pelo harness de paridade.
    """
    return getattr(g, "dono", "") or DONO_DO_PROCESSO

# --- Configuração ---
# A instancia da aplicacao e criada por `create_app()`, no fim do modulo.
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
TETO_DE_UPLOAD_EM_BYTES: Literal[16777216] = 16 * 1024 * 1024

# Derivado do mesmo teto para a mensagem de `413`, que fala em MB e nao em bytes.
# A divisao fica aqui, ao lado da origem, para as duas formas do MESMO teto
# mudarem juntas se o valor mudar um dia.
TETO_DE_UPLOAD_EM_MB: Literal[16] = TETO_DE_UPLOAD_EM_BYTES // (1024 * 1024)

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
MARGEM_DO_MULTIPART: Literal[1048576] = 1024 * 1024



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
    extras: str = os.environ.get(ANALISADOR_HOSTS_PERMITIDOS, "")
    return list(HOSTS_PERMITIDOS_PADRAO) + [
        nome.strip() for nome in extras.split(",") if nome.strip()
    ]



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
    apontada: str | None = os.environ.get("ANALISADOR_UPLOAD_FOLDER")
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
DATABASE_URL: str | None = os.environ.get("DATABASE_URL")
_REGISTRO: RegistroDeAnalisesPostgres | None = RegistroDeAnalisesPostgres(DATABASE_URL) if DATABASE_URL else None

# A entrada pelo provedor (feature 051): montada UMA vez, do ambiente. Sem as cinco
# variaveis, `_AUTENTICACAO` e None e `_FALTANTES` diz o que falta — a suite e o
# harness de paridade importam este modulo sem credencial, e por isso a recusa
# fica na subida do servidor (`__main__`), e nao no import.
_AUTENTICACAO, _FALTANTES = servico_do_ambiente()


# --- Identidade local (feature 053) -------------------------------------------------
#
# As tres dependencias da feature entram como portas: `RepositorioDeContas`,
# `TransporteDeEmail` e `Relogio`. Montadas UMA vez, no mesmo ponto unico das
# outras, e injetaveis em `create_app` para a suite trocar as tres.
def _pasta_contas() -> str:
    """Caminho do arquivo de contas: `ANALISADOR_CONTAS` ou `src/dados/contas.json`.

    Fica FORA de `src/uploads/` de proposito: a tela de entrada varre aquela pasta
    e a conta apareceria como item da lista.
    """
    apontada: str | None = os.environ.get("ANALISADOR_CONTAS")
    if apontada:
        return apontada
    return os.path.join(
        os.path.dirname(os.path.abspath(__file__)), "dados", "contas.json"
    )


class _RelogioDoSistema:
    """O relogio de producao: agora, com fuso UTC."""

    def agora(self) -> datetime:
        return datetime.now(timezone.utc)


_RELOGIO = _RelogioDoSistema()
_CONTAS = ContasEmArquivo(_pasta_contas())
_EMAIL: EmailPorSmtp | TransporteNulo = transporte_do_ambiente()


def _requisicao_grande(_erro) -> tuple[str, Literal[413]]:
    return render_template(
        "index.html",
        message=f"Arquivo maior que o limite de {TETO_DE_UPLOAD_EM_MB} MB.",
        success=False,
    ), 413


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
    current_app.logger.warning(
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
def _sem_enquadramento_por_terceiro(resposta):
    resposta.headers["X-Frame-Options"] = "DENY"
    return resposta


def _arvore_do_formulario() -> tuple[str | None, object | None, str | None, int]:
    """Arvore pedida pelo formulario: devolve `(referencia, arvore, mensagem, status)`.

    O `status` existe desde a feature 051: referencia que nao resolve — inexistente
    ou de outro dono — responde **404** com o mesmo literal, para a recusa nao se
    distinguir de arquivo ausente (`RN-06`). O campo ausente continua sendo erro de
    entrada (`200` com a mensagem), porque nao e acesso a recurso nenhum.

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
    referencia: str | None = request.form.get("gedcom_filename")
    if not referencia:
        return None, None, "Erro: Arquivo GEDCOM não encontrado.", 200
    try:
        arvore = _estado_de_borda()["carregador"].carregar(referencia, _dono())
    except Exception:
        # O traceback vai para o LOG, e nao para a tela: o operador precisa de uma frase que
        # diga o que aconteceu, e quem depura precisa do rastro. Antes desta guarda os dois
        # ficavam sem nada — a tela mostrava o traceback e ninguem o registrava.
        current_app.logger.exception("GEDCOM alcancado pela referencia nao pode ser lido")
        return None, None, (
            f"Erro: o arquivo '{rotulo_de_referencia(referencia)}' não pôde ser lido como GEDCOM. "
            "Ele pode estar corrompido, vazio, ou não ser um GEDCOM de verdade."
        ), 200
    if arvore is None:
        # 404 tambem para o arquivo de OUTRO dono: a resposta tem de ser a mesma de
        # arquivo ausente (`RN-06`), e nunca 403 — 403 confirmaria que ele existe.
        return None, None, f"Erro: Arquivo '{rotulo_de_referencia(referencia)}' não existe mais.", 404
    return referencia, arvore, None, 200


# --- Rotas de assets e downloads (OPP-20261023-ASST) ---
# As quatro rotas moram em `web/rotas_assets.py` (Blueprint `assets_bp`). Os caminhos
# continuam sendo configurados aqui porque `app.config` e o ponto que os testes
# usam para simular arte ausente (`monkeypatch.setitem(app.config, ...)`), sem
# tocar nos arquivos do repositorio.
ARTE_DO_ICONE: str = os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "assets", "apple-touch-icon.png"
)

#: O favicon TRANSPARENTE das telas de identidade (emenda E005). Separado do icone
#: de atalho porque os dois alvos pedem coisas opostas: a tela inicial do celular
#: compoe transparencia sobre preto e precisa de fundo branco; a aba do navegador
#: mostra o fundo, e o quadrado branco aparecia como moldura.
ARTE_DO_FAVICON: str = os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "assets", "favicon.png"
)

ARTE_DO_TOPO: str = os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "assets", "banner-da-tela.png"
)

ESTILO_DA_TELA: str = os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "assets", "app.css"
)



def _listas_da_tela() -> dict[str, list[ItemDaLista]]:
    """As duas listas de arquivos armazenados, para as abas da tela de entrada.

    A selecao por extensao do nome visivel, o agrupamento pela chave e a ordem por data moram
    na funcao pura: aqui so se pergunta a ela duas vezes, uma por aba. As extensoes que
    decidem cada aba vem declaradas la, e nao escritas de novo neste arquivo — a particao tem
    um dono so.
    """
    entradas = _estado_de_borda()["armazenamento"].listar(_dono())
    return {
        "arvores_da_lista": itens_da_aba(entradas, ABA_DE_ARVORES),
        "relatorios_da_lista": itens_da_aba(entradas, ABA_DE_DNA),
    }


# --- Despachadores de Acoes da Tela Principal (OPP-20261023-DISP) ---


def _acao_upload_gedcom() -> str:
    """Processa o envio de um novo arquivo GEDCOM."""
    if "gedcom" not in request.files:
        return render_template("index.html", message="Nenhum arquivo GEDCOM enviado.", success=False)
    gedcom_file: FileStorage = request.files["gedcom"]
    if gedcom_file.filename == "":
        return render_template("index.html", message="Nenhum arquivo selecionado.", success=False)
    try:
        borda: dict[Any, Any] = _estado_de_borda()
        resultado: ResultadoDeUpload = caso_de_uso_de_upload(
            gedcom_file.read(),
            gedcom_file.filename,
            _dono(),
            borda["armazenamento"],
            borda["carregador"],
        )
        auditar(
            "enviar_gedcom",
            resultado.desfecho,
            referencia=resultado.referencia,
            contagens={"nomes": len(resultado.nomes)},
            ip=ip_do_cliente(),
            origem=origem_da_requisicao(),
        )
        return render_template(
            "index.html",
            gedcom_filename=resultado.referencia,
            all_names=resultado.nomes,
            message=resultado.mensagem,
            success=True,
        )
    except ErroDeDominio as erro_de_dominio:
        auditar(
            "enviar_gedcom",
            "falha",
            ip=ip_do_cliente(),
            origem=origem_da_requisicao(),
        )
        return render_template("index.html", message=traduzir(erro_de_dominio).mensagem, success=False)
    except HTTPException:
        raise
    except Exception:
        current_app.logger.exception("falha inesperada no envio de GEDCOM")
        auditar(
            "enviar_gedcom",
            "falha",
            ip=ip_do_cliente(),
            origem=origem_da_requisicao(),
        )
        return render_template(
            "index.html",
            message="Erro ao processar GEDCOM: O detalhe foi registrado no log.",
            success=False,
        )


def _acao_aposentar_arquivo() -> str | tuple[str, Literal[404]]:
    """Aposenta um arquivo da lista (RN-14).

    As DUAS tentativas sao auditadas — e o que a decisao 14 do `gaps.md` mandou fazer
    (`_reversa_sdd/questions.md#pergunta-14`) e o que a feature 049 executa. A mensagem de
    cada ramo continua sendo o contrato congelado da tela.
    """
    referencia: str = request.form.get("arquivo_a_aposentar") or ""
    moveu = _estado_de_borda()["armazenamento"].aposentar(referencia, _dono())
    auditar(
        "aposentar",
        "sucesso" if moveu else "falha",
        referencia=referencia,
        ip=ip_do_cliente(),
        origem=origem_da_requisicao(),
    )
    if moveu:
        return render_template(
            "index.html",
            message=(
                f"'{rotulo_de_referencia(referencia)}' saiu da lista. "
                "O arquivo não foi apagado: ele continua guardado, inteiro, "
                "na pasta de aposentados."
            ),
            success=True,
        )
    return render_template(
        "index.html",
        message="Não foi possível aposentar o arquivo: ele não está mais na pasta.",
        success=False,
    ), 404


def _acao_selecionar_arvore(gedcom_filename, arvore, all_names) -> str:
    """Renderiza a tela com o estado da arvore escolhida."""
    return render_template("index.html", gedcom_filename=gedcom_filename, all_names=all_names)


def _acao_dna_analysis(gedcom_filename, arvore, all_names) -> str | tuple[str, Literal[404]]:
    """Processa o confronto de matches de DNA com a arvore genealogica."""
    try:
        borda: dict[Any, Any] = _estado_de_borda()
        nome_informado: str = request.form["root_name"]
        root_name: str = nome_informado.strip() or nome_informado

        referencia_do_csv: str | None = request.form.get("matches_csv_filename")
        # `str` desde o inicio, e nao `None`: o valor vai para o campo oculto do cartao
        # e para a auditoria. O `or ""` cobre o formulario sem o campo e impede que a
        # inferencia do checador fique presa em `str | None` para a atribuicao seguinte.
        referencia_do_csv_usada: str = referencia_do_csv or ""
        candidatos_fixos: dict[str, tuple[str, str]] = {}
        for valor in request.form.getlist("promover"):
            partes: list[str] = valor.split("|", 2)
            if len(partes) == 3:
                candidatos_fixos[partes[0]] = (partes[1], partes[2])
        # `""` significa "sem aviso". O tipo e `str` do inicio ao fim, e o `if` abaixo
        # continua distinguindo os dois casos sem depender de `None`.
        aviso_de_substituicao: str = ""
        if referencia_do_csv:
            caminho_do_csv = borda["armazenamento"].resolver(referencia_do_csv, _dono())
            if caminho_do_csv is None:
                return render_template(
                    "index.html",
                    gedcom_filename=gedcom_filename,
                    all_names=all_names,
                    message=f"Erro: Arquivo '{rotulo_de_referencia(referencia_do_csv)}' não existe mais.",
                    success=False,
                ), 404
        else:
            if "matches_csv" not in request.files or not request.files["matches_csv"].filename:
                return render_template(
                    "index.html",
                    gedcom_filename=gedcom_filename,
                    all_names=all_names,
                    message="Por favor, carregue o arquivo CSV de matches.",
                    success=False,
                )
            matches_file: FileStorage = request.files["matches_csv"]

            armazenado: ResultadoDeArmazenamento = guardar_com_substituicao(
                borda["armazenamento"],
                matches_file.read(),
                matches_file.filename,
                "csv",
                _dono(),
            )
            caminho_do_csv: str | None = armazenado.caminho
            if caminho_do_csv is None:
                return render_template(
                    "index.html",
                    gedcom_filename=gedcom_filename,
                    all_names=all_names,
                    message=armazenado.motivo or "",
                    success=False,
                )
            if caminho_do_csv:
                referencia_do_csv_usada = os.path.basename(caminho_do_csv)
            if armazenado.desfecho == SUBSTITUIDO:
                auditar(
                    "substituir_csv",
                    "substituido",
                    referencia=referencia_do_csv_usada,
                    ip=ip_do_cliente(),
                    origem=origem_da_requisicao(),
                )
                aviso_de_substituicao = (
                    f"O CSV '{armazenado.visivel}' substituiu a versão anterior, que "
                    "saiu da lista e continua guardada na pasta de aposentados."
                )

        resultado: ResultadoDeAnalise = caso_de_uso_dna(
            caminho_do_csv,
            root_name,
            arvore,
            borda["dependencias"],
            _dono(),
            gedcom_filename,
            borda["registro"],
            candidatos_fixos=candidatos_fixos or None,
        )
        mensagem_final: str = resultado.mensagem
        if aviso_de_substituicao:
            mensagem_final = f"{mensagem_final} {aviso_de_substituicao}"
        # Contagens, nunca nomes: o que a auditoria precisa saber e o TAMANHO do resultado
        # (`RF-07`), e a lista de matches e a de descartados carregam nome de pessoa.
        auditar(
            "analisar_dna",
            "sucesso",
            referencia=gedcom_filename,
            contagens={
                "resultados": len(resultado.resultados),
                "descartados": len(resultado.descartados),
                "sem_correspondencia": len(resultado.sem_correspondencia),
            },
            ip=ip_do_cliente(),
            origem=origem_da_requisicao(),
        )
        return render_template(
            "index.html",
            gedcom_filename=gedcom_filename,
            all_names=all_names,
            dna_results=resultado.resultados,
            skipped_matches=resultado.descartados,
            sem_correspondencia=resultado.sem_correspondencia,
            observacoes_do_arquivo=resultado.observacoes_do_arquivo,
            cobertura=resultado.cobertura,
            message=mensagem_final,
            aviso_de_persistencia=resultado.aviso_de_persistencia,
            root_name_usado=root_name,
            csv_filename_usado=referencia_do_csv_usada,
            success=True,
        )
    except ErroDeDominio as erro_de_dominio:
        auditar(
            "analisar_dna",
            "falha",
            referencia=gedcom_filename,
            ip=ip_do_cliente(),
            origem=origem_da_requisicao(),
        )
        return render_template(
            "index.html",
            gedcom_filename=gedcom_filename,
            all_names=all_names,
            message=traduzir(erro_de_dominio).mensagem,
            success=False,
        )
    except HTTPException:
        raise
    except Exception:
        current_app.logger.exception("falha inesperada na analise de DNA")
        auditar(
            "analisar_dna",
            "falha",
            referencia=gedcom_filename,
            ip=ip_do_cliente(),
            origem=origem_da_requisicao(),
        )
        return render_template(
            "index.html",
            gedcom_filename=gedcom_filename,
            all_names=all_names,
            message="Ocorreu um erro: O detalhe foi registrado no log.",
            success=False,
        )


def _contagens_do_caminho(dados) -> dict:
    """Numeros do resultado da busca, para a auditoria (`RF-07`).

    O payload carrega `person1_name` e `person2_name` — nome de pessoa. A auditoria le
    **apenas** o bloco documental e os numeros dele: quantos saltos pai-filho e quantos
    homonimos exatos entraram na decisao. Nenhuma string do payload atravessa.
    """
    if not dados:
        return {}
    documental: dict[Any, Any] | Any = dados.get("documentary") or {}
    homonimos: dict[Any, Any] | Any = documental.get("homonyms") or {}
    return {
        "meioses": documental.get("meioses") or 0,
        "homonimos": homonimos.get("exact_count") or 0,
    }


def _acao_path_search(gedcom_filename, arvore, all_names) -> str:
    """Processa a busca de parentesco entre duas pessoas."""
    try:
        person1_name: str = request.form["person1_name"].strip()
        person2_name: str = request.form["person2_name"].strip()

        resultado: ResultadoDeBusca = caso_de_uso_de_busca(
            person1_name,
            person2_name,
            arvore,
            _estado_de_borda()["dependencias"],
            _dono(),
        )
        auditar(
            "buscar_caminho",
            resultado.desfecho.value,
            referencia=gedcom_filename,
            contagens=_contagens_do_caminho(resultado.dados),
            ip=ip_do_cliente(),
            origem=origem_da_requisicao(),
        )

        if resultado.desfecho is Desfecho.ERRO_DE_ENTRADA:
            return render_template(
                "index.html",
                gedcom_filename=gedcom_filename,
                all_names=all_names,
                message=resultado.mensagem,
                success=False,
            )
        return render_template(
            "index.html",
            gedcom_filename=gedcom_filename,
            all_names=all_names,
            path_result=resultado.dados,
            message=resultado.mensagem,
            success=True,
        )
    except ErroDeDominio as erro_de_dominio:
        auditar(
            "buscar_caminho",
            "falha",
            referencia=gedcom_filename,
            ip=ip_do_cliente(),
            origem=origem_da_requisicao(),
        )
        return render_template(
            "index.html",
            gedcom_filename=gedcom_filename,
            all_names=all_names,
            message=traduzir(erro_de_dominio).mensagem,
            success=False,
        )
    except HTTPException:
        raise
    except Exception:
        current_app.logger.exception("falha inesperada na busca de caminho")
        auditar(
            "buscar_caminho",
            "falha",
            referencia=gedcom_filename,
            ip=ip_do_cliente(),
            origem=origem_da_requisicao(),
        )
        return render_template(
            "index.html",
            gedcom_filename=gedcom_filename,
            all_names=all_names,
            message="Ocorreu um erro: O detalhe foi registrado no log.",
            success=False,
        )


_ACOES_PRE_ARVORE = {
    "upload_gedcom": _acao_upload_gedcom,
    "aposentar_arquivo": _acao_aposentar_arquivo,
}

_ACOES_COM_ARVORE = {
    "selecionar_arvore": _acao_selecionar_arvore,
    "dna_analysis": _acao_dna_analysis,
    "path_search": _acao_path_search,
}


# --- Rota Principal ---
def index() -> str | tuple[str, Literal[404]] | tuple[str, int]:
    if request.method == "POST":
        action: str = request.form.get("action") or ""
        handler_pre = _ACOES_PRE_ARVORE.get(action)
        if handler_pre:
            return handler_pre()

        gedcom_filename, arvore, erro, status = _arvore_do_formulario()
        if erro is not None or arvore is None:
            return render_template("index.html", message=erro or "Erro: Arquivo GEDCOM não encontrado.", success=False), status
        all_names: list[str] = nomes_de_exibicao(arvore)

        handler_arvore = _ACOES_COM_ARVORE.get(action)
        if handler_arvore:
            return handler_arvore(gedcom_filename, arvore, all_names)

    return render_template("index.html")


class _SemAutenticacao:
    """Sentinela tipado do parametro `autenticacao` do `create_app`.

    `object()` cru perdia o tipo na dobra: o checador via `object` no lugar de
    `ServicoDeEntrada | None` e acusava atributo inexistente em `efetiva.configuracao`.
    A classe existe para o `isinstance` estreitar o tipo.
    """


_SEM_INJECAO = object()
_SEM_AUTENTICACAO = _SemAutenticacao()
CHAVE_DA_BORDA = "analisador"


def _estado_de_borda() -> dict:
    """O estado de borda da instancia que esta atendendo a requisicao."""
    return current_app.extensions[CHAVE_DA_BORDA]


def _configurar_entrada(aplicacao, configuracao) -> None:
    """Liga o segredo e o cookie da sessao. Sem entrada, nada disto e tocado.

    O segredo vem do ambiente e nunca do repositorio (`RN-08`): a `P-04` removeu o
    literal versionado, e ele nao volta por esta porta. O `Secure` acompanha o
    esquema da URL publica — no uso local em `http://` ele fica desligado.
    """
    aplicacao.secret_key = configuracao.segredo
    aplicacao.config.update(
        SESSION_COOKIE_NAME="analisador_sessao",
        SESSION_COOKIE_HTTPONLY=True,
        SESSION_COOKIE_SAMESITE="Lax",
        SESSION_COOKIE_SECURE=configuracao.usa_https,
        PERMANENT_SESSION_LIFETIME=timedelta(hours=12),
        SESSION_REFRESH_EACH_REQUEST=True,
    )


def _conta_tem_senha() -> dict:
    """Diz ao template se a conta da sessao ja tem credencial local (`RF-24`)."""
    conta: Any | None = getattr(g, "conta", None)
    if conta is None:
        return {"conta_tem_senha": False}
    try:
        registro = current_app.extensions[CHAVE_DA_BORDA]["contas"].por_sub(conta.sub)
    except Exception:
        return {"conta_tem_senha": False}
    return {"conta_tem_senha": bool(registro is not None and registro.tem_senha)}


def _montar_identidade(aplicacao, entrada) -> None:
    """Monta os servicos da identidade local sobre as tres portas injetadas.

    So roda com a entrada ligada: sem sessao, cadastro e senha nao tem onde
    guardar a conta, e as rotas nem sao registradas (mesma postura da 051).
    """
    borda = aplicacao.extensions[CHAVE_DA_BORDA]
    contas = borda["contas"]
    email = borda["email"]
    relogio = borda["relogio"]
    limite = Limitador(relogio)
    url_publica = entrada.configuracao.url_publica

    borda["limitador"] = limite
    borda["cadastro"] = ServicoDeCadastro(
        contas, email, relogio, limite, url_publica=url_publica
    )
    borda["entrada_local"] = ServicoDeEntradaLocal(contas, relogio, limite)
    borda["recuperacao"] = ServicoDeRecuperacao(
        contas, email, relogio, limite, url_publica=url_publica
    )
    borda["definir_senha"] = ServicoDeDefinirSenha(contas, relogio)
    borda["vinculo"] = VinculoDeIdentidade(contas, relogio)
    borda["verificador_de_versao"] = VerificadorDeVersao(contas)

    aplicacao.context_processor(_conta_tem_senha)

    @aplicacao.after_request
    def _sem_cache_de_identidade(resposta):
        """Toda pagina de identidade e `no-store`, com ou sem sessao.

        O `no-store` da guarda so alcanca resposta autenticada; a tela de entrada,
        o cadastro e a recuperacao sao anonimas e tambem nao podem ser cacheadas.
        """
        ponto: str = request.endpoint or ""
        if ponto.startswith("conta.") or ponto in ("auth.login", "auth.callback"):
            resposta.headers["Cache-Control"] = "no-store"
        return resposta

    if not getattr(email, "configurado", False):
        aplicacao.logger.warning(
            "Envio de e-mail nao configurado: o cadastro e a recuperacao vao avisar "
            "que o envio esta indisponivel. Defina ANALISADOR_SMTP_HOST e "
            "ANALISADOR_SMTP_REMETENTE para habilitar."
        )


def create_app(config=None, *, armazenamento=None, carregador=None,
               registro=_SEM_INJECAO, dependencias=None,
               autenticacao: ServicoDeEntrada | None | _SemAutenticacao = _SEM_AUTENTICACAO,
               contas=_SEM_INJECAO, email=_SEM_INJECAO, relogio=None) -> Flask:
    """Monta a aplicacao: configura, registra ganchos, Blueprint e rota.

    A instancia de modulo `app` e criada por esta funcao uma vez, no fim do
    arquivo. Chamar de novo devolve uma instancia independente de configuracao e
    de estado de borda: `armazenamento`, `carregador`, `registro` e `dependencias`
    podem ser injetados, e os handlers leem de `current_app.extensions`.

    Sem injecao, os quatro objetos do modulo entram como padrao, e o app de modulo
    se comporta exatamente como antes. `registro` usa sentinela porque `None` e um
    valor valido: significa persistencia desligada.
    """
    aplicacao = Flask(__name__)
    # O modo de identidade e DECLARADO, e nao inferido do ambiente (auditoria de
    # 2026-10-30, P1/P3). A recusa mora AQUI, e nao no `__main__`, porque enquanto ela
    # morava la qualquer runner que chamasse a fabrica — `waitress-serve`, um servico do
    # Windows, um `.bat` com `flask run` — subia a aplicacao ABERTA, com `_dono()` caindo
    # no literal `"unico"`. Agora quem nao declara nao sobe.
    modo: str | None = ler_modo()
    if modo == GOOGLE and isinstance(autenticacao, _SemAutenticacao) and _FALTANTES:
        raise RecusaDeSubida(
            "a entrada com o provedor exige configuracao que falta: "
            + "; ".join(_FALTANTES)
            + ". Defina as variaveis e tente de novo (ver onboarding.md)."
        )
    # Injecao explicita vence o modo: quem chama `create_app(autenticacao=...)` sabe o
    # que quer, e e assim que a suite monta a entrada com provedor falso sem tocar no
    # ambiente do processo.
    efetiva: ServicoDeEntrada | None = (
        (_AUTENTICACAO if modo == GOOGLE else None)
        if isinstance(autenticacao, _SemAutenticacao)
        else autenticacao
    )
    # Os tres destinos do registro sao montados UMA vez por processo (feature 049, `D-01`).
    # A chamada e idempotente por marcador no handler: a suite reexecuta este modulo a cada
    # fixture, e um booleano de modulo nao sobreviveria a isso — o registro de handlers do
    # `logging` e global.
    logs.configurar()
    aplicacao.extensions[CHAVE_DA_BORDA] = {
        "armazenamento": _ARMAZENAMENTO if armazenamento is None else armazenamento,
        "carregador": _CARREGADOR if carregador is None else carregador,
        "registro": _REGISTRO if registro is _SEM_INJECAO else registro,
        "dependencias": _DEPENDENCIAS if dependencias is None else dependencias,
        "autenticacao": efetiva,
        "pasta_de_uploads": _pasta_uploads(),
        "contas": _CONTAS if contas is _SEM_INJECAO else contas,
        "email": _EMAIL if email is _SEM_INJECAO else email,
        "relogio": _RELOGIO if relogio is None else relogio,
    }

    # A busca (feature 052, `D-01`/`D-02`): as duas fontes nascem AQUI, com as mesmas
    # dependencias ja injetadas na borda, e o caso de uso e montado uma vez por aplicacao.
    # A rota so le; ela nao constroi fonte nem decide casamento.
    _borda = aplicacao.extensions[CHAVE_DA_BORDA]
    aplicacao.extensions["busca"] = ServicoDeBusca((
        NomesDaArvoreGedcom(_borda["carregador"]),
        NomesDoArquivoDeMatches(_borda["armazenamento"]),
    ))
    # O literal do dono sem autenticacao vive numa constante deste modulo; a rota le daqui
    # para nao repetir o valor nem importar este arquivo (que a importaria de volta).
    aplicacao.config["DONO_LEGADO"] = DONO_DO_PROCESSO
    # O modo em uso, para o log de subida e para o teste. `None` e o escape de teste —
    # o unico valor que nao corresponde a um modo de producao.
    aplicacao.config["MODO_DE_IDENTIDADE"] = modo
    aplicacao.config["MAX_CONTENT_LENGTH"] = TETO_DE_UPLOAD_EM_BYTES

    # Em `config`, e nao lida dentro do tratador, para o teste poder trocar a lista sem mexer no
    # ambiente — o mesmo padrao das chaves de arte e da folha.
    aplicacao.config["TRUSTED_HOSTS"] = _hosts_permitidos()

    # Formato dos numeros que o operador le (BUG-20261004-EWSJ). O template pede o
    # filtro; a regra mora em `utils/number_format.py`, que e a autoridade unica.
    aplicacao.add_template_filter(formatar_cm, "cm_br")
    aplicacao.add_template_filter(formatar_inteiro, "inteiro_br")
    # O tamanho dos arquivos da lista, na unidade que se le de relance: `8,54 MB`, `55 KB`.
    # Nasceu em 2026-10-16, a pedido do operador: a coluna "Tamanho" das DUAS abas mostrava o total em
    # bytes, e `8.955.472 bytes` nao se le de relance. O numero exato continua no `title` da celula —
    # ver o comentario no macro.
    aplicacao.add_template_filter(formatar_tamanho, "tamanho_br")
    # A data da coluna "Enviado em". A conversao e a MESMA autoridade unica usada pela lista, em
    # `reporting/lista_de_arquivos.py`, e nao um `strftime` solto no template: data que o sistema
    # nao converte tem de virar celula vazia em um lugar so.
    aplicacao.add_template_filter(formatar_data_br, "data_br")
    # O nome VISIVEL da arvore aberta, a partir do `gedcom_filename` que a rota ja passa em todas
    # as renderizacoes. E filtro, e nao parametro de contexto, de proposito: a rota tem oito
    # `render_template` com `gedcom_filename`, e acrescentar um argumento em cada um seria oito
    # lugares para esquecer um — o mesmo defeito que o processador de contexto resolveu para as
    # listas. O filtro reusa `rotulo_de_referencia`, que ja existia para as mensagens, entao o nome
    # sai SEM a chave de conteudo pelo mesmo caminho de sempre.
    aplicacao.add_template_filter(rotulo_de_referencia, "rotulo_do_arquivo")

    aplicacao.config["ARTE_DO_ICONE"] = ARTE_DO_ICONE
    aplicacao.config["ARTE_DO_FAVICON"] = ARTE_DO_FAVICON
    aplicacao.config["ARTE_DO_TOPO"] = ARTE_DO_TOPO
    aplicacao.config["ESTILO_DA_TELA"] = ESTILO_DA_TELA

    aplicacao.register_error_handler(RequestEntityTooLarge, _requisicao_grande)
    aplicacao.register_error_handler(SecurityError, _host_recusado)
    aplicacao.after_request(_sem_enquadramento_por_terceiro)
    aplicacao.context_processor(_listas_da_tela)

    aplicacao.register_blueprint(assets_bp)
    aplicacao.register_blueprint(busca_bp)
    aplicacao.add_url_rule("/", endpoint="index", view_func=index, methods=["GET", "POST"])

    # Identificador por requisicao, cabecalho `X-Request-ID` e linha de acesso (feature 049).
    # Sao ganchos, e nao codigo da rota, porque o cabecalho precisa sair tambem nas respostas
    # que o Flask produz sem passar pela rota: arte ausente, corpo grande e `Host` recusado.
    instalar_registro(aplicacao)

    # A entrada (feature 051) so existe quando foi montada. Sem ela, nada de guarda,
    # de Blueprint nem de cookie: o caminho e o legado, que e o da suite e o da paridade.
    if efetiva is not None:
        _configurar_entrada(aplicacao, efetiva.configuracao)
        _montar_identidade(aplicacao, efetiva)
        aplicacao.register_blueprint(auth_bp)
        aplicacao.register_blueprint(conta_bp)
        instalar_guarda(
            aplicacao,
            aplicacao.extensions[CHAVE_DA_BORDA]["verificador_de_versao"],
        )

    if config:
        aplicacao.config.update(config)
    return aplicacao


try:
    app = create_app()
except RecusaDeSubida as erro:
    # `SystemExit` e nao traceback: quem le esta mensagem e o operador — e, no
    # instalador, o testador. O `from None` apaga a causa, que so repetiria a frase.
    raise SystemExit(f"Recusando subir: {erro}") from None

if __name__ == "__main__":
    # Configuracao de execucao lida do ambiente, com os padroes declarados aqui.
    # Mesmo padrao ja praticado pelo projeto em `ANALISADOR_UPLOAD_FOLDER`.
    #
    # O padrao do endereco e a maquina local (RF-02). A aplicacao nao tem
    # autenticacao alguma, entao atender a rede passa a ser ato explicito de quem
    # opera, e nao o comportamento que acontece por omissao.
    endereco_de_escuta: str = os.environ.get("ANALISADOR_HOST", "127.0.0.1")
    porta_de_escuta = int(os.environ.get("ANALISADOR_PORT", "5000"))
    concorrencia = int(os.environ.get("ANALISADOR_THREADS", "4"))

    # A recusa por credencial ausente NAO mora mais aqui (auditoria de 2026-10-30). Ela
    # morava so neste bloco, e por isso qualquer runner que nao fosse `python src/app.py`
    # subia o app aberto. Agora ela esta em `create_app`, pelo `ANALISADOR_MODO`.
    #
    # O que fica aqui e dizer QUAL modo esta no ar — e avisar quando nao ha modo nenhum,
    # o que so acontece com o escape de teste ligado.
    modo_em_uso = app.config.get("MODO_DE_IDENTIDADE")
    if modo_em_uso is None:
        logging.getLogger(__name__).warning(
            "MODO DE TESTE: a aplicacao esta sem identidade e sem guarda. "
            "Defina ANALISADOR_MODO para subir em modo de producao."
        )
    else:
        logging.getLogger(__name__).info("modo de identidade: %s", modo_em_uso)

    # O import fica aqui dentro de proposito. Este modulo e importado pela suite de
    # testes e pela instrumentacao de paridade, e um import no topo obrigaria o
    # servidor de producao instalado em quem so quer a aplicacao como objeto.
    try:
        # `waitress` nao publica stubs; o import e tardio e guardado por `except ImportError`.
        from waitress import serve  # pyrefly: ignore[untyped-import]
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
            motivo: str = f"nao foi possivel escutar em {endereco_de_escuta}:{porta_de_escuta}"
            saida = (
                "Confira se ANALISADOR_HOST aponta para um endereco desta maquina e "
                "se ANALISADOR_PORT e uma porta valida."
            )
        # A mensagem nao afirma quem ocupa a porta: pode ser uma instancia anterior
        # desta aplicacao ou qualquer outro processo.
        raise SystemExit(f"Recusando subir: {motivo} ({erro.strerror or erro}). {saida}")

    # A linha de inicializacao deixou de ser `print` (feature 049): o texto e o MESMO, e o
    # que muda e o destino. Ela continua sendo a unica prova do endereco e do numero de
    # threads em uso, agora tambem no arquivo de log — que e o que permite responder depois
    # "com quantas threads isso rodou?".
    logging.getLogger(__name__).info(
        "Servindo com waitress em http://%s:%s com %s threads",
        endereco_de_escuta,
        porta_de_escuta,
        concorrencia,
    )
    # `sockets` e mutuamente exclusivo de `host` e `port`: o servidor levanta
    # ValueError se receber `sockets` junto de qualquer um dos dois. Endereco e
    # porta ja estao no socket ligado.
    serve(app, sockets=[socket_de_escuta], threads=concorrencia,
          max_request_body_size=TETO_DE_UPLOAD_EM_BYTES + MARGEM_DO_MULTIPART)

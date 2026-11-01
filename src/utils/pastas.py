"""Onde ficam os dados do usuario: uma raiz, e as tres pastas abaixo dela.

Ate a auditoria de 2026-10-30 (`P4`), uploads, logs e contas moravam DENTRO da pasta do
programa - `src/uploads`, `logs/` e `src/dados/contas.json`. Isso funciona enquanto o
pacote e extraido num diretorio comum do usuario, e **nao** funciona no que o instalador
vai fazer: `C:\\Program Files` nao e gravavel por usuario comum, e o `os.makedirs` do
import derrubava o processo com `PermissionError` e traceback, antes de a tela existir.

A raiz passa a ser a pasta de dados do USUARIO:

    Windows   %LOCALAPPDATA%\\Analisador Genealogico
    outros    $XDG_DATA_HOME/Analisador Genealogico ou ~/.local/share/Analisador Genealogico

`ANALISADOR_DADOS` sobrepoe a raiz inteira. As tres variaveis antigas
(`ANALISADOR_UPLOAD_FOLDER`, `ANALISADOR_LOG_DIR`, `ANALISADOR_CONTAS`) continuam
valendo e vencem a raiz: a suite, o involucro de paridade e o container dependem delas,
e uma variavel especifica e mais explicita do que a raiz para quem so quer desviar uma
pasta.

Nada e movido da pasta antiga. Quando ha dados la, `restos_da_versao_antiga()` diz quais
sao, e a decisao de copiar continua sendo do operador - mover dado do usuario por
iniciativa do programa e o tipo de conveniencia que ninguem pediu.
"""
from __future__ import annotations

import os
from collections.abc import Mapping

# --- Variaveis de ambiente -------------------------------------------------

# A raiz unica. As tres abaixo sao as sobreposicoes por pasta, e continuam existindo
# porque sao o que a suite, o involucro de paridade e o compose ja usam.
VARIAVEL_DA_RAIZ = "ANALISADOR_DADOS"
VARIAVEL_DOS_UPLOADS = "ANALISADOR_UPLOAD_FOLDER"
VARIAVEL_DOS_LOGS = "ANALISADOR_LOG_DIR"
VARIAVEL_DAS_CONTAS = "ANALISADOR_CONTAS"

# --- Nomes no disco --------------------------------------------------------

# Sem acento de proposito: o nome aparece em `.bat`, em caminho de log e na resposta de
# erro, e os tres circulos do Windows (console, Notepad, codepage) sao mais fieis em ASCII.
NOME_DA_PASTA = "Analisador Genealogico"
SUPASTA_DE_UPLOADS = "uploads"
SUPASTA_DE_LOGS = "logs"
ARQUIVO_DE_CONTAS = "contas.json"

# Onde a versao anterior gravava, relativo ao diretorio do `app.py`. Existe so para o
# aviso de `restos_da_versao_antiga()`; nada no fluxo normal passa por aqui.
SUPASTA_ANTIGA_DE_CONTAS = "dados"


class PastaDeDadosInacessivel(RuntimeError):
    """A pasta de dados do usuario nao pode ser criada.

    Nao e erro de programacao: e condicao de maquina, e quem le a mensagem e o operador.
    Quem chama (`create_app`) converte isto em recusa de subida, com o nome `RecusaDeSubida`
    - a fronteira web fica com a decisao de recusar, e este modulo fica sem importar Flask.
    """


# --- A raiz ----------------------------------------------------------------


def raiz_de_dados(ambiente: Mapping[str, str] | None = None) -> str:
    """A pasta de dados do usuario: `ANALISADOR_DADOS` ou o padrao da plataforma.

    Le do `ambiente` recebido, e nao de `os.environ` direto, para o teste poder medir a
    resolucao sem mexer no processo - o mesmo desenho de `web/modo.py`.
    """
    valores: Mapping[str, str] = os.environ if ambiente is None else ambiente
    apontada: str | None = valores.get(VARIAVEL_DA_RAIZ)
    if apontada:
        return apontada
    # Windows: e o diretorio que o usuario comum pode escrever, e o que sobrevive a
    # desinstalar o programa.
    local: str | None = valores.get("LOCALAPPDATA")
    if local:
        return os.path.join(local, NOME_DA_PASTA)
    # Fora do Windows (CI, desenvolvimento no Linux, container sem a variavel): o padrao
    # XDG, que e o equivalente funcional.
    xdg: str | None = valores.get("XDG_DATA_HOME")
    if xdg:
        return os.path.join(xdg, NOME_DA_PASTA)
    return os.path.join(os.path.expanduser("~"), ".local", "share", NOME_DA_PASTA)


# --- As tres pastas --------------------------------------------------------


def pasta_de_uploads(ambiente: Mapping[str, str] | None = None) -> str:
    """`ANALISADOR_UPLOAD_FOLDER` ou `<raiz>/uploads`."""
    valores: Mapping[str, str] = os.environ if ambiente is None else ambiente
    apontada: str | None = valores.get(VARIAVEL_DOS_UPLOADS)
    if apontada:
        return apontada
    return os.path.join(raiz_de_dados(valores), SUPASTA_DE_UPLOADS)


def pasta_de_logs(ambiente: Mapping[str, str] | None = None) -> str:
    """`ANALISADOR_LOG_DIR` ou `<raiz>/logs`."""
    valores: Mapping[str, str] = os.environ if ambiente is None else ambiente
    apontada: str | None = valores.get(VARIAVEL_DOS_LOGS)
    if apontada:
        return apontada
    return os.path.join(raiz_de_dados(valores), SUPASTA_DE_LOGS)


def arquivo_de_contas(ambiente: Mapping[str, str] | None = None) -> str:
    """`ANALISADOR_CONTAS` ou `<raiz>/contas.json`.

    Fora da pasta de uploads de proposito: a tela de entrada varre aquela pasta e a conta
    apareceria como item da lista.
    """
    valores: Mapping[str, str] = os.environ if ambiente is None else ambiente
    apontada: str | None = valores.get(VARIAVEL_DAS_CONTAS)
    if apontada:
        return apontada
    return os.path.join(raiz_de_dados(valores), ARQUIVO_DE_CONTAS)


# --- Preparo e diagnostico -------------------------------------------------


def preparar(pasta: str) -> None:
    """Cria a pasta de dados, ou levanta `PastaDeDadosInacessivel` com o que fazer.

    Antes, o `os.makedirs` rodava no import: um `Program Files` sem escrita virava
    `PermissionError` e traceback, sem contrato e depois de o processo ja ter comecado. A
    mensagem nomeia a variavel que resolve o problema porque essa e a acao do operador.
    """
    try:
        os.makedirs(pasta, exist_ok=True)
    except OSError as erro:
        raise PastaDeDadosInacessivel(
            f"nao consegui preparar a pasta de dados {pasta!r}: "
            f"{erro.strerror or erro}. Defina {VARIAVEL_DA_RAIZ} para uma pasta "
            "gravavel (por exemplo, dentro da sua pasta de usuario) e tente de novo."
        ) from None


def _tem_conteudo(pasta: str) -> bool:
    """Se a pasta existe e tem pelo menos uma entrada. Pasta ilegivel conta como vazia."""
    try:
        return bool(os.listdir(pasta))
    except OSError:
        return False


def _pasta_do_app() -> str:
    """O diretorio do `app.py`, derivado deste arquivo (`src/utils/pastas.py`)."""
    return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def restos_da_versao_antiga(
    ambiente: Mapping[str, str] | None = None, pasta_do_app: str | None = None
) -> tuple[str | None, str | None]:
    """Dados da versao anterior que continuam na pasta do programa.

    Devolve `(pasta de uploads, arquivo de contas)`, com `None` no que nao vale avisar. O
    aviso so faz sentido quando o operador NAO escolheu caminho: com `ANALISADOR_DADOS` (ou
    a variavel da pasta) definida, o destino e escolha dele, e a pasta do programa e so
    historia - avisar ali seria ruido em todo teste e em toda subida de container.

    A pasta nova precisa estar vazia para o aviso valer: se ja ha arquivos no destino, o
    operador obviamente ja sabe onde eles ficam.
    """
    valores: Mapping[str, str] = os.environ if ambiente is None else ambiente
    if (
        valores.get(VARIAVEL_DA_RAIZ)
        or valores.get(VARIAVEL_DOS_UPLOADS)
        or valores.get(VARIAVEL_DAS_CONTAS)
    ):
        return None, None

    app: str = pasta_do_app or _pasta_do_app()

    antiga: str = os.path.join(app, SUPASTA_DE_UPLOADS)
    uploads: str | None = None
    if _tem_conteudo(antiga) and not _tem_conteudo(pasta_de_uploads(valores)):
        uploads = antiga

    antigas: str = os.path.join(app, SUPASTA_ANTIGA_DE_CONTAS, ARQUIVO_DE_CONTAS)
    contas: str | None = None
    if os.path.isfile(antigas) and not os.path.exists(arquivo_de_contas(valores)):
        contas = antigas

    return uploads, contas

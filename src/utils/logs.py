"""Configuracao central de registro, contexto de requisicao e medicao (feature 049).

## Os tres destinos, e por que sao tres

- **console** - operacao. Quem esta olhando a tela ve o que aconteceu agora.
- **arquivo geral** (`analisador.log`, rotativo em 5 x 5 MB) - diagnostico. O que passou
  nao se le de novo no console.
- **trilha de auditoria** (`analisador.auditoria.AAAA-MM-DD.log`, um arquivo por dia, sem
  descarte) - prova. E o unico destino que responde "quando este arquivo saiu da lista?".
  Ele **nao propaga** para os outros dois (`RN-01`): uma acao auditada nao vira eco no
  arquivo geral.

O prazo de 90 dias da trilha e **declarado**, e o expurgo e do operador (`RN-10`): por isso
a auditoria **nao** rotaciona por tamanho. Rotacionar apagaria dado antes do prazo, que e
expurgo automatico disfarcado - o oposto do que foi decidido.

## Idempotencia: marcador no handler, nao flag de modulo

`configurar()` pode ser chamada muitas vezes no mesmo processo. Um booleano de modulo
**nao serve**: a suite reexecuta `src/app.py` com `exec_module`
(`tests/conftest.py`), o que cria um namespace de modulo novo a cada vez - enquanto o
registro de handlers do `logging` e global do processo. A guarda e um marcador no proprio
handler ja instalado, e e por isso que `_nossos_handlers()` existe.

## A pasta

Ancorada na **raiz do projeto** (o pai de `src/`), e nao no diretorio corrente: e o caminho
que o `.gitignore` cobre e o mesmo que o volume `./logs:/app/logs` publica. Fora de
container, `ANALISADOR_LOG_DIR` aponta para outro lugar - o mesmo padrao de
`ANALISADOR_UPLOAD_FOLDER`.
"""
from __future__ import annotations

import contextlib
import contextvars
import logging
import logging.handlers
import os
import re
import sys
import time
import uuid

# --- Variaveis de ambiente -------------------------------------------------

VARIAVEL_DO_NIVEL = "ANALISADOR_LOG_LEVEL"
VARIAVEL_DA_PASTA = "ANALISADOR_LOG_DIR"

# `INFO` e o padrao: `DEBUG` foi descartado como padrao porque o parse real e barulhento e
# o operador nao pediu volume. O ajuste por modulo existe para nao obrigar a subir o
# sistema inteiro so para ver um parser (`RN-02`).
NIVEL_PADRAO = "INFO"

# --- Nomes dos arquivos ----------------------------------------------------

PASTA_PADRAO = "logs"
ARQUIVO_GERAL = "analisador.log"
PREFIXO_DA_AUDITORIA = "analisador.auditoria"

# --- Rotacao do log geral --------------------------------------------------

TAMANHO_MAXIMO_EM_BYTES = 5 * 1024 * 1024
ARQUIVOS_DE_ROTACAO = 5

# --- Formatos --------------------------------------------------------------

# `%(id)s` e injetado por `FiltroDeContexto` em TODA linha, dos tres destinos.
# A auditoria tambem o carrega: e o que liga a acao ao acesso que a pediu.
FORMATO = "%(asctime)s %(levelname)s [%(id)s] %(name)s: %(message)s"
FORMATO_DE_DATA = "%Y-%m-%d %H:%M:%S"

LOGGER_DE_AUDITORIA = "auditoria"
LOGGER_DE_ACESSO = "acesso"
LOGGER_DE_MEDICAO = "medicao"

# Nivel do servidor de producao. A linha de acesso dele e substituida pela nossa (que
# carrega o identificador) e por isso sobe para WARNING; os erros dele continuam visiveis.
LOGGER_DO_SERVIDOR = "waitress"
NIVEL_DO_SERVIDOR = logging.WARNING

_MARCA = "_do_analisador_049"

# --- Identificador de requisicao ------------------------------------------

# `ContextVar`, e nao `flask.g` nem `threading.local`: o valor precisa existir tambem fora
# do contexto de requisicao (o adaptador de cache registra linha fora de uma) e nao pode
# vazar quando a thread do pool e reaproveitada.
_IDENTIFICADOR: contextvars.ContextVar[str] = contextvars.ContextVar(
    "identificador_de_requisicao", default="-"
)


def identificador_atual() -> str:
    """O identificador da requisicao em curso, ou `-` fora de uma."""
    return _IDENTIFICADOR.get()


def novo_identificador() -> str:
    """Gera e adota um identificador curto para a requisicao em curso.

    Oito hexadecimais: o suficiente para nao colidir dentro do volume de uma sessao de
    operador, e curto o bastante para caber no console e ser copiado a mao.
    """
    valor: str = uuid.uuid4().hex[:8]
    _IDENTIFICADOR.set(valor)
    return valor


def esquecer_identificador() -> None:
    """Devolve o contexto ao estado neutro no fim da requisicao.

    Sem isto, uma linha registrada **fora** de requisicao (o aviso de pasta inutilizavel, a
    linha de inicializacao) herdaria o identificador da ultima requisicao daquela thread e
    passaria a afirmar uma correlacao que nao existe: o `id` e da requisicao, nao da thread.
    """
    _IDENTIFICADOR.set("-")


# --- Mascara de privacidade ------------------------------------------------

# Dois padroes, os dois de forma fechada: nada de heuristica por palavra. O identificador de
# kit e o MESMO padrao que a leitura do CSV usa para reconhecer a coluna de ID
# (`_reversa_sdd/architecture.md#6`), e o e-mail e o formato que o proprio arquivo de
# matches traz.
_ID_DE_KIT: re.Pattern[str] = re.compile(r"\b[A-Z]{2}\d{7}\b")
_EMAIL: re.Pattern[str] = re.compile(r"[\w.+-]+@[\w-]+\.[\w.-]+")
_MASCARA_DE_KIT = "<kit>"
_MASCARA_DE_EMAIL = "<email>"


def mascarar(texto: str) -> str:
    """Substitui identificador de kit e e-mail por marcadores.

    O e-mail vem primeiro: o formato de e-mail pode conter o de kit na parte local, e
    mascarar o kit antes deixaria um `<kit>@dominio` sem sentido.
    """
    if not texto:
        return texto
    return _ID_DE_KIT.sub(_MASCARA_DE_KIT, _EMAIL.sub(_MASCARA_DE_EMAIL, texto))


class FiltroDeContexto(logging.Filter):
    """Injeta o identificador da requisicao em todo registro."""

    def filter(self, record: logging.LogRecord) -> bool:
        record.id = identificador_atual()
        return True


class FiltroDePrivacidade(logging.Filter):
    """Aplica a mascara a mensagem, aos argumentos e ao traceback.

    ## Por que no handler, e nao no `except`

    Filtrar no ponto de chamada cobriria as linhas de hoje e deixaria passar a de amanha.
    O filtro no destino cobre **toda** linha que chega ali, inclusive as que ainda nao
    existem.

    ## O traceback exige materializar `exc_text`

    O formatador chama `formatException(record.exc_info)` quando `exc_info` esta presente -
    ou seja, se so mascarassemos a mensagem, a excecao seria formatada **crua** logo depois.
    Por isso o filtro formata a excecao, mascara o texto e zera `exc_info`; o que sobra e
    `exc_text`, que o formatador anexa sem passar pela excecao original.
    """

    _formatador = logging.Formatter()

    def filter(self, record: logging.LogRecord) -> bool:
        texto: str = record.getMessage()
        record.msg = mascarar(texto)
        record.args = ()
        if record.exc_info:
            record.exc_text = mascarar(self._formatador.formatException(record.exc_info))
            record.exc_info = None
        elif record.exc_text:
            record.exc_text = mascarar(record.exc_text)
        if record.stack_info:
            record.stack_info = mascarar(record.stack_info)
        return True


def texto_seguro(valor) -> str:
    """Texto de uma linha so: quebra de linha e controle viram espaco.

    A rota vem do cliente. Sem isso, um caminho com `%0a` escreveria uma linha falsa no
    arquivo de log - injecao de registro, que e a razao de o identificador tambem nao ser
    aceito do cliente (`RF-03`).
    """
    texto: str = "" if valor is None else str(valor)
    return "".join(" " if caractere in "\r\n\t" or ord(caractere) < 32 else caractere
                   for caractere in texto)


# --- Pastas e niveis ------------------------------------------------------


def _raiz_do_projeto() -> str:
    """O pai de `src/`, derivado do proprio arquivo (`src/utils/logs.py`)."""
    return os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def pasta_de_logs() -> str:
    """A pasta dos tres arquivos: `ANALISADOR_LOG_DIR` ou `<raiz>/logs`."""
    apontada: str | None = os.environ.get(VARIAVEL_DA_PASTA)
    if apontada:
        return apontada
    return os.path.join(_raiz_do_projeto(), PASTA_PADRAO)


def nivel_do_ambiente() -> tuple[int, dict[str, int]]:
    """Le `ANALISADOR_LOG_LEVEL`: nivel global e ajustes `modulo=NIVEL` separados por virgula.

    Valor invalido nao derruba nada: cai no padrao. Um sistema que nao sobe porque a
    variavel de log esta com erro de digitacao seria pior do que um sistema que sobe no
    nivel padrao - e o operador descobre o engano pela ausencia do volume esperado.
    """
    bruto: str = os.environ.get(VARIAVEL_DO_NIVEL, NIVEL_PADRAO)
    nivel = logging.INFO
    por_modulo: dict[str, int] = {}
    for pedaco in bruto.split(","):
        pedaco = pedaco.strip()
        if not pedaco:
            continue
        if "=" in pedaco:
            nome, _, valor = pedaco.partition("=")
            # pyrefly: ignore[deprecated]
            convertido = logging.getLevelName(valor.strip().upper())
            if isinstance(convertido, int) and nome.strip():
                por_modulo[nome.strip()] = convertido
            continue
        # pyrefly: ignore[deprecated]
        convertido = logging.getLevelName(pedaco.upper())
        if isinstance(convertido, int):
            nivel: int = convertido
    return nivel, por_modulo


def _formatador() -> logging.Formatter:
    return logging.Formatter(FORMATO, datefmt=FORMATO_DE_DATA)


def _com_filtros(handler: logging.Handler) -> logging.Handler:
    handler.addFilter(FiltroDeContexto())
    handler.addFilter(FiltroDePrivacidade())
    return handler


def _nossos_handlers(logger: logging.Logger) -> list[logging.Handler]:
    return [h for h in logger.handlers if getattr(h, _MARCA, False)]


def configurar() -> None:
    """Monta os tres destinos. Idempotente por marcador no handler.

    Segunda chamada no mesmo processo nao faz nada - nem quando o modulo que a chama foi
    reexecutado, porque o registro de handlers do `logging` e global.
    """
    raiz: logging.Logger = logging.getLogger()
    auditoria: logging.Logger = logging.getLogger(LOGGER_DE_AUDITORIA)

    if _nossos_handlers(raiz) or _nossos_handlers(auditoria):
        return

    nivel, por_modulo = nivel_do_ambiente()
    raiz.setLevel(nivel)
    for nome, valor in por_modulo.items():
        logging.getLogger(nome).setLevel(valor)
    logging.getLogger(LOGGER_DO_SERVIDOR).setLevel(NIVEL_DO_SERVIDOR)

    console: logging.Handler = _com_filtros(logging.StreamHandler(stream=sys.stderr))
    console.setFormatter(_formatador())
    setattr(console, _MARCA, True)
    raiz.addHandler(console)

    pasta: str = pasta_de_logs()
    # Sem arquivo, a auditoria **propaga** para o console: perder a trilha inteira por causa
    # de uma pasta seria trocar um destino degradado por nenhum destino.
    auditoria.propagate = not anexar_arquivos(pasta, raiz, auditoria)

    auditoria.setLevel(logging.INFO)


def anexar_arquivos(pasta: str, raiz: logging.Logger, auditoria: logging.Logger) -> bool:
    """Anexa o arquivo geral e a trilha de auditoria; devolve se conseguiu.

    Pasta inescrevivel (volume do container nao montado) **nao** pode derrubar requisicao
    nem impedir a subida: o diagnostico nao e motivo de indisponibilidade. O aviso sai uma
    vez, e quem chama decide o que fazer com a auditoria - ela passa a propagar para o
    console em vez de sumir.
    """
    try:
        os.makedirs(pasta, exist_ok=True)
        geral = logging.handlers.RotatingFileHandler(
            os.path.join(pasta, ARQUIVO_GERAL),
            maxBytes=TAMANHO_MAXIMO_EM_BYTES,
            backupCount=ARQUIVOS_DE_ROTACAO,
            encoding="utf-8",
        )
        diario = logging.FileHandler(
            os.path.join(pasta, arquivo_de_auditoria_de_hoje()), encoding="utf-8"
        )
    except OSError as erro:
        logging.getLogger(__name__).warning(
            "pasta de log inutilizavel (%s): seguindo so com o console", texto_seguro(erro)
        )
        return False

    for handler in (geral, diario):
        _com_filtros(handler)
        handler.setFormatter(_formatador())
        setattr(handler, _MARCA, True)

    raiz.addHandler(geral)
    auditoria.addHandler(diario)
    return True


def arquivo_de_auditoria_de_hoje() -> str:
    return f"{PREFIXO_DA_AUDITORIA}.{time.strftime('%Y-%m-%d')}.log"


# --- Linhas de acesso e de medicao ----------------------------------------


def registrar_acesso(metodo: str, rota: str, situacao: int, duracao_em_ms: float) -> None:
    """Uma linha por requisicao: metodo, rota, situacao e duracao (`RF-04`)."""
    logging.getLogger(LOGGER_DE_ACESSO).info(
        "acesso: %s %s -> %s (%.1f ms)",
        texto_seguro(metodo),
        texto_seguro(rota),
        situacao,
        duracao_em_ms,
    )


@contextlib.contextmanager
def medir(nome: str):
    """Mede o bloco e registra os milissegundos ao sair (`RN-07`).

    Nomear a etapa e o ponto: um numero solto nao diz o que foi medido, e a decisao sobre o
    cache da arvore (features 025 e 047) precisa da etapa, nao do total da requisicao.
    """
    inicio: float = time.perf_counter()
    try:
        yield
    finally:
        decorrido: float = (time.perf_counter() - inicio) * 1000
        logging.getLogger(LOGGER_DE_MEDICAO).info("%s: %.1f ms", texto_seguro(nome), decorrido)


__all__: list[str] = [
    "FiltroDeContexto",
    "FiltroDePrivacidade",
    "anexar_arquivos",
    "arquivo_de_auditoria_de_hoje",
    "configurar",
    "esquecer_identificador",
    "identificador_atual",
    "mascarar",
    "medir",
    "nivel_do_ambiente",
    "novo_identificador",
    "pasta_de_logs",
    "registrar_acesso",
    "texto_seguro",
]

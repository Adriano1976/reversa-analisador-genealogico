"""Duble SINTETICO de `psycopg2` para a sonda do item 9.

O driver REAL nao esta instalado no `.venv/` do repositorio (e o achado L-26 do
proprio projeto), entao o caminho "driver instalado + banco recusando a conexao"
nao pode ser exercitado com o driver verdadeiro. Este duble existe para medir o
que a APLICACAO faz com o TEXTO da excecao: ele levanta `OperationalError` com
uma mensagem no formato do driver real.

Usuario, senha, host, porta e base sao INVENTADOS. Nenhum valor do `.env` do
projeto foi lido ou transcrito aqui.
"""


class Error(Exception):
    """Raiz dos erros do duble."""


class OperationalError(Error):
    """Equivalente ao `psycopg2.OperationalError`."""


def connect(url, *args, **kwargs):
    """Falha sempre, com mensagem no formato do driver real."""
    raise OperationalError(
        'connection to server at "127.0.0.1", port 5432 failed: FATAL:  '
        'password authentication failed for user "analisador-sonda"'
    )

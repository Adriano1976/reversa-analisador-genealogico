"""Validacao do upload: nome visivel, chave de armazenamento e conteudo.

Modulo puro: nao importa Flask e nao toca o disco. Toda a decisao sobre o que
pode ser gravado vive aqui, para ser testavel isoladamente e para que a rota
fique apenas com a orquestracao.

Nasceu do BUG-20260929-QMLY. O legado gravava o arquivo com o nome enviado pelo
cliente (`os.path.join(UPLOAD_FOLDER, gedcom_file.filename)`), o que permitia
escrita fora da pasta de upload e colisao silenciosa entre envios. Aqui o nome do
cliente deixa de decidir o caminho: a chave de armazenamento e derivada do
conteudo, no servidor, e o nome original vira apenas metadado legivel.

A derivacao e por conteudo (sha256), e nao um UUID aleatorio, porque o valor
precisa ser estavel entre requisicoes: o formulario devolve `gedcom_filename` no
POST seguinte, para a busca de caminho e para a analise de DNA. A mesma arvore
reenviada gera a mesma chave.
"""
from __future__ import annotations

import hashlib
import re

# Declaracao que abre todo GEDCOM valido. A validacao e de CONTEUDO, e nao de
# extensao: o RISK-007 autoriza relaxar a extensao para nao rejeitar GEDCOM de
# exportador legitimo, que quebraria a paridade de parsing com o legado.
CABECALHO_GEDCOM = "0 HEAD"

# A chave e 16 hexadecimais, um separador de dois underscores e o nome visivel.
# A forma e fechada de proposito: exclui `/`, `\` e `..`, de modo que um valor
# vindo do formulario nunca pode escapar da pasta de upload.
_SEPARADOR = "__"
_HEX16 = r"[0-9a-f]{16}"
_FORMATO_CHAVE = re.compile(r"^" + _HEX16 + _SEPARADOR + r"[A-Za-z0-9._-]+$")

# O PREFIXO da chave, sem exigir que o nome INTEIRO seja valido. Existe porque as
# duas perguntas sao diferentes, e a feature 011 precisa das duas:
#
#   `chave_recebida_e_valida` responde "posso RESOLVER este nome?" — e por isso
#   exige a forma inteira, porque e ela que impede escape de caminho;
#   `_PREFIXO_CHAVE` responde "este nome TEM chave?" — e um nome com chave e nome
#   visivel acentuado devolve NAO para a primeira e SIM para a segunda.
#
# Sem esta distincao, o arquivo com acento cairia no mesmo balde do arquivo sem
# chave, e a tela diria ao operador a coisa errada sobre o proprio arquivo.
# `_HEX16` e `_SEPARADOR` sao os MESMOS objetos: a forma do nome e definida uma vez.
_PREFIXO_CHAVE = re.compile(r"^" + _HEX16 + _SEPARADOR)

# Separadores de caminho, dos dois sistemas, e o byte nulo.
_SEPARADORES = ("/", "\\", "\x00")

BOM_UTF8 = b"\xef\xbb\xbf"


def nome_visivel_seguro(nome_original) -> str:
    """Nome de exibicao do arquivo: sem caminho, sem byte nulo, nunca vazio.

    Preserva acentos, espacos e a EXTENSAO original, porque o rotulo e o que o
    usuario reconhece e porque o mesmo tratamento serve ao GEDCOM e ao CSV de
    DNA. Um nome sem extensao nenhuma recebe `.ged`. Nao e usado para compor
    caminho: a pasta de destino e sempre `UPLOAD_FOLDER`.
    """
    nome = nome_original or ""
    for separador in _SEPARADORES:
        nome = nome.replace(separador, "_")
    nome = nome.strip().strip(".")
    if not nome:
        return "arvore.ged"

    # A extensao e PRESERVADA, e nao fixada em `.ged`. O `_guardar_upload` serve
    # tanto ao GEDCOM quanto ao CSV de DNA, e fixar a extensao renomeava o CSV
    # para `<...>.csv.ged`, quebrando a analise de DNA. Regressao do
    # BUG-20260929-QMLY, corrigida em 2026-10-02.
    raiz, ponto, extensao = nome.rpartition(".")
    if ponto and raiz and extensao:
        raiz = raiz.strip().strip(".")
        if not raiz:
            return "arvore.ged"
        return raiz + "." + extensao
    return nome + ".ged"


def chave_de_armazenamento(conteudo: bytes) -> str:
    """Chave derivada do conteudo. Mesmo conteudo, mesma chave."""
    return hashlib.sha256(conteudo).hexdigest()[:16]


def nome_do_arquivo_armazenado(chave: str, nome_original) -> str:
    """Compõe o nome final: chave do servidor primeiro, nome visivel depois."""
    return chave + _SEPARADOR + nome_visivel_seguro(nome_original)


def chave_recebida_e_valida(nome_recebido) -> bool:
    """Aceita apenas valor na forma `<16 hex>__<nome visivel>`.

    Valor ausente, vazio, com separador de caminho ou com nome escolhido pelo
    cliente e recusado. E esta funcao que impede o escape por caminho, sem
    precisar de lista negra.
    """
    if not isinstance(nome_recebido, str) or not nome_recebido:
        return False
    return _FORMATO_CHAVE.match(nome_recebido) is not None


def validar_conteudo_gedcom(conteudo: bytes) -> str | None:
    """Devolve o motivo da recusa, ou None quando o conteudo e aceitavel.

    Verificacao estreita de proposito: apenas a declaracao de cabecalho. A
    gramatica do GEDCOM fica com o `ged4py`, que e quem ja a implementa. Comandos
    de controle tem o byte removido, nao escapam de forma alguma.
    """
    if not conteudo:
        return "arquivo vazio"
    if b"\x00" in conteudo:
        return "conteudo binario"
    texto = conteudo.replace(BOM_UTF8, b"", 1)
    inicio = texto.lstrip()[: len(CABECALHO_GEDCOM)]
    if inicio != CABECALHO_GEDCOM.encode("ascii"):
        return "não começa com a declaração {}".format(CABECALHO_GEDCOM)
    return None


# --- Decomposicao do nome armazenado (feature 011, `T014`) -------------------
#
# Estas duas funcoes existem para a LISTA da tela: a funcao pura de `reporting/`
# precisa saber, para cada arquivo da pasta, como ele se chama para o operador e
# se ele pode ser usado. As duas perguntas se respondem **sem abrir arquivo**, e
# por isso vivem aqui: este modulo ja e o dono da forma do nome, e uma segunda
# definicao dela em outro lugar seria uma segunda verdade sobre a mesma regra.

SEM_CHAVE = "sem chave de conteúdo no nome"
FORA_DA_FORMA = "nome com caractere que a referência não aceita"


def decompor_nome_armazenado(nome) -> tuple[str | None, str]:
    """`(chave, nome_visivel)` do nome armazenado. `(None, nome)` quando nao ha chave.

    A chave sai **so** quando o prefixo de 16 hexadecimais esta la, e ela pode vir
    acompanhada de um nome visivel que a forma fechada recusa — acento e espaco sao
    os casos medidos. Quem decide se o arquivo e ALCANCAVEL e
    `chave_recebida_e_valida`, e nao esta funcao: aqui so se separa o que e chave do
    que e rotulo.

    Nome que nao e `str`, ou vazio, devolve `(None, "")`.
    """
    if not isinstance(nome, str) or not nome:
        return None, ""
    if _PREFIXO_CHAVE.match(nome):
        chave, visivel = nome.split(_SEPARADOR, 1)
        return chave, visivel
    return None, nome


def motivo_de_indisponibilidade(nome) -> str | None:
    """Por que este nome armazenado NAO pode ser usado, ou `None` se ele pode.

    Dois motivos, e a distincao importa para o operador (`D-11`):

    - nao tem os 16 hexadecimais: e arquivo anterior a chave por conteudo, e a
      referencia nao tem como alcanca-lo;
    - tem chave, mas o nome visivel carrega caractere que a forma fechada recusa.
      E o caso do acento e do espaco, medido na pasta real, e o defeito de raiz
      esta registrado como `BUG-20261009-6RKP`.

    Dizer "sem chave" para o arquivo acentuado seria mentir sobre o motivo, e o
    operador concluiria que o arquivo e antigo quando ele nao e.
    """
    chave, _visivel = decompor_nome_armazenado(nome)
    if chave is None:
        return SEM_CHAVE
    if not chave_recebida_e_valida(nome):
        return FORA_DA_FORMA
    return None


def pode_ser_usado(nome) -> bool:
    """`True` quando a referencia alcanca este nome armazenado.

    Delega para `chave_recebida_e_valida`, que e a **mesma** funcao que
    `ArmazenamentoEmDisco.resolver` aplica. Nao ha segundo teste de alcance, de
    proposito: dois testes equivalentes divergem com o tempo, e a tela passaria a
    dizer "disponivel" para um arquivo que o resolvedor recusa.
    """
    return chave_recebida_e_valida(nome)

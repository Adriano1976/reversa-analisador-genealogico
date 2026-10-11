"""O que pode ser gravado, e o que pode ser alcançado: nome visivel, chave e conteudo.

Modulo **puro**: nao importa Flask e nao toca o disco. Toda a decisao sobre o nome do
arquivo armazenado vive aqui, para ser testavel isoladamente e para que a rota fique apenas
com a orquestracao.

## A origem, e o que este modulo tem de nao repetir

Nasceu do `BUG-20260929-QMLY`: o legado gravava com o nome enviado pelo cliente
(`os.path.join(UPLOAD_FOLDER, gedcom_file.filename)`), o que permitia escrever fora da pasta
e colidir em silencio. Aqui o nome do cliente **nao decide o caminho**: a chave e derivada
do conteudo, no servidor, e o nome original vira metadado legivel.

A chave e `sha256(conteudo)` truncado, e nao um UUID, porque o valor precisa ser **estavel
entre requisicoes**: o formulario devolve `gedcom_filename` no POST seguinte. A mesma arvore
reenviada gera a mesma chave — e e isso que permite reconhecer o reenvio identico.

## As tres perguntas deste modulo, que sao diferentes de proposito

| Pergunta | Funcao | Criterio |
|---|---|---|
| "Que nome visivel cabe no disco?" | `nome_visivel_seguro` | tira caminho e byte nulo, nunca devolve vazio |
| "Posso RESOLVER esta referencia?" | `chave_recebida_e_valida` | prefixo de 16 hexadecimais **e** um NOME simples |
| "Posso MOVER este nome?" | `referencia_de_arquivo_da_pasta` | um NOME simples, **sem** exigir a chave |

As tres nao se substituem, e confundi-las ja custou caro uma vez (`BUG-20261009-6RKP`).
"""
from __future__ import annotations

import hashlib
import os
import re

# A declaracao que abre todo GEDCOM valido. A validacao e de CONTEUDO, e nao de extensao:
# o `RISK-007` autoriza relaxar a extensao para nao rejeitar GEDCOM de exportador legitimo,
# o que quebraria a paridade de parsing com o legado.
CABECALHO_GEDCOM = "0 HEAD"

# O nome armazenado e `<16 hexadecimais>__<nome visivel>`.
#
# `_FORMATO_CHAVE` VIVEU AQUI ate 2026-10-10 e foi REMOVIDO: era o alfabeto fechado
# `^[0-9a-f]{16}__[A-Za-z0-9._-]+$`, que recusava o acento e o espaco que o gravador
# **preserva de proposito**. Ele nunca foi a defesa contra escape de caminho — a defesa e
# exigir que a referencia seja um NOME —, e a contradicao entre gravador e resolvedor esta
# registrada no `BUG-20261009-6RKP`, com a regra que a substituiu na `RN-20`.
_SEPARADOR = "__"
_HEX16 = r"[0-9a-f]{16}"

# O PREFIXO da chave, sem exigir que o nome inteiro seja valido. Existe porque as duas
# perguntas do topo sao diferentes: "posso resolver?" exige a forma inteira, e "este nome
# TEM chave?" nao. Sem a distincao, o arquivo com acento cairia no mesmo balde do arquivo
# anterior a convencao de chave, e a tela diria ao operador a coisa errada sobre o proprio
# arquivo. `_HEX16` e `_SEPARADOR` entram aqui como os MESMOS objetos: a forma e escrita uma
# vez so.
_PREFIXO_CHAVE = re.compile(r"^" + _HEX16 + _SEPARADOR)

# Separadores de caminho dos dois sistemas, mais o byte nulo.
_SEPARADORES = ("/", "\\", "\x00")

BOM_UTF8 = b"\xef\xbb\xbf"


# ---------------------------------------------------------------------------
# O nome visivel: o que o operador reconhece, e o que pode ir para o disco
# ---------------------------------------------------------------------------

def nome_visivel_seguro(nome_original) -> str:
    """Nome de exibicao do arquivo: sem caminho, sem byte nulo, nunca vazio.

    A extensao original e **preservada**, porque o rotulo e o que o usuario reconhece e
    porque a mesma funcao serve ao GEDCOM e ao CSV de DNA. Fixar `.ged` aqui renomeava o CSV
    para `<...>.csv.ged` e quebrava a analise de DNA — regressao do proprio `QMLY`, corrigida
    em 2026-10-02 e presa por teste proprio. Nome sem extensao nenhuma recebe `.ged`.

    O resultado **nao** e usado para compor caminho: a pasta de destino e sempre a pasta de
    upload, e quem separa o que e chave do que e rotulo e `decompor_nome_armazenado`.
    """
    nome = nome_original or ""
    for separador in _SEPARADORES:
        nome = nome.replace(separador, "_")
    nome = nome.strip().strip(".")
    if not nome:
        return "arvore.ged"

    raiz, ponto, extensao = nome.rpartition(".")
    if ponto and raiz and extensao:
        raiz = raiz.strip().strip(".")
        if not raiz:
            return "arvore.ged"
        return raiz + "." + extensao
    return nome + ".ged"


def chave_de_armazenamento(conteudo: bytes) -> str:
    """Chave derivada do CONTEUDO. Mesmo conteudo, mesma chave — e ela e estavel."""
    return hashlib.sha256(conteudo).hexdigest()[:16]


def nome_do_arquivo_armazenado(chave: str, nome_original) -> str:
    """Compoe o nome final: a chave do servidor primeiro, o nome visivel depois."""
    return chave + _SEPARADOR + nome_visivel_seguro(nome_original)


# ---------------------------------------------------------------------------
# O conteudo: a recusa e estreita de proposito
# ---------------------------------------------------------------------------

def validar_conteudo_gedcom(conteudo: bytes) -> str | None:
    """Motivo da recusa, ou `None` quando o conteudo e aceitavel.

    A verificacao e estreita: apenas a declaracao de cabecalho. A gramatica do GEDCOM fica
    com o `ged4py`, que ja a implementa. Os comandos de controle **nao** tem o byte removido,
    eles recusam — um byte nulo no meio do arquivo nao e GEDCOM.

    Os tres motivos devolvidos aqui sao texto de contrato: `traducao.py` os carrega dentro da
    excecao, e ha teste que prende o literal na origem.
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


# ---------------------------------------------------------------------------
# O nome ARMAZENADO: separar a chave do rotulo, e decidir o alcance
# ---------------------------------------------------------------------------
#
# Estas funcoes existem para a LISTA da tela e para o botao de aposentar. As duas perguntas
# se respondem **sem abrir arquivo**, e por isso vivem aqui: este modulo ja e o dono da forma
# do nome, e uma segunda definicao dela em outro lugar seria uma segunda verdade sobre a
# mesma regra — o defeito que o `QMLY` e o `6RKP` ja cobraram duas vezes.

SEM_CHAVE = "sem chave de conteúdo no nome"
FORA_DA_FORMA = "nome com caractere que a referência não aceita"


def decompor_nome_armazenado(nome) -> tuple[str | None, str]:
    """`(chave, nome_visivel)` do nome armazenado; `(None, nome)` quando nao ha chave.

    A chave sai **somente** quando o prefixo de 16 hexadecimais esta la. Ela pode vir
    acompanhada de um nome visivel que a referencia nao aceita — e aí o arquivo **tem** chave
    e **nao** e alcancavel, distincao que a tela precisa fazer para nao mentir sobre o motivo.

    Quem decide o alcance e `chave_recebida_e_valida`, nunca esta funcao: aqui so se separa o
    que e chave do que e rotulo.

    Nome que nao e `str`, ou vazio, devolve `(None, "")`.
    """
    if not isinstance(nome, str) or not nome:
        return None, ""
    if _PREFIXO_CHAVE.match(nome):
        chave, visivel = nome.split(_SEPARADOR, 1)
        return chave, visivel
    return None, nome


def chave_recebida_e_valida(nome_recebido) -> bool:
    """`True` quando a referencia pode ser RESOLVIDA para um arquivo da pasta.

    ## O que mudou em 2026-10-10, e por que (`BUG-20261009-6RKP`, `RN-20`)

    Ate entao a forma era um **alfabeto fechado**, e o gravador preserva acento e espaco no
    nome visivel — porque preserva-los e requisito. Os dois lados se contradiziam: o arquivo
    era gravado como `94e2402671702cac__Famílias_Sergipanas.csv` e **recusado na leitura**.
    Medido na pasta do operador: arquivos com acento e com espaco ficavam inalcancaveis, e a
    tela respondia `Erro: Arquivo '...' não existe mais.` — que era **falso**, porque o
    arquivo existia.

    ## A defesa contra escape nunca foi o alfabeto

    Era — e continua sendo — a exigencia de a referencia ser um **NOME**, e nao um caminho. O
    criterio novo e o mesmo que `referencia_de_arquivo_da_pasta` ja aplicava: sem barra, sem
    barra invertida, sem byte nulo, sem `.` nem `..`, e o valor igual ao proprio `basename`.

    Os cinco casos de escape do `BUG-20260929-QMLY` continuam recusados, e **por construcao**:
    `../etc/passwd`, `uploads\\..\\x.ged` e `nome_do_cliente.ged` nao tem o prefixo da chave;
    vazio e `None` saem na primeira linha. Quem tiver o prefixo valido e tentar escapar
    (`<chave>__../x`) e barrado na parte visivel. Ha teste para cada um dos casos, e um
    contrapeso contra o `return False` constante.

    ## O que esta funcao NAO responde

    Ela responde "posso resolver este nome?", e nao "este arquivo existe" — quem faz a segunda
    pergunta e o `os.path.exists` do adaptador. E ela e a **unica** autoridade sobre a
    primeira: a lista da tela e o botao de aposentar perguntam a ela, e nao a um teste proprio,
    para a marca da tela nunca divergir do resolvedor (`D-11`).
    """
    if not isinstance(nome_recebido, str) or not nome_recebido:
        return False
    if _PREFIXO_CHAVE.match(nome_recebido) is None:
        return False
    _chave, visivel = decompor_nome_armazenado(nome_recebido)
    return referencia_de_arquivo_da_pasta(visivel)


def referencia_de_arquivo_da_pasta(nome) -> bool:
    """`True` quando `nome` e um NOME DE ARQUIVO simples, e nao um caminho (`RN-14`).

    ## Por que esta validacao existe, e por que ela NAO reusa a do resolvedor

    Aposentar um arquivo tambem compoe caminho, entao precisa de defesa contra escape. Mas ela
    **nao pode** aplicar `chave_recebida_e_valida`: os arquivos **sem chave** seriam exatamente
    os que nao poderiam ser aposentados — e sao justamente os que o operador mais quer tirar da
    lista, porque sao os inalcancaveis.

    Entao a defesa aqui e de outra natureza e de outro escopo: em vez de exigir a forma
    canonica, exige que o valor seja um **nome**. Nao ha barra, nao ha barra invertida, nao ha
    byte nulo, nao ha `..`, nao ha string vazia, e o valor tem de ser igual ao seu proprio
    `basename`. Um nome que passa aqui so pode apontar para um arquivo **dentro** da pasta de
    upload — e a confirmacao final do diretorio pai e feita pelo adaptador, com o caminho ja
    resolvido.

    Isto **nao** afrouxa `resolver`: as duas funcoes respondem perguntas diferentes ("posso
    LER por referencia?" e "posso MOVER este nome?"), e o resolvedor continua sendo a unica
    autoridade sobre a primeira.
    """
    if not nome or not isinstance(nome, str):
        return False
    if nome in (".", ".."):
        return False
    for separador in _SEPARADORES:
        if separador in nome:
            return False
    return os.path.basename(nome) == nome


def pode_ser_usado(nome) -> bool:
    """`True` quando a referencia alcanca este nome armazenado.

    Delega para `chave_recebida_e_valida`, que e a **mesma** funcao que o resolvedor do
    adaptador aplica. Nao ha segundo teste de alcance, de proposito: dois testes equivalentes
    divergem com o tempo, e a tela passaria a dizer "disponivel" para um arquivo que o
    resolvedor recusa.
    """
    return chave_recebida_e_valida(nome)


def motivo_de_indisponibilidade(nome) -> str | None:
    """Por que este nome armazenado NAO pode ser usado, ou `None` se ele pode.

    Dois motivos, e a distincao importa para o operador (`D-11`):

    - **sem chave**: e arquivo anterior a convencao de chave por conteudo, e a referencia nao
      tem como alcanca-lo;
    - **fora da forma**: tem a chave, mas o nome visivel nao e um NOME simples.

    Dizer "sem chave" para um arquivo que tem chave seria mentir sobre o motivo, e o operador
    concluiria que o arquivo e antigo quando ele nao e.

    ## Nota medida depois da `RN-20`: o segundo ramo ficou quase inalcancavel, e fica

    Depois de o resolvedor passar a aceitar acento e espaco — que e o que o gravador produz —,
    o unico nome com chave que ainda cai no segundo ramo e um que carregue separador de
    caminho, `.`, `..` ou byte nulo na parte visivel. **O gravador nao produz nenhum deles**, e
    o sistema de arquivos nao aceita alguns: um arquivo desses nao nasce pela aplicacao. O ramo
    permanece porque a funcao responde sobre um NOME que chegou de fora, e retirar a resposta
    seria transformar "nao sei por que nao alcanca" em "sem chave" — a mentira que esta funcao
    existe para evitar. Ele e defesa em profundidade, e nao caminho de operacao.
    """
    chave, _visivel = decompor_nome_armazenado(nome)
    if chave is None:
        return SEM_CHAVE
    if not chave_recebida_e_valida(nome):
        return FORA_DA_FORMA
    return None

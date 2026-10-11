"""Da pasta de upload para as linhas das duas abas: selecao, agrupamento e rotulo.

Refazimento da feature `011-escolher-arquivo-da-lista` (acoes `T015`, `T016` e `T033`).

## Por que estas funcoes sao PURAS, e por que moram em `reporting/`

Esta e a camada de "dado -> apresentacao", e ela **nao toca o disco**: recebe entradas
que ja trazem nome, tamanho e data, e devolve os itens que a tela desenha. Isso a torna
testavel sem pasta real, e e o que sustenta o RNF de desempenho — a tela de entrada nao
pode reler os ~29 MB da pasta a cada renderizacao so para escrever nomes.

O lugar das tres alternativas, e por que cada uma foi recusada:

- no adaptador de disco, a apresentacao se misturaria com I/O, e o adaptador passaria a
  conhecer rotulo de tela;
- no template Jinja, a regra de negocio ficaria sem teste de unidade;
- numa segunda copia da forma do nome, haveria **duas verdades** sobre o contrato que
  defende a pasta de upload contra escape de caminho. Por isso a forma do nome e
  perguntada a `utils.validate`, que e o dono dela.

## As quatro perguntas que um item responde, e de onde vem a resposta

1. **De que aba ele e** — pela extensao do nome visivel **cru** (`RN-03`, `D-10`).
2. **Quantos arquivos ele representa** — agrupamento pela chave de conteudo ja embutida
   no nome (`RN-01`), e item proprio quando nao ha chave (`RN-10`).
3. **Que rotulo o operador le** — nome visivel sem a chave e sem a ultima extensao
   (`D-09`, `RN-13`).
4. **Se a referencia alcanca esse arquivo** — perguntado a mesma funcao que o resolvedor
   aplica (`RN-11`, `D-11`), com o motivo escrito quando nao alcanca.
"""
from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import datetime
from typing import Iterable, Protocol

from utils.validate import (
    decompor_nome_armazenado,
    motivo_de_indisponibilidade,
    pode_ser_usado,
)

# Tudo o que nao e letra, digito ou sublinhado. O sublinhado entra na classe de proposito,
# porque na pratica ele separa palavras (`arvore_sem_chave`), e o operador le melhor com
# espaco. `\w` em Python 3 ja e sensivel a acento, entao `Famílias` sobrevive inteiro — o
# rotulo nao pode virar transliteracao.
_SIMBOLOS = re.compile(r"[\W_]+")

# As duas unicas extensoes que decidem aba. Ficam aqui, e nao espalhadas pela rota, para
# que a particao tenha um dono so e possa ser lida de uma vez.
ABA_DE_ARVORES = ".ged"
ABA_DE_DNA = ".csv"


class Entrada(Protocol):
    """O que a montagem da lista exige de uma entrada da pasta.

    Estrutural de proposito: o teste de unidade monta entradas proprias sem arrastar a
    fronteira (`ports/`) para dentro do teste da apresentacao. O tipo real e
    `ports.EntradaArmazenada`, e ele satisfaz este contrato.
    """

    nome: str
    bytes: int
    modificado_em: float


@dataclass(frozen=True)
class ItemDaLista:
    """Uma linha da tabela, como a tela a desenha.

    `nome_armazenado` e a referencia que volta no formulario, e `nome_exibido` e o rotulo:
    os dois **nunca** sao a mesma string, e a tela usa o segundo. A chave de conteudo nao e
    assunto do operador (`D-09`).

    `disponivel` e `motivo_indisponivel` vem de `utils.validate` e sao o que impede a tela
    de oferecer, como se funcionasse, um item que a referencia nao alcanca.
    """

    nome_exibido: str
    nome_armazenado: str
    chave: str | None
    quantidade: int
    bytes: int
    modificado_em: float
    disponivel: bool
    motivo_indisponivel: str | None = None


def rotulo_limpo(nome_visivel: str) -> str:
    """O nome do arquivo como o operador o le: sem a ultima extensao e sem simbolos.

    `Backup-Arvore-Sandro-12-11-2024.ged` vira `Backup Arvore Sandro 12 11 2024`, e
    `Famílias_Sergipanas.csv` vira `Famílias Sergipanas`.

    ## Duas decisoes, e o custo de cada uma

    1. **So a ULTIMA extensao sai.** `planilha.csv.ged` vira `planilha csv`, e nao
       `planilha`. O `.csv` do meio e informacao: e o unico sinal que resta de que aquele
       `.ged` e, no conteudo, um relatorio de DNA. Apagar tudo o que parece extensao
       tiraria do operador o que o `D-08` decidiu **nao** esconder.
    2. **Ponto inicial nao e extensao.** Em `.ged` nao ha raiz antes do ponto, entao nada e
       retirado. A leitura ingenua ("corta no ultimo ponto") devolveria rotulo **vazio**, e
       a tela mostraria uma linha em branco — pior do que um rotulo feio.

    ## O que esta funcao NAO decide

    Ela nao escolhe a aba e nao decide alcance. As duas coisas leem o nome visivel **cru**,
    e nao o rotulo: o `D-08` mantem `planilha.csv.ged` na aba de arvores justamente pelo
    nome, e esconder a extensao na tela nao pode mudar isso. Por isso a formatacao acontece
    por ultimo, depois de tudo o que o nome governa.
    """
    raiz, ponto, _extensao = nome_visivel.rpartition(".")
    base = raiz if (ponto and raiz) else nome_visivel
    return _SIMBOLOS.sub(" ", base).strip()


def rotulo_de_referencia(nome_armazenado: str) -> str:
    """Rotulo de tela a partir do NOME ARMAZENADO, sem passar pela lista inteira.

    A rota precisa disto para as mensagens ("o arquivo X saiu da lista") sem vazar a chave
    de conteudo para os olhos do operador, e sem montar as duas abas so para formatar um
    nome. E a mesma formatacao do item, pelo mesmo caminho: separa a chave e limpa o resto.
    """
    _, visivel = decompor_nome_armazenado(nome_armazenado)
    return rotulo_limpo(visivel)


def formatar_data_br(modificado_em: float) -> str:
    """Data do arquivo em `dd/mm/aaaa`, para a coluna "Enviado em".

    ## De onde o valor vem, e por que a coluna se chama "Enviado em"

    Vem do `os.stat` da pasta, entao e a data de **modificacao do arquivo no disco**. Para
    um arquivo guardado pela aplicacao essa e a data do envio, porque a gravacao e a unica
    coisa que toca o arquivo; quem copia um arquivo para a pasta a mao muda essa data — e e
    por isso que o cabecalho da coluna carrega um `title` dizendo de onde o numero vem, em
    vez de o rotulo prometer mais do que entrega.

    ## Instante que o sistema nao converte devolve celula vazia, e nao excecao

    Um `OverflowError` ou `OSError` aqui viraria `500` na TELA DE ENTRADA — a tela que lista
    tudo — por causa de uma celula de data. O custo disso e desproporcional ao valor da
    informacao, entao a conversao falha para string vazia.
    """
    try:
        return datetime.fromtimestamp(modificado_em).strftime("%d/%m/%Y")
    except (OverflowError, OSError, ValueError):
        return ""


def itens_da_aba(entradas: Iterable[Entrada], extensao: str) -> list[ItemDaLista]:
    """Itens de UMA aba: filtra pela extensao, agrupa pelo conteudo, ordena por data.

    ## A particao, e por que ela le o nome CRU

    `extensao` e comparada com o **nome visivel**, e nao com o conteudo (`RN-09`, `D-10`).
    O `.xlsx` da pasta real nao entra em aba nenhuma, e `planilha.csv.ged` entra na aba de
    arvores **apesar** de o conteudo ser CSV: quem decide e o nome. Arquivo que anuncia um
    tipo e entrega outro continua listado, e quem o recusa e o uso — abrir a lista custaria
    a leitura da pasta inteira a cada renderizacao.

    ## O agrupamento, e o caso que ele NAO alcanca

    A chave de 16 hexadecimais ja esta no nome, entao agrupar nao custa leitura nenhuma. O
    arquivo **sem** chave e anterior a essa convencao: a chave nao o alcanca, e ler o
    conteudo para agrupa-lo custaria os mesmos ~29 MB. Ele vira item proprio, e nunca se
    junta a outro (`RN-10`) — nem a outro arquivo igualmente sem chave.

    ## A ordem

    Data decrescente, com empate pelo rotulo. Nao e decoracao: o nome exibido **nao e
    unico** (ha tres arquivos `Arvore_Unificada_Oficial_V1_2.ged` na pasta real), e e a data
    que distingue um do outro. O desempate pelo rotulo existe para a ordem nao depender da
    ordem em que o sistema de arquivos devolveu as entradas.
    """
    # Dois baldes, e a razao de serem dois: o de chave e um dicionario, porque chaves iguais
    # sao o MESMO item; o sem chave e uma lista de grupos de um, porque nome igual nao
    # significa conteudo igual.
    por_chave: dict[str, list[Entrada]] = {}
    sem_chave: list[list[Entrada]] = []

    for entrada in entradas:
        chave, visivel = decompor_nome_armazenado(entrada.nome)
        if not visivel.endswith(extensao):
            continue
        if chave is None:
            sem_chave.append([entrada])
        else:
            por_chave.setdefault(chave, []).append(entrada)

    itens = [_montar_item(grupo) for grupo in (*por_chave.values(), *sem_chave)]
    itens.sort(key=lambda item: (-item.modificado_em, item.nome_exibido))
    return itens


def _montar_item(grupo: list[Entrada]) -> ItemDaLista:
    """Um item a partir dos arquivos que representam o mesmo conteudo.

    O **representante** e o arquivo mais recente do grupo. Ele e quem carrega a referencia
    devolvida ao formulario: e a versao que o operador acabou de mandar, e a unica escolha
    que nao depende da ordem de leitura do diretorio.
    """
    representante = max(grupo, key=lambda entrada: entrada.modificado_em)
    chave, _visivel = decompor_nome_armazenado(representante.nome)
    return ItemDaLista(
        nome_exibido=_nome_a_exibir(grupo),
        nome_armazenado=representante.nome,
        chave=chave,
        quantidade=len(grupo),
        bytes=sum(entrada.bytes for entrada in grupo),
        modificado_em=representante.modificado_em,
        disponivel=pode_ser_usado(representante.nome),
        motivo_indisponivel=motivo_de_indisponibilidade(representante.nome),
    )


def _nome_a_exibir(grupo: list[Entrada]) -> str:
    """O rotulo do grupo, sem chave vazada (`D-09`).

    A regra e: entre os nomes visiveis do grupo, prefira um que **nao** comece com chave.
    Existe porque o operador pode reenviar um arquivo que ja tinha chave no nome — caso
    medido, chave `080e7943572d2652` —, e o grupo passa a ter dois nomes visiveis, um deles
    com a chave crua dentro. Exibir o primeiro em ordem alfabetica mostraria a chave.

    Se **todos** comecarem com chave, a chave e retirada do primeiro em ordem alfabetica:
    mostrar um rotulo sem a chave e melhor do que mostrar a chave, mesmo que o rotulo
    resultante nao seja o nome que o operador digitou.
    """
    visiveis = [decompor_nome_armazenado(entrada.nome)[1] for entrada in grupo]
    sem_chave = sorted(v for v in visiveis if decompor_nome_armazenado(v)[0] is None)
    if sem_chave:
        return rotulo_limpo(sem_chave[0])
    return rotulo_limpo(decompor_nome_armazenado(sorted(visiveis)[0])[1])

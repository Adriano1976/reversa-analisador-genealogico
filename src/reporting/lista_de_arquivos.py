"""Transformacao das entradas da pasta em ITENS de lista, para as duas abas da tela.

Feature `011-escolher-arquivo-da-lista`, acoes `T015` e `T016`.

## Por que isto e uma funcao PURA, e nao um metodo do adaptador

A `D-02` decidiu que o agrupamento pela chave e a marca de "sem chave" moram aqui, e
nao no adaptador nem no template:

- no adaptador, misturaria apresentacao com I/O, e o adaptador passaria a saber o que
  e um rotulo de tela;
- no template, Jinja viraria lugar de regra e nao haveria teste de unidade;
- numa segunda implementacao da forma do nome, haveria **duas verdades** sobre o
  mesmo contrato — que e a defesa contra escape da pasta de upload.

Pura tambem significa **testavel sem disco**: a entrada nao tem caminho, so nome e
atributos. Quem le o diretorio e a porta (`ArmazenamentoDeArquivos.listar`).

## O que a funcao NAO faz

- **Nao abre arquivo.** A extensao que decide a aba e a do NOME visivel, e o alcance
  vem de `utils.validate`, que so olha o nome. E o que evita reler 29 MB por
  renderizacao (RNF de desempenho).
- **Nao filtra por conteudo** (`D-08`). Arquivo cujo nome anuncia um tipo e cujo
  conteudo e outro continua na lista; quem recusa e o USO.
- **Nao esconde o indisponivel** (`RN-11`). Ele ganha marca e motivo, e continua ali.
"""
from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import datetime
from typing import Iterable, Protocol

from utils.validate import decompor_nome_armazenado, motivo_de_indisponibilidade, pode_ser_usado

# Tudo o que NAO e letra, digito ou sublinhado -- e o sublinhado entra na lista de
# proposito, porque na pratica ele separa palavras (`arvore_sem_chave`). `\w` em Python
# 3 ja e sensivel a acento, entao `Familias` e `Famílias` sobrevivem inteiros.
_SIMBOLOS = re.compile(r"[\W_]+")


class Entrada(Protocol):
    """O que a funcao pura exige de uma entrada da listagem.

    Estrutural de proposito: assim o teste de unidade monta entradas proprias, sem
    arrastar a fronteira (`ports/`) para dentro do teste da apresentacao. O tipo real
    e `ports.EntradaArmazenada`, e ele satisfaz este contrato.
    """

    nome: str
    bytes: int
    modificado_em: float


@dataclass(frozen=True)
class ItemDaLista:
    """Uma linha da lista, como a tela a desenha.

    `nome_exibido` e o rotulo, e `nome_armazenado` e a referencia que o formulario
    devolve. Os dois **nunca** sao a mesma string, e a tela usa o primeiro: a chave de
    conteudo nao e assunto do operador (`D-09`). O rotulo ainda passa por
    `rotulo_limpo`, que tira a extensao e troca os simbolos por espaco (`RN-13`) — mas
    **so na tela**: a particao por aba e o alcance por referencia continuam lendo o nome
    visivel cru.

    `disponivel` e `motivo_indisponivel` vem de `utils.validate` e sao o que impede a
    tela de oferecer, como se funcionasse, um item que a referencia nao alcanca.
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
    """O nome do arquivo como o operador o le: sem a extensao e sem os simbolos (`RN-13`).

    `Backup-Arvore-Sandro-12-11-2024.ged` vira `Backup Arvore Sandro 12 11 2024`, e
    `Famílias_Sergipanas.csv` vira `Famílias Sergipanas`.

    ## Duas decisoes, e por que cada uma

    1. **So a ULTIMA extensao sai.** `planilha.csv.ged` vira `planilha csv`, e nao
       `planilha`. O `.csv` do meio e informacao: e o unico sinal que sobra de que
       aquele `.ged` e, no conteudo, um relatorio de DNA. Apagar tudo o que parece
       extensao tiraria do operador o que `D-08` decidiu NAO esconder.
    2. **Ponto inicial nao e extensao.** Num nome como `.ged` nao ha raiz antes do
       ponto, entao nada e retirado -- a alternativa devolveria rotulo VAZIO, que e
       pior do que um rotulo feio. `rpartition` faz essa distincao de graca.

    ## O que esta funcao NAO decide

    Ela nao escolhe a aba, e nao decide se o item e alcancavel. As duas coisas olham o
    nome VISIVEL **cru** (`RN-03`, `D-10`, `RN-12`), e nao o rotulo: o `D-08` mantem
    `planilha.csv.ged` na aba de arvore justamente pelo nome, e esconder a extensao na
    tela nao pode mudar isso. Por isso a formatacao acontece no FIM, depois de tudo o
    que o nome decide.
    """
    raiz, ponto, _extensao = nome_visivel.rpartition(".")
    base = raiz if (ponto and raiz) else nome_visivel
    return _SIMBOLOS.sub(" ", base).strip()


def rotulo_de_referencia(nome_armazenado: str) -> str:
    """Rotulo de tela a partir do NOME ARMAZENADO, sem passar pela lista (`D-09`).

    A rota precisa disto para as mensagens — "o arquivo X foi aposentado" — sem vazar
    a chave de conteudo para os olhos do operador, e sem montar uma lista inteira so
    para formatar um nome. E a mesma formatacao do item, pelo mesmo caminho: decompor a
    chave e limpar o resto.
    """
    _, visivel = decompor_nome_armazenado(nome_armazenado)
    return rotulo_limpo(visivel)


def formatar_data_br(modificado_em: float) -> str:
    """Data do arquivo em `dd/mm/aaaa`, para a coluna "Enviado em" (`T035`).

    ## De onde o valor vem, e por que a coluna se chama "Enviado em"

    Ele vem do `os.stat` da pasta (`EntradaArmazenada.modificado_em`), entao e a data de
    **modificacao do arquivo no disco**. Para um arquivo guardado pela aplicacao, essa e
    a data do envio, porque a gravacao e a unica coisa que toca o arquivo. Quem copia um
    arquivo para a pasta a mao muda essa data — e por isso o cabecalho da coluna carrega
    um `title` dizendo de onde o numero vem, em vez de o rotulo prometer mais do que ele
    entrega.

    ## Instante que o sistema nao converte devolve celula vazia, e nao excecao

    Um `OverflowError` ou `OSError` aqui viraria `500` na TELA DE ENTRADA — a tela que
    lista tudo — por causa de uma celula de data. O custo disso e desproporcional ao
    valor da informacao, entao a conversao falha para uma string vazia.
    """
    try:
        return datetime.fromtimestamp(modificado_em).strftime("%d/%m/%Y")
    except (OverflowError, OSError, ValueError):
        return ""


def itens_da_aba(entradas: Iterable[Entrada], extensao: str) -> list[ItemDaLista]:
    """Itens de UMA aba: filtra pela extensao do nome visivel, agrupa pela chave, ordena.

    ## As quatro decisoes, e de onde cada uma vem

    1. **Selecao por extensao do nome visivel** (`RN-03`, `D-10`). O `.xlsx` da pasta
       real nao entra em aba nenhuma, e `planilha.csv.ged` entra na aba de arvore
       apesar de o conteudo ser CSV — quem decide e o nome, e e o que `RN-09` declara.
    2. **Agrupamento pela chave de conteudo** (`RN-01`), que ja esta no nome. Arquivo
       **sem** chave vira item proprio, nunca agrupado (`RN-10`): a chave nao o
       alcanca, e ler o conteudo para agrupa-lo custaria os 29 MB que o RNF evita.
    3. **Rotulo sem chave vazada** (`D-09`). Caso medido: o operador reenviou um
       arquivo que ja tinha chave no nome, e o grupo passou a ter dois rotulos, um
       deles com a chave crua. Exibir o primeiro em ordem alfabetica mostraria a chave.
    4. **Ordem por data decrescente** (`D-09`). O nome exibido **nao e unico** — ha
       tres arquivos chamados `Arvore_Unificada_Oficial_V1_2.ged` na pasta real —, e e
       a data que distingue; por isso ela e campo obrigatorio do item.
    """
    grupos: dict[tuple[str, str], list[Entrada]] = {}
    for entrada in entradas:
        chave, visivel = decompor_nome_armazenado(entrada.nome)
        if not visivel.endswith(extensao):
            continue
        # A chave agrupa; a ausencia dela nao agrupa nada. O nome entra na chave do
        # dicionario para que dois arquivos sem chave NAO caiam no mesmo item.
        marca = ("com", chave) if chave is not None else ("sem", entrada.nome)
        grupos.setdefault(marca, []).append(entrada)

    itens = [_montar_item(grupo) for grupo in grupos.values()]
    # `sort` estavel, e a data decrescente e o criterio. Empate cai no nome, para a
    # ordem nao depender da ordem de leitura do diretorio.
    itens.sort(key=lambda i: (-i.modificado_em, i.nome_exibido))
    return itens


def _montar_item(grupo: list[Entrada]) -> ItemDaLista:
    """Um item a partir dos arquivos que compartilham a mesma marca."""
    representante = max(grupo, key=lambda e: e.modificado_em)
    chave, _ = decompor_nome_armazenado(representante.nome)
    return ItemDaLista(
        nome_exibido=_rotulo_do_grupo(grupo),
        nome_armazenado=representante.nome,
        chave=chave,
        quantidade=len(grupo),
        bytes=sum(e.bytes for e in grupo),
        modificado_em=representante.modificado_em,
        disponivel=pode_ser_usado(representante.nome),
        motivo_indisponivel=motivo_de_indisponibilidade(representante.nome),
    )


def _rotulo_do_grupo(grupo: list[Entrada]) -> str:
    """O nome a exibir, sem chave vazada (`T016`, `D-09`).

    A regra e: entre os nomes visiveis do grupo, prefira um que **nao** comece com
    chave. Se todos comecarem — caso possivel, se o operador reenviar duas vezes um
    arquivo ja chaveado —, entao a chave e retirada do primeiro em ordem alfabetica,
    porque mostrar a chave crua e pior do que mostrar um rotulo sem ela.
    """
    visiveis = []
    for entrada in grupo:
        _, visivel = decompor_nome_armazenado(entrada.nome)
        visiveis.append(visivel)

    limpos = sorted(v for v in visiveis if decompor_nome_armazenado(v)[0] is None)
    if limpos:
        return rotulo_limpo(limpos[0])
    _, sem_chave = decompor_nome_armazenado(sorted(visiveis)[0])
    return rotulo_limpo(sem_chave)

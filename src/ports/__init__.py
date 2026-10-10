"""Portas da fronteira de aplicacao da Onda 2 (RF-02, RF-08, D-02, D-03).

Uma **porta** aqui e um `Protocol` — a interface que o caso de uso consome por
parametro, sem nunca instanciar a implementacao concreta. Quem implementa mora em
`ports/adaptadores.py` e e montado na borda (`src/app.py`).

## Quais portas existem, e por que sao estas

| Porta | O que a fronteira consome | Metodos |
|-------|---------------------------|---------|
| `ArmazenamentoDeArquivos` | gravar o upload, resolver a referencia recebida, LISTAR a pasta e APOSENTAR um arquivo | 4 |
| `CarregadorDeArvores` | entregar a arvore a partir da referencia | 1 |
| `RepositorioDeArvores` | persistencia da arvore — **Onda 3, sem implementacao** | 2 |
| `RegistroDeAnalises` | persistencia HISTORICA da analise — **feature 008** | 1 |

`RF-02` nomeia as duas primeiras como "armazenamento de arquivo" e "repositorio de
arvore". `CarregadorDeArvores` e a **terceira**, acrescentada pela `D-02` e nao
prevista no `requirements.md`: sem ela, ou o caso de uso importaria
`parsers.gedcom_parser` (acoplando a aplicacao a um pacote de borda) ou cada ramo
da rota repetiria a resolucao de caminho e o parse. Fica declarado como desvio.

A **quarta** — `RegistroDeAnalises` — vem da feature `008-persistencia-postgres-docker`.
Ela guarda o **resultado** da analise depois do processamento, e nao a arvore: e o
que a distingue de `RepositorioDeArvores`, que segue **declarado, sem implementacao
e sem consumidor**. O payload dela viaja em tipos proprios, declarados no fim deste
modulo, para que o adaptador receba **dado ja projetado** e nao precise conhecer o
formato do resultado do nucleo (`D-15`).

Nesta onda **nao** existe Protocolo para leitura de CSV nem para emissao de
diagrama: o contrato entre nucleo e fronteira para essas duas continua sendo a
classe concreta `Dependencias`, de `core/dna_analysis.py`, como a feature 005 a
estabilizou.

## O dono, nas tres portas

`dono` e parametro **obrigatorio** de `ArmazenamentoDeArquivos.guardar`,
`ArmazenamentoDeArquivos.resolver`, `CarregadorDeArvores.carregar` e dos dois
metodos de `RepositorioDeArvores`. A assimetria entre as portas — o repositorio
com dono desde a feature 006 e o armazenamento sem — acabou na feature
`007-dono-no-port-e-baseline`, e o motivo e o custo: a Onda 3 teria de reabrir toda
assinatura de porta e todos os chamadores para acrescenta-lo depois.

Ele e **costura de assinatura, e nao funcionalidade**: nao entra na chave, no nome
armazenado nem no caminho de nada, e nenhum arquivo e separado por dono. As
dividas #3 e #4 continuam abertas (`RN-06`).

**Esta frase deixou de valer na feature `011-escolher-arquivo-da-lista`.** Ate
entao ela dizia, com razao, que nenhum metodo novo havia sido criado em nenhuma
porta. A `011` criou o **primeiro**: `ArmazenamentoDeArquivos.listar`, que devolve
as entradas da pasta para a tela montar a lista de escolha. O motivo de ele
tambem receber `dono` e o mesmo do paragrafo acima, e nao simetria decorativa:
deixar o parametro de fora agora obrigaria a reabrir esta assinatura e todos os
chamadores depois, que e exatamente o custo que a feature 007 pagou para nao ter.

A `T033`/`T034` da mesma feature criou o **segundo**: `aposentar`, que tira o
arquivo da lista movendo-o para `<pasta>/_aposentados/`. Ele **nao** contraria a
`RN-07` — nada e apagado, e o arquivo continua no disco —, e o `dono` entra com o
mesmo alcance de sempre: sem comportamento.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Protocol

if TYPE_CHECKING:
    # Import so para o checador de tipos. Em execucao a anotacao e uma string
    # (`from __future__ import annotations`), e a porta nao arrasta o parser para
    # dentro de quem so quer o contrato.
    from parsers.gedcom_parser import Tree


class ArmazenamentoDeArquivos(Protocol):
    """Grava o upload sob chave derivada do conteudo e resolve a referencia de volta.

    As duas operacoes vivem na mesma porta porque sao o mesmo ciclo de vida: quem
    grava e quem le depois usam exatamente o mesmo identificador, e a `RF-09`
    proibe que o nome e o caminho voltem a ser intercambiaveis.
    """

    def guardar(self, conteudo: bytes, nome_original: str | None, tipo: str,
                dono: str) -> tuple[str | None, str | None]:
        """Valida ANTES de gravar e devolve `(referencia, motivo)`.

        `motivo is None` significa aceito, e `referencia` e o **caminho completo**
        do arquivo gravado — nunca um nome a ser remontado por quem chama.

        `motivo` preenchido significa recusado, e nesse caso **nada foi gravado**
        (`RF-10`). O motivo e texto, nao excecao: transforma-lo na excecao de
        dominio tipada e trabalho do caso de uso, nao do adaptador (`RF-03`,
        achado `A002`).

        `tipo` e o que decide se ha validacao de conteudo — hoje `"gedcom"` valida
        o cabecalho e `"csv"` nao valida conteudo nenhum. A assimetria e a divida
        #10, preservada de proposito nesta onda.

        `dono` e a identidade de quem enviou o dado, e entra **sem comportamento**
        (`RN-01`, `RN-02`). Ultimo parametro posicional e **sem valor padrao**, pela
        mesma forma do `RepositorioDeArvores`: um padrao deixaria toda chamada
        passar sem o dono e a Onda 3 nao teria onde ancorar.

        **O dono nao isola nada.** A chave continua derivada do conteudo, o nome
        armazenado continua `<chave>__<nome visivel>` e o caminho continua o mesmo,
        entao dois envios do mesmo conteudo com donos diferentes reencontram o
        MESMO arquivo. O armazenamento e unico por processo: a divida #4 (ausencia
        de isolamento) e a #3 (corrida entre requisicoes concorrentes) seguem
        abertas, e nenhuma entrega desta feature pode ser citada como tendo-as
        fechado (`RN-06`).
        """
        ...

    def resolver(self, referencia: str | None, dono: str) -> str | None:
        """Caminho do arquivo ja armazenado, ou `None`.

        `None` cobre as duas recusas, e cobre-as pelo mesmo motivo: nos dois casos
        nao existe arquivo a ler. Sao elas a **forma invalida** — o que impede um
        `gedcom_filename` manipulado de apontar para fora da pasta de upload — e o
        **arquivo ausente** no disco.

        `dono` entra pela mesma razao do `guardar`, e com o mesmo alcance: ele
        **nao** filtra nada. Quem resolve a referencia continua sendo a chave de
        conteudo, e a validacao de forma continua vindo antes de qualquer
        `os.path.exists`. O parametro existe para as duas operacoes da porta
        ficarem simetricas entre si e com o `RepositorioDeArvores`.
        """
        ...

    def listar(self, dono: str) -> list["EntradaArmazenada"]:
        """Entrada da pasta de upload: nome armazenado, bytes e data. **Nao le conteudo.**

        A `011-escolher-arquivo-da-lista` (`D-01`) trouxe esta operacao para a porta,
        e nao para a rota, porque a feature 006 tirou o acesso a disco da borda:
        `_arvore_do_formulario()` nao resolve caminho. Um `os.listdir` na rota
        desfaria essa fronteira e tornaria a listagem impossivel de testar sem
        pasta real.

        **O que ela lista, e o que ela NAO faz** (`D-08`, `RN-09`, `D-11`):

        - lista **tudo** o que e arquivo na pasta, sem julgar conteudo e sem julgar
          nome. Nao ha filtro aqui: quem separa as abas e quem marca o item
          indisponivel e a funcao pura de `reporting/`, que decide pelo NOME;
        - **nao abre arquivo nenhum**. O que ela le do diretorio e o nome, e do
          arquivo sao os atributos do sistema de arquivos (tamanho e data). E o
          que evita reler 29 MB a cada renderizacao, e e o que faz o agrupamento
          pela chave — que ja esta no nome — ser barato;
        - **pasta ausente devolve lista vazia, e nao excecao** (`D-07`). Instalacao
          nova tem a pasta criada e vazia, e uma pasta que desapareca sob a
          aplicacao em execucao nao pode virar erro na tela de entrada. O `D-07`
          recusou explicitamente o `os.makedirs` aqui: criar diretorio dentro de
          uma leitura e efeito colateral escondido;
        - **nao escreve nada**: listar e leitura pura (`RF-08`, `RN-06`).

        `dono` entra pela mesma razao e com o mesmo alcance dos outros metodos:
        **nao filtra nada** (dividas #3 e #4 abertas). Quem decide se uma entrada
        pode ser usada e a forma do nome, aplicada na leitura — e nao a identidade.
        """
        ...

    def aposentar(self, referencia: str | None, dono: str) -> bool:
        """Tira o arquivo da LISTA movendo-o para uma subpasta. **Nao apaga nada.**

        `True` significa que o arquivo saiu da pasta de upload; `False`, que nada foi
        movido — referencia em forma de caminho, arquivo inexistente, ou ja haver um
        aposentado com o mesmo nome.

        ## Aposentar, e nao apagar (`RN-14`)

        A `RN-07` diz que a aplicacao **nunca apaga** arquivo enviado, e ela continua
        valendo: o que este metodo faz e MOVER o arquivo para `<pasta>/_aposentados/`,
        onde ele permanece inteiro, com o mesmo nome e o mesmo conteudo. O operador
        deixa de ve-lo na lista, e o dado nao some. Desfazer e mover de volta.

        ## Por que a lista nao precisa de filtro novo

        Quem le a pasta e `listar`, e ela **ja** ignora subdiretorio, porque so aceita
        `os.path.isfile`. Aposentar para dentro da propria pasta aproveita isso: o
        arquivo sai da tela sem que nenhuma regra de filtragem precise ser acrescentada
        — e sem uma lista de excecoes que alguem teria de manter.

        ## A referencia e mais permissiva aqui do que em `resolver`, e isso e
        ## deliberado

        A defesa contra escape continua existindo, mas com outro criterio
        (`utils.validate.referencia_de_arquivo_da_pasta`): qualquer NOME simples, e nao
        apenas a forma canonica com chave. O motivo e medido — os arquivos **sem chave**
        da pasta real sao os inalcancaveis, e sao exatamente os que o operador quer
        tirar da lista. Exigir a chave aqui tornaria impossivel aposentar os tres que
        mais incomodam. `resolver` **nao** afrouxa: ler por referencia continua exigindo
        a forma fechada.

        `dono` entra pela mesma razao dos outros metodos: **nao filtra nada**. A pasta
        de aposentados nao e separada por dono.
        """
        ...


@dataclass(frozen=True)
class EntradaArmazenada:
    """Um arquivo da pasta de upload, como a LISTAGEM o ve (`D-01`).

    Nao e o arquivo: e o retrato do diretorio. Os tres campos sao os unicos que a
    leitura de uma entrada produz, e nenhum deles exige abrir o conteudo.

    `nome` e o **nome armazenado** (`<16 hex>__<nome visivel>`), e nao o visivel: e
    ele que o formulario devolve na requisicao seguinte, e e ele que o resolvedor
    aceita. Quem deriva o rotulo de tela e a funcao pura de `reporting/`, a partir
    deste campo.

    `modificado_em` e o instante do sistema de arquivos, em segundos desde a epoch,
    na mesma unidade que `os.path.getmtime`. A ordem da lista e por ele, decrescente:
    o nome exibido nao e unico — medido, ha tres arquivos chamados
    `Arvore_Unificada_Oficial_V1_2.ged` na pasta real — e e a data que distingue.
    """

    nome: str
    bytes: int
    modificado_em: float


class CarregadorDeArvores(Protocol):
    """Entrega a arvore a partir de uma referencia recebida (`D-02`).

    **Um unico metodo, e essa e a condicao declarada da `D-02`:** se esta porta
    precisar de um segundo metodo, a decisao esta errada e o `/reversa-audit` deve
    ser reexecutado para reabri-la. O executor da feature nao tem autoridade para
    acrescentar o segundo metodo por conveniencia.
    """

    def carregar(self, referencia: str, dono: str) -> Tree | None:
        """Arvore da referencia, ou `None` quando ela nao resolve para arquivo existente.

        `None` significa "nao ha o que carregar", e nao "arvore vazia": quem chama
        ja distinguiu o campo de formulario ausente antes de chegar aqui, e
        traduz o `None` na mensagem de referencia que nao existe mais.

        `dono` chega **por chamada** e e repassado a `ArmazenamentoDeArvores.resolver`
        — este e o unico ponto de producao que resolve referencia. Por chamada, e
        nao na construcao do adaptador, porque os adaptadores sao **singletons de
        processo**, montados uma vez no import de `src/app.py`: congelar identidade
        neles e exatamente o que a Onda 3 teria de desfazer.

        A porta continua com **um unico metodo**, que era a condicao declarada da
        `D-02` da feature 006 — a condicao era sobre a contagem de metodos, e ela
        segue satisfeita. Nenhum isolamento e implementado aqui (`RN-06`).
        """
        ...


class RepositorioDeArvores(Protocol):
    """Contrato de persistencia da arvore para a **Onda 3**. Sem implementacao.

    Declarado e **sem consumidor**, de proposito (`D-03`): ele existe para dar
    lugar tipado onde a persistencia vai encaixar, sem inventar comportamento
    agora. Nenhum caso de uso o chama nesta onda, e **nao** existe adaptador em
    memoria — um adaptador em memoria reintroduziria, com outro nome, o estado
    global de processo que a feature 005 removeu.

    `dono` e parametro **obrigatorio** em todo metodo desde ja (`RF-08`). Adiar o
    dono reabriria toda assinatura de porta na Onda 3, que e o custo que esta
    decisao existe para nao pagar. Nenhum comportamento de isolamento e
    implementado nesta onda (`RN-06`, divida #4): o parametro e a costura, nao a
    funcionalidade.
    """

    def guardar(self, arvore: Tree, dono: str) -> str:
        """Persiste a arvore do dono e devolve a referencia armazenada."""
        ...

    def obter(self, referencia: str, dono: str) -> Tree | None:
        """Arvore do dono para a referencia, ou `None` quando nao ha essa arvore."""
        ...


@dataclass(frozen=True)
class PessoaDaAnalise:
    """Retrato de UMA pessoa que a analise usou (`analysis_person`, `RF-04`).

    `completa` distingue a ficha inteira da mera identificacao. O resultado do
    nucleo traz a ficha pronta para a raiz e para o match — em
    `documentary.person_a` e `.person_b`, que sao `person_summary(...)` —, e dos
    nos intermediarios do caminho carrega apenas `id` e `nome`
    (`documentary.path.ids` e `.names`).

    Isso e **limite da saida atual do nucleo**, e nao escolha desta camada
    (`D-15`): expor o resto exigiria mexer na assinatura de retorno, que o `W016`
    congela e a paridade compara.
    """

    xref: str
    nome: str | None = None
    sexo: str | None = None
    nascimento: str | None = None
    local_nascimento: str | None = None
    falecimento: str | None = None
    completa: bool = False


@dataclass(frozen=True)
class KitDaAnalise:
    """Metadados de UM kit e o veredito **dele** (`match_kit`, `RF-05`, `RN-06`).

    O cM e o **deste** kit. Kits nunca se somam — a chave da evidencia e
    `(nome do CSV, kit)`, e dois kits do mesmo nome sao duas evidencias.
    """

    ordinal: int
    kit: str | None
    source: str | None
    total_cm: float | None
    segment_count: int | None
    largest_segment_cm: float | None
    status: str
    status_note: str | None = None


@dataclass(frozen=True)
class ConexaoDaAnalise:
    """UMA conexao: o documento, a genetica e o confronto (`match_result`).

    `caminho` carrega pares `(xref, papel)` na ordem do caminho documental, e nao
    so os identificadores: `match_path_node.role` e `NOT NULL` com dominio fechado
    (`ascendente`, `descendente`, `afinidade`), e o nucleo **nao** entrega o papel
    de cada no. Quem o deriva e a projecao, dividindo o caminho no ancestral comum
    — o adaptador **so escreve**, como a `D-15` exige.

    `afinidade` nunca aparece aqui: quem atribui esse estado e `path_search.py`, e
    nao o fluxo de analise de DNA (`state-machines.md#4`).
    """

    ordinal: int
    csv_name: str
    matched_name: str
    matched_person_xref: str
    comparison_status: str
    comparison_label: str
    comparison_detail: str
    documentary_status: str
    total_cm: float | None = None
    relationship_key: str | None = None
    relationship_label: str | None = None
    meioses: int | None = None
    mrca_xref: str | None = None
    comparison_method: str | None = None
    expected_low: float | None = None
    expected_high: float | None = None
    expected_average: float | None = None
    causes: tuple[str, ...] = ()
    observations: tuple[str, ...] = ()
    kits: tuple[KitDaAnalise, ...] = ()
    caminho: tuple[tuple[str, str], ...] = ()


@dataclass(frozen=True)
class DescartadoDaAnalise:
    """UMA conexao descartada, com o motivo (`skipped_match`, `RN-07`).

    O motivo e o **texto do nucleo**, e nao um codigo: o alvo tem `reason_code`
    como enum fechado, e fecha-lo aqui exigiria mapear texto em codigo — a
    inferencia a partir de mensagem de contrato que o projeto recusa desde a
    feature 006.
    """

    ordinal: int
    csv_name: str
    reason: str
    kit: str | None = None
    total_cm: float | None = None


@dataclass(frozen=True)
class AnaliseParaRegistrar:
    """A analise inteira, ja projetada — o que a porta recebe (`D-01`, `D-15`).

    E **dado plano**: nao carrega o resultado do nucleo, nao tem dicionario
    aninhado e nao expoe nome de campo de template. A projecao acontece no caso de
    uso, e o adaptador so escreve.
    """

    tree_ref: str
    match_file_ref: str
    root_name_input: str
    message: str
    pessoas: tuple[PessoaDaAnalise, ...]
    conexoes: tuple[ConexaoDaAnalise, ...]
    descartados: tuple[DescartadoDaAnalise, ...]
    root_person_xref: str | None = None
    accepted_count: int = 0
    skipped_count: int = 0


class RegistroDeAnalises(Protocol):
    """Persistencia historica do resultado da analise (`D-01`).

    Fica **depois** do processamento e **fora** da decisao: nenhum modulo de
    `src/core/` a conhece, e nenhum fluxo consulta o banco para decidir, completar
    ou corrigir um resultado (`RN-01`, `RN-12`). Ela responde "o que esta analise
    concluiu, e por que" — nao produz a resposta.
    """

    def registrar(self, analise: AnaliseParaRegistrar, dono: str) -> tuple[str | None, str | None]:
        """Grava a analise inteira e devolve `(referencia, aviso)`.

        `aviso is None` significa **gravado**, e `referencia` identifica a analise
        no banco.

        `aviso` preenchido significa **nao gravado**, e o texto explica por que. O
        aviso existe no lugar da excecao pela `RN-13`: falha de persistencia
        **nunca** interrompe a analise nem impede o resultado de ser exibido, e
        este texto e o unico sinal que o operador tem de que o historico nao foi
        registrado.

        A gravacao e **uma unica transacao** (`RF-10`): ou a analise inteira entra,
        ou nao entra nada. Analise pela metade e pior que analise ausente —
        deixaria o veredito de um par gravado com os dados de outro.

        `dono` e a identidade de quem enviou o dado, e entra **sem comportamento**
        (`RN-10`): vira coluna, e **nenhuma** consulta filtra por ele. Este metodo
        nao isola nada, e as dividas #3 e #4 seguem abertas.
        """
        ...


__all__ = [
    "ArmazenamentoDeArquivos",
    "CarregadorDeArvores",
    "RepositorioDeArvores",
    "RegistroDeAnalises",
    "EntradaArmazenada",
    "AnaliseParaRegistrar",
    "PessoaDaAnalise",
    "KitDaAnalise",
    "ConexaoDaAnalise",
    "DescartadoDaAnalise",
]

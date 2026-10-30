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
armazenado nem no caminho de nada, e nenhum arquivo e separado por dono. As dividas
#3 e #4 continuam abertas (`RN-06`).

**A partir da feature 051 o dono deixou de ser costura.** Ele e o `sub` do provedor
de identidade da conta autenticada, entra no caminho (`<pasta>/<dono>/`) e filtra
listagem, leitura e aposentadoria; a divida #4 (ausencia de isolamento) fecha nesta
entrega, e a #3 (corrida sobre o disco) continua aberta. Os docstrings de cada
metodo descrevem o comportamento novo, e a recusa por dono alheio e indistinguivel
de arquivo inexistente (`RN-06`).

**Esta frase deixou de valer na feature `011-escolher-arquivo-da-lista`.** Ate
entao ela dizia, com razao, que nenhum metodo novo havia sido criado em nenhuma
porta. A `011` criou o **primeiro**: `ArmazenamentoDeArquivos.listar`, que devolve
o retrato da pasta para a tela montar a lista de escolha. Ele tambem recebe `dono`,
e pela mesma razao do paragrafo acima — deixar o parametro de fora agora obrigaria
a reabrir esta assinatura e todos os chamadores depois, que e exatamente o custo
que a feature 007 pagou para nao ter.

A mesma feature criou o **segundo**: `aposentar`, que tira o arquivo da lista
movendo-o para `<pasta>/_aposentados/`. Ele **nao** contraria a `RN-07` — nada e
apagado, e o arquivo continua no disco —, e o `dono` entra com o mesmo alcance de
sempre: sem comportamento nenhum.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Protocol

if TYPE_CHECKING:
    # Import so para o checador de tipos. Em execucao a anotacao e uma string
    # (`from __future__ import annotations`), e a porta nao arrasta o parser para
    # dentro de quem so quer o contrato.
    from datetime import datetime

    from parsers.gedcom_parser import Tree

    from core.busca_de_nome import NomeParaBuscar
    from core.conta import ContaDeAcesso


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

        `dono` e a identidade de quem enviou o dado e **passa a isolar** (feature
        051): o arquivo e gravado em `<pasta>/<dono>/`, entao o mesmo conteudo
        enviado por dois donos sao **dois** arquivos. Dentro do dono, a chave
        continua vindo do conteudo. Ultimo parametro posicional e **sem valor
        padrao**, pela mesma forma do `RepositorioDeArvores`.
        """
        ...

    def resolver(self, referencia: str | None, dono: str) -> str | None:
        """Caminho do arquivo ja armazenado, ou `None`.

        `None` cobre as duas recusas, e cobre-as pelo mesmo motivo: nos dois casos
        nao existe arquivo a ler. Sao elas a **forma invalida** — o que impede um
        `gedcom_filename` manipulado de apontar para fora da pasta de upload — e o
        **arquivo ausente** no disco.

        `dono` entra como escopo (feature 051): a referencia e resolvida dentro de
        `<pasta>/<dono>/`, e a referencia de outro dono devolve `None`, como arquivo
        ausente. Quem resolve continua sendo a chave de conteudo, e a validacao de
        forma continua vindo antes de qualquer `os.path.exists`.
        """
        ...

    def listar(self, dono: str) -> list["EntradaArmazenada"]:
        """Retrato da pasta de upload: nome armazenado, bytes e data. **Nao abre arquivo.**

        A feature `011-escolher-arquivo-da-lista` (`D-01`) trouxe esta operacao para a
        **porta**, e nao para a rota. A razao e a fronteira que a feature 006 estabeleceu:
        `_arvore_do_formulario()` nao resolve caminho, e um `os.listdir` na rota desfaria
        isso — alem de tornar a listagem impossivel de testar sem pasta real.

        ## O que ela devolve, e o que ela NAO faz

        - devolve **tudo** o que e arquivo na pasta, sem julgar nome nem conteudo. Nao ha
          filtro aqui: separar as abas e marcar o item indisponivel e trabalho da funcao
          pura de `reporting/`, que decide pelo NOME (`D-08`, `RN-09`, `D-11`);
        - **nao abre arquivo nenhum**. Do diretorio ela le o nome; do arquivo, os atributos
          que o sistema de arquivos ja mantem — tamanho e data (`os.stat`). E o que evita
          reler a pasta inteira a cada renderizacao, e o que torna barato o agrupamento
          pela chave, que ja esta no nome;
        - **pasta ausente devolve lista vazia, e nao excecao** (`D-07`). Instalacao nova tem
          a pasta criada e vazia, e uma pasta que desapareca sob a aplicacao em execucao nao
          pode virar erro na tela de entrada. O `D-07` recusou explicitamente o
          `os.makedirs` aqui: criar diretorio dentro de uma leitura e efeito colateral
          escondido numa operacao que promete nao escrever;
        - **nao escreve nada**: listar e leitura pura (`RF-08`, `RN-06`).

        `dono` entra como escopo (feature 051): a listagem le `<pasta>/<dono>/`, e a
        pasta de outro dono nem e aberta. Quem decide se uma entrada pode ser usada
        continua sendo a forma do nome.
        """
        ...

    def aposentar(self, referencia: str | None, dono: str) -> bool:
        """Tira o arquivo da LISTA movendo-o para uma subpasta. **Nao apaga nada.**

        `True` significa que o arquivo saiu da pasta de upload. `False` significa que nada
        foi movido: referencia em forma de caminho, arquivo inexistente, ou ja haver um
        aposentado com o mesmo nome.

        ## Aposentar, e nao apagar (`RN-14`)

        A `RN-07` diz que a aplicacao **nunca apaga** arquivo enviado, e ela continua
        valendo: o que este metodo faz e MOVER para `<pasta>/_aposentados/`, onde o arquivo
        permanece inteiro, com o mesmo nome e o mesmo conteudo. O operador deixa de ve-lo na
        lista, e o dado nao some. Desfazer e mover de volta.

        ## Por que a lista nao precisa de filtro novo

        Quem le a pasta e `listar`, e ela ja ignora subdiretorio — so aceita `os.path.isfile`.
        Aposentar para dentro da propria pasta aproveita isso: o arquivo sai da tela sem que
        nenhuma regra de filtragem precise nascer, e sem uma lista de excecoes que alguem
        teria de manter.

        ## A referencia aqui e mais permissiva do que no `resolver`, e isso e deliberado

        A defesa contra escape continua existindo, com outro criterio
        (`utils.validate.referencia_de_arquivo_da_pasta`): qualquer NOME simples, e nao
        apenas a forma canonica com chave. O motivo e medido — os arquivos **sem chave** da
        pasta real sao os inalcancaveis, e sao exatamente os que o operador quer tirar da
        lista; exigir a chave aqui os tornaria impossiveis de aposentar. O `resolver` **nao**
        afrouxa: ler por referencia continua exigindo a forma da chave.

        `dono` entra como escopo (feature 051): a origem e a pasta de aposentados
        sao as do dono, e a referencia de outro dono devolve `False`, como arquivo
        ausente.
        """
        ...


@dataclass(frozen=True)
class EntradaArmazenada:
    """Um arquivo da pasta de upload, como a LISTAGEM o ve (`D-01`).

    Nao e o arquivo: e o retrato do diretorio. Os tres campos sao tudo o que a leitura de
    uma entrada produz, e nenhum deles exige abrir o conteudo.

    `nome` e o **nome armazenado** (`<16 hex>__<nome visivel>`), e nao o visivel: e ele que
    o formulario devolve na requisicao seguinte, e e ele que o resolvedor aceita. Derivar o
    rotulo de tela e trabalho da funcao pura de `reporting/`, a partir deste campo.

    `modificado_em` e o instante do sistema de arquivos, em segundos desde a epoch, na mesma
    unidade de `os.path.getmtime`. A lista e ordenada por ele, decrescente, porque o nome
    exibido **nao e unico** — medido, ha tres arquivos chamados
    `Arvore_Unificada_Oficial_V1_2.ged` na pasta real — e e a data que distingue um do outro.
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
        segue satisfeita. O isolamento e feito pelo adaptador de armazenamento, que
        recebe este mesmo `dono` (feature 051).
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
class CandidatoDoDescarte:
    """UM candidato que a arvore oferecia para um nome descartado (feature 034).

    Existe para que a tela possa dizer a quem o nucleo quase ligou o nome: sem isso,
    o descarte e' um beco sem saida. `nota` e `prenome` sao as duas medidas que o
    nucleo usa na decisao, e vao como numero — nao como texto de motivo.
    """

    nome: str
    prenome: float | None = None
    nota: float | None = None
    nascimento: str | None = None
    compativel: bool = False


@dataclass(frozen=True)
class DescartadoDaAnalise:
    """UMA conexao descartada, com o motivo (`skipped_match`, `RN-07`).

    O motivo e o **texto do nucleo**, e nao um codigo: o alvo tem `reason_code`
    como enum fechado, e fecha-lo aqui exigiria mapear texto em codigo — a
    inferencia a partir de mensagem de contrato que o projeto recusa desde a
    feature 006.

    Desde a feature 038 o texto e' **humano** (o que o operador le) e a causa viaja em
    `reason_code`, ao lado, sem substituir o texto. `detail` carrega os numeros medidos
    (`prenome`, `nota`, `sobrenomes em comum`, `grafia`) para quem precisa conferir o
    calculo. Os tres campos nascem vazios quando a recusa nao vem do bloco de semelhanca.
    """

    ordinal: int
    csv_name: str
    reason: str
    kit: str | None = None
    total_cm: float | None = None
    candidatos: tuple[CandidatoDoDescarte, ...] = ()
    reason_code: str = ""
    detail: str = ""


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

        `dono` e a identidade da conta que gerou a analise, e vira a coluna
        `owner_id`: a partir da feature 051 ele e o `sub` do provedor, e a leitura
        passa a ser escopada por ele (`RN-11`).
        """
        ...

    def adotar(self, dono_anterior: str, dono_novo: str) -> int:
        """Transfere ao dono novo as analises gravadas sob um dono anterior.

        Existe para a `RN-15`: os dados que antecedem a identidade tem um destino
        declarado, e o historico com `owner_id = 'unico'` passa a pertencer a conta
        inicial. **Idempotente por construcao** — o `UPDATE` e condicionado ao dono
        anterior, e a segunda chamada devolve `0`.

        Devolve quantas linhas mudaram. Falha de driver ou de banco devolve `0` e
        nao levanta: a adocao e beneficio e nunca pode impedir o login.
        """
        ...


class FonteDeNomes(Protocol):
    """Uma fonte de nomes para a busca (feature 052, `D-02`).

    A porta existe para que "arvore e relatorio" nao vire `if` de formato no caso de
    uso: uma terceira fonte e um adaptador novo, e o nucleo nao muda.

    ## O que a fonte declara

    - `identidade`: rotulo curto e estavel (`arvore`, `relatorio`), usado como chave;
    - `rotulo`: o texto que o operador le na secao;
    - `normalizar`: a AUTORIDADE de normalizacao **da fonte**. E com ela que o termo e
      normalizado antes de comparar. Se a busca usasse um normalizador unico, ela
      discordaria do dossie de homonimos (que normaliza com `core.homonimos.normalizar`)
      ou do `matching` (que usa `utils.name_keys.norm_name`) — `RN-06`;
    - `nomes`: os candidatos ja normalizados, com tokens prontos;
    - `fichas`: a ficha de exibicao dos que sobraram no ranking, pedida **so para eles** —
      montar ficha de 35 mil pessoas para mostrar 50 seria pagar o pior custo.

    ## `None` nao e lista vazia

    `nomes` devolve `None` quando a referencia **nao resolve** (arquivo inexistente ou de
    outro dono). Quem chama traduz isso no `404` com o literal de inexistencia (`RN-06` da
    feature 051). Tupla vazia significa "resolveu, e nao ha nome nenhum".
    """

    identidade: str
    rotulo: str

    def normalizar(self, texto: str) -> str:
        """A normalizacao de nome que esta fonte ja usa."""
        ...

    def nomes(self, referencia: str | None, dono: str) -> tuple[tuple["NomeParaBuscar", ...] | None, str | None]:
        """`(candidatos, aviso)`. `candidatos is None` = a referencia nao resolve.

        `aviso` preenchido significa "a fonte existe mas nao pode ser lida" — o relatorio
        ilegivel, por exemplo. A secao continua existindo, com o aviso, e a fonte irma nao
        e afetada (`RF-13`).
        """
        ...

    def fichas(self, referencia: str | None, dono: str,
               identificadores: tuple[str, ...]) -> dict[str, dict[str, object]]:
        """Ficha de exibicao por identificador. Fonte sem ficha devolve `{}`."""
        ...


class RepositorioDeContas(Protocol):
    """Persistencia das contas locais (feature 053, `D-05`).

    A porta existe para que o **arquivo de hoje** e o **Postgres de amanha** sejam
    trocados sem tocar no dominio, e para que o caso de uso pergunte "qual e a conta
    deste e-mail", nunca "como o JSON e escrito".

    Todos os metodos recebem e devolvem `ContaDeAcesso`, nunca dicionario: o
    formato de armazenamento e assunto do adaptador (`RNF-01`).
    """

    def criar(self, conta: "ContaDeAcesso") -> "ContaDeAcesso":
        """Grava a conta nova.

        Levanta `ContaDuplicada` quando o e-mail normalizado ou o `google_sub` ja
        pertencem a outra conta — a unicidade e invariante do dominio, e o adaptador
        e quem a faz valer contra o armazenamento.
        """
        ...

    def por_email(self, email_normalizado: str) -> "ContaDeAcesso | None":
        """A conta do e-mail normalizado, ou `None`."""
        ...

    def por_sub(self, sub: str) -> "ContaDeAcesso | None":
        """A conta do dono, ou `None`."""
        ...

    def por_google_sub(self, google_sub: str) -> "ContaDeAcesso | None":
        """A conta que ja anexou esta identidade Google, ou `None`."""
        ...

    def salvar(self, conta: "ContaDeAcesso") -> None:
        """Grava a conta inteira, preservando os tokens vigentes."""
        ...

    def anexar_token(self, sub: str, tipo: str, hash_token: str,
                     expira_em: "datetime") -> None:
        """Registra o token vigente de um tipo e invalida o anterior da mesma conta."""
        ...

    def consumir_token(self, hash_token: str, agora: "datetime") -> tuple[str, str] | None:
        """Consome o token e devolve `(sub, tipo)`, ou `None` se nao vale.

        `None` cobre ausente, ja usado e expirado — as tres recusas sao
        indistinguiveis para quem chama (`RN-09`). O token e removido mesmo quando
        expirado, para nao sobrar lixo no armazenamento.
        """
        ...

    def token_vigente(self, hash_token: str, agora: "datetime") -> tuple[str, str] | None:
        """Consulta **sem consumir**: `(sub, tipo)` se o token ainda vale.

        Existe para a tela de nova senha: ela precisa decidir entre mostrar o
        formulario e a mensagem de link vencido sem queimar o token de quem apenas
        abriu o link.
        """
        ...


class TransporteDeEmail(Protocol):
    """Saida de e-mail da confirmacao e da recuperacao (feature 053, `D-05`).

    `configurado` e a pergunta que a aplicacao faz **antes** de prometer envio: sem
    transporte, cadastro e recuperacao avisam que o envio nao esta configurado, em
    vez de criar conta que nunca confirma (`RN-18`).
    """

    configurado: bool

    def enviar(self, destino: str, assunto: str, corpo: str) -> None:
        """Envia uma mensagem de texto simples.

        Levanta `EnvioIndisponivel` quando o transporte existe mas falhou, e
        `EnvioNaoConfigurado` quando nao ha transporte. A aplicacao traduz as duas
        em aviso, nunca em 500.
        """
        ...


class Relogio(Protocol):
    """O instante corrente. Porta para o teste de expiracao ser deterministico."""

    def agora(self) -> "datetime":
        """Agora, com fuso (UTC)."""
        ...


__all__: list[str] = [
    "ArmazenamentoDeArquivos",
    "CarregadorDeArvores",
    "RepositorioDeArvores",
    "RegistroDeAnalises",
    "FonteDeNomes",
    "RepositorioDeContas",
    "TransporteDeEmail",
    "Relogio",
    "EntradaArmazenada",
    "AnaliseParaRegistrar",
    "PessoaDaAnalise",
    "KitDaAnalise",
    "ConexaoDaAnalise",
    "DescartadoDaAnalise",
    "CandidatoDoDescarte",
]

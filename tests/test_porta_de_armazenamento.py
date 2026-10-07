"""Testes da porta de armazenamento (acoes T027, T028 e T010).

Tres blocos, e cada um mede algo que nenhum outro teste da suite mede.

- `TestValidacaoAntesDaGravacao` (`T027`) mede a ORDEM da regra do `RF-10`: a
  validacao de conteudo acontece ANTES de qualquer escrita, e uma recusa nao
  deixa residuo na pasta. A prova so e possivel fora do HTTP. Pelo caso de uso,
  com a pasta de upload apontada para um diretorio vazio e conhecido, da para
  afirmar `os.listdir(pasta) == []` — "nenhum residuo" —, e nao apenas "a tela nao
  mostrou sucesso". O bloco tambem prende o TEXTO da excecao: o dominio carrega o
  MOTIVO puro, e a moldura de tela (`Arquivo nao reconhecido como GEDCOM: ...`) e
  da tabela de traducao do adaptador de entrada, nunca do nucleo (`RF-03`,
  `core/erros.py`). Se a moldura voltar para dentro da excecao, o literal de tela
  passa a viajar pelo dominio e o adaptador deixa de ser o unico que o redige.

- `TestContratoDoRepositorio` (`T028`) prova, por introspeccao, que
  `RepositorioDeArvores` exige o dono em todo metodo e que ele continua SEM
  implementacao. A prova e estrutural de proposito (`D-03`): enquanto o contrato
  nao tem consumidor, "recusado pelo proprio contrato" e tudo o que existe para
  medir, e um teste de comportamento aqui so poderia passar se alguem tivesse
  escrito a implementacao que a decisao proibe.

- `TestContratoDoArmazenamento` (`T010`, feature `007-dono-no-port-e-baseline`)
  prova, tambem por introspeccao, a **forma** do contrato de armazenamento: o dono
  existe nos dois metodos da porta e no metodo do carregador, nao tem valor padrao,
  e a chamada sem ele e recusada pelo proprio contrato. O bloco mede ainda o que o
  comportamento **nao** distingue — que dois donos com o mesmo conteudo chegam a UM
  arquivo, que o arquivo ja gravado nao e reescrito e que a resolucao nao e
  filtrada por dono. Ver o docstring da classe para o que cada prova cobre.

## Por que este arquivo CONTINUA usando `pasta_temporaria`

**Este paragrafo foi corrigido em 2026-10-07, e a versao anterior dele era falsa.**
Ele dizia que `tmp_path` nao funciona nesta maquina e que era por isso que o
arquivo usava `pasta_temporaria`. A feature `007-dono-no-port-e-baseline` declarou
o fixture `tmp_path` em `tests/conftest.py` — **delegando a `pasta_temporaria`** —,
e a partir dela `tmp_path` funciona: os 15 testes de `tests/test_upload_seguranca.py`
passaram a executar por causa disso.

O que continua verdadeiro, e o motivo de o arquivo nao ter sido reescrito:

- `pasta_temporaria` e `tmp_path` sao hoje **a mesma politica**. O pytest cacheia a
  instancia do fixture por teste, entao os dois nomes apontam para o MESMO
  diretorio, e usa-los ou nao e escolha de leitura, nao de comportamento.
- As assercoes deste arquivo sao **entregues** e continuam valendo ao caractere.
  Trocar o nome do fixture seria churn sem ganho — e a `D-10` da 007 decidiu
  corrigir o **comentario**, nao o codigo.

O import de `src/` fica no cabecalho padrao logo abaixo.
"""
import os
import sys

PROJETO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, PROJETO)
sys.path.insert(0, os.path.join(PROJETO, "src"))

import inspect

import pytest

from application import nomes_de_exibicao
from application.upload_gedcom import upload_gedcom
from core.erros import GedcomNaoSuportado
from ports import adaptadores
from ports import ArmazenamentoDeArquivos, CarregadorDeArvores, RepositorioDeArvores
from ports.adaptadores import ArmazenamentoEmDisco, CarregadorDeArvoresGedcom


# GEDCOM minimo, porem valido de verdade: comeca com `0 HEAD` e termina com
# `0 TRLR`, que e o que `utils/validate.py` exige e o que o ged4py precisa para
# parsear. As duas pessoas entram em ordem ALFABETICA INVERSA (Maria antes de
# Joao) de proposito: e o que torna a assercao de ORDENACAO dos nomes capaz de
# falhar. Com a ordem ja correta no arquivo, `sorted` seria indistinguivel de
# "ordem do arquivo" e o teste passaria sem medir nada.
GEDCOM_VALIDO = (
    "0 HEAD\n"
    "1 SOUR TESTE\n"
    "1 GEDC\n"
    "2 VERS 5.5.1\n"
    "2 FORM LINEAGE-LINKED\n"
    "0 @I1@ INDI\n"
    "1 NAME Maria /Souza/\n"
    "1 SEX F\n"
    "0 @I2@ INDI\n"
    "1 NAME Joao /Silva/\n"
    "1 SEX M\n"
    "0 TRLR\n"
)

# Ordem que `application.nomes_de_exibicao` tem de devolver: `sorted` sobre
# `get_name`. "Joao Silva" antes de "Maria Souza".
NOMES_ESPERADOS = ["Joao Silva", "Maria Souza"]

DONO = "dono"


def _portas(pasta: str):
    """Monta o par de adaptadores reais sobre a pasta recebida.

    Os adaptadores sao montados AQUI, e nao dentro do caso de uso: e a `RF-02` —
    o caso de uso recebe as portas por parametro e nunca instancia
    `ArmazenamentoEmDisco` nem `CarregadorDeArvoresGedcom`. Montar pelo mesmo
    caminho que `src/app.py` monta (`_ARMAZENAMENTO` e `_CARREGADOR`) e o que faz
    este teste medir a fiacao real, e nao uma variante so de teste.
    """
    armazenamento = ArmazenamentoEmDisco(pasta)
    return armazenamento, CarregadorDeArvoresGedcom(armazenamento)


class TestValidacaoAntesDaGravacao:
    """T027 — a recusa acontece antes da escrita e nao deixa residuo na pasta."""

    @pytest.mark.parametrize(
        ("conteudo", "motivo_esperado"),
        [
            (b"", "arquivo vazio"),
            (b"\x00\x01", "conteudo binario"),
        ],
        ids=["vazio", "binario"],
    )
    def test_conteudo_invalido_e_recusado_sem_residuo(
            self, pasta_temporaria, conteudo, motivo_esperado):
        """A pasta continua VAZIA, e o motivo e o unico texto da excecao.

        As duas assercoes prendem coisas diferentes, e as duas sao a `RF-10`:

        - `os.listdir(pasta) == []` e a prova de que a validacao veio ANTES da
          escrita. Um `guardar` que gravasse primeiro e validasse depois (ou que
          abrisse o arquivo e so entao recusasse) deixaria um residuo recuperavel
          pelo `gedcom_filename` da requisicao seguinte — exatamente o defeito do
          BUG-20260929-QMLY. O `== []` e literal de proposito: `not any(...)`
          passaria com um diretorio inexistente, e aqui a pasta existe.
        - `str(erro) == motivo_esperado` prende a fronteira do `RF-03`. O texto e
          o motivo do `utils/validate.py` e nada mais; a moldura
          (`Arquivo nao reconhecido como GEDCOM: ...`) e da traducao do adaptador
          de entrada. Se alguem passar a levantar a excecao ja com a moldura, a
          tela mostraria a moldura DUAS vezes, e este teste falha antes disso.

        Os dois conteudos cobrem os dois primeiros ramos de
        `validar_conteudo_gedcom` (`not conteudo` e o byte nulo): sao os que
        recusam sem depender do cabecalho, entao a recusa nao pode ser creditada
        ao texto do GEDCOM.
        """
        armazenamento, carregador = _portas(pasta_temporaria)

        with pytest.raises(GedcomNaoSuportado) as capturado:
            upload_gedcom(conteudo, "x.ged", DONO, armazenamento, carregador)

        assert str(capturado.value) == motivo_esperado, (
            "a excecao de dominio tem de carregar o motivo PURO do "
            "utils/validate.py; moldura de tela dentro dela e vazamento do "
            "adaptador de entrada para o nucleo (RF-03, core/erros.py)"
        )
        assert os.listdir(pasta_temporaria) == [], (
            "conteudo recusado deixou residuo na pasta de upload: a validacao "
            "aconteceu DEPOIS da gravacao (RF-10)"
        )

    def test_motivo_do_dominio_nao_traz_moldura_de_tela(self, pasta_temporaria):
        """O motivo nao contem o prefixo que o adaptador de entrada redige.

        `str(erro) == "arquivo vazio"` ja e medido acima; este teste mede a
        negacao explicita, porque a regressao que ele impede e a de alguem
        "melhorar" a mensagem do dominio para ficar pronta para a tela. A moldura
        do upload de GEDCOM e montada pela tabela de traducao
        (`application/traducao.py`), e e ela que o operador ve.
        """
        armazenamento, carregador = _portas(pasta_temporaria)

        with pytest.raises(GedcomNaoSuportado) as capturado:
            upload_gedcom(b"", "x.ged", DONO, armazenamento, carregador)

        texto = str(capturado.value)
        assert "Arquivo não reconhecido como GEDCOM:" not in texto, (
            "a moldura de tela de `application/traducao.py` (linha 86) vazou "
            "para dentro da excecao de dominio, e o adaptador de entrada "
            "passaria a exibir a moldura DUAS vezes"
        )
        assert texto == "arquivo vazio"

    def test_gedcom_valido_grava_e_devolve_referencia(self, pasta_temporaria):
        """O caminho positivo: o arquivo APARECE na pasta e a referencia o nomeia.

        `os.listdir(pasta) == [resultado.referencia]` e a assercao que une as duas
        metades do contrato do `ArmazenamentoDeArquivos`: a `referencia` devolvida
        e o NOME do arquivo que esta em disco, e nao uma forma remontavel por quem
        chama. E o que a `RF-09` separa do caminho: o formulario devolve a
        referencia na requisicao seguinte, e a mesma referencia tem de resolver de
        volta para o arquivo gravado.

        `nome_exibido` e o nome ORIGINAL, preservado como metadado legivel — o
        nome do cliente deixou de decidir o caminho no BUG-20260929-QMLY, mas
        continua sendo o rotulo que o operador reconhece.
        """
        armazenamento, carregador = _portas(pasta_temporaria)

        resultado = upload_gedcom(
            GEDCOM_VALIDO.encode("utf-8"), "arvore.ged", DONO,
            armazenamento, carregador)

        assert os.listdir(pasta_temporaria) == [resultado.referencia], (
            "o arquivo gravado e a referencia devolvida tem de ser o mesmo nome"
        )
        assert os.path.isfile(os.path.join(pasta_temporaria, resultado.referencia))
        assert resultado.referencia.endswith("__arvore.ged"), (
            "a chave do servidor vem primeiro e o nome visivel depois"
        )
        assert resultado.nome_exibido == "arvore.ged"
        assert resultado.mensagem == "Arquivo 'arvore.ged' carregado!"

    def test_nomes_de_exibicao_vem_ordenados(self, pasta_temporaria):
        """A lista do campo de sugestao sai ORDENADA, como contrato de tela.

        A ordem e `sorted` sobre `get_name`, e nao a ordem do arquivo — por isso o
        GEDCOM desta fixture lista Maria antes de Joao. Este teste roda o caso de
        uso de ponta a ponta (escrita, releitura pelo parser e derivacao dos nomes)
        porque a lista so existe depois do parse: e o unico ponto em que a
        derivacao de `application.nomes_de_exibicao` e exercitada pela porta.
        """
        armazenamento, carregador = _portas(pasta_temporaria)

        resultado = upload_gedcom(
            GEDCOM_VALIDO.encode("utf-8"), "arvore.ged", DONO,
            armazenamento, carregador)

        assert resultado.nomes == NOMES_ESPERADOS
        assert resultado.nomes == sorted(resultado.nomes)


class TestContratoDoRepositorio:
    """T028 — o contrato exige o dono, e nao existe implementacao nesta onda.

    A prova e ESTRUTURAL, e isso e a `D-03` levada a serio. O
    `RepositorioDeArvores` foi declarado sem implementacao e sem consumidor de
    proposito, como a costura tipada que a Onda 3 preenche. Um teste de
    comportamento aqui nao teria o que medir: para escreve-lo seria preciso um
    adaptador — e um adaptador EM MEMORIA reintroduziria, com outro nome, o estado
    global de processo que a feature 005 removeu. O que da para medir sem violar a
    decisao e a forma do contrato: o parametro existe, e obrigatorio, e nenhuma
    classe de `ports/adaptadores.py` o implementa.
    """

    @pytest.mark.parametrize(
        ("nome_metodo", "demais_argumentos"),
        [
            ("guardar", ("alguma_arvore", DONO)),
            ("obter", ("alguma_referencia", DONO)),
        ],
        ids=["guardar", "obter"],
    )
    def test_dono_e_obrigatorio_e_chamada_sem_ele_e_recusada(
            self, nome_metodo, demais_argumentos):
        """`dono` sem valor padrao, e o proprio contrato recusa a chamada sem ele.

        Duas provas, e a segunda e a que interessa:

        - `parametro.default is inspect.Parameter.empty` fixa que o dono NAO tem
          padrao. Um `dono: str = "unico"` seria a forma mais barata de adiar a
          costura e a mais cara de desfazer depois, porque todo chamador passaria
          a compilar sem o argumento e a Onda 3 nao teria onde ancorar.
        - `bind` sem o dono levanta `TypeError`: e assim que "recusado pelo
          proprio contrato" fica verificavel sem implementacao nenhuma. `bind` e
          a mesma checagem que a linguagem faz na chamada, so que sem executar
          corpo — e e por isso que ele serve aqui, onde nao ha corpo para
          executar.

        **`self` conta na assinatura.** `inspect.signature` sobre o atributo de
        classe de um `Protocol` devolve a funcao crua, entao a assinatura de
        `guardar` e `(self, arvore, dono)` e a de `obter` e
        `(self, referencia, dono)`. Por isso o `bind` recebe o objeto falso MAIS
        os demais argumentos, na ordem declarada: tirar o ULTIMO deles — o dono —
        e o que precisa levantar `TypeError`. Com `self` fora da conta, o `bind`
        acusaria a falta do dono mesmo quando ele tivesse padrao, e o teste
        passaria a medir a forma da chamada em vez da obrigatoriedade do dono.
        """
        assinatura = inspect.signature(getattr(RepositorioDeArvores, nome_metodo))

        assert "dono" in assinatura.parameters, (
            "RF-08: o dono tem de estar na assinatura ANTES de a Onda 3 chegar"
        )
        parametro = assinatura.parameters["dono"]
        assert parametro.default is inspect.Parameter.empty, (
            "dono com valor padrao deixa a chamada sem dono passar, e o custo de "
            "reabrir toda assinatura de porta na Onda 3 e o que a D-03 evita"
        )

        objeto_falso = object()
        # Com o dono: a chamada e aceita pela forma do contrato.
        assinatura.bind(objeto_falso, *demais_argumentos)
        # Sem o dono (o ultimo argumento declarado): recusada pelo contrato.
        with pytest.raises(TypeError):
            assinatura.bind(objeto_falso, *demais_argumentos[:-1])

    def test_adaptadores_nao_implementam_o_repositorio(self):
        """Nenhuma classe publica do modulo de adaptadores e o repositorio.

        Duas metades:

        - `adaptadores.__all__` e EXATAMENTE `["ArmazenamentoEmDisco",
          "CarregadorDeArvoresGedcom"]`. A lista literal prende a superficie
          publica do modulo: acrescentar um terceiro adaptador — o candidato
          obvio sendo o repositorio em memoria que a `D-03` descarta — quebra
          este teste e obriga a decisao a ser reaberta em vez de contornada.
        - Nenhuma classe DEFINIDA no modulo (o filtro por `__module__` exclui
          nome importado) implementa o par: ter `guardar` E `obter` com `dono`
          obrigatorio nos dois. Procurar o par, e nao a heranca, e deliberado:
          `RepositorioDeArvores` e um `Protocol`, e um `Protocol` nao aparece em
          `__mro__` de quem o satisfaz estruturalmente. A heranca responderia
          "nenhuma" mesmo se a implementacao existisse — medindo nada.
        """
        assert adaptadores.__all__ == [
            "ArmazenamentoEmDisco", "CarregadorDeArvoresGedcom",
        ], "a superficie publica dos adaptadores mudou: reabra a D-03 antes"

        classes_do_modulo = [
            classe for _, classe in inspect.getmembers(adaptadores, inspect.isclass)
            if classe.__module__ == adaptadores.__name__
        ]
        assert classes_do_modulo, (
            "guarda contra teste vacuamente verde: sem classes, a varredura "
            "abaixo nao mede nada"
        )

        implementam = [
            classe.__name__ for classe in classes_do_modulo
            if self._tem_o_par_do_repositorio(classe)
        ]
        assert implementam == [], (
            "estas classes implementam o RepositorioDeArvores: "
            f"{implementam}. A D-03 declara o contrato SEM implementacao nesta "
            "onda; um adaptador em memoria reintroduziria, com outro nome, o "
            "estado global de processo que a feature 005 removeu"
        )

    @staticmethod
    def _tem_o_par_do_repositorio(classe) -> bool:
        """A classe define `guardar` e `obter`, os dois exigindo `dono`?"""
        for nome_metodo in ("guardar", "obter"):
            metodo = getattr(classe, nome_metodo, None)
            if metodo is None:
                return False
            try:
                assinatura = inspect.signature(metodo)
            except (TypeError, ValueError):
                # Atributo que nao e chamavel inspecionavel (dado de classe com o
                # mesmo nome, por exemplo) nao conta como implementacao.
                return False
            if "dono" not in assinatura.parameters:
                return False
            if assinatura.parameters["dono"].default is not inspect.Parameter.empty:
                return False
        return True


class TestContratoDoArmazenamento:
    """T010 — o dono entra no contrato do armazenamento, e NAO no comportamento.

    Tres provas, e cada uma responde a uma clausula que nenhuma outra mede:

    - a **forma**: o dono existe nos dois metodos da porta de armazenamento e no
      metodo do carregador, nao tem valor padrao, e a chamada sem ele e recusada
      pelo proprio contrato — `RF-01`, no mesmo padrao estrutural do `T028` acima;
    - a **ausencia de superficie de compatibilidade**: nao ha assinatura variavel
      capaz de absorver a chamada antiga, o adaptador declara exatamente a mesma
      forma do `Protocol`, e a chamada como ela era antes do `T005` nao compila —
      `RF-12`;
    - o **comportamento preservado**: dois donos diferentes com o mesmo conteudo
      chegam a UM arquivo, o arquivo ja gravado nao e reescrito, e a resolucao nao
      e filtrada por dono — `RF-02`, que e a `RN-02` levada a serio.
    """

    @pytest.mark.parametrize(
        ("classe", "nome_metodo", "demais_argumentos"),
        [
            (ArmazenamentoDeArquivos, "guardar", (b"conteudo", "a.ged", "gedcom", DONO)),
            (ArmazenamentoDeArquivos, "resolver", ("referencia", DONO)),
            (CarregadorDeArvores, "carregar", ("referencia", DONO)),
        ],
        ids=["guardar", "resolver", "carregar"],
    )
    def test_dono_e_obrigatorio_e_sem_valor_padrao(
            self, classe, nome_metodo, demais_argumentos):
        """`dono` na assinatura, sem padrao, por ULTIMO, e a chamada sem ele recusada.

        Os `demais_argumentos` incluem um valor para o dono de proposito: e assim
        que `demais_argumentos[:-1]` deixa faltando **so** o dono. Sem isso, o
        `bind` acusaria a falta de outro parametro e o teste passaria medindo a
        aridade em vez da obrigatoriedade do dono — o mesmo cuidado que o `T028`
        documenta.

        `self` CONTA na assinatura: `inspect.signature` sobre o atributo de classe
        de um `Protocol` devolve a funcao crua.
        """
        assinatura = inspect.signature(getattr(classe, nome_metodo))

        assert "dono" in assinatura.parameters, (
            f"{classe.__name__}.{nome_metodo} perdeu o dono: a Onda 3 precisaria "
            "reabrir a assinatura e todos os chamadores (RF-01)"
        )
        assert assinatura.parameters["dono"].default is inspect.Parameter.empty, (
            f"{classe.__name__}.{nome_metodo} deu valor padrao ao dono: a chamada "
            "sem identidade volta a compilar e a costura perde onde ancorar "
            "(RF-01, RF-12)"
        )
        assert list(assinatura.parameters)[-1] == "dono", (
            f"{classe.__name__}.{nome_metodo} deixou de declarar o dono por "
            "ULTIMO. A simetria com `RepositorioDeArvores` — onde o dono tambem e "
            "o ultimo — e o que faz a leitura da Onda 3 nao consultar porta a "
            "porta (RNF de Manutenibilidade)"
        )

        objeto_falso = object()
        assinatura.bind(objeto_falso, *demais_argumentos)
        with pytest.raises(TypeError):
            assinatura.bind(objeto_falso, *demais_argumentos[:-1])

    @pytest.mark.parametrize(
        ("classe", "nome_metodo", "chamada_sem_dono"),
        [
            (ArmazenamentoDeArquivos, "guardar", (b"conteudo", "a.ged", "gedcom")),
            (ArmazenamentoDeArquivos, "resolver", ("referencia",)),
            (CarregadorDeArvores, "carregar", ("referencia",)),
        ],
        ids=["guardar", "resolver", "carregar"],
    )
    def test_nao_existe_forma_alternativa_de_chamada(
            self, classe, nome_metodo, chamada_sem_dono):
        """Nenhuma superficie de compatibilidade: a chamada antiga nao compila.

        A `RF-12` proibe duas coisas, e as duas sao medidas:

        - **assinatura variavel** (`*args`/`**kwargs`). Um `**extras` absorveria a
          chamada sem o dono e a obrigatoriedade viraria decorativa — o parametro
          continuaria "obrigatorio" no papel e opcional na pratica.
        - **a chamada antiga aceita.** `bind` monta a chamada EXATAMENTE como ela
          era antes do `T005`, sem o dono, e o contrato tem de recusa-la.
        """
        assinatura = inspect.signature(getattr(classe, nome_metodo))
        for parametro in assinatura.parameters.values():
            assert parametro.kind not in (
                inspect.Parameter.VAR_POSITIONAL,
                inspect.Parameter.VAR_KEYWORD,
            ), (
                f"{classe.__name__}.{nome_metodo} declara `{parametro.name}` "
                f"({parametro.kind.name}): uma assinatura variavel absorve a "
                "chamada antiga sem o dono e a RF-12 deixa de valer"
            )

        with pytest.raises(TypeError):
            assinatura.bind(object(), *chamada_sem_dono)

    @pytest.mark.parametrize(
        ("contrato", "adaptador", "nome_metodo"),
        [
            (ArmazenamentoDeArquivos, ArmazenamentoEmDisco, "guardar"),
            (ArmazenamentoDeArquivos, ArmazenamentoEmDisco, "resolver"),
            (CarregadorDeArvores, CarregadorDeArvoresGedcom, "carregar"),
        ],
        ids=["guardar", "resolver", "carregar"],
    )
    def test_adaptador_declara_a_mesma_forma_do_contrato(
            self, contrato, adaptador, nome_metodo):
        """O adaptador nao pode divergir do `Protocol` que ele satisfaz.

        Divergir aqui e o defeito mais silencioso desta feature. `Protocol` nao
        aparece em `__mro__` de quem o satisfaz, e a conformidade estrutural nao e
        conferida em execucao: um adaptador sem o dono so quebraria no primeiro
        chamador que passasse a identidade de verdade — na Onda 3, depois de a
        costura ter sido declarada pronta.
        """
        parametros_do_contrato = list(
            inspect.signature(getattr(contrato, nome_metodo)).parameters)
        parametros_do_adaptador = list(
            inspect.signature(getattr(adaptador, nome_metodo)).parameters)

        assert parametros_do_adaptador == parametros_do_contrato, (
            f"{adaptador.__name__}.{nome_metodo} declara "
            f"{parametros_do_adaptador}, e {contrato.__name__}.{nome_metodo} "
            f"declara {parametros_do_contrato}. Os nomes e a ordem fazem parte do "
            "contrato: a chamada por palavra-chave e a simetria entre as portas "
            "dependem deles"
        )

    def test_dois_donos_um_arquivo_so(self, pasta_temporaria):
        """`RF-02`: o dono NAO vira escopo de armazenamento.

        A segunda metade e a que interessa, e ela existe para separar duas coisas
        que devolveriam o mesmo resultado visivel: **reusar** o caminho e
        **regravar por cima**. Marcar o arquivo com conteudo arbitrario depois da
        primeira gravacao e conferir que a marca sobrevive e o que distingue as
        duas — se o adaptador regravasse, a referencia devolvida seria identica e a
        regra "conteudo ja armazenado nao e regravado" estaria quebrada sem que
        nenhuma assercao de caminho percebesse.
        """
        armazenamento, _ = _portas(pasta_temporaria)
        conteudo = GEDCOM_VALIDO.encode("utf-8")

        caminho_a, motivo_a = armazenamento.guardar(
            conteudo, "arvore.ged", "gedcom", "dono-a")
        assert motivo_a is None

        with open(caminho_a, "wb") as destino:
            destino.write(b"MARCA")

        caminho_b, motivo_b = armazenamento.guardar(
            conteudo, "arvore.ged", "gedcom", "dono-b")
        assert motivo_b is None

        assert caminho_a == caminho_b, (
            "dois donos com o mesmo conteudo passaram a produzir referencias "
            "diferentes: o dono entrou na chave ou no caminho, e isso e mudanca de "
            "comportamento observavel (RN-02)"
        )
        assert os.listdir(pasta_temporaria) == [os.path.basename(caminho_a)], (
            f"a pasta ficou com {os.listdir(pasta_temporaria)}: o mesmo conteudo "
            "passou a gerar mais de um arquivo"
        )
        with open(caminho_a, "rb") as origem:
            assert origem.read() == b"MARCA", (
                "o arquivo ja gravado foi REESCRITO por um envio com outro dono: a "
                "regra e reusar a chave de conteudo, nao regravar (RF-02)"
            )

    def test_resolucao_nao_e_filtrada_por_dono(self, pasta_temporaria):
        """`RF-02`: o dono tambem nao filtra o `resolver`, em nenhum sentido.

        As tres assercoes cobrem os tres casos que um filtro por dono mudaria:
        o dono que gravou, um dono **diferente**, e uma referencia com forma
        invalida. A ultima importa porque prova que o dono nao cria um caminho
        alternativo que escape da validacao de forma — a validacao que impede um
        `gedcom_filename` manipulado de apontar para fora da pasta.
        """
        armazenamento, _ = _portas(pasta_temporaria)
        caminho, _ = armazenamento.guardar(
            GEDCOM_VALIDO.encode("utf-8"), "arvore.ged", "gedcom", "dono-a")
        referencia = os.path.basename(caminho)

        assert armazenamento.resolver(referencia, "dono-a") == caminho
        assert armazenamento.resolver(referencia, "dono-b") == caminho, (
            "um dono diferente deixou de resolver a referencia: algum filtro por "
            "dono entrou no resolver, e o armazenamento deixou de ser unico por "
            "processo (RN-02)"
        )
        assert armazenamento.resolver("nao-e-uma-chave-valida", "dono-a") is None
        assert armazenamento.resolver(referencia, "dono-a") is not None

    def test_carregador_recebe_o_dono_por_chamada(self, pasta_temporaria):
        """`D-06`: o dono chega por chamada e nao muda o que o carregador devolve.

        O dono vai **por chamada**, e nao pelo construtor do adaptador, porque os
        adaptadores sao singletons de processo montados no import de `src/app.py`.
        A prova de que ele nao e interpretado: os dois donos devolvem a **mesma**
        arvore, e a referencia invalida continua devolvendo `None` — o dono nao
        abre caminho para fora da validacao de forma.
        """
        armazenamento, carregador = _portas(pasta_temporaria)
        caminho, _ = armazenamento.guardar(
            GEDCOM_VALIDO.encode("utf-8"), "arvore.ged", "gedcom", "dono-a")
        referencia = os.path.basename(caminho)

        for dono in ("dono-a", "dono-b"):
            arvore = carregador.carregar(referencia, dono)
            assert arvore is not None, (
                f"o carregador deixou de resolver a referencia para o dono "
                f"'{dono}': o dono passou a participar da resolucao (D-06)"
            )
            assert nomes_de_exibicao(arvore) == NOMES_ESPERADOS

        assert carregador.carregar("nao-e-uma-chave-valida", "dono-a") is None

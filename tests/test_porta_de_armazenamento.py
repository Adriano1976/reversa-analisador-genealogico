"""Testes da porta de armazenamento (acoes T027 e T028).

Dois blocos, e os dois medem algo que nenhum outro teste da suite mede.

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

## Por que este arquivo nao usa `tmp_path`

`tmp_path` e `tmp_path_factory` criam a pasta-base com `mode=0o700`, e nesta
maquina um diretorio `0o700` nao pode ser listado nem apagado. E a causa dos 15
erros de ambiente de `tests/test_upload_seguranca.py`. A fixture
`pasta_temporaria` de `tests/conftest.py` cria o diretorio em modo padrao e o
remove no fim; e ela que este arquivo usa, e o import de `src/` fica no cabecalho
padrao logo abaixo.
"""
import os
import sys

PROJETO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, PROJETO)
sys.path.insert(0, os.path.join(PROJETO, "src"))

import inspect

import pytest

from application.upload_gedcom import upload_gedcom
from core.erros import GedcomNaoSuportado
from ports import adaptadores
from ports import RepositorioDeArvores
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

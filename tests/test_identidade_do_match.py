"""Identidade do match: o nome pedido pelo CSV e a pessoa escolhida no GEDCOM.

## Por que este arquivo existe

O casamento entre o relatorio de DNA e a arvore e **por nome**, e o nome do CSV nao e
unico. Quando o nome nao casa exato, `core.matching` decide por semelhanca — e a decisao
pode escolher **outra pessoa** da familia, tipicamente alguem que compartilha os
sobrenomes. Medido em 2026-10-13 sobre os dois arquivos reais do operador: o CSV traz
`Therezinha Carvalho do Nascimento Souza`, o GEDCOM tem `Therezinha Carvalho do
Nascimento` e o motor escolheu `Soraia Carvalho do Nascimento Souza`, que tem os tres
sobrenomes do CSV contra dois da Therezinha. O cartao ficou com o cM de uma sob o nome da
outra, e nada na tela dizia isso.

## O que este arquivo mede, e o que ele NAO mede

Mede a **classificacao** (funcao pura, casos de borda) e a **aparencia na tela** (o selo e
o aviso existem onde precisam existir, e NAO existem onde nao precisam). Nao mede cor nem
posicao — isso e da folha.

A metade que mais importa e a **negativa**: um aviso que aparece em todo cartao nao avisa
nada. Os 16 casos de variacao de grafia dos dados reais (`Camila` x `Camilla`, `Manoel
Vieira da Silva` x `Manoel da Silva Vieira`, `SantAnna` x `Sant'Anna`) tem de ficar
**calados**, e ha teste para cada forma de variacao que o sistema existe para absorver.
"""
from __future__ import annotations

import os
import sys

import pytest

_RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
for _caminho in (_RAIZ, os.path.join(_RAIZ, "src")):
    if _caminho not in sys.path:
        sys.path.insert(0, _caminho)

from core.identidade_do_match import (  # noqa: E402
    A_CONFIRMAR,
    CONFIRMADA,
    GRAFIA,
    conferir,
    nomes_divergentes,
)

FOLHA = os.path.join(_RAIZ, "src", "assets", "app.css")
TEMPLATE = os.path.join(_RAIZ, "src", "templates", "index.html")


# ---------------------------------------------------------------------------
# A classificacao. Cada caso e um par REAL medido nos arquivos do operador ou um
# caso de borda declarado — nunca um par inventado para o teste passar.
# ---------------------------------------------------------------------------

#: Prenome de OUTRA pessoa, aceito porque os sobrenomes coincidem. E o falso positivo
#: que este trabalho torna visivel. O cM exibido deixa de ser apresentado como certo.
PREMONTE_TROCADO = (
    ("Therezinha Carvalho do Nascimento Souza", "Soraia Carvalho do Nascimento Souza"),
    ("Benigna Vieira de Melo", "Bernardina Vieira de Melo"),
    ("Darcy dos Santos Silva", "José Ariocy Silva Santos"),
    ("Maria Resende dos Santos", "Raul Resende Dos Santos"),
    ("*Silva Dantas", "Dionel Silva Dantas"),
    ("*Dias da Costa", "Danilo Dias Costa"),
    ("Gilson de Freitas Melro", "Danilo de Freitas Melro"),
    ("Iaraci Martins", "Gracia Martins"),
    ("*Giuliano Bertolucci", "Vicente Giuliano Bertolucci de Souza"),
)

#: Variacao de GRAFIA do mesmo prenome, que a normalizacao NAO resolve sozinha. O sistema
#: existe para absorver isto: marcar qualquer um deles seria transformar o aviso em ruido,
#: e ruido nao avisa.
MESMA_PESSOA = (
    ("Camila Maria de Jesus", "Camilla Maria de Jesus"),
    ("Matheus de Castro Andrade", "Mateus de Castro"),
    ("Maria Ivanda Bezerra de SantAnna", "Maria Ivanda Bezerra de Sant'Anna"),
    ("Manoel Vieira da Silva", "Manoel da Silva Vieira"),
    ("Eline Vasconcelos", "Eline Cabral Vieira Vasconcelos"),
    ("Sarah C Fontes Vieira", "Sarah Fontes Vieira"),
    ("Maria de Lourdes Prata de Jesus", "Maria de Lourdes de Jesus"),
    ("ANTONIO TELES LEITE NETO", "Antônio Telles Leite"),
    ("Joao Ribeiro de Almeida Neto", "João Ribeiro de Almeida"),
)

#: O mesmo nome depois da normalizacao. NAO e um alerta: e o caminho exato do matching, e
#: por isso nem chega a cair no ramo difuso. Acento e asterisco de anotacao do operador
#: (`*Maria Natividade`) sao absorvidos por `norm_name`.
MESMO_NOME = (
    ("Maria Souza", "Maria Souza"),
    ("Jose Vicente de Souza", "José Vicente de Souza"),
    ("*Maria Natividade", "Maria Natividade"),
    ("Katia Georgia Sa Azevedo", "Kátia Georgia Sá Azevedo"),
)


class TestAPessoaCertaNaoAlarma:
    """O caso mais frequente de todos: 36 dos 62 cartoes medidos nos dados reais."""

    @pytest.mark.parametrize("csv,ged", MESMO_NOME)
    def test_mesmo_nome_depois_da_normalizacao_e_confirmado(self, csv, ged):
        assert conferir(csv, ged) == CONFIRMADA, (
            f"{csv!r} x {ged!r}: a normalizacao ja resolve, entao este par nao pode virar "
            "aviso — ele e o caminho exato do matching"
        )

    @pytest.mark.parametrize("nome", ("Maria Souza", "maria souza", "MARIA SOUZA"))
    def test_caixa_nao_muda_o_estado(self, nome):
        assert conferir(nome, "Maria Souza") == CONFIRMADA

    @pytest.mark.parametrize("csv,ged", MESMO_NOME)
    def test_mesmo_nome_nao_produz_frase(self, csv, ged):
        assert nomes_divergentes(csv, ged) == ""


class TestAVariacaoDeGrafiaFicaCalada:
    """O sistema existe para absorver grafia variavel; alarmar aqui seria ruido."""

    @pytest.mark.parametrize("csv,ged", MESMA_PESSOA)
    def test_variacao_de_grafia_nao_alarma(self, csv, ged):
        assert conferir(csv, ged) == GRAFIA, (
            f"{csv!r} x {ged!r} e a mesma pessoa com grafia diferente: marcar isto "
            "transforma o aviso em ruido e ele deixa de avisar"
        )

    @pytest.mark.parametrize("csv,ged", MESMA_PESSOA)
    def test_variacao_de_grafia_nao_produz_frase(self, csv, ged):
        assert nomes_divergentes(csv, ged) == "", (
            "a tela so pode renderizar aviso quando ha frase; frase para variacao de "
            "grafia enche o cartao de texto que nao pede decisao nenhuma"
        )


class TestOPrenomeTrocadoAlarma:
    """O falso positivo perigoso: o nome casou pelo sobrenome, nao pela pessoa."""

    @pytest.mark.parametrize("csv,ged", PREMONTE_TROCADO)
    def test_prenome_de_outra_pessoa_marca(self, csv, ged):
        assert conferir(csv, ged) == A_CONFIRMAR, (
            f"{csv!r} x {ged!r}: os sobrenomes coincidem e o prenome e de outra pessoa. "
            "E este o caso que o cartao tem de mostrar, e nao esconder"
        )

    @pytest.mark.parametrize("csv,ged", PREMONTE_TROCADO)
    def test_a_frase_diz_os_dois_nomes(self, csv, ged):
        frase = nomes_divergentes(csv, ged)
        assert csv in frase and ged in frase, (
            "o aviso precisa mostrar o nome que o relatorio de DNA traz E o nome da pessoa "
            f"escolhida no GEDCOM; sem os dois, quem le nao tem o que conferir. frase={frase!r}"
        )


class TestCasosDeBorda:
    """Os pares que o template pode receber de payload antigo ou de arquivo torto."""

    def test_sem_pessoa_na_arvore_marca(self):
        """Sem pessoa resolvida nao ha o que confirmar; calar afirmaria o que nao se sabe."""
        assert conferir("Maria Souza", "") == A_CONFIRMAR

    def test_nome_vazio_no_csv_nao_quebra(self):
        assert conferir("", "Maria Souza") == A_CONFIRMAR

    def test_espacos_sobrando_nao_contam(self):
        assert conferir("  Maria   Souza  ", "Maria Souza") == CONFIRMADA

    def test_os_dois_vazios_marcam(self):
        assert conferir("", "") == A_CONFIRMAR

    def test_prenome_abreviado_na_arvore_nao_alarma(self):
        """`A.` e abreviacao de `Antonio`, e nao outra pessoa."""
        assert conferir("Antonio Silva", "Antonio Silva") == CONFIRMADA

    def test_prenome_encurtado_por_comum_acordo_nao_alarma(self):
        """`Terezinha` x `Therezinha` e a mesma pessoa com grafia variavel."""
        assert conferir("Terezinha Carvalho do Nascimento", "Therezinha Carvalho do Nascimento") == GRAFIA

    def test_o_pedaco_a_mais_na_FRENTE_marca(self):
        """LIMITE DECLARADO da regra, e nao defeito: quando o CSV usa um prenome que nao e o
        PRIMEIRO token da arvore, a comparacao de prenome nao tem como saber que e a mesma
        pessoa. `Claudio Miranda` x `Luiz Claúdio de Miranda` e `*Giuliano Bertolucci` x
        `Vicente Giuliano Bertolucci de Souza` caem aqui.

        Marcar e a escolha deliberada: o custo de um aviso a mais e o operador conferir um
        cartao que estava certo; o custo de um aviso a menos e aceitar o cM de outra pessoa.
        Fechar este caso exigiria comparar o prenome do CSV contra TODOS os tokens do nome da
        arvore, o que e uma mudanca de regra de matching — e nao o que o caminho 3 se propõe.
        """
        assert conferir("Claudio Miranda", "Luiz Claúdio de Miranda") == A_CONFIRMAR

    def test_esse_mesmo_pedaco_mudando_a_pessoa_ainda_alarma(self):
        """A rede de 3 letras nao engole o defeito: `Iaraci` e `Gracia` nao comecam igual."""
        assert conferir("Iaraci Martins", "Gracia Martins") == A_CONFIRMAR

    def test_o_estado_e_deterministico(self):
        """Funcao pura: oito chamadas, um estado so — o cartao nao pode mudar sozinho."""
        estados = {conferir("Therezinha Carvalho do Nascimento Souza",
                            "Soraia Carvalho do Nascimento Souza") for _ in range(8)}
        assert estados == {A_CONFIRMAR}


class TestOsLimiaresEstaoDeclarados:
    """O corte do prenome e heuristico declarado, como o `0.33` do Jaccard."""

    def test_os_limiares_sao_constantes_nomeadas(self):
        from core import identidade_do_match as modulo

        for nome in ("LIMITE_PREMONE", "MIN_SEMELHANCA_PREMONE", "PREFIXO_MINIMO"):
            assert isinstance(getattr(modulo, nome), int), (
                f"o limiar {nome} precisa ser constante nomeada e inteira: numero solto no "
                "meio da regra nao pode ser ajustado nem citado"
            )

    def test_o_docstring_declara_que_sao_heuristicos(self):
        from core import identidade_do_match as modulo

        texto = modulo.__doc__ or ""
        assert "heuristic" in texto.lower(), (
            "o modulo precisa declarar que os limiares sao heuristicos ajustaveis: sem isso "
            "o proximo leitor trata o corte como numero calibrado"
        )


# ---------------------------------------------------------------------------
# A tela
# ---------------------------------------------------------------------------


class TestAAparenciaNaTela:
    """O que o template e a folha precisam manter, medido no arquivo, sem servidor."""

    @pytest.fixture
    def template(self) -> str:
        with open(TEMPLATE, encoding="utf-8") as arquivo:
            return arquivo.read()

    @pytest.fixture
    def folha(self) -> str:
        with open(FOLHA, encoding="utf-8") as arquivo:
            return arquivo.read()

    def test_o_sinal_de_identidade_esta_no_cabecalho_do_cartao(self, template):
        """Com a tabela do indice fora (adendo 019), o cabecalho e' o unico lugar que mostra.

        E ele e' o `<summary>` do cartao: o sinal aparece com o cartao FECHADO, que era
        exatamente o trabalho da coluna que saiu — numa lista de 142 matches, o operador nao
        pode descobrir a troca de pessoa so depois de abrir o cartao.

        A limpeza dos comentarios NAO e' decorativa: o comentario do cartao cita
        `<div class="card-header">` em prosa, e sem tirar o comentario o regex casa ali e o
        teste mede a documentacao em vez do documento.

        E a busca e' ancorada no MARCADOR do cartao de resultado, e nao no primeiro
        `card-header` do arquivo: desde o adendo 022 o bloco dos avisos do arquivo tambem
        traz um `card-header`, e ele vem ANTES dos cartoes — o "primeiro do documento" passou
        a ser o dele.
        """
        import re

        sem_comentarios = re.sub(r"\{#.*?#\}", "", template, flags=re.S)
        cabecalho = re.search(
            r'(?s)<details class="card cartao-do-resultado".*?<div class="card-header">(.*?)</div>',
            sem_comentarios)
        assert cabecalho, "o cartao de resultado perdeu o cabecalho"
        assert "identidade-a-confirmar" in cabecalho.group(1), (
            "o sinal de identidade saiu do cabecalho do cartao"
        )

    def test_o_selo_so_aparece_quando_ha_o_que_confirmar(self, template):
        assert "{% if result.identidade == 'a_confirmar' %}" in template, (
            "sem a condicao, o cabecalho marcaria os 142 cartoes e o aviso viraria decoracao"
        )

    def test_o_selo_tem_um_ponto_de_uso_so(self, template):
        """Eram dois (o indice e o cabecalho) enquanto a tabela existia; hoje e' um.

        A contagem existia porque DOIS lugares mostravam a mesma coisa com a mesma classe, e
        duas chances de a cor divergir sao uma chance a mais do que o necessario. Com um ponto
        so, o que se prende e' que ele nao vire dois por descuido.
        """
        import re

        sem_comentarios = re.sub(r"\{#.*?#\}", "", template, flags=re.S)
        assert sem_comentarios.count("identidade-a-confirmar") == 1, (
            "a classe do selo de identidade tem UM ponto de uso, o cabecalho do cartao"
        )

    def test_a_frase_do_aviso_fica_no_cartao_e_no_title(self, template):
        """A explicacao tem dois lugares: o `title` (mouse) e a caixa do cartao (todos)."""
        assert 'title="{{ result.identidade_aviso }}"' in template, (
            "o selo perdeu o `title`: quem usa mouse ficaria sem saber o que confirmar"
        )
        assert 'class="alerta-identidade"' in template

    def test_o_aviso_do_cartao_vem_antes_das_secoes(self, template):
        posicao_aviso = template.find("alerta-identidade")
        posicao_secao_1 = template.find("1.</span> Parentesco documental")
        assert posicao_aviso != -1, "o aviso de identidade sumiu do cartao"
        assert posicao_secao_1 != -1, "a secao 1 sumiu do cartao"
        assert posicao_aviso < posicao_secao_1, (
            "o aviso sobre DE QUEM e o cartao tem de vir antes das conclusoes: depois das "
            "cinco secoes ele chega tarde demais para quem ja leu os numeros"
        )

    def test_o_aviso_do_cartao_nasce_do_nucleo_e_nao_do_template(self, template):
        """O texto de dominio e montado uma vez, no nucleo (`RF-20`)."""
        assert "{{ result.identidade_aviso }}" in template, (
            "o template voltou a montar texto de dominio: a frase com os dois nomes nasce em "
            "`core/identidade_do_match.nomes_divergentes`"
        )

    def test_o_aviso_do_cartao_nao_decide_nem_descarta(self, template):
        trecho = template[template.find("alerta-identidade"):]
        trecho = trecho[:trecho.find("</div>") + 6]
        for proibido in ("btn-danger", "Apagar", "descartad"):
            assert proibido not in trecho, (
                f"o aviso de identidade virou acao ({proibido!r}): o caminho escolhido mostra "
                "a divergencia e devolve a conferencia ao operador, sem descartar o match"
            )

    def test_o_selo_tem_estilo_na_folha(self, folha):
        assert ".identidade-a-confirmar" in folha, (
            "o selo ficaria sem forma na folha e sumiria entre os selos de confrontacao"
        )

    def test_o_aviso_tem_estilo_na_folha(self, folha):
        assert ".alerta-identidade" in folha, (
            "a caixa do aviso ficaria sem forma na folha"
        )

    def test_a_folha_nao_redefine_a_paleta_do_aviso(self, folha):
        """A paleta vem de `--aviso-bg`/`--aviso-line`, que os DOIS temas redefinem."""
        regra = folha[folha.find(".alerta-identidade{"):]
        regra = regra[:regra.find("}")]
        assert "var(--aviso-bg)" in regra and "var(--aviso-line)" in regra, (
            "a caixa do aviso fixou cor literal: no tema escuro ela ficaria ilegivel, que foi "
            "exatamente o defeito ja medido no botao 'Apagar'"
        )

    def test_o_selo_tambem_nao_fixa_cor(self, folha):
        regra = folha[folha.find(".identidade-a-confirmar{"):]
        regra = regra[:regra.find("}")]
        assert "var(--aviso-bg)" in regra and "var(--aviso-line)" in regra, (
            "o selo fixou cor literal e nao acompanha o tema"
        )


class TestUmPrenomeSoNaoConfirma:
    """Nome de UMA palavra nao identifica ninguem — e o estado tem de dizer isso.

    ## O caso medido, em 2026-10-14

    O kit `ZC1171551` traz `"Margarida"` no relatorio, e a arvore tem **oito** registros com
    esse nome exato. Com uma palavra so, todo termo de semelhanca da nota do matching fica
    IGUAL entre os oito; a ordem entre eles e do desempate congelado, nao de evidencia. Dois
    tem caminho ate a raiz (um de 1673 e um sem data), e a escolha entre os dois foi essa
    ordenacao. O cartao saiu com o de 1673 — 353 anos —, e o eixo da identidade dizia
    `CONFIRMADA`.

    Um casamento exato de `Margarida` com `Margarida` confirma que a PALAVRA e a mesma. Nao
    confirma que a pessoa e.
    """

    def test_um_prenome_so_nao_confirma(self):
        assert conferir("Margarida", "Margarida") == A_CONFIRMAR

    def test_um_prenome_so_nao_confirma_nem_com_arvore_maior(self):
        assert conferir("Margarida", "Margarida Souza") == A_CONFIRMAR

    def test_a_frase_fala_de_prenome_e_nao_de_sobrenome(self):
        """A frase generica diz "os sobrenomes coincidem" — e aqui nao ha sobrenome nenhum."""
        frase = nomes_divergentes("Margarida", "Margarida")
        assert "um prenome só" in frase
        assert "sobrenomes coincidem" not in frase, (
            "a frase generica afirma que os sobrenomes coincidem, e o relatorio nao trouxe nenhum"
        )
        assert "Confira a pessoa pelos pais" in frase

    @pytest.mark.parametrize("nome", [
        "Maria Natividade",           # `split_name_pt` chama `natividade` de prenome...
        "Jose Francisco Alves",       # ...e `alves` de prenome, nestes dois.
        "Maria Souza",
    ])
    def test_duas_palavras_ou_mais_continuam_confirmando(self, nome):
        """O corte e por NUMERO DE PALAVRAS, e nao por "nao tem sobrenome".

        `split_name_pt` classifica `natividade` como prenome quando o nome comeca por um
        prenome generico — e esses nomes TEM parte que discrimina. Marca-los seria
        transformar o aviso em ruido, e ruido nao avisa.
        """
        assert conferir(nome, nome) == CONFIRMADA

    def test_o_nome_vazio_continua_marcando(self):
        assert conferir("", "") == A_CONFIRMAR

    def test_a_regra_e_por_contagem_de_palavras(self):
        """Documenta o mecanismo: e o numero de palavras, nao a presenca de sobrenome."""
        assert conferir("Margarida", "Margarida") == A_CONFIRMAR
        assert conferir("Margarida Souza", "Margarida Souza") == CONFIRMADA
        assert conferir("Margarida de Souza", "Margarida de Souza") == CONFIRMADA

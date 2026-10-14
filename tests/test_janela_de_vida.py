"""Janela de vida: a data do registro permite que ele tenha doado aquele DNA?

## Por que este arquivo existe

O casamento entre o relatorio de DNA e a arvore e por **nome**, e nome casa com gente de outro
seculo. Medido em 2026-10-14, nos 62 cartoes da analise real do operador: **10** escolhas com
idade impossivel para quem doou DNA — entre elas um match de 25,4 cM casado com um registro de
**1793** (233 anos), e outro de 8,2 cM casado com um de **1360** (666 anos).

## O que este arquivo mede, e o que ele NAO mede

Mede a **classificacao** (funcao pura: os dois limiares, os qualificadores de data, os casos de
borda) e a **aparencia na tela** (o selo existe onde precisa e NAO existe onde nao precisa).

A metade que mais importa e a **negativa**, pela licao do selo de identidade: um aviso que
aparece em todo cartao nao avisa nada. Os **39** cartoes `possivel` e os **10** sem data tem de
ficar **calados** — marcar quem nao tem data encheria a tela de aviso sem informacao nenhuma.

## A assimetria e o ponto

O teste e `idade > limite`: acusa quando o registro e **jovem demais** para a distancia. Nunca
acusa um ancestral legitimo, porque o teste e sobre o **match** (quem doou o DNA), e nao sobre
os nos do caminho. Ha teste para isso — e para o outro lado: quem esta dentro da janela passa.
"""
from __future__ import annotations

import os
import re
import sys

import pytest

_RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
for _caminho in (_RAIZ, os.path.join(_RAIZ, "src")):
    if _caminho not in sys.path:
        sys.path.insert(0, _caminho)

from core.janela_de_vida import (  # noqa: E402
    DATA_IMPRECISA,
    IDADE_IMPOSSIVEL,
    IDADE_MINIMA_DE_GERACAO,
    IDADE_SUSPEITA,
    IMPOSSIVEL,
    POSSIVEL,
    SEM_DATA,
    SUSPEITA,
    ano_de_referencia,
    aviso_da_janela,
    conferir_janela_de_vida,
)

FOLHA = os.path.join(_RAIZ, "src", "assets", "app.css")
TEMPLATE = os.path.join(_RAIZ, "src", "templates", "index.html")

ANO = 2026


class TestOsDoisLimiares:
    """`IDADE_SUSPEITA` avisa; `IDADE_IMPOSSIVEL` e o teto duro."""

    def test_os_limiares_sao_constantes_nomeadas(self):
        assert isinstance(IDADE_SUSPEITA, int) and isinstance(IDADE_IMPOSSIVEL, int)
        assert IDADE_SUSPEITA < IDADE_IMPOSSIVEL, (
            "o limiar de aviso tem de ser menor que o teto: inverter os dois faria o aviso "
            "nunca disparar antes do impossivel"
        )

    def test_o_teto_e_o_recorde_humano_verificado(self):
        """122 e a idade de Jeanne Calment (1875-1997). Acima nao ha pessoa documentada."""
        assert IDADE_IMPOSSIVEL == 122, (
            "o teto deixou de ser o recorde verificado: um numero maior admitiria idade que "
            "nenhuma pessoa documentada alcancou"
        )

    def test_o_espaco_entre_aviso_e_teto_existe(self):
        assert IDADE_IMPOSSIVEL - IDADE_SUSPEITA >= 10, (
            "o espaco entre aviso e teto existe para nao tratar como absurdo o centenario que "
            "testou; encurta-lo demais elimina essa distincao"
        )

    @pytest.mark.parametrize("idade,esperado", [
        (30, POSSIVEL),
        (80, POSSIVEL),
        (105, POSSIVEL),          # o limiar em si ainda e possivel
        (106, SUSPEITA),          # um ano acima ja avisa
        (116, SUSPEITA),          # o caso real mais apertado
        (122, SUSPEITA),          # o teto em si ainda nao e impossivel
        (123, IMPOSSIVEL),        # um ano acima do teto
        (233, IMPOSSIVEL),        # o Manoel de 1793
        (666, IMPOSSIVEL),        # o Iaraci de 1360
    ])
    def test_a_fronteira_de_cada_limiar(self, idade, esperado):
        ano_de_nascimento = ANO - idade
        estado, idade_calc, _ = conferir_janela_de_vida(str(ano_de_nascimento), ANO)
        assert estado == esperado, (
            f"{idade} anos em {ANO} devia dar {esperado!r} e deu {estado!r}"
        )
        assert idade_calc == idade

    def test_a_idade_e_devolvida_para_a_tela_poder_exibir(self):
        _, idade, _ = conferir_janela_de_vida("1793", ANO)
        assert idade == 233


class TestOsCasosReais:
    """Os pares medidos nos arquivos do operador."""

    @pytest.mark.parametrize("nascimento,idade", [
        ("1793", 233),            # Manoel da Silva Vieira — o cartao de 25,4 cM
        ("MAY 1673", 353),        # Margarida
        ("1360", 666),            # o "Gracia Martins" que casou com "Iaraci Martins"
        ("5 APR 1815", 211),      # JOSE VICENTE de Souza
        ("1881", 145),            # Francisco Alves de Lima
    ])
    def test_escolha_impossivel_e_marcada(self, nascimento, idade):
        estado, idade_calc, _ = conferir_janela_de_vida(nascimento, ANO)
        assert estado == IMPOSSIVEL
        assert idade_calc == idade

    @pytest.mark.parametrize("nascimento,idade", [
        ("23 FEB 1909", 117),
        ("1910", 116),
        ("22 SEP 1916", 110),
    ])
    def test_centenario_e_suspeito_e_nao_impossivel(self, nascimento, idade):
        """Estar vivo ou nao e outro assunto: a regra so mede se a idade e alcancavel."""
        estado, idade_calc, _ = conferir_janela_de_vida(nascimento, ANO)
        assert estado == SUSPEITA, (
            f"{idade} anos esta abaixo do recorde verificado ({IDADE_IMPOSSIVEL}): marcar como "
            "impossivel seria afirmar mais do que o dado permite"
        )

    @pytest.mark.parametrize("nascimento", ["1976", "1941", "1936", "1958", "1930", "1925"])
    def test_doador_plausivel_nao_e_marcado(self, nascimento):
        """1936 e o nascimento do Manoel do GEDmatch — se ele entrar na arvore, passa limpo.

        A faixa para aqui em 1925 (101 anos): acima de `IDADE_SUSPEITA` o cartao ja avisa, e
        isso e o desenho, nao um defeito. Os dois testes seguintes fixam a fronteira real.
        """
        estado, _, _ = conferir_janela_de_vida(nascimento, ANO)
        assert estado == POSSIVEL, (
            f"alguem nascido em {nascimento} tem idade plausivel para ter doado DNA e NAO pode "
            "ser marcado"
        )

    def test_um_seculo_ja_avisa(self):
        """1920 sao 106 anos: acima do aviso, abaixo do teto. Escrevi esperando `possivel`."""
        estado, idade, _ = conferir_janela_de_vida("1920", ANO)
        assert idade == 106
        assert estado == SUSPEITA

    def test_um_seculo_de_idade_ja_e_impossivel(self):
        """1900 nao e caso de borda: 126 anos passa o recorde verificado.

        Escrevi este teste esperando `possivel` e o codigo me corrigiu — a data esta a 4 anos
        do teto. Fica registrado o limite real, e nao a minha intuicao.
        """
        estado, idade, _ = conferir_janela_de_vida("1900", ANO)
        assert idade == 126
        assert estado == IMPOSSIVEL


class TestSemDataNaoAlarma:
    """Nao saber nao e o mesmo que ser impossivel.

    Medido: 10 dos 62 cartoes nao trazem nascimento. Marca-los encheria a tela de aviso sem
    informacao — e o operador aprenderia a ignorar o selo.
    """

    @pytest.mark.parametrize("vazio", [None, "", "   ", "Sem data", "N/A"])
    def test_ausencia_de_data_nao_marca(self, vazio):
        estado, idade, imprecisa = conferir_janela_de_vida(vazio, ANO)
        assert estado == SEM_DATA
        assert idade is None
        assert imprecisa is False

    def test_ausencia_de_data_nao_produz_frase(self):
        assert aviso_da_janela(SEM_DATA, None, "Fulano", "Fulano", None, ANO) == ""

    def test_possivel_nao_produz_frase(self):
        assert aviso_da_janela(POSSIVEL, 50, "Fulano", "Fulano", "1976", ANO) == ""


class TestDataImprecisa:
    """`ABT 1852` nao e data exata, e o cartao precisa dizer isso."""

    @pytest.mark.parametrize("data", ["ABT 1852", "BEF 1878", "AFT 1900", "CAL 1890",
                                      "EST 1850", "CIRCA 1840", "ABT 1600", "ABT 1798"])
    def test_o_qualificador_fica_registrado_em_qualquer_estado(self, data):
        """A imprecisao e registrada sempre — e nao substitui o veredicto da idade.

        Escrevi este teste esperando so `data_imprecisa`, e o codigo me corrigiu: `ABT 1852`
        tem 174 anos, entao o estado e `impossivel` **e** a data segue marcada como estimada.
        As duas informacoes convivem, e o cartao mostra as duas.
        """
        estado, _, imprecisa = conferir_janela_de_vida(data, ANO)
        assert imprecisa is True, f"{data!r} e estimativa e tem de ficar registrado"
        assert estado in (DATA_IMPRECISA, SUSPEITA, IMPOSSIVEL)

    def test_data_estimada_e_recente_sai_como_imprecisa(self):
        """O caso em que a imprecisao e o que sobra: ano estimado, idade plausivel."""
        estado, _, imprecisa = conferir_janela_de_vida("ABT 1950", ANO)
        assert estado == DATA_IMPRECISA
        assert imprecisa is True

    def test_data_imprecisa_e_impossivel_vence_o_impossivel(self):
        """A idade absurda pesa mais que a imprecisao: `ABT 1600` e impossivel, nao 'estimada'."""
        estado, _, imprecisa = conferir_janela_de_vida("ABT 1600", ANO)
        assert estado == IMPOSSIVEL
        assert imprecisa is True, (
            "a imprecisao continua registrada mesmo quando o estado e impossivel"
        )

    def test_data_exata_nao_e_imprecisa(self):
        estado, _, imprecisa = conferir_janela_de_vida("12 OCT 1976", ANO)
        assert estado == POSSIVEL
        assert imprecisa is False

    def test_a_frase_da_data_estimada_cita_o_ano(self):
        frase = aviso_da_janela(DATA_IMPRECISA, 76, "Fulano", "Fulano", "ABT 1950", ANO)
        assert "ABT 1950" in frase and "76" in frase


class TestAAvisoEscritoParaOOperador:
    """A frase tem de dizer os dois nomes, a data, a idade e o que conferir."""

    @pytest.mark.parametrize("estado,idade,nascimento", [
        (IMPOSSIVEL, 233, "1793"),
        (SUSPEITA, 117, "23 FEB 1909"),
    ])
    def test_a_frase_traz_nomes_data_e_idade(self, estado, idade, nascimento):
        frase = aviso_da_janela(estado, idade, "Manoel Vieira da Silva",
                                "Manoel da Silva Vieira", nascimento, ANO)
        assert "Manoel Vieira da Silva" in frase, "falta o nome que o CSV traz"
        assert "Manoel da Silva Vieira" in frase, "falta o nome da pessoa escolhida"
        assert nascimento in frase, "falta a data do registro"
        assert str(idade) in frase, "falta a idade calculada"

    def test_a_frase_do_impossivel_nao_afirma_o_parentesco(self):
        frase = aviso_da_janela(IMPOSSIVEL, 233, "A", "B", "1793", ANO)
        assert "não pode ser lido como o do doador" in frase, (
            "o aviso precisa dizer que o parentesco exibido e o do REGISTRO ESCOLHIDO, e nao o "
            "do doador — e a razao de o cartao nao ser descartado"
        )

    def test_a_frase_do_suspeito_pede_conferencia(self):
        frase = aviso_da_janela(SUSPEITA, 117, "A", "B", "1909", ANO)
        assert "confirme" in frase.lower()


class TestAAncora:
    """A referencia sai do proprio dado, e nao so do relogio."""

    def test_usa_o_ano_atual_quando_a_raiz_e_antiga(self):
        assert ano_de_referencia(2026, "12 OCT 1976") == 2026

    def test_sobe_quando_a_raiz_e_mais_nova_que_o_ano_atual(self):
        """Uma raiz nascida em 2020 nao pode ser medida contra 2026."""
        assert ano_de_referencia(2026, "2020") == 2020 + IDADE_MINIMA_DE_GERACAO

    def test_sem_nascimento_da_raiz_cai_no_ano_atual(self):
        for vazio in (None, "", "Sem data"):
            assert ano_de_referencia(2026, vazio) == 2026

    def test_e_reproduzivel(self):
        assert ano_de_referencia(2026, "1976") == ano_de_referencia(2026, "1976")


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

    def test_o_indice_tem_a_coluna_de_janela(self, template):
        assert ">Janela de vida<" in template, (
            "o indice perdeu a coluna: numa lista de 62 matches o operador so descobriria a "
            "idade impossivel depois de abrir o cartao"
        )

    def test_o_selo_so_aparece_quando_ha_o_que_marcar(self, template):
        assert "{% if r.janela_de_vida == 'impossivel' %}" in template
        assert "{% elif r.janela_de_vida == 'suspeita' %}" in template

    def test_o_rotulo_do_indice_e_curto(self, template):
        """A licao do selo de identidade: o `visually-hidden` e rotulo, nao a explicacao."""
        sem_comentarios = re.sub(r"\{#.*?#\}", "", template, flags=re.S)
        selo = re.search(
            r'<span class="badge janela-impossivel" title="\{\{ r\.janela_aviso \}\}">'
            r'(.*?)</span></span>',
            sem_comentarios,
        )
        assert selo, "o selo de janela perdeu a forma esperada (classe, title e rotulo)"
        assert "janela_aviso" not in selo.group(1), (
            "o `visually-hidden` do indice voltou a carregar a frase inteira"
        )
        assert "idade" in selo.group(1).lower() or "anos" in selo.group(1), (
            "o selo do indice perdeu o rotulo acessivel"
        )

    def test_o_aviso_do_cartao_vem_antes_das_secoes(self, template):
        posicao_aviso = template.find("alerta-janela")
        posicao_secao_1 = template.find("1.</span> Parentesco documental")
        assert posicao_aviso != -1, "o aviso de janela de vida sumiu do cartao"
        assert posicao_aviso < posicao_secao_1, (
            "o aviso sobre a idade do doador tem de vir antes das conclusoes"
        )

    def test_o_aviso_do_cartao_vem_do_nucleo(self, template):
        assert "{{ result.janela_aviso }}" in template, (
            "o template voltou a montar texto de dominio: a frase nasce em "
            "`core/janela_de_vida.aviso_da_janela`"
        )

    def test_o_aviso_nao_descarta_o_match(self, template):
        """Medido: 9 das 10 escolhas impossiveis nao tem alternativa. Descartar perderia dado."""
        trecho = template[template.find("alerta-janela"):]
        trecho = trecho[:trecho.find("</div>") + 6]
        for proibido in ("btn-danger", "Apagar", "descartad"):
            assert proibido not in trecho, (
                f"o aviso de janela virou acao ({proibido!r}): o caminho escolhido mostra a "
                "divergencia sem perder a evidencia genetica"
            )

    @pytest.mark.parametrize("classe", [
        ".janela-impossivel", ".janela-suspeita", ".janela-imprecisa",
        ".alerta-janela", ".alerta-janela-impossivel",
    ])
    def test_as_classes_tem_estilo_na_folha(self, folha, classe):
        assert classe in folha, f"a folha perdeu a regra {classe}"

    def test_a_folha_nao_fixa_cor_literal(self, folha):
        """A licao do botao 'Apagar': cor fixa some no tema escuro."""
        for classe in (".janela-impossivel{", ".alerta-janela{", ".alerta-janela-impossivel{"):
            regra = folha[folha.find(classe):]
            regra = regra[:regra.find("}")]
            assert "var(--" in regra, f"{classe} fixou cor literal e nao acompanha o tema"

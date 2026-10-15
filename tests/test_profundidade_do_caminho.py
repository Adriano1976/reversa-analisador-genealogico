"""A terceira verificacao: a arvore afirma a mesma profundidade que o proprio kit?

## Por que este arquivo existe

Duas verificacoes ja existiam e nao se sobrepoem a esta. A **janela de vida**
(`tests/test_janela_de_vida.py`) pergunta se a pessoa escolhida pode ter doado aquele DNA. O
**confronto** (`tests/test_confrontacao_gedcom_dna.py`) pergunta se o cM cabe na faixa
publicada para o parentesco documental.

Medido em 2026-10-14 nos 62 cartoes reais, existe um cartao em que as duas se calam e a
profundidade acusa: kit `XS4787142`, 19,2 cM, doadora nascida em 1976 — idade plausivel, e a
versao 4.0 nao publica faixa para "Primos de 8º grau com 2× remoção". A arvore afirma 10,0
geracoes; o proprio relatorio de DNA estima 4,77. **Um cartao** nao justifica um arquivo.

O que justifica sao os outros dois motivos, e os dois sao de falha silenciosa:

1. a coluna `MRCA` vinha no CSV de todos os 270 kits e era **descartada** por
   `aggregate_matches`, que preserva so `Name` e `cM`. Trazida de volta, ela e o unico numero
   do arquivo de DNA que fala de profundidade;
2. o texto dos **7 cartoes que ficam sem faixa publicada** dizia apenas "Inconclusivo", que
   na tela se le como "sem objecao". Nenhum veredito muda (os quatro estados sao contrato:
   `RF-19`, `BR-D-27`, ADR-15) — o que muda e o texto passar a nomear a razao estrutural.
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

from core.evidence_comparison import compare  # noqa: E402
from core.genetic_evidence import build_genetic_evidence, detect_segment_columns  # noqa: E402
from core.profundidade_do_caminho import (  # noqa: E402
    ATENCAO,
    CONCORDA,
    DIVERGENCIA,
    LIMIAR_DE_ATENCAO,
    LIMIAR_DE_DIVERGENCIA,
    SEM_DADO,
    aviso_da_profundidade,
    conferir_profundidade,
    no_na_profundidade_sugerida,
    resumo_da_profundidade,
)
from core.relationship_hypotheses import (  # noqa: E402
    hypotheses_for_evidence,
    meioses_maximo_publicado,
    meioses_publicados,
)
from reporting.mermaid_render import anotar_profundidade  # noqa: E402

# ---------------------------------------------------------------------------
# A arvore sintetica: 3 geracoes de cada lado, primos de 3º grau.
#
#   Jose Silva x Rita Souza          <- ancestral comum (com conjuge: forca o no `A+B`)
#     ├─ Pedro Silva x Eva            ├─ Paulo Silva x Helena
#     │    └─ Fabio Silva x Gilda     │    └─ Igor Silva x Joana
#     │         └─ Carlos (raiz)      │         └─ Ana (o match)
#
# Caminho: Carlos -> Fabio -> Pedro -> Jose -> Paulo -> Igor -> Ana. 7 nos, ancestral no
# indice 3, 3 geracoes de cada lado, 6 meioses, media 3,0.
# ---------------------------------------------------------------------------
PROFUNDIDADE_GED = """0 HEAD
1 SOUR TEST
1 GEDC
2 VERS 5.5.1
2 FORM LINEAGE-LINKED
0 @G0A@ INDI
1 NAME Jose /Silva/
1 SEX M
1 FAMS @F0@
0 @G0B@ INDI
1 NAME Rita /Souza/
1 SEX F
1 FAMS @F0@
0 @G1A@ INDI
1 NAME Pedro /Silva/
1 SEX M
1 FAMC @F0@
1 FAMS @F1@
0 @G1B@ INDI
1 NAME Paulo /Silva/
1 SEX M
1 FAMC @F0@
1 FAMS @F2@
0 @G1C@ INDI
1 NAME Eva /Costa/
1 SEX F
1 FAMS @F1@
0 @G1D@ INDI
1 NAME Helena /Lima/
1 SEX F
1 FAMS @F2@
0 @G2A@ INDI
1 NAME Fabio /Silva/
1 SEX M
1 FAMC @F1@
1 FAMS @F3@
0 @G2B@ INDI
1 NAME Igor /Silva/
1 SEX M
1 FAMC @F2@
1 FAMS @F4@
0 @G2C@ INDI
1 NAME Gilda /Rocha/
1 SEX F
1 FAMS @F3@
0 @G2D@ INDI
1 NAME Joana /Pires/
1 SEX F
1 FAMS @F4@
0 @G3A@ INDI
1 NAME Carlos /Silva/ Souza
1 SEX M
1 FAMC @F3@
0 @G3B@ INDI
1 NAME Ana /Silva/ Souza
1 SEX F
1 FAMC @F4@
0 @F0@ FAM
1 HUSB @G0A@
1 WIFE @G0B@
1 CHIL @G1A@
1 CHIL @G1B@
0 @F1@ FAM
1 HUSB @G1A@
1 WIFE @G1C@
1 CHIL @G2A@
0 @F2@ FAM
1 HUSB @G1B@
1 WIFE @G1D@
1 CHIL @G2B@
0 @F3@ FAM
1 HUSB @G2A@
1 WIFE @G2C@
1 CHIL @G3A@
0 @F4@ FAM
1 HUSB @G2B@
1 WIFE @G2D@
1 CHIL @G3B@
0 TRLR
"""

RAIZ = "Carlos Silva Souza"

# Nomes no disco na forma que o armazenamento usa (`16hex__nome`), porque o POST de producao
# passa pelo `resolver`, que valida a FORMA da chave: um arquivo gravado como
# `profundidade.ged` seria recusado, a tela cairia no estado de entrada e o teste mediria uma
# pagina sem resultado nenhum — passando por vacuidade. A chave nao precisa ser o sha256 real
# do conteudo; quem a valida e o caminho de ENVIO.
NOME_GED = "0000000000000001__profundidade.ged"
NOME_CSV = "0000000000000002__profundidade.csv"


def _gedcom(nascimento_do_match: str | None = None) -> str:
    """O GEDCOM de teste, opcionalmente com data de nascimento no match.

    Com data, a janela de vida passa a ter o que dizer — e o selo do cabecalho precisa
    deixar de mostrar so o veredito de cM. Sem data, ela fica `sem_data`, que e o caso em
    que as duas verificacoes nao se tocam.
    """
    if not nascimento_do_match:
        return PROFUNDIDADE_GED
    bloco = f"1 BIRT\n2 DATE {nascimento_do_match}\n"
    return PROFUNDIDADE_GED.replace("1 FAMC @F4@", "1 FAMC @F4@\n" + bloco.rstrip("\n"))


def _csv(mrca) -> str:
    """O CSV de producao do GEDmatch, com a coluna `MRCA` que o app descartava."""
    linha = f"Ana Silva Souza,25.4,{mrca}\n" if mrca is not None else "Ana Silva Souza,25.4\n"
    cabecalho = "Name,cM,MRCA\n" if mrca is not None else "Name,cM\n"
    return cabecalho + linha


def _rodar(pasta: str, mrca, nascimento_do_match: str | None = None):
    from core.dna_analysis import Dependencias, dna_analysis
    from parsers.csv_ingest import aggregate_matches, detect_columns, read_csv_with_fallback
    from parsers.gedcom_parser import carregar_arvore
    from reporting.mermaid_render import (
        anotar_profundidade as anotar,
        generate_mermaid_graph,
        generate_mermaid_graph_indirect_bridge,
    )

    ged = os.path.join(pasta, NOME_GED)
    csv = os.path.join(pasta, NOME_CSV)
    with open(ged, "w", encoding="utf-8") as arquivo:
        arquivo.write(_gedcom(nascimento_do_match))
    with open(csv, "w", encoding="utf-8") as arquivo:
        arquivo.write(_csv(mrca))

    deps = Dependencias(read_csv_with_fallback, detect_columns, aggregate_matches,
                        generate_mermaid_graph, generate_mermaid_graph_indirect_bridge,
                        anotar)
    resultados, _descartados, _mensagem = dna_analysis(
        csv, RAIZ, deps, carregar_arvore(ged))
    return resultados


class TestA_Regra:
    """`conferir_profundidade`: os quatro estados, e onde ficam as fronteiras."""

    def test_sem_meioses_ou_sem_kit_e_sem_dado(self):
        """Nao saber nao e o mesmo que divergir — marcar aqui encheria a tela sem informacao."""
        assert conferir_profundidade(None, 4.0)[0] == SEM_DADO
        assert conferir_profundidade(0, 4.0)[0] == SEM_DADO
        assert conferir_profundidade(12, None)[0] == SEM_DADO
        assert conferir_profundidade(12, 0)[0] == SEM_DADO

    @pytest.mark.parametrize("meioses,kit,esperado", [
        # As duas calibragens medidas nos cartoes reais: a media de meioses bate com o MRCA.
        (11, 4.57, CONCORDA),   # TG8027863, "Primos de 1º grau com 7× remoção"
        (8, 5.19, CONCORDA),    # ZL6373425, "Primos de 1º grau com 6× remoção"
        (14, 6.97, CONCORDA),   # HY7011355
        (20, 4.77, DIVERGENCIA),  # XS4787142 — o cartao que motivou a regra
        (19, 4.84, ATENCAO),    # EJ8115026
        (18, 4.80, ATENCAO),    # WU5354158
    ])
    def test_os_casos_medidos(self, meioses, kit, esperado):
        assert conferir_profundidade(meioses, kit)[0] == esperado

    def test_as_fronteiras_sao_inclusivas_e_assimetricas(self):
        """`>=` nos dois limiares: 2,0 e divergencia, 1,5 e atencao."""
        assert conferir_profundidade(2 * LIMIAR_DE_DIVERGENCIA, 1.0)[0] == DIVERGENCIA
        assert conferir_profundidade(2 * LIMIAR_DE_ATENCAO, 1.0)[0] == ATENCAO
        assert conferir_profundidade(2 * (LIMIAR_DE_ATENCAO - 0.01), 1.0)[0] == CONCORDA

    def test_a_razao_e_meioses_sobre_dois_vezes_o_kit(self):
        estado, razao, documentais = conferir_profundidade(20, 4.77)
        assert (estado, documentais) == (DIVERGENCIA, 10.0)
        assert razao == pytest.approx(10.0 / 4.77)


class TestONoDaProfundidadeSugerida:
    """O ponto do caminho que o DNA sugere — sempre um no que JA estava la."""

    CAMINHO = ["raiz", "pai", "avo", "bisavo", "tataravo", "match"]
    # indice do ancestral = 3 ("bisavo")

    def test_devolve_o_no_k_geracoes_acima_do_match(self):
        """Subindo do match, que e o ULTIMO no do caminho."""
        assert no_na_profundidade_sugerida(self.CAMINHO, 3, 1.0) == "tataravo"
        # Com o ancestral em "avo", duas geracoes acima do match caem em "bisavo".
        assert no_na_profundidade_sugerida(self.CAMINHO, 2, 2.0) == "bisavo"

    def test_no_proprio_ancestral_nao_ha_o_que_marcar(self):
        """Se o DNA concorda com a arvore, o ponto sugerido E o ancestral comum."""
        assert no_na_profundidade_sugerida(self.CAMINHO, 3, 3.0) is None
        # Com o ancestral em "avo" (indice 2), o match esta a 3 geracoes dele.
        assert no_na_profundidade_sugerida(self.CAMINHO, 2, 3.0) is None

    def test_acima_do_ancestral_o_gedcom_nao_alcanca(self):
        assert no_na_profundidade_sugerida(self.CAMINHO, 3, 5.0) is None

    def test_o_match_nao_e_ancestral_de_si_mesmo(self):
        """`round(0.4)` e 0: o ponto sugerido cairia no proprio match."""
        assert no_na_profundidade_sugerida(self.CAMINHO, 3, 0.4) is None

    def test_sem_dado_nao_inventa_no(self):
        assert no_na_profundidade_sugerida(self.CAMINHO, 3, None) is None
        assert no_na_profundidade_sugerida([], 3, 2.0) is None

    def test_nunca_devolve_id_fora_do_caminho(self):
        for geracoes in (x / 2 for x in range(-4, 30)):
            resultado = no_na_profundidade_sugerida(self.CAMINHO, 3, geracoes)
            assert resultado is None or resultado in self.CAMINHO


class TestOAviso:
    """O texto para o operador."""

    def test_silencio_quando_nao_ha_o_que_dizer(self):
        assert aviso_da_profundidade(CONCORDA, "a", "b", 3.0, 2.5, 1.2) == ""
        assert aviso_da_profundidade(SEM_DADO, "a", "b", None, None, None) == ""

    def test_o_numero_sai_com_virgula_como_o_resto_da_tela(self):
        texto = aviso_da_profundidade(DIVERGENCIA, "Eline", "Eline C.", 10.0, 4.77, 2.1)
        assert "10,0 gerações" in texto
        assert "4,77 gerações" in texto
        assert "2,1× menos" in texto
        assert "10.0" not in texto, "ponto decimal vazou para a tela"

    def test_divergencia_e_atencao_dizem_coisas_diferentes(self):
        divergencia = aviso_da_profundidade(DIVERGENCIA, "a", "b", 10.0, 4.77, 2.1)
        atencao = aviso_da_profundidade(ATENCAO, "a", "b", 9.0, 4.8, 1.88)
        assert divergencia != atencao
        assert "dobro" in divergencia
        assert "dobro" not in atencao, "a atencao nao pode afirmar o que so a divergencia afirma"


class TestO_Dado_Do_Kit:
    """A coluna `MRCA` que o fluxo lia e descartava."""

    @pytest.mark.parametrize("cabecalho", ["MRCA", "mrca", "MRCA (generations)"])
    def test_a_coluna_e_encontrada_por_variacao_de_cabecalho(self, cabecalho):
        import pandas as pd
        df = pd.DataFrame({"Name": ["Ana Silva Souza"], "cM": [25.4], cabecalho: [4.77]})
        assert detect_segment_columns(df)["mrca"] == cabecalho

    def test_sem_a_coluna_o_kit_fica_sem_estimativa(self):
        import pandas as pd
        df = pd.DataFrame({"Name": ["Ana Silva Souza"], "cM": [25.4]})
        evidencias, _avisos = build_genetic_evidence(df)
        kit = next(iter(next(iter(evidencias.values())).values()))
        assert kit["mrca_generations"] is None
        assert kit["mrca_divergent"] is False

    def test_a_estimativa_do_kit_e_a_media_das_linhas(self):
        import pandas as pd
        df = pd.DataFrame({"Name": ["Ana Silva Souza"] * 2, "cM": [7.1, 18.3],
                           "Kit number": ["AA1234567"] * 2, "MRCA": [4.0, 5.0]})
        evidencias, _avisos = build_genetic_evidence(df)
        kit = next(iter(next(iter(evidencias.values())).values()))
        assert kit["mrca_generations"] == 4.5
        assert kit["mrca_divergent"] is True

    def test_linhas_com_estimativas_diferentes_avisam(self):
        """Medido no arquivo real: 0 dos 270 kits divergem. A guarda fica para quando divergir."""
        import pandas as pd
        df = pd.DataFrame({"Name": ["Ana Silva Souza"] * 2, "cM": [7.1, 18.3],
                           "Kit number": ["AA1234567"] * 2, "MRCA": [4.0, 5.0]})
        _ev, avisos = build_genetic_evidence(df)
        assert any(a["code"] == "mrca_divergente" for a in avisos), (
            "o cM somado misturaria profundidades estimadas diferentes sem avisar"
        )

    def test_a_hipotese_do_kit_carrega_a_estimativa(self):
        """Sem isto o confronto nao tem o numero para dizer o que a falta de faixa deixa aberto."""
        evidencia = {"available": True, "kits": [{"kit": "AA1", "total_cm": 25.4,
                                                  "mrca_generations": 4.77,
                                                  "segment_count": 1,
                                                  "largest_segment_cm": 25.4}]}
        blocos = hypotheses_for_evidence(evidencia)
        assert blocos[0]["mrca_generations"] == 4.77


class TestO_Desenho:
    """`anotar_profundidade`: as marcas no Mermaid ja pronto."""

    BASE = ('flowchart BT\n'
            'N_raiz["Raiz"]\n'
            'N_anc_esp["Ancestral &amp; Conjuge"]\n'
            'N_raiz --> N_anc_esp\n'
            'style N_raiz fill:#e8f5e9,stroke:#66bb6a,stroke-width:2px\n'
            'style N_anc_esp fill:#fff9c4,stroke:#fbc02d,stroke-width:2px')

    ANOTACAO = {"estado": DIVERGENCIA, "geracoes_documentais": 10.0,
                "geracoes_do_kit": 4.77, "razao": 2.1, "no_sugerido": "alvo"}

    def test_o_ancestral_perde_o_amarelo_liso_e_ganha_tracejado(self):
        saida = anotar_profundidade(self.BASE, self.ANOTACAO)
        assert "style N_anc_esp fill:#fff9c4,stroke:#c62828" in saida
        assert "stroke-dasharray" in saida
        assert "style N_anc_esp fill:#fff9c4,stroke:#fbc02d" not in saida, (
            "o estilo antigo ficou: as duas regras brigariam e a ultima venceria"
        )

    def test_marca_o_no_sugerido_com_contorno_proprio(self):
        saida = anotar_profundidade(self.BASE, self.ANOTACAO)
        assert "style N_alvo" in saida
        assert "#8e24aa" in saida, "o no sugerido precisa de cor propria, e nao a do ancestral"

    def test_o_desenho_so_recebe_estilo_e_nunca_texto(self):
        """A frase da profundidade vive na legenda; aqui so entram linhas `style`.

        Antes esta funcao emitia tambem um no de texto (`N_profundidade`), e ele saiu: num
        `flowchart` toda caixa parece um parente. A guarda fica para que ele nao volte.
        """
        saida = anotar_profundidade(self.BASE, self.ANOTACAO)
        # `diff` por linha, e nao por tamanho: o ancestral nao ganha uma linha nova, ele tem
        # a linha de estilo SUBSTITUIDA — entao o prefixo do texto muda de tamanho.
        novas = [linha for linha in saida.splitlines()
                 if linha not in self.BASE.splitlines()]
        assert novas, "nada foi anotado"
        assert all(linha.startswith("style ") for linha in novas), (
            f"o diagrama ganhou linha que nao e estilo: {novas}"
        )

    def test_sem_o_estilo_de_ancestral_nada_e_anotado(self):
        """O diagrama indireto nao tem esse estilo; anotar metade seria pior que nao anotar."""
        indireto = 'flowchart BT\nN_a["A"] --> N_b["B"]'
        assert anotar_profundidade(indireto, self.ANOTACAO) == indireto

    def test_sem_anotacao_o_diagrama_sai_intacto(self):
        assert anotar_profundidade(self.BASE, None) == self.BASE


class TestANaTela:
    """O caminho de producao: GEDCOM sintetico + CSV com `MRCA`, pelo POST real."""

    def test_divergencia_marca_o_cartao(self, cliente_de_upload):
        _app, _cliente, pasta = cliente_de_upload
        resultados = _rodar(pasta, 1.4)   # 3,0 / 1,4 = 2,14
        assert resultados, "a analise nao devolveu cartao"
        cartao = resultados[0]
        assert cartao["profundidade"] == DIVERGENCIA
        assert cartao["geracoes_documentais"] == pytest.approx(3.0)
        assert cartao["geracoes_do_kit"] == 1.4
        assert cartao["profundidade_aviso"], "a divergencia saiu sem texto"
        assert "style N_G2B" in cartao["mermaid_data"], (
            "o no na profundidade sugerida nao foi marcado no diagrama"
        )

    def test_atencao_marca_mais_fraco(self, cliente_de_upload):
        _app, _cliente, pasta = cliente_de_upload
        resultados = _rodar(pasta, 1.6)   # 3,0 / 1,6 = 1,875
        assert resultados[0]["profundidade"] == ATENCAO

    def test_concordancia_nao_marca_nada(self, cliente_de_upload):
        _app, _cliente, pasta = cliente_de_upload
        cartao = _rodar(pasta, 2.5)[0]    # 3,0 / 2,5 = 1,20
        assert cartao["profundidade"] == CONCORDA
        assert cartao["profundidade_aviso"] == ""
        assert "stroke-dasharray" not in (cartao["mermaid_data"] or ""), (
            "cartao em concordancia ganhou marca de divergencia"
        )

    def test_sem_a_coluna_mrca_o_estado_e_sem_dado(self, cliente_de_upload):
        """O CSV antigo (sem `MRCA`) nao pode virar suspeita: nao saber nao e divergir."""
        _app, _cliente, pasta = cliente_de_upload
        cartao = _rodar(pasta, None)[0]
        assert cartao["profundidade"] == SEM_DADO
        assert cartao["geracoes_do_kit"] is None

    def test_a_contradicao_do_selo_morreu_na_raiz(self, cliente_de_upload):
        """A regra do adendo 016 elimina a contradicao em vez de rotula-la.

        Antes: o cabecalho dizia "Compatível" e o aviso logo abaixo dizia "233 anos", e o selo
        combinado (`possível no cM, identidade impossível`) resolvia o rotulo. Agora, com a
        janela impossivel, **a comparacao de cM nem acontece** — o confronto responde o que
        responde para cartao sem caminho. Nao ha o que contradizer, entao nao ha selo
        combinado a emitir.
        """
        _app, _cliente, pasta = cliente_de_upload
        cartao = _rodar(pasta, 2.5, nascimento_do_match="1700")[0]

        assert cartao["janela_de_vida"] == "impossivel"
        assert cartao["comparison"]["status"] == "INCONCLUSIVO"
        assert cartao["comparison"]["expected_range"] is None, (
            "o cM voltou a ser comparado com um parentesco que a regra retirou da tela"
        )
        assert cartao["confrontacao_efetiva"] == "INCONCLUSIVO"
        assert cartao["confrontacao_rotulo"] == cartao["comparison"]["label"]

    def test_sem_data_a_janela_fica_calada_e_o_selo_e_o_do_confronto(self, cliente_de_upload):
        _app, _cliente, pasta = cliente_de_upload
        cartao = _rodar(pasta, 2.5)[0]
        assert cartao["janela_de_vida"] == "sem_data"
        assert cartao["confrontacao_efetiva"] == cartao["comparison"]["status"]
        assert cartao["confrontacao_rotulo"] == cartao["comparison"]["label"]


class TestOSilencioVirouAchado:
    """Item 3: o texto dos cartoes sem faixa publicada. O veredito NAO muda."""

    def _comparar(self, meioses, chave, mrca=4.77):
        documental = {"status": "found", "path": {"ids": ["x", "y"]},
                      "relationship_key": chave, "meioses": meioses,
                      "label": f"parentesco de teste ({meioses} meioses)"}
        bloco = {"kit": "AA1", "total_cm": 19.2, "possible_relationships": [],
                 "mrca_generations": mrca}
        return compare(documental, [bloco], {"available": True})

    def test_alem_do_alcance_da_fonte_o_texto_nomeia_o_limite(self):
        limite = meioses_maximo_publicado()
        resultado = self._comparar(limite + 4, "8C2R")
        assert resultado["status"] == "INCONCLUSIVO", "os quatro estados sao contrato"
        assert "mais profunda" in resultado["detail"]
        assert str(limite) in resultado["detail"]

    def test_lacuna_da_tabela_diz_os_vizinhos_e_nao_empresta_janela(self):
        """13 e 15 meioses nao tem linha publicada; as vizinhas sao 12/14 e 14/16."""
        publicados = meioses_publicados()
        assert 13 not in publicados and 15 not in publicados
        resultado = self._comparar(15, "5C3R")
        assert resultado["status"] == "INCONCLUSIVO"
        assert "não publica faixa para 15 meioses" in resultado["detail"]
        assert "14 e 16" in resultado["detail"]
        assert "nenhuma janela foi emprestada por proximidade" in resultado["detail"]

    def test_a_estimativa_do_kit_entra_nas_observacoes(self):
        resultado = self._comparar(20, "8C2R", mrca=4.77)
        juntas = " ".join(resultado["observations"])
        assert "4,77 gerações" in juntas, "o numero do proprio kit nao chegou ao operador"
        assert "10,0 gerações" in juntas
        assert "aviso de profundidade" in juntas, (
            "sem a remissao, o operador le o mesmo numero duas vezes sem saber que e o mesmo"
        )

    def test_sem_estimativa_do_kit_o_texto_nao_inventa_numero(self):
        resultado = self._comparar(20, "8C2R", mrca=None)
        juntas = " ".join(resultado["observations"])
        assert "gerações até o MRCA deste kit" not in juntas
        assert "mais profunda" in resultado["detail"], "a razao estrutural se perdeu"


class TestOResumo:
    """A leitura curta do diagrama — a que saiu de dentro do grafo.

    Ela nasceu como um no solto do `flowchart`. Num grafo toda caixa parece um parente, e o
    operador que ve uma caixa espera que ela seja pessoa ou vinculo: agora e texto, na
    legenda. O conteudo nao mudou — estes testes prendem que ele continua legivel e que
    NENHUM texto voltou para dentro do diagrama.
    """

    def test_silencio_quando_nao_ha_o_que_dizer(self):
        assert resumo_da_profundidade(CONCORDA, 3.0, 2.5) == ""
        assert resumo_da_profundidade(SEM_DADO, None, None) == ""
        assert resumo_da_profundidade(ATENCAO, None, 4.0) == ""
        assert resumo_da_profundidade(ATENCAO, 7.5, None) == ""

    def test_o_numero_sai_com_virgula_e_a_frase_e_a_mesma_do_grafo(self):
        """O texto mudou de LUGAR, e nao de conteudo: e o mesmo que o no mostrava."""
        texto = resumo_da_profundidade(ATENCAO, 7.5, 4.35)
        assert texto == ("Confira a profundidade: a árvore afirma 7,5 gerações até o ancestral "
                         "comum; este kit estima 4,3.")
        assert resumo_da_profundidade(DIVERGENCIA, 10.0, 4.77) == (
            "Elo documental não confirmado pelo DNA: a árvore afirma 10,0 gerações até o "
            "ancestral comum, e este kit estima 4,8.")

    def test_sai_acentuado_e_legivel(self):
        texto = resumo_da_profundidade(ATENCAO, 7.5, 4.35)
        assert "árvore" in texto and "gerações" in texto and "até" in texto
        assert "7.5" not in texto and "4.35" not in texto, "ponto decimal vazou"

    def test_o_diagrama_nao_carrega_texto_nenhum(self):
        """A guarda contra a regressao: nenhum no de texto volta para o desenho."""
        base = ('flowchart BT\n'
                'N_raiz["Raiz"]\n'
                'N_anc["Ancestral"]\n'
                'N_alvo["Alvo"]\n'
                'N_raiz --> N_anc\n'
                'style N_raiz fill:#e8f5e9,stroke:#66bb6a,stroke-width:2px\n'
                'style N_anc fill:#fff9c4,stroke:#fbc02d,stroke-width:2px')
        saida = anotar_profundidade(base, {"estado": DIVERGENCIA, "geracoes_documentais": 10.0,
                                           "geracoes_do_kit": 4.77, "razao": 2.1,
                                           "no_sugerido": "alvo"})
        assert "N_profundidade" not in saida, "o no de texto voltou para dentro do diagrama"
        assert "geraç" not in saida, "o desenho ganhou frase: toda caixa parece um parente"
        assert "afirma" not in saida
        for linha in saida.splitlines():
            if linha.startswith("style"):
                continue
            rotulos = re.findall(r'\["([^"]*)"\]', linha)
            assert all(r in ("Raiz", "Ancestral", "Alvo") for r in rotulos), (
                f"o desenho ganhou um no que nao e pessoa do caminho: {rotulos}"
            )


class TestO_Acoplamento_Com_A_Tela:
    """O que quebra em silencio entre o nucleo e o template."""

    FOLHA = os.path.join(_RAIZ, "src", "assets", "app.css")
    TEMPLATE = os.path.join(_RAIZ, "src", "templates", "index.html")

    @pytest.mark.parametrize("classe", ["profundidade-divergencia", "profundidade-atencao",
                                        "alerta-profundidade", "legenda-do-grafo",
                                        "legenda-titulo", "legenda-raiz", "legenda-match",
                                        "legenda-ancestral", "legenda-ancestral-nao-sustentado",
                                        "legenda-sugerido", "legenda-neutro",
                                        "legenda-informativa"])
    def test_a_classe_do_template_existe_na_folha(self, classe):
        with open(self.FOLHA, encoding="utf-8") as arquivo:
            folha = arquivo.read()
        assert f".{classe}" in folha, (
            f"a folha perdeu `.{classe}`: o selo fica sem cor e o texto some no fundo"
        )

    def test_o_template_le_os_campos_que_o_nucleo_produz(self):
        with open(self.TEMPLATE, encoding="utf-8") as arquivo:
            template = arquivo.read()
        for campo in ("result.profundidade", "result.profundidade_aviso",
                      "result.confrontacao_efetiva", "result.profundidade_no_sugerido",
                      "result.profundidade_resumo"):
            assert campo in template, f"o template deixou de ler `{campo}`"


# ---------------------------------------------------------------------------
# A LEGENDA DO DIAGRAMA.
#
# O risco desta legenda nao e ela sumir: e ela MENTIR. Ela descreve cores que sao emitidas em
# outro lugar — quatro literais em `reporting/mermaid_render.py` e dois no
# `mermaid.initialize` do template. Uma legenda que descreve cores que o desenho nao tem e
# pior que legenda nenhuma, porque o operador confia nela. Por isso as amostras sao presas
# contra a SAIDA REAL, e nao contra uma copia dos valores escrita no teste.
# ---------------------------------------------------------------------------
FOLHA_DO_PROJETO = os.path.join(_RAIZ, "src", "assets", "app.css")
TEMPLATE_DO_PROJETO = os.path.join(_RAIZ, "src", "templates", "index.html")


def _amostra(nome: str):
    """`(fundo, borda)` da amostra da legenda, lidos da folha de estilo."""
    with open(FOLHA_DO_PROJETO, encoding="utf-8") as arquivo:
        folha = arquivo.read()
    bloco = re.search(r"\.%s\{([^}]*)\}" % re.escape(nome), folha)
    assert bloco, f"a folha perdeu a amostra `.{nome}`"
    fundo = re.search(r"background:(#[0-9A-Fa-f]{6})", bloco.group(1))
    borda = re.search(r"border-color:(#[0-9A-Fa-f]{6})", bloco.group(1))
    assert fundo and borda, (
        f"a amostra `.{nome}` deixou de usar cor literal: cor de tema na legenda nao "
        "corresponderia ao desenho, que e renderizado sobre fundo branco nos dois temas"
    )
    return fundo.group(1).lower(), borda.group(1).lower()


def _cores_emitidas(mermaid: str) -> dict:
    """`{no: (fundo, borda)}` a partir do Mermaid realmente emitido."""
    return {m.group(1): (m.group(2).lower(), m.group(3).lower())
            for m in re.finditer(
                r"^style (\S+) fill:(#[0-9A-Fa-f]{6}),stroke:(#[0-9A-Fa-f]{6})",
                mermaid, re.M)}


class TestAsCoresDaLegenda:
    """Cada amostra da legenda tem de ser a cor que o desenho realmente pinta."""

    BASE = ('flowchart BT\n'
            'N_raiz["Raiz"]\n'
            'N_anc["Ancestral"]\n'
            'N_alvo["Alvo"]\n'
            'N_raiz --> N_anc\n'
            'style N_raiz fill:#e8f5e9,stroke:#66bb6a,stroke-width:2px\n'
            'style N_anc fill:#fff9c4,stroke:#fbc02d,stroke-width:2px')

    ANOTACAO = {"estado": DIVERGENCIA, "geracoes_documentais": 10.0,
                "geracoes_do_kit": 4.77, "razao": 2.1, "no_sugerido": "alvo"}

    def _emitidas_no_caminho_direto(self) -> dict:
        """As cores dos dois extremos e do ancestral, pelo renderizador de verdade."""
        from reporting.mermaid_render import generate_mermaid_graph
        people = {"a": {"name": "Raiz"}, "b": {"name": "Ancestral"},
                  "c": {"name": "Meio"}, "d": {"name": "Match"}}
        dominio = {"get_name": lambda pessoa: pessoa.get("name", ""),
                   "people": people,
                   "get_spouses": lambda _pid: []}
        return _cores_emitidas(
            generate_mermaid_graph(["a", "b", "c", "d"], "a", "d", "b", dominio))

    def test_os_dois_extremos_e_o_ancestral(self):
        emitidas = self._emitidas_no_caminho_direto()
        assert _amostra("legenda-raiz") == emitidas["N_a"]
        assert _amostra("legenda-match") == emitidas["N_d"]
        assert _amostra("legenda-ancestral") == emitidas["N_b"]

    def test_as_marcas_da_profundidade(self):
        """So os NOS sao marcados: a frase da profundidade nao entra no desenho."""
        emitidas = _cores_emitidas(anotar_profundidade(self.BASE, self.ANOTACAO))
        assert _amostra("legenda-ancestral-nao-sustentado") == emitidas["N_anc"]
        assert _amostra("legenda-sugerido") == emitidas["N_alvo"]
        assert "N_profundidade" not in emitidas, (
            "o no de texto voltou: a frase tem de ficar na legenda, e nao no grafo"
        )

    def test_a_amostra_sem_destaque_bate_com_o_tema_do_mermaid(self):
        """O no comum nao tem `style` nenhum: quem o pinta e o `themeVariables`."""
        with open(TEMPLATE_DO_PROJETO, encoding="utf-8") as arquivo:
            template = arquivo.read()
        tema = re.search(r"primaryColor:\s*'(#[0-9A-Fa-f]{6})',\s*"
                         r"primaryBorderColor:\s*'(#[0-9A-Fa-f]{6})'", template)
        assert tema, "o `themeVariables` do Mermaid mudou de forma"
        assert _amostra("legenda-neutro") == (tema.group(1).lower(), tema.group(2).lower())

    def test_as_marcas_da_legenda_sao_distintas_entre_si(self):
        """Amostras iguais nao distinguiriam nada."""
        amostras = [_amostra(nome) for nome in
                    ("legenda-raiz", "legenda-match", "legenda-ancestral",
                     "legenda-ancestral-nao-sustentado", "legenda-sugerido",
                     "legenda-neutro")]
        assert len(set(amostras)) == len(amostras), f"amostras repetidas: {amostras}"

    def test_o_ancestral_muda_de_forma_e_nao_de_item(self):
        """Com o elo nao sustentado, a amostra mantem o amarelo e muda a borda."""
        fundo_normal, borda_normal = _amostra("legenda-ancestral")
        fundo_marcado, borda_marcada = _amostra("legenda-ancestral-nao-sustentado")
        assert fundo_normal == fundo_marcado, (
            "as duas amostras do ancestral precisam do MESMO fundo: sao o mesmo no, "
            "marcado ou nao"
        )
        assert borda_normal != borda_marcada


def _pagina(cliente, pasta, mrca, nascimento=None) -> str:
    """O HTML do estado de resultado, pelo caminho de producao.

    Grava os arquivos na pasta de upload com a FORMA de chave que o armazenamento valida
    (`16hex__nome`) e faz o POST real: montar o payload a mao mediria o template contra uma
    forma que ninguem produz.
    """
    _rodar(pasta, mrca, nascimento)
    return cliente.post("/", data={
        "action": "dna_analysis",
        "gedcom_filename": NOME_GED,
        "matches_csv_filename": NOME_CSV,
        "root_name": RAIZ,
    }).get_data(as_text=True)


class TestALegendaNaTela:
    """A legenda e contextual: descreve o que ESTE diagrama tem, nem mais nem menos."""

    def _pagina(self, cliente, pasta, mrca, nascimento=None) -> str:
        return _pagina(cliente, pasta, mrca, nascimento)

    @staticmethod
    def _itens(pagina: str) -> list:
        bloco = re.search(r'(?s)<div class="legenda-do-grafo">(.*?)</div>', pagina)
        assert bloco, "a legenda do diagrama nao esta na tela"
        return re.findall(r"(?s)<li>(.*?)</li>", bloco.group(1))

    @staticmethod
    def _bloco_informativo(pagina: str) -> str:
        achado = re.search(r'(?s)<p class="legenda-informativa">(.*?)</p>', pagina)
        return " ".join(achado.group(1).split()) if achado else ""

    def test_sem_divergencia_a_legenda_ainda_explica_as_tres_cores_base(self, cliente_de_upload):
        """Verde, vermelho e amarelo existem em TODO diagrama e nao estavam explicados."""
        _app, cliente, pasta = cliente_de_upload
        pagina = self._pagina(cliente, pasta, 2.5)
        itens = self._itens(pagina)
        texto = " ".join(" ".join(i.split()) for i in itens)
        assert len(itens) == 4, f"itens: {texto}"
        assert "ponto de partida" in texto
        assert "relatório de DNA indicou" in texto
        assert "ancestral comum que o GEDCOM afirma" in texto
        assert "Sem destaque" in texto
        assert "legenda-ancestral-nao-sustentado" not in texto
        assert self._bloco_informativo(pagina) == "", (
            "sem divergencia nao ha leitura a fazer: o bloco informativo tem de sumir"
        )

    def test_a_legenda_nomeia_as_pessoas_do_cartao(self, cliente_de_upload):
        _app, cliente, pasta = cliente_de_upload
        texto = " ".join(self._itens(self._pagina(cliente, pasta, 2.5)))
        assert RAIZ in texto, "a legenda nao diz quem e a caixa verde"
        assert "Ana Silva Souza" in texto, "a legenda nao diz quem e a caixa vermelha"

    def test_a_atencao_marca_mais_fraco_no_texto_e_nao_no_desenho(self, cliente_de_upload):
        """O desenho marca o ancestral nos dois estados; o que muda e a AFIRMACAO.

        A anotacao cobre `atencao` e `divergencia` — a marca roxa e a mesma. Dizer "elo que
        o DNA nao sustenta" na atencao seria afirmar o que so a divergencia afirma, e o
        alerta do cartao ja usa o verbo mais cauteloso ("a conferir").
        """
        _app, cliente, pasta = cliente_de_upload
        pagina = self._pagina(cliente, pasta, 1.6)
        itens = self._itens(pagina)
        texto = " ".join(itens)
        assert len(itens) == 5, f"itens: {texto}"
        assert "legenda-ancestral-nao-sustentado" in texto
        assert "diferença de profundidade a conferir" in texto
        assert "não sustenta" not in texto, "a atencao afirmou o que so a divergencia afirma"
        assert "legenda-sugerido" in texto

    def test_a_divergencia_acrescenta_o_roxo(self, cliente_de_upload):
        _app, cliente, pasta = cliente_de_upload
        itens = self._itens(self._pagina(cliente, pasta, 1.4))
        texto = " ".join(itens)
        assert len(itens) == 5
        assert "legenda-sugerido" in texto
        assert "nada foi inventado no meio" in texto

    def test_a_leitura_da_profundidade_e_bloco_de_texto_e_nao_no_do_grafo(self, cliente_de_upload):
        """O pedido que originou esta mudanca: a frase sai do desenho e vira texto.

        Dentro de um `flowchart` toda caixa parece um parente, e o operador que ve uma caixa
        no grafo espera que ela seja uma pessoa ou um vinculo. A frase passa a ser um bloco
        na legenda, e o desenho nao carrega texto nenhum.
        """
        _app, cliente, pasta = cliente_de_upload
        pagina = self._pagina(cliente, pasta, 1.6)
        bloco = self._bloco_informativo(pagina)
        assert bloco, "a leitura da profundidade sumiu em vez de mudar de lugar"
        assert "O que os números mostram." in bloco
        assert "Confira a profundidade: a árvore afirma 3,0 gerações" in bloco
        assert "4,3" in bloco or "1,6" in bloco

        # e o grafo nao ficou com o no de texto
        grafo = re.search(r'(?s)<div class="mermaid">(.*?)</div>', pagina).group(1)
        assert "N_profundidade" not in grafo
        assert "afirma" not in grafo, "o desenho ganhou a frase de volta"
        assert "geraç" not in grafo

    def test_o_roxo_nao_entra_na_legenda_se_o_desenho_nao_o_tem(self, cliente_de_upload):
        """O caso adversarial: divergencia sem no na profundidade sugerida.

        Com 0,4 geracoes estimadas, `round` da 0 — o ponto sugerido cairia no proprio match,
        e o diagrama sai com o ancestral marcado mas SEM marca roxa. A legenda nao pode
        descrever uma cor ausente.
        """
        _app, cliente, pasta = cliente_de_upload
        cartao = _rodar(pasta, 0.4)[0]
        assert cartao["profundidade"] == DIVERGENCIA, "o cenario perdeu a divergencia"
        assert cartao["profundidade_no_sugerido"] is None
        assert "#8e24aa" not in cartao["mermaid_data"], "o desenho ganhou marca roxa"

        pagina = cliente.post("/", data={
            "action": "dna_analysis", "gedcom_filename": NOME_GED,
            "matches_csv_filename": NOME_CSV, "root_name": RAIZ,
        }).get_data(as_text=True)
        itens = self._itens(pagina)
        texto = " ".join(itens)
        assert "#fff9c4,stroke:#c62828" in pagina.replace(" ", ""), (
            "o ancestral deixou de ser marcado: o cenario nao testa o que eu quero"
        )
        assert "legenda-sugerido" not in texto, (
            "a legenda lista uma cor que o desenho nao tem"
        )
        assert len(itens) == 4, "sem a marca roxa sobram os quatro itens base"



class TestOCartaoDoDoadorImpossivel:
    """A REGRA: idade acima de 122 veta o parentesco. Adendo 016.

    ## A regra

    Quando a janela de vida e `impossivel`, o cartao passa a ser tratado como o grupo
    "Parentesco documental nao encontrado", **com todas as regras desse grupo**, e o diagrama
    e desconsiderado. O corte e o `impossivel` (> `IDADE_IMPOSSIVEL`); `suspeita` (105-122)
    continua avisando e mantendo o parentesco.

    ## O que ela custa, medido e declarado

    A arvore **tem** o caminho — 11, 12 e 10 meioses nos 3 cartoes alcancados hoje —, entao
    apresentar como "nao encontrado" diz algo **falso sobre a arvore**, e o efeito pratico e
    mandar o operador procurar registro faltando quando o trabalho e procurar homonimo. Custo
    medido: a unica comparacao de cM da analise (`TG8027863`, que sai de COMPATIVEL para
    INCONCLUSIVO) e 1 dos 5 cartoes que apontam para o mesmo ancestral. A decisao e do
    operador e esta no `_reversa_sdd/addenda/016`.

    ## O que ela NAO faz

    Nao destroi o dado: o parentesco original vai para `documentary_do_registro`, fora da
    tela, e e o que permite auditar a regra e reverte-la sem recarregar a arvore.
    """

    def _com_janela_impossivel(self, cliente_de_upload) -> str:
        _app, cliente, pasta = cliente_de_upload
        return _pagina(cliente, pasta, 2.5, "1700")

    def _sem_janela_impossivel(self, cliente_de_upload) -> str:
        _app, cliente, pasta = cliente_de_upload
        return _pagina(cliente, pasta, 2.5)

    def test_acima_de_122_o_cartao_vira_nao_encontrado(self, cliente_de_upload):
        _app, cliente, pasta = cliente_de_upload
        cartao = _rodar(pasta, 2.5, "1700")[0]
        assert cartao["janela_de_vida"] == "impossivel"
        assert cartao["documentary"]["status"] == "not_found"
        assert cartao["documentary"]["label"] == "Parentesco documental não encontrado"

    def test_o_parentesco_e_o_diagrama_saem_da_tela(self, cliente_de_upload):
        _app, cliente, pasta = cliente_de_upload
        cartao = _rodar(pasta, 2.5, "1700")[0]
        assert cartao["documentary"]["path"] is None
        assert cartao["documentary"]["meioses"] is None
        assert cartao["documentary"]["common_ancestor"] is None
        assert cartao["mermaid_data"] is None, "o diagrama nao foi desconsiderado"
        assert cartao["text_path"] == ""

    def test_o_parentesco_original_fica_guardado_fora_da_tela(self, cliente_de_upload):
        """Nao destruir o dado e o que permite auditar a regra e reverte-la."""
        _app, cliente, pasta = cliente_de_upload
        cartao = _rodar(pasta, 2.5, "1700")[0]
        original = cartao["documentary_do_registro"]
        assert original is not None, "o parentesco retirado nao foi guardado"
        assert (original.get("path") or {}).get("ids"), "o caminho se perdeu"
        assert original["meioses"], "as meioses se perderam"
        assert original["common_ancestor"], "o ancestral comum se perdeu"

    def test_o_confronto_segue_o_grupo(self, cliente_de_upload):
        _app, cliente, pasta = cliente_de_upload
        cartao = _rodar(pasta, 2.5, "1700")[0]
        assert cartao["comparison"]["status"] == "INCONCLUSIVO"
        assert "nenhum caminho" in (cartao["comparison"]["detail"] or "")

    def test_suspeita_nao_veta_o_parentesco(self, cliente_de_upload):
        """105-122 avisa e mantem: a regra e do limite duro, e so dele."""
        _app, cliente, pasta = cliente_de_upload
        cartao = _rodar(pasta, 2.5, "1910")[0]     # 116 anos em 2026
        assert cartao["janela_de_vida"] == "suspeita"
        assert cartao["documentary"]["status"] == "found"
        assert (cartao["documentary"]["path"] or {}).get("ids")
        assert cartao["mermaid_data"], "o diagrama sumiu num cartao que apenas avisa"
        assert cartao["documentary_do_registro"] is None

    def test_sem_data_nada_muda(self, cliente_de_upload):
        _app, cliente, pasta = cliente_de_upload
        cartao = _rodar(pasta, 2.5)[0]
        assert cartao["janela_de_vida"] == "sem_data"
        assert cartao["documentary"]["status"] == "found"
        assert cartao["documentary_do_registro"] is None

    def test_a_tela_nao_mostra_o_grafo_nem_o_caminho(self, cliente_de_upload):
        pagina = self._com_janela_impossivel(cliente_de_upload)
        assert "Parentesco documental não encontrado" in pagina
        assert 'class="mermaid"' not in pagina
        assert "flowchart BT" not in pagina, "o diagrama voltou para a tela"
        # O cartao suprimido sai IGUAL ao do grupo, inclusive nesta linha: o rotulo aparece
        # com "nenhum caminho encontrado". E o que "tratado como esse grupo" quer dizer.
        assert "Caminho genealógico no GEDCOM:" in pagina
        assert "nenhum caminho encontrado" in pagina

    def test_a_moldura_do_adendo_015_nao_aparece_mais(self, cliente_de_upload):
        """O veredicto, o selo e o recolhimento ficaram INATINGIVEIS sob a regra do 016.

        Eles existiam para dizer que o parentesco exibido era o do REGISTRO — e com a regra
        nao ha parentesco exibido. O codigo fica, declarado no template, porque a regra e
        reversivel numa linha de `core.dna_analysis`; este teste prende que ele nao aparece.
        """
        pagina = self._com_janela_impossivel(cliente_de_upload)
        assert "veredicto-do-doador" not in pagina
        assert "parentesco-do-registro" not in pagina
        # O `details` e a classe NAO aparecem; o nome ainda aparece no `<script>`, que fica.
        assert '<details class="grafo-do-registro"' not in pagina
        assert "não atribuível ao doador" not in pagina

    def test_sem_janela_impossivel_o_caminho_continua(self, cliente_de_upload):
        pagina = self._sem_janela_impossivel(cliente_de_upload)
        assert "Parentesco documental não encontrado" not in pagina
        assert 'class="mermaid"' in pagina
        assert "flowchart BT" in pagina

    def test_o_nucleo_exige_impossivel_e_caminho_para_vetar(self):
        """A guarda mora em `core.dna_analysis`, e nao no template — mas tem de existir."""
        caminho_nucleo = os.path.join(_RAIZ, "src", "core", "dna_analysis.py")
        with open(caminho_nucleo, encoding="utf-8") as arquivo:
            nucleo = arquivo.read()
        assert "if janela == IMPOSSIVEL and (documentary.get(\"path\") or {}).get(\"ids\")" in nucleo, (
            "a regra da janela de vida perdeu a guarda de caminho"
        )
        assert "documental_nao_encontrado(arvore, root_id, pid" in nucleo, (
            "a regra deixou de reaproveitar a forma do grupo 'nao encontrado'"
        )
        assert "documentary_do_registro" in nucleo, (
            "o parentesco retirado deixou de ser guardado: a regra ficaria irreversivel"
        )

    def test_o_js_do_recolhimento_continua_correto(self):
        """O recolhimento esta inatingivel, mas o JS que o sustenta fica correto."""
        with open(TEMPLATE_DO_PROJETO, encoding="utf-8") as arquivo:
            template = arquivo.read()
        assert 'closest("details:not([open])")' in template
        assert 'addEventListener("toggle"' in template

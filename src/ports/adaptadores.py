"""Adaptadores concretos das portas de `ports/` (`D-07`).

O adaptador **nao reimplementa a regra**: ele chama `utils/validate.py`, que
continua sendo a autoridade unica sobre o que pode ser gravado. Repetir a
derivacao de chave ou a validacao de conteudo aqui criaria uma segunda copia da
mesma regra, e as duas divergiriam no primeiro ajuste.

Nenhum adaptador levanta excecao de dominio. `validar_conteudo_gedcom` devolve
**motivo em texto**, e quem transforma o motivo na excecao de GEDCOM nao
reconhecido e o caso de uso `upload_gedcom` (`RF-03`, achado `A002`).

## `AnalisadorDeUpload` da `D-07` e `ArmazenamentoEmDisco` sao o mesmo papel

A `D-07` nomeia dois adaptadores concretos: `AnalisadorDeUpload` e
`ArmazenamentoEmDisco`, e descreve **os dois** como delegacoes para
`utils/validate.py` (chave por conteudo, nome armazenado, validacao de forma,
validacao de conteudo). Sao a mesma responsabilidade com dois nomes, e o `T007`
fixou um so: `ArmazenamentoEmDisco`. Nao existe componente faltando aqui — ver a
nota de execucao em `actions.md`.
"""
from __future__ import annotations

import os
from typing import TYPE_CHECKING

from parsers.gedcom_parser import Tree, carregar_arvore
from ports import EntradaArmazenada
from utils.validate import (
    chave_de_armazenamento,
    chave_recebida_e_valida,
    nome_do_arquivo_armazenado,
    referencia_de_arquivo_da_pasta,
    validar_conteudo_gedcom,
)

# Subpasta para onde `aposentar` move o arquivo (`RN-14`). Fica DENTRO da pasta de upload de
# proposito: `listar` ja ignora subdiretorio, entao o arquivo sai da lista sem que nenhum
# filtro novo precise ser escrito — e sem uma lista de excecoes que alguem teria de manter.
PASTA_DE_APOSENTADOS = "_aposentados"

if TYPE_CHECKING:
    # Import so para o checador de tipos. Em execucao a anotacao e string
    # (`from __future__ import annotations`) e o modulo nao precisa do nome.
    from . import AnaliseParaRegistrar


class ArmazenamentoEmDisco:
    """`ArmazenamentoDeArquivos` sobre a pasta de upload do processo.

    A pasta entra por parametro, e nao e lida do ambiente aqui dentro: quem
    resolve o caminho de upload e a borda (`src/app.py`), que ja responde a
    `ANALISADOR_UPLOAD_FOLDER` e ja garante que escrita e leitura usam o MESMO
    caminho. O adaptador nao sabe de ambiente nem de Flask.
    """

    def __init__(self, pasta: str):
        self._pasta = pasta

    def guardar(self, conteudo: bytes, nome_original: str | None, tipo: str,
                dono: str) -> tuple[str | None, str | None]:
        """Valida antes de gravar; devolve `(caminho, motivo)`.

        A ordem e a regra (`RF-10`): a validacao de conteudo acontece **antes** de
        qualquer escrita, e uma recusa nao deixa residuo na pasta. Tambem e aqui
        que o conteudo ja armazenado **nao** e regravado (`RF-09`) — a chave vem do
        conteudo, entao o mesmo envio reencontra o mesmo arquivo.

        `dono` e recebido e **NAO participa de decisao nenhuma** (`RF-02`): a
        chave continua vindo do conteudo, o nome armazenado continua
        `<chave>__<nome visivel>` e o caminho continua o mesmo. Usa-lo aqui — na
        chave ou no caminho — seria mudanca de comportamento observavel: dois
        envios do mesmo conteudo por donos diferentes deixariam de reencontrar o
        MESMO arquivo, e a paridade do armazenamento quebraria (`RN-02`). O
        parametro existe porque a Onda 3 o preenche, e nada mais.
        """
        motivo = validar_conteudo_gedcom(conteudo) if tipo == "gedcom" else None
        if motivo is not None:
            return None, motivo

        chave = chave_de_armazenamento(conteudo)
        nome_armazenado = nome_do_arquivo_armazenado(chave, nome_original)
        caminho = os.path.join(self._pasta, nome_armazenado)
        if not os.path.exists(caminho):
            with open(caminho, "wb") as destino:
                destino.write(conteudo)
        return caminho, None

    def resolver(self, referencia: str | None, dono: str) -> str | None:
        """Caminho completo do arquivo armazenado, ou `None`.

        A validacao de forma e o que impede um `gedcom_filename` manipulado de
        apontar para fora da pasta (BUG-20260929-QMLY, criterio 5), e ela vem
        antes de qualquer `os.path.exists`.

        `dono` e recebido e **ignorado**, pela mesma razao do `guardar`: a
        referencia continua sendo resolvida pela chave de conteudo, e nenhuma
        consulta e filtrada por dono. Ele chega por chamada do carregador de
        arvores, que o recebe da borda.
        """
        if not chave_recebida_e_valida(referencia):
            return None
        caminho = os.path.join(self._pasta, referencia)
        return caminho if os.path.exists(caminho) else None

    def listar(self, dono: str) -> list[EntradaArmazenada]:
        """Entradas da pasta: nome armazenado, bytes e data. **Nao abre arquivo.**

        Feature `011-escolher-arquivo-da-lista`, acao `T013` (`D-01`, `D-07`, `D-08`).

        ## O que ela le, e o que ela deliberadamente NAO le

        Do **diretorio**: o nome de cada entrada. Do **arquivo**: os atributos que o
        sistema de arquivos ja mantem — tamanho e data de modificacao —, por `os.stat`.
        Do **conteudo**: nada. Nao ha `open` aqui, e e por isso que a tela pode ser
        montada sem reler os 29 MB da pasta a cada renderizacao (RNF de desempenho).
        E tambem por isso que a extensao decide a aba, e nao o conteudo (`RN-09`).

        ## Pasta ausente devolve lista vazia, e nao excecao

        `D-07`. Uma instalacao nova tem a pasta criada e vazia; uma pasta que
        desapareca sob a aplicacao em execucao nao pode virar erro na tela de entrada.
        O `D-07` recusou o `os.makedirs` que seria o conserto obvio: criar diretorio
        dentro de uma leitura e efeito colateral escondido numa operacao que promete
        nao escrever nada. Por isso o `isdir` vem antes, e o retorno e `[]`.

        ## Nao filtra nada

        Nem por nome, nem por extensao, nem por forma da chave. Quem separa as abas e
        quem marca o item indisponivel e a funcao pura de `reporting/`, que decide pelo
        nome. Filtrar aqui esconderia do operador um arquivo que existe — e o `D-11`
        existe justamente para o item indisponivel aparecer **marcado**, em vez de
        desaparecer.

        Subdiretorio e ignorado: a pasta guarda arquivo, e um diretorio ali dentro nao
        tem referencia que o alcance. Desde a `RN-14` isso deixou de ser so higiene: e
        o que faz `aposentar` funcionar, porque o arquivo aposentado vai para
        `_aposentados/` e deixa de ser um arquivo desta pasta.

        `dono` e recebido e **ignorado**, como no `guardar` e no `resolver`. Ele nao
        filtra nada: as dividas #3 e #4 seguem abertas (`RN-06`), e a assimetria entre
        os tres metodos da porta seria o custo que a feature 007 pagou para nao ter.
        """
        if not os.path.isdir(self._pasta):
            return []

        entradas: list[EntradaArmazenada] = []
        for nome in os.listdir(self._pasta):
            caminho = os.path.join(self._pasta, nome)
            if not os.path.isfile(caminho):
                continue
            try:
                atributos = os.stat(caminho)
            except OSError:
                # Entrada que sumiu entre o listdir e o stat: a listagem e um retrato
                # do instante, e um arquivo que nao esta mais la nao vira excecao.
                continue
            entradas.append(EntradaArmazenada(
                nome=nome,
                bytes=atributos.st_size,
                modificado_em=atributos.st_mtime,
            ))
        return entradas

    def aposentar(self, referencia: str | None, dono: str) -> bool:
        """Move o arquivo para `<pasta>/_aposentados/` e devolve se moveu (`RN-14`).

        **Nao apaga nada**: o arquivo sai da lista e permanece no disco, inteiro e com
        o mesmo nome. Desfazer e mover de volta, e a pasta de aposentados fica dentro
        da propria pasta de upload justamente para isso.

        ## A defesa contra escape, em duas camadas

        1. `referencia_de_arquivo_da_pasta` recusa qualquer coisa que seja um CAMINHO
           em vez de um NOME (barra, barra invertida, byte nulo, `..`, vazio). Ela e
           deliberadamente mais permissiva que `chave_recebida_e_valida`: os arquivos
           **sem chave** da pasta real sao os inalcancaveis, e sao os que o operador
           mais quer tirar da lista — exigir a chave aqui os tornaria inapagaveis.
        2. `os.path.dirname` do caminho ja resolvido tem de ser **exatamente** a pasta
           de upload. A primeira camada ja garante isso; a segunda nao confia nela.
           E o mesmo espirito do `resolver`, que valida a forma antes de qualquer
           `os.path.exists` (`BUG-20260929-QMLY`, criterio 5).

        ## Nao sobrescreve um aposentado

        Se ja existir um aposentado com o mesmo nome, um sufixo numerico e acrescentado
        em vez de sobrescrever. Para os nomes COM chave isso seria inofensivo — o nome
        carrega o conteudo, entao os dois arquivos sao o mesmo dado —, mas para os nomes
        SEM chave o nome nao carrega conteudo nenhum, e sobrescrever apagaria um arquivo
        diferente. Como a `RN-07` proibe apagar, a escolha segura vale para os dois casos.

        `dono` e recebido e **ignorado**, como nos outros tres metodos da porta.
        """
        if not referencia_de_arquivo_da_pasta(referencia):
            return False

        origem = os.path.join(self._pasta, referencia)
        if os.path.dirname(os.path.abspath(origem)) != os.path.abspath(self._pasta):
            return False
        if not os.path.isfile(origem):
            return False

        destino_pasta = os.path.join(self._pasta, PASTA_DE_APOSENTADOS)
        os.makedirs(destino_pasta, exist_ok=True)
        destino = os.path.join(destino_pasta, referencia)
        if os.path.exists(destino):
            for sufixo in range(1, 100):
                alternativa = os.path.join(destino_pasta, f"{referencia}.{sufixo}")
                if not os.path.exists(alternativa):
                    destino = alternativa
                    break
            else:
                # Cem aposentados com o mesmo nome: desistir e melhor do que
                # sobrescrever um deles.
                return False

        os.replace(origem, destino)
        return True


class CarregadorDeArvoresGedcom:
    """`CarregadorDeArvores` sobre o parser de GEDCOM.

    Resolve a referencia pelo armazenamento recebido e chama `carregar_arvore`. E
    o **unico** lugar da fronteira que parseia: a rota entrega a referencia e
    recebe a arvore, e nenhum caso de uso importa `parsers/`.

    O `dono` que `carregar` recebe e repassado a `resolver` sem ser interpretado.
    Ele chega **por chamada**, e nao pelo construtor deste adaptador, porque o
    adaptador e um singleton de processo montado no import de `src/app.py`:
    congelar identidade nele seria o custo que a Onda 3 teria de desfazer.
    """

    def __init__(self, armazenamento: ArmazenamentoEmDisco):
        self._armazenamento = armazenamento

    def carregar(self, referencia: str, dono: str) -> Tree | None:
        caminho = self._armazenamento.resolver(referencia, dono)
        if caminho is None:
            return None
        return carregar_arvore(caminho)


class RegistroDeAnalisesPostgres:
    """`RegistroDeAnalises` sobre PostgreSQL (`D-03`, `D-04`, `D-05`).

    ## Nada acontece na construcao

    O construtor **so guarda a string de conexao**. Nao abre conexao, nao valida a
    URL e nao toca a rede (`D-02`) — e requisito, nao estilo. `src/app.py` e
    importado pela suite (`tests/conftest.py`) e pelo harness de paridade
    (`_reversa_sdd/parity/harness.py:356`), e uma conexao no import quebraria os
    dois **por ambiente**, que e o desfecho que o `RF-13` existe para impedir.

    ## O import do driver e PREGUICOSO, e pelo mesmo motivo

    `psycopg2` **nao esta instalado no `.venv/` do host**, que e o interpretador
    oficial da suite e da paridade; ele vive na imagem do conteiner. Um
    `import psycopg2` no topo deste modulo derrubaria `import app` nos dois — a
    mesma classe de defeito da `D-02`, so que na importacao em vez da conexao. Por
    isso ele acontece **dentro** de `registrar`, e a ausencia do driver vira
    **aviso** e nao excecao (`RN-13`).

    ## Uma conexao por analise, e uma transacao por analise

    `D-04`: conexao aberta e fechada **dentro** da chamada, sem pool. Sao 4 threads
    e uma gravacao por requisicao; um pool seria otimizacao sem necessidade medida
    que acrescenta estado por processo — o que a feature 005 removeu.

    `D-05`: a analise inteira vai em **uma** transacao. `with conexao:` e o
    gerenciador do proprio psycopg2 — commit no fim, rollback se algo levantar — e
    ele **nao** fecha a conexao; quem fecha e o `finally`.
    """

    def __init__(self, url: str):
        self._url = url

    def registrar(self, analise: AnaliseParaRegistrar,
                  dono: str) -> tuple[str | None, str | None]:
        """Grava a analise e devolve `(referencia, aviso)`. Nunca levanta (`RN-13`)."""
        try:
            import psycopg2
        except ImportError as erro:
            return None, ("Histórico não registrado: o driver do banco não está instalado "
                          f"neste interpretador ({erro}).")
        conexao = None
        try:
            conexao = psycopg2.connect(self._url)
            with conexao:
                with conexao.cursor() as cursor:
                    return self._escrever(cursor, analise, dono), None
        except Exception as erro:
            # A `RN-13` exige nao propagar: a analise ja foi calculada, e o
            # historico e beneficio, nunca condicao para ver o resultado.
            return None, f"Histórico não registrado: {type(erro).__name__}: {erro}"
        finally:
            if conexao is not None:
                conexao.close()

    # ------------------------------------------------------------------
    # A escrita. A ordem respeita as chaves estrangeiras: a analise, depois as
    # pessoas (que `match_result` e `match_path_node` referenciam), depois as
    # conexoes e o que pende delas.
    # ------------------------------------------------------------------

    def _escrever(self, cursor, analise: AnaliseParaRegistrar, dono: str) -> str:
        cursor.execute(
            """
            INSERT INTO dna_analysis
                (owner_id, tree_ref, match_file_ref, root_name_input, root_person_xref,
                 accepted_count, skipped_count, message)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            RETURNING analysis_id
            """,
            (dono, analise.tree_ref, analise.match_file_ref, analise.root_name_input,
             analise.root_person_xref, analise.accepted_count, analise.skipped_count,
             analise.message),
        )
        analysis_id = cursor.fetchone()[0]

        for pessoa in analise.pessoas:
            cursor.execute(
                """
                INSERT INTO analysis_person
                    (analysis_id, xref, nome, sexo, nascimento, local_nascimento,
                     falecimento, completa)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                """,
                (analysis_id, pessoa.xref, pessoa.nome, pessoa.sexo, pessoa.nascimento,
                 pessoa.local_nascimento, pessoa.falecimento, pessoa.completa),
            )

        for conexao in analise.conexoes:
            cursor.execute(
                """
                INSERT INTO match_result
                    (analysis_id, result_ordinal, csv_name, matched_name, matched_person_xref,
                     total_cm, relationship_key, relationship_label, meioses,
                     documentary_status, mrca_xref, causes, observations,
                     comparison_status, comparison_label, comparison_method,
                     expected_low, expected_high, expected_average, comparison_detail)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s,
                        %s, %s, %s, %s, %s, %s, %s)
                RETURNING match_id
                """,
                (analysis_id, conexao.ordinal, conexao.csv_name, conexao.matched_name,
                 conexao.matched_person_xref, conexao.total_cm, conexao.relationship_key,
                 conexao.relationship_label, conexao.meioses, conexao.documentary_status,
                 conexao.mrca_xref, list(conexao.causes),
                 list(conexao.observations), conexao.comparison_status,
                 conexao.comparison_label, conexao.comparison_method, conexao.expected_low,
                 conexao.expected_high, conexao.expected_average, conexao.comparison_detail),
            )
            match_id = cursor.fetchone()[0]

            for kit in conexao.kits:
                cursor.execute(
                    """
                    INSERT INTO match_kit
                        (match_id, ordinal, kit, source, total_cm, segment_count,
                         largest_segment_cm, status, status_note)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                    """,
                    (match_id, kit.ordinal, kit.kit, kit.source, kit.total_cm,
                     kit.segment_count, kit.largest_segment_cm, kit.status, kit.status_note),
                )

            for posicao, (xref, papel) in enumerate(conexao.caminho):
                cursor.execute(
                    """
                    INSERT INTO match_path_node
                        (match_id, ordinal, person_xref, role, is_affinity_anchor, analysis_id)
                    VALUES (%s, %s, %s, %s, %s, %s)
                    """,
                    # `is_affinity_anchor` e sempre FALSO: afinidade e atribuida por
                    # `path_search.py`, e nao pelo fluxo de analise de DNA.
                    (match_id, posicao, xref, papel, False, analysis_id),
                )

        for descartado in analise.descartados:
            cursor.execute(
                """
                INSERT INTO skipped_match
                    (analysis_id, ordinal, csv_name, kit, total_cm, reason)
                VALUES (%s, %s, %s, %s, %s, %s)
                """,
                (analysis_id, descartado.ordinal, descartado.csv_name, descartado.kit,
                 descartado.total_cm, descartado.reason),
            )

        return str(analysis_id)


__all__ = ["ArmazenamentoEmDisco", "CarregadorDeArvoresGedcom", "RegistroDeAnalisesPostgres"]

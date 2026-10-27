"""Rota do icone de atalho (`T004` e `T006` da feature 009).

## O que este arquivo prova

O contrato de `interfaces/apple-touch-icon.md`. A prova de opacidade e **estrutural**:
o formato PNG declara o tipo de cor no proprio cabecalho, e o tipo **2** e `truecolor`
sem canal alfa. Nao existe pixel transparente em um PNG cujo cabecalho diz que nao ha
canal alfa, e isso dispensa a biblioteca de imagem aqui - o que importa porque ela nao
esta em `requirements.txt` (`D-09`).

O teste que prova que a **tela nao mudou** compara o `sha256` do HTML servido com o ultimo valor
**declarado**. Ele nao e um teste de comportamento novo: e a guarda do `RF-05` e da `RN-02`, e por
isso ele ja passava antes de a rota existir. O criterio NAO e "a tela nunca muda" — ver o bloco
grande acima de `SHA_DA_TELA`, que declara quem pode mover o valor e onde a declaracao mora.
"""
from __future__ import annotations

import hashlib
import struct

import pytest

CAMINHO_DO_ICONE = "/apple-touch-icon.png"

#: Lado e tamanho da arte derivada. Herdados da receita (`tests/icone_de_atalho.py`).
LADO = 180
TAMANHO_ESPERADO = 16504

#: `sha256` do HTML de `GET /`.
#:
#: **Atualizado em 2026-10-09 pela feature `011-escolher-arquivo-da-lista`.** O invariante que
#: este teste mede e "a tela nao mudou DESDE a ultima mudanca declarada", e nao "a tela nunca
#: muda": a `011` mudou a tela de entrada por decisao declarada (`D-04`, `RF-06`), com adendo
#: vigente em `_reversa_sdd/addenda/011-escolher-arquivo-da-lista.md` e divergencia registrada
#: no `legacy-impact.md` dela.
#:
#: A troca do valor NAO e afrouxamento do teste, e o proprio comentario anterior ja declarava o
#: criterio: "qualquer mudanca aqui e mudanca de tela, e nao desta feature". Foi o que aconteceu.
#: O teste continua prendendo o que ele existe para prender — que nenhuma mudanca de tela passe
#: despercebida. Era 23.906 bytes em 2026-10-08; sao 25.825 agora.
#:
#: **Atualizado em 2026-10-10 pela `T036` da mesma feature.** O operador pediu que o titulo em
#: texto virasse a arte do topo, e o `<h1>` aparece nos DOIS ramos da tela — com e sem arquivo —,
#: entao a troca muda ate a tela vazia que este teste mede. Era `e18d1749…`, 25.825 bytes; e
#: `c1048cef…`, 26.007. O paragrafo acima continua sendo a justificativa, e nao uma licenca: a
#: mudanca esta declarada na `RN-16` do adendo vigente.
#:
#: **Atualizado de novo em 2026-10-10, pela `T044` da mesma feature.** O operador pediu uma
#: composicao nova para o topo da tela — arte reduzida a metade, subtitulo, titulo em texto e o
#: texto de apresentacao —, e o topo aparece nos DOIS ramos, com e sem arquivo, entao a mudanca
#: alcanca ate a tela vazia que este teste mede. Era `c1048cef…`, 26.007 bytes; e `36070ae0…`,
#: 27.209. Mais uma vez o paragrafo acima e a justificativa, e nao uma licenca: a mudanca esta
#: declarada na `RN-23` do adendo vigente.
#:
#: **Atualizado de novo em 2026-10-10, pela `T045` da mesma feature.** O operador pediu que o
#: texto de apresentacao ficasse na mesma forma organizada da documentacao — centralizado e em
#: coluna mais estreita —, e ele aparece nos DOIS ramos da tela. Era `36070ae0…`, 27.209 bytes;
#: e `17240e5a…`, 27.502. A mudanca esta declarada na `RN-24` do adendo vigente.
#:
#: **Atualizado em 2026-10-11, pela revisao de design da tela.** O operador pediu a aplicacao das
#: sugestoes de design que ele mandou: a folha de estilo saiu do `<style>` embutido e passou a ser
#: servida por `GET /app.css` (rota nova, em `src/assets/app.css` — `src/static/` continua proibida
#: pelo `W004`); o topo deixou de repetir em texto o titulo que a arte ja mostra; o resultado ganhou
#: indice com ancoras e o veredito da confrontacao subiu para o cabecalho do cartao. A tela vazia que
#: este teste mede carrega o `<head>` — folha, fontes e tema — e o topo, entao ela tambem muda.
#: `17240e5a…` (27.502 bytes) → `f2b2233e…` (28.858). O `1066e272…` que aparece na prosa foi medido
#: no meio da sessao e **nunca existiu em commit**; o valor foi recalculado uma vez antes de entrar.
#:
#: **O mesmo commit trouxe o controle de tema.** Botao visivel para escolher entre claro e escuro,
#: com o **claro como padrao** — antes o tema vinha de `matchMedia('(prefers-color-scheme: dark)')`,
#: e quem tinha o Windows no escuro abria a aplicacao no escuro sem ter pedido. O botao vive fora dos
#: dois ramos da tela, entao ele aparece tambem na tela vazia que este teste mede.
#:
#: ## A declaracao desta mudanca NAO mora aqui
#:
#: O paragrafo de 2026-10-09 (acima) continua sendo a justificativa, e nao uma licenca: o invariante e
#: "a tela nao mudou DESDE a ultima mudanca declarada". Mas **este comentario nao e o canal de
#: declaracao do projeto** — o canal e `_reversa_sdd/addenda/`, e foi la que as `RN-16`, `RN-23` e
#: `RN-24` viveram. Ate 2026-10-11 este arquivo era editado pelo mesmo autor que mudava a tela, e o
#: comentario virava a AUTORIZACAO da mudanca em vez da guarda dela — inclusive para uma mudanca que
#: contrariava uma regra vigente.
#:
#: A revisao de design esta declarada em
#: `_reversa_sdd/addenda/013-revisao-de-design-da-tela.md`, que **emenda a `RN-23`** (o titulo passa a
#: ser escondido se, e somente se, a arte do topo responder). Este hash continua valendo para o que
#: ele sempre mediu — "a tela nao mudou sem mudanca declarada" — e o alcance dele e declarado: ele
#: mede a tela de entrada **vazia**, com a pasta de upload do fixture.
#:
#: **Atualizado em 2026-10-14, pelo adendo `015-veredicto-do-doador-no-cartao`.** A tela de entrada
#: vazia NAO foi redesenhada: o conteudo visivel dela e o mesmo. O que mudou foi o `<script>` global
#: — o bloco do `mermaid.run` ganhou o filtro que pula diagrama dentro de `details` fechado e o
#: listener de `toggle` —, e o script vive fora dos dois ramos da tela, entao ele entra no que este
#: hash mede. `f2b2233e…` (28.858 bytes) → `9cf0e558…` (29.486). A declaracao esta em
#: `_reversa_sdd/addenda/015-veredicto-do-doador-no-cartao.md`.
#:
#: **Atualizado em 2026-10-14, pelo adendo `018-cartao-de-resultado-recolhivel`.** Mesmo caso do
#: `015`, e de novo so o `<script>`: cada cartao de resultado virou um `<details>` fechado por
#: padrao, e o script ganhou o ouvinte que abre o cartao do alvo da ancora (`hashchange`), a guarda
#: que impede o link "Voltar" — que mora no cabecalho, agora o proprio gatilho — de fechar o cartao,
#: e o par de controles "Expandir/Recolher todas". O seletor do `toggle` do Mermaid deixou de nomear
#: `details.grafo-do-registro` e passou a alcancar qualquer `details` com diagrama. Os dois botoes
#: estao sob `{% if dna_results %}` e NAO aparecem na tela vazia; o que entra no hash e o script.
#: `9cf0e558…` (29.486 bytes) → `6cc496b4…` (30.768). A declaracao esta em
#: `_reversa_sdd/addenda/018-cartao-de-resultado-recolhivel.md`.
#:
#: **Atualizado em 2026-10-14, pelo adendo `020-bloco-dos-descartados-recolhivel`.** So' o
#: `<script>`, de novo: o grupo "Matches descartados" virou um `<details>` recolhivel, e para os
#: botoes "Expandir/Recolher todas as analises" nao alcancarem esse bloco o seletor deles passou de
#: `details.card` para `details.cartao-do-resultado`. O bloco em si vive sob
#: `{% if skipped_matches %}` e NAO entra no que este hash mede — na tela vazia `skipped_matches` e'
#: indefinido e o corpo do `if` e' pulado inteiro. Medido, e nao deduzido: a primeira medicao deu
#: +69 bytes e nao fechava com os 15 do seletor, porque eu comparava o HTML do Flask com um render
#: de Jinja de contexto vazio. `6cc496b4…` (30.768 bytes) → `5e6842be…` (30.783, +15 = o seletor).
#: A declaracao esta em `_reversa_sdd/addenda/020-bloco-dos-descartados-recolhivel.md`.
#:
#: **Atualizado em 2026-10-14, pelo adendo `021-seletor-de-arquivos-por-formato`.** Desta vez a
#: tela de entrada muda de verdade, por um atributo visivel no HTML servido: o campo "Enviar nova
#: arvore" ganhou `accept=".ged"`, para o seletor de arquivos oferecer so' o formato da aba.
#: `5e6842be…` (30.745 bytes) → `39c6257f…` (30.759, +14 = exatamente o atributo). O campo do CSV
#: (`accept=".csv"`) NAO entra no que este hash mede: ele vive no formulario da analise, que so'
#: existe depois de uma arvore carregada. Os comentarios que explicam os dois campos fecham com
#: `-#}` para nao acrescentarem whitespace ao documento — sem isso o delta seria +59, e esta
#: declaracao estaria contando espaco em branco em vez de contar a regra.
#: A declaracao esta em `_reversa_sdd/addenda/021-seletor-de-arquivos-por-formato.md`.
#:
#: **Atualizado em 2026-10-16, pela troca da arte do topo.** A arte nova
#: (`docs/assets/img/banner-analisador.png`, 1024x547) NAO traz "Analisador Genealogico" desenhado.
#: Com isso o `<h1>` voltou a ser SEMPRE visivel: a condicao que o escondia enquanto a arte
#: respondia (`arte_do_topo_disponivel`, um processador de contexto) perdeu o objeto e saiu junto,
#: de `src/app.py` e do template. `39c6257f…` (30.759 bytes) → `c4a34f7b…` (30.781).
#:
#: A contribuicao DESTA mudanca e **-16 bytes** — exatamente o ` visually-hidden` que saiu da classe
#: do `h1`. Os +38 restantes do delta sao de edicoes **em curso e nao commitadas** de outra sessao no
#: mesmo template: medido, e nao deduzido, porque o valor anterior veio do commit do adendo `021` e o
#: template esta modificado na arvore. Este hash mede a TELA, entao ele acusa as duas coisas juntas.
#:
#: Com o titulo de volta, a **`RN-23` volta a valer como esta escrita**: a emenda que o adendo `013`
#: registrou ("escondido se, e somente se, a arte responder") foi RETIRADA. A declaracao desta
#: entrega esta em `_reversa_sdd/addenda/023-arte-do-topo-sem-o-titulo.md`.
#:
#: **Atualizado em 2026-10-20, pela feature 037 (tres fases da tela de entrada).** A tela de
#: entrada deixou de ter duas abas e passou a ter uma barra lateral com tres fases, mais a fase 1
#: com contadores, caixa de status e bloco de envio. `c4a34f7b…` (30.781 bytes) →
#: `794711aa…` (38.484 bytes, +7.703). Medido com a pasta de uploads VAZIA e temporaria, a mesma
#: montagem do fixture `cliente_de_upload`. A declaracao da entrega esta em
#: `_reversa_sdd/addenda/037-redesenho-das-tres-fases.md`.
#:
#: **Atualizado de novo no mesmo dia pela emenda `E001`**: a masthead passou a duas colunas
#: (texto a esquerda, arte a direita), emendando a `RN-24`. `794711aa…` (38.484) →
#: `c5fb4ff7…` (38.476, **-8 bytes**). O saldo negativo e a troca de `text-center mb-4` +
#: `row justify-content-center` + `col-lg-9` pelas duas colunas nomeadas — menos marcacao do que
#: antes, com a mesma informacao. A emenda esta no `requirements.md` da feature 037.
#:
#: **Terceira medicao do dia, emenda `E005`**: entraram os tres passos da jornada entre a linha
#: divisoria e as fases. `c5fb4ff7…` (38.476) → `ed4f8734…` (40.222, **+1.746 bytes**), que sao
#: os tres blocos informativos — texto, marcacao e atributos. As emendas `E002`, `E003` e `E004`
#: foram so de folha e NAO moveram este hash.
#:
#: **Quarta medicao, emenda `E006`**: a fileira de tres abas acima do painel, mais o script que
#: sincroniza o estado entre ela e a barra lateral. `ed4f8734…` (40.222) → `3bac6c24…`
#: (42.293, **+2.071 bytes**).
#:
#: **Quinta medicao, emenda `E010`**: a tipografia passou a ser a da sugestao visual —
#: `Cormorant Garamond` nos titulos e `Manrope` no texto. `3bac6c24…` (42.293) → `7375696d…`
#: (42.290, **-3 bytes**): o link do Google Fonts ficou tres bytes mais curto, e o resto da
#: mudanca e de folha (familias, pesos, tamanhos e raios). As emendas `E007`, `E008` e `E009`
#: foram so de folha e NAO moveram este hash.
#: **Sexta medicao, feature 046**: o controle de paginacao da lista de conexoes. O markup do
#: controle mora dentro de `{% if dna_results %}` e **nao aparece** na tela de entrada vazia; o que
#: moveu o hash foi o `<script>` — o motor da paginacao, os quatro ouvintes e a revelacao da pagina
#: do alvo antes de abrir o cartao. `7375696d…` (42.290) → `05f2179a…` (46.264, **+3.974 bytes**),
#: todos de script. O `TAMANHO_ESPERADO` acima **nao muda**: ele mede o PNG do icone, e a arte
#: nao foi tocada.
#:
#: **Setima medicao, 2026-10-26, passagem de design.** O botao de tema passou a levar `title`
#: sincronizado com o `aria-label`: acima de 992 px ele fica SO com o icone, e a dica de mouse
#: precisa existir sem depender de leitor de tela. `05f2179a…` (46.264) → `26d6cac7…`
#: (46.359, **+95 bytes**), todos de script — uma linha de `title`. O comentario Jinja que a
#: explica fecha com `-#}` para nao entrar nesta conta, a mesma armadilha de whitespace do
#: adendo `021`. O resto da passagem (raios, sombras, selos, navegacao por largura, campo de
#: arquivo) e' folha: `app.css` NAO passa por este hash, e a marcacao desta rota continua a
#: mesma tirando aquela linha.
#: **Oitava medicao, 2026-10-26, diagrama de parentesco.** O bloco `mermaid.initialize`
#: da tela trocou a fonte do desenho (IBM Plex Sans, que a pagina nao carrega, por Manrope),
#: a tinta do texto (`#172B3A` por `#2A2418`), a cor das linhas (`#566772` por `#6A6150`) e
#: ganhou `fontSize` e espacamento entre nos. `26d6cac7…` (46.359) → `5fc0b929…`
#: (46.477, **+118 bytes**), todos de script — o resto da mudanca (largura fixa dos nos,
#: datas e papeis no rotulo) e' gerado no servidor e so' aparece com resultado na tela.
#: **Nona medicao, 2026-10-26, impressao do resultado (feature 050).** O bloco de impressao
#: entra no script da tela (clone do cartao, espera do desenho, `afterprint`) e o
#: `#area-de-impressao` nasce DENTRO do ramo dos resultados — este hash mede a tela VAZIA,
#: onde o container nao existe. `5fc0b929…` (46.477) → `f49dd6da…` (51.117, **+4.640 bytes**),
#: todos de script. A marcacao do cartao (botao e identificacao) so aparece com resultado e
#: nao entra nesta conta.
#: **Decima medicao, 2026-10-26, entrada pelo provedor (feature 051).** O bloco da conta
#: logada entra na masthead dentro de `{% if conta %}`. Com a entrada desligada — que e
#: como ESTE hash mede, sem sessao — o bloco nao renderiza, e o delta e so o whitespace das
#: linhas do `if`: `f49dd6da…` (51.117) → `df702cbb…` (51.150, **+33 bytes**), todos de
#: marcacao Jinja. O resto da feature (`login.html`, cookie, guarda) nao passa por esta rota.
#: **Decima primeira medicao, 2026-10-27, nome do PDF (emenda E001 da feature 050).** O
#: script da impressao passa a trocar o `document.title` durante o dialogo, com o texto do
#: proprio titulo do cartao ("Analise de conexao com <nome>"), para o nome sugerido do
#: arquivo sair certo. `df702cbb…` (51.150) → `386f2fef…` (51.601, **+451 bytes**), todos
#: de script.
SHA_DA_TELA = "386f2fef0c63046648f3a04cb1eb1fc1c7ba377104210cbed4509a34bec6cb39"


def _cabecalho_png(corpo: bytes):
    """`(largura, altura, bits, tipo_de_cor)` lidos do IHDR, sem biblioteca de imagem."""
    assert corpo[:8] == b"\x89PNG\r\n\x1a\n", "o corpo nao comeca com assinatura PNG"
    assert corpo[12:16] == b"IHDR", "o primeiro chunk nao e IHDR"
    return struct.unpack(">IIBB", corpo[16:26])


@pytest.fixture
def resposta(cliente_de_upload):
    """A resposta da rota do icone, no app montado com pasta de upload temporaria."""
    _app, cliente, _pasta = cliente_de_upload
    return cliente.get(CAMINHO_DO_ICONE)


# --- T004: a rota existe e entrega a arte certa -------------------------------


def test_a_rota_do_icone_responde_200(resposta):
    """`RF-01`. Falha antes da rota existir, com `404`."""
    assert resposta.status_code == 200, (
        f"esperado 200 em {CAMINHO_DO_ICONE}, veio {resposta.status_code}"
    )


def test_o_tipo_de_conteudo_e_de_imagem(resposta):
    """`RF-01`: o tipo declarado e de imagem, e nao `text/html` do formulario."""
    tipo = resposta.headers.get("Content-Type", "")
    assert tipo.startswith("image/"), f"Content-Type inesperado: {tipo!r}"


def test_o_icone_tem_180_por_180(resposta):
    """`RF-02`. A dimensao e lida do cabecalho do PNG, nao estimada pelo tamanho."""
    largura, altura, _bits, _tipo = _cabecalho_png(resposta.get_data())
    assert (largura, altura) == (LADO, LADO), f"dimensao {largura}x{altura}, esperado {LADO}x{LADO}"


def test_o_icone_nao_tem_canal_alfa(resposta):
    """`RF-03`, por propriedade do formato.

    O tipo de cor **2** e `truecolor` sem canal alfa. E a prova mais forte de opacidade
    que existe sem decodificar pixel: nao ha onde guardar transparencia. Servir a arte
    **canonica** aqui daria tipo 6, e o icone ficaria com fundo preto no aparelho.
    """
    _l, _a, _b, tipo_de_cor = _cabecalho_png(resposta.get_data())
    assert tipo_de_cor == 2, (
        f"tipo de cor {tipo_de_cor}: esperado 2 (truecolor sem alfa). "
        "6 significaria canal alfa, e transparencia vira fundo preto no atalho."
    )


def test_o_tamanho_e_o_da_receita(resposta):
    """A ancora da receita: denuncia reamostragem, fundo ou compressao diferentes."""
    assert len(resposta.get_data()) == TAMANHO_ESPERADO, (
        f"{len(resposta.get_data())} bytes, esperado {TAMANHO_ESPERADO}. "
        "Confira a receita em tests/icone_de_atalho.py antes de suspeitar da rota."
    )


# --- T004: a tela nao mudou ---------------------------------------------------


def test_a_tela_nao_mudou_sem_mudanca_declarada(cliente_de_upload):
    """`RF-05` e `RN-02`: a tela de entrada nao mudou **desde a ultima mudanca declarada**.

    Nao e "a tela nao pode mudar": e "a tela nao pode mudar **sem declaracao**". A declaracao mora
    em `_reversa_sdd/addenda/` — a revisao de design de 2026-10-11 esta em `013-…`. O que este
    teste pega e a mudanca de tela que ninguem declarou: mutacao acidental de dependencia,
    ambiente de upload diferente, espacamento reordenado.
    """
    _app, cliente, _pasta = cliente_de_upload
    corpo = cliente.get("/").get_data()
    assert hashlib.sha256(corpo).hexdigest() == SHA_DA_TELA, (
        f"a tela mudou: {len(corpo)} bytes. Esperado {SHA_DA_TELA[:16]}... "
        "Se a mudanca foi deliberada, declare-a em `_reversa_sdd/addenda/` e atualize o valor; "
        "se nao foi, este e um defeito."
    )


def test_a_tela_nao_declara_o_icone_de_atalho(cliente_de_upload):
    """`RN-02`: a descoberta e por caminho convencional, sem declaracao no documento."""
    _app, cliente, _pasta = cliente_de_upload
    corpo = cliente.get("/").get_data().decode("utf-8")
    assert "apple-touch-icon" not in corpo, (
        "a tela passou a declarar o icone de atalho; a decisao era NAO tocar no template"
    )


def test_a_tela_mantem_o_icone_da_aba_embutido(cliente_de_upload):
    """`RF-09`: o icone da aba continua sendo o `data URI`, e nao uma segunda rota."""
    _app, cliente, _pasta = cliente_de_upload
    corpo = cliente.get("/").get_data().decode("utf-8")
    assert corpo.count('rel="icon"') == 1, "o icone da aba sumiu ou foi duplicado"
    assert corpo.count("data:image") == 1, "o icone da aba deixou de ser embutido"


# --- T006: metodo, cache, caminhos nao servidos e ausencia da arte ------------


def test_escrita_no_caminho_do_icone_e_recusada(cliente_de_upload):
    """`RF-06`: a rota e de leitura. A recusa sai do roteador, sem codigo nosso."""
    _app, cliente, _pasta = cliente_de_upload
    recusa = cliente.post(CAMINHO_DO_ICONE, data={"qualquer": "coisa"})
    assert recusa.status_code == 405, (
        f"escrita no icone devolveu {recusa.status_code}, esperado 405 (metodo nao permitido)"
    )


def test_a_resposta_traz_marca_de_versao(resposta):
    """`RF-07`: sem marca de versao o cliente nao tem como revalidar barato."""
    assert resposta.headers.get("ETag"), "a resposta nao trouxe ETag"


def test_requisicao_repetida_nao_traz_corpo(resposta, cliente_de_upload):
    """`RF-07`: a rebusca com a marca de versao responde 'nao modificado', sem corpo."""
    _app, cliente, _pasta = cliente_de_upload
    marca = resposta.headers["ETag"]
    repetida = cliente.get(CAMINHO_DO_ICONE, headers={"If-None-Match": marca})
    assert repetida.status_code == 304, (
        f"rebusca devolveu {repetida.status_code}, esperado 304"
    )
    assert repetida.get_data() == b"", "a resposta de 'nao modificado' trouxe corpo"


def test_nenhuma_validade_longa_de_cache(resposta):
    """`RF-07` e `D-05`: a arte foi trocada duas vezes em um dia.

    Uma validade de um ano congelaria o cliente que ja tivesse buscado, e o `ETag` nao
    salva - ele so age depois de a validade expirar.
    """
    cabecalho = resposta.headers.get("Cache-Control", "")
    if "max-age" in cabecalho:
        valor = int(cabecalho.split("max-age=")[1].split(",")[0].strip())
        assert valor <= 86400, (
            f"Cache-Control declara {valor}s de validade: e longo demais para uma arte "
            "que muda. O limite desta feature e um dia (RF-07)"
        )


@pytest.mark.parametrize("caminho", ["/apple-touch-icon-precomposed.png", "/favicon.ico"])
def test_os_caminhos_nao_servidos_continuam_sem_resposta(cliente_de_upload, caminho):
    """`RF-11` e `RN-09`: nenhum caminho sem consumidor foi criado.

    O alias legado pertence a sistemas anteriores; e o `favicon.ico` so e buscado quando
    o documento NAO declara icone - e o template declara. Criar qualquer um dos dois
    repetiria a divida #17, que este projeto ja fechou.
    """
    _app, cliente, _pasta = cliente_de_upload
    assert cliente.get(caminho).status_code == 404, (
        f"{caminho} passou a responder: e superficie sem consumidor (RN-09)"
    )


def test_a_tela_continua_de_pe_sem_a_arte(cliente_de_upload, monkeypatch):
    """`RN-08`: o icone ausente degrada, e nao derruba nada.

    Aponta a configuracao para um caminho inexistente em vez de mexer no arquivo: o teste
    nao pode alterar a arte do repositorio para provar um caso de ausencia.
    """
    app, cliente, _pasta = cliente_de_upload
    monkeypatch.setitem(app.config, "ARTE_DO_ICONE", "caminho/que/nao/existe.png")

    assert cliente.get(CAMINHO_DO_ICONE).status_code == 404
    tela = cliente.get("/")
    assert tela.status_code == 200, "a tela caiu por causa do icone ausente (RN-08)"
    assert hashlib.sha256(tela.get_data()).hexdigest() == SHA_DA_TELA, (
        "a tela mudou de conteudo quando a arte ficou ausente"
    )


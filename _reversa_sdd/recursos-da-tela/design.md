# Unit `recursos-da-tela` — Design Técnico

> Spec gerada pelo Reversa-Writer na re-extração de **2026-10-10** (nível **Completo**). Unit **nova**.
> ⚠️ **Zero linhas úteis próprias de módulo:** as duas rotas moram em `src/app.py`. A unidade é de **contrato**, e a "implementação" dela inclui as **receitas de derivação**, que vivem em `tests/`.
> Fontes: `app.py` (`ARTE_DO_ICONE`/`icone_de_atalho`, `ARTE_DO_TOPO`/`banner_do_topo`), `templates/index.html`, `src/assets/*`, `tests/{icone_de_atalho,banner_da_tela}.py`, `tests/{test_icone_de_atalho,test_banner_do_topo,test_deriva_da_arte}.py`, `.dockerignore`.
> Escala de confiança: 🟢 CONFIRMADO | 🟡 INFERIDO | 🔴 LACUNA

---

## Interface

### Endpoint HTTP

| Método | Caminho | Entrada | Saída | Status |
|--------|---------|---------|-------|--------|
| GET | `/apple-touch-icon.png` | — | PNG do ícone derivado | `200` / `404` (vazio) / `304` (revalidação) |
| GET | `/banner.png` | — | PNG do banner derivado | `200` / `404` (vazio) / `304` (revalidação) |
| POST, PUT, DELETE, PATCH | os dois caminhos | — | — | **`405`** pelo roteador |

> 🟢 **As duas rotas são o mesmo desenho:** `GET` sozinho, `ETag` do `send_file`, `404` com resposta vazia, caminho ancorado no arquivo do app e `mimetype="image/png"`. Não há diferença de contrato entre elas.

### Símbolos

| Símbolo | Arquivo | Assinatura | Retorno | Observação |
|---------|---------|-----------|---------|------------|
| `icone_de_atalho` | `src/app.py` | `()` | `PNG 200` \| `("", 404)` | Lê `app.config["ARTE_DO_ICONE"]` 🟢 |
| `banner_do_topo` | idem | `()` | `PNG 200` \| `("", 404)` | Lê `app.config["ARTE_DO_TOPO"]` 🟢 |
| `ARTE_DO_ICONE` / `ARTE_DO_TOPO` | idem | constante + chave de `config` | `str` (caminho absoluto) | Em `config` para o caso de ausência ser testável **sem tocar no repositório** 🟢 |
| `arte_derivada` | `tests/icone_de_atalho.py` | `(caminho_canonico)` | `Image` 180×180 RGB | Compõe sobre branco e reamostra com LANCZOS 🟢 |
| `bytes_da_arte` / `gravar_arte` | idem | `(caminhos)` | `bytes` / `int` | A receita do arquivo commitado 🟢 |
| `_e_fundo` | `tests/banner_da_tela.py` | `(pixel)` | `bool` | As duas faixas de brilho e saturação 🟢 |
| `mascara_do_fundo` | idem | `(imagem)` | `bytearray` | Remoção **global**, não por inundação 🟢 |
| `arte_limpa` | idem | `()` | `Image` RGBA | Máscara + alfa proporcional na fronteira 🟢 |
| `residuo_de_fundo` | idem | `(imagem)` | `int` | Mede com limite **mais estrito** que a regra 🟢 |
| `_imagens_diferem` | `tests/test_deriva_da_arte.py` | `(caminho)` | `bool` | Compara **pixel**, nunca `sha256` 🟢 |

### Constantes

| Constante | Valor | Onde | Papel |
|-----------|-------|------|-------|
| `TAMANHO_ESPERADO` | `16504` | `tests/icone_de_atalho.py` | Âncora contra reamostragem, fundo ou compressão diferentes 🟢 |
| `FUNDO` | branco opaco | idem | A arte tem 51,5 % de creme em **duas** tonalidades; eleger uma faria a outra parecer errada 🟢 |
| `LADO` do ícone | `180` | idem | Medida esperada pelo sistema móvel 🟢 |
| `CLARO_MINIMO` | `160` | `tests/banner_da_tela.py` | **Piso absoluto**: abaixo disso nunca é fundo 🟢 |
| `SATURACAO_MAXIMA` | `50` | idem | Teto da faixa **alta** (≥ 190) 🟢 |
| Teto da faixa **média** | `12` | idem | Entre 160 e 190 o teto é estreito, porque ali a tinta clara da arte é quase neutra 🟢 |
| Limite do resíduo | `SATURACAO_MAXIMA - 5` | idem | **Mais estrito** que a regra, de propósito 🟢 |
| Caixa de regressão | `(778,232)–(918,338)` | `test_banner_do_topo.py` | Onde o quadriculado sobreviveu; resíduo tem de ser **zero** 🟡 |
| Pontos de arte | `11` | idem | Cobrem arte escura pouco saturada e arte clara quase neutra 🟢 |

## Fluxo Principal

### 1. `GET` nas duas rotas — o mesmo desenho, duas vezes

1. O roteador casa apenas com `GET` (`BR-E-01`). **Qualquer escrita devolve `405` sem uma linha de validação nossa.** 🟢
2. A função lê o caminho da chave de `app.config` — `ARTE_DO_ICONE` ou `ARTE_DO_TOPO` (`BR-E-02`). 🟢
3. `os.path.isfile(caminho)`: falso → **`("", 404)`**, resposta vazia, e **nada mais muda** (`BR-E-03`). 🟢
4. Verdadeiro → `send_file(caminho, mimetype="image/png")` (`BR-E-04`). 🟢
5. O `send_file` emite **`ETag`**; na rebusca com `If-None-Match`, responde **`304` sem corpo** (`BR-E-06`). 🟢 **Nenhum `Cache-Control` de validade longa é declarado.**
6. Os dois caminhos são ancorados em `dirname(abspath(__file__))` (`BR-E-05`), de modo que escrita e leitura não podem divergir com o diretório corrente. 🟢

### 2. A derivação do ícone (a receita, em `tests/icone_de_atalho.py`)

1. Abre a canônica `docs/assets/img/logo.png` — 512×512 RGBA, com **32,5 %** de pixels totalmente transparentes e os quatro cantos em `(0,0,0,0)`. 🟢
2. **Compõe sobre branco opaco** (`BR-E-11`): o sistema móvel compõe transparência sobre **preto** no ícone de atalho, e servir a arte crua daria um quadrado preto com o desenho por cima — **incluindo as aberturas internas** entre folhas e galhos. 🟢
3. **Reamostra para 180×180** com LANCZOS (`BR-E-10`): é a medida que o sistema espera; outra medida é reamostrada por ele e perde nitidez. 🟢
4. Converte para **RGB**, mantendo os **cantos retos** (`BR-E-12`): o sistema aplica a própria máscara arredondada, e arredondar aqui produziria arredondamento duplo, com um anel de fundo no canto. 🟢
5. Salva como PNG e grava em `src/assets/apple-touch-icon.png` — **16.504 bytes**, tipo de cor **2** (`truecolor` sem alfa). 🟢

> 🟢 **A opacidade é provada por propriedade do formato, não por amostragem.** O tipo **2** no IHDR diz que **não existe canal alfa**: não há pixel transparente num PNG cujo cabeçalho nega o canal. Isso dispensa a biblioteca de imagem no teste — o que importa porque ela **não** está em `requirements.txt`.

### 3. A derivação do banner (a receita, em `tests/banner_da_tela.py`)

1. Abre a fonte `docs/assets/img/banner-analisador.png` — em **`RGB`, sem alfa**, com o quadriculado de transparência **gravado no bitmap** (`BR-E-15`). 🟢
2. `mascara_do_fundo` marca **globalmente** todo pixel que satisfaz `_e_fundo` (`BR-E-16`), e não por inundação a partir da borda. 🟢
   - **Faixa alta** (brilho ≥ 190): é fundo se a saturação ≤ 50. Ali o fundo pode estar **tingido**, então o teto é largo.
   - **Faixa média** (brilho 160–190): é fundo se a saturação ≤ 12. O teto é estreito porque o xadrez é **neutro** e a tinta clara da arte é levemente **quente**.
   - **Abaixo de 160: nunca é fundo** (`BR-E-17`).
3. Os pixels marcados ficam **transparentes**. 🟢
4. **Segunda passada:** a fronteira recebe **alfa proporcional** à distância do fundo (`BR-E-19`) — entre a arte e o xadrez há uma faixa de um a dois pixels de cinza intermediário, e deixá-la opaca desenharia um **halo claro** em volta de tudo. 🟢
5. Grava `src/assets/banner-da-tela.png` — **RGBA, 317.058 bytes**. 🟢

> 🟢 **Por que a remoção é global, e não por inundação.** A primeira versão inundava, para poupar as partes claras da arte, e **foi medida como insuficiente**: a árvore, o livro e o texto formam **anúncios fechados**, e o fundo preso dentro deles nunca é alcançado. Medido no resultado: o pixel `(300,150)` continuava opaco e sobravam **8.379** pixels de tom de fundo opacos numa amostra de **1/9** da imagem.
>
> 🟢 **Por que duas faixas, e não um limite único.** Com `brilho ≥ 160 e saturação ≤ 50`, o fundo (saturação 0–7) **e** o preenchimento do texto dourado (brilho ≈212, saturação ≈24) caíam os dois no fundo, e as letras ficavam **ocas** em partes — defeito medido no composto sobre **magenta**.
>
> 🟢 **Por que o resíduo usa limite mais estrito.** Medir o resíduo com o **mesmo** limite da regra devolve **sempre zero** — é uma métrica **circular**. Foi exatamente esse erro que deixou um bloco inteiro de quadriculado passar **duas vezes**: a métrica dizia `0,00 %` enquanto o composto sobre magenta mostrava o bloco.

### 4. A masthead (`templates/index.html`)

1. Arte do topo com **`w-50`** e um `alt` que descreve a **ilustração** (`BR-E-30`). 🟢
2. **Subtítulo**. 🟢
3. **Título em texto** (`<h1>`). 🟢
4. **Texto de apresentação**. 🟢

> 🟢 **A ordem é contrato, e ela já foi invertida uma vez:** a `T036` trocou o `<h1>` por imagem e a `T044` reverteu — arte reduzida à metade, subtítulo, título em texto e apresentação, **nessa ordem**. O título sobrevive à arte ausente **por construção**, e não por depender do `alt`.
>
> 🟢 **O `alt` não repete o título:** com o título escrito logo abaixo, repeti-lo faria o leitor de tela anunciar a mesma coisa **duas vezes**.

### 5. O contrato da deriva (`tests/test_deriva_da_arte.py`)

1. Importa a **receita** de `tests/` e regenera a derivada em memória. 🟢
2. Compara **pixel a pixel** com o arquivo **commitado** (`BR-E-26`) — nunca por `sha256` (`BR-E-27`). 🟢
3. Prova que a comparação **detecta um pixel alterado** — sem isso o teste poderia estar comparando algo consigo mesmo e passar por vacuidade. 🟢
4. Prova que **recompressão do mesmo desenho não é deriva**. 🟢
5. Falha se a arte estiver sob pasta estática (`BR-E-23`) e se `requirements.txt` citar a biblioteca de imagem (`BR-E-28`). 🟢

## Fluxos Alternativos

| Condição | Comportamento | Conf. |
| --- | --- | --- |
| Arte ausente no disco | `404` com corpo **vazio**; a tela continua de pé e o atalho degrada para ícone genérico | 🟢 |
| Escrita no caminho da arte | `405` pelo roteador, sem validação própria | 🟢 |
| Cliente revalida com `If-None-Match` | `304` **sem corpo** | 🟢 |
| Cliente busca `favicon.ico` ou `apple-touch-icon-precomposed.png` | `404` — superfície deliberadamente ausente | 🟢 |
| `pillow`/`PIL==` aparece em `requirements.txt` | O teste de deriva **falha** | 🟢 |
| A arte é movida para uma pasta estática | O teste de deriva **falha** (`W004`) | 🟢 |
| Alguém baixa o brilho ou alarga a saturação para "resolver" um resíduo | Um dos **11 pontos** vira buraco e o teste cai | 🟢 |
| A arte falha **dentro do container** | Degrada para `404` — e **não há teste que pegue isso** | 🔴 |

## Dependências

| Dependência | Como usa | Conf. |
| --- | --- | --- |
| **Flask** (`send_file`) | Emissão do `ETag`, do `304` e do `Content-Type` | 🟢 |
| `os.path` | `isfile` na rota; `dirname(abspath(__file__))` no caminho | 🟢 |
| **Pillow / PIL** | **Só na receita**, em `tests/`, com import **preguiçoso** dentro das funções. **Não** está em `requirements.txt` e **não** entra na imagem | 🟢 |
| `.dockerignore` | A lista de **permissão** que decide onde a arte pode morar | 🟢 |
| `docs/assets/img/logo.png`, `banner-analisador.png` | As **fontes canônicas** da receita — moram em `docs/`, que **não entra na imagem** | 🟢 |
| Unit nenhuma | **Esta unit não depende de nenhuma outra** — `modules.json` declara `dependencies: []` | 🟢 |
| Nenhuma integração de rede | Não há HTTP de saída, banco nem fila | 🟢 |

## Decisões de Design Identificadas

| Decisão | Evidência no código | Confiança |
| --- | --- | --- |
| `GET` **sozinho** nas duas rotas, deixando o `405` para o roteador | `app.py:263`, `:308` | 🟢 |
| Os caminhos em **`app.config`**, para o caso de ausência ser testável sem tocar no repositório | `app.py:258-260`, `:303-305` | 🟢 |
| **Sem validade longa de cache**; a revalidação é o `ETag` do `send_file` | `app.py:270-273`, `:312-313` | 🟢 |
| **Arte ausente é `404` vazio**, e nada mais muda | `app.py:279-280`, `:316-317` | 🟢 |
| Caminhos ancorados no **arquivo do app** | `app.py:255-257`, `:300-302` | 🟢 |
| O ícone é **composto sobre branco** e reamostrado para 180×180 | `tests/icone_de_atalho.py:arte_derivada` | 🟢 |
| **Cantos retos** — o sistema aplica a própria máscara | `tests/icone_de_atalho.py` | 🟢 |
| Opacidade provada pelo **tipo de cor 2** do IHDR, sem `PIL` | `tests/test_icone_de_atalho.py` | 🟢 |
| Remoção de fundo **global**, não por inundação | `tests/banner_da_tela.py:mascara_do_fundo` | 🟢 |
| **Duas faixas** de brilho/saturação, com piso absoluto em 160 | `tests/banner_da_tela.py:_e_fundo` | 🟢 |
| **Alfa proporcional** na fronteira, para o serrilhado não virar halo | `tests/banner_da_tela.py:arte_limpa` | 🟢 |
| Métrica de resíduo **não-circular** (`SATURACAO_MAXIMA - 5`) | `tests/banner_da_tela.py:residuo_de_fundo` | 🟢 |
| A arte de runtime mora em `src/assets/` por causa da lista de **permissão** | `.dockerignore`, `app.py:251-254` | 🟢 |
| A arte é **commitada**, e não gerada no runtime | `tests/icone_de_atalho.py` | 🟢 |
| A receita tem **fonte única** em `tests/`, importada pelo teste de deriva | `tests/test_deriva_da_arte.py` | 🟢 |
| Comparação de deriva por **pixel**, nunca por `sha256` | `tests/test_deriva_da_arte.py:_imagens_diferem` | 🟢 |
| A biblioteca de imagem **não** entra em `requirements.txt` | `tests/test_deriva_da_arte.py` | 🟢 |
| A `T044` reverteu a `T036`: o título voltou a ser **texto**, e a ordem é imagem → subtítulo → título → apresentação | `templates/index.html`, `test_banner_do_topo.py` | 🟢 |

## Estado Interno

**A unit não mantém estado.** 🟢

| Estado | Escopo | Observação | Conf. |
| --- | --- | --- | --- |
| `ARTE_DO_ICONE` / `ARTE_DO_TOPO` | `app.config`, no import | Só o caminho absoluto; **nenhum byte de arte é lido no import** | 🟢 |
| Bytes da arte | — | **Nunca em memória do processo**: `send_file` entrega o arquivo do disco a cada requisição | 🟡 |

> 🟡 **Não há cache em memória**, e o custo é do sistema operacional via `send_file` — 317 KB no banner. Não há medição de impacto no repositório. É uma escolha implícita, não uma decisão registrada. **[Verificar]**

## Observabilidade

| O quê | Onde | Observação |
|-------|------|------------|
| **Nenhum log** | — | A ausência de arte **não é registrada em lugar nenhum**: o `404` é indistinguível de "a rota não existe" 🔴 |
| **Nenhuma métrica ou trace** | — | Não há contagem de acertos de cache nem de `304` 🔴 |
| O `ETag` e o `304` | cabeçalhos HTTP | São a única evidência observável de que a revalidação funciona 🟢 |
| O teste de deriva como instrumento | `tests/test_deriva_da_arte.py` | É a **única** verificação de que a arte commitada corresponde à receita 🟢 |

## Riscos e Lacunas

- 🟡→🟢 **`L-33` — a arte servida não é verificada no ambiente do container: DECIDIDA em 2026-10-10.** Os testes rodam no **host**, onde `docs/` existe; se a arte falhar dentro da imagem, a degradação é o `404` — silencioso, sem log e sem teste. **Decisão humana: um health check no arranque**, que confira a presença das duas artes (e o tamanho delas) antes de o servidor aceitar a primeira requisição. A escolha é deliberada entre as três alternativas: um teste na imagem protegeria o **CI**, e o health check protege a **operação** — que é o ambiente onde a falha é invisível. A implementação é mudança de código em `src/app.py` e fica agendada para **depois do Passo 4**.
- 🟡 **`L-34` — o `sha256` do HTML de `GET /` em `test_icone_de_atalho.py` é um invariante mantido à mão**, atualizado **três vezes em 2026-10-10**. Enquanto cada atualização for uma decisão humana registrada em comentário, o teste prende o que promete; se virar rotina, ele deixa de prender — e um invariante que se atualiza sozinho não protege nada.
- 🟡 **A caixa de regressão `(778,232)–(918,338)` descreve uma composição que não existe mais** (a que tinha abajur). Continua valendo como caixa — ali é fundo hoje —, e o comentário do teste registra a origem, o que evita que alguém a leia como medida da arte atual.
- 🟡 **As duas rotas servem o arquivo do disco a cada requisição**, sem cache em memória.
- 🟡 **A folga dos limites é declarada, não medida por experimento controlado.** `CLARO_MINIMO = 160` e `SATURACAO_MAXIMA = 50` "saem de medição" com folga para os dois lados; os **11 pontos** são a rede contra o aperto indevido, mas não há estudo de quanto de folga sobra em cada direção.
- 🟡 **A receita vive em `tests/` e não em um módulo de produção.** É o que mantém `PIL` fora do runtime, e o preço é que a transformação que produz a arte **entregue ao operador** depende de código de teste para ser reproduzida.
- 🟢 **A unit não depende de nenhuma outra** (`modules.json` declara `dependencies: []`), e é a única assim: pode ser reimplementada isoladamente.
- 🟢 **As duas rotas são o mesmo desenho, deliberadamente** — não há uma diferença de contrato entre elas que precise ser aprendida duas vezes.

---

*Gerado pelo Reversa-Writer em 2026-10-10 (re-extração). Unit nova.*

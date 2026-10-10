# Unit `recursos-da-tela` — Requisitos

> Unit do tipo **endpoint** — cobre `GET /apple-touch-icon.png` e `GET /banner.png`.
> Spec gerada pelo Reversa-Writer na re-extração de **2026-10-10** (nível **Completo**).
> Unit **nova**: esta é a sua primeira especificação. Ela nasceu das features **009** (ícone de atalho) e **011** (arte do topo, com a `T044` invertendo a `T036`), e **não tem equivalente** nas extrações de 2026-08-03, 2026-09-30 e 2026-10-05.
> ⚠️ **A unit tem ZERO linhas úteis próprias de módulo:** as duas rotas moram em `src/app.py`. Ela existe como unidade de **contrato**, não de arquivo — dois contratos HTTP distintos, com regras próprias de degradação, cache e derivação de arte, e um corpo de testes dedicado.
> Fontes: `code-analysis.md` §6 (30 regras `BR-E-01`..`BR-E-30`), `flowcharts/recursos-da-tela.md` (§6 e §7), `.dockerignore`, `tests/{icone_de_atalho,banner_da_tela}.py` (as receitas), `tests/{test_icone_de_atalho,test_banner_do_topo,test_deriva_da_arte}.py`, `adrs/` (28, 29)
> Evidência de execução (2026-10-10): `src/assets/apple-touch-icon.png` = **16.504 bytes**; `src/assets/banner-da-tela.png` = **317.058 bytes**; `docs/assets/img/logo.png` = 32.317 bytes; `docs/assets/img/banner-analisador.png` = 926.083 bytes; `docs/assets/img/apple-touch-icon.png` = 16.504 bytes (byte a byte igual à de runtime).
> Escala de confiança: 🟢 CONFIRMADO | 🟡 INFERIDO | 🔴 LACUNA

---

## Visão Geral

Serve as **duas artes de runtime** da tela — o ícone de atalho do sistema móvel e o banner do topo — a partir de caminhos **convencionais** que ninguém declara: `/apple-touch-icon.png` e `/banner.png`. 🟢

A regra que define a unit é que **a arte servida não é a arte canônica**: as duas respostas são **renderizações derivadas**, e a receita que as produz tem **fonte única em `tests/`**, com um teste de deriva ao lado dela. A derivação não é estética — servir o arquivo como ele chegou produz um defeito **visível**: quadrado preto no atalho e grade cinza atrás do logo. 🟢

Ela resolve três problemas ao mesmo tempo: **degradação silenciosa** (arte ausente é `404` vazio, e nada mais muda), **revalidação barata sem prender o cliente** (`ETag` em vez de validade longa) e **sobrevivência ao container** (a arte mora onde a lista de permissão do `.dockerignore` a deixa entrar). 🟢

## Responsabilidades

- Registrar as duas rotas **somente** com `GET`, deixando a recusa de escrita para o roteador. 🟢
- Servir o arquivo apontado por `app.config["ARTE_DO_ICONE"]` e por `app.config["ARTE_DO_TOPO"]`. 🟢
- Degradar para **`404` com resposta vazia** quando a arte não está no disco, sem afetar nenhuma outra rota. 🟢
- Declarar `mimetype="image/png"` nas duas respostas. 🟢
- Ancorar os caminhos no **arquivo do app**, e não no diretório corrente. 🟢
- Sustentar a **revalidação por `ETag`**, com `304` sem corpo, e **não** prometer validade longa. 🟢
- Manter a **receita de derivação** das duas artes como fonte única, em código de teste. 🟢
- Manter as artes derivadas **commitadas** em `src/assets/`, e não geradas em tempo de execução. 🟢
- Manter a **masthead** na ordem imagem → subtítulo → título em texto → apresentação. 🟢

## Regras de Negócio

### O contrato das duas rotas

- As rotas são registradas **somente** com `GET` (`BR-E-01`): a recusa de escrita sai do **roteador**, com `405`, e não de uma validação escrita à mão que pudesse divergir da convenção. 🟢
- A rota do ícone serve `app.config["ARTE_DO_ICONE"]`; a do banner, `app.config["ARTE_DO_TOPO"]` (`BR-E-02`). 🟢
  - 🟢 **Os caminhos ficam em `config` para que o caso de ausência seja testável sem tocar no repositório:** o teste aponta a chave para um caminho inexistente em vez de mexer na arte de verdade.
- Arte ausente devolve **resposta vazia com `404`**, e **nada mais muda** (`BR-E-03`): o atalho degrada para ícone genérico, e a tela continua de pé. 🟢
- As duas rotas declaram `mimetype="image/png"` (`BR-E-04`). 🟢
- Os caminhos são ancorados no **arquivo do app** (`BR-E-05`), e não no diretório corrente. 🟢
- **Não há `Cache-Control` de validade longa** (`BR-E-06`); a revalidação barata é o `ETag` do `send_file`, que responde `304` sem corpo. 🟢
  - 🟢 **O motivo é medido:** a arte do ícone foi trocada **duas vezes em um único dia**, e uma validade de um ano congelaria o cliente que já tivesse buscado — o `ETag` só age **depois** de a validade expirar.
- **As duas rotas são o mesmo desenho, e isso é deliberado:** não há diferença de contrato entre elas. 🟢

### Descoberta e superfície

- O ícone de atalho é descoberto por **caminho convencional** na raiz; o template **não** o declara (`BR-E-07`). Não há como declarar o ícone de atalho no documento e ser obedecido. 🟢
- O ícone da **aba** continua sendo um `data URI` embutido no documento, e **não** uma segunda rota (`BR-E-08`). 🟢
- `favicon.ico` e `apple-touch-icon-precomposed.png` **não** têm rota (`BR-E-09`): superfície sem consumidor. O `favicon.ico` só é buscado quando o documento **não** declara ícone, e o template declara um. 🟢

### A derivação do ícone

- A arte do ícone é uma **renderização derivada**: a canônica **composta sobre branco** e reamostrada para **180×180** (`BR-E-10`). 🟢
  - 🟢 **Compor sobre branco** porque a arte tem **32,5 %** de pixels totalmente transparentes (os quatro cantos em `(0,0,0,0)`), e o sistema móvel compõe transparência sobre **preto**: servir a arte crua daria um quadrado preto com o desenho por cima, **incluindo as aberturas internas** entre folhas e galhos.
  - 🟢 **180×180** porque é a medida que o sistema espera; outra medida é reamostrada por ele e perde nitidez.
- O fundo da composição é **branco** (`BR-E-11`): a arte tem **51,5 %** de creme em **duas tonalidades**, e eleger uma faria a outra parecer errada. 🟢
- Os cantos ficam **retos** (`BR-E-12`): o sistema aplica a própria máscara arredondada, e arredondar aqui produziria arredondamento duplo, com um anel de fundo no canto. 🟢
- O PNG derivado tem **16.504 bytes**, e esse número é a **âncora** que denuncia reamostragem, fundo ou compressão diferentes (`BR-E-13`). 🟢
- A opacidade do ícone é provada pelo **tipo de cor 2** (`truecolor` **sem** canal alfa) lido do IHDR, **sem biblioteca de imagem** (`BR-E-14`): não existe pixel transparente num PNG cujo cabeçalho diz que não há canal alfa. 🟢

### A derivação do banner

- A arte do banner é uma **renderização derivada com o fundo removido** (`BR-E-15`), porque a fonte chegou em `RGB`, **sem alfa**, com o quadriculado de transparência **gravado no bitmap** — servir aquilo desenharia uma grade cinza atrás do logo. 🟢
- A remoção de fundo é **global**, e não por inundação a partir da borda (`BR-E-16`). 🟢
  - 🟢 **A inundação foi medida como insuficiente:** a árvore, o livro e o texto formam **anúncios fechados**, e o fundo preso dentro deles nunca é alcançado. Medido no resultado da primeira versão: o pixel `(300,150)` continuava opaco e sobravam **8.379** pixels de tom de fundo opacos numa amostra de 1/9 da imagem.
- Um pixel é fundo em **duas faixas** (`BR-E-17`): brilho **≥ 190** com saturação **≤ 50**, e brilho **160–190** com saturação **≤ 12**; **abaixo de 160 nunca é fundo**. 🟢
  - 🟢 **A separação existe porque o quadriculado é neutro e a tinta clara da arte é levemente quente.** Com um limite único de `brilho ≥ 160 e saturação ≤ 50`, o fundo (saturação 0–7) **e** o preenchimento do texto dourado (brilho ≈212, saturação ≈24) caíam os dois no fundo, e as letras ficavam **ocas** — defeito medido no composto sobre magenta.
- `CLARO_MINIMO = 160` e `SATURACAO_MAXIMA = 50` **saem de medição**, com folga declarada nos dois lados (`BR-E-18`). 🟢
- A fronteira recebe **alfa proporcional** à distância do fundo (`BR-E-19`): entre a arte e o xadrez há uma faixa de um a dois pixels de cinza intermediário, e deixá-la opaca desenharia um **halo claro** em volta de tudo. 🟢
- O **resíduo** é medido com limite **mais estrito** que o da regra, e precisa ser **zero** na caixa de regressão (`BR-E-20`). 🟢
  - 🟢 **Não é elegância:** medir o resíduo com o mesmo limite da regra devolve **sempre zero**, e foi exatamente esse erro que deixou um bloco inteiro de quadriculado passar **duas vezes** — a métrica dizia `0,00 %` enquanto o composto sobre magenta mostrava o bloco.
- **Onze pontos** da arte têm de continuar **opacos** (`BR-E-21`), cobrindo as duas famílias de risco: arte **escura e pouco saturada** (capa, lombada, base do livro) e arte **clara e quase neutra** (o preenchimento do texto dourado). 🟢

### Onde a arte mora, e por que ela é commitada

- A arte de runtime mora em `src/assets/`, porque o `.dockerignore` é lista de **permissão** (`*`, depois `!requirements.txt`, `!src/`, `!src/**`) — `BR-E-22`. 🟢
  - 🟢 **A falha que a lista evita é silenciosa:** arte fora de `src/` responde **200 na máquina de desenvolvimento** e **404 no container** — o ambiente que o operador usa. A escolha de pasta **não é estética**.
- `src/static/` é **proibida** (`W004`), e há teste que falha se a arte cair numa pasta estática (`BR-E-23`). 🟢
- `src/uploads/` é **reexcluído** do contexto de build **depois** de `!src/**` (`BR-E-24`), porque carrega dado real do operador — **13 arquivos** (mais 4 aposentados), entre eles um GEDCOM de 5,3 MB. A última regra que casa vence. 🟢
- A arte derivada é **commitada**, e não gerada em tempo de execução (`BR-E-25`): a fonte canônica mora em `docs/`, que **não entra na imagem** — dentro do container não existe fonte para gerar nada —, e gerar no host a cada partida seria I/O no import de `src/app.py`, módulo que a suíte e o harness de paridade importam. 🟢

### O contrato da receita e do teste de deriva

- A receita tem **fonte única** em `tests/`, e o teste de deriva a importa e compara **pixel** com o arquivo commitado (`BR-E-26`). 🟢
- A comparação por **`sha256`** entre canônica e derivada é **proibida na prática** (`BR-E-27`): o **mesmo** desenho existe em disco com 32.317 bytes e, vindo de outra codificação, com 44.069 bytes — e a diferença de pixel entre os dois é **zero**. Um teste que grita sem motivo é desligado. 🟢
- A **biblioteca de imagem não entra em `requirements.txt`**, que é lista de **runtime** (`BR-E-28`); há teste que falha se `pillow`/`PIL==` aparecer lá. O container não precisa dela porque a arte chega pronta dentro da imagem, e o `import` na receita é **preguiçoso**, dentro das funções. 🟢

### A masthead

- A masthead segue a ordem **imagem → subtítulo → título em texto → texto de apresentação** (`BR-E-29`), e a ordem tem teste próprio. 🟢
  - 🟢 **O título voltou a ser texto:** a `T036` trocou o `<h1>` por imagem, e a `T044` inverteu isso. O título sobrevive à arte ausente **por construção**, e não por depender do `alt`.
- A arte do topo é reduzida a **`w-50`**, e o `alt` descreve a **ilustração**, nunca o título (`BR-E-30`). 🟢 Com o título escrito logo abaixo, repeti-lo no `alt` faria o leitor de tela anunciar a mesma coisa duas vezes. 🟢

## Requisitos Funcionais

| ID | Requisito | Prioridade | Critério de Aceite |
| --- | --- | --- | --- |
| RF-01 | Registrar as duas rotas **somente** com `GET` | Must | `POST`, `PUT` e `DELETE` nos dois caminhos devolvem `405`, sem validação própria 🟢 |
| RF-02 | Servir o arquivo apontado por `app.config["ARTE_DO_ICONE"]` / `["ARTE_DO_TOPO"]` | Must | Trocar a chave muda o arquivo servido, sem tocar no código 🟢 |
| RF-03 | Degradar para **`404` com resposta vazia** quando a arte não está no disco | Must | Corpo vazio, `404`, e nenhuma outra rota altera a resposta 🟢 |
| RF-04 | Declarar `mimetype="image/png"` nas duas respostas | Must | `Content-Type: image/png` no `200` 🟢 |
| RF-05 | Ancorar os caminhos no **arquivo do app** | Must | A rota funciona com o processo iniciado de qualquer diretório de trabalho 🟢 |
| RF-06 | Sustentar a revalidação por **`ETag`**, sem validade longa | Must | `ETag` presente no `200`; revalidação com `If-None-Match` devolve **`304` sem corpo**; nenhum `Cache-Control` de validade longa 🟢 |
| RF-07 | Ser descoberto por **caminho convencional**, sem declaração no documento | Must | O template **não** menciona `/apple-touch-icon.png`; o `GET /` continua byte a byte o mesmo 🟢 |
| RF-08 | Manter o ícone da **aba** como `data URI` embutido | Must | Nenhuma segunda rota de ícone é criada 🟢 |
| RF-09 | **Não** responder em `favicon.ico` nem em `apple-touch-icon-precomposed.png` | Should | Os dois caminhos devolvem `404` 🟢 |
| RF-10 | Derivar o ícone: canônica **composta sobre branco**, **180×180**, cantos retos | Must | O PNG derivado tem 180×180 e **tipo de cor 2** (sem canal alfa) 🟢 |
| RF-11 | Fixar **16.504 bytes** como âncora do ícone derivado | Should | Reamostragem, fundo ou compressão diferentes mudam o tamanho e o teste cai 🟢 |
| RF-12 | Provar a opacidade pelo **IHDR**, sem biblioteca de imagem | Should | O teste lê o tipo de cor do cabeçalho e não importa `PIL` 🟢 |
| RF-13 | Derivar o banner com **remoção de fundo global** | Must | O fundo é removido onde ele estiver, inclusive dentro dos bolsões fechados da arte 🟢 |
| RF-14 | Aplicar as **duas faixas** de brilho/saturação, com o piso em 160 | Must | Pixel abaixo de 160 **nunca** é fundo; o texto dourado não fica oco 🟢 |
| RF-15 | Aplicar **alfa proporcional** na fronteira | Must | Nenhum halo claro em volta da arte no composto 🟢 |
| RF-16 | Medir o resíduo com limite **mais estrito** que o da regra, exigindo **zero** na caixa de regressão | Must | A caixa `(778,232)–(918,338)` tem resíduo zero 🟢 |
| RF-17 | Preservar **onze pontos** de arte opacos | Must | Os 11 pontos cobrem arte escura pouco saturada e arte clara quase neutra 🟢 |
| RF-18 | Manter as artes derivadas **commitadas** em `src/assets/` | Must | O arquivo existe no repositório e a rota o serve sem gerar nada 🟢 |
| RF-19 | Manter a **receita com fonte única** em `tests/`, importada pelo teste de deriva | Must | Existe uma só definição da transformação; o teste a importa 🟢 |
| RF-20 | Comparar a deriva por **pixel**, nunca por `sha256` | Must | Recompressão do mesmo desenho não é reportada como deriva 🟢 |
| RF-21 | Provar que a comparação **detecta um pixel alterado** | Must | O teste de deriva demonstra a própria sensibilidade, para não passar por vacuidade 🟢 |
| RF-22 | **Não** incluir a biblioteca de imagem em `requirements.txt` | Must | Há teste que falha se `pillow`/`PIL==` aparecer no arquivo 🟢 |
| RF-23 | Falhar se a arte estiver numa pasta estática | Must | `src/static/` é proibida (`W004`) e o teste guarda isso 🟢 |
| RF-24 | Manter a **masthead** na ordem imagem → subtítulo → título em texto → apresentação | Must | A ordem tem teste próprio 🟢 |
| RF-25 | Reduzir a arte do topo a `w-50`, com `alt` que descreve a **ilustração** | Should | O `alt` não repete o título; o `<h1>` traz o texto 🟢 |

## Requisitos Não Funcionais

| Tipo | Requisito inferido | Evidência no código | Confiança |
|------|--------------------|---------------------|-----------|
| Disponibilidade | **Degradação silenciosa**: arte ausente é `404` vazio, e a tela continua de pé — o título é texto, e o atalho cai no ícone genérico | `app.py:279-280`, `:316-317` | 🟢 |
| Performance | **Revalidação barata por `ETag`**, com `304` sem corpo, em vez de validade longa que congelaria o cliente | `app.py:270-273`, `:312-313` | 🟢 |
| Performance | 🟡 As duas rotas **servem o arquivo do disco a cada requisição**, sem cache em memória. Com 317 KB no banner, o custo é do sistema operacional via `send_file`, não do processo. **Não há medição de impacto no repositório** | `app.py:281`, `:318` | 🟡 |
| Portabilidade | A arte mora em `src/assets/` porque o `.dockerignore` é **lista de permissão**: fora de `src/`, responderia `200` no host e `404` no container | `.dockerignore`, `app.py:251-254` | 🟢 |
| Segurança | `src/uploads/` é reexcluído do contexto de build, porque carrega **dado real do operador** — inclusive um GEDCOM de 5,3 MB | `.dockerignore` | 🟢 |
| Manutenibilidade | A receita de derivação tem **fonte única** e vive em `tests/`; a comparação é por **pixel**, e o teste prova a própria sensibilidade | `tests/icone_de_atalho.py`, `tests/banner_da_tela.py`, `tests/test_deriva_da_arte.py` | 🟢 |
| Manutenibilidade | 🟡 O `sha256` do HTML de `GET /` em `test_icone_de_atalho.py` é um **invariante mantido à mão**, atualizado **três vezes em 2026-10-10**. Enquanto cada atualização for uma decisão humana registrada, ele prende o que promete; se virar rotina, deixa de prender | `tests/test_icone_de_atalho.py` | 🟡 |
| Confiabilidade | 🔴 **Não há verificação de que a arte servida é a derivada correta no ambiente do container** — os testes rodam no host, onde `docs/` existe | — | 🔴 |
| Observabilidade | **Nenhum log, métrica ou trace.** A ausência de arte não é registrada em lugar nenhum | — | 🟢 |
| Internacionalização | O único texto próprio é o `alt` da ilustração, em português | `templates/index.html` | 🟢 |

> Inferido a partir do código. **Não** há autenticação, timeout, retry, fila ou cache distribuído — as linhas correspondentes foram omitidas por falta de evidência.

## Critérios de Aceitação

```gherkin
Dado que a arte do ícone existe em src/assets/
Quando o cliente requisita GET /apple-touch-icon.png
Então a resposta é 200, com Content-Type image/png
E o corpo tem 16.504 bytes
E o PNG é 180x180 e declara tipo de cor 2 no IHDR

Dado que a arte do banner existe em src/assets/
Quando o cliente requisita GET /banner.png
Então a resposta é 200, com Content-Type image/png
E o PNG é RGBA
E a caixa de regressão (778,232)–(918,338) tem resíduo de fundo ZERO
E os onze pontos de arte continuam opacos

Dado que a arte não está no disco
Quando o cliente requisita a rota
Então a resposta é 404 com corpo VAZIO
E nenhuma outra rota altera a resposta por causa disso

Dado que o cliente já buscou a arte e recebeu o ETag
Quando ele revalida com If-None-Match
Então a resposta é 304 SEM corpo
E nenhuma validade longa de cache foi prometida

Dado o caminho convencional do ícone de atalho
Quando o cliente tenta POST no mesmo caminho
Então a resposta é 405, pelo roteador, sem uma linha de validação própria

Dado o documento da tela
Quando a masthead é renderizada
Então a ordem é imagem, subtítulo, título em texto e apresentação
E a arte aparece com w-50
E o alt descreve a ilustração, e não o título

Dado que alguém altera UM pixel do arquivo commitado
Quando o teste de deriva roda
Então ele detecta a divergência

Dado que alguém recomprime o mesmo desenho
Quando o teste de deriva roda
Então ele NÃO reporta deriva, porque a comparação é por pixel

Dado que alguém acrescenta pillow ao requirements.txt
Quando o teste de deriva roda
Então ele falha — a biblioteca de imagem não é dependência de runtime
```

## Prioridade (MoSCoW)

| Requisito | MoSCoW | Justificativa |
|-----------|--------|---------------|
| RF-03 Degradação em `404` vazio | **Must** | É o que impede a arte ausente de derrubar a tela |
| RF-10 e RF-13 Derivação das duas artes | **Must** | Servir a arte crua produz defeito **visível** — quadrado preto e grade cinza |
| RF-14/RF-15/RF-16/RF-17 Qualidade da remoção de fundo | **Must** | Letras ocas e halo são defeitos medidos, e o resíduo não-circular é o que os pega |
| RF-01/RF-04/RF-05 Contrato HTTP das rotas | **Must** | Base do contrato; a recusa de escrita vem do roteador |
| RF-06 Revalidação por `ETag` | **Must** | A arte muda com o pedido do operador; validade longa congelaria o cliente |
| RF-18/RF-19/RF-20 Arte commitada, receita única, comparação por pixel | **Must** | Sem isso a deriva fica invisível, ou o teste grita sem motivo |
| RF-22 Biblioteca de imagem fora do runtime | **Must** | `requirements.txt` é lista de runtime; o container não precisa dela |
| RF-23 Arte fora de pasta estática | **Must** | `W004` — é a garantia de que a arte não vira superfície estática |
| RF-24/RF-25 Ordem da masthead e `alt` próprio | **Must** | A ordem foi revertida uma vez (`T036` → `T044`); o teste a prende |
| RF-07/RF-08 Descoberta convencional e `data URI` | **Should** | A rota funciona sem isso; o que muda é a coerência com a convenção do sistema |
| RF-11 Âncora de 16.504 bytes | **Should** | Denuncia deriva de reamostragem; há outras provas (180×180, tipo de cor 2) |
| RF-12 Leitura do IHDR sem `PIL` | **Should** | Prova a opacidade sem depender da biblioteca, que não está instalada |
| RF-09 Caminhos não servidos | **Could** | Superfície deliberadamente ausente; o teste só a documenta |
| RF-21 Prova de sensibilidade do teste | **Could** | Protege contra o modo de falha mais perigoso (passar por vacuidade) |

## Rastreabilidade de Código

| Arquivo | Função / símbolo | Cobertura |
|---------|------------------|-----------|
| `src/app.py` | `ARTE_DO_ICONE` + `icone_de_atalho`, `ARTE_DO_TOPO` + `banner_do_topo`, as duas chaves de `app.config` | 🟢 |
| `src/assets/apple-touch-icon.png` | PNG 16.504 bytes, 180×180, tipo de cor 2 | 🟢 |
| `src/assets/banner-da-tela.png` | PNG RGBA 317.058 bytes, com o fundo removido | 🟢 |
| `tests/icone_de_atalho.py` | `arte_derivada`, `bytes_da_arte`, `gravar_arte`, `TAMANHO_ESPERADO`, `FUNDO`, `ARTE_CANONICA`, `ARTE_DE_RUNTIME` | 🟢 |
| `tests/banner_da_tela.py` | `_e_fundo`, `mascara_do_fundo`, `arte_limpa`, `residuo_de_fundo`, `CLARO_MINIMO`, `SATURACAO_MAXIMA` | 🟢 |
| `tests/test_deriva_da_arte.py` | `_imagens_diferem` e as cinco provas do contrato da deriva | 🟢 |
| `tests/test_icone_de_atalho.py` | Contrato das rotas, IHDR, ausência de rotas não servidas, `sha256` do HTML | 🟢 |
| `tests/test_banner_do_topo.py` | Contrato das rotas, ordem da masthead, resíduo zero e os 11 pontos | 🟢 |
| `.dockerignore` | Lista de **permissão**; `src/uploads/` reexcluído depois de `!src/**` | 🟢 |
| `src/templates/index.html` | A masthead: imagem, subtítulo, `<h1>` em texto e apresentação | 🟢 |
| `docs/assets/img/logo.png`, `banner-analisador.png` | As **fontes canônicas** da receita — **não** entram na imagem | 🟢 |

---

*Gerado pelo Reversa-Writer em 2026-10-10 (re-extração). Unit nova — não substitui artefato anterior.*

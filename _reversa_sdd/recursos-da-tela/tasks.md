# Unit `recursos-da-tela` — Tarefas de Implementação

> Spec gerada pelo Reversa-Writer na re-extração de **2026-10-10** (nível **Completo**). Unit **nova**.
> ⚠️ **A unit tem zero linhas próprias de módulo:** as duas rotas moram em `src/app.py` e as receitas de derivação em `tests/`. As tarefas abaixo cobrem **os dois lados**, porque o contrato da arte servida é feito dos dois.
> Cada tarefa cita o arquivo do legado de onde o comportamento foi extraído.
> Escala de confiança: 🟢 CONFIRMADO | 🟡 INFERIDO | 🔴 LACUNA

---

## Pré-requisitos

- [ ] **Flask 3.1.3** disponível (`send_file` é quem emite o `ETag`) 🟢
- [ ] As **fontes canônicas** presentes em `docs/assets/img/`: `logo.png` (512×512 RGBA) e `banner-analisador.png` (`RGB`) 🟢
- [ ] **Pillow disponível no ambiente de teste** — e **apenas** nele: a biblioteca **não** entra em `requirements.txt` 🟢
- [ ] `src/assets/` existente, sob `src/` — porque o `.dockerignore` é lista de **permissão** 🟢
- [ ] **`src/static/` não pode existir** (`W004`) 🟢
- [ ] **Não aplicável:** schema, banco, variável de ambiente ou dependência de outra unit — `modules.json` declara `dependencies: []` 🟢
- [ ] As artes derivadas **commitadas** em `src/assets/` antes de a rota ser exercitada 🟢

## Tarefas

### As duas rotas

- [ ] T-01, Implementar `icone_de_atalho` com o caminho vindo de `app.config["ARTE_DO_ICONE"]`
  - Origem no legado: `src/app.py:255-281`
  - Critério de pronto: registrada **só** com `GET`; lê a chave de `config`; `isfile` falso → `("", 404)`; verdadeiro → `send_file(..., mimetype="image/png")`
  - Confiança: 🟢

- [ ] T-02, Implementar `banner_do_topo` com o **mesmo desenho** de rota
  - Origem no legado: `src/app.py:300-318`
  - Critério de pronto: idêntica à anterior, lendo `app.config["ARTE_DO_TOPO"]`. **Nenhuma diferença de contrato entre as duas**
  - Confiança: 🟢

- [ ] T-03, Ancorar os dois caminhos no **arquivo do app**
  - Origem no legado: `src/app.py:255-257`, `:300-302`
  - Critério de pronto: `os.path.join(os.path.dirname(os.path.abspath(__file__)), "assets", …)`; as rotas funcionam com o processo iniciado de qualquer diretório de trabalho
  - Confiança: 🟢

- [ ] T-04, Expor os caminhos como **chaves de `app.config`**
  - Origem no legado: `src/app.py:258-260`, `:303-305`
  - Critério de pronto: `app.config["ARTE_DO_ICONE"]` e `app.config["ARTE_DO_TOPO"]` existem no import; apontar uma delas para um caminho inexistente **não** exige tocar no repositório para testar a ausência
  - Confiança: 🟢

- [ ] T-05, **Não** declarar `Cache-Control` de validade longa, e não escrever o `304` à mão
  - Origem no legado: `src/app.py:270-273`, `:312-313`
  - Critério de pronto: nenhum cabeçalho de validade longa na resposta; o `ETag` é o do `send_file`, e a rebusca com `If-None-Match` devolve `304` **sem corpo**
  - Confiança: 🟢
  - ⚠️ A arte foi trocada **duas vezes em um único dia**: validade de um ano congelaria o cliente que já tivesse buscado. O `ETag` só age **depois** de a validade expirar — por isso não há validade

- [ ] T-06, Garantir que a ausência da arte devolve **`404` vazio** sem afetar nenhuma outra rota
  - Origem no legado: `src/app.py:279-280`, `:316-317`
  - Critério de pronto: corpo vazio e status `404`; nenhuma rota existente altera a resposta por causa disso
  - Confiança: 🟢

- [ ] T-07, **Não** criar rota para `favicon.ico` nem para `apple-touch-icon-precomposed.png`, e manter o ícone da aba como `data URI`
  - Origem no legado: `templates/index.html:8`; `tests/test_icone_de_atalho.py`
  - Critério de pronto: os dois caminhos devolvem `404`; existe **um** ícone declarado no documento, e é `data URI`
  - Confiança: 🟢
  - ⚠️ O `favicon.ico` só é buscado quando o documento **não** declara ícone. Criar a rota seria **superfície sem consumidor**

### A receita do ícone

- [ ] T-08, Implementar `arte_derivada`: **compor sobre branco** e reamostrar para **180×180**
  - Origem no legado: `tests/icone_de_atalho.py:arte_derivada`
  - Critério de pronto: a canônica (RGBA, 32,5 % transparente) é composta sobre **branco opaco**, reamostrada com **LANCZOS** para 180×180 e convertida para **RGB** com os **cantos retos**
  - Confiança: 🟢
  - ⚠️ **As três transformações têm motivo medido:** o sistema móvel compõe transparência sobre **preto** (servir a arte crua daria um quadrado preto, inclusive nas aberturas internas entre folhas e galhos); 180×180 é a medida que ele espera; e ele aplica a **própria máscara arredondada**, de modo que arredondar aqui produziria arredondamento duplo

- [ ] T-09, Fixar o fundo em **branco** e os cantos em **retos**
  - Origem no legado: `tests/icone_de_atalho.py:FUNDO`
  - Critério de pronto: a arte tem 51,5 % de creme em **duas** tonalidades; eleger uma delas faria a outra parecer errada, então o fundo é branco. Nenhum raio de canto é aplicado
  - Confiança: 🟢

- [ ] T-10, Gravar a arte commitada e fixar a **âncora de bytes**
  - Origem no legado: `tests/icone_de_atalho.py:bytes_da_arte`, `gravar_arte`, `TAMANHO_ESPERADO`
  - Critério de pronto: `src/assets/apple-touch-icon.png` com **16.504 bytes**; o número está no código como âncora que denuncia reamostragem, fundo ou compressão diferentes
  - Confiança: 🟢

### A receita do banner

- [ ] T-11, Implementar `_e_fundo` com as **duas faixas** de brilho e saturação
  - Origem no legado: `tests/banner_da_tela.py:_e_fundo`
  - Critério de pronto: **≥ 190** com saturação ≤ `SATURACAO_MAXIMA` (50) → fundo; **160–190** com saturação ≤ **12** → fundo; **abaixo de 160 → nunca**
  - Confiança: 🟢
  - ⚠️ A separação existe porque o quadriculado é **neutro** e a tinta clara da arte é levemente **quente**. Com um limite único (`≥ 160` e `≤ 50`), o fundo (saturação 0–7) **e** o preenchimento do texto dourado (brilho ≈212, saturação ≈24) caíam os dois no fundo, e as letras ficavam **ocas** — defeito medido no composto sobre magenta

- [ ] T-12, Implementar `mascara_do_fundo` como remoção **global**
  - Origem no legado: `tests/banner_da_tela.py:mascara_do_fundo`
  - Critério de pronto: **todo** pixel de fundo é marcado, **onde ele estiver** — inclusive dentro dos bolsões fechados da arte
  - Confiança: 🟢
  - ⚠️ **Não usar inundação a partir da borda.** A árvore, o livro e o texto formam **anúncios fechados**; medido no resultado da primeira versão: o pixel `(300,150)` continuava opaco e sobravam **8.379** pixels de tom de fundo opacos numa amostra de **1/9** da imagem

- [ ] T-13, Implementar `arte_limpa` com a **segunda passada** de alfa proporcional
  - Origem no legado: `tests/banner_da_tela.py:arte_limpa`
  - Critério de pronto: os pixels marcados ficam transparentes, e a **fronteira** recebe alfa **proporcional** à distância do fundo — quanto mais claro o pixel, mais transparente
  - Confiança: 🟢
  - ⚠️ Existe por causa do **serrilhado**: entre a arte e o xadrez há uma faixa de 1–2 pixels de cinza intermediário, e deixá-la opaca desenharia um **halo claro** em volta de tudo

- [ ] T-14, Implementar `residuo_de_fundo` com limite **mais estrito** que o da regra
  - Origem no legado: `tests/banner_da_tela.py:residuo_de_fundo`
  - Critério de pronto: mede com `SATURACAO_MAXIMA - 5`, e **não** com o limite da regra
  - Confiança: 🟢
  - ⚠️ **A métrica seria circular se usasse o mesmo limite, e devolveria sempre zero.** Foi exatamente esse erro que deixou um bloco inteiro de quadriculado passar **duas vezes**: a métrica dizia `0,00 %` enquanto o composto sobre magenta mostrava o bloco

- [ ] T-15, Gravar a arte commitada do banner
  - Origem no legado: `tests/banner_da_tela.py`
  - Critério de pronto: `src/assets/banner-da-tela.png` em **RGBA**, com o fundo removido; **317.058 bytes** medidos em 2026-10-10
  - Confiança: 🟢

### O contrato da deriva e da pasta

- [ ] T-16, Manter a **fonte única** da receita em `tests/`, e o teste de deriva importando-a
  - Origem no legado: `tests/test_deriva_da_arte.py`
  - Critério de pronto: existe **uma só** definição de cada transformação; o teste regenera a derivada em memória e compara com o arquivo commitado
  - Confiança: 🟢

- [ ] T-17, Comparar **pixel a pixel**, e provar que a comparação detecta **um** pixel
  - Origem no legado: `tests/test_deriva_da_arte.py:_imagens_diferem`
  - Critério de pronto: comparação por pixel; e o teste demonstra a própria sensibilidade alterando **um** pixel — sem essa prova ele poderia estar comparando algo consigo mesmo e passar por vacuidade
  - Confiança: 🟢
  - ⚠️ **`sha256` é proibido na prática:** o mesmo desenho existe em disco com **32.317** bytes e, vindo de outra codificação, com **44.069** bytes — com diferença de pixel **zero**. Um teste que grita sem motivo é desligado

- [ ] T-18, Falhar se `pillow`/`PIL==` aparecer em `requirements.txt`
  - Origem no legado: `tests/test_deriva_da_arte.py`
  - Critério de pronto: o teste varre o arquivo de dependências e falha ao encontrar a biblioteca; o `import` na receita é **preguiçoso**, dentro das funções
  - Confiança: 🟢

- [ ] T-19, Falhar se a arte estiver numa pasta estática
  - Origem no legado: `tests/test_deriva_da_arte.py`
  - Critério de pronto: arte sob `src/` e **não** sob `src/static/` (`W004`)
  - Confiança: 🟢

- [ ] T-20, Manter `src/uploads/` reexcluído no `.dockerignore`, **depois** de `!src/**`
  - Origem no legado: `.dockerignore`
  - Critério de pronto: a lista é de **permissão** (`*`, `!requirements.txt`, `!src/`, `!src/**`), e a linha de exclusão de `src/uploads/` vem **depois** — a última regra que casa vence
  - Confiança: 🟢
  - ⚠️ A pasta carrega **dado real do operador**. Enviá-la ao daemon do Docker seria a mesma classe de exposição que o Princípio I proíbe

### A masthead

- [ ] T-21, Montar a masthead na ordem **imagem → subtítulo → título em texto → apresentação**
  - Origem no legado: `templates/index.html`
  - Critério de pronto: a ordem tem teste próprio; o `<h1>` traz o **texto** do título
  - Confiança: 🟢
  - ⚠️ A ordem já foi invertida uma vez: a `T036` trocou o `<h1>` por imagem e a `T044` reverteu

- [ ] T-22, Reduzir a arte do topo a **`w-50`** e dar-lhe um `alt` próprio
  - Origem no legado: `templates/index.html`, `tests/test_banner_do_topo.py`
  - Critério de pronto: `class="w-50"`; o `alt` descreve a **ilustração** e **não** repete o título
  - Confiança: 🟢
  - ⚠️ Com o título escrito logo abaixo, repeti-lo no `alt` faria o leitor de tela anunciar a mesma coisa **duas vezes**

## Tarefas de Teste

- [ ] TT-01, `200` com `Content-Type: image/png` nas duas rotas 🟢
- [ ] TT-02, `405` para `POST`/`PUT`/`DELETE` nos dois caminhos, **pelo roteador** 🟢
- [ ] TT-03, `404` com corpo **vazio** quando a arte não está no disco — apontando a chave de `config` para caminho inexistente 🟢
- [ ] TT-04, `ETag` presente, `304` sem corpo na revalidação, e **nenhuma** validade longa declarada 🟢
- [ ] TT-05, O ícone é 180×180 e declara **tipo de cor 2** no IHDR, lido **sem** `PIL` 🟢
- [ ] TT-06, O ícone tem **16.504 bytes** 🟢
- [ ] TT-07, O `GET /` **não** mudou (âncora `sha256` do HTML, mantida à mão) e **não** declara o ícone de atalho 🟢
- [ ] TT-08, `favicon.ico` e `apple-touch-icon-precomposed.png` seguem **`404`** 🟢
- [ ] TT-09, O banner é **RGBA**, entre 10 % e 90 % transparente 🟢
- [ ] TT-10, **Resíduo ZERO** na caixa de regressão `(778,232)–(918,338)` 🟢
- [ ] TT-11, Os **11 pontos** de arte continuam opacos: arte escura pouco saturada e arte clara quase neutra 🟢
- [ ] TT-12, A **ordem da masthead** é imagem → subtítulo → título → apresentação, com `w-50`, `<h1>` em texto e `alt` próprio 🟢
- [ ] TT-13, O teste de deriva detecta **um** pixel alterado 🟢
- [ ] TT-14, Recompressão do mesmo desenho **não** é deriva 🟢
- [ ] TT-15, A arte está sob `src/` e **não** sob pasta estática 🟢
- [ ] TT-16, `requirements.txt` **não** cita a biblioteca de imagem 🟢
- [ ] TT-17, 🔴 **Verificação de que a arte servida é a derivada correta dentro do container** — **não existe**. Os testes rodam no host, onde `docs/` existe (`L-33`). Exige um teste que rode na imagem, ou um health check

## Tarefas de Migração de Dados

**Não aplicável** — a unit não persiste nada, não tem banco e não tem volume. O único dado que ela toca são dois arquivos **commitados** no repositório. 🟢

## Ordem Sugerida

1. **T-01 a T-07 (as duas rotas) primeiro.** Elas não dependem das artes existirem — a degradação em `404` é justamente o que se prova sem arquivo. Escrever a rota **antes** da arte força o caso de ausência a ser exercitado.
2. **T-08 a T-10 (a receita do ícone).** É a derivação mais simples, e é ela que estabelece o padrão: compor, reamostrar, gravar, ancorar o tamanho.
3. **T-11 a T-15 (a receita do banner).** **T-14 antes de T-11**: a métrica de resíduo precisa existir para provar que a máscara está certa — e ela é o instrumento que pegou o defeito que passou duas vezes.
4. **T-16 a T-20 (contrato da deriva e da pasta).** Depois das duas receitas, porque o teste de deriva precisa delas para importar.
5. **T-21 e T-22 (a masthead)** por último: dependem de a arte existir para serem conferidas de olho, embora o teste seja estrutural.
6. **TT-01 a TT-16** em paralelo a cada bloco, com **TT-10 e TT-11** fechando a unit: são os dois que pegam a classe de defeito que já passou duas vezes.
7. **Bloqueios:** nenhum entre units — esta é a **única unit sem dependências** declaradas (`dependencies: []`). T-17 depende de T-16; o teste de deriva depende das duas receitas.

## Lacunas Pendentes (🔴)

1. **`L-33` — não há verificação de que a arte servida é a derivada correta no container.** Os testes rodam no host, onde `docs/` existe. Se a arte falhar **dentro da imagem**, a degradação é o `404` — silencioso, sem log e sem teste. **É a lacuna mais relevante da unit**, porque é exatamente o caso que a escolha de `src/assets/` existe para evitar. Exige decisão humana: teste que rode na imagem, ou health check que confira a arte no arranque.
2. **`L-34` — o `sha256` do HTML é um invariante mantido à mão**, atualizado três vezes em 2026-10-10. Decidir se ele continua sendo atualizado por decisão registrada ou se vira uma âncora estrutural (presença/ausência das marcas da masthead) em vez de hash integral.
3. **Não há cache em memória** e não há medição de impacto de servir 317 KB por requisição. **[Verificar]** se o custo justifica alguma forma de cache — lembrando que a arte **muda com o pedido do operador**, e o `ETag` existe justamente por isso.
4. **A folga dos limites** (`CLARO_MINIMO = 160`, `SATURACAO_MAXIMA = 50`, teto 12) é **declarada**, não medida por experimento controlado. Decidir se vale um estudo de quanto sobra em cada direção antes de alguém apertá-los.
5. **A caixa de regressão descreve uma composição que não existe mais** (a do abajur). Decidir se a caixa é redefinida sobre a composição atual ou se o comentário que registra a origem basta.
6. **A receita que produz a arte entregue ao operador é código de teste.** É o preço de manter `PIL` fora do runtime; decidir se esse preço continua valendo quando a arte mudar de novo.

---

*Gerado pelo Reversa-Writer em 2026-10-10 (re-extração). Unit nova.*

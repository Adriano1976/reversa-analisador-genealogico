# ADR-29 — A arte da tela é uma renderização derivada, com receita única e teste de deriva

- **Status:** Aceito e **vigente** — cobre as duas artes (ícone de atalho e banner do topo)
- **Data da decisão:** 2026-10-08 (ícone) e 2026-10-10 (banner)
- **Commit(s):** `ca8e477` e `6d6948e` (ícone, ciclo `009-rota-do-apple-touch-icon`); `73da6c6`, `926a488`, `3f71c49` (banner, ciclo `011-escolher-arquivo-da-lista`)
- **Confiança:** 🟢 CONFIRMADO

## Contexto

Duas necessidades de arte surgiram com dois dias de diferença, e as duas tinham o **mesmo problema estrutural**: o arquivo que o operador ou o designer produz **não é o arquivo que o navegador ou o sistema operacional precisam receber**.

- **Ícone de atalho.** A arte canônica (`docs/assets/img/logo.png`) tem **32,5 %** de pixels totalmente transparentes e os quatro cantos em `(0,0,0,0)`. O sistema móvel compõe transparência **sobre preto** no ícone de tela inicial: servir a canônica produziria um **quadrado preto** com o desenho por cima, incluindo as aberturas internas entre folhas e galhos.
- **Banner do topo.** A arte enviada pelo operador chegou em **`RGB`, sem canal alfa**, com o **quadriculado de transparência gravado dentro do bitmap** (branco `ffffff` alternando com cinza `c7c7c7` em blocos de 8 px). Servir o arquivo como veio desenharia uma **grade cinza** atrás do logo.

Havia ainda uma restrição de empacotamento: o `.dockerignore` é lista de permissão (`ADR-28`), então a **fonte canônica não existe dentro do container**.

## Decisão

**Servir uma renderização DERIVADA, commitada, com a receita em `tests/` e um teste de deriva ao lado.**

1. **A derivada é commitada em `src/assets/`** — o único caminho de arte que entra na imagem. `src/static/` continua proibida (`W004`).
2. **A receita tem fonte única** em `tests/icone_de_atalho.py` e `tests/banner_da_tela.py`, e é **código de teste**, com import preguiçoso da biblioteca de imagem, que **não** entra em `requirements.txt` (lista de runtime).
3. **Ícone:** compor sobre **branco** e reamostrar para **180×180** com LANCZOS, com **cantos retos** — o sistema aplica a própria máscara arredondada, e arredondar aqui produziria arredondamento duplo com um anel de fundo no canto. Fundo **branco** porque a arte tem 51,5 % de creme em **duas** tonalidades, e eleger uma faria a outra parecer errada.
4. **Banner:** remoção de fundo **global**, em **duas faixas de brilho** (≥190 com saturação ≤50; 160–190 com saturação ≤12; abaixo de 160 nunca é fundo), com **alfa proporcional** na fronteira.
5. **O teste de deriva regenera a derivada e compara PIXEL a pixel** com o arquivo commitado — **nunca** por `sha256`.
6. **O caminho do ícone é convenção, não escolha**: o sistema procura `/apple-touch-icon.png` na raiz, e não há como declará-lo no documento e ser obedecido. Por isso a rota é um acréscimo **puro**: o template **não** foi tocado.

## Evidência

- `src/assets/apple-touch-icon.png`: **16.504 bytes**, 180×180, **tipo de cor 2** (`truecolor` sem alfa), verificado pelo cabeçalho IHDR sem decodificar pixel.
- `src/assets/banner-da-tela.png`: 317.058 bytes, `RGBA`.
- `tests/test_deriva_da_arte.py` prova três coisas: que a arte commitada é a que a receita produz; que a comparação **detecta um único pixel alterado** (sem isso ela poderia passar por vacuidade); e que **recompressão do mesmo desenho não é deriva** — o caso que elimina a comparação por `sha256`, medido: o mesmo desenho existe em disco com 32.317 e 44.069 bytes e diferença de pixel **zero**.
- `tests/test_banner_do_topo.py` prende **11 pontos** de arte que têm de continuar opacos, cobrindo as duas famílias de risco (arte escura pouco saturada e arte clara quase neutra), mais uma **caixa de regressão** onde o quadriculado sobreviveu.
- A primeira versão da remoção de fundo **inundava a partir da borda** e foi medida como insuficiente: a árvore, o livro e o texto formam **anúncios fechados**, o pixel `(300,150)` continuava opaco e sobraram **8.379** pixels de fundo em uma amostra de 1/9 da imagem.
- Um limite **único** de brilho comia o preenchimento do texto dourado e deixava as letras **ocas** — o defeito que a segunda faixa corrige.
- `residuo_de_fundo` mede com `SATURACAO_MAXIMA - 5`, **mais apertado que a regra**: medir com o mesmo limite devolve sempre zero, e foi esse erro que deixou um bloco de quadriculado passar **duas vezes**.

## Justificativa

**A alternativa — gerar em tempo de execução — é inviável por empacotamento, e não por preferência.** A fonte canônica mora em `docs/`, que não entra na imagem; dentro do container **não existe fonte para gerar nada**. E gerar no host a cada partida seria I/O no import de `src/app.py`, módulo que a suíte e o harness de paridade importam.

Com a derivada commitada, o risco passa a ser **deriva silenciosa** — a fonte muda e a derivada não. É exatamente esse risco que o teste de pixel cobre.

## Consequências

- 🟢 **A opacidade do ícone é provada por propriedade do formato**, não por amostragem: não há onde guardar transparência em um PNG cujo cabeçalho diz que não há canal alfa. Isso dispensa a biblioteca de imagem no teste — que importa, porque ela não está em `requirements.txt`.
- 🟡 **O `sha256` do HTML de `GET /` é um invariante mantido à mão** em `test_icone_de_atalho.py`: foi atualizado **três vezes em 2026-10-10**, cada uma amarrada a uma `RN` de um adendo vigente. O comentário declara que ele mede "a tela não mudou **desde a última mudança declarada**", e não "a tela nunca muda".
- 🟡 **A caixa de regressão `(778,232)–(918,338)` descreve uma composição que não existe mais** (a que tinha abajur). Continua valendo como caixa, e o comentário registra a origem.
- 🟢 **`docs/assets/img/apple-touch-icon.png` existe e é byte a byte igual à de runtime** (16.504 bytes): é a cópia que o mini-site publicado consome. A **fonte da receita** é `docs/assets/img/logo.png`.
- 🔴 **Não há verificação de que a arte servida é a derivada correta dentro do container.** Os testes rodam no host, onde `docs/` existe. Se a arte falhar na imagem, a degradação é o `404` — exatamente o caso que a escolha de `src/assets/` existe para evitar.
- 🟢 **O título voltou a ser texto** (`T044`, 2026-10-10, depois da `T036` tê-lo trocado por imagem): arte a 50 %, subtítulo, título em texto e o texto de apresentação, **nessa ordem**, com teste próprio de ordem. O `alt` da arte descreve a **ilustração**, e não o título, para o leitor de tela não anunciar a mesma coisa duas vezes.

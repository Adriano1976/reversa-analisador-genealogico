# Onboarding: refino visual do cartão de resultado

> Identificador: `036-refino-do-cartao-de-resultado`
> Data: `2026-10-19`
> Requirements: `_reversa_forward/036-refino-do-cartao-de-resultado/requirements.md`

## 1. O que esta feature faz, em uma frase

Dá ao cartão de cada conexão o arranjo do desenho aprovado: **título, selos e sinais em três faixas**,
"Voltar" e indicador à direita, barra lateral, raio maior e superfície em degradê — **sem mudar um
texto, uma cor de veredito ou uma regra de domínio**.

## 2. O que você precisa ter

- O `.venv` oficial (Python 3.14.6) com as dependências do `requirements.txt`.
- `DATABASE_URL` **ausente** do ambiente.
- Um navegador com DevTools e o modo de dispositivo responsivo.
- Nenhum dado real: o passo 2 cria GEDCOM e CSV sintéticos de poucas linhas.

## 3. Passo a passo

### Passo 0 — congelar a linha de base

```powershell
git status --porcelain
git log -1 --oneline
.\.venv\Scripts\python.exe -m pytest -q
```

Esperado: **1.282 passam, 11 pulados, 0 falham**. Anote o `SHA_DA_TELA` em
`tests/test_icone_de_atalho.py` (`c4a34f7b…`, 30.781 bytes) para comparar no passo 9.

### Passo 1 — subir a aplicação

```powershell
.\.venv\Scripts\python.exe src\app.py
```

Abra `http://127.0.0.1:5000/`.

### Passo 2 — criar os arquivos sintéticos

`sintetico.ged`:

```text
0 HEAD
1 CHAR UTF-8
0 @I1@ INDI
1 NAME Carlos /Silva Souza/
1 SEX M
1 FAMS @F1@
0 @I2@ INDI
1 NAME Ana /Silva Souza/
1 SEX F
1 FAMC @F1@
0 @I3@ INDI
1 NAME Pedro /Silva Souza/
1 SEX M
1 FAMC @F1@
0 @F1@ FAM
1 HUSB @I1@
1 CHIL @I2@
1 CHIL @I3@
0 TRLR
```

`matches.csv`:

```text
Name,cM
Ana Silva Souza,100
Pedro Silva Souza,50
```

### Passo 3 — carregar a árvore e analisar

1. Na tela de entrada, aba **Buscar Conexão no GEDCOM**, envie `sintetico.ged` em **Enviar nova
   árvore** e clique em **Carregar**.
2. Na lista de árvores, clique em **Abrir** no arquivo recém-carregado. A tela de análise aparece com
   as duas abas.
3. Aba **Analisador de DNA**: em **1. Lista de Matches (CSV)**, use **Ou envie um arquivo novo
   abaixo** e selecione `matches.csv`. Em **2. Seu Nome**, digite `Carlos Silva Souza`.
4. Clique em **Analisar Matches de DNA**.

Esperado: a seção "Resultados das Análises de Conexão" com **dois cartões fechados**.

### Passo 4 — conferir as três faixas

Com o cartão fechado, ainda na primeira dobra do resultado:

1. **Faixa 1 — título:** "Análise de conexão com …" ocupa a linha inteira, sozinho. Em DevTools →
   Computed, o `font-size` do `.titulo-da-conexao` é **22,4 px (1,4 rem)**.
2. **Faixa 2 — selos:** `DNA: 100 cM` e o veredito ficam na linha de baixo, alinhados à esquerda.
3. **Faixa 3 — sinais:** Parentesco, Janela de vida e Profundidade aparecem na terceira linha.
4. **À direita:** a pílula "Voltar" (com um chevron à esquerda) e, ao lado, a caixa arredondada com o
   chevron de abrir — os dois centrados verticalmente nas três faixas.

### Passo 5 — conferir a superfície

1. O cartão tem uma **barra lateral** de ~5 px em degradê marrom (`--muted` → `--head`).
2. O raio é de **16 px** e há uma sombra discreta (só no tema claro).
3. O fundo do cartão vai de `--surface` a `--surface-2` (branco → creme no claro).
4. A faixa do cabeçalho não tem mais o tom `--surface-2` chapado: ela se mistura ao degradê.

### Passo 6 — conferir o hover

1. Passe o mouse sobre o cabeçalho do cartão fechado: **nada sublinha** — nem título, nem selos, nem
   sinais.
2. Passe o mouse sobre "Voltar": só a borda muda de cor.
3. Clique no cartão: ele abre e o chevron da caixa gira para a posição de aberto.

### Passo 7 — conferir o tema escuro

1. Clique no botão de tema (canto superior direito).
2. A barra lateral clareia (`--muted` → `--head` viram tan → dourado claro), o degradê do cartão
   escurece e a borda continua visível.
3. O texto do título e dos sinais continua legível — o contraste está no comentário da folha.

### Passo 8 — conferir o telefone

1. No modo responsivo, escolha **320 px**.
2. O "Voltar" desce para a própria linha, alinhado à esquerda; a caixa do chevron continua à direita,
   sem cobrir texto.
3. Não aparece rolagem horizontal.

### Passo 9 — confirmar que a tela vazia não mudou

```powershell
.\.venv\Scripts\python.exe -m pytest tests\test_icone_de_atalho.py -q
```

Esperado: **verde**, com `SHA_DA_TELA` `c4a34f7b…` e 30.781 bytes. A mudança vive sob
`{% if dna_results %}`, fora da tela vazia.

### Passo 10 — rodar as guardas e a suíte inteira

```powershell
.\.venv\Scripts\python.exe -m pytest tests\test_cartoes_recolhiveis.py tests\test_estado_do_resultado.py tests\test_estilo_da_tela.py -q
.\.venv\Scripts\python.exe -m pytest -q
git diff --stat -- src/
```

Esperado: guardas verdes; suíte em **1.282 / 11**; `git diff --stat` listando **apenas**
`src/assets/app.css` e `src/templates/index.html`.

### Passo 11 — registrar

Grave a saída dos passos 0, 9 e 10 em `evidence/`. O `regression-watch.md` e o adendo saem no coding e
no sync.

## 4. Como interpretar o resultado

Esta feature **não** muda o que o operador lê: os nomes, o cM, os vereditos, as mensagens e o texto
escondido do "Voltar" continuam ao caractere. O que muda é o arranjo do cabeçalho (três faixas), a
posição da ação, a superfície do cartão e o indicador de abrir. Os blocos "Matches descartados" e
"Observações do arquivo", que usam a mesma forma recolhível, **continuam como estavam** — decisão
`RN-07`.

## 5. Problemas comuns

| Sintoma | Causa provável | O que fazer |
|---------|----------------|-------------|
| O título continua na mesma linha dos selos | o `span.titulo-da-conexao` não foi para o template, ou o CSS não o encontra | conferir o markup no DevTools e o seletor `.titulo-da-conexao{display:block}` na folha |
| Os selos aparecem com espaços estranhos | a faixa `.selos-do-cabecalho` ficou fora do `span` | conferir se os quatro selos estão dentro do `span` |
| O "Voltar" some no telefone | `flex-wrap` sem `flex-basis:100%` no conteúdo | conferir a media query `max-width:575.98px` |
| O cabeçalho sublinha no hover | o override escopado perdeu a corrida | conferir `.cartao-do-resultado > summary.sumario-do-cartao:hover` |
| O chevron não gira | a regra genérica de `[open]` não está na folha | conferir `details.card[open] > summary.sumario-do-cartao::after` |
| O teste do hash falha | a mudança vazou para fora do `{% if dna_results %}` | conferir se o markup novo está dentro do laço dos cartões |
| `PermissionError` em `tests/.tmp` | permissão de pasta do Windows/sandbox | rodar em workspace com escrita liberada |

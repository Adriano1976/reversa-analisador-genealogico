# Investigation: polimento visual da tela de entrada

> Identificador: `026-polimento-visual-da-tela`
> Data: `2026-10-17`
> Requirements: `_reversa_forward/026-polimento-visual-da-tela/requirements.md`

## 1. A pergunta que o plano precisava responder

O pedido chegou como três pontos de revisão visual: favicon/ícone de atalho, a cor do estado
`INCONCLUSIVO` e a visibilidade do `<h1>` quando a arte do topo está presente. Antes de planejar
qualquer edição, a pergunta era: **quantos desses três pontos são defeito de código, e quantos são
leitura desatualizada do que o projeto já decidiu?**

A resposta mudou o tamanho da feature: **um** dos três pede edição de código (mais uma limpeza de
tokens que o pedido não nomeia), e os outros dois pedem **registro de decisão**, não mudança.

## 2. O que o código mostra (medido nesta sessão)

| Objeto | Medição |
|--------|---------|
| `<link rel="icon">` no template | 1 ocorrência; `type="image/png"`, `sizes="128x128"`, `data URI` de 14.456 bytes decodificados |
| PNG embutido | IHDR **128×128**, profundidade 8, tipo de cor 6 (RGBA) — `sizes` confere |
| `apple-touch-icon` no documento | **0** ocorrências |
| `GET /apple-touch-icon.png` | `200`, `image/png`, 16.504 bytes, 180×180, tipo de cor 2 (sem alfa) |
| `GET /favicon.ico` | `404`, preso por teste (`RN-09`) |
| `--inc` | 1 definição (`#6A6150`), **0** usos |
| `--ok`, `--poss`, `--conf` | 1 definição cada (`#2F6B3A`, `#7A4F00`, `#A8321F`), **0** usos cada |
| `--st-inconclusivo` | 1 definição (`#6A6150`, só no `:root`), 1 uso (`.estado-INCONCLUSIVO`) |
| `--muted` | claro `#6A6150`; escuro `#A99F88` |
| Contraste com texto branco | `COMPATIVEL` 6,39:1 · `POSSIVEL` 7,13:1 · `CONFLITANTE` 6,69:1 · `INCONCLUSIVO` 6,11:1 |
| Branco sobre `--muted` escuro | **2,62:1** — reprova em WCAG AA |
| `SHA_DA_TELA` | `c4a34f7b…`, 30.781 bytes, medido por `tests/test_icone_de_atalho.py` |
| Linha de base da suíte | 1.048 passam, 9 pulados, 0 falham |

As 27 ocorrências de `var(--ok)` no repositório estão em páginas HTML **autocontidas** de
`_reversa_refactor/` e `_reversa_bugs/`, que definem os próprios tokens no `:root` e não carregam
`/app.css` (conferido em duas delas). No sistema em execução — `src/`, `tests/`, `docs/` — a
referência é zero.

## 3. O que a extração já decidiu

- **Ícone de atalho sem declaração.** `_reversa_sdd/recursos-da-tela/requirements.md` (`RF-07`,
  `RF-08`, `RF-09`) e o adendo `009` (`W027`) fixam a descoberta por **caminho convencional**. O
  próprio adendo diz que acrescentar o `<link>` "toca a tela, contraria a `RN-02` e arranha o `W005`".
- **`<h1>` sempre visível.** O adendo `023` reverteu a emenda do adendo `013`: com a arte nova, sem o
  título desenhado, esconder o `h1` deixaria a tela **sem nenhuma identificação em português**.
- **`INCONCLUSIVO` é o estado inicial e o caminho de falha.** `state-machines.md#33`: "nenhum estado
  afirmado por omissão". O cinza não é uma cor genérica: é a ausência de veredito.
- **Os quatro estados são nomes de classe CSS** (`badge estado-{{ status }}`): renomear um estado
  quebra a cor do selo em silêncio (`state-machines.md#32`).

## 4. Por que a premissa do banner está vencida

A arte do topo foi trocada em **2026-10-16** (commit `15371b8`, "arte do topo sem o titulo e o h1
sempre visivel"). A arte anterior trazia "Analisador Genealógico" desenhado, e o `h1` era escondido
enquanto a imagem respondia — por um processador de contexto (`arte_do_topo_disponivel`) que
perguntava ao servidor se o arquivo existia, e não ao CSS se a imagem carregou.

Com a arte nova (1024×547, sem texto), a condição perdeu o objeto: o processador saiu de `src/app.py`
(hoje resta o comentário que registra o motivo, `app.py:438-452`) e o `h1` voltou a ser sempre visível
(`test_o_titulo_do_produto_esta_sempre_visivel`, `tests/test_banner_do_topo.py:219-240`).

O pedido, porém, ainda descreve "o banner, que já mostra o nome". É essa defasagem que explica o ponto
3 — e é o comentário de `src/assets/app.css:353` que a mantém viva.

## 5. Alternativas avaliadas

### 5.1 Declarar o ícone de atalho no documento

| Alternativa | Custo | Veredito |
|-------------|-------|----------|
| Manter sem declaração | nenhum; caminho convencional é o contrato vigente | **escolhida** (1a) |
| Declarar `<link rel="apple-touch-icon" sizes="180x180" href="/apple-touch-icon.png">` | revoga `RN-02`/`W027`; reescreve `test_a_tela_nao_declara_o_icone_de_atalho`; move o `SHA_DA_TELA`; exige adendo próprio; mexe nas 8 telas literais | recusada |
| Criar `favicon.ico` | superfície sem consumidor, proibida por `RN-09`; repetiria a dívida #17 | recusada |

### 5.2 Cor própria para o `INCONCLUSIVO`

| Cor | Contraste com branco | Leitura |
|-----|----------------------|---------|
| `#6A6150` (atual) | 6,11:1 | **escolhida** (2a): cinza de "sem veredito", dentro da paleta da arte |
| `#5B6B7A` | 5,48:1 | recusada: passa em contraste, mas introduz um matiz frio fora da paleta tirada da arte |
| `var(--muted)` | **2,62:1** no escuro | proibida: apaga o texto do selo |

O ponto decisivo não é a cor em si: é que `--muted` **muda** entre os temas e o selo **não pode**
mudar, porque o texto branco é fixo por `.badge[class*="estado-"]`. A coincidência de literal vale só
no tema claro; no escuro, os dois já divergem.

### 5.3 Esconder o `<h1>` quando a arte responde

| Mecanismo | O que sabe | Problema |
|-----------|------------|----------|
| CSS | só o que está no documento | não sabe se a imagem carregou; esconderia também no caso de falha |
| Servidor (`os.path.isfile`) | se o arquivo existe no disco | não sabe se o navegador carregou (rede, cache, 404); foi o mecanismo removido em 2026-10-16 |
| `onerror` no cliente | se a imagem falhou | só descobre depois da primeira pintura, e a correção pisca; acrescenta script novo a uma tela que hoje funciona sem ele |

Além disso, a arte atual não tem o título: qualquer um dos três mecanismos deixaria a tela sem
identificação do produto. **Manter o `h1` visível** é a única opção que cumpre o fallback por
construção (3a).

## 6. Padrões aplicáveis

- **Fonte única de verdade para token de cor.** Quatro cores de estado com **dois** nomes cada é o
  defeito de manutenção que a feature remove; o padrão é um nome por papel.
- **Comentário como guarda de decisão.** O arquivo já usa o comentário do laranja (2,57:1) para
  impedir que a regra seja desfeita por parecer gosto. A feature estende o mesmo padrão aos quatro
  estados.
- **Contraste medido, não opinado.** WCAG 2.1 AA para texto normal é 4,5:1; o teste resolve `var()`
  pela cascata em vez de ler a regra isolada, porque o defeito de 2026-10-14 nasceu de uma regra
  vencer a outra.
- **Declaração no canal certo.** O projeto declara mudança de tela em `_reversa_sdd/addenda/`, não em
  comentário de teste nem em arquivo solto da feature.

## 7. Fontes

- `src/assets/app.css` (linhas 33-35, 161-166, 351-353)
- `src/templates/index.html` (linhas 94-95, 195-202)
- `src/app.py` (rotas das artes e da folha; comentário do processador removido)
- `tests/test_estilo_da_tela.py` (`TestOContrasteDosSelos`, contrato de classes)
- `tests/test_icone_de_atalho.py` (`SHA_DA_TELA`, ausência de declaração, caminhos não servidos)
- `tests/test_banner_do_topo.py` (`h1` sempre visível, ordem da masthead, `alt`)
- `_reversa_sdd/recursos-da-tela/requirements.md` (`RF-07`, `RF-08`, `RF-09`, `#a-masthead`)
- `_reversa_sdd/addenda/009-rota-do-apple-touch-icon.md` (`W027`)
- `_reversa_sdd/addenda/013-revisao-de-design-da-tela.md` (a emenda do `h1`, depois revertida)
- `_reversa_sdd/addenda/023-arte-do-topo-sem-o-titulo.md` (a reversão e a arte sem título)
- `_reversa_sdd/state-machines.md#32-tabela-de-transições` e `#33-fatos-de-contrato`
- `_reversa_forward/006-fronteira-aplicacao-ports/requirements.md` (`RF-17`) e `regression-watch.md` (`W005`)
- WCAG 2.1, critério 1.4.3 (contraste mínimo) e 1.4.11 (contraste de elementos não textuais)

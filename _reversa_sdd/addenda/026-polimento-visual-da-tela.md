# Adendo: polimento visual da tela de entrada

> Identificador: `026-polimento-visual-da-tela`
> Data: `2026-10-17`
> Cenário: **legado** (âncora em `_reversa_sdd/architecture.md`, `state-machines.md` e `recursos-da-tela/`)

## Vigência

Vigente desde 2026-10-17.

## Resumo da entrega

A feature fechou três pontos de revisão visual da tela de entrada — favicon e ícone de atalho, cor do
estado `INCONCLUSIVO` e visibilidade do `<h1>` — e, ao investigá-los, mostrou que **dois já estavam
decididos no legado**: o ícone de atalho não é declarado no documento de propósito (`RN-02`/`W027`) e
o `<h1>` é sempre visível desde a troca da arte em 2026-10-16 (`RN-23`, adendo `023`).

A entrega de código é **um único arquivo**, `src/assets/app.css`: os quatro tokens sem uso
(`--ok`, `--poss`, `--conf`, `--inc`) saíram, a família `--st-*` passou a ser a única declaração das
cores de estado, o token do `INCONCLUSIVO` ganhou o comentário que proíbe o alias com `--muted`
(branco sobre `#6A6150` = 6,11:1; sobre o `--muted` escuro `#A99F88` = 2,62:1) e os dois comentários do
bloco do banner passaram a descrever a arte atual. O comentário dos estados registra os quatro
contrastes medidos (6,39 / 7,13 / 6,69 / 6,11:1).

**Nenhuma cor efetiva, classe, rota ou texto mudou.** O template não foi tocado: `GET /` continua
byte a byte, com `sha256` `c4a34f7b…` e 30.781 bytes. Suíte: **1.048 passam, 9 pulados, 0 falham**,
antes e depois. `git diff --stat -- src/ tests/` lista apenas `src/assets/app.css`.

**Quinze ações no total:** as 14 de código e esta, a `T015`.

## Impacto por artefato da extração

| Artefato | Seção | Tipo de impacto | Delta |
|----------|-------|-----------------|-------|
| `_reversa_sdd/architecture.md` | `#3` (Componentes e estrutura de pacotes) | `regra-alterada` | A folha de estilo da tela (`src/assets/app.css`, servida por `GET /app.css`) passa a ter **uma única declaração por cor de estado**; quatro tokens sem uso deixaram de existir. Nenhum componente, container, rota ou dependência nova |
| `_reversa_sdd/state-machines.md` | `#3.2` (Tabela de transições) e `#3.3` (Fatos de contrato) | `presença` | Os quatro estados, a ordem de conservadorismo e o `status` como nome de classe CSS continuam como estão. O cinza do `INCONCLUSIVO` (`#6A6150`, 6,11:1) agora tem declaração própria, com o comentário que proíbe segui-lo de `--muted` |
| `_reversa_sdd/recursos-da-tela/requirements.md` | `#requisitos-funcionais` (`RF-07`, `RF-08`, `RF-09`) e `#a-masthead` | `presença` | O ícone de atalho continua descoberto por caminho convencional, o favicon continua `data URI` e o `<h1>` continua sempre visível. Nenhuma declaração entrou no `<head>` |
| `_reversa_sdd/addenda/023-arte-do-topo-sem-o-titulo.md` | "Regras sob vigilância" (o `<h1>` visível) | `presença` | A regra continua verdadeira. Os dois comentários da folha que ainda descreviam a arte anterior a 2026-10-16 foram corrigidos em `src/assets/app.css` |
| `_reversa_sdd/screens/golden/manifest.yaml` | as 8 entradas literais | `presença` | `GET /` continua byte a byte (`sha256` `c4a34f7b…`, 30.781 bytes); as 8 telas literais mantêm diff textual zero |
| `_reversa_sdd/design-system/tokens-derived.md` | "Cores" | `presença` | ⚠️ O arquivo derivado de 2026-09-28 é anterior à folha servida por rota e **não** descreve a paleta atual. Não foi regenerado por esta feature; é dívida documental declarada, não delta desta entrega |

**Contagem por tipo:** `regra-alterada` 1 · `presença` 5 — **6 impactos**.

Nenhuma regra de `_reversa_sdd/domain.md` foi criada, alterada ou removida. Não há
`delta-de-dados` (nenhum campo, tabela, payload ou migração) nem `delta-de-contrato-externo` (o
contrato de `GET /app.css` — método, `Content-Type`, `ETag`, `304`, `404` — permanece o mesmo).

## Regras sob vigilância

`W001` a `W007`, definidos em
`_reversa_forward/026-polimento-visual-da-tela/regression-watch.md`, mais as observações `OBS-01` a
`OBS-03` do mesmo arquivo.

| Item | Cobre |
|------|-------|
| `W001` | Os quatro tokens mortos continuam ausentes |
| `W002` | `--st-inconclusivo` = `#6A6150`, nunca alias de `--muted` |
| `W003` | Os quatro contrastes medidos e o caso do laranja no comentário |
| `W004` | Os comentários do banner descrevem a arte atual |
| `W005` | `SHA_DA_TELA` inalterado e o template sem `apple-touch-icon` |
| `W006` | O `<h1>` sem `visually-hidden` |
| `W007` | Os quatro selos com ≥ 4,5:1 nos dois temas |

## Fontes

- `_reversa_forward/026-polimento-visual-da-tela/requirements.md`
- `_reversa_forward/026-polimento-visual-da-tela/roadmap.md`
- `_reversa_forward/026-polimento-visual-da-tela/legacy-impact.md`
- `_reversa_forward/026-polimento-visual-da-tela/regression-watch.md`
- `_reversa_forward/026-polimento-visual-da-tela/progress.jsonl` (14 linhas de ação)
- `_reversa_forward/026-polimento-visual-da-tela/evidence/RELATORIO.md`
- `_reversa_sdd/addenda/009-rota-do-apple-touch-icon.md` (`W027`)
- `_reversa_sdd/addenda/013-revisao-de-design-da-tela.md` (a folha servida por rota)
- `_reversa_sdd/addenda/023-arte-do-topo-sem-o-titulo.md` (o `<h1>` sempre visível)
- `_reversa_sdd/state-machines.md#32-tabela-de-transições` e `#33-fatos-de-contrato`

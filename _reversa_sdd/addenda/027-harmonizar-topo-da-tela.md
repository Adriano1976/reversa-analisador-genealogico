# Adendo: harmonização visual do topo da tela

> Identificador: `027-harmonizar-topo-da-tela`
> Data: `2026-10-17`
> Cenário: **legado** (âncora em `_reversa_sdd/architecture.md`, `recursos-da-tela/` e nos adendos `011`, `023` e `026`)

## Vigência

Vigente desde 2026-10-17.

## Resumo da entrega

A feature fechou a distância visual entre o topo e os cartões de resultado em **quatro frentes**, e
corrigiu uma premissa no caminho: o texto de introdução **não** estava desalinhado por descuido — ele é
centralizado e estreito por decisão (`RN-24`, presa por teste). O defeito era o **comentário** do
template, que ainda descrevia o comportamento anterior.

O que mudou, de fato:

1. **Alertas de retorno na paleta.** Quatro tokens novos (`--sucesso-bg`, `--sucesso-line`,
   `--perigo-bg`, `--perigo-line`, nos dois temas) e regras específicas de `.alert-success` e
   `.alert-danger`. O texto fica entre **12,16 e 13,70:1** e a borda entre **5,57 e 7,47:1**; antes, a
   borda era **1,15:1** e o bloco lia como chapa lisa. O botão de fechar foi preservado.
2. **Ação principal sem peso de barra.** `.d-grid > .btn` ganha largura natural acima de 576 px e
   continua de largura total no telefone. Uma regra cobre os três formulários.
3. **Escala do topo.** `h1` de `clamp(1.9rem,4vw,2.5rem)` para `clamp(1.8rem,3.2vw,2.2rem)`; arte de
   320 px para 280 px.
4. **Comentário da masthead.** Passou a descrever a `RN-24`.

O rodapé que o operador elogiou **não foi tocado**: nenhum cartão, selo de cM (`bg-secondary`) ou
espaçamento do resultado mudou; o `alert-warning` dentro do cartão de DNA continua com a cor do
framework.

**A tela servida não mudou.** O comentário corrigido é um comentário **Jinja** (`{# … #}`), removido na
renderização. O `SHA_DA_TELA` continua `c4a34f7b…`, com 30.781 bytes, e o teste do hash passou **sem
edição**. É a primeira entrega do ciclo forward que altera o template e não move o documento — o
`legacy-impact.md` e o `evidence/depois/hash.txt` registram a medição.

Suíte: **1.048 passam, 9 pulados, 0 falham**, antes e depois. Guardas da tela: **90 passam**. O teste
da `RN-24` está verde.

**Dezoito ações:** as 17 de código e esta, a `T018`.

## Impacto por artefato da extração

| Artefato | Seção | Tipo de impacto | Delta |
|----------|-------|-----------------|-------|
| `_reversa_sdd/architecture.md` | `#3` (Componentes e estrutura de pacotes) | `regra-alterada` | A folha de estilo ganha quatro tokens de alerta e duas regras de escala. Nenhum componente, container, rota ou dependência nova |
| `_reversa_sdd/recursos-da-tela/requirements.md` | `#a-masthead` | `presença` | A masthead mantém a ordem e o `<h1>` visível. A `RN-24` (texto centralizado e estreito) continua valendo; o comentário do template passou a descrevê-la |
| `_reversa_sdd/addenda/011-escolher-arquivo-da-lista.md` | `#3-regras-novas-que-a-feature-cria` (`RN-24`) | `presença` | O arranjo centralizado e a coluna `col-lg-*` não mudaram; o HTML servido continua sem `text-start`, e o teste da `RN-24` segue verde |
| `_reversa_sdd/addenda/023-arte-do-topo-sem-o-titulo.md` | "Regras sob vigilância" (o `<h1>` visível) | `presença` | O `<h1>` continua sempre visível; a mudança é só de escala (2,2 rem), não de visibilidade |
| `_reversa_sdd/addenda/026-polimento-visual-da-tela.md` | "Regras sob vigilância" (`--st-*`) | `presença` | Os tokens de estado não foram tocados. Os quatro tokens de alerta são uma família nova e não se confundem com `--st-*` |
| `_reversa_sdd/screens/golden/manifest.yaml` | as 8 entradas literais | `presença` | `GET /` continua byte a byte: `sha256 c4a34f7b…`, 30.781 bytes. Nenhum golden muda |
| `_reversa_sdd/design-system/tokens-derived.md` | "Cores" | `presença` | ⚠️ O arquivo derivado de 2026-09-28 continua sem descrever a paleta atual e não ganhou os tokens de alerta; é dívida documental declarada, não delta desta entrega |

**Contagem por tipo:** `regra-alterada` 1 · `presença` 6 — **7 impactos**.

Nenhuma regra de `_reversa_sdd/domain.md` foi criada, alterada ou removida. Não há `delta-de-dados`
(nenhum campo, tabela, payload ou migração) nem `delta-de-contrato-externo` (as rotas e o
`/app.css` mantêm método, `Content-Type`, `ETag`, `304` e `404`).

## Regras sob vigilância

`W001` a `W007`, definidos em
`_reversa_forward/027-harmonizar-topo-da-tela/regression-watch.md`, mais as observações `OBS-01` a
`OBS-03` do mesmo arquivo.

| Item | Cobre |
|------|-------|
| `W001` | Os quatro tokens de alerta existem nos dois temas |
| `W002` | O comentário dos alertas traz os oito contrastes medidos |
| `W003` | A ação principal é natural acima de 576 px e total abaixo |
| `W004` | `h1` ≤ 2,2 rem e arte ≤ 280 px |
| `W005` | A `RN-24` preservada: sem `text-start` no HTML, teste verde |
| `W006` | `SHA_DA_TELA` inalterado (`c4a34f7b…`) |
| `W007` | Nenhuma regra alcança o rodapé, inclusive o `alert-warning` do DNA |

## Fontes

- `_reversa_forward/027-harmonizar-topo-da-tela/requirements.md`
- `_reversa_forward/027-harmonizar-topo-da-tela/roadmap.md`
- `_reversa_forward/027-harmonizar-topo-da-tela/legacy-impact.md`
- `_reversa_forward/027-harmonizar-topo-da-tela/regression-watch.md`
- `_reversa_forward/027-harmonizar-topo-da-tela/progress.jsonl` (17 linhas de ação)
- `_reversa_forward/027-harmonizar-topo-da-tela/evidence/RELATORIO.md`
- `_reversa_forward/027-harmonizar-topo-da-tela/evidence/depois/hash.txt`
- `_reversa_sdd/addenda/011-escolher-arquivo-da-lista.md` (`RN-24`)
- `_reversa_sdd/addenda/013-revisao-de-design-da-tela.md` (a folha servida por rota)
- `_reversa_sdd/addenda/018-cartao-de-resultado-recolhivel.md`
- `_reversa_sdd/addenda/023-arte-do-topo-sem-o-titulo.md`
- `_reversa_sdd/addenda/026-polimento-visual-da-tela.md`
- `tests/test_banner_do_topo.py:270-298` (o teste da `RN-24`)

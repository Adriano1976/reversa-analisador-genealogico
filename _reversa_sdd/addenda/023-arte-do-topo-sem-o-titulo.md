# Adendo: arte do topo sem o título

> Identificador: `023-arte-do-topo-sem-o-titulo`
> Data: `2026-10-16`
> Cenário: **legado** (âncora em `_reversa_sdd/recursos-da-tela/` e `_reversa_sdd/design-system/`)

## Vigência

Vigente desde 2026-10-16.

**Reverte uma parte do adendo `013-revisao-de-design-da-tela.md`** — a emenda à `RN-23` que escondia o
`<h1>`. Ver "O que este adendo reverte do adendo 013".

## Resumo da entrega

O operador trocou a arte do topo por uma versão **sem o texto "Analisador Genealógico"** desenhado, e
relatou que o fundo não estava transparente.

O que estava errado não era a imagem: ele substituiu a arte **derivada** por uma **fonte crua**. O
arquivo `src/assets/banner-da-tela.png` é a saída da receita, e o que a rota serve; a fonte canônica
mora em `docs/assets/img/banner-analisador.png`. O arquivo entrou com **canal alfa inteiramente opaco**
(medido: 0 pixels transparentes em 560.128) e o **quadriculado de transparência pintado no bitmap**
(claro em 253-254 alternando com cinza em 191-192, em blocos de 8 px) — a mesma classe de defeito que a
feature 011 já tinha enfrentado em 2026-10-10.

A entrega tem quatro frentes:

1. **A arte nova entra como fonte canônica** — `docs/assets/img/banner-analisador.png` passa de
   926.083 para **1.101.780 bytes**, e de 1024x543 para **1024x547**.
2. **A derivada é regerada pela receita existente**, sem reajuste de limites:
   `python -m tests.banner_da_tela` produz **318.911 bytes, 72,4 % transparente, zero resíduo de
   fundo**. Os limites medidos em 2026-10-10 (`CLARO_MINIMO = 160` e as duas faixas de saturação)
   valem para esta composição.
3. **O `<h1>` volta a ser sempre visível.** Ele era escondido enquanto a arte respondesse, porque
   aquela arte trazia o título desenhado. A arte nova não traz — esconder o `h1` deixaria a tela sem
   **nenhuma** identificação do produto em português. O processador de contexto
   `arte_do_topo_disponivel` saiu de `src/app.py` junto com a condição.
4. **O ponto de amostra que prendia o texto dourado no teste da arte foi substituído**, e a família
   que ele protegia ganhou uma guarda por contagem.

**Suíte: `1020 passed, 9 skipped`.**

> ⚠️ **A paridade diferencial NÃO está em 100 % nesta data** — 20 divergências, todas no probe
> `ancestral[...]`, e **nenhuma delas é desta entrega**: elas vêm da correção da busca de ancestral
> comum que outra sessão tem em curso (`src/core/documentary_relationship.py`, `path_finding.py`,
> `identidade_do_match.py`). Registrado aqui para que ninguém atribua a divergência a esta troca de
> arte.

## O que este adendo reverte do adendo 013

O `013` registrou uma **emenda à `RN-23`**: "o título é texto no documento, e **visível apenas quando
a arte do topo não responde**". A emenda existia por um motivo real — a arte daquela data trazia
"Analisador Genealógico" desenhado, e manter os dois visíveis nomeava o produto duas vezes, uma logo
abaixo da outra.

**A emenda foi retirada.** Com uma arte sem o texto, a condição perdeu o objeto, e a `RN-23` volta a
valer **como está escrita**: "o título volta a ser texto visível".

O que **não** foi revertido do `013`: a folha de estilo servida por `GET /app.css`, o controle de
tema, o índice, o selo e a grade do kit continuam como aprovados — e a outra emenda do `013` (o teto
de 320 px da arte) segue vigente.

O comentário do `SHA_DA_TELA` em `tests/test_icone_de_atalho.py` foi atualizado na mesma direção: ele
apontava para a emenda do `013` e agora aponta para este adendo.

## Impacto por artefato da extração

| Artefato | Seção | Tipo de impacto | Delta |
|----------|-------|-----------------|-------|
| `_reversa_sdd/addenda/013-revisao-de-design-da-tela.md` | "Regras alteradas", linha da `RN-23` (título) | regra-removida | A emenda que escondia o `<h1>` deixa de valer; a `RN-23` volta ao texto original |
| `_reversa_sdd/recursos-da-tela/contracts.md` | arte do topo | delta-de-dados | A arte servida passa a ser 1024x547 (era 1024x543), com **72,4 %** de transparência e zero resíduo |
| `docs/assets/img/banner-analisador.png` (fora da extração, citado por completude) | — | delta-de-dados | A fonte canônica é substituída: 926.083 → **1.101.780 bytes** |
| `src/assets/banner-da-tela.png` | — | delta-de-dados | A derivada é regerada: 317.058 → **318.911 bytes**, pela receita, e não à mão |
| `tests/test_banner_do_topo.py` | `TestArteDerivada` | regra-alterada | O ponto `(270, 212)` — preenchimento do texto dourado — saiu, e entrou `test_a_faixa_estreita_de_saturacao_continua_protegendo_tinta` |
| `README.md` (fora da extração) | "A tela de entrada" | delta-de-contrato-externo | O texto descreve o topo com o título; a arte embutida no README é um `<img>` do banner, que continua válido |

## A guarda que substituiu o ponto do texto

O teste `test_a_arte_nao_perdeu_as_partes_claras_que_sao_arte` prendia, pelo pixel `(270, 212)`, a
família **"arte clara e quase neutra"** — a que um teto de saturação largo demais come, e foi o
defeito medido que deixou as letras de "Analisador Genealógico" **ocas**.

Com a arte sem texto, esse pixel virou fundo e o teste caiu — corretamente. Os candidatos que
sobraram na mesma família eram **pixels de borda** (antialiasing), e prender um deles tornaria o
teste frágil a qualquer ajuste na segunda passada da receita.

A substituição foi medida, e não escolhida:

- **455 pixels** opacos na faixa estreita (160 a 190, saturação 13 a 50), dos quais **401 são
  interiores** e **54 são borda**;
- com o teto largo (50), sobrariam **zero**;
- o teste novo exige **piso de 150**, com folga de 3x para baixo de propósito: o que ele prende é a
  **ordem de grandeza**, não o valor exato.

Dois pontos de **tinta** da mesma família entraram no teste por pixel, escolhidos a **≥ 4 px de
qualquer pixel de fundo** — `(511, 255)` e `(489, 377)` — para prenderem pintura, e não a fronteira.

## Regras sob vigilância

| Item | Onde | Sinal de quebra |
|------|------|-----------------|
| A arte servida vem da RECEITA | `tests/banner_da_tela.py` | Alguém editar `src/assets/banner-da-tela.png` à mão, ou trocar a fonte sem regerar a derivada — foi exatamente o que aconteceu aqui |
| A derivada não tem bloco de quadriculado | `TestArteDerivada` | `residuo_de_fundo` deixar de ser zero na caixa medida |
| A faixa estreita continua protegendo tinta | idem | A contagem cair abaixo de 150: o teto de `SATURACAO_MINIMA_ESCURA` foi alargado ou o brilho mínimo baixou |
| O `<h1>` está sempre visível | `test_o_titulo_do_produto_esta_sempre_visivel` | A classe do `h1` ganhar `visually-hidden` sem uma arte que traga o texto |
| `SHA_DA_TELA` | `tests/test_icone_de_atalho.py` | `c4a34f7b…` (30.781 bytes) |

## Fontes

- `docs/assets/img/banner-analisador.png` — a fonte canônica nova (1024x547)
- `src/assets/banner-da-tela.png` — a derivada regerada pela receita
- `tests/banner_da_tela.py` — a receita, com os limites medidos em 2026-10-10 e revalidados aqui
- `tests/test_banner_do_topo.py` — a rota, a arte derivada e as guardas de tinta
- `tests/test_icone_de_atalho.py` — o `SHA_DA_TELA` e a declaração desta mudança
- `src/app.py`, `src/templates/index.html` — a saída do processador de contexto e o `<h1>` visível
- `_reversa_sdd/addenda/013-revisao-de-design-da-tela.md` — o adendo cuja emenda à `RN-23` é revertida

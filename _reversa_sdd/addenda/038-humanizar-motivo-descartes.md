# Adendo: o motivo do descarte passou a dizer a causa, em português

> Identificador: `038-humanizar-motivo-descartes`
> Data: `2026-10-20`
> Cenário: **legado** (âncora em `_reversa_sdd/architecture.md` + `domain.md`)

## Vigência

Vigente desde 2026-10-20.

## Resumo da entrega

A coluna **Motivo** dos "Matches descartados" mostrava uma fórmula:
`score insuficiente ou conflito de sobrenome (given=100, final=88.25, inter=1/1, jacc=0.50)`.
Ela oferecia duas causas e não dizia qual, omitia o portão que de fato recusou (a penalidade de
token do meio) e falava em nome de variável de máquina — o adendo `024` já tinha medido que a
metade "conflito de sobrenome" **nunca** era a causa literal em 325 descartes.

A entrega troca a fórmula por **uma frase por causa**, escolhida por precedência fixa, na tela e na
lista de trabalho em CSV. Os quatro números não se perderam: viraram a nona coluna da planilha,
`Detalhe técnico`. **Nenhuma decisão de aceitação mudou** — mesmos cartões, mesmos descartes,
mesmos cM, mesmos caminhos.

12 ações concluídas (`T001`–`T012`), 43 testes novos, suíte em **1381 passou, 9 pulados**, e
`SHA_DA_TELA` intacto (`7375696d…`, 16.504 bytes).

## Impacto por artefato da extração

| Artefato | Seção | Tipo de impacto | Delta |
|---|---|---|---|
| `_reversa_sdd/architecture.md` | §3 Componentes e estrutura de pacotes | componente-novo | Nasceu `core.motivos_do_descarte`: catálogo `código → frase`, `Motivo(codigo, texto, detalhe)`, `diagnosticar()` e `detalhe_tecnico()` |
| `_reversa_sdd/architecture.md` | §3 Componentes e estrutura de pacotes | contrato-alterado | `core.matching.avaliar_candidatos` devolve `Motivo` no segundo elemento; `match_candidates` mantém o contrato de dois valores **com texto** |
| `_reversa_sdd/architecture.md` | §3 Componentes e estrutura de pacotes | contrato-alterado | `core.dna_analysis` passou a montar o descarte com `motivo` (texto humano), `motivo_codigo` e `motivo_detalhe` |
| `_reversa_sdd/architecture.md` | §3 Componentes e estrutura de pacotes | contrato-alterado | `ports.DescartadoDaAnalise` ganhou `reason_code` e `detail` (default vazio); o adaptador de persistência continua gravando apenas `reason` |
| `_reversa_sdd/domain.md` | §3.4 Matching difuso de nomes: o cM **não** decide aceitação | regra-nova | **RN-25/RN-26/RN-27**: o motivo é texto de apresentação em português comum; nomeia **uma** causa por precedência fixa (nome do meio → sobrenomes de menos → grafia → prenome → semelhança geral) e carrega um código estável ao lado do texto |
| `_reversa_sdd/domain.md` | §3.4 Matching difuso de nomes: o cM **não** decide aceitação | regra-alterada | O filtro anti-falso-positivo perdeu o parêntese técnico no texto (`RN-25`); a decisão do filtro não mudou |
| `_reversa_sdd/domain.md` | §5.2 Núcleo e aplicação (`src/core/`, `src/application/`) | regra-alterada | O motivo de recusa por semelhança deixou de ser fórmula montada no bloco de scoring: quem o escolhe é `diagnosticar()`, sobre os valores que a decisão já calculou |
| `_reversa_sdd/analise-dna/contracts.md` | §6 Contrato do payload e dos avisos | delta-de-contrato-externo | O catálogo de motivos perde a entrada `"score insuficiente ou conflito de sobrenome (…)"` e ganha cinco frases nomeadas; o motivo `"sem sobrenome em comum (filtro anti-falso-positivo)"` passa a `"nenhum sobrenome em comum entre o nome e o da árvore"` |
| `_reversa_sdd/analise-dna/contracts.md` | §5 Contrato do veredito (o confronto) | delta-de-contrato-externo | Cada descarte carrega `motivo_codigo` e `motivo_detalhe` além de `motivo` |
| `_reversa_sdd/data-dictionary.md` | §Exportações | delta-de-dados | A lista de trabalho dos descartes passou de oito para **nove** colunas: a nona é `Detalhe técnico` |
| `_reversa_sdd/code-analysis.md` | §4.3 Algoritmos e lógica não trivial | regra-alterada | O bloco de scoring não monta mais texto: o sétimo portão (veto do token do meio) ganhou nome próprio, e o cálculo do token do meio subiu para antes do veredito, com a mesma expressão |
| `_reversa_sdd/addenda/024-motivo-de-recusa-por-sobrenome.md` | Resíduo declarado, item 3 | regra-alterada | O resíduo 3 está **fechado**: a mensagem de score deixou de ser ambígua e passou a citar o portão que recusou |
| `_reversa_sdd/addenda/035-lista-de-trabalho-dos-descartes.md` | Impacto por artefato da extração | delta-de-contrato-externo | A planilha ganhou a nona coluna; as oito primeiras mantêm nome e posição |

## Regras sob vigilância

`W001` a `W011` — ver `_reversa_forward/038-humanizar-motivo-descartes/regression-watch.md`.

## Fontes

- `_reversa_forward/038-humanizar-motivo-descartes/requirements.md`
- `_reversa_forward/038-humanizar-motivo-descartes/roadmap.md`
- `_reversa_forward/038-humanizar-motivo-descartes/actions.md`
- `_reversa_forward/038-humanizar-motivo-descartes/legacy-impact.md`
- `_reversa_forward/038-humanizar-motivo-descartes/regression-watch.md`
- `_reversa_forward/038-humanizar-motivo-descartes/progress.jsonl`

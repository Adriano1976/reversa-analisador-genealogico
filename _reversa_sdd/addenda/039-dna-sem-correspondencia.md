# Adendo: DNA sem correspondência na árvore

> Identificador: `039-dna-sem-correspondencia`
> Data: `2026-10-22`
> Cenário: **legado** (âncora em `_reversa_sdd/architecture.md` + `domain.md`)

## Vigência

Vigente desde 2026-10-22.

## Resumo da entrega

A análise de DNA já separa cartões aceitos e descartes; o que faltava era dar visibilidade aos
descartes de cM alto que não têm nenhuma pessoa com nome compatível na árvore. O bloco novo
**"DNA sem correspondência na árvore"** lê a lista de descartes já produzida, seleciona os itens
com `cm >= 40,0` sem candidato compatível e cujo nome não tem cartão em nenhum kit, e os mostra
ordenados por cM, com nome, kit, cM e MRCA estimado.

O bloco é uma **leitura derivada**: não cria cartão, não afirma parentesco, não mostra diagrama
nem promoção e não altera a lista completa de descartes, o CSV de nove colunas, o matching, o
veredito, o cM ou o caminho. Na análise real de 2026-10-22, são **9** itens em **448** descartes,
com Clezia Santos (154,5 cM) em primeiro e Airton Passos Vasconcelos (51,3 cM) presente.

**13 ações concluídas** (`T001`–`T013`). Suíte em **1411 passou, 9 pulados**; `SHA_DA_TELA`
inalterado (`7375696d…`, 16.504 bytes).

## Impacto por artefato da extração

| Artefato | Seção | Tipo de impacto | Delta |
|---|---|---|---|
| `_reversa_sdd/architecture.md#3-componentes-e-estrutura-de-pacotes` | §3 Componentes e estrutura de pacotes | componente-novo | Entra `core.sem_correspondencia` — seletor puro com `CM_MINIMO_SEM_CORRESPONDENCIA = 40.0`, filtro por cM/candidato/cartão e ordem determinística |
| `_reversa_sdd/architecture.md#3-componentes-e-estrutura-de-pacotes` | §3 Componentes e estrutura de pacotes | delta-de-dados | `core.dna_analysis` passa a levar `mrca_generations` no dicionário de descarte; `application.dna_analysis` expõe `sem_correspondencia`; `app.py` repassa ao template |
| `_reversa_sdd/architecture.md#3-componentes-e-estrutura-de-pacotes` | §3 Componentes e estrutura de pacotes | delta-de-contrato-externo | A resposta HTML de `POST /` com `action=dna_analysis` ganha um bloco aberto e uma frase no resumo; request, status, erros e timeouts não mudam |
| `_reversa_sdd/domain.md#34-matching-difuso-de-nomes-o-cm-não-decide-aceitação` | §3.4 Matching difuso | regra-nova | O cM continua sem decidir aceitação; a leitura derivada só separa descartes de cM alto, sem criar cartão nem tocar no matching |
| `_reversa_sdd/domain.md#39-ordem-de-apresentação-dos-resultados` | §3.9 Ordem de apresentação | regra-nova | A ordem dos cartões (documental primeiro, cM dentro do grupo) não muda; o bloco novo tem ordem própria por cM decrescente |
| `_reversa_sdd/analise-dna/contracts.md#62-descartes` | §6.2 Descartes | delta-de-dados | O item de descarte ganha `mrca_generations` (aditivo, `None` quando o CSV não traz a coluna); `csv_name`, `kit`, `cm`, `motivo`, `motivo_codigo`, `motivo_detalhe` e `candidatos` continuam iguais |
| `_reversa_sdd/data-dictionary.md#8-payload-do-núcleo--tela` | §8 Payload do núcleo → tela | delta-de-dados | `ResultadoDeAnalise` ganha `sem_correspondencia: tuple = ()`; `DescartadoDaAnalise`, `AnaliseParaRegistrar`, `skipped_match` e o schema PostgreSQL não mudam |
| `_reversa_sdd/addenda/022-bloco-de-observacoes-recolhivel.md#a-decisão-que-difere-do-bloco-dos-descartados-ele-nasce-aberto` | A decisão que difere do bloco dos descartados | regra-nova | O bloco novo reusa a forma de aviso aberto (`details` com `open` e `--aviso-bg`); o bloco de observações e o de descartes não mudam |
| `_reversa_sdd/addenda/034-revisao-dos-descartes.md#resumo-da-entrega` | Resumo da entrega | regra-nova | A promoção continua manual e só na lista completa; o bloco novo não promove nem mostra candidato |
| `_reversa_sdd/addenda/035-lista-de-trabalho-dos-descartes.md#resumo-da-entrega` | Resumo da entrega | regra-nova | A lista completa e o CSV de nove colunas continuam a via de trabalho; o bloco é um recorte, não uma segunda lista |
| `_reversa_sdd/addenda/038-humanizar-motivo-descartes.md#resumo-da-entrega` | Resumo da entrega | regra-nova | O motivo humano continua na lista completa e na planilha; o bloco novo não exibe motivo |

## Regras sob vigilância

- `W001` a `W012` — ver `_reversa_forward/039-dna-sem-correspondencia/regression-watch.md`.

## Fontes

- `_reversa_forward/039-dna-sem-correspondencia/requirements.md`
- `_reversa_forward/039-dna-sem-correspondencia/roadmap.md`
- `_reversa_forward/039-dna-sem-correspondencia/actions.md`
- `_reversa_forward/039-dna-sem-correspondencia/data-delta.md`
- `_reversa_forward/039-dna-sem-correspondencia/legacy-impact.md`
- `_reversa_forward/039-dna-sem-correspondencia/regression-watch.md`
- `_reversa_forward/039-dna-sem-correspondencia/progress.jsonl`
- `_reversa_forward/039-dna-sem-correspondencia/interfaces/bloco-dna-sem-correspondencia.md`

## Atualização 2026-10-22

As emendas `E001` e `E002` mudaram a entrega:

- o corte de triagem passou de **40,0** para **20,0 cM** — o recorte da análise real passou de
  9 para **60 itens**;
- o bloco separado **deixou de existir**: os itens agora são **cartões na lista de resultados**,
  com o mesmo tratamento dos cartões "Parentesco documental não encontrado" (rótulo,
  cabeçalho, as cinco seções e o recolhimento), **sem diagrama e sem promoção**; o **MRCA
  estimado do kit** continua visível na seção 2 (Evidência genética);
- a projeção histórica **ignora** os cartões sem correspondência (não há pessoa para
  `match_result.matched_person_xref` NOT NULL/FK); eles continuam registrados em
  `skipped_match`, como descartes;
- a lista completa de descartes e o CSV de nove colunas continuam intactos; o mesmo item
  aparece nos dois lugares, e o resumo dos resultados diz que os N cartões sem
  correspondência também estão na lista completa;
- a análise real passa a **68 cartões** (8 aceitos + 60 sem correspondência), **448
  descartes** e **60** itens em `sem_correspondencia`; Clezia Santos (154,5 cM) e Airton
  Passos Vasconcelos (51,3 cM) estão entre os cartões sem correspondência;
- `W005` e `W007` foram substituídos por `W010` e `W011`; a vigilância vigente é
  `W001`–`W012`, no `_reversa_forward/039-dna-sem-correspondencia/regression-watch.md`.
- a **E003** removeu o seletor `core.sem_correspondencia.selecionar`: o módulo fica só
  com a regra (`CM_MINIMO_SEM_CORRESPONDENCIA`, `nomes_com_cartao_aceito` e `elegivel`),
  e a aplicação deriva `sem_correspondencia` dos **próprios cartões** marcados em
  `resultados` — não há segunda seleção. Nenhuma mudança de tela, descartes, CSV,
  projeção histórica ou promoção; a suíte passa a **1409 passed, 9 skipped** (antes:
  1412/9). O `mrca_generations` do descarte permanece sem consumidor na tela (B+ não
  aplicado); o cartão lê o MRCA de `genetic_evidence`.

Nenhum limiar de matching, veredito, cM, caminho, motivo ou promoção foi alterado.

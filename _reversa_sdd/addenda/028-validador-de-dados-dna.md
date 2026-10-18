# Adendo: validador de dados de DNA × GEDCOM

> Identificador: `028-validador-de-dados-dna`
> Data: `2026-10-18`
> Cenário: **legado** (âncora em `_reversa_sdd/architecture.md` e `_reversa_sdd/domain.md`)

## Vigência

Vigente desde 2026-10-18.

## Resumo da entrega

A feature entrega um módulo de **validação temporal** para comparações entre um kit de DNA e uma
pessoa do GEDCOM. Para cada comparação, ele devolve um de três status — `VALIDADO`,
`INCONCLUSIVO` ou `ERRO CRONICO / QUEBRA DE LINHA` —, estima o ano do MRCA a partir do cM, mede a
idade por lado (doador e match), confere a coerência entre cM e profundidade documental e acusa
conflitos biológicos críticos, como um doador vivo ligado a um ancestral do século XVII por um
caminho curto demais.

A entrega foi concluída em **19 de 19 ações**. Ela é composta por:

- `core.validator` — regras puras, sem árvore, arquivo, HTTP ou relógio;
- `application.validacao` — fachada que lê o GEDCOM uma vez, lê o CSV, reutiliza o matching e o
  parentesco documental existentes e chama o núcleo;
- `core.janela_de_vida.data_imprecisa` — wrapper público, sem mudança de comportamento.

O status novo é um **campo separado**: `COMPATIVEL`, `POSSIVEL`, `CONFLITANTE` e `INCONCLUSIVO`
continuam existindo, com o mesmo texto e a mesma classe CSS. Não há mudança em `app.py`, template,
CSS, `init.sql`, `requirements.txt` ou nas tabelas do banco. O maior segmento não entra na
estimativa do MRCA; a marca de 15 cM continua em `core.genetic_evidence`.

**Achado registrado no código:** a coluna `meioses` de `SCP40_ROWS` não é o total de saltos do
caminho — para `1C`, a tabela diz 2 e o caminho tem 4. O núcleo deriva o total da chave canônica
(`1C` → 4, `2C` → 6, `1C1R` → 5), sem alterar a tabela.

## Impacto por artefato da extração

| Artefato | Seção | Tipo de impacto | Delta |
|----------|-------|-----------------|-------|
| `_reversa_sdd/architecture.md` | §3 Componentes e estrutura de pacotes | componente-novo | `core.validator` concentra a decisão pura; `application.validacao` faz a leitura e o cruzamento, sem tocar na borda HTTP |
| `_reversa_sdd/architecture.md` | §3 Componentes e estrutura de pacotes | regra-nova | `core.janela_de_vida` ganha `data_imprecisa(texto)` público; a lista de qualificadores e os limiares 105/122 não mudam |
| `_reversa_sdd/architecture.md` | §4 Modelo de dados | delta-de-dados | Nenhuma estrutura persistente nova; `ComparacaoParaValidar`, `MrcaEstimado` e `ResultadoDeValidacao` vivem só em memória |
| `_reversa_sdd/domain.md` | §2.1 Os quatro estados do confronto | regra-nova | O confronto ganha um veredito de validação separado, com três literais; os quatro estados não são renomeados nem substituídos |
| `_reversa_sdd/domain.md` | §3.1 Parentesco documental | regra-nova | A faixa 12–70 passa a ser aplicada também **por lado** (doador e match), não só por salto; o MRCA não pode nascer depois do descendente |
| `_reversa_sdd/domain.md` | §3.3 Possibilidades (Shared cM Project 4.0) | regra-nova | A coluna `meioses` da tabela é lida como chave de relação, não como total do caminho; o total é derivado da chave |
| `_reversa_sdd/code-analysis.md` | §4 Unidade `analise-dna` | componente-novo | A unidade ganha uma fachada de validação fora do fluxo de DNA; nenhum contrato de tela é criado |

## Regras sob vigilância

- **W001** — `data_imprecisa` público e com a mesma lista de qualificadores; ver
  `_reversa_forward/028-validador-de-dados-dna/regression-watch.md#watch-principal`.
- As observações **O-01 a O-04** do mesmo arquivo registram a pureza do núcleo, os literais do
  status, a preservação dos quatro estados e o cM por kit, sem peso de regressão.

## Fontes

- `_reversa_forward/028-validador-de-dados-dna/requirements.md`
- `_reversa_forward/028-validador-de-dados-dna/roadmap.md`
- `_reversa_forward/028-validador-de-dados-dna/legacy-impact.md`
- `_reversa_forward/028-validador-de-dados-dna/regression-watch.md`
- `_reversa_forward/028-validador-de-dados-dna/progress.jsonl`

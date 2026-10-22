# Adendo: explicar a fonte não declarada

> Identificador: `042-explicar-fonte-nao-declarada`
> Data: `2026-10-22`
> Cenário: **legado** (âncora em `_reversa_sdd/architecture.md` e `_reversa_sdd/data-dictionary.md`)
> Modo: **express** — a spec fina vive em `_reversa_forward/042-explicar-fonte-nao-declarada/`

## Vigência

Vigente desde 2026-10-22.

## Resumo da entrega

Na seção 2, um cartão com valor de fonte que não é laboratório exibia `Fonte: não declarada` e a etiqueta
com o texto original — **sem dizer o que aquele texto era**. O cartão passou a explicar o motivo ao lado
da etiqueta, usando a classificação que o núcleo já fazia e a tela não mostrava:

| Valor no arquivo | O que o cartão exibe agora |
|---|---|
| `Migration - F2 - T` | `Fonte: não declarada` `Migration - F2 - T` — **nome de projeto de pesquisa, não de laboratório** |
| `Outro (insira o nome abaixo)` | … — **texto de formulário do site de origem, não um laboratório** |
| `Minha herança` | … — **empresa não confirmada pelo projeto, que não presume o laboratório** |
| `L1b1a` | … — **haplogrupo na coluna de fonte, não um laboratório** |
| `-` ou vazio | `Fonte: não declarada` — **o arquivo não traz uma fonte utilizável nesta coluna** (sem etiqueta) |
| `Genera` | `Fonte: Genera` — sem texto extra |

O texto original continua visível sempre que há conteúdo; a etiqueta é omitida só para `-`/vazio, que não
têm o que mostrar. `MOTIVOS_TEXTO` (contagem do painel de cobertura) ficou separado de `EXPLICACOES`
(frase do cartão) de propósito: são leituras diferentes do mesmo motivo.

**4 ações concluídas** (`T001`–`T004`). Suíte em **1500 passed, 9 skipped** (antes: 1492/9, delta de +8).
Na análise real, os 8 cartões com fonte não declarada passaram a exibir a explicação, e nenhum cartão com
laboratório reconhecido ganhou texto extra.

## Impacto por artefato da extração

| Artefato | Seção | Tipo de impacto | Delta |
|---|---|---|---|
| `_reversa_sdd/architecture.md#3-componentes-e-estrutura-de-pacotes` | §3 Componentes e estrutura de pacotes | delta-de-contrato-externo | A linha `Fonte:` do bloco 2 na resposta HTML de `POST /` (`action=dna_analysis`) passa a exibir `— <explicação do motivo>` e a omitir a etiqueta quando o valor é `-` ou vazio |
| `_reversa_sdd/data-dictionary.md#54-evidência-consolidada-de-uma-pessoa-evidence_for` | §5.4 Evidência consolidada | delta-de-dados | `evidence_for` ganha `source_motivo` e `source_explicacao` (aditivos); `source` e `source_original` não mudam |
| `_reversa_sdd/addenda/040-fonte-e-cobertura-do-arquivo.md#resumo-da-entrega` | Resumo da entrega | regra-alterada | A etiqueta do texto original, criada pela 040, deixa de vir sozinha: agora vem acompanhada da explicação do que aquele valor é |

## Regras sob vigilância

- `W001` a `W003` — ver `_reversa_forward/042-explicar-fonte-nao-declarada/regression-watch.md`.
- As três observações sem peso (laboratório sem texto extra, original nunca escondido e a frase ser do
  projeto) estão no mesmo arquivo.

## Fontes

- `_reversa_forward/042-explicar-fonte-nao-declarada/requirements.md`
- `_reversa_forward/042-explicar-fonte-nao-declarada/roadmap.md`
- `_reversa_forward/042-explicar-fonte-nao-declarada/actions.md`
- `_reversa_forward/042-explicar-fonte-nao-declarada/legacy-impact.md`
- `_reversa_forward/042-explicar-fonte-nao-declarada/regression-watch.md`
- `_reversa_forward/042-explicar-fonte-nao-declarada/progress.jsonl`

# Adendo: fonte normalizada e cobertura do arquivo

> Identificador: `040-fonte-e-cobertura-do-arquivo`
> Data: `2026-10-22`
> Cenário: **legado** (âncora em `_reversa_sdd/architecture.md`, `_reversa_sdd/domain.md` e
> `_reversa_sdd/data-dictionary.md`)

## Vigência

Vigente desde 2026-10-22.

## Resumo da entrega

A tela de DNA exibia a **fonte** exatamente como veio do CSV — inclusive
`Outro (insira o nome abaixo)`, `Selecione uma empresa ou fonte` e `-` — e não dizia nada sobre o
arquivo como um todo. A entrega faz três leituras novas sobre o dado que já existia, sem tocar em
nenhuma decisão de parentesco:

1. **Fonte normalizada** por um catálogo declarado de 11 laboratórios
   (`core.fontes_de_laboratorio`): o valor cru vira rótulo canônico (`Genera`, `meuDNA`, …,
   `não declarada`, `outro`), com o texto original preservado em `source_raw`. A escolha dentro do
   kit passou a preferir a **primeira linha com laboratório reconhecido**, e dois laboratórios no
   mesmo kit emitem o aviso `fontes_divergentes`.
2. **Cobertura do arquivo** (`core.cobertura_do_arquivo`), derivada das evidências já montadas e
   exibida num bloco de escopo-arquivo antes dos cartões: linhas, evidências, kits, laboratórios e
   grafias, cromossomos, mediana de cM, percentual de segmentos abaixo do piso de 10 cM e
   percentual de evidências sem bloco de 15 cM.
3. **Estado da medida** por cartão (`core.qualidade_da_medida`): `robusta`, `parcial` ou
   `insuficiente`, com os três números que o produzem e a ressalva "Qualidade da medida, não do
   parentesco."

Na análise real de 2026-10-22 (`Adriano_Santos_v3_tratado.ged` + `Famílias_Sergipanas.csv`):
**68 cartões e 448 descartes idênticos aos de antes**; painel com **617 / 456 / 456 / 11 (de 45) /
22 / 9,05 / 74% / 88%** e **59** células sem laboratório; estados **35 robusta / 28 parcial / 5
insuficiente** nos cartões. **20 ações concluídas** (`T001`–`T020`); suíte em **1492 passou, 9
pulados** (antes: 1409/9). `SHA_DA_TELA` inalterado (`7375696d…`, 16.504 bytes).

**Achado fora do escopo:** o harness de paridade está com **30 divergências pré-existentes** —
motivo humanizado (feature 038), aceitação (024/034) e 18 em `ancestral`. A última medição com
100% é de 2026-10-13. Nenhuma vem desta entrega: o coletor não captura `source`, `medida` nem
`cobertura`. Detalhe em `_reversa_forward/040-fonte-e-cobertura-do-arquivo/evidence/depois/paridade.txt`.

## Impacto por artefato da extração

| Artefato | Seção | Tipo de impacto | Delta |
|---|---|---|---|
| `_reversa_sdd/architecture.md#3-componentes-e-estrutura-de-pacotes` | §3 Componentes e estrutura de pacotes | componente-novo | Entram três módulos puros: `core.fontes_de_laboratorio` (catálogo, `rotulo`, `escolher`), `core.qualidade_da_medida` (pisos e `avaliar`) e `core.cobertura_do_arquivo` (`medir`) |
| `_reversa_sdd/architecture.md#3-componentes-e-estrutura-de-pacotes` | §3 Componentes e estrutura de pacotes | delta-de-dados | `core.genetic_evidence` passa a levar `source` canônico + `source_raw` + `source_motivo` + `medida`; `core.dna_analysis` ganha o coletor `cobertura`; `application.dna_analysis` expõe `ResultadoDeAnalise.cobertura`; `app.py` repassa ao template |
| `_reversa_sdd/architecture.md#3-componentes-e-estrutura-de-pacotes` | §3 Componentes e estrutura de pacotes | delta-de-contrato-externo | A resposta HTML de `POST /` com `action=dna_analysis` ganha o bloco "Cobertura do arquivo", a etiqueta do texto original na linha `Fonte:` e a linha da medida no bloco 2; request, status, erros e timeouts não mudam, e a tela de entrada não muda um byte |
| `_reversa_sdd/domain.md#32-evidência-genética` | §3.2 Evidência genética | regra-alterada | A fonte deixa de ser o texto cru: `source` é rótulo canônico e o original fica em `source_raw`. A chave (nome, kit), o "nunca somar kits" e o `None` honesto continuam valendo; `medida` é campo novo e não participa da aceitação |
| `_reversa_sdd/domain.md#2-a-regra-central-do-domínio-três-eixos-que-não-se-contaminam` | §2 A regra central | regra-nova | O estado da medida é explicitamente **qualidade do dado**, com ressalva na tela; não recolore, não rebaixa e não substitui o confronto, a viabilidade ou o selo de cM |
| `_reversa_sdd/code-analysis.md#46-constantes-parâmetros-e-configuração` | §4.6 Constantes | regra-alterada | `LIMITE_SEGMENTO_FRACO` continua `15.0`, mas passa a referenciar `qualidade_da_medida.PISO_MAIOR_BLOCO_CM`: o dono do número mudou de módulo, o valor não |
| `_reversa_sdd/data-dictionary.md#51-evidência-por-nome-normalizado-kit` | §5.1 Evidência por (nome, kit) | delta-de-dados | `source` muda de **semântica** (era "primeira não vazia", agora é rótulo); entram `source_raw`, `source_motivo` e `medida` (estado, motivos, números, ressalva). Nenhum campo existente muda de nome, tipo ou ordem |
| `_reversa_sdd/data-dictionary.md#54-evidência-consolidada-de-uma-pessoa-evidence_for` | §5.4 Evidência consolidada | regra-alterada | `source` devolve o rótulo; o texto `"fonte não identificada no CSV"` só aparece quando o CSV não tem coluna de fonte; ganha `source_original` para a etiqueta |
| `_reversa_sdd/addenda/017-observacao-de-arquivo-nao-e-observacao-de-cartao.md#para-que-a-frase-serve--a-parte-que-se-manteve` | A parte que se manteve | regra-nova | O painel é de **escopo-arquivo**: fica fora da guarda dos cartões, como o bloco de observações, e não se repete em cartão nenhum |
| `_reversa_sdd/addenda/022-bloco-de-observacoes-recolhivel.md#o-que-mudou` | O que mudou | regra-nova | O painel reusa a forma `details` aberto + `summary` + `card-body`; o cabeçalho ganha a classe `cabecalho-da-cobertura` para não ser tomado por cartão de resultado, e o bloco de observações fica intocado |

## Regras sob vigilância

- `W001` a `W011` — ver `_reversa_forward/040-fonte-e-cobertura-do-arquivo/regression-watch.md`.
- As quatro observações sem peso (paridade, `TestCompany`, ausência de `BR-D` para `source`, e o
  catálogo provisório de "Minha herança"/"Meu Patrimônio") estão no mesmo arquivo.

## Fontes

- `_reversa_forward/040-fonte-e-cobertura-do-arquivo/requirements.md`
- `_reversa_forward/040-fonte-e-cobertura-do-arquivo/roadmap.md`
- `_reversa_forward/040-fonte-e-cobertura-do-arquivo/actions.md`
- `_reversa_forward/040-fonte-e-cobertura-do-arquivo/data-delta.md`
- `_reversa_forward/040-fonte-e-cobertura-do-arquivo/legacy-impact.md`
- `_reversa_forward/040-fonte-e-cobertura-do-arquivo/regression-watch.md`
- `_reversa_forward/040-fonte-e-cobertura-do-arquivo/progress.jsonl`
- `_reversa_forward/040-fonte-e-cobertura-do-arquivo/investigation.md`
- `_reversa_forward/040-fonte-e-cobertura-do-arquivo/onboarding.md`
- `_reversa_forward/040-fonte-e-cobertura-do-arquivo/interfaces/bloco-cobertura-e-estado.md`

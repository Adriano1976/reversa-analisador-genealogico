# Adendo 057 — Distribuição por cromossomo

> Identificador: `057-distribuicao-por-cromossomo`
> Data: `2026-11-11`
> Cenário: `legado` (extração em `_reversa_sdd/`, com `architecture.md` e `domain.md`)
> Feature: `_reversa_forward/057-distribuicao-por-cromossomo/`

## Vigência

Vigente desde 2026-11-11.

## Resumo da entrega

O cartão "Regiões compartilhadas" ganhou um gráfico de barras por cromossomo com **dois eixos**:
**Matches** (kits distintos com região naquele cromossomo) à esquerda e **cM médio** (média
aritmética dos segmentos de 10 cM ou mais que formam as regiões) à direita. As duas séries partem
de zero e têm escalas independentes; o cartão do hover e do foco de teclado mostra o cromossomo, o
número de matches e o cM médio. A feature é **leitura derivada**: não relê o CSV, não faz segundo
matching, não soma cM e não altera nenhum veredito.

Foram executadas **18 de 18** ações do `actions.md` (Preparação 3, Testes 4, Núcleo 3,
Integração 5, Polimento 3), sem falha.

## Impacto por artefato da extração

| Artefato | Seção | Tipo de impacto | Delta |
|----------|-------|-----------------|-------|
| `_reversa_sdd/architecture.md` | §3. Componentes e estrutura de pacotes | `componente-novo` | Três módulos novos: `src/core/distribuicao.py` (agregação), `src/application/distribuicao.py` (projeção) e `src/reporting/distribuicao.py` (geometria). `src/app.py` projeta e desenha uma vez, como já fazia com as regiões |
| `_reversa_sdd/c4-components.md` | Fichas de componente (nível 3) | `componente-novo` | Fichas dos três módulos, com o detalhe de que a agregação é derivada das regiões e que o desenho não formata número |
| `_reversa_sdd/data-dictionary.md` | §8.2. `ResultadoDeAnalise` | `delta-de-dados` | Campo novo `distribuicao: tuple`, default `()`, preenchido em `application/dna_analysis.py` depois da classificação das regiões |
| `_reversa_sdd/domain.md` | §1. Glossário de Domínio | `regra-nova` | "Distribuição por cromossomo": por cromossomo, **kits distintos** (um kit conta uma vez, mesmo em duas regiões) e **cM médio** de um segmento por kit, o de maior cM (`D-12`) |
| `_reversa_sdd/inventory.md` | Superfície do código | `componente-novo` | Três arquivos de `src/` e três de `tests/`; `tests/fixtures/sample_dna.py` ganhou a fixture sintética de 11 segmentos em 3 cromossomos |

Nenhuma regra 🟢 de `domain.md` foi alterada ou removida: a regra central (`#2`), a evidência
genética (`#3.2`) e a ordem de apresentação (`#3.9`) continuam valendo sem emenda, e o piso de
10 cM continua sendo **filtro das regiões**, não do gráfico — o gráfico lê as regiões já filtradas.

## Regras sob vigilância

`W057-01` a `W057-08` — ver `_reversa_forward/057-distribuicao-por-cromossomo/regression-watch.md`.

## Fontes

- `_reversa_forward/057-distribuicao-por-cromossomo/requirements.md`
- `_reversa_forward/057-distribuicao-por-cromossomo/roadmap.md`
- `_reversa_forward/057-distribuicao-por-cromossomo/legacy-impact.md`
- `_reversa_forward/057-distribuicao-por-cromossomo/regression-watch.md`
- `_reversa_forward/057-distribuicao-por-cromossomo/progress.jsonl`
- `_reversa_forward/057-distribuicao-por-cromossomo/evidence/` (SHA da tela, medições, captura do gráfico)

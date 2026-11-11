# Legacy Impact: distribuição por cromossomo

> Identificador: `057-distribuicao-por-cromossomo`
> Data: `2026-11-10`
> Política de edição do legado no momento da execução: `allowLegacyEdits: true`, com
> `allowedPaths` liberando `src/**`, `tests/**` e `README.md` — todos os caminhos desta feature
> estão cobertos pela lista.

## Arquivos afetados

| Arquivo afetado | Componente | Tipo | Severidade | Justificativa |
|-----------------|------------|------|------------|---------------|
| `src/core/distribuicao.py` (novo) | `analise-dna` | `regra-nova` | MEDIUM | Agregação por cromossomo: kits distintos e cM médio, como leitura derivada das regiões |
| `src/application/distribuicao.py` (novo) | `analise-dna` (projeção) | `componente-novo` | LOW | Projeta o resumo em dicionário; nenhuma decisão de negócio |
| `src/reporting/distribuicao.py` (novo) | `tela-de-resultado` (desenho) | `componente-novo` | LOW | Geometria do gráfico: topo de eixo, marcas e altura |
| `src/application/dna_analysis.py` | `analise-dna` | `delta-de-dados` | MEDIUM | Campo `distribuicao` no payload do caso de uso, preenchido em `try/except` |
| `src/app.py` | borda | `delta-de-contrato-externo` | LOW | Projeta e desenha uma vez; passa `grafico_da_distribuicao` ao template |
| `src/templates/index.html` | tela de resultado | `regra-alterada` | LOW | Sub-bloco novo dentro do cartão "Regiões compartilhadas" |
| `src/assets/app.css` | tela de resultado | `regra-alterada` | LOW | Classes do gráfico; nenhum token novo |
| `tests/fixtures/sample_dna.py` | fixtures | `componente-novo` | LOW | Fixture sintética de 11 segmentos em 3 cromossomos |
| `tests/test_distribuicao.py`, `tests/test_projecao_da_distribuicao.py`, `tests/test_grafico_da_distribuicao.py` (novos) | testes | `componente-novo` | LOW | Cobertura de `RN-02`, `RN-03`, `RN-06`, `RN-08` e da ordem |
| `tests/test_contrato_das_regioes.py` | testes | `regra-alterada` | LOW | Contrato da posição do sub-bloco e do caso sem região |
| `README.md` | documentação | `regra-alterada` | LOW | O item "Regiões compartilhadas" passa a descrever o gráfico |

## Diff conceitual por componente

**`analise-dna` (núcleo).** Nada do fluxo muda: matching, cM por segmento, ordem dos cartões e
confronto continuam idênticos. O que nasce é uma leitura **derivada** das regiões: para cada
cromossomo com região, o conjunto de kits distintos e a média dos cM do segmento escolhido de cada
kit. A derivação roda depois da classificação das regiões e é protegida por `try/except`: falha nela
some com o gráfico e acrescenta uma observação de arquivo, nunca derruba a análise — mesma política
da 056.

**Payload do caso de uso.** `ResultadoDeAnalise` ganha `distribuicao: tuple = ()`. É campo novo com
default, então toda construção existente continua válida; `data-dictionary.md#8.2` será atualizado
pelo `/reversa-sync`.

**Projeção e desenho.** `application/distribuicao.py` troca o tipo de domínio por dicionário, sem
formatar número (a formatação é do filtro do template). `reporting/distribuicao.py` calcula topo,
marcas e altura em porcentagem — desenho, não domínio.

**Tela.** O sub-bloco entra entre a legenda do ideograma e a lista de regiões, com duas barras por
cromossomo, dois eixos rotulados, legenda das séries e cartão do hover/foco reaproveitando `.dica`.

**O que NÃO mudou:** `src/parsers/`, `src/ports/`, `src/core/regioes.py`, `src/core/matching.py`,
o esquema PostgreSQL, as rotas existentes e o `/regioes.csv`.

## Preservadas

Regras 🟢 do `_reversa_sdd/domain.md` que continuam intactas:

- `#2` — os três eixos não se contaminam: o gráfico é leitura, não cria nem altera veredito.
- `#3.2` — evidência genética: o cM continua evidência adicional, nunca decisão sozinha; o gráfico
  não soma cM e não muda nenhuma classificação.
- `#3.9` — ordem de apresentação dos resultados: os cartões não são reordenados.
- `#5` — contrato de mensagens: nenhuma mensagem existente mudou de texto.

## Modificadas

Nenhuma regra 🟢 de domínio foi alterada ou removida. A feature **acrescenta** uma leitura derivada
e um campo de payload; o que existia continua com o mesmo comportamento, coberto pelos testes que
já estavam verdes antes dela.

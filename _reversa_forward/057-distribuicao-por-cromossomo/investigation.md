<!--
Investigação de fundo da feature 057 — Distribuição por cromossomo.
Pesquisa de alternativas e fontes; não decide requisito (isso está no requirements.md).
-->

# Investigação: Distribuição por cromossomo

> Identificador: `057-distribuicao-por-cromossomo`
> Data: `2026-11-10`
> Insumo visual: as duas capturas enviadas pelo operador em 2026-11-10 (painel "Distribuição por
> Cromossomo", barras agrupadas por cromossomo com dois eixos e cartão no hover)

## 1. O problema que o gráfico resolve

O bloco "Regiões compartilhadas" hoje responde **onde**: o ideograma posiciona cada região no
cromossomo. Não responde **quanto**: quantos matches o arquivo tem em cada cromossomo e qual o
tamanho médio desses segmentos. Sem isso, comparar dois arquivos — ou dois cromossomos do mesmo
arquivo — exige abrir a lista e somar de cabeça, que é exatamente o que o produto evita.

## 2. O risco conhecido do gráfico de dois eixos

O gráfico de duas séries com duas escalas é o tipo mais contestado em visualização de dados, e o
motivo é específico: **ele parece fácil de ler e não é**. A leitura errada típica é comparar a
altura da barra verde com a da barra escura e concluir uma relação que a escala inventou. Duas
recomendações do material de referência entram direto nos requisitos:

- **"If you start one axis at zero, start the other one at zero, too"** — barra pressupõe base
  zero, e as duas séries precisam do mesmo referencial ([Datawrapper, guia de dois eixos](https://www.datawrapper.de/blog/dual-axis-charts-guide)). Virou `RN-08`.
- **Declarar as duas medidas no texto do gráfico**, com legenda e cartão de hover que nomeiam as
  séries, porque o título sozinho não desfaz a confusão. Virou `RF-08` e `RF-06`.

O guia também recomenda "alinhar as escalas" (mesma taxa de crescimento nas duas), o que **não se
aplica aqui**: alinhar taxa em barras categóricas exigiria transformar um dos números, e o produto
não altera número de genética para caber no desenho. A escolha foi manter as duas escalas honestas,
rotuladas e independentes (`RN-04`), com o cartão dizendo os dois valores exatos.

## 3. Alternativas avaliadas

| Alternativa | Por que foi descartada |
|-------------|------------------------|
| **Dois gráficos separados** (small multiple: um para matches, um para cM médio) | Elimina o risco de leitura cruzada, mas dobra a altura do bloco, separa os dois números do mesmo cromossomo e perde a comparação lado a lado que o operador pediu |
| **Uma série só, com um eixo** | Não há como: matches é contagem e cM é centimorgan. Escolher um dos dois deixa metade da pergunta sem resposta |
| **Tabela por cromossomo** | Honesta e acessível, mas foi justamente o que o operador pediu para não ser: a leitura de relance se perde, e a lista de regiões logo abaixo já é textual |
| **Barras agrupadas com dois eixos, base zero e topo redondo** (escolhida) | Atende o pedido, mantém os dois números juntos e o risco fica controlado por rótulo, legenda, base zero e cartão |
| **Biblioteca de gráfico (JavaScript)** | A tela não pode buscar recurso fora da origem (`tests/test_tela_sem_origem_externa.py`) e o resultado precisa imprimir sem depender de hover |

## 4. Como a barra vira altura (o "número redondo")

Base zero resolve metade do problema; a outra metade é o topo. Topo no maior valor exato faz a
barra mais alta encostar na borda e as demais ficarem com alturas arbitrárias; topo "redondo" com
marcas igualmente espaçadas dá escala legível. O critério adotado é o mesmo usado por escalas
contínuas em bibliotecas de gráfico: escolher um passo "bonito" (1, 2, 5 × 10ⁿ) a partir do
intervalo desejado e multiplicar pelo número de marcas — a ideia está descrita em
[`d3-scale` (`nice`, `tickStep`)](https://cdn.jsdelivr.net/npm/d3-scale@4.0.2/README.md#2). Aqui o
passo é escolhido entre conjuntos fixos para contagem e para cM, porque o domínio é pequeno
(poucas dezenas de kits, cM na casa das dezenas) e um passo fixo é testável.

## 5. Densidade do eixo dos cromossomos

Com 22 cromossomos autossômicos mais X/Y/MT, o rótulo `Chr 22` na horizontal não cabe. As opções
usuais são girar o rótulo, mostrar um a cada dois, ou encurtar. A escolha: rótulo curto (`Chr N`),
giro de 45°, largura mínima por coluna e o nome completo no `aria-label` do botão — o mesmo padrão
que a 056 fixou para a faixa do ideograma, em que o dado nunca existe só no mouse.

## 6. O que já existe no projeto e serve de molde

| Peça existente | Como é reaproveitada |
|----------------|----------------------|
| `src/reporting/ideograma.py` | Prova que a geometria pode ser calculada em Python puro (`esquerda`, `largura`, `lado`) e testada sem navegador |
| `.dica` (CSS da 056) | Cartão do hover com `bottom: calc(100% + 8px)`, foco de teclado e `role="tooltip"` |
| Filtros `inteiro_br`, `decimal_br`, `cm_br` | Formatação dos números do eixo e do cartão, sem duplicar regra |
| `montar_ideograma` + `SHA_DA_TELA` | Modelo de invariante: o bloco só existe com resultado, então a tela de entrada não muda |

## 7. Fontes consultadas

- Datawrapper — *What to consider when creating dual-axis charts*: https://www.datawrapper.de/blog/dual-axis-charts-guide (consultado em 2026-11-10)
- `d3-scale` — `continuous.nice` e `tickStep`, referência do passo "bonito": https://cdn.jsdelivr.net/npm/d3-scale@4.0.2/README.md#2 (consultado em 2026-11-10)
- Flourish — *Dual axis charts: why they spark debate, and how to get them right*: https://flourish.studio/blog/dual-axis-charts/ (consultado em 2026-11-10)
- Capturas do painel de referência enviadas pelo operador (2026-11-10), usadas como alvo visual e não como fonte de número

# Verificação nova — profundidade do caminho × estimativa do próprio kit

**Data:** 2026-10-14
**Tipo:** **acréscimo na camada de verificação**, com um defeito de apresentação corrigido de
passagem. Não altera decisão de matching, escolha de pessoa, caminho nem veredito.
**Arquivos alterados:** `src/core/profundidade_do_caminho.py` (novo),
`src/core/genetic_evidence.py`, `src/core/relationship_hypotheses.py`,
`src/core/evidence_comparison.py`, `src/core/dna_analysis.py`,
`src/reporting/mermaid_render.py`, `src/app.py`, `src/templates/index.html`,
`src/assets/app.css`, `README.md`
**Teste novo:** `tests/test_profundidade_do_caminho.py` (47 testes)

## De onde veio

O operador apresentou um diagrama — "Árvore de Adriano Santos com correção de conexão DNA
(Margarida)" — com quatro regras de negócio propostas para tratar conflitos entre árvore e DNA.
O diagrama está certo na direção, mas das quatro regras **três já existiam** e a quarta era a
única que eu recusaria. Medir a proposta antes de aceitá-la foi o que produziu o trabalho: a
medição achou uma verificação que faltava, e um defeito de tela que ninguém tinha visto.

## O que a medição da proposta mostrou

| Regra proposta | Situação real |
|---|---|
| 1. Ramo do usuário imutável | Já é a regra do projeto. A parte **epistêmica** ("é fato consolidado") foi recusada: a árvore não é infalível — nesta mesma sessão ela precisou de correção de dado. |
| 2. Cruzar cM × data | **Já existia**: é a coluna "Confrontação" (`evidence_comparison`), e com fonte publicada em vez de limiar de mão. |
| 3. Desacoplar identidade | **Já existia**: selo de identidade + janela de vida. |
| 4. Interpolar nós de 25–30 anos | **Recusada como dado.** Medi: cobrir os hiatos dos 10 cartões exigiria **104 a 125 nós inventados**, enxertados no ancestral errado (o homônimo que o motor escolheu). Adotada como **desenho**: o diagrama do operador já a marca como "teórico". |

Os três números do diagrama foram reproduzidos de forma independente: 21,6 cM, **5,7 gerações**
(tabela do Shared cM Project) e **353 anos** (2026 − 1673).

## A verificação que faltava

Duas verificações já existiam e **não se sobrepõem** a esta:

- a **janela de vida** pergunta se a pessoa escolhida pode ter doado aquele DNA;
- o **confronto** pergunta se o cM cabe na faixa publicada para o parentesco documental.

Faltava a que não depende de ninguém estar vivo: **a árvore afirma a mesma profundidade que o
próprio kit informa?** Medido em 2026-10-14, existe **um** cartão em que as duas primeiras se
calam e esta acusa — e é isso que a torna necessária, e não redundante:

```
kit XS4787142   19,2 cM   doadora nascida em 1976   "Primos de 8º grau com 2× remoção"
  janela de vida ....... 50 anos, plausível  -> silêncio
  confronto ............ versão 4.0 não publica faixa para 20 meioses -> silêncio
  profundidade ......... árvore afirma 10,0 gerações; o kit estima 4,77 -> 2,1×  DIVERGÊNCIA
```

## A coluna que o app lia e descartava

`MRCA` é uma coluna do próprio CSV de matches — a estimativa de gerações até o ancestral comum
que o GEDmatch publica por kit. **270 de 270 kits** do arquivo real a trazem. `csv_ingest`
recebia o arquivo e a jogava fora: `aggregate_matches` preserva apenas `Name` e `cM`.

Trazida de volta por `core.genetic_evidence` (o módulo dono do que o arquivo de DNA afirma), ela
é o **único** número do arquivo que fala de profundidade. Nenhuma tabela nova foi inventada.

**A divisão por dois não é arbitrária.** `MRCA` é um número só para o **par**; `meioses` conta os
saltos dos **dois** lados. O comparável é a média. Calibragem medida em dois cartões
independentes, sem ajuste: `1C7R` (11 meioses, média 5,5) contra `MRCA` 4,57; `1C6R` (8 meioses,
média 4,0) contra `MRCA` 5,19.

## Os limiares

**2,0** para divergência e **1,5** para atenção. A estimativa `MRCA` é derivada do cM e tem
incerteza própria: 1,3 está dentro do ruído. **Dobro** não está — é a afirmação de que o caminho
documental tem duas vezes mais gerações do que o cM sustenta.

Medido nos 62 cartões: **1 divergência** (2,10) e **4 atenções** (1,70 a 1,96). Cinco delas são o
**mesmo ancestral contado cinco vezes** (`Manoel da Silva Vieira`, 1720, `@I8bf4f5b7@`, em cinco
kits de 11,2 a 34,5 cM) — a concentração que o diagrama do operador mostra visualmente, e que o
app apresentava como cinco achados independentes. Com limiar 1,3 marcaria 6, e eu não confio em
1,3: está dentro do ruído de quem estima gerações a partir de um segmento.

## O defeito de tela que a medição achou

No cartão `TG8027863` (25,4 cM, casado com registro de **1793**), o cabeçalho dizia
**"Compatível"** e o aviso imediatamente abaixo dizia **"nenhuma pessoa com essa idade pode ter
doado DNA"**. Os dois estavam certos sobre eixos diferentes — o cM cabe na faixa para aquele
parentesco, mas a identidade não fecha —, e o selo é o mais visível dos dois.

O veredito **não** mudou em campo nenhum (`comparison` fica intacto, e a seção 4 continua
mostrando o confronto de cM, que é outra pergunta). O que mudou é o **rótulo do cabeçalho**, que
passa a dizer os dois. Agora o cartão lê:

> Análise de conexão com **Manoel da Silva Vieira** · DNA: 25,4 cM · **compatível no cM,
> identidade impossível**

O "no cM" é deliberado: o cabeçalho já mostra o selo `DNA: 25,4 cM` imediatamente antes, e a
primeira versão do rótulo repetia a unidade (`cM compatível`) — lia como gagueira.

## O silêncio virou achado — sem criar quinto estado

Os **quatro estados do confronto são contrato declarado**: `RF-19`, `BR-D-27`, `contracts.md`
§5.1, ADR-15, `CHECK` no banco em quatro lugares e três arquivos de teste. Um quinto estado
(`FORA_DE_ALCANCE`) seria violação de contrato, não melhoria — e o ADR-15 já decidiu que ausência
de faixa publicada **não** vira veredito.

Então o veredito continua `INCONCLUSIVO`, e o que mudou foi o **texto**. Medi a causa real dos 7
cartões que ficavam em silêncio, e são **duas** causas diferentes:

- **3 além do alcance** (18, 19 e 20 meioses, contra um teto publicado de 16) — o texto agora diz
  que a relação é mais profunda que a mais distante que a fonte calibra, e que o silêncio não é
  concordância;
- **4 em lacuna da tabela** (13 e 15 meioses, entre 12 e 14 e entre 14 e 16) — o texto nomeia os
  vizinhos publicados e diz que nenhuma janela foi emprestada por proximidade.

O caminho fácil — usar a janela do número de meioses mais próximo — daria veredito aos 7, e é
**exatamente inventar número**: não foi feito, e há teste prendendo isso.

## O desenho

No diagrama do cartão, quando há divergência:

- o **ancestral comum documental** continua amarelo e ganha contorno **vermelho tracejado**;
- o **ponto do caminho na profundidade que o kit estima** ganha contorno **roxo tracejado**;
- uma **legenda** em nó solto, sem aresta, com os dois números.

O ponto roxo é **sempre uma pessoa que já estava no caminho documental**. Nenhum nó é criado e
nenhuma geração é interpolada — é o oposto da Regra 4 da proposta: o desenho mostra onde o DNA
sugere o ancestral e onde a árvore o colocou, sem preencher o meio. Quando o GEDCOM não alcança a
profundidade sugerida, só o ancestral é marcado.

**O ancestral é marcado trocando o estilo que já está no texto**, e não por um id recebido de
fora. Com casal, o renderizador funde o ancestral e o cônjuge num nó único (`A+B`), e o id do
ancestral sozinho **não existe** no diagrama — o `style` cairia no vazio, sem erro nenhum, e a
marca sumiria justamente nos casos com casal. Reimplementar a decisão do casal aqui duplicaria
regra que o ADR-11 mantém no renderizador. A primeira versão desta correção tinha esse defeito, e
a verificação na tela o pegou.

A dependência é **opcional** em `Dependencias` (como `generate_mermaid_indirect`): sem ela, o
diagrama sai exatamente como sempre saiu, e nenhuma sonda ou teste antigo precisou mudar.

## A legenda do diagrama

Um desenho colorido sem legenda obriga o operador a adivinhar, e adivinhar cor é adivinhar
conclusão. O diagrama usava **três cores desde sempre** — verde, vermelho e amarelo — e nenhuma
delas estava explicada em lugar nenhum da tela. A legenda agora explica as cores que **aquele**
diagrama mostra:

| Amostra | Significado |
|---|---|
| Verde | Você, o ponto de partida da análise |
| Vermelho | A pessoa do GEDCOM que o relatório de DNA indicou |
| Amarelo | O ancestral comum que o GEDCOM afirma |
| Amarelo com contorno vermelho tracejado | O mesmo ancestral, com o elo que o DNA não sustenta (ou, em atenção, uma diferença a conferir) |
| Roxo tracejado | Onde o DNA sugere o ancestral comum — sempre uma pessoa que já estava no caminho |
| Sem destaque | O caminho documental comum |

E, abaixo da lista, um **bloco informativo** com a leitura em uma frase: *"O que os números mostram. Confira
a profundidade: a árvore afirma 7,5 gerações até o ancestral comum; este kit estima 4,3."*

### A frase saiu de dentro do grafo

Essa frase nasceu como um **nó solto do Mermaid**, desenhado ao lado do diagrama — e estava errado. Num
`flowchart` toda caixa parece um parente: o operador que vê uma caixa no grafo espera que ela seja uma pessoa
ou um vínculo, e uma frase dentro de uma caixa no meio de um pedigree se lê como parte do parentesco.

A correção moveu o texto para o bloco informativo da legenda e **tirou todo texto do desenho**. Duas
consequências de projeto:

1. a função que montava a frase saiu de `reporting/` e foi para
   `core.profundidade_do_caminho.resumo_da_profundidade` — texto que lê números do domínio não pertence ao
   renderizador, e agora o template o consome pronto (o template não remonta frase de domínio);
2. `anotar_profundidade` passou a **só emitir linhas `style`**, e isso virou guarda testada: o teste faz o
   diff por linha contra o diagrama de entrada e exige que tudo que a função acrescenta comece por `style `.
   Um nó de texto que voltasse reprova.

O texto é o mesmo, palavra por palavra — mudou de lugar, não de conteúdo. E o item "creme tracejado" da
legenda saiu junto, porque não existe mais marca creme no desenho: a legenda continua sem descrever cor
ausente.

Três decisões de projeto, e as três por um motivo de honestidade:

1. **É contextual, não fixa.** Descreve o que aquele diagrama tem. Listar uma cor ausente é ruído;
   omitir uma presente é pior que não ter legenda. Por isso o item do ancestral muda de **forma**
   (amarelo liso → amarelo com contorno tracejado) em vez de virar dois itens que se contradizem.
2. **O item do roxo depende do desenho, não do estado.** O caso adversarial está em teste: com
   0,4 gerações estimadas a divergência existe, mas o ponto sugerido cairia no próprio match e o
   diagrama sai **sem** marca roxa. A legenda acompanha — e foi o próprio teste que revelou que a
   primeira versão condicionava o item ao estado, listando uma cor ausente.
3. **A atenção não afirma o que só a divergência afirma.** A marca no desenho é a mesma nos dois
   estados; o texto muda ("com o elo que o DNA não sustenta" só na divergência, "com uma diferença
   de profundidade a conferir" na atenção). O teste prende a diferença.

**O risco desta legenda não é ela sumir: é ela mentir.** Ela descreve cores emitidas em outro
lugar — quatro literais em `reporting/mermaid_render.py` e dois no `mermaid.initialize` do
template. Por isso as amostras são presas contra a **saída real** do Mermaid, e não contra uma
cópia dos valores escrita no teste: seis testes leem a folha de estilo e comparam com o que o
renderizador efetivamente emitiu, mais um que prende que as sete amostras são distintas entre si.

## O terceiro erro meu, e o teste que ele quase escondeu

Os testes de tela gravavam os arquivos como `profundidade.ged`. O armazenamento valida a **forma**
da chave (`16hex__nome`) no `resolver`, então o POST era recusado, a tela caía no estado de
entrada e o teste media uma página **sem resultado nenhum**. Ele falhou porque eu afirmava ver a
legenda; tivesse eu afirmado "a legenda não aparece quando não há divergência", teria passado por
vácuo sobre uma tela vazia. Os arquivos passaram a usar a mesma convenção dos outros testes de
tela.

## Verificação

## Um erro meu, pego na verificação

A legenda dentro do grafo saiu **sem acentos** — `arvore`, `geracoes` — porque eu supus que a
lista branca do rótulo Mermaid os descartaria. Não descarta: as faixas `À-Ö`, `Ø-ö` e `ø-ÿ`
cobrem `á â ã ç é ê í ó ô õ ú`, e os nomes dos nós ao lado já são acentuados. Corrigido, com
teste que prende os acentos. O que de fato **não** passa é o sinal de multiplicação (U+00D7) e o
de aproximado (U+2248), que caem nos vãos das faixas — por isso "vezes" por extenso.

## Verificação

- **910 testes, zero falhas** (841 → 910; 68 novos).
- Os testes que já prendiam os **quatro estados**, a ordem de conservadorismo, a envoltória por
  meioses e a caracterização do matching passaram **sem edição** — a mudança é aditiva.
- Medido no HTML renderizado da análise real: coluna **Profundidade** no índice, 1 selo de
  divergência, 4 de atenção, 1 selo combinado no cabeçalho, **11 legendas de diagrama** (4 itens
  nos 6 cartões em concordância; 5 nos 4 em atenção e no de divergência) e nenhum nó de texto
  dentro dos 5 diagramas anotados.

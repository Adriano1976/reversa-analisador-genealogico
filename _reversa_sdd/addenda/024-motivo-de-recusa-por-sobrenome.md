# Adendo: o motivo da recusa por sobrenome deixou de acusar o arquivo

> Identificador: `024-motivo-de-recusa-por-sobrenome`
> Data: `2026-10-16`
> Cenário: **legado** (âncora em `_reversa_sdd/analise-dna/`)
> **Origem do registro:** escrito à mão, a pedido do operador. O canal canônico de adendo é o
> `/reversa-sync`, e esta linha existe para que a próxima rodada saiba que este arquivo **não**
> saiu daquele pipeline.

## Vigência

Vigente desde 2026-10-16.

**Emenda o motivo catalogado em `_reversa_sdd/analise-dna/contracts.md`** (§ "Motivos
catalogados"). **Não** muda `SHA_DA_TELA`: a tela de entrada vazia não carrega motivo nenhum —
eles só existem com uma análise carregada.

## O pedido

O operador perguntou por que matches de cM alto não entram em "Resultado da Análise". A
investigação dessa pergunta mostrou que **um dos motivos dizia algo falso sobre o arquivo dele**.

## O que mudou

O motivo era **um só**, e cobria quatro causas diferentes:

```
antes:  "sem candidatos por sobrenome (abreviação/corrupção?)"
```

Agora é quatro, um por causa:

| Causa | Motivo novo |
|---|---|
| Havia sobrenome, e ele foi empurrado para a casa do prenome | `o sobrenome foi lido como prenome (nome sem sobrenome isolável)` |
| Sobrou um token só: não havia sobrenome para perder | `o nome não tem sobrenome (nome único)` |
| O sobrenome virou inicial | `sobrenome curto demais para buscar (inicial ou abreviação)` |
| O sobrenome não está na árvore | `nenhum sobrenome do nome existe no GEDCOM` |

**A DECISÃO NÃO MUDOU.** Pool vazio descarta o nome nas quatro causas, antes e depois. O que
mudou é só o texto — e é isso que torna a mudança barata.

## Por que: a escala, medida

Rodei a análise real do operador — CSV `Famílias Sergipanas`, raiz "Adriano Santos" — nas duas
árvores, **uma árvore por processo**. O cuidado vem de um defeito medido antes: `_indice_por_nome`
invalida o cache por `(len(people), primeiro xref, último xref)`, e as duas **versões** da árvore
unificada (antes e depois do tratamento) têm as mesmas 35.460 pessoas e os mesmos xrefs — aí o
cache não invalida e a segunda medição lê o índice da primeira. Para **este** par as contagens
diferem (13.716 e 35.460), então não haveria colisão; o cuidado foi mantido porque custa zero e a
regra é do arquivo, não do par.

| | V2 tratada (13.716) | Unificada tratada (35.460) |
|---|---|---|
| Cartões | 8 | 90 |
| Descartes com o motivo antigo | **94** | **85** |
| → `nome único` | 68 | 68 |
| → `sobrenome lido como prenome` | **16** | **11** |
| → `nenhum sobrenome existe no GEDCOM` | 8 | 5 |
| → `sobrenome curto demais` | **2** | **1** |

Dos 94 grupos que liam *"abreviação/corrupção?"*, **84 não tinham sobrenome nenhum para procurar**,
2 tinham apenas uma inicial, e 8 tinham sobrenome utilizável que não existe na árvore. O
`Marcos Antonio de Melo` não é abreviação nem corrupção: `marcos` **e** `antonio`
estão os dois em `GENERIC_GIVENS`, então `melo` virou o prenome e o sobrenome sumiu do conjunto
de busca.

## A palavra antiga estava certa — em 2 dos 94

Vale registrar, porque impede a leitura de que o motivo era simplesmente ruim: `*Roger S` tem
sobrenome `s` e `A CF` tem `cf`. São iniciais de verdade. O motivo antigo acertava exatamente aí,
e errava nos outros 92. Por isso a quarta causa ficou separada em vez de absorvida: é o único
lugar onde "abreviação" descreve o arquivo.

## Duas causas escondem a mesma frase, e o critério teve de mudar

O achado caracterizado em `tests/test_characterization_matching.py` (desde 2026-09-29) descreve
**um** caminho: *"um nome cujo único token não-genérico é o sobrenome, como 'Joao Silva', tem o
sobrenome interpretado como prenome"*. Medido, esse caminho responde por **15 dos 16** grupos.

Existe um **segundo** caminho, que aquela descrição não nomeia: quando o último token é sufixo de
sobrenome, `surname_core_tokens` o consome, e o sobrenome de família — que era o token anterior —
sobra como prenome. É o caso de **`*Coutinho Neto`** (30,3 cM): `neto` sai como sufixo,
`coutinho` vira o prenome, e o conjunto de sobrenomes esvazia. **Um grupo** nesta árvore.

Foi esse segundo caminho que obrigou o critério da mensagem a ser **"sobrou mais de um token"** e
não "o primeiro token é genérico": em `*Coutinho Neto` o primeiro token não é genérico, e a versão
ingênua o mandaria para `nome único` — dizendo que ele não tem sobrenome quando ele tem.

O efeito de trocar o critério foi medido, e não suposto: `*Coutinho Neto` passou de `nome único`
para `sobrenome lido como prenome`, e `PAULO` fez o caminho inverso — um nome único de verdade, que
antes era acusado de ter perdido um sobrenome. Os totais dos dois baldes (68 e 16) ficaram iguais
por coincidência: um grupo saiu de cada lado.

## O achado caracterizado continua, e este adendo não o reabre

O comportamento — sobrenome lido como prenome, pool vazio, nome descartado — **continua sem
correção**. A docstring do próprio arquivo de caracterização declara que corrigi-lo "mudaria
comportamento, logo é feature, não refactor". O que este adendo fez foi **dizer a verdade sobre
ele**, e a docstring foi ampliada com o segundo caminho, não reescrita.

E há um argumento para **não** corrigir, que a medição sustenta: casar esses nomes significa
casá-los por um único sobrenome comum (`Lima`, `Souza`, `Melo`, `Santana`) — exatamente o falso
positivo por homônimo que o tratamento `[Homônimo - Ixxxxxxx]` existe para reduzir. A decisão é do
operador, e precisa ser deliberada.

## Um teste caiu, e a correção foi estreitá-lo

`tests/test_dna_analysis.py::test_anti_false_positive` (`TT-04`) afirmava
`"não" in motivo or "sem" in motivo`. O motivo novo — `nenhum sobrenome do nome existe no GEDCOM`
— não contém nenhuma das duas, e o teste acusou **um filtro anti-falso-positivo que não foi
perdido**. Mesmo caso do `accept` no adendo `021`: proxy de texto não é prova de comportamento.

A correção foi trocar o proxy pela pergunta real — "veio um motivo do catálogo?" — com os motivos
nomeados numa constante e o motivo de score (o único dinâmico) conferido por prefixo. A asserção
não foi apagada nem afrouxada.

A tabela `DECISOES` ganhou **5 casos**: `A CF` e `*Roger S` prendem a causa do sobrenome curto;
`Marcos Antonio de Melo` e `*Coutinho Neto` prendem os dois caminhos do sobrenome lido como
prenome; `PAULO` prende o nome único que **não** perdeu sobrenome nenhum.

## Verificação

| | |
|---|---|
| Decisões na árvore real | **idênticas**: 8 cartões e 448 descartes na V2; 90 e 366 na unificada |
| Replicação instrumentada de `matching.py` | **0 divergências** em 456 grupos (aceita/recusa e texto do motivo) |
| `tests/test_characterization_matching.py` | 29 passou (eram 24; +5 casos novos na tabela `DECISOES`) |
| Suíte completa | **1046 passou, 9 pulados, exit 0** — ver o resíduo 4 sobre a instabilidade das rodadas anteriores |
| Servidor no ar | responde com os motivos novos e **0** ocorrências do antigo — medido ponta a ponta por HTTP, pelo caminho real da tela (`_reversa_bugs/_sondas-matching/servidor_motivos.py`) |
| `SHA_DA_TELA` | não muda — a tela de entrada não carrega motivo |

## Resíduo declarado

1. **O defeito estrutural NÃO foi corrigido, por decisão.** Os 84 grupos sem sobrenome nenhum
   (68 + 16) continuam inalcançáveis por qualquer valor de cM: com `inter_cnt` sempre 0, os seis
   ramos exigem `inter_cnt >= 1` ou `>= 2`, e a única porta que sobra é o casamento exato do nome
   inteiro. Na árvore V2, **1** dos 87 grupos sem sobrenome utilizável entrou por essa porta
   (`Maria Pacheco`); os outros 86 foram descartados. Isso é agora **legível na tela**, que era o
   objetivo deste adendo — não deixa de ser verdade.
2. **As âncoras do legado continuam descrevendo o texto antigo.** `contracts.md`, `design.md` e
   `flowcharts/analise-dna.md` são a reconstrução do legado, e o legado dizia aquilo. Este adendo é
   a emenda; reescrever as âncoras falsificaria a reconstrução. Se o projeto quiser o catálogo
   atualizado nos três, é ato separado.
3. **A outra mensagem enganosa continua de pé.** O motivo de score diz *"score insuficiente **ou**
   conflito de sobrenome"* e nunca diz qual das duas. Medido: em **100%** dos 325 descartes com
   esse motivo na árvore V2, o mínimo de interseção de sobrenomes foi cumprido — a metade "conflito
   de sobrenome" nunca é a causa literal. E existe ainda um **sétimo portão** (a penalidade de token
   do meio), que não aparece em número nenhum da mensagem: 3 grupos na V2 e 10 na unificada foram
   vetados por ele com todos os números visíveis suficientes. Não implementado aqui porque não foi
   pedido.
4. **A árvore foi editada por outra sessão durante esta rodada, e as rodadas da suíte não são
   comparáveis entre si.** Enquanto esta medição corria, outra sessão gravou `.gitignore`
   (03:21), `src/app.py` (03:27), `src/templates/index.html` (03:27),
   `tests/test_tabela_da_tela.py` (03:28) e `tests/test_guardas_do_armazenamento.py` (03:40).
   **Não toquei em nenhum desses arquivos.** Quatro rodadas da suíte deram quatro resultados
   diferentes — 17 falhas, 2 falhas, 2 erros, e por fim **0** —, e o número de testes aprovados
   subiu de 1005 para 1046 ao longo delas, porque a outra sessão acrescentava testes enquanto as
   rodadas corriam. Toda falha ou erro reportado passou quando rodado isolado, e nenhum
   dos testes envolvidos lê o motivo (`test_estilo_da_tela` confere a folha de estilo;
   `test_profundidade_do_caminho`, a profundidade). A leitura registrada é **instabilidade por
   edição concorrente**, e não efeito desta mudança — mas fica declarado, porque um número de
   suíte só vale junto com o estado da árvore em que foi medido.

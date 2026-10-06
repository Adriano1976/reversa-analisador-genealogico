# User Stories — Fluxo `analise-dna`

> Re-extração de **2026-10-05** (nível **Completo**). Artefato novo: o nível `essencial` não o gerava.
> Persona única do sistema. Fontes: `analise-dna/requirements.md`, `analise-dna/design.md`, `domain.md` §2 e §3, `state-machines.md` §3, `adrs/14`, `adrs/15`
> Escala de confiança: 🟢 CONFIRMADO | 🟡 INFERIDO | 🔴 LACUNA

---

## Persona

**Genealogista Genético**, com a árvore carregada e sem autenticação. Tem o CSV de matches de DNA exportado do GEDmatch (ou similar) e quer saber **quais daqueles matches fazem sentido dentro da árvore** — e onde a genética e o documento **discordam**. 🟢

## História principal

> **Como** genealogista genético, **quero** cruzar minha lista de matches de DNA com a minha árvore GEDCOM **para que** eu saiba quais matches têm respaldo documental, quais são apenas pistas e quais entram em conflito com o que a árvore afirma.

**A regra que define o produto:** o DNA **não** determina parentesco, e o cM **nunca** é usado sozinho para afirmar vínculo. O resultado nunca é "o parentesco é X porque o cM é Y" — é **três coisas separadas** mais um confronto entre elas. 🟢

## Histórias

### US-D-01 — Ver os três eixos lado a lado, sem mistura

> **Como** genealogista, **quero** ver, para cada match, **o que o GEDCOM afirma**, **o que o DNA informa** e **se os dois são compatíveis** — em blocos separados **para que** eu saiba qual parte é documento e qual é genética.

#### Critérios de aceite

```gherkin
Dado uma árvore carregada e um CSV de matches válido
Quando submeto a análise informando meu nome como raiz
Então cada conexão traz quatro blocos distintos: parentesco documental, evidência genética, possibilidades e confronto
E o cM exibido é o do kit, nunca a soma de kits diferentes
E o bloco documental NÃO menciona cM
E a mensagem final informa quantas conexões foram encontradas e quantas descartadas
```

### US-D-02 — O veredito do confronto, com o porquê

> **Como** genealogista, **quero** um veredito claro por conexão — compatível, possível, conflitante ou inconclusivo — **acompanhado do motivo** **para que** eu saiba o que investigar.

#### Critérios de aceite

```gherkin
Dado um cM dentro da faixa esperada para o parentesco documental
Quando o confronto é calculado
Então o estado é COMPATIVEL
E a tela informa a faixa esperada e a relação publicada usada como referência

Dado um cM fora da faixa, mas com alguma relação publicada cuja faixa se sobrepõe à documental
Quando o confronto é calculado
Então o estado é POSSIVEL
E a tela diz qual relação vizinha acomoda o valor e por que o cM não separa as duas leituras

Dado um cM fora da faixa, sem nenhuma relação publicada que se sobreponha
Quando o confronto é calculado
Então o estado é CONFLITANTE
E a tela apresenta o rol de causas possíveis a considerar

Dado que não há faixa publicada para o parentesco documental
Quando o confronto é calculado
Então o estado é INCONCLUSIVO
E a tela informa que o parentesco documental segue registrado, mas não é confrontável
```

### US-D-03 — Nenhum número é inventado

> **Como** genealogista, **quero** que, quando a fonte não publica dados para uma relação, o sistema **diga isso** em vez de estimar **para que** eu não tome um palpite por medição.

#### Critérios de aceite

```gherkin
Dado um parentesco documental cuja relação não é publicada na versão 4.0 da fonte
Quando a janela esperada é determinada
Então o sistema usa a envoltória das relações publicadas com o mesmo número de meioses
E informa explicitamente qual referência foi usada

Dado um parentesco documental sem relação publicada e sem relação de mesmo número de meioses
Quando o confronto é calculado
Então o estado é INCONCLUSIVO
E nenhum valor de faixa é apresentado
```

### US-D-04 — Vários kits do mesmo nome não são somados

> **Como** genealogista, **quero** que dois testes da mesma pessoa em laboratórios diferentes **não** sejam somados **para que** o cM não seja inflado artificialmente.

#### Critérios de aceite

```gherkin
Dado um CSV em que o mesmo nome aparece em dois kits diferentes
Quando a evidência genética é construída
Então existem DUAS evidências, uma por kit
E o total de cM da pessoa é indeterminado, porque não se sabe qual kit é a pessoa do GEDCOM
E a tela informa que há mais de um kit
E o estado final do confronto é o mais conservador entre os kits
E a tela mostra o estado de cada kit separadamente
```

### US-D-05 — Ver os descartes, com motivo

> **Como** genealogista, **quero** ver quais matches **não** entraram e **por quê** **para que** eu confie que a lista foi filtrada por critério, e não truncada.

#### Critérios de aceite

```gherkin
Dado um match cujo nome não corresponde a ninguém na árvore
Quando a análise termina
Então o match aparece na lista de descartados com o motivo registrado
E a contagem final de descartados o inclui

Dado um match com sobrenomes sem nenhuma interseção e sem sufixo coincidente
Quando a análise termina
Então o motivo é "sem sobrenome em comum (filtro anti-falso-positivo)"

Dado um match que casa mas não tem caminho documental
Quando a análise termina
Então ele NÃO é descartado
E aparece no resultado com o confronto INCONCLUSIVO
```

### US-D-06 — Ler o CSV como ele veio, sem eu ter de ajustá-lo

> **Como** genealogista, **quero** que o sistema leia o CSV **como o exportador o gerou** — com ponto e vírgula, com linhas de título, em latin-1 — **e me diga o que descartou** **para que** eu não precise editar o arquivo à mão.

#### Critérios de aceite

```gherkin
Dado um CSV com separador ponto e vírgula, em latin-1 e com 3 linhas de título
Quando a análise é executada
Então o separador é detectado como ponto e vírgula
E o encoding usado é latin-1
E o cabeçalho é localizado na linha 4
E a tela informa as linhas de preâmbulo ignoradas

Dado um CSV com 2 linhas com número de campos diferente do cabeçalho
Quando a análise é executada
Então a análise prossegue com as demais linhas
E a tela informa quantas linhas foram descartadas e quais

Dado um arquivo que não é a lista de matches
Quando a análise é executada
Então a mensagem diz o separador usado, as colunas encontradas e o que conferir
```

### US-D-07 — Homônimos e DNA

> **Como** genealogista, **quero** ser avisado quando o match pode corresponder a mais de um registro **para que** eu confira antes de aceitar qualquer conclusão.

#### Critérios de aceite

```gherkin
Dado que o nome do match corresponde a mais de um registro do GEDCOM
Quando o confronto é calculado
Então o estado é INCONCLUSIVO
E os registros homônimos são listados para conferência
E o texto explica que sem saber a qual registro o match corresponde a comparação não conclui

Dado que o nome informado como raiz corresponde a mais de um registro
Quando a análise começa
Então o sistema usa o primeiro e avisa quantos e quais são
```

### US-D-08 — Segmento fraco é sinalizado

> **Como** genealogista, **quero** saber quando o maior segmento compartilhado é pequeno **para que** eu trate aquele match com cautela.

#### Critérios de aceite

```gherkin
Dado um match cujo maior segmento é de 12 cM
Quando a evidência é construída
Então a evidência é marcada como segmento fraco
E um aviso é emitido
E o aviso deixa claro que o limite é critério do projeto, e não da fonte
```

### US-D-09 — Erro de entrada não derruba a análise

> **Como** genealogista, **quero** que um CSV sem as colunas necessárias, ou um nome de raiz errado, me digam o que houve **para que** eu corrija e tente de novo.

#### Critérios de aceite

```gherkin
Dado um nome de raiz que não existe na árvore
Quando submeto a análise
Então a tela exibe "Ocorreu um erro: Seu nome 'X' não foi encontrado no GEDCOM."
E nenhum resultado parcial é exibido

Dado um CSV sem a coluna de cM
Quando submeto a análise
Então a tela exibe um erro acionável dizendo o separador usado e as colunas encontradas
E a aplicação não quebra
```

## O que o usuário **não** recebe — e por quê

| Ausência | Motivo | Conf. |
| --- | --- | --- |
| "Relacionamento provável (DNA)" | O rótulo foi **removido** de propósito: um número não afirma parentesco. O que existe é "Possibilidades de parentesco pelo DNA" | 🟢 |
| Mediana das faixas | A fonte **não publica** mediana; inventá-la seria fabricar dado | 🟢 |
| Correção para endogamia ou colapso de pedigree | A fonte declara não atender esses casos. O colapso é **avisado**, mas não altera o veredito | 🟡 |
| Faixas para as relações mais distantes | Não são publicadas na versão 4.0; usa-se envoltória por meioses, ou o estado fica inconclusivo | 🟡 |
| Resultado reprodutível no desempate de nomes | ✅ **CORRIGIDO em 2026-10-05** — com empate exato nos três critérios, vence o **menor `xref_id`**, de forma estável entre execuções | 🟢 |
| Histórico de análises | Nada é persistido | 🔴 |

## Lacunas que afetam esta história 🔴

- **`L-15` / `RF-26`:** o determinismo do desempate foi **decidido** pelo usuário e **não está implementado**. É a única decisão humana vigente que o código viola.
- **`L-14`:** a origem empírica do valor 0,33 no relaxamento de Jaccard continua sem medição registrada.
- **`L-17`:** endogamia e colapso não entram na decisão do estado.
- **`L-19`:** a divergência de `RapidFuzz` entre o pin e o ambiente pode mudar o matching sem mudar código.
- **`E-03`:** a sentinela `SEM-KIT` pode colidir com um kit homônimo.

---

*Gerado pelo Reversa-Writer em 2026-10-05 (re-extração, nível completo).*

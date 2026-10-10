# User Stories — Fluxo `analise-dna`

> Re-extração de **2026-10-10** (nível **Completo**). Substitui a versão de 2026-10-05, que dizia que **nada era persistido** e listava o determinismo do desempate como decisão **não implementada** (`L-15`).
> Persona única do sistema. Fontes: `analise-dna/requirements.md`, `analise-dna/design.md`, `analise-dna/contracts.md`, `domain.md` §2 e §3, `state-machines.md` §3, `adrs/` 14, 15, 27, 33
> Escala de confiança: 🟢 CONFIRMADO | 🟡 INFERIDO | 🔴 LACUNA

---

## Persona

**Genealogista Genético**, com a árvore carregada e sem autenticação. Tem o CSV de matches de DNA exportado do GEDmatch (ou similar) e quer saber **quais daqueles matches fazem sentido dentro da árvore** — e onde a genética e o documento **discordam**. 🟢

## História principal

> **Como** genealogista genético, **quero** cruzar minha lista de matches de DNA com minha árvore GEDCOM **para que** eu saiba quais matches têm respaldo documental, quais são apenas pistas e quais entram em conflito com o que a árvore afirma.

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

> 🟢 **`INCONCLUSIVO` é o estado inicial de todo resultado** — as guardas retornam sem alterá-lo. Nenhum estado é afirmado por omissão.

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

> 🟡 **Isto atinge o caso real deste repositório:** as seis relações **não publicadas** (`1C4R`, `1C5R`, `1C6R`, `3C2R` e os bisavôs distantes) são justamente as **mais distantes**, que é onde a árvore do operador cai.

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

> 🟡 **A ordem de conservadorismo tem uma consequência declarada:** `INCONCLUSIVO` é o **último** da lista, então um kit **sem cM utilizável** não rebaixa o resultado quando outro kit é `COMPATIVEL`. A ausência de dado nunca protege contra uma conclusão otimista de outro kit.

### US-D-05 — Ver os descartes, com motivo acionável

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

> 🟢 **O motivo é a informação, não o rótulo.** O descarte mais informativo carrega os **quatro números** da decisão (`given`, `final`, `inter`, `jacc`) justamente para o operador julgar caso a caso. Encurtá-lo destrói a utilidade da lista.

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

### US-D-07 — Escolher um CSV já guardado, sem enviar de novo

> **Como** genealogista, **quero** escolher um relatório de matches que **já está** na lista **para que** eu não precise procurá-lo no disco e enviá-lo outra vez.

#### Critérios de aceite

```gherkin
Dado um relatório de matches já guardado
Quando escolho esse relatório no formulário da análise
Então a análise usa o arquivo escolhido
E ele tem precedência sobre qualquer arquivo enviado no mesmo formulário

Dado que escolho um relatório que já não está na pasta
Quando submeto a análise
Então a tela diz "Erro: Arquivo 'X' não existe mais."
E a tela continua utilizável

Dado que envio um relatório com o MESMO nome e conteúdo novo
Quando a análise termina
Então a lista passa a ter uma linha com aquele nome
E o aviso de substituição é acrescentado DEPOIS da mensagem do resultado, sem substituí-la
```

### US-D-08 — Homônimos e DNA

> **Como** genealogista, **quero** ser avisado quando o match pode corresponder a mais de um registro **para que** eu confira antes de aceitar qualquer conclusão.

#### Critérios de aceite

```gherkin
Dado que o nome do match corresponde a mais de um registro do GEDCOM
Quando o confronto é calculado
Então o estado é INCONCLUSIVO
E os registros homônimos são listados para conferência

Dado que o nome informado como raiz corresponde a mais de um registro
Quando a análise começa
Então o sistema usa o primeiro e avisa quantos e quais são
```

### US-D-09 — Segmento fraco é sinalizado

> **Como** genealogista, **quero** saber quando o maior segmento compartilhado é pequeno **para que** eu trate aquele match com cautela.

#### Critérios de aceite

```gherkin
Dado um match cujo maior segmento é de 12 cM
Quando a evidência é construída
Então a evidência é marcada como segmento fraco
E um aviso é emitido
E o aviso deixa claro que o limite é critério do projeto, e não da fonte
```

### US-D-10 — O mesmo resultado, sempre

> **Como** genealogista, **quero** que a mesma análise produza **o mesmo resultado** entre execuções **para que** eu possa confiar no que li ontem.

#### Critérios de aceite

```gherkin
Dado um match cujo nome empata com dois registros nos três critérios de semelhança
Quando a análise é repetida, com os candidatos em ordem diferente
Então o registro escolhido é SEMPRE o mesmo
E o resultado não muda entre execuções
```

> 🟢 **Esta história começou como uma divergência viva e fechou nesta rodada.** O desempate passou a ter um **quarto critério** — o **menor `xref_id`** — e o comportamento está congelado por teste nas **duas** ordens de *pool*.

### US-D-11 — O histórico não pode me impedir de ver o resultado

> **Como** genealogista, **quero** que a análise apareça **independentemente** de o histórico ter sido gravado **para que** uma falha de banco não me custe o trabalho.

#### Critérios de aceite

```gherkin
Dado que o banco de dados está indisponível e a variável de conexão está definida
Quando submeto a análise
Então o resultado completo chega à tela
E uma faixa avisa que o histórico não foi registrado
E nada impede a leitura do resultado

Dado que o banco não está configurado
Quando submeto a análise
Então nada muda na tela — o aviso é nulo e não renderiza nada
```

> 🟢 **A regra vale para as duas metades:** exceção na preparação dos dados **ou** na gravação vira **aviso**, nunca interrupção. Uma falha ali seria a persistência bloqueando a análise — exatamente o que ela não pode.

### US-D-12 — Erro de entrada não derruba a análise

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
| Correção para endogamia ou colapso de pedigree | A fonte declara não atender esses casos. O colapso é **avisado**, mas não altera o veredito | 🔴 |
| Faixas para as relações mais distantes | Não são publicadas na versão 4.0; usa-se envoltória por meioses, ou o estado fica inconclusivo | 🔴 |
| Resultado reprodutível no desempate de nomes | ✅ **IMPLEMENTADO** — com empate exato nos três critérios, vence o **menor `xref_id`**, de forma estável entre execuções | 🟢 |
| Retenção, expurgo ou consentimento do histórico | 🔴 **O histórico guarda nome, sexo, nascimento, local e falecimento de pessoas vivas**, sem prazo e sem base legal registrada | 🔴 |
| Garantia de que a gravação funciona | 🔴 Não há teste do caminho feliz de gravação: o driver do banco não está no interpretador oficial da suíte | 🔴 |

## Lacunas que afetam esta história 🔴

- **`L-29` / `P-07`:** o histórico persiste **dado pessoal de pessoas vivas** sem retenção, expurgo ou consentimento. **Bloqueante** para uso real com dado de terceiros.
- **`L-28` / `X-05`:** não há teste de caminho feliz de gravação — erro de SQL, de ordem de chave estrangeira ou de tipo só apareceria dentro do contêiner.
- **`L-17`:** endogamia e colapso não entram na decisão do estado; o cM lido é um teto otimista nesses casos.
- **`L-24` / `E-05`:** esta unit **consome** o dossiê de homônimos alimentado pelo cache de nomes compartilhado — e a chave desse cache **pode não invalidar** entre duas árvores.
- **`E-03`:** a sentinela `" SEM-KIT"` pode colidir com um kit homônimo.
- ✅ **`L-15` / `RF-26` fechada em 2026-10-05:** o determinismo do desempate está **implementado e congelado por teste**.
- ✅ **`L-14` fechada em 2026-10-05:** o valor `0,33` do relaxamento de Jaccard foi declarado **heurística ajustável**, e não número calibrado.
- ✅ **Superada:** a afirmação de que "nada é persistido" — a feature 008 passou a gravar o histórico, opcionalmente.

---

*Gerado pelo Reversa-Writer em 2026-10-10 (re-extração). Substitui a versão de 2026-10-05.*

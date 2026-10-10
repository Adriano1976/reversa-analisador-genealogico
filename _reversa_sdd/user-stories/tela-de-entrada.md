# User Stories — Fluxo `tela-de-entrada`

> Re-extração de **2026-10-10** (nível **Completo**). Artefato **novo** — nasceu com a unit, que não existia em nenhuma extração anterior.
> Persona única do sistema. Fontes: `tela-de-entrada/requirements.md`, `tela-de-entrada/design.md`, `tela-de-entrada/contracts.md`, `permissions.md`, `adrs/` 25, 30, 32
> Escala de confiança: 🟢 CONFIRMADO | 🟡 INFERIDO | 🔴 LACUNA

---

## Persona

**Genealogista Genético**, que trabalha sozinho na própria máquina e **não faz login**. Antes de qualquer análise, ele precisa responder a uma pergunta prática: **o que eu já tenho guardado aqui?** 🟢

## História principal

> **Como** genealogista, **quero** abrir a tela e **ver imediatamente** as árvores e os relatórios que já estão armazenados **para que** eu escolha com o que trabalhar sem precisar procurar arquivos na pasta.

**Valor de negócio:** é a superfície de **escolha** do sistema. Sem ela, o único caminho para usar um arquivo já guardado seria enviá-lo de novo. 🟢

**A regra que define o fluxo:** as listas aparecem **sempre**, em toda renderização, e **nada é escondido** — o arquivo que a referência não alcança aparece **marcado, com o motivo**, em vez de desaparecer. 🟢

## Histórias

### US-T-01 — A lista está lá antes de eu enviar nada

> **Como** genealogista, **quero** ver o que já está guardado na primeira vez que abro a tela **para que** eu não precise enviar um arquivo para descobrir o que existe.

#### Critérios de aceite

```gherkin
Dado que a pasta de upload tem árvores e relatórios guardados
Quando abro GET /
Então as duas abas aparecem com suas listas já preenchidas
E nenhum envio foi necessário

Dado que a pasta está vazia
Quando abro GET /
Então cada aba mostra um estado vazio próprio
E a aba de DNA explica que o relatório entra pela análise, e não por envio
```

### US-T-02 — Um arquivo, uma linha

> **Como** genealogista, **quero** que a mesma árvore enviada duas vezes apareça **uma vez só** **para que** a lista não vire um histórico de versões ilegível.

#### Critérios de aceite

```gherkin
Dado dois arquivos com o mesmo conteúdo guardados na pasta
Quando a lista é montada
Então eles aparecem como UM item
E a quantidade exibida é 2
E o tamanho exibido é a soma dos dois

Dado um arquivo guardado antes da chave por conteúdo, sem os 16 hexadecimais
Quando a lista é montada
Então ele aparece como item próprio
E nunca é agrupado com outro
```

### US-T-03 — A chave de conteúdo não aparece para mim

> **Como** genealogista, **quero** ver o **nome** do arquivo, e não um identificador técnico **para que** eu reconheça o que escolhi.

#### Critérios de aceite

```gherkin
Dado um arquivo guardado como "94e2402671702cac__Famílias_Sergipanas.csv"
Quando a lista é montada
Então o rótulo exibido é "Famílias Sergipanas"
E nenhum rótulo da tela contém 16 hexadecimais seguidos de dois underscores

Dado um arquivo chamado "planilha.csv.ged"
Quando a lista é montada
Então o rótulo é "planilha csv"
E o arquivo aparece na aba de árvores, porque o nome termina em .ged
```

### US-T-04 — O arquivo que não posso abrir continua visível, e diz por quê

> **Como** genealogista, **quero** ver os arquivos que a aplicação **não consegue** abrir e saber o motivo **para que** eu possa tirá-los da lista em vez de procurá-los em vão.

#### Critérios de aceite

```gherkin
Dado um arquivo sem chave de conteúdo no nome
Quando a lista é montada
Então ele aparece marcado, com o motivo "sem chave de conteúdo no nome"
E o botão "Apagar" está disponível para ele
E o botão "Abrir" NÃO está

Dado um arquivo que a referência alcança
Quando a lista é montada
Então ele aparece disponível, e os dois botões estão disponíveis
```

> 🟢 **Esconder o inalcançável tiraria do operador justamente o arquivo que ele mais quer aposentar.** Os dois botões têm regras opostas de propósito: "Abrir" só no disponível; "Apagar" em **todo** item, inclusive no indisponível.

### US-T-05 — Escolher uma árvore com um clique

> **Como** genealogista, **quero** clicar numa árvore da lista e passar a trabalhar nela **para que** eu não precise enviá-la de novo.

#### Critérios de aceite

```gherkin
Dado um item disponível na aba de árvores
Quando clico em "Abrir"
Então a tela mostra "Árvore aberta: ROTULO"
E os formulários das outras abas passam a operar sobre essa árvore
E o estado é o MESMO que um envio produziria
```

> 🟢 **Este ramo existe por causa de um defeito medido em 2026-10-09:** sem ele, o clique caía no `return` final da rota, que renderiza a tela **sem** a árvore resolvida — o operador clicava e nada acontecia.

### US-T-06 — Apagar que não apaga

> **Como** genealogista, **quero** tirar um arquivo da lista **sem** perdê-lo **para que** eu possa desfazer a decisão se ela estiver errada.

#### Critérios de aceite

```gherkin
Dado um arquivo na lista
Quando clico em "Apagar" e confirmo
Então a tela diz "'ROTULO' saiu da lista. O arquivo não foi apagado: ele continua guardado, inteiro, na pasta de aposentados."
E o arquivo sai da lista
E ele continua no disco, com o mesmo nome

Dado que tento apagar um arquivo que já não está na pasta
Quando a ação é processada
Então a tela diz "Não foi possível aposentar o arquivo: ele não está mais na pasta."
E nada é movido

Dado que apago a árvore que está aberta no momento
Quando a ação é processada
Então a tela confirma o sucesso
E NÃO diz que o arquivo não existe mais
```

> 🟢 **A ordem dos ramos é a regra, e o último cenário é a prova dela.** A aposentadoria é tratada **antes** de a árvore do formulário ser resolvida e parseada. Se viesse depois, o operador veria "arquivo não existe mais" sobre uma ação que **deu certo**.

> ⚠️ **A palavra do botão e a palavra da mensagem discordam de propósito.** O botão diz **Apagar** porque é isso que o operador reconhece; a mensagem diz que **não foi apagado** porque é isso que aconteceu. A confirmação do navegador carrega as duas informações na mesma frase, e é o único aviso **antes** do efeito.

### US-T-07 — "Enviado em" é de onde vem a data

> **Como** genealogista, **quero** distinguir dois arquivos de mesmo nome **para que** eu escolha o certo.

#### Critérios de aceite

```gherkin
Dado três arquivos com o mesmo nome exibido e datas diferentes
Quando a lista é montada
Então os três aparecem como itens distintos
E a coluna "Enviado em" distingue um do outro
E a ordem é da data mais recente para a mais antiga

Dado um arquivo cuja data o sistema não consegue converter
Quando a lista é montada
Então a célula de data aparece vazia
E a tela continua funcionando
```

## Fluxo resumido

1. Abre `/` e recebe as duas abas com as listas. 🟢
2. Confere o que está guardado, com nome legível, tamanho e data. 🟢
3. Escolhe uma árvore em "Abrir", ou envia uma nova pelo formulário da aba. 🟢
4. Se algum arquivo estiver atrapalhando, "Apagar" o tira da lista — e ele continua no disco. 🟢

## O que o usuário **não** recebe — e por quê

| Ausência | Motivo | Conf. |
| --- | --- | --- |
| Identificador público de árvore | A aplicação **não tem** um, e a chave de conteúdo **não pode** ocupar esse lugar — ela é exatamente o que não deve aparecer | 🟢 |
| Botão "Abrir" na aba de DNA | Não existe ação que carregue um CSV sozinho: o relatório entra pela análise de DNA, que exige uma árvore. Oferecer "Abrir" prometeria o que a rota não atende | 🟢 |
| Formulário de envio na aba de DNA | Mesma razão: não há ação que guarde um CSV sozinho | 🟢 |
| Filtro por nome, extensão ou forma da chave | Decisão: filtrar esconderia do operador um arquivo que existe. **A pasta é a superfície de confiança da tela** | 🔴 |
| Botão para desfazer a aposentadoria | Desfazer é mover o arquivo de volta, à mão. Não há ação na tela | 🔴 |
| Qualquer registro de quem apagou o quê | Nada é registrado: uma tentativa de aposentar não deixa rastro no servidor | 🔴 |

## Lacunas que afetam esta história 🔴

- **`L-30`:** o motivo "fora da forma" (`nome com caractere que a referência não aceita`) ficou **praticamente inalcançável** depois de 2026-10-10 — ele foi escrito para o acento e o espaço, que agora **passam**. O ramo do template continua correto; o que mudou é a probabilidade de aparecer. **Requer decisão humana.**
- **`L-31`:** a disponibilidade do item é a do **representante** do grupo. Num grupo cujos membros têm nomes visíveis diferentes, nada garante que a elegibilidade seja a mesma para todos.
- **`L-32`:** a quantidade conta **arquivos**, não versões úteis.
- **A listagem não filtra nada, por decisão** — um arquivo colocado na pasta por fora da aplicação aparece listado, e os **nomes** de tudo o que está lá ficam visíveis para qualquer cliente que alcance a porta, porque a aplicação **não tem autenticação**.
- **`_arvore_do_formulario` é um guarda-chuva compartilhado** por três units, e vive dentro de `app.py`, sem dono declarado.

---

*Gerado pelo Reversa-Writer em 2026-10-10 (re-extração). Unit nova.*

# Requirements: Escolher arquivo da lista

> Identificador: `011-escolher-arquivo-da-lista`
> Data: `2026-10-09`
> Pasta da extração reversa: `_reversa_sdd/`
> Confidência: 🟢 CONFIRMADO, 🟡 INFERIDO, 🔴 LACUNA / DÚVIDA

## 1. Resumo executivo

Hoje o operador só consegue usar uma árvore enviando o arquivo de novo: a tela de entrada pede a árvore
genealógica em formato GEDCOM antes de mostrar qualquer outra coisa, e o relatório de matches em CSV
(valores separados por vírgula) é enviado junto de **cada** análise. Esta feature troca isso por uma
**lista do que já está armazenado**: a aba "Buscar Conexão no GEDCOM" passa a mostrar as árvores
disponíveis e a aba "Analisador de DNA" passa a mostrar os relatórios de CSV disponíveis, e o operador
escolhe qual usar — ou envia um novo pela própria aba. A lista é por **conteúdo**, não por arquivo, mas a
medição de 2026-10-09 mostra que **o agrupamento não é o que limpa a lista**: dos 16 arquivos com extensão
`.ged`, o agrupamento por conteúdo reduz a **15 itens**, porque nove deles são sondas e fixtures de
instrumento com conteúdos diferentes entre si. O ganho real de legibilidade vem de outra entrega — o
expurgo do resíduo, que leva a aba de árvore de **16 para 7 arquivos** e a de DNA de **19 para 10**.
Nada é apagado, renomeado ou alterado por esta feature.

## 2. Contexto a partir do legado

| Fonte | Trecho relevante | Confidência |
|-------|------------------|-------------|
| `_reversa_sdd/upload-gedcom/contracts.md#2.1` | O nome no disco é `<16 hexadecimais>__<nome visível>`, com a chave vinda de `sha256(conteúdo)` — **a chave já está no nome**, então agrupar por conteúdo não exige reler arquivo nenhum | 🟢 |
| `_reversa_sdd/upload-gedcom/contracts.md#3` | A referência devolvida no formulário é o que sustenta a continuidade entre requisições; é o mecanismo que a seleção da árvore vai reusar | 🟢 |
| `_reversa_sdd/upload-gedcom/contracts.md#1.1` | O contrato da requisição: rota única com despacho por `action` e `enctype` de formulário | 🟢 |
| `_reversa_sdd/analise-dna/contracts.md#1.1` | Hoje o CSV entra **na requisição da análise**; escolher de uma lista cria uma referência que precisa viajar entre requisições | 🟢 |
| `_reversa_sdd/user-stories/upload-gedcom.md#us-u-04--continuidade-entre-requisições` | A continuidade é história de usuário declarada, não detalhe de implementação | 🟢 |
| `_reversa_sdd/architecture.md#7` | Dívida 8: "nada é persistido entre requisições" — propriedade deliberada, que esta feature não pode quebrar | 🟢 |
| `_reversa_sdd/inventory.md#4` | A pasta de upload é resolvida por `ANALISADOR_UPLOAD_FOLDER` e é a fonte da lista | 🟢 |
| `_reversa_sdd/screens/golden/SCR-001-initial-upload.html.txt` | A tela de entrada atual — o golden que a mudança do `GET /` invalida | 🟢 |
| `_reversa_forward/010-uploads-fora-do-repositorio/onboarding.md#16` | A pasta canônica está fora do repositório e tem duas cópias idênticas de 36 arquivos | 🟢 |
| Medição desta feature (2026-10-09) | Na pasta canônica: **36 arquivos**, dos quais **19 `.csv`**, **16 `.ged`** e **1 `.xlsx`**. Aplicando a regra de agrupar pela chave do nome: a aba de árvore dá **15 itens para 16 arquivos** e a de DNA dá **19 itens para 19 arquivos** — o agrupamento quase não reduz. Dos 36, **18 são resíduo de instrumento** (9 na aba de árvore, 9 na de DNA), e é a remoção deles que leva as abas a 7 e 10 arquivos. **3 arquivos não têm chave no nome** (`Adriano_Santos.ged`, `Arvore_Unificada_Oficial_V1_2.ged` e `Famílias_Sergipanas.csv`), e o `.xlsx` não aparece em aba nenhuma | 🟢 |

## 3. Personas e cenários de uso

| Persona | Objetivo | Cenário-chave |
|---------|----------|---------------|
| Operador (usuário único, sem login, uso local) | Reaproveitar uma árvore ou um relatório que já enviou, sem procurar o arquivo de novo no disco | Abre a aplicação, escolhe a árvore unificada na lista e roda a busca de conexão — sem enviar arquivo nenhum |
| Operador | Comparar a mesma árvore com dois relatórios de DNA diferentes | Escolhe a árvore, roda a análise com o primeiro CSV da lista e repete com o segundo |
| Operador | Trazer material novo | Envia um GEDCOM pela aba de árvore, sem sair da aba |

## 4. Regras de negócio novas ou alteradas

1. **RN-01:** A lista apresenta **um item por conteúdo**, e o agrupamento usa a chave de 16 hexadecimais já
   embutida no nome armazenado — **sem reler o conteúdo** dos arquivos. 🟢
   - Origem no legado: `_reversa_sdd/upload-gedcom/contracts.md#2.1`
   - Tipo: **nova**
2. **RN-02:** Cada item exibe o **nome visível** do arquivo; havendo mais de um arquivo com o mesmo
   conteúdo, o item declara quantos são. 🟢
   - Origem no legado: `_reversa_sdd/upload-gedcom/contracts.md#2.1` (o nome visível é o que o operador
     reconhece; a chave é o que o sistema usa)
   - Tipo: **nova**
3. **RN-03:** A aba de árvore lista os arquivos cujo nome visível termina em `.ged`, e a aba de DNA os que
   terminam em `.csv`. 🟢
   - Origem no legado: `_reversa_sdd/upload-gedcom/contracts.md#2.1`
   - Tipo: **nova**
4. **RN-04:** A árvore escolhida continua sendo a referência que o formulário devolve entre requisições; o
   CSV escolhido passa a ser **também** uma referência que viaja entre requisições. 🟢
   - Origem no legado: `_reversa_sdd/upload-gedcom/contracts.md#3`, `_reversa_sdd/analise-dna/contracts.md#1.1`
   - Tipo: **alterada** para o CSV (o contrato da árvore não muda)
5. **RN-05:** A lista é lida do disco no momento de renderizar a tela; **nada** é mantido em memória entre
   requisições. 🟢
   - Origem no legado: `_reversa_sdd/architecture.md#7` (dívida 8) — propriedade preservada
   - Tipo: **preservada**
6. **RN-06:** Escolher um arquivo não o altera, não o copia e não cria arquivo novo. 🟢
   - Origem no legado: `_reversa_sdd/upload-gedcom/contracts.md#2.2`
   - Tipo: **preservada**
7. **RN-07:** A aplicação em execução continua **sem** apagar arquivo enviado; nenhuma ação desta feature
   remove, renomeia ou move arquivo. 🟢
   - Origem no legado: `_reversa_sdd/upload-gedcom/contracts.md#2.2`, `_reversa_sdd/state-machines.md#5`
   - Tipo: **preservada** — a remoção pela tela é decisão adiada para outra feature
8. **RN-08:** As ações HTTP existentes (`upload_gedcom`, `path_search`, `dna_analysis`) mantêm nome e
   campos, para a paridade diferencial e os testes de rota continuarem válidos. 🟢
   - Origem no legado: `_reversa_sdd/upload-gedcom/contracts.md#1.1`, `_reversa_sdd/analise-dna/contracts.md#1`
   - Tipo: **preservada**

## 5. Requisitos Funcionais

| ID | Requisito | Prioridade | Critério de aceite | Confidência |
|----|-----------|------------|--------------------|-------------|
| RF-01 | A aba de árvore lista as árvores armazenadas, um item por conteúdo, com nome visível, tamanho e data | Must | Com a pasta medida em 2026-10-09, a aba mostra **15 itens para 16 arquivos** e o item que agrupa declara **2 arquivos**; nenhum arquivo é lido para montar a lista; depois do expurgo do resíduo, a mesma aba mostra **7 arquivos** | 🟢 |
| RF-02 | O operador escolhe a árvore a ser usada, e a escolha é a referência que o formulário devolve | Must | Escolher um item e submeter a busca de caminho conclui, sem novo envio de arquivo | 🟢 |
| RF-03 | A aba de DNA lista os relatórios de CSV armazenados, pelo mesmo critério de agrupamento | Must | A aba mostra um item por conteúdo, com nome visível, tamanho e data; com a pasta medida em 2026-10-09 são **19 itens para 19 arquivos**, e depois do expurgo do resíduo, **10 arquivos** | 🟢 |
| RF-04 | O operador escolhe o CSV a ser usado, e a escolha viaja entre requisições | Must | Duas análises seguidas, com CSVs diferentes escolhidos na lista, concluem sem reenvio de arquivo | 🟢 |
| RF-05 | Cada aba permite enviar um arquivo novo, com o contrato de envio atual preservado | Must | O envio pela aba valida o conteúdo antes de gravar, grava sob chave de conteúdo e passa a listar o arquivo novo | 🟢 |
| RF-06 | A tela de entrada passa a exibir as duas abas com a lista, sem exigir um envio prévio | Must | `GET /` com a pasta povoada renderiza as duas abas com a lista; nenhum arquivo é exigido para chegar até elas | 🟢 |
| RF-07 | Estado vazio: sem arquivo do tipo na pasta, a aba orienta o envio e não falha | Must | Com a pasta vazia, a aba mostra a orientação de envio e responde `200` | 🟢 |
| RF-08 | Nenhuma ação da feature remove, renomeia ou altera arquivo armazenado | Must | Inventário por `sha256` da pasta antes e depois de percorrer todas as telas: idêntico | 🟢 |

## 6. Requisitos Não Funcionais

| Tipo | Requisito | Evidência ou justificativa | Confidência |
|------|-----------|----------------------------|-------------|
| Desempenho | A listagem **não** relê o conteúdo dos arquivos: agrupa pela chave já presente no nome | A pasta medida tem 27,9 MB; reler tudo a cada renderização custaria I/O de hash em uma tela que só mostra nomes. A chave de 16 hexadecimais no nome é a mesma que `sha256(conteúdo)` produziu (`contracts.md#2.1`) | 🟢 |
| Consistência de estado | A aplicação continua sem estado entre requisições; a escolha viaja por campo de formulário, como já faz a árvore. A listagem tolera arquivo que desapareça entre a renderização e o uso: a resposta de "arquivo não existe mais" já existe e a tela tem de continuar utilizável | `_reversa_sdd/architecture.md#7` (dívida 8); `src/app.py` (mensagem de referência que não resolve) | 🟢 |
| Segurança | A lista expõe os nomes dos arquivos no HTML entregue ao navegador. Isso é o **mesmo regime** do contrato atual, que já publica todos os nomes da árvore para os campos de sugestão; a aplicação não tem autenticação e escuta apenas a máquina local por padrão | `README.md`; `_reversa_sdd/permissions.md` | 🟢 |
| Compatibilidade | As três ações HTTP existentes mantêm nome e campos, e a ordem das seções obrigatórias do formulário não muda | Paridade diferencial em 100 % e os testes de rota dependem dessas ações (`RN-08`) | 🟢 |
| Testes | Toda mudança de comportamento chega com teste que falha antes e passa depois | Princípio III de `.reversa/principles.md` | 🟢 |
| Versionamento | Nenhum dado real entra no versionamento, inclusive fixtures da lista, que são sintéticas | Princípio I de `.reversa/principles.md` | 🟢 |
| Natureza da mudança | Isto **não é refactor**: a tela de entrada e o fluxo da análise de DNA mudam de comportamento. O que não muda é o núcleo, que continua recebendo a árvore e o caminho do CSV por parâmetro | Princípio II de `.reversa/principles.md` | 🟢 |
| Documentação | A tela de entrada descrita no `README.md` e o procedimento do `onboarding.md` precisam acompanhar a mudança | `README.md` | 🟢 |

## 7. Critérios de Aceitação

```gherkin
Cenário: escolher a árvore da lista
  Dado que a pasta de upload tem árvores armazenadas
  Quando o operador abre a aplicação
  Então a aba de árvore mostra um item por conteúdo, com nome visível, tamanho e data
  E o operador escolhe uma árvore e submete a busca de caminho
  E a busca conclui sem novo envio de arquivo

Cenário: arquivos idênticos aparecem como um item
  Dado que quatro arquivos armazenados têm o mesmo conteúdo e nomes visíveis iguais
  Quando a lista é renderizada
  Então existe um único item para esse conteúdo
  E esse item declara que são quatro arquivos

Cenário: listar os relatórios de DNA armazenados
  Dado que a pasta tem relatórios de CSV armazenados, incluindo dois com o mesmo conteúdo
  Quando o operador abre a aba de DNA
  Então a aba mostra um item por conteúdo, com nome visível, tamanho e data
  E o item do conteúdo repetido declara quantos arquivos são

Cenário: escolher o CSV da lista e repetir com outro
  Dado que a pasta tem dois relatórios de CSV armazenados
  Quando o operador roda a análise com o primeiro e depois com o segundo, sem enviar arquivo
  Então as duas análises concluem com sucesso

Cenário: enviar um arquivo novo pela aba
  Dado que a aba de árvore está aberta
  Quando o operador envia um GEDCOM novo por ela
  Então o arquivo é validado antes de gravar
  E passa a aparecer na lista

Cenário: pasta vazia
  Dado que a pasta não tem nenhum arquivo do tipo
  Quando a aba é aberta
  Então a tela orienta o envio de um arquivo
  E responde com sucesso, sem erro

Cenário: arquivo escolhido que não é do tipo anunciado (caso negativo)
  Dado que existe um arquivo de conteúdo CSV com nome visível terminando em .ged
  Quando o operador o escolhe na aba de árvore
  Então a aplicação responde com a mensagem de conteúdo não reconhecido
  E nenhuma árvore é carregada

Cenário: nada é apagado nem alterado (guarda de escopo)
  Dado o inventário da pasta por sha256 antes de percorrer as telas
  Quando o operador lista, escolhe e envia arquivos
  Então todos os arquivos preexistentes continuam existindo, com o mesmo sha256
```

## 8. Prioridade MoSCoW

| Item | MoSCoW | Justificativa |
|------|--------|---------------|
| RF-01, RF-03 | Must | A lista é o objeto da feature. O agrupamento por conteúdo é barato (não relê arquivo) e evita a duplicação trivial, mas **não é o que limpa a tela**: medido, ele reduz 16 arquivos a 15 itens. A legibilidade da lista depende do expurgo do resíduo, que é passo do `onboarding.md` da feature 010 |
| RF-02, RF-04 | Must | Escolher é o que evita o reenvio; para o CSV é também o contrato novo |
| RF-05 | Must | Sem o envio pela aba, o operador ficaria preso à lista — e a tela de entrada deixa de existir |
| RF-06 | Must | É a razão de ser: alcançar as abas sem enviar arquivo antes |
| RF-07 | Must | Estado vazio é o primeiro estado de uma instalação nova |
| RF-08 | Must | Guarda de escopo: a remoção pela tela é de outra feature, e nada desta pode tocar arquivo |
| RNF Desempenho | Must | Reler 27,9 MB por renderização transformaria uma tela de nomes em gargalo |
| RNF Documentação | Should | Não bloqueia a entrega, mas a tela de entrada descrita no README deixa de existir |

## 9. Esclarecimentos

> Nenhuma sessão de dúvidas registrada ainda. Rode `/reversa-clarify` quando houver `[DÚVIDA]` pendente.

## 10. Lacunas

- 🔴 [DÚVIDA] **Escopo:** a lista mostra todo arquivo cuja extensão corresponde, sinalizando os que não são
  do tipo, ou valida o conteúdo e desabilita o que não serve? A pasta real tem um caso concreto —
  `Famílias_Sergipanas.csv.ged`, que é um CSV com nome de GEDCOM. Listar apenas com aviso é barato;
  validar o conteúdo na listagem custa leitura de arquivo em toda renderização, que é justamente o que o
  RNF de desempenho evita.
- 🔴 [DÚVIDA] **Experiência:** a escolha é lembrada entre sessões do navegador, ou vale apenas para a
  página aberta? A segunda opção preserva a propriedade "nada é persistido entre requisições"
  (`architecture.md#7`, dívida 8); a primeira introduz estado novo no sistema, com um lugar para guardá-lo
  que hoje não existe.
- 🔴 [DÚVIDA] **Experiência:** a tela de entrada muda — o `GET /` passa a renderizar as duas abas com a
  lista, e o golden `SCR-001-initial-upload.html.txt` deixa de valer, exigindo recaptura. Confirmar que a
  mudança da tela de entrada entra no escopo desta feature, já que a recaptura do golden é custo real.

**Fatos medidos que o plano precisa tratar** — não são dúvidas, são consequências já conhecidas:

- **Três arquivos não têm chave de conteúdo no nome:** `Adriano_Santos.ged`,
  `Arvore_Unificada_Oficial_V1_2.ged` e `Famílias_Sergipanas.csv`. São anteriores à chave por conteúdo, e a
  regra de agrupar pela chave **não os alcança**: cada um vira um item próprio, e a mesma árvore pode
  aparecer duas vezes na lista — uma sem chave, outra com. Agrupá-los de verdade exigiria reler o conteúdo
  (10,6 MB só nas duas árvores), que é exatamente o que o RNF de desempenho evita. Fica declarado o
  trade-off, para o desenho escolher.
- **O mesmo conteúdo aparece em abas diferentes.** A chave `94e2402671702cac` existe como
  `…__Famílias_Sergipanas.csv` **e** como `…__Famílias_Sergipanas.csv.ged`. Como o agrupamento é por aba, a
  duplicação entre abas não é vista. Registrado; resolver isso está fora do escopo.
- **Um arquivo não aparece em aba nenhuma:** `Familias Sergipanas.xlsx`, que nenhum dos dois fluxos
  consome. Ele continua armazenado e invisível, como hoje.

## 11. Histórico de alterações

| Data | Alteração | Autor |
|------|-----------|-------|
| 2026-10-09 | Versão inicial gerada por `/reversa-requirements` | reversa |

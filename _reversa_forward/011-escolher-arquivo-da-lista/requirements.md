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
| `_reversa_sdd/screens/golden/SCR-001-initial-upload.html.txt` | O golden da tela de entrada — **do oráculo legado congelado**, não da aplicação atual. Medido no plano: a mudança do `GET /` **não** o invalida; o que fica é uma divergência declarada | 🟢 |
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
   - Tipo: **preservada** — confirmada na §9: a escolha do operador também **não** sobrevive ao fechamento
     da página
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
9. **RN-09:** A lista seleciona por **extensão do nome visível**, sem ler o conteúdo de arquivo nenhum.
   Arquivo cujo nome anuncia um tipo e cujo conteúdo é outro continua listado, e a recusa acontece **no
   uso**, pela validação de conteúdo que já existe. 🟢
   - Origem no legado: `_reversa_sdd/upload-gedcom/contracts.md#2.1` (a extensão original é preservada no
     nome); a validação de conteúdo é do uso, não da listagem
   - Tipo: **nova** — decidida na §9
10. **RN-10:** Arquivo armazenado **sem** chave de conteúdo no nome vira item próprio, marcado na tela
    como sem chave; ele não é agrupado, e o conteúdo **não** é lido para agrupá-lo. 🟢
    - Origem no legado: `_reversa_sdd/upload-gedcom/contracts.md#2.1` — a chave passou a compor o nome
      depois, e três arquivos são anteriores a isso
    - Tipo: **nova** — decidida na §9
11. **RN-11:** Item cujo arquivo **não pode ser usado por referência** é exibido com a marca de
    **indisponível** e o motivo, e **continua na lista** — ele não é escondido nem filtrado. 🟢
    - Origem no legado: `_reversa_sdd/upload-gedcom/contracts.md#2.1` — quem decide se uma referência
      alcança o arquivo é a **forma fechada do nome** (`utils/validate.py:32`), aplicada pelo resolvedor
      (`ports/adaptadores.py:93`)
    - Tipo: **nova** — decidida na auditoria de 2026-10-09, depois de medida a pasta real: **6 dos 17
      itens** que a lista desenha não podem ser escolhidos, e a resposta a eles hoje é a mensagem
      **falsa** `Erro: Arquivo '…' não existe mais.` (o arquivo existe)

## 5. Requisitos Funcionais

| ID | Requisito | Prioridade | Critério de aceite | Confidência |
|----|-----------|------------|--------------------|-------------|
| RF-01 | A aba de árvore lista as árvores armazenadas, um item por conteúdo, com nome visível, tamanho e data | Must | Antes do expurgo do resíduo a aba mostrava **15 itens para 16 arquivos**; hoje, com o resíduo expurgado, mostra **8 arquivos e 7 itens** — dois compartilham a chave `080e7943572d2652`. Nenhum arquivo é lido para montar a lista (`RN-09`), e os três sem chave aparecem como item próprio marcado (`RN-10`) | 🟢 |
| RF-02 | O operador escolhe a árvore a ser usada, e a escolha é a referência que o formulário devolve | Must | Escolher um item e submeter a busca de caminho conclui, sem novo envio de arquivo | 🟢 |
| RF-03 | A aba de DNA lista os relatórios de CSV armazenados, pelo mesmo critério de agrupamento | Must | A aba mostra um item por conteúdo, com nome visível, tamanho e data; antes do expurgo eram **19 itens para 19 arquivos**, e hoje são **10 arquivos e 10 itens** | 🟢 |
| RF-04 | O operador escolhe o CSV a ser usado, e a escolha viaja entre requisições | Must | Duas análises seguidas, com CSVs diferentes escolhidos na lista, concluem sem reenvio de arquivo | 🟢 |
| RF-05 | Cada aba permite enviar um arquivo novo, com o contrato de envio atual preservado | Must | O envio pela aba valida o conteúdo antes de gravar, grava sob chave de conteúdo e passa a listar o arquivo novo | 🟢 |
| RF-06 | A tela de entrada passa a exibir as duas abas com a lista, sem exigir um envio prévio | Must | `GET /` com a pasta povoada renderiza as duas abas com a lista; nenhum arquivo é exigido para chegar até elas | 🟢 |
| RF-07 | Estado vazio: sem arquivo do tipo na pasta, a aba orienta o envio e não falha | Must | Com a pasta vazia, a aba mostra a orientação de envio e responde `200` | 🟢 |
| RF-08 | Nenhuma ação da feature remove, renomeia ou altera arquivo armazenado | Must | Inventário por `sha256` da pasta antes e depois de percorrer todas as telas: idêntico | 🟢 |
| RF-09 | A lista marca o item cujo arquivo **não pode ser usado por referência**, com o motivo, sem escondê-lo | Must | Medido em 2026-10-09: **3 dos 7 itens** da aba de árvore e **3 dos 10** da de DNA são marcados como indisponíveis, com o motivo, e nenhum arquivo desaparece da lista | 🟢 |

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

Cenário: a tela de entrada mostra as duas abas sem exigir envio
  Dado que a pasta de upload tem arquivos armazenados
  Quando o operador acessa a raiz da aplicação
  Então as duas abas aparecem com as suas listas
  E nenhum arquivo é exigido para chegar até elas
  E a aplicação passa a divergir da tela inicial do legado, e a divergência fica declarada

Cenário: arquivo sem chave de conteúdo aparece marcado
  Dado que a pasta tem um arquivo cujo nome não começa com a chave de 16 hexadecimais
  Quando a lista é renderizada
  Então esse arquivo aparece como item próprio
  E o item declara que ele é anterior à chave por conteúdo
  E nenhum conteúdo é lido para agrupá-lo

Cenário: item indisponível, forçado (caso negativo)
  Dado que a pasta tem um arquivo cujo nome visível tem acento, ou que não tem chave de conteúdo
  Quando o operador força o uso dele, apesar da marca
  Então a aplicação recusa e nenhuma árvore é carregada
  E a tela continua utilizável
  E o arquivo continua na lista

Cenário: arquivo de conteúdo trocado, no envio (caso negativo)
  Dado que o operador envia um arquivo cujo conteúdo não começa com a declaração 0 HEAD
  Quando o envio é submetido
  Então a aplicação responde com a mensagem de conteúdo não reconhecido
  E nada é gravado na pasta

Cenário: nada é apagado nem alterado (guarda de escopo)
  Dado o inventário da pasta por sha256 antes de percorrer as telas
  Quando o operador lista, escolhe e envia arquivos
  Então todos os arquivos preexistentes continuam existindo, com o mesmo sha256

Cenário: item que não pode ser usado por referência aparece marcado
  Dado que a pasta tem um arquivo cujo nome visível tem acento, ou que não tem chave de conteúdo
  Quando a lista é renderizada
  Então esse item aparece marcado como indisponível
  E o item declara o motivo
  E o arquivo continua na lista, sem ser escondido
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
| RN-09 | Must | Decidida na §9: a lista abre sem ler conteúdo, e a recusa do arquivo trocado acontece no uso, onde a validação já existe |
| RN-10 | Must | Decidida na §9: sem a marca de "sem chave", o operador veria dois itens parecidos sem entender por quê |
| RF-09, RN-11 | Must | Decidida na auditoria: sem a marca de indisponível, **6 dos 17 itens** levariam o operador à mensagem **falsa** "não existe mais", e ele concluiria que o arquivo sumiu do disco |

## 9. Esclarecimentos

### Sessão 2026-10-09

- **Q:** Existe arquivo guardado cujo nome termina em `.ged` mas cujo conteúdo é um CSV
  (`Famílias_Sergipanas.csv.ged`). A lista seleciona só pelo nome, ou confere o conteúdo?
  **R:** Só pelo nome. A lista abre **sem ler arquivo nenhum**; o arquivo que anuncia um tipo e entrega
  outro continua listado e é recusado **no uso**, pela validação de conteúdo que já existe
  (`Arquivo não reconhecido como GEDCOM: {motivo}`), sem quebrar nada. Conferir o conteúdo na listagem
  custaria reler 27,9 MB a cada renderização — exatamente o que o RNF de desempenho evita.
- **Q:** Os três arquivos salvos antes de a chave de conteúdo entrar no nome aparecem separados no
  agrupamento. O que fazer com eles?
  **R:** Cada um vira **item próprio**, marcado na tela como sem chave. O agrupamento pela chave não os
  alcança, e **não** haverá leitura de conteúdo para agrupá-los (10,6 MB só nas duas árvores). Efeito
  aceito: a mesma árvore pode aparecer duas vezes — uma sem chave, outra com — e a marca diz qual é qual.
- **Q:** A escolha sobrevive se a página for fechada e reaberta?
  **R:** Não. Vale só para a página aberta. Preserva a propriedade "nada é persistido entre requisições"
  (`architecture.md#7`, dívida 8) e não cria lugar nenhum para guardar preferência.
- **Q:** A tela de entrada (o `GET /`, que hoje exige um envio antes de mostrar qualquer coisa) entra no
  escopo desta feature?
  **R:** Entra. Ela passa a renderizar as duas abas com a lista, e o envio se muda para dentro de cada
  aba. **Correção medida no `/reversa-plan`:** o golden **não** é recapturado — ele captura o **oráculo
  legado congelado** (`legacyOrigin: analisador-genealogico/templates/index.html:41-52`, captura na
  porta do oráculo por `_reversa_sdd/parity/_golden_capture.py`), e um oráculo congelado não deixa de
  valer porque o candidato mudou. O que existe de real é a **divergência**: a aplicação atual deixa de
  ter o estado inicial "envie antes de tudo" que o legado tem, e isso passa a ser declarado
  (`D-05`, `D-06` do roadmap).

## 10. Lacunas

Nenhuma lacuna aberta. As três dúvidas do documento inicial foram resolvidas na sessão de 2026-10-09
(§9); as decisões viraram as regras `RN-09` e `RN-10` (§4) e dois cenários novos (§7).

**Fatos medidos que o plano precisa tratar** — não são dúvidas, são consequências já conhecidas:

- **Três arquivos não têm chave de conteúdo no nome:** `Adriano_Santos.ged`,
  `Arvore_Unificada_Oficial_V1_2.ged` e `Famílias_Sergipanas.csv`. São anteriores à chave por conteúdo, e a
  regra de agrupar pela chave **não os alcança**: cada um vira um item próprio, e a mesma árvore pode
  aparecer duas vezes na lista — uma sem chave, outra com. **Decidido na §9:** item próprio, com marca de
  "sem chave", e sem leitura de conteúdo para agrupá-los.
- **O mesmo conteúdo aparece em abas diferentes.** A chave `94e2402671702cac` existe como
  `…__Famílias_Sergipanas.csv` **e** como `…__Famílias_Sergipanas.csv.ged`. Como o agrupamento é por aba, a
  duplicação entre abas não é vista. Registrado; resolver isso está fora do escopo.
- **Um arquivo não aparece em aba nenhuma:** `Familias Sergipanas.xlsx`, que nenhum dos dois fluxos
  consome. Ele continua armazenado e invisível, como hoje.
- **6 dos 17 itens não podem ser usados por referência** — medido em 2026-10-09, arquivo por arquivo
  (`evidence/_sonda_forma_do_nome.py`): `50a3dd36fea8f8bb__Famílias_Sergipanas.csv`,
  `94e2402671702cac__Famílias_Sergipanas.csv` e `94e2402671702cac__Famílias_Sergipanas.csv.ged` têm
  **acento no nome visível**, que a forma fechada de `utils/validate.py:32` não admite; e os **três sem
  chave** não têm os 16 hexadecimais que a mesma forma exige. Escolher qualquer um deles responde
  `Erro: Arquivo '…' não existe mais.`, que é **falso** — o arquivo está na pasta. **Decidido na
  auditoria:** o item é marcado como indisponível, com o motivo, e o defeito do contrato do nome (o
  gravador preserva acento e o resolvedor o recusa) vira **bug próprio**, fora do escopo desta feature.

## 11. Histórico de alterações

| Data | Alteração | Autor |
|------|-----------|-------|
| 2026-10-09 | Versão inicial gerada por `/reversa-requirements` | reversa |
| 2026-10-09 | Sessão de dúvidas: 4 perguntas respondidas, 3 dúvidas resolvidas; `RN-09` e `RN-10` acrescentadas; 2 cenários novos (§7); contagens de `RF-01` e `RF-03` atualizadas para o estado pós-expurgo | reversa |
| 2026-10-09 | Correção vinda do `/reversa-plan`: a premissa de que o golden `SCR-001` "deixa de valer" era **falsa** — ele captura o oráculo legado congelado. Corrigidos a linha da §2, a resposta da §9 e um cenário da §7; o golden **não** é recapturado, e a divergência da app atual passa a ser declarada | reversa |
| 2026-10-09 | Correção vinda do `/reversa-audit` (`A007`): medido na pasta real que **6 dos 17 itens** não podem ser usados por referência. Acrescentados a `RN-11` (§4), o `RF-09` (§5), um cenário (§7), a linha de MoSCoW (§8) e o fato medido da §10; o defeito do contrato do nome fica registrado como bug próprio, fora do escopo | reversa |

# Requirements: dono no port de armazenamento e linha de base da suíte

> Identificador: `007-dono-no-port-e-baseline`
> Data: `2026-10-07`
> Pasta da extração reversa: `_reversa_sdd/`
> Confidência: 🟢 CONFIRMADO, 🟡 INFERIDO, 🔴 LACUNA / DÚVIDA

## 1. Resumo executivo

A Onda 2 (`006-fronteira-aplicacao-ports`) entregou a fronteira de aplicação, mas deixou
dois desvios declarados fora do escopo. Esta feature fecha os dois.

Antes dos dois: uma **porta** é a interface que a fronteira consome por parâmetro, sem que
o caso de uso instancie a implementação — o armazenamento de arquivo e o repositório de
árvore são as duas portas desta família. O **dono** é a identidade de quem enviou o dado;
nesta onda ele é apenas um parâmetro obrigatório, sem comportamento.

O primeiro desvio é de **contrato**: o port de repositório de árvores recebe a identidade do
dono desde já, e o port de **armazenamento de arquivo** não — uma assimetria que a Onda 3
teria de resolver reabrindo a assinatura da porta e todos os seus chamadores. O dono entra
na assinatura de `guardar` e `resolver` **sem comportamento**: a chave continua derivada do
conteúdo, o caminho continua o mesmo e nada passa a ser isolado por dono.

O segundo é de **verificação**: 15 testes de rota de `tests/test_upload_seguranca.py` nunca
executam nesta máquina, porque a infraestrutura de testes cria o diretório-base temporário
com um modo de permissão que o sistema de arquivos recusa listar, escrever e apagar. Os 15
testes são justamente os da superfície que a Onda 2 reescreveu — e que por isso só pôde ser
verificada por uma sonda construída à mão. Corrigir isso devolve cobertura real à rota e
**recalcula a linha de base da suíte**, que hoje é citada como "178 aprovados, 15 erros de
ambiente" nos artefatos das features 005 e 006.

## 2. Contexto a partir do legado

| Fonte | Trecho relevante | Confidência |
|-------|------------------|-------------|
| `_reversa_sdd/architecture.md#7` | Dívidas #3 e #4: contaminação entre requisições concorrentes e ausência de identidade/isolamento. Ambas continuam **abertas** e não são tratadas aqui | 🟢 |
| `_reversa_sdd/domain.md#3.5` | O contrato de armazenamento: chave derivada do conteúdo (`sha256` truncado), forma fechada `<16 hex>__<nome visível>`, arquivo com a mesma chave não é reescrito, extensão original preservada, teto de 16 MB | 🟢 |
| `_reversa_sdd/domain.md#3.5` | "**É a chave de conteúdo que faz o papel de identificador de sessão**" — não existe sessão, login nem dono no legado | 🟢 |
| `_reversa_sdd/domain.md#5.1` | As dez mensagens da camada de rota, que esta feature **não** pode alterar | 🟢 |
| `_reversa_sdd/permissions.md` | Varredura RBAC: zero papéis, zero sessão, zero autenticação (`P-01` a `P-05`) | 🟢 |
| `_reversa_sdd/migration/cutover_plan.md#Pré-requisitos` | **Onda 3** exige isolamento por usuário provado por teste negativo (`404`, não `403`). É para ela que o dono está sendo preparado | 🟢 |
| `_reversa_sdd/addenda/006-fronteira-aplicacao-ports.md` | Adendo **vigente**: forma das três portas, `D-03` (repositório sem consumidor), `RF-08` (dono obrigatório no repositório), `RN-06` (nenhum isolamento implementado) | 🟢 |
| `_reversa_forward/006-fronteira-aplicacao-ports/evidence/README-evidencias.md#2` | Causa medida dos 15 erros: `os.mkdir(caminho, 0o700)` cria diretório que não pode ser listado nem apagado; o `tmp_path_factory` do pytest usa exatamente esse modo. Inventário de **13 diretórios presos**, 8 deles anteriores à feature 006 | 🟢 |
| `_reversa_forward/006-fronteira-aplicacao-ports/requirements.md#5` | `RF-16` da 006, que registra a linha de base como "**178 aprovados, 0 falhas esperadas, 15 erros de ambiente**" | 🟢 |
| `requirements.txt` | Decisão de 2026-10-05: "o interpretador **oficial** do projeto é o `.venv/`, e não o global". O pin (`ged4py==0.5.5`, `networkx==3.7`, `pandas==3.0.6`) segue o `.venv`; o global tem `0.5.2`/`3.6.1`/`3.0.3`, que são as versões do **manifesto do oráculo** | 🟢 |
| `.reversa/principles.md#II` | Comportamento observável é preservado em refatoração: mudar a assinatura de uma porta não pode mudar comportamento | 🟢 |
| `.reversa/principles.md#III` | Nenhuma mudança sem teste que a cubra | 🟢 |

**Estado medido do código, para dimensionar o delta (não é suposição):**

| Ponto | Hoje |
|---|---|
| `ArmazenamentoDeArquivos.guardar(conteudo, nome_original, tipo)` | **sem** dono (`src/ports/__init__.py`) |
| `ArmazenamentoDeArquivos.resolver(referencia)` | **sem** dono |
| `RepositorioDeArvores.guardar/obter` | **com** dono, obrigatório (`RF-08` da 006) |
| `upload_gedcom(conteudo, nome_original, dono, armazenamento, carregador)` | **já recebe** o dono e **não** o repassa à porta |
| Constante de dono no adaptador de entrada | **já existe** (`DONO_DO_PROCESSO = "unico"`), citada em três pontos de chamada |
| Chamadas a `guardar` no código de produção | **duas** (GEDCOM no caso de uso, CSV na rota) |
| Chamadas a `resolver` no código de produção | **uma** (dentro do carregador de árvores) |

## 3. Personas e cenários de uso

| Persona | Objetivo | Cenário-chave |
|---------|----------|---------------|
| Quem executa a Onda 3 | Encontrar a identidade do dono **já** na assinatura das duas portas, para não reabrir contrato e chamadores | Ao ligar a persistência da Onda 3, nenhuma assinatura de porta precisa mudar |
| Quem mantém a suíte | Ter os testes de rota **executando**, e não pulados por defeito de ambiente | Rodar `pytest` numa máquina limpa e ver os 15 executarem |
| Quem lê os artefatos do ciclo forward | Saber qual é a linha de base **vigente** e qual é histórica | Ao comparar uma medição nova, não comparar contra um número que nunca foi medido de verdade |

## 4. Regras de negócio novas ou alteradas

1. **RN-01:** A identidade do dono passa a ser parâmetro **obrigatório** do port de
   armazenamento de arquivo, exatamente como já é do port de repositório. O dono **não**
   altera comportamento nesta feature: ele é costura de assinatura para a Onda 3. 🟢
   - Origem no legado: `_reversa_sdd/addenda/006-fronteira-aplicacao-ports.md` (`RF-08`, `RN-06`)
   - Tipo: alterada (mesma regra, aplicada à segunda porta)
2. **RN-02:** O armazenamento continua sendo **único por processo** e **não** ganha escopo
   por dono: a chave continua derivada do conteúdo, a referência continua sendo
   `<chave>__<nome visível>` e dois envios do mesmo conteúdo pelo mesmo processo continuam
   encontrando o mesmo arquivo. Introduzir o dono no caminho ou na chave seria mudança de
   comportamento observável e quebraria a paridade do armazenamento. 🟢
   - Origem no legado: `_reversa_sdd/domain.md#3.5`
   - Tipo: nova (restrição de preservação)
3. **RN-03:** Nenhuma mensagem visível ao operador muda. As dez mensagens da camada de rota
   permanecem literais e nos mesmos casos. 🟢
   - Origem no legado: `_reversa_sdd/domain.md#5.1`
   - Tipo: nova (restrição de preservação)
4. **RN-04:** A linha de base da suíte passa a ser a **nova medição, feita no interpretador
   oficial**, e o par "178 aprovados, 15 erros de ambiente" passa a ser leitura **histórica** —
   o registro de uma medição feita numa máquina onde 15 testes não executavam. Nenhuma entrega
   futura pode ser comparada contra o número antigo como se ele medisse a mesma coisa. O número
   antigo **não** é reescrito nos artefatos das features 005 e 006 nem no adendo vigente da 006:
   a marca de histórico vive nos artefatos desta feature. 🟢
   - Origem no legado: `_reversa_forward/006-fronteira-aplicacao-ports/requirements.md#5` (`RF-16`)
   - Tipo: alterada (emenda de **métrica**, não de comportamento de produto)
5. **RN-05:** A correção do defeito de ambiente vive **no repositório** e não depende de
   estado da máquina: não pode exigir variável de ambiente definida à mão, caminho absoluto
   local nem passo manual documentado. Quem clonar o projeto e rodar a suíte tem de obter o
   mesmo resultado. 🟢
   - Origem no legado: `.reversa/principles.md#II` e `#III`
   - Tipo: nova
6. **RN-06:** O dono **não** é credencial e **não** é mecanismo de segurança. A dívida #3
   (contaminação entre requisições concorrentes) e a #4 (ausência de isolamento) continuam
   abertas, e nenhuma entrega desta feature pode ser citada como tendo-as fechado. 🟢
   - Origem no legado: `_reversa_sdd/architecture.md#7` (dívidas #3 e #4)
   - Tipo: nova (não-objetivo declarado)

## 5. Requisitos Funcionais

| ID | Requisito | Prioridade | Critério de aceite | Confidência |
|----|-----------|------------|--------------------|-------------|
| RF-01 | O port de armazenamento de arquivo recebe a identidade do dono como parâmetro obrigatório nos **dois** métodos | Must | A assinatura de `guardar` e de `resolver` expõe o dono sem valor padrão; uma chamada montada sem ele é recusada pelo próprio contrato; nenhum chamador pode omiti-lo | 🟢 |
| RF-02 | O adaptador em disco implementa o contrato novo **ignorando** o dono para comportamento | Must | Chave, nome armazenado, caminho devolvido, reuso por conteúdo e ordem de validação permanecem idênticos aos de hoje; o `RF-09` da feature 006 continua verdadeiro | 🟢 |
| RF-03 | Todos os chamadores passam o dono ao port de armazenamento | Must | As duas chamadas de produção a `guardar` e a chamada a `resolver` passam o dono; nenhuma passa valor inventado no local | 🟢 |
| RF-04 | Existe **uma** constante nomeada de dono local, declarada em um único lugar, e ela registra que não é mecanismo de segurança | Must | A constante é citada por todos os chamadores; existe comentário ou docstring declarando que não há isolamento e que a dívida #3 não é tratada | 🟢 |
| RF-05 | O contrato do port de armazenamento é provado por teste, e não só por inspeção | Must | Um teste monta a chamada sem o dono e prova que ela é recusada; outro prova que o adaptador aceita o dono e **não** o usa para decidir caminho nem chave | 🟢 |
| RF-06 | Os 15 testes de `tests/test_upload_seguranca.py` que hoje morrem no setup passam a **executar** | Must | A suíte completa não reporta nenhum erro de ambiente; nenhum teste foi removido, desabilitado, renomeado por conveniência ou teve asserção reescrita | 🟢 |
| RF-07 | A correção do ambiente vive no repositório e não depende de estado da máquina | Must | A correção é feita em `tests/conftest.py`, sem mexer em `pytest.ini`; a suíte roda igual em clone limpo, sem variável de ambiente extra, sem `--basetemp` na linha de comando e sem passo manual; nenhuma referência a caminho absoluto de estação | 🟢 |
| RF-08 | A linha de base da suíte é remedida e registrada, no interpretador oficial | Must | Existe uma medição nova, feita com `.venv/Scripts/python.exe`, com aprovados e erros separados, registrada como a linha de base vigente; a anterior fica marcada como histórica; o comando de medição fica registrado junto do número | 🟢 |
| RF-09 | Se algum dos 15 testes falhar na primeira execução, a falha é triada e registrada | Should | Cada falha tem veredito explícito e datado: **defeito de produto** (não é corrigido aqui — vira requisito próprio, com arquivo e linha) ou **defeito de teste** (corrigido nesta feature, com o motivo declarado). Nenhuma falha fica sem veredito | 🟡 |
| RF-10 | A paridade diferencial permanece em 100 %, medida no interpretador oficial | Must | As 6 fixtures contra o oráculo congelado seguem em 100 %, exit 0, **executadas com `.venv/Scripts/python.exe`**. O estado atual já foi medido nele em 2026-10-07 — 100 %, zero divergência, exit 0 — e o que a feature precisa é **manter** e **registrar o comando** da medição. Nenhuma constante numérica de domínio pode mudar de valor | 🟢 |
| RF-11 | A assinatura de retorno do núcleo continua congelada | Must | `path_search` e `dna_analysis` continuam devolvendo a tupla de três; o `Tree` continua com quatro elementos; nenhum campo de desfecho entra no núcleo | 🟢 |
| RF-12 | Nenhuma superfície de compatibilidade nova é criada | Should | O dono não vira parâmetro opcional por conveniência, nem existe sobrecarga que aceite a chamada antiga sem dono | 🟡 |

## 6. Requisitos Não Funcionais

| Tipo | Requisito | Evidência ou justificativa | Confidência |
|------|-----------|----------------------------|-------------|
| Manutenibilidade | As duas portas ficam **simétricas** quanto ao dono | A assimetria é o motivo de a Onda 3 ter de reabrir contrato; `RF-08` da 006 já fixou o dono na porta de repositório | 🟢 |
| Testabilidade | Os 15 testes de rota deixam de ser inalcançáveis, e a nova linha de base é reproduzível por qualquer clone | `_reversa_forward/006-fronteira-aplicacao-ports/evidence/README-evidencias.md#2` | 🟢 |
| Reprodutibilidade | Toda medição desta feature — linha de base e paridade — é feita no interpretador **oficial** (`.venv/`), com o comando registrado ao lado do número | `requirements.txt` (decisão de 2026-10-05); as medições de 2026-10-07 que sustentaram a Onda 2 rodaram no global, e por isso não valem como medição desta feature | 🟢 |
| Portabilidade | A correção não pode depender do modo do diretório temporário nem do sistema operacional | O defeito é do par `os.mkdir(mode=0o700)` + sistema desta estação; a correção tem de valer também onde ele não ocorre | 🟢 |
| Desempenho | A suíte não piora de ordem de grandeza; 15 testes a mais executando é acréscimo esperado, não regressão | Linha de base medida: a suíte completa roda em ~15 s com os erros de setup | 🟡 |
| Segurança | O dono não é credencial, não é segredo e não habilita acesso a dado de terceiro | `RN-06`; `_reversa_sdd/permissions.md` (zero autenticação) | 🟢 |
| Concorrência | A mudança **não** altera a exclusividade de processo nem trata a corrida entre requisições simultâneas: o armazenamento continua único por processo, e a dívida #3 segue aberta | `_reversa_sdd/architecture.md#7` (dívida #3); considerada e declarada fora do escopo, não ignorada | 🟢 |
| Dados de teste | Toda fixture envolvida é **sintética**; nenhum GEDCOM, CSV ou nome real entra no repositório | `Princípio I`; as fixtures existentes são `tests/fixtures/sample_gedcom.py` e as constantes sintéticas de `tests/test_upload_seguranca.py` | 🟢 |
| Observabilidade | A causa dos 15 erros fica registrada onde o próximo leitor a encontra, e não só no histórico de conversa | Requer que a correção cite `0o700` e o inventário de diretórios presos no lugar onde ela vive | 🟡 |
| Rastreabilidade | A constante de dono cita a origem (dívida #4 / `RN-06`) e o motivo de existir | `_reversa_sdd/architecture.md#7` | 🟢 |
| Operação | Os **13 diretórios presos que já existem** no workspace ficam **documentados**, com o comando de remoção que exige shell elevado, e **não** são removidos por esta feature | `_reversa_forward/006-fronteira-aplicacao-ports/evidence/README-evidencias.md#2.2`; eles são resíduo de execução, não do produto | 🟢 |

## 7. Critérios de Aceitação

```gherkin
# RF-01, RF-05 — o contrato novo, provado pelo caminho negativo.
Cenário: O port de armazenamento exige o dono
  Dado o contrato do port de armazenamento de arquivo
  Quando uma chamada é montada sem informar o dono
  Então o próprio contrato a recusa, e nenhum chamador de produção pode omiti-lo

# RF-02 — o dono não pode virar escopo de armazenamento.
Cenário: O dono não muda o armazenamento
  Dado o mesmo conteúdo enviado duas vezes com donos diferentes
  Quando o port grava e resolve a referência
  Então a chave, o nome armazenado e o caminho devolvido são os mesmos nos dois casos
  E o arquivo já gravado não é reescrito

# RF-03 — nenhum ponto de chamada fica para trás.
Cenário: Todos os chamadores passam o dono
  Dado o código de produção que grava e resolve arquivos
  Quando as chamadas ao port de armazenamento são inspecionadas
  Então todas passam o dono, e nenhuma inventa um valor no próprio local

# RF-04 — uma constante só, e ela não é segurança.
Cenário: A constante de dono é única e declarada como não-segurança
  Dado o adaptador de entrada
  Quando a origem do valor de dono é procurada
  Então ela está declarada em um único lugar
  E o lugar declara que não há isolamento entre donos e que a dívida de concorrência não é tratada aqui

# RF-06 — os testes voltam a executar.
Cenário: A suíte executa os testes de rota
  Dado um clone limpo do projeto
  Quando a suíte completa é executada
  Então os testes de test_upload_seguranca.py executam
  E não há nenhum erro de ambiente no relatório
  E nenhum teste foi removido, desabilitado ou teve asserção reescrita

# RF-07 — a correção vale fora desta estação.
Cenário: A correção não depende da máquina
  Dado um ambiente sem variável de ambiente extra e sem argumento de linha de comando
  Quando a suíte é executada
  Então ela produz o mesmo resultado que em qualquer outro clone

# RF-08 — a métrica vigente muda de dono.
Cenário: A linha de base nova é registrada com o comando que a produziu
  Dado o resultado da suíte após a correção, no interpretador oficial
  Quando a linha de base é atualizada
  Então o valor anterior fica marcado como histórico
  E o comando de medição fica registrado junto do número novo
  E nenhuma entrega futura é comparada contra o valor antigo como se medisse o mesmo conjunto

# RF-09 — o que fazer quando um teste nunca executado falha.
Cenário: Algum teste de rota falha ao executar pela primeira vez
  Dado um dos testes que nunca executou nesta máquina
  Quando ele executa e falha
  Então a falha recebe veredito explícito: defeito de produto, encaminhado como requisito próprio, ou defeito de teste, corrigido aqui

# RF-10 — a rede de segurança do comportamento, no interpretador oficial.
Cenário: A paridade é remedida no interpretador oficial e permanece em 100 %
  Dado o oráculo congelado e as 6 fixtures
  Quando o instrumento diferencial roda com o interpretador oficial do projeto
  Então o resultado é 100 % sem divergência
  E nenhuma constante de domínio mudou de valor

# RF-11 — o que esta feature não pode tocar.
Cenário: A assinatura de retorno do núcleo continua congelada
  Dado os fluxos de busca e de análise de DNA no núcleo
  Quando os seus retornos são conferidos
  Então a tupla de três com o indicador de sucesso permanece
  E nenhum campo de desfecho foi acrescentado ao núcleo

# RF-12 — a costura não pode virar superfície de compatibilidade.
Cenário: Nenhuma superfície de compatibilidade é criada
  Dado o contrato do port de armazenamento
  Quando as suas formas de chamada são procuradas
  Então existe uma só, com o dono obrigatório
  E não existe forma alternativa que aceite a chamada antiga sem dono

# RN-03 — o que o operador lê não muda.
Cenário: Nenhuma mensagem de tela muda
  Dado o conjunto de casos de erro e de sucesso das três telas
  Quando o texto e o modo de renderização são comparados antes e depois
  Então não há divergência em nenhum caso
```

## 8. Prioridade MoSCoW

| Item | MoSCoW | Justificativa |
|------|--------|---------------|
| RF-01, RF-02, RF-03 | Must | É a costura que a Onda 3 consome; adiá-la reabre contrato e chamadores |
| RF-06, RF-07 | Must | Sem isso, a superfície reescrita pela Onda 2 continua sem cobertura executável |
| RF-10, RF-11 | Must | Preservação de comportamento e da assinatura congelada do núcleo |
| RF-04, RF-05 | Must | Constante única e contrato provado por teste, não por inspeção |
| RF-08 | Must | A linha de base é o instrumento de comparação de toda entrega seguinte |
| RF-09 | Should | Depende de um fato que só existe depois da primeira execução |
| RF-12 | Should | Evita que a costura vire superfície de compatibilidade, que é o que a feature 005 fechou |
| RNF de portabilidade | Must | Uma correção que só funciona nesta estação não corrige o defeito |
| RNF de desempenho | Should | 15 testes a mais executando é acréscimo esperado; só a ordem de grandeza é requisito |

## 9. Esclarecimentos

### Sessão 2026-10-07

- **Q:** Qual interpretador define a linha de base e a medição de paridade desta feature?
  **R:** **O `.venv/`**, que o `requirements.txt` declara como oficial desde 2026-10-05, **e a
  paridade é remedida nele**. Razão factual que decidiu a pergunta: a última verificação de
  paridade no `.venv` é de 2026-10-05, **anterior** às features 005 e 006 — ou seja, a Onda 2
  nunca foi medida no interpretador oficial. As medições de 2026-10-07 que a sustentaram rodaram
  no global (`C:\Python314\python.exe`, com `ged4py 0.5.2`/`networkx 3.6.1`/`pandas 3.0.3`, que
  são as versões do manifesto do oráculo, e não as do pin). O global e o `.venv` divergem em três
  das quatro dependências que decidem o matching, e o `RISK-009` registra que essa diferença
  produz divergência que **não** é erro do port. Consequência declarada: a nova linha de base e a
  nova medição de paridade têm de ser feitas no `.venv/`, com o comando registrado ao lado do
  número. **Medido durante esta própria sessão, logo após a resposta:** no `.venv/` a suíte dá
  `231 passed, 15 errors` e a paridade dá `100 %`, exit 0 — **idênticos ao global**. Ou seja, a
  divergência de versões das dependências **não** alterou o resultado observável, e o `RISK-009`
  não se materializou nesta medição. O que muda é o **instrumento**: a medição oficial passa a
  ser a do `.venv/`. *(Esta resposta corrige uma premissa da versão inicial, que não dizia em
  qual interpretador a linha de base seria medida.)*
- **Q:** Qual artefato carrega a correção do diretório temporário?
  **R:** **`tests/conftest.py`**, que já existe e está dentro de `tests/**`, liberado pela política
  de edição. `pytest.ini` **não** está em `allowedPaths`, então a correção por lá exigiria um ato
  do usuário; e trocar só o fixture `app_cliente` deixaria qualquer teste futuro com o mesmo
  defeito. A correção vale para a suíte inteira.
- **Q:** Se um dos 15 testes falhar quando finalmente executar, o conserto é desta feature?
  **R:** **Triagem, com veredito explícito.** Defeito de **teste** é corrigido aqui; defeito de
  **produto** não é corrigido aqui — vira requisito próprio, com arquivo e linha. Razão: mudança de
  comportamento disfarçada de correção de ambiente violaria o Princípio II, e é exatamente a
  distinção que a feature 006 fez ao tratar o `AMB-015`. Nenhuma falha fica sem veredito.
- **Q:** Os 13 diretórios presos que já existem no workspace entram no escopo?
  **R:** **Não. Só impedir novos.** Os 13 ficam **documentados** com o comando de remoção que exige
  shell elevado, junto da causa (`os.mkdir(caminho, 0o700)`). Razão: eles são resíduo de execução
  de rodadas anteriores, não defeito do produto, e removê-los exige privilégio que o agente não tem
  — transformá-los em entregável criaria uma tarefa impossível de verificar.
- **Q:** A linha de base nova substitui o número antigo nos artefatos já entregues?
  **R:** **Não.** O par "178 aprovados, 15 erros de ambiente" fica marcado como **histórico** nos
  artefatos desta feature; os artefatos das features 005 e 006 e o adendo vigente da 006 **não** são
  reescritos. É a mesma decisão de 2026-10-07 já aplicada à migração: o delta entra por adendo, e
  reescrever artefato entregue apagaria o registro do que foi medido na época.

## 10. Lacunas

> **Nenhuma lacuna aberta.** As três dúvidas da versão inicial foram resolvidas na sessão de
> esclarecimento de 2026-10-07 e estão registradas na seção 9.

O que segue **não bloqueia** esta feature e fica registrado para não se perder:

- 🔴 **A paridade nunca foi medida no interpretador oficial depois das features 005 e 006.**
  Não é lacuna de requisito — é lacuna de **verificação** herdada, e a `RF-10` existe para
  fechá-la. Se a medição no `.venv/` divergir da do global, a divergência **não** é regressão
  desta feature: ela é o efeito medido da troca de versões das dependências que decidem o
  matching (`RISK-009`). Decidir o que fazer com essa divergência, se ela aparecer, é ato do
  usuário.
- 🔴 **Os 13 diretórios presos permanecem no workspace** e continuam exigindo shell elevado
  para remoção. Registrado em `README-evidencias.md#2.2` da feature 006.
- 🔴 **A dívida #3 (corrida entre requisições concorrentes) e a #4 (isolamento) seguem
  abertas**, por decisão desta e das ondas anteriores. A `RN-06` existe para impedir que
  qualquer entrega desta feature seja citada como tendo-as fechado.

## 11. Histórico de alterações

| Data | Alteração | Autor |
|------|-----------|-------|
| 2026-10-07 | Versão inicial gerada por `/reversa-requirements` | reversa |
| 2026-10-07 | Sessão de esclarecimento: as 3 dúvidas resolvidas (interpretador oficial, artefato da correção do temp, triagem de falha, diretórios presos, histórico da linha de base); `RF-07`, `RF-08`, `RF-09` e `RF-10` emendados; `RN-04` explicitada; duas linhas de RNF acrescentadas (reprodutibilidade e operação) e dois cenários Gherkin reescritos | reversa |

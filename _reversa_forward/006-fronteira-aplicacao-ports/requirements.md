# Requirements: fronteira de aplicação em `src/` — `application/` + `ports/` (Onda 2 do cutover)

> Identificador: `006-fronteira-aplicacao-ports`
> Data: `2026-10-07`
> Pasta da extração reversa: `_reversa_sdd/`
> Confidência: 🟢 CONFIRMADO, 🟡 INFERIDO, 🔴 LACUNA / DÚVIDA

## 1. Resumo executivo

A Onda 2 do `cutover_plan.md` exige uma fronteira de aplicação com contrato tipado e exceções de domínio. Hoje a orquestração dos três fluxos vive dentro da rota `index()` de `src/app.py`, que decide, valida, grava arquivo, chama o núcleo e monta a mensagem no mesmo lugar. Esta feature extrai essa orquestração para três casos de uso em `src/application/`, declara as interfaces que a fronteira consome em `src/ports/` e transforma os sinais de erro que hoje são strings e `ValueError` genérico em exceções de domínio tipadas. Cada caso de uso devolve um **resultado tipado**, e é o adaptador que decide como renderizá-lo. O Flask permanece como adaptador de entrada e a tela continua idêntica: **diff textual zero**. Vale para quem vai construir a persistência e o isolamento por usuário na Onda 3, e para quem precisa trocar a borda sem tocar no núcleo.

## 2. Contexto a partir do legado

| Fonte | Trecho relevante | Confidência |
|-------|------------------|-------------|
| `_reversa_sdd/migration/cutover_plan.md#Pré-requisitos` | "Onda 2 — Fronteira de aplicação com contrato tipado, exceções de domínio e status HTTP semântico" | 🟢 |
| `_reversa_sdd/migration/paradigm_decision.md#Implicações` | Implicação 3: "Lógica embutida na rota migra para serviços de domínio, com os limiares virando constantes nomeadas"; e a restrição dura de que nomear constantes **não pode alterar nenhum valor** | 🟢 |
| `_reversa_sdd/migration/paradigm_decision.md#Notas` | Regra de fronteira operacional: *algoritmo de negócio* → núcleo, função pura, fidelidade absoluta; *plumbing* → borda, modernização livre | 🟢 |
| `_reversa_sdd/migration/topology_decision.md#Notas` | "Onda 2 cria `application/`, `api/`, `ports/`" e "a fronteira segue o desenho moderno sem restrição" | 🟢 |
| `_reversa_sdd/architecture.md#1` | O `src/app.py` concentra roteamento, validação de entrada, gravação em disco, orquestração dos dois fluxos pós-upload e montagem de mensagem | 🟢 |
| `_reversa_sdd/architecture.md#7` | Dívida #3 (contaminação entre requisições, Alta, **não fechada**), dívida #4 (ausência de identidade e isolamento, Alta), dívida #8 (nada é persistido entre requisições) e dívida #10 (o CSV de DNA é gravado antes de qualquer verificação de conteúdo) | 🟢 |
| `_reversa_sdd/domain.md#4` | "O GEDCOM é re-parseado a partir da chave recebida, antes de ramificar. Não há árvore 'carregada' sobrevivendo entre requisições" | 🟢 |
| `_reversa_sdd/domain.md#5.1` | Os 10 literais da camada de rota, incluindo `"Ocorreu um erro: {e}"` e `"Arquivo maior que o limite de {n} MB."` (HTTP 413) | 🟢 |
| `_reversa_sdd/domain.md#5.2` | As exceções do núcleo: `"Seu nome '{root_name}' não foi encontrado no GEDCOM."` (`dna_analysis.py:127`) e `"Colunas de Nome e cM não encontradas no CSV."` (`genetic_evidence.py:125`) | 🟢 |
| `_reversa_sdd/migration/parity_tests/12-paridade-telas.feature` | Cenário "Mensagens de erro do backend são preservadas literalmente": 9 mensagens congeladas, entre literais fixos e literais com nome interpolado | 🟢 |
| `_reversa_sdd/screens/golden/manifest.yaml` | 7 das 8 telas literais com golden capturado (`present: true`); "Para a Onda 2, as 8 telas literais mantêm o comportamento atual (diff textual zero)" contrasta com a única exceção autorizada, DEV-005 (`Close` → `Fechar`) | 🟢 |
| `src/app.py:190`, `:231`, `:245` | Os três `except Exception as e` que convertem qualquer falha em `"Erro ao processar GEDCOM: {e}"` ou `"Ocorreu um erro: {e}"` | 🟢 |
| `tests/test_confrontacao_gedcom_dna.py:920`, `:936` e `tests/test_dna_analysis.py:219`, `:241` | Quatro asserções que exigem `pytest.raises(ValueError)` e conferem o **texto** da mensagem | 🟢 |
| `tests/test_upload_seguranca.py:412` | Asserção sobre o literal `"Ocorreu um erro"` na resposta HTTP renderizada | 🟢 |
| `_reversa_sdd/addenda/005-nucleo-puro-src.md#Resumo da entrega` | `src/core/` é puro e recebe a árvore por parâmetro; `_DEPENDENCIAS` é montado no `app.py` e injetado; `cm_estimator.py` permanece em disco | 🟢 |

## 3. Personas e cenários de uso

| Persona | Objetivo | Cenário-chave |
|---------|----------|---------------|
| Desenvolvedor do analisador | Mudar uma regra de orquestração sem ler `app.py` inteiro | Abre `application/analyze_dna.py` e vê a sequência de passos e as dependências que ela pede |
| Mantenedor da migração | Trocar a borda sem risco de mexer no núcleo | Substitui o adaptador de entrada e confere que o núcleo não importou nada da borda |
| Responsável pelo cutover | Fechar o portão da Onda 2 antes de iniciar a Onda 3 | Confere que a fronteira tem contrato tipado e que a paridade e a suíte seguem verdes |
| Genealogista (usuário final) | Continuar vendo exatamente as mesmas telas e as mesmas mensagens | Usa a aplicação após a mudança e não percebe nenhuma diferença de texto, fluxo ou resultado |

## 4. Regras de negócio novas ou alteradas

1. **RN-01:** A orquestração deixa de viver na função de rota e passa a viver em casos de uso; o núcleo não é tocado. Nenhum limiar, peso, ordem de avaliação, ordem de agregação ou critério do matching e do caminho é alterado. 🟢
   - Origem no legado: `_reversa_sdd/migration/paradigm_decision.md#Notas` (regra de fronteira) e `_reversa_sdd/addenda/005-nucleo-puro-src.md#Resumo da entrega`
   - Tipo: nova, e é uma regra de preservação — a `RN-01` da feature 005 continua valendo integralmente
2. **RN-02:** O tratamento de erro da camada de aplicação deixa de ser string de retorno e `except Exception` genérico, e passa a ser exceção de domínio tipada. As mensagens que o usuário lê **não mudam**: o adaptador de entrada continua produzindo exatamente os literais de `_reversa_sdd/domain.md#5.1`. 🟢
   - Origem no legado: `_reversa_sdd/migration/paradigm_decision.md#Implicações` (Implicação 2) e `_reversa_sdd/domain.md#5.1`
   - Tipo: alterada — o mecanismo de sinalização muda, o texto observável não
3. **RN-03:** O fallback de encoding Latin-1 do CSV continua sendo comportamento de negócio congelado e não pode desaparecer nem virar efeito colateral de um `try/except` incidental. 🟢
   - Origem no legado: `_reversa_sdd/migration/paradigm_decision.md#Implicações` (Implicação 2, parágrafo final)
   - Tipo: nova, restrição de preservação
4. **RN-04:** As telas literais mantêm **diff textual zero**. A única correção de texto historicamente autorizada é `DEV-005` (`Close` → `Fechar`), que já está aplicada; esta feature não autoriza nenhuma outra. 🟢
   - Origem no legado: `_reversa_sdd/migration/parity_tests/12-paridade-telas.feature` e `_reversa_sdd/screens/golden/manifest.yaml`
   - Tipo: nova, critério de aceite
5. **RN-05:** O mapeamento de exceção para `404`/`422` com payload estruturado vale **somente** para a API nova. Ele não é exercido por nenhuma tela atual e não pode alterar a resposta que o operador recebe hoje. 🟢
   - Origem no legado: decisão do usuário registrada em 2026-10-07
   - Tipo: nova, delimitação de escopo
6. **RN-06:** A fronteira é desenhada para receber `owner_id`, mas nenhum comportamento de isolamento é implementado nesta feature. A dívida #3 (contaminação entre requisições concorrentes) **não** é fechada aqui, e nenhuma entrega desta feature pode ser citada como tendo fechado. 🟢
   - Origem no legado: `_reversa_sdd/architecture.md#7` (dívidas #3 e #4) e `_reversa_sdd/addenda/005-nucleo-puro-src.md#Regras sob vigilância` (`W003`)
   - Tipo: nova, não-objetivo declarado

> **Decisão de 2026-10-07 sobre a hierarquia de exceções.** A raiz é `ErroDeDominio`, que herda de `ValueError`. **Quatro** tipos herdam dela: `PessoaNaoEncontrada`, `GedcomNaoSuportado`, `DnaCsvSemColunas` e `CsvIlegivel`. A herança de `ValueError` é deliberada e tem uma razão verificável: as quatro asserções de `tests/test_confrontacao_gedcom_dna.py:920`, `:936` e `tests/test_dna_analysis.py:219`, `:241` capturam `ValueError` e conferem o texto da mensagem. Sem a herança, a `RF-05` e o cenário negativo "A suíte existente não pode ser reduzida" seriam violados. **Consequência declarada:** exceção de domínio e exceção de valor da linguagem ficam na mesma linhagem, e por isso todo `except ValueError` que não seja de domínio precisa continuar sendo distinguido pelo tipo, nunca pela mensagem.
>
> **Decisão de 2026-10-07 sobre o tipo que não entra (achado `A002` da auditoria).** Um quinto tipo, `ArmazenamentoInvalido`, foi **descartado** na sessão de esclarecimento. Razão factual: a validação de conteúdo devolve **motivo em texto**, não exceção (`src/utils/validate.py`), e é o caso de uso que transforma o motivo na exceção de GEDCOM não reconhecido. Um tipo que o adaptador de armazenamento nunca levanta seria superfície sem gatilho — a mesma classe de defeito que a dívida #17 da feature 005 fechou. A falha de **armazenamento** propriamente dita (chave gerada, escrita em object storage, escopo por dono) é outro tipo, com outro gatilho, e pertence à Onda 3.
>
> **Decisão de 2026-10-07 sobre onde mora o texto de tela.** Cada exceção carrega **apenas a mensagem do ponto que a levanta**, nunca a moldura de apresentação. Exemplo medido: o `app.py:108` monta hoje `f"Arquivo não reconhecido como GEDCOM: {motivo}."`, mas o `validate.py` devolve só o `motivo`. A exceção `GedcomNaoSuportado` carrega o **motivo**; a moldura `"Arquivo não reconhecido como GEDCOM: …"` continua na tabela de tradução do adaptador. Sem essa separação, texto de tela vazaria para dentro do núcleo, que é o inverso do objetivo desta onda.

> **Decisão de 2026-10-07 sobre o desfecho no resultado (achado `A003` da auditoria).** O resultado tipado carrega um campo de **desfecho**, e o adaptador deriva dele o `success=` do template e o modo de renderização. O campo tem **três valores, todos alcançáveis**, e é derivado do que o núcleo já sinaliza — nunca do texto da mensagem:

| Insumo do núcleo | Desfecho no resultado tipado | Render do adaptador |
|---|---|---|
| sucesso **com** payload | `RESULTADO` | Cartão de resultado |
| sucesso **sem** payload | `SEM_RESULTADO` | "Nenhuma conexão encontrada" — **com sucesso** |
| falha sinalizada pelo núcleo | `ERRO_DE_ENTRADA` | Alerta de erro |

> **Por que não há um quarto valor para "entrada inválida" em geral.** Toda entrada inválida que **não** vem do núcleo já é exceção de domínio, e exceção não produz valor de enum: ela interrompe o fluxo. Um valor que nenhum caminho preenche seria superfície sem gatilho — o mesmo defeito que esta sessão descartou no `ArmazenamentoInvalido`.
>
> **Restrição dura que acompanha esta decisão.** A **assinatura de retorno do núcleo é congelada**: o harness compara o indicador de sucesso dos fluxos contra o oráculo (`_reversa_sdd/parity/harness.py:211` e `:412`) e nove asserções de teste dependem da tupla de três elementos. O campo de desfecho vive **no resultado tipado do caso de uso**, e o núcleo **não** é alterado. A extração lê o que o núcleo já devolve; não o reinterpreta nem o reescreve.
>
> **Correção de premissa registrada no achado `A001`.** A sessão de esclarecimento anterior registrou que a referência pendente no GEDCOM seria *"aceita e sinalizada, como o Designer recomendou"*. A segunda metade estava **errada**: o `AMB-015` classifica a sinalização como `REFERIDO À CODIFICAÇÃO` — recomendação do Designer **pendente**, nunca implementada —, e o parser nunca sinalizou nada. O legado aceita o arquivo e descarta a aresta em silêncio. A decisão de 2026-10-07 corrige o requisito para o comportamento real; ver `RF-19` e §10.

> **Decisão de 2026-10-07 sobre o que atravessa a fronteira.** Cada caso de uso devolve um **resultado tipado** — uma estrutura com campos nomeados e tipados — e o adaptador de entrada decide como renderizá-lo. Não atravessa a fronteira da aplicação para o adaptador: nome de campo de template, o parâmetro `success=`, dicionário de contexto de renderização ou qualquer outro detalhe de apresentação. **Uma exceção é explícita:** as mensagens de sucesso e de erro que a tela exibe são contrato congelado (`_reversa_sdd/domain.md#5.1`), e por isso viajam como **campo declarado do resultado**, e não como texto montado dentro da aplicação. O adaptador lê o campo; ele não o redige.

> **Decisão de 2026-10-07 sobre o `Dependencias`.** A classe permanece em `src/core/dna_analysis.py`, e `ports/` declara Protocolos **apenas** para o armazenamento de arquivo e para o repositório de árvore. Nesta onda **não** é criado Protocolo para a leitura de CSV nem para a emissão de diagrama. Isso preserva a assinatura que a feature 005 estabilizou e concentra os ports no que a Onda 3 vai substituir. **Limite declarado:** o contrato entre núcleo e fronteira continua sendo uma classe concreta do núcleo, e não uma interface da fronteira.

> **Decisão de 2026-10-07 sobre o alvo da migração (opção (c) da divergência).** O alvo é `src/`, com Flask servido por waitress. **Não** existe e **não** será criado um projeto `analisador/` nesta onda. FastAPI, PostgreSQL e React permanecem especificados em `_reversa_sdd/migration/` e ficam para ondas posteriores. Os artefatos de migração **não são reescritos**: o delta é registrado por adendo, e a divergência entre o esboço de árvore de `topology_decision.md#Notas` — que pressupunha `analisador/` — e o alvo real fica declarada em vez de silenciada.

> **Decisão de 2026-10-07 sobre o Flask.** O Flask permanece como adaptador de entrada nesta onda. Consequência direta: `src/api/` **não** é criado aqui. O adaptador de entrada continua sendo `src/app.py`, que passa a ser fino — recebe HTTP, chama o caso de uso, e traduz o resultado ou a exceção para o template.

## 5. Requisitos Funcionais

| ID | Requisito | Prioridade | Critério de aceite | Confidência |
|----|-----------|------------|--------------------|-------------|
| RF-01 | A orquestração de cada um dos três fluxos (`upload_gedcom`, `dna_analysis`, `path_search`) sai de `index()` e passa a um caso de uso próprio em `src/application/` | Must | Existem três casos de uso, um por fluxo; `index()` não contém sequência de passos de domínio — nenhuma chamada a parser, agregador de CSV ou resolvedor de diagrama permanece no `app.py`; cada caso de uso é chamável sem HTTP, sem `request` e sem contexto de template. A extração do fluxo `dna_analysis` é a última das três e ocupa ação própria do `roadmap.md`, para que a execução possa parar entre elas | 🟢 |
| RF-02 | `src/ports/` declara as interfaces que a fronteira consome para I/O | Must | Existem **dois** ports: armazenamento de arquivo e repositório de árvore. Ambos são consumidos por parâmetro pelos casos de uso, e nenhum caso de uso instancia a implementação concreta. Protocolo para leitura de CSV ou para emissão de diagrama **não** é criado nesta onda | 🟢 |
| RF-03 | As exceções de domínio são tipadas e nomeadas, com raiz própria, substituindo `ValueError` genérico e strings de erro no caminho da aplicação | Must | A raiz é `ErroDeDominio`; existem **quatro** tipos distintos e nomeados, todos herdando dela: `PessoaNaoEncontrada` (raiz do DNA ausente do GEDCOM), `GedcomNaoSuportado` (conteúdo recusado na validação), `DnaCsvSemColunas` (CSV sem as colunas obrigatórias) e `CsvIlegivel` (CSV que não pôde ser lido). Cada tipo é levantado pelo ponto que **detecta** a condição: os dois primeiros pelo núcleo, `CsvIlegivel` pela leitura do CSV e `GedcomNaoSuportado` pelo caso de uso, ao receber o motivo da recusa do armazenamento. Cada tipo carrega **apenas a mensagem do seu ponto de detecção** — a moldura de apresentação fica na tabela de tradução do adaptador | 🟢 |
| RF-04 | Cada exceção de domínio carrega a mensagem literal que a tela atual exibe | Must | A representação textual de cada exceção é **idêntica** à mensagem que o `app.py` produz hoje para a mesma condição, inclusive nos trechos interpolados (`Seu nome 'X' não foi encontrado no GEDCOM.`) | 🟢 |
| RF-05 | As exceções de domínio continuam capturáveis pelas asserções existentes da suíte | Must | As quatro asserções que hoje exigem `pytest.raises(ValueError)` — `tests/test_confrontacao_gedcom_dna.py:920`, `:936`, `tests/test_dna_analysis.py:219`, `:241` — continuam passando **sem serem reescritas**, por herança de `ErroDeDominio` a partir de `ValueError` | 🟢 |
| RF-06 | O adaptador de entrada traduz cada exceção de domínio de volta ao literal exato da tela, e recebe do resultado tipado o **desfecho** que decide o modo de renderização | Must | As 9 mensagens congeladas de `12-paridade-telas.feature` são produzidas nos mesmos casos em que são produzidas hoje; o teste `tests/test_upload_seguranca.py:412` continua encontrando o literal `"Ocorreu um erro"`; e a decisão entre alerta de erro, cartão de resultado e "nenhuma conexão encontrada" vem do campo de desfecho, **nunca** do texto da mensagem | 🟢 |
| RF-07 | A resposta HTTP observável não muda: mesmas rotas, mesmos campos de formulário, mesmos status, mesmo template | Must | Os 7 golden files capturados em `_reversa_sdd/screens/golden/manifest.yaml` continuam batendo; `GET /` responde 200; `POST /` com corpo acima do teto continua respondendo `413` | 🟢 |
| RF-08 | O port de repositório recebe a identidade do dono como parte do contrato, desde já | Must | A assinatura do port expõe o dono como parâmetro obrigatório; a implementação desta onda pode ignorá-lo, mas nenhum chamador pode omiti-lo | 🟡 |
| RF-09 | O port de armazenamento preserva o contrato atual de gravação e reuso por conteúdo | Must | O arquivo continua sendo gravado sob chave derivada do conteúdo; conteúdo já armazenado **não** é regravado; o caminho devolvido é o caminho completo do arquivo, e nunca um nome a ser remontado | 🟢 |
| RF-10 | A validação de conteúdo do GEDCOM acontece antes de o arquivo ser gravado, como hoje | Must | Um conteúdo inválido produz a exceção de GEDCOM não reconhecido **sem** que o arquivo apareça na pasta de upload | 🟢 |
| RF-11 | O fallback de encoding Latin-1 do CSV é preservado como estratégia explícita de codec | Must | `read_csv_with_fallback` continua sendo chamado pelo port de leitura de CSV nos mesmos termos; nenhuma exceção de domínio intercepta a queda para Latin-1 | 🟢 |
| RF-12 | O fallback de formatação de nome vazio é preservado exatamente como está | Must | O formato vazio continua devolvendo string vazia e apenas a ausência de nome produz `"Sem Nome"` (`AMB-024`); nenhuma normalização nova é introduzida na borda | 🟢 |
| RF-13 | O núcleo não passa a importar a fronteira | Must | Teste automático falha se qualquer módulo de `src/core/` importar `application/` ou `ports/`; os quatro guardas de `tests/test_dependencias_nucleo.py` continuam verdes | 🟢 |
| RF-14 | As dependências de borda que o núcleo consome continuam declaradas em um único lugar | Should | `Dependencias` permanece em `src/core/dna_analysis.py` e segue sendo o contrato entre núcleo e fronteira; existe **exatamente um** ponto que a monta, e nenhum caso de uso monta a sua própria cópia por requisição. Nenhum Protocolo de `ports/` a substitui nesta onda | 🟡 |
| RF-15 | Nenhum limiar, peso ou valor de domínio é alterado pela extração | Must | Paridade diferencial em 100% nas 6 fixtures contra o oráculo congelado, e revisão que mostre que nenhuma constante numérica mudou de valor | 🟢 |
| RF-16 | A suíte de testes existente continua passando, sem teste removido ou desabilitado | Must | Linha de base da feature 005: **178 aprovados, 0 falhas esperadas, 15 erros de ambiente**. Os 15 erros são de `test_upload_seguranca.py` em `setup`, por `PermissionError` de diretório temporário, e nenhum deles é regressão de código | 🟢 |
| RF-17 | As 8 telas literais mantêm diff textual zero | Must | Nenhum literal visível ao operador muda; a única exceção autorizada é `DEV-005`, já aplicada | 🟢 |
| RF-18 | Existe caminho de teste para o mapeamento exceção → status, mesmo sem a API nova | Should | O mapeamento é exercitado por teste direto sobre a tabela de tradução, sem subir uma aplicação HTTP nova | 🟡 |
| RF-19 | Referência pendente no GEDCOM é **aceita**, e a aresta correspondente não entra na árvore — rejeitar é proibido | Must | Um GEDCOM com `HUSB`, `WIFE`, `CHIL`, `FAMC` ou `FAMS` apontando para xref inexistente continua sendo aceito, exatamente como no legado; a aresta correspondente não entra na árvore e **nenhuma exceção é levantada por essa condição**. Rejeitar o arquivo, ou introduzir validação estrita de referência, é proibido nesta onda e nas seguintes sem requisito próprio (`AMB-015`). A **sinalização** das referências pendentes **não** é exigida por esta onda — ver §10 | 🟢 |
| RF-20 | O caso de uso devolve resultado tipado, e nenhum detalhe de apresentação atravessa a fronteira | Must | O retorno de cada caso de uso é uma estrutura com campos nomeados e tipados; ela **não** contém nome de campo de template, o parâmetro `success=`, nem dicionário de contexto de renderização. As mensagens de contrato congeladas viajam como campo declarado do resultado, não como texto montado na aplicação. O **desfecho** que o adaptador usa para escolher o modo de renderização é campo tipado do resultado. **A assinatura de retorno do núcleo não é alterada**: o harness compara o indicador de sucesso dos fluxos contra o oráculo, e o caso de uso lê o que o núcleo já devolve | 🟢 |
| RF-21 | A falha de leitura do CSV de matches é sinalizada como exceção de domínio tipada | Must | Um CSV que não pôde ser lido — separador inutilizável, aspas desbalanceadas, arquivo de outro tipo — produz `CsvIlegivel` com a **mesma mensagem** que o ponto de detecção já produz hoje, incluindo a lista de tentativas. Esta é a lacuna de rastreabilidade fechada pelo achado `A002`: o tipo já tem ponto de levantamento e teste, e passava sem requisito que o autorizasse. O fallback de encoding Latin-1 **não** é afetado (`RN-03`, `RF-11`) | 🟢 |

## 6. Requisitos Não Funcionais

| Tipo | Requisito | Evidência ou justificativa | Confidência |
|------|-----------|----------------------------|-------------|
| Manutenibilidade | O núcleo é o único lugar com decisão de domínio; a aplicação orquestra e não decide regra de negócio | `_reversa_sdd/architecture.md#3`; regra de fronteira de `_reversa_sdd/migration/paradigm_decision.md#Notas` | 🟢 |
| Testabilidade | Os casos de uso são executáveis sem HTTP, sem `request` e sem processo do servidor | Ganho declarado em `_reversa_sdd/migration/topology_decision.md#Ganhos concretos esperados` | 🟢 |
| Exatidão | A comparação de paridade continua sendo por igualdade exata, sem tolerância e sem arredondamento | `_reversa_sdd/migration/parity_specs.md#Critérios`, RISK-004 | 🟢 |
| Preservação | Nenhum texto visível ao operador muda | `_reversa_sdd/domain.md#5` e `_reversa_sdd/migration/parity_tests/12-paridade-telas.feature` | 🟢 |
| Segurança | Nenhum segredo é introduzido na fronteira; a chave de armazenamento continua sendo identificador, **não** segredo | `_reversa_sdd/architecture.md#7` (dívida #4) e `_reversa_sdd/permissions.md` (`P-04`) | 🟢 |
| Rastreabilidade | Toda constante transcrita carrega referência ao ponto de origem no legado | `_reversa_sdd/migration/topology_decision.md#Notas`, mecanismo contra RISK-003 | 🟡 |
| Desempenho | A extração não piora a ordem de grandeza do custo por requisição; o parse continua dominando | `_reversa_sdd/migration/parity_harness.md#O que ainda NÃO está coberto`, item 5 | 🟡 |
| Determinismo | A ordem de apresentação dos resultados não muda: documental primeiro, e a ordenação por cM permanece a mesma | `_reversa_sdd/domain.md#3.7` | 🟢 |
| Observabilidade | O motivo de descarte de um candidato continua disponível para auditoria na resposta | `_reversa_sdd/migration/parity_tests/10-descartados-auditoria.feature` | 🟢 |
| Portabilidade | Nenhuma dependência nova é específica de plataforma; a guarda de exclusividade continua no bloco de entrada | `src/app.py` concentra o `SO_EXCLUSIVEADDRUSE` em `__main__` | 🟡 |

## 7. Critérios de Aceitação

```gherkin
Cenário: A rota deixa de orquestrar
  Dado o adaptador de entrada depois da extração
  Quando a função de rota é inspecionada
  Então ela recebe a requisição, chama um caso de uso e devolve a resposta
  E nenhuma chamada a parser, agregador de CSV ou resolvedor de diagrama permanece nela

Cenário: Os três fluxos têm caso de uso próprio
  Dado o código depois da extração
  Quando os casos de uso de src/application são enumerados
  Então existe um para upload de GEDCOM, um para análise de DNA e um para busca de caminho
  E a extração da análise de DNA foi a última das três

Cenário: O caso de uso roda sem HTTP
  Dado um arquivo GEDCOM sintético já armazenado
  Quando o caso de uso de busca de caminho é chamado diretamente com as dependências injetadas
  Então ele devolve o mesmo resultado que a rota devolvia
  E nenhum objeto de requisição HTTP foi necessário

Cenário: O retorno do caso de uso não conhece a tela
  Dado qualquer um dos três casos de uso
  Quando o seu retorno é inspecionado
  Então ele é uma estrutura com campos nomeados e tipados
  E não contém nome de campo de template, nem o parâmetro success=, nem contexto de renderização
  E a mensagem de contrato é um campo declarado, não texto montado na aplicação

Cenário: O modo de renderização vem do desfecho, não do texto
  Dado um retorno de busca de caminho com desfecho de sucesso sem payload
  Quando o adaptador escolhe o modo de renderização
  Então ele exibe "nenhuma conexão encontrada" como resultado bem-sucedido
  E a decisão não foi tomada a partir do texto da mensagem
  E alterar o texto da mensagem não muda o modo escolhido

Cenário: Referência pendente é aceita e descartada em silêncio
  Dado um GEDCOM em que FAMS aponta para uma família que não existe no arquivo
  Quando o upload é processado
  Então o arquivo é aceito, como no legado
  E a árvore não ganha a aresta correspondente
  E nenhuma exceção é levantada por essa condição
  E o arquivo não é rejeitado por validação de referência

Cenário: CSV de matches ilegível vira exceção tipada
  Dado um arquivo que não é uma lista de matches legível
  Quando a análise de DNA é executada
  Então é levantada a exceção de CSV ilegível
  E a mensagem é a mesma que o ponto de detecção produz hoje, com as tentativas de leitura listadas

Cenário: Raiz não encontrada vira exceção tipada com a mensagem congelada
  Dado um CSV de matches e um nome de raiz ausente do GEDCOM
  Quando a análise de DNA é executada
  Então é levantada a exceção de raiz não encontrada
  E sua mensagem é exatamente "Seu nome 'X' não foi encontrado no GEDCOM."

Cenário: CSV sem as colunas obrigatórias vira exceção tipada
  Dado um CSV sem coluna de cM reconhecível
  Quando a análise de DNA é executada
  Então é levantada a exceção de colunas ausentes
  E a tela continua exibindo "Ocorreu um erro: " seguido da mesma mensagem de hoje

Cenário: GEDCOM não reconhecido é recusado antes da gravação
  Dado um arquivo cujo conteúdo não é GEDCOM
  Quando o upload é processado
  Então é levantada a exceção de GEDCOM não reconhecido
  E nenhum arquivo novo aparece na pasta de upload

Cenário: Upload sem arquivo é recusado com a mensagem congelada
  Dado um POST de upload em que o campo do arquivo não foi enviado
  Quando o adaptador de entrada processa a requisição
  Então a tela exibe exatamente "Nenhum arquivo GEDCOM enviado."
  E nenhum arquivo é gravado na pasta de upload

Cenário: Upload com nome de arquivo vazio é recusado com a mensagem congelada
  Dado um POST de upload em que o campo do arquivo veio sem nome
  Quando o adaptador de entrada processa a requisição
  Então a tela exibe exatamente "Nenhum arquivo selecionado."
  E nenhum arquivo é gravado na pasta de upload

Cenário: Corpo acima do teto é recusado antes de qualquer verificação de negócio
  Dado um corpo de requisição maior que 16 MB
  Quando o adaptador de entrada processa a requisição
  Então a resposta tem status 413
  E a tela exibe exatamente "Arquivo maior que o limite de 16 MB."
  E nenhuma verificação de negócio foi executada

Cenário: O fallback Latin-1 sobrevive
  Dado um CSV codificado em Latin-1 com as colunas obrigatórias
  Quando a análise de DNA é executada
  Então o CSV é lido com sucesso pelo codec de reserva
  E o resultado é idêntico ao da leitura em UTF-8

Cenário: O port de repositório exige o dono
  Dado o contrato do port de repositório de árvore
  Quando uma chamada é montada sem informar o dono
  Então a chamada é recusada pelo próprio contrato
  E nenhum caso de uso pode omitir esse parâmetro

Cenário: A paridade de telas é preservada
  Dado o adaptador de entrada depois da extração
  Quando as telas literais são comparadas com os golden files capturados
  Então o diff textual é zero
  E nenhum literal novo aparece para o operador

Cenário: A paridade do núcleo é preservada
  Dado o candidato depois da extração
  Quando o harness diferencial roda contra o oráculo congelado
  Então a paridade é de 100% nas 6 fixtures
  E nenhuma divergência é relatada

Cenário negativo: A fronteira não pode vazar para o núcleo
  Dado que um módulo de src/core foi alterado para importar application ou ports
  Quando o teste de dependências varre os imports do núcleo
  Então o teste falha
  E a entrega é recusada

Cenário negativo: A dívida de concorrência não pode ser declarada fechada
  Dado o relatório de encerramento desta feature
  Quando ele afirma ter resolvido a contaminação entre requisições concorrentes
  Então a afirmação é falsa
  E a entrega é recusada

Cenário negativo: A suíte existente não pode ser reduzida
  Dado que um teste foi removido, desabilitado ou reescrito para acomodar a mudança
  Quando a suíte completa é executada
  Então a contagem de aprovados é menor que a linha de base
  E a entrega é recusada
```

## 8. Prioridade MoSCoW

| Item | MoSCoW | Justificativa |
|------|--------|---------------|
| RF-01 | Must | É a definição da Onda 2: sem tirar a orquestração da rota não há fronteira |
| RF-02 | Must | Sem port não há contrato; é o que a Onda 3 vai substituir |
| RF-03 | Must | É o "contrato tipado" do pré-requisito do `cutover_plan.md` |
| RF-04 | Must | A mensagem é contrato de tela; perdê-la quebra `RF-17` |
| RF-05 | Must | Princípio III: nenhuma mudança sem teste que a cubra — e sem reescrever o teste existente |
| RF-06 | Must | É o que garante que a extração não vazou para a tela |
| RF-07 | Must | A superfície HTTP é contrato observável congelado |
| RF-10 | Must | A ordem validação-antes-de-gravar é o miolo do `BUG-20260929-QMLY` |
| RF-11 | Must | O fallback Latin-1 é comportamento de negócio congelado, por decisão explícita |
| RF-12 | Must | `AMB-024` mediu: o fallback estreito é o que mantém paridade |
| RF-13 | Must | Violação invalida a Onda 1 e torna a paridade não isolável |
| RF-15 | Must | É o risco #1 declarado do brief |
| RF-16 | Must | Princípio III |
| RF-17 | Must | Decisão do usuário de 2026-10-07 |
| RF-19 | Must | `AMB-015`: rejeitar por invariante é melhor engenharia, mas quebra paridade — e paridade é o critério nº 1. A sinalização, que o `AMB-015` deixou pendente, **não** é exigida nesta onda |
| RF-20 | Must | É o que impede a fronteira de nascer acoplada ao template, que é o defeito que ela existe para corrigir |
| RF-21 | Must | Achado `A002`: o tipo tem ponto de levantamento e teste e passava sem requisito que o autorizasse — lacuna de rastreabilidade, não contrato novo |
| RF-08 | Must | É o que prepara a Onda 3 sem implementá-la; adiar torna a assinatura do port obsoleta no dia seguinte |
| RF-09 | Must | O reuso por conteúdo é o que faz o formulário devolver a chave no POST seguinte |
| RF-14 | Should | A duplicação da montagem por requisição é defeito latente, não bloqueio |
| RF-18 | Should | Sem a API nova o mapeamento não tem consumidor; testá-lo direto evita código morto |
| RNF de desempenho | Should | O parse domina o custo; a extração não deve piorar a ordem de grandeza |
| RNF de portabilidade | Could | Nada na fronteira é específico de plataforma hoje |

> **Nota sobre a distribuição das prioridades.** `RF-08` está em `Must` embora a Onda 3 não seja desta feature: adiar o parâmetro de dono significaria reabrir **toda** assinatura de port na onda seguinte, que é exatamente o custo que a Onda 2 existe para não pagar duas vezes. `RF-19`, `RF-20` e `RF-21` também são `Must`: o primeiro proíbe, nesta onda, um endurecimento que quebraria a paridade; o segundo fixa a forma do retorno antes de os três casos de uso existirem, porque mudá-la depois seria reescrever os três; o terceiro fecha a lacuna que a auditoria encontrou, dando requisito a um tipo que já é levantado e testado. Já `RF-14` e `RF-18` são `Should` porque nenhum dos dois bloqueia a fronteira: o primeiro é limpeza de um defeito latente, o segundo é cobertura de um mapeamento que ainda não tem consumidor de produção.

## 9. Esclarecimentos

### Sessão 2026-10-07

- **Q:** O escopo dos casos de uso nesta onda: os três fluxos de uma vez, um como padrão provado, ou uma combinação?
  **R:** Os três, mas com o `dna_analysis` entrando por último e sob ação própria do `roadmap.md`, para que a execução possa parar entre eles. Fronteira completa numa onda, com dois pontos de parada construídos de propósito: o `upload_gedcom` é o mais simples e prova o padrão; o `path_search` acrescenta o resolvedor de diagrama injetado; o `dna_analysis` é o mais longo e o que concentra mais literais congelados, então é o último a ser mexido. O risco de não haver tela já migrada para comparar é mitigado pela paridade diferencial e pelos 7 golden files capturados, que são a rede de segurança real.
- **Q:** Como conciliar as exceções de domínio novas com as quatro asserções da suíte que exigem `pytest.raises(ValueError)`?
  **R:** Hierarquia própria com `ErroDeDominio(ValueError)` como raiz única. Os tipos de domínio herdam de `ErroDeDominio`, e `ErroDeDominio` herda de `ValueError`. As quatro asserções continuam passando sem serem tocadas **e** existe um tipo de domínio próprio para capturar, o que preserva a `RF-05` e o Princípio III. Custo aceito e declarado em §4: exceção de domínio e exceção de valor da linguagem ficam na mesma linhagem, então nenhum `except ValueError` pode passar a distinguir casos pela mensagem — a distinção é sempre pelo tipo. *(Nomes atualizados para o português na sessão de auditoria — ver a nota de nomenclatura lá.)*
- **Q:** O caso de uso devolve parâmetros crus, tuplas posicionais ou resultado tipado?
  **R:** Resultado tipado com campos nomeados. Nenhum nome de campo de template, nenhum `success=` e nenhum dicionário de contexto de renderização atravessa da aplicação para o adaptador. As mensagens de contrato congeladas — que a `RN-04` obriga a preservar — viajam como **campo declarado do resultado**, não como texto montado dentro da aplicação: o adaptador lê o campo, não o redige. Isso mantém a mensagem sob contrato sem deixar a apresentação entrar na camada de aplicação.
- **Q:** Onde vive `Dependencias`, o contrato entre núcleo e fronteira?
  **R:** Permanece em `src/core/dna_analysis.py`, e `ports/` declara Protocolos apenas para o armazenamento de arquivo e para o repositório de árvore. Nenhum Protocolo para leitura de CSV ou emissão de diagrama é criado nesta onda. A escolha preserva a assinatura que a feature 005 estabilizou e concentra os ports no que a Onda 3 efetivamente vai substituir.
- **Q:** Qual cobertura de caminho negativo e de borda entra nesta onda?
  **R:** Os três casos de borda do upload com mensagem congelada — campo de arquivo ausente, nome de arquivo vazio e corpo acima do teto de 16 MB respondendo `413` — e a decisão sobre referência pendente no GEDCOM (`AMB-015`). Os três primeiros ganharam cenário Gherkin próprio em §7. A referência pendente foi decidida como `RF-19`: o GEDCOM é **aceito** e rejeitar está descartado. ⚠️ **A segunda metade desta resposta foi corrigida na sessão de auditoria** — ver abaixo. Ficaram fora do escopo desta onda, e portanto seguem abertos: a sinalização da ambiguidade de homônimos na raiz da análise (`AMB-008`) e a validação de conteúdo do CSV de DNA (dívida #10).

### Sessão 2026-10-07 (auditoria)

Aberta depois do `/reversa-audit`, que registrou 7 findings em `audit/cross-check.md`. Os três findings de severidade CRITICAL e HIGH são os que esta sessão fecha.

- **Q:** O `AMB-015` mandava "aceitar e sinalizar", e o parser nunca sinalizou nada. A `RF-19` deve implementar a sinalização, levá-la à tela, ou ser estreitada?
  **R:** **Estreitar a `RF-19`.** A sinalização não existe no legado, não tem consumidor nesta onda e, quando a Onda 3 introduzir o repositório de árvores, teria de ser redesenhada — porque aí ela pertence ao resultado da importação persistida, não ao retorno de um caso de uso. Levá-la à tela está descartado pelo `AMB-015` e pela `RN-04`. O que a `RF-19` passa a dizer é a parte que tem valor e que é verificável: **o arquivo é aceito, a aresta não entra, nenhuma exceção é levantada, e rejeitar é proibido** — nesta onda e nas seguintes, sem requisito próprio. `AMB-015` fecha como comportamento preservado, e a sinalização vai para §10 como questão aberta.
  ⚠️ **Correção de premissa.** A resposta anterior desta mesma data afirmou que a sinalização era devida "como o Designer recomendou". A leitura do `AMB-015` mostra que ele está classificado como `REFERIDO À CODIFICAÇÃO`, com recomendação do Designer **pendente** — nunca aprovada como decisão e nunca implementada. O requisito herdou a palavra "sinalizada" como se descrevesse comportamento existente, e não descrevia. O `AMB-015` continua aberto **na parte da sinalização**, por decisão explícita.
- **Q:** A hierarquia de exceção deve ter cinco tipos, incluindo `ArmazenamentoInvalido`, ou quatro?
  **R:** **Quatro.** `ArmazenamentoInvalido` sai. A razão é factual: a validação de conteúdo devolve **motivo em texto**, não exceção (`src/utils/validate.py`), e é o caso de uso que transforma o motivo na exceção de GEDCOM não reconhecido — logo o adaptador de armazenamento nunca levantaria esse tipo. Mantê-lo criaria superfície sem gatilho, a mesma classe de defeito que a dívida #17 da feature 005 fechou. A falha de armazenamento propriamente dita (chave gerada, object storage, escopo por dono) é outro tipo, com outro gatilho, e pertence à Onda 3. `CsvIlegivel` **entra** com requisito próprio — ele já tinha ponto de levantamento e teste e passava sem requisito que o autorizasse, o que era lacuna de rastreabilidade, não contrato novo.
  **Consequência de implementação registrada.** Cada exceção carrega **apenas a mensagem do seu ponto de detecção**. O `app.py:108` monta hoje `f"Arquivo não reconhecido como GEDCOM: {motivo}."`, mas o `validate.py` devolve só o `motivo`: a exceção carrega o motivo, e a moldura literal fica na tabela de tradução do adaptador. Sem essa separação, texto de tela vazaria para dentro do núcleo.
- **Q:** Onde mora a distinção entre "resultado", "sem resultado" e "erro de entrada", hoje carregada pelo parâmetro `success=` que a `RF-20` proíbe de atravessar a fronteira?
  **R:** Em um **campo de desfecho** do resultado tipado, com **três valores, todos alcançáveis**: `RESULTADO` (sucesso com payload), `SEM_RESULTADO` (sucesso sem payload) e `ERRO_DE_ENTRADA` (falha sinalizada pelo núcleo). O adaptador deriva dele o `success=` do template e o modo de renderização. **Não existe quarto valor para "entrada inválida" em geral:** toda entrada inválida que não vem do núcleo já é exceção de domínio, e exceção interrompe o fluxo em vez de produzir valor de enum — um valor que nenhum caminho preenche seria o mesmo tipo zumbi que esta sessão descartou no `ArmazenamentoInvalido`.
  **Restrição dura que acompanha a decisão.** A **assinatura de retorno do núcleo é congelada**: o harness compara o indicador de sucesso dos fluxos contra o oráculo (`_reversa_sdd/parity/harness.py:211` e `:412`) e nove asserções de teste dependem da tupla de três elementos. O campo de desfecho vive no resultado tipado do caso de uso; o núcleo não é alterado, e o caso de uso lê o que o núcleo já devolve.
  **Decisão descartada e por quê.** Fazer "pessoa não encontrada" virar exceção dentro do núcleo foi considerado e recusado: mudaria o que o harness observa e produziria divergência de paridade.
- **Q:** Os nomes das exceções devem ficar em inglês, como o `paradigm_decision.md` os grafou, ou em português?
  **R:** **Em português** — `PessoaNaoEncontrada`, `GedcomNaoSuportado`, `DnaCsvSemColunas`, `CsvIlegivel`, sob a raiz `ErroDeDominio`. Razão: o vocabulário de domínio do projeto já é em português (`carregar_arvore`, `chave_de_armazenamento`, `nome_do_arquivo_armazenado`, `documentary_relationship`), e misturar os dois idiomas na mesma hierarquia seria pior que a divergência de grafia com o artefato de migração. O `paradigm_decision.md` fica **intacto** — ele nomeia os conceitos em inglês, e a tradução é decisão de implementação, registrada no `investigation.md` §6. Este é o fecho do achado `A004` da auditoria.

## 10. Lacunas

> As três lacunas da versão inicial foram resolvidas na sessão de esclarecimento de 2026-10-07, e as três da auditoria na sessão de auditoria da mesma data. Estão registradas na seção 9.

O que segue **não bloqueia esta feature** e fica registrado para não se perder:

- 🔴 **`AMB-015`, parte da sinalização — referência pendente no GEDCOM.** A recomendação do Designer era aceitar **e sinalizar**, e o legado nunca sinalizou: o parser descarta a aresta em silêncio, sem campo, aviso ou contador. Esta feature preserva o comportamento real e **proíbe** rejeitar (`RF-19`), mas **não** entrega a sinalização. Implementá-la é mudança de comportamento e, pelo Princípio II, exige feature própria — e provavelmente deve nascer junto com o repositório de árvores da Onda 3, porque é lá que o resultado da importação passa a ter existência persistida. Custo a considerar quando chegar a hora: a árvore tem forma congelada (`Tree` de quatro elementos, contrato de paridade), então o sinal **não** pode ser acrescentado a ela.
- 🔴 **`AMB-008` — sinalização de ambiguidade de homônimos.** A decisão de 2026-09-28 manda manter o 1º ID como default **e** sinalizar a ambiguidade no payload. A sinalização não existe hoje: a escolha entre homônimos testa até 5×5 combinações e avisa por texto na mensagem. Se a sinalização tipada entra na fronteira, ela é candidata natural a esta onda; foi declarada fora do escopo nesta sessão. Fica para feature própria ou para a Onda 4, quando o payload passar a ser consumido por cliente que possa desambiguar.
- 🔴 **Dívida #10 — o CSV de DNA não tem validação de conteúdo.** Só a forma do nome é validada, e o arquivo é gravado antes de qualquer verificação de conteúdo — diferente do GEDCOM, que é validado antes de gravar (`RF-10`). Esta feature **preserva** a assimetria de propósito, porque corrigi-la muda comportamento observável e quebra paridade. Pelo Princípio II, a correção é feature própria.

## 11. Histórico de alterações

| Data | Alteração | Autor |
|------|-----------|-------|
| 2026-10-07 | Versão inicial gerada por `/reversa-requirements` | reversa |
| 2026-10-07 | Sessão de esclarecimento: 5 decisões integradas, 3 `[DÚVIDA]` removidas, `RF-19` e `RF-20` acrescentadas, cenários de resultado tipado, de referência pendente e dos três caminhos negativos de upload acrescentados, duas questões não bloqueantes transportadas para §10 | reversa |
| 2026-10-07 | Sessão de auditoria, aberta por `audit/cross-check.md` (7 findings): `A001` fechado estreitando a `RF-19` ao comportamento real e corrigindo a premissa do `AMB-015`; `A002` fechado com `RF-21` nova e a remoção de `ArmazenamentoInvalido`; `A003` fechado com o campo de desfecho de três valores e a restrição dura de que a assinatura do núcleo é congelada. Dois cenários Gherkin reescritos e dois acrescentados | reversa |

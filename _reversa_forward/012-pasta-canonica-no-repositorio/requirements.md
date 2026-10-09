# Requirements: Pasta canônica de uploads dentro do repositório

> Identificador: `012-pasta-canonica-no-repositorio`
> Data: `2026-10-09`
> Pasta da extração reversa: `_reversa_sdd/`
> Confidência: 🟢 CONFIRMADO, 🟡 INFERIDO, 🔴 LACUNA / DÚVIDA

## 1. Resumo executivo

O operador decidiu que os arquivos enviados vivem em **uma única pasta**, dentro do repositório:
`src/uploads`. Esta feature desfaz a decisão `D-01`/`3b` da feature
`010-uploads-fora-do-repositorio` — que declarou uma pasta canônica **fora** da árvore do repositório —
e preserva tudo o que a 010 entregou e **não** depende da localização: a ferramenta de manutenção, o
invólucro que isola o instrumento de paridade e a linha da variável de ambiente na tabela de
configuração. A sessão de esclarecimento de 2026-10-09 mediu que a intenção "só uma pasta" estava mais
longe do que o documento supunha: além da cópia externa, havia **três cópias de arrasto de dado real**
dentro de `_reversa_refactor/` (27 arquivos, 50.762.352 bytes), deixadas ali quando a transformação de
refactor congelou `src/` inteiro. Removê-las passou a fazer parte do escopo. O preço declarado na §6 é
que a pasta é **não rastreada**, e por isso a proteção contra `git clean` passa a ser backup do
operador — decisão explícita de 2026-10-09, sem verbo de backup na ferramenta. O padrão do código
**nunca** deixou de ser `src/uploads`: a 010 não tocou em `src/`.

## 2. Contexto a partir do legado

| Fonte | Trecho relevante | Confidência |
|-------|------------------|-------------|
| `_reversa_sdd/upload-gedcom/contracts.md#2.2` | Padrão da pasta: `<diretório do app>/uploads`, ancorada no arquivo do app e não no diretório corrente; sobreposição por `ANALISADOR_UPLOAD_FOLDER`; criada no **import** pela **mesma** função que a resolve; arquivo de mesma chave não é reescrito; "o sistema **nunca** apaga um arquivo enviado" | 🟢 |
| `_reversa_sdd/inventory.md#5` | "**Arquivos enviados:** gravados em `src/uploads/` (ou no caminho de `ANALISADOR_UPLOAD_FOLDER`) sob **chave derivada do conteúdo** do arquivo, com a extensão original preservada" | 🟢 |
| `_reversa_sdd/inventory.md#4` | Tabela de variáveis de ambiente: `ANALISADOR_UPLOAD_FOLDER` — "Redireciona a pasta de upload; usado pelos testes para não escrever na pasta real" | 🟢 |
| `_reversa_sdd/c4-containers.md#2` | Container 3 — "Sistema de arquivos local `src/uploads/`, arquivos `.ged` e `.csv`, nome = chave de conteúdo + nome visível" | 🟢 |
| `_reversa_sdd/addenda/008-persistencia-postgres-docker.md` | "volume nomeado para o banco e *bind mount* para `src/uploads/`" e "**O leiaute de `src/uploads/`.** Nenhum arquivo precisa ser renomeado ou movido" | 🟢 |
| `_reversa_sdd/addenda/010-uploads-fora-do-repositorio.md` | Adendo **vigente** que esta feature reverte: pasta canônica fora do repositório, 13 impactos declarados sobre a extração | 🟢 |
| `_reversa_sdd/upload-gedcom/design.md` | `_pasta_uploads()` como a função que resolve a pasta, com a variável sobrepondo o padrão | 🟢 |
| `.reversa/principles.md#I` | "Dados reais de DNA/GEDCOM nunca entram no versionamento", em nenhum caminho, incluindo `uploads/` | 🟢 |
| `_reversa_refactor/pacote-reconstructed/transformations/OPP-20261003-RAIZ-distribuir-modulos-soltos/transformation.md` | "Antes de mover qualquer arquivo, `src/` foi copiado inteiro para `before-after/src-antes/`" — **é a causa medida das três cópias de arrasto**; os representantes `FLAT` e `GUE7` repetem a mesma frase nos seus `transformation.md` | 🟢 |

Fora da extração, mas medido para esta feature: `.gitignore:30` (`uploads/`), `.dockerignore:24`
(`src/uploads/`), `docker/Dockerfile:25-26`, `docker-compose.yml:61-67`, `README.md:296-323`,
`tests/conftest.py:154`, `tests/rodar_paridade.py:38`, `tests/test_documentacao_do_upload.py`,
`registrar-diff.py:105-113` (o filtro `endswith(".py")` que ignora `uploads/`) e
`verificar-estrutura.py:269-274` (a lista de pacotes que já exclui `uploads`).

## 3. Personas e cenários de uso

| Persona | Objetivo | Cenário-chave |
|---------|----------|---------------|
| Adriano — operador único, máquina local | Ter o dado de genealogia em um só lugar, sem manter duas pastas sincronizadas à mão | Sobe a aplicação **sem configurar nada** e o arquivo enviado aparece em `src/uploads` |
| Adriano — operador, modo contêiner | Subir a composição e o dado continuar sendo exatamente o mesmo do modo local | `docker compose up` monta a pasta do repositório no alvo interno que o aplicativo já deriva |
| O repositório (versionamento e build) | Nunca versionar dado real nem enviá-lo ao daemon do Docker | `git status` não lista nada de `src/uploads/`, e o contexto de build continua sem a pasta |
| O instrumento de paridade | Medir sem contaminar a pasta do operador | O invólucro define a variável para uma pasta descartável antes de lançar o instrumento (`harness.py`) |
| Adriano — operador, auditoria do próprio repositório | Saber onde há dado real no disco, não só onde o git o mostraria | Uma varredura de `uploads/` em qualquer profundidade devolve **um** diretório, o canônico |

## 4. Regras de negócio novas ou alteradas

1. **RN-01:** A pasta canônica de dados é `<diretório do app>/uploads` — **dentro** da árvore do
   repositório — e é a **única** pasta que recebe arquivos enviados. 🟢
   - Origem no legado: `_reversa_sdd/upload-gedcom/contracts.md#2.2`
   - Tipo: **alterada** — reverte `D-01`/`3b` do `roadmap.md` da feature 010 e a linha
     `delta-de-dados` do adendo 010
2. **RN-02:** `ANALISADOR_UPLOAD_FOLDER` continua existindo como **sobreposição de processo**, e a
   suíte de testes e o instrumento de paridade continuam **obrigados** a usá-la, para que nenhuma
   execução de teste escreva na pasta canônica. 🟢
   - Origem no legado: `_reversa_sdd/inventory.md#4`,
     `_reversa_sdd/upload-gedcom/contracts.md#2.2`, `tests/conftest.py:154`
   - Tipo: alterada — o papel da variável volta a ser o do legado; o que se explicita é a
     obrigação de uso no teste e no instrumento
3. **RN-03:** Duas guardas tornam esta decisão compatível com o Princípio I: o `.gitignore` cobre
   `uploads/` em qualquer profundidade, e o `.dockerignore` reexclui `src/uploads/` do contexto de
   build. **Remover qualquer uma das duas faz esta feature violar o Princípio I.** 🟢
   - Origem no legado: `.reversa/principles.md#I`, `.gitignore:30`, `.dockerignore:24`
   - Tipo: nova
4. **RN-04:** A composição de contêineres monta a pasta do repositório (`./src/uploads`) no alvo
   interno que a aplicação deriva de `__file__` (`/app/src/uploads`), **sem** variável de ambiente
   dentro do contêiner. 🟢
   - Origem no legado: `_reversa_sdd/c4-containers.md#2`,
     `_reversa_sdd/addenda/008-persistencia-postgres-docker.md`, `docker/Dockerfile:25-26`
   - Tipo: alterada — reverte `D-02` da feature 010
5. **RN-05:** O sistema continua **sem apagar** arquivo enviado. Decisão de 2026-10-09: o expurgo do
   resíduo (§9, Q2) é ato do operador, fora do runtime, por manifesto revisável com simulação
   obrigatória, e é a **última** ação desta feature. 🟢
   - Origem no legado: `_reversa_sdd/upload-gedcom/contracts.md#2.2`,
     `_reversa_sdd/state-machines.md#5`
   - Tipo: alterada — a 010 já previa o expurgo por manifesto; o que muda é ele passar a ser
     executado dentro do escopo desta feature, e não ficar pendente
6. **RN-06:** A ferramenta de manutenção mantém os quatro verbos (`migrar`, `manifesto`, `expurgo`,
   `duplicatas`). O verbo `migrar` deixa de ser procedimento recomendado e passa a ser ferramenta de
   cópia avulsa, sem papel no modo de operação. **Nenhum verbo de backup é criado** (§9, Q3): a
   proteção contra `git clean` é documentação mais backup do operador. 🟢
   - Origem no legado: **não há** — a extração não descreve manutenção de pasta. A origem é a
     ferramenta entregue pela feature 010 (`tests/manutencao_de_uploads.py`)
   - Tipo: alterada
7. **RN-07 (guarda de escopo):** esta feature **não** altera `src/`, não muda o padrão de
   `_pasta_uploads()`, não renomeia nem apaga arquivo armazenado, não muda a forma fechada do nome
   (`^[0-9a-f]{16}__[A-Za-z0-9._-]+$`), o teto de 16 MB nem os três valores de `action`. 🟢
   - Origem no legado: `_reversa_sdd/upload-gedcom/contracts.md#2.1`, `#2.2`
   - Tipo: nova
8. **RN-08:** O dado real do operador existe em **um único** diretório: `src/uploads`. Cópias de
   arrasto em artefatos do framework são removidas com inventário medido; a remoção é cancelada se
   qualquer arquivo divergir. Uma varredura de `uploads/` sob a árvore do repositório devolve um
   diretório, o canônico, mais o resíduo sintético de evidência da feature 007 (§10). 🟢
   - Origem no legado: **não há** regra correspondente. A origem é a medição de 2026-10-09 sobre
     `_reversa_refactor/pacote-reconstructed/transformations/OPP-20261003-*/before-after/src-antes/uploads`
   - Tipo: nova
9. **RN-09:** As duas guardas do Princípio I (`RN-03`) são **prendidas por teste automatizado** que
   falha se qualquer uma sair do lugar. Uma guarda que depende de alguém lembrar de olhar duas
   linhas não é guarda. 🟢
   - Origem no legado: `.reversa/principles.md#III` ("nenhuma mudança sem teste que a cubra")
   - Tipo: nova
10. **RN-10:** O `onboarding.md` da feature 010 é **revisado no lugar**, com marcador de revisão e o
    texto antigo preservado, para não ensinar um procedimento que deixou de valer. 🟢
    - Origem no legado: precedente `roadmap.md` `D-02` da feature 004 ("**Revista em 2026-10-04.**")
    - Tipo: nova

## 5. Requisitos Funcionais

| ID | Requisito | Prioridade | Critério de aceite | Confidência |
|----|-----------|------------|--------------------|-------------|
| RF-01 | A composição de contêineres volta a montar a pasta do repositório no alvo interno que o aplicativo deriva | Must | A linha de `volumes:` do serviço `app` declara `./src/uploads:/app/src/uploads`, e nenhum caminho absoluto de host aponta para pasta de uploads. Medido: `git diff HEAD -- docker-compose.yml` fica **vazio** | 🟢 |
| RF-02 | A documentação declara `src/uploads` como a pasta canônica e **única**, e apresenta a variável como sobreposição, não como modo de operação | Must | O `README.md` não chama pasta alguma fora do repositório de canônica, não manda apontar a variável para fora como procedimento de uso, e **mantém** a variável na tabela de configuração | 🟢 |
| RF-03 | A documentação declara as duas guardas do Princípio I e o risco da pasta não rastreada | Must | O `README.md` nomeia `.gitignore` (`uploads/`) e `.dockerignore` (`src/uploads/`) como o que torna a escolha segura, e diz explicitamente que `git clean -xdf` (e `-Xdf`) apaga a pasta | 🟢 |
| RF-04 | A cópia externa é removida **depois** de conferido que a origem tem o mesmo inventário, e só se não houver processo com a pasta em uso | Must | O inventário de `src/uploads` antes e depois é idêntico (36 arquivos, 27.932.474 bytes, mesmo `sha256` por arquivo) e a pasta externa deixa de existir. Divergência em qualquer arquivo **cancela** a remoção | 🟢 |
| RF-05 | Um adendo novo registra a reversão e **supera** o adendo 010 | Must | `_reversa_sdd/addenda/012-*.md` existe, marca `010-*.md` como superado na seção Vigência, e lista, dos 13 impactos do 010, quais deixam de valer e quais permanecem | 🟢 |
| RF-06 | A ferramenta de manutenção permanece íntegra e a suíte não regride | Must | Os quatro verbos continuam respondendo; a suíte não fica abaixo da linha de base medida na 010, `327 passed, 9 skipped` | 🟢 |
| RF-07 | O invólucro de paridade continua sendo o caminho documentado, e o resultado continua total | Must | O `README.md` aponta `tests/rodar_paridade.py`; a execução imprime `PARIDADE 100 %` e **não** deixa arquivo novo em `src/uploads` | 🟢 |
| RF-08 | O teste de documentação continua prendendo a variável na tabela de configuração, com a justificativa atualizada | Should | O teste exige a variável na mesma tabela em que vive `ANALISADOR_HOST`, e o texto do teste deixa de afirmar que é a documentação que mantém a pasta fora do repositório | 🟢 |
| RF-09 | As três cópias de arrasto de dado real dentro de `_reversa_refactor/…/before-after/src-antes/uploads/` são removidas, com inventário medido e cancelável | Must | Os três diretórios deixam de existir; cada um tinha 9 arquivos e 16.920.784 bytes; nenhum arquivo de `src/uploads` muda; nenhuma referência de documento ou instrumento se quebra (medido: zero ocorrências de `src-antes/uploads` no repositório). Divergência em qualquer arquivo **cancela** a remoção | 🟢 |
| RF-10 | O resíduo de instrumento é expurgado por manifesto revisável, **depois** de tudo o mais, com simulação antes da aplicação | Must | A simulação lista os arquivos do manifesto e o inventário fica inalterado; a aplicação remove os 18 arquivos (6.631 bytes) e nenhum outro; o inventário final de `src/uploads` tem 18 arquivos | 🟢 |
| RF-11 | As duas guardas do Princípio I passam a ter teste que falha se qualquer uma sair | Must | Um teste falha se `uploads/` sair do `.gitignore` ou se `src/uploads/` sair do `.dockerignore`; o teste é exercitado por mutação (remover a linha numa cópia e ver falhar) | 🟢 |
| RF-12 | O `onboarding.md` da 010 é revisado no lugar, com marcador de revisão e o texto antigo preservado | Should | O documento traz o marcador de revisão com data, o procedimento correto apontando `src/uploads`, e o registro do que valia antes continua legível | 🟢 |

## 6. Requisitos Não Funcionais

| Tipo | Requisito | Evidência ou justificativa | Confidência |
|------|-----------|----------------------------|-------------|
| Rastreabilidade | A decisão fica registrada com data, motivo e a lista de impactos que deixa de valer, e o adendo superado **permanece legível** | `_reversa_sdd/addenda/` é a memória de decisões do projeto; a convenção é marcar superação, nunca apagar | 🟢 |
| Segurança / Privacidade | Nenhuma cópia do dado real pode aparecer em `git status` nem no contexto de build do contêiner | Princípio I; as guardas são `.gitignore:30` e `.dockerignore:24` | 🟢 |
| Segurança / Privacidade | O passivo de dado real no disco cai de 4 diretórios (78.694.826 bytes) para 1 (27.932.474 bytes) | Medição de 2026-10-09: 36 arquivos em `src/uploads` mais 27 arquivos em três cópias de arrasto. A redução é de 50.762.352 bytes e não altera um byte do dado canônico | 🟢 |
| Reprodutibilidade | A suíte e a paridade mantêm os números medidos antes da mudança | Linha de base da 010: `327 passed, 9 skipped` e `PARIDADE 100 %` nas duas direções | 🟢 |
| Manutenção | A reversão não cria ponto de configuração novo: a pasta continua resolvida **uma vez, no import**, pela mesma função que a cria | `_reversa_sdd/upload-gedcom/contracts.md#2.2` | 🟢 |
| Operação | O risco do `git clean` é **declarado**, não escondido, em um lugar que o operador lê | `uploads/` está no `.gitignore`, então a pasta é não rastreada por construção, não por acidente | 🟢 |
| Escopo | `src/` e `_reversa_sdd/` não mudam de conteúdo | A 010 já provou o caminho: a decisão é de operação e documentação, não de domínio | 🟢 |

## 7. Critérios de Aceitação

```gherkin
Cenário: Uso local sem nenhuma configuração
  Dado que a variável de pasta de uploads não está definida no processo
  Quando o operador sobe a aplicação e envia um GEDCOM
  Então o arquivo aparece em src/uploads sob nome de chave mais nome visível
  E nenhuma outra pasta do sistema recebe cópia

Cenário: Clone novo, sem a pasta de uploads no disco
  Dado um clone do repositório em que src/uploads não existe
  Quando a aplicação é importada
  Então a pasta é criada pela mesma função que a resolve
  E o envio conclui sem erro

Cenário: Composição de contêineres monta a pasta do repositório
  Dado o docker-compose.yml com a linha de volumes do serviço app
  Quando o operador sobe a composição
  Então a pasta canônica do host é ./src/uploads
  E o alvo dentro do contêiner é /app/src/uploads
  E nenhuma variável de ambiente de pasta de uploads é declarada no serviço

Cenário: Remoção da cópia externa preserva o inventário
  Dado que a cópia externa e src/uploads têm o mesmo inventário medido
  Quando o operador remove a cópia externa
  Então o inventário de src/uploads depois é idêntico ao de antes, arquivo a arquivo, por sha256
  E a pasta externa não existe mais

Cenário: Divergência de inventário cancela a remoção
  Dado que ao menos um arquivo da cópia externa difere de src/uploads em tamanho ou sha256
  Quando o operador pede a remoção
  Então a remoção não acontece
  E o relatório nomeia os arquivos divergentes

Cenário: Pasta externa em uso cancela a remoção
  Dado que um processo mantém a pasta externa aberta
  Quando o operador pede a remoção
  Então a remoção não acontece e o relatório nomeia o que impediu
  E src/uploads permanece intacta

Cenário: As três cópias de arrasto saem do repositório
  Dado os três diretórios src-antes/uploads sob _reversa_refactor
  Quando a feature remove as cópias de arrasto
  Então os três diretórios deixam de existir
  E os arquivos de código irmãos em src-antes continuam intactos
  E nenhum arquivo de src/uploads mudou

Cenário: As cópias de arrasto não quebram instrumento nenhum
  Dado que nenhum documento ou instrumento referencia src-antes/uploads
  Quando a remoção termina
  Então registrar-diff.py e verificar-estrutura.py continuam executando sem erro
  E o git status não ganha nenhuma linha nova

Cenário: A documentação ensina a pasta única e declara o risco
  Dado o README.md depois da feature
  Quando o operador procura onde ficam os arquivos enviados
  Então encontra src/uploads declarada como a única pasta canônica
  E encontra a variável de ambiente apresentada como sobreposição
  E encontra nomeadas as guardas do gitignore e do dockerignore
  E encontra o aviso de que git clean apaga a pasta

Cenário: A ferramenta e a suíte continuam inteiras
  Dado o repositório depois da feature
  Quando o operador lista os verbos da ferramenta de manutenção e roda a suíte
  Então os quatro verbos respondem
  E a suíte não fica abaixo de 327 passed, 9 skipped

Cenário: As guardas do Princípio I continuam de pé
  Dado o repositório versionado com uploads/ no gitignore e src/uploads/ no dockerignore
  Quando o operador roda git status e monta o contexto de build
  Então nenhum arquivo de src/uploads aparece como não rastreado a commitar
  E nenhum arquivo de src/uploads entra no contexto de build

Cenário: O teste das guardas falha quando a guarda sai
  Dado o teste que prende as duas linhas de configuração
  Quando uma cópia do repositório perde a linha uploads/ do gitignore
  Então o teste falha nomeando a guarda que saiu
  E o mesmo vale para a linha src/uploads/ do dockerignore

Cenário: A paridade não suja a pasta canônica
  Dado o inventário de src/uploads medido antes da verificação
  Quando o operador roda tests/rodar_paridade.py
  Então a saída termina em PARIDADE 100 %
  E o inventário de src/uploads depois é idêntico ao de antes

Cenário: O expurgo do resíduo é simulado antes de ser aplicado
  Dado o manifesto revisável com 18 arquivos de resíduo de instrumento
  Quando o operador roda o expurgo em simulação
  Então a lista sai completa e o inventário de src/uploads fica inalterado
  E quando o operador aplica, saem exatamente os 18 arquivos e nenhum outro

Cenário: O onboarding deixa de ensinar o procedimento revertido
  Dado o onboarding.md da feature 010
  Quando o operador o lê depois da feature
  Então encontra o marcador de revisão com a data
  E encontra o procedimento correto apontando src/uploads
  E o registro do procedimento anterior continua legível

Cenário: A extração recebe a reversão sem perder o registro anterior
  Dado o adendo 010 vigente
  Quando o adendo 012 é escrito
  Então o adendo 010 passa a declarar-se superado
  E o adendo 010 continua legível, com o seu conteúdo original intacto

Cenário: Guarda de escopo desta feature
  Dado o inventário de src/uploads e o conteúdo de src/ antes da feature
  Quando a feature termina
  Então nenhum arquivo armazenado foi apagado ou renomeado
  E o git diff de src/ e de _reversa_sdd/ está vazio
```

## 8. Prioridade MoSCoW

| Item | MoSCoW | Justificativa |
|------|--------|---------------|
| RF-01 | Must | É a condição para o modo contêiner usar a mesma pasta única do modo local; sem ele, "só uma pasta" é falso no contêiner |
| RF-02 | Must | A documentação é o que sustenta a decisão: o padrão do código já é o desejado, e o README é o único lugar que hoje ensina o contrário |
| RF-03 | Must | Sem as guardas declaradas, a escolha parece insegura quando é segura — e sem o aviso do `git clean` o risco fica invisível |
| RF-04 | Must | É o que torna a decisão verdadeira na prática: enquanto as duas pastas existirem, o dado tem duas verdades |
| RF-05 | Must | Sem o adendo, a extração continua afirmando o contrário do que o projeto faz |
| RF-06 | Must | A ferramenta de manutenção é o que permite expurgar o resíduo; perdê-la prejudicaria a feature 011 |
| RF-07 | Must | O invólucro é a razão de a paridade não recriar o resíduo que a 010 mediu |
| RF-08 | Should | É a prova de que a variável continua documentada; não muda comportamento de runtime |
| RF-09 | Must | É o passivo maior descoberto na sessão: 48 MB de dado real em três lugares que o operador não sabia que existiam |
| RF-10 | Must | É o que faz a lista da feature 011 nascer utilizável: a aba de árvore passa de 16 arquivos / 15 itens para **7 arquivos / 6 itens**; a de DNA, de 19 arquivos / 19 itens para **10 arquivos / 10 itens** |
| RF-11 | Must | É o Princípio III aplicado à única coisa que separa esta decisão de uma exposição de dado real |
| RF-12 | Should | Vale por não deixar um procedimento morto circulando; não muda comportamento de runtime |
| RNF de Operação | Must | O risco do `git clean` é a única desvantagem real da decisão, e o operador precisa conhecê-la |
| RNF de Segurança | Must | É o Princípio I: sem as guardas, manter dado real na árvore do repositório seria exposição |

## 9. Esclarecimentos

### Sessão 2026-10-09

- **Q:** As três cópias de dado real em `_reversa_refactor/…/before-after/src-antes/uploads/`
  (27 arquivos, 50.762.352 bytes) — o que fazer?
  **R:** Entram na 012: remover as três com inventário medido. Medição que sustenta a decisão:
  nenhum arquivo de `uploads/` está rastreado pelo git; os 19 `.ged`/`.csv` versionados são fixtures
  sintéticas de 26 a 606 bytes; `.dockerignore` é lista de permissão e nunca incluiu
  `_reversa_refactor/**`; e as 30 ocorrências de `before-after/src-antes` no repositório apontam
  todas para `.py`, nenhuma para `uploads/`. `registrar-diff.py` filtra `endswith(".py")` e
  `verificar-estrutura.py:271` já exclui `uploads` da lista de pacotes.
- **Q:** O expurgo do resíduo de instrumento (18 arquivos, 6.631 bytes em `src/uploads`) entra no
  escopo da 012 ou fica no passo 11 da 010?
  **R:** Entra na 012, como **última** ação. É o que faz a lista da feature 011 nascer utilizável —
  e as duas unidades precisam ser ditas, porque são diferentes: a aba de árvore passa de **16
  arquivos / 15 itens** para **7 arquivos / 6 itens** (dois arquivos compartilham a chave
  `080e7943572d2652`), e a aba de DNA passa de **19 arquivos / 19 itens** para **10 arquivos / 10
  itens**. Contar só "itens" ou só "arquivos" esconde metade do efeito.
- **Q:** Como se proteger do risco de `git clean -xdf` apagar `src/uploads`?
  **R:** Só documentação mais backup periódico do operador. Nenhum verbo de backup é criado na
  ferramenta: um verbo desses reabriria a dúvida sobre qual pasta é a fonte de leitura, que é
  exatamente o problema que esta feature fecha.
- **Q:** As duas guardas do Princípio I passam a ter teste automatizado?
  **R:** Sim: um teste que falha se `uploads/` sair do `.gitignore` ou se `src/uploads/` sair do
  `.dockerignore`, exercitado por mutação. Sustenta-se no Princípio III — uma guarda que depende de
  alguém lembrar de olhar duas linhas não é guarda.
- **Q:** O `onboarding.md` da 010, que ensina o procedimento revertido, é revisado no lugar?
  **R:** Revisado no lugar, com marcador de revisão e o texto antigo preservado. Precedente do
  projeto: a `D-02` da feature 004 foi revista com "**Revista em 2026-10-04.**", mantendo o registro.

## 10. Lacunas

Nenhuma lacuna aberta. As três dúvidas do documento inicial foram resolvidas na sessão de
2026-10-09 (§9), e as decisões viraram as regras `RN-08` a `RN-10` e os requisitos `RF-09` a `RF-12`.

### Notas medidas, declaradas (não são dúvidas)

- `src/uploads` tem **36 arquivos e 27.932.474 bytes**: 16 com extensão `.ged` e 19 com `.csv`.
- `D:\dados-genealogicos\uploads` tem exatamente os **mesmos 36 arquivos**, com os mesmos nomes e os
  mesmos `sha256`, e os mesmos 27.932.474 bytes. **Já removida** em 2026-10-09, por ordem explícita do
  operador, com o inventário conferido antes e depois (`evidence/remocao-da-copia-externa.txt`,
  exit code 0): a origem ficou idêntica, arquivo a arquivo. O diretório-pai `D:\dados-genealogicos`
  ficou no disco, **vazio** (0 itens), e não foi removido: a ordem era sobre os arquivos.
- As **três cópias de arrasto** somam **27 arquivos e 50.762.352 bytes** (9 arquivos e 16.920.784
  bytes cada). Contêm dado real, inclusive
  `080e7943572d2652__Arvore_Unificada_Oficial_V1_2.ged` (5.332.198 bytes) e `Adriano_Santos.ged`
  (3.063.082 bytes). **Ainda não removidas** — a remoção é escopo do `RF-09`, no estágio de coding.
- O resíduo de instrumento (**18 arquivos, 6.631 bytes**) está em `src/uploads`, porque a 010 copiou
  a pasta inteira. **Ainda não expurgado** — é escopo do `RF-10`, e é a última ação da feature.
- `_reversa_forward/007-dono-no-port-e-baseline/evidence/_tmp_e2e/uploads` tem 2 arquivos e 587
  bytes (`arvore.ged` de 561 bytes e `matches.csv` de 26 bytes): são **sondas sintéticas** da
  verificação manual da 007, não dado real. Ficam como estão — a `RN-08` os declara como a exceção
  sintética da varredura.
- O adendo `008-persistencia-postgres-docker.md` volta a estar **integralmente correto** com a
  reversão: ele já afirmava "*bind mount* para `src/uploads/`" e "nenhum arquivo precisa ser
  renomeado ou movido".
- O comentário do `docker/Dockerfile` (`:25-26`) **não** nomeia caminho de host: ele afirma que a
  pasta dentro do contêiner é `/app/src/uploads` e que é ali que a composição monta o *bind*. Ele
  permanece verdadeiro sem edição — o que muda é só o lado do host.
- `.dockerignore` é **lista de permissão** com reexclusão explícita de `src/uploads/` (`:24`). Ou
  seja, manter a pasta dentro do repositório **não** envia dado real ao daemon do Docker: era um
  risco considerado, e ele já está fechado por uma linha que existe desde a feature 008.
- `ANALISADOR_UPLOAD_FOLDER` **não pode ser removida**: `tests/conftest.py:154` e
  `tests/rodar_paridade.py:38` dependem dela para não escreverem na pasta real. Removê-la faria a
  suíte gravar na pasta de dados do operador — exatamente o resíduo que a 010 mediu.
- A pasta é resolvida **uma vez, no import**. Uma instância já no ar com a variável apontando para a
  pasta externa a mantém em uso: é por isso que o `RF-04` condiciona a remoção a não haver processo
  com a pasta aberta. Conferido antes da remoção: nenhum processo `python` de pé e nada escutando nas
  portas 5000 e 5080.
- A 010 **não** alterou `src/`: o `git diff` de `src/` está vazio desde então. O que a 010 alterou foi
  `docker-compose.yml`, `README.md` e artefatos do Reversa.
- **Achado defasado na extração:** `_reversa_sdd/inventory.md:182` afirma "15 arquivos em
  `src/uploads/` e 4 em `uploads/` (local legado da raiz, anterior à ancoragem)". Medido em
  2026-10-09: nem `uploads/` nem `analisador-genealogico/uploads/` existem. A contagem também está
  velha (hoje são 36). Não corrigido aqui — `_reversa_sdd/` é do `/reversa`, e a `RN-07` proíbe esta
  feature de tocá-lo.
- **Achado de ambiente, fora do escopo desta feature:** `DATABASE_URL` está definido **no ambiente do
  processo** desta sessão (apontando para `db:5432`, o nome do serviço do compose), embora não esteja
  definido nas variáveis de usuário nem de máquina do Windows, e `psycopg2` **não** está instalado no
  `.venv`. Com a variável presente, `tests/test_persistencia_desabilitada.py` falha em 2 testes
  (`325 passed, 2 failed, 9 skipped`); sem ela, a suíte dá exatamente a linha de base da 010
  (`327 passed, 9 skipped`). **Nenhuma regressão desta feature.** Fica declarado porque é atrito real
  para quem opera o Postgres no próprio shell, e o rastreamento correto é `/reversa-debugger`.

## 11. Histórico de alterações

| Data | Alteração | Autor |
|------|-----------|-------|
| 2026-10-09 | Versão inicial gerada por `/reversa-requirements` | reversa |
| 2026-10-09 | Sessão de dúvidas: 5 perguntas respondidas; 3 dúvidas resolvidas; `RN-08` a `RN-10` e `RF-09` a `RF-12` acrescentados | reversa |
| 2026-10-09 | Correção de unidade nas contagens do expurgo: "itens" (agrupados pela chave do nome) e "arquivos" são números diferentes, e a §8 e a §9 misturavam os dois. Medido no estágio de plano: árvore 16/15 → 7/6; DNA 19/19 → 10/10 | reversa |

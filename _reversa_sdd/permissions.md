# Permissões e Papéis (RBAC/ACL) — analisador-genealogico

> Nível de documentação: **Completo** (`state.json` → `doc_level`) — este artefato é gerado neste nível **mesmo quando o resultado é a ausência total** de RBAC, porque a ausência tem consequência de negócio e precisa ficar registrada com evidência.
> Re-extração de **2026-10-10**. Substitui o artefato de 2026-10-05, que descrevia o estado global do GEDCOM, a corrida entre threads como vetor vivo e a ausência de qualquer coluna de dono.
> Snapshot da versão substituída: `.reversa/snapshots/2026-10-10-pre-reextracao/permissions.md`
> Escala de confiança: 🟢 CONFIRMADO | 🟡 INFERIDO | 🔴 LACUNA

---

## 1. Resultado da Varredura

**Método.** Varredura de `src/` inteiro pelos termos `session`, `login`, `logout`, `password`, `current_user`, `role`, `permission`, `authenticat`, `authoriz`, `token`, `login_required`, `owner`; inspeção dos imports de `src/app.py`; procura por entidade de usuário e por qualquer noção de dono do dado — **agora também no esquema do banco** (`init.sql`) e nas assinaturas das quatro portas.

| Verificação | Resultado | Evidência | Conf. |
| --- | --- | --- | --- |
| Login / autenticação | **inexistente** | zero ocorrências de `login`, `authenticat`, `password` em `src/` | 🟢 |
| Sessão de usuário | **inexistente** | `flask.session` **nunca é importado**; o import é `from flask import Flask, render_template, request, send_file` (`app.py:6`) | 🟢 |
| Papéis / permissões | **inexistente** | zero ocorrências de `role`, `permission`, `authoriz`, `token`, `login_required` | 🟢 |
| Entidade de usuário | **inexistente** | nenhuma tabela, dataclass ou dicionário de usuário — nem em `src/`, nem em `init.sql` | 🟢 |
| Propriedade do dado (`owner_id`) | **EXISTE COMO COLUNA E COMO PARÂMETRO, e não FILTRA nada** | `init.sql:26` cria `owner_id TEXT NOT NULL`; nenhuma consulta tem `WHERE owner_id` (`RN-10`) | 🟢 |
| Autorização por recurso | **inexistente** | nenhuma verificação de propriedade antes de carregar a árvore endereçada por `gedcom_filename` | 🟢 |
| Registro de auditoria | **parcial, e não é de acesso** | o que existe é o **histórico da análise** (`dna_analysis`), que grava *o que foi analisado* e não *quem acessou* | 🟢 |
| Caminho de escrita de identidade | **um único literal, sem consumidor** | `DONO_DO_PROCESSO = "unico"` (`app.py:70`) | 🟢 |

**Falsos positivos descartados (para que a varredura seja reproduzível):** as ocorrências dos termos-chave continuam divididas em três grupos que **não** são controle de acesso — atributos **HTML de acessibilidade** (`role="alert"`, `role="tab"`, `role="tabpanel"`, `role="status"` em `templates/index.html`), funções de **tokenização de nomes** (`top_given_tokens`, `token_prefixes`, `drop_short_tokens`, `surname_core_tokens`) e o substantivo "token" em comentários sobre a **gramática do Mermaid** (`reporting/mermaid_render.py`). 🟢

### 1.1 A mudança estrutural desta rodada: `dono` existe, e não isola

A rodada anterior registrava que não havia **nenhuma** noção de dono. Hoje existe, em três lugares, e a conclusão de negócio **não mudou**:

| Onde | Forma | Comportamento |
| --- | --- | --- |
| Assinatura das portas | `dono: str` obrigatório em `guardar`, `resolver`, `listar`, `aposentar`, `carregar` e nos dois métodos de `RepositorioDeArvores` | Chega por chamada, e **não** pela construção do adaptador |
| Adaptador de armazenamento | parâmetro **ignorado** nos quatro métodos | Não entra na chave, no nome armazenado nem no caminho. Dois envios do mesmo conteúdo por donos diferentes reencontram o **mesmo** arquivo (`RN-02`) |
| Coluna do banco | `dna_analysis.owner_id TEXT NOT NULL` | Vira **dado gravado**, e nenhuma consulta filtra por ele (`RN-10`). Nenhum índice começa por `owner_id` |

**Leitura correta:** o `dono` é **costura de assinatura**, e não funcionalidade. Ele existe porque a Onda 3 teria de reabrir **toda** assinatura de porta e **todos** os chamadores para acrescentá-lo depois — o custo que a feature `007-dono-no-port-e-baseline` pagou para não ter. Nenhuma entrega pode ser citada como tendo implementado isolamento. 🟢

---

## 2. Papéis

**Nenhum papel existe.** O sistema tem **um único ator implícito** — quem alcança a porta —, sem identidade, sem nome, sem credencial e sem distinção.

| Pergunta de negócio | Resposta | Conf. |
| --- | --- | --- |
| Quantos papéis o sistema define? | **Zero.** | 🟢 |
| Como um papel é atribuído? | Não é — não há mecanismo de atribuição. | 🟢 |
| Como um papel é revogado? | Não é — não há credencial a revogar. | 🟢 |
| Existe usuário com privilégio diferente? | Não. Todos os atores são indistinguíveis. | 🟢 |
| Existe "dono" do dado? | **Existe o registro do dono, e nenhuma consequência dele.** O dado não pertence a ninguém no sistema. | 🟢 |

---

## 3. Matriz de Permissões

A matriz continua deliberadamente **degenerada**: uma linha só, e "permitido" em todas as células de acesso. Ela ganhou as rotas e ações que nasceram desde 2026-10-05.

| Ator (único) | `GET /` | `GET /banner.png` | `GET /apple-touch-icon.png` | `POST upload_gedcom` | `POST aposentar_arquivo` | `POST selecionar_arvore` | `POST dna_analysis` | `POST path_search` | Ler arquivo de outro dono | Subir 2ª instância |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Qualquer processo que alcance a porta | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ **se conhecer a chave** | ❌ recusado |

> **Escopo do "✅"**: todas as permissões valem para **qualquer** solicitante, sem credencial. As duas únicas colunas negadas são proteção de **integridade**, não de acesso: a segunda instância na mesma porta, e — no caso do `POST /` — a recusa de escrita nas rotas de arte, que é feita pelo **roteador** (`405`), porque elas são registradas só com `GET`.

---

## 4. O que Existe no Lugar de Autenticação

### 4.1 A chave de conteúdo como identificador de continuidade

Sem sessão, a continuidade entre requisições é carregada **no próprio formulário**:

1. No upload, o servidor deriva `chave = sha256(conteúdo)[:16]` e grava o arquivo como `<chave>__<nome visível>`.
2. A tela devolve ao navegador o campo oculto `gedcom_filename` (e, desde a feature 011, `matches_csv_filename`) com esse valor.
3. **Em todo `POST` seguinte, o servidor remonta a árvore a partir da referência recebida, antes de qualquer ramificação.**

**A chave de conteúdo desempenha o papel que uma sessão desempenharia** — e desempenha melhor em um aspecto: como é derivada do conteúdo, a mesma árvore reenviada produz a mesma chave, e o arquivo não é duplicado. Continua **sendo entregue ao navegador**: ela não é segredo, é identificador. 🟢

### 4.2 A defesa contra escape ficou mais permissiva, e a razão está medida

A rodada anterior descrevia a forma **fechada** (`^[0-9a-f]{16}__[A-Za-z0-9._-]+$`) como a defesa contra escape. **Isso deixou de valer em 2026-10-10:** o alfabeto recusava **acento e espaço**, que o gravador **preserva de propósito** (`RF-06`), e três arquivos com acento e um com espaço ficaram inalcançáveis — a tela dizia que não existiam (`BUG-20261009-6RKP` / `RN-20`).

A defesa passou a ser a **forma de NOME**, em duas funções com perguntas distintas:

| Função | Pergunta | Critério |
| --- | --- | --- |
| `_PREFIXO_CHAVE` / `chave_recebida_e_valida` | "tem chave?" | Exige a forma `<16 hex>__<nome>` — é o que `resolver` usa para **ler** |
| `referencia_de_arquivo_da_pasta` | "posso tratar como nome da pasta?" | Recusa caminho: barra, barra invertida, NUL, `.`, `..`, vazio, e o valor tem de ser `basename` de si mesmo. É o que `aposentar` usa |

**O afrouxamento é do `aposentar`, e é deliberado:** os arquivos **sem chave** são justamente os que o operador mais quer tirar da lista, e exigir a chave ali os tornaria inapagáveis. `resolver` **não** afrouxou. 🟢

### 4.3 Cobertura — e o que mudou desde 2026-10-05

| Dimensão | Cobertura | Mecanismo / limite |
| --- | --- | --- |
| **Escape de diretório** | ✅ **coberto** | Forma de NOME (sem separador de caminho, NUL, `.` ou `..`), aplicada **antes** de qualquer `os.path.exists`; e, no `aposentar`, uma segunda camada que confere que o `dirname` do caminho resolvido é exatamente a pasta de upload |
| **Colisão entre envios** | ✅ **coberto** | O nome do cliente nunca compõe o caminho; a chave vem do conteúdo |
| **Tamanho do corpo** | ✅ **coberto** | Teto de 16 MB com `HTTP 413` **antes** de gravar qualquer byte |
| **Conteúdo não-GEDCOM** | ✅ **parcial** | Só `0 HEAD` é verificado, e **apenas o GEDCOM passa por isso**: o CSV **não** tem validação de conteúdo (dívida preservada). A mensagem de recusa passou a ser **fixa** (`RN-18`), e o motivo segue dentro da exceção |
| **Autenticação** | ❌ **não coberto** | Não há como provar quem é o solicitante |
| **Autorização / propriedade** | ❌ **não coberto** | Nada verifica se a referência pertence a quem a apresenta. **A chave é portadora do acesso** |
| **Segredo da chave** | ❌ **não coberto** | A chave é entregue ao navegador em campo oculto. Não é segredo; é identificador |
| **Isolamento entre árvores** | ✅ **COBERTO desde a feature 005** | **Não há mais estado global.** A árvore é um **valor** devolvido por `carregar_arvore` e passada por parâmetro em todo o núcleo. Ver §4.4 |
| **Confidencialidade dos dados** | ❌ **não coberto** | `all_names` — a lista completa de nomes — continua embutida no HTML de resposta |
| **Confidencialidade do banco** | ❌ **não coberto, e é novo** | `DATABASE_URL` traz usuário e senha em claro no `.env`; o Postgres escuta em `127.0.0.1:5432` e não há TLS. Ver `P-06` |

### 4.4 A corrida entre requisições MUDOU DE NATUREZA — e a parte que a definia foi fechada

A rodada anterior registrava, como vetor **vivo**, esta sequência com duas requisições simultâneas:

```text
Thread A: parseia a árvore A   →  estado global = A
Thread B: parseia a árvore B   →  estado global = B
Thread A: segue o fluxo lendo o estado global  →  lê B   ← contaminação
```

**Essa sequência deixou de ser possível.** A feature `005-nucleo-puro-src` removeu o módulo de estado (`src/core/gedcom_state.py`, apagado no `T023`) e fez a árvore entrar **por parâmetro** em todo o núcleo: cada requisição constrói a **sua** árvore e a carrega consigo até o fim. Não existe mais variável de módulo que uma thread possa sobrescrever para outra. **A guarda de instância única deixou de ter esse motivo** — ela permanece pelo armazenamento em disco, e o código registra isso. 🟢

**O que permanece, e é outra corrida:** o **armazenamento em disco** continua único por processo. Duas requisições que gravem ou movam arquivos ao mesmo tempo ainda podem intercalar (ex.: `aposentar` verifica a existência do destino e depois move). É a dívida #3, e ela **não** é de identidade — é de concorrência de sistema de arquivos. 🟢 *(mecanismo)* / 🟡 *(alcance não medido)*

### 4.5 Divergência registrada contra o `BUG-20260929-BJJH`

O registro do bug (crítico, P0) descreve o sintoma nos "Steps to Reproduce": *"Em outra sessão, carregue um GEDCOM diferente. O parse substitui o estado global do processo. Volte à sessão A e repita a busca: o resultado é calculado sobre a árvore da segunda sessão."*

**Esse passo não se reproduz no código de 2026-10-10 — e agora não por causa do re-parse, e sim porque o estado global não existe.** Cada `POST` monta a sua árvore a partir da referência que trouxe.

| Vetor | Estado atual | Conf. |
| --- | --- | --- |
| Sessão A vê a árvore de B por "última carga vence" | ❌ **estruturalmente impossível** — não há estado compartilhado | 🟢 |
| Quem conhece (ou obtém) a chave carrega a árvore alheia | ✅ **permanece** — não há verificação de propriedade | 🟢 |
| Requisições concorrentes corrompem o armazenamento em disco | ✅ **permanece** — dívida #3, e não é de identidade | 🟡 |
| `all_names` expõe a lista completa de nomes a quem carrega a árvore | ✅ **permanece** | 🟢 |
| O histórico da análise é gravado com `owner_id` de um dono único | ✅ **permanece, e é novo** | 🟢 |

> **Registro correto, para não se trabalhar sobre premissa morta:** o `BUG-20260929-BJJH` **não foi encerrado nem invalidado** — o critério de aceite dele ("duas sessões nunca compartilham árvore; requisição a árvore de outro dono responde 404") continua **não atendido**: a primeira metade virou verdade por construção, a segunda continua falsa porque não há identidade para comparar.

---

## 5. Consequências de Negócio

1. **Todo dado genealógico continua, na prática, público para quem alcança a porta.** Nome, sexo, datas e locais de nascimento e morte, filiação e cônjuges — inclusive de **pessoas vivas** — são exibidos a qualquer solicitante. É dado pessoal sob LGPD/GDPR, e o sistema não tem base para distinguir titular, finalidade ou consentimento. 🟢
2. **Não há como atender a um pedido de exclusão ou de portabilidade.** Nada associa dado a titular. O que existe agora é um **histórico de análises** que guarda *xref*, *nome*, *sexo*, *nascimento*, *local de nascimento* e *falecimento* das pessoas usadas — ou seja, o sistema **passou a persistir dado pessoal** que antes só existia em memória. A consequência é nova nesta rodada e agrava a anterior: apagar a árvore já não apaga o retrato. 🟢
3. **A exposição depende do ambiente, e o padrão segue endurecido.** A aplicação escuta em `127.0.0.1` por padrão (`ANALISADOR_HOST`); no `docker-compose.yml` as duas portas são publicadas **em `127.0.0.1`** (`5080:5000` e `5432:5432`). Abrir para a rede é ato explícito. 🟢
4. **O aceite de risco está vigente e é declarado, não presumido.** A mitigação de 2026-10-04 no `BUG-20260929-BJJH` é `kind: risk-acceptance`, `temporary: true`, e a condição que **reabre** o assunto está nomeada no próprio registro: *"se qualquer pessoa além de Adriano passar a ter acesso à aplicação antes da Onda 3"*. 🟢
5. **A mitigação ganhou duas garantias técnicas novas:** a árvore por requisição (§4.4) e a recusa de segunda instância. O que antes dependia de disciplina de comportamento passou a depender de construção. 🟢
6. **O alvo da migração já especifica a correção, e ela não é opcional:** `migration/risk_register.md#risk-005` exige `owner_id` como **invariante do aggregate**, repositório **sempre escopado** na assinatura e **teste negativo obrigatório** (usuário A acessando recurso de B recebe **404**, não 403) como **portão de go-live**. A coluna `owner_id` que a feature 008 criou **não** satisfaz esse requisito: ela grava o dono e não filtra por ele. 🟢

---

## 6. Lacunas 🔴

| ID | Lacuna | Conf. |
| --- | --- | --- |
| **P-01** | ✅ **DECIDIDA (2026-10-05) — é OMISSÃO, não requisito.** A correção pertence à **Onda 3**: `owner_id` como invariante, repositório escopado e teste negativo de 404 como portão de go-live. **Nada é alterado no legado.** O que mudou nesta rodada: a infraestrutura para a Onda 3 **já existe** (o parâmetro nas portas e a coluna no banco), e continua **sem comportamento**. | 🟢 |
| **P-02** | **O alcance da corrida de armazenamento não foi medido.** A contaminação de árvore entre threads (§4.4) deixou de existir; o que resta é concorrência sobre o sistema de arquivos. Não se sabe se já produziu efeito em uso real, nem a janela com 4 threads. | 🟡 |
| **P-03** | ✅ **DECIDIDA (2026-10-05) — a exposição deve ser RESTRINGIDA, e a implementação pertence ao ALVO.** `all_names` continua embutida em cada resposta; removê-la hoje quebraria a busca sem substituto. A restrição exige **busca no servidor** (Onda 4/SPA), registrada em `gaps.md`. | 🟢 |
| **P-04** | ✅ **FECHADA (2026-10-05)** — `app.secret_key` foi removida. **Reconferido em 2026-10-10:** o símbolo não existe em `src/`, e o comentário que registra a decisão permanece no lugar da linha. | 🟢 |
| **P-05** | ✅ **DECIDIDA (2026-10-05) — é assimetria HERDADA, a corrigir no ALVO.** Validar o CSV no legado rejeitaria arquivos que a leitura tolerante aceita. **Reconferido em 2026-10-10:** `guardar` continua validando só quando `tipo == "gedcom"`. | 🟢 |
| **P-06** | 🔴 **NOVA: credencial de banco em claro e sem TLS.** O `.env` traz usuário, senha, nome do banco e a `DATABASE_URL` completa. Ele está no `.gitignore` e **não** entra na imagem (o `.dockerignore` é lista de permissão), mas é lido pelo `docker-compose` do host. Não há TLS nem rotação, e a senha é de um Postgres que publica a porta em `127.0.0.1`. **Nenhum valor foi transcrito para os artefatos.** | 🟢 |
| **P-07** | 🔴 **NOVA: o histórico da análise persiste dado pessoal que antes era efêmero.** `analysis_person` guarda xref, nome, sexo, nascimento, local de nascimento e falecimento — inclusive de **pessoas vivas** — e não há política de retenção, expurgo nem consentimento. Não há tabela de retenção no esquema (`data_retention_policy` existe no DDL do alvo e **não** foi criada). | 🟢 |
| **P-08** | 🟡 **NOVA: as duas rotas de arte são públicas e não verificam origem.** Não expõem dado pessoal — servem dois PNG do próprio projeto —, mas `send_file` responde a qualquer solicitante e o `ETag` permite revalidação barata. Registrado para que a varredura de superfície fique completa: **7 rotas, nenhuma com credencial**. | 🟢 |

---

*Gerado pelo Reversa-Detective em 2026-10-10 (re-extração, nível completo).*

# Permissões e Papéis (RBAC/ACL) — analisador-genealogico

> Nível de documentação: **Completo** (`state.json` → `doc_level`) — este artefato é gerado neste nível **mesmo quando o resultado é a ausência total** de RBAC, porque a ausência tem consequência de negócio e precisa ficar registrada com evidência.
> Re-extração de **2026-10-05**. Não existia nas extrações anteriores (em 2026-09-30 a conclusão ficou embutida em `domain.md` §6).
> Escala de confiança: 🟢 CONFIRMADO | 🟡 INFERIDO | 🔴 LACUNA

---

## 1. Resultado da Varredura

**Método.** Varredura de `src/` inteiro pelos termos `session`, `login`, `logout`, `password`, `current_user`, `role`, `permission`, `authenticat`, `authoriz`, `token`, `login_required`; inspeção dos imports de `src/app.py`; procura por entidade de usuário, `owner_id` e qualquer noção de dono do dado.

| Verificação | Resultado | Evidência | Conf. |
| --- | --- | --- | --- |
| Login / autenticação | **inexistente** | zero ocorrências de `login`, `authenticat`, `password` em `src/` | 🟢 |
| Sessão de usuário | **inexistente** | `flask.session` **nunca é importado**; o import é `from flask import Flask, render_template, request` (`app.py:6`) | 🟢 |
| Papéis / permissões | **inexistente** | zero ocorrências de `role`, `permission`, `authoriz`, `token`, `login_required` | 🟢 |
| Entidade de usuário | **inexistente** | nenhuma tabela, dataclass ou dicionário de usuário em `src/` | 🟢 |
| Propriedade do dado (`owner_id`) | **inexistente** | nenhuma referência; a pasta `uploads/` é única e o arquivo não registra quem o enviou | 🟢 |
| Autorização por recurso | **inexistente** | nenhuma verificação de propriedade antes de abrir o arquivo endereçado por `gedcom_filename` | 🟢 |
| Registro de auditoria | **inexistente** | nada é gravado sobre quem fez o quê; o único artefato é o arquivo enviado | 🟢 |

**Falsos positivos descartados (para que a varredura seja reproduzível):** as 44 ocorrências dos termos-chave dividem-se em três grupos que **não** são controle de acesso — atributos **HTML de acessibilidade** (`role="alert"`, `role="tab"`, `role="tabpanel"`, `role="presentation"`, `role="status"` em `templates/index.html`), funções de **tokenização de nomes** (`top_given_tokens`, `token_prefixes`, `drop_short_tokens`, `surname_core_tokens`) e o substantivo "token" em comentários sobre a **gramática do Mermaid** (`reporting/mermaid_render.py:39`). 🟢

### 1.1 Configuração morta: `app.secret_key` — ✅ REMOVIDA em 2026-10-05

`src/app.py:22` definia `app.secret_key = 'f@milyse@rch_dna_edition_v16'` — segredo **embutido no código e versionado**. Ele existe para assinar cookie de sessão, e **não há sessão**: `flask.session` nunca foi importado, nenhum cookie era emitido e nada o consumia em todo o `src/`.

**Leitura correta:** não era um controle de acesso desativado — era **configuração sem consumidor**, herdada do legado. Duas consequências: (a) o valor versionado era um passivo de higiene, não um risco explorável *enquanto não houvesse sessão*; (b) no instante em que alguém introduzisse `session` para resolver o isolamento (a Rota 2 descartada do `BUG-20260929-BJJH`), esse literal passaria a ser a **chave de forja de sessão de todo usuário**, porque está no repositório. 🟢

> ✅ **RESOLVIDO em 2026-10-05.** Você decidiu **remover a linha**, e ela foi removida de `src/app.py`. Em seu lugar ficou um comentário registrando a decisão e o motivo. **Nenhum consumidor foi afetado** — confirmado por varredura: `flask.session` não é importado em nenhum arquivo, não há `flash()` e nenhum teste referencia `secret_key`. O `app` continua importando e servindo normalmente. `P-04` está **fechada**. 🟢

---

## 2. Papéis

**Nenhum papel existe.** O sistema tem **um único ator implícito** — quem alcança a porta —, sem identidade, sem nome, sem credencial e sem distinção. Não há usuário administrador, operador, leitor ou convidado.

| Pergunta de negócio | Resposta | Conf. |
| --- | --- | --- |
| Quantos papéis o sistema define? | **Zero.** | 🟢 |
| Como um papel é atribuído? | Não é — não há mecanismo de atribuição. | 🟢 |
| Como um papel é revogado? | Não é — não há credencial a revogar. | 🟢 |
| Existe usuário com privilégio diferente? | Não. Todos os atores são indistinguíveis. | 🟢 |
| Existe "dono" do dado? | Não. O dado genealógico não pertence a ninguém no sistema. | 🟢 |

---

## 3. Matriz de Permissões

A matriz é deliberadamente **degenerada**: como não há papéis, ela tem uma linha só, e a resposta é "permitido" em todas as células. Registrá-la assim é mais honesto do que omiti-la — é o retrato exato do modelo de acesso atual.

| Ator (único) | `GET /` | `POST action=upload_gedcom` | `POST action=dna_analysis` | `POST action=path_search` | Ler arquivo de outra pessoa | Subir segunda instância |
| --- | --- | --- | --- | --- | --- | --- |
| Qualquer processo que alcance a porta | ✅ | ✅ | ✅ | ✅ | ✅ **se conhecer a chave** | ❌ recusado |

> **Escopo do "✅"**: todas as permissões valem para **qualquer** solicitante, sem credencial. A única coluna negada — subir uma segunda instância na mesma porta e endereço — é proteção de **integridade de estado**, não de acesso (ver `permissions.md` §4.3).

---

## 4. O que Existe no Lugar de Autenticação

O sistema **não é desprotegido por descuido** em todos os eixos: ele tem uma defesa real, e é essencial entender exatamente o que ela cobre e o que não cobre.

### 4.1 A chave de conteúdo como identificador de continuidade

Como não há sessão, a continuidade entre requisições é carregada **no próprio formulário**:

1. No upload, o servidor deriva `chave = sha256(conteúdo)[:16]` e grava o arquivo como `<chave>__<nome visível>` (`utils/validate.py:68-75`).
2. A tela devolve ao navegador o campo oculto `gedcom_filename` com esse valor.
3. **Em todo `POST` seguinte, o servidor re-parseia o GEDCOM a partir da chave recebida, antes de qualquer ramificação** (`app.py:131-137`).

**Ou seja: a chave de conteúdo desempenha o papel que uma sessão desempenharia** — e desempenha melhor em um aspecto: como é derivada do conteúdo, a mesma árvore reenviada produz a mesma chave, e o arquivo não é duplicado.

### 4.2 O que esta defesa cobre — e o que não cobre

| Dimensão | Cobertura | Mecanismo / limite |
| --- | --- | --- |
| **Escape de diretório** | ✅ **coberto** | A validação é por **forma fechada** (`^[0-9a-f]{16}__[A-Za-z0-9._-]+$`, `validate.py:32`), que exclui `/`, `\` e `..`. Um valor manipulado **não tem como** apontar para fora da pasta de upload. Não depende de lista negra. |
| **Colisão entre envios** | ✅ **coberto** | O nome do cliente **nunca** compõe o caminho; a chave vem do conteúdo. Antes, dois envios com o mesmo nome de arquivo se sobrescreviam em silêncio. |
| **Tamanho do corpo** | ✅ **coberto** | Teto de 16 MB com `HTTP 413` **antes** de gravar qualquer byte (`app.py:32`, `:65-72`). |
| **Conteúdo não-GEDCOM** | ✅ **parcial** | Só a **declaração de cabeçalho** `0 HEAD` é verificada — a gramática fica com o `ged4py` (`RISK-007` autoriza o relaxamento). E **apenas o GEDCOM passa por isso**: o CSV de DNA **não** tem validação de conteúdo (`app.py:86`). |
| **Autenticação** | ❌ **não coberto** | Não há como provar quem é o solicitante. |
| **Autorização / propriedade** | ❌ **não coberto** | Nada verifica se a chave pertence a quem a apresenta. **A chave é portadora do acesso**: quem a conhece, carrega a árvore. |
| **Segredo da chave** | ❌ **não coberto** | A chave é **entregue ao navegador** em campo oculto do HTML. Ela não é segredo; é identificador. |
| **Isolamento entre árvores** | ⚠️ **parcial e frágil** | Depende de o estado em memória não ser trocado entre o parse e o uso — o que **não** está garantido sob concorrência (§4.3). |
| **Confidencialidade dos dados** | ❌ **não coberto** | `all_names` — a **lista completa de nomes** da árvore — é embutida no HTML de resposta. |

### 4.3 A corrida que substitui a sessão — e a quebra

O estado do GEDCOM (`people`, `families`, `graph`, `child_to_family`) é **global de processo** (`core/gedcom_state.py`) e é **reescrito a cada requisição** (`app.py:137`), enquanto o servidor atende com **4 threads por padrão** (`ANALISADOR_THREADS`, `app.py:188`).

Sequência possível, com duas requisições simultâneas:

```text
Thread A: parseia a árvore A   →  estado global = A
Thread B: parseia a árvore B   →  estado global = B
Thread A: segue o fluxo lendo o estado global  →  lê B   ← contaminação
```

A **guarda de instância única** (`app.py:205-257`) impede dois **processos**, e não duas **threads** — são problemas diferentes, resolvidos em camadas diferentes. Classificação: mecanismo 🟢 por leitura de código; **alcance não medido** 🟡 (`L-16` em `domain.md` §7).

### 4.4 Divergência registrada contra o `BUG-20260929-BJJH`

O registro do bug (crítico, P0) descreve o sintoma assim, nos "Steps to Reproduce": *"Em outra sessão, carregue um GEDCOM diferente. O parse substitui o estado global do processo. Volte à sessão A e repita a busca: o resultado é calculado sobre a árvore da segunda sessão."*

**Esse passo, como escrito, não se reproduz no código de 2026-10-05.** Cada `POST` traz a **sua própria chave** e o servidor **re-parseia o arquivo correspondente antes de ramificar** (`app.py:131-137`); a sessão A, portanto, recalcula sobre a árvore de A.

**O bug continua aberto e crítico — o mecanismo é que mudou de forma.** O que resta é mais estreito e mais difícil de acertar por acaso, mas não menos grave:

| Vetor | Estado atual | Conf. |
| --- | --- | --- |
| Sessão A vê a árvore de B por "última carga vence" | ❌ **não ocorre mais** — cada requisição remonta a sua árvore pela chave | 🟢 |
| Quem conhece (ou obtém) a chave carrega a árvore alheia | ✅ **permanece** — não há verificação de propriedade | 🟢 |
| Requisições concorrentes trocam de árvore entre o parse e o uso | ✅ **permanece** — corrida de §4.3 | 🟡 |
| `all_names` expõe a lista completa de nomes a quem carrega a árvore | ✅ **permanece** | 🟢 |

> **Registro correto, para não se trabalhar sobre premissa morta:** o `BUG-20260929-BJJH` **não foi encerrado nem invalidado** por esta constatação — o critério de aceite dele ("duas sessões nunca compartilham árvore; requisição a árvore de outro dono responde 404") continua **não atendido**, e o próprio registro já declara que esses critérios pertencem à **Onda 3** e são **inaplicáveis ao legado** por não existir identidade.

---

## 5. Consequências de Negócio

1. **Todo dado genealógico é, na prática, público para quem alcança a porta.** Nome, sexo, datas e locais de nascimento e morte, filiação e cônjuges de pessoas — inclusive **pessoas vivas** — são exibidos a qualquer solicitante. É dado pessoal sob LGPD/GDPR, e o sistema não tem base para distinguir titular, finalidade ou consentimento. 🟢
2. **Não há como atender a um pedido de exclusão ou de portabilidade.** Nada associa dado a titular: existem arquivos em uma pasta e um processo em memória. 🟢
3. **A exposição depende do ambiente, e o padrão foi endurecido em 2026-10-04.** A aplicação passou a escutar em `127.0.0.1` por padrão, e abrir para a rede virou **ato explícito** de quem opera (`ANALISADOR_HOST`, `app.py:186`). Antes, nascer escutando em `0.0.0.0` já expunha a rede inteira por omissão. 🟢
4. **O aceite de risco está vigente e é declarado, não presumido.** A mitigação de 2026-10-04 no `BUG-20260929-BJJH` é `kind: risk-acceptance`, `temporary: true`, e a pergunta que a sustentava foi respondida diretamente: *"Só eu mesmo"* usa a aplicação. A condição que **reabre** o assunto é nomeada no próprio registro: *"se qualquer pessoa além de Adriano passar a ter acesso à aplicação antes da Onda 3"*. 🟢
5. **A mitigação ganhou garantia técnica, não apenas disciplina.** O padrão local (§5.3) mais a recusa de segunda instância na mesma porta fazem com que a exposição **exija** uma ação deliberada. A mitigação deixou de depender de promessa de comportamento. 🟢
6. **O alvo da migração já especifica a correção, e ela não é opcional:** `migration/risk_register.md#risk-005` exige `owner_id` como **invariante do aggregate**, repositório **sempre escopado** na assinatura e **teste negativo obrigatório** (usuário A acessando recurso de B recebe **404**, não 403) como **portão de go-live** (`migration/cutover_plan.md`). 🟢

---

## 6. Lacunas 🔴

| ID | Lacuna | Conf. |
| --- | --- | --- |
| **P-01** | ✅ **DECIDIDA em 2026-10-05 — é OMISSÃO, não requisito.** A correção pertence à **Onda 3** da migração, que já a especifica: `owner_id` como invariante do aggregate, repositório sempre escopado e **teste negativo de 404** como portão de go-live. **Nada é alterado no legado**, e o motivo é o mesmo que sustenta o `adrs/18`: sem identidade, qualquer correção de isolamento aqui é **inverificável**. | 🟢 |
| **P-02** | **O alcance da corrida de §4.3 não foi medido.** Não se sabe se ela já produziu resultado cruzado em uso real, nem qual a janela de exposição com 4 threads (mecanismo: 🟢; frequência: 🟡). | 🟡 |
| **P-03** | ✅ **DECIDIDA em 2026-10-05 — a exposição deve ser RESTRINGIDA, e a implementação pertence ao ALVO.** Você decidiu que a lista completa de nomes não deve ser embutida em cada resposta. **O legado não foi alterado**, e o motivo é prático: `all_names` alimenta os campos de busca (`index.html:112`), e removê-la hoje **quebraria a busca sem oferecer substituto**. A restrição exige **busca no servidor**, que é trabalho da Onda 4 (SPA) — registrada como requisito encaminhado (`gaps.md`). Enquanto isso, a exposição segue coberta pelo aceite de risco single-tenant (`P-01`). | 🟢 |
| **P-04** | ✅ **FECHADA em 2026-10-05** — a linha foi **removida** de `src/app.py` por decisão sua. Não havia consumidor, e o literal versionado deixou de existir, o que elimina a chave de forja de sessão antes de qualquer introdução de `session`. | 🟢 |
| **P-05** | ✅ **DECIDIDA em 2026-10-05 — é assimetria HERDADA, a corrigir no ALVO.** Você confirmou que não foi decisão de propósito. **O legado não foi alterado** (validar o CSV agora rejeitaria arquivos que a leitura tolerante aceita, mudando comportamento sem substituto). Entra como requisito do sistema alvo: validar conteúdo também na entrada do CSV. Ver `gaps.md` § "Requisitos encaminhados ao alvo". | 🟢 |

---

*Gerado pelo Reversa-Detective em 2026-10-05 (re-extração, nível completo).*

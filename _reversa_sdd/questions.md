# Perguntas para Validação — teste_reversa

> Gerado pelo **Reversa-Reviewer** na re-extração de **2026-10-05**. Substitui integralmente o `questions.md` de 2026-09-30.
> Nível de documentação: **Completo** → **todos os 🔴** são apresentados, e não apenas os que bloqueiam a reimplementação.
> `answer_mode = "chat"` — pode responder aqui mesmo, numerando as respostas. As **4 primeiras** são as de maior consequência.
>
> **STATUS: 16 de 16 respondidas e aplicadas em 2026-10-05.** Três delas **mudaram código** (`matching.py`, `app.py`, `genetic_evidence.py`) e uma **mudou o pin** (`requirements.txt`) — todas com autorização explícita e cobertura de `reversa-config.json`. Quatro decisões geraram **requisitos encaminhados ao sistema alvo** (`gaps.md` §6).
> Escala de confiança: 🟢 CONFIRMADO | 🟡 INFERIDO | 🔴 LACUNA

---

## Como ler esta lista

| Grupo | Tema | Perguntas |
| --- | --- | --- |
| **A** | Decisões que podem mudar **código** | 1 a 3 |
| **B** | Decisões de **produto** | 4 a 8 |
| **C** | **Dados e ambiente** | 9 a 12 |
| **D** | Detalhes técnicos que só o dono sabe | 13 a 16 |

**A pergunta 9 é a única herdada da rodada anterior** e continua aberta há mais de um mês: a medição do `0,33` nunca foi fornecida.

---

## Grupo A — Decisões que podem mudar código

### Pergunta 1 — O determinismo do desempate deve ser corrigido **no legado** ou apenas exigido do alvo?

**Contexto:** Unit `analise-dna` — `match_candidates` em `src/core/matching.py`. O laço de candidatos percorre um `set` (`:73`, `:91`) e o desempate usa comparação **estrita** (`:103-105`), de modo que empate exato nos três critérios mantém **o primeiro candidato da ordem de iteração do conjunto**. Essa ordem muda a cada execução do processo (medido em três sementes de `PYTHONHASHSEED`: nenhuma posição em comum).
**Spec afetada:** [`_reversa_sdd/analise-dna/requirements.md`] (`RF-26`), [`_reversa_sdd/analise-dna/tasks.md`] (`T-31`), [`_reversa_sdd/adrs/23-desempate-deterministico.md`]
**Pergunta:** Você já decidiu em **2026-09-30** que "precisa ser determinístico" (critério sugerido: menor `xref_id`). O código **nunca implementou** isso — a reescrita das três etapas em 2026-10-04 não passou pelo ciclo forward. O que fazer agora: (a) **corrigir o legado** nesta rodada (mudança de código autorizada por `reversa-config.json`), ou (b) **manter apenas como requisito** do sistema alvo, sem tocar no código atual?
**Impacto:** Em (a), eu edito `matching.py`, adiciono teste de determinismo e a suíte passa a proteger o comportamento. Em (b), a divergência entre decisão humana e código permanece registrada como lacuna aberta — e é a **única** das 13 decisões verificadas que o código viola.

**Resposta:** ✅ **(a) Corrigir o legado agora — EXECUTADO em 2026-10-05.**
**Aplicado em:**

- `src/core/matching.py` → **quarto critério** no desempate (`:107-110`): em empate triplo, vence o **menor `xref_id`** lexicográfico. Comentário no código registra a decisão e o motivo
- `tests/test_characterization_matching.py` → **2 testes novos**: `test_desempate_escolhe_o_menor_xref_id` (parametrizado nas duas ordens de *pool*) e `test_desempate_nao_depende_da_ordem_do_pool`
- `analise-dna/requirements.md` (`RF-26`) · `analise-dna/design.md` · `analise-dna/tasks.md` (`T-31`, `TT-15`) · `analise-dna/contracts.md` · `domain.md` (`L-15`) · `adrs/23` · `architecture.md` (dívida 1)
- **Verificação:** `pytest tests/test_characterization_matching.py -q` → **24 passam**; suíte completa **163 passam + 15 erros de ambiente** = **178 itens** (eram 175)
- ⚠️ **Segunda divergência deliberada do legado, e a primeira que muda comportamento.** Nos casos de empate triplo o vencedor pode ser outro; fora do empate, nada muda

---

### Pergunta 2 — `app.secret_key`: remover, externalizar ou manter?

**Contexto:** `src/app.py:22` define `app.secret_key = 'f@milyse@rch_dna_edition_v16'`, **embutido no código e versionado**. Ele **não tem consumidor**: `flask.session` nunca é importado, nenhum cookie é emitido, nada o lê.
**Spec afetada:** [`_reversa_sdd/permissions.md`] §1.1 e §6 (`P-04`); [`_reversa_sdd/upload-gedcom/design.md`] (Riscos)
**Pergunta:** Remover a linha (não há sessão), externalizar para variável de ambiente, ou preservar por fidelidade ao legado?
**Impacto:** Hoje é passivo de higiene, sem risco explorável. Mas no instante em que alguém introduzir `session` para resolver o isolamento entre usuários (a Rota 2 descartada do `BUG-20260929-BJJH`), esse literal **versionado** passa a ser a chave de forja de sessão de todo usuário.

**Resposta:** ✅ **Remover a linha — EXECUTADO em 2026-10-05.**
**Aplicado em:**

- `src/app.py` → a linha `app.secret_key = ...` foi **removida**; em seu lugar ficou um comentário registrando a decisão, o motivo e o ponteiro para `permissions.md`
- `permissions.md` §1.1 e §6 (`P-04`) · `upload-gedcom/design.md` · `upload-gedcom/requirements.md` · `architecture.md` (dívida 16)
- `inventory.md` → a linha de configurações internas foi corrigida, com marcação de correção do Revisor
- **Verificação:** nenhum consumidor afetado — `flask.session` não é importado em nenhum arquivo, não há `flash()` e nenhum teste referencia `secret_key`. `import app` continua funcionando, e `app.secret_key` deixou de ter valor

---

### Pergunta 3 — A ausência de autenticação é requisito ou omissão?

**Contexto:** Não existe `session`, `login`, `logout`, `password`, `current_user`, `role` ou `permission` em `src/`. Não há usuário, papel, permissão nem `owner_id`. O aceite de risco do `BUG-20260929-BJJH` (2026-10-04) foi dado sobre um uso de **uma pessoa só**, com a condição de reabertura nomeada: *"se qualquer pessoa além de Adriano passar a ter acesso antes da Onda 3"*.
**Spec afetada:** [`_reversa_sdd/permissions.md`] §5 e §6 (`P-01`)
**Pergunta:** Para o **produto**, a ausência de autenticação é (a) **omissão** a corrigir — como a Onda 3 da migração já especifica com `owner_id` e teste negativo de 404 —, ou (b) **requisito aceito** de uma ferramenta local de uso pessoal?
**Impacto:** Em (a), as specs de unidade ganham requisito de isolamento e a recomendação final prioriza a Onda 3. Em (b), registra-se como decisão de produto e o assunto sai da lista de lacunas.

**Resposta:** ✅ **(a) É OMISSÃO — corrigir na Onda 3.**
**Aplicado em:**

- `permissions.md` §5 e §6 (`P-01`) → a decisão está registrada: é **omissão**, e a correção pertence à **Onda 3** da migração, que já a especifica com `owner_id` como invariante do aggregate, repositório sempre escopado e **teste negativo de 404** como portão de go-live
- **Nenhuma mudança de código no legado, e isso é deliberado:** sem identidade, qualquer correção de isolamento aqui é **inverificável** — o próprio critério de aceite do `BUG-20260929-BJJH` é declarado inaplicável ao legado (`adrs/18`)
- **Consequência de priorização:** a recomendação do projeto passa a ser **priorizar a Onda 3 da migração**, e não corrigir autenticação no legado

---

## Grupo B — Decisões de produto

### Pergunta 4 — Nada é persistido entre requisições: isso é desejado?

**Contexto:** O GEDCOM é **re-parseado integralmente a cada `POST`**, e nenhum resultado de análise é gravado. Não há histórico, nem como comparar duas execuções. Registrado como `L-21` (`domain.md` §7) e `E-04` (`erd-complete.md` §8).
**Spec afetada:** [`_reversa_sdd/domain.md`], [`_reversa_sdd/erd-complete.md`], [`_reversa_sdd/architecture.md`] (dívida 8)
**Pergunta:** É requisito (ferramenta efêmera, sem estado) ou herança do legado que você gostaria de mudar?
**Impacto:** Se for herança a mudar, isso é escopo do sistema alvo, não do legado — mas precisa constar como requisito, porque hoje **nenhum artefato** afirma qual dos dois é.

**Resposta:** ✅ **Herança — quero histórico no alvo.**
**Aplicado em:** `domain.md` (`L-21`) · `erd-complete.md` (`E-04`) · `gaps.md` §6 como **requisito encaminhado ao alvo nº 1**. **Nada muda no legado**: criar persistência aqui seria construir o que a Onda 3 substitui.

---

### Pergunta 5 — O operador deve **agir** sobre os matches descartados?

**Contexto:** O match que não casa com nenhum registro vai para `skipped_matches` com o motivo textual (um de quatro). A tela os exibe. Não há indicação de negócio sobre se o operador deve fazer algo com eles, nem qual taxa de descarte seria aceitável. Registrado como `L-22`.
**Spec afetada:** [`_reversa_sdd/analise-dna/requirements.md`] (`RF-23`), [`_reversa_sdd/user-stories/analise-dna.md`] (`US-D-05`)
**Pergunta:** A lista de descartados é **informativa** (auditoria de que nada foi truncado) ou **acionável** (você revisa nomes para descobrir por que não casaram)?
**Impacto:** Se for acionável, a spec precisa dizer o que o operador faz com cada motivo — e talvez o próprio motivo precise de mais contexto (ex.: sugerir a grafia mais próxima).

**Resposta:** ✅ **ACIONÁVEL — você age sobre os motivos.**
**Aplicado em:** `analise-dna/requirements.md` → `RF-23` subiu de `Should` para **`Must`**, com o critério de aceite exigindo a ação por motivo · `analise-dna/design.md` → **nova seção "Discartes — o que o operador faz com cada motivo"**, com a ação esperada para cada um dos quatro motivos · `gaps.md` (`L-22` fechada). **Consequência de design:** o motivo **não pode ser encurtado na tela** — os quatro números do motivo de score são o que permite julgar o caso.

---

### Pergunta 6 — A lista completa de nomes da árvore pode continuar sendo embutida na página?

**Contexto:** `all_names` — **todos** os nomes da árvore carregada — é renderizado no HTML de cada resposta (`index.html:112`), inclusive nos erros. Ela alimenta os campos de busca. Contém nomes de **pessoas vivas**. Registrado como `P-03`.
**Spec afetada:** [`_reversa_sdd/permissions.md`] §4.2 e §6
**Pergunta:** Manter como está, ou restringir (ex.: busca com autocomplete no servidor, sem expor a lista inteira)?
**Impacto:** Como o sistema não tem autenticação, qualquer um que alcance a porta recebe a lista completa. Não há indício de que alguém tenha decidido mantê-la assim — é uma consequência, não uma escolha.

**Resposta:** ✅ **RESTRINGIR — não expor a lista completa.**
**Aplicado em:** `permissions.md` (`P-03`) · `gaps.md` §6 como **requisito encaminhado ao alvo nº 3**. **O legado não foi alterado**, e o motivo é prático: `all_names` alimenta os campos de busca (`index.html:112`), e removê-la hoje **quebraria a busca sem substituto**. A restrição exige **busca no servidor**, que é trabalho da Onda 4 (SPA). Enquanto isso, a exposição segue coberta pelo aceite de risco single-tenant.

---

### Pergunta 7 — Para endogamia e colapso de pedigree, **avisar** é suficiente?

**Contexto:** A fonte estatística (Shared cM Project 4.0) declara que não atende colapso de pedigree nem endogamia. O código **detecta** colapso no lado documental (aviso `colapso_de_pedigree`, contagem de cadeias até 8) e **lista** as duas entre as causas possíveis de conflito — mas **o veredito do confronto não muda** por causa disso. Registrado como `L-17`.
**Spec afetada:** [`_reversa_sdd/domain.md`] §7, [`_reversa_sdd/adrs/21-endogamia-avisar-nao-corrigir.md`], [`_reversa_sdd/analise-dna/design.md`]
**Pergunta:** Avisar (com o cM sendo, nesses casos, um **teto otimista**) é suficiente, ou o veredito deveria ser rebaixado quando há colapso detectado?
**Impacto:** Rebaixar exigiria definir **quanto** rebaixar — e não há modelo de correção no projeto. A ADR-21 registra que avisar foi a escolha, mas com confiança 🟡 justamente por falta de decisão explícita.

**Resposta:** ✅ **AVISAR BASTA.**
**Aplicado em:** `domain.md` (`L-17` fechada) · `adrs/21-endogamia-avisar-nao-corrigir.md` → status passa a **"confirmado pelo usuário"** · `gaps.md`. O colapso continua detectado no lado documental e **sem alterar o veredito**; o cM permanece declarado como **teto otimista** nesses casos. A incerteza que a ADR registrava em 🟡 está resolvida.

---

### Pergunta 8 — O veredito do operador sobre uma conexão precisa ser registrado?

**Contexto:** Não existe estado para "aceitei", "rejeitei" ou "corrigi" uma conexão. Como nada é persistido, nenhum julgamento humano pode ser gravado. Registrado como `M-04` (`state-machines.md` §7).
**Spec afetada:** [`_reversa_sdd/state-machines.md`]
**Pergunta:** Registrar a decisão do operador é requisito do produto, ou a ferramenta é deliberadamente só-leitura sobre o GEDCOM?
**Impacto:** Se for requisito, ele **não está no sistema** e precisa entrar no alvo — e `M-04` deixa de ser lacuna.

**Resposta:** ✅ **É REQUISITO — e pertence ao ALVO.**
**Aplicado em:** `state-machines.md` (`M-04`) · `gaps.md` §6 como **requisito encaminhado ao alvo nº 2**. **Nada muda no legado**: sem persistência (`E-04`), um veredito não teria onde viver — este requisito **depende** do nº 1. No alvo, vira uma máquina de estados nova, com transições por ação humana.

---

## Grupo C — Dados e ambiente

### Pergunta 9 — ✅ A medição do `0,33` (herdada de 2026-09-30)

**Contexto:** O limiar de Jaccard cai de **0,50 para 0,33** quando `cM ≥ 150` e o prenome não é genérico (`matching.py:130-136`). A decisão de **manter** o relaxamento é sua, de 2026-08-03, e continua 🟢. O que nunca foi fornecido é a **origem do número**. Você indicou ter a medição em 2026-09-30, mas ela não foi colada.
**Spec afetada:** [`_reversa_sdd/analise-dna/design.md`], [`_reversa_sdd/analise-dna/requirements.md`]
**Pergunta:** O `0,33` foi **calibrado** contra dados reais (existe a medição de quantos falsos positivos ele introduz, e contra que conjunto?) ou foi um **chute** que funcionou na prática?
**Impacto:** Se calibrado, a medição entra como evidência e a lacuna `L-14` fecha. Se foi chute, o número passa a 🟡 **ajustável**, e a reimplementação pode tratá-lo como parâmetro em vez de literal. **É a pergunta mais antiga em aberto.**

**Resposta:** ✅ **Foi um CHUTE que funcionou na prática — NÃO foi calibrado.**
**Aplicado em:**

- `analise-dna/design.md` → a lacuna `L-14` é declarada fechada, com o número passando a **heurístico e ajustável**
- `analise-dna/requirements.md` → a regra do Jaccard ganha a nota de que o `0,33` é heurística sem medição de calibração
- `analise-dna/contracts.md` §9 → a linha do limiar separa a **decisão** (alta estabilidade: relaxar é intencional) do **número** (média: ajustável)
- **O que NÃO muda:** a decisão de **manter** o relaxamento segue 🟢 desde 2026-08-03, e a mecânica (limiar 0,50 por padrão; 0,33 apenas com `cM ≥ 150` e prenome não genérico) permanece intacta. O que mudou foi a **autoridade do número**

---

### Pergunta 10 — Quais exportadores de CSV precisam ser suportados?

**Contexto:** A coluna de kit é detectada por regex (`[A-Z]{2}\d{7}` e `[A-Z]{1,3}\d{4,8}`), que é específica de um padrão de exportador (GEDmatch). A leitura foi tornada tolerante a separador, preâmbulo e linha torta (ADR-16), mas a **identificação de colunas por papel** é heurística. Registrado como `L-08`.
**Spec afetada:** [`_reversa_sdd/analise-dna/contracts.md`] §2.1
**Pergunta:** Quais exportadores você usa de fato (GEDmatch, MyHeritage, FamilyTreeDNA, outro)? A lista define o que precisa ser testado com fixture real.
**Impacto:** Se houver um exportador com formato diferente, a detecção por papel precisa de coluna de apoio — e hoje só existe teste com o formato conhecido.

**Resposta:** ✅ **Apenas o GEDmatch.**
**Aplicado em:** `analise-dna/contracts.md` §2.1 → nota de **cobertura declarada** · `gaps.md` (`L-08` fechada). A lacuna deixa de ser incerteza e passa a ser **escopo declarado**: as regras de detecção são as do formato testado, e **não há prova de generalidade** para os outros exportadores — nem precisa haver enquanto o uso for este.

---

### Pergunta 11 — Qual interpretador é o oficial: o global ou o `.venv`?

**Contexto:** O `.venv/` do projeto **não reproduz** o pin do `requirements.txt` em **5 pacotes**: `ged4py` 0.5.5 (pin 0.5.2), `networkx` 3.7 (3.6.1), `pandas` 3.0.6 (3.0.3), `RapidFuzz` 3.14.6 (3.14.5) e `python-Levenshtein` 0.27.5 (0.27.3). O `RapidFuzz` é o **backend real do matching difuso**. O `README.md` documenta o interpretador **global**. Registrado como `L-19`.
**Spec afetada:** [`_reversa_sdd/analise-dna/design.md`], [`_reversa_sdd/architecture.md`] (dívida 2), [`_reversa_sdd/adrs/13-fixar-dependencias-diretas.md`]
**Pergunta:** O oficial é o **global** (e o `.venv` é resíduo que pode ser removido/realinhado) ou o **`.venv`** (e o `requirements.txt` precisa ser atualizado para as versões de lá)?
**Impacto:** Duas execuções, uma em cada interpretador, podem produzir **matching diferente sem uma linha de código mudar**. É a divergência de maior risco silencioso do projeto.

**Resposta:** ✅ **O `.venv` é o OFICIAL — atualizar o pin.**
**Aplicado em — e esta foi a resposta de maior consequência da rodada:**

- `requirements.txt` → realinhado: **`ged4py==0.5.5`**, **`networkx==3.7`**, **`pandas==3.0.6`** (Flask, thefuzz e waitress já coincidiam)
- `requirements.txt` → **`rapidfuzz==3.14.6`** e **`python-Levenshtein==0.27.5`** promovidos a **dependência declarada**. Eram transitivas do `thefuzz`, e o `RapidFuzz` é o **backend real do matching**: deixá-lo livre permitiria que uma instalação nova trouxesse outra versão. A alternativa anterior (nomear as transitivas para tornar a divergência *detectável*) foi substituída por torná-la **impossível**
- `.venv/` → **instalado o `pytest`** (que não existia lá) e o `pytest-cov`, para que o interpretador oficial consiga rodar a suíte
- **Verificação:** a suíte passa **igual nos dois interpretadores** — **163 passam + 15 erros de ambiente** em cada um. Depois do teste da sentinela: **164 passam**
- ⚠️ **Pendência declarada:** o `README.md` documenta o fluxo pelo **global** e agora contradiz o pin. **Não editei o README** por ser documento do usuário

---

### Pergunta 12 — Vale medir a cobertura de testes?

**Contexto:** Não há `pytest-cov` nem configuração de cobertura. A suíte tem **11 arquivos, 126 funções e 175 itens coletados**, mas isso não diz que proporção do comportamento está congelada. Registrado como `L-23`.
**Spec afetada:** [`_reversa_sdd/architecture.md`] (dívida 13)
**Pergunta:** Medir a cobertura agora (ferramenta nova, execução local) ou deixar como está?
**Impacto:** A cobertura mediria **linhas**, não comportamento — e há 4 componentes de alto risco sem teste de unidade dedicado (`csv_ingest`, `family_navigation`, `path_finding` e a rota do `app.py`). O número ajudaria a priorizar.

**Resposta:** ✅ **MEDIR AGORA — medido.**
**Aplicado em:** `pytest-cov` instalado no `.venv` · `domain.md` (`L-23` fechada) · `architecture.md` (dívida 13) · `spec-impact-matrix.md` (`X-03` com números reais) · `gaps.md`.
**Resultado: cobertura de `src/` = 83 %** (1.520 instruções, 253 descobertas). Destaques, que **confirmam** o que a Matriz C já apontava por inspeção:

| Módulo | Cobertura |
| --- | ---: |
| `number_format.py` | **53 %** ← a pior, e é a autoridade de **todo** número exibido |
| `relationship_hypotheses.py` | 76 % |
| `mermaid_render.py` | 78 % |
| `evidence_comparison.py` | 83 % |
| `csv_ingest.py` · `name_normalization.py` · `matching.py` | 84 % · 84 % · 86 % |
| `validate.py` · `dna_analysis.py` · `gedcom_parser.py` | 98 % · 97 % · 98 % |

---

## Grupo D — Detalhes técnicos que só o dono sabe

### Pergunta 13 — A assimetria da ambiguidade é intencional?

**Contexto:** A identidade ambígua **rebaixa** `found` para `ambiguous`, mas **não** rebaixa `not_found`: quando não há caminho **e** há homônimos, o status permanece `not_found` e a ambiguidade aparece apenas como aviso adicional. Registrado como `M-02`.
**Spec afetada:** [`_reversa_sdd/state-machines.md`] §4.3, [`_reversa_sdd/busca-caminho/contracts.md`] §2.1
**Pergunta:** A ambiguidade ter **dois pesos diferentes** conforme o estado é intencional, ou herdado sem decisão?
**Impacto:** Sendo intencional, vira contrato documentado. Sendo herdado, quem reimplementar precisa saber que pode unificar.

**Resposta:** ✅ **INTENCIONAL — vira contrato.**
**Aplicado em:** `state-machines.md` (`M-02`) · `gaps.md`. O motivo registrado: `not_found` **já é** um resultado mais fraco que `ambiguous` — quando não há caminho, não existe afirmação de parentesco a qualificar. Quem reimplementar deve **preservar** a assimetria.

---

### Pergunta 14 — O CSV não ter validação de conteúdo é deliberado?

**Contexto:** `app.py:86` valida o conteúdo **apenas** para o GEDCOM (`kind == "gedcom"`). O CSV de DNA tem só a **forma do nome** validada, e é gravado em disco **antes** de qualquer verificação. Registrado como `P-05`.
**Spec afetada:** [`_reversa_sdd/permissions.md`] §6, [`_reversa_sdd/upload-gedcom/requirements.md`] (RNF)
**Pergunta:** É coerente com a leitura tolerante (ADR-16) por decisão, ou é assimetria herdada?
**Impacto:** Sendo herdada, é uma decisão de segurança pendente; sendo deliberada, vira contrato explícito.

**Resposta:** ✅ **HERDADO — assimetria a corrigir no ALVO.**
**Aplicado em:** `permissions.md` (`P-05`) · `gaps.md` §6 como **requisito encaminhado ao alvo nº 4**. **Nada muda no legado**: validar o CSV agora **rejeitaria** arquivos que a leitura tolerante (ADR-16) aceita — mudaria comportamento sem substituto. No alvo, o CSV passa a ter validação de conteúdo como o GEDCOM tem.

---

### Pergunta 15 — A sentinela `SEM-KIT` pode colidir com um kit real?

**Contexto:** Quando o CSV não tem coluna de kit **nem** e-mail, a evidência usa a chave literal `SEM-KIT`. Um CSV que trouxesse um kit literalmente chamado `SEM-KIT` seria agrupado junto. Registrado como `E-03`.
**Spec afetada:** [`_reversa_sdd/erd-complete.md`] §8, [`_reversa_sdd/analise-dna/contracts.md`] §3.1
**Pergunta:** Risco aceito, ou vale trocar a sentinela por algo que não possa colidir (ex.: prefixo impossível)?
**Impacto:** Trocar a sentinela muda a chave de agrupamento e, portanto, o resultado — é mudança de comportamento, não de forma.

**Resposta:** ✅ **TROCAR — EXECUTADO em 2026-10-05.**
**Aplicado em:**

- `src/core/genetic_evidence.py` → nova constante **`SEM_KIT = " SEM-KIT"`**, com o **espaço à esquerda** como defesa: `_clean` aplica `str(valor).strip()` em **todo** valor vindo do CSV, então nenhum kit real — nem e-mail — pode começar com espaço. Era o que tornava a colisão possível
- `src/core/genetic_evidence.py` → os **4 usos** do literal passaram a usar a constante (`:140`, `:180`, `:184`, `:253`), e ela entrou no `__all__`
- `tests/test_confrontacao_gedcom_dna.py` → teste existente atualizado + **teste novo** `test_8c_kit_chamado_SEM_KIT_nao_colide_com_a_ausencia_de_kit`, que prova **três grupos separados**: kit real (150 cM), ausência de kit (25 cM) e um kit literalmente chamado `SEM-KIT` (10 cM)
- `data-dictionary.md` · `erd-complete.md` (`E-03`) · `analise-dna/contracts.md` §3.1
- **Verificação:** `test_confrontacao_gedcom_dna.py` → **30 passam** (eram 29); suíte completa → **164 passam + 15 erros de ambiente = 179 itens**

---

### Pergunta 16 — Você já observou resultado cruzado entre análises simultâneas?

**Contexto:** O estado do GEDCOM é **global de processo** e é reescrito a cada requisição (`app.py:137`), enquanto o servidor atende com **4 threads** (`ANALISADOR_THREADS`). Duas requisições simultâneas podem intercalar: A parseia a árvore A, B parseia a árvore B, e A segue lendo o estado que agora é o de B. A guarda de instância única impede dois **processos**, não duas **threads**. Registrado como `L-16` e `M-03`.
**Spec afetada:** [`_reversa_sdd/permissions.md`] §4.3, [`_reversa_sdd/state-machines.md`] §7
**Pergunta:** Você já viu um resultado que parecia pertencer a outra árvore? (O mecanismo está confirmado por leitura de código; a **frequência** não foi medida.)
**Impacto:** Se já ocorreu, deixa de ser risco teórico e passa a justificar mitigação no legado. Se nunca ocorreu, permanece como condição de corrida latente — que o uso single-user tende a não disparar.

**Resposta:** ✅ **NUNCA VI resultado cruzado.**
**Aplicado em:** `gaps.md` (`L-16` / `M-03` / `P-02`) · `permissions.md` §4.3 · `state-machines.md` §7.
**A lacuna NÃO fecha, e o registro é honesto:** o mecanismo está confirmado por leitura de código, mas o **alcance nunca foi medido**. O que a sua resposta muda é a **probabilidade percebida**, não a existência da janela: com uso single-user, a janela raramente é disparada. **É a única lacuna crítica que restou** — e nenhuma mitigação no legado foi autorizada, porque o isolamento real pertence à Onda 3 (`P-01`).

---

## Perguntas **já decididas** — NÃO são pendências

Verificadas contra o código de 2026-10-05. Nenhuma precisa ser refeita.

| Assunto | Resposta vigente | Verificação no código | Conf. |
| --- | --- | --- | --- |
| Regras de aceitação do matching são definitivas | Preservar com fidelidade | 5 ramos + prefixo + rebaixamento intactos (`matching.py:138-166`) | 🟢 |
| Homônimos usam o 1º ID | Aceitável — **hoje é apenas o recuo** | `path_search.py:154-167` amplia para 5×5 combinações com caminho | 🟢 |
| Upload sem validação de extensão/tamanho | **Superada** pelo `BUG-20260929-QMLY` | teto de 16 MB, validação de conteúdo e chave de conteúdo (`app.py:32`, `validate.py:90-105`) | 🟢 |
| Relaxamento de Jaccard é intencional | Mantém-se | `matching.py:132-136` | 🟢 |
| Teto de 20 iterações do BFS | Preservar fidelidade, sem sinalização | `path_finding.py:25` | 🟢 |
| Varredura de `get_spouses` é condicional | Contrato explícito | `family_navigation.py:66-75` | 🟢 |
| Entidades decorativas | Arquitetura abandonada — **removidas** | nenhuma existe em `src/` | 🟢 |
| Faixas de cM escritas à mão | Declarar como heurística | `cm_estimator.py:1`, `:21` — fora do fluxo | 🟢 |
| Legado permanece single-tenant | Aceite de risco, temporário | `BUG-20260929-BJJH`, bloco `mitigation` | 🟢 |

> A **Pergunta 1** não reabre a decisão de tornar o desempate determinístico — ela pergunta **onde** aplicá-la. A **Pergunta 9** não reabre a decisão de manter o `0,33` — pergunta pela **origem do número**.

---

*Gerado pelo Reversa-Reviewer em 2026-10-05 (re-extração, nível completo).*

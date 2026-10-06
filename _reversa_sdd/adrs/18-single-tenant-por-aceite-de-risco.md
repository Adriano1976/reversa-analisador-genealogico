# ADR-18 — Legado permanece single-tenant por aceite de risco, sem correção no código

- **Status:** Aceito, **vigente** — mitigação por aceite de risco, `temporary: true`
- **Data da decisão:** 2026-10-02 (decisão) e 2026-10-04 (mitigação registrada)
- **Confiança:** 🟢 CONFIRMADO

## Contexto

O `BUG-20260929-BJJH` (severidade **crítica**, prioridade **P0**) registra que a árvore genealógica carregada **não pertence a ninguém**: ela vive em estado global de processo, a pasta `uploads/` é única e compartilhada, o arquivo é endereçável pelo valor que o cliente envia, não há autenticação, não há sessão e não há `owner_id`. Em contexto multiusuário, é **vazamento de dado genealógico** entre contas — e o dado inclui **pessoas vivas**.

As alternativas de tratamento foram levantadas como três rotas no `fix/plano-de-tratamento.md`.

## Decisão

**Não corrigir no legado.** O tratamento é a **Rota 3**: resolver na **Onda 3 da migração**, onde a spec manda — com `api/auth` resolvendo `owner_id`, repositório com escopo obrigatório na assinatura e o **teste negativo de 404** que o cutover exige como portão de go-live.

A pergunta que sustentava a decisão foi feita diretamente — *"alguém além de você precisa usar a aplicação antes da Onda 3?"* — e a resposta foi: **"Só eu mesmo"**. Com o uso restrito a uma pessoa, a aplicação permanece **single-tenant**, que é exatamente a contingência que o `RISK-005` já autorizava.

## Evidência

- `_reversa_bugs/busca-caminho/bugs/BUG-20260929-BJJH-exposicao-de-arvore-entre-usuarios/bug.md` — estado `active` / `mitigating`, bloco `mitigation` com `kind: risk-acceptance`, `temporary: true`, e `blocking` de tipo `external` nomeando a dependência da Onda 3.
- `mitigation.applied_at: 2026-10-04`, com a declaração explícita: **"Nenhuma linha de código foi alterada nesta mitigação, e o bug continua aberto."**
- Specs que definem o alvo: `migration/risk_register.md#risk-005` (propriedade do dado como invariante do aggregate; sempre escopado; teste negativo `404`), `migration/ambiguity_log.md#amb-009` e `migration/target_business_rules.md#br-humana-004` (eliminar o conceito de "GEDCOM carregado" global; `owner_id` como identidade), `migration/cutover_plan.md` (go-live condicionado ao teste negativo).
- **Condição que reabre, nomeada no próprio registro:** *"Alguém além do owner passar a ter acesso antes da Onda 3."*

## Justificativa

Não é adiamento por dificuldade, e o registro diz isso de forma explícita. A correção no legado seria **código descartado pela Onda 3** e, ainda assim, **não fecharia o segundo critério de aceite** — porque sem identidade não existem "dono A" e "dono B" para que a resposta difira entre `404` e `403`. O critério é **inaplicável ao legado**, e não apenas caro.

## Consequências

- ✅ **O pré-requisito da mitigação deixou de ser promessa de disciplina e ganhou garantia técnica.** O plano exigia que a aplicação não fosse exposta a mais de uma pessoa; isso antes dependia de comportamento humano, porque a aplicação **nascia escutando em `0.0.0.0`**. A feature `004-servidor-waitress` (ADR-12), entregue em 2026-10-04, mudou o padrão para `127.0.0.1` e passou a **recusar uma segunda instância na mesma porta**. Medido na mitigação: a instância no ar escutava em `127.0.0.1:5000`.
- ✅ **O bug continua aberto e rastreável.** O `spec_verdict` segue nulo e o `change_set` segue vazio; a mitigação **não substitui** a Resolution.
- ⚠️ **Divergência de reprodutibilidade encontrada nesta re-extração.** O passo 4 dos "Steps to Reproduce" — *"volte à sessão A e repita a busca: o resultado é calculado sobre a árvore da segunda sessão"* — **não se reproduz no código de 2026-10-05**, porque cada `POST` traz a sua própria chave e o servidor **re-parseia o arquivo correspondente antes de ramificar** (`app.py:131-137`). O bug **não** está invalidado: o vetor "última carga vence" foi substituído pelos vetores "quem conhece a chave carrega" e "requisições concorrentes trocam de árvore" (ver `permissions.md` §4.3 e §4.4).
- 🔴 **A lacuna de identidade persiste e é a raiz do problema:** enquanto não houver `owner_id`, **nenhuma** correção de isolamento é verificável. É o que torna a Onda 3 a única rota honesta.
- 🔴 **O aceite de risco vale para um usuário, não para o produto.** Se o sistema for usado por outra pessoa, a decisão **perde validade por definição**, e o próprio registro declara a condição.

## Alternativas consideradas

- **Rota 1 — corrigir no legado agora.** Descartada: código que a Onda 3 descarta, e sem fechar o critério de aceite.
- **Rota 2 — escopo por sessão em memória.** Descartada **por decisão humana**, não por impedimento técnico. Duas razões: introduziria `flask.session` e faria do `app.secret_key` **versionado** a chave de forja de sessão de todo usuário (`P-04` em `permissions.md`), e ainda assim não criaria identidade real.
- **Rota 3 — resolver na Onda 3 (escolhida).** Única rota em que o critério de aceite é **verificável**.

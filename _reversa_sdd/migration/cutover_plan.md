---
schemaVersion: 1
generatedAt: 2026-09-28T03:00:12Z
reversa:
  version: "1.2.58"
kind: cutover_plan
producedBy: strategist
hash: "sha256:3d054ecdce8c139cba65242abd3e470990d41f6565aa34e0d7f387ba770b90e5"
---

# Cutover Plan

> Plano de corte do legado para o sistema novo, alinhado à estratégia escolhida em `migration_strategy.md`.

## Estratégia base

- **Estratégia confirmada**: **Parallel Run materializado como ondas incrementais com validação diferencial** (recomendação do Strategist — `migration_strategy.md` § Recomendação).
- **Status da confirmação**: ✅ **CONFIRMADA** pelo usuário (Adriano) em 2026-09-28T03:02:10Z — ver `migration_strategy.md` § Decisão humana. O sequenciamento em 7 ondas é vinculante e este plano vale como escrito.

### ⚠️ Este cutover tem três características que o tornam atípico

1. **Não há dados a migrar.** O legado não tem SGBD — o estado é 100% em memória (`architecture.md` §1, §5). Não há ETL, não há schema legado, não há janela de congelamento de escrita, não há reconciliação de registros. A "migração de dados" é **modelagem nova**, não conversão. Toda a seção clássica de ETL de um cutover **não se aplica**.
2. **Não há produção a parar.** O legado nunca foi deployado: sem CI/CD, sem Docker, sem workflow (`architecture.md` §5 dívida #3; `inventory.md` §6). Não há SLA, não há usuários ativos, não há janela de manutenção a negociar.
3. **O "cutover" real é a abertura para usuários externos**, não uma troca de sistema em operação. O risco do corte não é perder dados nem derrubar serviço — é **colocar dado genético sensível nas mãos de terceiros** com o núcleo ainda não provado. Por isso o portão crítico do plano não é técnico, é de **paridade provada + conformidade pronta**.

## Pré-requisitos

Todos devem estar satisfeitos antes de iniciar a janela de cutover. Os itens marcados com onda têm vínculo direto ao sequenciamento.

- [ ] **Onda 0 — Oráculo congelado**: harness diferencial operando e golden files gerados a partir de **`analisador-genealogico/app.py`** (nunca de `reconstructed/`) — ver RISK-002.
- [ ] **Onda 1 — Paridade do núcleo provada**: `parity_tests/` em **100% de aprovação**, comparando valores exatos. Nenhuma divergência aberta. Este é o pré-requisito mais importante do plano.
- [ ] **Onda 2 — Fronteira de aplicação** com contrato tipado, exceções de domínio e status HTTP semântico.
- [ ] **Onda 3 — Isolamento por usuário provado** por **teste negativo**: usuário A recebe `404` ao tentar acessar recurso de usuário B (não `403`). Sem isso, o cutover não pode ocorrer — ver RISK-005.
- [ ] **Onda 4 — UI React** funcional, incluindo visualização de grafo com as regras de decomposição preservadas no domínio.
- [ ] **Onda 5 — Conformidade LGPD/GDPR em vigor**: base legal definida, consentimento instrumentado, retenção com expurgo implementado, direito de exclusão exercível, criptografia em repouso e em trânsito. **Bloqueante absoluto** — ver RISK-006.
- [ ] **Dependências fixadas** (`pins`) no projeto novo (resolve a dívida #1 do legado; mitiga RISK-009).
- [ ] **`secret_key` fora do código** — descartado conforme BR-DESCARTAR-007.
- [ ] **Validação de upload em vigor** — extensão/MIME, tamanho máximo, chave gerada pelo servidor, escopo por usuário (BR-HUMANA-001 / RISK-007).
- [ ] **Legado preservado como oráculo** em estado congelado e somente-leitura; nenhum artefato do legado modificado (regra absoluta do Reversa).
- [ ] **Rollback ensaiado** em ambiente de staging, com tempo medido.

## Janela de cutover

- **Data alvo**: **indefinida** — o brief declara explicitamente *"sem prazo"* e *"qualidade sobre velocidade"*. A data é determinada pelo fechamento dos pré-requisitos, não por calendário.
- **Duração estimada**: **2 a 4 horas** de janela técnica. A complexidade do corte é baixa (sem ETL, sem migração de dados, sem usuários ativos): trata-se de provisionar infraestrutura, aplicar schema novo, publicar aplicação e executar smoke tests.
- **Ambiente afetado**: **produção nova** (a ser provisionada). Não há ambiente de produção existente a afetar. Staging obrigatório antes.
- **Comunicação prévia**: stakeholder único (Adriano). Sem necessidade de comunicação externa — **não há usuários a avisar**, porque o produto ainda não foi aberto. ⚠️ Se houver abertura de cadastro antes do fechamento dos pré-requisitos, esta seção precisa ser reescrita e a comunicação passa a ser obrigatória.

## Passos do cutover

| # | Passo | Owner | Duração | Reversível? |
|---|---|---|---|---|
| 1 | Confirmar fechamento de **todos** os pré-requisitos, com evidência de `parity_tests/` em 100% e do teste negativo de isolamento | Inspector | 1h | sim |
| 2 | Provisionar infraestrutura (aplicação + PostgreSQL + armazenamento de objetos) | Agente de codificação | 1–2h | sim |
| 3 | Aplicar migrations do schema novo | Agente de codificação | 15min | sim (banco vazio — sem dados a perder) |
| 4 | Configurar segredos em runtime (chave de sessão rotacionável, credenciais de banco, chaves de criptografia) — **nada hardcoded** | Agente de codificação | 30min | sim |
| 5 | Publicar aplicação (API + SPA) em produção | Agente de codificação | 30min | sim |
| 6 | Executar **smoke tests** do `parity_specs.md` contra a instância de produção, com as fixtures de referência | Inspector | 30min | sim |
| 7 | Verificar **manual e explicitamente** os mecanismos de conformidade: consentimento registrado, expurgo agendado, exclusão de conta funcionando, criptografia ativa em repouso | Adriano + Agente de codificação | 1h | sim |
| 8 | **Congelar o legado como oráculo**: marcar o commit de `analisador-genealogico/app.py` como referência imutável de comportamento. Nenhuma remoção de código legado | Adriano | 15min | n/a |
| 9 | Declarar go-live. Só então avaliar abertura de cadastro para usuários externos | Adriano | — | sim |
| 10 | Monitoramento estendido: acompanhar erros de análise, falhas de parse e qualquer divergência reportada contra o oráculo | Adriano | período estendido | n/a |

> **Nota de sequenciamento**: os passos 2–6 são mecânicos e de baixo risco. O risco real do cutover está **concentrado nos pré-requisitos** (passo 1) e na **decisão de abrir cadastro** (passo 9). Um cutover que publique a aplicação sem usuários externos é reversível e barato; abrir cadastro sem conformidade e sem paridade provada é o único movimento verdadeiramente irreversível deste plano.

## Plano de rollback

- **Critérios de acionamento** (qualquer um):
  - Paridade divergente em produção em qualquer caso de `parity_tests/`.
  - Qualquer evidência de acesso cruzado entre usuários (vazamento de tenant).
  - Falha nos mecanismos de conformidade (consentimento não registrado, criptografia inativa, exclusão de conta não funcional).
  - Erro de parsing ou de análise não reproduzível, sem causa identificada.
- **Passos**:
  1. Retirar a aplicação nova do ar (ou bloquear cadastro/login, se o problema for contido).
  2. Não há dados de usuário a restaurar em rollback **durante a fase sem usuários externos** — o banco pode ser recriado. ⚠️ **Após** o go-live com usuários reais, esta premissa deixa de valer: passa a existir dado genético persistido, e o rollback não pode descartá-lo.
  3. Manter o legado disponível: ele permanece intacto em disco e utilizável, conforme a regra absoluta do Reversa.
  4. Registrar a divergência em `ambiguity_log.md` e no `risk_register.md` antes de corrigir — não corrigir silenciosamente.
- **Tempo máximo aceitável até rollback**: **1 hora** (não há produção a restaurar nem SLA a cumprir na fase sem usuários; o prazo é de disciplina, não de contrato).
- **Owner do rollback**: Adriano (decisão) + Agente de codificação (execução).

## Critérios de go / no-go

- **Go** (todos obrigatórios):
  - `parity_tests/` em **100% de aprovação**, com oráculo derivado de **`app.py`** e comparação de valores exatos.
  - Teste negativo de isolamento entre usuários passando (`404` para recurso de outro usuário).
  - Mecanismos LGPD/GDPR verificados manualmente: consentimento, expurgo, exclusão, criptografia.
  - Dependências fixadas e nenhum segredo no código.
  - Rollback ensaiado em staging com tempo medido ≤ 1h.
  - Nenhum item PENDENTE no `ambiguity_log.md`.
- **No-go** (qualquer um bloqueia):
  - Qualquer divergência de paridade em aberto, **mesmo com aparência de melhoria** sobre o legado.
  - Paridade medida contra a **reconstrução** em vez do legado (oráculo circular — RISK-002).
  - Isolamento por usuário não provado por teste negativo.
  - Base legal ou prazo de retenção indefinidos.
  - Qualquer segredo (chave de sessão, credencial) presente no repositório.
  - Risco crítico do `risk_register.md` sem mitigação aplicada **e** sem aceite formal do usuário.

## Pós-cutover

- [ ] Monitoramento estendido por período a definir com o usuário (não há SLA declarado no brief).
- [ ] Validação de paridade conforme `parity_specs.md` (produzido pelo Inspector).
- [ ] Manter o legado como **oráculo congelado**, somente-leitura. **Não** decommissionar enquanto houver qualquer investigação de divergência aberta.
- [ ] **Decommission do legado**: apenas após (a) paridade estável em produção, (b) conformidade auditada, (c) decisão explícita do usuário. ⚠️ Recomendação: **não remover o legado** mesmo após o decommission operacional — ele é a única especificação executável do comportamento congelado e o único instrumento capaz de dirimir dúvidas futuras de matching. A regra absoluta do Reversa (nunca apagar arquivos pré-existentes do legado) já aponta nessa direção.
- [ ] Registrar em `ambiguity_log.md` os itens REFERIDOS À CODIFICAÇÃO (AMB-002: validação com usuário externo real; AMB-003: disciplina de ondas) como pendências de produto, não de migração.

## Notas

- **A ausência de prazo é um ativo, não uma omissão.** Ela é o que permite recusar Big Bang e exigir paridade provada antes da Onda 2. Se um prazo for introduzido, este plano precisa ser revisado: o caminho mais curto seria cortar as ondas 4–5 e entregar apenas núcleo + fronteira mínima.
- **O maior risco deste cutover não está no cutover.** Não há dados, não há usuários, não há SLA. O risco está em (a) o oráculo ser inválido ou circular, e (b) abrir cadastro antes de o isolamento e a conformidade estarem provados. Os passos 1 e 9 são, respectivamente, o portão técnico e o portão de negócio.
- **Nenhum arquivo do legado foi, é ou será modificado por este plano.** O legado é lido para gerar o oráculo e mantido como referência; nunca escrito.

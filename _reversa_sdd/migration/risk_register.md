---
schemaVersion: 1
generatedAt: 2026-09-28T03:00:12Z
reversa:
  version: "1.2.58"
kind: risk_register
producedBy: strategist
hash: "sha256:192bb2c47eeaa80bd7547b7abf2ca7ca0ae4cb0c9ee8d30f3b40cac075a3e44a"
---

# Risk Register

> Registro de riscos da migração com probabilidade, impacto, mitigação e responsável.
> Baseado na estratégia recomendada (**Parallel Run em ondas**, `migration_strategy.md`), no gap de paradigma (`paradigm_decision.md`) e nas 49 regras curadas (`target_business_rules.md`).

## Riscos

### RISK-001
- **Descrição**: **Perda de fidelidade do matching viral de DNA.** O núcleo congelado (score `0.55/0.25/0.20` + InterBonus, regras A/B/C/D com limiares 92/90/86/100, relaxamento de Jaccard 0.5→0.33, filtros anti-falso-positivo, interseção adaptativa, desempate) é heurístico e silencioso. Qualquer "limpeza" durante o port altera resultados sem erro visível — o sistema continua funcionando e devolvendo respostas **erradas**.
- **Categoria**: técnico
- **Probabilidade**: alta
- **Impacto**: crítico
- **Severidade combinada**: **CRÍTICA**
- **Trigger / sinal de alerta**: qualquer divergência em `parity_tests/`; ou — pior — ausência de divergência porque o oráculo não cobre o caso. Sinal secundário: um resultado de matching que "parece mais razoável" que o do legado.
- **Mitigação**: (a) Onda 0 obrigatória: harness diferencial executando o `app.py` original e o candidato sobre as mesmas fixtures, comparando saída a saída; (b) Onda 1 portada **sem nenhuma feature nova**, para que qualquer divergência seja atribuível ao port; (c) transcrição literal dos limiares como constantes nomeadas, **sem alterar valores nem ordem de avaliação**; (d) revisão linha-a-linha das regras A/B/C/D contra `app.py:726-793`.
- **Plano de contingência**: se a paridade não fechar em 100% na Onda 1, **não avançar** para a Onda 2. Isolar a divergência com fixtures mínimos e decidir caso a caso se é defeito do port ou lacuna do oráculo. Nunca "ajustar o alvo para bater com a nova implementação".
- **Owner**: Agente de codificação (implementação) + Inspector (critério de paridade)
- **Status**: aberto

### RISK-002
- **Descrição**: **Oráculo circular.** O brief elege *"paridade de matching ≥ 100% nos casos de teste"* como métrica primária, mas o único conjunto de testes existente (`tests/`, 47 passed) valida a **reconstrução** (`reconstructed/*.py`), não o **legado** (`analisador-genealogico/app.py`). Se os golden files forem gerados a partir da reconstrução, a migração será validada contra uma interpretação de segunda mão — e um erro compartilhado entre reconstrução e alvo passaria despercebido indefinidamente.
- **Categoria**: técnico
- **Probabilidade**: média
- **Impacto**: crítico
- **Severidade combinada**: **CRÍTICA**
- **Trigger / sinal de alerta**: golden files cujo `producedBy` aponta para `reconstructed/` em vez de `analisador-genealogico/app.py`; ou paridade de 100% atingida **antes** de o harness apontar para o legado.
- **Mitigação**: gerar os golden files executando `analisador-genealogico/app.py` (leitura apenas, nunca escrita) sobre as fixtures de `tests/fixtures/`; registrar a **origem** de cada golden; tratar `tests/` como pista, nunca como oráculo. Exigir que o Inspector declare explicitamente qual é o oráculo em `parity_specs.md`.
- **Plano de contingência**: se o `app.py` não for executável no ambiente atual (dependências não fixadas — ver RISK-009), reconstruir o ambiente em venv isolado a partir do `requirements.txt` **sem alterar o arquivo**; se ainda assim falhar, escalar ao usuário — paridade inverificável é um bloqueio de go/no-go, não um detalhe.
- **Owner**: Inspector (definição do oráculo) + Agente de codificação (harness)
- **Status**: aberto

### RISK-003
- **Descrição**: **Transcrição incompleta a partir do código.** Duas regras do núcleo existem **somente em `app.py`** e não estão transcritas em nenhuma spec: a lista exata de primeiros nomes genéricos (BR-MIGRAR-011) e a tabela de equivalentes de grafia / lista de sobrenomes comuns / sufixos salvadores (BR-MIGRAR-012). O agente de codificação que as reconstruir a partir da descrição textual produzirá uma lista plausível e **errada** — e o erro é invisível, porque produz resultados que parecem corretos.
- **Categoria**: técnico
- **Probabilidade**: alta
- **Impacto**: alto
- **Severidade combinada**: **ALTA**
- **Trigger / sinal de alerta**: constante de domínio no código novo sem referência de linha ao `app.py`; divergência de matching concentrada em nomes com grafia variante ou primeiro nome comum.
- **Mitigação**: exigir que toda constante transcrita traga **referência de linha ao legado** no comentário (`# app.py:6xx`); incluir fixtures com nomes genéricos (`Maria`, `José`) e grafias variantes (`netto`/`neto`, `gouvea`/`gouveia`) no harness diferencial; revisão dedicada desses dois itens.
- **Plano de contingência**: extrair as tabelas mecanicamente do `app.py` (leitura de constantes) em vez de transcrever manualmente, eliminando a etapa sujeita a erro humano.
- **Owner**: Agente de codificação
- **Status**: aberto

### RISK-004
- **Descrição**: **Divergência aritmética silenciosa por ponto flutuante.** A soma de cM (BR-MIGRAR-016), a ordem de soma do score (BR-MIGRAR-009) e o desempate (BR-MIGRAR-015) dependem de ordem de acumulação — soma em ponto flutuante **não é associativa**. Ao introduzir persistência (Onda 3), agregar com `SUM` do PostgreSQL em vez de reproduzir a ordem de leitura do `groupby.agg` do pandas pode alterar o último dígito e **cruzar um limite de faixa de cM**, mudando a relação prevista (ex.: de "Primos de 1º grau" para a faixa vizinha).
- **Categoria**: técnico
- **Probabilidade**: média
- **Impacto**: alto
- **Severidade combinada**: **ALTA**
- **Trigger / sinal de alerta**: divergência de paridade que aparece **apenas após a Onda 3** (persistência), com valores diferindo em centésimos de cM; mudança de relação prevista para cM próximo de fronteira de faixa (46, 200, 553, 1317, 2200, 3300).
- **Mitigação**: definir no `target_data_model.md` a **estratégia de acumulação** (reproduzir a ordem de origem, não delegar a `SUM` cego); incluir fixtures com cM exatamente nas fronteiras das 9 faixas e valores que provoquem empate de arredondamento; comparar valores **exatos** no diferencial, nunca com tolerância.
- **Plano de contingência**: se o `SUM` do banco for inevitável, materializar o total agregado calculado em aplicação (função pura) e persistir o valor já calculado, mantendo o banco como armazenamento e não como calculadora.
- **Owner**: Designer (modelo de dados) + Agente de codificação
- **Status**: aberto

### RISK-005
- **Descrição**: **Vazamento de dados genéticos entre usuários.** O legado mantém `people`, `families`, `graph`, `child_to_family` como globais de processo sobrescritos a cada parse (`app.py:20-23`), sem autenticação e sem RBAC (`domain.md` §4). Converter isso em multiusuário exige que `owner_id` seja **invariante do aggregate**, não filtro de rota. Um único ponto de leitura esquecido expõe a árvore de um usuário a outro — e dados genéticos são irrevogáveis (não há como "rotacionar" o genoma de alguém).
- **Categoria**: regulatório
- **Probabilidade**: média
- **Impacto**: crítico
- **Severidade combinada**: **CRÍTICA**
- **Trigger / sinal de alerta**: qualquer query a repositório sem escopo de tenant; resposta de API que retorne entidade sem verificação de propriedade; teste negativo de isolamento inexistente ou falhando.
- **Mitigação**: (a) tornar o escopo por tenant **estrutural** — repositórios que exigem `owner_id` na assinatura, não opcional; (b) **teste negativo obrigatório**: usuário A autenticado tentando ler recurso de B deve receber `404` (não `403`, para não vazar existência); (c) incluir o isolamento na Onda 3 antes de qualquer UI multiusuário; (d) criptografia em repouso e em trânsito na Onda 5.
- **Plano de contingência**: se o isolamento não puder ser garantido estruturalmente na Onda 3, **não liberar a Onda 4** — manter a aplicação single-tenant até o isolamento ser provado. Vazar dado genético é falha irreversível, não um bug a corrigir depois.
- **Owner**: Designer (modelo/agregados) + Agente de codificação + Adriano (aceite de risco residual)
- **Status**: aberto

### RISK-006
- **Descrição**: **Conformidade LGPD/GDPR não especificável.** O brief exige conformidade para dado genético, mas o legado não tem nenhum elemento correlato (sem usuário, sem persistência, sem consentimento, sem expurgo, sem log de auditoria) e o usuário **ainda não declarou** base legal nem prazo de retenção (BR-HUMANA-007). A Onda 5 não pode ser completamente especificada.
- **Categoria**: regulatório
- **Probabilidade**: alta
- **Impacto**: alto
- **Severidade combinada**: **ALTA**
- **Trigger / sinal de alerta**: início da Onda 5 sem base legal e prazo de retenção definidos; coleta de dado genético de usuário externo antes de consentimento instrumentado.
- **Mitigação**: (a) implementar criptografia e isolamento já nas Ondas 2–3 (estruturais, não dependem de decisão de negócio); (b) **bloquear o go-live com usuários externos** até consentimento, retenção e direito de exclusão existirem; (c) obter do usuário a definição de base legal e prazo de retenção **antes** de a Onda 5 começar.
- **Plano de contingência**: se as definições não vierem, operar com retenção mais restritiva e conservadora (expurgo agressivo + consentimento explícito de finalidade única) e registrar como decisão provisória a revisar — nunca operar sem consentimento.
- **Owner**: Adriano (decisão de negócio) + Agente de codificação (implementação)
- **Status**: aberto

### RISK-007
- **Descrição**: **Validação de upload insuficiente.** A decisão BR-HUMANA-001 aprovou validar extensão/MIME/tamanho e escopar por usuário, mas o parse do conteúdo permanece intacto por paridade. Se a validação for implementada de forma frouxa, um arquivo malicioso ou gigante alcança o parser `ged4py`/pandas — superfície de abuso e de negação de serviço num produto público.
- **Categoria**: técnico
- **Probabilidade**: média
- **Impacto**: médio
- **Severidade combinada**: **MÉDIA**
- **Trigger / sinal de alerta**: upload aceito sem verificação de tipo declarado vs conteúdo; ausência de limite de tamanho; nomes de arquivo do cliente usados em caminho.
- **Mitigação**: chave de armazenamento gerada pelo servidor (UUID) e nome original apenas como metadado (já descartado em BR-DESCARTAR-003); limite de tamanho explícito; validação de extensão **e** verificação de que o conteúdo é GEDCOM antes do parse; isolamento por `owner_id`.
- **Plano de contingência**: se a validação estrita rejeitar GEDCOM válido de algum exportador (risco de paridade), **relaxar apenas a validação de extensão** e manter limite de tamanho + chave gerada, registrando a exceção.
- **Owner**: Agente de codificação + Designer (modelo de armazenamento)
- **Status**: mitigando

### RISK-008
- **Descrição**: **Escopo integral + multiusuário + conformidade, sem prazo, com decisor único** (AMB-003). Todas as decisões humanas recaem sobre uma pessoa. O projeto pode progredir indefinidamente sem atingir cutover, porque não há pressão externa que force priorização — e cada onda revela novas decisões (a Onda 3 já deixou aberta a questão de o que `gedcom_filename` referencia no alvo).
- **Categoria**: organizacional
- **Probabilidade**: alta
- **Impacto**: médio
- **Severidade combinada**: **ALTA**
- **Trigger / sinal de alerta**: ondas que não fecham; decisões abertas acumulando sem bloqueio; trabalho iniciado na Onda N+1 antes de a Onda N ter paridade provada.
- **Mitigação**: (a) tratar cada onda como entregável **fechado**, com critério de saída verificável; (b) **proibir** avanço de onda com paridade pendente — a única regra de sequenciamento rígida; (c) manter a Onda 1 como prioridade absoluta, já que concentra todo o risco e não depende de nenhuma decisão de negócio em aberto; (d) revisar o `ambiguity_log.md` a cada transição de onda.
- **Plano de contingência**: se a Onda 1 travar, reduzir escopo explicitamente com o usuário (candidato natural: adiar a visualização de grafo) em vez de manter o escopo integral e não entregar nada.
- **Owner**: Adriano (decisor) + orquestrador (disciplina de gate)
- **Status**: mitigando

### RISK-009
- **Descrição**: **Ambiente e dependências do oráculo.** O `requirements.txt` do legado não tem versões fixadas (`architecture.md` §5, dívida #1 🔴) e o projeto já roda sob **Python 3.14** localmente (`reconstructed/__pycache__/*.cpython-314.pyc`), enquanto o alvo declara Python 3.12+. `ged4py`, `networkx`, `thefuzz`, `pandas` e `python-Levenshtein` podem comportar-se de forma diferente entre versões — e uma mudança de biblioteca **muda o resultado sem mudar uma linha de código nosso**.
- **Categoria**: técnico
- **Probabilidade**: média
- **Impacto**: alto
- **Severidade combinada**: **ALTA**
- **Trigger / sinal de alerta**: divergência de paridade concentrada em `fuzz.token_sort_ratio`/`partial_ratio`; parsing GEDCOM diferente; necessidade de fixar versões para o oráculo reproduzir.
- **Mitigação**: congelar as versões do **oráculo** no ambiente em que os golden files forem gerados e documentar a combinação exata; fixar as versões do alvo (`pins` obrigatórios — resolve a dívida #1); comparar a versão de cada biblioteca de matching entre oráculo e alvo **antes** de culpar o port; considerar substituir `thefuzz`+`python-Levenshtein` por implementação própria **somente** se a paridade exigir e com validação diferencial.
- **Plano de contingência**: se as versões do legado não forem instaláveis hoje, gerar os golden files no ambiente mais próximo possível, documentar a divergência conhecida e adicionar casos que isolem o efeito da versão.
- **Owner**: Agente de codificação + Inspector
- **Status**: aberto

### RISK-010
- **Descrição**: **Dependência de decisor único e de conhecimento tácito.** O único stakeholder é o próprio usuário (AMB-002), e parte do conhecimento do legado existe apenas no código (`app.py`), sem outra fonte. Se o usuário ficar indisponível, nem as decisões de negócio pendentes (base legal, retenção) nem a validação de ambiguidades podem avançar.
- **Categoria**: organizacional
- **Probabilidade**: baixa
- **Impacto**: médio
- **Severidade combinada**: **MÉDIA**
- **Trigger / sinal de alerta**: itens PENDENTES no `ambiguity_log.md` sem resposta por período prolongado; necessidade de decisão de negócio durante implementação da onda.
- **Mitigação**: manter `ambiguity_log.md` e `target_business_rules.md` como **fonte única de verdade auditável**, de modo que qualquer implementador entenda o porquê de cada decisão sem perguntar; documentar o oráculo de forma que ele fale por si (goldens autoexplicativos); registrar no `handoff.md` tudo que depende de decisão humana.
- **Plano de contingência**: sem usuário, a Onda 1 (núcleo puro, validado por oráculo) pode prosseguir integralmente — é justamente a onda que não depende de nenhuma decisão de negócio. Ondas 3–5 param.
- **Owner**: Adriano + orquestrador (documentação)
- **Status**: aberto

### RISK-011
- **Descrição**: **Perda silenciosa das regras de decomposição do caminho.** BR-DESCARTAR-005 remove a geração de Mermaid/pyvis no servidor. As funções `split_path_by_marriage` e `are_spouses` codificam **como o parentesco é decomposto** na conexão indireta (divisão no 1º par de cônjuges adjacentes, âncoras de casamento). Se a implementação do grafo no React tratar todo o assunto como preocupação de UI, essas regras desaparecem — e a paridade da conexão indireta quebra sem que nenhum teste de matching falhe.
- **Categoria**: técnico
- **Probabilidade**: média
- **Impacto**: médio
- **Severidade combinada**: **MÉDIA**
- **Trigger / sinal de alerta**: ausência de `split_path_by_marriage`/`are_spouses` equivalentes na camada de domínio do alvo; `parity_tests/` cobrindo conexão direta mas não a **indireta por casamento**; lógica de divisão por cônjuges aparecendo dentro de componente React.
- **Mitigação**: migrar ambas como **funções puras de domínio** (decidido em BR-HUMANA-008); exigir `parity_tests/` específicos para conexão indireta com múltiplas afinidades; incluir no `target_domain_model.md` a estrutura de caminho tipada (ramos, MRCA, par de cônjuges).
- **Plano de contingência**: se a estrutura tipada for adiada, implementar as duas funções no núcleo e expor o caminho já decomposto no payload, mantendo as regras fora da UI.
- **Owner**: Designer (modelo de domínio) + Inspector (cobertura de paridade)
- **Status**: aberto

### RISK-012
- **Descrição**: **Capacidade do time na stack alvo.** O alvo combina FastAPI + PostgreSQL + React/TypeScript + multitenancy + conformidade — superficie bem maior que o legado Flask single-user de ~888 linhas. Se a experiência com esse conjunto for baixa, o gargalo deixa de ser a paridade do matching (que o oráculo resolve) e passa a ser a construção da fronteira, onde não existe oráculo para guiar.
- **Categoria**: organizacional
- **Probabilidade**: média
- **Impacto**: médio
- **Severidade combinada**: **MÉDIA**
- **Trigger / sinal de alerta**: ondas 2–4 consumindo tempo desproporcional ao tamanho; retrabalho de modelo de dados; decisões de tenancy sendo refeitas.
- **Mitigação**: aproveitar que a fronteira é **modernização livre** (o `paradigm_decision.md` não exige fidelidade nela) para escolher as opções mais convencionais e bem documentadas; manter o núcleo isolado da fronteira, de modo que atraso de UI/infra não bloqueie a prova de paridade; começar pelas ondas 0–1, que não exigem a stack nova.
- **Plano de contingência**: priorizar a Onda 1 + uma fronteira mínima viável (Onda 2) e adiar UI (Onda 4) e conformidade (Onda 5) — o núcleo provado tem valor mesmo sem o produto completo.
- **Owner**: Adriano (capacidade) + Agente de codificação
- **Status**: aberto

## Resumo por severidade

| Severidade | Quantidade | IDs |
|---|---|---|
| **Crítica** | 3 | RISK-001, RISK-002, RISK-005 |
| **Alta** | 5 | RISK-003, RISK-004, RISK-006, RISK-008, RISK-009 |
| **Média** | 4 | RISK-007, RISK-010, RISK-011, RISK-012 |
| **Baixa** | 0 | — |

**12 riscos: 3 críticos, 5 altos, 4 médios.**

> Os 3 críticos têm uma característica comum: **dois deles (RISK-001 e RISK-002) são o mesmo risco visto de dois ângulos** — a fidelidade do núcleo e a validade do instrumento que a mede. Ambos são endereçados pela Onda 0. O terceiro (RISK-005) é endereçado estruturalmente na Onda 3. Nenhum dos três depende de prazo, orçamento ou infraestrutura: dependem de disciplina de sequenciamento.

## Riscos relacionados ao paradigma alvo

> Subseção dedicada à mudança de paradigma (`procedural → OO com DI`, gap **alto**), conforme exigido pelo SKILL.md do Strategist.

- **RISK-001 — Perda de fidelidade do matching viral.** Origem direta no gap: o port de `app.py` para funções puras exige mover lógica que hoje vive **dentro de um bloco de rota** (`process_dna_action`), misturada com `pandas` e variáveis de contexto de template. Extrair essa lógica é exatamente a operação em que um limiar pode ser reordenado, um desempate invertido ou uma ordem de avaliação alterada. O paradigma alvo **exige** essa extração (a lógica não pode permanecer no controller); portanto o risco é criado pela própria migração.
- **RISK-005 — Vazamento de dados entre usuários.** Origem direta no gap: o legado é procedural com **estado global de processo** — "a árvore atual" é uma variável de módulo. O paradigma alvo (OO com DI + repositórios escopados) só elimina o vazamento se a conversão for feita de forma **estrutural**. Converter mecanicamente o global em um campo de serviço ou em um cache compartilhado preservaria o vazamento com aparência de arquitetura moderna — o pior dos dois mundos.
- **RISK-011 — Perda das regras de decomposição do caminho.** Origem direta no gap: no legado, a decomposição do parentesco e sua **apresentação** são a mesma coisa (a função gera Mermaid). O paradigma alvo separa domínio de apresentação — e a separação é um ato de julgamento, não um passo mecânico. O gap cria a oportunidade de perder a regra junto com a tecnologia.
- **RISK-009 — Divergência de bibliotecas.** Origem direta no gap: o paradigma alvo reescreve a fronteira de I/O, o que abre a tentação de também modernizar as dependências de matching (`thefuzz`, `python-Levenshtein`). Modernizar biblioteca que produz valor de domínio **é** alterar o domínio, ainda que o código pareça equivalente.
- **Risco operacional obrigatório (gap alto declarado)**: **a mudança de paradigma é simultaneamente a principal fonte de risco e o principal objetivo da migração.** Não há como reduzir o gap sem reduzir o valor da migração. A mitigação viável não é evitar o gap, e sim **isolá-lo no tempo**: executar a parte paradigmática que toca o núcleo (Onda 1) sob diferencial estrito, antes que a parte paradigmática que não toca o núcleo (Ondas 2–5) traga complexidade nova. Registrado explicitamente conforme a regra absoluta do Strategist: *"Mudança grande de paradigma sempre dispara registro explícito de risco operacional."*

---
*Gerado pelo Reversa-Strategist em 2026-09-28.*

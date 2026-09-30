---
schemaVersion: 1
generatedAt: 2026-09-28T02:45:48Z
reversa:
  version: "1.2.58"
kind: ambiguity_log
producedBy: orchestrator
hash: "sha256:97ee497482a263ffc74e7539f8583150671012313c1e8763a60623c22a22a1b8"
---

# Ambiguity Log

> Consolidação de todos os itens ⚠️ AMBÍGUOS ou pendentes detectados pelos agentes ao longo do pipeline.
> Status final esperado quando o pipeline conclui: nenhum item PENDENTE.

## Resumo
- Total de itens: 24
- PENDENTES: **0**
- RESOLVIDOS COM DECISÃO HUMANA: 12
- REFERIDOS À CODIFICAÇÃO: 12

> ✅ **Estado: nenhum item PENDENTE.** Os 9 itens abertos pelo Curator (AMB-006 a AMB-014) foram decididos em 2026-09-28T02:56:00Z; AMB-015 a AMB-024 foram adicionados pelos agentes seguintes (Designer, Screen Translator, Inspector) e pela **verificação empírica do oráculo** pós-handoff (AMB-023 e AMB-024), e todos nascem REFERIDOS À CODIFICAÇÃO — são decisões de implementação que não bloqueiam o início da codificação. O requisito do Passo 7 (0 pendentes ao fim do pipeline) está **satisfeito**.
>
> ⚠️ **Precedente importante**: AMB-023 e AMB-024 são **erros na spec de origem** (`domain.md` §2.1 e `upload-gedcom/requirements.md`), herdados da descoberta e propagados por todos os artefatos. Ambos foram encontrados **executando o oráculo** — o primeiro sobre uma fixture, o segundo sobre **dados reais**. Confrontar as specs com o oráculo **antes da Onda 1** é o passo de maior valor pendente.

## Itens

### AMB-001
- **Descrição**: Artefato obrigatório `_reversa_sdd/gaps.md` ausente, embora listado com `required: true` em `references/expected_legacy_artifacts.yaml`. A verificação de pré-condições do `/reversa-migrate` bloqueia o pipeline nesse caso.
- **Detectado por**: orchestrator
- **Origem**: pré-condições (Passo 1) — `expected_legacy_artifacts.yaml` linha 39
- **Status**: RESOLVIDO COM DECISÃO HUMANA
- **Decisão tomada**:
  - **Escolha**: Prosseguir com o pipeline, substituindo `gaps.md` por `confidence-report.md` § "Lacunas Pendentes (🔴)" + `questions.md` como fonte de lacunas. Justificativa factual: o próprio SKILL.md do Reviewer declara que `gaps.md` "não" é input do confidence-report, mas sim **incorporado** nele — e o `confidence-report.md` presente contém a seção de 17 lacunas agrupadas por unit.
  - **Decisor**: Adriano
  - **Quando**: 2026-09-28T02:45:48Z
  - **Justificativa**: Evitar uma nova passada completa do Time de Descoberta (Scout → Reviewer), que reclassificaria artefatos pré-existentes, quando o conteúdo exigido já está disponível de forma estruturada. Registrado aqui para que o Curator saiba que a fonte é substituta.
  - **Impacto**: O Curator deve tratar `confidence-report.md` § "Lacunas Pendentes (🔴)" como a lista canônica de lacunas. Se alguma lacuna estiver subespecificada por não ter passado pelo `gaps.md`, isso é uma lacuna de rastreabilidade — candidata a item REFERIDO À CODIFICAÇÃO.
  - **Onde gravado**: `_reversa_sdd/migration/migration_brief.md` § Notas livres; `.state.json` § preflight.userOverride

### AMB-002
- **Descrição**: Tensão entre o objetivo declarado (**produto multiusuário / SaaS para usuários externos com dados genéticos sensíveis**) e o stakeholder declarado (**único — o próprio Adriano**). As necessidades dos usuários externos estão sendo inferidas, não validadas por ninguém.
- **Detectado por**: orchestrator (entrevista do brief, Passo 3)
- **Origem**: `migration_brief.md` § Objetivo da migração vs § Stakeholders
- **Status**: REFERIDO À CODIFICAÇÃO
- **Decisão tomada**:
  - **Escolha**: Manter o objetivo SaaS como escopo (decisão explícita do usuário) e transportar a lacuna de validação de usuário externo para a codificação.
  - **Decisor**: Adriano
  - **Quando**: 2026-09-28T02:45:48Z
  - **Justificativa**: O usuário confirmou explicitamente incluir auth/isolamento/persistência no escopo desta migração. Não cabe ao pipeline inventar personas ausentes; cabe sinalizar que as necessidades de UX e consentimento dos usuários externos não foram validadas por pesquisa.
  - **Impacto**: Requisitos de UX, onboarding e consentimento no alvo derivam de inferência. Antes de abrir para usuários reais, validar com pelo menos um usuário externo representativo.
  - **Onde gravado**: `migration_brief.md` § Stakeholders (nota de tensão)

### AMB-003
- **Descrição**: Tensão de dimensionamento — escopo **integral** (todos os módulos, incluindo visualização de grafo) + **multiusuário** + **conformidade LGPD/GDPR**, declarados como **sem prazo e sem orçamento**, com **decisor humano único**.
- **Detectado por**: orchestrator (entrevista do brief, Passo 3)
- **Origem**: `migration_brief.md` § Escopo declarado vs § Restrições
- **Status**: REFERIDO À CODIFICAÇÃO
- **Decisão tomada**:
  - **Escolha**: Não reduzir escopo unilateralmente. O `Strategist` deve fatiar a entrega em ondas e o `handoff.md` deve carregar essa orientação.
  - **Decisor**: Adriano (escopo) / orquestrador (registro)
  - **Quando**: 2026-09-28T02:45:48Z
  - **Justificativa**: O usuário escolheu explicitamente "tudo entra; sem prazo rígido" e recusou excluir a visualização de grafo. Reduzir escopo sem aval violaria a decisão. Mas "escopo máximo sem restrição de tempo" com um decisor único é um risco de execução que precisa estar explícito.
  - **Impacto**: Se executado como um big bang, o projeto tem alta chance de nunca atingir cutover. Mitigação obrigatória: ondas entregáveis, com paridade validada por onda.
  - **Onde gravado**: `migration_brief.md` § Escopo declarado (nota do orquestrador)

### AMB-004
- **Descrição**: As 4 respostas de `questions.md` (perguntas críticas 🔴 do Reviewer) foram registradas como respondidas **apenas em prosa** no `reconstruction-plan.md` § "Alertas de pré-voo", sem indicação de que o próprio `questions.md` continha as respostas.
- **Detectado por**: orchestrator (leitura de contexto pré-entrevista)
- **Origem**: `_reversa_sdd/reconstruction-plan.md` § Alertas de pré-voo vs `_reversa_sdd/questions.md`
- **Status**: RESOLVIDO COM DECISÃO HUMANA
- **Decisão tomada**:
  - **Escolha**: Tratar as 4 respostas como **comportamento congelado** → classificar como MIGRAR, nunca reabrir como DECISÃO HUMANA.
  - **Decisor**: Adriano (respostas originais) / orquestrador (consolidação)
  - **Quando**: 2026-09-28T02:45:48Z
  - **Justificativa**: As respostas existem, são inequívocas e foram dadas explicitamente sobre a fidelidade da reimplementação.
  - **Impacto**: As 4 regras correspondentes migram com fidelidade. Ver correção abaixo.
  - **Onde gravado**: `migration_brief.md` § Notas livres
- **⚠️ CORREÇÃO FACTUAL (2026-09-28T02:52:40Z, pelo curator)**: a descrição original deste item afirmava que as respostas estavam "registradas apenas em prosa" no `reconstruction-plan.md`. **Isso está INCORRETO.** As 4 respostas estão **dentro do próprio `questions.md`**, sob a marcação `**Resposta:**` (linhas 16, 27, 38 e 49). O `reconstruction-plan.md` apenas as resume.
  - **Efeito sobre a conclusão**: **nenhum**. A decisão (são comportamento congelado → MIGRAR) permanece, e agora está **melhor fundamentada**: é uma decisão humana explícita registrada no artefato canônico de perguntas, não uma paráfrase de segunda mão.
  - **Efeito sobre a rastreabilidade**: **positivo** — `questions.md` passou a ser fonte citável direta em `target_business_rules.md`: BR-MIGRAR-013 (Pergunta 1), BR-MIGRAR-014 (Pergunta 4), BR-MIGRAR-026 (Pergunta 2), BR-HUMANA-001 (Pergunta 3) e BR-HUMANA-003 (Pergunta 2).
  - **Causa raiz**: o conteúdo de `questions.md` foi inferido a partir do resumo em `reconstruction-plan.md` antes de o arquivo ser lido. Registrado para auditoria do processo.

### AMB-005
- **Descrição**: O Paradigm Advisor exige registrar a **justificativa do usuário** para a escolha de paradigma (regra absoluta: *"Nunca decidir paradigma sem registrar a justificativa do usuário"*). O usuário escolheu a opção 3 (Híbrido) **sem fornecer texto livre** de justificativa.
- **Detectado por**: paradigm_advisor
- **Origem**: `paradigm_decision.md` § Decisão do usuário
- **Status**: RESOLVIDO COM DECISÃO HUMANA
- **Decisão tomada**:
  - **Escolha**: Registrar a escolha 3 (Híbrido) como decisão válida e **reconstruir** a justificativa a partir das restrições que o próprio usuário declarou no `migration_brief.md`, rotulando-a explicitamente como reconstruída pelo agente e sujeita a correção — em vez de bloquear o pipeline pedindo texto livre.
  - **Decisor**: Adriano
  - **Quando**: 2026-09-28T02:50:16Z
  - **Justificativa**: A decisão em si é inequívoca e foi tomada com o diagnóstico completo do gap à vista (as três opções foram apresentadas com consequências concretas). Exigir prosa adicional adicionaria atrito sem informação nova: as restrições do brief (matching congelado, auth/tenant no escopo, LGPD, sem prazo) determinam a escolha de forma dedutível. A transparência sobre a origem da justificativa preserva a auditabilidade.
  - **Impacto**: A justificativa em `paradigm_decision.md` é de origem inferida, não declarada. Se o usuário discordar da racionalidade registrada, deve corrigir o artefato antes de o Designer concluir a Fase 2 — a decisão (opção 3 / `balanced`) permanece válida independentemente da prosa.
  - **Onde gravado**: `paradigm_decision.md` § Decisão do usuário → Justificativa do usuário

### AMB-006
- **Descrição**: Validar extensão/tamanho de upload, gerar nomes de arquivo no servidor e escopar por usuário. O legado não faz nada disso e a descoberta registrou a ausência como **limitação aceita para uso local** (`questions.md` Pergunta 3). O brief atual declara produto **multiusuário público** com **dado genético sensível** — a resposta anterior pressupunha outro contexto.
- **Detectado por**: curator
- **Origem**: `target_business_rules.md` **BR-HUMANA-001**; `discard_log.md` BR-DESCARTAR-006; `questions.md` Pergunta 3
- **Status**: RESOLVIDO COM DECISÃO HUMANA
- **Recomendação do Curator**: **Meio-termo** — validar extensão/MIME e tamanho e escopar por usuário (correções de **fronteira**), **sem** alterar nenhum comportamento de parsing do conteúdo (preservação do **núcleo**). Preservar a limitação não é fidelidade: é transportar um defeito para um contexto onde ele deixa de ser aceitável. Nenhum GEDCOM válido deve passar a ser rejeitado.

- **Decisão (2026-09-28T02:56:00Z)**: Aprovada a recomendacao do Curator. Decisor: Adriano. Quando: 2026-09-28T02:56:00Z. Escolha: meio-termo (opcao 3) - validar extensao/MIME e tamanho e escopar por usuario na fronteira, sem alterar nenhum comportamento de parsing do conteudo. Justificativa: preservar a limitacao de "uso local" nao e fidelidade, e transportar um defeito para um contexto onde ele deixa de ser aceitavel; nenhum GEDCOM valido passa a ser rejeitado.
### AMB-007
- **Descrição**: `app.secret_key = 'f@milyse@rch_dna_edition_v16'` está **hardcoded** no código-fonte. No legado é inócuo; no alvo, a chave protege sessões que dão acesso a dados genéticos — uma chave pública conhecida permite forjar sessão de qualquer usuário.
- **Detectado por**: curator
- **Origem**: `target_business_rules.md` **BR-HUMANA-002**; `architecture.md` §5 dívida #6
- **Status**: RESOLVIDO COM DECISÃO HUMANA
- **Recomendação do Curator**: **Descarte automático** — é segredo de configuração, não regra de negócio; sai do código para variável de ambiente/secret manager, sem impacto em paridade. Registrado apenas porque a dívida é citada nas specs e não deve consumir uma rodada de decisão. Responder "1" move o item para `discard_log.md` como descarte de fronteira.

- **Decisão (2026-09-28T02:56:00Z)**: Aprovada a recomendacao do Curator. Decisor: Adriano. Quando: 2026-09-28T02:56:00Z. Escolha: descarte automatico - `secret_key` sai do codigo e vira configuracao (variavel de ambiente / secret manager). Justificativa: e segredo de configuracao, nao regra de negocio; nenhum impacto em paridade. Registrado em `discard_log.md` como descarte de fronteira.
### AMB-008
- **Descrição**: Homônimos resolvidos pelo **primeiro ID** podem conectar a pessoa errada. A resposta de `questions.md` Pergunta 2 validou o comportamento *"para uso local"*. Em produto multiusuário, conectar a pessoa errada gera parentesco incorreto e pode exibir dados de outra pessoa.
- **Detectado por**: curator
- **Origem**: `target_business_rules.md` **BR-HUMANA-003**; `busca-caminho/design.md` § Riscos 🔴; `questions.md` Pergunta 2
- **Status**: RESOLVIDO COM DECISÃO HUMANA
- **Recomendação do Curator**: **Manter o 1º ID como default e apenas sinalizar ambiguidade no payload** (ex.: `ambiguous_name: true` + lista de IDs candidatos), oferecendo desambiguação na UI como recurso adicional. Preserva a paridade (o default não muda, os `parity_tests/` continuam válidos) e elimina o risco de exibir a pessoa errada. Exigir desambiguação obrigatória quebraria o critério de paridade #1 do brief.

- **Decisão (2026-09-28T02:56:00Z)**: Aprovada a recomendacao do Curator. Decisor: Adriano. Quando: 2026-09-28T02:56:00Z. Escolha: opcao 2 - manter o 1o ID como default e sinalizar ambiguidade no payload (ex.: `ambiguous_name: true` + lista de IDs candidatos), oferecendo desambiguacao na UI como recurso adicional. Justificativa: preserva a paridade (o default nao muda; os `parity_tests/` continuam validos) e elimina o risco de exibir a pessoa errada em produto multiusuario.
### AMB-009
- **Descrição**: Estado global (`people`, `families`, `graph`, `child_to_family`) sobrescrito a cada parse, sem tratamento de concorrência. Em servidor multi-worker, requisições simultâneas corrompem a análise uma da outra; em multiusuário, um usuário pode ver a árvore de outro. `domain.md` §4: *"Sem autenticação/autorização."*
- **Detectado por**: curator
- **Origem**: `target_business_rules.md` **BR-HUMANA-004**; `upload-gedcom/design.md` § Riscos 🔴
- **Status**: RESOLVIDO COM DECISÃO HUMANA
- **Recomendação do Curator**: **Eliminar o conceito de "GEDCOM carregado" global** — árvore como aggregate persistido com `owner_id`, carregada por repositório escopado, tornando o isolamento estrutural em vez de defensivo. É o que o `paradigm_decision.md` já decidiu (implicações 1 e 4). O item existe para dar ao usuário a chance de vetar o custo. ⚠️ **Deixa aberta uma questão de design que o Designer precisa resolver**: o que exatamente `gedcom_filename` referencia no alvo (qual árvore uma requisição de análise usa?).

- **Decisão (2026-09-28T02:56:00Z)**: Aprovada a recomendacao do Curator. Decisor: Adriano. Quando: 2026-09-28T02:56:00Z. Escolha: opcao 1 - eliminar o conceito de "GEDCOM carregado" global; arvore como aggregate persistido com `owner_id`, carregada por repositorio escopado por tenant. Justificativa: torna o isolamento estrutural em vez de defensivo, conforme `paradigm_decision.md` implicacoes 1 e 4. Fica aberta para o Designer a questao do que `gedcom_filename` referencia no alvo.
### AMB-010
- **Descrição**: `strip_bad_utf` usa substituições **manuais e incompletas** de mojibake; a tabela não está transcrita em nenhuma spec, existe apenas em `app.py`. O comportamento é simultaneamente núcleo do matching (sem ele nomes acentuados não casam) e reconhecidamente defeituoso (`architecture.md` dívida #7).
- **Detectado por**: curator
- **Origem**: `target_business_rules.md` **BR-HUMANA-005**; `confidence-report.md` § Lacunas (analise-dna)
- **Status**: RESOLVIDO COM DECISÃO HUMANA
- **Recomendação do Curator**: **Transcrever fielmente do código, inclusive as lacunas** — manter todas as substituições existentes, sem adicionar novas. Corrigir com estratégia robusta (`ftfy`/detecção por bytes) melhoraria a cobertura real mas **mudaria resultados** para os GEDCOM que hoje caem nas lacunas, violando "matching congelado". A evolução correta (fiel + modo robusto opt-in) pode virar item de `/reversa-forward` depois de a paridade estar provada.

- **Decisão (2026-09-28T02:56:00Z)**: Aprovada a recomendacao do Curator. Decisor: Adriano. Quando: 2026-09-28T02:56:00Z. Escolha: opcao 1 - transcrever `strip_bad_utf` fielmente do legado, inclusive as lacunas, sem adicionar substituicoes novas. Justificativa: corrigir com estrategia robusta mudaria resultados para os GEDCOM que hoje caem nas lacunas, violando a restricao "matching congelado" do brief. Modo robusto opt-in fica como candidato a `/reversa-forward` posterior.
### AMB-011
- **Descrição**: As regras A/B/C/D são congeladas e definitivas, mas **não existe oráculo** para provar que foram preservadas: `design.md` § Riscos registra *"difícil de validar sem dados reais/amostra"* e o `confidence-report.md` confirma *"sem base de teste"*. Os 47 testes de `tests/` testam a **reconstrução**, não o legado.
- **Detectado por**: curator
- **Origem**: `target_business_rules.md` **BR-HUMANA-006**; `analise-dna/design.md` § Riscos 🔴
- **Status**: RESOLVIDO COM DECISÃO HUMANA
- **Recomendação do Curator**: **Construir oráculo a partir do próprio legado** — executar `app.py` contra fixtures sintéticos (já existem em `tests/fixtures/`) e congelar as **saídas** como golden files. O brief elege *"paridade de matching ≥ 100% nos casos de teste"* como métrica primária; sem oráculo derivado do legado essa métrica é **inverificável**. É a decisão de maior alavancagem de todo o pipeline. O legado é apenas lido, nunca modificado.

- **Decisão (2026-09-28T02:56:00Z)**: Aprovada a recomendacao do Curator. Decisor: Adriano. Quando: 2026-09-28T02:56:00Z. Escolha: opcao 2 - construir oraculo a partir do proprio legado, executando `app.py` contra fixtures sinteticos e congelando as saidas como golden files. Justificativa: o brief elege "paridade de matching >= 100% nos casos de teste" como metrica primaria; sem oraculo derivado do legado essa metrica e inverificavel, pois os 47 testes existentes validam a reconstrucao contra si mesma. O legado e apenas lido, nunca modificado.
### AMB-012
- **Descrição**: O brief exige conformidade **LGPD/GDPR para dados genéticos** (consentimento, retenção/expurgo, criptografia, direito de exclusão). O legado **não possui nenhum** desses elementos: não há usuário, persistência, endpoint de exclusão nem log de consentimento. Não há spec de origem — é **construção nova**, não curadoria.
- **Detectado por**: curator
- **Origem**: `target_business_rules.md` **BR-HUMANA-007**; `domain.md` §4 🔴; brief § Restrições
- **Status**: RESOLVIDO COM DECISÃO HUMANA
- **Recomendação do Curator**: **Escopo mínimo viável agora + conformidade completa antes do go-live** — criptografia e isolamento já (são estruturais; retrofitar depois é caro), consentimento/retenção/expurgo numa onda dedicada **antes de qualquer usuário externo real**. A opção "escopo completo agora" exige respostas de negócio que você ainda não declarou (qual base legal? qual prazo de retenção?). ⚠️ Combinada com AMB-002, é a lacuna de maior risco regulatório do projeto.

- **Decisão (2026-09-28T02:56:00Z)**: Aprovada a recomendacao do Curator. Decisor: Adriano. Quando: 2026-09-28T02:56:00Z. Escolha: opcao 2 - criptografia e isolamento ja (estruturais); consentimento, retencao e expurgo em onda dedicada antes de qualquer usuario externo real. Justificativa: retrofitar criptografia e isolamento e caro e arriscado; consentimento/retencao dependem de decisoes de negocio ainda nao declaradas (base legal, prazo de retencao).
### AMB-013
- **Descrição**: O legado gera **Mermaid/pyvis no servidor**; com React o grafo passa a ser renderizado no cliente. As funções que geram o diagrama contêm **decisões de negócio** (`split_path_by_marriage` divide no 1º par de cônjuges adjacentes, `are_spouses` verifica casamento) que determinam como a relação é apresentada. Se o cliente redesenhar livremente, essas regras se perdem; exigir Mermaid idêntico no cliente é um objetivo ruim de engenharia.
- **Detectado por**: curator
- **Origem**: `target_business_rules.md` **BR-HUMANA-008**; `discard_log.md` BR-DESCARTAR-005
- **Status**: RESOLVIDO COM DECISÃO HUMANA
- **Recomendação do Curator**: **Preservar a lógica, redesenhar a apresentação** — `split_path_by_marriage`, `are_spouses` e a identificação de cônjuges migram como **funções puras de domínio** que produzem uma estrutura de caminho tipada (ramos, MRCA, par de casamento); o React renderiza essa estrutura com a tecnologia que preferir. Separa corretamente *regra de negócio* (precisa de paridade) de *tecnologia de desenho* (livre). Descartar as funções junto com o Mermaid violaria o `decision-rubric.md`.

- **Decisão (2026-09-28T02:56:00Z)**: Aprovada a recomendacao do Curator. Decisor: Adriano. Quando: 2026-09-28T02:56:00Z. Escolha: opcao 1 - preservar a logica e redesenhar a apresentacao. `split_path_by_marriage`, `are_spouses` e a identificacao de conjuge migram como funcoes puras de dominio que produzem estrutura de caminho tipada; o React renderiza com a tecnologia que preferir, sem Mermaid no servidor. Justificativa: separa regra de negocio (precisa de paridade) de tecnologia de desenho (livre); descartar as funcoes junto com o Mermaid violaria o `decision-rubric.md`.
### AMB-014
- **Descrição**: Dois pontos onde o legado é reconhecidamente frágil face a exportadores reais, enquanto o brief declara compatibilidade com MyHeritage/FTDNA/GEDmatch como **inegociável**: (a) detecção de colunas depende de **ordem/posição** como heurística (`design.md` § Riscos 🟢); (b) regex de ID `[A-Z]{2}\d{7}` com cobertura **não comprovada** entre exportadores (`confidence-report.md`).
- **Detectado por**: curator
- **Origem**: `target_business_rules.md` **BR-HUMANA-009**; `analise-dna/design.md` § Riscos
- **Status**: RESOLVIDO COM DECISÃO HUMANA
- **Recomendação do Curator**: **Preservar por default + ampliar cobertura de forma aditiva** — manter a heurística atual como primeiro caminho e **acrescentar** reconhecimento de mais variações de cabeçalho e formatos de ID como fallback *depois* de a heurística atual falhar. É a única opção que atende as duas restrições simultaneamente: paridade (nada que hoje funciona muda) e compatibilidade de exportadores (o que hoje falha passa a funcionar). ⚠️ Exige que o Inspector **prove que a extensão é aditiva** — nenhum caso de teste existente pode mudar de resultado.

- **Decisão (2026-09-28T02:56:00Z)**: Aprovada a recomendacao do Curator. Decisor: Adriano. Quando: 2026-09-28T02:56:00Z. Escolha: opcao 2 - preservar a heuristica atual como primeiro caminho e acrescentar reconhecimento de mais variacoes de cabecalho e formatos de ID como fallback aditivo. Justificativa: unica opcao que atende paridade (nada que hoje funciona muda) e compatibilidade de exportadores (o que hoje falha passa a funcionar). Exige que o Inspector prove que a extensao e aditiva.

### AMB-015
- **Descrição**: GEDCOM contendo **referência pendente** (`HUSB`, `WIFE`, `CHIL`, `FAMC` ou `FAMS` apontando para xref inexistente). O legado **aceitava** o arquivo — o grafo simplesmente não ganhava a aresta. O alvo, pela invariante I-2 de AGG-01, tende a **rejeitar** com exceção tipada.
- **Detectado por**: designer (Fase 2)
- **Origem**: `data_migration_plan.md` § Notas (Transformação T-01); `target_domain_model.md` AGG-01 I-2
- **Status**: REFERIDO À CODIFICAÇÃO
- **Contexto do conflito**: rejeitar é **melhor engenharia**, mas é **mudança de comportamento observável** e portanto **quebra paridade** — o critério nº 1 do brief. O Designer deliberadamente **não decidiu em silêncio**: registrou a escolha como aberta e recomendou a opção que preserva paridade.
- **Opções**: (a) aceitar e **sinalizar** as referências pendentes no resultado da importação (preserva paridade integralmente; **recomendação do Designer**, coerente com BR-HUMANA-003 — sinalizar em vez de bloquear); (b) **rejeitar**, aceitando a divergência como melhoria deliberada; (c) aceitar por default com validação estrita opcional.
- **Onde decidir**: implementação da Onda 1 (parse). O cenário correspondente já existe em `parity_tests/01-carregar-gedcom.feature` e **documenta a divergência em vez de escondê-la**.

### AMB-016
- **Descrição**: O que `gedcom_filename` referencia no alvo. No legado, era o **nome do arquivo original do cliente** viajando como `<input type="hidden">` e identificando a árvore. No alvo, o identificador é `tree_id` resolvido por sessão/tenant — mas a **interface** entre uma requisição de análise e a árvore sobre a qual ela opera precisa ser definida.
- **Detectado por**: curator (previu), confirmado por designer e screen_translator
- **Origem**: `target_business_rules.md` BR-MIGRAR-033; `target_domain_model.md` § Notas; `screen_deviation_log.md` DEV-002
- **Status**: REFERIDO À CODIFICAÇÃO
- **Relevância**: é a **tradução semântica mais delicada** de todo o pipeline. No legado "GEDCOM carregado" significava "existe no estado global do processo" — condição implícita que persistia entre requisições. No alvo significa "existe árvore persistida pertencente a este usuário". O mecanismo muda; as **mensagens** e o comportamento visível, não (BR-MIGRAR-028).
- **Onde decidir**: `target_architecture.md` BC-02/BC-03, na Onda 3 (quando a persistência existe).

### AMB-017
- **Descrição**: Algoritmo e parâmetros concretos de **criptografia em repouso e em trânsito** para dado genético.
- **Detectado por**: designer
- **Origem**: `migration_brief.md` § Restrições (LGPD/GDPR); BR-HUMANA-007 (opção 2)
- **Status**: REFERIDO À CODIFICAÇÃO
- **Relevância**: requisito **estrutural** — o `cutover_plan.md` § go/no-go exige *"criptografia ativa em repouso"* verificada manualmente. A obrigação está clara; a escolha de algoritmo e gestão de chaves é decisão de implementação. Retrofitar criptografia depois é caro, por isso o brief a coloca já (Onda 3), não na Onda 5.
- **Onde decidir**: Onda 3 (infraestrutura de persistência), antes do go-live.

### AMB-018
- **Descrição**: **Base legal** e **prazo de retenção** para o tratamento de dado genético.
- **Detectado por**: curator (BR-HUMANA-007), reafirmado pelo designer
- **Origem**: `target_business_rules.md` BR-HUMANA-007 § Opções; `target_screens.md` SCR-008 e SCR-009
- **Status**: REFERIDO À CODIFICAÇÃO
- **Relevância**: ⚠️ **É a única lacuna que só o usuário pode responder** — não é técnica. O pipeline especificou a **estrutura** (campos de consentimento, política de retenção, endpoint de exclusão) e a materializou nas telas SCR-008/SCR-009, mas **não pode inventar** a base legal nem o prazo. O `cutover_plan.md` trata isso como **No-go absoluto**: *"Base legal ou prazo de retenção indefinidos"* bloqueia o go-live. Combinada com AMB-002, é a lacuna de maior risco regulatório do projeto.
- **Onde decidir**: pelo **usuário**, antes da Onda 5. As telas já existem como estrutura; o texto jurídico e os valores são conteúdo a fornecer.

### AMB-019
- **Descrição**: Ferramenta de migrations do schema.
- **Detectado por**: designer
- **Origem**: `data_migration_plan.md` § Estratégia de ETL (idempotência das migrations)
- **Status**: REFERIDO À CODIFICAÇÃO
- **Recomendação**: **Alembic** (padrão do ecossistema FastAPI/SQLAlchemy, coerente com a stack do brief). Não fixado como decisão — escolha de implementação de baixo impacto e reversível.
- **Onde decidir**: Onda 2/3, ao criar o repositório novo.

### AMB-020
- **Descrição**: Estratégia de **reprocessamento** quando o GEDCOM é reimportado. O mesmo `owner_id` pode ter múltiplas árvores, e análises antigas referenciam a árvore de origem — falta definir a política de ciclo de vida.
- **Detectado por**: designer
- **Origem**: `target_data_model.md` § Notas (imutabilidade de `match_result`); `target_domain_model.md` AGG-01 I-4
- **Status**: REFERIDO À CODIFICAÇÃO
- **Contexto**: o design já decidiu o essencial — *"o resultado de uma análise não muda; se a árvore for reimportada, cria-se **nova** análise"* (AD-03 e I-4 de AGG-01). Isso **elimina** a classe de bugs em que um resultado antigo é recalculado com dados novos — que era exatamente o comportamento do legado (re-parse a cada POST). O que falta é a **política de produto**: a árvore antiga é mantida, arquivada ou removida? As análises antigas continuam acessíveis?
- **Onde decidir**: Onda 3/4, com SCR-007 e SCR-010 como superfície.

### AMB-021
- **Descrição**: **Determinismo explícito** do núcleo: injeção de relógio e de fonte de aleatoriedade.
- **Detectado por**: inspector
- **Origem**: `screens/golden/manifest.yaml` § `normalizationRules` (`injectClock`, `seedRandom`); `parity_specs.md` § Riscos residuais
- **Status**: REFERIDO À CODIFICAÇÃO
- **Contexto**: o matching do legado **não usa** relógio nem aleatoriedade, então o determinismo não está em risco hoje. Mas as `normalizationRules` do manifesto **exigem** clock fake e seed fixo para a captura de goldens ser reproduzível, e a comparação de paridade pressupõe determinismo. Fixar isso explicitamente no núcleo é o que impede que uma dependência de tempo entre silenciosamente e torne os `parity_tests/` intermitentes.
- **Onde decidir**: Ondas 0/1, na construção do harness diferencial.

### AMB-022
- **Descrição**: **Captura dos golden files das telas literais. Nenhum foi capturado** — todas as entradas do `screens/golden/manifest.yaml` estão com `present: false`. Consequência: a paridade **visual** das 8 entradas literais está **especificada mas não provada**.
- **Detectado por**: inspector
- **Origem**: `screens/golden/manifest.yaml`; `parity_specs.md` § Paridade de telas; caso de borda do SKILL do Inspector (*"Modo literal sem golden files capturados"*)
- **Status**: REFERIDO À CODIFICAÇÃO
- **Contexto**: os cenários `@paridade-visual` foram **emitidos mesmo assim** (conforme o caso de borda), mas a validação é **manual até a captura**. O oráculo legado **é executável** (Flask local), o que torna a captura barata. Ordem recomendada no manifesto, do mais barato ao mais caro: `SCR-G02` (submeter formulário sem arquivo → prova a mensagem congelada *"Nenhum arquivo GEDCOM enviado."* **sem nenhuma fixture**) → `SCR-001` (sem fixture) → `SCR-002/003/004` (uma fixture GEDCOM) → `SCR-005` (GEDCOM + CSV + raiz) → `SCR-G03` (exige navegador headless).
- **Onde decidir**: Onda 0, junto com a materialização das fixtures `.ged`/`.csv`. Captura **manual** em v1 (OQ-02 não automatizada).

### AMB-023
- **Descrição**: O comportamento de `get_relationships_by_cm` para **cM ≤ 0 ou não numérico** estava **errado em todos os artefatos do pipeline**. A spec (`domain.md` §2.1) afirmava que retornava o literal `"Relação distante ou indeterminada"`. **É falso**: o oráculo retorna **lista vazia** (`[]`). O literal só aparece quando o valor é um número **positivo** que não cai em nenhuma das 9 faixas. São **dois casos distintos** que a spec havia fundido em um.
- **Detectado por**: orchestrator, **executando o oráculo congelado** (não lendo o código)
- **Origem**: `_reversa_sdd/oracle/ORACLE_MANIFEST.md` § Comportamento verificado; `domain.md` §2.1 (Observação) — **fonte do erro**
- **Status**: REFERIDO À CODIFICAÇÃO
- **Evidência da execução**: `get_relationships_by_cm(0) == []` e `get_relationships_by_cm(-5) == []`. O código do oráculo é explícito: `if not isinstance(cm_value, (int, float)) or cm_value <= 0: return []`, e o literal é retornado por um caminho diferente (`return poss if poss else ["Relação distante ou indeterminada"]`), alcançável apenas com `cm_value > 0`.
- **Achado adicional da mesma execução**: as faixas se sobrepõem **muito mais** do que os artefatos sugeriam — um mesmo valor pode casar **até 4 faixas simultaneamente** (50 cM retorna 4 relações). O contrato é uma **lista**, não uma relação única. Reforça BR-MIGRAR-020 e **invalida** qualquer implementação que retorne valor escalar.
- **Impacto propagado** (já corrigido): um `relationship_label` obrigatório (`NOT NULL`) no schema era **incompatível** com o caso A. Um teste de paridade escrito a partir da spec teria falhado corretamente — o erro era latente, não hipotético.
- **Correções aplicadas**:
  - `target_business_rules.md` **BR-MIGRAR-021** — título, descrição e bloco de correção factual com os dois casos (A e B).
  - `data_migration_plan.md` — T-02 (tratamento de inválidos) e T-06 (cM → relação).
  - `target_domain_model.md` — VO `RelationshipLabel` passa a ser **anulável**.
  - `target_data_model.md` — `match_result.relationship_label` **deixa de ser `NOT NULL`**.
  - `target_screens.md` — nota da interpolação `result.relationships`.
  - `parity_tests/02-agregacao-segmentos-cm.feature` — cenário reescrito para "sem relação prevista".
  - `parity_tests/09-relacao-por-cm.feature` — **dois** cenários do Caso A (lista vazia) + **novo** cenário do Caso B (literal indeterminada).
- **Lição registrada**: **a spec do legado não era oráculo; o código era.** Este erro sobreviveu a 6 agentes e 7 gates humanos porque todos operaram no nível das specs, exatamente como o desenho do pipeline manda — e o erro **estava na spec de origem** (`domain.md`), herdado da descoberta. Foi encontrado no primeiro minuto em que o oráculo foi **executado**. É o argumento mais forte a favor de executar a Onda 0 antes de qualquer código de produto.
- **Onde decidir**: nada a decidir — já corrigido. Registrado como **precedente**: antes da Onda 1, **execute** o oráculo contra as fixtures para confrontar as specs, em vez de confiar nelas.

### AMB-024
- **Descrição**: O fallback **`"Sem Nome"`** de `get_name` é **mais estreito do que a spec afirma**. O código é `return person.name.format() if person and person.name else "Sem Nome"` — o literal só é produzido quando o objeto de nome é **ausente/falsy**. Quando o objeto **existe mas seu formato resulta vazio**, a função retorna **string vazia**. A spec (`upload-gedcom/requirements.md` § Regras de Negócio) afirma que *"Pessoas sem nome são listadas como 'Sem Nome'"*, o que é **impreciso**.
- **Detectado por**: orchestrator, **executando o oráculo sobre os dados reais do usuário**
- **Origem**: `_reversa_sdd/oracle/ORACLE_MANIFEST.md`; `upload-gedcom/requirements.md` § Regras de Negócio — **fonte do erro**; `code-analysis.md` § Fluxos Alternativos (`get_name`, `app.py:42`)
- **Status**: REFERIDO À CODIFICAÇÃO
- **Evidência da execução** — medição sobre as **6 árvores GEDCOM reais (55.523 nomes)**:

  | Árvore | Total | String vazia | Literal `"Sem Nome"` |
  |---|---|---|---|
  | `Arvore_Unificada_Oficial_V1_2.ged` | 35.460 | **301** | **0** |
  | `sssazevedo_2025-10-07.ged` | 4.420 | 0 | 0 |
  | `Backup-Arvore-Sandro-12-11-2024.ged` | 4.313 | 0 | 0 |
  | `Gedcom_Sandro.ged` | 4.313 | 0 | 0 |
  | `SandroTree.ged` | 3.961 | 0 | 0 |
  | `Adriano_Santos.ged` | 3.056 | **17** | **0** |
  | **TOTAL** | **55.523** | **318 (0,57%)** | **0** |

  O literal `"Sem Nome"` **nunca foi observado em dado real**; o que ocorre é **string vazia**.
- **Impacto na UI**: a string vazia entra na lista de nomes como **opção em branco**, visível e selecionável na `datalist`. O usuário pode escolher um valor vazio e submeter — comportamento que a spec não descreve. Como a lista é ordenada com `sorted()` puro, as entradas vazias aparecem **primeiro**.
- **Impacto no schema**: `display_name` continua `NOT NULL` — **string vazia satisfaz `NOT NULL`**, então não há conflito (diferente do caso do cM em AMB-023). Mas a implementação **não pode** tratar `''` como ausente nem substituí-lo por `"Sem Nome"`.
- **Por que sobreviveu ao pipeline**: **mesmo modo de falha do AMB-023**. A spec de origem descrevia o comportamento "correto e intuitivo"; o código implementa algo mais estreito; nenhum dado real havia sido confrontado. Os 46 testes da reconstrução passam porque as fixtures sintéticas **não exercitam** o caso do nome presente com formato vazio — foi preciso rodar sobre **dados reais** para encontrá-lo.
- **Correções aplicadas**: `target_business_rules.md` (BR-MIGRAR-003, com a correção factual completa e a tabela), `parity_tests/01-carregar-gedcom.feature` (cenário **dividido em três**: nome ausente → `"Sem Nome"`; nome presente com formato vazio → `""`; ordenação com vazios), `target_domain_model.md` (I-6, VO `DisplayName`, entidade `Person`, tabela de regras), `target_data_model.md` (DDL + nota), `data_migration_plan.md` (T-01) e `parity_specs.md` (invariantes e tabela de arquivos).
- **Onde decidir**: nada a decidir — já corrigido. **Segundo caso do mesmo precedente**: o oráculo **executado sobre dados reais** é o único instrumento que revela este tipo de erro. Confrontar as specs com ele **antes** da Onda 1 é o próximo passo de maior valor.

## Itens referidos à codificação
> Lista somente itens com status `REFERIDO À CODIFICAÇÃO`. Aparecem destacados em `handoff.md`.

- AMB-002: Necessidades dos usuários externos do SaaS (UX, onboarding, consentimento) não foram validadas por nenhum usuário real — validar antes de abrir para o público.
- AMB-003: Escopo integral + multiusuário + conformidade, sem prazo/orçamento e com decisor único — entregar em ondas com paridade validada por onda, nunca big bang.
- AMB-015: GEDCOM com referência pendente (`HUSB`/`WIFE`/`CHIL`/`FAMC`/`FAMS` apontando para xref inexistente): o legado **aceitava**; o alvo tende a **rejeitar** pela invariante I-2 de AGG-01. Rejeitar é melhor engenharia mas **quebra paridade**. Recomendação do Designer: aceitar e apenas sinalizar. Decidir na implementação.
- AMB-016: O que `gedcom_filename` referencia no alvo. No legado era o nome do arquivo do cliente identificando a árvore. No alvo é `tree_id` com escopo por sessão/tenant — mas a **interface** entre requisição de análise e árvore carregada precisa ser definida na implementação.
- AMB-017: Algoritmo e parâmetros de criptografia em repouso e em trânsito (dados genéticos). Requisito estrutural da Onda 5, mas a escolha concreta não foi especificada.
- AMB-018: Base legal e prazo de retenção para dado genético. **Decisão de negócio do usuário**, ainda não declarada. Sem ela a Onda 5 (consentimento/expurgo) não pode ser completamente especificada.
- AMB-019: Ferramenta de migrations a usar. Recomendação do Designer: Alembic (padrão do ecossistema FastAPI/SQLAlchemy). Não fixado como decisão.
- AMB-020: Estratégia de reprocessamento quando o GEDCOM é reimportado. Um `owner_id` pode ter várias árvores; resultados antigos referenciam a versão anterior — é preciso definir a política.
- AMB-021: Injeção de relógio e de aleatoriedade no núcleo. O legado não usa nenhum dos dois no matching, mas fixá-los explicitamente é o que garante determinismo dos `parity_tests/` (declarado no `manifest.yaml` como `injectClock` e `seedRandom`).
- AMB-022: Captura dos golden files das telas. **Nenhum foi capturado** (`present: false` em todas as entradas). Enquanto não houver golden, a paridade visual das telas literais está **especificada mas não provada**. Ordem recomendada de captura no `manifest.yaml`.
- AMB-023: `get_relationships_by_cm` com cM ≤ 0 ou não numérico retorna **lista vazia**, não o literal `"Relação distante ou indeterminada"` como a spec afirmava — **dois casos distintos** que a spec havia fundido. Erro já corrigido em 7 artefatos. Descoberto executando o oráculo.
- AMB-024: `get_name` → o fallback `"Sem Nome"` é **mais estreito** do que a spec afirmava (`upload-gedcom/requirements.md`). Medição sobre **55.523 nomes reais**: **318 pessoas (0,57%)** têm **string vazia** e **0** têm o literal `"Sem Nome"`. O fallback só dispara quando o objeto de nome é ausente, não quando o formato resulta vazio. Implementar o fallback "correto" (sempre `"Sem Nome"`) **quebraria paridade**. Corrigido em 7 artefatos. Descoberto executando o oráculo sobre dados reais.

## Notas

- Este log foi criado pelo orquestrador no Passo 4 (inicialização). AMB-001 a AMB-004 vêm dos Passos 1–3 (pré-condições e entrevista do brief). AMB-005 veio do Paradigm Advisor. AMB-006 a AMB-014 vieram do Curator (espelham BR-HUMANA-001 a 009). AMB-015 a AMB-022 foram acrescentados pelo Designer (015, 016, 017, 019, 020), pelo Inspector (021, 022) e um por consolidação (018, levantado pelo Curator e reafirmado pelo Designer).
- Os agentes do Time de Migração **acrescentam** itens, nunca renumeram ou removem os existentes.
- Convenção: `RESOLVIDO COM DECISÃO HUMANA` para o que o usuário decidiu; `PENDENTE` para o que ainda bloqueia; `REFERIDO À CODIFICAÇÃO` para o que o pipeline não pode decidir e o implementador precisa resolver.
- **Regra de fronteira operacional** (do Paradigm Advisor, para todos os agentes posteriores): se o item é *algoritmo de negócio* → núcleo, função pura, fidelidade absoluta. Se é *plumbing* (HTTP, persistência, auth, tenancy, config) → borda, modernização livre. Ambiguidade sobre o lado deve subir para este log.
- **Os 9 itens abertos pelo Curator (AMB-006 a AMB-014) eram esperados**: o legado tem 17 lacunas 🔴 registradas e a migração muda o contexto de uso (local single-user → SaaS público com dado sensível), o que **reativa** decisões que estavam fechadas. AMB-006 e AMB-008 são exatamente respostas válidas para "uso local" que precisavam ser revalidadas. **Todos foram decididos em 2026-09-28T02:56:00Z.**
- **Os 10 itens REFERIDOS À CODIFICAÇÃO (AMB-002, AMB-003, AMB-015 a AMB-022) não bloqueiam nada.** São decisões de implementação — não lacunas de especificação. Nenhum deles impede o início da Onda 0 ou da Onda 1. Dois merecem destaque: **AMB-018** é a única pergunta que só o usuário pode responder (base legal e prazo de retenção) e é **No-go absoluto de go-live**; **AMB-022** registra que a paridade visual das telas literais está especificada mas **não provada**, porque nenhum golden file foi capturado.
- **Correção factual aplicada em AMB-004** pelo Curator: as respostas de `questions.md` estão no próprio arquivo, não apenas em prosa no `reconstruction-plan.md`. Conclusão inalterada; rastreabilidade melhorada.
- **Correção de encoding registrada**: uma corrupção de mojibake (`DECISÃƒO`) foi introduzida por script PowerShell ao fechar as decisões do Curator e corrigida por round-trip UTF-8 explícito. Verificado por varredura de assinaturas de mojibake em todos os artefatos. A única ocorrência remanescente é **intencional**: o exemplo `Ã§` em `target_business_rules.md` BR-MIGRAR-006, que documenta o próprio mojibake.

---
*Gerado pelo Reversa em 2026-09-28.*

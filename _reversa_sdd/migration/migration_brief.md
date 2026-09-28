---
schemaVersion: 1
generatedAt: 2026-09-28T02:45:48Z
reversa:
  version: "1.2.58"
kind: migration_brief
producedBy: orchestrator
hash: "sha256:d49fc0cb9dc2e0837917ab253bf5f2a5cd517f751aacc60e582378da0df7b66d"
---

# Migration Brief

> Documento de critério de migração coletado em entrevista no início do `/reversa-migrate`.
> Consumido pelos seis agentes do Time de Migração. Não pergunta paradigma (responsabilidade do Paradigm Advisor) nem apetite (derivado em `paradigm_decision.md`).

## Objetivo da migração

Transformar o **analisador-genealogico** — hoje um monólito Flask de ~888 linhas, com UI server-side e **estado 100% em memória** — em um **produto multiusuário (SaaS)** de análise de genealogia genética.

O que muda no negócio:

- **Hoje**: ferramenta local, single-user, sem persistência. Cada reinício perde tudo. Sem contas, sem isolamento, sem histórico.
- **Depois**: serviço multiusuário com contas, isolamento de dados por usuário, persistência real de árvores/análises e API desacoplada de UI.
- **Se a migração não acontecer**: o sistema permanece inutilizável para usuários externos (não há como servir dois genealogistas no mesmo processo, nem sobreviver a um restart) e não há caminho de evolução para o produto.

**Núcleo de valor que não pode regredir**: o algoritmo de matching viral de DNA e a busca de caminho na árvore. A migração é de **arquitetura e modelo de entrega**; o comportamento de negócio é congelado (ver Restrições).

## Métricas de sucesso

- **Paridade de matching ≥ 100% nos casos de teste**: para os mesmos arquivos GEDCOM/CSV de referência, o sistema novo produz exatamente os mesmos matches, caminhos e classificações de relação que o legado. Verificação pela suíte `parity_tests/` produzida pelo Inspector.
- **Multiusuário real** (métrica complementar declarada na entrevista): contas funcionais, isolamento de dados por usuário (nenhum cruzamento de árvores/matches entre contas) e persistência sobrevivendo a restart.
- **Cobertura de testes automatizados do domínio** (métrica complementar): suíte substituindo os 47 testes da reconstrução atual, cobrindo regras A/B/C/D, caminhos diretos/indiretos e agregação de segmentos.
- **Deploy do novo stack funcionando ponta a ponta** (métrica complementar): projeto novo buildável, schema migrado e aplicação no ar.

> Nota do orquestrador: na entrevista apenas **paridade de matching** foi marcada explicitamente como métrica primária. As três seguintes foram coletadas nas demais respostas (objetivo SaaS, reaproveitamento da reconstrução testada, ausência de prazo) e ficam registradas como complementares — revisáveis pelo usuário.

## Restrições

- **Prazo**: sem prazo definido. Prioridade explícita em **qualidade sobre velocidade**.
- **Orçamento**: sem orçamento definido. Sem contratação prevista.
- **Técnicas (inegociáveis)**:
  - **Compatibilidade GEDCOM/CSV inegociável** — os arquivos `.ged` e `.csv` dos usuários e os formatos de exportador (MyHeritage, FTDNA, GEDmatch) continuam suportados. Nenhum exportador hoje aceito pode deixar de funcionar.
  - **Matching congelado** — o resultado do matching não pode mudar. Ficam congelados: regras A/B/C/D de aceitação (limiares literais 92/90/86/100), relaxamento de Jaccard 0.5 → 0.33 para cM ≥ 150 e dado não-genérico, regex de ID `[A-Z]{2}\d{7}`, agregação por chave (nome + ID/email) e o matching difuso viral. `HARD_MIN`/`GIVEN_MIN` permanecem código morto.
  - **Reaproveitamento da reconstrução** — a reconstrução fiel em Python (`reconstructed/domain.py`, `upload.py`, `path_search.py`, `dna_analysis.py`, 47 testes) é o **núcleo candidato** do serviço novo. O legado Flask é a referência de comportamento; a reconstrução é o ponto de partida do código.
- **Regulatórias**:
  - **LGPD/GDPR para dados genéticos**. Dados genéticos são categoria sensível. Requisitos explícitos no escopo: base legal/consentimento, finalidade, retenção e expurgo, criptografia em trânsito e repouso, direito de exclusão do titular e minimização.
- **Operacionais**: sem janela de manutenção definida — não há produção a preservar. Não há SLA a cumprir durante a migração (o legado nunca foi servido a usuários externos).

## Fatores de risco conhecidos

- **Fidelidade do matching de DNA (#1)** — risco principal declarado. O matching viral é heurístico, com limiares literais e relaxamentos intencionais; qualquer "limpeza" durante a reescrita muda resultados silenciosamente. Mitigação: `parity_tests/` obrigatórios antes de qualquer refatoração.
- **Volatilidade do estado → persistência** — o legado mantém tudo em memória com estado global mutável; a reconstrução preservou isso de propósito (`clear` + `update` in-place). Introduzir persistência e concorrência multiusuário ataca diretamente essa decisão de fidelidade.
- **Isolamento entre usuários** — um estado global compartilhado é, por construção, um vazamento entre contas. É simultaneamente requisito de produto e requisito regulatório.
- **Dados genéticos sensíveis** — vazamento tem impacto regulatório e irreversível (dado genético não é revogável). Exige tratamento de segurança desde o design, não como hardening posterior.
- **Comportamento informal do legado** — caminho por pais assume famílias nucleares (famílias adotivas/complexas não cobertas), homônimos resolvidos pelo 1º ID, upload sem validação de extensão/tamanho, colisão de nomes em `uploads/` sobrescreve. Migrar "correto" aqui romperia paridade; migrar "igual" carrega os defeitos para o produto.
- **Duas fontes de verdade** — specs do Reversa, código legado e reconstrução podem divergir entre si. Toda divergência deve ser explicitada, não silenciada.

## Stakeholders

| Nome / papel | Responsabilidade na migração |
|---|---|
| Adriano (usuário, decisor único) | Aprova paradigma, topologia, estratégia e arquitetura. Único decisor humano das pausas do pipeline. |
| Time de Migração Reversa (6 agentes) | Produzir as specs alvo, o plano de dados e os testes de paridade. |
| Agente de codificação (a definir) | Implementar o sistema novo a partir do `handoff.md`. |
| Usuários externos futuros | Consumidores do produto SaaS. **Ainda não ouvidos** — a entrevista declarou stakeholder único; requisitos de UX/consentimento capturados apenas via requisitos regulatórios. |

> ⚠️ Tensão registrada pelo orquestrador: o objetivo declarado é um **produto para usuários externos com dados sensíveis**, mas o stakeholder declarado é **único**. Isso significa que as necessidades dos usuários externos estão sendo **inferidas**, não validadas. Registrado em `ambiguity_log.md` para o Curator/Designer.

## Stack alvo

- **Linguagem**: Python 3.12+
- **Framework**: FastAPI
- **Banco**: PostgreSQL
- **Mensageria**: não definida (nenhuma necessária identificada — processamento é síncrono por requisição no legado). A confirmar pelo Designer.
- **Infra**: não definida. Sem prazo/restrição de infra declarados. Requisito implícito: criptografia em repouso e em trânsito (dados genéticos).
- **Front-end**: React + TypeScript (SPA), substituindo a renderização server-side Jinja2 + Bootstrap 5.
- **Outros componentes relevantes**: observabilidade não definida na entrevista; considerar que o legado possui visualização de grafo via `pyvis` (`static/graph_path_search.html`) que precisa de equivalente no alvo.

## Escopo declarado

- **Incluído**:
  - **Multiusuário/SaaS**: contas, autenticação, **isolamento de dados por usuário**, persistência (árvores GEDCOM, uploads, análises e resultados).
  - **Conformidade**: requisitos LGPD/GDPR para dados genéticos (consentimento, retenção/expurgo, criptografia, direito de exclusão).
  - Todos os módulos do legado: `upload-gedcom` (upload + parsing `.ged` + construção do grafo), `busca-caminho` (conexão direta por ancestral comum + fallback indireto por afinidade), `analise-dna` (agregação de segmentos `.csv`, matching viral, regras A/B/C/D, tabela de relação por cM, caminho até a raiz) e a **visualização do grafo**.
  - Camada de API REST (hoje inexistente) + front-end React.
- **Excluído**: nada foi declarado como excluído. O escopo é integral — inclusive a visualização de grafo, que a entrevista optou por manter em vez de adiar.

> Nota do orquestrador: o escopo **integral + multiusuário + conformidade** foi declarado como "sem prazo" e "sem orçamento". Isso é uma tensão de dimensionamento real: escopo máximo, restrição de tempo nula, mas capacidade presumidamente finita (decisor único). Registrado em `ambiguity_log.md` — o Strategist deve fatiar em ondas.

## Notas livres

- **Nível de documentação do legado**: `essencial`. Não existem `data-dictionary.md`, `state-machines.md`, `permissions.md` nem `traceability/code-spec-matrix.md`. Não há schema de banco a migrar (estado 100% em memória), então o `data_migration_plan.md` tende a ser de **modelagem nova**, não de conversão de dados existentes.
- **Artefato `gaps.md` ausente**: `_reversa_sdd/gaps.md` não existe, embora seja listado como obrigatório em `expected_legacy_artifacts.yaml`. **Decisão do usuário nesta sessão**: prosseguir usando `confidence-report.md` (§ "Lacunas Pendentes (🔴)", 17 lacunas) + `questions.md` como fonte de lacunas. Registrado em `ambiguity_log.md`.
- **Lacunas já resolvidas no legado**: as 4 perguntas de `questions.md` foram respondidas durante a reconstrução (`reconstruction-plan.md` § Alertas de pré-voo): regras A/B/C/D são comportamento definitivo; homônimos mantêm o 1º ID; upload sem política de segurança é limitação aceita; relaxamento de Jaccard é intencional.
- **Correção já aplicada na reconstrução**: `upload.py` muta as globais in-place (`clear` + `update`) para manter válidas as referências importadas por `path_search`/`dna_analysis`. Isso é um artefato do estado global e **não deve ser transportado** para o alvo multiusuário — mas o comportamento observável sim.
- **UI do legado**: 1 tela (`templates/index.html`) + `static/graph_path_search.html` (pyvis). UI server-side, single-user, sem RBAC — a entrevista de descoberta classificou fluxos de usuário como "não aplicável", o que **deixa de valer** agora que o alvo é multiusuário.
- **Suíte de testes atual**: 47 passed (`tests/`) sobre a reconstrução. Servem de base factual para os `parity_tests/` do Inspector, mas testam código, não comportamento do legado — o Inspector deve decidir o que é oráculo válido.

# Domínio de Negócio — analisador-genealogico

> Nível de documentação: **Essencial** (`state.json` → `doc_level`)
> Re-extração de 2026-09-30. Substitui o `domain.md` de 2026-08-03.
> Escala de confiança: 🟢 CONFIRMADO | 🟡 INFERIDO | 🔴 LACUNA

---

## 1. Glossário de Domínio

| Termo | Definição |
| --- | --- |
| **GEDCOM** | Formato padronizado (`.ged`) para troca de árvores genealógicas. Define registros `INDI` (pessoa) e `FAM` (família). 🟢 |
| **INDI** | Registro de indivíduo, identificado por `xref_id` (ex.: `@I0001@`). `FAMC` referencia a família onde é filho(a); `FAMS` as famílias onde é cônjuge. 🟢 |
| **FAM** | Registro de família, identificado por `xref_id` (ex.: `@F1@`). Campos `HUSB` (marido), `WIFE` (esposa) e `CHIL` (filhos). 🟢 |
| **DNA Match** | Pessoa do relatório CSV de parentes compartilhados (ex.: GEDmatch Ancestor Project) com valor de cM compartilhado. 🟢 |
| **cM (centiMorgan)** | Unidade de recombinação genética; valor maior indica parentesco mais próximo. 🟢 |
| **Ancestral Comum / MRCA** | Ascendente mais recente compartilhado entre duas pessoas. Base da conexão direta. 🟢 |
| **Grupos de segmento** | Vários segmentos de DNA do mesmo match; agregados por chave e **somados** em cM. 🟢 |
| **Mojibake** | Caracteres corrompidos por encoding incorreto (Latin-1 lido como UTF-8), comum em nomes portugueses. 🟢 |
| **Ponte matrimonial** | Elo de afinidade (casamento) entre dois ramos que não compartilham ancestral. Base da conexão indireta. 🟢 |
| **Casal (nó composto)** | No diagrama, quando o ancestral comum tem cônjuge presente no caminho, os dois são fundidos num único nó. 🟢 |
| **Descartado / skipped** | Match que o sistema **não** conseguiu conectar. Exibido ao usuário para auditoria. 🟢 |

---

## 2. Regras de Negócio Principais

### 2.1. Relação prevista por faixa de cM 🟢

O cM total (soma dos segmentos de um match) é traduzido em relações prováveis via `SHARED_CM_DATA`:

| Faixa de cM | Relação prevista |
| --- | --- |
| 3300–3720 | Pai/Mãe ↔ Filho(a) |
| 2200–3400 | Irmãos completos |
| 1317–2312 | Avós/Netos, Tios/Tias ↔ Sobrinhos(as), Meios-irmãos |
| 553–1330 | Primos de 1º grau |
| 200–850 | Primos de 1º grau (1× removido), Meios-primos, Tios-avós ↔ Sobrinhos-netos |
| 46–515 | Primos de 2º grau |
| 30–350 | Primos de 2º grau (1× removido), Primos de 3º grau |
| 10–220 | Primos de 3º grau (1× removido), Primos de 4º grau |
| 0–110 | Primos de 4º/5º grau ou mais distantes |

**O contrato é uma LISTA, nunca um escalar.** As faixas se sobrepõem até 4 vezes: 50 cM casa 4 faixas simultaneamente, 300 cM casa 3, e 3400/800/15 casam 2 cada. A tela exibe todas as relações aplicáveis concatenadas. 🟢

| Entrada | Retorno | Conf. |
| --- | --- | --- |
| `cM ≤ 0` | **lista vazia** `[]` | 🟢 |
| `cM` não numérico | **lista vazia** `[]` | 🟢 |
| `cM` positivo dentro de ≥ 1 faixa | lista das relações dessas faixas | 🟢 |
| `cM` positivo fora de todas as faixas | `["Relação distante ou indeterminada"]` | 🟢 |

> ⚠️ **Correção contra a extração anterior.** O `domain.md` de 2026-08-03 afirmava que "cM `<= 0` ou não numérico retorna 'Relação distante ou indeterminada'". **Isso está errado.** O código (`dna_analysis.py:62-64`) devolve lista vazia nesses dois casos; o literal só aparece com valor positivo fora de todas as faixas. A correção já havia sido registrada como `AMB-023` no `migration/ambiguity_log.md` — veio do confronto empírico com o oráculo congelado.

### 2.2. Conexão genealógica: direta e indireta 🟢

A busca tem **dois estágios, nesta ordem** — o segundo só roda se o primeiro falhar:

| Estágio | Método | Suba por | Teto | Mensagem de sucesso |
| --- | --- | --- | --- | --- |
| **Direta** | BFS bidirecional (`find_ancestral_path`) | **apenas pais** (`FAMC` / `child_to_family`) | 20 iterações de profundidade | `"Conexão direta encontrada (ancestral comum)."` |
| **Indireta** | `nx.shortest_path` (`find_indirect_path`) | **qualquer parentesco** no grafo pessoa↔família | 40 arestas | `"Conexão indireta encontrada (via casamento/afinidade)."` |

Se nenhum dos dois achar caminho: `"Nenhuma conexão encontrada entre '{p1}' e '{p2}'."` com `success=True`. 🟢

> 🟡 **L-03:** o teto 20 conta **iterações de profundidade** do BFS bidirecional (cada iteração expande um nível de um dos lados), não gerações. O efeito prático do corte não está documentado em nenhum lugar. A palavra "profundidade máxima 20 níveis" usada na extração anterior é uma simplificação imprecisa.

### 2.3. Matching difuso de nomes 🟢

- **Limpeza de mojibake** — autoridade única em `domain.py` (`strip_bad_utf`, `demojibake`), com 18 pares de correção. Antes do refactor `003`, `dna_analysis` tinha uma cópia divergente que acertava 5 de 9 casos a mais que a de `domain`. 🟢
- **Score** = `0.55×token_sort_ratio + 0.25×partial_ratio + 0.20×ratio(prenome) + InterBonus`, arredondado a 2 casas. 🟢
- **InterBonus** = `8.0 × (nº de sobrenomes em comum) − 4.0 × (quantos deles são sobrenomes comuns)`. 🟢
- **Filtro anti-falso-positivo** — se ambos os lados têm sobrenomes, a interseção é 0 e não há acerto de sufixo (`filho`, `neto`, …), o candidato é **rejeitado** com motivo registrado. 🟢
- **Interseção mínima adaptativa** — prenome genérico (20 nomes em `GENERIC_GIVENS`) com ≥ 2 sobrenomes no CSV eleva a exigência de 1 para 2 sobrenomes em comum. 🟢
- **Jaccard com prefixo suave** — limiar 0.5 com ≥ 2 sobrenomes; cai para **0.33 apenas** quando `cM ≥ 150` **e** o prenome não é genérico. 🟢
- **Equivalentes de grafia** — `netto→neto`, `gouvea`/`gouvêa`/`gouvéia`→`gouveia`. 🟢
- **Abreviações** — prefixos de sobrenome (mín. 3 caracteres) resgatam matches abreviados ou corrompidos. 🟢
- **Conflito de nome do meio** — se o CSV traz um token que não é prenome nem sobrenome e ele não existe no GEDCOM, o aceite é rebaixado a `score ≥ 96` e `given ≥ 92`. 🟢
- **Desempate do candidato** — mais sobrenomes em comum → maior similaridade de prenome → maior score. 🟢
- O cM **não** decide aceitação diretamente; ele só influencia o limiar de Jaccard (regra acima). Confirmado por teste de caracterização (`test_limiar_de_cm_nao_muda_a_decisao`). 🟢

### 2.4. Limites de busca 🟢

| Limite | Valor | Onde |
| --- | --- | --- |
| Profundidade do BFS bidirecional | 20 iterações | `path_search.py:22` |
| Arestas do caminho indireto | 40 | `path_search.py:23` |

---

## 3. Regras de Decisão e Fluxo

| Ação do usuário | Pré-condições | Regra de negócio | Conf. |
| --- | --- | --- | --- |
| **Upload GEDCOM** | arquivo presente e com nome não vazio | Salva em `uploads/` com o nome original; parseia; reconstrói o grafo; devolve os nomes ordenados. Sucesso: `"Arquivo '{nome}' carregado!"` | 🟢 |
| **Path Search** | GEDCOM já carregado + dois nomes resolvíveis | Tenta conexão direta; se falhar, indireta; se ambas falharem, informa sem conexão | 🟢 |
| **DNA Analysis** | GEDCOM carregado + CSV + `root_name` existente no GEDCOM | Agrega segmentos, casa nomes, calcula caminho até a raiz, prevê parentesco, ordena por cM decrescente | 🟢 |
| Match que casa mas sem caminho até a raiz | — | Vai para `skipped_matches` com motivo `"sem caminho subindo por pais (pais ausentes no GED?)"` | 🟢 |
| Match que não casa | — | Vai para `skipped_matches` com o motivo específico da rejeição | 🟢 |
| Pessoa não encontrada por nome | — | `"Pessoa 1 '{nome}' não encontrada."` / `"Pessoa 2 '{nome}' não encontrada."` | 🟢 |

---

## 4. Contrato de Mensagens ao Usuário 🟢

As mensagens abaixo são **texto de contrato**, não prosa: testes de golden file dependem delas de forma literal (ver `migration/parity_harness.md`).

### 4.1. Núcleo (`reconstructed/`)

| Mensagem | Origem | Categoria |
| --- | --- | --- |
| `"{n} conexões encontradas. {m} descartadas."` | `dna_analysis.py:394` | Sucesso |
| `"Conexão direta encontrada (ancestral comum)."` | `path_search.py:485` | Sucesso |
| `"Conexão indireta encontrada (via casamento/afinidade)."` | `path_search.py:494` | Sucesso |
| `"Nenhuma conexão encontrada entre '{p1}' e '{p2}'."` | `path_search.py:490` | Sem resultado |
| `"Pessoa 1 '{nome}' não encontrada."` | `path_search.py:475` | Erro de entrada |
| `"Pessoa 2 '{nome}' não encontrada."` | `path_search.py:477` | Erro de entrada |
| `"Seu nome '{root_name}' não foi encontrado no GEDCOM."` | `dna_analysis.py:348` (exceção) | Erro de entrada |
| `"Colunas de Nome e cM não encontradas no CSV."` | `dna_analysis.py:354` (exceção) | Erro de entrada |
| `"Relação distante ou indeterminada"` | `dna_analysis.py:66` | Fallback de faixa |
| `"sem candidatos por sobrenome (abreviação/corrupção?)"` | `dna_analysis.py:255` | Motivo de descarte |
| `"sem sobrenome em comum (filtro anti-falso-positivo)"` | `dna_analysis.py:289` | Motivo de descarte |
| `"score insuficiente ou conflito de sobrenome (given=…, final=…, inter=…/…, jacc=…)"` | `dna_analysis.py:330-331` | Motivo de descarte |
| `"sem caminho subindo por pais (pais ausentes no GED?)"` | `dna_analysis.py:391` | Motivo de descarte |

### 4.2. Camada de rota (`app.py`)

| Mensagem | Linha |
| --- | --- |
| `"Nenhum arquivo GEDCOM enviado."` | `:24` |
| `"Nenhum arquivo selecionado."` | `:27` |
| `"Erro ao processar GEDCOM: {e}"` | `:34` |
| `"Erro: Arquivo GEDCOM não encontrado."` | `:38` |
| `"Erro: Arquivo '{nome}' não existe mais."` | `:41` |
| `"Por favor, carregue o arquivo CSV de matches."` | `:47` |
| `"Ocorreu um erro: {e}"` | `:63` e `:78` |
| `"Arquivo '{nome}' carregado!"` | `:32` |

---

## 5. Máquinas de Estado

**Não se aplica.** Varredura de `app.py` e de todo `reconstructed/` não encontrou **nenhum** campo de `status`, `state`, `flag`, `enabled`, `active` ou equivalente. Não há entidade central com múltiplos estados, portanto `state-machines.md` **não é gerado** — o que a tabela de `doc_level` do agente autoriza explicitamente para o nível `essencial`.

O único estado que persiste entre requisições é o conteúdo do grafo em memória, e ele é substituído integralmente a cada upload (não transiciona). 🟢

---

## 6. Permissões e Papéis (RBAC/ACL)

**Não se aplica.** Não existe `session`, `login`, `auth`, `logout`, `password` ou `current_user` em nenhum arquivo do sistema. Não há usuários, papéis nem permissões.

**Consequência de negócio, e ela é séria:** a aplicação não distingue usuários. Como o estado é global no processo (`upload.py:16-19`), **dois usuários simultâneos compartilham a mesma árvore** — o upload de um substitui o do outro, e ambos veem os mesmos resultados. Isso já está registrado como risco de isolamento multi-tenant no `migration/risk_register.md`. 🟢

| Verificação | Resultado |
| --- | --- |
| Papéis definidos | nenhum 🟢 |
| Permissões por papel | inexistentes 🟢 |
| Login / sessão | inexistente 🟢 |
| Isolamento de dados por usuário | **inexistente** 🟢 |

---

## 7. ADRs Retroativos (arqueologia Git)

> A extração anterior declarou que ADRs eram impossíveis "porque não há repositório Git". **Isso é falso**: o repositório tem **66 commits**, com histórico de decisões rico. Esta seção corrige a lacuna.
> Nível `essencial` não gera `_reversa_sdd/adrs/`; as decisões ficam consolidadas aqui.

### ADR-01 — Reconstruir o sistema em módulos, sem reescrever o legado 🟢
**Commits:** `6b6483d` (2026-08-03, inicialização), `d2ea17a` / `5ee57c9` (2026-08-07, módulos)
**Decisão:** extrair `domain.py`, `upload.py`, `path_search.py` e `dna_analysis.py` como reconstrução fiel, com testes, em vez de editar o monolito.
**Justificativa observável:** a diretiva não-destrutiva do Reversa e a decisão de usar o legado como referência de comportamento.
**Consequência:** o monolito permaneceu intacto como oráculo potencial — o que mais tarde viabilizou o harness de paridade.

### ADR-02 — Promover `reconstructed/` a subpacote e `app.py` a camada de rota fina 🟢
**Commit:** `f51bac1` (2026-08-11) — feature `002-integrar-rota-app-modulos`
**Decisão:** mover os módulos para `analisador-genealogico/reconstructed/` e reduzir `app.py` de ~887 para ~70 linhas, delegando os três fluxos.
**Justificativa:** eliminar a lógica inline **duplicada** entre rota e módulos — a divergência entre duas cópias da mesma regra era o defeito estrutural.
**Consequência não óbvia:** o `app.py` deixou de ser um oráculo utilizável (`RISK-002`) — passou a importar o próprio candidato, criando risco de validação circular. Foi isso que obrigou o congelamento do commit `e43ca22` como oráculo (ver ADR-04).

### ADR-03 — Migrar a visualização de grafo de Pyvis para Mermaid 🟢
**Evidência:** `pyvis` e `matplotlib` removidos do `requirements.txt`; `O PP-20260929-SEQO` removeu `STATIC_FOLDER`; o README ainda anuncia Pyvis.
**Decisão:** renderizar no cliente com Mermaid 10 via CDN, em vez de gerar HTML estático no servidor com Pyvis.
**Justificativa aparente:** 🟡 reduzir dependências pesadas e eliminar a escrita de arquivos no servidor.
**Consequência:** o servidor deixou de produzir artefato HTML; o diagrama passou a depender de JS no navegador. **E abriu um vetor novo de defeito**: o texto do nó passou a ser interpretado pela gramática do Mermaid, o que gerou o BUG J6PQ (ver ADR-05). 

### ADR-04 — Oráculo congelado por commit, não a reconstrução 🟢
**Evidência:** `_reversa_sdd/oracle/app_legacy_e43ca22.py`, `ORACLE_MANIFEST.md`, `migration/parity_harness.md`
**Decisão:** congelar `e43ca22` (monolito de 888 linhas, zero referências a `reconstructed/`) como referência de comportamento, em vez de usar `app.py` atual ou os 47 testes.
**Justificativa:** os testes existentes testavam a **reconstrução**, não o legado — usá-los como oráculo seria validação circular (`RISK-002`).
**Resultado medido:** paridade de 100% em 6/6 fixtures e 5/5 árvores reais (incluindo uma de 35.460 pessoas), e a descoberta de `DIV-001` (`get_name`) — a **única** divergência de comportamento real.
**Lição registrada no próprio manifesto:** *"a spec do legado não era oráculo; o código era"*.

### ADR-05 — Escape de rótulo Mermaid: lista branca, e o escape de entidades DEPOIS do filtro 🟢
**Commit:** `c709ea0` (2026-09-30) — corrige `BUG-20260929-J6PQ`
**Decisão:** substituir a lista **negra** por uma lista **branca**, e inverter a ordem para que a conversão de `&`/`<`/`>` em entidades HTML rode **depois** do filtro.
**Justificativa:** o gatilho confirmado em navegador é a sequência **aspa dupla seguida de crase** num nome vindo do GEDCOM — o lexer do Mermaid desvia para *markdown-string* e o fecha-colchete nunca vira o token que a gramática exige, derrubando o diagrama inteiro. A lista negra anterior era furada justamente pela crase.
**Evidência de correção:** 19 testes novos; fuzz independente não encontrou vazamento em 288 payloads combinados nem linha de nó inválida em 30.000 nomes.
**Consequência:** a ordem `filtro → entidades` é agora invariante do contrato — nenhuma entidade já escapada pode ser reintroduzida pelo filtro à frente.

### ADR-06 — Governança de edição do legado liberada por lista de caminhos permitidos 🟢
**Commits:** `80afe02` (2026-09-29) e `.reversa/reversa-config.json`
**Decisão:** permitir edição do legado **apenas** com `allowLegacyEdits: true` e globs explícitos (`analisador-genealogico/**`, `tests/**`, `README.md`, `pyrefly.toml`). Ausência de arquivo, JSON inválido ou tipo errado = falha segura (`false`).
**Justificativa:** o Reversa escreve por padrão apenas em suas próprias pastas; editar código de produção é ato explícito e auditável do usuário.
**Consequência:** cada escrita fora das pastas do Reversa fica registrada com hash no `.state.json` da migração.

### ADR-07 — Unificar a limpeza de nome numa única autoridade 🟢
**Commit:** `9318864` (2026-09-29) — `OPP-B5F2` opção B
**Decisão:** mover os dois corpos de limpeza de `dna_analysis` para `domain.py`, deixando uma só implementação.
**Justificativa:** havia **duas** implementações de limpeza de nome que divergiam em **5 de 9 casos**; a de `domain.py` não era consumida por nenhum caminho de produção.
**Consequência:** a autoridade agora é `domain.strip_bad_utf` / `domain.demojibake`, e `dna_analysis` importa de lá.

### ADR-08 — Não implementar `HARD_MIN`/`GIVEN_MIN` na reconstrução 🟢
**Evidência:** `migration/data_migration_plan.md`, `ORACLE_MANIFEST.md:119`, `reconstruction-plan.md:23`
**Decisão:** tratar as duas constantes como código morto e **não** as implementar; manter os limiares como literais dentro das regras de aceitação.
**Justificativa:** no monolito original elas eram declaradas e nunca referenciadas (`app_legacy_e43ca22.py:653-654`).
**⚠️ Efeito colateral documental:** as specs da extração anterior passaram a afirmar que elas estavam "declaradas mas não usadas" **na reconstrução** — o que é falso, porque ali nunca existiram. O adendo `003-refactor-code-quality` corrige o registro. Esta é a origem de `OBS-03` da feature 002 estar errado.

---

## 8. Decisões Humanas Vigentes

Quatro perguntas foram respondidas pelo usuário em 2026-08-03 e **continuam valendo** — o código atual as honra:

| # | Assunto | Resposta vigente | Conf. |
| --- | --- | --- | --- |
| 1 | Regras de aceitação do matching | **Definitivas** — preservar com fidelidade | 🟢 |
| 2 | Homônimos usam o 1º ID | **Aceitável** — comportamento já validado | 🟢 |
| 3 | Upload sem validação de extensão/tamanho | **Limitação aceita** para uso local | 🟢 |
| 4 | Relaxamento de Jaccard 0.5 → 0.33 com cM ≥ 150 | **Intencional** — mantém-se | 🟢 |

> Verificação no código atual: `questions.md#4` corresponde a `dna_analysis.py:299-301`; `#2` a `path_search.py:479`; `#3` a `app.py:29`; `#1` aos seis ramos de `dna_analysis.py:305-320`. Todas conferem. 🟢

---

## 9. Lacunas 🔴 (requerem validação humana)

| ID | Lacuna | Conf. |
| --- | --- | --- |
| ✅ L-01 | **RESOLVIDA em 2026-09-30:** `GenealogyGraph` e `DNAGroup` (e a dataclass `Family`) eram **arquitetura abandonada** — **removidas** por decisão do usuário (`questions.md#pergunta-3`). Não eram preparação para uso futuro. | 🟢 |
| L-07 | **Fonte das faixas de cM**: a tabela `SHARED_CM_DATA` não cita origem. O README menciona o Shared cM Project, mas não há referência à versão nem aos dados que geraram as faixas — e elas **se sobrepõem**, o que é atípico para uma tabela derivada de percentis. | 🔴 |
| L-08 | **Escopo do matching**: a cobertura dos 6 ramos de aceitação é conhecida apenas pelos testes de caracterização, que congelam o comportamento atual. Não há prova de que os ramos cobrem os casos reais de exportadores diferentes (o regex `[A-Z]{2}\d{7}` é específico). | 🟡 |
| L-09 | **Política de descarte**: match rejeitado é exibido em `skipped_matches` com motivo textual. Não há indicação de negócio sobre se o usuário deve agir sobre os descartados. | 🟡 |
| L-10 | **`README.md` do módulo desatualizado**: anuncia Pyvis como biblioteca de visualização, removida do projeto. Contradição documental interna. | 🟢 |

> Lacuna **fechada** nesta re-extração: "não há repositório Git → ADRs impossíveis". O repositório tem 66 commits e a §7 os documenta.

---

## 10. Resumo para o Reversa

- **Regras de negócio catalogadas:** 12 principais (faixas de cM com contrato de lista, conexão direta/indireta com tetos, 8 famílias de regras de matching, equivalentes de grafia, abreviações, conflito de nome do meio, desempate).
- **Máquinas de estado:** **nenhuma** entidade com múltiplos status → `state-machines.md` não gerado (autorizado para o nível `essencial`).
- **Permissões:** **inexistentes** → `permissions.md` não gerado. Registrada a consequência de negócio: sem isolamento entre usuários.
- **ADRs:** **8 decisões** reconstruídas do histórico Git nesta seção; `adrs/` não gerado por ser nível `essencial`.
- **Mensagens de contrato:** 21 literais catalogados (§4), dos quais 3 são provados por golden file.
- **Lacunas para validação:** 5 (L-01, L-07, L-08, L-09, L-10), sendo 2 🔴.

---

*Gerado pelo Reversa-Detective em 2026-09-30 (re-extração).*

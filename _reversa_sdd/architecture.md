# Arquitetura — analisador-genealogico

> Nível de documentação: **Completo** (`state.json` → `doc_level`, decidido em 2026-10-05)
> Re-extração de **2026-10-05**. Substitui o `architecture.md` de 2026-09-30, que descrevia a raiz `analisador-genealogico/`, o pacote `reconstructed/` (1.117 linhas) e **não conhecia** a regra final da análise nem as três dívidas que ela fechou.
> Snapshot da versão substituída: `.reversa/snapshots/2026-10-05-pre-reextracao/architecture.md`
> Escala de confiança: 🟢 CONFIRMADO | 🟡 INFERIDO | 🔴 LACUNA
> Detalhamento: `c4-context.md` (nível 1) · `c4-containers.md` (nível 2) · `c4-components.md` (nível 3) · `erd-complete.md` · `adrs/` (23 decisões) · `domain.md` · `state-machines.md` · `permissions.md`

---

## 1. Visão Geral da Arquitetura

Aplicação **web monolítica de um único processo**, com renderização **server-side** (Flask 3.1.3 + Jinja2) servida por **waitress 3.0.2**, **sem banco de dados**, **sem persistência de resultados** e **sem autenticação**.

O que define a arquitetura atual é a separação entre uma **camada de rota fina** e um **núcleo de domínio organizado por responsabilidade**:

| Camada | Onde | Linhas | Contrato |
| --- | --- | ---: | --- |
| **Rota** | `src/app.py` | 267 | Valida entrada HTTP, despacha por `action`, renderiza, aplica filtros e **sobe o servidor** com a guarda de instância única. **Zero regra de negócio de domínio.** 🟢 |
| **Núcleo** | `src/core/` + `parsers/` + `reporting/` + `utils/` | 3.489 (com o `app.py`) | Toda a decisão de domínio. **Não conhece HTTP.** 🟢 |
| **Apresentação** | `src/templates/index.html` | 525 | Única tela: upload, abas de busca e de análise, **quatro seções de resultado** e o confronto. Bootstrap 5.3.3 e Mermaid 10 por CDN. 🟢 |

> **Nota sobre a contagem da rota:** o `app.py` **cresceu** de 84 para 267 linhas, e isso **não** contradiz a decisão de rota fina (ADR-02). As linhas acrescentadas são **infraestrutura de entrada** — teto de corpo com handler de `413`, filtros de template, ancoragem do caminho de upload, guarda de instância única e bloco waitress. Nenhuma das **118 regras de negócio** catalogadas vive ali.

**O mecanismo de integração entre as camadas é estado global mutável**, e não injeção de dependência. `core/gedcom_state.py` mantém `people`, `families`, `graph` e `child_to_family`, e os demais módulos os importam. Duas assimetrias deliberadas, e ambas importam para quem reimplementar:

| Estrutura | Como é substituída | Consequência no código |
| --- | --- | --- |
| `people`, `families`, `child_to_family` | **Mutação *in place*** (`clear()` + `update()`) | Os bindings importados **no topo** continuam apontando para o objeto vivo |
| `graph` | **Reatribuição** | Quem o consome precisa importá-lo **dentro da função** (`path_finding.py:38`) — um import no topo ficaria preso ao grafo antigo |
| `versao` | Incremento a cada carga | Sinal de invalidação de índices derivados; existe porque `id()` **não** muda com mutação *in place* |

**O funcionamento é de análise sob demanda:** a cada `POST` de análise, o GEDCOM é **re-parseado integralmente** a partir da chave de conteúdo recebida no formulário, o grafo é reconstruído e só então o fluxo roda. Não há cache entre requisições. 🟢

---

## 2. Containers

**Três containers**, todos no mesmo host — detalhamento em `c4-containers.md`:

1. **Aplicação web** — o único processo (Python 3.14.6, Flask, waitress). Estado em memória.
2. **Navegador do usuário** — HTML/Jinja2 + Bootstrap + **Mermaid renderizado no cliente**. Deixou de ser cliente burro quando o diagrama foi movido para o cliente (ADR-03).
3. **Sistema de arquivos local** (`src/uploads/`) — o único estado persistente, com arquivos **imutáveis** sob chave de conteúdo.

**Não há** container de banco, fila, cache, worker assíncrono, serviço externo ou container de aplicação adicional. 🟢

**Concorrência:** o processo é **single-instance por construção** (socket exclusivo ligado antes de servir) e **multi-thread** (`ANALISADOR_THREADS = 4`). 🔴 **A exclusividade é de processo, não de thread** — e o estado do GEDCOM é global de processo. É a lacuna `L-16` (`domain.md` §7) e `M-03` (`state-machines.md` §7). 🟡

---

## 3. Componentes e estrutura de pacotes

**19 módulos** em quatro pacotes, mais a rota. Inventário completo em `c4-components.md`.

| Pacote | Módulos | Papel declarado |
| --- | ---: | --- |
| `core/` | 12 (+`__init__`) | Decisão de domínio, sem saber de HTTP |
| `parsers/` | 2 (+`__init__`) | Leitura do mundo de fora |
| `reporting/` | 1 (+`__init__`) | Emissão do diagrama e contrato de escape |
| `utils/` | 3 (+`__init__`) | Autoridades únicas transversais |

### 🔴 Os pacotes **não** formam camadas acíclicas

A intenção da reorganização (ADR-11) era uma pilha. O grafo real de importações tem **dois ciclos no nível de pacote**:

| Ciclo | Ida | Volta |
| --- | --- | --- |
| **`core/` ↔ `reporting/`** | `core/path_search.py:51`, `core/dna_analysis.py:51` → `reporting.mermaid_render` | `reporting/mermaid_render.py:16-23` → `core.family_navigation`, `core.path_finding`, `core.gedcom_state` |
| **`core/` ↔ `parsers/`** | `core/dna_analysis.py:50` → `parsers.csv_ingest` | `parsers/gedcom_parser.py:15-16` e `parsers/csv_ingest.py:41-42` → `core.gedcom_state`, `core.name_normalization`, `utils.text_cleaning` |

**Não há ciclo em nível de módulo** — o sistema importa e a suíte passa. As consequências são outras:

1. **`reporting/` não é folha, e não pode ser.** O renderizador navega o domínio para decidir *como desenhar* (`get_spouses`, `pick_spouse_for_couple`, `split_path_by_marriage`, `exclude_tail`, `find_ancestral_path`). Há **decisão de negócio dentro da apresentação** — o mesmo ponto que a análise de migração registrou ao tratar o Mermaid no cliente.
2. **`parsers/` não devolve valor: ele escreve o estado do domínio.** `gedcom_parser` substitui as quatro estruturas globais. É a origem do contador `versao` e do import dentro de função.
3. **`utils/` é o único pacote folha real** — nenhum de seus módulos importa outro módulo do projeto.

🔴 **Não há decisão humana registrada** sobre manter ou desfazer essa fronteira.

---

## 4. Modelo de Dados

**Sem banco de dados.** Não há DDL, migration, schema, ORM nem arquivo de configuração de persistência. O ERD completo (27 estruturas, com PK/FK lógicos e cardinalidades) está em `erd-complete.md`; os campos, tipos, padrões e sentinelas, em `data-dictionary.md`.

| Onde o dado vive | Estruturas | Persiste? |
| --- | ---: | --- |
| Memória do processo | 21 | Não — morre com o processo |
| Disco (`src/uploads/`) | 2 | **Sim**, e o arquivo é imutável (mesma chave não é reescrita) |
| Requisição / payload da tela | 4 | Não — uma requisição |

> ⚠️ **`None` significa "não sei / não existe", nunca zero.** É invariante do sistema e vale para `totals.cm` com múltiplos kits, `largest_segment_cm`, `plausible` e `age_birth`.
> ⚠️ **`PK`/`FK` do ERD são lógicos.** Não existe constraint: uma referência GEDCOM pendente é **aceita** e a aresta simplesmente não é criada. O alvo da migração quer o inverso.

---

## 5. O Fluxo que Define o Sistema

A decisão de arquitetura mais consequente **não** é estrutural, é de domínio: o fluxo de análise foi separado em **três eixos que não se contaminam** e um **confronto** que os compara sem alterá-los (ADR-14).

```text
Parentesco documental (GEDCOM)  ─┐
                                 ├─►  CONFRONTO  ─►  COMPATIVEL | POSSIVEL | CONFLITANTE | INCONCLUSIVO
Evidência genética (CSV)  ───────┤
   └─► Possibilidades (SCP 4.0) ─┘
```

- O **parentesco documental** nunca lê cM; a **evidência genética** não conhece o GEDCOM. 🟢
- O DNA **não** altera o parentesco documental: conflito vira **aviso e rol de causas**, nunca reescrita de vínculo. 🟢
- O cM **nunca** é usado sozinho para afirmar parentesco. 🟢

Detalhamento das regras em `domain.md` §2 e §3; as máquinas de decisão com diagramas, em `state-machines.md`. As **118 regras** catalogadas linha a linha estão em `code-analysis.md`; os fluxos por unidade, em `flowcharts/`.

---

## 6. Mapa de Integrações Externas

| Sistema externo | Tipo | Protocolo / formato | Uso | Conf. |
| --- | --- | --- | --- | --- |
| **Nenhuma API REST/GraphQL** consumida ou produzida | — | — | A aplicação é standalone | 🟢 |
| **Nenhum webhook, fila, evento ou mensageria** | — | — | Não há integração assíncrona | 🟢 |
| **GEDCOM (`.ged`)** | Arquivo | Formato GEDCOM, lido por `ged4py` 0.5.2 | Parsing da árvore; **re-parseado a cada requisição** | 🟢 |
| **CSV de matches de DNA** | Arquivo | CSV com colunas de Nome, cM, kit/ID/e-mail; `utf-8` com recuo para `latin-1` | Agregação de segmentos | 🟢 |
| **CDN de assets web** | Assets | HTTPS | Bootstrap 5.3.3 e Mermaid 10, carregados pelo navegador | 🟢 |
| **Exportadores de CSV** | Indireto | GEDmatch, MyHeritage, FamilyTreeDNA e similares | A detecção de coluna de ID depende do padrão `[A-Z]{2}\d{7}`; a leitura foi tornada tolerante a separador, preâmbulo e linha torta (ADR-16) | 🟡 |
| **Fonte estatística** | Dado embutido | Tabela publicada do **Shared cM Project 4.0** (março/2020, 59.714 envios) | 27 relações publicadas, em `relationship_hypotheses.py` | 🟢 |

**Zero integrações de rede.** O único tráfego de saída é o **download dos assets de CDN feito pelo navegador do próprio usuário**. 🟢

---

## 7. Dívidas Técnicas Consolidadas

Consolidação das 16 dívidas do `code-analysis.md` §6 com os achados desta fase (`L-15`, `L-16`, `L-19` e os ciclos de pacote). Ordenadas por **gravidade × probabilidade de morder quem reimplementar**.

| # | Dívida | Gravidade | Evidência | Referência |
| ---: | --- | --- | --- | --- |
| 1 | ✅ **FECHADA em 2026-10-05 — desempate determinístico.** Era "decisão humana não implementada"; o legado foi corrigido com um **quarto critério** (menor `xref_id`) e **2 testes** de regressão. **É a única divergência deliberada que muda comportamento** em toda a extração. | 🟢 Resolvida | `matching.py:107-111`; `tests/test_characterization_matching.py` | `adrs/23` |
| 2 | ✅ **FECHADA em 2026-10-05 — divergência de ambiente realinhada.** O `.venv/` é o interpretador **oficial**; o `requirements.txt` foi atualizado para as versões dele (`ged4py==0.5.5`, `networkx==3.7`, `pandas==3.0.6`) e passou a **declarar o `rapidfuzz` e o `python-Levenshtein`**, que decidem o matching. Verificado: a suíte passa **igual nos dois interpretadores**. | 🟢 Resolvida | `requirements.txt`; `.venv/` | `adrs/13` |
| 3 | **Contaminação entre requisições concorrentes.** Estado global reescrito por requisição + 4 threads; a guarda de instância única é de processo, não de thread. | 🔴 **Alta** | `app.py:126`, `:137`, `:188`; `core/gedcom_state.py` | `L-16`, `M-03` |
| 4 | **Ausência de identidade e de isolamento.** Sem `owner_id`, sem sessão, sem autorização; a chave de conteúdo é **identificador, não segredo**. Mantido por **aceite de risco** com condição de reabertura nomeada. | 🔴 **Alta** | `BUG-20260929-BJJH`; `permissions.md` §4 | `adrs/18` |
| 5 | **Ciclos de pacote `core/` ↔ `reporting/` e `core/` ↔ `parsers/`.** Sem ciclo de módulo, mas a fronteira entre decisão e apresentação não é acionável por importação. | 🟡 Média | `path_search.py:51`, `mermaid_render.py:16-23`, `csv_ingest.py:41-42` | `§3` desta página |
| 6 | **`get_children` varre todas as famílias, sem índice.** Diferente de `get_parents`, que usa `child_to_family`. | 🟡 Média | `documentary_relationship.py:112-124` | `L-20` |
| 7 | **Fichas completas por pessoa em cada resultado** (142 fichas nos 71 casos reais), para uma tela que exibe poucas. | 🟡 Média | `documentary_relationship.py:127-143` | `L-20` |
| 8 | **Nada é persistido entre requisições** e não há decisão de negócio sobre isso. | 🟡 Média | `app.py:137`; `L-21` | `E-04` |
| 9 | **Caminho indireto não passa pela checagem de plausibilidade de datas** (12–70 anos só no caminho direto). | 🟡 Média | `path_search.py:178-192` | `domain.md` §3.1 |
| 10 | **O CSV de DNA não tem validação de conteúdo** — só a forma do nome; é gravado antes de qualquer verificação. | 🟡 Média | `app.py:86` | `P-05` |
| 11 | **Endogamia e colapso de pedigree não são corrigidos**: o colapso é detectado no lado documental, mas **não altera o veredito**; o cM lido é teto otimista. | 🟡 Média | `evidence_comparison.py:55-68` | `L-17`, `adrs/21` |
| 12 | **Relações mais distantes não publicadas na SCP 4.0** — justamente onde o caso real cai. Mitigado por envoltória de meioses, sem substituir a fonte. | 🟡 Média | `relationship_hypotheses.py:96-103` | `L-18` |
| 13 | ✅ **FECHADA em 2026-10-05 — cobertura medida: 83 %** de `src/` (1.520 instruções, 253 descobertas). Os piores índices dão nome ao risco: `number_format` 53 %, `relationship_hypotheses` 76 %, `mermaid_render` 78 % | 🟢 Resolvida | `pytest-cov` no `.venv` | `X-03` |
| 14 | **Teto de 20 iterações do BFS corta em silêncio.** Contrato **aceito** por decisão humana, com aviso de que não prova ausência de parentesco. | 🟡 Média (aceita) | `path_finding.py:25` | `adrs/` — decisão 1 de 2026-09-30 |
| 15 | **`get_spouses` esconde cônjuges** quando o primeiro `FAMS` resolve. Contrato **aceito** e documentado. | 🟡 Média (aceita) | `family_navigation.py:66-75` | `adrs/` — decisão 2 de 2026-09-30 |
| 16 | ✅ **FECHADA em 2026-10-05 — `app.secret_key` removido.** Não havia consumidor (`flask.session` nunca importado); o literal versionado deixou de existir. | 🟢 Resolvida | `app.py:22` (comentário da remoção) | `permissions.md` (`P-04`) |
| 17 | **Superfícies de compatibilidade** reexportando nomes históricos que ninguém usa (`path_search.__all__`, `dna_analysis.__all__`). Dívida de teste, não de produção. | 🟢 Baixa | `path_search.py:61-64` | `c4-components.md` §7 |
| 18 | **`cm_estimator` segue no repositório como legado fora do fluxo**, com faixas sem fonte verificável. Declarado e reexportado. | 🟢 Baixa | `cm_estimator.py:1`, `:21` | `adrs/19` |
| 19 | **Duplicatas literais:** `COMMON_SURNAMES` tem `souza` duas vezes; o mapa de mojibake tem chave duplicada e um mapeamento identidade. | 🟢 Baixa | `name_normalization.py:36`; `text_cleaning.py:41-50` | `code-analysis.md` §2.7, §3.7 |
| 20 | **`LIMITE_SEGMENTO_FRACO` (15 cM) é heurística do projeto** apresentada ao lado de números publicados; a verificação de que a tela a apresenta como tal é da interface. | 🟢 Baixa | `genetic_evidence.py:31` | `adrs/19` |

### Dívidas **fechadas** desde a extração anterior

| Dívida de 2026-09-30 | Como foi fechada |
| --- | --- |
| "Código monolítico com rotas + lógica acopladas" | ✅ `app.py` é camada de rota fina; a lógica vive em quatro pacotes (ADR-02, ADR-11) |
| "Ausência total de testes" | ✅ 11 arquivos, 126 funções, 175 itens, incluindo caracterização, segurança de upload e a regra do confronto |
| "Correções de mojibake heurísticas e fragmentadas" | ✅ autoridade única em `utils/text_cleaning.py` (ADR-07) |
| "Dependências sem versão fixada" | ✅ seis diretas pinadas (ADR-13) — **ressalva da dívida #2 desta tabela** |
| "Upload sem validação de extensão, tipo ou tamanho" | ✅ teto de 16 MB, validação de conteúdo e chave derivada do conteúdo (ADR-17) |
| "Entidades declaradas que o fluxo não usa" | ✅ removidas (ADR-09) |
| "`README.md` do módulo anuncia Pyvis" | ✅ o README herdado foi removido; o README da raiz está em dia |
| "Ausência de CI/CD" | ⚠️ **parcialmente**: existe deploy do mini-site no GitHub Pages, **não** há pipeline de teste, build ou análise estática |

---

## 8. Decisões Arquiteturais

**23 decisões** documentadas em `adrs/`, reconstruídas de **125 commits** e dos registros de bug e de mitigação:

| Faixa | Assunto |
| --- | --- |
| `01`–`08` | Fundação: reconstrução em módulos, rota fina, Mermaid no cliente, oráculo congelado, escape do rótulo, política de edição do legado, autoridade de limpeza, `HARD_MIN`/`GIVEN_MIN` |
| `09`–`13` | Estrutura: remoção das entidades decorativas, `/src`, pacotes por responsabilidade, waitress + instância única, pinagem de dependências |
| `14`–`17` | Domínio: **separação dos três eixos**, sobreposição de faixas, leitura tolerante do CSV, upload por chave de conteúdo |
| `18`–`23` | Operação e contrato: single-tenant por aceite de risco, heurísticas declaradas, formatação só na apresentação, endogamia, ordem de apresentação, **desempate determinístico (decidido e NÃO implementado)** |

---

## 9. Resumo para o Reversa

- **Containers:** **3** — aplicação web (único processo), navegador do usuário (renderiza Mermaid) e sistema de arquivos local. Sem banco, fila, cache ou API. 🟢
- **Camadas:** 2 com contratos opostos — rota de **267 linhas** (zero regra de negócio) e núcleo de **3.489 linhas**, integrados por **estado global mutável**. 🔴 **Os quatro pacotes do núcleo não formam camadas acíclicas** (dois ciclos de pacote). 🟢
- **Componentes:** **19 módulos**; `utils/` é o único pacote folha real; `reporting/` contém decisão de negócio de apresentação. 🟢
- **Integrações externas:** **zero** de rede. Entrada por arquivo (`.ged`, `.csv`), assets por CDN no navegador e uma tabela estatística publicada embutida. 🟢
- **Modelo de dados:** **27 estruturas**, **nenhuma tabela**. Sem constraint, sem `owner_id`, sem histórico. Persistência apenas de arquivos imutáveis. 🟢
- **Regra central:** os **três eixos que não se contaminam** + confronto em quatro estados — capacidade que **não existe em nenhum artefato da extração anterior**. 🟢
- **Dívidas técnicas:** **20 consolidadas**, sendo **4 de gravidade alta** — e **três delas são achados desta rodada** (determinismo não implementado, divergência de ambiente, corrida entre threads). 🟢
- **Decisões:** **23 ADRs**; **13 decisões humanas verificadas**, das quais **1 não está honrada** pelo código. 🟢
- **Instrumentação de desenvolvimento (fora do runtime):** oráculo congelado (`oracle/`), harness diferencial com **paridade 100%** em 6 fixtures e 5 árvores reais (`parity/`), 7 goldens de tela (`screens/`), a suíte de migração (`migration/`) e os 23 ADRs. O repositório também hospeda o sub-projeto Node `plugins/dsh-markdownlint/` e a pasta `docs/` publicada no GitHub Pages (cópia do mini-site). **Nada disso faz parte do sistema em execução.** 🟢

---

*Gerado pelo Reversa-Architect em 2026-10-05 (re-extração, nível completo).*

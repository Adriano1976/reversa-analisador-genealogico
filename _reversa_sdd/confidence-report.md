# Relatório de Confiança — teste_reversa

> Gerado pelo **Reversa-Reviewer** na re-extração de **2026-10-10** (nível **Completo**). Substitui integralmente o relatório de 2026-10-05.
> **Atualizado em 2026-10-10** após o processamento de **18 de 18 perguntas** de `questions.md` — todas respondidas com a recomendação do Revisor.
> Revisão cruzada por engine externa: **não realizada** — nenhuma ferramenta com prefixo `codex:` está ativa nesta sessão, conforme o Passo 0 do agente. Não foi oferecida ao usuário.
> Este relatório cobre: **5 units** (20 canônicos, incluindo os 5 `contracts.md`), **25 artefatos transversais com marcadores** (mais o `openapi/index.yaml`, que não usa marcadores) e **36 ADRs**.
> Método de contagem: ocorrência dos marcadores 🟢/🟡/🔴 por arquivo, **excluindo as linhas de legenda** (aquelas que citam os três nomes ao mesmo tempo). É a mesma convenção das rodadas anteriores, para que os números sejam comparáveis.

---

## Resumo Geral

| Escopo | 🟢 | 🟡 | 🔴 | Total | Confiança |
| --- | ---: | ---: | ---: | ---: | ---: |
| **5 units** (requirements + design + tasks + contracts) | 1.746 | 108 | 69 | 1.923 | **93,6 %** |
| **Artefatos transversais** (25) | 1.098 | 136 | 99 | 1.333 | **87,5 %** |
| **ADRs** (36) | 113 | 26 | 25 | 164 | 76,8 % |
| **Extração completa** | **2.957** | **270** | **193** | **3.420** | **90,4 %** |

**Confiança geral: 90,4 %** — `(2.957 + 270×0,5) / 3.420`

> **Comparação com a re-extração anterior:** 2026-10-05 fechou com **1.922** marcadores e **92,8 %**. Hoje são **3.420** — **1,8× mais** — com **90,4 %**. A queda de 2,4 pontos é **esperada e saudável**: o escopo cresceu em tudo o que o nível `completo` exige sobre um sistema que dobrou de tamanho (3 → **5 units**, 23 → **36 ADRs**, 3 → **5 flowcharts**, 3 → **5 user-stories**), e as **duas units novas** (`tela-de-entrada` e `recursos-da-tela`) entraram nesta rodada já **com** as suas lacunas abertas — que é o comportamento correto de uma extração que não inventa confirmação.
>
> **Os ADRs continuam com a menor confiança do conjunto (76,8 %), e isso é esperado:** eles são reconstrução de decisão a partir de commit, código e registro de bug — não leitura de comportamento. Onde não há prosa de decisão, a ADR **declara a ausência** em vez de preencher.
>
> **O que mudou de qualidade, e não de número:** a revisão **mediu quatro coisas** que a rodada anterior tinha declarado sem medir (o `L-24`, o `L-31`, o `L-20` e a cobertura) e **corrigiu dez defeitos de consistência** entre artefatos — incluindo um global que **não era YAML válido**.

---

## Por Spec

### Units

| Spec | 🟢 | 🟡 | 🔴 | Total | Confiança |
| --- | ---: | ---: | ---: | ---: | ---: |
| `tela-de-entrada/` | 251 | 11 | 6 | 268 | **95,7 %** |
| `recursos-da-tela/` | 303 | 15 | 11 | 329 | **94,4 %** |
| `upload-gedcom/` | 257 | 13 | 10 | 280 | **94,1 %** |
| `analise-dna/` | 507 | 33 | 18 | 558 | **93,8 %** |
| `busca-caminho/` | 428 | 36 | 24 | 488 | **91,4 %** |

> **A unit com mais 🔴 é `busca-caminho` (24), e a razão é específica:** ela concentra o `L-24` (confirmado por execução nesta rodada), o `L-25` (determinismo) e o `L-20` (custo medido) — os três achados que a revisão **mediu** e cujas correções estão **agendadas**. As duas units **novas** ficaram acima de 94 %: elas nasceram de features recentes, com teste ao lado, e a revisão não encontrou nelas nenhuma contradição com o código.
>
> **`analise-dna` continua sendo a maior unit** (558 marcadores, 95 regras `BR-D-*`) e subiu de 95,7 % para 93,8 % **em número absoluto de confiança** — porque ganhou a fronteira de aplicação, a persistência opcional e a projeção pura, e com elas as lacunas `L-28` e `L-29`.

### Artefatos transversais

| Artefato | 🟢 | 🟡 | 🔴 | Total | Confiança |
| --- | ---: | ---: | ---: | ---: | ---: |
| `c4-components.md` | 45 | 2 | 0 | 47 | **97,9 %** |
| `user-stories/recursos-da-tela.md` | 19 | 0 | 3 | 22 | 86,4 % |
| `user-stories/upload-gedcom.md` | 26 | 0 | 4 | 30 | 86,7 % |
| `inventory.md` | 45 | 3 | 1 | 49 | 94,9 % |
| `flowcharts/recursos-da-tela.md` | 52 | 3 | 1 | 56 | **95,5 %** |
| `flowcharts/analise-dna.md` | 122 | 8 | 3 | 133 | 94,7 % |
| `flowcharts/busca-caminho.md` | 94 | 12 | 1 | 107 | 93,5 % |
| `flowcharts/tela-de-entrada.md` | 3 | 1 | 1 | 5 | 70,0 % |
| `flowcharts/upload-gedcom.md` | 2 | 1 | 3 | 6 | 41,7 % |
| `domain.md` | 156 | 9 | 5 | 170 | 94,4 % |
| `code-spec-matrix.md` | 73 | 5 | 3 | 81 | 93,2 % |
| `erd-complete.md` | 85 | 2 | 6 | 93 | 92,5 % |
| `data-dictionary.md` | 39 | 3 | 2 | 44 | 92,0 % |
| `c4-containers.md` | 26 | 3 | 1 | 30 | 91,7 % |
| `state-machines.md` | 59 | 7 | 4 | 70 | 89,3 % |
| `permissions.md` | 36 | 4 | 3 | 43 | 88,4 % |
| `c4-context.md` | 14 | 2 | 1 | 17 | 88,2 % |
| `dependencies.md` | 27 | 6 | 4 | 37 | 81,1 % |
| `code-analysis.md` | 75 | 19 | 11 | 105 | 80,5 % |
| `user-stories/tela-de-entrada.md` | 13 | 0 | 4 | 17 | 76,5 % |
| `user-stories/busca-caminho.md` | 7 | 3 | 2 | 12 | 70,8 % |
| `architecture.md` | 41 | 38 | 12 | 91 | 65,9 % |
| `traceability/spec-impact-matrix.md` | 30 | 3 | 17 | 50 | 63,0 % |
| `user-stories/analise-dna.md` | 9 | 2 | 7 | 18 | 55,6 % |
| `openapi/index.yaml` | — | — | — | — | *sem marcadores* |

> **Os artefatos com menor confiança são os que existem para expor risco**, e não para descrever comportamento: `spec-impact-matrix.md` (63,0 %) concentra as lacunas de **ordem determinística**, de **constantes embutidas em mensagens** e de **cobertura desigual**; `architecture.md` (65,9 %) consolida as **28 dívidas técnicas**. Confiança baixa ali significa que o documento está fazendo o trabalho dele.
>
> **Os dois `flowcharts` com menos de 6 marcadores** (`upload-gedcom.md`, 6; `tela-de-entrada.md`, 5) **não são artefatos rasos**: eles usam diagrama Mermaid como corpo e reservam o marcador para as decisões não triviais. O número baixo é **forma**, não cobertura — e é uma limitação honesta deste método de contagem.
>
> **`openapi/index.yaml` não usa marcadores** — é contrato. **Foi validado por parser YAML real** (`js-yaml`, que existe no repositório dentro de `plugins/dsh-markdownlint/node_modules/`): `openapi 3.0.3`, `version 2.0.0`, **3 rotas** (`/`, `/apple-touch-icon.png`, `/banner.png`), **9 schemas**, e o `pattern` de `ReferenciaDeArquivo` **compila como regex**. ⚠️ **Na primeira validação o arquivo estava INVÁLIDO** — ver §4.

---

## Verificações de Consistência Executadas

| # | Verificação | Método | Resultado |
| ---: | --- | --- | --- |
| 1 | Os 3 canônicos + opcionais existem em cada unit | varredura do sistema de arquivos | ✅ **20 canônicos + 5 `contracts.md`** presentes; nenhuma unit incompleta |
| 2 | Units geradas == `surface.json.modules` | comparação de conjuntos | ✅ **5/5** — `upload-gedcom`, `tela-de-entrada`, `analise-dna`, `busca-caminho`, `recursos-da-tela`; nada faltando nem sobrando |
| 3 | A matriz de código cobre o `src/` real | confronto com a árvore do sistema de arquivos | ✅ **38 linhas** para **35 `.py`** + `index.html` + 2 artes; contagem de `.py` bate exatamente |
| 4 | Globais do nível `completo` presentes | verificação de existência | ✅ `openapi/index.yaml`, **5** `user-stories/`, `code-spec-matrix.md`, `spec-impact-matrix.md`, `gaps.md` |
| 5 | Constantes de contrato coerentes entre units | **importação e medição**, não leitura | ✅ 13 medidas: `CAUSAS_POSSIVEIS`=12, `CAUSAS_POSSIVEL`=**8**, `SCP40_ROWS`=27, `SCP40_NOT_PUBLISHED`=6, `SEM_KIT`=`' SEM-KIT'`, `LIMITE_SEGMENTO_FRACO`=15.0, `GENERIC_GIVENS`=20, `SURNAME_SUFFIXES`=5, `STOP_WORDS`=6, `LIMITE_DE_PREAMBULO`=10, `COMMON_SURNAMES`=16 literais/15 efetivas, `TAMANHO_ESPERADO`=16504, `_chave_de`=`(len, 1ª, última)` |
| 6 | Contagem de RFs confere com o publicado | contagem de linhas de tabela `\| RF-nn \|` | ✅ **24 / 24 / 34 / 43 / 25 = 150** nas 5 units |
| 7 | Dependências declaradas batem com as reais | confronto de `modules.json` com os `design.md` | ❌ **NÃO batiam em duas units** — `analise-dna` e `busca-caminho` omitiam `tela-de-entrada`, de que ambos dependem (`_arvore_do_formulario` + lista de escolha do CSV). **Corrigido em `modules.json`** |
| 8 | Contagem de `render_template` e de `gedcom_filename` | contagem por linha em `src/app.py` | ❌ **"oito" era falso em 4 artefatos.** Medido: **23** `render_template`, **12** com `gedcom_filename`. **Corrigido** |
| 9 | `person_summary` tem os campos que a spec declara | leitura do fonte | ❌ **12 era falso.** São **13** (`id`, `name`, `sex`, `birth`, `birth_year`, `birth_place`, `death`, `death_year`, `parents`, `parent_names`, `spouses`, `children`, `family_as_child`). **Corrigido em 5 arquivos** |
| 10 | O número de nomes vazios do `get_name` | **execução** do parser sobre as **três** cópias reais da árvore | ❌ **296 era falso — e era outra grandeza.** Medido: **301** em 35.460, `"Sem Nome"` = **0**. O 296 é a contagem de pessoas **divergentes do `DIV-001`** medida pelo harness de paridade em 2026-09-28. **Corrigido, com a proveniência registrada** |
| 11 | O `openapi/index.yaml` é YAML válido | **parser real** (`js-yaml`) | ❌ **NÃO era.** Erro na linha 414: escalar não citado começando com `*` (que em YAML inicia um alias) derrubava as 426 linhas. **Corrigido e revalidado** |
| 12 | Referências a `adrs/NN` resolvem | extração das referências e teste de existência | ✅ todas entre os **36 arquivos existentes** |
| 13 | Afirmações 🟡 reclassificáveis por medição | execução de 4 experimentos | ✅ **4 medições**: `L-24` (confirmado), `L-31` (negativo), `L-20` (custo), cobertura (**89 %**) |

---

## Histórico de Reclassificações

### Defeitos de consistência corrigidos nesta rodada (10, em 11 arquivos)

| # | O que dizia | O que é | Onde | Como foi decidido |
| ---: | --- | --- | --- | --- |
| 1 | `openapi/index.yaml` válido | **YAML inválido** — 1 escalar com `*` inicial derrubava 426 linhas | `openapi/index.yaml:414` | **parser real** (`js-yaml`) |
| 2 | `CAUSAS_POSSIVEL` = 9 | **8** (`[0]+[3:8]+[10:]` = 1+5+2) | `code-analysis.md` `BR-D-35` · `modules.json` · `spec-impact-matrix.md` Matriz D | importação |
| 3 | `person_summary` = 12 campos | **13** | `code-analysis.md` `BR-C-45` · `modules.json` · 4 arquivos de `busca-caminho` | leitura do fonte |
| 4 | "a rota tem **oito** `render_template`" | **23** (12 com `gedcom_filename`) | `code-analysis.md` `BR-T-17` · `modules.json` · `domain.md` · `flowcharts/tela-de-entrada.md` · `upload-gedcom/tasks.md` | contagem por linha |
| 5 | `uploads` com "33 entradas" | **13 arquivos** + 4 aposentados | `recursos-da-tela/{requirements,contracts}.md` · `flowcharts/recursos-da-tela.md` | contagem do diretório |
| 6 | "296 pessoas em 35.460" | **301** — e o 296 é outra grandeza | `upload-gedcom/requirements.md` · `data-dictionary.md` | execução do parser nas 3 cópias |
| 7 | `tela-de-entrada` com "126 testes em 7 arquivos" | **132 em 8** — faltava `test_gedcom_ilegivel_nao_derruba.py` | `tela-de-entrada/{requirements,design,contracts}.md` | o próprio `tasks.md` (`TT-12`) e a `code-spec-matrix.md` o citavam |
| 8 | O índice "não é invalidado por `id()`, **nem por tamanho**" | A chave **usa** a contagem: `(len(people), 1ª, última)` | `busca-caminho/design.md` | leitura de `_chave_de` |
| 9 | `analise-dna` e `busca-caminho` dependem de 2 units | **3** — falta `tela-de-entrada` | `modules.json` | os próprios `design.md` a listam |
| 10 | `adrs/21`: "subconjunto de 9" | **8** | `adrs/21` | importação |

### Reclassificações por medição (4)

| De | Para | Afirmação | Evidência |
| --- | --- | --- | --- |
| 🔴 | 🟢 | **`L-24`: "a colisão do cache de nomes é possível"** | **Confirmada por experimento.** Duas árvores de 4 pessoas com a mesma chave `(4,'@I1@','@I9@')` e xrefs interiores diferentes: o dossiê da **segunda** respondeu `exact_count: 1` citando **`@I2@`, que não existe nela**, e `person_summary` degradou para `"Sem Nome"` **sem levantar nada**. O gatilho medido é a **contagem**, não o conteúdo |
| 🟡 | 🟢 | **`L-31`: "a disponibilidade do grupo é a do representante"** | **Medição negativa:** 13 grupos na pasta real, **nenhum** com mais de um membro → a divergência **não pode ocorrer**. Decisão: manter |
| 🔴 | 🟡 | **`L-20`: "custo real, sem limite medido"** | **Medido:** 15,4 ms/ficha → 142 fichas ≈ **2,2 s**, contra **20,9 s** de parse e **1,73 s** de dossiê. O gargalo é o parse. Decisão: **não** otimizar |
| 🟡 | 🟢 | **`X-03`: "a medição não foi refeita"** | **Remedida: `src/` = 89 %** (era 83 %). A pior cobertura trocou de dono: `ports/adaptadores.py` **73 %** — exatamente o módulo do `L-28` |

### Fechadas por construção (2)

| ID | Como |
| --- | --- |
| **`L-16` / `M-03` / `P-02`** | **A corrida entre requisições concorrentes deixou de existir** (`ADR-24`): a árvore é valor de retorno e entra por parâmetro; `gedcom_state.py` não existe mais. **Era a única lacuna crítica das duas rodadas anteriores.** Provado por `test_arvore_devolvida.py` e `test_dependencias_nucleo.py` |
| **`CS-06`** | **Bytecode órfão removido** (decisão humana). Reverificado: nenhum dos 35 `.pyc` de `src/` ficou sem `.py` |

### Decisões humanas aplicadas nesta rodada (18)

Ver `questions.md` e `gaps.md` §5. **Quinze** foram registradas como decisão em spec; **uma** foi executada nesta rodada (a remoção do bytecode); **cinco** viraram mudança de código **agendada para depois do Passo 4** — `L-24` (chave do cache), `L-25` (4º critério), `L-30` (docstring), `L-33` (health check) e o log das tentativas de aposentar. O motivo do agendamento é a decisão registrada pelo próprio projeto: *não mexer no código antes do Passo 4, para não verificar regressão com o código mudando ao mesmo tempo*.

**Nenhuma mudança de comportamento foi feita nesta revisão.** O único arquivo do legado tocado foi um `.pyc` órfão.

---

## Verificação por execução

| Verificação | Comando | Resultado |
| --- | --- | --- |
| Suíte completa | `.venv/Scripts/python.exe -m pytest -q` (com `DATABASE_URL` limpa) | ✅ **527 passam · 9 pulados · 0 falham** |
| Cobertura de `src/` | `-m pytest --cov=src` no `.venv` | ✅ **89 %** (2.081 instruções, 228 não cobertas) |
| Parser do `openapi` | `node` + `js-yaml` do repositório | ✅ **válido** — 3 rotas, 9 schemas, regex compila |
| `markdown_lint` | todos os `_reversa_sdd/**` e `.reversa/**` | ✅ **exit 0 / nenhum problema** |
| `state.json` | `json.load` | ✅ **válido** |
| `modules.json` | `json.load` | ✅ **válido** — 233 regras em 5 módulos |

> ⚠️ **A suíte exige `DATABASE_URL` limpa.** Com a variável definida no ambiente e **sem** o `psycopg2` instalado, 2 testes de `test_persistencia_desabilitada.py` falham — não é regressão: é o teste medindo um estado que o ambiente não pode produzir. Registrado aqui porque é uma armadilha real para quem rodar a suíte numa shell que exporte a variável.

---

## Lacunas Pendentes 🔴

**A contagem consolidada está em `gaps.md` §8**, que é a fonte da verdade.

| Severidade | Itens |
| --- | ---: |
| 🔴 Crítico | **0** |
| 🟠 Moderado | 12 |
| ⚪ Cosmético | 10 |
| **Total em aberto** | **22** |

**Nenhuma lacuna crítica restou.** A única das duas rodadas anteriores — a corrida entre threads — foi **eliminada estruturalmente** pelo `ADR-24`, não mitigada.

**Fechadas nesta rodada: 21** — 4 por medição/experimento (`L-24`, `L-31`, `L-20`, cobertura), 2 por construção (`L-16`, `CS-06`), 1 por releitura de matriz (`X-01`), e 14 registradas como decisão com efeito em spec.

> **Três das 22 em aberto são limitação da fonte e não são resolvíveis por decisão humana:** as 6 relações não publicadas na versão 4.0 (`L-18`), a endogamia que não é detectada (`L-17`, resíduo) e a ordem de inserção das arestas do grafo (`E-01`/`X-04`), que é semântica do `networkx` e contrato de paridade com o oráculo.
>
> **O que sobra depois disso é trabalho de engenharia declarado e com dono:** cobertura (`L-28`, 73 % no módulo do INSERT), custo (`L-20`, medido e não prioritário), rastreabilidade (`X-02`/`CS-03`) e as cinco correções agendadas.

---

## Recomendações

- [ ] **Executar as 5 correções agendadas, na ordem:** (1) `L-24` — acrescentar à chave do cache algo derivado do conteúdo, com o `TT-20` que já existe; (2) `L-25` — quarto critério determinístico em `common_ancestors`, com teste nas duas ordens de *pool*; (3) `L-30` — corrigir a docstring de `motivo_de_indisponibilidade`; (4) `L-33` — health check das duas artes no arranque; (5) log das duas tentativas de aposentar. **Todas depois do Passo 4.** Nenhuma muda comportamento observável, exceto a do `L-24` (que corrige um defeito silencioso) e a do `L-25` (que torna determinístico o que hoje depende do `PYTHONHASHSEED`).
- [ ] **Levar os 6 requisitos encaminhados ao alvo para o próximo ciclo forward** (`_reversa_forward/`): persistir histórico (1, já parcialmente atendido no legado), registrar o veredito do operador (2), restringir a lista de nomes (3), validar o CSV (4), **retenção/expurgo/consentimento (5 — novo)** e a política de deduplicação do histórico (6 — novo). **Enquanto o nº 5 não existir, o uso do legado com dado de terceiros está declarado PROIBIDO.**
- [ ] **Observar a `L-31` sem instrumento não é suficiente.** A medição deu negativo *hoje*; o gatilho (mesmo conteúdo reenviado com outro nome) é observável. Um teste que **falhe quando um grupo passar a ter dois membros** é a forma barata de não depender de ninguém lembrar disto.
- [ ] **Regenerar `_reversa_docs/` e as matrizes de `_reversa_bugs/*/generated/`** — ambas derivam de artefatos de 2026-09-30/10-05, e o `_reversa_docs` é de 2026-10-08. O gerador **não lê** `_reversa_sdd/addenda/`.
- [ ] **Atualizar o `README.md`, que continua contradizendo o pin** (documenta o interpretador **global**; o oficial é o `.venv/`). Uma linha resolve — **não editei por ser documento seu**.
- [ ] **Conferir o estado do repositório antes de commitar.** Esta revisão tocou **apenas arquivos do Reversa**: `.reversa/context/modules.json`, `.reversa/state.json`, `.reversa/plan.md` e 15 arquivos de `_reversa_sdd/`. Do legado, **um** arquivo foi tocado: o `.pyc` órfão, removido por decisão sua. Os artefatos substituídos estão em `.reversa/snapshots/2026-10-10-pre-reextracao/`.

---

## Revisão Cruzada

**Não realizada** — nenhuma ferramenta com prefixo `codex:` está ativa nesta sessão. O Passo 0 do agente determina, nesse caso, pular o passo sem mencioná-lo ao usuário; o registro fica aqui, como nas rodadas anteriores, para que a ausência seja auditável.

---

*Gerado pelo Reversa-Reviewer em 2026-10-10 (re-extração, nível completo). Atualizado após as 18 respostas.*

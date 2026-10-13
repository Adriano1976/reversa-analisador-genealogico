# Lacunas Remanescentes — teste_reversa

> Gerado pelo **Reversa-Reviewer** na re-extração de **2026-10-10** (nível **Completo**). Substitui integralmente o `gaps.md` de 2026-10-05.
> **Atualizado em 2026-10-10** após o processamento das **18 perguntas** de `questions.md` — todas respondidas com a recomendação do Revisor.
> Este arquivo é o **passivo** da extração: o que ficou sem resposta depois da revisão. Ele complementa `questions.md` (as perguntas) e `confidence-report.md` (os números).
> Escala de confiança: 🟢 CONFIRMADO | 🟡 INFERIDO | 🔴 LACUNA

---

## 1. Como este arquivo se organiza

| Severidade | Critério | Efeito de ignorar |
| --- | --- | --- |
| 🔴 **Crítico** | Bloqueia a reimplementação **fiel**, ou pode produzir resultado **errado em silêncio** | Quem reimplementar erra sem saber |
| 🟠 **Moderado** | Afeta qualidade, custo ou decisão de produto | A reimplementação funciona, mas herda um problema |
| ⚪ **Cosmético** | Precisão documental ou armadilha de leitura | Custa tempo de quem lê, não corretude |

> ⚠️ **Nada do legado foi alterado nesta rodada de revisão**, com **uma** exceção de higiene: o bytecode órfão `gedcom_state.cpython-314.pyc` foi removido (decisão humana, pergunta 4). As seis mudanças de código que as respostas 1 a 3 e 12 a 14 autorizam estão **agendadas para depois do Passo 4** — ver §5 —, para que a verificação de regressão semântica não seja feita com o código mudando ao mesmo tempo.

---

## 2. Lacunas críticas 🔴

| ID | Lacuna | Onde está documentada |
| --- | --- | --- |
| — | **NENHUMA.** | — |

> **A única lacuna crítica das duas rodadas anteriores está FECHADA, e por construção.** O `L-16` / `M-03` / `P-02` — corrida entre requisições concorrentes sobre o estado do GEDCOM — **deixou de existir em 2026-10-07** quando o `ADR-24` eliminou o estado global de árvore: a árvore virou o **valor de retorno** do parse e entra por **parâmetro** em todo o núcleo. O `gedcom_state.py` **não existe mais** (restava apenas o bytecode, removido nesta rodada).
>
> A verificação não é por leitura: `tests/test_arvore_devolvida.py` prova que **duas cargas consecutivas no mesmo processo produzem árvores independentes**, e `tests/test_dependencias_nucleo.py` prova as dependências entre pacotes. O que **permanece** é a corrida sobre o **disco** (`guardar` e `aposentar` verificam e depois agem — dívidas #3/#4), que é de natureza diferente: ela é de **sistema de arquivos**, não de memória compartilhada, e nunca foi medida.
>
> **Consequência para quem lê isto:** o projeto passou a não ter lacuna crítica de reimplementação. Isso **não** significa que não haja risco — significa que os riscos que restam são de custo, de cobertura e de limitação da fonte, e não de comportamento errado em silêncio.

---

## 3. Lacunas moderadas 🟠

### 3.1 A confirmada por execução, com correção agendada

| ID | Lacuna | Onde | Situação |
| --- | --- | --- | --- |
| `L-24` / `E-05` | **Colisão da chave do cache de nomes.** `_chave_de` = `(len(people), chaves[0], chaves[-1])`: duas árvores do **mesmo tamanho** com os **mesmos xrefs extremos** compartilham o índice, e o dossiê de homônimos da segunda cita xrefs **que não existem nela**, degradando em silêncio para `"Sem Nome"`. | `busca-caminho/design.md` § Riscos · `analise-dna/design.md` § Riscos · `flowcharts/busca-caminho.md` §13 | ✅ **confirmada por execução** em 2026-10-10 (era **inferida**). O gatilho medido **não depende do conteúdo, depende só da contagem**: as duas árvores reais pequenas da pasta do operador já compartilham os dois extremos (`@I1000@` e `@I9@`) e diferem **apenas** no tamanho. Correção **aceita**, agendada para depois do Passo 4 (§5). |

### 3.2 Limitação da fonte, não decisão do projeto

| ID | Lacuna | Onde | Por que segue aberta |
| --- | --- | --- | --- |
| `L-18` | As relações **mais distantes** não são publicadas na versão 4.0 da fonte — justamente onde o caso real deste repositório cai (6 de 27). | `analise-dna/requirements.md` (`BR-D-25`) · `contracts.md` §4.1 | **Não é resolvível por decisão humana.** A envoltória por meioses mitiga, e inventar números foi descartado. |
| `L-17` (resíduo) | **Endogamia** não é nem **detectada** (o colapso de pedigree é), e nenhum dos dois altera o veredito: o cM lido é **teto otimista** nesses casos. | `adrs/21` · `analise-dna/design.md` | A decisão "avisar basta" é de 2026-10-05 e **continua vigente**. O que a rodada nova acrescenta é a distinção: o colapso **é** detectado, a endogamia **não**. Decidir "detectar endogamia também" é decisão nova — e não foi pedida. |

### 3.3 Ordem, rastreabilidade e cobertura

| ID | Lacuna | Onde | Situação |
| --- | --- | --- | --- |
| `E-01` | **Ordem é dado, não consequência.** Três ordens determinam resultado: inserção das arestas do grafo, ordem dos candidatos de nome e ordem de apresentação. | `erd-complete.md` §8 | 🟡 **Duas das três fechadas:** o desempate de nomes é determinístico desde 2026-10-05 (menor `xref_id`) e a ordem de `common_ancestors` **recebeu decisão equivalente nesta rodada** (pergunta 2, execução agendada). Resta a **ordem de inserção das arestas**. |
| `X-04` | **A ordem de inserção das arestas do grafo não está sob teste**, embora determine qual caminho o `shortest_path` devolve. | `spec-impact-matrix.md` §8 | Sem teste. É a lacuna que a migração nomeia como `BR-MIGRAR-024`. **É a última lacuna de ordem do projeto.** |
| `X-03` | **Cobertura desigual — remedida nesta rodada:** `src/` = **89 %** (era 83 %). Pior: `ports/adaptadores.py` **73 %**, que é **exatamente** o módulo do caminho de gravação sem teste (`L-28`/`X-05`). Depois: `app.py` 77 %, `relationship_hypotheses` 78 %, `mermaid_render` 78 %. | `spec-impact-matrix.md` §8 | ✅ **Remedida em 2026-10-10.** O número virou **acionável**: a pior cobertura do projeto está no módulo onde a lacuna já apontava, e o `number_format.py`, que era a pior (53 %), subiu para **87 %**. |
| `X-02` / `CS-03` | **Não há vínculo automático** SPEC ↔ CODE ↔ TEST ↔ BUG, e as matrizes de `_reversa_bugs/*/generated/` derivam das specs de **2026-09-30**. | `spec-impact-matrix.md` §8 · `code-spec-matrix.md` §6 | Pendente de regeneração — é o **passo 4 da ordem pós-extração** registrada em `state.json`. |
| `CS-04` | **A cobertura da matriz é de arquivo, não de comportamento.** "🟢 coberto" significa que há requisito, design e tarefa — não que todo caminho de execução esteja especificado. | `code-spec-matrix.md` §6 | Natureza do método. Agora há **dois** números reais para contrastar (83 % → 89 %). |

### 3.4 Custo, medido nesta rodada

| ID | Lacuna | Onde | Situação |
| --- | --- | --- | --- |
| `L-20` | `get_children` varre todas as famílias **sem índice**, e `person_a`/`person_b` são **fichas completas** por resultado. | `busca-caminho/design.md` § Riscos | ✅ **medida:** 15,4 ms por ficha, **142 fichas ≈ 2,2 s** — contra **20,9 s de parse** e **1,73 s** de uma chamada de `homonym_dossier`. **O gargalo é o parse, não as fichas.** Decisão: **não otimizar agora**, porque a otimização mexeria em `get_children`, que alimenta também a detecção de colapso, e a ordem das arestas é contrato de paridade. |
| — | **O parse da árvore custa ~21 s** para 35.460 pessoas, e **nada é cacheado entre requisições**. | `upload-gedcom/design.md` (NFR) | 🟡 Declarado desde 2026-10-05 como consequência do `ADR-24`. Agora **tem número**. Não é lacuna: é o preço explícito da árvore-como-valor. |

### 3.5 Correções agendadas — liberadas pelo Passo 4, concluído em 2026-10-13

| ID | O que falta | Onde | Situação |
| --- | --- | --- | --- |
| `L-25` | `common_ancestors` / `additional_paths`: quarto critério determinístico no empate triplo. | `busca-caminho/design.md` | Decisão tomada (pergunta 2). **Liberada** pelo Passo 4 de 2026-10-13; aguarda execução. |
| `L-28` / `X-05` | Ambiente de teste **com** `psycopg2`, para o caminho feliz de INSERT. | `analise-dna/design.md` | ✅ **executada em 2026-10-13** pelo instrumento `tests/verificacao_no_conteiner.py`, que roda **dentro da imagem** (o `.venv/` oficial não foi tocado). Medido contra o PostgreSQL do compose: `registrar()` devolve referência, `dna_analysis` com `accepted=1`/`skipped=0`, 3 linhas em `analysis_person`, `match_result.matched_person_xref=I13` (a **FK composta** satisfeita), `match_kit` com cM `[200.0, 60.0]` **sem soma**, `match_path_node` com 3 nós em papéis do domínio fechado, `skipped_match` = 0, e a limpeza deixou **0 linhas** no histórico do operador. |
| `L-33` | Verificação da arte **dentro do contêiner**. | `recursos-da-tela/design.md` | ✅ **executada em 2026-10-13** pelo mesmo instrumento. Medido na imagem: `/apple-touch-icon.png` (200, `image/png`, 16.504 bytes, `sha256 c89e29e2fc029287…`), `/banner.png` (200, `image/png`, 317.058 bytes, `sha256 1629dfd08ffb8f7d…`), `/app.css` (200, `text/css`, 8.816 bytes, `sha256 82a67d33b3ef09fb…`) e `GET /` (200, 28.858 bytes) — os **mesmos hashes do host**, o que prova que a arte que a imagem serve é a arte atual. O comando está no `README.md`, seção Testes. |
| `L-30` | Corrigir a docstring de `motivo_de_indisponibilidade` (o ramo **fica**). | `tela-de-entrada/design.md` | ✅ **verificada como já executada** em 2026-10-13: a frase antiga ("o caso do acento e do espaço, medido na pasta real") **não existe mais** e a docstring traz a "Nota medida depois da `RN-20`", que declara o segundo ramo quase inalcançável e mantém o ramo. Nenhuma mudança de código foi necessária. |
| — | Log de servidor nas duas tentativas de aposentar (sucesso e fracasso). | `tela-de-entrada/requirements.md` | Decisão tomada (pergunta 14). **Liberada** pelo Passo 4 de 2026-10-13; aguarda execução. |

> **Passo 4 concluído em 2026-10-13.** A nota que prendia estas correções dizia: *"não corrigir código do legado antes da Fase 5 e do Passo 4 — o Passo 4 confere regressão contra as features 003/004, e mexer no código antes disso é trabalhar com duas variáveis ao mesmo tempo"*. A Fase 5 foi concluída em 2026-10-10 e o Passo 4 foi fechado em **2026-10-13** (12 features, 67 watch items: 61 🟢, 5 🟡 e 1 🔴 — o mesmo `010-W008`, com triagem humana pendente; paridade em 100 % e suíte em 605 passam / 9 pulados / 0 falham). As correções desta tabela estão, portanto, **liberadas**.

---

## 4. Lacunas cosméticas ⚪

| ID | Lacuna | Onde |
| --- | --- | --- |
| `M-01` | O estado `affinity` é atribuído a uma **cópia** do dicionário; o original segue `not_found`. Nenhum consumidor atual usa o original — mas a divergência é armadilha para quem reimplementar. | `state-machines.md` §7 · `busca-caminho/contracts.md` §2.1 |
| `M-02` | A ambiguidade rebaixa `found` → `ambiguous`, mas **não** rebaixa `not_found`. **Decidido em 2026-10-05: é intencional** e virou contrato. | `state-machines.md` §4.3 |
| `E-02` | O item de resultado **não referencia a pessoa escolhida por chave**, só por nome e pelo conteúdo do documental. | `erd-complete.md` §8 |
| `CS-01` | O `app.py` tem **cinco donos** (um por ramo de `action`) mais as duas rotas de arte: a ordem das guardas e a re-parse atravessam as units. **Cresceu de 267 para 559 linhas úteis.** | `code-spec-matrix.md` §6 |
| `CS-02` | `documentary_relationship.py` e `mermaid_render.py` são **compartilhados** entre `busca-caminho` e `analise-dna` — e o `L-24` mostrou o custo: **uma** regra em `busca-caminho` degrada os avisos de `analise-dna`. | `code-spec-matrix.md` §6 |
| `CS-07` | **Duas units novas entraram sem arquivo próprio:** `tela-de-entrada` tem um arquivo puro e o resto em `app.py`; `recursos-da-tela` tem **zero** arquivos de módulo. A granularidade `endpoint` permite isso, mas a matriz deixa de localizar o código de uma unit sem ler o `app.py`. | `code-spec-matrix.md` §6 |
| `CS-08` | **`src/uploads/` contém dado real dentro da árvore do projeto** — 13 arquivos e 4 aposentados, incluindo um GEDCOM de 5,3 MB. Fora do versionamento e do contexto de build, mas **no disco**. | `code-spec-matrix.md` §6 |
| `L-34` | O `sha256` do HTML de `GET /` é um invariante **mantido à mão**, atualizado três vezes em 2026-10-10. Decidido: vira âncora estrutural quando doer — o hash **funcionou** nesta rodada. | `recursos-da-tela/design.md` § Riscos |
| — | A caixa de regressão do banner `(778,232)–(918,338)` descreve uma composição que **não existe mais** (a do abajur). Decidido: **manter**, com o comentário de origem. | `recursos-da-tela/design.md` · `tasks.md` |
| — | Divergência de versão de `RapidFuzz` entre o pin e o `.venv` — declarado; o pin e o ambiente **coincidem** em 3.14.6 hoje. | `analise-dna/design.md` § Riscos · `adrs/13` |

---

## 5. Fechadas nesta rodada — 21 lacunas

### Por execução de experimento (3)

| ID | Como foi fechada |
| --- | --- |
| **`L-24`** / **`E-05`** | **Deixou de ser inferida.** Duas árvores sintéticas de 4 pessoas, com a **mesma chave** `(4, '@I1@', '@I9@')` e xrefs interiores diferentes, carregadas no mesmo processo: o dossiê da segunda citou **`@I2@` — que não existe nela** — e degradou para `"Sem Nome"`, **sem levantar nada**. A segunda árvore não continha nenhum "Joao". O gatilho medido é a **contagem**, não o conteúdo. Correção aceita, agendada |
| **`L-31`** | **Fechada por medição negativa:** na pasta real, **13 grupos e nenhum com mais de um membro** — a divergência de elegibilidade **não pode ocorrer** nos dados atuais. Decisão: manter a decisão pelo representante |
| **`L-20`** | **Medida:** 15,4 ms/ficha → 142 fichas ≈ **2,2 s**, contra 20,9 s de parse e 1,73 s de dossiê. **O gargalo é o parse.** Decisão: não otimizar |

### Por verificação no código (3)

| ID | Como foi fechada |
| --- | --- |
| **`L-16`** / **`M-03`** / **`P-02`** | **Corrida entre requisições concorrentes: ELIMINADA estruturalmente** (`ADR-24`, 2026-10-07). A árvore é valor de retorno e entra por parâmetro; `gedcom_state.py` não existe mais. Provado por `test_arvore_devolvida.py` e `test_dependencias_nucleo.py`. **Era a única lacuna crítica das duas rodadas anteriores** |
| **`CS-06`** | **Bytecode órfão removido.** `src/core/__pycache__/gedcom_state.cpython-314.pyc` apagado; reverificado: **nenhum** bytecode de `src/` ficou sem `.py` (os outros 34 conferem) |
| **`X-01`** | **A matriz de impacto FOI relida contra as specs novas** — é esta própria revisão. A releitura encontrou e corrigiu uma afirmação errada na Matriz D (`CAUSAS_POSSIVEL` = 9 → **8**) e um valor desatualizado (`number_format` 53 % → **87 %**) |

### Por decisão sua (15)

| # | Pergunta | Decisão | Efeito |
| ---: | --- | --- | --- |
| 1 | `L-24` cache de nomes | **Medir primeiro** → medido, **corrigir** | Confirmado por execução; correção agendada |
| 2 | `L-25` ordem de ancestrais | **Mesmo tratamento do `matching`** | Quarto critério determinístico; execução agendada |
| 3 | `L-30` motivo "fora da forma" | **Corrigir a docstring, manter o ramo** | `T-06` desbloqueada; execução agendada |
| 4 | `CS-06` bytecode órfão | **Apagar** | ✅ **executado nesta rodada** |
| 5 | `L-29` / `P-07` dado pessoal | **Declarar a proibição de uso com dado de terceiros** + retenção/expurgo/consentimento como **requisito do alvo nº 5** | Registrado em `analise-dna/requirements.md` e `design.md` |
| 6 | `L-28` / `X-05` INSERT sem teste | **Criar ambiente de teste com o driver**, **sem** tocar no `.venv/` oficial | Agendado; ganhou número (`adaptadores.py` = 73 %, a pior cobertura) |
| 7 | `L-33` arte no container | **Health check no arranque** | Protege a **operação**, não o CI. Agendado |
| 8 | `L-34` sha256 do HTML | **Âncora estrutural quando doer** — o hash funcionou | Declarado |
| 9 | Custo de 317 KB/requisição | **Aceitar** — o `ETag` cobre; cache reintroduziria estado de processo | Declarado |
| 10 | Caixa de regressão do banner | **Manter**, com o comentário de origem | Declarado |
| 11 | `TM-02` arquivos sem chave | **Declarar definitivo** (movidos à mão); regularizar quebraria a `BR-T-16` | Declarado |
| 12 | `L-31` disponibilidade do grupo | **Medir** → medido (nenhum grupo com 2 membros); **manter** | Fechada |
| 13 | `_arvore_do_formulario` sem dono | **Declarar em contrato**; movê-la é decisão de arquitetura maior | Declarado |
| 14 | Aposentadoria sem log | **Logar as duas tentativas** | Agendado |
| 15 | Listagem sem filtro | **Confirmar** a decisão | Declarado |
| 16 | `L-20` custo do dossiê | **Medir** → medido; **não otimizar** | Fechada |
| 17 | Duas análises, duas linhas | **Aceitar**: o histórico é **trilha de execuções** | Declarado, com a consequência registrada na pergunta 5 |
| 18 | Cobertura | **Remedir** → **89 %** | `X-03` atualizada com o ranking novo |

---

## 6. Requisitos encaminhados ao sistema alvo

**Não são lacunas do legado.** São decisões cuja implementação **não pertence** a ele — porque exigiria identidade, persistência ou uma tela nova, e porque o legado não será o sistema final.

| # | Requisito | Origem | Por que não no legado |
| --- | --- | --- | --- |
| 1 | **Persistir resultados e histórico de análises** | 2026-10-05, pergunta 4 (`L-21`/`E-04`) | ✅ **Parcialmente atendido:** o legado ganhou o histórico na feature 008 (`init.sql`, 6 tabelas). O que falta é o alvo tratá-lo como dado de primeira classe |
| 2 | **Registrar o veredito do operador** por conexão | 2026-10-05, pergunta 8 (`M-04`) | Não existe estado para isso; depende do requisito 1 |
| 3 | **Restringir a exposição da lista completa de nomes** | 2026-10-05, pergunta 6 (`P-03`) | `all_names` alimenta os campos de busca; removê-la hoje quebraria a busca sem substituto |
| 4 | **Validar o conteúdo do CSV na entrada**, como já se faz com o GEDCOM | 2026-10-05, pergunta 14 (`P-05`) | Validar agora rejeitaria arquivos que a leitura tolerante aceita |
| 5 | **Retenção, expurgo e consentimento** para o dado pessoal persistido, inclusive de **pessoas vivas** | 2026-10-10, pergunta 5 (`L-29`/`P-07`) | Construir retenção aqui é construir o que a Onda 3/5 da migração substitui. **Enquanto não existir, o uso do legado com dado de terceiros está declarado PROIBIDO** |
| 6 | **Deduplicar análises repetidas** — ou declarar formalmente que o histórico é trilha | 2026-10-10, pergunta 17 | Decidido: o histórico **é** trilha de execuções. O que o alvo precisa decidir é a política de retenção que isso implica (liga com o requisito 5) |

> **Estes requisitos não estão em nenhum artefato de migração**, porque o pipeline foi concluído em 2026-09-28 e está preservado sem regeneração. Precisam entrar no **próximo ciclo forward** (`_reversa_forward/`) para virarem spec do alvo.

### Pendência de documentação (não é lacuna)

⚠️ **O `README.md` da raiz continua contradizendo o pin.** Documenta o fluxo pelo interpretador **global**; o oficial é o `.venv/` desde 2026-10-05. **Não editei** por ser documento do usuário — a correção é uma linha.

---

## 7. O que **não** é lacuna — decisões vigentes

| Assunto | Decisão |
| --- | --- |
| Regras de aceitação do matching | Definitivas, preservadas com fidelidade 🟢 |
| Homônimos usam o 1º ID | Acolhida — hoje é apenas o **recuo** de uma escolha por combinações 🟢 |
| Upload sem validação de extensão | **Superada** pelo teto e pela validação de conteúdo 🟢 |
| Relaxamento de Jaccard 0,5 → 0,33 | Intencional; o **número** é heurístico e ajustável 🟢 |
| `HARD_MIN` / `GIVEN_MIN` | Não implementar — nunca existiram na reconstrução 🟢 |
| Teto de 20 iterações do BFS | Preservar, sem sinalização 🟢 |
| Varredura condicional de `get_spouses` | Contrato explícito; torná-la complementar muda o resultado 🟢 |
| Legado single-tenant | Aceite de risco temporário, com condição de reabertura nomeada 🟢 |
| Endogamia: avisar, não corrigir | **Confirmada** em 2026-10-05 🟢 |
| Escape do rótulo Mermaid | Lista branca, com entidades **depois** do filtro 🟢 |
| Desempate de candidatos | **Determinístico** pelo menor `xref_id` 🟢 |
| A árvore é um valor, nunca estado global | **`ADR-24`** — é o que fechou o `L-16` 🟢 |
| Elegibilidade da referência por **forma de nome** | `RN-20` / `ADR-32`; duas funções para duas perguntas 🟢 |
| `aposentar` move, nunca apaga | `ADR-30` 🟢 |
| O `dono` existe e **não** isola | `ADR-26`; costura da Onda 3 🟢 |
| A ordem dos ramos de `index` é contrato | `aposentar` **antes** de resolver a árvore (`BR-T-12`) 🟢 |
| `get_name` devolve `''`, nunca `"Sem Nome"`, para formato vazio | Paridade `DIV-001`; medido: **301** em 35.460 🟢 |

---

## 8. Resumo

| Severidade | Itens |
| --- | ---: |
| 🔴 Crítico | **0** |
| 🟠 Moderado | 12 |
| ⚪ Cosmético | 10 |
| **Total em aberto** | **22** |

| Movimento da rodada | Quantidade |
| --- | ---: |
| Fechadas em 2026-10-10 | **21** |
| Perguntas ao usuário | **18** — **todas respondidas** com a recomendação do Revisor |
| Medições/experimentos executados na revisão | **4** (`L-24`, `L-31`, `L-20`, cobertura) |
| Defeitos de consistência corrigidos | **10**, em **11 arquivos** — incluindo o `openapi`, que não era YAML válido |
| Correções de código agendadas (pós-Passo 4) | **5** |
| Requisitos encaminhados ao alvo | **6** |

> **Somente 1 lacuna crítica nas duas rodadas anteriores, e ela está fechada.** O que resta são **12 moderadas** e **10 cosméticas** — custo, cobertura, ordem de arestas e rastreabilidade. **Três delas são limitação da fonte** (`L-18`, `L-17` resíduo, `E-01` resíduo) e **não** são resolvíveis por decisão humana.
>
> **A medição que mais mudou a leitura da rodada foi a do `L-24`.** Ele entrou nesta sessão como o único achado de gravidade alta **inferido** — e a recomendação foi medir antes de decidir. O experimento levou minutos e **confirmou o defeito**, além de revelar algo que a leitura não dava: o gatilho não depende do conteúdo, depende só da **contagem**, e as duas árvores reais pequenas do operador já compartilham os dois extremos da chave. Sem a medição, a correção teria sido feita (ou não) sobre uma hipótese.
>
> **A medição que mais mudou a prioridade foi a da cobertura.** Ela tirou o `number_format` do posto de pior módulo (53 % → 87 %) e colocou lá o `ports/adaptadores.py` com **73 %** — exatamente o módulo cujo caminho de gravação não tem teste feliz. A lacuna `L-28` deixou de ser argumento e passou a ter número.

---

*Gerado pelo Reversa-Reviewer em 2026-10-10 (re-extração, nível completo). Atualizado após as 18 respostas.*

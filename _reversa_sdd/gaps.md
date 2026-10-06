# Lacunas Remanescentes — teste_reversa

> Gerado pelo **Reversa-Reviewer** na re-extração de **2026-10-05** (nível **Completo**). Artefato **novo**.
> **Atualizado em 2026-10-05** após o processamento das **16 perguntas** de `questions.md`.
> Este arquivo é o **passivo** da extração: o que ficou sem resposta depois da revisão. Ele complementa `questions.md` (as perguntas) e `confidence-report.md` (os números).
> Escala de confiança: 🟢 CONFIRMADO | 🟡 INFERIDO | 🔴 LACUNA

---

## 1. Como este arquivo se organiza

| Severidade | Critério | Efeito de ignorar |
| --- | --- | --- |
| 🔴 **Crítico** | Bloqueia a reimplementação **fiel**, ou pode produzir resultado **errado em silêncio** | Quem reimplementar erra sem saber |
| 🟠 **Moderado** | Afeta qualidade, custo ou decisão de produto | A reimplementação funciona, mas herda um problema |
| ⚪ **Cosmético** | Precisão documental ou armadilha de leitura | Custa tempo de quem lê, não corretude |

> ⚠️ **O legado foi tocado nesta rodada**, por autorização explícita nas respostas 1, 2 e 15 — ver §5. Toda lacuna remanescente já foi checada contra o código **depois** dessas mudanças.

---

## 2. Lacuna crítica 🔴

| ID | Lacuna | Onde está documentada |
| --- | --- | --- |
| **`L-16`** / **`M-03`** / **`P-02`** | **Corrida entre requisições concorrentes.** O estado do GEDCOM é global de processo e é reescrito a cada requisição, enquanto o servidor atende com **4 threads**. Duas requisições simultâneas podem intercalar: A parseia a árvore A, B parseia a árvore B, e A segue lendo o estado que agora é o de B. A guarda de instância única impede dois **processos**, não duas **threads**. **Você respondeu que nunca observou resultado cruzado** — o que rebaixa a probabilidade, mas **não fecha** a lacuna: o mecanismo é confirmado por leitura, e o **alcance segue não medido**. O uso single-user tende a não disparar a janela. | `domain.md` §7 · `permissions.md` §4.3 · `state-machines.md` §7 |

> **É a única lacuna crítica que restou.** A mais consequente depois desta é a divergência de ambiente, que **foi encerrada** (§5).

---

## 3. Lacunas moderadas 🟠

### Herdadas do sistema, sem decisão pendente

| ID | Lacuna | Onde | Por que segue aberta |
| --- | --- | --- | --- |
| `L-18` | As relações **mais distantes** não são publicadas na versão 4.0 da fonte — justamente onde o caso real deste repositório cai. | `domain.md` §7 · `analise-dna/design.md` | **Limitação da fonte**, não decisão do projeto: a envoltória por meioses mitiga, e inventar números foi descartado. Não é resolvível por decisão humana. |
| `L-20` | **Custo sem limite:** `get_children` varre todas as famílias sem índice, e `person_a`/`person_b` são fichas completas por resultado (142 fichas nos 71 casos reais). | `domain.md` §7 · `architecture.md` (dívidas 6 e 7) | Custo real, sem limite medido e sem meta de performance definida. Não foi submetido a pergunta porque é otimização, não decisão de negócio. |

### Dados, ordem e teste

| ID | Lacuna | Onde | Situação |
| --- | --- | --- | --- |
| `E-01` | **Ordem é dado, não consequência — e não está modelada.** Três ordens determinam resultado: inserção das arestas do grafo, ordem dos candidatos de nome e ordem de apresentação. Só a terceira é explícita no código. | `erd-complete.md` §8 | ✅ **Melhorou nesta rodada:** o desempate de nomes passou a ter critério determinístico (menor `xref_id`), o que remove **uma** das três. As outras duas seguem. |
| `X-04` | **A ordem de inserção das arestas do grafo não está sob teste**, embora determine qual caminho o `shortest_path` devolve. | `spec-impact-matrix.md` §8 | Sem teste. É a lacuna que a migração já nomeia como `BR-MIGRAR-024`. |
| `X-03` | **Cobertura desigual, agora medida.** Global de `src/`: **83 %**. Piores: `number_format` **53 %**, `relationship_hypotheses` **76 %**, `mermaid_render` **78 %**, `evidence_comparison` **83 %**. Melhores: `validate` 98 %, `dna_analysis` 97 %. | `spec-impact-matrix.md` §8 | ✅ **Medida em 2026-10-05** (era "não medida"). O número existe; **a lacuna de qualidade permanece** — `number_format` é a autoridade de todo número exibido na tela. |
| `X-01` | **A matriz de impacto não foi relida contra as specs novas** — foi escrita pelo Arquiteto antes da fase de geração. | `spec-impact-matrix.md` §8 | Pendente de releitura. |
| `X-02` / `CS-03` | **Não há vínculo automático** SPEC ↔ CODE ↔ TEST ↔ BUG. As matrizes de `_reversa_bugs/*/generated/` derivam das specs de 2026-09-30 e estão defasadas. | `spec-impact-matrix.md` §8 · `code-spec-matrix.md` §6 | Pendente de regeneração. |
| `CS-04` | **A cobertura da matriz é de arquivo, não de comportamento.** "🟢 coberto" significa que há requisito, design e tarefa — não que todo caminho de execução esteja especificado. | `code-spec-matrix.md` §6 | Natureza do método. Agora há um número real (83 %) para contrastar. |

---

## 4. Lacunas cosméticas ⚪

| ID | Lacuna | Onde |
| --- | --- | --- |
| `M-01` | O estado `affinity` é atribuído a uma **cópia** do dicionário; o original segue `not_found`. Nenhum consumidor atual usa o original — mas a divergência é armadilha para quem reimplementar. | `state-machines.md` §7 |
| `E-02` | O item de resultado **não referencia a pessoa escolhida por chave**, só por nome e pelo conteúdo do documental. | `erd-complete.md` §8 |
| `CS-01` | O `app.py` tem **três donos**: cada ramo de `action` pertence a uma unit, mas a ordem das guardas e a re-parse atravessam as três. Mudar ali exige atualizar **três** specs. | `code-spec-matrix.md` §6 |
| `CS-02` | `documentary_relationship.py` e `mermaid_render.py` são **compartilhados** entre `busca-caminho` e `analise-dna`. | `code-spec-matrix.md` §6 |
| `CS-05` | A matriz **esconde a concentração de dependência**: `gedcom_state` é usado por 8 dos 19 módulos e não pode ser "de uma unit". | `code-spec-matrix.md` §6 |

---

## 5. Fechadas nesta rodada — 16 lacunas

### Por execução no código (3)

| ID | Como foi fechada |
| --- | --- |
| **`L-15`** | **Determinismo do desempate.** Você autorizou corrigir o legado: `matching.py` ganhou o **quarto critério** (menor `xref_id`), com **2 testes** de regressão. Era a única decisão humana vigente que o código violava — **as 13 estão honradas agora** |
| **`P-04`** | **`app.secret_key` removido** de `src/app.py`. Não tinha consumidor; nenhum teste o referencia |
| **`E-03`** | **Sentinela de kit tornada incapaz de colidir.** `SEM_KIT` passou a ser `" SEM-KIT"`, com espaço à esquerda: como `_clean` remove espaços das pontas de todo valor do CSV, nenhum kit real pode ter esse texto. **Teste novo** prova três grupos separados (kit real, ausência de kit e um kit literalmente chamado `SEM-KIT`) |

### Por decisão sua (9)

| ID | Decisão | Efeito |
| --- | --- | --- |
| **`P-01`** | Autenticação: é **omissão** | Correção pertence à **Onda 3** da migração; nada muda no legado, porque sem identidade a correção é inverificável |
| **`L-14`** | O `0,33` foi **chute que funcionou** | O número passa a **heurístico e ajustável**; a decisão de manter o relaxamento segue 🟢 |
| **`L-17`** | Endogamia: **avisar basta** | O veredito não é rebaixado por colapso detectado; o cM segue declarado como teto otimista |
| **`L-19`** | O `.venv/` é o **interpretador oficial** | `requirements.txt` realinhado (`ged4py==0.5.5`, `networkx==3.7`, `pandas==3.0.6`) + **`rapidfuzz` e `python-Levenshtein` promovidos a dependência declarada** |
| **`L-21`** | Persistência: é **herança**, e vira requisito do alvo | O legado mantém o comportamento efêmero; o histórico entra em §6 |
| **`L-22`** | Discartes são **acionáveis** | `RF-23` sobe de `Should` para `Must`, e cada motivo ganha **ação esperada** em `analise-dna/design.md` |
| **`L-23`** | Cobertura: **medir agora** | Medida: **83 %** de `src/`, com o detalhe por módulo |
| **`M-02`** | A assimetria da ambiguidade é **intencional** | Vira contrato: `not_found` **não** é rebaixado, porque já é resultado mais fraco |
| **`L-08`** | Você usa **apenas o GEDmatch** | Cobertura de exportadores deixa de ser incerteza e passa a ser **declarada** |

### Por verificação no código (2)

| ID | Como foi fechada |
| --- | --- |
| **`L-06`** | **Por leitura do template.** `index.html:43-45` usa `success` para a cor do alerta e `:457` usa `path_result` para o cartão — "conexão", "sem conexão" e "erro" produzem telas distintas |
| **`M-04`** | **Registro do veredito do operador é requisito** — e vai para §6. A parte verificável (não existe estado para isso hoje) está confirmada no código |

> Mais `P-05` (validação do CSV é assimetria **herdada**, a corrigir no alvo) e `P-03` (a exposição da lista de nomes **deve ser restringida**), ambos em §6.

---

## 6. Requisitos encaminhados ao sistema alvo

**Não são lacunas do legado.** São decisões tomadas nesta revisão cuja implementação **não pertence** a ele — porque exigiria identidade, persistência ou uma tela nova, e porque o legado não será o sistema final.

| # | Requisito | Origem | Por que não no legado |
| --- | --- | --- | --- |
| 1 | **Persistir resultados e histórico de análises** | Pergunta 4 (`L-21`, `E-04`) | Nada é persistido hoje; criar persistência no legado é construir o que a Onda 3 substitui. Exige banco, que o alvo já especifica (`migration/target_data_model.md`) |
| 2 | **Registrar o veredito do operador** por conexão (aceitei / rejeitei / corrigi) | Pergunta 8 (`M-04`) | Não existe estado para isso, e sem persistência um veredito não teria onde viver — depende do requisito 1 |
| 3 | **Restringir a exposição da lista completa de nomes** (busca no servidor) | Pergunta 6 (`P-03`) | `all_names` alimenta os campos de busca; removê-la hoje **quebraria a busca sem substituto**. É trabalho da Onda 4 (SPA) |
| 4 | **Validar o conteúdo do CSV na entrada**, como já se faz com o GEDCOM | Pergunta 14 (`P-05`) | Validar agora rejeitaria arquivos que a leitura tolerante aceita — mudaria comportamento sem substituto |

> **Estes quatro requisitos não estão em nenhum artefato de migração**, porque o pipeline de migração foi concluído em 2026-09-28 e está preservado sem regeneração. Eles precisam entrar no **próximo ciclo forward** (`_reversa_forward/`) para virarem spec do alvo.

### Pendência de documentação (não é lacuna)

⚠️ **O `README.md` da raiz contradiz o pin.** Ele documenta o fluxo pelo interpretador **global** (`pip install -r requirements.txt`, `python src/app.py`, sem ativar o venv). Com a decisão da pergunta 11, o oficial é o `.venv/`. **Não editei o README** por ser documento do usuário — a correção é uma linha, e a decisão de editar é dele.

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

---

## 8. Resumo

| Severidade | Linhas | IDs distintos |
| --- | ---: | ---: |
| 🔴 Crítico | 1 | 3 |
| 🟠 Moderado | 8 | 9 |
| ⚪ Cosmético | 5 | 5 |
| **Total em aberto** | **14** | **17** |

| Movimento da rodada | Quantidade |
| --- | ---: |
| Fechadas em 2026-10-05 | **16** |
| Perguntas ao usuário | **16** — **todas respondidas** |
| Requisitos encaminhados ao alvo | **4** |
| Mudanças de código autorizadas | **4 arquivos + 3 testes** |

> **Somente 1 das 14 linhas em aberto é crítica** — a corrida entre threads, que você nunca observou e que o uso single-user tende a não disparar. **Nenhuma das 14 depende de decisão sua**: são limitações da fonte (`L-18`), custo (`L-20`) e trabalho de rastreabilidade e teste (`X-*`, `CS-*`, `E-*`).
>
> **A pergunta que mais mudou o projeto foi a 11** (interpretador oficial): ela encerrou a divergência de ambiente, que era a de maior risco silencioso — duas execuções do mesmo código dando resultados diferentes sem ninguém mudar nada.

---

*Gerado pelo Reversa-Reviewer em 2026-10-05 (re-extração, nível completo). Atualizado após as 16 respostas.*

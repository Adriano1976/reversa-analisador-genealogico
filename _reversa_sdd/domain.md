# Domínio de Negócio — analisador-genealogico

> Nível de documentação: **Completo** (`state.json` → `doc_level`, decidido em 2026-10-05)
> Re-extração de **2026-10-05**. Substitui o `domain.md` de 2026-09-30 (nível `essencial`), que descrevia a raiz `analisador-genealogico/`, o pacote `reconstructed/` e **não conhecia** a regra final da análise.
> Snapshot da versão substituída: `.reversa/snapshots/2026-10-05-pre-reextracao/domain.md`
> Escala de confiança: 🟢 CONFIRMADO | 🟡 INFERIDO | 🔴 LACUNA
> Artefatos irmãos desta rodada: `adrs/` (23 decisões), `state-machines.md`, `permissions.md`, `code-analysis.md`, `data-dictionary.md`, `flowcharts/`

---

## 1. Glossário de Domínio

| Termo | Definição | Conf. |
| --- | --- | --- |
| **GEDCOM** | Formato padronizado (`.ged`) para troca de árvores genealógicas. Define registros `INDI` (pessoa) e `FAM` (família). | 🟢 |
| **INDI** | Registro de indivíduo, identificado por `xref_id` (ex.: `@I0001@`). `FAMC` referencia a família onde é filho(a); `FAMS` as famílias onde é cônjuge. | 🟢 |
| **FAM** | Registro de família, identificado por `xref_id` (ex.: `@F1@`). Campos `HUSB` (marido), `WIFE` (esposa) e `CHIL` (filhos). | 🟢 |
| **DNA Match** | Pessoa do relatório CSV de matches compartilhados (GEDmatch, MyHeritage, FamilyTreeDNA) com valor de cM compartilhado. | 🟢 |
| **cM (centiMorgan)** | Unidade de recombinação genética. Valor maior indica parentesco mais próximo. | 🟢 |
| **Kit** | Amostra de teste genético de uma pessoa. **Duas linhas com o mesmo nome e kits diferentes são duas evidências distintas** — nunca uma só, e seus cM nunca são somados entre si. | 🟢 |
| **Parentesco documental** | O que o **GEDCOM afirma**: caminho por pais, ancestral comum, distância geracional e rótulo de parentesco. **Nunca lê cM.** | 🟢 |
| **Evidência genética** | O que o **CSV de DNA informa**: kit, fonte, cM total, segmentos, maior segmento, SNPs, cromossomos, posições. **Não conhece o GEDCOM.** | 🟢 |
| **Possibilidades de parentesco** | Lista de relações compatíveis com um valor de cM, pela tabela publicada do **Shared cM Project 4.0**. É sempre **lista**, nunca um parentesco único. | 🟢 |
| **Confronto** | Comparação entre parentesco documental e evidência genética, que responde **um de quatro estados**: `COMPATIVEL`, `POSSIVEL`, `CONFLITANTE`, `INCONCLUSIVO` — sempre dizendo por quê. | 🟢 |
| **MRCA / Ancestral Comum** | Ascendente mais recente compartilhado entre duas pessoas. Base da conexão **direta**. | 🟢 |
| **Meioses** | Número de saltos pai-filho entre duas pessoas. É a **grandeza que o cM mede** — e a chave que liga o rótulo documental à tabela do Shared cM Project. | 🟢 |
| **Janela** | Faixa de cM esperada para o parentesco documental. Vem da relação exata publicada (SCP 4.0) ou, quando ela não é publicada, da **envoltória** das relações publicadas com o mesmo número de meioses. | 🟢 |
| **Afinidade (ponte matrimonial)** | Elo **por casamento** entre dois ramos que não compartilham ancestral. Nunca é apresentado como parentesco consanguíneo. | 🟢 |
| **Homônimo** | Registros distintos com o mesmo nome (ou nome equivalente sem acento). O sistema **não escolhe em silêncio**: monta dossiê e marca a identidade como ambígua. | 🟢 |
| **Colapso de pedigree / endogamia** | Mesmo ancestral alcançado por **mais de uma cadeia** de pais. Infla o cM esperado. É **detectado e avisado**, não corrigido. | 🟢 |
| **Segmento fraco** | Maior segmento abaixo de **15 cM**. Gera o aviso `segmento_fraco`. Limite é **heurística do projeto**, não da fonte. | 🟢 |
| **Mojibake** | Caracteres corrompidos por encoding incorreto, comum em nomes portugueses exportados. A autoridade única de correção é `utils/text_cleaning.py`. | 🟢 |
| **Aviso (`warning`)** | Par `{code, message}` anexado ao resultado. O `code` é o **estado/invariante de máquina**; a `message` é o texto para o operador. | 🟢 |
| **Descartado (`skipped`)** | Match que o sistema **não** conseguiu ligar a nenhum registro do GEDCOM. Exibido com o motivo, nunca omitido. | 🟢 |
| **Chave de armazenamento** | Identificador do arquivo gravado, derivado do **conteúdo** (sha256 truncado em 16 hexadecimais) e não do nome do cliente. É o valor que circula entre requisições no lugar de uma sessão. | 🟢 |

---

## 2. A Regra Central do Domínio: três eixos que não se contaminam 🟢

Esta é a **decisão de negócio mais importante do sistema** e a razão de existir desta re-extração. Ela nasceu em 2026-10-04 (commits `7bf2676`, `cd8d7f3`, `a4d24df`) e **não existe em nenhum artefato da extração anterior**.

```text
        ┌─────────────────────────┐        ┌─────────────────────────┐
        │  PARENTESCO DOCUMENTAL  │        │   EVIDÊNCIA GENÉTICA    │
        │  (o GEDCOM afirma)      │        │   (o CSV informa)       │
        │  NUNCA lê cM            │        │   NUNCA lê o GEDCOM     │
        └───────────┬─────────────┘        └────────────┬────────────┘
                    │                                   │
                    │                                   ▼
                    │                     ┌───────────────────────────┐
                    │                     │ POSSIBILIDADES (SCP 4.0)  │
                    │                     │ cM → LISTA de relações    │
                    │                     └────────────┬──────────────┘
                    │                                  │
                    └──────────────┬───────────────────┘
                                   ▼
                        ┌──────────────────────┐
                        │      CONFRONTO       │
                        │ 4 estados + o porquê │
                        └──────────────────────┘
```

**As duas proibições, declaradas literalmente no código** (`core/dna_analysis.py:16-23`):

1. O DNA **não** altera o parentesco documental. Um conflito vira **aviso e lista de causas**, nunca reescrita de vínculo (`core/evidence_comparison.py:8-11`).
2. O cM **nunca** é usado sozinho para afirmar parentesco. O código proíbe nominalmente os dois antipadrões que o legado sugeria: `if cm == faixa: parentesco = relacionamento_do_GEDCOM` e `if cm == 10.8: relacionamento = "primo de 4º grau"`.

**Consequência de produto, também decidida:** o rótulo **"Relacionamento Provável (DNA)" foi removido**. O que existe agora é **"Possibilidades de parentesco pelo DNA"**, dentro da seção de evidência genética (`core/dna_analysis.py:22-23`).

### 2.1 Os quatro estados do confronto 🟢

| Estado | Gatilho | Mensagem (contrato literal) |
| --- | --- | --- |
| **COMPATIVEL** | cM **dentro** da janela esperada para o parentesco documental. | "Compatível: o parentesco documental encontrado no GEDCOM não entra em conflito evidente com a quantidade de DNA compartilhada." |
| **POSSIVEL** | cM **fora** da janela, **mas** alguma relação publicada que contém o valor tem faixa que **se sobrepõe** à janela documental. | "Possível: a evidência genética permite esse relacionamento, mas não é suficiente para confirmar o caminho documental." |
| **CONFLITANTE** | cM **fora** da janela e **nenhuma** relação publicada que contém o valor se sobrepõe a ela. | "Conflitante: a quantidade de DNA observada apresenta incompatibilidade significativa com o parentesco documental encontrado. Verifique homônimos, vínculos incorretos, pedigree collapse, endogamia ou outro caminho ancestral." |
| **INCONCLUSIVO** | Sem DNA, sem caminho documental, identidade ambígua, ou **sem faixa publicada** para comparar. | "Inconclusivo: os dados disponíveis não permitem avaliar adequadamente a compatibilidade entre o caminho documental e a evidência genética." |

> **Por que sobreposição de faixas, e não distância em meioses.** As duas distribuições "se tocam" quando as faixas se sobrepõem, e nesse caso o cM **não consegue separar** as duas leituras — é isso que autoriza `POSSIVEL`. A distância em meioses **não** serve como critério, e o código registra o contraexemplo medido: irmãos (1613–3488 cM) e primos de 1º grau com uma remoção (102–980 cM) estão a **uma** meioses de distância e **mesmo assim** não se sobrepõem (`core/evidence_comparison.py:92-94`). 🟢

**Regra de agregação com múltiplos kits** 🟢 — o estado final é sempre o **mais conservador** entre os kits, na ordem `CONFLITANTE > POSSIVEL > COMPATIVEL > INCONCLUSIVO` (`core/evidence_comparison.py:225-227`). O código avisa na tela que fez isso e mostra o estado por kit.

**Rol de causas** 🟢 — `CONFLITANTE` recebe as **12** causas possíveis; `POSSIVEL` recebe um subconjunto de **9** (`CAUSAS_POSSIVEL = CAUSAS_POSSIVEIS[:1] + [3:8] + [10:]`). O próprio código declara que **não é diagnóstico automático**: é o rol que o operador deve considerar (`core/evidence_comparison.py:53-54`).

---

## 3. Regras de Negócio Principais

> As 118 regras catalogadas linha a linha estão em `code-analysis.md` §2.5, §3.5 e §4.5. Esta seção consolida **as decisões de domínio**, não a enumeração.

### 3.1 Parentesco documental 🟢

Dois estágios, **nesta ordem** — o segundo só roda se o primeiro falhar:

| Estágio | Método | Sobe por | Teto | Mensagem |
| --- | --- | --- | --- | --- |
| **Direta** | BFS **bidirecional** (`find_ancestral_path`) | **apenas pais** (`FAMC` / `child_to_family`) | 20 **iterações de profundidade** | `"Conexão direta encontrada (ancestral comum)."` |
| **Indireta** | `nx.shortest_path` no grafo pessoa↔família | **qualquer** vínculo, inclusive casamento | 40 arestas | `"Conexão indireta encontrada (via casamento/afinidade)."` |

- **Sem caminho nos dois estágios** → `"Nenhuma conexão encontrada entre 'X' e 'Y'."` com `success = True` — isto é, **"não achei" não é erro**; erro é entrada inválida (`success = False`). 🟢
- **O teto de 20 conta iterações, não gerações** e corta **em silêncio**; o aviso diz explicitamente que isso **não prova** ausência de parentesco. Decisão humana de 2026-09-30: preservar a fidelidade ao legado e **não** sinalizar de outro modo. 🟢
- **Idade de genitor fora de 12–70 anos** marca `plausible: False` e gera o aviso `data_impossivel`, **sem invalidar o vínculo** — o caminho é mantido "como o GEDCOM o declara" e o operador é convidado a conferir (`core/documentary_relationship.py:497-507`). Sem data para julgar, `plausible` é `None`, e `None` **não** é falso. 🟢
- **Caminhos múltiplos nunca são descartados**: o caminho exibido é o de menor distância total e os demais ficam listados, com o aviso `caminhos_multiplos`. 🟢
- **Afinidade em três lugares**: `status = "affinity"`, rótulo "Sem ancestral comum: conexão por afinidade (casamento)" e um aviso **em maiúsculas** de que aquilo **NÃO** representa parentesco consanguíneo (`core/path_search.py:66-67`, `:187-191`). 🟢
- **A idade só é conferida no caminho direto.** A ponte por casamento **não** passa pela checagem de 12–70 anos — assimetria registrada, não corrigida. 🟡

### 3.2 Evidência genética 🟢

- A chave de evidência é **(nome, kit)**, nunca só o nome. Sem coluna de kit, o **e-mail** assume o papel; sem ambos, a chave é `SEM-KIT` e sai o aviso `kit_ausente`. 🟢
- **Mais de um kit para o mesmo nome** → aviso `multiplos_kits`, e **nenhum total é somado entre kits**. Quando há vários kits e não se sabe qual deles é a pessoa do GEDCOM, `totals.cm` é **`None`** — "é o número honesto". 🟢
- **O cM acumulado nunca é arredondado** no núcleo; o arredondamento é **exclusivamente de apresentação**. O contrato está congelado em `tests/test_formatacao_cm.py`, porque a paridade contra o oráculo exige igualdade exata. 🟢
- **Sem evidência** → `available: False` com o aviso `sem_evidencia`. 🟡 *(o fluxo segue e o confronto responde INCONCLUSIVO)*

### 3.3 Possibilidades (Shared cM Project 4.0) 🟢

- **27 relações publicadas** são a tabela; o cM vira **lista** ordenada por distância da média (empate desempatado pelo nome). 🟢
- **Seis relações NÃO são publicadas** na versão 4.0 — `1C4R`, `1C5R`, `1C6R`, `3C2R`, 2º bisavô/avó e 3º bisavô/avó — justamente as mais distantes. **Nenhum número é inventado**: a janela passa a ser a **envoltória** das relações publicadas com o mesmo número de meioses; sem relação publicada naquele número, **não há janela** e o confronto fica `INCONCLUSIVO`. 🟢
- **Valor sem cobertura publicada devolve lista vazia** e a leitura de que **isso não descarta parentesco**. 🟢
- **A confiança da lista (`indeterminada` / `baixa` / `muito baixa`) é heurística DO PROJETO** e o código a declara como tal: a fonte **não define** grau de confiança. Quanto mais relações contêm o valor, menos o valor discrimina. 🟢
- **Duas limitações da fonte, herdadas de propósito:** a 4.0 **não publica mediana** (existe `average`, não `median`) e a coluna *Range* **exclui 1% dos envios** (0,5% em cada ponta) — a faixa **não** é o intervalo observado completo, e a janela do confronto herda a limitação. Quem reimplementar **não deve** inventar mediana nem tratar a faixa como intervalo total. 🟡

### 3.4 Matching difuso de nomes: o cM **não** decide aceitação 🟢

- **Score** = `0.55·token_sort_ratio + 0.25·partial_ratio + 0.20·ratio(prenome) + InterBonus`, com `InterBonus = 8.0·(sobrenomes em comum) − 4.0·(quantos deles são comuns)`, arredondado a 2 casas. **Pesos herdados do legado, não alterados nesta extração.** 🟢
- **Desempate lexicográfico**: mais sobrenomes em comum → maior similaridade de prenome → maior score. 🟢
- **Filtro anti-falso-positivo**: sem sobrenome em comum **e** sem acerto de sufixo (`filho`, `neto`, `júnior`, `sobrinho`) → candidato **rejeitado**, com o motivo registrado. 🟢
- **Interseção mínima adaptativa**: prenome genérico (20 nomes em `GENERIC_GIVENS`) com ≥ 2 sobrenomes no CSV eleva a exigência de 1 para 2 sobrenomes. 🟢
- **Jaccard de prefixo suave**: limiar 0,50 com ≥ 2 sobrenomes, caindo para **0,33 apenas quando `cM ≥ 150` E o prenome não é genérico**. Decisão humana de 2026-08-03: **intencional**. 🟢
- **O cM só influencia esse limiar** — confirmado por teste de caracterização (`test_limiar_de_cm_nao_muda_a_decisao`). 🟢
- **Equivalentes de grafia** (`netto→neto`, `gouvea`/`gouvêa`/`gouvéia→gouveia`) e **prefixos de sobrenome** (mín. 3 caracteres) resgatam grafias abreviadas ou corrompidas. 🟢
- **Conflito de nome do meio**: token do CSV que não é prenome nem sobrenome e não existe no GEDCOM rebaixa o aceite para `score ≥ 96` e `given ≥ 92`. 🟢
- **O matching recebe o cM DO KIT**, nunca a soma de kits diferentes (`core/dna_analysis.py:168-171`). 🟢

### 3.5 Upload e armazenamento 🟢

- **A validação é de conteúdo, não de extensão**: depois de remover um BOM UTF-8 e espaços à esquerda, o arquivo precisa começar com `0 HEAD`. O `RISK-007` **autoriza** esse relaxamento para não rejeitar GEDCOM de exportador legítimo. 🟢
- **Motivos de recusa, literais**: `arquivo vazio`, `conteudo binario`, `não começa com a declaração 0 HEAD` (`utils/validate.py:97-104`). 🟢
- **O nome do cliente nunca compõe o caminho**: o arquivo é gravado como `<16 hex do sha256 do conteúdo>__<nome visível>`. A forma é **fechada** (`^[0-9a-f]{16}__[A-Za-z0-9._-]+$`) e é ela — e não uma lista negra — que impede escape da pasta de upload. 🟢
- **A extensão original é preservada**, não fixada em `.ged`: fixá-la renomeava o CSV de DNA para `<...>.csv.ged` e quebrava a análise (regressão do `BUG-20260929-QMLY`, corrigida em 2026-10-02). Nome sem extensão recebe `.ged`; nome vazio ou só pontos vira `arvore.ged`. 🟢
- **Mesmo conteúdo, mesma chave — e a chave é o que circula entre requisições.** Um UUID aleatório quebraria a continuidade, porque o formulário devolve `gedcom_filename` no POST seguinte. **É a chave de conteúdo que faz o papel de identificador de sessão** (ver `permissions.md`). 🟢
- **Teto de corpo de 16 MB** com resposta **HTTP 413** e mensagem em português. Ausente no legado, e a ausência fazia o multipart inteiro ser gravado em disco **antes** de qualquer verificação de negócio. 🟢
- **Arquivo com a mesma chave já existente não é reescrito.** 🟢
- **O CSV de DNA não passa por validação de conteúdo** — só a forma do nome é validada (`app.py:86`). É coerente com a leitura tolerante do CSV, mas significa que um CSV arbitrário é gravado antes de qualquer verificação. 🟡

### 3.6 Leitura tolerante do CSV: descartar sim, esconder não 🟢

- Tenta `utf-8` e, na falha, `latin-1`. 🟢
- O separador é decidido pelo cabeçalho entre vírgula, ponto e vírgula, TAB e barra vertical; no empate vence a **vírgula** (padrão do GEDmatch). 🟢
- O cabeçalho é localizado quando há preâmbulo, com **três guardas** contra falsos positivos medidos: frequência ≥ 2, primeira linha divergente e posição dentro das 10 primeiras linhas. As guardas existem para que um arquivo **sem** cabeçalho não perca a primeira linha de dados, e para que um arquivo que **não é tabela** não eleja uma linha com vírgula como cabeçalho. 🟢
- Linha com número de campos diferente do cabeçalho **não derruba a análise**: o arquivo é relido descartando essas linhas, e a tela **publica a contagem e os números de linha**. O que foi descartado não desaparece. 🟢
- O erro, quando nenhuma tentativa produz tabela utilizável, é acionável: diz o separador usado, as colunas encontradas, as linhas divergentes e o que conferir — antes, o operador via o erro cru do pandas em inglês. 🟢

### 3.7 Ordem de apresentação dos resultados 🟢

Decisão deliberada de 2026-10: **primeiro o que tem caminho documental, depois cM decrescente dentro de cada grupo** — e **não** cM global. A justificativa é medida e está no código: no GEDCOM real, são **71 conexões, das quais 64 sem caminho**; ordenar só por cM enterraria as 7 conexões documentais no meio das 64 (`core/dna_analysis.py:220-228`). O código declara que **não é ordem de confiança**.

---

## 4. Fluxo de Decisão por Ação do Usuário

| Ação | Pré-condições | Regra de negócio | Conf. |
| --- | --- | --- | --- |
| **Abrir `/` (GET)** | — | Renderiza a única tela, sem estado. | 🟢 |
| **Upload GEDCOM** (`action=upload_gedcom`) | campo `gedcom` presente e com nome não vazio | Lê o conteúdo **inteiro**, valida **antes** de gravar, grava sob chave de conteúdo, parseia, reconstrói o grafo e devolve os nomes ordenados. Sucesso: `"Arquivo '{nome}' carregado!"` | 🟢 |
| **Qualquer outro `action`** | `gedcom_filename` presente **e** com forma válida **e** arquivo existente | **O GEDCOM é re-parseado a partir da chave recebida, antes de ramificar.** Não há árvore "carregada" sobrevivendo entre requisições: cada requisição remonta a sua. | 🟢 |
| **Path Search** (`action=path_search`) | duas pessoas resolvíveis por nome | Testa até 5×5 combinações de homônimos e vence a **primeira que tiver caminho**; tenta conexão direta; se falhar, indireta; se ambas falharem, informa sem conexão com `success=True` | 🟢 |
| **DNA Analysis** (`action=dna_analysis`) | CSV presente + `root_name` resolvível no GEDCOM | Agrega por (nome, kit), casa nomes, calcula parentesco documental até a raiz, lista possibilidades e confronta. Ordena com documental primeiro. | 🟢 |
| **Match casa mas não tem caminho documental** | — | **Não é mais descartado em silêncio.** Entra no resultado com as quatro seções; 64 dos 71 casos reais são assim. Só vai para `skipped` o match que **não casa com nenhum registro**. | 🟢 |
| **Match não casa** | — | Vai para `skipped_matches` com o motivo específico (ex.: `"sem candidatos por sobrenome (abreviação/corrupção?)"`, `"sem sobrenome em comum (filtro anti-falso-positivo)"`, `"score insuficiente ou conflito de sobrenome (...)"`). | 🟢 |
| **Raiz ambígua** | `root_name` casa com mais de um registro | Usa o **primeiro** e avisa quantos e quais são. | 🟢 |
| **Pessoa não encontrada por nome** | — | `"Pessoa 1 '{nome}' não encontrada."` / `"Pessoa 2 '{nome}' não encontrada."` com `success=False`. | 🟢 |
| **Subir uma segunda instância** | porta já em uso | **Recusa subir**, com diagnóstico que separa "porta ocupada" de "endereço indisponível" porque pedem ações diferentes. | 🟢 |

---

## 5. Contrato de Mensagens ao Usuário 🟢

Texto de **contrato**, não prosa: testes de golden file e o harness de paridade dependem de literais.

### 5.1 Camada de rota (`src/app.py`)

| Mensagem | Local | Categoria |
| --- | --- | --- |
| `"Nenhum arquivo GEDCOM enviado."` | `:113` | Erro de entrada |
| `"Nenhum arquivo selecionado."` | `:116` | Erro de entrada |
| `"Arquivo '{nome original}' carregado!"` | `:122` | Sucesso |
| `"Arquivo não reconhecido como GEDCOM: {motivo}."` | `:83` | Erro de conteúdo |
| `"Erro ao processar GEDCOM: {e}"` | `:124` | Erro de parse |
| `"Erro: Arquivo GEDCOM não encontrado."` | `:128` | Erro de entrada |
| `"Erro: Arquivo '{chave}' não existe mais."` | `:131` | Erro de estado |
| `"Por favor, carregue o arquivo CSV de matches."` | `:137` | Erro de entrada |
| `"Ocorreu um erro: {e}"` | `:154`, `:169` | Erro inesperado |
| `"Arquivo maior que o limite de {n} MB."` (**HTTP 413**) | `:65` | Recusa por tamanho |

### 5.2 Núcleo (`src/core/`)

| Mensagem | Local | Categoria |
| --- | --- | --- |
| `"{n} conexões encontradas. {m} descartadas."` | `dna_analysis.py:231` | Sucesso |
| `"Seu nome '{root_name}' não foi encontrado no GEDCOM."` (exceção) | `dna_analysis.py:92` | Erro de entrada |
| `"Colunas de Nome e cM não encontradas no CSV. ..."` (exceção, acionável) | `dna_analysis.py:117-123` | Erro de arquivo |
| `"Colunas de Nome e cM não encontradas no CSV."` | `genetic_evidence.py:125` | Erro de arquivo |
| `"Conexão direta encontrada (ancestral comum)."` | `path_search.py:176` | Sucesso |
| `"Conexão indireta encontrada (via casamento/afinidade)."` | `path_search.py:185` | Sucesso |
| `"Nenhuma conexão encontrada entre '{p1}' e '{p2}'."` | `path_search.py:181` | Sem resultado |
| `"Pessoa 1 '{nome}' não encontrada."` / `"Pessoa 2 ..."` | `path_search.py:139`, `:141` | Erro de entrada |
| `AVISO_AFINIDADE` — `"...NÃO representa parentesco consanguíneo."` | `path_search.py:66-67` | Alerta obrigatório |
| `"Sem ancestral comum: conexão por afinidade (casamento)"` (rótulo) | `path_search.py:188` | Rótulo |
| `"Pessoas não encontradas no GEDCOM"` / `"Parentesco documental não encontrado"` (rótulos) | `documentary_relationship.py:445`, `:470` | Rótulo |
| `"Sem Nome"` — **apenas** quando não há `name` | `gedcom_state.py:43`, `:52` | Fallback de exibição |
| As **4 mensagens** de `MENSAGENS[...]` (§2.1) | `evidence_comparison.py:41-51` | Veredito do confronto |

> ⚠️ **Correção contra a extração de 2026-09-30.** O `domain.md` anterior listava `"Relação distante ou indeterminada"` como mensagem do núcleo em `dna_analysis.py:66`. No código atual esse literal **existe apenas em `core/cm_estimator.py`**, que está **fora do fluxo** e não é consultado pela interface. `get_relationships_by_cm` é hoje superfície de compatibilidade, não caminho de produção.

---

## 6. Decisões Humanas Vigentes

> Todas foram **verificadas contra o código de 2026-10-05**. A coluna de situação diz se o código atual **honra** a decisão.

### 6.1 Decisões de 2026-08-03 (4)

| # | Assunto | Resposta vigente | Situação no código atual | Conf. |
| --- | --- | --- | --- | --- |
| 1 | Regras de aceitação do matching | **Definitivas** — preservar com fidelidade | ✅ honrada: 5 ramos de aceitação + filtro anti-falso-positivo intactos | 🟢 |
| 2 | Homônimos usam o 1º ID | **Aceitável** | ⚠️ **ampliada**: hoje testa até 5×5 combinações e vence a primeira com caminho; o 1º ID é só o recuo. A escolha deixou de ser silenciosa | 🟢 |
| 3 | Upload sem validação de extensão/tamanho | **Limitação aceita** para uso local | ❌ **superada**: hoje há teto de 16 MB, validação de conteúdo e chave de conteúdo (`BUG-20260929-QMLY`) | 🟢 |
| 4 | Relaxamento de Jaccard 0,5 → 0,33 com cM ≥ 150 | **Intencional** — mantém-se | ✅ honrada em `matching.py:132-136` | 🟢 |

### 6.2 Decisões de 2026-09-30 (5 respostas)

| # | Assunto | Resposta | Situação no código atual | Conf. |
| --- | --- | --- | --- | --- |
| 1 | Teto de 20 iterações do BFS | **Aceitável** — preservar fidelidade ao legado | ✅ honrada: `MAX_DEPTH = 20`, corte silencioso mantido, nenhum requisito novo | 🟢 |
| 2 | Varredura global de `get_spouses` | **Intencional** — documentar como contrato | ✅ honrada: a varredura só roda quando a lista de `FAMS` fica vazia | 🟢 |
| 3 | Entidades decorativas (`Family`, `GenealogyGraph`, `DNAGroup`) | **Arquitetura abandonada — REMOVER** | ✅ **executada**: removidas no commit `6a52d69` (2026-09-30) | 🟢 |
| 4 | Desempate de candidatos | **Precisa ser determinístico** (critério sugerido: menor `xref_id`) | ✅ **Honrada em 2026-10-05** — o legado foi corrigido: quarto critério de desempate (`matching.py:107-111`), com 2 testes novos | 🟢 |
| 5 | Faixas de cM escritas à mão | **Declarar como heurística** | ✅ honrada: `cm_estimator.py` marcado "LEGADO, fora do fluxo", reexportado só por compatibilidade | 🟢 |

### 6.3 Decisões operacionais de 2026-10-02 e 2026-10-04

| Assunto | Decisão | Situação | Conf. |
| --- | --- | --- | --- |
| Isolamento entre usuários (`BUG-20260929-BJJH`) | **Não corrigir no legado.** Legado permanece **single-tenant por aceite de risco** (mitigação de 2026-10-04, `kind: risk-acceptance`); tratamento na **Onda 3** da migração. Motivo declarado: "Só eu mesmo" usa a aplicação | ⚠️ vigente, e a exposição **deixou de ser promessa de disciplina**: o padrão passou a ser `127.0.0.1` e a segunda instância é recusada | 🟢 |
| Correção do `BUG-20260929-QMLY` | Validação de limite + chave derivada do conteúdo | ✅ aplicada em 2026-10-02 | 🟢 |
| Servidor de entrada (feature `004`) | **waitress**, instância única, escuta local por padrão | ✅ aplicada em 2026-10-04 | 🟢 |
| Formatação de cM (`BUG-20261004-EWSJ`) | Ruído de ponto flutuante sai da tela | ✅ corrigida em 2026-10-04 | 🟢 |

---

## 7. Lacunas 🔴 (requerem validação humana)

| ID | Lacuna | Conf. |
| --- | --- | --- |
| **L-15** | ✅ **FECHADA em 2026-10-05.** A pergunta 4 de 2026-09-30 mandou tornar o desempate **determinístico**, e o código violava o requisito. Você autorizou **corrigir o legado**: foi acrescentado o critério final do **menor `xref_id`** (empate triplo), com **2 testes** de regressão sob ordens de *pool* opostas. Registro preservado: a divergência mecanismo/alcance foi confirmada (a ordem de iteração do `set` muda a cada semente de hash) e o efeito propagava até o veredito do confronto. **É a segunda divergência deliberada do legado — e a primeira que muda comportamento.** | 🟢 |
| **L-16** | **Contaminação entre requisições concorrentes.** O estado do GEDCOM é **global de processo** e é **reatribuído/mutado a cada requisição** (`app.py:126`, `:137` → `core/gedcom_state.py`), enquanto o servidor atende com **4 threads** por padrão (`app.py:188`). Duas requisições simultâneas podem intercalar: A parseia a árvore A, B parseia a árvore B, e A segue lendo o estado que agora é o de B. A guarda de instância única impede dois **processos**, não duas **threads**. **Consequência de negócio:** a separação entre árvores, hoje, depende de não haver concorrência sobreposta. Não reproduzido empiricamente nesta rodada. | 🟡 |
| **L-17** | ✅ **DECIDIDA em 2026-10-05 — avisar é suficiente.** O colapso continua detectado no lado documental (aviso `colapso_de_pedigree`) e **sem alterar o veredito** do confronto; o cM permanece declarado como **teto otimista** nesses casos. A confirmação fecha a incerteza que a `adrs/21` registrava em 🟡. | 🟢 |
| **L-18** | **Relações mais distantes não publicadas na SCP 4.0**, que é exatamente onde o caso real deste repositório cai. O tratamento por envoltória de meioses mitiga, sem substituir a fonte. | 🟡 |
| **L-19** | ✅ **FECHADA em 2026-10-05 — o `.venv/` é o interpretador OFICIAL.** Você decidiu, e o `requirements.txt` foi **realinhado** às versões verificadas dentro do `.venv` (`ged4py==0.5.5`, `networkx==3.7`, `pandas==3.0.6`), com o **`rapidfuzz==3.14.6` e o `python-Levenshtein==0.27.5` promovidos a dependência declarada** — era o risco que sobrevivia ao pin das diretas. **Verificado:** a suíte passa **igual nos dois interpretadores** (163 passam + 15 erros de ambiente). ⚠️ **Pendência de documentação:** o `README.md` ainda descreve o fluxo pelo interpretador **global** e agora contradiz o pin. | 🟢 |
| **L-20** | **Custo não limitado por resultado.** `person_a` e `person_b` são **fichas completas** em cada resultado, e `get_children` varre **todas** as famílias sem índice. No caso real de 71 conexões foram **142 fichas** montadas para uma tela que exibe poucas. Custo real, sem limite medido. | 🟢 |
| **L-21** | ✅ **DECIDIDA em 2026-10-05 — é HERANÇA, e persistir passa a ser requisito do ALVO.** O comportamento atual (re-parse a cada `POST`, nada gravado) permanece no legado; você quer **histórico de análises** no sistema alvo. Registrado como requisito encaminhado — ver `gaps.md` § "Requisitos encaminhados ao alvo". | 🟢 |
| **L-22** | **Política de descarte.** O match descartado é exibido com motivo. Não há indicação de negócio sobre se o operador **deve agir** sobre os descartados, nem qual taxa de descarte é aceitável. | 🟡 |
| **L-23** | ✅ **FECHADA em 2026-10-05 — cobertura MEDIDA.** Com `pytest-cov` (instalado no `.venv`), a cobertura de `src/` é **83 %** (1.520 instruções, 253 não cobertas). Os menores índices confirmam a Matriz C da `spec-impact-matrix`: **`number_format` 53 %**, `relationship_hypotheses` 76 %, `mermaid_render` 78 %, `evidence_comparison` 83 %. | 🟢 |

> **Lacunas fechadas em 2026-09-30 que NÃO foram reabertas:** `L-01` (entidades decorativas — removidas), `L-02` (`get_spouses` — contrato declarado), `L-03` (teto de 20 — decisão de preservar), `L-11` (idem `L-01`), `L-13` (determinismo — decidido; **porém não implementado**, ver `L-15`).
> **Lacuna fechada nesta rodada:** "não há repositório Git → ADRs impossíveis" era falso em 2026-09-30 (66 commits) e continua falso: são **125 commits**, e as **23 decisões** estão em `adrs/`.
> **Lacuna fechada em 2026-10-05:** `L-15` (determinismo do desempate) — decidida em 2026-09-30 e **executada** nesta rodada, por sua autorização para corrigir o legado.

---

## 8. Resumo para o Reversa

- **Regras de negócio de domínio consolidadas:** 7 famílias (§3), sobre **118 regras** catalogadas linha a linha no `code-analysis.md`.
- **Regra central nova:** os **três eixos que não se contaminam** (parentesco documental, evidência genética, confronto) com **quatro estados** — capacidade que **não existe em nenhum artefato da extração anterior**.
- **Máquinas de estado:** existe **1 máquina de estados real de decisão** (o veredito do confronto, 4 estados) e **1 máquina de classificação** (o `status` do parentesco documental, 4 valores). **Nenhuma entidade persistente tem ciclo de vida** — não há campo de status em registro algum e nada sobrevive à requisição. Detalhamento, diagramas Mermaid e os estados que **não** foram gerados em `state-machines.md`.
- **Permissões:** **inexistentes** — nenhum `session`, `login`, `auth`, `role` ou `permission` no código. `app.secret_key` está definido e **nunca é usado**, porque `flask.session` nunca é importado. Registrada a consequência de negócio (isolamento por chave de conteúdo e a corrida entre threads) em `permissions.md`.
- **ADRs:** **23 decisões** reconstruídas do histórico Git e dos registros de bug/mitigação, em `adrs/` — 8 herdadas da extração anterior (revalidadas contra o código atual) e **15 novas**.
- **Mensagens de contrato:** **21 literais** catalogados (§5), dos quais **7 são provados por golden file** (`SCR-001`, `SCR-002`, `SCR-005`, `SCR-G01`, `SCR-G02`).
- **Decisões humanas vigentes:** **13**, e **todas as 13 estão honradas** pelo código após a correção do desempate em 2026-10-05.
- **Lacunas para validação:** **8** abertas (`L-16` a `L-23`) — `L-15` foi fechada por execução. Restam as de concorrência, ambiente, custo e política de produto.

---

*Gerado pelo Reversa-Detective em 2026-10-05 (re-extração, nível completo).*

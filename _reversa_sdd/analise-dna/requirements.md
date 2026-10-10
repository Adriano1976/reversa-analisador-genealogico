# Unit `analise-dna` — Requisitos

> Unit do tipo **endpoint** — cobre `POST /` com `action=dna_analysis`.
> Spec gerada pelo Reversa-Writer na re-extração de **2026-10-10** (nível **Completo**).
> **Substitui a versão de 2026-10-05**, que descrevia **62** regras, um núcleo sem fronteira de aplicação, `ValueError` como único erro tipado e **nenhuma persistência**. Snapshot: `.reversa/snapshots/2026-10-10-pre-reextracao/analise-dna/`
> Fontes: `code-analysis.md` §4 (95 regras `BR-D-01`..`BR-D-95`), `flowcharts/analise-dna.md`, `data-dictionary.md` §6 e §8, `domain.md` §2, `state-machines.md` §3 e §4, `erd-complete.md` Diagrama E, `adrs/` (13, 14, 15, 16, 19, 20, 22, 23, 25, 26, 27, 32, 33)
> Evidência de execução (2026-10-10): as constantes desta unit foram **medidas** por importação — `SCP40_ROWS` = 27, `SCP40_NOT_PUBLISHED` = 6, `CAUSAS_POSSIVEIS` = 12, `CAUSAS_POSSIVEL` = **8**, `SEM_KIT` = `' SEM-KIT'` (com espaço), `LIMITE_SEGMENTO_FRACO` = `15.0`.
> Escala de confiança: 🟢 CONFIRMADO | 🟡 INFERIDO | 🔴 LACUNA

---

## Visão Geral

Cruza a árvore GEDCOM carregada com um CSV de matches de DNA e responde **três perguntas separadas**, sem nunca misturá-las: *o que o GEDCOM afirma sobre o parentesco*, *o que o arquivo de DNA informa* e *as duas coisas são compatíveis entre si*. 🟢

É a **unit de maior complexidade do sistema**: **95 regras** de negócio, **13 arquivos**, e a única cuja saída é um **veredito** (`COMPATIVEL` / `POSSIVEL` / `CONFLITANTE` / `INCONCLUSIVO`). A regra que a define é negativa: **o cM nunca é usado sozinho para afirmar parentesco**. 🟢

> ⚠️ **O que mudou desde 2026-10-05.** A unit ganhou uma **fronteira de aplicação** (`application/dna_analysis.py` + `application/traducao.py` + a porta `RegistroDeAnalises`, `ADR-25`), **persistência Postgres opcional** que nunca pode bloquear o resultado (`ADR-27`), e **projeção pura** do resultado para o payload da porta (`ADR-33`). Os erros deixaram de ser `ValueError` genérico: são **cinco exceções de domínio irmãs** com tabela de tradução. O CSV passou a poder vir da **lista** (com precedência sobre o arquivo enviado) e a **substituir a versão anterior** no reenvio. E o **determinismo do desempate** — que era `RF-26` e divergência viva — está **implementado e congelado por teste** (`BR-D-63`).

## Responsabilidades

- Ler o CSV de matches de forma **tolerante** (encoding, separador, preâmbulo, linha torta) e **reportar** o que foi descartado. 🟢
- Detectar as colunas por **papel**, e não por nome fixo. 🟢
- Agregar os segmentos de um mesmo match **somando cM, sem arredondar**. 🟢
- Construir a **evidência genética por (nome, kit)**, sem nunca somar kits diferentes. 🟢
- Construir os índices do GEDCOM e decidir a **aceitação** de cada candidato por score difuso com filtros anti-falso-positivo. 🟢
- Obter o **parentesco documental** de cada candidato e escolher aquele que tem caminho. 🟢
- Traduzir o cM em **lista** de possibilidades pela tabela publicada do Shared cM Project 4.0. 🟢
- Produzir o **confronto** entre documento e genética, com um dos quatro estados e o porquê. 🟢
- Ordenar e apresentar os resultados, mais a lista auditável dos descartes. 🟢
- **Projetar** o resultado no payload da porta, de forma **pura**, sem recalcular nada. 🟢 *(novo)*
- **Registrar o histórico** quando houver registro e referência, **sem que a persistência possa impedir o resultado de chegar à tela**. 🟢 *(novo)*
- **Traduzir** exceção de domínio em literal de tela e status. 🟢 *(novo)*

## Regras de Negócio

### Entrada e leitura tolerante

- A raiz é resolvida por **substring do nome, sem diferenciar maiúsculas**; usa o **primeiro** registro e **avisa** quantos e quais são os homônimos (`BR-D-36`, `BR-D-37`). 🟢
- O CSV é lido primeiro como `utf-8`; na falha, como `latin-1` (`BR-D-01`). **O fallback de encoding não é interceptado por nenhuma exceção de domínio.** 🟢
- O separador é decidido pelo cabeçalho entre vírgula, ponto e vírgula, TAB e barra vertical: vence a maior contagem, e **no empate vence a vírgula** (`BR-D-02`). **Nunca `csv.Sniffer`**, que erra em arquivo de uma coluna. 🟢
- O cabeçalho é localizado quando há preâmbulo, com **três guardas** (`BR-D-03`): frequência ≥ 2 do número modal de campos, primeira linha divergente e posição dentro das **10** primeiras linhas. 🟢
- Linhas antes do cabeçalho são **preâmbulo**, reportado à parte (`BR-D-04`); linha com número de campos diferente **não derruba a análise** — o arquivo é relido descartando-a, e a tela **publica a contagem e os números de linha** (`BR-D-05`). 🟢
- Sem nenhuma tentativa utilizável, o erro é `CsvIlegivel`, em português, **listando as tentativas** (`BR-D-06`). 🟢
- Os nomes das colunas são normalizados com `strip` (`BR-D-07`). 🟢
- Colunas por papel (`BR-D-08`, `BR-D-09`, `BR-D-10`): nome = `Name`/`MatchedName`/`Nome`; cM = `cM`/`TotalCM`/`Total cM`; ID de match = a **primeira** com > 30 % dos valores casando `[A-Z]{2}\d{7}`; e-mail = a **última** cujo nome contém `mail`. 🟢
- A agregação legada soma cM por `nome normalizado + cauda`, com a cauda sendo id, e-mail ou nada (`BR-D-11`). 🟢

### Evidência genética

- A chave de evidência é **(nome, kit)** — duas linhas com o mesmo nome e kits diferentes são **duas** evidências (`BR-D-12`). 🟢
- Sem coluna de kit, o **e-mail** assume o papel; sem ambos, a chave é a sentinela `" SEM-KIT"` e sai o aviso `kit_ausente` (`BR-D-13`). 🟢 **O espaço à esquerda é a defesa**: `_clean` faz `strip` em todo valor do CSV, e era assim que o literal sem espaço colidia com um kit de verdade (`E-03`). 🟢
- **Nenhum total é somado entre kits** (`BR-D-14`). Com mais de um kit e sem saber qual é a pessoa do GEDCOM, `totals.cm` é **`None`** — é o número honesto, e somar laboratórios produziria um valor que nenhuma das duas fontes sustenta (`BR-D-19`). 🟢
- **O cM acumulado não é arredondado** (`BR-D-15`); o contrato está congelado em `tests/test_formatacao_cm.py` (`19.200000000000003` é o valor esperado). Arredondar na acumulação quebraria a paridade. 🟢
- A coluna de kit é a que tem nome casando `kit|gedmatch|teste|test` com > 50 % em `[A-Z]{1,3}\d{4,8}`; senão, a que tem > 30 % em `[A-Z]{2}\d{7}` (`BR-D-16`). 🟢
- Maior segmento abaixo de **15 cM** marca a evidência como fraca e gera o aviso `segmento_fraco` (`BR-D-17`). **O limite é heurística do projeto**, não da fonte. 🟢
- Segmentos são ordenados por cM decrescente; cromossomos, por tamanho e depois por valor (`BR-D-18`). 🟢
- Sem evidência genética, `available: False` com o aviso `sem_evidencia` (`BR-D-20`). 🟢

### Possibilidades a partir do cM

- cM vira **lista** de possibilidades pelo SCP 4.0; **nunca um parentesco único** (`BR-D-21`). 🟢
- As candidatas são ordenadas por distância da média e, em empate, pelo nome em inglês (`BR-D-22`). 🟢
- A confiança da lista é **heurística do projeto** (`BR-D-23`): 0 → `indeterminada`; 1 e 2–3 → `baixa`; 4–6 e > 6 → `muito baixa`. A fonte **não publica mediana** — existe `average`, não `median`. 🟡
- Valor sem cobertura publicada devolve **lista vazia** e a leitura de que **isso não descarta parentesco** (`BR-D-24`). 🟢
- **Seis relações não são publicadas na 4.0** e não recebem número inventado (`BR-D-25`): `1C4R`, `1C5R`, `1C6R`, `3C2R` e os bisavôs distantes — justamente as mais distantes, que é onde o caso real deste repositório cai. 🔴
- Sem faixa publicada para a relação exata, a janela é a **envoltória** das publicadas com o mesmo número de meioses (`BR-D-26`); sem nenhuma, não há janela. 🟢
- A coluna "Range" da fonte **exclui 1 % dos envios**, e a janela do confronto herda essa limitação. 🟡

### Parentesco documental e confronto

- O parentesco documental **nunca lê cM**; a evidência genética **não conhece o GEDCOM**. 🟢
- O DNA **não altera** o parentesco documental: um conflito vira **aviso e rol de causas**, nunca reescrita de vínculo. 🟢
- O confronto devolve **sempre** um de quatro estados, cada um com mensagem própria (`BR-D-27`). 🟢
- cM dentro da janela → `COMPATIVEL` (`BR-D-28`); fora → `POSSIVEL` **apenas** quando alguma relação publicada que contém o valor tem faixa que **se sobrepõe** à janela (`BR-D-29`); caso contrário → `CONFLITANTE`. 🟢
- **Distância em meioses não é critério**, e o código registra por quê: irmãos (1613–3488) e primos de 1º grau com 1 remoção (102–980) estão a **uma** meiosa e **não se sobrepõem**. 🟢
- `INCONCLUSIVO` em quatro situações (`BR-D-30`..`BR-D-33`): sem evidência genética; com DNA e **sem caminho documental** (nenhum caminho é inventado a partir do DNA); **identidade ambígua** (listando os homônimos); e **sem faixa publicada**, nem por meioses. 🟢
- Com mais de um kit, o estado final é o **mais conservador**: `CONFLITANTE > POSSIVEL > COMPATIVEL > INCONCLUSIVO` (`BR-D-34`). 🟢 **`INCONCLUSIVO` é o último da ordem**: um kit sem cM utilizável **não** rebaixa o resultado quando outro kit é `COMPATIVEL`. 🟡
- `CONFLITANTE` recebe o rol de **12** causas; `POSSIVEL`, um subconjunto de **8** (`BR-D-35`). 🟢 ⚠️ **Correção medida nesta rodada:** o catálogo do Arqueólogo (`code-analysis.md` §4.4 e `modules.json`) afirma **9** para o subconjunto; a medição por importação dá **8** (`[0] + [3:8] + [10:]` = 1 + 5 + 2). Vale **8**.
- Sem endogamia e colapso de pedigree **corrigidos**: o cM lido é um **teto otimista** nesses casos; a fonte declara a limitação e o confronto lista as duas entre as causas, **mas não as detecta**. 🔴

### Matching difuso

- O matching exato é por `norm_name` sobre o índice de nomes do GEDCOM (`BR-D-44`); sem acerto exato, busca por **sobrenome**; sem nenhum, por **prefixo de 3 letras** (`BR-D-45`). 🟢
- **Score** = `0.55·token_sort + 0.25·partial + 0.20·given + (8·interseção − 4·comuns)`, em 2 casas (`BR-D-46`). **Pesos herdados do legado, não alterados.** 🟢
- Melhor candidato: mais sobrenomes em comum → melhor prenome → melhor score (`BR-D-47`) → **e, no empate exato dos três, o menor `xref_id`** (`BR-D-63`). 🟢 **É o critério que fecha a divergência de determinismo**: sem ele o vencedor caía na ordem de iteração de um `set`, medida como variável a cada `PYTHONHASHSEED`.
- **Filtro anti-falso-positivo** (`BR-D-48`): ambos os lados com sobrenome, interseção zero e sem acerto de sufixo → **rejeita**, com o motivo registrado. 🟢
- **Jaccard com prefixo suave** (`BR-D-49`): limiar 0,50 com ≥ 2 sobrenomes; cai para **0,33 apenas** quando `cM ≥ 150` **e** o prenome não é genérico. 🟢
  - 🟡 **O número `0,33` é heurística, sem medição de calibração.** Confirmado por você em 2026-10-05: foi um **chute que funcionou na prática**. Continua valendo como está.
- **Interseção mínima adaptativa** (`BR-D-50`): prenome genérico exige **≥ 2** sobrenomes em comum; não genérico, **≥ 1**. 🟢
- **Cinco ramos de aceitação alternativos**, avaliados em ordem, mais o ramo de prefixo (`BR-D-51`, `BR-D-52`); o primeiro verdadeiro vence. 🟢
- **Tokens do meio ausentes** no GEDCOM exigem `score ≥ 96` e `given ≥ 92`, e o motivo da recusa é registrado (`BR-D-53`). 🟢
- **O cM não decide a aceitação.** Ele só influencia o limiar de Jaccard; há teste de caracterização que congela isso. 🟢
- Os limiares são **literais dentro dos ramos**, e não constantes nomeadas — decisão deliberada (`ADR-08`), com o custo de não haver ponto único de mudança. 🟡

### Vocabulário de nomes

- `norm_name` (`BR-D-54`): limpa mojibake, decompõe NFKD, remove diacríticos, troca `/` e pontuação por espaço, minúsculas, colapsa espaços. 🟢
- `STOP_WORDS` = `de`, `da`, `do`, `das`, `dos`, `e` (`BR-D-55`). 🟢
- `GENERIC_GIVENS` = **20** prenomes comuns, com variantes acentuadas (`BR-D-56`). 🟢
- `SURNAME_SUFFIXES` = `filho`, `neto`, `junior`, `júnior`, `sobrinho` (`BR-D-57`). 🟢
- `COMMON_SURNAMES` = **16** entradas com `souza` **duplicada** (15 efetivas) (`BR-D-58`). 🟡 *(duplicação inofensiva em conjunto, mas é sinal de descuido no vocabulário)*
- `SURNAME_EQUIV` unifica `netto→neto` e `gouvea`/`gouvêa`/`gouvéia→gouveia` (`BR-D-59`). 🟢
- O prenome é o **primeiro** token que não é stop word nem genérico; os sobrenomes são os **últimos 3** tokens úteis, sem genéricos, com equivalências; sufixos são separados (`BR-D-60`). 🟢
- `soft_prefix_jaccard` compara prefixos de 4 quando algum lado tem token curto (≤ 4) ou terminando em ponto (`BR-D-61`). 🟢

### Apresentação

- A ordem é **documental primeiro, cM decrescente depois** (`BR-D-41`), e o código declara que **não é ordem de confiança**. Justificativa medida: das **71 conexões** do GEDCOM real, **64 não têm caminho**. 🟢
- Mensagem final: `"N conexões encontradas. M descartadas."` (`BR-D-42`); **sem nenhum resultado**, os avisos do arquivo são anexados à mensagem, porque não há cartão onde apareçam (`BR-D-43`). 🟢
- As **observações** de um resultado são deduplicadas preservando a ordem: documental → genética → confronto → avisos da raiz e do arquivo (`BR-D-65`). 🟢
- O **diagrama** só é montado quando há caminho documental; sem caminho, o campo é `None` (`BR-D-66`), e o resolvedor é montado **uma vez por análise**, fora do laço de evidências (`BR-D-64`). 🟢
- Os quatro estados são **também nomes de classe CSS** no template (`badge estado-{{ status }}`), e **não há teste** que compare o nome do estado com a folha de estilo. 🟡

### Fronteira: projeção, erro tipado e persistência *(tudo novo em 2026-10-10)*

- `projetar_analise` é **pura**: não reordena, não recalcula cM, não formata e não chama o núcleo (`BR-D-75`). É pública para poder ser exercitada **sem banco**. 🟢
- A ficha **completa** vence a identificação ao juntar pessoas, e uma identificação sem nome cede lugar a uma com nome (`BR-D-68`); ficha sem `id` é descartada, porque **não há pessoa sem xref** (`BR-D-69`). 🟢
- O papel de cada nó do caminho é **derivado**, com corte no ancestral comum; sem MRCA, o corte cai no **penúltimo** nó (`BR-D-70`). **`afinidade` nunca é atribuída** por esta projeção (`BR-D-71`): quem atribui é `busca-caminho`. 🟢
- O pareamento entre metadados de kit e veredito é **por índice**, e um kit sem avaliação herda o estado final com `status_note` nulo (`BR-D-72`). 🟢
- A raiz do retrato é `documentary.person_a.id` da **primeira** conexão (`BR-D-73`); `ordinal` é a posição na ordem **apresentada**, com defaults `INCONCLUSIVO`, `not_found` e string vazia (`BR-D-74`). 🟢
- O motivo do descarte é transportado como **texto**, sem virar código (`BR-D-76`); `match_file_ref` é o **nome do arquivo armazenado**, derivado do caminho do CSV (`BR-D-77`). 🟢
- **Sem registro ou sem referência da árvore, a análise não é registrada** — é o estado desabilitado (`BR-D-78`), e sem `DATABASE_URL` a borda monta registrador **nulo** (`BR-D-79`). 🟢
- A gravação acontece **depois** do núcleo, e **nenhum módulo de `core/` conhece o registro** (`BR-D-80`). 🟢
- **Exceção na projeção ou na gravação vira AVISO**, e o resultado chega à tela (`BR-D-81`): uma falha aqui seria a persistência bloqueando a análise, exatamente o que ela não pode. 🟢
- O adaptador faz **import preguiçoso** de `psycopg2`, e driver ausente → **aviso**, nunca exceção (`BR-D-82`); **nada acontece na construção** — não abre conexão, não valida a URL, não toca a rede (`BR-D-83`). 🟢
- **Uma conexão por análise** (sem pool) e **uma transação por análise**; o `finally` fecha a conexão (`BR-D-84`). 🟢
- A ordem de escrita respeita as **chaves estrangeiras** (`BR-D-85`): `dna_analysis` → `analysis_person` → `match_result` → `match_kit` / `match_path_node` → `skipped_match`. 🟢
- `is_affinity_anchor` é **sempre** `FALSE` (`BR-D-86`); `dono` vira a coluna `owner_id`, e **nenhuma consulta filtra por ele** (`BR-D-87`). 🟢
- `dono` está na assinatura do caso de uso e **não participa de decisão nenhuma** (`BR-D-67`). 🟢
- `aviso_de_persistencia` nulo significa "nada a avisar", e a tela **não renderiza nada** (`BR-D-88`). 🟢
- A **referência de CSV escolhida na lista tem precedência** sobre o arquivo enviado, e o campo é **opcional** (`BR-D-89`); referência que não resolve → `Erro: Arquivo 'X' não existe mais.` (`BR-D-90`). 🟢
- O CSV passa pela **mesma porta** do GEDCOM com `tipo="csv"` — **sem validação de conteúdo** — e pela **mesma regra de reenvio** (`BR-D-91`); o aviso de substituição é **acrescentado** à mensagem do resultado, nunca a substitui (`BR-D-92`). 🟢
- Erro de domínio → **tabela de tradução** (mensagem + status); falha inesperada → `Ocorreu um erro: {e}` com `success=False` (`BR-D-93`). 🟢
- As **cinco exceções de domínio são irmãs**, não uma cadeia; `ErroDeDominio` herda de `ValueError` para preservar quatro asserções existentes da suíte (`BR-D-94`). 🟢 Consequência declarada: nenhum `except ValueError` pode distinguir casos pela **mensagem** — a distinção é sempre pelo **tipo**. 🟢
- O **status HTTP** da tradução **não tem consumidor** nesta onda: vale só para a API nova, que não existe (`BR-D-95`). 🟢

### Compatibilidade declarada

- `cm_estimator` (as 9 faixas escritas à mão, `BR-D-62`) **está fora do fluxo e da interface**. Continua existindo porque a suíte e o harness de paridade o exercitam, o próprio módulo declara que não deve ser usado em código novo, e a superfície que o reexportava para `core/dna_analysis` **saiu** nesta rodada. 🟢

## Requisitos Funcionais

| ID | Requisito | Prioridade | Critério de Aceite |
| --- | --- | --- | --- |
| RF-01 | Receber `POST` com `action=dna_analysis`, exigindo `gedcom_filename` e `root_name`, e **ou** o arquivo `matches_csv` **ou** a referência `matches_csv_filename` | Must | Sem CSV e sem referência → `"Por favor, carregue o arquivo CSV de matches."`, preservando `gedcom_filename` e `all_names` na tela 🟢 |
| RF-02 | Dar **precedência** à referência de CSV escolhida na lista, mantendo o campo **opcional** | Must | Com os dois presentes, o CSV da lista é usado; sem a referência, o caminho é exatamente o de antes 🟢 |
| RF-03 | Responder `Erro: Arquivo 'X' não existe mais.` quando a referência de CSV não resolve | Must | A tela continua utilizável, com `gedcom_filename` e `all_names` 🟢 |
| RF-04 | Gravar o CSV pela **mesma porta** do GEDCOM, com `tipo="csv"` e **sem validação de conteúdo** | Must | Um CSV que não é lista de matches é gravado e falha depois, na leitura, com erro acionável 🟢 |
| RF-05 | Aplicar ao CSV a **mesma regra de reenvio** do GEDCOM e **acrescentar** o aviso de substituição à mensagem do resultado | Must | Reenviar um CSV de conteúdo novo deixa **uma** linha na aba de DNA; o aviso vem depois da mensagem do resultado, sem substituí-la 🟢 |
| RF-06 | Ler o CSV tolerando encoding (`utf-8` → `latin-1`), separador (`,` `;` TAB `\|`) e preâmbulo | Must | CSV em `latin-1`, com `;` e 3 linhas de título é lido com as colunas corretas; o separador nunca vem do `csv.Sniffer` 🟢 |
| RF-07 | Localizar o cabeçalho com as **três guardas**, sem perder a primeira linha de dados de um arquivo sem cabeçalho | Must | Arquivo sem cabeçalho não perde a linha 1; arquivo que não é tabela não elege cabeçalho falso 🟢 |
| RF-08 | Descartar linhas irregulares **publicando** contagem e números de linha | Must | A tela informa quantas linhas e quais foram descartadas, e sugere conferir o arquivo de origem 🟢 |
| RF-09 | Levantar `CsvIlegivel` quando nenhuma tentativa produz tabela utilizável | Must | Mensagem em português **listando as tentativas feitas** 🟢 |
| RF-10 | Normalizar os nomes das colunas com `strip` e detectá-las **por papel** | Must | Nome em `Name`/`MatchedName`/`Nome`; cM em `cM`/`TotalCM`/`Total cM`; ID pela primeira com > 30 % em `[A-Z]{2}\d{7}`; e-mail pela **última** com `mail` 🟢 |
| RF-11 | Agregar cM por `nome normalizado + cauda`, com a cauda sendo id, e-mail ou nada | Must | Um registro por chave, com o cM somado 🟢 |
| RF-12 | Construir evidência por **(nome, kit)**, com o e-mail assumindo o papel de kit quando não há coluna de kit | Must | Mesmo nome em dois kits produz **duas** evidências; sem kit e sem e-mail, a sentinela `" SEM-KIT"` e o aviso `kit_ausente` 🟢 |
| RF-13 | Nunca somar kits diferentes, e avisar `multiplos_kits` | Must | `totals.cm` é `None` quando há mais de um kit e não se sabe qual é a pessoa do GEDCOM 🟢 |
| RF-14 | **Não arredondar** o cM acumulado | Must | `tests/test_formatacao_cm.py` congela `19.200000000000003`; o arredondamento é só de apresentação 🟢 |
| RF-15 | Detectar as colunas de segmento/kit, marcar `segmento_fraco` abaixo de 15 cM e ordenar segmentos e cromossomos | Should | Aviso `segmento_fraco` presente quando o maior segmento é menor que 15 cM; o limite é declarado heurística do projeto 🟢 |
| RF-16 | Reunir os kits **sem somar** e declarar ausência de evidência | Must | Sem evidência genética, `available: False` com aviso `sem_evidencia` 🟢 |
| RF-17 | Traduzir o cM em **lista** de possibilidades pela tabela do SCP 4.0, ordenada por distância da média | Must | Sempre lista, inclusive vazia; 27 relações publicadas; empate pelo nome em inglês 🟢 |
| RF-18 | Usar a **envoltória por meioses** quando a relação exata não for publicada | Must | As **6** relações não publicadas não recebem número inventado; sem nenhuma publicada com o mesmo número de meioses, não há janela 🟢 |
| RF-19 | Produzir o confronto com um dos **quatro estados**, sempre com o porquê | Must | `method`, `expected_range`, `detail` e `per_kit` preenchidos quando há janela; mensagem própria por estado 🟢 |
| RF-20 | Agregar múltiplos kits pelo **mais conservador** e registrar o estado por kit | Must | Um kit `CONFLITANTE` entre cinco torna o resultado `CONFLITANTE`, com a nota por kit 🟢 |
| RF-21 | Anexar o rol de causas: **12** em `CONFLITANTE`, **8** em `POSSIVEL` | Must | Nenhuma causa vazia; o total é **8**, medido — o catálogo diz 9 e está errado 🟢 |
| RF-22 | Resolver a raiz por substring, usando o **primeiro** registro e **avisando** a ambiguidade | Must | Raiz inexistente → `PessoaNaoEncontrada`; ambígua → aviso com a contagem e os ids 🟢 |
| RF-23 | Alimentar o matching com o cM **do kit**, nunca a soma, e escolher o **primeiro candidato com caminho documental** | Must | Resultado com `documentary`, `text_path` e `mermaid_data`; sem nenhum com caminho, vence o primeiro da lista 🟢 |
| RF-24 | Calcular o dossiê de homônimos **uma vez por nome** e o parentesco **uma vez por pessoa** | Should | O laço não revarre os ~35 mil nomes nem recalcula o mesmo par 🟢 |
| RF-25 | Ordenar com **documental primeiro**, depois cM decrescente | Must | Resultados com caminho aparecem antes dos que só têm DNA; a ordem declarada **não** é de confiança 🟢 |
| RF-26 | Emitir a mensagem final `"N conexões encontradas. M descartadas."` | Must | Contagens corretas; **sem resultados**, os avisos do arquivo são anexados 🟢 |
| RF-27 | Listar os descartes com o motivo específico, **orientando a ação** do operador | Must | Cada descarte traz `csv_name`, `kit`, `cm` e `motivo` — **nunca vazio** 🟢 |
| RF-28 | Construir os índices do GEDCOM e o cache de atributos normalizados | Must | `ged_index`, `surname_index` e `features[pid]` populados uma vez por análise 🟢 |
| RF-29 | Aplicar score, desempate em **quatro** níveis e os filtros de aceitação | Must | Score conforme a fórmula; desempate inter → given → score → **menor `xref_id`**; decisão idêntica à congelada pelos testes de caracterização 🟢 |
| RF-30 | Aplicar as regras de vocabulário de nomes | Must | `norm_name`, `split_name_pt`, `surname_core_tokens` e `soft_prefix_jaccard` conforme as regras `BR-D-54`..`BR-D-61` 🟢 |
| RF-31 | Projetar o resultado no payload da porta de forma **pura**, com as regras de junção, de papel do caminho e de pareamento por índice | Must | `projetar_analise` roda **sem banco** e sem `DATABASE_URL`; nenhum kit troca de cM com outro 🟢 |
| RF-32 | Registrar o histórico **sem poder bloquear** o resultado | Must | Sem registro ou sem referência da árvore, não registra e a tela não muda; exceção vira aviso `Histórico não registrado: …` 🟢 |
| RF-33 | Traduzir exceção de domínio em literal de tela, e falha inesperada em `Ocorreu um erro: {e}` | Must | As quatro molduras medidas são preservadas; `GedcomNaoSuportado` mantém a frase fixa 🟢 |
| RF-34 | Declarar `cm_estimator` como **legado fora do fluxo** | Should | O módulo não é importado por nenhum caminho de produção nem pela interface; `cM ≤ 0` ou não numérico devolvem lista vazia 🟢 |

## Requisitos Não Funcionais

| Tipo | Requisito inferido | Evidência no código | Confiança |
|------|--------------------|---------------------|-----------|
| Performance | O cache de atributos normalizados e o resolvedor de diagrama são montados **uma vez por análise**, fora do laço de candidatos; antes, o laço renormalizava o mesmo nome ~7 vezes por candidato | `matching.py:27-59`, `core/dna_analysis.py:202-204` | 🟢 |
| Performance | **Sem cache entre requisições**: os índices do GEDCOM inteiro são reconstruídos a cada `POST` | `core/dna_analysis.py:180` | 🟢 |
| Reprodutibilidade | O cM acumulado **não é arredondado**; o contrato está congelado em teste, porque a paridade exige igualdade exata | `genetic_evidence.py`; `tests/test_formatacao_cm.py` | 🟢 |
| Reprodutibilidade | O desempate do ramo difuso **é determinístico**: o quarto critério é o menor `xref_id`, e a caracterização o congela nas duas direções | `matching.py:116-125`; `tests/test_characterization_matching.py` | 🟢 |
| Confiabilidade | `thefuzz` delega a `RapidFuzz`/`python-Levenshtein`; trocar a versão de qualquer uma **altera o resultado do matching** sem mudar uma linha do projeto | `requirements.txt`; `RISK-006` | 🟢 |
| Confiabilidade | Ausência ou divergência de faixa publicada **não** vira veredito: o confronto responde `INCONCLUSIVO` | `evidence_comparison.py:203-208` | 🟢 |
| Disponibilidade | A persistência **nunca** impede o resultado: import preguiçoso do driver, nada na construção, e falha na projeção ou na gravação vira aviso | `ports/adaptadores.py:243-297`, `application/dna_analysis.py:271-284` | 🟢 |
| Segurança | O CSV gravado **não passa por validação de conteúdo** — só a forma do nome é validada. É a **dívida #10**, preservada de propósito | `app.py:459-461`, `ports/adaptadores.py:76` | 🟢 |
| Privacidade | O histórico persiste **dado pessoal de pessoas vivas** (xref, nome, sexo, nascimento, local, falecimento) **sem retenção, expurgo nem consentimento**. **DECISÃO HUMANA DE 2026-10-10: o uso do legado com dado de TERCEIROS fica PROIBIDO — o sistema é ferramenta da própria árvore do operador.** Retenção, expurgo e consentimento passam a **requisito do sistema alvo** (`TM-04`), e não a trabalho desta rodada | `ports/adaptadores.py:320-330`; `init.sql` | 🔴 |
| Observabilidade | **Nenhum log, métrica ou trace.** A única visibilidade do motivo de um match não aparecer é a lista de descartados. O aviso de persistência chega à tela, mas não ao log | — | 🟢 |
| Manutenibilidade | Os limiares de aceitação são **literais dentro dos ramos**, e não constantes nomeadas — decisão deliberada (`ADR-08`) | `matching.py` | 🟡 |
| Internacionalização | Todas as mensagens ao operador são literais em português | `traducao.py`, `evidence_comparison.py`, `csv_ingest.py` | 🟢 |

> Inferido a partir do código. **Não** há timeout, retry, circuit breaker, fila ou cache distribuído — as linhas correspondentes foram omitidas por falta de evidência.

## Critérios de Aceitação

```gherkin
Dado um GEDCOM carregado e um CSV válido
Quando o operador submete a análise com um root_name existente
Então cada conexão traz parentesco documental, evidência genética, possibilidades e confronto
E o resultado traz um dos quatro estados, com o porquê
E a mensagem final informa quantas conexões foram encontradas e quantas descartadas

Dado um CSV em que o mesmo nome aparece em dois kits diferentes
Quando a evidência genética é construída
Então existem DUAS evidências, uma por kit
E totals.cm é None, porque não se sabe qual kit é a pessoa do GEDCOM
E nenhum total é somado entre os kits

Dado um match cujo maior segmento é de 12 cM
Quando a evidência é construída
Então a evidência é marcada como segmento fraco
E o aviso "segmento_fraco" é emitido

Dado um CSV com separador ponto e vírgula, em latin-1, com 3 linhas de título
Quando a análise é executada
Então o separador é detectado como ponto e vírgula
E o encoding usado é latin-1
E o cabeçalho é localizado na linha 4
E a tela informa as linhas de preâmbulo ignoradas

Dado um cM fora da janela documental, sem nenhuma relação publicada que se sobreponha a ela
Quando o confronto é executado
Então o estado é CONFLITANTE
E o rol completo de 12 causas é apresentado

Dado um cM fora da janela, mas alguma relação publicada que contém o valor se sobrepõe à janela
Quando o confronto é executado
Então o estado é POSSIVEL
E o subconjunto de 8 causas é apresentado

Dado um match sem nenhuma evidência genética utilizável
Quando o confronto é executado
Então o estado é INCONCLUSIVO
E o texto registra que o parentesco documental continua valendo por si, sem DNA para confrontar

Dado um match com identidade ambígua no GEDCOM
Quando o confronto é executado
Então o estado é INCONCLUSIVO
E os registros homônimos são listados

Dado um nome de raiz que não existe na árvore
Quando a análise é executada
Então a tela exibe "Ocorreu um erro: Seu nome 'X' não foi encontrado no GEDCOM."
E nenhum resultado parcial é exibido

Dado um CSV que não é lista de matches
Quando a análise é executada
Então a tela exibe um erro acionável dizendo o separador usado e as colunas encontradas
E a aplicação não quebra

Dado um banco de dados indisponível e DATABASE_URL definida
Quando a análise é executada
Então o resultado completo chega à tela
E a faixa avisa "Histórico não registrado: ..." sem impedir a exibição

Dado que o operador escolhe na lista um CSV já armazenado
Quando a análise é executada
Então a referência escolhida tem precedência sobre qualquer arquivo enviado no mesmo formulário
E o aviso de substituição, quando houver, é acrescentado depois da mensagem do resultado
```

## Prioridade (MoSCoW)

| Requisito | MoSCoW | Justificativa |
|-----------|--------|---------------|
| RF-12/RF-13 Evidência por (nome, kit), sem somar kits | **Must** | Somar kits é erro silencioso de dado; sustenta todo o confronto |
| RF-17/RF-18 Possibilidades pela fonte publicada | **Must** | Base da comparação; substitui a tabela escrita à mão |
| RF-19/RF-20/RF-21 Confronto, agregação conservadora e causas | **Must** | É o produto da unit |
| RF-28/RF-29 Matching: índices, score, desempate e filtros | **Must** | Núcleo do casamento de nomes, com 5 ramos interdependentes |
| RF-23 Parentesco documental e escolha do candidato | **Must** | Sem caminho não há resultado |
| RF-06 a RF-11 Leitura tolerante, colunas por papel e agregação | **Must** | Porta de entrada dos dados |
| RF-22 Resolução da raiz com aviso de ambiguidade | **Must** | Sem raiz não há análise |
| RF-25/RF-26 Ordenação e mensagem final | **Must** | Contrato de apresentação |
| RF-27 Auditoria dos descartes | **Must** | Elevada a `Must` em 2026-10-05: a lista é **acionável** — o operador age sobre os motivos |
| RF-31 Projeção pura | **Must** | Sem ela não há histórico; e ela é o que permite testar sem banco |
| RF-32 Registro sem bloquear a tela | **Must** | A persistência é benefício, nunca condição para ver o resultado |
| RF-01 a RF-05 Entrada do CSV: precedência, reenvio e porta | **Must** | É o caminho pelo qual o insumo chega à análise |
| RF-33 Tradução de erro tipado | **Must** | É o que mantém o texto observável igual, agora com a condição tipada |
| RF-15 Segmento fraco | **Should** | Heurística do projeto; não bloqueia o veredito |
| RF-24 Dossiê e parentesco cacheados | **Should** | Desempenho: sem eles a análise fica lenta, mas correta |
| RF-30 Vocabulário de nomes | **Should** | Regras estáveis, exercitadas por testes de caracterização |
| RF-34 `cm_estimator` fora do fluxo | **Should** | Existe só para a suíte e o harness não quebrarem |
| `HARD_MIN` / `GIVEN_MIN` | **Won't** | Nunca existiram na reconstrução; decisão de não implementar (`ADR-08`) |

## Rastreabilidade de Código

| Arquivo | Função / símbolo | Cobertura |
|---------|------------------|-----------|
| `src/application/dna_analysis.py` | `dna_analysis` (caso de uso), `projetar_analise`, `_juntar`, `_ficha`, `_pessoas`, `_papeis_do_caminho`, `_kits`, `_conexao`, `ResultadoDeAnalise` | 🟢 |
| `src/core/dna_analysis.py` | `dna_analysis` (núcleo), `_montar_diagrama`, `_observacoes`, `_ordem` | 🟢 |
| `src/parsers/csv_ingest.py` | `read_csv_with_fallback`, `detectar_separador`, `localizar_cabecalho`, `linhas_irregulares`, `detect_columns`, `aggregate_matches` | 🟢 |
| `src/core/genetic_evidence.py` | `build_genetic_evidence`, `detect_segment_columns`, `evidence_for`, `SEM_KIT`, `LIMITE_SEGMENTO_FRACO` | 🟢 |
| `src/core/relationship_hypotheses.py` | `possible_relationships`, `hypotheses_for_evidence`, `row_for_key`, `rows_by_meioses`, `meioses_window`, `SCP40_ROWS`, `SCP40_NOT_PUBLISHED` | 🟢 |
| `src/core/evidence_comparison.py` | `compare`, `_avaliar_kit`, `_janela_do_documental`, `STATUS_LABEL`, `MENSAGENS`, `CAUSAS_POSSIVEIS`, `CAUSAS_POSSIVEL` | 🟢 |
| `src/core/matching.py` | `build_ged_indexes`, `match_candidates` | 🟢 |
| `src/core/name_normalization.py` | `split_name_pt`, `surname_core_tokens`, `soft_prefix_jaccard`, `STOP_WORDS`, `GENERIC_GIVENS`, `SURNAME_SUFFIXES`, `COMMON_SURNAMES`, `SURNAME_EQUIV` | 🟢 |
| `src/utils/name_keys.py` | `norm_name` | 🟢 |
| `src/core/registro.py` | `get_name`, `ref_id` — **cópia literal do oráculo** | 🟢 |
| `src/core/erros.py` | `ErroDeDominio`, `PessoaNaoEncontrada`, `GedcomNaoSuportado`, `DnaCsvSemColunas`, `CsvIlegivel` | 🟢 |
| `src/application/traducao.py` | `traduzir`, `RespostaDeErro`, `_TRADUTORES` | 🟢 |
| `src/ports/__init__.py` | `RegistroDeAnalises`, `AnaliseParaRegistrar`, `PessoaDaAnalise`, `KitDaAnalise`, `ConexaoDaAnalise`, `DescartadoDaAnalise` | 🟢 |
| `src/ports/adaptadores.py` | `RegistroDeAnalisesPostgres.registrar` / `._escrever` | 🟢 |
| `src/app.py` | ramo `dna_analysis` do `index` | 🟢 |
| `src/core/cm_estimator.py` | `get_relationships_by_cm` — **legado fora do fluxo** | 🟢 |
| `src/core/documentary_relationship.py` | `documentary_relationship`, `homonym_dossier` — usados por esta unit e por `busca-caminho` | 🟢 |
| `init.sql` | 6 tabelas: `dna_analysis`, `analysis_person`, `match_result`, `match_path_node`, `match_kit`, `skipped_match` | 🟢 |
| `tests/test_dna_analysis.py`, `test_characterization_matching.py`, `test_confrontacao_gedcom_dna.py`, `test_formatacao_cm.py`, `test_projecao_da_analise.py`, `test_registro_de_analises.py`, `test_persistencia_desabilitada.py`, `test_persistencia_indisponivel.py`, `test_traducao_de_erros.py`, `test_reenvio_do_csv.py`, `test_campo_de_escolha_do_csv.py` | cobertura do pipeline, da caracterização, do confronto, do contrato de cM, da projeção, do registro e da tradução | 🟢 |

---

*Gerado pelo Reversa-Writer em 2026-10-10 (re-extração). Substitui a versão de 2026-10-05.*

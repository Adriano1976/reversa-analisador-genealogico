# Domínio de Negócio — analisador-genealogico

> Nível de documentação: **Completo** (`state.json` → `doc_level`)
> Re-extração de **2026-10-10**. Substitui o `domain.md` de 2026-10-05, que descrevia o estado global do GEDCOM, três ações de usuário e sete famílias de regras.
> Snapshot da versão substituída: `.reversa/snapshots/2026-10-10-pre-reextracao/domain.md`
> Escala de confiança: 🟢 CONFIRMADO | 🟡 INFERIDO | 🔴 LACUNA
> Artefatos irmãos desta rodada: `adrs/` (36 decisões), `state-machines.md`, `permissions.md`, `code-analysis.md`, `data-dictionary.md`, `flowcharts/`

---

## 1. Glossário de Domínio

| Termo | Definição | Conf. |
| --- | --- | --- |
| **GEDCOM** | Formato padronizado (`.ged`) para troca de árvores genealógicas. Define registros `INDI` (pessoa) e `FAM` (família). | 🟢 |
| **INDI** | Registro de indivíduo, identificado por `xref_id` (ex.: `@I0001@`). `FAMC` referencia a família onde é filho(a); `FAMS` as famílias onde é cônjuge. | 🟢 |
| **FAM** | Registro de família, identificado por `xref_id` (ex.: `@F1@`). Campos `HUSB` (marido), `WIFE` (esposa) e `CHIL` (filhos). | 🟢 |
| **Árvore** | Tupla `(people, families, graph, child_to_family)` devolvida pelo parse. **Desde a feature 005 ela é um VALOR que entra por parâmetro** em todo o núcleo — não há estado de processo. | 🟢 |
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
| **Referência** *(novo)* | O **nome armazenado** completo — `<chave>__<nome visível>`. É o que o formulário devolve e o que o resolvedor aceita. Não é o nome visível, e não é o caminho. | 🟢 |
| **Nome visível** *(novo)* | A parte legível do nome armazenado, com acentos, espaços e a extensão original preservados. É o que a tela **exibe**, e o que decide a aba da lista. | 🟢 |
| **Reenvio** *(novo)* | Envio de um arquivo cujo **nome visível** já existe na pasta. Tem três desfechos: `identico`, `substituido` e `novo` (`RN-17`). | 🟢 |
| **Aposentado** *(novo)* | Arquivo **movido** para `<pasta>/_aposentados/` — sai da lista e continua no disco, inteiro e com o mesmo nome. **Aposentar não é apagar** (`RN-14`). | 🟢 |
| **Item indisponível** *(novo)* | Arquivo que aparece na lista mas não pode ser usado, com o motivo à vista: "sem chave" ou "fora da forma". Ele **não é escondido** (`D-11`). | 🟢 |
| **Dono** *(novo)* | Identidade de quem enviou o dado. Está na assinatura de todas as portas e vira coluna `owner_id` no banco, e **não participa de decisão nenhuma** (`RN-06`, `RN-10`). | 🟢 |
| **Porta** *(novo)* | `Protocol` que o caso de uso consome **por parâmetro**, sem instanciar a implementação concreta. São quatro: `ArmazenamentoDeArquivos`, `CarregadorDeArvores`, `RepositorioDeArvores` (sem implementação) e `RegistroDeAnalises`. | 🟢 |
| **Desfecho** *(novo)* | O que aconteceu, em três valores — `RESULTADO`, `SEM_RESULTADO`, `ERRO_DE_ENTRADA` —, derivado da presença de payload e do indicador de sucesso, e **nunca do texto da mensagem**. | 🟢 |
| **Histórico da análise** *(novo)* | O que a análise concluiu, gravado em PostgreSQL **depois** do cálculo e **fora** da decisão. Não produz a resposta: registra-a. Opcional — sem `DATABASE_URL` ele não existe, e a tela não muda. | 🟢 |

---

## 2. A Regra Central do Domínio: três eixos que não se contaminam 🟢

Esta continua sendo a **decisão de negócio mais importante do sistema**. Ela nasceu em 2026-10-04 (commits `7bf2676`, `cd8d7f3`, `a4d24df`), foi documentada pela primeira vez na extração de 2026-10-05, e **nenhuma das features 005 a 012 a tocou**.

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

**As duas proibições, declaradas literalmente no código** (`core/dna_analysis.py`):

1. O DNA **não** altera o parentesco documental. Um conflito vira **aviso e lista de causas**, nunca reescrita de vínculo.
2. O cM **nunca** é usado sozinho para afirmar parentesco. O código proíbe nominalmente os dois antipadrões que o legado sugeria: `if cm == faixa: parentesco = relacionamento_do_GEDCOM` e `if cm == 10.8: relacionamento = "primo de 4º grau"`.

**Consequência de produto, também decidida:** o rótulo **"Relacionamento Provável (DNA)" foi removido**; o que existe é **"Possibilidades de parentesco pelo DNA"**, dentro da seção de evidência genética.

### 2.1 Os quatro estados do confronto 🟢

| Estado | Gatilho | Mensagem (contrato literal) |
| --- | --- | --- |
| **COMPATIVEL** | cM **dentro** da janela esperada para o parentesco documental | "Compatível: o parentesco documental encontrado no GEDCOM não entra em conflito evidente com a quantidade de DNA compartilhada." |
| **POSSIVEL** | cM **fora** da janela, **mas** alguma relação publicada que contém o valor tem faixa que **se sobrepõe** à janela documental | "Possível: a evidência genética permite esse relacionamento, mas não é suficiente para confirmar o caminho documental." |
| **CONFLITANTE** | cM **fora** da janela e **nenhuma** relação publicada que contém o valor se sobrepõe a ela | "Conflitante: a quantidade de DNA observada apresenta incompatibilidade significativa com o parentesco documental encontrado. Verifique homônimos, vínculos incorretos, pedigree collapse, endogamia ou outro caminho ancestral." |
| **INCONCLUSIVO** | Sem DNA, sem caminho documental, identidade ambígua, ou **sem faixa publicada** para comparar | "Inconclusivo: os dados disponíveis não permitem avaliar adequadamente a compatibilidade entre o caminho documental e a evidência genética." |

> **Por que sobreposição de faixas, e não distância em meioses.** As duas distribuições "se tocam" quando as faixas se sobrepõem, e nesse caso o cM **não consegue separar** as duas leituras — é isso que autoriza `POSSIVEL`. O contraexemplo medido está no código: irmãos (1613–3488 cM) e primos de 1º grau com uma remoção (102–980 cM) estão a **uma** meioses de distância e **mesmo assim** não se sobrepõem. 🟢

**Regra de agregação com múltiplos kits** 🟢 — o estado final é sempre o **mais conservador** entre os kits, na ordem `CONFLITANTE > POSSIVEL > COMPATIVEL > INCONCLUSIVO`. O código avisa na tela e mostra o estado por kit.

**Rol de causas** 🟢 — `CONFLITANTE` recebe as **12** causas possíveis; `POSSIVEL` recebe um subconjunto de **9**. O próprio código declara que **não é diagnóstico automático**: é o rol que o operador deve considerar.

> ⚠️ **O estado é também nome de classe CSS** (`badge estado-{{ status }}`). Renomear um estado quebra a cor do selo **em silêncio**, e não há teste que prenda o par.

---

## 3. Regras de Negócio Principais

> As 233 regras catalogadas estão em `code-analysis.md` §2.4 a §6.3 e em `.reversa/context/modules.json`. Esta seção consolida **as decisões de domínio**, não a enumeração.

### 3.1 Parentesco documental 🟢

Dois estágios, **nesta ordem** — o segundo só roda se o primeiro falhar:

| Estágio | Método | Sobe por | Teto | Mensagem |
| --- | --- | --- | --- | --- |
| **Direta** | BFS **bidirecional** (`find_ancestral_path`) | **apenas pais** (`FAMC` / `child_to_family`) | 20 **iterações de profundidade** | `"Conexão direta encontrada (ancestral comum)."` |
| **Indireta** | `nx.shortest_path` no grafo pessoa↔família | **qualquer** vínculo, inclusive casamento | 40 **arestas** do grafo (≈20 vínculos entre pessoas) | `"Conexão indireta encontrada (via casamento/afinidade)."` |

- **Sem caminho nos dois estágios** → `"Nenhuma conexão encontrada entre 'X' e 'Y'."` com `success = True` — isto é, **"não achei" não é erro**; erro é entrada inválida. Desde a feature 006 esse fato é carregado pelo campo **`desfecho`**, e não pelo texto. 🟢
- **O teto de 20 conta iterações, não gerações** e corta **em silêncio**; o aviso diz explicitamente que isso **não prova** ausência de parentesco. Decisão humana de 2026-09-30: preservar a fidelidade ao legado. 🟢
- **Idade de genitor fora de 12–70 anos** marca `plausible: False` e gera o aviso `data_impossivel`, **sem invalidar o vínculo**. Sem data para julgar, `plausible` é `None`, e `None` **não** é falso. 🟢
- **Caminhos múltiplos nunca são descartados**: o caminho exibido é o de menor distância total e os demais ficam listados. 🟢
- **Afinidade em três lugares**: `status = "affinity"`, rótulo próprio e um aviso **em maiúsculas** de que aquilo **NÃO** representa parentesco consanguíneo. 🟢
- **A escolha entre homônimos deixou de ser o 1º ID na busca** (feature de 2026-10-05): até **5×5** combinações são testadas e vence a primeira **com caminho**. Medido: "Jose Vicente de Souza" tem três registros e só um tem pais. No fluxo de DNA, mantém-se o primeiro candidato do legado. Nos dois casos a ambiguidade é **avisada**. 🟢
- **A idade só é conferida no caminho direto.** A ponte por casamento **não** passa pela checagem de 12–70 anos — assimetria registrada, não corrigida. 🟡

### 3.2 Evidência genética 🟢

- A chave de evidência é **(nome, kit)**, nunca só o nome. Sem coluna de kit, o **e-mail** assume o papel; sem ambos, a chave é a sentinela ` SEM-KIT` — **com espaço à esquerda**, porque o saneamento aplica `strip` a todo valor do CSV, e era assim que o literal `SEM-KIT` colidia com um kit de verdade. 🟢
- **Mais de um kit para o mesmo nome** → aviso `multiplos_kits`, e **nenhum total é somado entre kits**. Quando há vários kits e não se sabe qual deles é a pessoa do GEDCOM, `totals.cm` é **`None`** — "é o número honesto". 🟢
- **O cM acumulado nunca é arredondado** no núcleo; o arredondamento é **exclusivamente de apresentação**. O contrato está congelado em `tests/test_formatacao_cm.py`, porque a paridade contra o oráculo exige igualdade exata. 🟢
- **Sem evidência** → `available: False` com o aviso `sem_evidencia`. 🟡 *(o fluxo segue e o confronto responde INCONCLUSIVO)*

### 3.3 Possibilidades (Shared cM Project 4.0) 🟢

- **27 relações publicadas** são a tabela; o cM vira **lista** ordenada por distância da média (empate desempatado pelo nome). 🟢
- **Seis relações NÃO são publicadas** na versão 4.0 — `1C4R`, `1C5R`, `1C6R`, `3C2R`, 2º bisavô/avó e 3º bisavô/avó — justamente as mais distantes. **Nenhum número é inventado**: a janela passa a ser a **envoltória** das publicadas com o mesmo número de meioses; sem nenhuma, **não há janela** e o confronto fica `INCONCLUSIVO`. 🟢
- **Valor sem cobertura publicada devolve lista vazia** e a leitura de que **isso não descarta parentesco**. 🟢
- **A confiança da lista (`indeterminada` / `baixa` / `muito baixa`) é heurística DO PROJETO** e o código a declara como tal: a fonte **não define** grau de confiança. 🟢
- **Duas limitações da fonte, herdadas de propósito:** a 4.0 **não publica mediana** (existe `average`, não `median`) e a coluna *Range* **exclui 1% dos envios** — a faixa **não** é o intervalo observado completo. Quem reimplementar **não deve** inventar mediana nem tratar a faixa como intervalo total. 🟡

### 3.4 Matching difuso de nomes: o cM **não** decide aceitação 🟢

- **Score** = `0.55·token_sort_ratio + 0.25·partial_ratio + 0.20·ratio(prenome) + InterBonus`, com `InterBonus = 8.0·(sobrenomes em comum) − 4.0·(quantos deles são comuns)`, arredondado a 2 casas. **Pesos herdados do legado.** 🟢
- **Desempate em QUATRO níveis**: mais sobrenomes em comum → maior similaridade de prenome → maior score → **menor `xref_id`**. O quarto critério foi acrescentado em 2026-10-06 e é o que torna a escolha **independente da ordem de iteração de um `set`**. 🟢
- **Filtro anti-falso-positivo**: sem sobrenome em comum **e** sem acerto de sufixo (`filho`, `neto`, `júnior`, `sobrinho`) → candidato **rejeitado**, com o motivo registrado. 🟢
- **Interseção mínima adaptativa**: prenome genérico com ≥ 2 sobrenomes no CSV eleva a exigência de 1 para 2 sobrenomes. 🟢
- **Jaccard de prefixo suave**: limiar 0,50 com ≥ 2 sobrenomes, caindo para **0,33 apenas quando `cM ≥ 150` E o prenome não é genérico**. Decisão humana de 2026-08-03: **intencional**. 🟢
- **O cM só influencia esse limiar.** 🟢
- **Equivalentes de grafia** (`netto→neto`, `gouvea`/`gouvêa`/`gouvéia→gouveia`) e **prefixos de sobrenome** (mín. 3 caracteres) resgatam grafias abreviadas ou corrompidas. 🟢
- **Conflito de nome do meio**: token do CSV que não é prenome nem sobrenome e não existe no GEDCOM rebaixa o aceite para `score ≥ 96` e `given ≥ 92`. 🟢
- **O matching recebe o cM DO KIT**, nunca a soma de kits diferentes. 🟢

### 3.5 Upload, armazenamento e reenvio 🟢

- **A validação é de conteúdo, não de extensão**: depois de remover um BOM UTF-8 e espaços à esquerda, o arquivo precisa começar com `0 HEAD`. O `RISK-007` **autoriza** esse relaxamento. 🟢
- **A elegibilidade da referência passou a ser por FORMA DE NOME, e não por alfabeto fechado** (2026-10-10): o alfabeto recusava acento e espaço, que o gravador **preserva de propósito**, e três arquivos com acento e um com espaço ficaram inalcançáveis — a tela dizia que não existiam (`BUG-20261009-6RKP` / `RN-20`). A defesa continua sendo de forma, e não de lista negra: barra, barra invertida, NUL, `.` e `..` são recusados. 🟢
- **O nome do cliente nunca compõe o caminho**: o arquivo é gravado como `<16 hex do sha256 do conteúdo>__<nome visível>`. 🟢
- **A extensão original é preservada**, não fixada em `.ged`. 🟢
- **Mesmo conteúdo, mesma chave — e a chave é o que circula entre requisições.** Um UUID aleatório quebraria a continuidade, porque o formulário devolve a referência no POST seguinte. **É a chave de conteúdo que faz o papel de identificador de sessão.** 🟢
- **Teto de corpo de 16 MB** com resposta **HTTP 413** e mensagem em português. 🟢
- **O reenvio tem três desfechos com mensagem própria** (`RN-17`): `identico` (nada mudou), `substituido` (a versão anterior foi para `_aposentados/`) e `novo` (o literal congelado `Arquivo 'X' carregado!`). A regra vale para **GEDCOM e CSV**, pela **mesma função**. 🟢
- **A ordem da `RN-17` é a regra: listar ANTES de guardar.** Só a foto de antes separa "já existia" de "acabou de nascer", porque `guardar` **não sobrescreve**. 🟢
- **Aposentar move, e nunca apaga** (`RN-14`): o arquivo vai para `<pasta>/_aposentados/`, inteiro e com o mesmo nome. Se já existe um aposentado de mesmo nome, um sufixo `.1`…`.99` é acrescentado; depois de 99 tentativas a operação **desiste** em vez de sobrescrever. 🟢
- **O CSV de DNA não passa por validação de conteúdo** — só a forma do nome é validada. É coerente com a leitura tolerante, mas significa que um CSV arbitrário é gravado antes de qualquer verificação. 🟡
- **A mensagem de recusa de conteúdo do GEDCOM passou a ser fixa** (`RN-18`): as três recusas — arquivo vazio, byte NUL e cabeçalho ausente — têm o **mesmo texto**, a pedido do operador. O motivo não se perdeu: continua dentro da exceção, a um `str(erro)` de distância de quem depura. 🟢

### 3.6 A tela de entrada: listar, escolher e aposentar 🟢 *(novo)*

- **As duas abas com as listas são entregues em TODA renderização**, e não só depois de um envio (`D-04`). Elas entram por **processador de contexto**, porque a rota tem **23** `render_template` — medidos em 2026-10-10, dos quais **12** passam `gedcom_filename` — e repetir o argumento seria 23 lugares para esquecer um. 🟢
- **Quem lê a pasta é a porta, e a listagem não abre arquivo nenhum**: do diretório ela lê o nome, e do arquivo apenas tamanho e data. É o que permite montar a tela sem reler os 29 MB da pasta. 🟢
- **Arquivos com a mesma chave de conteúdo viram um item**, e o representante é o de maior data. Arquivo **sem** chave vira item próprio e **nunca** é agrupado — a chave não o alcança. 🟢
- **A aba é decidida pela extensão do nome visível cru**, e não pelo conteúdo: `planilha.csv.ged` entra na aba de árvore, e quem recusa é o **uso**. 🟢
- **O item indisponível aparece marcado, com o motivo**, e há **dois motivos distintos**: "sem chave" (arquivo anterior à chave por conteúdo) e "fora da forma". Esconder o inalcançável tiraria do operador justamente o arquivo que ele mais quer aposentar. 🟢
- **A tela pergunta a MESMA função que o resolvedor**, para a marca nunca divergir dele. 🟢
- **Escolher uma árvore da lista tem ramo próprio** (feature 012): sem ele, o clique seria descartado e o operador clicaria sem nada acontecer — defeito medido em 2026-10-09. 🟢
- **A referência escolhida na lista tem precedência sobre o arquivo enviado**, e o campo é opcional: sem ele, o caminho é exatamente o de antes. 🟢

### 3.7 Histórico da análise: registrar sem decidir 🟢 *(novo)*

- **A persistência fica depois do processamento e fora da decisão.** Nenhum módulo de `core/` conhece o registro, e nenhum fluxo consulta o banco para decidir, completar ou corrigir um resultado. Ela responde "o que esta análise concluiu, e por quê" — não produz a resposta. 🟢
- **É opcional, e a ausência é o comportamento de antes.** Sem `DATABASE_URL` a borda monta um registrador **nulo**; a tela não muda um byte. O mesmo vale sem a referência da árvore: sem a chave de conteúdo não há o que gravar. 🟢
- **Falha de persistência nunca interrompe a análise.** O texto `Histórico não registrado: …` é o único sinal que o operador tem, e a análise continua na tela. O driver é importado **preguiçosamente** justamente porque não está instalado no interpretador oficial. 🟢
- **A análise inteira vai em uma transação**: ou entra tudo, ou não entra nada. Análise pela metade é pior que análise ausente — deixaria o veredito de um par gravado com os dados de outro. 🟢
- **A árvore NÃO é duplicada no banco.** Ela continua sendo o arquivo imutável de `src/uploads/`, referenciado pela chave de conteúdo. O que se guarda é o **retrato** das pessoas daquela análise. 🟢
- **O `dono` é gravado e não filtra nada**: nenhuma consulta tem `WHERE owner_id`, e nenhum índice começa por ele. 🟢

### 3.8 Leitura tolerante do CSV: descartar sim, esconder não 🟢

- Tenta `utf-8` e, na falha, `latin-1`. 🟢
- O separador é decidido pelo cabeçalho entre vírgula, ponto e vírgula, TAB e barra vertical; no empate vence a **vírgula** (padrão do GEDmatch). Nunca `csv.Sniffer`, que erra em arquivo de uma coluna. 🟢
- O cabeçalho é localizado quando há preâmbulo, com **três guardas** contra falsos positivos medidos. 🟢
- Linha com número de campos diferente do cabeçalho **não derruba a análise**: o arquivo é relido descartando essas linhas, e a tela **publica a contagem e os números de linha**. 🟢
- O erro, quando nenhuma tentativa produz tabela utilizável, é **acionável**: diz o separador usado, as colunas encontradas, as linhas divergentes e o que conferir. 🟢

### 3.9 Ordem de apresentação dos resultados 🟢

Decisão deliberada de 2026-10: **primeiro o que tem caminho documental, depois cM decrescente dentro de cada grupo** — e **não** cM global. A justificativa é medida e está no código: no GEDCOM real, são **71 conexões, das quais 64 sem caminho**; ordenar só por cM enterraria as 7 conexões documentais no meio das 64. O código declara que **não é ordem de confiança**. 🟢

### 3.10 Arte da tela: a servida não é a canônica 🟢 *(novo)*

- **A arte do ícone de atalho é uma RENDERIZAÇÃO DERIVADA**: a canônica composta sobre **branco** e reamostrada para **180×180** com cantos retos. Servir a canônica daria um **quadrado preto** no atalho, porque o sistema móvel compõe transparência sobre preto. 🟢
- **A arte do banner também é derivada**: a fonte chegou em `RGB`, com o **quadriculado de transparência gravado no bitmap**, e o fundo é removido. Deixar o arquivo como veio desenharia uma grade cinza atrás do logo. 🟢
- **A arte de runtime mora em `src/assets/`** porque o `.dockerignore` é lista de **permissão**: arte em `docs/` responderia 200 no host e **404 dentro do container** — falha silenciosa no ambiente do operador. 🟢
- **A receita tem fonte única em `tests/`**, e um teste de deriva regenera a arte e compara **pixel a pixel** com o arquivo commitado. Comparar por `sha256` daria alarme falso: o mesmo desenho existe em disco com duas codificações de bytes diferentes e diferença de pixel **zero**. 🟢

---

## 4. Fluxo de Decisão por Ação do Usuário

| Ação | Pré-condições | Regra de negócio | Conf. |
| --- | --- | --- | --- |
| **Abrir `/` (GET)** | — | Renderiza a tela com as **duas listas**, por processador de contexto | 🟢 |
| **`GET /banner.png`** | — | Serve a arte derivada; ausente → `404` e nada mais muda | 🟢 |
| **`GET /apple-touch-icon.png`** | — | Idem, com o ícone opaco de 180×180 | 🟢 |
| **Upload GEDCOM** (`action=upload_gedcom`) | campo `gedcom` presente e com nome não vazio | Lê o conteúdo **inteiro**, valida **antes** de gravar, grava sob chave de conteúdo, aposenta versões anteriores de mesmo nome visível, parseia e devolve os nomes ordenados. O desfecho decide a mensagem | 🟢 |
| **Qualquer outro `action`** | referência presente **e** válida **e** arquivo existente | **A árvore é remontada a partir da referência recebida, antes de ramificar.** Não há árvore "carregada" sobrevivendo entre requisições | 🟢 |
| **Aposentar** (`action=aposentar_arquivo`) | referência é um nome válido e o arquivo existe | Move para `_aposentados/`, com sufixo em caso de colisão. **Nada é apagado.** A ação é tratada **antes** da resolução da árvore | 🟢 |
| **Escolher árvore** (`action=selecionar_arvore`) | referência resolvida | Renderiza o **mesmo** estado do envio. Sem efeito colateral | 🟢 |
| **Path Search** (`action=path_search`) | duas pessoas resolvíveis por nome | Testa até 5×5 combinações de homônimos e vence a **primeira com caminho**; tenta direta; se falhar, indireta; se ambas falharem, informa sem conexão com `desfecho = SEM_RESULTADO` | 🟢 |
| **DNA Analysis** (`action=dna_analysis`) | CSV (enviado **ou** escolhido da lista) + `root_name` resolvível | Agrega por (nome, kit), casa nomes, calcula parentesco documental até a raiz, lista possibilidades e confronta. Ordena com documental primeiro. **Depois**, registra o histórico | 🟢 |
| **CSV escolhido da lista** | referência presente | Tem **precedência** sobre o arquivo enviado; se não resolver, `Erro: Arquivo 'X' não existe mais.` | 🟢 |
| **Reenvio de CSV com conteúdo novo** | mesmo nome visível | Substitui: a versão anterior vai para `_aposentados/`, e o aviso é **acrescentado** à mensagem do resultado — nunca a substitui | 🟢 |
| **Match casa mas não tem caminho documental** | — | **Não é descartado em silêncio.** Entra no resultado com as quatro seções; 64 dos 71 casos reais são assim | 🟢 |
| **Match não casa** | — | Vai para `skipped_matches` com o motivo específico, em **texto** | 🟢 |
| **Raiz ambígua** | `root_name` casa com mais de um registro | Usa o **primeiro** e avisa quantos e quais são | 🟢 |
| **Pessoa não encontrada por nome** | — | `"Pessoa 1 '{nome}' não encontrada."` / `"Pessoa 2 ..."` com `desfecho = ERRO_DE_ENTRADA` | 🟢 |
| **Subir uma segunda instância** | porta já em uso | **Recusa subir**, com diagnóstico que separa "porta ocupada" de "endereço indisponível" | 🟢 |

---

## 5. Contrato de Mensagens ao Usuário 🟢

Texto de **contrato**, não prosa: testes de golden file e o harness de paridade dependem de literais.

### 5.1 Borda (`src/app.py`)

| Mensagem | Categoria |
| --- | --- |
| `"Nenhum arquivo GEDCOM enviado."` | Erro de entrada |
| `"Nenhum arquivo selecionado."` | Erro de entrada |
| `"Arquivo '{nome original}' carregado!"` | Sucesso — **literal congelado** |
| `"Arquivo '{X}' já estava armazenado com o mesmo conteúdo: nada mudou."` | Sucesso — desfecho `identico` |
| `"Arquivo '{X}' atualizado: a versão anterior saiu da lista e continua guardada, inteira, na pasta de aposentados."` | Sucesso — desfecho `substituido` |
| `"O CSV '{X}' substituiu a versão anterior, que saiu da lista e continua guardada na pasta de aposentados."` | Sucesso — aviso **acrescentado** ao resultado |
| `"Arquivo não reconhecido como GEDCOM. Favor, enviar o arquivo correto."` | Erro de conteúdo — **texto FIXO desde a `RN-18`** |
| `"'{ROTULO}' saiu da lista. O arquivo não foi apagado: ele continua guardado, inteiro, na pasta de aposentados."` | Sucesso — aposentar |
| `"Não foi possível aposentar o arquivo: ele não está mais na pasta."` | Erro de estado |
| `"Erro: Arquivo GEDCOM não encontrado."` | Erro de entrada |
| `"Erro: Arquivo '{referência}' não existe mais."` | Erro de estado — serve à árvore **e** ao CSV |
| `"Erro: o arquivo '{rotulo}' não pôde ser lido como GEDCOM. Ele pode estar corrompido, vazio, ou não ser um GEDCOM de verdade."` | Erro de parse |
| `"Por favor, carregue o arquivo CSV de matches."` | Erro de entrada |
| `"Ocorreu um erro: {e}"` | Erro inesperado |
| `"Arquivo maior que o limite de {n} MB."` (**HTTP 413**) | Recusa por tamanho |

### 5.2 Núcleo e aplicação (`src/core/`, `src/application/`)

| Mensagem | Categoria |
| --- | --- |
| `"{n} conexões encontradas. {m} descartadas."` | Sucesso |
| `"Histórico não registrado: o driver do banco não está instalado neste interpretador ({erro})."` | Aviso de degradação |
| `"Histórico não registrado: falha ao preparar os dados ({Tipo}: {erro})."` | Aviso de degradação |
| `"Seu nome '{root_name}' não foi encontrado no GEDCOM."` (exceção) | Erro de entrada |
| `"Colunas de Nome e cM não encontradas no CSV. ..."` (exceção, acionável) | Erro de arquivo |
| `"Não foi possível ler o arquivo CSV. Tentativas feitas: ..."` (exceção) | Erro de arquivo |
| `"Conexão direta encontrada (ancestral comum)."` | Sucesso |
| `"Conexão indireta encontrada (via casamento/afinidade)."` | Sucesso |
| `"Nenhuma conexão encontrada entre '{p1}' e '{p2}'."` | Sem resultado |
| `"Pessoa 1 '{nome}' não encontrada."` / `"Pessoa 2 ..."` | Erro de entrada |
| `AVISO_AFINIDADE` — `"...NÃO representa parentesco consanguíneo."` | Alerta obrigatório |
| `"Sem ancestral comum: conexão por afinidade (casamento)"` (rótulo) | Rótulo |
| `"Pessoas não encontradas no GEDCOM"` / `"Parentesco documental não encontrado"` (rótulos) | Rótulo |
| `"Sem Nome"` — **apenas** quando não há `name` | Fallback de exibição |
| As **4 mensagens** de `MENSAGENS[...]` (§2.1) | Veredito do confronto |

> ⚠️ **Duas correções contra a extração de 2026-10-05.** (a) O literal `"Arquivo não reconhecido como GEDCOM: {motivo}."` **deixou de existir** na tela: desde a `RN-18` a mensagem é fixa e o motivo só vive dentro da exceção. (b) `"Relação distante ou indeterminada"` continua existindo **apenas em `core/cm_estimator.py`**, que está **fora do fluxo** e não é consultado pela interface.

---

## 6. Decisões Humanas Vigentes

> Todas foram **verificadas contra o código de 2026-10-10**. A coluna de situação diz se o código atual **honra** a decisão.

### 6.1 Decisões de 2026-08-03 (4)

| # | Assunto | Resposta vigente | Situação no código atual | Conf. |
| --- | --- | --- | --- | --- |
| 1 | Regras de aceitação do matching | **Definitivas** — preservar com fidelidade | ✅ honrada: 5 ramos + filtro anti-falso-positivo intactos | 🟢 |
| 2 | Homônimos usam o 1º ID | **Aceitável** | ⚠️ **ampliada**: a busca testa até 5×5 e vence a primeira com caminho; o 1º ID é só o recuo. A escolha deixou de ser silenciosa | 🟢 |
| 3 | Upload sem validação de extensão/tamanho | **Limitação aceita** para uso local | ❌ **superada**: teto de 16 MB, validação de conteúdo e chave de conteúdo | 🟢 |
| 4 | Relaxamento de Jaccard 0,5 → 0,33 com cM ≥ 150 | **Intencional** — mantém-se | ✅ honrada | 🟢 |

### 6.2 Decisões de 2026-09-30 (5 respostas)

| # | Assunto | Resposta | Situação no código atual | Conf. |
| --- | --- | --- | --- | --- |
| 1 | Teto de 20 iterações do BFS | **Aceitável** — preservar fidelidade ao legado | ✅ honrada: `MAX_DEPTH = 20`, corte silencioso mantido | 🟢 |
| 2 | Varredura global de `get_spouses` | **Intencional** — documentar como contrato | ✅ honrada: a varredura só roda quando a lista de `FAMS` fica vazia | 🟢 |
| 3 | Entidades decorativas | **Arquitetura abandonada — REMOVER** | ✅ executada em 2026-09-30 | 🟢 |
| 4 | Desempate de candidatos | **Precisa ser determinístico** (menor `xref_id`) | ✅ **implementada** em 2026-10-06 (commit `9aa190a`) e congelada por teste | 🟢 |
| 5 | Faixas de cM escritas à mão | **Declarar como heurística** | ✅ honrada: `cm_estimator.py` marcado "LEGADO, fora do fluxo" | 🟢 |

### 6.3 Decisões de 2026-10-05 (16 perguntas) e das rodadas seguintes

| Assunto | Decisão | Situação | Conf. |
| --- | --- | --- | --- |
| **Núcleo puro** (feature 005) | A árvore entra **por parâmetro** em todo o núcleo; o estado global sai | ✅ executada em 2026-10-07: `core/gedcom_state.py` **apagado**, `get_name`/`ref_id` extraídos para módulo puro | 🟢 |
| **Fronteira de aplicação** (feature 006) | Quatro portas `Protocol` + casos de uso com resultado tipado + erros de domínio tipados | ✅ executada: `src/application/` e `src/ports/` existem, e a casca `load_gedcom_and_build_graph` foi removida | 🟢 |
| **Dono no port** (feature 007) | Exigir `dono` em **todos** os métodos das três portas, **sem comportamento** | ✅ executada: o parâmetro existe e é ignorado; a coluna existe e não filtra | 🟢 |
| **Persistência** (feature 008) | PostgreSQL **opcional** para o histórico, com Docker em dois serviços | ✅ executada: 6 tabelas, import preguiçoso, degradação em aviso | 🟢 |
| **Isolamento entre usuários** (`BUG-20260929-BJJH`) | **Não corrigir no legado.** Single-tenant por aceite de risco; tratamento na **Onda 3** | ⚠️ vigente. A parte "duas sessões compartilham árvore" tornou-se **estruturalmente impossível**; a parte "quem conhece a chave carrega a árvore" permanece | 🟢 |
| **Arte do ícone** (feature 009) | Servir uma **derivada** opaca de 180×180, com receita única e teste de deriva | ✅ executada em 2026-10-08 | 🟢 |
| **Uploads fora do repositório** (feature 010) | Declarou uma pasta canônica **fora** da árvore do repositório | ❌ **REVERTIDA** pela feature 012 (ver abaixo) | 🟢 |
| **Pasta canônica de uploads** (feature 012) | Os arquivos vivem em **uma única pasta dentro do repositório**: `src/uploads/` | ✅ vigente. A garantia material é o `.gitignore`: o padrão `uploads/` com barra final casa em qualquer profundidade, e **zero** arquivos de `src/uploads/` são rastreados (13 em disco, 0 no índice) | 🟢 |
| **Aposentar em vez de apagar** (feature 011 / `RN-14`) | Tirar da lista **movendo** para `_aposentados/`, nunca apagando | ✅ executada | 🟢 |
| **Reenvio com substituição** (feature 011 / `RN-17`) | Reenviar o mesmo nome visível substitui, com três desfechos nomeados | ✅ executada; a mesma regra passou a valer para o CSV | 🟢 |
| **Elegibilidade da referência** (feature 011 / `RN-20`) | Trocar o **alfabeto fechado** por **forma de nome**, para o arquivo com acento voltar a ser alcançável | ✅ executada em 2026-10-10; `BUG-20261009-6RKP` fechado | 🟢 |
| **Mensagem de recusa do GEDCOM** (`RN-18`) | Texto **único e fixo** para as três recusas de conteúdo | ✅ executada a pedido do operador, com a perda de pista declarada | 🟢 |
| **Arte do topo** (feature 011 / `T036` e `T044`) | Substituir o `<h1>` por imagem e depois **voltar o título a texto**, com arte a 50 % | ✅ executada; a ordem imagem → subtítulo → título → texto tem teste próprio | 🟢 |
| **Formatação de cM** (`BUG-20261004-EWSJ`) | Ruído de ponto flutuante sai da tela | ✅ corrigida em 2026-10-04 | 🟢 |
| **Servidor de entrada** (feature 004) | **waitress**, instância única, escuta local por padrão | ✅ vigente; o motivo da guarda passou a ser só o armazenamento em disco | 🟢 |

### 6.4 A reversão registrada: 010 → 012

**Este é o único caso de decisão revertida no histórico do projeto, e ele está documentado nos dois sentidos.** A feature `010-uploads-fora-do-repositorio` (2026-10-09) decidiu que a pasta canônica de uploads viveria **fora** da árvore do repositório. No **mesmo dia**, a feature `012-pasta-canonica-no-repositorio` desfez a decisão `D-01`/`3b` da 010 e fixou `src/uploads/`.

**O que sustenta a decisão vigente não é preferência, e sim a garantia material:** o `.gitignore` tem `uploads/` com barra final, padrão que casa em **qualquer profundidade** e portanto cobre `src/uploads/`. A verificação feita nesta rodada confirma: **0 arquivos de `src/uploads/` rastreados pelo Git, 13 em disco**. Sem essa linha, a decisão de manter a pasta dentro do repositório colocaria dado real do operador — um GEDCOM de 5,3 MB entre 13 arquivos — a um `git add .` de ser versionado. 🟢

---

## 7. Lacunas 🔴

| ID | Lacuna | Conf. |
| --- | --- | --- |
| **L-15** | ✅ **FECHADA.** Determinismo do desempate: decidido em 2026-09-30, **implementado em 2026-10-06** e congelado por `tests/test_characterization_matching.py`. | 🟢 |
| **L-16** | ✅ **FECHADA em 2026-10-10 — a contaminação entre requisições concorrentes deixou de existir.** Não há mais estado global: a árvore é um valor por requisição. O que resta é a corrida sobre o **armazenamento em disco** (dívida #3), que é de concorrência de sistema de arquivos e não de identidade. | 🟢 |
| **L-17** | ✅ **DECIDIDA (2026-10-05)** — avisar é suficiente; o cM segue declarado como teto otimista em colapso/endogamia. | 🟢 |
| **L-18** | **Relações mais distantes não publicadas na SCP 4.0**, que é onde o caso real cai. A envoltória de meioses mitiga, sem substituir a fonte. | 🟡 |
| **L-19** | ✅ **FECHADA (2026-10-05)** — o `.venv/` é o interpretador oficial, e o `README.md` **passou a documentá-lo** (reconferido em 2026-10-10: a pendência de documentação está fechada). | 🟢 |
| **L-20** | **Custo não limitado por resultado.** `person_a` e `person_b` são **fichas completas** em cada resultado, e `get_children` varre **todas** as famílias sem índice. No caso real de 71 conexões foram **142 fichas**. | 🟢 |
| **L-21** | ✅ **DECIDIDA (2026-10-05)** — persistir passa a ser requisito do alvo. **Executada no legado em 2026-10-08** pela feature 008. | 🟢 |
| **L-22** | **Política de descarte.** O match descartado é exibido com motivo. Não há indicação de negócio sobre se o operador **deve agir** sobre os descartados, nem qual taxa de descarte é aceitável. | 🟡 |
| **L-23** | ✅ **FECHADA (2026-10-05)** — cobertura de `src/` medida em **83 %**. | 🟢 |
| **L-24** | 🔴 **NOVA: a chave do cache de nomes pode não invalidar entre duas árvores.** `_chave_de` usa `(len(people), primeira chave, última chave)`. Dois GEDCOMs com o mesmo número de pessoas e os mesmos xrefs extremos — provável entre exports do mesmo exportador — produzem a mesma chave, e o índice da árvore **anterior** é reaproveitado: o dossiê de homônimos passa a listar xrefs de outra árvore, **sem exceção**. É a lacuna de maior risco aberta nesta rodada. Ver `flowcharts/busca-caminho.md` §13. | 🟡 |
| **L-25** | 🟡 **NOVA: a ordem de `common_ancestors` e de `additional_paths` depende do `PYTHONHASHSEED`** quando dois ancestrais empatam em meioses, distância **e** nome. É a mesma classe do defeito que o `matching` fechou em 2026-10-06, e aqui segue aberta. | 🟡 |
| **L-26** | 🔴 **NOVA: `psycopg2-binary==2.9.13` está pinado e NÃO está instalado no `.venv`**, que é o interpretador oficial. A persistência fica **desligada** no ambiente oficial por ausência de driver, e não por decisão. É o **inverso** da divergência de versão da rodada anterior. | 🟢 |
| **L-27** | 🟢 **NOVA: o resultado da suíte depende do ambiente.** Com `DATABASE_URL` presente no ambiente e sem o driver, **2 testes** de `tests/test_persistencia_desabilitada.py` falham — o aviso não bloqueante aparece onde o contrato de tela congelado exige silêncio. Sem a variável: 527 passam, 9 pulados, 0 falham. | 🟢 |
| **L-28** | 🔴 **NOVA: não há teste de caminho feliz de INSERT.** Os testes de persistência exercitam a persistência **desabilitada** e **indisponível**, por desenho. Erro de SQL, de ordem de chave estrangeira ou de tipo só apareceria no contêiner. | 🟢 |
| **L-29** | 🔴 **NOVA: o histórico persiste dado pessoal que antes era efêmero.** `analysis_person` guarda xref, nome, sexo, nascimento, local de nascimento e falecimento — inclusive de **pessoas vivas** — e não há retenção, expurgo nem consentimento. Apagar a árvore já não apaga o retrato. Ver `permissions.md` `P-07`. | 🟢 |

> **Lacunas fechadas em 2026-09-30 que NÃO foram reabertas:** `L-01`/`L-11` (entidades decorativas), `L-02` (`get_spouses`), `L-03` (teto de 20), `L-13` (determinismo).
> **Lacuna fechada nesta rodada:** "o sistema não tem banco de dados" — falso desde a feature 008.

---

## 8. Resumo para o Reversa

- **Regras de negócio de domínio consolidadas:** **10 famílias** (§3), sobre **233 regras** catalogadas no `code-analysis.md` e no `modules.json`.
- **Regra central:** os **três eixos que não se contaminam** (parentesco documental, evidência genética, confronto) com **quatro estados**.
- **Máquinas de estado:** **1 ciclo de vida de verdade** (a posição do arquivo: na pasta ↔ aposentado), **1 estado durável de produto** (a análise registrada, que não transiciona) e **4 máquinas de decisão** — o veredito do confronto, o status do parentesco documental, o **desfecho do reenvio** e o **desfecho da busca**. Detalhamento, diagramas e as máquinas que **não** foram geradas em `state-machines.md`.
- **Permissões:** **inexistentes** — nenhum `session`, `login`, `auth`, `role` ou `permission`. `app.secret_key` foi **removida** em 2026-10-05. O **`dono` agora existe** em toda assinatura de porta e como coluna `owner_id`, e **não isola nada**. A corrida entre threads sobre a árvore **deixou de existir**. Registrado em `permissions.md`, com 4 lacunas novas (credencial em claro, dado pessoal persistido, rotas de arte públicas, alcance da corrida de disco).
- **ADRs:** **36 decisões** em `adrs/` — 23 herdadas (revalidadas contra o código atual) e **13 novas** para as features 005 a 012, incluindo a **reversão** da feature 010 pela 012.
- **Mensagens de contrato:** **29 literais** catalogados (§5), dos quais 7 são provados por golden file.
- **Decisões humanas vigentes:** **19** verificadas; **1 revertida** (010 → 012), registrada nos dois sentidos.
- **Lacunas para validação:** **6 abertas** (`L-18`, `L-22`, `L-24`, `L-25`, `L-28`, `L-29`), das quais **3 críticas** — a colisão da chave do cache de nomes, o dado pessoal persistido sem retenção e a ausência de teste do caminho de gravação.

---

*Gerado pelo Reversa-Detective em 2026-10-10 (re-extração, nível completo).*

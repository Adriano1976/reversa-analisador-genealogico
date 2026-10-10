# Unit `analise-dna` — Contratos

> Re-extração de **2026-10-10** (nível **Completo**). Substitui o artefato de 2026-10-05, que fixava `ValueError` como único erro tipado, o CSV como única entrada possível e **nenhum** contrato de persistência.
> Este arquivo fixa **o que atravessa a fronteira** da unit: o contrato HTTP, o contrato do CSV, o contrato da evidência, o do veredito, o do payload da porta, os avisos, as mensagens e o contrato de falha.
> Escala de confiança: 🟢 CONFIRMADO | 🟡 INFERIDO | 🔴 LACUNA

---

## 1. Contrato HTTP

| Método | Caminho | Ação | Entrada | Status | Corpo da resposta |
| --- | --- | --- | --- | --- | --- |
| `POST` | `/` | `dna_analysis` | `gedcom_filename`, `root_name` e **ou** o arquivo `matches_csv` **ou** a referência `matches_csv_filename` | `200` | HTML com `dna_results`, `skipped_matches`, `message`, `aviso_de_persistencia`, `success`, `all_names` e `gedcom_filename` |
| `POST` | `/` (qualquer `action`) | — | corpo acima de **16 MB** | **`413`** | HTML com `"Arquivo maior que o limite de 16 MB."` |

> 🟢 **Não há contrato JSON, `redirect`, `201`, `400`, `404` ou `422`.** Toda recusa de **negócio** desta unit é HTML com status `200` e `success=False`. O `413` é a única recusa de transporte, e acontece **antes** de a rota executar.
>
> 🔴 **Os status que `traduzir` calcula não têm consumidor.** A tabela devolve `404` para pessoa não encontrada e `422` para as demais, mas **nenhuma tela lê essa coluna** — ela existe, e é testada, para que a regra da API nova esteja em um lugar só (`BR-D-95`).

### 1.1 Contrato da requisição

| Campo | Local | Obrigatório | Forma aceita | Recusa |
| --- | --- | --- | --- | --- |
| `action` | `form` | sim | literal `dna_analysis` | outro valor não entra neste ramo 🟢 |
| `gedcom_filename` | `form` | sim | **referência** (`<16 hex>__<nome visível>`) | ausente → `Erro: Arquivo GEDCOM não encontrado.` 🟢 |
| `root_name` | `form` | sim | nome da raiz, resolvido por **substring case-insensitive** | ausente do GEDCOM → `PessoaNaoEncontrada` 🟢 |
| `matches_csv` | `files` | condicional | CSV de matches; **não passa por validação de conteúdo** | ausente **e** sem referência → `"Por favor, carregue o arquivo CSV de matches."` 🟢 |
| `matches_csv_filename` | `form` | **opcional** | referência de um CSV **já armazenado** | presente e não resolvida → `Erro: Arquivo 'X' não existe mais.` 🟢 |

> 🟢 **A precedência é a regra:** com `matches_csv_filename` presente, o arquivo enviado é **ignorado**. O campo é **novo** em vez de reaproveitar `matches_csv` justamente para que o caminho antigo continue provado idêntico (`BR-D-89`).

### 1.2 Contrato da resposta

| Variável | Tipo | Quando vem | Significado |
| --- | --- | --- | --- |
| `dna_results` | `list[dict]` | no sucesso | Itens de resultado, já ordenados (§6) 🟢 |
| `skipped_matches` | `list[dict]` | no sucesso | Descartes com motivo (§6.2) 🟢 |
| `message` | `str` | sempre que há algo a dizer | `"{n} conexões encontradas. {m} descartadas."`, ou o literal do erro 🟢 |
| `success` | `bool` | junto com `message` | `True` só quando a análise concluiu 🟢 |
| `aviso_de_persistencia` | `str \| None` | no sucesso | **`None` significa "nada a avisar"** — gravado, ou persistência desabilitada. Nulo ⇒ a tela **não renderiza nada** 🟢 |
| `gedcom_filename` | `str` | nas ações pós-upload | Devolvido para o próximo `POST` 🟢 |
| `all_names` | `list[str]` | nas ações pós-upload | Lista de nomes da árvore — **preservada mesmo nos erros**, para o formulário não esvaziar 🟢 |

---

## 2. Contrato do CSV de entrada

### 2.1 Colunas reconhecidas por papel

| Papel | Nomes aceitos / regra | Obrigatório |
| --- | --- | --- |
| Nome | `Name`, `MatchedName`, `Nome` | **sim** 🟢 |
| cM | `cM`, `TotalCM`, `Total cM` | **sim** 🟢 |
| ID de match | **primeira** coluna com > 30 % dos valores casando `[A-Z]{2}\d{7}` | não 🟢 |
| E-mail | a **última** coluna cujo nome contém `mail` | não 🟢 |
| Kit | coluna cujo **nome** casa `kit`, `gedmatch`, `teste` ou `test` com > 50 % dos valores em `[A-Z]{1,3}\d{4,8}`; senão, a que tem > 30 % em `[A-Z]{2}\d{7}` | não 🟢 |
| SNPs, cromossomo, início, fim, fonte | nomes variantes por papel | não 🟢 |

> ✅ **Cobertura de exportadores DECIDIDA em 2026-10-05** (`questions.md#pergunta-10`): o operador usa **apenas o GEDmatch**. As regras acima são as do formato testado, e a lacuna de cobertura fecha como **cobertura declarada de um exportador**, não como incerteza. **Não há prova de generalidade** para outros exportadores, e não precisa haver enquanto o uso for este.

### 2.2 Contrato de tolerância

| Situação | Contrato |
| --- | --- |
| Encoding | `utf-8`; recuo para `latin-1` no erro de codec — e **nenhuma exceção de domínio intercepta a troca** 🟢 |
| Separador | decisão por contagem no cabeçalho; **empate fica com a vírgula**; **nunca `csv.Sniffer`** 🟢 |
| Preâmbulo | até **10** linhas antes do cabeçalho são examinadas e reportadas 🟢 |
| Linha torta | descartada, **com contagem e números de linha publicados** 🟢 |
| Arquivo que não é tabela | **não** elege cabeçalho falso; o erro final diz o que conferir 🟢 |

### 2.3 Canal de metadados (`df.attrs`)

| Atributo | Tipo | Padrão | Significado |
| --- | --- | --- | --- |
| `separador` | `str` | `","` | Separador efetivamente usado 🟢 |
| `encoding` | `str` | `"utf-8"` | Encoding que funcionou 🟢 |
| `linhas_antes_do_cabecalho` | `int` | `0` | Linhas de preâmbulo puladas 🟢 |
| `linhas_ignoradas` | `list[int]` | `[]` | Números **1-based** das linhas descartadas 🟢 |
| `erro_de_leitura` | `str \| None` | `None` | Texto do erro do pandas, quando houve releitura 🟢 |

> ⚠️ **`attrs` é o canal por contrato.** Trocar o retorno por tupla quebraria o núcleo. Quem reimplementar deve manter o canal ou assumir a quebra explicitamente. 🟢

---

## 3. Contrato da evidência genética

### 3.1 Chave

```text
evidencias[ nome_normalizado ][ kit ]
```

| Regra | Consequência | Conf. |
| --- | --- | --- |
| Duas linhas com o mesmo nome e **kits diferentes** são **duas** evidências | Nunca há soma entre laboratórios | 🟢 |
| Sem coluna de kit, o **e-mail** assume o papel | Kits distintos por e-mail permanecem separados | 🟢 |
| Sem kit e sem e-mail, a chave é `" SEM-KIT"` — **com espaço à esquerda** | Aviso `kit_ausente`. **O espaço é a defesa contra colisão (`E-03`)**: a limpeza remove espaços das pontas de todo valor do CSV, então nenhum kit real pode ter esse texto | 🟢 |

### 3.2 Contrato de valores

| Campo | Contrato | Conf. |
| --- | --- | --- |
| `total_cm` | Soma dos segmentos **sem arredondamento** — o contrato está congelado em teste (`19.200000000000003` é o esperado) | 🟢 |
| `totals.cm` | cM do kit quando há **um**; **`None`** quando há mais de um | 🟢 |
| `cm_por_kit` | Um valor por kit, com a chave `" SEM-KIT"` (espaço à esquerda) quando não informado | 🟢 |
| `largest_segment_cm` | `None` quando nenhum segmento tem cM numérico | 🟢 |
| `weak_segment` | Presente e `True` quando o maior segmento é < **15 cM** (heurística **do projeto**) | 🟢 |
| `snps_total` | `None` quando não há SNPs informados | 🟢 |

> ⚠️ **`None` significa "não sei", nunca zero.** É invariante do sistema e vale para `totals.cm`, `largest_segment_cm`, `plausible` e `age_at_birth` (`data-dictionary.md` §10). 🟢

---

## 4. Contrato das possibilidades

| Regra | Contrato | Conf. |
| --- | --- | --- |
| Tipo do retorno | **Sempre lista**, inclusive vazia — **nunca** um parentesco único | 🟢 |
| `cM` utilizável | Todas as relações publicadas que contêm o valor, ordenadas por distância da média e, em empate, pelo nome em inglês | 🟢 |
| `cM` ausente/inválido (`≤ 0` ou não numérico) | Lista vazia + confiança `indeterminada` | 🟢 |
| Lista vazia com valor válido | **Não descarta parentesco** — é ausência de cobertura publicada | 🟢 |
| Confiança | `indeterminada` (0), `baixa` (1–3), `muito baixa` (4–6 e > 6) — **heurística do projeto** | 🟢 |
| Relação não publicada | **Nenhum número é inventado**; a janela passa a ser a **envoltória por meioses** | 🟢 |

### 4.1 Contrato da fonte (Shared cM Project 4.0)

| Propriedade | Valor | Efeito no contrato |
| --- | --- | --- |
| Versão | 4.0, março de 2020 | 🟢 |
| Amostra | 59.714 envios | — 🟢 |
| Relações publicadas | **27** (medido por importação em 2026-10-10) | A tabela é embutida 🟢 |
| Mediana | **não publicada** — existe `average`, não existe `median` | **Não inventar mediana** 🟢 |
| Faixa | Após remoção de **1 %** dos envios | **Não é o intervalo observado completo** 🟢 |
| Endogamia / colapso de pedigree | **A fonte declara que não atende** | O cM lido é teto otimista nesses casos (`L-17`) 🟢 |
| Relações ausentes | **6**: `1C4R`, `1C5R`, `1C6R`, `3C2R` e os 2º/3º bisavós | Envoltória por meioses, ou `INCONCLUSIVO` 🟢 |

---

## 5. Contrato do veredito (o confronto)

### 5.1 Os quatro estados

| Estado | Rótulo | Gatilho | Conf. |
| --- | --- | --- | --- |
| `COMPATIVEL` | Compatível | cM **dentro** da janela esperada | 🟢 |
| `POSSIVEL` | Possível | cM **fora**, mas alguma relação publicada que contém o valor tem faixa que **se sobrepõe** à janela | 🟢 |
| `CONFLITANTE` | Conflitante | cM **fora** e **nenhuma** sobreposição | 🟢 |
| `INCONCLUSIVO` | Inconclusivo | Sem DNA, sem caminho documental, identidade ambígua, ou sem faixa publicada | 🟢 |

**`INCONCLUSIVO` é o estado inicial de todo resultado** — as guardas retornam **sem alterá-lo**. Nenhum estado é afirmado por omissão. 🟢

> 🟡 **Os quatro rótulos acima são também nomes de classe CSS no template** (`badge estado-{{ status }}`). Renomear um estado muda a cor da tela, e **não há teste** que amarre os dois.

### 5.2 Contrato do veredito

| Campo | Contrato | Conf. |
| --- | --- | --- |
| `status` | Um dos quatro, sempre | 🟢 |
| `label` | Rótulo em português, acoplado a `status` (de `STATUS_LABEL`) | 🟢 |
| `message` | Mensagem fixa do estado (de `MENSAGENS`) | 🟢 |
| `causes` | **12** causas em `CONFLITANTE`; **8** em `POSSIVEL`; vazio nos demais | 🟢 |
| `per_kit` | `{kit, status, cm, note}` por kit — **a severidade é auditável** | 🟢 |
| `method` | `scp40:<nome>` ou `scp40:meioses=<n>` — **como o estado foi decidido** | 🟢 |
| `expected_range` | `{low, high, average, label}` da janela | 🟢 |
| `detail` | Frase que reúne parentesco documental, janela e a nota de cada kit | 🟢 |
| `observations` | Notas preservadas → vão para a seção de observações da tela | 🟢 |

> ⚠️ **Correção medida em 2026-10-10:** o subconjunto de `POSSIVEL` tem **8** causas, e não 9. O valor é `CAUSAS_POSSIVEIS[:1] + [3:8] + [10:]` = 1 + 5 + 2, medido por importação do módulo. O catálogo anterior (`code-analysis.md` §4.4 e `modules.json` `BR-D-35`) afirmava 9 e está errado. Há teste dedicado para essa contagem (`TT-19`) justamente para impedir que alguém a "corrija" de volta.

### 5.3 Contrato de agregação entre kits

**Ordem literal:** `CONFLITANTE > POSSIVEL > COMPATIVEL > INCONCLUSIVO`. O estado final é o **primeiro dessa lista que aparecer** entre os kits. 🟢

> Não é média, não é maioria, não é "o pior cM". Um único kit `CONFLITANTE` entre cinco torna o veredito `CONFLITANTE` — de propósito: a agregação existe para **preservar o alerta**, e a tela mostra o estado por kit para que a decisão seja auditável.
>
> 🟡 **`INCONCLUSIVO` é o último da ordem**, e isso tem consequência: um kit **sem cM utilizável** não rebaixa o resultado quando outro kit é `COMPATIVEL`. A ausência de dado nunca protege contra uma conclusão otimista de outro kit.

### 5.4 Contrato com o parentesco documental

| Garantia | Conf. |
| --- | --- |
| O confronto **não altera** o parentesco documental — nenhum campo de `documentary` é reescrito | 🟢 |
| Nenhum caminho é **inventado** a partir do DNA | 🟢 |
| Sem caminho documental, o estado é `INCONCLUSIVO` e o texto diz que o documental vale por si | 🟢 |
| A **distância em meioses não é critério** — e `_avaliar_kit` recebe o parâmetro `meioses_documental` **sem lê-lo** | 🟡 |

---

## 6. Contrato do payload e dos avisos

### 6.1 Item de resultado (o que a tela consome)

| Campo | Contrato |
| --- | --- |
| `match_name` | Nome do registro do GEDCOM escolhido 🟢 |
| `csv_name` | Nome como veio do CSV 🟢 |
| `cm` | cM **do kit** — nunca a soma de kits 🟢 |
| `text_path` | Nomes do caminho separados por `" → "` 🟢 |
| `mermaid_data` | Diagrama do caminho **documental**, ou `None` 🟢 |
| `documentary` / `genetic_evidence` / `hypotheses` / `comparison` | As quatro seções 🟢 |
| `observations` | Textos **deduplicados**, na ordem documental → genética → confronto → avisos 🟢 |
| `warnings` | Avisos do documental + da evidência 🟢 |

**Ordem de apresentação:** `(0 se tem caminho documental senão 1, −cM)`. **Não é ordem de confiança** — está declarado no código. 🟢

### 6.2 Descartes

| Campo | Contrato |
| --- | --- |
| `csv_name` | Nome do CSV que não virou resultado 🟢 |
| `kit` | Kit do descartado 🟢 |
| `cm` | cM do kit 🟢 |
| `motivo` | **Nunca vazio**; `"não encontrado"` é o padrão 🟢 |

**Motivos catalogados:** `"sem candidatos por sobrenome (abreviação/corrupção?)"`, `"sem sobrenome em comum (filtro anti-falso-positivo)"`, `"score insuficiente ou conflito de sobrenome (given=…, final=…, inter=…/…, jacc=…)"`, `"não encontrado"`. 🟢

> 🟢 **O motivo é texto, e o texto é contrato.** O terceiro carrega os **quatro números** da decisão, e é o que permite ao operador agir. Encurtá-lo destrói a utilidade da lista.

### 6.3 Códigos de aviso

| Código | Produtor | Significado |
| --- | --- | --- |
| `multiplos_kits` | `genetic_evidence` | Mais de um kit para o mesmo nome; **nenhum total somado** 🟢 |
| `kit_ausente` | `genetic_evidence` | Sem coluna de kit e sem e-mail: chave `" SEM-KIT"` 🟢 |
| `segmento_fraco` | `genetic_evidence` | Maior segmento abaixo de 15 cM (**heurística do projeto**) 🟢 |
| `sem_evidencia` | `genetic_evidence` | Não há evidência genética para esta pessoa 🟢 |
| `pessoa_ausente` | `documentary_relationship` | Registro ausente no GEDCOM 🟢 |
| `sem_caminho` | `documentary_relationship` | Nenhum caminho dentro do teto — **não prova** ausência de parentesco 🟢 |
| `homonimo` | `documentary_relationship` | Identidade ambígua; análise não conclusiva 🟢 |
| `data_impossivel` | `documentary_relationship` | Idade de genitor fora de 12–70; **o vínculo é mantido** 🟢 |
| `caminhos_multiplos` | `documentary_relationship` | Mais de um percurso; nenhum descartado 🟢 |
| `colapso_de_pedigree` | `documentary_relationship` | Mesmo ancestral por mais de uma cadeia (teto 8) 🟢 |
| `afinidade` | `path_search` | Caminho por casamento; **não** é consanguinidade 🟢 |

### 6.4 Contrato do payload da porta `RegistroDeAnalises` *(novo)*

`AnaliseParaRegistrar` é **dado plano**, e é o que a projeção pura produz:

| Campo | Contrato | Conf. |
| --- | --- | --- |
| `tree_ref` | Referência da árvore — **exigida**: sem ela não há registro | 🟢 |
| `match_file_ref` | **Nome do arquivo armazenado** do CSV (derivado do caminho) | 🟢 |
| `root_name_input` | O `root_name` como o operador digitou | 🟢 |
| `root_person_xref` | `documentary.person_a.id` da **primeira** conexão | 🟢 |
| `message` | A mensagem final, literal | 🟢 |
| `pessoas` | Retrato por xref, **uma vez cada**: `xref, nome, sexo, nascimento, local_nascimento, falecimento, completa` | 🟢 |
| `conexoes` | 21 campos, com `kits` e `caminho` como **tuplas**; `caminho` = pares `(xref, papel)` | 🟢 |
| `descartados` | `ordinal, csv_name, reason` (**texto**), `kit, total_cm` | 🟢 |
| `accepted_count` / `skipped_count` | Tamanhos das listas | 🟢 |

**Regras de projeção que são contrato:**

| Regra | Conf. |
| --- | --- |
| A projeção é **pura**: não reordena, não recalcula cM, não formata e não chama o núcleo | 🟢 |
| `ordinal` é a posição na ordem **apresentada** | 🟢 |
| O pareamento kit ↔ veredito é **por índice**; kit sem avaliação herda o estado final com `status_note` nulo | 🟢 |
| Papel do nó: **`descendente`** depois do ancestral comum, **`ascendente`** até ele; sem MRCA, o corte cai no **penúltimo** nó; **`afinidade` nunca** é atribuída aqui | 🟢 |
| Ficha **completa** vence a identificação; ficha sem `id` é descartada | 🟢 |
| Defaults: `comparison_status = "INCONCLUSIVO"`, `documentary_status = "not_found"`, strings vazias, `reason = "não encontrado"` | 🟢 |

**Tabelas de destino** (`init.sql`, 6 tabelas idempotentes, sem `DROP`): `dna_analysis` → `analysis_person` → `match_result` → `match_kit` / `match_path_node` → `skipped_match`. `is_affinity_anchor` é **sempre** `FALSE`; `owner_id` recebe o `dono` e **nenhuma** consulta filtra por ele. 🟢

---

## 7. Contrato de mensagens

### 7.1 Literais da tela

| Literal | Categoria |
| --- | --- |
| `"{n} conexões encontradas. {m} descartadas."` | Sucesso 🟢 |
| `"Por favor, carregue o arquivo CSV de matches."` | Erro de entrada 🟢 |
| `"Ocorreu um erro: {e}"` | Erro inesperado 🟢 |
| As **4** mensagens de veredito (`MENSAGENS`) | Veredito 🟢 |
| `"Sem evidência genética disponível para esta pessoa."` | Aviso 🟢 |
| `"Nenhuma relação publicada na versão 4.0 cobre exatamente este valor."` | Aviso 🟢 |

### 7.2 Tabela de tradução das exceções de domínio *(novo)*

As molduras foram **medidas**, não deduzidas. **O prefixo `Ocorreu um erro: ` existe onde o legado o produzia, e só lá.**

| Exceção | Moldura na tela | Status | Conf. |
| --- | --- | --- | --- |
| `PessoaNaoEncontrada` | `Ocorreu um erro: Seu nome '{root_name}' não foi encontrado no GEDCOM.` | `404` | 🟢 |
| `DnaCsvSemColunas` | `Ocorreu um erro: Colunas de Nome e cM não encontradas no CSV. O arquivo foi lido com o separador … e as colunas encontradas foram: […]. Confira se o arquivo enviado é a lista de matches de DNA …` | `422` | 🟢 |
| `CsvIlegivel` | `Ocorreu um erro: Não foi possível ler o arquivo CSV. Tentativas feitas: … Confira se o arquivo enviado é a lista de matches de DNA …` | `422` | 🟢 |
| `GedcomNaoSuportado` | `Arquivo não reconhecido como GEDCOM. Favor, enviar o arquivo correto.` — **frase fixa, sem o motivo e sem prefixo** | `422` | 🟢 |
| Qualquer outro `ErroDeDominio` | `Ocorreu um erro: {e}` | `422` | 🟢 |

> 🟢 **Por que a tabela é de FUNÇÕES, e não de constantes:** sete das nove mensagens congeladas **interpolam valores**. Um mapa de classe para string constante não conseguiria construí-las.
>
> 🟢 **O motivo da recusa de GEDCOM não se perdeu:** ele continua dentro da exceção, a um `str(erro)` de distância de quem depura. Só a **apresentação** deixou de exibi-lo (`RN-18`).

### 7.3 Aviso de persistência

| Situação | Literal | Conf. |
| --- | --- | --- |
| Driver ausente no interpretador | `Histórico não registrado: o driver do banco não está instalado neste interpretador ({erro}).` | 🟢 |
| Falha na projeção dos dados | `Histórico não registrado: falha ao preparar os dados ({Tipo}: {msg}).` | 🟢 |
| Banco fora ou erro de SQL | `Histórico não registrado: {Tipo}: {msg}` | 🟢 |
| Gravado com êxito, ou persistência desabilitada | **`None`** — a tela não renderiza nada | 🟢 |

---

## 8. Contrato de falha

| Situação | O que **é** garantido | O que **não** é |
| --- | --- | --- |
| CSV ilegível | `CsvIlegivel` acionável, listando as tentativas | Retry, log ou alerta 🔴 |
| Raiz inexistente | Mensagem ao operador; **nenhum resultado parcial** exibido | — 🟢 |
| Faixa não publicada | Veredito `INCONCLUSIVO`; **nenhum número inventado** | — 🟢 |
| Identidade ambígua | Veredito `INCONCLUSIVO` com os registros listados | — 🟢 |
| Endogamia / colapso de pedigree | Aviso no lado documental | 🔴 **Não altera o veredito** — o cM é teto otimista (`L-17`) |
| Empate triplo no desempate de candidatos | O **menor `xref_id`** vence, sempre — estável entre processos e ordens de *pool* | — 🟢 |
| Persistência desabilitada | Nada é gravado e a tela **não muda um byte** | — 🟢 |
| Driver ausente, banco fora ou erro de SQL | A análise **conclui** e é exibida, com aviso **não bloqueante** | Nada vai para o log 🟡 |
| Falha na projeção | Idêntico ao anterior: aviso, e o resultado chega | — 🟢 |
| Erro inesperado | `"Ocorreu um erro: {e}"` na tela | Nada é registrado em log 🔴 |
| Duas requisições concorrentes | Cada uma usa a **sua** árvore: a corrida sobre o estado global **deixou de existir** (`ADR-24`) | A corrida de **armazenamento em disco** continua aberta (dívidas #3/#4) 🟡 |

---

## 9. Compatibilidade e versionamento

| Elemento do contrato | Estabilidade exigida | Consequência de mudar |
| --- | --- | --- |
| Valores de `action` e nomes dos campos | **Alta** | É a granularidade das units (endpoint) |
| Precedência de `matches_csv_filename` sobre `matches_csv` | **Alta** | Inverter reintroduz o CSV duplicado na lista — o defeito medido na feature 012 |
| Chave de evidência **(nome, kit)** | **Alta** | Somar kits é erro silencioso de dado |
| `totals.cm = None` com múltiplos kits | **Alta** | Trocar por soma produz um número que o sistema não pode afirmar |
| Os quatro estados e a ordem de conservadorismo | **Alta** | Muda o produto da unit; o template consome os literais |
| Contagem de causas (12 / **8**) | Média | Muda o texto da tela; o **8** é medido e tem teste |
| Ordem `documental primeiro` | Média | Muda a leitura da tela, não o resultado |
| Tabela do SCP 4.0 e a definição de faixa | **Alta** | Muda **todas** as janelas e, portanto, os vereditos |
| Limiar de 15 cM (segmento fraco) | Média | Heurística do projeto; altera avisos, não vereditos |
| Limiar de Jaccard `0,33` (`cM ≥ 150` e prenome não genérico) | **Alta** (a decisão) / **Média** (o número) | A decisão de relaxar é intencional; o **número é heurístico e ajustável** |
| Critério final do desempate (menor `xref_id`) | **Alta** | Removê-lo reintroduz o resultado não reprodutível entre execuções |
| Versão de `RapidFuzz` | **Alta** | Muda o matching **sem** mudar código (`L-19`) |
| Contrato da projeção pura | **Alta** | É o que sustenta o histórico e os testes sem banco |
| Literais de `aviso_de_persistencia` | Média | A tela os exibe, mas o operador age pelo resultado, não pelo aviso |
| Schema das 6 tabelas | **Alta** | O histórico é dado durável: mudar coluna exige migração real |

---

*Gerado pelo Reversa-Writer em 2026-10-10 (re-extração). Substitui a versão de 2026-10-05.*

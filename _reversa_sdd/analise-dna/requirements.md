# Unit `analise-dna` — Requisitos

> Unit do tipo **endpoint** — cobre `POST /` com `action=dna_analysis`.
> Spec gerada pelo Reversa-Writer na re-extração de **2026-10-05** (nível **Completo**).
> Substitui a versão de 2026-09-30, que descrevia o fluxo **anterior** ao refactor: um pipeline único de matching + faixas de cM escritas à mão, **sem** evidência genética por kit e **sem** confronto. Snapshot: `.reversa/snapshots/2026-10-05-pre-reextracao/analise-dna/`
> Fontes: `code-analysis.md` §3 (62 regras `BR-D-*`), `flowcharts/analise-dna.md`, `data-dictionary.md` §4 a §6, `domain.md` §2, `state-machines.md` §3, `adrs/` (13, 14, 15, 16, 19, 20, 22, 23)
> Escala de confiança: 🟢 CONFIRMADO | 🟡 INFERIDO | 🔴 LACUNA

---

## Visão Geral

Cruza a árvore GEDCOM carregada com um CSV de matches de DNA e responde **três perguntas separadas**, sem nunca misturá-las: *o que o GEDCOM afirma sobre o parentesco*, *o que o arquivo de DNA informa* e *as duas coisas são compatíveis entre si*. 🟢

É a **unit de maior complexidade do sistema**: 62 regras de negócio, 8 módulos, e a única cuja saída é um **veredito** (`COMPATIVEL` / `POSSIVEL` / `CONFLITANTE` / `INCONCLUSIVO`). A regra que a define é negativa: **o cM nunca é usado sozinho para afirmar parentesco**. 🟢

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

## Regras de Negócio

### Entrada e leitura tolerante

- A raiz é resolvida por **substring do nome, sem diferenciar maiúsculas**; usa o **primeiro** registro e **avisa** quantos e quais são os homônimos. 🟢
- O CSV é lido primeiro como `utf-8`; na falha, como `latin-1`. 🟢
- O separador é decidido pelo cabeçalho entre vírgula, ponto e vírgula, TAB e barra vertical: vence a maior contagem, e **no empate vence a vírgula** (padrão do GEDmatch). 🟢
- O cabeçalho é localizado quando há preâmbulo, com **três guardas**: frequência ≥ 2 do número modal de campos, primeira linha divergente e posição dentro das **10** primeiras linhas. 🟢
- Linha com número de campos diferente do cabeçalho **não derruba a análise**: o arquivo é relido descartando essas linhas, e a tela **publica a contagem e os números de linha**. 🟢
- Sem coluna de Nome ou de cM → `ValueError` **acionável** em português, dizendo o separador usado, as colunas encontradas e o que conferir. 🟢

### Evidência genética

- A chave de evidência é **(nome, kit)** — duas linhas com o mesmo nome e kits diferentes são **duas** evidências. 🟢
- Sem coluna de kit, o **e-mail** assume o papel; sem ambos, a chave é `SEM-KIT` e sai o aviso `kit_ausente`. 🟢
- **Nenhum total é somado entre kits.** Com mais de um kit e sem saber qual é a pessoa do GEDCOM, `totals.cm` é **`None`** — é o número honesto. 🟢
- **O cM acumulado não é arredondado**; o arredondamento é só de apresentação, e o contrato está congelado em teste. 🟢
- Maior segmento abaixo de **15 cM** marca `weak_segment` e gera o aviso `segmento_fraco`. **Limite é heurística do projeto**, não da fonte. 🟢

### Matching difuso

- **Score** = `0.55·token_sort_ratio + 0.25·partial_ratio + 0.20·similaridade_do_prenome + (8·interseção − 4·sobrenomes_comuns)`, arredondado a 2 casas. **Pesos herdados do legado, não alterados.** 🟢
- **Desempate** lexicográfico: mais sobrenomes em comum → maior similaridade de prenome → maior score. 🟢
- **Filtro anti-falso-positivo:** ambos os lados com sobrenome, interseção zero e sem acerto de sufixo → **rejeita**, com o motivo registrado. 🟢
- **Interseção mínima adaptativa:** prenome genérico com ≥ 2 sobrenomes no CSV eleva a exigência de 1 para 2. 🟢
- **Jaccard com prefixo suave:** limiar 0,50 com ≥ 2 sobrenomes; cai para **0,33 apenas** quando `cM ≥ 150` **e** o prenome não é genérico. A decisão de manter o relaxamento é humana e de 2026-08-03: **intencional**. 🟢
  - 🟡 **O número `0,33` é heurística, sem medição de calibração.** Confirmado por você em 2026-10-05: foi um **chute que funcionou na prática**, e não um valor calibrado contra dados reais. Continua valendo como está — o que muda é a **autoridade** do número, que passa a ser **ajustável** (`L-14`, agora fechada como 🟡).
- **Cinco ramos de aceitação alternativos**, avaliados em ordem, mais um sexto por prefixo de sobrenome; o primeiro verdadeiro vence. 🟢
- **Conflito de nome do meio** rebaixa o aceite para `score ≥ 96` e `given ≥ 92`. 🟢
- **O cM não decide a aceitação.** Ele só influencia o limiar de Jaccard, e há teste de caracterização que congela isso. 🟢

### Parentesco documental e confronto

- O parentesco documental **nunca lê cM**; a evidência genética **não conhece o GEDCOM**. 🟢
- O DNA **não altera** o parentesco documental: um conflito vira **aviso e rol de causas**, nunca reescrita de vínculo. 🟢
- O confronto devolve **sempre** um de quatro estados, e o `INCONCLUSIVO` é o **estado inicial** de todo resultado — nenhum estado é afirmado por omissão. 🟢
- cM dentro da janela → `COMPATIVEL`; fora → `POSSIVEL` quando alguma relação publicada que contém o valor tem faixa que **se sobrepõe** à janela; caso contrário → `CONFLITANTE`. **Distância em meioses não é critério.** 🟢
- Sem DNA, sem caminho documental, identidade ambígua ou sem faixa publicada → `INCONCLUSIVO`. 🟢
- **Com mais de um kit, o estado final é o mais conservador**, na ordem `CONFLITANTE > POSSIVEL > COMPATIVEL > INCONCLUSIVO`. 🟢
- Seis relações **não publicadas** na versão 4.0 não recebem número inventado: a janela passa a ser a **envoltória** das relações publicadas com o mesmo número de meioses. 🟢
- A **confiança da lista** (`indeterminada` / `baixa` / `muito baixa`) é heurística **do projeto** — a fonte não define grau de confiança. 🟢

### Apresentação

- A ordem é **documental primeiro, cM decrescente depois** — e o código declara que **não é ordem de confiança**. Justificativa medida: das **71 conexões** do GEDCOM real, **64 não têm caminho**. 🟢
- Mensagem final: `"{n} conexões encontradas. {m} descartadas."`; **sem nenhum resultado**, os avisos do arquivo são anexados à mensagem, porque não há cartão onde apareçam. 🟢

### Compatibilidade declarada

- `cm_estimator` (as 9 faixas escritas à mão) **está fora do fluxo e da interface**. Continua existindo porque a suíte e o harness de paridade o exercitam, e o próprio módulo declara que não deve ser usado em código novo. 🟢

## Requisitos Funcionais

| ID | Requisito | Prioridade | Critério de Aceite |
| --- | --- | --- | --- |
| RF-01 | Receber `POST` com `action=dna_analysis`, exigindo `gedcom_filename`, `root_name` e o arquivo no campo `matches_csv` | Must | Sem CSV → `"Por favor, carregue o arquivo CSV de matches."`, preservando `all_names` na tela 🟢 |
| RF-02 | Ler o CSV tolerando encoding, separador e preâmbulo | Must | CSV em `latin-1`, com `;` e com 3 linhas de título é lido com as colunas corretas 🟢 |
| RF-03 | Localizar o cabeçalho com as três guardas, sem perder a primeira linha de dados de um arquivo sem cabeçalho | Must | Arquivo sem cabeçalho não perde a linha 1; arquivo que não é tabela não elege cabeçalho falso 🟢 |
| RF-04 | Descartar linhas irregulares **publicando** contagem e números de linha | Must | A tela informa quantas linhas e quais foram descartadas 🟢 |
| RF-05 | Detectar as colunas por papel, tolerando variação de cabeçalho | Must | Nome em `Name`/`MatchedName`/`Nome`; cM em `cM`/`TotalCM`/`Total cM`; kit, SNPs, cromossomo, início, fim e fonte opcionais 🟢 |
| RF-06 | Agregar cM por `nome normalizado + cauda`, com a cauda sendo id, e-mail ou nada | Must | Um registro por chave, com o cM somado 🟢 |
| RF-07 | Construir evidência por **(nome, kit)**, sem somar kits diferentes | Must | Mesmo nome em dois kits produz **duas** evidências 🟢 |
| RF-08 | Marcar `segmento_fraco` quando o maior segmento for menor que 15 cM | Should | Aviso `segmento_fraco` presente; o limite é declarado como heurística do projeto 🟢 |
| RF-09 | Construir os índices do GEDCOM e o cache de atributos normalizados | Must | `ged_index`, `surname_index` e `features[pid]` populados a partir da árvore 🟢 |
| RF-10 | Calcular o score difuso ponderado e desempatar candidatos | Must | Score conforme a fórmula; desempate inter → given → score 🟢 |
| RF-11 | Aplicar o filtro anti-falso-positivo | Must | Match com sobrenomes disjuntos e sem sufixo é rejeitado com motivo 🟢 |
| RF-12 | Aplicar a interseção mínima adaptativa e o limiar de Jaccard, com o relaxamento condicional | Must | Prenome genérico com ≥ 2 sobrenomes exige 2 em comum; limiar 0,33 **só** com `cM ≥ 150` e prenome não genérico 🟢 |
| RF-13 | Aplicar os cinco ramos de aceitação em ordem, mais o ramo de prefixo e o rebaixamento do nome do meio | Must | Decisão idêntica à congelada pelos testes de caracterização 🟢 |
| RF-14 | **Não** permitir que o cM decida aceitação diretamente | Must | Alterar o cM sob o limiar de 150 não muda a decisão de aceitação 🟢 |
| RF-15 | Resolver a raiz por substring, usando o primeiro registro e **avisando** a ambiguidade | Must | Raiz inexistente → `"Seu nome '{root_name}' não foi encontrado no GEDCOM."`; ambígua → aviso com a contagem e os ids 🟢 |
| RF-16 | Obter o parentesco documental de cada candidato e escolher o **primeiro que tiver caminho** | Must | Resultado com `documentary`, `text_path` e `mermaid_data` 🟢 |
| RF-17 | Traduzir o cM em **lista** de possibilidades pela tabela do SCP 4.0 | Must | Sempre lista, inclusive vazia; 27 relações publicadas; ordenada por distância da média 🟢 |
| RF-18 | Usar a **envoltória por meioses** quando a relação exata não for publicada | Must | `1C6R` e os bisavós distantes não recebem número inventado 🟢 |
| RF-19 | Produzir o confronto com um dos quatro estados, sempre com o porquê | Must | `method`, `expected_range`, `detail` e `per_kit` preenchidos quando há janela 🟢 |
| RF-20 | Agregar múltiplos kits pelo **mais conservador** e registrar o estado por kit | Must | Um kit `CONFLITANTE` entre cinco torna o resultado `CONFLITANTE`, com a nota por kit 🟢 |
| RF-21 | Ordenar com **documental primeiro**, depois cM decrescente | Must | Resultados com caminho aparecem antes dos que só têm DNA 🟢 |
| RF-22 | Emitir a mensagem final `"{n} conexões encontradas. {m} descartadas."` | Must | Contagens corretas; sem resultados, os avisos do arquivo são anexados 🟢 |
| RF-23 | Listar os descartes com o motivo específico, **orientando a ação** do operador | Must | Cada descarte traz `csv_name`, `kit`, `cm` e `motivo` — **nunca vazio**; e cada motivo tem uma **ação esperada** correspondente (`design.md` § Discartes) 🟢 |
| RF-24 | Reportar erro amigável, sem quebrar a aplicação | Must | Raiz inexistente e colunas ausentes viram `"Ocorreu um erro: {e}"` com `success=False` 🟢 |
| RF-25 | Declarar `cm_estimator` como **legado fora do fluxo**, reexportado só por compatibilidade | Should | O módulo não é importado por nenhum caminho de produção nem pela interface 🟢 |
| **RF-26** | **Tornar o desempate de candidatos determinístico** | Must | ✅ **IMPLEMENTADO em 2026-10-05.** Com empate exato nos três critérios, vence o **menor `xref_id`** (`matching.py:107-111`). Testes: `test_desempate_escolhe_o_menor_xref_id` (duas ordens de *pool*) e `test_desempate_nao_depende_da_ordem_do_pool` 🟢 |

> ⚠️ **Herança de numeração.** O `RF-26` desta spec corresponde ao **`RF-14` da spec de 2026-09-30** ("tornar o desempate determinístico"), renumerado nesta rodada porque o identificador `RF-14` passou a designar outro requisito. **O conteúdo é o mesmo, e foi ATENDIDO nesta rodada.** Nada foi perdido na renumeração, e a decisão humana de 2026-09-30 segue vigente (`adrs/23`). 🟢
>
> ✅ **Execução do `RF-26` (2026-10-05).** Você escolheu **corrigir o legado** em vez de deixar o requisito apenas para o sistema alvo. O que mudou:
>
> | Item | Antes | Depois |
> | --- | --- | --- |
> | Critério de desempate | três critérios, com empate caindo na ordem de iteração do `set` | **quatro**, sendo o último o **menor `xref_id` lexicográfico** |
> | `src/core/matching.py` | comparação estrita nos três critérios | comparação estrita + `pid < best_pid` quando os três empatam |
> | Teste | inexistente (`TT-15` era lacuna) | `tests/test_characterization_matching.py` com **2 testes novos** |
> | Resultado | vencedor variava entre processos | **estável**, independentemente da ordem do *pool* e de `PYTHONHASHSEED` |
>
> **Esta é a segunda divergência deliberada do legado** — a primeira foi declarar as faixas de cM como heurística e retirá-las do fluxo (`T-32`). Ao contrário dela, esta **muda comportamento**: nos casos de empate triplo, o vencedor pode ser outro. Fora do empate, nada muda. 🟢
>
> ⚠️ **Requisitos da spec anterior que deixaram de existir, e por quê:**
>
> | Requisito de 2026-09-30 | Situação |
> | --- | --- |
> | `RF-10` "prever o parentesco por faixa de cM" | **Substituído por RF-17/RF-18.** A previsão passou a vir da tabela **publicada** (SCP 4.0), e não das faixas escritas à mão |
> | `RF-10a` "as 9 faixas são heurísticas" | **Preservado como RF-25**, com destino diferente: o módulo saiu do fluxo |
> | `RF-08` "aplicar os 6 ramos de aceitação" | **Reescrito como RF-13** — o código atual tem **5 ramos** mais o de prefixo e o rebaixamento do meio |
> | `RF-09` "caminho ancestral até a raiz para o primeiro candidato com caminho" | **Preservado como RF-16**, com destino novo: `documentary_relationship` |
> | `RF-02` "detectar colunas de Nome, cM, ID e e-mail" | **Ampliado no RF-05**: hoje há detecção por papel para kit, SNPs, cromossomo, início, fim e fonte |

## Requisitos Não Funcionais

| Tipo | Requisito inferido | Evidência no código | Confiança |
| --- | --- | --- | --- |
| Performance | O cache de atributos normalizados é calculado **uma vez por análise**, fora do laço de candidatos; o laço renormalizava o mesmo nome ~7 vezes por candidato | `matching.py:27-59` (`norm_name` ≈ 41 µs, `surnames_set` ≈ 72 µs) | 🟢 |
| Performance | **Sem cache entre requisições**: os índices do GEDCOM inteiro são reconstruídos a cada `POST` | `dna_analysis.py:144` | 🟢 |
| Reprodutibilidade | O cM acumulado **não é arredondado** no núcleo; o contrato está congelado em teste, porque a paridade exige igualdade exata | `genetic_evidence.py:162-166`; `tests/test_formatacao_cm.py` | 🟢 |
| Reprodutibilidade | ~~🔴 **O desempate do ramo difuso não é determinístico**~~ ✅ **CORRIGIDO em 2026-10-05:** o critério final passou a ser o **menor `xref_id`** | `matching.py:73`, `:91`, `:107-110` | 🟢 |
| Confiabilidade | `thefuzz` delega a `RapidFuzz`/`python-Levenshtein`; trocar a versão de qualquer uma **altera o resultado do matching** sem mudar uma linha do projeto | `requirements.txt`; `RISK-006` | 🟢 |
| Confiabilidade | Ausência ou divergência de faixa publicada **não** vira veredito: o confronto responde `INCONCLUSIVO` | `evidence_comparison.py:203-208` | 🟢 |
| Segurança | O CSV gravado **não passa por validação de conteúdo** — só a forma do nome é validada | `app.py:86` | 🟢 |
| Escalabilidade | Estado global compartilhado; a análise usa a árvore do último parse da requisição, e o servidor atende com 4 threads | `gedcom_state.py`; `app.py:137`, `:188` | 🟢 |
| Manutenibilidade | Os limiares de aceitação são **literais dentro dos ramos**, e não constantes nomeadas — decisão deliberada (ADR-08), com o custo de não haver ponto único de mudança | `matching.py:140-155`, `:161` | 🟢 |
| Observabilidade | **Nenhum log, métrica ou trace.** A única visibilidade do motivo de um match não aparecer é a lista de descartados | — | 🟢 |
| Internacionalização | Todas as mensagens ao operador são literais em português | `dna_analysis.py`, `evidence_comparison.py` | 🟢 |

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

Dado um CSV com 2 linhas com número de campos diferente do cabeçalho
Quando a análise é executada
Então a análise prossegue com as demais linhas
E a tela informa quantas linhas foram descartadas e quais

Dado um match sem nenhuma evidência genética utilizável
Quando o confronto é executado
Então o estado é INCONCLUSIVO
E o texto registra que o parentesco documental continua valendo por si, sem DNA para confrontar

Dado um match com identidade ambígua no GEDCOM
Quando o confronto é executado
Então o estado é INCONCLUSIVO
E os registros homônimos são listados

Dado um cM fora da janela documental, sem nenhuma relação publicada que se sobreponha a ela
Quando o confronto é executado
Então o estado é CONFLITANTE
E o rol completo de 12 causas é apresentado

Dado um nome de raiz que não existe na árvore
Quando a análise é executada
Então a tela exibe "Ocorreu um erro: Seu nome 'X' não foi encontrado no GEDCOM."
E nenhum resultado parcial é exibido

Dado um CSV sem a coluna de cM
Quando a análise é executada
Então a tela exibe um erro acionável dizendo o separador usado e as colunas encontradas
E a aplicação não quebra
```

## Prioridade (MoSCoW)

| Requisito | MoSCoW | Justificativa |
| --- | --- | --- |
| RF-07 Evidência por (nome, kit), sem somar kits | **Must** | Somar kits é erro silencioso de dado; sustenta todo o confronto |
| RF-17/RF-18 Possibilidades pela fonte publicada | **Must** | Base da comparação; substitui a tabela escrita à mão |
| RF-19 Confronto com os quatro estados | **Must** | É o produto da unit |
| RF-20 Agregação pelo mais conservador | **Must** | Sem ela, um kit conflitante seria diluído |
| RF-10 a RF-13 Matching e aceitação | **Must** | Núcleo do casamento de nomes, com 5 ramos interdependentes |
| RF-16 Parentesco documental e escolha do candidato | **Must** | Sem caminho não há resultado |
| RF-02 a RF-06 Leitura tolerante e agregação | **Must** | Porta de entrada dos dados |
| RF-15 Resolução da raiz com aviso de ambiguidade | **Must** | Sem raiz não há análise |
| RF-21/RF-22 Ordenação e mensagem | **Must** | Contrato de apresentação |
| RF-23 Auditoria dos descartes | **Must** | Elevada de `Should` para `Must` em 2026-10-05: você confirmou que a lista é **acionável** — você age sobre os motivos |
| RF-08 Segmento fraco | **Should** | Heurística do projeto; não bloqueia o veredito |
| RF-25 `cm_estimator` fora do fluxo | **Should** | Existe só para a suíte e o harness não quebrarem |
| **RF-26** Determinismo do desempate | **Must** | ✅ **Implementado em 2026-10-05** — o menor `xref_id` decide o empate triplo |
| `HARD_MIN` / `GIVEN_MIN` | **Won't** | Nunca existiram na reconstrução; decisão de não implementar (ADR-08) |

## Rastreabilidade de Código

| Arquivo | Função / símbolo | Cobertura |
| --- | --- | --- |
| `src/app.py` | ramo `dna_analysis` `:134-154`; re-parse `:132`; guarda do CSV `:136-137` | 🟢 |
| `src/core/dna_analysis.py` | `dna_analysis` `:83`; `_montar_diagrama` `:56`; `_observacoes` `:65`; `_ordem` `:226` | 🟢 |
| `src/parsers/csv_ingest.py` | `read_csv_with_fallback` `:140`; `detectar_separador` `:76`; `localizar_cabecalho` `:93`; `linhas_irregulares` `:126`; `detect_columns` `:185`; `aggregate_matches` `:198` | 🟢 |
| `src/core/genetic_evidence.py` | `build_genetic_evidence` `:110`; `detect_segment_columns` `:41`; `evidence_for` `:209` | 🟢 |
| `src/core/relationship_hypotheses.py` | `possible_relationships` `:161`; `hypotheses_for_evidence` `:208`; `row_for_key` `:106`; `meioses_window` `:120` | 🟢 |
| `src/core/evidence_comparison.py` | `compare` `:150`; `_avaliar_kit` `:75`; `_janela_do_documental` `:116` | 🟢 |
| `src/core/matching.py` | `build_ged_indexes` `:27`; `match_candidates` `:62` | 🟢 |
| `src/core/name_normalization.py` | `norm_name` `:52`; `split_name_pt` `:77`; `surname_core_tokens` `:66`; `soft_prefix_jaccard` `:106` | 🟢 |
| `src/core/documentary_relationship.py` | `documentary_relationship` `:436`; `homonym_dossier` `:205` | 🟢 |
| `src/core/cm_estimator.py` | `get_relationships_by_cm` `:53` — **legado fora do fluxo** | 🟢 |
| `tests/test_dna_analysis.py`, `test_characterization_matching.py`, `test_confrontacao_gedcom_dna.py`, `test_formatacao_cm.py` | cobertura do pipeline, da caracterização, do confronto e do contrato de cM | 🟢 |

---

*Gerado pelo Reversa-Writer em 2026-10-05 (re-extração, nível completo).*

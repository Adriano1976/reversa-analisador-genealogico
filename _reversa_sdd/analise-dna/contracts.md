# Unit `analise-dna` — Contratos

> Re-extração de **2026-10-05** (nível **Completo**). Artefato novo: o nível `essencial` não o gerava.
> Este arquivo fixa **o que atravessa a fronteira** da unit: o contrato HTTP, o contrato do CSV, o contrato da evidência, o contrato do veredito, os códigos de aviso e o contrato de falha.
> Escala de confiança: 🟢 CONFIRMADO | 🟡 INFERIDO | 🔴 LACUNA

---

## 1. Contrato HTTP

| Método | Caminho | Entrada | Status | Corpo da resposta |
| --- | --- | --- | --- | --- |
| `POST` | `/` (`action=dna_analysis`) | `multipart/form-data` com `gedcom_filename`, `root_name` e o arquivo em `matches_csv` | `200` | HTML com `dna_results`, `skipped_matches`, `message`, `success`, `all_names` e `gedcom_filename` |
| `POST` | `/` (qualquer `action`) | corpo acima de **16 MB** | `413` | HTML com a mensagem de limite |

### 1.1 Contrato da requisição

| Campo | Local | Obrigatório | Observação |
| --- | --- | --- | --- |
| `action` | `form` | sim | literal `dna_analysis` 🟢 |
| `gedcom_filename` | `form` | sim | **Chave de conteúdo**, validada por forma; o GEDCOM é **re-parseado** a partir dela antes do despacho 🟢 |
| `root_name` | `form` | sim | Nome da raiz; resolvido por **substring case-insensitive** 🟢 |
| `matches_csv` | `files` | sim | CSV de matches; **não passa por validação de conteúdo** — só a forma do nome 🟢 |

### 1.2 Contrato da resposta

| Variável | Tipo | Significado |
| --- | --- | --- |
| `dna_results` | `list[dict]` | Itens de resultado, já ordenados (§6) 🟢 |
| `skipped_matches` | `list[dict]` | Descartes com motivo (§6.2) 🟢 |
| `message` | `str` | `"{n} conexões encontradas. {m} descartadas."` 🟢 |
| `success` | `bool` | `True` só quando a análise concluiu 🟢 |
| `gedcom_filename` | `str` | Devolvido para o próximo `POST` 🟢 |
| `all_names` | `list[str]` | Lista de nomes da árvore — **preservada mesmo nos erros**, para o formulário não esvaziar 🟢 |

---

## 2. Contrato do CSV de entrada

### 2.1 Colunas reconhecidas por papel

| Papel | Nomes aceitos / regra | Obrigatório |
| --- | --- | --- |
| Nome | `Name`, `MatchedName`, `Nome` | **sim** 🟢 |
| cM | `cM`, `TotalCM`, `Total cM` | **sim** 🟢 |
| Kit | coluna cujo **nome** casa `kit`, `gedmatch`, `teste` ou `test` com > 50 % dos valores em `[A-Z]{1,3}\d{4,8}`; senão, a que tem > 30 % em `[A-Z]{2}\d{7}` | não 🟢 |

> ✅ **Cobertura de exportadores DECIDIDA em 2026-10-05** (`questions.md#pergunta-10`): você usa **apenas o GEDmatch**. As regras acima são, portanto, as do formato testado — e a lacuna `L-08` fecha como **cobertura declarada de um exportador**, não como incerteza. Os nomes de coluna aceitos já são tolerantes por papel, mas **não há prova de generalidade** para os outros exportadores, e não precisa haver enquanto o uso for este.
| ID de match | primeira coluna com > 30 % dos valores casando `[A-Z]{2}\d{7}` | não 🟢 |
| E-mail | a **última** coluna cujo nome contém `mail` | não 🟢 |
| SNPs, cromossomo, início, fim, fonte | nomes variantes por papel | não 🟢 |

### 2.2 Contrato de tolerância

| Situação | Contrato |
| --- | --- |
| Encoding | `utf-8`; recuo para `latin-1` **apenas** em `UnicodeDecodeError` 🟢 |
| Separador | decisão por contagem no cabeçalho; **empate fica com a vírgula** 🟢 |
| Preâmbulo | até **10** linhas antes do cabeçalho são examinadas e reportadas 🟢 |
| Linha torta | descartada, **contagem e números de linha publicados** 🟢 |
| Arquivo que não é tabela | **não** elege cabeçalho falso; o erro final diz o que conferir 🟢 |

### 2.3 Canal de metadados (`df.attrs`)

| Atributo | Tipo | Padrão | Significado |
| --- | --- | --- | --- |
| `separador` | `str` | `","` | Separador efetivamente usado 🟢 |
| `encoding` | `str` | `"utf-8"` | Encoding que funcionou 🟢 |
| `linhas_antes_do_cabecalho` | `int` | `0` | Linhas de preâmbulo puladas 🟢 |
| `linhas_ignoradas` | `list[int]` | `[]` | Números **1-based** das linhas descartadas 🟢 |
| `erro_de_leitura` | `str \| None` | `None` | Texto do erro do pandas, quando houve releitura 🟢 |

> ⚠️ **`attrs` é o canal por contrato.** Trocar o retorno por tupla quebraria `dna_analysis` e o `__all__` que reexporta as funções. Quem reimplementar deve manter o canal ou assumir a quebra explicitamente. 🟢

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
| Sem kit e sem e-mail, a chave é `" SEM-KIT"` — **com espaço à esquerda** | Aviso `kit_ausente`. **O espaço é a defesa contra colisão (`E-03`)**: `_clean` remove espaços das pontas de todo valor do CSV, então nenhum kit real pode ter esse texto. Corrigido em 2026-10-05 | 🟢 |

### 3.2 Contrato de valores

| Campo | Contrato | Conf. |
| --- | --- | --- |
| `total_cm` | Soma dos segmentos **sem arredondamento** | 🟢 |
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
| `cM` utilizável | Todas as relações publicadas que contêm o valor, ordenadas por distância da média | 🟢 |
| `cM` ausente/ inválido | Lista vazia + confiança `indeterminada` | 🟢 |
| Lista vazia com valor válido | **Não descarta parentesco** — é ausência de cobertura publicada | 🟢 |
| Confiança | `indeterminada` (0), `baixa` (1–3), `muito baixa` (4–6 e > 6) — **heurística do projeto** | 🟢 |
| Relação não publicada | **Nenhum número é inventado**; a janela passa a ser a envoltória por meioses | 🟢 |

### 4.1 Contrato da fonte (Shared cM Project 4.0)

| Propriedade | Valor | Efeito no contrato |
| --- | --- | --- |
| Versão | 4.0, março de 2020 | `SCP40_META.version` 🟢 |
| Amostra | 59.714 envios | — 🟢 |
| Mediana | **não publicada** — existe `average`, não existe `median` | 🟢 **Não inventar mediana** |
| Faixa | Após remoção de **1 %** dos envios (0,5 % em cada ponta) | 🟢 **Não é o intervalo observado completo** |
| Endogamia / colapso de pedigree | **A fonte declara que não atende** | 🟢 O cM lido é teto otimista nesses casos (`L-17`) |
| Relações ausentes | `1C4R`, `1C5R`, `1C6R`, `3C2R`, 2º e 3º bisavós | 🟢 Envoltória por meioses, ou `INCONCLUSIVO` |

---

## 5. Contrato do veredito (o confronto)

### 5.1 Os quatro estados

| Estado | Rótulo | Gatilho | Conf. |
| --- | --- | --- | --- |
| `COMPATIVEL` | Compatível | cM **dentro** da janela esperada | 🟢 |
| `POSSIVEL` | Possível | cM **fora**, mas alguma relação publicada que contém o valor tem faixa que **se sobrepõe** à janela | 🟢 |
| `CONFLITANTE` | Conflitante | cM **fora** e **nenhuma** sobreposição | 🟢 |
| `INCONCLUSIVO` | Inconclusivo | Sem DNA, sem caminho, identidade ambígua, ou sem faixa publicada | 🟢 |

**`INCONCLUSIVO` é o estado inicial de todo resultado** — as guardas retornam **sem alterá-lo**. Nenhum estado é afirmado por omissão. 🟢

### 5.2 Contrato do veredito

| Campo | Contrato | Conf. |
| --- | --- | --- |
| `status` | Um dos quatro, sempre | 🟢 |
| `label` | Rótulo em português, acoplado a `status` (de `STATUS_LABEL`) | 🟢 |
| `message` | Mensagem fixa do estado (de `MENSAGENS`) | 🟢 |
| `causes` | **12** causas em `CONFLITANTE`; **9** em `POSSIVEL`; vazio nos demais | 🟢 |
| `per_kit` | `{kit, status, cm, note}` por kit — **a severidade é auditável** | 🟢 |
| `method` | `scp40:<nome>` ou `scp40:meioses=<n>` — **como o estado foi decidido** | 🟢 |
| `expected_range` | `{low, high, average, label}` da janela | 🟢 |
| `detail` | Frase que reúne parentesco documental, janela e a nota de cada kit | 🟢 |
| `observations` | Notas preservadas → vão para a seção de observações da tela | 🟢 |

### 5.3 Contrato de agregação entre kits

**Ordem literal:** `CONFLITANTE > POSSIVEL > COMPATIVEL > INCONCLUSIVO`. O estado final é o **primeiro dessa lista que aparecer** entre os kits. 🟢

> Não é média, não é maioria, não é "o pior cM". Um único kit `CONFLITANTE` entre cinco torna o veredito `CONFLITANTE` — de propósito: a agregação existe para **preservar o alerta**, e a tela mostra o estado por kit para que a decisão seja auditável. 🟢

### 5.4 Contrato com o parentesco documental

| Garantia | Conf. |
| --- | --- |
| O confronto **não altera** o parentesco documental — nenhum campo de `documentary` é reescrito | 🟢 |
| Nenhum caminho é **inventado** a partir do DNA | 🟢 |
| Sem caminho documental, o estado é `INCONCLUSIVO` e o texto diz que o documental vale por si | 🟢 |

---

## 6. Contrato do payload e dos avisos

### 6.1 Item de resultado

| Campo | Contrato |
| --- | --- |
| `match_name` | Nome do registro do GEDCOM escolhido 🟢 |
| `csv_name` | Nome como veio do CSV 🟢 |
| `cm` | cM **do kit** — nunca a soma de kits 🟢 |
| `kit` | Kit do match 🟢 |
| `text_path` | Nomes do caminho separados por `" → "` 🟢 |
| `mermaid_data` | Diagrama do caminho **documental**, ou `None` 🟢 |
| `documentary` | Resultado do parentesco documental 🟢 |
| `genetic_evidence` | Evidência consolidada da pessoa 🟢 |
| `hypotheses` | Um bloco por kit 🟢 |
| `comparison` | O veredito 🟢 |
| `observations` | Textos deduplicados, na ordem de origem 🟢 |
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

### 6.3 Códigos de aviso

| Código | Produtor | Significado |
| --- | --- | --- |
| `multiplos_kits` | `genetic_evidence` | Mais de um kit para o mesmo nome; **nenhum total somado** 🟢 |
| `kit_ausente` | `genetic_evidence` | Sem coluna de kit e sem e-mail: chave `SEM-KIT` 🟢 |
| `segmento_fraco` | `genetic_evidence` | Maior segmento abaixo de 15 cM (**heurística do projeto**) 🟢 |
| `sem_evidencia` | `genetic_evidence` | Não há evidência genética para esta pessoa 🟢 |
| `pessoa_ausente` | `documentary_relationship` | Registro ausente no GEDCOM 🟢 |
| `sem_caminho` | `documentary_relationship` | Nenhum caminho dentro do teto — **não prova** ausência de parentesco 🟢 |
| `homonimo` | `documentary_relationship` | Identidade ambígua; análise não conclusiva 🟢 |
| `data_impossivel` | `documentary_relationship` | Idade de genitor fora de 12–70; **o vínculo é mantido** 🟢 |
| `caminhos_multiplos` | `documentary_relationship` | Mais de um percurso; nenhum descartado 🟢 |
| `colapso_de_pedigree` | `documentary_relationship` | Mesmo ancestral por mais de uma cadeia (teto 8) 🟢 |
| `afinidade` | `path_search` | Caminho por casamento; **não** é consanguinidade 🟢 |

---

## 7. Contrato de mensagens

| Literal | Local | Categoria |
| --- | --- | --- |
| `"{n} conexões encontradas. {m} descartadas."` | `dna_analysis.py:231` | Sucesso |
| `"Seu nome '{root_name}' não foi encontrado no GEDCOM."` (exceção) | `dna_analysis.py:92` | Erro de entrada |
| `"Colunas de Nome e cM não encontradas no CSV. ..."` (exceção acionável) | `dna_analysis.py:117-123` | Erro de arquivo |
| `"Colunas de Nome e cM não encontradas no CSV."` | `genetic_evidence.py:125` | Erro de arquivo |
| `"Por favor, carregue o arquivo CSV de matches."` | `app.py:142` | Erro de entrada |
| `"Ocorreu um erro: {e}"` | `app.py:159` | Erro inesperado |
| As **4** mensagens de veredito | `evidence_comparison.py:41-51` | Veredito |
| `"Sem evidência genética disponível para esta pessoa."` | `genetic_evidence.py:229` | Aviso |
| `"Nenhuma relação publicada na versão 4.0 cobre exatamente este valor."` | `relationship_hypotheses.py:150` | Aviso |

---

## 8. Contrato de falha

| Situação | O que **é** garantido | O que **não** é |
| --- | --- | --- |
| CSV ilegível | `ValueError` acionável com separador, colunas e linhas tortas | Retry, log ou alerta 🔴 |
| Raiz inexistente | Mensagem ao operador; **nenhum resultado parcial** exibido | — 🟢 |
| Faixa não publicada | Veredito `INCONCLUSIVO`; **nenhum número inventado** | — 🟢 |
| Identidade ambígua | Veredito `INCONCLUSIVO` com os registros listados | — 🟢 |
| Endogamia / colapso | Aviso no lado documental | 🔴 **Não altera o veredito** — o cM é teto otimista (`L-17`) |
| Empate triplo no desempate de candidatos | O **menor `xref_id`** vence, sempre — comportamento estável entre processos e ordens de *pool* (corrigido em 2026-10-05) | — 🟢 |
| Requisição concorrente | — | Sem isolamento: estado global com 4 threads (`L-16`) |
| Erro inesperado | `"Ocorreu um erro: {e}"` na tela | Nada é registrado em log 🔴 |

---

## 9. Compatibilidade e versionamento

| Elemento do contrato | Estabilidade exigida | Consequência de mudar |
| --- | --- | --- |
| Valores de `action` e nomes dos campos | **Alta** | É a granularidade das units (endpoint) |
| Chave de evidência **(nome, kit)** | **Alta** | Somar kits é erro silencioso de dado |
| `totals.cm = None` com múltiplos kits | **Alta** | Trocar por soma produz um número que o sistema não pode afirmar |
| Os quatro estados e a ordem de conservadorismo | **Alta** | Muda o produto da unit; o template consome os literais |
| Ordem `documental primeiro` | Média | Muda a leitura da tela, não o resultado |
| Tabela do SCP 4.0 e a definição de faixa | **Alta** | Muda **todas** as janelas e, portanto, os vereditos |
| Limiar de 15 cM (segmento fraco) | Média | Heurística do projeto; altera avisos, não vereditos |
| Limiar de Jaccard `0,33` (`cM ≥ 150` e prenome não genérico) | **Alta** (a decisão) / **Média** (o número) | A decisão de relaxar é intencional; o **número é heurístico e ajustável** — não foi calibrado contra dados reais (2026-10-05) |
| Critério final do desempate (menor `xref_id`) | **Alta** | Removê-lo reintroduz o resultado não reprodutível entre execuções |
| Versão de `RapidFuzz` | **Alta** | Muda o matching **sem** mudar código (`L-19`) |

---

*Gerado pelo Reversa-Writer em 2026-10-05 (re-extração, nível completo).*

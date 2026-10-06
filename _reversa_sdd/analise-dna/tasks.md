# Unit `analise-dna` — Tarefas de Implementação

> Unit do tipo **endpoint** — `POST /` com `action=dna_analysis`.
> Re-extração de **2026-10-05** (nível **Completo**). Substitui as tasks de 2026-09-30, que não previam as três etapas separadas nem o confronto.
> Escala de confiança: 🟢 CONFIRMADO | 🟡 INFERIDO | 🔴 LACUNA

---

## Pré-requisitos

- [ ] Dependências **pinadas**: `pandas==3.0.3`, `thefuzz==0.22.1` (+ `RapidFuzz` e `python-Levenshtein` transitivas) 🟢
- [ ] Unit `upload-gedcom` implementada: `people`, `families`, `graph` e `child_to_family` publicados 🟢
- [ ] `documentary_relationship`, `family_navigation` e `path_finding` disponíveis (módulos de domínio compartilhados com `busca-caminho`) 🟢
- [ ] `mermaid_render.generate_mermaid_graph` disponível 🟢
- [ ] `text_cleaning` como autoridade única de limpeza de nome (ADR-07) e `number_format` como autoridade de exibição (ADR-20) 🟢
- [ ] **Atenção à divergência de ambiente:** o `.venv/` **não reproduz** o pin (`pandas` 3.0.6, `RapidFuzz` 3.14.6). O `RapidFuzz` **decide o matching**; executar no interpretador errado pode mudar resultado sem mudar código (`L-19`) 🟢
- [ ] **Não aplicável:** schema, migrations ou banco de dados 🟢

## Tarefas

> Cada tarefa referencia o arquivo do legado de onde o comportamento foi extraído.

### Entrada e pré-condições

- [ ] **T-01**, Validar o GEDCOM e **re-parsear** antes de ramificar por `action`
  - Origem no legado: `src/app.py:131-137`
  - Critério de pronto: sem `gedcom_filename` → `"Erro: Arquivo GEDCOM não encontrado."`; forma inválida ou arquivo removido → `"Erro: Arquivo '{valor}' não existe mais."`; caso contrário, árvore recarregada com `all_names` recalculado
  - Confiança: 🟢
  - ⚠️ O re-parse **precede** o despacho: é ele que decide sobre qual árvore a análise roda.

- [ ] **T-02**, Validar a presença do CSV, preservando a lista de nomes na tela
  - Origem no legado: `src/app.py:141-142`
  - Critério de pronto: ausência → `"Por favor, carregue o arquivo CSV de matches."` com `all_names` no contexto
  - Confiança: 🟢

- [ ] **T-03**, Localizar a pessoa-raiz por substring case-insensitive, avisando ambiguidade
  - Origem no legado: `src/core/dna_analysis.py:90-93`, `:146-153`
  - Critério de pronto: raiz inexistente → `ValueError("Seu nome '{root_name}' não foi encontrado no GEDCOM.")`; ambígua → usa o primeiro e emite aviso com a contagem e os ids
  - Confiança: 🟢

### Leitura tolerante do CSV

- [ ] **T-04**, Ler com recuo de encoding e normalizar os nomes de coluna
  - Origem no legado: `src/parsers/csv_ingest.py:140-154`
  - Critério de pronto: `utf-8` lido direto; `UnicodeDecodeError` cai para `latin-1`; nomes de coluna sem espaços nas pontas
  - Confiança: 🟢
  - ⚠️ O recuo é **apenas** em `UnicodeDecodeError`. Não estender para outros erros.

- [ ] **T-05**, Detectar o separador pelo cabeçalho, com empate na vírgula
  - Origem no legado: `src/parsers/csv_ingest.py:46`, `:76-90`
  - Critério de pronto: conta `,` `;` TAB `\|` na primeira linha não vazia; maior vence; empate → vírgula
  - Confiança: 🟢

- [ ] **T-06**, Localizar o cabeçalho com as **três guardas**
  - Origem no legado: `src/parsers/csv_ingest.py:51`, `:93-123`
  - Critério de pronto: número de campos **modal** entre linhas com ≥ 2 campos, frequência ≥ 2, primeira linha divergente, posição dentro das `LIMITE_DE_PREAMBULO` (10) primeiras; arquivo sem cabeçalho **não perde a linha 1**
  - Confiança: 🟢

- [ ] **T-07**, Reler descartando linhas irregulares e **publicar** o descarte em `df.attrs`
  - Origem no legado: `src/parsers/csv_ingest.py:126-137`, `:157-174`
  - Critério de pronto: `separador`, `encoding`, `linhas_antes_do_cabecalho`, `linhas_ignoradas` (1-based) e `erro_de_leitura` disponíveis; a análise prossegue
  - Confiança: 🟢
  - ⚠️ `attrs` é o canal **por contrato**: trocar o retorno por tupla quebraria `dna_analysis` e o `__all__`.

### Agregação e evidência genética

- [ ] **T-08**, Detectar as colunas por papel
  - Origem no legado: `src/parsers/csv_ingest.py:185-194`; `src/core/genetic_evidence.py:46-81`
  - Critério de pronto: nome, cM, ID, e-mail, kit, SNPs, cromossomo, início, fim e fonte conforme as regras de cada papel
  - Confiança: 🟢

- [ ] **T-09**, Construir a chave de agrupamento e **somar** o cM, sem arredondar
  - Origem no legado: `src/parsers/csv_ingest.py:198-222`
  - Critério de pronto: chave = `norm_name(demojibake(nome))` + `" | "` + cauda (id em maiúsculas, ou e-mail normalizado, ou nada); um registro por chave; `map(str)` no lugar de `astype(str)`
  - Confiança: 🟢

- [ ] **T-10**, Construir a evidência por **(nome, kit)**
  - Origem no legado: `src/core/genetic_evidence.py:115-166`
  - Critério de pronto: `evidencias[nome][kit]`; sem coluna de kit o e-mail assume; sem ambos a chave é `SEM-KIT`; `total_cm` somado **sem `round`**
  - Confiança: 🟢

- [ ] **T-11**, Derivar os agregados por kit e emitir os avisos
  - Origem no legado: `src/core/genetic_evidence.py:180-209`, `:221-250`
  - Critério de pronto: segmentos ordenados por cM decrescente; cromossomos ordenados; maior segmento abaixo de **15 cM** → `weak_segment` + aviso `segmento_fraco`; mais de um kit → `multiplos_kits`; sem evidência → `available: False` + `sem_evidencia`
  - Confiança: 🟢
  - ⚠️ O limite de 15 cM é **heurística do projeto**, não da fonte (ADR-19).

- [ ] **T-12**, Consolidar a evidência da pessoa com `evidence_for`, **sem somar kits**
  - Origem no legado: `src/core/genetic_evidence.py:214-234`
  - Critério de pronto: um kit → `totals.cm` é o cM do kit; mais de um → `totals.cm` é **`None`** e `totals.cm_por_kit` traz cada valor separado; kits ordenados por cM decrescente
  - Confiança: 🟢

### Normalização, índices e matching

- [ ] **T-13**, Implementar a normalização e a decomposição de nomes
  - Origem no legado: `src/core/name_normalization.py:52-122`
  - Critério de pronto: `norm_name`, `split_name_pt`, `surnames_set`, `surname_core_tokens`, `drop_short_tokens`, `token_prefixes`, `soft_prefix_jaccard`, `top_given_tokens`
  - Confiança: 🟢

- [ ] **T-14**, Construir os índices do GEDCOM e o cache de atributos
  - Origem no legado: `src/core/matching.py:27-59`
  - Critério de pronto: `ged_index` (nome normalizado → ids), `surname_index` (sobrenome → ids) e `features[pid]` com `norm`, `given_tokens`, `surnames` (set), `surnames_list` e `tokens` (set)
  - Confiança: 🟢
  - ⚠️ **Não construir `given_index`**: foi removido por prova de morte (`OPP-20260929-32Q7`). O que existe é o cache `features`.

- [ ] **T-15**, Implementar o casamento exato e o *pool* de candidatos por sobrenome
  - Origem no legado: `src/core/matching.py:64-84`
  - Critério de pronto: acerto exato devolve a lista do índice com `reason=None`; sem exato, monta o *pool* por sobrenome e, se vazio, por prefixos de 3 caracteres; *pool* vazio → `"sem candidatos por sobrenome (abreviação/corrupção?)"`
  - Confiança: 🟢

- [ ] **T-16**, Implementar o scoring e o desempate
  - Origem no legado: `src/core/matching.py:99-112`
  - Critério de pronto: `score = round(0.55*s_token + 0.25*s_part + 0.20*s_given + (8*inter − 4*common_penalty), 2)`; desempate inter → given → score
  - Confiança: 🟢
  - ⚠️ A comparação é **estrita** — é justamente o que produz o desempate não determinístico do `T-30`.

- [ ] **T-17**, Implementar o filtro anti-falso-positivo e a interseção mínima adaptativa
  - Origem no legado: `src/core/matching.py:122-128`
  - Critério de pronto: interseção zero sem acerto de sufixo → rejeita com `"sem sobrenome em comum (filtro anti-falso-positivo)"`; prenome genérico com ≥ 2 sobrenomes eleva a exigência de 1 para 2
  - Confiança: 🟢

- [ ] **T-18**, Implementar o limiar de Jaccard com o relaxamento condicional
  - Origem no legado: `src/core/matching.py:130-136`
  - Critério de pronto: 0,50 por padrão com ≥ 2 sobrenomes; **0,33 somente** quando `cM ≥ 150` **e** o prenome não é genérico
  - Confiança: 🟢
  - ⚠️ Decisão intencional do usuário (2026-08-03). O **número** 0,33 continua sem medição registrada (`L-14`).

- [ ] **T-19**, Implementar os cinco ramos de aceitação, o ramo de prefixo e o rebaixamento do nome do meio
  - Origem no legado: `src/core/matching.py:138-166`
  - Critério de pronto: genérico `inter≥2 / jacc≥0,67 / score≥100`; não genérico `inter≥2 / jacc≥0,50 / given≥85 / score≥80`; `inter≥1 / jacc≥0,80 / score≥86`; `given≥90 / score≥92`; `given≥95 / score≥88`; prefixo de sobrenome com `given≥90 / score≥86`; primeiro verdadeiro vence; conflito de meio exige `score≥96` e `given≥92`
  - Confiança: 🟢
  - ⚠️ **Não criar constantes nomeadas** `HARD_MIN`/`GIVEN_MIN` (ADR-08).

- [ ] **T-20**, Garantir que o cM **não** decida a aceitação
  - Origem no legado: `src/core/matching.py:134`; teste `test_limiar_de_cm_nao_muda_a_decisao`
  - Critério de pronto: alterar o cM abaixo de 150 não muda a decisão de aceitação para um mesmo par de nomes
  - Confiança: 🟢

### Parentesco documental, possibilidades e confronto

- [ ] **T-21**, Obter o parentesco documental por candidato e escolher o **primeiro com caminho**
  - Origem no legado: `src/core/dna_analysis.py:187-196`
  - Critério de pronto: dossiê de homônimos calculado **uma vez por nome**; primeiro candidato com `path` vence; sem nenhum, usa o primeiro da lista; o resultado sai marcado como identidade ambígua quando for o caso
  - Confiança: 🟢

- [ ] **T-22**, Traduzir o cM em **lista** de possibilidades pela tabela publicada
  - Origem no legado: `src/core/relationship_hypotheses.py:106-205`
  - Critério de pronto: 27 relações publicadas; candidatas ordenadas por distância da média e, em empate, pelo nome; **sempre lista**, inclusive vazia; confiança `indeterminada` / `baixa` / `muito baixa` como heurística **do projeto**
  - Confiança: 🟢

- [ ] **T-23**, Tratar as relações **não publicadas** por envoltória de meioses
  - Origem no legado: `src/core/relationship_hypotheses.py:96-137`
  - Critério de pronto: `1C4R`, `1C5R`, `1C6R`, `3C2R` e os bisavós distantes **não recebem número inventado**; a janela é a envoltória das publicadas com o mesmo número de meioses; sem publicada naquele número, não há janela
  - Confiança: 🟢

- [ ] **T-24**, Decidir a janela esperada do parentesco documental
  - Origem no legado: `src/core/evidence_comparison.py:116-147`
  - Critério de pronto: faixa da relação exata → `method = "scp40:<nome>"`; senão envoltória → `method = "scp40:meioses=<n>"` com a nota explicando; senão `None` com o motivo
  - Confiança: 🟢

- [ ] **T-25**, Avaliar cada kit e determinar o estado final
  - Origem no legado: `src/core/evidence_comparison.py:75-113`, `:216-238`
  - Critério de pronto: dentro da janela → `COMPATIVEL`; fora com sobreposição → `POSSIVEL` (citando a relação vizinha mais próxima da média); fora sem sobreposição → `CONFLITANTE`; `total_cm` ausente → `INCONCLUSIVO`; estado final = **o mais conservador** na ordem `CONFLITANTE > POSSIVEL > COMPATIVEL > INCONCLUSIVO`; `per_kit` sempre preenchido
  - Confiança: 🟢

- [ ] **T-26**, Aplicar as guardas de `INCONCLUSIVO` e o rol de causas
  - Origem no legado: `src/core/evidence_comparison.py:161-208`, `:232-235`
  - Critério de pronto: `status` nasce `INCONCLUSIVO` e nenhuma guarda o altera; sem DNA / sem caminho / identidade ambígua / sem faixa publicada retornam sem veredito; `CONFLITANTE` recebe **12** causas e `POSSIVEL` recebe **9**
  - Confiança: 🟢

### Saída

- [ ] **T-27**, Ordenar os resultados com **documental primeiro**
  - Origem no legado: `src/core/dna_analysis.py:220-230`
  - Critério de pronto: chave `(0 se tem caminho senão 1, −cM)`; documentado que **não é ordem de confiança**
  - Confiança: 🟢

- [ ] **T-28**, Montar o item de resultado com os quatro eixos lado a lado
  - Origem no legado: `src/core/dna_analysis.py:204-218`
  - Critério de pronto: `documentary`, `genetic_evidence`, `hypotheses`, `comparison`, `observations` deduplicadas e `warnings` concatenados; `cm` é o **do kit**
  - Confiança: 🟢

- [ ] **T-29**, Montar a mensagem final e a auditoria de descartes
  - Origem no legado: `src/core/dna_analysis.py:174-180`, `:231-235`
  - Critério de pronto: `"{n} conexões encontradas. {m} descartadas."`; descartes com `csv_name`, `kit`, `cm` e `motivo` **nunca vazio** (`"não encontrado"` como padrão); sem resultados, os avisos do arquivo são anexados à mensagem
  - Confiança: 🟢

- [ ] **T-30**, Tratar exceções com erro amigável na rota
  - Origem no legado: `src/app.py:158-159`
  - Critério de pronto: exceção → `"Ocorreu um erro: {e}"` com `success=False`, sem derrubar a aplicação
  - Confiança: 🟢

### Divergências deliberadas do legado

> Estas tarefas **não** preservam comportamento. A primeira foi decidida pelo usuário e **ainda não foi implementada**; a segunda já está executada.

- [x] **T-31**, Acrescentar critério final **determinístico** ao desempate de candidatos ✅ **EXECUTADO em 2026-10-05**
  - Origem no legado: `src/core/matching.py:73`, `:91`, `:103-105` — onde empates exatos caíam na ordem de iteração de um `set`
  - Critério de pronto: empate exato nos três critérios escolhe sempre o **mesmo** candidato, com o *pool* inserido em **qualquer ordem**
  - Confiança: 🟢
  - Decisão do usuário: `questions.md#pergunta-4` (2026-09-30) — "precisa ser determinístico"; retomada e **autorizada a corrigir o legado** em `questions.md#pergunta-1` (2026-10-05)
  - Alinha com: `RF-26` em `requirements.md`; testes `TT-15`; `adrs/23`
  - **O que foi feito:** quarto critério no desempate de `match_candidates` — o **menor `xref_id`** lexicográfico vence o empate triplo (`src/core/matching.py:107-111`); comentário no código registra a decisão e o motivo
  - **Verificação:** `python -m pytest tests/test_characterization_matching.py -q` → **24 passam**, incluindo os **2 testes novos**; a suíte completa passou de 175 para **178 itens**
  - ⚠️ **Segunda divergência deliberada do legado, e a primeira que muda comportamento:** nos casos de empate triplo o vencedor pode ser outro. Fora do empate, nada muda

- [x] **T-32**, Declarar as 9 faixas de cM como heurística e **retirá-las do fluxo** ✅
  - Origem no legado: `src/core/cm_estimator.py:1`, `:21`; `src/core/dna_analysis.py:25-30`
  - Critério de pronto: o módulo declara "LEGADO, fora do fluxo"; nem o fluxo nem a interface o usam; permanece reexportado apenas para a suíte e o harness
  - Confiança: 🟢
  - Decisão do usuário: `questions.md#pergunta-5` — as faixas foram **escritas à mão**; a sobreposição de até 4× é consequência do método
  - Alinha com: `RF-25`; `adrs/19`

## Tarefas de Teste

- [ ] **TT-01**, Leitura em `utf-8` e em `latin-1` 🟢
- [ ] **TT-02**, Detecção de separador, incluindo o empate na vírgula 🟢
- [ ] **TT-03**, Localização do cabeçalho sob preâmbulo, e **sem** perder a linha 1 de um arquivo sem cabeçalho 🟢
- [ ] **TT-04**, Linha torta: análise prossegue e o descarte é publicado com os números de linha 🟢
- [ ] **TT-05**, Detecção de colunas por papel 🟢
- [ ] **TT-06**, Agregação somando cM de segmentos duplicados 🟢
- [ ] **TT-07**, Evidência por (nome, kit): dois kits do mesmo nome produzem **duas** evidências, com `totals.cm = None` 🟢
- [ ] **TT-08**, `segmento_fraco` marcado quando o maior segmento é < 15 cM 🟢
- [ ] **TT-09**, O cM **não** é arredondado no núcleo (contrato congelado em `tests/test_formatacao_cm.py`) 🟢
- [ ] **TT-10**, Happy path de ponta a ponta, com os quatro eixos preenchidos 🟢
- [ ] **TT-11**, Filtro anti-falso-positivo rejeita com o motivo correto 🟢
- [ ] **TT-12**, Raiz não encontrada e colunas ausentes viram erro amigável 🟢
- [ ] **TT-13**, Caracterização do pipeline e da decisão de matching 🟢
- [ ] **TT-14**, **O limiar de cM não muda a decisão por si só** 🟢
- [x] **TT-15**, Determinismo do desempate ✅ **implementado** como `test_desempate_escolhe_o_menor_xref_id` (parametrizado nas duas ordens de *pool*) e `test_desempate_nao_depende_da_ordem_do_pool` 🟢
  - ⚠️ **Desenhado sem subprocesso, de propósito.** Duas execuções com `PYTHONHASHSEED` diferente provariam a mesma coisa de forma **indireta** e dependente de o empate acontecer por acaso. Montar dois candidatos **idênticos** — que empatam nos três critérios por construção — e afirmar o vencedor com o *pool* nas duas ordens prova a propriedade **diretamente**, e ainda documenta o critério escolhido
- [ ] **TT-16**, Confronto: os quatro estados, a sobreposição de faixas, a envoltória por meioses e a agregação conservadora entre kits (`tests/test_confrontacao_gedcom_dna.py`, 922 linhas) 🟢
- [ ] **TT-17**, `possible_relationships` devolve **lista vazia** para `cM ≤ 0` ou não numérico — e **não** o literal de relação distante 🟢
- [ ] **TT-18**, Relação não publicada (`1C6R`) não inventa número e cai em `INCONCLUSIVO` quando não há meioses publicadas 🟢

## Tarefas de Migração de Dados

**Não aplicável** — sem banco de dados e sem volume a migrar. 🟢

## Ordem Sugerida

1. **T-13 (normalização) primeiro.** Todas as tarefas de matching dependem dela, e ela deve vir de `text_cleaning` como autoridade única.
2. **T-04 a T-09 (leitura, agregação e colunas).** Sem dados normalizados não há o que casar.
3. **T-10 a T-12 (evidência genética).** Independentes do matching; podem correr em paralelo a T-14.
4. **T-14 (índices).** Pré-requisito de T-15.
5. **T-15 a T-20 (matching).** Nesta ordem — cada tarefa depende da anterior. É o bloco mais crítico do sistema.
6. **T-21 (parentesco documental).** Depende de `documentary_relationship`, compartilhado com `busca-caminho`.
7. **T-22 a T-24 (possibilidades e janela).** Dependem de T-12.
8. **T-25 e T-26 (confronto).** Dependem de T-21, T-22 e T-23. **É o núcleo da unit.**
9. **T-27 a T-30 (saída e erro).** Depois do confronto.
10. **T-31 (determinismo)** pode ser feita em paralelo ao bloco de matching; é pequena e localizada. **T-32 já está executada.**
11. **Bloqueios:** T-21 depende da unit `busca-caminho` (módulos de parentesco); nada aqui funciona sem `upload-gedcom`; `<unit>` de DNA não bloqueia as outras.

## Lacunas Pendentes (🔴)

- ✅ **`T-31` / `RF-26` — determinismo EXECUTADO em 2026-10-05.** O menor `xref_id` decide o empate triplo; 2 testes novos protegem a propriedade. A divergência entre decisão humana e código está **fechada** (`L-15`). Permanece apenas o registro de que **é uma divergência deliberada de comportamento**.
- ✅ **`L-14` FECHADA em 2026-10-05:** o valor **0,33** foi um **chute que funcionou na prática**, e não um número calibrado contra dados reais. A decisão de manter o relaxamento continua 🟢; o que muda é que o número passa a ser declarado **heurístico e ajustável** em vez de literal com aparência de calibração.
- **`L-17`:** endogamia e colapso de pedigree não entram na decisão do estado. O cM lido é um teto otimista nesses casos.
- **`L-18`:** as relações mais distantes não são publicadas na versão 4.0 — justamente onde o caso real cai.
- **`L-19`:** a divergência de `RapidFuzz` entre o pin e o `.venv` pode mudar o matching sem mudar código.
- **`L-08`:** cobertura de exportadores de CSV — a regex de ID é específica de um padrão, sem prova de generalidade.
- **`E-03`:** a sentinela `SEM-KIT` pode colidir com um kit literalmente chamado `SEM-KIT`. Não há decisão registrada.
- ✅ **Já decididas, não são pendências:** regras de aceitação definitivas (2026-08-03); relaxamento de Jaccard intencional (2026-08-03); faixas de cM como heurística e fora do fluxo (2026-09-30, executada); `HARD_MIN`/`GIVEN_MIN` não implementados (ADR-08).

---

*Gerado pelo Reversa-Writer em 2026-10-05 (re-extração, nível completo).*

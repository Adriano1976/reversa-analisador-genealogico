# Unit `analise-dna` — Tarefas de Implementação

> Spec gerada pelo Reversa-Writer na re-extração de **2026-10-10** (nível **Completo**). Substitui as tasks de 2026-10-05, que não previam a **fronteira de aplicação**, a **projeção pura**, a **persistência** nem a **tradução de erros tipados**.
> Cada tarefa cita o arquivo do legado de onde o comportamento foi extraído.
> Escala de confiança: 🟢 CONFIRMADO | 🟡 INFERIDO | 🔴 LACUNA

---

## Pré-requisitos

- [ ] Dependências **pinadas**: `pandas==3.0.6`, `thefuzz==0.22.1` (+ `RapidFuzz 3.14.6` e `python-Levenshtein 0.27.5` transitivas), `ged4py==0.5.5` 🟢
- [ ] Unit `upload-gedcom` implementada: a **árvore como valor** `(people, families, graph, child_to_family)` e a porta de armazenamento 🟢
- [ ] Unit `tela-de-entrada` implementada: `_arvore_do_formulario` (guarda de entrada) e a lista de CSVs escolhível 🟢
- [ ] `documentary_relationship` e `homonym_dossier` disponíveis — módulos de domínio **compartilhados** com `busca-caminho` 🟢
- [ ] Módulos de diagrama disponíveis (`resolvedor_de_diagrama` e a renderização Mermaid) 🟢
- [ ] A autoridade única de limpeza de nome e a de exibição de número (`ADR-07`, `ADR-20`) 🟢
- [ ] Para o **registro histórico**: `DATABASE_URL` e o driver `psycopg2-binary==2.9.13` — **ausente do `.venv/`**, que é o interpretador oficial da suíte e da paridade. Sem o driver, a persistência **fica desligada** e a análise não muda 🟢 / 🔴
- [ ] **Atenção à divergência de ambiente:** o `.venv/` **não reproduz** todos os pins. O `RapidFuzz` **decide o matching**: executar no interpretador errado pode mudar o resultado sem mudar uma linha de código (`L-19`) 🟢
- [ ] Schema do histórico aplicado a partir de `init.sql` (6 tabelas idempotentes) — **só** para o caminho de registro 🔴

## Tarefas

### Entrada e pré-condições

- [ ] T-01, Resolver a árvore do formulário **antes** de ramificar por `action`, sem reparsear duas vezes
  - Origem no legado: `src/app.py:406-413` (`_arvore_do_formulario`)
  - Critério de pronto: sem `gedcom_filename` → `"Erro: Arquivo GEDCOM não encontrado."`; forma inválida ou arquivo removido → `"Erro: Arquivo 'ROTULO' não existe mais."` com o **rótulo**, e não a referência; conteúdo ilegível → mensagem própria + log, nunca `500`
  - Confiança: 🟢

- [ ] T-02, Validar a presença do CSV, preservando a lista de nomes na tela
  - Origem no legado: `src/app.py:455-456`
  - Critério de pronto: ausência dos **dois** caminhos (arquivo e referência) → `"Por favor, carregue o arquivo CSV de matches."` com `all_names` e `gedcom_filename` no contexto
  - Confiança: 🟢

- [ ] T-03, Dar **precedência** à referência de CSV escolhida na lista, mantendo o campo **opcional**
  - Origem no legado: `src/app.py:442-453`
  - Critério de pronto: com a referência presente, o arquivo enviado é **ignorado**; sem ela, o caminho é exatamente o anterior — mesma gravação, mesma porta, mesma mensagem
  - Confiança: 🟢
  - ⚠️ O campo é **NOVO** em vez de reaproveitar `matches_csv`: reaproveitar apagaria a prova de que o caminho antigo continua igual, e é essa prova que a paridade e os testes de rota consomem

- [ ] T-04, Gravar o CSV pela mesma porta do GEDCOM, com `tipo="csv"` e **sem validação de conteúdo**, e responder à referência que não resolve
  - Origem no legado: `src/app.py:448-453`, `:467-472`; `src/ports/adaptadores.py:76`
  - Critério de pronto: referência não resolvida → `Erro: Arquivo 'X' não existe mais.`, com a tela utilizável; CSV sem validação de conteúdo **por decisão** (dívida #10)
  - Confiança: 🟢

- [ ] T-05, Aplicar ao CSV a mesma regra de reenvio, e **acrescentar** o aviso de substituição à mensagem do resultado
  - Origem no legado: `src/app.py:467-489`
  - Critério de pronto: reenviar um CSV de conteúdo novo deixa **uma** linha na aba de DNA; o aviso vem **depois** da mensagem do resultado e não a substitui
  - Confiança: 🟢

### Leitura tolerante do CSV

- [ ] T-06, Ler com recuo de encoding e normalizar os nomes de coluna
  - Origem no legado: `src/parsers/csv_ingest.py:147-154`, `:170`
  - Critério de pronto: `utf-8` lido direto; falha de codec cai para `latin-1`; nomes de coluna sem espaços nas pontas
  - Confiança: 🟢
  - ⚠️ O recuo é **apenas** no erro de codec, e **nenhuma exceção de domínio** intercepta a troca

- [ ] T-07, Detectar o separador pelo cabeçalho, com empate na vírgula
  - Origem no legado: `src/parsers/csv_ingest.py:detectar_separador`
  - Critério de pronto: conta `,` `;` TAB `\|` no cabeçalho; maior vence; empate → vírgula. **Nunca `csv.Sniffer`**
  - Confiança: 🟢

- [ ] T-08, Localizar o cabeçalho com as **três guardas**
  - Origem no legado: `src/parsers/csv_ingest.py:localizar_cabecalho`
  - Critério de pronto: número de campos **modal**, frequência ≥ 2, primeira linha divergente, posição dentro das 10 primeiras; arquivo sem cabeçalho **não perde a linha 1**
  - Confiança: 🟢

- [ ] T-09, Reler descartando linhas irregulares e **publicar** o descarte em `df.attrs`
  - Origem no legado: `src/parsers/csv_ingest.py:linhas_irregulares`, `read_csv_with_fallback`
  - Critério de pronto: `separador`, `encoding`, `linhas_antes_do_cabecalho`, `linhas_ignoradas` (1-based) e `erro_de_leitura` disponíveis; a análise prossegue
  - Confiança: 🟢
  - ⚠️ `attrs` é o canal **por contrato**: trocar o retorno por tupla quebraria o núcleo

- [ ] T-10, Levantar `CsvIlegivel` listando as tentativas
  - Origem no legado: `src/parsers/csv_ingest.py:178-183`
  - Critério de pronto: mensagem em português com as tentativas feitas e o que conferir no arquivo
  - Confiança: 🟢

### Agregação e evidência genética

- [ ] T-11, Detectar as colunas por papel
  - Origem no legado: `src/parsers/csv_ingest.py:detect_columns`; `src/core/genetic_evidence.py:detect_segment_columns`
  - Critério de pronto: nome, cM, ID (primeira com > 30 % em `[A-Z]{2}\d{7}`), e-mail (a **última** com `mail`), kit, SNPs, cromossomo, início, fim e fonte
  - Confiança: 🟢

- [ ] T-12, Construir a chave de agrupamento e **somar** o cM, sem arredondar
  - Origem no legado: `src/parsers/csv_ingest.py:aggregate_matches`
  - Critério de pronto: chave = nome normalizado + cauda (id em maiúsculas, e-mail normalizado, ou nada); um registro por chave; **sem `round`** no acumulado
  - Confiança: 🟢

- [ ] T-13, Construir a evidência por **(nome, kit)**, com o e-mail assumindo o papel de kit
  - Origem no legado: `src/core/genetic_evidence.py:build_genetic_evidence`
  - Critério de pronto: `evidencias[nome][kit]`; sem coluna de kit o e-mail assume; sem ambos a chave é a sentinela `" SEM-KIT"` **com espaço à esquerda** e sai o aviso `kit_ausente`
  - Confiança: 🟢
  - ⚠️ O espaço à esquerda é a defesa: a limpeza de valor do CSV faz `strip`, e o literal sem espaço colidia com um kit de verdade (`E-03`)

- [ ] T-14, Derivar os agregados por kit e emitir os avisos
  - Origem no legado: `src/core/genetic_evidence.py:build_genetic_evidence`
  - Critério de pronto: segmentos por cM decrescente; cromossomos por tamanho e valor; maior segmento abaixo de **15 cM** → `weak_segment` + aviso `segmento_fraco`; mais de um kit → `multiplos_kits`; sem evidência → `available: False` + `sem_evidencia`
  - Confiança: 🟢
  - ⚠️ O limite de 15 cM é **heurística do projeto**, não da fonte (`ADR-19`)

- [ ] T-15, Consolidar a evidência da pessoa com `evidence_for`, **sem somar kits**
  - Origem no legado: `src/core/genetic_evidence.py:evidence_for`
  - Critério de pronto: um kit → `totals.cm` é o cM do kit; mais de um → `totals.cm` é **`None`** e cada valor aparece separado
  - Confiança: 🟢

### Normalização, índices e matching

- [ ] T-16, Implementar a normalização e a decomposição de nomes
  - Origem no legado: `src/utils/name_keys.py:norm_name`; `src/core/name_normalization.py:split_name_pt`, `surname_core_tokens`, `soft_prefix_jaccard`
  - Critério de pronto: `STOP_WORDS` (6), `GENERIC_GIVENS` (20), `SURNAME_SUFFIXES` (5), `COMMON_SURNAMES` (**16 literais, 15 efetivas** — `souza` duplicada em `set`), `SURNAME_EQUIV`; prenome = primeiro token não genérico e não stop word; sobrenomes = **últimos 3** tokens úteis
  - Confiança: 🟢
  - ⚠️ `COMMON_SURNAMES` é um **`set` literal com `souza` duas vezes**: contar em execução dá 15 (o `set` colapsa na construção). Só a leitura do fonte revela os 16

- [ ] T-17, Construir os índices do GEDCOM e o cache de atributos
  - Origem no legado: `src/core/matching.py:build_ged_indexes`
  - Critério de pronto: `ged_index` (nome normalizado → ids), `surname_index` (sobrenome → ids) e `features[pid]` com `norm`, `given_tokens`, `surnames`, `surnames_list` e `tokens` — **uma vez por análise**
  - Confiança: 🟢
  - ⚠️ **Não construir `given_index`**: foi removido por prova de morte (`OPP-20260929-32Q7`)

- [ ] T-18, Implementar o casamento exato e o *pool* de candidatos por sobrenome
  - Origem no legado: `src/core/matching.py:match_candidates`
  - Critério de pronto: acerto exato devolve a lista do índice com `reason=None`; sem exato, *pool* por sobrenome e, se vazio, por prefixos de 3 caracteres; *pool* vazio → `"sem candidatos por sobrenome (abreviação/corrupção?)"`
  - Confiança: 🟢

- [ ] T-19, Implementar o scoring e o desempate em **quatro** níveis
  - Origem no legado: `src/core/matching.py:116-125`
  - Critério de pronto: `score = round(0.55·token_sort + 0.25·partial + 0.20·given + (8·interseção − 4·comuns), 2)`; desempate inter → given → score → **menor `xref_id`**
  - Confiança: 🟢
  - ⚠️ O quarto critério é o que torna a escolha independente da ordem de iteração do `set` — **é a correção de determinismo implementada em 2026-10-05** (`BR-D-63`)

- [ ] T-20, Implementar o filtro anti-falso-positivo e a interseção mínima adaptativa
  - Origem no legado: `src/core/matching.py:137`
  - Critério de pronto: interseção zero sem acerto de sufixo → rejeita com `"sem sobrenome em comum (filtro anti-falso-positivo)"`; prenome genérico com ≥ 2 sobrenomes eleva a exigência de 1 para 2
  - Confiança: 🟢

- [ ] T-21, Implementar o limiar de Jaccard com o relaxamento condicional
  - Origem no legado: `src/core/matching.py`
  - Critério de pronto: 0,50 por padrão com ≥ 2 sobrenomes; **0,33 somente** quando `cM ≥ 150` **e** o prenome não é genérico
  - Confiança: 🟢
  - ⚠️ Decisão intencional do usuário (2026-08-03). O **número** 0,33 continua sendo heurística sem calibração (`L-14`)

- [ ] T-22, Implementar os cinco ramos de aceitação, o ramo de prefixo e o rebaixamento do nome do meio
  - Origem no legado: `src/core/matching.py:140-178`
  - Critério de pronto: genérico `inter≥2 / jacc≥0,67 / score≥100`; não genérico `inter≥2 / jacc≥0,50 / given≥85 / score≥80`; `inter≥1 / jacc≥0,80 / score≥86`; `given≥90 / score≥92`; `given≥95 / score≥88`; prefixo de sobrenome com `given≥90 / score≥86`; primeiro verdadeiro vence; conflito de meio exige `score≥96` e `given≥92`; o motivo da recusa carrega `given`, `final`, `inter` e `jacc`
  - Confiança: 🟢
  - ⚠️ **Não criar constantes nomeadas** `HARD_MIN`/`GIVEN_MIN` (`ADR-08`)

- [ ] T-23, Garantir que o cM **não** decida a aceitação
  - Origem no legado: `src/core/matching.py`; teste `test_limiar_de_cm_nao_muda_a_decisao`
  - Critério de pronto: alterar o cM abaixo de 150 não muda a decisão de aceitação para um mesmo par de nomes
  - Confiança: 🟢

### Parentesco documental, possibilidades e confronto

- [ ] T-24, Obter o parentesco documental por candidato e escolher o **primeiro com caminho**
  - Origem no legado: `src/core/dna_analysis.py:205-230`
  - Critério de pronto: dossiê de homônimos calculado **uma vez por nome** e parentesco **uma vez por pessoa**; primeiro candidato com `path` vence; sem nenhum, usa o primeiro da lista; o resultado sai marcado como identidade ambígua quando for o caso
  - Confiança: 🟢

- [ ] T-25, Traduzir o cM em **lista** de possibilidades pela tabela publicada
  - Origem no legado: `src/core/relationship_hypotheses.py:possible_relationships`
  - Critério de pronto: **27** relações publicadas; candidatas ordenadas por distância da média e, em empate, pelo nome em inglês; **sempre lista**, inclusive vazia; confiança `indeterminada` / `baixa` / `muito baixa` como heurística **do projeto**
  - Confiança: 🟢

- [ ] T-26, Tratar as relações **não publicadas** por envoltória de meioses
  - Origem no legado: `src/core/relationship_hypotheses.py:meioses_window`, `SCP40_NOT_PUBLISHED`
  - Critério de pronto: as **6** relações não publicadas (`1C4R`, `1C5R`, `1C6R`, `3C2R` e os bisavôs distantes) **não recebem número inventado**; a janela é a envoltória das publicadas com o mesmo número de meioses; sem publicada naquele número, não há janela
  - Confiança: 🟢

- [ ] T-27, Decidir a janela esperada do parentesco documental
  - Origem no legado: `src/core/evidence_comparison.py:_janela_do_documental`
  - Critério de pronto: faixa da relação exata → `method = "scp40:<nome>"`; senão envoltória → `method = "scp40:meioses=<n>"` com a nota explicando; senão nada, com o motivo
  - Confiança: 🟢

- [ ] T-28, Avaliar cada kit e determinar o estado final
  - Origem no legado: `src/core/evidence_comparison.py:_avaliar_kit`, `compare`
  - Critério de pronto: dentro da janela → `COMPATIVEL`; fora com sobreposição → `POSSIVEL`; fora sem sobreposição → `CONFLITANTE`; `total_cm` ausente → `INCONCLUSIVO`; estado final = **o mais conservador** (`CONFLITANTE > POSSIVEL > COMPATIVEL > INCONCLUSIVO`); `per_kit` sempre preenchido
  - Confiança: 🟢
  - ⚠️ **Não usar a distância em meioses como critério.** O parâmetro `meioses_documental` de `_avaliar_kit` **existe e não é lido** — não reintroduzir o critério por ele

- [ ] T-29, Aplicar as guardas de `INCONCLUSIVO` e o rol de causas
  - Origem no legado: `src/core/evidence_comparison.py:compare`
  - Critério de pronto: `status` nasce `INCONCLUSIVO` e nenhuma guarda o altera; sem DNA / sem caminho / identidade ambígua / sem faixa publicada retornam sem veredito; `CONFLITANTE` recebe **12** causas e `POSSIVEL` recebe **8**
  - Confiança: 🟢
  - ⚠️ **8, e não 9.** Medido por importação: `CAUSAS_POSSIVEIS[:1] + [3:8] + [10:]` = 1 + 5 + 2. O catálogo do Arqueólogo diz 9 e está errado

### Saída

- [ ] T-30, Ordenar os resultados com **documental primeiro**
  - Origem no legado: `src/core/dna_analysis.py:_ordem`
  - Critério de pronto: chave `(0 se tem caminho senão 1, −cM)`; documentado que **não é ordem de confiança**
  - Confiança: 🟢

- [ ] T-31, Montar o item de resultado com os quatro eixos lado a lado, o diagrama e as observações deduplicadas
  - Origem no legado: `src/core/dna_analysis.py:_montar_diagrama`, `_observacoes`
  - Critério de pronto: `documentary`, `genetic_evidence`, `hypotheses`, `comparison`, `observations` deduplicadas na ordem documental → genética → confronto → avisos; `cm` é o **do kit**; diagrama **`None`** quando não há caminho; resolvedor montado **uma vez por análise**
  - Confiança: 🟢

- [ ] T-32, Montar a mensagem final e a auditoria de descartes
  - Origem no legado: `src/core/dna_analysis.py:dna_analysis`
  - Critério de pronto: `"N conexões encontradas. M descartadas."`; descartes com `csv_name`, `kit`, `cm` e `motivo` **nunca vazio** (`"não encontrado"` como padrão); sem resultados, os avisos do arquivo são anexados à mensagem
  - Confiança: 🟢

### Fronteira: exceções, tradução e projeção *(novo em 2026-10-10)*

- [ ] T-33, Definir as **cinco exceções de domínio irmãs**
  - Origem no legado: `src/core/erros.py`
  - Critério de pronto: `ErroDeDominio(ValueError)` + `PessoaNaoEncontrada`, `GedcomNaoSuportado`, `DnaCsvSemColunas`, `CsvIlegivel`; **nenhum** tipo novo sem gatilho real; cada tipo carrega **apenas a mensagem do seu ponto de detecção**, e a moldura fica na tradução
  - Confiança: 🟢
  - ⚠️ A herança de `ValueError` é deliberada: preserva quatro asserções existentes da suíte. **Não** há quinto tipo (`ArmazenamentoInvalido` foi descartado por falta de gatilho)

- [ ] T-34, Implementar a **tabela de tradução** de exceção → literal de tela e status
  - Origem no legado: `src/application/traducao.py`
  - Critério de pronto: tabela de **funções** (não mapa de classe → constante), porque sete das nove mensagens congeladas **interpolam valores**; `404` para pessoa não encontrada, `422` para as demais; `GedcomNaoSuportado` devolve a **frase fixa** e a rede de segurança para tipo novo preserva `Ocorreu um erro: {e}`
  - Confiança: 🟢
  - ⚠️ O status **não tem consumidor** nesta onda (`BR-D-95`); ele existe e é testado para que a regra esteja em um lugar só quando a API chegar

- [ ] T-35, Implementar o caso de uso com `ResultadoDeAnalise` congelado
  - Origem no legado: `src/application/dna_analysis.py:41-57`, `:256-291`
  - Critério de pronto: dataclass congelada com `resultados`, `descartados`, `mensagem` e `aviso_de_persistencia=None`; **nenhuma** decisão de negócio na fronteira; `dono` na assinatura **sem** comportamento
  - Confiança: 🟢
  - ⚠️ Esta unit **não** tem desfecho de três valores (diferente de `busca-caminho`): ou levanta exceção de domínio, ou devolve resultado

- [ ] T-36, Implementar `projetar_analise` **pura** e as regras de junção de pessoas
  - Origem no legado: `src/application/dna_analysis.py:66-97`, `:222-253`
  - Critério de pronto: função pública, sem efeito, exercitável **sem banco**; ficha **completa** vence a identificação; identificação sem nome cede lugar a uma com nome; ficha sem `id` é descartada; raiz = `person_a.id` da **primeira** conexão; `match_file_ref` = **nome do arquivo armazenado**
  - Confiança: 🟢

- [ ] T-37, Implementar `_papeis_do_caminho` — papel **derivado**, sem `afinidade`
  - Origem no legado: `src/application/dna_analysis.py:100-126`
  - Critério de pronto: corte no ancestral comum; sem MRCA, corte no **penúltimo** nó; caminho de um nó só → `ascendente`; **`afinidade` nunca** atribuída aqui
  - Confiança: 🟢
  - ⚠️ Quem atribui `afinidade` é `busca-caminho` (`state-machines.md#4`). O recuo do penúltimo nó é **declarado**, não um palpite silencioso

- [ ] T-38, Implementar `_kits` e `_conexao` com pareamento **por índice** e defaults explícitos
  - Origem no legado: `src/application/dna_analysis.py:129-161`, `:192-219`
  - Critério de pronto: um `KitDaAnalise` por kit, com o cM **deste** kit; kit sem avaliação herda o estado **final** com `status_note` nulo; `ordinal` = posição **apresentada**; defaults `INCONCLUSIVO`, `not_found` e string vazia
  - Confiança: 🟢
  - ⚠️ O pareamento **não** pode ser por rótulo: dois kits com o mesmo nome — ou ambos sem kit — trocariam o cM de um com o estado do outro

- [ ] T-39, Carregar as descartes como **texto** e o resumo de contagens
  - Origem no legado: `src/application/dna_analysis.py:240-252`; `src/ports/__init__.py:DescartadoDaAnalise`
  - Critério de pronto: `reason` textual (default `"não encontrado"`), `ordinal`, `csv_name`, `kit`, `total_cm`; `accepted_count` e `skipped_count` iguais aos tamanhos das listas
  - Confiança: 🟢

### Registro histórico e persistência *(novo em 2026-10-10)*

- [ ] T-40, Definir a porta `RegistroDeAnalises` e o payload **plano**
  - Origem no legado: `src/ports/__init__.py`
  - Critério de pronto: `AnaliseParaRegistrar` (dado plano), `PessoaDaAnalise`, `KitDaAnalise`, `ConexaoDaAnalise` (21 campos, com `kits` e `caminho` como tuplas) e `DescartadoDaAnalise`; **nenhum** módulo de `core/` importa a porta
  - Confiança: 🟢

- [ ] T-41, Registrar **condicionalmente**, e nunca deixar a persistência bloquear o resultado
  - Origem no legado: `src/application/dna_analysis.py:271-284`
  - Critério de pronto: `registro is None` **ou** `referencia_da_arvore` vazia ⇒ não registra e a tela **não muda um byte**; exceção na projeção **ou** na gravação vira aviso `Histórico não registrado: …` e o resultado chega inteiro
  - Confiança: 🟢
  - ⚠️ A regra vale para as **duas metades**: uma falha aqui seria a persistência bloqueando a análise — exatamente o que ela não pode

- [ ] T-42, Implementar o adaptador Postgres: **nada na construção**, import **preguiçoso**, uma conexão e uma transação por análise
  - Origem no legado: `src/ports/adaptadores.py:243-297`
  - Critério de pronto: o construtor **só guarda a URL**; `import psycopg2` **dentro** do método; driver ausente → aviso, nunca exceção; `with conexao:` (commit/rollback do próprio driver) e `finally` fechando a conexão; **nunca levanta**
  - Confiança: 🟢
  - ⚠️ Sem o import preguiçoso, `import app` quebraria a suíte e a paridade **por ambiente**, porque o driver não está no `.venv/`

- [ ] T-43, Escrever respeitando as **chaves estrangeiras** e o schema de `init.sql`
  - Origem no legado: `src/ports/adaptadores.py:_escrever`; `init.sql`
  - Critério de pronto: ordem `dna_analysis` → `analysis_person` → `match_result` → `match_kit` / `match_path_node` → `skipped_match`; `is_affinity_anchor` **sempre** `FALSE`; `dono` vira `owner_id` e **nenhuma** consulta filtra por ele; `match_path_node` recebe também o `analysis_id`
  - Confiança: 🟢

- [ ] T-44, Montar o registrador na borda e declarar o **estado desabilitado**
  - Origem no legado: `src/app.py:160-161`
  - Critério de pronto: sem `DATABASE_URL` → `_REGISTRO = None`; com a variável → adaptador construído (sem conexão); a borda é o **único** ponto de montagem
  - Confiança: 🟢

- [ ] T-45, Renderizar o aviso de persistência **apenas quando houver aviso**
  - Origem no legado: `src/app.py:497`; `templates/index.html`
  - Critério de pronto: `aviso_de_persistencia` nulo ⇒ **nada** é renderizado; presente ⇒ faixa de aviso **não bloqueante**, ao lado do resultado
  - Confiança: 🟢

### Compatibilidade declarada

- [ ] T-46, Manter `cm_estimator` **fora do fluxo**, sem reexportação de compatibilidade
  - Origem no legado: `src/core/cm_estimator.py`
  - Critério de pronto: o módulo declara "LEGADO, fora do fluxo"; nem o fluxo nem a interface o usam; `cM ≤ 0` ou não numérico devolvem **lista vazia**; a superfície que o reexportava para `core/dna_analysis` **não existe mais**
  - Confiança: 🟢

## Tarefas de Teste

- [ ] TT-01, Leitura em `utf-8` e em `latin-1` 🟢
- [ ] TT-02, Detecção de separador, incluindo o empate na vírgula 🟢
- [ ] TT-03, Localização do cabeçalho sob preâmbulo, e **sem** perder a linha 1 de um arquivo sem cabeçalho 🟢
- [ ] TT-04, Linha torta: análise prossegue e o descarte é publicado com os números de linha 🟢
- [ ] TT-05, Detecção de colunas por papel 🟢
- [ ] TT-06, Agregação somando cM de segmentos duplicados 🟢
- [ ] TT-07, Evidência por (nome, kit): dois kits do mesmo nome produzem **duas** evidências, com `totals.cm = None` 🟢
- [ ] TT-08, `segmento_fraco` marcado quando o maior segmento é < 15 cM 🟢
- [ ] TT-09, O cM **não** é arredondado no núcleo (contrato congelado em `tests/test_formatacao_cm.py`) 🟢
- [ ] TT-10, Happy path de ponta a ponta, com os quatro eixos preenchidos 🟢
- [ ] TT-11, Filtro anti-falso-positivo rejeita com o motivo correto 🟢
- [ ] TT-12, Raiz não encontrada e colunas ausentes viram erro amigável 🟢
- [ ] TT-13, Caracterização do pipeline e da decisão de matching 🟢
- [ ] TT-14, **O limiar de cM não muda a decisão por si só** 🟢
- [x] TT-15, Determinismo do desempate ✅ **implementado** como `test_desempate_escolhe_o_menor_xref_id` (parametrizado nas duas ordens de *pool*) e `test_desempate_nao_depende_da_ordem_do_pool` 🟢
  - ⚠️ **Desenhado sem subprocesso, de propósito.** Duas execuções com `PYTHONHASHSEED` diferente provariam o mesmo de forma **indireta** e dependente de o empate acontecer por acaso. Montar dois candidatos **idênticos** — que empatam por construção — e afirmar o vencedor com o *pool* nas duas ordens prova a propriedade **diretamente**
- [ ] TT-16, Confronto: os quatro estados, a sobreposição de faixas, a envoltória por meioses e a agregação conservadora entre kits (`tests/test_confrontacao_gedcom_dna.py`) 🟢
- [ ] TT-17, `possible_relationships` devolve **lista vazia** para `cM ≤ 0` ou não numérico — e **não** o literal de relação distante 🟢
- [ ] TT-18, Relação não publicada (`1C6R`) não inventa número e cai em `INCONCLUSIVO` quando não há meioses publicadas 🟢
- [ ] TT-19, **Contagem das causas:** `CONFLITANTE` recebe 12 e `POSSIVEL` recebe **8** — e o teste falha se alguém "corrigir" para 9 (`tests/test_confrontacao_gedcom_dna.py`) 🟢
- [ ] TT-20, **Projeção sem banco:** `projetar_analise` roda sem `DATABASE_URL` e produz o payload esperado (`tests/test_projecao_da_analise.py`) 🟢
- [ ] TT-21, **Pareamento por índice:** dois kits de mesmo nome não trocam cM com estado; kit sem avaliação herda o estado final (`tests/test_projecao_da_analise.py`) 🟢
- [ ] TT-22, **Papel do caminho:** corte no MRCA, recuo no penúltimo nó e **ausência de `afinidade`** (`tests/test_projecao_da_analise.py`) 🟢
- [ ] TT-23, **Tradução de erros:** as quatro molduras medidas (com e sem o prefixo `Ocorreu um erro:`) e a frase fixa de conteúdo recusado (`tests/test_traducao_de_erros.py`) 🟢
- [ ] TT-24, **Persistência desabilitada e indisponível:** a tela não muda um byte; driver ausente e banco fora viram aviso, nunca exceção (`tests/test_persistencia_desabilitada.py`, `tests/test_persistencia_indisponivel.py`) 🟢
- [ ] TT-25, **Reenvio do CSV:** conteúdo novo substitui a versão anterior, e o aviso é **acrescentado** à mensagem do resultado (`tests/test_reenvio_do_csv.py`) 🟢
- [ ] TT-26, **Precedência do CSV da lista:** com referência e arquivo presentes, a referência vence (`tests/test_campo_de_escolha_do_csv.py`) 🟢
- [ ] TT-27, 🔴 **Caminho feliz de INSERT** — **não existe** e não pode existir no `.venv/` enquanto o driver não estiver instalado. Precisa rodar no contêiner (`L-28` / `X-05`)

## Tarefas de Migração de Dados

> ⚠️ **Mudou em 2026-10-10.** Até 2026-10-05 esta seção dizia "não aplicável — sem banco de dados". Agora **há** banco: `init.sql` cria 6 tabelas para o registro histórico. Não há **ETL** (o legado nunca teve dado persistido), mas há schema, e há uma questão de dado pessoal em aberto.

- [ ] TM-01, Aplicar `init.sql` de forma **idempotente** (6 tabelas, sem `DROP`): `dna_analysis`, `analysis_person`, `match_result`, `match_path_node`, `match_kit`, `skipped_match` 🟢
- [ ] TM-02, Conferir a **ordem de criação** das tabelas contra a ordem de escrita de `_escrever`: as FKs exigem a análise antes das pessoas e as pessoas antes das conexões 🟢
- [ ] TM-03, Decidir sobre **`owner_id`**: existe em `NOT NULL` e **não tem índice por dono**, porque nenhuma consulta filtra por ele. Criar o índice quando a consulta existir — não antes 🟡
- [ ] TM-04, 🔴 **Decidir retenção, expurgo e consentimento** para `analysis_person`, que guarda nome, sexo, nascimento, local e falecimento de pessoas **vivas**, sem prazo e sem base legal registrada (`L-29` / `P-07`). **Bloqueante para uso real com dado de terceiros.**
- [ ] TM-05, 🔴 **Decidir o que fazer com o retrato quando a árvore é apagada** da pasta: o histórico **não** é apagado junto, e desde a feature 008 o dado sobrevive ao arquivo de origem 🟡

## Ordem Sugerida

1. **T-16 (normalização) primeiro.** Todas as tarefas de matching dependem dela, e ela precisa vir da autoridade única de limpeza de nome.
2. **T-06 a T-12 (leitura, colunas e agregação).** Sem dados normalizados não há o que casar.
3. **T-13 a T-15 (evidência genética).** Independentes do matching; podem correr em paralelo a T-17.
4. **T-17 (índices).** Pré-requisito de T-18.
5. **T-18 a T-23 (matching).** Nesta ordem — cada tarefa depende da anterior. É o bloco mais crítico do sistema. **T-19 antes de tudo**: o quarto critério de desempate muda a escolha entre empatados, e escrevê-lo depois obrigaria a reconferir todos os testes de caracterização.
6. **T-24 (parentesco documental).** Depende dos módulos compartilhados com `busca-caminho`.
7. **T-25 a T-27 (possibilidades e janela).** Dependem de T-15.
8. **T-28 e T-29 (confronto).** Dependem de T-24, T-25 e T-26. **É o núcleo da unit.**
9. **T-30 a T-32 (saída).** Depois do confronto.
10. **T-33 e T-34 (exceções e tradução).** Antes do caso de uso: a fronteira precisa dos tipos para poder traduzir.
11. **T-35 a T-39 (caso de uso e projeção).** A projeção (T-36 a T-38) **antes** do registro (T-41): ela é pura e testável sem banco, e é ela que o registro consome.
12. **T-40 a T-45 (registro e persistência).** Por último: **nada aqui pode ser pré-requisito de nada**, por construção. T-45 é o único consumidor de tela.
13. **T-46 (compatibilidade)** em qualquer momento.
14. **Bloqueios:** T-24 depende da unit `busca-caminho`; nada aqui funciona sem `upload-gedcom` nem sem `tela-de-entrada`; T-41 depende de T-36; T-43 depende de TM-01.

## Lacunas Pendentes (🔴)

1. **`L-29` / `P-07` — dado pessoal sem retenção, expurgo ou consentimento** em `analysis_person`, incluindo pessoas vivas. **Bloqueante** para uso com dado de terceiros (TM-04).
2. **`L-28` / `X-05` — não há teste de caminho feliz de INSERT.** Enquanto o driver não estiver no interpretador oficial, erro de SQL, de FK ou de tipo só aparece no contêiner (TT-27).
3. **`L-17` — endogamia e colapso de pedigree não entram na decisão do estado.** O cM lido é um teto otimista nesses casos; o colapso é **detectado**, mas não altera o veredito.
4. **`L-18` — as relações mais distantes não são publicadas na 4.0**, justamente onde o caso real cai.
5. **`L-19` — a divergência de `RapidFuzz`** entre o pin e o `.venv` pode mudar o matching sem mudar código.
6. **`L-24` / `E-05` — a chave do cache de nomes do módulo documental pode não invalidar entre duas árvores**, e esta unit consome o dossiê de homônimos que ele alimenta. **[Verificar]** se a contaminação alcança os avisos desta unit.
7. **`L-30` do catálogo — `_avaliar_kit` recebe `meioses_documental` e não o usa.** Decidir: remover o parâmetro ou documentar por que ele fica.
8. **Duas análises iguais gravam duas linhas.** Nada deduplica uma análise repetida; não há decisão registrada. **[Verificar]**
9. **`L-08` — cobertura de exportadores de CSV:** a regex de ID é específica de um padrão, sem prova de generalidade.
10. **`E-03` — a sentinela `" SEM-KIT"` pode colidir** com um kit literalmente chamado `SEM-KIT`. Não há decisão registrada.
11. **Os quatro estados são nomes de classe CSS** e não há teste que amarre estado e folha de estilo.
12. **Os status HTTP da tradução não têm consumidor** nesta onda — decidir se ficam (documentados) ou saem até a API existir.

> ✅ **Já decididas, não são pendências:** regras de aceitação definitivas (2026-08-03); relaxamento de Jaccard intencional (2026-08-03, número declarado heurístico); faixas de cM fora do fluxo (2026-09-30, executada); `HARD_MIN`/`GIVEN_MIN` não implementados (`ADR-08`); determinismo do desempate (**implementado** em 2026-10-05, `L-15` fechada).

---

*Gerado pelo Reversa-Writer em 2026-10-10 (re-extração). Substitui a versão de 2026-10-05.*

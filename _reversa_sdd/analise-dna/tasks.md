# analise-dna, Tarefas de Implementação

> Unit do tipo **endpoint** — `POST /` com `action=dna_analysis`.
> Nível de documentação: **Essencial**. Escala: 🟢 CONFIRMADO | 🟡 INFERIDO | 🔴 LACUNA
> Re-extração de 2026-09-30. Substitui as tasks de 2026-08-03.

## Pré-requisitos

- [ ] Dependências: `pandas` 3.0.3, `thefuzz` 0.22.1 (+ `RapidFuzz` 3.14.5, `python-Levenshtein` 0.27.3) 🟢
- [ ] **Versões fixadas** (`==`) — não fixar aqui significa resultado de matching não reprodutível (RISK-006) 🟢
- [ ] Unit `upload-gedcom` implementada: as globais `people` e `graph` must estar publicadas 🟢
- [ ] `find_ancestral_path` e `generate_mermaid_graph` disponíveis (unit `busca-caminho` ou módulo equivalente) 🟢
- [ ] `domain.demojibake` e `domain.strip_bad_utf` disponíveis como autoridade única de limpeza de nome 🟢
- [ ] **Não aplicável:** schema/migrations de banco 🟢

## Tarefas

> Cada tarefa referencia o arquivo do legado de onde o comportamento foi extraído.

### Entrada e pré-condições

- [ ] **T-01**, Validar GEDCOM carregado: presença do nome, existência em disco e re-parse
  - Origem no legado: `analisador-genealogico/app.py:36-42`
  - Critério de pronto: sem `gedcom_filename` → `"Erro: Arquivo GEDCOM não encontrado."`; arquivo removido → `"Erro: Arquivo '{nome}' não existe mais."`; caso contrário, árvore recarregada
  - Confiança: 🟢

- [ ] **T-02**, Validar presença do CSV de matches, preservando a lista de nomes na tela
  - Origem no legado: `analisador-genealogico/app.py:46-47`
  - Critério de pronto: ausência → `"Por favor, carregue o arquivo CSV de matches."` com `all_names` presentes no contexto do template
  - Confiança: 🟢

- [ ] **T-03**, Localizar a pessoa-raiz por substring case-insensitive, usando o primeiro ID
  - Origem no legado: `analisador-genealogico/reconstructed/dna_analysis.py:346-349`
  - Critério de pronto: raiz inexistente → `ValueError("Seu nome '{root_name}' não foi encontrado no GEDCOM.")`; existente → `root_person_ids[0]`
  - Confiança: 🟢

### Leitura e agregação

- [ ] **T-04**, Ler o CSV com fallback de encoding e normalizar nomes de coluna
  - Origem no legado: `analisador-genealogico/reconstructed/dna_analysis.py:151-157`
  - Critério de pronto: UTF-8 lido direto; `UnicodeDecodeError` cai para `latin-1`; `df.columns` sem espaços nas pontas
  - Confiança: 🟢
  - ⚠️ O fallback é **apenas** em `UnicodeDecodeError`. Não estender para outros erros de parse.

- [ ] **T-05**, Detectar as colunas de Nome, cM, ID e e-mail
  - Origem no legado: `analisador-genealogico/reconstructed/dna_analysis.py:160-170`
  - Critério de pronto: nome em `Name`/`MatchedName`/`Nome`; cM em `cM`/`TotalCM`/`Total cM`; ID pela regex `[A-Z]{2}\d{7}` com corte de **30 %** dos valores; e-mail na **última** coluna contendo `mail`
  - Confiança: 🟢

- [ ] **T-06**, Construir `_group_key` e agregar somando cM
  - Origem no legado: `analisador-genealogico/reconstructed/dna_analysis.py:173-191`
  - Critério de pronto: chave = `norm_name(demojibake(nome))` + `" | "` + (ID **ou** e-mail normalizado, com ID tendo precedência); um registro por chave com cM **somado**
  - Confiança: 🟢

### Índices e matching

- [ ] **T-07**, Construir os índices do GEDCOM e o cache de atributos normalizados
  - Origem no legado: `analisador-genealogico/reconstructed/dna_analysis.py:198-230`
  - Critério de pronto: `ged_index` por nome normalizado, `surname_index` por sobrenome, `features[pid]` com `norm`, `given_tokens`, `surnames`, `surnames_list`, `tokens`
  - Confiança: 🟢
  - ⚠️ **Não construir `given_index`.** Esse índice existia na extração anterior e foi **removido por prova de morte** (`OPP-20260929-32Q7`): nenhum ponto do código o lia. O que existe hoje é o cache `features`.

- [ ] **T-08**, Implementar as funções de normalização e decomposição de nome
  - Origem no legado: `analisador-genealogico/reconstructed/dna_analysis.py:74-144`
  - Critério de pronto: `norm_name` (NFKD, sem diacríticos, minúsculas), `drop_short_tokens` (preserva `sa`/`sá`), `surname_core_tokens` (remove 5 sufixos), `split_name_pt`, `surnames_set`, `token_prefixes`, `soft_prefix_jaccard`
  - Confiança: 🟢

- [ ] **T-09**, Implementar o scoring difuso e o desempate triplo
  - Origem no legado: `analisador-genealogico/reconstructed/dna_analysis.py:262-277`
  - Critério de pronto: `score = round(0.55*s_token + 0.25*s_part + 0.20*s_given + (8*inter − 4*common_penalty), 2)`; desempate por `inter` → `given` → `score`
  - Confiança: 🟢

- [ ] **T-10**, Implementar o filtro anti-falso-positivo e a interseção mínima adaptativa
  - Origem no legado: `analisador-genealogico/reconstructed/dna_analysis.py:287-293`
  - Critério de pronto: interseção 0 sem acerto de sufixo → rejeita com motivo; prenome genérico + ≥ 2 sobrenomes eleva a exigência para 2
  - Confiança: 🟢

- [ ] **T-11**, Implementar o limiar de Jaccard com o relaxamento condicional
  - Origem no legado: `analisador-genealogico/reconstructed/dna_analysis.py:295-301`
  - Critério de pronto: limiar 0.5 por padrão com ≥ 2 sobrenomes; **0.33 somente** quando `cM ≥ 150` **e** prenome não-genérico
  - Confiança: 🟢
  - ⚠️ Decisão intencional do usuário (`questions.md#4`). Preservar exatamente; não "endurecer".

- [ ] **T-12**, Implementar os **6 ramos de aceitação**, na ordem exata
  - Origem no legado: `analisador-genealogico/reconstructed/dna_analysis.py:305-320`
  - Critério de pronto: `100/0.67` (genérico) → `80/85/0.50` → `86/0.80` → `92/90` → `88/95` → bônus de prefixo `86/90`; primeira condição verdadeira vence
  - Confiança: 🟢
  - ⚠️ **Não criar constantes nomeadas** `HARD_MIN`/`GIVEN_MIN` (ADR-08). Os literais ficam onde estão.

- [ ] **T-13**, Implementar o rebaixamento por conflito de nome do meio
  - Origem no legado: `analisador-genealogico/reconstructed/dna_analysis.py:322-326`
  - Critério de pronto: token do CSV que não é prenome nem sobrenome e é disjunto dos tokens do GEDCOM → exige `score ≥ 96` e `given ≥ 92`
  - Confiança: 🟢

### Saída

- [ ] **T-14**, Calcular o caminho ancestral até a raiz para o **primeiro** candidato aceito com caminho
  - Origem no legado: `analisador-genealogico/reconstructed/dna_analysis.py:374-389`
  - Critério de pronto: `break` no primeiro candidato com caminho; item de resultado com `match_name`, `cm`, `text_path`, `mermaid_data`, `relationships`, `csv_name`
  - Confiança: 🟢

- [ ] **T-15**, Registrar os descartes com o motivo específico
  - Origem no legado: `analisador-genealogico/reconstructed/dna_analysis.py:255, 289, 330-331, 391`
  - Critério de pronto: cada descarte traz `csv_name` e `motivo`, entre os 4 catalogados
  - Confiança: 🟢

- [ ] **T-16**, Implementar `get_relationships_by_cm` com contrato de **lista**
  - Origem no legado: `analisador-genealogico/reconstructed/dna_analysis.py:62-66`
  - Critério de pronto: `cM ≤ 0` ou não numérico → `[]`; dentro de faixas → lista das relações; fora de todas → `["Relação distante ou indeterminada"]`
  - Confiança: 🟢
  - ⚠️ **Não devolver o literal para `cM ≤ 0`.** Foi exatamente esse erro que a extração anterior cometeu e que o confronto com o oráculo corrigiu (`AMB-023`).

### Saída

- [ ] **T-17**, Ordenar por cM decrescente e montar a mensagem final
  - Origem no legado: `analisador-genealogico/reconstructed/dna_analysis.py:393-395`
  - Critério de pronto: ordenação por `cm` desc; mensagem `"{n} conexões encontradas. {m} descartadas."`
  - Confiança: 🟢

- [ ] **T-18**, Tratar exceções com erro amigável na rota
  - Origem no legado: `analisador-genealogico/app.py:62-63`
  - Critério de pronto: exceção → `"Ocorreu um erro: {e}"` com `success=False`, sem quebrar
  - Confiança: 🟢

### Correções decididas pelo usuário em 2026-09-30

> Estas duas tarefas **divergem de propósito** do legado. Todas as outras preservam comportamento; estas corrigem o que o usuário decidiu que não deve ser preservado.

- [ ] **T-19**, Acrescentar critério final **determinístico** ao desempate de candidatos
  - Origem no legado: `analisador-genealogico/reconstructed/dna_analysis.py:262`, `:274-277` — onde o legado deixa empates exatos caírem na ordem de iteração de `set`
  - Critério de pronto: duas execuções sobre a mesma entrada, com `PYTHONHASHSEED` diferente, escolhem o **mesmo** candidato; sugestão de critério final: menor `xref_id`
  - Confiança: 🟢
  - Decisão do usuário: `_reversa_sdd/questions.md#pergunta-4` — "precisa ser determinístico"
  - Alinha com: `RF-14` em `requirements.md`; teste `TT-13`

- [ ] **T-20**, Declarar as 9 faixas de cM como **heurísticas** e expô-las como parâmetro
  - Origem no legado: `analisador-genealogico/reconstructed/dna_analysis.py:30-40`
  - Critério de pronto: a tabela é configurável (não literal cravado) e a documentação declara ausência de fonte; a mecânica de devolver **lista** permanece intacta
  - Confiança: 🟡
  - Decisão do usuário: `_reversa_sdd/questions.md#pergunta-5` — as faixas foram **escritas à mão**, não calibradas; a sobreposição de até 4× é consequência disso
  - Alinha com: `RF-10a` em `requirements.md`

## Tarefas de Teste

O legado **já tem** estes testes:

- [ ] **TT-01**, Leitura UTF-8 e Latin-1 (`test_read_csv_utf8`, `test_read_csv_latin1`) 🟢
- [ ] **TT-02**, Detecção de colunas (`test_detect_columns`) 🟢
- [ ] **TT-03**, Agregação de segmentos duplicados somando cM (`test_aggregate_duplicated`) 🟢
- [ ] **TT-04**, Happy path de ponta a ponta (`test_dna_analysis_happy`) 🟢
- [ ] **TT-05**, Filtro anti-falso-positivo (`test_anti_false_positive`) 🟢
- [ ] **TT-06**, Raiz não encontrada (`test_root_not_found`) 🟢
- [ ] **TT-07**, Colunas ausentes (`test_missing_columns`) 🟢
- [ ] **TT-08**, Match aceito sem caminho ancestral (`test_match_without_path`) 🟢
- [ ] **TT-09**, Faixas de cM dentro e fora do intervalo (`test_relationships_by_cm`, `test_relationships_by_cm_out_of_range`) 🟢
- [ ] **TT-10**, **Caracterização do pipeline e da decisão de matching** (`test_pipeline_caracterizado`, `test_decisao_de_matching`) 🟢
- [ ] **TT-11**, **O limiar de cM não muda a decisão por si só** (`test_limiar_de_cm_nao_muda_a_decisao`) 🟢
- [ ] **TT-12**, Teste discriminante para `cM ≤ 0` devolvendo **lista vazia** (não coberto pelo legado — criar) 🟡
- [ ] **TT-13**, Teste de determinismo do desempate sob `PYTHONHASHSEED` variável (não coberto — cria, por causa do `L-13`) 🟡

## Tarefas de Migração de Dados

**Não aplicável** — sem banco de dados, sem volume a migrar. 🟢

## Ordem Sugerida

1. **T-08 (normalização) primeiro.** Todas as demais tarefas de matching dependem dela, e ela deve vir de `domain.py` como autoridade única.
2. **T-04 a T-06 (leitura e agregação).** Sem dados normalizados não há o que casar.
3. **T-07 (índices).** Pré-requisito de T-09.
4. **T-01 a T-03 (pré-condições).** Podem ser feitas em paralelo, mas são testáveis só com o núcleo pronto.
5. **T-09 a T-13 (matching).** Nesta ordem — cada tarefa depende da anterior. É o bloco mais crítico.
6. **T-14 a T-17 (saída).** Dependem do matching.
7. **T-19 (erro) por último.**
8. **T-18 (faixas de cM como parâmetro)** e **T-20/`RF-14` (determinismo)** podem ser feitas em paralelo ao bloco de matching, mas T-18 depende de T-16 estar pronto.
9. **Bloqueios:** T-14 depende de `find_ancestral_path` (unit `busca-caminho`); nada aqui funciona sem a unit `upload-gedcom`.

## Lacunas Pendentes (🔴)

- ✅ **L-13 RESOLVIDA em 2026-09-30:** o desempate **precisa ser determinístico** — decisão do usuário (`questions.md#pergunta-4`). Virou requisito `RF-14` em `requirements.md` e tarefas `T-19`/`TT-13`. **É a única divergência deliberada do legado em toda a re-extração.**
- ✅ **L-07 RESOLVIDA em 2026-09-30:** as faixas de cM foram **escritas à mão**, sem calibração — decisão do usuário (`questions.md#pergunta-5`). Virou `RF-10a` e tarefa `T-18`; a sobreposição de até 4× é consequência do método.
- **L-08:** cobertura dos exportadores de CSV — a regex de ID `[A-Z]{2}\d{7}` é específica. Confirmar quais exportadores precisam ser suportados.
- **L-14:** origem empírica do valor 0,33 no relaxamento de Jaccard — o usuário indicou ter a medição de calibração, mas ela **ainda não foi fornecida**. A decisão de manter o relaxamento é 🟢; o número segue 🔴 (`questions.md#pergunta-6`).
- **Já decididas, não são pendências:** regras de aceitação são definitivas (`questions.md#1`); relaxamento de Jaccard é intencional (`questions.md#4`); determinismo é exigido (`questions.md#pergunta-4`); faixas de cM são heurísticas (`questions.md#pergunta-5`).

---

*Gerado pelo Reversa-Writer em 2026-09-30 (re-extração).*

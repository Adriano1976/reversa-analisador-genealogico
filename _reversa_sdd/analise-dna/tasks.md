# Análise de DNA, Tarefas de Implementação

> Nível de documentação: **Essencial**
> Confiança: 🟢 CONFIRMADO | 🟡 INFERIDO | 🔴 LACUNA

## Pré-requisitos
- [ ] Dependências: `Flask`, `pandas`, `thefuzz`, `networkx`, `ged4py`
- [ ] Unit `upload-gedcom` implementada (grafo e globals disponíveis)

## Tarefas

> Cada tarefa referencia o arquivo do legado de onde o comportamento foi extraído.

- [ ] T-01, Validar GEDCOM carregado e re-parsear antes da análise
  - Origem no legado: `analisador-genealogico/app.py:576-582`
  - Critério de pronto: sem `gedcom_filename` → erro; com → `people`/`graph` recarregados
  - Confiança: 🟢

- [ ] T-02, Validar presença do CSV de matches
  - Origem no legado: `analisador-genealogico/app.py:586-587`
  - Critério de pronto: ausência → mensagem "Por favor, carregue o arquivo CSV de matches."
  - Confiança: 🟢

- [ ] T-03, Localizar pessoa-raiz por nome
  - Origem no legado: `analisador-genealogico/app.py:592-595`, `find_person_by_name` (`app.py:208-211`)
  - Critério de pronto: raiz inexistente → erro com o nome; existente → usa o primeiro ID
  - Confiança: 🟢

- [ ] T-04, Ler CSV com fallback de encoding UTF-8/Latin-1
  - Origem no legado: `analisador-genealogico/app.py:598-601`
  - Critério de pronto: ambos encodings são lidos sem exceção
  - Confiança: 🟢

- [ ] T-05, Identificar colunas de Nome, cM e ID/Email
  - Origem no legado: `analisador-genealogico/app.py:606-615`
  - Critério de pronto: `Name`/`MatchedName`/`Nome`, `cM`/`TotalCM`/`Total cM`, e ID regex `[A-Z]{2}\d{7}`
  - Confiança: 🟢

- [ ] T-06, Construir `_group_key` e agregar segmentos somando cM
  - Origem no legado: `analisador-genealogico/app.py:617-635`
  - Critério de pronto: um registro por match com cM somado
  - Confiança: 🟢

- [ ] T-07, Construir índices de nomes/sobrenomes/given do GEDCOM
  - Origem no legado: `analisador-genealogico/app.py:639-651`
  - Critério de pronto: `ged_index`, `surname_index`, `given_index` populados
  - Confiança: 🟢

- [ ] T-08, Implementar scoring e desempate do matching difuso
  - Origem no legado: `analisador-genealogico/app.py:700-724`
  - Critério de pronto: score `0.55*token + 0.25*part + 0.20*given + inter_bonus`; desempate inter>given>score
  - Confiança: 🟢

- [ ] T-09, Implementar regras de aceitação A/B/C/D e filtro anti-falso-positivo
  - Origem no legado: `analisador-genealogico/app.py:726-793`
  - Critério de pronto: candidatos rejeitados corretamente (interseção 0, dado genérico, Jaccard)
  - Confiança: 🟡 (regras complexas, exigem validação com dados reais)

- [ ] T-10, Calcular caminho ancestral até a raiz para candidatos aceitos
  - Origem no legado: `analisador-genealogico/app.py:803-820`, `find_ancestral_path` (`app.py:297-318`)
  - Critério de pronto: `path` e `common_ancestor` corretos; sem caminho → descartado
  - Confiança: 🟢

- [ ] T-11, Prever relação por faixa de cM e gerar Mermaid
  - Origem no legado: `analisador-genealogico/app.py:809`, `get_relationships_by_cm` (`app.py:169-173`), `generate_mermaid_graph` (`app.py:320-375`)
  - Critério de pronto: relação e diagrama renderizados no resultado
  - Confiança: 🟢

- [ ] T-12, Ordenar resultados por cM decrescente e exibir descartados
  - Origem no legado: `analisador-genealogico/app.py:824-833`
  - Critério de pronto: `results_list_sorted` e `skipped_matches` exibidos na UI
  - Confiança: 🟢

- [ ] T-13, Tratar exceções com erro amigável
  - Origem no legado: `analisador-genealogico/app.py:835-836`
  - Critério de pronto: exceção → mensagem sem crash
  - Confiança: 🟢

## Tarefas de Teste

- [ ] TT-01, Happy path: CSV válido com matches produz resultados ordenados por cM
- [ ] TT-02, Agregação: segmentos duplicados somam cM em um único registro
- [ ] TT-03, Encoding: CSV Latin-1 é lido via fallback
- [ ] TT-04, Anti-falso-positivo: match sem interseção de sobrenome é descartado
- [ ] TT-05, Raiz inexistente: erro exibido
- [ ] TT-06, Sem arquivo CSV: erro exibido
- [ ] TT-07, Match sem caminho ancestral: entra em `skipped_matches`

## Tarefas de Migração de Dados (se aplicável)

Não aplicável — sem banco de dados. 🟢

## Ordem Sugerida
1. T-01 a T-03 (validações de entrada) — contrato do fluxo.
2. T-04 a T-06 (leitura/agregação) — base de dados.
3. T-07 a T-09 (índices e matching) — núcleo de qualidade.
4. T-10 a T-12 (caminho, relação, saída).
5. T-13 (erro) e testes TT-01..TT-07.

## Lacunas Pendentes (🔴)
- Regras A/B/C/D de aceitação precisam de validação com amostra real de dados.
- Relaxamento de Jaccard para cM alto (0.5→0.33) é intencional?
- Detecção de ID por regex `[A-Z]{2}\d{7}` cobre todos os exportadores (GEDmatch etc.)?
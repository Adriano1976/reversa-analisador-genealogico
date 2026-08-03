# Busca de Caminho, Tarefas de Implementação

> Nível de documentação: **Essencial**
> Confiança: 🟢 CONFIRMADO | 🟡 INFERIDO | 🔴 LACUNA

## Pré-requisitos
- [ ] Dependências: `Flask`, `networkx`, `ged4py`
- [ ] Unit `upload-gedcom` implementada (grafo e globals disponíveis)

## Tarefas

> Cada tarefa referencia o arquivo do legado de onde o comportamento foi extraído.

- [ ] T-01, Validar GEDCOM carregado e re-parsear antes da busca
  - Origem no legado: `analisador-genealogico/app.py:576-582`
  - Critério de pronto: sem `gedcom_filename` → erro; com → `people`/`graph` recarregados
  - Confiança: 🟢

- [ ] T-02, Localizar as duas pessoas pelo nome
  - Origem no legado: `analisador-genealogico/app.py:843-853`, `find_person_by_name` (`app.py:208-211`)
  - Critério de pronto: IDs resolvidos; inexistente → "Pessoa 1/2 'X' não encontrada."; usa o primeiro ID
  - Confiança: 🟢

- [ ] T-03, Implementar busca de conexão direta por ancestral comum
  - Origem no legado: `analisador-genealogico/app.py:856-860`, `find_ancestral_path` (`app.py:297-318`)
  - Critério de pronto: caminho com `common_ancestor` e msg "Conexão direta encontrada (ancestral comum)."
  - Confiança: 🟢

- [ ] T-04, Implementar fallback de conexão indireta por afinidade
  - Origem no legado: `analisador-genealogico/app.py:863-870`, `find_indirect_path` (`app.py:281-294`)
  - Critério de pronto: sem direta → caminho por casamento/afinidade via `shortest_path` (máx. 40 hops), com compressão de famílias
  - Confiança: 🟢

- [ ] T-05, Renderizar caminho textual e diagrama Mermaid
  - Origem no legado: `analisador-genealogico/app.py:857-859`, `868-869`, `872-879`
  - Critério de pronto: `path_result` com `text_path` e `mermaid_data` (direto ou bridge) exibido
  - Confiança: 🟢

- [ ] T-06, Tratar ausência de conexão e exceções
  - Origem no legado: `analisador-genealogico/app.py:864-867`, `880-882`
  - Critério de pronto: sem conexão → "Nenhuma conexão encontrada entre 'X' e 'Y'."; exceção → erro amigável
  - Confiança: 🟢

## Tarefas de Teste

- [ ] TT-01, Conexão direta: duas pessoas com ancestral comum exibem caminho e Mermaid
- [ ] TT-02, Conexão indireta: fallback por afinidade exibe "Conexão indireta encontrada"
- [ ] TT-03, Pessoa inexistente: mensagem por pessoa exibida
- [ ] TT-04, Sem conexão: mensagem de nenhuma conexão
- [ ] TT-05, Pessoas idênticas: caminho trivial `(start, start)`

## Tarefas de Migração de Dados (se aplicável)

Não aplicável — sem banco de dados. 🟢

## Ordem Sugerida
1. T-01 e T-02 (validações de entrada).
2. T-03 (conexão direta) — caminho principal.
3. T-04 (fallback indireto) — depende do grafo e de `split_path_by_marriage`.
4. T-05 (renderização) e T-06 (erros).
5. Testes TT-01..TT-05.

## Lacunas Pendentes (🔴)
- Uso do primeiro ID em caso de homônimos — definir política de desambiguação.
- Cobertura de famílias adotivas/complexas no `find_ancestral_path`.
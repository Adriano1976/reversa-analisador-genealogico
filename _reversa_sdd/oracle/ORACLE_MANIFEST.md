---
schemaVersion: 1
generatedAt: "2026-09-28T04:32:00Z"
reversa:
  version: "1.2.58"
kind: oracle_manifest
producedBy: orchestrator
hash: "sha256:8b052746f0b14e51020b81852478164f646fa9401885c2a8d7295f079473babe"
---

# Oracle Manifest — Oráculo Congelado

> **Este é o artefato que torna a métrica primária do brief verificável.**
> Define, de forma imutável, **contra o que** a paridade será medida. Sem ele, a estratégia `Parallel Run` confirmada pelo usuário fica sem instrumento e o RISK-002 permanece materializado.

## ⚠️ Por que este oráculo precisou ser reconstruído

O pipeline foi escrito assumindo que `analisador-genealogico/app.py` **era** o legado. **Não é mais.**

| Fato | Evidência |
|---|---|
| O `app.py` atual tem **86 linhas** e é um **wrapper fino** | `analisador-genealogico/app.py:1-7` importa `reconstructed.dna_analysis`, `reconstructed.path_search` e `reconstructed.upload` |
| Ele foi reduzido de **887 → 86 linhas** num único commit | `git diff --stat e43ca22 HEAD -- analisador-genealogico/app.py` → **812 deleções, 11 inserções** |
| O commit que fez isso | `3ed0179 — feat: integrar módulos reconstruídos ao app Flask e reorganizar estrutura do projeto` |
| O monolito original está **íntegro** no git | `git show e43ca22:analisador-genealogico/app.py` → 888 linhas, 41.950 bytes |

**Consequência se isto não fosse corrigido**: o harness da Onda 0 apontaria para o `app.py` atual e estaria comparando a **reconstrução com ela mesma** — a **validação circular** que o RISK-002 existe para prevenir, e que o handoff marca como **pré-requisito mais importante do cutover**. A mitigação estava quebrada na prática. Este artefato a restaura.

## Identidade do oráculo

| Campo | Valor |
|---|---|
| **Arquivo congelado** | `_reversa_sdd/oracle/app_legacy_e43ca22.py` |
| **Origem** | git blob `e43ca22:analisador-genealogico/app.py` |
| **Commit** | `e43ca22` — *"chore: inicializa projeto reversa do app analisador genealogico"* |
| **sha256** | `44370b2339a645c4d9ce732ac3962811b16b35f587ece3507dad4fc3d87646bb` |
| **Tamanho** | 41.950 bytes |
| **Linhas** | 888 (887 de código + a linha final) |
| **`__name__` guard** | presente em `L886` (`if __name__ == "__main__":`) — importar **não** sobe o servidor |
| **Referências a `reconstructed/`** | **nenhuma** (verificado) — oráculo **limpo** |
| **Modo de uso** | **somente leitura**. Executado, nunca modificado. |

### Funções verificadas presentes (14/14)

`ref_id` (L39) · `get_name` (L42) · `find_person_by_name` (L208) · `are_spouses` (L251) · `split_path_by_marriage` (L254) · `find_indirect_path` (L281) · `find_ancestral_path` (L297) · `generate_mermaid_graph` (L320) · `generate_mermaid_graph_indirect_bridge` (L377) · `load_gedcom_and_build_graph` · `build_graph_from_parser` · `get_relationships_by_cm` · `demojibake` · `norm_name` · `split_name_pt` · `surnames_set` · `strip_bad_utf`

> ✅ **Verificação de risco RISK-011**: `are_spouses` (L251) e `split_path_by_marriage` (L254) existem como **funções separadas de verdade** — a lógica de decomposição do parentesco está genuinamente apartada da geração do diagrama Mermaid, que a consome (`generate_mermaid_graph_indirect_bridge` → `split_path_by_marriage` em L406). Isso **confirma** que a decisão do Curator e do Designer (migrar a decomposição como função pura, descartar só a emissão de Mermaid) é implementável sem reescrever regra de negócio.

## Dependências congeladas (mitigação de RISK-009)

Versões **exatas** no ambiente onde o oráculo executa. Registradas porque uma diferença de versão em `thefuzz`/`pandas`/`ged4py` produz divergência que **não é erro do port**, e culpar o código por isso custaria dias.

| Pacote | Versão | Papel |
|---|---|---|
| `Flask` | 3.1.3 | Framework web |
| `ged4py` | **0.5.2** | Parsing GEDCOM |
| `networkx` | **3.6.1** | Grafo e caminhos |
| `pandas` | **3.0.3** | Leitura/agregação do CSV |
| `thefuzz` | **0.22.1** | Matching difuso |
| `RapidFuzz` | 3.14.5 | Backend do `thefuzz` |
| `python-Levenshtein` / `Levenshtein` | 0.27.3 | Aceleração C |
| `numpy` | 2.5.0 | Dependência do pandas |
| `matplotlib` | 3.11.1 | Suporte a visualização |
| `pyvis` | 0.3.2 | Grafo interativo |
| `gunicorn` | 26.0.0 | WSGI (não usado no oráculo) |

> ⚠️ **Ambiente**: as dependências estão no **Python global** (`C:\Python314`, Python **3.14.6**), **não** no `.venv` do projeto (que contém apenas `pip`). O `reconstruction-report.md` registra a suíte da reconstrução passando (47 testes) — ela roda no ambiente global. O alvo declara Python 3.12+; a diferença de minor (3.14 vs 3.12) **precisa ser resolvida antes da Onda 1**: escolha um único ambiente para oráculo e candidato, ou registre a divergência como risco aceito.

## Duas armadilhas operacionais descobertas por execução

> Descobertas **executando o oráculo**, não lendo o código. Ambas custariam tempo se descobertas durante a Onda 1.

### 1. O import do oráculo cria diretórios no diretório de trabalho

`L15-L18` executam `os.makedirs("uploads")` e `os.makedirs("static")` com caminhos **relativos**, no momento do import. Na verificação, `_reversa_sdd/oracle/uploads/` e `static/` foram criados como efeito colateral (removidos depois).

- **Implicação para o harness**: faça `os.chdir(<diretório do legado>)` **antes** de importar, ou o oráculo poluirá o diretório de trabalho. Se `chdir` para o legado, a gravação vai para `analisador-genealogico/uploads/` — que **já existe** e é descartável, mas contém os 12 arquivos de dados do usuário.
- **Mitigação recomendada**: o harness deve copiar o oráculo para um diretório temporário com `uploads/` e `static/` próprios, e rodar **isolado**. Isso também protege os dados reais do usuário de sobrescrita por nome de arquivo (a colisão que BR-DESCARTAR-003 registra como defeito do legado).

### 2. A saída do oráculo contém caracteres que o console Windows não codifica

`get_relationships_by_cm` retorna strings com `↔` (U+2194). Imprimir isso no console padrão (cp1252) levanta `UnicodeEncodeError`. Não é bug do oráculo — é limitação de console.

- **Mitigação**: `PYTHONIOENCODING=utf-8` ao executar, e no harness **nunca** comparar via `print`/`stdout` em texto — comparar **estruturas serializadas** (JSON canônico) com encoding explícito.

## Comportamento verificado contra dados reais

> Executado na verificação, com os dados reais do usuário restaurados.

### Parse de GEDCOM real
`SandroTree.ged` (949.169 bytes) → **3.961 pessoas**, **1.523 famílias**, grafo com **5.484 nós / 5.530 arestas**.

### Tabela de relação por cM — faixas **se sobrepõem** como previsto

Execução real de `get_relationships_by_cm`:

| cM | Retorno |
|---|---|
| 3400 | `['Pai/Mãe ↔ Filho(a)', 'Irmãos completos']` (2 faixas) |
| 2500 | `['Irmãos completos']` |
| 1500 | `['Avós/Netos, Tios/Tias ↔ Sobrinhos(as), Meios-irmãos']` |
| 800 | `['Primos de 1º grau', 'Primos de 1º grau (1× removido), ...']` (2 faixas) |
| 300 | 3 faixas simultâneas |
| 50 | **4 faixas simultâneas** |
| 15 | 2 faixas |
| **0** | **`[]`** |
| **-5** | **`[]`** |

> ⚠️ **A sobreposição é muito maior do que os artefatos sugeriam.** BR-MIGRAR-020 registra "as faixas se sobrepõem" e dá um exemplo; a execução mostra que um mesmo valor pode casar **até 4 faixas** (50 cM). Isso **reforça** a restrição de preservar a ordem de avaliação e **invalida** qualquer implementação que retorne uma única relação — o contrato é uma **lista**.

> 🔴 **ERRO NOS NOSSOS ARTEFATOS, encontrado por este teste.** A spec (`domain.md` §2.1) afirmava que cM ≤ 0 retorna o literal `"Relação distante ou indeterminada"`. **É falso.** O oráculo retorna **lista vazia** para cM ≤ 0 ou não numérico; o literal só aparece quando o valor é **positivo** e não cai em nenhuma faixa. São **dois casos distintos** que a spec havia fundido. Corrigido em: `target_business_rules.md` (BR-MIGRAR-021, com a correção factual completa), `data_migration_plan.md` (T-02 e T-06), `target_domain_model.md` (VO `RelationshipLabel` agora **anulável**), `target_data_model.md` (`relationship_label` deixa de ser `NOT NULL`) e nos cenários `02` e `09` de `parity_tests/`.

### Funções de normalização verificadas
- `demojibake('JoÃ£o da Silva')` → `'João da Silva'` ✅
- `norm_name('João da Silva')` → `'joao da silva'` ✅
- `surnames_set('João Netto Gouvea')` → `{'neto', 'gouveia'}` ✅ (equivalentes de grafia aplicados)

### Código morto confirmado
`HARD_MIN = 92` (L653) e `GIVEN_MIN = 90` (L654) estão declarados e **nunca referenciados em nenhum outro ponto do arquivo**. Confirma a classificação do Curator: são código morto e **não** entram no alvo.

## Restrições de uso do oráculo

1. **Somente leitura.** O arquivo congelado nunca é editado. Se precisar de outra versão, extraia um novo blob e registre um novo manifesto — **não** sobrescreva este.
2. **Nunca importe o módulo diretamente no processo do candidato.** O oráculo mantém **estado global mutável** (`people`, `families`, `graph`, `child_to_family`) e o candidato precisa ser puro (AD-01). Importar ambos no mesmo processo contaminaria o candidato com exatamente o acoplamento que a migração remove. O harness deve **isolar**: oráculo em subprocesso (ou diretório temporário por execução), candidato in-process.
3. **Nunca aponte o harness para `reconstructed/`.** Os 47 testes existentes em `tests/` testam a reconstrução — são úteis como pista de comportamento, **inúteis como oráculo**.
4. **Registre o hash do oráculo em cada execução de paridade.** Um golden sem a proveniência do oráculo que o gerou é evidência sem valor.

## Impacto nos artefatos do pipeline

| Artefato | Ação |
|---|---|
| `parity_specs.md` § Riscos residuais (RISK-002) | **Mitigação agora é factual**: o oráculo existe, tem hash e foi verificado executando. |
| `screens/golden/manifest.yaml` § `oracleCommand` | **Precisa ser corrigido** — apontava para `python -m flask --app analisador-genealogico/app.py`, que hoje sobe o wrapper. Ver nota abaixo. |
| `cutover_plan.md` § Pré-requisitos (Onda 0) | Item "oráculo congelado" passa de **pendente** para **atendido** (o artefato existe; falta o harness). |
| `target_business_rules.md` BR-MIGRAR-021 | Corrigido. |
| `parity_tests/02` e `09` | Cenários corrigidos; o Caso B ganhou cenário próprio. |
| `target_domain_model.md` / `target_data_model.md` | `RelationshipLabel` anulável; coluna `relationship_label` deixa de ser `NOT NULL`. |
| `ambiguity_log.md` | Novo item registrando a correção factual (AMB-023). |

## Notas

- **Este artefato não existia no plano original do pipeline.** Ele nasceu de uma verificação empírica feita **depois** do handoff, quando o usuário perguntou qual era o próximo passo. É a evidência de que **executar o oráculo antes de escrever código** já pagou: descobriu um bloqueio (oráculo contaminado), um erro nos nossos próprios artefatos (cM ≤ 0) e duas armadilhas operacionais — tudo antes de uma linha de código de produto.
- **O que ainda falta para a Onda 0 estar completa**: o **harness diferencial** propriamente dito (o executável que roda oráculo e candidato sobre as mesmas fixtures e compara) e a **materialização das fixtures** `.ged`/`.csv`. O oráculo é a fundação; o harness é a construção.
- **Os dados reais do usuário são o melhor corpus disponível** — 5 árvores GEDCOM (de 949 KB a 5,6 MB) e 6 CSVs de DNA. São ordens de magnitude superiores às fixtures sintéticas de `tests/fixtures/`. ⚠️ São **dados genéticos reais de terceiros**: o corpus de paridade deve usar preferencialmente as fixtures sintéticas nos testes versionados, e os dados reais para **validação de escala e descoberta de casos de borda**, nunca commitados em repositório público.

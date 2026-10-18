# Data delta: validador de dados de DNA × GEDCOM

> Identificador: `028-validador-de-dados-dna`
> Data: `2026-10-18`
> Requirements: `_reversa_forward/028-validador-de-dados-dna/requirements.md`
> Modelo extraído de referência: `_reversa_sdd/erd-complete.md` e `_reversa_sdd/data-dictionary.md`

## 1. Escopo

Esta feature **não cria, remove nem altera estruturas persistentes**. Não há migração, coluna nova,
tabela nova, índice novo ou mudança em `init.sql`. O validador trabalha com estruturas efêmeras em
memória e devolve um dicionário serializável.

## 2. Estruturas novas em memória

### 2.1 `ComparacaoParaValidar` (entrada do núcleo)

| Campo | Tipo | Obrigatório | Invariante |
|-------|------|-------------|------------|
| `doador` | `dict` | sim | `{id, nome, nascimento}`; `nascimento` é o texto GEDCOM, não o ano |
| `match` | `dict` | sim | `{id, nome, nascimento}`; idem |
| `documental` | `dict` | sim | Saída de `documentary_relationship`; ver §2.2 |
| `kit` | `dict` | sim | Saída de `evidence_for`; ver §2.3 |
| `ano_referencia` | `int` | sim | Ano contra o qual "doador vivo" é medido; calculado uma vez pela fachada |
| `intervalo_de_geracao` | `float \| None` | não | `> 0` quando conhecido; `None` faz o núcleo usar 25.0 |
| `comparacao_existente` | `dict \| None` | não | Saída de `evidence_comparison.compare`, quando a fachada a produz |

### 2.2 Subconjunto de `documental` consumido

| Campo | Tipo | Uso |
|-------|------|-----|
| `status` | `str` | `found`, `ambiguous`, `affinity`, `not_found` |
| `label` | `str` | Texto do parentesco documental |
| `relationship_key` | `str \| None` | Chave canônica (`1C`, `SIBLINGS`, ...) |
| `meioses` | `int \| None` | Soma dos saltos pai-filho |
| `degrees` | `dict` | `{a_up, b_up, ...}`; `a_up` é o lado do doador, `b_up` o do match |
| `common_ancestor` | `dict` | `{id, name, birth}`; `birth` é texto GEDCOM |
| `path` | `dict` | `{ids, names}`; `ids[0]` é o doador e `ids[-1]` o match |
| `evidence` | `list[dict]` | Por salto: `parent_birth`, `child_birth`, `age_at_birth`, `plausible` |
| `ambiguous_identity` | `bool` | Identidade ambígua no GEDCOM |
| `homonyms` | `dict` | Dossiê de homônimos, quando houver |

> O núcleo **não** recebe a árvore. Tudo o que ele precisa de data já está em `documental`,
> `doador.nascimento`, `match.nascimento` e `common_ancestor.birth`.

### 2.3 Subconjunto de `kit` consumido

| Campo | Tipo | Uso |
|-------|------|-----|
| `kit` | `str \| None` | Identificador do kit |
| `total_cm` | `float \| None` | Métrica principal da estimativa |
| `largest_segment_cm` | `float \| None` | **Não** entra na estimativa; é registrado para auditoria |
| `mrca_generations` | `float \| None` | Primeira escolha para `geracoes_kit` |
| `segment_count` | `int \| None` | Contexto do match |
| `weak_segment` | `bool \| None` | Marca já existente de `genetic_evidence`; não altera o status |

### 2.4 `MrcaEstimado` (saída de `estimar_mrca`)

| Campo | Tipo | Invariante |
|-------|------|------------|
| `ano` | `int \| None` | Ano estimado do nascimento do MRCA |
| `ano_min` | `int \| None` | Limite inferior da janela |
| `ano_max` | `int \| None` | Limite superior da janela |
| `geracoes` | `float \| None` | Gerações por lado até o MRCA |
| `metodo` | `str \| None` | `mrca_do_kit` ou `scp40:mediana` |

`None` em todos os campos quando não há cM, nascimento do doador ou candidatos.

### 2.5 `ResultadoDeValidacao` (saída de `validar_comparacao`)

| Campo | Tipo | Invariante |
|-------|------|------------|
| `status` | `str` | Exatamente `VALIDADO`, `INCONCLUSIVO` ou `ERRO CRONICO / QUEBRA DE LINHA` |
| `motivo` | `str` | Frase humana, sem jargão de código |
| `codigos` | `list[dict]` | `{codigo, severidade, mensagem}`; sem código repetido; ordenada por severidade e código |
| `kit` | `str \| None` | O kit avaliado |
| `cm` | `float \| None` | cM total do kit, nunca somado entre kits |
| `mrca_estimado` | `dict \| None` | Contrato de §2.4 |
| `mrca_documentado` | `dict \| None` | `{id, nome, ano, impreciso}` |
| `geracoes_documentais` | `dict` | `{doador, match, total}` |
| `comparacao_existente` | `str \| None` | Estado de quatro valores, quando fornecido |

### 2.6 `ResultadoDaFachada` (saída de `validar_arquivos`)

| Campo | Tipo | Invariante |
|-------|------|------------|
| `doador` | `dict` | `{id, nome, nascimento}` |
| `comparacoes` | `list[dict]` | Um item por kit; nunca vazio quando há kit utilizável |
| `resumo` | `dict` | `{status, total, por_status}`; `status` é o pior entre os kits |
| `ano_referencia` | `int` | O ano usado em todas as comparações |
| `intervalo_de_geracao` | `float \| None` | O `G` calculado para a árvore |

## 3. Regras de integridade

1. **Status único:** `status` é sempre um dos três literais, sem variação de caixa ou acento.
2. **Precedência:** `ERRO CRONICO / QUEBRA DE LINHA` > `INCONCLUSIVO` > `VALIDADO`, tanto por
   comparação quanto no `resumo` entre kits.
3. **Nunca somar kits:** `cm` é sempre o total de um kit; dois kits do mesmo nome geram dois
   resultados.
4. **`None` é desconhecido:** data ausente não vira `0`, não vira erro e não vira `VALIDADO`.
5. **Códigos estáveis:** o `codigo` é o contrato de máquina; a `mensagem` é para o operador.
6. **Sem dado pessoal persistido:** o resultado existe só na memória da chamada.

## 4. O que NÃO muda

| Estrutura | Estado |
|-----------|--------|
| Tabelas do PostgreSQL (`analysis`, `analysis_person`, `match_result`, `match_segment`, `match_path_node`, `analysis_kit`) | intocadas |
| `init.sql` | intocado |
| `analysis_person` (dado pessoal já persistido) | intocado; esta feature não grava nada |
| `evidence_comparison` (quatro estados) | intocado |
| `janela_de_vida` (122 e qualificadores) | comportamento idêntico; ganha apenas um wrapper público |
| `genetic_evidence` (`segmento_fraco`/15 cM) | intocado |
| `app.py`, template, CSS, `requirements.txt` | intocados |

## 5. Migração

n/a. Não há dado a migrar nem schema a alterar. Se uma feature futura quiser persistir o resultado,
ela precisará de uma decisão própria de modelo, retenção e consentimento — nada disso está no escopo
de `028`.

## 6. Privacidade

- Nenhum dado real de DNA/GEDCOM entra em fixture, teste ou documentação.
- O resultado não é gravado no banco; não há nova retenção de dado pessoal.
- O `motivo` pode citar nomes e anos que já estão no GEDCOM carregado, mas o resultado não é
  persistido nem enviado a terceiros.

## 7. Compatibilidade

- Python 3.14.6 do `.venv`; apenas biblioteca padrão (`dataclasses`, `statistics`, `typing`).
- Nenhuma dependência nova em `requirements.txt`.
- O núcleo devolve `dict` puro; uma futura borda HTTP pode serializar sem retrabalho.
- As dataclasses são internas; o contrato público é o dicionário.

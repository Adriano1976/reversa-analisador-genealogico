# analise-dna

> Unit do tipo **endpoint** — cobre `POST /` com `action=dna_analysis`.
> Nível de documentação: **Essencial**. Escala: 🟢 CONFIRMADO | 🟡 INFERIDO | 🔴 LACUNA
> Re-extração de 2026-09-30. Substitui a spec de 2026-08-03.

## Visão Geral

Cruza a árvore GEDCOM já carregada com um CSV de matches de DNA (ex.: GEDmatch Ancestor Project). Agrega os segmentos de um mesmo match **somando cM**, casa cada nome do CSV contra a árvore por similaridade difusa com filtros anti-falso-positivo, calcula o caminho ancestral até a pessoa-raiz, prevê o parentesco pela faixa de cM e devolve os resultados ordenados por cM decrescente, mais a lista auditável dos descartes. 🟢

É a **unit de maior complexidade do sistema**: 25 regras de negócio, das quais 6 são ramos de aceitação encadeados e interdependentes. 🟢

## Responsabilidades

- Ler o CSV com fallback de encoding (UTF-8 → Latin-1) e normalizar nomes de coluna 🟢
- Detectar as colunas de Nome, cM, ID e e-mail de forma tolerante 🟢
- Agregar segmentos do mesmo match pela chave `_group_key` e **somar** os cM 🟢
- Construir índices do GEDCOM por nome normalizado e por sobrenome 🟢
- Casar cada match no GEDCOM por similaridade difusa, com filtros anti-falso-positivo 🟢
- Calcular o caminho ancestral até a pessoa-raiz 🟢
- Prever o parentesco pela faixa de cM e emitir o diagrama Mermaid 🟢
- Auditar os descartes com o motivo específico 🟢

## Regras de Negócio

### Pré-condições e entrada
- Requer GEDCOM carregado (`gedcom_filename` presente e arquivo existente em disco). 🟢
- Requer o arquivo CSV no campo `matches_csv`. 🟢
- A pessoa-raiz é resolvida por **substring case-insensitive** no nome; usa o **primeiro ID** encontrado. 🟢
- Colunas de nome aceitas: `Name`, `MatchedName`, `Nome`. Colunas de cM: `cM`, `TotalCM`, `Total cM`. 🟢
- Coluna de ID detectada pela regex `[A-Z]{2}\d{7}` quando **≥ 30 %** dos valores casam; usa a **primeira** coluna que servir. 🟢
- Coluna de e-mail: a **última** cujo nome contenha `mail` (case-insensitive). 🟢
- Sem coluna de nome ou de cM → `ValueError("Colunas de Nome e cM não encontradas no CSV.")`. 🟢

### Agregação
- Chave de agrupamento = `norm_name(demojibake(nome))` **mais** o ID (se houver) **ou** o e-mail normalizado, unidos por `" | "`. 🟢
- O cM do match é a **soma** dos segmentos do grupo. 🟢

### Matching
- Score = `round(0.55*token_sort_ratio + 0.25*partial_ratio + 0.20*ratio(prenome) + InterBonus, 2)`. 🟢
- `InterBonus` = `8.0 × (sobrenomes em comum) − 4.0 × (quantos deles são comuns)`. 🟢
- Desempate do melhor candidato: mais sobrenomes em comum → maior similaridade de prenome → maior score. 🟢
- **Filtro anti-falso-positivo:** ambos os lados com sobrenome, interseção 0 e sem acerto de sufixo → **rejeita**. 🟢
- Interseção mínima adaptativa: prenome genérico **e** ≥ 2 sobrenomes no CSV eleva a exigência de 1 para **2**. 🟢
- Jaccard com prefixo suave: limiar **0.5** com ≥ 2 sobrenomes; cai para **0.33 apenas** quando `cM ≥ 150` **e** o prenome **não** é genérico. 🟢
- Seis ramos de aceitação, avaliados **em ordem**, com limiares literais `100/0.67`, `80/85/0.50`, `86/0.80`, `92/90`, `88/95` e o bônus de prefixo `86/90`. 🟢
- Conflito de nome do meio rebaixa o aceite para `score ≥ 96` e `given ≥ 92`. 🟢
- O cM **não** decide aceitação diretamente — ele só influencia o limiar de Jaccard. 🟢

### Saída
- De cada match aceito, o sistema usa o **primeiro** candidato que tiver caminho ancestral até a raiz (`break`). 🟢
- Sem caminho subindo por pais, o match vai para os descartados. 🟢
- Resultados ordenados por cM **decrescente**. 🟢
- Mensagem final: `"{n} conexões encontradas. {m} descartadas."` 🟢

### Faixas de cM
- 9 faixas **sobrepostas**; o contrato é **lista**, nunca escalar. 🟢
- `cM ≤ 0` ou não numérico → **lista vazia**. Positivo fora de todas as faixas → `["Relação distante ou indeterminada"]`. 🟢

> ⚠️ **Correções contra a spec anterior**, todas verificadas no código atual:
> 1. A spec afirmava que `HARD_MIN = 92` e `GIVEN_MIN = 90` eram "declarados mas não usados (código morto)". **Falso.** Essas constantes **não existem em nenhum arquivo de `analisador-genealogico/`**. Eram código morto do monolito original (`app_legacy_e43ca22.py:653-654`) e a reconstrução **nunca as implementou**. Os literais 92 e 90 vivem dentro dos ramos 4 e 5 de aceitação.
> 2. A spec dizia que a detecção de ID usava "arquivo CSV" e o candidato `***` como exemplo de regex. O exemplo era um valor mascarado, não um ID real.
> 3. A spec citava `given_index` como índice a construir (T-07). Esse índice **foi removido** por prova de morte (`OPP-20260929-32Q7`): nenhum ponto do código o lia. Hoje o que existe é o cache `features`.

## Requisitos Funcionais

| ID | Requisito | Prioridade | Critério de Aceite |
|----|-----------|-----------|-------------------|
| RF-01 | Ler CSV em UTF-8 com fallback para Latin-1 | Must | CSV Latin-1 é lido sem exceção 🟢 |
| RF-02 | Detectar colunas de Nome, cM, ID e e-mail de forma tolerante | Must | Colunas corretas identificadas nos dois formatos de exportador conhecidos 🟢 |
| RF-03 | Agregar segmentos e **somar** cM por match | Must | Um registro por match com cM total correto 🟢 |
| RF-04 | Construir índices de nome normalizado e de sobrenome | Must | Índices populados a partir da árvore carregada 🟢 |
| RF-05 | Calcular score difuso ponderado e desempatar candidatos | Must | Score conforme a fórmula; desempate inter→given→score 🟢 |
| RF-06 | Aplicar o filtro anti-falso-positivo | Must | Match com sobrenomes disjuntos é rejeitado com motivo 🟢 |
| RF-07 | Aplicar a interseção mínima adaptativa e o limiar de Jaccard | Must | Prenome genérico com 2+ sobrenomes exige 2 em comum; limiar 0.33 só com cM ≥ 150 e prenome não-genérico 🟢 |
| RF-08 | Aplicar os 6 ramos de aceitação em ordem | Must | Decisão igual à do legado nos casos cobertos por caracterização 🟢 |
| RF-09 | Calcular o caminho ancestral até a raiz para o primeiro candidato aceito com caminho | Must | Resultado com `text_path` e `common_ancestor` corretos 🟢 |
| RF-10 | Prever o parentesco por faixa de cM, devolvendo **lista** | Must | 50 cM devolve 4 relações; `cM ≤ 0` devolve lista vazia 🟢 |
| RF-10a | As 9 faixas de cM são **heurísticas sem fonte verificável** — a sobreposição é consequência de terem sido escritas à mão | Must | A spec declara a natureza heurística; a reimplementação pode tratá-las como parâmetro ajustável 🟡 |
| RF-14 | Tornar o desempate de candidatos **determinístico** | Must | Duas execuções sobre a mesma entrada, com `PYTHONHASHSEED` diferente, produzem o mesmo vencedor 🟢 |
| RF-11 | Listar os descartados com motivo específico | Should | Cada descarte traz um dos 4 motivos conhecidos 🟢 |
| RF-12 | Ordenar os resultados por cM decrescente | Must | Lista ordenada por `cm` desc 🟢 |
| RF-13 | Reportar erro amigável, sem quebrar a aplicação | Must | Raiz inexistente e colunas ausentes viram mensagem na tela 🟢 |

## Requisitos Não Funcionais

| Tipo | Requisito inferido | Evidência no código | Confiança |
|------|--------------------|---------------------|-----------|
| Performance | Cache de atributos normalizados calculado **uma vez por análise**, fora do laço de candidatos. Medido: 27,77 ms → 2,29 ms por match (12,13×). | `analisador-genealogico/reconstructed/dna_analysis.py:198-230` | 🟢 |
| Performance | **Sem cache entre requisições.** Recalcula os índices do GEDCOM inteiro a cada POST. | `analisador-genealogico/reconstructed/dna_analysis.py:357` | 🟢 |
| Segurança | **Sem sanitização** do nome de arquivo CSV recebido. | `analisador-genealogico/app.py:49-50` | 🟢 |
| Segurança | `app.secret_key` hardcoded. | `analisador-genealogico/app.py:11` | 🟢 |
| Confiabilidade | A dependência `thefuzz` delega a `RapidFuzz`/`python-Levenshtein`; trocar a versão de qualquer uma **altera o resultado do matching** sem mudar uma linha do projeto. | `requirements.txt` + `migration/risk_register.md` (RISK-006) | 🟢 |
| Reprodutibilidade | **Requisito novo (2026-09-30).** O desempate de candidatos precisa de critério final determinístico. O legado deixa empates exatos no terceiro critério serem resolvidos pela **ordem de iteração de um `set`**, que varia com `PYTHONHASHSEED`. Decisão do usuário (`questions.md#pergunta-4`): **precisa ser determinístico**. | `reconstructed/dna_analysis.py:262`, `:274-277` | 🟢 |
| Escalabilidade | Estado global compartilhado; a análise de um usuário usa a árvore do último upload, de qualquer usuário. | `reconstructed/upload.py:16-19` | 🟢 |

> A unit **não emite nenhuma observabilidade**: sem `logging`, métrica ou trace. 🟢

## Critérios de Aceitação

```gherkin
Dado um GEDCOM carregado e um CSV válido com matches
Quando o usuário submete a análise com um root_name existente na árvore
Então as conexões são exibidas ordenadas por cM decrescente
E cada conexão traz o caminho textual, o diagrama e a relação prevista
E a mensagem final informa quantas conexões foram encontradas e quantas descartadas

Dado um CSV com vários segmentos do mesmo match
Quando a análise é executada
Então os segmentos são somados em um único registro por match

Dado um match cujo nome não corresponde a ninguém na árvore
Quando a análise é executada
Então o match aparece entre os descartados com o motivo registrado
E a contagem final de descartados o inclui

Dado um match com sobrenomes sem nenhuma interseção com o GEDCOM e sem acerto de sufixo
Quando a análise é executada
Então o candidato é rejeitado com o motivo "sem sobrenome em comum (filtro anti-falso-positivo)"

Dado um nome de raiz que não existe na árvore
Quando a análise é executada
Então a tela exibe "Seu nome 'X' não foi encontrado no GEDCOM."
E nenhum resultado parcial é exibido

Dado um CSV sem a coluna de cM
Quando a análise é executada
Então a tela exibe "Colunas de Nome e cM não encontradas no CSV."
E a aplicação não quebra

Dado um match com cM total de 50
Quando a relação prevista é calculada
Então as 4 faixas que contêm 50 cM são devolvidas
E o resultado é uma lista, não um valor único

Dado um match com cM total de 0 ou negativo
Quando a relação prevista é calculada
Então a lista devolvida é vazia
E a mensagem "Relação distante ou indeterminada" NÃO é exibida
```

## Prioridade (MoSCoW)

| Requisito | MoSCoW | Justificativa |
|-----------|--------|---------------|
| RF-03 Agregação com soma de cM | **Must** | Base de todo o cálculo de parentesco |
| RF-05 a RF-08 Matching e aceitação | **Must** | Núcleo do produto; 6 ramos interdependentes |
| RF-09 Caminho ancestral até a raiz | **Must** | Sem caminho não há resultado |
| RF-10 Faixas de cM | **Must** | Saída principal para o usuário |
| RF-12 Ordenação por cM | **Must** | Contrato de apresentação |
| RF-01 / RF-02 Leitura e detecção de colunas | **Must** | Porta de entrada dos dados |
| RF-13 Erro amigável | **Must** | Robustez exigida |
| RF-04 Índices | **Must** | Pré-requisito de performance e correção do matching |
| RF-11 Auditoria de descartados | **Should** | Importante para o usuário confiar, mas o fluxo funciona sem |
| `HARD_MIN` / `GIVEN_MIN` | **Won't** | Nunca existiram na reconstrução; decisão de não implementar (ADR-08) |

## Rastreabilidade de Código

| Arquivo | Função / Classe | Cobertura |
|---------|-----------------|-----------|
| `analisador-genealogico/app.py` | `index()` — ramo `dna_analysis` (`:44-63`) | 🟢 |
| `analisador-genealogico/reconstructed/dna_analysis.py` | `dna_analysis` (`:340`) | 🟢 |
| `analisador-genealogico/reconstructed/dna_analysis.py` | `match_candidates` (`:233`) | 🟢 |
| `analisador-genealogico/reconstructed/dna_analysis.py` | `build_ged_indexes` (`:198`) | 🟢 |
| `analisador-genealogico/reconstructed/dna_analysis.py` | `aggregate_matches` (`:173`), `detect_columns` (`:160`), `read_csv_with_fallback` (`:151`) | 🟢 |
| `analisador-genealogico/reconstructed/dna_analysis.py` | `get_relationships_by_cm` (`:62`), `norm_name` (`:74`), `split_name_pt` (`:99`), `soft_prefix_jaccard` (`:128`) | 🟢 |
| `analisador-genealogico/reconstructed/domain.py` | `demojibake` (`:44`), `strip_bad_utf` (`:25`) | 🟢 |
| `analisador-genealogico/reconstructed/path_search.py` | `find_ancestral_path` (`:144`), `generate_mermaid_graph` (`:217`) | 🟢 |
| `tests/test_dna_analysis.py` | 11 testes, incl. `test_anti_false_positive`, `test_relationships_by_cm_out_of_range` | 🟢 |
| `tests/test_characterization_matching.py` | 3 testes, incl. `test_limiar_de_cm_nao_muda_a_decisao` | 🟢 |

> ⚠️ **Correção de rastreabilidade.** A spec anterior apontava tudo para `app.py` com linhas como `:653-654`, `:759`, `:803-820`. Essas linhas **não existem mais** — o núcleo foi movido para `reconstructed/`. As referências acima foram conferidas contra o código atual.

---

*Gerado pelo Reversa-Writer em 2026-09-30 (re-extração).*

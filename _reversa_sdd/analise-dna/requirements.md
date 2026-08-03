# Análise de DNA (DNA Analysis)

> Nível de documentação: **Essencial**
> Confiança: 🟢 CONFIRMADO | 🟡 INFERIDO | 🔴 LACUNA

## Visão Geral

Endpoint que cruza a árvore GEDCOM (já carregada) com um CSV de matches de DNA (ex.: GEDmatch Ancestor Project). Agrega segmentos duplicados por pessoa (somando cM), faz o matching difuso de nomes contra o GEDCOM, calcula o caminho genealógico até a pessoa-raiz, prevê o parentesco por cM e renderiza os resultados ordenados por cM decrescente.

## Responsabilidades
- Ler o CSV de DNA com fallback de encoding (UTF-8 → Latin-1).
- Identificar colunas de Nome, cM e ID/Email de forma tolerante.
- Agregar segmentos do mesmo match (somar cM) pela chave `_group_key`.
- Localizar cada match no GEDCOM via matching difuso com regras anti-falso-positivo.
- Calcular caminho genealógico até a raiz (`find_ancestral_path`).
- Prever relação por faixa de cM e renderizar Mermaid.
- Exibir lista de descartados para auditoria (`skipped_matches`).

## Regras de Negócio
- Requer GEDCOM já carregado (via `gedcom_filename`). 🟢
- Requer arquivo CSV presente no campo `matches_csv`. 🟢
- A pessoa-raiz (`root_name`) deve existir no GEDCOM; usa o primeiro ID encontrado. 🟢
- Colunas aceitas: Nome = `Name`/`MatchedName`/`Nome`; cM = `cM`/`TotalCM`/`Total cM`. 🟢
- ID de match detectado por regex `[A-Z]{2}\d{7}` (ex.: `ZH7115669`). 🟢
- Segmentos duplicados de um mesmo match são somados em cM. 🟢
- Score de matching: `0.55×token_sort + 0.25×partial + 0.20×given + inter_bonus`. 🟢
- Rejeição se ambos têm sobrenomes e interseção = 0 (sem sufixo salvador). 🟢
- Interseção mínima adaptativa: dado genérico + 2+ sobrenomes exige 2 sobrenomes em comum. 🟢
- Limiares de score e given usados como literais nas regras A/B/C/D (92, 90, 86, 100...). 🟢
- `HARD_MIN = 92` e `GIVEN_MIN = 90` são declarados mas não usados (código morto). 🟡
- Se não há caminho subindo por pais, o match é descartado. 🟢
- Resultados ordenados por cM decrescente. 🟢

## Requisitos Funcionais

| ID | Requisito | Prioridade | Critério de Aceite |
|----|-----------|-----------|-------------------|
| RF-01 | Ler CSV com fallback UTF-8/Latin-1 | Must | CSV Latin-1 é lido sem erro |
| RF-02 | Identificar colunas Nome/cM/ID/Email tolerante | Must | Colunas corretas detectadas |
| RF-03 | Agregar segmentos e somar cM por match | Must | cM total correto por pessoa |
| RF-04 | Matching difuso de nomes com anti-falso-positivo | Must | Matches corretos e sem falsos positivos |
| RF-05 | Calcular caminho ancestral até a raiz | Must | Caminho com ancestral comum exibido |
| RF-06 | Prever relação por faixa de cM | Must | Relação provável exibida |
| RF-07 | Listar descartados com motivo | Should | Auditoria visível na UI |
| RF-08 | Exibir erro amigável em exceções | Must | Erro não quebra a aplicação |

## Requisitos Não Funcionais

| Tipo | Requisito inferido | Evidência no código | Confiança |
|------|--------------------|---------------------|-----------|
| Performance | BFS bidirecional até profundidade 20 | `app.py:297-318` | 🟢 |
| Performance | Cálculo em memória, sem cache | `app.py:639-651` | 🟡 |
| Segurança | Sem sanitização de nomes de arquivos recebidos | `app.py:589` | 🔴 |
| Segurança | `secret_key` hardcoded | `app.py:13` | 🟡 |

## Critérios de Aceitação

```gherkin
Dado um GEDCOM carregado e um CSV válido de matches
Quando o usuário submete dna_analysis com root_name existente
Então são exibidas as conexões ordenadas por cM decrescente com relação prevista

Dado um CSV com segmentos duplicados do mesmo match
Quando a análise é executada
Então os cM são somados em um único registro por pessoa

Dado um match cujo nome não corresponde a ninguém no GEDCOM
Quando a análise é executada
Então o match aparece em "descartados" com motivo

Dado um root_name inexistente no GEDCOM
Quando a análise é executada
Então a mensagem "Seu nome 'X' não foi encontrado no GEDCOM." é exibida

Dado um match com sobrenomes sem interseção com o GEDCOM
Quando a análise é executada
Então o candidato é rejeitado pelo filtro anti-falso-positivo
```

## Prioridade (MoSCoW)

| Requisito | MoSCoW | Justificativa |
|-----------|--------|---------------|
| Leitura/agregação de CSV (RF-01..03) | Must | Base de todo o fluxo |
| Matching e caminho (RF-04..05) | Must | Núcleo do produto |
| Predição de relação (RF-06) | Must | Saída principal |
| Auditoria de descartados (RF-07) | Should | Ajuda no debug, sem impacto funcional |
| Erros amigáveis (RF-08) | Must | Robustez exigida |

## Rastreabilidade de Código

| Arquivo | Função / Classe | Cobertura |
|---------|-----------------|-----------|
| `analisador-genealogico/app.py` | `index()` (bloco `dna_analysis`) | 🟢 |
| `analisador-genealogico/app.py` | `build_group_key` | 🟢 |
| `analisador-genealogico/app.py` | `demojibake`, `norm_name`, `split_name_pt`, `surnames_set` | 🟢 |
| `analisador-genealogico/app.py` | `find_ancestral_path` | 🟢 |
| `analisador-genealogico/app.py` | `get_relationships_by_cm` | 🟢 |
| `analisador-genealogico/app.py` | `generate_mermaid_graph` | 🟢 |

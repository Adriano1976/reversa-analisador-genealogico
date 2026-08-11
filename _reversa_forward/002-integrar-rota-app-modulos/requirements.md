# Requirements: integrar a rota index() do app.py com os modulos reconstruidos

> Identificador: `002-integrar-rota-app-modulos`
> Data: `2026-08-11`
> Pasta da extração reversa: `_reversa_sdd/`
> Confidência: 🟢 CONFIRMADO, 🟡 INFERIDO, 🔴 LACUNA / DÚVIDA

## 1. Resumo executivo

Esta feature entrega a **camada de apresentação que faltou na reconstrução**: o `app.py` passa a delegar a lógica de upload GEDCOM, busca de caminho e análise de DNA aos módulos reconstruídos em `reconstructed/` (`upload.py`, `path_search.py`, `dna_analysis.py`), em vez de duplicá-la inline. Resolve a divergência onde o refactor modular está validado por 47 testes, mas a aplicação real ainda roda o código monolítico duplicado.

## 2. Contexto a partir do legado

| Fonte | Trecho relevante | Confidência |
|-------|------------------|-------------|
| `_reversa_sdd/architecture.md#2` | Aplicação monolítica Flask; estado em memória; re-parse do GEDCOM a cada `POST`. | 🟢 |
| `_reversa_sdd/architecture.md#5` | Dívida técnica nº 5: "Código monolítico (app.py ~887 linhas) com rotas + lógica acopladas". | 🟢 |
| `_reversa_sdd/domain.md#3` | Regras de decisão: DNA Analysis e Path Search exigem GEDCOM carregado; matching e limites de busca. | 🟢 |
| `_reversa_sdd/reconstruction-report.md` | 4 módulos reconstruídos (`reconstructed/`) com 47 testes passando, comportamento idêntico ao legado. | 🟢 |
| `_reversa_sdd/addenda/001-reconstrua-o-conteudo-da-index.md` | Front-end (index.html) reconstruído e convergido; contrato Jinja2 com `app.py` intacto. | 🟢 |

## 3. Personas e cenários de uso

| Persona | Objetivo | Cenário-chave |
|---------|----------|---------------|
| Genealogista Genético | Usar upload + buscas via navegador sem mudança percebida | Envia GEDCOM, busca caminho entre duas pessoas e analisa matches de DNA com o mesmo fluxo visual de hoje. |
| Desenvolvedor do projeto | Eliminar a duplicação lógica entre `app.py` e `reconstructed/` | Mantém uma única fonte de verdade para regras de matching e busca, coberta por testes. |

## 4. Regras de negócio novas ou alteradas

1. **RN-01:** O `app.py` (rota `index()`) passa a delegar execução aos módulos `reconstructed/`, mantendo comportamento observável idêntico ao legado. 🟢
   - Origem no legado: `_reversa_sdd/domain.md#3` (regras de decisão/fluxo) e `_reversa_sdd/architecture.md#5` (dívida de acoplamento).
   - Tipo: alterada (refactor sem mudança de comportamento de negócio).
2. **RN-02:** O contrato de renderização com `templates/index.html` permanece intacto — todas as variáveis Jinja2 expostas pelo `app.py` (`gedcom_filename`, `message`, `success`, `all_names`, `path_result`, `dna_results`, `skipped_matches`) continuam iguais. 🟢
   - Origem no legado: `_reversa_sdd/addenda/001-reconstrua-o-conteudo-da-index.md` (front-end convergido).
   - Tipo: mantida.

## 5. Requisitos Funcionais

| ID | Requisito | Prioridade | Critério de aceite | Confidência |
|----|-----------|------------|--------------------|-------------|
| RF-01 | Rota `upload_gedcom` usa `reconstructed.upload.load_gedcom_and_build_graph` | Must | Upload salva o `.ged` e popula `people`/`families`/`graph` via módulo reconstruído; lista de nomes retornada é idêntica. | 🟢 |
| RF-02 | Rota `path_search` usa `reconstructed.path_search.path_search` | Must | Para as mesmas entradas, `path_result` (text_path, mermaid_data, person1/2_name) e mensagens são idênticas ao legado. | 🟢 |
| RF-03 | Rota `dna_analysis` usa `reconstructed.dna_analysis.dna_analysis` | Must | Agregação, matching A/B/C/D, `skipped_matches` e ordenação por cM idênticos; erros (ex.: root não encontrado) viram `message` com `success=False`. | 🟢 |
| RF-04 | Tratamento de exceções do fluxo DNA | Must | `ValueError` lançado pelos módulos reconstruídos é capturado e renderizado como mensagem de erro amigável, como hoje. | 🟡 |
| RF-05 | Estado GEDCOM e re-parse | Must | Manter o comportamento de re-parse a cada `POST` e as globals compartilhadas (`people`, `families`, `graph`, `child_to_family`). | 🟢 |
| RF-06 | Remoção da lógica duplicada inline no `app.py` | Should | Toda função/constante duplicada (matching, mermaid, cM, helpers) removida do `app.py`; restam apenas rotas e renderização. | 🟡 |

## 6. Requisitos Não Funcionais

| Tipo | Requisito | Evidência ou justificativa | Confidência |
|------|-----------|----------------------------|-------------|
| Manutenibilidade | Fonte única de lógica de negócio | Reduz acoplamento apontado em `architecture.md#5`; regras vivem em `reconstructed/` com testes. | 🟢 |
| Compatibilidade | Sem mudança visual/funcional | Contrato Jinja2 preservado (adendo 001); front-end não é tocado. | 🟢 |
| Confiabilidade | Reaproveitar os 47 testes existentes | Suíte atual valida os módulos; a rota deve delegar a eles sem regressão. | 🟢 |
| Observabilidade | Mensagens de erro consistentes | Textos de `message`/`success` idênticos ao legado. | 🟢 |

## 7. Critérios de Aceitação

```gherkin
Cenário: Upload de GEDCOM continua funcional
  Dado o usuário na página inicial
  Quando envia um arquivo .ged válido
  Então o app usa reconstructed.upload e exibe a lista de nomes carregada

Cenário: Busca de caminho continua funcional
  Dado um GEDCOM carregado
  Quando o usuário busca duas pessoas existentes
  Então o app usa reconstructed.path_search e renderiza text_path + Mermaid

Cenário: Análise de DNA continua funcional
  Dado um GEDCOM carregado
  Quando o usuário envia CSV + root_name
  Então o app usa reconstructed.dna_analysis e renderiza resultados e descartados

Cenário: Erro de DNA tratado
  Dado um GEDCOM carregado
  Quando root_name não é encontrado no GEDCOM
  Então a página mostra mensagem de erro com success=False
```

## 8. Prioridade MoSCoW

| Item | MoSCoW | Justificativa |
|------|--------|---------------|
| RF-01, RF-02, RF-03 | Must | São o objetivo central: rotas delegando aos módulos reconstruídos. |
| RF-04, RF-05 | Must | Preservam contrato e robustez do legado. |
| RF-06 | Should | Eliminar duplicação é desejável, mas pode ser feita em passos. |

## 9. Esclarecimentos

> Nenhuma sessão de dúvidas registrada ainda. Rode `/reversa-clarify` quando houver `[DÚVIDA]` pendente.

## 10. Lacunas

- 🔴 [DÚVIDA] Escopo da remoção (RF-06): o `app.py` deve ter a lógica duplicada **totalmente removida** nesta feature, ou apenas as rotas delegando e os helpers inline ficando órfãos (a remover em feature futura)?
- 🔴 [DÚVIDA] Integração `reconstructed` em produção: os módulos reconstruídos ficam em `reconstructed/` (fora do pacote principal). O `app.py` deve importá-los como `from reconstructed import ...` mantendo a pasta atual, ou os módulos devem ser movidos/promovidos para dentro do pacote `analisador-genealogico/`?

## 11. Histórico de alterações

| Data | Alteração | Autor |
|------|-----------|-------|
| 2026-08-11 | Versão inicial gerada por `/reversa-requirements` | reversa |

# Adendo — Refactor de qualidade de código

> Identificador: `003-refactor-code-quality`
> Data: 2026-09-29
> Cenário: **legado** (âncora em `_reversa_sdd/architecture.md` + `domain.md`)
> Transformações: `OPP-20260929-TPSH`, `OPP-20260929-AU76`, `OPP-20260929-32Q7`, `OPP-20260929-SEQO`

## Vigência

Vigente desde 2026-09-29, aplicado sob o gate de edição do legado liberado pelo usuário em
`.reversa/reversa-config.json` (`allowLegacyEdits: true`, `allowedPaths: ["analisador-genealogico/**", "tests/**"]`).

Superado pela re-extração de 2026-09-30.

> Ressalva de cronologia (registrada nesta data, sem remover as linhas acima): a marcação é uma
> declaração de vigência, não a constatação de que os deltas abaixo foram absorvidos. Nesta data o
> `_reversa_sdd/` ainda é o da extração de 2026-08-03 e **não** reflete estas quatro
> transformações — `dependencies.md` ainda lista `matplotlib`/`pyvis` e `architecture.md` ainda
> descreve a criação da pasta `static`. Os deltas continuam válidos até que uma re-extração real
> rode.

## Resumo da entrega

Quatro transformações de Code Quality, todas com comportamento observável preservado e provado:

| Transformação | Verbo | O que mudou |
|---------------|-------|-------------|
| `OPP-20260929-TPSH` | restructure | `_mermaid_sid` e `_mermaid_label` passaram a existir em nível de módulo; as quatro cópias internas foram removidas |
| `OPP-20260929-AU76` | optimize | Atributos normalizados por pessoa passaram a ser calculados uma vez por análise, em vez de a cada candidato de cada match. Medido: 27,77 ms para 2,29 ms por match, 12,13x |
| `OPP-20260929-32Q7` | prune | O índice `given_index`, que nenhum ponto do código lia, foi removido; o docstring que afirmava existirem `HARD_MIN` e `GIVEN_MIN` foi corrigido |
| `OPP-20260929-SEQO` | prune | `STATIC_FOLDER` e o `makedirs` correspondente saíram de `app.py`; `matplotlib` e `pyvis` saíram de `requirements.txt` |

Suíte de 50 testes verde antes e depois de cada uma. Provas: caracterização da saída Mermaid
(4 casos, 40 linhas), equivalência diferencial de saída (2.206 comparações, 0 divergências),
equivalência de rotas do Flask e prova de morte por varredura de referências.

## Impacto por artefato da extração

| Artefato | Seção | Tipo de impacto | Delta |
|----------|-------|-----------------|-------|
| `_reversa_sdd/analise-dna/tasks.md` | T-07 | critério-alterado | O critério de pronto exigia `ged_index`, `surname_index` e `given_index` populados. O `given_index` foi removido por prova de morte, porque nenhum ponto do código o lia. O critério passa a exigir `ged_index`, `surname_index` e o cache de atributos normalizados |
| `_reversa_sdd/analise-dna/design.md` | Interface | contrato-alterado | `build_ged_indexes` deixou de devolver o `given_index` e passou a devolver o cache de atributos; `match_candidates` ganhou o parâmetro desse cache. Nenhuma regra de aceitação A/B/C/D, limiar, peso ou desempate foi tocada |
| `_reversa_sdd/analise-dna/requirements.md` | Riscos | regra-removida (parcial) | A afirmação de que `HARD_MIN = 92` e `GIVEN_MIN = 90` são "declarados mas não usados" não correspondia ao código: nenhum dos dois existe no módulo reconstruído. A menção saiu do docstring |
| `_reversa_sdd/busca-caminho/design.md` | Interface | componente-novo | Duas funções de módulo passaram a existir. As assinaturas públicas `generate_mermaid_graph` e `generate_mermaid_graph_indirect_bridge` não mudaram, e os 45 pontos de chamada continuam idênticos |
| `_reversa_sdd/architecture.md` | §5 Dívidas Técnicas | regra-alterada | A camada de rota perdeu a criação da pasta `static`, resíduo do pyvis, e ficou com 84 linhas |
| `_reversa_sdd/dependencies.md` | §2 Dependências Diretas | regra-removida | `matplotlib` e `pyvis` saíram de `requirements.txt`. Varredura de 406 arquivos do repositório: zero imports das duas |
| `_reversa_forward/002-integrar-rota-app-modulos/regression-watch.md` | OBS-03 | correção de registro | O OBS-03 afirma que `HARD_MIN`/`GIVEN_MIN` "foram preservados nos módulos reconstruídos". O código nunca os teve. Este adendo corrige o registro, e o mesmo vale para a menção equivalente em `_reversa_sdd/addenda/002-integrar-rota-app-modulos.md` |

## Regras sob vigilância

Nenhum watch item (`W001`...) foi criado. As quatro transformações são de Code Quality: nenhuma
regra de negócio confirmada de `domain.md` foi alterada. A regra de matching congelada pelo
`migration_brief.md` (regras A/B/C/D, relaxamento de Jaccard 0.5 para 0.33 com cM maior ou igual a
150, regex de ID `[A-Z]{2}\d{7}`, agregação por chave) permanece intacta: a `AU76` mudou apenas onde
o valor é calculado, nunca o valor.

## Divergências de documentação

### Fechada em 2026-09-29

| Documento | O que afirmava | Correção aplicada |
|-----------|----------------|-------------------|
| `analisador-genealogico/README.md` linhas 15, 25 e 34 | Anunciavam `Pyvis` como a biblioteca de visualização de grafo | Trocado por Mermaid. A varredura de `analisador-genealogico/` e `tests/` não encontra nenhuma ocorrência de `pyvis` no código do aplicativo: a pilha real é `generate_mermaid_graph` (`reconstructed/path_search.py:205`, saída começando por `flowchart BT`), renderizada no cliente por `mermaid@10` via CDN (`templates/index.html:8` e `182-186`). As três linhas também perderam o qualificador "interactive", que o Mermaid 10 não sustenta: a saída é um SVG estático, sem pan, zoom ou arrasto |

Fonte da correção: `analisador-genealogico/README.md`, nos commits `70703f7` e `27aaed5`. Suíte de 76 testes verde antes e depois, sem relação causal (a mudança é de documentação, não de código).

Nota de precisão sobre a varredura, para quem for reproduzi-la: a contagem depende do escopo. Restrita a `analisador-genealogico/` e a `tests/`, ela retorna zero, e antes desta correção retornava exatamente as 3 linhas deste README. Sobre o repositório inteiro, excluindo `.git/` e `.pytest-tmp/`, ela retorna 89 ocorrências em 28 arquivos, e nenhuma delas está no código do aplicativo. As 89 vivem em artefatos do Reversa que registram o histórico da extração, o estado pré-refactor, ou a própria remoção do `pyvis` pela `OPP-20260929-SEQO`: `_reversa_docs/`, `_reversa_sdd/`, o `intake` dos bugs e as pastas de transformação. O `README.md` da raiz contribui com 3 delas e segue fora do gate.

### Abertas

| Documento | O que afirma | Situação |
|-----------|--------------|----------|
| `README.md` da raiz, linhas 21, 74 e 100 | Anuncia `Pyvis` na stack, na estrutura do projeto e nas funcionalidades | **Fora do gate de edição.** O arquivo da raiz não casa com `analisador-genealogico/**` nem com `tests/**`, então nenhuma edição foi feita. É o README do projeto Reversa, não o do legado |
| `README.md` da raiz, linha 74 | Documenta `static/graph_path_search.html` como "HTML estático gerado para grafos interativos (Pyvis)" | A pasta `analisador-genealogico/static/` **não existe** na árvore. Mesma situação de gate da linha acima |
| `README.md` da raiz, linhas 104 e 118 | Afirma que o `app.py` tem cerca de 86 linhas e que a suíte tem 47 testes | Medido na árvore atual: `app.py` tem 84 linhas e a suíte tem 76 testes. Mesma situação de gate |
| `README.md` da raiz, linha 69 | Descreve as entidades de `domain.py` como PERSON, FAMILIA e DNA_MATCH | As entidades reais são `Family`, `GenealogyGraph` e `DNAGroup` (a linha 112 do mesmo arquivo já lista os nomes corretos). Mesma situação de gate |
| `_reversa_docs/assets/data/modules.json` e `_reversa_docs/assets/js/data.js` | Inventariam `static/graph_path_search.html` com 321 linhas e citam Pyvis | É o mini-site "Documentação Antes" (ver `README.md:138` da raiz), um retrato do estado pré-refactor. Corrigir à mão seria falsear o retrato. O caminho é regenerar via `/reversa-docs` |
| `.reversa/context/surface.json:55` | Lista `pyvis` como dependência vinda de `requirements.txt` | Instantâneo da extração, quando `pyvis` de fato estava no manifesto. Historicamente correto, potencialmente enganoso hoje |
| `_reversa_sdd/oracle/ORACLE_MANIFEST.md:63-64` | Lista `matplotlib` 3.11.1 e `pyvis` 0.3.2 no ambiente do oráculo | Histórico do ambiente do legado, que não existe mais na árvore |
| `_reversa_sdd/parity/harness.py:40` | Aponta para `_reversa_sdd/oracle/app_legacy_e43ca22.py` | Esse arquivo foi removido na limpeza de histórico. **O harness diferencial não pode mais rodar**, e o projeto perdeu o oráculo de equivalência mais forte que tinha. As redes de caracterização e equivalência do refactor passam a ser a melhor prova disponível |

## Fontes

- `_reversa_refactor/busca-caminho/transformations/OPP-20260929-TPSH-unificar-sid-lab/transformation.md`
- `_reversa_refactor/analise-dna/transformations/OPP-20260929-AU76-cache-de-atributos/transformation.md`
- `_reversa_refactor/analise-dna/transformations/OPP-20260929-32Q7-podar-given-index/transformation.md`
- `_reversa_refactor/upload-gedcom/transformations/OPP-20260929-SEQO-podar-residuos/transformation.md`
- `_reversa_refactor/generated/index.md`
- `analisador-genealogico/README.md` (correção da divergência de Pyvis)
- `.reversa/reversa-config.json`

---
*Gerado pelo Reversa-Sync em 2026-09-29.*

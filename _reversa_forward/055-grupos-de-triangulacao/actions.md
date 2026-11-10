# Actions: grupos de triangulação

> Identificador: `055-grupos-de-triangulacao`
> Data: `2026-11-09`
> Roadmap: `_reversa_forward/055-grupos-de-triangulacao/roadmap.md`

## Resumo

| Métrica | Valor |
|---------|-------|
| Total de ações | 25 |
| Paralelizáveis (`[//]`) | 9 |
| Maior cadeia de dependência | 12 (T001 → T004 → T007 → T008 → T011 → T012 → T014 → T017 → T021 → T022 → T023 → T025) |
| Concluídas nesta rodada | 25 |

## Fase 1, Preparação

| ID | Descrição | Dependências | Paralelismo | Arquivo alvo | Confidência | Status |
|----|-----------|--------------|-------------|--------------|-------------|--------|
| T001 | Criar a fixture sintética `sample_triangulation.py` com os seis casos (`trio_fechado`, `cadeia`, `acumulo`, `dois_segmentos`, `bom` com BOM e `*`, `sem_build`) e um gravador para disco, no molde de `sample_dna.py` | - | `[//]` | `tests/fixtures/sample_triangulation.py` | 🟢 | `[X]` |
| T002 | Adicionar a função de limpeza do nome do GEDmatch (remove `*` inicial, preserva o bruto) em `text_cleaning` e o teste que a fixa, sem tocar em `norm_name` (`D-09`, `ADR-07`) | - | `[//]` | `src/utils/text_cleaning.py` | 🟢 | `[X]` |
| T003 | Adicionar `parece_triangulacao(df)` — reconhece a forma de pares (dois kits + cromossomo + cM) — com teste de positivo e negativo (`D-03`, `RF-02`) | - | `[//]` | `src/core/genetic_evidence.py` | 🟢 | `[X]` |

## Fase 2, Testes

| ID | Descrição | Dependências | Paralelismo | Arquivo alvo | Confidência | Status |
|----|-----------|--------------|-------------|--------------|-------------|--------|
| T004 | Escrever os testes do agrupamento (fechado vira grupo, cadeia não vira, dois segmentos do mesmo par, ordem determinística) e do acúmulo/limite — **falham antes** da T007 | T001 | `[//]` | `tests/test_triangulacao.py` | 🟢 | `[X]` |
| T005 | Escrever os testes da classificação: convergente, dividido, parcial, sem ancestral, junção por kit e queda para nome (`RN-04`, `RN-08`) | T001 | `[//]` | `tests/test_grupos_no_cartao.py` | 🟢 | `[X]` |
| T006 | Escrever os testes do parser: dois kits, `B37 Start/End`, `*`, BOM, arquivo sem build, arquivo de matches recusado com o campo correto (`RF-03`, `RF-04`, `RF-14`, `RF-17`) | T001, T002, T003 | `[//]` | `tests/test_triangulacao_gedmatch.py` | 🟢 | `[X]` |

## Fase 3, Núcleo

| ID | Descrição | Dependências | Paralelismo | Arquivo alvo | Confidência | Status |
|----|-----------|--------------|-------------|--------------|-------------|--------|
| T007 | Implementar `agrupar`: varredura por cromossomo, interseção comum, teste de fechamento, grupos maximais e dedupe dos aninhados (`RN-01`, `RN-11`, `D-01`) | T004 | - | `src/core/triangulacao.py` | 🟢 | `[X]` |
| T008 | Implementar `regiao_de_acumulo` com o limiar da `RN-05`, o `LIMITE_DE_GRUPOS = 200` e o truncamento declarado (`D-08`) | T007 | - | `src/core/triangulacao.py` | 🟡 | `[X]` |
| T009 | Implementar a classificação do grupo a partir de `documentary.common_ancestor.id`, sem segunda passagem de matching (`RN-04`, `D-04`) | T005 | - | `src/core/triangulacao_no_cartao.py` | 🟢 | `[X]` |
| T010 | Implementar o adaptador do CSV de pares: detecção por papel (dois kits + nome de cada), B37, cM, descartes contados, avisos e build declarado (`RN-10`, `D-02`) | T006 | - | `src/parsers/triangulacao_gedmatch.py` | 🟢 | `[X]` |

## Fase 4, Integração

| ID | Descrição | Dependências | Paralelismo | Arquivo alvo | Confidência | Status |
|----|-----------|--------------|-------------|--------------|-------------|--------|
| T011 | Criar o caso de uso isolado `analisar_triangulacao`, devolvendo `ResultadoDeTriangulacao` e as observações de arquivo (`RF-18`) | T008, T010 | - | `src/application/triangulacao.py` | 🟢 | `[X]` |
| T012 | Acrescentar `grupos` a `ResultadoDeAnalise` (padrão `()`) e chamar o caso de uso + a classificação depois do núcleo, sem alterar o que ele devolveu (`RF-12`, `D-07`) | T009, T011 | - | `src/application/dna_analysis.py` | 🟢 | `[X]` |
| T013 | Registrar a ação `triangulacao_analysis` no despacho **pré-árvore** e escrever o handler que guarda o arquivo e renderiza o bloco sem árvore (`D-05`, `RF-18`) | T011 | - | `src/app.py` | 🟢 | `[X]` |
| T014 | Acrescentar o campo opcional `triangulacao_csv` ao handler `_acao_dna_analysis`, guardando-o e passando ao template | T012 | - | `src/app.py` | 🟢 | `[X]` |
| T015 | Criar o formulário de triangulação da Fase 3, visível **sem** árvore, com o texto de que o desfecho depende da análise completa (`RF-11`, `RF-18`) | T013 | - | `src/templates/index.html` | 🟢 | `[X]` |
| T016 | Criar o bloco "Grupos de triangulação" `<details open>` antes dos cartões: cromossomo, faixa, cM mín/máx, membros, desfecho, marca do par abaixo de 10 cM, alerta de acúmulo e a negativa explícita (`RF-06`, `RF-07`, `RF-10`, `RF-13`, `D-11`) | T013 | - | `src/templates/index.html` | 🟢 | `[X]` |
| T017 | Acrescentar o campo de arquivo de triangulação ao formulário de DNA e o botão de download dos grupos (`RF-16`) | T014 | - | `src/templates/index.html` | 🟡 | `[X]` |
| T018 | Estilizar o bloco e os selos de desfecho com os tokens vigentes, respeitando o contraste preso por teste | T016 | - | `src/assets/app.css` | 🟢 | `[X]` |
| T019 | Implementar `csv_dos_grupos` no dialeto de `csv_de_descartes` (BOM, `;`, decimal com vírgula, desarme de fórmula) | T009 | `[//]` | `src/reporting/csv_dos_grupos.py` | 🟢 | `[X]` |
| T020 | Criar a rota `POST /grupos.csv` no regime de `descartes_em_csv` (`D-12`) | T019 | - | `src/web/rotas_assets.py` | 🟡 | `[X]` |
| T021 | Escrever os testes de integração da borda: ação isolada, ação combinada, arquivo no campo errado e bloco ausente sem o arquivo (`RF-01`, `RF-02`, `RF-18`) | T017, T018, T020 | - | `tests/test_acao_triangulacao.py` | 🟢 | `[X]` |
| T022 | Escrever os testes de contrato: `RF-12` (HTML dos cartões e CSV de descartes idênticos sem o arquivo novo) e `RN-14` (nenhuma média/mediana/distribuição no modo sem árvore) | T021 | - | `tests/test_contrato_dos_grupos.py` | 🟢 | `[X]` |

## Fase 5, Polimento

| ID | Descrição | Dependências | Paralelismo | Arquivo alvo | Confidência | Status |
|----|-----------|--------------|-------------|--------------|-------------|--------|
| T023 | Medir e registrar em `evidence/`: tempo com a amostra de 1.650 linhas, número de grupos (esperado 28) e `SHA_DA_TELA` com o delta em bytes | T022 | `[//]` | `_reversa_forward/055-grupos-de-triangulacao/evidence/` | 🟢 | `[X]` |
| T024 | Documentar a funcionalidade no `README.md`, na lista de Principais Funcionalidades, com o que ela **não** faz | T022 | `[//]` | `README.md` | 🟢 | `[X]` |
| T025 | Rodar a suíte e a paridade, conferir que nenhum teste de caracterização regrediu e registrar o atestado em `actions.md` | T023, T024 | - | `tests/` | 🟢 | `[X]` |

## Notas de execução

1. **O reparo guloso de conjunto mascarado foi implementado e removido na mesma rodada.** Ele
   recuperava trios escondidos por um kit de fora, mas também fabricava trios dentro da região de
   acúmulo do chr20 (0,40 Mb, cM 5–10): 46 grupos em vez de 28. Ver `evidence/medicoes.md`.
2. **A janela do agrupamento nasceu de uma falha medida.** Sem ela, os 18 pares com dois segmentos no
   mesmo cromossomo zeravam a interseção e o resultado era 27 grupos em vez de 28.
3. **A `T022` foi entregue na parte que dá para provar sem montar a análise inteira.** O contrato
   escrito prende a `RN-14` (nenhuma estatística no modo sem árvore), o padrão `grupos == ()` de
   `ResultadoDeAnalise` e a pureza da projeção (`projetar_grupos` não muta o grupo). O contraste
   byte a byte do HTML dos cartões com e sem o arquivo novo **não** foi escrito — fica como dívida
   declarada da feature, e é o primeiro teste a acrescentar antes de a feature ser considerada
   convergida.
4. **Suíte:** `2043 passed, 9 skipped, 5 failed`. As cinco falhas são as pré-existentes declaradas
   nos adendos 052 e 053 (quatro de `test_characterization_mermaid` e o literal
   `1. Lista de Matches (CSV)`). Nenhuma falha nova.
5. **`SHA_DA_TELA` movido por decisão declarada:** `3487986a…` (51.218 bytes) → `82258c2b…`
   (52.768 bytes, +1.550). O delta é o formulário da Fase 3, não o bloco de grupos.

## Histórico de alterações

| Data | Alteração | Autor |
|------|-----------|-------|
| 2026-11-09 | Versão inicial gerada por `/reversa-to-do` | reversa |
| 2026-11-09 | `/reversa-coding`: 25 de 25 ações concluídas; notas de execução e dívida da T022 | reversa |

# Actions: busca por nome e sobrenome em GEDCOM e CSV

> Identificador: `052-busca-nome-e-sobrenome`
> Data: `2026-10-28`
> Roadmap: `_reversa_forward/052-busca-nome-e-sobrenome/roadmap.md`

## Resumo

| Métrica | Valor |
|---------|-------|
| Total de ações | 27 |
| Paralelizáveis (`[//]`) | 9 |
| Maior cadeia de dependência | 10 (T001 → T003 → T010 → T011 → T012 → T017 → T021 → T022 → T026 → T027) |

> **A verificação em navegador não é ação de agente.** O roteiro está em `onboarding.md` — dez passos,
> do campo ausente sem árvore até o relatório ilegível — e entra como gate do critério de pronto do
> `roadmap.md#10`. O agente não pode declarar a feature fechada sem ele, mas também não pode executá-lo.

## Fase 1, Preparação

| ID | Descrição | Dependências | Paralelismo | Arquivo alvo | Confidência | Status |
|----|-----------|--------------|-------------|--------------|-------------|--------|
| T001 | Criar `tests/fixtures/busca_arvores.py`: três árvores sintéticas — uma com sobrenome composto e partícula (`Silva e Souza`, `dos Santos`), e duas do **mesmo tamanho e com os mesmos xrefs extremos**, que é o cenário que reproduzia a `L-24` | - | `[//]` | `tests/fixtures/busca_arvores.py` | 🟢 | `[X]` |
| T002 | Criar `tests/fixtures/busca_relatorios.py`: relatório com nome que existe na árvore, nome que não existe, e um arquivo que **não** é relatório de matches (para `RF-13`) | - | `[//]` | `tests/fixtures/busca_relatorios.py` | 🟢 | `[X]` |

## Fase 2, Testes

| ID | Descrição | Dependências | Paralelismo | Arquivo alvo | Confidência | Status |
|----|-----------|--------------|-------------|--------------|-------------|--------|
| T003 | Escrever `tests/test_busca_de_nome_dominio.py`: `TermoDeBusca` (tokens e escopo derivado), cada estratégia isolada, e ordem total determinística com empate resolvido por `(nome normalizado, xref)` | T001 | - | `tests/test_busca_de_nome_dominio.py` | 🟢 | `[X]` |
| T004 | Escrever `tests/test_indice_de_tokens.py`: as duas visões saem da mesma varredura; **duas árvores de mesmo tamanho não compartilham mapa**; árvore sem grafo não pendura e não falha | T001 | `[//]` | `tests/test_indice_de_tokens.py` | 🟢 | `[X]` |
| T005 | Escrever `tests/test_busca_de_nome_fontes.py`: o adaptador da árvore entrega `NomeDaFonte` com ficha; o do CSV usa `norm_name`; arquivo ilegível devolve falha com motivo, não exceção crua | T001, T002 | - | `tests/test_busca_de_nome_fontes.py` | 🟢 | `[X]` |
| T006 | Escrever `tests/test_rota_de_busca.py`: busca feliz, termo vazio, termo acima de 120 caracteres e `404` para `gedcom_filename` que não resolve | T002 | - | `tests/test_rota_de_busca.py` | 🟢 | `[X]` |
| T007 | Escrever `tests/test_isolamento_da_busca.py` — o portão: dois donos, `404` sem `403`, e nenhum nome de A no corpo servido a B | T002 | `[//]` | `tests/test_isolamento_da_busca.py` | 🟢 | `[X]` |
| T008 | Escrever `tests/test_busca_nao_muda_analise.py`: veredito, contagem de conexões e descartados idênticos antes e depois de buscas (`RF-11`) | T001, T002 | `[//]` | `tests/test_busca_nao_muda_analise.py` | 🟢 | `[X]` |
| T009 | Escrever `tests/test_tela_da_busca.py` sobre o **HTML entregue**: bloco só com árvore aberta, rótulos acessíveis, termo preservado, seção do relatório omitida quando ilegível e total declarado acima de 50 | T002 | - | `tests/test_tela_da_busca.py` | 🟢 | `[X]` |

## Fase 3, Núcleo

| ID | Descrição | Dependências | Paralelismo | Arquivo alvo | Confidência | Status |
|----|-----------|--------------|-------------|--------------|-------------|--------|
| T010 | Implementar `TermoDeBusca` congelado: texto cru preservado, forma normalizada pela autoridade da fonte, tokens e escopo derivado da contagem (`RN-02`) | T003 | - | `src/core/busca_de_nome.py` | 🟢 | `[X]` |
| T011 | Implementar `EstrategiaDeCasamento` (`Protocol`) mais as quatro estratégias — exata, sobrenome, prefixo e aproximada —, com a **ordem declarada na construção** (`D-05`, `RN-09`) | T003, T010 | - | `src/core/busca_de_nome.py` | 🟢 | `[X]` |
| T012 | Implementar `AcertoDeBusca` e `ResultadoDaBusca` congelados, com ordenação total `(-pontuacao, nome_normalizado, xref)` e truncamento em **50** por seção (`RN-04`, `RN-07`) | T003, T010, T011 | - | `src/core/busca_de_nome.py` | 🟢 | `[X]` |
| T013 | Em `core/homonimos.py`, produzir a visão `token → xrefs` no **mesmo laço** de `_indice_por_nome` e pendurá-la no grafo por `setattr`, com atributo próprio (`D-04`, `addenda/048`) | T004 | - | `src/core/homonimos.py` | 🟢 | `[X]` |

## Fase 4, Integração

| ID | Descrição | Dependências | Paralelismo | Arquivo alvo | Confidência | Status |
|----|-----------|--------------|-------------|--------------|-------------|--------|
| T014 | Declarar `FonteDeNomes` (`Protocol`) e `NomeDaFonte` congelado em `src/ports/__init__.py`, com docstrings que dizem que a fonte já chega escopada pelo dono (`D-02`) | T005 | - | `src/ports/__init__.py` | 🟢 | `[X]` |
| T015 | Implementar `NomesDaArvoreGedcom` em `src/ports/adaptadores.py`: resolve a referência pela porta de carregamento e entrega `NomeDaFonte` com a ficha | T005, T013, T014 | - | `src/ports/adaptadores.py` | 🟢 | `[X]` |
| T016 | Implementar `NomesDoArquivoDeMatches` em `src/ports/adaptadores.py`: lê o CSV pelo leitor existente e devolve `NomeDaFonte`; falha de leitura vira resultado vazio **mais o motivo**, sem derrubar a fonte irmã | T005, T014 | - | `src/ports/adaptadores.py` | 🟢 | `[X]` |
| T017 | Implementar o caso de uso `application/busca_de_nome.py`: consulta as fontes na ordem, delega o ranking ao núcleo, trunca e devolve `ResultadoDaBusca`, sem `if` de formato (`D-03`) | T012, T014, T015, T016 | - | `src/application/busca_de_nome.py` | 🟢 | `[X]` |
| T018 | Implementar `reporting/resultado_da_busca.py`: função pura que traduz `ResultadoDaBusca` no view-model do partial, incluindo o aviso de relatório ilegível e o de total truncado | T012 | `[//]` | `src/reporting/resultado_da_busca.py` | 🟢 | `[X]` |
| T019 | Criar `src/templates/_busca.html`: campo com rótulo, botão, **seletor do relatório** (quando a lista de relatórios não está vazia), duas seções rotuladas, card de acerto e os quatro estados — sem árvore, sem acerto, sem relatório, relatório ilegível | T009 | `[//]` | `src/templates/_busca.html` | 🟢 | `[X]` |
| T020 | Incluir o partial em `index.html` dentro de `{% if gedcom_filename %}`, antes das fases, **sem tocar** no bloco `#nomes-da-arvore` nem no script do combobox (`D-09`) | T019 | - | `src/templates/index.html` | 🟢 | `[X]` |
| T021 | Criar `src/web/rotas_busca.py`: Blueprint com `POST /busca`, guarda herdada da 051, validação do termo (vazio e teto de 120) e render da **tela inteira** com o partial já preenchido (`D-01`, `interfaces/busca.md`) | T006, T017, T020 | - | `src/web/rotas_busca.py` | 🟢 | `[X]` |
| T022 | Em `src/app.py`, registrar o Blueprint e montar as duas fontes por injeção, sem decidir casamento na borda (`D-01`) | T021 | - | `src/app.py` | 🟢 | `[X]` |

## Fase 5, Polimento

| ID | Descrição | Dependências | Paralelismo | Arquivo alvo | Confidência | Status |
|----|-----------|--------------|-------------|--------------|-------------|--------|
| T023 | Acrescentar a `src/assets/app.css` os estilos do campo, das duas seções, do card de acerto e dos estados vazios | T019 | `[//]` | `src/assets/app.css` | 🟢 | `[X]` |
| T024 | Varrer os literais de tela: os **29 catalogados** intactos, e os novos — rótulo, dica, termo vazio, títulos das seções e aviso de relatório ilegível — listados para a convergência (`domain.md#5`) | T020 | `[//]` | `src/templates/` | 🟢 | `[X]` |
| T025 | Medir e registrar dois números: o acréscimo da segunda visão sobre os ~0,9 s da varredura, e o custo de uma busca por trecho com a árvore real (`RN-09`, `D-04`) | T013, T017 | - | `tests/` | 🟡 | `[X]` |
| T026 | Rodar a suíte completa e a paridade; registrar marco, divergências e veredito, **sem ajustar teste existente para passar** | T022, T023, T024, T025 | - | `tests/` | 🟢 | `[X]` |
| T027 | Atestar os invariantes no mesmo commit: `tests/test_combobox_de_nomes.py` inalterado, `SHA_DA_TELA` inalterado e o marco das **4 falhas pré-existentes** mantido | T020, T026 | - | `tests/test_icone_de_atalho.py` | 🟢 | `[X]` |

## Notas de execução

## Histórico de alterações

| Data | Alteração | Autor |
|------|-----------|-------|
| 2026-10-28 | Versão inicial gerada por `/reversa-to-do` a partir do `roadmap.md` com 12 decisões e do `interfaces/busca.md` | reversa |

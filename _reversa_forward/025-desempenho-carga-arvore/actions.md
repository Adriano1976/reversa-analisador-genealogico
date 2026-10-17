# Actions: desempenho da carga da árvore GEDCOM

> Identificador: `025-desempenho-carga-arvore`
> Data: `2026-10-17`
> Roadmap: `_reversa_forward/025-desempenho-carga-arvore/roadmap.md`

## Resumo

| Métrica | Valor |
|---------|-------|
| Total de ações | 20 |
| Paralelizáveis (`[//]`) | 15 |
| Maior cadeia de dependência | 8 (`T008 → T009 → T010 → T011 → T016 → T017 → T018 → T020`) |

> **Duas notas de leitura.** (1) Onde a coluna "Arquivo alvo" nomeia `evidence/…`, a ação é de
> **execução e medição**, e o arquivo alvo é a evidência que ela produz. (2) A `T021` é do estágio
> `/reversa-sync`, que é quem cria adendos neste projeto (`roadmap.md` §8); ela fica aqui porque o
> critério de pronto depende dela.

## Fase 1, Preparação

| ID | Descrição | Dependências | Paralelismo | Arquivo alvo | Confidência | Status |
|----|-----------|--------------|-------------|--------------|-------------|--------|
| T001 | Escrever o instrumento de perfil do **código de produção**: importa `carregar_arvore` e `application.dna_analysis`, redireciona a pasta de upload por `ANALISADOR_UPLOAD_FOLDER`, instrumenta `GedcomReader` para contar `records0` por tag, `index0`, `_init_index` e `read_record`, e mede a carga em 1 aquecimento descartado + 3 repetições em processo próprio (`RF-01`, `RF-02`, `RF-03`, `D-01`, `D-05`, `D-06`) | - | `[//]` | `_reversa_sdd/parity/_perfil_da_carga.py` | 🟢 | [X] |
| T002 | Escrever o instrumento de **impressão digital**: serialização canônica (chaves de `people`/`families` na ordem, nós com `label`/`type` na ordem, arestas na ordem, `child_to_family` na ordem, resultado de DNA na ordem) e `sha256` da árvore e do resultado; grava **apenas hashes e contagens**, nunca nome ou cM (`RF-05`, `RF-06`, `D-04`) | - | `[//]` | `_reversa_forward/025-desempenho-carga-arvore/evidence/_impressao_da_arvore.py` | 🟢 | [X] |
| T003 | Registrar o ambiente da medição: HEAD do git, tamanho e `sha256` do GEDCOM e do CSV oficiais, versões de Python e `ged4py`, e ausência de `DATABASE_URL` (`RF-12`, `D-05`) | - | `[//]` | `_reversa_forward/025-desempenho-carga-arvore/evidence/antes/ambiente.txt` | 🟢 | [X] |
| T004 | Rodar a suíte completa **antes** da mudança, com `DATABASE_URL` ausente, e registrar: esperado **1.046 passed, 9 skipped**, zero falhas (`RF-11`, `D-10`) | - | `[//]` | `_reversa_forward/025-desempenho-carga-arvore/evidence/antes/suite.txt` | 🟢 | [X] |
| T005 | Rodar a paridade **antes** da mudança pelo invólucro `tests/rodar_paridade.py` e registrar a saída completa: esperado **24 divergências em 5 de 6 fixtures**, `exit 1` — é a linha de base, não regressão (`RF-10`, `D-08`) | - | `[//]` | `_reversa_forward/025-desempenho-carga-arvore/evidence/antes/paridade.txt` | 🟢 | [X] |
| T006 | Rodar o instrumento **antes** da mudança e registrar contagens e tempos: `records0("FAM")` = 2, `read_record` = 49.321, `_init_index` = 1, `index0` = 3, e as etapas `INDI`/`FAM`/`grafo`/`carga`/`DNA` (`RF-01`, `RF-03`, `RF-08`) | T001 | `[//]` | `_reversa_forward/025-desempenho-carga-arvore/evidence/antes/carga.txt` | 🟢 | [X] |
| T007 | Rodar a impressão digital **antes** da mudança e registrar os dois hashes (árvore e resultado de DNA), com 93 cartões e 363 descartes (`RF-05`, `RF-06`) | T002 | `[//]` | `_reversa_forward/025-desempenho-carga-arvore/evidence/antes/impressao.txt` | 🟢 | [X] |

## Fase 2, Testes

| ID | Descrição | Dependências | Paralelismo | Arquivo alvo | Confidência | Status |
|----|-----------|--------------|-------------|--------------|-------------|--------|
| T008 | Escrever o teste da `RN-02`: numa carga, `records0("INDI")` = 1, `records0("FAM")` = **1** e `read_record` = 1 + pessoas + famílias; reusa a fixture sintética de GEDCOM já existente e **roda para ver falhar** contra o código atual (contagem 2) (`RF-09`, `D-07`) | - | `[//]` | `tests/test_carga_da_arvore.py` | 🟢 | [X] |

## Fase 3, Núcleo

| ID | Descrição | Dependências | Paralelismo | Arquivo alvo | Confidência | Status |
|----|-----------|--------------|-------------|--------------|-------------|--------|
| T009 | Aplicar a mudança em `parsers/gedcom_parser.py`: `build_graph_from_parser(people_dict, familias)` deixa de receber o `GedcomReader` e de chamar `records0("FAM")`; `carregar_arvore` materializa `list(parser.records0("FAM"))` **uma vez**, monta `families` dessa lista e a entrega ao grafo; documentar no docstring o invariante de que o grafo só **lê** `xref_id` e `sub_records` (`RF-04`, `RF-07`, `RN-03`, `D-02`, `D-03`) | T008 | - | `src/parsers/gedcom_parser.py` | 🟢 | [X] |
| T010 | Adaptar os dois testes que exercitam o grafo (`tests/test_upload.py:217` e `:263`) para ler as famílias do mesmo `GedcomReader` e passá-las — mesma cobertura, assinatura nova; **nenhum teste removido** (`RF-11`, `D-07`) | T009 | - | `tests/test_upload.py` | 🟢 | [X] |

## Fase 4, Integração

| ID | Descrição | Dependências | Paralelismo | Arquivo alvo | Confidência | Status |
|----|-----------|--------------|-------------|--------------|-------------|--------|
| T011 | Rodar a suíte completa **depois** e registrar: zero falhas e coletados ≥ 1.046; o teste da `T008` agora passa (`RF-09`, `RF-11`) | T010 | `[//]` | `_reversa_forward/025-desempenho-carga-arvore/evidence/depois/suite.txt` | 🟢 | [X] |
| T012 | Rodar a paridade **depois**, pelo mesmo invólucro, e comparar **item a item** com `evidence/antes/paridade.txt`: nenhuma divergência nova e nenhuma fixture nova divergente (`RF-10`, `D-08`) | T010 | `[//]` | `_reversa_forward/025-desempenho-carga-arvore/evidence/depois/paridade.txt` | 🟢 | [X] |
| T013 | Rodar a impressão digital **depois** e comparar os dois hashes com `evidence/antes/impressao.txt`: árvore e resultado de DNA **idênticos** (`RF-05`, `RF-06`, `D-04`) | T010 | `[//]` | `_reversa_forward/025-desempenho-carga-arvore/evidence/depois/impressao.txt` | 🟢 | [X] |
| T014 | Rodar o instrumento **depois**, com o mesmo protocolo, e registrar a comparação: `FAM` = 1, `read_record` = 42.391, `_init_index` = 1, e as medianas de tempo (`RF-03`, `RF-08`, `D-05`) | T010 | `[//]` | `_reversa_forward/025-desempenho-carga-arvore/evidence/depois/carga.txt` | 🟢 | [X] |
| T015 | Provar o escopo fechado (`D-09`): `git diff --stat` só com `src/parsers/gedcom_parser.py`, `tests/test_upload.py` e `tests/test_carga_da_arvore.py`; `requirements.txt` intacto; `sha256` de `_reversa_sdd/parity/_profile_big.py` e `harness.py` igual ao registrado na `T003` | T010 | `[//]` | `_reversa_forward/025-desempenho-carga-arvore/evidence/depois/escopo.txt` | 🟢 | [X] |

## Fase 5, Polimento

| ID | Descrição | Dependências | Paralelismo | Arquivo alvo | Confidência | Status |
|----|-----------|--------------|-------------|--------------|-------------|--------|
| T016 | Consolidar o relatório da feature: tabela antes/depois por etapa (carga, `INDI`, `FAM`, grafo, DNA, total), contagem de chamadas, hashes e resultado da paridade, com uma frase explícita sobre o ganho estar ou não dentro da dispersão (`RF-12`) | T011, T012, T013, T014, T015 | - | `_reversa_forward/025-desempenho-carga-arvore/evidence/RELATORIO.md` | 🟢 | [X] |
| T017 | Preencher no `onboarding.md` a tabela "resultados efetivamente medidos" com os números reais, e corrigir qualquer valor esperado que tenha divergido | T016 | - | `_reversa_forward/025-desempenho-carga-arvore/onboarding.md` | 🟢 | [X] |
| T018 | Escrever o `legacy-impact.md`: cada arquivo tocado, o tipo de impacto (`regra-alterada` / `contrato-alterado` / `sem mudança`) e a evidência que o sustenta | T017 | `[//]` | `_reversa_forward/025-desempenho-carga-arvore/legacy-impact.md` | 🟢 | [X] |
| T019 | Escrever o `regression-watch.md`: cada item de vigilância (contagem de `FAM`, hashes da árvore e do DNA, divergências da paridade, número de testes), o que vigia e o sintoma que o dispara | T017 | `[//]` | `_reversa_forward/025-desempenho-carga-arvore/regression-watch.md` | 🟢 | [X] |
| T020 | Escrever o adendo `_reversa_sdd/addenda/025-desempenho-carga-arvore.md`, com a vigência, o delta no parser e a linha de base da paridade declarada. **Estágio `/reversa-sync`** (`RF-12`) | T019 | - | `_reversa_sdd/addenda/025-desempenho-carga-arvore.md` | 🟢 | [X] |

## Notas de execução

- **O teste vem antes da mudança.** A `T008` tem de ser **vista falhando** com `records0("FAM")` = 2.
  Um teste de contagem que nunca falhou não prova nada (Princípio III).
- **A `T005` é linha de base, não defeito.** A paridade está vermelha desde antes desta feature
  (24 divergências em 5 de 6 fixtures). O critério é "nenhuma divergência nova", comparado item a
  item — nunca "100 %".
- **A carga roda 3 vezes; o DNA roda 1 vez por lado.** O DNA não é alvo da mudança e custa ~54 s;
  ele entra no total como uma execução declarada, não como mediana.
- **A árvore é lida, nunca escrita.** O `sha256` do GEDCOM e do CSV é conferido na `T003` e de novo
  na `T013`; se mudar no meio, a comparação é cancelada e refeita, não "ajustada".
- **Nada de `_reversa_sdd/parity/_profile_big.py` nem de `harness.py`.** A `T015` confere por `sha256`
  que os dois continuam byte a byte (`D-01`).
- **Ambiente desta máquina:** a suíte e a paridade precisam de acesso total, porque o sandbox bloqueia
  a escrita em `tests/.tmp` (medido em 2026-10-17). Isso é execução, não código.
- **`DATABASE_URL` ausente em todas as execuções de suíte.** Presente, 2 testes de
  `tests/test_persistencia_desabilitada.py` falham por dívida alheia (`L-27`).

### Notas da execução (2026-10-17)

- **As medianas de ponta a ponta não são o ganho.** A rodada "antes" variou 83 % (25,09 a 45,96 s) e a
  "depois", 6 % — a máquina estava mais calma. O ganho declarado é o da fase removida, medida 3 vezes
  na árvore real: **mediana 1,59 s**. Ver `evidence/RELATORIO.md` §4.
- **A `T008` foi vista falhando** com `records0("FAM")` = 2 (`evidence/antes/T008-teste-falhando.txt`) e
  passou depois da `T009`.
- **A paridade ficou idêntica linha a linha**: a comparação entre `evidence/antes/paridade.txt` e
  `evidence/depois/paridade.txt` devolveu **0 linhas diferentes**. As 24 divergências são pré-existentes.
- **O escopo fechou como planejado**: `git diff --stat` só com `src/parsers/gedcom_parser.py` e
  `tests/test_upload.py`, mais o teste novo não rastreado. `requirements.txt` sem diff e os dois
  instrumentos da paridade com `sha256` inalterado.
- **Nenhum dado pessoal em evidência:** os arquivos guardam contagens, tempos, hashes e nomes de
  arquivo — nunca nome de pessoa, xref ou cM.

## Histórico de alterações

| Data | Alteração | Autor |
|------|-----------|-------|
| 2026-10-17 | Versão inicial gerada por `/reversa-to-do`, com 20 ações e 15 paralelizáveis | reversa |
| 2026-10-17 | 20 ações executadas e marcadas `[X]` pelo `/reversa-coding` | reversa |

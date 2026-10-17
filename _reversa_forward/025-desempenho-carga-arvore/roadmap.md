# Roadmap: desempenho da carga da árvore GEDCOM

> Identificador: `025-desempenho-carga-arvore`
> Data: `2026-10-17`
> Requirements: `_reversa_forward/025-desempenho-carga-arvore/requirements.md`
> Confidência: 🟢 CONFIRMADO, 🟡 INFERIDO, 🔴 LACUNA

## 1. Resumo da abordagem

A feature tem **duas metades que não se misturam**: medir e mudar. A primeira entrega um
**instrumento de desenvolvimento** novo, irmão de `_profile_big.py`, que mede o **código de
produção** — `parsers.gedcom_parser.carregar_arvore` mais `application.dna_analysis.dna_analysis` —
e conta as chamadas ao `ged4py`. A segunda aplica uma mudança de **12 linhas** em um único arquivo
de produção (`src/parsers/gedcom_parser.py`): `carregar_arvore` passa a materializar a lista de
registros `FAM` **uma vez** e a entrega a `build_graph_from_parser`, que deixa de receber o
`GedcomReader` e de chamar `records0("FAM")`.

O que torna a mudança barata é o que foi medido antes de escrevê-la: a indexação do `ged4py`
acontece **uma vez** (`_init_index` = 1), e o desperdício é a **segunda materialização dos 6.930
registros de família** (`read_record` 49.321 → 42.391). Na árvore real o grafo construído sobre as
famílias já lidas tem **os mesmos nós, as mesmas arestas, a mesma ordem de nós e de arestas e o
mesmo `child_to_family`** — verificado nesta sessão, antes do plano.

O ganho é **~1,5 s em ~105 s de requisição** (~5 % da carga, ~1,4 % do total). A feature remove
trabalho redundante e enxuga o acoplamento parser↔grafo; **não** promete redução perceptível, e o
roadmap não a vende como tal. Os 19,3 s da passada `INDI` e os 54,0 s da análise de DNA ficam
declaradamente fora do escopo.

Nada mais muda: `ports/adaptadores.py` continua chamando `carregar_arvore(caminho)`, a árvore
continua sendo a tupla de quatro posições, `core/` continua sem importar `parsers/`, e o
`harness.py` da paridade continua byte a byte.

## 2. Princípios aplicados

| Princípio | Como a feature se relaciona | Status |
|-----------|------------------------------|--------|
| I. Dados reais de DNA/GEDCOM nunca entram no versionamento | A medição usa a árvore real **de fora do versionamento**: o arquivo é lido de `src/uploads/` (que o `.gitignore` protege desde a feature 012) e o instrumento devolve só contagens, tempos e hashes. A prova de identidade é feita por **impressão digital sha256**, nunca por transcrição de nomes, xrefs ou cM. Nenhum artefato desta feature contém uma linha de dado pessoal | respeita |
| II. Comportamento observável é preservado em refatoração | É o eixo da feature: `RF-05` e `RF-06` exigem identidade **exata** de pessoas, famílias, grafo (inclusive ordem), `child_to_family` e resultado da análise de DNA. A mudança é um refactor puro — se qualquer coisa divergir, ela é revertida, não justificada | respeita |
| III. Nenhuma mudança sem teste que a cubra | `RF-09` cria o teste que hoje não existe: a contagem de `records0("FAM")` numa carga tem de ser **1**. Ele é escrito **antes** da mudança, falha com a contagem 2 e passa depois. Os dois testes que exercitam `build_graph_from_parser` são **adaptados**, nunca removidos | respeita |
| IV. Arestas do grafo são tipadas | Não se aplica: nenhum tipo de aresta, nenhuma travessia e nenhum cálculo de parentesco é tocado; o conjunto e a ordem das arestas são **invariantes exigidos** (`RF-05`) | não se aplica |
| V. Toda suposição de genealogia genética cita a fonte | Não se aplica: nenhuma faixa de cM, nenhuma heurística e nenhum limiar de matching é alterado | não se aplica |

## 3. Decisões técnicas

| ID | Decisão | Justificativa | Alternativas descartadas | Confidência |
|----|---------|----------------|--------------------------|-------------|
| D-01 | O instrumento é um **script irmão novo** em `_reversa_sdd/parity/` (`_perfil_da_carga.py`), e `_profile_big.py` fica **byte a byte** como está | `_profile_big.py` copia `oracle/app_legacy_e43ca22.py` para uma pasta temporária e mede `load_gedcom_and_build_graph` do **legado congelado**; ele é a régua do oráculo, e mexer nele mistura dois papéis. O irmão mede o código de produção e pode evoluir sem contaminar a régua | (a) estender `_profile_big.py` — um script com dois alvos e dois imports em conflito; (b) instrumentar por `pytest --durations` — mede teste, não a etapa; (c) profiler externo (cProfile/py-spy) — não devolve a contagem por tag e não é reproduzível por script | 🟢 |
| D-02 | A assinatura nova é `build_graph_from_parser(people_dict, familias)`, onde `familias` é a **lista de registros na ordem do arquivo**, e `carregar_arvore` a materializa com `list(parser.records0("FAM"))` **uma vez**. As duas estruturas (`families` e grafo) passam a compartilhar os mesmos objetos de registro | O dicionário `families` **não** serve como fonte da lista: ele é chaveado por `ref_id`, e `ref_id(None)` devolve `None` (`core/registro.py:35-37`), então **famílias sem `xref_id` colapsam numa única chave**. Passar `families.values()` mudaria a sequência iterada em relação à segunda passada atual. A lista é a **sequência exata** que o código percorre hoje | (a) `families.values()` — colapsa as famílias sem xref e muda o que é iterado; (b) passar o `parser` e embrulhá-lo num proxy que devolve a lista — mantém o acoplamento que a `RN-03` quer remover; (c) construir o grafo dentro de `carregar_arvore` — concentra duas responsabilidades no mesmo laço e dificulta o teste do grafo | 🟢 |
| D-03 | Compartilhar os objetos `Record` entre `families` e a construção do grafo é **seguro por invariante declarado**: `build_graph_from_parser` só lê `fam.xref_id` e `fam.sub_records`, e nunca muta o registro | A alternativa (reler para obter objetos novos) é exatamente o desperdício que a feature remove. O invariante fica escrito no docstring da função e é a condição que precisa continuar verdadeira para o compartilhamento ser válido | (a) copiar cada registro antes de entregar — paga de novo o custo que se quer remover; (b) não declarar o invariante e deixar implícito | 🟢 |
| D-04 | A prova de identidade é uma **impressão digital determinística** (`sha256` sobre uma serialização canônica: chaves de `people` e de `families` na ordem, nós com `label`/`type` na ordem, arestas na ordem, `child_to_family` com as listas na ordem e o resultado da análise de DNA na ordem), calculada antes e depois e comparada **exatamente** | `RISK-004` proíbe tolerância, e a comparação precisa ser de **uma linha**, não de um olhar sobre milhares de nós. O hash também resolve o Princípio I: prova igualdade sem transcrever nome de pessoa nem cM. Serialização por `pickle` foi recusada porque embute endereços e ordem de dicionário irrelevante e não é comparável entre processos de forma estável | (a) comparar contagens e amostras — não prova ordem; (b) salvar os objetos em JSON e comparar arquivos — guardaria dado pessoal em evidência; (c) `pickle` — não determinístico para este fim | 🟢 |
| D-05 | O protocolo de medição é **1 aquecimento descartado + 3 repetições medidas, cada uma em processo próprio**, reportando mediana, mínimo e máximo | Medido nesta sessão: a mesma carga variou **26,55 / 28,02 / 32,71 s** no mesmo processo (23 %), e a **primeira** execução de um processo novo levou **51,68 s** (cache frio). Uma execução única não distingue 1,5 s de ruído — e "não declare ganho sem medição" inclui não declarar ganho que é ruído | (a) uma execução — foi a origem do número de 8,4 s do pedido; (b) mediana de 3 no mesmo processo — não descarta o efeito de cache do primeiro; (c) média de 10 — caro (cada repetição custa ~28 s de carga + 54 s de DNA) sem ganho de confiança | 🟢 |
| D-06 | O instrumento é **artefato de desenvolvimento** e vive em `_reversa_sdd/parity/`, nunca em `src/`; ele redireciona a pasta de upload pela mesma variável que `tests/rodar_paridade.py` usa (`ANALISADOR_UPLOAD_FOLDER`) | Importar `app` cria `uploads/` e `static/` no diretório de trabalho, e a paridade já aprendeu (feature 010) que isso deixa resíduo na pasta real do operador. A variável é o mecanismo documentado de isolamento sem editar o instrumento | (a) importar `app` sem redirecionar — repete o resíduo medido em 2026-10-09; (b) `os.chdir` — não redireciona a pasta, que é ancorada no arquivo do app desde a feature 006 | 🟢 |
| D-07 | Os dois testes que chamam `build_graph_from_parser` (`tests/test_upload.py:217` e `:263`) são **adaptados** para ler as famílias do mesmo `GedcomReader` e passá-las; e um teste novo (`RF-09`) conta as chamadas a `records0("FAM")` numa carga | O que esses testes medem é o **grafo** (nós, arestas, `child_to_family`), não a assinatura; adaptar preserva a cobertura e a intenção. Removê-los violaria "nenhum teste removido" e deixaria o grafo sem teste de estrutura | (a) manter uma sobrecarga que aceita `parser` **ou** lista — assinatura ambígua e dois caminhos para manter; (b) apagar os testes e confiar no harness — o harness não cobre `child_to_family` nem `type` de nó | 🟢 |
| D-08 | A linha de base da paridade é **capturada em arquivo de evidência antes da primeira linha de código**, no HEAD do dia, e a comparação depois é **item a item** contra essa captura | O vermelho atual (24 divergências em 5 de 6 fixtures) é anterior à feature; sem a captura, "não piorou" vira impressão. A captura também congela o HEAD e o conjunto de fixtures medidos | (a) comparar de memória com o número 24 — não distingue troca de divergências; (b) exigir 100 % — impossível sem corrigir o vermelho alheio, que o operador mandou não fazer aqui | 🟢 |
| D-09 | **Nenhum outro módulo de produção é tocado**: `ports/`, `application/`, `app.py`, `core/`, `reporting/`, `utils/`, `templates/`, `docker/`, `init.sql` e `requirements.txt` ficam intactos | A mudança é interna ao parser: `ports/adaptadores.py:257` chama `carregar_arvore(caminho)` e continua valendo; a forma da árvore não muda; `ged4py` continua pinado. O critério verificável é `git diff --stat` listando apenas `src/parsers/gedcom_parser.py`, os testes e o instrumento | (a) tocar `ports/` para "esconder" a leitura — não há ganho e alarga o diff; (b) trocar `ged4py` — depende de medição que esta feature faz, mas a decisão é de outra feature | 🟢 |
| D-10 | O número de testes do pedido (**246**) é **substituído pelo medido** (1.046 coletados, 1.046 passam, 9 pulados), e a regra que vale é "nenhum teste removido" | O 246 é de uma era anterior do projeto; usá-lo como critério faria a entrega parecer que ganhou 800 testes ou que perdeu 246, dependendo da leitura. O critério verificável é: coletados antes ≥ coletados depois, e zero falhas | (a) manter 246 como meta — número sem relação com o repositório; (b) exigir exatamente 1.046 — quebra ao acrescentar o teste do `RF-09` | 🟢 |

## 4. Premissas

Nenhuma premissa vem de `[DÚVIDA]`: o documento chegou ao plano com **0** marcadores, depois da
sessão de esclarecimento de 2026-10-17 (`requirements.md` §9).

| Premissa | Origem (`requirements.md`) | Risco se errada |
|----------|----------------------------|-----------------|
| O ganho atribuível é o da **fase isolada** (~1,49 s), e não a diferença entre as medianas antes/depois | §2.1 e RNF de desempenho | Se o ganho real for menor que o ruído (23 %), o relatório declara "dentro do ruído" e **não** afirma ganho. Nenhum requisito depende de o ganho ser visível |
| A árvore real permanece a mesma entre a medição de antes e a de depois | §2.1; decisão de 2026-10-17 | Se o arquivo mudar no meio (reenvio do operador), a comparação por impressão digital falha de forma **ruidosa** e a medição é refeita. O `sha256` do arquivo é registrado antes e depois para detectar isso |
| O `harness.py` da paridade continua executável e sem edição | `RF-10`; `tests/rodar_paridade.py` | Se ele quebrar por motivo alheio, a captura e a comparação usam o mesmo instrumento e a conclusão é "não medido", nunca "sem divergência nova" |

## 5. Delta arquitetural

| Componente | Arquivo de origem no legado | Tipo de mudança | Resumo |
|------------|------------------------------|-----------------|--------|
| `gedcom_parser` — construção do grafo | `_reversa_sdd/architecture.md#3`; `_reversa_sdd/c4-components.md#3`; `src/parsers/gedcom_parser.py:26-55` | contrato-alterado (interno) | `build_graph_from_parser` deixa de receber o `GedcomReader` e passa a receber a lista de registros `FAM`. Não lê mais o arquivo (`RN-03`) |
| `gedcom_parser` — carga da árvore | `_reversa_sdd/upload-gedcom/requirements.md#5` (`RF-11` a `RF-14`); `src/parsers/gedcom_parser.py:61-76` | regra-alterada | Materializa `INDI` e `FAM` **uma vez** cada e entrega a lista de famílias à construção do grafo. A tupla devolvida e a ordem de inserção **não** mudam |
| Porta `CarregadorDeArvores` e adaptador | `_reversa_sdd/c4-components.md#3`; `src/ports/adaptadores.py:240-257` | **sem mudança** | Continua chamando `carregar_arvore(caminho)` e devolvendo a tupla |
| Borda HTTP, casos de uso, núcleo, reporting, utils | `src/app.py`, `src/application/`, `src/core/`, `src/reporting/`, `src/utils/` | **sem mudança** | Provado por `git diff` vazio (`D-09`) |
| Instrumento de perfil de desenvolvimento | `_reversa_sdd/parity/_profile_big.py` (irmão, não substituído) | componente-novo | `_perfil_da_carga.py`: mede carga e DNA do código de produção e conta chamadas ao `ged4py`. **Não** faz parte do sistema em execução |

## 6. Delta no modelo de dados

- **Nenhum campo, tabela, índice, payload ou migração.** A tupla `(people, families, graph,
  child_to_family)` mantém forma, tipos e ordem.
- O que muda é **transitório**: deixam de existir 6.930 materializações de registro `FAM` por carga
  (objetos que morriam no fim da função). O pico de memória não cresce de forma relevante — a lista
  acrescenta 6.930 referências (dezenas de KB) e os registros já eram mantidos pelo dicionário
  `families`.
- Detalhe completo em: `_reversa_forward/025-desempenho-carga-arvore/data-delta.md`

## 7. Delta de contratos externos

Nenhum contrato externo é afetado: rota, campos de formulário, códigos de status, mensagens,
template e formato de CSV/GEDCOM ficam intactos. A mudança é **interna ao parser**. Por isso **não
há diretório `interfaces/`**.

| Contrato | Tipo | Arquivo de detalhe |
|----------|------|--------------------|
| n/a — nenhum contrato HTTP, de arquivo ou de banco afetado | — | n/a |

## 8. Plano de migração

Não há migração de dados. O que existe é uma **ordem de execução** que impede medir depois de mudar.

1. **Congelar a linha de base** (`RF-03`, `RF-10`, `D-08`): com o código no HEAD `c946b6c`, rodar a
   suíte, o harness de paridade e o instrumento novo, e gravar as três saídas em
   `evidence/antes/`. Registrar o `sha256` da árvore real e do CSV.
2. **Escrever o teste do `RF-09`** e vê-lo **falhar** contra o código atual (contagem 2), antes de
   qualquer mudança de produção.
3. **Aplicar a mudança** em `src/parsers/gedcom_parser.py` (`D-02`, `D-03`): materializar a lista de
   famílias, entregá-la ao grafo, remover o parâmetro `parser` da função.
4. **Adaptar os dois testes existentes** (`D-07`) e confirmar que o teste do passo 2 passa.
5. **Provar a identidade** (`RF-05`, `RF-06`, `D-04`): calcular a impressão digital antes/depois e
   comparar; rodar a análise de DNA nos dois estados e comparar contagens e ordem.
6. **Medir depois** (`RF-08`, `D-05`): mesmo instrumento, mesma árvore, mesmo CSV, 3 repetições em
   processo próprio, com a árvore conferida pelo `sha256`.
7. **Paridade depois** (`RF-10`): mesma execução, comparada item a item com a captura do passo 1.
8. **Suíte depois** (`RF-11`): sem falhas e sem queda no número de testes coletados.
9. **Evidência** (`RF-12`): consolidar `evidence/antes/` e `evidence/depois/` num relatório com os
   números, a contagem de chamadas e o resultado da paridade, sem dado pessoal.

## 9. Riscos e mitigações

| Risco | Impacto | Probabilidade | Mitigação |
|-------|---------|---------------|-----------|
| O ganho de ~1,5 s ser confundido com ruído de medição (23 % de variação) | médio | **alta** | `D-05` mede a fase isolada e reporta mediana, mínimo e máximo; o relatório declara "dentro do ruído" se for o caso, e nenhum requisito promete ganho perceptível |
| A lista materializada mudar a ordem em que o grafo é construído | alto | baixa | `D-02` passa a **sequência exata** que o código percorre hoje; `RF-05` compara ordem de nós e de arestas, e a verificação já feita nesta sessão deu igualdade |
| Compartilhar objetos `Record` entre `families` e o grafo permitir mutação cruzada | alto | baixa | `D-03` declara o invariante (o grafo só lê `xref_id` e `sub_records`); o código de hoje não muta registro em lugar nenhum, e a revisão do diff confirma |
| Famílias sem `xref_id` colapsarem numa chave só do dicionário e o grafo "perder" famílias | médio | baixa | `D-02` existe justamente por isso: a lista preserva a cardinalidade real, e o caso é coberto por `test_family_without_id_skipped` |
| A paridade já estar vermelha e a feature ser culpada por ela | alto | **alta** | `D-08` captura a linha de base antes da primeira linha de código e compara item a item; a captura nomeia HEAD e fixture |
| O instrumento deixar resíduo na pasta real do operador ao importar `app` | médio | média | `D-06` redireciona `ANALISADOR_UPLOAD_FOLDER` como `tests/rodar_paridade.py` faz; a pasta é conferida antes e depois |
| A árvore real mudar entre antes e depois | alto | baixa | `sha256` do arquivo registrado nas duas pontas; divergência cancela a comparação em vez de mascará-la |
| O ambiente desta máquina exigir acesso total para criar pasta temporária | baixo | **alta** (medido) | A suíte e a paridade rodam com aprovação de acesso total; o efeito é de execução, não de código |
| Alguém "otimizar" além do escopo e mexer no `INDI`, no matching ou no parser inteiro | médio | baixa | `D-09` fixa o diff permitido; qualquer arquivo fora da lista é desvio declarado |

## 10. Critério de pronto

- [ ] Todas as ações do `actions.md` marcadas `[X]`
- [ ] Teste do `RF-09` escrito **antes** da mudança, visto falhar com contagem 2 e passando com 1
- [ ] `records0("FAM")` = **1** por carga e `read_record` = **42.391** na árvore real
- [ ] `index0` acessado 3 vezes e `_init_index` executado **1** vez, como antes (prova de que a indexação não era o problema)
- [ ] Impressão digital da árvore **idêntica** antes e depois (`RF-05`)
- [ ] Impressão digital do resultado de DNA **idêntica** antes e depois (`RF-06`): 93 cartões e 363 descartes
- [ ] Paridade com **exatamente** as 24 divergências da captura, nenhuma nova, nenhuma fixture nova divergente (`RF-10`)
- [ ] Suíte com **0 falhas** e coletados ≥ 1.046 (`RF-11`)
- [ ] Números antes/depois registrados com mediana, mínimo e máximo de 3 repetições (`RF-08`)
- [ ] Contagem de chamadas registrada antes e depois (`RF-03`)
- [ ] `git diff --stat` limitado a `src/parsers/gedcom_parser.py`, `tests/test_upload.py`, o teste
      novo e o instrumento (`D-09`)
- [ ] `requirements.txt` e o pin de `ged4py` inalterados (`RF-13`)
- [ ] `_reversa_sdd/parity/_profile_big.py` e `harness.py` byte a byte (`D-01`)
- [ ] Nenhum artefato de evidência contém nome de pessoa, xref ou cM (Princípio I)
- [ ] `regression-watch.md` gerado

## 11. Histórico de alterações

| Data | Alteração | Autor |
|------|-----------|-------|
| 2026-10-17 | Versão inicial gerada por `/reversa-plan`, com 10 decisões técnicas e zero premissas de `[DÚVIDA]` | reversa |

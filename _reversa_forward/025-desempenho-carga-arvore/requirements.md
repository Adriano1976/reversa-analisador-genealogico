# Requirements: desempenho da carga da árvore GEDCOM

> Identificador: `025-desempenho-carga-arvore`
> Data: `2026-10-17`
> Pasta da extração reversa: `_reversa_sdd/`
> Confidência: 🟢 CONFIRMADO, 🟡 INFERIDO, 🔴 LACUNA / DÚVIDA

## 1. Resumo executivo

O operador espera até a análise de DNA terminar para ver o resultado, e a árvore GEDCOM é
re-parseada integralmente a cada requisição. Esta feature entrega **dois passos, nesta ordem**:
primeiro **medir** a requisição completa (carga da árvore + análise de DNA) com a árvore real e
registrar o tempo por etapa; depois, **se a medição confirmar** leitura repetida dos registros de
família, eliminar a segunda leitura até hoje feita por `build_graph_from_parser`.

A medição já feita nesta sessão (registrada em §2.1) muda a premissa do pedido: a carga real desta
máquina é de **~28 s**, e não 8,4 s; a indexação do arquivo acontece **uma única vez**, e o que se
repete é a **materialização dos 6.930 registros `FAM`**. O ganho atribuível ao passo 2 é de
**~1,5 s (~5 % da carga, ~1,4 % da requisição completa)**. É remoção de trabalho redundante com
saída idêntica — **não é** um ganho perceptível ao operador, e esta feature não afirma que seja.

## 2. Contexto a partir do legado

| Fonte | Trecho relevante | Confidência |
|-------|------------------|-------------|
| `_reversa_sdd/architecture.md#1` | Aplicação de um processo; **a cada `POST` o GEDCOM é re-parseado integralmente**; **não há cache entre requisições** | 🟢 |
| `_reversa_sdd/architecture.md#7` | Dívidas consolidadas; a carga não é dívida catalogada — é custo de arquitetura | 🟢 |
| `_reversa_sdd/upload-gedcom/requirements.md#5` | `RF-11` (parsear `INDI`/`FAM`), `RF-12` (grafo bipartido), `RF-13` (`child_to_family`), `RF-14` (devolver a árvore como valor) | 🟢 |
| `_reversa_sdd/code-analysis.md#4` | `BR-U-18`: família sem `xref_id` é ignorada; aresta só para nó existente | 🟢 |
| `_reversa_sdd/migration/parity_specs.md#4` | `@ordem`: a **ordem de inserção das arestas** decide qual caminho `nx.shortest_path` devolve — é contrato | 🟢 |
| `_reversa_sdd/migration/parity_specs.md#tipos-de-teste-a-aplicar` | "**Carga / performance: fora do escopo de paridade.** … Se houver meta de performance, ela é requisito novo, não paridade" | 🟢 |
| `_reversa_sdd/migration/risk_register.md#RISK-004` | Comparação **exata, sem tolerância**; divergência de um dígito conta | 🟢 |
| `_reversa_sdd/migration/risk_register.md#RISK-005` | Estado global é vetor de contaminação; a correção é **estrutural** | 🟢 |
| `_reversa_sdd/migration/risk_register.md#RISK-006` | LGPD: dado genético sem retenção; vale a regra de não versionar dado real | 🟢 |
| `_reversa_sdd/migration/risk_register.md#RISK-008` | Decisor único; **cada onda é entregável fechado**, com critério de saída verificável | 🟢 |
| `_reversa_sdd/addenda/024-motivo-de-recusa-por-sobrenome.md#por-que-a-escala-medida` | A árvore unificada tem **35.460 pessoas** e os mesmos xrefs entre versões — a chave do cache de nomes colide (`L-24`) | 🟢 |
| `.reversa/principles.md#I` | Dado real de GEDCOM/DNA **nunca** entra no versionamento | 🟢 |
| `.reversa/principles.md#II` | Refatoração preserva comportamento observável; mudança de comportamento é feature | 🟢 |
| `.reversa/principles.md#III` | Nenhuma mudança sem teste que a cubra | 🟢 |

### 2.1 Linha de base medida antes de qualquer mudança (2026-10-17)

Árvore real do operador: `src/uploads/0fa3699e246caae1__Arvore_Unificada_Oficial_V1_2.ged`,
5.508.014 bytes, **35.460 pessoas**, **6.930 famílias**, grafo com 42.390 nós e 36.807 arestas.
Interpretador oficial `.venv` (Python 3.14.6), `ged4py==0.5.5`, sem `DATABASE_URL`.
Este par **é o oficial** para os números antes/depois (decisão de 2026-10-17 na §9).

| Etapa | Tempo | Observação |
|-------|------:|------------|
| Carga (`carregar_arvore`), 3 execuções no mesmo processo | **26,55 / 28,02 / 32,71 s** — mediana **28,02 s** | dispersão de 23 % entre execuções |
| Carga, 1ª execução em processo novo (cache frio) | **51,68 s** | quase o dobro da mediana — o cache do SO pesa |
| → passada `INDI` | 19,32 s | 71 % da carga |
| → passada `FAM` (para montar `families`) | 2,06 s | |
| → `build_graph_from_parser` (2ª passada `FAM` + grafo) | 2,39 s | |
| → 2ª materialização dos `FAM`, isolada | **1,80 s** | 6.930 registros relidos |
| → grafo montado sobre as famílias **já lidas** | 0,90 s | ganho atribuível ≈ **1,49 s** |
| Análise de DNA (`dna_analysis`, CSV `Famílias Sergipanas`, raiz `Adriano Santos`) | **54,05 s** | 93 cartões, 363 descartes |
| **Requisição completa** (carga + DNA, processo frio) | **105,73 s** | |

Outros dois baselines medidos no mesmo dia, porque são os portões da entrega: a **suíte completa**
dá **1.046 passam, 9 pulados, 0 falham** em 104,07 s (o pedido fala em 246 testes; esse número é de
uma era anterior do projeto — o que vale é a linha de base de hoje e a regra "nenhum teste
removido"); e o **harness de paridade** dá **24 divergências em 5 das 6 fixtures**, exit 1
(só `affinity.ged` está limpo). Ver a primeira lacuna da §10.

Chamadas ao parser na carga, medidas por instrumentação: `records0("INDI")` = **1**,
`records0("FAM")` = **2**; propriedade `index0` acessada **3** vezes; `_init_index`
executada **1** vez; `read_record` **49.321** = 1 (`HEAD`) + 35.460 (`INDI`) + 2 × 6.930 (`FAM`).

**Consequência para o pedido:** a "indexação repetida" **não acontece** — o índice de nível 0 é
construído uma vez e fica em cache no `GedcomReader`. O desperdício é a **segunda materialização
dos registros de família**. A afirmação "index0 chamado 3 vezes" está correta como contagem de
acesso à propriedade, mas **não** significa três varreduras do arquivo.

## 3. Personas e cenários de uso

| Persona | Objetivo | Cenário-chave |
|---------|----------|---------------|
| Operador (persona única, sem login) | Ver o resultado da análise sem esperar mais do que o necessário | Carrega a árvore unificada e roda o CSV de correspondentes; hoje espera ~105 s |
| Quem mantém o código | Reduzir trabalho redundante sem alterar um byte da saída | Mede, muda, mede de novo e prova a identidade da árvore e do resultado |
| Revisor de paridade | Confiar que a ordem de inserção não mudou | Compara grafo e `child_to_family` antes/depois, exatos, com o harness |

## 4. Regras de negócio novas ou alteradas

1. **RN-01: A árvore continua sendo um valor de quatro posições, com a mesma forma e a mesma ordem
   de inserção.** `people`, `families`, `graph` e `child_to_family` são o contrato (`@ordem`). 🟢
   - Origem no legado: `_reversa_sdd/upload-gedcom/requirements.md#5` (`RF-11` a `RF-14`)
   - Tipo: **preservada** (explicitada para esta feature)
2. **RN-02: cada registro de nível 0 do GEDCOM é materializado uma única vez por carga.** 🟢
   - Origem no legado: nenhuma — regra **nova**, derivada da medição de §2.1
   - Tipo: nova
3. **RN-03: a leitura do arquivo é autoridade única do parser; a construção do grafo não lê o
   arquivo.** A função que monta o grafo transforma dados já lidos. 🟡
   - Origem no legado: `_reversa_sdd/architecture.md#3` (responsabilidade de `parsers/`)
   - Tipo: nova (formaliza uma separação hoje vazada)
4. **RN-04: ganho de desempenho só é declarado com medição, e medição de uma execução única não é
   evidência.** O número precisa vir de processo próprio, com repetição e dispersão declarada. 🟢
   - Origem no legado: medição desta sessão (23 % de variação intraprocesso; 2× entre cache frio e quente)
   - Tipo: nova
5. **RN-05: dado real de GEDCOM/DNA não é versionado nem transcrito.** A evidência registra nome,
   tamanho, contagens e tempos — nunca nomes de pessoas, xrefs ou conteúdo de cM. 🟢
   - Origem no legado: `.reversa/principles.md#I`; `_reversa_sdd/migration/risk_register.md#RISK-006`
   - Tipo: preservada

## 5. Requisitos Funcionais

| ID | Requisito | Prioridade | Critério de aceite | Confidência |
|----|-----------|------------|--------------------|-------------|
| RF-01 | Medir a **requisição completa** com a árvore real — carga da árvore **e** análise de DNA — **antes** de qualquer mudança de código | Must | Relatório com o tempo de cada etapa (carga, `INDI`, `FAM`, grafo, DNA) e o total, produzido antes do primeiro commit de código | 🟢 |
| RF-02 | O instrumento de medição deve exercitar o **código de produção** (`carregar_arvore` + `application.dna_analysis`), não o oráculo congelado | Must | Um **instrumento irmão** na pasta `_reversa_sdd/parity/` mede carga e DNA; `_profile_big.py` permanece **byte a byte** como está, porque ele mede o oráculo e é régua | 🟢 |
| RF-03 | Registrar a **contagem de chamadas** ao parser, por tag, antes e depois | Must | Antes: `FAM` = 2 e `read_record` = 49.321; depois: `FAM` = 1 e `read_record` = 42.391 (−6.930) | 🟢 |
| RF-04 | Eliminar a segunda materialização dos registros de família: a construção do grafo passa a receber as famílias **já lidas** | Must | Uma carga da árvore real executa `records0("FAM")` **uma** vez | 🟢 |
| RF-05 | A saída deve ser **idêntica**: pessoas, famílias, grafo (nós, arestas e **ordem de inserção**) e `child_to_family`, comparados de forma exata, sem tolerância | Must | Igualdade exata de `list(graph.nodes())`, `list(graph.edges())`, `child_to_family` e das chaves de `people`/`families`, por comparação binária antes/depois | 🟢 |
| RF-06 | O resultado da **análise de DNA** deve ser idêntico, exato: cartões, descartados, ordem e valores | Must | Mesmo número de cartões (93) e de descartes (363), com a mesma ordem e os mesmos valores, comparados sem tolerância | 🟢 |
| RF-07 | Preservar o contrato público: `carregar_arvore(caminho)` devolve a mesma tupla; **nenhum** estado de módulo é criado; `core/` continua sem importar `parsers/` | Must | Assinatura e forma da tupla inalteradas; guardas de dependência do núcleo passam | 🟢 |
| RF-08 | Medir **depois**, com o mesmo instrumento, a mesma árvore e o mesmo CSV, em condições equivalentes | Must | Relatório "depois" com as mesmas etapas, mesma repetição e dispersão declarada | 🟢 |
| RF-09 | Provar a RN-02 por teste: a contagem de `records0("FAM")` numa carga é 1 | Must | Teste falha contra o código atual e passa depois da mudança | 🟢 |
| RF-10 | Rodar a paridade das 6 fixtures e registrar o resultado **sem nenhuma divergência nova** em relação à linha de base medida antes da mudança | Must | Relatório do harness para as 6 fixtures; as **24 divergências de hoje** ficam registradas como linha de base e a lista depois é comparada item a item — nenhuma nova, nenhuma fixture nova divergente | 🟢 |
| RF-11 | A suíte continua sem falha e **nenhum teste é removido** | Must | Suíte completa verde; número de testes coletados não diminui | 🟢 |
| RF-12 | Registrar em evidência o antes, o depois, a contagem de chamadas e o resultado da paridade | Must | Arquivo de evidência na pasta da feature, sem dado pessoal | 🟢 |
| RF-13 | Manter `ged4py` fixado no `requirements.txt` e não trocar o parser | Must | `requirements.txt` inalterado nessa dependência | 🟢 |

## 6. Requisitos Não Funcionais

| Tipo | Requisito | Evidência ou justificativa | Confidência |
|------|-----------|----------------------------|-------------|
| Desempenho | A carga **não pode ficar mais lenta**; o ganho medido deve ser reportado com mediana de ≥ 3 execuções e a dispersão | Medido: 26,55–32,71 s intraprocesso (23 %) e 51,68 s em cache frio; um número único não distingue ganho de ruído | 🟢 |
| Desempenho | O ganho esperado é **≈ 1,5 s na carga** (~5 %) e ~1,4 % da requisição; a feature **não** promete redução perceptível | Medido em §2.1; declarar mais que isso seria afirmação sem medição | 🟢 |
| Desempenho | Não criar cache de árvore, de índice nem de resultado — **fora de escopo** | Exige ADR próprio, trava e limite de memória; `_reversa_sdd/architecture.md#1` | 🟢 |
| Memória | Reaproveitar o dicionário de famílias já lido; não criar cópia adicional da coleção | O ganho não pode ser trocado por pico de memória; a árvore já ocupa ~42 mil nós | 🟡 |
| Determinismo | A saída deve ser idêntica em execuções repetidas e com `PYTHONHASHSEED` distintos | `@ordem` é contrato; `L-25` mostra que ordem sensível a hash já mordeu o projeto | 🟢 |
| Portabilidade | Rodar no `.venv` oficial (Python 3.14.6) com `ged4py==0.5.5` | Interpretador e pin são o ambiente de referência do projeto | 🟢 |
| Privacidade | Nenhum artefato da feature pode conter nome de pessoa, xref ou valor de cM da árvore real | `.reversa/principles.md#I`; `RISK-006` | 🟢 |
| Manutenibilidade | A leitura do arquivo fica no parser; a transformação em grafo deixa de depender de um objeto de I/O | Alta coesão e baixo acoplamento (pedido da feature); alternativa é manter o vazamento | 🟡 |
| Observabilidade | A medição é **artefato de desenvolvimento**, não instrumentação de runtime; nenhuma métrica nova entra na aplicação | A aplicação não tem telemetria, e esta feature não a introduz | 🟢 |

## 7. Critérios de Aceitação

```gherkin
Cenário: medição da requisição completa antes da mudança
  Dado a árvore real de 35.460 pessoas e o CSV de correspondentes do operador
  Quando o instrumento de produção roda a carga e a análise de DNA em processo próprio, com 3 repetições
  Então o relatório traz o tempo de cada etapa, o total, a mediana e a dispersão
  E traz a contagem de records0 por tag, de index0, de _init_index e de read_record
  E nenhuma linha do relatório contém nome de pessoa, xref ou valor de cM

Cenário: a indexação é construída uma vez e os registros FAM são materializados duas vezes
  Dado o código no início da feature
  Quando uma carga da árvore real é instrumentada
  Então records0("INDI") é chamado 1 vez e records0("FAM") é chamado 2 vezes
  E _init_index é executado 1 vez
  E read_record totaliza 49.321 chamadas

Cenário: a segunda leitura dos registros de família é eliminada
  Dado que a construção do grafo recebe as famílias já lidas na carga
  Quando uma carga da árvore real é instrumentada
  Então records0("FAM") é chamado 1 vez
  E read_record totaliza 42.391 chamadas

Cenário: a árvore produzida é idêntica, inclusive na ordem
  Dado o mesmo arquivo GEDCOM real
  Quando a árvore é carregada antes e depois da mudança
  Então as chaves de people e de families são iguais e na mesma ordem
  E list(graph.nodes()) e list(graph.edges()) são idênticos, na mesma ordem
  E child_to_family é idêntico, com as mesmas listas na mesma ordem

Cenário: o resultado da análise de DNA é idêntico
  Dado o mesmo par árvore + CSV e a mesma raiz
  Quando a análise roda antes e depois da mudança
  Então há o mesmo número de cartões e de descartados
  E a ordem e os valores são idênticos, comparados sem tolerância

Cenário: a paridade não ganha divergência nova
  Dado a linha de base de paridade registrada antes da mudança
  Quando o harness roda as 6 fixtures depois da mudança
  Então a lista de divergências é exatamente a mesma de antes
  E nenhuma fixture nova aparece divergente

Cenário: a medição depois é comparável com a de antes
  Dado a linha de base registrada antes da mudança
  Quando o mesmo instrumento roda o mesmo par árvore + CSV, com a mesma repetição
  Então o relatório traz as mesmas etapas e a mesma forma de mediana e dispersão
  E a comparação entre antes e depois é feita etapa por etapa

Cenário: os portões finais da entrega
  Dado a mudança aplicada
  Quando a suíte completa roda e a árvore de dependências é verificada
  Então a suíte não tem falha e o número de testes coletados não diminuiu
  E carregar_arvore continua recebendo só o caminho e devolvendo a tupla de quatro posições
  E nenhum módulo de core/ importa parsers/
  E ged4py continua fixado no requirements.txt

Caso negativo: árvore sem nenhuma família
  Dado um GEDCOM só com registros INDI
  Quando a árvore é carregada
  Então people é preenchido, families é vazio e o grafo contém apenas nós de pessoa
  E nenhuma exceção é levantada

Caso negativo: família sem xref_id
  Dado um GEDCOM com um registro FAM sem xref_id
  Quando a árvore é carregada
  Então essa família não vira nó, e nenhuma aresta é criada para ela
  E as pessoas continuam mapeadas em child_to_family pelas demais famílias

Caso negativo: arquivo que não é GEDCOM
  Dado um arquivo corrompido
  Quando a carga é tentada
  Então o erro continua sendo levantado como hoje, sem arquivo parcial utilizável
```

## 8. Prioridade MoSCoW

| Item | MoSCoW | Justificativa |
|------|--------|---------------|
| RF-01, RF-02, RF-03 (medir antes) | **Must** | Sem isso não há como decidir nem provar ganho — é a condição do pedido |
| RF-04 (eliminar a 2ª leitura) | **Must** | É o passo 2 do pedido, já confirmado pela contagem |
| RF-05, RF-06, RF-07 (identidade e contrato) | **Must** | `RISK-004`: divergência de um dígito invalida a entrega |
| RF-08 (medir depois) | **Must** | "Não declare ganho sem medição" |
| RF-09 (teste da contagem) | **Must** | Princípio III |
| RF-10 (paridade sem divergência nova) | **Must** | Portão de saída |
| RF-11, RF-13 (suíte e pin) | **Must** | Regressão e ambiente |
| RF-12 (evidência) | **Should** | Rastreabilidade; sem valor se as demais falharem |
| RNF de memória | **Should** | O ganho é pequeno; não vale trocá-lo por pico de memória |
| RNF de observabilidade | **Won't** | Métrica de runtime está fora do escopo |

## 9. Esclarecimentos

### Sessão 2026-10-17

- **Q:** A paridade está vermelha hoje — 24 divergências em 5 das 6 fixtures (só `affinity.ged`
  limpo), por mudanças declaradas de matching e janela de vida posteriores a 2026-10-13. Qual é o
  portão de saída desta feature?
  **R:** **"Nenhuma divergência nova".** As 24 de hoje viram a linha de base registrada; a feature
  não pode acrescentar nenhuma e não pode deixar fixture nova divergente. Corrigir o vermelho não
  entra no escopo desta feature.

- **Q:** O `_reversa_sdd/parity/_profile_big.py` mede o oráculo congelado, não `carregar_arvore`
  nem a análise de DNA atuais. Como medir o código de produção?
  **R:** **Instrumento irmão.** Um script novo ao lado dos demais `_*.py` da pasta mede carga e DNA
  do código de produção; `_profile_big.py` fica **byte a byte** como está, porque ele é a régua do
  oráculo.

- **Q:** Há três GEDCOM reais (5,5 / 8,0 / 8,9 MB) e dois CSVs. Qual par é o oficial para os
  números antes/depois?
  **R:** **`Arvore_Unificada_Oficial_V1_2.ged` (5,5 MB, 35.460 pessoas) + CSV `Famílias
  Sergipanas` + raiz `Adriano Santos`** — a combinação já medida. Não é preciso medir as três.

- **Q:** Confirmado que a leitura se repete, mas o ganho medido é ~1,5 s em ~105 s. O passo 2
  continua no escopo?
  **R:** **Sim, fazer o passo 2.** Remove 6.930 materializações redundantes e enxuga o acoplamento
  parser↔grafo; a identidade da saída já foi verificada na árvore real. O custo da passada `INDI`
  (19,3 s) é assunto de outra feature, não desta.

## 10. Lacunas

Nenhuma lacuna em aberto: as três dúvidas da versão inicial foram resolvidas na sessão de
2026-10-17 (§9).

Ficam **registrados, sem bloquear**, dois fatos medidos que não são dúvidas:

- a paridade tem 24 divergências **anteriores** a esta feature, e elas são a linha de base do
  portão (RF-10), não trabalho desta entrega;
- a passada `INDI` responde por 19,3 s dos ~28 s da carga, muito acima do que esta feature remove.

## 11. Histórico de alterações

| Data | Alteração | Autor |
|------|-----------|-------|
| 2026-10-17 | Versão inicial gerada por `/reversa-requirements`, com linha de base medida nesta sessão e três lacunas abertas | reversa |
| 2026-10-17 | `/reversa-clarify`: quatro decisões integradas (portão de paridade, instrumento irmão, par oficial de medição, passo 2 confirmado); três `[DÚVIDA]` zeradas | reversa |

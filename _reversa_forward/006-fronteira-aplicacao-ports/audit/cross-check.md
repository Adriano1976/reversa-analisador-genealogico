# Cross-check: fronteira de aplicação em `src/` — `application/` + `ports/` (Onda 2 do cutover)

> Identificador da feature: `006-fronteira-aplicacao-ports`
> Data: `2026-10-07`
> Artefatos analisados:
> - `_reversa_forward/006-fronteira-aplicacao-ports/requirements.md`
> - `_reversa_forward/006-fronteira-aplicacao-ports/roadmap.md`
> - `_reversa_forward/006-fronteira-aplicacao-ports/actions.md`
>
> Leitura auxiliar: `data-delta.md`, `investigation.md`, `onboarding.md`, `_reversa_sdd/domain.md`, `_reversa_sdd/architecture.md`, `_reversa_sdd/migration/paradigm_decision.md`, `_reversa_sdd/migration/ambiguity_log.md`.
>
> Escopo medido: **20 requisitos funcionais**, **10 requisitos não funcionais**, **18 cenários Gherkin**, **10 decisões técnicas**, **25 ações**.

## Resumo

| Severidade | Quantidade | Fechados |
|---|---|---|
| CRITICAL | **1** | 1 |
| HIGH | **2** | 2 |
| MEDIUM | **3** | 2 |
| LOW | **1** | 0 |
| **Total** | **7** | **5** |

> ⚠️ **Este relatório é um retrato de 2026-10-07, antes das correções.** Os findings `A001`, `A002`, `A003`, `A004` e `A005` foram fechados na sessão de esclarecimento de auditoria da mesma data, com as decisões registradas em `requirements.md` §9 (`### Sessão 2026-10-07 (auditoria)`), na `D-11` e na `D-12` do `roadmap.md` e nas ações `T001`, `T012`, `T019`, `T026` a `T031` do `actions.md`.
>
> **Duas correções que a sessão fez contra este relatório**, e que ficam registradas por honestidade:
>
> 1. No `A001`, o achado recomendou levar a sinalização ao resultado do caso de uso, com a nota de que o parser não a produz hoje. A sessão foi além do achado: verificou que o `AMB-015` classifica a sinalização como **recomendação pendente**, nunca aprovada como decisão, e que carregá-la exigiria mexer na forma congelada da árvore. A `RF-19` foi **estreitada** — aceitar, não criar a aresta, não levantar exceção, e proibir rejeitar —, e a sinalização virou questão aberta em §10.
> 2. No `A003`, o achado sugeriu uma enumeração de "três ou quatro valores". A sessão fixou **três valores, todos alcançáveis**, e recusou explicitamente um quarto valor para "entrada inválida", pelo mesmo motivo que o `A002` deu para remover o `ArmazenamentoInvalido`: nenhum caminho o preencheria.
>
> **`A006` e `A007` seguem abertos e são cosméticos.** O `A006` (três nomes para o mesmo artefato: "adaptador de entrada", `src/app.py` e "a borda") e o `A007` (o `actions.md` não repete o comando de medição) não bloqueiam a execução.

## Findings

| ID | Severidade | Eixo | Descrição | Onde está | Situação |
|----|-----------|------|-----------|-----------|----------|
| A001 | **CRITICAL** | Cobertura + coerência com o legado | A `RF-19` exige que o resultado do carregamento carregue a **sinalização tipada** das referências pendentes. O parser **não tem** sinalização alguma: uma referência pendente é descartada em silêncio por `g.has_node()`. A ação `T002` apenas troca o tipo levantado em `dna_analysis.py`; a ação `T025` verifica telas e as três mensagens negativas do upload. Nenhuma ação implementa nem verifica a sinalização, e o sinal não existe no legado para ser preservado | `requirements.md` §5 `RF-19` e §7 cenário "Referência pendente é sinalizada e não rejeitada"; `src/parsers/gedcom_parser.py:40-46`; `actions.md` `T001`, `T025` | ✅ **fechado** — `RF-19` estreitada, cenário reescrito, sinalização em §10 |
| A002 | **HIGH** | Cobertura | Dois tipos da hierarquia não têm requisito que os autorize. `ArmazenamentoInvalido` aparece **só** em `D-01`/`T001` — nenhum `RF` descreve quando ele é levantado, e a leitura do adaptador mostra que ele pode nunca ser levantado. `CsvIlegivel` tem ponto de levantamento (`T003`) e teste (`T010`), mas também nenhum `RF` | `requirements.md` §5 (nenhuma menção a `ArmazenamentoInvalido` nem a `CsvIlegivel`); `roadmap.md` `D-01`; `actions.md` `T001`, `T003` | ✅ **fechado** — `RF-21` nova para o `CsvIlegivel`; `ArmazenamentoInvalido` removido |
| A003 | **HIGH** | Consistência + coerência com o legado | A `RF-20` proíbe que o parâmetro `success=` atravesse a fronteira, e o roadmap não define onde o resultado tipado carrega essa semântica. Sem ela o adaptador **não consegue** reproduzir o comportamento de hoje: `path_search_flow` devolve `success=True` com `path_result=None` para "nenhuma conexão encontrada", e `success=False` para "pessoa não encontrada". Os dois casos são visualmente diferentes na tela e colapsariam num só | `requirements.md` §5 `RF-20`; `src/core/path_search.py:183-185` e `:136-138`; `src/app.py:240-244`; `roadmap.md` §3 (nenhuma decisão sobre a semântica do resultado) | ✅ **fechado** — campo de desfecho de 3 valores; `D-11`, `D-12`, `T012`, `T019`, `T026` |
| A004 | MEDIUM | Consistência | Os três tipos que o `paradigm_decision.md` nomeia em inglês (`RootPersonNotFound`, `UnsupportedGedcom`, `DnaCsvMissingColumns`) aparecem **3 vezes cada** no `requirements.md` e **zero** vezes no roadmap e no actions, que usam os nomes em português (`PessoaNaoEncontrada`, `GedcomNaoSuportado`, `DnaCsvSemColunas`). A troca é justificada no `investigation.md` §6, mas os dois artefatos que a executam não citam os nomes que o requisito usa | `requirements.md` §4 e §5 `RF-03`; `roadmap.md` `D-01`; `actions.md` `T001`; justificativa em `investigation.md` §6 | ✅ **fechado** — decisão de nomenclatura registrada em §9; nomes em inglês zerados nos três artefatos |
| A005 | MEDIUM | Cobertura | Quatro cenários Gherkin do `requirements.md` não têm ação que os verifique: "Upload sem arquivo…" e "Upload com nome de arquivo vazio…"; "GEDCOM não reconhecido é recusado antes da gravação"; e "O port de repositório exige o dono". O cenário "Corpo acima do teto…" tem verificação **parcial**: `tests/test_upload_seguranca.py:154` confere o status `413` e a ausência de gravação, mas **não** o literal | `requirements.md` §7; `actions.md` Fases 2 e 5 | ✅ **fechado** — `T027` a `T031` acrescentadas |
| A006 | MEDIUM | Consistência | O módulo alvo das ações de integração é `src/app.py`, mas o papel que elas descrevem ("monta as dependências de diagrama na borda", "traduz exceção pela tabela") é o que o `roadmap.md` §5 chama de **adaptador de entrada**, e o `T004` chama de "adaptador de entrada". Os três nomes convivem para a mesma coisa | `roadmap.md` §5 e `D-04`; `actions.md` `T004`, `T016`-`T019` | ⬜ aberto (cosmético) |
| A007 | LOW | Consistência | O `actions.md` não repete o comando de medição nem a forma exata da saída esperada, o que deixa a verificação dependente do texto do `onboarding.md` | `requirements.md` §6; `onboarding.md` §2 e §3; `actions.md` `T021`-`T023` | ⬜ aberto (cosmético) |

## Detalhe dos findings CRITICAL e HIGH

### A001, CRITICAL — a `RF-19` pede um sinal que não existe

O `requirements.md` §7 traz o cenário:

> **Referência pendente é sinalizada e não rejeitada** — *"Então o resultado do carregamento carrega a sinalização das referências pendentes"*.

A leitura do parser mostra que esse sinal **não existe** e nunca existiu. Em `src/parsers/gedcom_parser.py:40-46`, cada referência é filtrada por `g.has_node(...)`:

```python
if husband_id and g.has_node(husband_id):
    g.add_edge(husband_id, fam_id)
```

Quando a referência é pendente, a aresta simplesmente não entra e **nada é registrado**. Não há campo, aviso, contador ou observação. O mesmo vale para `CHIL` e `FAMC`/`FAMS`.

Três consequências, em ordem de gravidade:

1. **O critério de aceite da `RF-19` é inverificável.** Não há como escrever teste que passe sem implementar algo novo. Uma ação futura só pode falhar ou inventar.
2. **O `AMB-015` registrava "aceitar e apenas sinalizar" como recomendação do Designer, e a decisão de 2026-10-07 citou essa recomendação ao escolher aceitar.** A parte "aceitar" é o que o legado faz; a parte "sinalizar" foi transportada para o requisito como se já fosse comportamento existente, e não é.
3. **A tensão com a paridade é real e precisa ser decidida, não presumida.** Sinalizar no resultado do caso de uso é inofensivo para o harness, que compara a árvore e a lista de nomes. Sinalizar na **resposta HTTP** é mudança de comportamento observável e quebra a paridade de telas — ou seja, é exatamente o que o `AMB-015` recusou ao descartar a alternativa de rejeitar.

**Direção de correção, para o humano escolher.** Há dois caminhos, e eles são diferentes:

- **Estreitar a `RF-19` ao que é verificável hoje:** manter "aceita, e a aresta não entra", remover a exigência de sinalização tipada do critério de aceite e registrar a sinalização como feature própria — ela é mudança de comportamento pelo Princípio II, e o `AMB-015` já a tratava como decisão em aberto. Custo: nenhuma ação nova.
- **Implementar a sinalização no resultado do caso de uso, sem levá-la à tela:** exige pelo menos uma ação nova (o parser devolver as referências pendentes) e um teste. Preserva a paridade porque a resposta HTTP não muda.

Nenhum dos dois é decisão do auditor. O caminho é `/reversa-clarify` para reabrir a `RF-19`, ou edição manual do `requirements.md` seguida de nova decomposição da ação afetada.

### A002, HIGH — dois tipos de exceção sem requisito que os autorize

O `requirements.md` §5 `RF-03` fixa **três** tipos nomeados. A `D-01` e o `T001` criam **cinco**. Os dois a mais não têm requisito:

- **`ArmazenamentoInvalido`.** A busca por ele nos três artefatos encontra **uma** ocorrência no roadmap (`D-01`) e **uma** no actions (`T001`). Nenhuma descreve a condição que o levanta. Lendo o adaptador que o `T007` vai escrever, o caminho é: `_guardar_upload` recebe o resultado de `validar_conteudo_gedcom` e devolve uma **mensagem**, não uma exceção. Um adaptador que delegue fielmente a `validate.py` **nunca levanta `ArmazenamentoInvalido`** — ele devolve o motivo, como hoje. O tipo nasce sem ponto de levantamento, e o `T009` (o teste da hierarquia) só prova que ele é capturável como `ValueError`, não que ele é usado.
- **`CsvIlegivel`.** Tem ponto de levantamento (`T003`, em `csv_ingest.py:177`) e tem teste (`T010`), mas nenhum `RF` descreve o comportamento que ele representa. A `RF-03` só cita raiz não encontrada, GEDCOM não reconhecido e CSV sem colunas. Um tipo com ponto de levantamento mas sem requisito é requisito faltando, não código a mais.

**Por que isso é HIGH e não LOW.** O eixo de cobertura exige que toda decisão do roadmap tenha ação correspondente — e tem. O problema é na direção contrária: o roadmap decidiu criar dois tipos que o `requirements.md` não pede. Sem requisito, a implementação fica sem critério de aceite, e a revisão de código não tem contra o que conferir. A correção é acrescentar o requisito que falta (uma `RF` para o comportamento do CSV ilegível, e uma decisão sobre `ArmazenamentoInvalido`: ou ganha condição de levantamento descrita, ou sai da hierarquia) — caminho `/reversa-clarify` ou edição manual.

**Achado colateral do mesmo ponto:** o `RF-03` diz que cada tipo "é levantado pelo ponto que **detecta** a condição, não pelo adaptador", mas os dois tipos que o adaptador detecta (`GedcomNaoSuportado` e `ArmazenamentoInvalido`) só podem ser levantados **pelo** adaptador. A frase, como está, contradiz a si mesma para metade dos tipos.

### A003, HIGH — a semântica de `success` não tem onde viver depois da extração

Hoje a rota distingue dois casos que se parecem:

| Caso | Retorno do núcleo | O que a tela faz |
|---|---|---|
| Pessoa não encontrada | `(None, "Pessoa 1 'X' não encontrada.", False)` | Alerta de erro |
| Nenhuma conexão encontrada | `(None, "Nenhuma conexão encontrada entre 'X' e 'Y'.", True)` | Resultado, **com sucesso** |

O código da rota separa os dois por uma única linha, em `src/app.py:240`:

```python
if not success and path_result is None:
    return render_template(..., message=msg, success=False)
return render_template(..., path_result=path_result, message=msg, success=True)
```

A `RF-20` proíbe que `success=` atravesse a fronteira, e faz bem: é parâmetro de template. Mas o **fato** que ele carrega — "esta mensagem é um alerta de erro" contra "esta mensagem acompanha um resultado" — é comportamento observável, e precisa de um lugar no resultado tipado. O `roadmap.md` §3 não tem nenhuma decisão sobre isso: a `D-04` trata da tradução de exceção para mensagem, e o caminho de "nenhuma conexão" **não é exceção** — é retorno normal do núcleo.

**O risco concreto.** Sem um campo que declare o caráter do resultado, a implementação mais natural é o adaptador inferir do texto da mensagem — e aí o texto de tela vira dado de decisão, que é a inversão que esta feature existe para corrigir. A alternativa igualmente natural, tratar todo retorno sem caminho como erro, muda o comportamento da tela e quebra a paridade visual.

**Direção de correção.** Uma decisão no `roadmap.md` §3 fixando **qual campo** do resultado tipado carrega essa distinção — candidato natural: um campo de tipo enumerado que declare o desfecho (`sucesso`, `sem_resultado`, `entrada_invalida`), do qual o adaptador deriva o `success=`. Isso exige uma ação na Fase 3 (declarar o campo nos três resultados) e ajuste nas ações de integração. Caminho: `/reversa-clarify` ou edição manual do `roadmap.md` e do `actions.md`.

## Itens verificados que passaram

### Eixo 1, Cobertura

- Os **20 requisitos funcionais** foram confrontados um a um com as **10 decisões** e as **25 ações**. **18 dos 20** têm cobertura por ação: `RF-01` (`T011`-`T018`), `RF-02` (`T005`, `T006`), `RF-03` (`T001`), `RF-04` (`T002`, `T003`, `T014`), `RF-05` (`T001`, `T009`), `RF-06` (`T014`, `T019`), `RF-07` (`T016`, `T019`), `RF-08` (`T008`), `RF-09` (`T007`, `T011`), `RF-10` (`T007`), `RF-12` (`T025`), `RF-13` (`T009` e a guarda existente), `RF-14` (`T018`), `RF-15` e `RF-16` (`T021`-`T023`), `RF-17` (`T025`), `RF-18` (`T024`), `RF-20` (`T011`-`T013`). Os dois sem cobertura adequada são `RF-19` (`A001`) e `RF-11`, que por decisão **não deve** ter ação nova — o fallback Latin-1 é preservado por não ser tocado, e a `T003` verifica explicitamente que ele não foi.
- **13 dos 18 cenários Gherkin** têm verificação nomeada. Os cinco restantes estão em `A005` e `A001`.
- Toda decisão técnica tem pelo menos uma ação, **exceto** `D-07` (o adaptador delega para `validate.py` em vez de reimplementar), cuja execução está embutida na `T007` sem citação — coberto por `A002`, no ponto do `ArmazenamentoInvalido`.

### Eixo 2, Consistência

- **Nenhum identificador fantasma.** As 25 dependências foram resolvidas por varredura: todas apontam para IDs de ação existentes. As referências cruzadas a `RF-01` a `RF-20`, `D-01` a `D-10`, `RN-01` a `RN-06`, `T001` a `T025`, `AMB-015`, `AMB-024`, `W003`, `OBS-10`, `DEV-005`, `BR-D-15` e `ADRs 02/16/17/18/20` foram conferidas contra os documentos de origem — todas existem.
- **Vocabulário de domínio consistente** entre os três documentos: "árvore", "referência armazenada", "caso de uso", "porta", "adaptador de entrada", "resultado tipado", "mensagem de contrato", "teto de 16 MB". A única divergência é a dos nomes de exceção, em `A004`, e a dos três nomes do adaptador, em `A006`.
- **`interfaces/` não existe, e o roadmap declara por quê** (§7), com a razão amarrada à `RN-05`. O eixo 2.3 é satisfeito por ausência justificada, não por omissão.

### Eixo 3, Coerência com o legado

- **As 9 mensagens congeladas de `12-paridade-telas.feature` têm todas um destino declarado.** As de entrada e de arquivo viajam como campo de contrato do resultado (`RF-04`, `RF-06`, `RF-20`); as de sucesso e de sem-resultado vêm do núcleo sem alteração. A lista foi conferida contra `_reversa_sdd/domain.md#5.1` e `#5.2`, literal a literal, e nenhuma decisão do roadmap as contradiz.
- **Nenhuma decisão contradiz regra 🟢 do legado.** Foram conferidas as regras que a feature toca: `domain.md#4` (o GEDCOM é re-parseado a partir da chave recebida antes de ramificar — preservado por `RF-09` e `T007`), `domain.md#3.5` (upload gravado sob chave de conteúdo — preservado por `RF-09`), `domain.md#3.7` (ordem de apresentação documental primeiro — intocada, e o `RF-15` a protege por paridade), `domain.md#5` (contrato de mensagens — `RN-04` e `RF-17`).
- **Os componentes citados existem.** `src/core/dna_analysis.py`, `src/core/genetic_evidence.py`, `src/parsers/csv_ingest.py`, `src/parsers/gedcom_parser.py`, `src/utils/validate.py`, `src/app.py` e `_reversa_sdd/parity/harness.py` foram todos conferidos em disco. As linhas citadas (`dna_analysis.py:127` e `:152`, `genetic_evidence.py:125`, `csv_ingest.py:177`, `app.py:52` e `:217`) foram lidas e contêm o que as ações afirmam.
- **As três decisões que desviam do `requirements.md` foram rastreadas e são coerentes com ele:** `D-01` (exceções em `core/erros.py`) honra a direção de import que o `RF-13` exige; `D-02` (porta do carregador) honra `RF-01` e `RF-02` sem acoplar a aplicação a `parsers/`; `D-06` (remover a casca) **fortalece** `RF-12` e a política que a feature 005 fixou, e a varredura confirma que a casca tem **zero** consumidores de produção.
- **As preservações negativas estão declaradas e não foram contrariadas:** dívida #3 (`RN-06`, `W003`), dívida #5, dívida #10 e `cm_estimator` aparecem no `roadmap.md` §5 e no `data-delta.md` §6 como **inalteradas**, e nenhuma ação as toca.

### Eixo 4, Sanidade do actions

- **25 ações, 25 IDs únicos, zero auto-dependência, zero ciclo.** O grafo foi percorrido e a maior cadeia tem **7 ações** (6 elos), por dois caminhos: `T001 → T003 → T010 → T007 → T013 → T018 → T023` e `T019 → T020 → T025`.
- **As 4 ações marcadas `[//]` não compartilham arquivo alvo** — `T004`, `T006`, `T009`, `T015`. Verificado por varredura da coluna de arquivo alvo.
- **As cinco ações que editam `src/app.py`** (`T004`, `T016`, `T017`, `T018`, `T019`) **não** carregam a marca, e a nota da fase explica por quê. Esta é a correção que a própria decomposição aplicou depois de uma primeira versão ter marcado `T016` e `T017` indevidamente; a varredura confirma que a versão gravada está correta.
- **Todas as 25 ações começam com status `[ ]`**, nenhuma já fechada, e nenhuma ação é de "configurar IDE", "rodar lint" ou "abrir PR".
- **Zero premissas.** O `roadmap.md` §4 declara "Nenhuma", e a conferência confirma: os únicos casamentos de `[DÚVIDA]` nos artefatos são menções históricas ao registro da sessão de esclarecimento de 2026-10-07.

## Nota sobre a ordem dos findings

O `A001` é o único CRITICAL porque é o único que **bloqueia a execução**: uma ação que implemente a `RF-19` como escrita não tem comportamento definido para implementar, e uma que a ignore produz entregável que não satisfaz o próprio critério de aceite. O `A002` e o `A003` são HIGH porque ambos deixam buracos que só aparecem no meio do `T007`, do `T014` e do `T019` — o ponto em que o executor precisa de uma resposta que os artefatos não dão.

Nenhum dos sete findings exige refazer o plano: cinco são ajustes de uma linha em um dos três documentos, e dois (`A001` e `A003`) pedem uma decisão sua. O que **não** se sustenta é seguir para o `/reversa-coding` com o `A001` aberto, porque a primeira ação que tocar o parse vai ou inventar o sinal ou descobrir que ele não existe — e nos dois casos o resultado é retrabalho.

## Histórico de alterações

| Data | Alteração | Autor |
|------|-----------|-------|
| 2026-10-07 | Auditoria inicial gerada por `/reversa-audit` | reversa |
| 2026-10-07 | Situação dos findings atualizada após a sessão de esclarecimento de auditoria: `A001` a `A005` fechados; `A006` e `A007` seguem abertos e cosméticos. O corpo do relatório **não** foi reescrito — ele continua sendo o retrato de antes das correções, como registro do que a auditoria encontrou | reversa |

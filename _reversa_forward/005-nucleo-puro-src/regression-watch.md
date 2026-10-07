# Regression Watch: núcleo puro em `src/core/`

> Identificador da feature: `005-nucleo-puro-src`
> Data: `2026-10-06`
> Rodada: **parcial** — Fase 1 (Preparação), ações `T001` a `T004`
> Base do watch: seção "Modificadas" de `legacy-impact.md`
>
> ⚠️ **Este arquivo tem DUAS rodadas**, pelo mesmo motivo do `legacy-impact.md`: a
> rodada 1 cobriu o instrumento de paridade, e a **rodada 2** (ao final) cobre a
> remoção do estado global. Os watch items `W002` a `W004` são os que têm peso de
> regressão para a entrega real.

## Rodada 1 — Fase 1 (Preparação), `T001` a `T004`

### Itens sob vigilância (rodada 1)

> O watch principal recebe apenas regras que **eram 🟢** e foram alteradas ou removidas. Esta rodada **não alterou nenhuma regra de negócio** — o que mudou é instrumento de verificação. Por isso há **um** item no watch principal e o resto vai para Observações.

| ID | Origem (arquivo, seção) | Regra esperada após mudança | Tipo de verificação | Sinal de violação |
|---|---|---|---|---|
| **W001** | `_reversa_sdd/parity/harness.py`, contrato dos coletores | O harness executa o oráculo **congelado** e o candidato `src/`, e ambos os coletores recebem o diretório de CSVs de DNA como parte do contrato. O oráculo permanece apontado para `_reversa_sdd/oracle/app_legacy_e43ca22.py` | `presença` | Se o harness passar a apontar para `src/app.py` ou para `reconstructed/`, a validação vira circular (RISK-002). Se um coletor for chamado sem o diretório de CSVs, o probe de aceitação morre com `IndexError` |

## Observações

> Sem peso de regressão. Registradas porque uma leitura futura precisa saber que existem.

| ID | Observação | Por que importa |
|---|---|---|
| **OBS-01** | O probe de aceitação (`dna`) **não isola** as regras A/B/C/D da busca de caminho: o campo `motivo` do legado funde "recusado por score" com "aceito sem caminho". O probe mede o resultado observável da análise inteira | Quem ler "paridade 100% no probe `dna`" não pode concluir que as cinco ramificações de aceitação estão provadas isoladamente. A `RF-10` pedia isolamento; o que se entregou é cobertura ponta a ponta, por impossibilidade técnica do lado do oráculo |
| **OBS-02** | O cM agregado **não** é comparado pelo probe `dna`, porque diverge por desenho: o legado soma os segmentos do nome; o candidato agrupa por kit. Medido: 3.760 vs o valor do kit em `cm_boundaries.csv` sobre `basic.ged` | Evita que alguém "conserte" o probe reintroduzindo uma comparação que produziria divergência falsa |
| **OBS-03** | Mensagens de erro são comparadas por **modo** (`ok`, `erro`, `raiz_ausente`, `arquivo_ausente`, `sem_arquivo`, `outro`), nunca por texto | O legado responde `Ocorreu um erro: None` e o candidato nomeia a causa. Comparar texto acusaria divergência de redação, que o `parity_specs.md` manda asserir fora da comparação |
| **OBS-04** | Nas fixtures `affinity`, `deep25`, `no_name` e `variants`, a raiz do probe (`Ana Silva`, via `PARITY_ROOT`) não existe, e os dois lados devolvem `raiz_ausente`. Nelas o probe mede o caminho de recusa, não a aceitação | A aceitação é exercitada de fato em `basic.ged` e `mojibake_latin1.ged`, que contêm `Ana Silva`. Um probe futuro com raiz por fixture cobriria mais |
| **OBS-05** | O probe `decomposicao` só é avaliado nas fixtures que têm `affinity.ged` ao lado | É a mitigação do RISK-011, e é o probe que o `parity_specs.md` §Riscos residuais descrevia como faltante |
| **OBS-06** | O `--gedcom` do harness agora é normalizado para caminho absoluto | O coletor faz `chdir` antes de usar o caminho; um caminho relativo passado pelo usuário falhava com `FileNotFoundError` |

## Histórico de alterações

| Data | Alteração | Autor |
|------|-----------|-------|
| 2026-10-06 | Versão inicial criada por `/reversa-coding` na execução de `T001` a `T004` (rodada parcial, Fase 1) | reversa |

---
---

## Rodada 2 — Integração e Polimento, `T009` a `T029` ⚠️ **O WATCH DA ENTREGA**

> Data: `2026-10-07`
> Base do watch: seção "Modificadas" da rodada 2 do `legacy-impact.md`
> Acrescentada retroativamente pelo `/reversa-sync`.

### Itens sob vigilância (rodada 2)

> O watch principal recebe regras que **eram 🟢** e foram alteradas ou removidas.
> A rodada 1 não alterou nenhuma; a rodada 2 alterou **o mecanismo de integração**,
> que é contrato observável para quem reimplementar. Daí três itens.

| ID | Origem (arquivo, seção) | Regra esperada após mudança | Tipo de verificação | Sinal de violação |
|---|---|---|---|---|
| **W002** | `_reversa_sdd/architecture.md#1`, "mecanismo de integração" | A árvore é **valor**, não estado: as funções do núcleo a recebem por parâmetro e `carregar_arvore` a **devolve**. Não existe escrita de global em `src/` | `ausência` | Se qualquer módulo de `src/core/` voltar a declarar `people`/`families`/`graph`/`child_to_family`/`versao` em nível de módulo, ou se `carregar_arvore` voltar a fazer `clear()`/`update()`, a `RF-01` é violada. Detectado por `tests/test_dependencias_nucleo.py` e pelo passo 7/8 do `onboarding.md` |
| **W003** | `_reversa_sdd/architecture.md#7`, dívida #3 (contaminação entre requisições) | **A dívida NÃO está fechada.** O vetor "estado global reescrito por requisição + 4 threads" deixou de existir, mas a guarda de instância única continua sendo de **processo, não de thread** | `presença` | Se alguém declarar que a contaminação entre requisições foi resolvida por esta feature, está errado: o que saiu foi o estado de domínio compartilhado. Thread-safety geral (I/O, `src/uploads/`) segue aberta — é a lacuna `L-16` / `M-03` |
| **W004** | `_reversa_sdd/erd-complete.md`, entidade `ESTADO_VERSAO` | A entidade **não existe mais**, e a razão dela também não: a invalidação do índice de nomes é derivada do **conteúdo** de `people`, nunca de `id()` | `presença` | Se o cache de `_INDICE_DE_NOMES` voltar a ser chaveado por `id(people)`, o cache pode devolver o mapa de um GEDCOM diferente — `id()` é reciclado quando o dicionário anterior perde a referência. **Este defeito não aparece em teste isolado**, só sob carga com GEDCOMs sucessivos |

### Observações (rodada 2)

> Sem peso de regressão.

| ID | Observação | Por que importa |
|---|---|---|
| **OBS-07** | `cm_estimator.py` **permanece em disco** e continua sendo legado fora do fluxo, mas **deixou de ser reexportado** por `dna_analysis` (`T022`) | A dívida #18 do `architecture.md#7` está **parcialmente** fechada: o arquivo existe por decisão explícita da ação, e o que saiu foi a fachada. Não confundir "não é mais reexportado" com "foi removido" |
| **OBS-08** | Os ciclos de pacote (dívida #5) **não** foram tocados | `core/` ↔ `reporting/` e `core/` ↔ `parsers/` continuam idênticos. Esta feature removeu o estado, não o ciclo; `mermaid_render` segue recebendo a árvore por resolvedor injetado |
| **OBS-09** | O erro de ambiente da suíte é pré-existente e não é regressão | Os 15 erros são `PermissionError` de `setup` em `tests/test_upload_seguranca.py`, presentes já na linha de base de `T004`, que media "15 errors". A suíte precisa de `TEMP`/`TMP` gravável |
| **OBS-10** | A verificação manual (`T029`) **deixa resíduo** em `src/uploads/` | Subir o app grava o GEDCOM enviado. O `_clean_residue.py` limpa só instrumento de paridade e **não** remove isso — conferir `git status` antes de commitar (Princípio I) |

## Histórico de re-extrações

> Preenchido pelo agente reverso quando `/reversa` rodar de novo. Vazio nesta data.

## Arquivadas

> Vazio nesta data.

### Histórico de alterações (rodada 2)

| Data | Alteração | Autor |
|------|-----------|-------|
| 2026-10-06 | Versão inicial criada por `/reversa-coding` na execução de `T001` a `T004` (rodada parcial, Fase 1) | reversa |
| 2026-10-07 | **Rodada 2** acrescentada retroativamente pelo `/reversa-sync`: `W002` (a árvore é valor), `W003` (a dívida #3 **não** está fechada) e `W004` (`ESTADO_VERSAO` extinto; `id()` nunca é chave), mais `OBS-07` a `OBS-10` | reversa |

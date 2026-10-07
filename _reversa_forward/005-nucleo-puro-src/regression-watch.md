# Regression Watch: núcleo puro em `src/core/`

> Identificador da feature: `005-nucleo-puro-src`
> Data: `2026-10-06`
> Rodada: **parcial** — Fase 1 (Preparação), ações `T001` a `T004`
> Base do watch: seção "Modificadas" de `legacy-impact.md`

## Itens sob vigilância

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

## Histórico de re-extrações

> Preenchido pelo agente reverso quando `/reversa` rodar de novo. Vazio nesta data.

## Arquivadas

> Vazio nesta data.

## Histórico de alterações

| Data | Alteração | Autor |
|------|-----------|-------|
| 2026-10-06 | Versão inicial criada por `/reversa-coding` na execução de `T001` a `T004` (rodada parcial, Fase 1) | reversa |

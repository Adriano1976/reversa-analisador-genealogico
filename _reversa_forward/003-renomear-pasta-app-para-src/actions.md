# Actions: renomear a raiz da aplicação de `analisador-genealogico/` para `src/`

> Identificador: `003-renomear-pasta-app-para-src`
> Data: `2026-10-02`
> Roadmap: `_reversa_forward/003-renomear-pasta-app-para-src/roadmap.md`

## Resumo

| Métrica | Valor |
|---------|-------|
| Total de ações | 21 |
| Paralelizáveis (`[//]`) | 17 |
| Maior cadeia de dependência | 8 |

## Fase 1, Preparação

| ID | Descrição | Dependências | Paralelismo | Arquivo alvo | Confidência | Status |
|----|-----------|--------------|-------------|--------------|-------------|--------|
| T001 | Medir a linha de base da suíte de testes e gravar a saída em arquivo de evidência | - | `[//]` | `_reversa_forward/003-renomear-pasta-app-para-src/evidence/gate0-suite-antes.txt` | 🟢 | `[X]` |
| T002 | Medir a linha de base do comparador de paridade e gravar a saída em arquivo de evidência | - | `[//]` | `_reversa_forward/003-renomear-pasta-app-para-src/evidence/gate0-paridade-antes.txt` | 🟢 | `[X]` |
| T003 | Registrar a contagem de arquivos e a soma de bytes da pasta de upload antes da movimentação | - | `[//]` | `_reversa_forward/003-renomear-pasta-app-para-src/evidence/upload-antes.txt` | 🟢 | `[X]` |

## Fase 2, Testes

**Não se aplica.** A decisão D-06 do roadmap determinou não criar teste novo: a suíte existente já exercita a importação do aplicativo, o `root_path` forçado e a renderização da tela, que é exatamente o que um caminho errado quebraria. Criar teste redundante inflaria a suíte e mudaria a contagem da linha de base, que é o critério de RF-06. O gate de testes desta feature está na Fase 5.

## Fase 3, Núcleo

| ID | Descrição | Dependências | Paralelismo | Arquivo alvo | Confidência | Status |
|----|-----------|--------------|-------------|--------------|-------------|--------|
| T004 | Renomear a raiz de código em uma única operação de renomeação do versionador | T001, T002, T003 | - | `analisador-genealogico/` → `src/` | 🟢 | `[X]` |
| T005 | Mover a pasta de upload por movimentação de sistema de arquivos, conferindo contagem e bytes contra a evidência de T003 | T004 | `[//]` | `analisador-genealogico/uploads/` → `src/uploads/` | 🟢 | `[X]` |
| T006 | Descartar o cache de bytecode e remover o README herdado do módulo e o arquivo de ignore do módulo | T004 | `[//]` | `src/README.md`, `src/.gitignore.txt` | 🟢 | `[X]` |
| T007 | Remover o diretório vazio de artefatos estáticos e o diretório antigo remanescente, confirmando que ficou vazio | T005, T006 | - | `src/static/`, `analisador-genealogico/` | 🟢 | `[X]` |
| T008 | Mover o arquivo de dependências para a raiz do repositório | T004 | `[//]` | `requirements.txt` | 🟢 | `[X]` |
| T009 | Atualizar os 9 pontos de caminho nos 8 arquivos de teste, incluindo a definição da pasta do aplicativo que alimenta o `root_path` e o caminho do arquivo de entrada | T004 | `[//]` | `tests/*.py` | 🟢 | `[X]` |
| T010 | Atualizar a configuração do analisador estático para a nova raiz de código | T004 | `[//]` | `pyrefly.toml` | 🟢 | `[X]` |
| T011 | Atualizar a configuração do editor para o novo diretório | T004 | `[//]` | `.vscode/settings.json` | 🟢 | `[X]` |

## Fase 4, Integração

| ID | Descrição | Dependências | Paralelismo | Arquivo alvo | Confidência | Status |
|----|-----------|--------------|-------------|--------------|-------------|--------|
| T012 | Atualizar os scripts de instrumentação que resolvem a raiz de código, e a linha do log que identifica o candidato | T004 | `[//]` | `_reversa_sdd/parity/harness.py`, `_reversa_sdd/parity/_check_split_types.py`, `_reversa_sdd/parity/_golden_capture.py` | 🟢 | `[X]` |
| T013 | Atualizar a contraprova de paridade, incluindo a string de busca que ela guarda e que ficaria obsoleta em silêncio (D-08); confirmar que a verificação continua encontrando o que procura | T004 | `[//]` | `_reversa_sdd/parity/_verify_fix_gives_parity.py` | 🟢 | `[X]` |
| T014 | Atualizar os scripts que apontam para a pasta de upload e o runner do oráculo | T005 | `[//]` | `_reversa_sdd/parity/_profile_big.py`, `_reversa_sdd/parity/_profile_collector_costs.py`, `_reversa_sdd/parity/_scr005_find_trio.py`, `_reversa_sdd/oracle/run_oracle.py` | 🟢 | `[X]` |
| T015 | Atualizar o README da raiz: caminhos, comandos de instalação e execução, e remoção das linhas da árvore que descrevem os artefatos extintos | T007, T008 | `[//]` | `README.md` | 🟢 | `[X]` |

## Fase 5, Polimento

| ID | Descrição | Dependências | Paralelismo | Arquivo alvo | Confidência | Status |
|----|-----------|--------------|-------------|--------------|-------------|--------|
| T016 | Rodar a suíte de testes e comparar o resultado com a evidência de T001, confirmando que nenhum teste foi removido ou desabilitado | T009, T010, T011, T012, T013, T014 | `[//]` | `_reversa_forward/003-renomear-pasta-app-para-src/evidence/gate1-suite-depois.txt` | 🟢 | `[X]` |
| T017 | Rodar o comparador de paridade, confirmar 100% sem divergência nova e limpar o resíduo gerado | T012, T013, T014 | `[//]` | `_reversa_forward/003-renomear-pasta-app-para-src/evidence/gate2-paridade-depois.txt` | 🟢 | `[X]` |
| T018 | Varrer o conjunto vivo por referência residual ao nome antigo e registrar o resultado | T009, T010, T011, T012, T013, T014, T015 | `[//]` | `_reversa_forward/003-renomear-pasta-app-para-src/evidence/varredura-residual.txt` | 🟢 | `[X]` |
| T019 | Conferir que nenhum arquivo de dado real entrou no versionamento, em nenhuma profundidade | T005, T008 | `[//]` | `_reversa_forward/003-renomear-pasta-app-para-src/evidence/versionamento.txt` | 🟢 | `[X]` |
| T020 | Publicar o adendo da feature em `_reversa_sdd/addenda/`, registrando as remoções e as citações de caminho que ficaram desatualizadas nas specs | T016, T017, T018, T019 | - | `_reversa_sdd/addenda/003-renomear-pasta-app-para-src.md` | 🟢 | `[X]` |
| T021 | Regenerar o mini-site de documentação para refletir a árvore nova | T020 | - | `_reversa_docs/` | 🟡 | `[ ]` |

## Notas de execução

**Pré-requisito bloqueante, que não é ação de agente.** A renomeação de T004 exige que `src/**` e `.vscode/**` constem em `allowedPaths` de `.reversa/reversa-config.json`. A edição desse arquivo é ato exclusivo do usuário — o agente não pode fazê-la, e sem ela a escrita no destino é recusada pela política de edição do legado. T001 a T003 podem ser executadas antes, sem impedimento.

**A pasta de upload não é versionada.** A renomeação de T004 é uma operação do versionador e, por isso, não alcança `uploads/`: ela permanece no diretório antigo até T005, que a move por movimentação de sistema de arquivos. São 9 arquivos reais, 16.920.784 bytes. Copiar e apagar não é alternativa aceitável (D-02).

**Registro histórico não é tocado.** T012 a T014 editam scripts executáveis de instrumentação. Nenhum arquivo de `_reversa_bugs/`, `_reversa_refactor/` ou `_reversa_forward/` é editado, e nenhuma spec de `_reversa_sdd/` é reescrita: a correção documental vai no adendo de T020 (RN-03).

### Rodada 1 — 2026-10-03

**Fase 1 concluída; Fase 3 interrompida e retomada.** T001 a T003 mediram a linha de base: suíte com **118 aprovados e 15 erros de ambiente**; paridade em **100% nas 6 fixtures**; **9 arquivos e 16.920.784 bytes** na pasta de upload. A T004 foi bloqueada porque o `allowedPaths` ainda não continha `src/**` nem `.vscode/**`, com status `failed` em `progress.jsonl`. O usuário liberou os dois caminhos e a execução foi retomada.

**Segundo bloqueio, de natureza diferente.** Mesmo com a política liberada, a renomeação falhou porque três processos externos tinham o diretório como diretório corrente — uma janela de terminal e dois processos do servidor de desenvolvimento iniciados a partir dela em 2026-10-02. Nenhum era do agente, e nenhum arquivo interno estava travado: os filhos do diretório renomeavam normalmente, o que isolou a causa no diretório corrente de processos vivos. Resolvido pelo usuário.

**Fatos medidos que corrigem o plano.** A renomeação do versionador moveu **todo** o diretório, incluindo o conteúdo não versionado. A pasta de upload chegou ao destino na mesma operação atômica, sem a janela de duplicação que a T005 presumia; a T005 passou a ser a **conferência** de integridade (9 arquivos e 16.920.784 bytes conferidos contra a evidência de T003), e não uma segunda movimentação. Isso é melhor do que o plano previa.

**Correção de premissa em D-08.** A decisão afirmava que atualizar só o caminho real deixaria a contraprova de paridade "silenciosamente sem efeito, sem erro nenhum". **Isso está errado**: o script tem uma asserção explícita com mensagem de ajuste, então a falha seria ruidosa. A ação determinada por D-08 continua correta e foi executada; o que se corrige é a justificativa.

### Rodada 2 — correções e ressalvas

**Defeito de escopo no próprio verificador de varredura.** A primeira execução do script de T018 varreu também os arquivos de documentação dentro do diretório do oráculo, e reportou 9 "ocorrências inesperadas". Eram todas `ORACLE_MANIFEST.md` e `RECUPERACAO-20260929.md` — documentação da extração, preservada por decisão (RN-03) e corrigida por adendo. O escopo foi restringido à instrumentação executável (apenas `.py` nesses dois diretórios), e o veredito passou a zero inesperadas. O defeito era do verificador, não do repositório.

**Duas exceções aceitas e declaradas na varredura residual:**

1. `src/reconstructed/__init__.py` — a ocorrência é o **nome do projeto** numa docstring, não um caminho. O pacote foi reconstruído a partir do projeto `analisador-genealogico`, e o projeto não foi renomeado: apenas a raiz de código. Manter é correto, e o verificador a classifica como esperada.
2. `_reversa_sdd/oracle/run_oracle.py` — a ocorrência está numa linha que emite o comando `git show e43ca22:analisador-genealogico/app.py`, contra o **commit congelado**, onde o caminho era esse. Reescrevê-la produziria um comando que falha, porque aquele commit não tem `src/`.

**T021 permanece pendente.** A regeneração do mini-site de documentação é executada pelo pipeline de documentação, não pelo ciclo de codificação. O `[ ]` fica registrado, e a pendência é reportada ao usuário em vez de simulada.

**Incidente de execução, registrado por transparência.** Ao atualizar o status das três primeiras ações por linha de comando, o `actions.md` foi gravado com codificação dupla: o `Get-Content` do PowerShell 5.1 leu o arquivo UTF-8 como Windows-1252 e a gravação seguinte corrompeu os caracteres acentuados. O mesmo comando gerou o `progress.jsonl` com registros separados por espaço em vez de quebra de linha. Ambos foram reparados por reescrita completa e reverificados. A lição operacional: neste ambiente, arquivo com acento nunca é reescrito por `Get-Content` sem `-Encoding`, e conteúdo multilinha vai pela ferramenta de escrita, não por concatenação no shell.

## Histórico de alterações

| Data | Alteração | Autor |
|------|-----------|-------|
| 2026-10-02 | Versão inicial gerada por `/reversa-to-do` | reversa |
| 2026-10-03 | Rodada 1 de `/reversa-coding`: T001 a T003 concluídas; T004 bloqueada pela política e retomada após liberação de `src/**` e `.vscode/**`; T004 a T020 executadas; T021 pendente; reparo do próprio arquivo após corrupção de codificação | reversa-coding |

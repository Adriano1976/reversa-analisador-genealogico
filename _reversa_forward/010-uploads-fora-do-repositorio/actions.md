# Actions: Uploads fora do repositÃ³rio

> Identificador: `010-uploads-fora-do-repositorio`
> Data: `2026-10-09`
> Roadmap: `_reversa_forward/010-uploads-fora-do-repositorio/roadmap.md`

## Resumo

| MÃ©trica | Valor |
|---------|-------|
| Total de aÃ§Ãµes | **24** |
| ParalelizÃ¡veis (`[//]`) | **7** (`T001`, `T002`, `T004`, `T007`, `T008`, `T012`, `T024`) |
| Maior cadeia de dependÃªncia | **7 aÃ§Ãµes** (6 elos): `T001` â†’ `T005` â†’ `T006` â†’ `T010` â†’ `T011` â†’ `T018` â†’ `T021` |
| Linha de base herdada | `282 passed`, `8 skipped`, paridade `100 %` â€” medidos em 2026-10-08, **antes** do plano |

> **A ordem tem trÃªs pontos que nÃ£o sÃ£o preferÃªncia, sÃ£o o plano.**
> **(1)** A paridade Ã© medida antes de tudo (`T003`) executando o harness **com a pasta definida Ã  mÃ£o no
> ambiente** â€” Ã© a prova empÃ­rica do mecanismo de `D-07`, e ela precisa existir antes de o invÃ³lucro ser
> escrito.
> **(2)** A migraÃ§Ã£o (`T013`) acontece **antes** de a aplicaÃ§Ã£o ser apontada para o destino (`T014`,
> `T015`): apontar primeiro faria a pasta nova responder "arquivo nÃ£o existe mais" para referÃªncias que a
> pasta antiga ainda resolvia.
> **(3)** Nada aqui apaga arquivo do operador. A remoÃ§Ã£o da pasta antiga Ã© passo manual dele, descrito no
> `onboarding.md` Â§12 â€” nenhuma aÃ§Ã£o desta tabela a executa.

## Fase 1, PreparaÃ§Ã£o

<!-- Setup, scaffolding, migraÃ§Ãµes iniciais, configuraÃ§Ã£o de infraestrutura local. -->

| ID | DescriÃ§Ã£o | DependÃªncias | Paralelismo | Arquivo alvo | ConfidÃªncia | Status |
|----|-----------|--------------|-------------|--------------|-------------|--------|
| T001 | Registrar o inventÃ¡rio de origem: nome, bytes e `sha256` de cada arquivo de `src/uploads/`, mais os totais. Ã‰ a Ã¢ncora de todas as conferÃªncias seguintes | - | `[//]` | `_reversa_forward/010-uploads-fora-do-repositorio/evidence/inventario-origem.txt` | ðŸŸ¢ | [X] |
| T002 | Registrar a linha de base da suÃ­te (`pytest -q`) com aprovados, pulados e erros, para comparaÃ§Ã£o posterior | - | `[//]` | `_reversa_forward/010-uploads-fora-do-repositorio/evidence/linha-de-base-suite.txt` | ðŸŸ¢ | [X] |
| T003 | Registrar a linha de base da paridade executando o harness **com `ANALISADOR_UPLOAD_FOLDER` definido Ã  mÃ£o no ambiente** e conferindo que a pasta real nÃ£o ganhou arquivo. Prova o mecanismo de `D-07` antes de o invÃ³lucro existir, e fixa `PARIDADE 100 %` como nÃºmero de partida | T001 | - | `_reversa_forward/010-uploads-fora-do-repositorio/evidence/linha-de-base-paridade.txt` | ðŸŸ¢ | [X] |
| T004 | Criar o destino canÃ´nico confirmado pelo operador â€” proposto `D:\dados-genealogicos\uploads`, fora da Ã¡rvore do repositÃ³rio. O caminho escolhido vale para os dois modos | - | `[//]` | `D:\dados-genealogicos\uploads` (fora do repositÃ³rio) | ðŸŸ¢ | [X] |

## Fase 2, Testes

<!-- Testes que precisam existir antes ou logo apÃ³s o nÃºcleo. -->

| ID | DescriÃ§Ã£o | DependÃªncias | Paralelismo | Arquivo alvo | ConfidÃªncia | Status |
|----|-----------|--------------|-------------|--------------|-------------|--------|
| T005 | Escrever os testes da migraÃ§Ã£o, com arquivos **sintÃ©ticos** em pasta temporÃ¡ria (PrincÃ­pio I): cÃ³pia que confere `sha256` arquivo a arquivo, origem que permanece intacta, repetiÃ§Ã£o idempotente e divergÃªncia de hash que **nÃ£o** sobrescreve o destino nem remove a origem | T001 | - | `tests/test_manutencao_de_uploads.py` | ðŸŸ¢ | [X] |
| T006 | Acrescentar ao mesmo arquivo de `T005` os testes do manifesto e do expurgo: a simulaÃ§Ã£o nÃ£o remove nada; a aplicaÃ§Ã£o remove apenas o que estÃ¡ no manifesto; cada falha de remoÃ§Ã£o aparece nomeada no relatÃ³rio; duplicatas byte a byte idÃªnticas sÃ£o relatadas e **permanecem** no disco; manifesto vazio devolve relatÃ³rio vazio sem erro; link simbÃ³lico e caminho fora da pasta alvo sÃ£o recusados | T005 | - | `tests/test_manutencao_de_uploads.py` | ðŸŸ¢ | [X] |
| T007 | Escrever os testes do invÃ³lucro: ele define a variÃ¡vel **antes** de lanÃ§ar o harness, localiza o instrumento pelo caminho do repositÃ³rio, repassa os argumentos recebidos e devolve o mesmo cÃ³digo de saÃ­da do harness | - | `[//]` | `tests/test_rodar_paridade.py` | ðŸŸ¢ | [X] |
| T008 | Escrever o teste de documentaÃ§Ã£o: a tabela de variÃ¡veis do `README.md` lista `ANALISADOR_UPLOAD_FOLDER` e o caminho de execuÃ§Ã£o da paridade aponta para o invÃ³lucro. **Falha antes de `T019`** â€” Ã© a prova do PrincÃ­pio III para a entrega documental | - | `[//]` | `tests/test_documentacao_do_upload.py` | ðŸŸ¢ | [X] |

## Fase 3, NÃºcleo

<!-- LÃ³gica central da feature. -->

| ID | DescriÃ§Ã£o | DependÃªncias | Paralelismo | Arquivo alvo | ConfidÃªncia | Status |
|----|-----------|--------------|-------------|--------------|-------------|--------|
| T009 | Implementar o verbo `migrar` da ferramenta (`--origem`, `--destino`, `--relatorio`): cÃ³pia com conferÃªncia de `sha256` por arquivo, idempotÃªncia e recusa de sobrescrever destino divergente | T005 | - | `tests/manutencao_de_uploads.py` | ðŸŸ¢ | [X] |
| T010 | Implementar o verbo `manifesto` (`--pasta`, `--saida`): gera a lista revisÃ¡vel com nome, `sha256` e **motivo** por arquivo, regenerÃ¡vel por comando, a partir de um critÃ©rio explÃ­cito de resÃ­duo de instrumento | T006 | - | `tests/manutencao_de_uploads.py` | ðŸŸ¢ | [X] |
| T011 | Implementar o verbo `expurgo` (`--manifesto`, `--dry-run`, `--aplicar`, `--relatorio`): a simulaÃ§Ã£o lista e nÃ£o remove; a aplicaÃ§Ã£o remove apenas o que estÃ¡ no manifesto e relata removidos, preservados, duplicatas e falhas | T006, T010 | - | `tests/manutencao_de_uploads.py` | ðŸŸ¢ | [X] |
| T012 | Implementar o invÃ³lucro `rodar_paridade.py`: define a pasta de upload para um diretÃ³rio descartÃ¡vel e invoca o harness, **sem editar o instrumento** (`D-07`) | T007 | `[//]` | `tests/rodar_paridade.py` | ðŸŸ¢ | [X] |

## Fase 4, IntegraÃ§Ã£o

<!-- Cola com outras partes do sistema, contratos externos, ganchos. -->

| ID | DescriÃ§Ã£o | DependÃªncias | Paralelismo | Arquivo alvo | ConfidÃªncia | Status |
|----|-----------|--------------|-------------|--------------|-------------|--------|
| T013 | Executar a migraÃ§Ã£o dos arquivos para o destino canÃ´nico e conferir os dois lados por `sha256`, com a origem intacta. Registrar a saÃ­da | T004, T009 | - | `_reversa_forward/010-uploads-fora-do-repositorio/evidence/migracao-conferida.txt` | ðŸŸ¢ | [X] |
| T014 | Apontar o modo local para o destino canÃ´nico, subir a aplicaÃ§Ã£o e provar a continuidade (envio da Ã¡rvore, busca de caminho, anÃ¡lise de DNA), conferindo que `src/uploads/` nÃ£o ganhou arquivo | T013 | - | `_reversa_forward/010-uploads-fora-do-repositorio/evidence/T014-verificacao-local.md` | ðŸŸ¢ | [X] |
| T015 | Ajustar o ponto de montagem do serviÃ§o `app` no `docker-compose.yml` para a pasta canÃ´nica do host, mantendo o alvo interno que a aplicaÃ§Ã£o jÃ¡ deriva | T013 | - | `docker-compose.yml` | ðŸŸ¢ | [X] |
| T016 | Provar o modo contÃªiner: continuidade na tela pela porta publicada e preservaÃ§Ã£o dos arquivos depois de derrubar e subir a composiÃ§Ã£o. Se a montagem exigir compartilhamento de drive indisponÃ­vel, registrar e aplicar o recuo declarado | T015 | - | `_reversa_forward/010-uploads-fora-do-repositorio/evidence/T016-conteiner.md` | ðŸŸ¢ | [X] |
| T017 | Provar que a paridade executada pelo invÃ³lucro mantÃ©m `100 %` e deixa o inventÃ¡rio da pasta real **idÃªntico** ao de `T001` â€” nenhum arquivo novo, nenhum hash alterado (`RF-04`) | T012, T013 | - | `_reversa_forward/010-uploads-fora-do-repositorio/evidence/T017-isolamento-do-instrumento.md` | ðŸŸ¢ | [X] |
| T018 | Gerar o manifesto de resÃ­duo da pasta de origem e rodar a simulaÃ§Ã£o, conferindo que nada foi removido e que as duplicatas aparecem **relatadas**, nÃ£o removidas (`D-06`) | T011, T013 | - | `_reversa_forward/010-uploads-fora-do-repositorio/evidence/manifesto-residuo.txt` | ðŸŸ¢ | [X] |

## Fase 5, Polimento

<!-- Logs, telemetria, mensagens de erro, documentaÃ§Ã£o curta. -->

| ID | DescriÃ§Ã£o | DependÃªncias | Paralelismo | Arquivo alvo | ConfidÃªncia | Status |
|----|-----------|--------------|-------------|--------------|-------------|--------|
| T019 | Corrigir e ampliar o `README.md`: a variÃ¡vel na tabela de configuraÃ§Ãµes, o destino canÃ´nico, o caminho de execuÃ§Ã£o da paridade e a correÃ§Ã£o das afirmaÃ§Ãµes que deixaram de ser verdadeiras | T008 | - | `README.md` | ðŸŸ¢ | [X] |
| T020 | Provar por `diff` que `src/**` e `_reversa_sdd/**` **nÃ£o** foram tocados e que a mudanÃ§a se limita a `tests/**`, `README.md` e `docker-compose.yml` (`D-08`) | T019 | - | `_reversa_forward/010-uploads-fora-do-repositorio/evidence/T020-conferencia-de-escopo.md` | ðŸŸ¢ | [X] |
| T021 | Atualizar o `onboarding.md` da feature com os nÃºmeros medidos (arquivos, bytes, resÃ­duo) e os caminhos reais das evidÃªncias produzidas, e corrigir o passo 2 do documento: a linha de base da paridade Ã© medida com a variÃ¡vel definida Ã  mÃ£o no ambiente, porque o invÃ³lucro ainda nÃ£o existe no estado de partida | T018 | - | `_reversa_forward/010-uploads-fora-do-repositorio/onboarding.md` | ðŸŸ¢ | [X] |
| T022 | Gerar o `regression-watch.md` com os itens de vigilÃ¢ncia desta entrega, sem reciclar IDs de features anteriores | T017, T020 | - | `_reversa_forward/010-uploads-fora-do-repositorio/regression-watch.md` | ðŸŸ¢ | [X] |
| T023 | Executar a verificaÃ§Ã£o manual pelo `onboarding.md` e registrar o que passou, o que falhou e o que fica pendente do operador â€” incluindo a decisÃ£o de apagar a pasta antiga, que **nÃ£o** Ã© executada aqui | T022 | - | `_reversa_forward/010-uploads-fora-do-repositorio/evidence/T023-verificacao-manual.md` | ðŸŸ¢ | [X] |
| T024 | Limpar o resÃ­duo do instrumento (`.parity-run-*`, `_collect_*.py`, `_obs_*.json`) com o limpador existente e registrar o que foi removido e o que permaneceu | T017 | `[//]` | `_reversa_forward/010-uploads-fora-do-repositorio/evidence/T024-limpeza-de-residuo.md` | ðŸŸ¢ | [X] |

## Notas de execuÃ§Ã£o

<!--
Reservado para /reversa-coding registrar avisos ou observaÃ§Ãµes que surgiram durante a execuÃ§Ã£o.
NÃ£o use isso para corrigir aÃ§Ãµes, edits manuais ficam fora desse arquivo, vÃ£o direto no cÃ³digo.
-->

## HistÃ³rico de alteraÃ§Ãµes

| Data | AlteraÃ§Ã£o | Autor |
|------|-----------|-------|
| 2026-10-09 | VersÃ£o inicial gerada por `/reversa-to-do` | reversa |

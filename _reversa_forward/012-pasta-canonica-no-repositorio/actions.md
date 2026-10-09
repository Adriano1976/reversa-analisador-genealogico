# Actions: Pasta canônica de uploads dentro do repositório

> Identificador: `012-pasta-canonica-no-repositorio`
> Data: `2026-10-09`
> Roadmap: `_reversa_forward/012-pasta-canonica-no-repositorio/roadmap.md`

## Resumo

| Métrica | Valor |
|---------|-------|
| Total de ações | 25 |
| Paralelizáveis (`[//]`) | 14 |
| Maior cadeia de dependência | 11 (`T001 → T011 → T012 → T015 → T016 → T018 → T019 → T020 → T022 → T024 → T025`) |

> **Duas notas de leitura.** (1) Onde a coluna "Arquivo alvo" nomeia `evidence/…`, a ação é de
> **execução e medição**, e o arquivo alvo é a evidência que ela produz. (2) A `T025` é do estágio
> `/reversa-sync`, que é quem cria adendos neste projeto (roadmap §8, passo 7); ela fica aqui porque
> `RF-05` é requisito da feature e o critério de pronto depende dela.

## Fase 1, Preparação

| ID | Descrição | Dependências | Paralelismo | Arquivo alvo | Confidência | Status |
|----|-----------|--------------|-------------|--------------|-------------|--------|
| T001 | Conferir o estado do ambiente **antes de qualquer remoção**: `docker compose ps` mais os processos `python` do host, registrando a saída. **Não** usar a tabela de portas, que se mostrou não confiável (`D-11`) | - | - | `_reversa_forward/012-pasta-canonica-no-repositorio/evidence/T001-estado-do-ambiente.txt` | 🟢 | [X] |
| T002 | Restaurar a linha de `volumes:` do serviço `app` em `docker-compose.yml` para `- ./src/uploads:/app/src/uploads`, sem nenhum caminho absoluto de host (`RF-01`, `D-02`) | T001 | - | `docker-compose.yml` | 🟢 | [X] |
| T003 | Recriar o serviço `app` com `docker compose up -d` e conferir que `/app/src/uploads` volta a existir dentro do contêiner com **36** entradas. **Proibido `down -v`**: ele apaga o volume do banco (`D-11`) | T002 | `[//]` | `_reversa_forward/012-pasta-canonica-no-repositorio/evidence/T003-conteiner-recreado.txt` | 🟢 | [X] |
| T004 | Provar que a composição voltou ao estado entregue pela feature 008: `git diff HEAD -- docker-compose.yml` **vazio**, registrado como evidência (`RF-01`, `D-02`) | T002 | `[//]` | `_reversa_forward/012-pasta-canonica-no-repositorio/evidence/T004-compose-restaurado.txt` | 🟢 | [X] |

## Fase 2, Testes

| ID | Descrição | Dependências | Paralelismo | Arquivo alvo | Confidência | Status |
|----|-----------|--------------|-------------|--------------|-------------|--------|
| T005 | Escrever o teste das guardas do Princípio I com as asserções de **linha literal** e de **efeito** (`git check-ignore -v` nomeando `.gitignore`), mais a asserção de **ordem** de `src/uploads/` depois de `!src/**` no `.dockerignore` (`RF-11`, `D-04`) | T001 | `[//]` | `tests/test_guardas_do_armazenamento.py` | 🟢 | [X] |
| T006 | Acrescentar ao mesmo teste a verificação por **mutação**: sobre cópia temporária de cada arquivo, a linha é removida e a asserção tem de **falhar** (`D-05`) | T005 | - | `tests/test_guardas_do_armazenamento.py` | 🟢 | [X] |
| T007 | Corrigir a justificativa de `tests/test_documentacao_do_upload.py`: o texto deixa de afirmar que é a documentação que mantém a pasta fora do repositório, e a exigência da variável na tabela de configuração continua (`RF-08`) | T001 | `[//]` | `tests/test_documentacao_do_upload.py` | 🟢 | [X] |

## Fase 3, Núcleo

| ID | Descrição | Dependências | Paralelismo | Arquivo alvo | Confidência | Status |
|----|-----------|--------------|-------------|--------------|-------------|--------|
| T008 | Reescrever a seção "Onde ficam os arquivos enviados" do `README.md` declarando `src/uploads` como a pasta canônica e **única**, e ajustar a linha de `ANALISADOR_UPLOAD_FOLDER` na tabela de configurações para o papel de sobreposição — **respeitando o limite de 120 colunas** do repositório (`RF-02`) | T001 | `[//]` | `README.md` | 🟢 | [X] |
| T009 | Acrescentar à mesma seção as **duas guardas** do Princípio I (`.gitignore` com `uploads/`, `.dockerignore` com `src/uploads/`) e o aviso de que `git clean -xdf` e `-Xdf` **apagam** a pasta, porque ela é não rastreada (`RF-03`) | T008 | - | `README.md` | 🟢 | [X] |
| T010 | Varrer o `README.md` atrás das afirmações que a reversão tornou falsas e corrigi-las: a árvore do projeto (a linha que diz que a pasta canônica fica fora do repositório), o comando de exemplo que define a variável para fora e o comando `migrar` apresentado como procedimento (`RF-02`, `RN-06`) | T009 | - | `README.md` | 🟢 | [X] |
| T011 | Escrever o instrumento *fail-closed* de remoção das cópias de arrasto: por diretório, ele confere que **todo `sha256` ocorre em `src/uploads`** e cancela a remoção daquele diretório se houver qualquer órfão (`RF-09`, `D-03`) | T001 | `[//]` | `_reversa_forward/012-pasta-canonica-no-repositorio/evidence/_remover_copias_de_arrasto.py` | 🟢 | [X] |
| T012 | Executar o instrumento e registrar a evidência: três diretórios removidos, **0 órfãos**, `src/uploads` inalterado em 36 arquivos e 27.932.474 bytes (`RF-09`) | T011 | - | `_reversa_forward/012-pasta-canonica-no-repositorio/evidence/remocao-das-copias-de-arrasto.txt` | 🟢 | [X] |

## Fase 4, Integração

| ID | Descrição | Dependências | Paralelismo | Arquivo alvo | Confidência | Status |
|----|-----------|--------------|-------------|--------------|-------------|--------|
| T013 | Executar `registrar-diff.py` e `verificar-estrutura.py` do refactor e registrar a saída, provando **por execução** que a retirada não quebrou os instrumentos (premissa de §4 do roadmap) | T012 | `[//]` | `_reversa_forward/012-pasta-canonica-no-repositorio/evidence/T013-instrumentos-do-refactor.txt` | 🟡 | [X] |
| T014 | Provar que `src/` não mudou e que o git não ganhou linha: `git diff -- src` vazio e `git status --porcelain` sem novidade (`D-01`) | T012 | `[//]` | `_reversa_forward/012-pasta-canonica-no-repositorio/evidence/T014-src-intacto.txt` | 🟢 | [X] |
| T015 | Rodar a suíte com `DATABASE_URL` **ausente** e registrar; esperado `327 passed, 9 skipped` (`RF-06`) | T012 | `[//]` | `_reversa_forward/012-pasta-canonica-no-repositorio/evidence/T015-suite.txt` | 🟢 | [X] |
| T016 | Rodar a paridade pelo invólucro `tests/rodar_paridade.py`, conferir `PARIDADE 100 %` e inventário de `src/uploads` idêntico antes e depois (`RF-07`) | T015 | - | `_reversa_forward/012-pasta-canonica-no-repositorio/evidence/T016-paridade.txt` | 🟢 | [X] |
| T017 | Revisar o `onboarding.md` da 010 **no lugar**: bloco `> **Revisto em 2026-10-09 (feature 012).**` por seção afetada, texto anterior preservado, e a **seção 12 deixando de mandar apagar `src/uploads/`** (`RF-12`, `D-06`) | T010 | `[//]` | `_reversa_forward/010-uploads-fora-do-repositorio/onboarding.md` | 🟢 | [X] |

## Fase 5, Polimento

| ID | Descrição | Dependências | Paralelismo | Arquivo alvo | Confidência | Status |
|----|-----------|--------------|-------------|--------------|-------------|--------|
| T018 | Regenerar o manifesto do resíduo e rodar a **simulação** do expurgo, registrando `removidos: 18`, `recusados: 0` e o inventário ainda com 36 arquivos (`RF-10`, `D-07`) | T016 | - | `_reversa_forward/012-pasta-canonica-no-repositorio/evidence/manifesto-residuo-012.txt` | 🟢 | [X] |
| T019 | Aplicar o expurgo e conferir que `src/uploads` termina com **18 arquivos**, sem remover nada fora do manifesto (`RF-10`) | T018 | - | `_reversa_forward/012-pasta-canonica-no-repositorio/evidence/expurgo-aplicado-012.txt` | 🟢 | [X] |
| T020 | Regenerar o manifesto **depois** do expurgo e provar que devolve **0** entradas; registrar as duplicatas que restam (`D-12`) | T019 | `[//]` | `_reversa_forward/012-pasta-canonica-no-repositorio/evidence/manifesto-pos-expurgo.txt` | 🟢 | [X] |
| T021 | Recapturar os números das duas abas **nas duas unidades** — árvore 7 arquivos / 6 itens, DNA 10 arquivos / 10 itens — e registrar para a feature 011 (`D-08`) | T019 | `[//]` | `_reversa_forward/012-pasta-canonica-no-repositorio/evidence/T021-numeros-finais.txt` | 🟢 | [X] |
| T022 | Preencher a tabela "Resultados medidos" (§15) do `onboarding.md` da 012 com o que foi efetivamente medido em cada passo | T020, T021 | - | `_reversa_forward/012-pasta-canonica-no-repositorio/onboarding.md` | 🟢 | [X] |
| T023 | Escrever o `legacy-impact.md` da feature, listando cada arquivo tocado, o tipo de impacto e a evidência que o sustenta | T022 | `[//]` | `_reversa_forward/012-pasta-canonica-no-repositorio/legacy-impact.md` | 🟢 | [X] |
| T024 | Escrever o `regression-watch.md`, com os itens de vigilância, o que cada um vigia e o sintoma que o dispara | T022 | `[//]` | `_reversa_forward/012-pasta-canonica-no-repositorio/regression-watch.md` | 🟢 | [X] |
| T025 | Escrever o adendo `_reversa_sdd/addenda/012-pasta-canonica-no-repositorio.md`, superando o adendo 010 **em parte** e listando o que permanece válido dele (ferramenta, invólucro e linha da variável). **Estágio `/reversa-sync`** (`RF-05`, `D-10`) | T024 | - | `_reversa_sdd/addenda/012-pasta-canonica-no-repositorio.md` | 🟢 | [X] |

## Notas de execução

- **Ordem destrutiva é deliberada.** `T012` (arrastos) vem antes de `T018`/`T019` (resíduo) porque o
  critério de cancelamento de `T011` compara contra `src/uploads`, e expurgar antes mudaria a referência
  da comparação no meio da feature (`D-08`).
- **A suíte tem de rodar com `DATABASE_URL` ausente.** Medido: com a variável no ambiente, 2 testes de
  `tests/test_persistencia_desabilitada.py` falham e a suíte dá `325 passed, 2 failed, 9 skipped`. Não é
  regressão desta feature.
- **`down -v` está proibido** em `T003`: o `-v` remove o volume nomeado do banco.

## Histórico de alterações

| Data | Alteração | Autor |
|------|-----------|-------|
| 2026-10-09 | Versão inicial gerada por `/reversa-to-do` | reversa |

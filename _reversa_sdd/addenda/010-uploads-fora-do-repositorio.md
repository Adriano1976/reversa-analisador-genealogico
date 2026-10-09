# Adendo: uploads fora do repositório

> Identificador da feature: `010-uploads-fora-do-repositorio`
> Data: `2026-10-09`
> Cenário: **legado** (âncora em `_reversa_sdd/architecture.md` + `_reversa_sdd/domain.md`)

## Vigência

Vigente desde 2026-10-09.

## Resumo da entrega

A extração descreve o armazenamento como `<raiz do repositório>/src/uploads` — o único estado persistente
do sistema. Esta feature tirou esse dado da árvore do repositório **sem tocar em uma linha de `src/`**: o
que mudou foi o **modo de operação declarado**. A pasta canônica de dados passou a viver fora do
repositório nos dois modos de execução, os 36 arquivos e 27.932.474 bytes existentes foram **copiados** com
conferência de `sha256` (a origem permanece intacta), a composição de contêineres passou a montar a pasta
canônica no alvo interno que o aplicativo já deriva, e o instrumento de paridade deixou de escrever as
suas sondas na pasta real do operador — a origem medida do resíduo. Entrou também uma ferramenta de
manutenção com dois verbos, `migrar` e `expurgo`, sendo o expurgo por **manifesto revisável**, com
simulação obrigatória.

**24 de 24 ações concluídas** (`actions.md`), **0 falhas**. Paridade diferencial em **100 %** antes e
depois, com o `harness.py` byte a byte idêntico. Suíte: `302 passed, 8 skipped` antes e **`327 passed,
9 skipped`** depois.

**Nenhuma regra de domínio foi modificada.** O `git diff` está vazio em `src/` e em `_reversa_sdd/`.

## Impacto por artefato da extração

| Artefato | Seção | Tipo de impacto | Delta |
|----------|-------|-----------------|-------|
| `_reversa_sdd/architecture.md` | §1 Visão Geral da Arquitetura | delta-de-dados | O "sistema de arquivos local (`src/uploads/`)" continua sendo o único estado persistente, mas a **raiz declarada** passa a ser a pasta canônica fora do repositório |
| `_reversa_sdd/architecture.md` | §7 Dívidas Técnicas Consolidadas | regra-alterada | A dívida 3 segue de pé; o que muda é que o motivo remanescente da guarda de instância única é a pasta compartilhada — que continua sendo **uma só**, agora a canônica |
| `_reversa_sdd/inventory.md` | §4 Pontos de Entrada e Configurações | regra-alterada | `ANALISADOR_UPLOAD_FOLDER` deixa de ser "usada pelos testes para não escrever na pasta real" e passa a ser o **modo de operação declarado** do operador, com destino canônico |
| `_reversa_sdd/inventory.md` | §5 Banco de Dados e Armazenamento | delta-de-dados | A localização do armazenamento muda; o mecanismo — arquivos imutáveis sob chave derivada do conteúdo — não muda |
| `_reversa_sdd/upload-gedcom/contracts.md` | §2.2 Pasta | regra-alterada | O **padrão do código** permanece `<diretório do app>/uploads`; o que passa a apontar para fora do repositório é o uso declarado, e é a documentação que o sustenta |
| `_reversa_sdd/upload-gedcom/design.md` | Estado Interno | delta-de-dados | A linha "Arquivo enviado: `src/uploads/`" deve ser lida como "pasta canônica de dados"; a imutabilidade e a ausência de remoção pelo sistema continuam |
| `_reversa_sdd/state-machines.md` | §5 Estados Deliberadamente NÃO Gerados | regra-alterada | O arquivo enviado continua sem ciclo de vida e o runtime continua sem apagar nada; passa a existir, **fora do runtime**, um expurgo por manifesto com simulação |
| `_reversa_sdd/c4-containers.md` | Container 3 — sistema de arquivos local | delta-de-dados | O ponto de montagem da composição deixou de ser a pasta do repositório e passou a ser a pasta canônica do host, no mesmo alvo interno |
| `_reversa_sdd/data-dictionary.md` | Caminho padrão e tabela de variáveis de ambiente | delta-de-dados | O caminho padrão continua o do código, e a variável passa a ter destino canônico declarado; nenhum nome de campo ou de arquivo muda |
| `_reversa_sdd/erd-complete.md` | `ARQUIVO_ARMAZENADO` | delta-de-dados | A coluna de localização passa a apontar para a raiz canônica; a chave de conteúdo e a forma do nome permanecem idênticas, e o histórico do banco segue resolvível |
| `_reversa_sdd/user-stories/upload-gedcom.md` | O que esta história não cobre | regra-alterada | A limitação "nada é registrado e o arquivo nunca é apagado pelo sistema" ganha a ressalva de que existe expurgo por manifesto, acionado pelo operador |
| `_reversa_sdd/addenda/008-persistencia-postgres-docker.md` | O que a extração não precisa mudar | delta-de-contrato-externo | O leiaute em disco segue intacto e nenhum arquivo foi renomeado — o 008 continua correto nisso; o que este adendo complementa é que o *bind mount* deixou de ser `./src/uploads` |
| `README.md` (fora da extração, citado por completude) | Configuração de execução e Testes | delta-de-contrato-externo | A tabela passa a listar a variável da pasta e o caminho de execução da paridade passa a ser o invólucro `tests/rodar_paridade.py` |

## Regras sob vigilância

`W001`, `W002`, `W003`, `W004`, `W005`, `W006`, `W007`, `W008` —
detalhe em `_reversa_forward/010-uploads-fora-do-repositorio/regression-watch.md`.

## Fontes

- `_reversa_forward/010-uploads-fora-do-repositorio/requirements.md`
- `_reversa_forward/010-uploads-fora-do-repositorio/roadmap.md` (decisões `D-01` a `D-08`)
- `_reversa_forward/010-uploads-fora-do-repositorio/legacy-impact.md`
- `_reversa_forward/010-uploads-fora-do-repositorio/regression-watch.md`
- `_reversa_forward/010-uploads-fora-do-repositorio/progress.jsonl`
- `_reversa_forward/010-uploads-fora-do-repositorio/evidence/` (14 arquivos de medição)

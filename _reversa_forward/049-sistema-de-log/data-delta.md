# Delta de dados: sistema de log completo

> Identificador: `049-sistema-de-log`
> Data: `2026-10-25`
> Base: `_reversa_sdd/erd-complete.md` (42 estruturas) e `_reversa_sdd/architecture.md#4`

## 1. Resumo

**Nenhuma tabela, nenhuma coluna, nenhuma migração.** A persistência PostgreSQL não é tocada, e a
tabela `access_audit` do sistema alvo **não** é criada aqui — a razão está em `investigation.md` §7.

O que muda é o **modelo em memória e em disco**: entram três estruturas de processo (contexto de
requisição, linha de auditoria e destinos configurados), uma estrutura existente ganha um campo
(`ResultadoDeUpload.desfecho`) e nasce uma pasta com arquivos datados.

## 2. Estrutura alterada

### `ResultadoDeUpload` — campo novo

| Campo | Tipo | Valores | Origem do valor |
|---|---|---|---|
| `desfecho` | `str` | `novo` \| `identico` \| `substituido` | `armazenado.desfecho`, vindo de `application/reenvio.py:38-40` |

- **Por que precisa existir:** a borda audita o envio e precisa distinguir os três desfechos da
  `RN-17`. Hoje o `ResultadoDeUpload` (`application/upload_gedcom.py:45-58`) expõe `referencia`,
  `nome_exibido`, `nomes` e `mensagem` — o desfecho já é calculado dentro do caso de uso e descartado.
- **Por que não inferir na borda:** reconhecer o caso pelo texto de `mensagem` daria autoridade
  semântica ao literal de tela, que é exatamente o que a `RF-20` proíbe (é a mesma razão pela qual
  `Desfecho` existe em `application/path_search.py`).
- **Compatibilidade:** `dataclass(frozen=True)`; o campo entra **sem default** e com três chamadores
  no máximo (o caso de uso e os testes que constroem o resultado). Nenhum consumidor de template lê
  esse campo.

## 3. Estruturas novas em memória

| Estrutura | Onde vive | Vida | Conteúdo |
|---|---|---|---|
| `CONTEXTO_DE_REQUISICAO` | `utils/logs.py` (um `ContextVar`) | a requisição; nasce no `before_request` e morre no fim dela | o identificador curto da requisição |
| `LINHA_DE_AUDITORIA` | `utils/auditoria.py` (registro tipado, montado e descartado) | o instante da emissão | os nove campos da §4 abaixo |
| `DESTINOS` | `utils/logs.py` (estado de processo, montado uma vez) | o processo inteiro | os handlers configurados, os caminhos resolvidos e o nível por módulo |

> Estas três estruturas **não** são cache nem estado de domínio: nenhuma delas sobrevive a uma
> decisão de negócio, e nenhuma é lida pelo núcleo. O `ADR-24` continua valendo — a árvore segue
> sendo valor de passagem.

## 4. Os campos da linha de auditoria

| Campo | Exemplo | Regra |
|---|---|---|
| data e hora | `2026-10-25 15:06:29` | locais, com segundos |
| ação | `aposentar` \| `enviar_gedcom` \| `substituir_csv` \| `analisar_dna` \| `buscar_caminho` | valor de um conjunto fechado, nunca texto livre |
| desfecho | `sucesso` \| `falha` \| `novo` \| `identico` \| `substituido` \| `resultado` \| `sem_resultado` \| `erro_de_entrada` | derivado do tipo já existente (`Desfecho`, `reenvio`) |
| chave | `94e2402671702cac` | os 16 hexadecimais, via `decompor_nome_armazenado` (`utils/validate.py:152`) |
| extensão | `.ged` \| `.csv` | de `os.path.splitext` sobre o nome visível, **nunca** o nome |
| contagens | `resultados=12 descartados=3` | só números; nenhum rótulo, nenhum xref, nenhum nome |
| IP | `127.0.0.1` | `request.remote_addr`, decisão de 2026-10-25 |
| identificador da requisição | `a3f19c2e` | o mesmo valor do cabeçalho `X-Request-ID` |
| origem | `POST /` | método e rota |

**O que nunca entra:** rótulo visível do arquivo, nome de pessoa, `xref`, e-mail, identificador de
kit, caminho completo, conteúdo do arquivo, resultado da análise.

## 5. Delta em disco

| Caminho | Tipo | Versionado? | Observação |
|---|---|---|---|
| `logs/analisador.log` (+ `.1`…`.4`) | arquivo rotativo, 5 × 5 MB | **não** | diagnóstico |
| `logs/analisador.auditoria.AAAA-MM-DD.log` | arquivo novo por dia, sem descarte | **não** | trilha de auditoria; o prazo de 90 dias é do operador (`RN-10`) |
| `logs/` | diretório | **não** | criado no arranque, como a pasta de upload |
| `.gitignore` | arquivo de controle | sim | ganha a linha da pasta — executada em 2026-10-26 (T022) |
| `.dockerignore` | arquivo de controle | sim | **não muda**: já é lista de permissão (`*` exclui `logs/`) |
| `docker-compose.yml` | arquivo de operação | sim | ganha o volume `./logs` e a rotação do orquestrador |

## 6. Impacto no inventário da extração

| Artefato | O que passa a ser verdade |
|---|---|
| `_reversa_sdd/erd-complete.md#7` | O inventário de 42 estruturas passa a **45**: entram `CONTEXTO_DE_REQUISICAO`, `LINHA_DE_AUDITORIA` e `DESTINOS` |
| `_reversa_sdd/architecture.md#4` | A linha "memória, de módulo" sobe de **1** (cache de árvores) para **2** (`DESTINOS`); as outras duas são de requisição/instante |
| `_reversa_sdd/architecture.md#2` | O container "aplicação web" deixa de ser "sem estado observável": ele mantém a configuração de log enquanto vive |
| `_reversa_sdd/data-dictionary.md` | Ganha as três estruturas e o campo `desfecho` de `ResultadoDeUpload` |

## 7. Migração

**Não há migração de dado.** Nada do que existe é reescrito, renomeado ou convertido.

1. Instalação nova: a pasta de log nasce no arranque, como já acontece com `src/uploads/`.
2. Instalação existente: os arquivos de log anteriores simplesmente não existem — a feature começa a
   registrar a partir da primeira requisição depois de subir.
3. Container: sem o volume `./logs`, a trilha de auditoria cai para o fluxo padrão e a degradação é
   avisada uma vez (`D-11` do `roadmap.md`).
4. **A linha da pasta de log no `.gitignore` foi executada em 2026-10-26 (T022)**, depois de o
   operador liberar `.gitignore` no `allowedPaths` de `.reversa/reversa-config.json`. Sem ela, a
   feature já funcionava; a linha existe para o log de operação não ser versionado por acidente.

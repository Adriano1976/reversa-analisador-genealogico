# Impacto no legado: sistema de log completo

> Identificador: `049-sistema-de-log`
> Data: `2026-10-25` (atualizado em `2026-10-26`, com a T022)
> **Política de edição do legado no momento da execução:** `allowLegacyEdits: true`, com
> `allowedPaths` liberando `src/**`, `tests/**`, `docker/**`, `docker-compose.yml`,
> `.dockerignore`, `requirements.txt`, `docs/**`, `.github/**`, `init.sql`, `*.ps1`,
> `analisador-genealogico/**`, `publicar_docs.py`, `pyrefly.toml`, `.vscode/**`,
> `.markdownlint-cli2.jsonc`, `_docs_auxiliary/**` e `.gitignore` (liberado em 2026-10-26).
> **Recusado pela política:** nenhum.

## 1. Arquivos afetados

| Arquivo afetado | Componente | Tipo | Severidade | Justificativa |
|---|---|---|---|---|
| `src/utils/logs.py` | `utils/` (folha transversal) | `componente-novo` | LOW | Configuração dos três destinos, contexto de requisição, máscara de privacidade e medição. Nenhum módulo existente passa a depender dele além de `ports/adaptadores.py` e da borda |
| `src/utils/auditoria.py` | `utils/` | `componente-novo` | LOW | Linha de auditoria tipada; usa a autoridade já existente `decompor_nome_armazenado` em vez de reimplementar a separação chave/rótulo |
| `src/web/hooks_de_registro.py` | borda HTTP (`web/`) | `componente-novo` | MEDIUM | Passa a emitir `X-Request-ID` em **toda** resposta e uma linha de acesso por requisição |
| `src/app.py` | borda HTTP | `delta-de-contrato-externo` | **HIGH** | Três mensagens de erro de tela trocam o texto interno da exceção pela frase fixa (`RN-06`). É o único contrato percebido pelo operador que muda |
| `src/app.py` | borda HTTP | `regra-nova` | MEDIUM | Auditoria nos cinco fluxos (envio, substituição de CSV, aposentar ×2, análise, busca) — fecha a decisão 14 do `gaps.md` |
| `src/app.py` | borda HTTP | `regra-alterada` | LOW | `print` de inicialização virou linha `INFO`; o texto é o mesmo |
| `src/ports/adaptadores.py` | `ports/` | `regra-nova` | LOW | `CarregadorDeArvoresGedcom.carregar` mede o parse com `medir("carregar_arvore")`. Nenhuma regra de leitura muda |
| `src/application/upload_gedcom.py` | `application/` | `delta-de-dados` | LOW | `ResultadoDeUpload` ganha `desfecho` (valores de `reenvio.py`); nenhum consumidor de template lê o campo |
| `docker-compose.yml` | operação | `regra-alterada` | LOW | Volume `./logs` e rotação `json-file` 5 × 5 MB no serviço da aplicação |
| `tests/conftest.py` | instrumentação de teste | `regra-alterada` | LOW | Isola `ANALISADOR_LOG_DIR` no import do conftest e insere `src/` no `sys.path` uma vez |
| `tests/rodar_paridade.py` | instrumentação de teste | `regra-alterada` | LOW | Passa `ANALISADOR_LOG_DIR` ao coletor, pelo mesmo mecanismo que já isolava a pasta de upload. O instrumento congelado (`_reversa_sdd/parity/harness.py`) **não** foi tocado |
| `.gitignore` | operação | `regra-nova` | LOW | A pasta `logs/` deixa de ser rastreada pelo Git; nenhum comportamento de runtime muda |

## 2. Diff conceitual por componente

**`utils/`** deixou de ser só validação, formatação e limpeza: ganhou a autoridade única sobre
registro. A escolha do pacote não é estética — `utils/` é o único pacote folha real do projeto, e
uma configuração de log em `core/` violaria a direção de dependência que o `ADR-34` fechou.

**A borda (`app.py`)** passou a ser o ponto de auditoria. O núcleo e os casos de uso **não
souberam** de nada: nenhuma assinatura de porta mudou, e `dono` continua sem comportamento. A
única mudança de contrato de dados é o campo `desfecho` em `ResultadoDeUpload`, e existe
justamente para a borda não precisar inferir o caso pelo texto da mensagem (`RF-20`).

**`ports/adaptadores.py`** não ganhou regra: ganhou um medidor em volta do ponto que já existia.
O `medir` é um `with` curto, e o cache da feature 047 continua sendo o que intercepta o parse.

**A operação** mudou de lugar, não de natureza: os logs saem para `logs/` na raiz (fora do
versionamento, com a linha do `.gitignore` que a T022 acrescentou) e, no container, para o fluxo
padrão com rotação do orquestrador, com a trilha de auditoria em volume.

## 3. Regras preservadas (🟢 do `domain.md`)

| Regra | Como continua verdadeira |
|---|---|
| `RN-14` — aposentar move e nunca apaga | O adaptador não foi tocado; a auditoria só observa o retorno |
| `RN-07` — a aplicação nunca apaga arquivo enviado | Nenhum `os.remove`, `os.unlink` ou `rmtree` entrou em `src/` |
| `RN-18` — a mensagem de recusa de GEDCOM é fixa | `utils/validate.py` e `application/upload_gedcom.py` mantêm o literal |
| `RN-13` — a persistência nunca bloqueia o resultado | A auditoria não toca no banco; `RegistroDeAnalisesPostgres` intacto |
| Contrato de mensagens de domínio (`traducao.py`) | 29 literais: os de **erro previsto** continuam idênticos, com par (mensagem, status) fixado por `test_traducao_de_erros.py` |
| Paridade 100 % das fixtures | A mudança de mensagem preserva os prefixos que o `modo()` do harness usa para classificar o desfecho (`harness.py:185`) |
| `RF-20` — literal de tela sem autoridade semântica | O desfecho viaja como campo, não como texto |

## 4. Regras modificadas (🟢 que deixaram de valer como estavam)

| Regra | O que mudou |
|---|---|
| RNF "Observabilidade" das 5 units — "nenhum log, métrica ou trace" | Deixa de ser verdade: há três destinos, identificador, linha de acesso e trilha de auditoria. A convergência nos artefatos é do `/reversa-sync` |
| Lacuna 5 da `tela-de-entrada` — "nenhuma tentativa de aposentar deixa rastro" | Fechada: as duas tentativas deixam linha com desfecho distinto |
| Decisão 14 do `gaps.md` — "Agendado" | Executada |
| As três mensagens do `except Exception` em `src/app.py` | `{e}` saiu; entrou "O detalhe foi registrado no log.", com o prefixo preservado |
| "O projeto inteiro tem **um** log" (`questions.md` #14, contexto) | Passa a ter nove chamadas + três destinos + auditoria |
| Linha de acesso do `waitress` como única observabilidade do acesso | Substituída pela linha própria, que carrega o identificador; a do servidor subiu para `WARNING` |

## 5. O que **não** foi tocado

`core/`, `parsers/`, `reporting/`, `application/traducao.py`, `application/reenvio.py`,
`application/dna_analysis.py`, `application/path_search.py`, `web/rotas_assets.py`,
`src/templates/index.html`, `init.sql`, `requirements.txt`, `docker/Dockerfile`,
`.dockerignore` e todo o `_reversa_sdd/` (exceto o ADR-37, que é artefato novo).

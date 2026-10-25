# Adendo: o sistema passou a ter observabilidade em camadas

> Identificador: `049-sistema-de-log`
> Data: `2026-10-25`
> Cenário: **legado** (âncora em `_reversa_sdd/architecture.md` e `_reversa_sdd/domain.md`)

## Vigência

Vigente desde 2026-10-25.

## Resumo da entrega

A extração registrava, nas cinco units, a mesma frase: **"nenhum log, métrica ou trace"**. O que
existia, medido na abertura da feature: nove chamadas de registro espalhadas em `src/app.py` e
`src/ports/adaptadores.py`, um `print` de inicialização e **nenhuma** configuração — sem
`basicConfig`, sem `dictConfig`, sem `setLevel`. Tudo abaixo de `WARNING` se perdia, não havia
arquivo, não havia identidade de requisição e a única ação capaz de mover arquivo do operador
(aposentar) não deixava rastro nenhum.

A entrega fecha a decisão **14** do `gaps.md` e a lacuna 5 da `tela-de-entrada` com um sistema de
registro em **três destinos de papéis distintos** — console (operação), arquivo geral rotativo
(diagnóstico) e trilha de auditoria em arquivo por dia (prova, sem descarte por tamanho) —, mais
identificador por requisição em `contextvars` devolvido no cabeçalho `X-Request-ID`, linha de
acesso por requisição, máscara de privacidade aplicada **também ao traceback**, medição nomeada do
parse e a operação correspondente (stdout no container, volume `./logs`, rotação `json-file`).

**23 de 24 ações concluídas.** Suíte: **1684 passam / 9 pulados / 0 falham**. A ação aberta é a
`T022` (linha da pasta de log no `.gitignore`), recusada pela política de edição do legado — o
caminho não está no `allowedPaths` de `.reversa/reversa-config.json`. Enquanto ela não fechar,
rodar a aplicação no repositório cria `logs/` não versionado; o `.dockerignore` já a exclui do
contexto de build por ser lista de permissão.

**Nota de privacidade.** A trilha passou a acumular **IP e chave de conteúdo** com prazo declarado
de 90 dias e **sem mecanismo que o faça cumprir** (`RN-10`, expurgo manual). É acúmulo novo de dado
pessoal, registrado como lacuna 🟡 no `requirements.md` §10 e em `regression-watch.md`.

## Impacto por artefato da extração

| Artefato | Seção | Tipo de impacto | Delta |
|---|---|---|---|
| `_reversa_sdd/architecture.md` | §3 (componentes e estrutura de pacotes) | `componente-novo` | `utils/logs.py`, `utils/auditoria.py` e `web/hooks_de_registro.py` entram; `utils/` deixa de ser só validação, formatação e limpeza, e passa a ser também a autoridade única sobre registro |
| `_reversa_sdd/architecture.md` | §4 (onde o dado vive) | `delta-de-dados` | Entram três estruturas **em memória**: o contexto de requisição (um `ContextVar`), a linha de auditoria e a configuração dos destinos |
| `_reversa_sdd/architecture.md` | §2 (containers/concorrência) | `delta-de-contrato-externo` | O container da aplicação passa a escrever no fluxo padrão (com rotação) e na pasta `logs/`, publicada como volume |
| `_reversa_sdd/domain.md` | §5 (contrato de mensagens ao usuário) | `delta-de-contrato-externo` | As **três** mensagens do `except Exception` genérico perdem o texto interno da exceção e terminam em "O detalhe foi registrado no log."; os prefixos foram preservados de propósito, e o `modo()` do harness de paridade continua classificando o desfecho |
| `_reversa_sdd/domain.md` | §3.6 (tela de entrada: listar, escolher e aposentar) | `regra-nova` | As **duas** tentativas de aposentar deixam linha de auditoria, com desfecho distinto — a decisão 14 executada |
| `_reversa_sdd/domain.md` | §7 (lacunas) | `regra-removida` | A ausência de observabilidade deixa de ser lacuna; entra a retenção declarada e não mecanizada como lacuna nova |
| `_reversa_sdd/tela-de-entrada/requirements.md` | RNF Observabilidade | `regra-removida` | "Nenhuma métrica, nenhum log de listagem ou de aposentadoria" deixa de valer |
| `_reversa_sdd/upload-gedcom/requirements.md` · `analise-dna/requirements.md` · `busca-caminho/requirements.md` · `recursos-da-tela/requirements.md` | RNF Observabilidade | `regra-removida` | "Nenhum log, métrica ou trace" deixa de valer nas quatro units: envio, análise e busca passam a auditar com contagens, e a carga da árvore é medida |
| `_reversa_sdd/erd-complete.md` | §7 (inventário das 42 estruturas) | `delta-de-dados` | Vai a **45**: entram `CONTEXTO_DE_REQUISICAO`, `LINHA_DE_AUDITORIA` e `DESTINOS` |
| `_reversa_sdd/data-dictionary.md` | estruturas em memória e `ResultadoDeUpload` | `delta-de-dados` | Três estruturas novas; o resultado do envio ganha `desfecho` (`novo` / `identico` / `substituido`), que já era calculado e era descartado |
| `_reversa_sdd/c4-containers.md` | containers | `delta-de-contrato-externo` | O container da aplicação ganha dois destinos de registro e um volume de auditoria |
| `_reversa_sdd/gaps.md` | §5 (decisões tomadas) | `regra-alterada` | A decisão 14, "logar as duas tentativas", passa de **Agendado** a executada |
| `_reversa_sdd/adrs/` | acervo de decisões | `componente-novo` | Entra o `ADR-37 — observabilidade em camadas, sem ferramenta externa`, com as alternativas descartadas |

## Regras sob vigilância

`W001`, `W002`, `W003`, `W004`, `W005`, `W006`, `W007`, `W008`, `W009` — em
`_reversa_forward/049-sistema-de-log/regression-watch.md`.

## Fontes

- `_reversa_forward/049-sistema-de-log/requirements.md`
- `_reversa_forward/049-sistema-de-log/roadmap.md`
- `_reversa_forward/049-sistema-de-log/legacy-impact.md`
- `_reversa_forward/049-sistema-de-log/regression-watch.md`
- `_reversa_forward/049-sistema-de-log/progress.jsonl`
- `_reversa_forward/049-sistema-de-log/actions.md`
- `_reversa_sdd/adrs/37-observabilidade-em-camadas.md`

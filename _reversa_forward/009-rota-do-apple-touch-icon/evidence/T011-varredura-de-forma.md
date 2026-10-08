# T011 — Varredura de forma

> Feature: `009-rota-do-apple-touch-icon` · Ação: `T011` · Data: `2026-10-08`

## O que esta varredura procura

Três coisas que passariam nos testes de comportamento e ainda assim estariam erradas:
superfície sem consumidor, pasta proibida reaberta, e arte fora do contexto de build.

| Verificação | Requisito | Medido | Veredito |
|---|---|---|---|
| `src/static` existe | `RN-07`, `W004` | **`False`** | ✅ ausente |
| `src/assets/apple-touch-icon.png` existe | `RF-04` | **`True`** | ✅ presente |
| Rotas declaradas em `src/app.py` | `RF-11`, `RN-09` | **2** (era 1) | ✅ só a nova |
| O template menciona o ícone de atalho | `RN-02` | **0 ocorrências** | ✅ não declara |

## As duas rotas

```
217 : @app.route("/apple-touch-icon.png", methods=["GET"])
239 : @app.route("/", methods=["GET", "POST"])
```

A rota nova é `GET` **apenas**. Isso não é detalhe de estilo: é o que faz a recusa de
escrita sair do roteador com `405`, sem uma linha de validação nossa que pudesse divergir
da convenção (`D-07`).

## O contexto de build permite a arte

`.dockerignore` na raiz, as três linhas que importam:

```
!src/
!src/**
src/uploads/
```

A arte está sob `src/`, então entra por `!src/**`. E a reexclusão de `src/uploads/` continua
**depois** dela, que é a ordem que importa: a última regra que casa vence, e é ela que
impede o GEDCOM real do operador de viajar para o daemon do Docker (`Princípio I`).

## Nenhuma superfície sem consumidor foi criada

A `RN-09` existe porque a tentação aqui é "simetria": servir também o alias legado
`/apple-touch-icon-precomposed.png` (que pertence a sistemas anteriores) e o `/favicon.ico`
(que o navegador só busca quando o documento **não** declara ícone — e o template declara).

Os dois continuam **sem resposta**, e isso está preso por teste
(`test_os_caminhos_nao_servidos_continuam_sem_resposta`) e confirmado no ar:
`GET /favicon.ico -> 404`.

Criar qualquer um dos dois repetiria a **dívida #17** — *"superfícies de compatibilidade
reexportando nomes históricos que ninguém usa"* —, que este projeto já fechou uma vez.

## Veredito

**APROVADO.** Nenhuma pasta proibida reaberta, nenhum caminho sem consumidor, e a arte no
único lugar que entra na imagem.

## Fontes

- `.dockerignore` na raiz · `src/app.py` · `src/templates/index.html`
- `evidence/_t008_t009_conteiner.txt` (o `404` do `favicon.ico`, medido no ar)
- `_reversa_sdd/architecture.md#7` (dívida #17, fechada)
- `_reversa_forward/003-renomear-pasta-app-para-src/regression-watch.md#W004`

# Delta de dados — feature 054

> Identificador: `054-embutir-bootstrap-e-mermaid`
> Data: `2026-10-31`
> Modelo extraído: `_reversa_sdd/erd-complete.md`, `_reversa_sdd/data-dictionary.md`

## 1. Veredito

**Nenhuma mudança em entidade, campo, tabela, índice, constraint ou migração.** A feature não toca o modelo de
dados do sistema: não há persistência de recurso de apresentação, não há linha nova no Postgres e não há alteração
no documento de contas (`src/dados/contas.json`).

O que existe é um **inventário novo de arquivos versionados** e quatro chaves novas de configuração em memória.
Os dois são registrados aqui porque o `/reversa-coding` e o `/reversa-sync` precisam saber exatamente o que entra
no repositório, com qual procedência e como se regenera.

## 2. Inventário de arquivos novos

| Caminho | Bytes | Origem | Regeneração |
|---------|------:|--------|-------------|
| `src/assets/bootstrap.min.css` | 232.803 | jsDelivr, Bootstrap 5.3.3 | baixar de novo e conferir `sha256` |
| `src/assets/bootstrap.bundle.min.js` | 80.721 | jsDelivr, Bootstrap 5.3.3 | idem |
| `src/assets/mermaid.min.js` | 3.337.857 | jsDelivr, Mermaid 10.9.8 | idem |
| `src/assets/fontes.css` | ~17 KB | CSS do Google Fonts, com as URLs reescritas | receita `tests/fontes_da_tela.py` |
| `src/assets/fontes/*.woff2` | 201.468 (11) | `fonts.gstatic.com` | idem |

Total: **3.852.849 bytes** (~3,67 MiB), medido em 2026-10-31.

Nenhum desses arquivos contém dado de genealogia, de DNA ou de pessoa: são biblioteca de terceiro e desenho
tipográfico. O Princípio I não é afetado.

## 3. Chaves de configuração novas

No molde de `ESTILO_DA_TELA` (`src/app.py:424`), publicadas em `create_app` (`src/app.py:1006`):

| Chave | Constante | Aponta para |
|-------|-----------|-------------|
| `BIBLIOTECA_CSS` | `BIBLIOTECA_CSS` | `src/assets/bootstrap.min.css` |
| `BIBLIOTECA_JS` | `BIBLIOTECA_JS` | `src/assets/bootstrap.bundle.min.js` |
| `MERMAID` | `MERMAID` | `src/assets/mermaid.min.js` |
| `FOLHA_DE_FONTES` | `FOLHA_DE_FONTES` | `src/assets/fontes.css` |
| `PASTA_DE_FONTES` | `PASTA_DE_FONTES` | `src/assets/fontes/` |

São caminho de arquivo, não dado: não entram no `data-dictionary.md` como entidade, e o teste que simula arquivo
ausente continua usando `monkeypatch.setitem(app.config, ...)`.

## 4. Contrato de leitura dos `woff2`

O nome do arquivo chega pelo caminho da URL e é validado contra **um conjunto fechado**, montado a partir de uma
constante com os 11 nomes gerados pela receita (`D-04`). Regras:

1. Nome fora do conjunto → `404`, sem revelar se o arquivo existe.
2. Nome com separador de caminho, `..` ou NUL → `404` pelo mesmo caminho (não é um segundo teste).
3. Arquivo do conjunto ausente no disco → `404`, como nas artes.
4. Nenhum `listdir` por requisição: o conjunto é resolvido uma vez a partir da constante.

## 5. O que **não** muda

- `_reversa_sdd/erd-complete.md`: os 5 diagramas e as 42 estruturas continuam válidos.
- `_reversa_sdd/data-dictionary.md`: nenhum campo, tipo ou origem de dado novo.
- O esquema do Postgres (`init.sql`): intocado; nenhuma migração.
- `src/dados/contas.json` e o volume do compose: intocados.
- `src/uploads/`: intocado.

## 6. Migração

Não há. A troca é de proveniência, e o plano de migração está na seção 8 do `roadmap.md`. A única "conversão" é a
geração de `fontes.css` e dos `woff2` pela receita, que é idempotente: rodar de novo com a mesma versão do Google
produz os mesmos bytes, e o teste falha se o `sha256` divergir.

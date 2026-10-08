# Legacy Impact — feature `009-rota-do-apple-touch-icon`

> Feature: `009-rota-do-apple-touch-icon`
> Data: `2026-10-08`
> Cenário: **legado** (âncora em `_reversa_sdd/architecture.md` + `_reversa_sdd/domain.md`)
> Executor: `/reversa-coding`

## 1. Arquivos afetados

| Arquivo afetado | Componente | Tipo | Severidade | Justificativa |
|---|---|---|---|---|
| `src/app.py` | Camada de rota (`_reversa_sdd/c4-components.md`) | `contrato-alterado` | **HIGH** | A camada de rota passa de **uma** para **duas** rotas. O contrato HTTP documentado em `_reversa_sdd/upload-gedcom/contracts.md#1` ganha a **quarta linha**. Medido: **47 inserções, 1 remoção** — e a remoção é a linha de import reescrita para trazer `send_file`. **Nenhuma linha de `index()` foi tocada** |
| `src/assets/apple-touch-icon.png` | Inventário de pacotes (`_reversa_sdd/architecture.md#3`) | `componente-novo` | LOW | `src/assets/` não existe no inventário. Recebe **um** binário: a arte derivada, 180×180, opaca, 16.504 bytes. Não é dado de domínio nem entidade do modelo |
| `tests/icone_de_atalho.py` | Instrumento de desenvolvimento | `componente-novo` | LOW | A receita de derivação (`D-02`) como **fonte única**. É o que o teste de deriva importa para regenerar e comparar |
| `tests/test_icone_de_atalho.py` | Instrumento de verificação | `componente-novo` | LOW | 15 testes do contrato: status, tipo, dimensão, opacidade, tamanho, tela imutável, método, cache, caminhos não servidos e ausência da arte |
| `tests/test_deriva_da_arte.py` | Instrumento de verificação | `componente-novo` | LOW | 5 testes: deriva, **sensibilidade** da comparação, o caso de recompressão que não pode falhar, localização da arte e a separação de dependência de teste |

**Nenhum arquivo é removido e nenhum componente se extingue.**

## 2. Diff conceitual por componente

### 2.1 Camada de rota

Antes: uma única rota (`GET`/`POST /`) que adapta o HTTP, chama o caso de uso e traduz a
exceção de domínio. Depois: a mesma rota, **sem uma linha alterada**, e uma segunda ao lado
— `GET /apple-touch-icon.png` — que devolve um arquivo fixo do próprio projeto.

A rota nova **não tem caso de uso, não tem porta e não tem entrada**. Servir um arquivo de
propriedade do projeto é adaptação de entrada pura (`D-01`); criar um caso de uso para ela
seria cerimônia sem consumidor, e o `roadmap.md` §3 registra a alternativa descartada.

O contrato HTTP passa de três para quatro linhas, e as três antigas continuam **idênticas**.
A frase do contrato — *"Não há contrato JSON, redirect, `201`, `400` ou `409`"* — continua
**verdadeira**: a linha nova devolve imagem, e não payload nem redirecionamento.

### 2.2 Arte do produto

A arte **servida** não é a arte **canônica**, e a diferença é medida, não estética: a
canônica é tipo de cor **6** (com canal alfa, 32,5 % de pixels transparentes) e a derivada é
tipo de cor **2** (sem canal alfa). O sistema móvel compõe transparência sobre **preto** no
ícone de atalho, então servir a canônica produziria um quadrado preto com o desenho por cima
(`RN-04`).

A canônica **não sai de `docs/`**: o mini-site publicado consome o mesmo arquivo, e as duas
cópias servem a dois alvos de publicação distintos. O que a entrega acrescenta é a
**detecção de deriva** entre elas (`RN-05`, `RF-10`).

### 2.3 Instrumentos de verificação

Dois arquivos de teste e um módulo de receita. O módulo existe para que a receita tenha
**fonte única**: o teste de deriva regenera a partir da canônica com a mesma função que
produziu o arquivo commitado, e compara **pixel a pixel** — nunca bytes, porque o mesmo
desenho foi medido com 32.317 e 44.069 bytes e diferença de pixel **zero** (`D-08`).

## 3. Delta de contrato externo

| Contrato | Antes | Depois |
|---|---|---|
| HTTP — `_reversa_sdd/upload-gedcom/contracts.md#1` | **3 linhas** (`GET /`, `POST /` upload, `POST /` 413) | **4 linhas**, com `GET /apple-touch-icon.png` → `200` imagem. Documentado em `interfaces/apple-touch-icon.md` |

## 4. Delta de dados

**Nenhum.** Nenhuma das 27 estruturas de `_reversa_sdd/erd-complete.md` é criada, alterada ou
removida; nenhum campo, índice ou migração. Ver `data-delta.md`.

## 5. Preservadas

Regras 🟢 que continuam **intactas**, e o instrumento que o demonstra:

| Regra preservada | Origem | Prova |
|---|---|---|
| As **dez mensagens** da camada de rota, literais e caso a caso | `_reversa_sdd/domain.md#5.1` | Template intocado (`git diff --stat -- src/templates` vazio) |
| "Não achei" é sucesso; pessoa não encontrada é erro | `_reversa_sdd/domain.md#5.1` | `index()` sem uma linha alterada |
| Nenhum limiar, peso ou ordem do matching | `_reversa_sdd/domain.md#2`, `#3.1`–`#3.4`, `#3.7` | `git diff` vazio em `src/core/` — paridade **100 %**, exit 0 |
| A forma dos dados do núcleo (`Tree` de quatro elementos; tupla de três na saída) | `W016` (006) | `git diff` vazio em `src/core/` |
| Contrato de armazenamento: chave por conteúdo, `<chave>__<nome>`, teto de 16 MB | `_reversa_sdd/domain.md#3.5` | Nenhum arquivo de armazenamento tocado |
| O contrato de segurança da forma fechada `^[0-9a-f]{16}__[A-Za-z0-9._-]+$` | `_reversa_sdd/upload-gedcom/contracts.md#2.1` | Não tocado |
| As três primeiras linhas do contrato HTTP | `_reversa_sdd/upload-gedcom/contracts.md#1` | `GET /` em **23.906 bytes**, o mesmo `sha256` de antes |
| `src/static/` ausente | `W004` (003) | Ausente no host **e** dentro da imagem |
| O dono não entra na chave nem no caminho | `W020` (007) | Nenhum arquivo de armazenamento tocado |
| Nada persistido é lido para decidir a tela | `RN-12` (008) | Nenhum arquivo de persistência tocado |

## 6. Modificadas

| Regra 🟢 modificada | Origem | Como mudou | Watch |
|---|---|---|---|
| O contrato HTTP tem **três** linhas, e nenhuma delas devolve imagem | `_reversa_sdd/upload-gedcom/contracts.md#1` | Passa a ter **quatro**. A afirmação sobre não haver JSON, redirect, `201`, `400` ou `409` **continua verdadeira** | `W026` |

**É a única regra 🟢 modificada.** Nenhuma regra foi **removida**, então não há item do tipo
`ausência` derivado de remoção. Os `W027` a `W030` do `regression-watch.md` vigiam
propriedades que esta entrega **estabelece** e que uma leitura futura pode quebrar sem
perceber — e estão declarados como tal, não como regras herdadas alteradas.

## 7. Declaração de limite

1. **Nada foi testado em aparelho real.** A conclusão sobre composição de transparência,
   máscara de canto e cache agressivo vem de documentação e relato de terceiros
   (`investigation.md` §6.1). O que foi medido é a arte e o comportamento das rotas.
2. **A paridade em 100 % não é conquista desta entrega** — é a ausência dela no núcleo,
   provada por `diff` vazio e medida por não ser presumível.
3. **A `RN-05` do `requirements.md` diz "cópia"** onde a decisão técnica estabelece
   **renderização derivada**. A imprecisão está declarada no `roadmap.md` §3 e **não** foi
   corrigida por este skill, que não escreve no `requirements.md`.
4. **A biblioteca de imagem usada pelos testes não está em `requirements.txt`**, que é a
   lista de runtime (`D-09`). Quem montar ambiente de teste do zero precisa dela.

## Fontes

- `git diff` e `git diff --stat` executados em 2026-10-08
- `_reversa_forward/009-rota-do-apple-touch-icon/evidence/` (`T003`, `T008`, `T009`, `T010`, `T011`, `T012`)
- `_reversa_forward/009-rota-do-apple-touch-icon/roadmap.md` (`D-01` a `D-10`)
- `_reversa_sdd/architecture.md`, `_reversa_sdd/domain.md`, `_reversa_sdd/upload-gedcom/contracts.md`

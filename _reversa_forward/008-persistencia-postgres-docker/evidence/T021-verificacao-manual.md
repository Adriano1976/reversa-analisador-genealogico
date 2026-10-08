# T021 — Verificação manual de ponta a ponta

> Feature: `008-persistencia-postgres-docker` · Data: `2026-10-08`
> Ações cobertas: `T021` — os passos §6 e §9 do `onboarding.md`, com dado **sintético**
> (`RF-02`, `RF-10`, `RF-16`, `RF-17`, Princípio I)

## 1. Estado de partida

| Medição | Valor |
|---|---|
| Análises gravadas | **0** — a limpeza do `T020` esvaziou |
| Arquivos em `src/uploads/` no host | **35** |

## 2. Upload e análise, com o banco no ar

`upload_gedcom` e `dna_analysis` pelo `curl`, com o GEDCOM e o CSV sintéticos de
`evidence/_tmp_e2e/` — e nada de dado real em nenhum ponto.

| Medição | Valor |
|---|---|
| Chave da árvore | `b79bce6984606468__arvore.ged` |
| Conexões na tela | **2** |
| Aviso de persistência | **ausente** — banco no ar |
| Análises gravadas | **1** |

## 3. `down` + `up` **sem** `-v` — `RF-02` provado

É a metade do `RF-02` que o `T020` não podia cobrir: o ciclo de vida dos serviços.

| Medição | Antes | Depois do ciclo |
|---|---|---|
| Arquivos em `src/uploads/` | 35 | **35** |
| Análises gravadas | 1 | **1** |
| Conexões consultáveis | 2 | **2** |
| Kits consultáveis | 2 | **2** |
| O arquivo enviado continua lá? | — | **`True`** |

**O bind mount dos uploads e o volume nomeado do banco sobreviveram os dois ao
`down`/`up`** — que é exatamente o que a `D-08` desenhou, com regimes diferentes para cada
estado.

Banco pronto em **3 s** e aplicação respondendo `200` em **8 s** depois do ciclo.

## 4. Banco **derrubado** — `RF-17` provado pela rota

`docker compose stop db`, e a mesma análise de novo:

| Medição | Valor |
|---|---|
| HTTP | **`200`** — e nao `500` |
| Conexões na tela | **2** |
| **Aviso não bloqueante** | **presente** |
| Texto do aviso | `Histórico não registrado: OperationalError: could not translate host name "db" to address: No address asso…` |

⚠️ **A causa da falha aqui é a de produção**, e não a do host: com o contêiner do banco
parado, o nome `db` não resolve, e é isso que o `OperationalError` diz. O `T019`, rodando no
`.venv/` do host, exercita a **mesma invariante** por outra causa — a ausência do driver. As
duas juntas cobrem o que o `Q-03` decidiu: **a análise nunca depende do banco para ser
exibida**.

## 5. Depois de religar o banco: nada parcial

| Medição | Valor |
|---|---|
| Análises (antes do passo 4) | 1 |
| Análises (depois de religar) | **1** |

A gravação que falhou **não deixou linha nenhuma** — nem a de `dna_analysis`, que é inserida
primeiro. É o `RF-10` verificado no caminho de falha real, e não só no `CHECK` do `T020`.

## 6. Limpeza e escopo — `RF-16` e Princípio I

```
DELETE FROM dna_analysis;   -> DELETE 1
SELECT count(*) ...         -> 0
```

O `git status` depois da verificação **não lista `src/uploads/`**, porque a pasta é coberta
pelo `.gitignore` (`uploads/`, linha 34) — e nada de dado real entrou em fixture, evidência ou
captura. Os dois HTMLs gerados na verificação foram removidos.

## 7. O que este passo **não** provou

1. **Não houve comparação byte a byte da tela com e sem o banco.** O que foi medido é que a
   tela renderiza `200` com as **mesmas 2 conexões** nos dois estados, mais o aviso. A
   `RF-17` fala em "a mesma tela", e a prova mais forte seria um `diff` ignorando o bloco do
   aviso — ele não foi feito aqui. O que existe é o teste do estado desabilitado
   (`test_persistencia_desabilitada.py`), que compara o caso **sem** persistência.
2. **Nenhum dado real foi usado**, e é por isso que o teste vale: o GEDCOM é o sintético de
   `tests/fixtures/sample_dna.py`, com cinco pessoas.
3. **A sobrevivência ao `down -v` não foi testada, e não deve ser**: `-v` remove o volume por
   definição, e o `T020` o usou de propósito para recriar o esquema.

# `T023` — medição do bloco 3 (`dna_analysis`) e resultado final

> Ponto de medição da `D-09` para o terceiro bloco, e o fechamento. Ver o **Desvio
> 2** nas "Notas de execução" do `../actions.md`.

## Resultado final

| Instrumento | Antes (linha de base `T004` da feature 005) | Depois | Veredito |
|---|---|---|---|
| Suíte completa | `178 passed, 15 errors` | **`231 passed, 15 errors`** | ✅ 53 testes novos, nenhuma falha nova |
| Erros por arquivo | 15 em `tests/test_upload_seguranca.py` | **os mesmos 15**, no mesmo arquivo | ✅ nenhum erro novo |
| Paridade diferencial | `PARIDADE 100%`, exit 0 | **`PARIDADE 100%`, exit 0** | ✅ idêntico |
| Sonda de mensagens | `mensagens_antes.json` | `mensagens_depois.json` — **0 divergências em 19 casos** | ✅ status, alerta e texto |
| Varredura de forma (`T020`) | passo de domínio presente | **APROVADO** | ✅ |
| Verificação manual (`T025`) | — | os sete passos do `onboarding.md` passam | ✅ no `waitress` real |

## Nenhum teste foi removido, desabilitado ou reescrito

Esta é a afirmação que a ação manda **confirmar**, e não só verificar por
impressão. Medido:

- A contagem **cresceu** de 178 para 231. Um teste removido teria feito a contagem
  cair; um teste desabilitado teria acrescentado `skip` ou `xfail`.
- **Nenhum `skip` e nenhum `xfail` foi introduzido** nesta feature. Os dois
  arquivos de teste que existiam e foram migrados
  (`tests/test_upload.py`, `tests/test_arvore_devolvida.py`) mantiveram o número de
  testes e as asserções: o que mudou foi a **procedência** do dado, de casca para
  árvore.
- Dois testes desses arquivos ganharam **nome novo**, porque o antigo falava de um
  estado global que não existe desde a feature 005:
  `test_load_populates_globals` → `test_carga_devolve_a_arvore_com_pessoas_e_familias`
  e `test_reload_replaces_globals` → `test_recarga_nao_soma_a_arvore_anterior`.
  Renomear não remove nem enfraquece: as asserções dos dois são as mesmas.
- `git diff --numstat tests/test_upload_seguranca.py` no acréscimo de `T030`/`T031`:
  **129 adições, 0 remoções** — as 425 linhas originais, o fixture `app_cliente` e
  as constantes estão intactos.

## Casos do bloco 3 na sonda diferencial

| Caso | Status | Classe do alerta | Texto |
|---|---|---|---|
| `dna_sem_csv` | `200` | `danger` | `Por favor, carregue o arquivo CSV de matches.` |
| `dna_csv_nome_vazio` | `200` | `danger` | `Por favor, carregue o arquivo CSV de matches.` |
| `dna_raiz_ausente` | `200` | `danger` | `Ocorreu um erro: Seu nome 'Zzz Ninguem' não foi encontrado no GEDCOM.` |
| `dna_csv_sem_colunas` | `200` | `danger` | `Ocorreu um erro: Colunas de Nome e cM não encontradas no CSV. O arquivo foi lido com o separador ',' e as colunas encontradas foram: ['alfa', 'beta']. …` |
| `dna_ok` | `200` | **`success`** | `1 conexões encontradas. 0 descartadas.` |

Este é o bloco onde a tabela de tradução mais podia errar, e a medição é o motivo
de ela existir: `dna_raiz_ausente` e `dna_csv_sem_colunas` são exibidas **com o
prefixo** `Ocorreu um erro: `, enquanto o GEDCOM recusado do bloco 1 é exibido
**sem** prefixo nenhum. Escrever a tabela de cabeça produziria uma das duas formas
erradas, e as duas apareceriam como "pequena diferença de redação" na revisão —
que é exatamente o que a `RN-02` e a `RN-04` proíbem.

O caso `dna_ok` cobre a única mensagem de sucesso do fluxo, e `dna_csv_nome_vazio`
cobre uma guarda de formulário que **nenhum teste tinha antes** (`A005`).

## `T025` — verificação manual no servidor de produção

Executada com `waitress` na porta `58041`. Resultado e saídas cruas em
`T025-verificacao-manual.md`. Dois achados, os dois em `onboarding.md` e nenhum no
código:

1. O padrão de cabeçalho do passo 6.3 não existe no template — o template renderiza
   `Resultado da Análise` e o Gherkin congelado diz `Resultados da Análise de DNA`.
   Divergência **anterior a esta feature**; o template não foi tocado. Virou o item
   `W019` do `regression-watch.md`.
2. O padrão do passo 6.5b usava apóstrofo literal, e o Jinja escapa apóstrofo no
   HTML. O texto estava certo; o padrão era inalcançável.

## Resíduo

`src/uploads/` ficou com as mesmas **32** entradas de antes da feature — a
verificação manual usou pasta isolada. O `_clean_residue.py` do instrumento de
paridade foi executado. O `git status` final está no relatório da rodada, e a única
coisa que ele mostra além dos arquivos desta feature é o resíduo pré-existente
(`.parity-run-cand/`, os dois `_collect_*.py` gerados pelo harness) e a cicatriz de
diretório preso em `tests/`, tratada em `tests/conftest.py` e inventariada em
`README-evidencias.md` §2.2.

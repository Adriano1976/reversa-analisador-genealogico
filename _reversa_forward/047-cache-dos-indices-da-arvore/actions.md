# Actions: cache dos índices derivados da árvore

> Identificador: `047-cache-dos-indices-da-arvore`
> Data: `2026-10-24`
> Roadmap: `_reversa_forward/047-cache-dos-indices-da-arvore/roadmap.md`

## Resumo

| Métrica | Valor |
|---------|-------|
| Total de ações | 17 |
| Paralelizáveis (`[//]`) | 6 |
| Maior cadeia de dependência | 10 |

## Fase 1, Preparação

| ID | Descrição | Dependências | Paralelismo | Arquivo alvo | Confidência | Status |
|----|-----------|--------------|-------------|--------------|-------------|--------|
| T001 | Criar o instrumento de medição: sobe a aplicação com porta e pasta de upload descartáveis, executa upload, seleção e análise, cronometra as fases (parse, índices, pipeline, render) e imprime o `sha256` da árvore e do resultado. Grava apenas contagens, tempos e hashes — nunca nome, `xref` ou cM | - | `[//]` | `_reversa_forward/047-cache-dos-indices-da-arvore/evidence/medir.py` | 🟢 | `[ ]` |
| T002 | Registrar a linha de base com o instrumento: suíte (esperado `1635 passed, 9 skipped`), `POST` de análise (67,29 s) e de seleção (47,56 s), com as fases e os dois hashes. Sem `DATABASE_URL` no ambiente | T001 | - | `_reversa_forward/047-cache-dos-indices-da-arvore/evidence/linha-de-base.md` | 🟢 | `[ ]` |

## Fase 2, Testes

| ID | Descrição | Dependências | Paralelismo | Arquivo alvo | Confidência | Status |
|----|-----------|--------------|-------------|--------------|-------------|--------|
| T003 | Escrever os testes do cache da árvore no estado desligado e ligado: sem a variável, duas chamadas parseiam duas vezes; com `ANALISADOR_CACHE_DE_ARVORE=1`, parseiam uma vez e devolvem a **mesma** árvore; valores `0`, `nao`, `false` e vazio não ligam | - | `[//]` | `tests/test_cache_de_arvores.py` | 🟢 | `[ ]` |
| T004 | Acrescentar os testes de invalidação e teto: arquivo trocado no mesmo caminho (com `os.utime` forçando `mtime` novo) reconstrói; teto 1 carrega A, B e A de novo e reconstrói A; capacidade 0 levanta `ValueError` | T003 | - | `tests/test_cache_de_arvores.py` | 🟢 | `[ ]` |
| T005 | Acrescentar o teste de concorrência (4 threads na mesma árvore pagam **um** parse, com contador e barreira) e o de referência inexistente (devolve `None` sem parsear) | T004 | - | `tests/test_cache_de_arvores.py` | 🟢 | `[ ]` |
| T006 | Escrever os testes do memo de índices: duas chamadas de `build_ged_indexes(arvore)` devolvem o **mesmo objeto** e a segunda não percorre as pessoas (contando chamadas a `get_name`); os dicionários devolvidos não são mutados pelos consumidores | - | `[//]` | `tests/test_indices_de_matching_memo.py` | 🟢 | `[ ]` |
| T007 | Acrescentar o teste de não-contaminação (classe `L-24`): duas árvores com o mesmo número de pessoas e os mesmos `xref` extremos **não** compartilham índices, e a segunda não enxerga `xref` da primeira | T006 | - | `tests/test_indices_de_matching_memo.py` | 🟢 | `[ ]` |

## Fase 3, Núcleo

| ID | Descrição | Dependências | Paralelismo | Arquivo alvo | Confidência | Status |
|----|-----------|--------------|-------------|--------------|-------------|--------|
| T008 | Implementar `CacheDeArvores` em `adaptadores.py`: chave `(caminho absoluto, mtime_ns, tamanho)`, LRU com teto, trava, evento de *single-flight* por chave, `VARIAVEL_DO_CACHE`, capacidade padrão 1 e leitura das duas variáveis de ambiente. Documentar no próprio arquivo por que a chave é o arquivo e por que o teto é 1 | T003, T004, T005 | - | `src/ports/adaptadores.py` | 🟢 | `[ ]` |
| T009 | Ligar o cache ao `CarregadorDeArvoresGedcom`: parâmetro `cache` injetável (padrão decidido pelo ambiente) e `carregar` usando o cache quando presente, sem mudar a assinatura pública da porta | T008 | - | `src/ports/adaptadores.py` | 🟢 | `[ ]` |
| T010 | Memoizar `build_ged_indexes` no **grafo da árvore**, com atributo privado e o mesmo padrão de `fichas_da_pessoa._indice_de_filhos`; devolver sempre o mesmo trio e nunca usar chave derivada de conteúdo. Documentar a razão no docstring | T006, T007 | - | `src/core/matching.py` | 🟢 | `[ ]` |

## Fase 4, Integração

| ID | Descrição | Dependências | Paralelismo | Arquivo alvo | Confidência | Status |
|----|-----------|--------------|-------------|--------------|-------------|--------|
| T011 | Emitir, por carga, uma linha de log com acerto, erro e reconstrução do cache (RF-06), sem nome, `xref` ou cM; acrescentar teste que verifica a contagem emitida | T009, T005 | - | `src/ports/adaptadores.py` | 🟢 | `[ ]` |
| T012 | Rodar a suíte completa sem `DATABASE_URL`, corrigir regressões e registrar o número final (esperado: `1635 + 13` testes, zero falhas) | T010, T011 | - | `tests/` | 🟢 | `[ ]` |
| T013 | Medir o depois com o mesmo instrumento do T001, nos dois estados (cache ligado e desligado), e registrar as fases lado a lado com a linha de base | T012 | - | `_reversa_forward/047-cache-dos-indices-da-arvore/evidence/depois.md` | 🟢 | `[ ]` |
| T014 | Conferir a paridade: `sha256` da árvore e do resultado idênticos com o cache ligado e desligado, no mesmo GEDCOM e no mesmo CSV | T013 | `[//]` | `_reversa_forward/047-cache-dos-indices-da-arvore/evidence/paridade.md` | 🟢 | `[ ]` |
| T015 | Medir a memória: RSS depois do parse e depois dos índices, com teto 1, e registrar os dois números ao lado dos 381 MB e 412 MB previstos | T013 | `[//]` | `_reversa_forward/047-cache-dos-indices-da-arvore/evidence/memoria.md` | 🟢 | `[ ]` |

## Fase 5, Polimento

| ID | Descrição | Dependências | Paralelismo | Arquivo alvo | Confidência | Status |
|----|-----------|--------------|-------------|--------------|-------------|--------|
| T016 | Atualizar o `onboarding.md` com os números efetivamente medidos (tempo por fase e RSS), substituindo os valores esperados e a tabela de sintomas se algo tiver mudado | T013, T014, T015 | - | `_reversa_forward/047-cache-dos-indices-da-arvore/onboarding.md` | 🟢 | `[ ]` |
| T017 | Documentar as duas variáveis de ambiente no `docker-compose.yml`, comentadas e sem ligar, para o operador que quiser habilitar no contêiner | T011 | `[//]` | `docker-compose.yml` | 🟢 | `[ ]` |

## Notas de execução

## Histórico de alterações

| Data | Alteração | Autor |
|------|-----------|-------|
| 2026-10-24 | Versão inicial gerada por `/reversa-to-do` | reversa |

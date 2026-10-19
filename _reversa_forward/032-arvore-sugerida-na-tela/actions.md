# Actions: árvore sugerida na tela

> Identificador: `032-arvore-sugerida-na-tela`
> Data: `2026-10-19`
> Roadmap: `_reversa_forward/032-arvore-sugerida-na-tela/roadmap.md`

## Resumo

| Métrica | Valor |
|---------|-------|
| Total de ações | 14 |
| Paralelizáveis (`[//]`) | 2 |
| Maior cadeia de dependência | 4 |

## Fase 1, Preparação

| ID | Descrição | Dependências | Paralelismo | Arquivo alvo | Confidência | Status |
|----|-----------|--------------|-------------|--------------|-------------|--------|
| T001 | Estender `tests/fixtures/resultado_para_cartao.py` com as quatro chaves de sugestão e dois helpers: um cartão com sugestão e um em conflito sem gerações a injetar | - | `[//]` | `tests/fixtures/resultado_para_cartao.py` | 🟢 | `[X]` |

## Fase 2, Testes

| ID | Descrição | Dependências | Paralelismo | Arquivo alvo | Confidência | Status |
|----|-----------|--------------|-------------|--------------|-------------|--------|
| T002 | Escrever os testes de `resumo_da_sugestao` nos quatro casos: sugestão com hiato 3, hiato 0, sem estimativa e cartão validado (aviso nulo) | - | - | `tests/test_resumo_da_sugestao.py` | 🟢 | `[X]` |
| T003 | Escrever o teste de custo: um espião em `arvore_sugerida` que levanta prova que o fluxo de DNA não chama a cirurgia, e que o resumo roda só com dicionários | - | - | `tests/test_resumo_da_sugestao.py` | 🟢 | `[X]` |
| T004 | Escrever os testes do emissor: `graph TD`, os três `classDef` da paleta, os `:::` por classe, a aresta `-.->` rotulada e o `linkStyle` no índice da última aresta | - | - | `tests/test_mermaid_da_sugestao.py` | 🟢 | `[X]` |
| T005 | Escrever os testes de determinismo e escape do emissor: duas chamadas idênticas e nome com aspas e parêntese sem quebrar a gramática | T004 | - | `tests/test_mermaid_da_sugestao.py` | 🟢 | `[X]` |
| T006 | Escrever os testes de tela: bloco presente, resumo no `<summary>`, diagrama no corpo e posição **depois** de `grafo-do-registro` | T001 | - | `tests/test_arvore_sugerida_na_tela.py` | 🟢 | `[X]` |
| T007 | Escrever o teste do caso negativo: cartão validado não mostra bloco nem frase; cartão em conflito com hiato 0 mostra a frase e nenhum diagrama | T001 | - | `tests/test_arvore_sugerida_na_tela.py` | 🟢 | `[X]` |

## Fase 3, Núcleo e emissor

| ID | Descrição | Dependências | Paralelismo | Arquivo alvo | Confidência | Status |
|----|-----------|--------------|-------------|--------------|-------------|--------|
| T008 | Implementar `resumo_da_sugestao(resultado, documental)` em `core/cirurgia_do_grafo`, derivando o hiato pela fórmula da `029`, sem tocar no grafo, e incluí-la no `__all__` | - | - | `src/core/cirurgia_do_grafo.py` | 🟢 | `[X]` |
| T009 | Implementar `mermaid_da_sugestao(...)` em `reporting/mermaid_render`, com `classDef` das três classes, cadeia virtual e aresta rompida por último | - | `[//]` | `src/reporting/mermaid_render.py` | 🟢 | `[X]` |
| T010 | Acrescentar `gerar_mermaid_da_sugestao` (opcional, padrão `None`) a `Dependencias` e gravar as quatro chaves no dicionário de resultado em `core/dna_analysis` | T008, T009 | - | `src/core/dna_analysis.py` | 🟢 | `[X]` |
| T011 | Passar o emissor na montagem de `Dependencias` em `src/app.py` e em `tests/fixtures/helpers.py` | T010 | - | `src/app.py` | 🟢 | `[X]` |

## Fase 4, Tela

| ID | Descrição | Dependências | Paralelismo | Arquivo alvo | Confidência | Status |
|----|-----------|--------------|-------------|--------------|-------------|--------|
| T012 | Renderizar o `details.arvore-sugerida` depois do diagrama documentado, com o resumo no `<summary>`, e a frase de ausência quando `sugestao_aviso` existir | T001, T010 | - | `src/templates/index.html` | 🟢 | `[X]` |

## Fase 5, Polimento

| ID | Descrição | Dependências | Paralelismo | Arquivo alvo | Confidência | Status |
|----|-----------|--------------|-------------|--------------|-------------|--------|
| T013 | Completar docstrings e comentários: por que a tela não chama a cirurgia, por que o emissor entra por injeção (ADR-34) e por que Mermaid e não Graphviz | T012 | - | `src/core/cirurgia_do_grafo.py` | 🟡 | `[X]` |
| T014 | Rodar a suíte completa, conferir `git status`, **verificar** que o `SHA_DA_TELA` não muda e reiniciar o servidor para ver o bloco | T011, T012, T013 | - | `tests/` | 🟢 | `[X]` |

## Notas de execução

Cinco observações registradas durante o coding.

1. **O plano foi corrigido antes do código: `src/app.py` muda.** Ao decompor, ficou claro que
   `core/dna_analysis` não pode importar `reporting/` (ADR-34) — o emissor entra por injeção em
   `Dependencias`, e a borda passa a fornecê-lo. Virou `D-11` no `roadmap.md`, com as três
   alternativas descartadas.
2. **`_validacao_do_cartao` passou a devolver `(chaves, resultado_bruto)`.** O resumo da árvore
   precisa do `status` e do `mrca_estimado` do **validador**, que ficavam dentro da função. Devolver
   o bruto evita recalcular o veredito por cartão.
3. **O vocabulário dos códigos foi unificado.** O `requirements.md` criava `SEM_GERACOES_A_SUGERIR` e
   `SEM_ESTIMATIVA_DE_MRCA`; a implementação usa `HIATO_NAO_POSITIVO` e `SEM_MRCA_ESTIMADO`, que já
   existem na `029`. Dois nomes para o mesmo fato é a classe de defeito que este projeto já pagou
   caro para não repetir — o documento foi corrigido.
4. **O índice do `linkStyle` foi conferido na mão antes do teste.** No caminho de 4 pessoas e 2
   gerações saem 6 arestas, e a rompida é a de índice **5**. O teste fixa exatamente essa conta,
   porque uma reordenação mandaria o vermelho tracejado para a aresta errada em silêncio.
5. **O `SHA_DA_TELA` não mudou, como previsto.** Os 15 testes do ícone passam sem alteração — o
   bloco novo vive dentro do cartão, e `GET /` sem resultados não renderiza cartão. Diferente da
   `031`, aqui isso foi **verificado**, não suposto.

**Tempo da suíte, declarado sem maquiagem:** a suíte completa rodou em **446 s** (1198 passam, 11
pulados), contra 113 s da medição anterior. O mesmo subconjunto de 45 testes rodou em 7,46 s contra
5,42 s de antes — alta de ~38%, compatível com o trabalho novo por cartão. A diferença entre 38% e
4× é a máquina, não o código: o intervalo entre os dois comandos foi de 46 minutos, e o ambiente
estava visivelmente carregado. Fica registrado como suspeita, não como medição.

## Histórico de alterações

| Data | Alteração | Autor |
|------|-----------|-------|
| 2026-10-19 | Versão inicial gerada por `/reversa-to-do` | reversa |
| 2026-10-19 | 14 ações executadas; cinco observações, incluindo a correção do plano sobre `app.py` | reversa |

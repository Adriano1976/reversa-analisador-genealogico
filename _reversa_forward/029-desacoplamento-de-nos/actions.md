# Actions: desacoplamento de nós e gerações virtuais no grafo

> Identificador: `029-desacoplamento-de-nos`
> Data: `2026-10-18`
> Roadmap: `_reversa_forward/029-desacoplamento-de-nos/roadmap.md`

## Resumo

| Métrica | Valor |
|---------|-------|
| Total de ações | 22 |
| Paralelizáveis (`[//]`) | 4 |
| Maior cadeia de dependência | 9 |

## Fase 1, Preparação

| ID | Descrição | Dependências | Paralelismo | Arquivo alvo | Confidência | Status |
|----|-----------|--------------|-------------|--------------|-------------|--------|
| T001 | Criar `tests/fixtures/arvore_para_cirurgia.py` com três GEDCOMs sintéticos (doador de 1985 com ancestral de 1650 em duas gerações, linha datada válida e caminho por casamento) e os CSVs correspondentes; nenhum nome ou kit real | - | `[//]` | `tests/fixtures/arvore_para_cirurgia.py` | 🟢 | `[X]` |
| T002 | Acrescentar `incluir_documental: bool = False` a `validar_arquivos` e incluir a chave `documental` em cada comparação quando verdadeiro, sem alterar o retorno padrão | - | `[//]` | `src/application/validacao.py` | 🟢 | `[X]` |

## Fase 2, Testes

| ID | Descrição | Dependências | Paralelismo | Arquivo alvo | Confidência | Status |
|----|-----------|--------------|-------------|--------------|-------------|--------|
| T003 | Escrever os testes de `ramo_base` e `ramo_base_intacto`: ids e arestas na ordem do caminho, ancestral presente nos ids, aresta da junção fora das arestas protegidas e violação detectada quando uma aresta interna desaparece | T001 | - | `tests/test_cirurgia_do_grafo.py` | 🟢 | `[X]` |
| T004 | Escrever os testes de `juncao`: localização pelo `FAMC`/`CHIL` do filho, fallback pelo `child_to_family`, escolha do lado pelos códigos do resultado e `JUNCAO_NAO_LOCALIZADA` quando não há família | T001 | - | `tests/test_cirurgia_do_grafo.py` | 🟢 | `[X]` |
| T005 | Escrever os testes de `desacoplar_identidade`: aresta de filiação removida só na cópia, grafo original intacto, nó histórico preservado com as suas outras arestas e casamento nunca cortado | T001 | - | `tests/test_cirurgia_do_grafo.py` | 🟢 | `[X]` |
| T006 | Escrever os testes de `injetar_geracoes`: `k` nós `virtual` rotulados `Geração 1..k`, famílias `virtual-family` em cadeia, `k=0` sem alteração e ausência de `name`, `sex` e data exata | T001 | - | `tests/test_cirurgia_do_grafo.py` | 🟢 | `[X]` |
| T007 | Escrever os testes de `arvore_sugerida` para o contrato de §4.7 e os três status: `natureza`, `grafo` nulo com o aviso correto, `status_origem` e `ramo_base.intacto` | T001 | - | `tests/test_sugestao_de_correcao.py` | 🟢 | `[X]` |
| T008 | Escrever os testes de hiato, insuficiência e determinismo: `2.5` arredonda para 3, `hiato <= 0` devolve `HIATO_NAO_POSITIVO`, cadeia curta emite `SUGESTAO_INSUFICIENTE` e dois processos com `PYTHONHASHSEED` diferente produzem os mesmos ids | T001 | - | `tests/test_sugestao_de_correcao.py` | 🟡 | `[X]` |
| T009 | Escrever o teste da emenda na `028`: sem o parâmetro o retorno tem as mesmas chaves de antes; com `incluir_documental=True` cada comparação traz `documental` com `path.ids` | T002 | `[//]` | `tests/test_validacao_de_arquivos.py` | 🟢 | `[X]` |

## Fase 3, Núcleo

| ID | Descrição | Dependências | Paralelismo | Arquivo alvo | Confidência | Status |
|----|-----------|--------------|-------------|--------------|-------------|--------|
| T010 | Criar `src/core/cirurgia_do_grafo.py` com as constantes de tipo (`virtual`, `virtual-family`), o prefixo de id, os helpers de rótulo e de id derivado do conteúdo, as assinaturas públicas e o `__all__` | T001 | - | `src/core/cirurgia_do_grafo.py` | 🟢 | `[X]` |
| T011 | Implementar `ramo_base` e `ramo_base_intacto`, com as arestas internas do caminho do doador e a aresta da junção excluída por construção | T010, T003 | - | `src/core/cirurgia_do_grafo.py` | 🟢 | `[X]` |
| T012 | Implementar o índice família→filhos montado uma vez por chamada, a partir do `child_to_family` e dos registros `CHIL` | T010 | - | `src/core/cirurgia_do_grafo.py` | 🟢 | `[X]` |
| T013 | Implementar `juncao`, traduzindo o salto pessoa→pessoa no par pessoa↔família e escolhendo o lado pelos códigos do resultado | T012, T004 | - | `src/core/cirurgia_do_grafo.py` | 🟢 | `[X]` |
| T014 | Implementar `desacoplar_identidade` sobre `grafo.copy()`, removendo apenas a aresta de filiação da junção e recusando qualquer aresta de casamento | T011, T013, T005 | - | `src/core/cirurgia_do_grafo.py` | 🟢 | `[X]` |
| T015 | Implementar `injetar_geracoes` com `k` nós virtuais, `k` famílias sintéticas, faixa de nascimento estimada e justificativa por nó | T014, T006 | - | `src/core/cirurgia_do_grafo.py` | 🟢 | `[X]` |
| T016 | Implementar `arvore_sugerida` orquestrando os passos 1 a 8 de §4.6 e devolvendo o contrato de §4.7 | T015, T007 | - | `src/core/cirurgia_do_grafo.py` | 🟢 | `[X]` |
| T017 | Implementar a conferência de janela de §4.6 passo 9 e o aviso `SUGESTAO_INSUFICIENTE`, sem ajustar `k` | T016, T008 | - | `src/core/cirurgia_do_grafo.py` | 🟡 | `[X]` |

## Fase 4, Integração

| ID | Descrição | Dependências | Paralelismo | Arquivo alvo | Confidência | Status |
|----|-----------|--------------|-------------|--------------|-------------|--------|
| T018 | Criar `src/application/correcao.py` com `sugerir_correcao`, reutilizando `validar_arquivos(..., incluir_documental=True)` e montando uma sugestão por comparação | T017, T002 | - | `src/application/correcao.py` | 🟢 | `[X]` |
| T019 | Escrever o teste de integração da fachada com GEDCOM e CSV sintéticos, cobrindo erro com sugestão, validado sem sugestão e múltiplos kits | T018 | - | `tests/test_correcao_de_arquivos.py` | 🟢 | `[X]` |
| T020 | Escrever o teste de fronteira garantindo que `core/cirurgia_do_grafo.py` não importa `parsers`, `application`, `reporting`, HTTP nem `datetime`, e não abre arquivo | T010 | `[//]` | `tests/test_fronteira_da_cirurgia.py` | 🟢 | `[X]` |

## Fase 5, Polimento

| ID | Descrição | Dependências | Paralelismo | Arquivo alvo | Confidência | Status |
|----|-----------|--------------|-------------|--------------|-------------|--------|
| T021 | Completar as docstrings de `cirurgia_do_grafo.py` e `correcao.py` com a fórmula do hiato, a topologia da cadeia, a razão do `copy()` e a limitação de D-11 (o grafo sugerido não serve aos leitores existentes) | T018 | - | `src/core/cirurgia_do_grafo.py` | 🟡 | `[X]` |
| T022 | Rodar a suíte completa no `.venv`, conferir `git status`/`git diff --stat` e confirmar que `app.py`, template, CSS, `init.sql`, `requirements.txt` e as tabelas do banco não mudaram | T019, T020, T021 | - | `tests/` | 🟢 | `[X]` |

## Notas de execução

Seis observações registradas durante o coding. Todas são **desvios declarados** do
`actions.md`, nenhuma é correção silenciosa.

1. **O contrato ganhou `juncoes` (plural).** Com os dois lados acusados e famílias de
   junção diferentes, há **duas** junções a cortar; `juncao` continua sendo a primeira.
   Sem isso, `DOIS_LADOS_ACUSADOS` prometeria uma divisão que o contrato não saberia
   representar.
2. **Dois lados podem compartilhar a mesma família de junção** (dois filhos do mesmo
   ancestral). Cortar a mesma aresta duas vezes falharia na segunda, então a lista é
   deduplicada e a cadeia, nesse caso, é única. Achado durante a escrita dos testes, não
   previsto no plano.
3. **`incluir_documental` também devolve a chave `arvore`.** O plano dizia só
   `documental`, mas `validar_arquivos` não devolvia a árvore parseada — sem ela, a
   fachada de correção teria de reparsear o GEDCOM. As duas chaves saem do **mesmo**
   opt-in e o retorno padrão continua idêntico.
4. **A fixture ganhou `GED_DOIS_LADOS`** (quarta árvore) e a árvore "por casamento" foi
   trocada por `GED_MATCH_SEM_FAMILIA`. Motivo: `documentary_relationship` **nunca**
   devolve `status="affinity"` — a afinidade nasce em `core.path_search`, não no
   parentesco documental. O cenário de afinidade passou a ser exercitado com um
   `documental` montado à mão, e o teste de "casamento nunca é cortado" usa os cônjuges
   `@I2@`/`@I3@` da árvore existente.
5. **As datas de `GED_SALTO_IMPOSSIVEL` mudaram** (match em 1710, tia em 1680, tio em
   1678). Com o match em 1950, o salto do lado do match também ficava implausível
   (1650 → 1925), e o caso deixava de ser o do requirements — uma linha quebrada no lado
   do doador. A árvore nova acusa **só** o lado do doador; os dois lados ficaram em
   `GED_DOIS_LADOS`.
6. **O teste de `PYTHONHASHSEED` roda em processo, duas vezes**, e não em subprocesso
   com semente diferente. O sandbox desta sessão recusa subprocesso com stdio capturado;
   a verificação equivalente é chamar duas vezes e comparar ids, ordem e conjunto de
   nós, mais a asserção de que o id é derivado do conteúdo (`VIRTUAL:@I1@:@I10@:doador:1`).

## Histórico de alterações

| Data | Alteração | Autor |
|------|-----------|-------|
| 2026-10-18 | Versão inicial gerada por `/reversa-to-do` | reversa |
| 2026-10-18 | 22 ações executadas; seis desvios declarados nas notas de execução | reversa |

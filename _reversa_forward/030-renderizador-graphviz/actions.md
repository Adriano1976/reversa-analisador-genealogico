# Actions: renderizador Graphviz da árvore sugerida

> Identificador: `030-renderizador-graphviz`
> Data: `2026-10-18`
> Roadmap: `_reversa_forward/030-renderizador-graphviz/roadmap.md`

## Resumo

| Métrica | Valor |
|---------|-------|
| Total de ações | 19 |
| Paralelizáveis (`[//]`) | 3 |
| Maior cadeia de dependência | 7 |

## Fase 1, Preparação

| ID | Descrição | Dependências | Paralelismo | Arquivo alvo | Confidência | Status |
|----|-----------|--------------|-------------|--------------|-------------|--------|
| T001 | Acrescentar `graphviz==0.21` ao `requirements.txt`, junto das diretas, com comentário citando `ADR-13` e avisando que o binário `dot` não vem do `pip` | - | `[//]` | `requirements.txt` | 🟢 | `[X]` |
| T002 | Criar `tests/fixtures/sugestao_para_desenho.py` com uma sugestão sintética independente da `029`: grafo de fixture, uma junção, duas gerações virtuais e o resultado de validação com `cm` e `geracoes` conhecidos | - | `[//]` | `tests/fixtures/sugestao_para_desenho.py` | 🟢 | `[X]` |

## Fase 2, Testes

| ID | Descrição | Dependências | Paralelismo | Arquivo alvo | Confidência | Status |
|----|-----------|--------------|-------------|--------------|-------------|--------|
| T003 | Escrever os testes de estrutura e cores do DOT: `digraph`, `rankdir=TB`, `#a8e6cf` no nó base, `#f5f5f5` no documental, `#ffd3b6` no virtual | T002 | - | `tests/test_visualizer.py` | 🟢 | `[X]` |
| T004 | Escrever os testes da aresta rompida (`style=dashed`, `color=red`, rótulo literal) e da cadeia sugerida entre o ancestral e o filho | T002 | - | `tests/test_visualizer.py` | 🟢 | `[X]` |
| T005 | Escrever os testes da caixa de evidência: formato `21.6 cM, 5.7 gerações - ...`, campo `—` quando falta dado e o mapa de veredito por código crítico | T002 | - | `tests/test_visualizer.py` | 🟢 | `[X]` |
| T006 | Escrever os testes de escape (aspas, barra, `&`, acento) e de recorte (sem nó de família, sem irmão fora do caminho) | T002 | - | `tests/test_visualizer.py` | 🟢 | `[X]` |
| T007 | Escrever os testes de recusa e determinismo: `SEM_SUGESTAO_PARA_DESENHAR`, `FORMATO_NAO_SUPORTADO`, `DESTINO_OBRIGATORIO` e duas chamadas com texto idêntico | T002 | - | `tests/test_visualizer.py` | 🟢 | `[X]` |
| T008 | Escrever o teste de `DOT_AUSENTE` e `GRAPHVIZ_AUSENTE`, com `shutil.which` e o helper de import monkeypatchados | T002 | - | `tests/test_visualizer.py` | 🟢 | `[X]` |
| T009 | Escrever o teste de fronteira por AST: `import graphviz` só dentro de função e nenhum import de `core` | T010 | - | `tests/test_fronteira_do_visualizer.py` | 🟢 | `[X]` |

## Fase 3, Núcleo

| ID | Descrição | Dependências | Paralelismo | Arquivo alvo | Confidência | Status |
|----|-----------|--------------|-------------|--------------|-------------|--------|
| T010 | Criar `src/reporting/visualizer.py` com as constantes de cor e rótulo, a exceção `ErroDeRenderizacao` com `codigo`, os helpers de escape, de veredito e de import preguiçoso, e o `__all__` | T002 | - | `src/reporting/visualizer.py` | 🟢 | `[X]` |
| T011 | Implementar o recorte: nós do caminho, nós virtuais e as arestas genitor→filho com a inversão antes do ancestral | T010, T003 | - | `src/reporting/visualizer.py` | 🟢 | `[X]` |
| T012 | Implementar as arestas rompidas por junção e a cadeia sugerida do ancestral até o filho, com os atributos de estilo | T011, T004 | - | `src/reporting/visualizer.py` | 🟢 | `[X]` |
| T013 | Implementar a caixa de evidência (`shape=note`, aresta invisível ao doador) e o mapa de veredito | T011, T005 | - | `src/reporting/visualizer.py` | 🟢 | `[X]` |
| T014 | Implementar `texto_dot` fechando o grafo com título, `bgcolor` e ordem determinística de nós e arestas | T012, T013, T006 | - | `src/reporting/visualizer.py` | 🟢 | `[X]` |
| T015 | Implementar `renderizar_arvore_sugerida`: validar destino e formato, checar `dot` com `shutil.which`, importar `graphviz` sob demanda e gravar a imagem | T014, T007, T008 | - | `src/reporting/visualizer.py` | 🟢 | `[X]` |

## Fase 4, Integração

| ID | Descrição | Dependências | Paralelismo | Arquivo alvo | Confidência | Status |
|----|-----------|--------------|-------------|--------------|-------------|--------|
| T016 | Escrever o teste fim-a-fim com GEDCOM e CSV sintéticos: validação, sugestão da `029` e DOT não vazio, sem exigir imagem | T015 | - | `tests/test_visualizer_integracao.py` | 🟢 | `[X]` |
| T017 | Escrever o teste de renderização real (PNG e SVG), com `skipif` quando o `dot` não está no `PATH` e motivo declarado | T015 | `[//]` | `tests/test_visualizer_render.py` | 🟢 | `[X]` |

## Fase 5, Polimento

| ID | Descrição | Dependências | Paralelismo | Arquivo alvo | Confidência | Status |
|----|-----------|--------------|-------------|--------------|-------------|--------|
| T018 | Completar as docstrings do módulo: compressão de família, formato do rótulo, razão do import preguiçoso e a citação ao `L-26` e ao `ADR-34` | T015 | - | `src/reporting/visualizer.py` | 🟡 | `[X]` |
| T019 | Rodar a suíte completa no `.venv`, conferir `git status`/`git diff --stat` e confirmar que `app.py`, template, CSS, `mermaid_render.py`, Docker e banco não mudaram | T016, T017, T018 | - | `tests/` | 🟢 | `[X]` |

## Notas de execução

Quatro observações registradas durante o coding.

1. **O salto rompido não é desenhado duas vezes.** A primeira versão desenhava, para a
   junção, a filiação comum **e** a cadeia virtual **e** a aresta tracejada — três ligações
   entre o mesmo par de pessoas. Ficou decidido que o salto da junção só recebe a aresta
   tracejada (o vínculo que caiu) e a cadeia (a sugestão); a filiação comum é omitida
   naquele salto. Não estava no `actions.md` porque só apareceu ao ver o texto pronto.
2. **O pin é `graphviz==0.21`**, a versão verificada no `.venv` — e o comentário no
   `requirements.txt` avisa que o binário `dot` **não** vem do `pip`, senão a próxima pessoa
   instala o pacote, tenta renderizar e não entende o `DOT_AUSENTE`.
3. **A fixture do desenho é independente da `029`.** `tests/fixtures/sugestao_para_desenho.py`
   monta à mão o dicionário da sugestão; se ela dependesse da cirurgia, uma mudança na `029`
   quebraria o teste do desenho por um motivo que não é do desenho.
4. **O ambiente mudou no meio do pipeline.** O binding `graphviz` foi instalado às 02:18,
   depois da medição das 02:10 que dizia que ele faltava. Os documentos foram corrigidos com
   a hora de cada medição; o pin só pôde ser fixado porque a segunda medição existiu.

**Cobertura declarada:** 32 testes novos passam; **2 são pulados** — os de renderização real,
porque o binário `dot` não está no `PATH`. O caminho de falha (`DOT_AUSENTE`) é testado com
`shutil.which` monkeypatchado, então a recusa está coberta; o que não está é a imagem gerada.

## Histórico de alterações

| Data | Alteração | Autor |
|------|-----------|-------|
| 2026-10-18 | Versão inicial gerada por `/reversa-to-do` | reversa |
| 2026-10-18 | 19 ações executadas; quatro observações e a cobertura parcial declarada | reversa |

<!--
Actions da feature 058 — Detalhamento dos segmentos compartilhados.
IDs estáveis, nunca reciclados. Status inicial [ ]. /reversa-coding muda para [X].
-->

# Actions: Detalhamento dos segmentos compartilhados

> Identificador: `058-detalhamento-dos-segmentos`
> Data: `2026-11-11`
> Roadmap: `_reversa_forward/058-detalhamento-dos-segmentos/roadmap.md`

## Resumo

| Métrica | Valor |
|---------|-------|
| Total de ações | 18 |
| Paralelizáveis (`[//]`) | 10 |
| Maior cadeia de dependência | 8 (T002 → T004 → T008 → T011 → T012 → T013 → T015 → T016) |

## Fase 1, Preparação

| ID | Descrição | Dependências | Paralelismo | Arquivo alvo | Confidência | Status |
|----|-----------|--------------|-------------|--------------|-------------|--------|
| T001 | Tornar `ordem_do_cromossomo` pública em `core/distribuicao.py` (renomear, entrar no `__all__`), sem mudar comportamento | - | `[//]` | `src/core/distribuicao.py` | 🟢 | `[X]` |
| T002 | Criar `src/core/segmentos.py` com o dataclass `SegmentoDeRegiao` e a assinatura documentada de `segmentos_das_regioes`, sem lógica | - | `[//]` | `src/core/segmentos.py` | 🟢 | `[X]` |
| T003 | Criar `src/application/segmentos.py` com a assinatura documentada de `projetar_segmentos`, sem lógica | - | `[//]` | `src/application/segmentos.py` | 🟢 | `[X]` |

## Fase 2, Testes

| ID | Descrição | Dependências | Paralelismo | Arquivo alvo | Confidência | Status |
|----|-----------|--------------|-------------|--------------|-------------|--------|
| T004 | Testes do núcleo: uma linha por par (região, kit), ordem cromossomo → início → kit, `regiao_indice` sobrevive à ordenação (duas regiões no mesmo cromossomo) e lista vazia | T002 | `[//]` | `tests/test_segmentos.py` | 🟢 | `[X]` |
| T005 | Testes da projeção da tabela: chaves esperadas, `extensao_mb` derivada de `fim - inicio`, `cm` cru (sem formatar) e imutabilidade da entrada | T004 | - | `tests/test_segmentos.py` | 🟢 | `[X]` |
| T006 | Teste de contrato HTTP: seção entre a distribuição e a lista, contador, 11 linhas da fixture, sete colunas e `href="#regiao-N"` batendo com o `id` da faixa; sem região, nenhuma seção | T003 | `[//]` | `tests/test_contrato_dos_segmentos.py` | 🟢 | `[X]` |
| T007 | Teste da chave `indice` em `projetar_regioes`: 1..N na ordem da lista, e o mesmo `indice` aparecendo no `id` da faixa do ideograma | T002 | `[//]` | `tests/test_contrato_das_regioes.py` | 🟢 | `[X]` |

## Fase 3, Núcleo

| ID | Descrição | Dependências | Paralelismo | Arquivo alvo | Confidência | Status |
|----|-----------|--------------|-------------|--------------|-------------|--------|
| T008 | Implementar `segmentos_das_regioes`: achatar as regiões, gravar o `regiao_indice` antes de ordenar e ordenar por cromossomo natural, início e kit | T004 | - | `src/core/segmentos.py` | 🟢 | `[X]` |
| T009 | Implementar `projetar_segmentos`: derivar `extensao_mb` e montar os dicionários da linha | T005 | - | `src/application/segmentos.py` | 🟢 | `[X]` |
| T010 | Acrescentar a chave `indice` (1-based) a `projetar_regioes` | T007 | - | `src/application/regioes.py` | 🟢 | `[X]` |

## Fase 4, Integração

| ID | Descrição | Dependências | Paralelismo | Arquivo alvo | Confidência | Status |
|----|-----------|--------------|-------------|--------------|-------------|--------|
| T011 | Projetar os segmentos no fluxo da análise e passar `segmentos` ao template | T008, T009 | - | `src/app.py` | 🟢 | `[X]` |
| T012 | Marcar a seção "Detalhamento dos segmentos compartilhados" **depois da distribuição e antes da lista**, com título, contador, toolbar (busca e filtro por cromossomo), tabela de sete colunas e controles de paginação | T011 | - | `src/templates/index.html` | 🟢 | `[X]` |
| T013 | Emitir `id="regiao-N"` na faixa do ideograma, a partir do `indice` da região | T012 | - | `src/templates/index.html` | 🟢 | `[X]` |
| T014 | Estilos da tabela: badge do cromossomo, toolbar, cabeçalho, zebra sutil, `:target` da faixa, `scroll-margin` e regra de impressão que mostra as linhas paginadas | - | `[//]` | `src/assets/app.css` | 🟢 | `[X]` |
| T015 | Script da tabela: busca normalizada, filtro por cromossomo, contador, paginação 10/20/30 com anterior/próxima, clique na linha (exceto no botão de copiar) e copiar com retorno "copiado" | T013 | - | `src/templates/index.html` | 🟡 | `[X]` |

## Fase 5, Polimento

| ID | Descrição | Dependências | Paralelismo | Arquivo alvo | Confidência | Status |
|----|-----------|--------------|-------------|--------------|-------------|--------|
| T016 | Medir `SHA_DA_TELA` e registrar em `evidence/SHA_DA_TELA.md` (esperado: inalterado, 52.497 bytes) | T015 | `[//]` | `_reversa_forward/058-detalhamento-dos-segmentos/evidence/SHA_DA_TELA.md` | 🟢 | `[X]` |
| T017 | Gerar `regression-watch.md` com os itens da ordem, do par linha↔faixa, do estado vazio e da impressão | T015 | `[//]` | `_reversa_forward/058-detalhamento-dos-segmentos/regression-watch.md` | 🟢 | `[X]` |
| T018 | Atualizar o item "Regiões compartilhadas" do README com a tabela e registrar as medições em `evidence/medicoes.md` | T015 | `[//]` | `README.md` | 🟢 | `[X]` |

## Notas de execução

## Histórico de alterações

| Data | Alteração | Autor |
|------|-----------|-------|
| 2026-11-11 | Versão inicial gerada por `/reversa-to-do` | reversa |

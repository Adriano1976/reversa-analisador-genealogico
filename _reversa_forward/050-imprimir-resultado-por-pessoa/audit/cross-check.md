# Cross-check: impressão do resultado por pessoa

> Identificador: `050-imprimir-resultado-por-pessoa`
> Data: `2026-10-26`
> Artefatos analisados: [`requirements.md`](../requirements.md) · [`roadmap.md`](../roadmap.md) ·
> [`actions.md`](../actions.md) — mais [`interfaces/bloco-de-impressao.md`](../interfaces/bloco-de-impressao.md),
> [`data-delta.md`](../data-delta.md) e [`investigation.md`](../investigation.md) como apoio.
>
> **Auditoria estritamente leitora: nenhum dos artefatos analisados foi alterado.**

## 1. Resumo

| Severidade | Findings |
|------------|----------|
| CRITICAL | 0 |
| HIGH | 1 |
| MEDIUM | 7 |
| LOW | 5 |
| **Total** | **13** |

**Veredito: revisão necessária antes do código.** Há um requisito `Must` que o plano decidiu não
cumprir por impossibilidade técnica (`A001`) e ele precisa de decisão humana. Os demais achados são de
cobertura, atomicidade e redação — baratos de fechar, mas todos no caminho da execução.

## 2. Findings

| ID | Severidade | Eixo | Descrição | Onde está |
|----|------------|------|-----------|-----------|
| A001 | **HIGH** | Cobertura | O `RF-04` (`Must`) pede "todas as páginas trazem… página N de M"; a `D-07` declara que a numeração não é implementável e entrega só a origem repetida. O requisito continua `Must` e não é cumprido | `requirements.md#5` (RF-04) · `roadmap.md#3` (D-07) · `roadmap.md#9` (R-01) |
| A002 | MEDIUM | Consistência | O `RF-11` promete que a tela vazia muda "apenas no script declarado", mas a `T001` insere `#area-de-impressao` no `<body>` de toda página — inclusive a tela de entrada vazia, que não tem cartão | `requirements.md#5` (RF-11) · `actions.md` (T001) |
| A003 | MEDIUM | Sanidade do actions | Seis ações `[//]` compartilham arquivo alvo: `T007`, `T008` e `T009` usam `src/assets/app.css`; `T010`, `T011` e `T012` usam `src/templates/index.html`. O critério do projeto é que tarefa `[//]` não compartilhe alvo | `actions.md`, Fase 3 |
| A004 | MEDIUM | Sanidade do actions | `T017` e `T018` não são atômicas por agente: exigem quatro navegadores, julgamento visual e um PDF salvo à mão — o oposto de "concluída num turno, sem feedback humano no meio" | `actions.md`, Fase 5 · `onboarding.md#9` |
| A005 | MEDIUM | Cobertura | A `D-07` (rodapé com a origem em toda folha) tem folha de estilo (`T009`) e desenho de dados ("script (no clone)"), mas **nenhuma ação cria o nó** `.origem-da-impressao`: `T011` monta o clone e não o nomeia | `roadmap.md#D-07` · `actions.md` (T009, T011) · `data-delta.md#4` |
| A006 | MEDIUM | Consistência | O critério do `RF-02` diz "não contém o nome de nenhuma outra pessoa da mesma análise", mas o cartão imprime, por definição, nomes de outras pessoas: o caminho genealógico, a tabela de evidências por salto e os homônimos. O cenário Gherkin diz outra coisa — "não contém o **cartão** de nenhuma outra pessoa" | `requirements.md#5` (RF-02) × `#7` |
| A007 | MEDIUM | Coerência com o legado | O critério de pronto exige **"Paridade 100 %"**, mas o registro mais recente do projeto (`049`, 2026-10-26) declara **30 divergências pré-existentes em `ancestral`**, medidas num checkout limpo do `HEAD`. Como critério absoluto, é inalcançável por esta feature | `roadmap.md#10` · `_reversa_forward/049-sistema-de-log/actions.md` |
| A008 | MEDIUM | Cobertura | Cinco requisitos (`RF-03`, `RF-06`, `RF-09`, `RF-10`, `RF-11`) e uma escolha de produto — o momento da impressão preenchido pelo navegador (`RN-02`) — não têm linha de decisão no roadmap; vivem na prosa, no anexo de interface e nas ações | `roadmap.md#3` · `interfaces/bloco-de-impressao.md#2.3` e `#4` |
| A009 | LOW | Consistência | Tensões internas de redação no requirements: (a) `RN-02` pede o momento da impressão e `RN-03` exige o mesmo documento, mas o carimbo de hora os diferencia; (b) `RN-05` diz que nada é reordenado e `RN-07` manda o desenho para o fim — a ordem do resultado não muda, a do documento sim | `requirements.md#4` (RN-02, RN-03, RN-05, RN-07) |
| A010 | LOW | Cobertura | A `D-12` ("nenhuma dependência nova, nenhuma linha de Python") não tem ação de verificação: `T016` roda a suíte, mas não confere `requirements.txt` nem `src/**.py` | `roadmap.md#3` (D-12) · `actions.md` (T016) |
| A011 | LOW | Cobertura | O risco `R-07` (crescimento do HTML de resultados) não tem ação de medição; `T015` mede apenas a tela vazia (`SHA_DA_TELA`) | `roadmap.md#9` (R-07) · `actions.md` (T015) |
| A012 | LOW | Consistência | Terminologia oscila nos três documentos: "desenho" e "diagrama" para o mesmo objeto; "documento" com dois sentidos (a página HTML e o produto da impressão). O glossário do requirements define "documento" e "folha", mas o roadmap não segue a distinção | `requirements.md#2` (glossário), `RN-07` e `RF-05` · `roadmap.md#1` e `#D-06` |
| A013 | LOW | Consistência | A `D-09` diz que os tokens do tema claro são redeclarados "sob o contêiner de impressão"; a interface manda `body.imprimindo`. Dois seletores diferentes para a mesma intenção | `roadmap.md#D-09` · `interfaces/bloco-de-impressao.md#4` |

## 3. Detalhe do HIGH

### A001 — o `RF-04` é `Must` e não é cumprido

**Impacto.** O requisito promete três coisas: a identificação no topo, a origem em **todas** as
páginas e a posição "página N de M". A terceira é fisicamente impossível no modelo de impressão dos
quatro navegadores-alvo: caixas de margem de `@page` não são implementadas, e o documento não tem
acesso ao número da página durante a impressão. A `D-07` escolheu não prometer o que não pode entregar,
mas **não reescreveu o requisito** — e um `Must` não cumprido contamina o critério de pronto e a
matriz SPEC↔CODE que o `/reversa-sync` vai gerar.

O risco de seguir assim é o pior dos mundos: a feature entrega tudo o que prometeu, e o relatório
final precisa declarar um requisito em aberto que ninguém decidiu fechar.

**Sugestão de correção (humano).** Rodar `/reversa-clarify` para reescrever o `RF-04` — por exemplo,
"a identificação aparece no topo e a origem em toda folha; a numeração de página fica com o diálogo
do navegador" — ou editar o `requirements.md` à mão. Se a decisão for aceitar a divergência, ela
precisa estar escrita **no próprio requisito**, não só no roadmap. Depois, esta auditoria pode rodar
de novo ou o ciclo segue para `/reversa-coding`.

## 4. O que passou

### Cobertura

- Os **11 requisitos funcionais** têm decisão ou ação correspondente (com as ressalvas `A001` e `A008`).
- As **13 decisões** do roadmap têm ação correspondente, exceto a `D-12`, que é ausência deliberada e
  não tem verificação (`A010`).
- Os **12 cenários Gherkin** têm decisão ou ação correspondente.
- RNFs com ação associada: Papel → `T009`; Prontidão → `T010`; Desempenho → `T012`; Privacidade →
  `T003`/`T015`; Testabilidade → `T004`–`T006`; Compatibilidade → `T017`; Paridade → `T016`; Suíte →
  `T016`; Acessibilidade → `T002`/`T014`.

### Consistência

- Toda dependência em `T001`–`T018` aponta para IDs existentes na própria tabela.
- Todos os `RF-`, `RN-`, `D-` e `R-` citados existem nos documentos que os definem.
- `interfaces/bloco-de-impressao.md` é citado no `roadmap.md#7` e consumido pelas ações.
- `data-delta.md` não contradiz o roadmap: os dois afirmam delta de DOM/folha e nenhum dado de domínio.
- Os valores de `SHA_DA_TELA` citados (46.477 bytes, `5fc0b929…`) batem com
  `tests/test_icone_de_atalho.py#L189`.
- As datas dos três documentos coincidem (`2026-10-26`).

### Coerência com o legado

- Nenhuma decisão contradiz regra 🟢 do `_reversa_sdd/domain.md`: `BR-D-41`/`BR-D-42`/`BR-D-65` são
  preservadas, `BR-D-66` (diagrama só com caminho) é respeitada pela `D-06`, e a ordem de apresentação
  não é tocada.
- A ausência de auditoria para imprimir é coerente com a `RN-04` da feature 049, que audita apenas
  ações de servidor.
- A `D-08` (identificação pela referência `chave__rótulo.ext`) alinha a folha à mesma chave de
  conteúdo usada pela trilha de auditoria, em vez de divergir dela.
- Os componentes citados existem no lugar indicado: `architecture.md#1` e `#3`,
  `src/app.py#L566-L576`, `src/assets/app.css#L10-L66`, `src/templates/index.html#L2022` e
  `#L1979-L1989`, e `_reversa_sdd/parity/harness.py#L191`.

### Sanidade do actions

- Não há ciclo de dependência: o grafo `T001`–`T018` é acíclico, e a maior cadeia tem 9 ações
  (`T003 → T010 → T011 → T012 → T014 → T015 → T016 → T017 → T018`).
- Nenhuma ação de "configurar IDE", "rodar lint" ou "abrir PR" foi inserida.
- Os IDs são sequenciais e não reciclados.
- A cobertura requisito ↔ ação foi verificada por **conteúdo**, não por citação de ID: o template de
  `actions.md` não tem coluna para o requisito, então a rastreabilidade depende da leitura — não é
  achado, é a natureza do artefato.

## 5. Histórico de alterações

| Data | Alteração | Autor |
|------|-----------|-------|
| 2026-10-26 | Auditoria gerada por `/reversa-audit` | reversa |
| 2026-10-26 | Consolidação: achados verificados mantidos e acrescentados os de cobertura e consistência desta passagem | reversa |

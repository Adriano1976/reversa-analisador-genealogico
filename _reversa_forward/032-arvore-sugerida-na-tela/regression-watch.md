# Regression Watch: árvore sugerida na tela

> Identificador: `032-arvore-sugerida-na-tela`
> Data: `2026-10-19`
> Fonte dos itens: seção "Modificadas" de `legacy-impact.md`

## Itens de vigilância

| ID | Origem (arquivo, seção) | Regra esperada após a mudança | Tipo de verificação | Sinal de violação |
|----|--------------------------|-------------------------------|---------------------|-------------------|
| W001 | `_reversa_forward/032-arvore-sugerida-na-tela/requirements.md` §4.4; `legacy-impact.md#4-modificadas` | Os códigos da sugestão são os da `029` — `HIATO_NAO_POSITIVO` e `SEM_MRCA_ESTIMADO` —, sem sinônimos na tela | `presença` | Um código novo aparecer para a mesma condição (por exemplo `SEM_GERACOES_A_SUGERIR`), dando dois nomes ao mesmo fato |

## Observações (sem peso de regressão)

- **O-01 — a tela não copia o grafo.** `resumo_da_sugestao` é O(1) e não tem acesso ao grafo; um
  teste com espião em `arvore_sugerida` falha se alguém "simplificar" chamando a cirurgia. É a
  garantia de que 142 cartões não copiam a estrutura da árvore.
- **O-02 — o `linkStyle` indexa por posição.** A aresta rompida é a última ligação de propósito; o
  teste fixa o índice. Reordenar as arestas manda o vermelho tracejado para a aresta errada, em
  silêncio.
- **O-03 — o bloco aparece fechado.** O resumo fica no título; o desenho carrega no `toggle`, pelo
  handler genérico que já existia (`index.html:1253-1263`). O JavaScript não foi tocado.
- **O-04 — o emissor é injetado, não importado.** `core/` não importa `reporting/` (ADR-34). Sem a
  dependência, o cartão mostra o resumo e não o desenho — e há um teste para esse caminho.
- **O-05 — a ausência só é explicada em conflito.** Cartão validado ou inconclusivo não ganha frase.
  Se uma extração futura encontrar a frase nesses cartões, é regressão de decisão (§9 da `032`).

## Histórico de re-extrações

> Preenchido pelo agente reverso quando `/reversa` rodar novamente.

| Data | Item | Resultado | Observação |
|------|------|-----------|------------|
| — | — | — | Nenhuma re-extração executada desde a criação deste arquivo |

## Arquivadas

| ID | Motivo | Data |
|----|--------|------|
| — | Nenhum item arquivado | — |

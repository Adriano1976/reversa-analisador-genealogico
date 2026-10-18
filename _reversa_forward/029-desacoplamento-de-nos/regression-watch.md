# Regression Watch: desacoplamento de nós e gerações virtuais

> Identificador: `029-desacoplamento-de-nos`
> Data: `2026-10-18`
> Fonte dos itens: seção "Modificadas" de `legacy-impact.md`

## Itens de vigilância

| ID | Origem (arquivo, seção) | Regra esperada após a mudança | Tipo de verificação | Sinal de violação |
|----|--------------------------|-------------------------------|---------------------|-------------------|
| W001 | `_reversa_sdd/addenda/028-validador-de-dados-dna.md`; `_reversa_forward/029-desacoplamento-de-nos/legacy-impact.md#4-modificadas` | `validar_arquivos` **sem** `incluir_documental` devolve exatamente as mesmas chaves de antes: `doador`, `comparacoes`, `resumo`, `ano_referencia`, `intervalo_de_geracao`, e cada comparação com `status`, `motivo`, `codigos`, `kit`, `cm`, `mrca_estimado`, `mrca_documentado`, `geracoes_documentais`, `comparacao_existente` | `presença` | Uma chave nova aparecer no retorno padrão (`documental`, `arvore` ou outra), ou uma chave antiga sumir |

## Observações (sem peso de regressão)

Itens 🟡/🔴 que não eram regra confirmada antes da feature. Não entram na tabela acima porque a
extração reversa nunca os confirmou como 🟢.

- **O-01 — `juncoes` (plural) é extensão de contrato.** O `requirements.md` §4.7 previa só
  `juncao`. Com dois lados acusados e famílias de junção distintas há duas junções a cortar; sem o
  campo plural, `DOIS_LADOS_ACUSADOS` prometeria uma divisão que o contrato não representaria.
  Registrado em `actions.md#notas-de-execucao` (item 1).
- **O-02 — deduplicação da junção compartilhada.** Dois lados acusados podem apontar para a mesma
  aresta (dois filhos do mesmo ancestral). A lista é deduplicada e a cadeia, nesse caso, é única,
  com o aviso `DOIS_LADOS_ACUSADOS` explicando por quê. Achado durante os testes, não previsto no
  plano (`actions.md#notas-de-execucao`, item 2).
- **O-03 — `SUGESTAO_INSUFICIENTE` é heurística declarada.** A conferência usa a faixa 12–70 da
  `028`, mas o **gatilho** do aviso é uma escolha desta feature: quando o cM pede menos gerações do
  que a janela exigiria, a sugestão sai marcada como insuficiente em vez de ser inflada ou cortada.
  Se a extração futura confirmar outro critério, este é o ponto a revisar.
- **O-04 — o grafo sugerido não é árvore para os leitores existentes.** Os nós virtuais não
  existem em `people`/`families`, então `get_parents` e `documentary_relationship` devolveriam `[]`
  em silêncio para eles. É limitação declarada (D-11 do `roadmap.md`) e documentada na docstring do
  módulo e no `data-delta.md`.
- **O-05 — `incluir_documental` também devolve `arvore`.** O `roadmap.md` (D-04) previa só a chave
  `documental`; a árvore entrou junto porque `validar_arquivos` não a devolvia e a fachada teria de
  reparsear o GEDCOM. As duas chaves saem do mesmo opt-in (`actions.md#notas-de-execucao`, item 3).

## Histórico de re-extrações

> Preenchido pelo agente reverso quando `/reversa` rodar novamente. Cada linha deve trazer a data
> da re-extração, o ID do item e o resultado da verificação (verde/amarelo/vermelho).

| Data | Item | Resultado | Observação |
|------|------|-----------|------------|
| — | — | — | Nenhuma re-extração executada desde a criação deste arquivo |

## Arquivadas

| ID | Motivo | Data |
|----|--------|------|
| — | Nenhum item arquivado | — |

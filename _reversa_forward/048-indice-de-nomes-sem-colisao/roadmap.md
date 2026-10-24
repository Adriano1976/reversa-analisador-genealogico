# Roadmap: índice de nomes sem colisão entre árvores

> Identificador: `048-indice-de-nomes-sem-colisao`
> Data: `2026-10-24`
> Requirements: `_reversa_forward/048-indice-de-nomes-sem-colisao/requirements.md`
> Confidência: 🟢 CONFIRMADO, 🟡 INFERIDO, 🔴 LACUNA

## 1. Resumo da abordagem

O índice de nomes deixa de ser **estado de módulo**. Ele passa a ser preso ao **grafo da
árvore** que o originou, exatamente como `fichas_da_pessoa._indice_de_filhos` e o memo de
`build_ged_indexes` (feature 047) já fazem. Com isso a chave de invalidação **desaparece**:
não há mais o que colidir, porque não há cache compartilhado entre árvores.

A alternativa registrada em 2026-10-10 — "acrescentar à chave algo derivado do conteúdo" — foi
avaliada e **descartada**: derivar a chave dos nomes custa a mesma varredura que construir o
índice (~0,9 s por 35 mil pessoas), e derivá-la só dos xrefs colide em reexportações que mantêm
os identificadores e mudam os dados. Prender o índice à árvore resolve as duas coisas de uma vez.

## 2. Princípios aplicados

| Princípio | Como a feature se relaciona | Status |
|-----------|------------------------------|--------|
| I. Dados reais nunca no versionamento | Testes com árvores sintéticas de 3 pessoas | respeita |
| II. Comportamento observável preservado | Dossiê idêntico: conjunto, ordem, `exact_count`, fichas | respeita |
| III. Nenhuma mudança sem teste | O teste da colisão (`TT-20`) vem antes da correção | respeita |
| IV. Arestas tipadas | Não percorre grafo | respeita |
| V. Toda suposição cita a fonte | O custo de 0,9 s vem do `data-dictionary.md`; a colisão, do experimento de 2026-10-10 | respeita |

## 3. Decisões técnicas

| ID | Decisão | Justificativa | Alternativas descartadas | Confidência |
|----|---------|----------------|--------------------------|-------------|
| D-01 | O índice é preso ao **grafo** da árvore | É o objeto que vive com a árvore e já é usado por dois memos; não há chave, logo não há colisão | chave derivada do conteúdo (custa a mesma varredura); chave de todos os xrefs (colide em reexportação) | 🟢 |
| D-02 | `_INDICE_DE_NOMES` e `_chave_de` são **removidos** | Enquanto houver estado de módulo, a classe do defeito pode voltar por outro caminho | manter o global como fallback (reintroduz o risco e a corrida) | 🟢 |
| D-03 | A função tolera árvore sem grafo (`arvore[2] is None`) | Árvores degeneradas aparecem em teste e em sonda; sem a guarda, `setattr` estoura | exigir grafo (quebra consumidores de teste) | 🟢 |
| D-04 | O arquivo de testes do cache é **reescrito** | `test_indice_de_nomes_do_documental.py` lê o módulo por AST e exige a tupla `_INDICE_DE_NOMES`; ele deixa de fazer sentido | adaptar os testes antigos (mediriam uma implementação que não existe) | 🟢 |
| D-05 | O custo é medido por contagem, não por relógio | O parse desta máquina variou de 41 s a 92 s; contagem de `get_name` é estável | cronometrar (ruído) | 🟢 |

## 4. Premissas

Nenhuma. O `requirements.md` está com zero marcadores `[DÚVIDA]`.

## 5. Delta arquitetural

| Componente | Arquivo de origem no legado | Tipo de mudança | Resumo |
|------------|------------------------------|-----------------|--------|
| `homonimos.py` (índice de nomes) | `_reversa_sdd/architecture.md#3` | `regra-alterada` | O índice deixa de ser cache de módulo e passa a viver preso ao grafo da árvore |
| `CACHE_DE_NOMES` (ERD) | `_reversa_sdd/erd-complete.md#7` | `delta-de-dados` | Muda de "memória de módulo" para "memória da árvore", como `CHILD_TO_FAMILY` |
| Quadro "onde o dado vive" | `_reversa_sdd/architecture.md#4` | `delta-de-dados` | A memória de módulo cai de 2 para 1 estrutura (`CACHE_DE_ARVORES`); o índice passa para a linha da requisição/árvore |
| Cache de nomes (design) | `_reversa_sdd/busca-caminho/design.md#riscos-e-lacunas` | `regra-removida` | A lacuna `L-24` deixa de existir: não há mais chave para colidir |

## 6. Delta no modelo de dados

- Resumo: nenhum campo persistido. A estrutura `CACHE_DE_NOMES` **muda de dono**: deixa de ser
  estado de processo e passa a morrer com a árvore.
- Detalhe completo em: `_reversa_forward/048-indice-de-nomes-sem-colisao/data-delta.md`

## 7. Delta de contratos externos

n/a — nenhuma rota, formulário, status ou HTML muda.

## 8. Plano de migração

1. Não há migração: a estrutura antiga morre com o processo, e a nova nasce vazia com a árvore.
2. Sem a feature 047 ligada, cada requisição reconstrói o índice (como já acontece hoje, porque a
   chave muda a cada árvore nova).

## 9. Riscos e mitigações

| Risco | Impacto | Probabilidade | Mitigação |
|-------|---------|---------------|-----------|
| Custo de ~0,9 s por requisição quando o cache da árvore está desligado | baixo | certa | é o comportamento de hoje: a chave muda a cada árvore, então o índice já é reconstruído |
| Teste antigo do cache quebrar de forma silenciosa | médio | alta | o arquivo é reescrito na mesma ação; nenhum teste fica órfão |
| Árvore sem grafo em teste/sonda | baixo | média | guarda `arvore[2] is None` constrói sem memo (D-03) |
| Reintroduzir ordem dependente de `set` no dossiê | médio | baixa | a construção do mapa não muda; `L-25` fica fora do escopo |
| Alguém "otimizar" de volta para cache de módulo | alto | baixa | teste estrutural proíbe `_INDICE_DE_NOMES` no módulo |

## 10. Critério de pronto

- [ ] Duas árvores de mesmo tamanho e mesmos xrefs extremos não compartilham o índice
- [ ] O módulo não tem `_INDICE_DE_NOMES` nem `_chave_de`
- [ ] O dossiê de homônimos é idêntico antes/depois (conjunto, ordem, `exact_count`, fichas)
- [ ] O índice é construído uma vez por árvore (contagem de `get_name`)
- [ ] Suíte completa verde
- [ ] Todas as ações do `actions.md` marcadas `[X]`
- [ ] `regression-watch.md` gerado
- [ ] Adendo da 048 escrito no `/reversa-sync`

## 11. Histórico de alterações

| Data | Alteração | Autor |
|------|-----------|-------|
| 2026-10-24 | Versão inicial gerada por `/reversa-plan` | reversa |

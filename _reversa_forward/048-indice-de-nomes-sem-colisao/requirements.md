# Requirements: índice de nomes sem colisão entre árvores

> Identificador: `048-indice-de-nomes-sem-colisao`
> Data: `2026-10-24`
> Pasta da extração reversa: `_reversa_sdd/`
> Confidência: 🟢 CONFIRMADO, 🟡 INFERIDO, 🔴 LACUNA / DÚVIDA

## 1. Resumo executivo

O índice de nomes do módulo de homônimos é um cache **de módulo**, invalidado por uma chave
derivada do conteúdo: `(quantidade de pessoas, primeiro xref, último xref)`. Duas árvores com o
mesmo número de pessoas e os mesmos xrefs extremos produzem a **mesma chave**, e a segunda passa a
usar o índice da primeira — o dossiê de homônimos cita `xref` que não existe na árvore carregada e
degrada em silêncio para `"Sem Nome"`.

O defeito foi **confirmado por execução** em 2026-10-10, e a correção foi aceita e agendada. Esta
feature a executa: o índice deixa de ser estado de módulo e passa a viver preso à árvore que o
originou, de modo que duas árvores distintas não tenham como compartilhá-lo.

## 2. Contexto a partir do legado

| Fonte | Trecho relevante | Confidência |
|-------|------------------|-------------|
| `_reversa_sdd/domain.md#7-lacunas` | `L-24`: a chave pode não invalidar entre duas árvores; "é a lacuna de maior risco aberta nesta rodada" | 🟢 |
| `_reversa_sdd/architecture.md#7` | Dívida #1, gravidade **Alta**: colisão possível da chave do cache de nomes | 🟢 |
| `_reversa_sdd/busca-caminho/design.md#riscos-e-lacunas` | O experimento de 2026-10-10: duas árvores de 4 pessoas com a mesma chave `(4, '@I1@', '@I9@')`; o dossiê da segunda citou `@I2@`, que não existe nela | 🟢 |
| `_reversa_sdd/busca-caminho/tasks.md` | `TT-20` já escrito: duas árvores de mesmo tamanho **não** podem compartilhar o índice; "teste que hoje falharia" | 🟢 |
| `_reversa_sdd/flowcharts/busca-caminho.md#13` | O mecanismo completo e o gatilho: a colisão depende só da contagem, não do conteúdo | 🟢 |
| `_reversa_sdd/gaps.md#3-lacunas-moderadas` | Correção aceita em 2026-10-10, agendada para depois do Passo 4 (concluído em 2026-10-13) | 🟢 |
| `_reversa_sdd/addenda/047-cache-dos-indices-da-arvore.md` | Precedente direto: o índice de matching passou a viver preso ao grafo da árvore, sem chave derivada de conteúdo | 🟢 |

## 3. Personas e cenários de uso

| Persona | Objetivo | Cenário-chave |
|---------|----------|---------------|
| Operador do analisador | Confiar no dossiê de homônimos de qualquer árvore que abrir | Abre duas árvores de tamanhos parecidos na mesma sessão e o dossiê da segunda não cita ninguém da primeira |
| Quem reimplementa o sistema | Não repetir a classe de defeito | Lê a regra e não recria cache de módulo com chave derivada de conteúdo |

## 4. Regras de negócio novas ou alteradas

1. **RN-01 — Duas árvores nunca compartilham o índice de nomes.** O índice de uma árvore só pode ser lido por consultas feitas sobre **aquela** árvore. 🟢
   - Origem no legado: `_reversa_sdd/domain.md#7-lacunas` (`L-24`); `_reversa_sdd/busca-caminho/design.md#riscos-e-lacunas`
   - Tipo: nova

2. **RN-02 — O índice morre com a árvore.** Ele deixa de ser estado de módulo e passa a ter o mesmo tempo de vida da árvore que o originou; nenhuma estrutura derivada de uma árvore sobrevive à requisição que a carregou, a menos que a própria árvore sobreviva (feature 047). 🟢
   - Origem no legado: `_reversa_sdd/addenda/bug-BUG-20261021-7O7V-v001.md#o-que-passa-a-valer` (regra 2: derivado nasce e morre com a árvore, sem chave que possa colidir)
   - Tipo: alterada

3. **RN-03 — O dossiê de homônimos não muda de resultado.** Para a mesma árvore, o conjunto de registros, a ordem, a contagem (`exact_count`) e os campos das fichas são idênticos aos de hoje. 🟢
   - Origem no legado: princípio II de `.reversa/principles.md`
   - Tipo: nova

4. **RN-04 — O custo não pode voltar ao de antes do cache.** O índice é construído **no máximo uma vez por árvore**, não uma vez por nome consultado: sem isso, a análise de DNA real pagaria ~0,9 s por nome distinto (71 no arquivo real). 🟢
   - Origem no legado: `_reversa_sdd/data-dictionary.md` (o cache existe porque a varredura de 35 mil pessoas custa ~0,9 s)
   - Tipo: nova

## 5. Requisitos Funcionais

| ID | Requisito | Prioridade | Critério de aceite | Confidência |
|----|-----------|------------|--------------------|-------------|
| RF-01 | O índice de nomes é construído no máximo uma vez por árvore e devolvido igual nas consultas seguintes | Must | Duas chamadas devolvem o **mesmo objeto**, e a segunda não percorre as pessoas | 🟢 |
| RF-02 | Duas árvores distintas com a mesma contagem e os mesmos xrefs extremos não compartilham o índice | Must | O dossiê da segunda árvore não cita nenhum `xref` da primeira; o `TT-20` passa | 🟢 |
| RF-03 | Nenhum estado de módulo guarda o índice entre requisições | Must | `_INDICE_DE_NOMES` e `_chave_de` deixam de existir; o módulo não tem variável global de cache | 🟢 |
| RF-04 | O dossiê de homônimos mantém conjunto, ordem, contagem e fichas | Must | Comparação antes/depois com a mesma árvore e o mesmo nome | 🟢 |
| RF-05 | O índice é construído uma única vez por consulta composta | Must | Analisar 71 nomes distintos na mesma árvore constrói o índice **uma** vez | 🟢 |

## 6. Requisitos Não Funcionais

| Tipo | Requisito | Evidência ou justificativa | Confidência |
|------|-----------|----------------------------|-------------|
| Desempenho | A construção do índice não pode passar de uma por árvore; o custo por consulta é O(1) depois da primeira | `_reversa_sdd/data-dictionary.md`: ~0,9 s por varredura de 35 mil pessoas | 🟢 |
| Memória | A solução não pode reter a árvore anterior para comparar identidade | Reter `people` da árvore passada custaria centenas de MB; a feature 047 mostrou que uma árvore custa ~337 MB | 🟢 |
| Paridade | Mesmo dossiê, mesma ordem, mesmos textos para a mesma árvore | Princípio II | 🟢 |
| Concorrência | Duas threads em árvores diferentes não podem ler o índice uma da outra | A corrida foi fechada em 2026-10-24 com a troca atômica do par; qualquer solução nova tem de manter isso | 🟢 |
| Determinismo | A ordem dos registros no dossiê não pode depender de iteração de `set` | Defeito já registrado em `L-25`, não pode ser reintroduzido aqui | 🟢 |
| Testes | Fixtures sintéticas; nunca arquivo real de `src/uploads/` | Princípio I | 🟢 |

## 7. Critérios de Aceitação

```gherkin
Cenário: Duas árvores de mesmo tamanho não compartilham o índice
  Dado que a árvore A tem 3 pessoas com xrefs @I1@, @I2@ e @I9@
  E a árvore B tem 3 pessoas com xrefs @I1@, @I4@ e @I9@
  Quando o dossiê de homônimos é consultado na árvore B
  Então nenhum xref exclusivo da árvore A aparece no resultado
  E a ficha de cada registro é montada com dados da árvore B

Cenário: O índice é construído uma vez por árvore
  Dado que a árvore já foi consultada uma vez
  Quando o mesmo nome é consultado de novo
  Então o índice é o mesmo objeto
  E nenhuma pessoa é percorrida para reconstruí-lo

Cenário: O resultado do dossiê continua idêntico
  Dado uma árvore e um nome com homônimos
  Quando o dossiê é consultado antes e depois da mudança
  Então o conjunto de ids, a ordem, o exact_count e as fichas são os mesmos
```

## 8. Prioridade MoSCoW

| Item | MoSCoW | Justificativa |
|------|--------|---------------|
| RF-02 | Must | É o defeito em si, confirmado por execução |
| RF-03 | Must | Enquanto houver estado de módulo, a classe do defeito volta por outro caminho |
| RF-01 | Must | Sem o memo por árvore, o custo volta a 0,9 s por nome |
| RF-04 | Must | Correção que muda o dossiê não é correção, é mudança de comportamento |
| RF-05 | Should | Cobre o caminho composto da análise real |

## 9. Esclarecimentos

> Nenhuma sessão de dúvidas registrada ainda. Rode `/reversa-clarify` quando houver `[DÚVIDA]` pendente.

## 10. Lacunas

Nenhuma lacuna aberta. O defeito está confirmado por execução, a correção foi aceita em
2026-10-10 e o teste `TT-20` já está especificado.

## 11. Histórico de alterações

| Data | Alteração | Autor |
|------|-----------|-------|
| 2026-10-24 | Versão inicial gerada por `/reversa-requirements` | reversa |

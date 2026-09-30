# Perguntas para Validação — teste_reversa

> Re-extração de 2026-09-30. Substitui integralmente o `questions.md` de 2026-08-03.
> Nível **essencial**: apenas lacunas 🔴 que **bloqueiam a reimplementação fiel**.
> `answer_mode = "chat"` — pode responder aqui mesmo, numerando as respostas.

---

## Pergunta 1

**Contexto:** Unit `busca-caminho` — `find_ancestral_path` em `analisador-genealogico/reconstructed/path_search.py:144-178`. O teto `MAX_DEPTH = 20` (`:22`) limita **iterações de profundidade** do BFS bidirecional, não gerações: cada iteração expande um nível de um dos dois lados, alternadamente.
**Spec afetada:** [`_reversa_sdd/busca-caminho/design.md`], [`_reversa_sdd/busca-caminho/tasks.md`]
**Pergunta:** Uma árvore real com mais de ~20 níveis de ascendência faz a conexão direta falhar **em silêncio**, caindo para a busca indireta (que pode achar um laço por afinidade sem significado genealógico). Isso é aceitável, ou o corte deveria produzir uma mensagem explícita ao usuário de que o limite foi atingido?
**Impacto:** Se o corte precisa ser visível, `requirements.md` ganha um requisito de sinalização e o `design.md` precisa distinguir "não existe caminho" de "limite atingido" — hoje os dois casos são indistinguíveis no retorno `(None, None)`.

**Resposta:** <!-- preencha aqui -->

---

## Pergunta 2

**Contexto:** Unit `busca-caminho` — `get_spouses` em `analisador-genealogico/reconstructed/path_search.py:64-88`. A varredura global de `families` (fallback) só roda **se `spouse_ids` ficou vazio** (`:79-80`). Se a pessoa tem algum `FAMS` que resolve e outro que não, o fallback **nunca roda** e o cônjuge da segunda família desaparece do resultado.
**Spec afetada:** [`_reversa_sdd/busca-caminho/design.md`]
**Pergunta:** Essa condicional é intencional (economia de varredura) ou acidente? Em árvores com `FAMS` parcialmente resolvidos, cônjuges legítimos podem faltar — e isso muda o resultado da busca indireta e das pontes matrimoniais.
**Impacto:** Se for acidente, a reimplementação deve varrer sempre (ou varrer quando `FAMS` não cobrir todas as famílias). Se for intencional, precisa ficar registrado como contrato, não como detalhe.

**Resposta:** <!-- preencha aqui -->

---

## Pergunta 3

**Contexto:** Unit `upload-gedcom` — `reconstructed/domain.py` declara `Family` (`:61`), `GenealogyGraph` (`:74`) e `DNAGroup` (`:106`), e **nenhuma das três é instanciada em qualquer caminho de produção**. O fluxo real usa os dicionários globais e os registros do `ged4py` diretamente.
**Spec afetada:** [`_reversa_sdd/upload-gedcom/requirements.md`], [`_reversa_sdd/upload-gedcom/tasks.md`]
**Pergunta:** Essas três entidades são **arquitetura abandonada no meio do caminho** (devem ser removidas) ou **preparação para uso futuro** (devem ser implementadas e adotadas pelo fluxo)?
**Impacto:** Se removidas, a reimplementação fica menor e mais honesta. Se adotadas, o modelo de domínio muda de "dicionários globais" para objetos — o que afeta as três units, não só esta.

**Resposta:** <!-- preencha aqui -->

---

## Pergunta 4

**Contexto:** Unit `analise-dna` — `match_candidates` em `analisador-genealogico/reconstructed/dna_analysis.py:233-333`. O desempate do melhor candidato (`:274-277`) compara três critérios, mas empates exatos no terceiro são resolvidos pela **ordem de iteração de um `set`** (`:262`). Essa ordem depende de `PYTHONHASHSEED` e **não é determinística entre processos**.
**Spec afetada:** [`_reversa_sdd/analise-dna/design.md`]
**Pergunta:** Um matching não reprodutível entre execuções é aceitável, ou o desempate precisa de um critério final determinístico (ex.: menor `xref_id`)?
**Impacto:** Se precisa ser determinístico, entra um requisito não funcional de reprodutibilidade e `tasks.md` ganha uma tarefa. Hoje o risco está registrado como `L-13` mas não há decisão.

**Resposta:** <!-- preencha aqui -->

---

## Pergunta 5

**Contexto:** Unit `analise-dna` — a tabela `SHARED_CM_DATA` (`dna_analysis.py:30-40`) define 9 faixas de cM que **se sobrepõem até 4 vezes**: 50 cM casa 4 faixas simultaneamente; 300 cM casa 3. Nenhuma faixa cita origem, versão ou fonte. O README menciona o Shared cM Project, mas sem referência à versão nem aos dados.
**Spec afetada:** [`_reversa_sdd/analise-dna/requirements.md`]
**Pergunta:** Qual é a fonte e a versão dessas faixas? A sobreposição é intencional (para mostrar todas as relações plausíveis) ou é consequência de as faixas terem sido escritas à mão?
**Impacto:** Se houver fonte citável, ela entra na spec e a tabela ganha rastreabilidade. Se for escrita à mão, a spec deve declarar que os números são heurísticos — o que muda a classificação de 🟢 para 🟡 em `RF-10`.

**Resposta:** <!-- preencha aqui -->

---

## Pergunta 6

**Contexto:** Unit `analise-dna` — o relaxamento do limiar de Jaccard de **0,5 para 0,33** quando `cM ≥ 150` e o prenome não é genérico (`dna_analysis.py:299-301`). A decisão de manter foi confirmada por você em 2026-08-03 (`questions.md` antigo, pergunta 4), mas **o valor 0,33 em si** não tem justificativa documentada em nenhum lugar.
**Spec afetada:** [`_reversa_sdd/analise-dna/design.md`]
**Pergunta:** O valor 0,33 foi **calibrado** contra dados reais (e nesse caso existe alguma medição de quantos falsos positivos ele introduz?), ou foi um **chute** que funcionou na prática?
**Impacto:** Se calibrado, a medição entra na spec como evidência. Se foi chute, a spec deve marcar o número como 🟡 ajustável, e a reimplementação pode tratá-lo como parâmetro configurável em vez de literal.

**Resposta:** <!-- preencha aqui -->

---

## Perguntas já decididas — NÃO são pendências

As quatro respostas de 2026-08-03 foram **verificadas contra o código atual** e continuam valendo. Nenhuma precisa ser refeita:

| Assunto | Resposta vigente | Verificação no código |
| --- | --- | --- |
| Regras de aceitação do matching são definitivas | Preservar com fidelidade | `dna_analysis.py:305-320` — 6 ramos intactos 🟢 |
| Homônimos usam o 1º ID | Aceitável, já validado | `path_search.py:479` — `ids[0]` 🟢 |
| Upload sem validação de extensão/tamanho | Limitação aceita para uso local | `app.py:29` — sem validação por decisão 🟢 |
| Relaxamento de Jaccard 0,5 → 0,33 com cM ≥ 150 | Intencional | `dna_analysis.py:299-301` 🟢 |

> A **Pergunta 6** acima não reabre a decisão de manter o relaxamento — ela pergunta pela **origem do número**, que é informação nova.

---

*Gerado pelo Reversa-Reviewer em 2026-09-30 (re-extração).*

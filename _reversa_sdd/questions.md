# Perguntas para Validação — teste_reversa

> Re-extração de 2026-09-30. Substitui integralmente o `questions.md` de 2026-08-03.
> Nível **essencial**: apenas lacunas 🔴 que **bloqueiam a reimplementação fiel**.
> `answer_mode = "chat"` — pode responder aqui mesmo, numerando as respostas.
>
> **STATUS: 5 de 6 respondidas e aplicadas às specs em 2026-09-30. Apenas a Pergunta 6 segue em aberto.**

---

## Pergunta 1 — ✅ Respondida

**Contexto:** Unit `busca-caminho` — `find_ancestral_path` em `analisador-genealogico/reconstructed/path_search.py:144-178`. O teto `MAX_DEPTH = 20` (`:22`) limita **iterações de profundidade** do BFS bidirecional, não gerações: cada iteração expande um nível de um dos dois lados, alternadamente.
**Spec afetada:** [`_reversa_sdd/busca-caminho/design.md`], [`_reversa_sdd/busca-caminho/tasks.md`]
**Pergunta:** Uma árvore real com mais de ~20 níveis de ascendência faz a conexão direta falhar **em silêncio**, caindo para a busca indireta (que pode achar um laço por afinidade sem significado genealógico). Isso é aceitável, ou o corte deveria produzir uma mensagem explícita ao usuário de que o limite foi atingido?
**Impacto:** Se o corte precisa ser visível, `requirements.md` ganha um requisito de sinalização e o `design.md` precisa distinguir "não existe caminho" de "limite atingido" — hoje os dois casos são indistinguíveis no retorno `(None, None)`.

**Resposta:** ✅ **Aceitável — preservar fidelidade ao legado.** O corte continua silencioso, sem novo requisito e sem sinalização ao usuário.
**Aplicado em:** `busca-caminho/design.md` → seção "Riscos e Lacunas" (bloco RESOLVIDO); `busca-caminho/tasks.md` → **L-03** marcada resolvida. Nenhuma mudança em `requirements.md`, porque a decisão foi **não** acrescentar requisito.

---

## Pergunta 2 — ✅ Respondida

**Contexto:** Unit `busca-caminho` — `get_spouses` em `analisador-genealogico/reconstructed/path_search.py:64-88`. A varredura global de `families` (fallback) só roda **se `spouse_ids` ficou vazio** (`:79-80`). Se a pessoa tem algum `FAMS` que resolve e outro que não, o fallback **nunca roda** e o cônjuge da segunda família desaparece do resultado.
**Spec afetada:** [`_reversa_sdd/busca-caminho/design.md`]
**Pergunta:** Essa condicional é intencional (economia de varredura) ou acidente? Em árvores com `FAMS` parcialmente resolvidos, cônjuges legítimos podem faltar — e isso muda o resultado da busca indireta e das pontes matrimoniais.
**Impacto:** Se for acidente, a reimplementação deve varrer sempre (ou varrer quando `FAMS` não cobrir todas as famílias). Se for intencional, precisa ficar registrado como contrato, não como detalhe.

**Resposta:** ✅ **Intencional — documentar como contrato.** A varredura global é **fallback total, não complemento**. A reimplementação **não** deve torná-la complementar, sob pena de mudar o resultado.
**Aplicado em:** `busca-caminho/design.md` → tabela de símbolos (nota "contrato explícito") + bloco RESOLVIDO em "Riscos e Lacunas"; `busca-caminho/tasks.md` → **L-02** marcada resolvida.

---

## Pergunta 3 — ✅ Respondida

**Contexto:** Unit `upload-gedcom` — `reconstructed/domain.py` declara `Family` (`:61`), `GenealogyGraph` (`:74`) e `DNAGroup` (`:106`), e **nenhuma das três é instanciada em qualquer caminho de produção**. O fluxo real usa os dicionários globais e os registros do `ged4py` diretamente.
**Spec afetada:** [`_reversa_sdd/upload-gedcom/requirements.md`], [`_reversa_sdd/upload-gedcom/tasks.md`]
**Pergunta:** Essas três entidades são **arquitetura abandonada no meio do caminho** (devem ser removidas) ou **preparação para uso futuro** (devem ser implementadas e adotadas pelo fluxo)?
**Impacto:** Se removidas, a reimplementação fica menor e mais honesta. Se adotadas, o modelo de domínio muda de "dicionários globais" para objetos — o que afeta as três units, não só esta.

**Resposta:** ✅ **Arquitetura abandonada — remover.**
**Aplicado em — e esta resposta foi além das specs, mexeu no código:**
- `analisador-genealogico/reconstructed/domain.py` → as três classes **removidas**; módulo caiu de **115 para 84 linhas** e hoje contém apenas `strip_bad_utf` e `demojibake`
- `analisador-genealogico/reconstructed/domain.py` → imports `dataclass` e `field` removidos (ficaram órfãos)
- `tests/test_domain.py` → **9 testes removidos** (os que exercitavam as classes extintas); o arquivo documenta a remoção. Suíte: **95 → 86 itens coletados**, 85 passando
- `_reversa_sdd/upload-gedcom/design.md` → bloco RESOLVIDO; `requirements.md` → rastreabilidade atualizada; `tasks.md` → **L-01 e L-11** marcadas resolvidas
- `_reversa_sdd/code-analysis.md`, `architecture.md`, `domain.md`, `inventory.md`, `.reversa/context/{surface,modules}.json` → contagens e entidades atualizadas

---

## Pergunta 4 — ✅ Respondida

**Contexto:** Unit `analise-dna` — `match_candidates` em `analisador-genealogico/reconstructed/dna_analysis.py:233-333`. O desempate do melhor candidato (`:274-277`) compara três critérios, mas empates exatos no terceiro são resolvidos pela **ordem de iteração de um `set`** (`:262`). Essa ordem depende de `PYTHONHASHSEED` e **não é determinística entre processos**.
**Spec afetada:** [`_reversa_sdd/analise-dna/design.md`]
**Pergunta:** Um matching não reprodutível entre execuções é aceitável, ou o desempate precisa de um critério final determinístico (ex.: menor `xref_id`)?
**Impacto:** Se precisa ser determinístico, entra um requisito não funcional de reprodutibilidade e `tasks.md` ganha uma tarefa. Hoje o risco está registrado como `L-13` mas não há decisão.

**Resposta:** ✅ **Precisa ser determinístico.** Critério final sugerido: menor `xref_id` entre os empatados.
**Aplicado em:**
- `analise-dna/requirements.md` → novo **`RF-14`** + requisito não funcional de **Reprodutibilidade**
- `analise-dna/design.md` → tabela de decisões ganhou a linha do desempate não-determinístico; lacuna `L-13` marcada resolvida
- `analise-dna/tasks.md` → nova seção **"Correções decididas pelo usuário em 2026-09-30"** com **`T-19`**; teste **`TT-13`** já existia
- ⚠️ **É a única divergência deliberada do legado em toda a re-extração.** As demais tarefas preservam comportamento; esta corrige.

---

## Pergunta 5 — ✅ Respondida

**Contexto:** Unit `analise-dna` — a tabela `SHARED_CM_DATA` (`dna_analysis.py:30-40`) define 9 faixas de cM que **se sobrepõem até 4 vezes**: 50 cM casa 4 faixas simultaneamente; 300 cM casa 3. Nenhuma faixa cita origem, versão ou fonte. O README menciona o Shared cM Project, mas sem referência à versão nem aos dados.
**Spec afetada:** [`_reversa_sdd/analise-dna/requirements.md`]
**Pergunta:** Qual é a fonte e a versão dessas faixas? A sobreposição é intencional (para mostrar todas as relações plausíveis) ou é consequência de as faixas terem sido escritas à mão?
**Impacto:** Se houver fonte citável, ela entra na spec e a tabela ganha rastreabilidade. Se for escrita à mão, a spec deve declarar que os números são heurísticos — o que muda a classificação de 🟢 para 🟡 em `RF-10`.

**Resposta:** ✅ **Escritas à mão — declarar como heurística.** A sobreposição de até 4× é consequência do método, não do Shared cM Project.
**Aplicado em:**
- `analise-dna/requirements.md` → novo **`RF-10a`** (heurísticas sem fonte verificável, tratáveis como parâmetro). O `RF-10` **permanece 🟢** quanto à *mecânica* (devolver lista) — o que mudou de status foi a **autoridade dos números**, não o comportamento.
- `analise-dna/design.md` → tabela de decisões + lacuna `L-07` marcada resolvida
- `analise-dna/tasks.md` → **`T-20`** na seção de correções decididas

---

## Pergunta 6 — ⏳ EM ABERTO

**Contexto:** Unit `analise-dna` — o relaxamento do limiar de Jaccard de **0,5 para 0,33** quando `cM ≥ 150` e o prenome não é genérico (`dna_analysis.py:299-301`). A decisão de manter foi confirmada por você em 2026-08-03 (`questions.md` antigo, pergunta 4), mas **o valor 0,33 em si** não tem justificativa documentada em nenhum lugar.
**Spec afetada:** [`_reversa_sdd/analise-dna/design.md`]
**Pergunta:** O valor 0,33 foi **calibrado** contra dados reais (e nesse caso existe alguma medição de quantos falsos positivos ele introduz?), ou foi um **chute** que funcionou na prática?
**Impacto:** Se calibrado, a medição entra na spec como evidência. Se foi chute, a spec deve marcar o número como 🟡 ajustável, e a reimplementação pode tratá-lo como parâmetro configurável em vez de literal.

**Resposta:** ⏳ **CALIBRADO — o usuário indicou ter a medição, mas ela ainda não foi fornecida.**
**Pendência:** a medição (quantos falsos positivos o 0,33 introduz, e contra que conjunto de dados foi calibrado) precisa ser colada aqui para eu registrar como evidência em `analise-dna/design.md` e fechar a lacuna `L-14`.

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

*Gerado pelo Reversa-Reviewer em 2026-09-30 (re-extração). Respostas processadas em 2026-09-30.*

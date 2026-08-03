# Perguntas para Validação — teste_reversa

> Gerado pelo Revisor em 2026-08-03
> Nível essencial — apenas 🔴 críticos que bloqueiam reimplementação.
> Responda cada pergunta e me avise quando terminar.

---

## Pergunta 1

**Contexto:** Unit `analise-dna` — regras de aceitação do matching (regras A/B/C/D) em `analisador-genealogico/app.py:759-790`.
**Spec afetada:** [`_reversa_sdd/analise-dna/requirements.md`], [`_reversa_sdd/analise-dna/design.md`]
**Pergunta:** As regras A/B/C/D de aceitação do matching difuso (combinações de dado genérico/não-genérico, interseção de sobrenomes, thresholds de Jaccard e score) são o comportamento definitivo esperado, ou algumas são heurísticas ad hoc que podem ser simplificadas numa reimplementação?
**Impacto:** Se forem definitivas, devem ser preservadas com fidelidade. Se forem heurísticas, podem ser simplificadas mantendo o espírito.

**Resposta:** <!-- preencha aqui -->

---

## Pergunta 2

**Contexto:** Unit `busca-caminho` — `find_person_by_name` em `analisador-genealogico/app.py:208-211`; uso do primeiro ID em `app.py:853`.
**Spec afetada:** [`_reversa_sdd/busca-caminho/requirements.md`], [`_reversa_sdd/busca-caminho/design.md`]
**Pergunta:** Em caso de homônimos (duas pessoas com o mesmo nome no GEDCOM), o sistema usa o primeiro ID encontrado. Essa é uma política aceitável ou é preciso desambiguação explícita (ex.: pedir confirmação ao usuário)?
**Impacto:** Se aceitável, mantém-se como está. Se não, a spec precisa de requisito de desambiguação.

**Resposta:** <!-- preencha aqui -->

---

## Pergunta 3

**Contexto:** Unit `upload-gedcom` — `app.py:569` salva o arquivo com o nome original; `app.py:15-18` define `UPLOAD_FOLDER`.
**Spec afetada:** [`_reversa_sdd/upload-gedcom/requirements.md`], [`_reversa_sdd/upload-gedcom/design.md`]
**Pergunta:** Não há validação de extensão/tamanho dos arquivos enviados e arquivos com o mesmo nome são sobrescritos. Essa é uma limitação conhecida aceita para uso local, ou deve haver política de segurança (extensões permitidas, tamanho máximo, nomes únicos)?
**Impacto:** Se aceita, documenta-se como limitação. Se não, a spec deve incluir os requisitos de segurança.

**Resposta:** <!-- preencha aqui -->

---

## Pergunta 4

**Contexto:** Unit `analise-dna` — relaxamento de Jaccard em `app.py:751-753` (threshold 0.5→0.33 para cM ≥ 150 e dado não-genérico).
**Spec afetada:** [`_reversa_sdd/analise-dna/design.md`]
**Pergunta:** O relaxamento do threshold de Jaccard para matches de cM alto (0.5 → 0.33) é intencional para capturar parentes próximos com nomes divergentes, ou pode gerar falsos positivos que deveriam ser evitados?
**Impacto:** Se intencional, mantém-se. Se não, o threshold deve ser mais rígido.

**Resposta:** <!-- preencha aqui -->

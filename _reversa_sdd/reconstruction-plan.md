# Reconstruction Plan — teste_reversa

**Fonte:** original
**Stack:** Python 3 / Flask (Jinja2, Bootstrap 5) · ged4py · networkx · pandas · thefuzz · python-Levenshtein · pyvis · matplotlib · gunicorn
**Gerado em:** 2026-08-07 (Reconstructor)
**Status:** 4 tarefas | 3 concluídas | 1 pendente

---

## Alertas de pré-voo

> Revise estes pontos antes de iniciar. Gaps marcados com ⚠️ bloqueiam a tarefa associada. As 4 lacunas principais do `questions.md` foram **respondidas e resolvidas**; as demais permanecem como decisão de implementação documentada.

- 🔴 **LACUNA (analise-dna):** detecção de ID por regex `[A-Z]{2}\d{7}` — cobertura entre exportadores não comprovada. Decisão: preservar o regex conforme `analise-dna/design.md`. (Tarefa 4)
- 🔴 **LACUNA (busca-caminho):** famílias adotivas/complexas — `find_ancestral_path` assume caminho por pais. Decisão: manter o comportamento da spec (sem antepassados fora da linhagem por pais). (Tarefa 3)
- 🔴 **LACUNA (upload-gedcom):** colisão de nomes em `uploads/` (sobrescrita) e estado global sem tratamento de concorrência. Decisão: limitação aceita para uso local, conforme resposta à Pergunta 3. (Tarefa 2)
- 🟢 **Resolvido (Regras A/B/C/D)** — resposta Pergunta 1: são comportamentos definitivos, preservar com fidelidade. (Tarefa 4)
- 🟢 **Resolvido (Homônimos)** — resposta Pergunta 2: manter uso do 1º ID. (Tarefa 3)
- 🟢 **Resolvido (Upload sem validação)** — resposta Pergunta 3: sem política de segurança, documenta-se limitação. (Tarefa 2)
- 🟢 **Resolvido (Relaxamento Jaccard 0.5→0.33)** — resposta Pergunta 4: intencional, manter. (Tarefa 4)
- 🟡 **Código morto:** `HARD_MIN=92` / `GIVEN_MIN=90` (app.py:653-654) não são usados; limiares reais são literais nas regras A/B/C/D. Não implementar como limiar principal, mas preservar o comportamento real. (Tarefa 4)

---

## Tarefas

### Tarefa 01 — Entidades de Domínio
**Status:** done
**Lê:** `_reversa_sdd/domain.md`
**Constrói:** representação em memória das entidades `PERSON`, `FAMILIA` e `DNA_MATCH` (dicionários + `networkx.MultiGraph`), sem persistência.
**Pronto quando:** Estruturas de dados capazes de representar pessoas (xref_id, nome, sub-registros FAMC/FAMS), famílias (husb, wife, chil) e matches de DNA (chave de grupo, cM, nome casado) implementadas com limpeza de mojibake (`strip_bad_utf`, `demojibake`).

---

### Tarefa 02 — Upload GEDCOM
**Status:** done
**Lê:** `_reversa_sdd/upload-gedcom/requirements.md`, `_reversa_sdd/upload-gedcom/design.md`, `_reversa_sdd/upload-gedcom/tasks.md`, `_reversa_sdd/dependencies.md`
**Constrói:** rota de upload + parsing de `.ged` (com `ged4py`), geração de nome formatado (`get_name`), limpeza de mojibake, e construção do grafo pessoa↔família (`build_graph`).
**Pronto quando:** Arquivo `.ged` enviado (sem validação de extensão/tamanho — limitação aceita) é salvo em `UPLOAD_FOLDER` (colisão sobrescreve), parseado em `PERSON`/`FAMILIA` e o grafo família é construído em memória; estados GEDCOM carregado/sem GEDCOM corretos.
**Alerta:** colisão de nomes e estado global sem concorrência — aceito como limitação.

---

### Tarefa 03 — Busca de Caminho
**Status:** done
**Lê:** `_reversa_sdd/busca-caminho/requirements.md`, `_reversa_sdd/busca-caminho/design.md`, `_reversa_sdd/busca-caminho/tasks.md`, `_reversa_sdd/dependencies.md`
**Constrói:** resolução de pessoa por nome (`find_person_by_name`, usa 1º ID em homônimos), conexão direta por ancestral comum (sob `FAMC`/`get_parents`, prof. máx. 20) e fallback de conexão indirecta por afinidade (BFS, máx. 40 hops).
**Pronto quando:** dada a pessoa-raiz e um match, o caminho ascendente+descendente é montado; fallback indireto corretamente; homônimos usam o 1º ID; limites de busca respeitados.
**Alerta:** política de homônimos resolvida (1º ID); famílias adotivas/complexas assumem caminho por pais.

---

### Tarefa 04 — Análise de DNA
**Status:** pending
**Lê:** `analise-dna/requirements.md`, `analise-dna/design.md`, `analise-dna/tasks.md`, `dependencies.md`
**Constrói:** carregamento/agregação de segmentos de `.csv`, matching difuso viral (`0.55×token_sort + 0.25×partial + 0.20×given + InterBonus`), filtro anti-falso-positivo, intersecção adaptativa, regras A/B/C/D de aceitação, relaxamento de Jaccard (0.5→0.33 p/ cM≥150 e não-genérico), equivalente de grafia/abreviações, tabela de relação por faixa de cM, e cálculo de caminho até a raiz.
**Pronto quando:** matches agregados por chave (nome + ID/email), soma de cM e matching viral com regras A/B/C/D preservadas com fidelidade; relação por faixa de cM; `skipped_matches` listados como descartados.
**Alerta:** regras A/B/C/D definitivas (Pergunta 1); relaxamento de cM alto intencional (Pergunta 4); regex de ID `[A-Z]{2}\d{7}` mantida; código morto HARD_MIN/GIVEN_MIN não ganha papel real.

---

## Próximos passos

- Camada de API: **não aplicável** (Flask renderiza server-side, sem canal REST de negócio).
- Fluxos de usuário: **não aplicável** (uso local single-user sem RBAC), conforme nível essencial.
- Máquinas de estado: **não aplicável** (sem `state-machines.md`).
- Schema de banco: **não aplicável** (estado 100% em memória, sem persistência).

Para iniciar, diga **INICIAR** ou **execute a tarefa 1**.
# Relatório de Confiança — teste_reversa

> Gerado pelo Revisor em 2026-08-03
> Nível de documentação: **Essencial**

---

## Resumo Geral

| Nível | Quantidade | Percentual |
|-------|-----------|------------|
| 🟢 CONFIRMADO | 182 | 86,3% |
| 🟡 INFERIDO | 12 | 5,6% |
| 🔴 LACUNA | 17 | 8,1% |
| **Total** | **211** | 100% |

**Confiança geral:** **89,1%** (soma de 🟢 + metade dos 🟡)

---

## Por Spec

| Spec | 🟢 | 🟡 | 🔴 | Confiança |
|------|----|----|-----|-----------|
| `analise-dna/` (requirements+design+tasks) | 71 | 6 | 5 | 91,5% |
| `busca-caminho/` (requirements+design+tasks) | 58 | 3 | 4 | 92,3% |
| `upload-gedcom/` (requirements+design+tasks) | 53 | 3 | 8 | 87,5% |

---

## Lacunas Pendentes (🔴)

Itens que permaneceram sem confirmação e precisam de validação humana — detalhados em `questions.md`.

### analise-dna
- **Regras A/B/C/D de aceitação do matching** — complexas, sem base de teste; exigem confirmação do comportamento definitivo (`questions.md#1`).
- **Relaxamento de Jaccard (0.5→0.33 p/ cM alto)** — duvidoso; pode gerar falsos positivos (`questions.md#4`).
- **Detecção de ID por regex `[A-Z]{2}\d{7}`** — cobertura entre exportadores não comprovada.

### busca-caminho
- **Uso do 1º ID em homônimos** — política de desambiguação indefinida (`questions.md#2`).
- **Famílias adotivas/complexas** — `find_ancestral_path` assume caminho por pais.

### upload-gedcom
- **Sem validação de extensão/tamanho** — política de upload indefinida (`questions.md#3`).
- **Colisão de nomes em `uploads/`** — sobrescrita sem tratamento.
- **Estado global** — concorrência entre requisições não tratada.

---

## Achados da Revisão

### Reclassificações / Correções

| De | Para | Afirmação | Evidência |
|----|------|-----------|-----------|
| 🟢 | 🟡 | Constantes `HARD_MIN=92` e `GIVEN_MIN=90` como "limiares de matching" | São **código morto** — definidas em `app.py:653-654` mas nunca usadas; limiares reais são literais nas regras A/B/C/D. |

### Consistência verificada
- Referências de linha das specs conferidas contra o código (`get_name` :42, `load_gedcom` :175, `build_graph` :184, `find_indirect_path` :281/288, `find_ancestral_path` :297/301, `HARD_MIN`/`GIVEN_MIN` :653-654, rotas `index` :558-582). 🟢
- Unidades interna e cruzadamente consistentes; sem contradições entre units. ✅

---

## Recomendações

- [ ] **Priorizar**: responder `questions.md` (4 perguntas) — em especial a #1 (regras A/B/C/D), que mais afeta a fielidade do matching.
- [ ] **Remover código morto** `HARD_MIN`/`GIVEN_MIN` numa futura refatoração (ou usá-lo como fonte de literal) — consideração p/ implementação.
- [ ] **Adicionar testes** para matching e regras A/B/C/D — hoje condicionais com 🔴.
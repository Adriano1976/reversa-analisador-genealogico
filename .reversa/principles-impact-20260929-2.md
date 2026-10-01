# Relatório de impacto dos princípios — 2026-09-29 (execução 2)

> Gerado por `/reversa-principles` (modo `atualizar`, segunda execução do dia).
> Fonte: `.reversa/principles.md`, princípios **IV** e **V**, adicionados nesta execução.
> A execução 1 do mesmo dia gerou `.reversa/principles-impact-20260929.md`, que trata dos
> princípios I, II e III. Este arquivo recebeu o sufixo `-2` para não sobrescrever aquele,
> conforme a regra de nunca reescrever relatório de impacto antigo.
> **Este relatório apenas sugere. Aplicar as sugestões é decisão do humano.**

Operação aplicada nesta execução: **adicionar IV e V**. Os princípios I, II e III não foram
alterados, por decisão do usuário.

---

## 1. `.reversa/templates/requirements-template.md`

### 1.1. Seção 4: declarar os tipos de aresta que a regra percorre (princípio IV)

**Âncora.** Seção `## 4. Regras de negócio novas ou alteradas`, itens numerados, linhas 57-60.

**Texto atual.**
```
1. **RN-01:** <descrição> 🟢
   - Origem no legado: `_reversa_sdd/domain.md#<id>` (se aplicável)
   - Tipo: nova | alterada | removida
```

**Sugestão.** Acrescentar um campo obrigatório para regras que percorrem o grafo:
```
   - Arestas percorridas: filiação | casamento | ambas | não percorre o grafo
```
Regra que percorra o grafo sem declarar o campo é lacuna, não requisito.

---

### 1.2. Seção 4: declarar a fonte de todo número de domínio (princípio V)

**Âncora.** Mesma seção 4, itens numerados.

**Sugestão.** Acrescentar:
```
   - Fonte do valor numérico: <referência> (consultada em YYYY-MM-DD) | não há valor numérico
```

E na seção `## 6. Requisitos Não Funcionais`, mesma exigência para limiares numéricos:
```
| Tipo | Requisito | Fonte do valor | Evidência ou justificativa | Confidência |
```

---

### 1.3. Seção 7: cenário obrigatório de caminho misto (princípio IV)

**Âncora.** Seção `## 7. Critérios de Aceitação`, bloco `gherkin`, linhas 79-89.

**Sugestão.** Acrescentar após o bloco:
```
> Toda feature que altere travessia de grafo inclui um cenário com caminho que misture
> filiação e casamento, afirmando que o resultado identifica a conexão por afinidade.
```

---

## 2. `.reversa/templates/roadmap-template.md`

### 2.1. Seção 3: tipagem de aresta na decisão (princípio IV)

**Âncora.** Seção `## 3. Decisões técnicas`, tabela, linhas 38-41.

**Texto atual.**
```
| ID | Decisão | Justificativa | Alternativas descartadas | Confidência |
```

**Sugestão.** Acrescentar coluna, com `n/a` para decisões que não tocam o modelo do grafo:
```
| ID | Decisão | Tipagem de aresta | Justificativa | Alternativas descartadas | Confidência |
```
Valores: `filiação`, `casamento`, `ambas`, `n/a`.

---

### 2.2. Seção 3 e 5: citação da fonte nas decisões com número (princípio V)

**Âncora.** Seções `## 3. Decisões técnicas` e `## 5. Delta arquitetural`.

**Sugestão.** Regra textual logo abaixo da tabela da seção 3:
```
> Decisão que fixe valor de domínio (faixa de cM, profundidade de busca, limiar de score)
> cita a referência externa e a data de consulta na coluna de justificativa.
```

---

### 2.3. Seção 10: dois itens novos no critério de pronto

**Âncora.** Seção `## 10. Critério de pronto`, linhas 96-101.

**Sugestão.** Acrescentar:
```
- [ ] Existe teste com caminho que mistura filiação e casamento
- [ ] Todo número de domínio no código cita a fonte e a data de consulta
```

---

## 3. `.reversa/templates/actions-template.md`

### 3.1. Fase 2: teste de caminho misto

**Âncora.** Seção `## Fase 2, Testes`, tabela, linhas 40-44.

**Sugestão.** Acrescentar ação-padrão para features que mexem no grafo:
```
| T0NN | Teste com caminho misto (filiação + casamento), afirmando que a afinidade é marcada | T0MM | `[//]` | `tests/` | 🟢 | `[ ]` |
```

---

### 3.2. Fase 3: declarar o tipo de aresta na travessia

**Âncora.** Seção `## Fase 3, Núcleo`, tabela, linhas 46-53.

**Sugestão.** Ação obrigatória quando a tarefa percorre o grafo:
```
| T0NN | Declarar o tipo de aresta percorrida na travessia | T0MM | - | `<módulo de busca>` | 🟢 | `[ ]` |
```

---

### 3.3. Fase 5: citação da fonte junto ao valor

**Âncora.** Seção `## Fase 5, Polimento`, tabela, linhas 63-70.

**Sugestão.** Acrescentar:
```
| T0NN | Citar a fonte e a data de consulta junto a cada constante de domínio | - | `[//]` | `analisador-genealogico/reconstructed/dna_analysis.py` | 🟢 | `[ ]` |
```

---

## 4. Violações já existentes que os princípios IV e V tornam acionáveis

Estas não são sugestões de template: são os pontos do código atual que passam a contrariar
princípio a partir de agora.

| Princípio | Onde | Situação |
|-----------|------|----------|
| IV | `analisador-genealogico/reconstructed/path_search.py` (`find_indirect_path`, `split_path_by_marriage`) | A busca indireta conta hops sem distinguir filiação de casamento, e apenas o primeiro par de cônjuges adjacentes é reconhecido |
| IV | `analisador-genealogico/reconstructed/upload.py:50-79` | O grafo é construído com um único tipo de aresta pessoa↔família |
| V | `analisador-genealogico/reconstructed/dna_analysis.py:31` (`SHARED_CM_DATA`) | Tabela de faixas de cM sem fonte citada no código; o Shared cM Project consta só no `README.md` |
| V | `_reversa_sdd/domain.md:72` | A própria extração registra a lacuna: "as garantias das faixas de cM não têm fonte citationada no código" |

---

## 5. Ação executada fora do escopo deste skill

Com autorização explícita do usuário nesta sessão, a linha abaixo foi acrescentada ao `.gitignore`
(linha 24), tornando verdadeira a afirmação do princípio I sobre `uploads/`:

```
uploads/
```

Verificado com `git check-ignore`: casa tanto `uploads/` quanto `analisador-genealogico/uploads/`.
Este skill não altera `.gitignore` por conta própria; a mudança foi pedida pelo usuário.

---

## 6. Templates não afetados

- `.reversa/templates/quality-template.md`: sem seção de princípios nem de valores de domínio.

## 7. Resumo

| Template | Sugestões | Princípios |
|----------|-----------|------------|
| `requirements-template.md` | 3 | IV, V |
| `roadmap-template.md` | 3 | IV, V |
| `actions-template.md` | 3 | IV, V |
| `quality-template.md` | 0 | — |

Total: **9 sugestões textuais**, nenhuma aplicada automaticamente.

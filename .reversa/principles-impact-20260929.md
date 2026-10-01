# Relatório de impacto dos princípios — 2026-09-29

> Gerado por `/reversa-principles` (modo `criar`).
> Fonte: `.reversa/principles.md` — princípios I, II e III.
> **Este relatório apenas sugere. Aplicar as sugestões é decisão do humano.**

Os templates abaixo foram lidos na íntegra. Nenhum foi alterado automaticamente.

---

## 1. `.reversa/templates/requirements-template.md`

### 1.1. Cabeçalho — declarar princípios aplicáveis

**Âncora.** Bloco de citação, linhas 15–18.

**Texto atual.**
```
> Identificador: `<NNN>-<short-name>`
> Data: `YYYY-MM-DD`
> Pasta da extração reversa: `_reversa_sdd/`
> Confidência: 🟢 CONFIRMADO, 🟡 INFERIDO, 🔴 LACUNA / DÚVIDA
```

**Sugestão.** Acrescentar uma linha:
```
> Princípios aplicáveis: `.reversa/principles.md` (I, II, III)
```

**Princípios.** I, II, III.

---

### 1.2. Seção 4 — separar refactor de mudança de comportamento

**Âncora.** Seção `## 4. Regras de negócio novas ou alteradas`, linha 59.

**Texto atual.**
```
   - Tipo: nova | alterada | removida
```

**Sugestão.** Ampliar o vocabulário e tornar o refactor rastreável:
```
   - Tipo: nova | alterada | removida | refactor-sem-mudanca-de-comportamento
   - Se tipo = refactor-sem-mudanca-de-comportamento:
     entradas e saídas de referência antes da mudança (ver princípio II)
```

**Princípio.** II.

---

### 1.3. Seção 5 — critério de aceite tem de ser automatizável

**Âncora.** Seção `## 5. Requisitos Funcionais`, coluna `Critério de aceite`, linhas 64–67.

**Texto atual.**
```
| ID | Requisito | Prioridade | Critério de aceite | Confidência |
| RF-01 | <descrição> | Must | <critério verificável> | 🟢 |
```

**Sugestão.** Tornar explícito que o critério precisa virar teste antes da implementação:
```
| ID | Requisito | Prioridade | Critério de aceite | Teste que o cobre | Confidência |
| RF-01 | <descrição> | Must | <critério verificável> | `tests/<arquivo>::<teste>` ou `novo` | 🟢 |
```

**Princípio.** III.

---

### 1.4. Seção 6 — nova subseção obrigatória "Dados de teste"

**Âncora.** Entre as seções 6 e 7 (após a tabela de Requisitos Não Funcionais, linha 75).

**Sugestão.** Inserir seção obrigatória:
```
## 6.1. Dados de teste (obrigatória quando a feature lê arquivo do usuário)

| Insumo do teste | Origem sintética | Arquivo real proibido? |
|-----------------|------------------|------------------------|
| <GEDCOM de exemplo> | `tests/fixtures/sample_gedcom.py` | sim |

- Nenhum arquivo de `uploads/`, nenhum GEDCOM real, nenhum CSV de DNA real,
  nenhum nome/e-mail/ID de kit real entra no repositório. (princípio I)
```

Se a feature não lê arquivo do usuário, registrar `n/a`.

**Princípio.** I.

---

### 1.5. Seção 7 — cenários de aceitação viram testes

**Âncora.** Seção `## 7. Critérios de Aceitação`, bloco `gherkin`, linhas 79–89.

**Sugestão.** Acrescentar após o bloco:
```
> Todo cenário acima é traduzido em teste automatizado na mesma feature.
> Cenário sem teste correspondente é lacuna, não critério de aceite. (princípio III)
```

**Princípio.** III.

---

## 2. `.reversa/templates/roadmap-template.md`

### 2.1. Seção 2 já cobre os princípios — apenas endurecer o status

**Âncora.** Seção `## 2. Princípios aplicados`, linhas 25–34. **Estrutura já existe; nenhuma seção nova é necessária.**

**Texto atual.**
```
| Princípio | Como a feature se relaciona | Status |
|-----------|------------------------------|--------|
| I. <título> | <observação> | respeita / conflita |
```

**Sugestão.** Acrescentar nota logo abaixo da tabela:
```
> Conflito com o princípio I (dados reais) ou III (teste antes da mudança)
> não é trade-off aceitável: bloqueia o roadmap até resolução.
```

**Princípios.** I, III.

---

### 2.2. Seção 3 — refactor exige paridade antes/depois

**Âncora.** Seção `## 3. Decisões técnicas`, linhas 38–41.

**Sugestão.** Acrescentar coluna:
```
| ID | Decisão | Justificativa | Alternativas descartadas | Paridade antes/depois | Confidência |
```
com valores `n/a` para features sem refactor, e para refactors:
```
comparação de saída executada: <comando> → <resultado>
```

**Princípio.** II.

---

### 2.3. Seção 10 — dois novos itens no critério de pronto

**Âncora.** Seção `## 10. Critério de pronto`, linhas 96–101.

**Texto atual.**
```
- [ ] Todas as ações do `actions.md` marcadas `[X]`
- [ ] `cross-check.md` (se executado) sem CRITICAL nem HIGH
- [ ] `regression-watch.md` gerado
- [ ] Re-extração reversa executada e sem regressão vermelha (recomendado, não obrigatório)
```

**Sugestão.** Acrescentar:
```
- [ ] Suíte completa verde (`py -3.14 -m pytest`, 50 passed)
- [ ] Nenhum dado real de DNA/GEDCOM versionado (`git status` sem `uploads/`)
- [ ] Refactors com paridade antes/depois registrada na seção 3
```

**Princípios.** I, II, III.

---

## 3. `.reversa/templates/actions-template.md`

### 3.1. Fase 2 deixa de ser opcional

**Âncora.** Seção `## Fase 2, Testes`, comentário da linha 40.

**Texto atual.**
```
<!-- Testes que precisam existir antes ou logo após o núcleo. Omitir se a equipe não pratica TDD. -->
```

**Sugestão.** Substituir por:
```
<!-- Fase obrigatória: todo comportamento alterado tem ação de teste associada,
     escrita antes da ação de código correspondente. Não omitir. (princípio III) -->
```

**Princípio.** III.

---

### 3.2. Fase 4 — par de ações para refactor

**Âncora.** Seção `## Fase 4, Integração`, linhas 55–61.

**Sugestão.** Para features com refactor, exigir o par:
```
| T0NN | Capturar saída de referência antes do refactor | T0MM | `[//]` | `<caminho do script de captura>` | 🟢 | `[ ]` |
| T0NN | Comparar saída pós-refactor com a de referência | T0NN | - | `<mesmo caminho>` | 🟢 | `[ ]` |
```
Divergência bloqueia a conclusão da tarefa de refactor.

**Princípio.** II.

---

### 3.3. Fase 5 — verificação de dados reais e suíte completa

**Âncora.** Seção `## Fase 5, Polimento`, linhas 63–70.

**Sugestão.** Acrescentar duas ações-padrão:
```
| T0NN | Verificar que nenhum dado real entrou no versionamento | - | `[//]` | `git status` | 🟢 | `[ ]` |
| T0NN | Rodar a suíte completa e registrar o resultado | T0MM | - | `tests/` | 🟢 | `[ ]` |
```

**Princípios.** I, III.

---

## 4. Templates não afetados

- `.reversa/templates/quality-template.md` — sem seção de princípios; nenhuma sugestão nesta rodada.

## 5. Resumo

| Template | Sugestões | Princípios |
|----------|-----------|------------|
| `requirements-template.md` | 5 | I, II, III |
| `roadmap-template.md` | 3 | I, II, III |
| `actions-template.md` | 3 | I, II, III |
| `quality-template.md` | 0 | — |

Total: **11 sugestões textuais**, nenhuma aplicada automaticamente.

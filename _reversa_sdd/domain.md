# Domínio de Negócio — analisador-genealogico

> Gerado pelo **Detective** em 2026-08-03
> Nível de documentação: **Essencial**
> Escala de confiança: 🟢 CONFIRMADO | 🟡 INFERIDO | 🔴 LACUNA

---

## 1. Glossário de Domínio

| Termo | Definição |
| --- | --- |
| **GEDCOM** | Formato de arquivo padronizado (.ged) para troca de árvores genealógicas. Define registros `INDI` (pessoa) e `FAM` (família). 🟢 |
| **INDI** | Registro de indivíduo; identificado por `xref_id` (ex.: `@I0001@`). Campo `FAMC` referencia a família onde é filho(a); `FAMS` as famílias onde é cônjuge. 🟢 |
| **FAM** | Registro de família; identificado por `xref_id` (ex.: `@F1@`). Campos `HUSB` (marido), `WIFE` (esposa) e `CHIL` (filhos). 🟢 |
| **DNA Match** | Pessoa do relatório CSV de parentes compartilhados (ex.: GEDmatch Ancestor Project) com valor de cM compartilhado. 🟢 |
| **cM (centiMorgan)** | Unidade de medida de recombinação genética; nível maior indica parentesco mais próximo. 🟢 |
| **Ancestral Comum / MRCA** | Pessoa ascendente mais recente compartilhada entre duas pessoas. Base da conexão direta. 🟢 |
| **Grupos de segmento** | Segmentos de DNA repetidos de um mesmo match; agregados e somados por cM. 🟢 |
| **Mojibake** | Caracteres corrompidos causados por encoding incorreto (ex.: Latin-1 lido como UTF-8) — comum em nomes portugueses. 🟢 |

---

## 2. Regras de Negócio Principais

### 2.1. Relação prevista por faixa de cM 🟢 CONFIRMADO
O valor total de cM (soma de segmentos de um mesmo match) é traduzido para relações prováveis via tabela `SHARED_CM_DATA`:

| Faixa de cM | Relação Prevista |
| --- | --- |
| 3300–3720 | Pai/Mãe ↔ Filho(a) |
| 2200–3400 | Irmãos completos |
| 1317–2312 | Avós/Netos, Tios/Tias ↔ Sobrinhos(as), Meios-irmãos |
| 553–1330 | Primos de 1º grau |
| 200–850 | Primos de 1º grau (1× removido), Meios-primos, Tios-avós ↔ Sobrinhos-netos |
| 46–515 | Primos de 2º grau |
| 30–350 | Primos de 2º grau (1× removido), Primos de 3º grau |
| 10–220 | Primos de 3º grau (1× removido), Primos de 4º grau |
| 0–110 | Primos de 4º/5º grau ou mais distantes |
**Observação:** cM `<= 0` ou não numérico retorna "Relação distante ou indeterminada". 🟢

### 2.2. Conexão genealogical por ancestral comum (direta) 🟡
Dada a pessoa raiz e um match, o sistema busca o **ancestral comum de menor profundidade** subindo apenas pelas conexões de pais (`FAMC`/`get_parents`). Se encontrado, monta o caminho ascendente + descendente entre as duas pessoas. O fallback é uma conexão **indireta** por afinidade (casamentos/cunhados) via BFS no grafo pessoa↔família.

### 2.3. Regras de namespace de nome (matching viral) 🟢
- **Limpeza de mojibake** (`strip_bad_utf`, `demojibake`): corrige encoding corrompido de acentos (ex.: `Ã§`→`ç`, `JoA�o`→`João`). 🟢
- **Score de matching difuso**: `0.55×token_sort + 0.25×partial + 0.20×given + InterBonus`. InterBonus = `8.0×intersecão de sobrenomes − 4.0×sobrenomes comuns`. 🟢
- **Filtro anti-falso-positivo**: se ambos têm sobrenomes e a intersecão é 0 (sem sufixo "salvador" como `filho`/`neto`), o candidato é **rejeitado**. 🟢
- **Intersecão mínima adaptativa**: primeiro nome genérico (ex.: `Maria`, `José`) com 2+ sobrenomes exige intersecão ≥ 2 sobrenomes. 🟡
- **Equivalentes de grafia**: `netto→neto`, `gouvea/gouvêa→gouveia`. 🟢
- **Abreviações**: prefixos de sobrenome (min. 3 chars) usados para matches abreviados/corrompidos. 🟢

### 2.4. Limites de busca 🟢
- Ancestral comum: profundidade máxima `20` níveis. 🟢
- Conexão indata (indirect): máximo `40` hops. 🟢

---

## 3. Regras de decisão e fluxo

| Ação de usuário | Regra de negócio implementada |
| --- | --- |
| **DNA Analysis** | Exige GEDCOM carregado + CSV + `root_name` encontrado no GEDCOM. Agrega segmentos por chave (nome + ID/email), soma cM, faz matching viral e calcula caminho até a raiz. 🟢 |
| **Path Search** | Recebe duas pessoas; tenta conexão direta (ancestral comum) e, se falhar, conexão indireta por afinidade. 🟢 |
| Sem parém de matemática encontrado | Match é listado como "descartado" em `skipped_matches` (auditoria visual). 🟢 |

---

## 4. Lacunas 🔴 (requerem validação humana)

- 🔴 **Histórico de decisões**: não há repositório Git no projeto — ADRs retrospectivos por commits não são possíveis.
- 🔴 **Tabela de cM**: as garantias das faixas de cM não têm fonte citationada no código (é implícito ao Shared cM Project do README).
- 🔴 **Sem autenticação/autorização**: sistema não possui RBAC — qualquer acesso via web possui todas funcionalidades.
- 🔴 **Delimitação de escopo do matching**: regras de aceitação (A/B/C/D) são complexas e silenciosas — comportamento de aparência não coberta por testes.

---

## 5. Resumo para o Reversa

- **Regras de negócio**: 8 identificadas (tabela cM, conexão direta/indireta, matching viral, anti-falso-positivo, intersecão adaptativa, limites de busca).
- **Máquinas de estado**: nenhuma entidade central com múltiplos status (sem geração de `state-machines.md` no nível essencial).
- **Permissões**: ausentes (sem RBAC; não gera `permissions.md`).
- **ADRs**: não aplicáveis neste nível/contexto (sem Git).
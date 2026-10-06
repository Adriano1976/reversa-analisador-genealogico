# ADR-09 — Remover as entidades decorativas do domínio

- **Status:** Aceito e **executado**
- **Data da decisão:** 2026-09-30 (resposta do usuário no `questions.md#pergunta-3`)
- **Commit(s):** `6a52d69` — "chore: remove entidades mortas de domain.py"
- **Confiança:** 🟢 CONFIRMADO

## Contexto

`domain.py` declarava três estruturas que **não eram instanciadas em nenhum ponto de produção**: a dataclass `Family`, a classe `GenealogyGraph` e a classe `DNAGroup`. Elas tinham aparência de modelo de domínio — e a extração anterior as havia descrito como parte da arquitetura. A pergunta que ficou aberta por semanas foi: **são preparação para uso futuro ou arquitetura abandonada?**

## Decisão

**Arquitetura abandonada — remover.** O usuário respondeu diretamente, e a remoção foi executada na mesma sessão.

## Evidência

- `_reversa_sdd/questions.md#pergunta-3` — resposta registrada.
- Commit `6a52d69`; `domain.py` passou de **115 para 84 linhas**; os imports `dataclass`/`field` saíram; **9 testes** foram removidos de `tests/test_domain.py`; a suíte passou de **95 para 86 itens** coletados.
- **Verificação no código de 2026-10-05:** nenhuma das três classes existe em `src/` (nem `dataclass` em `core/gedcom_state.py` ou `core/documentary_relationship.py`, que são hoje os módulos de estado e de parentesco).
- Antes da remoção, a verificação foi feita **por varredura**: as três eram decorativas, sem instanciação em produção.

## Justificativa

Código morto com nome de domínio é **pior do que código morto comum**: ele é lido como modelo, entra nas specs, é migrado para o alvo por engano e reaparece como requisito. A decisão humana de 2026-08-03 já havia fixado que as regras de negócio do legado são **definitivas** — e uma classe que ninguém instancia não é regra.

## Consequências

- ✅ **`L-01` e `L-11` fechadas** em `domain.md` da extração de 2026-09-30.
- ✅ **Efeito colateral saudável:** o estado do GEDCOM ficou com **uma** representação (`people`, `families`, `graph`, `child_to_family` em `core/gedcom_state.py`), e a entidade `Family` da tabela de dados é hoje **o registro FAM do ged4py**, não uma dataclass paralela.
- ⚠️ **Custo aceito:** 9 testes removidos. Eles testavam as classes removidas, e não comportamento de produção — mas a contagem da suíte caiu, e é preciso saber **por quê** ao comparar números entre extrações (86 → 175 itens depois, por outras razões).
- 🟢 **A escolha foi testada contra a alternativa oposta.** Este é o único caso em que uma decisão humana de 2026-09-30 **mudou o código**, e não apenas as specs — o que o torna o precedente de que a política de edição do legado (ADR-06) **funciona na prática**.

## Alternativas consideradas

- **Manter como preparação para uso futuro.** Descartada pelo usuário: não havia plano de uso, e a classe `Family` duplicava o que o `ged4py` já entrega.
- **Manter marcadas com aviso de "não usar".** Descartada: o repositório já tem o padrão de declarar legado em docstring (`cm_estimator`, ADR-19), mas ali **há** superfície de compatibilidade a preservar — aqui não havia **nenhum** consumidor, nem testes de terceiros.

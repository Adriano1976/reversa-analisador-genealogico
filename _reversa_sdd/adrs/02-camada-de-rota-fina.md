# ADR-02 — Camada de rota fina: o `app.py` deixa de conter regra de negócio

- **Status:** Aceito, **vigente e ampliado**
- **Data da decisão:** 2026-08-11
- **Commit(s):** `f51bac1` (feature `002-integrar-rota-app-modulos`)
- **Confiança:** 🟢 CONFIRMADO

## Contexto

Depois do ADR-01, a mesma regra existia **em dois lugares**: implementada nos módulos reconstruídos e **ainda inline na rota**. O defeito estrutural não era a duplicação de código, era a **divergência silenciosa** entre duas cópias da mesma decisão de negócio — corrigir uma não corrigia a outra.

## Decisão

Mover os módulos para um pacote interno e reduzir o `app.py` a uma **camada de rota fina**, que apenas lê a requisição, delega aos módulos e renderiza. `app.py` caiu de ~887 para ~70 linhas.

## Evidência

- `f51bac1` — "integrar módulos reconstruídos ao app Flask e reorganizar estrutura do projeto".
- Estado atual: `src/app.py` com **267 linhas**, e a contagem maior **não** contradiz a decisão — as linhas acrescentadas são de **infraestrutura de entrada** (teto de corpo, handler de 413, filtros de template, ancoragem do caminho de upload, guarda de instância única, bloco waitress), não de regra de negócio. Nenhuma das 118 regras catalogadas em `code-analysis.md` vive em `app.py`.

## Justificativa

Uma só autoridade por regra. A duplicação entre rota e módulo era a origem de regressões que reapareciam depois de corrigidas.

## Consequências

- **Consequência não óbvia, e que custou caro:** o `app.py` deixou de ser um oráculo utilizável. Como passou a **importar o próprio candidato**, usá-lo como referência de comportamento produziria **validação circular** (`RISK-002`). Foi isso que obrigou o congelamento do commit `e43ca22` (ADR-04).
- A fronteira "rota fina" precisa ser vigiada: `_guardar_upload` e `_resolver_caminho_armazenado` vivem em `app.py` e contêm **decisão de negócio** sobre o que pode ser gravado e lido. A decisão em si mora em `utils/validate.py` (módulo puro), e a rota só a orquestra — mas a fronteira é tênue e vale a ressalva.
- Surgiu o padrão de **superfície de compatibilidade** (`__all__` reexportando nomes históricos), que se repetiu em vários módulos após o ADR-11 e deve ser lido como custo deliberado, não como descuido.

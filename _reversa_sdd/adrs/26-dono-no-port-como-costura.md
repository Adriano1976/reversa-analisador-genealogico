# ADR-26 — O dono nas portas é costura, e não isolamento

- **Status:** Aceito e **vigente** — é a única decisão do projeto cujo objeto é **uma assinatura sem comportamento**
- **Data da decisão:** 2026-10-07
- **Commit(s):** `f875b7f` (abre o ciclo `007-dono-no-port-e-baseline`), `6a7c0d3`, `73d859a`
- **Confiança:** 🟢 CONFIRMADO

## Contexto

O `ADR-25` criou as portas. Naquele momento havia uma **assimetria**: `RepositorioDeArvores` já recebia `dono` em todos os métodos desde a feature 006, e `ArmazenamentoDeArquivos` e `CarregadorDeArvores` não. A assimetria era arbitrária, e o sistema continua a **não ter identidade alguma** (`permissions.md`): não há sessão, login, papel nem credencial.

A pergunta real não era "como isolar", e sim: **quando** acrescentar o parâmetro que o isolamento vai usar.

## Decisão

**Exigir `dono` em todos os métodos das três portas, sem implementar comportamento nenhum.**

1. `dono` é parâmetro **obrigatório** de `guardar`, `resolver`, `listar`, `aposentar`, `carregar` e dos dois métodos de `RepositorioDeArvores`.
2. É **último parâmetro posicional e sem valor padrão** — um padrão deixaria toda chamada passar sem o dono, e a Onda 3 não teria onde ancorar.
3. Chega **por chamada**, e **não** pela construção do adaptador: os adaptadores são **singletons de processo**, montados uma vez no import de `src/app.py`, e congelar identidade neles é exatamente o que a Onda 3 teria de desfazer.
4. O valor é declarado em **um único lugar**: `DONO_DO_PROCESSO = "unico"`, com um comentário que declara em maiúsculas que **não é mecanismo de segurança**.
5. O adaptador **ignora** o parâmetro nos quatro métodos do armazenamento.

## Evidência

- `src/ports/__init__.py` traz `dono` nas assinaturas, com a justificativa declarada em cada docstring.
- `ArmazenamentoEmDisco.guardar` / `resolver` / `listar` / `aposentar` recebem e **não usam** o parâmetro; os docstrings dizem isso explicitamente, com a consequência medida: **dois envios do mesmo conteúdo por donos diferentes reencontram o MESMO arquivo** (`RN-02`).
- `tests/test_porta_de_armazenamento.py` (583 linhas úteis) cobre a obrigatoriedade do dono.
- `src/app.py` declara o literal uma vez, e os **quatro** pontos que fornecem o valor o citam — o comentário enumera quais são.

## Justificativa

**O custo é a justificativa inteira, e ele é de segunda ordem.** Adiar o parâmetro não custa hoje; custa na Onda 3, quando seria preciso reabrir **toda** assinatura de porta e **todos** os chamadores de uma vez. A decisão aceita pagar um parâmetro sem comportamento agora para não pagar uma refatoração transversal depois. É a mesma lógica do `ADR-25` ao declarar o `RepositorioDeArvores` vazio.

## Consequências

- 🔴 **Nenhuma entrega pode ser citada como tendo implementado isolamento.** As dívidas #3 (corrida) e #4 (ausência de identidade) seguem **abertas**, e o código o declara em maiúsculas para que a costura não seja lida como conserto.
- 🟢 **A Onda 3 tem onde ancorar:** o parâmetro existe em todas as assinaturas e, desde o `ADR-27`, também como **coluna** `owner_id`.
- 🟡 **O parâmetro é ignorado nos quatro métodos do armazenamento**, e essa é a parte que envelhece pior: um leitor futuro pode interpretar a presença do parâmetro como filtro aplicado. Os docstrings combatem isso caso a caso.
- 🟢 **`listar` e `aposentar` nasceram já com `dono`**, na feature 011, pelo mesmo motivo — e são os dois métodos criados **depois** da decisão, o que mostra que ela foi seguida e não apenas declarada.

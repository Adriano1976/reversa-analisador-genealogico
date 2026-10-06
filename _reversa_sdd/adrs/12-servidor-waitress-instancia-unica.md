# ADR-12 — Servidor de produção waitress, instância única e escuta local por padrão

- **Status:** Aceito e vigente
- **Data da decisão:** 2026-10-04
- **Commit(s):** `1c2db61` (plano da feature `004`), `a946af3` (troca o servidor), `2783cc5` (instância única), `8ed3f8e` (documenta)
- **Confiança:** 🟢 CONFIRMADO

## Contexto

A aplicação subia pelo **servidor de desenvolvimento do Flask**, que (a) **não** é servidor de produção, (b) **não** impõe exclusividade de instância e (c) escutava em `0.0.0.0` por omissão — expondo a rede inteira sem que ninguém tivesse decidido isso. Somando: cada processo tem o **seu próprio** estado global da árvore, e **duas instâncias atendendo** fazem requisições do mesmo operador caírem em estados diferentes.

## Decisão

Três decisões acopladas, todas no bloco de entrada (`src/app.py:179-267`):

1. **Servir com `waitress`** em vez do servidor de desenvolvimento.
2. **Garantir instância única**: o socket é criado, marcado e **ligado** antes de servir, e entregue já pronto ao servidor (`serve(app, sockets=[...])`).
3. **Escutar em `127.0.0.1` por padrão**; abrir para a rede passa a ser **ato explícito** via `ANALISADOR_HOST`.

## Evidência

- `_reversa_forward/004-servidor-waitress/` (requirements, roadmap, actions) e `_reversa_sdd/addenda/004-servidor-waitress.md`.
- `requirements.txt` — `waitress==3.0.2` **entrou**, `gunicorn` **saiu**.
- `src/app.py:229-235` — `SO_EXCLUSIVEADDRUSE` no Windows (a porta fica exclusiva do processo e outra instância recebe erro no `bind` **mesmo pedindo** `SO_REUSEADDR`); fora do Windows, `SO_REUSEADDR` é ativamente **zerado**.
- `src/app.py:233-257` — o diagnóstico **separa** "porta ocupada" (`errno.EADDRINUSE`) de "endereço indisponível" (`10049`), porque pedem ações diferentes.
- `tests/test_servidor_producao.py` — cobre servidor de produção, instância única e o padrão do endereço.
- Variáveis com padrão declarado no código: `ANALISADOR_HOST=127.0.0.1`, `ANALISADOR_PORT=5000`, `ANALISADOR_THREADS=4`.

## Justificativa

**A medição de 2026-10-04 mostrou que a plataforma NÃO impede a coexistência:** o servidor pede `SO_REUSEADDR`, e no Windows duas instâncias escutam na mesma porta ao mesmo tempo. A exclusividade, portanto, é responsabilidade da aplicação. E, sem autenticação (ADR-18), atender a rede **não pode** ser o comportamento que acontece por omissão.

## Consequências

- ✅ **A mitigação de risco do `BUG-20260929-BJJH` deixou de depender de disciplina.** O plano de tratamento exigia que a aplicação não fosse exposta a mais de uma pessoa; isso antes dependia de comportamento humano, e agora tem **garantia técnica no padrão**: escuta local + recusa de segunda instância.
- ⚠️ **A guarda é de processo, não de thread.** Ela **não** resolve a troca de estado entre requisições concorrentes — o servidor atende com **4 threads** e o estado do GEDCOM é global de processo (`L-16` em `domain.md` §7 e `permissions.md` §4.3).
- 🟢 **Detalhe de implementação que é contrato:** o socket fica **aberto até o processo terminar**. Fechá-lo para só então servir abriria uma janela entre fechar e servir — exatamente o que a marca de uso exclusivo existe para não ter.
- 🟢 **A troca para `waitress` fez parte do mesmo movimento da fixação de versões (ADR-13)**: o servidor passou a ser uma dependência declarada e pinada, e não o servidor embutido do framework.

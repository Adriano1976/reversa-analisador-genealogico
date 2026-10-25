# ADR-37 — Observabilidade em camadas, sem ferramenta externa

- **Status:** Aceito e **vigente**
- **Data da decisão:** 2026-10-25
- **Origem:** entrega da feature `049-sistema-de-log`, a partir do plano de implantação
  anexado pelo operador e da decisão 14 do `gaps.md`
- **Confiança:** 🟢 CONFIRMADO (código em `src/utils/logs.py`, `src/utils/auditoria.py` e
  `src/web/hooks_de_registro.py`)

## Contexto

A extração de 2026-10-10 registrou, nas cinco units, a mesma frase: **"nenhum log, métrica ou
trace"**. O que existia, medido na abertura da feature 049: **nove** chamadas de registro
espalhadas em dois arquivos (`src/app.py` e `src/ports/adaptadores.py`), **um** `print` de
inicialização e **nenhuma** configuração — sem `basicConfig`, sem `dictConfig`, sem
`setLevel`. Consequências medidas:

1. tudo abaixo de `WARNING` **se perdia** (o `_log.info` do cache da árvore, da feature 047,
   existia e não chegava a lugar nenhum);
2. não havia arquivo: o que passava no console não se lia de novo;
3. não havia identidade de requisição, então uma linha de erro não se ligava ao acesso que a
   causou;
4. a **única ação que move arquivo do operador** — aposentar — não deixava rastro nenhum
   (`tela-de-entrada/tasks.md`, lacuna 5).

A decisão 14 do `gaps.md` já mandava "logar as duas tentativas". Faltava o resto: onde, como e
com qual proteção de privacidade.

## Decisão

**Registro em três destinos, com um papel para cada, usando só a biblioteca padrão.**

1. **Console** — operação. **Arquivo geral** (`analisador.log`, rotativo em 5 × 5 MB) —
   diagnóstico. **Trilha de auditoria** (`analisador.auditoria.AAAA-MM-DD.log`) — prova. A
   trilha **não propaga** para os outros dois (`RN-01`).
2. **A auditoria não rotaciona por tamanho.** Rotacionar apagaria dado antes dos **90 dias**
   declarados na `RN-10` — seria expurgo automático disfarçado. Ela grava um arquivo por dia e
   o descarte é do operador.
3. **Identificador por requisição** em `contextvars`, devolvido no cabeçalho `X-Request-ID` e
   repetido na linha de acesso e em toda linha de erro. O valor **nunca** é aceito do cliente
   (texto de cliente em arquivo de log é vetor de injeção de linha).
4. **Máscara de privacidade no destino, não no ponto de chamada:** um `Filter` que reescreve
   mensagem, argumentos **e o traceback** (materializa `exc_text` e zera `exc_info`, senão o
   formatador reformataria a exceção crua). Cobre identificador de kit (`[A-Z]{2}\d{7}`, o
   mesmo padrão da leitura do CSV) e e-mail.
5. **A auditoria é emitida na borda** (`src/app.py`), nunca no caso de uso: IP e identificador
   são HTTP.
6. **A linha identifica o arquivo pela chave de conteúdo com extensão**, nunca pelo rótulo
   visível — os nomes reais da pasta incluem nome de pessoa.
7. **A configuração é idempotente por marcador no handler**, e não por booleano de módulo: a
   suíte reexecuta `src/app.py` com `exec_module`, o que cria namespace novo a cada vez,
   enquanto o registro de handlers do `logging` é global do processo.
8. **Pasta inescrevível degrada para console** com um aviso e não derruba requisição: o
   diagnóstico não é motivo de indisponibilidade.

## Evidência

- `src/utils/logs.py` — configuração, contexto (`ContextVar`), `FiltroDeContexto`,
  `FiltroDePrivacidade`, `medir()` e `registrar_acesso()`; pasta ancorada na raiz do projeto,
  sobrescrevível por `ANALISADOR_LOG_DIR`.
- `src/utils/auditoria.py` — `ACOES` e `DESFECHOS` fechados; a linha leva `acao`, `desfecho`,
  `arquivo` (chave + extensão), `ip`, `origem` e contagens numéricas.
- `src/web/hooks_de_registro.py` — `before_request` gera o identificador; `after_request`
  grava a linha de acesso, emite o cabeçalho e devolve o contexto ao neutro.
- `src/app.py` — `logs.configurar()` e `instalar_registro()` em `create_app()`; auditoria nos
  cinco fluxos; `print` de inicialização virou `INFO`.
- `ResultadoDeUpload` ganhou `desfecho` (`src/application/upload_gedcom.py`), para a borda
  auditar sem reconhecer o caso pelo texto da mensagem (`RF-20`).
- `tests/test_configuracao_de_log.py`, `test_identificador_de_requisicao.py`,
  `test_privacidade_do_log.py`, `test_registro_de_auditoria.py`, `test_medicao_da_carga.py` —
  28 testes, incluindo o de privacidade sobre uma análise com árvore sintética.
- `docker-compose.yml` — volume `./logs` e rotação `json-file` 5 × 5 MB no serviço da
  aplicação.

## Justificativa

**Ferramenta externa foi descartada por três motivos, nesta ordem:** o sistema trata dado
genealógico de pessoas vivas, e enviar linha de log a um coletor é exportar dado pessoal para
fora da máquina do operador (Princípio I); a escala é um operador, um processo e uma tela; e a
`RN-09` proíbe dependência nova de runtime. O detalhe está em
`_reversa_forward/049-sistema-de-log/investigation.md` §2.

**Auditar no banco foi descartado** mesmo existindo `access_audit` no DDL do alvo: a
persistência é **opcional** (`ADR-27`), e auditoria que desaparece sem `DATABASE_URL` não é
auditoria. O driver também não está no `.venv` oficial (`L-26`).

**A separação de destinos é o que permite prazos diferentes.** Diagnóstico é descartável e
rotaciona por tamanho; prova tem prazo declarado e não pode sumir por volume. Um destino só
obrigaria a escolher entre as duas políticas.

## Consequências

- 🟢 **A lacuna 5 da `tela-de-entrada` e a decisão 14 do `gaps.md` estão fechadas**: as duas
  tentativas de aposentar deixam linha, com desfecho distinto.
- 🟢 **A afirmação "nenhum log" das cinco units deixa de ser verdadeira** — a convergência nos
  artefatos de extração é feita pelo `/reversa-sync`.
- 🟢 **A correlação erro↔acesso passou a existir**: o operador copia o `X-Request-ID` e acha a
  linha, inclusive a de exceção.
- 🔴 **A trilha passou a acumular dado pessoal** (IP e chaves de conteúdo) com prazo declarado
  de 90 dias e **nenhum mecanismo que o faça cumprir** (`RN-10`, expurgo manual). Registrado
  como lacuna 🟡 no `requirements.md` §10.
- 🟡 **As três mensagens de tela mudaram** (`RN-06`): o texto interno da exceção saiu da tela e
  ficou no log. É alteração de contrato declarada, com golden e fixture a atualizar em
  conjunto — e a decisão preservou os prefixos justamente para o `modo()` do harness de
  paridade continuar classificando o desfecho (`harness.py:185`).
- 🟡 **A pasta de log na raiz não está no `.gitignore`**: o caminho não está no `allowedPaths`
  da política de edição do legado, e a ação correspondente (T022) ficou aberta. O
  `.dockerignore` já a exclui do contexto de build por ser lista de permissão.
- 🟢 **A medição nomeada do parse** (`carregar_arvore`) passa a alimentar a decisão do cache
  das features 025 e 047 com número do próprio sistema, e não com cronômetro externo.

## Alternativas registradas e descartadas

| Alternativa | Por que não |
|---|---|
| Ferramenta externa de observabilidade | Dado pessoal para fora da máquina; escala de um operador; `RN-09` |
| Biblioteca de log estruturado | Mesma proibição, e não resolveria a máscara no traceback |
| `basicConfig` | No-op a partir da segunda chamada no processo: falha silenciosa na suíte |
| `dictConfig` | Camada de configuração sem ganho medido para três destinos |
| Linha de acesso do `waitress` como única fonte | Não tem identificador, não passa pela máscara, formato do servidor |
| Auditoria persistida em `access_audit` | Depende do banco, que é opcional; driver ausente do `.venv` |
| Rotação por tamanho também na auditoria | Descartaria dado antes dos 90 dias declarados |

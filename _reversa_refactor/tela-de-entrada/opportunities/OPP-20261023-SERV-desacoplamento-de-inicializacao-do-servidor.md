---
schema_version: 1
id: OPP-20261023-SERV
display_number: 41
context: tela-de-entrada
verb: decouple
title: Desacoplamento da inicialização de servidor e controle de sockets de SO
target:
  files: [src/app.py]
  symbol: bloco __main__ (linhas 795-889)
smell: >
  O arquivo app.py abriga 95 linhas de logica de baixo nivel de rede e sockets de sistema
  operacional (socket.socket, SO_EXCLUSIVEADDRUSE, bind, listen, checagem de errno EADDRINUSE
  e inicializacao de servidor Waitress com teto de corpo e margem).
roi:
  confidence: green
  impact: >
    Desacopla a camada de infraestrutura de rede da aplicacao Flask web. Permite importar app.py
    em testes sem carregar logica de socket e prepara o projeto para rodar via WSGI padrao ou CLI.
  cost: low
  est_return: >
    app.py aliviado de 95 linhas de codigo de infraestrutura de rede. Modulo de execucao isolado.
state: declined
declined_reason: >
  O teste tests/test_servidor_producao.py inspeciona o AST do arquivo src/app.py
  exigindo que o bloco if __name__ == "__main__": contenha os simbolos e chamadas
  de socket e waitress diretamente no app.py. Mover o bloco quebraria o contrato
  estatico aferido pelo teste.
promoted_to: null
traceability:
  soul: []
  specs:
    - _reversa_sdd/architecture.md
    - _reversa_sdd/adrs/28-docker-dois-servicos-dockerignore-permissao.md
---

## Antes observado

Em `src/app.py:795-889`:
O bloco `if __name__ == "__main__":` implementa toda a configuracao de socket exclusivo para Windows,
tratamento de erros de bind/porta em uso, deteccao de variaveis de ambiente e inicializacao do Waitress.

## Transformação proposta

Extrair a rotina de inicializacao para uma funcao de execucao `iniciar_servidor(app)` em modulo proprio
(ex: `src/servidor.py` ou `src/runner.py`), mantendo em `app.py` apenas a chamada `iniciar_servidor(app)`
no `if __name__ == "__main__":`.

## Rede de segurança

A suite valida o servidor atraves de `tests/test_guardas_do_armazenamento.py` e testes de ambiente.

---
*Gerado pelo Reversa-Refactor em 2026-10-23.*

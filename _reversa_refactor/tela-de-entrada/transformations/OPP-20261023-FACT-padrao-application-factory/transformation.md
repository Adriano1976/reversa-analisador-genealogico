---
schema_version: 1
id: OPP-20261023-FACT
verb: modularize
state: applied
safety_net:
  kind: characterization
  green_before: true
  green_after: true
preservation:
  method: tests
  evidence:
    - safety-net/suite-antes.txt
    - safety-net/suite-depois.txt
    - safety-net/suite-direcionada.txt
measurement:
  before: "src/app.py com 737 linhas: a montagem do app e o proprio corpo do modulo, sem composition root"
  after: "src/app.py com 764 linhas, com `create_app(config=None)` e `app = create_app()`; 6 testes de caracterizacao"
change_set:
  - chg: CHG-001
    file: src/app.py
    purpose: extrai `create_app`, troca os cinco decoradores por registro explicito, move config/filtros/Blueprint para a fabrica e usa `current_app.logger`
  - chg: CHG-001
    file: tests/test_fabrica_do_app.py
    purpose: caracteriza a fabrica, as cinco rotas, a configuracao e os ganchos
approval:
  by: user
  at: 2026-10-23T04:10:05-03:00
reversible_via: [CHG-001-fabrica-do-app.diff]
---

# Transformacao: OPP-20261023-FACT (composition root explicito)

## O que mudou

A montagem da aplicacao deixou de ser o corpo do modulo e passou a ser uma funcao
com nome. O modulo continua criando uma instancia, no fim do arquivo:

```python
def create_app(config=None) -> Flask:
    aplicacao = Flask(__name__)
    aplicacao.config["MAX_CONTENT_LENGTH"] = TETO_DE_UPLOAD_EM_BYTES
    aplicacao.config["TRUSTED_HOSTS"] = _hosts_permitidos()
    ...
    aplicacao.register_blueprint(assets_bp)
    aplicacao.add_url_rule("/", endpoint="index", view_func=index, methods=["GET", "POST"])
    if config:
        aplicacao.config.update(config)
    return aplicacao


app = create_app()
```

Os passos, na ordem:

| Passo | Refatoracao | Efeito |
|---|---|---|
| 1 | Extract Function | `app = Flask(...)`, as 5 chaves de config, os 5 filtros e o Blueprint saem do escopo do modulo para `create_app` |
| 2 | Replace Decorator with Registration | os 5 decoradores viram `register_error_handler`, `after_request`, `context_processor` e `add_url_rule` |
| 3 | Replace Global with Context | os 5 `app.logger` viram `current_app.logger` |
| 4 | Introduce Factory Facade | `app = create_app()` fecha o modulo, antes do bloco `__main__` |
| 5 | Characterization Test | `tests/test_fabrica_do_app.py` fixa a fabrica e as cinco rotas |

## O teste de caracterizacao

Seis testes, em `tests/test_fabrica_do_app.py`:

1. `create_app()` devolve instancia nova, diferente de `app`;
2. a instancia nova tem as cinco rotas com os metodos certos;
3. as cinco chaves de configuracao sao copiadas do app de modulo;
4. `create_app({"TESTING": True, "MAX_CONTENT_LENGTH": 123})` honra a sobreposicao;
5. criar uma instancia nao altera o `url_map` nem a config do app de modulo;
6. os tratadores 413 e 400 e os ganchos `after_request` e processador de contexto
   estao registrados, e apontam para as funcoes do modulo.

O teste importa `app` no topo e insere `src/` no `sys.path` explicitamente, como
`tests/test_arvore_devolvida.py` ja fazia. O `tests/conftest.py` so faz essa
insercao dentro do fixture `cliente_de_upload`, e a primeira coleta falhou com
`ModuleNotFoundError`. A correcao ficou no teste; nenhuma linha de `src/` mudou
por causa dela.

## O que NAO mudou

- as cinco rotas, os metodos e os endpoints (`index`, `assets.*`);
- os literais de mensagem, os status HTTP e as chaves de contexto;
- o `url_map` do app de modulo: seis regras, as mesmas de antes;
- `TETO_DE_UPLOAD_EM_BYTES`, `HOSTS_PERMITIDOS_PADRAO`, `_hosts_permitidos`,
  `_ARMAZENAMENTO`, `_CARREGADOR` e `_REGISTRO`, que os testes importam;
- o bloco `if __name__ == "__main__":` e a chamada `serve(app, ...)`, que o
  `tests/test_servidor_producao.py` le por AST.

## O que a fabrica NAO entrega

Isolamento de estado. `_ARMAZENAMENTO`, `_CARREGADOR`, `_REGISTRO` e
`_DEPENDENCIAS` continuam no escopo do modulo, entao duas instancias compartilham
a pasta de uploads e o registro. O que a fabrica entrega e isolamento de
**configuracao** e um ponto de montagem explicito. A injecao de estado nos
handlers e um passo de `decouple`, com oportunidade propria.

Isto esta declarado na docstring de `create_app` e no plano, para que ninguem
leia a existencia da fabrica como prova de isolamento.

## Prova

Antes de tocar em `src/`, o diff foi aplicado numa copia isolada de `src/` (fora do
repositorio) e exercitado: importacao, cinco rotas, instancia nova, config padrao,
sobreposicao, tratadores, `GET /`, `GET /app.css` e `POST /descartes.csv`.

Depois da aplicacao:

| Momento | Resultado |
|---|---|
| antes, estado com o lote e a realocacao | 1615 passed, 9 skipped em 128,75 s |
| teste novo isolado | 6 passed em 8,57 s |
| suite completa depois | 1621 passed, 9 skipped em 294,19 s |

1615 + 6 = 1621, com as mesmas 9 exclusoes e nenhuma falha. Evidencia em
[suite-antes.txt](safety-net/suite-antes.txt),
[suite-depois.txt](safety-net/suite-depois.txt) e
[suite-direcionada.txt](safety-net/suite-direcionada.txt).

## Reversibilidade

`CHG-001-fabrica-do-app.diff` foi gerado do estado anterior a FACT (737 linhas,
sem `create_app`) para o estado aplicado (764 linhas), e inclui o teste novo. A
reversao devolve `src/app.py` ao corpo de modulo e apaga
`tests/test_fabrica_do_app.py`.

## Aprovacao

O plano foi aprovado antes do diff, e o diff foi aprovado antes da aplicacao, os
dois por decisao do usuario nesta sessao. O horario acima e o da gravacao do
`src/app.py` aplicado.

---
schema_version: 1
id: OPP-20261023-ESTD
display_number: 44
context: tela-de-entrada
verb: decouple
title: Estado de borda em variaveis de modulo impede isolamento por instancia do app
target:
  files: [src/app.py]
  symbol: _ARMAZENAMENTO, _CARREGADOR, _REGISTRO, _DEPENDENCIAS, _arvore_do_formulario, _listas_da_tela, _acao_upload_gedcom, _acao_aposentar_arquivo, _acao_dna_analysis, _acao_path_search, create_app
smell: >
  O `create_app()` da OPP-20261023-FACT monta uma instancia nova, mas os handlers
  continuam lendo quatro objetos do escopo do modulo. Duas instancias compartilham
  a mesma pasta de uploads, o mesmo carregador, o mesmo registro e as mesmas
  dependencias do nucleo. O unico jeito de trocar um deles num teste e
  `monkeypatch` no global do modulo, e o proprio `create_app` declara esse limite
  na docstring.
roi:
  confidence: green
  impact: >
    Fecha a promessa que a fabrica abriu. `create_app(armazenamento=...,
    carregador=..., registro=..., dependencias=...)` passa a montar uma instancia
    com estado proprio, e os handlers leem de `current_app.extensions` em vez de
    nomes globais. O app de modulo continua identico, porque os defaults sao os
    mesmos objetos de hoje.
  cost: medium
  est_return: >
    Quatro dependencias injetaveis por instancia, handlers sem leitura de global,
    e testes de isolamento sem `monkeypatch` em `_ARMAZENAMENTO`.
state: applied
promoted_to: null
traceability:
  soul: [soul.md#D3, soul.md#D5]
  specs:
    - _reversa_sdd/adrs/25-fronteira-de-aplicacao-portas.md
    - _reversa_sdd/adrs/26-dono-no-port-como-costura.md
    - _reversa_sdd/adrs/27-persistencia-postgres-opcional.md
    - _reversa_sdd/architecture.md
---

## Antes observado

`src/app.py` monta o estado de borda no import e o deixa em quatro nomes de modulo:

| Linha | Objeto | Quem le hoje |
|---|---|---|
| 47 | `_DEPENDENCIAS` | `_acao_dna_analysis` (487), `_acao_path_search` (539) |
| 190 | `_ARMAZENAMENTO` | `_listas_da_tela` (358), `_acao_upload_gedcom` (380), `_acao_aposentar_arquivo` (402), `_acao_dna_analysis` (439, 460) |
| 191 | `_CARREGADOR` | `_arvore_do_formulario` (316), `_acao_upload_gedcom` (381) |
| 210 | `_REGISTRO` | `_acao_dna_analysis` (490) |

`create_app()` cria a instancia Flask, mas nao recebe nenhum desses objetos. Duas
instancias criadas por `create_app()` continuam compartilhando a pasta de uploads
e o registro, e a docstring de `create_app` declara exatamente esse limite.

## Transformacao proposta

Quatro passos:

1. `create_app` passa a aceitar as quatro dependencias, com sentinela para
   distinguir "nao injetado" de "injetado como `None`" no caso do registro
   opcional:

```python
_SEM_INJECAO = object()


def create_app(config=None, *, armazenamento=None, carregador=None,
               registro=_SEM_INJECAO, dependencias=None) -> Flask:
    aplicacao = Flask(__name__)
    ...
    aplicacao.extensions["analisador"] = {
        "armazenamento": armazenamento or _ARMAZENAMENTO,
        "carregador": carregador or _CARREGADOR,
        "registro": _REGISTRO if registro is _SEM_INJECAO else registro,
        "dependencias": dependencias or _DEPENDENCIAS,
    }
    ...
```

2. Um unico acesso no modulo:

```python
def _estado_de_borda() -> dict:
    return current_app.extensions["analisador"]
```

3. Os cinco pontos de leitura passam a usar `_estado_de_borda()`:
   `_arvore_do_formulario`, `_listas_da_tela`, `_acao_upload_gedcom`,
   `_acao_aposentar_arquivo`, `_acao_dna_analysis` e `_acao_path_search`.

4. Os quatro nomes de modulo continuam existindo, porque o `app = create_app()`
   usa os defaults e ha testes que os leem (`_REGISTRO is None` em
   `tests/test_persistencia_desabilitada.py:88`, por exemplo).

## Fronteira de comportamento

Nenhuma rota, mensagem, status, template ou chave de contexto muda. Com o app de
modulo, `_estado_de_borda()` devolve os mesmos quatro objetos de hoje, entao a
suite deve continuar passando sem alteracao de expectativa. O que muda e a
possibilidade de uma instancia nova receber outros objetos.

## Riscos medidos

| Risco | O que acontece | Mitigacao |
|---|---|---|
| `current_app` fora de contexto | `_listas_da_tela` e os handlers so rodam em requisicao; `_arvore_do_formulario` tambem | a suite inteira exercita os cinco caminhos |
| `tests/test_promocao_de_descarte.py:198` | faz `monkeypatch` em `type(modulo_app._ARMAZENAMENTO).resolver`, no nivel da classe | o patch continua valendo para a instancia padrao e para qualquer instancia da mesma classe |
| `tests/test_persistencia_desabilitada.py:88` | afirma `modulo._REGISTRO is None` sem `DATABASE_URL` | o nome de modulo permanece |
| `tests/test_promocao_de_descarte.py:195` | troca `modulo_app._arvore_do_formulario` | `index` continua chamando o nome global; a troca segue funcionando |
| registro `None` como valor valido | `registro or _REGISTRO` confundiria "nao injetado" com "sem persistencia" | sentinela `_SEM_INJECAO` |

## O que fica de fora

- Mover o estado para um modulo proprio (`web/` ou `ports/`): nao e necessario para
  injetar e mudaria a topologia de pacotes.
- Trocar as portas ou o `Protocol` de `src/ports/`: as assinaturas continuam as
  mesmas.
- Tirar o `dono` das assinaturas: e costura declarada do `ADR-26`.
- Mudar a regra dos tres estados da persistencia (`ADR-27`).

## Rede de seguranca

A suite atual tem 1621 testes passando e 9 pulados, e cobre as cinco acoes. A
transformacao acrescenta testes de isolamento:

1. `create_app(armazenamento=fake)` guarda o fake em `extensions["analisador"]`;
2. uma requisicao `GET /` na instancia nova chama `fake.listar`, e nao o
   armazenamento de disco;
3. `create_app(registro=None)` grava `None` em `extensions`, distinto de "nao
   injetado";
4. o app de modulo continua com os quatro objetos padrao.

O gate e a suite verde antes e depois, com a contagem de 1621 preservada e os
testes novos somados.

## Registro de aplicação (2026-10-23)

Plano e diff aprovados e aplicados. `create_app` recebe `armazenamento`,
`carregador`, `registro` e `dependencias` como parâmetros keyword-only, guarda em
`extensions["analisador"]`, e as dez leituras dos handlers passam por
`_estado_de_borda()`.

- Transformação: `transformations/OPP-20261023-ESTD-estado-de-borda-injetavel/transformation.md`
- Diff: `.../CHG-001-estado-de-borda-injetavel.diff`
- Acoplamento: 10 → 0 leituras de global em handlers; 0 → 4 dependências injetáveis.
- Suíte: 1621 → 1625 passed, 9 skipped (4 testes novos).

A independência das quatro é deliberada: injetar só `armazenamento` não reconstrói
o `carregador`, que continua apontando para o armazenamento real. Um teste de
upload isolado injeta os dois.

---
*Gerado pelo Reversa-Refactor em 2026-10-23.*

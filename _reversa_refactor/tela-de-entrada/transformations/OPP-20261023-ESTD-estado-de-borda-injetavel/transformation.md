---
schema_version: 1
id: OPP-20261023-ESTD
verb: decouple
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
  before: "4 objetos de estado no modulo, 10 leituras do global em 6 funcoes, 0 dependencias injetaveis em create_app"
  after: "0 leituras de global em handlers, 1 ponto de acesso (_estado_de_borda), 4 dependencias injetaveis, 1 chave de extensao"
change_set:
  - chg: CHG-001
    file: src/app.py
    purpose: injeta as quatro dependencias em create_app, guarda em extensions e troca as dez leituras por _estado_de_borda
  - chg: CHG-001
    file: tests/test_estado_de_borda_injetavel.py
    purpose: caracteriza a injecao e o isolamento de duas instancias
approval:
  by: user
  at: 2026-10-23T13:32:45-03:00
reversible_via: [CHG-001-estado-de-borda-injetavel.diff]
---

# Transformacao: OPP-20261023-ESTD (estado de borda injetavel)

## Acoplamento antes e depois

| Medida | Antes | Depois |
|---|---|---|
| Objetos de estado no modulo | 4 | 4 (so como padrao) |
| Leituras do global dentro de handlers | 10 | **0** |
| Funcoes acopladas ao global | 6 | **0** |
| Pontos de acesso ao estado | 10 | **1** (`_estado_de_borda`) |
| Dependencias injetaveis em `create_app` | 0 | **4** |
| Chaves de extensao | 0 | **1** (`"analisador"`) |

O numero que importa e o primeiro: os handlers nao leem mais nome de modulo. As
quatro ocorrencias que sobraram no arquivo sao a construcao (linhas 47, 190, 191
e 210) e os quatro defaults dentro de `create_app`.

## A costura aplicada

Injecao por construtor no composition root, com um ponto unico de leitura:

```python
_SEM_INJECAO = object()
CHAVE_DA_BORDA = "analisador"


def _estado_de_borda() -> dict:
    return current_app.extensions[CHAVE_DA_BORDA]


def create_app(config=None, *, armazenamento=None, carregador=None,
               registro=_SEM_INJECAO, dependencias=None) -> Flask:
    ...
    aplicacao.extensions[CHAVE_DA_BORDA] = {
        "armazenamento": _ARMAZENAMENTO if armazenamento is None else armazenamento,
        "carregador": _CARREGADOR if carregador is None else carregador,
        "registro": _REGISTRO if registro is _SEM_INJECAO else registro,
        "dependencias": _DEPENDENCIAS if dependencias is None else dependencias,
    }
```

As dez leituras trocadas:

| Funcao | Era | Ficou |
|---|---|---|
| `_arvore_do_formulario` | `_CARREGADOR` | `_estado_de_borda()["carregador"]` |
| `_listas_da_tela` | `_ARMAZENAMENTO` | `_estado_de_borda()["armazenamento"]` |
| `_acao_upload_gedcom` | `_ARMAZENAMENTO`, `_CARREGADOR` | `borda["armazenamento"]`, `borda["carregador"]` |
| `_acao_aposentar_arquivo` | `_ARMAZENAMENTO` | `_estado_de_borda()["armazenamento"]` |
| `_acao_dna_analysis` | `_ARMAZENAMENTO` (2), `_DEPENDENCIAS`, `_REGISTRO` | `borda[...]`, um acesso no inicio da funcao |
| `_acao_path_search` | `_DEPENDENCIAS` | `_estado_de_borda()["dependencias"]` |

A sentinela existe so para `registro`, porque `None` e um valor valido: significa
persistencia desligada.

## Independencia das quatro dependencias

Cada uma entra por conta propria. Injetar so `armazenamento` **nao** reconstroi o
`carregador`: ele continua sendo o `_CARREGADOR` do modulo, que aponta para o
armazenamento real. Para um teste de upload totalmente isolado, injete os dois.
Isso e deliberado: a fabrica nao adivinha qual carregador combina com qual
armazenamento, e criar um novo a cada injecao acrescentaria uma construcao que o
plano nao previu.

## O que NAO mudou

- as cinco rotas, metodos, endpoints, mensagens e status;
- o `url_map` do app de modulo;
- os quatro nomes de modulo, que continuam existindo como padrao;
- `DONO_DO_PROCESSO`, os `Protocol` de `src/ports/` e a regra dos tres estados da
  persistencia;
- o bloco `if __name__ == "__main__":` e `serve(app, ...)`.

## Prova

Antes do gate 2, o diff foi aplicado numa copia isolada de `src/` e exercitado com
duas instancias e dois armazenamentos falsos: cada `GET /` chamou o proprio
armazenamento. A prova rodou fora do repositorio.

Depois da aplicacao:

| Momento | Resultado |
|---|---|
| antes (estado da FACT) | 1621 passed, 9 skipped em 294,19 s |
| testes novos isolados | 4 passed em 8,95 s |
| suite completa depois | 1625 passed, 9 skipped em 157,14 s |

1621 + 4 = 1625, com as mesmas 9 exclusoes e nenhuma falha. Evidencia em
[suite-antes.txt](safety-net/suite-antes.txt),
[suite-depois.txt](safety-net/suite-depois.txt) e
[suite-direcionada.txt](safety-net/suite-direcionada.txt).

## Riscos que nao se materializaram

| Risco | O que aconteceu |
|---|---|
| `tests/test_promocao_de_descarte.py` troca o metodo da classe de `_ARMAZENAMENTO` | continua valendo: o app de modulo usa a mesma instancia |
| `tests/test_persistencia_desabilitada.py` afirma `_REGISTRO is None` | continua valendo: o nome de modulo permanece |
| `tests/test_promocao_de_descarte.py` troca `_arvore_do_formulario` | continua valendo: `index` chama o nome global |
| `current_app` fora de contexto | nao ocorreu: os seis caminhos rodam em requisicao |

## Reversibilidade

`CHG-001-estado-de-borda-injetavel.diff` aplica os dois arquivos e reverte pelo
mesmo diff. A reversao devolve as dez leituras de global, remove a sentinela, a
chave, o helper e os quatro parametros, e apaga o teste novo.

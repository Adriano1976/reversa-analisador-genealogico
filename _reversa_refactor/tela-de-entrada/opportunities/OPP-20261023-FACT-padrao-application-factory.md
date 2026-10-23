---
schema_version: 1
id: OPP-20261023-FACT
display_number: 42
context: tela-de-entrada
verb: modularize
title: Padrão Application Factory para instanciação e configuração de app Flask
target:
  files: [src/app.py]
  symbol: app, filtros e manipuladores de erro
smell: >
  A instancia app = Flask(__name__) e criada como singleton global de modulo.
  Filtros de template, limites de upload, headers de seguranca e errorhandlers
  sao registrados diretamente no escopo global, dificultando isolamento de testes
  e reconfiguracao controlada.
roi:
  confidence: yellow
  impact: >
    Introduz o padrao arquitetural Application Factory (create_app()), recomendacao oficial
    do ecossistema Flask. Permite criar instancias isoladas para testes e manter
    uma fachada retrocompativel app no modulo para zero breaking change.
  cost: medium
  est_return: >
    Ciclo de vida configurado de forma orientada a objetos com create_app().
state: applied
promoted_to: null
traceability:
  soul: []
  specs:
    - _reversa_sdd/architecture.md
    - _reversa_sdd/c4-components.md
---

## Antes observado

Em `src/app.py:87-147, 184, 238-293`:
A aplicacao Flask e inicializada no momento do import de `app.py`.
Todas as configuracoes e manipuladores de erro ficam no espaco global.

## Transformação proposta

Encapsular a criacao e montagem de componentes na funcao `create_app(config=None) -> Flask`:

```python
def create_app(config=None) -> Flask:
    app = Flask(__name__)
    _configurar_limites(app)
    _registrar_filtros(app)
    _registrar_manipuladores_de_erro(app)
    _registrar_rotas(app)
    return app

# Fachada retrocompativel para importadores legados:
app = create_app()
```

## Rede de segurança

A suite inteira de testes que importa `from app import app` continua funcionando
gracas a instancia de modulo exportada pela fachada retrocompativel.

## Reclassificação (2026-10-23)

O verbo foi corrigido de `restructure` para `modularize`. O especialista de
`restructure` tem limite explicito: trabalha a estrutura interna de um metodo ou
classe e recusa alvo que seja o corpo do modulo. O que esta em jogo aqui e a
distribuicao de responsabilidade do modulo inteiro, que hoje constroi o app,
configura, registra seguranca, rotas e servidor no mesmo escopo de import.

O nome do padrao (Application Factory) permanece, mas o que se extrai e o
**composition root**: a funcao que monta a aplicacao passa a existir com nome e
pode ser chamada mais de uma vez.

## Limite medido antes de planejar

Um levantamento feito em 2026-10-23 mostra o custo e o limite do que uma factory
resolve:

| Item | Medida |
|---|---|
| referencias ao `app` global em `src/app.py` | 27 |
| referencias a `app.config` e `app.test_client` em `tests/` | 21 |
| estado de modulo criado no import | `_ARMAZENAMENTO`, `_CARREGADOR`, `_REGISTRO`, `_DEPENDENCIAS` |
| `app.logger` dentro dos handlers | 5 |

Conclusao: a factory entrega **isolamento de configuracao** (cada app com seu
`MAX_CONTENT_LENGTH`, `TRUSTED_HOSTS` e chaves de arte) e um ponto de montagem
explicito. Ela **nao entrega** isolamento de armazenamento nem de persistencia,
porque `_ARMAZENAMENTO`, `_CARREGADOR` e `_REGISTRO` continuam no escopo do
modulo. Esse segundo passo e `decouple`, nao `modularize`, e nao entra nesta
transformacao.

## Registro de aplicação (2026-10-23)

Plano e diff aprovados nesta sessão e aplicados. `create_app(config=None)` existe
em `src/app.py`, o `app` de módulo é criado por ele, e as cinco rotas continuam
iguais. Entrou também `tests/test_fabrica_do_app.py`, com 6 testes.

- Transformação: `transformations/OPP-20261023-FACT-padrao-application-factory/transformation.md`
- Diff: `.../CHG-001-fabrica-do-app.diff`
- Suíte: 1615 passed, 9 skipped antes; 1621 passed, 9 skipped depois (1615 + 6).

O limite declarado continua valendo: a fábrica isola **configuração**, não o
estado de borda (`_ARMAZENAMENTO`, `_CARREGADOR`, `_REGISTRO`). Isolar isso é
`decouple`, e fica para outra oportunidade.

---
*Gerado pelo Reversa-Refactor em 2026-10-23.*

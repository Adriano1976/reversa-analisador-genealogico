---
schema_version: 1
id: OPP-20261003-INIT
display_number: 26
context: pacote-reconstructed
verb: modularize
title: criar src/__init__.py, como o exemplo do usuario pede
target:
  files: [src/__init__.py]
  symbol: o arquivo que o exemplo chama de "torna a pasta src um pacote importavel"
smell: o exemplo do usuario inclui `src/__init__.py`, e ele nao existe. Nao e um code smell: e um pedido explicito que contradiz uma regra registrada
roi:
  confidence: red
  impact: nenhum ganho de importacao, e um risco medido. Ver as duas secoes abaixo
  cost: low
  est_return: nenhum. A intencao declarada no exemplo, "tornar a pasta src um pacote importavel", ja e atendida sem o arquivo
state: proposed
traceability:
  soul:
    - .reversa/soul.md#decisoes-fundadoras
  specs:
    - _reversa_forward/003-renomear-pasta-app-para-src/requirements.md#4
    - _reversa_forward/003-renomear-pasta-app-para-src/investigation.md
---

## Antes observado

`src/__init__.py` nao existe, e a ausencia e deliberada. A `RN-01` da feature 003 diz, literalmente:

> O diretorio que contem o codigo da aplicacao e uma **raiz de caminho de importacao**, nao um pacote importavel; a identidade dos modulos do nucleo (`reconstructed.*`) independe do nome desse diretorio.

A origem da regra esta em `_reversa_sdd/inventory.md#4`: o `search-path` do `pyrefly.toml` e o `sys.path` dos testes existem justamente porque `src` e raiz, e nao pacote.

## A intencao do exemplo ja esta atendida sem o arquivo

O comentario do exemplo diz que o arquivo "torna a pasta src um pacote importavel". O objetivo e importar o codigo de dentro de `src/`. Isso ja funciona hoje, e continuara funcionando depois da `OPP-20261003-FLAT`, sem `src/__init__.py`:

- `pyrefly.toml` tem `search-path = ["src"]`, e e assim que o verificador acha os modulos;
- os testes fazem `sys.path.insert(0, .../src)`;
- o `harness.py` faz `sys.path.insert(0, os.path.join(W, "src"))` dentro do coletor;
- ao rodar `python src/app.py`, o diretorio do script entra no `sys.path` sozinho.

Com `src` no caminho de busca, `core`, `parser` e `utils` sao pacotes de primeiro nivel e sao importaveis. O `__init__.py` nao acrescenta acesso: ele apenas acrescenta um segundo nome para o mesmo arquivo.

## O risco, que foi medido neste projeto

O `__init__.py` em `src/` cria a possibilidade de o mesmo arquivo ser alcancado por **dois nomes**: `core.matching`, quando a busca comeca em `src`, e `src.core.matching`, quando ela comeca na raiz do repositorio. O Python trata isso como dois modulos distintos, com dois espacos de nomes independentes.

Nao e hipotese. A `OPP-20260929-EHNZ` registra esse mecanismo como a raiz do defeito de exposicao entre usuarios, e a investigacao da feature 003 mediu o caso concreto: o mesmo arquivo carregado por dois caminhos produz **dois objetos distintos e dois dicionarios `people` distintos**. Neste projeto isso significa arvore genealogica carregada em um lugar e lida em outro.

Alem disso, com `src/__init__.py` o `search-path = ["src"]` do `pyrefly.toml` passaria a apontar para **dentro** do pacote, e a resolucao de `reconstructed.*` mudaria de sentido.

## Transformacao proposta

**Nenhuma como refactor.** Esta oportunidade esta registrada para dar rastreabilidade ao pedido, e nao para ser roteada a um especialista: criar o arquivo e uma decisao de arquitetura que muda um contrato registrado, e o efeito medido e ruim.

Se o usuario quiser `src` como pacote de verdade, isso e mudanca de requisito, e nao refactor: o caminho e `/reversa-requirements` ou `/reversa-add`, que alteram a `RN-01` com registro proprio, e depois uma feature que conserte o `search-path`, o `sys.path` dos testes e a resolucao do harness na mesma mudanca.

**Recomendacao: manter como `declined`**, e a decisao fica preservada no registro.

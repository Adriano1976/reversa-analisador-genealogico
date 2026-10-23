---
schema_version: 1
id: OPP-20261023-RDME
display_number: 45
context: documentacao-do-projeto
verb: standardize
title: README desatualizado na arvore de src e na descricao da borda
target:
  files: [README.md]
  symbol: "## Estrutura do Projeto e paragrafo de arquitetura"
smell: >
  A arvore de `src/` no README e anterior a `src/web/`, a
  `src/application/projecao_analise.py` e a cinco modulos de `src/core/`
  entregues entre as features 028 e 040. O `app.py` e descrito como "5 rotas,
  despacho por 5 actions e montagem das dependencias", sem `create_app` nem o
  Blueprint de assets. A contagem de arquivos e linhas nao e reproduzivel.
roi:
  confidence: green
  impact: >
    O README e a porta de entrada do projeto. A arvore errada faz um leitor novo
    procurar `rotas_assets.py` em `reporting/` e nao encontrar `web/`, e a
    descricao da borda esconde o composition root que a FACT criou e o estado
    injetavel que a ESTD criou.
  cost: low
  est_return: >
    Arvore de `src/` e paragrafo de arquitetura alinhados ao codigo, com a
    contagem medida e o metodo declarado.
state: applied
promoted_to: null
traceability:
  soul: [.reversa/soul.md#1]
  specs: [_reversa_sdd/architecture.md, _reversa_sdd/inventory.md]
---

## Antes observado

O README descreve a estrutura do projeto em `## Estrutura do Projeto` (linha 457)
e a arquitetura em `src/app.py` (linhas 82 a 84). As duas secoes ficaram atras do
codigo.

### Defasagem medida em 2026-10-23

| Item | README hoje | Codigo atual |
|---|---|---|
| pacotes internos | `application`, `core`, `ports`, `parsers`, `reporting`, `utils` mais `app.py` | os mesmos mais `web/` |
| `app.py` | "5 rotas, despacho por 5 actions, variaveis de ambiente, guarda de instancia unica e montagem das dependencias" | `create_app(config=None, *, ...)` com quatro dependencias injetaveis e o Blueprint `assets_bp` |
| `application/` | 7 modulos | 8: falta `projecao_analise.py` |
| `core/` | 21 modulos | 26: faltam `cobertura_do_arquivo.py`, `fontes_de_laboratorio.py`, `graus_de_parentesco.py`, `qualidade_da_medida.py` e `sem_correspondencia.py` |
| `reporting/` | 4 modulos | 4, correto |
| `web/` | ausente | 2 arquivos: `rotas_assets.py` e `__init__.py` |
| contagem | "49 arquivos, 12.715 linhas nao vazias" | 55 arquivos `.py` com 11.099 linhas nao vazias; 59 arquivos no total sem cache e uploads |

A contagem do README nao e reproduzivel com o codigo atual: nao ha metodo
declarado para ela (se conta `.py` ou todos os arquivos, se inclui templates,
assets e uploads). Ela muda a cada entrega e nao protege nada.

## Transformacao proposta

1. Acrescentar `web/` a arvore, com os dois arquivos e a responsabilidade de borda
   HTTP.
2. Acrescentar `projecao_analise.py` a `application/` e os cinco modulos que faltam
   em `core/`, cada um com uma linha de descricao.
3. Reescrever a linha do `app.py` para citar `create_app`, o Blueprint `assets_bp`
   e o estado de borda injetavel.
4. Atualizar o paragrafo de arquitetura (linhas 82 a 84) para incluir `src/web/` e
   dizer que `app.py` monta a aplicacao e registra o Blueprint.
5. Trocar a contagem por uma medida com metodo declarado, ou remover a contagem se
   ela nao valer a manutencao. A proposta e declarar o metodo e medir na hora da
   edicao.

## O que fica de fora

- `_reversa_sdd/**`: e a `OPP-20261006-W4KD`, bloqueada pela config.
- O mini-site (`_reversa_docs/` e `docs/`): e do time `/reversa-docs`, e o gerador
  nao le addenda.
- Qualquer arquivo de `src/` ou `tests/`: esta oportunidade e so de documentacao.
- A contagem de testes: o README nao a declara.

## Rede de seguranca

Documentacao nao tem comportamento observavel. A prova e:

- `git diff --check` sem erro de whitespace;
- `markdownlint-cli2` se estiver disponivel no ambiente (o repositorio tem
  `.markdownlint-cli2.jsonc`);
- conferencia de que cada caminho citado na arvore existe no disco, e de que
  nenhum modulo de `src/` ficou de fora.

Nao ha teste a rodar, e nenhuma linha de codigo muda.

## Registro de aplicação (2026-10-23)

Diff aprovado e aplicado. A árvore do README foi de 46 para 54 arquivos
conferidos, com os oito que faltavam, e a contagem passou a declarar o método.

- Transformação: `transformations/OPP-20261023-RDME-readme-defasado/transformation.md`
- Diff: `.../CHG-001-readme-alinhado.diff`
- Prova: 54 arquivos conferidos e 0 faltando; suíte 1625 passed, 9 skipped; `git diff --check` limpo.
- `markdownlint-cli2` não foi executado: não há `node_modules`, e o `npx` não foi usado para baixar da rede.

---
*Gerado pelo Reversa-Refactor em 2026-10-23.*

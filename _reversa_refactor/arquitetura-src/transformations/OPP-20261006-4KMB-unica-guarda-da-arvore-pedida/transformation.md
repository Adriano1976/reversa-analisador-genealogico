---
schema_version: 1
id: OPP-20261006-4KMB
verb: restructure
state: applied
safety_net:
  kind: existing
  green_before: true
  green_after: true
preservation:
  method: tests
  evidence:
    - safety-net/resultado-suite.txt
    - safety-net/resultado-pyrefly.txt
    - before-after/pyrefly-antes.txt
    - before-after/pyrefly-depois.txt
    - CHG-001.diff
measurement:
  before: 9 linhas duplicadas em index() (2 copias das mesmas 2 guardas) e 22 linhas de mensagem literal repetida
  after: 0 guardas duplicadas; 1 funcao de modulo com as 2 guardas; 25 linhas no helper, 9 linhas removidas da rota
change_set:
  - chg: CHG-001
    file: src/app.py
    purpose: Extrai `_gedcom_do_formulario()` como fonte unica das duas guardas de entrada dos fluxos pos-upload e reduz os dois blocos copiados em `index()` a uma chamada
approval:
  by: user
  at: 2026-10-06T00:00:00Z
reversible_via: [CHG-001.diff]
---

# OPP-20261006-4KMB, guarda unica da arvore pedida

Transformação de `restructure` sobre `src/app.py`. O alvo era duplicação de nível de método dentro
de `index()`: o mesmo par de guardas de entrada (campo `gedcom_filename` ausente e chave inválida
ou expirada) aparecia antes do ramo de análise de DNA e antes do ramo de busca de caminho.

## O que mudou

| Antes | Depois |
|---|---|
| Duas cópias das mesmas duas guardas, cada uma com a sua chamada de `render_template` | Uma função de módulo, `_gedcom_do_formulario()`, fonte única das duas guardas |
| `gedcom_filename`, `gedcom_path` e as mensagens construídos em dois lugares | Os três valores devolvidos por uma única chamada |
| 9 linhas de verificação dentro da rota | 3 linhas: chamada, tratamento do erro e guarda de tipo |

A ordem dos efeitos colaterais foi preservada: `request.form.get`, a validação de forma por
`chave_recebida_e_valida`, o teste de existência em disco e a chamada de
`load_gedcom_and_build_graph` acontecem na mesma sequência e no mesmo ponto do fluxo. O helper
**não** parseia de propósito, porque o parse substitui o estado global do processo.

## Incidente registrado durante a aplicação

A primeira versão do helper devolvia `(caminho, mensagem)` e a rota deixava de definir
`gedcom_filename`. Como o template usa essa variável no campo oculto
(`src/templates/index.html:77` e `:96`), o campo sairia vazio na resposta e a requisição seguinte
perderia a árvore carregada: regressão direta no contrato de continuidade da D3 do `soul.md`.

Detectado antes de rodar a suíte, por leitura do template. Corrigido fazendo o helper devolver
também o nome recebido, que é o valor original que o formulário devolve, e não uma forma derivada
do caminho. `test_fluxo_completo_de_analise_de_dna` e `test_arvore_continua_encontravel_na_requisicao_seguinte`
são as duas redes que pegariam esse defeito.

## Segunda correção registrada

A anotação de tipo do helper introduziu um erro novo de checagem: o pyrefly não estreita o
segundo elemento de uma tupla por `erro is not None`, e `load_gedcom_and_build_graph` passava a
receber `str | None`. A contagem de erros de `src/` subiu de **27 para 28**.

Foram sondadas quatro alternativas antes de decidir, em `.pytest-tmp/tdprobe/narrow.py`:

| Sondagem | Resultado |
|---|---|
| Anotação de retorno explícita e guarda por `erro is not None` | não estreita |
| Retorno sem anotação | não estreita |
| União discriminada `tuple[str, str \| None] \| tuple[None, str]` | não estreita |
| Guarda explícita de `None` no chamador | **estreita** |

Decisão: anotação explícita mais guarda de `None` no chamador, com a guarda marcada como
inalcançável em execução, porque `erro` e `caminho` são preenchidos juntos. Resultado medido:
**27 antes, 27 depois**, com zero diferença no conjunto de erros.

## Prova

| Verificação | Antes | Depois |
|---|---|---|
| Suíte (`pytest -q`) | 164 passam, 15 erros de ambiente | **164 passam, 15 erros idênticos** |
| Verificação de tipos (`pyrefly check src`) | 27 erros | **27 erros, conjunto idêntico** |
| `git diff --stat` | — | 1 arquivo, 28 inserções, 6 remoções |
| Linhas de lógica alteradas | — | 0 |

Os 15 erros são `PermissionError` do sandbox ao criar o diretório temporário do `tmp_path`, e não
regressão: o número e a causa já constavam do `soul.md` §5 e foram reproduzidos nesta sessão com
e sem a mudança. A separação exata entre antes e depois está em `before-after/pyrefly-antes.txt` e
`before-after/pyrefly-depois.txt`, e o resultado da suíte em `safety-net/`.

## Reversão

`git apply -R _reversa_refactor/arquitetura-src/transformations/OPP-20261006-4KMB-unica-guarda-da-arvore-pedida/CHG-001.diff`

---
schema_version: 1
id: OPP-20261023-ORQA
display_number: 46
context: analise-dna
verb: restructure
title: Função dna_analysis com 553 linhas, o passo por kit inteiro dentro de um único laço
target:
  files: [src/core/dna_analysis.py]
  symbol: dna_analysis
smell: >
  A função `dna_analysis` ocupa 553 das 1.108 linhas do módulo e concentra 21
  condicionais, 4 laços, 140 chamadas e aninhamento de 4 níveis. O corpo útil é um
  único laço por kit, com 370 linhas, que executa catorze etapas de decisão do mesmo
  cartão em sequência e termina montando um dicionário de 40 chaves inline. Não é um
  laço longo por repetição: é um pipeline inteiro escrito de uma vez, sem nenhuma
  fronteira nomeada entre as etapas.
roi:
  confidence: green
  impact: >
    Hotpath por execução e por mudança. Por execução: roda uma vez por análise e o
    laço interno percorre todos os kits do CSV (a análise real tem 142 cartões). Por
    mudança: 18 commits tocaram o arquivo, com 1.283 linhas somadas e 175 removidas, e
    as últimas 12 entregas de feature acrescentaram um bloco cada uma ao mesmo corpo.
    O custo de inserir cresce a cada entrega, e o de testar em partes já é proibitivo:
    não existe forma de exercitar "o cartão de um kit" sem rodar a análise inteira.
  cost: medium
  est_return: >
    `dna_analysis` com cerca de 205 linhas, e o passo por kit com contrato nomeado,
    recebendo um objeto de contexto em vez de 18 nomes capturados do escopo. O
    mesmo comportamento observável, provado pela suíte que já existe.
state: applied
traceability:
  soul: []
  specs:
    - _reversa_sdd/analise-dna/design.md
    - _reversa_sdd/analise-dna/requirements.md
    - _reversa_sdd/adrs/24-nucleo-puro-arvore-por-parametro.md
    - _reversa_sdd/adrs/33-desfecho-em-tres-valores-e-projecao-pura.md
---

## Antes observado

`src/core/dna_analysis.py` tem **1.108 linhas**. Contagem medida por AST, nesta
sessão:

| Medida | Valor |
|---|---|
| linhas do módulo | 1.108 |
| linhas de `dna_analysis` | **553** (539-1091) |
| `if` dentro da função | 21 |
| laços | 4 |
| chamadas | 140 |
| dicionários literais | 28 |
| aninhamento máximo | 4 |
| linhas do laço por kit | **370** (682-1051) |
| chaves do dicionário de resultado | 40 (956-1051, 96 linhas) |

O laço por kit captura **18 nomes do estado da análise**, além dos auxiliares do
próprio módulo e dos tipos embutidos. Medido pela diferença entre nomes carregados e
nomes escritos no corpo do laço:

```
analisador_de_dna, ano_base, arvore, avisos_de_cartao, candidatos_fixos, deps,
documental_por_pessoa, dominio, evidencias, features, ged_index,
intervalo_de_geracao, results_list, root_id, sem_candidatos, skipped_matches,
surname_index, _dossie
```

As catorze etapas que hoje se sucedem sem nome, todas no mesmo nível:

1. mitigação de endogamia do kit (690-692)
2. casamento de nome e cM (696-697)
3. promoção manual do descarte (702-706)
4. recusa e montagem do descarte (712-755)
5. escolha do parentesco documental entre candidatos (762-771)
6. diagnóstico de endogamia estrutural (779-820)
7. identidade do match (826-827)
8. janela de vida e a regra do operador (832-855)
9. confronto (861-863)
10. profundidade do caminho e anotação do diagrama (874-898)
11. rótulo efetivo do confronto (906-913)
12. veredito de validação (920-926)
13. árvore sugerida (938-944)
14. montagem do cartão (956-1051)

## Por que o retorno é alto

Duas medidas, não uma opinião:

- **frequência de execução**: a análise percorre todos os kits do arquivo, e o
  caminho real de 2026-10 tem 142 cartões;
- **frequência de mudança**: `git log` do arquivo mostra 18 commits e, nas últimas
  12 entregas, 12 features que acrescentaram um bloco cada uma dentro do mesmo
  laço. A décima terceira vai precisar do mesmo lugar.

A função é o ponto onde toda feature nova encosta. É exatamente o alvo que o
critério de ROI do registro prefere: código que combina alta frequência de execução
com alta taxa de mudança.

## Transformação proposta

Extrair o passo por kit para uma função própria, com um contexto explícito em vez
de 18 nomes capturados. Duas formas possíveis, na ordem de preferência:

**A. Objeto de contexto congelado (recomendada).**

```python
@dataclass(frozen=True, slots=True)
class _ContextoDaAnalise:
    arvore: ...          # a tupla (pessoas, familias, grafo)
    root_id: str
    deps: Dependencias
    ged_index: dict
    surname_index: dict
    features: ...
    dominio: dict
    ano_base: int
    intervalo_de_geracao: int
    analisador: DNAAnalyzer
    candidatos_fixos: dict
    avisos_de_cartao: list
    documental_por_pessoa: dict   # cache entre kits, por isso nao e constante
```

`_cartao_do_kit(contexto, chave_nome, por_kit, chave_kit, kit)` devolveria o
cartão pronto, ou um marcador de "sem candidatos" que o chamador transforma em
descarte e em cartão sem correspondência. O `continue` da linha 755 vira o retorno
desse marcador.

**B. Função com dezoito parâmetros.** Faz o mesmo corte, mas troca uma captura
implícita por uma assinatura de 18 posições, que é a definição de acoplamento por
assinatura. Fica registrada como alternativa, e não como recomendação.

### Precedente dentro do próprio núcleo

A forma A não é importação de paradigma de fora. `src/core/endogamia.py` já usa
`@dataclass(frozen=True, slots=True)` em cinco value objects (`EvidenciaMitigada`,
`DiagnosticoDeEndogamia`, `Reconvergencia`, `CorrespondenciaDeNome`,
`AnaliseDeEndogamia`) e uma classe de serviço (`DNAAnalyzer`), todos sem estado
mutável de domínio. O contexto proposto é a mesma forma, no mesmo pacote.

Isso mantém a decisão de `_reversa_sdd/migration/paradigm_decision.md` intacta: o
que ela recusa é *"reificar o matching viral e a busca de caminho como objetos com
estado"*, e o contexto aqui é um invólucro congelado de entradas, não um agregado
com invariantes nem um algoritmo virando objeto.

## Fronteira de comportamento

Nenhuma regra muda de lugar lógico. O diff é estrutural: o mesmo código, na mesma
ordem, com um escopo nomeado. A ordem de apresentação (`_ordem`, 1076-1080) e a
assinatura pública de `dna_analysis` **não** mudam.

## Rede de segurança

A suíte existente cobre o fluxo inteiro, inclusive a caracterização do oráculo
(`tests/test_characterization_matching.py`) e o confronto GEDCOM x DNA. Medição
desta sessão, antes de qualquer escrita: **1625 passed, 9 skipped em 105,64 s**.
O gate exige a mesma contagem depois.

## O que fica de fora

- A divisão do módulo em arquivos menores é `OPP-20261023-CTAO`, e rende mais depois
  deste corte, porque o passo por kit já vai existir como função.
- `_ordem` continua aqui. `_reversa_sdd/analise-dna/design.md` ancora a decisão
  "ordem documental-primeiro" em `core/dna_analysis.py:_ordem`, e a spec não está em
  caminho liberado pela config.

## Resultado da aplicação

Aplicada em 2026-10-23, sob gate de plano e de diff aprovados, em duas partes:
`CHG-001` no módulo e `CHG-002` na guarda de teste que a movimentação quebrou.

| Medida | Antes | Depois |
|---|---|---|
| `dna_analysis` | 539 linhas | **205** |
| condicionais | 21 | 13 |
| nomes capturados do escopo | 18 | 0 |
| `_cartao_do_kit` | não existia | 368 linhas, 5 parâmetros |

A estimativa desta oportunidade dizia "cerca de 140 linhas" para `dna_analysis`.
O número real é **205**: o trecho anterior ao laço, que monta raiz, CSV, avisos,
evidências e índices, são 115 linhas que continuam na função.

Suíte: **1625 passed, 9 skipped**, antes (106,01 s) e depois (108,78 s). Digest de
equivalência idêntico em três cenários. O registro completo está em
`../transformations/OPP-20261023-ORQA-fluxo-de-553-linhas-sem-fronteira/transformation.md`.

O corpo de `_cartao_do_kit` continua com as catorze etapas encadeadas. A
decomposição interna virou a `OPP-20261023-ETAP`, porque só ficou barata depois
deste corte.

---
*Gerado pelo Reversa-Refactor em 2026-10-23. Aplicada no mesmo dia.*

<!-- GENERATED, DO NOT EDIT: regenerado por /reversa-refactor em 2026-10-24 a partir de 9 oportunidades -->
<!-- Atualizado a mao em 2026-10-01: OPP-20260929-5XGJ, OPP-20260929-UXEF e OPP-20260929-H2YY passaram a applied. O gerador nao foi reexecutado. -->

# Índice de qualidade de código · busca-caminho

> Gerado em `2026-10-24`. Fonte de verdade: `../opportunities/*.md`.
> Evidência da medição: `medir_documental.py` a `medir_documental4.py`, nesta pasta. Leem o
> repositório e não escrevem nada.

## Oportunidades

| # | ID | Verbo | Confiança | Impacto | Custo | Estado | Retorno esperado |
|---|----|-------|-----------|---------|-------|--------|------------------|
| #5 | `OPP-20260929-TPSH` | restructure | green | risco de correção pela metade | low | applied | uma única autoridade de escape e de id de nó, eliminando a divergência em curso |
| #15 | `OPP-20260929-5XGJ` | standardize | green | quem lê precisa entender por que três formatos coexistem, e um deles tem supressão de aviso | low | applied | uma única regra de import no arquivo, com o motivo escrito |
| #6 | `OPP-20260929-UXEF` | modularize | yellow | acoplamento e testabilidade | medium | applied | busca testável sem render, e o render isolado como o ponto onde o escape vive |
| #7 | `OPP-20260929-H2YY` | simplify | yellow | clareza e risco de alteração | medium | applied | mesma string gerada, com a estrutura do diagrama legível em nível de bloco |
| #52 | `OPP-20261024-CACH` | decouple | yellow | único estado de módulo do arquivo, janela de corrida entre threads | low | **applied** | um mecanismo de memoização com troca atômica e o mapa devolvido da variável local |
| #53 | `OPP-20261024-SEPM` | modularize | yellow | 782 linhas com cinco assuntos que só compartilham a árvore | medium | **applied** | quatro ou cinco módulos de 80 a 130 linhas, fachada com os dezoito nomes |
| #54 | `OPP-20261024-FLUX` | restructure | green | função de 102 linhas com quatro blocos de aviso no meio | medium | **applied** | seis etapas nomeadas e o cartão montado no fim |
| #55 | `OPP-20261024-DUPL` | simplify | green | a mesma varredura escrita duas vezes, para DATE e para PLAC | low | **applied** | uma varredura parametrizada e a regra "primeira família que liga" com nome |
| #56 | `OPP-20261024-SUPR` | standardize | green | quatro nomes em `__all__` sem um único consumidor | low | **applied** | `__all__` com catorze nomes, cada um com importador verificado |

## Transformações

| OPP | Estado | Plano | Diff proposto | Rede de segurança |
|-----|--------|-------|---------------|-------------------|
| `OPP-20260929-TPSH` | aplicada | `plan.html` | sim | 5 artefato(s) |
| `OPP-20260929-5XGJ` | aplicada | - | sim | 2 artefato(s) |
| `OPP-20260929-UXEF` | aplicada | `plan.html` | sim | 8 artefato(s) |
| `OPP-20260929-H2YY` | aplicada | `plan.html` | sim | 12 artefato(s) |
| `OPP-20261024-CACH` | **aplicada em 2026-10-24** | `plan.html` | `CHG-001.diff` (19 inserções, 24 remoções) e `CHG-002` (arquivo novo) | prova do defeito antes, guardas estruturais depois, suíte 1635/9 |
| `OPP-20261024-DUPL` | **aplicada em 2026-10-24** | `plan.html` | `CHG-001.diff` (30 inserções, 27 remoções) | equivalência em 86.497 casos com controle negativo, suíte 1635/9 |
| `OPP-20261024-FLUX` | **aplicada em 2026-10-24** | `plan.html` | `CHG-001.diff` (108 inserções, 67 remoções) | equivalência em 3.928 casos com os 6 códigos de aviso, suíte 1635/9 |
| `OPP-20261024-SEPM` | **aplicada em 2026-10-24** | `plan.html` | `CHG-001.diff` (545 inserções, 457 remoções) e `CHG-002.diff` (12 inserções, 11 remoções) | equivalência em 3.928 casos e superfície da fachada, suíte 1635/9 |
| `OPP-20261024-SUPR` | **aplicada em 2026-10-24** | `plan.html` | `CHG-001.diff` (7 inserções, 6 remoções) | superfície dos 14 nomes e dos 4 retirados, suíte 1635/9 |

## Auditoria de 2026-10-24: as quatro configurações em `core/documentary_relationship.py`

Pedido do usuário: verificar orientação a objeto, padrão de projeto, alta coesão e baixo
acoplamento em `src/core/documentary_relationship.py`, achar função sem utilidade, limpar
o código e dividir em módulos menores. O arquivo tem **782 linhas**, 26 funções, 593
linhas dentro de `def`.

| Configuração | Situação | Evidência medida |
|---|---|---|
| Orientação a objeto | 🔴 ausente por decisão | zero `class`; a única estrutura nomeada é `_CacheDeNomes`, um `TypedDict`. O padrão do núcleo é função pura recebendo a tupla `arvore` |
| Padrão de projeto | 🟡 parcial e inconsistente | três padrões reais: Cache (duas implementações diferentes para o mesmo problema), Facade (`__all__` com reexport) e contrato de forma entre os dois construtores de cartão. Nenhuma fábrica, estratégia ou injeção |
| Alta coesão | 🔴 baixa no módulo | cinco assuntos independentes; o arquivo tem cinco razões para mudar. As funções, individualmente, são pequenas: 22 das 26 têm 51 linhas ou menos |
| Baixo acoplamento | 🟡 com um ponto 🔴 | fan-out de 5 módulos do projeto e 4 da biblioteca padrão; fan-in de **15** módulos de `src/`. O ponto 🔴 é `_INDICE_DE_NOMES`, estado de módulo compartilhado por todas as requisições |

### A função sem utilidade não existe

As 26 funções e classes têm chamador. O que a varredura encontrou foi peso morto de outra
natureza, e ele está medido:

| Item | Medição | Encaminhamento |
|---|---|---|
| `ROMANO` e `MAX_DEPTH` em `__all__` | zero importações de qualquer lugar do repositório | `OPP-20261024-SUPR` |
| `hop_evidence` e `find_all_common_ancestors` em `__all__` | zero importações externas; uso só interno | `OPP-20261024-SUPR` |
| `link_source`, `family_husband`, `family_wife` | escritos em `hop_evidence` e lidos zero vezes em `src/`, `tests/` e templates | **não roteável**: contrato em `data-dictionary.md:335,338`, `BR-C-48` e `T-18` |
| variação de chaves entre o ramo de sucesso e o de não encontrado | 16 chaves no caminho encontrado, 4 no de pessoa ausente | fora do escopo, já registrado em `OPP-20261006-YTSH` |

### O que a auditoria NÃO registra como refactor

| Item pedido | Situação | Encaminhamento |
|---|---|---|
| Orientação a objeto no núcleo | Ausente por decisão: `paradigm_decision.md` proíbe aggregates com estado no núcleo de cálculo | `_reversa_sdd/migration/` (alvo) |
| Nomear a tupla `arvore` como `NamedTuple` | Seria a única forma de OO compatível com o contrato atual (subtipo de `tuple`; 56 acessos posicionais em `src/`, 27 deles neste arquivo) | mesma família de `OPP-20261006-YTSH`, que recomenda não rotear |
| Tipos de domínio para as 16 chaves do cartão | Mudam comportamento observável | `OPP-20261006-YTSH`, `proposed` |

### Dívida de documentação criada ou encontrada

| Artefato | Afirmação | Situação real |
|---|---|---|
| `_reversa_sdd/busca-caminho/design.md:210` | "`get_children` varre todas as famílias, **sem índice**" | existe índice, preso ao grafo, desde `7799304` |
| `_reversa_sdd/flowcharts/busca-caminho.md:395` e `busca-caminho/tasks.md:146` | `_diferencas` é chamado duas vezes e remonta as fichas | chamado uma vez desde a correção registrada no próprio código |
| `_reversa_sdd/busca-caminho/requirements.md:173` | mesma dívida de performance | idem |

Os três caminhos estão em `_reversa_sdd/**`, fora dos globs liberados pela config, e por
isso não foram roteados. É o mesmo bloqueio da `OPP-20261006-W4KD`.

### `CACH`, aplicada em 2026-10-24

O índice de nomes deixou de ser um dicionário de dois campos escritos em dois tempos e
passou a ser a tupla `(chave, mapa)`, publicada por uma atribuição e devolvida da
referência lida uma vez. Saíram o `TypedDict _CacheDeNomes` e o import de `TypedDict`.

| Medida | Antes | Depois |
|---|---|---|
| Objetos mutáveis de módulo | 1 | 0 |
| Campos publicados independentemente | 2 | 0 |
| Leituras do global por chamada | 2 | 1 |
| Releituras depois da escrita | 1 | 0 |
| Guardas sobre a janela | 0 | 3 estruturais + 1 de invariante |
| Suíte | 1629 passam, 9 pulados | **1635 passam, 9 pulados** |

O defeito foi provado antes da correção: a thread A, que pediu a árvore Alfa, recebeu os
três registros Beta. A prova e o `CHG-001.diff` estão em
[`transformations/OPP-20261024-CACH-cache-de-nomes-global/`](../transformations/OPP-20261024-CACH-cache-de-nomes-global/).

### `DUPL`, aplicada em 2026-10-24

`_data_de` e `_local_de` eram a mesma função de dez linhas com uma constante trocada. Agora
há `_sub_valor` com a varredura única, e as duas viraram uma linha de corpo cada. Em
`hop_evidence`, os dois laços de "qual família liga esta pessoa a este genitor" viraram
`_familia_que_liga`, e o conjunto de pais ganhou nome em `_pais_da_familia`.

| Medida | Antes | Depois |
|---|---|---|
| Linhas para ler data e local | 20 | 14 |
| Laços "primeira família que liga" | 2 | 1 |
| Linhas de `hop_evidence` até a evidência | 21 | 8 |
| Casos de equivalência comparados | 0 | 86.497, com 0 divergência |
| Suíte | 1635 passam, 9 pulados | 1635 passam, 9 pulados |

O `_casal_da_familia` que a oportunidade previa foi **descartado na aplicação**, com a
medição: teria mais linhas do que as quatro leituras que substituiria.

### `FLUX`, aplicada em 2026-10-24

`documentary_relationship` tinha 102 linhas, três laços e quatro blocos de aviso, cada um
montando a mensagem no meio do percurso. Virou uma sequência de oito passos nomeados, com 54
linhas. A mensagem de homônimo, que existia aqui e em `documental_nao_encontrado`, passou a
existir uma vez só.

| Medida | Antes | Depois |
|---|---|---|
| Linhas de `documentary_relationship` | 102 | **54** |
| Blocos `if ...: avisos.append({...})` | 4 | 0 |
| Lugares com a mensagem de homônimo | 2 | 1 |
| Comparações de equivalência | 0 | 3.928, com 0 divergência |
| Suíte | 1635 passam, 9 pulados | 1635 passam, 9 pulados |

Os seis códigos de aviso foram exercitados na prova: `caminhos_multiplos` 2.941, `homonimo`
2.815, `sem_caminho` 440, `data_impossivel` 250, `colapso_de_pedigree` 148 e `pessoa_ausente`
4. Uma diferença injetada de propósito foi acusada em 3.844 casos.

### `SEPM`, aplicada em 2026-10-24

O arquivo de 821 linhas virou quatro módulos de responsabilidade única e uma fachada. Nenhum
dos quatro passa de 154 linhas, e a fachada ficou com 406: o cartão, os avisos e as
reexportações que os quinze consumidores já importavam.

| Módulo | Linhas |
|---|---|
| `core/datas_do_gedcom.py` | 135 |
| `core/fichas_da_pessoa.py` | 98 |
| `core/homonimos.py` | 154 |
| `core/caminhos_alternativos.py` | 116 |
| `core/documentary_relationship.py` | 406 |

Duas funções privadas viraram públicas ao atravessar a fronteira: `_ids` para `ids_com_tag`,
`_local_de` para `birth_place`. Dois testes mudaram de endereço, nenhuma asserção mudou. A
equivalência foi reexecutada sobre o código dividido: 3.928 comparações, zero divergência.

### `SUPR`, aplicada em 2026-10-24

Fechou a série. Quatro dos dezoito nomes de `__all__` não tinham um único importador no
repositório: `hop_evidence`, `find_all_common_ancestors`, `ROMANO` e `MAX_DEPTH`. Saíram do
anúncio, e o comentário da reexportação passou a citar só `nome_do_grau`, que dois testes
importam daqui.

Nenhum import foi tocado: os quatro nomes continuam no módulo e continuam importáveis por
nome. `death_date` e `get_children` ficaram, com consumidor real ainda que congelado em
`_reversa_bugs/`.

### Ordem de encadeamento sugerida

| Ordem | Oportunidade | Por quê nesta posição |
|---|---|---|
| ~~1~~ | ~~`OPP-20261024-CACH`~~ | **aplicada em 2026-10-24.** Fechou a janela de corrida sem depender de mais nada |
| ~~2~~ | ~~`OPP-20261024-DUPL`~~ | **aplicada em 2026-10-24.** Deixou menos linhas para mover na etapa seguinte |
| ~~3~~ | ~~`OPP-20261024-FLUX`~~ | **aplicada em 2026-10-24.** Deixou a função recortada para a divisão em módulos |
| ~~4~~ | ~~`OPP-20261024-SEPM`~~ | **aplicada em 2026-10-24.** Fechou a divisão, com a fachada preservando os endereços |
| ~~5~~ | ~~`OPP-20261024-SUPR`~~ | **aplicada em 2026-10-24.** Anunciou só o que tem consumidor |
| 2 | `OPP-20261024-DUPL` | simplify de baixo custo; deixa menos linhas para mover na etapa seguinte |
| 3 | `OPP-20261024-FLUX` | restructure antes do modularize, para que os módulos novos já nasçam com as etapas separadas |
| 4 | `OPP-20261024-SEPM` | com as etapas nomeadas, a divisão vira recorte, não reescrita |
| 5 | `OPP-20261024-SUPR` | fica mais preciso depois que a `SEPM` decidir a superfície de cada módulo |

## Fechamento da auditoria: as mesmas quatro configurações, medidas de novo

As cinco oportunidades foram aplicadas em 2026-10-24. Medição de fechamento em
`generated/medir_fechamento.py`:

| Configuração | Na abertura | No fechamento |
|---|---|---|
| Orientação a objeto | zero `class` em 782 linhas | zero `class` nos cinco arquivos: continua ausente por decisão do `paradigm_decision.md` |
| Padrão de projeto | Cache com dois mecanismos, um com janela de corrida; Facade com 18 nomes | Cache com um mecanismo (par imutável trocado por atribuição); Facade com 14 nomes, todos com consumidor |
| Alta coesão | 5 assuntos em 1 arquivo; maior função com 102 linhas | 5 arquivos, 1 assunto cada; maior função com 54 linhas |
| Baixo acoplamento | 1 estado de módulo com 2 campos escritos em 2 tempos | 1 estado de módulo, em `homonimos.py`, com troca atômica; zero ciclo entre os cinco |

| Arquivo | Linhas | Funções | Maior função |
|---|---|---|---|
| `documentary_relationship.py` | 407 | 14 | 54 |
| `homonimos.py` | 154 | 5 | 26 |
| `datas_do_gedcom.py` | 135 | 8 | 49 |
| `caminhos_alternativos.py` | 116 | 5 | 22 |
| `fichas_da_pessoa.py` | 98 | 5 | 28 |
| **total** | **910** | **37** | **54** |

**Correção de uma medição da abertura:** o número "15 módulos consomem o arquivo" vinha de
menção textual. Por AST, **10 módulos de `src/` importam** de `documentary_relationship`, e
outros 9 citam o nome em docstring ou leem chave do dicionário sem importar.

## Legenda

- Confiança: 🟢 coberto e entendido | 🟡 parcial | 🔴 sem prova de comportamento
- Custo: `low` | `medium` | `high`
- Estado: `proposed` | `approved` | `applied` | `reverted` | `declined`

---
*Gerado pelo Reversa-Refactor em 2026-10-24.*

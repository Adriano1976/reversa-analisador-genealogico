# Legacy Impact: cache dos índices derivados da árvore

> Feature: `047-cache-dos-indices-da-arvore`
> Data: `2026-10-24`
> Política de edição do legado: `allowLegacyEdits: true`, com `src/**`, `tests/**` e
> `docker-compose.yml` na lista de caminhos liberados (`.reversa/reversa-config.json`)

## Arquivos afetados

| Arquivo afetado | Componente | Tipo | Severidade | Justificativa |
|---|---|---|---|---|
| `src/ports/adaptadores.py` | `CarregadorDeArvoresGedcom` (camada Portas) | `regra-alterada` | **HIGH** | Passa a manter uma árvore em memória entre requisições; muda a propriedade "sem cache entre requisições" que `architecture.md#1` declarava |
| `src/core/matching.py` | `build_ged_indexes` (unit `analise-dna`) | `regra-alterada` | MEDIUM | O trio de índices passa a ser memoizado no grafo da árvore; mesmo resultado, custo de reconstrução menor |
| `tests/test_cache_de_arvores.py` | — (teste) | `componente-novo` | LOW | 18 testes de presença, invalidação, teto, concorrência e log |
| `tests/test_indices_de_matching_memo.py` | — (teste) | `componente-novo` | LOW | 7 testes de memo e de não-contaminação entre árvores |
| `docker-compose.yml` | empacotamento | `delta-de-contrato-externo` | LOW | Duas variáveis de ambiente documentadas e ligadas por padrão (rev. 2026-10-26) |

## Diff conceitual por componente

**`CarregadorDeArvoresGedcom`.** Antes, cada `carregar` chamava `carregar_arvore` e pagava o parse.
Agora ele pode guardar a última árvore, chaveada por `(caminho, mtime_ns, tamanho)`, com teto 1 e
*single-flight*. A porta não mudou: mesma assinatura, mesmo retorno, `None` para referência
inexistente. O que mudou é **quando** o parse acontece — e o cache está **ligado por padrão** desde
a revisão de 2026-10-26, desligável por `ANALISADOR_CACHE_DE_ARVORE=0`.

**`build_ged_indexes`.** Antes, toda chamada percorria as 19.403 pessoas e custava ~9 s. Agora o
trio fica preso ao objeto do grafo, como `fichas_da_pessoa._indice_de_filhos` já fazia com o
índice de filhos. Nenhuma chave derivada de conteúdo é usada — é isso que impede a repetição do
defeito `L-24`. O trio é o mesmo objeto, e os consumidores só leem.

## Regras preservadas

- Separação dos três eixos (documental, genético, possibilidades) e o confronto em quatro estados.
- Ordem de apresentação dos resultados e o desempate determinístico pelo menor `xref_id`.
- Limiares de matching (`HARD_MIN`, `GIVEN_MIN`), pesos e bônus de sobrenome.
- Regra 2 do adendo `bug-BUG-20261021-7O7V-v001`: índice derivado sem chave que possa colidir.
- `L-24` no cache de nomes do módulo documental: **intocado**, segue na correção agendada.
- Contrato de `POST /`: mesmo formulário, mesmo status, mesmo HTML (provado por `sha256`).

## Regras modificadas

- **"Não há cache entre requisições"** (`architecture.md#1`): passa a haver, opcional e limitado,
  para a árvore e seus derivados. O resto do sistema continua sem cache.
- **Item "O que NÃO muda"** do adendo `bug-BUG-20261021-7O7V-v001`: superado pela decisão de
  2026-10-24. A regra 2 do mesmo adendo permanece.
- **`build_ged_indexes`**: deixa de reconstruir a cada chamada e passa a reconstruir uma vez por
  árvore, com o memo morrendo junto com ela.

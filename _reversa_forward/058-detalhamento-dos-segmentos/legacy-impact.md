# Legacy Impact: detalhamento dos segmentos compartilhados

> Identificador: `058-detalhamento-dos-segmentos`
> Data: `2026-11-11`
> Política de edição do legado no momento da execução: `allowLegacyEdits: true`, com
> `allowedPaths` liberando `src/**`, `tests/**` e `README.md` — todos os caminhos desta feature
> estão cobertos pela lista.

## Arquivos afetados

| Arquivo afetado | Componente | Tipo | Severidade | Justificativa |
|-----------------|------------|------|------------|---------------|
| `src/core/segmentos.py` (novo) | `analise-dna` | `regra-nova` | MEDIUM | Achata as regiões em uma linha por par (região, kit), com ordem fixa e o índice da região |
| `src/application/segmentos.py` (novo) | `analise-dna` (projeção) | `componente-novo` | LOW | Projeta as linhas (`extensao_mb`, `chave_de_busca`) e lista os cromossomos do filtro |
| `src/application/regioes.py` | projeção das regiões | `delta-de-dados` | MEDIUM | Cada região ganha `indice` (1-based), usado como âncora `regiao-N` |
| `src/core/distribuicao.py` | `analise-dna` | `regra-alterada` | LOW | `ordem_do_cromossomo` passou a ser pública, para não haver terceira cópia da ordem; comportamento idêntico |
| `src/app.py` | borda | `delta-de-contrato-externo` | LOW | Projeta os segmentos e passa `segmentos` e `cromossomos_dos_segmentos` ao template |
| `src/templates/index.html` | tela de resultado | `regra-alterada` | MEDIUM | Seção da tabela, `id` nas faixas do ideograma e o script de filtro/paginação/cópia |
| `src/assets/app.css` | tela de resultado | `regra-alterada` | LOW | Estilos da tabela, `:target` da faixa, `scroll-margin` e regra de impressão |
| `tests/test_segmentos.py` (novo) | testes | `componente-novo` | LOW | Cobre `RN-02`, `RN-03`, `D-02` e a projeção |
| `tests/test_contrato_dos_segmentos.py` (novo) | testes | `componente-novo` | LOW | Posição, contador, colunas, par linha↔faixa e ausência sem região |
| `tests/test_contrato_das_regioes.py` | testes | `regra-alterada` | LOW | Prende o `indice` na projeção e o `id="regiao-N"` no ideograma |
| `README.md` | documentação | `regra-alterada` | LOW | O item "Regiões compartilhadas" passa a descrever a tabela |

## Diff conceitual por componente

**`analise-dna` (núcleo).** Nada do fluxo de análise muda: matching, cM, ordem dos cartões e
confronto idênticos. Nasce um achatamento **derivado** das regiões: uma linha por (região, kit), com
ordem determinística e o índice da região. O `ordem_do_cromossomo` deixou de ser privado em
`core/distribuicao.py` para ser reaproveitado — mesmo algoritmo, mesmo resultado.

**Projeção.** `application/regioes.py` acrescenta `indice` (o CSV não muda: escreve colunas
explícitas). `application/segmentos.py` deriva `extensao_mb` e a `chave_de_busca` sem acento, e
devolve os cromossomos na ordem da tabela, que é a ordem do filtro.

**Tela.** A seção entra entre a distribuição e a lista, com toolbar, tabela semântica de sete
colunas e paginação. A faixa do ideograma ganha `id="regiao-N"`; o clique na linha usa `location.hash`
e o destaque é `:target`, sem JavaScript. O script da tabela esconde linhas, atualiza o contador e
copia a linha — tudo sobre o HTML já servido.

**O que NÃO mudou:** `src/parsers/`, `src/ports/`, `src/core/regioes.py`, `src/reporting/csv_das_regioes.py`,
o esquema PostgreSQL, as rotas existentes e o `/regioes.csv`.

## Preservadas

Regras 🟢 do `_reversa_sdd/domain.md` que continuam intactas:

- `#2` — os três eixos não se contaminam: a tabela mostra, não decide.
- `#3.2` — evidência genética: o cM é do segmento e continua não sendo somado.
- `#3.9` — ordem de apresentação dos resultados: os cartões não são reordenados pela tabela.
- `#5` — contrato de mensagens: nenhuma mensagem existente mudou.

## Modificadas

Nenhuma regra 🟢 de domínio foi alterada ou removida. A feature **acrescenta** uma leitura derivada e
uma chave de apresentação, e o que existia continua com o mesmo comportamento — coberto pelos testes
que já estavam verdes antes dela (`SHA_DA_TELA` inclusive, que voltou ao valor anterior depois de o
script ser movido para dentro do `{% if %}`).

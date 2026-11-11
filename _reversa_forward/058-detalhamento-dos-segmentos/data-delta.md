<!--
Delta de dados da feature 058 — Detalhamento dos segmentos compartilhados.
Diff conceitual sobre o modelo extraído em _reversa_sdd/.
-->

# Delta de dados: detalhamento dos segmentos compartilhados

> Identificador: `058-detalhamento-dos-segmentos`
> Data: `2026-11-11`
> Base comparada: `_reversa_sdd/data-dictionary.md` (extração de 2026-10-10) + adendos 056 e 057

## 1. Veredito curto

A feature **não cria tabela, não muda o esquema PostgreSQL e não persiste nada**. Ela achata as
regiões em linhas de segmento, na memória, e acrescenta duas chaves de apresentação: o índice da
região (âncora) e o próprio dicionário da linha. O `/regioes.csv` continua com uma linha por região.

## 2. Tipo novo no domínio

| Item | Antes | Depois |
|------|-------|--------|
| `src/core/segmentos.py` | não existe | `SegmentoDeRegiao` (`frozen=True, slots=True`) |
| Campos | — | `regiao_indice: int` (1-based), `cromossomo: str`, `inicio: int`, `fim: int`, `cm: float`, `kit: str`, `nome: str`, `desfecho: str`, `desfecho_chave: str` |
| Derivação | — | `segmentos_das_regioes(regioes) -> tuple[SegmentoDeRegiao, ...]` |
| Ordem | — | cromossomo em ordem natural, depois `inicio`, depois `kit` (`RN-03`) |

`regiao_indice` é o **vínculo com a faixa do ideograma**: nasce na posição da região na lista
recebida e sobrevive à ordenação da tabela. Sem ele, a linha não teria como apontar para a faixa
certa quando duas regiões caem no mesmo cromossomo.

`extensao_mb` **não** entra no dataclass: é derivada de `fim - inicio` na projeção, como a região já
faz, para não existirem duas fontes do mesmo número.

## 3. Chave nova na projeção de regiões

| Item | Antes | Depois |
|------|-------|--------|
| `application.regioes.projetar_regioes` | 17 chaves | 18 chaves |
| Chave nova | — | `indice: int` (1-based, posição da região na lista projetada) |
| Consumidores | template (lista, ideograma), `csv_das_regioes` | idem + o `id="regiao-N"` da faixa e a tabela |

O CSV **não muda**: `src/reporting/csv_das_regioes.py` escreve colunas explícitas, não despeja o
dicionário.

## 4. Projeção da tabela

| Item | Antes | Depois |
|------|-------|--------|
| `src/application/segmentos.py` | não existe | `projetar_segmentos(segmentos) -> list[dict]` |
| Chaves | — | `regiao` (o `regiao_indice`), `cromossomo`, `inicio`, `fim`, `extensao_mb`, `cm`, `kit`, `nome`, `desfecho`, `desfecho_chave` |
| Regra | — | Não formata número (o template formata) e não reordena (a ordem vem do núcleo) |

## 5. Contexto do template

| Item | Antes | Depois |
|------|-------|--------|
| `render_template("index.html", ...)` | `regioes`, `regioes_dados`, `ideograma`, `grafico_da_distribuicao` | + `segmentos` |
| Marcação | — | `<section class="segmentos">` com título, contador, toolbar, tabela e paginação |
| Âncora | — | A faixa do ideograma passa a ter `id="regiao-N"` |

## 6. Persistência e esquema

| Item | Situação |
|------|----------|
| Tabelas novas | nenhuma |
| Colunas novas | nenhuma |
| Migração | não se aplica |
| Histórico | não se aplica (a tabela é leitura derivada) |

## 7. Compatibilidade

| Consumidor | Impacto |
|------------|---------|
| `POST /` (tela de resultado) | Ganha marcação e um `<script>`; nenhum campo de formulário novo |
| `POST /regioes.csv` | Nenhuma coluna nova; mesmas linhas |
| `GET /` (tela de entrada) | Nenhum byte: `SHA_DA_TELA` inalterado |
| `montar_ideograma` | Passa a receber `indice` (já repassa chaves do item); o `id` é emitido no template |
| Testes de caracterização | Nenhuma saída existente muda de valor |

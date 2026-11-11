<!--
Delta de dados da feature 057 — Distribuição por cromossomo.
Diff conceitual sobre o modelo extraído em _reversa_sdd/.
-->

# Delta de dados: Distribuição por cromossomo

> Identificador: `057-distribuicao-por-cromossomo`
> Data: `2026-11-10`
> Base comparada: `_reversa_sdd/data-dictionary.md` (extração de 2026-10-10) + adendo 056

## 1. Veredito curto

A feature **não cria tabela, não altera o esquema PostgreSQL e não persiste nada**. Ela acrescenta
um tipo de domínio em memória e um campo no payload do caso de uso, ambos derivados das regiões que
a 056 já calcula. O que o operador vê é a mesma análise, agregada de outro jeito.

## 2. Tipo novo no domínio

| Item | Antes | Depois |
|------|-------|--------|
| `src/core/distribuicao.py` | não existe | `ResumoDoCromossomo` (`frozen=True, slots=True`) |
| Campos | — | `cromossomo: str`, `kits: tuple[str, ...]`, `cm_medio: float` |
| Invariante | — | `cm_medio` é média aritmética simples do **segmento escolhido de cada kit** (o de maior cM, desempate pelo menor início — `D-12`); nunca soma |
| Derivação | — | `distribuicao_por_cromossomo(regioes) -> tuple[ResumoDoCromossomo, ...]`, em ordem natural de cromossomo |

Por que `kits` é tupla e não contagem: a deduplicação é a regra (`RN-02`); guardar a tupla deixa o
teste verificar **quais** kits entraram, e a contagem é `len(kits)` na projeção. Não existe campo
separado de "segmentos": com `D-12`, cada kit contribui com exatamente um segmento, então o número
de observações é `len(kits)` por construção.

## 3. Campo novo no payload do caso de uso

| Item | Antes | Depois |
|------|-------|--------|
| `application.dna_analysis.ResultadoDeAnalise` | `regioes: tuple = ()` (056) | `regioes: tuple = ()` + `distribuicao: tuple = ()` |
| Origem do valor | `dna_analysis` do núcleo preenche `regioes` | `application/dna_analysis.py` chama `distribuicao_por_cromossomo` sobre as regiões já classificadas, em `try/except` |
| Default | `()` | `()` — objeto montado à mão (testes, chamadas antigas) continua válido |

`_reversa_sdd/data-dictionary.md#8.2` passa a ter duas linhas novas quando o `/reversa-sync` rodar;
até lá, esta é a fonte do delta.

## 4. Projeção para a tela

| Item | Antes | Depois |
|------|-------|--------|
| `src/application/distribuicao.py` | não existe | `projetar_distribuicao(resumos) -> list[dict]` |
| Chaves do dicionário | — | `cromossomo`, `kits` (int), `cm_medio` |
| Regra | — | Não formata número e não calcula geometria (mesma regra de `projetar_regioes`) |

## 5. Desenho

| Item | Antes | Depois |
|------|-------|--------|
| `src/reporting/distribuicao.py` | não existe | `montar_distribuicao(itens) -> dict` |
| Saída | — | `{"eixo_matches": {...}, "eixo_cm": {...}, "colunas": [...]}` |
| Por coluna | — | `cromossomo`, `kits`, `cm_medio`, `altura_matches` (%), `altura_cm` (%), `lado` (para o cartão) |
| Por eixo | — | `topo`, `passo`, `marcas` (lista de valores, de zero ao topo) |

Os percentuais são **de desenho**: `altura = 100 × valor / topo`. Nenhum número do domínio é
alterado; o eixo volta ao valor real na marca e no cartão.

## 6. Persistência e esquema

| Item | Situação |
|------|----------|
| Tabelas novas | nenhuma |
| Colunas novas | nenhuma |
| Migração | não se aplica |
| Histórico | não se aplica (o gráfico é leitura derivada; a análise continua sendo registrada como hoje) |

## 7. Compatibilidade

| Consumidor | Impacto |
|------------|---------|
| `POST /` (tela de resultado) | Ganha marcação; nenhum campo de formulário novo |
| `POST /regioes.csv` | Nenhuma coluna nova (`D-11`); o arquivo continua com uma linha por região |
| `GET /` (tela de entrada) | Nenhum byte: `SHA_DA_TELA` inalterado |
| Testes de caracterização | Nenhuma saída existente muda: campo novo, defaults vazios |

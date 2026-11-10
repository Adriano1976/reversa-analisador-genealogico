# Data Delta: grupos de triangulação

> Identificador: `055-grupos-de-triangulacao`
> Data: `2026-11-09`
> Modelo extraído em: `_reversa_sdd/data-dictionary.md` e `_reversa_sdd/erd-complete.md`
> Confidência: 🟢 CONFIRMADO, 🟡 INFERIDO, 🔴 LACUNA

## 1. Resumo

**Nenhuma mudança de schema. Nenhuma migração. Nenhuma tabela nova.** O arquivo de triangulação é entrada
nova em memória, e os grupos são derivados a cada requisição a partir dele e dos cartões já produzidos. O que
muda é o **payload em memória** da análise (`ResultadoDeAnalise`) e o **contexto do template**. O banco
continua com as **6 tabelas** de `init.sql`, e nem a projeção (`projetar_analise`) nem o adaptador
`RegistroDeAnalisesPostgres` são tocados.

## 2. Estruturas novas (em memória)

| Estrutura | Campos | Origem | Confidência |
|-----------|--------|--------|-------------|
| `ParDeTriangulacao` | `kit_a`, `nome_a`, `nome_a_bruto`, `kit_b`, `nome_b`, `nome_b_bruto`, `cromossomo`, `inicio`, `fim`, `cm`, `snps`, `linha` | CSV de triangulação | 🟢 |
| `LeituraDeTriangulacao` | `pares`, `linhas`, `pares_descartados`, `avisos`, `build_declarado` | adaptador | 🟢 |
| `GrupoDeTriangulacao` | `cromossomo`, `inicio`, `fim`, `kits`, `pares`, `cm_minimo`, `cm_maximo`, `acumulo` | núcleo | 🟢 |
| `MembroDoGrupo` | `nome`, `nome_bruto`, `kit`, `cartao` (ou `None`), `ancestral_id`, `ancestral_nome` | classificação | 🟢 |
| `GrupoClassificado` | `grupo`, `membros`, `desfecho`, `motivo` | classificação | 🟢 |
| `ResultadoDeTriangulacao` | `grupos`, `observacoes_do_arquivo`, `mensagem` | caso de uso | 🟢 |

**Invariantes dos tipos**

- `inicio` e `fim` são inteiros de pares de bases; `fim > inicio`, senão o par é descartado com motivo.
- `cm` é `float` e **nunca** é arredondado no núcleo (`BR-D-15`); o arredondamento é só de apresentação.
- `kits` é um conjunto ordenado e imutável na saída (a ordem entra na chave de determinismo da `RN-13`).
- `cm_minimo` e `cm_maximo` são dos **pares**, nunca uma soma (`RN-06`); o grupo não tem "cM total".
- `acumulo` é booleano derivado de `RN-05`, e não altera `desfecho`.

## 3. Campos novos em estruturas existentes

| Estrutura | Campo | Tipo | Padrão | Consumidor |
|-----------|-------|------|--------|------------|
| `ResultadoDeAnalise` (`src/application/dna_analysis.py`) | `grupos` | `tuple` | `()` | `src/app.py` → template |
| Contexto de `index.html` | `grupos` | `list` | ausente | bloco de grupos |
| Contexto de `index.html` (modo isolado) | `triangulacao_sem_arvore` | `bool` | `False` | texto do bloco |

O padrão `()` em `grupos` é a compatibilidade: as construções existentes de `ResultadoDeAnalise` continuam
válidas, e a ausência do campo no template significa "bloco não renderiza". É a mesma escolha feita na 039
(`sem_correspondencia`) e na 040 (`cobertura`).

## 4. Campos removidos

Nenhum.

## 5. Impacto no banco (`init.sql`, 6 tabelas)

Nenhum. Em particular:

- `dna_analysis` **não** ganha coluna: o grupo não é parte do veredito, e o histórico registra a análise que
  existia. Acrescentar `triangulation_file` obrigaria migração e não teria consumidor.
- `match_kit` **não** é reutilizada: ela guarda os kits da análise de matches, e o grupo pode conter kits que
  não viraram cartão.
- `skipped_match` **não** muda: o grupo não descarta match nenhum.

## 6. O que deliberadamente **não** é persistido

| Dado | Por que não | Consequência |
|------|-------------|--------------|
| Grupo e membros | É leitura derivada; persistir exigiria 2 tabelas e migração para dado que se recalcula do arquivo | O histórico não reconstrói os grupos; para auditoria, o CSV de grupos (`/grupos.csv`) é a via |
| Arquivo de triangulação associado à análise | Exigiria coluna nova e FK; a análise de DNA já guarda o CSV de matches por nome | Quem quiser reencontrar o grupo reenvia o arquivo |

`D-07` registra a decisão e a alternativa descartada (JSON em `dna_analysis`).

## 7. Compatibilidade e migração

| Cenário | Comportamento |
|---------|---------------|
| Arquivo GEDCOM/CSV armazenado antes da feature | Lido como sempre; nada muda |
| Análise de DNA sem o campo novo | Resultado idêntico ao de hoje (`grupos = ()`) |
| Histórico no Postgres | Nenhuma linha nova, nenhuma coluna nula |
| Banco desligado | A feature funciona igual: o grupo não toca persistência |

**Migração necessária:** n/a. Não há `ALTER TABLE`, nem backfill, nem índice.

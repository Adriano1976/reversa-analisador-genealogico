# Investigation: cache dos índices derivados da árvore

> Identificador: `047-cache-dos-indices-da-arvore`
> Data: `2026-10-24`
> Requirements: `_reversa_forward/047-cache-dos-indices-da-arvore/requirements.md`

## 1. O que motivou

O `POST` de análise de DNA custa **67,29 s** no caso real medido (árvore de 19.403 pessoas,
CSV de matches de 492 linhas). Desse total, **59,25 s são custo fixo reexecutado para o mesmo
arquivo**: 50,53 s de parse e 8,72 s de índices. O pipeline por cartão responde por 6,84 s.

A pergunta de pesquisa era: o cache vale a pena, ou o tempo está no trabalho de análise?

## 2. Medições

| Cenário | Parse | Índices | Pipeline | Render | Total |
|---|---:|---:|---:|---:|---:|
| `POST` de análise (sem cache) | 50,53 s | 8,72 s | 6,84 s | 0,22 s | **67,29 s** |
| `POST` de seleção de árvore (sem cache) | 47,56 s | — | 0,12 s | — | **47,56 s** |
| Mesmo `POST` de seleção, com cache | 0 s | — | 0,12 s | — | **0,58 s** |

Memória, medida com `psutil` no mesmo processo:

| Estado | RSS |
|---|---:|
| processo vazio | 44 MB |
| após o parse | 381 MB (+337) |
| após os índices | 412 MB (+31) |

Índices: 17.590 chaves de nome, 6.397 sobrenomes, 19.403 fichas de atributos.

## 3. Alternativas avaliadas

| Alternativa | Veredito | Por quê |
|---|---|---|
| **Não fazer nada** | descartada | 88 % do `POST` é trabalho repetido para o mesmo arquivo |
| **Trocar pandas por Polars / parsers em Rust** | descartada | o CSV custa 0,30 s do `POST`; o gargalo é o parse do GEDCOM em Python puro |
| **Cache da árvore + índices presos a ela** | **escolhida** | ataca os 59,25 s, sem mudar regra nenhuma |
| **Cache só dos índices, chaveado por arquivo, em módulo** | descartada | é a classe do `L-24`: estado de módulo com chave derivada do conteúdo, sujeita a colisão silenciosa |
| **Cache em disco (pickle da árvore)** | descartada | 340 MB por arquivo em disco, risco de formato obsoleto e nenhum ganho sobre a memória |
| **Parse preguiçoso (materializar só o que a análise usa)** | adiada | mexe no parser e no contrato de paridade; é a próxima alavanca se a memória apertar |
| **Persistir a árvore no PostgreSQL** | descartada | o banco guarda o histórico, não a árvore (`architecture.md#4`) |

## 4. Padrões aplicáveis

- **Memoização por objeto**: o resultado é preso ao objeto que o originou, e morre com ele. É o
  padrão já usado em `fichas_da_pessoa._indice_de_filhos`.
- **LRU com teto**: `OrderedDict` + `move_to_end` + `popitem(last=False)`.
- **Single-flight**: um evento por chave; quem chega depois espera, e se o primeiro falhar,
  parseia por conta própria — o erro de um não vira resultado vazio para os outros.

## 5. O que a medição desmentiu

1. **Os "6 minutos" do `BUG-20261021-7O7V` não reproduzem.** A análise do caso equivalente leva
   hoje 15,56 s. O relato é anterior às correções de `get_children` e `_diferencas`.
2. **O pipeline por cartão não é o gargalo.** Ele é 10 % do `POST`; o custo fixo é 88 %.
3. **A renderização não pesa.** 10 MB de HTML custam 0,22 s.

## 6. Fontes

- `_reversa_sdd/architecture.md#1` e `#4`
- `_reversa_sdd/addenda/025-desempenho-carga-arvore.md`
- `_reversa_sdd/addenda/bug-BUG-20261021-7O7V-v001.md`
- `_reversa_sdd/addenda/046-paginacao-dos-resultados.md`
- `_reversa_sdd/gaps.md#3-lacunas-moderadas` (`L-24`)
- `.reversa/principles.md`

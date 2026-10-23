---
schema_version: 1
id: OPP-20261023-DOCF
display_number: 48
context: analise-dna
verb: prune
title: Docstring órfão de 14 linhas e um nome morto no __all__ do módulo
target:
  files: [src/core/dna_analysis.py]
  symbol: dna_analysis (corpo), __all__
smell: >
  Duas sobras sem efeito. A primeira: logo depois de `analisador_de_dna = DNAAnalyzer()`,
  há um bloco de 14 linhas que parece docstring e não é. Como é a segunda instrução de
  string da função, o Python a avalia e descarta; a docstring real é a da linha 541.
  A segunda: `DNAAnalyzer` está declarado em `__all__`, mas nenhum arquivo do projeto o
  importa de `core.dna_analysis`.
roi:
  confidence: green
  impact: >
    Uma sobra que se lê como documentação viva é pior que uma sobra evidente: o texto
    diz que a função "retorna (results_sorted, skipped, message)" e descreve
    `observacoes_do_arquivo`, como se fosse a docstring, e quem edita o módulo pode
    atualizar o bloco errado. O nome morto no `__all__` amplia uma superfície de
    compatibilidade que o próprio módulo declara ter enxugado em T022.
  cost: low
  est_return: 15 linhas a menos e uma única docstring por função, com a superfície de compatibilidade reduzida ao que tem consumidor.
state: applied
traceability:
  soul: []
  specs:
    - _reversa_sdd/analise-dna/requirements.md
    - _reversa_sdd/analise-dna/design.md
    - _reversa_sdd/adrs/19-heuristicas-declaradas-como-heuristicas.md
---

## Antes observado

### 1. O docstring órfão

Linhas 553-571, transcritas na forma em que o interpretador as enxerga:

```python
    candidatos_fixos = candidatos_fixos or {}
    analisador_de_dna = DNAAnalyzer()
    """Executa o fluxo completo da analise de DNA.

    Retorna `(results_sorted, skipped, message)`. Cada resultado traz, lado a lado
    e sem misturar: `documentary` (GEDCOM), `genetic_evidence` (DNA),
    `hypotheses` (possibilidades) e `comparison` (confronto).
    ...
    """
    root_person_ids = [...]
```

Verificação por AST, nesta sessão:

```
--- expressoes de string soltas (nao-docstring) ---
  linha  558  dentro de dna_analysis  -> 'Executa o fluxo completo da analise de DNA.\n\n    Retorna `(r'...
```

É um `Expr(Constant(str))`: avaliação sem efeito colateral, descartada. A docstring
de `dna_analysis` vem da linha 541 e não muda com a remoção.

O bloco não é só redundante com a primeira docstring: ele descreve um retorno de
três posições que a primeira também descreve, e repete a explicação de
`observacoes_do_arquivo`, que já está no primeiro texto. Foi o segundo docstring de
uma função que ganhou um segundo cabeçalho em alguma edição.

### 2. O nome morto no `__all__`

`__all__` declara 15 nomes. Varredura de todos os `.py` do projeto, por AST,
procurando quem importa de `core.dna_analysis`:

| Nome em `__all__` | Consumidores fora do módulo |
|---|---|
| `dna_analysis` | 47 arquivos |
| `Dependencias` | 34 arquivos |
| `build_ged_indexes`, `match_candidates` | `tests/test_characterization_matching.py` |
| `norm_name`, `split_name_pt`, `surnames_set`, `top_given_tokens`, `token_prefixes`, `drop_short_tokens`, `surname_core_tokens`, `soft_prefix_jaccard`, `strip_bad_utf`, `demojibake` | `_reversa_sdd/parity/_collect_cand.py` e `_check_split_types.py` |
| **`DNAAnalyzer`** | **nenhum** |

Não existe `from core.dna_analysis import *` em nenhum arquivo do projeto (0
ocorrências). O import de `DNAAnalyzer` no módulo permanece, porque o corpo o usa na
linha 557; o que sai é a declaração em `__all__`.

## Prova de morte

| Item | Como se prova |
|---|---|
| linhas 558-571 | `ast` mostra `Expr(Constant(str))`; string constante não tem efeito colateral, e `inspect.getdoc(dna_analysis)` continua devolvendo o texto da linha 541 nas duas variantes |
| `DNAAnalyzer` em `__all__` | varredura por AST de todos os `.py`: zero importações do nome a partir deste módulo, e zero `import *` no projeto |

O teste de equivalência é a própria suíte, mais uma asserção de que
`dna_analysis.__doc__` é idêntico antes e depois. Medição desta sessão, antes da
poda: **1625 passed, 9 skipped em 105,64 s**.

## O que NÃO é poda neste módulo

Registrado porque a pergunta "existe função sem utilidade?" foi medida e a resposta
honesta é: **nenhuma função inteira é órfã**. As 10 funções de nível de módulo e a
classe `Dependencias` têm chamador.

| Candidato | Medição | Decisão |
|---|---|---|
| Alguma das 10 funções | todas referenciadas no corpo ou importadas (inclusive por `tests/test_endogamia.py`) | não poda |
| `Dependencias.aggregate_matches` | atribuído na linha 130 e **nunca lido** no módulo | não poda: é argumento posicional obrigatório de 34 chamadores em `_reversa_bugs/_sondas-matching/` e `_reversa_sdd/parity/`, caminhos que a config não libera. Remover quebra instrumentos congelados |
| `Dependencias.generate_mermaid_indirect` | lido por `src/core/path_search.py:187` | não poda, é usado por outro fluxo |
| `getattr(deps, "anotar_profundidade", None)` (linha 157) | o slot sempre existe, então o `getattr` é cerimônia | não poda: um `getattr` defensivo de uma linha não muda leitura nem comportamento |
| 12 imports sem uso no corpo | usados pela fachada de `__all__` | ver `OPP-20261023-CTAO`; não vira oportunidade por ROI, e o consumidor está congelado |

## Transformação proposta

1. Remover as linhas 558-571 (as 14 linhas do docstring órfão).
2. Remover `"DNAAnalyzer"` da lista de `__all__`.

Nada mais. Nem uma linha de lógica, nem um import.

## Fronteira de comportamento

Nenhuma. O módulo exporta o mesmo que antes, exceto um nome que ninguém importava, e
o texto solto nunca foi lido por ninguém além do interpretador, que o descartava.

## Resultado da aplicação

Aplicada em 2026-10-23, sob gate de plano e de diff aprovados. O módulo passou de
**1.108 para 1.094 linhas**, e `__all__` de 15 para 14 nomes. A suíte ficou em
**1625 passed, 9 skipped** (106,01 s), a mesma contagem de antes (105,64 s).

O registro completo, com a prova de morte por trecho e o diff de reversão, está em
`../transformations/OPP-20261023-DOCF-sobras-sem-efeito/transformation.md`.

---
*Gerado pelo Reversa-Refactor em 2026-10-23. Aplicada no mesmo dia.*

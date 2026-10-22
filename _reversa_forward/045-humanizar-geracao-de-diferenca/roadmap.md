# Roadmap: humanizar a geração de diferença

> Identificador: `045-humanizar-geracao-de-diferenca`
> Data: `2026-10-22`
> Modo: express

## 1. Resumo da abordagem

Duas funções puras em `core.graus_de_parentesco` — `geracoes_de_diferenca(quantidade)` e
`nome_do_primo(grau, removidos)` — passam a ser a **única** fonte do rótulo do primo. A tabela
publicada (`SCP40_ROWS`) deixa de escrever o nome à mão nas nove linhas com diferença de geração, e
`documentary_label` deixa de montar a sua própria versão: as duas chamam `nome_do_primo`.

O ganho não é só de redação. Antes, a mesma relação aparecia como `Primos de 1º grau (1× removido)`
no bloco 3 e como `Primos de 1º grau com 2× remoção` no bloco 2 — dois jeitos para o mesmo fato, com
concordância diferente. Com fonte única, essa classe de divergência desaparece, e o teste de
igualdade entre as duas superfícies a prende.

## 5. Delta arquitetural

| Componente | Tipo | Arquivo alvo |
|---|---|---|
| `core.graus_de_parentesco` | regra-nova | `src/core/graus_de_parentesco.py` (`geracoes_de_diferenca`, `nome_do_primo`) |
| `core.documentary_relationship` | contrato-alterado | `src/core/documentary_relationship.py` (`documentary_label` usa `nome_do_primo`; reexporta) |
| `core.relationship_hypotheses` | contrato-alterado | `src/core/relationship_hypotheses.py` (9 linhas de `SCP40_ROWS` deixam de ter literal) |
| `tests` | contrato-alterado | `tests/test_rotulos_de_parentesco.py`, `tests/test_confrontacao_gedcom_dna.py`, `tests/test_tabela_do_bloco_3.py`, `tests/test_destaque_da_hipotese.py`, `tests/test_destaque_na_tela.py` |

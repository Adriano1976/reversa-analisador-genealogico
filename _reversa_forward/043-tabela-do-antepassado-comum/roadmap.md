# Roadmap: tabela das possibilidades com o antepassado comum

> Identificador: `043-tabela-do-antepassado-comum`
> Data: `2026-10-22`
> Modo: express

## 1. Resumo da abordagem

O núcleo já sabe tudo o que a tabela precisa mostrar; falta (a) ligar a chave canônica
de cada relação ao par de graus que leva ao antepassado comum e (b) desenhar a coluna.
A ligação é **definicional**, e por isso pode ser conferida: `GRAUS_ATE_O_MRCA` alimenta
`documentary_label`, e o teste exige que a chave devolvida seja a mesma. As três
meias-relações entram à parte, porque `documentary_label` não as produz.

A série portuguesa de graus sai de `core.documentary_relationship` para um módulo sem
import nenhum (`core/graus_de_parentesco.py`): `core.relationship_hypotheses` precisa do
plural `bisavós` e não pode arrastar `networkx` (que entra naquele módulo por
`path_finding`) para dentro do caminho do CSV. `nome_do_grau` continua público no
módulo antigo, por reexportação.

## 5. Delta arquitetural

| Componente | Tipo | Arquivo alvo |
|---|---|---|
| `core.graus_de_parentesco` | componente-novo | `src/core/graus_de_parentesco.py` (série de graus e o plural `bisavós`) |
| `core.documentary_relationship` | contrato-preservado | `src/core/documentary_relationship.py` (reexporta `nome_do_grau`; `_ROMANO` → `ROMANO`) |
| `core.relationship_hypotheses` | contrato-alterado | `src/core/relationship_hypotheses.py` (`mrca` e `posicao` no payload da candidata) |
| `templates/index.html` | contrato-alterado | `src/templates/index.html` (bloco 3: lista → tabela) |
| `assets/app.css` | contrato-alterado | `src/assets/app.css` (`.tabela-das-hipoteses`, `.barra-da-faixa`) |
| `tests` | contrato-alterado | `tests/test_mrca_e_posicao_na_faixa.py`, `tests/test_tabela_do_bloco_3.py`, `tests/test_rotulos_de_parentesco.py` |

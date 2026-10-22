# Roadmap: Explicar a fonte não declarada no cartão

> Identificador: `042-explicar-fonte-nao-declarada`
> Data: `2026-10-22`
> Modo: express

## 1. Resumo da abordagem

Levar o motivo que o catálogo já produz até a tela: `fontes_de_laboratorio` ganha uma função pura
`explicacao(motivo, bruto)`, `evidence_for` passa a expor `source_motivo` e `source_explicacao`, e a linha
`Fonte:` do bloco 2 exibe a explicação depois da etiqueta. O texto original continua visível, e a etiqueta
some quando o valor é vazio ou `-` (não há o que mostrar).

## 5. Delta arquitetural

| Componente | Tipo | Arquivo alvo |
|---|---|---|
| `core.fontes_de_laboratorio` | regra-nova | `src/core/fontes_de_laboratorio.py` (função `explicacao`) |
| `core.genetic_evidence` | contrato-alterado | `src/core/genetic_evidence.py` (`evidence_for` expõe motivo e explicação) |
| `templates/index.html` | contrato-alterado | `src/templates/index.html` (linha `Fonte:` do bloco 2) |
| `tests` | contrato-alterado | `tests/test_fontes_de_laboratorio.py`, `tests/test_fonte_e_cobertura_na_tela.py` |

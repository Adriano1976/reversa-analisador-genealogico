---
schema_version: 1
id: OPP-20261023-CLSM
display_number: 36
context: analise-dna
verb: restructure
title: Seis funções auxiliares de projeção sem agrupamento formal (ausência de classe Mapper)
target:
  files: [src/application/projecao_analise.py]
  symbol: ProjetorDeAnalise
smell: >
  Sete funções soltas que formam um cluster coeso de projeção operavam sem nenhum contrato de
  objeto. Elas compartilhavam implicitamente o tipo de entrada (resultado do núcleo) e o tipo de
  saída (payloads da porta), mas esse contrato não estava expresso: qualquer chamador podia invocar
  qualquer função fora de ordem sem que o tipo forçasse a sequência correta.
roi:
  confidence: green
  impact: >
    A classe ProjetorDeAnalise agrupa as sete funções, expõe apenas
    projetar como método público e encapsula os auxiliares como métodos de classe e estáticos.
    O padrão Mapper/Projector torna o contrato explícito, facilita mock nos testes e isola o cluster
    do restante da aplicação.
  cost: medium
  est_return: >
    Classe com contrato explícito substituindo funções soltas. Padrão de projeto Mapper presente
    na camada de aplicação. Facilita evolução isolada da projeção sem tocar no caso de uso.
state: applied
promoted_to: null
traceability:
  soul: []
  specs:
    - _reversa_sdd/analise-dna/design.md
    - _reversa_sdd/adrs/25-fronteira-de-aplicacao-portas.md
    - _reversa_sdd/adrs/33-desfecho-em-tres-valores-e-projecao-pura.md
---

## Antes observado

As sete funções de projeção em `src/application/dna_analysis.py` (linhas 79-289) operam como
um cluster informal sem encapsulamento:

| Função | Papel |
|---|---|
| `_juntar` | merge de pessoa no dict por xref |
| `_ficha` | converte dict -> `PessoaDaAnalise` |
| `_papeis_do_caminho` | extrai `(xref, papel)` do caminho documental |
| `_kits` | monta `tuple[KitDaAnalise, ...]` por índice |
| `_pessoas` | retrato de todas as pessoas + raiz |
| `_conexao` | monta `ConexaoDaAnalise` de um resultado |
| `projetar_analise` | orquestra todos os anteriores |

O cluster tem alta coesão **dentro de si** mas nenhum contrato formal que force a sequência
correta ou que deixe claro o invariante: *"dado o resultado bruto do núcleo, produza o payload
tipado da porta"*.

## Transformação proposta

```python
class ProjetorDeAnalise:
    """Mapeia o resultado bruto do nucleo para o payload da porta (D-15)."""

    def _juntar(self, ...) -> None: ...
    def _ficha(self, ...) -> PessoaDaAnalise | None: ...
    def _papeis_do_caminho(self, ...) -> tuple: ...
    def _kits(self, ...) -> tuple[KitDaAnalise, ...]: ...
    def _pessoas(self, ...) -> tuple: ...
    def _conexao(self, ...) -> ConexaoDaAnalise: ...
    def projetar(self, resultados, descartados, mensagem, ...) -> AnaliseParaRegistrar: ...
```

O método público seria `projetar` (ou `projetar_analise` para compatibilidade). O `__all__`
exportaria `ProjetorDeAnalise` e `projetar_analise` (função wrapper de compatibilidade).

## Nota de dependência

Esta oportunidade é **dependente** da OPP-20261023-MPRA: faz mais sentido aplicar a classe
**depois** de o mapper estar em módulo próprio (`projecao_analise.py`). A sequência recomendada
é: primeiro modularize (OPP-35), depois restructure (OPP-36).

## Rede de segurança

A projeção é pura e coberta indiretamente pelos testes existentes. A rede é a suíte verde antes
e depois, sem necessidade de nova caracterização — desde que a interface pública `projetar_analise`
permaneça compatível.

---
*Gerado pelo Reversa-Refactor em 2026-10-23.*

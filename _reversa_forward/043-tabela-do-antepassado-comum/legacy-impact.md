# Legacy impact: tabela das possibilidades com o antepassado comum

> Identificador: `043-tabela-do-antepassado-comum`
> Data: `2026-10-22`
> Modo: **express**
> Política de edição do legado: `allowLegacyEdits: true`, com `allowedPaths` liberando `src/**` e
> `tests/**`. Todos os arquivos tocados estão dentro desses globs.

## 1. Arquivos afetados

| Arquivo afetado | Componente | Tipo | Severidade | Justificativa |
|---|---|---|---|---|
| `src/core/graus_de_parentesco.py` | — | componente-novo | LOW | Série portuguesa de graus sem import nenhum: `nome_do_grau`, `ROMANO` e o plural `bisavós` |
| `src/core/documentary_relationship.py` | `busca-caminho` | contrato-preservado | LOW | Importa e reexporta `nome_do_grau`/`ROMANO`; `_ROMANO` deixou de existir aqui |
| `src/core/relationship_hypotheses.py` | `analise-dna` | contrato-alterado | LOW | `GRAUS_ATE_O_MRCA`, `GRAUS_DAS_MEIAS_RELACOES`, `mrca_da_relacao`, `posicao_na_faixa`; `mrca` e `posicao` no payload |
| `src/templates/index.html` | apresentação | contrato-alterado | LOW | Bloco 3: a lista de nomes vira tabela de quatro colunas com o rodapé do sentido da ordem |
| `src/assets/app.css` | apresentação | contrato-alterado | LOW | Estilos da tabela, da barra da faixa e do rótulo da posição |
| `tests/test_mrca_e_posicao_na_faixa.py` | — | componente-novo | LOW | 48 casos: ida e volta dos graus, plural, posições, payload, proibição da probabilidade |
| `tests/test_tabela_do_bloco_3.py` | — | componente-novo | LOW | 8 casos de tela, incluindo o cartão sem cobertura publicada |
| `tests/test_rotulos_de_parentesco.py` | — | contrato-alterado | LOW | O plural `bisavós` passa a ser medido na mesma série dos avós |

## 2. Diff conceitual

**`core.graus_de_parentesco`.** Recebe a série que morava em `documentary_relationship`,
com a terceira coluna da tabela: o plural do ancestral (`bisavós`, `trisavós`). O
plural **não** é derivado com `+ "s"` — `avô` faz `avós`, e a diferença é o acento. O
módulo não importa nada, e há teste que falha se ele ganhar import.

**`core.relationship_hypotheses`.** Duas grandezas novas por candidata:
`mrca` (graus por lado, rótulo e detalhe) e `posicao` (fração, percentual e rótulo da
posição do valor dentro da faixa publicada). Ambas são **aditivas**: `name_pt`,
`range_low`, `range_high`, `average`, `meioses` e a ordenação não mudaram.

**Template.** A `<ul>` do bloco 3 vira `<table>` de quatro colunas. Entram a barra da
faixa e duas frases no rodapé: o sentido da ordem e o aviso de que o antepassado comum
é definição, e não estatística. O aviso amarelo do rodapé continua igual.

## 3. Regras do `domain.md` **preservadas**

| Regra | Verificação |
|---|---|
| §3.3 — o cM vira **lista**, nunca um parentesco único | a tabela tem N linhas, e N > 1 na maioria dos cartões; nenhum campo novo escolhe uma |
| §3.3 — a confiança é heurística do projeto | o selo `confiança:` continua vindo de `_confianca`, inalterado |
| §3.3 — a fonte não publica mediana | a coluna continua dizendo `média`, nunca mediana |
| §3.3 — nenhum número inventado | `GRAUS_ATE_O_MRCA` é definição conferida por ida e volta; `posicao` só lê a faixa publicada |
| Princípio V — referência e data | o módulo declara que o antepassado **não** vem da fonte, e a tela repete isso |
| §3.2 — o DNA não decide parentesco | o bloco 4 continua sendo o único que confronta; nada aqui altera veredito |

## 4. Regras **modificadas**

| Regra | O que mudou | Onde |
|---|---|---|
| Apresentação das possibilidades no bloco 3 | lista → tabela com a posição do valor na faixa e o antepassado comum | `src/templates/index.html` |
| Payload da candidata (`possible_relationships`) | ganha `mrca` e `posicao` (aditivo) | `src/core/relationship_hypotheses.py` |
| Casa da série portuguesa de graus | `documentary_relationship` → `graus_de_parentesco`, com reexportação | `src/core/graus_de_parentesco.py` |

> **Decisão registrada:** a coluna `Probabilidade` da referência apresentada pelo
> operador foi **recusada**. A versão 4.0 não publica probabilidade por relação (só
> número de envios, mínimo, média, máximo e desvio), os percentuais somariam 100% e
> fechariam o mundo num conjunto que o projeto recusa fechar, e na profundidade real do
> caso — 9 a 51 cM, com 11 a 15 relações compatíveis — o maior percentual seria lido
> como resposta. `posicao_na_faixa` ocupa o lugar sem inventar número.

> **Para o `/reversa-sync`:** `_reversa_sdd/domain.md#33` descreve o bloco das
> possibilidades (lista ordenada, sem colunas); ganha a tabela, o antepassado comum
> definicional e a posição na faixa. `_reversa_sdd/data-dictionary.md` descreve o
> payload de `possible_relationships`; ganha duas chaves. A série de graus muda de
> arquivo em `_reversa_sdd/architecture.md` (componentes de `busca-caminho` e
> `analise-dna`).

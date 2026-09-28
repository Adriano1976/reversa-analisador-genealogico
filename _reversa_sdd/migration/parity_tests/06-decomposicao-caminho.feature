# language: pt
# spec-id: PT-006
# rastreabilidade:
#   process_flows: "_reversa_sdd/busca-caminho/design.md § Detalhe da conexao indireta e split_path_by_marriage; _reversa_sdd/code-analysis.md §3 (find_indirect_path)"
#   target_architecture: "BC-04 Parentesco e Caminho; core/pathfinding.py (find_indirect_path), core/decomposition.py (split_path_by_marriage, are_spouses); AD-04"
#   paradigma_alvo: "OO com DI sobre funcoes puras"
#   regras: [BR-MIGRAR-024, BR-MIGRAR-025, BR-HUMANA-008]
#   oraculo: "analisador-genealogico/app.py (SOMENTE LEITURA)"
#   cobertura_paradigma: "@ordem (ordem de arestas) — reinterpretacao da tag para ausencia de eventos"
#
# ############################################################################
# # ARQUIVO DE MAIOR RISCO DO CONJUNTO (RISK-011)                            #
# # Nenhum cenario de matching falharia se split_path_by_marriage e          #
# # are_spouses desaparecessem — o matching continuaria correto. Esta e a    #
# # unica barreira contra a perda SILENCIOSA dessas regras de negocio,       #
# # que o legado misturava com a geracao de diagrama Mermaid.                #
# ############################################################################

Funcionalidade: Decomposicao de conexao indireta por afinidade
  Como genealogista genetico
  Quero ver como duas pessoas se conectam por casamento
  Para entender relacoes que nao passam por ancestral comum

  @paridade @critico
  Cenario: Conexao indireta por casamento e encontrada quando nao ha ancestral comum
    Dado duas pessoas sem ancestral comum
    E conectadas por vinculo de casamento ou afinidade dentro da arvore
    Quando a busca direta falha e a indireta e executada
    Entao um caminho e retornado
    E a mensagem exibida e exatamente "Conexão indireta encontrada (via casamento/afinidade)."

  @paridade @critico
  Cenario: Caminho indireto e comprimido removendo nos de familia
    Dado um caminho indireto retornado pelo algoritmo de menor caminho
    Quando o caminho e preparado para exibicao
    Entao o caminho contem apenas nos de pessoa
    E o numero de pessoas no caminho e identico ao do oraculo legado

  @paridade @critico
  Cenario: Limite de saltos e medido ANTES da compressao
    Dado um caminho cujo comprimento bruto, incluindo nos de familia, excede 40 saltos
    Quando a conexao indireta e avaliada
    Entao o caminho e considerado inexistente
    # BR-MIGRAR-025: o limite e aplicado ao caminho BRUTO (com nos de familia),
    # antes da compressao. Medir depois da compressao produziria resultado diferente.

  @paridade @critico
  Cenario: Caminho indireto e dividido no primeiro par de conjuges adjacentes
    Dado um caminho indireto que contem um ou mais pares de conjuges adjacentes
    Quando o caminho e decomposto para apresentacao
    Entao a divisao ocorre no PRIMEIRO par de conjuges adjacentes
    E o ramo a esquerda, o ramo a direita e o par de conjuges sao identicos aos do oraculo legado
    # BR-HUMANA-008 (decisao humana explicita): a LOGICA de decomposicao migra.
    # Apenas a emissao de sintaxe Mermaid e descartada (DEV-004 / BR-DESCARTAR-005).
    # ATENCAO: se o front-end recalcular a decomposicao em vez de consumir a
    # estrutura produzida pelo dominio, RISK-011 se materializa.

  @paridade @critico
  Cenario: Verificacao de vinculo conjugal e preservada
    Dado dois identificadores de pessoa
    Quando a verificacao de vinculo conjugal e executada
    Entao o resultado e identico ao do oraculo legado
    # are_spouses. Regra de negocio pura, nao tecnologia de desenho.

  @paridade @critico
  Cenario: Caminho indireto com multiplas afinidades e decomposto corretamente
    Dado um caminho indireto que atravessa mais de um casamento
    Quando o caminho e decomposto
    Entao a decomposicao e identica a do oraculo legado
    # O legado detecta apenas o 1o par de conjuges (limitacao conhecida,
    # registrada em busca-caminho/design.md § Riscos como 🟡).
    # Em modo literal, a limitacao e PRESERVADA — nao "corrigir" sem decisao.

  @paridade @critico
  Cenario: Ausencia de conjuges no caminho usa a representacao simples
    Dado um caminho indireto sem nenhum par de conjuges adjacentes
    Quando a representacao do caminho e montada
    Entao a representacao simples e usada
    E o resultado e identico ao do oraculo legado

  @paridade @critico
  Cenario: O alvo NAO emite sintaxe Mermaid
    Dado um caminho direto ou indireto resolvido
    Quando o payload de resposta e inspecionado
    Entao a resposta contem a estrutura decomposta do caminho
    E a resposta NAO contem sintaxe Mermaid
    # DEV-004 / BR-DESCARTAR-005. A comparacao de paridade nao pode asserir
    # sobre string Mermaid — a string nao existe mais no alvo.

# language: pt
# spec-id: PT-009
# rastreabilidade:
#   process_flows: "_reversa_sdd/domain.md §2.1; _reversa_sdd/code-analysis.md §4.4 (SHARED_CM_DATA)"
#   target_architecture: "BC-03 Analise de DNA; core/relationship.py (relationship_by_cm)"
#   paradigma_alvo: "OO com DI sobre funcoes puras"
#   regras: [BR-MIGRAR-020, BR-MIGRAR-021]
#   oraculo: "analisador-genealogico/app.py (SOMENTE LEITURA)"
#   cobertura_paradigma: "@exatidao (dimensao NOVA) — fronteiras de faixa"

Funcionalidade: Relacao prevista por faixa de centiMorgans
  Como genealogista genetico
  Quero saber o parentesco provavel a partir do total de cM
  Para interpretar o significado de cada match

  @paridade @critico @exatidao
  Cenario: Cada faixa de cM produz a relacao exata do legado
    Dado um total de cM em cada uma das nove faixas conhecidas
    Quando a relacao prevista e calculada
    Entao cada relacao retornada e IDENTICA a do oraculo legado
    # As faixas e seus rotulos sao literais congelados. Nao parafrasear.

  @paridade @critico @exatidao
  Cenario: Sobreposicao entre faixas e resolvida pela ORDEM de avaliacao
    Dado um total de cM que pertence simultaneamente a mais de uma faixa
    Quando a relacao prevista e calculada
    Entao a relacao retornada e a da PRIMEIRA faixa que casa
    E o resultado e identico ao do oraculo legado
    # BR-MIGRAR-020: as faixas SE SOBREPOEM (ex.: 46-515 e 200-850 contem
    # 200-515). A ordem sequencial e o contrato. NAO converter para busca
    # binaria, para intervalo de banco ou para tabela ordenada por faixa.

  @paridade @critico @exatidao
  Cenario: Valores exatamente nas fronteiras de faixa sao classificados corretamente
    Dado totais de cM exatamente iguais a 0, 10, 30, 46, 200, 553, 1317, 2200 e 3300
    Quando a relacao prevista e calculada
    Entao a relacao de cada fronteira e identica a do oraculo legado
    # Fronteiras sao onde um erro de arredondamento se manifesta como
    # mudanca de relacao apresentada ao usuario.

  @paridade @critico
  Cenario: cM nao numerico produz LISTA VAZIA de relacoes
    Dado um match cujo campo de cM contem texto nao numerico
    Quando a relacao prevista e calculada
    Entao nenhuma relacao e retornada
    # CASO A de BR-MIGRAR-021. Verificado contra o oraculo.
    # A spec original afirmava que este caso retornava o literal
    # "Relacao distante ou indeterminada" — INCORRETO. Ver correcao factual.

  @paridade @critico
  Cenario: cM igual a zero ou negativo produz LISTA VAZIA de relacoes
    Dado um match cujo total de cM e zero ou negativo
    Quando a relacao prevista e calculada
    Entao nenhuma relacao e retornada
    # Verificado por execucao direta do oraculo:
    #   get_relationships_by_cm(0)  == []
    #   get_relationships_by_cm(-5) == []

  @paridade @critico
  Cenario: cM positivo fora de todas as faixas produz a relacao indeterminada
    Dado um match cujo total de cM e um numero positivo
    E esse valor nao pertence a nenhuma das nove faixas conhecidas
    Quando a relacao prevista e calculada
    Entao a relacao retornada e exatamente "Relação distante ou indeterminada"
    # CASO B de BR-MIGRAR-021 — DISTINTO do Caso A. Este e o unico caso em que
    # o literal "Relacao distante ou indeterminada" e produzido.

  @paridade @critico
  Cenario: Resultados sao ordenados por cM decrescente com desempate estavel
    Dado uma analise com diversos matches aceitos
    Quando os resultados sao apresentados
    Entao a ordem e por total_cm decrescente
    E matches com o mesmo total_cm mantem ordem deterministica e reproduzivel
    E a ordem e identica a do oraculo legado
    # BR-MIGRAR-031. A ordenacao ocorre no servidor e e preservada no payload —
    # nao delegada ao cliente.

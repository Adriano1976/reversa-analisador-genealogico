# language: pt
# spec-id: PT-002
# rastreabilidade:
#   process_flows: "_reversa_sdd/analise-dna/design.md § Fluxo Principal passos 7-8; _reversa_sdd/code-analysis.md §3 (process_dna_action)"
#   target_architecture: "BC-03 Analise de DNA; core/dna.py; AGG-02 DnaAnalysis; AD-03"
#   paradigma_alvo: "OO com DI sobre funcoes puras"
#   regras: [BR-MIGRAR-016, BR-MIGRAR-019]
#   oraculo: "analisador-genealogico/app.py (SOMENTE LEITURA) — nunca reconstructed/"
#   cobertura_paradigma: "@exatidao (dimensao NOVA — nao prevista na matriz) + @ordem"

Funcionalidade: Agregacao de segmentos de DNA e soma de centiMorgans
  Como genealogista genetico
  Quero que segmentos repetidos do mesmo match sejam somados
  Para que o parentesco previsto reflita o total compartilhado

  @paridade @critico @exatidao
  Cenario: Segmentos duplicados do mesmo match sao somados
    Dado um CSV de DNA com tres segmentos do mesmo match
    E os segmentos tem valores de cM conhecidos
    Quando a analise e executada
    Entao existe um unico registro de match para essa pessoa
    E o total_cm e EXATAMENTE igual ao do oraculo legado
    # Sem tolerancia. Sem pytest.approx. Sem arredondamento.
    # Ver RISK-004: soma em ponto flutuante nao e associativa.

  @paridade @critico @exatidao @ordem
  Cenario: Ordem de acumulacao dos cM e preservada
    Dado um CSV cujos segmentos, somados em ordens diferentes, produzem resultados distintos no ultimo digito
    Quando o candidato agrega os segmentos
    Entao o total_cm e identico ao do oraculo legado
    E a agregacao usa a ordem de leitura do CSV, nao uma agregacao de banco
    # AD-03: a soma e calculada no nucleo puro e persistida ja calculada.
    # Usar SUM do PostgreSQL produziria resultado potencialmente diferente.

  @paridade @critico @exatidao
  Cenario: Fronteiras de faixa de cM sao respeitadas exatamente
    Dado um conjunto de matches com total_cm exatamente em 46, 200, 553, 1317, 2200 e 3300
    Quando a relacao prevista e calculada
    Entao cada total_cm produz a mesma relacao que o oraculo legado produz
    # Um erro de centesimo pode cruzar uma fronteira e mudar a relacao apresentada.

  @paridade @critico
  Cenario: A chave de agrupamento combina nome normalizado e identificador
    Dado um CSV com dois registros que diferem apenas no identificador de match
    Quando os segmentos sao agrupados
    Entao os registros NAO sao fundidos
    E o numero de matches e identico ao do oraculo legado

  @paridade @critico
  Cenario: Identificador de match no formato *** e reconhecido
    Dado um CSV onde o identificador do match segue o padrao de duas letras maiusculas seguidas de sete digitos
    Quando a chave de agrupamento e construida
    Entao o identificador e extraido e compoe a chave
    E o agrupamento resultante e identico ao do oraculo legado

  @paridade @critico
  Cenario: cM nao numerico ou nao positivo permanece no resultado SEM relacao prevista
    Dado um CSV com um match cujo valor de cM e zero, negativo ou nao numerico
    Quando a analise e executada
    Entao o match permanece no conjunto de resultados
    E o match NAO possui relacao prevista
    # CASO A de BR-MIGRAR-021, VERIFICADO CONTRA O ORACULO:
    #   get_relationships_by_cm(0)  == []   (lista VAZIA, nao uma mensagem)
    #   get_relationships_by_cm(-5) == []
    # A spec original (domain.md §2.1) afirmava que este caso retornava o literal
    # "Relacao distante ou indeterminada". Isso estava INCORRETO — ver a correcao
    # factual em target_business_rules.md BR-MIGRAR-021.
    # O CASO B (cM > 0 fora de todas as faixas -> literal "Relacao distante ou
    # indeterminada") e OUTRO caso e esta coberto em 09-relacao-por-cm.feature.

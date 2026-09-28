# language: pt
# spec-id: PT-007
# rastreabilidade:
#   process_flows: "_reversa_sdd/analise-dna/design.md § Fluxo Principal passos 5-6; § Fluxos Alternativos (encoding invalido)"
#   target_architecture: "BC-03 Analise de DNA; core/dna.py (read_dna_csv)"
#   paradigma_alvo: "OO com DI sobre funcoes puras"
#   regras: [BR-MIGRAR-017, BR-MIGRAR-018, BR-HUMANA-009]
#   oraculo: "analisador-genealogico/app.py (SOMENTE LEITURA)"
#   cobertura_paradigma: "equivalencia funcional estrita"

Funcionalidade: Leitura de CSV de DNA com fallback de encoding e deteccao de colunas
  Como genealogista genetico
  Quero que meu relatorio de matches seja lido independentemente do exportador
  Para nao perder matches por problema de formato

  @paridade @critico
  Cenario: CSV em UTF-8 e lido sem erro
    Dado um arquivo CSV codificado em UTF-8
    Quando o arquivo e lido
    Entao os valores sao lidos sem corrupcao
    E o resultado e identico ao do oraculo legado

  @paridade @critico
  Cenario: CSV em Latin-1 e lido sem erro pelo fallback
    Dado um arquivo CSV codificado em Latin-1 que nao e UTF-8 valido
    Quando o arquivo e lido
    Entao o fallback para Latin-1 e acionado
    E os valores sao lidos sem corrupcao
    E o resultado e identico ao do oraculo legado
    # BR-MIGRAR-017 / RF-01 (Must): "CSV Latin-1 e lido sem erro".
    # A ORDEM de tentativa importa: UTF-8 primeiro, Latin-1 como fallback.
    # No alvo o fallback e estrategia explicita de codec, nao try/except incidental.

  @paridade @critico
  Cenario: Colunas de nome sao reconhecidas nas variacoes aceitas pelo legado
    Dado um CSV cuja coluna de nome se chama Name, MatchedName ou Nome
    Quando as colunas sao detectadas
    Entao a coluna de nome e identificada em todos os casos
    E o resultado e identico ao do oraculo legado

  @paridade @critico
  Cenario: Colunas de cM sao reconhecidas nas variacoes aceitas pelo legado
    Dado um CSV cuja coluna de cM se chama cM, TotalCM ou "Total cM"
    Quando as colunas sao detectadas
    Entao a coluna de cM e identificada em todos os casos

  @paridade @critico
  Cenario: Colunas obrigatorias ausentes produzem erro claro
    Dado um CSV sem coluna de nome ou sem coluna de cM
    Quando a analise e tentada
    Entao a analise nao e executada
    E o erro e comunicado de forma que o usuario entenda o que falta

  @paridade @critico
  Cenario: Ausencia de arquivo CSV produz a mensagem congelada
    Dado que nenhum arquivo CSV foi enviado
    Quando a analise de DNA e submetida
    Entao a mensagem e exatamente "Por favor, carregue o arquivo CSV de matches."

  @paridade @critico
  Cenario: Pessoa-raiz inexistente produz a mensagem congelada
    Dado um GEDCOM carregado e um CSV valido
    E um nome de pessoa-raiz que nao existe na arvore
    Quando a analise de DNA e submetida
    Entao a mensagem e exatamente "Seu nome 'X' não foi encontrado no GEDCOM."

  @paridade @critico
  Cenario: Extensao aditiva de cabecalhos nao altera nenhum resultado existente
    Dado um CSV cujo cabecalho e reconhecido pela heuristica ATUAL do legado
    Quando o candidato le o arquivo com a deteccao ampliada
    Entao a coluna escolhida e a MESMA que o legado escolheria
    E o resultado e identico ao do oraculo legado
    # BR-HUMANA-009 (decisao humana): a ampliacao de cobertura de exportadores
    # e ADITIVA. Ela so pode fazer funcionar o que hoje FALHA; nunca pode mudar
    # o resultado do que hoje FUNCIONA. Este cenario e a prova disso.

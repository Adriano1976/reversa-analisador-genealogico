# language: pt
# spec-id: PT-004
# rastreabilidade:
#   process_flows: "_reversa_sdd/analise-dna/design.md § Detalhe do matching passos 5-6; _reversa_sdd/code-analysis.md §4.3; _reversa_sdd/questions.md Pergunta 4"
#   target_architecture: "BC-03 Analise de DNA; core/matching.py (reject_false_positive, adaptive_min_intersection, jaccard_threshold)"
#   paradigma_alvo: "OO com DI sobre funcoes puras"
#   regras: [BR-MIGRAR-010, BR-MIGRAR-011, BR-MIGRAR-014]
#   oraculo: "analisador-genealogico/app.py (SOMENTE LEITURA)"
#   cobertura_paradigma: "equivalencia funcional estrita"

Funcionalidade: Filtros anti-falso-positivo e relaxamento de Jaccard
  Como genealogista genetico
  Quero que falsos positivos sejam rejeitados como no sistema original
  Para nao atribuir parentesco a quem nao tem

  @paridade @critico
  Cenario: Sobrenomes sem interseccao rejeitam o candidato
    Dado um match e um candidato do GEDCOM que ambos possuem sobrenomes
    E a interseccao de sobrenomes e vazia
    E nenhum dos nomes possui sufixo salvador
    Quando o filtro anti-falso-positivo e aplicado
    Entao o candidato e rejeitado
    # ATENCAO (RISK-003): a lista de sufixos salvadores (filho, neto, ...) existe
    # SOMENTE em app.py. Transcrever do legado, nao reconstruir de memoria.

  @paridade @critico
  Cenario: Sufixo salvador permite a aceitacao mesmo sem interseccao
    Dado um match e um candidato sem interseccao de sobrenomes
    E o nome contem um sufixo salvador reconhecido pelo legado
    Quando o filtro anti-falso-positivo e aplicado
    Entao o candidato NAO e rejeitado por este filtro
    E o resultado e identico ao do oraculo legado

  @paridade @critico
  Cenario: Relaxamento de Jaccard para cM alto e aplicado exatamente como no legado
    Dado um match nao-generico com total de cM maior ou igual a 150
    E cujo coeficiente de Jaccard esta entre 0.33 e 0.5
    Quando o limiar de Jaccard e aplicado
    Entao o candidato e ACEITO
    # BR-MIGRAR-014 / Pergunta 4: relaxamento INTENCIONAL de 0.5 para 0.33.
    # Trade-off deliberado, aceito com o risco de falso positivo.
    # Nao "corrigir" este comportamento: ele e comportamento congelado.

  @paridade @critico
  Cenario: Relaxamento NAO se aplica a dado generico ou a cM abaixo do limiar
    Dado um match cujo primeiro nome e generico, ou cujo cM e menor que 150
    E cujo coeficiente de Jaccard esta entre 0.33 e 0.5
    Quando o limiar de Jaccard e aplicado
    Entao o candidato e REJEITADO
    E o resultado e identico ao do oraculo legado

  @paridade @critico
  Cenario: Intersecao minima adaptativa e exigida para dado generico
    Dado um match cujo primeiro nome e generico
    E cujo nome contem dois ou mais sobrenomes
    Quando a intersecao minima e verificada
    Entao sao exigidos no minimo dois sobrenomes em comum
    E o resultado e identico ao do oraculo legado

  @paridade @critico
  Cenario: Match sem candidato no GEDCOM e registrado como descartado
    Dado um match cujo nome nao corresponde a nenhum individuo da arvore
    Quando a analise de DNA e executada
    Entao o match aparece na lista de descartados
    E o motivo registrado permite identificar a causa
    # O legado usa string livre de motivo; o alvo usa codigo tipado + mensagem.
    # A MENSAGEM visivel deve corresponder a do legado (BR-MIGRAR-028).

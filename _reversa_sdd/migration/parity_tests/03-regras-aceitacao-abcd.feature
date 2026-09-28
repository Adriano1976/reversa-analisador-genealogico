# language: pt
# spec-id: PT-003
# rastreabilidade:
#   process_flows: "_reversa_sdd/analise-dna/design.md § Detalhe do matching, passo 7 (app.py:726-793); _reversa_sdd/questions.md Pergunta 1"
#   target_architecture: "BC-03 Analise de DNA; core/matching.py (accept_match)"
#   paradigma_alvo: "OO com DI sobre funcoes puras"
#   regras: [BR-MIGRAR-013, BR-MIGRAR-015]
#   oraculo: "analisador-genealogico/app.py (SOMENTE LEITURA)"
#   cobertura_paradigma: "equivalencia funcional estrita — nucleo congelado"

Funcionalidade: Regras A/B/C/D de aceitacao do matching difuso
  Como genealogista genetico
  Quero que as regras de aceitacao sejam preservadas com fidelidade
  Para que os matches apresentados sejam os mesmos do sistema original

  @paridade @critico
  Cenario: Match nao-generico com sobrenome em comum e aceito
    Dado um match com nome nao-generico e sobrenome presente no GEDCOM
    Quando as regras de aceitacao sao avaliadas
    Entao o candidato e aceito
    E o candidato aceito e o mesmo que o oraculo legado escolhe

  @paridade @critico
  Cenario: Primeiro nome generico com dois sobrenomes exige dois em comum
    Dado um match cujo primeiro nome esta na lista de nomes genericos
    E o nome contem dois ou mais sobrenomes
    E apenas um sobrenome tem interseccao com o GEDCOM
    Quando as regras de aceitacao sao avaliadas
    Entao o candidato e rejeitado
    # ATENCAO (RISK-003): a lista de nomes genericos existe SOMENTE em app.py.
    # Deve ser TRANSCRITA do legado, nunca reconstruida de memoria.
    # Uma lista plausivel-mas-errada produz divergencia silenciosa apenas nos casos afetados.

  @paridade @critico
  Cenario: Ordem de avaliacao das regras e preservada
    Dado um match que satisfaz simultaneamente as condicoes de mais de uma regra
    Quando as regras A, B, C e D sao avaliadas
    Entao o resultado e o da PRIMEIRA regra que casa
    E o resultado e identico ao do oraculo legado
    # A ordem de avaliacao e parte do contrato: reordenar muda o resultado.

  @paridade @critico
  Cenario: Limiares literais sao preservados nos valores exatos
    Dado um match cujo score, given_ratio e similaridade de Jaccard estao proximos dos limiares
    Quando as regras de aceitacao sao avaliadas
    Entao a decisao e identica a do oraculo legado para os limiares 92, 90, 86 e 100
    # Estes limiares estao declarados como codigo morto (HARD_MIN/GIVEN_MIN) no legado,
    # mas os valores LITERAIS usados nas regras reais sao estes. Nao confundir os dois.

  @paridade @critico
  Cenario: Desempate entre candidatos segue a ordem declarada
    Dado dois candidatos com o mesmo score
    Quando o desempate e aplicado
    Entao a escolha segue a ordem: interseccao de sobrenomes, depois given, depois score
    E o candidato escolhido e identico ao do oraculo legado
    # BR-MIGRAR-015. Exige ordenacao ESTAVEL.

  @paridade @critico
  Cenario: Candidatos sem caminho ate a raiz sao descartados, nao aceitos
    Dado um match aceito pelas regras de aceitacao
    E que nao possui caminho ascendente por pais ate a pessoa-raiz
    Quando o resultado e montado
    Entao o match NAO aparece entre os aceitos
    E aparece na lista de descartados com motivo
    # BR-MIGRAR-029.

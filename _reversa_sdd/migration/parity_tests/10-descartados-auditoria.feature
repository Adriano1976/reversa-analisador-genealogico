# language: pt
# spec-id: PT-010
# rastreabilidade:
#   process_flows: "_reversa_sdd/analise-dna/design.md § Fluxos Alternativos; _reversa_sdd/analise-dna/requirements.md RF-07"
#   target_architecture: "BC-03 Analise de DNA; AGG-02 DnaAnalysis invariante I-4; entidade SkippedMatch"
#   paradigma_alvo: "OO com DI sobre funcoes puras"
#   regras: [BR-MIGRAR-029, BR-MIGRAR-030, BR-MIGRAR-033, BR-MIGRAR-034]
#   oraculo: "analisador-genealogico/app.py (SOMENTE LEITURA)"
#   cobertura_paradigma: "@invariante (completude da auditoria)"

Funcionalidade: Auditoria de matches descartados
  Como genealogista genetico
  Quero ver quais matches foram descartados e por que
  Para confiar nos resultados e investigar ausencias

  @paridade @critico @invariante
  Cenario: Todo match do CSV aparece exatamente uma vez no resultado
    Dado um CSV com N matches
    Quando a analise de DNA e concluida
    Entao cada match aparece ou entre os aceitos ou entre os descartados
    E nenhum match aparece nos dois conjuntos
    E nenhum match desaparece silenciosamente
    # Invariante I-4 de AGG-02. Completude da auditoria.

  @paridade @critico
  Cenario: Match sem correspondencia no GEDCOM e listado como descartado com motivo
    Dado um match cujo nome nao corresponde a nenhum individuo da arvore
    Quando a analise e concluida
    Entao o match aparece na lista de descartados
    E o motivo identifica a ausencia de candidato

  @paridade @critico
  Cenario: Candidato aceito mas sem caminho ancestral e listado como descartado
    Dado um match que passou pelas regras de aceitacao
    E que nao possui caminho ascendente por pais ate a pessoa-raiz
    Quando a analise e concluida
    Entao o match aparece na lista de descartados
    E o motivo identifica a ausencia de caminho
    # BR-MIGRAR-029.

  @paridade @critico
  Cenario: A contagem exibida de descartados corresponde ao numero de itens
    Dado uma analise com K matches descartados
    Quando o resultado e apresentado
    Entao o titulo exibe o numero K
    E K corresponde exatamente ao tamanho da lista de descartados

  @paridade @critico
  Cenario: Motivos descartados sao tipados no alvo sem perder a mensagem do legado
    Dado um match descartado
    Quando o payload e inspecionado
    Entao o motivo e um codigo de um vocabulario fechado
    E existe uma mensagem associada correspondente a do oraculo legado
    # O legado usa string livre. O alvo usa codigo tipado (permite assercao
    # programatica nos parity tests) MAIS a mensagem (preserva a experiencia
    # e o texto congelado de BR-MIGRAR-028). Nao substituir um pelo outro.

  @paridade @critico
  Cenario: Pre-condicoes de entrada produzem mensagens distintas e especificas
    Dado que a arvore nao esta selecionada
    Quando a analise e submetida
    Entao o erro comunica a ausencia de arvore
    E quando o CSV esta ausente, a mensagem e exatamente "Por favor, carregue o arquivo CSV de matches."
    E quando a raiz nao existe, a mensagem e exatamente "Seu nome 'X' não foi encontrado no GEDCOM."
    # BR-MIGRAR-033: no legado "GEDCOM carregado" significava "existe no estado
    # global do processo". No alvo significa "existe arvore persistida deste
    # usuario". A SEMANTICA muda; as MENSAGENS e o comportamento visivel, nao.

  @paridade @critico
  Cenario: Excecao durante a analise nao quebra a aplicacao e informa o usuario
    Dado que ocorre um erro inesperado durante a analise
    Quando o erro e tratado
    Entao a aplicacao permanece operacional
    E o usuario recebe informacao sobre a falha
    # BR-MIGRAR-034 (RF-08, Must nas tres units). A GARANTIA migra; o mecanismo
    # (render de index.html com message=) e descartado — DEV-009.

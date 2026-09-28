# language: pt
# spec-id: PT-012
# rastreabilidade:
#   process_flows: "_reversa_sdd/migration/target_screens.md; _reversa_sdd/migration/screen_modernization_decision.md (modo hibrido)"
#   target_architecture: "presentation/ (SPA React); componentes do tokens-derived.md"
#   paradigma_alvo: "OO com DI sobre funcoes puras"
#   regras: [BR-MIGRAR-028 (mensagens congeladas)]
#   deviations: [DEV-001..DEV-010]
#   oraculo: "analisador-genealogico/templates/index.html + Flask local (SOMENTE LEITURA)"
#   cobertura_paradigma: "paridade de telas — modo HIBRIDO (literal + modernizado)"
#
# ############################################################################
# # ESTADO DOS GOLDEN FILES: NENHUM FOI CAPTURADO AINDA.                      #
# # _reversa_sdd/screens/golden/manifest.yaml lista todas as entradas com     #
# # present: false. Conforme o caso de borda do Inspector (modo literal sem   #
# # golden files), os cenarios @paridade-visual sao emitidos MESMO ASSIM, mas #
# # a validacao e MANUAL ate a captura ser executada.                        #
# # Os comandos de captura estao no manifesto, em ordem recomendada.         #
# ############################################################################

Funcionalidade: Paridade de telas do sistema migrado
  Como genealogista genetico
  Quero que a interface preserve os textos e o fluxo do sistema original
  Para nao reaprender o uso e nao perder informacao

  # ==========================================================================
  # GRUPO A — TELAS LEGADAS EM MODO LITERAL (SCR-001 a SCR-005, SCR-G01 a G03)
  # Paridade TEXTUAL ESTRITA. Unica excecao: DEV-005.
  # ==========================================================================

  @paridade-visual @critico
  Cenario: Textos da tela inicial sao preservados literalmente
    Dado a tela inicial sem arvore carregada
    Quando a interface e renderizada
    Entao o titulo e exatamente "Analisador Genealógico e de DNA"
    E a instrucao e exatamente "Para começar, carregue a sua árvore genealógica em formato GEDCOM."
    E o rotulo do campo e exatamente "Arquivo GEDCOM"
    E o botao e exatamente "Carregar e Analisar"
    E o campo de arquivo e obrigatorio

  @paridade-visual @critico
  Cenario: Textos do hub de analise sao preservados literalmente
    Dado uma arvore carregada
    Quando a interface e renderizada
    Entao as abas sao exatamente "Buscar Conexão no GEDCOM" e "Analisador de DNA"
    E a aba "Buscar Conexão no GEDCOM" esta ativa por padrao

  @paridade-visual @critico
  Cenario: Textos do formulario de busca de conexao sao preservados literalmente
    Dado que a aba de busca de conexao esta ativa
    Quando o formulario e renderizado
    Entao a instrucao e exatamente "Escolha duas pessoas do arquivo GEDCOM carregado para encontrar o caminho genealógico entre elas."
    E os rotulos sao exatamente "Pessoa 1" e "Pessoa 2"
    E os campos tem o placeholder exatamente "Comece a digitar um nome..."
    E ambos sao obrigatorios
    E o botao e exatamente "Encontrar Conexão"

  @paridade-visual @critico
  Cenario: Textos do formulario de analise de DNA sao preservados literalmente
    Dado que a aba de analise de DNA esta ativa
    Quando o formulario e renderizado
    Entao a instrucao e exatamente "Carregue sua lista de matches (CSV) e insira o seu nome para encontrar as conexões confirmadas por DNA."
    E os rotulos sao exatamente "1. Lista de Matches (CSV)" e "2. Seu Nome (como está no GEDCOM)"
    E o placeholder e exatamente "Ex: João da Silva"
    E o botao e exatamente "Analisar Matches de DNA"

  @paridade-visual @critico
  Cenario: Textos dos blocos de resultado sao preservados literalmente
    Dado uma analise de DNA concluida com matches aceitos
    Quando os resultados sao exibidos
    Entao o cabecalho e exatamente "Resultados da Análise de DNA"
    E cada item exibe o prefixo "Conexão com: " seguido do nome
    E cada item exibe o total de cM
    E cada item exibe os rotulos "Caminho:" e "Relacionamento Provável (DNA):"

  @paridade-visual @critico
  Cenario: Textos do bloco de descartados sao preservados literalmente
    Dado uma analise com matches descartados
    Quando os descartados sao exibidos
    Entao o cabecalho e exatamente "Matches descartados"
    E a explicacao e exatamente "Estes nomes estavam no CSV, mas foram rejeitados pelas regras de validação. O motivo aparece abaixo."
    E as colunas sao exatamente "Nome no CSV" e "Motivo"

  @paridade-visual @critico
  Cenario: Textos do resultado de busca de conexao sao preservados literalmente
    Dado uma busca de conexao concluida
    Quando o resultado e exibido
    Entao o cabecalho e exatamente "Resultado da Busca de Conexão"
    E o cabecalho do cartao exibe "Conexão entre: " seguido dos dois nomes separados por " e "
    E o rotulo "Caminho:" e exibido

  @paridade-visual @critico
  Cenario: Texto do indicador de carregamento e preservado literalmente
    Dado que um formulario foi submetido
    Quando o estado de carregamento e exibido
    Entao o texto e exatamente "Analisando... Isso pode levar alguns segundos."

  @paridade-visual @critico
  Cenario: Mensagens de erro do backend sao preservadas literalmente
    Dado cada um dos cenarios de erro do sistema
    Quando a mensagem e exibida ao usuario
    Entao as mensagens sao exatamente as do legado, incluindo:
      | Nenhum arquivo GEDCOM enviado.                        |
      | Nenhum arquivo selecionado.                           |
      | Por favor, carregue o arquivo CSV de matches.         |
      | Seu nome 'X' não foi encontrado no GEDCOM.            |
      | Pessoa 1 'X' não encontrada.                          |
      | Pessoa 2 'X' não encontrada.                          |
      | Nenhuma conexão encontrada entre 'X' e 'Y'.           |
      | Conexão direta encontrada (ancestral comum).          |
      | Conexão indireta encontrada (via casamento/afinidade).|
    # BR-MIGRAR-028. Estas mensagens sao os literais que sustentam os
    # criterios de aceitacao Gherkin das tres units de descoberta.

  @paridade-visual @critico
  Cenario: A unica correcao de texto autorizada e aplicada
    Dado o controle de fechar do bloco de alerta
    Quando sua acessibilidade e inspecionada
    Entao o rotulo acessivel e "Fechar"
    E NAO e "Close"
    # DEV-005. Unica excecao autorizada a invariante de diff textual zero.
    # Aprovacao explicita de revisao linguistica registrada na decisao.

  # ==========================================================================
  # EXCECOES DECLARADAS — deviations aprovadas que suspendem a paridade estrita
  # ==========================================================================

  @paridade-visual @critico
  Cenario: Identificador de arvore nao e o nome do arquivo do cliente
    Dado que uma arvore esta carregada
    Quando o payload e o estado da interface sao inspecionados
    Entao NAO existe campo oculto com o nome do arquivo do cliente
    E a arvore e identificada por um identificador proprio
    # DEV-002.

  @paridade-visual @critico
  Cenario: Sugestoes de nomes vem de busca, nao de lista embutida no HTML
    Dado que uma arvore esta carregada
    Quando os campos de nome oferecem sugestoes
    Entao as sugestoes vem de consulta ao backend
    E a lista completa de nomes NAO esta embutida no HTML inicial
    # DEV-003.

  @paridade-visual @critico
  Cenario: O loading e local ao formulario submetido
    Dado que existem resultados de uma operacao anterior na tela
    Quando um novo formulario e submetido
    Entao o indicador de carregamento e exibido
    E os resultados anteriores PERMANECEM visiveis
    # DEV-010 (aprovada). O legado ocultava a regiao de resultados inteira
    # a cada submit, fazendo o usuario perder a analise anterior.

  @paridade-visual @critico
  Cenario: O alvo nao emite sintaxe Mermaid
    Dado um caminho genealogico resolvido
    Quando a resposta do backend e inspecionada
    Entao ela contem a estrutura decomposta do caminho
    E NAO contem sintaxe de diagrama Mermaid
    # DEV-004. A comparacao deve asserir sobre a ESTRUTURA (ramos, MRCA,
    # par de afinidade), nunca sobre a string do diagrama.
    # Ver 06-decomposicao-caminho.feature — RISK-011.

  # ==========================================================================
  # GRUPO B — TELAS NOVAS EM MODO MODERNIZADO (SCR-006 a SCR-010)
  # CONTRACT TEST DE TELA. Sem comparacao byte-a-byte: nao ha origem no legado.
  # Exigencia: hierarquia, eventos, conteudo textual e os QUATRO estados.
  # ==========================================================================

  @paridade @critico
  Cenario: Tela de autenticacao respeita o contrato declarado
    Dado a tela de autenticacao
    Quando ela e inspecionada
    Entao ela implementa os quatro estados: idle, loading, error e success
    E possui campos de email e senha, ambos obrigatorios
    E o evento de submissao corresponde ao endpoint de criacao de sessao declarado

  @paridade @critico
  Cenario: Tela de arvores e escopada pelo usuario autenticado
    Dado a tela "Minhas árvores"
    Quando ela e inspecionada
    Entao ela implementa os quatro estados
    E lista apenas arvores do usuario autenticado
    E oferece estado vazio com acao de carregar uma arvore

  @paridade @critico @regulatorio
  Cenario: Tela de consentimento bloqueia o uso sem registro
    Dado um usuario sem consentimento registrado
    Quando ele tenta criar uma arvore
    Entao a operacao e impedida pelo backend
    E a tela de consentimento oferece o controle de concessao
    # BR-HUMANA-007. A tela orienta; a INVARIANTE e aplicada no backend.

  @paridade @critico @regulatorio
  Cenario: Tela de conta oferece o direito de exclusao
    Dado a tela de conta e dados
    Quando ela e inspecionada
    Entao ela oferece exportacao dos dados do titular
    E oferece a exclusao da conta com confirmacao explicita
    E exibe o prazo de retencao vigente

  @paridade @critico
  Cenario: Tela de historico exibe resultados persistidos sem recalcular
    Dado uma analise de DNA concluida anteriormente
    Quando o historico e consultado e a analise e reaberta
    Entao os resultados exibidos sao os PERSISTIDOS
    E o total de cM nao e recalculado
    # AD-03: o total_cm persistido e a autoridade. O banco nao e calculadora.

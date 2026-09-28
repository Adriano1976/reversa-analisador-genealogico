# language: pt
# spec-id: PT-011
# rastreabilidade:
#   process_flows: "_reversa_sdd/upload-gedcom/design.md § Estado Interno (globais); _reversa_sdd/domain.md §4 (ausencia de autenticacao)"
#   target_architecture: "BC-01 Identidade e Tenancy; BC-02/BC-03 com owner_id; AD-02; ports/tree_repository.py"
#   paradigma_alvo: "OO com DI sobre funcoes puras"
#   regras: [BR-HUMANA-004, BR-DESCARTAR-001, BR-DESCARTAR-002, BR-DESCARTAR-003]
#   riscos: [RISK-005 (critico), RISK-001]
#   oraculo: "NAO APLICAVEL — o legado nao tem multiusuario nem autenticacao."
#            Este fluxo e CONSTRUCAO NOVA; a paridade aqui e com o brief e a arquitetura,
#            nao com o comportamento do legado.
#   cobertura_paradigma: "@isolamento (dimensao NOVA — nao prevista na matriz) + @composicao/@imutabilidade adaptados"

Funcionalidade: Isolamento de dados entre usuarios
  Como responsavel pelo tratamento de dados geneticos
  Quero garantir que nenhum usuario acesse dados de outro
  Para cumprir LGPD/GDPR e evitar vazamento irreversivel

  # #######################################################################
  # # FLUXO SEM ORACULO NO LEGADO. A paridade aqui nao e comportamental:   #
  # # e conformidade com um requisito NOVO. Registrado explicitamente     #
  # # para nao simular paridade onde ela nao existe.                     #
  # #######################################################################

  @paridade @critico @regulatorio @isolamento
  Cenario: Usuario nao acessa arvore de outro usuario
    Dado o usuario A autenticado com uma arvore propria
    E o usuario B autenticado com uma arvore propria
    Quando o usuario A solicita a arvore do usuario B
    Entao a resposta e 404
    E a resposta NAO e 403
    # Decisao deliberada: 403 confirmaria a EXISTENCIA do recurso, vazando
    # informacao sobre outro usuario. 404 nao revela nada.

  @paridade @critico @regulatorio @isolamento
  Cenario: Usuario nao acessa analise de outro usuario
    Dado o usuario A com uma analise de DNA concluida
    E o usuario B autenticado
    Quando o usuario B solicita a analise do usuario A
    Entao a resposta e 404

  @paridade @critico @regulatorio @isolamento
  Cenario: Listagem de arvores e sempre escopada pelo dono
    Dado que existem arvores de tres usuarios distintos
    Quando um usuario lista suas arvores
    Entao apenas as arvores com owner_id igual ao dele sao retornadas
    E nenhuma arvore de outro usuario aparece

  @paridade @critico @regulatorio @isolamento
  Cenario: Nenhuma operacao de leitura ou escrita existe sem escopo de dono
    Dado o contrato do repositorio de arvores
    Quando suas assinaturas sao inspecionadas
    Entao toda operacao de leitura e escrita exige o identificador do dono
    E nao existe variante sem escopo
    # AD-02: owner_id e INVARIANTE de aggregate, nao filtro de consulta.
    # Um unico ponto de leitura esquecido vaza dado genetico, e o erro e
    # invisivel em teste felizario.

  @paridade @critico @regulatorio @isolamento
  Cenario: Exclusao de conta remove todos os dados geneticos do titular
    Dado o usuario A com arvores, arquivos e analises
    Quando A solicita a exclusao da propria conta
    Entao suas arvores sao removidas
    E seus arquivos enviados sao removidos
    E suas analises sao removidas
    E nao resta nenhum dado genetico orfao associado a A
    # BR-HUMANA-007 e invariante I-3 de AGG-03. O registro de auditoria de
    # acesso sobrevive (ON DELETE SET NULL) por decisao de design — mas ele
    # nao contem dado genetico.

  @paridade @critico @regulatorio @isolamento
  Cenario: Arquivo enviado e escopado por dono e com chave gerada pelo servidor
    Dado um usuario autenticado que envia um arquivo GEDCOM cujo nome original contem caracteres de caminho
    Quando o arquivo e armazenado
    Entao a chave de armazenamento e gerada pelo servidor
    E o nome original e preservado apenas como metadado de exibicao
    E o nome original NAO e usado como caminho nem como identificador
    # BR-DESCARTAR-003 e BR-HUMANA-001. O legado salvava com o nome do cliente
    # em pasta compartilhada, com colisao sobrescrevendo.

  @paridade @critico @isolamento
  Cenario: Duas arvores de usuarios diferentes sao processadas concorrentemente sem interferencia
    Dado o usuario A com a arvore TA e o usuario B com a arvore TB
    Quando ambos executam analise de DNA simultaneamente
    Entao o resultado de A corresponde integralmente a TA
    E o resultado de B corresponde integralmente a TB
    E nenhum resultado contem dados da arvore do outro
    # BR-DESCARTAR-001: o legado usava globais sobrescritos a cada parse
    # (people, families, graph, child_to_family). Em multi-worker, requisicoes
    # simultaneas corrompiam a analise uma da outra. Este cenario prova que
    # o estado global NAO foi transportado.

  @paridade @critico @isolamento
  Cenario: O nucleo nao possui estado mutavel compartilhado
    Dado o codigo do nucleo de calculo
    Quando suas dependencias de importacao sao inspecionadas
    Entao o nucleo nao importa framework web nem camada de persistencia
    E o nucleo nao mantem variavel de modulo mutavel compartilhada entre chamadas
    # Salvaguarda da Onda 1: se core/ importar fastapi, sqlalchemy, pydantic ou
    # flask, ou mantiver estado de modulo, o harness diferencial perde valor
    # e a paridade deixa de ser isolavel (AD-01).

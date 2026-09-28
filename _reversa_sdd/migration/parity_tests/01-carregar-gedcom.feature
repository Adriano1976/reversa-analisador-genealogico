# language: pt
# spec-id: PT-001
# rastreabilidade:
#   process_flows: "_reversa_sdd/code-analysis.md §3 (load_gedcom_and_build_graph, build_graph_from_parser); _reversa_sdd/upload-gedcom/design.md § Detalhe do fluxo de parsing"
#   target_architecture: "BC-02 Arvore Genealogica; core/parser.py, core/tree.py; AGG-01 GedcomTree"
#   paradigma_alvo: "OO com DI sobre funcoes puras (paradigm_decision.md, opcao 3 hibrido)"
#   regras: [BR-MIGRAR-001, BR-MIGRAR-002, BR-MIGRAR-003, BR-MIGRAR-004, BR-MIGRAR-005]
#   oraculo: "analisador-genealogico/app.py (SOMENTE LEITURA) — nunca reconstructed/"
#   cobertura_paradigma: "@invariante (procedural -> OO com DI)"

Funcionalidade: Carregamento e parsing de GEDCOM
  Como genealogista genetico
  Quero carregar minha arvore GEDCOM
  Para que as analises de DNA e busca de caminho possam ser executadas

  @paridade @critico @invariante
  Cenario: GEDCOM valido produz grafo bidirecional e lista de nomes ordenada
    Dado um arquivo GEDCOM valido com registros INDI e FAM
    Quando o candidato e o oraculo legado parseiam o mesmo arquivo
    Entao a lista de nomes de exibicao e identica nas duas saidas
    E a lista esta em ordem alfabetica
    E o numero de pessoas e identico
    E o numero de familias e identico
    E para cada familia, os vinculos HUSB, WIFE e CHIL sao identicos
    E o indice filho-para-familia (FAMC) e identico

  @paridade @critico @invariante
  Cenario: Nome ausente e apresentado com o literal "Sem Nome"
    Dado um arquivo GEDCOM contendo um individuo INDI SEM o objeto de nome
    Quando o arquivo e parseado
    Entao o nome de exibicao desse individuo e exatamente "Sem Nome"
    # Caminho do fallback do oraculo: get_name = person.name.format() if person and person.name else "Sem Nome"

  @paridade @critico @invariante
  Cenario: Nome presente com formato VAZIO produz string vazia, nao "Sem Nome"
    Dado um arquivo GEDCOM contendo um individuo cujo objeto de nome EXISTE mas cujo formato resulta em texto vazio
    Quando o arquivo e parseado
    Entao o nome de exibicao desse individuo e string VAZIA
    E NAO e "Sem Nome"
    # DESCOBERTO EXECUTANDO O ORACULO SOBRE DADOS REAIS (BR-MIGRAR-003, correcao factual).
    # Medicao nas 6 arvores reais do usuario (55.523 nomes):
    #   string vazia = 318 ocorrencias (0,57%)   |   literal "Sem Nome" = 0 ocorrencias
    # O fallback "Sem Nome" e MAIS ESTREITO do que a spec afirmava: ele so dispara
    # quando person.name e ausente/falsy, NAO quando o formato resulta vazio.
    # ATENCAO: implementar o fallback "correto" (sempre "Sem Nome") QUEBRA PARIDADE.
    # Consequencia visivel: a string vazia entra na lista de nomes como opcao em branco.

  @paridade @critico
  Cenario: Nomes vazios sao preservados na ordenacao alfabetica
    Dado um arquivo GEDCOM com pessoas de nome vazio e pessoas nomeadas
    Quando a lista de nomes e ordenada
    Entao as entradas vazias aparecem PRIMEIRO
    E a ordem total e identica a do oraculo legado
    # String vazia ordena antes de qualquer nome. A ordenacao e sorted() puro.

  @paridade @critico @invariante
  Cenario: Invariante de integridade referencial e respeitada ou reportada
    Dado um arquivo GEDCOM com uma referencia HUSB, WIFE, CHIL, FAMC ou FAMS apontando para xref inexistente
    Quando o arquivo e parseado
    Entao o comportamento observavel e comparado ao do oraculo legado
    E a decisao de aceitar-com-sinalizacao ou rejeitar esta registrada como divergencia explicita
    # ATENCAO: o legado ACEITA (o grafo apenas nao ganha a aresta). Rejeitar e MELHORIA e
    # portanto QUEBRA PARIDADE. Ver data_migration_plan.md § Notas (T-01).
    # Enquanto nao decidido, este cenario documenta a divergencia em vez de esconde-la.

  @paridade @critico
  Cenario: Ausencia de arquivo e ausencia de nome de arquivo sao erros distintos
    Dado uma requisicao de upload sem o campo de arquivo
    Quando a validacao e executada
    Entao a mensagem e exatamente "Nenhum arquivo GEDCOM enviado."
    E nenhuma arvore e persistida

  @paridade @critico
  Cenario: Arquivo com nome vazio produz erro distinto
    Dado uma requisicao de upload com o campo de arquivo presente mas filename vazio
    Quando a validacao e executada
    Entao a mensagem e exatamente "Nenhum arquivo selecionado."
    E nenhuma arvore e persistida

  @paridade @critico
  Cenario: GEDCOM malformado nao quebra a aplicacao
    Dado um arquivo GEDCOM corrompido
    Quando o parse e tentado
    Entao o comportamento observavel e comparado ao do oraculo legado
    E a aplicacao permanece operacional
    E a mensagem de erro e identica a do oraculo

  @paridade @critico @invariante
  Cenario: Arvore carregada pertence a exatamente um dono
    Dado um usuario autenticado
    Quando ele importa um GEDCOM
    Entao a arvore persistida tem owner_id igual ao do usuario
    E o nome original do arquivo do cliente e armazenado apenas como metadado
    E o nome original nao e usado como identificador nem como caminho de armazenamento

  @paridade @critico @ordem
  Cenario: Ordem de leitura dos registros e preservada
    Dado um arquivo GEDCOM com multiplos individuos
    Quando o arquivo e parseado
    Entao cada pessoa tem seu source_ordinal correspondente a ordem de leitura no arquivo
    # Esta ordem determina QUAL id o "primeiro ID" escolhe em homonimos (BR-MIGRAR-026/027)
    # e a ordem de insercao das arestas do grafo (BR-MIGRAR-024).
    # Uma ordem diferente muda resultados de busca de caminho sem gerar erro.

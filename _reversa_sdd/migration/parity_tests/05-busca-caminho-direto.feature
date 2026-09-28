# language: pt
# spec-id: PT-005
# rastreabilidade:
#   process_flows: "_reversa_sdd/busca-caminho/design.md § Detalhe da conexao direta; _reversa_sdd/code-analysis.md §3 (find_ancestral_path)"
#   target_architecture: "BC-04 Parentesco e Caminho; core/pathfinding.py (find_ancestral_path); core/tree.py (find_person_by_name)"
#   paradigma_alvo: "OO com DI sobre funcoes puras"
#   regras: [BR-MIGRAR-022, BR-MIGRAR-023, BR-MIGRAR-026, BR-MIGRAR-027]
#   oraculo: "analisador-genealogico/app.py (SOMENTE LEITURA)"
#   cobertura_paradigma: "@invariante + @ordem"

Funcionalidade: Busca de conexao direta por ancestral comum
  Como genealogista genetico
  Quero encontrar o caminho genealogico entre duas pessoas
  Para entender como elas se relacionam

  @paridade @critico
  Cenario: Conexao direta entre duas pessoas com ancestral comum
    Dado duas pessoas da arvore que compartilham um ancestral comum
    Quando a busca de caminho direta e executada
    Entao o caminho ascendente a partir da pessoa 1 e identico ao do oraculo legado
    E o caminho descendente ate a pessoa 2 e identico ao do oraculo legado
    E o ancestral comum identificado e o mesmo
    E a mensagem exibida e exatamente "Conexão direta encontrada (ancestral comum)."

  @paridade @critico
  Cenario: Ancestral comum de menor profundidade e escolhido
    Dado duas pessoas que compartilham mais de um ancestral
    Quando a busca bidirecional e executada
    Entao o ancestral comum escolhido e o de MENOR profundidade
    E a escolha e identica a do oraculo legado
    # O legado usa BFS BIDIRECIONAL com expansao intercalada — NAO usa
    # nx.lowest_common_ancestor. A escolha difere entre as duas abordagens
    # quando ha multiplos MRCAs. Nao substituir o algoritmo.

  @paridade @critico
  Cenario: A mesma pessoa nas duas pontas produz caminho trivial
    Dado o mesmo identificador informado para pessoa 1 e pessoa 2
    Quando a busca de caminho e executada
    Entao o caminho retornado e o trivial
    E o comportamento e identico ao do oraculo legado

  @paridade @critico
  Cenario: Limite de profundidade e estourado
    Dado duas pessoas cuja conexao exige mais de 20 niveis de ascendencia por pais
    Quando a busca direta e executada
    Entao a busca direta falha
    E o fluxo prossegue para a busca indireta
    # BR-MIGRAR-023: o estouro do limite NAO e apenas performance —
    # ele MUDA O FLUXO (cai para a conexao indireta). Comportamento, nao otimizacao.

  @paridade @critico
  Cenario: Pessoa inexistente produz mensagem especifica por posicao
    Dado que a pessoa 1 informada nao existe na arvore
    Quando a busca e executada
    Entao a mensagem e exatamente "Pessoa 1 'X' não encontrada."
    E quando o mesmo ocorre com a pessoa 2, a mensagem e exatamente "Pessoa 2 'Y' não encontrada."

  @paridade @critico
  Cenario: Ausencia de qualquer conexao produz mensagem especifica
    Dado duas pessoas existentes na arvore sem nenhuma conexao direta nem indireta
    Quando a busca e executada
    Entao a mensagem e exatamente "Nenhuma conexão encontrada entre 'X' e 'Y'."

  @paridade @critico @ordem
  Cenario: Homonimos resolvem para o primeiro identificador, e a ambiguidade e sinalizada
    Dado duas pessoas na arvore com exatamente o mesmo nome de exibicao
    Quando o nome e resolvido
    Entao o identificador escolhido e o PRIMEIRO na ordem de leitura do arquivo
    E o resultado do caminho e o mesmo do oraculo legado
    E a resposta sinaliza que o nome era ambiguo, sem alterar o resultado padrao
    # BR-MIGRAR-026 / BR-HUMANA-003 (decisao humana): o default NAO muda (1o ID);
    # a ambiguidade e apenas SINALIZADA no payload. Nao exigir desambiguacao —
    # isso quebraria o criterio de paridade #1 do brief.

  @paridade @critico @ordem
  Cenario: Ordem de insercao das arestas do grafo e preservada
    Dado um GEDCOM cujos registros produzem multiplos caminhos de mesmo comprimento
    Quando o caminho indireto e calculado sobre o grafo
    Entao o caminho retornado e o mesmo do oraculo legado
    # BR-MIGRAR-024: shortest_path com caminhos de mesmo comprimento retorna
    # aquele determinado pela ORDEM DE INSERCAO das arestas. Ordem diferente
    # muda o caminho sem gerar erro.

# language: pt
# spec-id: PT-008
# rastreabilidade:
#   process_flows: "_reversa_sdd/code-analysis.md §4.1 e §4.2; _reversa_sdd/domain.md §2.3; _reversa_sdd/analise-dna/design.md § Detalhe do matching passos 1-5"
#   target_architecture: "BC-03 Analise de DNA; core/mojibake.py, core/normalization.py, core/matching.py (fuzzy_score); core/constants.py"
#   paradigma_alvo: "OO com DI sobre funcoes puras"
#   regras: [BR-MIGRAR-006, BR-MIGRAR-007, BR-MIGRAR-008, BR-MIGRAR-009, BR-MIGRAR-012]
#   oraculo: "analisador-genealogico/app.py (SOMENTE LEITURA)"
#   cobertura_paradigma: "equivalencia funcional estrita — nucleo mais congelado do sistema"

Funcionalidade: Limpeza de mojibake, normalizacao e pontuacao do matching viral
  Como genealogista genetico
  Quero que nomes com acentos corrompidos ainda encontrem seus correspondentes
  Para nao perder parentes por problema de encoding do exportador

  @paridade @critico
  Cenario: Mojibake de acentos e corrigido como no legado
    Dado um nome contendo sequencias corrompidas de acentuacao portuguesa
    Quando a limpeza de mojibake e aplicada
    Entao o nome corrigido e IDENTICO ao produzido pelo oraculo legado
    # BR-MIGRAR-006. ATENCAO (BR-HUMANA-005, decisao humana): a tabela de
    # substituicoes do legado e MANUAL e INCOMPLETA. Ela deve ser transcrita
    # FIELMENTE, INCLUSIVE AS LACUNAS, sem adicionar substituicoes novas.
    # Corrigir com estrategia robusta (ftfy, deteccao por bytes) MELHORARIA a
    # cobertura real mas MUDARIA RESULTADOS — violando "matching congelado".

  @paridade @critico
  Cenario: Re-encoding Latin-1 para UTF-8 e tentado e seus limites sao preservados
    Dado um nome cujos bytes sao Latin-1 interpretados como UTF-8
    Quando a correcao de encoding e aplicada
    Entao o nome corrigido e identico ao do oraculo legado
    E quando a string nao e valida em Latin-1, o comportamento e o do legado
    # O legado lanca excecao neste caso e a captura no controller. No alvo a
    # funcao pura deve ser TOTAL (nunca lancar sobre entrada de usuario) e
    # reproduzir o comportamento OBSERVAVEL do legado.

  @paridade @critico
  Cenario: Normalizacao de nome produz o mesmo resultado byte a byte
    Dado uma lista de nomes com acentos, cedilha e maiusculas mistas
    Quando a normalizacao e aplicada
    Entao cada nome normalizado e identico ao do oraculo legado
    # NFKD + remocao de acentos + minusculas. A ORDEM das operacoes importa.

  @paridade @critico
  Cenario: Decomposicao em nome proprio, sobrenomes e sufixos e identica
    Dado uma lista de nomes completos em portugues
    Quando a decomposicao e aplicada
    Entao o nome proprio, o conjunto de sobrenomes e os sufixos sao identicos aos do oraculo legado

  @paridade @critico
  Cenario: Equivalentes de grafia sao aplicados exatamente como no legado
    Dado nomes contendo variantes de grafia reconhecidas pelo legado
    Quando o matching e executado
    Entao as variantes casam entre si como no oraculo legado
    # ATENCAO (RISK-003): a TABELA de equivalentes de grafia existe SOMENTE em
    # app.py. Deve ser EXTRAIDA MECANICAMENTE do legado, nunca reconstruida.
    # Uma tabela plausivel mas incompleta produz divergencia silenciosa.

  @paridade @critico
  Cenario: Abreviacoes de sobrenome com no minimo tres caracteres sao reconhecidas
    Dado um match cujo sobrenome esta abreviado
    E o prefixo tem tres ou mais caracteres
    Quando o pool de candidatos e construido
    Entao o candidato correspondente entra no pool
    E o resultado e identico ao do oraculo legado

  @paridade @critico
  Cenario: Score de matching difuso e calculado com os pesos exatos
    Dado um par de nomes com token_sort, partial e given conhecidos
    E uma interseccao de sobrenomes conhecida
    Quando o score e calculado
    Entao o score e IDENTICAMENTE igual ao do oraculo legado
    # Formula congelada: 0.55*token_sort + 0.25*partial + 0.20*given + InterBonus
    # InterBonus = 8.0*interseccao - 4.0*sobrenomes_comuns
    # ATENCAO ARITMETICA (RISK-004): pontos flutuantes NAO sao associativos.
    # Nomear as constantes e permitido; mudar valor ou ORDEM DE SOMA nao e.

  @paridade @critico
  Cenario: Ordem de avaliacao dos candidatos e deterministica
    Dado dois candidatos com scores muito proximos
    Quando o melhor candidato e escolhido
    Entao a escolha e identica a do oraculo legado em execucoes repetidas
    E a escolha nao depende de ordem de dicionario ou de paralelizacao

  @paridade @critico
  Cenario: Indices de busca reproduzem o pool de candidatos do legado
    Dado um nome com correspondencia exata normalizada no GEDCOM
    Quando o pool de candidatos e construido
    Entao apenas o candidato exato e considerado
    E quando nao ha exato, o pool por sobrenome e identico ao do legado
    E quando nao ha por sobrenome, o pool por prefixo e identico ao do legado
    # BR-MIGRAR-008. Um pool DIFERENTE produz matches diferentes mesmo com o
    # mesmo score — a cascata exact -> sobrenome -> prefixo e o contrato.

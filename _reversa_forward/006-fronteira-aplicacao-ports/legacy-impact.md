# Impacto no legado — feature `006-fronteira-aplicacao-ports`

> Feature: `006-fronteira-aplicacao-ports` (Onda 2 do `_reversa_sdd/migration/cutover_plan.md`)
> Data: 2026-10-07
> Âncora: `_reversa_sdd/architecture.md` + `_reversa_sdd/domain.md` (legado)
> Executor: `/reversa-coding`, sobre `actions.md` revisado pós-auditoria

## Resumo

A Onda 2 move a **orquestração** de `index()` para três casos de uso, atrás de
portas, com exceções de domínio tipadas. **O núcleo não é tocado**: nenhum limiar,
peso, ordem de avaliação ou critério de matching muda (`RN-01`, `RF-15`).

Medido, não afirmado:

| Instrumento | Antes | Depois |
|---|---|---|
| Paridade diferencial (6 fixtures, oráculo congelado) | `100%`, exit 0 | `100%`, exit 0 |
| Mensagens de tela (19 casos: status, classe do alerta e texto) | `mensagens_antes.json` | `mensagens_depois.json` — **zero divergência** |
| Passos de domínio em `index()` | presentes | **zero** (`evidence/T020-varredura.txt`) |
| Testes | `178 passed, 15 errors` | nenhum teste removido, desabilitado ou reescrito |

O impacto é de **forma**, não de comportamento. Por isso nenhum item abaixo é
`CRITICAL`: o que um `CRITICAL` significaria aqui — divergência observável — foi
medido e é zero.

## 1. Arquivos afetados

| Arquivo afetado | Componente (`architecture.md` §3) | Tipo | Severidade | Justificativa |
|---|---|---|---|---|
| `src/application/__init__.py` | novo pacote `application/` | `componente-novo` | MEDIUM | O vocabulário da camada: `Desfecho` e `nomes_de_exibicao`. Passa a existir uma camada entre a rota e o núcleo |
| `src/application/upload_gedcom.py` | novo pacote `application/` | `componente-novo` | MEDIUM | Caso de uso do upload. Absorve a orquestração que estava em `index()` |
| `src/application/path_search.py` | novo pacote `application/` | `componente-novo` | MEDIUM | Caso de uso da busca; é onde o campo de desfecho nasce (`D-11`) |
| `src/application/dna_analysis.py` | novo pacote `application/` | `componente-novo` | MEDIUM | Caso de uso da análise de DNA |
| `src/application/traducao.py` | novo pacote `application/` | `componente-novo` | HIGH | Tabela exceção → literal. É o único lugar onde o texto de tela vive fora do template; um erro aqui muda o que o operador lê |
| `src/ports/__init__.py` | novo pacote `ports/` | `componente-novo` | MEDIUM | Três `Protocol`: armazenamento, carregador de árvores e repositório de árvores (`RF-02`, `RF-08`, `D-02`, `D-03`) |
| `src/ports/adaptadores.py` | novo pacote `ports/` | `componente-novo` | HIGH | `ArmazenamentoEmDisco` e `CarregadorDeArvoresGedcom`. A validação antes da gravação (`RF-10`) passa a ser responsabilidade declarada aqui |
| `src/core/erros.py` | `core/` | `componente-novo` | MEDIUM | Hierarquia de exceção de domínio. Fica em `core/` por `D-01` (🟡, ver §4) |
| `src/app.py` | a rota (`index()`) | `regra-alterada` | HIGH | `index()` deixa de orquestrar: chama caso de uso, traduz exceção, renderiza. É a mudança de maior superfície da onda e a que mais depende de medição |
| `src/core/dna_analysis.py` | `core/` | `regra-alterada` | LOW | Só o **tipo** levantado em dois pontos muda (`PessoaNaoEncontrada`, `DnaCsvSemColunas`). Nenhum caractere das mensagens mudou |
| `src/core/genetic_evidence.py` | `core/` | `regra-alterada` | LOW | Idem, em um ponto: `DnaCsvSemColunas` |
| `src/parsers/csv_ingest.py` | `parsers/` | `regra-alterada` | LOW | `CsvIlegivel` fecha a lacuna de rastreabilidade do achado `A002` (`RF-21`). O fallback Latin-1 não foi tocado (`RN-03`) |
| `src/parsers/gedcom_parser.py` | `parsers/` | `componente-extinto` (parcial) | LOW | Sai a casca `load_gedcom_and_build_graph` (`D-06`). `carregar_arvore` e o `Tree` ficam **idênticos** — a forma da árvore é contrato de paridade (`D-12`) |
| `_reversa_sdd/parity/harness.py` | instrumento de paridade | `regra-alterada` | MEDIUM | **Só o coletor do CANDIDATO.** Ele chamava a casca removida; passou a derivar `names` da árvore. O coletor do ORÁCULO não foi tocado. Paridade remedida: 100% |
| `tests/test_upload.py` | suíte | `regra-alterada` | LOW | Migrado da casca para a árvore. A mesma migração corrigiu um defeito latente: o helper não chamava `guardar(...)`, e os testes que leem `atual()` dependiam da árvore guardada por um teste ANTERIOR |
| `tests/test_arvore_devolvida.py` | suíte | `regra-alterada` | LOW | O teste que fixava o contrato antigo passou a derivar a lista da árvore. Asserções preservadas |
| `tests/conftest.py` | suíte | `componente-novo` | LOW | Fixtures temporárias que funcionam nesta máquina (`pasta_temporaria`, `cliente_de_upload`) e o `collect_ignore` da cicatriz. Ver `evidence/README-evidencias.md` §2 |
| `tests/test_erros_de_dominio.py` | suíte | `componente-novo` | LOW | `T009`/`T010`: a forma da hierarquia e os quatro pontos de detecção |
| `tests/test_traducao_de_erros.py` | suíte | `componente-novo` | LOW | `T024`/`T029` |
| `tests/test_desfecho_do_resultado.py` | suíte | `componente-novo` | LOW | `T026` |
| `tests/test_porta_de_armazenamento.py` | suíte | `componente-novo` | LOW | `T027`/`T028` |
| `tests/test_upload_seguranca.py` | suíte | `regra-alterada` (aditivo) | LOW | `T030`/`T031`. **Nada existente foi alterado**; a classe nova usa o fixture novo |
| `_reversa_forward/006-.../onboarding.md` | artefato do Reversa | `delta-de-contrato-externo` | LOW | Dois padrões de verificação que não podiam casar com o template. Correção medida em `T025` |

**Não afetados, verificado:** `src/templates/index.html`, `src/reporting/`,
`src/utils/`, `src/core/` fora dos três pontos citados. O `git status` da entrega
mostra exatamente os arquivos acima.

## 2. Diff conceitual por componente

### 2.1 A rota (`src/app.py`)

Antes: `index()` continha os três fluxos inteiros — validava o upload, resolvia o
caminho, parseava, chamava o núcleo, decidia o modo de renderização por
`success` e por uma comparação de `path_result is None`, e traduzia erro com três
`except Exception` genéricos.

Depois: `index()` faz quatro coisas, e só quatro — lê o formulário, chama o caso
de uso, traduz o que voltou, renderiza. A varredura por AST
(`evidence/_t020_varredura.py`) mede zero chamada de domínio, e verifica que as
cinco funções de dependência (`read_csv_with_fallback`, `detectar_colunas`,
`aggregate_matches`, `generate_mermaid_graph`,
`generate_mermaid_graph_indirect_bridge`) aparecem **apenas** na montagem única do
pacote `Dependencias` — que é montagem de borda, não passo de domínio.

**O que continua na rota, de propósito:** as duas guardas de formulário do upload,
a guarda de "arquivo CSV ausente", as duas mensagens de guarda da árvore
(`"Erro: Arquivo GEDCOM não encontrado."`, `"Erro: Arquivo '{ref}' não existe
mais."`), o handler de `413` e os `except Exception` de último recurso. Nenhuma
delas é decisão de negócio: todas decidem sobre o **formulário** ou sobre falha
inesperada.

### 2.2 O par de literais que quase se perdeu

Medido com a sonda antes de escrever a tabela de tradução: **duas condições
parecidas têm apresentações diferentes**, e escrever a tabela de cabeça teria
quebrado a paridade.

| Condição | Texto na tela |
|---|---|
| GEDCOM recusado na validação | `Arquivo não reconhecido como GEDCOM: <motivo>.` — **sem** prefixo |
| Raiz do DNA ausente do GEDCOM | `Ocorreu um erro: Seu nome 'X' não foi encontrado no GEDCOM.` — **com** prefixo |
| CSV sem colunas obrigatórias | `Ocorreu um erro: Colunas de Nome e cM não encontradas no CSV. ...` — com prefixo |
| CSV ilegível | `Ocorreu um erro: Não foi possível ler o arquivo CSV. ...` — com prefixo |

O prefixo existe porque, no legado, as três últimas nascem **dentro** do fluxo de
DNA e caem no `except Exception` genérico daquele ramo. A primeira nasce no
caminho de gravação e sai direto. A tabela de tradução reproduz o prefixo onde ele
existe — e é por isso que ela é uma tabela de **funções**, e não um mapa de classe
para constante.

### 2.3 As exceções de domínio (`src/core/erros.py`)

`ErroDeDominio(ValueError)` como raiz, com quatro tipos irmãos: `PessoaNaoEncontrada`,
`GedcomNaoSuportado`, `DnaCsvSemColunas` e `CsvIlegivel`.

A herança de `ValueError` é **deliberada e verificável**: as quatro asserções de
`tests/test_confrontacao_gedcom_dna.py:920`, `:936` e `tests/test_dna_analysis.py:219`,
`:241` capturam `ValueError` e conferem o texto. Sem a herança, a `RF-05` e o
cenário "A suíte existente não pode ser reduzida" seriam violados pela própria
feature que existe para preservar comportamento. **Consequência declarada:** todo
`except ValueError` que não seja de domínio precisa ser distinguido pelo **tipo**,
nunca pela mensagem.

Cada tipo carrega **apenas a mensagem do seu ponto de detecção**. A moldura de
apresentação vive na tabela de tradução. Sem essa separação, texto de tela vazaria
para dentro do núcleo — o inverso do objetivo da onda.

Um quinto tipo, `ArmazenamentoInvalido`, foi **descartado** (achado `A002`): o
adaptador de armazenamento nunca o levantaria, porque `validate.py` devolve motivo
em texto e é o caso de uso que o transforma em exceção. Seria superfície sem
gatilho.

### 2.4 As portas (`src/ports/`)

Duas portas com consumidor — armazenamento de arquivo (`guardar`/`resolver`) e
carregador de árvores (`carregar`) — e uma **declarada sem consumidor e sem
implementação**, o `RepositorioDeArvores`, que existe para a Onda 3 e para que o
dono já esteja na assinatura (`RF-08`).

O `CarregadorDeArvores` é a **terceira** porta, e não estava no `requirements.md`:
a `D-02` a acrescentou para que nenhum caso de uso importe `parsers/` e para que a
resolução de referência e o parse aconteçam em **um** lugar. É o único desvio de
superfície desta onda, e está declarado no `roadmap.md`.

Nenhum adaptador levanta exceção de domínio: eles devolvem **motivo em texto**, e
o caso de uso é quem tipa.

### 2.5 A casca removida e o quarto consumidor

`load_gedcom_and_build_graph` devolvia a lista de nomes ordenada, no contrato
antigo. A varredura de consumidores de produção deu zero.

A `D-06` afirmava que os consumidores eram três (dois de teste e um comentário) e
que o `harness.py` "já consome `carregar_arvore`" — **a afirmação estava errada, e
foi medida**: o coletor do **candidato** chamava a casca de fato, na linha
imediatamente anterior a `GP.carregar_arvore(GED)`, parseando a mesma fixture duas
vezes. Remover a casca sem tocar no coletor quebraria a paridade.

Feito: o coletor do candidato deriva `names` da árvore, com a **mesma** fórmula da
casca. O coletor do **oráculo** não foi tocado — o oráculo é congelado. Paridade
remedida depois da mudança: `100%`, exit 0.

## 3. Preservadas

Regras 🟢 de `_reversa_sdd/domain.md` que continuam **intactas**, verificadas:

- **§5.1 — as dez mensagens da camada de rota.** Todas as dez medidas na sonda de
  19 casos: `"Nenhum arquivo GEDCOM enviado."`, `"Nenhum arquivo selecionado."`,
  `"Arquivo '{nome}' carregado!"`, `"Arquivo não reconhecido como GEDCOM: {motivo}."`,
  `"Erro ao processar GEDCOM: {e}"`, `"Erro: Arquivo GEDCOM não encontrado."`,
  `"Erro: Arquivo '{ref}' não existe mais."`, `"Por favor, carregue o arquivo CSV de matches."`,
  `"Ocorreu um erro: {e}"`, `"Arquivo maior que o limite de {n} MB."`
- **§5.2 — as mensagens do núcleo.** `"Seu nome '{root_name}' não foi encontrado no GEDCOM."`,
  as duas variantes de `"Colunas de Nome e cM não encontradas no CSV."`,
  `"Conexão direta encontrada (ancestral comum)."`,
  `"Conexão indireta encontrada (via casamento/afinidade)."`,
  `"Nenhuma conexão encontrada entre '{p1}' e '{p2}'."`,
  `"Pessoa 1 '{nome}' não encontrada."` / `"Pessoa 2 ..."`.
  Todas as nove mensagens congeladas de `12-paridade-telas.feature` estão cobertas
  pela sonda.
- **`AVISO_AFINIDADE`**, com o `NÃO` em maiúsculas. Medido no servidor de produção:
  presente no passo 6.4b da verificação manual.
- **A distinção "não achei" × "entrada inválida"**: `"Nenhuma conexão encontrada"`
  continua saindo com **sucesso** e a pessoa não encontrada com **erro**. É o
  achado `A003`, e a sonda mede a classe do alerta nos dois casos.
- **O fallback de encoding Latin-1** do CSV (`RN-03`, `RF-11`): nenhuma exceção de
  domínio intercepta a troca de codec.
- **O fallback de nome vazio** (`AMB-024`): formato vazio devolve string vazia;
  apenas a ausência de nome produz `"Sem Nome"`.
- **A validação de conteúdo antes da gravação** (`RF-10`): um GEDCOM inválido não
  deixa resíduo na pasta.
- **A chave de armazenamento derivada do conteúdo** (`RF-09`): medido na
  verificação manual — `c6926bb74ce64b88__basic.ged`, chave, dois underscores e
  nome original preservado; reenvio do mesmo conteúdo não regrava.
- **A ordem de apresentação dos resultados** (§3.7): documental primeiro, cM
  decrescente dentro do grupo.
- **A ordem de inserção** das estruturas da árvore (tag `@ordem`): o `Tree`
  continua com a mesma forma de quatro elementos, e o núcleo continua devolvendo a
  mesma tupla.
- **As asserções de `tests/test_upload_seguranca.py:412`** (`"Ocorreu um erro"`
  ausente no caminho feliz do DNA) e a do literal `Ocorreu um erro` do último
  recurso.
- **O teto de upload**: o valor é o mesmo (`16 * 1024 * 1024`), só ganhou nome. A
  mensagem de `413` continua "de 16 MB".
- **A guarda de exclusividade** (`SO_EXCLUSIVEADDRUSE` em `__main__`): intocada.
- **`Dependencias` continua em `core/dna_analysis.py`** e continua sendo o
  contrato entre núcleo e fronteira. O que mudou é que existe **um** ponto que a
  monta, em vez de dois.

## 4. Modificadas

| Regra | Natureza da mudança |
|---|---|
| `RN-02` — o mecanismo de sinalização de erro | De string de retorno e `except Exception` genérico para exceção de domínio tipada. **O texto observável não mudou** — foi medido, caso a caso |
| A orquestração dos três fluxos | Saiu de `index()` e foi para `src/application/`. `index()` deixa de conter passo de domínio (verificado por AST) |
| O contrato antigo de `load_gedcom_and_build_graph` | **Removido.** Nenhum consumidor de produção; os três de teste migraram para a árvore, e o coletor do candidato do harness também |
| O par `success=` / `path_result is None` como critério de renderização | Substituído por um campo de **desfecho** com três valores. O adaptador deriva o modo dele; o texto da mensagem perde a autoridade semântica que tinha (`RF-20`) |
| O ponto de montagem de `Dependencias` | Era dois (`app.py` no módulo e `app.py:217` por requisição). Passou a ser **um**, no módulo, injetado no caso de uso (`D-05`, `RF-14`) |
| O caminho de resolução da referência da árvore | Era `_resolver_caminho_armazenado` + `carregar_arvore` direto na rota. Passou a ser o port `CarregadorDeArvores`, que resolve e parseia |
| Os dois padrões de verificação do `onboarding.md` §6 | Corrigidos para o que o template de fato renderiza. Nenhuma mudança de código por trás |

## 5. Observações (regras que **não** eram 🟢)

Sem peso de regressão. Ficam aqui para não se perderem:

1. **`src/core/erros.py` fica em `core/`, e a `D-01` é 🟡.** Resolve a direção de
   import (`parsers/` e `core/` importam de lá, e `core/` não pode importar
   `application/`), mas coloca dentro do núcleo um vocabulário com sabor de
   fronteira. Se a Onda 3 criar uma camada de domínio própria, esta é a primeira
   decisão a reabrir.
2. **`CarregadorDeArvores` é a terceira porta e a `D-02` é 🟡, com condição
   declarada:** a porta tem **um** método, e se precisar de um segundo, a decisão
   está errada. O `/reversa-audit` deve verificar esse ponto.
3. **`RepositorioDeArvores` não tem implementação nem consumidor** (`D-03`). É
   dívida técnica de baixa gravidade aceita de propósito; um adaptador em memória
   reintroduziria, com outro nome, o estado global que a feature 005 removeu.
4. **A dívida #3 (contaminação entre requisições concorrentes) NÃO foi fechada**, e
   a `RN-06` proíbe que qualquer entrega desta feature seja citada como tendo
   fechado. `DONO_DO_PROCESSO` é marcador de costura, não identidade.
5. **A dívida #4 (sem identidade nem isolamento) NÃO foi fechada.** O `dono` entra
   como parâmetro obrigatório e não tem comportamento.
6. **As dívidas #5 (ciclos entre pacotes), #8 (nada é persistido) e #10 (o CSV de
   DNA não tem validação de conteúdo) foram preservadas.** A #10 foi preservada
   **de propósito**, por ser assimetria com o GEDCOM que corrigi-la mudaria
   comportamento observável.
7. **`AMB-008` (sinalização da ambiguidade de homônimos) e `AMB-015` na parte da
   sinalização seguem abertos.** A `RF-19` foi estreitada ao comportamento real:
   aceitar, não criar a aresta, não levantar exceção, e proibir rejeitar.
8. **Os 15 erros de ambiente da suíte não são regressão, e a causa foi
   identificada:** `os.mkdir(..., 0o700)` cria diretório inutilizável nesta
   máquina, e o `tmp_path_factory` do pytest usa exatamente esse modo. Ver
   `evidence/README-evidencias.md` §2, que também inventaria 13 diretórios presos,
   oito deles anteriores a esta feature.
9. **O template renderiza `Resultado da Análise` e o Gherkin congelado diz
   `Resultados da Análise de DNA`.** Divergência anterior a esta feature; o
   template não foi tocado, porque mudar literal visível é o que a `RN-04` proíbe.
   Está em `regression-watch.md` como item de `redação`.

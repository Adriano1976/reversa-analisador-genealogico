# Roadmap: dono no port de armazenamento e linha de base da suíte

> Identificador: `007-dono-no-port-e-baseline`
> Data: `2026-10-07`
> Requirements: `_reversa_forward/007-dono-no-port-e-baseline/requirements.md`
> Confidência: 🟢 CONFIRMADO, 🟡 INFERIDO, 🔴 LACUNA

## 1. Resumo da abordagem

Dois deltas independentes, em dois blocos, com medição entre eles.

O primeiro é o **instrumento**. O defeito não é o modo com que o pytest cria o
diretório por teste: é `getbasetemp()`, que cria `pytest-of-<usuário>` com `0o700` e em
seguida tenta **listá-lo**. Nesta máquina um diretório `0o700` não é listável, e o
`os.scandir` levanta `PermissionError` — a linha exata do traceback. Declarando o
fixture `tmp_path` em `tests/conftest.py`, `getbasetemp()` nunca é chamado e os 15
testes de rota executam. Medido com uma sonda descartável, **sem tocar em nenhum
arquivo do projeto: 246 aprovados, 0 erros** — os 15 executam e **todos passam**.

O segundo é a **costura**: `dono` entra como último parâmetro obrigatório de `guardar`
e `resolver` no port de armazenamento, e por chamada em `CarregadorDeArvores.carregar`.
O adaptador aceita o dono e **não o usa**: a chave continua vindo do conteúdo, o
caminho continua o mesmo e nada passa a ser isolado por dono.

A ordem é essa porque medir a costura exige instrumento confiável — e o instrumento é
o que o bloco 0 devolve.

## 2. Princípios aplicados

| Princípio | Como a feature se relaciona | Status |
|-----------|------------------------------|--------|
| I. Dados reais de DNA/GEDCOM nunca entram no versionamento | Respeita. Nenhuma fixture nova usa dado real — os GEDCOM dos testes são os literais sintéticos já existentes. A ação de encerramento confere `git status` contra `src/uploads/`, `uploads/` e contra o resíduo temporário de `tests/.tmp/` | respeita |
| II. Comportamento observável é preservado em refatoração | **É o princípio que governa esta feature.** A costura do dono é refactor puro: mesma chave, mesmo caminho, mesmos literais de tela, mesmos status. A ativação dos 15 testes muda o **relatório** da suíte (`15 errors` → `0`), e isso é mudança de **instrumento**, não de produto — a distinção só é honesta porque foi **medida**: os 15 passam sem que uma linha de produto mude, e nenhuma asserção é reescrita. Se algum falhasse por motivo de produto, a `RF-09` obrigaria a virar requisito próprio em vez de conserto aqui | respeita |
| III. Nenhuma mudança sem teste que a cubra | Respeita, nas duas metades. O contrato novo do port é provado pelo caminho negativo e pelo positivo (`RF-05`); e a própria correção do ambiente ganha teste que a prende, para que ela não possa sair de vigor sem a suíte acusar | respeita |
| IV. Arestas do grafo são tipadas | **Não é tocada por esta feature, e o conflito permanece.** Nenhuma travessia, nenhum peso e nenhuma constante de parentesco é tocada. O conflito é herdado e está declarado desde a feature 005 | conflita (herdado, declarado) |
| V. Toda suposição de genealogia genética cita a fonte | Respeita. Nenhum número de domínio é criado, alterado ou reinterpretado. As únicas constantes tocadas são `DONO_DO_PROCESSO` (marcador de costura, sem valor de domínio) e o teto de upload, que não é tocado | respeita |

> **Sobre o Princípio IV.** Ele não é violado *por esta feature*: a violação é anterior e
> está documentada em `_reversa_forward/005-nucleo-puro-src/requirements.md` §4. O
> registro existe para que ninguém leia esta entrega como "a costura do dono aproximou a
> tipagem de aresta". Não aproximou — são coisas sem relação.

## 3. Decisões técnicas

| ID | Decisão | Justificativa | Alternativas descartadas | Confidência |
|----|---------|----------------|--------------------------|-------------|
| D-01 | A causa raiz é **`TempPathFactory.getbasetemp()`**, e não o `mode=0o700` do diretório por teste. `getbasetemp()` cria `rootdir = <temp>/pytest-of-<usuário>` com `0o700` (`_pytest/tmpdir.py:168`) e em seguida chama `make_numbered_dir_with_cleanup`, que faz `find_prefixed(rootdir, "pytest-")` → `os.scandir(rootdir)` (`_pytest/pathlib.py:175`) → `PermissionError [WinError 5]`. É essa a linha do traceback, e é por isso que a correção tem de **impedir que `getbasetemp()` seja chamado**, e não "consertar o modo" | Muda o desenho da correção inteira: se o defeito fosse o `mktemp`, bastaria trocar o modo de criação; sendo o `getbasetemp`, qualquer correção que ainda o chame continua quebrando depois que o diretório-base existe. Medido: `os.mkdir(p, 0o700)` → não listável, não gravável, não removível; `os.makedirs(p)` → listável, gravável, removível | (a) tratar como defeito do `mktemp` e só trocar o modo lá — deixa o `getbasetemp` no caminho e não corrige; (b) tratar como defeito de `TEMP`/`TMP` — a anotação da feature 005, já declarada incompleta no adendo da 006 | 🟢 medido |
| D-02 | `tests/conftest.py` declara o fixture **`tmp_path`**, criando o diretório com `os.makedirs` no modo padrão, sob a **mesma raiz** de `pasta_temporaria` (`tests/.tmp/`), e `pasta_temporaria` passa a ser a implementação única — `tmp_path` delega a ela e converte para `pathlib.Path` | Resolve a causa pela raiz: com o fixture declarado no repositório, o `tmp_path` do pytest não é resolvido e `getbasetemp()` nunca é chamado. A precedência é a favor: um fixture de `conftest.py` vence qualquer plugin, e a medição usou um plugin (`-p`) — precedência **menor** — que já venceu `_pytest.tmpdir`. E a delegação deixa **uma** política de diretório temporário no repositório, onde hoje há duas | (a) proxy de `tmp_path_factory` reimplementando `mktemp` — duplica interno do pytest, fica frágil a upgrade, e não cobre `getbasetemp` sem mais reimplementação; (b) `monkeypatch` do modo em `_pytest.pathlib` — acopla o projeto a nome interno de biblioteca; (c) `--basetemp` — **medido: não ajuda**, o pytest apaga e recria o diretório dado com `0o700`; (d) `pytest.ini` — não resolve e **não está em `allowedPaths`**; (e) editar o fixture `app_cliente` em `tests/test_upload_seguranca.py` — deixa o defeito de pé para todo teste futuro, que é o que a resposta da sessão de esclarecimento recusa; (f) criar `tests/.tmp/.gitignore` — o arquivo é versionado e impede a própria raiz de ser removida quando vazia, criando o resíduo que ele existiria para evitar | 🟢 |
| D-03 | A remoção do diretório no `finally` **sai do diretório antes de remover** (`os.chdir` para a raiz do projeto), e isso é requisito, não capricho | **Medido: 15 diretórios vazios sobrevivem por execução** sem essa saída. `app_cliente` faz `monkeypatch.chdir(tmp_path)`; o pytest desmonta o `tmp_path` **antes** de o `monkeypatch` desfazer o chdir, então o `rmtree` do teardown roda com o CWD **dentro** do diretório, o Windows recusa, e o `ignore_errors=True` engole a recusa. Medido depois da correção: **zero resíduo**. Os 15 sobreviventes não são "presos" — foram removidos com `Remove-Item -Recurse -Force` sem privilégio nenhum —, o que separa este defeito do defeito dos diretórios `0o700` | (a) varrer a raiz em `pytest_sessionfinish` como única garantia — funciona, mas deixa o diretório vivo durante toda a sessão e esconde a causa; (b) deixar o resíduo e ignorá-lo — o projeto já carrega 13 diretórios presos, e acrescentar 15 por execução dentro do repositório é agravar um problema conhecido | 🟢 medido |
| D-04 | A correção do ambiente ganha **teste próprio**, que prende que o `tmp_path` da suíte é o do projeto e que ele é listável, gravável e removível | Sem ele, a correção é invisível: um upgrade de pytest, ou alguém removendo o fixture por parecer redundante, devolve o defeito em silêncio — e o sintoma é *erro de ambiente*, que o próximo leitor atribui à máquina de novo, que é exatamente o que aconteceu entre as features 005 e 006. O teste mede a propriedade (onde o diretório está e o que dá para fazer com ele), não a implementação | (a) confiar no docstring — foi o que já falhou uma vez; (b) varrer o código-fonte dos testes procurando `tmp_path_factory`/`tmpdir` — o próprio arquivo da varredura citaria os nomes e o teste passaria a se medir | 🟢 |
| D-05 | `dono` entra como **último parâmetro posicional** de `ArmazenamentoDeArquivos.guardar(conteudo, nome_original, tipo, dono)` e de `.resolver(referencia, dono)`, **sem valor padrão** | É a forma simétrica à de `RepositorioDeArvores`, onde o dono também é o último (`guardar(arvore, dono)`, `obter(referencia, dono)`) — e simetria entre as duas portas é RNF declarado. Sem padrão, a chamada antiga deixa de compilar, que é o que a `RF-12` exige: nenhuma superfície de compatibilidade | (a) `dono` primeiro, como em `upload_gedcom` — quebra a simetria entre as duas portas; (b) keyword-only (`*, dono: str`) — é a forma mais difícil de errar, mas deixa as duas portas com **formas** diferentes de exigir o mesmo parâmetro; (c) `dono: str = "unico"` — proibido pela `RF-12`, e é a forma mais barata de adiar a costura e a mais cara de desfazer | 🟢 |
| D-06 | O carregador de árvores recebe o dono **por chamada**: `CarregadorDeArvores.carregar(referencia, dono)`, que o repassa a `resolver` | É o único ponto de produção que chama `resolver`, e o dono tem de chegar lá sem ser inventado no local (`RF-03`). Por chamada, o fluxo do dono é o mesmo do `guardar`: sai da borda e chega à porta. Isso importa porque **os adaptadores são singletons de processo**, montados uma vez no import (`_ARMAZENAMENTO`, `_CARREGADOR` em `src/app.py`): congelar identidade na construção é exatamente o que a Onda 3 teria de desfazer, e é o custo que esta feature existe para não pagar | (a) o dono no `__init__` de `CarregadorDeArvoresGedcom` — prende a identidade num objeto que vive o processo inteiro; (b) deixar `resolver` sem dono e só corrigir `guardar` — contra a `RF-01`, que exige os **dois** métodos, e recria a assimetria que a feature fecha; (c) atributo mutável de dono no adaptador — estado global de identidade, disfarçado | 🟢 |
| D-07 | O adaptador `ArmazenamentoEmDisco` aceita `dono` nas duas assinaturas e **não o usa em nenhuma decisão**, com comentário no corpo dizendo por quê | É a `RF-02`/`RN-02` escrita em código: chave, nome armazenado, caminho, reuso por conteúdo e ordem de validação ficam idênticos, e o `RF-09` da feature 006 continua verdadeiro. O parâmetro mantém o nome `dono` para que a chamada por palavra-chave também funcione | (a) renomear para `_dono` ou absorver em `**extras` — quebra a chamada por palavra-chave e a simetria com o `Protocol`; (b) usar o dono no caminho — mudança de comportamento observável e quebra de paridade do armazenamento | 🟢 |
| D-08 | `DONO_DO_PROCESSO` **permanece em `src/app.py`** (a borda, ponto único de montagem) e o comentário dela ganha a menção explícita à **dívida #3** | A `RF-04` exige uma constante única **e** que o lugar declare que não há isolamento e que a dívida #3 não é tratada. A constante já é única e o comentário já declara a ausência de isolamento; o que falta é nomear a dívida #3 e tirar o "nesta onda", que prende a constante à feature 006 — a costura é para a Onda 3 do cutover, não para uma onda desta feature | (a) mover a constante para um módulo novo de configuração — cria um lugar para uma constante que já tem um, e o ponto único de montagem é a borda; (b) deixar o comentário como está — a `RF-04` ficaria parcialmente não atendida, e o texto continuaria dizendo que a costura pertence a uma onda que já foi entregue | 🟢 |
| D-09 | Os testes do contrato novo vivem em **`tests/test_porta_de_armazenamento.py`**, em classe nova, ao lado do teste estrutural do repositório (`T028` da 006) | É o arquivo cujo cabeçalho já se declara "testes da porta de armazenamento", e o `T028` é o precedente literal da prova por forma de contrato — `bind` sem o dono levanta `TypeError`. Repetir o padrão no mesmo arquivo deixa as duas portas simétricas também na verificação | (a) arquivo novo por feature — separa duas provas do mesmo contrato em dois lugares; (b) teste de integração pela rota — mediria a rota, e a `RF-05` pede o contrato, que se prova sem HTTP | 🟢 |
| D-10 | O cabeçalho de `tests/test_porta_de_armazenamento.py` — a seção "Por que este arquivo não usa `tmp_path`" — é **corrigido**, porque a correção do ambiente o torna falso | Ele afirma que `tmp_path` não funciona nesta máquina e que por isso o arquivo usa `pasta_temporaria`. Depois do bloco 0 isso deixa de ser verdade, e um comentário que mente sobre o motivo de uma escolha é pior que comentário nenhum: o próximo leitor repetiria a regra errada. É **comentário, não asserção** — a `RF-06` continua intacta, e o diff das asserções do arquivo permanece vazio | (a) deixar como está — a extração passaria a mentir sobre o estado do projeto, que é o defeito que o adendo da 006 registrou em quatro artefatos; (b) reescrever as escolhas do arquivo para `tmp_path` — churn em teste entregue sem ganho, e `pasta_temporaria` continua válida | 🟢 |
| D-11 | A execução é em **dois blocos com parada e medição**: Bloco 0 — instrumento (conftest, teste da correção, nova linha de base); Bloco 1 — costura (as duas assinaturas, o carregador, os três chamadores, os testes do contrato) | O bloco 0 é o que transforma a suíte em instrumento: sem ele, a única medição disponível para a costura é uma suíte cega em 15 testes da superfície que a Onda 2 reescreveu. E como o bloco 1 é edição de assinatura em quatro arquivos, medir antes e depois dele permite atribuir uma regressão a um conjunto pequeno e nomeado | (a) um bloco só — a suíte voltaria a executar e a assinatura mudaria no mesmo passo, sem ponto de atribuição; (b) começar pela costura — mede com o instrumento quebrado, que é o erro que a feature existe para corrigir | 🟢 |
| D-12 | A **linha de base vigente** passa a ser a medição pós-correção, no interpretador oficial; as anteriores ficam **históricas** e a regra de comparação muda de "total" para "nenhum aprovado vira falha" | A `RN-04` exige a troca de métrica e proíbe reescrever os artefatos das 005/006. O número **não** pode ser prometido aqui: medido com a sonda (`246 aprovados, 0 erros`), ele é o valor **esperado** do bloco 0 e vai **crescer** com os testes do `RF-05`. Comparar totais contra `231/15` ou contra `178/15` é comparar coisas diferentes; o que se compara é o conjunto de aprovados | (a) fixar `246` como critério de pronto — passaria a acusar regressão falsa assim que os testes novos entrarem; (b) manter `231 aprovados, 15 erros` como vigente e só anotar — é a situação que produziu a leitura errada entre as features 005 e 006 | 🟢 |

## 4. Premissas

Nenhuma. O `requirements.md` desta feature foi fechado com **zero** marcadores
`[DÚVIDA]`: as três dúvidas da versão inicial foram resolvidas na sessão de
esclarecimento de 2026-10-07 e estão registradas na §9 daquele documento. Nada aqui
depende de premissa não decidida.

## 5. Delta arquitetural

| Componente | Arquivo de origem no legado | Tipo de mudança | Resumo |
|------------|------------------------------|-----------------|--------|
| `ArmazenamentoDeArquivos` (`Protocol`) | `_reversa_sdd/addenda/006-fronteira-aplicacao-ports.md` | contrato-alterado | `guardar` e `resolver` ganham `dono` como último parâmetro obrigatório (`D-05`). Nenhum método novo, nenhuma remoção |
| `CarregadorDeArvores` (`Protocol`) | `_reversa_sdd/addenda/006-fronteira-aplicacao-ports.md` | contrato-alterado | `carregar` ganha `dono` (`D-06`). **Continua com UM método**, que era a condição declarada da `D-02` da feature 006 — a condição era sobre a contagem de métodos, e ela segue satisfeita |
| `src/ports/adaptadores.py` — `ArmazenamentoEmDisco` | `_reversa_sdd/architecture.md#3` | regra-alterada | Assinaturas novas; o dono é aceito e ignorado. Chave, nome armazenado, caminho, reuso por conteúdo e ordem de validação **idênticos** |
| `src/ports/adaptadores.py` — `CarregadorDeArvoresGedcom` | `_reversa_sdd/architecture.md#3` | regra-alterada | Repassa o dono recebido à chamada de `resolver`. Continua sendo o **único** lugar da fronteira que parseia |
| `src/application/upload_gedcom.py` | `_reversa_sdd/addenda/006-fronteira-aplicacao-ports.md` | regra-alterada | Passa a **repassar** o `dono` que já recebe por parâmetro. Uma linha; nenhum outro passo do caso de uso muda |
| `index()` / `_arvore_do_formulario()` em `src/app.py` | `_reversa_sdd/architecture.md#1` | regra-alterada | A chamada de `guardar` do CSV e a de `carregar` passam a citar `DONO_DO_PROCESSO`. `index()` **não** ganha passo de domínio — a `RF-01` da 006 continua verdadeira |
| `DONO_DO_PROCESSO` em `src/app.py` | `_reversa_sdd/architecture.md#7` (dívida #4) | regra-alterada | Permanece única e no mesmo lugar; o comentário passa a nomear a dívida #3 e deixa de dizer "nesta onda" (`D-08`) |
| `tests/conftest.py` | *(infraestrutura de teste, fora da extração)* | regra-alterada | Passa a ser a autoridade do diretório temporário da suíte: declara `tmp_path`, e `pasta_temporaria` vira a implementação única. O `collect_ignore` da cicatriz **permanece** |
| `tests/test_porta_de_armazenamento.py` | *(infraestrutura de teste, fora da extração)* | regra-alterada | Classe nova com a prova do contrato de armazenamento (`RF-05`); cabeçalho corrigido quanto ao `tmp_path` (`D-10`). Asserções existentes **intocadas** |
| `tests/test_upload_seguranca.py` | *(infraestrutura de teste, fora da extração)* | **presença** | **NÃO É TOCADO.** É o `RF-06`: nenhum teste removido, desabilitado, renomeado ou com asserção reescrita. Os 15 passam a executar por efeito do `conftest.py` |
| `src/core/` (todo o pacote) | `_reversa_sdd/architecture.md#3` | presença | **Nenhuma alteração.** Nem `erros.py`, nem `path_search.py`, nem `dna_analysis.py`. É a `RF-11`: a assinatura de retorno do núcleo continua congelada |
| `src/parsers/`, `src/reporting/`, `src/utils/` | `_reversa_sdd/architecture.md#3` | presença | **Nenhuma alteração.** `utils/validate.py` continua sendo a autoridade única da regra de upload; o adaptador segue só chamando |
| `RepositorioDeArvores` | `_reversa_sdd/addenda/006-fronteira-aplicacao-ports.md` (`D-03`, `RF-08`) | presença | **INALTERADO.** Continua declarado, sem implementação e **sem consumidor**. Esta feature **não** o preenche: ela prepara a mesma porta de armazenamento, não a persistência |
| Dívidas #3 e #4 (`architecture.md#7`) | `_reversa_sdd/architecture.md#7` | presença | **INALTERADAS.** A guarda continua de processo, não de thread, e não há isolamento entre donos. A `RN-06` proíbe declarar o contrário |
| Dívida #10 (`architecture.md#7`) | `_reversa_sdd/architecture.md#7` | presença | **INALTERADA de propósito.** O CSV de DNA continua sem validação de conteúdo, e a assimetria com o GEDCOM é preservada |
| `pytest.ini` | *(configuração de teste)* | presença | **NÃO É TOCADO** — e não está em `allowedPaths`, então tocá-lo exigiria ato do usuário. A `RF-07` fixa a correção no `conftest.py` justamente por isso |
| `.gitignore` | *(raiz do projeto)* | presença | **NÃO É TOCADO** — também fora de `allowedPaths`. Consequência declarada: a rede de segurança contra resíduo de `tests/.tmp/` é a remoção do `D-03`, e não uma linha de ignore. Ver §9 |
| `src/api/` (citado em `topology_decision.md#Notas`) | `_reversa_sdd/migration/topology_decision.md#Notas` | **não criado** | Continua válida a decisão de 2026-10-07: o Flask permanece como adaptador de entrada. Esta feature não cria rota, schema nem camada HTTP nova |
| `_reversa_sdd/parity/harness.py` | `_reversa_sdd/migration/parity_harness.md` | presença | **Nenhuma alteração.** É o instrumento da `RF-10`, não objeto dela |

## 6. Delta no modelo de dados

- Resumo das mudanças: **nenhuma no modelo.** Nenhum campo de `PESSOA`, `FAMILIA`,
  `GRAFO_BIPARTIDO` ou `CHILD_TO_FAMILY` é acrescentado, removido, renomeado ou
  retipado, e nenhum arquivo migra de formato. A parte desta feature mais próxima de
  "dado" é o **layout de armazenamento em disco**, e a decisão é que ele **não muda**:
  a chave continua derivada do conteúdo, a referência continua `<chave>__<nome visível>`
  e o dono **não** entra na chave nem no caminho (`RN-02`). A dívida #8 ("nada é
  persistido entre requisições") continua aberta.
- Detalhe completo em: `_reversa_forward/007-dono-no-port-e-baseline/data-delta.md`

## 7. Delta de contratos externos

| Contrato | Tipo | Arquivo de detalhe |
|----------|------|--------------------|
| `POST /` (as três `action` do formulário) | HTTP | **não alterado** — mesmas rotas, mesmos campos, mesmos status, mesmos literais. O diretório `interfaces/` **não** é criado, pela mesma razão da Onda 2: o contrato JSON com `404`/`422` só existe junto com a API nova, que não é desta feature. O `dono` é parâmetro **interno** entre borda, caso de uso e porta — não é campo de formulário, não é cabeçalho e não é credencial (`RN-06`) |
| Layout de arquivos em `uploads/` | arquivo | **não alterado** — `<chave sha256 truncada>__<nome visível>`, um arquivo por conteúdo, reuso quando a chave já existe. A ausência do dono no nome é decisão (`RN-02`), não esquecimento; o detalhe está em `data-delta.md` |

## 8. Plano de migração

> Não há dados a migrar: o sistema não tem SGBD e nada é persistido entre requisições.
> A "migração" aqui é de **código e de instrumento**, em dois blocos com parada própria
> (`D-11`).

1. **Bloco 0 — o instrumento.** Declarar `tmp_path` em `tests/conftest.py` com a raiz de
   `pasta_temporaria` e a saída de CWD antes de remover (`D-02`, `D-03`); tornar
   `pasta_temporaria` a implementação única; acrescentar o teste que prende a correção
   (`D-04`). **Medir:** suíte completa com `.venv/Scripts/python.exe` — esperado
   `246 aprovados, 0 erros` e **zero** resíduo em `tests/.tmp/` — e paridade diferencial.
   Registrar a linha de base vigente com o comando ao lado (`D-12`).
2. **Bloco 1 — a costura.** Acrescentar `dono` às duas assinaturas do port de
   armazenamento e à do carregador (`D-05`, `D-06`); aceitar e ignorar no adaptador
   (`D-07`); repassar em `upload_gedcom` e citar `DONO_DO_PROCESSO` nos dois pontos de
   `app.py` (`D-08`); atualizar o comentário da constante; acrescentar a classe de teste
   do contrato e corrigir o cabeçalho obsoleto (`D-09`, `D-10`). **Medir:** suíte e
   paridade de novo, e conferir que **nenhum aprovado do bloco 0 virou falha** (`D-12`).
3. **Bloco 2 — fechamento.** Conferir por diff que
   `tests/test_upload_seguranca.py` **não tem alteração nenhuma**; conferir que nenhuma
   constante numérica de domínio mudou; rodar a verificação manual do `onboarding.md`;
   conferir `git status` contra `src/uploads/`, `uploads/` e `tests/.tmp/`.

## 9. Riscos e mitigações

| Risco | Impacto | Probabilidade | Mitigação |
|-------|---------|---------------|-----------|
| Algum dos 15 testes falhar ao executar pela primeira vez, expondo defeito de produto escondido atrás do erro de ambiente | alto | **aposentado por medição** | **Medido antes do plano:** os 15 passam — `246 aprovados, 0 erros`. O conjunto de triagem da `RF-09` é **vazio**, e isso está registrado como fato, não como expectativa. Se a medição do bloco 0 divergir, a `RF-09` volta a valer: veredito explícito por falha, defeito de produto vira requisito próprio |
| O `tmp_path` do projeto deixar de ser o do pytest ser lido como "teste rodando fora do temporário" e alguém "restaurar" o fixture | alto | baixa | O `D-04` prende a propriedade por teste, o docstring do `conftest.py` registra a causa medida, e a `D-01` nomeia a linha do traceback. Restaurar o fixture volta a produzir 15 erros de ambiente, e não 15 falhas — o modo de falha é reconhecível |
| Um teste futuro pedir `tmp_path_factory` ou o `tmpdir` legado e cair no `getbasetemp()` de novo | médio | média | Nenhum teste do repositório pede os dois hoje (varredura: só `tmp_path`, em `test_upload_seguranca.py`). O docstring do `conftest.py` passa a dizer **por que** os dois não são usáveis aqui, ao lado da causa; é o mesmo padrão do aviso que a 006 deixou e que funcionou |
| Reintroduzir resíduo temporário dentro do repositório, agora que o temporário passa a viver em `tests/.tmp/` | médio | média | O `D-03` foi **medido com resíduo zero**; `.tmp` é prefixo de ponto, então `norecursedirs` mantém o diretório fora da coleta (o mesmo mecanismo que `pasta_temporaria` já usa); e o critério de pronto confere `git status`. ⚠️ **`.gitignore` está fora de `allowedPaths`**, então não ganha linha de ignore nesta feature — se o usuário quiser a rede dupla, é ato dele, e o roadmap registra isso em vez de silenciar |
| Alguém remover o `collect_ignore` de `tests/conftest.py` "já que o problema do `0o700` foi resolvido" | alto | média | A correção **não** remove diretório preso nenhum: `tests/_basetemp_probe/` continua lá e continua inlistável (a `RF` de Operação manda documentar, não remover). O docstring do `conftest.py` diz, na mesma seção, que a linha perde a razão **só** quando o diretório for removido com shell elevado — a instrução já está escrita e é preservada |
| A mudança de assinatura do carregador ser lida como violação da `D-02` da feature 006 ("um método, e essa é a condição") | médio | baixa | A condição era sobre a **contagem de métodos**, e ela continua em um. O delta arquitetural (§5) registra a leitura explicitamente, para que a decisão não seja reaberta por engano nem dada como violada |
| A nova linha de base ser lida como "a feature acrescentou 15 testes de produto" | médio | alta | A `D-12` fixa a aritmética: `231 aprovados + 15 que executam = 246`, **zero** teste novo nessa conta. O número autoritativo é a medição pós-correção, que cresce com os testes do `RF-05` |
| Comparar a suíte nova contra `231/15` ou `178/15` e concluir regressão | médio | média | A `RN-04` proíbe, e a `D-12` troca a regra de comparação de total para conjunto: nenhum aprovado pode virar falha. Os números antigos ficam marcados como históricos nos artefatos **desta** feature |
| Alguma constante numérica de domínio mudar de valor durante a costura | alto | baixa | A costura não toca `src/core/`, `src/parsers/`, `src/reporting/` nem `src/utils/` — a lista de arquivos do bloco 1 é fechada e enumerada. A paridade diferencial nas 6 fixtures é a rede, e ela é medida nos dois blocos |
| O resíduo da verificação manual ficar em `src/uploads/` e violar o Princípio I | baixo | alta | A verificação manual do `onboarding.md` aponta a pasta de upload para um diretório descartável, como a 006 fez; a ação de encerramento confere `git status`. O `_clean_residue.py` **não** limpa essa pasta |

## 10. Critério de pronto

- [ ] Todas as ações do `actions.md` marcadas `[X]`
- [ ] `cross-check.md` (se executado) sem CRITICAL nem HIGH
- [ ] `regression-watch.md` gerado, incluindo o aviso de que `RepositorioDeArvores` segue sem consumidor
- [ ] Suíte completa **sem nenhum erro de ambiente**, medida com `.venv/Scripts/python.exe`, com o comando registrado ao lado do número (`RF-06`, `RF-08`)
- [ ] `diff` de `tests/test_upload_seguranca.py` contra o estado anterior **vazio**: nenhum teste removido, desabilitado, renomeado ou com asserção reescrita (`RF-06`)
- [ ] `guardar` e `resolver` exigem `dono` sem valor padrão, provado pelo caminho negativo, e o adaptador aceita o dono **sem** mudar chave, nome ou caminho (`RF-01`, `RF-02`, `RF-05`)
- [ ] Todas as chamadas de produção a `guardar` e a `resolver` passam o dono, e nenhuma inventa valor no próprio local (`RF-03`)
- [ ] Existe **uma** constante de dono, citada por todos os chamadores, declarando que não é segurança e que a dívida #3 não é tratada (`RF-04`)
- [ ] Nenhuma superfície de compatibilidade criada: o dono não tem default e não há forma alternativa de chamada (`RF-12`)
- [ ] Paridade diferencial em 100 %, exit 0, medida com `.venv/Scripts/python.exe` (`RF-10`)
- [ ] `src/core/`, `src/parsers/`, `src/reporting/` e `src/utils/` sem nenhuma alteração; assinatura de retorno do núcleo intacta (`RF-11`)
- [ ] `pytest.ini` e `.gitignore` intocados
- [ ] `tests/.tmp/` ausente ao fim da execução, e ausente do `git status`
- [ ] Linha de base nova registrada, e o par anterior marcado como histórico sem reescrever os artefatos das features 005 e 006 nem o adendo vigente da 006 (`RF-08`, `RN-04`)
- [ ] Verificação manual do `onboarding.md` executada e registrada em `evidence/`
- [ ] Nenhuma afirmação, em nenhum artefato da feature, de que a dívida #3 ou a #4 foi fechada (`RN-06`)
- [ ] Os 13 diretórios presos continuam apenas **documentados**, com o comando de remoção que exige shell elevado

## 11. Histórico de alterações

| Data | Alteração | Autor |
|------|-----------|-------|
| 2026-10-07 | Versão inicial gerada por `/reversa-plan` | reversa |
| 2026-10-07 | Medição prévia ao plano, com sonda descartável: causa raiz corrigida para `getbasetemp()`/`os.scandir` (`D-01`), resíduo de 15 diretórios por execução medido e fechado (`D-03`), e a triagem da `RF-09` encerrada por medição — os 15 testes **passam** | reversa |
| 2026-10-07 | Correção de vocabulário do §5, exposta pelo `/reversa-to-do`: a linha de `tests/conftest.py` usava `componente-alterado`, valor que **não existe** no enum do template do roadmap. Passa a `regra-alterada`. Nenhuma decisão, delta ou critério muda — é o mesmo conteúdo com o rótulo previsto | reversa |

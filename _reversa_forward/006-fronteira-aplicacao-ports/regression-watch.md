# Regras sob vigilância — feature `006-fronteira-aplicacao-ports`

> Feature: `006-fronteira-aplicacao-ports` (Onda 2 do cutover)
> Data: `2026-10-07`
> Base do watch: seção "Modificadas" do `legacy-impact.md` desta feature
> Executor: `/reversa-coding`

> **IDs.** Esta feature continua a numeração da `005-nucleo-puro-src`, que usou
> `W001` a `W004` e `OBS-01` a `OBS-10`. IDs são estáveis e não se reciclam entre
> features do mesmo projeto: um `W006` é sempre o mesmo item, em qualquer leitura.

## Itens sob vigilância

> O watch principal recebe regras que **eram 🟢** e foram alteradas ou removidas.
> A Onda 2 alterou o **mecanismo de orquestração**, **removeu** uma superfície de
> compatibilidade e **acrescentou** um vocabulário de exceção. As regras 🟡 e 🔴
> estão em Observações, sem peso de regressão.

| ID | Origem (arquivo, seção) | Regra esperada após mudança | Tipo de verificação | Sinal de violação |
|---|---|---|---|---|
| **W005** | `_reversa_sdd/domain.md#5.1` e `#5.2` | As dez mensagens da camada de rota e as nove mensagens congeladas de `12-paridade-telas.feature` continuam **ao caractere**, inclusive nos trechos interpolados, e cada uma no mesmo caso em que era produzida | `redação` | Qualquer divergência na sonda de mensagens (`evidence/probe_mensagens.py` + `_comparar.py`), que compara status, classe do alerta e texto em 19 casos. Um literal que "melhora" de redação é violação, não melhoria |
| **W006** | `_reversa_sdd/domain.md#5.2`, exceções do núcleo | As exceções de domínio continuam **capturáveis como `ValueError`**, por herança de `ErroDeDominio` | `presença` | As quatro asserções de `tests/test_confrontacao_gedcom_dna.py:920`, `:936` e `tests/test_dna_analysis.py:219`, `:241` deixam de passar sem reescrita. `tests/test_erros_de_dominio.py` falha primeiro |
| **W007** | `_reversa_sdd/domain.md#3`, "sem caminho nos dois estágios" | "Nenhuma conexão encontrada" continua sendo **sucesso**, e pessoa não encontrada continua sendo **erro de entrada**. Os dois casos têm o mesmo status HTTP e se distinguem pelo **modo de renderização** | `presença` | A classe do alerta troca para o mesmo caso nos dois sentidos. Medido no servidor de produção: passo 6.5 do `onboarding.md`; medido em teste: `tests/test_desfecho_do_resultado.py` |
| **W008** | `_reversa_sdd/domain.md#5.2`, `AVISO_AFINIDADE` | O aviso de afinidade continua presente no caminho indireto, com o `NÃO` em **maiúsculas** | `presença` | O aviso some, ou a caixa muda. É contrato do Princípio IV: afinidade nunca pode ser apresentada como consanguinidade |
| **W009** | `src/parsers/gedcom_parser.py`, contrato antigo | A casca `load_gedcom_and_build_graph` **não existe mais**, e nenhum módulo de produção a chama | `ausência` | A função reaparece, ou aparece `import load_gedcom_and_build_graph` em `src/` ou em `_reversa_sdd/parity/harness.py`. Era superfície sem consumidor de produção; o `D-06` a removeu |
| **W010** | `src/app.py`, `index()` | `index()` **não** contém passo de domínio: nenhuma chamada a parser, agregador de CSV, resolvedor de diagrama ou aos fluxos do núcleo | `ausência` | `python _reversa_forward/006-fronteira-aplicacao-ports/evidence/_t020_varredura.py` sai diferente de APROVADO. Atenção: as cinco funções de dependência **continuam importadas** para montar o pacote `Dependencias` — o que a regra proíbe é a **chamada** |
| **W011** | `_reversa_sdd/domain.md#5.1`, teto de upload (`RN-01`) | O teto continua `16 * 1024 * 1024`, e a mensagem de `413` continua `"Arquivo maior que o limite de 16 MB."` | `presença` | O valor muda (a `RN-01` proíbe) ou a mensagem muda de número. O nome `TETO_DE_UPLOAD_EM_BYTES` é só um nome; o número é contrato |
| **W012** | `_reversa_sdd/domain.md`, `RF-09`/`RF-10` | A chave de armazenamento continua derivada do **conteúdo**; o mesmo conteúdo não é regravado; o caminho devolvido é **completo**; e a validação de conteúdo acontece **antes** de gravar | `presença` | Chave aleatória, reenvio regravando, nome sendo remontado por quem chama, ou resíduo na pasta depois de uma recusa. `tests/test_porta_de_armazenamento.py` e o passo 6.2 do `onboarding.md` |
| **W013** | `RN-03` / `RF-11`, fallback de encoding | O fallback Latin-1 do CSV continua alcançável e **nenhuma exceção de domínio o intercepta** | `presença` | `read_csv_with_fallback` deixa de tentar latin-1, ou o `except` de `CsvIlegivel` passa a capturar também a queda de codec. Fixture `mojibake_latin1.ged`/CSV latin-1 na paridade |
| **W014** | `AMB-024`, fallback de nome | Formato de nome vazio devolve **string vazia**; apenas a **ausência** de nome produz `"Sem Nome"` | `presença` | `"Sem Nome"` aparece para formato vazio. `get_name` é cópia literal do oráculo; "melhorá-la" quebra paridade (DIV-001) |
| **W015** | `RF-14` / `D-05`, ponto de montagem | Existe **exatamente um** ponto que monta `Dependencias`, e nenhum caso de uso monta a sua própria cópia por requisição | `presença` | Uma segunda montagem aparece (era o defeito em `app.py:217`). Verificado pela varredura de forma |
| **W016** | `D-12`, assinatura do núcleo | `core.path_search.path_search` e `core.dna_analysis.dna_analysis` continuam devolvendo a **tupla de três** com o indicador de sucesso, e o `Tree` continua com quatro elementos | `presença` | `_reversa_sdd/parity/harness.py:211` e `:412` divergem na comparação de `success`, ou uma das nove asserções que desempacotam a tupla quebra. O campo de desfecho vive no resultado do caso de uso, **nunca** no núcleo |
| **W017** | `RF-16`, suíte | Nenhum teste foi removido, desabilitado ou reescrito para caber na mudança | `presença` | A contagem de testes cai abaixo da linha de base, ou aparece `skip`/`xfail` novo sem defeito medido que o justifique. Baseline de 005: 178 testes; a 006 acrescenta arquivos novos |
| **W018** | `RF-15`, paridade | `python _reversa_sdd/parity/harness.py` continua em **100%, exit 0** nas 6 fixtures | `presença` | Qualquer divergência. **Toda** divergência é No-go absoluto, "mesmo com aparência de melhoria sobre o legado" (`cutover_plan.md`) |
| **W019** | `12-paridade-telas.feature:71` | ⚠️ **Divergência conhecida, pré-existente e não resolvida:** o Gherkin diz que o cabeçalho é `Resultados da Análise de DNA`, e `src/templates/index.html` renderiza `Resultado da Análise` | `redação` | O template muda para casar com o Gherkin **sem decisão registrada** — mudar literal visível é o que a `RN-04` proíbe. Quem resolver a divergência decide qual dos dois é a autoridade, e registra a decisão. Medido em `evidence/T025-verificacao-manual.md` §1.1 |

## Observações

> Sem peso de regressão. Regras que **não** eram 🟢 ficam aqui, e não no watch
> principal. Registradas porque uma leitura futura precisa saber que existem.

| ID | Observação | Por que importa |
|---|---|---|
| **OBS-11** | A leitura do `OBS-03` da feature 005 — "mensagens são comparadas por **modo**, nunca por texto" — vale para o **harness**. A Onda 2 acrescentou o instrumento que faltava: a sonda de mensagens compara **texto** na tela, por caso, com `curl`/cliente Flask | Os dois instrumentos são complementares e nenhum substitui o outro. O harness cobre o núcleo contra o oráculo; a sonda cobre a camada de tela, que o harness não vê |
| **OBS-12** | **Correção do `OBS-09` da feature 005.** Ele registrou que "a suíte precisa de `TEMP`/`TMP` gravável". A causa é mais estreita e foi medida: `os.mkdir(caminho, 0o700)` cria um diretório que não pode ser listado nem apagado nesta máquina, e o `tmp_path_factory` do pytest usa **exatamente** esse modo | Um `TEMP` gravável **não** resolve: escrever dentro do diretório criado por `mkdtemp` também é negado. Enquanto isso não for corrigido, todo teste novo deve evitar `tmp_path` e usar as fixtures de `tests/conftest.py` |
| **OBS-13** | Há **13 diretórios presos** no workspace, oito deles anteriores a esta feature (`.pytest-tmp/*`, `_reversa_refactor/.pytest-baseline`). A remoção exige shell elevado | Explica a entrada `.pytest-tmp/` do `.gitignore` e a anotação de "15 erros de ambiente": a armadilha é do projeto, não desta rodada. Comando de remoção em `evidence/README-evidencias.md` §2.2 |
| **OBS-14** | `src/core/erros.py` fica em `core/` por `D-01`, que é **🟡**: resolve a direção de import, mas põe no núcleo um vocabulário com sabor de fronteira | Se a Onda 3 criar camada de domínio própria, esta é a primeira decisão a reabrir |
| **OBS-15** | `CarregadorDeArvores` é a **terceira** porta, acrescentada pela `D-02`, que é **🟡** e tem condição declarada: a porta tem **um** método, e um segundo método significa que a decisão está errada | O `/reversa-audit` deve verificar este ponto na próxima execução. O `CarregadorDeArvores` não estava no `requirements.md` |
| **OBS-16** | `RepositorioDeArvores` está **declarado sem implementação e sem consumidor** (`D-03`), como contrato para a Onda 3 | Um adaptador em memória reintroduziria, com outro nome, o estado global que a feature 005 removeu. `tests/test_porta_de_armazenamento.py` prova a ausência de forma estrutural |
| **OBS-17** | `DONO_DO_PROCESSO = "unico"` em `src/app.py` é **marcador de costura**, não identidade. As dívidas #3 e #4 continuam abertas | A `RN-06` proíbe citar qualquer entrega desta feature como tendo implementado isolamento. O `dono` está na assinatura para a Onda 3 não reabrir as portas |
| **OBS-18** | As dívidas #5 (ciclos entre pacotes), #8 (nada é persistido) e #10 (o CSV de DNA não tem validação de conteúdo) **foram preservadas** — a #10 de propósito | A #10 é assimetria com o GEDCOM que validar antes de gravar; corrigi-la mudaria comportamento observável e quebraria paridade. Pelo Princípio II, é feature própria |
| **OBS-19** | `AMB-008` (sinalização da ambiguidade de homônimos na raiz) e `AMB-015` na **parte da sinalização** continuam abertos | A `RF-19` foi estreitada ao comportamento real (aceitar, não criar a aresta, não levantar exceção, proibir rejeitar). A sinalização exigiria mudança de comportamento e provavelmente nasce junto com o repositório da Onda 3 |
| **OBS-20** | `AnalisadorDeUpload`, nomeado na `D-07`, **não existe como classe**: a `T007` fixou um adaptador só, `ArmazenamentoEmDisco`, e as duas descrições da `D-07` são a mesma responsabilidade | Não há componente faltando. Registrado para que a divergência de nome não seja lida como lacuna |

## Histórico de re-extrações

> Preenchido pelo agente reverso quando `/reversa` rodar de novo. Vazio nesta data.

## Arquivadas

> Vazio nesta data.

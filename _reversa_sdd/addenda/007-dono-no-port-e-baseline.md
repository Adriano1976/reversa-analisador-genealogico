# Adendo: dono no port de armazenamento e linha de base da suíte

> Identificador da feature: `007-dono-no-port-e-baseline`
> Data: `2026-10-07`
> Cenário: **legado** (âncora em `_reversa_sdd/architecture.md` + `_reversa_sdd/domain.md`)

## Vigência

Vigente desde 2026-10-07.

## Resumo da entrega

A feature fecha os **dois desvios declarados** que a Onda 2 deixou fora do escopo.

O primeiro é de **contrato**: o port de repositório de árvores recebia a identidade do
dono desde a 006, e o port de **armazenamento de arquivo** não — uma assimetria que a
Onda 3 teria de resolver reabrindo a assinatura da porta e todos os seus chamadores. O
dono entrou nos **dois** métodos de `ArmazenamentoDeArquivos` e no método de
`CarregadorDeArvores`, como último parâmetro posicional e sem valor padrão, **sem
comportamento nenhum**: a chave continua derivada do conteúdo, o caminho continua o
mesmo, e nada passou a ser isolado por dono.

O segundo é de **verificação**: 15 testes de rota de `tests/test_upload_seguranca.py`
não executavam nesta máquina, porque o pytest tentava **listar** um diretório-base
criado com `0o700`. A correção declarou o fixture `tmp_path` em `tests/conftest.py`, e
os 15 passaram a executar — e **passam**, o que encerra a triagem da `RF-09` por
medição. A linha de base da suíte foi remedida no interpretador oficial.

| Prova | Resultado |
|---|---|
| Suíte (`.venv/`) | **261 aprovados, 0 erros de ambiente** |
| Linha de base anterior | `231 aprovados, 15 erros` — agora **histórica** |
| Paridade diferencial | **100 %** nas 6 fixtures, exit 0 |
| Mensagens de tela (19 casos) | **zero divergência** contra a entrega da 006 |
| Forma dos chamadores | **APROVADO** — 5 chamadores de porta, todos passando o dono |
| Verificação manual de ponta a ponta | **APROVADO** — os três fluxos, e nenhum resíduo |

**Progresso: 16 de 16 ações concluídas**, nenhuma aberta em `actions.md`.

⚠️ **A Onda 3 do cutover continua NÃO satisfeita.** Esta feature **prepara** a costura
que ela consome; não implementa isolamento. As dívidas **#4** (ausência de isolamento)
e **#3** (contaminação entre requisições concorrentes) seguem **abertas**, e o
`cutover_plan.md#Pré-requisitos` continua exigindo o teste negativo de isolamento
(`404`, não `403`) que ainda não existe. Os artefatos de `migration/` **não** foram
reescritos, pela mesma decisão de 2026-10-07 que a feature 006 registrou.

## Impacto por artefato da extração

| Artefato | Seção | Tipo de impacto | Delta |
|---|---|---|---|
| `_reversa_sdd/architecture.md` | `#3` (Componentes e estrutura de pacotes) | `regra-alterada` | Leia `ports/__init__.py` como **três portas que exigem o dono** — último parâmetro posicional, sem padrão — e `ports/adaptadores.py` como adaptadores que **aceitam o dono e não o usam**. Nenhum método novo foi criado: `CarregadorDeArvores` continua com um só |
| `_reversa_sdd/architecture.md` | `#1` (Visão Geral da Arquitetura) | `presença` | ❌ Nada mudou de forma. `index()` continua **sem passo de domínio**; a alteração em `src/app.py` são dois argumentos e um comentário. Não leia esta entrega como nova camada |
| `_reversa_sdd/architecture.md` | `#7` (Dívidas), #3 e #4 | `presença` | ❌ **INALTERADAS.** Nenhum comportamento de isolamento existe, e a guarda de exclusividade continua de **processo**, não de thread. O que mudou é que as duas agora estão **nomeadas** no comentário de `DONO_DO_PROCESSO`, em `src/app.py`. Nomear não é fechar |
| `_reversa_sdd/architecture.md` | `#7` (Dívidas), #5, #8, #10, #17 e #18 | `presença` | ❌ **INALTERADAS.** Os ciclos entre pacotes continuam; nada é persistido; o CSV de DNA continua sem validação de conteúdo (de propósito); nenhuma superfície de compatibilidade nova; `cm_estimator.py` segue em disco sem reexport |
| `_reversa_sdd/domain.md` | `#3.5` (Upload e armazenamento) | `presença` | ❌ A **regra não mudou**: chave por conteúdo, forma `<chave>__<nome visível>`, conteúdo já armazenado não é regravado, extensão preservada, teto de 16 MB, validação antes da gravação. O que mudou é que a porta que implementa a regra **recebe o dono** — e o ignora. O dono **não** entra na chave nem no caminho (`RN-02`) |
| `_reversa_sdd/domain.md` | `#5.1` (Camada de rota) | `presença` | ❌ As dez mensagens continuam **literais e nos mesmos casos**. Medido em 19 casos, com comparação de status HTTP, **classe do alerta** e texto, contra a entrega da 006 |
| `_reversa_sdd/domain.md` | `#5.2` (Núcleo) | `presença` | ❌ Nenhum texto, tipo ou limiar do núcleo foi tocado. `src/core/`, `src/parsers/`, `src/reporting/` e `src/utils/` não têm uma linha alterada |
| `_reversa_sdd/domain.md` | `#2`, `#3.1`–`#3.4`, `#3.6`, `#3.7`, `#4` | `presença` | ❌ **NENHUMA regra de negócio criada, alterada ou removida.** A paridade em 100 % nas 6 fixtures é a prova, e ela é o instrumento que compara o núcleo contra o oráculo congelado |
| `_reversa_sdd/permissions.md` | `P-01` a `P-05` | `presença` | ❌ Continua **zero** papel, **zero** sessão e **zero** autenticação. ⚠️ **O dono NÃO é credencial**: é um marcador único de processo com valor `"unico"`, e a `RN-06` proíbe citar esta entrega como tendo implementado isolamento |
| `_reversa_sdd/addenda/006-fronteira-aplicacao-ports.md` | `D-03`, `RF-08`, `RN-06` | `regra-alterada` | O adendo da 006 continua **vigente**, e ele descreve o dono apenas na porta de **repositório**. Leia os dois juntos: este estende a exigência às outras duas portas. O `RepositorioDeArvores` continua declarado, **sem implementação e sem consumidor** |
| `_reversa_sdd/c4-components.md` | "Camada de rota" e "Cadeia de dependência dos três fluxos" | `presença` | ❌ Nada a acrescentar por esta feature. O inventário continua precisando do que o adendo da 006 já apontou — `application/`, `ports/` e `core/erros.py` —, e a cadeia dos fluxos não mudou de forma |
| `_reversa_sdd/code-analysis.md` | `#2.2` e `#4.3`; e `upload-gedcom/design.md`, "Camada de rota" | `presença` | ⚠️ As faixas de linha citadas para `src/app.py` **já estavam defasadas** pela feature 006 e continuam defasadas: esta entrega acrescentou cerca de trinta linhas ao arquivo. Leia os apontadores de linha de `app.py` como **aproximados**, e o nome da função como a parte que vale |

## Regras sob vigilância

`W020` a `W025`, definidos em
`_reversa_forward/007-dono-no-port-e-baseline/regression-watch.md`, mais as
observações `OBS-21` a `OBS-29` do mesmo arquivo.

| Item | Cobre |
|---|---|
| `W020` | O dono não entra na chave nem no caminho do armazenamento |
| `W021` | O `tmp_path` da suíte é o do projeto, e continua utilizável |
| `W022` | As três portas continuam simétricas quanto ao dono |
| `W023` | A linha de base vigente, e a comparação por conjunto em vez de por total |
| `W024` | Os 15 testes de rota executam, e nenhum foi reescrito |
| `W025` | A constante de dono é única, e o lugar dela declara o que a `RF-04` exige |

**Dois itens merecem leitura explícita.** O `W020` é o que a Onda 3 vai querer
quebrar: a tentação é pôr o dono no caminho do arquivo para "isolar", e isso é
mudança de comportamento observável — dois envios do mesmo conteúdo por donos
diferentes deixariam de reencontrar o mesmo arquivo. O `W021` existe porque a
correção do ambiente é **invisível**: o sintoma de ela sair de vigor é um `erro de
ambiente`, que já foi atribuído à máquina duas vezes neste projeto.

## O que a extração **não** precisa mudar

- **A forma dos dados.** O `Tree` continua a tupla de quatro elementos, e a
  assinatura de retorno do núcleo continua congelada: `path_search` e `dna_analysis`
  devolvem a tupla de três com o indicador de sucesso. Nenhum campo de desfecho entra
  no núcleo.
- **A superfície HTTP.** Mesmas rotas, mesmos campos de formulário, mesmos status,
  mesmo template. O `dono` é parâmetro **interno** entre borda, caso de uso e porta:
  não é campo de formulário, não é cabeçalho e não é credencial.
- **O leiaute de armazenamento em disco.** Nenhum arquivo em `uploads/` precisa ser
  renomeado ou movido, e nenhum é. Foi consequência direta da `RN-02`: se o dono
  entrasse na chave, esta feature passaria a ter migração de dados em disco — e não
  tem nenhuma.
- **Os artefatos de `migration/`.** Continuam válidos como plano de ondas futuras
  (FastAPI, PostgreSQL, React) e não foram reescritos. A Onda 3 continua **No-go**
  pelos mesmos motivos de antes, com um a menos: o custo de reabrir as assinaturas.

## Lacunas declaradas

Nem tudo neste adendo é uma afirmação verificada. O que segue é limite de
conhecimento, e não omissão:

1. **Os dois números antigos da linha de base ficam como estão.** O par `178
   aprovados, 15 erros de ambiente` (feature 005) e o par `231 aprovados, 15 erros`
   (feature 006) **não** foram reescritos nos artefatos que os registraram — nem
   neste adendo da 006. Eles são leitura **histórica**, não errada: foram medições
   reais, feitas numa máquina onde 15 testes não executavam. A regra de comparação
   entre entregas passa a ser por **conjunto** (nenhum aprovado vira falha), e não
   por total (`RN-04`).
2. **A causa raiz registrada pela 006 está correta e imprecisa num ponto.** O
   `OBS-12` afirma que "o `tmp_path_factory` cria o diretório-base com `mode=0o700`".
   O passo que falha não é a criação do diretório **por teste**: é o
   `TempPathFactory.getbasetemp()`, que cria `pytest-of-<usuário>` com `0o700` e em
   seguida tenta **listá-lo** por `os.scandir` (`_pytest/pathlib.py:175`). O ramo do
   `mktemp`, que também usa `0o700`, nunca chega a rodar. É por isso que "trocar o
   modo do diretório por teste" não corrigiria nada.
3. **Os 13 diretórios presos continuam no workspace.** Eles são resíduo de execução,
   não defeito do produto, e a remoção exige shell elevado. Esta entrega impede que
   **novos** apareçam, e não remove nenhum existente. O `collect_ignore` de
   `tests/conftest.py` permanece por isso.
4. **O `git status` sujo do instrumento de paridade foi resolvido.** O harness deixa
   dois diretórios e dois scripts de trabalho a cada execução — `.parity-run-oracle/`,
   `.parity-run-cand/`, `_reversa_sdd/parity/_collect_oracle.py` e `_collect_cand.py` —
   e só o primeiro estava no `.gitignore`. **Atualização de 2026-10-07, posterior à
   conferência de escopo:** as duas linhas que faltavam foram acrescentadas ao
   `.gitignore` por **ato do usuário**, e a eficácia foi verificada com
   `git check-ignore -v` e com arquivo dentro dos diretórios:**

   ```gitignore
   tests/.tmp/
   .parity-run-cand/
   ```

   O resíduo **em disco** continua existindo enquanto o instrumento rodar; o que
   mudou é ele deixar de sujar o `git status`. Ver `OBS-29` do
   `regression-watch.md` e `evidence/T016-conferencia-de-escopo.md` §6.
5. **O `W019` da feature 006 continua não resolvido:** o Gherkin congelado diz
   `Resultados da Análise de DNA` e o template renderiza `Resultado da Análise`. O
   template **não** foi tocado por esta feature, e a decisão segue pendente.
6. **A decomposição desta feature errou uma enumeração, e o erro está registrado.**
   Ela contou os chamadores de `guardar` e de `resolver` e esqueceu os de `carregar`:
   `src/application/upload_gedcom.py:67` ficou sem o dono e **11 testes falharam** na
   primeira execução do Bloco 1. Corrigido na mesma rodada. A varredura de forma
   passou a **afirmar a contagem** de 5 chamadores, para que a próxima lacuna dessas
   falhe alto em vez de passar despercebida.
7. **O `RepositorioDeArvores` continua sem implementação e sem consumidor**, como a
   `D-03` da 006 decidiu. Esta feature prepara a porta de **armazenamento**, não a
   persistência — quem ler "a costura do dono está completa" não deve concluir que
   existe repositório.
8. **O instrumento de paridade não foi alterado por esta feature**, e ele continua
   sendo a única comparação contra o oráculo congelado. Esta entrega o executou e
   registrou a saída; não o estendeu.

## Fontes

- `_reversa_forward/007-dono-no-port-e-baseline/legacy-impact.md` (fonte principal do delta)
- `_reversa_forward/007-dono-no-port-e-baseline/regression-watch.md` (`W020` a `W025`, `OBS-21` a `OBS-29`)
- `_reversa_forward/007-dono-no-port-e-baseline/requirements.md` (objetivo, `RN-01` a `RN-06`, `RF-01` a `RF-12`)
- `_reversa_forward/007-dono-no-port-e-baseline/roadmap.md` (`D-01` a `D-12`)
- `_reversa_forward/007-dono-no-port-e-baseline/actions.md` (16 de 16 ações concluídas, e as Notas de execução)
- `_reversa_forward/007-dono-no-port-e-baseline/progress.jsonl` (19 eventos)
- `_reversa_forward/007-dono-no-port-e-baseline/data-delta.md` (sem delta de dados)
- `_reversa_forward/007-dono-no-port-e-baseline/investigation.md` (a causa raiz medida e as alternativas avaliadas)
- `_reversa_forward/007-dono-no-port-e-baseline/evidence/README-evidencias.md` (os cinco instrumentos)
- `_reversa_forward/007-dono-no-port-e-baseline/evidence/T004-linha-de-base-bloco0.md`,
  `T011-varredura.txt`, `T012-mensagens.txt`, `T014-suite-bloco1.txt`,
  `T015-verificacao-manual.md`, `T016-conferencia-de-escopo.md` (medições)
- `_reversa_sdd/architecture.md`, `_reversa_sdd/domain.md`, `_reversa_sdd/permissions.md`,
  `_reversa_sdd/c4-components.md`, `_reversa_sdd/code-analysis.md`,
  `_reversa_sdd/addenda/006-fronteira-aplicacao-ports.md` (conferência de nomes de seção)

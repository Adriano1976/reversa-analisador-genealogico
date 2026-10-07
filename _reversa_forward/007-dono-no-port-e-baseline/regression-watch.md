# Regras sob vigilância — feature `007-dono-no-port-e-baseline`

> Feature: `007-dono-no-port-e-baseline`
> Data: `2026-10-07`
> Base do watch: seção "Modificadas" do `legacy-impact.md` desta feature
> Executor: `/reversa-coding`

> **IDs.** Esta feature continua a numeração do projeto: a `005-nucleo-puro-src` usou
> `W001` a `W004` e `OBS-01` a `OBS-10`; a `006-fronteira-aplicacao-ports` usou
> `W005` a `W019` e `OBS-11` a `OBS-20`. IDs são estáveis e não se reciclam entre
> features: um `W012` é sempre o mesmo item, em qualquer leitura.

## Itens sob vigilância

> O watch principal recebe regras que **eram 🟢** e foram alteradas. Esta feature
> alterou o **contrato de duas portas internas** e o **instrumento de verificação da
> suíte** — e não alterou comportamento nenhum. **Nenhuma regra foi removida**, então
> não há item do tipo `ausência` nesta rodada.

| ID | Origem (arquivo, seção) | Regra esperada após mudança | Tipo de verificação | Sinal de violação |
|---|---|---|---|---|
| **W020** | `_reversa_sdd/domain.md#3.5` + `src/ports/__init__.py` | O dono **não** entra na chave nem no caminho do armazenamento. Dois envios do mesmo conteúdo com donos diferentes continuam reencontrando **um** arquivo, e o arquivo já gravado **não** é regravado | `presença` | `tests/test_porta_de_armazenamento.py::TestContratoDoArmazenamento` falha, ou a pasta de upload fica com mais de um arquivo para o mesmo conteúdo. A tentação da Onda 3 é pôr o dono no caminho: isso é mudança de comportamento observável, e a `RN-02` a proíbe |
| **W021** | `tests/conftest.py`, fixtures `pasta_temporaria` e `tmp_path` | O `tmp_path` da suíte é o **do projeto** (`tests/.tmp/`), criado em modo padrão, e ele é listável, gravável e removível | `presença` | A suíte volta a reportar `ERROR ... at setup` com `PermissionError [WinError 5]` sobre `pytest-of-<usuário>`. `tests/test_ambiente_temporario_da_suite.py` falha **primeiro**, e é esse o aviso antecipado |
| **W022** | `src/ports/__init__.py`, as três portas | `ArmazenamentoDeArquivos.guardar`, `.resolver` e `CarregadorDeArvores.carregar` continuam com `dono` obrigatório, **sem valor padrão**, na **última** posição; e `CarregadorDeArvores` continua com **um único** método | `presença` | Uma porta sem o dono, um valor padrão aparecendo, o dono mudando de posição, ou um segundo método no carregador (que é a condição declarada da `D-02` da 006 — ver `OBS-15`). `T010` cobre as três primeiras; a quarta é leitura |
| **W023** | `legacy-impact.md` §5, `RN-04` | A linha de base vigente é a **medição pós-correção** no interpretador oficial, com o comando registrado ao lado; e a comparação entre entregas é por **conjunto** (nenhum aprovado vira falha), nunca por total | `redação` | Alguma entrega comparada por total contra `178 aprovados, 15 erros` ou `231 aprovados, 15 erros` como se medissem o mesmo conjunto. Os dois números são **históricos**, e não errados |
| **W024** | `RF-06`, suíte | Os 15 testes de `tests/test_upload_seguranca.py` continuam **executando**, e nenhum teste foi removido, desabilitado, renomeado por conveniência ou teve asserção reescrita | `presença` | `git diff --stat -- tests/test_upload_seguranca.py` deixa de ser vazio; a contagem cai abaixo de `261` sem justificativa medida; aparece `skip`/`xfail` novo sem defeito que o justifique |
| **W025** | `RF-04`, `src/app.py`, constante `DONO_DO_PROCESSO` | Existe **uma só** declaração do valor de dono em produção; todos os chamadores passam expressão, e nenhum literal no próprio local; e o bloco da constante declara a ausência de isolamento, a **dívida #3** e que o dono não é mecanismo de segurança | `presença` | `python _reversa_forward/007-dono-no-port-e-baseline/evidence/_t011_varredura.py` sai diferente de APROVADO — inclusive pela **contagem** de chamadores, que é 5 e existe para obrigar a revisão quando um chamador novo aparecer (ver `OBS-24`) |

## Observações

> Sem peso de regressão. Regras que **não** eram 🟢 ficam aqui, e não no watch
> principal. Registradas porque uma leitura futura precisa saber que existem.

| ID | Observação | Por que importa |
|---|---|---|
| **OBS-21** | 🔴 **Achado para ato do usuário.** O instrumento de paridade deixa `.parity-run-cand/` **não rastreado**, enquanto o irmão `.parity-run-oracle/` está coberto pelo `.gitignore`. Consequência: **toda** execução do harness suja o `git status`. `.gitignore` **não** está em `allowedPaths` | Acrescentar `.parity-run-cand/` ao `.gitignore`. É comportamento **anterior** a esta feature, encontrado ao conferir o escopo (`evidence/T016` §4) |
| **OBS-22** | 🔴 **Achado para ato do usuário.** `tests/.tmp/` — a raiz temporária da suíte — também **não** está no `.gitignore`, e o mesmo arquivo está fora de `allowedPaths` | A rede contra resíduo é a remoção medida em `D-03` (zero resíduo), não uma linha de ignore. Acrescentar `tests/.tmp/` é ato do usuário, e o roadmap já declarava essa consequência antes da execução |
| **OBS-23** | O `W019` da feature 006 continua **não resolvido**: o Gherkin congelado diz `Resultados da Análise de DNA` e o template renderiza `Resultado da Análise` | Esta feature **não** tocou o template — mudar literal visível é o que a `RN-04` proíbe. A divergência segue sendo decisão pendente do usuário, e não regressão |
| **OBS-24** | ⚠️ **Lacuna da decomposição, medida.** O plano enumerou os chamadores de `guardar` e de `resolver`, e **não** os de `carregar`: `src/application/upload_gedcom.py:67` ficou sem o dono e **11 testes falharam** na primeira execução do Bloco 1. Corrigido na mesma rodada, e declarado em `actions.md` "Notas de execução" | A lição é operacional: enumeração de chamadores de porta tem de cobrir **os três** métodos, porque a assinatura mudou nos três. A contagem de 5 passou a ser **asserção** do `_t011_varredura.py`, então a próxima lacuna dessas falha alto |
| **OBS-25** | A triagem da `RF-09` está **vazia por medição**: os 15 testes **passam** quando executam. A verificação manual e a suíte confirmam, e não há defeito de produto escondido atrás do erro de ambiente | Se os 15 voltarem a falhar por motivo de produto, a `RF-09` **volta a valer integralmente**: veredito explícito e datado por falha, defeito de produto vira requisito próprio com arquivo e linha, defeito de teste é corrigido com o motivo declarado. O procedimento está no §12 do `onboarding.md` |
| **OBS-26** | As dívidas #3 (contaminação entre requisições concorrentes), #4 (ausência de isolamento), #5 (ciclos entre pacotes), #8 (nada é persistido), #10 (CSV sem validação de conteúdo), #17 (superfícies de compatibilidade) e #18 (`cm_estimator` em disco) continuam **abertas** | A #3 e a #4 agora estão **nomeadas no código**, no comentário de `DONO_DO_PROCESSO`. Nomear não é fechar: a `RN-06` proíbe citar esta entrega como tendo implementado isolamento, e nenhum comportamento de isolamento existe |
| **OBS-27** | `src/uploads/` tem **33 entradas**, incluindo um GEDCOM **real** do operador (`Arvore_Unificada_Oficial_V1_2.ged`) e o diretório preso `_pytest` criado pela rodada da 006. A pasta é coberta por `uploads/` no `.gitignore` | Princípio I preservado: o dado real **não** é versionado, e a pasta existe para recebê-lo. Esta rodada **não** escreveu nada ali — a verificação manual apontou `ANALISADOR_UPLOAD_FOLDER` para uma pasta descartável (`evidence/T015` §2) |
| **OBS-28** | Os **13 diretórios presos** continuam presos e apenas **documentados**, com o comando de remoção que exige shell elevado. O `collect_ignore = ["_basetemp_probe"]` de `tests/conftest.py` permanece, e **só** sai quando o diretório for removido | A correção do `W021` impede diretórios presos **novos**; ela não remove nenhum existente. Remover o `collect_ignore` antes do diretório sair faz a coleta da suíte abortar **inteira**, e o sintoma não parece com a causa |
| **OBS-29** | ✅ **Fecha o `OBS-21` e o `OBS-22`.** As duas linhas foram acrescentadas ao `.gitignore` — `tests/.tmp/` (linha 22) e `.parity-run-cand/` (linha 23) —, por **ato do usuário** logo após o relatório do `/reversa-coding`. Verificado com `git check-ignore -v` **com arquivo dentro** dos diretórios: o `git status` deixa de listar os dois | A verificação teve de ser refeita: diretório **vazio** não mede `.gitignore`, porque o git não rastreia diretório vazio de qualquer forma — a primeira tentativa desta conferência passou por verde sem medir nada. O resíduo **em disco** continua enquanto o instrumento rodar; o que muda é ele deixar de sujar o `git status`. Detalhe em `evidence/T016-conferencia-de-escopo.md` §6 |

## Histórico de re-extrações

> Preenchido pelo agente reverso quando `/reversa` rodar de novo. Vazio nesta data.

## Arquivadas

> Vazio nesta data.

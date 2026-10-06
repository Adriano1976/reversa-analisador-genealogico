# Relatório de Confiança — teste_reversa

> Gerado pelo **Reversa-Reviewer** na re-extração de **2026-10-05** (nível **Completo**). Substitui integralmente o relatório de 2026-09-30.
> **Atualizado em 2026-10-05** após o processamento de **16 de 16 perguntas** de `questions.md`. **Quatro decisões mudaram código** (`matching.py`, `app.py`, `genetic_evidence.py` e os testes) e uma **mudou o pin** (`requirements.txt`).
> Revisão cruzada por engine externa: **não realizada** — nenhuma ferramenta `codex:` está ativa nesta sessão, conforme o Passo 0 do agente.
> Este relatório cobre: **3 units** (9 canônicos + 3 `contracts.md`), **17 artefatos transversais com marcadores** (mais o `openapi/index.yaml`, que não usa marcadores), **23 ADRs**.
> Método de contagem: ocorrência dos marcadores 🟢/🟡/🔴 por arquivo, **excluindo as linhas de legenda** (aquelas que citam os três nomes ao mesmo tempo). É a mesma convenção das rodadas anteriores.

---

## Resumo Geral

| Escopo | 🟢 | 🟡 | 🔴 | Total | Confiança |
| --- | ---: | ---: | ---: | ---: | ---: |
| **3 units** (requirements+design+tasks+contracts) | 941 | 35 | 34 | 1.010 | **94,9 %** |
| **Artefatos transversais** (17) | 751 | 54 | 41 | 846 | **92,0 %** |
| **ADRs** (23) | 45 | 6 | 15 | 66 | 72,7 % |
| **Extração completa** | **1.737** | **95** | **90** | **1.922** | **92,8 %** |

**Confiança geral: 92,8 %** — `(1.737 + 95×0,5) / 1.922`

> **Evolução dentro desta própria revisão.** O relatório nasceu com **1.923 afirmações**, **91,5 %** e **109 🔴**. As 16 decisões humanas elevaram para **92,8 %** e derrubaram os 🔴 para **90** — porque **quatro lacunas foram executadas no código** e uma **mediu o que era suposto**: a cobertura, que passou de "não medida" a **83 %** apurados.
>
> **Comparação com a re-extração anterior:** 819 afirmações com **90,5 %**. Hoje são **1.918** — 2,3× mais — com **92,4 %**. O volume cresceu porque a rodada gerou o que o nível `completo` exige e que o `essencial` não gerava: os **23 ADRs**, o **ERD completo**, os **níveis 2 e 3 do C4**, a **matriz de impacto**, as **3 specs de contrato**, as **user stories** e o **OpenAPI**.
>
> **Os ADRs têm a menor confiança do conjunto (69,9 %), e isso é esperado:** eles são reconstrução de decisão a partir de commit, código e registro de bug — não leitura de comportamento. Onde não há prosa de decisão, a ADR **declara a ausência** em vez de preencher (ADR-03, ADR-07, ADR-12, ADR-14, ADR-22).

---

## Por Spec

### Units

| Spec | 🟢 | 🟡 | 🔴 | Total | Confiança |
| --- | ---: | ---: | ---: | ---: | ---: |
| `upload-gedcom/` | 222 | 9 | 8 | 239 | **94,8 %** |
| `analise-dna/` | 374 | 14 | 10 | 398 | **95,7 %** |
| `busca-caminho/` | 345 | 12 | 16 | 373 | **94,1 %** |

> **`analise-dna` deixou de ser a unidade com mais 🔴** (de 20 para **10**): era onde estava a divergência viva, agora executada. A distribuição ficou mais uniforme — e `busca-caminho` passou a concentrar os vermelhos que restam no núcleo de domínio.

### Artefatos transversais

| Artefato | 🟢 | 🟡 | 🔴 | Total | Confiança |
| --- | ---: | ---: | ---: | ---: | ---: |
| `inventory.md` | 33 | 2 | 0 | 35 | 97,1 % |
| `dependencies.md` | 21 | 4 | 2 | 27 | 85,2 % |
| `code-analysis.md` | 262 | 12 | 3 | 277 | 96,8 % |
| `data-dictionary.md` | 37 | 0 | 0 | 37 | **100,0 %** |
| `domain.md` | 96 | 8 | 1 | 105 | 95,2 % |
| `state-machines.md` | 31 | 1 | 1 | 33 | 95,5 % |
| `permissions.md` | 30 | 4 | 1 | 35 | 91,4 % |
| `architecture.md` | 32 | 12 | 6 | 50 | 76,0 % |
| `c4-context.md` | 12 | 1 | 0 | 13 | 96,2 % |
| `c4-containers.md` | 19 | 1 | 2 | 22 | 88,6 % |
| `c4-components.md` | 25 | 0 | 3 | 28 | 89,3 % |
| `erd-complete.md` | 65 | 0 | 1 | 66 | 98,5 % |
| `openapi/index.yaml` | — | — | — | — | *sem marcadores* |
| `traceability/code-spec-matrix.md` | 38 | 3 | 3 | 44 | 89,8 % |
| `traceability/spec-impact-matrix.md` | 20 | 2 | 11 | 33 | 63,6 % |
| `user-stories/upload-gedcom.md` | 20 | 0 | 3 | 23 | 87,0 % |
| `user-stories/analise-dna.md` | 5 | 2 | 2 | 9 | 66,7 % |
| `user-stories/busca-caminho.md` | 5 | 2 | 2 | 9 | 66,7 % |

> **Os dois artefatos com menor confiança são os que existem para expor risco**, e não para descrever comportamento: `spec-impact-matrix.md` (63,6 %) concentra as lacunas de **ordem determinística**, de **constantes embutidas em mensagens** e de **cobertura desigual de teste**; `architecture.md` (70,0 %) consolida as **20 dívidas técnicas**. Confiança baixa ali significa que o documento está fazendo o trabalho dele.
>
> **`openapi/index.yaml` não usa marcadores** — é contrato, e o próprio cabeçalho declara a natureza e os limites. Foi validado por parsing (js-yaml): 1 path, 5 schemas, 3 ações, status `200` e `413`.

---

## Verificações de Consistência Executadas

| # | Verificação | Método | Resultado |
| ---: | --- | --- | --- |
| 1 | Os 3 canônicos + opcionais existem em cada unit | varredura do sistema de arquivos | ✅ **9 canônicos + 3 `contracts.md`** presentes; nenhuma unit incompleta |
| 2 | Units geradas == `surface.json.modules` | comparação de conjuntos | ✅ **3/3** — `upload-gedcom`, `analise-dna`, `busca-caminho`; nada faltando nem sobrando |
| 3 | Nenhuma afirmação funcional sobre símbolo extinto | varredura de `HARD_MIN`, `GIVEN_MIN`, `process_dna`, `given_index`, `Pyvis`, `STATIC_FOLDER`, `ensure_dirs` | ✅ **todas** as ocorrências são **avisos de "não fazer isso"** ou registro histórico em ADR. `process_dna` e `ensure_dirs`: **zero**. |
| 4 | Globais do nível `completo` presentes | verificação de existência | ✅ `code-spec-matrix.md`, `spec-impact-matrix.md`, `gaps.md`, `openapi/index.yaml` e 3 `user-stories/` |
| 5 | Constantes de contrato coerentes entre units | busca de `MAX_DEPTH`, `MAX_HOPS`, `LIMITE_SEGMENTO_FRACO`, `MAX_CONTENT_LENGTH`, Jaccard, faixa 12–70 | ✅ cada constante declarada com **um** valor e referenciada, nunca redefinida: 20 · 40 · 15 cM · 16 MB · 0,50 / 0,33 · 12–70 |
| 6 | Contagem de RFs confere com o publicado | contagem de linhas de tabela `\| RF-nn \|` | ✅ **19 / 26 / 24 = 69** (a contagem bruta por regex dá 39 nas units 2 e 3 porque as tabelas **MoSCoW** também começam com `\| RF-`; conferido linha a linha) |
| 7 | Dependências entre units são reais | confronto com o grafo de importações | ✅ `analise-dna` → `busca-caminho` → `upload-gedcom`; **sem ciclo de módulo** |
| 8 | Referências a `adrs/NN` resolvem | extração das referências e teste de existência | ✅ **10 números referenciados** (05, 09, 13, 14, 15, 18, 19, 21, 22, 23), todos entre os **23 arquivos existentes** |
| 9 | O `L-06` se confirma? | leitura do template | ❌ **NÃO se confirma** — ver reclassificação abaixo |
| 10 | Afirmações 🟡 reclassificáveis por evidência direta | releitura de `matching.py`, `evidence_comparison.py`, `path_search.py`, `mermaid_render.py` | ✅ 4 upgrades aplicados (abaixo) |

---

## Histórico de Reclassificações

### Nesta rodada

| De | Para | Afirmação | Evidência |
| --- | --- | --- | --- |
| 🔴 | 🟢 | **`L-06`: "sem conexão" e "erro" seriam indistinguíveis no template** | **Falso.** `index.html:43-45` decide a **cor do alerta** por `success` (`'success' if success else 'danger'`); `:457` decide se o **cartão de resultado** aparece, por `path_result`. Os três desfechos — conexão, sem conexão, erro — produzem telas distintas. Lacuna **fechada por verificação**. |
| 🟡 | 🟢 | Mapa de mojibake com 18 entradas e 17 chaves efetivas | medido por AST na escavação; confirmado na spec de contrato |
| 🟡 | 🟢 | `get_spouses` faz varredura global **apenas** quando `FAMS` fica vazio | `family_navigation.py:66-75` — o código confirma a condicional |
| 🟡 | 🟢 | O teto do BFS conta **iterações de profundidade**, não gerações | `path_finding.py:51-85` — o laço alterna um nível por lado |
| 🟡 | 🟢 | O escape do rótulo aplica entidades **depois** do filtro | `mermaid_render.py:59-60`; `tests/test_mermaid_escape.py` |

### Decisões humanas aplicadas em 2026-10-05 (as 16 perguntas)

Você respondeu **todas as 16**. **Quatro decisões mudaram código** e uma **mudou o pin** — o que exigiu editar o legado, autorizado por `.reversa/reversa-config.json` (`allowedPaths` cobre `src/**`, `tests/**`, `requirements.txt` e `README.md`).

| # | Resposta | O que mudou | Lacuna |
| ---: | --- | --- | --- |
| **1** | Corrigir o legado agora | `matching.py`: **quarto critério** de desempate (menor `xref_id`, `:107-110`). 2 testes novos | ✅ `L-15` fechada |
| **2** | Remover a linha | `app.py`: `app.secret_key` **removido** | ✅ `P-04` fechada |
| **3** | É omissão — Onda 3 | Registrado em `permissions.md`; **sem** mudança no legado (correção é inverificável sem identidade) | ✅ `P-01` decidida |
| **4** | Herança — quero histórico no alvo | `domain.md`, `erd-complete.md`; **requisito encaminhado ao alvo nº 1** | ✅ `L-21` / `E-04` |
| **5** | Discartes são **acionáveis** | `RF-23` sobe para `Must`; **nova seção** em `analise-dna/design.md` com a ação por motivo | ✅ `L-22` fechada |
| **6** | **Restringir** a lista de nomes | `permissions.md`; **requisito encaminhado ao alvo nº 3** (busca no servidor, Onda 4) | ✅ `P-03` decidida |
| **7** | Avisar basta | `domain.md`, `adrs/21` com status confirmado | ✅ `L-17` fechada |
| **8** | **É requisito** — registrar veredito | `state-machines.md`; **requisito encaminhado ao alvo nº 2** | ✅ `M-04` decidida |
| **9** | Foi um **chute** que funcionou | O `0,33` passa a **heurístico e ajustável** | ✅ `L-14` fechada |
| **10** | Só **GEDmatch** | `analise-dna/contracts.md`: cobertura **declarada** | ✅ `L-08` fechada |
| **11** | O **`.venv`** é o oficial | `requirements.txt` realinhado + **`rapidfuzz` e `python-Levenshtein` declarados**; `pytest` instalado no `.venv` | ✅ `L-19` fechada |
| **12** | **Medir** a cobertura | `pytest-cov` no `.venv`: **83 %** de `src/`, com detalhe por módulo | ✅ `L-23` fechada |
| **13** | **Intencional** | `state-machines.md`: a assimetria vira **contrato** | ✅ `M-02` fechada |
| **14** | **Herdado** — corrigir no alvo | `permissions.md`; **requisito encaminhado ao alvo nº 4** | ✅ `P-05` decidida |
| **15** | **Trocar** a sentinela | `genetic_evidence.py`: `SEM_KIT = " SEM-KIT"` (espaço à esquerda); **1 teste novo** prova 3 grupos separados | ✅ `E-03` fechada |
| **16** | **Nunca vi** resultado cruzado | `gaps.md`: a lacuna **permanece aberta** — nunca observada, mas o mecanismo é confirmado | ⚠️ `L-16` / `M-03` |

> **Duas notas de honestidade sobre esta tabela:**
>
> 1. **A pergunta 11 foi a de maior consequência**, e não a 1. Encerrar a divergência de ambiente eliminou o risco de duas execuções do **mesmo código** darem resultados diferentes — algo que nenhuma quantidade de testes detecta, porque o código está certo.
> 2. **A pergunta 16 não fechou nada.** Ela mudou a **probabilidade percebida**, não a existência da janela de corrida. Registrar isso é mais útil do que tratá-la como resolvida.

**Verificação das mudanças de código** 🟢

| Verificação | Comando | Resultado |
| --- | --- | --- |
| Testes do matching | `pytest tests/test_characterization_matching.py -q` | **24 passam** (incluindo os 2 novos) |
| Testes do confronto | `pytest tests/test_confrontacao_gedcom_dna.py -q` | **30 passam** (incluindo o de não-colisão da sentinela) |
| Testes sem `tmp_path` | 9 arquivos, incluindo `test_servidor_producao.py` e `test_formatacao_cm.py` | **121 passam** |
| **Suíte completa — global** | `python -m pytest -q` | **164 passam, 15 erros** |
| **Suíte completa — `.venv`** | `.venv/Scripts/python.exe -m pytest -q` | **164 passam, 15 erros** — **idêntico** |
| Cobertura | `.venv/Scripts/python.exe -m pytest --cov=src` | **83 %** (1.520 instruções, 253 descobertas) |
| `app` importável | `import app` | OK; `app.secret_key` deixou de ter valor |

> ⚠️ **Os 15 erros da suíte completa não são regressão.** São todos de `tests/test_upload_seguranca.py`, **em `setup`**, causados por `PermissionError [WinError 5]` quando o pytest cria/limpa o diretório temporário. Reproduzem com **qualquer** `--basetemp` — inclusive dentro do workspace — e **já haviam sido registrados em 2026-09-30** como restrição do ambiente. A conta fecha: **164 + 15 = 179 itens**, contra 175 antes desta rodada (4 testes acrescentados).

### Contra a extração anterior — correções aplicadas nas specs desta rodada

| De | Para | Afirmação da spec antiga | O que o código de 2026-10-05 mostra |
| --- | --- | --- | --- |
| 🟢 | 🔴 | "Upload sem validação de extensão/tamanho é decisão vigente do usuário" | **Superada.** Há teto de 16 MB, validação de conteúdo e chave derivada do conteúdo (`BUG-20260929-QMLY`) |
| 🟢 | 🔴 | "Homônimos usam o 1º ID, sem desempate e sem aviso" | **Ampliada.** Testa até 5×5 combinações; a ambiguidade é **avisada**. O 1º ID virou recuo |
| 🟢 | 🔴 | "A previsão de parentesco vem de 9 faixas de cM" | **Substituída.** Vem da tabela publicada do SCP 4.0, com envoltória por meioses; as faixas saíram do fluxo |
| 🟢 | 🔴 | "`get_relationships_by_cm` é o núcleo da previsão" | **Fora do fluxo.** `cm_estimator` existe só por compatibilidade (`RF-25`, `T-32`) |
| 🟢 | 🟡 | "6 ramos de aceitação" | São **5** ramos + o de prefixo + o rebaixamento por nome do meio |
| 🟢 | 🟢 | **Todas** as referências de linha das specs antigas | Apontavam para `analisador-genealogico/` e `reconstructed/`, que **deixaram de existir**. Reescritas contra `src/` |
| 🔴 | 🟢 | "`RF-14`: desempate determinístico é requisito novo" | **Continua requisito e continua NÃO implementado.** Renumerado para **`RF-26`** nesta rodada, com nota de herança preservada |

> ⚠️ **A renumeração do `RF-14` → `RF-26` é a única perda potencial de rastreabilidade desta rodada.** Ela está **declarada na própria spec** (`analise-dna/requirements.md`, bloco "Herança de numeração") e repetida em `tasks.md` (`T-31`) e `contracts.md` §8, para que quem procurar `RF-14` encontre a nota em vez do silêncio.

---

## Lacunas Pendentes 🔴

Consolidadas de todos os artefatos desta rodada. O detalhamento com pergunta correspondente está em `gaps.md`; as 16 perguntas para o usuário, em `questions.md`.

**A contagem consolidada está em `gaps.md` §8**, que é a fonte da verdade das lacunas. Resumo depois das 16 decisões:

| Severidade | Linhas | IDs distintos |
| --- | ---: | ---: |
| 🔴 Crítico | 1 | 3 |
| 🟠 Moderado | 8 | 9 |
| ⚪ Cosmético | 5 | 5 |
| **Total em aberto** | **14** | **17** |

**Fechadas nesta rodada: 16** — 3 por execução no código (`L-15`, `P-04`, `E-03`), 9 por decisão sua, 2 por verificação (`L-06`, `M-04`), mais `P-03` e `P-05` encaminhadas como requisito do alvo.

### A lacuna crítica que restou

**`L-16` / `M-03` / `P-02` — corrida entre requisições concorrentes.** O estado do GEDCOM é global de processo e é reescrito a cada requisição, enquanto o servidor atende com **4 threads**. Duas requisições simultâneas podem intercalar. A guarda de instância única impede dois **processos**, não duas **threads**.

**Você respondeu que nunca observou resultado cruzado** — o que rebaixa a probabilidade, mas **não fecha a lacuna**: o mecanismo é confirmado por leitura, e o alcance nunca foi medido. O uso single-user tende a não disparar a janela. Nenhuma mitigação no legado foi autorizada, porque o isolamento real pertence à Onda 3 (`P-01`).

> **Nenhuma das 14 lacunas em aberto depende de decisão sua.** São limitação da fonte (`L-18`), custo (`L-20`) e trabalho de rastreabilidade e teste (`X-*`, `CS-*`, `E-*`).

---

## Recomendações

- [ ] **Levar os 4 requisitos encaminhados ao próximo ciclo forward** (`_reversa_forward/`): persistir histórico (1), registrar o veredito do operador (2), restringir a lista de nomes (3) e validar o conteúdo do CSV (4). **Eles não estão em nenhum artefato de migração**, porque o pipeline de migração foi concluído em 2026-09-28 e está preservado sem regeneração.
- [ ] **Atualizar o `README.md`, que agora contradiz o pin.** Ele documenta o fluxo pelo interpretador **global**, e o oficial passou a ser o `.venv/`. Uma linha resolve — **não editei por ser documento seu**.
- [ ] **Priorizar a Onda 3 da migração para o isolamento entre usuários.** Por sua decisão (`P-01`), a ausência de autenticação é **omissão**, e a correção já está especificada na migração — não no legado.
- [ ] **Olhar a `number_format.py`: 53 % de cobertura, a pior do projeto.** É a autoridade de **todo** número exibido na tela, e o `BUG-20261004-EWSJ` (badge com ruído de ponto flutuante) nasceu exatamente ali. É o melhor candidato a teste dedicado.
- [ ] **Regerar `_reversa_docs/` e as matrizes de `_reversa_bugs/*/generated/`.** Ambas derivam de artefatos de 2026-09-30 e hoje descrevem código que não existe mais.
- [ ] **Promover o fuzz do `BUG-20260929-J6PQ` a teste permanente.** A evidência de 288 payloads combinados vive em arquivo de adendo, fora da suíte. O contrato de escape é a **única** defesa contra o diagrama inteiro deixar de renderizar.
- [ ] **Conferir o estado do repositório antes de commitar.** Esta rodada editou **5 arquivos do legado** (`matching.py`, `app.py`, `genetic_evidence.py`, `requirements.txt` e 2 arquivos de teste), todos por decisão sua registrada em `questions.md`. As 9 specs substituídas estão em `.reversa/snapshots/2026-10-05-pre-reextracao/`.

---

*Gerado pelo Reversa-Reviewer em 2026-10-05 (re-extração, nível completo).*

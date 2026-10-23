# Registro de Qualidade de Código (Reversa Refactor)

> GENERATED / MANAGED. Este README guarda as políticas do registro.
> As pastas de contexto e os artefatos de transformação nascem sob demanda.

## Políticas

- `control_mode`: gated
  - `gated` (padrão): leitura, análise, medição e prova de comportamento fluem sem aprovação. TODO passo que toca o código do projeto passa por gate com diff aprovado.
  - `supervised`: o agente pode aplicar transformações de baixo risco já provadas, avisando; alto risco continua com gate.
  - `autonomous`: aplica automaticamente o que estiver 🟢 e provado. Mesmo aqui têm gate obrigatório: remover código, alterar spec efetiva, enviar material a harness externo, operação destrutiva.
- `safety_net_policy`: require-characterization
  - `require-characterization` (padrão): transformação que altera estrutura ou lógica exige rede de segurança (testes existentes + caracterização) verde antes e depois.
  - `allow-unproven`: permite transformação sem rede, sempre rebaixada para 🔴 e marcada como sem prova mecânica no registro.

## Invariante do registro

Nenhuma transformação altera comportamento observável. O que não prova preservação, para no gate. Toda transformação aplicada é revertível pelo diff guardado.

## Estrutura

```
_reversa_refactor/
  README.md                         (este arquivo)
  <contexto>/                        (feature, módulo ou caso de uso)
    opportunities/                   (oportunidades detectadas, uma por arquivo)
    transformations/
      OPP-<data>-<sufixo>-<slug>/
        plan.html                    (relatório visual do plano, antes de tocar arquivo)
        safety-net/                  (testes de caracterização + resultado verde/vermelho)
        before-after/                (evidência: medição, prova de equivalência, prova de morte)
        CHG-NNN.diff                 (diffs aplicados, fonte de reversão)
        transformation.md            (registro conforme opportunity-schema.md)
    generated/                       (index e catalog regeneráveis, nunca editados à mão)
```

## Contextos deste projeto

| Contexto | Alvo principal | Oportunidades |
|----------|----------------|---------------|
| `analise-dna` | `src/application/dna_analysis.py`, `src/application/projecao_analise.py` e `src/core/` (Dna + 8 módulos) | 19 |
| `arquitetura-src` | `src/` inteiro: acoplamento, ciclos de pacote e duplicação | 4 |
| `busca-caminho` | `src/core/path_search.py` | 4 |
| `contrato-de-dados-src` | contrato dos dicionários de domínio e caminhos de importação | 2 |
| `documentacao-sdd` | desvio entre `_reversa_sdd/` e o código, criado pelas transformações de 2026-10-06 | 1 |
| `documentacao-do-projeto` | `README.md`: árvore de `src/` e descrição da arquitetura | 1 |
| `pacote-reconstructed` | árvore do pacote (histórico, já em `src/`) | 9 |
| `tela-de-entrada` | `src/app.py`: rotas web, assets, despacho de acoes, composicao e servidor | 6 |
| `upload-gedcom` | `src/parsers/`, `src/core/gedcom_state.py` e `src/app.py` | 3 (1 declined) |
| `verificacao-de-tipos` | `pyrefly.toml` e as anotações de tipo de `tests/` | 1 |

## Auditoria de 2026-10-06: as quatro configurações pedidas

A pedido do usuário, `src/` foi auditado contra quatro configurações: orientação a objeto, padrão
de projeto, alta coesão e baixo acoplamento. Linha de base medida nesta data:

| Verificação | Resultado |
|---|---|
| Suíte (`py -3.14 -m pytest -q`) | 164 passam, 15 erros de ambiente |
| Verificação de tipos (`py -3.14 -m pyrefly check src`) | 27 erros |

Os 15 erros de suíte são `PermissionError` do sandbox ao criar o diretório temporário do
`tmp_path`. Não são regressão: a causa e a contagem constam do `.reversa/soul.md` §5 e foram
reproduzidas nesta sessão antes e depois da transformação aplicada.

Diagnóstico:

| Configuração | Situação | Evidência medida |
|---|---|---|
| Orientação a objeto | ausente por decisão | zero `class` e zero `@dataclass` em `src/` (22 módulos, 3.473 linhas) |
| Padrão de projeto | ausente | nenhuma fábrica, repositório, estratégia ou injeção; o único padrão é o singleton de estado global |
| Alta coesão | parcial | excelente por pacote e módulo, ausente no nível de dado |
| Baixo acoplamento | ausente | 2 ciclos de import em nível de pacote e estado global importado por 9 módulos |

Resultado: 6 oportunidades novas (`#27` a `#32`). Duas foram aplicadas (`OPP-20261006-4KMB` e
`OPP-20261006-ULVW`), e as outras quatro ficam em `proposed`, porque orientação a objeto, padrão de
projeto e o tipo dos dados de domínio **não são refactor**: mudam comportamento observável e a
`_reversa_sdd/migration/paradigm_decision.md` já aloca essas decisões ao alvo, não ao legado.

### Efeito da `OPP-20261006-ULVW` no acoplamento

O ciclo `core/` ↔ `reporting/` foi **extinto** por injeção do resolvedor de domínio
(`src/core/diagram_domain.py`), sem mover nenhuma decisão de layout: `architecture.md` §3 proíbe
tirar de `reporting/` a decisão de como desenhar.

| Aresta | Antes | Depois |
|---|---|---|
| `reporting` → `core` | 3 | **0** |
| Ciclo `core/` ↔ `reporting/` | presente | **EXTINTO** |
| `parsers` → `core` | 3 | **2** |
| Ciclo `core/` ↔ `parsers/` | presente | **presente** (aresta 2 bloqueada por spec) |

**Pendência de documentação:** `_reversa_sdd/architecture.md` §3 e `c4-components.md` afirmam que
`reporting/mermaid_render.py` importa `core.family_navigation`, `core.path_finding` e
`core.gedcom_state`. Depois da `OPP-20261006-ULVW` isso é falso, e os dois artefatos precisam de
adendo.

### Por que o ciclo `core/` ↔ `parsers/` ficou meio aberto

A `OPP-20261006-LIGH` tinha duas arestas. A do `csv_ingest` foi resolvida movendo `norm_name` para
`src/utils/name_keys.py`. A do `gedcom_parser` **não é desacoplável por refactor**, e o bloqueio é de
spec, não de código:

| Artefato | O que fixa |
|---|---|
| `_reversa_sdd/upload-gedcom/design.md:33` | `load_gedcom_and_build_graph` **substitui o estado** e devolve `list[str]` |
| `_reversa_sdd/upload-gedcom/requirements.md:148` | a função mora em `src/parsers/gedcom_parser.py` |

Quebrar o ciclo exige que o parser deixe de instalar estado, o que **muda comportamento observável**
de uma função que a spec fixa. Isso pertence ao `/reversa-forward` com atualização da spec de
`upload-gedcom`, e a migração já aloca a correção ao alvo.

### Reconciliação do registro, também em 2026-10-06

Ao levantar as oportunidades em aberto, duas apareceram desatualizadas. Nenhuma das correções tocou
em código do projeto:

| Oportunidade | Problema encontrado | Ação |
|---|---|---|
| `OPP-20260929-EHNZ` (#10) | Os três arquivos do bloco `target` estão em `analisador-genealogico/reconstructed/`, raiz extinta em 2026-10-03 pela `OPP-20261003-FLAT`; o conteúdo é o mesmo acoplamento por variável global que a `OPP-20261006-3WR5` registra sobre os arquivos atuais | Marcada `declined`, com `superseded_by: OPP-20261006-3WR5`. O encaminhamento ao Forward (`BR-HUMANA-004`, `AMB-009`, `BR-DESCARTAR-002`), o vínculo com o `BUG-20260929-BJJH` e a exigência de caracterização de concorrência foram transportados para a oportunidade nova |
| `OPP-20261003-PAST` (#25) | O bloco `target` e a tabela apontavam para `src/reconstructed/...`, nível de pacote apagado pela `OPP-20261003-FLAT` | Alvos reescritos em 2026-10-06 e, na mesma data, a oportunidade foi **declinada** por decisão do usuário: ver a seção abaixo |

A relação entre a `OPP-20261003-PAST` e a `OPP-20261006-ESKO` também foi verificada: as superfícies
são disjuntas (a primeira renomeia arquivos, a segunda corrige o caminho de importação usado pelos
consumidores), com uma ressalva de ordem registrada na própria oportunidade.

Estado do registro depois da reconciliação: **33 oportunidades**, sendo **26 aplicadas**, **1
aplicada em parte** (`OPP-20261006-LIGH`, aresta restante no Forward), **3 declined** e **3 que
permanecem `proposed` por não serem roteáveis**: `OPP-20261003-INIT` contradiz a RN-01,
`OPP-20261006-YTSH` não é refactor, e `OPP-20261006-W4KD` está em caminho não liberado pela config.

### Pendência de documentação, agora com oportunidade própria

As transformações de 2026-10-06 tornaram **quatro afirmações** de `_reversa_sdd/` falsas, e criaram
**dois módulos** que nenhum artefato cita. Isso está registrado como `OPP-20261006-W4KD`, no contexto
`documentacao-sdd`.

O bloqueio é de política: a config não libera `_reversa_sdd/**`, e os dois alvos principais foram
testados contra a lista e **recusados**. Três caminhos ficam ao usuário: liberar o glob e rotear a
`/reversa-standardize`; registrar um **adendo**, como o `addenda/003-renomear-pasta-app-para-src.md`
já faz para as transformações de 2026-10-03; ou nova re-extração.

A afirmação mais consequente é a de `architecture.md:73`: ela diz que `reporting/` "não é folha, e
não pode ser", e é dela que sai a conclusão de que há decisão de negócio na apresentação. Depois da
`OPP-20261006-ULVW`, a decisão de layout **continua** em `reporting/`, mas o renderizador **não
navega mais o domínio por importação**. Uma spec que afirma só a primeira parte leva o
reimplementador a desenhar a fronteira errada.

### As três declinadas, e por que o motivo importa

| Oportunidade | Motivo medido |
|---|---|
| `OPP-20260929-EHNZ` (#10) | Alvos em raiz extinta desde 2026-10-03, e conteúdo duplicado pela #27 |
| `OPP-20261003-PAST` (#25) | Renomeações com alcance de 89 ocorrências em 18 arquivos, perda de precisão nos nomes de módulo e quebra de uma sonda de bug, sem ganho funcional |
| `OPP-20261006-3WR5` (#27) | Comportamento fixado pela spec de `upload-gedcom`, mitigação no legado **nunca autorizada** (`questions.md:262-264`) e isolamento alocado à Onda 3, que já descarta o mecanismo |

O padrão das duas últimas é o mesmo: o legado resolveu o problema **por descarte na migração**, não
por conserto. Propor a correção aqui contradiz decisões vigentes registradas pelo próprio usuário.

### A `OPP-20261003-PAST` foi declinada em 2026-10-06

Ela propunha renomear `parsers/` para `parser/`, `reporting/` para `generator/`, `gedcom_state.py`
para `state.py` e `dna_analysis.py` para `analyzer.py`, para alinhar ao exemplo de árvore do usuário.
A medição da véspera da aplicação contradisse a estimativa de custo `low`:

| Item | Estimativa de 2026-10-03 | Medição de 2026-10-06 |
|---|---|---|
| Alcance | duas linhas de import por arquivo | **89 ocorrências em 18 arquivos** |
| `_reversa_bugs/` | não previsto | uma sonda de bug importa dois dos alvos |
| Ganho | alinhamento ao exemplo | nenhum ganho funcional |

Três motivos para a recusa: os dois nomes de módulo propostos **perdem informação**
(`gedcom_state.py` diz que estado é; `state.py` não), a renomeação **quebraria a sonda do
`BUG-20261004-EWSJ`** que não está em caminho liberado, e não há ganho funcional em mover 18
arquivos. `parser/` no singular era o único item neutro.

Nada foi renomeado. O registro com a medição completa está na própria oportunidade.

## Lote de 2026-10-23: analise-dna e tela-de-entrada

Duas frentes foram abertas no mesmo dia. A de `analise-dna` fechou; a de
`tela-de-entrada` parou de madrugada com o código aplicado e o registro pela
metade. Em ambos os casos o código estava correto e a suíte verde; o que faltava
era o registro.

| # | Oportunidade | Contexto | Verbo | Estado | Efeito medido |
|---|---|---|---|---|---|
| #35 | `OPP-20261023-MPRA` | analise-dna | modularize | **applied** | `dna_analysis.py` 345 → 128 linhas; `projecao_analise.py` novo com 293 |
| #36 | `OPP-20261023-CLSM` | analise-dna | restructure | **applied** | classe `ProjetorDeAnalise` (Mapper), com fachada funcional preservada |
| #37 | `OPP-20261023-DONO` | analise-dna | standardize | **applied** | docstring do `dono` alinhada ao ADR-26; **prune recusado** |
| #38 | `OPP-20261023-KITS` | analise-dna | simplify | **applied** | `_kits` com `zip_longest` e fatia, sem lista mutável |
| #39 | `OPP-20261023-DISP` | tela-de-entrada | restructure | **applied** | `index()` 234 → 19 linhas; 5 handlers e dois mapas de ação |
| #40 | `OPP-20261023-ASST` | tela-de-entrada | modularize | **applied** | Blueprint `assets_bp` em `src/web/rotas_assets.py`; `app.py` 888 → 737 |
| #43 | `OPP-20261023-DEAD` | tela-de-entrada | prune | **applied** | guarda inalcançável unificada; checagem mantida para estreitar tipo |
| #41 | `OPP-20261023-SERV` | tela-de-entrada | decouple | **declined** | `tests/test_servidor_producao.py` exige o bloco de servidor no AST de `app.py` |
| #42 | `OPP-20261023-FACT` | tela-de-entrada | modularize | **applied** | `create_app(config=None)` com 6 testes; suite 1621 passed, 9 skipped |
| #44 | `OPP-20261023-ESTD` | tela-de-entrada | decouple | **applied** | estado de borda injetável: 10 leituras de global em handlers viraram 0; 4 testes novos |
| #45 | `OPP-20261023-RDME` | documentacao-do-projeto | standardize | **applied** | README alinhado: 54 arquivos na árvore, 0 faltando; suíte 1625/9 |

### O que a conciliação corrigiu

| Constatação | Correção |
|---|---|
| `DISP` aplicada no código, marcada `proposed` e sem `transformation.md` | Registro escrito, estado corrigido, diff real gerado |
| o `proposed.diff` de `DISP` era um esboço com `...` e não aplicava | Removido e substituído por `CHG-001-despachador-de-acoes.diff` (471 linhas) |
| nenhuma das sete tinha diff de reversão, embora os índices dissessem "sim" | Seis diffs gerados do `HEAD 221b6c1` e verificados por aplicação em cadeia |
| os arquivos de suíte declaravam `Python 3.12.3`, `pytest 8.3.2` e `pyproject.toml`, que o projeto não tem | Substituídos pela medição real nas duas pontas do lote |
| `MPRA` dizia "suite rodando em background" e "preservado" ao mesmo tempo | Registro reescrito com a medição real |
| `DONO` estava como `prune` aplicado, sem poda e sem `death-proof` | Verbo corrigido para `standardize`; recusa do prune registrada |
| a prova de equivalência de `KITS` estava errada para `avaliacoes` mais longa | Corrigida: a fatia `avaliacoes[:len(kits)]` é o que preserva o truncamento |
| a extração de `ASST` deixou `build_only`, re-exportações sem efeito e `import json` sem uso | Removidos; o template usa `url_for('assets.descartes_em_csv')` |

O diff do lote de `analise-dna` é **único** (`CHG-LOTE-extracao-e-mapper.diff`,
586 linhas): as quatro etapas foram empilhadas antes de qualquer captura, e os dois
arquivos só são reproduzidos pelo conjunto. A reversão é em bloco e foi verificada
aplicando o diff sobre o `HEAD`: os dois arquivos saem byte a byte iguais aos
atuais. No `tela-de-entrada`, os diffs são por transformação
(`CHG-001` de DEAD, três de ASST, `CHG-001` de DISP), e a cadeia DEAD → ASST → DISP
reproduz o `app.py` atual byte a byte.

### Medição real do lote

| Momento | Resultado |
|---|---|
| linha de base `HEAD 221b6c1` (cópia limpa via `git archive`) | **1615 passed, 9 skipped** em 190,29 s |
| working tree depois do lote e da limpeza | **1615 passed, 9 skipped** em 197,00 s |
| verificação de tipos | **não medida**: `pyrefly` não está instalado no `.venv` |

Evidência: `tela-de-entrada/generated/evidence/` e `analise-dna/generated/evidence/`,
copiada para o `before-after/` de cada transformação.

### FACT, aprovada depois do fechamento

A `OPP-20261023-FACT`, que estava `proposed`, foi aprovada em plano e em diff e
aplicada no mesmo dia. `create_app(config=None)` existe em `src/app.py`, o app de
módulo é criado por ele, e `tests/test_fabrica_do_app.py` acrescenta 6 testes. A
suíte foi de 1615 para **1621 passed, 9 skipped**, com as mesmas 9 exclusões.

O limite declarado no plano continua valendo: a fábrica isola **configuração**,
não o estado de borda (`_ARMAZENAMENTO`, `_CARREGADOR`, `_REGISTRO`). Isolar isso
é `decouple`, e fica para outra oportunidade.

### ESTD, o isolamento de estado

A `OPP-20261023-ESTD` foi aberta na sequência para fechar esse limite e foi
aprovada e aplicada no mesmo dia. `create_app` passou a aceitar `armazenamento`,
`carregador`, `registro` e `dependencias` como parâmetros keyword-only, guardados
em `extensions["analisador"]`; as 10 leituras de global em handlers viraram 0. A
suíte foi de 1621 para **1625 passed, 9 skipped**, com 4 testes novos.

A independência das quatro é deliberada: injetar só `armazenamento` não reconstrói
o `carregador`, que continua apontando para o armazenamento real. Um teste de
upload totalmente isolado injeta os dois.

### RDME, o README de volta ao código

A `OPP-20261023-RDME` fechou a defasagem que a FACT e a ESTD criaram. A árvore do
README passou a listar os 54 arquivos conferidos, com `src/web/`,
`projecao_analise.py` e os cinco módulos de `core/` que faltavam; a contagem passou
a declarar o método e a data. A suíte continuou em **1625 passed, 9 skipped**,
porque só documentação mudou.

### ORQA, CTAO e DOCF: a auditoria de `core/dna_analysis.py`

Na mesma data, um segundo pedido mirou **um arquivo**: verificar orientação a objeto,
padrão de projeto, alta coesão e baixo acoplamento em `src/core/dna_analysis.py`,
achar função sem utilidade, limpar o código e dividir em módulos menores se possível.
O arquivo tem **1.108 linhas**. A medição respondeu:

| Configuração | Situação | Evidência |
|---|---|---|
| Orientação a objeto | 🟡 parcial | uma classe (`Dependencias`, Parameter Object); o núcleo já usa `@dataclass(frozen=True, slots=True)` em `core/endogamia.py` |
| Padrão de projeto | 🟡 parcial | Parameter Object e Facade; a Fachada é o único padrão sem consumidor interno |
| Alta coesão | 🔴 baixa no módulo | cinco razões para mudar; oito das dez funções têm 61 linhas ou menos |
| Baixo acoplamento | 🟡, com um ponto 🔴 | 56 nomes de 21 módulos; `Dependencias` é consumida por `core/path_search.py` sem dono |

A função sem utilidade que o pedido procurava **não existe**: as 10 funções e a classe
têm chamador. O peso morto é outro, e está medido: um docstring órfão de 14 linhas
dentro de `dna_analysis` (expressão de string, avaliada e descartada) e `DNAAnalyzer`
declarado em `__all__` sem nenhum consumidor no projeto.

| # | ID | Verbo | Custo | Efeito esperado |
|---|---|---|---|---|
| #46 | `OPP-20261023-ORQA` | restructure | medium | **aplicada em 2026-10-23**: `dna_analysis` de 539 para 205 linhas |
| #47 | `OPP-20261023-CTAO` | modularize | medium | **aplicada em 2026-10-23**: oito módulos de 43 a 470 linhas |
| #48 | `OPP-20261023-DOCF` | prune | low | **aplicada em 2026-10-23**: 1.108 → 1.094 linhas, suíte 1625/9 |
| #49 | `OPP-20261023-ETAP` | restructure | medium | **aplicada em 2026-10-23**: `_cartao_do_kit` de 368 para 224 linhas |
| #50 | `OPP-20261023-UNCA` | restructure | low | **aplicada em 2026-10-23**: as 40 chaves do cartão declaradas uma vez e guardadas por teste |

Duas recusas ficaram registradas na própria `DOCF`, com a medição: a fachada de 12
imports sem uso tem consumidor em instrumentos congelados de `_reversa_sdd/parity/`
(caminho não liberado pela config), e `Dependencias.aggregate_matches` é argumento
posicional obrigatório de 34 chamadores em `_reversa_bugs/`, também fora dos globs.
Nenhuma das duas foi roteada. **A `DOCF` e a `ORQA` foram aplicadas** em 2026-10-23,
cada uma sob gate de plano e de diff. A `DOCF` levou o módulo de 1.108 para 1.094
linhas. A `ORQA` levou `dna_analysis` de **539 para 205 linhas**, com o passo por kit
em `_cartao_do_kit` e o estado em `_ContextoDaAnalise`; a suíte ficou em **1625
passed, 9 skipped** (108,78 s), e o digest de equivalência seguiu idêntico.

A `ORQA` quebrou uma guarda textual em `tests/test_profundidade_do_caminho.py`, que
prendia a chamada literal `documental_nao_encontrado(arvore, root_id, pid`. O diff
foi revertido, a guarda virou verificação por AST e os dois diffs entraram juntos.
A decomposição interna que sobrou virou a `OPP-20261023-ETAP` (#49), aplicada na
sequência: `_cartao_do_kit` caiu de 368 para **224 linhas**, com seis etapas
nomeadas. Fechando a auditoria, a `CTAO` (#47) dividiu o arquivo em **oito módulos**
de 43 a 470 linhas; `dna_analysis.py` caiu de 1.258 para **321 linhas**.

A `CTAO` também quebrou dois testes que apontavam para o arquivo antigo, e o mesmo
procedimento valeu: diff revertido, correções separadas em `CHG-002`, nenhuma
asserção afrouxada. Um teste mudou de arquivo lido, o outro de módulo patcheado.

Com isso a auditoria de `src/core/dna_analysis.py` está fechada: 1.108 linhas em um
arquivo viraram 1.363 em oito, com o mesmo comportamento provado por um digest
sha256 que atravessou as transformações sem mudar um byte.

A `UNCA` (#50) fechou a última consequência do corte: o contrato de 40 chaves do
cartão passou a ser declarado uma vez em `src/core/contrato_do_cartao.py` e guardado
por dois testes que comparam o conjunto de cada construtor. Os testes nasceram
verdes, provando que os dois construtores já respeitavam o contrato; o que faltava
era alguém avisar no dia em que um lado mudasse sem o outro.

## Gate de edição do legado: LIBERADO em 2026-09-29

`.reversa/reversa-config.json` está em `allowLegacyEdits: true`. Os globs liberados evoluíram por
edição do próprio usuário, e hoje são dezessete:
`["analisador-genealogico/**", "tests/**", "README.md", "pyrefly.toml", "publicar_docs.py", "src/**", ".vscode/**", "requirements.txt", ".markdownlint-cli2.jsonc", "_docs_auxiliary/**", "docker/**", "docker-compose.yml", "init.sql", ".dockerignore", "docs/**", "*.ps1", ".github/**"]`.

As **42 oportunidades aplicadas** estão listadas abaixo; o lote de 2026-10-03 (sete
transformações) e o de 2026-10-23 (dezesseis, contando FACT, ESTD, RDME, DOCF, ORQA,
ETAP, CTAO, UNCA e GRDA) ocupam uma linha cada.
| Oportunidade | Verbo | Arquivo | Estado |
|--------------|-------|---------|--------|
| `OPP-20260929-TPSH` | restructure | `reconstructed/path_search.py` | aplicada |
| `OPP-20260929-AU76` | optimize | `reconstructed/dna_analysis.py` | aplicada |
| `OPP-20260929-32Q7` | prune | `reconstructed/dna_analysis.py` | aplicada, empilhada sobre a AU76 |
| `OPP-20260929-SEQO` | prune | `app.py`, `requirements.txt` | aplicada |
| `OPP-20260929-B5F2` | modularize | `reconstructed/domain.py`, `reconstructed/dna_analysis.py` | aplicada |
| `OPP-20260929-4LE3` | modularize | executada dentro da B5F2, sem transformação própria | aplicada |
| `OPP-20260929-4MGR` | optimize | `reconstructed/dna_analysis.py` | aplicada |
| `OPP-20260929-IM3Q` | prune | `requirements.txt` | aplicada |
| `OPP-20260929-DW3U` | prune | `reconstructed/domain.py` | aplicada, opção B |
| `OPP-20260929-U2NK` | prune | `reconstructed/dna_analysis.py` | aplicada |
| `OPP-20260929-Z6IO` | prune | `pyrefly.toml`, seis arquivos de `tests/` | aplicada |
| `OPP-20260929-5XGJ` | standardize | `reconstructed/path_search.py` | aplicada em 2026-10-01 |
| `OPP-20260929-NUMT` | optimize | `reconstructed/dna_analysis.py` | aplicada em 2026-10-01 |
| `OPP-20260929-ZV52` | modularize | `reconstructed/{name_normalization,csv_ingest,matching}.py` novos, `dna_analysis.py` reduzido | aplicada em 2026-10-01 |
| `OPP-20260929-UXEF` | modularize | `reconstructed/{family_navigation,path_finding,mermaid_render}.py` novos, `path_search.py` reduzido | aplicada em 2026-10-01 |
| `OPP-20260929-H2YY` | simplify | `reconstructed/mermaid_render.py` | aplicada em 2026-10-01 |
| `OPP-20261003-TWNT` a `OPP-20261003-FLAT` | modularize, decouple, standardize | árvore do pacote: `src/core/`, `src/parsers/`, `src/reporting/`, `src/utils/` | 7 aplicadas em 2026-10-03 |
| `OPP-20261006-4KMB` | restructure | `src/app.py` | aplicada em 2026-10-06 |
| `OPP-20261006-ULVW` | decouple | `src/reporting/mermaid_render.py`, `src/core/path_search.py`, `src/core/dna_analysis.py` e `src/core/diagram_domain.py` (novo) | aplicada em 2026-10-06 |
| `OPP-20261006-LIGH` | decouple | `src/utils/name_keys.py` (novo), `src/core/name_normalization.py`, `src/parsers/csv_ingest.py` | aplicada em parte em 2026-10-06; aresta restante bloqueada por spec |
| `OPP-20261006-ESKO` | standardize | `src/core/path_search.py`, `tests/test_path_search.py`, `tests/test_mermaid_escape.py` e `_reversa_sdd/parity/harness.py` | aplicada em 2026-10-06 |
| `OPP-20261023-MPRA` a `OPP-20261023-DISP` | modularize, restructure, simplify, standardize, prune | `src/application/{dna_analysis,projecao_analise}.py`, `src/app.py`, `src/web/rotas_assets.py` (novo) e `src/templates/index.html` | 7 aplicadas em 2026-10-23 |
| `OPP-20261023-FACT` | modularize | `src/app.py` (`create_app`) e `tests/test_fabrica_do_app.py` (novo) | aplicada em 2026-10-23 |
| `OPP-20261023-ESTD` | decouple | `src/app.py` e `tests/test_estado_de_borda_injetavel.py` (novo) | aplicada em 2026-10-23 |
| `OPP-20261023-RDME` | standardize | `README.md` | aplicada em 2026-10-23 |
| `OPP-20261023-DOCF` | prune | `src/core/dna_analysis.py` | aplicada em 2026-10-23 |
| `OPP-20261023-ORQA` | restructure | `src/core/dna_analysis.py` e `tests/test_profundidade_do_caminho.py` | aplicada em 2026-10-23 |
| `OPP-20261023-ETAP` | restructure | `src/core/dna_analysis.py` | aplicada em 2026-10-23 |
| `OPP-20261023-CTAO` | modularize | `src/core/` (sete módulos novos), `src/core/dna_analysis.py`, `tests/test_profundidade_do_caminho.py` e `tests/test_veredito_no_nucleo.py` | aplicada em 2026-10-23 |
| `OPP-20261023-UNCA` | restructure | `src/core/contrato_do_cartao.py` (novo) e `tests/test_contrato_do_cartao.py` (novo) | aplicada em 2026-10-23 |
| `OPP-20261023-GRDA` | standardize | `tests/test_uso_do_cm_estimator.py` (novo) | aplicada em 2026-10-23 |

Nenhuma delas escreveu fora dos globs liberados na época. `tests/**` passou a ser usado na
`OPP-20260929-Z6IO`, que removeu seis supressões de tipo obsoletas. Promover as redes de segurança por
caracterização e equivalência a teste permanente da suíte continua sendo decisão do usuário.

## Rede de segurança disponível

Números medidos em **2026-10-23**, no ambiente oficial (`.venv`, Python 3.14.6,
pytest 9.1.1, `pytest.ini`):

- Suíte no `HEAD 221b6c1` (cópia limpa via `git archive`): **1615 passed, 9 skipped**, 190,29 s.
- Suíte no working tree depois do lote de 2026-10-23 e da limpeza: **1615 passed, 9 skipped**, 197,00 s.
- Suíte depois da FACT (`create_app` + 6 testes): **1621 passed, 9 skipped**, 294,19 s.
- Suíte depois da ESTD (estado injetável + 4 testes): **1625 passed, 9 skipped**, 157,14 s.
- Verificação de tipos: **não medida**, porque o `pyrefly` não está instalado no `.venv`
  (`No module named pyrefly`). Os 27 erros de 2026-10-06 vieram de outro ambiente e não
  servem de critério hoje.
- Evidência: `tela-de-entrada/generated/evidence/suite-lote-antes.txt` e
  `suite-lote-depois.txt`.

Números históricos, mantidos para rastreabilidade e **substituídos** pela medição acima:

- Suíte existente em 2026-10-06: **164 testes passam e 15 erros de ambiente** em `tests/` (`py -3.14 -m pytest -q`). Os 15 erros são `PermissionError` do sandbox ao criar o diretório temporário do `tmp_path`, e não regressão: o mesmo número e a mesma causa aparecem antes e depois de cada transformação.
- **Suíte remedida em 2026-10-08**, no contexto da `OPP-20261008-JXQN`: **282 passam, 8 pulados, 0 erros e 0 falhas**, em 290 itens coletados, com 173 s de execução. Os 15 erros de ambiente de 2026-10-06 **não existem mais**: a correção do `tmp_path` feita pela feature 007 os eliminou. Os 8 pulados são os 8 testes de `tests/test_registro_de_analises.py`, pulados por ausência de `DATABASE_URL`. Evidência bruta: `analise-dna/transformations/OPP-20261008-JXQN-legado-de-cm-fora-do-fluxo/before-after/suite-antes.txt`.
- Verificação de tipos em 2026-10-06: `py -3.14 -m pyrefly check src` reportava **27 erros**, em outro ambiente.
- Harness de paridade diferencial oráculo x reconstrução: `_reversa_sdd/parity/harness.py`, com
  fixtures sintéticas em `_reversa_sdd/parity/fixtures/`. Roda e reporta 100 por cento, ao
  contrário do que este README afirmava antes de 2026-10-03.
- Linha de base congelada antes da aplicação: `.pytest-tmp/baseline/` (fora do versionamento), usada
  como variante A nas provas de equivalência.
- Medição: todo `optimize` registra antes e depois. Os scripts de medição e de equivalência ficam
  junto de cada transformação, e aceitam `VARIANT_A_DIR` e `VARIANT_B_DIR` para comparar duas
  variantes arbitrárias do pacote.

---
*Gerado pelo Reversa-Refactor em 2026-09-29. Auditoria de arquitetura, contextos e linha de base atualizados em 2026-10-06.*

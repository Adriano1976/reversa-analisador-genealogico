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
| `analise-dna` | `src/core/dna_analysis.py` e dependências | 9 |
| `arquitetura-src` | `src/` inteiro: acoplamento, ciclos de pacote e duplicação | 4 |
| `busca-caminho` | `src/core/path_search.py` | 4 |
| `contrato-de-dados-src` | contrato dos dicionários de domínio e caminhos de importação | 2 |
| `documentacao-sdd` | desvio entre `_reversa_sdd/` e o código, criado pelas transformações de 2026-10-06 | 1 |
| `pacote-reconstructed` | árvore do pacote (histórico, já em `src/`) | 9 |
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

## Gate de edição do legado: LIBERADO em 2026-09-29

`.reversa/reversa-config.json` está em `allowLegacyEdits: true`. Os globs liberados evoluíram por
edição do próprio usuário, e hoje são oito:
`["analisador-genealogico/**", "tests/**", "README.md", "pyrefly.toml", "src/**", ".vscode/**", "requirements.txt", ".markdownlint-cli2.jsonc"]`.

As **25 oportunidades aplicadas** estão listadas abaixo em 18 linhas: o lote `OPP-20261003-*` de sete
transformações ocupa uma linha só.
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

Nenhuma delas escreveu fora dos globs liberados na época. `tests/**` passou a ser usado na
`OPP-20260929-Z6IO`, que removeu seis supressões de tipo obsoletas. Promover as redes de segurança por
caracterização e equivalência a teste permanente da suíte continua sendo decisão do usuário.

## Rede de segurança disponível

Números medidos em **2026-10-06** (substituem os de 2026-09-29):

- Suíte existente: **164 testes passam e 15 erros de ambiente** em `tests/` (`py -3.14 -m pytest -q`). Os 15 erros são `PermissionError` do sandbox ao criar o diretório temporário do `tmp_path`, e não regressão: o mesmo número e a mesma causa aparecem antes e depois de cada transformação.
- **Suíte remedida em 2026-10-08**, no contexto da `OPP-20261008-JXQN`: **282 passam, 8 pulados, 0 erros e 0 falhas**, em 290 itens coletados, com 173 s de execução. Os 15 erros de ambiente de 2026-10-06 **não existem mais**: a correção do `tmp_path` feita pela feature 007 os eliminou. Os 8 pulados são os 8 testes de `tests/test_registro_de_analises.py`, pulados por ausência de `DATABASE_URL`. **A verificação de tipos não foi remedida nesta data**, e os 27 erros do pyrefly continuam sendo o número de 2026-10-06. Evidência bruta: `analise-dna/transformations/OPP-20261008-JXQN-legado-de-cm-fora-do-fluxo/before-after/suite-antes.txt`.
- Verificação de tipos: `py -3.14 -m pyrefly check src` reporta **27 erros**. O critério de aceite de qualquer transformação é a contagem e o conjunto de erros não aumentarem, comparados arquivo a arquivo.
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

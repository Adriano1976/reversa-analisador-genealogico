---
schema_version: 1
id: OPP-20261008-JXQN
display_number: 34
context: analise-dna
verb: prune
title: Legado de cM fora do fluxo, sem consumidor de produção
target:
  files: [src/core/cm_estimator.py, tests/test_dna_analysis.py]
  symbol: SHARED_CM_DATA, get_relationships_by_cm
smell: módulo sem nenhum consumidor de produção, mantido por dois consumidores de verificação, um deles carregado por string
roi:
  confidence: green
  impact: fecha a defesa textual do ADR-19 (as faixas continuam alcançáveis por importação) e a dívida #18, tirando do pacote 65 linhas de heurística já retirada do fluxo, sem tocar em comportamento algum
  cost: low
  est_return: 65 linhas e 2 testes a menos de heurística aposentada, com a defesa contra uso indevido passando de textual para estrutural
state: proposed
promoted_to: null
traceability:
  soul: [.reversa/soul.md#d2-núcleo-de-domínio-em-pacotes-por-responsabilidade-sob-uma-camada-de-rota-fina, .reversa/soul.md#4-lacunas]
  specs: [_reversa_sdd/analise-dna/requirements.md#RF-25, _reversa_sdd/analise-dna/tasks.md#T-32, _reversa_sdd/adrs/19-heuristicas-declaradas-como-heuristicas.md, _reversa_sdd/architecture.md, _reversa_sdd/code-analysis.md]
---

## Antes observado

`src/core/cm_estimator.py` tem 65 linhas e 3.432 bytes. Contém duas coisas: a tabela
`SHARED_CM_DATA` nas linhas 40 a 50 (nove faixas de cM escritas à mão, sobrepostas até quatro
vezes, sem fonte externa verificável) e a função `get_relationships_by_cm` nas linhas 53 a 65, que
traduz um valor de cM na lista de relações daquela faixa.

O próprio módulo declara o que é, na primeira linha do docstring: **"Estimador de parentesco por
faixas de cM, LEGADO, fora do fluxo"**, com "não usar em código novo". O ADR-19 o rebaixou a legado
em 2026-10-04 e a `T-32` retirou as faixas do fluxo.

A medição de 2026-10-08 confirma o quadro e acrescenta um detalhe que a documentação não registra.

### Consumidores, por varredura do repositório inteiro

| Consumidor | Como alcança | Vivo? |
|---|---|---|
| `tests/test_dna_analysis.py:31` | `from core.cm_estimator import get_relationships_by_cm` | Sim, é a suíte |
| `_reversa_sdd/parity/harness.py:266` | import **dentro da string** `CANDIDATE_COLLECTOR`, usada na linha 339 como `safo(_cm_rel, cm)` | Sim, é o harness diferencial |
| `_reversa_forward/005-nucleo-puro-src/evidence/_verificar_t029.py:193` | import dentro de função, numa sonda de evidência do ciclo forward | Não é suíte nem harness, é evidência datada |
| `src/` inteiro | nenhum import | **zero** |
| `src/core/dna_analysis.py:27` | só cita o módulo em docstring, para contar que a reexportação saiu na `T022` | Não é referência de código |
| `_reversa_sdd/oracle/app_legacy_e43ca22.py:169` | define a **própria** cópia de `get_relationships_by_cm` | Não importa nada do candidato |

### Duas correções ao registro vigente

1. **O `RF-25` está desatualizado em metade da sua redação.** Ele diz "reexportado só por
   compatibilidade", e isso deixou de valer na `T022`: `src/core/dna_analysis.py:287-293` lista o
   `__all__` e **não** traz mais `get_relationships_by_cm` nem `SHARED_CM_DATA`. A outra metade do
   requisito ("não é importado por nenhum caminho de produção nem pela interface") continua
   verdadeira e foi reconfirmada agora.
2. **A dependência do harness não é um import comum.** Ela vive dentro de
   `CANDIDATE_COLLECTOR = r'''...'''` (`harness.py:254`), um coletor que o harness escreve em
   disco e executa como processo separado. Uma varredura por AST em `harness.py` **não enxerga**
   essa linha; só a varredura textual do arquivo a encontra. O mesmo vale para o lado do oráculo,
   que calcula `obs["cm"]` na linha 134 a partir da cópia congelada.

## Prova de morte

O verbo `prune` exige duas condições. A segunda se cumpre; a primeira **não**.

**Condição 1, sem referência estática: FALHA.** Existem dois consumidores vivos, a suíte e o
harness de paridade. A remoção do módulo quebra os dois, e é exatamente o que o ADR-19 registrou
como motivo para não removê-lo em 2026-10-04.

**Condição 2, sem entrada dinâmica: cumprida no módulo.** `src/core/cm_estimator.py` não contém
`globals()`, `getattr`, `__import__`, `importlib`, `eval`, `exec`, rota, configuração nem feature
flag. É uma lista e uma função puras, com `isinstance` como única operação sobre o valor de
entrada. Não há como religá-lo por nome.

**A tensão que a condição 2 revela:** a entrada que mantém o módulo vivo é, ela mesma, uma entrada
por código gerado. O harness monta o coletor como texto e o executa, de modo que a referência a
`core.cm_estimator` não é verificável por análise estática do arquivo. É o caso que a própria
doutrina do `prune` manda tratar como órfão suspeito, e não como morto.

## Classificação

**Órfão suspeito**, com `promoted_to: null`. Não é elegível para remoção enquanto as duas condições
não forem satisfeitas ao mesmo tempo, e a primeira depende de uma decisão que não é de código.

### A trava da alma

A conferência contra a alma encontrou um bloqueio real, e ele precisa estar declarado antes de
qualquer plano:

| Locator | O que ele fixa |
|---|---|
| `.reversa/soul.md#4-lacunas` | "a declaração das faixas de cM como heurística" é **decisão vigente**, não lacuna |
| `.reversa/soul.md#d2-...` | registra o `cm_estimator` como "legado mantido fora do fluxo apenas porque a suíte e o harness o exercitam" |
| `_reversa_sdd/analise-dna/requirements.md#RF-25` | requisito vivo (`Should`) que manda declarar o módulo como legado fora do fluxo |
| `_reversa_sdd/analise-dna/tasks.md#T-32` | a tarefa que produziu o estado atual, com critério de pronto explícito |
| `_reversa_sdd/adrs/19` | decisão aceita e vigente, que já descartou a remoção completa uma vez |
| `_reversa_sdd/code-analysis.md:306` | **`BR-D-62`**, regra de negócio catalogada como 🟢, que descreve a mecânica de `get_relationships_by_cm` |
| `_reversa_sdd/architecture.md:154` | dívida técnica #18: o módulo segue no repositório com faixas sem fonte verificável |

A regra da alma é dura: **código que implementa uma regra de negócio confirmada nunca é tratado
como morto**. `BR-D-62` é uma regra catalogada e confirmada na extração de 2026-10-05, e o módulo é
o único lugar onde ela vive. Remover o módulo **apaga uma regra catalogada e um requisito vivo**
(`RF-25`), o que é alteração de spec efetiva, e alteração de spec efetiva tem gate obrigatório e
pertence ao `/reversa-forward`, não ao `prune`.

## Veredito do podador (2026-10-08)

Fluxo executado até o gate. **Nada foi removido.** A classificação registrada é **órfão suspeito**,
com `promoted_to: null`, e a oportunidade permanece `proposed`.

### A prova de morte, medida

| Item | Resultado |
|---|---|
| Varredura | repositório inteiro, 551 ocorrências em 147 arquivos, sem amostra |
| Natureza das ocorrências | decidida por `tokenize`, com granularidade de **coluna**, e não de linha |
| Código executável | 51 ocorrências, das quais **8** no alvo ou no instrumento vivo: 3 definições em `src/core/cm_estimator.py` e 5 usos em `tests/test_dna_analysis.py` |
| Dentro de literal de string | 66 ocorrências, incluindo as **duas que importam**: `harness.py:266` e `harness.py:339` |
| Em comentário | 2 ocorrências (`tests/test_dna_analysis.py:28` e `:29`) |
| Fora de Python | 432 ocorrências, em documentação e artefatos datados |

Artefatos: `transformations/OPP-20261008-JXQN-legado-de-cm-fora-do-fluxo/before-after/medir-usos.py`
(a medição, reexecutável) e `before-after/prova-de-uso.txt` (a saída bruta).

### As duas condições

1. **Sem referência estática: FALHA.** `tests/test_dna_analysis.py:31` é um `import` que o
   interpretador executa, e as linhas 286, 287, 288 e 302 usam a função de fato.
2. **Sem entrada dinâmica: FALHA.** `_reversa_sdd/parity/harness.py:266` está dentro da string
   `CANDIDATE_COLLECTOR` (`harness.py:254`), que o harness escreve em disco e executa como processo
   separado. É carregamento por string, o caso em que a doutrina manda elevar o rigor.

Dentro do próprio módulo, a condição 2 se cumpre: zero `globals()`, `getattr`, `__import__`,
`importlib`, `eval` ou `exec`.

### O que a varredura corrigiu

A varredura do repositório inteiro mostrou que a dependência do harness é **invisível para análise
estática de AST**: a linha 266 não é um import de `harness.py`, é texto dentro de uma string. Uma
medição por AST teria concluído, erradamente, que o único consumidor era o teste.

### O que não foi gerado, e por quê

Não existe `CHG-NNN.diff` e não existe `transformation.md`. O verbo `prune` só gera remoção para o
que for provado morto, e o conjunto de remoções é vazio. O schema da transformação admite apenas
`state: applied` ou `reverted`, e registrar qualquer um dos dois aqui seria afirmar um fato que não
aconteceu. O plano e a prova ficam em `transformations/OPP-20261008-JXQN-legado-de-cm-fora-do-fluxo/`,
e o detalhe visual em `plan.html`.

## Transformação proposta, se a decisão humana for aposentar a superfície

Nada será aplicado nesta rodada. O plano do podador só pode ser escrito depois de a decisão abaixo
existir, porque ela muda o conjunto de arquivos.

**Decisão que falta: a superfície de verificação vai junto ou não?**

| Cenário | Arquivos | Consequência |
|---|---|---|
| A. Aposentar módulo, suíte e o campo `cm` da paridade | `src/core/cm_estimator.py` (removido), `tests/test_dna_analysis.py` (33 linhas), `_reversa_sdd/parity/harness.py` (campo `cm` nos dois coletores) | Fecha a dívida #18 e o risco residual do ADR-19, mas **exige editar `_reversa_sdd/**`, que não está liberado**, e anular `RF-25`/`BR-D-62` por decisão de spec |
| B. Aposentar só o consumidor de teste e manter o módulo | `tests/test_dna_analysis.py` (33 linhas) | Não muda nada de substância: o módulo continua vivo pelo harness, e o órfão suspeito permanece |
| C. Declinar e manter como está | nenhum | Mantém a defesa textual do ADR-19, com o risco residual declarado de um reimplementador tratar as faixas como canônicas |

O cenário **A** é o único que produz o retorno descrito no `roi.est_return`. Ele exige, nesta ordem:
decisão humana sobre `RF-25`/`BR-D-62` no ciclo forward, liberação do glob `_reversa_sdd/**` pelo
usuário em `.reversa/reversa-config.json`, e só então a poda.

### Alcance medido do cenário A

| Arquivo | O que sai | Linhas |
|---|---|---|
| `src/core/cm_estimator.py` | o arquivo inteiro | 65 |
| `tests/test_dna_analysis.py` | import da linha 31, comentário das linhas 28 a 30, `test_relationships_by_cm` (275 a 288) e `test_relationships_by_cm_out_of_range` (291 a 302) | 33 (o arquivo vai de 302 para 269) |
| `_reversa_sdd/parity/harness.py` | import da linha 266, uso da linha 339 e o campo `cm` dos dois coletores | 3 no coletor do candidato, mais o espelho no do oráculo |

## O que NÃO será removido

| Item | Por que fica |
|---|---|
| `tests/test_dna_analysis.py` fora das 33 linhas | O restante cobre o pipeline de DNA, colunas, agregação e regras do confronto |
| A fixture `dna_loaded` | Serve outros testes do mesmo arquivo |
| `src/core/relationship_hypotheses.py` | É a autoridade **vigente** sobre cM, pela tabela publicada do SCP 4.0 (`RF-17`, `RF-18`) |
| `src/core/genetic_evidence.py:31` (`LIMITE_SEGMENTO_FRACO = 15.0`) | Heurística declarada do projeto, com requisito próprio (`RF-08`), e não pertence a este alvo |
| `_reversa_sdd/oracle/app_legacy_e43ca22.py` | Cópia congelada do oráculo, tem a própria definição e é somente leitura por decisão de extração |
| `README.md:166` | Só entra no plano do cenário A, para a árvore do projeto parar de listar o módulo. O arquivo está liberado |
| Os resíduos de execução mapeados em 2026-10-08 | Não são código e não têm referência estática a provar; ficam fora desta oportunidade |

## Rede de segurança exigida

`control_mode: gated` e `safety_net_policy: require-characterization`. A remoção não altera
comportamento observável de nenhum caminho de produção, então a rede é a suíte existente mais o
harness de paridade, **antes e depois**.

Ponto de atenção declarado: a suíte do workspace tem 15 erros de ambiente (`PermissionError` do
`tmp_path`), documentados no `conftest.py` e não relacionados a este alvo. O critério de aceite é a
contagem e o conjunto de falhas não aumentarem, comparados arquivo a arquivo, como já é praxe neste
registro.

## Risco

| Risco | Gravidade | Mitigação |
|---|---|---|
| A remoção do campo `cm` reduz o escopo da paridade | média | É consequência declarada, não efeito colateral: o campo passa a ser comparado só no lado do oráculo, que tem cópia própria |
| A regra catalogada `BR-D-62` fica sem implementação | média | Exige decisão de spec no forward; a alternativa é manter o cenário C |
| A sonda `_verificar_t029.py` quebra | baixa | É evidência datada do ciclo 005, não roda na suíte; se a remoção avançar, a sonda fica registrada como histórica |
| Editar `_reversa_sdd/**` sem liberação | alta | O gate recusa por política. A liberação é ato do usuário em `.reversa/reversa-config.json`, que nenhum agente edita |

## Nota de método

`roi.confidence: green` mede o **entendimento e a cobertura do alvo**, não a elegibilidade para
remoção. O módulo é puro, o comportamento está congelado por dois testes e o fluxo não o alcança: é
isso que a confiança verde afirma. A elegibilidade está bloqueada, e o bloqueio está na tabela de
cenários acima.

---
*Gerado pelo Reversa-Refactor em 2026-10-08.*

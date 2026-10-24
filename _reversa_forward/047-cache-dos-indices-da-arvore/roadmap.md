# Roadmap: cache dos índices derivados da árvore

> Identificador: `047-cache-dos-indices-da-arvore`
> Data: `2026-10-24`
> Requirements: `_reversa_forward/047-cache-dos-indices-da-arvore/requirements.md`
> Confidência: 🟢 CONFIRMADO, 🟡 INFERIDO, 🔴 LACUNA

## 1. Resumo da abordagem

Dois caches, um dono cada. O **adaptador** `CarregadorDeArvoresGedcom` guarda a última árvore
parseada, chaveada pelo **arquivo** (caminho + `mtime` + tamanho), com teto 1 e uma trava de
*single-flight*. O **núcleo** passa a prender os índices de matching ao **grafo da própria
árvore**, exatamente como `fichas_da_pessoa._indice_de_filhos` já prende o índice de filhos.

Nada mais muda: nenhuma regra de matching, nenhum limiar, nenhuma rota, nenhuma dependência nova.
O memo de índices é compatível com o adendo vigente por construção — ele morre com a árvore. O
cache da árvore é a supersessão aprovada em 2026-10-24, ligada por variável de ambiente e limitada
a uma árvore.

O que a medição fixou: 88 % do `POST` de análise é custo fixo reexecutado para o mesmo arquivo
(50,53 s de parse + 8,72 s de índices, de 67,29 s).

## 2. Princípios aplicados

| Princípio | Como a feature se relaciona | Status |
|-----------|------------------------------|--------|
| I. Dados reais nunca no versionamento | Os testes usam fixtures sintéticas; a medição não grava nome, `xref` nem cM em artefato | respeita |
| II. Comportamento observável preservado | Hash da árvore e do resultado idênticos com cache ligado e desligado | respeita |
| III. Nenhuma mudança sem teste | Cada RF tem teste de contagem, não de relógio | respeita |
| IV. Arestas tipadas | A feature não percorre grafo; não toca filiação nem casamento | respeita |
| V. Toda suposição cita a fonte | Os números vêm de medição datada, com comando e cenário declarados | respeita |

## 3. Decisões técnicas

| ID | Decisão | Justificativa | Alternativas descartadas | Confidência |
|----|---------|----------------|--------------------------|-------------|
| D-01 | O cache da árvore vive no adaptador `CarregadorDeArvoresGedcom` | É a fronteira que já resolve a referência; o núcleo é puro e não pode guardar estado | cache em `app.py` (borda já tem responsabilidades demais); cache em `core/` (viola o `ADR-24`) | 🟢 |
| D-02 | Chave = caminho absoluto + `mtime_ns` + tamanho | Invalida quando o conteúdo muda, sem reler o arquivo para hashear | chave pela referência (não invalida); `id()` (reciclado); `sha256` do conteúdo (relê 12,5 MB por `POST`) | 🟢 |
| D-03 | Índices presos ao grafo da árvore, por atributo | Segue o padrão já existente de `_indice_de_filhos`; a vida do índice é a vida da árvore | dicionário de módulo chaveado por conteúdo (é a lacuna `L-24`); cache na camada de aplicação (não cobriria `validacao`) | 🟢 |
| D-04 | O memo de índices fica **sempre ligado**; só a árvore é condicionada à flag | O memo morre com a árvore, então cumpre a regra 2 do adendo mesmo com a flag desligada | condicionar os dois à flag (perde o ganho do `validacao` sem motivo) | 🟢 |
| D-05 | Teto 1, LRU, configurável por ambiente | O caso de uso é a mesma árvore em requisições seguidas; duas árvores custam ~714 MB | sem teto (cresce sem limite); teto 2 como padrão (dobra a memória) | 🟢 |
| D-06 | *Single-flight* com evento por chave | Quatro threads na mesma árvore pagariam quatro parses de ~50 s | sem trava (duplicação de parse); fila global (serializa árvores diferentes) | 🟢 |
| D-07 | Desligado por padrão, ligado por `ANALISADOR_CACHE_DE_ARVORE` | O operador pode reverter em produção sem editar código; a spec antiga continua válida por omissão | ligado por padrão (muda memória sem o operador saber) | 🟢 |

## 4. Premissas

Nenhuma. O `requirements.md` está com zero marcadores `[DÚVIDA]` desde a sessão de 2026-10-24.

## 5. Delta arquitetural

| Componente | Arquivo de origem no legado | Tipo de mudança | Resumo |
|------------|------------------------------|-----------------|--------|
| `CarregadorDeArvoresGedcom` | `_reversa_sdd/architecture.md#1` (camada Portas) | regra-alterada | Passa a manter uma árvore em memória, com invalidação por arquivo e teto |
| `build_ged_indexes` | `_reversa_sdd/analise-dna/design.md#fluxo-principal` | regra-alterada | Memoiza o trio de índices no grafo, em vez de reconstruir a cada chamada |
| Afirmação "não há cache entre requisições" | `_reversa_sdd/architecture.md#1` | regra-alterada | Deixa de valer para a árvore e seus derivados; o resto do sistema segue sem cache |
| Quadro "onde o dado vive" | `_reversa_sdd/architecture.md#4` | delta-de-dados | A memória de módulo passa de 1 para 2 estruturas: `CACHE_DE_NOMES` e `CACHE_DE_ARVORES` |
| `CACHE_DE_NOMES` (ERD) | `_reversa_sdd/erd-complete.md#7` | componente-novo | Entra `CACHE_DE_ARVORES`, com chave por arquivo e ciclo de vida por processo |
| Adendo `bug-BUG-20261021-7O7V-v001` | `_reversa_sdd/addenda/bug-BUG-20261021-7O7V-v001.md` | regra-alterada | O item "O que NÃO muda" é superado; a regra 2 (índice derivado) continua valendo |

## 6. Delta no modelo de dados

- Resumo: nenhum campo persistido nasce ou muda. Entra **uma** estrutura em memória
  (`CACHE_DE_ARVORES`) e **um** atributo derivado no grafo (`_índices_de_matching`), os dois
  morrendo com o processo.
- Detalhe completo em: `_reversa_forward/047-cache-dos-indices-da-arvore/data-delta.md`

## 7. Delta de contratos externos

n/a — o `POST /` continua com o mesmo formulário, o mesmo status e o mesmo HTML. O que muda é o
tempo. Não há `interfaces/` nesta feature.

## 8. Plano de migração

1. Não há migração de dado: a estrutura nova é memória de processo e nasce vazia.
2. O operador liga a variável de ambiente no ambiente em que quiser o ganho (`docker-compose` ou
   `.env`); sem ela, nada muda.
3. Reverter é remover a variável e reiniciar o processo — nenhum dado fica para trás.

## 9. Riscos e mitigações

| Risco | Impacto | Probabilidade | Mitigação |
|-------|---------|---------------|-----------|
| ~412 MB residentes (340 da árvore + 30 do índice) em host pequeno | alto | baixa | teto 1, desligado por padrão, e medição do RSS no `onboarding.md` |
| Entrada não invalidar (arquivo trocado com `mtime` e tamanho idênticos) | alto | baixa | o armazenamento é endereçado por hash de conteúdo; o teste cobre a troca com `os.utime` |
| Duplicação de parse sob concorrência | médio | média | *single-flight* com evento e teste de 4 threads |
| Regressão de paridade (ordem, cartões, vereditos) | alto | baixa | hash da árvore e do resultado antes/depois, precedente da feature 025 |
| Superar o adendo sem registro formal | alto | média | adendo da 047 no `/reversa-sync` e ADR próprio |
| Memo de índices compartilhado entre árvores | alto | baixa | preso ao objeto do grafo; teste de duas árvores com o mesmo tamanho |

## 10. Critério de pronto

- [ ] `POST` de análise no caso medido (19.403 pessoas, CSV de 492 linhas) ≤ 9 s com cache ligado
- [ ] `POST` de seleção de árvore ≤ 1 s com cache ligado
- [ ] Desligado, o `POST` não piora mais que 1 % em relação à linha de base (67,29 s)
- [ ] Impressão digital da árvore e do resultado idêntica com cache ligado e desligado
- [ ] Suíte completa verde, com os testes novos contando chamadas (não cronometrando)
- [ ] Todas as ações do `actions.md` marcadas `[X]`
- [ ] `regression-watch.md` gerado
- [ ] Adendo da 047 escrito no `/reversa-sync`

## 11. Histórico de alterações

| Data | Alteração | Autor |
|------|-----------|-------|
| 2026-10-24 | Versão inicial gerada por `/reversa-plan` | reversa |

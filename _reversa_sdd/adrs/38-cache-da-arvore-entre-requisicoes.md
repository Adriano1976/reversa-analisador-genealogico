# ADR-38 — Cache da árvore entre requisições, com chave pelo arquivo

- **Status:** Aceito e **vigente**
- **Data da decisão:** 2026-10-24 (cache), revista em **2026-10-26** (ligado por padrão)
- **Commit(s):** `222d433` (feature 047, implementação), `ba95a4e` (observabilidade), decisão de 2026-10-26 (padrão)
- **Confiança:** 🟢 CONFIRMADO

## Contexto

Cada `POST` reparseava o GEDCOM inteiro. Medido na árvore real de 19.403 pessoas (12,5 MB), o `POST` de
análise levava **67,29 s**, dos quais **50,53 s eram parse** e **8,72 s** a construção dos índices: **88 % do
tempo era custo fixo reexecutado para o mesmo arquivo**. A afirmação anterior de `architecture.md#1` — "não há
cache entre requisições" — era consequência do `ADR-24`, que removeu o estado global e fez a árvore virar
valor.

A feature 047 entregou o cache **desligado por padrão**, por dois receios legítimos: a memória residente
(~412 MB com uma árvore) e a possibilidade de o operador não saber que ela passou a ocupar RAM. O efeito
colateral é que o caso de uso principal — a segunda ação sobre a mesma árvore — continuava pagando ~50 s para
quem não lesse a documentação. O objetivo declarado da mudança (de dezenas de segundos para quase zero) só é
atingido com o cache **ligado**.

## Decisão

1. **O cache vive no adaptador** `CarregadorDeArvoresGedcom`, não no núcleo: é a fronteira que já resolve a
   referência, e nenhum caso de uso importa `parsers/`.
2. **A chave é o arquivo:** `(caminho absoluto, mtime_ns, tamanho)`. Trocar o conteúdo invalida sozinho, sem
   reler 12,5 MB para hashear.
3. **O `dono` não entra na chave.** O armazenamento ignora `dono` e o nome é endereçado por hash de conteúdo;
   incluir `dono` duplicaria a mesma árvore em RAM sem ganho de isolamento. Quando o armazenamento virar
   *owner-scoped* (Onda 3), o caminho passará a distinguir os donos e a chave continuará correta.
4. **Teto 1, LRU, configurável** por `ANALISADOR_CACHE_DE_ARVORE_CAPACIDADE`. Duas árvores custam ~714 MB e
   não servem ao caso de uso; valor inválido avisa e volta ao padrão 1.
5. **Ligado por padrão.** `ANALISADOR_CACHE_DE_ARVORE=0` (ou `false`, `nao`, `off`, `no`) desliga e devolve um
   parse por chamada. Vazio conta como ligado (é `export` sem valor, não intenção).
6. **Falha não é cacheada:** exceção no parse não deixa entrada, e o evento de *single-flight* é liberado no
   `finally`.
7. **Sem `invalidar()` explícito.** Com teto 1, a entrada antiga é despejada na carga seguinte; `aposentar`
   faz o `resolver` devolver `None`, e a árvore antiga deixa de ser servida mesmo antes do despejo. A chave
   pelo arquivo é a segunda barreira.
8. **Proibido devolver cópia profunda.** O custo é `O(V+E)` por requisição e o memo dos índices deixaria de
   valer; a segurança vem da ausência de mutação, não da cópia.

## Evidência

- **Desempenho (pareado, mesma sessão, 2026-10-24):** seleção de árvore **54,81 s → 0,92 s**; análise nº 1
  **70,70 s → 17,79 s**; análise nº 2 **62,17 s → 4,74 s**.
- **Reprodução em 2026-10-26, com o padrão ligado** (mesma árvore real de 19.403 pessoas, 21.528 famílias,
  77.346 arestas): 1ª carga **50,13 s**, 2ª **0,2 ms**, 3ª **0,1 ms**, mesmo objeto nas três; RSS 41 MB →
  **364 MB** depois do parse (Δ 323 MB). O cache já nasce ligado, sem variável.
- **Memória:** RSS 45 MB (vazio) → **381 MB** após o parse → **412 MB** após os índices. Duas árvores: ~714 MB.
- **Paridade A/B do candidato (2026-10-26):** o harness de paridade produziu observações **idênticas** com
  `ANALISADOR_CACHE_DE_ARVORE=1` e `=0` nas 7 fixtures de GEDCOM e no probe de DNA (JSON canônico igual,
  16.510 bytes). O harness contra o **oráculo congelado** acusa 30 divergências **iguais nos dois estados** —
  são do oráculo antigo contra o código atual, não do cache.
- **Paridade de resultado (2026-10-24):** `sha256` do HTML idêntico nas quatro execuções (duas com, duas sem
  cache); nenhum cartão, veredito, ordem ou descarte mudou.
- **Suíte:** 1.686 testes aprovados e 9 pulados em 2026-10-26; `tests/test_cache_de_arvores.py` tem 18 testes.
- **Concorrência:** quatro threads na mesma árvore pagam **um** parse; a árvore devolvida é o mesmo objeto.
- **Falha:** parse que levanta não deixa entrada e não prende o evento; quem esperava parseia por conta própria.

## Consequências

- 🟢 **A segunda ação sobre a mesma árvore não paga o parse.** É o ganho que motivou a mudança.
- 🟢 **Nenhum resultado de análise muda**; a árvore é o mesmo valor que o parse produziria.
- 🟡 **Memória residente passa a ~412 MB** com uma árvore. O host medido tem 11,9 GB (2,2 GB livres), com
  folga para uma árvore; o teto 1 é deliberado.
- 🟡 **Retenção:** a árvore — dado pessoal de terceiros — passa a viver enquanto o processo viver, e não
  apenas durante a requisição. Continua sem ser gravada em disco, logada ou serializada; `L-29` (dado pessoal
  no PostgreSQL) segue intocada.
- 🟡 **Estado compartilhado entre threads:** a árvore cacheada é lida por várias threads. Os quatro
  componentes não são mutados; três memos derivados são pendurados no grafo de forma idempotente
  (`matching`, `homonimos`, `fichas_da_pessoa`), sem trava — duas construções simultâneas podem acontecer,
  mas o valor é sempre o mesmo. `cirurgia_do_grafo` copia o grafo antes de escrever.
- 🟢 **Reversível sem editar código:** `ANALISADOR_CACHE_DE_ARVORE=0` e reiniciar.

## Riscos e limites

| Risco | Impacto | Mitigação |
| --- | --- | --- |
| Árvore trocada com mesmo `mtime` e tamanho | alto | o armazenamento é endereçado por hash de conteúdo; o teste cobre troca com `os.utime` |
| Memória em host pequeno | alto | teto 1, desligável por ambiente, aviso no `README` |
| Mutação acidental do objeto compartilhado | alto | auditoria: nenhum dos quatro componentes é mutado fora do parse; memo idempotente; teste de índice por árvore |
| Duplicação de parse sob concorrência | médio | *single-flight* por chave, com evento |
| Duplicação transitória de índice no primeiro acesso concorrente | baixo | construção idempotente; custo ~31 MB por cópia, descartada |
| Isolamento por dono ainda ausente (dívida #2 de `architecture.md#7`, Onda 3) | alto | a chave por caminho não piora o que o armazenamento já faz; corrigir junto com a Onda 3 |

## Alternativas descartadas

- **Chave pela referência:** não invalida quando o arquivo é substituído no mesmo nome.
- **Chave por `id()`:** reciclado pelo CPython, serviria a árvore errada.
- **Chave por `sha256` do conteúdo:** relê 12,5 MB a cada `POST`.
- **Cache de módulo chaveado por conteúdo:** é a classe do defeito `L-24`, que a feature 048 removeu.
- **Cópia profunda por requisição:** `O(V+E)`, mata o memo dos índices.
- **Cache em Redis/entre processos:** fora de escopo; o processo é único por construção.
- **Teto 2 como padrão:** ~714 MB para um acerto que quase não acontece.

## Fontes

- `_reversa_forward/047-cache-dos-indices-da-arvore/requirements.md`
- `_reversa_forward/047-cache-dos-indices-da-arvore/roadmap.md`
- `_reversa_forward/047-cache-dos-indices-da-arvore/evidence/depois.md`
- `_reversa_forward/047-cache-dos-indices-da-arvore/evidence/memoria.md`
- `_reversa_forward/047-cache-dos-indices-da-arvore/evidence/paridade.md`
- `_reversa_sdd/addenda/047-cache-dos-indices-da-arvore.md`
- `src/ports/adaptadores.py` (`CacheDeArvores`, `CarregadorDeArvoresGedcom`)

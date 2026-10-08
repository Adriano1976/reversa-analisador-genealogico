# Cross-check: persistência histórica das análises em banco relacional

> Identificador da feature: `008-persistencia-postgres-docker`
> Data: `2026-10-08`
> Artefatos auditados: `requirements.md`, `roadmap.md`, `actions.md` — os três em
> `_reversa_forward/008-persistencia-postgres-docker/`
> Apoio consultado: `data-delta.md`, `investigation.md`, `onboarding.md`, `_reversa_sdd/`
> (extração), `.reversa/principles.md`, `src/` (código real) e medição do workspace
> **Este arquivo contém duas passagens.** A **2ª** verifica o fechamento dos achados da 1ª; o
> registro da **1ª** foi preservado na §"1ª passagem", porque ele é o relato do que foi
> encontrado antes de qualquer correção.
> Escala: CRITICAL · HIGH · MEDIUM · LOW

## Resumo

| Passagem | CRITICAL | HIGH | MEDIUM | LOW | Total |
|---|---:|---:|---:|---:|---:|
| **1ª** — `01:16`, antes das correções | 0 | **3** | 3 | 4 | 10 |
| **2ª** — verificação e reexame | 0 | **0** | 3 | 3 | 6 |

**Fechamento da 1ª passagem: 9 dos 10 achados fechados; `A009` fechado pela metade.**

| Achado | Severidade | Veredito da 2ª passagem |
|---|---|---|
| `A001` | HIGH | ✅ **FECHADO** |
| `A002` | HIGH | ✅ **FECHADO** |
| `A003` | HIGH | ✅ **FECHADO** |
| `A004` | MEDIUM | ✅ **FECHADO** |
| `A005` | MEDIUM | ✅ **FECHADO** |
| `A006` | MEDIUM | ✅ **FECHADO** |
| `A007` | LOW | ✅ **FECHADO** |
| `A008` | LOW | ✅ **FECHADO** |
| `A009` | LOW | ⚠️ **PARCIAL** — ver `B001` |
| `A010` | LOW | ✅ **FECHADO** |

**Veredito da 2ª passagem: aprovado — nenhum CRITICAL, nenhum HIGH e nenhum achado que
impeça o coding.** Os três MEDIUM e três LOW são ressalvas, não bloqueios. Duas merecem
leitura antes do `/reversa-coding`: o `B002` (uma ação cita como linha de base um lugar que
não a contém) e o `B003` (a projeção não tem teste sem banco).

## 2ª passagem — verificação dos fechamentos

| Achado | Como foi verificado | Evidência no artefato |
|---|---|---|
| `A001` | Leitura de `T004`, `T005` e `T006` | `T004` diz "**Toda criação com `IF NOT EXISTS` e nenhum `DROP`**"; `T005` repete "**`IF NOT EXISTS` em tudo, sem `DROP`**"; `T006` declara "**bind mount somente-leitura de `./init.sql` em `/docker-entrypoint-initdb.d/init.sql`** (sem ele o `T009` não tem o que executar)". O `T009` passa a ter arquivo para executar |
| `A002` | Leitura de `T002` e de `D-18`, e conferência de que a lista cobre o que o `T003` copia | `T002` escreve `*`, `!requirements.txt`, `!src/`, `!src/**`, e reexclui `src/uploads/` e `src/**/__pycache__/`. `D-18` registra a medição (**22** ilegíveis, **12** cobertos, **10** fora) e a alternativa estrutural. **`requirements.txt` e `src/**` — as duas origens do `COPY` do `T003` — estão na lista de permissão** |
| `A003` | Leitura de `T026` e do critério de pronto | `T026` mede com a persistência desabilitada e habilitada, com o critério "**abaixo do dobro**", que é o RNF de Desempenho. O `roadmap.md` §10 ganhou o item correspondente |
| `A004` | Leitura de `T021` | Passa a citar "os passos §6 (`down` + `up`, com `src/uploads/` e a contagem de análises preservadas, `RF-02`) e §9 (banco **derrubado**)" |
| `A005` | Leitura de `T014` | Passa a afirmar "dois kits do mesmo nome **sem soma entre eles e com o estado final gravado sendo o mais conservador dos dois**" |
| `A006` | Leitura de `T019` | Passa a dizer "gravação **recusada por alvo inválido** — `DATABASE_URL` apontando para uma porta fechada" |
| `A007` | Leitura de `T021` | Passa a nomear o esperado: "esperando que nenhum dos dois apareça (`RF-16`)" |
| `A008` | Leitura de `T013` | Passa a citar o `D-16`, o texto "**ao caractere**" e a ausência do código do aviso |
| `A009` | Varredura por "achado C" no `roadmap.md` | ⚠️ **Parcial.** A ocorrência do §9 foi corrigida para "Achado C do `actions.md` da feature 007"; a **`D-11` (§3, linha 88) mantém "achado C da 007" sem o arquivo**, e o histórico do próprio roadmap (§11) afirma que a citação foi corrigida. Ver `B001` |
| `A010` | Leitura de `T002` | ✅ Resolvido por consequência: a linha `.probe/` saiu junto com a lista de negação, e o resíduo passa a ficar fora pela lista de permissão |

## 2ª passagem — achados novos

| ID | Severidade | Eixo | Descrição | Onde está |
|---|---|---|---|---|
| `B001` | MEDIUM | Consistência | A citação imprecisa do `A009` **sobreviveu num dos dois lugares**: a `D-11` ainda diz "achado C da 007" sem apontar o arquivo, e o **histórico do `roadmap.md`** afirma que a citação foi corrigida. É contradição interna entre o §3 e o §11 do mesmo documento | `roadmap.md` §3 (`D-11`), §11 |
| `B002` | MEDIUM | Consistência | O `T026` manda medir o custo e diz que "o `roadmap.md` §0 registra a linha de base de onde ele parte". O §0 **não contém duração de análise** — ele traz suíte (`261 passed`), paridade (`100 %`) e medições de ambiente. A linha de base do tempo tem de ser medida **na própria ação**, com a persistência desabilitada | `actions.md` `T026` · `roadmap.md` §0 |
| `B003` | MEDIUM | Cobertura | A **projeção** (`D-15`, `T015`) não tem teste que rode **sem banco**. Os únicos que a exercitam — `T014` e `T020` — exigem `DATABASE_URL`, e o `T014` é pulado sem ele (`D-17`). Sem Docker, o ponto mais delicado da costura, que é o mapeamento do resultado para as linhas, fica sem cobertura automatizada; e a projeção é **pura**, logo testável sem banco | `roadmap.md` `D-15` · `actions.md` `T015`, `T014`, `T020` |
| `B004` | LOW | Consistência | O `T010` e o `T024` citam `D-11` onde `D-18` é a decisão aplicável — a lista de permissão e o resíduo preso. Referência imprecisa, não incorreta: `D-11` é a decisão-mãe das duas | `actions.md` `T010`, `T024` |
| `B005` | LOW | Cobertura | `DD-05` do `data-delta.md` §9 — 🔴 "empate exato entre kits de mesmo cM pode não ser reproduzível", porque o núcleo ordena por cM com desempate não declarado — **não aparece em nenhum risco** do `roadmap.md` §9. A lacuna está declarada no artefato de dados, mas não chegou ao registro de riscos | `data-delta.md` §9 · `roadmap.md` §9 |
| `B006` | LOW | Cosmético | O blockquote do resumo do `actions.md` tem uma quebra de linha que parte a frase ao meio ("...estar medido, porque" / "> o risco de contêiner..."). Artefato da edição das correções; não muda o sentido | `actions.md` §Resumo |

### `B001` — o fechamento parcial, detalhado

**Impacto.** O `A009` pedia que uma citação imprecisa passasse a apontar o arquivo. A correção
atingiu uma das duas ocorrências, e o **histórico de alterações do próprio roadmap** registra
que a citação "passa a apontar o arquivo". O resultado é um documento que **afirma ter
corrigido o que não corrigiu por completo** — o defeito é pequeno, mas a classe dele não é: é
a mesma de um adendo que declara um delta que o código não tem.

**Registro honesto de quem errou.** A declaração anterior desta sessão dizia que a correção
foi feita "nas duas ocorrências". **Estava errada**, e a varredura desta passagem é o que
mostra isso. O erro está preservado aqui em vez de apagado.

**Sugestão de direção.** Corrigir a `D-11` no §3 do `roadmap.md` para citar o arquivo, ou
ajustar o histórico do §11 para dizer que a correção foi parcial. Qualquer das duas fecha —
mas só uma é verdadeira sem editar o §3.

### `B002` — a linha de base que não existe no lugar citado

**Impacto.** O `T026` é a única ação que atende ao RNF de Desempenho, e ele aponta para o §0
como origem da linha de base. O §0 é honesto e medido, mas mede **outra coisa**: suíte,
paridade e ambiente. Um executor que siga a instrução ao pé da letra vai procurar ali um
número que não existe. A consequência é branda, porque a ação também diz "com a persistência
desabilitada e habilitada" — a medição dupla está descrita. Mas a citação é falsa, e citação
falsa em ação de medição é o defeito que a feature 007 corrigiu no `T004` dela.

**Sugestão de direção.** Retirar a menção ao §0 do `T026` e deixar explícito que a linha de
base do tempo é **a primeira metade da própria medição**.

### `B003` — a projeção pura sem teste sem banco

**Impacto.** A `D-15` faz da projeção o núcleo da costura: é ela que transforma o resultado
do núcleo nas linhas, e é ela que garante que nada é recalculado. Sendo **pura**, ela é
justamente a parte que **mais** se beneficia de um teste sem ambiente — e é a única parte
central da feature sem um. Com o Docker fora, o `T014` é pulado e o `T020` não roda; sobra o
`T018`, que prova só o estado desabilitado, e o `T019`, que prova só o estado de falha.

**Sugestão de direção.** Acrescentar um teste da projeção que não toque o banco: dado um
resultado sintético com dois kits e um caminho, afirmar as linhas produzidas — pessoas com
`completa` verdadeiro e falso, kits sem soma, ordem preservada e os quatro estados passando
intactos. É a ação que torna a `D-17` sustentável: o que dá para provar sem banco, prova-se
sem banco.

## 1ª passagem — registro preservado (2026-10-08, 01:16)

Dez achados, antes de qualquer correção: **zero CRITICAL**, três HIGH, três MEDIUM, quatro LOW.
Íntegra do que foi encontrado.

| ID | Severidade | Eixo | Descrição | Onde está |
|---|---|---|---|---|
| `A001` | HIGH | Cobertura | A decisão `D-07` — `init.sql` idempotente e executado pelo `docker-entrypoint-initdb.d` — **não tinha ação correspondente**. Nem `T004`/`T005` mandavam escrever `IF NOT EXISTS`, nem `T006` mandava montar o `init.sql` no entrypoint, e o `T009` executava `psql -f /docker-entrypoint-initdb.d/init.sql` | `roadmap.md` `D-07` · `actions.md` `T004`, `T005`, `T006`, `T009` · `requirements.md` `RF-12` |
| `A002` | HIGH | Cobertura | O `.dockerignore` do `D-11`/`T002` **não cobria 10 diretórios ilegíveis** dentro do contexto de build. Medido: **22** dirs recusam `scandir` na raiz, **12 cobertos**, **10 fora** — sete em `.pytest-tmp/`, dois em `_probe_acl/` e um em `_probe_acl2/`. O `docker build` do `T008` abortaria neles | `roadmap.md` `D-11` · `actions.md` `T002`, `T008` |
| `A003` | HIGH | Cobertura | O **RNF de Desempenho** não tinha decisão nem ação. O `investigation.md` §7 declarava que "o plano exige a medição", e nenhuma ação a produzia | `requirements.md` §6, §8 · `investigation.md` §7 |
| `A004` | MEDIUM | Cobertura | O cenário "o histórico sobrevive ao reinício dos serviços" (`RF-02`) não era citado por ação nenhuma: o `T021` citava só o §9 | `requirements.md` §7 · `actions.md` `T021` |
| `A005` | MEDIUM | Cobertura | O cenário "dois kits do mesmo nome" tinha só metade instruída: faltava a asserção "o estado final gravado é o mais conservador" | `requirements.md` §7 · `actions.md` `T014` |
| `A006` | MEDIUM | Cobertura | O `T019` mandava testar "gravação recusada" sem dizer **como** provocar a recusa com o banco no ar | `actions.md` `T019` |
| `A007` | LOW | Cobertura | O `RF-16` estava coberto por consequência: o `T021` conferia `git status` sem resultado esperado próprio | `requirements.md` `RF-16` · `actions.md` `T021` |
| `A008` | LOW | Cobertura | A `D-16` (texto ao caractere, sem o código do aviso) não era mencionada em ação nenhuma | `roadmap.md` `D-16` · `actions.md` `T005`, `T013` |
| `A009` | LOW | Consistência | Citação imprecisa: "achado C da 007" sem caminho, e o achado C está no `actions.md` da 007, não no adendo dela | `roadmap.md` §9, §11 · `investigation.md` §2 |
| `A010` | LOW | Consistência | O `T002` excluía `.probe/` na raiz enquanto o resíduo real vive em `_reversa_forward/008-.../.probe/`, já coberto por `_reversa_*/` — linha inócua onde estava | `actions.md` `T002` · `roadmap.md` §5 |

> **Hipótese refutada por medição, na 1ª passagem, e registrada para não ser refeita.**
> Suspeitou-se que o `.probe/` desta sessão fosse suficiente para derrubar o build. Ele **não**
> é o problema principal: está coberto por `_reversa_*/`. O problema eram os dez diretórios
> que já existiam na raiz antes desta feature.

## Itens verificados que passaram, nas duas passagens

### Cobertura

- Os **17 requisitos funcionais** têm decisão no roadmap, e **nenhum ficou sem ação** depois
  das correções. O `RF-13` ganhou a `D-17`, e o `RF-02` e o `RF-16` ganharam instrução
  explícita no `T021`.
- Os **17 requisitos não funcionais** foram conferidos um a um: 12 têm decisão e ação;
  Desempenho passou a ter o `T026`; Segurança sobre criptografia em repouso é **aceite de
  risco** (`Q-04`), e aceite não produz ação de implementação; Privacidade e Reprodutibilidade
  são exercidos pelo `T021` e pelo `T014`.
- Os **7 cenários Gherkin** têm cobertura: cinco por ação direta, e os dois que estavam
  parciais (`A004`, `A005`) passaram a estar instruídos.
- As **18 decisões** (`D-01` a `D-18`) têm ação correspondente, com uma única exceção
  declarada: a `D-13` é decisão de **não fazer**, e o `actions.md` a registra nas notas.

### Consistência

- A contagem de **seis tabelas** bate em três lugares: `roadmap.md` §6, `data-delta.md` §3 e
  a aritmética `T004` (4 herdadas) + `T005` (2 extensões).
- `owner_id` (coluna) e `dono` (conceito) seguem com a distinção declarada.
- Os **quatro estados do veredito** mantêm a mesma grafia nos quatro documentos que os citam.
- O diretório `interfaces/` **não existe**, e o `roadmap.md` §7 declara por quê.
- **Nenhum identificador fantasma**, reconferido nesta passagem: `RF-01`–`RF-17`,
  `RN-01`–`RN-13`, `D-01`–`D-18`, `T001`–`T026`, `E-01`, `W016`, `RISK-004`/`005`,
  `AMB-017`/`019`, `L-21`, `P-01`–`P-05` e `DD-01`–`DD-05`.
- A nova `D-18` é citada pelo `T002` (o artefato que a implementa), pelo `roadmap.md` §5 e §9
  e pelo critério de pronto do §10 — a decisão nasceu já com âncora nos dois lados.

### Coerência com o legado

- **Nenhuma regra 🟢 do `_reversa_sdd/domain.md` é alterada.** `src/core/`, `src/parsers/`,
  `src/reporting/` e `src/utils/` seguem como *presença* no delta arquitetural, e o `T023`
  confere por `diff`.
- O `ADR-18` (single-tenant por aceite de risco) segue respeitado: `owner_id` sem `FK`, sem
  índice de escopo e sem filtro.
- O `ADR-03` (Mermaid no cliente) segue respeitado: o texto do Mermaid não é persistido.
- O `erd-complete.md` §7 ("não existe constraint") não é contradito: as `FK` são entre as seis
  tabelas novas, e o `data-delta.md` §7 explica.
- Componentes citados existem, e as **âncoras de linha** conferem: `src/app.py:268` e
  `:310-314`, `tests/conftest.py:166-171`, `_reversa_sdd/parity/harness.py:356`,
  `core/dna_analysis.py:100-115`, `:182-189`, `:243-249`, `:266-270`,
  `core/genetic_evidence.py:234`, `core/evidence_comparison.py:55-68` e `index.html:27`.

### Sanidade do actions

- **26 IDs únicos**, `T001` a `T026`, nenhum reciclado e nenhuma lacuna na sequência.
- **Todas as dependências apontam para IDs existentes** e para trás — **sem ciclo**. Cadeia
  mais longa: 14 ações, 13 elos, conferida elo a elo.
- **Nenhuma das 11 marcações `[//]` compartilha arquivo alvo**, reconferido par a par depois
  das correções. A única ressalva continua sendo a **pasta** `evidence/` compartilhada por
  `T009`, `T010` e `T024`, com arquivos distintos e nenhuma leitura cruzada — declarada no
  próprio `actions.md`.
- **Todos os 26 status são `[ ]`**, e nenhuma ação de IDE, lint ou PR foi incluída.
- O `T026`, acrescentado nas correções, **não quebrou o paralelismo**: não leva `[//]` e não
  compartilha alvo com nenhuma outra ação.

## Nota de método, e o limite desta passagem

Esta passagem **mediu** o que pôde. As duas verificações decisivas foram a varredura por
"achado C" no `roadmap.md`, que revelou o fechamento parcial do `A009` (`B001`), e a
reconferência da matriz de cobertura, que revelou a projeção sem teste sem banco (`B003`).

⚠️ **Limite declarado, e ele é real: as duas passagens foram feitas pelo mesmo autor.**
A auditoria existe para ser uma leitura independente, e esta não é — o mesmo agente que
escreveu os artefatos os auditou e depois os corrigiu. O que reduz o valor da 2ª passagem não
é ela ter encontrado pouco, e sim ela ter procurado com o mesmo olhar que produziu o defeito.
As duas coisas que ela encontrou — uma citação que sobreviveu à correção e uma ação que cita
um lugar que não contém o que ela diz — são exatamente do tipo que o próprio autor não vê.
Nada aqui substitui uma revisão humana ou uma passagem por outro agente.

## Histórico de alterações

| Data | Alteração | Autor |
|------|-----------|-------|
| 2026-10-08 | 1ª passagem: auditoria cruzada com 3 HIGH, 3 MEDIUM e 4 LOW, zero CRITICAL | reversa |
| 2026-10-08 | 2ª passagem: verificação dos dez fechamentos — **9 fechados, 1 parcial** (`A009`) — e seis achados novos, sendo 3 MEDIUM e 3 LOW, zero HIGH. Registro da 1ª passagem preservado na íntegra | reversa |

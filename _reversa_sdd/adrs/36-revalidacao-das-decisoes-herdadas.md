# ADR-36 — Revalidação das 23 decisões herdadas contra o código de 2026-10-10

- **Status:** Registro de revalidação — **não é uma decisão nova**
- **Data da revalidação:** 2026-10-10
- **Método:** releitura de cada ADR contra os artefatos desta rodada (`code-analysis.md`, `data-dictionary.md`, `flowcharts/`, `.reversa/context/modules.json`), que por sua vez foram extraídos do código de `980502c`, e contra o histórico de commits (`git log` — 126 commits desde 2026-10-05)
- **Confiança:** 🟢 CONFIRMADO

## Por que este registro existe

As 23 decisões de `adrs/01` a `adrs/23` foram reconstruídas em 2026-10-05, e **descrevem o código daquele dia**. Entre aquele dia e este entraram **8 features do ciclo forward** (`005` a `012`) e 126 commits — incluindo uma decisão **revertida** (`ADR-35`) e uma mudança que **contradiz** o texto de um ADR anterior (`ADR-32` contra o `ADR-17`).

Editar cada um dos 23 arquivos seria reescrever história; deixá-los sem ressalva seria pior. Este registro dá o **estado de cada um** e o **delta**, em um lugar só, para que nenhum leitor futuro trabalhe sobre um ADR materialmente vencido sem saber.

**Nenhum dos 23 foi declarado superado.** Todos continuam válidos no **sentido**; o que muda, em seis deles, é a **descrição do estado atual**.

## Quadro de revalidação

| ADR | Assunto | Status | Delta desde 2026-10-05 |
| --- | --- | --- | --- |
| 01 | Reconstruir em módulos | 🟢 vigente | Nenhum |
| 02 | Camada de rota fina | ⚠️ **vigente, e a fronteira ficou menos fina** | `app.py` passou de 267 para **559 linhas úteis** (625 cruas). O aumento **não** é de regra de negócio histórica, mas **passou a haver regra nova ali**: as duas rotas de arte (`BR-E-01` a `BR-E-06`) e a orquestração da lista (`BR-T-12` a `BR-T-17`) vivem no adaptador. A afirmação de 2026-10-05 — "nenhuma regra catalogada vive em `app.py`" — **deixou de ser verdadeira**. Ver a ressalva abaixo |
| 03 | Mermaid no cliente | 🟢 vigente | Nenhum. O Mermaid continua sendo renderizado pelo navegador via CDN |
| 04 | Oráculo congelado por commit | 🟢 vigente | Nenhum. O oráculo continua em `_reversa_sdd/oracle/app_legacy_e43ca22.py` e a paridade é medida contra ele |
| 05 | Escape de rótulo Mermaid | 🟢 vigente e **ampliado** | O `BUG-20261002-T4ZM` já estava registrado; a lista branca permanece a defesa, e o `ADR-34` garantiu que ela continue chegando ao renderizador pelo resolvedor |
| 06 | Política de edição do legado | 🟢 vigente e **ampliada** | `docs/**` foi **liberado para escrita** em 2026-10-08 (commit `ad23f20`), e `_reversa_config` passou a permitir `docker/**`, `docker-compose.yml`, `init.sql` e `.dockerignore` para as features 008 e 011 |
| 07 | Autoridade única de limpeza de nome | 🟢 vigente e **ampliada** | `norm_name` foi movida para `utils/name_keys.py` (`ADR-34`), o que **reforça** a decisão: a autoridade continua única e agora mora onde é pura |
| 08 | Não implementar `HARD_MIN`/`GIVEN_MIN` | 🟢 vigente | Nenhum. Os literais continuam ausentes do código |
| 09 | Remover entidades decorativas | 🟢 vigente | Nenhum |
| 10 | Mover a raiz para `src/` | 🟢 vigente | Nenhum |
| 11 | Reorganizar em pacotes por responsabilidade | 🟢 vigente e **ampliada** | Entraram `src/application/` e `src/ports/` (`ADR-25`); o ciclo `core↔reporting` foi quebrado (`ADR-34`) **sem** mover as decisões de layout — a decisão de que `reporting/` não é folha continua valendo |
| 12 | Servidor waitress, instância única | ⚠️ **vigente, com o MOTIVO alterado** | A guarda de exclusividade existia por causa do **estado global da árvore**. Esse motivo **desapareceu** com o `ADR-24`; o que resta é o **armazenamento em disco**. A guarda continua correta; a justificativa registrada no ADR está vencida, e o próprio código já a atualizou |
| 13 | Fixar as dependências diretas | ⚠️ **vigente, com divergência nova e INVERSA** | O pin das 9 diretas continua. Mas `psycopg2-binary==2.9.13` **está pinado e não está instalado** no `.venv`, que é o interpretador oficial (`L-26`). A rodada anterior registrava divergência **de versão**; esta registra divergência **de presença** |
| 14 | Separar documental, genética e confronto | 🟢 vigente | **Nenhum.** É a regra central do domínio e nenhuma das features 005–012 a tocou |
| 15 | Confronto por sobreposição de faixas | 🟢 vigente | Nenhum. O critério continua sendo sobreposição, e não distância em meioses |
| 16 | Leitura tolerante do CSV | 🟢 vigente | Nenhum |
| 17 | Upload por chave de conteúdo | ⚠️ **vigente no princípio, com a DEFESA reescrita** | A chave por conteúdo continua correta e é o que faz o papel de sessão. O que **caiu** foi a **forma fechada como defesa única**: o alfabeto recusava o que o gravador preserva, e a defesa passou a ser a forma de nome (`ADR-32` / `RN-20` / `BUG-20261009-6RKP`) |
| 18 | Single-tenant por aceite de risco | 🟢 vigente, e **metade do risco fechou** | A contaminação de árvore entre threads tornou-se **estruturalmente impossível** (`ADR-24`). Permanecem: quem conhece a chave carrega a árvore, a exposição de `all_names` e a ausência de propriedade. O critério de aceite do `BUG-20260929-BJJH` **continua não atendido** |
| 19 | Heurísticas declaradas como heurísticas | 🟢 vigente e **ampliada** | Somaram-se `LIMITE_SEGMENTO_FRACO` (15 cM) e a **confiança da lista** de possibilidades, ambas declaradas no código como critério do projeto e não da fonte |
| 20 | Formatação numérica só na apresentação | 🟢 vigente e **ampliada** | Somaram-se `formatar_inteiro`, `formatar_data_br` e o filtro `rotulo_do_arquivo`. Nenhum deles move cálculo para a apresentação |
| 21 | Endogamia: avisar, não corrigir | 🟢 vigente | Nenhum. E ele **interage** com a persistência nova: o veredito gravado é o mesmo que a tela mostra |
| 22 | Ordem de apresentação: documental primeiro | 🟢 vigente | Nenhum — e a decisão ganhou reforço: `match_result.result_ordinal` é o único campo do banco que **reproduz** essa ordem, e o `init.sql` registra que o índice do alvo **não** a reproduziria |
| 23 | Desempate determinístico | ✅ **FECHADO por execução** | A decisão de 2026-10-05 era o menor `xref_id` e estava **não implementada**. Foi implementada em 2026-10-06 (commit `9aa190a`) e está congelada por `tests/test_characterization_matching.py`, que prova as duas direções |

## As três ressalvas que mudam a leitura

### 1. A "rota fina" deixou de ser tão fina (ADR-02)

O `ADR-02` afirma que a contagem maior de `app.py` não contradiz a decisão porque as linhas acrescentadas são de **infraestrutura de entrada**. Isso **ainda vale** para o teto de corpo, o handler de 413, os filtros de template, a ancoragem do caminho e a guarda de instância única. **Deixou de valer** para as features 009, 011 e 012: as duas rotas de arte e as duas ações da lista são **contrato de comportamento**, com regras catalogadas (`BR-E-*`, `BR-T-12` a `BR-T-17`) cuja **localização é o adaptador**.

**A leitura correta hoje:** `app.py` continua sendo a **borda**, e as regras que vivem nele são de **apresentação e de superfície HTTP** — não de domínio. Nenhuma regra de negócio genealógica mora no adaptador. A fronteira que o `ADR-02` protege continua intacta; o que cresceu foi a superfície, e ela cresceu **com contrato declarado**, não com regra vazada.

### 2. A justificativa da instância única venceu (ADR-12)

O `ADR-12` justifica a guarda de exclusividade pela combinação de **estado global em memória** e **armazenamento em disco**. A primeira metade morreu no `ADR-24`. A guarda permanece — e o código de `src/app.py` já registra o motivo atualizado, nomeando o armazenamento como o que resta.

**Consequência prática:** se algum dia o armazenamento ganhar escopo por dono (`owner_id` de verdade), a justificativa da guarda cai **inteira**, e ela poderá ser reavaliada. Hoje ela não pode.

### 3. O `ADR-17` convive com o `ADR-32`, e a ordem de leitura importa

Os dois tratam da referência ao arquivo armazenado, e **não se contradizem**:

| Dimensão | Vale o quê |
| --- | --- |
| **Como o identificador é derivado** | `ADR-17`: do **conteúdo** (`sha256` truncado). Vigente, sem exceção |
| **O que acontece se a mesma chave for reenviada** | `ADR-17`: **não reescreve**. Vigente |
| **Qual é a defesa contra escape de pasta** | **`ADR-32`**: a **forma de nome**, em duas funções. O alfabeto fechado descrito no `ADR-17` foi **revogado** |
| **Se a referência precisa ter chave** | Depende do uso: `resolver` **sim**; `aposentar` **não** |

## Consequências deste registro

- 🟢 **Nenhum ADR herdado foi editado.** A história permanece como foi escrita, e a revalidação fica datada e localizada.
- 🟡 **Seis ADRs precisam ser lidos com este registro ao lado:** 02, 06, 12, 13, 17 e 23.
- 🟢 **A numeração continua sem lacuna:** as decisões novas vão de `24` a `35`, e este registro é o `36`.
- 🟡 **A revalidação foi feita contra os artefatos desta rodada**, não por execução do sistema. As afirmações de comportamento que envolvem execução — paridade, suíte, cobertura — carregam a confiança declarada nos artefatos de origem, e não foram remedidas aqui além do que o `inventory.md` registra.

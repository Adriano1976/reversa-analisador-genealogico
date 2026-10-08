# Adendo: rota do ícone de atalho para tela inicial

> Identificador da feature: `009-rota-do-apple-touch-icon`
> Data: `2026-10-08`
> Cenário: **legado** (âncora em `_reversa_sdd/architecture.md` + `_reversa_sdd/domain.md`)

## Vigência

Vigente desde 2026-10-08.

## Resumo da entrega

Acrescenta a **quarta linha** do contrato HTTP: uma rota de leitura em `src/app.py` que
devolve o **ícone de atalho** — a arte do projeto composta sobre branco, 180×180, opaca —
para quem salva o endereço na tela inicial de um celular.

A lacuna que ela fecha é medida, e não estética: o projeto **já tinha** ícone na aba do
navegador, embutido no documento como `data URI`, e essa solução é **inerte** para o atalho.
O sistema móvel não lê a imagem do documento; ele procura um caminho convencional na raiz.
São dois recursos diferentes, com dois tamanhos e duas exigências de transparência.

A arte servida **não é a canônica**: a canônica tem 32,5 % de pixels transparentes e o
sistema móvel compõe transparência sobre **preto**, o que produziria um quadrado preto com
o desenho por cima. A arte servida é uma **renderização derivada**, commitada em
`src/assets/`, com um teste que a regenera a partir da canônica e compara **pixel a pixel**.

**Progresso: 15 de 15 ações concluídas**, nenhuma aberta em `actions.md`.

| Prova | Resultado |
|---|---|
| Suíte | **302 aprovados, 8 pulados** (linha de base: `282 aprovados`) |
| Paridade diferencial | **100 %**, exit 0 |
| "Falha antes" (`RF-08`) | **registrada**: com a rota ausente, 5 falharam com `404` e 3 guardas da tela já passavam |
| Arte na imagem | **16.504 bytes** dentro do contêiner, com `src/static/` ausente |
| Rota de dentro do contêiner | `200`, `image/png`, 16.504 bytes, `cache-control: no-cache` |
| Tela imutável | `GET /` com **23.906 bytes** — o mesmo `sha256` de antes da feature |
| Núcleo e template | **`diff` vazio** em `src/templates/`, `src/core/`, `src/parsers/`, `src/reporting/`, `src/utils/` |
| Pegada total | `src/app.py`: **47 inserções e 1 remoção** — e a remoção é o import reescrito |

## Impacto por artefato da extração

| Artefato | Seção | Tipo de impacto | Delta |
|---|---|---|---|
| `_reversa_sdd/upload-gedcom/contracts.md` | `#1` (Contrato HTTP) | `delta-de-contrato-externo` | O contrato passa de **três para quatro linhas**: `GET /apple-touch-icon.png` → `200` com imagem. As três linhas existentes ficam **idênticas**, e a frase *"não há contrato JSON, redirect, `201`, `400` ou `409`"* **continua verdadeira** — a linha nova não é payload nem redirecionamento. O detalhe está em `interfaces/apple-touch-icon.md`, o **primeiro** `interfaces/` do projeto |
| `_reversa_sdd/c4-components.md` | "Inventário de componentes" e "Cadeia de dependência dos três fluxos" | `contrato-alterado` | A camada de rota deixa de ter **uma** rota e passa a ter **duas**. ⚠️ A rota nova **não entra na cadeia dos três fluxos**: ela não chama caso de uso, porta nem núcleo — servir um arquivo fixo é adaptação de entrada pura |
| `_reversa_sdd/architecture.md` | `#3` (Componentes e estrutura de pacotes) | `componente-novo` | `src/assets/` **não existe** no inventário. Recebe **um** binário: a arte derivada, 180×180, opaca, 16.504 bytes. Não é entidade do modelo nem dado de domínio |
| `_reversa_sdd/architecture.md` | `#2` (Containers) | `presença` | ❌ **INALTERADA.** A composição não muda. O `.dockerignore` continua lista de permissão e a arte entra por `!src/**`; `src/static/` segue **ausente na imagem** |
| `_reversa_sdd/architecture.md` | `#4` (Modelo de Dados) | `presença` | ❌ **INALTERADO.** Nenhuma das 27 estruturas é criada, alterada ou removida. Nenhum campo, índice ou migração. Ver `data-delta.md` da feature |
| `_reversa_sdd/architecture.md` | `#6` (Mapa de Integrações Externas) | `presença` | ❌ **INALTERADO.** Nenhuma dependência externa nova. A rota é servida do próprio processo, sem rede de saída |
| `_reversa_sdd/architecture.md` | `#7` (Dívidas), #17 | `presença` | ❌ **INALTERADA, de propósito.** A dívida era *"superfícies de compatibilidade reexportando nomes históricos que ninguém usa"* e está **fechada**. A `RN-09` existe para que esta entrega não a reabra: o alias legado e o `favicon.ico` continuam **sem resposta** |
| `_reversa_sdd/domain.md` | `#2`, `#3` e `#5` | `presença` | ❌ **NENHUMA regra de negócio criada, alterada ou removida.** As dez mensagens da camada de rota continuam **literais e nos mesmos casos**. A paridade em 100 % nas 6 fixtures é a prova |
| `_reversa_sdd/domain.md` | `#5` (Contrato de Mensagens), `#5.1` (Camada de rota) | `presença` | ❌ **Nenhuma mensagem nova.** A rota do ícone **não tem caminho de erro visível**: arte ausente devolve `404` sem corpo, e o atalho degrada para ícone genérico em silêncio (`RN-08`) |
| `_reversa_sdd/domain.md` | `#6` (Decisões Humanas Vigentes) | `presença` | ❌ O **single-tenant por aceite de risco** continua vigente (`adrs/18`), e o `BUG-20260929-BJJH` continua `active`/`mitigating` |
| `_reversa_sdd/permissions.md` | `P-01` a `P-05` | `presença` | ❌ Continua **zero** papel, **zero** sessão e **zero** autenticação. A rota nova é **pública** e não acrescenta identidade nem a exige. `P-01` segue decidida: a ausência de autenticação é **omissão**, e a correção pertence à Onda 3 |
| `_reversa_sdd/screens/golden/manifest.yaml` | as 8 entradas literais | `presença` | ❌ **INALTERADO.** O template **não foi tocado**: `git diff --stat -- src/templates` é vazio, e `GET /` devolve os mesmos 23.906 bytes e o mesmo `sha256` de antes da feature |
| `_reversa_sdd/addenda/008-persistencia-postgres-docker.md` | "O que a extração não precisa mudar" (superfície HTTP) | `regra-alterada` | A 008 declarou *"mesmas rotas, mesmos campos, mesmos status, mesmos redirecionamentos, mesmo template"*. Leia os dois juntos: esta entrega **acrescenta** uma rota e mantém as três existentes e o template **intocados**. A declaração da 008 continua valendo para tudo o que ela descrevia |
| `_reversa_sdd/addenda/006-fronteira-aplicacao-ports.md` e `007-dono-no-port-e-baseline.md` | as três portas e a costura do dono | `presença` | ❌ **Nada a reescrever.** Nenhuma porta, nenhum caso de uso e nenhum adaptador foram tocados. O `W020` (o dono não entra na chave nem no caminho) continua verdadeiro, e por um motivo mais forte: nada de armazenamento foi tocado |
| `_reversa_sdd/migration/cutover_plan.md` | "Pré-requisitos" | `presença` | ❌ **Nada muda.** Esta feature **não é uma onda** do `cutover_plan`: ela acrescenta uma rota ao `src/` atual. A Onda 3 continua **No-go**, e as dívidas **#3** e **#4** seguem **abertas** |

**Contagem por tipo:** `presença` 11 · `delta-de-contrato-externo` 1 · `contrato-alterado` 1 ·
`componente-novo` 1 · `regra-alterada` 1 — **15 impactos**.

> **Nota sobre a proporção.** Onze dos quinze impactos são `presença`, e isso **não** é
> preenchimento: numa feature cujo objetivo declarado é acrescentar sem alterar, a afirmação
> mais útil para quem lê a extração é **o que continua valendo**. Cada linha `presença` tem
> um instrumento ao lado — `diff` vazio, paridade, `sha256` da tela —, e não uma promessa.

## Regras sob vigilância

`W026` a `W030`, definidos em
`_reversa_forward/009-rota-do-apple-touch-icon/regression-watch.md`, mais as observações
`OBS-30` a `OBS-35` do mesmo arquivo.

| Item | Cobre |
|---|---|
| `W026` | O contrato HTTP com quatro linhas, e a quarta sendo imagem |
| `W027` | O template sem declarar o ícone, e `GET /` byte a byte |
| `W028` | A arte sob `src/`, e `src/static/` ausente no host e na imagem |
| `W029` | Os caminhos não servidos continuando sem resposta |
| `W030` | A arte servida continuando opaca, e a deriva continuando detectada |

**Um item merece leitura explícita.** O `W027` existe porque a tentação futura é real e
parece inofensiva: acrescentar um `<link rel="apple-touch-icon">` ao template "para
garantir". Isso **toca a tela**, contraria a `RN-02`, arranha o `W005` e não é necessário —
o caminho convencional é descoberto sem declaração. A feature foi desenhada para **não**
precisar disso, e o item registra o porquê.

## O que a extração **não** precisa mudar

- **A forma dos dados do núcleo.** O `Tree` continua a tupla de quatro elementos, e
  `path_search` e `dna_analysis` continuam devolvendo a tupla de três com o indicador de
  sucesso. `diff` vazio em `src/core/`.
- **A superfície HTTP existente.** Mesma rota de formulário, mesmos campos, mesmos status,
  mesmos redirecionamentos. A quarta linha entrou **ao lado** das três.
- **O template e as 8 telas literais.** Nenhum byte mudou. Esta entrega não declara o ícone
  no documento justamente para não tocar na tela.
- **O leiaute de `src/uploads/`.** Nenhum arquivo é renomeado ou movido, e nenhum foi.
- **As três portas e a costura do dono.** Nada de armazenamento, persistência ou caso de uso
  foi tocado.
- **Os artefatos de `migration/`.** Continuam válidos como plano de ondas futuras e **não**
  foram reescritos.

## Lacunas declaradas

Nem tudo neste adendo é afirmação verificada. O que segue é limite de conhecimento, e não
omissão:

1. **Nada foi testado em aparelho real.** A conclusão sobre a composição da transparência
   sobre preto, sobre a máscara de canto e sobre o cache agressivo do ícone de atalho vem de
   **documentação e relato de terceiros**, não de medição própria. O que foi medido nesta
   entrega é a arte (tipo de cor, dimensão, cantos, integridade do fluxo) e o comportamento
   das rotas. O procedimento para a prova em aparelho está no `onboarding.md` §8 e
   **depende do operador** (`OBS-30`).
2. **A paridade em 100 % não é conquista desta entrega.** O núcleo não foi tocado, e o `diff`
   vazio prova isso — mas a paridade foi **medida** porque uma feature que não toca o núcleo
   é exatamente o caso em que ninguém confere, e o instrumento é o que distingue "não toquei"
   de "não percebi que toquei".
3. **Uma medição falhou e quase virou resultado.** A primeira verificação manual usou uma
   ferramenta que não funciona no modo não interativo desta sessão, e o bloco de erro
   imprimiu `status= bytes=0 (304 nao traz corpo)` — que **tem a forma da resposta certa** e
   não era medição nenhuma. A medição foi refeita com outra ferramenta. Registrado em
   `evidence/T015-verificacao-manual.md` §2 porque o fragmento errado poderia ser lido como
   prova por quem encontrasse o histórico.
4. **A `RN-05` do `requirements.md` diz "cópia"** onde a decisão técnica estabelece
   **renderização derivada** (opaca, 180×180, composta sobre branco). A diferença é de
   vocabulário, não de escopo, e o `RF-10` já está escrito de forma compatível com a versão
   precisa. Declarado no `roadmap.md` §3 e **não** corrigido — o `/reversa-sync` escreve
   apenas em `addenda/`.
5. **A biblioteca de imagem usada pelos testes não está em `requirements.txt`**, que é a
   lista de **runtime**. É deliberado (`D-09`): o contêiner não precisa dela, porque a arte
   chega pronta dentro da imagem. Quem montar ambiente de teste do zero precisa instalá-la
   (`OBS-33`).
6. **Os artefatos desta feature não são lintados.** A `.markdownlint-cli2.jsonc` passou a
   ignorar `_reversa_forward/**` em 2026-10-08, por decisão de outra sessão. Um lint "limpo"
   sobre eles é **vazio**, e não aprovado (`OBS-35`).
7. **Uma sessão concorrente commitou artefatos desta feature em curso** e tocou
   `src/app.py` entre a leitura e a edição desta execução (conteúdo idêntico, `mtime`
   restaurado por commit). Nada foi causado por esta entrega e nada foi revertido.
   Registrado em `evidence/T015-verificacao-manual.md` §6.

## Fontes

- `_reversa_forward/009-rota-do-apple-touch-icon/legacy-impact.md` (fonte principal do delta)
- `_reversa_forward/009-rota-do-apple-touch-icon/regression-watch.md` (`W026` a `W030`, `OBS-30` a `OBS-35`)
- `_reversa_forward/009-rota-do-apple-touch-icon/requirements.md` (objetivo, `RN-01` a `RN-09`, `RF-01` a `RF-11`, §9 com as quatro respostas, §12 fora de escopo)
- `_reversa_forward/009-rota-do-apple-touch-icon/roadmap.md` (`D-01` a `D-10`)
- `_reversa_forward/009-rota-do-apple-touch-icon/actions.md` (15 de 15 concluídas)
- `_reversa_forward/009-rota-do-apple-touch-icon/progress.jsonl` (15 eventos)
- `_reversa_forward/009-rota-do-apple-touch-icon/data-delta.md` (sem delta de dados)
- `_reversa_forward/009-rota-do-apple-touch-icon/investigation.md` (as cinco alternativas avaliadas e as três lacunas)
- `_reversa_forward/009-rota-do-apple-touch-icon/interfaces/apple-touch-icon.md` (o contrato, primeiro do projeto)
- `_reversa_forward/009-rota-do-apple-touch-icon/evidence/` (`T003`, `T008`, `T009`, `T010`, `T011`, `T012`, `T015`)
- `_reversa_sdd/architecture.md`, `_reversa_sdd/domain.md`, `_reversa_sdd/c4-components.md`, `_reversa_sdd/permissions.md`, `_reversa_sdd/upload-gedcom/contracts.md`, `_reversa_sdd/screens/golden/manifest.yaml` (conferência de nomes de seção)

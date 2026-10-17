# Roadmap: polimento visual da tela de entrada

> Identificador: `026-polimento-visual-da-tela`
> Data: `2026-10-17`
> Requirements: `_reversa_forward/026-polimento-visual-da-tela/requirements.md`
> Confidência: 🟢 CONFIRMADO, 🟡 INFERIDO, 🔴 LACUNA

## 1. Resumo da abordagem

A feature fecha três pontos de revisão visual **sem mudar o que a tela faz**. A investigação mostrou
que dois deles já estavam decididos no legado — o ícone de atalho é descoberto por convenção
(`RN-02`/`W027`) e o `<h1>` é sempre visível desde a troca da arte em 2026-10-16 (`RN-23`) —, e que o
defeito real é de **manutenção da folha**: quatro tokens sem uso, um estado declarado com o mesmo
literal do texto neutro e dois comentários que descrevem uma arte que não existe mais.

A mudança é um patch de apresentação em **um único arquivo**, `src/assets/app.css`. Sai a família
curta `--ok/--poss/--conf/--inc`, fica a família `--st-*` que os selos já usam; `--st-inconclusivo`
mantém `#6A6150` e ganha o comentário que impede o alias com `--muted` (que daria **2,62:1** no tema
escuro); o bloco do banner passa a descrever a arte atual.

O template não é tocado: o `SHA_DA_TELA` não se move, as 8 telas literais ficam idênticas e a suíte
mantém a linha de base de **1.048 passam / 9 pulados**. A entrega documental é o adendo do
`/reversa-sync`, com as três decisões e a medição que as sustenta.

## 2. Princípios aplicados

| Princípio | Como a feature se relaciona | Status |
|-----------|------------------------------|--------|
| I. Dados reais de DNA/GEDCOM nunca entram no versionamento | A feature não lê árvore, CSV nem análise: o objeto é a folha de estilo e a documentação da decisão. Nenhum artefato carrega nome, xref ou cM | respeita |
| II. Comportamento observável é preservado em refatoração | É o eixo: nenhuma classe, nenhuma cor efetiva e nenhum texto mudam. A remoção dos tokens mortos não altera nenhuma regra aplicada — prova por `git diff --stat` e pelos testes de contraste | respeita |
| III. Nenhuma mudança sem teste que a cubra | Não há mudança de comportamento, e as duas armadilhas reais **já têm guarda**: o contraste dos selos é medido por `TestOContrasteDosSelos` (que reprova o alias no tema escuro) e a imutabilidade do documento é medida por `test_a_tela_nao_mudou_sem_mudanca_declarada` | respeita |
| IV. Arestas do grafo são tipadas | Não se aplica: nenhuma travessia, nenhum tipo de aresta e nenhum cálculo de parentesco é tocado | não se aplica |
| V. Toda suposição de genealogia genética cita a fonte | Não se aplica: nenhuma faixa de cM, limiar ou heurística é alterado | não se aplica |

## 3. Decisões técnicas

| ID | Decisão | Justificativa | Alternativas descartadas | Confidência |
|----|---------|----------------|--------------------------|-------------|
| D-01 | O **único arquivo de produção tocado** é `src/assets/app.css`. `src/templates/index.html`, `src/app.py`, `tests/` e o resto de `src/` ficam intactos | Preserva `RF-01`, `RF-02`, `RF-06`, `RF-11` e `RF-17`: o documento não muda, o `SHA_DA_TELA` (`c4a34f7b…`, 30.781 bytes) não se move e as 8 telas literais mantêm diff textual zero. Verificável por `git diff --stat` | (a) corrigir também o ponteiro do favicon no template — move o hash e exige emenda que o operador não pediu; (b) tocar só comentários e deixar os tokens mortos — não cumpre `RF-11`; (c) trocar a folha por um sistema de tokens novo — churn sem ganho e quebra a nomenclatura que os testes e a documentação citam | 🟢 |
| D-02 | **Remover** `--ok`, `--poss`, `--conf` e `--inc`; a família `--st-*` passa a ser a única declaração das quatro cores de estado | Medido: as quatro definições curtas têm **zero referências no sistema em execução** (`src/`, `tests/`, `docs/`). As 27 ocorrências de `var(--ok)` no repositório são de páginas HTML autocontidas em `_reversa_refactor/` e `_reversa_bugs/`, que **definem os próprios tokens** e não carregam `/app.css` — verificado em duas delas | (a) manter `--inc` como alias de `--st-inconclusivo` — cria dois nomes para o mesmo papel e mantém viva justamente a cor que se confunde com `--muted`; (b) tornar os nomes curtos canônicos e apontar `--st-*` para eles — mexe nas regras sem necessidade; (c) deixar tudo como está — contraria o `RF-11` e a decisão 4a da sessão de esclarecimento | 🟢 |
| D-03 | `--st-inconclusivo` **mantém `#6A6150`** e recebe, ao lado da declaração, o comentário que proíbe segui-lo de `--muted` | É o estado **inicial** e o caminho de falha do confronto (`state-machines.md#33`): "nenhum estado afirmado por omissão". Com texto branco, o selo mede **6,11:1**; se herdasse o `--muted` do tema escuro (`#A99F88`), cairia para **2,62:1**. O comentário é a defesa contra a "simplificação" que parece inofensiva | (a) `#5B6B7A` (5,48:1) — recusada na sessão de esclarecimento por introduzir matiz fora da paleta tirada da arte; (b) alias de `--muted` — reprova no contraste do tema escuro; (c) criar um tom escuro só para o selo — quatro cores novas para medir, fora do escopo | 🟢 |
| D-04 | O comentário da seção de estados passa a trazer os **quatro números medidos** (6,39 / 7,13 / 6,69 / 6,11:1) e a razão do texto branco, preservando o caso histórico do laranja (2,57:1) | É a praxe declarada do arquivo: o comentário do laranja existe para que a regra não seja desfeita por parecer gosto. Números no lugar onde a cor é editada evitam que a decisão viva só no adendo | (a) deixar os números apenas no adendo — quem edita a folha não o lê; (b) prender os números em teste — teste não explica a escolha e envelhece com o gosto | 🟢 |
| D-05 | Corrigir **os dois comentários** do bloco do banner: o que diz que "o texto dele é marrom" e o que diz que "o banner já mostra o nome" | Os dois são falsos desde a arte de 2026-10-16, que não traz texto. O `RF-06` cobre o segundo; o primeiro está no mesmo bloco e, se ficasse, manteria a explicação errada da placa branca do tema escuro. A regra da placa **permanece**: ela existe porque a arte foi desenhada para fundo claro, e não porque haja texto | (a) corrigir só o comentário do `h1` — o outro continua enganando sobre a placa; (b) remover a placa do tema escuro — a arte perderia contraste no fundo escuro; (c) remover os dois comentários — apaga a razão da regra | 🟢 |
| D-06 | **Não** criar override dos `--st-*` no tema escuro; o comentário registra que os quatro selos têm a mesma cor nos dois temas | O selo é cor cheia com texto branco nos dois temas: o par texto/fundo não depende do tema, e um override só criaria quatro cores novas para medir. Hoje o tema escuro redefine `--muted`, e é exatamente por isso que o alias é perigoso — o comentário transforma a ausência de override em decisão | (a) quatro cores escuras novas — exige medição e muda a identidade aprovada; (b) mover a cor para dentro de `@media` — mesma necessidade de cor nova | 🟢 |
| D-07 | **Nenhum teste novo** e nenhum teste editado. A verificação usa as guardas existentes | As duas armadilhas já estão presas: `TestOContrasteDosSelos` resolve o `var()` pela cascata e reprova o alias no escuro; `test_a_tela_nao_mudou_sem_mudanca_declarada` prende o documento. Um teste que exigisse a **ausência** dos quatro nomes proibiria uma reintrodução futura legítima, sem cobrir comportamento | (a) teste de ausência dos tokens — prende nomenclatura, não comportamento; (b) teste do texto dos comentários — frágil e sem valor de regressão | 🟢 |
| D-08 | O protocolo de verificação é: **diff de escopo** (`git diff --stat` só com a folha), **três arquivos de teste** (`test_estilo_da_tela`, `test_icone_de_atalho`, `test_banner_do_topo`) e **suíte completa** com linha de base 1.048/9 | O diff de escopo prova o `RF-10`/`RF-17`; os três arquivos cobrem rota da folha, contraste, hash da tela e `h1`; a suíte inteira prova o `RF-09`. Rodar só o diff não provaria o contraste, e rodar só a suíte não provaria o escopo | (a) confiar só na suíte — não mostra que o template ficou intocado; (b) confiar só no diff — não mede contraste | 🟢 |
| D-09 | A declaração da decisão (`RF-03`) é o **adendo** `_reversa_sdd/addenda/026-polimento-visual-da-tela.md`, escrito no `/reversa-sync`; não nasce um `decision.md` na pasta da feature | O canal de declaração do projeto é `_reversa_sdd/addenda/` — o próprio comentário do `SHA_DA_TELA` diz isso, e o adendo `023` é o precedente. Um arquivo novo na pasta da feature ficaria fora do canal que a extração lê | (a) `decision.md` na feature — não é lido pela extração nem pelo mini-site; (b) editar o adendo `023` — adendo é registro histórico, não se reescreve | 🟢 |

## 4. Premissas

Nenhuma premissa vem de marcador em aberto: o documento chegou ao plano com **0** marcadores, depois
da sessão de esclarecimento de 2026-10-17 (`requirements.md` §9). As quatro decisões estão fechadas.

| Premissa | Origem (`requirements.md`) | Risco se errada |
|----------|----------------------------|-----------------|
| n/a | — | — |

## 5. Delta arquitetural

| Componente | Arquivo de origem no legado | Tipo de mudança | Resumo |
|------------|------------------------------|-----------------|--------|
| Folha de estilo da tela | `_reversa_sdd/addenda/013-revisao-de-design-da-tela.md` (parte não revertida pelo `023`); `src/assets/app.css:33-35,161-166,351-353` | regra-alterada (apresentação) | Família de tokens consolidada em `--st-*`; comentário com os quatro contrastes; comentários do banner corrigidos |
| Rota `GET /app.css` | `_reversa_sdd/addenda/013-revisao-de-design-da-tela.md`; `src/app.py:472-490` | **sem mudança** | Mesmo `GET`, mesmo `text/css`, mesmo `ETag`/`304`, mesmo `404` sem corpo quando o arquivo falta |
| Template `index.html` | `src/templates/index.html:94-95,195-202` | **sem mudança** | Nenhum byte muda; `SHA_DA_TELA` e as 8 telas literais intactos |
| Testes da tela | `tests/test_estilo_da_tela.py`, `tests/test_icone_de_atalho.py`, `tests/test_banner_do_topo.py` | **sem mudança** | Nenhum teste removido, editado ou acrescentado (`D-07`) |
| Tokens derivados da extração | `_reversa_sdd/design-system/tokens-derived.md` | **sem mudança** | Artefato derivado de 2026-09-28, anterior à folha servida por rota; já não descreve o estado atual e não é regenerado por esta feature — dívida declarada |

## 6. Delta no modelo de dados

- **Nenhum campo, tabela, payload, índice ou migração.** O modelo de domínio (`data-dictionary.md`) e
  o esquema PostgreSQL de 6 tabelas não são tocados.
- O delta é de **apresentação**: quatro definições de token saem e uma declaração ganha comentário. As
  cores efetivas continuam as mesmas nos dois temas.
- Detalhe completo em: `_reversa_forward/026-polimento-visual-da-tela/data-delta.md`

## 7. Delta de contratos externos

Nenhum contrato externo muda. A rota `/app.css` continua com o mesmo método, `Content-Type`, `ETag`,
`304` e `404`; o conteúdo textual do arquivo muda, mas o contrato HTTP não. O documento servido em
`GET /` não muda. Por isso **não há diretório `interfaces/`**.

| Contrato | Tipo | Arquivo de detalhe |
|----------|------|--------------------|
| n/a — nenhum contrato HTTP, de arquivo ou de banco afetado | — | n/a |

## 8. Plano de migração

Não há migração de dados nem de configuração. O que existe é uma **ordem de execução** que impede
declarar pronto sem ter olhado o que não podia mudar.

1. **Congelar a linha de base** (`D-08`): `git status`, `git log -1` e a suíte completa, registrando
   o resultado (esperado 1.048 passam / 9 pulados) em `evidence/antes/suite.txt`.
2. **Editar a folha** (`D-02`, `D-03`, `D-04`, `D-05`, `D-06`): remover as quatro definições curtas,
   comentar o `--st-inconclusivo` e o bloco de estados, corrigir os dois comentários do banner.
3. **Rodar os três arquivos de teste** (`D-08`) e conferir que nada regrediu.
4. **Rodar a suíte completa** e comparar com o passo 1.
5. **Provar o escopo** (`D-01`): `git diff --stat` só com `src/assets/app.css`; nenhuma alteração em
   `src/templates/`, `src/app.py` ou `tests/`.
6. **Conferir na tela** (`onboarding.md`): tema claro e escuro, selo `Inconclusivo`, ícone da aba e
   ícone de atalho.
7. **Registrar** (`RF-03`): evidência na pasta da feature; adendo `026` no `/reversa-sync`.

## 9. Riscos e mitigações

| Risco | Impacto | Probabilidade | Mitigação |
|-------|---------|---------------|-----------|
| Alguém "simplificar" `--st-inconclusivo` para `var(--muted)` | alto — texto branco a 2,62:1 no tema escuro | média | `D-03` grava a proibição e o número ao lado do token; `TestOContrasteDosSelos` reprova a troca |
| Remover um token que algum consumidor externo usasse | médio — folha de estilo é pública | baixa | Medido: zero referências no sistema em execução; as 27 ocorrências do repositório são de páginas autocontidas com tokens próprios (`D-02`) |
| Mover o `SHA_DA_TELA` sem intenção ao tocar o template | médio — quebra `RF-17` e o teste de tela | baixa | `D-01` fixa a folha como único arquivo; `D-08` exige `git diff --stat` e o teste do hash |
| Corrigir só um dos dois comentários do banner | baixo — mantém uma explicação falsa | média | `D-05` nomeia os dois; o onboarding manda lê-los |
| A suíte não rodar no sandbox por falta de permissão em `tests/.tmp` | médio — verificação incompleta | média | Rodar com permissão de escrita no workspace (ou executar a suíte fora do sandbox); registrar a saída em `evidence/` |
| Alguém ler a ausência de override escuro como esquecimento | baixo — leva a "consertar" o que está certo | média | `D-06` registra a decisão no comentário do bloco de estados |

## 10. Critério de pronto

- [ ] Todas as ações do `actions.md` marcadas `[X]`
- [ ] `cross-check.md` (se executado) sem CRITICAL nem HIGH
- [ ] `regression-watch.md` gerado
- [ ] Re-extração reversa executada e sem regressão vermelha (recomendado, não obrigatório)
- [ ] `git diff --stat` lista **apenas** `src/assets/app.css` (`D-01`)
- [ ] Os quatro tokens `--ok`, `--poss`, `--conf` e `--inc` não existem mais na folha (`RF-11`)
- [ ] O comentário do bloco de estados traz os quatro números medidos (`RF-05`)
- [ ] Os dois comentários do banner descrevem a arte atual (`RF-06`)
- [ ] Suíte verde com **1.048 passam / 9 pulados**, sem teste removido (`RF-09`)
- [ ] `SHA_DA_TELA` inalterado e teste do hash verde (`RF-10`)
- [ ] Adendo `026` escrito no `/reversa-sync`, com as três decisões e a evidência (`RF-03`)

## 11. Histórico de alterações

| Data | Alteração | Autor |
|------|-----------|-------|
| 2026-10-17 | Versão inicial gerada por `/reversa-plan` | reversa |

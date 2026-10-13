# Regras sob vigilância — feature `009-rota-do-apple-touch-icon`

> Feature: `009-rota-do-apple-touch-icon`
> Data: `2026-10-08`
> Base do watch: seção "Modificadas" do `legacy-impact.md` desta feature
> Executor: `/reversa-coding`

> **IDs.** Esta feature continua a numeração do projeto: a `005-nucleo-puro-src` usou
> `W001` a `W004` e `OBS-01` a `OBS-10`; a `006-fronteira-aplicacao-ports` usou `W005` a
> `W019` e `OBS-11` a `OBS-20`; a `007-dono-no-port-e-baseline` usou `W020` a `W025` e
> `OBS-21` a `OBS-29`; a `008-persistencia-postgres-docker` **não criou item nenhum**.
> Esta feature começa em `W026`. IDs são estáveis e não se reciclam entre features.

## Itens sob vigilância

> ⚠️ **Este watch é curto, e a razão é medida, não presumida.** Das regras 🟢 do
> `_reversa_sdd/domain.md`, esta feature modificou **exatamente uma**: a contagem de linhas
> do contrato HTTP. Nenhuma regra foi removida. Os itens `W027` a `W030` **não** derivam de
> regra herdada alterada — eles vigiam **propriedades que esta entrega estabelece** e que
> uma leitura futura pode quebrar em silêncio. Estão aqui porque uma watch vazia, como a da
> feature 008, deixa o leitor sem saber o que deveria ter sido vigiado.

| ID | Origem (arquivo, seção) | Regra esperada após mudança | Tipo de verificação | Sinal de violação |
|---|---|---|---|---|
| **W026** | `_reversa_sdd/upload-gedcom/contracts.md#1` | O contrato HTTP passa a ter **quatro** linhas, e a quarta é **imagem**. A afirmação *"não há contrato JSON, redirect, `201`, `400` ou `409`"* continua **verdadeira**: a rota nova não devolve payload nem redireciona | `presença` | A rota do ícone passar a devolver JSON, redirecionar, ou responder `201`/`400`/`409`. O contrato está detalhado em `interfaces/apple-touch-icon.md`, e qualquer divergência entre ele e o código é violação |
| **W027** | `src/templates/index.html` + `RF-05` | O template **não** declara o ícone de atalho, e `GET /` continua **byte a byte** o mesmo (23.906 bytes, `sha256` `4b7f0b0c…`) | `presença` | `test_a_tela_nao_mudou_um_byte` ou `test_a_tela_nao_declara_o_icone_de_atalho` falha. A tentação futura é acrescentar um `<link rel="apple-touch-icon">` "para garantir": isso toca o template, contraria a `RN-02` e arranha o `W005` |
| **W028** | `src/assets/`, `.dockerignore`, `W004` (003) | A arte de runtime mora sob **`src/`** e `src/static/` continua **ausente**, no host e dentro da imagem | `presença` | `src/static/` reaparece, ou a arte muda para fora de `src/`. A segunda forma é a pior: responde `200` no host e `404` no contêiner, e **nenhum teste de host pega** — só a conferência dentro da imagem (`T008`) |
| **W029** | `RN-09`, `RF-11` | Os caminhos **não** servidos continuam sem resposta: `/apple-touch-icon-precomposed.png` e `/favicon.ico` seguem devolvendo `404` | `ausência` | Qualquer um dos dois passa a responder. É a reabertura da **dívida #17** — *"superfícies de compatibilidade reexportando nomes históricos que ninguém usa"*. O alias legado pertence a sistemas anteriores, e o navegador só busca `favicon.ico` quando o documento **não** declara ícone |
| **W030** | `RN-04`, `tests/icone_de_atalho.py`, `tests/test_deriva_da_arte.py` | A arte servida continua **opaca** (tipo de cor **2**, 180×180, 16.504 bytes) e a deriva contra a canônica continua **detectada** | `presença` | O tipo de cor vira **6** (canal alfa presente) — o ícone fica com fundo preto no aparelho. Ou o teste de deriva passa a comparar **bytes**, e passa a dar alarme falso a cada recompressão (`D-08`) |

## Observações

> Sem peso de regressão. O que **não** era 🟢 fica aqui. Registrado porque uma leitura
> futura precisa saber que existe.

| ID | Observação | Por que importa |
|---|---|---|
| `OBS-30` | **Nada foi testado em aparelho real.** A composição de transparência sobre preto, a máscara de canto e o cache agressivo do ícone de atalho vêm de documentação e de relato de terceiros | `investigation.md` §6.1. O `onboarding.md` §8 traz o procedimento, e ele **depende do operador**. Enquanto não for feito, a paridade visual do atalho está especificada e **não provada** |
| `OBS-31` | **A arte canônica (`docs/assets/img/logo.png`) não entra no contexto de build.** O `.dockerignore` é lista de permissão e só admite `requirements.txt` e `src/**` | É a razão de a arte derivada ser **commitada** (`D-02`) em vez de gerada em tempo de execução. Quem tentar "simplificar" gerando dentro do contêiner vai descobrir que a fonte não está lá |
| `OBS-32` | **O ícone da aba responde por 81 % de cada página.** Medido: 19.298 dos 23.906 bytes de `GET /` são o `data URI` embutido | Registrado em `requirements.md` **§12 Fora de escopo** como candidato a feature própria. Não é dívida desta entrega, e não foi tocado |
| `OBS-33` | **A biblioteca de imagem é dependência de TESTE e não está em `requirements.txt`.** Ela existe no `.venv/`, que é o interpretador oficial | `D-09`. O container não precisa dela. Quem montar ambiente de teste do zero precisa instalá-la, e a suíte falha alto se ela faltar |
| `OBS-34` | **O `interfaces/` desta feature é o primeiro do projeto.** Nenhuma feature anterior criou contrato externo novo | Se a rota mudar de caminho, de tamanho ou de política de cache, é `interfaces/apple-touch-icon.md` que acompanha. É a primeira vez que o projeto tem um documento com essa responsabilidade |
| `OBS-35` | **A `.markdownlint-cli2.jsonc` passou a ignorar `_reversa_forward/**`** em 2026-10-08, por decisão de outra sessão | Consequência prática: os artefatos desta feature **não são lintados**. Um lint "limpo" sobre eles é **vazio**, e não aprovado. Registrado para que a ausência de avisos não seja lida como qualidade |

## Histórico de re-extrações

### Re-extração 2026-10-13 13:32 (verificação suplementar)

**Verificação suplementar, sem regeneração de spec:** o `_reversa_sdd/` é o de 2026-10-10; o que mudou desde então foi o **código**, e é o código de hoje que está medido. Suíte: **605 passam / 9 pulados / 0 falham**. Paridade: **100 %, exit 0, 6/6 fixtures** (`tests/rodar_paridade.py`).

**Segunda verificação real destes watch items.**

| ID | Veredito | Observação |
|----|----------|------------|
| W026 | 🟢 verde | A rota serve o ícone por `send_file(caminho, mimetype="image/png")` e nenhuma rota de arte responde `201`/`409` nem redireciona (medido). |
| W027 | 🟢 verde | O template **não** declara `apple-touch-icon` (**0 ocorrências**) e `test_a_tela_nao_mudou_um_byte` passa na suíte de hoje — o hash de referência foi atualizado junto com a tela de 2026-10-12, como o próprio teste exige. |
| W028 | 🟢 verde | `src/static/` **não existe** e a arte de runtime está em `src/assets/` (`app.css`, `apple-touch-icon.png`, `banner-da-tela.png`) — medido no host. |
| W029 | 🟢 verde | **Zero** rotas para `favicon.ico` e `apple-touch-icon-precomposed.png` (medido em `src/app.py`). |
| W030 | 🟢 verde | Medido no arquivo: **180×180, tipo de cor 2 (sem alfa), 16.504 bytes**; a deriva continua comparada por **pixel**. |

### Re-extração 2026-10-10 21:40

**Primeira verificação real destes watch items.**

| ID | Veredito | Observação |
|----|----------|------------|
| W026 | 🟡 amarelo | **A essência vale; a forma mudou por reorganização deliberada.** A afirmação *"não há contrato JSON, redirect, `201`, `400` ou `409`"* continua **verdadeira** e está declarada em três artefatos regenerados (`upload-gedcom/contracts.md` §1, `tela-de-entrada/contracts.md` §1 e `recursos-da-tela/contracts.md` §1). O que mudou é que as **duas rotas de arte deixaram de ser uma linha do contrato de upload**: viraram uma **unit própria** (`recursos-da-tela`), com `contracts.md` e entrada no `openapi/index.yaml`. A contagem "quatro linhas" descreve a organização anterior. **Não é regressão.** |
| W027 | 🟡 amarelo | **A regra substantiva vale; o literal está superado por decisão.** Medido: o template **não** declara o ícone de atalho (zero ocorrências de `apple-touch-icon`). Mas o `GET /` **não** é mais o de 23.906 bytes: a tela mudou **três vezes em 2026-10-10**, por decisões registradas (`T036`→`T044` da masthead), e o `sha256` de referência do teste é hoje `17240e5a…`. A "tentação futura" que este item vigia — acrescentar um `<link rel="apple-touch-icon">` — **não** aconteceu. |
| W028 | 🟢 verde | `src/static/` **não existe** e a arte mora em `src/assets/` (medido). `recursos-da-tela/requirements.md` (`BR-E-22`, `BR-E-23`) e o teste de deriva guardam a proibição. |
| W029 | 🟢 verde | Nenhuma rota para `favicon.ico` nem para `apple-touch-icon-precomposed.png` (zero ocorrências em `src/app.py`). `BR-E-09`; `TT-08`. |
| W030 | 🟢 verde | **Medido no arquivo:** 180×180, **tipo de cor 2** (truecolor sem alfa) e **16.504 bytes**. A deriva é comparada por **pixel**, nunca por bytes (`BR-E-27`). |

> Preenchido pelo agente reverso quando o `/reversa` rodar de novo. Vazio por enquanto.

| Data | Re-extração | `W026` | `W027` | `W028` | `W029` | `W030` |
|---|---|---|---|---|---|---|
| — | — | — | — | — | — | — |

## Arquivadas

> Itens que deixaram de valer, com a data e o motivo. Vazio por enquanto.

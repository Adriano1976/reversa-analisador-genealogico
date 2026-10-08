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

> Preenchido pelo agente reverso quando o `/reversa` rodar de novo. Vazio por enquanto.

| Data | Re-extração | `W026` | `W027` | `W028` | `W029` | `W030` |
|---|---|---|---|---|---|---|
| — | — | — | — | — | — | — |

## Arquivadas

> Itens que deixaram de valer, com a data e o motivo. Vazio por enquanto.

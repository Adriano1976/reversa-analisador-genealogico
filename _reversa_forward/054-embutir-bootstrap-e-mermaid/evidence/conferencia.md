# Conferência da entrega — feature 054

> Data: `2026-10-31`. Complementa o `onboarding.md`, que é o roteiro para o operador.

## 1. O que foi verificado por execução

### 1.1 Toda referência da tela resolve pela própria aplicação

Script que lê o HTML de `GET /`, extrai **todas** as tags `href`/`src` e todas as `url()` da folha de
fontes, e pede cada caminho de volta ao servidor. Resultado: **18 recursos, 18 com `200`**, e **zero**
referências externas (`externos: []`).

Isso é a garantia estrutural do "sem internet": se o documento não aponta para fora, a ausência de rede
não remove estilo, script nem fonte.

### 1.2 Os bytes são os oficiais

`tests/test_recursos_embutidos.py` prende o `sha256` dos três arquivos de biblioteca contra o valor
medido no download; `tests/test_fontes_da_tela.py` prende os 11 `woff2` e a estrutura da folha (45
blocos, ASCII, só caminhos locais).

### 1.3 As telas de identidade continuam sem a webfont

`tests/test_tela_sem_origem_externa.py` confere o documento servido de `/login`, `/cadastro` e
`/recuperar-senha`, e a fonte da base das seis telas: nenhuma referência a `/fontes.css` e nenhuma tag
externa. A tipografia delas continua a de hoje (`Georgia`/`system-ui`), como a decisão `L-02` fixou.

### 1.4 Dentro da imagem do contêiner

`docker compose run --rm -v ./tests:/app/tests -e ANALISADOR_MODO_TESTE=1 -e ANALISADOR_UPLOAD_FOLDER=/tmp/uploads-verificacao app python tests/verificacao_no_conteiner.py`

Resultado: **19 verificações executadas, 0 falhas, 1 pulada** (a gravação no banco, que sem
`DATABASE_URL` é pulada por decisão `D-17`). As 18 rotas de recurso responderam `200` com o tipo de
mídia certo e o `sha256` do arquivo na imagem; `GET /` respondeu `200` com 51.218 bytes.

> Nota de honestidade: rodando **com** o modo de identidade (o padrão do `compose`), `GET /` responde
> `302` para `/login`, porque a verificação não autentica — comportamento pré-existente da feature 051,
> não da 054. Por isso a rodada registrada acima usa o escape de teste.

### 1.5 A suíte e a paridade

- Suíte: **2.002 passam, 9 pulados, 5 falham** — as cinco falhas são exatamente as pré-existentes da
  linha de base (quatro de `test_characterization_mermaid` e o literal `1. Lista de Matches (CSV)` de
  `test_tres_fases_da_tela`). São **94 testes novos** passando.
- Paridade: **30 divergências**, o mesmo número da linha de base de 2026-10-30; nenhuma nova.
- `SHA_DA_TELA`: `577a17fd…` (51.612) → `3487986a…` (51.218), delta registrado em
  `evidence/SHA_DA_TELA.md`.

## 2. O que **não** foi verificado por execução, e fica para o operador

O ambiente do agente não tem navegador. A conferência visual com a rede desligada — o olho no desenho,
nas abas alternando e no diagrama — é do operador, pelo roteiro de `onboarding.md` seções 3 a 5. O que
pode ser dito com segurança é o que os testes provam: o documento não referencia host externo, todos os
recursos respondem, a configuração do Mermaid não mudou, e a ordem das folhas e dos scripts está
preservada.

## 3. Pendência registrada

- A conferência humana offline **não foi executada** nesta rodada (sem navegador no ambiente). Ela é
  item do critério de pronto da feature e do `onboarding.md`. Enquanto não houver o registro do
  operador em `evidence/`, o item permanece aberto — e isso é uma pendência declarada, não um sucesso
  presumido.

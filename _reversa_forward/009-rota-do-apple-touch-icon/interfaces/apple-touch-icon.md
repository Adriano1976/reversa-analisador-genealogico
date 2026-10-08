# Interface: ícone de atalho — `GET /apple-touch-icon.png`

> Feature: `009-rota-do-apple-touch-icon`
> Data: `2026-10-08`
> Tipo de contrato: **HTTP**
> Posição no contrato existente: **quarta linha** de `_reversa_sdd/upload-gedcom/contracts.md#1`
> Confidência: 🟢 CONFIRMADO, 🟡 INFERIDO, 🔴 LACUNA

> **Este é o primeiro `interfaces/` do projeto.** Nenhuma feature anterior criou um contrato
> externo novo: a 006 e a 007 moveram orquestração e assinatura sem mudar a superfície, e a 008
> acrescentou persistência **atrás** da rota, declarando explicitamente "mesmas rotas, mesmos
> campos, mesmos status, mesmo template". Esta feature acrescenta uma rota, e é isso que torna
> o diretório devido.

## 1. Requisição

| Item | Valor |
|---|---|
| Método | **`GET`** apenas |
| Caminho | `/apple-touch-icon.png` |
| Corpo | **nenhum** |
| Parâmetros de consulta | **nenhum** — nenhum é lido, nem para ser ignorado |
| Campos de formulário | **nenhum** |
| Cabeçalhos exigidos | **nenhum** |
| Autenticação | **nenhuma** — o sistema não tem identidade (`_reversa_sdd/permissions.md` `P-01` a `P-05` continuam sem papel, sem sessão e sem autenticação) |
| Entrada do cliente usada para compor caminho | **nenhuma, por construção** (`D-06`) |

## 2. Resposta `200`

| Item | Valor |
|---|---|
| Tipo de conteúdo | `image/png` |
| Corpo | PNG de **180×180**, **opaco** — nenhum pixel com transparência |
| Tamanho do corpo | **16.504 bytes** — valor medido da receita de `D-02` executada sobre a arte canônica (compor sobre branco, reamostrar para 180×180, PNG otimizado). É 21 % menor que os 20.954 bytes da mesma arte **transparente**, porque o fundo branco chapado comprime melhor |
| Fundo | branco sólido `#ffffff` |
| Cantos | **retos** — a máscara é aplicada pelo sistema que consome |
| Marca de versão | cabeçalho de versão por conteúdo do próprio conteúdo (`ETag`) |
| Data de modificação | cabeçalho de última modificação (`Last-Modified`) |
| Validade declarada | **nenhuma validade longa.** Nenhuma resposta declara validade superior a um dia |

## 3. Resposta `304` — requisição condicional

Quando o cliente reenvia a marca de versão que já recebeu, a resposta é de **conteúdo não
modificado**, **sem corpo**. É o comportamento que o `RF-07` exige: a revalidação é barata e a
troca de arte é vista assim que acontece.

## 4. Erros

| Situação | Status | Corpo | Observação |
|---|---|---|---|
| Arte ausente no disco | `404` | vazio | Não é caminho de falha visível: o cliente degrada para ícone genérico (`RN-08`). Nenhuma mensagem ao operador é produzida |
| Método diferente de `GET` | `405` | vazio | Sai do próprio roteador, por a rota estar registrada só com `GET` (`D-07`) |

> ⚠️ **Nenhuma recusa de negócio existe aqui.** As três linhas atuais do contrato concentram a
> regra de que *toda recusa de negócio é HTML com status `200` e `success=false`*, e a única
> recusa de transporte é o `413`. Esta linha **não tem negócio**: não há entrada a validar, e
> portanto não há recusa de negócio a representar.

## 5. Idempotência e efeitos

- **Leitura pura.** Nenhuma escrita, nenhum estado criado, nada guardado entre requisições.
- **Idempotente por natureza:** duas requisições iguais produzem a mesma resposta, e nenhuma
  delas altera o sistema.
- **Sem concorrência a considerar:** o recurso é **imutável** durante a execução do processo.

## 6. Tempos limite

**n/a.** Não há dependência externa, não há espera, não há tentativa. O arquivo é local ao
processo.

## 7. O que este contrato **não** inclui

- **Não** inclui o caminho legado com o mesmo nome e o sufixo de compatibilidade. Ele continua
  respondendo que o recurso não foi encontrado, e a `RN-09` registra o motivo: nenhum sistema
  atual o requisita, e criá-lo repetiria a dívida #17.
- **Não** inclui o caminho do ícone de aba. Ele continua sendo servido **dentro do documento**,
  como `data URI`, e essa decisão permanece: é a forma que respeita a rota única e o `W004`.
- **Não** inclui manifesto de aplicação web. A alternativa foi avaliada e rejeitada em
  `investigation.md` §3.2, porque exigiria tocar no template.

## 8. Relação com as três linhas existentes do contrato

| Linha | Status depois desta feature |
|---|---|
| `GET /` → `200` HTML da tela | **inalterada, byte a byte** (`RF-05`, `RN-02`) |
| `POST /` `action=upload_gedcom` → `200` | **inalterada** |
| `POST /` acima de 16 MB → `413` | **inalterada** |
| **`GET /apple-touch-icon.png` → `200` imagem** | **nova** |

## 9. Fontes

- `_reversa_sdd/upload-gedcom/contracts.md#1` (o contrato HTTP existente, com três linhas)
- `_reversa_sdd/addenda/008-persistencia-postgres-docker.md` ("mesmas rotas, mesmos campos,
  mesmos status, mesmos redirects, mesmo template")
- `_reversa_sdd/domain.md#5.1` (as dez mensagens da camada de rota, **nenhuma** das quais muda)
- `_reversa_sdd/permissions.md` (`P-01` a `P-05`: zero autenticação)
- `_reversa_forward/009-rota-do-apple-touch-icon/requirements.md` (`RF-01`, `RF-02`, `RF-03`,
  `RF-06`, `RF-07`, `RF-11`, `RN-08`, `RN-09`)
- `_reversa_forward/009-rota-do-apple-touch-icon/roadmap.md` (`D-04`, `D-05`, `D-06`, `D-07`)

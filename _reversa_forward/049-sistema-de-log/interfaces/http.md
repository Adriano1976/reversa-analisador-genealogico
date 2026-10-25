# Interface: HTTP — cabeçalho `X-Request-ID` e mensagens de erro

> Identificador: `049-sistema-de-log`
> Data: `2026-10-25`
> Contratos afetados: **toda** resposta da aplicação (cabeçalho novo) e **três** respostas de erro
> (texto). Nenhum código de situação muda.

## 1. Cabeçalho `X-Request-ID`

### Requisição

O cliente **não** envia nada. Se enviar, o valor é ignorado (`RF-03`): aceitar identificador do
cliente permitiria injetar texto arbitrário no arquivo de log, e o valor não é usado para nada
além de correlação.

### Resposta

| Item | Valor |
|---|---|
| Nome | `X-Request-ID` |
| Formato | 8 caracteres hexadecimais minúsculos (`[0-9a-f]{8}`) |
| Unicidade | por requisição; duas requisições seguidas têm valores diferentes |
| Presença | em **toda** resposta, inclusive `404`, `413` e `400` |

Rotas cobertas, sem exceção:

| Método | Caminho | Origem no legado |
|---|---|---|
| `GET` | `/` | `src/app.py` (`index`) |
| `POST` | `/` (5 ações: `upload_gedcom`, `aposentar_arquivo`, `selecionar_arvore`, `dna_analysis`, `path_search`) | `src/app.py` (`_ACOES_PRE_ARVORE` / `_ACOES_COM_ARVORE`) |
| `GET` | `/apple-touch-icon.png` | `src/web/rotas_assets.py` |
| `GET` | `/banner.png` | `src/web/rotas_assets.py` |
| `GET` | `/app.css` | `src/web/rotas_assets.py` |
| `POST` | `/descartes.csv` | `src/web/rotas_assets.py` |

### O que **não** muda

- Corpo da resposta: byte a byte o mesmo (o cabeçalho é acrescentado depois da renderização).
- `ETag` e `304` das duas artes: o `send_file` continua sendo o dono desses cabeçalhos.
- `200`, `201`, `304`, `400`, `404`, `413`, `405`: nenhum código novo, nenhum removido.
- `X-Frame-Options: DENY`, que já era emitido por `after_request`
  (`src/app.py:_sem_enquadramento_por_terceiro`).

### Idempotência

`GET` continua idempotente. O identificador é **diferente** a cada requisição, inclusive em
repetição idêntica de `GET` — ele identifica a **requisição**, não o recurso. Nenhum cache é
alterado por causa dele.

## 2. As três mensagens de erro de tela

Só estas três mudam. Todas pertencem ao `except Exception` genérico — ou seja, à exceção
**inesperada**. As mensagens de erro de domínio (`src/application/traducao.py`) **não** mudam.

| # | Origem no legado | Antes | Depois |
|---:|---|---|---|
| 1 | `src/app.py:397` | `Erro ao processar GEDCOM: {e}` | `Erro ao processar GEDCOM: O detalhe foi registrado no log.` |
| 2 | `src/app.py:529` | `Ocorreu um erro: {e}` | `Ocorreu um erro: O detalhe foi registrado no log.` |
| 3 | `src/app.py:580` | `Ocorreu um erro: {e}` | `Ocorreu um erro: O detalhe foi registrado no log.` |

### Por que o prefixo é preservado

O harness de paridade classifica o desfecho pelo **modo**, não pela redação:
`modo()` testa `"Ocorreu um erro" in m or "Erro ao processar GEDCOM" in m`
(`_reversa_sdd/parity/harness.py:185`). Com o prefixo intacto, a categoria continua `erro` e as
fixtures continuam comparáveis; a diferença de redação não entra na comparação.

### O que acompanha a mudança

| Item | Ação |
|---|---|
| Traceback | passa a ser registrado no log com o identificador da requisição |
| Golden de tela | atualizar **se** algum golden capturar um destes três textos (verificar antes) |
| `tests/test_upload_seguranca.py:428` | afirma ausência de `"Ocorreu um erro"` no **caminho feliz**; segue válido |
| `tests/test_traducao_de_erros.py` | **não muda**: mede as mensagens de domínio, não o `except` genérico |

## 3. Erros, tempo e idempotência dos fluxos de auditoria

A auditoria **não** vira contrato HTTP:

- falha ao escrever o arquivo de auditoria **não** muda a resposta (o operador recebe o resultado da
  operação, como hoje) e não é silenciosa: vira aviso único no console (`D-11` do `roadmap.md`);
- não há timeout, retentativa nem fila: a linha é escrita na mesma requisição;
- a trilha é *append-only*; nenhuma leitura da trilha pela aplicação existe nesta entrega.

## 4. Versionamento

Nenhuma versão de API é declarada no projeto e nada aqui a introduz. O cabeçalho é aditivo e
ignorável por qualquer cliente; a mudança de texto é a única alteração perceptível por quem lê a
tela, e é a `RN-06` do `requirements.md`.

# Regression watch: login com Google e isolamento por dono

> Identificador: `051-login-google-e-isolamento`
> Data: `2026-10-27`
> O que vigiar nas próximas extrações e entregas. Cada item nasce de uma regra **Modificada** no
> `legacy-impact.md`; regras que já eram 🟡 ou 🔴 vivem em "Observações", sem peso de regressão.

| ID | Origem (arquivo, seção) | Regra esperada após a mudança | Tipo de verificação | Sinal de violação |
|---|---|---|---|---|
| W001 | `permissions.md#3`, `domain.md#3.6` | A listagem de um dono não mostra arquivo de outro | presença | Um `os.listdir` na raiz sem o dono, ou um teste em que B vê o rótulo de A |
| W002 | `permissions.md#4.3`, `domain.md#3.5` | A referência resolve apenas dentro do dono; a de outro devolve `None` | presença | `resolver`/`carregar` aceitando foto de referência de outro dono |
| W003 | `domain.md#3.5` (`RN-14`) | Aposentar move só o arquivo do dono da sessão | presença | Aposentar de A removendo o arquivo de B |
| W004 | `migration/risk_register.md#RISK-005` | Recurso de outro dono responde `404`, nunca `403`, com o texto de inexistência | presença | Qualquer `403`, ou texto que revele a existência do recurso |
| W005 | `permissions.md#1.1` | O mesmo conteúdo por dois donos gera dois arquivos | presença | `guardar` devolvendo o mesmo caminho para donos diferentes |
| W006 | `domain.md#5` | Os 29 literais de tela continuam intactos; os novos são acréscimo | redação | Um literal antigo alterado, ou um texto de recusa novo para dono alheio |
| W007 | `architecture.md#1` | Sem autenticação injetada, o comportamento é o de antes (sem guarda, `/login` 404) | presença | A suite ou a paridade recebendo `302` no `GET /` |
| W008 | `tests/test_icone_de_atalho.py#L189` | `SHA_DA_TELA` mede a tela vazia com a entrada DESLIGADA | presença | Hash atualizado sem a medição declarada, ou a masthead mudando sem o hash |
| W009 | `addenda/049-sistema-de-log.md`, `RN-12` | A trilha identifica a conta pelo `sub` e nunca grava o e-mail | presença | `@` em linha de auditoria, ou `conta=` ausente em `acao=entrar` |
| W010 | `RN-16`, `D-10` | Faltando qualquer uma das cinco variáveis, o servidor não sobe e a mensagem as nomeia | presença | Subida em modo legado com a configuração incompleta |

## Observações

- **Pré-existente, não desta feature:** `tests/test_characterization_mermaid.py` tem 4 testes vermelhos no `HEAD` limpo (medido em worktree separado). Não foram tocados e não são regressão desta entrega.
- **Layout do dono legado:** a raiz da pasta de upload continua sendo o espaço do dono `"unico"`, o único que existe sem sessão. Uma extração futura deve ler isso como **exceção declarada**, não como ausência de isolamento.
- **`owner_id` continua `TEXT` e sem FK:** a lacuna `E-06` do `erd-complete.md` permanece aberta, agora com o conteúdo certo (o `sub`).
- **A entrada aberta não tem limite de criação de contas** e a aplicação não tem token CSRF por formulário (`SameSite=Lax` apenas). Os dois estão declarados no `requirements.md` e no `roadmap.md`.

## Histórico de re-extrações

## Arquivadas

# Regression watch: identidade local com senha

> Identificador: `053-conta-com-senha-e-recuperacao`
> Data: `2026-10-30`

Cada item abaixo nasce de uma regra **modificada** no `legacy-impact.md`. O sinal de violação é o que a
próxima extração reversa deve conseguir observar sem ler este documento.

| ID | Origem (arquivo, seção) | Regra esperada após a mudança | Tipo de verificação | Sinal de violação |
|---|---|---|---|---|
| W001 | `_reversa_sdd/permissions.md#4.3` | A autenticação tem **duas** formas: conta Google e credencial local confirmada; as duas produzem o mesmo `sub` canônico por pasta | presença | Rota de identidade que aceite sessão sem `sub`, ou conta local que grave em pasta diferente da do `sub` |
| W002 | `_reversa_sdd/addenda/051-login-google-e-isolamento.md` | O caminho Google continua funcionando sem a credencial local, com as três frases de falha e o `?iniciar=1` | presença | `GET /login?iniciar=1` deixar de redirecionar, ou as três frases sumirem da tela |
| W003 | `_reversa_sdd/domain.md#5` | Os 36 literais anteriores continuam intactos; os novos são os da `RN-13` | redação | Qualquer literal anterior alterado, ou texto de tela novo fora do catálogo |
| W004 | `src/web/sessao.py` | A sessão carrega a versão de credencial e a guarda recusa versão anterior | presença | Sessão emitida antes de uma redefinição continuar autenticando |
| W005 | `src/utils/auditoria.py` | O conjunto de ações inclui `cadastrar`, `confirmar`, `definir_senha`, `pedir_senha` e `redefinir_senha`, e a linha nunca carrega e-mail, senha ou token | presença | Ação de identidade fora do conjunto, ou linha de auditoria com `@`, senha ou token |
| W006 | `.gitignore` · `docker-compose.yml` | O arquivo `src/dados/contas.json` fica fora do versionamento e tem volume próprio no contêiner | presença | `git status` listando `src/dados/`, ou contêiner recriado sem o volume |
| W007 | `_reversa_sdd/domain.md#3.6` | O cadastro deslogado **nunca** altera conta existente, e a tela não revela quem tem conta | ausência | Cadastro com e-mail existente criando credencial, ou resposta diferente para e-mail cadastrado |
| W008 | `tests/test_icone_de_atalho.py` | `SHA_DA_TELA` continua medindo a tela vazia sem entrada; o bloco da conta não é renderizado sem sessão | ausência | Hash da tela mudando sem mudança declarada na tela principal |

## Histórico de re-extrações

_(vazio — preenchido pelo agente reverso quando rodar `/reversa` de novo)_

## Arquivadas

_(vazio)_

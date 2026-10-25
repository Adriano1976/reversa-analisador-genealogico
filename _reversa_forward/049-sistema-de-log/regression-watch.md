# Regression Watch: sistema de log completo

> Identificador: `049-sistema-de-log`
> Data: `2026-10-25`
> Itens abaixo derivam das regras **🟢 confirmadas** que a feature alterou ou removeu
> (`legacy-impact.md` §4). O que era 🟡 ou 🔴 está em "Observações", sem peso de regressão.

## Watch principal

| ID | Origem (arquivo, seção) | Regra esperada após mudança | Tipo de verificação | Sinal de violação |
|---|---|---|---|---|
| W001 | `_reversa_sdd/domain.md#5` (Contrato de Mensagens); `src/app.py:397,529,580` | As três respostas de exceção inesperada terminam em "O detalhe foi registrado no log." e **nenhuma** interpola o texto da exceção | `redação` | Qualquer das três voltar a conter `{e}` ou o texto interno de uma exceção |
| W002 | `_reversa_sdd/questions.md#pergunta-14`; `_reversa_sdd/gaps.md#5-fechadas-nesta-rodada--21-lacunas` | As **duas** tentativas de aposentar gravam linha na trilha, com desfechos distintos (`sucesso` / `falha`) | `presença` | Aposentar arquivo inexistente sem linha em `analisador.auditoria.*.log` |
| W003 | `.reversa/principles.md#i`; `_reversa_sdd/architecture.md#6` | Nenhum dos três destinos carrega nome de pessoa, rótulo visível de arquivo, e-mail ou identificador de kit — **inclusive no traceback** | `presença` (ausência) | Um nome real da árvore, um e-mail ou um `[A-Z]{2}\d{7}` aparecendo em amostra de log |
| W004 | `_reversa_sdd/tela-de-entrada/requirements.md#requisitos-não-funcionais` | Toda ação que mexe em arquivo ou produz resultado deixa linha: envio (3 desfechos), substituição de CSV, aposentar (2), análise e busca | `presença` | Fluxo concluído sem linha de auditoria correspondente |
| W005 | `_reversa_sdd/architecture.md#2` | O identificador da requisição sai no cabeçalho `X-Request-ID`, é **gerado** pelo servidor (nunca aceito do cliente) e casa com a linha de acesso | `presença` | Resposta sem o cabeçalho, duas requisições com o mesmo valor, ou valor forçado pelo cliente aceito |
| W006 | `_reversa_sdd/c4-containers.md` | A trilha de auditoria **não propaga** para o arquivo geral nem para o console; a auditoria grava um arquivo por dia e **não** descarta por tamanho | `presença` | Linha de auditoria duplicada no arquivo geral, ou trilha rotacionada por tamanho |
| W007 | `_reversa_sdd/domain.md#5` (`RN-18`, mensagens de erro previsto) | As mensagens de erro de **domínio** (`application/traducao.py`) continuam idênticas, com o mesmo par (mensagem, status) | `redação` | Mudança de literal em `traducao.py`, ou alteração de status na tabela |
| W008 | RNF "Observabilidade" das 5 units | Os artefatos da extração deixam de afirmar "nenhum log, métrica ou trace" e passam a declarar os três destinos e a auditoria | `presença` | Uma unit voltar, numa re-extração, a afirmar ausência total de observabilidade |
| W009 | `_reversa_sdd/arquitetura` (`ADR-34`, direção de dependência) | `utils/logs.py` continua folha: **não** importa `core/`, `application/`, `ports/` nem `web/` | `presença` | Um `from core` / `from ports` dentro de `utils/logs.py` ou `utils/auditoria.py` |

## Observações (sem peso de regressão)

- 🟡 **Retenção da auditoria é declarada, não mecanizada.** O prazo de 90 dias está na `RN-10` e
  nada o faz cumprir: não há aviso, não há expurgo automático. Um revisor deve tratar isso como
  **decisão declarada**, não como defeito de implementação.
- 🟡 **A pasta de log não está no `.gitignore`.** T022 foi recusada pela política de edição do
  legado. Enquanto durar, rodar a aplicação no repositório cria `logs/` não versionado — o
  `.dockerignore` já a exclui do contexto de build por ser lista de permissão.
- 🟡 **A máscara cobre dois padrões, e só dois.** Foi decisão: heurística por palavra atrapalharia
  o diagnóstico. Nome de pessoa **não** é mascarado — ele é proibido na origem (`RN-05`), e o
  teste de privacidade vigia a proibição, não a máscara.
- 🟡 **Divergência de paridade pré-existente, medida em 2026-10-25:** a paridade acusa **30
  divergências** no bloco `ancestral` (`oraculo=[None, None]` contra um caminho no candidato). O
  mesmo resultado foi obtido em checkout limpo do `HEAD` (`344bfbd`), **sem** nenhuma alteração
  desta feature — portanto não é regressão da 049. Fica para o `/reversa-audit` decidir se é
  defeito do harness (o coletor do oráculo devolve `None` para todos os pares) ou mudança de
  comportamento de `find_ancestral_path` que nenhuma extração registrou.
- 🟡 **O log do servidor HTTP foi silenciado no nível informativo** (`waitress` → `WARNING`). Se
  alguém procurar a linha de acesso original do servidor, ela não está mais lá: a linha própria
  a substitui, e é ela que carrega o identificador.

## Histórico de re-extrações

| Data | Re-extração | Resultado |
|---|---|---|
| — | — | Ainda não houve re-extração depois desta entrega |

## Arquivadas

| ID | Motivo | Data |
|---|---|---|
| — | Nenhum item arquivado | — |

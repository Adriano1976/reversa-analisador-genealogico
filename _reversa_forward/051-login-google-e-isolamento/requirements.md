# Requirements: login com Google e isolamento por dono

> Identificador: `051-login-google-e-isolamento`
> Data: `2026-10-26`
> Pasta da extração reversa: `_reversa_sdd/`
> Confidência: 🟢 CONFIRMADO, 🟡 INFERIDO, 🔴 LACUNA / DÚVIDA
> Entrada do pedido: `D:\Autenticação com Google OAuth — Onda 3.md`, conferido contra a árvore em `21a259f` (2026-10-26, árvore limpa).

## 1. Resumo executivo

O sistema analisa árvores genealógicas e relatórios de DNA — dado pessoal sensível, inclusive de pessoas vivas — sem nenhuma identidade: quem alcança a porta entra, e a chave de conteúdo entregue no formulário decide qual árvore abre (`permissions.md#4.3`). Esta feature põe a conta Google do operador — e de qualquer outra conta que se autentique — como identidade de entrada e transforma o campo `dono`, hoje uma costura de assinatura sem comportamento, no escopo efetivo do dado: a árvore que um dono envia deixa de existir para qualquer outro, e a recusa é a mesma de arquivo inexistente.

Para o operador, a tela passa a pedir entrada antes de qualquer uso e a mostrar só os próprios arquivos; para a instalação, cada conta ganha o seu espaço, o que **encerra o aceite de risco single-tenant** (`permissions.md#5.4`) — e só depois do teste negativo de `404` que o alvo exige como portão (`migration/risk_register.md#RISK-005`). Fica fora: senha própria, papéis e permissões diferenciadas, e retenção, expurgo e consentimento do dado persistido (Onda 5).

## 2. Contexto a partir do legado

| Fonte | Trecho relevante | Confidência |
|-------|------------------|-------------|
| `_reversa_sdd/permissions.md#1` | Varredura de `src/`: zero `login`, `password`, `role`, `token`; `flask.session` nunca importado; a borda importa só `Flask`, `render_template`, `request` e `send_file` | 🟢 |
| `_reversa_sdd/permissions.md#1.1` | O `dono` é **costura de assinatura**: obrigatório nas portas, **ignorado** nos quatro métodos do adaptador, e `owner_id` sem filtro e sem índice no banco | 🟢 |
| `_reversa_sdd/permissions.md#2` | **Zero papéis** e um único ator implícito — sem nome, credencial ou distinção | 🟢 |
| `_reversa_sdd/permissions.md#3` | Matriz degenerada: uma linha, permitido em tudo; "ler arquivo de outro dono ✅ **se conhecer a chave**"; a única coluna negada é "subir 2ª instância" | 🟢 |
| `_reversa_sdd/permissions.md#4.1` | A chave de conteúdo **faz o papel de sessão** e é entregue ao navegador em campo oculto: é identificador, não segredo | 🟢 |
| `_reversa_sdd/permissions.md#4.3` | Autenticação ❌ e autorização ❌ na cobertura; "**a chave é portadora do acesso**"; confidencialidade dos dados ❌ (a lista completa de nomes vai no HTML) | 🟢 |
| `_reversa_sdd/permissions.md#5.4` | O aceite de risco do `BUG-20260929-BJJH` é `temporary: true` e **reabre** quando alguém além de Adriano tiver acesso antes da Onda 3 | 🟢 |
| `_reversa_sdd/permissions.md#5.6` | O alvo exige `owner_id` como **invariante do aggregate**, repositório **sempre escopado** e **teste negativo** (A acessando B recebe `404`, não `403`) como **portão de go-live** | 🟢 |
| `_reversa_sdd/permissions.md#6` | `P-01` decidida: a correção pertence à **Onda 3**; `P-06` credencial em claro, `P-07` dado pessoal persistido sem retenção, `P-08` as duas artes públicas | 🟢 |
| `_reversa_sdd/architecture.md#1` | Monolito de um processo, server-side, **sem autenticação**; a borda valida entrada, despacha por `action` e escolhe o render pelo desfecho | 🟢 |
| `_reversa_sdd/architecture.md#3` | "A tela é **um** template" (`index.html`) e as portas são "**a fronteira que a Onda 3 vai estender**" | 🟢 |
| `_reversa_sdd/domain.md#3.5` | Mesmo conteúdo, mesma chave — e é a chave que circula entre requisições; o nome do cliente nunca compõe o caminho | 🟢 |
| `_reversa_sdd/domain.md#3.6` | As duas listas entram em **toda** renderização, por processador de contexto | 🟢 |
| `_reversa_sdd/domain.md#3.7` | O histórico **grava o `dono` e não filtra nada**; nenhuma consulta tem `WHERE owner_id` | 🟢 |
| `_reversa_sdd/domain.md#6.3` | Decisão vigente: o isolamento **não se corrige no legado**; single-tenant por aceite; tratamento na **Onda 3** | 🟢 |
| `_reversa_sdd/erd-complete.md#E-06` | `owner_id` existe sem consulta e **sem FK** para entidade de dono; o teste negativo segue como portão | 🟢 |
| `_reversa_sdd/inventory.md#4` | Variáveis de ambiente com padrão declarado; `app.secret_key` **removido** em 2026-10-05; `DONO_DO_PROCESSO = "unico"` declarado como costura e **não** como segurança | 🟢 |
| `_reversa_sdd/inventory.md#5` | 13 arquivos em `src/uploads/` e 3 em `_aposentados/`; 6 tabelas sem tabela de usuário; **sem runner de migração** — esquema novo exige `down -v` ou `ALTER TABLE` manual | 🟢 |
| `_reversa_sdd/migration/risk_register.md#RISK-005` | Mitigação: (a) escopo **estrutural** na assinatura, (b) **teste negativo obrigatório** com `404`, (c) isolamento antes de qualquer UI multiusuário, (d) criptografia na Onda 5 | 🟢 |
| `_reversa_sdd/migration/cutover_plan.md#Onda-3` | O go-live fica **condicionado** ao teste negativo de `404` | 🟢 |
| `_reversa_sdd/migration/target_data_model.md` | No alvo, `owner_id UUID NOT NULL REFERENCES app_user(user_id)` e a leitura é **sempre** escopada | 🟢 |
| `_reversa_sdd/adrs/18` | Single-tenant por aceite de risco; a Onda 3 é a **única rota** em que o critério de aceite é verificável | 🟢 |
| `_reversa_sdd/addenda/014-endurecimento-da-borda.md` | `TRUSTED_HOSTS` e a frase que define o estado atual: "sem sessão e sem cookie, não havia nada entre essa página e as árvores" | 🟢 |
| `_reversa_sdd/addenda/049-sistema-de-log.md` | Trilha de auditoria por ação de servidor, com **conjuntos fechados** de ação e desfecho e máscara de privacidade | 🟢 |
| `.reversa/principles.md#i` | Dado real de DNA nunca entra em repositório, fixture, golden, **log** ou documentação | 🟢 |
| `.reversa/principles.md#iii` | Nenhuma mudança sem teste que a cubra | 🟢 |
| `src/app.py#L91` | `DONO_DO_PROCESSO = "unico"` — o **único** lugar que declara o valor, consumido por 8 chamadas às portas | 🟢 |
| `src/app.py#L93-L100` | `app.secret_key` removido: "seria a chave de forja de sessão no instante em que alguém introduzisse sessão" | 🟢 |
| `src/app.py#L134-L165` | Lista de `Host` confiável e extensão por `ANALISADOR_HOSTS_PERMITIDOS`; a porta não participa da comparação | 🟢 |
| `src/ports/adaptadores.py#L64-L206` | `dono` **recebido e ignorado** em `guardar`, `resolver`, `listar` e `aposentar` — inclusive na listagem | 🟢 |
| `init.sql#L24-L26` e `#L171-L177` | `owner_id TEXT NOT NULL` sem FK e sem índice; `app_user` e `access_audit` **existem no DDL do alvo e não são criadas** — pertencem às Ondas 3 e 5 | 🟢 |
| `requirements.txt` | Nenhuma biblioteca de autenticação instalada: só Flask e Werkzeug (transitivo) | 🟢 |
| `tests/test_icone_de_atalho.py#L189` | `SHA_DA_TELA` é invariante mantido **à mão**; a masthead com a conta e "Sair" muda a tela vazia | 🟢 |

> **Glossário mínimo deste documento.** **Conta** é o registro de identidade criado no primeiro
> acesso autenticado; **dono** é a conta a que um dado pertence; **sessão** é o vínculo entre o
> navegador e a conta, carregado em cookie; **provedor de identidade** é o serviço externo que
> confirma a conta (aqui, o Google); **OAuth 2.0** é o protocolo de delegação usado nessa
> confirmação; **escopo** é o recorte por dono aplicado a toda leitura e escrita; **404** é a
> resposta de recurso inexistente, usada também para recurso de outro dono; **modo legado** é a
> operação sem autenticação, com o marcador único de processo.

## 3. Personas e cenários de uso

| Persona | Objetivo | Cenário-chave |
|---------|----------|---------------|
| Operador (dono da instalação) | Usar a ferramenta na própria árvore | Abre a aplicação, entra com a conta Google e analisa a árvore que ele mesmo enviou |
| Segunda pessoa, qualquer conta Google | Usar o próprio espaço sem ver o alheio | Entra com a própria conta no primeiro acesso, recebe lista vazia e envia a própria árvore, sem nenhum arquivo do operador |
| Operador com sessão vencida | Voltar ao trabalho sem perder o que estava fazendo | É devolvido à tela de entrada e, depois de entrar, chega de novo à tela principal |
| Quem reimplementa o sistema | Saber o que é contrato | Lê que recurso de outro dono responde `404` com o texto de inexistência, nunca `403`, e que a chave de conteúdo deixou de ser portadora do acesso |

## 4. Regras de negócio novas ou alteradas

1. **RN-01 — A conta autenticada é o dono, e qualquer conta Google entra.** Toda operação que lê ou grava dado é feita em nome de uma conta identificada pelo provedor; qualquer conta Google que se autentique passa a existir como conta no primeiro acesso, **sem convite, lista ou aprovação** (D1, 2026-10-26). O dono é a **conta**, e não o texto do e-mail: ajuste declarado em relação ao documento de entrada ("o e-mail vira o dono") — e-mail muda e a conta não, e o alvo já modela `owner_id` como referência a uma entidade de usuário. 🟢
   - Origem no legado: `_reversa_sdd/permissions.md#2` (o ator único implícito) e `#4.1` (a chave de conteúdo no papel de sessão)
   - Tipo: nova

2. **RN-02 — O literal de dono deixa de alimentar as portas.** `DONO_DO_PROCESSO = "unico"` deixa de ser o valor das chamadas de `guardar`, `resolver`, `listar`, `aposentar` e `carregar`; o valor passa a vir da sessão. O literal deixa de existir no caminho servido: sem credenciais configuradas a aplicação não sobe (RN-16). 🟢
   - Origem no legado: `src/app.py#L91`, `_reversa_sdd/domain.md#3.7`
   - Tipo: alterada

3. **RN-03 — Sem sessão, não há tela nem ação.** As sete operações que tocam dado — `GET /`, as cinco ações de `POST /` e `POST /descartes.csv` — exigem sessão. As únicas superfícies anônimas são a tela de entrada, o retorno do provedor e as três rotas de arte e de folha de estilo. 🟢
   - Origem no legado: `_reversa_sdd/permissions.md#3` (a matriz degenerada), `#4.3` (a chave como portadora do acesso)
   - Tipo: alterada

4. **RN-04 — A referência de conteúdo pertence a um dono.** Uma referência (`<chave>__<nome>`) resolve para o dono que a enviou e para nenhum outro; a chave deixa de ser credencial de acesso e passa a ser endereço dentro de um escopo. 🟢
   - Origem no legado: `_reversa_sdd/permissions.md#1.1` ("dois envios do mesmo conteúdo por donos diferentes reencontram o **mesmo** arquivo") e `#4.3`
   - Tipo: alterada

5. **RN-05 — Mesmo conteúdo enviado por dois donos são dois arquivos.** A deduplicação por conteúdo continua valendo **dentro** do dono: o mesmo conteúdo reenviado pelo mesmo dono reencontra o arquivo, e o mesmo conteúdo enviado por outro dono nasce como arquivo próprio — aposentar um não pode afetar o outro. 🟢
   - Origem no legado: `_reversa_sdd/domain.md#3.5` (chave por conteúdo) e `_reversa_sdd/permissions.md#1.1`
   - Tipo: alterada

6. **RN-06 — Recurso de outro dono é indistinguível de inexistente.** Listar, carregar árvore, analisar, buscar e aposentar só operam sobre referências do dono da sessão; a tentativa sobre referência alheia recebe a **mesma** resposta de referência inexistente: `404`, o literal já existente e nenhuma pista de que o recurso existe. Nunca `403`, nunca "pertence a outro dono". 🟢
   - Origem no legado: `_reversa_sdd/migration/risk_register.md#RISK-005` (mitigação b) e `_reversa_sdd/permissions.md#5.6`
   - Tipo: nova

7. **RN-07 — A sessão tem prazo, e sair a encerra.** O prazo desta entrega é de **12 horas de inatividade**, renovado a cada operação da conta; depois de sair ou de expirar, qualquer operação volta a exigir entrada, e o histórico do navegador não reabre a tela autenticada em resposta a um `GET` guardado. 🟢
   - Origem no legado: nenhuma — não há sessão hoje (`_reversa_sdd/permissions.md#1`)
   - Tipo: nova

8. **RN-08 — O segredo que assina a sessão vem do ambiente e nunca do repositório.** Esta regra **reverte a remoção** registrada em `P-04` sem revogar o motivo dela: o símbolo `app.secret_key` pode voltar como leitura de ambiente, jamais como literal versionado. Sem segredo configurado, a autenticação não liga. 🟢
   - Origem no legado: `src/app.py#L93-L100` e `_reversa_sdd/permissions.md#6` (`P-04`)
   - Tipo: alterada

9. **RN-09 — O retorno do provedor é validado, e o endereço de retorno é declarado.** A entrada carrega um valor de estado ligado à sessão e só aceita retorno com estado correspondente e código de uso único; o endereço de retorno vem da **configuração**, nunca do cabeçalho `Host` da requisição. Código, token e segredo não aparecem em URL de tela, log, auditoria ou mensagem. 🟢
   - Origem no legado: `_reversa_sdd/addenda/014-endurecimento-da-borda.md` (o vetor de `Host`) e `_reversa_sdd/addenda/049-sistema-de-log.md` (máscara de privacidade)
   - Tipo: nova

10. **RN-10 — A tela diz quem entrou e oferece Sair, e nenhum outro literal muda.** A masthead ganha o rótulo da conta e o comando de sair; a tela de entrada é uma superfície nova (segundo template — delta declarado contra `architecture.md#3`). Os 29 literais catalogados em `domain.md#5` continuam intactos, e a recusa por recurso alheio reaproveita o literal de inexistência. 🟢
    - Origem no legado: `_reversa_sdd/domain.md#5` (texto de tela é contrato) e `_reversa_sdd/architecture.md#3`
    - Tipo: nova

11. **RN-11 — O histórico grava o dono real, e toda leitura é escopada.** A gravação usa o dono da sessão; nenhuma leitura do histórico pode devolver linha de outro dono. Como hoje **nenhum código de `src/` lê as tabelas** (`architecture.md#4`), a regra nasce como invariante de interface, presa por teste, e não como consulta corrigida. 🟢
    - Origem no legado: `_reversa_sdd/domain.md#3.7` e `_reversa_sdd/erd-complete.md#E-06`
    - Tipo: alterada

12. **RN-12 — Entrar, sair e a recusa de entrada deixam linha de auditoria.** A trilha da `049` ganha as ações de entrada e saída, com desfecho; a linha identifica a conta pelo **identificador**, nunca pelo e-mail, porque a trilha sobrevive à requisição. 🟢
    - Origem no legado: `_reversa_sdd/addenda/049-sistema-de-log.md` e `src/utils/auditoria.py#L38-L49`
    - Tipo: nova

13. **RN-13 — O aceite de risco single-tenant termina com o teste negativo verde.** Com entrada provada e isolamento provado, a condição do `BUG-20260929-BJJH` deixa de valer; a entrega **não fecha** sem o teste que prova `404` para A→B. A decisão de abrir a entrada a **qualquer conta Google** (D1) torna esse teste a única barreira que resta entre duas contas, e é por isso que ele é portão, e não recomendação. 🟢
    - Origem no legado: `_reversa_sdd/permissions.md#5.4`, `_reversa_sdd/adrs/18` e `_reversa_sdd/migration/cutover_plan.md#Onda-3`
    - Tipo: removida (o aceite de risco)

14. **RN-14 — Sem internet não há entrada, e o sistema não inventa sessão.** A dependência do provedor é consequência aceita da escolha do documento; o que não se admite é cair sozinho no modo legado por falha de rede, de configuração ou de resposta do provedor. 🟡
    - Origem no legado: nenhuma — a aplicação hoje funciona offline
    - Tipo: nova

15. **RN-15 — A conta inicial é declarada, nunca inferida.** Os dados que existiam antes da identidade — os 13 arquivos de `src/uploads/`, os de `_aposentados/` e o histórico com `owner_id = 'unico'` — passam a pertencer à conta declarada na configuração como dona inicial. A atribuição é feita uma vez, é idempotente e **nunca** depende de quem se autentica primeiro: com a entrada aberta a qualquer conta (D1), inferir o dono pela ordem de acesso entregaria o acervo do operador ao primeiro estranho. 🟢
    - Origem no legado: `_reversa_sdd/inventory.md#5` e `_reversa_sdd/permissions.md#1.1`; decisão D2 de 2026-10-26
    - Tipo: nova

16. **RN-16 — Sem credenciais, o servidor não sobe.** A ausência das credenciais do provedor interrompe a subida com mensagem que nomeia o que falta; a aplicação não escuta porta e não cai em modo legado. O import do módulo continua funcionando, porque é assim que a suíte e o harness de paridade o carregam sem subir servidor. 🟢
    - Origem no legado: `docker-compose.yml#L23-L25` (o `${VAR:?}` que interrompe com mensagem) e `src/app.py#L836-L846` (o `SystemExit` do waitress ausente)
    - Tipo: nova

## 5. Requisitos Funcionais

| ID | Requisito | Prioridade | Critério de aceite | Confidência |
|----|-----------|------------|--------------------|-------------|
| RF-01 | A tela de entrada permite entrar com a conta Google, sem senha e sem cadastro prévio | Must | A tela de entrada oferece a entrada pelo provedor; qualquer conta Google autenticada abre a tela principal no primeiro acesso, com o próprio espaço e o rótulo da conta; nenhum campo de senha existe no sistema | 🟢 |
| RF-02 | As sete operações de dado exigem sessão; as três rotas de arte e de folha de estilo não | Must | Sem sessão, `GET /` responde com a tela de entrada e nenhuma ação de `POST` toca arquivo, árvore ou resultado; `GET /app.css`, `/banner.png` e `/apple-touch-icon.png` respondem `200` | 🟢 |
| RF-03 | A lista de arquivos mostra apenas os arquivos do dono | Must | Com dois donos e arquivos distintos, cada um vê só os seus nas duas abas; nenhum rótulo do outro aparece no HTML servido | 🟢 |
| RF-04 | Abrir árvore, analisar DNA, buscar caminho e aposentar exigem referência do dono | Must | A referência do dono B, apresentada por A, não carrega árvore, não produz análise, não produz busca e não move arquivo | 🟢 |
| RF-05 | A recusa a recurso de outro dono é a mesma de recurso inexistente | Must | Resposta `404` com o literal existente ("Erro: Arquivo 'X' não existe mais." ou "Não foi possível aposentar o arquivo: ele não está mais na pasta."); nenhum status, texto ou cabeçalho distingue "de outro" de "não existe" | 🟢 |
| RF-06 | Sair encerra a sessão | Must | Depois de sair, qualquer operação volta a exigir entrada; o botão "voltar" do navegador não devolve uma tela autenticada | 🟢 |
| RF-07 | A tela identifica a conta e oferece o comando de sair | Must | A masthead mostra o rótulo da conta e um comando de sair, operável por teclado; nenhum dos 29 literais catalogados muda | 🟡 |
| RF-08 | A sessão expira | Must | Passadas 12 horas de inatividade, a próxima operação exige entrada de novo e a tela de entrada explica o motivo | 🟡 |
| RF-09 | Falha no retorno do provedor não cria sessão | Must | Cancelamento, código expirado, estado divergente e conta recusada devolvem a tela de entrada com uma frase; nenhuma sessão é criada e nenhum recurso é tocado | 🟢 |
| RF-10 | O histórico grava o dono da sessão e nenhuma leitura devolve linha de outro dono | Must | Uma análise de A não aparece em consulta feita como B; a gravação usa o dono da sessão | 🟢 |
| RF-11 | O teste negativo A→B é portão da entrega | Must | Existe teste automatizado, com dois donos, que prova `404` (e a ausência de `403`) em todas as operações do RF-04; a entrega não é declarada pronta sem ele | 🟢 |
| RF-12 | Os dados anteriores à identidade vão para a conta inicial declarada | Must | Os 13 arquivos de `src/uploads/`, os de `_aposentados/` e o histórico com `owner_id = 'unico'` aparecem para a conta declarada como inicial; nada é apagado; a atribuição é idempotente e não muda com a ordem de entrada | 🟢 |
| RF-13 | A tela de entrada funciona sem sessão e com a folha de estilo | Must | `GET /app.css` responde anonimamente e a tela de entrada renderiza com o estilo do projeto | 🟢 |
| RF-14 | A identidade entra no teste por injeção, nunca por rede | Must | A suíte inteira roda sem internet e sem credenciais reais; nenhum teste chama o provedor | 🟢 |
| RF-15 | Entrar, sair e a recusa de entrada deixam linha de auditoria | Should | A trilha ganha as ações de entrada e saída, com desfecho; a linha identifica a conta pelo identificador, nunca pelo e-mail | 🟡 |
| RF-16 | Subir sem as credenciais do provedor encerra o processo, com diagnóstico | Must | Sem as credenciais, a subida termina com mensagem que nomeia o que falta e nenhuma porta é escutada; importar o módulo continua funcionando | 🟢 |

## 6. Requisitos Não Funcionais

| Tipo | Requisito | Evidência ou justificativa | Confidência |
|------|-----------|----------------------------|-------------|
| Segurança | O segredo que assina a sessão vem do ambiente, tem tamanho suficiente e nunca é versionado | `P-04` e `src/app.py#L93-L100`: o literal versionado seria chave de forja de sessão | 🟢 |
| Segurança | O cookie de sessão é `HttpOnly`, `SameSite=Lax`, `Secure` quando servida por HTTPS, e não carrega dado pessoal no valor | Sem cookie protegido, o vetor que o `BUG-20260929-BJJH` descreve volta por outra porta | 🟢 |
| Segurança | A URL de retorno é declarada na configuração e nunca derivada do cabeçalho `Host`; a lista de `Host` confiável continua valendo | `_reversa_sdd/addenda/014-endurecimento-da-borda.md` (DNS rebinding) | 🟢 |
| Segurança | Código de autorização, token e segredo não aparecem em URL de tela, log, auditoria nem mensagem de erro | `_reversa_sdd/addenda/049-sistema-de-log.md` e princípio I | 🟢 |
| Privacidade | O e-mail da conta não entra em fixture, golden, log, auditoria nem documentação; a trilha usa o identificador da conta | `.reversa/principles.md#i`; `src/utils/auditoria.py#L10-L20` identifica por chave, nunca por rótulo | 🟢 |
| Privacidade | A feature **não** aumenta o que já é persistido sobre terceiros (`P-07`): nenhuma retenção, expurgo ou consentimento novos | `_reversa_sdd/permissions.md#6` (`P-07`); decidido para a Onda 5 | 🟡 |
| Testabilidade | A suíte roda offline, sem credenciais reais e sem rede; o provedor é substituído por injeção | Princípio III; a suíte e o harness de paridade importam `app` | 🟢 |
| Compatibilidade | A entrada funciona nos dois endereços em uso (host `:5000`, container `:5080`) e a URL de retorno registrada casa com o endereço em uso | `_reversa_sdd/inventory.md#4` e `docker-compose.yml#L84` | 🟡 |
| Disponibilidade | Sem internet não há entrada; a falha e o tempo limite do provedor são declarados na tela, e o processo continua no ar | Consequência aceita da escolha do documento | 🟡 |
| Concorrência | Duas requisições simultâneas da mesma conta enxergam o mesmo escopo, e a sessão não é estado mutável compartilhado entre threads | `_reversa_sdd/architecture.md#2`: processo multi-thread com 4 threads | 🟢 |
| Desempenho | Entrar custa no máximo dois redirecionamentos e não paga parse de árvore; o cache da árvore continua válido | `_reversa_sdd/adrs/38`: com o armazenamento escopado, o caminho distingue donos e a chave segue correta | 🟢 |
| Observabilidade | Entrar, sair e a recusa de entrada entram na trilha da `049`, com o identificador de requisição | `_reversa_sdd/addenda/049-sistema-de-log.md` | 🟡 |
| Acessibilidade | O comando de entrada e o de sair são botões com nome acessível e foco visível; a falha é anunciada como alerta | `_reversa_sdd/addenda/036-refino-do-cartao-de-resultado.md` e `addenda/037` (ARIA própria) | 🟢 |
| Suíte | O marco é **1.717 passam / 9 pulados / 0 falham**; a entrega acrescenta testes e não ajusta teste existente para passar | `_reversa_sdd/addenda/050-imprimir-resultado-por-pessoa.md` | 🟢 |
| Documentação | A entrega converge a extração: a matriz de `permissions.md#3` deixa de ser degenerada, a decisão vira ADR e `architecture.md` e `c4-*` refletem a autenticação | Passo 6 do documento de entrada; `_reversa_sdd/architecture.md#8` | 🟢 |
| Esquema | A tabela da conta entra no `init.sql` de forma idempotente; banco já existente recebe a tabela por `ALTER` documentado ou por recriação declarada | `_reversa_sdd/inventory.md#5`: não há runner de migração | 🟡 |
| Tela | A tela deixa de ser um template único: a tela de entrada é o segundo, e o invariante `SHA_DA_TELA` muda no mesmo commit | `_reversa_sdd/architecture.md#3` e `tests/test_icone_de_atalho.py#L189` | 🟢 |

## 7. Critérios de Aceitação

```gherkin
Cenário: Entrar com a conta Google
  Dado que o operador abre a aplicação sem sessão
  Quando ele escolhe entrar pelo provedor e confirma a própria conta
  Então a tela principal abre identificando a conta
  E a lista mostra os arquivos daquela conta

Cenário: Sem sessão, a tela é a de entrada
  Dado que não há sessão
  Quando a página inicial é pedida
  Então a resposta é a tela de entrada
  E o HTML não contém a lista de arquivos de ninguém

Cenário: Sem sessão, nenhuma ação toca dado
  Dado que não há sessão
  Quando uma das ações de POST é enviada
  Então nenhum arquivo é lido, gravado, movido ou analisado
  E nenhum resultado é produzido

Cenário: A lista de um dono não mostra o arquivo do outro
  Dado que A enviou uma árvore e B tem a própria sessão
  Quando B abre a tela principal
  Então a lista de B não contém o arquivo de A
  E o rótulo do arquivo de A não aparece no HTML de B

Cenário: A referência de outro dono é inexistente
  Dado que A enviou uma árvore e conhece a referência
  Quando B apresenta essa referência numa ação
  Então a resposta é 404 com o texto de arquivo inexistente
  E a resposta não é 403 e não menciona outro dono

Cenário: Aposentar referência de outro dono não move nada
  Dado que A tem um arquivo na lista
  Quando B pede para aposentar a referência de A
  Então o arquivo de A continua na lista de A
  E B recebe a mesma resposta de arquivo inexistente

Cenário: O mesmo conteúdo em dois donos são dois arquivos
  Dado que A e B enviam o mesmo conteúdo
  Quando A aposenta o próprio arquivo
  Então o arquivo de B continua na lista de B
  E o de A sai da lista de A sem afetar o de B

Cenário: Sair encerra a sessão
  Dado que o operador está autenticado
  Quando ele aciona o comando de sair
  Então a próxima operação exige entrada de novo
  E o botão "voltar" do navegador não devolve a tela autenticada

Cenário: Retorno recusado não cria sessão
  Dado que o operador inicia a entrada e o retorno chega inválido, cancelado ou expirado
  Quando a aplicação processa o retorno
  Então nenhuma sessão é criada
  E a tela de entrada explica a falha em uma frase

Cenário: O histórico de um dono não aparece para o outro
  Dado que A executou uma análise
  Quando B consulta o histórico
  Então nenhuma linha da análise de A é devolvida
  E a análise de B, quando existir, continua visível para B

Cenário: A tela de entrada funciona sem sessão
  Dado que não há sessão
  Quando a tela de entrada é pedida
  Então a folha de estilo e as duas artes são servidas
  E a página renderiza sem depender de autenticação

Cenário: A conta mantém o dado quando o e-mail muda
  Dado que a conta de A mudou de e-mail no provedor
  Quando A entra novamente
  Então os arquivos continuam pertencendo à mesma conta
  E nenhum arquivo muda de dono

Cenário: A sessão expira
  Dado que a conta está autenticada e fica 12 horas sem operar
  Quando a próxima operação é pedida
  Então a tela de entrada volta com a explicação do prazo
  E nenhum dado é alterado

Cenário: A conta nova começa com a lista vazia
  Dado que a conta é nova e nunca enviou arquivo
  Quando ela abre a tela principal
  Então as duas abas aparecem vazias
  E nenhum arquivo de outro dono aparece nelas

Cenário: Os dados anteriores vão para a conta inicial declarada
  Dado os 13 arquivos, os aposentados e o histórico anterior
  Quando a conta inicial declarada entra
  Então os dados anteriores aparecem para ela
  E nenhum arquivo é apagado do disco

Cenário: A primeira conta a entrar não herda os dados anteriores
  Dado que os dados anteriores pertencem à conta inicial declarada
  Quando outra conta Google se autentica antes dela
  Então essa conta começa com as duas abas vazias
  E os dados anteriores continuam pertencendo à conta inicial

Cenário: A suíte roda sem rede nem credenciais
  Dado o ambiente sem internet e sem credencial do provedor
  Quando a suíte completa é executada
  Então nenhum teste chama o provedor
  E o resultado não depende de credencial real

Cenário: Entrar deixa linha de auditoria
  Dado que a conta entra com sucesso
  Quando a trilha de auditoria é lida
  Então há uma linha de entrada com o identificador da conta e o desfecho
  E o e-mail não aparece na linha

Cenário: Subir sem as credenciais do provedor
  Dado o ambiente sem as credenciais
  Quando a aplicação é iniciada como servidor
  Então o processo encerra com mensagem que nomeia o que falta
  E nenhuma porta é escutada
```

## 8. Prioridade MoSCoW

| Item | MoSCoW | Justificativa |
|------|--------|---------------|
| RF-01, RF-02 | Must | É o pedido: entrar e, a partir daí, só operar identificado |
| RF-03, RF-04 | Must | Sem escopo na lista e nas ações, a entrada não protege nada e cria falsa segurança |
| RF-05 | Must | É o critério do alvo: `404`, não `403`, para não vazar a existência do recurso |
| RF-06, RF-07, RF-08 | Must | Entrada sem saída nem prazo é sessão perpétua, que a operação real não aceita |
| RF-09 | Must | Um retorno não validado é o caminho de entrada do ataque que a feature existe para fechar |
| RF-10 | Must | O dono gravado no histórico precisa ser verdadeiro, ou o filtro futuro nasce sobre dado errado |
| RF-11 | Must | Portão de go-live declarado em `risk_register.md#RISK-005`; sem ele o aceite de risco continua |
| RF-12 | Must | Ligar o filtro sem destino explícito esconde os arquivos atuais do operador |
| RF-13, RF-14 | Must | Tela de entrada sem estilo e suíte dependente de rede tornam a entrega inutilizável ou não verificável |
| RF-15 | Should | A trilha de acesso é prova de quem entrou; não bloqueia a entrada, mas é o que sustenta a auditoria |
| RF-16 | Must | Subir aberto por credencial ausente é o risco que a feature existe para fechar |
| Papéis diferenciados (administrador, somente leitura) | Fora do escopo | Decidido no documento de entrada |
| Login próprio com usuário e senha | Fora do escopo | Alternativa descartada no documento de entrada |
| Retenção, expurgo e consentimento do dado persistido | Fora do escopo | Pertence à Onda 5 (`P-07`, `RISK-005` d) |

## 9. Esclarecimentos

### Sessão 2026-10-26

- **Q:** Quem pode entrar na aplicação?
  **R:** **Qualquer conta Google.** Qualquer pessoa que alcance a aplicação e se autentique cria o próprio espaço no primeiro acesso; não há convite, lista nem aprovação. A decisão aceita o multi-tenant aberto, e o que a torna defensável é o isolamento provado (`RF-11`) — não a identidade.

- **Q:** O que acontece com os 13 arquivos de `src/uploads/`, os 3 aposentados e o histórico gravado com dono `"unico"`?
  **R:** **Vão para a conta inicial declarada na configuração.** Nada é apagado, e a atribuição não depende de quem entrar primeiro: com a entrada aberta, inferir o dono pela ordem de acesso entregaria o acervo do operador ao primeiro estranho.

- **Q:** O que a aplicação faz ao subir sem as credenciais do provedor?
  **R:** **Recusa subir**, com mensagem que nomeia o que falta. Não há modo legado alcançável por servidor; o import do módulo continua funcionando, e é assim que a suíte e o harness de paridade seguem rodando sem credencial.

## 10. Lacunas

### Dúvidas de produto

Nenhuma. As três de 2026-10-26 — entrada, dados anteriores e ausência de credencial — foram resolvidas na sessão de esclarecimentos (§9) e viraram `RN-01`, `RN-15`, `RN-16`, `RF-12` e `RF-16`.

### Pontos técnicos, de verificação na fase de plano

- 🟡 **A superfície de `POST` tem seis rotas, não cinco.** O documento de entrada fala em "5 rotas POST"; a contagem real é as cinco ações de `src/app.py#L704-L713` mais `POST /descartes.csv` (`src/web/rotas_assets.py#L57`). O RF-02 cobre as seis.

- 🟡 **A dependência declarada no documento não existe no `requirements.txt`.** O documento afirma que a biblioteca de entrada "já está no `requirements.txt`"; o arquivo não traz **nenhuma** biblioteca de autenticação — só Flask e Werkzeug (transitivo). A entrega acrescenta dependências novas, com pin e comentário, sob a regra da `L-26`: import preguiçoso, para que a ausência do pacote não derrube `import app` nem a suíte.

- 🟡 **`owner_id` é `TEXT` sem FK; o alvo é `UUID REFERENCES app_user`.** A entrega escolhe entre antecipar a forma do alvo ou manter `TEXT`; a decisão precisa declarar o que acontece com as linhas existentes.

- 🟡 **O esquema não tem runner de migração.** `init.sql` só roda com o diretório de dados vazio (`CREATE TABLE IF NOT EXISTS`); um banco já existente exige `ALTER TABLE` documentado ou `docker compose down -v` declarado (`inventory.md#5`).

- 🟡 **Não há proteção contra falsificação de requisição entre sites (CSRF) em formulário.** Com cookie de sessão, o envio de formulário em nome de outro vira vetor; `SameSite=Lax` reduz o alcance, e a decisão de acrescentar valor de uso único por formulário é do plano.

- 🟡 **A masthead muda a tela vazia.** `SHA_DA_TELA` (`tests/test_icone_de_atalho.py#L189`) é invariante mantido à mão e precisa da medição nova no mesmo commit, como a `050` fez com a nona medição.

- 🟡 **A pasta `_aposentados/` é única.** Escopar o armazenamento por dono afeta o desempate de nomes (`.1` a `.99`) quando dois donos aposentam arquivos de mesmo nome visível.

- 🟡 **A lista completa de nomes (`all_names`) continua no HTML.** A autenticação não reduz essa exposição: ela passa a existir só para quem está autenticado, e a restrição de verdade continua dependendo da busca no servidor (`P-03`, Onda 4).

- 🟡 **A sessão e a lista de `Host`.** O retorno do provedor chega com o `Host` do endereço em uso; um endereço fora da lista (`127.0.0.1`, `localhost` e o que `ANALISADOR_HOSTS_PERMITIDOS` acrescentar) seria recusado antes da rota, com a página do `400` — o diagnóstico está na tela, mas a URL de retorno registrada precisa casar com ele.

- 🟡 **A recusa de subida precisa ficar na inicialização do servidor, não no import.** O `app` é importado pela suíte e pelo harness de paridade; checar credencial no topo do módulo derrubaria os 1.717 testes. O lugar é o bloco `__main__`, como já faz o `SystemExit` do waitress ausente (`src/app.py#L836-L846`).

- 🟡 **A entrada aberta não tem limite de tentativas nem de contas.** Não há defesa contra criação em massa de contas nem contra o custo de disco que cada conta nova pode trazer; o perímetro continua sendo o loopback (`ANALISADOR_HOST` padrão `127.0.0.1`), e um limite é decisão do plano.

- 🟡 **A atribuição da conta inicial precisa ser idempotente e verificável.** Rodar a atribuição duas vezes não pode duplicar arquivo nem reescrever dono já atribuído, e o teste do `RF-12` precisa cobrir a segunda execução.

## 11. Histórico de alterações

| Data | Alteração | Autor |
|------|-----------|-------|
| 2026-10-26 | Versão inicial gerada por `/reversa-requirements` a partir do documento `D:\Autenticação com Google OAuth — Onda 3.md` e da extração de 2026-10-10 com os adendos vigentes | reversa |
| 2026-10-26 | Sessão de esclarecimentos: D1 = qualquer conta Google; D2 = dados anteriores para a conta inicial declarada; D3 = sem credenciais o servidor não sobe. Entram `RN-15`, `RN-16` e `RF-16`; as três dúvidas zeradas | reversa |

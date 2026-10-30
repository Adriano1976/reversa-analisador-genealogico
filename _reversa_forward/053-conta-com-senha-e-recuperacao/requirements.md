# Requirements: cadastro com senha e e-mail confirmado, recuperação e a tela de entrada em verde

> Identificador: `053-conta-com-senha-e-recuperacao`
> Data: `2026-10-29`
> Pasta da extração reversa: `_reversa_sdd/`
> Confidência: 🟢 CONFIRMADO, 🟡 INFERIDO, 🔴 LACUNA / DÚVIDA

## 1. Resumo executivo

Hoje a única porta é a conta Google (feature 051): sem ela não se entra, e quem perde a conta perde também o próprio histórico. Esta feature entrega **cadastro e entrada com e-mail e senha**, com **e-mail confirmado antes do primeiro acesso**, mantém o Google como caminho alternativo e acrescenta **recuperação de senha por e-mail** com link de uso único. A tela de entrada passa a ser a das duas referências visuais — cartão central, Google primeiro, campos de e-mail e senha, botão principal na **cor verde do app** —, com o banner na posição atual e o **ícone na aba do navegador** vindo de `src/assets/apple-touch-icon.png`. O `dono` continua sendo o `sub` opaco da conta, e a instância nasce preparada para ser compartilhada: identidade unificada por e-mail verificado, armazenamento local atrás de uma porta e sessões revogáveis.

## 2. Contexto a partir do legado

| Fonte | Trecho relevante | Confidência |
|-------|------------------|-------------|
| `_reversa_sdd/addenda/051-login-google-e-isolamento.md` | Vigente. Entrada por OAuth Google com `state` de uso único; `Conta{sub,email,nome}` no cookie assinado; guarda por endpoint; `dono` = `sub`; cinco variáveis obrigatórias; sete literais novos; auditoria `entrar`/`sair` com `conta=sub` | 🟢 |
| `_reversa_sdd/architecture.md#1` | Monolito de um processo, sem estado de domínio. A frase "sem autenticação" foi superada pela 051 | 🟢 |
| `_reversa_sdd/architecture.md#3` | 31 componentes em sete unidades; o pacote `web/` nasceu depois da extração (051 e 052) | 🟢 |
| `_reversa_sdd/architecture.md#6` | "Nenhuma integração de rede com terceiros" — falso desde a 051 (Google). O e-mail acrescenta a segunda saída de rede | 🟢 |
| `_reversa_sdd/permissions.md#3` | Matriz degenerada; ler com o adendo 051: o `dono` escopa listagem, leitura e aposentadoria, e recurso alheio responde `404`, nunca `403` | 🟢 |
| `_reversa_sdd/permissions.md#4.3` | Autenticação e autorização/propriedade passaram a cobertas com a 051; a confidencialidade de `all_names` continua aberta (`P-03`) | 🟢 |
| `_reversa_sdd/permissions.md#5` | O aceite de risco do `BUG-20260929-BJJH` reabre se qualquer pessoa além do operador tiver acesso — é o gatilho da postura de compartilhamento | 🟢 |
| `_reversa_sdd/domain.md#3.6` | A tela de entrada entrega as duas listas em toda renderização, por processador de contexto | 🟢 |
| `_reversa_sdd/domain.md#5` | Texto de tela é contrato: 29 literais catalogados mais os 7 da 051 | 🟢 |
| `_reversa_sdd/domain.md#7` | `L-29`: o histórico persiste dado pessoal sem retenção, expurgo nem consentimento — o que pesa ao abrir para outras pessoas | 🟢 |
| `_reversa_sdd/state-machines.md#11` | Declarava não existir ciclo de vida de usuário nem de sessão; o adendo 051 cria a máquina da sessão | 🟢 |
| `_reversa_sdd/inventory.md#4` | Superfície HTTP e variáveis de ambiente; a 051 acrescentou três rotas e cinco variáveis | 🟢 |
| `_reversa_sdd/inventory.md#5` | "Sem autenticação, sem sessão e sem papéis — nenhuma tabela de usuário": continua valendo para o esquema Postgres | 🟢 |
| `_reversa_sdd/erd-complete.md` (E-06) | `owner_id` é `TEXT`, sem FK e sem índice de escopo | 🟢 |
| `_reversa_sdd/adrs/35-pasta-de-uploads-dentro-do-repositorio.md` | A garantia material de manter dado dentro do repositório é o `.gitignore`; o mesmo padrão serve ao arquivo de contas | 🟢 |
| `_reversa_sdd/addenda/052-busca-nome-e-sobrenome.md` | Vigente. `POST /busca` herda a guarda e o escopo da 051; a busca é leitura pura | 🟢 |
| `.reversa/principles.md#i` | Dado real de DNA/GEDCOM e dado pessoal nunca entram em repositório, fixture, golden, log ou documentação | 🟢 |
| `.reversa/principles.md#ii` | Refactor não muda comportamento; mudar comportamento é feature | 🟢 |
| `.reversa/principles.md#iii` | Nenhuma mudança sem teste que a cubra | 🟢 |
| `src/templates/login.html#L39-L40` | A tela de entrada tem um único caminho: a frase e o botão "Entrar com Google" | 🟢 |
| `src/web/sessao.py#L45-L56` | `Conta` é congelada; `sub` é o dono, e `email`/`nome` são rótulo de tela | 🟢 |
| `src/app.py#L773-L788` | Cookie `analisador_sessao`, `HttpOnly`, `SameSite=Lax`, `Secure` só em HTTPS, vida de 12 h | 🟢 |
| `src/utils/auditoria.py#L38-L41` | Conjunto fechado de ações; `conta` é o `sub`, nunca o e-mail | 🟢 |
| `src/assets/app.css#L18-L20` | O verde do app é `--primary:#3F6B2E`, com `--primary-hover:#335724` | 🟢 |
| `docker-compose.yml#L91-L92` | A aplicação publica só `127.0.0.1:5080` e não termina TLS; compartilhar exige entrada própria e `ANALISADOR_URL_PUBLICA` em HTTPS | 🟢 |
| `tests/test_dependencias_nucleo.py` | O acoplamento do núcleo já é guardado por inspeção de AST, e a mesma técnica serve às guardas novas | 🟢 |

> **Glossário mínimo deste documento.** **Conta local** é a identidade criada nesta instalação por e-mail e senha; **conta Google** é a identidade devolvida pelo provedor OAuth; **conta unificada** é a conta local que também carrega a identidade Google do mesmo e-mail verificado; **dono** (`sub`) é o identificador opaco que escopa pasta de uploads e histórico e que nunca muda na unificação; **confirmação de e-mail** é a prova de posse do endereço, feita por link; **credencial** é o par e-mail + derivação de senha; **política de senha** é o conjunto de exigências da `RN-02`; **token** é o valor aleatório de uso único que autoriza confirmação ou redefinição; **transporte de e-mail** é o meio pelo qual as mensagens saem do servidor; **sessão** é o cookie assinado que carrega a conta; **referências visuais** são as duas imagens anexadas pelo operador.

## 3. Personas e cenários de uso

| Persona | Objetivo | Cenário-chave |
|---------|----------|---------------|
| Operador sem conta Google | Usar o analisador sem depender de terceiro | Cria conta, confirma o e-mail pelo link e entra |
| Operador que já usa o Google | Não perder o caminho atual, nem o histórico | Continua clicando em "Entrar com Google"; ao criar senha com o mesmo e-mail, cai na mesma conta e na mesma pasta |
| Operador que esqueceu a senha | Voltar a entrar sem suporte manual | Pede instruções, recebe o link no e-mail e define uma nova senha |
| Operador que perdeu o acesso ao Google | Recuperar o próprio histórico | Se tem senha local, entra por ela; se não, a tela explica o caminho do Google |
| Operador que compartilha a instância | Abrir para outras pessoas sem virar suporte | Confere que cada conta vê só a própria pasta e que o cadastro só vale com e-mail confirmado |
| Quem reimplementa o sistema | Saber o que é contrato | Lê as regras, os literais e o que permanece intocável |

## 4. Regras de negócio novas ou alteradas

1. **RN-01 — Cadastro aberto, com e-mail confirmado antes do primeiro acesso.** Quem alcança a porta pode criar uma conta com e-mail e senha. O cadastro **não abre sessão** e a conta nasce **não confirmada**: só entra quem provou a posse do endereço pelo link enviado por e-mail. 🟢
   - Tipo: nova
2. **RN-02 — Política de senha.** Mínimo de 8 caracteres; pelo menos uma letra minúscula, uma maiúscula, um dígito e um caractere especial; máximo de 128 caracteres. A contagem é em caracteres, sem aparar espaços. "Caractere especial" é o símbolo ASCII imprimível que não seja letra sem acento nem dígito; o espaço não conta como especial. A recusa nomeia o que falta e nunca repete a senha. 🟢
   - Tipo: nova
3. **RN-03 — E-mail é a chave de cadastro e de verificação, não é dono.** O e-mail é normalizado (aparar espaços e baixar caixa) e é único entre contas locais. O **dono** é um identificador opaco e estável — no cadastro local, `local-<32 hex>` — nunca o e-mail, e é seguro como nome de pasta: apenas `[a-z0-9-]`. 🟢
   - Origem: `_reversa_sdd/addenda/051-login-google-e-isolamento.md` (Resumo da entrega)
   - Tipo: nova
4. **RN-04 — Senha nunca em claro.** A senha não é gravada, não entra em log e não é devolvida por nenhuma rota; o armazenamento guarda apenas uma derivação lenta, com sal por conta. 🟢
   - Origem: `.reversa/principles.md#i`
   - Tipo: nova
5. **RN-05 — Falha de entrada é indistinguível.** E-mail inexistente e senha errada produzem a mesma resposta, o mesmo texto e o mesmo caminho de comparação; a verificação da derivação usa comparação em tempo constante. Conta **não confirmada** só recebe resposta própria **depois de a senha conferir**: quem não sabe a senha continua vendo a mensagem genérica, e a enumeração de contas não ganha um oráculo novo. 🟡
   - Tipo: nova
6. **RN-06 — O Google continua sendo caminho.** O botão, o literal `Entrar com Google`, a rota `/login?iniciar=1` e as três mensagens de falha permanecem como a 051 entregou; o Google só entrega conta com `email_verified` verdadeiro, como hoje. Ao criar uma senha com o mesmo e-mail, a conta Google **não** é duplicada: ver `RN-20`. 🟢
   - Origem: `_reversa_sdd/domain.md#5`; `_reversa_sdd/addenda/051-login-google-e-isolamento.md` (Resumo da entrega)
   - Tipo: alterada (preservação)
7. **RN-07 — Cadastro e recuperação não revelam quem tem conta.** O cadastro responde **a mesma frase** exista ou não conta para o e-mail; quando já existe, a mensagem de "esse e-mail já está em uso" (com o atalho para entrar ou recuperar) vai por **e-mail** ao dono do endereço, nunca para a tela de quem está deslogado. O pedido de recuperação segue a mesma regra. 🟢
   - Tipo: nova
8. **RN-08 — Token de recuperação.** O token tem 32 bytes de entropia em forma segura para URL, é guardado apenas como derivação, vale 60 minutos, é de uso único e um pedido novo invalida os anteriores da mesma conta. O token nunca é registrado em log nem em auditoria. 🟢
   - Tipo: nova
9. **RN-09 — Link de redefinição.** O `GET` do link apenas mostra o formulário e não consome o token; o `POST` é quem consome. Token inválido, expirado ou já usado produz a mesma tela, com a mensagem própria e o atalho para pedir outro. Quem redefine a senha pelo link **confirma o e-mail** junto, porque o link prova a posse do endereço. 🟢
   - Tipo: nova
10. **RN-10 — Redefinição troca a credencial e revoga as sessões anteriores.** A nova senha passa pela `RN-02`, a conta incrementa a **versão de credencial** e a sessão carrega a versão em que nasceu; a guarda recusa sessão de versão anterior. Vale para conta local; a sessão de conta apenas Google segue como na 051. 🟢
    - Tipo: nova
11. **RN-11 — Sessão é a da 051.** A conta local entra pelo mesmo `guardar_conta`, que limpa a sessão antes de gravar (defesa contra fixação); o cookie mantém `HttpOnly`, `SameSite=Lax` e `Secure` quando a URL pública é HTTPS. 🟢
    - Origem: `_reversa_sdd/addenda/051-login-google-e-isolamento.md`; `src/app.py#L773-L788`
    - Tipo: alterada (reuso)
12. **RN-12 — Isolamento por dono vale igual.** A pasta de uploads e o histórico são escopados pelo `sub`; recurso de outro dono responde como inexistente (`404`), e a listagem não mistura donos. 🟢
    - Origem: `_reversa_sdd/permissions.md#3` lido com o adendo 051
    - Tipo: alterada (extensão)
13. **RN-13 — Texto de tela é contrato.** Os literais novos entram no catálogo e os 36 existentes (29 + 7 da 051) não mudam. Entram: `Entre na sua conta`; `E-mail`; `Senha`; `Entrar`; `Esqueci minha senha`; `Criar conta`; `Crie sua conta`; `Repita a senha`; `A senha precisa ter ao menos 8 caracteres, com maiúscula, minúscula, número e caractere especial.`; `E-mail ou senha inválidos.`; `Confirme seu e-mail para entrar. Enviamos um link para o endereço informado.`; `Reenviar o link de confirmação`; `E-mail confirmado. Entre com a sua senha.`; `Este link de confirmação expirou ou já foi usado. Peça outro.`; `Se este e-mail puder ser usado, enviaremos as instruções.`; `Recupere sua senha`; `Se você entra apenas com Google, recupere o acesso na sua conta Google.`; `Solicitar instruções`; `Se este e-mail estiver cadastrado, enviaremos as instruções.`; `O envio de e-mail não está configurado nesta instalação.`; `Defina uma nova senha`; `Este link expirou ou já foi usado. Peça outro.`; `Senha alterada. Entre com a nova senha.`; `Voltar para entrar`; `Definir senha`; `Defina uma senha para entrar sem depender do Google.`; `Senha definida. Você já pode entrar com e-mail e senha.`; `Não foi possível concluir agora. Tente de novo em instantes.`; `Mostrar senha`; `Esconder senha`. 🟢
    - Origem: `_reversa_sdd/domain.md#5`
    - Tipo: nova
14. **RN-14 — Auditoria sem dado pessoal.** As ações novas entram no conjunto fechado de auditoria; a linha identifica a conta pelo `sub`, e nunca carrega e-mail, senha ou token. 🟢
    - Origem: `src/utils/auditoria.py#L38-L41`; `_reversa_sdd/addenda/049-sistema-de-log.md`
    - Tipo: alterada (extensão do conjunto)
15. **RN-15 — Anti-abuso cobre entrada, recuperação, cadastro e reenvio.** Cinco falhas de entrada para o mesmo par (e-mail, origem) em quinze minutos passam a ser recusadas com a mensagem genérica da `RN-05`; três pedidos de recuperação para o mesmo e-mail em quinze minutos são descartados sem envio, com a resposta da `RN-07`; cinco cadastros por origem em uma hora são recusados com a resposta genérica; três reenvios de confirmação para a mesma conta em uma hora são descartados. O bloqueio é temporário e não trava a conta. 🟡
    - Tipo: nova
16. **RN-16 — Ícone na aba do navegador.** As telas de identidade declaram `rel="icon"` apontando para `/favicon.png`, uma derivada **transparente** (128×128, com canal alfa) da mesma arte canônica do ícone de atalho; `/apple-touch-icon.png` continua opaco, porque o atalho do celular compõe transparência sobre preto. A derivada tem receita única em `tests/favicon_da_aba.py` e teste de deriva com o canal alfa. 🟢
    - Origem: `_reversa_sdd/domain.md#3.10`; `src/templates/_entrada_base.html`; `tests/favicon_da_aba.py`
    - Tipo: nova
17. **RN-17 — A tela segue as referências, com o verde do app.** A estrutura é a das duas imagens: título em destaque, botão do Google antes dos campos, `E-mail`, `Senha`, botão principal e links; na recuperação, o título, a frase sobre Google, o campo e o botão, com o atalho de volta; na confirmação, a frase de estado e o reenvio. O banner permanece **no topo do cartão, na posição atual**; o botão principal usa o verde primário do app (`--primary`), não a cor terracota da referência; nenhuma folha de estilo ou fonte nova de CDN entra. 🟢
    - Origem: referências visuais anexadas; `src/assets/app.css#L18-L20`
    - Tipo: nova
18. **RN-18 — Sem transporte de e-mail, o resto continua.** Entrada e saída de contas já confirmadas funcionam sem configuração de e-mail; sem transporte, o cadastro não conclui (não há como confirmar), a recuperação avisa que o envio não está configurado e a subida registra aviso — o servidor **não** se recusa a subir. 🟡
    - Tipo: nova
19. **RN-19 — Confirmação de e-mail.** O cadastro gera um token de confirmação com as mesmas garantias do token de recuperação (32 bytes, guardado como derivação, uso único), válido por 24 horas; um novo pedido invalida o anterior; o reenvio é permitido na tela de aviso, dentro do limite da `RN-15`. Conta não confirmada não abre sessão, e o e-mail de confirmação é o único caminho até ela; a redefinição de senha também confirma (RN-09). 🟢
    - Tipo: nova
20. **RN-20 — Unificação de identidade por e-mail verificado, nas duas direções e numa regra só.** A unificação **anexa identidade à conta que já existe**, nunca cria segunda conta nem segunda pasta, e o `sub` nunca muda. Ela acontece por dois caminhos seguros: (a) **entrada Google** com e-mail de conta local confirmada anexa o `google_sub` à conta local e usa o `sub` dela, confirmando o e-mail local de passagem; (b) **conta Google autenticada** define a primeira senha pela tela de definir senha, sem cadastro novo. O cadastro **não autenticado** com e-mail já existente **não cria nem altera** conta: responde a frase genérica e avisa o dono por e-mail (`RN-07`). Sem confirmação dos dois lados, as identidades seguem separadas. 🟢
    - Tipo: nova
21. **RN-21 — Armazenamento local das contas.** As contas vivem em um arquivo local **fora de `src/uploads/`** (a tela varre essa pasta), coberto pelo `.gitignore`, com permissão restrita ao usuário do processo quando o sistema operacional permitir. O registro guarda apenas o necessário: e-mail normalizado, derivação e sal da senha, estado de confirmação, versão de credencial, identidade Google quando houver e tokens derivados. A escrita é atômica e serializada entre as quatro threads; o backup é a cópia do arquivo; recriar o contêiner sem volume próprio apaga as contas, e isso é declarado. 🟢
    - Origem: `_reversa_sdd/adrs/35-pasta-de-uploads-dentro-do-repositorio.md`; `docker-compose.yml#L81-L90`
    - Tipo: nova
22. **RN-22 — Alternância de visibilidade da senha.** Todo campo de senha alterna entre escondida e visível no **tipo do `coliff/bootstrap-show-password-toggle`** (MIT): o ícone de olho — e o de olho cortado quando visível — é o `background-image` do próprio campo, **visível desde o carregamento**, e um botão **vazio e invisível** cobre a área do ícone. O botão nasce `d-none` e o script o habilita; sem JavaScript, ele não aparece e o campo continua senha (`RF-18`). O controle é `type="button"`, com `aria-pressed` e rótulo que muda entre `Mostrar senha` e `Esconder senha`; o campo desliga `spellcheck`, `autocorrect` e `autocapitalize`, e mantém o raio do tema nos dois lados, porque o `input-group` zera o lado direito. 🟢
    - Tipo: nova

## 5. Requisitos Funcionais

| ID | Requisito | Prioridade | Critério de aceite | Confidência |
|----|-----------|------------|--------------------|-------------|
| RF-01 | A tela de entrada mostra Google, `E-mail`, `Senha`, `Entrar`, `Esqueci minha senha` e `Criar conta` | Must | `GET /login` responde 200 e contém os quatro controles e os dois links; a frase e o botão do Google continuam presentes | 🟢 |
| RF-02 | O cadastro tem tela própria com e-mail, senha, repetição e a política visível | Must | `GET /cadastro` responde 200 com os três campos e o texto da `RN-02` | 🟢 |
| RF-03 | A política é validada no servidor e refletida no cliente | Must | Cinco senhas fracas (curta, sem maiúscula, sem minúscula, sem dígito, sem especial) são recusadas e nenhuma conta é criada | 🟢 |
| RF-04 | Cadastro com e-mail já usado responde igual ao cadastro aceito e avisa o dono por e-mail | Must | Os dois `POST /cadastro` produzem o mesmo corpo e o mesmo status; o e-mail existente recebe a mensagem de conta já existente, o novo recebe o link de confirmação | 🟢 |
| RF-05 | Credenciais corretas de conta confirmada abrem a sessão e levam à tela principal | Must | Resposta 303 para `/`; cookie `analisador_sessao` presente; `GET /` responde 200 e mostra a conta na masthead | 🟢 |
| RF-06 | Credenciais erradas produzem uma única resposta; conta não confirmada pede confirmação | Must | Senha errada e e-mail inexistente devolvem o mesmo texto e o mesmo status; e-mail de conta não confirmada **com a senha correta** mostra a frase de confirmação e o reenvio | 🟢 |
| RF-07 | O caminho Google permanece intacto | Must | Os três literais de falha e o link `?iniciar=1` seguem iguais; os testes da 051 continuam verdes | 🟢 |
| RF-08 | O pedido de recuperação responde sempre igual e envia só quando há conta local | Must | Conta existente: um e-mail com link e a resposta da `RN-07`; conta inexistente: a mesma resposta e nenhum envio | 🟢 |
| RF-09 | O link abre a tela de nova senha e o token é consumido no `POST` | Must | Token válido mostra o formulário; expirado e já usado mostram a mensagem própria; o segundo `POST` com o mesmo token não altera a senha | 🟢 |
| RF-10 | A redefinição invalida sessões anteriores da conta | Must | Sessão aberta antes da redefinição passa a receber 302 para `/login` na próxima requisição de dado | 🟢 |
| RF-11 | A sessão e a guarda são as mesmas da 051 | Must | Endpoint de dado sem sessão responde 302 (GET) ou 303 (POST); resposta autenticada leva `Cache-Control: no-store` | 🟢 |
| RF-12 | O isolamento por dono vale para a conta local | Must | Duas contas locais: a conta B não lê arquivo da conta A, recebe `404` e nenhum nome de A aparece no corpo | 🟢 |
| RF-13 | As ações novas entram na auditoria sem dado pessoal | Must | Cadastro, confirmação, pedido e redefinição geram linha com `conta=<sub>`; o texto da linha não contém e-mail, senha nem token | 🟢 |
| RF-14 | A tela de entrada tem ícone na aba | Must | O HTML de `/login` contém `rel="icon"` apontando para `/apple-touch-icon.png`, e a rota responde 200 com `image/png` | 🟢 |
| RF-15 | A tela de entrada segue as referências com o verde do app | Must | Cartão central, Google antes dos campos, botão principal usando o verde primário e banner no topo do cartão; contraste de texto em nível AA (mínimo da WCAG) | 🟡 |
| RF-16 | Sair encerra a sessão da conta local | Must | `POST /logout` responde 303; `GET /` seguinte responde 302 para `/login` | 🟢 |
| RF-17 | Entrada, cadastro, recuperação e reenvio são limitados | Must | A sexta falha em quinze minutos recebe a mensagem genérica; o sexto cadastro em uma hora é recusado; o quarto pedido de recuperação em quinze minutos não gera envio; o quarto reenvio de confirmação em uma hora não gera envio | 🟡 |
| RF-18 | Os formulários funcionam sem JavaScript | Must | Todas as ações são `POST` de formulário; a tela não depende de script para cadastrar, confirmar, entrar, pedir ou redefinir | 🟢 |
| RF-19 | Nenhuma dependência de runtime nova | Must | `requirements.txt` não muda; a suíte que prende o pin continua verde | 🟢 |
| RF-20 | O desenho respeita as restrições de projeto | Must | Ver `RNF-01` a `RNF-04`; as guardas estruturais falham se um módulo novo violar a direção das dependências | 🟢 |
| RF-21 | O cadastro envia a confirmação e a conta só entra depois de confirmada | Must | Conta recém-criada: `POST /login` correto mostra a frase de confirmação e não abre sessão; o link confirma e a entrada seguinte funciona; reenvio disponível e limitado | 🟢 |
| RF-22 | A conta unificada mantém um único dono e a mesma pasta | Must | Conta Google verificada com arquivos + definição de senha autenticada: a entrada pelos dois caminhos cai no mesmo `sub`, e os arquivos anteriores continuam visíveis; o cadastro deslogado com o mesmo e-mail não cria conta nem altera a existente | 🟢 |
| RF-24 | A conta autenticada pode definir a primeira senha | Must | `POST /definir-senha` com sessão Google válida cria a credencial na conta atual, aplica a política e mantém o `sub`; sem sessão, responde 302 para `/login` | 🟢 |
| RF-23 | O arquivo de contas sobrevive a reinício e não perde escrita concorrente | Must | Duas criações simultâneas resultam em duas contas, sem corrupção; reiniciar o processo mantém as contas e as sessões emitidas antes | 🟢 |

## 6. Requisitos Não Funcionais

| Tipo | Requisito | Evidência ou justificativa | Confidência |
|------|-----------|----------------------------|-------------|
| RNF-01 · Orientação a objetos | O domínio de identidade é feito de valores imutáveis e serviços com colaboradores injetados; nenhum dicionário solto atravessa camada, e nenhuma regra de senha mora na rota | É o padrão já praticado: `Conta` congelada, `ServicoDeEntrada`, `ProvedorGoogle` | 🟢 |
| RNF-02 · Padrões de projeto | Todo padrão usado é nomeado no desenho, com o ponto de variação que ele resolve; padrão decorativo é proibido. Os candidatos são Strategy para o provedor de identidade, Adapter/porta para o transporte de e-mail e porta/repositório para as contas | Pedido do operador; o projeto já usa `Protocol` como porta e `EstrategiaDeCasamento` como Strategy | 🟢 |
| RNF-03 · Alta coesão | Cada módulo novo tem uma razão para mudar: política de senha, credencial, token, transporte, sessão e rotas não se misturam no mesmo arquivo; a política tem autoridade única | Pedido do operador; o projeto já registra o custo de regra duplicada (autoridade única de limpeza de nome) | 🟢 |
| RNF-04 · Baixo acoplamento | Dependência descendente `web → application → ports → core`; `core/` não importa `web`, `ports`, o framework web, o banco nem a biblioteca de correio; nenhum ciclo; colaborador entra por `Protocol`; guarda por AST no molde de `tests/test_dependencias_nucleo.py` | Pedido do operador; `ADR-24`, `ADR-25`, `ADR-34` | 🟢 |
| RNF-05 · Segurança | Derivação de senha lenta e com sal; tokens de 32 bytes, com validade e uso único; mensagens genéricas na entrada e no cadastro; comparação em tempo constante; nenhuma credencial em log ou auditoria | `RN-04`, `RN-05`, `RN-07`, `RN-08`, `RN-19` | 🟢 |
| RNF-06 · Privacidade | E-mail é dado pessoal e não entra em log nem em auditoria; senha e token nunca são registrados; o `sub` é opaco | `.reversa/principles.md#i`; `src/utils/auditoria.py` | 🟢 |
| RNF-07 · Desempenho | A derivação de senha custa o suficiente para desencorajar força bruta sem travar as quatro threads; o alvo é até 250 ms por verificação no interpretador oficial, medido e registrado | Sem medição, o custo vira surpresa; o servidor é multi-thread e de instância única | 🟡 |
| RNF-08 · Acessibilidade | Rótulos associados aos campos, `autocomplete` correto (`email`, `current-password`, `new-password`), foco visível e contraste de nível AA (mínimo de contraste da WCAG) | A tela atual já usa rótulo e `alert` acessível | 🟡 |
| RNF-09 · Observabilidade | Falha de entrada, de cadastro, de confirmação, de envio e de redefinição gera linha de log com motivo curto, sem identificar a conta; a auditoria registra o desfecho; a subida avisa quando o transporte de e-mail não está configurado | `_reversa_sdd/addenda/049-sistema-de-log.md` | 🟢 |
| RNF-10 · Compatibilidade | Tudo funciona sem JavaScript, em temas claro e escuro, e sem depender de CDN nova | A tela de entrada é formulário puro hoje | 🟢 |
| RNF-11 · Dependências | Biblioteca padrão para derivação, token, transporte e armazenamento local; `requirements.txt` intocado | `ADR-13` fixa as dependências; a arte já ficou fora do runtime por decisão | 🟢 |
| RNF-12 · Persistência das contas | Escrita atômica e serializada sob quatro threads, leitura sempre consistente, permissão restrita e backup por cópia do arquivo | `RN-21`; o projeto já paga caro por escrita não serializada no disco | 🟢 |
| RNF-13 · Operação no contêiner | O arquivo de contas tem volume próprio no compose; sem ele, recriar o contêiner apaga as contas, e o README declara isso | `docker-compose.yml#L81-L90` mostra o mesmo cuidado com uploads e logs | 🟢 |

## 7. Critérios de Aceitação

```gherkin
Cenário: Cadastro válido envia confirmação e não abre sessão
  Dado que não existe conta para o e-mail informado
  Quando o operador envia o cadastro com senha que atende à política
  Então a conta é criada como não confirmada e a tela mostra "Se este e-mail puder ser usado, enviaremos as instruções."
  E nenhuma sessão é aberta e um e-mail com link de confirmação é enviado

Cenário: Cadastro com senha fora da política
  Dado o formulário de cadastro
  Quando o operador envia uma senha com 7 caracteres ou sem caractere especial
  Então nenhuma conta é criada e a mensagem nomeia o requisito que falta
  E a senha digitada não aparece na resposta

Cenário: Cadastro com e-mail que já tem conta
  Dado que existe conta para o e-mail informado
  Quando o operador envia o cadastro
  Então a tela mostra a mesma resposta do cadastro válido, sem dizer que o e-mail existe
  E o dono do endereço recebe a mensagem de conta já existente, e nenhuma conta nova é criada

Cenário: Conta não confirmada não entra
  Dado uma conta recém-criada e ainda não confirmada
  Quando o operador tenta entrar com e-mail e senha corretos
  Então nenhuma sessão é aberta e a tela mostra "Confirme seu e-mail para entrar. Enviamos um link para o endereço informado."
  E o reenvio do link está disponível, dentro do limite

Cenário: Confirmação pelo link
  Dado um token de confirmação válido
  Quando o operador abre o link
  Então a conta fica confirmada e a tela mostra "E-mail confirmado. Entre com a sua senha."
  E a entrada seguinte com a mesma senha abre a sessão

Cenário: Entrada com e-mail e senha corretos
  Dado que existe uma conta local confirmada
  Quando o operador envia e-mail e senha corretos
  Então a sessão é aberta, o cookie é gravado e a tela principal responde 200 com a conta na masthead

Cenário: Entrada com senha errada e com e-mail inexistente
  Dado que existe uma conta local confirmada
  Quando o operador envia a senha errada, ou um e-mail que não tem conta
  Então as duas respostas têm o mesmo texto "E-mail ou senha inválidos."
  E nenhuma sessão é aberta e a tentativa entra na auditoria como falha

Cenário: Recuperação responde igual com e sem conta
  Dado um e-mail com conta e outro sem conta
  Quando o operador pede a recuperação para cada um
  Então os dois recebem a mesma frase "Se este e-mail estiver cadastrado, enviaremos as instruções."
  E só o e-mail com conta recebe o link de redefinição, válido por 60 minutos

Cenário: Link de redefinição expirado ou já usado
  Dado um token vencido ou já consumido
  Quando o operador abre o link e tenta enviar a nova senha
  Então a senha não muda e a tela mostra "Este link expirou ou já foi usado. Peça outro."
  E existe atalho para pedir um novo link

Cenário: Sessão anterior deixa de valer após a redefinição
  Dado que a conta tem uma sessão aberta em outro navegador
  Quando a senha é redefinida pelo link
  Então a sessão anterior recebe 302 para a tela de entrada na próxima operação de dado

Cenário: Conta Google ganha senha sem virar outra conta
  Dado que o operador está autenticado por uma conta Google verificada e já tem arquivos
  Quando ele define a primeira senha pela tela de definir senha
  Então a conta passa a aceitar entrada por e-mail e senha, o dono continua o mesmo e os arquivos anteriores seguem visíveis
  E a pasta de uploads não muda de lugar

Cenário: Entrada Google em conta local confirmada usa o mesmo dono
  Dado que existe conta local confirmada para o e-mail e uma conta Google com o mesmo e-mail verificado
  Quando o operador entra pelo Google pela primeira vez
  Então a identidade Google é anexada à conta local e a sessão usa o sub que já existia
  E a pasta de uploads não muda de lugar
```

Cobertura dos cenários: o cadastro cobre `RF-02`, `RF-03`, `RF-04` e `RF-21`; a confirmação cobre `RF-21` e `RF-23`; a entrada cobre `RF-05`, `RF-06`, `RF-11` e `RF-16`; a recuperação e a redefinição cobrem `RF-08`, `RF-09` e `RF-10`; a unificação e a definição de senha cobrem `RF-22` e `RF-24`; o caminho Google (`RF-07`) e os requisitos de tela (`RF-01`, `RF-14`, `RF-15`) são presos pelos testes de contrato de `tests/test_tela_de_entrada.py`; `RF-12`, `RF-13`, `RF-17`, `RF-18`, `RF-19` e `RF-20` são presos por teste próprio, indicado no plano de testes.

## 8. Prioridade MoSCoW

| Item | MoSCoW | Justificativa |
|------|--------|---------------|
| RF-01, RF-02, RF-03 | Must | Sem tela, formulário e política validada não existe a feature pedida |
| RF-05, RF-06, RF-07 | Must | Entrar por senha sem quebrar o Google é o núcleo do pedido |
| RF-08, RF-09 | Must | "Esqueci minha senha" é pedido explícito do operador |
| RF-21 | Must | Sem confirmação, a recuperação entrega link para quem não é o dono do endereço |
| RF-22, RF-24 | Must | Sem unificação agora, quem já usa Google fica com duas pastas; sem a tela autenticada, o próprio operador não consegue deixar de depender do Google |
| RF-11, RF-12, RF-16, RF-23 | Must | A conta nova precisa do mesmo isolamento e da mesma durabilidade |
| RF-13, RF-14, RF-15 | Must | Auditoria, ícone na aba e o desenho são pedidos explícitos |
| RF-04, RF-17 | Must | Ambiente compartilhado: enumeração de contas e criação em massa são vetores reais |
| RF-10 | Must | Redefinir senha sem revogar sessão é redefinir pela metade |
| RF-18, RF-19 | Must | Compatibilidade e a política de dependências do projeto |
| RF-20 e RNF de projeto | Must | Restrições explícitas do operador para esta funcionalidade |
| RNF de desempenho e acessibilidade | Should | São verificáveis, mas não bloqueiam a primeira versão |

## 9. Esclarecimentos

### Sessão 2026-10-30

- **Q:** O cadastro exige confirmação de e-mail antes do primeiro acesso?
  **R:** **Sim (a).** O operador pretende compartilhar a instância; sem confirmação, qualquer um cria conta com o e-mail de outra pessoa e a recuperação de senha passa a entregar o link para quem não é o dono do endereço. A alternativa sem confirmação obrigaria a migrar todas as contas depois. Custo declarado: sem transporte de e-mail configurado, o cadastro não conclui.

- **Q:** O mesmo e-mail já usado numa conta Google deve levar à mesma conta?
  **R:** **Sim (a), com verificação dos dois lados.** O Google já entrega `email_verified` e a 051 recusa sem ele. A regra é que a identidade nova se anexa à conta existente, o `sub` não muda e a pasta de uploads nunca muda de dono; sem os dois lados verificados, as identidades seguem separadas. O caminho é **autenticado**: a conta Google define a senha estando logada, e o cadastro deslogado com e-mail existente não cria nem altera conta — senão quem escolhesse a senha primeiro sequestraria a conta alheia (pré-sequestro).

- **Q:** Onde as contas locais ficam guardadas?
  **R:** **Arquivo local (a), atrás de uma porta.** Fica fora de `src/uploads/`, no `.gitignore`, com permissão restrita; escrita atômica e serializada. A porta `Contas` existe desde já para o adaptador Postgres entrar depois sem tocar no domínio. No Docker, o arquivo ganha volume próprio.

- **Q:** Transporte de e-mail e comportamento sem credencial?
  **R:** **SMTP por variáveis de ambiente (a).** Sem credencial, o servidor sobe, a recuperação e o cadastro avisam que o envio não está configurado, e a subida registra aviso. Derrubar a instância por causa do canal de recuperação tiraria o acesso de quem já tem conta.

- **Q:** A redefinição derruba as sessões anteriores?
  **R:** **Sim (a).** A conta carrega uma versão de credencial, a sessão carrega a versão em que nasceu e a guarda recusa versão anterior. O custo é uma leitura do armazenamento por requisição autenticada de conta local, amortecida por cache em processo invalidado por modificação do arquivo.

**Decisões decorrentes, aceitas na mesma sessão:**

- O cadastro **não** diz na tela que o e-mail já tem conta: a resposta é a mesma do cadastro aceito e o aviso vai por e-mail ao dono do endereço (`RN-07`, `RF-04`), porque com a instância compartilhada essa mensagem seria um oráculo de contas.
- O cadastro e o reenvio de confirmação entram no limite de tentativas da `RN-15`, porque cada conta pode carregar uma árvore inteira em memória.

## 10. Lacunas

- 🟡 **Risco declarado — sem SMTP, ninguém novo entra.** O cadastro depende da confirmação por e-mail; sem transporte configurado, contas já confirmadas entram, mas novas não concluem. O aviso na subida e na tela é a mitigação.
- 🟡 **Risco declarado — contas Google anteriores à unificação.** Elas não têm linha local; a linha nasce no primeiro cadastro de senha com o mesmo e-mail, herdando o `sub` e a pasta que já existiam. A verificação é no teste de migração da conta Google para a conta unificada.
- 🟡 **Risco declarado — limite em memória.** O contador da `RN-15` vive no processo; reiniciar a instância zera o bloqueio. A instância é única por construção, então não há divergência entre réplicas.
- 🟡 **Risco declarado — entregabilidade.** A entrega real do e-mail depende de domínio, reputação e credencial que a suíte não exercita; só um envio manual prova o caminho de ponta a ponta.
- 🟡 **Risco declarado — aprovação visual.** "Mesmo designer" é julgamento do operador sobre as duas imagens anexadas; a suíte prende presença de elementos e cor, não a semelhança percebida.
- 🟡 **Risco declarado — restrição de desenho dentro do requisito.** O operador pediu orientação a objetos, padrões, coesão e acoplamento como restrições desta funcionalidade. Elas são "como" por natureza; ficam registradas como requisitos verificáveis (`RNF-01` a `RNF-04`), sem escolher biblioteca nem padrão específico antes do desenho.

**Portões antes de abrir a instância para outras pessoas** (não pertencem a esta entrega, mas ficam declarados para não serem descobertos depois):

- TLS e proxy de entrada: hoje o compose publica só `127.0.0.1:5080` e não termina HTTPS; com entrada pública, `ANALISADOR_URL_PUBLICA` precisa ser `https://` para o cookie ganhar `Secure`.
- Cota por conta (número de árvores e bytes): o cache de uma árvore custa cerca de 337 MB no processo, e dez pessoas usando ao mesmo tempo não cabem como está.
- Retenção, expurgo e exclusão de conta: o histórico já persiste dado pessoal de terceiros sem política (`L-29`); compartilhar transforma isso em obrigação.
- Convite ou allowlist: decisão de produto sobre quem pode criar conta.
- Entregabilidade com domínio próprio: sem SPF/DKIM, confirmação e recuperação caem em spam e a feature parece quebrada.

## 11. Histórico de alterações

| Data | Alteração | Autor |
|------|-----------|-------|
| 2026-10-29 | Versão inicial gerada por `/reversa-requirements` | reversa |
| 2026-10-30 | Sessão de esclarecimentos `/reversa-clarify` (2026-10-30): confirmação de e-mail obrigatória, unificação por e-mail verificado, arquivo local atrás de porta, SMTP sem derrubar a subida e revogação de sessão; entram `RN-19` a `RN-21` e `RF-21` a `RF-23`; os três marcadores de dúvida foram zerados | reversa |
| 2026-10-30 | Correção de segurança na entrada do plano: a unificação com conta Google existente exige sessão autenticada (`RN-20`, `RF-24`); cadastro deslogado com e-mail existente não cria nem altera conta | reversa |
| 2026-10-30 | Endurecimento pós-entrega (emenda `E001`): falha de armazenamento vira mensagem e log, nunca `500`; entra o literal `Não foi possível concluir agora. Tente de novo em instantes.` na `RN-13` | reversa |
| 2026-10-30 | Emenda `E004`: alternância de visibilidade das senhas, com botão oculto sem JavaScript (`RN-22`) e quatro literais novos na `RN-13` | reversa |
| 2026-10-30 | Emenda `E005`: favicon **transparente** em `/favicon.png` para as abas das telas de identidade; `rel="icon"` deixa de apontar para o ícone opaco de atalho (`RN-16` revista) | reversa |
| 2026-10-30 | Emenda `E006`: alternância de senha no tipo do `bootstrap-show-password-toggle` — ícone de olho no próprio campo e botão vazio sobreposto, revelado no primeiro foco (`RN-22` revista) | reversa |

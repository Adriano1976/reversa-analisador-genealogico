# Investigation: identidade local com senha, confirmação e recuperação

> Identificador: `053-conta-com-senha-e-recuperacao`
> Data: `2026-10-30`
> Requirements: `_reversa_forward/053-conta-com-senha-e-recuperacao/requirements.md`
> Confidência: 🟢 CONFIRMADO, 🟡 INFERIDO, 🔴 LACUNA

## 1. A pergunta de investigação

A feature precisa de **identidade própria**, sem provedor externo, num sistema que hoje só tem a conta Google (051) e que não tem banco garantido, nem driver de banco no `.venv`, nem serviço de e-mail. As perguntas são quatro: **como guardar a senha**, **onde guardar a conta**, **como provar posse do e-mail** e **como revogar uma sessão sem estado de processo**. O operador declarou que pretende compartilhar a instância depois, o que transforma enumeração de contas e pré-sequestro de conta de "detalhe" em requisito.

## 2. O que o projeto já resolve, e pode ser reusado

| Necessidade | O que já existe | Como a feature usa |
|---|---|---|
| Sessão assinada | `src/web/sessao.py`: `Conta{sub,email,nome}` no cookie, `guardar_conta` limpa a sessão antes de gravar, `instalar_guarda` recusa por endpoint | Reusa a sessão inteira; acrescenta só o campo `versao` e o verificador |
| Identidade por Google | `src/web/autenticacao.py`: `ProvedorGoogle` com `state`, troca de código e perfil; recusa `email_verified` falso | É o lado "verificado" da unificação (`RN-20`) |
| Degradação sem serviço | `src/ports/adaptadores.py`: registrador nulo quando não há `DATABASE_URL`, import preguiçoso do driver | Mesmo desenho para o transporte de e-mail: objeto nulo, aviso, nunca exceção na subida |
| Auditoria | `src/utils/auditoria.py`: conjunto fechado de ações, campo `conta` = `sub` | Ganha cinco ações e nunca recebe e-mail |
| Arte pública | `src/web/rotas_assets.py`: `/apple-touch-icon.png` com `image/png` e `ETag` | Serve de ícone da aba, sem rota nova (`RN-16`) |
| Pasta de runtime no repositório | `src/uploads/` coberta pelo `.gitignore` (`ADR-35`), volume no compose | Mesmo padrão para `src/dados/` |
| Guarda estrutural | `tests/test_dependencias_nucleo.py` inspeciona a AST do núcleo | Serve de molde para o teste que impede o núcleo de importar SMTP ou arquivo |

## 3. Alternativas avaliadas

### 3.1 Derivação da senha

| Alternativa | Prós | Contras | Veredito |
|---|---|---|---|
| **`hashlib.scrypt` (n=2¹⁴, r=8, p=1)** | Biblioteca padrão, resistente a memória, parâmetros guardados junto do hash | Sem ajuste automático de custo por hardware | **adotada** |
| `argon2-cffi` | Estado da arte | Dependência nova (`RNF-11`) | descartada |
| `bcrypt` | Maduro | Dependência nova; limite de 72 bytes | descartada |
| `hashlib.pbkdf2_hmac` | Padrão, simples | Resistência a GPU menor que scrypt para o mesmo custo | descartada |
| Texto puro ou hash simples | — | Inaceitável | descartada |

Parâmetros iniciais: `N=2**14` (16 MB), `r=8`, `p=1`, `dklen=32`, sal de 16 bytes. O alvo de `RNF-07` (até 250 ms por verificação no interpretador oficial) será medido e registrado; se estourar, o ajuste é para baixo com o número declarado, nunca silencioso. O formato guardado inclui algoritmo e parâmetros, então endurecer depois não invalida contas antigas.

### 3.2 Onde a conta vive

| Alternativa | Prós | Contras | Veredito |
|---|---|---|---|
| **Arquivo JSON com trava e `os.replace`** | Biblioteca padrão; inspecionável; backup é cópia; sem migração de esquema | Escrita do documento inteiro; concorrência resolvida em processo | **adotada** |
| SQLite | ACID, leitores concorrentes, WAL | Binário; exige esquema e um runner que o projeto não tem | descartada agora, é o próximo passo atrás da mesma porta |
| PostgreSQL | Já existe para o histórico | Opcional; driver ausente no `.venv`; entrar exigiria o banco de pé | descartada (`L-26`) |
| Um arquivo por conta | Escrita pequena | Sem transação entre conta e token; diretório com N arquivos para inspecionar | descartada |

O volume é de dezenas de contas, com escrita rara — a linha de uma conta Google nasce uma vez; o reset grava uma vez. O documento inteiro é pequeno, e a leitura é cacheada por `(mtime_ns, tamanho)`.

### 3.3 Token de confirmação e de redefinição

| Alternativa | Prós | Contras | Veredito |
|---|---|---|---|
| **Aleatório de 32 bytes, guardado como derivação, uso único e validade** | Impede replay; vazamento do arquivo não entrega token utilizável | Precisa de índice por hash para busca O(1) | **adotada** |
| JWT assinado | Sem estado | Revogação exige lista negra; assinatura nova para gerenciar | descartada |
| Código curto de 6 dígitos | Fácil de digitar | Espaço pequeno; exige limite por tentativa e expiração curta | descartada |
| Token derivado do e-mail | Determinístico | Previsível | descartada |

### 3.4 Revogação de sessão

| Alternativa | Prós | Contras | Veredito |
|---|---|---|---|
| **Versão de credencial no cookie e no registro, conferida pela guarda** | Sem tabela de sessões; revoga todas as sessões da conta de uma vez | Uma leitura por requisição autenticada (amortecida por cache) | **adotada** |
| Tabela de sessões | Revogação seletiva | Contra o desenho sem estado de processo; escrita por requisição | descartada |
| Não revogar | Zero custo | Redefinir senha sem derrubar o invasor | descartada (`RN-10`) |

### 3.5 Anti-abuso e anti-CSRF

| Alternativa | Prós | Contras | Veredito |
|---|---|---|---|
| **Contador em memória por escopo e decorator** | Simples, testável com relógio falso | Reiniciar zera | **adotada** (risco declarado) |
| Redis / banco | Persistente | Dependência ou escrita | descartada |
| **Validação de `Origin` e `Sec-Fetch-Site`** | Sem estado, cobre login CSRF | Depende do navegador enviar o cabeçalho | **adotada** |
| Token CSRF em sessão anônima | Defesa clássica | Mais estado, mais tela, mais um token para errar | descartada nesta entrega |
| `SameSite=Strict` | Barra CSRF | Quebra o retorno do OAuth | descartada |

### 3.6 Segurança da unificação

| Alternativa | Prós | Contras | Veredito |
|---|---|---|---|
| **Unificar por e-mail verificado, com a senha definida só autenticado** | Impede pré-sequestro; preserva pasta e histórico | Exige uma tela a mais ("Definir senha") | **adotada** |
| Anexar senha no cadastro deslogado | Um passo a menos | **Vulnerável**: quem escolhe a senha primeiro ganha a conta quando o dono confirma | descartada |
| Nunca unificar | Simples | Duas pastas para a mesma pessoa; migração futura | descartada |

O pré-sequestro é a classe de ataque em que o atacante prepara a conta antes do dono: cadastra o e-mail alheio com a própria senha, e a vítima confirma o endereço sem perceber que está confirmando a credencial do atacante. A defesa adotada é não permitir que o cadastro deslogado toque em conta existente — a senha de uma conta Google só nasce de dentro da sessão dela.

## 4. Padrões aplicáveis, e onde cada um resolve variação real

| Padrão | Onde | Ponto de variação | Por que não é decorativo |
|---|---|---|---|
| **Adapter / Port** | `RepositorioDeContas`, `TransporteDeEmail` | Arquivo agora, Postgres depois; SMTP agora, outro transporte depois | Trocar o adaptador não toca domínio nem rota |
| **Repository** | `ports/contas_em_arquivo.py` | Persistência | O caso de uso pergunta "qual é a conta deste e-mail", não "como o JSON é escrito" |
| **Value Object** | `ContaDeAcesso`, `Credencial`, `Token`, `ResultadoDaPolitica` | — | Valores congelados impedem que a senha derivada ou o token circulem mutáveis |
| **Null Object** | `TransporteNulo` | Ausência de configuração | É o que mantém a subida de pé sem SMTP, como o registrador nulo da 008 |
| **Decorator** | `com_limite` sobre os casos de uso | Política de abuso | O caso de uso não sabe que existe contador; o limite pode ser desligado em teste |
| **Factory / composition root** | `create_app` | Montagem | Um lugar só decide qual adaptador entra, e a suíte injeta os de teste |

**Strategy foi considerada e recusada.** Os dois caminhos de entrada — Google e senha — não são intercambiáveis no ponto de chamada: um é redirecionamento com `state` e o outro é formulário. O que se compartilha é a `Conta` e a sessão, e isso já é valor, não estratégia. Uma `Strategy` ali seria decorativa, o que a `RNF-02` proíbe.

## 5. Fontes externas consultadas

- [OWASP — Password Storage Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/Password_Storage_Cheat_Sheet.html): derivação lenta com sal, parâmetros guardados e custo calibrado por hardware.
- [Python — `hashlib.scrypt`](https://docs.python.org/3/library/hashlib.html#hashlib.scrypt): assinatura, parâmetros de memória e custo.
- [NIST SP 800-63B](https://pages.nist.gov/800-63-3/sp800-63b.html): comprimento mínimo, limite superior e verificação contra senhas comuns.
- [Microsoft Security — pre-hijacking de contas](https://www.microsoft.com/en-us/security/blog/2022/05/23/account-pre-hijacking-attacks-revisited/): classe de ataque que orienta a `RN-20`.
- [The Register — metade dos sites populares vulneráveis a pré-sequestro](https://www.theregister.com/security/2022/05/25/about-half-of-popular-websites-vulnerable-to-pre-hijacking/): evidência de prevalência.
- [MDN — `SameSite` de cookie](https://developer.mozilla.org/en-US/docs/Web/HTTP/Headers/Set-Cookie/SameSite): por que `Lax` e não `Strict` no retorno do OAuth.
- [Flask — sessões](https://flask.palletsprojects.com/en/stable/quickstart/#sessions): cookie assinado e limpeza na troca de sessão.

## 6. O que será medido antes de fechar

1. Custo de `derivar_senha` no interpretador oficial (`.venv`, Python 3.14.6), com os parâmetros escolhidos — alvo até 250 ms.
2. Custo de uma verificação de versão por requisição autenticada, com o cache quente — alvo abaixo de 1 ms.
3. Tamanho do documento JSON com 1, 10 e 100 contas, para dimensionar escrita e backup.
4. Custo do `POST /login` no caminho de e-mail inexistente, para confirmar que a derivação falsa iguala o caminho.

Nenhuma dessas medições muda o desenho; elas mudam **números** e, se algum estourar, mudam a decisão de forma declarada — não silenciosa.

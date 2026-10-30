# Legacy impact: identidade local com senha

> Identificador: `053-conta-com-senha-e-recuperacao`
> Data: `2026-10-30`
> Extração de referência: `_reversa_sdd/` (2026-10-10 + adendos 051 e 052)
> Política de edição do legado no momento da execução: `allowLegacyEdits: true`, com
> `allowedPaths` liberando `src/**`, `tests/**`, `README.md`, `docker-compose.yml`, `.gitignore`,
> `docs/**`, `docker/**` e os arquivos de configuração do projeto. Nenhum caminho fora da lista
> foi tocado.

## 1. Arquivos afetados

| Arquivo afetado | Componente | Tipo | Severidade | Justificativa |
|---|---|---|---|---|
| `src/core/conta.py` (novo) | Núcleo — identidade | componente-novo | HIGH | Política de senha, credencial e conta de acesso; é a autoridade única da `RN-02` |
| `src/core/token_de_uso_unico.py` (novo) | Núcleo — identidade | componente-novo | HIGH | Emissão, validade e conferência de token; sem ele não há confirmação nem recuperação |
| `src/ports/__init__.py` | Portas | contrato-novo | MEDIUM | `RepositorioDeContas`, `TransporteDeEmail`, `Relogio` e `token_vigente` |
| `src/ports/contas_em_arquivo.py` (novo) | Portas — adaptador | componente-novo | HIGH | Persistência das contas, com trava e escrita atômica |
| `src/ports/email_smtp.py` (novo) | Portas — adaptador | componente-novo | MEDIUM | SMTP da biblioteca padrão e transporte nulo |
| `src/application/cadastro.py` (novo) | Aplicação | componente-novo | HIGH | Cadastro, resposta genérica e confirmação |
| `src/application/entrada_com_senha.py` (novo) | Aplicação | componente-novo | HIGH | Verificação de credencial e falha indistinguível |
| `src/application/recuperacao.py` (novo) | Aplicação | componente-novo | HIGH | Pedido, redefinição e revogação de sessão |
| `src/application/definir_senha.py` (novo) | Aplicação | componente-novo | MEDIUM | Primeira senha da conta autenticada |
| `src/application/vinculo.py` (novo) | Aplicação | componente-novo | HIGH | Unificação por e-mail verificado e barreira ao pré-sequestro |
| `src/application/limite.py` (novo) | Aplicação | componente-novo | MEDIUM | Contador de tentativas por escopo |
| `src/application/sessao_da_conta.py` (novo) | Aplicação | componente-novo | HIGH | Verificação da versão de credencial na guarda |
| `src/web/rotas_conta.py` (novo) | Borda HTTP | contrato-novo | HIGH | Seis rotas de identidade e tradução das exceções |
| `src/web/origem.py` (novo) | Borda HTTP | componente-novo | MEDIUM | Recusa de `POST` de outra origem |
| `src/web/textos_de_conta.py` (novo) | Apresentação | componente-novo | MEDIUM | Literais da `RN-13` em um lugar só |
| `src/web/sessao.py` | Sessão | regra-alterada | HIGH | `Conta.versao`, verificador injetado e endpoints públicos novos |
| `src/web/rotas_auth.py` | Borda HTTP | regra-alterada | HIGH | `POST /login` com credencial e vínculo no callback |
| `src/utils/auditoria.py` | Observabilidade | regra-alterada | MEDIUM | Cinco ações novas no conjunto fechado |
| `src/app.py` | Borda / composição | contrato-alterado | HIGH | Montagem das três portas, `no-store` de identidade e aviso sem SMTP |
| `src/templates/_entrada_base.html` (novo) | Apresentação | componente-novo | LOW | Base das cinco telas |
| `src/templates/login.html` | Apresentação | regra-alterada | MEDIUM | Google primeiro, campos, links e ícone da aba |
| `src/templates/cadastro.html` (novo) | Apresentação | componente-novo | LOW | Cadastro |
| `src/templates/recuperar_senha.html` (novo) | Apresentação | componente-novo | LOW | Pedido de recuperação |
| `src/templates/redefinir_senha.html` (novo) | Apresentação | componente-novo | LOW | Nova senha |
| `src/templates/definir_senha.html` (novo) | Apresentação | componente-novo | LOW | Primeira senha autenticada |
| `src/templates/mensagem.html` (novo) | Apresentação | componente-novo | LOW | Resultado genérico, confirmação e reenvio |
| `src/templates/index.html` | Apresentação | regra-alterada | MEDIUM | Link "Definir senha" na masthead, sob `conta_tem_sem_senha` |
| `src/assets/app.css` | Apresentação | regra-alterada | LOW | Bloco do cartão de identidade |
| `.gitignore` | Operação | delta-de-dados | MEDIUM | Passa a ignorar `dados/` |
| `docker-compose.yml` | Operação | delta-de-dados | MEDIUM | Volume `./src/dados:/app/src/dados` |
| `README.md` | Documentação | regra-alterada | LOW | Seção da entrada local e variáveis de SMTP |
| `tests/*` (14 arquivos novos e 2 alterados) | Instrumentação | componente-novo | MEDIUM | Cobertura da feature e atualização do contrato de tela |

## 2. Diff conceitual por componente

**Identidade (novo).** O sistema deixa de ter uma única porta de entrada. A conta local é um valor
congelado (`ContaDeAcesso`) com credencial derivada por `scrypt`, e-mail normalizado e `sub` opaco. A
política de senha é a única autoridade sobre o que é aceitável; nenhuma rota a reimplementa.

**Portas.** A fronteira ganha três contratos. O repositório isola o formato de armazenamento (hoje JSON,
amanhã Postgres), o transporte isola o envio (hoje SMTP, amanhã outro), e o relógio existe para o teste de
expiração ser determinístico. `token_vigente` nasceu para a tela de redefinição não consumir o token de quem
só abriu o link.

**Aplicação.** Quatro casos de uso e três serviços de apoio. A regra que atravessa todos: o cadastro
deslogado nunca altera conta existente, e a resposta da tela nunca revela se um e-mail tem conta.

**Sessão.** `Conta` ganhou `versao`, e a guarda passou a aceitar um verificador injetado. A lista de
endpoints públicos cresceu com as cinco rotas de quem ainda não tem sessão; a lista continua fechada e
nomeando endpoints, não prefixos.

**Borda.** `create_app` monta as três portas e injeta os serviços; sem entrada configurada, nada disso é
registrado — a suíte e a paridade continuam no caminho da 051. As páginas de identidade ganham `no-store`
mesmo sem sessão, e as com token ganham `no-referrer`.

**Observabilidade.** Cinco ações novas na trilha. A linha identifica a conta pelo `sub`; e-mail, senha e
token nunca entram.

## 3. Regras preservadas

- Os **três eixos** do domínio e o confronto em quatro estados (`ADR-14`) — a identidade não toca em
  análise, busca nem veredito.
- As **233 regras** catalogadas do núcleo, os fluxos de upload, aposentadoria e reenvio.
- Os **29 literais** da extração e os **7 da 051**; a frase e o botão do Google permanecem byte a byte.
- O **isolamento por dono** da 051: pasta e histórico continuam escopados pelo `sub`.
- A **guarda de instância única** e o `TRUSTED_HOSTS`.
- `SHA_DA_TELA` e `tests/test_combobox_de_nomes.py`, intocados.
- A paridade diferencial, sem divergência nova.

## 4. Regras modificadas ou removidas

- **Autenticação**: de "somente Google" para "Google e credencial local". A `permissions.md` §4.3, que
  declarava autenticação coberta apenas pelo provedor, passa a ter duas formas de entrada.
- **Sessão**: passou a carregar a versão de credencial e a poder ser revogada por redefinição.
- **Tela de entrada**: o contrato de tela mudou por decisão declarada (`RN-17`); o teste antigo foi
  atualizado junto, no mesmo commit.
- **Auditoria**: o conjunto fechado de ações cresceu; nenhuma ação antiga foi renomeada.
- **Integrações externas**: o SMTP entra como segunda saída de rede, depois do Google — a afirmação
  "nenhuma integração de rede com terceiros" já era falsa desde a 051 e continua sendo lida com o adendo.
- **Nada foi removido.** Nenhum arquivo do projeto foi apagado nesta entrega.

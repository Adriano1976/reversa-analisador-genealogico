# Legacy impact: login com Google e isolamento por dono

> Identificador: `051-login-google-e-isolamento`
> Data: `2026-10-27`
> Política de edição do legado: `allowLegacyEdits: true`, com `allowedPaths` liberando `src/**`,
> `tests/**`, `requirements.txt`, `docker-compose.yml`, `README.md` e os demais caminhos já declarados
> em `.reversa/reversa-config.json`. Nenhum caminho fora da lista foi tocado.

## Arquivos afetados

| Arquivo afetado | Componente | Tipo | Severidade | Justificativa |
|---|---|---|---|---|
| `src/web/sessao.py` (novo) | Sessão da borda | componente-novo | HIGH | Conta, cookie, guarda e `no-store`; autoridade única de "quem está logado" |
| `src/web/autenticacao.py` (novo) | Entrada pelo provedor | componente-novo | HIGH | Fluxo OAuth 2.0, configuração das cinco variáveis e fail-closed |
| `src/web/rotas_auth.py` (novo) | Rotas de entrada | contrato-novo | HIGH | `/login`, `/callback`, `/logout` e a adoção na entrada |
| `src/application/dono_inicial.py` (novo) | Adoção de dados | regra-nova | MEDIUM | Cópia idempotente, marcador e aviso de dados não atribuídos |
| `src/app.py` | Borda HTTP | contrato-alterado | HIGH | Guarda, `_dono()`, injeção da autenticação, fail-closed e `404` na referência que não resolve |
| `src/ports/__init__.py` | Portas | contrato-alterado | HIGH | O `dono` passa a filtrar; `RegistroDeAnalises.adotar` nasce |
| `src/ports/adaptadores.py` | Armazenamento e histórico | regra-alterada | HIGH | Pasta por dono, validação de forma do dono e `adotar` no registrador |
| `src/utils/auditoria.py` | Observabilidade | contrato-alterado | LOW | Ações `entrar`/`sair` e campo `conta` |
| `src/templates/index.html` | Apresentação | delta-de-contrato-externo | MEDIUM | Masthead com a conta e "Sair" |
| `src/templates/login.html` (novo) | Apresentação | componente-novo | MEDIUM | Tela de entrada; segundo template do sistema |
| `src/assets/app.css` | Apresentação | componente-alterado | LOW | Estilos da entrada e da conta |
| `requirements.txt` | Dependências | componente-novo | LOW | `requests==2.32.5`, com import preguiçoso |
| `docker-compose.yml` | Empacotamento | delta-de-contrato-externo | MEDIUM | As cinco variáveis com `${VAR:?}` |
| `README.md` | Documentação | regra-alterada | LOW | Aviso de "sem autenticação" deixa de valer; seção de configuração nova |
| `tests/**` | Instrumento | sem-impacto no legado | LOW | 32 testes novos e 8 asserções de contrato atualizadas |

## Diff conceitual por componente

**Borda HTTP (`src/app.py`).** As sete operações de dado passam por uma guarda única de
`before_request`; sem sessão, `GET` recebe `302` e `POST` recebe `303` para `/login`, e nenhum handler
roda. O literal `DONO_DO_PROCESSO` deixou de alimentar as chamadas de porta: `_dono()` responde o `sub`
da sessão e cai no literal apenas no caminho sem autenticação (suite e paridade). A referência que não
resolve passou a responder **`404`** com o mesmo texto de antes — nunca `403` —, e o mesmo vale para
aposentar e para o CSV da análise.

**Portas (`src/ports/`).** O `dono` deixou de ser costura: `guardar`, `resolver`, `listar`, `aposentar`
e `carregar` o usam como escopo. `RegistroDeAnalises` ganhou `adotar(dono_anterior, dono_novo)`, que é
um `UPDATE` condicionado e idempotente.

**Armazenamento (`ArmazenamentoEmDisco`).** Cada dono tem a própria pasta (`<base>/<dono>/`) e a própria
`_aposentados`. O **dono legado `"unico"` é a exceção declarada**: ele continua na raiz, porque é o
espaço que existe sem sessão — é o que a suíte e o invólucro de paridade exercitam. Nenhuma sessão
autenticada chega a esse valor (o `sub` do provedor é numérico), e o isolamento real é medido com dois
`sub` em `tests/test_isolamento_por_dono.py`.

**Entrada e sessão (`src/web/`).** Fluxo OAuth 2.0 manual: `state` de 32 bytes de uso único, troca do
código e leitura do perfil no servidor, `id_token` ignorado (não há criptografia a instalar). O cookie
é assinado, `HttpOnly`, `SameSite=Lax`, `Secure` sob HTTPS e expira em 12 h de inatividade. A sessão é
limpa no login (fixação) e no logout, e as respostas autenticadas saem com `Cache-Control: no-store`.

**Adoção (`src/application/dono_inicial.py`).** No primeiro login da conta declarada em
`ANALISADOR_DONO_INICIAL`, os arquivos da raiz e os aposentados são **copiados** para a pasta do dono,
o histórico com `owner_id = 'unico'` é adotado pela porta e um marcador `.dono-inicial` fecha a cópia.
Nada é apagado ou movido; a segunda execução é no-op.

**Observabilidade.** A trilha ganhou `acao=entrar` e `acao=sair`, com o campo `conta=<sub>`; o e-mail
nunca entra na linha. Nenhum token, código ou segredo é registrado.

## Preservadas

- Os **quatro estados** do confronto e a separação dos três eixos (`domain.md#2.1`, `#3.1` a `#3.4`).
- A leitura tolerante do CSV, a ordem de apresentação e a arte derivada (`domain.md#3.8`, `#3.9`, `#3.10`).
- Os **29 literais** de tela catalogados em `domain.md#5`; os novos são acréscimo, não substituição.
- A chave de conteúdo como nome armazenado (`<chave>__<nome visível>`), o teto de 16 MB, a validação antes da gravação e a aposentadoria que move sem apagar.
- A árvore por parâmetro, sem estado global, e o cache por caminho absoluto (que agora distingue donos).
- O `TRUSTED_HOSTS`, o `X-Frame-Options: DENY` e o comportamento do `Host` recusado.
- A paridade: **30 divergências**, o mesmo número da linha de base da 049/050.

## Modificadas

- **`domain.md#3.5` / `permissions.md#1.1`:** o mesmo conteúdo enviado por dois donos deixou de reencontrar o mesmo arquivo; a deduplicação vale dentro do dono (`RN-05`).
- **`permissions.md#3`:** a matriz deixou de ser degenerada; a coluna "ler arquivo de outro dono" passou a ❌, com `404` indistinguível de inexistente.
- **`architecture.md#6`:** a afirmação "nenhuma integração de rede com terceiros" deixou de valer — o Google é o primeiro provedor externo de identidade.
- **Contrato de tela:** a referência que não resolve passou de `200` para **`404`** (mesmo texto); a masthead ganhou conta e "Sair"; o `SHA_DA_TELA` foi remedido (`df702cbb…`, 51.150 bytes, +33).
- **`dna_analysis.owner_id`:** passou a receber o `sub`; a coluna continua `TEXT`, sem FK (a lacuna `E-06` permanece aberta e declarada).
- **`app.py`:** o literal `DONO_DO_PROCESSO` deixou de ser o dono do caminho servido.

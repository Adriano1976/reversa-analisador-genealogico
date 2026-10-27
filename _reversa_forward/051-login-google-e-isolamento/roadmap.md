# Roadmap: login com Google e isolamento por dono

> Identificador: `051-login-google-e-isolamento`
> Data: `2026-10-26`
> Requirements: `_reversa_forward/051-login-google-e-isolamento/requirements.md`
> Confidência: 🟢 CONFIRMADO, 🟡 INFERIDO, 🔴 LACUNA

## 1. Resumo da abordagem

A entrada vira um portão único na borda. Um serviço de autenticação é montado a partir do ambiente e **injetado** em `create_app`; quando ele existe, cada requisição resolve a conta da sessão e o `sub` do provedor passa a ser o `dono` de todas as chamadas de porta. O fluxo OAuth é implementado no próprio projeto — autorização, troca de código e leitura do perfil — com `requests` importado preguiçosamente e **sem** validar `id_token`, o que dispensa biblioteca de criptografia.

O armazenamento deixa de ser um balde único: cada dono ganha `<pasta>/<sub>/`, com `_aposentados` dentro do espaço dele, e a referência `<chave>__<nome>` continua com o mesmo formato — ela só passa a ser resolvida **dentro** do escopo. Os dados anteriores são **copiados** (nunca movidos) para a pasta da conta declarada em `ANALISADOR_DONO_INICIAL`, no primeiro login dessa conta, com marcador de ida única; o histórico com `owner_id = 'unico'` é adotado pela mesma porta que grava.

Sem as cinco variáveis de ambiente, o **servidor** não sobe; o import e a suíte continuam funcionando, porque a autenticação é injetável e o caminho legado segue sendo o default de `create_app` — é o seam que mantém os 1.717 testes verdes e o harness de paridade intacto.

## 2. Princípios aplicados

| Princípio | Como a feature se relaciona | Status |
|-----------|------------------------------|--------|
| I. Dados reais nunca versionados | Toda conta usada em teste é sintética; o e-mail da conta não entra em fixture, golden, trilha nem documentação, e a trilha grava o identificador (`sub`), nunca o e-mail | respeita |
| II. Comportamento observável preservado em refatoração | A tela anônima muda **por requisito**, e não disfarçada de refactor: a feature percorre o fluxo de requisito. No caminho autenticado, os 29 literais de tela continuam intactos | respeita |
| III. Nenhuma mudança sem teste | O teste negativo A→B é portão do critério de pronto, e a migração tem teste de idempotência | respeita |
| IV. Arestas do grafo são tipadas | A feature não percorre o grafo | n/a |
| V. Suposição de genealogia cita a fonte | A feature não cria número nem heurística de domínio | n/a |

> **Tensão declarada, e não escondida:** o layout de armazenamento muda, e cerca de quinze asserções de pasta em nove arquivos de teste existentes passam a afirmar o layout novo. Isso é **atualização de contrato** — as asserções ficam mais fortes, não mais frouxas —, e cada uma é listada no `legacy-impact.md` da execução. Ver `R-01`.

## 3. Decisões técnicas

| ID | Decisão | Justificativa | Alternativas descartadas | Confidência |
|----|---------|----------------|--------------------------|-------------|
| D-01 | Identidade é o `sub` do provedor; **não** há tabela de contas, e `owner_id` continua `TEXT` guardando o `sub` | A sessão assinada carrega a conta; uma tabela exigiria PostgreSQL para **entrar**, quebrando o uso local sem Docker. `RN-01`, `RN-15` e `RF-10` não pedem registro, pedem identidade estável | (a) tabela `app_user` do documento; (b) SQLite local — terceiro regime de persistência | 🟢 |
| D-02 | Sessão é o cookie assinado do Flask, com segredo de `ANALISADOR_SECRET_KEY`; `HttpOnly`, `SameSite=Lax`, `Secure` quando a URL pública for HTTPS, validade de 12 h deslizantes | Sem estado de sessão no processo: reinício do servidor não derruba o operador, e o processo continua sem estado de domínio (`architecture.md#2`). A assinatura usa `itsdangerous`, que já vem com o Flask — nenhuma dependência nova para assinar | (a) sessão em memória; (b) arquivo de sessões; (c) tabela de sessões | 🟢 |
| D-03 | Fluxo OAuth 2.0 **manual** com `requests`: autorização, troca de código e leitura do perfil no endpoint de userinfo; sem `id_token`, sem validação de JWT, sem biblioteca de criptografia | O fluxo cabe em um módulo testável; o `id_token` é dispensável porque a troca do código e a leitura do perfil acontecem no servidor, sobre TLS. Evita a cadeia de `cryptography`/`joserfc` e o risco de wheel em cp314 | (a) Authlib — cadeia pesada; (b) `requests-oauthlib`; (c) validação de `id_token` com criptografia | 🟢 |
| D-04 | `state` de 32 bytes (`secrets.token_urlsafe`) guardado na sessão e de uso único; `redirect_uri` montado de `ANALISADOR_URL_PUBLICA`, nunca do cabeçalho `Host` | Fecha o retorno forjado e o redirecionamento aberto; o Host já é validado pelo `TRUSTED_HOSTS` (adendo 014), mas a URL de retorno não pode depender dele | (a) sem `state`; (b) `redirect_uri` derivado de `request.url_root` | 🟢 |
| D-05 | Guarda única na borda (`before_request`): as sete operações de dado exigem sessão; `GET` sem sessão → `302 /login`, `POST` sem sessão → `303 /login`. Públicas: `/login`, `/callback` e as três rotas de arte e de folha de estilo | Um ponto único não pode ser esquecido; a lista pública é fechada e por endpoint, não por prefixo de caminho | (a) decorador em cada rota; (b) guarda por path | 🟢 |
| D-06 | Armazenamento escopado por pasta: `<base>/<sub>/<chave>__<nome>` e `<base>/<sub>/_aposentados/`; o `dono` é validado por forma (`^[A-Za-z0-9_-]{1,64}$`) antes de compor caminho | Mantém o formato da referência e a chave por conteúdo **dentro** do dono; o caminho passa a distinguir donos, que é o que o `ADR-38` já antecipava para o cache da árvore | (a) dono no nome do arquivo — quebra o formato; (b) índice lateral de donos — concorrência de disco; (c) balde único — não isola | 🟢 |
| D-07 | Migração dos dados anteriores por **cópia** para a pasta da conta inicial, mais a adoção do histórico pela porta, com marcador `<base>/.dono-inicial`; idempotente, nada é apagado | Cópia preserva o original para rollback manual e torna literal a promessa de "nenhum arquivo é apagado"; o marcador é o que impede repetir a adoção | (a) mover os arquivos; (b) atribuir no primeiro login de qualquer conta — entrega o acervo ao primeiro estranho | 🟢 |
| D-08 | A conta inicial é declarada em `ANALISADOR_DONO_INICIAL` (e-mail verificado) e a migração só roda quando o e-mail autenticado casa | O `sub` não é digitável nem previsível antes do primeiro login; declarar por e-mail é o único caminho que não depende de inferência | (a) declarar o `sub`; (b) migrar no primeiro login | 🟢 |
| D-09 | `create_app` ganha `autenticacao=None` injetável; o app de módulo monta do ambiente, e **sem injeção** o caminho é o legado (sem guarda) | É o seam que mantém a suíte e o harness de paridade sem credencial, e é o mesmo padrão de `armazenamento`, `carregador`, `registro` e `dependencias` | (a) guarda sempre ativa; (b) desligar por variável de ambiente em teste | 🟢 |
| D-10 | Fail-closed na **subida** (`__main__`): faltando qualquer das cinco variáveis, `SystemExit` que nomeia as ausentes; o import continua funcionando | Fecha o risco de subir aberto por esquecimento sem quebrar `import app`, que a suíte e o harness fazem | (a) checar no import; (b) avisar e subir no modo legado | 🟢 |
| D-11 | `requests` pinado no `requirements.txt`, importado **dentro** da função de troca de token | Mesmo padrão de `psycopg2` e `graphviz` (`L-26`): a ausência do pacote não pode derrubar `import app`; com autenticação ligada, a falta dele entra no fail-closed | (a) import no topo; (b) biblioteca de OAuth completa | 🟢 |
| D-12 | Nova tela `src/templates/login.html`, masthead com a conta e "Sair", estilos em `src/assets/app.css`, e `Cache-Control: no-store` nas respostas autenticadas | A tela deixa de ser um template único, o que é delta declarado contra `architecture.md#3`; o `no-store` é o que impede o "voltar" de exibir a tela autenticada depois do logout (`RF-06`) | (a) renderizar o login dentro de `index.html`; (b) sem `no-store`, confiando no servidor | 🟢 |
| D-13 | Auditoria ganha as ações `entrar`/`sair` e o campo `conta` (o `sub`); o e-mail nunca entra na trilha | `RN-12`; a trilha sobrevive à requisição e o e-mail é dado pessoal, ao contrário do identificador | (a) gravar o e-mail; (b) não auditar a entrada | 🟢 |
| D-14 | Sem token CSRF por formulário: `SameSite=Lax` mais o `state` do OAuth | O cookie `Lax` não acompanha `POST` de outra origem, e não há formulário sensível fora da sessão; a decisão fica declarada para reabertura | (a) token por formulário — superfície nova sem vetor medido | 🟡 |

## 4. Premissas

Nenhuma. O `requirements.md` chegou ao plano com **zero** marcadores `[DÚVIDA]`: as três dúvidas de 2026-10-26 foram resolvidas na sessão de esclarecimentos e viraram `RN-01`, `RN-15`, `RN-16`, `RF-12` e `RF-16`.

## 5. Delta arquitetural

| Componente | Arquivo de origem no legado | Tipo de mudança | Resumo |
|------------|------------------------------|-----------------|--------|
| Borda HTTP (`src/app.py`) | `_reversa_sdd/architecture.md#1` | contrato-alterado | As sete operações de dado passam por guarda; `_dono()` substitui o literal nas oito chamadas; `create_app` recebe `autenticacao`; a subida valida as cinco variáveis |
| Contexto (C4 nível 1) | `_reversa_sdd/c4-context.md` | contrato-alterado | A persona deixa de ser "sem login e sem sessão", e o Google entra como o primeiro sistema externo de identidade |
| Portas (`src/ports/`) | `_reversa_sdd/architecture.md#3` | contrato-alterado | O `dono` deixa de ser costura e passa a filtrar; `RegistroDeAnalises` ganha `adotar`; os docstrings que afirmam "não filtra" são reescritos |
| Armazenamento (`ArmazenamentoEmDisco`) | `_reversa_sdd/architecture.md#2` | componente-alterado | Pasta por dono, aposentados por dono, validação de forma do `dono` antes de compor caminho |
| Apresentação (`src/templates/`, `src/assets/`) | `_reversa_sdd/architecture.md#3` | componente-novo + contrato-alterado | `login.html` é o segundo template; a masthead ganha conta e "Sair"; `SHA_DA_TELA` é remedido |
| Integração externa (Google) | `_reversa_sdd/architecture.md#6` | componente-novo | **A primeira integração de rede com terceiro do sistema**: a afirmação "nenhuma integração de rede com terceiros" deixa de valer |
| Sessão (novo) | — | componente-novo | Cookie assinado, guarda de borda e helpers em `src/web/` |
| Observabilidade | `_reversa_sdd/addenda/049-sistema-de-log.md` | contrato-alterado | Conjunto fechado de ações ganha `entrar`/`sair`; a linha ganha o campo `conta` |

## 6. Delta no modelo de dados

- Resumo: **nenhuma tabela nova**. `dna_analysis.owner_id` continua `TEXT` e passa a receber o `sub`; os dados antigos com `'unico'` são adotados pela porta uma vez. No disco, o layout deixa de ser plano e passa a ser `<base>/<sub>/`, com migração por cópia e marcador.
- Detalhe completo em: `_reversa_forward/051-login-google-e-isolamento/data-delta.md`

## 7. Delta de contratos externos

| Contrato | Tipo | Arquivo de detalhe |
|----------|------|--------------------|
| Entrada e sessão (`/login`, `/callback`, `/logout`, guarda das sete operações, cookie) | HTTP | `_reversa_forward/051-login-google-e-isolamento/interfaces/entrada-e-sessao.md` |
| Provedor de identidade (Google OAuth 2.0) | HTTP de saída | `_reversa_forward/051-login-google-e-isolamento/interfaces/provedor-de-identidade.md` |

## 8. Plano de migração

1. Publicar o código com a autenticação **desligada** (sem as variáveis): o comportamento é o de hoje, e a suíte roda igual.
2. Configurar as cinco variáveis e subir; o servidor passa a exigir entrada.
3. Primeiro login da conta declarada em `ANALISADOR_DONO_INICIAL`: a aplicação copia `src/uploads/*` para `src/uploads/<sub>/`, copia `_aposentados/` para `src/uploads/<sub>/_aposentados/`, adota as linhas de `dna_analysis` com `owner_id = 'unico'` e grava o marcador `.dono-inicial`. Os originais **permanecem** onde estavam.
4. Conferir a lista: os arquivos aparecem para a conta inicial e para mais ninguém.
5. Segundo login, de outra conta Google: lista vazia, e nenhuma referência da primeira resolve.
6. Rollback: voltar o código (não há modo legado servível) e, se necessário, apontar `ANALISADOR_UPLOAD_FOLDER` para a pasta antiga — os originais nunca saíram do lugar.

## 9. Riscos e mitigações

| Risco | Impacto | Probabilidade | Mitigação |
|-------|---------|---------------|-----------|
| `R-01` — A mudança de layout quebra cerca de quinze asserções de pasta em nove arquivos de teste | alto | alta | Atualização declarada de contrato, não afrouxamento: cada asserção passa a afirmar o layout novo, e o total de testes não pode cair. Lista nominal no `legacy-impact.md` |
| `R-02` — A migração mexe em dado real (13 arquivos, 29 MB) | alto | média | Cópia, nunca movimento; marcador de ida única; log por arquivo; teste de idempotência com árvore sintética |
| `R-03` — A entrada depende de internet e do provedor | alto | alta | Consequência aceita (`RN-14`); a tela diz que não foi possível entrar; não há queda silenciosa para o modo legado |
| `R-04` — `redirect_uri` divergente entre `:5000` e `:5080` | médio | alta | As quatro URIs registradas no provedor estão no `onboarding.md`; erro `redirect_uri_mismatch` tem diagnóstico na tela |
| `R-05` — Cookie sem `Secure` no uso local em HTTP | médio | média | `Secure` desligado apenas quando a URL pública é `http://`; o perímetro continua o loopback |
| `R-06` — `ANALISADOR_DONO_INICIAL` com e-mail diferente do real deixa o acervo invisível | alto | média | Aviso no log quando há dados não atribuídos e a conta entrou com e-mail diferente; passo explícito no onboarding |
| `R-07` — Cache da árvore compartilhado entre donos | baixo | baixa | A chave é o caminho absoluto; com pasta por dono o caminho já distingue (o `ADR-38` previu exatamente isso) |
| `R-08` — `requests` ausente no interpretador oficial | médio | média | Import preguiçoso; com autenticação ligada, a ausência entra no fail-closed da subida, nomeando o pacote |
| `R-09` — Entrada aberta a qualquer conta, sem limite de criação | médio | alta | Decisão de 2026-10-26 (`D1`); o perímetro é o loopback por padrão, e o limite fica registrado como ponto do plano |

## 10. Critério de pronto

- [ ] Todas as ações do `actions.md` marcadas `[X]`
- [ ] Teste negativo A→B com `404` (e sem `403`) nas cinco operações de dado — portão de go-live
- [ ] Mesmo conteúdo enviado por dois donos gera dois arquivos, e aposentar um não afeta o outro
- [ ] Migração idempotente: segunda execução não copia, não duplica e não reescreve; nenhum arquivo apagado
- [ ] Suíte sem rede e sem credencial: marco de 1.717 passam / 9 pulados / 0 falham preservado, mais os testes novos
- [ ] Paridade nas 30 divergências já conhecidas, sem regressão
- [ ] `SHA_DA_TELA` atualizado por medição no mesmo commit que muda a masthead
- [ ] `permissions.md` com matriz não degenerada, `ADR-39` escrito e `architecture.md`/`c4-*` atualizados (etapa `sync`)
- [ ] Onboarding executado uma vez pelo operador, com uma segunda conta Google

## 11. Histórico de alterações

| Data | Alteração | Autor |
|------|-----------|-------|
| 2026-10-26 | Versão inicial gerada por `/reversa-plan` a partir do requirements esclarecido de 2026-10-26 | reversa |

# Data delta: contas locais em arquivo

> Identificador: `053-conta-com-senha-e-recuperacao`
> Data: `2026-10-30`
> Requirements: `_reversa_forward/053-conta-com-senha-e-recuperacao/requirements.md`
> Confidência: 🟢 CONFIRMADO, 🟡 INFERIDO, 🔴 LACUNA

## 1. O modelo hoje

| Onde | Estruturas | Persiste? |
|---|---|---|
| Memória, por requisição | `Conta{sub,email,nome}` na sessão assinada | Não — vive no cookie |
| Disco | `src/uploads/` e `_aposentados/` | Sim — conteúdo imutável, posição mutável |
| PostgreSQL (opcional) | 6 tabelas do histórico — `dna_analysis`, `analysis_person`, `match_result`, `match_path_node`, `match_kit`, `skipped_match` | Sim |

**Não existe tabela de conta.** `owner_id` é `TEXT` sem FK e sem índice de escopo (`_reversa_sdd/erd-complete.md`, E-06), e o `dono` só ganhou comportamento na 051 porque o `sub` do Google passou a escopar a pasta. O esquema é do **histórico**, não da identidade.

## 2. O modelo depois

Nasce **um documento JSON** em `src/dados/contas.json` (caminho configurável por `ANALISADOR_CONTAS`), com duas coleções: `contas` e `tokens`.

```json
{
  "versao": 1,
  "contas": {
    "local-3f6a…": {
      "sub": "local-3f6a…",
      "email": "operador@example.com",
      "email_normalizado": "operador@example.com",
      "google_sub": null,
      "nome": "",
      "credencial": {
        "algoritmo": "scrypt",
        "n": 16384,
        "r": 8,
        "p": 1,
        "sal": "<base64 de 16 bytes>",
        "hash": "<base64 de 32 bytes>"
      },
      "verificado_em": "2026-10-30T12:00:00Z",
      "criado_em": "2026-10-30T11:58:00Z",
      "versao_de_credencial": 0,
      "token_confirmacao": null,
      "token_redefinicao": null
    }
  },
  "tokens": {
    "<sha256 hex do token>": {
      "sub": "local-3f6a…",
      "tipo": "confirmacao",
      "expira_em": "2026-10-31T11:58:00Z"
    }
  }
}
```

## 3. Campos da conta

| Campo | Tipo | Nulo? | Semântica | Conf. |
|---|---|---|---|---|
| `sub` | texto, `[a-z0-9-]` | não | Dono canônico; é o nome da pasta em `src/uploads/` e o identificador da auditoria. Nunca muda, nem na unificação | 🟢 |
| `email` | texto | não | O e-mail como o operador escreveu, só para exibição e para o endereço de envio | 🟢 |
| `email_normalizado` | texto | não | Aparado e em caixa baixa; **único** entre contas. É a chave de busca do login e da recuperação | 🟢 |
| `google_sub` | texto | sim | O `sub` do provedor, quando a conta já entrou pelo Google. **Único** quando presente | 🟢 |
| `nome` | texto | não (pode ser vazio) | Nome de exibição, quando veio do Google | 🟢 |
| `credencial` | objeto | sim | Ausente em conta só-Google. Presente em conta local, confirmada ou não | 🟢 |
| `verificado_em` | data/hora UTC | sim | Instante da confirmação do e-mail. Nulo significa conta não confirmada (só existe em conta local) | 🟢 |
| `criado_em` | data/hora UTC | não | Criação do registro | 🟢 |
| `versao_de_credencial` | inteiro ≥ 0 | não | Sobe a cada redefinição; a sessão carrega o valor em que nasceu (RN-10) | 🟢 |
| `token_confirmacao` | hash hex | sim | Hash do token vigente de confirmação; o token anterior é descartado ao emitir outro | 🟢 |
| `token_redefinicao` | hash hex | sim | Hash do token vigente de redefinição, mesma regra | 🟢 |

### 3.1 O objeto `credencial`

| Campo | Tipo | Semântica |
|---|---|---|
| `algoritmo` | texto | Hoje sempre `scrypt`; o campo existe para o futuro |
| `n`, `r`, `p` | inteiros | Parâmetros da derivação, gravados com o hash para permitir endurecer depois sem quebrar contas antigas |
| `sal` | base64 | 16 bytes aleatórios por conta |
| `hash` | base64 | 32 bytes derivados da senha com o sal e os parâmetros |

**A senha em claro não existe em lugar nenhum** — nem no documento, nem em log, nem na sessão. O documento guarda o suficiente para verificar, não para recuperar.

## 4. Coleção `tokens`

Chaveada pelo **sha256 do token**, para busca O(1) no consumo e para que o vazamento do arquivo não entregue token utilizável.

| Campo | Tipo | Semântica |
|---|---|---|
| `<hash>` | chave | sha256 hexadecimal do token em claro, que só existe no e-mail e na URL |
| `sub` | texto | Conta dona do token |
| `tipo` | `confirmacao` \| `redefinicao` | Decide a validade e a tela de consumo |
| `expira_em` | data/hora UTC | 24 h para confirmação; 60 min para redefinição |

Um token novo do mesmo tipo **substitui** o anterior daquela conta: o hash antigo sai da coleção e o campo da conta aponta para o novo. Token consumido é removido, e um segundo uso cai na mensagem de "expirado ou já usado".

## 5. Invariantes

1. `email_normalizado` é única entre contas — dois cadastros com o mesmo e-mail normalizado apontam para a mesma conta.
2. `google_sub`, quando presente, é único.
3. `sub` é único, casa com `[a-z0-9-]+` e **nunca** é derivado do e-mail.
4. Conta sem `credencial` é conta só-Google e não entra por senha; conta com `credencial` e sem `verificado_em` não abre sessão.
5. `token_confirmacao` e `token_redefinicao` guardam apenas hash; o token em claro nunca é escrito.
6. `versao_de_credencial` só cresce, e só na redefinição.
7. O documento é escrito inteiro, em temporário mais `os.replace`; nunca é editado no lugar.

## 6. Índices e busca

O documento **não tem índice persistido**. O adaptador mantém, em memória, dois mapas derivados — `email_normalizado → sub` e `google_sub → sub` — reconstruídos na carga e invalidados na escrita. Com dezenas de contas, a varredura linear seria suficiente; os mapas existem para o caminho de login não varrer o documento a cada tentativa. A escolha é declarada: se o número de contas crescer a ponto de o documento não caber confortavelmente em memória, o passo seguinte é SQLite atrás da **mesma** porta.

## 7. Migração

| Situação | O que acontece |
|---|---|
| Instalação nova | O arquivo nasce no primeiro cadastro; a pasta `src/dados/` é criada no primeiro uso |
| Instalação com contas Google | **Nenhuma migração em lote.** A linha da conta nasce no primeiro login Google depois do deploy, com `verificado_em` preenchido, sem `credencial` e com o **mesmo** `sub` do provedor — a pasta de uploads não muda de nome |
| Conta Google que quer senha | Entra pelo Google e usa "Definir senha"; o `sub` e a pasta continuam os mesmos (`RF-24`) |
| Conta local que também usa Google | A entrada Google anexa `google_sub` à conta local e usa o `sub` dela (`RN-20`) |
| Reversão da feature | Remover o volume/arquivo e o código; o caminho Google volta a funcionar sozinho. Nenhum dado do operador é apagado |

## 8. O que NÃO muda

- `init.sql` (6 tabelas do histórico) — **intocado**. Não há tabela `app_user` nesta entrega; ela continua pertencendo à Onda 3 do alvo.
- `_reversa_sdd/erd-complete.md` — o Diagrama E é o esquema **Postgres** e não ganha estrutura.
- `_reversa_sdd/data-dictionary.md` — descreve o banco e as estruturas de memória do fluxo de análise; a conta local não entra nele nesta rodada.
- `src/uploads/` — a pasta por dono continua igual; o arquivo de contas fica em `src/dados/`, justamente para **não** aparecer na lista da tela de entrada.

## 9. Operação, backup e segurança do arquivo

| Item | Decisão |
|---|---|
| Caminho padrão | `src/dados/contas.json`, ao lado de `src/uploads/` |
| Configuração | `ANALISADOR_CONTAS` sobrescreve o caminho |
| Versionamento | `.gitignore` ganha `dados/`, o mesmo padrão de `uploads/` (casa em qualquer profundidade) |
| Contêiner | Volume `./src/dados:/app/src/dados`; sem ele, recriar o contêiner apaga as contas |
| Permissão | `chmod 0600` depois da escrita quando o sistema operacional permitir; no Windows, a limitação é declarada e o arquivo herda a ACL da pasta |
| Backup | Cópia do arquivo; não há exportação nem importação nesta entrega |
| Retenção e exclusão | Fora do escopo desta entrega; entram no portão de abertura (requirements §10) |
| Auditoria do arquivo | Nenhum acesso ao arquivo é auditado; a auditoria registra as **ações** de conta, não o acesso ao armazenamento |

## 10. Riscos do modelo

| Risco | Mitigação |
|---|---|
| Corrupção por escrita concorrente ou queda no meio | Trava em processo, escrita em temporário mais `os.replace`, teste de duas criações simultâneas |
| Documento inteiro reescrito a cada mudança | Escrita rara por desenho (login Google grava uma vez; reset grava uma vez); medir o tamanho com 1, 10 e 100 contas |
| Perda do arquivo em recriação do contêiner | Volume no compose e aviso no onboarding; backup por cópia |
| Vazamento do arquivo entrega credenciais | Derivação lenta com sal (a senha não é recuperável de imediato) e tokens guardados como hash (não utilizáveis) |
| Duas instâncias escrevendo o mesmo arquivo | A instância é única por construção (`ADR-12`); o adaptador não promete coordenação entre processos, e isso está declarado |

# Data delta: login com Google e isolamento por dono

> Identificador: `051-login-google-e-isolamento`
> Data: `2026-10-26`
> Modelo de referência: `_reversa_sdd/erd-complete.md` e `_reversa_sdd/data-dictionary.md`
> Confidência: 🟢 CONFIRMADO, 🟡 INFERIDO, 🔴 LACUNA

## 1. Resumo

**Nenhuma tabela nova e nenhuma coluna nova.** O esquema de seis tabelas fica como está; o que muda
é o **conteúdo** de `dna_analysis.owner_id` e o **layout** da pasta de uploads. As estruturas novas
são de memória e de disco: a conta lida da sessão, o marcador `.dono-inicial` e o layout por dono.

| Onde | Mudança | Tipo |
|---|---|---|
| `dna_analysis.owner_id` | Continua `TEXT NOT NULL`; passa a receber o `sub` do provedor, e as linhas antigas com `'unico'` são adotadas uma vez | delta-de-dados (conteúdo) |
| `src/uploads/` | De layout plano para `<base>/<sub>/`, com `_aposentados` por dono | delta-de-dados (disco) |
| `<base>/.dono-inicial` | Arquivo novo de uma linha, marcador da adoção | estrutura-nova (disco) |
| Conta em memória | `sub`, `email`, `nome` — lida da sessão a cada requisição | estrutura-nova (memória) |
| Linha de auditoria | Ganha o campo `conta` (o `sub`); nunca o e-mail | delta-de-contrato |
| Cookie de sessão | Passa a existir, assinado, com a conta e o `state` transitório | estrutura-nova (cliente) |

## 2. Layout de disco

**Antes** (medido em 2026-10-26: 13 arquivos na raiz, 3 em `_aposentados/`):

```text
src/uploads/
├── <chave>__<nome>.ged
├── <chave>__<nome>.csv
└── _aposentados/
    └── <chave>__<nome>.ged
```

**Depois**:

```text
src/uploads/
├── .dono-inicial                  # uma linha: o sub da conta inicial
├── <sub>/
│   ├── <chave>__<nome>.ged
│   ├── <chave>__<nome>.csv
│   └── _aposentados/
│       └── <chave>__<nome>.ged
└── (originais da raiz, mantidos pela cópia e invisíveis para a aplicação)
```

A referência continua sendo `<chave>__<nome>`: ela é resolvida **dentro** da pasta do dono da sessão.
O formato do nome, a chave por conteúdo e a validação de forma não mudam.

## 3. Regra de escopo

1. Toda operação de armazenamento recebe `dono` (já recebia) e passa a resolver o caminho em
   `<base>/<dono>/`.
2. O `dono` é validado por forma (`^[A-Za-z0-9_-]{1,64}$`) **antes** de compor o caminho. A origem é a
   sessão assinada, mas a validação é defesa em profundidade: um valor estranho nunca vira caminho.
3. `listar`, `resolver`, `aposentar` e `guardar` usam o mesmo diretório do dono. `aposentar` move para
   `<base>/<dono>/_aposentados/`, e a conferência de `dirname` passa a ser contra essa pasta.
4. A chave de conteúdo continua valendo **dentro** do dono: reenviar o mesmo conteúdo pelo mesmo dono
   reencontra o arquivo; o mesmo conteúdo por outro dono nasce como arquivo próprio.

## 4. Migração

### 4.1 Gatilho

O retorno do provedor, quando o e-mail verificado é igual a `ANALISADOR_DONO_INICIAL` (comparação sem
diferença de caixa) **e** o marcador `.dono-inicial` ainda não existe.

### 4.2 Passos

1. Criar `<base>/<sub>/` e `<base>/<sub>/_aposentados/` se não existirem.
2. Para cada **arquivo** da raiz de `<base>` cujo nome não comece por `.`: copiar para
   `<base>/<sub>/` se o destino não existir; se existir, pular e registrar no log.
3. O mesmo para os arquivos de `<base>/_aposentados/`, com destino em `<base>/<sub>/_aposentados/`.
4. Se `DATABASE_URL` estiver presente, chamar `RegistroDeAnalises.adotar("unico", sub)`; o adaptador
   executa `UPDATE dna_analysis SET owner_id = %s WHERE owner_id = %s` e devolve a contagem. Falha do
   banco **não** impede o login: vira aviso no log, e o marcador não é gravado, para a próxima
   entrada tentar de novo.
5. Gravar `.dono-inicial` com o `sub`, de forma atômica (arquivo temporário mais renomeação).
6. Registrar no log quantos arquivos foram copiados, quantos pulados e quantas linhas adotadas.

### 4.3 Idempotência

- A cópia só acontece para destino inexistente; repetir não duplica nem sobrescreve.
- O marcador é a condição de parada: com ele presente, a rotina não roda.
- A adoção no banco é um `UPDATE` condicionado a `owner_id = 'unico'`; repetir devolve `0`.

### 4.4 O que nunca acontece

- **Nada é apagado, movido ou renomeado** na raiz. A aplicação simplesmente deixa de enxergar a raiz:
  `listar` lê a pasta do dono.
- Nenhuma linha de `analysis_person`, `match_result`, `match_path_node`, `match_kit` ou
  `skipped_match` é tocada — a adoção muda só a coluna `owner_id` de `dna_analysis`, e as filhas
  seguem por FK para o `analysis_id`.

## 5. Estruturas novas

| Estrutura | Onde vive | Campos | Observação |
|---|---|---|---|
| `Conta` | memória, por requisição | `sub`, `email`, `nome` | `sub` é o dono; `email` e `nome` são rótulo de tela e não vão para a trilha |
| Conteúdo do cookie de sessão | cliente, assinado | `conta` e `oauth_state` (transitório) | Não carrega token de acesso nem código |
| `.dono-inicial` | disco | uma linha com o `sub` | Marcador de ida única; não é lido pela listagem de arquivos |

## 6. Delta para a extração (etapa `sync`)

| Artefato | Seção | Delta |
|---|---|---|
| `_reversa_sdd/data-dictionary.md` | `dna_analysis.owner_id` | A descrição "marcador único de processo, não filtra" deixa de valer: passa a ser o `sub` do provedor e o escopo de toda leitura e escrita |
| `_reversa_sdd/erd-complete.md` | Diagrama E | Sem tabela nova; `owner_id` continua `TEXT` e sem FK — a lacuna `E-06` **permanece aberta** e é declarada |
| `_reversa_sdd/architecture.md` | §4 (onde o dado vive) | Entram a pasta por dono, o marcador e a sessão; a pasta raiz deixa de ser lida |
| `_reversa_sdd/domain.md` | §3.5 | A chave por conteúdo passa a valer dentro do dono; dois donos com o mesmo conteúdo são dois arquivos |
| `_reversa_sdd/permissions.md` | §1.1, §3, §4.3, §6 | Matriz deixa de ser degenerada; `P-01` fecha; `P-08` (artes públicas) continua |

## 7. O que não muda

- As seis tabelas do `init.sql` e as constraints de domínio (`ck_comparison_status`, `ck_documentary_status`, `ck_path_role`, `ck_kit_status`).
- O snapshot de pessoas da análise (`analysis_person`) e o que ele persiste — inclusive a lacuna `P-07`, que é da Onda 5.
- A referência armazenada (`<16 hex>__<nome visível>`) e a validação por forma de nome.
- O cache da árvore: a chave é o caminho absoluto, e o caminho passa a distinguir donos.

## 8. Dados de teste

Toda conta usada em teste é sintética e usa o domínio reservado `.test` (RFC 2606), por exemplo
`a@example.test` com `sub` `"1001"` e `b@example.test` com `sub` `"1002"`. Nenhum e-mail real, nenhum
`sub` real e nenhuma árvore real entram em fixture, golden ou documentação (Princípio I).

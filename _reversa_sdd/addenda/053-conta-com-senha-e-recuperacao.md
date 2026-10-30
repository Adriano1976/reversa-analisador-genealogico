# Adendo: o sistema passou a ter identidade própria, com e-mail confirmado

> Identificador: `053-conta-com-senha-e-recuperacao`
> Data: `2026-10-30`
> Cenário: **legado** (âncora em `_reversa_sdd/architecture.md`, `_reversa_sdd/domain.md`,
> `_reversa_sdd/permissions.md` e `_reversa_sdd/state-machines.md`, lidos com os adendos 049, 051 e 052)

## Vigência

Vigente desde 2026-10-30.

## Resumo da entrega

A única porta de entrada era a conta Google (051): sem ela não se entrava, e quem perdia a conta perdia
também o próprio histórico. A 053 entrega **cadastro e entrada com e-mail e senha**, com **e-mail
confirmado antes do primeiro acesso**, mantendo o Google como caminho alternativo, e acrescenta
**recuperação de senha por e-mail** com link de uso único. A conta Google que já existia pode receber a
primeira senha **sem virar outra conta**: o `sub`, a pasta de uploads e o histórico continuam os mesmos
(`RF-24`, `RN-20`). O cadastro deslogado com e-mail já existente **não cria nem altera** conta — o caminho
seria pré-sequestro. As contas vivem em `src/dados/contas.json`, atrás de uma porta, com escrita atômica e
trava; a senha é derivada com `scrypt` e sal, nunca gravada; os tokens são guardados como hash. A sessão
ganhou **versão de credencial**, e redefinir a senha derruba as sessões anteriores. A tela de entrada segue
o layout das referências visuais, no verde do app, com o banner na posição atual e o ícone da aba reusando
a rota pública da 009.

**45 de 45 ações concluídas.** Suíte: **1.908 passam / 9 pulados / 5 falham**, e as cinco falhas são
exatamente as pré-existentes da linha de base (`test_characterization_mermaid` e o literal
`1. Lista de Matches (CSV)` de `test_tres_fases_da_tela.py`). São **107 testes novos**. Paridade: **30
divergências**, o mesmo número de 049/050/051 — nenhuma nova.

## Impacto por artefato da extração

| Artefato | Seção | Tipo de impacto | Delta |
|---|---|---|---|
| `_reversa_sdd/architecture.md` | §1 (visão geral / borda) | `contrato-alterado` | A borda ganha seis rotas de identidade e o `POST /login` com credencial; `create_app` monta repositório de contas, transporte de e-mail e relógio |
| `_reversa_sdd/architecture.md` | §2 (containers e concorrência) | `delta-de-contrato-externo` | O SMTP entra como segunda saída de rede; o processo continua sem estado de domínio, agora com um arquivo de contas em disco além dos uploads |
| `_reversa_sdd/architecture.md` | §3 (componentes e pacotes) | `componente-novo` | Entram `core/conta.py`, `core/token_de_uso_unico.py`, `ports/contas_em_arquivo.py`, `ports/email_smtp.py`, sete módulos de `application/`, `web/rotas_conta.py`, `web/origem.py` e `web/textos_de_conta.py`; o grafo de pacotes continua descendente |
| `_reversa_sdd/architecture.md` | §4 (onde o dado vive) | `delta-de-dados` | Nasce `src/dados/contas.json`, fora de `src/uploads/`, coberto pelo `.gitignore` e com volume no compose; o esquema Postgres não muda |
| `_reversa_sdd/architecture.md` | §6 (integrações externas) | `delta-de-contrato-externo` | O SMTP é a segunda integração de rede, depois do Google; sem ele, cadastro e recuperação avisam e a subida registra o aviso |
| `_reversa_sdd/architecture.md` | §7 (dívidas) | `presença` | Nenhuma dívida fecha; a #3 (corrida sobre o disco) não é afetada por esta entrega, e a operação ganha a dependência de manter o volume do arquivo de contas |
| `_reversa_sdd/architecture.md` | §8 (decisões) | `regra-nova` | A decisão desta entrega — identidade local com `scrypt`, arquivo JSON atrás de porta e versão de credencial — vira ADR na próxima re-extração |
| `_reversa_sdd/permissions.md` | §3 (matriz de permissões) | `regra-alterada` | A matriz passa a ter **duas** formas de entrada; as cinco rotas de identidade de quem ainda não tem sessão são públicas, e `POST /definir-senha` exige sessão |
| `_reversa_sdd/permissions.md` | §4.3 (cobertura) | `regra-alterada` | Autenticação passa a cobrir também a credencial local; autorização/propriedade continua coberta pela 051, e a confidencialidade de `all_names` segue aberta |
| `_reversa_sdd/permissions.md` | §5 (consequências) | `presença` | O sistema passa a guardar credencial e e-mail de terceiros; e-mail não entra em log nem em auditoria, e a senha só existe como derivação |
| `_reversa_sdd/domain.md` | §3.6 (tela de entrada) | `regra-alterada` | O cartão de entrada ganha dois caminhos — Google e e-mail/senha —, com cadastro, recuperação e confirmação; a tela principal (`GET /`) não muda |
| `_reversa_sdd/domain.md` | §5 (contrato de mensagens) | `regra-nova` | Entram os literais da `RN-13`; os 36 anteriores (29 da extração + 7 da 051) permanecem intactos |
| `_reversa_sdd/domain.md` | §6.3 (decisões humanas) | `presença` | Nova decisão verificada: identidade local obrigatória para compartilhar a instância, com unificação por e-mail verificado e caminho autenticado para a primeira senha |
| `_reversa_sdd/domain.md` | §7 (lacunas) | `presença` | Nenhuma lacuna fecha; a `L-29` (retenção de dado pessoal) ganha peso quando a instância passa a ter contas de terceiros |
| `_reversa_sdd/state-machines.md` | §11 (estados deliberadamente não gerados) | `regra-alterada` | O ciclo da conta local passa a existir: **não confirmada → confirmada → com senha**, e a sessão ganha a transição de revogação por versão de credencial |
| `_reversa_sdd/erd-complete.md` | E-06 (`owner_id` sem FK) | `presença` | Nada muda no esquema físico; o arquivo de contas é deliberadamente **fora** do banco |
| `_reversa_sdd/data-dictionary.md` | `dna_analysis.owner_id` | `presença` | O `sub` agora também pode ser local (`local-<32 hex>`); a coluna continua `TEXT`, sem FK e sem índice de escopo |
| `_reversa_sdd/inventory.md` | §4 (rotas e variáveis) | `delta-de-contrato-externo` | Entram seis rotas, as variáveis `ANALISADOR_SMTP_*` e `ANALISADOR_CONTAS`, e o volume do arquivo de contas |
| `_reversa_sdd/inventory.md` | §5 (banco e armazenamento) | `delta-de-dados` | Terceiro regime de persistência: arquivo local de contas, ao lado dos uploads e do Postgres opcional |
| `_reversa_sdd/c4-context.md` | persona e sistemas externos | `regra-alterada` | O servidor SMTP entra no contexto; a persona deixa de depender só do provedor de identidade |
| `_reversa_sdd/addenda/051-login-google-e-isolamento.md` | entrada, sessão e escopo | `presença` | A 051 continua vigente; a 053 acrescenta o segundo caminho de entrada e a versão de credencial na sessão |
| `_reversa_sdd/addenda/049-sistema-de-log.md` | auditoria | `regra-alterada` | O conjunto fechado de ações ganha `cadastrar`, `confirmar`, `definir_senha`, `pedir_senha` e `redefinir_senha` |

**Contagem por tipo:** `regra-alterada` 6 · `presença` 7 · `delta-de-contrato-externo` 3 · `delta-de-dados` 2 · `regra-nova` 2 · `componente-novo` 1 · `contrato-alterado` 1 — **22 impactos**.

## Regras sob vigilância

`W001` a `W008` — em `_reversa_forward/053-conta-com-senha-e-recuperacao/regression-watch.md`.

## Fontes

- `_reversa_forward/053-conta-com-senha-e-recuperacao/requirements.md`
- `_reversa_forward/053-conta-com-senha-e-recuperacao/roadmap.md`
- `_reversa_forward/053-conta-com-senha-e-recuperacao/legacy-impact.md`
- `_reversa_forward/053-conta-com-senha-e-recuperacao/regression-watch.md`
- `_reversa_forward/053-conta-com-senha-e-recuperacao/progress.jsonl` (45 eventos)
- `_reversa_forward/053-conta-com-senha-e-recuperacao/actions.md` (45 de 45 ações)
- `_reversa_forward/053-conta-com-senha-e-recuperacao/data-delta.md`
- `_reversa_forward/053-conta-com-senha-e-recuperacao/interfaces/entrada-e-senha.md`
- `_reversa_forward/053-conta-com-senha-e-recuperacao/onboarding.md`

## Atualização 2026-10-30

**O ícone da aba ganhou arte própria, transparente.** O resumo acima diz que o ícone "reusa a rota pública
da 009"; a partir desta atualização, `/favicon.png` serve uma derivada **transparente** da mesma arte
canônica (128×128, com canal alfa), e o `apple-touch-icon` opaco continua sendo o do atalho do celular. O
motivo é o alvo: a tela inicial do aparelho compõe transparência sobre preto e precisa de fundo branco; a
aba do navegador mostra o fundo, e o quadrado branco do ícone opaco aparecia como moldura. A tela principal
mantém o ícone embutido (`data:image`), que já era transparente.

A receita única está em `tests/favicon_da_aba.py`, com âncora de tamanho e teste de deriva que compara
**pixel e canal alfa** (`tests/test_deriva_da_arte.py`). A rota é pública, como as demais artes (`P-08`), e
entra em `PUBLICOS` na guarda da 051. Vale para as telas de identidade — login, cadastro, confirmação,
recuperação e definição de senha —, que são as que declaram o `rel="icon"` no documento.

A `RN-16` do `requirements.md` foi revista para descrever as duas artes, e a emenda `E005` registra a
mudança no `actions.md`.

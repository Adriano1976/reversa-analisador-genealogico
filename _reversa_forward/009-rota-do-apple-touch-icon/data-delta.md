# Data Delta: Rota do ícone de atalho para tela inicial

> Identificador: `009-rota-do-apple-touch-icon`
> Data: `2026-10-08`
> Modelo extraído: `_reversa_sdd/erd-complete.md`
> Confidência: 🟢 CONFIRMADO, 🟡 INFERIDO, 🔴 LACUNA

## Veredito

**Sem delta de dados.**

Nenhuma estrutura do modelo extraído é criada, alterada ou removida. Nenhum campo, nenhum
índice, nenhuma restrição, nenhuma migração. Esta feature não lê nem escreve dado de
genealogia: ela devolve um arquivo de imagem que é marca do projeto.

| Operação | Quantidade |
|---|---|
| Estruturas criadas | **0** |
| Estruturas alteradas | **0** |
| Estruturas removidas | **0** |
| Campos criados | **0** |
| Campos removidos | **0** |
| Índices ou restrições | **0** |
| Migrações necessárias | **0** |

## O que muda em disco — e por que não é dado

Um único arquivo novo, **binário de arte**, sob `src/assets/`:

| Arquivo | Natureza | Entra no versionamento | Entra na imagem |
|---|---|---|---|
| A arte de atalho, 180×180, opaca | Marca do projeto (PNG derivado) | sim | sim |

Ele **não** é dado no sentido do modelo extraído, e a distinção importa:

- **Não é dado pessoal.** O `.reversa/principles.md#I` proíbe versionar dado real de DNA ou
  GEDCOM — árvores, cromossomos, nomes, e-mails e identificadores de kit. Um logo não é nada
  disso: é a mesma classe de arquivo que `docs/assets/img/logo.png`, já versionado.
- **Não é dado de runtime.** A pasta de dados do sistema continua sendo `src/uploads/`, e ela
  **não** é tocada. O `.dockerignore` continua reexcluindo `src/uploads/` da imagem, e é isso
  que impede o GEDCOM real do operador de viajar para o daemon do Docker.
- **Não é entidade.** Não tem chave, ciclo de vida, dono nem relação com nenhuma das 27
  estruturas de `erd-complete.md`.

## Relação com o modelo extraído

| Estrutura de `_reversa_sdd/erd-complete.md` | Relação com esta feature |
|---|---|
| Todas as 27 | **nenhuma** — a feature não as consulta, não as altera e não depende delas |

## Migração

**n/a.** Não há ETL, não há conversão, não há janela de congelamento. Nenhum arquivo existente
em `src/uploads/` é renomeado ou movido — mesma propriedade que a feature 007 preservou com a
`RN-02` dela, e que a 008 preservou com o *bind mount* do volume.

O que existe, e não é migração de dados, é uma consequência de cache no cliente: quem já salvou
o atalho na tela inicial antes desta feature continua vendo o ícone antigo até o sistema
refazer a busca, que ele faz no ritmo dele e ignorando cabeçalhos. O procedimento está no
`onboarding.md`.

## Verificação de conformidade com o Princípio I

| Pergunta | Resposta |
|---|---|
| A feature versiona dado real de terceiros? | **Não** |
| A feature embute nome, e-mail ou identificador de kit? | **Não** |
| A feature toca `src/uploads/`? | **Não** |
| A feature acrescenta algo a `src/uploads/` à imagem? | **Não** — a reexclusão do `.dockerignore` continua valendo |
| A arte é a mesma já publicada em `docs/`? | **Sim**, derivada dela, e a deriva é detectada por teste (`RF-10`) |

## Fontes

- `_reversa_sdd/erd-complete.md` (as 27 estruturas, para afirmar que nenhuma muda)
- `_reversa_sdd/architecture.md#4` (modelo de dados)
- `.reversa/principles.md#I` (dado real nunca versionado)
- `.dockerignore` na raiz (a reexclusão de `src/uploads/`)
- `_reversa_forward/009-rota-do-apple-touch-icon/requirements.md` (`RF-04`, `RF-10`)

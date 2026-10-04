# Delta de dados: servir a aplicação por um servidor de produção no Windows

> Identificador: `004-servidor-waitress`
> Data: `2026-10-03`
> Requirements: `_reversa_forward/004-servidor-waitress/requirements.md`

## 1. Resumo

**Nenhuma mudança de dado.** Esta feature altera o modo de execução da aplicação, e não o que ela guarda, lê ou devolve. Não há campo novo, campo removido, entidade alterada, índice, migração ou dado a transformar.

## 2. Modelo extraído em `_reversa_sdd/`

Para deixar a ausência de impacto explícita, e não apenas afirmada:

| Elemento do modelo | Arquivo de origem no legado | Efeito desta feature |
|---|---|---|
| Registro de pessoa (GEDCOM `INDI`) | `_reversa_sdd/architecture.md#3.1` | nenhum |
| Agregado de correspondência de DNA (`DNA_MATCH`) | `_reversa_sdd/architecture.md#3.1` | nenhum |
| Estruturas de runtime da árvore | `_reversa_sdd/architecture.md#3.3` | nenhum |
| Entidades removidas em 2026-09-30 | `_reversa_sdd/architecture.md#3.2` | continuam removidas, e a feature não as reintroduz |
| Contrato de mensagens ao usuário | `_reversa_sdd/domain.md#4.1` e `#4.2` | nenhum: as mensagens permanecem literais |

## 3. Campos novos

Nenhum.

## 4. Campos removidos

Nenhum.

## 5. Migrações necessárias

Nenhuma. Não há dado persistido a migrar: o sistema não tem banco nem persistência de resultados, e o armazenamento de uploads continua em `src/uploads/`, resolvido pela mesma função ancorada no arquivo do aplicativo.

## 6. O que muda, e não é dado

O que esta feature acrescenta é **configuração de execução**, não estado persistido:

| Item | Natureza | Onde vive |
|---|---|---|
| Endereço de escuta | configuração de processo, lida a cada inicialização | variável de ambiente, com padrão declarado no código |
| Porta | idem | idem |
| Concorrência | idem | idem |

Nada disso é gravado, versionado ou lido de arquivo. Reiniciar o processo relê os valores, e não há histórico a preservar.

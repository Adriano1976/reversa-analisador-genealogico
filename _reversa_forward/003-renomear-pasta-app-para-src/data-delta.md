# Data Delta: renomear a raiz da aplicação de `analisador-genealogico/` para `src/`

> Identificador: `003-renomear-pasta-app-para-src`
> Data: `2026-10-02`
> Modelo de referência: `_reversa_sdd/architecture.md#3` (ERD) e `_reversa_sdd/architecture.md#3.3` (estruturas de runtime)
> Confidência: 🟢 CONFIRMADO, 🟡 INFERIDO, 🔴 LACUNA

## 1. Veredito

**Não há delta de modelo de dados.** Nenhuma entidade, campo, índice, chave ou relação é criada, alterada ou removida. Nenhuma migração de dados é necessária. Esta feature é uma mudança de **localização física**, e o delta que ela produz é de arranjo de arquivos, não de dados.

## 2. Entidades do modelo extraído

| Entidade | Situação | Onde |
|----------|----------|------|
| Registro de pessoa (`INDI` do GEDCOM) | inalterada | `_reversa_sdd/architecture.md#3.1` |
| Registro de família (`FAM` do GEDCOM) | inalterada | `_reversa_sdd/architecture.md#3.1` |
| Agregado de correspondência de DNA (`DNA_MATCH`) | inalterada | `_reversa_sdd/architecture.md#3.1` |
| Estruturas de runtime (`people`, `families`, `graph`, `child_to_family`, `ged_index`, `surname_index`, `features`) | inalteradas | `_reversa_sdd/architecture.md#3.3` |
| Diretório de upload (sistema de arquivos) | **localização alterada; contrato de chave inalterado** | `_reversa_sdd/architecture.md#3.3` |

## 3. A única estrutura afetada, em detalhe

O diretório de upload é a única estrutura de dados do sistema extraído que muda. O que muda e o que não muda:

| Aspecto | Antes | Depois | Muda? |
|---|---|---|---|
| Localização | `<raiz do código>/uploads/` | `<nova raiz>/uploads/` | **sim** |
| Papel do diretório | pasta de trabalho do processo | idem | não |
| Formato do nome de arquivo armazenado | chave derivada do conteúdo em hexadecimal, mais o nome visível saneado | idem | não |
| Contrato do campo oculto do formulário | o valor devolvido é reencontrado na requisição seguinte | idem | não |
| Ordem validar-antes-de-gravar | arquivo recusado não fica em disco | idem | não |
| Versionamento | ignorado pelo versionador em qualquer profundidade | idem | não |

Fonte do contrato preservado: `_reversa_sdd/addenda/bug-BUG-20260929-QMLY-v001.md#2` e `#5`, adendo vigente.

**Consequência prática:** os arquivos que já estão na pasta continuam válidos e continuam sendo encontrados pela mesma chave, porque a chave é derivada do conteúdo. Nenhum arquivo é renomeado, convertido ou reinterpretado. Nenhuma migração roda.

## 4. Delta de arranjo de arquivos

| Item | Tipo de delta | Detalhe |
|---|---|---|
| Raiz do código e todo o seu conteúdo versionado | movido | Passa a se chamar `src/`; os 12 arquivos do pacote do núcleo, o arquivo de entrada e os templates vão junto |
| Diretório de upload | movido à parte | 9 arquivos, 16.920.784 bytes; é ignorado pelo versionador, então a renomeação do versionador não o alcança |
| Arquivo de dependências | movido | Sobe para a raiz do repositório |
| `README.md` herdado do módulo | removido | Documentação original do projeto legado, em inglês |
| `.gitignore.txt` do módulo | removido | A única regra exclusiva apontava para um artefato que o projeto deixou de gerar |
| `static/` | removido | Diretório vazio |
| Cache de bytecode | descartado | Regenerável; não é artefato |
| Diretório de dados legado da raiz | inalterado | Decisão explícita do usuário: permanece onde está |

## 5. Migrações necessárias

**Nenhuma.** Não há esquema, tabela, índice ou chave a migrar. Não há dado a converter. O único cuidado operacional é a movimentação física dos 9 arquivos de dados reais da pasta de upload, que é uma operação de sistema de arquivos, não uma migração de modelo.

## 6. Verificação

1. Contagem de arquivos e soma de bytes do diretório de upload **antes** e **depois** da movimentação: `9` arquivos e `16.920.784` bytes.
2. O estado do versionamento não lista nenhum arquivo de dado real, em nenhuma profundidade (princípio I).
3. A suíte de testes, que exercita o ciclo de gravar e reencontrar o arquivo armazenado, permanece verde (RF-06, RF-08).
4. O comparador de paridade permanece em 100%, o que prova que nenhuma saída observável mudou (RF-07).

# Data Delta: Uploads fora do repositório

> Identificador: `010-uploads-fora-do-repositorio`
> Data: `2026-10-09`
> Modelo extraído: `_reversa_sdd/erd-complete.md`, `_reversa_sdd/data-dictionary.md`
> Confidência: 🟢 CONFIRMADO, 🟡 INFERIDO, 🔴 LACUNA

## Veredito

**Nenhuma mudança de schema.** O que muda é a **localização** de um dado que já existe em disco — os
arquivos enviados — e a mudança é uma **cópia com o mesmo nome**. Essa última palavra é o que sustenta
o resto: como o nome armazenado deriva do conteúdo
(`_reversa_sdd/upload-gedcom/contracts.md#2.1`), copiar sem renomear preserva o lastro do histórico do
banco, e nenhuma migração de dados é necessária — nem SQL, nem reescrita de referência.

| Pergunta | Resposta |
|----------|----------|
| Tabela nova? | **Não** |
| Campo novo ou removido? | **Não** |
| Migração de schema? | **Não** |
| Conversão de dados? | **Não** |
| Cópia de dados em disco? | **Sim** — 36 arquivos, 27.932.474 bytes, com o mesmo nome |
| Remoção de dados? | **Não por esta feature.** A origem só sai por decisão manual do operador, depois de conferida |

## O que muda em disco

| Propriedade | Antes | Depois |
|-------------|-------|--------|
| Raiz da pasta | `<raiz do repositório>/src/uploads` (padrão do código) | pasta canônica do host, **fora** do repositório, declarada uma vez (D-01) |
| Nome armazenado | `<16 hexadecimais>__<nome visível>` | **idêntico** — nenhum arquivo é renomeado (`RN-02`) |
| Chave | `sha256(conteúdo)` truncado em 16 hexadecimais | **idêntico** |
| Quantidade | 36 arquivos, 27.932.474 bytes | 36 arquivos, 27.932.474 bytes no destino, e os mesmos 36 na origem |
| Idempotência | mesmo envio não reescreve | preservada na aplicação e estendida à migração: arquivo já presente com o mesmo hash é ignorado |
| Remoção | nunca pelo sistema | **nunca pelo sistema**; o expurgo é ferramenta separada, por manifesto e com simulação |

## Relação com o modelo extraído

- **`ARQUIVO_ARMAZENADO`** (`_reversa_sdd/erd-complete.md`): a entidade continua sendo o arquivo em
  disco, endereçado pela chave de conteúdo. O que muda é a **coluna de localização** descrita no ERD,
  que passa a apontar para a raiz canônica em vez de `src/uploads/`. A forma do nome não muda, então a
  entidade não muda de identidade.
- **`dna_analysis.tree_ref` e `dna_analysis.match_file_ref`**: continuam válidos **sem qualquer
  atualização**, porque guardam o nome derivado de conteúdo e não o caminho
  (`src/application/dna_analysis.py:234-235`; a projeção usa `os.path.basename` no
  `match_file_ref`, `:276`). É esta propriedade que torna a migração de baixo risco.
- **`_reversa_sdd/data-dictionary.md`**: a linha do caminho padrão da pasta e a tabela de variáveis de
  ambiente passam a registrar o destino canônico como modo de operação declarado. A variável em si já
  está documentada na extração; o que não existia era o uso dela como procedimento.
- **Nenhuma entidade nova, nenhuma removida.** A ferramenta de manutenção não cria estrutura de dados:
  ela lê a pasta, escreve um manifesto e relata.

## Migração

1. **Inventário de origem** — nome e `sha256` de cada arquivo, mais o total de bytes, gravados como
   evidência antes de qualquer escrita.
2. **Criação do destino** — a pasta canônica é criada se não existir.
3. **Cópia com conferência** — para cada arquivo: copiar, reler o destino, comparar o `sha256` com o da
   origem. Divergência **não** sobrescreve o destino nem remove a origem: entra no relatório final.
4. **Idempotência** — repetir o comando não regrava o que já confere e não duplica nada.
5. **Conferência final** — 36 nomes no destino, todos os hashes iguais, origem intacta com os mesmos
   hashes.
6. **Nada é removido.** A remoção de `src/uploads/` é passo manual do operador, posterior à conferência
   e à prova de continuidade (`onboarding.md` §11).

**Ordem obrigatória:** a migração acontece **antes** de apontar a aplicação para o destino. Apontar
primeiro, com a cópia incompleta, faria a pasta nova responder "arquivo não existe mais" para
referências que a pasta antiga ainda resolvia.

## Verificação de conformidade com o Princípio I

O princípio I (`.reversa/principles.md`) proíbe que dado real entre no versionamento, em qualquer
caminho. Esta feature o atende em quatro frentes, e uma delas é uma tensão declarada:

| Frente | Situação |
|--------|----------|
| Destino fora do repositório | O destino canônico está fora da árvore do repositório, portanto fora do alcance do versionador 🟢 |
| Origem | `src/uploads/` continua coberta pela regra de ignore (`uploads/`, que casa em qualquer profundidade) durante todo o período de transição 🟢 |
| Testes da ferramenta | Usam arquivos **sintéticos** criados em pasta temporária; nenhum teste lê arquivo real do operador 🟢 |
| Densidade de dado real | A pasta contém 27,9 MB de dado real, dos quais três arquivos byte a byte idênticos. A feature **não** os remove nem os deduplica (D-06): o que ela entrega é a condição para que o operador os remova com segurança 🟡 |
| Tensão declarada | Sob a resposta 1a, o **padrão do código** continua sendo `<diretório do app>/uploads`, dentro do repositório. O princípio não é violado (o caminho é ignorado pelo versionador), mas a proteção passa a depender do procedimento documentado — e é isso que o RNF de Documentação, agora `Must`, registra 🟡 |

## Fontes

- `_reversa_sdd/upload-gedcom/contracts.md#2.1` e `#2.2` — forma do nome e contrato da pasta
- `_reversa_sdd/erd-complete.md` — `ARQUIVO_ARMAZENADO` e a coluna de localização
- `_reversa_sdd/data-dictionary.md` — caminho padrão e tabela de variáveis
- `src/application/dna_analysis.py:234-235,276` — o que o histórico guarda
- `src/ports/adaptadores.py:52-79` — a escrita idempotente
- Medição de 2026-10-09: 36 arquivos, 27.932.474 bytes, 18 de resíduo de instrumento, três hashes iguais
  e um quarto distinto

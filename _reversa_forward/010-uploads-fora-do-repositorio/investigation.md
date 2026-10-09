# Investigation: Uploads fora do repositório

> Identificador: `010-uploads-fora-do-repositorio`
> Data: `2026-10-09`
> Requirements: `_reversa_forward/010-uploads-fora-do-repositorio/requirements.md`

## 1. A pergunta de fundo

Por que a pasta de upload vive dentro do repositório, o que depende dela, e qual é a **menor** mudança
que tira o dado de lá sem quebrar essas dependências?

Três coisas dependem, e cada uma impõe um limite diferente:

1. **A continuidade entre requisições.** O formulário devolve o nome armazenado no campo oculto
   `gedcom_filename`, e o `POST` seguinte reparseia o arquivo a partir dele
   (`_reversa_sdd/upload-gedcom/contracts.md#3`). Se o arquivo não estiver no lugar esperado, a tela
   responde "Arquivo '...' não existe mais" (`src/app.py:188`).
2. **O histórico do banco.** `tree_ref` e `match_file_ref` guardam o **nome** armazenado
   (`src/application/dna_analysis.py:234-235`). O nome é derivado do conteúdo — logo, migrar sem
   renomear preserva o lastro do histórico; renomear destruiria.
3. **Os instrumentos de verificação.** O harness de paridade e os coletores leem GEDCOMs **reais** da
   pasta como fixtures (`_reversa_sdd/parity/_profile_collector_costs.py:47`,
   `_reversa_sdd/oracle/run_oracle.py:115-127`). Tirar o dado de lá sem redirecionar os instrumentos
   cega a paridade.

Uma segunda pergunta foi respondida antes de qualquer desenho: **"temporária" é a resposta certa?**
A investigação abaixo mostra que não — e por quê.

## 2. O que o sistema faz hoje — medido

| Fato | Como foi medido |
|------|-----------------|
| A pasta é resolvida no **import**, com o padrão `<diretório do app>/uploads` e sobreposição por `ANALISADOR_UPLOAD_FOLDER` | leitura de `src/app.py:103-118`; `os.makedirs` na linha 123; caminho congelado no adaptador na linha 129 |
| A escrita é idempotente: mesma chave **não** é reescrita | leitura de `src/ports/adaptadores.py:73-79` |
| A leitura valida a **forma** do nome antes de qualquer acesso ao disco | leitura de `src/ports/adaptadores.py:93-96` e `src/utils/validate.py:78-79` |
| **Nada apaga arquivo enviado**: zero ocorrências de `unlink`, `os.remove`, `shutil.rmtree` e `tempfile` em `src/` | varredura em `src/` |
| Quem escreve na pasta real sem ser a aplicação em uso: o **coletor candidato** do harness de paridade | leitura de `_reversa_sdd/parity/harness.py`: o bloco `CANDIDATE_COLLECTOR` faz `os.chdir` (linha 259) e sobe `probe.ged` pela aplicação (linha 401); nenhum script de paridade define `ANALISADOR_UPLOAD_FOLDER` (varredura) |
| O `chdir` **não** redireciona a pasta | a pasta é ancorada em `__file__` desde a feature 006 (`_reversa_sdd/addenda/006-fronteira-aplicacao-ports.md`); o `chdir` isola o diretório corrente, não a pasta resolvida |
| O isolamento **é possível de fora**, sem editar o instrumento | o harness lança cada coletor com `env = dict(os.environ, …)` (`_reversa_sdd/parity/harness.py:465`), então a variável definida **antes** da chamada chega ao processo do coletor, que importa o app (`:356`) e tem a pasta resolvida no import |
| Estado da pasta real em 2026-10-09 | **36 arquivos, 27.932.474 bytes**; **18 arquivos (6.631 bytes)** com nomes de sonda e de fixture de instrumento; **três** arquivos idênticos por `sha256` (`080E7943572D2652…`, 5.332.198 bytes cada) e uma **quarta** cópia de mesmo tamanho e hash distinto (`C84FD7FB4201B69F…`) |

A consequência do penúltimo item é o achado que motiva parte da feature: o instrumento que existe para
**medir sem interferir** é, ele mesmo, a origem do resíduo — e o resíduo tem nomes de fixture porque
são as fixtures de DNA e as sondas de GEDCOM que a paridade envia pela aplicação.

## 3. Alternativas avaliadas

### 3.1 Pasta temporária por execução — **rejeitada**

Criar a pasta no arranque e removê-la na saída é a leitura literal de "temporária durante a execução".
Foi recusada por quatro motivos, todos verificáveis no repositório:

- inverte quatro contratos escritos: `_reversa_sdd/upload-gedcom/design.md#estado-interno`,
  `_reversa_sdd/state-machines.md#5`, `_reversa_sdd/user-stories/upload-gedcom.md` e
  `_reversa_sdd/upload-gedcom/contracts.md#2.2` ("o sistema **nunca** apaga um arquivo enviado");
- quebra o lastro do histórico: as referências do banco passariam a apontar para arquivos que a
  próxima execução não tem;
- reiniciar invalida a página aberta — hoje não invalida;
- e a limpeza só é tão boa quanto o caminho de encerramento: `SIGKILL` e o `SIGTERM` do encerramento de
  contêiner não executam o gancho de saída do interpretador, então a pasta ficaria para trás
  justamente nos encerramentos anormais.

### 3.2 `%TEMP%` como destino — **rejeitada**

É a escolha que parece óbvia e não é. O Windows trata arquivos temporários do usuário como
descartáveis: o Storage Sense vem **habilitado por padrão**, roda automaticamente **quando o espaço em
disco está baixo**, tem cadência configurável (diária, semanal ou mensal) e oferece uma opção
específica de limpeza de arquivos temporários do usuário
([Microsoft Learn, *Configure Storage Sense in Windows*, atualizado em 2025-07-14](https://learn.microsoft.com/en-us/windows/configuration/storage/storage-sense),
consultado em 2026-10-09).

🟡 **Inferência declarada:** a fonte não promete que um arquivo será removido entre duas requisições —
ela sustenta que a pasta de temporários **não é um lugar durável por definição**. O que pesa contra é o
custo do erro: a leitura do arquivo acontece só durante a requisição, então uma remoção automática
apareceria como falha intermitente e de diagnóstico difícil, no meio de uma sessão de análise.

### 3.3 Pasta dentro do contêiner, com volume nomeado — **rejeitada nesta rodada**

Dá durabilidade entre derrubar e subir e é o padrão que o próprio projeto já usa para o banco
(`docker-compose.yml:76-79`). Foi recusada pela resposta 3b porque o dado sai do alcance do sistema de
arquivos do host: o operador perde o acesso direto, o backup trivial e a inspeção pelo explorador — e
os 36 arquivos existentes precisariam ser copiados para dentro do volume, sem ganho correspondente.

### 3.4 Pasta do host fora do repositório, por configuração — **ESCOLHIDA**

É a menor mudança que atende ao objetivo, e o mecanismo **já existe e já é exercitado**: a suíte
redireciona a pasta por variável de ambiente (`tests/conftest.py:154`,
`tests/test_upload_seguranca.py:120`), e a verificação manual da feature 007 fez exatamente isso
(`_reversa_forward/007-dono-no-port-e-baseline/evidence/T015-verificacao-manual.md:26`). Não há
mecanismo novo a inventar: há um procedimento a documentar, um destino a escolher e uma montagem a
ajustar.

### 3.5 Mudar o padrão do código — **rejeitada nesta rodada**

Faria a pasta nascer fora do repositório sem configuração alguma, o que é mais conveniente. Recusada
por custo: altera um contrato vigente (`contracts.md#2.2`), exige adendo à extração, `regression-watch`
e teste novo — e destrói uma propriedade útil do padrão atual, que é ser o **recuo seguro** (o
diretório do app, que sempre existe e sempre é gravável pelo processo).

### 3.6 Expurgo por padrão de nome ou por janela de data — **rejeitada**

Um padrão de nome não distingue resíduo de dado real, e aqui a confusão é concreta: a pasta real
contém nomes de **fixture de instrumento** porque foram instrumentos que os enviaram — `probe.ged`,
`utf8.csv`, `cm_boundaries.csv`, `matches_dois_kits.csv`. Uma janela de data é pior: o critério
dependeria de registrar execuções de verificação, o que hoje não existe. Escolhido o **manifesto
explícito** (D-05), com a lista revisável antes de qualquer remoção.

### 3.7 Deduplicação automática das cópias idênticas — **rejeitada**

Há três arquivos byte a byte idênticos e um quarto de **mesmo tamanho com conteúdo distinto**. A
heurística barata (tamanho) erraria no quarto; a cara (hash) identificaria os três, mas ainda exigiria
decidir qual cópia permanece e o que fazer com os nomes derivados de conteúdo que o histórico
referencia. Relatar e devolver a decisão ao operador (D-06).

### 3.8 Editar o `harness.py` para ele se auto-isolar — **rejeitada**

Seria a correção mais direta: uma atribuição no coletor candidato. Recusada por dois motivos. Primeiro,
o instrumento é a **régua** da paridade, e uma régua editada enfraquece a medição que ela produz — este
repositório já tratou esse arquivo como "instrumento, não objeto da feature"
(`_reversa_forward/007-dono-no-port-e-baseline/legacy-impact.md:33`). Segundo, o precedente
`_reversa_refactor/analise-dna/opportunities/OPP-20261008-JXQN-legado-de-cm-fora-do-fluxo.md:158`
registra esse caminho como "**exige editar `_reversa_sdd/**`, que não está liberado**". Como o ambiente
já é herdado pelos coletores, o invólucro resolve o problema por fora e a edição é desnecessária.

## 4. Padrões aplicáveis

- **Endereçamento por conteúdo** (já existente no legado): a chave `sha256` truncada faz o mesmo envio
  reencontrar o mesmo arquivo — é exatamente o que permite migrar **sem renomear** e manter o
  histórico resolvível.
- **Cópia idempotente com verificação**: o destino é conferido por hash e a operação pode ser repetida
  sem efeito colateral, o que torna uma interrupção inofensiva.
- **Expurgo por manifesto com simulação**: o `--dry-run` como contrato de segurança, e o precedente
  interno de **melhor esforço com relatório** em `_reversa_sdd/parity/_clean_residue.py`, que reporta o
  que não conseguiu remover em vez de fingir sucesso.
- **Isolamento de instrumento por ambiente**: o oráculo já é isolado por `chdir` mais atribuição da
  constante que ele lê; o candidato passa a ser isolado pela variável que o código **realmente** lê,
  definida por um invólucro **antes** de o instrumento ser lançado — o instrumento, esse, não muda.

## 5. Fontes externas

- Microsoft Learn — *Configure Storage Sense in Windows* (atualizado em 2025-07-14; consultado em
  2026-10-09): <https://learn.microsoft.com/en-us/windows/configuration/storage/storage-sense>
- Docker Docs — *Bind mounts* (consultado em 2026-10-09):
  <https://docs.docker.com/engine/storage/bind-mounts/>
- Internas: `_reversa_sdd/parity/_clean_residue.py` (limpeza com relatório de melhor esforço);
  `_reversa_forward/007-dono-no-port-e-baseline/evidence/T015-verificacao-manual.md` (redirecionamento
  da pasta em verificação); `tests/conftest.py:154` (redirecionamento na suíte).

## 6. Lacunas declaradas

- 🔴 O requisito de **compartilhamento de volume** do Docker Desktop no Windows, para montar uma pasta
  fora do projeto, **não foi verificado** nesta rodada: a página de *bind mounts* não foi lida por
  inteiro. A verificação é uma ação do `onboarding.md` §7, e o recuo — volume nomeado — está declarado
  desde já.
- 🟡 A eficácia do Storage Sense sobre um arquivo que **não** está aberto no instante da limpeza é
  inferência a partir do comportamento documentado da funcionalidade, não citação literal. Ela reforça
  a recusa de `%TEMP%`; não é o único motivo dela.
- 🟡 O `harness.py` continua **capaz** de escrever na pasta real se for invocado direto, sem o
  invólucro — e isso é declarado, não corrigido: corrigir exigiria editar o instrumento (3.8). O
  caminho de execução documentado passa a ser o invólucro, e o sintoma de uma execução fora dele é
  imediato no inventário, porque os nomes de sonda reaparecem.

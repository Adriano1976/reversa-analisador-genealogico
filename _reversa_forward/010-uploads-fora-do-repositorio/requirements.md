# Requirements: Uploads fora do repositório

> Identificador: `010-uploads-fora-do-repositorio`
> Data: `2026-10-09`
> Pasta da extração reversa: `_reversa_sdd/`
> Confidência: 🟢 CONFIRMADO, 🟡 INFERIDO, 🔴 LACUNA / DÚVIDA

## 1. Resumo executivo

O sistema guarda todo arquivo enviado pelo operador — a árvore genealógica no formato GEDCOM
(GEnealogical Data COMmunication) e o relatório de DNA em CSV (valores separados por vírgula) — numa
pasta que hoje vive **dentro do repositório** (`src/uploads/`) e que
nunca é apagada. Esta feature tira essa pasta da árvore do repositório, no uso local e no contêiner,
sem tocar no leiaute dos nomes, e devolve ao operador uma ferramenta de expurgo que **mostra antes de
remover**. Ela corrige também o instrumento de verificação que hoje grava os arquivos de sondagem do
harness de paridade **na pasta real do operador** — a origem do resíduo medido. Nada é apagado por
esta feature: remover o resíduo existente é decisão do operador, com a lista na mão.

## 2. Contexto a partir do legado

| Fonte | Trecho relevante | Confidência |
|-------|------------------|-------------|
| `_reversa_sdd/upload-gedcom/contracts.md#2.2` | Contrato da pasta: padrão `<diretório do app>/uploads`, sobreposta por `ANALISADOR_UPLOAD_FOLDER`; criada no **import** pela **mesma** função que a resolve; arquivo com a mesma chave não é reescrito; "o sistema **nunca** apaga um arquivo enviado" | 🟢 |
| `_reversa_sdd/upload-gedcom/contracts.md#2.1` | Nome no disco na forma fechada `<16 hexadecimais>__<nome visível>`; a chave vem de `sha256(conteúdo)` (impressão digital do conteúdo), então o mesmo envio reencontra o mesmo arquivo | 🟢 |
| `_reversa_sdd/upload-gedcom/contracts.md#3` | A referência devolvida no formulário é o que sustenta a continuidade entre requisições | 🟢 |
| `_reversa_sdd/inventory.md#4` | Tabela de configurações: `ANALISADOR_UPLOAD_FOLDER` redireciona a pasta de upload e é usada pelos testes para não escreverem na pasta real | 🟢 |
| `_reversa_sdd/inventory.md#5` | O sistema de arquivos é o armazenamento; não existe banco para os arquivos enviados | 🟢 |
| `_reversa_sdd/architecture.md#1` | "Sistema de arquivos local (`src/uploads/`) — o único estado persistente, com arquivos imutáveis sob chave de conteúdo" | 🟢 |
| `_reversa_sdd/architecture.md#7` | Dívida 3 (contaminação entre requisições concorrentes; a guarda de instância única é de processo, não de thread) e dívida 8 (nada é persistido entre requisições) | 🟢 |
| `_reversa_sdd/state-machines.md#5` | "Ciclo de vida do arquivo enviado: o arquivo é imutável após a gravação e nunca é apagado pelo sistema. Não há estados." | 🟢 |
| `_reversa_sdd/user-stories/upload-gedcom.md#o-que-esta-história-não-cobre` | "Histórico de uploads: nada é registrado: o arquivo é gravado e nunca apagado pelo sistema" 🔴 (limitação declarada) | 🟢 |
| `_reversa_sdd/addenda/007-dono-no-port-e-baseline.md#o-que-a-extração-não-precisa-mudar` (vigente) | "O leiaute de armazenamento em disco. Nenhum arquivo em `uploads/` precisa ser renomeado ou movido, e nenhum é." | 🟢 |
| `_reversa_sdd/addenda/008-persistencia-postgres-docker.md#o-que-a-extração-não-precisa-mudar` (vigente) | O ponto de montagem da composição "preserva os 35 arquivos existentes através de `down` + `up`" — é essa propriedade que a mudança de raiz precisa manter | 🟢 |
| `_reversa_sdd/addenda/006-fronteira-aplicacao-ports.md` (vigente) | Precedente de verificação: a pasta de upload foi apontada para um diretório descartável e `src/uploads/` ficou com as mesmas entradas de antes | 🟢 |
| `README.md#arquitetura-do-projeto` | "Esse diretório é armazenamento local persistente; não é um diretório temporário de processamento" | 🟢 |
| Medição desta feature (2026-10-09) | 36 arquivos, 27.932.474 bytes na pasta real; 18 arquivos (6.631 bytes) classificáveis como resíduo de instrumento; **três** arquivos byte a byte idênticos da mesma árvore (mesmo sha256) mais uma quarta cópia com conteúdo distinto e mesmo tamanho | 🟢 |

## 3. Personas e cenários de uso

| Persona | Objetivo | Cenário-chave |
|---------|----------|---------------|
| Operador (usuário único, sem login, uso local) | Manter o dado genealógico fora do repositório e poder descartá-lo por decisão própria e informada | Termina uma sessão de análise, aponta a pasta para fora do repositório e roda o expurgo em modo de simulação para ver o que seria removido |
| Instrumento de verificação (harness de paridade: comparador diferencial entre o sistema atual e o oráculo congelado do legado) | Medir paridade sem tocar no dado do operador | Executa a paridade completa e a pasta real fica com o mesmo inventário, byte a byte |

## 4. Regras de negócio novas ou alteradas

1. **RN-01:** No uso declarado do sistema, a pasta que recebe os arquivos enviados não reside sob a
   raiz do repositório, nos dois modos de execução: no processo local ela é apontada por configuração
   de sessão, e no contêiner o destino é uma pasta do host fora do repositório. A resolução da pasta
   continua sendo a do legado — padrão `<diretório do app>/uploads`, sobreposto pela configuração de
   processo —, e é a configuração que garante o afastamento, não o padrão. 🟢
   - Origem no legado: `_reversa_sdd/upload-gedcom/contracts.md#2.2`, cujo padrão é `<diretório do app>/uploads`
   - Tipo: **alterada** no modo de operação; a regra de resolução permanece **preservada**
   - Decidida em 2026-10-09 pelas respostas 1a e 3b da sessão de esclarecimentos
2. **RN-02:** O leiaute dos nomes dentro da pasta permanece `<16 hexadecimais>__<nome visível>`,
   derivado do conteúdo; nada é renomeado nem movido dentro da pasta. 🟢
   - Origem no legado: `_reversa_sdd/upload-gedcom/contracts.md#2.1`
   - Tipo: **preservada** por esta feature (a feature não a altera)
3. **RN-03:** A pasta é resolvida uma única vez, no arranque do processo, e a mesma função resolve
   escrita e leitura; a configuração de processo tem precedência sobre o padrão. 🟢
   - Origem no legado: `_reversa_sdd/upload-gedcom/contracts.md#2.2`
   - Tipo: **preservada**
4. **RN-04:** A aplicação em execução continua **sem** apagar arquivo enviado. O expurgo é ferramenta
   separada, acionada pelo operador, e nunca comportamento do runtime. 🟢
   - Origem no legado: `_reversa_sdd/upload-gedcom/contracts.md#2.2` (linha "Remoção") e
     `_reversa_sdd/state-machines.md#5`
   - Tipo: **preservada**
5. **RN-05:** Instrumento de verificação não escreve na pasta de upload do operador; escreve em pasta
   descartável própria. **Ler** os arquivos reais continua permitido, porque é deles que vêm as
   fixtures de paridade. 🟢 (medido)
   - Origem no legado: precedente de `_reversa_sdd/addenda/006-fronteira-aplicacao-ports.md`; a
     regressão é medida nesta feature
   - Tipo: **nova**
6. **RN-06:** O expurgo opera sobre um **manifesto explícito e revisável**, gerado por comando, com
   nome, `sha256` e motivo por arquivo; remove apenas o que está no manifesto. Nenhuma remoção se apoia
   em padrão de nome, em tamanho ou em data. Cópias byte a byte idênticas de arquivo do operador **não**
   são removidas: são relatadas. 🟢
   - Origem no legado: princípio I de `.reversa/principles.md` (dado real fora do versionamento) e o
     precedente de melhor esforço de `_reversa_sdd/parity/_clean_residue.py`
   - Tipo: **nova**
   - Decidida em 2026-10-09 pelas respostas 4a e 5a da sessão de esclarecimentos

## 5. Requisitos Funcionais

| ID | Requisito | Prioridade | Critério de aceite | Confidência |
|----|-----------|------------|--------------------|-------------|
| RF-01 | A raiz da pasta de upload é definida por configuração de processo (`ANALISADOR_UPLOAD_FOLDER`), lida antes de qualquer escrita, e o operador a aponta para fora do repositório; pasta inexistente é criada no arranque | Must | Com a configuração apontando para fora da raiz do repositório, um envio conclui, o arquivo aparece no destino configurado e o inventário da pasta dentro do repositório fica inalterado; com o destino ainda inexistente, o arranque cria a pasta e o envio conclui | 🟢 |
| RF-02 | No contêiner, os arquivos enviados sobrevivem a derrubar e subir a composição sem que a pasta precise estar dentro do repositório, e o destino fica acessível pelo sistema de arquivos do host | Must | Depois de derrubar e subir, a contagem e os nomes dos arquivos são os mesmos de antes, **incluindo os migrados**; a pasta do host mostra os mesmos arquivos | 🟢 |
| RF-03 | A continuidade entre requisições é preservada: a referência devolvida no formulário continua resolvendo depois da mudança de raiz | Must | A sequência envio da árvore → busca de caminho → análise de DNA conclui com sucesso, sem resposta de "arquivo não existe mais" | 🟢 |
| RF-04 | As sondas de verificação deixam a pasta real do operador intacta | Must | Inventário da pasta real (nomes e sha256 de cada arquivo) idêntico antes e depois de uma execução completa da paridade | 🟢 |
| RF-05 | Existe um comando que gera o **manifesto de resíduo** e um comando de expurgo que, em modo de simulação, lista exatamente o que removeria e não remove nada | Must | A simulação lista os arquivos do manifesto e o inventário da pasta fica inalterado ao final; com o manifesto vazio, o relatório sai vazio e sem erro; o manifesto é regenerável por comando e registra o critério que o produziu | 🟢 |
| RF-06 | O expurgo, quando executado de verdade, remove apenas o que está no manifesto, relata o que não conseguiu remover e relata as duplicatas byte a byte idênticas que encontrou | Must | Nenhum arquivo fora do manifesto é removido; cada remoção falha aparece nomeada no relatório final; as duplicatas idênticas aparecem no relatório e **continuam** no disco | 🟢 |
| RF-07 | Nenhum arquivo existente é apagado, renomeado ou movido por esta feature; arquivo migrado para a nova raiz é **copiado** e conferido por hash, e a origem permanece intacta | Must | Inventário por sha256 antes e depois: todo arquivo preexistente continua existindo na origem, com o mesmo conteúdo, e existe também no destino | 🟢 |
| RF-08 | Os dois modos de execução apontam para o mesmo destino canônico, declarado uma única vez | Must | O caminho aparece idêntico no procedimento local e no destino da composição; alternar entre os modos não invalida a referência de uma página aberta | 🟢 |

## 6. Requisitos Não Funcionais

| Tipo | Requisito | Evidência ou justificativa | Confidência |
|------|-----------|----------------------------|-------------|
| Integridade de dados | Nenhum arquivo do operador pode ser perdido: movimentação de raiz é cópia verificada por hash, nunca remoção seguida de nova escrita | Medido em 2026-10-09: 36 arquivos, 27.932.474 bytes, incluindo **três** arquivos com o mesmo sha256 e uma quarta cópia de mesmo tamanho e conteúdo distinto — qualquer heurística de "duplicata" precisa de conferência, não de suposição | 🟢 |
| Testes | Toda mudança de comportamento chega com teste que falha antes e passa depois | Princípio III de `.reversa/principles.md` | 🟢 |
| Versionamento | Nenhum dado real entra no versionamento, inclusive os arquivos usados para exercitar o expurgo, que são sintéticos e criados em pasta temporária | Princípio I de `.reversa/principles.md`; `.gitignore` cobre `uploads/` em qualquer profundidade | 🟢 |
| Portabilidade | O destino não pode ser pasta sujeita a limpeza automática do sistema operacional | A leitura do arquivo acontece só durante a requisição; uma remoção automática entre dois `POST` apareceria como "arquivo não existe mais" no meio da sessão, de forma intermitente | 🟡 |
| Concorrência | A mudança não introduz estado novo compartilhado entre as 4 threads; a pasta continua sendo o único estado em disco | `_reversa_sdd/architecture.md#7` (dívidas 3 e 8) | 🟢 |
| Observabilidade | O expurgo informa, ao final, o que removeu, o que não removeu e por quê | Precedente de melhor esforço com relatório em `_reversa_sdd/parity/_clean_residue.py` | 🟢 |
| Natureza da mudança | A troca de raiz e a correção do instrumento são **organizacionais**: o resultado da paridade e o resultado das análises não mudam. O único comportamento novo é o expurgo | Princípio II de `.reversa/principles.md` | 🟢 |
| Documentação | A configuração da pasta, o destino canônico, o destino recomendado e os procedimentos de migração e de limpeza passam a estar na documentação do operador (tabela de variáveis do `README.md` e `onboarding.md` da feature). Sob a resposta 1a é esta documentação que sustenta o afastamento da pasta, e não o padrão do código: um operador que não a leia volta a gravar dentro do repositório sem receber erro. Nenhuma afirmação que deixa de ser verdadeira permanece, inclusive a justificativa da guarda de instância única | `_reversa_sdd/inventory.md#4` (a variável existe e não está na tabela do README) e `README.md#uma-instância-por-vez` | 🟢 |
| Segurança | O expurgo não segue link simbólico nem sai da pasta alvo, e recusa remover qualquer arquivo que não esteja na lista classificada | Contrato de forma fechada de `_reversa_sdd/upload-gedcom/contracts.md#2.1`, que existe justamente para impedir escape de caminho | 🟡 |

## 7. Critérios de Aceitação

```gherkin
Cenário: uso local com a pasta fora do repositório
  Dado que a pasta de upload está configurada para um diretório fora da raiz do repositório
  Quando o operador envia uma árvore GEDCOM
  Então o arquivo é gravado no diretório configurado
  E nenhum arquivo novo aparece sob a raiz do repositório

Cenário: destino ainda inexistente
  Dado que a pasta configurada para receber os arquivos não existe
  Quando a aplicação é iniciada
  Então a pasta é criada
  E o envio seguinte conclui com sucesso

Cenário: continuidade entre requisições
  Dado que uma árvore foi enviada com a pasta fora do repositório
  Quando o operador busca um caminho e depois roda a análise de DNA na mesma página
  Então as duas análises concluem com sucesso
  E nenhuma resposta diz que o arquivo não existe mais

Cenário: a composição preserva os arquivos
  Dado que o sistema está no ar e há arquivos enviados
  Quando a composição é derrubada e subida de novo
  Então os mesmos arquivos continuam disponíveis, com os mesmos nomes
  E a análise seguinte conclui com sucesso

Cenário: a paridade não toca na pasta real
  Dado o inventário da pasta real, com nome e sha256 de cada arquivo
  Quando a paridade é executada por completo
  Então o inventário ao final é idêntico ao inicial

Cenário: simulação de expurgo
  Dado que existem arquivos classificados como resíduo de instrumento
  Quando o expurgo roda em modo de simulação
  Então ele lista exatamente os arquivos que removeria
  E nenhum arquivo é removido

Cenário: expurgo parcialmente falho
  Dado que um arquivo classificado não pode ser removido pelo sistema operacional
  Quando o expurgo roda de verdade
  Então os demais arquivos classificados são removidos
  E o relatório final nomeia o arquivo que permaneceu

Cenário: arquivo do operador não é tocado
  Dado que a pasta real contém arquivos do operador e arquivos de resíduo
  Quando o expurgo roda de verdade com o manifesto
  Então todo arquivo do operador continua existindo, com o mesmo sha256

Cenário: migração para a nova raiz
  Dado que a pasta antiga contém arquivos enviados, com nome e sha256 registrados
  Quando o operador migra os arquivos para a raiz nova
  Então cada arquivo existe no destino com o mesmo conteúdo
  E a origem permanece intacta, com os mesmos arquivos

Cenário: os dois modos apontam para o mesmo destino
  Dado um destino canônico declarado na documentação
  Quando o operador alterna entre rodar no processo local e na composição
  Então a referência de uma página aberta continua resolvendo nos dois modos
```

## 8. Prioridade MoSCoW

| Item | MoSCoW | Justificativa |
|------|--------|---------------|
| RF-01 | Must | É o objetivo declarado da feature: o dado sai da árvore do repositório |
| RF-02 | Must | Sem isso, o contêiner perde os arquivos a cada recriação — e com eles a continuidade do histórico |
| RF-03 | Must | A continuidade entre requisições é contrato vigente (`contracts.md#3`); quebrá-la inviabiliza o uso |
| RF-04 | Must | É a causa medida do resíduo: sem a correção, a pasta suja de novo na próxima verificação |
| RF-05 | Must | Simular antes de remover é a única forma de o expurgo ser seguro |
| RF-06 | Must | Expurgo que falha em silêncio é pior que expurgo nenhum |
| RF-07 | Must | Perder arquivo do operador é inaceitável, e há três arquivos idênticos que uma heurística ingênua trataria como descartáveis. É também a garantia que torna seguro apagar a pasta antiga **depois** da migração |
| RF-08 | Must | Com 1a e 3b existem dois pontos de configuração; sem um destino canônico, alternar entre modos quebra a continuidade da página aberta |
| RNF Documentação | Must | **Promovido de Should para Must em 2026-10-09:** sob a resposta 1a, é a documentação — não o padrão do código — que mantém a pasta fora do repositório |
| RNF Portabilidade | Should | Decisão de destino; erra quem escolhe a pasta de temporários do sistema |
| RNF Segurança do expurgo | Should | Reforça o RF-06; o contrato de forma fechada já existe e deve ser reaproveitado |

## 9. Esclarecimentos

### Sessão 2026-10-09

Cinco perguntas apresentadas, cinco respondidas. O conjunto resolve as três dúvidas da versão inicial
e as duas lacunas de cobertura que a leitura do documento revelou (migração dos arquivos existentes e
destino das cópias idênticas).

- **Q:** Escopo — como o operador passa a usar a pasta fora do repositório no uso local? (a)
  procedimento documentado, com o padrão do código preservado; (b) o padrão do código muda; (c) arquivo
  de configuração local; (d) resposta livre.
  **R:** **1a** — procedimento documentado: o operador aponta a pasta por configuração de sessão e o
  padrão do código continua `<diretório do app>/uploads`. Consequência aceita: **nenhuma linha de `src/`
  é alterada**, e é a documentação que passa a sustentar o afastamento da pasta — esquecer a
  configuração não gera erro e volta a gravar dentro do repositório, o que está registrado como risco
  no RNF de Documentação.
- **Q:** Migração — o que acontece com os 36 arquivos existentes quando a raiz mudar? (a) copiar com
  conferência por `sha256`, origem intacta; (b) raiz nova vazia, com reenvio manual; (c) mover de fato;
  (d) adiar a troca de raiz para outra feature.
  **R:** **2a** — cópia verificada por `sha256` arquivo a arquivo, com a pasta antiga intacta. É o que
  fecha o objetivo: depois da cópia conferida, o operador pode apagar a pasta do repositório com
  segurança, e é esse passo que retira os 27,9 MB de dado genético da árvore do repositório. As
  referências do histórico no banco continuam resolvíveis, porque os arquivos passam a existir na raiz
  nova com os **mesmos nomes** derivados de conteúdo.
- **Q:** Contêiner — onde a pasta passa a viver no modo com contêiner? (a) volume nomeado na pasta do
  contêiner; (b) pasta do host fora do repositório, montada por caminho absoluto; (c) manter o ponto de
  montagem atual nesta entrega.
  **R:** **3b** — pasta do host fora do repositório, montada por caminho absoluto. Consequência
  declarada: a composição passa a conter um caminho específico desta máquina, e em troca o operador
  mantém o acesso direto pelo sistema de arquivos e o backup trivial.
- **Q:** Classificação — qual critério marca um arquivo como resíduo de instrumento? (a) manifesto
  explícito e revisável; (b) conjunto fechado de nomes conhecidos dos instrumentos; (c) janela de
  execução.
  **R:** **4a** — manifesto explícito, gerado por comando, com nome, `sha256` e motivo por arquivo; o
  expurgo remove apenas o que está nele. O manifesto precisa ser **regenerável**, senão envelhece na
  próxima execução da paridade — daí o requisito de regeneração em `RF-05`.
- **Q:** Duplicatas — e as quatro cópias da mesma árvore (três byte a byte idênticas, uma de conteúdo
  distinto e mesmo tamanho)? (a) não tocar, apenas relatar; (b) remover as idênticas mantendo uma; (c)
  tratar em feature separada.
  **R:** **5a** — o expurgo não toca nelas: relata as duplicatas e a decisão fica com o operador. As três
  cópias idênticas e a quarta permanecem no disco.

**Efeitos desta sessão no documento:** `RN-01` passou a declarar que o afastamento vem da configuração,
não do padrão; `RN-06` passou a exigir manifesto regenerável e a proibir remoção de duplicatas;
`RF-02`, `RF-05`, `RF-06` e `RF-07` foram reescritos; `RF-08` foi criado para o destino canônico único;
o RNF de Documentação subiu de `Should` para `Must`; e dois cenários de aceitação foram acrescentados.

## 10. Lacunas

Nenhuma lacuna em aberto. As três dúvidas da versão inicial foram resolvidas na sessão de 2026-10-09
(ver §9), junto com as duas lacunas de cobertura que a revisão do documento revelou — migração dos
arquivos existentes e destino das cópias idênticas.

**Restrição de política a resolver no plano** (não é dúvida de requisito, é limite de escrita deste
projeto): `.reversa/reversa-config.json` libera `src/**`, `tests/**`, `docker/**`, `docs/**`,
`README.md`, `docker-compose.yml` e afins, mas **não** uma pasta nova como `scripts/**`. Ou o comando
de expurgo entra num caminho já liberado, ou o operador acrescenta o glob ao arquivo de configuração —
edição que, pela política do Reversa, é ato exclusivo dele.

## 11. Histórico de alterações

| Data | Alteração | Autor |
|------|-----------|-------|
| 2026-10-09 | Versão inicial gerada por `/reversa-requirements` | reversa |
| 2026-10-09 | Sessão de esclarecimentos (1a, 2a, 3b, 4a, 5a): `RN-01` e `RN-06` reescritas; `RF-02`, `RF-05`, `RF-06` e `RF-07` reescritos; `RF-08` criado; RNF de Documentação promovido a `Must`; dois cenários acrescentados; `## 10. Lacunas` zerada | reversa |

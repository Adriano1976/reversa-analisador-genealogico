# Legacy Impact: renomear a raiz de código de `analisador-genealogico/` para `src/`

> Identificador da feature: `003-renomear-pasta-app-para-src`
> Data: `2026-10-03`
> Âncora: **legado** (`_reversa_sdd/architecture.md` + `_reversa_sdd/domain.md`)
> Ações executadas: T001 a T020 de 21. `T021` pendente (pipeline de documentação).

## Arquivos afetados

| Arquivo afetado | Componente | Tipo | Severidade | Justificativa |
|---|---|---|---|---|
| `src/app.py` | Camada de apresentação (`architecture.md#1`) | `regra-alterada` | LOW | Mudou de caminho; **nenhuma linha de conteúdo foi alterada** (D-03). A pasta de upload e os templates são resolvidos a partir do próprio arquivo, então acompanham o diretório |
| `src/reconstructed/` (12 arquivos) | Núcleo (`architecture.md#1`) | `regra-alterada` | LOW | Mudou de caminho; nenhum nome de módulo mudou e **nenhuma linha de importação foi tocada** (D-04). Paridade medida em 100% depois da mudança |
| `src/templates/index.html` | Tela única (`architecture.md#1`) | `regra-alterada` | LOW | Mudou de caminho; conteúdo idêntico |
| `src/uploads/` | Estrutura de runtime (`architecture.md#3.3`) | `regra-alterada` | MEDIUM | Mudou de caminho, carregando **9 arquivos de dados reais, 16.920.784 bytes**, conferidos antes e depois. O contrato de chave derivada do conteúdo permanece idêntico |
| `requirements.txt` | Dependências (`dependencies.md#1`) | `regra-alterada` | LOW | Subiu da raiz de código para a raiz do repositório; os comandos publicados foram atualizados |
| `README.md` (raiz) | Documentação viva | `regra-alterada` | LOW | Árvore do projeto, comandos de instalação e execução, e nota de política atualizados |
| `tests/` (8 arquivos) | Suíte de testes | `regra-alterada` | LOW | 9 pontos de caminho atualizados, incluindo a definição da pasta do aplicativo que alimenta o `root_path` e o caminho do arquivo de entrada |
| `pyrefly.toml` | Configuração de ferramenta | `regra-alterada` | LOW | `search-path` passou a apontar para `src` |
| `.vscode/settings.json` | Configuração de ferramenta | `regra-alterada` | LOW | Caminho do editor atualizado para `./src` |
| `src/README.md` (README herdado) | Documentação do projeto original | `componente-extinto` | LOW | Removido por decisão do usuário; anunciava uma biblioteca abandonada na migração para Mermaid (`architecture.md#5`, dívida 9) |
| `src/.gitignore.txt` | Configuração do módulo | `componente-extinto` | LOW | Removido por decisão do usuário; a única regra exclusiva apontava para artefato que o projeto deixou de gerar |
| `src/static/` | Diretório de artefatos estáticos | `componente-extinto` | LOW | Diretório vazio removido; o conteúdo estático deixou de existir com a migração para Mermaid |
| `_reversa_sdd/parity/*.py` (7) e `_reversa_sdd/oracle/run_oracle.py` | Instrumentação de desenvolvimento (`architecture.md#6`) | `regra-alterada` | LOW | 21 ocorrências de caminho atualizadas. É instrumentação executável, não registro histórico |

**Nenhum arquivo de `_reversa_bugs/`, `_reversa_refactor/` ou `_reversa_forward/` foi editado.** Nenhuma spec de `_reversa_sdd/` foi reescrita: a correção documental foi publicada como adendo (RN-03).

## Diff conceitual por componente

**Camada de apresentação e núcleo.** O sistema continua com as duas camadas de contratos opostos que `architecture.md#1` descreve. O que mudou é o diretório que as abriga. Como o nome do pacote do núcleo não mudou, a única coisa que precisou de ajuste fora do próprio diretório foram os valores que apontam para a raiz de caminho — e nenhum deles está dentro do `app.py`, que resolve tudo o que precisa a partir do próprio arquivo.

**Pasta de upload.** Saiu de `analisador-genealogico/uploads/` e entrou em `src/uploads/`, com os 9 arquivos intactos. O contrato do adendo vigente do defeito de upload permanece: chave derivada do conteúdo, nome do cliente como metadado, validação antes da gravação, e resolução da pasta ancorada no arquivo do aplicativo — nunca no diretório corrente. A regra de ignore do versionador alcança a pasta em qualquer profundidade, o que foi confirmado por consulta ao próprio mecanismo de ignore.

**Instrumentação de desenvolvimento.** Os scripts que comparam o oráculo congelado com o código atual passaram a resolver o novo caminho. A paridade foi remedida depois da mudança e permaneceu em 100%, com a linha de log que identifica o candidato já citando o caminho novo. A contraprova de paridade teve a string de busca atualizada junto: ela localiza, dentro do instrumento, a linha que aponta para o candidato, e teria deixado de encontrar o que procura se apenas o caminho real fosse trocado.

**Documentação.** As specs da extração citam o caminho antigo em aproximadamente 259 pontos e **não foram reescritas**. O adendo publicado declara uma regra de leitura única — toda citação de `analisador-genealogico/` deve ser lida como `src/` — com uma exceção nominal para as citações ao commit congelado, onde o caminho histórico está correto.

## Preservadas

Regras confirmadas do legado que continuam intactas, verificadas por paridade de 100% nas 6 fixtures e pela suíte com resultado idêntico ao da linha de base:

- **Relação prevista por faixa de cM** e o contrato de devolver **lista**, nunca escalar; `cM ≤ 0` e valor não numérico devolvendo lista vazia (`domain.md#2.1`)
- **Conexão direta e indireta** em dois estágios, com tetos de 20 iterações de profundidade e 40 arestas, e as mensagens de sucesso e de ausência de conexão (`domain.md#2.2`)
- **Matching difuso**: fórmula de score, bônus de sobrenome, filtro anti-falso-positivo, interseção mínima adaptativa, limiar de Jaccard com relaxamento condicionado, equivalentes de grafia, abreviações e desempate de candidato (`domain.md#2.3`)
- **Limites de busca** (`domain.md#2.4`)
- **Regras de decisão e fluxo** das três ações do usuário (`domain.md#3`)
- **Mensagens de contrato** do núcleo e da camada de rota, literais (`domain.md#4.1` e `#4.2`)
- **Ausência de máquinas de estado e de controle de acesso**, com a consequência de negócio registrada (`domain.md#5` e `#6`)
- **Contrato de upload** do adendo vigente: chave derivada do conteúdo, teto de requisição, recurso recusado não gravado, validação de conteúdo e não de extensão (`addenda/bug-BUG-20260929-QMLY-v001.md`)

## Modificadas

**Nenhuma regra de negócio foi alterada ou removida.** Esta feature é estrutural: mudou o caminho de arquivos e removeu dois artefatos de documentação e configuração do projeto original. Nenhum comportamento observável mudou — o que é exatamente o que o princípio II exige e o que os dois gates mediram.

Por consequência, o `regression-watch.md` não deriva itens de regras modificadas; ele vigia as **condições estruturais que esta feature estabeleceu** e que uma extração futura precisa encontrar verdadeiras.

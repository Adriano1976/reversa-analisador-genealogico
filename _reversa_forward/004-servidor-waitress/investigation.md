# Investigation: servir a aplicação por um servidor de produção no Windows

> Identificador: `004-servidor-waitress`
> Data: `2026-10-03`
> Requirements: `_reversa_forward/004-servidor-waitress/requirements.md`

## 1. O problema, medido no disco

O bloco de entrada do `src/app.py` chama o servidor de desenvolvimento com depuração ligada. O aviso que o usuário quer eliminar é emitido pelo próprio servidor de desenvolvimento do framework, e não pelo projeto: é uma advertência de biblioteca para o modo errado de uso em produção.

Três fatos apurados nesta investigação, todos por execução e não por leitura de prosa:

| Fato | Como foi verificado |
|------|---------------------|
| O servidor de desenvolvimento do framework **já atende em múltiplas threads** | A fonte instalada do framework faz `options.setdefault("threaded", True)` antes de delegar ao servidor |
| O servidor de produção listado no arquivo de dependências **não sobe no Windows** | `import fcntl` falha com `ModuleNotFoundError`. O pacote em si importa (versão 26.0.0), mas `gunicorn.arbiter` e `gunicorn.workers.sync` falham com `ModuleNotFoundError: No module named 'fcntl'` |
| O projeto já tem precedente de configuração por variável de ambiente | `src/app.py` lê `ANALISADOR_UPLOAD_FOLDER` em `_pasta_uploads()` |

O primeiro fato corrige uma intuição comum: trocar o servidor de desenvolvimento por um servidor de produção **não aumenta** a concorrência por si só, e o servidor de produção escolhido abre menos threads do que o servidor de desenvolvimento, que abre uma por requisição. O estado global da árvore genealógica, compartilhado no processo, não é criado nem resolvido por esta troca.

O segundo fato é o que dá sentido à feature: o arquivo de dependências lista um servidor de produção **que não consegue subir na plataforma alvo**. A extração já havia registrado isso como dívida e como inferência (`_reversa_sdd/architecture.md#6`, `_reversa_sdd/dependencies.md#5`), sem apontar a causa. A causa é a dependência de uma chamada de sistema que só existe em plataformas POSIX.

## 2. Alternativas avaliadas

| Alternativa | Veredito | Motivo |
|-------------|----------|--------|
| Manter o servidor de desenvolvimento | descartada | É a origem do aviso, e não tem suporte de operação |
| Servidor listado hoje no arquivo de dependências | descartada | Não importa no Windows por dependência de `fcntl`, verificado por execução |
| Servidor de produção com compilador ou extensão nativa | descartada | Acrescenta exigência de compilação na plataforma alvo, contra a RNF de portabilidade |
| Servidor de produção em Python puro, compatível com Windows | **adotada** | Atende portabilidade, implementa a interface padrão e é a escolha declarada do usuário |
| Manter o servidor de desenvolvimento atrás de variável de ambiente | descartada | O usuário decidiu por um único modo de execução; manter dois modos reintroduz o aviso quando alguém liga o modo antigo |
| Endereço de escuta fixo no código | descartada | Impede restringir a escuta em campo sem editar código |
| Endereço de escuta só na máquina local | descartada | Contraria o cenário de demonstrar o sistema a partir de outro equipamento |
| Teste de fumaça contra porta efêmera | descartada nesta rodada | Prova mais forte, com custo de tempo e risco de flutuação na suíte; fica como candidato a integração futura |
| Declarar o bloco de entrada fora de cobertura | descartada | O princípio III exige teste que cubra a mudança, e uma exceção silenciosa enfraqueceria o princípio |

## 3. Padrões aplicados

1. **Configuração por ambiente, com padrão declarado.** O valor padrão vive no código; o ambiente sobrescreve. É o padrão que o projeto já pratica em `ANALISADOR_UPLOAD_FOLDER`.
2. **Dependência de execução importada no ponto de uso.** Importar dentro do bloco de entrada mantém o módulo importável por quem só quer a aplicação, sem exigir o servidor instalado. Isso importa aqui porque a suíte e o harness de paridade importam esse módulo.
3. **Falha de pré-condição com instrução de correção.** Ausência de dependência nomeia o pacote e o comando de instalação, em vez de deixar a exceção crua subir.
4. **Um único modo de execução.** Elimina a classe de defeito em que o modo de desenvolvimento é usado sem querer em operação.

## 4. Fontes

Todas as fontes são locais, e nenhuma fonte externa foi consultada nesta investigação. Isso é declarado de propósito: não há link de documentação de terceiro a citar, e inventar um seria pior do que registrar a ausência.

| Fonte | Uso |
|-------|-----|
| `src/app.py` | bloco de entrada atual e o precedente `ANALISADOR_UPLOAD_FOLDER` |
| `requirements.txt` | dependências atuais, incluindo a que não opera na plataforma alvo |
| fonte instalada do framework web | a linha `options.setdefault("threaded", True)` |
| `_reversa_sdd/architecture.md#6` | dívida registrada sobre o servidor de produção sem uso no código |
| `_reversa_sdd/dependencies.md#2` e `#5` | dependências diretas e ausência de uso interno |
| `_reversa_sdd/migration/migration_strategy.md#1` | ausência de CI/CD, container e fluxo de deploy no legado |
| `.reversa/principles.md#II` e `#III` | preservação de comportamento e cobertura por teste |

## 5. Segunda rodada, 2026-10-04

Esta seção foi aberta depois da **primeira execução real** da entrega, e existe porque a execução mediu o que a leitura de código não teria medido.

### 5.1. A plataforma não impede duas instâncias

O cenário de porta ocupada do `requirements.md` partia de uma premissa falsa para o Windows. O experimento foi controlado, numa porta livre, com duas instâncias do servidor de produção:

| Observação | Resultado |
|---|---|
| A primeira instância subiu e escutou | `TCP 127.0.0.1:5099 LISTENING`, processo próprio |
| A segunda instância, mesma porta, com a primeira no ar | **subiu e continuou viva**, imprimindo a mesma linha de inicialização |
| O `netstat` com as duas no ar | **dois processos distintos em `LISTENING` na mesma porta** |
| O processo mais antigo foi derrubado pela tentativa nova | não |

A causa é conhecida: o servidor usa `SO_REUSEADDR`, e a semântica do Windows para essa opção é permissiva, permitindo que dois processos escutem o mesmo endereço e a mesma porta. Em outras plataformas, `SO_REUSEADDR` não autoriza dois ouvintes vivos, e o segundo `bind` falha.

**Consequência para o requisito:** a falha que o cenário pedia não existia, e por isso não havia mensagem a melhorar nem código de saída a exigir. A exclusividade passa a ser responsabilidade da aplicação, e o requisito foi reescrito.

**Consequência operacional do que foi medido:** com duas instâncias, a distribuição das requisições entre elas não é determinística, e cada processo tem o seu próprio estado global da árvore genealógica, em `core/gedcom_state.py`. Duas requisições do mesmo navegador podem ser atendidas por processos diferentes, e a segunda responde que não há árvore carregada.

### 5.2. Como garantir a exclusividade, verificado na fonte instalada

A aplicação pode criar o socket de escuta por conta própria e entregá-lo ao servidor pronto. Três fatos apurados na fonte do pacote instalado:

| Fato | Evidência |
|---|---|
| O servidor aceita uma lista de sockets prontos | `Adjustments(sockets=[])` é aceito, e o padrão é lista vazia |
| Com socket pronto, o servidor **não** faz `bind` nem `listen` | Em `create_server`, o caminho que liga o socket só roda dentro de `if not adj.sockets`, e os sockets recebidos entram com `bind_socket=False`. Em `BaseWSGIServer.__init__`, a ligação é `if bind_socket: self.bind_server_socket()`, e é `bind_server_socket` que chama `bind` |
| O Windows oferece a marca de uso exclusivo | `socket.SO_EXCLUSIVEADDRUSE` existe, com valor `-5` |

Ou seja: a aplicação cria o socket, marca-o para uso exclusivo, faz `bind` e `listen`, e só então entrega ao servidor. A partir daí o sistema recusa a segunda instância durante toda a vida do processo, **sem janela de corrida**, que é o defeito da alternativa de fechar o socket antes de servir.

O detalhe que a implementação não pode esquecer: **a aplicação precisa fazer o `listen`**, porque o servidor não o fará. Um socket ligado sem `listen` não aceita conexão, e o erro apareceria como aplicação muda, não como exceção.

### 5.3. Alternativas novas, avaliadas

| Alternativa | Veredito | Motivo |
|---|---|---|
| Socket próprio com marca de uso exclusivo, entregue pronto | **adotada** | Exclusividade garantida pelo sistema, sem janela de corrida, e verificada na fonte do pacote |
| Fazer `bind` exclusivo, fechar o socket e só então servir | descartada | Deixa uma janela entre fechar e servir, e outra instância pode entrar nela |
| Arquivo de trava com criação atômica | descartada | É a opção que o usuário **não** escolheu, e exige tratamento de arquivo órfão depois de queda abrupta |
| Sondar a porta com uma conexão antes de servir | descartada | Sofre de corrida e não garante nada: as duas instâncias podem ver a porta livre |
| Confiar na plataforma | descartada | Foi o que a medição de 5.1 derrubou |
| `pip freeze` completo no arquivo de dependências | descartada | Arrasta ferramentas de desenvolvimento para um arquivo de runtime |
| Arquivo de trava de dependências separado | adiada | Exigiria liberar caminho novo em `allowedPaths`: a política libera `requirements.txt` e não `requirements.*.txt` |

### 5.4. Versões validadas no ambiente que executa

Medidas por leitura dos metadados das distribuições instaladas, no interpretador que roda a aplicação:

| Dependência | Versão |
|---|---|
| `Flask` | 3.1.3 |
| `ged4py` | 0.5.2 |
| `networkx` | 3.6.1 |
| `pandas` | 3.0.3 |
| `thefuzz` | 0.22.1 |
| `waitress` | 3.0.2 |

Duas delas aparecem só como dependências de outras, e não entram no arquivo: `rapidfuzz 3.14.5` e `Werkzeug 3.1.8`. É por isso que fixar apenas as diretas **não** garante o mesmo conjunto de pacotes, e a limitação está declarada na decisão `D-12` do roadmap.

### 5.5. Fontes desta rodada

Além das fontes da primeira rodada: a execução real do aplicativo em 2026-10-04, os dois experimentos controlados de porta, a fonte instalada do pacote do servidor, e o `netstat` do sistema. Nenhuma fonte externa foi consultada, e nenhum link é citado por esse motivo.

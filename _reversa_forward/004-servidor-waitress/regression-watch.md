# Regression Watch: servir a aplicação por um servidor de produção no Windows

> Identificador da feature: `004-servidor-waitress`
> Data: `2026-10-03`
> Base: `legacy-impact.md` desta feature
> Peso: os itens abaixo são condições **estruturais** estabelecidas por esta feature, verificadas na execução. Uma extração futura deve encontrá-las verdadeiras.

## Watch principal

| ID | Origem (arquivo, seção) | Regra esperada após mudança | Tipo de verificação | Sinal de violação |
|----|--------------------------|------------------------------|---------------------|-------------------|
| W001 | `src/app.py`, bloco de entrada | O ponto de entrada inicia a aplicação por um servidor WSGI de produção, e o servidor de desenvolvimento do framework **não** é chamado em nenhum ponto do código | presença | Reaparecimento de chamada ao servidor de desenvolvimento, ou aviso de servidor de desenvolvimento na saída |
| W002 | `src/app.py`, bloco de entrada | Endereço de escuta, porta e concorrência vêm de `ANALISADOR_HOST`, `ANALISADOR_PORT` e `ANALISADOR_THREADS`, com padrões declarados no código | presença | Valor de escuta herdado de padrão de biblioteca, ou variável renomeada sem atualizar a documentação |
| W003 | `_reversa_sdd/domain.md#4.1` e `#4.2` | A superfície HTTP e as mensagens de contrato permanecem idênticas: mesma rota, mesmos métodos, mesmos nomes de campo, mesmas mensagens literais | presença | Divergência no comparador de paridade; mensagem de contrato alterada; campo de formulário renomeado |
| W004 | `requirements.txt` | O arquivo registra o servidor de produção e **não** lista a dependência que não importa no Windows | presença | Dependência de servidor ausente do arquivo, ou reaparecimento da dependência que exige `fcntl` |
| W005 | `.reversa/principles.md#III`; `_reversa_sdd/parity/` | A suíte mantém o mesmo conjunto de testes mais os três testes do bloco de entrada, e a paridade permanece em 100 por cento | presença | Teste removido, desabilitado ou com resultado diferente; divergência nova no comparador |
| W006 | `src/app.py`, bloco de entrada | A aplicação **não coexiste consigo mesma**: o socket de escuta é criado pela própria aplicação, marcado com uso exclusivo no Windows, ligado com `bind` e `listen`, e entregue pronto ao servidor sem `host` nem `port` na mesma chamada | presença | Remoção da guarda; chamada ao servidor com `sockets` junto de `host` ou `port`, combinação que ele recusa com `ValueError`; socket entregue sem `listen` |
| W007 | `src/app.py`, bloco de entrada | O padrão do endereço de escuta atende **apenas a máquina local**, e abrir para a rede exige `ANALISADOR_HOST` | presença | Padrão de volta ao endereço que atende todas as interfaces; documentação descrevendo o padrão como aberto |
| W008 | `requirements.txt` | Toda linha de dependência declara a versão com `==`, nas versões validadas | presença | Linha sem versão, ou versão fixada diferente das validadas (`Flask 3.1.3`, `ged4py 0.5.2`, `networkx 3.6.1`, `pandas 3.0.3`, `thefuzz 0.22.1`, `waitress 3.0.2`) |

> **`W002` e `W006` se sobrepõem de propósito.** A `W002` verifica que os parâmetros operacionais vêm do ambiente; a `W006` verifica o que a aplicação faz com eles antes de servir. Uma mudança pode satisfazer a primeira e quebrar a segunda, e foi exatamente essa a forma do achado de 2026-10-04 sobre `sockets` junto de `host` e `port`.

> **`W004` não estava satisfeito nesta data.** A ação que troca o servidor no arquivo de dependências está bloqueada pela política de edição, porque `requirements.txt` não casa com nenhum glob de `allowedPaths`. O item entra no watch já com a condição pendente, para que a próxima verificação não o trate como cumprido.
>
> **Atualização de 2026-10-04:** `W004` **passou a estar satisfeito**. O usuário liberou o caminho, e as ações `T001` e `T002` foram executadas. Ver as medições abaixo.

## Observações

Itens sem peso de regressão, registrados para não se perderem:

- **O1**, pendência de entrega: as ações `T001` e `T002` seguem abertas em `actions.md`, ambas por consequência do bloqueio de política, e não por dificuldade técnica.
- **O2**, verificação não realizada: a ação `T011` (porta ocupada) não pôde ser executada nesta sessão porque a sandbox nega o diretório temporário do `pip`, e o servidor de produção não pôde ser instalado no ambiente.
- **O3**, lacuna substantiva do plano: o cenário de porta ocupada do `requirements.md` exige falha legível, e **nenhuma ação do plano implementa essa mensagem**. Com o servidor instalado, a expectativa é que a falha apareça como exceção de sistema operacional, e não como mensagem tratada.
- **O4**, consequência operacional declarada: com `requirements.txt` não atualizado, uma instalação limpa sobe a aplicação e a interrompe com mensagem que nomeia o pacote e o interpretador. O comportamento foi verificado na `T010`, e é o esperado enquanto a `T001` estiver bloqueada.
- **O5**, decisão de segurança vigente: o endereço padrão atende todas as interfaces de rede e a aplicação **não tem autenticação alguma**. Restringir é uma variável de ambiente, e a documentação traz o aviso.

### Medições de 2026-10-04

Observações novas, acrescentadas sem reescrever as anteriores. As duas primeiras **superam** o que dizem `O2` e `O3` acima, que descreviam a expectativa antes da medição.

- **O6**, comportamento medido, que corrige uma premissa desta feature: no Windows, **duas instâncias do servidor de produção escutam na mesma porta ao mesmo tempo**, porque o servidor usa `SO_REUSEADDR` e a semântica do Windows é permissiva nesse ponto. O experimento foi controlado, numa porta livre: as duas instâncias imprimiram a linha de inicialização, o `netstat` listou os dois processos em `LISTENING` na mesma porta, e as duas se mantiveram vivas. Consequências: o cenário de porta ocupada do `requirements.md` **não se realiza nesta plataforma**, e o risco real e medido é a coexistência de instâncias, cada uma com o seu próprio estado global da árvore genealógica, o que permite que duas requisições do mesmo navegador sejam atendidas por processos diferentes.
- **O7**, verificação ao vivo: o caminho feliz foi confirmado com o aplicativo em execução real, com `HTTP 200` na rota raiz, cabeçalho `Server: waitress`, formulário de upload presente e três requisições seguidas estáveis com o mesmo tamanho. O endereço em uso foi `127.0.0.1`, e não o padrão `0.0.0.0` do código, o que indica `ANALISADOR_HOST` definida na sessão da execução. O modo restrito à máquina local estava ativo.
- **O8**, higiene das verificações: os processos dos experimentos foram encerrados e as portas liberadas, conferido por `netstat`. Nenhum resíduo ficou no ambiente.
- **O9**, fechamento da pendência de dependência, também em 2026-10-04: o usuário acrescentou `requirements.txt` aos caminhos liberados, e as ações `T001` e `T002` foram executadas. O arquivo perdeu `gunicorn` e ganhou `waitress`, ficando em ordem alfabética, e `pip install -r requirements.txt` terminou com código de saída 0, com `waitress 3.0.2` visível tanto para `py -3.14` quanto para `python`. Isto **supera** as observações `O1` e `O4`: a instalação limpa a partir do arquivo passa a ter o servidor de produção. O `gunicorn` continua instalado na máquina, e isso é inofensivo, porque ele deixou de ser dependência do projeto.

### Medições da segunda rodada, 2026-10-04

Observações novas, acrescentadas sem reescrever as anteriores. A `O15` **corrige um número** do watch principal sem tocar na linha original, por esta tabela ser de registro.

- **O10**, a `T011` foi executada e agora confirma o requisito. Experimento controlado em porta livre, com o código desta rodada: a primeira instância atendeu `HTTP 200` com `Server: waitress`, a segunda terminou com código de saída 1 e mensagem legível sobre a porta em uso, sem pilha de exceção, e a primeira continuou atendendo depois da tentativa. Isto **supera** a `O6`, que registrava a coexistência como o comportamento medido: a coexistência continua sendo o que a plataforma faz sozinha, e é a aplicação que passou a recusar.
- **O11**, o mesmo experimento foi repetido com a instância que já estava no ar iniciada pelo caminho da **versão anterior**, em que o servidor cria o próprio socket e pede `SO_REUSEADDR` (confirmado com `getsockopt`, valor 1). A versão nova também recusou a subida, com código 1, e a instância antiga seguiu atendendo. É este resultado que torna honesta a instrução do plano de migração de encerrar a instância no ar antes de subir a versão nova.
- **O12**, correção de premissa da `D-10`, registrada também no `roadmap.md`: o servidor **faz** `listen` quando recebe socket pronto. Com `bind_socket=False` ele pula o `bind`, mas `accept_connections`, chamada na criação, chama `socket.listen(self.adj.backlog)` (`waitress/server.py`). A aplicação continua ligando o socket por conta própria, e o motivo correto é garantir que ele já esteja em escuta quando o servidor assumir.
- **O13**, contrato do servidor que restringe a implementação: `sockets` é mutuamente exclusivo de `host` e `port`, e a combinação levanta `ValueError` (`waitress/adjustments.py`, linhas 299 e 300). Consequência aceita: o endereço e a porta deixam de ser argumentos da chamada e passam a existir apenas no socket ligado, o que faz da linha de inicialização impressa pela aplicação a única observabilidade do endereço em uso. É o que mantém o RNF de observabilidade satisfeito.
- **O14**, diagnóstico da recusa separado por erro medido: `errno.EADDRINUSE` vale `10048` neste interpretador e chega para porta ocupada, enquanto endereço que não pertence à máquina chega com `10049`. A mensagem segue o erro, e os dois ramos foram verificados. Sem essa separação, um `ANALISADOR_HOST` inválido produziria a orientação errada.
- **O15**, correção de número do watch principal: a linha `W005` fala em "três testes do bloco de entrada", e o número está superado pela `T014`, que levou o arquivo a **sete** afirmações. A linha não foi reescrita. O conjunto de referência da `W005` passa a ser: suíte em **125 aprovados e 15 erros de ambiente**, os mesmos 15 da linha de base, e paridade em **100 por cento** nas 6 fixtures.
- **O16**, resíduo de ambiente, e uma repetição que não deveria ter acontecido: os processos dos experimentos foram encerrados, as portas liberadas, e os três scripts de verificação removidos do repositório. O `_clean_residue.py` fechou o resíduo da paridade (dois diretórios `.parity-run-*` e quatro arquivos gerados). **Mas a tentativa de apontar o diretório temporário do pytest para dentro do projeto já estava documentada como abandonada no próprio `_clean_residue.py`**, que lista `.parity-pytest-tmp/` como "criado numa tentativa com `--basetemp` (abandonada)" e explica que o sandbox nega remover diretórios no workspace. A tentativa foi repetida nesta rodada com outro nome, gastou tempo e deixou um diretório que precisou de acesso ampliado para ser removido. O registro fica: a resposta está no arquivo de limpeza, e a nota acrescentada ao `onboarding.md` repete o que ele já dizia.
- **O17**, evidência ao vivo da `RF-02`, com **controle positivo**: sem `ANALISADOR_HOST` definida, o `netstat` mostrou `127.0.0.1:5088` em `LISTENING`, a requisição na máquina local respondeu `HTTP 200`, e a requisição no endereço de rede da máquina (`192.168.1.40`) não respondeu. Com `ANALISADOR_HOST=0.0.0.0`, o `netstat` mostrou `0.0.0.0:5089` e as duas requisições responderam `HTTP 200`. O controle positivo é o que separa "não responde porque o padrão fecha" de "não responde porque a sondagem está quebrada", e ele entrou porque o critério de aceite tem as duas metades. As portas dos dois experimentos foram liberadas depois, conferido por `netstat`.

## Histórico de re-extrações

| Data | Extração | Veredito | Observação |
|------|----------|----------|------------|

## Arquivadas

Nenhuma.

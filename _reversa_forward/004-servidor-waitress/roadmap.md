# Roadmap: servir a aplicação por um servidor de produção no Windows

> Identificador: `004-servidor-waitress`
> Data: `2026-10-04`
> Requirements: `_reversa_forward/004-servidor-waitress/requirements.md`
> Confidência: 🟢 CONFIRMADO, 🟡 INFERIDO, 🔴 LACUNA
> **Revisão:** esta é a segunda rodada do plano. A primeira, de `2026-10-03`, decidiu `D-01` a `D-09`, e a entrega chegou a ser executada. A sessão de esclarecimento de `2026-10-04`, aberta depois da execução real, acrescentou requisito novo e revisou um valor. As decisões anteriores são **carregadas** aqui, e não descartadas; `D-02` aparece marcada como revista.

## 1. Resumo da abordagem

A primeira rodada trocou o servidor de desenvolvimento pelo de produção, com endereço, porta e concorrência lidos do ambiente. Esta rodada fecha três lacunas que só apareceram quando o aplicativo foi executado de verdade.

Primeiro, o **endereço padrão passa a ser a máquina local**: o padrão anterior atendia todas as interfaces de rede, e a aplicação não tem autenticação alguma. Segundo, a aplicação passa a **recusar subir quando já existe uma instância** no endereço e na porta configurados, porque a medição mostrou que a plataforma não impede a coexistência sozinha e que duas instâncias significam dois estados globais independentes. Terceiro, as dependências passam a ter **versão fixada**, porque dois ambientes da mesma máquina já divergiram.

A guarda de exclusividade é feita com um socket criado pela própria aplicação, marcado para uso exclusivo no Windows e entregue ao servidor já ligado, o que evita a janela de corrida de um `bind` que se fecha antes de servir.

## 2. Princípios aplicados

| Princípio | Como a feature se relaciona | Status |
|-----------|------------------------------|--------|
| I. Dados reais de DNA/GEDCOM nunca entram no versionamento | A feature não cria, lê nem versiona dado de entrada. Nada muda nesta rodada | respeita |
| II. Comportamento observável é preservado em refatoração | A feature é evolução deliberada, não refatoração. A `RN-01` mantém a superfície HTTP e as mensagens, e as três mudanças desta rodada são declaradas: o padrão de escuta fecha, a aplicação pode recusar subir, e as versões ficam fixas | respeita, com três mudanças observáveis declaradas |
| III. Nenhuma mudança sem teste que a cubra | A `RF-05` cobre a escolha do servidor por inspeção, e a `D-13` estende a inspeção à guarda de exclusividade. A recusa funcional, com dois processos, fica verificada no `onboarding.md` | respeita, com a cobertura funcional declarada como verificação de onboarding |
| IV. Arestas do grafo são tipadas | Não tocada: nenhum módulo do núcleo é alterado | respeita |
| V. Toda suposição de genealogia genética cita a fonte | Não tocada: nenhuma faixa, limiar ou heurística é alterada | respeita |

## 3. Decisões técnicas

| ID | Decisão | Justificativa | Alternativas descartadas | Confidência |
|----|---------|----------------|--------------------------|-------------|
| D-01 | O servidor de produção é o `waitress` | Escolha declarada do usuário, roda em Windows sem compilação e sem chamada de sistema POSIX | O servidor listado antes no arquivo, que exige `fcntl`; o servidor de desenvolvimento; servidores que exigem compilador | 🟢 |
| D-02 | **Revista em 2026-10-04.** O endereço de escuta e a porta vêm de `ANALISADOR_HOST` e `ANALISADOR_PORT`, com padrões declarados no código, e o padrão do endereço é **a máquina local** | Antes o padrão atendia todas as interfaces. A revisão decorre de o sistema não ter autenticação alguma: expor passa a exigir ato explícito de quem opera. O prefixo `ANALISADOR_` já é praticado em `ANALISADOR_UPLOAD_FOLDER` (`src/app.py`) | (a) valores fixos no código; (b) padrão aberto para a rede com variável para fechar; (c) flag de linha de comando | 🟢 |
| D-03 | A concorrência vem de `ANALISADOR_THREADS`, com padrão explícito declarado no código | A concorrência é declarada e calibrável por medição, sem reescrever o bloco | (a) deixar o padrão da biblioteca; (b) número fixo; (c) uma thread, serializando | 🟢 |
| D-04 | O servidor de desenvolvimento e o modo de depuração saem do bloco de entrada | Decisão do usuário: a aplicação passa a ter um único modo de execução. O console interativo de erro não pertence à operação | (a) manter o servidor de desenvolvimento atrás de variável de ambiente; (b) mantê-lo atrás de flag de linha de comando | 🟢 |
| D-05 | O import do servidor fica **dentro** do bloco de entrada, com tratamento de importação ausente | O módulo é importado pela suíte e pela instrumentação de paridade; importar no topo obrigaria o servidor instalado em quem só quer a aplicação como objeto. Dentro do bloco, a ausência se manifesta ao iniciar o servidor, que é quando a mensagem da `RF-07` faz sentido | (a) importar no topo do módulo | 🟢 |
| D-06 | O teste do bloco de entrada lê o módulo e afirma qual servidor é usado | Cumpre o princípio III pelo menor custo, sem abrir porta e sem flutuação. Falhava antes da mudança porque o bloco chamava o servidor de desenvolvimento | (a) teste de fumaça contra porta efêmera; (b) os dois, com a fumaça marcada como integração; (c) declarar o bloco fora de cobertura | 🟢 |
| D-07 | O arquivo de dependências perde o servidor que não opera no Windows e ganha o de produção | O arquivo é a fonte única de instalação, e listar servidor que não sobe na plataforma alvo quebra a promessa dele (`_reversa_sdd/dependencies.md#2` e `#5`) | (a) manter o inoperante para deploy em Linux; (b) manter com nota no `README.md` | 🟢 |
| D-08 | A mensagem de dependência ausente nomeia o pacote e o interpretador exato, e o processo termina sem subir nada | A `RF-07` pede diagnóstico legível no primeiro uso em máquina nova. Nomear o interpretador resolve a causa mais comum de "instalei e não achou" | (a) deixar a exceção crua de importação subir | 🟡 |
| D-09 | O `README.md` documenta o comando, o endereço de acesso e as três variáveis | A `RF-06` pede isso, e sem as variáveis documentadas quem opera não descobre como abrir ou fechar a escuta | (a) documentar só o comando | 🟡 |
| D-10 | **Nova.** A exclusividade é garantida por um socket criado pela própria aplicação, marcado com `SO_EXCLUSIVEADDRUSE` no Windows, ligado com `bind` e `listen`, e entregue ao servidor já pronto | Verificado na fonte instalada: o servidor aceita socket pronto (`Adjustments(sockets=...)`, padrão lista vazia) e, quando recebe um, **não faz bind nem listen**, porque o caminho de ligação só roda com `bind_socket=True`. Com o socket marcado para uso exclusivo, o sistema recusa a segunda instância durante toda a vida do processo, sem janela de corrida | (a) fazer `bind` exclusivo, fechar o socket e só então servir, que deixa uma janela entre fechar e servir; (b) arquivo de trava, que é a opção que o usuário **não** escolheu; (c) sondar a porta com uma conexão antes de servir, que sofre de corrida e não garante nada; (d) confiar na plataforma, que a medição de 2026-10-04 derrubou | 🟢 |
| D-11 | **Nova.** A recusa da segunda instância é uma mensagem legível na saída, com término de código diferente de zero, e a instância que já estava no ar não é afetada | A `RF-08` exige mensagem legível e código de saída, e a instância em execução não pode ser derrubada pela tentativa nova | (a) deixar a exceção de sistema operacional subir | 🟢 |
| D-12 | **Nova.** As dependências diretas passam a ter versão fixada com `==`, nas versões validadas no ambiente que executa a aplicação | A `RF-09` exige versão fixa, e a divergência já se materializou: `pandas 3.0.3` em um ambiente e `3.0.6` em outro, com a versão mais nova bloqueada pela política de aplicativo do sistema. As versões validadas são `Flask 3.1.3`, `ged4py 0.5.2`, `networkx 3.6.1`, `pandas 3.0.3`, `thefuzz 0.22.1` e `waitress 3.0.2` | (a) `pip freeze` completo no mesmo arquivo, que arrasta ferramentas de desenvolvimento para um arquivo de runtime; (b) arquivo de trava separado, que exigiria liberar caminho novo em `allowedPaths`, porque a política libera `requirements.txt` e não `requirements.*.txt` | 🟢 |
| D-13 | **Nova.** O teste por inspeção passa a cobrir também a presença da guarda de exclusividade no bloco de entrada | Estende a `RF-05` ao comportamento novo, mantendo o custo baixo e sem abrir porta | (a) teste funcional com dois processos na suíte, que é mais forte, mais lento e mais frágil; ele fica no `onboarding.md` | 🟢 |

## 4. Premissas

Nenhuma. Todas as lacunas da versão inicial foram fechadas na sessão de esclarecimento de `2026-10-03`, e a sessão de `2026-10-04` não deixou ponto em aberto: converteu a contradição medida em requisito novo e revisou dois valores. O documento chegou a esta rodada com zero marcadores `[DÚVIDA]`.

## 5. Delta arquitetural

| Componente | Arquivo de origem no legado | Tipo de mudança | Resumo |
|------------|------------------------------|-----------------|--------|
| Camada de rota (`app.py`) | `_reversa_sdd/inventory.md#3` e `#4` | regra-alterada | O bloco de entrada muda em três pontos: o padrão do endereço fecha, o socket passa a ser criado pela aplicação com uso exclusivo, e a recusa da segunda instância ganha mensagem própria |
| Configuração de execução | `_reversa_sdd/architecture.md#6` | contrato-alterado | Os mesmos três parâmetros, com o padrão do endereço revisto |
| Arquivo de dependências | `_reversa_sdd/dependencies.md#2` | contrato-alterado | Além da troca de servidor já entregue, cada linha passa a ter versão fixada |
| Documentação de execução (`README.md`) | fora do runtime, `_reversa_sdd/inventory.md#4` | regra-alterada | O padrão documentado passa a ser a máquina local, e o comportamento de recusa entra na documentação |
| Suíte de testes | `_reversa_sdd/inventory.md#6` | regra-alterada | O arquivo de teste existente ganha asserção sobre a guarda de exclusividade |

Nenhum componente do núcleo entra neste delta.

## 6. Delta no modelo de dados

- Resumo das mudanças: **nenhuma**. A feature continua sem tocar campo, entidade ou estrutura persistida, e o único estado envolvido, a árvore em memória de `core/gedcom_state.py`, não muda.
- Detalhe completo em: `_reversa_forward/004-servidor-waitress/data-delta.md`

## 7. Delta de contratos externos

**n/a.** A `RN-01` declara a superfície HTTP sem impacto, e nada nesta rodada a toca. O que muda é a operação: o endereço padrão, a política de instância única e as versões das dependências. O diretório `interfaces/` **não é criado**.

## 8. Plano de migração

n/a para dado. A migração é de operação, e muda em relação à rodada anterior:

1. Instalar as dependências a partir do arquivo, agora com versões fixas.
2. Nenhuma ação necessária para o endereço: o padrão fechado passa a valer sozinho, e quem precisa de acesso pela rede define `ANALISADOR_HOST` explicitamente.
3. Encerrar qualquer instância que esteja no ar antes de subir a versão nova, porque a partir dela a segunda execução passa a ser recusada em vez de coexistir.

## 9. Riscos e mitigações

| Risco | Impacto | Probabilidade | Mitigação |
|-------|---------|---------------|-----------|
| A guarda ser implementada com socket injetado mas **sem** `listen`, e o servidor não aceitar conexão alguma | alto | média | A `D-10` registra que o servidor não faz bind nem listen com socket pronto. O `onboarding.md` verifica uma requisição HTTP real, que é o que detecta esse erro |
| O padrão fechado quebrar o cenário de demonstrar pela rede, sem aviso a quem tenta | médio | média | A linha de inicialização informa o endereço em uso, e o procedimento de abertura está no `README.md` e no `onboarding.md` |
| A versão fixada impedir a instalação em outra plataforma, por ausência de pacote construído para ela | médio | baixa | As versões fixadas são as **validadas nesta máquina**, e o registro diz isso. Fixar para outra plataforma é decisão nova, e o arquivo é o lugar de mudá-la |
| A versão fixada não cobrir as dependências transitivas, e o conjunto ainda divergir | médio | média | Declarado na `D-12`: a reprodução do conjunto completo exigiria arquivo de trava, que a política atual não libera. O critério da `RF-09` deve ser lido como versões fixas das dependências **declaradas** |
| A guarda recusar a subida por causa de um processo alheio que ocupe a porta, e a mensagem sugerir que é o próprio analisador | baixo | média | A mensagem descreve a porta e o endereço em uso, e não afirma quem ocupa |
| Regressão silenciosa da superfície HTTP | alto | baixa | Suíte completa mais paridade diferencial em 100 por cento, medidas antes e depois |

## 10. Critério de pronto

- [ ] Todas as ações do `actions.md` marcadas `[X]`, incluindo as novas desta rodada
- [ ] Suíte no mesmo resultado da linha de base, mais os testes do bloco de entrada
- [ ] Paridade diferencial em 100 por cento nas 6 fixtures, remedida
- [ ] O padrão do endereço é a máquina local, e abrir para a rede exige a variável
- [ ] A segunda instância é recusada, com mensagem legível e código de saída diferente de zero, e a primeira continua atendendo
- [ ] O arquivo de dependências tem versão fixada em todas as linhas
- [ ] O `README.md` documenta o padrão fechado e o comportamento de recusa
- [ ] `regression-watch.md` atualizado com as condições novas
- [ ] `cross-check.md` sem CRITICAL nem HIGH, se for executado
- [ ] Re-extração reversa executada e sem regressão vermelha (recomendado, não obrigatório)

## 11. Histórico de alterações

| Data | Alteração | Autor |
|------|-----------|-------|
| 2026-10-03 | Versão inicial gerada por `/reversa-plan`, com as decisões `D-01` a `D-09` | reversa |
| 2026-10-04 | Segunda rodada, depois da execução real e da sessão de esclarecimento: `D-02` revista para o padrão fechado, e as decisões `D-10` a `D-13` acrescentadas. As decisões anteriores foram carregadas para este documento, e não descartadas | reversa |

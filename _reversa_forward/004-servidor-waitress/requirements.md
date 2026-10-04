# Requirements: servir a aplicação por um servidor de produção no Windows

> Identificador: `004-servidor-waitress`
> Data: `2026-10-03`
> Pasta da extração reversa: `_reversa_sdd/`
> Confidência: 🟢 CONFIRMADO, 🟡 INFERIDO, 🔴 LACUNA / DÚVIDA

## 1. Resumo executivo

Hoje a aplicação sobe pelo servidor de desenvolvimento do framework web, que avisa em toda execução que não deve ser usado em produção e não oferece suporte de operação. Esta feature entrega um modo de execução por um servidor de produção que implementa a interface padrão entre aplicação web e servidor (WSGI), compatível com Windows, eliminando o aviso, e mantendo intactas a superfície de requisições do protocolo de transferência de hipertexto (HTTP), as regras de negócio do núcleo e a suíte de testes. Quem opera e quem demonstra o analisador passa a subir a aplicação por um servidor próprio para isso, e quem mantém ganha um ponto de entrada declarado, testado e documentado.

## 2. Contexto a partir do legado

| Fonte | Trecho relevante | Confidência |
|-------|------------------|-------------|
| `_reversa_sdd/inventory.md#4` | O ponto de entrada é o bloco `if __name__ == "__main__"` do arquivo do aplicativo, que chama o servidor de desenvolvimento com o modo de depuração ligado | 🟢 |
| `_reversa_sdd/architecture.md#6` | Dívida registrada: o arquivo de dependências lista um servidor de produção que **não é usado no código**, e o deploy por WSGI é inferência da extração | 🟡 |
| `_reversa_sdd/dependencies.md#2` | O servidor listado nas dependências é de deploy, sem uso interno em nenhum ponto do código | 🟢 |
| `_reversa_sdd/migration/migration_strategy.md#1` | O legado não tem integração nem entrega contínuas (CI/CD), container ou fluxo automatizado; a presença de um servidor de produção no arquivo de dependências é inferência | 🟡 |
| `_reversa_sdd/addenda/003-renomear-pasta-app-para-src.md#Vigência` (vigente) | Corrige a leitura das fontes acima: a raiz de código é `src/`, o ponto de entrada é `src/app.py`, e o arquivo de dependências fica na raiz do repositório | 🟢 |
| `.reversa/principles.md#III` | Nenhuma mudança sem teste que a cubra, com o critério de falhar antes e passar depois | 🟢 |
| `.reversa/principles.md#II` | O comportamento observável é o que se preserva: aqui, a superfície HTTP e as mensagens de contrato | 🟢 |

## 3. Personas e cenários de uso

| Persona | Objetivo | Cenário-chave |
|---------|----------|---------------|
| Quem opera o analisador | Subir a aplicação em Windows sem aviso de servidor de desenvolvimento e sem depender de um servidor que não existe na plataforma | Executa o comando de inicialização documentado e vê a aplicação no ar, sem aviso |
| Quem demonstra o analisador | Mostrar o sistema funcionando para alguém em outra máquina da mesma rede | Define a variável de endereço para atender a rede e acessa a aplicação a partir de outro equipamento |
| Quem mantém o código | Trocar o modo de execução sem tocar em rota, regra de negócio ou mensagem | Roda a suíte e a paridade depois da mudança e vê o mesmo resultado |

## 4. Regras de negócio novas ou alteradas

1. **RN-01:** Nenhuma regra de negócio do núcleo é criada, alterada ou removida por esta feature. As mensagens de contrato permanecem literais, e a superfície HTTP continua com a rota raiz aceitando `GET` e `POST`, com os mesmos nomes de campo (`action`, `gedcom`, `gedcom_filename`, `matches_csv`, `root_name`, `person1_name`, `person2_name`). 🟢
   - Origem no legado: `_reversa_sdd/domain.md#4.1` e `#4.2` (contrato de mensagens do núcleo e da camada de rota)
   - Tipo: n/a, declaração explícita de não-impacto, exigida pelo princípio II
2. **RN-02:** A aplicação passa a ter um único modo de execução, o de produção. O servidor de desenvolvimento e o modo de depuração deixam de existir no bloco de entrada, porque o console interativo na resposta de erro e o reinício do processo a cada alteração de arquivo não pertencem à operação. 🟢
   - Origem no legado: `_reversa_sdd/inventory.md#4` (o modo de depuração é o estado atual do bloco de entrada)
   - Tipo: alterada
   - Decisão: sessão de esclarecimento de 2026-10-03, pergunta 4 da seção 9
3. **RN-03:** O endereço de escuta e a concorrência do servidor são lidos de variáveis de ambiente, com padrões declarados no código: o endereço atende **apenas a máquina local** por padrão, e o número de threads tem valor explícito. Nenhum dos dois depende de padrão de biblioteca, e nenhum exige editar código para mudar em campo. 🟢
   - Tipo: nova
   - Decisão: sessão de esclarecimento de 2026-10-03, perguntas 1 e 2 da seção 9, com o valor padrão do endereço **revisto** na sessão de 2026-10-04, pergunta 3
4. **RN-04:** A dependência do servidor de produção é registrada no arquivo de dependências da raiz do repositório, junto das demais, e a dependência que não opera na plataforma alvo é removida do mesmo arquivo. Uma dependência instalada apenas na máquina de quem executa não é dependência do projeto. 🟢
   - Origem no legado: `_reversa_sdd/dependencies.md#1` (o arquivo de dependências é único e fica na raiz) e `#5` (a dependência listada não tem uso interno em nenhum ponto do código)
   - Tipo: nova
   - Decisão: sessão de esclarecimento de 2026-10-03, pergunta 5 da seção 9
5. **RN-05:** A aplicação **não coexiste consigo mesma**. Se já houver uma instância atendendo no endereço e na porta configurados, a nova execução recusa subir, em vez de atender em paralelo. O motivo é que cada processo mantém o seu próprio estado global da árvore genealógica, e duas instâncias fariam requisições do mesmo operador serem atendidas por estados diferentes. 🟢
   - Origem no legado: `_reversa_sdd/architecture.md#3.3` (estruturas de runtime em processo único), e a mesma classe do defeito de exposição de estado já registrada no projeto
   - Tipo: nova
   - Decisão: sessão de esclarecimento de 2026-10-04, perguntas 1 e 2 da seção 9
   - Fundamento medido: a plataforma **não** impede a coexistência por conta própria. Duas instâncias do servidor escutam na mesma porta ao mesmo tempo, porque o servidor usa `SO_REUSEADDR` e a semântica do Windows é permissiva nesse ponto. A exclusividade passa a ser responsabilidade da aplicação
6. **RN-06:** As dependências do projeto têm **versão fixada** no arquivo da raiz. Duas instalações feitas a partir da mesma lista têm de produzir o mesmo conjunto de pacotes. 🟢
   - Tipo: nova
   - Decisão: sessão de esclarecimento de 2026-10-04, pergunta 4 da seção 9
   - Fundamento medido: com a lista sem versão, dois ambientes da mesma máquina ficaram com `pandas` em versões diferentes, `3.0.3` em um e `3.0.6` no outro, e a versão mais nova foi bloqueada pela política de aplicativo do sistema operacional

## 5. Requisitos Funcionais

| ID | Requisito | Prioridade | Critério de aceite | Confidência |
|----|-----------|------------|--------------------|-------------|
| RF-01 | O bloco de entrada do `src/app.py` inicia a aplicação por um servidor WSGI de produção, e não pelo servidor de desenvolvimento | Must | O comando documentado de inicialização sobe a aplicação e nenhum aviso de servidor de desenvolvimento é emitido na saída | 🟢 |
| RF-02 | O endereço de escuta e a porta são lidos de variáveis de ambiente, com padrões declarados no código, e o padrão do endereço atende **apenas a máquina local** | Must | Sem as variáveis definidas, a aplicação responde só no endereço local e **não** responde no endereço de rede da máquina; com as variáveis definidas, responde exatamente nos valores informados | 🟢 |
| RF-03 | A aplicação tem um único modo de execução: não existe servidor de desenvolvimento nem modo de depuração no bloco de entrada | Must | Nenhuma chamada do bloco de entrada liga depuração ou servidor de desenvolvimento, e um erro de aplicação não devolve console interativo | 🟢 |
| RF-04 | A dependência do servidor é declarada no arquivo de dependências da raiz, e a dependência que não opera na plataforma alvo é removida dele | Must | Uma instalação limpa a partir do arquivo sobe a aplicação, e o arquivo não lista mais a dependência inoperante | 🟢 |
| RF-05 | Existe teste automatizado que cobre a escolha do servidor por inspeção do módulo de entrada, sem abrir porta de rede | Must | A suíte executa o teste, ele falha antes da mudança e passa depois, e nenhuma porta é aberta durante a execução | 🟢 |
| RF-06 | A documentação de execução descreve o comando de inicialização e as variáveis de ambiente com seus valores padrão | Should | O `README.md` mostra o comando, informa o endereço de acesso e lista as variáveis que alteram o comportamento | 🟡 |
| RF-07 | A falha por dependência ausente nomeia a dependência e o comando de instalação | Should | Sem a dependência instalada, a saída nomeia o pacote e o comando, sem pilha de exceção crua | 🟡 |
| RF-08 | A inicialização recusa subir quando já existe uma instância atendendo no endereço e na porta configurados | Must | Com uma instância no ar, a segunda execução termina com mensagem legível sobre a porta já em uso e com código diferente de zero, a instância que já estava no ar continua atendendo, e o comportamento é coberto por teste automatizado | 🟢 |
| RF-09 | O arquivo de dependências da raiz lista cada dependência com a versão fixada | Must | Duas instalações feitas a partir do mesmo arquivo produzem o mesmo conjunto de pacotes, e nenhuma linha deixa a versão em aberto | 🟢 |

## 6. Requisitos Não Funcionais

| Tipo | Requisito | Evidência ou justificativa | Confidência |
|------|-----------|----------------------------|-------------|
| Portabilidade | O servidor escolhido roda em Windows sem compilação e sem dependência de chamada de sistema POSIX | O servidor listado hoje no arquivo de dependências exige uma chamada que não existe no Windows, o que torna a lista atual inoperante na plataforma alvo (`_reversa_sdd/architecture.md#6`) | 🟢 |
| Tecnologia | O servidor de produção adotado é o `waitress`, escolha declarada do usuário em 2026-10-03 | Decisão do usuário registrada nesta data. É a única linha deste documento que nomeia um produto, e ela existe porque a escolha foi declarada por quem pediu a feature, e não inferida pela extração | 🟢 |
| Segurança | O padrão **fecha** a aplicação na máquina local, e abrir para a rede passa a ser ação explícita de quem opera, porque o sistema não tem autenticação alguma | Decisão da sessão de esclarecimento de 2026-10-04, pergunta 3, que reverte o padrão anterior, o de atender todas as interfaces. A execução real de 2026-10-04 já havia sido feita em modo local, e o sistema não tem nenhuma forma de autenticar quem chega | 🟢 |
| Desempenho | A concorrência do servidor é declarada por variável de ambiente, com valor padrão explícito no código, e não herdada da biblioteca | Decisão da sessão de esclarecimento de 2026-10-03, pergunta 2. O servidor de desenvolvimento atual já atende em múltiplas threads, e o número definitivo deve ser calibrado por medição depois da entrega | 🟢 |
| Configuração | Todo parâmetro operacional novo (endereço de escuta, porta e concorrência) é variável de ambiente com padrão declarado, e nenhum deles exige editar código para mudar em campo | Decisão da sessão de esclarecimento de 2026-10-03, perguntas 1 e 2 | 🟢 |
| Observabilidade | A inicialização informa na saída o servidor, o host e a porta em uso | Sem isso, quem opera não distingue o modo de produção do modo de desenvolvimento | 🟡 |
| Conformidade | Nenhuma regra de negócio do núcleo muda, e a suíte e a paridade diferencial permanecem no mesmo resultado | Princípios II e III de `.reversa/principles.md` | 🟢 |
| Reprodutibilidade | As dependências têm versão fixada, e duas instalações feitas a partir da mesma lista produzem o mesmo conjunto de pacotes | Decisão da sessão de esclarecimento de 2026-10-04, pergunta 4. Com a lista sem versão, dois ambientes da mesma máquina ficaram com `pandas` em `3.0.3` e em `3.0.6`, e a versão mais nova foi bloqueada pela política de aplicativo do sistema operacional | 🟢 |

## 7. Critérios de Aceitação

```gherkin
Cenário: execução pelo servidor de produção
  Dado o ambiente Windows com as dependências do projeto instaladas
  Quando o operador executa o comando documentado de inicialização
  Então a aplicação responde na rota raiz
  E nenhum aviso de servidor de desenvolvimento é emitido na saída

Cenário: superfície HTTP preservada
  Dado a aplicação servida pelo servidor de produção, com uma árvore GEDCOM carregada
  Quando o operador envia um arquivo GEDCOM pela rota raiz com a ação de upload
  Então a resposta traz a mesma mensagem de sucesso do servidor de desenvolvimento
  E o nome do arquivo devolvido é o mesmo

Cenário: dependência ausente
  Dado um ambiente sem o servidor de produção instalado
  Quando o operador executa o comando de inicialização
  Então a falha nomeia a dependência ausente e o comando de instalação
  E nenhuma porta fica aberta

Cenário: abertura de escuta por variável de ambiente
  Dado a aplicação com o endereço padrão, que atende apenas a máquina local
  Quando o operador define a variável de ambiente do endereço para atender todas as interfaces e inicia a aplicação
  Então a aplicação responde no endereço de rede da máquina
  E responde também no endereço local

Cenário: segunda instância recusada
  Dado que uma instância já atende no endereço e na porta configurados
  Quando o operador inicia a aplicação outra vez
  Então a segunda execução termina com mensagem legível informando que a porta já está em uso
  E o processo termina com código diferente de zero
  E a instância que já estava no ar continua atendendo
```

## 8. Prioridade MoSCoW

| Item | MoSCoW | Justificativa |
|------|--------|---------------|
| RF-01 | Must | É o objetivo declarado da feature: eliminar o servidor de desenvolvimento e o aviso dele |
| RF-02 | Must | Sem endereço e porta declarados e configuráveis, o endereço de acesso volta a ser implícito e não auditável |
| RF-03 | Must | Um único modo de execução elimina o console interativo de erro, inaceitável em operação |
| RF-04 | Must | Dependência não registrada quebra a instalação limpa, e dependência que não opera na plataforma alvo quebra a promessa do arquivo |
| RF-05 | Must | Princípio III do projeto: nenhuma mudança de comportamento sem teste que a cubra |
| RF-06 | Should | A documentação de execução já existe e ficaria incorreta sem o ajuste |
| RF-07 | Should | Melhora o diagnóstico, e o modo de falha é provável na primeira execução em máquina nova |
| RF-08 | Must | A plataforma não impede a coexistência, e duas instâncias atendendo significam dois estados globais independentes para o mesmo operador |
| RF-09 | Must | Lista sem versão faz duas instalações divergirem, e a divergência já se materializou nesta máquina |
| RNF de portabilidade | Must | Um servidor que não roda na plataforma alvo não atende à feature |
| RNF de segurança | Must | O padrão fechado é o que impede exposição sem decisão, porque o sistema não tem autenticação alguma |
| RNF de configuração | Must | Parâmetro operacional que só muda editando código não é operável |
| RNF de reprodutibilidade | Must | Dependência sem versão fixada torna a entrega dependente da máquina de quem instala |
| RNF de observabilidade | Should | Não muda comportamento de negócio, mas muda a operação |

## 9. Esclarecimentos

### Sessão 2026-10-03

- **Q:** O endereço de escuta deve atender todas as interfaces de rede, ou só a máquina local?
  **R:** Variável de ambiente, com padrão `0.0.0.0`. O comportamento pedido é preservado, com acesso pela rede, e a restrição à máquina local passa a ser uma linha de configuração, sem alterar código.
  > **Revisado na sessão de 2026-10-04, pergunta 3:** o padrão passou a ser a máquina local. A resposta acima registra o que foi decidido naquele momento, e não o que vale hoje.
- **Q:** Quantas threads o servidor de produção deve abrir?
  **R:** Variável de ambiente, com padrão explícito declarado no código. A concorrência passa a ser declarada, e o valor é calibrável depois por medição, sem reescrita.
- **Q:** O que o teste do ponto de entrada deve cobrir?
  **R:** Inspeção do módulo. O teste lê o bloco de entrada e afirma que o servidor em uso é o de produção. Cumpre o princípio III pelo menor custo, sem abrir porta e sem flutuação na suíte.
- **Q:** O que acontece com o servidor de desenvolvimento?
  **R:** Sai de vez: a aplicação passa a ter um único modo de execução. O recarregador automático e o depurador do navegador deixam de existir, e a perda é aceita explicitamente.
- **Q:** O `gunicorn`, que está no `requirements.txt` e não roda no Windows, fica ou sai?
  **R:** Sai do arquivo. A extração já o registra como dependência inferida e sem uso interno, e ele exige uma chamada de sistema que não existe na plataforma alvo.

### Sessão 2026-10-04

Sessão aberta depois da primeira execução real da entrega, para tratar o que a medição contradisse.

- **Q:** O cenário de porta ocupada afirma uma falha que a medição mostrou que não acontece no Windows. O que fazer com ele?
  **R:** Reescrever o cenário para o comportamento real, e transformar a proteção em requisito novo. A medição mostrou que **duas instâncias do servidor escutam na mesma porta ao mesmo tempo**, porque o servidor usa `SO_REUSEADDR` e a semântica do Windows é permissiva nesse ponto. Não havia falha a reportar, e a exclusividade passa a ser responsabilidade da aplicação.
- **Q:** O projeto deve impedir duas instâncias simultâneas?
  **R:** Sim, com **exclusividade de porta na inicialização**. A aplicação recusa subir quando já há instância no endereço e na porta configurados, com mensagem legível e código de saída diferente de zero. O mecanismo é decisão do plano, e fica o alerta: um `bind` comum pode não bastar no Windows, porque é justamente o `SO_REUSEADDR` do servidor que permite a coexistência hoje.
- **Q:** O padrão do endereço de escuta continua atendendo todas as interfaces de rede?
  **R:** Não. O padrão passa a ser a **máquina local**, e abrir para a rede vira ação explícita de quem opera. O motivo é o peso da decisão: o sistema não tem autenticação alguma, e a execução real de 2026-10-04 já havia sido feita em modo local.
- **Q:** As dependências devem passar a ter versão fixada?
  **R:** Sim, **todas**. Com a lista sem versão, dois ambientes da mesma máquina divergiram, `pandas 3.0.3` contra `3.0.6`, e a versão mais nova foi bloqueada pela política de aplicativo do sistema operacional.

## 10. Lacunas

- n/a. As três lacunas da versão inicial foram resolvidas na sessão de 2026-10-03, e a sessão de 2026-10-04 não deixou ponto em aberto: ela converteu a contradição medida em requisito novo e revisou dois valores.

## 11. Histórico de alterações

| Data | Alteração | Autor |
|------|-----------|-------|
| 2026-10-03 | Versão inicial gerada por `/reversa-requirements` | reversa |
| 2026-10-03 | Sessão de esclarecimento com cinco perguntas: três lacunas fechadas e duas ambiguidades de escopo resolvidas | reversa |
| 2026-10-04 | Sessão de esclarecimento com quatro perguntas, aberta após a primeira execução real: cenário de porta ocupada reescrito para o comportamento medido, exclusividade de porta e versões fixadas acrescentadas como requisito, e o padrão do endereço revisto para a máquina local | reversa |

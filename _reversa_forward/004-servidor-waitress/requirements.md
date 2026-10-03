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
| Quem demonstra o analisador | Mostrar o sistema funcionando para alguém em outra máquina da mesma rede | Acessa a aplicação a partir de outro equipamento |
| Quem mantém o código | Trocar o modo de execução sem tocar em rota, regra de negócio ou mensagem | Roda a suíte e a paridade depois da mudança e vê o mesmo resultado |

## 4. Regras de negócio novas ou alteradas

1. **RN-01:** Nenhuma regra de negócio do núcleo é criada, alterada ou removida por esta feature. As mensagens de contrato permanecem literais, e a superfície HTTP continua com a rota raiz aceitando `GET` e `POST`, com os mesmos nomes de campo (`action`, `gedcom`, `gedcom_filename`, `matches_csv`, `root_name`, `person1_name`, `person2_name`). 🟢
   - Origem no legado: `_reversa_sdd/domain.md#4.1` e `#4.2` (contrato de mensagens do núcleo e da camada de rota)
   - Tipo: n/a, declaração explícita de não-impacto, exigida pelo princípio II
2. **RN-02:** O modo de depuração do framework web não é habilitado no modo de produção. Ele expõe um console interativo na resposta de erro e reinicia o processo a cada alteração de arquivo, comportamentos que não pertencem à operação. 🟢
   - Origem no legado: `_reversa_sdd/inventory.md#4` (o modo de depuração é o estado atual do bloco de entrada)
   - Tipo: alterada
3. **RN-03:** O host e a porta de escuta passam a ser declarados de forma explícita no bloco de entrada, e não herdados do padrão do framework web. 🟢
   - Tipo: nova
4. **RN-04:** A dependência do servidor é registrada no arquivo de dependências da raiz do repositório, junto das demais. Uma dependência instalada apenas na máquina de quem executa não é dependência do projeto. 🟢
   - Origem no legado: `_reversa_sdd/dependencies.md#1` (o arquivo de dependências é único e fica na raiz)
   - Tipo: nova

## 5. Requisitos Funcionais

| ID | Requisito | Prioridade | Critério de aceite | Confidência |
|----|-----------|------------|--------------------|-------------|
| RF-01 | O bloco de entrada do `src/app.py` inicia a aplicação por um servidor WSGI de produção, e não pelo servidor de desenvolvimento | Must | O comando documentado de inicialização sobe a aplicação e nenhum aviso de servidor de desenvolvimento é emitido na saída | 🟢 |
| RF-02 | O host e a porta de escuta são valores explícitos no bloco de entrada | Must | Os dois valores aparecem no código do bloco de entrada, e não dependem de padrão de biblioteca | 🟢 |
| RF-03 | O modo de depuração não é habilitado no modo de produção | Must | Nenhuma chamada do bloco de entrada liga depuração, e um erro de aplicação não devolve console interativo | 🟢 |
| RF-04 | A dependência do servidor é declarada no arquivo de dependências da raiz | Must | A dependência aparece no arquivo, e uma instalação limpa a partir dele sobe a aplicação | 🟢 |
| RF-05 | Existe teste automatizado que cobre a escolha do servidor sem abrir porta de rede | Must | A suíte executa o teste, ele falha antes da mudança e passa depois, e nenhuma porta é aberta durante a execução | 🟢 |
| RF-06 | A documentação de execução descreve o comando de inicialização e os valores de host e porta | Should | O `README.md` mostra o comando e informa o endereço de acesso | 🟡 |
| RF-07 | A falha por dependência ausente nomeia a dependência e o comando de instalação | Should | Sem a dependência instalada, a saída nomeia o pacote e o comando, sem pilha de exceção crua | 🟡 |

## 6. Requisitos Não Funcionais

| Tipo | Requisito | Evidência ou justificativa | Confidência |
|------|-----------|----------------------------|-------------|
| Portabilidade | O servidor escolhido roda em Windows sem compilação e sem dependência de chamada de sistema POSIX | O servidor listado hoje no arquivo de dependências exige uma chamada que não existe no Windows, o que torna a lista atual inoperante na plataforma alvo (`_reversa_sdd/architecture.md#6`) | 🟢 |
| Tecnologia | O servidor de produção adotado é o `waitress`, escolha declarada do usuário em 2026-10-03 | Decisão do usuário registrada nesta data. É a única linha deste documento que nomeia um produto, e ela existe porque a escolha foi declarada por quem pediu a feature, e não inferida pela extração | 🟢 |
| Segurança | A exposição de rede decorrente do endereço de escuta é decisão explícita do usuário, não valor herdado por padrão | O projeto adota endereço de máquina local na própria instrumentação (`_reversa_sdd/parity/_golden_capture.py`), e o endereço pedido atende todas as interfaces. Ver a lacuna 1 na seção 10 | 🔴 |
| Desempenho | A concorrência do servidor de produção é declarada, e não deixada no valor padrão da biblioteca | O servidor de desenvolvimento atual já atende em múltiplas threads. Ver a lacuna 2 na seção 10 | 🔴 |
| Observabilidade | A inicialização informa na saída o servidor, o host e a porta em uso | Sem isso, quem opera não distingue o modo de produção do modo de desenvolvimento | 🟡 |
| Conformidade | Nenhuma regra de negócio do núcleo muda, e a suíte e a paridade diferencial permanecem no mesmo resultado | Princípios II e III de `.reversa/principles.md` | 🟢 |

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

Cenário: porta em uso
  Dado que a porta configurada já está ocupada por outro processo
  Quando o operador inicia a aplicação
  Então a falha é reportada de forma legível
  E o processo termina com código diferente de zero
```

## 8. Prioridade MoSCoW

| Item | MoSCoW | Justificativa |
|------|--------|---------------|
| RF-01 | Must | É o objetivo declarado da feature: eliminar o servidor de desenvolvimento e o aviso dele |
| RF-02 | Must | Sem host e porta explícitos, o endereço de acesso volta a ser implícito e não auditável |
| RF-03 | Must | O modo de depuração expõe console interativo, o que é inaceitável em operação |
| RF-04 | Must | Dependência não registrada quebra a instalação limpa, e o projeto tem um único arquivo de dependências |
| RF-05 | Must | Princípio III do projeto: nenhuma mudança de comportamento sem teste que a cubra |
| RF-06 | Should | A documentação de execução já existe e ficaria incorreta sem o ajuste |
| RF-07 | Should | Melhora o diagnóstico, e o modo de falha é provável na primeira execução em máquina nova |
| RNF de portabilidade | Must | Um servidor que não roda na plataforma alvo não atende à feature |
| RNF de segurança | Must | A exposição de rede é a decisão de maior consequência da feature |
| RNF de observabilidade | Should | Não muda comportamento de negócio, mas muda a operação |

## 9. Esclarecimentos

> Nenhuma sessão de dúvidas registrada ainda. Rode `/reversa-clarify` quando houver `[DÚVIDA]` pendente.

## 10. Lacunas

- 🔴 [DÚVIDA] **Endereço de escuta.** O pedido do usuário é atender todas as interfaces de rede (`0.0.0.0`), e o projeto usa endereço de máquina local na instrumentação. Atender todas as interfaces torna a aplicação alcançável por qualquer equipamento da rede onde a máquina estiver, sem autenticação alguma no sistema. Precisa de confirmação explícita, com a consequência declarada.
- 🔴 [DÚVIDA] **Concorrência.** O servidor de desenvolvimento atual atende em múltiplas threads (uma por requisição), e o servidor de produção tem um número fixo de threads. O estado da árvore genealógica é global no processo, e cada requisição o substitui. Não há teste que exercite duas requisições simultâneas. Definir o número de threads sem essa medição é escolher no escuro.
- 🔴 [DÚVIDA] **Cobertura de teste do ponto de entrada.** O princípio III exige teste que cubra a mudança, e o bloco de entrada nunca teve teste, porque subir um servidor real numa suíte é caro e frágil. É preciso decidir o que o teste cobre: a escolha do servidor por inspeção do módulo, um teste de fumaça contra um servidor efêmero em porta livre, ou a declaração de que o bloco fica fora da cobertura com justificativa registrada.

## 11. Histórico de alterações

| Data | Alteração | Autor |
|------|-----------|-------|
| 2026-10-03 | Versão inicial gerada por `/reversa-requirements` | reversa |

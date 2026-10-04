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

## Histórico de re-extrações

| Data | Extração | Veredito | Observação |
|------|----------|----------|------------|

## Arquivadas

Nenhuma.

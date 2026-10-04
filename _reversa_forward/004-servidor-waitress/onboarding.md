# Onboarding: testar a feature do servidor de produção

> Identificador: `004-servidor-waitress`
> Data: `2026-10-03`
> Requirements: `_reversa_forward/004-servidor-waitress/requirements.md`
> Roadmap: `_reversa_forward/004-servidor-waitress/roadmap.md`

Passo a passo para uma pessoa que nunca viu o projeto testar a entrega. Os comandos são de terminal do Windows, a partir da raiz do repositório.

## 1. Pré-requisitos

- Python 3.14 disponível. Neste projeto o comando é `py -3.14`.
- Dependências do projeto instaladas. Se ainda não estiverem:

```powershell
py -3.14 -m pip install -r requirements.txt
```

- Confirmar que o interpretador que executa a aplicação é o mesmo onde a dependência foi instalada. O projeto tem mais de um interpretador na máquina, e instalar em um para rodar em outro é a causa mais comum de "instalei e não achou":

```powershell
py -3.14 -c "import sys; print(sys.executable)"
```

## 2. Conferir as dependências do servidor de produção

A instalação vem do `requirements.txt`, que fixa a versão de cada dependência com `==`. Não instale o servidor de produção à parte: uma instalação avulsa pode trazer uma versão diferente da validada, que é exatamente o que a versão fixada existe para impedir.

```powershell
py -3.14 -m pip install -r requirements.txt
py -3.14 -c "import importlib.metadata as m; print('waitress', m.version('waitress'))"
```

O que se espera: código de saída 0 na primeira linha, e `waitress 3.0.2` na segunda.

Optei pela leitura dos metadados da distribuição, e não por um atributo de versão do próprio pacote: nem toda biblioteca expõe esse atributo, e um comando de verificação que falha por isso confunde quem está testando.

Para conferir de uma vez que o conjunto instalado corresponde ao declarado:

```powershell
py -3.14 -c "import importlib.metadata as m, pathlib; d = dict(l.split('==') for l in pathlib.Path('requirements.txt').read_text().splitlines() if l.strip()); print('divergentes:', [(k, v, m.version(k)) for k, v in d.items() if m.version(k) != v])"
```

O que se espera: `divergentes: []`. As dependências **transitivas** não entram nesta conferência, e o motivo está na decisão `D-12` do `roadmap.md`.

## 3. Iniciar a aplicação

```powershell
py -3.14 src/app.py
```

O que se espera ver:

1. Nenhuma linha de aviso sobre servidor de desenvolvimento.
2. Uma linha informando o servidor, o endereço e a porta em uso.
3. O processo permanece em primeiro plano, atendendo requisições.

Se aparecer `ModuleNotFoundError` com o nome do pacote do servidor, a dependência não está no interpretador que está executando o arquivo. Volte ao passo 1 e confira o `sys.executable` dos dois comandos.

## 4. Acessar pela máquina local

Abra `http://127.0.0.1:5000/` no navegador. A tela inicial de upload deve aparecer.

## 5. Abrir a escuta para a rede

O padrão da aplicação atende **apenas a máquina local**. Para que outro equipamento alcance o analisador, quem opera precisa abrir a escuta explicitamente:

```powershell
$env:ANALISADOR_HOST = "0.0.0.0"
py -3.14 src/app.py
```

1. Descubra o endereço de rede da máquina onde a aplicação está rodando:

```powershell
ipconfig | Select-String "IPv4"
```

2. Em outro equipamento na mesma rede, abra `http://<endereço-ipv4>:5000/`.

**Aviso que precisa ser lido antes deste passo:** o sistema **não tem autenticação alguma**. Qualquer equipamento que alcance a porta vê a aplicação e pode enviar arquivos. Faça este teste em rede confiável, apague os arquivos enviados depois, e encerre a aplicação quando terminar.

## 6. Conferir que o padrão fecha a escuta

Sem definir variável alguma:

```powershell
py -3.14 src/app.py
```

Verificação: o passo 4 continua funcionando, e o passo 5 deixa de funcionar. Esse é o comportamento pretendido, e não um defeito.

## 7. Ajustar a concorrência

```powershell
$env:ANALISADOR_THREADS = "8"
py -3.14 src/app.py
```

Sem a variável, vale o padrão declarado no código.

## 8. Rodar a suíte e a paridade

```powershell
py -3.14 -m pytest -q
py -3.14 _reversa_sdd/parity/harness.py
```

O que se espera:

- Suíte no mesmo resultado da linha de base: **125 aprovados e 15 erros de ambiente**. Os 15 erros são os mesmos de antes, todos em `test_upload_seguranca.py`, causados por permissão de diretório temporário no sandbox, e não regressão.
- Paridade: **100 por cento nas 6 fixtures, zero divergência**.

Apontar o diretório temporário do pytest para dentro do projeto (`--basetemp`) **não** resolve neste sandbox, e o registro fica aqui para ninguém perder tempo com a tentativa: o diretório é criado, mas o próprio Windows nega enumerá-lo, e os 15 erros continuam.

## 9. Testar o caminho negativo da dependência ausente

Em um interpretador sem a dependência instalada, iniciar a aplicação deve produzir uma mensagem que nomeia o pacote, o comando de instalação e o interpretador exato, com código de saída diferente de zero e sem abrir porta.

Para reproduzir sem desinstalar nada do ambiente de trabalho, use um ambiente virtual descartável. **A linha de desinstalação é obrigatória**: o arquivo de dependências inclui o servidor de produção, então uma instalação a partir dele deixaria o ambiente completo, e o passo não testaria nada.

```powershell
py -3.14 -m venv .tmp-sem-waitress
.\.tmp-sem-waitress\Scripts\python -m pip install -r requirements.txt
.\.tmp-sem-waitress\Scripts\python -m pip uninstall -y waitress
.\.tmp-sem-waitress\Scripts\python src/app.py
"codigo de saida: $LASTEXITCODE"
Remove-Item -Recurse -Force .tmp-sem-waitress
```

O que se espera: a mensagem abaixo, e `codigo de saida: 1`.

```text
Servidor de producao ausente neste interpretador: o pacote waitress nao esta instalado. Instale a partir do arquivo de dependencias, com: <caminho do python> -m pip install -r requirements.txt
```

> **Este passo não foi executado em 2026-10-04**, e a razão é de ambiente: o `pip` de um ambiente virtual novo precisa desempacotar em diretório temporário, e o sandbox nega esse diretório. A verificação equivalente foi feita na mesma data, contra o bloco de entrada atual, escondendo o módulo do servidor do interpretador com `sys.modules`: a saída foi a mensagem acima, com código de saída 1 e sem pilha de exceção. A execução por ambiente virtual continua sendo o procedimento recomendado, por ser o que testa a instalação de verdade.

## 10. Testar a recusa da segunda instância

1. Suba a aplicação em uma janela.
2. Em outra janela, suba de novo, sem encerrar a primeira.
3. Confira o código de saída da segunda execução, que é diferente de zero.
4. Abra a página novamente, para confirmar que **a primeira continua atendendo**.

No PowerShell, o código de saída da segunda execução aparece em `$LASTEXITCODE` logo depois dela. O que se espera é a mensagem abaixo, e `codigo de saida: 1`:

```text
Recusando subir: 127.0.0.1:5000 ja esta em uso (...). Encerre o processo que ja esta no ar, ou suba esta instancia em outra porta com ANALISADOR_PORT.
```

O trecho entre parênteses é o diagnóstico do sistema operacional, no idioma dele, e é por isso que ele não aparece transcrito aqui.

Mudando `ANALISADOR_PORT` para uma porta livre, a segunda instância sobe normalmente. É o caminho de quem precisa de duas execuções ao mesmo tempo.

### Por que este passo existe

Antes desta rodada, as duas instâncias coexistiam, porque o servidor pede `SO_REUSEADDR` e a semântica do Windows é permissiva nesse ponto. A recusa passou a ser responsabilidade da aplicação, e é ela que este passo verifica.

### O que foi medido em 2026-10-04

Execução real, em porta livre, com o código desta rodada:

- A primeira instância subiu e atendeu: `HTTP 200` e cabeçalho `Server: waitress`.
- A segunda terminou com código de saída 1 e a mensagem acima, sem pilha de exceção crua na saída.
- A primeira continuou atendendo depois da tentativa.

O experimento foi repetido com a instância que já estava no ar iniciada pelo **caminho da versão anterior**, em que o servidor cria o próprio socket e pede `SO_REUSEADDR` (confirmado com `getsockopt`, valor 1): a versão nova também recusou a subida, com código 1, e a instância antiga seguiu atendendo. É este resultado que torna honesta a instrução de encerrar a instância no ar antes de subir a versão nova.

Também foi medido o ramo de diagnóstico errado: com `ANALISADOR_HOST` apontando para um endereço que não pertence à máquina, a recusa sai com a mensagem de "não foi possível escutar" e a orientação de conferir o endereço, e **não** com a de porta em uso. Os dois casos chegam com códigos de erro diferentes, e a mensagem acompanha.

### Correção sobre o `listen`

A versão anterior deste documento afirmava que "o servidor não faz `listen` quando recebe um socket". **A leitura da fonte instalada mostra que a afirmação é falsa.** Com socket pronto, o servidor pula o `bind` (`waitress/server.py`, `bind_socket=False`), mas a aceitação de conexões chama `socket.listen(self.adj.backlog)` logo depois, na função `accept_connections`. A aplicação continua fazendo `bind` e `listen` por conta própria, e continua sendo isso que fecha a janela entre ligar e servir, mas o motivo correto é garantir que o socket já esteja em escuta quando o servidor assumir, e não suprir uma omissão dele.

O passo 4, que faz uma requisição de verdade, é o que detecta um socket ligado sem escuta: o sintoma não seria exceção, seria a aplicação muda.

## 11. Checklist de aceite

- [ ] A suíte roda sem aviso de servidor de desenvolvimento
- [ ] A aplicação responde na máquina local
- [ ] Sem variável definida, a aplicação **não** responde no endereço de rede da máquina
- [ ] Definindo `ANALISADOR_HOST` para atender todas as interfaces, outro equipamento alcança a aplicação
- [ ] A variável de concorrência é aceita
- [ ] A suíte mantém o resultado da linha de base, mais os testes do bloco de entrada
- [ ] A paridade diferencial continua em 100 por cento
- [ ] Dependência ausente produz mensagem legível, sem porta aberta
- [ ] A segunda instância é recusada, com mensagem legível e código diferente de zero, e a primeira continua atendendo
- [ ] O arquivo de dependências tem versão fixada em todas as linhas

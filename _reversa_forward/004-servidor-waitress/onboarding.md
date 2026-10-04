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

## 2. Instalar a dependência do servidor de produção

```powershell
py -3.14 -m pip install waitress
```

Verificação:

```powershell
py -3.14 -c "import importlib.metadata as m; print('waitress', m.version('waitress'))"
```

Optei pela leitura dos metadados da distribuição, e não por um atributo de versão do próprio pacote: nem toda biblioteca expõe esse atributo, e um comando de verificação que falha por isso confunde quem está testando.

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

- Suíte no mesmo resultado da linha de base: **121 aprovados e 15 erros de ambiente**. Os 15 erros são de ambiente (permissão de diretório temporário no sandbox), e não regressão.
- Paridade: **100 por cento nas 6 fixtures, zero divergência**.

## 9. Testar o caminho negativo da dependência ausente

Em um interpretador sem a dependência instalada, iniciar a aplicação deve produzir uma mensagem que nomeia o pacote e o comando de instalação, e o processo não deve abrir porta.

Para reproduzir sem desinstalar nada do ambiente de trabalho, use um ambiente virtual descartável:

```powershell
py -3.14 -m venv .tmp-sem-waitress
.\.tmp-sem-waitress\Scripts\python -m pip install -r requirements.txt
.\.tmp-sem-waitress\Scripts\python src/app.py
Remove-Item -Recurse -Force .tmp-sem-waitress
```

## 10. Testar a recusa da segunda instância

1. Suba a aplicação em uma janela.
2. Em outra janela, suba de novo, sem encerrar a primeira.

O que se espera: a segunda execução termina com mensagem legível informando que o endereço e a porta já estão em uso, e com código de saída diferente de zero. **A primeira continua atendendo**, e a verificação é abrir a página novamente depois da segunda tentativa.

Por que este passo existe: antes desta rodada, as duas instâncias coexistiam, porque o servidor usa `SO_REUSEADDR` e a semântica do Windows é permissiva nesse ponto. A recusa passou a ser responsabilidade da aplicação, e é ela que este passo verifica.

Atenção a um detalhe de implementação que este passo também cobre: a aplicação cria o socket de escuta e o entrega pronto ao servidor, e é ela que precisa fazer o `listen`, porque o servidor não o faz quando recebe um socket. Um socket ligado sem `listen` não aceita conexão alguma, e o sintoma não seria uma exceção: seria a aplicação muda. Por isso o passo 4, que faz uma requisição de verdade, é parte desta verificação.

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

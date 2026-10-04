# Legacy Impact: servir a aplicação por um servidor de produção no Windows

> Identificador da feature: `004-servidor-waitress`
> Data: `2026-10-03`
> Requirements: `_reversa_forward/004-servidor-waitress/requirements.md`
> Roadmap: `_reversa_forward/004-servidor-waitress/roadmap.md`

## 1. Arquivos afetados

| Arquivo afetado | Componente | Tipo | Severidade | Justificativa |
|---|---|---|---|---|
| `src/app.py` | Camada de rota (`_reversa_sdd/inventory.md#3` e `#4`) | `regra-alterada` | **HIGH** | O bloco de entrada troca o servidor de desenvolvimento pelo de produção, e o endereço padrão passa a atender todas as interfaces de rede. É a mudança de maior consequência da feature: muda como o serviço sobe e quem alcança o serviço |
| `tests/test_servidor_producao.py` | Suíte de testes (`_reversa_sdd/inventory.md#6`) | `componente-novo` | LOW | Teste novo, por inspeção do bloco de entrada. Não altera comportamento de produção |
| `README.md` | Documentação de execução (fora do runtime) | `regra-alterada` | LOW | Comando, endereço de acesso, tabela de variáveis e aviso de ausência de autenticação |
| `requirements.txt` | Dependências diretas (`_reversa_sdd/dependencies.md#2`) | **pendente, não aplicado** | MEDIUM | A troca de servidor está planejada e **não foi executada**: o caminho está fora dos liberados pela política, e o gate do coding recusou a escrita |

## 2. Diff conceitual por componente

### `src/app.py`, camada de rota

O módulo tinha 166 linhas e um bloco de entrada de duas linhas:

```python
if __name__ == "__main__":
    app.run(debug=True)
```

Agora o bloco lê três valores do ambiente com padrões declarados (`ANALISADOR_HOST` com `0.0.0.0`, `ANALISADOR_PORT` com `5000` e `ANALISADOR_THREADS` com `4`), importa o servidor de produção dentro do próprio bloco com tratamento de importação ausente, emite uma linha informando servidor, endereço e porta, e entrega a aplicação ao servidor de produção.

**O que muda para quem observa:**

1. Nenhum aviso de servidor de desenvolvimento é emitido.
2. O endereço padrão passa de `127.0.0.1` para `0.0.0.0`, então a aplicação responde a partir de outro equipamento da rede. Isso é intencional, decidido pelo usuário, e está declarado como risco alto no roadmap.
3. Não existe mais modo de depuração: sem console interativo de erro e sem reinício automático a cada alteração de arquivo.

**O que não muda:** nenhuma rota, nenhum nome de campo, nenhuma mensagem de contrato, nenhuma regra de negócio do núcleo. O módulo ganhou uma linha de importação de `sys` no topo, usada apenas na mensagem de dependência ausente, que nomeia o interpretador exato.

### `tests/test_servidor_producao.py`, suíte

Arquivo novo, com três testes que leem `src/app.py` por AST e afirmam o comportamento do bloco de entrada: que ele inicia o servidor de produção e não o de desenvolvimento, que declara as três variáveis de ambiente, e que não liga depuração.

O teste **não importa** o módulo, e por isso não exige o servidor de produção instalado nem abre porta. Antes da mudança ele falhava nas três asserções; depois, passa nas três. É a evidência do princípio III.

### `README.md`, documentação de execução

O passo de execução passou a dizer que o ponto de entrada sobe a aplicação por um servidor WSGI de produção, e o endereço de acesso deixou de ser apenas `127.0.0.1`. Foi acrescentada uma seção com as três variáveis, seus padrões e um exemplo de restrição de escuta, além do aviso de que a aplicação não tem autenticação alguma.

## 3. O que ficou pendente, e por quê

A `T001` (registrar o servidor de produção em `requirements.txt` e remover o que não importa no Windows) e a `T002` (instalar a partir do arquivo atualizado) **não foram executadas**. O caminho `requirements.txt` não casa com nenhum glob de `allowedPaths` em `.reversa/reversa-config.json`, e a política do Reversa manda recusar a escrita fora dos caminhos liberados.

Consequência declarada: uma instalação limpa a partir do arquivo de dependências **não terá o servidor de produção**. A aplicação sobe até o bloco de entrada e termina com mensagem que nomeia o pacote e o interpretador exato, sem abrir porta. Esse comportamento foi verificado e é o da `T010`.

A `T011` (porta ocupada) **não foi verificada**: a sandbox nega o diretório temporário que o `pip` usa para desempacotar, então o servidor não pôde ser instalado no ambiente desta execução. Há também uma lacuna substantiva declarada: nenhuma ação do plano implementa mensagem legível para porta ocupada, e o cenário correspondente do `requirements.md` exige isso.

## 4. Preservadas

Regras confirmadas de `_reversa_sdd/domain.md` que continuam intactas, e a feature não as toca:

| Regra | Fonte | Como foi conferido |
|---|---|---|
| Relação prevista por faixa de cM, com contrato de lista | `_reversa_sdd/domain.md#2.1` | Paridade diferencial em 100 por cento, com os 40 valores de cM sondados |
| Conexão genealógica direta e indireta por afinidade | `_reversa_sdd/domain.md#2.2` | Paridade em 100 por cento, com a amostra de pares de caminho |
| Matching difuso de nomes com filtro anti-falso-positivo | `_reversa_sdd/domain.md#2.3` | Paridade em 100 por cento nos probes de nome |
| Limites de busca (profundidade e hops) | `_reversa_sdd/domain.md#2.4` | Paridade em 100 por cento |
| Contrato de mensagens ao usuário, núcleo e camada de rota | `_reversa_sdd/domain.md#4.1` e `#4.2` | Suíte completa, com os mesmos 118 testes aprovados da linha de base |
| Fluxo de decisão por `action` | `_reversa_sdd/domain.md#3` | Suíte completa; nenhuma rota foi tocada |

## 5. Modificadas

**Nenhuma regra de negócio do domínio foi alterada, removida ou criada.** É a declaração de não-impacto da `RN-01`, e ela é sustentada pela suíte e pela paridade, e não apenas afirmada.

O que mudou está fora do domínio, no contrato de operação da aplicação:

| Item | Antes | Depois |
|---|---|---|
| Servidor que atende | servidor de desenvolvimento do framework web | servidor WSGI de produção |
| Modo de depuração | ligado | não existe |
| Endereço de escuta padrão | apenas a máquina local | todas as interfaces de rede |
| Porta | padrão do framework, 5000 | declarada no código, 5000, com variável de ambiente |
| Concorrência | uma thread por requisição | número declarado, com variável de ambiente |
| Registro da dependência de servidor | servidor que não importa no Windows, sem uso no código | **pendente**: bloqueado pela política de edição |

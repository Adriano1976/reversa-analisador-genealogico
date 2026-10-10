# User Stories — Fluxo `upload-gedcom`

> Re-extração de **2026-10-10** (nível **Completo**). Substitui a versão de 2026-10-05, que descrevia a árvore como **estado global reescrito** e o motivo da recusa **dentro da mensagem**.
> Persona única do sistema. Fontes: `upload-gedcom/requirements.md`, `upload-gedcom/design.md`, `upload-gedcom/contracts.md`, `domain.md` §3.5, `permissions.md`, `adrs/` 24, 30, 31, 32
> Escala de confiança: 🟢 CONFIRMADO | 🟡 INFERIDO | 🔴 LACUNA

---

## Persona

**Genealogista Genético.** Trabalha sozinho, na própria máquina. Tem a árvore da família em um arquivo GEDCOM exportado de um site de genealogia e a lista de matches de DNA em CSV exportado do GEDmatch (ou similar). **Não há login**: a aplicação não sabe quem ele é. 🟢

## História principal

> **Como** genealogista genético, **quero** carregar minha árvore GEDCOM no analisador **para que** as outras duas análises (busca de caminho e cruzamento com DNA) tenham sobre o que operar.

**Valor de negócio:** é a porta de entrada do sistema. Sem upload bem-sucedido, **nada** mais funciona. 🟢

**Regras que o usuário não vê, mas recebe:**

| Regra | Efeito percebido |
| --- | --- |
| A validação é de **conteúdo** (`0 HEAD`), não de extensão | Um GEDCOM legítimo sem `.ged` é aceito — ele não é recusado por detalhe de nome 🟢 |
| O arquivo é gravado sob **chave derivada do conteúdo** | Reenviar a mesma árvore não duplica nem sobrescreve nada 🟢 |
| A **extensão original é preservada** | Um CSV enviado por engano continua `.csv`, e não é renomeado para `.ged` 🟢 |
| O teto de corpo é de **16 MB**, aplicado antes de ler | Um arquivo gigante é recusado **sem** consumir disco 🟢 |
| A continuidade é uma **referência de arquivo**, não uma sessão | Ele pode continuar a análise após recarregar a página, porque o valor viaja no formulário 🟢 |
| O **reenvio do mesmo nome com conteúdo novo substitui a versão anterior**, sem apagar nada | Ele mantém **uma** linha na lista, e a versão antiga continua guardada em `_aposentados/` 🟢 |

## Histórias secundárias

### US-U-02 — Recusa clara, sem jargão técnico

> **Como** genealogista, **quero** ser informado de que meu arquivo foi recusado **para que** eu saiba que o problema é o arquivo — sem precisar ler o motivo técnico do validador.

#### Critérios de aceite

```gherkin
Dado que enviei um arquivo que não é GEDCOM
Quando o upload é processado
Então a tela diz "Arquivo não reconhecido como GEDCOM. Favor, enviar o arquivo correto."
E nenhum arquivo é gravado em disco
E o motivo técnico continua acessível a quem depura, dentro da exceção

Dado que enviei um arquivo vazio
Quando o upload é processado
Então a tela diz a MESMA frase — não há pista de qual foi o problema
E o motivo ("arquivo vazio") continua dentro da exceção

Dado que enviei um arquivo de 20 MB
Quando o upload é processado
Então a resposta tem status HTTP 413
E a mensagem é "Arquivo maior que o limite de 16 MB."
```

> ⚠️ **A frase fixa é decisão do operador, de 2026-10-10, e ela tem preço declarado:** as **três** recusas de conteúdo — arquivo vazio, byte nulo e cabeçalho ausente — passam a ter o **mesmo texto**, e ele perde a pista de qual foi. A troca foi pedida com a consequência à vista, e o motivo não se perdeu: está a um `str(erro)` de distância.

### US-U-03 — Duas árvores não se misturam, mesmo sem estado

> **Como** genealogista, **quero** que cada análise use **exatamente** a árvore que escolhi **para que** eu não veja resultado misturando duas famílias.

#### Critérios de aceite

```gherkin
Dado que carreguei uma árvore com 1.000 pessoas
Quando carrego uma árvore diferente com 10 pessoas
Então cada uma das duas análises opera sobre a árvore do arquivo que ela referenciou
E nenhuma pessoa da outra árvore aparece no resultado

Dado que duas análises são submetidas ao mesmo tempo
Quando cada uma resolve a sua referência
Então cada uma parseia a sua própria árvore
E nenhuma das duas vê a árvore da outra
```

> 🟢 **A garantia mudou de natureza nesta rodada, e ficou mais forte.** Até 2026-10-10 a árvore era **estado de processo reescrito a cada upload**, e havia uma lacuna aberta (`L-16`): com 4 threads, dois envios simultâneos podiam trocar a árvore entre o parse e o uso. Hoje a árvore é o **valor de retorno** do parse e entra **por parâmetro** em todo o núcleo — a corrida **deixou de existir estruturalmente** (`ADR-24`).

### US-U-04 — Continuidade entre requisições

> **Como** genealogista, **quero** que a análise seguinte use exatamente a árvore que carreguei **para que** o resultado corresponda ao arquivo que escolhi.

#### Critérios de aceite

```gherkin
Dado que carreguei uma árvore e recebi a referência do arquivo
Quando submeto uma busca de caminho
Então o servidor resolve e parseia o arquivo a partir da referência que enviei
E o resultado é calculado sobre a árvore daquele arquivo

Dado que enviei um valor de referência manipulado, com separador de caminho
Quando submeto a busca
Então a resposta é "Erro: Arquivo 'ROTULO' não existe mais."
E nenhum arquivo fora da pasta de upload é aberto

Dado um arquivo cujo nome visível tem acento, com chave válida
Quando submeto a busca
Então o arquivo é encontrado e a leitura funciona
E nenhuma mensagem diz que ele não existe
```

> 🟢 **O último cenário é a correção de 2026-10-10.** O alfabeto fechado da chave recusava acento e espaço — que o gravador **preserva de propósito** —, e três arquivos com acento e um com espaço da pasta real ficaram **inalcançáveis**, com a tela dizendo que não existiam (`BUG-20261009-6RKP`). A elegibilidade passou a ser por **forma de nome**, e a defesa contra escape continua: o valor tem de ser um **nome**, e não um caminho.

### US-U-05 — Reenvio que substitui, sem apagar

> **Como** genealogista, **quero** que reenviar a mesma árvore com correções **substitua** a versão anterior na lista **para que** eu não fique com duas linhas iguais — sem perder a versão antiga.

#### Critérios de aceite

```gherkin
Dado que já enviei "arvore.ged" e ele está na lista
Quando envio outro arquivo com o MESMO nome visível e conteúdo DIFERENTE
Então a lista passa a ter UMA linha com aquele nome
E a versão anterior foi movida para a pasta de aposentados
E nenhum arquivo foi apagado

Dado que envio um arquivo com conteúdo IDÊNTICO a um já armazenado
Quando o envio termina
Então a mesma referência é reencontrada
E o arquivo não é reescrito

Dado que envio um arquivo com nome visível inédito
Quando o envio termina
Então a lista ganha uma linha nova
```

> 🟢 **A ordem é a regra: listar ANTES de guardar.** Só a **foto de antes** separa "já existia" de "acabou de nascer", porque `guardar` **não sobrescreve**. Os três desfechos — `novo`, `identico` e `substituido` — têm mensagem própria.

### US-U-06 — Recuperação após erro de parsing

> **Como** genealogista, **quero** que um GEDCOM malformado **não** derrube a aplicação **para que** eu possa tentar outro arquivo.

#### Critérios de aceite

```gherkin
Dado que enviei um GEDCOM sintaticamente inválido
Quando o parse falha
Então a tela mostra uma mensagem em português
E a aplicação continua no ar
E as outras árvores continuam utilizáveis
```

### US-U-07 — A árvore que voltou é a árvore do arquivo

> **Como** genealogista, **quero** que a lista de nomes sugerida nos formulários venha da árvore que carreguei **para que** eu escolha entre as pessoas certas.

#### Critérios de aceite

```gherkin
Dado que carreguei uma árvore
Quando a tela é renderizada
Então a lista de nomes sugeridos está em ordem alfabética
E tem exatamente um item por pessoa carregada
E some da tela quando a árvore não tem ninguém
```

## Fluxo resumido

1. Abre `/` e recebe a tela com as **duas abas** e o formulário de envio dentro da aba de árvores. 🟢
2. Escolhe o arquivo `.ged` e envia. 🟢
3. O sistema lê o conteúdo inteiro, valida-o e só então grava sob a chave de conteúdo. 🟢
4. O sistema lista a pasta **antes** de gravar, para saber se é reenvio. 🟢
5. O sistema parseia `INDI`/`FAM`, monta o grafo e **devolve a árvore como valor**, mais a lista ordenada de nomes. 🟢
6. A tela confirma a carga e guarda a **referência** no formulário. 🟢

## Exceções e o que o usuário vê

| Exceção | Mensagem |
| --- | --- |
| Nenhum arquivo no campo | `"Nenhum arquivo GEDCOM enviado."` 🟢 |
| Arquivo sem nome | `"Nenhum arquivo selecionado."` 🟢 |
| Conteúdo recusado (vazio, com NUL ou sem `0 HEAD`) | `"Arquivo não reconhecido como GEDCOM. Favor, enviar o arquivo correto."` — **frase fixa para os três** 🟢 |
| Corpo acima do teto | `"Arquivo maior que o limite de 16 MB."` com `413` 🟢 |
| Falha inesperada de parse | `"Erro ao processar GEDCOM: {e}"` 🟢 |
| Referência ausente ou que não resolve | `"Erro: Arquivo GEDCOM não encontrado."` / `"Erro: Arquivo 'ROTULO' não existe mais."` 🟢 |

## O que esta história **não** cobre

| Fora de escopo | Por quê |
| --- | --- |
| Autenticação ou escolha de usuário | O sistema **não tem** usuário, sessão, papel ou permissão (`permissions.md`). O `dono` existe nas assinaturas e **não** isola nada 🟢 |
| Seleção de qual árvore usar | É da unit `tela-de-entrada`: a lista das duas abas, o "Abrir" e o "Apagar" 🟢 |
| Histórico de uploads | Nada é registrado: o arquivo é gravado e nunca apagado pelo sistema. **Aposentar move, não apaga** 🔴 |
| Correção de problemas no GEDCOM | O GEDCOM é tratado como autoridade; o sistema **avisa**, não corrige 🟢 |
| Limpeza da pasta de aposentados | A pasta cresce indefinidamente; não há expurgo nem decisão registrada 🔴 |

## Lacunas que afetam esta história 🔴

- **`P-05` → resolvida como decisão:** o CSV de DNA **não** passa por validação de conteúdo. A assimetria em relação ao GEDCOM é a **dívida #10**, preservada de propósito e agora declarada no contrato de cada unit.
- **`P-04`:** `app.secret_key` está no código sem consumidor; vira chave de forja caso alguém introduza sessão.
- ✅ **`L-16` fechada em 2026-10-10:** a corrida entre threads sobre a árvore **deixou de existir estruturalmente** — não há estado global de árvore para dois uploads disputarem.
- ✅ **`L-21` superada:** a decisão de **não** persistir resultados foi substituída pela feature 008, que passou a persistir o **histórico das análises de DNA** (opcionalmente). O upload em si continua sem registro.
- 🔴 **Nada verifica que a árvore gravada é legível antes de a análise pedir** — o GEDCOM é validado por conteúdo no envio, mas a pasta pode receber arquivo por fora da aplicação, e 10 dos 13 arquivos da pasta real derrubavam o parser até a guarda de 2026-10-10.

---

*Gerado pelo Reversa-Writer em 2026-10-10 (re-extração). Substitui a versão de 2026-10-05.*

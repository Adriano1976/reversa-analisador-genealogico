# Investigation: Rota do ícone de atalho para tela inicial

> Identificador: `009-rota-do-apple-touch-icon`
> Data: `2026-10-08`
> Confidência: 🟢 CONFIRMADO, 🟡 INFERIDO, 🔴 LACUNA

## 1. A pergunta de fundo

O projeto **já tem** ícone na aba do navegador — 128×128, embutido no documento como `data URI`
em `src/templates/index.html:8`, commitado em `b931062`. A pergunta desta investigação é
estreita e não óbvia:

> Por que o ícone que já existe **não** aparece quando o endereço é salvo na tela inicial de um
> celular?

A resposta não é "falta a imagem". É que **são dois recursos diferentes**, descobertos por
mecanismos diferentes.

## 2. O que a plataforma faz

| Comportamento | Consequência para esta feature | Confidência |
|---|---|---|
| O ícone de atalho é descoberto por um **caminho convencional na raiz do site**, e não pela imagem embutida no documento | É por isso que a solução do ícone da aba é **inerte** aqui. Não adianta melhorar o `data URI` | 🟢 |
| Quando o PNG tem transparência, o ícone é composto sobre **preto** | Servir a arte canônica como está produziria um quadrado preto com o desenho por cima — incluindo as aberturas internas entre folhas e galhos. Medido: a arte tem **32,5 % de pixels transparentes** e os quatro cantos em `(0, 0, 0, 0)` | 🟢 |
| O sistema aplica a **própria máscara de canto** | Cantos já arredondados na arte produziriam arredondamento duplo, com um anel de fundo no canto. A arte é enviada com cantos **retos** | 🟢 |
| O ícone do atalho é cacheado de forma **agressiva**, em ritmo próprio e ignorando cabeçalhos | Nenhuma escolha de cabeçalho resolve isso. O procedimento é remover e salvar o atalho de novo | 🟡 |
| O tamanho esperado é **180×180** | Outra medida é reamostrada pelo sistema e perde nitidez | 🟢 |

## 3. Alternativas avaliadas

### 3.1 `data URI` no próprio link do ícone de atalho — **rejeitada**

Seria a alternativa mais barata, porque reaproveitaria exatamente o mecanismo que já funciona na
aba: nenhuma rota, nenhum arquivo novo, nenhuma alteração em `src/app.py`.

**Rejeitada por dois motivos independentes:**

1. **Não funciona onde importa.** O sistema móvel não lê a imagem embutida para o ícone de
   atalho; ele busca o caminho na raiz. Há relato de terceiro com a tentativa de injeção em
   `base64` listada entre as que **falharam de forma confirmada** (ver §5).
2. **Custa caro.** Medido nesta sessão sobre a arte real: um PNG de 180×180 tem **20.954 bytes**,
   que viram **27.940 bytes** em base64. Somados aos 19.298 bytes que o ícone da aba já embute,
   o documento passaria a carregar ~47 KB só de ícone em **cada** resposta.

> A alternativa foi descartada por medição e por comportamento de plataforma, não por
> preferência. Se ela funcionasse, seria a escolhida.

### 3.2 Manifesto de aplicação web — **rejeitada**

É o mecanismo *moderno*: um arquivo de manifesto declara os ícones, e o documento o referencia
por um `<link rel="manifest">`.

**Rejeitada** porque a declaração exige **tocar no template**, o que contraria a `RN-02` (o
`GET /` deixaria de ser byte a byte idêntico) e mexe no que o `W005` vigia. Some-se que o
suporte a ícone por manifesto é **parcial** entre plataformas, enquanto o caminho convencional
funciona **sem declaração nenhuma**.

> É a alternativa mais defensável das rejeitadas, e vale como caminho futuro se o projeto
> ganhar uma SPA — quando mexer no documento deixar de ser proibido.

### 3.3 Servir por pasta estática do framework — **rejeitada**

**Rejeitada** por duas razões: `src/static/` é **proibida** desde a feature 003 pelo `W004`
("Reaparecimento de `src/README.md`, `src/.gitignore.txt` ou `src/static/`"), e configurar um
diretório estático normalmente implica um caminho parametrizado — que é exatamente a superfície
que o `BUG-20260929-QMLY` explorou no upload.

### 3.4 Rota dedicada com arquivo commitado — **ESCOLHIDA**

Uma rota de leitura em `src/app.py` devolvendo um PNG opaco de 180×180, commitado sob
`src/assets/`, com a facilidade do próprio framework cuidando da revalidação condicional.

**Escolhida** porque satisfaz todos os requisitos sem tocar em nada existente: o template fica
intocado, as três linhas atuais do contrato HTTP ficam intocadas, `src/static/` continua ausente
e não há entrada do cliente na composição do caminho.

### 3.5 Gerar a imagem em tempo de execução — **rejeitada**

Seria elegante: uma fonte só, nenhuma deriva possível.

**Rejeitada** por um impedimento medido: a arte canônica mora em `docs/assets/img/logo.png`, e o
`.dockerignore` é **lista de permissão** (`*`, `!requirements.txt`, `!src/`, `!src/**`). O
diretório `docs/` **não entra** na imagem, então dentro do contêiner **não existe fonte para
gerar nada**. Gerar no host, a cada partida, seria I/O no *import* de `src/app.py` — módulo que
a suíte e o harness de paridade importam.

### 3.6 Comparações de fidelidade da arte — o que foi medido

A pergunta prática do `RF-10` é **como** provar que a arte de runtime não derivou da canônica.
Três candidatos, e um deles foi eliminado por medição nesta sessão:

| Candidato | Veredito |
|---|---|
| Comparar `sha256` dos dois arquivos | ❌ **Eliminado por medição.** O **mesmo desenho** existe em disco com **32.317 bytes** e, vindo de outra codificação, com **44.069 bytes** — e a diferença de pixel entre os dois é **zero**. Uma comparação por hash daria alarme falso na primeira recompressão |
| Comparar dimensões e modo | ❌ Não detecta arte **trocada** pela metade, que é o caso que importa |
| **Regenerar** a partir da canônica e comparar **pixel a pixel** | ✅ **Escolhido.** É a única comparação que funciona entre um arquivo derivado e a sua fonte, e a que detecta tanto troca de desenho quanto edição pontual |

## 4. Padrões aplicáveis

| Padrão | Como se aplica | Confidência |
|---|---|---|
| **Recurso de caminho bem conhecido** | O caminho é imposto pela plataforma, não escolhido. Por isso `RN-09` trata cada caminho adicional como custo de contrato, e não como simetria | 🟢 |
| **Separação entre ícone de aba e ícone de atalho** | São dois recursos, com dois mecanismos, dois tamanhos e duas exigências de transparência. Tratá-los como um só foi o que motivou esta investigação | 🟢 |
| **Arte derivada com detecção de deriva** | Uma fonte canônica, uma cópia derivada commitada por exigência do empacotamento, e um teste que regenera e compara. É o mesmo desenho de "autoridade única + teste" que o projeto usa para a limpeza de texto | 🟢 |
| **Sem entrada do cliente no caminho** | A rota não tem parâmetro, não lê `query string` e deriva o caminho de `__file__`. É a defesa por construção contra a classe de falha do `BUG-20260929-QMLY` | 🟢 |

## 5. Fontes externas

- Relato de terceiro com as tentativas de ícone de atalho **falhando de forma confirmada**,
  incluindo a injeção por `base64` e a colocação do arquivo na raiz, e com a conclusão de que o
  servidor precisa servir o caminho na raiz:
  <https://station.railway.com/questions/streamlit-app-custom-icon-not-displaying-c9b7f771>
- Verificação de ícone de atalho do Lighthouse, que trata o ícone como **recurso buscável** e não
  como dado embutido:
  <https://developer.chrome.com/docs/lighthouse/pwa/apple-touch-icon.md.txt>

## 6. Lacunas declaradas

1. **Nada foi testado em aparelho real.** A conclusão sobre a composição da transparência sobre
   preto, sobre a máscara de canto e sobre o cache agressivo vem de **documentação e de relato
   de terceiros**, não de medição própria. O que foi medido nesta sessão é a arte (32,5 % de
   pixels transparentes, cantos `(0,0,0,0)`, cores dominantes) e o comportamento dos caminhos
   hoje (`404` nos três). **A prova em aparelho é do `onboarding.md`, e depende do operador.**
2. **O caminho convencional não foi verificado com o cabeçalho de descoberta.** Existe um
   mecanismo de declaração do ícone de atalho no documento; a `RN-09` decidiu **não** usá-lo,
   porque o caminho convencional é descoberto sem declaração e declarar custaria tocar no
   template. Se a descoberta se mostrar pouco confiável em algum sistema, a alternativa 3.2
   (manifesto) volta à mesa — e aí a `RN-02` teria de ser reaberta por decisão do operador.
3. **O tamanho de 180×180 não foi confrontado com outros tamanhos.** Há sistemas que usam
   152×152 e 167×167. Servir apenas 180 e deixar o sistema reamostrar foi considerado
   suficiente; **não** foi medido se um tamanho específico produz resultado visivelmente melhor.

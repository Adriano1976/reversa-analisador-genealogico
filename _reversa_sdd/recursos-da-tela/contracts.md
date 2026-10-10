# Unit `recursos-da-tela` — Contratos

> Re-extração de **2026-10-10** (nível **Completo**). Unit **nova** — não substitui artefato anterior.
> Este arquivo fixa **o que atravessa a fronteira** da unit: o contrato HTTP das duas rotas, o contrato das **artes derivadas**, o contrato da **receita**, o contrato de **pasta** e o contrato da **masthead**.
> Escala de confiança: 🟢 CONFIRMADO | 🟡 INFERIDO | 🔴 LACUNA

---

## 1. Contrato HTTP

### 1.1 As duas rotas

| Método | Caminho | Status | Corpo | Cabeçalhos |
| --- | --- | --- | --- | --- |
| `GET` | `/apple-touch-icon.png` | `200` | PNG do ícone derivado | `Content-Type: image/png`, `ETag` 🟢 |
| `GET` | `/banner.png` | `200` | PNG do banner derivado | `Content-Type: image/png`, `ETag` 🟢 |
| `GET` | qualquer das duas, arte ausente | **`404`** | **vazio** | — 🟢 |
| `GET` | qualquer das duas, com `If-None-Match` que casa | **`304`** | **sem corpo** | `ETag` 🟢 |
| `POST`, `PUT`, `DELETE`, `PATCH` | qualquer das duas | **`405`** | — | pelo **roteador**, sem validação própria 🟢 |

> 🟢 **As duas rotas são o mesmo contrato.** Não há diferença de desenho entre elas: `GET` sozinho, `ETag` do `send_file`, `404` com resposta vazia, caminho ancorado no arquivo do app e `mimetype="image/png"`.
>
> 🟢 **Não há `Cache-Control` de validade longa em nenhuma das duas.** A arte do ícone foi trocada **duas vezes em um único dia**, e uma validade de um ano congelaria o cliente que já tivesse buscado — o `ETag` só age **depois** de a validade expirar. A revalidação barata vem do `304`.
>
> 🟢 **O `405` sai do roteador, e não de uma validação escrita à mão** — que poderia divergir da convenção.

### 1.2 Contrato da ausência

| Propriedade | Contrato |
| --- | --- |
| Status | `404` 🟢 |
| Corpo | **vazio** — não há HTML de erro, não há mensagem 🟢 |
| Efeito em outras rotas | **Nenhum**: `GET /` e todas as demais respondem igual 🟢 |
| Efeito na tela | O atalho degrada para o ícone genérico; o banner não aparece, e o **título continua**, porque é texto 🟢 |
| Como é testado | Apontando a chave de `app.config` para um caminho inexistente, **sem tocar no repositório** 🟢 |

### 1.3 Contrato da descoberta

| Propriedade | Contrato |
| --- | --- |
| Descoberta do ícone | Por **caminho convencional** na raiz; o template **não** o declara 🟢 |
| `GET /` | **Byte a byte o mesmo** — a rota de arte é um acréscimo **puro** 🟢 |
| Ícone da aba | `data URI` embutido no documento, **não** uma segunda rota 🟢 |
| `favicon.ico` | **Sem rota.** Só seria buscado se o documento não declarasse ícone, e ele declara 🟢 |
| `apple-touch-icon-precomposed.png` | **Sem rota** — alias legado, superfície sem consumidor 🟢 |

---

## 2. Contrato das artes derivadas

> ⚠️ **A arte servida NÃO é a arte canônica.** Nas duas rotas a resposta é uma **renderização derivada**. Servir o arquivo como chegou produz um defeito **visível**: quadrado preto no atalho e grade cinza atrás do logo.

### 2.1 O ícone de atalho — `src/assets/apple-touch-icon.png`

| Propriedade | Contrato | Conf. |
| --- | --- | --- |
| Fonte | `docs/assets/img/logo.png` — 512×512 RGBA, **32,5 %** de pixels totalmente transparentes | 🟢 |
| Composição | Sobre **branco opaco** | 🟢 |
| Fundo | **Branco** — a arte tem 51,5 % de creme em **duas** tonalidades, e eleger uma faria a outra parecer errada | 🟢 |
| Reamostragem | `180×180`, com **LANCZOS** | 🟢 |
| Cantos | **Retos** — o sistema aplica a própria máscara arredondada | 🟢 |
| Modo | `RGB`, **sem canal alfa** | 🟢 |
| Tamanho do arquivo | **16.504 bytes** — âncora contra reamostragem, fundo ou compressão diferentes | 🟢 |
| Opacidade provada por | **Tipo de cor 2** no IHDR (`truecolor` sem alfa), lido **sem biblioteca de imagem** | 🟢 |

> 🟢 **Por que compor sobre branco:** o sistema móvel compõe transparência sobre **preto** no ícone de atalho. Servir a arte crua daria um quadrado preto com o desenho por cima — **incluindo as aberturas internas** entre folhas e galhos.
>
> 🟢 **Por que a prova é estrutural:** não existe pixel transparente num PNG cujo cabeçalho **nega** o canal alfa. Isso dispensa a biblioteca de imagem no teste — o que importa porque ela **não** está em `requirements.txt`.

### 2.2 O banner — `src/assets/banner-da-tela.png`

| Propriedade | Contrato | Conf. |
| --- | --- | --- |
| Fonte | `docs/assets/img/banner-analisador.png` — em **`RGB`, sem alfa**, com o quadriculado **gravado no bitmap** | 🟢 |
| Remoção de fundo | **Global**, e **não** por inundação a partir da borda | 🟢 |
| Faixa alta | brilho **≥ 190** → fundo se saturação **≤ 50** | 🟢 |
| Faixa média | brilho **160–190** → fundo se saturação **≤ 12** | 🟢 |
| Piso | brilho **< 160** → **nunca** é fundo | 🟢 |
| Fronteira | **Alfa proporcional** à distância do fundo | 🟢 |
| Modo | `RGBA` | 🟢 |
| Tamanho do arquivo | **317.058 bytes** (medido em 2026-10-10) | 🟢 |
| Resíduo na caixa de regressão | **Zero** | 🟢 |
| Pontos de arte preservados | **11**, opacos | 🟢 |

> 🟢 **Por que global, e não por inundação:** a árvore, o livro e o texto formam **anúncios fechados**, e o fundo preso dentro deles nunca é alcançado. Medido na primeira versão: o pixel `(300,150)` continuava opaco e sobravam **8.379** pixels de tom de fundo opacos numa amostra de **1/9** da imagem.
>
> 🟢 **Por que duas faixas:** o quadriculado é **neutro** (saturação 0–7) e a tinta clara da arte é levemente **quente** (o preenchimento do texto dourado tem brilho ≈212 e saturação ≈24). Com um limite único, os dois caíam no fundo e as **letras ficavam ocas** — defeito medido no composto sobre magenta.
>
> 🟢 **Por que o alfa é proporcional:** entre a arte e o xadrez há uma faixa de **1 a 2 pixels** de cinza intermediário; deixá-la opaca desenharia um **halo claro** em volta de tudo.
>
> 🟢 **Por que a métrica de resíduo é não-circular:** ela usa `SATURACAO_MAXIMA - 5`, **mais estrita** que a regra. Medir com o mesmo limite devolve **sempre zero** — e foi esse erro que deixou um bloco inteiro de quadriculado passar **duas vezes**, com a métrica dizendo `0,00 %` enquanto o composto sobre magenta mostrava o bloco.

---

## 3. Contrato da receita

| Propriedade | Contrato | Conf. |
| --- | --- | --- |
| Onde mora | **`tests/`** — `icone_de_atalho.py` e `banner_da_tela.py` | 🟢 |
| Fonte única | Sim: existe **uma só** definição de cada transformação, e o teste de deriva a **importa** | 🟢 |
| Import da biblioteca de imagem | **Preguiçoso**, dentro das funções, para importar o módulo não exigir a biblioteca | 🟢 |
| A biblioteca em `requirements.txt` | **Proibida** — há teste que falha se `pillow`/`PIL==` aparecer | 🟢 |
| Onde a arte commitada mora | `src/assets/` | 🟢 |
| Geração em tempo de execução | **Proibida**: a arte é **commitada**. A fonte canônica mora em `docs/`, que **não entra na imagem** — dentro do container não existe fonte para gerar nada | 🟢 |
| Comparação de deriva | **Pixel a pixel**, com prova de que detecta **um** pixel alterado | 🟢 |
| Comparação por `sha256` | **Proibida na prática** | 🟢 |

> 🟢 **Por que `sha256` é proibido:** o **mesmo** desenho existe em disco com **32.317** bytes e, vindo de outra codificação, com **44.069** bytes — e a diferença de pixel entre os dois é **zero**. Um teste que acusa divergência onde não há nenhuma é desligado, e aí a deriva real passa despercebida.
>
> 🟢 **Por que a receita não é código de runtime:** o container não precisa da biblioteca de imagem, porque a arte **chega pronta** dentro da imagem. E gerar no host a cada partida seria I/O no import de `src/app.py` — módulo que a suíte e o harness de paridade importam.

---

## 4. Contrato de pasta e de build

| Propriedade | Contrato | Conf. |
| --- | --- | --- |
| Onde a arte de runtime pode morar | **`src/assets/`** | 🟢 |
| Por quê | O `.dockerignore` é lista de **permissão**: `*`, `!requirements.txt`, `!src/`, `!src/**` | 🟢 |
| O que a lista evita | Uma falha **silenciosa**: arte fora de `src/` responde **`200` na máquina de desenvolvimento** e **`404` no container** — o ambiente que o operador usa | 🟢 |
| `src/static/` | **Proibida** (`W004`); há teste que falha se a arte cair numa pasta estática | 🟢 |
| `src/uploads/` | **Reexcluído** do contexto de build **depois** de `!src/**` | 🟢 |
| Por que a reexclusão | A pasta carrega **dado real do operador** — **13 arquivos** (mais 4 aposentados), entre eles um GEDCOM de 5,3 MB. A última regra que casa vence | 🟢 |

> 🟢 **A escolha de pasta não é estética.** É a diferença entre a arte existir no ambiente do operador e existir só na máquina de quem desenvolve.

---

## 5. Contrato da masthead

| Ordem | Elemento | Contrato | Conf. |
| ---: | --- | --- | --- |
| 1 | **Imagem** | Arte do topo com `class="w-50"`; `alt` descreve a **ilustração** | 🟢 |
| 2 | **Subtítulo** | — | 🟢 |
| 3 | **Título em texto** | `<h1>` — o título **voltou a ser texto** | 🟢 |
| 4 | **Texto de apresentação** | — | 🟢 |

> 🟢 **A ordem é contrato, e já foi invertida uma vez:** a `T036` trocou o `<h1>` por imagem, e a `T044` reverteu — arte reduzida à metade, subtítulo, título em texto e apresentação, **nessa ordem**.
>
> 🟢 **O título sobrevive à arte ausente por construção**, e não por depender do `alt`.
>
> 🟢 **O `alt` não repete o título:** com o título escrito logo abaixo, repeti-lo faria o leitor de tela anunciar a mesma coisa **duas vezes**.

---

## 6. Contrato de mensagens

**Não há nenhuma mensagem ao operador nesta unit.** 🟢

| Situação | O que a unidade responde |
| --- | --- |
| Arte ausente | `404` com corpo **vazio** — sem texto, sem HTML de erro 🟢 |
| Escrita no caminho | `405` do roteador, com o corpo padrão do Flask 🟡 |
| Revalidação bem-sucedida | `304` **sem corpo** 🟢 |

> 🟡 **Não há log de arte ausente.** O `404` é indistinguível, nos registros, de "essa rota não existe" — e a aplicação não registra nada em nenhum dos casos.

---

## 7. Contrato de falha

| Situação | O que **é** garantido | O que **não** é |
| --- | --- | --- |
| Arte ausente no disco | `404` vazio; a tela continua de pé, com o título em texto | Nenhum log, nenhum aviso 🔴 |
| Escrita no caminho da arte | `405` pelo roteador | — 🟢 |
| Cliente com a arte em cache e sem revalidar | — | **Não há validade longa**, então a rebusca é barata, mas não é evitada |
| Recompressão da arte commitada | **Não** é reportada como deriva | — 🟢 |
| Alteração de **um** pixel na arte commitada | O teste de deriva **detecta** | — 🟢 |
| Arte corrompida em disco | A rota serve os bytes que existirem | 🔴 **Não há validação de integridade em runtime** — só o teste de deriva, que roda fora da aplicação |
| Arte errada **dentro do container** | — | 🔴 **Não detectado**: os testes rodam no host, onde `docs/` existe (`L-33`) |
| Biblioteca de imagem instalada por engano no runtime | — | Só o teste de deriva acusa, e ele roda no host 🔴 |

---

## 8. Compatibilidade e versionamento

| Elemento do contrato | Estabilidade exigida | Consequência de mudar |
| --- | --- | --- |
| Os dois caminhos (`/apple-touch-icon.png`, `/banner.png`) | **Crítica** | O primeiro é **convenção do sistema operacional**: não há como declará-lo e ser obedecido |
| `GET` sozinho nas duas rotas | **Alta** | Acrescentar método reintroduz a validação que o roteador já faz |
| `404` com corpo **vazio** na ausência | **Alta** | Um corpo com HTML mudaria o que o cliente recebe numa degradação |
| Ausência de validade longa | **Alta** | Uma validade de um ano congelaria o cliente depois da próxima troca de arte |
| Caminho ancorado no **arquivo do app** | **Alta** | Ancorar no diretório corrente reintroduz o defeito que a leitura e a escrita divergem |
| Ordem `filtro → entidades`… — **não se aplica aqui**: esta unit não tem escape de texto | — | — |
| Composição do ícone sobre **branco** | **Alta** | Trocar por transparente devolve o quadrado preto no atalho |
| Lado do ícone em **180×180** e cantos **retos** | **Alta** | Outra medida é reamostrada pelo sistema; cantos arredondados produzem arredondamento duplo |
| As **duas faixas** de brilho/saturação | **Alta** | Um limite único deixa as letras do texto dourado **ocas** |
| Métrica de resíduo **mais estrita** que a regra | **Alta** | Igualá-la torna a métrica **circular**: ela passa a devolver sempre zero |
| Arte **commitada** em `src/assets/` | **Alta** | Gerar em runtime exigiria a fonte dentro da imagem — que a lista de permissão **não** deixa entrar |
| Comparação de deriva por **pixel** | **Alta** | Voltar ao `sha256` acusa deriva onde não há, e o teste é desligado |
| A biblioteca de imagem fora de `requirements.txt` | **Alta** | Entrar no runtime leva `PIL` para dentro do container sem necessidade |
| A ordem da masthead | Média | Muda a leitura da tela; o título em texto é o que sustenta a degradação |
| Os bytes exatos das artes (16.504 / 317.058) | Média | São **âncoras de deriva**, não formato: mudam legitimamente quando a arte muda, e é isso que o teste de deriva registra |

---

*Gerado pelo Reversa-Writer em 2026-10-10 (re-extração). Unit nova.*

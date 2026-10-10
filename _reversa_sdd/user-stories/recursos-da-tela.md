# User Stories — Fluxo `recursos-da-tela`

> Re-extração de **2026-10-10** (nível **Completo**). Artefato **novo** — nasceu com a unit, que não existia em nenhuma extração anterior.
> Persona única do sistema. Fontes: `recursos-da-tela/requirements.md`, `recursos-da-tela/design.md`, `recursos-da-tela/contracts.md`, `adrs/` 28, 29
> Escala de confiança: 🟢 CONFIRMADO | 🟡 INFERIDO | 🔴 LACUNA

---

## Persona

**Genealogista Genético** — e, neste fluxo, também o **leitor do resultado**. Ele não pede a arte: o **navegador** e o **sistema operacional** pedem. O que ele percebe é a consequência. 🟢

## História principal

> **Como** genealogista, **quero** que a aplicação tenha a **cara** de um produto — ícone próprio no celular e ilustração no topo da tela — **para que** ela seja reconhecível entre os atalhos e a tela não pareça um formulário cru.

**Valor de negócio:** é a única unit do sistema cuja entrega é **visual**. E é a única que **não depende de nenhuma outra** (`dependencies: []`). 🟢

**A regra que define o fluxo:** **a arte servida não é a arte canônica.** As duas respostas são **renderizações derivadas**, e a derivação existe porque servir o arquivo como ele chegou produz um defeito **visível**: quadrado preto no atalho e grade cinza atrás do logo. 🟢

## Histórias

### US-E-01 — O atalho não vira um quadrado preto

> **Como** genealogista, **quero** adicionar a aplicação à tela inicial do celular e ver **o desenho**, não um quadrado preto **para que** eu reconheça o atalho.

#### Critérios de aceite

```gherkin
Dado que a arte canônica tem 32,5 % de pixels transparentes e os quatro cantos vazios
Quando o ícone de atalho é derivado
Então a arte é composta sobre fundo BRANCO
E é reamostrada para 180x180
E os cantos ficam RETOS
E o PNG resultante não declara canal alfa

Dado que o sistema procura o ícone por caminho convencional
Quando o atalho é criado
Então a arte é encontrada na raiz, sem precisar ser declarada no documento
```

> 🟢 **O motivo é específico, e não estético:** o sistema móvel compõe transparência sobre **preto** no ícone de atalho. Servir a arte crua daria um quadrado preto com o desenho por cima — **incluindo as aberturas internas** entre folhas e galhos. E os cantos ficam retos porque o sistema aplica a **própria** máscara arredondada: arredondar aqui produziria arredondamento duplo, com um anel de fundo no canto.

### US-E-02 — A ilustração do topo não traz o xadrez junto

> **Como** genealogista, **quero** ver a ilustração no topo da tela **sem** a grade cinza de transparência atrás dela **para que** a tela pareça acabada.

#### Critérios de aceite

```gherkin
Dado que a fonte da ilustração chegou em RGB, com o quadriculado de transparência gravado no bitmap
Quando a arte do topo é derivada
Então o fundo é removido ONDE ELE ESTIVER, e não apenas a partir das bordas
E o resultado é um PNG com canal alfa
E nenhum bloco de quadriculado sobrevive opaco

Dado que a arte tem texto dourado claro sobre fundo claro
Quando o fundo é removido
Então o preenchimento das letras permanece opaco
E as letras não ficam ocas

Dado que existe uma faixa de 1 a 2 pixels entre a arte e o fundo
Quando o fundo é removido
Então essa fronteira recebe transparência PARCIAL
E não aparece um halo claro em volta da arte
```

> 🟢 **Os três cenários são defeitos medidos, um por um:** a inundação a partir da borda deixou **8.379** pixels de fundo opacos numa amostra de 1/9 da imagem (a árvore, o livro e o texto formam anúncios fechados); um limite único de brilho deixou as **letras ocas**; e deixar a fronteira opaca desenharia o **halo**.

### US-E-03 — A tela continua de pé se a arte faltar

> **Como** genealogista, **quero** que a ausência de uma imagem **não** me deixe sem a tela **para que** eu consiga trabalhar mesmo assim.

#### Critérios de aceite

```gherkin
Dado que a arte não está no disco
Quando o navegador pede a rota
Então a resposta é 404 com corpo VAZIO
E a tela continua funcionando
E o título da tela continua visível, porque é TEXTO
E nenhuma outra rota altera a resposta
```

> 🟢 **O título em texto é o que sustenta a degradação, e isso já foi o contrário:** a arte substituiu o `<h1>` numa primeira versão, e a decisão foi revertida — hoje a ilustração vem **acima** do título, que voltou a ser texto. A ordem é **imagem → subtítulo → título → apresentação**.

### US-E-04 — Não mexer no que já funcionava

> **Como** genealogista, **quero** que acrescentar a arte ao topo **não** mude mais nada na tela **para que** eu não precise reaprender onde as coisas ficam.

#### Critérios de aceite

```gherkin
Dado que a tela funcionava antes da arte do topo
Quando a arte é acrescentada
Então a ordem dos elementos da masthead é imagem, subtítulo, título em texto e apresentação
E a arte aparece reduzida à metade da largura
E o texto alternativo descreve a ILUSTRAÇÃO, e não o título
E o ícone da aba continua sendo o mesmo, embutido no documento
```

> 🟢 **O `alt` não repete o título** de propósito: com o título escrito logo abaixo, repeti-lo faria o leitor de tela anunciar a mesma coisa **duas vezes**.

### US-E-05 — A arte não é baixada de novo a cada visita

> **Como** genealogista, **quero** que a tela carregue rápido na segunda visita **para que** eu não espere por uma imagem que já vi.

#### Critérios de aceite

```gherkin
Dado que já carreguei a tela uma vez
Quando volto à aplicação
Então o navegador revalida a arte com o identificador que recebeu
E a resposta é 304, sem corpo
E eu não fico preso a uma versão antiga depois de a arte mudar
```

> 🟢 **Aqui há uma escolha deliberada, e ela custa:** não há validade longa de cache. A arte do ícone foi trocada **duas vezes em um único dia**, e uma validade de um ano congelaria o cliente que já tivesse buscado. A revalidação barata vem do identificador de versão, que responde `304` sem corpo.

## Fluxo resumido

1. O navegador pede o ícone de atalho no caminho convencional, ou o **sistema móvel** o faz ao criar o atalho. 🟢
2. A aplicação responde o PNG **derivado** — composto sobre branco, 180×180, sem alfa. 🟢
3. O navegador pede a arte do topo ao renderizar a tela. 🟢
4. A aplicação responde o PNG **derivado** com o fundo removido. 🟢
5. Na visita seguinte, o navegador revalida: `304`, sem corpo. 🟢

## O que o usuário **não** recebe — e por quê

| Ausência | Motivo | Conf. |
| --- | --- | --- |
| `favicon.ico` | O documento **declara** um ícone (embutido), e o `favicon.ico` só é buscado quando não há declaração. A rota seria superfície sem consumidor | 🟢 |
| `apple-touch-icon-precomposed.png` | Alias legado, sem consumidor | 🟢 |
| Um ícone servido por rota própria na aba do navegador | O ícone da aba é um `data URI` embutido: não custa requisição nem arquivo | 🟢 |
| Texto alternativo com o nome do sistema | O `alt` descreve a **ilustração**; o título é texto logo abaixo | 🟢 |
| Arte gerada em tempo de execução | A fonte canônica mora fora da imagem: dentro do contêiner não existe fonte para gerar nada, e gerar no arranque seria I/O na suíte | 🟢 |
| A biblioteca de imagem no ambiente de execução | A arte chega **pronta** dentro da imagem; a biblioteca só existe no ambiente de teste | 🟢 |
| Qualquer aviso quando a arte falta | 🔴 Nenhum log, nenhuma métrica: o `404` é indistinguível, nos registros, de "essa rota não existe" | 🔴 |

## Lacunas que afetam esta história 🔴

- **`L-33`:** não há verificação de que a arte servida é a **derivada correta dentro do contêiner**. Os testes rodam no host, onde a pasta de fontes existe. Se a arte falhar **dentro da imagem**, a degradação é o `404` — **silencioso, sem log e sem teste**, que é exatamente o caso que a escolha de `src/assets/` existe para evitar. **É a lacuna mais relevante desta história.**
- **`L-34`:** a âncora que prova que a tela **não mudou** é um resumo criptográfico do HTML **mantido à mão**, atualizado três vezes em um único dia. Enquanto cada atualização for decisão humana registrada, ele prende o que promete.
- **Não há cache em memória**, e não há medição do custo de servir 317 KB por requisição.
- **A folga dos limites de remoção de fundo é declarada, não medida** por experimento controlado; os onze pontos de arte preservados são a rede contra aperto indevido.
- **A receita que produz a arte entregue ao operador é código de teste** — é o preço de manter a biblioteca de imagem fora do ambiente de execução.

---

*Gerado pelo Reversa-Writer em 2026-10-10 (re-extração). Unit nova.*

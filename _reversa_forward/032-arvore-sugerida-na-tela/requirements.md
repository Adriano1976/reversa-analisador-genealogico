# Requirements: árvore sugerida na tela

> Identificador: `032-arvore-sugerida-na-tela`
> Data: `2026-10-19`
> Pasta da extração reversa: `_reversa_sdd/`
> Confidência: 🟢 CONFIRMADO, 🟡 INFERIDO, 🔴 LACUNA / DÚVIDA
> Documento pedido pelo operador em 2026-10-19, depois de ele não encontrar as gerações virtuais
> na tela: elas existem no grafo e no DOT, mas **nenhuma superfície as mostra**.

## 1. Resumo executivo

O operador viu `ERRO CRONICO / QUEBRA DE LINHA` no cartão e não encontrou em lugar nenhum a
correção sugerida: as gerações virtuais que a `029` injeta existem no grafo e no desenho de imagem,
mas **não na tela**. Esta feature põe a árvore sugerida no cartão: um resumo em texto com o número
de gerações intermediárias e o desenho do caminho corrigido, em Mermaid, sem instalar nada.

O ponto que a feature **não** pode errar é o custo: `arvore_sugerida` copia o grafo da árvore
(O(V+E)) e a análise real tem 142 cartões. A tela não chama essa função — ela deriva o mesmo número
(hiato) dos dados que o cartão já tem, e desenha a partir dos metadados do caminho.

## 2. Contexto a partir do legado

| Fonte | Trecho relevante | Confidência |
|-------|------------------|-------------|
| `src/templates/index.html` (871-891) | O cartão já desenha o caminho **documentado** em Mermaid, dentro de `details.grafo-do-registro` | 🟢 |
| `src/templates/index.html` (1246-1260) | O JS roda `mermaid.run` e o `toggle` re-renderiza qualquer `details` com diagrama | 🟢 |
| `src/reporting/mermaid_render.py` | Emissor Mermaid com contrato de escape próprio; não importa `core` | 🟢 |
| `src/core/cirurgia_do_grafo.py` | `arvore_sugerida` monta a sugestão **copiando o grafo** | 🟢 |
| `_reversa_sdd/addenda/029-desacoplamento-de-nos.md` | O contrato da sugestão: `hiato`, `geracoes_virtuais`, `juncoes` | 🟢 |
| `_reversa_sdd/addenda/030-renderizador-graphviz.md` | As três cores e o rótulo da aresta rompida, já validados na imagem | 🟢 |
| `_reversa_sdd/addenda/031-veredito-no-cartao.md` | O selo de validação no cabeçalho, que diz **que** quebrou | 🟢 |
| `docker/Dockerfile`; `.dockerignore` | O container não tem o binário `dot` e a lista é de permissão | 🟢 |
| `.reversa/principles.md#iii` | Nenhuma mudança sem teste que a cubra | 🟢 |

### 2.1 O que já existe e **não** será reimplementado

| Componente | O que já responde | Por que não basta |
|------------|-------------------|-------------------|
| `core.cirurgia_do_grafo.arvore_sugerida` | A árvore sugerida completa, com grafo transformado | Copia o grafo por chamada; 142 cartões inviabilizam |
| `reporting.mermaid_render` | Emite Mermaid do caminho documentado | Não conhece gerações virtuais nem aresta rompida |
| `index.html` | Desenha o caminho documentado, com toggle | Não tem segundo diagrama |
| `core.validator` | O veredito e o `mrca_estimado.geracoes` | Não diz quantas gerações faltam |

### 2.2 A lacuna que esta feature fecha

1. **Nenhuma superfície mostra a sugestão.** Ela existe em `arvore_sugerida`, que só teste e script
   chamam.
2. **O operador conclui que a feature não funciona.** Foi exatamente o que aconteceu em 2026-10-19:
   sem ver nada na tela, a leitura natural é "não implementado".
3. **O hiato não é explicado quando é zero.** Quando não há geração a injetar, nada na tela diz
   isso — e a ausência vira a mesma dúvida.
4. **A imagem depende do Graphviz.** Sem `dot`, não há PNG; a tela não pode depender disso.

## 3. Personas e cenários de uso

| Persona | Objetivo | Cenário-chave |
|---------|----------|---------------|
| Operador / genealogista | Ver onde a linha quebrou e como ficaria corrigida | Abre o cartão em conflito e vê "3 gerações sugeridas" com o desenho do caminho corrigido |
| Auditor de dados | Conferir o número que a sugestão usa | Confere `hiato` e as gerações no resumo, sem depender de imagem |
| Desenvolvedor do legado | Não pagar 142 cópias de grafo por análise | A tela deriva o hiato aritmeticamente |

## 4. Regras de negócio novas ou alteradas

### 4.1 Definições operacionais

| Termo | Definição nesta feature |
|-------|--------------------------|
| **Árvore sugerida** | O caminho documental com as gerações virtuais inseridas e a aresta rompida marcada. |
| **Hiato** | `floor(gerações_estimadas + 0,5) − gerações documentadas do doador`; o número que a `029` usa. |
| **Geração virtual** | Nó `Geração k`, sem pessoa, inserido entre o ancestral e o primeiro descendente documentado. |
| **Aresta rompida** | O vínculo que a `029` cortou; no desenho, tracejado vermelho. |

### 4.2 Regras

1. **RN-01: a tela deriva o hiato, não chama a cirurgia.** `arvore_sugerida` copia o grafo da
   árvore; a análise real tem 142 cartões. A tela calcula o mesmo número a partir de
   `mrca_estimado.geracoes` e `degrees.a_up`, sem tocar no grafo. 🟢
   - Origem no legado: `src/core/cirurgia_do_grafo.py`; `_reversa_sdd/architecture.md#4`
   - Tipo: nova (restrição de custo)

2. **RN-02: o desenho é Mermaid, no navegador.** Nenhuma dependência nova, nada a instalar no
   container, e a tela funciona em máquina sem Graphviz — que é o estado atual. 🟢
   - Origem no legado: `src/templates/index.html` (871-891, 1246-1260);
     `docker/Dockerfile`
   - Tipo: nova

3. **RN-03: as cores são as mesmas da imagem.** Base `#a8e6cf`, documental `#f5f5f5`, virtual
   `#ffd3b6`, aresta rompida tracejada `red`. A mesma linguagem visual nos dois produtos. 🟢
   - Origem no legado: `_reversa_sdd/addenda/030-renderizador-graphviz.md`
   - Tipo: preservada (a paleta é contrato, não gosto)

4. **RN-04: a geração virtual é rotulada `Geração k`, sem nome.** No desenho e no resumo. Nenhum
   nome de pessoa é inventado. 🟢
   - Origem no legado: `_reversa_sdd/addenda/029-desacoplamento-de-nos.md` (RN-11 da 029)
   - Tipo: preservada

5. **RN-05: o resumo em texto existe sempre que o desenho existe.** "3 gerações sugeridas entre o
   ancestral e o primeiro descendente" — a informação não pode viver só na imagem, por
   acessibilidade e por conferência. 🟢
   - Origem no legado: `.reversa/principles.md#iii`
   - Tipo: nova

6. **RN-06: sem geração a injetar, a tela explica — mas só onde há conflito.** Quando
   `hiato <= 0`, o cartão **em conflito** informa que as duas medidas concordam (ou que o cM não
   permitiu estimar). Cartão validado ou inconclusivo não ganha frase nenhuma: repetir a explicação
   em 142 cartões, a maioria sem conflito, trocaria um silêncio ruidoso por um ruído constante. 🟢
   - Origem no legado: `src/core/cirurgia_do_grafo.py` (`HIATO_NAO_POSITIVO`,
     `SEM_MRCA_ESTIMADO`)
   - Tipo: nova (decidido em §9, D3)

7. **RN-07: o diagrama documentado continua como está, e o novo bloco fica logo abaixo dele.** O
   segundo desenho não substitui `grafo-do-registro` nem os quatro estados; ele entra na mesma
   vizinhança e usa a mesma mecânica de `details` + `toggle` que já existe. O **resumo fica no
   título do bloco** (visível sem clique) e o diagrama carrega quando o operador abre. 🟢
   - Origem no legado: `.reversa/principles.md#ii`; `index.html` (871-891, 1246-1260)
   - Tipo: preservada (decidido em §9, D1 e D2)

8. **RN-08: o texto Mermaid é determinístico.** Mesma entrada, mesmo texto; nada depende de
   iteração de `set`. 🟢
   - Origem no legado: `_reversa_forward/030-.../requirements.md` (RN-12)
   - Tipo: preservada

9. **RN-09: rótulo é escapado pelo contrato do emissor Mermaid.** Nome com aspas, parêntese ou
   acento não quebra o diagrama. 🟢
   - Origem no legado: `reporting/mermaid_render.py` (contrato de escape, `BUG-20260929-J6PQ`)
   - Tipo: preservada

10. **RN-10: nada muda fora do cartão.** Os quatro estados, o selo da `031`, a busca, a lista de
    arquivos e o banco ficam intactos. 🟢
    - Origem no legado: `.reversa/principles.md#ii`
    - Tipo: preservada

11. **RN-11: uma derivação por cartão, O(saltos).** Sem cópia de grafo, sem segunda passada de
    matching e sem chamar o validador de novo. 🟢
    - Origem no legado: `RN-01`; `_reversa_sdd/architecture.md#4`
    - Tipo: nova

> **Princípios aplicados.** I (fixture sintética), II (o que existe na tela não muda), III (todo
> caminho com teste), IV (só filiação é desenhada como linhagem), V (o número vem da `028`/`029`,
> com a fonte lá citada). Nenhum conflito com princípio ativo.

### 4.3 Valores de domínio e fontes

| Constante | Valor | Fonte | Confidência |
|-----------|-------|-------|-------------|
| Cor do nó base | `#a8e6cf` | `_reversa_sdd/addenda/030-...`; pedido do operador | 🟢 |
| Cor do nó documental | `#f5f5f5` (borda `#666666`) | idem | 🟢 |
| Cor do nó virtual | `#ffd3b6` | idem | 🟢 |
| Cor da aresta rompida | `red`, tracejada | idem | 🟢 |
| Rótulo da aresta | `DESVIO DE CONEXÃO / QUEBRA DE LINHA` | idem | 🟢 |
| Fórmula do hiato | `floor(gerações + 0,5) − a_up` | `core.cirurgia_do_grafo` (RN-07 da 029) | 🟢 |

### 4.4 Códigos de aviso

| Código | Quando aparece | Efeito na tela |
|--------|----------------|----------------|
| `SUGESTAO_DISPONIVEL` | `hiato >= 1` e veredito de erro | Resumo no título do bloco + diagrama colapsável |
| `HIATO_NAO_POSITIVO` | `hiato <= 0`, **em cartão em conflito** | Frase curta explicando que as medidas concordam |
| `SEM_MRCA_ESTIMADO` | Sem `mrca_estimado.geracoes`, **em cartão em conflito** | Frase curta explicando que o cM não permitiu estimar |
| `SUGESTAO_INSUFICIENTE` | A cadeia ainda viola 12–70 | Aviso ao lado do resumo |

> **Sem vocabulário novo para os três últimos.** São os mesmos códigos que a `029` já usa para essas
> três condições. Criar `SEM_GERACOES_A_SUGERIR` e `SEM_ESTIMATIVA_DE_MRCA` daria dois nomes ao mesmo
> fato — a classe de defeito que este projeto já pagou caro para não repetir.

## 5. Requisitos Funcionais

| ID | Requisito | Prioridade | Critério de aceite | Confidência |
|----|-----------|------------|--------------------|-------------|
| RF-01 | `resumo_da_sugestao(resultado, documental)` devolve `{hiato, geracoes, motivo, rotulos}` sem tocar no grafo | Must | Com 25 cM e `a_up=2`, devolve hiato 3 e três rótulos `Geração 1..3` | 🟢 |
| RF-02 | `mermaid_da_sugestao(...)` devolve texto Mermaid do caminho com as gerações virtuais e a aresta rompida | Must | O texto contém `graph`, os nós do caminho, `Geração 1` e a aresta tracejada | 🟢 |
| RF-03 | O cartão renderiza o bloco colapsável **logo abaixo do diagrama documentado**, com o resumo no `<summary>` | Must | HTML do cartão contém o bloco depois de `grafo-do-registro`, com o resumo visível e um `div.mermaid` no corpo | 🟢 |
| RF-04 | O resumo em texto fica no título do bloco, visível sem clique | Must | O `<summary>` mostra "3 gerações sugeridas"; o texto não depende do diagrama | 🟢 |
| RF-05 | As cores e a aresta rompida seguem a paleta da `030` | Must | `classDef` com os três hexas e `linkStyle` tracejado vermelho | 🟢 |
| RF-06 | Sem geração a injetar, o cartão **em conflito** explica o motivo; os demais não | Must | `hiato = 0` num cartão em conflito produz a frase; num cartão validado, nada aparece | 🟢 |
| RF-07 | O diagrama documentado continua intacto | Must | `details.grafo-do-registro` e `result.mermaid_data` continuam no HTML | 🟢 |
| RF-08 | Nenhuma dependência nova e nada a instalar no container | Must | `requirements.txt` e `docker/*` intocados; o teste roda sem `dot` | 🟢 |
| RF-09 | O texto Mermaid é determinístico e escapado | Must | Duas chamadas idênticas; nome com aspas não quebra a gramática | 🟢 |
| RF-10 | Os testes cobrem os três casos (sugestão, hiato zero, sem estimativa), o desenho e o escape | Must | Suíte verde; um teste por caso | 🟢 |
| RF-11 | Docstrings explicam por que a tela não chama `arvore_sugerida` e por que Mermaid e não Graphviz | Should | Inspeção mostra as duas explicações e a citação ao custo da cópia | 🟡 |

## 6. Requisitos Não Funcionais

| Tipo | Requisito | Evidência ou justificativa | Confidência |
|------|-----------|----------------------------|-------------|
| Desempenho | O(Saltos) por cartão; nenhuma cópia do grafo, nenhum segundo parse | 142 cartões × O(V+E) seria inaceitável numa árvore de 35.460 pessoas | 🟢 |
| Dependência | Nada de Graphviz no servidor: o desenho é Mermaid no navegador | O container não tem `dot` e o `.dockerignore` é lista de permissão | 🟢 |
| Arquitetura | O emissor fica em `reporting/` e não importa `core` (ADR-34); os números chegam por parâmetro | O cartão já recebe `mrca_estimado` e `degrees` no dicionário | 🟢 |
| Determinismo | Mesma entrada, mesmo texto Mermaid | `RN-08` | 🟢 |
| Acessibilidade | O resumo em texto carrega a informação; o diagrama é complemento | `RN-05`; a tela já usa `visually-hidden` nos outros sinais | 🟢 |
| Compatibilidade | Mermaid 10 por CDN, já carregado pela tela | `index.html` (1246) | 🟢 |
| Testabilidade | O emissor é puro; o teste de tela renderiza o template real | Padrão das features `030` e `031` | 🟢 |
| Observabilidade | O motivo da ausência é dito em texto, não deduzido | `RN-06` | 🟢 |

## 7. Critérios de Aceitação

```gherkin
Cenário: cartão em conflito mostra a árvore sugerida
  Dado um resultado com veredito de erro, 25 cM e 2 gerações documentadas
  Quando o cartão é renderizado
  Então aparece o resumo com "3 gerações sugeridas"
  E aparece o diagrama com "Geração 1", "Geração 2" e "Geração 3"

Cenário: a geração virtual não tem nome de pessoa
  Dado o diagrama da árvore sugerida
  Quando os rótulos são inspecionados
  Então os nós virtuais são "Geração k"
  E nenhum nome novo de pessoa aparece

Cenário: a aresta rompida é visível no desenho
  Dado o diagrama da árvore sugerida
  Quando o texto Mermaid é inspecionado
  Então existe uma ligação tracejada em vermelho com o rótulo do desvio

Cenário: hiato zero é explicado no cartão em conflito
  Dado um cartão em conflito cujo cM estima as mesmas gerações que a árvore já tem
  Quando o cartão é renderizado
  Então aparece a frase de que não há gerações a sugerir
  E nenhum diagrama de sugestão é renderizado

Cenário: cartão sem conflito não ganha explicação
  Dado um cartão validado ou inconclusivo
  Quando o cartão é renderizado
  Então nenhuma frase de sugestão aparece
  E nenhum bloco de árvore sugerida é renderizado

Cenário: sem estimativa de MRCA
  Dado um resultado cujo cM não cai em nenhuma relação publicada
  Quando o cartão é renderizado
  Então a tela diz que não foi possível estimar
  E nenhum número é inventado

Cenário: o diagrama documentado continua
  Dado um cartão com caminho documental
  Quando a tela é renderizada
  Então o bloco do caminho documentado continua presente e igual

Cenário: a tela funciona sem Graphviz
  Dado que o binário "dot" não está instalado
  Quando a suíte roda
  Então os testes da árvore sugerida passam
  E nenhum teste novo é pulado

Cenário: nome com aspas não quebra o desenho
  Dado um nó cujo rótulo tem aspas e parêntese
  Quando o texto Mermaid é gerado
  Então o rótulo sai escapado
  E o texto continua válido para o Mermaid
```

## 8. Prioridade MoSCoW

| Item | MoSCoW | Justificativa |
|------|--------|---------------|
| RF-01, RF-02 | Must | Sem derivação e sem desenho não há o que mostrar |
| RF-03, RF-04 | Must | É a feature: ver a sugestão no cartão, em desenho e em texto |
| RF-05 | Must | A paleta é contrato entre a imagem e a tela |
| RF-06 | Must | O silêncio foi a causa da dúvida que abriu esta feature |
| RF-07 | Must | Não se substitui o que o operador já usa |
| RF-08, RF-09 | Must | Sem dependência nova e sem quebra de gramática |
| RF-10 | Must | `.reversa/principles.md#iii` |
| RF-11 | Should | Documentação exigida pelo projeto |
| Botão que baixa a imagem PNG | Won't (esta feature) | Exigiria o Graphviz no servidor e uma rota nova; é outra decisão |
| Substituir o diagrama documentado | Won't (esta feature) | São dois desenhos com propósitos diferentes |
| Editar a árvore a partir da tela | Won't (esta feature) | A sugestão é hipótese; alterar o GEDCOM pela tela é outro produto |

## 9. Esclarecimentos

### Sessão 2026-10-19

- **Q:** O que a árvore sugerida mostra no cartão?
  **R:** O **resumo no título do bloco**, visível sem clique, e o **diagrama colapsável** no corpo.
  Quem só quer saber quantas gerações foram sugeridas não precisa abrir; quem quer ver o caminho
  abre.
- **Q:** Onde o bloco fica?
  **R:** **Logo abaixo do diagrama documentado**, na mesma vizinhança e com a mesma mecânica de
  `details` + `toggle` que já existe. Assim o operador compara os dois desenhos sem rolar o cartão.
- **Q:** O que a tela diz quando não há geração a injetar?
  **R:** Uma **frase curta, só nos cartões em conflito**. Nos validados e inconclusivos, nada: a
  frase em 142 cartões trocaria um silêncio ruidoso por um ruído constante.
- **Consequência registrada:** com D3 restrita ao conflito, o cartão em conflito passa a ter sempre
  uma resposta — ou o bloco com as gerações, ou a frase que explica a ausência. Nenhum caso de
  erro fica mudo na tela.

## 10. Lacunas

Nenhuma lacuna aberta após a sessão de esclarecimentos de 2026-10-19. As três dúvidas iniciais
(conteúdo do bloco, lugar no cartão e o que dizer sem geração a injetar) foram resolvidas em §9.

## 11. Histórico de alterações

| Data | Alteração | Autor |
|------|-----------|-------|
| 2026-10-19 | Versão inicial gerada por `/reversa-requirements` | reversa |
| 2026-10-19 | Sessão de esclarecimentos: resumo no título + diagrama colapsável, abaixo do diagrama documentado, e frase de ausência só no conflito | reversa |

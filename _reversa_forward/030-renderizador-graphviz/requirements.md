# Requirements: renderizador Graphviz da árvore sugerida

> Identificador: `030-renderizador-graphviz`
> Data: `2026-10-18`
> Pasta da extração reversa: `_reversa_sdd/`
> Confidência: 🟢 CONFIRMADO, 🟡 INFERIDO, 🔴 LACUNA / DÚVIDA
> Documento pedido pelo operador em 2026-10-18. O literal `DESVIO DE CONEXÃO / QUEBRA DE LINHA`
> aparece sempre nesta forma, porque é o texto que vai para dentro da imagem e não pode ter duas
> grafias.
>
> **Sobre nomear a biblioteca.** O documento cita Graphviz porque o operador a exigiu no pedido. Ela
> **não** está declarada no `requirements.txt`. O binding Python **foi instalado no `.venv` em
> 2026-10-18 02:18 (versão 0.21)** — não por este pipeline —, e o binário `dot` continua **fora do
> `PATH`**. As duas coisas são medidas datadas: a ausência do binding foi verificada às 02:10 e
> deixou de valer oito minutos depois, quando o operador instalou o pacote. Por isso a dependência é
> assunto de §6 e de D2, e não um detalhe de implementação.

## 1. Resumo executivo

A feature `029` produz uma **árvore sugerida** — um grafo em que a junção provada errada foi
desacoplada e as gerações que faltam aparecem como nós virtuais. Hoje essa árvore só existe como
estrutura em memória: o operador não consegue vê-la nem mostrar a ninguém. Esta feature entrega o
renderizador Graphviz que transforma a sugestão em **imagem**: layout hierárquico limpo, cores por
classe de nó, aresta tracejada em vermelho marcando a quebra de linha e uma caixa com o resumo da
evidência genética, exportada em PNG ou SVG.

A entrega é um módulo de `reporting/` mais testes. Não há rota HTTP, não há persistência e a imagem
não é servida pela aplicação.

## 2. Contexto a partir do legado

| Fonte | Trecho relevante | Confidência |
|-------|------------------|-------------|
| `_reversa_sdd/architecture.md#3-componentes-e-estrutura-de-pacotes` | `reporting/` emite o diagrama e **não importa `core`**: recebe o domínio por parâmetro (ADR-34) | 🟢 |
| `_reversa_sdd/architecture.md#4-modelo-de-dados` | `None` significa "não sei / não existe"; a árvore não é duplicada no banco | 🟢 |
| `_reversa_sdd/domain.md#31-parentesco-documental` | Afinidade nunca é linhagem; a idade só é conferida no caminho direto | 🟢 |
| `_reversa_sdd/adrs/34-ciclos-quebrados-e-superficies-removidas.md` | O ciclo `core/` ↔ `reporting/` foi fechado; o renderizador recebe as consultas prontas | 🟢 |
| `_reversa_sdd/adrs/11-reorganizar-em-pacotes-por-responsabilidade.md` | Decidir o desenho é decisão de negócio e mora em `reporting/`, não no núcleo | 🟢 |
| `_reversa_sdd/adrs/13-fixar-dependencias-diretas.md` | Toda dependência direta entra **pinada** no `requirements.txt`, para uma instalação nova não trazer outra versão | 🟢 |
| `_reversa_sdd/dependencies.md` | **Graphviz não está entre as dependências** do projeto; `networkx`, `ged4py`, `pandas`, `flask`, `thefuzz`, `waitress`, `rapidfuzz`, `python-Levenshtein`, `psycopg2-binary` estão | 🟢 |
| `requirements.txt` | 9 pins de runtime; nenhum é `graphviz` | 🟢 |
| `docker/Dockerfile` | `python:3.14-slim`, instala **só** o `requirements.txt`; não há `apt-get` de pacote de sistema | 🟢 |
| `_reversa_sdd/addenda/029-desacoplamento-de-nos.md` | O contrato da árvore sugerida: `grafo`, `juncoes`, `geracoes_virtuais`, `hiato`, `arestas_removidas` | 🟢 |
| `_reversa_sdd/addenda/028-validador-de-dados-dna.md` | O resultado da validação traz `cm`, `mrca_estimado.geracoes` e o `status` de três valores | 🟢 |
| `src/reporting/mermaid_render.py` | O renderizador de tela: emite texto Mermaid e recebe `dominio` por parâmetro; tem contrato de escape de rótulo próprio | 🟢 |
| `_reversa_sdd/architecture.md#7-dividas-tecnicas-consolidadas` | `L-26`: `psycopg2` pinado e ausente do `.venv` — o import é **preguiçoso** para não derrubar a suíte | 🟢 |
| `.reversa/principles.md#i` | Dados reais nunca entram no versionamento; imagem com nome de pessoa viva é dado real | 🟢 |
| `.reversa/principles.md#iii` | Nenhuma mudança sem teste que a cubra | 🟢 |
| `_reversa_sdd/architecture.md#7-dividas-tecnicas-consolidadas` | `L-33`: arte que funciona no host e falha no container degrada em silêncio | 🟡 |

### 2.1 O que já existe e **não** será reimplementado

| Componente | O que já responde | Por que não basta |
|------------|-------------------|-------------------|
| `core.cirurgia_do_grafo` | Produz a árvore sugerida, com junções, gerações virtuais e arestas removidas | Não desenha nada |
| `application.correcao` | Lê GEDCOM + CSV e monta a sugestão por comparação | Não desenha nada |
| `reporting.mermaid_render` | Emite o diagrama Mermaid da tela | Mermaid é texto para o navegador; não gera arquivo de imagem nem tem as cores pedidas |
| `core.diagram_domain` | Resolve as consultas de layout ligadas à árvore | Entrega dados, não imagem |

### 2.2 A lacuna que esta feature fecha

1. **Nenhuma imagem é gerada.** O projeto inteiro produz texto (HTML, Mermaid, JSON) e nunca um
   arquivo de imagem derivado de um grafo.
2. **A sugestão da `029` não é apresentável.** Quem recebe `sugestao["grafo"]` precisa escrever
   código para enxergar qualquer coisa.
3. **Não há convenção visual.** Nó do doador, nó documental e geração virtual são hoje
   indistinguíveis a olho nu.
4. **A quebra de linha não é mostrada.** `arestas_removidas` sabe qual vínculo caiu, mas nada
   desenha a queda.

## 3. Personas e cenários de uso

| Persona | Objetivo | Cenário-chave |
|---------|----------|---------------|
| Operador / genealogista | Entender em uma imagem onde a linha quebrou | Vê o doador em verde, as gerações sugeridas em amarelo e a aresta vermelha tracejada com o rótulo da quebra |
| Auditor de dados | Anexar a evidência a um laudo | Exporta o SVG e cola no documento; a caixa de evidência traz cM, gerações e o motivo |
| Desenvolvedor do legado | Chamar o renderizador sem a borda HTTP | Chama a função a partir de um teste com a sugestão da `029` e um `tmp_path` |
| Revisor de privacidade | Garantir que a imagem não vaze para o repositório | Confere que a função grava só no destino informado e que o teste usa fixture sintética |

## 4. Regras de negócio novas ou alteradas

### 4.1 Definições operacionais

| Termo | Definição nesta feature |
|-------|--------------------------|
| **Nó base** | O nó do doador / kit ativo: `sugestao["doador"]["id"]`. |
| **Nó documental** | Pessoa que o GEDCOM declara, sem marca de geração virtual. |
| **Nó virtual** | Nó com `type="virtual"` criado pela `029` (`Geração 1..k`). |
| **Aresta rompida** | Cada item de `sugestao["arestas_removidas"]`: o vínculo que a cirurgia cortou. |
| **Caixa de evidência** | Nó de nota com o resumo `"{cM} cM, {gerações} gerações - {veredito}"`. |
| **Recorte** | O subconjunto desenhado: caminho do doador ao ancestral, o caminho até o match e a cadeia virtual. |
| **Renderizador** | A função que transforma a sugestão em arquivo `.png` ou `.svg`. |

**Siglas.** **GEDCOM** é o formato de árvore genealógica; **cM** é centiMorgan; **MRCA** é *Most
Recent Common Ancestor*; **DOT** é a linguagem de descrição de grafos do Graphviz.

### 4.2 Regras

1. **RN-01: desenha-se a árvore sugerida, não a árvore original.** A entrada é o dicionário da
   `029`; o grafo original do GEDCOM não é lido nem desenhado. 🟢
   - Origem no legado: `_reversa_sdd/addenda/029-desacoplamento-de-nos.md`
   - Tipo: nova

2. **RN-02: sem sugestão, não há imagem.** Se `sugestao["grafo"]` é `None` — status que não é erro,
   hiato não positivo, afinidade ou ausência de caminho —, o renderizador **não grava nada** e
   devolve `SEM_SUGESTAO_PARA_DESENHAR`. Não se desenha uma linha que não foi considerada quebrada. 🟢
   - Origem no legado: `_reversa_sdd/addenda/029-desacoplamento-de-nos.md` (códigos de aviso)
   - Tipo: nova

3. **RN-03: as cores são as do pedido, por classe de nó.** Nó base `#a8e6cf` (verde); nó documental
   `#f5f5f5` com borda `#666666` (cinza/branco); nó virtual `#ffd3b6` (amarelo). Nenhuma outra
   classe existe no desenho. 🟢
   - Origem no legado: pedido do operador de 2026-10-18
   - Tipo: nova

4. **RN-04: a aresta rompida é tracejada, vermelha e rotulada.** Cada aresta de
   `arestas_removidas` é redesenhada com `style=dashed`, `color=red` e
   `label="DESVIO DE CONEXÃO / QUEBRA DE LINHA"`. O rótulo é literal: é o que o operador lê na
   imagem. 🟢
   - Origem no legado: pedido do operador de 2026-10-18
   - Tipo: nova

5. **RN-05: o desenho é hierárquico e os nós de família não aparecem.** O layout é delegado ao
   `dot` com `rankdir=TB`; as arestas pessoa↔família são comprimidas em arestas **genitor→filho**,
   de modo que a imagem seja uma árvore descendente legível. A legenda declara a compressão. 🟢
   - Origem no legado: `_reversa_sdd/architecture.md#3-componentes-e-estrutura-de-pacotes`
     (decisão de layout em `reporting/`)
   - Tipo: nova (compressão e recorte confirmados em 2026-10-18, §9)

6. **RN-06: o recorte é o caminho, não a árvore inteira.** Entram o doador, a cadeia até o MRCA, o
   caminho do MRCA até o match, os nós virtuais e as arestas rompidas. O caminho vem de
   `documental["path"]["ids"]`, a pessoa do match de `documental["person_b"]` e as gerações virtuais
   de `sugestao["geracoes_virtuais"]`. Irmãos, cônjuges e primos fora do caminho ficam de fora: a
   árvore real tem 35.460 pessoas e a imagem precisa ser legível. 🟢
   - Origem no legado: `_reversa_sdd/architecture.md#4-modelo-de-dados` (35.460 pessoas)
   - Tipo: nova (recorte confirmado em 2026-10-18, §9)

7. **RN-07: a caixa de evidência traz cM, gerações e veredito.** Formato exato:
   `"{cm:.1f} cM, {geracoes:.1f} gerações - {veredito}"`, com ponto decimal, como no pedido
   (`21.6 cM, 5.7 gerações - Incompatibilidade Biológica`). `cm` vem de `resultado["cm"]` e
   `geracoes` de `resultado["mrca_estimado"]["geracoes"]`; sem um deles, o campo vira `—` e a caixa
   não inventa número. 🟡
   - Origem no legado: `_reversa_sdd/addenda/028-validador-de-dados-dna.md` (campos `cm` e
     `mrca_estimado`)
   - Tipo: nova

8. **RN-08: o veredito da caixa é uma frase de negócio, derivada do primeiro código crítico.**
   `PROFUNDIDADE_TEMPORAL_INCOMPATIVEL` → `Incompatibilidade Biológica`;
   `GENITOR_FORA_DA_JANELA_BIOLOGICA` → `Idade de genitor impossível`;
   `CM_INCOMPATIVEL_COM_PROFUNDIDADE` → `cM incompatível com a profundidade`;
   `MRCA_POSTERIOR_A_DESCENDENTE` → `MRCA posterior ao descendente`;
   `DOADOR_VIVO_EM_LINHA_INCOMPATIVEL` → `Doador vivo em linha incompatível`;
   `CONFLITO_CM_DOCUMENTAL` → `Conflito entre cM e documento`;
   qualquer outro → `Quebra de linha documental`. 🟡
   - Origem no legado: `_reversa_forward/029-desacoplamento-de-nos/requirements.md#44-codigos-de-aviso`
   - Tipo: nova

9. **RN-09: só PNG e SVG.** Outros formatos são recusados com `FORMATO_NAO_SUPORTADO`, sem gravar
   arquivo parcial. O formato é derivado da extensão do destino, e a extensão e o formato têm de
   concordar. 🟢
   - Origem no legado: pedido do operador de 2026-10-18
   - Tipo: nova

10. **RN-10: o destino é obrigatório e explícito.** A função recebe o caminho completo do arquivo e
    grava **apenas** ali. Nunca escolhe pasta, nunca grava em `src/uploads/`, nunca sobrescreve
    arquivo existente sem que o chamador peça. 🟢
    - Origem no legado: `.reversa/principles.md#i`;
      `_reversa_sdd/adrs/30-aposentar-em-vez-de-apagar.md`
    - Tipo: nova (destino explícito confirmado em 2026-10-18, §9)

11. **RN-11: o import do Graphviz é preguiçoso.** `import app` continua funcionando sem a
    dependência instalada; a falha aparece só quando o renderizador é chamado, como exceção de
    domínio com mensagem clara (`GRAPHVIZ_AUSENTE`, `DOT_AUSENTE`). 🟢
    - Origem no legado: `_reversa_sdd/architecture.md#7-dividas-tecnicas-consolidadas` (`L-26`);
      o precedente do `psycopg2` na feature `008`
    - Tipo: preservada (aplicação da mesma decisão)

12. **RN-12: o `.dot` gerado é determinístico.** Mesma sugestão produz o mesmo texto: nós e arestas
    em ordem explícita, sem depender da iteração de `set` nem da ordem de inserção do grafo. É o que
    permite testar o desenho sem comparar imagem. 🟢
    - Origem no legado: `.reversa/principles.md#iii`; `_reversa_sdd/domain.md#34-matching-difuso-de-nomes-o-cm-nao-decide-aceitacao`
    - Tipo: nova

13. **RN-13: rótulo é sempre escapado.** Todo texto de nó vai entre aspas duplas, com `\"` para
    aspas e `\\` para barra; nome com `&`, `<` ou `>` não vira HTML no Graphviz. 🟢
    - Origem no legado: `src/reporting/mermaid_render.py` (contrato de escape próprio, BUG-20260929-J6PQ)
    - Tipo: preservada (mesma preocupação, outro dialeto)

14. **RN-14: a imagem é derivada e não é versionada.** O arquivo gerado nunca é commitado, e os
    testes só produzem imagem a partir de fixture sintética, em diretório temporário. 🟢
    - Origem no legado: `.reversa/principles.md#i`
    - Tipo: nova

> **Princípios aplicados.** I (fixture sintética, imagem fora do versionamento), II (nenhum
> comportamento existente muda: o renderizador é um módulo novo), III (todo invariante com teste),
> IV (a compressão de família preserva a direção genitor→filho), V (o cM e as gerações vêm da `028`
> e da `029`, com a fonte já citada lá). Nenhum conflito com princípio ativo.

### 4.3 Valores de domínio e fontes

| Constante | Valor | Fonte | Confidência |
|-----------|-------|-------|-------------|
| Cor do nó base | `#a8e6cf` | Pedido do operador, 2026-10-18 | 🟢 |
| Cor do nó documental | `#f5f5f5` (borda `#666666`) | Pedido do operador ("cinza/branco"); o par foi fixado aqui para não haver duas leituras | 🟡 |
| Cor do nó virtual | `#ffd3b6` | Pedido do operador, 2026-10-18 | 🟢 |
| Cor da aresta rompida | `red` | Pedido do operador, 2026-10-18 | 🟢 |
| Rótulo da aresta rompida | `DESVIO DE CONEXÃO / QUEBRA DE LINHA` | Pedido do operador, 2026-10-18 | 🟢 |
| Formato da caixa de evidência | `{cm:.1f} cM, {geracoes:.1f} gerações - {veredito}` | Pedido do operador (exemplo `21.6 cM, 5.7 gerações - Incompatibilidade Biológica`) | 🟢 |
| Layout | `dot`, `rankdir=TB` | Pedido do operador ("hierárquico limpo") | 🟡 |
| Versão do `graphviz` (binding) | a fixar no `plan` | `requirements.txt` fixa todas as diretas; a versão entra pinada como as demais | 🟡 |

> **Sobre o ponto decimal.** O padrão do projeto em tela é vírgula decimal, mas o pedido escreveu
> `21.6 cM` e este número vai para dentro de uma imagem técnica. Fica o ponto, **exatamente como
> pedido**; trocar é decisão de outra feature, não ajuste escondido.

### 4.4 Códigos de erro

| Código | Quando aparece | Efeito |
|--------|----------------|--------|
| `SEM_SUGESTAO_PARA_DESENHAR` | `sugestao["grafo"]` é `None` | Nada é gravado; a mensagem repete o aviso da `029` |
| `FORMATO_NAO_SUPORTADO` | Extensão/`formato` diferente de `png` ou `svg` | Nada é gravado |
| `DESTINO_OBRIGATORIO` | Destino vazio, sem nome de arquivo ou sem pasta existente | Nada é gravado |
| `GRAPHVIZ_AUSENTE` | O pacote `graphviz` não está instalado | Nada é gravado; a mensagem diz como instalar |
| `DOT_AUSENTE` | O binário `dot` não está no `PATH` | Nada é gravado; a mensagem aponta o Graphviz de sistema |

> **O segundo é o caminho esperado hoje.** Medido em 2026-10-18: o binding está instalado no `.venv`
> (0.21, instalado às 02:18) e o binário **não** está no `PATH`. Decidido em §9: a feature **falha
> com erro claro** nesse caso, em vez de degradar para `.dot`. A mensagem de `DOT_AUSENTE` cita a
> página de download do Graphviz e a necessidade de reiniciar o terminal depois de instalar, porque o
> `PATH` do Windows não se atualiza sozinho.

### 4.5 O que a imagem mostra

```
        ┌──────────────┐
        │   Doador     │   #a8e6cf  (nó base)
        └──────┬───────┘
               │            aresta normal: filiação documental
        ┌──────▼───────┐
        │    Pai       │   #f5f5f5  (documental)
        └──────┬───────┘
               ┊            ┊ tracejada vermelha
               ┊            ┊ label: DESVIO DE CONEXÃO / QUEBRA DE LINHA
        ┌──────▼───────┐
        │  Geração 1   │   #ffd3b6  (virtual)
        └──────┬───────┘
        ┌──────▼───────┐
        │  Geração 2   │   #ffd3b6
        └──────┬───────┘
        ┌──────▼───────┐
        │   MRCA       │   #f5f5f5
        └──────────────┘

  ┌─────────────────────────────────────────────────────────────┐
  │ Evidência genética                                          │
  │ 21.6 cM, 5.7 gerações - Incompatibilidade Biológica          │
  └─────────────────────────────────────────────────────────────┘
```

A caixa de evidência é um nó de nota (`shape=note`) ligado ao nó do doador por aresta invisível,
para não confundir com parentesco.

## 5. Requisitos Funcionais

| ID | Requisito | Prioridade | Critério de aceite | Confidência |
|----|-----------|------------|--------------------|-------------|
| RF-01 | `renderizar_arvore_sugerida(sugestao, resultado, documental, destino, formato=None)` gera a imagem e devolve o caminho do arquivo | Must | Com a sugestão de fixture e destino em `tmp_path`, o arquivo existe e a função devolve o caminho. O teste é **pulado com motivo** quando o `dot` não está instalado; o caminho de falha (`DOT_AUSENTE`) roda sempre | 🟢 |
| RF-02 | `texto_dot(sugestao, resultado, documental)` devolve o texto DOT sem tocar disco nem exigir o Graphviz | Must | A função não importa `graphviz` e o texto contém `digraph` e os nós esperados | 🟢 |
| RF-03 | O nó base recebe `#a8e6cf`, o documental `#f5f5f5` e o virtual `#ffd3b6` | Must | No texto DOT, cada nó tem o `fillcolor` da sua classe | 🟢 |
| RF-04 | Cada aresta rompida vira aresta tracejada vermelha com o rótulo literal | Must | O texto DOT tem `style=dashed`, `color=red` e `label="DESVIO DE CONEXÃO / QUEBRA DE LINHA"` para cada aresta removida | 🟢 |
| RF-05 | A caixa de evidência traz cM, gerações e veredito no formato da RN-07 | Must | Com 21.6 cM e 5.7 gerações, o texto contém `21.6 cM, 5.7 gerações - Incompatibilidade Biológica` | 🟢 |
| RF-06 | Só PNG e SVG são aceitos; o resto é recusado sem gravar arquivo | Must | Formato `pdf` devolve `FORMATO_NAO_SUPORTADO` e o diretório continua vazio | 🟢 |
| RF-07 | Sem sugestão, nada é gravado e o erro é `SEM_SUGESTAO_PARA_DESENHAR` | Must | `sugestao["grafo"] = None` não cria arquivo e a mensagem cita o motivo da `029` | 🟢 |
| RF-08 | O destino é obrigatório e é o único lugar escrito | Must | Destino vazio devolve `DESTINO_OBRIGATORIO`; nenhum arquivo aparece em `src/uploads/` | 🟢 |
| RF-09 | O renderizador não desenha os nós de família e comprime a filiação em arestas genitor→filho | Should | O texto DOT não contém nó `@F..@` nem `shape=point` de família | 🟡 |
| RF-10 | O texto DOT é determinístico | Must | Duas chamadas com a mesma sugestão produzem strings idênticas | 🟢 |
| RF-11 | Nome com aspas, `&` e acento não quebra o DOT | Must | Um nome com `"` produz `\"` no texto e o Graphviz aceita | 🟢 |
| RF-12 | Ausência do binding ou do binário produz erro de domínio claro e nenhum arquivo parcial | Must | Com `graphviz` indisponível, a chamada sobe `GRAPHVIZ_AUSENTE` e o diretório fica vazio | 🟢 |
| RF-13 | Os testes cobrem as três cores, a aresta rompida, a caixa, os cinco códigos de erro e o determinismo | Must | A suíte do projeto passa no `.venv` e cada código de §4.4 tem ao menos um teste | 🟢 |
| RF-14 | Docstrings explicam a compressão de família, o formato do rótulo e a razão do import preguiçoso | Should | Inspeção mostra as três explicações e a citação ao precedente `L-26` | 🟡 |

## 6. Requisitos Não Funcionais

| Tipo | Requisito | Evidência ou justificativa | Confidência |
|------|-----------|----------------------------|-------------|
| Arquitetura | Fica em `reporting/` e **não importa `core`**: recebe a sugestão pronta por parâmetro | `ADR-34` fechou o ciclo `core/` ↔ `reporting/` | 🟢 |
| Dependência | `graphviz` entra pinado em `requirements.txt`, como as demais diretas; o binário `dot` é dependência de **sistema** e precisa estar documentado | `requirements.txt` fixa todas as diretas; `dot` não é pacote Python | 🟡 |
| Inicialização | Import preguiçoso do binding: `import app` e a suíte funcionam sem a dependência | Precedente `psycopg2`/`L-26`: o driver ausente do `.venv` não pode derrubar nada | 🟢 |
| Container | A renderização é de **host**. O container não recebe `graphviz` nem `dot` nesta feature, e isso fica declarado na docstring | `docker/Dockerfile` instala só o `requirements.txt`; `.dockerignore` é lista de permissão; `L-33` mostra que a falha silenciosa no container é o risco | 🟡 |
| Determinismo | Mesmo texto DOT para a mesma entrada; ordenações explícitas | `RN-12`; o projeto já fechou a dependência de `PYTHONHASHSEED` no matching | 🟢 |
| Desempenho | O recorte tem dezenas de nós, não 35 mil; a geração do DOT é O(nós+arestas) do recorte | `RN-06`; o desenho da árvore inteira seria ilegível e lento | 🟢 |
| Privacidade | Fixture sintética nos testes; a imagem não é versionada e só é gravada no destino informado | `.reversa/principles.md#i`; `RN-10`, `RN-14` | 🟢 |
| Compatibilidade | Python 3.14.6 do `.venv`; `graphviz` precisa de wheel compatível; Windows e Linux | `.venv` é o interpretador oficial desde 2026-10-05 | 🟡 |
| Observabilidade | Erro de domínio com mensagem acionável, sem `print` e sem log de nome de pessoa | Padrão do projeto para erros de entrada | 🟢 |
| Testabilidade | `texto_dot` é puro e testável sem Graphviz; o teste de renderização é pulado com motivo declarado quando o `dot` não existe | `pytest.mark.skipif` já usado no projeto para dependência opcional; sem isso, a suíte ficaria vermelha em máquina sem Graphviz, o que esconde regressão de verdade | 🟢 |

## 7. Critérios de Aceitação

```gherkin
Cenário: sugestão de quebra vira imagem
  Dado uma sugestão da feature 029 com grafo, junções e gerações virtuais
  E um destino "saida/arvore.png" em diretório existente
  Quando o renderizador roda
  Então o arquivo "saida/arvore.png" existe
  E a função devolve esse caminho

Cenário: as três cores aparecem no desenho
  Dado uma sugestão com doador, nós documentais e gerações virtuais
  Quando o texto DOT é gerado
  Então o nó do doador tem fillcolor "#a8e6cf"
  E os nós documentais têm fillcolor "#f5f5f5"
  E as gerações virtuais têm fillcolor "#ffd3b6"

Cenário: a aresta rompida é tracejada, vermelha e rotulada
  Dado uma sugestão cuja aresta removida liga a família de junção ao ancestral
  Quando o texto DOT é gerado
  Então existe uma aresta com style=dashed e color=red
  E o rótulo dela é exatamente "DESVIO DE CONEXÃO / QUEBRA DE LINHA"

Cenário: a caixa de evidência traz o resumo genético
  Dado um resultado de validação com 21.6 cM e 5.7 gerações estimadas
  E o código crítico PROFUNDIDADE_TEMPORAL_INCOMPATIVEL
  Quando o texto DOT é gerado
  Então a caixa de evidência contém "21.6 cM, 5.7 gerações - Incompatibilidade Biológica"

Cenário: formato não suportado
  Dado um destino "arvore.pdf"
  Quando o renderizador roda
  Então a chamada falha com FORMATO_NAO_SUPORTADO
  E nenhum arquivo é criado

Cenário: sugestão ausente
  Dado uma sugestão com grafo nulo
  Quando o renderizador roda
  Então a chamada falha com SEM_SUGESTAO_PARA_DESENHAR
  E nenhum arquivo é criado

Cenário: Graphviz não instalado
  Dado que o binário "dot" não está no PATH
  Quando o renderizador roda
  Então a chamada falha com DOT_AUSENTE
  E nenhum arquivo parcial fica no destino

Cenário: o desenho é determinístico
  Dado a mesma sugestão e o mesmo resultado
  Quando o texto DOT é gerado duas vezes
  Então as duas strings são idênticas

Cenário: nome com aspas não quebra o DOT
  Dado um nó cujo rótulo contém aspas e "&"
  Quando o texto DOT é gerado
  Então as aspas aparecem escapadas
  E o texto continua sendo um DOT válido

Cenário: nenhum arquivo fora do destino
  Dado um destino no diretório temporário da suíte
  Quando o renderizador roda
  Então nenhum arquivo novo aparece em "src/uploads/"
```

## 8. Prioridade MoSCoW

| Item | MoSCoW | Justificativa |
|------|--------|---------------|
| RF-01, RF-02 | Must | Sem texto DOT e sem arquivo não existe a feature |
| RF-03 | Must | É o requisito 2 do pedido (estilização condicional) |
| RF-04 | Must | É o coração visual: a quebra tem de ser visível |
| RF-05 | Must | É o requisito 3 do pedido (resumo da evidência) |
| RF-06, RF-07, RF-08 | Must | Recusas que evitam arquivo errado ou parcial |
| RF-10, RF-11 | Must | Determinismo e escape: sem eles o teste não existe e o desenho quebra com nome real |
| RF-12 | Must | Import preguiçoso é decisão vigente do projeto |
| RF-09 | Should | Sem a compressão o desenho fica poluído, mas a imagem ainda existe |
| RF-13 | Must | `.reversa/principles.md#iii` |
| RF-14 | Should | Documentação exigida pelo projeto |
| Rota HTTP para baixar a imagem | Won't (esta feature) | O pedido é o módulo; expor imagem com nome de pessoa viva na rede é decisão de segurança separada |
| CLI que escolhe a pasta do arquivo | Won't (esta feature) | Decidido em §9: o destino é parâmetro obrigatório, e uma pasta padrão seria mais uma política para manter |
| Degradar para `.dot` quando faltar o Graphviz | Won't (esta feature) | Decidido em §9: falha clara em vez de um arquivo de texto chamado "imagem" |
| Renderizar dentro do container | Won't (esta feature) | Exigiria `apt-get install graphviz` no `Dockerfile`; decisão de infraestrutura separada (§9) |
| Exportar PDF | Won't (esta feature) | O pedido nomeia PNG/SVG; PDF seria formato a mais sem uso declarado |

## 9. Esclarecimentos

### Sessão 2026-10-18

- **Q:** Como a imagem sai do renderizador?
  **R:** A função **grava no destino informado** e devolve o caminho do arquivo. Quem chama escolhe a
  pasta; o renderizador nunca decide onde escrever, nunca grava em `src/uploads/` e nunca sobrescreve
  arquivo existente sem pedido explícito. Sem CLI e sem rota HTTP nesta feature.
- **Q:** O que fazer quando o Graphviz (binding ou binário `dot`) não está instalado?
  **R:** **Falhar com erro claro** (`GRAPHVIZ_AUSENTE` / `DOT_AUSENTE`) e não gerar nada. Não há
  degradação para `.dot` nesta entrega: um arquivo de texto chamado "imagem" seria pior do que uma
  falha honesta, e o pedido é PNG/SVG. A dependência entra pinada no `requirements.txt`, e o binário
  de sistema fica documentado no `onboarding.md`.
- **Q:** O que entra na imagem?
  **R:** **Só o recorte do caminho** — doador, cadeia até o MRCA, caminho do MRCA até o match, as
  gerações virtuais e as arestas rompidas. Irmãos, cônjuges e primos fora do caminho não entram. A
  árvore inteira está descartada: com 35.460 pessoas a imagem seria ilegível e lenta.
- **Consequência registrada, e ela é desconfortável:** enquanto o `dot` não estiver instalado nesta
  máquina, o teste que realmente gera a imagem **é pulado**. O que fica coberto é o texto DOT (cores,
  aresta rompida, caixa de evidência, escape, determinismo) e o caminho de falha `DOT_AUSENTE`. Isso
  precisa aparecer no relatório do `/reversa-coding` como cobertura parcial declarada, não como
  "tudo verde".

## 10. Lacunas

Nenhuma lacuna aberta após a sessão de esclarecimentos de 2026-10-18. As três dúvidas iniciais
(forma de entrega, comportamento sem Graphviz e recorte desenhado) foram resolvidas em §9.

## 11. Histórico de alterações

| Data | Alteração | Autor |
|------|-----------|-------|
| 2026-10-18 | Versão inicial gerada por `/reversa-requirements` | reversa |
| 2026-10-18 | Sessão de esclarecimentos: destino explícito, falha clara sem Graphviz e recorte do caminho; cobertura parcial declarada | reversa |
| 2026-10-18 | `documental` entra na assinatura das duas funções: o caminho e a pessoa do match não estão no contrato da `029`, e sem eles o recorte da RN-06 não existe | reversa |

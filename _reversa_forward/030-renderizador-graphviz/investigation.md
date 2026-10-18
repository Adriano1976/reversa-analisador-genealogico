# Investigation: renderizador Graphviz da árvore sugerida

> Identificador: `030-renderizador-graphviz`
> Data: `2026-10-18`
> Escopo: por que o DOT é montado à mão, por que não `pydot` nem Mermaid, como o recorte é
> reconstruído e o que foi medido no ambiente antes de planejar.

## 1. Estado do ambiente, medido antes de planejar

| Verificação | Comando | Resultado em 2026-10-18 |
|-------------|---------|--------------------------|
| Binding Python | `.venv\Scripts\python -c "import graphviz"` | **instalado: 0.21**, em `site-packages`, criado às **02:18** — não por este pipeline (às 02:10 o mesmo comando dava `ModuleNotFoundError`) |
| Binário de sistema | `Get-Command dot` | **não está no `PATH`** |
| Pin no runtime | `requirements.txt` | 9 dependências, nenhuma é `graphviz` |
| Imagem Docker | `docker/Dockerfile` | `python:3.14-slim` + `pip install -r requirements.txt`; nenhum `apt-get` de pacote de sistema |

> **A medição tem hora, e a hora importou.** A primeira verificação (02:10) dizia que o binding não
> existia; a segunda (02:21) dizia que sim, versão 0.21, com o diretório criado às 02:18. O ambiente
> mudou **no meio do pipeline** — o pacote foi instalado de fora. Registrar o instante da medição não
> é preciosismo: sem ele, este documento afirmaria algo falso e o plano pinaria uma versão inventada.

**Consequência para o plano:** o caminho de falha que qualquer execução vai encontrar é `DOT_AUSENTE`
— o binário de sistema —, não `GRAPHVIZ_AUSENTE`. E a versão do pin já é conhecida: **0.21**.

## 2. Por que o DOT é montado à mão

`graphviz.Digraph` é um construtor de grafo que serializa para DOT e chama o binário. Usá-lo em tudo
seria idiomático, mas amarraria o **teste do desenho** ao pacote — e o pacote não está instalado.
Montar a string à mão custa cerca de 40 linhas e dá três ganhos:

1. **Testabilidade sem dependência.** Cores, arestas, rótulos e escape são verificados por igualdade
   de string, sem `dot`, sem `pip install`, em qualquer máquina.
2. **Determinismo sob controle.** A ordem dos nós e das arestas é a que o código escrever; com
   `Digraph`, parte da ordem vem da inserção no objeto e o texto fica menos previsível entre versões.
3. **Escape explícito.** O contrato de escape fica no módulo, como já acontece em
   `reporting/mermaid_render.py` desde o `BUG-20260929-J6PQ`.

O pacote continua sendo usado — mas só para **executar** o `dot` sobre o texto pronto.

## 3. Alternativas avaliadas

| # | Abordagem | Por que foi descartada (ou escolhida) |
|---|-----------|----------------------------------------|
| A | `graphviz.Digraph` para construir e renderizar | Exigiria o pacote até para testar o desenho; e o texto depende da versão do pacote |
| B | `pydot` + `dot` | Troca uma dependência por outra e não resolve a ausência do binário; API menos previsível para atributos |
| C | Reimplementar o desenho em SVG, sem Graphviz | Layout hierárquico é um projeto inteiro; contradiz o pedido |
| D | Mermaid, reaproveitando `mermaid_render` | Mermaid é texto para o navegador; cores por classe e export de PNG exigiriam um renderizador de Mermaid no servidor |
| E | DOT à mão + `graphviz` só para executar o `dot` | **Escolhida.** Testa o desenho sem dependência e mantém o export real |
| F | Gravar `.dot` e deixar o operador renderizar | Recusada em §9: um arquivo de texto chamado "imagem" é pior que uma falha honesta |

## 4. Como o recorte é reconstruído

O grafo da `029` é **bipartido**: as arestas ligam pessoa↔família, e a direção genitor→filho não
está nelas — está no registro da família, que `reporting/` não pode ler sem importar `core` (ADR-34).
Duas saídas foram consideradas:

| Saída | Problema |
|-------|----------|
| Percorrer o grafo e inferir a direção pela distância ao ancestral | Funciona no caminho linear, mas exige BFS e um critério de desempate; e a cadeia virtual tem nós sem registro |
| Reconstruir do `documental` + `sugestao` | **Escolhida.** O caminho já vem ordenado (`path.ids`), o ancestral é conhecido (`common_ancestor`), as gerações virtuais já vêm com `ordem` e `lado`, e as junções já trazem `pai_id`/`filho_id` |

A direção sai da posição: no trecho antes do ancestral o caminho sobe (filho → pai), então a aresta
desenhada é a inversa (pai → filho); depois do ancestral o caminho desce, e a aresta é a própria
ordem. Isso está escrito na função e testado com o caminho real da fixture.

## 5. Escape no DOT

A gramática do DOT aceita `label="texto"` com escapes de barra invertida (`\"` e `\\`). O modo
`label=<texto>` é HTML e muda a gramática: um nome de pessoa com `<`, `>` ou `&` vira tag ou entidade,
e o desenho quebra — ou, pior, renderiza algo que não é o nome.

Decisão: **sempre aspas**, com `\` e `"` escapados, e sem modo HTML. Nome de pessoa é dado de
entrada; tratar texto de entrada como marcação é a classe de defeito que o contrato de escape do
Mermaid já fechou uma vez neste projeto.

## 6. Formatos e o que o `dot` garante

| Formato | Extensão | Observação |
|---------|----------|------------|
| PNG | `.png` | raster; bom para colar em documento e para visualização rápida |
| SVG | `.svg` | vetor; melhor para laudo e para zoom |

`dot` aceita dezenas de formatos; a feature restringe a dois porque foi o pedido, e um formato a mais
seria superfície sem uso declarado. Formato e extensão têm de concordar: `destino="x.png"` com
`formato="svg"` é erro, não conversão silenciosa.

## 7. Cores e legibilidade

| Classe | `fillcolor` | Observação |
|--------|-------------|------------|
| Nó base | `#a8e6cf` | verde claro do pedido; texto escuro mantém contraste |
| Documental | `#f5f5f5` com borda `#666666` | branco quase puro precisa de borda, senão some no fundo branco do PNG |
| Virtual | `#ffd3b6` | pêssego do pedido; `Geração k` em texto escuro |

`fontcolor` fixo em `#333333` para não depender do tema do Graphviz. As cores são do pedido e não
serão "melhoradas": trocar cor sem pedido é o tipo de ajuste que ninguém percebe e todo mundo herda.

## 8. Dependência: o que entra no `requirements.txt`

Segundo o `ADR-13`, toda dependência direta entra pinada. A versão só pode ser fixada **depois** de
instalar, porque hoje não há nenhuma instalada — o plano fixa o procedimento, e o coding fixa o
número. O binário `dot` **não** é pacote Python e não entra no `requirements.txt`; ele é dependência
de sistema, documentada no `onboarding.md`.

O import é preguiçoso (dentro da função), pelo mesmo motivo do `psycopg2` (`L-26`): uma dependência
ausente não pode derrubar `import app` nem a suíte inteira.

## 9. Fatos medidos no código

| Fato | Onde |
|------|------|
| `reporting/` **não** importa `core`; recebe o domínio por parâmetro | `src/reporting/mermaid_render.py` (docstring) |
| Existe contrato de escape de rótulo próprio, com bug registrado | `reporting/mermaid_render.py`; `BUG-20260929-J6PQ` |
| `sugestao["geracoes_virtuais"]` traz `id`, `label`, `lado`, `ordem` | `src/core/cirurgia_do_grafo.py` |
| `sugestao["juncoes"]` traz `familia_id`, `pai_id`, `filho_id`, `lado` | idem |
| `sugestao["arestas_removidas"]` guarda pares **com id de família** | idem |
| `resultado["cm"]` e `resultado["mrca_estimado"]["geracoes"]` existem no contrato da `028` | `src/core/validator.py` |
| `documental["path"]["ids"]` vem ordenado doador → MRCA → match | `src/core/documentary_relationship.py` |

## 10. Fontes externas

- Graphviz, atributos de nó e de aresta (`fillcolor`, `style`, `color`, `label`):
  <https://graphviz.org/doc/info/attrs.html>
- Graphviz, formatos de saída suportados: <https://graphviz.org/docs/outputs/>
- Graphviz, gramática do DOT e regras de aspas: <https://graphviz.org/doc/info/lang.html>
- Pacote `graphviz` para Python (só o binding; requer o binário):
  <https://graphviz.readthedocs.io/en/stable/>
- Download do Graphviz (instalador de sistema, Windows/Linux/macOS):
  <https://graphviz.org/download/>
- `ADR-13` do projeto, fixação de dependências diretas:
  `_reversa_sdd/adrs/13-fixar-dependencias-diretas.md`

## 11. Lacunas de investigação

- **Não foi medido** o tempo de renderização de um caminho longo com `dot`, porque não há `dot`
  nesta máquina. O recorte é pequeno (dezenas de nós), então o risco é baixo, mas fica registrado.
- **Não foi verificado** se a wheel do `graphviz` tem suporte declarado a Python 3.14. O pacote é
  Python puro, o que torna o risco baixo; o coding confirma na instalação.

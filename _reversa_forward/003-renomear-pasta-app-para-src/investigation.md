# Investigation: renomear a raiz da aplicação de `analisador-genealogico/` para `src/`

> Identificador: `003-renomear-pasta-app-para-src`
> Data: `2026-10-02`
> Requirements: `_reversa_forward/003-renomear-pasta-app-para-src/requirements.md`
> Confidência: 🟢 CONFIRMADO, 🟡 INFERIDO, 🔴 LACUNA

## 1. Pesquisa de fundo

### 1.1. O que exatamente muda, em termos de mecânica de importação

O diretório `analisador-genealogico/` não é um pacote importável: não tem arquivo de inicialização, e o nome contém hífen, que não é expressável na sintaxe de importação. O que existe é uma **raiz de caminho**: um diretório colocado na lista de busca de módulos, dentro do qual vivem o módulo de entrada e o pacote do núcleo.

Três fatos foram medidos neste workspace em 2026-10-02, e sustentam a decisão:

| Verificação | Resultado | Leitura |
|---|---|---|
| `import analisador-genealogico` | erro de sintaxe | O nome não é expressável na linguagem |
| `importlib.import_module("analisador-genealogico")` | **carrega**, com `__file__` nulo | O diretório é um pacote de espaço de nomes implícito |
| `reconstructed.upload` e `analisador-genealogico.reconstructed.upload` | dois objetos de módulo distintos, com **dois estados globais independentes** (`a.people is b.people` → falso) | A mesma lógica pode existir duas vezes em memória, com dois grafos diferentes |

O terceiro fato é o achado que importa: não é um defeito ativo — nada no projeto importa pelo caminho com hífen —, mas é uma armadilha latente de duplicação de estado. Ela deixa de ser possível com a raiz renomeada para `src`, cujo nome também não é importável, mas que ao menos não se confunde com o nome de um pacote (RN-01).

### 1.2. Por que o custo não está no código

Como o nome do pacote do núcleo não muda, **nenhuma linha de `import` é tocada**. Os módulos continuam sendo alcançados pelo mesmo nome. O que muda é o valor que aponta para a raiz de caminho, em três lugares vivos e em oito scripts de instrumentação. E o aplicativo não muda em nada: a pasta de upload é ancorada no próprio arquivo do aplicativo e o servidor web resolve os templates pelo diretório do arquivo de entrada — ambos acompanham o diretório.

## 2. Alternativas avaliadas

| # | Alternativa | Avaliação | Veredito |
|---|---|---|---|
| A | Renomear a raiz para `src/`, mantendo a estrutura interna | Menor superfície de mudança; preserva os contratos; resolve o objetivo declarado | **Adotada** |
| B | `src/` contendo um pacote de nome importável, com metadados de empacotamento e instalação editável | Eliminaria as 16 inserções de caminho nos testes e a configuração de caminho do analisador estático; é o destino natural da convenção | **Adiada pelo usuário** para feature própria (resposta 2c da sessão de esclarecimentos) |
| C | Renomear também o pacote do núcleo | Fora de escopo, e invalidaria os instrumentos congelados do comparador de paridade, que importam o pacote pelo nome atual | Descartada |
| D | Manter o nome atual e corrigir apenas a documentação | Não entrega o objetivo: a árvore continuaria nomeada como o produto | Descartada |
| E | Tornar o diretório atual importável | Impossível: o hífen não é expressável na sintaxe de importação | Descartada por impossibilidade |

### 2.1. Alternativa avaliada e não adotada: configuração de caminho do pytest

A documentação do pytest recomenda, para o layout com raiz de código em subdiretório, declarar o caminho na própria configuração (`pythonpath = ["src"]`) em vez de inserir o caminho em cada arquivo de teste. A versão instalada neste ambiente (**pytest 9.1.1**) suporta a opção, e adotá-la apagaria as 16 inserções dos 8 arquivos de teste.

**Não foi adotada**, por dois motivos objetivos:

1. Contraria o requisito não funcional de testabilidade aprovado, que exige que a suíte rode a partir da raiz **sem alteração do arquivo de configuração do pytest**.
2. Faz parte do mesmo pacote de trabalho da alternativa B (pacote instalável), que o usuário adiou explicitamente. Adotá-la agora misturaria duas mudanças estruturais e ampliaria a superfície de reversão.

Fica registrada como o passo natural da feature seguinte.

## 3. Padrões aplicáveis

- **Raiz de código em subdiretório** — o diretório que contém o código importável fica separado da raiz do repositório, que guarda configuração, testes e documentação. É a convenção que motiva a mudança.
- **Superfície de compatibilidade preservada** — o projeto já pratica isso: `path_search.py` e `dna_analysis.py` são fachadas que reexportam o que era definido neles antes da separação por responsabilidade, justamente para não quebrar consumidores. Esta feature estende o mesmo cuidado aos scripts de instrumentação.
- **Renomeação atômica de diretório** — uma única operação de renomeação, em vez de recriar a árvore, o que preserva o histórico por arquivo e evita a janela de duplicação.
- **Medir antes e depois** — o princípio II do projeto exige comparação de comportamento. A medição da linha de base é um passo do plano, não uma consequência dele.

## 4. Fontes externas

Consultadas em 2026-10-02:

| Fonte | Uso nesta feature |
|---|---|
| PyPA — *src layout vs flat layout* — https://packaging.python.org/en/latest/discussions/src-layout-vs-flat-layout/ | Define as duas convenções e o critério de "código destinado a ser importado" que separa uma da outra |
| pytest — *Good Integration Practices* — https://docs.pytest.org/en/stable/explanation/goodpractices.html | Recomenda a raiz de código em subdiretório com o modo de importação padrão; documenta a opção de caminho na configuração (avaliada em §2.1) |
| PEP 420 — *Implicit Namespace Packages* — https://peps.python.org/pep-0420/ | Explica por que um diretório sem arquivo de inicialização é importável como pacote de espaço de nomes, que é o que sustenta o achado de §1.1 |

## 5. Pontos em aberto para o futuro (não bloqueiam esta feature)

1. **Pacote instalável** (alternativa B) — tornaria o projeto instalável e dispensaria os caminhos inseridos à mão. Foi adiado por decisão do usuário.
2. **Caminho na configuração do pytest** (§2.1) — o par natural da alternativa B.
3. **Rótulo da raiz de código na documentação de extração** — a extração registra o diretório como o "módulo" do sistema analisado; depois da renomeação, esse rótulo passa a ser `src`, que é um nome de papel e não de produto. Corrigir isso depende de uma re-extração, e por ora fica com o adendo.
4. **Publicação do mini-site** — o fluxo de publicação existente dispara para uma branch diferente da branch principal do repositório e, por isso, não roda. Defeito pré-existente, fora de escopo.

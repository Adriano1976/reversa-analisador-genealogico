# Legacy Impact: renderizador Graphviz da árvore sugerida

> Identificador: `030-renderizador-graphviz`
> Data: `2026-10-18`
> Cenário: **legado** (âncora em `_reversa_sdd/architecture.md`, `_reversa_sdd/dependencies.md` e
> `_reversa_sdd/adrs/`)

## 1. Arquivos afetados

| Arquivo afetado | Componente | Tipo | Severidade | Justificativa |
|-----------------|------------|------|------------|---------------|
| `src/reporting/visualizer.py` | `reporting.visualizer` | componente-novo | HIGH | Primeiro emissor de **imagem** do projeto; monta DOT, comprime famílias e exporta PNG/SVG |
| `requirements.txt` | `dependencies` | regra-alterada | HIGH | Décima dependência de runtime, pinada em `graphviz==0.21`; o binário `dot` é dependência de sistema e não vem do `pip` |
| `tests/fixtures/sugestao_para_desenho.py` | `tests.fixtures` | artefato-novo | LOW | Sugestão sintética independente da `029`; nenhum dado real |
| `tests/test_visualizer.py` | `tests` | artefato-novo | LOW | 28 testes de DOT, cores, aresta rompida, caixa e recusas |
| `tests/test_fronteira_do_visualizer.py` | `tests` | artefato-novo | LOW | 3 testes de fronteira por AST |
| `tests/test_visualizer_integracao.py` | `tests` | artefato-novo | LOW | 1 teste fim-a-fim (validação → sugestão → DOT) |
| `tests/test_visualizer_render.py` | `tests` | artefato-novo | LOW | 2 testes de renderização real, **pulados** sem `dot` |

**Arquivos que NÃO mudaram:** `src/app.py`, `src/templates/index.html`, `src/assets/app.css`,
`src/reporting/mermaid_render.py`, `init.sql`, `docker/Dockerfile`, `docker-compose.yml`,
`.dockerignore`, `src/core/*` e todas as tabelas do PostgreSQL.

## 2. Diff conceitual por componente

### 2.1 `reporting.visualizer` (novo)

O projeto emite texto — HTML, Mermaid, JSON — e nunca uma imagem. Este componente é o primeiro
que produz **arquivo binário derivado de grafo**, e por isso carrega três decisões de fronteira:

- **não importa `core`** (ADR-34): a direção genitor→filho não está na aresta bipartida, então o
  desenho é **reconstruído** do caminho documental, das gerações virtuais e das junções;
- **não importa `graphviz` no topo**: o import é preguiçoso, como o do `psycopg2` (`L-26`), para
  que `import app` e a suíte não dependam do pacote;
- **o DOT é escrito à mão**: só o binário é chamado pelo pacote, o que torna o desenho testável
  em máquina sem Graphviz — que é o estado atual.

Complementos que a imagem carrega: cores por classe (`#a8e6cf` base, `#f5f5f5` documental,
`#ffd3b6` virtual), aresta tracejada vermelha com o rótulo `DESVIO DE CONEXÃO / QUEBRA DE LINHA`,
cadeia sugerida em pêssego e uma caixa de nota com `"<cM> cM, <gerações> gerações - <veredito>"`.

### 2.2 `requirements.txt` (emenda)

Décima dependência direta, pinada em **`graphviz==0.21`** conforme o `ADR-13`, com comentário que
separa explicitamente **binding** (pip) de **binário** (`dot`, instalador de sistema). O
`.dockerignore` continua lista de permissão e o `Dockerfile` continua `python:3.14-slim` + `pip`:
a renderização é de host, decidido em §9 do requirements.

## 3. Preservadas

| Regra | Onde | Por que não foi tocada |
|-------|------|------------------------|
| `reporting/` não importa `core` | `architecture.md#3`; `ADR-34` | Garantido por teste de AST |
| Decisão de layout mora em `reporting/` | `ADR-11` | O módulo novo é dessa camada e não chama núcleo |
| Dependência direta entra pinada | `ADR-13` | `graphviz==0.21` pinado, com versão verificada |
| Import preguiçoso de dependência opcional | `L-26` (precedente `psycopg2`) | `graphviz` só é importado dentro da função |
| Mermaid é o diagrama da tela | `reporting/mermaid_render.py` | Arquivo intocado; a imagem é outro produto |
| Dados reais não entram no versionamento | `principles.md#i` | Fixture sintética; imagem fora do repositório e não versionada |
| `None` significa "não sei" | `architecture.md#4` | A caixa imprime `—` em vez de inventar número |
| Os três status da `028` | `addenda/028-...` | O renderizador só lê o status e os códigos |
| Árvore sugerida da `029` | `addenda/029-...` | Consumida como entrada; nenhum campo novo |
| Árvore não duplicada no banco | `architecture.md#4` | Nenhuma escrita; DOT e imagem são efêmeros |

## 4. Modificadas

| Regra | Onde | O que mudou | Severidade |
|-------|------|-------------|------------|
| Conjunto de dependências de runtime | `dependencies.md`; `requirements.txt` | Passa de 9 para 10 pins, com `graphviz==0.21`. **Nenhuma dependência existente mudou de versão** | HIGH |

Nenhuma regra de domínio foi alterada ou removida. A única modificação é a lista de dependências,
e ela vem acompanhada do aviso de que o binário de sistema não é instalável por `pip`.

## 5. Verificação de execução

| Verificação | Resultado |
|-------------|-----------|
| Suíte completa no `.venv` | **1154 passam, 11 pulados, 0 falham** (94,78 s) |
| Baseline antes da feature | 1122 passam, 9 pulados |
| Testes novos | **32** (28 + 3 + 1), mais 2 de renderização que ficam pulados sem `dot` |
| Skips | 11 = 9 pré-existentes + **2 de renderização**, com motivo declarado |
| `git status` | apenas os arquivos de §1 e os artefatos de `_reversa_forward/030-*` |
| `app.py`, template, CSS, `mermaid_render.py`, Docker, `init.sql` | intocados |
| Cobertura declarada | o desenho (DOT) está coberto; a **imagem** não, porque falta o binário `dot` |

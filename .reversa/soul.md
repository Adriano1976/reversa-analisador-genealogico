# Soul — analisador-genealogico

> Síntese executiva gerada por **reversa-extract-soul**
> Fontes: Scout (surface.json/inventory.md), Detective (domain.md), Architect (architecture.md)
> Escala de confiança: 🟢 CONFIRMADO | 🟡 INFERIDO | 🔴 LACUNA

---

## Propósito

**analisador-genealogico** (Genetic Genealogy Path Analyzer) é uma aplicação web monolítica em **Python + Flask** para **genealogistas genéticos**. Ela responde a pergunta central do usuário: *"como eu me conecto geneticamente a essa outra pessoa?"*

O sistema cruza duas fontes de dados:
1. **Árvore genealógica** em arquivo **GEDCOM** (`.ged`) — quem é quem, quem é filho/a de quem.
2. **Relatório de DNA** em CSV (ex.: GEDmatch) — quanto DNA (em **cM**) o usuário compartilha com cada correspondente.

A partir desse cruzamento, ele calcula e visualiza o **caminho de parentesco** entre a pessoa raiz e cada DNA match: sobe até o **ancestral comum** (MRCA) pelas ligações de pai/mãe e desce até o match — ou recorre a uma **conexão indireta por afinidade** (casamentos/cunhados) quando não há ligação sanguínea direta. Para nomes corrompidos ou grafias divergentes, aplica **matching difuso** que ignora entradas não confiáveis em vez de forçar falsos positivos. 🟢

**Público-alvo:** genealogistas amadores e pesquisadores de história familiar que usam testes autossômicos e precisam transformar listas de segmentos em árvores concretas de parentesco.

---

## Entidades centrais

- **GEDCOM** — Formato padronizado (`.ged`) de troca de árvores genealógicas; define registros `INDI` (pessoa) e `FAM` (família). É a fonte de verdade da genealogia. 🟢
- **INDI** — Registro de indivíduo, identificado por `xref_id` (ex.: `@I0001@`). `FAMC` = família onde é filho/a; `FAMS` = famílias onde é cônjuge. 🟢
- **FAM** — Registro de família (`@F1@`), com `HUSB` (marido), `WIFE` (esposa) e `CHIL` (filhos). 🟢
- **DNA Match** — Pessoa do CSV de correspondentes com valor de **cM** compartilhado. Entidade de entrada para a predição de relação. 🟢
- **cM (centiMorgan)** — Unidade de medida de recombinação genética; quanto maior, mais próximo o parentesco. É a moeda que traduz genética em grau de relação. 🟢
- **Ancestral comum / MRCA** — Ascendente mais recente compartilhado entre duas pessoas; base da conexão direta. 🟢
- **Grafo pessoa↔família** — Estrutura em memória (`networkx.Graph`/`DiGraph`) sobre a qual rodam BFS e menor caminho para achar conexões diretas e indiretas. 🟢

---

## Decisões fundadoras

1. **Toda a análise roda em memória, sem banco de dados.** O GEDCOM vira dicionários `people`/`families` e grafos NetworkX por sessão; a persistência é só a pasta `uploads/` com os arquivos enviados. Simplicidade acima de durabilidade. 🟢
2. **Monolito server-side com Flask + Jinja2**, sem backend em JS e sem API." Tudo centralizado em um único `app.py` com três fluxos (`process_dna`, `path_search` e renderização inicial). 🟢
3. **Predição de relação baseada em faixas de cM** (tabela `SHARED_CM_DATA`, padrão do Shared cM Project) — a genética é traduzida em "provável primo de 1º grau" etc. por faixas numéricas. 🟢
4. **Matching de nomes é viral e defensivo.** Combina score difuso (`token_sort`, `partial`, `given`) com bônus por interseção de sobrenomes e rejeita candidatos suspeitos (sem sobrenome comum) para não fabricar parentescos falsos — priorizando auditoria visual de matches descartados. 🟢
5. **Conexão direta primeiro, afinidade como fallback.** Busca ancestral comum até profundidade 20; se não acha, tenta conexão indireta por afinidade em até 40 hops — reconhece que nem todo parentesco é sanguíneo. 🟢
6. **Tratamento de mojibake embutido** (`strip_bad_utf`, `demojibake`): nomes portugueses com encoding corrompido (Latin-1 lido como UTF-8) são saneados antes do matching — decisão motivada por dados reais de genealogia brasileira. 🟢

---

## Lacunas 🔴 (validação humana)

- 🔴 **Sem autenticação/RBAC** — qualquer acesso web usa todas as funcionalidades, sem camada de permissão.
- 🔴 **Sem testes automatizados** — nenhum framework de testes detectado; regras críticas de matching (aceite A/B/C/D) sem cobertura.
- 🔴 **Sem histórico Git** — decisões fundadoras reconstruídas por inferência de código, não por commits.
- 🔴 **Tabela de cM sem fonte citada no código** — as faixas são implícitas ao Shared cM Project do README.
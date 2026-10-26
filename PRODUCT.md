# Product

<!-- impeccable:product-schema 1 -->

## Platform

web

## Users

**Genealogista genético, operador único.** Trabalha com a **própria** árvore e os **próprios** kits de DNA, numa máquina pessoal. Não há autenticação, contas, multiusuário nem separação por cliente — e não deve passar a haver.

A situação de uso: ele já tem o GEDCOM da família e um CSV de matches exportado do GEDmatch (ou similar), e precisa decidir, entre dezenas ou centenas de matches, quais têm respaldo documental, quais são apenas pista e quais contradizem o que a árvore afirma.

## Product Purpose

Cruza a árvore GEDCOM com a lista de matches de DNA e apresenta **três coisas separadas**: o que o GEDCOM afirma, o que o DNA informa e se os dois são compatíveis — sem nunca tratar o cM como confirmação de parentesco.

Sucesso é o operador decidir rápido quais matches perseguir e quais descartar, **com o motivo escrito em cada caso**, e conseguir revisar o resultado meses depois sem reconstruir o raciocínio.

## Positioning

O que um vizinho de categoria (GEDmatch, ThruLines, MyHeritage) não pode copiar sem abandonar o próprio modelo: **este app recusa**. O DNA não cria, não corrige e não altera caminho documental; o cM vira uma lista de possibilidades pela tabela publicada do Shared cM Project, nunca um veredito único; e quando a data do registro torna a doação do DNA impossível, o parentesco é apresentado como não encontrado, com o motivo. A saída mais valiosa do produto é a **negativa justificada**.

## Operating Context

Fluxo em três fases na mesma tela: carregar ou escolher a árvore (GEDCOM), buscar o caminho documental entre duas pessoas, e cruzar o CSV de matches com o parentesco. O resultado vem em cartões recolhíveis com selos de confronto, janela de vida, profundidade e validação temporal; descartes aparecem em lista própria com motivo.

Uso local, em português do Brasil, num navegador — a tela é responsiva até o telefone. Sessão típica: uma árvore carregada por vez, um relatório de matches por análise, leitura do topo para baixo, com tema claro como padrão e escuro por escolha lembrada.

## Capabilities and Constraints

Confirmado no código e nas specs:

- Ingestão de GEDCOM (`.ged`) e de CSV de matches (nome, cM e, quando o arquivo traz, kit, fonte, segmentos, SNPs e cromossomo).
- Confronto em quatro estados (COMPATÍVEL, POSSÍVEL, CONFLITANTE, INCONCLUSIVO) e veredito temporal (VALIDADO, INCONCLUSIVO, ERRO CRÔNICO).
- Detecções: homônimos e identidade ambígua, endogamia e colapso de pedigree, profundidade do caminho, janela de vida, qualidade do segmento e cobertura do arquivo.
- A única exportação é o **CSV da lista de descartes** (`assets.descartes_em_csv`); o relatório em si é lido na tela, sem PDF e sem envio por e-mail.
- Bootstrap, fontes e Mermaid vêm por CDN. É dependência de **apresentação**: sem rede a tela degrada para as fontes nativas e o diagrama não desenha, mas nenhum dado do operador sai da máquina.

Decisão de produto, confirmada: **pessoal, local, operador único**. Sem login, multiusuário, nuvem pública, cobrança ou retenção por cliente.

Em aberto (não decidir sem o operador): política de retenção dos arquivos já enviados; se o resultado precisa ser arquivável fora da tela além do CSV de descartes.

## Brand Commitments

- Nome de tela: **Analisador Genealógico** (título do documento: "Analisador de Conexões Genealógicas").
- Idioma e voz: português do Brasil, tom documental e sóbrio. O app afirma o que pode sustentar e diz quando não sabe.
- Identidade já praticada: paleta de pergaminho, verde-folha e marrom de tronco, tirada da própria arte do topo; serifa editorial nos títulos, sans no texto; logo do livro aberto com hélice de DNA.
- Ativos: logo em `_reversa_docs/assets/img/logo.png`, arte do topo em `src/assets/banner-da-tela.png`, ícone da aba em `src/assets/apple-touch-icon.png` (servido por `/apple-touch-icon.png` e também embutido como data URI no template).

## Evidence on Hand

- **Não há dados reais versionados.** A suíte usa GEDCOM e CSVs sintéticos em `tests/fixtures/`; a pasta de uploads do repositório é de trabalho, não é amostra pública.
- Especificações, adendos, ADRs e user stories em `_reversa_sdd/`; a regra de análise e os invariantes estão no `README.md`.
- Não há depoimentos, clientes, benchmarks públicos ou números de desempenho publicados. Trabalho futuro não deve inventá-los; se precisar de prova, medir e declarar o método.

## Product Principles

1. **Documento manda; genética informa.** Nenhuma tela pode sugerir que o DNA determinou o parentesco.
2. **Negativa justificada vale mais que match.** Todo descarte e todo "não encontrado" carrega o motivo.
3. **Número sem procedência não entra.** Cada valor exibido tem fonte declarada — GEDCOM, CSV ou tabela publicada.
4. **O operador decide.** O app apresenta evidência e possibilidade; não emite veredito de parentesco.
5. **Local por padrão.** Dado genealógico e genético não sai da máquina do operador.

## Accessibility & Inclusion

- Contraste medido e preso por teste nos dois temas (`tests/test_estilo_da_tela.py`): mínimo AA para texto e 3:1 para objeto gráfico.
- Tema claro como padrão, escuro por escolha lembrada; foco de teclado visível em todos os controles, inclusive nos cartões recolhíveis.
- Interface apenas em PT-BR; não há requisito confirmado de outros idiomas nem de tecnologia assistiva específica além do que a suíte já cobre.

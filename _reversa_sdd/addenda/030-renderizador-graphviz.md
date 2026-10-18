# Adendo: renderizador Graphviz da árvore sugerida

> Identificador: `030-renderizador-graphviz`
> Data: `2026-10-18`
> Cenário: **legado** (âncora em `_reversa_sdd/architecture.md`, `_reversa_sdd/domain.md` e
> `_reversa_sdd/dependencies.md`)

## Vigência

Vigente desde 2026-10-18.

## Resumo da entrega

A feature entrega o **primeiro emissor de imagem** do projeto: a árvore sugerida da `029` deixa de
existir só como estrutura em memória e passa a sair como PNG ou SVG, com layout hierárquico, cores
por classe de nó, a aresta rompida tracejada em vermelho e uma caixa com o resumo da evidência
genética. Nada é servido por HTTP, nada é persistido e a imagem só é escrita no caminho que o
chamador informar.

A entrega foi concluída em **19 de 19 ações**, com 32 testes novos (suíte em 1154 passam, 11
pulados, 0 falham). Ela é composta por `reporting.visualizer` — que monta o DOT **à mão** e usa o
pacote `graphviz` só para invocar o binário `dot` — mais a décima dependência de runtime, pinada em
`graphviz==0.21`.

**Cobertura parcial declarada:** os 2 testes de renderização real são **pulados** enquanto o binário
`dot` não estiver no `PATH`. O texto DOT (cores, aresta rompida, caixa, escape, determinismo) e a
recusa `DOT_AUSENTE` estão cobertos; a imagem gerada, não.

## Impacto por artefato da extração

| Artefato | Seção | Tipo de impacto | Delta |
|----------|-------|-----------------|-------|
| `_reversa_sdd/architecture.md` | §3 Componentes e estrutura de pacotes | componente-novo | `reporting.visualizer` é o emissor de imagem: reconstrói o recorte do caminho, comprime as famílias em arestas genitor→filho e exporta PNG/SVG sem importar `core` |
| `_reversa_sdd/architecture.md` | §4 Modelo de dados | delta-de-dados | Nenhuma estrutura persistente nova: o DOT é string em memória e a imagem é arquivo efêmero no destino informado, nunca versionado |
| `_reversa_sdd/dependencies.md` | §2 Dependências Diretas (`requirements.txt`) | regra-alterada | A lista passa de 9 para 10 pins com `graphviz==0.21`; o **binário** `dot` não vem do `pip` e é dependência de sistema, documentada e exigida em tempo de execução |
| `_reversa_sdd/domain.md` | §5 Contrato de Mensagens ao Usuário | regra-nova | Entram dois literais que vão para dentro da imagem: `DESVIO DE CONEXÃO / QUEBRA DE LINHA` na aresta cortada e `"<cM> cM, <gerações> gerações - <veredito>"` na caixa de evidência, com ponto decimal |
| `_reversa_sdd/domain.md` | §3.1 Parentesco documental | regra-nova | No desenho, só filiação vira aresta; casamento nunca é desenhado nem atravessado, e a compressão de família preserva a direção genitor→filho |
| `_reversa_sdd/code-analysis.md` | §5 Unidade `busca-caminho` | componente-novo | A unidade que navega o grafo ganha o lado da emissão: o desenho é reconstruído dos metadados (caminho, gerações virtuais, junções), não por travessia do grafo bipartido |

## Regras sob vigilância

- **W001** — `requirements.txt` mantém as 9 dependências anteriores e ganha `graphviz==0.21`, com o
  aviso de que o `dot` não vem do `pip`; ver
  `_reversa_forward/030-renderizador-graphviz/regression-watch.md#itens-de-vigilância`.
- As observações **O-01 a O-04** do mesmo arquivo registram a cobertura parcial, o salto da junção
  sem filiação comum, a renderização ser de host (não de container) e a independência da fixture,
  sem peso de regressão.

## Fontes

- `_reversa_forward/030-renderizador-graphviz/requirements.md`
- `_reversa_forward/030-renderizador-graphviz/roadmap.md`
- `_reversa_forward/030-renderizador-graphviz/investigation.md`
- `_reversa_forward/030-renderizador-graphviz/data-delta.md`
- `_reversa_forward/030-renderizador-graphviz/actions.md`
- `_reversa_forward/030-renderizador-graphviz/legacy-impact.md`
- `_reversa_forward/030-renderizador-graphviz/regression-watch.md`

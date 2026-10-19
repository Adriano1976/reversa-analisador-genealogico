# 035 — Lista de trabalho dos descartes

> Feature: `035-lista-de-trabalho-dos-descartes`
> Data: `2026-10-19`
> Cenário: **legado** (âncora em `_reversa_sdd/`, adendos `020`, `034`)

## 1. O problema, medido

A `034` fechou o que o software podia fazer com os descartes: 366 nomes, 76 com candidato
compatível, 7 com caminho documental viável. Medi também a porta da grafia e ela está
**vazia**: dos 91 descartes cujo sobrenome não existe na árvore, apenas 5 têm sobrenome
parecido (≥ 85) e **nenhum** tem prenome compatível.

Os 288 restantes não se resolvem no casamento de nomes — ou a pessoa não está na árvore,
ou está com um nome que não compartilha nem prenome nem sobrenome. **Resolve-se no
cadastro da árvore, em outra ferramenta.**

O que faltava era levar a lista para lá.

## 2. O que a entrega faz

### RF-01 — Botão de download no bloco dos descartados

"Baixar lista de trabalho (CSV)". Só aparece quando há descartes.

### RF-02 — Uma linha por descarte, com o que a tela sabe

Colunas: `Nome no CSV`, `Kit`, `cM`, `Motivo`, `Candidato na árvore`, `Nascimento`,
`Prenome`, `Nota`.

### RF-03 — Só o candidato compatível entra na planilha

Homônimo "melhor avaliado" aparece na tela para explicar a recusa, mas na planilha seria
enganoso — a lista é de nomes a cadastrar. Medido: *Luzia Martins dos Santos*, nascida em
1798, aparecia como candidata de *Clezia Santos*.

### RF-04 — O arquivo abre no Excel em português

Separador `;`, decimal com vírgula, BOM UTF-8 e guarda contra fórmula (`=`, `+`, `-`, `@`
recebem prefixo `'`).

### RF-05 — O formato mora em `reporting/`, não no template

`reporting.csv_de_descartes.csv_de_descartes(itens) -> str` é função pura: não lê arquivo,
não fala com a rede e não importa `core/` (`ADR-34`).

## 3. Decisão de arquitetura: o que viaja no formulário

A aplicação não tem sessão nem histórico. Para exportar **exatamente** o que o operador
está vendo, o bloco carrega num campo oculto o JSON que ele mesmo renderizou, e a rota
`POST /descartes.csv` só formata. Nenhuma análise roda de novo — 90 segundos de espera
para baixar um arquivo seriam inaceitáveis.

## 4. Critérios de aceite

- [x] Cabeçalho com as oito colunas.
- [x] Uma linha por descarte, com acento preservado e decimal com vírgula.
- [x] Candidato incompatível não entra.
- [x] Nome que parece fórmula sai desarmado.
- [x] Corpo inválido ou que não é lista devolve só o cabeçalho, sem estourar.
- [x] Sem descartes, o botão não aparece.

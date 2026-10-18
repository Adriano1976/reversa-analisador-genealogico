# Regression Watch: renderizador Graphviz da árvore sugerida

> Identificador: `030-renderizador-graphviz`
> Data: `2026-10-18`
> Fonte dos itens: seção "Modificadas" de `legacy-impact.md`

## Itens de vigilância

| ID | Origem (arquivo, seção) | Regra esperada após a mudança | Tipo de verificação | Sinal de violação |
|----|--------------------------|-------------------------------|---------------------|-------------------|
| W001 | `_reversa_sdd/dependencies.md`; `_reversa_forward/030-renderizador-graphviz/legacy-impact.md#4-modificadas` | `requirements.txt` mantém as 9 dependências anteriores nas mesmas versões **e** `graphviz==0.21`; o comentário continua separando binding (pip) de binário (`dot`, sistema) | `presença` | O pin de `graphviz` sumir, mudar de versão sem decisão, ou o aviso de que o `dot` não vem do `pip` for removido |

## Observações (sem peso de regressão)

Itens 🟡/🔴 que não eram regra confirmada antes da feature.

- **O-01 — a imagem não está coberta pela suíte.** O teste de renderização é pulado enquanto o
  binário `dot` não estiver no `PATH`. O que está coberto é o texto DOT (cores, aresta rompida,
  caixa, escape, determinismo) e a recusa `DOT_AUSENTE`. Quando o Graphviz for instalado, os dois
  testes passam a rodar sem nenhuma mudança de código — é o sinal de que a cobertura fechou.
- **O-02 — o salto da junção não tem filiação comum.** Para não desenhar três ligações entre o
  mesmo par de pessoas, o salto cortado recebe só a aresta tracejada e a cadeia sugerida. É
  decisão de desenho tomada no coding, registrada em `actions.md#notas-de-execução` (item 1).
- **O-03 — a renderização é de host, não de container.** O `Dockerfile` não instala o Graphviz e o
  `.dockerignore` é lista de permissão. Se alguém ligar o renderizador a uma rota dentro do
  container, o resultado é `DOT_AUSENTE` em produção — a mesma classe da `L-33`.
- **O-04 — a fixture do desenho é independente da `029`.** Uma mudança no contrato da sugestão
  **não** quebra os testes de desenho, porque eles montam o dicionário à mão. O efeito colateral é
  que a divergência entre o contrato real e a fixture só apareceria no teste de integração.

## Histórico de re-extrações

> Preenchido pelo agente reverso quando `/reversa` rodar novamente.

| Data | Item | Resultado | Observação |
|------|------|-----------|------------|
| — | — | — | Nenhuma re-extração executada desde a criação deste arquivo |

## Arquivadas

| ID | Motivo | Data |
|----|--------|------|
| — | Nenhum item arquivado | — |

# Cápsula de reprodução

> Bug: `BUG-20261004-EWSJ`, contexto `analise-dna`
> Executada em 2026-10-04 por `/reversa-debugger-fix`, etapa 2

| Item | Valor |
|------|-------|
| Commit base | `aba650d` |
| Branch | `master` |
| Sistema | Microsoft Windows NT 10.0.26200.0 |
| Runtime | Python 3.14.6 (`py -3.14`) |
| Comando | `py -3.14 evidence/probe_reproducao.py` |
| Código de saída | 0 |
| Taxa | **3/3** execuções com o defeito |
| Classificação | `deterministic` |

## O que a sonda faz

A sonda não abre porta, não usa a rede e não escreve no projeto. Ela:

1. carrega o GEDCOM sintético de `tests/fixtures/sample_dna.py` pelo parser de produção
   (`parsers.gedcom_parser.load_gedcom_and_build_graph`), a partir de arquivo temporário;
2. escreve um CSV temporário com **três segmentos de 6,4 cM do mesmo match**, que é a soma que
   produz o resíduo;
3. roda o fluxo real de análise (`core.dna_analysis.dna_analysis`) com a raiz `Carlos Silva Souza`;
4. renderiza o **template real** `src/templates/index.html` em contexto de requisição do Flask, sem
   subir servidor, e recorta o HTML do badge.

## Resultado observado

Trecho literal de `reproduction.txt`:

```text
soma bruta em Python: 19.200000000000003
esperado pelo relator: 19,2

GEDCOM dos fixtures carregado (5 pessoas, sem abrir porta)
resultados: 1 | descartados: 0 | mensagem: 1 conexões encontradas. 0 descartadas.
match: Ana Silva Souza
valor guardado em result['cm']: 19.200000000000003
tipo do valor: float

HTML real renderizado pelo template (src/templates/index.html):
  ...<strong>Ana Silva Souza</strong> <span class="badge bg-success">19.200000000000003 cM</span>...

exibido hoje : 19.200000000000003 cM
exibido certo: 19,2 cM

VEREDITO: DEFEITO REPRODUZIDO
```

## O que esta medição prova

- O valor **armazenado** é o `float` exato da soma, e a soma está correta.
- O HTML emitido pelo template real contém o valor cru, sem formatação, e é a **única** origem do
  texto que o operador lê.
- A cadeia causal está fechada sem hipótese: o string exibido é exatamente o `str` do `float`.

## O que esta medição não prova

- **Não exercita o navegador.** A prova é sobre o HTML emitido, não sobre a renderização visual. É o
  mesmo tipo de lacuna que o `BUG-20261002-T4ZM` declarou, e aqui ela é menor: o defeito está no
  texto do HTML, não em como o navegador o interpreta, e o print do relator corrobora o resultado.
- **Não prova que o CSV do relator produziu a mesma soma.** O print dele traz a string idêntica
  `19.200000000000003`, o que é a corroboração disponível. O valor exato do CSV dele não foi lido.
- **Não mede a frequência real** na base dele. A taxa `3/3` é das execuções desta sonda, não da tela
  do relator.

# Requirements: Explicar a fonte não declarada no cartão

> Identificador: `042-explicar-fonte-nao-declarada`
> Data: `2026-10-22`
> Modo: express
> Pasta da extração reversa: `_reversa_sdd/`

## 1. Resumo executivo

Na seção 2, um cartão cuja célula de fonte é um nome de projeto exibe
`Fonte: não declarada` com a etiqueta `Migration - F2 - T` e **nenhuma explicação** — o operador vê um
texto que não é laboratório e não sabe por quê. O cartão passa a dizer **o que** aquele valor é, usando o
motivo que o núcleo já calcula e a tela ainda não mostrava: `Fonte: não declarada (Migration - F2 - T) —
nome de projeto de pesquisa, não de laboratório`. O texto original continua visível; nada é escondido.

## 2. Contexto a partir do legado

| Fonte | Trecho relevante | Confidência |
|-------|------------------|-------------|
| `_reversa_sdd/domain.md#38-leitura-tolerante-do-csv-descartar-sim-esconder-não` | Descartar o valor sim, esconder não: o original fica visível ao lado do rótulo | 🟢 |
| `src/core/fontes_de_laboratorio.py` | `MOTIVOS_TEXTO` já classifica cada valor não-laboratório (`texto_de_formulario`, `empresa_nao_confirmada`, `nome_de_projeto`, `haplogrupo`, `nao_reconhecida`) | 🟢 |
| `src/core/genetic_evidence.py` (`evidence_for`) | O payload do cartão expõe `source` e `source_original`, mas **não** o motivo — a explicação existe e não chega à tela | 🟢 |
| `_reversa_sdd/addenda/040-fonte-e-cobertura-do-arquivo.md#resumo-da-entrega` | A 040 decidiu os três desfechos e a etiqueta do original; esta emenda completa a leitura | 🟢 |

## 4. Regras de negócio novas ou alteradas

1. **RN-01 — Todo valor não-laboratório diz o que é.** Ao lado da etiqueta do texto original, a linha da
   fonte passa a exibir uma explicação curta e específica ao motivo: texto de formulário, empresa não
   confirmada, nome de projeto, haplogrupo ou valor não reconhecido. 🟢
   - Tipo: nova.
2. **RN-02 — Sem valor utilizável, a explicação diz isso.** Célula vazia ou `-` não exibe etiqueta (não há
   o que mostrar) e explica "o arquivo não traz uma fonte utilizável nesta coluna". 🟢
   - Tipo: nova.
3. **RN-03 — Laboratório reconhecido não ganha explicação.** `Fonte: Genera` continua com uma etiqueta
   apenas quando a grafia difere (`GENERA`), e sem nenhum texto extra. 🟢
   - Tipo: preservada (040).

## 7. Critérios de Aceitação

- Um cartão com `Migration - F2 - T` exibe a etiqueta do texto **e** a explicação "nome de projeto de
  pesquisa, não de laboratório".
- Um cartão com `-` exibe "não declarada" e "o arquivo não traz uma fonte utilizável nesta coluna", **sem**
  a etiqueta `-`.
- Um cartão com `Genera` continua exibindo só `Fonte: Genera`.
- A suíte completa segue verde e nenhum número, veredito ou contagem muda.

## Emendas

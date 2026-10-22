# Legacy impact: explicar a fonte não declarada

> Identificador: `042-explicar-fonte-nao-declarada`
> Data: `2026-10-22`
> Modo: **express**
> Política de edição do legado: `allowLegacyEdits: true`, com `allowedPaths` liberando `src/**` e
> `tests/**`. Todos os arquivos tocados estão dentro desses globs.

## 1. Arquivos afetados

| Arquivo afetado | Componente | Tipo | Severidade | Justificativa |
|---|---|---|---|---|
| `src/core/fontes_de_laboratorio.py` | — | regra-nova | LOW | `EXPLICACOES`, `SEM_VALOR_UTIL` e a função pura `explicacao(motivo, bruto)` |
| `src/core/genetic_evidence.py` | `analise-dna` | contrato-alterado | LOW | `evidence_for` passa a expor `source_motivo` e `source_explicacao` no payload do cartão |
| `src/templates/index.html` | apresentação | contrato-alterado | LOW | A linha `Fonte:` do bloco 2 exibe a explicação depois da etiqueta e omite a etiqueta quando o valor é `-` ou vazio |
| `tests/fixtures/sample_dna.py` | — | componente-novo | LOW | Constantes `DNA_CSV_FONTE_NOME_DE_PROJETO` e `DNA_CSV_FONTE_VAZIA` |
| `tests/test_fontes_de_laboratorio.py` | — | contrato-alterado | LOW | Seis casos de unidade da `explicacao` |
| `tests/test_fonte_e_cobertura_na_tela.py` | — | contrato-alterado | LOW | Dois casos de tela: nome de projeto e célula vazia |

## 2. Diff conceitual

**`core.fontes_de_laboratorio`.** O motivo já existia (`source_motivo`), mas só era usado como contagem no
painel (`MOTIVOS_TEXTO`: "nome de projeto", "texto de formulário"). Entra `EXPLICACOES`, com a frase que
o cartão lê, e `explicacao(motivo, bruto)`, que devolve `SEM_VALOR_UTIL` quando a célula é `-` ou vazia —
nesse caso não há texto original que valha mostrar.

**`core.genetic_evidence`.** `evidence_for` expõe `source_motivo` e `source_explicacao` ao lado de
`source` e `source_original`. Nada mais no payload mudou.

**Template.** A linha passa a ser
`Fonte: <rótulo> [etiqueta do original] — <explicação>`, com a etiqueta suprimida para `-`/vazio.

## 3. Regras do `domain.md` **preservadas**

| Regra | Verificação |
|---|---|
| §3.8 — descartar sim, esconder não | o texto original continua visível na etiqueta; o que entrou foi a explicação ao lado |
| §3.2 — o DNA não vira parentesco | a linha é descritiva; nenhum veredito, cM ou caminho foi tocado |
| Os três desfechos da 040 (`laboratório`, `não declarada`, `outro`) e a escolha dentro do kit | inalterados; os testes de catálogo continuam passando |
| Contagem de células sem laboratório no painel (`MOTIVOS_TEXTO`) | inalterada — `EXPLICACOES` é outro dicionário |

## 4. Regras **modificadas**

| Regra | O que mudou | Onde |
|---|---|---|
| Texto da linha `Fonte:` no cartão | passa a explicar o motivo e a omitir a etiqueta inútil | `src/templates/index.html`, seção 2 |
| Payload do cartão (`evidence_for`) | ganha `source_motivo` e `source_explicacao` (aditivo) | `src/core/genetic_evidence.py` |

> **Para o `/reversa-sync`:** `_reversa_sdd/data-dictionary.md#54` descreve `evidence_for`; ganha duas
> chaves. `_reversa_sdd/addenda/040-…` registra a etiqueta do original — esta emenda acrescenta a
> explicação ao lado dela.

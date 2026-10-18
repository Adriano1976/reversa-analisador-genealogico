# Legacy Impact: validador de dados de DNA × GEDCOM

> Identificador: `028-validador-de-dados-dna`
> Data: `2026-10-18`
> Âncora: `_reversa_sdd/architecture.md` e `_reversa_sdd/domain.md` (cenário legado)

## 1. Arquivos afetados

| Arquivo afetado | Componente | Tipo | Severidade | Justificativa |
|-----------------|------------|------|------------|---------------|
| `src/core/validator.py` | `core.validator` (novo) | componente-novo | MEDIUM | Regras puras de estimativa do MRCA, viabilidade temporal, anomalias e status |
| `src/application/validacao.py` | `application.validacao` (novo) | componente-novo | MEDIUM | Fachada de leitura/cruzamento; reutiliza parser, evidência, matching e parentesco documental |
| `src/core/janela_de_vida.py` | `core.janela_de_vida` | contrato-novo | LOW | Expõe `data_imprecisa(texto)` público; `conferir_janela_de_vida` passa a chamar o wrapper, sem mudança de comportamento |
| `tests/fixtures/arvore_com_datas.py` | testes | artefato-novo | LOW | GEDCOMs sintéticos com datas, sem dado real |
| `tests/test_validator.py` | testes | artefato-novo | LOW | 23 testes do núcleo puro |
| `tests/test_validacao_de_arquivos.py` | testes | artefato-novo | LOW | 9 testes de integração da fachada |
| `tests/test_fronteira_do_validador.py` | testes | artefato-novo | LOW | 3 guardas de fronteira (sem parsers/HTTP/relógio) |

**Não tocados:** `src/app.py`, `src/templates/index.html`, `src/assets/app.css`, `init.sql`,
`requirements.txt`, `docker-compose.yml` e as 6 tabelas do PostgreSQL.

## 2. Diff conceitual por componente

### `core.validator` (novo)

O módulo recebe uma `ComparacaoParaValidar` congelada — doador, match, `documental`, `kit`,
`ano_referencia`, `intervalo_de_geracao` e `comparacao_existente` — e devolve um dicionário com
`status`, `motivo`, `codigos`, `kit`, `cm`, `mrca_estimado`, `mrca_documentado`,
`geracoes_documentais` e `comparacao_existente`.

A decisão é uma composição das peças que já existiam:

- `documentary_relationship` fornece caminho, `degrees.a_up`/`b_up`, `meioses`,
  `common_ancestor` e `evidence` por salto;
- `hop_evidence` já marca `plausible is False` fora de 12–70;
- `janela_de_vida` fornece `IDADE_IMPOSSIVEL = 122` e, agora, `data_imprecisa`;
- `relationship_hypotheses` fornece as relações publicadas que contêm o cM;
- `evidence_comparison.compare` é usado pela fachada como insumo, quando existe.

O módulo **não** altera `evidence_comparison`, não renomeia os quatro estados e não escreve em
lugar nenhum. O status novo é um campo separado.

**Achado de implementação:** a coluna `meioses` de `SCP40_ROWS` não é o total de saltos do
caminho. Para `1C`, a tabela diz 2, mas o caminho tem 4 (2 de cada lado). O módulo deriva o total
da chave canônica (`1C` → 4, `2C` → 6, `1C1R` → 5) em `_meioses_totais_da_relacao`, sem alterar a
tabela. Usar a coluna crua subestimaria a profundidade pela metade.

### `application.validacao` (novo)

A fachada carrega a árvore uma vez, lê o CSV com `read_csv_with_fallback`, monta a evidência com
`build_genetic_evidence`, resolve o match com `build_ged_indexes`/`match_candidates`, monta o
parentesco com `documentary_relationship`, chama `compare` e entrega a comparação ao núcleo.

A política de raiz é a mesma do `core.dna_analysis`: substring do nome, sem diferenciar maiúsculas,
primeiro registro. A política de match também: primeiro candidato com caminho documental. O doador
nunca é candidato a match. Nenhum parser, matching ou regra de parentesco foi duplicado.

### `core.janela_de_vida` (contrato novo)

Ganhou `data_imprecisa(data_gedcom)`, wrapper público de `_e_imprecisa`, e a entrada em `__all__`.
`conferir_janela_de_vida` passou a chamar o wrapper. A lista de qualificadores (`ABT`, `EST`,
`CAL`, `BEF`, `AFT`, `CIRCA`, `APPROX`) e os limiares 105/122 permanecem os mesmos. O comportamento
observável é idêntico; a mudança existe para o validador não importar função privada nem duplicar a
lista.

## 3. Preservadas

- **Os quatro estados do confronto** (`COMPATIVEL`, `POSSIVEL`, `CONFLITANTE`, `INCONCLUSIVO`), seus
  gatilhos, mensagens e classes CSS — `_reversa_sdd/domain.md#21-os-quatro-estados-do-confronto`.
- **A separação dos três eixos** (documental, genético, confronto) — `_reversa_sdd/domain.md#2`.
- **A faixa 12–70 por salto** — `core.documentary_relationship` e `hop_evidence` não foram tocados.
- **O corte de 122 anos da janela de vida** — `core.janela_de_vida` mantém os limiares e as
  mensagens; só ganhou um wrapper.
- **A marca de 15 cM do maior segmento** — `core.genetic_evidence` não foi tocado; a feature não a
  transforma em veredito.
- **O contrato da tela** — `app.py`, template, CSS e o hash da tela não foram tocados.
- **O banco** — `init.sql` e as 6 tabelas não foram tocados; a feature não persiste nada.
- **O princípio I** — todas as fixtures são sintéticas; nenhum dado de `uploads/` foi lido ou
  copiado.

## 4. Modificadas

- `core.janela_de_vida`: **contrato-novo** (`data_imprecisa` público), sem alteração de regra ou de
  comportamento. É a única mudança em arquivo de produção que já existia.
- **Nenhuma regra 🟢 foi alterada ou removida.** `core.validator` e `application.validacao` são
  componentes novos; `evidence_comparison`, `documentary_relationship`, `genetic_evidence`,
  `relationship_hypotheses` e `dna_analysis` permanecem intactos.

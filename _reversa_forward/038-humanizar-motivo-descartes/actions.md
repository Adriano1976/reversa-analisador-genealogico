# Actions: Humanizar o motivo dos matches descartados

> Identificador: `038-humanizar-motivo-descartes`
> Data: `2026-10-20`
> Roadmap: `_reversa_forward/038-humanizar-motivo-descartes/roadmap.md`

## Resumo

| Métrica | Valor |
|---------|-------|
| Total de ações | 12 |
| Paralelizáveis (`[//]`) | 2 |
| Maior cadeia de dependência | 9 (T001 → T002 → T004 → T005 → T006 → T007 → T008 → T010 → T011) |

## Fase 1, Preparação

| ID | Descrição | Dependências | Paralelismo | Arquivo alvo | Confidência | Status |
|----|-----------|--------------|-------------|--------------|-------------|--------|
| T001 | Medir a linha de base antes de tocar em código: rodar a suíte completa, registrar a contagem (`passed`/`skipped`/`failed`), gravar `SHA_DA_TELA` e salvar a saída em `evidence/antes/suite.txt` e `evidence/antes/hash.txt` | - | - | `_reversa_forward/038-humanizar-motivo-descartes/evidence/antes/` | 🟢 | `[X]` |

## Fase 2, Testes

| ID | Descrição | Dependências | Paralelismo | Arquivo alvo | Confidência | Status |
|----|-----------|--------------|-------------|--------------|-------------|--------|
| T002 | Criar `tests/test_motivo_humanizado.py` com os testes de catálogo e diagnóstico: cada um dos seis códigos devolve a frase correspondente; nenhuma frase contém `given`, `final`, `inter` ou `jacc`; a precedência devolve nome do meio antes de sobrenome, e semelhança geral por último; `detalhe_tecnico` rotula os quatro números e usa vírgula decimal | T001 | `[//]` | `tests/test_motivo_humanizado.py` | 🟢 | `[X]` |
| T003 | Acrescentar ao mesmo arquivo os testes ponta a ponta: o caso do token do meio (`Maria Aparecida de Oliveira` × `Aparecida Oliveira`) sai com a causa `nome_do_meio_ausente`; o HTML do bloco não contém `given=`; a planilha tem nove colunas e a nona é `Detalhe técnico` | T001 | `[//]` | `tests/test_motivo_humanizado.py` | 🟢 | `[X]` |

## Fase 3, Núcleo

| ID | Descrição | Dependências | Paralelismo | Arquivo alvo | Confidência | Status |
|----|-----------|--------------|-------------|--------------|-------------|--------|
| T004 | Criar `src/core/motivos_do_descarte.py`: dataclass congelada `Motivo` (`codigo`, `texto`, `detalhe`), tabela `TEXTOS` dos onze códigos, `diagnosticar()` com a precedência `D-03` e `detalhe_tecnico()` com rótulos sem jargão | T002 | - | `src/core/motivos_do_descarte.py` | 🟢 | `[X]` |
| T005 | Trocar a montagem da string em `src/core/matching.py`: os cinco motivos de semelhança e os cinco do adendo `024` passam a nascer como `Motivo`, com o diagnóstico calculado depois do veredito; `avaliar_candidatos` devolve `Motivo` no segundo elemento e `match_candidates` continua devolvendo texto | T004 | - | `src/core/matching.py` | 🟢 | `[X]` |
| T006 | Propagar o motivo humano em `src/core/dna_analysis.py`: o dicionário do descarte passa a levar `motivo` (texto), `motivo_codigo` e `motivo_detalhe`, e o caso `reason is None` vira `não encontrado` com código `nao_encontrado` | T005 | - | `src/core/dna_analysis.py` | 🟢 | `[X]` |

## Fase 4, Integração

| ID | Descrição | Dependências | Paralelismo | Arquivo alvo | Confidência | Status |
|----|-----------|--------------|-------------|--------------|-------------|--------|
| T007 | Acrescentar `reason_code` e `detail` (default vazio) em `ports.DescartadoDaAnalise` e projetá-los em `application/dna_analysis.py`, sem tocar na escrita do adaptador | T006 | - | `src/ports/__init__.py`, `src/application/dna_analysis.py` | 🟢 | `[X]` |
| T008 | Acrescentar a nona coluna `Detalhe técnico` em `src/reporting/csv_de_descartes.py`, preservando BOM, `;`, decimal com vírgula e a guarda contra fórmula | T006 | `[//]` | `src/reporting/csv_de_descartes.py` | 🟢 | `[X]` |
| T009 | Ajustar o texto sob o botão de download em `src/templates/index.html` para dizer que o detalhe técnico vai na planilha, mantendo a edição dentro do `{% if skipped_matches %}` | T006 | `[//]` | `src/templates/index.html` | 🟡 | `[X]` |
| T010 | Atualizar os três testes presos ao literal antigo: `tests/test_dna_analysis.py` (prefixo do motivo de score), `tests/test_candidatos_do_descarte.py` (literal e comparação de tipos) e `tests/test_csv_de_descartes.py` (cabeçalho e fatias de coluna) | T007, T008, T009 | - | `tests/` | 🟢 | `[X]` |

## Fase 5, Polimento

| ID | Descrição | Dependências | Paralelismo | Arquivo alvo | Confidência | Status |
|----|-----------|--------------|-------------|--------------|-------------|--------|
| T011 | Fechar a verificação: rodar a suíte completa e a caracterização, conferir que `SHA_DA_TELA` não mudou, gravar `evidence/depois/suite.txt`, `evidence/depois/hash.txt` e `evidence/depois/escopo.txt` | T010 | - | `_reversa_forward/038-humanizar-motivo-descartes/evidence/depois/` | 🟢 | `[X]` |
| T012 | Gravar `legacy-impact.md` e `regression-watch.md` da feature, listando arquivos tocados e as regras sob vigilância | T011 | - | `_reversa_forward/038-humanizar-motivo-descartes/` | 🟢 | `[X]` |

## Notas de execução

- **T005, caso extra encontrado na execução.** O par sintético que reproduz o veto do token do
  meio não é o do `requirements.md` (`Maria Aparecida de Jesus Oliveira` × `Maria Oliveira`):
  com três sobrenomes a grafia cai para `0,33` e a causa passa a ser `sobrenome_pouco_parecido`
  — corretamente, aliás. O par que reproduz **exatamente** o caso do operador
  (`prenome 100`, `nota 88,75`, `sobrenomes em comum 1 de 1`) é
  `Maria Aparecida de Oliveira` × `Aparecida Oliveira`: `Maria` sobra como token do meio e não
  existe na árvore. O teste foi escrito com esse par, e o segundo caso
  (`Maria Cristina Oliveira`, `prenome 35`) prende a causa do prenome.
- **T010.** `tests/test_characterization_matching.py` também precisou de ajuste — não estava na
  lista da ação, e a razão é legítima: o contrato caracterizado do descarte ganhou as duas chaves
  novas. O `motivo` **não** mudou.
- Nenhum arquivo pré-existente foi apagado. Nenhuma dependência foi instalada.

## Histórico de alterações

| Data | Alteração | Autor |
|------|-----------|-------|
| 2026-10-20 | Versão inicial gerada por `/reversa-to-do` | reversa |
| 2026-10-20 | Execução das 12 ações por `/reversa-coding` (modo autônomo) | reversa |

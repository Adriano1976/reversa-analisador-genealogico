# Legacy Impact: grupos de triangulação

> Identificador: `055-grupos-de-triangulacao`
> Data: `2026-11-09`
> Política de edição do legado no momento da execução: `allowLegacyEdits: true`, com
> `allowedPaths` liberando `src/**`, `tests/**` e `README.md` — todos os alvos usados.
> Âncora: `_reversa_sdd/architecture.md` + `_reversa_sdd/domain.md`.

## 1. Arquivos afetados

| Arquivo afetado | Componente | Tipo | Severidade | Justificativa |
|---|---|---|---|---|
| `src/core/triangulacao.py` | Núcleo — domínio puro | componente-novo | MEDIUM | Agrupamento por interseção e fechamento; não existia |
| `src/core/triangulacao_no_cartao.py` | Núcleo — domínio puro | componente-novo | MEDIUM | Desfecho derivado dos cartões, sem segundo matching |
| `src/parsers/triangulacao_gedmatch.py` | Adaptador de entrada | componente-novo | MEDIUM | Leitura do CSV de pares; o adaptador de segmentos não serve |
| `src/core/genetic_evidence.py` | Evidência genética | regra-nova | MEDIUM | `parece_triangulacao` e `colunas_de_kit_nomeadas`; o detector existente **não** mudou |
| `src/core/dna_analysis.py` | Fluxo de DNA | regra-nova | HIGH | Arquivo de pares no campo de matches passa a ter mensagem que nomeia o campo certo |
| `src/utils/text_cleaning.py` | Limpeza de texto | regra-nova | LOW | `limpar_nome_de_gedmatch`; `norm_name` intocado (`ADR-07`) |
| `src/application/triangulacao.py` | Fronteira de aplicação | componente-novo | MEDIUM | Caso de uso dos dois modos + projeção pura |
| `src/application/dna_analysis.py` | Fronteira de aplicação | delta-de-dados | MEDIUM | Campo `grupos` em `ResultadoDeAnalise`, com padrão `()` |
| `src/app.py` | Borda HTTP | delta-de-contrato-externo | HIGH | Ação nova pré-árvore + campo opcional na ação de DNA |
| `src/templates/index.html` | Apresentação | delta-de-contrato-externo | HIGH | Formulário na Fase 3 e bloco de grupos antes dos cartões |
| `src/assets/app.css` | Apresentação | regra-nova | LOW | Estilos do bloco, com tokens existentes |
| `src/reporting/csv_dos_grupos.py` | Relatório | componente-novo | LOW | Exportação no dialeto de `csv_de_descartes` |
| `src/web/rotas_assets.py` | Rotas de recurso | delta-de-contrato-externo | MEDIUM | `POST /grupos.csv` |
| `tests/fixtures/sample_triangulation.py` | Suíte | componente-novo | LOW | Fixture sintética, sem dado real |
| `tests/test_triangulacao.py` + 5 arquivos | Suíte | componente-novo | MEDIUM | 27 testes novos |
| `tests/test_icone_de_atalho.py` | Suíte | regra-alterada | MEDIUM | `SHA_DA_TELA` movido por mudança declarada |
| `tests/test_traducao_de_erros.py` | Suíte | regra-alterada | LOW | O quarto ramo que traduz passou a existir |
| `tests/test_tres_fases_da_tela.py` | Suíte | regra-alterada | MEDIUM | Fase 3 agora oferece **um** upload sem árvore |
| `README.md` | Documentação | regra-nova | LOW | Funcionalidade documentada com o que ela não faz |

## 2. Diff conceitual por componente

### Núcleo de triangulação
Novo módulo puro. Recebe pares, devolve grupos fechados e maximais, com a região de
interseção, o cM mínimo e máximo dos pares e o alerta de acúmulo. Não lê arquivo,
não formata texto e não conhece GEDCOM. A ordem é total (cromossomo natural,
posição, kits), o que torna a saída determinística.

### Classificação do grupo
Novo módulo puro. Junta cada membro ao cartão pelo **kit** e, na falta dele, pelo
nome normalizado; o desfecho sai de `documentary.common_ancestor.id`. Não roda
matching, não cria cartão e não altera o veredito.

### Fluxo de DNA
Uma linha nova antes do `detect_columns`: se o arquivo tem forma de pares, a
mensagem passa a nomear o campo correto em vez de falar de "Nome e cM". Para o CSV
de matches, **nada muda**. Depois do núcleo, quando o arquivo auxiliar veio, o
caso de uso chama a triangulação e classifica contra `resultados`; exceção ali
vira observação do arquivo, nunca bloqueio.

### Borda
Duas costuras: a ação `triangulacao_analysis` no despacho **pré-árvore** (o modo
isolado não tem raiz e não pode passar por `_arvore_do_formulario`) e o campo
opcional `triangulacao_csv` na ação de DNA. As duas convergem no mesmo caso de
uso.

### Apresentação
O formulário da Fase 3 nasce **fora** da guarda `gedcom_filename`, porque existe
para rodar sem árvore. O bloco de grupos nasce no mesmo regime da cobertura: fora
da guarda de `dna_results`, aberto, antes dos cartões, e sem estatística agregada.

## 3. Preservadas

Regras 🟢 do `domain.md` que continuam intactas:

- Os **três eixos** e as duas proibições: o DNA não altera parentesco documental e o cM não é usado sozinho (`domain.md#2`).
- Os **quatro estados** do confronto e suas mensagens (`domain.md#2.1`).
- A chave de evidência **(nome, kit)** e a proibição de somar kits (`BR-D-12`, `BR-D-14`).
- O cM **nunca arredondado** no núcleo (`BR-D-15`).
- O piso de 10 cM por segmento e o aviso de segmento fraco (`BR-D-17`).
- A leitura tolerante do CSV, com encoding, separador, preâmbulo e linhas irregulares (`domain.md#3.8`).
- A ordem de apresentação documental primeiro (`BR-D-41`), que a feature **não** toca.
- O CSV de descartes e a lista de descartes, byte a byte iguais.
- O comportamento do histórico: a triangulação **não** é persistida e nada muda no banco.

## 4. Modificadas

| Regra anterior | O que passa a valer | Por quê |
|---|---|---|
| CSV sem coluna de Nome → "Colunas de Nome e cM não encontradas" | Se o arquivo tem forma de pares, a mensagem nomeia o campo "CSV de Triangulação" | A mensagem antiga era verdadeira e inútil (`RF-02`) |
| Fases 2 e 3 não oferecem campo sem árvore | A Fase 3 oferece o upload de triangulação; a análise de conexão continua exigindo árvore | `D-01`: o arquivo sozinho mostra os grupos |
| `SHA_DA_TELA` de 2026-10-31 | Novo hash, +1.550 bytes | Formulário novo no painel da Fase 3 |
| "Três ramos traduzem erro de domínio" | Quatro ramos | O ramo da triangulação também traduz |

## 5. O que a feature deliberadamente não tocou

- `init.sql` e o esquema PostgreSQL: nenhuma tabela, nenhuma coluna, nenhuma migração.
- `projetar_analise` e `RegistroDeAnalisesPostgres`: o grupo não entra no histórico.
- O matching (`matching.py`) e o vocabulário de nomes (`name_normalization.py`).
- Os fixtures e goldens de paridade.
- O oráculo congelado em `_reversa_sdd/oracle/`.

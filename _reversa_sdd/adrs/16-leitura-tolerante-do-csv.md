# ADR-16 — Leitura tolerante do CSV, com descarte reportado em vez de falha

- **Status:** Aceito e vigente
- **Data da decisão:** 2026-10-05
- **Commit(s):** `f371951` — "feat(csv): tolera separador, preambulo e linha torta com erro acionavel em portugues"; `3527851` (documenta)
- **Confiança:** 🟢 CONFIRMADO

## Contexto

Os CSVs de matches de DNA vêm de **exportadores diferentes** (GEDmatch, MyHeritage, FamilyTreeDNA) e não obedecem a um formato único: mudam o separador, trazem **linhas de título antes do cabeçalho** e podem ter linhas com número de campos irregular — muitas vezes por aspas desbalanceadas. O comportamento anterior era **derrubar a análise com o erro cru do pandas em inglês** (`Error tokenizing data. C error: Expected 1 fields in line 4, saw 2`), que não diz ao operador o que conferir.

## Decisão

Ler de forma **tolerante em quatro frentes**, e **reportar o que foi descartado** em vez de esconder:

1. Tentar `utf-8`; na falha, `latin-1`.
2. Detectar o separador pelo cabeçalho entre `,`, `;`, TAB e `|`.
3. **Localizar** a linha do cabeçalho quando há preâmbulo.
4. No erro de tokenização, **reler** o arquivo descartando as linhas irregulares (`on_bad_lines="skip"`), e **publicar a contagem e os números de linha** descartados.

## Evidência

- `src/parsers/csv_ingest.py` — `detectar_separador` (`:76`), `localizar_cabecalho` (`:93`), `linhas_irregulares` (`:126`), `read_csv_with_fallback` (`:140`).
- `src/parsers/csv_ingest.py:170-174` — o descarte é publicado em **`df.attrs`**: `separador`, `encoding`, `linhas_antes_do_cabecalho`, `linhas_ignoradas`, `erro_de_leitura`.
- `src/core/dna_analysis.py:98-141` e `:232-235` — a tela publica a contagem e os números de linha; **sem resultado nenhum, o aviso é anexado à mensagem**, porque não há cartão onde ele apareça.
- `src/core/dna_analysis.py:117-123` — o `ValueError` acionável: diz o separador usado, as colunas encontradas, as linhas divergentes e o que conferir.
- `_reversa_bugs/analise-dna/` — o registro de bug da análise de DNA.

## Justificativa

O arquivo do usuário é **dado real de terceiro**, exportado por uma ferramenta que ele não controla. Recusar a análise por causa de uma linha torta transfere ao usuário um problema que o sistema consegue resolver — e o erro cru em inglês nem sequer diz **o que** estava errado. A escolha correta é **prosseguir e reportar**: o operador precisa saber que faltam linhas, e não ser impedido de trabalhar por causa delas.

## Consequências

- ✅ **O que foi descartado não desaparece.** A tela publica a contagem, os primeiros dez números de linha e a causa provável; sem resultados, o aviso vai para a mensagem principal.
- ✅ **A escolha de `df.attrs` como canal foi deliberada**, e o código registra o motivo: trocar o retorno por uma tupla **quebraria** `dna_analysis` e o `__all__` que reexporta as funções. Foi a forma de acrescentar informação **sem alterar assinatura**.
- ⚠️ **Três guardas no cabeçalho existem contra falsos positivos medidos:** frequência ≥ 2, primeira linha divergente e posição dentro das **10 primeiras** linhas. Sem elas, um arquivo **sem cabeçalho** perderia sua primeira linha de dados, e um arquivo que **não é tabela** (um GEDCOM com uma linha contendo vírgula) elegeria essa linha como cabeçalho e **esconderia o problema real**.
- ⚠️ **O CSV de DNA não passa por validação de conteúdo** no upload (`app.py:86`): só a forma do nome é validada. A tolerância da leitura é o que justifica a assimetria em relação ao GEDCOM — mas o arquivo é gravado em disco **antes** de qualquer verificação (`P-05` em `permissions.md` §6).
- 🟢 **`map(str)` no lugar de `astype(str)` é obrigatório** na montagem da chave de agrupamento: em coluna de objeto, o `astype` do pandas preserva `NaN` como `float`, e o `demojibake` **estoura**. É o tipo de detalhe que só a execução revela.

## Alternativas consideradas

- **Recusar arquivos com linha irregular e exigir que o usuário os corrija.** Descartada: transfere ao usuário um problema tratável e interrompe a análise por um defeito de formato que não afeta as demais linhas.
- **Descartar linhas irregulares em silêncio.** Descartada por princípio: o usuário concluiria que analisou todos os matches quando parte deles foi ignorada.

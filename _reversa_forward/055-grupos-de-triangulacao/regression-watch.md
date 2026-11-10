# Regression Watch: grupos de triangulação

> Identificador: `055-grupos-de-triangulacao`
> Data: `2026-11-09`
> Vigiar nas próximas extrações. Cada item nasce de uma regra alterada ou de um
> contrato novo em `legacy-impact.md`.

## Itens

| ID | Origem (arquivo, seção) | Regra esperada após a mudança | Tipo de verificação | Sinal de violação |
|----|--------------------------|-------------------------------|---------------------|-------------------|
| W001 | `src/core/dna_analysis.py` | Arquivo com forma de pares no campo de matches é recusado com mensagem que nomeia o campo "CSV de Triangulação"; o CSV de matches mantém a mensagem antiga | presença | Volta a dizer só "Colunas de Nome e cM não encontradas", ou o CSV de matches passa a ser recusado como pares |
| W002 | `src/app.py` (`_ACOES_PRE_ARVORE`) | A ação `triangulacao_analysis` é despachada **antes** da resolução da árvore e roda sem `gedcom_filename` | presença | A ação passa a exigir árvore, ou some do despacho pré-árvore |
| W003 | `src/application/dna_analysis.py` | Análise sem o arquivo auxiliar devolve `grupos == ()` e não muda nada do resultado | presença | `grupos` deixa de ter padrão vazio, ou a ausência do arquivo altera cartões |
| W004 | `src/core/triangulacao.py` (`_fechado`) | Grupo exige **todos** os pares registrados; sobreposição geométrica sem par não vira grupo | presença | O número de grupos da amostra sobe de 28 para a casa das centenas |
| W005 | `src/core/triangulacao.py` (`_montar`) | A região do grupo é a **interseção** dos pares; a faixa publicada está contida em cada faixa membro | presença | A faixa do grupo fica maior que a de algum par |
| W006 | `src/core/triangulacao.py` (`PISO_DE_CM`) | O piso de 10 cM **marca** o par mais fraco e não exclui o grupo | presença | Grupo com par de 6,7 cM desaparece |
| W007 | `src/core/triangulacao.py` | Nenhum cM é somado: o grupo guarda mínimo e máximo **de par** | presença | Aparece campo de cM total do grupo |
| W008 | `src/templates/index.html` (bloco de grupos) | No modo sem árvore, o bloco não exibe média, mediana, distribuição nem percentual | presença | Qualquer estatística agregada renderiza sem árvore |
| W009 | `tests/test_icone_de_atalho.py` (`SHA_DA_TELA`) | `82258c2b…` (52.768 bytes) até uma mudança declarada em `evidence/` | presença | Hash diverge sem delta declarado |
| W010 | `src/application/triangulacao.py` | Desfecho documental só existe com cartões; sem cartões, `desfecho is None` | presença | Grupo sem árvore recebe "sem ancestral" ou "convergente" |
| W011 | `src/parsers/triangulacao_gedmatch.py` | Nome do GEDmatch é limpo do `*` no adaptador; `norm_name` continua intocado | presença | `*Teresa` deixa de casar, ou `norm_name` passa a remover `*` |

## Observações sem peso de regressão

Regras 🟡, que não entram no watch principal:

- **Limiar de acúmulo** (`RN-05`, `ACUMULO_*`): é heurística declarada, ancorada na amostra (51 kits, 0,40 Mb, 5,2–10,4 cM) e nos grupos fechados (2,25–29,85 Mb). Não é número publicado, e pode ser revisto com nova medição.
- **Export nativo do GEDmatch**: a v1 não distingue o consolidado do nativo. Um arquivo com o kit raiz produz grupos que incluem esse kit — limitação declarada, não regressão.
- **Reparo de conjunto mascarado**: foi implementado e removido na mesma rodada (fabricava trios em região de acúmulo). Se voltar, precisa de um teste que o impeça de atravessar o pile-up do chr20.
- **Custo do bloco**: 0,577 s para 1.650 linhas (parse 0,464 s + agrupamento 0,113 s). Não há medição com 100 mil linhas, e estimar seria inventar número.

## Histórico de re-extrações

| Data | Extração | Resultado |
|------|----------|-----------|
| — | — | Ainda não houve re-extração depois desta entrega |

## Arquivadas

Nenhum item arquivado.

# Roadmap: grupos de triangulação

> Identificador: `055-grupos-de-triangulacao`
> Data: `2026-11-09`
> Requirements: `_reversa_forward/055-grupos-de-triangulacao/requirements.md`
> Confidência: 🟢 CONFIRMADO, 🟡 INFERIDO, 🔴 LACUNA

## 1. Resumo da abordagem

A feature entra como **leitura derivada**, no mesmo regime do bloco 039 e da cobertura do arquivo (040): um
módulo de núcleo puro agrupa os pares do CSV de triangulação por **interseção comum com teste de fechamento**;
um segundo módulo classifica cada grupo a partir dos cartões que a análise de DNA **já** produziu; a borda
apenas liga os dois e entrega o bloco ao template. Nada do fluxo existente é reescrito: o CSV de triangulação
é uma entrada opcional a mais, lida por um adaptador próprio que reusa a leitura tolerante de
`parsers/csv_ingest`, e a classificação **não** roda um segundo matching. São dois pontos de entrada para o
mesmo caso de uso — a ação nova, que funciona sem árvore e entrega só os grupos, e um campo opcional na ação
de DNA, que entrega os grupos com desfecho. Não há mudança de banco, de schema nem de contrato de persistência.

## 2. Princípios aplicados

| Princípio | Como a feature se relaciona | Status |
|-----------|------------------------------|--------|
| I. Dados reais nunca entram no versionamento | A fixture é sintética e reproduz as **formas** medidas (BOM, `*`, dois segmentos por par, par incompleto, acúmulo); a amostra real fica fora do repositório e é usada só para medir | respeita |
| II. Comportamento observável preservado | `RF-12` congela: cartões, cM, caminhos, vereditos e descartes não mudam; sem o arquivo novo, a tela é byte a byte a de hoje | respeita |
| III. Nenhuma mudança sem teste | Cada regra nova ganha teste; as que dependem de número (`RN-05`) ganham teste com o caso medido, não com o valor inventado | respeita |
| IV. Arestas do grafo são tipadas | A feature **não** percorre o grafo: a classificação consome o parentesco documental já calculado, que declara os tipos de aresta. Não há travessia nova | respeita (não toca) |
| V. Toda suposição cita a fonte | O único número novo é o limiar de acúmulo, declarado como **heurística do projeto** e ancorado na amostra; nenhuma média, mediana ou faixa é inventada | respeita |

## 3. Decisões técnicas

| ID | Decisão | Justificativa | Alternativas descartadas | Confidência |
|----|---------|----------------|--------------------------|-------------|
| D-01 | Agrupar por **varredura de intervalos por cromossomo**, com interseção comum e fechamento dos pares | `O(n log n)`; a interseção comum garante, por si, que todos os pares se sobrepõem (para intervalos em 1D, interseção dois a dois equivale a interseção comum); é a regra que a amostra validou: 1.535 regiões → 28 grupos | Comparar todos os pares com todos; agrupar por cM; agrupar por distância entre centros | 🟢 |
| D-02 | Adaptador próprio em `parsers/triangulacao_gedmatch.py`, reusando `read_csv_with_fallback` e a detecção **por papel** | O arquivo tem **dois** kits por linha, e `detect_segment_columns` escolhe um só em silêncio (`Kit1 Number`) e ignora `B37 Start/End`; forçar o detector antigo corromperia o dado | Estender `detect_segment_columns`; ler o par como duas linhas sintéticas | 🟢 |
| D-03 | Função de forma compartilhada (`parece_triangulacao`) usada pelos **dois** adaptadores | `RF-02`: o arquivo errado no campo errado precisa ser recusado nomeando o campo correto; hoje ele cai em `DnaCsvSemColunas`, que não diz o que fazer | Validar por extensão; validar por nome de arquivo | 🟢 |
| D-04 | Classificar o desfecho a partir de `documentary.common_ancestor.id` do cartão | É o dado que a análise já produziu; convergente = ids iguais, dividido = ids distintos. Não há segunda passagem de matching (`RN-04`) | Rematchar os membros do grupo; comparar `text_path` | 🟢 |
| D-05 | **Dois pontos de entrada, um caso de uso**: ação nova `triangulacao_analysis` em `_ACOES_PRE_ARVORE` (sem árvore) e campo opcional `triangulacao_csv` na ação `dna_analysis` | A ação de DNA exige árvore e raiz (`_arvore_do_formulario` roda antes do despacho); mover a ação para antes da árvore poria em risco um caminho coberto por paridade | Relaxar a ação de DNA para aceitar tudo; uma ação só com despacho interno | 🟢 |
| D-06 | Armazenar o arquivo com `tipo="csv"`, sem tipo novo nem aba nova | A lista da tela é particionada por **extensão** (`lista_de_arquivos.ABA_DE_DNA`), não por tipo; um tipo novo não mudaria a aba e só acrescentaria contrato | Tipo `"triangulacao"` + terceira aba | 🟢 |
| D-07 | **Sem persistência** dos grupos na v1 | Duas tabelas novas (`group`, `group_member`) e migração de schema para uma leitura derivada; o CSV de grupos cobre a auditoria fora da tela | Persistir em `dna_analysis` como JSON | 🟢 |
| D-08 | Limite de **200 grupos** por análise, com truncamento declarado na tela | A amostra tem 28; o limite existe para arquivo anômalo, não para o caso real | Sem limite; limite por memória | 🟡 |
| D-09 | Remover o `*` inicial **no adaptador**, guardando o nome bruto para exibição | `norm_name` é autoridade global (`ADR-07`); mudá-lo afetaria o fluxo de DNA inteiro e a paridade. O `*` é propriedade do arquivo, não do nome — logo, a limpeza pertence a quem conhece o formato | Alterar `norm_name`; `lstrip("*")` no template | 🟢 |
| D-10 | Só agrupar quando o cabeçalho declara o build (`B37`) | Coordenada sem build corrompe a interseção sem deixar rastro (`RN-10`) | Assumir 37 sempre; pedir o build ao operador | 🟢 |
| D-11 | Bloco `<details open>` **antes** dos cartões, com selo por grupo | Precedente do bloco de cobertura (040): é achado, não rodapé; e `RF-11` exige visível | Bloco recolhido; aba nova | 🟢 |
| D-12 | Export por `POST /grupos.csv`, com os grupos no campo oculto, no regime de `/descartes.csv` | O grupo é grande, mas o conjunto é pequeno (28 grupos, ~116 kits na amostra); reusar o padrão existente evita nova forma de estado | Recalcular no servidor a partir do arquivo; GET com id | 🟡 |
| D-13 | O piso de 10 cM é **marca**, nunca filtro de grupo | Aplicá-lo por linha fraturaria 18 dos 60 grupos fechados; o piso é regra de evidência por match (`BR-D-17`) | Filtrar pares antes de agrupar | 🟢 |
| D-14 | Nenhuma estatística agregada no modo sem árvore | `RN-14`; é o que impede o modo isolado de virar o painel que o produto recusa | Mostrar cM médio e distribuição | 🟢 |

## 4. Premissas

Nenhuma premissa: as três dúvidas do documento inicial foram resolvidas na sessão de esclarecimentos de 2026-11-09.

| Premissa | Origem (`requirements.md` seção) | Risco se errada |
|----------|----------------------------------|-----------------|
| — | — | — |

## 5. Delta arquitetural

| Componente | Arquivo de origem no legado | Tipo de mudança | Resumo |
|------------|------------------------------|-----------------|--------|
| Núcleo de triangulação | `src/core/` (novo) | componente-novo | Agrupamento por interseção e fechamento, região de acúmulo, limite e ordem determinística |
| Classificação de grupo | `src/core/` (novo) | componente-novo | Desfecho a partir dos cartões; junção por kit e, na falta, por nome normalizado |
| Adaptador de entrada | `src/parsers/segmentos_gedmatch.py` (irmão) | componente-novo | Leitura do CSV de pares, detecção por papel, dois kits, B37, `*` |
| Detecção de forma | `src/core/genetic_evidence.py` (`detect_segment_columns`) | contrato-novo | `parece_triangulacao(df)` compartilhada pelos dois adaptadores |
| Caso de uso | `src/application/dna_analysis.py` | contrato-alterado | `ResultadoDeAnalise` ganha `grupos` (padrão `()`); um caso de uso novo de triangulação isolada |
| Borda | `src/app.py` (`_ACAO...`, `_ACOES_PRE_ARVORE`, `index`) | contrato-alterado | Ação `triangulacao_analysis` e campo `triangulacao_csv` em `dna_analysis` |
| Apresentação | `src/templates/index.html` (Fase 3) | contrato-alterado | Formulário de triangulação no modo isolado; bloco de grupos antes dos cartões |
| Exportação | `src/reporting/csv_de_descartes.py` (irmão) | componente-novo | `csv_dos_grupos` com o mesmo desarme de fórmula e o mesmo dialeto |
| Rota de download | `src/web/rotas_assets.py` (`descartes_em_csv`) | contrato-novo | `POST /grupos.csv` |
| Limpeza de nome | `src/utils/text_cleaning.py` | regra-alterada | Função de limpeza do nome do GEDmatch, sem tocar em `norm_name` |

## 6. Delta no modelo de dados

- Resumo: **nenhuma mudança de schema e nenhuma migração**. O que nasce são estruturas em memória (par,
  grupo, membro, desfecho) e um campo novo em `ResultadoDeAnalise`. O banco continua com as 6 tabelas.
- Detalhe completo em: `_reversa_forward/055-grupos-de-triangulacao/data-delta.md`

## 7. Delta de contratos externos

| Contrato | Tipo | Arquivo de detalhe |
|----------|------|--------------------|
| `POST /` com `action=triangulacao_analysis` | HTTP | `_reversa_forward/055-grupos-de-triangulacao/interfaces/triangulacao-analysis.md` |
| `POST /` com `action=dna_analysis` (campo `triangulacao_csv`) | HTTP | `_reversa_forward/055-grupos-de-triangulacao/interfaces/dna-analysis.md` |
| `POST /grupos.csv` | HTTP | `_reversa_forward/055-grupos-de-triangulacao/interfaces/grupos-csv.md` |

## 8. Plano de migração

n/a. Não há dado a migrar: o arquivo de triangulação é entrada nova, os grupos são derivados em memória e
nada é gravado. Arquivo já armazenado antes da feature continua legível pelo fluxo antigo, sem alteração.

## 9. Riscos e mitigações

| Risco | Impacto | Probabilidade | Mitigação |
|-------|---------|---------------|-----------|
| Export nativo (com kit raiz) entra como grupo | alto | média | Formato esperado declarado na tela; limitação registrada na §10 dos requirements; feature futura com fixture própria |
| Grupo fechado que é acúmulo (pares completos numa região curta) | alto | baixa | `RN-05` marca a região; o desfecho não é alterado, e a tela mostra os números que sustentam o alerta |
| Nome com `*` ou de uma palavra casa com a pessoa errada | alto | média | Junção primária por **kit**; `RF-17` limpa o `*`; a identidade ambígua já existente continua avisando |
| Arquivo grande (100 mil linhas) estoura tempo ou memória | médio | baixa | Varredura log-linear, limite de 200 grupos com truncamento, medição obrigatória no `onboarding.md` |
| Dois pontos de entrada confundem o operador | médio | média | Texto de ajuda em cada formulário dizendo o que cada um entrega; o desfecho é anunciado como dependente da análise |
| Pressão para o bloco virar dashboard | médio | média | `RN-14` + teste que falha se o modo sem árvore renderizar média, mediana ou distribuição |
| `SHA_DA_TELA` muda sem declaração | médio | alta | Atualização declarada em `evidence/`, com o delta em bytes, como na 054 |

## 10. Critério de pronto

- [ ] Todas as ações do `actions.md` marcadas `[X]`
- [ ] `cross-check.md` (se executado) sem CRITICAL nem HIGH
- [ ] `regression-watch.md` gerado
- [ ] `RF-12` provado: HTML dos cartões e do CSV de descartes idêntico ao de antes quando o arquivo novo não é enviado
- [ ] O bloco não aparece e a tela não muda um byte sem o arquivo de triangulação
- [ ] Nenhuma estatística agregada no modo sem árvore (teste dedicado)
- [ ] `SHA_DA_TELA` novo declarado em `evidence/` com o delta em bytes
- [ ] Re-extração reversa executada e sem regressão vermelha (recomendado, não obrigatório)

## 11. Histórico de alterações

| Data | Alteração | Autor |
|------|-----------|-------|
| 2026-11-09 | Versão inicial gerada por `/reversa-plan` | reversa |

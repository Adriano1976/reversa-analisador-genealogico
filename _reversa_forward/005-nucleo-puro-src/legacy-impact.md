# Legacy Impact: núcleo puro em `src/core/`

> Identificador da feature: `005-nucleo-puro-src`
> Data: `2026-10-06`
> Cenário: **legado** (âncora em `_reversa_sdd/architecture.md` + `_reversa_sdd/domain.md`)
> Rodada: **parcial** — Fase 1 (Preparação), ações `T001` a `T004`

## Escopo desta rodada

Esta rodada **não tocou código de produto**. Ela instrumentou o harness diferencial (dois probes novos) e registrou a linha de base. `src/` está exatamente como estava: nenhuma regra de negócio foi criada, alterada ou removida.

## Arquivo afetado | Componente | Tipo | Severidade | Justificativa

| Arquivo afetado | Componente | Tipo | Severidade | Justificativa |
|---|---|---|---|---|
| `_reversa_sdd/parity/harness.py` | instrumento de paridade (`_reversa_sdd/migration/parity_harness.md`) | contrato-alterado | MEDIUM | Os dois coletores passam a receber o diretório de CSVs de DNA como argumento posicional, e o harness ganha `--dna`. O probe de aceitação só é possível por essa porta. Também corrigido o caminho do `--gedcom` para absoluto, porque o coletor faz `chdir` antes de usar o caminho |
| `_reversa_sdd/parity/harness.py` | instrumento de paridade | componente-alterado | MEDIUM | Dois probes novos: `dna` (análise pela rota, nas 7 fixtures de CSV) e `decomposicao` (`are_spouses` para todos os pares + `split_path_by_marriage` para todo par com caminho indireto) |
| `_reversa_sdd/parity/harness.py` | instrumento de paridade | regra-nova | HIGH | Classificação do desfecho por **modo** (`ok`, `erro`, `raiz_ausente`, `arquivo_ausente`, `sem_arquivo`, `outro`) em vez de comparação de texto de mensagem. Sem isso, todo caso de erro acusaria divergência de redação |
| `_reversa_forward/005-nucleo-puro-src/evidence/` | — | componente-novo | LOW | Evidência da linha de base: suíte, paridade e procedência do oráculo |

## Diff conceitual por componente

### `harness.py` — o probe de aceitação não podia ser o que a `T001` descrevia

A ação pedia comparar `build_ged_indexes` e `match_candidates` nos dois lados. **No oráculo essas funções não existem.** Verificado por varredura das definições: as 16 funções do oráculo são `get_name`, `strip_bad_utf`, `norm_name`, `drop_short_tokens`, `surname_core_tokens`, `split_name_pt`, `surnames_set`, `top_given_tokens`, `token_prefixes`, `demojibake`, `get_relationships_by_cm`, `load_gedcom_and_build_graph`, `are_spouses`, `split_path_by_marriage`, `find_indirect_path` e `find_ancestral_path`.

A decisão de aceitação do legado está **inline** dentro da rota `POST /`, entre `app_legacy_e43ca22.py:695` (`best_score = best_g = -1`) e `:796` (a mensagem com `given`, `final`, `inter`, `jacc`). Transcrever aquele bloco para o coletor criaria uma segunda implementação para comparar com a primeira — exatamente a validação circular que o RISK-002 existe para prevenir.

**Solução implementada, por decisão explícita do usuário em 2026-10-06:** os dois lados executam a análise de DNA **pela rota**, com o mesmo GEDCOM e o mesmo CSV, e o probe intercepta `render_template` para capturar o contexto de domínio — `dna_results`, `skipped_matches` e a mensagem — **sem renderizar HTML**. É compatível com a regra do `parity_specs.md` ("asserir sobre comportamento de domínio, nunca sobre HTML") e não depende de `src/templates/index.html` nem do template legado, cuja deriva está registrada como não reconciliada.

### `harness.py` — a limitação que o probe carrega

O campo `motivo` do legado funde **duas causas distintas**:

| Causa | Mensagem |
|---|---|
| Recusado pelas regras de aceitação | `score insuficiente ou conflito de sobrenome (given=…, final=…, inter=…, jacc=…)` |
| **Aceito** mas sem caminho | `sem caminho subindo por pais (pais ausentes no GED?)` |

O candidato mantém a mesma fusão. Portanto o probe **não isola** as regras A/B/C/D da busca de caminho. O que ele prova é o **resultado observável da análise inteira**, o que fecha a lacuna nº 1 do `parity_harness.md` — mas **não** é o probe cirúrgico que a `RF-10` descrevia, e isso está declarado no artefato de evidência.

### Correções necessárias ao próprio probe

Cinco defeitos do probe foram encontrados e corrigidos **antes** da medição final. Registrados porque três deles são armadilhas que voltariam a morder:

1. **Caminho relativo do `--gedcom`** quebrava, porque o coletor faz `chdir` antes de usar o caminho. Corrigido com `os.path.abspath`.
2. **O candidato deriva o nome do arquivo GEDCOM do conteúdo** (`chave_de_armazenamento`, BUG-QMLY), e o formulário devolve esse nome no POST seguinte. Reenviar o nome original fazia o candidato responder `Arquivo 'probe.ged' não existe mais` — erro de encanamento do probe, não divergência de domínio. Corrigido fazendo o que o navegador faz: sobe, lê o nome devolvido e usa o nome devolvido.
3. **`relacoes` não existe no resultado do candidato.** O oráculo passa `relationships` como string pronta; o candidato passa `hypotheses` em estrutura. Comparar produziria divergência de forma, não de conteúdo. Campo removido da comparação.
4. **cM agregado diverge por desenho.** Medido em `cm_boundaries.csv` sobre `basic.ged`: o legado soma os 6 segmentos de `Ana Silva` (3.760); o candidato agrupa por kit. Comparar esses números acusaria divergência onde não há. O cM **não** é comparado; caminho, nome e contagens são.
5. **`"não encontrada"` é substring de `"não encontradas"`.** O erro de colunas do CSV (`Colunas de Nome e cM não encontradas`) era classificado como raiz ausente. Corrigido com padrão específico (`seu nome.*não foi encontrad`), e não por substring.

## Preservadas

Todas as regras 🟢 de `_reversa_sdd/domain.md` continuam intactas. As que importam para esta feature, e que a linha de base confirma:

| Regra | Situação |
|---|---|
| BR-D-44 a BR-D-53 — matching exato, score difuso, filtro anti-falso-positivo, Jaccard adaptativo e os cinco ramos de aceitação | **Intactas.** O probe novo exercita a cadeia inteira e não achou divergência |
| BR-D-15 — o cM acumulado não é arredondado | **Intacta.** Nenhum código de produto foi tocado |
| BR-C-04 a BR-C-08 — BFS bidirecional com teto de 20, caminho indireto com teto de 40, import do grafo dentro da função | **Intactas.** Os 1.600 pares por fixture seguem em paridade |
| BR-C-22 — o índice nome→ids é reconstruído quando `versao` muda | **Intacta.** Nenhum código de produto foi tocado |
| BR-MIGRAR-020/021 — as 9 faixas de cM se sobrepõem; cM ≤ 0 devolve lista vazia | **Intactas.** Os 40 valores de cM seguem em paridade |
| `are_spouses` / `split_path_by_marriage` — decomposição do caminho (RISK-011) | **Intactas e agora medidas.** Passaram a ter probe dedicado, o que não tinham |

## Modificadas

**Nenhuma regra de negócio foi modificada, removida ou criada nesta rodada.** A alteração é toda em instrumento de verificação (`harness.py`), que não é runtime do sistema — o `architecture.md` já declara `_reversa_sdd/oracle/`, `parity/`, `screens/` e `migration/` como instrumentação **fora do escopo do sistema em runtime**.

## Histórico de alterações

| Data | Alteração | Autor |
|------|-----------|-------|
| 2026-10-06 | Versão inicial gerada por `/reversa-coding` na execução de `T001` a `T004` (rodada parcial, Fase 1) | reversa |

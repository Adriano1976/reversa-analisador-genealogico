# Linha de base da Fase 1 (T004)

> Feature: `005-nucleo-puro-src`
> Data da medição: `2026-10-06`
> Ação: `T004` — medir e registrar a linha de base **com a assinatura atual**, antes de qualquer edição de produto.

## Procedência do oráculo

Sem isto a evidência não tem valor — é a exigência do `ORACLE_MANIFEST.md` §Restrições de uso, item 4.

| Campo | Valor |
|---|---|
| Arquivo | `_reversa_sdd/oracle/app_legacy_e43ca22.py` |
| sha256 medido em 2026-10-06 | `44370B2339A645C4D9CE732AC3962811B16B35F587ECE3507DAD4FC3D87646BB` |
| sha256 registrado no `ORACLE_MANIFEST.md` | `44370b2339a645c4d9ce732ac3962811b16b35f587ece3507dad4fc3d87646bb` |
| Confere? | ✅ **Sim** — o oráculo está intacto, e nenhuma ação desta rodada o modificou |

## Medição 1 — suíte de testes

Arquivo: `T004-suite-linha-de-base.txt`

```
164 passed, 15 errors in 68.26s
```

Os 15 erros são todos de `tests/test_upload_seguranca.py`, em `setup`, por `PermissionError` do diretório temporário — os mesmos de `inventory.md#6`, e não regressão. Confere com a linha de base medida em `/reversa-requirements` (164 + 15 = 179 itens).

## Medição 2 — paridade diferencial

Arquivo: `T004-paridade-linha-de-base.txt`

```
RESULTADO: PARIDADE 100%% (zero divergencia)
6 de 6 fixtures com PARIDADE OK
```

| Fixture | Resultado |
|---|---|
| `affinity.ged` | ✅ paridade |
| `basic.ged` | ✅ paridade |
| `deep25.ged` | ✅ paridade |
| `mojibake_latin1.ged` | ✅ paridade |
| `no_name.ged` | ✅ paridade |
| `variants.ged` | ✅ paridade |

Amostra de pares de caminho: 40×40 = 1.600 por lado. Valores de cM: 40.

## Probes ativos nesta medição

Além dos probes que já existiam, esta rodada acrescentou dois (`T001` e `T002`):

| Probe | O que compara | Ação |
|---|---|---|
| `dna` | análise de DNA **pela rota**, nas 7 fixtures de CSV, com 3 campos comparados: `success`, `modo` e a lista de resultados (nome, cM, caminho) e de descartados (nome, motivo) | `T001` |
| `decomposicao` | `are_spouses` para **todos** os pares de pessoas, mais `split_path_by_marriage` (esquerda, direita, casal) para todo par com caminho indireto | `T002` |

> O probe `decomposicao` só é avaliado nas fixtures que têm `affinity.ged` ao lado, porque o caminho indireto com múltiplas afinidades é o caso que o RISK-011 nomeia. É a mitigação obrigatória que o `parity_specs.md` §Riscos residuais descrevia como faltante.

## O que esta linha de base NÃO prova

Registrado para não dar impressão de cobertura maior do que a real:

1. **O probe de aceitação não isola as regras A/B/C/D da busca de caminho.** No legado, um match aceito que não tenha caminho é descartado com o motivo `"sem caminho subindo por pais (pais ausentes no GED?)"` — o mesmo campo `motivo` que recebe a recusa por score. As duas causas ficam fundidas, nos dois lados. O que se compara é o **resultado observável da análise inteira**, que é um avanço real (é a lacuna nº 1 do `parity_harness.md`), mas **não** é o probe cirúrgico que a `RF-10` descrevia.
2. **O cM agregado diverge entre os lados por desenho, e por isso não é comparado.** Medido em `cm_boundaries.csv` sobre `basic.ged`: o legado soma os 6 segmentos de `Ana Silva` (0 + −5 + 15 + 50 + 300 + 3400 = **3760**); o candidato agrupa por kit e reporta o valor do kit selecionado. Comparar esses números acusaria divergência onde não há decisão de domínio divergente. O que **é** comparado é o caminho, o nome e a contagem de resultados e descartados.
3. **Mensagens de erro são comparadas por MODO, não por texto.** O legado fecha com `"Ocorreu um erro: None"` (a exceção do pandas não tem texto) e o candidato nomeia a causa. O `modo()` classifica o desfecho em `ok`, `erro`, `raiz_ausente`, `arquivo_ausente`, `sem_arquivo` ou `outro`. Sem isso o probe acusaria divergência de redação em todo caso de erro, o que o `parity_specs.md` manda asserir fora da comparação.
4. **A paridade visual de telas continua não medida** — 0 goldens capturados (AMB-022).

## Observação sobre a raiz dos probes de DNA

O probe usa `PARITY_ROOT` (padrão `"Ana Silva"`). Nas fixtures que **não** contêm essa pessoa — `affinity`, `deep25`, `no_name`, `variants` — os dois lados devolvem `raiz_ausente`, e o probe compara isso. Ou seja: nessas quatro fixtures o probe mede o **caminho de recusa por raiz ausente**, não a aceitação. A aceitação é exercitada de fato em `basic.ged` e `mojibake_latin1.ged`, que contêm `Ana Silva` e onde os 7 CSVs produzem resultados comparados.

## Histórico de alterações

| Data | Alteração | Autor |
|------|-----------|-------|
| 2026-10-06 | Linha de base registrada por `/reversa-coding` na execução de `T001` a `T004` | reversa |
